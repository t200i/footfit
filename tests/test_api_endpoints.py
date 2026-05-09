"""
Crash scenario: api.py endpoints return wrong HTTP status or malformed JSON.
If /v1/chat/completions or /v1/models don't respond correctly, OpenAI SDK
and Open WebUI will fail to connect or parse responses.
"""
import pytest
from fastapi.testclient import TestClient
from tests.conftest import EchoText2Text
from api import build


@pytest.fixture
def client():
    model = EchoText2Text()
    app = build(model, model_name="echo-test")
    return TestClient(app)


class TestApiEndpoints:
    def test_models_endpoint(self, client):
        """GET /v1/models must return model list with correct id."""
        resp = client.get("/v1/models")
        assert resp.status_code == 200
        data = resp.json()
        assert data["object"] == "list"
        assert len(data["data"]) == 1
        assert data["data"][0]["id"] == "echo-test"
        assert data["data"][0]["owned_by"] == "ryzenai"

    def test_chat_completions_non_stream(self, client):
        """POST /v1/chat/completions (stream=false) returns full response."""
        resp = client.post("/v1/chat/completions", json={
            "model": "echo-test",
            "messages": [{"role": "user", "content": "hello"}],
            "stream": False,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["object"] == "chat.completion"
        assert data["choices"][0]["message"]["content"] == "hello"

    def test_chat_completions_stream(self, client):
        """POST /v1/chat/completions (stream=true) returns SSE stream."""
        resp = client.post("/v1/chat/completions", json={
            "model": "echo-test",
            "messages": [{"role": "user", "content": "hi"}],
            "stream": True,
        })
        assert resp.status_code == 200
        assert "text/event-stream" in resp.headers["content-type"]
        body = resp.text
        assert "data: [DONE]" in body

    def test_chat_completions_multimodal_content(self, client):
        """Multimodal content (list) is correctly processed."""
        resp = client.post("/v1/chat/completions", json={
            "model": "echo-test",
            "messages": [{
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,abc"}},
                    {"type": "text", "text": "describe"},
                ],
            }],
            "stream": False,
        })
        assert resp.status_code == 200

    def test_chat_completions_missing_messages(self, client):
        """Missing required field 'messages' returns 422."""
        resp = client.post("/v1/chat/completions", json={
            "model": "echo-test",
        })
        assert resp.status_code == 422
