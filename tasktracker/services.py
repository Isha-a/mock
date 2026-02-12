from __future__ import annotations
import uuid
from typing import Optional

from .models import Task
from .utils import utcnow, to_iso

class TaskService:
    """In-memory service managing Task CRUD, filtering, and history log."""

    def __init__(self) -> None:
        # TODO: initialize
        # - self._store: dict[str, Task]
        # - self._history: list[dict]
        raise NotImplementedError

    # ---------- CRUD ----------
    def create_task(self, title: str, description: str, priority: int) -> Task:
        """Create a task with status OPEN. Validate input."""
        raise NotImplementedError

    def get_task(self, task_id: str) -> Task:
        """Return task by id; raise KeyError if missing."""
        raise NotImplementedError

    def update_task(
        self,
        task_id: str,
        *,
        title: Optional[str] = None,
        description: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[int] = None,
    ) -> Task:
        """Partial update. Only validate fields being updated."""
        raise NotImplementedError

    def delete_task(self, task_id: str) -> None:
        """Delete task; raise KeyError if missing."""
        raise NotImplementedError

    def list_tasks(self) -> list[Task]:
        """List tasks sorted by created_at ascending."""
        raise NotImplementedError

    # ---------- Level 4 ----------
    def filter_tasks(
        self,
        *,
        status: Optional[str] = None,
        min_priority: Optional[int] = None,
    ) -> list[Task]:
        """Filter tasks by status and/or min_priority (priority >= min_priority)."""
        raise NotImplementedError

    @property
    def history(self) -> list[dict]:
        """History events (CREATE/UPDATE/DELETE)."""
        raise NotImplementedError

    # ---------- Helpers ----------
    def _validate_title(self, title: str) -> None:
        raise NotImplementedError

    def _validate_priority(self, priority: int) -> None:
        raise NotImplementedError

    def _validate_status(self, status: str) -> None:
        raise NotImplementedError

    def _log(self, action: str, task_id: str) -> None:
        raise NotImplementedError
