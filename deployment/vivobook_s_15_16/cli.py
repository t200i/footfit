"""
deployment/vivobook_s_15_16/cli.py — iGPU CLI (Composition Root)
=================================================================
Environment: rocm-pytorch
Hardware:    Ryzen AI 9 HX 370 (RDNA iGPU)

Usage:
  conda activate rocm-pytorch
  python deployment/vivobook_s_15_16/cli.py --model google/gemma-4-E4B-it
  python deployment/vivobook_s_15_16/cli.py --model google/gemma-4-E4B-it --prompt "你好"
  python deployment/vivobook_s_15_16/cli.py --model google/gemma-4-E4B-it --prompt "這是什麼?" --image cat.jpg
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from models.igpu.base import IgpuVisionLm
from interfaces.cli import run_interactive, run_single


def main() -> None:
    parser = argparse.ArgumentParser(description="iGPU CLI — Vivobook S 15/16")
    parser.add_argument(
        "--model",
        default="google/gemma-4-E4B-it",
        help="HuggingFace repo ID (default: google/gemma-4-E4B-it)",
    )
    parser.add_argument("--prompt", "-p", default=None)
    parser.add_argument("--image",  "-i", default=None, help="Path to image file (for VLM)")
    parser.add_argument("--max-tokens", type=int, default=200)
    args = parser.parse_args()

    svc = IgpuVisionLm(model_id=args.model)

    if args.prompt:
        run_single(svc, args.prompt, args.max_tokens, image=args.image)
    else:
        run_interactive(svc, args.max_tokens, image=args.image)


if __name__ == "__main__":
    main()
