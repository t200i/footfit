"""
Crash scenario: InteractiveSession doesn't accumulate conversation history.
If assistant messages aren't appended after generation, multi-turn
conversations will lose context and the model will behave as stateless.
"""
from tests.conftest import EchoText2Text
from ryzenai.session import InteractiveSession


class TestInteractiveSessionHistory:
    def test_send_returns_generator(self):
        import types
        model = EchoText2Text()
        session = InteractiveSession(model)
        result = session.send("hi")
        assert isinstance(result, types.GeneratorType)

    def test_send_yields_correct_content(self):
        model = EchoText2Text()
        session = InteractiveSession(model)
        output = "".join(session.send("hello"))
        assert output == "hello"

    def test_history_accumulates_user_messages(self):
        """After send(), user message must be in context."""
        model = EchoText2Text()
        session = InteractiveSession(model)
        list(session.send("turn1"))  # consume generator
        assert len(session._context.messages) >= 1
        assert session._context.messages[0].role == "user"
        assert session._context.messages[0].content == "turn1"

    def test_history_accumulates_assistant_messages(self):
        """After send() is fully consumed, assistant message must be appended."""
        model = EchoText2Text()
        session = InteractiveSession(model)
        list(session.send("turn1"))  # must fully consume
        assert len(session._context.messages) == 2
        assert session._context.messages[1].role == "assistant"
        assert session._context.messages[1].content == "turn1"

    def test_multi_turn_history(self):
        """Multiple turns accumulate correctly."""
        model = EchoText2Text()
        session = InteractiveSession(model)
        list(session.send("a"))
        list(session.send("b"))
        assert len(session._context.messages) == 4
        roles = [m.role for m in session._context.messages]
        assert roles == ["user", "assistant", "user", "assistant"]

    def test_partial_consumption_still_appends(self):
        """Even if generator is partially consumed, assistant message
        must reflect what was yielded so far when generator is collected."""
        model = EchoText2Text()
        session = InteractiveSession(model)
        gen = session.send("abc")
        # Consume all tokens
        tokens = list(gen)
        assert "".join(tokens) == "abc"
        assert session._context.messages[-1].content == "abc"
