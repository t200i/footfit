"""
deployment/PN54/serve.py — NPU API server (Composition Root)
=============================================================
Environment: ryzen-ai-1.7.1
Hardware:    Ryzen AI 350 (XDNA NPU)

Usage:
  conda activate ryzen-ai-1.7.1
  python deployment/PN54/serve.py --model ./Llama-3.2-3B-Instruct_rai_1.7.1_npu_16K
  python deployment/PN54/serve.py --model ./Llama-3.2-3B-Instruct_rai_1.7.1_npu_16K --host 0.0.0.0
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from models.npu.base import NpuTextLm
from interfaces.api import build_app


def main() -> None:
    import uvicorn

    parser = argparse.ArgumentParser(description="NPU API server — PN54")
    parser.add_argument(
        "--model",
        required=True,
        help="Local path to AMD NPU model directory (e.g. ./Llama-3.2-3B-Instruct_rai_1.7.1_npu_16K)",
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    svc = NpuTextLm(model_id=args.model)
    app = build_app(svc)
    print(f"[serve] {svc.model_id} → http://{args.host}:{args.port}/v1")
    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
