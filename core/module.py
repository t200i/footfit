"""
core/module.py — ChatModel base class
======================================
Analogous to PyTorch's nn.Module:
  - Subclass it, implement __init__ (load weights) and create (inference).
  - Everything else (SSE formatting, OpenAI JSON, routing, CLI) is handled
    automatically by the interfaces layer.

Naming follows OpenAI SDK:
  - create()   ←→  client.chat.completions.create()
  - model_id   ←→  the "model" field in OpenAI requests/responses
"""

from __future__ import annotations

from typing import ClassVar, Iterator


class ChatModel:
    """
    Base class for all LLM/VLM inference drivers.

    Subclass contract — implement exactly two things:
      1. __init__:  load weights, processor, tokenizer.
                    set self.model_id and self.device.
      2. create():  inference logic. Always yield str chunks.
                    Non-streaming backends: yield the full text once.

    Class variables (declare in class body):
      description:     one-line description of this driver.
      supports_vision: True if the driver accepts image inputs.

    Instance variables (set in __init__):
      model_id:  the HuggingFace repo ID or local path that was loaded.
                 api.py uses this as the "model" field in responses.
      device:    resolved device string, e.g. "cuda:0", "cpu", "NPU".

    Usage:
        class IgpuVisionLm(ChatModel):
            description     = "iGPU VisionLM via HuggingFace transformers"
            supports_vision = True

            def __init__(self, model_id: str, device_map: str = "auto"):
                self.model_id = model_id
                self.model    = load_weights(model_id, device_map)
                self.device   = "cuda:0"

            def create(self, messages, max_tokens=200):
                for token in self.model.stream(messages):
                    yield token

        serve(IgpuVisionLm("google/gemma-4-E4B-it"))
    """

    # ── Driver-level metadata (ClassVar — describes the driver, not one run) ─
    description:     ClassVar[str]  = ""
    supports_vision: ClassVar[bool] = False

    # ── Instance attributes set in __init__ ──────────────────────────────────
    model_id: str = ""   # set by subclass __init__
    device:   str = ""   # set by subclass __init__

    def __init__(self) -> None:
        """Load model weights, processor, tokenizer. Set self.model_id and self.device."""
        raise NotImplementedError

    def create(
        self,
        messages: list[dict],
        max_tokens: int = 200,
    ) -> Iterator[str]:
        """
        Inference logic. Always yield str chunks.

        messages — OpenAI-compatible list:
            [{"role": "user", "content": "hello"},
             {"role": "user", "content": [          # multimodal
                 {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,..."}},
                 {"type": "text",      "text": "describe this"},
             ]},
             {"role": "assistant", "content": "..."}]

        Streaming backend  — yield token by token.
        Non-streaming      — yield the full text once (still valid).
        """
        raise NotImplementedError

    # ── Static helper — usable by subclasses, not required to override ───────

    @staticmethod
    def parse_content(content: str | list) -> tuple[str, list]:
        """
        Extract (text: str, images: list[PIL.Image.Image]) from an OpenAI
        content field.  Handles plain str and content-part lists.
        Decodes base64 data URIs automatically.
        """
        if isinstance(content, str):
            return content, []

        import base64
        from io import BytesIO
        from PIL import Image

        texts:  list[str]              = []
        images: list[Image.Image]      = []

        for part in content:
            if part.get("type") == "text":
                texts.append(part["text"])
            elif part.get("type") == "image_url":
                url: str = part["image_url"]["url"]
                if url.startswith("data:"):
                    b64 = url.split(",", 1)[1]
                    images.append(
                        Image.open(BytesIO(base64.b64decode(b64))).convert("RGB")
                    )

        return " ".join(texts), images
