from ryzenai.backend.base import Backend, logger


class ONNXVitisAIBackend(Backend):
    """NPU — onnxruntime-genai + Vitis AI EP（conda: ryzen-ai-1.7.1）"""

    name = "ONNXVitisAI"

    def __init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        import onnxruntime as ort
        available = ort.get_available_providers()
        if "VitisAIExecutionProvider" not in available:
            raise RuntimeError(
                f"VitisAI EP not found. Available providers: {available}"
            )
        logger.info("Backend: ONNX Runtime GenAI — VitisAI EP (NPU)")


class ONNXDirectMLBackend(Backend):
    """GPU — onnxruntime-genai + DirectML EP（conda: ryzen-ai-1.7.1）"""

    name = "ONNXDirectML"

    def __init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        import onnxruntime as ort
        available = ort.get_available_providers()
        if "DmlExecutionProvider" not in available:
            raise RuntimeError(
                f"DirectML EP not found. Available providers: {available}"
            )
        logger.info("Backend: ONNX Runtime GenAI — DirectML EP (GPU)")
