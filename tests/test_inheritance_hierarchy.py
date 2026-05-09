"""
Crash scenario: Type hierarchy broken — isinstance checks fail.
If Text2Text/ImageText2Text don't inherit from Model, or modules don't
inherit from the correct type, type-based routing in api.py will crash.
"""
from ryzenai.model import Model, Text2Text, ImageText2Text
from ryzenai.backend.base import Backend
from tests.conftest import EchoText2Text, EchoImageText2Text


class TestInheritanceHierarchy:
    def test_text2text_is_model(self):
        assert issubclass(Text2Text, Model)

    def test_imagetext2text_is_model(self):
        assert issubclass(ImageText2Text, Model)

    def test_echo_text2text_isinstance(self):
        model = EchoText2Text()
        assert isinstance(model, Text2Text)
        assert isinstance(model, Model)

    def test_echo_imagetext2text_isinstance(self):
        model = EchoImageText2Text()
        assert isinstance(model, ImageText2Text)
        assert isinstance(model, Model)

    def test_model_is_abc(self):
        """Model cannot be instantiated directly (abstract)."""
        import pytest
        with pytest.raises(TypeError):
            Model(backend=None)
