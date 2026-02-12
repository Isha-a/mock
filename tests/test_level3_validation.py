import pytest
from datetime import datetime, timezone

from tasktracker.services import TaskService

def test_validation_on_create(monkeypatch):
    svc = TaskService()
    monkeypatch.setattr("tasktracker.services.utcnow", lambda: datetime(2026, 2, 10, 9, 0, tzinfo=timezone.utc))

    with pytest.raises(ValueError):
        svc.create_task("   ", "d", 3)

    with pytest.raises(ValueError):
        svc.create_task("A", "d", 0)

    with pytest.raises(ValueError):
        svc.create_task("A", "d", 6)

def test_validation_on_update(monkeypatch):
    svc = TaskService()
    monkeypatch.setattr("tasktracker.services.utcnow", lambda: datetime(2026, 2, 10, 9, 0, tzinfo=timezone.utc))
    t = svc.create_task("A", "d", 3)

    with pytest.raises(ValueError):
        svc.update_task(t.id, status="BAD")

    with pytest.raises(ValueError):
        svc.update_task(t.id, priority=10)

    # update with no-op should not error
    t2 = svc.update_task(t.id, title="A")
    assert t2.title == "A"
