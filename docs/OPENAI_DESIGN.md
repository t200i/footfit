# OpenAI SDK 深度 Survey — 伺服器端相容性參考

> **目的**：深度調查 OpenAI Python SDK (`openai>=2.x`) 原始碼，找出伺服器端必須遵守的  
> 確切行為，供 `interfaces/api.py` 實作時對照，避免重複 survey。  
> 不重複 `ARCHITECTURE.md` 中的架構決策。  
> 版本：openai-python `main` branch，2026-05-08 調查。

---

## 1. SDK Package 結構（`src/openai/`）

| 路徑 | 用途 |
|------|------|
| `_client.py` | `OpenAI` / `AsyncOpenAI` 主類別，組合所有 resource |
| `_base_client.py` | HTTP transport、retry、auth 基底 |
| `resources/chat/completions/completions.py` | `Completions` / `AsyncCompletions` 資源 |
| `types/chat/` | 所有 request / response Pydantic 類別 |
| `_streaming.py` | `Stream[T]` 包裝，解析 SSE |
| `lib/streaming/` | `ChatCompletionStream` 高階包裝（`.stream()` context manager） |

SDK 的 `client.chat.completions.create(...)` 直接對 `POST /v1/chat/completions` 發請求；  
`client.models.list()` 對 `GET /v1/models` 發請求。

傳輸層使用 **httpx**（非 requests）。重試、超時均由 `_base_client.py` 管理，與我方無關。

---

## 2. 我方伺服器必須實作的端點

| Method | Path | SDK 呼叫 | 對應 SDK 類別 |
|--------|------|----------|--------------|
| `POST` | `/v1/chat/completions` | `client.chat.completions.create(...)` | `ChatCompletion` / `Stream[ChatCompletionChunk]` |
| `GET` | `/v1/models` | `client.models.list()` | `SyncCursorPage[Model]` |

> **最小實作**：只需這兩個端點即可通過 OpenAI SDK 的基本使用場景。

---

## 2.5. 客戶端初始化陷阱（`_client.py` 實際行為）

### `api_key` 不能是空字串

```python
# SDK 原始碼邏輯（_client.py）
if _enforce_credentials and not self.api_key ...:
    raise OpenAIError("Missing credentials. Please pass an `api_key`...")
```

`not ""` 為 `True`，所以空字串會 raise。  
**結論**：呼叫者必須傳非空 `api_key`，習慣上用 `api_key="none"` 或 `api_key="local"`。

### SDK 永遠送出 `Authorization` header

```python
# _bearer_auth property
return {"Authorization": f"Bearer {api_key}"}
```

我方 FastAPI 伺服器完全不需要驗證這個 header，但也不能因為不認識而 reject（FastAPI 預設不管）。  
若要本地安全，可以加 `Authorization: Bearer <known-token>` 的 middleware，但非必要。

### 若 `api_key` 為空但 header 被 omit → `_validate_headers` 會 raise

```python
def _validate_headers(self, headers, custom_headers):
    if _has_header(headers, "Authorization") or _has_omitted_header(custom_headers, "Authorization"):
        return
    raise TypeError("Could not resolve authentication method...")
```

只要 `api_key="none"`（非空），SDK 就能正常初始化且會帶 header，伺服器不受影響。

---

## 3. `POST /v1/chat/completions` — 請求結構

### 3.1 Request JSON Body

```json
{
  "model": "my-model-id",
  "messages": [ /* 見 3.2 */ ],
  "max_tokens": 512,
  "stream": false,
  "temperature": 1.0,
  "top_p": 1.0,
  "n": 1,
  "stop": null,
  "stream_options": { "include_usage": true }
}
```

**我方必實作欄位**：`model`, `messages`, `max_tokens`, `stream`  
其餘欄位為選用，伺服器可忽略（不可報錯）。

### 3.2 `messages` 陣列元素型別

`ChatCompletionMessageParam` = Union of：

| 角色 | Python 類別 | `role` 值 | `content` 型別 |
|------|-------------|-----------|----------------|
| 使用者 | `ChatCompletionUserMessageParam` | `"user"` | `str \| Iterable[ContentPart]` |
| 系統 | `ChatCompletionSystemMessageParam` | `"system"` | `str \| Iterable[ContentPart]` |
| 開發者 | `ChatCompletionDeveloperMessageParam` | `"developer"` | `str \| Iterable[ContentPart]` |
| 助手 | `ChatCompletionAssistantMessageParam` | `"assistant"` | `str \| None` |
| 工具回應 | `ChatCompletionToolMessageParam` | `"tool"` | `str \| Iterable[ContentPart]` |

### 3.3 `ContentPart` 型別（`ChatCompletionContentPartParam`）

```python
ChatCompletionContentPartParam = Union[
    ChatCompletionContentPartTextParam,       # {"type": "text",      "text": "..."}
    ChatCompletionContentPartImageParam,      # {"type": "image_url", "image_url": {...}}
    ChatCompletionContentPartInputAudioParam, # {"type": "input_audio", ...}
    File,                                     # {"type": "file",  "file": {...}}
]
```

#### 純文字 Part
```json
{ "type": "text", "text": "請描述這張圖片" }
```

#### 圖片 Part（VLM 關鍵）
```json
{
  "type": "image_url",
  "image_url": {
    "url": "https://example.com/photo.jpg",
    "detail": "auto"
  }
}
```
- `url`：HTTP URL **或** `data:image/jpeg;base64,<base64>` 格式
- `detail`：`"auto"` | `"low"` | `"high"`（optional）

#### 典型多模態 user message
```json
{
  "role": "user",
  "content": [
    { "type": "image_url", "image_url": { "url": "data:image/jpeg;base64,..." } },
    { "type": "text",      "text": "這張圖片裡有什麼？" }
  ]
}
```

---

## 5. `GET /v1/models` — 回應結構

```json
{
  "object": "list",
  "data": [
    {
      "id": "my-model-id",
      "object": "model",
      "created": 1700000000,
      "owned_by": "local"
    }
  ]
}
```

SDK `client.models.list()` 回傳 `SyncCursorPage[Model]`，會讀 `data` 陣列。  
額外的 `description` 欄位不影響 SDK（Pydantic `extra="ignore"`），可保留。

---

## 6. 深度：image_url 在傳輸過程中的行為

### SDK 端不做任何轉換

SDK 原始碼（`types/chat/chat_completion_content_part_image_param.py`）：
```python
class ImageURL(TypedDict, total=False):
    url: Required[str]       # 就是字串，SDK 不動它
    detail: Literal["auto", "low", "high"]
```

SDK **直接把 `url` 字串序列化進 JSON** 送出，不會：
- 驗證 URL 是否可達
- 解碼 base64
- 壓縮圖片
- 更改 `detail`

**結論**：伺服器收到的 `image_url.url` 就是客戶端傳入的原始字串。

### 伺服器端解析路徑

```
content (str | list)
    │
    ├── isinstance(content, str)
    │   → 純文字，送給文字模型
    │
    └── isinstance(content, list)
        → 遍歷 parts：
            part["type"] == "text"      → 提取 part["text"]
            part["type"] == "image_url" → 提取 part["image_url"]["url"]
                │
                ├── url.startswith("data:")
                │   → data URI，格式：data:<mime>;base64,<b64data>
                │   → 解碼：base64.b64decode(url.split(",",1)[1])
                │   → 結果：bytes（可直接用 PIL.Image.open(BytesIO(bytes))）
                │
                └── url.startswith("http")
                    → 需要 requests.get(url).content 下載
                    → 本地部署通常不走這條（無網路存取）
```

### 完整的 content 解析 helper

```python
import base64
from io import BytesIO
from PIL import Image  # 或用其他圖片庫

def parse_message_content(content: str | list) -> tuple[str, list[Image.Image]]:
    """
    Returns (combined_text, list_of_PIL_images).
    text model: ignore images; vlm: pass both.
    """
    if isinstance(content, str):
        return content, []

    texts: list[str] = []
    images: list[Image.Image] = []

    for part in content:
        t = part.get("type")
        if t == "text":
            texts.append(part["text"])
        elif t == "image_url":
            url: str = part["image_url"]["url"]
            if url.startswith("data:"):
                # data:image/jpeg;base64,<data>
                b64 = url.split(",", 1)[1]
                img_bytes = base64.b64decode(b64)
                images.append(Image.open(BytesIO(img_bytes)).convert("RGB"))
            # HTTP URL: 本地部署跳過或自行實作下載

    return " ".join(texts), images
```

### 多個 image part 的順序

SDK 按 `content` 陣列的順序送出。Gemma4 的 `apply_chat_template` 期望圖片與文字交錯，  
或圖片先於文字——順序與 content 陣列一致，由客戶端決定。

---

## 7. 深度：SSE 串流相容性細節（`_streaming.py`）

### SSEDecoder chunk 邊界規則

```python
# 三種合法邊界
if data.endswith((b"\r\r", b"\n\n", b"\r\n\r\n")):
    yield data
```

我方用 `yield f"data: ...\n\n"` → 符合 `\n\n` 規則。  
**不要用 `\r\n\r\n`**（Windows 換行），FastAPI 的 yield 在 Python 中預設是 `\n`。

### [DONE] 停止條件

```python
# __stream__ 內部
for sse in self._iter_events():
    if sse.data.startswith("[DONE]"):
        break
    data = sse.json()  # 如果 JSON 解析失敗 → raise json.JSONDecodeError
    yield process_data(data, cast_to, response)
```

**我方必須在 stream 結束時送 `data: [DONE]\n\n`，否則 SDK 會等到 TCP connection close 才結束迭代。**

### SSE 中的 JSON 解析錯誤

若送出非 JSON 的 data（如空行或除 `[DONE]` 外的非 JSON），`sse.json()` 會 raise。  
**絕對不要送空的 `data: \n\n`**，送 `data: [DONE]\n\n` 才是正確結尾。

### stream 中的錯誤傳遞

```python
if is_mapping(data) and data.get("error"):
    error = data.get("error")
    message = error.get("message") if is_mapping(error) else None
    raise APIError(message=message or "An error occurred during streaming", ...)
```

推論失敗時的正確 SSE 格式：
```
data: {"error": {"message": "CUDA out of memory", "type": "server_error", "code": "500"}}\n\n
data: [DONE]\n\n
```

客戶端會收到 `openai.APIError`。

### `object` literal 必須精確匹配

Pydantic 的 `Literal["chat.completion.chunk"]` 驗證：若值為 `"chat.completion_chunk"`（底線）或其他變體，SDK 會 raise `ValidationError`。  
**現有 `api.py` 已正確使用 `"chat.completion.chunk"`。**

---

## 8. `interfaces/api.py` 現狀 vs. 需修正項目

### 問題清單

| 項目 | 現狀 | 影響 | 修正方法 |
|------|------|------|----------|
| `Message.content` 型別 | `str` only | 多模態請求被 Pydantic **拒絕**（422 error） | 改為 `Union[str, list]` |
| 回應中的 `model` 欄位 | `req.model`（客戶端傳入值） | 客戶端看到的 model 與 `/v1/models` 列表不一致 | 改為 `svc.info.model_id` |
| 首個 stream chunk | 無 role 宣告 chunk | 功能正常，但不夠嚴格相容 | 選擇性加入 |
| `usage` 數值 | `-1` | 功能正常，Pydantic 接受任意 int | 可保留 |

### 修正 1：`Message.content` 型別

```python
# 改前
class Message(BaseModel):
    role: str
    content: str

# 改後
from typing import Union

class Message(BaseModel):
    role: str
    content: Union[str, list]  # list 內部是 ContentPart dict
```

這是支援 VLM 的**最小必要修改**。

### 修正 2：回應 `model` 欄位

```python
# _completion_response 和 _stream 中，將：
"model": model,  # 原為 req.model
# 改為：
"model": svc.info.model_id,
```

並從函式簽名移除 `model: str` 參數（不再需要）。

### 修正 3（選用）：首個 stream chunk 加入 role

```python
# _stream() 函式開頭加入：
first = {
    "id": cid, "object": "chat.completion.chunk", "created": ts,
    "model": svc.info.model_id,
    "choices": [{"index": 0, "delta": {"role": "assistant", "content": None}, "finish_reason": None}],
}
yield f"data: {json.dumps(first)}\n\n"
```

---

## 9. 端對端：自訂多模態模型的最小修改路徑

### 伺服器端（`interfaces/api.py`）

只需改兩行：

1. `content: str` → `content: Union[str, list]`
2. `"model": req.model` → `"model": svc.info.model_id`（兩處）

### 模型端（`models/igpu/gemma4.py`）

`generate()` 和 `generate_stream()` 的 `messages: list[dict]` 已支援 `content: str | list`。  
需在 `_build_inputs()` 中用 `parse_message_content()` 從 content list 提取 PIL images。

### CLI 端（`interfaces/cli.py`）

加入 `--image` 參數，將圖片轉為 base64 data URI 後塞入 content list：

```python
import base64
if args.image:
    b64 = base64.b64encode(open(args.image, "rb").read()).decode()
    content = [
        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
        {"type": "text", "text": args.prompt},
    ]
else:
    content = args.prompt
```

---

## 10. 自訂模型接入的最小化架構設計

> 本節回答一個具體問題：**「我有一個新模型，最少要動哪些東西才能讓它透過 OpenAI SDK 被呼叫？」**

### 10.1 整體資料流

```
OpenAI SDK client
    │  POST /v1/chat/completions
    │  {"messages": [...], "stream": true/false, ...}
    ▼
interfaces/api.py  (FastAPI)
    │  parse → list[dict]   ← 這裡 content 必須是 str|list
    │  呼叫 svc.generate() / svc.generate_stream()
    ▼
core/base.py  LLMService (ABC)
    │  generate(messages, max_new_tokens) → str
    │  generate_stream(messages, max_new_tokens) → Iterator[str]
    ▼
models/*/your_model.py  (concrete implementation)
    │  解析 messages 中的 content（str or list of parts）
    │  執行推論
    │  yield / return 文字片段
    ▼
interfaces/api.py  (序列化)
    │  包裝為 ChatCompletion / ChatCompletionChunk JSON
    ▼
OpenAI SDK  解析 → response.choices[0].message.content
```

**關鍵洞察**：`interfaces/api.py` 是唯一知道 OpenAI 協議格式的層；  
模型實作 (`LLMService`) 完全不需要知道 SSE、JSON schema、或 SDK 的任何細節。

---

### 10.2 `LLMService` 是唯一必須實作的契約

```python
# core/base.py — 這是接入的全部契約
class LLMService(ABC):
    info: ModelInfo  # model_id, name, description, device

    @abstractmethod
    def generate(self, messages: list[dict], max_new_tokens: int = 200) -> str:
        """同步推論，回傳完整文字"""
        ...

    @abstractmethod
    def generate_stream(self, messages: list[dict], max_new_tokens: int = 200) -> Iterator[str]:
        """串流推論，每次 yield 一個文字片段（token 或字）"""
        ...
```

`messages` 的格式：
```python
[
    {"role": "system",    "content": "你是助手"},
    {"role": "user",      "content": "你好"},              # 純文字
    {"role": "user",      "content": [                     # 多模態
        {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,..."}},
        {"type": "text",      "text": "這張圖是什麼？"}
    ]},
    {"role": "assistant", "content": "這是一隻貓"},
]
```

模型實作需要能消化這兩種 content 格式。

---

### 10.3 接入新模型的 Checklist（最小化步驟）

#### Step 1：建立模型檔案

```python
# models/<backend>/my_model.py
from core.base import LLMService, ModelInfo

class MyModelService(LLMService):
    info = ModelInfo(
        model_id="org/my-model",
        name="My Model",
        description="...",
        device="cuda",
        supports_vision=True,  # 或 False
    )

    def __init__(self):
        # 載入模型（一次性）
        self._model = load_my_model(...)

    def generate(self, messages, max_new_tokens=200) -> str:
        inputs = self._prepare(messages)
        return self._model.generate(inputs, max_new_tokens)

    def generate_stream(self, messages, max_new_tokens=200):
        inputs = self._prepare(messages)
        for token in self._model.stream(inputs, max_new_tokens):
            yield token

    def _prepare(self, messages):
        # 解析 content str|list，提取文字和圖片
        ...
```

#### Step 2：建立 composition root

```python
# deployment/<machine>/serve.py
import sys
sys.path.insert(0, project_root)

from models.<backend>.my_model import MyModelService
from interfaces.api import build_app
import uvicorn

svc = MyModelService()
app = build_app(svc)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

#### Step 3（僅 VLM 需要）：確認 `interfaces/api.py` 的 `Message.content` 已是 `Union[str, list]`

#### Step 4：不需要動任何其他檔案

`interfaces/api.py`、`interfaces/cli.py`、`interfaces/comfyui.py` 完全不依賴具體模型。

---

### 10.4 `_prepare()` / `_build_inputs()` 的標準實作模式

這是接入工作量最集中的地方，以下是可複用的模式：

```python
import base64
from io import BytesIO
from PIL import Image

def _parse_messages(self, messages: list[dict]):
    """
    把 OpenAI messages 格式轉換成模型需要的輸入。
    返回 (text_prompt: str, images: list[PIL.Image])
    """
    prompt_parts = []
    images = []

    for msg in messages:
        role = msg["role"]
        content = msg["content"]

        if isinstance(content, str):
            prompt_parts.append(f"<{role}>: {content}")
        elif isinstance(content, list):
            for part in content:
                if part["type"] == "text":
                    prompt_parts.append(f"<{role}>: {part['text']}")
                elif part["type"] == "image_url":
                    url = part["image_url"]["url"]
                    if url.startswith("data:"):
                        b64 = url.split(",", 1)[1]
                        img = Image.open(BytesIO(base64.b64decode(b64))).convert("RGB")
                        images.append(img)
                    # 忽略 HTTP URL（本地部署）

    return "\n".join(prompt_parts), images
```

**不同後端的差異只在最後一步**：  
- HuggingFace (iGPU)：`processor(text=prompt, images=images, return_tensors="pt")`  
- ONNX / subprocess (NPU)：把圖片存成暫存檔，傳路徑給 subprocess  
- 純文字模型：直接忽略 `images` 串列

---

### 10.5 架構 Insight：為什麼這個設計能最小化接入成本

#### Insight 1：協議轉換集中在 `interfaces/api.py` 一個地方

```
OpenAI JSON schema ←→ interfaces/api.py ←→ list[dict] ←→ LLMService
```

新模型只需懂 `list[dict]` 格式，不需要懂 SSE 格式、`Literal["chat.completion.chunk"]` 等協議細節。  
反過來，若 OpenAI 改了 API 格式（如新增欄位），只需改 `api.py` 一個地方。

#### Insight 2：`content: str | list` 是唯一的多模態邊界

整個系統只有一個地方需要處理 `str vs list` 判斷：模型的 `_prepare()` 方法。  
`interfaces/api.py` 只需接受 `list`，不需要理解 image part 的結構。  
`interfaces/cli.py` 只需把 `--image` 轉成 data URI 塞進 list，不需要知道模型如何處理。

#### Insight 3：`svc.info.model_id` 是 SDK ↔ 伺服器的身份錨點

SDK 呼叫時帶的 `model` 參數其實只是**建議**，伺服器回應中的 `"model"` 欄位才是 SDK  
用來識別是哪個模型回應的。若回傳 `req.model` 而非 `svc.info.model_id`，  
客戶端的 `response.model` 就會是傳入值（可能是 `"gpt-4"`），造成混淆。

#### Insight 4：`generate_stream` 只需 yield 字串片段

SDK 的 Stream 解析對 chunk 大小沒有要求——可以 yield 整個 token，也可以 yield 單一字元。  
`interfaces/api.py` 的 `_stream()` 負責把每個 yield 包裝成正確的 SSE JSON。  
模型端不需要知道如何格式化 SSE。

#### Insight 5：NPU / iGPU 不能共存在同一 process

兩個後端分別有不同的 conda 環境。  
**composition root（`deployment/*/serve.py`）是決定使用哪個後端的唯一位置。**  
`interfaces/api.py` 收到的永遠只是一個 `LLMService` 實例，不知道底下是 NPU 還是 iGPU。

---

### 10.6 接入新模型時的常見陷阱

| 陷阱 | 原因 | 解法 |
|------|------|------|
| 422 Unprocessable Entity | `Message.content: str`，VLM 請求帶 list | 改為 `Union[str, list]` |
| Stream 不結束 | 沒有送 `data: [DONE]\n\n` | 確認 `_stream()` 最後有 `yield "data: [DONE]\n\n"` |
| `object` validation error | 拼成 `"chat.completion_chunk"`（底線） | 必須是 `"chat.completion.chunk"`（點） |
| SDK `OpenAIError: Missing credentials` | `api_key=""` 空字串 | 改為 `api_key="none"` |
| 模型回應 model 與 `/v1/models` 不一致 | 回傳 `req.model` 而非 `svc.info.model_id` | 改用 `svc.info.model_id` |
| base64 decode 失敗 | data URI 格式：`data:image/jpeg;base64,XXX` | `url.split(",", 1)[1]` 才是 base64 部分 |
| 圖片 mode 不對 | PIL 預設保留原始 mode（如 RGBA） | 統一 `.convert("RGB")` |

---

*Source: openai-python `main` branch，原始碼調查日期 2026-05-08*
