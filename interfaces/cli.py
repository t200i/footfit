"""
interfaces/cli.py — Generic interactive CLI
============================================
Does NOT import any concrete model — only depends on core.module.ChatModel.
Called by deployment cli.py.

Supports multimodal input via --image: the image is base64-encoded and
injected as an OpenAI image_url content part.
"""

from __future__ import annotations

import base64
from pathlib import Path

from core.module import ChatModel


def _image_to_content_part(image_path: str) -> dict:
    """Read an image file and return an OpenAI image_url content part."""
    data = Path(image_path).read_bytes()
    suffix = Path(image_path).suffix.lower().lstrip(".")
    mime = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png"}.get(suffix, "image/jpeg")
    b64 = base64.b64encode(data).decode()
    return {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}}


def _build_messages(prompt: str, image_path: str | None) -> list[dict]:
    if image_path:
        content = [
            _image_to_content_part(image_path),
            {"type": "text", "text": prompt},
        ]
    else:
        content = prompt
    return [{"role": "user", "content": content}]


def run_single(svc: ChatModel, prompt: str, max_tokens: int, image: str | None = None) -> None:
    messages = _build_messages(prompt, image)
    print(f"User: {prompt}")
    print("Assistant: ", end="", flush=True)
    for chunk in svc.create(messages, max_tokens=max_tokens):
        print(chunk, end="", flush=True)
    print()


def run_interactive(svc: ChatModel, max_tokens: int, image: str | None = None) -> None:
    print(f"\n[{svc.model_id}] Interactive CLI  (type 'exit' to quit)\n")
    if image:
        print(f"[image: {image}]\n")
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

        messages = _build_messages(user_input, image)
        print("Assistant: ", end="", flush=True)
        for chunk in svc.create(messages, max_tokens=max_tokens):
            print(chunk, end="", flush=True)
        print()
        image = None   # image applies only to the first turn
