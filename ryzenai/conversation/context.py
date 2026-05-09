from dataclasses import dataclass, field

from ryzenai.conversation.message import Message


@dataclass
class ConversationContext:
    messages: list[Message] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
