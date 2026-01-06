# Job Claiming Strategy

This document defines how workers safely claim jobs from PostgreSQL without race conditions.

The design prioritizes correctness, simplicity, and scalability over exactly-once execution.

---

## Eligibility Criteria

A job is **claimable** if:
- `status = 'queued'`
- `run_at <= now()`

Only eligible jobs are considered by workers.

---

## Claim Algorithm (High-Level)

1. Worker opens a **short-lived transaction**.
2. Selects a single eligible job:
   - filtered by `status` and `run_at`
   - ordered by priority and creation time
   - locked using `FOR UPDATE SKIP LOCKED`
3. Updates the job:
   - `status = 'running'`
   - sets `locked_by`
   - sets `locked_until = now() + lease_duration`
   - increments `attempts`
4. Transaction commits immediately.
5. Job execution happens **outside** the transaction.

This ensures atomic ownership transfer while keeping transactions minimal.

---

## Concurrency Guarantees

- Row-level locks prevent multiple workers from claiming the same job.
- `SKIP LOCKED` ensures workers do not block each other.
- Multiple workers can claim different jobs concurrently.

---

## Failure Handling

- **Worker crashes after claim:**  
  Lease expires (`locked_until`), job becomes reclaimable.
- **Duplicate execution:**  
  Possible under at-least-once delivery; task handlers must be idempotent.
- **Long-running jobs:**  
  Lease duration must exceed expected execution time (or be extended later).

---

## Explicit Non-Goals

- No exactly-once execution guarantees.
- No advisory locks (row-level locking is sufficient and simpler).
- No long-running transactions.
- No job execution inside database transactions.

---

## Index Requirements

- Partial index on runnable jobs:
  - supports `status = 'queued' AND run_at <= now()`
- Index on `(queue, locked_until)`:
  - supports reclaiming expired leases
- Indexes on `status` and timestamps:
  - support monitoring and dashboard queries

Indexes are designed to match the claim scan and operational queries.

---

## Summary

Job claiming relies on:
- short atomic transactions
- row-level locking with `FOR UPDATE SKIP LOCKED`
- time-based leasing for fault tolerance

This approach provides safe coordination across many workers while remaining simple to reason about.
