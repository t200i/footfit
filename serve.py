"""
serve.py — OpenAI-compatible API server
=========================================
Loads a model by HuggingFace repo ID and starts an HTTP server.

Usage:
  python serve.py --model google/gemma-4-E4B-it
  python serve.py --model google/gemma-4-E4B-it --host 0.0.0.0 --port 8000

For CLI usage, see cli.py.

Adding a new model family:
  1. Create models/<name>.py — implement LLMService from core.base.
  2. Add a prefix entry to MODEL_REGISTRY below.
"""

from __future__ import annotations

import importlib

from core.base import LLMService

# ── Model registry ────────────────────────────────────────────────────────────
# key: HuggingFace repo ID prefix  →  value: (module path, class name)
# Prefix matching allows one entry to cover an entire model family.
# Example: "google/gemma-4" covers google/gemma-4-E2B-it, google/gemma-4-E4B-it …

MODEL_REGISTRY: dict[str, tuple[str, str]] = {
    "google/gemma-4": ("models.gemma4", "Gemma4Service"),
    # "meta-llama/":  ("models.llama",   "LlamaService"),
    # "HuggingFaceTB/SmolLM2": ("models.smollm2", "SmolLM2Service"),
}


def load_model(model_id: str) -> LLMService:
    for prefix, (module_path, class_name) in MODEL_REGISTRY.items():
        if model_id.startswith(prefix):
            module = importlib.import_module(module_path)
            cls = getattr(module, class_name)
            return cls(model_id=model_id)
    available = "\n  ".join(MODEL_REGISTRY)
    raise ValueError(
        f"No handler registered for '{model_id}'.\n"
        f"Registered prefixes:\n  {available}"
    )


# ── Main ──────────────────────────────────────────────────────────────────────


def main() -> None:
    import argparse
    import uvicorn
    from interfaces.api import build_app

    parser = argparse.ArgumentParser(description="Gemma4 OpenAI-Compatible API Server")
    parser.add_argument("--model", required=True, help="HuggingFace repo ID (e.g. google/gemma-4-E4B-it)")
    parser.add_argument("--host", default="127.0.0.1", help="Bind host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="Bind port (default: 8000)")
    args = parser.parse_args()

    svc = load_model(args.model)
    app = build_app(svc)
    print(f"[serve] {args.model} → http://{args.host}:{args.port}/v1")
    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
