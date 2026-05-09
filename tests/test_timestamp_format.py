"""
Crash scenario: _now() returns invalid timestamp format.
All Message objects depend on _now() for timestamp. If it returns
non-ISO8601 or crashes, every Message creation fails.
"""
from datetime import datetime, timezone
from ryzenai.conversation._utils import _now


class TestTimestampFormat:
    def test_now_returns_string(self):
        result = _now()
        assert isinstance(result, str)

    def test_now_is_valid_iso8601(self):
        """Must be parseable back to a datetime."""
        result = _now()
        parsed = datetime.fromisoformat(result)
        assert parsed.tzinfo is not None, "Timestamp must include timezone"

    def test_now_is_utc(self):
        result = _now()
        parsed = datetime.fromisoformat(result)
        assert parsed.tzinfo == timezone.utc
