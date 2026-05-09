import argparse
import json
import logging
import time
import uuid
from typing import Generator, Optional, Union

logging.basicConfig(format="[%(name)s] %(message)s")
logging.getLogger("ryzenai").setLevel(logging.INFO)

import uvicorn
from fastapi import FastAPI
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

from ryzenai.conversation import ConversationContext, Message
from ryzenai.conversation._utils import _now
from ryzenai.model import Model
from ryzenai.registry import build_model, available_models


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


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="api.py", description="Ryzen AI REST API Server")
    parser.add_argument("-m", "--model", required=True, help="模型識別名稱（見 registry）")
    parser.add_argument("--host", default="0.0.0.0", help="監聽位址（預設 0.0.0.0）")
    parser.add_argument("--port", type=int, default=8000, help="監聽埠（預設 8000）")
    args = parser.parse_args()

    model = build_model(args.model)
    app = build(model, model_name=args.model)
    uvicorn.run(app, host=args.host, port=args.port)
