import uuid
from datetime import datetime, timezone

from tasktracker.models import Task

def test_task_roundtrip_to_from_dict():
    now = datetime(2026, 2, 10, 10, 0, 0, tzinfo=timezone.utc)
    tid = str(uuid.uuid4())

    t = Task(
        id=tid,
        title="Write tests",
        description="Add unit tests for service",
        status="OPEN",
        priority=2,
        created_at=now,
        updated_at=now,
    )

    d = t.to_dict()
    assert d["id"] == tid
    assert d["created_at"].endswith("+00:00")
    assert d["updated_at"].endswith("+00:00")

    t2 = Task.from_dict(d)
    assert t2 == t
