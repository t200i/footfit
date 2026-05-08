"""
interfaces/api.py — Generic OpenAI-compatible FastAPI server
=============================================================
Does NOT import any concrete model — only depends on core.module.ChatModel.
Called by deployment serve.py via build_app(model).
"""

from __future__ import annotations

import json
import time
import uuid
from typing import Iterator, Union

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from core.module import ChatModel


class Message(BaseModel):
    role: str
    content: Union[str, list]   # list for multimodal (OpenAI content-parts)


class ChatCompletionRequest(BaseModel):
    model: str = "default"
    messages: list[Message]
    max_tokens: int = 200
    stream: bool = False


def build_app(svc: ChatModel) -> FastAPI:
    """Return a FastAPI app bound to the given ChatModel instance."""

    app = FastAPI(title=f"{svc.model_id} — OpenAI-Compatible API", version="1.0.0")

    @app.get("/v1/models")
    def list_models():
        return {
            "object": "list",
            "data": [
                {
                    "id": svc.model_id,
                    "object": "model",
                    "created": int(time.time()),
                    "owned_by": "local",
                    "description": svc.description,
                }
            ],
        }

    @app.post("/v1/chat/completions")
    def chat_completions(req: ChatCompletionRequest):
        messages = [m.model_dump() for m in req.messages]

        if req.stream:
            return StreamingResponse(
                _stream(svc, messages, req),
                media_type="text/event-stream",
            )

        text = "".join(svc.create(messages, max_tokens=req.max_tokens))
        return _completion_response(svc.model_id, text)

    return app


def _completion_response(model_id: str, text: str) -> dict:
    return {
        "id": f"chatcmpl-{uuid.uuid4().hex}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": model_id,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": text},
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": -1, "completion_tokens": -1, "total_tokens": -1},
    }


def _stream(
    svc: ChatModel, messages: list[dict], req: ChatCompletionRequest
) -> Iterator[str]:
    cid = f"chatcmpl-{uuid.uuid4().hex}"
    ts  = int(time.time())

    for chunk in svc.create(messages, max_tokens=req.max_tokens):
        payload = {
            "id": cid,
            "object": "chat.completion.chunk",
            "created": ts,
            "model": svc.model_id,
            "choices": [{"index": 0, "delta": {"content": chunk}, "finish_reason": None}],
        }
        yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"

    final = {
        "id": cid,
        "object": "chat.completion.chunk",
        "created": ts,
        "model": svc.model_id,
        "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
    }
    yield f"data: {json.dumps(final)}\n\n"
    yield "data: [DONE]\n\n"
