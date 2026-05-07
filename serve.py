"""
serve.py — Unified entry point
================================
Wires a model from models/ to an interface (api | cli | comfyui-hint).

Usage:
  python serve.py --model gemma4 --mode api
  python serve.py --model gemma4 --mode api --host 0.0.0.0 --port 8000
  python serve.py --model gemma4 --mode cli
  python serve.py --model gemma4 --mode cli --prompt "你好"

Adding a new model:
  1. Create models/<your_model>.py — implement LLMService from core.base.
  2. Register it in MODEL_REGISTRY below.
  That's it. CLI, API, and ComfyUI support it automatically.
"""

from __future__ import annotations

import argparse
import importlib

from core.base import LLMService

# ── Model registry ────────────────────────────────────────────────────────────
# key: CLI name  →  value: (module path, class name)
# Add new models here — no other file needs to change.

MODEL_REGISTRY: dict[str, tuple[str, str]] = {
    "gemma4": ("models.gemma4", "Gemma4Service"),
    # "llama":   ("models.llama",  "LlamaService"),
    # "smollm2": ("models.smollm2", "SmolLM2Service"),
}


def load_model(name: str) -> LLMService:
    if name not in MODEL_REGISTRY:
        available = ", ".join(MODEL_REGISTRY)
        raise ValueError(f"Unknown model '{name}'. Available: {available}")
    module_path, class_name = MODEL_REGISTRY[name]
    module = importlib.import_module(module_path)
    cls = getattr(module, class_name)
    return cls()


# ── Interface runners ─────────────────────────────────────────────────────────


def run_api(model: LLMService, host: str, port: int) -> None:
    from interfaces.api import build_app
    import uvicorn

    app = build_app(model)
    print(f"[serve] API server → http://{host}:{port}/v1")
    uvicorn.run(app, host=host, port=port)


def run_cli(model: LLMService, prompt: str | None, max_tokens: int) -> None:
    from interfaces.cli import run_interactive, run_single

    if prompt:
        run_single(model, prompt, max_tokens)
    else:
        run_interactive(model, max_tokens)


# ── Main ──────────────────────────────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser(description="Unified model server / CLI")
    parser.add_argument(
        "--model", required=True,
        choices=list(MODEL_REGISTRY),
        help="Model to load",
    )
    parser.add_argument(
        "--mode", required=True,
        choices=["api", "cli"],
        help="Interface to expose",
    )
    # API options
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    # CLI options
    parser.add_argument("--prompt", "-p", default=None)
    parser.add_argument("--max-tokens", type=int, default=200)
    args = parser.parse_args()

    svc = load_model(args.model)

    if args.mode == "api":
        run_api(svc, args.host, args.port)
    elif args.mode == "cli":
        run_cli(svc, args.prompt, args.max_tokens)


if __name__ == "__main__":
    main()
