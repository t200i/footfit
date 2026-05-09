"""
Model Registry — 唯一真實來源 (Single Source of Truth)

新增模型只需在 _REGISTRY 加入一個 tuple，格式為：
    "model-id": ("ryzenai.modules.<module>", "<ClassName>", "<init_arg>", ...)

cli.py、api.py 與 ryzenai/modules/__init__.py 皆自動從此處派生，
不需要個別維護。
"""
import importlib

from ryzenai.model import Model

# ── 在此登錄所有可用模型 ────────────────────────────────────────────────────
# 格式：  "model-id": ("module.path", "ClassName", "init_arg1", ...)
# model-id  : CLI --model / API model 欄位使用的識別名稱
# module.path: 模組的完整 import 路徑
# ClassName  : 模組內的類別名稱
# init_arg*  : 傳給 __init__ 的位置引數（通常是 weights 路徑或 HuggingFace model_id）
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
}
# ────────────────────────────────────────────────────────────────────────────


def available_models() -> list[str]:
    """回傳所有已登錄的 model-id 清單。"""
    return list(_REGISTRY)


def build_model(model_id: str) -> Model:
    """根據 model-id 建立並回傳對應的模型實例。

    import 在此函式被呼叫時才發生（lazy），避免啟動時觸碰
    硬體相依套件（onnxruntime_genai、torch）。
    """
    if model_id not in _REGISTRY:
        raise ValueError(
            f"Unknown model: '{model_id}'. Available: {available_models()}"
        )
    module_path, class_name, *args = _REGISTRY[model_id]
    mod = importlib.import_module(module_path)
    return getattr(mod, class_name)(*args)
