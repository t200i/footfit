"""
Gemma 4 輸出解析 — 將模型原始輸出（保留 special tokens）拆成文字與 ToolCall。

Gemma 4 的工具呼叫格式（見 chat_template.jinja）：
    <|tool_call>call:get_weather{city:<|"|>台北<|"|>,days:3}<tool_call|>
字串以 <|"|> 包夾，key 不加引號，可巢狀 {} / []。

本模組不依賴 torch / transformers，可在無硬體的 CI 上測試。
"""
from typing import Union

from ryzenai.conversation import ToolCall

_TOOL_OPEN, _TOOL_CLOSE = "<|tool_call>", "<tool_call|>"
_CHANNEL_OPEN, _CHANNEL_CLOSE = "<|channel>", "<channel|>"
_QUOTE = '<|"|>'
# 回合結束 / 停止符號，直接丟棄
_DROP = ("<turn|>", "<eos>", "<|tool_response>", "<pad>")

_OPENERS = (_TOOL_OPEN, _CHANNEL_OPEN, *_DROP)


class Gemma4StreamParser:
    """逐段餵入串流文字，產出 str（可顯示文字）或 ToolCall。

    標記可能被切在兩個 chunk 之間，因此尾端若可能是標記的開頭會先暫留。
    """

    def __init__(self) -> None:
        self._buf = ""
        self._mode: str | None = None  # None | "call" | "channel"

    def feed(self, chunk: str) -> list[Union[str, ToolCall]]:
        self._buf += chunk
        out: list[Union[str, ToolCall]] = []
        while True:
            if self._mode == "call":
                end = self._buf.find(_TOOL_CLOSE)
                if end < 0:
                    break
                out.append(parse_tool_call(self._buf[:end]))
                self._buf = self._buf[end + len(_TOOL_CLOSE):]
                self._mode = None
            elif self._mode == "channel":
                end = self._buf.find(_CHANNEL_CLOSE)
                if end < 0:
                    break
                self._buf = self._buf[end + len(_CHANNEL_CLOSE):]
                self._mode = None
            else:
                hits = [(i, m) for m in _OPENERS if (i := self._buf.find(m)) >= 0]
                if not hits:
                    keep = _partial_marker_len(self._buf)
                    text = self._buf[: len(self._buf) - keep]
                    if text:
                        out.append(text)
                    self._buf = self._buf[len(self._buf) - keep:]
                    break
                i, marker = min(hits)
                if i > 0:
                    out.append(self._buf[:i])
                self._buf = self._buf[i + len(marker):]
                if marker == _TOOL_OPEN:
                    self._mode = "call"
                elif marker == _CHANNEL_OPEN:
                    self._mode = "channel"
        return out

    def flush(self) -> list[Union[str, ToolCall]]:
        """串流結束時呼叫；未閉合的 tool_call / thinking 內容會被丟棄。"""
        rest, mode = self._buf, self._mode
        self._buf, self._mode = "", None
        return [rest] if rest and mode is None else []


def _partial_marker_len(buf: str) -> int:
    """buf 尾端與任一標記開頭重疊的最長長度。"""
    best = 0
    for marker in _OPENERS:
        for k in range(min(len(marker) - 1, len(buf)), best, -1):
            if marker.startswith(buf[-k:]):
                best = k
                break
    return best


def parse_tool_call(body: str) -> ToolCall:
    """解析 `call:name{...}`（不含外層 <|tool_call> 標記）。"""
    body = body.strip()
    if body.startswith("call:"):
        body = body[len("call:"):]
    brace = body.find("{")
    if brace < 0:
        return ToolCall(name=body.strip(), arguments={})
    name = body[:brace].strip()
    value, _ = _Reader(body, brace).read_value()
    return ToolCall(name=name, arguments=value if isinstance(value, dict) else {"value": value})


class _Reader:
    def __init__(self, text: str, pos: int) -> None:
        self.s, self.i = text, pos

    def read_value(self):
        s = self.s
        if s.startswith(_QUOTE, self.i):
            end = s.find(_QUOTE, self.i + len(_QUOTE))
            if end < 0:
                end = len(s)
            value = s[self.i + len(_QUOTE):end]
            self.i = end + len(_QUOTE)
            return value, self.i
        if self.i < len(s) and s[self.i] == "{":
            return self._read_object(), self.i
        if self.i < len(s) and s[self.i] == "[":
            return self._read_array(), self.i
        start = self.i
        while self.i < len(s) and s[self.i] not in ",}]":
            self.i += 1
        return _scalar(s[start:self.i].strip()), self.i

    def _read_object(self) -> dict:
        s, obj = self.s, {}
        self.i += 1  # {
        while self.i < len(s) and s[self.i] != "}":
            if s[self.i] == ",":
                self.i += 1
                continue
            if s.startswith(_QUOTE, self.i):
                key, _ = self.read_value()
            else:
                colon = s.find(":", self.i)
                if colon < 0:
                    break
                key = s[self.i:colon].strip()
                self.i = colon
            if self.i < len(s) and s[self.i] == ":":
                self.i += 1
            obj[key], _ = self.read_value()
        self.i += 1  # }
        return obj

    def _read_array(self) -> list:
        s, arr = self.s, []
        self.i += 1  # [
        while self.i < len(s) and s[self.i] != "]":
            if s[self.i] == ",":
                self.i += 1
                continue
            item, _ = self.read_value()
            arr.append(item)
        self.i += 1  # ]
        return arr


def _scalar(token: str):
    if token == "true":
        return True
    if token == "false":
        return False
    if token in ("null", ""):
        return None
    for cast in (int, float):
        try:
            return cast(token)
        except ValueError:
            pass
    return token
