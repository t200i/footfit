from __future__ import annotations

from dataclasses import dataclass
from typing import Union


@dataclass(frozen=True)
class Message:
    role: str                       # "user" | "system" | "assistant"
    content: Union[str, list]       # 純文字，或多模態內容串列（含 image_url 物件）
    timestamp: str                  # ISO8601，例如 "2026-05-09T12:00:00Z"
