"""
Crash scenario: Content conversion between Pydantic and Message breaks.
api.py must correctly convert _ContentPart (Pydantic) → dict (Message.content).
If model_dump() is missing or wrong, modules/generate() receives Pydantic
objects instead of dicts and crashes on dict key access.
"""
import pytest
from fastapi.testclient import TestClient
from tests.conftest import EchoImageText2Text
from api import build


@pytest.fixture
def client():
    model = EchoImageText2Text()
    app = build(model, model_name="echo-vlm")
    return TestClient(app)


class TestContentConversion:
    def test_str_content_passthrough(self, client):
        """String content should pass through unchanged."""
        resp = client.post("/v1/chat/completions", json={
            "model": "echo-vlm",
            "messages": [{"role": "user", "content": "hello"}],
            "stream": False,
        })
        assert resp.status_code == 200
        assert resp.json()["choices"][0]["message"]["content"] == "hello"

    def test_list_content_converted_to_dicts(self, client):
        """List content (Pydantic _ContentPart) must be converted to dicts via model_dump()."""
        resp = client.post("/v1/chat/completions", json={
            "model": "echo-vlm",
            "messages": [{
                "role": "user",
                "content": [
                    {"type": "text", "text": "describe this"},
                    {"type": "image_url", "image_url": {"url": "data:image/png;base64,xyz"}},
                ],
            }],
            "stream": False,
        })
        assert resp.status_code == 200
        # EchoImageText2Text extracts text parts → "describe this"
        content = resp.json()["choices"][0]["message"]["content"]
        assert "describe this" in content
