"""
Crash scenario: SingleSession produces no output or crashes on generator consumption.
If SingleSession.run() doesn't return a valid generator, cli.py's run_single()
and print("".join(tokens)) will crash.
"""
from tests.conftest import EchoText2Text
from ryzenai.session import SingleSession


class TestSingleSessionOutput:
    def test_run_returns_generator(self):
        """run() must return a generator that yields strings."""
        import types
        model = EchoText2Text()
        session = SingleSession(model)
        result = session.run("hello")
        assert isinstance(result, types.GeneratorType)

    def test_run_yields_correct_content(self):
        """run() output joined must equal the input (echo model)."""
        model = EchoText2Text()
        session = SingleSession(model)
        output = "".join(session.run("hello"))
        assert output == "hello"

    def test_run_stateless(self):
        """Each run() creates a fresh context — no cross-contamination."""
        model = EchoText2Text()
        session = SingleSession(model)
        out1 = "".join(session.run("first"))
        out2 = "".join(session.run("second"))
        assert out1 == "first"
        assert out2 == "second"

    def test_run_with_multimodal_content(self):
        """run() accepts list content for multimodal input."""
        model = EchoText2Text()
        session = SingleSession(model)
        content = [
            {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,abc"}},
            {"type": "text", "text": "describe"},
        ]
        # EchoText2Text returns "multimodal" for list content
        output = "".join(session.run(content))
        assert output == "multimodal"
