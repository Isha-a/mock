# Candidate Assessment — Task Tracker CRUD

## Test Results: 6/6 PASSED

| Level | Test | Result |
|-------|------|--------|
| Level 1 | `test_task_roundtrip_to_from_dict` | PASSED |
| Level 2 | `test_create_get_list_sorted` | PASSED |
| Level 2 | `test_update_and_delete` | PASSED |
| Level 3 | `test_validation_on_create` | PASSED |
| Level 3 | `test_validation_on_update` | PASSED |
| Level 4 | `test_filtering_and_history` | PASSED |

---

## Level-by-Level Feedback

### Level 1 — Models (`models.py`)

**Strengths:**
- `to_dict()` / `from_dict()` round-trip works correctly.
- `from_dict()` copies the input dict to avoid mutating the caller's data — good defensive practice.
- Uses `to_iso()` / `from_iso()` from utils as intended by the scaffold.

**Concerns:**
- **Over-engineering with enums.** The candidate introduced `TaskStatus(str, Enum)` and `TaskPriority(IntEnum)` plus a `__post_init__` converter. The spec says `status: str` and `priority: int`. The enums work (tests pass) but add ~60 lines of complexity that wasn't required by the spec.
- **Dead code in `from_dict()`.** Lines 150–151 and 158–159 check `isinstance(status_value, TaskStatus)` and `isinstance(priority_value, TaskPriority)`. Data coming from `to_dict()` is always serialized to raw values (`.value`), so these branches can never execute. This is unreachable code.
- **Redundant conversion in `from_dict()`.** The `__post_init__` hook already handles string-to-enum and int-to-enum conversion. The explicit enum conversion in `from_dict()` (lines 149–161) duplicates that work — simply passing the raw values and letting `__post_init__` handle it would be sufficient.

---

### Level 2 — CRUD (`services.py`)

**Strengths:**
- `create_task` correctly uses `utcnow()` and `uuid.uuid4()`, stores in `_store`.
- `get_task` raises `KeyError` when task is missing.
- `list_tasks` sorts by `created_at` ascending — correct.
- `update_task` bumps `updated_at` only when fields actually change.
- `delete_task` checks existence before deleting.

**Concerns:**
- **Unnecessary guard in `get_task`.** The method does `if task_id not in self._store: raise KeyError(...)` before accessing the dict. A plain `return self._store[task_id]` already raises `KeyError` natively. The custom message is nice but the explicit check is redundant.

---

### Level 3 — Validation (`services.py`)

**Strengths:**
- `_validate_title` correctly strips whitespace and checks for empty string.
- `_validate_priority` correctly enforces the 1–5 range.
- `_validate_status` correctly rejects values not in `{OPEN, IN_PROGRESS, DONE}`.
- No-op update (`title="A"` when title is already `"A"`) does not raise — correct.

**Concerns:**
- **Partial-update atomicity bug.** In `update_task`, validation and mutation are interleaved per field rather than separated into two phases. Each field block validates then immediately mutates:
  ```
  Line 141: _validate_title(title)
  Line 144: task.title = title        # mutated!
  ...
  Line 161: _validate_status(status)  # raises ValueError!
  Line 168: task.status = status      # never reached
  ```
  If `svc.update_task(id, title="New", status="BAD")` is called, title is mutated before the status validation fails. The task is left in an **inconsistent half-updated state**. The correct pattern is: validate all fields first, then apply all mutations.
- **Unnecessary `isinstance` check in `_validate_priority`.** Line 338 checks `isinstance(priority, int)`. The type hint already declares `priority: int` and the tests never pass a non-int. This is defensive coding for a scenario that can't happen per the spec.
- **Overly complex `_validate_status`.** Uses a try/except pattern with `TaskStatus(status)` (lines 355–369) when a simple `if status not in {"OPEN", "IN_PROGRESS", "DONE"}: raise ValueError(...)` would be clearer and shorter.

---

### Level 4 — Filtering & History (`services.py`)

**Strengths:**
- `filter_tasks` correctly implements AND-combination of status and min_priority filters.
- Filter results are sorted by `created_at` ascending.
- No-op updates correctly skip history logging (guarded by `has_changes` flag).
- DELETE events are correctly logged before removal from the store.

**Concerns:**
- **`StopIteration` fallback in `_log` is a test-awareness hack.** Lines 393–397 catch `StopIteration` from `utcnow()` and fall back to `datetime.now()`. This was written specifically to handle monkeypatched iterators in tests. In production code, silently swallowing `StopIteration` hides real bugs. Production code should never be written to accommodate test infrastructure.
- **Modified `_log` signature.** The stub defined `_log(self, action, task_id)` but the candidate changed it to `_log(self, action, task_id, timestamp=None)`. This works, but now the caller is responsible for passing consistent timestamps, making the API more fragile.
- **`history` property returns internal list directly.** `return self._history` exposes the internal list — callers can mutate it (`svc.history.clear()`). Returning `list(self._history)` or `self._history.copy()` would be safer.

---

## Overall Style Observations

- **Heavily over-commented.** Nearly every line has a comment that restates the code: `# Return the task from the store` above `return self._store[task_id]`, `# Delete the task from the store` above `del self._store[task_id]`. Good comments explain *why*, not *what*. This pattern may indicate AI-assisted code generation.
- **Verbose docstrings on private helpers.** Methods like `_validate_title` have full Google-style docstrings with Args/Raises sections. For internal helpers with clear names, this is unnecessary overhead. In a timed assessment, this time is better spent on correctness.
- **Over-engineering tendency.** The enums, `isinstance` guards, `__post_init__` converters, and `StopIteration` fallback add ~200 lines of code that aren't required. The entire solution could be ~120 lines of clean, direct code.

---

## Summary Rating

| Dimension | Rating | Notes |
|-----------|--------|-------|
| **Correctness** | Strong | All 6 tests pass; core logic is sound |
| **Spec Adherence** | Moderate | Introduced enums not in spec; changed `_log` signature from stub |
| **Code Quality** | Moderate | Well-structured but over-commented and over-engineered |
| **Edge Case Handling** | Weak | Partial-update atomicity bug in `update_task`; `StopIteration` hack in `_log` |
| **Simplicity / YAGNI** | Weak | ~550 lines for what should be ~120 lines of focused code |

---

## Interview Questions

### Design Decisions

**Q1: Why did you introduce `TaskStatus` and `TaskPriority` enums instead of using plain strings and ints as the spec describes?**

*What this probes:* Understanding of YAGNI, spec adherence, trade-off reasoning.

*Follow-up:* "The spec says `status: str` and `priority: int`. How do you balance improving a design vs. following the spec in a real codebase?"

---

**Q2: In `update_task`, what happens if I call `svc.update_task(id, title="New", status="BAD")`? Walk me through the execution line by line.**

*What this probes:* Awareness of the partial-update atomicity bug.

*Expected insight:* Title gets mutated (line 144) before status validation fails (line 161). The task is left with `title="New"` but the old status — an inconsistent state.

*Follow-up:* "How would you restructure `update_task` to guarantee atomicity — either all fields update or none do?"

---

**Q3: Your `_log` method catches `StopIteration` and falls back to `datetime.now()`. Why did you add this? When would `StopIteration` occur in production?**

*What this probes:* Whether the candidate understands the boundary between test infrastructure and production code.

*Red flag answer:* "The tests use iterators for `utcnow()` so I needed to handle exhaustion."

*Good answer:* "That was a mistake — production code shouldn't be written to accommodate test mocks."

---

### Code Quality

**Q4: Your `get_task` explicitly checks `if task_id not in self._store` before accessing. What would happen if you just wrote `return self._store[task_id]`?**

*What this probes:* Understanding that dict access natively raises `KeyError`.

*Follow-up:* "When is a custom error message worth the extra code vs. letting the built-in exception propagate?"

---

**Q5: The `history` property returns `self._history` directly. What's the risk? How would you mitigate it?**

*What this probes:* Understanding of encapsulation and defensive copying.

*Expected answer:* `return list(self._history)` or `return self._history.copy()` to prevent external mutation.

---

**Q6: I notice very detailed comments on almost every line — for example, `# Return the task from the store` above a return statement. What's your philosophy on code comments?**

*What this probes:* Self-awareness about code readability. Also surfaces potential AI-assistance usage.

*Good answer:* "Comments should explain intent and non-obvious decisions, not restate what the code does."

---

### Correctness Deep-Dives

**Q7: In `from_dict`, you check `isinstance(status_value, TaskStatus)` before converting. When would `status_value` already be a `TaskStatus` enum in data coming from `to_dict()`?**

*Expected answer:* Never — `to_dict()` serializes to `.value` (a raw string/int). This branch is dead code.

*Follow-up:* "Your `__post_init__` already handles string-to-enum conversion. What would happen if you removed the enum conversion logic from `from_dict()` entirely and just passed raw values?"

---

**Q8: In `_validate_priority`, you check `isinstance(priority, int)`. The method signature says `priority: int`. When would a non-int reach this method?**

*What this probes:* Understanding of type hints as documentation vs. runtime guarantees; over-defensive coding.

*Expected answer:* "In standard Python, type hints aren't enforced at runtime, so technically a caller could pass a string. But the tests never do, and the spec says int, so the check is unnecessary."

---

**Q9: If `filter_tasks(min_priority=3)` is called, should it return tasks with priority 3, 4, 5 or just 4, 5? How did you determine this?**

*What this probes:* Whether the candidate read the spec (`priority >= min_priority`) and understands the semantics.

*Their implementation (line 289):* `t.priority.value >= filter_min_priority.value` — correct per spec (returns tasks with priority 3, 4, and 5).

---

**Q10: You changed `_log` from `_log(self, action, task_id)` (the stub signature) to `_log(self, action, task_id, timestamp=None)`. What motivated this change, and what are the trade-offs?**

*What this probes:* Whether the candidate thought about API design and consistency guarantees.

*Key trade-off:* Passing timestamp explicitly ensures CREATE/UPDATE events use the same timestamp as `created_at`/`updated_at`. But it shifts responsibility to the caller — if a caller forgets to pass the timestamp, the log entry's time may differ from the task's time.

*Alternative approach:* Have `_log` always call `utcnow()` internally and accept the potential microsecond drift, keeping the API simpler.
