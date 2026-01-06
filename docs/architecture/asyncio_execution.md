# Asyncio Execution, Timeouts, and Cancellation

This document summarizes how asyncio handles timeouts and cancellation, based on
small execution experiments.

---

## Timeouts (`asyncio.wait_for`)

- `asyncio.wait_for(coro, timeout)` enforces timeouts by **cancelling** the task.
- A timeout raises `asyncio.TimeoutError` to the caller.
- Inside the task, cancellation manifests as `asyncio.CancelledError`.
- `finally` blocks are executed on timeout-induced cancellation.

**Implication:** timeouts are a form of cancellation.

---

## Manual Cancellation (`task.cancel()`)

- Calling `task.cancel()` injects `CancelledError` into the task.
- The task may stop at the next await point.
- `finally` blocks always run.
- The caller must handle `asyncio.CancelledError`.

---

## Worker Design Implications

- Task execution must wrap user code in `try/finally`.
- Cleanup logic (releasing resources, updating state) belongs in `finally`.
- Timeouts and cancellations should be treated as retryable failures by default.
- Cancellation is cooperative; tasks must be written to be cancellable.

---

## Error Classification

| Event | Exception Seen | Meaning |
|-----|---------------|--------|
| Timeout | `TimeoutError` (caller) | Execution exceeded allowed time |
| Cancellation | `CancelledError` | Task intentionally stopped |
| Crash | Other Exception | Bug or non-retryable failure |

---

## Summary

Asyncio enforces execution limits via cancellation, not preemption.  
Correct worker behavior depends on handling `CancelledError` and ensuring cleanup
runs reliably.
