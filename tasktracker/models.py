from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from .utils import to_iso, from_iso

@dataclass
class Task:
    # TODO (Level 1): define fields
    # id: str
    # title: str
    # description: str
    # status: str
    # priority: int
    # created_at: datetime
    # updated_at: datetime

    def to_dict(self) -> dict[str, Any]:
        """Return JSON-serializable dict (timestamps as ISO strings)."""
        raise NotImplementedError

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Task":
        """Create Task from dict returned by to_dict()."""
        raise NotImplementedError
