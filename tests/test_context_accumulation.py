"""
Crash scenario: ConversationContext fails to accumulate messages.
If messages list is shared across instances (mutable default) or append
fails, the entire session pipeline breaks.
"""
from ryzenai.conversation import Message, ConversationContext
from ryzenai.conversation._utils import _now


class TestConversationContext:
    def test_default_factory_isolation(self):
        """Two contexts must NOT share the same messages list (mutable default trap)."""
        ctx1 = ConversationContext()
        ctx2 = ConversationContext()
        ctx1.messages.append(Message(role="user", content="a", timestamp=_now()))
        assert len(ctx2.messages) == 0, "Mutable default leaked across instances"

    def test_append_message(self):
        """Messages can be appended to context."""
        ctx = ConversationContext()
        ctx.messages.append(Message(role="user", content="hello", timestamp=_now()))
        assert len(ctx.messages) == 1
        assert ctx.messages[0].role == "user"

    def test_metadata_isolation(self):
        """Two contexts must NOT share metadata dict."""
        ctx1 = ConversationContext()
        ctx2 = ConversationContext()
        ctx1.metadata["key"] = "value"
        assert "key" not in ctx2.metadata
