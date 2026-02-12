import pytest
from datetime import datetime, timezone

from tasktracker.services import TaskService

def test_create_get_list_sorted(monkeypatch):
    svc = TaskService()

    times = [
        datetime(2026, 2, 10, 9, 0, tzinfo=timezone.utc),
        datetime(2026, 2, 10, 10, 0, tzinfo=timezone.utc),
    ]
    it = iter(times)
    monkeypatch.setattr("tasktracker.services.utcnow", lambda: next(it))

    t1 = svc.create_task("A", "d1", 3)
    t2 = svc.create_task("B", "d2", 1)

    assert svc.get_task(t1.id).title == "A"
    assert svc.get_task(t2.id).priority == 1

    tasks = svc.list_tasks()
    assert [t.id for t in tasks] == [t1.id, t2.id]
    assert [t.created_at.hour for t in tasks] == [9, 10]

def test_update_and_delete(monkeypatch):
    svc = TaskService()

    monkeypatch.setattr("tasktracker.services.utcnow", lambda: datetime(2026, 2, 10, 9, 0, tzinfo=timezone.utc))
    t = svc.create_task("A", "d", 2)

    monkeypatch.setattr("tasktracker.services.utcnow", lambda: datetime(2026, 2, 10, 11, 0, tzinfo=timezone.utc))
    t2 = svc.update_task(t.id, title="A2")
    assert t2.title == "A2"
    assert t2.updated_at.hour == 11

    svc.delete_task(t.id)
    with pytest.raises(KeyError):
        svc.get_task(t.id)
