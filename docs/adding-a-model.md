# 新增模型模組指引

本文件說明如何在這個框架中新增一個模型，讓它能夠透過命令列（`cli.py`）與 REST API（`api.py`）直接被呼叫使用。

完成後，你不需要動到任何框架核心程式碼。所有工作都集中在 `ryzenai/modules/` 資料夾和 `ryzenai/registry.py` 的一行登錄。

---

## 閱讀前的心理準備：框架是怎麼運作的？

在開始之前，花兩分鐘理解框架的設計思路，後面的步驟就會變得非常直觀。

這個框架採用「插件式」設計：框架本身負責管理對話歷史、SSE 串流格式、API 路由等「膠水工作」，而**每個模型模組只負責一件事——把一段對話輸入，變成逐字輸出的文字串流**。

具體來說，當使用者執行 `python cli.py --model gemma3-4b-npu --prompt "你好"` 時，框架內部的流程是這樣的：

```
使用者輸入
  │
  ▼
ryzenai/registry.py 的 build_model()  ← 你要在這裡登錄你的模型
  │  根據 --model 名稱，初始化對應的模組類別
  ▼
InteractiveSession / SingleSession      ← 框架管理對話歷史（你不需要動這裡）
  │  將對話歷史打包成 ConversationContext
  ▼
你實作的 YourModel.generate(context)   ← 你只需要實作這個函式
  │  逐字 yield token
  ▼
cli.py 的 _print_stream()              ← 框架負責即時印出到終端機（你不需要動這裡）
```

也就是說，**你需要做的事情只有兩件**：

1. 在 `ryzenai/modules/` 建立一個 Python 類別，實作 `generate()` 函式
2. 在 `ryzenai/registry.py` 加入一個 tuple，把這個類別登錄到 registry

以下四個步驟帶你完成這兩件事。

---

## 步驟一：決定繼承哪個基底類別

你的模型類別必須繼承框架提供的基底類別，框架才能辨識它是一個合法的模型。選哪個很簡單：

| 你的模型是否支援圖片輸入？ | 繼承自 |
|--------------------------|--------|
| 否（純文字 LLM） | `Text2Text` |
| 是（看圖說話 VLM） | `ImageText2Text` |

> **為什麼要繼承？** 框架的 `session/` 層在執行推論前會做型別檢查，確保傳入的物件是合法的模型。繼承基底類別就是向框架「報到」的方式。兩個基底類別目前都不新增任何方法，差異僅在型別標記，未來框架可利用這個標記做路由決策。

---

## 步驟二：建立模組檔案

在 `ryzenai/modules/` 資料夾下，新增一個 `.py` 檔案。命名慣例是 `<模型簡稱>_<後端簡稱>.py`，全小寫加底線。

舉例來說，如果你要新增「LFM2 2.6B 跑在 NPU 上」，檔名就叫 `lfm2_2b6_npu.py`。

```
ryzenai/modules/
├── gemma3_4b_npu.py      ← 已有的範例（NPU 路線）
├── gemma4_e4b_gpu.py     ← 已有的範例（iGPU 路線）
└── lfm2_2b6_npu.py       ← 你要新增的檔案
```

---

## 步驟三：實作模組

這是整個過程中唯一需要你寫邏輯的部分。根據你使用的 SDK，選擇對應的情境。

### 先決定你用哪條推論路線

| 模型格式 | 執行硬體 | 使用的 SDK | Conda 環境 |
|---------|---------|-----------|-----------|
| ONNX（`.onnx` 檔案） | NPU 或 DirectML GPU | `onnxruntime_genai` | `ryzen-ai-1.7.1` |
| HuggingFace 原始模型 | iGPU (ROCm) | `transformers` + PyTorch | `rocm-pytorch` |

---

### 情境 A：ONNX Runtime GenAI（NPU / DirectML GPU）

適合使用 AMD 在 HuggingFace 上釋出的 ONNX 格式模型（例如 `amd/Gemma-3-4b-it-mm-onnx-ryzenai-npu`）。

```python
# ryzenai/modules/your_model_npu.py
import onnxruntime_genai as og
from typing import Generator

from ryzenai.model import ImageText2Text          # 純文字模型改用 Text2Text
from ryzenai.backend.onnx import ONNXVitisAIBackend   # DirectML GPU 改用 ONNXDirectMLBackend
from ryzenai.conversation import ConversationContext


class YourModelNPU(ImageText2Text):
    """一行說明：模型名稱 — 使用的後端與硬體"""

    def __init__(self, model_dir: str) -> None:
        # super().__init__() 會在這裡呼叫 ONNXVitisAIBackend()，
        # 它會自動檢查 VitisAI EP 是否存在。若環境不對，這行就會拋出 RuntimeError。
        super().__init__(ONNXVitisAIBackend())

        # 載入 ONNX 模型檔案（model_dir 是本地資料夾路徑，內含 .onnx 與 genai_config.json）
        self._og_model = og.Model(model_dir)

        # VLM（圖文）用 MultiModalProcessor；純文字 LLM 改用 og.Tokenizer
        self._processor = og.MultiModalProcessor(self._og_model)

    def generate(self, context: ConversationContext) -> Generator[str, None, None]:
        # 第一步：把框架的 ConversationContext 轉換成 SDK 能讀的格式
        messages, images = _parse_context(context)

        # 第二步：呼叫 onnxruntime_genai 進行推論，逐 token yield 輸出
        # 參考官方文件：https://onnxruntime.ai/docs/genai/
        # 典型做法：
        #   inputs = self._processor(text=messages, images=images)
        #   generator = og.Generator(self._og_model, ...)
        #   while not generator.is_done():
        #       generator.compute_logits()
        #       generator.generate_next_token()
        #       yield self._processor.decode(generator.get_next_tokens()[0])
        raise NotImplementedError("尚未實作 generate()，請參考上方說明補上推論邏輯")
```

---

### 情境 B：HuggingFace Transformers（PyTorch ROCm iGPU）

適合直接使用 HuggingFace Hub 上未轉換的原始模型（例如 `google/gemma-4-E4B-it`）。

```python
# ryzenai/modules/your_model_gpu.py
from transformers import AutoProcessor, AutoModelForImageTextToText, TextIteratorStreamer
from threading import Thread
from typing import Generator

from ryzenai.model import ImageText2Text          # 純文字模型改用 Text2Text + AutoModelForCausalLM
from ryzenai.backend.pytorch import PyTorchROCmBackend
from ryzenai.conversation import ConversationContext


class YourModelGPU(ImageText2Text):
    """一行說明：模型名稱 — HuggingFace Transformers + PyTorch ROCm（iGPU）"""

    def __init__(self, model_id: str) -> None:
        # super().__init__() 呼叫 PyTorchROCmBackend()，
        # 它會自動執行 torch.cuda.is_available() 確認 GPU 可用。
        super().__init__(PyTorchROCmBackend())

        # 從 HuggingFace Hub 下載（或從本地快取載入）模型
        self._processor = AutoProcessor.from_pretrained(model_id)
        self._hf_model = AutoModelForImageTextToText.from_pretrained(
            model_id, device_map="cuda"   # 自動分配到 CUDA/ROCm GPU
        )

    def generate(self, context: ConversationContext) -> Generator[str, None, None]:
        # 第一步：把框架的 ConversationContext 轉換成 SDK 能讀的格式
        messages, images = _parse_context(context)

        # 第二步：呼叫 HuggingFace 進行串流推論，逐 token yield 輸出
        # 典型做法（使用 TextIteratorStreamer 實現不阻塞的串流）：
        #   inputs = self._processor.apply_chat_template(messages, images=images, return_tensors="pt").to("cuda")
        #   streamer = TextIteratorStreamer(self._processor.tokenizer, skip_special_tokens=True)
        #   thread = Thread(target=self._hf_model.generate, kwargs={**inputs, "streamer": streamer})
        #   thread.start()
        #   for token in streamer:
        #       yield token
        raise NotImplementedError("尚未實作 generate()，請參考上方說明補上推論邏輯")
```

---

### 輔助函式：`_parse_context()` — 把框架格式轉成 SDK 格式

`generate()` 收到的 `context` 是框架自己的資料結構，裡面包含完整的多輪對話歷史。在呼叫任何 SDK 之前，你需要把它轉換成 SDK 能讀懂的格式。

下面這個函式處理兩種情況：

- **純文字訊息**：直接保留為字串
- **圖文混合訊息**（VLM）：把 base64 圖片解碼成 `PIL.Image` 物件，文字部分拼接為字串

你可以直接把這段程式碼複製到你的模組檔案底部，或者如果多個模組都要用，可以把它抽取到 `ryzenai/modules/_utils.py` 共用。

```python
import base64
from io import BytesIO
from PIL import Image

def _parse_context(context: ConversationContext) -> tuple[list[dict], list[Image.Image]]:
    """
    輸入：ConversationContext（框架的對話歷史物件）
    輸出：
      - messages_for_sdk：[{"role": "user", "content": "..."}, ...]
        → 這個格式可以直接傳給 apply_chat_template() 或 og 的 processor
      - images：[PIL.Image, ...]
        → 從訊息中解析出來的圖片，依序對應訊息中出現的順序
    """
    messages_for_sdk: list[dict] = []
    images: list[Image.Image] = []

    for msg in context.messages:
        if isinstance(msg.content, str):
            # 純文字訊息，直接包裝
            messages_for_sdk.append({"role": msg.role, "content": msg.content})
        else:
            # 圖文混合訊息（msg.content 是 list[dict]，每個 dict 有 "type" 欄位）
            text_parts: list[str] = []
            for part in msg.content:
                if part["type"] == "text":
                    text_parts.append(part["text"])
                elif part["type"] == "image_url":
                    # 格式是 "data:image/jpeg;base64,<base64資料>"
                    url: str = part["image_url"]["url"]
                    _, b64data = url.split(",", 1)
                    images.append(Image.open(BytesIO(base64.b64decode(b64data))))
            messages_for_sdk.append({"role": msg.role, "content": " ".join(text_parts)})

    return messages_for_sdk, images
```

> **重要提示**：不同 SDK 對 `content` 格式的要求不同。`onnxruntime_genai` 通常需要把所有文字合併成單一字串；`transformers` 的 `apply_chat_template` 則可以接受包含 `{"type": "text", ...}` 的 list 格式。如果推論結果異常，優先檢查這個轉換邏輯是否符合你使用的 SDK 文件。

---

## 步驟四：在 registry 登錄你的模型

這是整個流程**唯一需要改動的框架檔案**。打開 `ryzenai/registry.py`，在 `_REGISTRY` 字典中加入一個 tuple：

```python
# ryzenai/registry.py  ← 只改這一個檔案

_REGISTRY: dict[str, tuple] = {
    "gemma3-4b-npu": (
        "ryzenai.modules.gemma3_4b_npu", "Gemma3_4B_NPU",
        "weights/Gemma-3-4b-it-mm-onnx-ryzenai-npu",
    ),
    "gemma4-4b-gpu": (
        "ryzenai.modules.gemma4_e4b_gpu", "Gemma4_E4B_GPU",
        "google/gemma-4-E4B-it",
    ),
    "gemma4-2b-gpu": (
        "ryzenai.modules.gemma4_e2b_gpu", "Gemma4_E2B_GPU",
        "google/gemma-4-E2B-it",
    ),
    # ↓ 新增這一行，格式：("模組路徑", "類別名稱", "傳給 __init__ 的引數")
    "your-model-npu": (
        "ryzenai.modules.your_model_npu", "YourModelNPU",
        "weights/your-model-weights-dir",
    ),
}
```

三個欄位的說明：

| 欄位 | 範例 | 說明 |
|------|------|------|
| `model-id` | `"your-model-npu"` | CLI `--model` 與 API `model` 欄位使用的識別名稱 |
| `"模組路徑"` | `"ryzenai.modules.your_model_npu"` | 對應 `ryzenai/modules/your_model_npu.py` |
| `"類別名稱"` | `"YourModelNPU"` | 模組檔案內的類別名稱 |
| `"引數"` | `"weights/your-model-weights-dir"` | 傳給 `__init__` 的第一個位置引數（通常是 weights 路徑或 HuggingFace model_id） |

> **為什麼不用 `lambda`？** registry 改為 tuple 格式後，`build_model()` 函式會在實際呼叫時才執行 `importlib.import_module()`，同樣保留了懶載入語義——啟動程式時不會觸碰 `onnxruntime_genai` 或 `torch`。

登錄完成後，你的模型立刻在所有介面生效，不需要動其他任何檔案：

```powershell
# 命令列互動模式
python cli.py --model your-model-npu

# 命令列單次推論
python cli.py --model your-model-npu --prompt "請解釋量子糾纏" --stream

# 啟動 REST API server（之後用 OpenAI SDK 連線）
python api.py --model your-model-npu
```

---

## 附錄 A：`generate()` 的四條規則

實作 `generate()` 時，只要遵守以下四條規則，框架其餘的 CLI、API、串流處理就會自動運作正確：

**規則 1：逐 token yield，不要一次性回傳整段文字。**
框架的 `_print_stream()` 和 SSE 串流機制都依賴 `yield`，如果你用 `return` 一次回傳整段文字，CLI 不會有打字機效果，API 也無法串流。

**規則 2：輸入永遠是完整的多輪歷史，不只是最後一句話。**
`context.messages` 包含從對話開始到現在的所有訊息（包含 user 和 assistant 輪流說的話）。SDK 的 chat template 通常需要完整歷史才能正確理解上下文，不要只取最後一條。

**規則 3：推論失敗時拋出例外，不要靜默忽略。**
如果 `generate()` 遇到錯誤卻沒有拋出例外，框架不會知道出問題了，使用者只會看到一片空白輸出，很難除錯。

**規則 4：`generate()` 本身不需要管理對話歷史。**
多輪對話的記憶（把 user 說的話和 assistant 的回應存起來）是 `InteractiveSession` 的工作，已經由框架處理好了。你的 `generate()` 只需要讀取 `context`、產出 token，不需要寫入任何東西。

---

## 附錄 B：可選用的 Backend 類別

| Backend 類別 | 適用 Conda 環境 | 目標硬體 | 驗證邏輯 |
|-------------|----------------|---------|---------|
| `ONNXVitisAIBackend` | `ryzen-ai-1.7.1` | NPU (XDNA) | 檢查 `VitisAIExecutionProvider` 是否在 `ort.get_available_providers()` 清單中 |
| `ONNXDirectMLBackend` | `ryzen-ai-1.7.1` | GPU (DirectML) | 檢查 `DmlExecutionProvider` 是否在 `ort.get_available_providers()` 清單中 |
| `PyTorchROCmBackend` | `rocm-pytorch` | iGPU (RDNA / ROCm) | 呼叫 `torch.cuda.is_available()` |

所有 Backend 類別都在 `__init__` 中自動執行環境驗證。如果環境不符（例如沒有裝驅動、Conda 環境不對），會在模型初始化時立即拋出 `RuntimeError`，並附上清楚的錯誤說明，你不需要在自己的模組裡重複做這個檢查。

---

## 完成確認清單

做完以上步驟後，請對照以下清單確認沒有遺漏：

- [ ] `ryzenai/modules/your_model.py` 檔案已建立
- [ ] 類別繼承了 `Text2Text` 或 `ImageText2Text`（其中一個，視模型類型而定）
- [ ] `__init__` 中呼叫了 `super().__init__(<對應的Backend類別>())`
- [ ] `generate()` 使用 `yield` 逐 token 輸出（回傳型別為 `Generator[str, None, None]`）
- [ ] `ryzenai/registry.py` 的 `_REGISTRY` 已新增一筆 tuple
