# Celery Source Review — Key Takeaways

_Date:_ 2026-01-06  
_Scope:_ [Celery](https://github.com/celery/celery/tree/main) “Getting Started”, task definitions, retry behavior, and worker concepts.  
_Goal:_ Extract architectural patterns applicable to eQueue without copying implementation details.

---

## High-Level Observation

Celery’s codebase is organized around **clear separations of responsibility**:
- task definition vs task execution
- message transport vs task semantics
- retry as expected control flow, not failure
- monitoring as first-class behavior

Most of the complexity in Celery exists to support **multiple brokers and backends**. eQueue deliberately avoids this by using PostgreSQL as the single source of truth.

---

## Core Patterns Identified

### 1. Tasks Are Identified by Name, Not Code

In Celery:
- Tasks are registered under a **string name**
- Messages reference tasks by name
- Workers look up the callable in a **task registry**

**Takeaway for eQueue:**
- Jobs should reference a task by name (e.g. `puzzles.extract_mate_tag`)
- Workers execute tasks via a registry: `name → callable`
- Job payloads should never contain executable code

This enables:
- decoupling producers from workers
- versioning and refactoring tasks without changing enqueued jobs
- safer execution boundaries

---

### 2. Retry Is a First-Class, Expected Outcome

In Celery:
- Retry is not an error condition
- `retry()` is explicit and intentional
- Retry schedules future execution with delay/backoff
- Retries are part of normal task lifecycle

**Takeaway for eQueue:**
- A failed attempt is an *event*, not a state
- Retry should be represented by:
  - incremented `attempts`
  - future `run_at`
  - `status` returning to `queued`
- Exhausted retries transition the job to `dead`

This aligns with eQueue’s decision to **exclude a `failed` state**.

---

### 3. Worker Lifecycle Is Simple, Even If the System Is Not

Despite Celery’s size, the conceptual worker loop is:

1. Reserve work
2. Execute task
3. Record outcome
4. Emit signals / events

All additional complexity (prefetching, concurrency pools, heartbeats) builds on this core loop.

**Takeaway for eQueue:**
- Keep the worker lifecycle minimal and explicit
- Separate:
  - job claiming (transactional, short-lived)
  - job execution (outside the DB transaction)
- Treat job ownership via data (leases), not long-held locks

---

### 4. Acknowledgement and Execution Are Separate Concerns

In Celery:
- “Acknowledging” a task is distinct from executing it
- Depending on configuration, ack can happen:
  - before execution
  - after execution
- This choice affects failure semantics

**Takeaway for eQueue:**
- Claiming a job ≠ completing a job
- Completion must be explicit (`succeeded`, `dead`, `cancelled`)
- The database is the authoritative source of completion state

eQueue’s `status + locked_until` model mirrors this separation cleanly.

---

### 5. Monitoring Is Not an Afterthought

Celery emits:
- task-received
- task-started
- task-succeeded
- task-failed
- retry events

These power tools like Flower and `celery events`.

**Takeaway for eQueue:**
- Job state transitions should be observable
- Monitoring can be driven by:
  - database state changes
  - optional LISTEN/NOTIFY hooks
- Dashboards should reflect *lifecycle events*, not just final states

This validates eQueue’s plan to base monitoring on job status transitions.

---

## What eQueue Will Explicitly Borrow

- Task registry keyed by name
- Retry as a scheduled re-queue, not a failure state
- Explicit worker lifecycle
- Clear distinction between “claimed”, “running”, and “completed”

---

## What eQueue Will Intentionally Do Differently

- Single backend (PostgreSQL) instead of pluggable brokers/backends
- No message acknowledgements; durability comes from DB transactions
- Simpler failure model (no `failed` state)
- Monitoring driven by DB state, not event streams

---

## Concrete Impact on eQueue Design

1. Jobs reference tasks by name; payloads are pure data.
2. Retry logic updates `run_at` and returns jobs to `queued`.
3. Workers use short transactions for claiming only.
4. Terminal states (`succeeded`, `dead`, `cancelled`) are explicit and final.
5. Observability is designed into the lifecycle, not layered on later.

---

## Open Questions / Follow-Ups

- Should eQueue support task-level retry policies (per task defaults)?
- Should job execution emit structured events beyond DB updates?
- Is lease extension needed for long-running tasks?

These will be revisited after the worker execution engine is implemented.
