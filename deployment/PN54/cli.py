"""
deployment/PN54/cli.py — NPU CLI (Composition Root)
====================================================
Environment: ryzen-ai-1.7.1
Hardware:    Ryzen AI 350 (XDNA NPU)

Usage:
  conda activate ryzen-ai-1.7.1
  python deployment/PN54/cli.py --model ./Llama-3.2-3B-Instruct_rai_1.7.1_npu_16K
  python deployment/PN54/cli.py --model ./Phi-4-mini-instruct_rai_1.7.1_npu_16K --prompt "你好"
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from models.npu.base import NpuTextLm
from interfaces.cli import run_interactive, run_single


def main() -> None:
    parser = argparse.ArgumentParser(description="NPU CLI — PN54")
    parser.add_argument(
        "--model",
        required=True,
        help="Local path to AMD NPU model directory (e.g. ./Llama-3.2-3B-Instruct_rai_1.7.1_npu_16K)",
    )
    parser.add_argument("--prompt", "-p", default=None)
    parser.add_argument("--max-tokens", type=int, default=256)
    args = parser.parse_args()

    svc = NpuTextLm(model_id=args.model)

    if args.prompt:
        run_single(svc, args.prompt, args.max_tokens)
    else:
        run_interactive(svc, args.max_tokens)


if __name__ == "__main__":
    main()
