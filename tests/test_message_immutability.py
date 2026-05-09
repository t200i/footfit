"""
Crash scenario: Message frozen dataclass violated.
If Message is not truly immutable, downstream code that relies on hashability
or assumes no mutation after creation will break silently.
"""
import pytest
from ryzenai.conversation import Message


class TestMessageImmutability:
    def test_message_is_frozen(self):
        """Message fields cannot be mutated after creation → crash if mutable."""
        msg = Message(role="user", content="hello", timestamp="2026-01-01T00:00:00+00:00")
        with pytest.raises(AttributeError):
            msg.role = "assistant"

    def test_message_content_str(self):
        """Plain text content round-trips correctly."""
        msg = Message(role="user", content="test", timestamp="2026-01-01T00:00:00+00:00")
        assert msg.content == "test"
        assert isinstance(msg.content, str)

    def test_message_content_list(self):
        """Multimodal content (list) round-trips correctly."""
        parts = [
            {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,abc"}},
            {"type": "text", "text": "describe"},
        ]
        msg = Message(role="user", content=parts, timestamp="2026-01-01T00:00:00+00:00")
        assert isinstance(msg.content, list)
        assert len(msg.content) == 2
