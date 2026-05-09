"""Shared test fixtures: mock backends and models for CI without hardware."""
from typing import Generator

from ryzenai.backend.base import Backend
from ryzenai.model import Model, Text2Text, ImageText2Text
from ryzenai.conversation import ConversationContext


class MockBackend(Backend):
    """A backend that always validates successfully (no hardware needed)."""

    name = "MockBackend"

    def __init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        pass


class EchoText2Text(Text2Text):
    """Echoes back the last user message content, token by token."""

    def __init__(self) -> None:
        super().__init__(MockBackend())

    def generate(self, context: ConversationContext) -> Generator[str, None, None]:
        last_msg = context.messages[-1]
        content = last_msg.content if isinstance(last_msg.content, str) else "multimodal"
        for char in content:
            yield char


class EchoImageText2Text(ImageText2Text):
    """Echoes back text parts from multimodal content."""

    def __init__(self) -> None:
        super().__init__(MockBackend())

    def generate(self, context: ConversationContext) -> Generator[str, None, None]:
        last_msg = context.messages[-1]
        if isinstance(last_msg.content, str):
            for char in last_msg.content:
                yield char
        else:
            text_parts = [
                p["text"] for p in last_msg.content if p.get("type") == "text"
            ]
            combined = " ".join(text_parts)
            for char in combined:
                yield char
