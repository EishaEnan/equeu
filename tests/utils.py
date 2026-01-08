from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

from equeue.api.models.jobs import JobPublic, JobStatus


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def make_job(
    *,
    job_id: UUID | None = None,
    created_by: str = "user-1",
    status: JobStatus = JobStatus.queued,
    now: datetime | None = None,
) -> JobPublic:
    now = now or utcnow()
    return JobPublic(
        id=job_id or uuid4(),
        task_name="puzzles.extract_mate_tag",
        status=status,
        queue="default",
        payload={},
        priority=0,
        run_at=now,
        attempts=0,
        max_attempts=25,
        created_by=created_by,
        created_at=now,
        updated_at=now,
        cancel_requested_at=None,
        last_error=None,
    )
