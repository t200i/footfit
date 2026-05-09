import base64
import os
from io import BytesIO
from threading import Thread
from typing import Generator

import torch
from PIL import Image

# Opt-in to experimental ROCm attention kernels (Flash + Mem-Efficient).
# Without this the runtime emits UserWarning for every attention call even
# though the kernels are already being used.  Setting the variable here keeps
# the opt-in scoped to this module rather than requiring shell configuration.
os.environ.setdefault("TORCH_ROCM_AOTRITON_ENABLE_EXPERIMENTAL", "1")
from transformers import AutoModelForImageTextToText, AutoProcessor, TextIteratorStreamer

from ryzenai.backend.pytorch import PyTorchROCmBackend
from ryzenai.conversation import ConversationContext
from ryzenai.model import ImageText2Text


class Gemma4_E2B_GPU(ImageText2Text):
    """Gemma4 E2B Vision — HuggingFace transformers + PyTorch ROCm（iGPU）"""

    def __init__(self, model_id: str) -> None:
        super().__init__(PyTorchROCmBackend())
        self._processor = AutoProcessor.from_pretrained(model_id)
        self._model = AutoModelForImageTextToText.from_pretrained(
            model_id,
            device_map="cuda",
            torch_dtype=torch.bfloat16,
        )

    def generate(self, context: ConversationContext) -> Generator[str, None, None]:
        messages = _build_messages(context)

        inputs = self._processor.apply_chat_template(
            messages,
            add_generation_prompt=True,
            tokenize=True,
            return_dict=True,
            return_tensors="pt",
        ).to(self._model.device)

        streamer = TextIteratorStreamer(
            self._processor.tokenizer,
            skip_prompt=True,
            skip_special_tokens=True,
        )

        thread = Thread(
            target=self._model.generate,
            kwargs={**inputs, "streamer": streamer, "max_new_tokens": 512},
            daemon=True,
        )
        thread.start()

        for token in streamer:
            yield token


def _build_messages(context: ConversationContext) -> list[dict]:
    """Convert ConversationContext to transformers apply_chat_template format.

    Text messages → {"role": ..., "content": str}
    Multimodal    → {"role": ..., "content": [{"type": "text"|"image", ...}]}
    """
    messages = []
    for msg in context.messages:
        if isinstance(msg.content, str):
            messages.append({"role": msg.role, "content": msg.content})
        else:
            content_parts: list[dict] = []
            for part in msg.content:
                if part["type"] == "text":
                    content_parts.append({"type": "text", "text": part["text"]})
                elif part["type"] == "image_url":
                    url: str = part["image_url"]["url"]
                    _, b64data = url.split(",", 1)
                    img = Image.open(BytesIO(base64.b64decode(b64data)))
                    content_parts.append({"type": "image", "image": img})
            messages.append({"role": msg.role, "content": content_parts})
    return messages
