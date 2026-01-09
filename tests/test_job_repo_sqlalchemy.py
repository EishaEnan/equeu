#tests/test_job_repo_sqlalchemy.py

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from equeue.api.models.jobs import EnqueueJobRequest, JobListQuery, JobStatus
from equeue.db.job_repo import SqlAlchemyJobRepo
from sqlalchemy import text


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


@pytest.mark.anyio
async def test_insert_and_get_non_leaky(session):
    repo = SqlAlchemyJobRepo(session=session)
    now = utcnow()

    req = EnqueueJobRequest(task_name="puzzles.extract_mate_tag", queue="default", payload={"puzzle_id": 1})
    job = await repo.insert_job(created_by="user-1", req=req, now=now)
    await session.commit()

    # owner can see it
    got = await repo.get_job(created_by="user-1", job_id=job.id)
    assert got is not None
    assert got.id == job.id

    # other user cannot see it (non-leaky)
    got2 = await repo.get_job(created_by="user-2", job_id=job.id)
    assert got2 is None


@pytest.fixture
async def test_insert_idempotency_returns_same_job(session):
    repo = SqlAlchemyJobRepo(session=session)
    now = utcnow()

    req1 = EnqueueJobRequest(
        task_name="puzzles.extract_mate_tag",
        queue="default",
        payload={"puzzle_id": "1"},
        idempotency_key="abc123",
    )
    job1 = await repo.insert_job(created_by="user-1", req=req1, now=now)
    await session.commit()

    req2 = EnqueueJobRequest(
        task_name="puzzles.extract_mate_tag",
        queue="default",
        payload={"puzzle_id": "SHOULD_NOT_MATTER"},
        idempotency_key="abc123",
    )
    job2 = await repo.insert_job(created_by="user-1", req=req2, now=now)
    await session.commit()

    assert job2.id == job1.id

@pytest.fixture
async def test_cancel_queued_sets_cancelled(session):
    repo = SqlAlchemyJobRepo(session=session)
    now = utcnow()

    req = EnqueueJobRequest(task_name="puzzles.extract_mate_tag", queue="default", payload={})
    job = await repo.insert_job(created_by="user-1", req=req, now=now)
    await session.commit()

    updated, accepted = await repo.cancel_job(created_by="user-1", job_id=job.id, now=utcnow())
    await session.commit()

    assert updated is not None
    assert updated.status == JobStatus.cancelled
    assert accepted is False

@pytest.mark.anyio
async def test_cancel_running_sets_cancel_requested_at_and_returns_accepted(session):
    repo = SqlAlchemyJobRepo(session=session)
    now = utcnow()

    req = EnqueueJobRequest(task_name="puzzles.extract_mate_tag", queue="default", payload={})
    job = await repo.insert_job(created_by="user-1", req=req, now=now)
    await session.commit()

    # Force job to running (simulating worker claim) — direct SQL is fine in repo tests
    await session.execute(
        text("UPDATE jobs SET status='running', locked_by='w1', locked_until=now() + interval '1 minute' WHERE id=:id"),
        {"id": job.id},
    )
    await session.commit()

    updated, accepted = await repo.cancel_job(created_by="user-1", job_id=job.id, now=utcnow())
    await session.commit()

    assert updated is not None
    assert updated.status == JobStatus.running
    assert updated.cancel_requested_at is not None
    assert accepted is True


@pytest.mark.anyio
async def test_list_cursor_pagination(session):
    repo = SqlAlchemyJobRepo(session=session)
    now = utcnow()

    # Insert 3 jobs
    for i in range(3):
        req = EnqueueJobRequest(task_name="puzzles.extract_mate_tag", queue="default", payload={"i": i})
        await repo.insert_job(created_by="user-1", req=req, now=now)
    await session.commit()

    page1 = await repo.list_jobs(created_by="user-1", q=JobListQuery(limit=2))
    assert len(page1.items) == 2
    assert page1.next_cursor is not None

    page2 = await repo.list_jobs(created_by="user-1", q=JobListQuery(limit=2, cursor=page1.next_cursor))
    assert len(page2.items) == 1
    assert page2.next_cursor is None