"""
deployment/vivobook_s_15_16/serve.py — iGPU API server (Composition Root)
==========================================================================
Environment: rocm-pytorch
Hardware:    Ryzen AI 9 HX 370 (RDNA iGPU)

Usage:
  conda activate rocm-pytorch
  python deployment/vivobook_s_15_16/serve.py --model google/gemma-4-E4B-it
  python deployment/vivobook_s_15_16/serve.py --model google/gemma-4-E4B-it --host 0.0.0.0 --port 8000
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Add project root to path so core/ models/ interfaces/ are importable
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from models.igpu.base import IgpuVisionLm
from interfaces.api import build_app


def main() -> None:
    import uvicorn

    parser = argparse.ArgumentParser(description="iGPU API server — Vivobook S 15/16")
    parser.add_argument(
        "--model",
        default="google/gemma-4-E4B-it",
        help="HuggingFace repo ID (default: google/gemma-4-E4B-it)",
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    svc = IgpuVisionLm(model_id=args.model)
    app = build_app(svc)
    print(f"[serve] {args.model} → http://{args.host}:{args.port}/v1")
    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
