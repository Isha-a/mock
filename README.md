# Mock Interview Assessment – Task Tracker CRUD (Python)

This practice repo simulates the kind of **Python-only, test-driven CRUD assignment** you described.

You will implement code to make the provided unit tests pass. There is **no database**—everything is stored **in-memory**.

## Setup

```bash
python -m venv .venv
# mac/linux
source .venv/bin/activate
# windows
# .venv\Scripts\activate

pip install -e .[dev]
pytest -q
```

## Rules

- Use **only** the Python standard library.
- Do **not** edit tests.
- Implement level-by-level: **Level 1 → 2 → 3 → 4**
- Raise exceptions exactly as required:
  - `ValueError` for validation errors
  - `KeyError` for missing ids

---

## Domain

A **Task** has:

- `id: str` (UUID string)
- `title: str` (required, non-empty after strip)
- `description: str` (can be empty)
- `status: str` (one of: `"OPEN"`, `"IN_PROGRESS"`, `"DONE"`)
- `priority: int` (1–5, where 1 is highest)
- `created_at: datetime` (timezone-aware UTC)
- `updated_at: datetime` (timezone-aware UTC)

---

## Level 1 — Models

Implement `tasktracker/models.py`

- Create a `Task` `@dataclass` with the fields above.
- Implement:
  - `to_dict()` → JSON-serializable dict, timestamps must be ISO strings with timezone offset.
  - `@classmethod from_dict(data)` → create `Task` from dict produced by `to_dict()`.

Run:
```bash
pytest -q tests/test_level1_models.py
```

---

## Level 2 — CRUD Service (in-memory)

Implement `tasktracker/services.py`:

Create `TaskService` with an in-memory store.

Methods:

- `create_task(title: str, description: str, priority: int) -> Task`
  - status should default to `"OPEN"`
- `get_task(task_id: str) -> Task`
- `update_task(task_id: str, *, title=None, description=None, status=None, priority=None) -> Task`
  - **partial update**: only update provided fields
  - always bump `updated_at` if at least one field changes
- `delete_task(task_id: str) -> None`
- `list_tasks() -> list[Task]`
  - sorted by `created_at` ascending

Run:
```bash
pytest -q tests/test_level2_crud.py
```

---

## Level 3 — Validation

Add validation rules in `TaskService`:

- title: must be non-empty after `.strip()`
- priority: must be int 1..5
- status: must be one of `"OPEN"`, `"IN_PROGRESS"`, `"DONE"`

Validate:
- on create: validate title + priority (status is default)
- on update: validate only fields being updated

Raise `ValueError` with a helpful message.

Run:
```bash
pytest -q tests/test_level3_validation.py
```

---

## Level 4 — Filtering + History Log

Add:

### Filtering
Implement:
- `filter_tasks(*, status=None, min_priority=None) -> list[Task]`

Rules:
- If `status` provided: exact match
- If `min_priority` provided: include tasks with `priority >= min_priority`
- Combine filters with AND if both provided
- Return results sorted by created_at ascending (same as list_tasks)

### History Log
Keep a history list of dict events.
Append event on:
- CREATE (always)
- UPDATE (only if at least one field actually changes)
- DELETE (always)

Event shape:
```py
{"action": "CREATE"|"UPDATE"|"DELETE", "task_id": "<id>", "at": "<iso utc timestamp>"}
```

Expose:
- `@property def history(self) -> list[dict]`

Run:
```bash
pytest -q tests/test_level4_filtering.py
```

Good luck—treat tests as the spec.
