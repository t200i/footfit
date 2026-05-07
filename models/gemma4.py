"""
models/gemma4.py — Gemma4 implementation of LLMService
=======================================================
Registered in serve.py as "gemma4".
"""

from __future__ import annotations

import threading

import torch
from transformers import AutoProcessor, AutoModelForImageTextToText, TextIteratorStreamer

from core.base import LLMService, ModelInfo

DEFAULT_MODEL_ID = "google/gemma-4-E4B-it"


class Gemma4Service(LLMService):

    def __init__(self, model_id: str = DEFAULT_MODEL_ID, device_map: str = "auto"):
        print(f"[Gemma4Service] Loading: {model_id}")
        self.processor = AutoProcessor.from_pretrained(model_id)
        self.model = AutoModelForImageTextToText.from_pretrained(
            model_id, dtype=torch.bfloat16, device_map=device_map
        )
        self.model.eval()
        device = str(next(self.model.parameters()).device)
        self.info = ModelInfo(
            model_id=model_id,
            name="gemma4",
            description="Google Gemma 4 vision-language model",
            device=device,
        )
        print(f"[Gemma4Service] Ready on {device}")

    def generate(self, messages: list[dict], max_new_tokens: int = 200) -> str:
        inputs = self._build_inputs(messages)
        with torch.inference_mode():
            output_ids = self.model.generate(**inputs, max_new_tokens=max_new_tokens)
        input_len = inputs["input_ids"].shape[-1]
        generated = output_ids[:, input_len:]
        return self.processor.batch_decode(generated, skip_special_tokens=True)[0]

    def generate_stream(self, messages: list[dict], max_new_tokens: int = 200):
        inputs = self._build_inputs(messages)
        streamer = TextIteratorStreamer(
            self.processor.tokenizer,
            skip_prompt=True,
            skip_special_tokens=True,
        )
        gen_kwargs = {**inputs, "max_new_tokens": max_new_tokens, "streamer": streamer}
        thread = threading.Thread(target=self.model.generate, kwargs=gen_kwargs)
        with torch.inference_mode():
            thread.start()
        for chunk in streamer:
            if chunk:
                yield chunk
        thread.join()

    # ── helpers ───────────────────────────────────────────────────────────────

    def _build_inputs(self, messages: list[dict]) -> dict:
        # Normalise: ensure each message content is in multimodal list format
        normalised = []
        for m in messages:
            content = m["content"]
            if isinstance(content, str):
                content = [{"type": "text", "text": content}]
            normalised.append({"role": m["role"], "content": content})

        inputs = self.processor.apply_chat_template(
            normalised,
            add_generation_prompt=True,
            tokenize=True,
            return_tensors="pt",
            return_dict=True,
        )
        device = next(self.model.parameters()).device
        return {k: v.to(device) for k, v in inputs.items()}
