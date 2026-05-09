import onnxruntime_genai as og
from typing import Generator

from ryzenai.model import ImageText2Text
from ryzenai.backend.onnx import ONNXVitisAIBackend
from ryzenai.conversation import ConversationContext


class Gemma3_4B_NPU(ImageText2Text):
    """Gemma3 4B Vision — onnxruntime_genai + Vitis AI EP（NPU）"""

    def __init__(self, model_dir: str) -> None:
        super().__init__(ONNXVitisAIBackend())
        self._model = og.Model(model_dir)
        self._processor = og.MultiModalProcessor(self._model)

    def generate(self, context: ConversationContext) -> Generator[str, None, None]:
        # TODO: 待個別模型測試後實作
        raise NotImplementedError
