import pytest
from datetime import datetime, timezone
from uuid import uuid4

from pydantic import ValidationError

from equeue.api.models.jobs import (
    EnqueueJobRequest,
    JobError,
    JobListQuery,
    JobPublic,
    JobStatus,
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def test_enqueue_rejects_extra_fields():
    with pytest.raises(ValidationError):
        EnqueueJobRequest(
            task_name="puzzles.extract_mate_tag",
            queue="default",
            payload={},
            unexpected="nope",
        )


def test_enqueue_strips_task_name_and_queue():
    req = EnqueueJobRequest(
        task_name="  puzzles.extract_mate_tag  ",
        queue="  default  ",
        payload={},
    )
    assert req.task_name == "puzzles.extract_mate_tag"
    assert req.queue == "default"


@pytest.mark.parametrize(
    "task_name,queue",
    [
        ("", "default"),
        ("   ", "default"),
        ("puzzles.extract_mate_tag", ""),
        ("puzzles.extract_mate_tag", "   "),
    ],
)
def test_enqueue_rejects_empty_task_name_or_queue(task_name, queue):
    with pytest.raises(ValidationError):
        EnqueueJobRequest(task_name=task_name, queue=queue, payload={})


def test_job_error_allows_extra_keys():
    err = JobError(type="TimeoutError", message="timed out", foo="bar", code=123)
    assert err.type == "TimeoutError"
    # extra fields should be preserved on model_dump (extra="allow")
    dumped = err.model_dump()
    assert dumped["foo"] == "bar"
    assert dumped["code"] == 123


def test_job_list_query_limit_bounds():
    # ok
    q = JobListQuery(limit=1)
    assert q.limit == 1

    # too small
    with pytest.raises(ValidationError):
        JobListQuery(limit=0)

    # too large
    with pytest.raises(ValidationError):
        JobListQuery(limit=201)


def test_job_list_query_strips_optional_filters():
    q = JobListQuery(task_name="  puzzles.extract_mate_tag  ", queue="  default  ")
    assert q.task_name == "puzzles.extract_mate_tag"
    assert q.queue == "default"


def test_job_public_accepts_last_error_as_dict():
    job = JobPublic(..., last_error={"type": "KeyError", "message": "missing key", "retryable": False})
    assert isinstance(job.last_error, JobError)
    assert job.last_error.type == "KeyError"



def test_job_public_accepts_last_error_as_dict():
    job = JobPublic(
        id=uuid4(),
        task_name="puzzles.extract_mate_tag",
        status=JobStatus.dead,
        queue="default",
        payload={},
        priority=0,
        run_at=_now(),
        attempts=1,
        max_attempts=25,
        created_by="user-1",
        created_at=_now(),
        updated_at=_now(),
        last_error={"type": "KeyError", "message": "missing key", "retryable": False},
    )
    assert isinstance(job.last_error, dict)
    assert job.last_error["type"] == "KeyError"


def test_job_public_rejects_extra_fields():
    with pytest.raises(ValidationError):
        JobPublic(
            id=uuid4(),
            task_name="puzzles.extract_mate_tag",
            status=JobStatus.queued,
            queue="default",
            payload={},
            priority=0,
            run_at=_now(),
            attempts=0,
            max_attempts=25,
            created_by="user-1",
            created_at=_now(),
            updated_at=_now(),
            # extra:
            locked_by="worker-1",
        )
