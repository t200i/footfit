# 專案架構

本專案採用 Clean Architecture，介面（CLI / API / ComfyUI）與模型實作完全解耦。

## 目錄結構

```
core/
  base.py              ← LLMService 合約（所有模型必須實作）
models/
  gemma4.py            ← Gemma4 實作
  <your_model>.py      ← 新增模型放這裡
interfaces/
  api.py               ← 通用 OpenAI 相容 API server
  cli.py               ← 通用 CLI（互動/單次）
  comfyui.py           ← 通用 ComfyUI custom node
serve.py               ← API server 入口（--model HuggingFace repo ID）
cli.py                 ← CLI 入口（--model HuggingFace repo ID）
```

## 依賴方向

```
models/      →  core/base.py
interfaces/  →  core/base.py
serve.py     →  models/ + interfaces/
```

`interfaces/` 完全不 import 任何具體模型，只依賴 `LLMService` 介面。  
新增模型時，介面層零修改。

## 新增一個模型

### 1. 實作 LLMService

```python
# models/my_model.py
from core.base import LLMService, ModelInfo

class MyModelService(LLMService):
    def __init__(self, model_id: str):
        # 載入模型...
        self.info = ModelInfo(
            model_id=model_id,
            name="my_model",
            description="My custom model",
            device="cuda:0",
        )

    def generate(self, messages: list[dict], max_new_tokens: int = 200) -> str:
        # 回傳完整回應字串
        ...

    def generate_stream(self, messages: list[dict], max_new_tokens: int = 200):
        # yield text chunks（供 CLI 串流 / API SSE 使用）
        ...
```

### 2. 在 serve.py 的 MODEL_REGISTRY 加一行

```python
# serve.py — MODEL_REGISTRY（prefix 匹配，涵蓋整個模型家族）
MODEL_REGISTRY = {
    "google/gemma-4":      ("models.gemma4",   "Gemma4Service"),
    "meta-llama/Llama-3": ("models.llama",    "LlamaService"),   # ← 新增範例
}
```

完成。`cli.py`、`serve.py`、ComfyUI 節點全部自動支援新模型，無需其他修改。

## deployment 資料夾慣例

硬體特定設定（device_map、量化參數、driver 版本等）放在 `deployment/<device_name>/`，透過環境變數或 config file 傳入 `serve.py`，不需要 fork 介面層。

```
deployment/
  vivobook_s_15_16/    ← Ryzen AI 9 HX 370 (ROCm iGPU)
  pn54/                ← Ryzen AI 350 (NPU)
```
