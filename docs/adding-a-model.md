# 新增模型模組指引

本指引說明如何在 `ryzenai/modules/` 下新增模型，使其能夠透過 `cli.py` 與 `api.py` 立即可用。整個過程不需要修改框架核心（`model/`、`backend/`、`conversation/`、`session/`）。

---

## 概念說明

`ryzenai/modules/` 是框架唯一的**擴充點**。每個模組代表一個具體的「模型 × 後端」組合，例如：

- `Gemma3_4B_NPU` = Gemma3 4B 權重 × VitisAI EP（NPU）
- `Gemma4_E4B_GPU` = Gemma4 E4B 權重 × PyTorch ROCm（iGPU）

框架其餘部分完全不感知模型細節；`cli.py` 與 `api.py` 透過 `_build_model()` registry 取得已初始化的模型物件後，統一以 `model(context)` 觸發推論。

```
你要做的事                    框架自動處理
──────────────────────        ─────────────────────────────────
繼承 Text2Text / ImageText2Text
實作 generate()           →   cli.py / api.py 的串流消費
登錄至 registry           →   ConversationContext 管理 (session/)
                          →   OpenAI API 格式轉換 (api.py)
                          →   SSE 串流協定 (api.py)
```

---

## 步驟一：確認基底類別

| 情境 | 繼承自 |
|------|--------|
| 純文字輸入 / 文字輸出（LLM） | `Text2Text` |
| 影像 + 文字輸入 / 文字輸出（VLM） | `ImageText2Text` |

如果模型支援圖片輸入，選 `ImageText2Text`；否則選 `Text2Text`。兩者目前均為語義標記類別（無新方法），差異僅在型別標註，未來可用於路由與型別檢查。

---

## 步驟二：建立模組檔案

在 `ryzenai/modules/` 下新增一個 Python 檔案，命名慣例：`<model_shortname>_<backend_shortname>.py`，全小寫加底線。

```
ryzenai/modules/
├── gemma3_4b_npu.py      ← 已有
├── gemma4_e4b_gpu.py     ← 已有
└── your_model_here.py    ← 新增於此
```

---

## 步驟三：實作模組

以下為最小可執行的模組骨架，分兩種情境說明。

### 情境 A：ONNX Runtime GenAI（NPU / DirectML GPU）

```python
# ryzenai/modules/your_model_npu.py
import onnxruntime_genai as og
from typing import Generator

from ryzenai.model import ImageText2Text   # 或 Text2Text
from ryzenai.backend.onnx import ONNXVitisAIBackend  # 或 ONNXDirectMLBackend
from ryzenai.conversation import ConversationContext


class YourModelNPU(ImageText2Text):
    """簡短描述：模型名稱 — 推論後端（硬體）"""

    def __init__(self, model_dir: str) -> None:
        super().__init__(ONNXVitisAIBackend())       # 在此驗證 EP 可用性
        self._og_model = og.Model(model_dir)
        self._processor = og.MultiModalProcessor(self._og_model)  # VLM 用；LLM 改用 og.Tokenizer

    def generate(self, context: ConversationContext) -> Generator[str, None, None]:
        text, images = _parse_context(context)

        # ── 在此呼叫 onnxruntime_genai 推論 ──────────────────────────────────
        # 參考：https://onnxruntime.ai/docs/genai/
        # 建議步驟：
        #   1. 用 self._processor 將 text/images 編碼為 inputs
        #   2. 呼叫 og.Generator 並逐步 yield token
        raise NotImplementedError("TODO: 待個別模型測試後實作")
```

### 情境 B：HuggingFace Transformers（PyTorch ROCm iGPU）

```python
# ryzenai/modules/your_model_gpu.py
from transformers import AutoProcessor, AutoModelForImageTextToText, TextIteratorStreamer
from threading import Thread
from typing import Generator

from ryzenai.model import ImageText2Text   # 或 Text2Text + AutoModelForCausalLM
from ryzenai.backend.pytorch import PyTorchROCmBackend
from ryzenai.conversation import ConversationContext


class YourModelGPU(ImageText2Text):
    """簡短描述：模型名稱 — HuggingFace Transformers + PyTorch ROCm（iGPU）"""

    def __init__(self, model_id: str) -> None:
        super().__init__(PyTorchROCmBackend())       # 在此驗證 CUDA/ROCm 可用性
        self._processor = AutoProcessor.from_pretrained(model_id)
        self._hf_model = AutoModelForImageTextToText.from_pretrained(
            model_id, device_map="cuda"
        )

    def generate(self, context: ConversationContext) -> Generator[str, None, None]:
        text, images = _parse_context(context)

        # ── 在此呼叫 HuggingFace 推論 ────────────────────────────────────────
        # 建議步驟：
        #   1. self._processor.apply_chat_template() 建立 inputs
        #   2. 建立 TextIteratorStreamer，以 Thread 執行 model.generate()
        #   3. for token in streamer: yield token
        raise NotImplementedError("TODO: 待個別模型測試後實作")
```

### `_parse_context()` — 從 ConversationContext 萃取輸入

兩種情境均需解析 `context.messages`。以下輔助函式實作 **DESIGN.md Section 3.1** 的解析規則，可直接複製至模組中或抽取至 `ryzenai/modules/_utils.py`：

```python
import base64
from io import BytesIO
from PIL import Image
from ryzenai.conversation import ConversationContext

def _parse_context(context: ConversationContext) -> tuple[list[dict], list[Image.Image]]:
    """
    將 ConversationContext 轉換為 (messages_for_sdk, images) 兩份資料。

    messages_for_sdk: [{"role": "user", "content": "..."}, ...]  ← 傳入 chat_template
    images:           [PIL.Image, ...]                            ← 傳入 processor
    """
    messages_for_sdk: list[dict] = []
    images: list[Image.Image] = []

    for msg in context.messages:
        if isinstance(msg.content, str):
            messages_for_sdk.append({"role": msg.role, "content": msg.content})
        else:
            # list[dict]，每個 dict 含 "type" 欄位
            text_parts: list[str] = []
            for part in msg.content:
                if part["type"] == "text":
                    text_parts.append(part["text"])
                elif part["type"] == "image_url":
                    url: str = part["image_url"]["url"]
                    # 僅支援 base64 data URI：data:image/<ext>;base64,<data>
                    header, b64data = url.split(",", 1)
                    images.append(Image.open(BytesIO(base64.b64decode(b64data))))
            messages_for_sdk.append({"role": msg.role, "content": " ".join(text_parts)})

    return messages_for_sdk, images
```

> **注意**：`messages_for_sdk` 的 `content` 格式（純字串 vs. list）因 SDK 而異。
> `onnxruntime_genai` 通常需要單一字串；`transformers` 的 `apply_chat_template` 可接受 list。
> 請依照各 SDK 的文件調整 `_parse_context()` 的輸出格式。

---

## 步驟四：登錄至 registry

`api.py` 與 `cli.py` 各自有一個 `_build_model()` 函式作為組合根，新增模型只需在兩個檔案的 `registry` dict 各加一行：

```python
# api.py 與 cli.py 的 _build_model() 中
from ryzenai.modules.your_model_npu import YourModelNPU  # 新增 import

registry = {
    "gemma3-npu": lambda: Gemma3_4B_NPU("weights/Gemma-3-4b-it-mm-onnx-ryzenai-npu"),
    "gemma4-gpu": lambda: Gemma4_E4B_GPU("google/gemma-4-E4B-it"),
    "your-model": lambda: YourModelNPU("weights/your-model-dir"),  # ← 新增這行
}
```

登錄後，模型立即可透過以下方式使用，無需其他改動：

```powershell
# CLI
python cli.py --model your-model --prompt "Hello"

# API server
python api.py --model your-model
```

---

## 步驟五：更新 `ryzenai/modules/__init__.py`

將新類別加入公開介面，以保持 `from ryzenai.modules import ...` 的一致性：

```python
# ryzenai/modules/__init__.py
from ryzenai.modules.gemma3_4b_npu import Gemma3_4B_NPU
from ryzenai.modules.gemma4_e4b_gpu import Gemma4_E4B_GPU
from ryzenai.modules.your_model_npu import YourModelNPU   # ← 新增

__all__ = ["Gemma3_4B_NPU", "Gemma4_E4B_GPU", "YourModelNPU"]  # ← 新增
```

---

## 參考：`generate()` 契約

實作 `generate()` 時必須遵守以下契約，框架其餘部分依賴這些不變式：

| 項目 | 規範 |
|------|------|
| **輸入** | `context: ConversationContext`，包含完整多輪對話歷史 |
| **輸出** | `Generator[str, None, None]`，以 `yield` 逐步產出 token 字串（非整句） |
| **串流** | 必須逐 token yield，不可一次性回傳完整字串（`cli.py` 與 `api.py` 依賴串流） |
| **例外** | 推論失敗時拋出具體例外；不可靜默忽略錯誤 |
| **狀態** | `generate()` 本身無狀態；多輪歷史已由 `InteractiveSession` 維護於 `context.messages` |

---

## 參考：可用 Backend

| Backend 類別 | Conda 環境 | 硬體 | 驗證方式 |
|-------------|-----------|------|---------|
| `ONNXVitisAIBackend` | `ryzen-ai-1.7.1` | NPU (XDNA) | `VitisAIExecutionProvider` in `ort.get_available_providers()` |
| `ONNXDirectMLBackend` | `ryzen-ai-1.7.1` | GPU (DirectML) | `DmlExecutionProvider` in `ort.get_available_providers()` |
| `PyTorchROCmBackend` | `rocm-pytorch` | iGPU (RDNA / ROCm) | `torch.cuda.is_available()` |

Backend 在 `__init__` 中自動驗證環境，若環境不符則拋出 `RuntimeError`，無需在模組內重複驗證。

---

## 快速檢查清單

新增模型完成後，請確認：

- [ ] 模組檔案置於 `ryzenai/modules/your_model.py`
- [ ] 繼承正確的基底類別（`Text2Text` 或 `ImageText2Text`）
- [ ] `super().__init__(<Backend>())` 已呼叫
- [ ] `generate()` 回傳 `Generator[str, None, None]`（以 `yield` 產出 token）
- [ ] `ryzenai/modules/__init__.py` 已加入新類別的 import 與 `__all__`
- [ ] `api.py` 的 `_build_model()` registry 已登錄
- [ ] `cli.py` 的 `_build_model()` registry 已登錄
