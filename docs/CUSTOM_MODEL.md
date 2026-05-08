# 自訂模型接入指南

本指南說明如何把任意一個本地推論模型包裝成可被 **OpenAI Python SDK** 直接呼叫的服務。

---

## 概念：你只需做這兩件事

```
                你寫的部份                 框架自動處理
┌─────────────────────────────┐    ┌──────────────────────────────────┐
│  class MyModel(ChatModel):  │    │  POST /v1/chat/completions       │
│                             │    │  SSE 格式（data: {...}\n\n）     │
│    def __init__(self):      │ →  │  GET /v1/models                  │
│        # 載入模型            │    │  OpenAI JSON schema              │
│                             │    │  stream / non-stream 切換        │
│    def create(self, ...):   │    │  CLI、ComfyUI 節點               │
│        yield token          │    └──────────────────────────────────┘
└─────────────────────────────┘
```

`__init__` 負責**載入模型**，`create` 負責**推論並 yield 文字**。其餘全部不用管。

---

## 快速開始：5 分鐘接入一個純文字模型

```python
# models/igpu/my_model.py
from core.module import ChatModel
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

class MyModel(ChatModel):
    model_id    = "mistralai/Mistral-7B-Instruct-v0.3"   # HuggingFace ID
    description = "Mistral 7B on iGPU"

    def __init__(self):
        self.tok   = AutoTokenizer.from_pretrained(self.model_id)
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_id, dtype=torch.bfloat16, device_map="auto"
        )
        self.model.eval()
        self.device = str(next(self.model.parameters()).device)  # "cuda:0" 等

    def create(self, messages, max_tokens=200):
        prompt = self.tok.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        ids    = self.tok(prompt, return_tensors="pt").to(self.device)
        out    = self.model.generate(**ids, max_new_tokens=max_tokens)
        text   = self.tok.decode(out[0][ids["input_ids"].shape[-1]:], skip_special_tokens=True)
        yield text   # 一次 yield 完整回答（非串流後端的標準做法）
```

```python
# deployment/my_machine/serve.py
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parents[2]))

from models.igpu.my_model import MyModel
from interfaces.serve import serve

serve(MyModel(), port=8000)
```

```python
# 客戶端（任意機器）
from openai import OpenAI
client = OpenAI(base_url="http://localhost:8000/v1", api_key="local")

resp = client.chat.completions.create(
    model="mistralai/Mistral-7B-Instruct-v0.3",
    messages=[{"role": "user", "content": "你好"}],
)
print(resp.choices[0].message.content)
```

---

## `create()` 的兩種寫法

### 寫法 A — 一次 yield（適合不支援串流的後端）

```python
def create(self, messages, max_tokens=200):
    result = self.model.run(messages)  # subprocess / ONNX / 任何同步後端
    yield result                       # 整段文字 yield 一次
```

客戶端 `stream=False` → 看到完整回答  
客戶端 `stream=True`  → 看到一次性出現的完整文字（不是逐字）

### 寫法 B — 逐 token yield（適合 HuggingFace 串流）

```python
from threading import Thread
from transformers import TextIteratorStreamer

def create(self, messages, max_tokens=200):
    inputs   = self._prepare(messages)
    streamer = TextIteratorStreamer(self.tok, skip_prompt=True, skip_special_tokens=True)
    thread   = Thread(target=self.model.generate,
                      kwargs={**inputs, "max_new_tokens": max_tokens, "streamer": streamer})
    thread.start()
    for chunk in streamer:
        if chunk:
            yield chunk          # 每個 token 立即輸出
    thread.join()
```

客戶端 `stream=False` → 框架自動 `"".join()` 收集  
客戶端 `stream=True`  → 每個 token 實時輸出

> **選哪個**：後端支援串流就用 B；NPU / subprocess / ONNX 用 A。

---

## 接入多模態 VLM（支援圖片）

宣告 `supports_vision = True`，然後在 `create()` 裡用內建的 `parse_content()` helper 提取圖片：

```python
from core.module import ChatModel
from transformers import AutoProcessor, AutoModelForImageTextToText
from threading import Thread
from transformers import TextIteratorStreamer
import torch

class MyVLM(ChatModel):
    model_id        = "google/gemma-4-E4B-it"
    description     = "Vision-Language Model on iGPU"
    supports_vision = True                         # ← 宣告支援圖片

    def __init__(self):
        self.processor = AutoProcessor.from_pretrained(self.model_id)
        self.model     = AutoModelForImageTextToText.from_pretrained(
            self.model_id, dtype=torch.bfloat16, device_map="auto"
        )
        self.model.eval()
        self.device = str(next(self.model.parameters()).device)

    def create(self, messages, max_tokens=200):
        inputs   = self._build_inputs(messages)
        streamer = TextIteratorStreamer(
            self.processor.tokenizer, skip_prompt=True, skip_special_tokens=True
        )
        thread = Thread(
            target=self.model.generate,
            kwargs={**inputs, "max_new_tokens": max_tokens, "streamer": streamer}
        )
        with torch.inference_mode():
            thread.start()
        for chunk in streamer:
            if chunk:
                yield chunk
        thread.join()

    def _build_inputs(self, messages):
        # 把每條 message 的 content 標準化為 list-of-parts 格式
        normalised = []
        for m in messages:
            content = m["content"]
            if isinstance(content, str):
                content = [{"type": "text", "text": content}]
            # image_url parts 直接保留給 processor（它自己解 base64）
            normalised.append({"role": m["role"], "content": content})

        inputs = self.processor.apply_chat_template(
            normalised, add_generation_prompt=True,
            tokenize=True, return_tensors="pt", return_dict=True,
        )
        return {k: v.to(self.device) for k, v in inputs.items()}
```

### 客戶端發送圖片

```python
import base64
from openai import OpenAI

client  = OpenAI(base_url="http://localhost:8000/v1", api_key="local")
img_b64 = base64.b64encode(open("photo.jpg", "rb").read()).decode()

resp = client.chat.completions.create(
    model="google/gemma-4-E4B-it",
    messages=[{
        "role": "user",
        "content": [
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}},
            {"type": "text",      "text": "這張圖片裡有什麼？"},
        ]
    }],
)
print(resp.choices[0].message.content)
```

---

## 接入 NPU 模型（subprocess 呼叫）

NPU 環境無法直接 import HuggingFace，需透過 subprocess 呼叫：

```python
import subprocess
from core.module import ChatModel

class MyNpuModel(ChatModel):
    model_id    = "my-npu-model"
    description = "LLM on AMD NPU via subprocess"

    def __init__(self, model_dir: str = "/path/to/onnx/model"):
        self.model_dir = model_dir
        self.device    = "npu"
        # 不需要載入模型物件，subprocess 會自己管理

    def create(self, messages, max_tokens=200):
        # 把最後一條 user message 取出
        prompt = next(
            m["content"] for m in reversed(messages) if m["role"] == "user"
        )
        result = subprocess.run(
            ["python", "model_chat.py",
             "--model-dir", self.model_dir,
             "--prompt",    prompt,
             "--max-tokens", str(max_tokens)],
            capture_output=True, text=True
        )
        yield result.stdout.strip()   # 一次 yield
```

---

## `parse_content()` helper — 處理多模態 content

當 `content` 可能是 `str` 或 `list`（圖片 + 文字混合）時，使用內建 helper：

```python
def create(self, messages, max_tokens=200):
    for msg in messages:
        text, images = self.parse_content(msg["content"])
        # text:   str — 所有文字 parts 合併
        # images: list[PIL.Image] — 所有圖片解碼後的 PIL Image 物件
```

helper 會自動：
- 處理 `content: str`（直接回傳，images 為空）
- 拆解 `content: list` 中的 `text` 和 `image_url` parts
- 解碼 `data:image/jpeg;base64,...` 為 PIL Image（`.convert("RGB")` 已呼叫）

---

## `ChatModel` class variables 完整清單

| 名稱 | 型別 | 是否必填 | 說明 |
|------|------|----------|------|
| `model_id` | `str` | **必填** | HuggingFace ID 或本地路徑；對應 OpenAI response 的 `"model"` 欄位 |
| `description` | `str` | 選填，預設 `""` | 出現在 `GET /v1/models` 回應中 |
| `supports_vision` | `bool` | 選填，預設 `False` | `True` 時 CLI 會開放 `--image` 參數；ComfyUI 節點會新增圖片輸入埠 |

`self.device` 是 **instance attribute**（不是 class variable），在 `__init__` 內設定：

```python
def __init__(self):
    ...
    self.device = str(next(self.model.parameters()).device)  # "cuda:0", "cpu", "npu"
```

---

## 常見錯誤

| 錯誤 | 原因 | 修正 |
|------|------|------|
| `NotImplementedError` | 忘記實作 `__init__` 或 `create` | 確認兩個方法都有覆寫 |
| `create()` 不是 generator | 用了 `return` 而非 `yield` | 改成 `yield result` |
| 客戶端 422 error | 傳了圖片但 `Message.content` 是 `str` 型別 | 確認 `interfaces/api.py` 已改為 `Union[str, list]` |
| 圖片解碼失敗 | 直接傳 PIL Image 到 processor | 要先 `parse_content()` 解碼，或讓 processor 接受 base64 |
| `model_id` 未定義 | 繼承但忘記宣告 class variable | 在 class body 加上 `model_id = "..."` |
| streaming 在 `stream=False` 時也很慢 | 用了 Pattern B 但 Pattern A 就夠 | NPU/subprocess 用 Pattern A（`yield result`） |
