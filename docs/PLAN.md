# ChatModel 設計規劃

> **核心比喻**：就像 PyTorch 的 `nn.Module`——  
> 你只需繼承、實作 `__init__`（載入模型）和 `create`（推論邏輯），  
> 其餘的 SSE 格式化、OpenAI JSON 包裝、路由、CLI 全部自動處理。  
>
> **命名對齊 OpenAI SDK**：方法名稱 `create()` 直接對應  
> `client.chat.completions.create(messages=..., stream=...)`。

---

## 1. 設計哲學：對比 nn.Module 與 OpenAI SDK

```python
# PyTorch 的方式
class MyNet(nn.Module):
    def __init__(self):
        super().__init__()
        self.linear = nn.Linear(10, 1)   # 宣告結構

    def forward(self, x): ...            # 定義計算（框架呼叫）
```

```python
# OpenAI SDK 的呼叫方式（客戶端）
client.chat.completions.create(messages=[...], stream=True)
#                      ^^^^^^  ← 這個方法名稱就是我們的錨點
```

```python
# 我們的方式：命名與 OpenAI create() 對齊
class MyModel(ChatModel):
    description = "my model"             # 宣告驅動器描述（class body）

    def __init__(self, model_id: str):
        self.model_id = model_id         # ← instance attr，傳入時決定
        self.model = load_weights(...)   # 載入模型

    def create(self, messages, max_tokens=200):
        yield self.model.infer(...)      # 推論邏輯，永遠 yield

# serve(MyModel("org/my-model")) → 自動處理 SSE、OpenAI JSON、路由、CLI
```

**對應關係**：

| PyTorch `nn.Module` | OpenAI SDK | 我們的 `ChatModel` |
|---------------------|------------|-------------------|
| `__init__` — 定義 layers | — | `__init__` — 載入模型 |
| `forward(x)` — 定義計算 | `create(messages, stream)` | `create(messages, max_tokens)` |
| `nn.Module.__call__` | SDK HTTP layer | `serve()` — SSE / JSON 包裝 |
| `model.to(device)` | — | `__init__` 內設定 `self.device` |

---

## 2. `ChatModel` 基底類別（`core/module.py`）

```python
# core/module.py
from __future__ import annotations

from typing import ClassVar, Iterator


class ChatModel:
    """
    Base class for all LLM/VLM inference backends.

    Naming follows OpenAI SDK:
      - create()  ←→  client.chat.completions.create()
      - model_id  ←→  the "model" field in OpenAI requests/responses

    Subclass contract — implement exactly two things:
      1. __init__:  load weights, processor, tokenizer.
                    set self.device after loading.
      2. create():  inference logic. Always yield str chunks.
                    For non-streaming backends: yield the whole text once.

    Usage:
        class IgpuVisionLm(ChatModel):
            description     = "iGPU VisionLM via HuggingFace transformers"
            supports_vision = True

            def __init__(self, model_id: str, device_map: str = "auto"):
                self.model_id = model_id     # ← instance attr，每次載入可指定不同模型
                self.model = load_weights(model_id, device_map)
                self.device = "cuda:0"

            def create(self, messages, max_tokens=200):
                for token in self.model.stream(messages):
                    yield token

        serve(IgpuVisionLm("google/gemma-4-E4B-it"))
    """

    # ── 驅動器描述 — 宣告在 class body（ClassVar，描述驅動器能力）────────────
    description:     ClassVar[str]  = ""
    supports_vision: ClassVar[bool] = False

    # ── model_id — 在 __init__ 內設定 self.model_id ─────────────────────────
    # 不用 ClassVar：同一個驅動器可載入不同的模型權重
    # api.py 用 svc.model_id 回報 OpenAI "model" 欄位
    model_id: str = ""

    # ── 子類別必須實作的兩個方法 ──────────────────────────────────────────────

    def __init__(self) -> None:
        """Load model weights, processor, tokenizer. Set self.device."""
        raise NotImplementedError

    def create(
        self,
        messages: list[dict],
        max_tokens: int = 200,
    ) -> Iterator[str]:
        """
        Inference logic. Always yield str chunks.

        messages format (OpenAI-compatible):
            [{"role": "user",   "content": "text"},
             {"role": "user",   "content": [          # multimodal
                 {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,..."}},
                 {"type": "text",      "text": "describe this"}
             ]},
             {"role": "assistant", "content": "..."}]

        Streaming backend:  yield token by token.
        Non-streaming:      yield the full text once — still valid.
        """
        raise NotImplementedError

    # ── Built-in helper — subclasses may use but not override ───────────────

    @staticmethod
    def parse_content(content: str | list) -> tuple[str, list]:
        """
        Extract (text: str, images: list[PIL.Image]) from OpenAI content.
        Handles plain str and content-part list. Decodes base64 data URIs.
        """
        if isinstance(content, str):
            return content, []

        import base64
        from io import BytesIO
        from PIL import Image

        texts, images = [], []
        for part in content:
            if part.get("type") == "text":
                texts.append(part["text"])
            elif part.get("type") == "image_url":
                url: str = part["image_url"]["url"]
                if url.startswith("data:"):
                    b64 = url.split(",", 1)[1]
                    images.append(
                        Image.open(BytesIO(base64.b64decode(b64))).convert("RGB")
                    )
        return " ".join(texts), images
```

### 設計要點

| 決策 | 理由 |
|------|------|
| 方法名稱 `create()` | 直接對應 `client.chat.completions.create()` |
| 永遠 `yield`（generator） | `api.py` 對串流直接 pipe；非串流用 `"".join()` 收集，無需 magic 偵測 |
| 無 `stream` 參數 | `create()` 的 stream/非stream 由 `api.py` 決定，不應洩漏進模型邏輯 |
| 無 `__call__` 覆寫 | `api.py` 直接呼叫 `model.create()`，行為透明 |
| `model_id` 在 class body | 不用 dataclass，不用 `__init__` 內建立物件，一行宣告 |
| `parse_content` 是 static helper | 複用邏輯，不強迫繼承，也可獨立匯入 |
| `model_id` 是 instance attr | 同一驅動器可載不同模型；`description` 才是 ClassVar |

---

## 3. `create()` 實作模式

### Pattern A — yield 一次（非串流後端）

```python
def create(self, messages, max_tokens=200):
    inputs = self._prepare(messages)
    output = self.model.run(inputs)               # subprocess / ONNX / 等
    yield output                                  # 整段文字 yield 一次
```

- 適合：NPU subprocess、ONNX Runtime 無串流支援的後端
- `api.py` 的非串流呼叫方 `"".join(...)` 得到完整文字
- `api.py` 的串流呼叫方得到單一 chunk，使用者看到「瞬間出現」

### Pattern B — yield token（原生串流，推薦）

```python
def create(self, messages, max_tokens=200):
    inputs = self._prepare(messages)
    streamer = TextIteratorStreamer(self.tokenizer, skip_special_tokens=True)
    thread = Thread(
        target=self.model.generate,
        kwargs={**inputs, "max_new_tokens": max_tokens, "streamer": streamer}
    )
    thread.start()
    for chunk in streamer:
        if chunk:
            yield chunk
    thread.join()
```

- 適合：HuggingFace `TextIteratorStreamer`
- 非串流請求：`api.py` 用 `"".join()` 收集，仍需等全部生成完

| | Pattern A | Pattern B |
|--|-----------|-----------|
| 實作難度 | 簡單 | 需要 threading |
| stream 延遲 | 高（全部生成才顯示） | 低（首 token 即輸出） |
| non-stream 效能 | 相同 | 相同（join 無額外開銷） |

---

## 4. `api.py` 如何使用 `ChatModel`

```python
# interfaces/api.py — 完整呼叫邏輯（無 magic 偵測）

if req.stream:
    # create() 是 generator → 直接 pipe 進 SSE
    return StreamingResponse(
        _sse_wrap(svc, messages, req.max_tokens),
        media_type="text/event-stream",
    )
else:
    # "".join() 收集所有 chunk → 回傳完整 JSON
    text = "".join(svc.create(messages, max_tokens=req.max_tokens))
    return _completion_response(svc.model_id, text)


def _sse_wrap(svc, messages, max_tokens):
    cid = f"chatcmpl-{uuid.uuid4().hex}"
    ts  = int(time.time())
    for chunk in svc.create(messages, max_tokens=max_tokens):
        yield f"data: {json.dumps({...})}\n\n"
    yield f"data: {json.dumps({...finish_reason: stop...})}\n\n"
    yield "data: [DONE]\n\n"
```

`api.py` 呼叫 `svc.create()` 一次，根據 `req.stream` 決定如何消費 generator。  
**`ChatModel` 不需要知道 SSE、JSON schema 或 `stream` flag 的任何細節。**

---

## 5. 基礎設施函式

```python
# interfaces/serve.py
def serve(model: ChatModel, host: str = "0.0.0.0", port: int = 8000) -> None:
    app = _build_app(model)
    uvicorn.run(app, host=host, port=port)

# interfaces/cli.py
def cli(model: ChatModel) -> None: ...

# interfaces/comfyui.py
def make_comfyui_node(model: ChatModel) -> type: ...
```

---

## 6. Gemma4 改寫對照

### 現況（`LLMService` ABC）

```python
class Gemma4Service(LLMService):
    def __init__(self, model_id, device_map):
        self.info = ModelInfo(model_id=..., name=..., ...)   # ← 多餘 dataclass

    def generate(self, messages, max_new_tokens): ...        # ← 方法一
    def generate_stream(self, messages, max_new_tokens): ... # ← 方法二（幾乎一樣）
```

### 改後（`ChatModel`，統一命名規則）

```python
# models/igpu/vision_lm.py
class IgpuVisionLm(ChatModel):
    description     = "iGPU VisionLM via HuggingFace transformers (ROCm / CUDA)"
    supports_vision = True

    def __init__(self, model_id: str, device_map: str = "auto"):
        self.model_id  = model_id                                   # ← instance attr
        self.processor = AutoProcessor.from_pretrained(model_id)
        self.model = AutoModelForImageTextToText.from_pretrained(
            model_id, dtype=torch.bfloat16, device_map=device_map
        )
        self.model.eval()
        self.device = str(next(self.model.parameters()).device)

    def create(self, messages, max_tokens=200):
        inputs = self._build_inputs(messages)
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
```

用法：`IgpuVisionLm("google/gemma-4-E4B-it")`  或  `IgpuVisionLm("llava-hf/llava-1.5-7b-hf")`

**改動量**：移除 `generate()`、`generate_stream()`、`ModelInfo`；class 名稱 `Gemma4Service` → `IgpuVisionLm`；`model_id` 從 class var 改為 instance attr；`max_new_tokens` → `max_tokens`。推論邏輯零改動。

---

## 7. 與現況的差異對照

| | 現況（`LLMService`） | 新設計（`ChatModel`） |
|--|----------------------|----------------------|
| 基底類別名稱 | `LLMService` | `ChatModel` — 對應 OpenAI chat API |
| 驅動器命名 | `Gemma4Service`、`OnnxLLMService` | `IgpuVisionLm`、`NpuTextLm` — 統一規則 |
| 必須實作 | `generate` + `generate_stream` | `create` — 一個方法 |
| 方法名稱 | `generate` / `generate_stream` | `create` — 對應 `completions.create()` |
| 串流/非串流 | 兩個方法 | 同一個 generator，呼叫端 `join` 或 `pipe` |
| `stream` 參數 | 無（靠兩個方法區分） | 無（由 `api.py` 決定如何消費） |
| `model_id` | `ModelInfo.model_id` dataclass field | `self.model_id` — `__init__` 內設定 |
| 驅動器描述 | `ModelInfo` dataclass | `description`、`supports_vision` class var |
| token 參數名 | `max_new_tokens` | `max_tokens` — 與 OpenAI 一致 |

---

## 8. 命名規則（嚴格統一）

### 兩層架構

`models/` 下分兩層：

```
第一層（通用驅動器）：{Hardware}{Modality}   ← 描述「用什麼硬體跑什麼類型」
第二層（模型特定）  ：{ModelName}             ← 描述「是什麼模型」，繼承第一層
```

**hardware 由「目錄」表達**，因此第二層類別名稱不需要加 `Igpu`/`Npu` 前綴：

```python
# models/igpu/gemma3_4b_mm.py
class Gemma3_4bMm(IgpuVisionLm):    # 目錄已表達 igpu，名稱只寫模型
    ...

# models/npu/gemma3_4b_mm_onnx.py
class Gemma3_4bMmOnnx(NpuVisionLm): # 目錄已表達 npu，加 Onnx 後綴區分 backend
    ...
```

### 命名規則表

| 層次 | 規則 | 範例 |
|------|------|------|
| ABC 基底 | `ChatModel` | `core/module.py` |
| 第一層（通用驅動器） | `{Hardware}{Modality}` PascalCase | `IgpuVisionLm`、`NpuTextLm` |
| 第一層檔案 | `base.py`（存放第一層通用驅動器） | `models/igpu/base.py` |
| 第二層（模型特定） | `{ModelName}` PascalCase，繼承第一層 | `Gemma3_4bMm`、`Phi4Mini` |
| 第二層檔案 | `{model_name}.py` snake\_case | `gemma3_4b_mm.py` |
| 驅動器目錄 | 硬體名稱小寫 | `models/igpu/`、`models/npu/` |
| 後綴禁止 | ❌ `Service` ❌ `LLM`（全大寫縮寫）| ✅ `Lm`（首字大寫縮寫）|

### 第一層：四種通用驅動器

```
{Hardware}  ∈  { Igpu, Npu }
{Modality}  ∈  { TextLm, VisionLm }
```

| 類別 | 檔案 | 目錄 | 底層技術 |
|------|------|------|---------|
| `IgpuVisionLm` | `base.py` | `models/igpu/` | `AutoModelForImageTextToText` (ROCm) |
| `IgpuTextLm`   | `base.py` | `models/igpu/` | `AutoModelForCausalLM` (ROCm) |
| `NpuTextLm`    | `base.py` | `models/npu/`  | AMD `model_chat.py` subprocess |
| `NpuVisionLm`  | `base.py` | `models/npu/`  | AMD `vlm_run.py` subprocess |

### 第二層：模型特定類別（按需建立）

```python
# models/igpu/gemma3_4b_mm.py — 只有在模型有特殊邏輯時才建立
class Gemma3_4bMm(IgpuVisionLm):
    description = "Gemma 3 4B IT multimodal (iGPU)"

    def __init__(self, model_id: str = "google/gemma-3-4b-it", **kw):
        super().__init__(model_id, **kw)
        # patch chat template 或其他模型特定設定 ...

# models/npu/gemma3_4b_mm_onnx.py
class Gemma3_4bMmOnnx(NpuVisionLm):
    description = "Gemma 3 4B IT multimodal ONNX (NPU)"

    def __init__(self, model_dir: str = "./Gemma-3-4b-it-mm-onnx-ryzenai-npu", **kw):
        super().__init__(model_dir, **kw)
```

**若模型無特殊需求，直接在 deployment 用第一層，不需建第二層檔案：**

```python
# deployment/vivobook_s_15_16/serve.py
from models.igpu.base import IgpuVisionLm
serve(IgpuVisionLm("google/gemma-4-E4B-it"))   # 直接用，不需要 gemma4.py
```

### 廢棄對照

| 舊名 | 新名（第一層） | 廢棄原因 |
|------|--------------|---------|
| `LLMService` | `ChatModel` | 舊 ABC；混用 LLM/VLM 不一致 |
| `Gemma4Service` | `IgpuVisionLm` / `Gemma3_4bMm` | 混用模型名稱與驅動器角色 |
| `OnnxLLMService` | `NpuTextLm` | 混用技術名（Onnx）與類型（LLM） |
| `ModelInfo` dataclass | class variables | 移進 class body，一行宣告 |
| `model_id: ClassVar[str]` | `self.model_id = model_id` | 同一驅動器可載不同模型 |

---

## 9. 完整目錄結構

```
amd-ryzen-ai-benchmark/
│
├── core/
│   └── module.py                    # ChatModel ABC（新）
│
├── models/
│   ├── igpu/
│   │   ├── __init__.py
│   │   ├── base.py                  # IgpuVisionLm, IgpuTextLm — 第一層通用驅動器
│   │   └── gemma3_4b_mm.py          # Gemma3_4bMm(IgpuVisionLm) — 第二層，有特殊邏輯才建
│   └── npu/
│       ├── __init__.py
│       ├── base.py                  # NpuTextLm, NpuVisionLm   — 第一層通用驅動器
│       ├── gemma3_4b_mm_onnx.py     # Gemma3_4bMmOnnx(NpuVisionLm) — 第二層
│       ├── phi4_mini.py             # Phi4Mini(NpuTextLm)          — 第二層
│       └── lfm2_2_6b.py             # Lfm2_2_6b(NpuTextLm)         — 第二層
│
├── interfaces/
│   ├── api.py                       # build_app(model: ChatModel) — 修正 content 型別
│   ├── cli.py                       # cli(model: ChatModel)       — 新增 --image
│   └── comfyui.py                   # make_comfyui_node(model: ChatModel)
│
├── deployment/
│   ├── vivobook_s_15_16/
│   │   ├── serve.py                 # IgpuVisionLm("google/gemma-4-E4B-it")  ← 第一層直用
│   │   └── cli.py
│   └── PN54/
│       ├── serve.py                 # Phi4Mini() 或 NpuTextLm(model_dir)     ← 視需要
│       └── vlm.py                   # Gemma3_4bMmOnnx() 或 NpuVisionLm(...)
│
└── weights/                         # .gitignored — NPU 模型權重目錄
    ├── Llama-3.2-3B-Instruct_.../
    ├── Phi-4-mini-instruct_.../
    └── Gemma-3-4b-it-mm-onnx_.../
```

### 決策樹：何時建第二層檔案？

```
這個模型需要接入嗎？
├─ 是 → 通用驅動器能直接用嗎？（inputs 建構方式、預設 model_id 等）
│       ├─ 能 → 直接在 deployment serve.py 用第一層 ← 不建第二層
│       └─ 不能（chat template patch、特殊 processor...）
│               └─ 在 models/{hw}/{model_name}.py 建第二層類別
└─ 否 → 略過
```

### 需要刪除的舊檔案

| 路徑 | 原因 |
|------|------|
| `serve.py`（root） | 舊進入點，被 `deployment/` 取代 |
| `cli.py`（root） | 舊進入點 |
| `gemma4_api.py`（root） | 廢棄草稿 |
| `gemma4_service.py`（root） | 廢棄草稿 |
| `models/gemma4.py` | 廢棄草稿 |
| `core/base.py` | 被 `core/module.py` 取代 |

### 需要改名/改寫的檔案

| 舊路徑 | 新路徑 | 改動 |
|--------|--------|------|
| `models/igpu/gemma4.py` | `models/igpu/base.py` | 類別 `Gemma4Service` → `IgpuVisionLm`，改為通用驅動器 |
| `models/npu/onnx_llm.py` | `models/npu/base.py` | 類別 `OnnxLLMService` → `NpuTextLm`、`NpuVisionLm`，改為通用驅動器 |

---

*規劃日期：2026-05-08*

