"""
interfaces/cli.py — Generic CLI
================================
Does NOT import any concrete model — only depends on core.base.LLMService.
Called by serve.py.
"""

from __future__ import annotations

from core.base import LLMService


def run_single(svc: LLMService, prompt: str, max_tokens: int) -> None:
    messages = [{"role": "user", "content": prompt}]
    print(f"User: {prompt}")
    print("Assistant: ", end="", flush=True)
    for chunk in svc.generate_stream(messages, max_new_tokens=max_tokens):
        print(chunk, end="", flush=True)
    print()


def run_interactive(svc: LLMService, max_tokens: int) -> None:
    print(f"\n[{svc.info.name}] Interactive CLI  (type 'exit' to quit)\n")
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

        messages = [{"role": "user", "content": user_input}]
        print("Assistant: ", end="", flush=True)
        for chunk in svc.generate_stream(messages, max_new_tokens=max_tokens):
            print(chunk, end="", flush=True)
        print()
