from __future__ import annotations
from datetime import datetime, timezone

def utcnow() -> datetime:
    """Return timezone-aware UTC datetime. Extracted for easy monkeypatching in tests."""
    return datetime.now(timezone.utc)

def to_iso(dt: datetime) -> str:
    """Convert datetime to ISO string in UTC."""
    if dt.tzinfo is None:
        raise ValueError("datetime must be timezone-aware")
    return dt.astimezone(timezone.utc).isoformat()

def from_iso(s: str) -> datetime:
    """Parse ISO string into timezone-aware datetime."""
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        raise ValueError("timestamp must include timezone offset")
    return dt.astimezone(timezone.utc)
