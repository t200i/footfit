"""
models/igpu/base.py — iGPU generic drivers
===========================================
Provides two ChatModel drivers for iGPU (ROCm / CUDA) inference via
HuggingFace transformers:

  IgpuVisionLm  — AutoModelForImageTextToText  (text + image input)
  IgpuTextLm    — AutoModelForCausalLM         (text-only input)

Both drivers use TextIteratorStreamer for native token-level streaming.

Environment: rocm-pytorch conda env
"""

from __future__ import annotations

from threading import Thread
from typing import ClassVar, Iterator

import torch
from transformers import (
    AutoModelForCausalLM,
    AutoModelForImageTextToText,
    AutoProcessor,
    AutoTokenizer,
    TextIteratorStreamer,
)

from core.module import ChatModel


# ── IgpuVisionLm ─────────────────────────────────────────────────────────────

class IgpuVisionLm(ChatModel):
    """
    iGPU vision-language model driver (ROCm / CUDA).

    Loads any HuggingFace AutoModelForImageTextToText checkpoint.
    Streams tokens via TextIteratorStreamer.

    Usage:
        svc = IgpuVisionLm("google/gemma-4-E4B-it")
        serve(svc)
    """

    description:     ClassVar[str]  = "iGPU VisionLM via HuggingFace transformers (ROCm / CUDA)"
    supports_vision: ClassVar[bool] = True

    def __init__(self, model_id: str, device_map: str = "auto") -> None:
        print(f"[IgpuVisionLm] Loading: {model_id}")
        self.model_id  = model_id
        self.processor = AutoProcessor.from_pretrained(model_id)
        self.model     = AutoModelForImageTextToText.from_pretrained(
            model_id, torch_dtype=torch.bfloat16, device_map=device_map
        )
        self.model.eval()
        self.device = str(next(self.model.parameters()).device)
        print(f"[IgpuVisionLm] Ready on {self.device}")

    def create(self, messages: list[dict], max_tokens: int = 200) -> Iterator[str]:
        inputs   = self._build_inputs(messages)
        streamer = TextIteratorStreamer(
            self.processor.tokenizer,
            skip_prompt=True,
            skip_special_tokens=True,
        )
        thread = Thread(
            target=self.model.generate,
            kwargs={**inputs, "max_new_tokens": max_tokens, "streamer": streamer},
        )
        with torch.inference_mode():
            thread.start()
        for chunk in streamer:
            if chunk:
                yield chunk
        thread.join()

    def _build_inputs(self, messages: list[dict]) -> dict:
        """Normalise OpenAI messages and tokenise for the model."""
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


# ── IgpuTextLm ───────────────────────────────────────────────────────────────

class IgpuTextLm(ChatModel):
    """
    iGPU text-only LLM driver (ROCm / CUDA).

    Loads any HuggingFace AutoModelForCausalLM checkpoint.
    Streams tokens via TextIteratorStreamer.

    Usage:
        svc = IgpuTextLm("mistralai/Mistral-7B-Instruct-v0.3")
        serve(svc)
    """

    description:     ClassVar[str]  = "iGPU TextLM via HuggingFace transformers (ROCm / CUDA)"
    supports_vision: ClassVar[bool] = False

    def __init__(self, model_id: str, device_map: str = "auto") -> None:
        print(f"[IgpuTextLm] Loading: {model_id}")
        self.model_id  = model_id
        self.tokenizer = AutoTokenizer.from_pretrained(model_id)
        self.model     = AutoModelForCausalLM.from_pretrained(
            model_id, torch_dtype=torch.bfloat16, device_map=device_map
        )
        self.model.eval()
        self.device = str(next(self.model.parameters()).device)
        print(f"[IgpuTextLm] Ready on {self.device}")

    def create(self, messages: list[dict], max_tokens: int = 200) -> Iterator[str]:
        inputs   = self._build_inputs(messages)
        streamer = TextIteratorStreamer(
            self.tokenizer,
            skip_prompt=True,
            skip_special_tokens=True,
        )
        thread = Thread(
            target=self.model.generate,
            kwargs={**inputs, "max_new_tokens": max_tokens, "streamer": streamer},
        )
        with torch.inference_mode():
            thread.start()
        for chunk in streamer:
            if chunk:
                yield chunk
        thread.join()

    def _build_inputs(self, messages: list[dict]) -> dict:
        text = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )
        inputs = self.tokenizer(text, return_tensors="pt")
        device = next(self.model.parameters()).device
        return {k: v.to(device) for k, v in inputs.items()}
