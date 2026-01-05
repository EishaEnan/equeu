# Job State Machine

This document defines the minimal job lifecycle for **eQueue**. A “failure” is treated as an **attempt outcome**, not a persistent `failed` state. Retry is represented by rescheduling the job back to `queued` with a future `run_at`.

## States

- `queued` — eligible to be claimed when `run_at <= now()`.
- `running` — leased to a worker (`locked_by`, `locked_until` set).
- `succeeded` — completed successfully (terminal).
- `dead` — failed permanently (terminal).
- `cancelled` — explicitly stopped by a user/admin; terminal state.

## Transitions

| From       | To         | Trigger / Condition | DB Update Summary |
|-----------|------------|---------------------|-------------------|
| `queued`  | `running`  | Worker claims job (atomic claim) | set `status=running`, set `locked_by`, set `locked_until` |
| `running` | `succeeded`| Job completes successfully | set `status=succeeded`, clear/ignore lease fields (optional) |
| `running` | `queued`   | Attempt fails AND `attempts < max_attempts` | set `status=queued`, set `run_at = now() + backoff`, set `last_error` |
| `running` | `dead`     | Attempt fails AND `attempts >= max_attempts` OR non-retryable error | set `status=dead`, set `last_error` |
| `queued`  | `cancelled`| User/admin cancels before execution | set `status=cancelled` |
| `running` | `cancelled`| User/admin cancels while running (best-effort) | set `status=cancelled` (worker may still finish; decide policy later) |

## Notes

- **Retry scheduling:** only jobs in `queued` with `run_at <= now()` are claimable. Backoff is implemented by pushing `run_at` into the future.
- **Leasing:** `running` implies a valid lease; if a worker dies, the job can be reclaimed after `locked_until` expires (policy defined in worker logic).
- **Cancellation semantics:** cancelling a `running` job is best-effort unless you implement cooperative cancellation in job handlers.
