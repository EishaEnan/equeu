
# eQueue — Distributed Task Queue for FastAPI
## Project Plan & Learning Roadmap

---

## Overview

eQueue is a learning-focused project that explores the design and implementation of a
PostgreSQL-backed distributed task queue integrated with FastAPI. The goal is to build
a production-inspired system from first principles, emphasizing correctness, reliability,
and clear architectural reasoning.

The project is intentionally scoped to prioritize deep understanding over speed, with
design decisions documented and validated incrementally.

---

## Phase 1: Foundation & Architecture (Weeks 1–2)

### 1.1 System Design & Architecture

**Project scope:**
- A distributed task queue that accepts jobs from FastAPI endpoints
- Jobs are persisted in PostgreSQL and executed asynchronously by workers
- Workers handle retries, failures, and job leasing
- Job status and results are queryable by clients

**Learning objectives:**
- Understand distributed coordination and concurrency
- Reason about failure modes in async systems
- Design a clear job lifecycle and state machine

**Deliverables:**
1. End-to-end architecture diagram:
   - Job flow from FastAPI → PostgreSQL → workers → results
   - Identification of bottlenecks
   - Worker discovery strategy

2. Research and comparative analysis:
   - Celery architecture and task execution model
   - AWS SQS concepts (visibility timeout, at-least-once delivery)
   - Common failure modes (worker crashes, network partitions, DB contention)

3. Design documentation (1–2 pages):
   - Database schema and core tables
   - API contracts exposed by the queue
   - Worker lifecycle (startup, job claiming, execution, reporting)

**AI usage guidelines:**
- Appropriate for clarifying concepts and validating designs
- Useful for trade-off analysis and failure mode exploration
- Not used for generating full designs or implementations

---

### 1.2 Project Setup & Dependencies

**Repository structure:**
```text
equeue/
├── src/
│   ├── equeue/
│   │   ├── core/
│   │   ├── worker/
│   │   ├── api/
│   │   └── models/
│   ├── tests/
│   └── examples/
├── db/
│   └── migrations/
├── docker/
├── docs/
├── pyproject.toml
└── README.md
````

**Development environment:**

* Python async stack (FastAPI, asyncio)
* PostgreSQL (local or Docker)
* pytest + pytest-asyncio
* Code quality tooling (ruff, black, mypy)

**Initial dependencies:**

* FastAPI, uvicorn
* asyncpg
* pydantic
* pytest, pytest-asyncio

---

## Phase 2: Database Layer (Weeks 1–2, parallel with Phase 1)

### 2.1 PostgreSQL Schema Design

**Design questions:**

* What metadata must a job track to support retries and leasing?
* What states exist in the job lifecycle?
* How are race conditions prevented when multiple workers claim jobs?

**Deliverables:**

* Raw SQL migrations defining the jobs table
* Indexes supporting efficient job claiming and querying
* Clear state transition rules documented separately

---

## AI Usage Principles

AI is used as a **design review and clarification tool**, not as a replacement for
architectural reasoning.

**Appropriate uses:**

* Concept clarification
* Trade-off discussion
* Debugging support after independent investigation

**Avoided uses:**

* Generating full implementations
* Making core design decisions
* Copying existing systems wholesale

---

## Success Criteria

* Architecture can be explained end-to-end without reference material
* Job claiming is race-safe and resilient to worker crashes
* Retry and failure semantics are explicit and testable
* All major design decisions are documented and justified

---

## Notes

This document is a living plan. As implementation progresses, assumptions may be revised,
but changes should be documented with rationale.

