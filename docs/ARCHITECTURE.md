# 專案架構

本專案採用 Clean Architecture + Domain-Driven Design，以**執行後端**（iGPU / NPU）作為領域邊界。

## 兩個 Domain

| Domain | Backend | Conda 環境 | 模型來源 |
|--------|---------|-----------|---------|
| **iGPU** | PyTorch + ROCm | `rocm-pytorch` | HuggingFace repo ID（線上下載） |
| **NPU** | ONNX Runtime + Vitis AI EP | `ryzen-ai-1.7.1` | 本地 git clone 的 AMD Collection 目錄 |

這兩個 Domain **無法在同一個 Python process 裡共存**，因此 Composition Root 放在各自的 `deployment/` 資料夾，而非頂層。

## 目錄結構

```
core/
  base.py                    ← LLMService 合約（與 backend 無關）
models/
  igpu/
    gemma4.py                ← Gemma4 (PyTorch / ROCm)
  npu/
    onnx_llm.py              ← 通用 AMD NPU 模型（ONNX Runtime via subprocess）
interfaces/
  api.py                     ← 通用 OpenAI 相容 API server
  cli.py                     ← 通用 CLI（互動/單次）
  comfyui.py                 ← 通用 ComfyUI custom node
deployment/
  vivobook_s_15_16/          ← Composition Root（rocm-pytorch）
    serve.py                 ← 組裝 igpu/gemma4 + interfaces/api
    cli.py                   ← 組裝 igpu/gemma4 + interfaces/cli
    gemma4.py                ← 保留作為 standalone demo
  PN54/                      ← Composition Root（ryzen-ai-1.7.1）
    serve.py                 ← 組裝 npu/onnx_llm + interfaces/api
    cli.py                   ← 組裝 npu/onnx_llm + interfaces/cli
    llm.py                   ← 保留作為 standalone NPU wrapper
    vlm.py                   ← 保留作為 standalone NPU VLM wrapper
```

## 依賴方向

```
models/igpu/  →  core/base.py
models/npu/   →  core/base.py
interfaces/   →  core/base.py        ← 只依賴合約，不知道是哪個 backend
deployment/   →  models/ + interfaces/  ← 唯一知道全貌的地方
```

## 新增模型

### iGPU — 新的 HuggingFace 模型

1. 在 `models/igpu/` 新增 `<name>.py`，繼承 `LLMService`
2. 在對應 `deployment/` 的 `serve.py` / `cli.py` 中 import 並組裝

```python
# models/igpu/llama.py
from core.base import LLMService, ModelInfo
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, TextIteratorStreamer

class LlamaService(LLMService):
    def __init__(self, model_id: str):
        ...
    def generate(self, messages, max_new_tokens=200) -> str: ...
    def generate_stream(self, messages, max_new_tokens=200): ...
```

### NPU — 新的 AMD Collection 模型

NPU 模型統一透過 `models/npu/onnx_llm.py` 的 `OnnxLLMService` 處理，**不需要新增任何 Python 檔案**，只需 git clone 模型目錄後直接傳路徑即可：

```powershell
git clone https://huggingface.co/amd/Phi-4-mini-instruct_rai_1.7.1_npu_16K
python deployment/PN54/cli.py --model ./Phi-4-mini-instruct_rai_1.7.1_npu_16K
```

