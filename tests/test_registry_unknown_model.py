"""
Crash scenario: build_model() registry doesn't raise on unknown model.
If it silently returns None or crashes with KeyError, the error message
is unhelpful and debugging is painful.
"""
import pytest
from ryzenai.registry import build_model


class TestRegistryUnknownModel:
    def test_build_model_unknown_raises_valueerror(self):
        """build_model must raise ValueError with available models listed."""
        with pytest.raises(ValueError, match="Unknown model"):
            build_model("nonexistent-model")

    def test_error_lists_available(self):
        """Error message must include available model names."""
        with pytest.raises(ValueError, match="gemma3-4b-npu"):
            build_model("bad")
