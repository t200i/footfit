"""
cli.py — Interactive / single-shot CLI
========================================
Usage:
  python cli.py --model google/gemma-4-E4B-it
  python cli.py --model google/gemma-4-E4B-it --prompt "解釋量子計算"
  python cli.py --model google/gemma-4-E4B-it --prompt "hello" --max-tokens 100

For API server usage, see serve.py.
"""

from __future__ import annotations

import argparse

from serve import load_model
from interfaces.cli import run_interactive, run_single


def main() -> None:
    parser = argparse.ArgumentParser(description="Ryzen AI LLM CLI")
    parser.add_argument(
        "--model", required=True,
        help="HuggingFace repo ID (e.g. google/gemma-4-E4B-it)",
    )
    parser.add_argument(
        "--prompt", "-p", default=None,
        help="Single prompt — omit for interactive mode",
    )
    parser.add_argument(
        "--max-tokens", type=int, default=200,
        help="Max new tokens (default: 200)",
    )
    args = parser.parse_args()

    svc = load_model(args.model)

    if args.prompt:
        run_single(svc, args.prompt, args.max_tokens)
    else:
        run_interactive(svc, args.max_tokens)


if __name__ == "__main__":
    main()
