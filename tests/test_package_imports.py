"""
Crash scenario: Package imports fail due to missing __init__.py or circular imports.
If any subpackage import breaks, the entire application crashes on startup.
"""


class TestPackageImports:
    def test_import_backend(self):
        from ryzenai.backend import Backend, ONNXVitisAIBackend, ONNXDirectMLBackend, PyTorchROCmBackend
        assert Backend is not None

    def test_import_model(self):
        from ryzenai.model import Model, Text2Text, ImageText2Text
        assert Model is not None

    def test_import_conversation(self):
        from ryzenai.conversation import Message, ConversationContext
        assert Message is not None

    def test_import_session(self):
        from ryzenai.session import SingleSession, InteractiveSession
        assert SingleSession is not None

    def test_import_utils(self):
        from ryzenai.conversation._utils import _now
        assert callable(_now)

    def test_import_api_symbols(self):
        from api import build, _build_response, _sse_stream
        from api import ChatCompletionRequest, _ContentPart, _RequestMessage
        assert callable(build)

    def test_import_cli_symbols(self):
        from cli import run_single, run_interactive, _print_stream, _load_image
        assert callable(run_single)
