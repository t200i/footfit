import argparse
import asyncio
import json
import logging
import os
import time
import uuid
from typing import Generator, Optional, Union, Annotated

logging.basicConfig(format="[%(name)s] %(message)s")
logging.getLogger("ryzenai").setLevel(logging.INFO)

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

from ryzenai.conversation import ConversationContext, Message
from ryzenai.conversation._utils import _now
from ryzenai.model import Model
from ryzenai.model import SegmentationModel
from ryzenai.registry import build_model, build_vision_model
from ryzenai.modules.sam3_segmentator import summarize_results


# ── Pydantic Schema ──────────────────────────────────────────────────────────


class _ContentPart(BaseModel):
    type: str
    text: Optional[str] = None
    image_url: Optional[dict] = None


class _RequestMessage(BaseModel):
    role: str
    content: Union[str, list[_ContentPart]]


class ChatCompletionRequest(BaseModel):
    model: str
    messages: list[_RequestMessage]
    stream: bool = False


# ── Helpers ──────────────────────────────────────────────────────────────────


def _build_response(content: str, model_name: str) -> dict:
    return {
        "id": f"chatcmpl-{uuid.uuid4().hex[:8]}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": model_name,
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": content,
                },
                "finish_reason": "stop",
            }
        ],
    }


def _sse_stream(
    tokens: Generator[str, None, None],
    model_name: str,
) -> Generator[str, None, None]:
    request_id = f"chatcmpl-{uuid.uuid4().hex[:8]}"
    created = int(time.time())

    def _chunk(delta: dict, finish_reason=None) -> str:
        payload = {
            "id": request_id,
            "object": "chat.completion.chunk",
            "created": created,
            "model": model_name,
            "choices": [{"index": 0, "delta": delta, "finish_reason": finish_reason}],
        }
        return f"data: {json.dumps(payload)}\n\n"

    yield _chunk({"role": "assistant", "content": ""})

    for token in tokens:
        yield _chunk({"content": token})

    yield _chunk({}, finish_reason="stop")

    yield "data: [DONE]\n\n"


def _build_segment_response(
    results: list,
    model_name: str,
    device: str,
    image_width: int,
    image_height: int,
    text: list[str],
    normalize: bool = False,
    decimals: int = 5,
) -> dict:
    detections = summarize_results(results, normalize=normalize, decimals=decimals)
    return {
        "object": "segment.result",
        "model": model_name,
        "device": device,
        "image": {"width": image_width, "height": image_height},
        "text": text,
        "count": len(detections),
        "detections": detections,
    }


# ── FastAPI App Factory ─────────────────────────────────────────────────────


def build(
    model: Model | None,
    model_name: str | None,
    vision_model: SegmentationModel | None = None,
    vision_model_name: str | None = None,
) -> FastAPI:
    app = FastAPI()

    @app.get("/healthz")
    async def healthz():
        models = []
        if model is not None and model_name is not None:
            models.append({"id": model_name, "task": "chat"})
        if vision_model is not None and vision_model_name is not None:
            models.append(
                {
                    "id": vision_model_name,
                    "task": "segment",
                    "device": getattr(vision_model, "device", "unknown"),
                    "torch_device_type": getattr(vision_model, "torch_device_type", None),
                }
            )
        return {
            "status": "ok",
            "service": "ryzenai-model-container",
            "models": models,
            "license": {
                "env": "AIHUB_LICENSE_KEY",
                "configured": bool(os.getenv("AIHUB_LICENSE_KEY")),
            },
        }

    @app.get("/v1/models")
    async def list_models():
        data = []
        if model is not None and model_name is not None:
            data.append(
                {
                    "id": model_name,
                    "object": "model",
                    "created": int(time.time()),
                    "owned_by": "ryzenai",
                }
            )
        if vision_model is not None and vision_model_name is not None:
            data.append(
                {
                    "id": vision_model_name,
                    "object": "model",
                    "created": int(time.time()),
                    "owned_by": "ryzenai",
                }
            )
        return {
            "object": "list",
            "data": data,
        }

    if model is not None:
        @app.post("/v1/chat/completions")
        async def chat_completions(request: ChatCompletionRequest):
            context = ConversationContext(
                messages=[
                    Message(
                        role=m.role,
                        content=(
                            m.content
                            if isinstance(m.content, str)
                            else [p.model_dump() for p in m.content]
                        ),
                        timestamp=_now(),
                    )
                    for m in request.messages
                ]
            )
            tokens = model(context)
            if request.stream:
                return StreamingResponse(
                    _sse_stream(tokens, request.model),
                    media_type="text/event-stream",
                )
            else:
                return JSONResponse(
                    _build_response("".join(tokens), request.model)
                )

    if vision_model is not None:
        segment_model_name = vision_model_name or model_name or "vision-model"

        @app.post("/v1/segment")
        async def segment(
            file: UploadFile = File(...),
            text: Annotated[list[str], Form()] = ["object"],
            conf: float = Form(0.25),
            iou: float = Form(0.7),
            normalize: bool = Form(False),
            decimals: int = Form(5),
        ):
            try:
                import cv2
                import numpy as np
            except Exception as exc:
                raise HTTPException(status_code=500, detail=f"Segmentation dependencies unavailable: {exc}") from exc

            arr = np.frombuffer(await file.read(), dtype=np.uint8)
            image = cv2.imdecode(arr, cv2.IMREAD_COLOR)
            if image is None:
                raise HTTPException(status_code=400, detail="Invalid image")

            image_height, image_width = image.shape[:2]
            try:
                results = await asyncio.to_thread(
                    vision_model.predict,
                    image,
                    text=text,
                    conf=conf,
                    iou=iou,
                )
            except Exception as exc:
                raise HTTPException(status_code=500, detail=f"Segmentation inference error: {exc}") from exc

            return JSONResponse(
                _build_segment_response(
                    results=results,
                    model_name=segment_model_name,
                    device=getattr(vision_model, "device", "unknown"),
                    image_width=image_width,
                    image_height=image_height,
                    text=text,
                    normalize=normalize,
                    decimals=decimals,
                )
            )

    return app


# ── Composition Root ─────────────────────────────────────────────────────────


if __name__ == "__main__":
    import uvicorn

    parser = argparse.ArgumentParser(prog="api.py", description="Ryzen AI REST API Server")
    parser.add_argument("-m", "--model", default=None, help="聊天模型識別名稱（見 registry）")
    parser.add_argument("--vision-model", default=None, help="Vision/SAM3 模型識別名稱（見 vision registry）")
    parser.add_argument("--host", default="0.0.0.0", help="監聽位址（預設 0.0.0.0）")
    parser.add_argument("--port", type=int, default=8000, help="監聽埠（預設 8000）")
    args = parser.parse_args()

    if args.model is None and args.vision_model is None:
        parser.error("至少需要指定 --model 或 --vision-model")

    model = build_model(args.model) if args.model is not None else None
    vision_model = build_vision_model(args.vision_model) if args.vision_model is not None else None
    app = build(
        model,
        model_name=args.model,
        vision_model=vision_model,
        vision_model_name=args.vision_model,
    )
    uvicorn.run(app, host=args.host, port=args.port)
