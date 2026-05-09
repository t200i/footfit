from datetime import datetime, timezone


def _now() -> str:
    """回傳 ISO8601 格式的當前 UTC 時間戳記，供建立 Message 時使用。"""
    return datetime.now(timezone.utc).isoformat()
