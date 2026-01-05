# AWS SQS Concepts → PostgreSQL Queue Mapping (eQueue)

This document maps core AWS SQS concepts to their equivalents in a PostgreSQL-backed
task queue (eQueue). The goal is to understand *why* these features exist and how
they can be implemented without a managed broker.

---

## Core Concept Mapping

| AWS SQS Concept | SQS Meaning | PostgreSQL / eQueue Equivalent |
|-----------------|------------|--------------------------------|
| Message | Unit of work | Row in `jobs` table |
| Queue | Logical message stream | `queue` column (topic / namespace) |
| Visibility Timeout | Message hidden after receive | `locked_until` lease |
| Receive Message | Reserve message | `SELECT … FOR UPDATE SKIP LOCKED` |
| Delete Message | Acknowledge success | Update `status = succeeded` |
| Delay Queue | Message not immediately visible | `run_at > now()` |
| Dead-Letter Queue (DLQ) | Messages that exceeded retries | `status = dead` |
| MaxReceiveCount | Retry limit | `attempts >= max_attempts` |
| At-least-once delivery | Possible duplicate delivery | Lease expiry + idempotency |
| Long polling | Reduce empty receives | LISTEN/NOTIFY + poll fallback |

---

## Visibility Timeout → Job Leasing

### SQS
- When a consumer receives a message, it becomes invisible for `visibility_timeout`
- If the consumer crashes before deleting it, the message reappears

### eQueue
- When a worker claims a job:
  - `status = running`
  - `locked_until = now() + lease_duration`
- If the worker crashes:
  - lease expires
  - job becomes reclaimable

**Key insight:**  
`locked_until` is the PostgreSQL equivalent of SQS visibility timeout.

---

## Delayed Messages → `run_at`

### SQS
- Messages can be delayed (per-queue or per-message)
- Message is invisible until delay expires

### eQueue
- Jobs remain `queued`
- `run_at` determines eligibility
- Claim query enforces `run_at <= now()`

This unifies:
- delayed jobs
- scheduled execution
- retry backoff

into a single column.

---

## Dead-Letter Queue → `status = dead`

### SQS
- Messages exceeding `maxReceiveCount` are moved to a DLQ
- DLQ is inspected manually or processed separately

### eQueue
- When `attempts >= max_attempts`:
  - job transitions to `status = dead`
- Same table, different terminal state

**Design choice:**  
DLQ is modeled as a **state**, not a separate queue.

---

## Receive + Delete → Claim + Acknowledge

### SQS
- Receive message (not removed yet)
- Process message
- Delete message on success

### eQueue
- Claim job (short transaction, row lock)
- Execute job outside transaction
- Explicitly mark terminal state (`succeeded`, `dead`, `cancelled`)

This separation mirrors SQS’s receive/delete model.

---

## At-Least-Once Delivery Guarantees

### SQS
- Messages may be delivered more than once
- Consumers must be idempotent

### eQueue
- Jobs may be re-claimed if:
  - worker crashes
  - lease expires
- Idempotency must be enforced at the task level

**Equivalent risk, different mechanism.**

---

## Polling vs Long Polling → LISTEN/NOTIFY + Poll

### SQS
- Long polling reduces empty receives
- Still requires periodic polling

### eQueue
- LISTEN/NOTIFY wakes workers immediately
- Polling fallback guarantees no missed jobs

This preserves correctness without relying on best-effort notifications.

---

## What PostgreSQL Cannot Do Like SQS

- Infinite horizontal scaling without coordination
- Managed durability and availability guarantees
- Automatic shard partitioning

These trade-offs are accepted intentionally for:
- transparency
- control
- learning value

---

## What PostgreSQL Enables That SQS Does Not

- Strong consistency with transactional guarantees
- Arbitrary querying for monitoring and debugging
- Rich job metadata and history
- Easier local development and testing

---

## Summary Insight

SQS and eQueue solve the same problems with different primitives:

- SQS uses **broker-managed invisibility**
- eQueue uses **database-managed leasing**

The underlying guarantees (at-least-once delivery, retries, DLQ)
are conceptually identical.

---

## Impact on eQueue Design

- `locked_until` is mandatory (visibility timeout)
- `run_at` replaces delayed messages
- `status = dead` replaces DLQ
- Idempotency is required at task level
- Short-lived claim transactions are critical
