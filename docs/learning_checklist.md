# eQueue Learning Checklist
Practical learning to unlock each phase of the eQueue roadmap. Check items off as you gain confidence and capture notes/diagrams in your docs.

## Phase 1 — Foundation & Architecture
- [✅] Sketch end-to-end flow (FastAPI → PostgreSQL → workers → results) with bottlenecks and worker discovery strategy.
- [✅] Review Celery’s core patterns (broker, task registry, retries, monitoring) from source for 1–2 hours; log takeaways.
- [✅] Read AWS SQS concepts (visibility timeout, dead-letter queues, delays) and map parallels to PostgreSQL.
- [✅] List failure modes (network, worker crash, DB outage) and mitigation options to test later.

## Phase 2 — Database Layer
- [ ] Define job state diagram and required columns (payload, attempts, backoff, error logs, timestamps).
- [ ] Research safe job-claiming patterns in PostgreSQL (`SELECT ... FOR UPDATE SKIP LOCKED`, advisory locks).
- [ ] Decide on migration approach (ordered SQL files + tracking table) and indexes for status/time-based queries.

## Phase 3 — Worker Logic
- [ ] Study task registry patterns (decorators, import discovery) and note a minimal registry API you want.
- [ ] Deepen asyncio knowledge on timeouts/cancellation (`asyncio.wait_for`, shielded tasks) and error capture.
- [ ] Compare argument serialization options (JSON vs pickle vs msgpack) and choose constraints for safety.

## Phase 4 — FastAPI Integration
- [ ] Draft API contract for enqueue/status/list/cancel with auth and rate-limiting strategy.
- [ ] Review pagination and filtering patterns in FastAPI/Pydantic for job lists.
- [ ] Outline a `QueueClient` interface and how it talks to the DB/worker layer.

## Phase 5 — Monitoring & Real-Time
- [ ] Learn PostgreSQL LISTEN/NOTIFY usage from async clients and how to debounce noisy events.
- [ ] Plan WebSocket reconnection/backoff behavior for the dashboard.
- [ ] Define the minimal dashboard views and metrics (active jobs, recent failures, throughput).

## Phase 6 — DevOps & Deployment
- [ ] Review multi-stage Dockerfiles for FastAPI/async workers and image size trimming.
- [ ] Map a Docker Compose setup for app + worker + Postgres for local dev.
- [ ] Outline AWS path: build/push to ECR, run on ECS/EC2, RDS for Postgres, CloudWatch logs.

## Phase 7 — Testing & Reliability
- [ ] Set up pytest + pytest-asyncio patterns for concurrent worker tests.
- [ ] Plan failure simulations (DB down, worker crash mid-task, timeout) and expected recovery behavior.
- [ ] Choose a load-testing approach (Locust/k6/custom asyncio scripts) for >100 jobs/sec goals.

## Phase 8 — Documentation & Portfolio
- [ ] Draft README skeleton (what/why/how to run).
- [ ] Outline full docs: architecture, API reference, deployment, benchmarks, trade-offs.
- [ ] Plan storytelling assets (blog post points, demo video checklist, sample apps).
