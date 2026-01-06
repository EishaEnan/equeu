### Month 1 Summary (Dec 2025 - early Jan 2026)
- Learned: task-queue basics, Pydantic v2 modeling, decorators for cross-cutting concerns, HTTP clients (requests/JSON), FastAPI full-stack patterns with auth + Postgres.
- Confidence gained: designing validated payloads/settings, wrapping behaviors with decorators (logging/timing/auth), building secure CRUD APIs, integrating DB sessions with FastAPI.
- Next on eQueue: draft architecture + state diagram (enqueue → claim → execute → retry), write the 1–2 page design doc (schema + API contracts + worker lifecycle), pick DB job-claim pattern (`FOR UPDATE SKIP LOCKED` vs advisory locks), and outline test cases for retries/race conditions before coding.

## Wednesday, 3rd Dec 2025
- Resource: [Task Queues - System Design (GeeksForGeeks)](https://www.geeksforgeeks.org/system-design/task-queues-system-design/)
- Focus: push vs pull workers, ack/reserve semantics, failure handling patterns.
- Notes for eQueue: informs job state transitions and worker claim strategy.

## Monday, 22 Dec 2025
- Resource: [Pydantic V2 - Udemy](https://www.udemy.com/course/pydantic/)
- Focus: robust data modeling, advanced validation, and tighter type hinting to improve readability and correctness.
- Applied: prototyped job payload models/settings with richer validation, contrasted data classes vs Pydantic for eQueue inputs.

## Thursday, 26 Dec 2025
- Resource: [Python Decorators - Udemy](https://www.udemy.com/course/intermediate-python-master-decorators-from-scratch/) 
- Focus: writing decorators from scratch, chaining, handling `*args/**kwargs`, preserving metadata with `functools.wraps`.
- Applied: built logging, caching, timing, and auth decorators; plan to use timing/logging wrappers for worker steps and auth wrappers for admin endpoints.

## Tuesday, 23 Dec 2025
- Resources: [Python `Requests` - Udemy](https://www.udemy.com/course/learn-python-requests/) and [Python `JSON` - Udemy](https://www.udemy.com/course/master-json-using-python/)
- Focus: calling APIs, timeouts/retries, and safe JSON serialization for task args/results.
- Applied: planned patterns for integration tests and sample tasks that enqueue HTTP calls.

## Saturday, 03 Jan 2026
- Resource: [FastAPI - Udemy](https://www.udemy.com/course/fastapi-the-complete-course/)
- Focus: REST CRUD patterns, dependency injection, Pydantic models, auth (bcrypt + JWT), SQLAlchemy/PostgreSQL integration, pytest testing, and deployment steps.
- Applied: built a full-stack todo app (auth + CRUD on Postgres) to mirror eQueue needs: secure enqueue endpoints, dependency-managed DB sessions, JWT-protected admin operations, and confidence to add tests for queue APIs.

## Phase 1 Complete — Foundation & Architecture

**Status:** Completed

This phase focused on understanding task queues as distributed systems before writing any production code.

### Key outcomes
- Designed and documented an end-to-end architecture for a PostgreSQL-backed task queue (FastAPI → DB → workers → results).
- Finalized a minimal job state machine (`queued → running → succeeded | dead | cancelled`) with retries modeled via scheduling (`run_at`), not extra states.
- Mapped Celery and AWS SQS concepts (task registry, retries, visibility timeout, DLQ) to PostgreSQL primitives (row locks, leases, terminal states).
- Identified core failure modes (worker crashes, network issues, DB outages) and corresponding mitigations to test later.

### Major conceptual takeaways
- **Atomicity vs idempotency:** atomic transactions coordinate ownership; idempotent handlers tolerate retries and at-least-once execution.
- **Leasing over locking:** short claim transactions + time-based leases scale better than long-held locks.
- **Retries are control flow:** failed attempts are events, not states.
- **PostgreSQL as a coordinator:** with `FOR UPDATE SKIP LOCKED`, Postgres can safely replace a message broker for learning-scale systems.

### Artifacts produced
- Architecture diagram and flow description
- Job state machine specification
- Celery source takeaways
- SQS → PostgreSQL concept mapping
- Failure modes and mitigation checklist

Phase 2 will focus on implementing the database layer and worker claiming logic based on these decisions.


## Phase 2 Complete — Database Layer & Coordination

**Focus:** translating architectural decisions into concrete database structures and coordination logic.

### Objectives
- Finalize the jobs table schema and constraints based on the state machine.
- Document and validate a safe job-claiming strategy using PostgreSQL row-level locking.
- Define a simple, forward-only migration approach suitable for early development.
- Ensure indexes and access patterns align with worker and monitoring queries.

### Scope boundaries
- No worker execution code yet.
- No ORM or migration framework.
- No performance tuning beyond correctness-focused indexing.

## Phase 3 — Worker Logic (Conceptual Foundations)

**Status:** Completed

This phase focused on understanding execution semantics and constraints before
implementing workers.

### Key learnings
- Designed and prototyped a minimal task registry using explicit, namespaced task
  identifiers decoupled from Python module paths.
- Learned how asyncio enforces execution limits via cancellation rather than
  preemption (`asyncio.wait_for`, `task.cancel()`).
- Observed that `finally` blocks run reliably on both timeouts and cancellation,
  making them the correct place for cleanup and state reconciliation.
- Clarified error classification boundaries (timeout vs cancellation vs crash)
  to inform future retry logic.
- Chose JSON-only serialization for job payloads and results, prioritizing safety,
  debuggability, and alignment with PostgreSQL `jsonb`.

### Design implications for eQueue
- Workers must treat timeouts as cancellation events.
- Cleanup and job state updates must live in `finally` blocks.
- Jobs should reference domain data by identifier (e.g. `puzzle_id`), not embed
  large datasets in payloads.
- Task identity (behavior) must remain distinct from task inputs (data).

This phase established the execution and safety model required to implement
workers without premature complexity.
