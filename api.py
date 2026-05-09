import argparse
import json
import time
import uuid
from typing import Generator, Optional, Union

import uvicorn
from fastapi import FastAPI
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

from ryzenai.conversation import ConversationContext, Message
from ryzenai.conversation._utils import _now
from ryzenai.model import Model


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


# ── FastAPI App Factory ─────────────────────────────────────────────────────


def build(model: Model, model_name: str) -> FastAPI:
    app = FastAPI()

    @app.get("/v1/models")
    async def list_models():
        return {
            "object": "list",
            "data": [
                {
                    "id": model_name,
                    "object": "model",
                    "created": int(time.time()),
                    "owned_by": "ryzenai",
                }
            ],
        }

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

    return app


# ── Composition Root ─────────────────────────────────────────────────────────


def _build_model(model_id: str) -> Model:
    registry = {
        "gemma3-npu": lambda: _import_and_build(
            "ryzenai.modules.gemma3_4b_npu", "Gemma3_4B_NPU",
            "weights/Gemma-3-4b-it-mm-onnx-ryzenai-npu",
        ),
        "gemma4-gpu": lambda: _import_and_build(
            "ryzenai.modules.gemma4_e4b_gpu", "Gemma4_E4B_GPU",
            "google/gemma-4-E4B-it",
        ),
    }
    if model_id not in registry:
        raise ValueError(f"Unknown model: '{model_id}'. Available: {list(registry)}")
    return registry[model_id]()


def _import_and_build(module_path: str, class_name: str, *args):
    import importlib
    mod = importlib.import_module(module_path)
    cls = getattr(mod, class_name)
    return cls(*args)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="api.py", description="Ryzen AI REST API Server")
    parser.add_argument("-m", "--model", required=True, help="模型識別名稱（見 registry）")
    parser.add_argument("--host", default="0.0.0.0", help="監聽位址（預設 0.0.0.0）")
    parser.add_argument("--port", type=int, default=8000, help="監聽埠（預設 8000）")
    args = parser.parse_args()

    model = _build_model(args.model)
    app = build(model, model_name=args.model)
    uvicorn.run(app, host=args.host, port=args.port)
