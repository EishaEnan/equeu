#src/equeue/api/queue_client.py

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol
from uuid import UUID

from equeue.api.models.jobs import (
    EnqueueJobRequest,
    JobListPage,
    JobListQuery,
    JobPublic,
    JobStatus,
)

def utcnow() -> datetime:
    return datetime.now(timezone.utc)

# ------------------------------------------------------------------
# Repo boundary (DB later)
# ------------------------------------------------------------------

class JobRepo(Protocol):
    async def insert_job(self, *, created_by: str, req: EnqueueJobRequest, now: datetime) -> JobPublic: ...
    async def get_job(self, *, created_by: str, job_id: UUID) -> JobPublic | None: ...
    async def list_jobs(self, *, created_by: str, q: JobListQuery) -> JobListPage: ...
    async def cancel_job(self, *, created_by: str, job_id: UUID, now: datetime) -> tuple[JobPublic | None, bool]: ...
    # returns: (job_or_none, accepted_running_cancel)

# ------------------------------------------------------------------
# Domain-ish errors (API layer maps these to HTTP later)
# ------------------------------------------------------------------
class JobNotFoundError(Exception):
    pass


# ------------------------------------------------------------------
# QueueClient
# ------------------------------------------------------------------

@dataclass(frozen=True)
class QueueClient:
    repo: JobRepo

    async def enqueue(self, *, created_by: str, req: EnqueueJobRequest) -> JobPublic:
        # normalize run_at default here so repo stays dumb
        now = utcnow()
        if req.run_at is None:
            req = req.model_copy(update={"run_at": now})
        return await self.repo.insert_job(created_by=created_by, req=req, now=now)
    
    async def get(self, *, created_by: str, job_id: UUID) -> JobPublic:
        job = await self.repo.get_job(created_by=created_by,job_id=job_id)
        # ownership enforecement: return 404 if mismatch (don't leak existence)
        if job is None:
            raise JobNotFoundError()
        return job
    
    async def list(self, *, created_by: str, q: JobListQuery) -> JobListPage:
        # list is always scoped to created_by
        return await self.repo.list_jobs(created_by=created_by, q=q)
    
    async def cancel(self, *, created_by: str, job_id: UUID) -> tuple[JobPublic, bool]:
        now = utcnow()
        job, accepted = await self.repo.cancel_job(created_by=created_by, job_id=job_id, now=now)
        if job is None:
            raise JobNotFoundError()
        return job, accepted