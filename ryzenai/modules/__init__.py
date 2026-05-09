def __getattr__(name: str):
    if name == "Gemma3_4B_NPU":
        from ryzenai.modules.gemma3_4b_npu import Gemma3_4B_NPU
        return Gemma3_4B_NPU
    if name == "Gemma4_E4B_GPU":
        from ryzenai.modules.gemma4_e4b_gpu import Gemma4_E4B_GPU
        return Gemma4_E4B_GPU
    raise AttributeError(f"module 'ryzenai.modules' has no attribute {name!r}")

__all__ = ["Gemma3_4B_NPU", "Gemma4_E4B_GPU"]
