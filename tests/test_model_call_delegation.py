"""
Crash scenario: Model.__call__ doesn't delegate to generate().
If __call__ is broken, model(context) crashes and the entire api.py/cli.py
pipeline fails since they all use model(context) syntax.
"""
from tests.conftest import EchoText2Text, MockBackend
from ryzenai.conversation import Message, ConversationContext
from ryzenai.conversation._utils import _now


class TestModelCallDelegation:
    def test_call_delegates_to_generate(self):
        """model(context) must produce the same output as model.generate(context)."""
        model = EchoText2Text()
        ctx = ConversationContext(
            messages=[Message(role="user", content="hi", timestamp=_now())]
        )
        via_call = list(model(ctx))
        ctx2 = ConversationContext(
            messages=[Message(role="user", content="hi", timestamp=_now())]
        )
        via_generate = list(model.generate(ctx2))
        assert via_call == via_generate

    def test_call_returns_generator(self):
        """model(context) must return a Generator, not a string."""
        import types
        model = EchoText2Text()
        ctx = ConversationContext(
            messages=[Message(role="user", content="x", timestamp=_now())]
        )
        result = model(ctx)
        assert isinstance(result, types.GeneratorType)

    def test_model_holds_backend(self):
        """Model._backend must be set to the injected backend."""
        model = EchoText2Text()
        assert isinstance(model._backend, MockBackend)
