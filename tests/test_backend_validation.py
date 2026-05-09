"""
Crash scenario: Backend ABC contract — instantiating Backend directly must fail.
This is a pure framework test; no hardware or SDK is required.
"""
import pytest
from ryzenai.backend.base import Backend


class TestBackendValidationContract:
    def test_backend_is_abstract(self):
        """Backend cannot be instantiated directly."""
        with pytest.raises(TypeError):
            Backend()
