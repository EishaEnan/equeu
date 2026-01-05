# Failure Modes & Mitigations (to test later)

## Network failures
- **API ↔ DB connection drop / timeout**
  - *Mitigation:* connection pool + retries with backoff; fail fast on enqueue if DB unavailable.
  - *Test:* kill DB container mid-request; simulate slow DB responses.
- **Worker ↔ DB connection drop**
  - *Mitigation:* reconnect loop; avoid holding long transactions; claim is short + retry-safe.
  - *Test:* drop worker network during claim and during status update.

## Worker failures
- **Worker crash during execution**
  - *Mitigation:* lease (`locked_until`) expires; job becomes reclaimable; task handler must be idempotent.
  - *Test:* `SIGKILL` worker mid-job; ensure job is re-claimed after lease expiry.
- **Worker crash after claim, before marking outcome**
  - *Mitigation:* same as above (lease expiry); keep claim txn short; ensure “running” implies lease.
  - *Test:* crash worker immediately after claim; validate no job is stuck forever.
- **Duplicate execution (at-least-once behavior)**
  - *Mitigation:* idempotent handlers; results table uses unique key + UPSERT.
  - *Test:* force lease expiry early; run two workers; confirm result written once.
- **Poison pill job (always fails)**
  - *Mitigation:* `attempts/max_attempts` + `run_at` backoff; terminal `dead`.
  - *Test:* task that always raises; verify transitions to `dead` and stops retrying.

## Database failures
- **DB outage / restart**
  - *Mitigation:* durability via Postgres; workers retry connections; jobs remain in DB.
  - *Test:* restart Postgres; verify workers recover and continue processing.
- **DB contention on claim query**
  - *Mitigation:* indexes for runnable scan; keep claim txn minimal; tune polling; consider queue partitioning later.
  - *Test:* run N workers; measure claim latency; ensure no deadlocks.
- **Long transactions / locking issues**
  - *Mitigation:* never execute jobs inside a transaction; use `FOR UPDATE SKIP LOCKED`.
  - *Test:* inject slow queries; verify workers don’t block each other.

## Data / correctness failures
- **Invalid payload / task not found**
  - *Mitigation:* validate at enqueue; mark job `dead` as non-retryable with error message.
  - *Test:* enqueue bad task name; ensure it goes terminal without infinite retries.
- **Clock skew**
  - *Mitigation:* rely on DB time (`now()`) for `run_at` / `locked_until`.
  - *Test:* set worker clock wrong; ensure scheduling still behaves correctly (DB-driven).

## Observability gaps
- **Stuck jobs / silent failures**
  - *Mitigation:* metrics/queries for: running with expired lease, high retry counts, dead jobs rate.
  - *Test:* create stuck conditions; verify detection queries and dashboard filters work.
