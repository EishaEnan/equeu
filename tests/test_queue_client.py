# tests/test_queue_client.py

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

import pytest

from equeue.api.models.jobs import (
    EnqueueJobRequest,
    JobListPage,
    JobListQuery,
    JobPublic,
    JobStatus,
)

from equeue.api.queue_client import QueueClient, JobNotFoundError
from tests.utils import make_job, utcnow


class FakeRepo:
    """
    In-memory fake for QueueClient tests (no DB).
    """
    def __init__(self):
        self.jobs: dict[UUID, JobPublic] = {}
        self.last_insert_now: datetime | None = None

    async def insert_job(self, *, created_by: str, req: EnqueueJobRequest, now: datetime) -> JobPublic:
        self.last_insert_now = now
        job = JobPublic(
            id=uuid4(),
            task_name=req.task_name,
            status=JobStatus.queued,
            queue=req.queue,
            payload=req.payload,
            priority=req.priority,
            run_at=req.run_at if req.run_at is not None else now,
            attempts=0,
            max_attempts=25,
            created_by=created_by,
            created_at=now,
            updated_at=now,
            cancel_requested_at=None,
            last_error=None,
        )
        self.jobs[job.id] = job
        return job

    async def get_job(self, *, created_by: str, job_id: UUID) -> JobPublic | None:
        job = self.jobs.get(job_id)
        if job is None or job.created_by != created_by:
            return None
        return job

    async def list_jobs(self, *, created_by: str, q: JobListQuery) -> JobListPage:
        # minimal fake: return all jobs for created_by, ignore filters for now
        items = [j for j in self.jobs.values() if j.created_by == created_by]
        return JobListPage(items=items, next_cursor=None)

    async def cancel_job(self, *, created_by: str, job_id: UUID, now: datetime):
        job = self.jobs.get(job_id)
        if job is None or job.created_by != created_by:
            return None, False

        # emulate semantics:
        if job.status == JobStatus.queued:
            job = job.model_copy(update={"status": JobStatus.cancelled, "updated_at": now})
            self.jobs[job_id] = job
            return job, False

        if job.status == JobStatus.running:
            job = job.model_copy(update={"cancel_requested_at": now, "updated_at": now})
            self.jobs[job_id] = job
            return job, True

        # terminal: no-op
        return job, False


@pytest.mark.anyio
async def test_enqueue_sets_run_at_default_when_missing():
    repo = FakeRepo()
    qc = QueueClient(repo=repo)

    req = EnqueueJobRequest(task_name="puzzles.extract_mate_tag", queue="default", payload={})
    job = await qc.enqueue(created_by="user-1", req=req)

    assert job.run_at is not None
    # ensure QueueClient normalized run_at to "now" (repo sees same-ish now)
    assert repo.last_insert_now is not None
    assert abs((job.run_at - repo.last_insert_now).total_seconds()) < 2


@pytest.mark.anyio
async def test_get_returns_job_for_owner():
    repo = FakeRepo()
    job = make_job(created_by="user-1")
    repo.jobs[job.id] = job

    qc = QueueClient(repo=repo)
    got = await qc.get(created_by="user-1", job_id=job.id)

    assert got.id == job.id


@pytest.mark.anyio
async def test_get_hides_job_if_wrong_owner_as_not_found():
    repo = FakeRepo()
    job = make_job(created_by="user-1")
    repo.jobs[job.id] = job

    qc = QueueClient(repo=repo)

    with pytest.raises(JobNotFoundError):
        await qc.get(created_by="user-2", job_id=job.id)


@pytest.mark.anyio
async def test_list_scopes_to_created_by():
    repo = FakeRepo()
    job1 = make_job(created_by="user-1")
    job2 = make_job(created_by="user-2")
    repo.jobs[job1.id] = job1
    repo.jobs[job2.id] = job2

    qc = QueueClient(repo=repo)
    page = await qc.list(created_by="user-1", q=JobListQuery(limit=50))

    assert len(page.items) == 1
    assert page.items[0].created_by == "user-1"


@pytest.mark.anyio
async def test_cancel_queued_sets_cancelled_and_not_accepted():
    repo = FakeRepo()
    job = make_job(created_by="user-1", status=JobStatus.queued)
    repo.jobs[job.id] = job

    qc = QueueClient(repo=repo)
    updated, accepted = await qc.cancel(created_by="user-1", job_id=job.id)

    assert updated.status == JobStatus.cancelled
    assert accepted is False


@pytest.mark.anyio
async def test_cancel_running_sets_cancel_requested_and_accepted_true():
    repo = FakeRepo()
    job = make_job(created_by="user-1", status=JobStatus.running)
    repo.jobs[job.id] = job

    qc = QueueClient(repo=repo)
    updated, accepted = await qc.cancel(created_by="user-1", job_id=job.id)

    assert updated.status == JobStatus.running
    assert updated.cancel_requested_at is not None
    assert accepted is True


@pytest.mark.anyio
async def test_cancel_not_found_raises():
    repo = FakeRepo()
    qc = QueueClient(repo=repo)

    with pytest.raises(JobNotFoundError):
        await qc.cancel(created_by="user-1", job_id=uuid4())
