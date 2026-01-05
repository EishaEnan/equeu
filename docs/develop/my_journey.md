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
