"""
Crash scenario: _build_model() registry doesn't raise on unknown model.
If it silently returns None or crashes with KeyError, the error message
is unhelpful and debugging is painful.
"""
import pytest
from api import _build_model as api_build_model
from cli import _build_model as cli_build_model


class TestRegistryUnknownModel:
    def test_api_build_model_unknown_raises_valueerror(self):
        """api._build_model must raise ValueError with available models listed."""
        with pytest.raises(ValueError, match="Unknown model"):
            api_build_model("nonexistent-model")

    def test_cli_build_model_unknown_raises_valueerror(self):
        """cli._build_model must raise ValueError with available models listed."""
        with pytest.raises(ValueError, match="Unknown model"):
            cli_build_model("nonexistent-model")

    def test_api_error_lists_available(self):
        """Error message must include available model names."""
        with pytest.raises(ValueError, match="gemma3-npu"):
            api_build_model("bad")

    def test_cli_error_lists_available(self):
        with pytest.raises(ValueError, match="gemma3-npu"):
            cli_build_model("bad")
