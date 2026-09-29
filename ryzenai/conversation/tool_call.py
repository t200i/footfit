import uuid
from dataclasses import dataclass, field


@dataclass(frozen=True)
class ToolCall:
    """模型發出的一次工具呼叫（對應 OpenAI 的 tool_calls[] 項目）。"""
    name: str
    arguments: dict
    id: str = field(default_factory=lambda: f"call_{uuid.uuid4().hex[:12]}")
