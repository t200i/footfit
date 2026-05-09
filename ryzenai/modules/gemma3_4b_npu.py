import base64
import json
import logging
import os
import tempfile
from io import BytesIO
from pathlib import Path
from typing import Generator

import onnxruntime_genai as og
from PIL import Image

from ryzenai.backend.onnx import ONNXVitisAIBackend
from ryzenai.conversation import ConversationContext
from ryzenai.model import ImageText2Text

logger = logging.getLogger("ryzenai.modules.gemma3_4b_npu")


class Gemma3_4B_NPU(ImageText2Text):
    """Gemma3 4B Vision — onnxruntime_genai + Vitis AI EP（NPU）"""

    def __init__(self, model_dir: str) -> None:
        super().__init__(ONNXVitisAIBackend())
        self._model_dir = os.path.abspath(model_dir)
        config = og.Config(self._model_dir)
        self._model = og.Model(config)
        self._processor = self._model.create_multimodal_processor()
        self._tokenizer = og.Tokenizer(self._model)
        logger.info(
            "Gemma3-4B-NPU loaded (type=%s, device=%s)",
            self._model.type,
            self._model.device_type,
        )

    def generate(self, context: ConversationContext) -> Generator[str, None, None]:
        messages, pil_images = _extract_messages_and_images(context)
        prompt = _apply_chat_template(self._model_dir, self._tokenizer, messages)
        logger.info("Running NPU inference (images=%d)", len(pil_images))

        temp_paths: list[str] = []
        try:
            for img in pil_images:
                with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
                    tmp_path = tmp.name
                img.convert("RGB").save(tmp_path, format="JPEG")
                temp_paths.append(tmp_path)

            images = og.Images.open(*temp_paths) if temp_paths else None
            inputs = self._processor(prompt, images=images) if images is not None else self._processor(prompt)

            params = og.GeneratorParams(self._model)
            generator = og.Generator(self._model, params)
            generator.set_inputs(inputs)

            stream = self._processor.create_stream()
            try:
                while not generator.is_done():
                    generator.generate_next_token()
                    token = generator.get_next_tokens()[0]
                    yield stream.decode(token)
            finally:
                del generator
        finally:
            for path in temp_paths:
                try:
                    os.unlink(path)
                except OSError:
                    pass


def _extract_messages_and_images(
    context: ConversationContext,
) -> tuple[list[dict], list[Image.Image]]:
    """Convert ConversationContext to an OpenAI-style messages list and PIL image list.

    Images in content are replaced with {"type": "image"} placeholders (for the
    chat template) and the decoded PIL images are returned separately in order.
    """
    messages: list[dict] = []
    pil_images: list[Image.Image] = []

    for msg in context.messages:
        if isinstance(msg.content, str):
            messages.append({"role": msg.role, "content": [{"type": "text", "text": msg.content}]})
        else:
            content_list: list[dict] = []
            for part in msg.content:
                if part["type"] == "text":
                    content_list.append({"type": "text", "text": part["text"]})
                elif part["type"] == "image_url":
                    url: str = part["image_url"]["url"]
                    _, b64data = url.split(",", 1)
                    pil_images.append(Image.open(BytesIO(base64.b64decode(b64data))))
                    content_list.append({"type": "image"})
            messages.append({"role": msg.role, "content": content_list})

    return messages, pil_images


def _apply_chat_template(
    model_dir: str,
    tokenizer: og.Tokenizer,
    messages: list[dict],
) -> str:
    """Build a prompt string using the model's chat template."""
    model_path = Path(model_dir)
    tok_cfg_path = model_path / "tokenizer_config.json"
    jinja_path = model_path / "chat_template.jinja"

    template_str: str | None = None
    bos: str | None = None

    if tok_cfg_path.exists():
        with open(tok_cfg_path, encoding="utf-8") as f:
            tok_cfg = json.load(f)
        template_str = tok_cfg.get("chat_template")
        bos = tok_cfg.get("bos_token")

    if not template_str and jinja_path.exists():
        with open(jinja_path, encoding="utf-8") as f:
            template_str = f.read()

    if not template_str:
        raise RuntimeError(f"No chat template found in {model_dir}")

    if not bos:
        template_str = template_str.replace("{{ bos_token }}", "")

    return tokenizer.apply_chat_template(
        json.dumps(messages),
        template_str=template_str,
        add_generation_prompt=True,
    )
