from transformers import AutoProcessor, AutoModelForImageTextToText, TextIteratorStreamer
from typing import Generator

from ryzenai.model import ImageText2Text
from ryzenai.backend.pytorch import PyTorchROCmBackend
from ryzenai.conversation import ConversationContext


class Gemma4_E4B_GPU(ImageText2Text):
    """Gemma4 E4B Vision — HuggingFace transformers + PyTorch ROCm（iGPU）"""

    def __init__(self, model_id: str) -> None:
        super().__init__(PyTorchROCmBackend())
        self._processor = AutoProcessor.from_pretrained(model_id)
        self._model = AutoModelForImageTextToText.from_pretrained(
            model_id, device_map="cuda"
        )

    def generate(self, context: ConversationContext) -> Generator[str, None, None]:
        # TODO: 待個別模型測試後實作
        raise NotImplementedError
