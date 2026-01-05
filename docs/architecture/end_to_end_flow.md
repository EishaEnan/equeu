# End-to-End Job Flow

This document describes the end-to-end flow of a job in **eQueue**, from submission via FastAPI,
through PostgreSQL-backed coordination, to execution by distributed workers and final result retrieval.

PostgreSQL is the single source of truth for job state, coordination, retries, and failure handling.

---

## Architecture Diagram

![End-to-End Job Flow](architecture_flow.svg)

---

## High-Level Flow

1. **Client / API Consumer** submits a job via FastAPI.
2. **FastAPI** inserts the job into PostgreSQL with `status = queued` and emits a `NOTIFY`.
3. **Workers** wake up via `LISTEN / NOTIFY` and also poll as a fallback.
4. A worker atomically claims a job using a short transaction  
   (`SELECT … FOR UPDATE SKIP LOCKED`) and marks it `running` with a lease.
5. The worker executes the job outside the transaction.
6. On completion:
   - Success → `status = succeeded`
   - Failure with retries left → reschedule (`status = queued`, future `run_at`)
   - Failure with no retries left → `status = dead`
7. **Clients** query job status/results via the API.

---

## Job Lifecycle States

- `queued` – eligible to be claimed
- `running` – leased to a worker
- `succeeded` – completed successfully (terminal)
- `dead` – failed permanently (terminal)
- `cancelled` – explicitly stopped (terminal)
Retry is implemented by rescheduling failed jobs back to `queued` with a future `run_at`.

---

## Worker Discovery Strategy

Workers use a **hybrid discovery model**:
- **Primary**: PostgreSQL `LISTEN / NOTIFY` for low-latency wakeups
- **Fallback**: periodic polling to guarantee jobs are never missed

This avoids relying on notifications alone, which are best-effort.

---

## Failure & Retry Semantics

- If a job fails and `attempts < max_attempts`:
  - The job is rescheduled with backoff.
- If `attempts >= max_attempts` (or the failure is non-retryable):
  - The job is marked `dead` and will not be retried.

---

## Known Bottlenecks & Trade-offs

- **Claim contention**: many workers competing on the same queue stress the claim query.
- **Long-running jobs**: require careful lease duration tuning.
- **Large payloads**: JSONB payloads increase storage and query cost.
- **Dashboard queries**: require proper indexing to avoid full table scans.
