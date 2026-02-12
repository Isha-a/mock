from datetime import datetime, timezone

from tasktracker.services import TaskService

def test_filtering_and_history(monkeypatch):
    svc = TaskService()

    times = [
        datetime(2026, 2, 10, 9, 0, tzinfo=timezone.utc),
        datetime(2026, 2, 10, 10, 0, tzinfo=timezone.utc),
        datetime(2026, 2, 10, 11, 0, tzinfo=timezone.utc),
        datetime(2026, 2, 10, 12, 0, tzinfo=timezone.utc),
    ]
    it = iter(times)
    monkeypatch.setattr("tasktracker.services.utcnow", lambda: next(it))

    t1 = svc.create_task("A", "d", 1)   # priority 1
    t2 = svc.create_task("B", "d", 3)   # priority 3
    t3 = svc.create_task("C", "d", 5)   # priority 5

    # filter by status
    open_tasks = svc.filter_tasks(status="OPEN")
    assert [t.id for t in open_tasks] == [t1.id, t2.id, t3.id]

    # update status
    svc.update_task(t1.id, status="IN_PROGRESS")

    open_tasks = svc.filter_tasks(status="OPEN")
    assert [t.id for t in open_tasks] == [t2.id, t3.id]

    # filter by min_priority (>=)
    p3 = svc.filter_tasks(min_priority=3)
    assert [t.id for t in p3] == [t2.id, t3.id]

    # AND combine
    both = svc.filter_tasks(status="OPEN", min_priority=5)
    assert [t.id for t in both] == [t3.id]

    # history: 3 creates + 1 update
    assert [e["action"] for e in svc.history] == ["CREATE", "CREATE", "CREATE", "UPDATE"]
    assert svc.history[0]["at"].endswith("+00:00")

    # no-op update should NOT add UPDATE
    svc.update_task(t1.id, status="IN_PROGRESS")
    assert [e["action"] for e in svc.history] == ["CREATE", "CREATE", "CREATE", "UPDATE"]

    # delete adds DELETE
    svc.delete_task(t2.id)
    assert svc.history[-1]["action"] == "DELETE"
