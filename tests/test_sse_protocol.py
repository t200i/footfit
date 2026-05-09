"""
Crash scenario: SSE stream format violates OpenAI protocol.
If chunks are malformed, OpenAI SDK and Open WebUI will fail to parse
the stream — connection hangs or throws parse errors.
"""
import json
from tests.conftest import EchoText2Text
from api import _sse_stream, _build_response


def _token_gen():
    yield "Hello"
    yield " world"


class TestSSEStreamProtocol:
    def test_first_chunk_has_role(self):
        """First chunk delta must contain role='assistant' and content=''."""
        chunks = list(_sse_stream(_token_gen(), "test-model"))
        first = chunks[0]
        assert first.startswith("data: ")
        assert first.endswith("\n\n")
        payload = json.loads(first[6:].strip())
        delta = payload["choices"][0]["delta"]
        assert delta["role"] == "assistant"
        assert delta["content"] == ""

    def test_middle_chunks_have_content(self):
        """Middle chunks must have delta with content only (no role)."""
        chunks = list(_sse_stream(_token_gen(), "test-model"))
        # chunks[1] = "Hello", chunks[2] = " world"
        for chunk in chunks[1:-2]:  # exclude finish + DONE
            payload = json.loads(chunk[6:].strip())
            delta = payload["choices"][0]["delta"]
            assert "content" in delta
            assert "role" not in delta

    def test_finish_chunk_has_stop(self):
        """Second-to-last chunk must have finish_reason='stop' and empty delta."""
        chunks = list(_sse_stream(_token_gen(), "test-model"))
        finish = chunks[-2]
        payload = json.loads(finish[6:].strip())
        assert payload["choices"][0]["finish_reason"] == "stop"
        assert payload["choices"][0]["delta"] == {}

    def test_done_signal(self):
        """Last chunk must be 'data: [DONE]\\n\\n'."""
        chunks = list(_sse_stream(_token_gen(), "test-model"))
        assert chunks[-1] == "data: [DONE]\n\n"

    def test_consistent_id_across_chunks(self):
        """All JSON chunks must share the same id and created timestamp."""
        chunks = list(_sse_stream(_token_gen(), "test-model"))
        json_chunks = [c for c in chunks if c != "data: [DONE]\n\n"]
        payloads = [json.loads(c[6:].strip()) for c in json_chunks]
        ids = {p["id"] for p in payloads}
        created_set = {p["created"] for p in payloads}
        assert len(ids) == 1, f"IDs not consistent: {ids}"
        assert len(created_set) == 1, f"Created not consistent: {created_set}"

    def test_object_is_chunk_type(self):
        """All JSON chunks must have object='chat.completion.chunk'."""
        chunks = list(_sse_stream(_token_gen(), "test-model"))
        json_chunks = [c for c in chunks if c != "data: [DONE]\n\n"]
        for c in json_chunks:
            payload = json.loads(c[6:].strip())
            assert payload["object"] == "chat.completion.chunk"

    def test_each_chunk_ends_with_double_newline(self):
        """SSE spec: every chunk must end with \\n\\n."""
        chunks = list(_sse_stream(_token_gen(), "test-model"))
        for chunk in chunks:
            assert chunk.endswith("\n\n")


class TestBuildResponse:
    def test_non_stream_response_structure(self):
        """_build_response must return valid OpenAI chat.completion format."""
        resp = _build_response("hello", "test-model")
        assert resp["object"] == "chat.completion"
        assert resp["model"] == "test-model"
        assert resp["choices"][0]["message"]["role"] == "assistant"
        assert resp["choices"][0]["message"]["content"] == "hello"
        assert resp["choices"][0]["finish_reason"] == "stop"

    def test_non_stream_response_has_id(self):
        resp = _build_response("x", "m")
        assert resp["id"].startswith("chatcmpl-")

    def test_non_stream_response_has_created(self):
        resp = _build_response("x", "m")
        assert isinstance(resp["created"], int)
