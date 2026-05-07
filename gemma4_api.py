"""
Gemma4 OpenAI-Compatible API Server
=====================================
Depends on: fastapi, uvicorn, gemma4_service.py

Install:
  pip install fastapi uvicorn

Run:
  python gemma4_api.py                        # localhost:8000
  python gemma4_api.py --host 0.0.0.0 --port 8080

Client usage (OpenAI SDK):
  from openai import OpenAI
  client = OpenAI(base_url="http://localhost:8000/v1", api_key="local")
  resp = client.chat.completions.create(
      model="gemma4",
      messages=[{"role": "user", "content": "你好"}],
      stream=True,
  )
  for chunk in resp:
      print(chunk.choices[0].delta.content or "", end="", flush=True)
"""

from __future__ import annotations

import json
import time
import uuid
from typing import Iterator

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from gemma4_service import Gemma4Service, DEFAULT_MODEL_ID

# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(title="Gemma4 OpenAI-Compatible API", version="1.0.0")

# Lazy-loaded singleton — model loads on first request
_service: Gemma4Service | None = None


def get_service() -> Gemma4Service:
    global _service
    if _service is None:
        _service = Gemma4Service()
    return _service


# ── OpenAI-compatible schemas ─────────────────────────────────────────────────


class Message(BaseModel):
    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    model: str = DEFAULT_MODEL_ID
    messages: list[Message]
    max_tokens: int = 200
    stream: bool = False


# ── Routes ────────────────────────────────────────────────────────────────────


@app.get("/v1/models")
def list_models():
    return {
        "object": "list",
        "data": [
            {
                "id": DEFAULT_MODEL_ID,
                "object": "model",
                "created": int(time.time()),
                "owned_by": "google",
            }
        ],
    }


@app.post("/v1/chat/completions")
def chat_completions(req: ChatCompletionRequest):
    svc = get_service()
    messages = [m.model_dump() for m in req.messages]

    if req.stream:
        return StreamingResponse(
            _stream_response(svc, messages, req),
            media_type="text/event-stream",
        )

    # ── Non-streaming ──
    # Build full text from generator to reuse generate_stream
    response_text = "".join(svc.generate_stream(messages, max_new_tokens=req.max_tokens))
    return {
        "id": f"chatcmpl-{uuid.uuid4().hex}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": req.model,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": response_text},
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": -1, "completion_tokens": -1, "total_tokens": -1},
    }


def _stream_response(
    svc: Gemma4Service,
    messages: list[dict],
    req: ChatCompletionRequest,
) -> Iterator[str]:
    completion_id = f"chatcmpl-{uuid.uuid4().hex}"
    created = int(time.time())

    for chunk_text in svc.generate_stream(messages, max_new_tokens=req.max_tokens):
        payload = {
            "id": completion_id,
            "object": "chat.completion.chunk",
            "created": created,
            "model": req.model,
            "choices": [
                {
                    "index": 0,
                    "delta": {"content": chunk_text},
                    "finish_reason": None,
                }
            ],
        }
        yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"

    # Final chunk signaling stop
    final = {
        "id": completion_id,
        "object": "chat.completion.chunk",
        "created": created,
        "model": req.model,
        "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
    }
    yield f"data: {json.dumps(final)}\n\n"
    yield "data: [DONE]\n\n"


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    import uvicorn

    parser = argparse.ArgumentParser(description="Gemma4 OpenAI-Compatible API Server")
    parser.add_argument("--host", default="127.0.0.1", help="Bind host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="Bind port (default: 8000)")
    args = parser.parse_args()

    print(f"Starting server at http://{args.host}:{args.port}/v1")
    uvicorn.run(app, host=args.host, port=args.port)
