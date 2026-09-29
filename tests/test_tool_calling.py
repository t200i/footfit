"""
Crash scenario: function calling 協定錯誤。
若 tool_calls 格式不符 OpenAI 規範，Open WebUI 的原生 function calling
（Skills 按需載入的 view_skill）會無法觸發，或把工具呼叫當成亂碼文字顯示。
"""
import json
from typing import Generator

import pytest
from fastapi.testclient import TestClient

from api import build, _sse_stream, _build_response
from ryzenai.conversation import ConversationContext, ToolCall
from ryzenai.model import Text2Text
from ryzenai.modules.gemma4_tool_parser import Gemma4StreamParser, parse_tool_call
from tests.conftest import MockBackend

Q = '<|"|>'


# ── Gemma4 output parser ─────────────────────────────────────────────────────


def _feed_all(raw: str, step: int) -> list:
    parser = Gemma4StreamParser()
    out = []
    for i in range(0, len(raw), step):
        out.extend(parser.feed(raw[i:i + step]))
    out.extend(parser.flush())
    return out


class TestGemma4Parser:
    def test_parse_string_and_int_args(self):
        tc = parse_tool_call(f"call:get_weather{{city:{Q}台北{Q},days:3}}")
        assert tc.name == "get_weather"
        assert tc.arguments == {"city": "台北", "days": 3}

    def test_parse_nested_and_scalars(self):
        tc = parse_tool_call(
            f"call:f{{a:{{b:[1,{Q}x, y{Q},true]}},c:null,d:1.5,e:false}}"
        )
        assert tc.arguments == {"a": {"b": [1, "x, y", True]}, "c": None, "d": 1.5, "e": False}

    def test_parse_no_args(self):
        assert parse_tool_call("call:ping{}").arguments == {}

    def test_string_may_contain_braces(self):
        tc = parse_tool_call(f"call:run{{code:{Q}def f(): return {{1: [2]}}{Q}}}")
        assert tc.arguments == {"code": "def f(): return {1: [2]}"}

    @pytest.mark.parametrize("step", [1, 3, 1000])
    def test_stream_tool_call_split_across_chunks(self, step):
        raw = f"<|tool_call>call:view_skill{{skill_id:{Q}haiku-writer{Q}}}<tool_call|><|tool_response>"
        out = _feed_all(raw, step)
        assert len(out) == 1
        assert isinstance(out[0], ToolCall)
        assert out[0].name == "view_skill"
        assert out[0].arguments == {"skill_id": "haiku-writer"}

    @pytest.mark.parametrize("step", [1, 2, 1000])
    def test_stream_plain_text_drops_end_of_turn(self, step):
        out = _feed_all("你好！<b>ok</b> a < b<turn|>", step)
        assert all(isinstance(x, str) for x in out)
        assert "".join(out) == "你好！<b>ok</b> a < b"

    def test_stream_drops_thinking_channel(self):
        out = _feed_all("<|channel>thought\nhmm<channel|>答案<turn|>", 1)
        assert "".join(out) == "答案"

    def test_stream_text_then_multiple_calls(self):
        raw = f"查詢中<|tool_call>call:a{{x:1}}<tool_call|><|tool_call>call:b{{y:{Q}z{Q}}}<tool_call|>"
        out = _feed_all(raw, 4)
        assert out[0] == "查詢中"
        assert [(c.name, c.arguments) for c in out[1:]] == [("a", {"x": 1}), ("b", {"y": "z"})]


# ── API protocol ─────────────────────────────────────────────────────────────


class ToolAwareModel(Text2Text):
    """有 tools 時呼叫第一個工具；收到 tool 結果後以文字回覆結果內容。"""

    def __init__(self) -> None:
        super().__init__(MockBackend())
        self.last_context: ConversationContext | None = None

    def generate(self, context: ConversationContext) -> Generator:
        self.last_context = context
        last = context.messages[-1]
        if last.role == "tool":
            yield f"result={last.content}"
        elif context.metadata.get("tools"):
            name = context.metadata["tools"][0]["function"]["name"]
            yield ToolCall(name=name, arguments={"skill_id": "haiku"}, id="call_1")
        else:
            yield "plain"


TOOLS = [{
    "type": "function",
    "function": {
        "name": "view_skill",
        "description": "Load a skill",
        "parameters": {"type": "object", "properties": {"skill_id": {"type": "string"}}},
    },
}]


@pytest.fixture
def model():
    return ToolAwareModel()


@pytest.fixture
def client(model):
    return TestClient(build(model, model_name="tool-test"))


class TestToolCallingApi:
    def test_non_stream_returns_tool_calls(self, client):
        resp = client.post("/v1/chat/completions", json={
            "model": "tool-test",
            "messages": [{"role": "user", "content": "寫俳句"}],
            "tools": TOOLS,
        })
        choice = resp.json()["choices"][0]
        assert choice["finish_reason"] == "tool_calls"
        assert choice["message"]["content"] is None
        tc = choice["message"]["tool_calls"][0]
        assert tc["id"] == "call_1"
        assert tc["type"] == "function"
        assert tc["function"]["name"] == "view_skill"
        assert json.loads(tc["function"]["arguments"]) == {"skill_id": "haiku"}

    def test_stream_emits_tool_call_delta(self, client):
        resp = client.post("/v1/chat/completions", json={
            "model": "tool-test",
            "messages": [{"role": "user", "content": "寫俳句"}],
            "tools": TOOLS,
            "stream": True,
        })
        payloads = [
            json.loads(line[6:]) for line in resp.text.splitlines()
            if line.startswith("data: ") and line != "data: [DONE]"
        ]
        deltas = [p["choices"][0]["delta"] for p in payloads]
        tool_deltas = [d["tool_calls"][0] for d in deltas if "tool_calls" in d]
        assert tool_deltas == [{
            "index": 0, "id": "call_1", "type": "function",
            "function": {"name": "view_skill", "arguments": '{"skill_id": "haiku"}'},
        }]
        assert payloads[-1]["choices"][0]["finish_reason"] == "tool_calls"

    def test_tool_choice_none_hides_tools(self, client, model):
        resp = client.post("/v1/chat/completions", json={
            "model": "tool-test",
            "messages": [{"role": "user", "content": "hi"}],
            "tools": TOOLS,
            "tool_choice": "none",
        })
        assert resp.json()["choices"][0]["message"]["content"] == "plain"
        assert "tools" not in model.last_context.metadata

    def test_tool_result_round_trip(self, client, model):
        """assistant tool_calls（arguments 為 JSON 字串）+ role=tool 結果可被接受並轉入 context。"""
        resp = client.post("/v1/chat/completions", json={
            "model": "tool-test",
            "messages": [
                {"role": "user", "content": "寫俳句"},
                {"role": "assistant", "content": None, "tool_calls": [{
                    "id": "call_1", "type": "function",
                    "function": {"name": "view_skill", "arguments": '{"skill_id": "haiku"}'},
                }]},
                {"role": "tool", "tool_call_id": "call_1", "content": "SKILL BODY"},
            ],
            "tools": TOOLS,
        })
        assert resp.status_code == 200
        assert resp.json()["choices"][0]["message"]["content"] == "result=SKILL BODY"
        assistant = model.last_context.messages[1]
        assert assistant.content is None
        assert assistant.tool_calls == (ToolCall(name="view_skill", arguments={"skill_id": "haiku"}, id="call_1"),)
        assert model.last_context.messages[2].tool_call_id == "call_1"

    def test_no_tools_behaves_as_before(self, client):
        resp = client.post("/v1/chat/completions", json={
            "model": "tool-test",
            "messages": [{"role": "user", "content": "hi"}],
        })
        choice = resp.json()["choices"][0]
        assert choice["finish_reason"] == "stop"
        assert "tool_calls" not in choice["message"]


class TestHelpers:
    def test_build_response_with_text_and_tool_calls(self):
        resp = _build_response("先查一下", "m", tool_calls=[ToolCall("f", {}, id="c")])
        msg = resp["choices"][0]["message"]
        assert msg["content"] == "先查一下"
        assert msg["tool_calls"][0]["function"]["arguments"] == "{}"

    def test_sse_multiple_tool_calls_indexed(self):
        chunks = list(_sse_stream(iter([ToolCall("a", {}), ToolCall("b", {})]), "m"))
        deltas = [json.loads(c[6:])["choices"][0]["delta"] for c in chunks[:-1]]
        idx = [d["tool_calls"][0]["index"] for d in deltas if "tool_calls" in d]
        assert idx == [0, 1]
