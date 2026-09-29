from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Union

from ryzenai.conversation.tool_call import ToolCall


@dataclass(frozen=True)
class Message:
    role: str                       # "user" | "system" | "assistant" | "tool"
    content: Union[str, list, None] # 純文字，或多模態內容串列（含 image_url 物件）；僅含 tool_calls 的 assistant 訊息可為 None
    timestamp: str                  # ISO8601，例如 "2026-05-09T12:00:00Z"
    tool_calls: Optional[tuple[ToolCall, ...]] = None  # assistant 發出的工具呼叫
    tool_call_id: Optional[str] = None                 # role="tool" 時，對應的 ToolCall.id
