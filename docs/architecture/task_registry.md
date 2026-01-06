# Task Registry Design

This document defines how tasks are registered, identified, and resolved for execution
by workers in eQueue.

The registry provides a stable mapping from **task name → callable**, decoupling job
producers from task implementations.

---

## Goals

- Allow users to define tasks via a simple, explicit API.
- Reference tasks by **string name**, not executable code.
- Enable workers to resolve and execute tasks deterministically.
- Keep the registry minimal and explicit in early phases.

---

## Non-Goals

- No dynamic module autodiscovery.
- No plugin system.
- No hot reloading of tasks.
- No distributed registry or DB-backed registry.

All tasks must be registered at process startup.

---

## Task Identification

Each task is identified by a **globally unique string name**.

Recommended naming convention:
```
<namespace>.<task_name>
````

Examples:
- `puzzles.extract_mate_tag`
- `emails.send_welcome`
- `http.fetch_url`

Task names are:
- explicit
- stable
- independent of Python module paths

---

## Registration Mechanism

Tasks are registered via a decorator-based API.

Conceptually:
- A global in-memory registry stores task metadata.
- Registration occurs at import time.
- Duplicate task names are not allowed.

Example (illustrative, not final API):

```python
@task(name="puzzles.extract_mate_tag")
def extract_mate_tag(puzzle_id: str) -> dict:
    ...
````

---

## Registry Contents

For each task, the registry stores:

* task name (string key)
* callable reference
* optional metadata (e.g. retry defaults, timeout hints)

The registry does **not**:

* store task arguments
* manage execution
* perform serialization

---

## Resolution & Execution Boundary

Workers interact with the registry as follows:

1. Read job record from database.
2. Extract `task_name` from job payload.
3. Look up callable in registry.
4. Invoke callable with deserialized arguments.

Task execution semantics (timeouts, retries, cancellation) are handled **outside**
the registry.

---

## Error Handling

* Unknown task name → non-retryable error → job marked `dead`.
* Duplicate registration → process startup error.
* Registry mutation after startup → not supported.

Failures at this layer are considered **configuration errors**, not runtime failures.

---

## Rationale

This design mirrors mature task queues (e.g. Celery) at the conceptual level while
remaining simple enough to reason about during early development.

By keeping the registry:

* in-memory
* explicit
* deterministic

eQueue avoids complexity that is unnecessary before multi-worker execution is implemented.

---

## Future Extensions (Out of Scope)

* Automatic task discovery
* Versioned task names
* Per-task concurrency limits
* Task-level retry/backoff configuration
