"""
Gemma4 AI Service — single file, three interfaces
==================================================
Usage:
  [Python]   from gemma4_service import Gemma4Service
  [CLI]      python gemma4_service.py                     # interactive
             python gemma4_service.py -p "你好"            # single prompt
  [ComfyUI]  copy / symlink this file to ComfyUI/custom_nodes/
"""

from __future__ import annotations

import sys
import threading
import torch
from transformers import AutoProcessor, AutoModelForImageTextToText, TextStreamer, TextIteratorStreamer

DEFAULT_MODEL_ID = "google/gemma-4-E4B-it"


# ── Core service ──────────────────────────────────────────────────────────────


class Gemma4Service:
    """Reusable Gemma4 inference service (load once, call many times)."""

    def __init__(self, model_id: str = DEFAULT_MODEL_ID, device_map: str = "auto"):
        print(f"[Gemma4Service] Loading model: {model_id}")
        self.processor = AutoProcessor.from_pretrained(model_id)
        self.model = AutoModelForImageTextToText.from_pretrained(
            model_id, dtype=torch.bfloat16, device_map=device_map
        )
        self.model.eval()
        self.device = next(self.model.parameters()).device
        print(f"[Gemma4Service] Model loaded on: {self.device}")

    def generate(
        self,
        prompt: str,
        max_new_tokens: int = 200,
        stream: bool = False,
    ) -> str:
        """
        Generate a response.

        Args:
            prompt: User text input.
            max_new_tokens: Maximum tokens to generate.
            stream: If True, print tokens to stdout as they are generated
                    and return an empty string. If False, return the full response.

        Returns:
            Generated text (empty string when stream=True).
        """
        messages = [
            {"role": "user", "content": [{"type": "text", "text": prompt}]}
        ]
        inputs = self.processor.apply_chat_template(
            messages,
            add_generation_prompt=True,
            tokenize=True,
            return_tensors="pt",
            return_dict=True,
        )
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        if stream:
            streamer = TextStreamer(
                self.processor.tokenizer,
                skip_prompt=True,
                skip_special_tokens=True,
            )
            with torch.inference_mode():
                self.model.generate(
                    **inputs, max_new_tokens=max_new_tokens, streamer=streamer
                )
            return ""
        else:
            with torch.inference_mode():
                output_ids = self.model.generate(**inputs, max_new_tokens=max_new_tokens)
            input_len = inputs["input_ids"].shape[-1]
            generated = output_ids[:, input_len:]
            return self.processor.batch_decode(generated, skip_special_tokens=True)[0]

    def generate_stream(self, messages: list[dict], max_new_tokens: int = 200):
        """
        Yield text chunks incrementally (for use by the API layer).
        Args:
            messages: OpenAI-style message list, e.g.
                      [{"role": "user", "content": "hi"}]
        Yields:
            str: Text chunks as they are generated.
        """
        inputs = self.processor.apply_chat_template(
            messages,
            add_generation_prompt=True,
            tokenize=True,
            return_tensors="pt",
            return_dict=True,
        )
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

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


# ── ComfyUI custom node ───────────────────────────────────────────────────────

# Singleton so the model is loaded only once across multiple ComfyUI executions
_comfyui_service: Gemma4Service | None = None


def _get_comfyui_service() -> Gemma4Service:
    global _comfyui_service
    if _comfyui_service is None:
        _comfyui_service = Gemma4Service()
    return _comfyui_service


class Gemma4Node:
    """
    ComfyUI custom node for Gemma4 text generation.
    Place (or symlink) this file in:  ComfyUI/custom_nodes/gemma4_service.py
    """

    CATEGORY = "LLM"
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("response",)
    FUNCTION = "run"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt": ("STRING", {"multiline": True, "default": "你好！"}),
                "max_new_tokens": ("INT", {"default": 200, "min": 1, "max": 2048}),
            }
        }

    def run(self, prompt: str, max_new_tokens: int) -> tuple[str]:
        service = _get_comfyui_service()
        response = service.generate(prompt, max_new_tokens=max_new_tokens, stream=False)
        return (response,)


# Required by ComfyUI to discover the node
NODE_CLASS_MAPPINGS = {"Gemma4Node": Gemma4Node}
NODE_DISPLAY_NAME_MAPPINGS = {"Gemma4Node": "Gemma4 Text Generation"}


# ── CLI ───────────────────────────────────────────────────────────────────────


def _cli() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description="Gemma4 CLI — run without arguments for interactive mode"
    )
    parser.add_argument(
        "--prompt", "-p", type=str, default=None, help="Single prompt (non-interactive)"
    )
    parser.add_argument(
        "--max-tokens", type=int, default=200, help="Max new tokens (default: 200)"
    )
    parser.add_argument(
        "--no-stream", action="store_true", help="Disable streaming output"
    )
    parser.add_argument(
        "--model", type=str, default=DEFAULT_MODEL_ID, help="Model ID to load"
    )
    args = parser.parse_args()

    service = Gemma4Service(model_id=args.model)
    streaming = not args.no_stream

    if args.prompt:
        # Single-shot mode
        print(f"User: {args.prompt}")
        print("Assistant: ", end="", flush=True)
        response = service.generate(args.prompt, max_new_tokens=args.max_tokens, stream=streaming)
        if response:
            print(response)
        print()
    else:
        # Interactive mode
        print("\nGemma4 Interactive CLI  (type 'exit' or press Ctrl-C to quit)\n")
        while True:
            try:
                user_input = input("You: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nBye!")
                break

            if not user_input:
                continue
            if user_input.lower() in {"exit", "quit", "bye"}:
                print("Bye!")
                break

            print("Assistant: ", end="", flush=True)
            response = service.generate(
                user_input, max_new_tokens=args.max_tokens, stream=streaming
            )
            if response:
                print(response)
            print()


if __name__ == "__main__":
    _cli()
