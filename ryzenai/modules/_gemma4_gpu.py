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
from ryzenai.model.base import Chunk
from ryzenai.modules.gemma4_tool_parser import Gemma4StreamParser


class Gemma4GPU(ImageText2Text):
    """Gemma4 Vision — HuggingFace transformers + PyTorch ROCm（GPU），支援 function calling"""

    def __init__(self, model_id: str) -> None:
        super().__init__(PyTorchROCmBackend())
        self._processor = AutoProcessor.from_pretrained(model_id)
        self._model = AutoModelForImageTextToText.from_pretrained(
            model_id,
            device_map="cuda",
            dtype=torch.bfloat16,
        )

    def generate(self, context: ConversationContext) -> Generator[Chunk, None, None]:
        messages = _build_messages(context)

        inputs = self._processor.apply_chat_template(
            messages,
            tools=context.metadata.get("tools") or None,
            add_generation_prompt=True,
            tokenize=True,
            return_dict=True,
            return_tensors="pt",
        ).to(self._model.device)

        # 保留 special tokens：工具呼叫標記 <|tool_call>、<|"|> 皆為 special token，
        # 交由 Gemma4StreamParser 拆出 ToolCall 並濾掉 <turn|> 等控制符號。
        streamer = TextIteratorStreamer(
            self._processor.tokenizer,
            skip_prompt=True,
            skip_special_tokens=False,
        )

        thread = Thread(
            target=self._model.generate,
            kwargs={**inputs, "streamer": streamer, "max_new_tokens": 512},
            daemon=True,
        )
        thread.start()

        parser = Gemma4StreamParser()
        for text in streamer:
            yield from parser.feed(text)
        yield from parser.flush()


def _build_messages(context: ConversationContext) -> list[dict]:
    """Convert ConversationContext to transformers apply_chat_template format.

    Text messages → {"role": ..., "content": str}
    Multimodal    → {"role": ..., "content": [{"type": "text"|"image", ...}]}
    Tool calls    → assistant 附 "tool_calls"；工具結果為 {"role": "tool", "tool_call_id", "content"}
    """
    messages = []
    for msg in context.messages:
        if msg.content is None or isinstance(msg.content, str):
            entry = {"role": msg.role, "content": msg.content}
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
            entry = {"role": msg.role, "content": content_parts}
        if msg.tool_calls:
            entry["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {"name": tc.name, "arguments": tc.arguments},
                }
                for tc in msg.tool_calls
            ]
        if msg.tool_call_id is not None:
            entry["tool_call_id"] = msg.tool_call_id
        messages.append(entry)
    return messages
