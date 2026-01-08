#tests/test_jobs_routes.py

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from equeue.api.routes.jobs import (
    router,
    get_auth_context,
    get_queue_client,
    AuthContext,
    QueueClient,
)

from equeue.api.models.jobs import (
    EnqueueJobRequest,
    JobListPage,
    JobListQuery,
    JobPublic,
    JobStatus,
)

# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

@pytest.fixture
def now() -> datetime:
    return datetime.now(timezone.utc)


@pytest.fixture
def job_factory(now):
    def _make_job(*, status: JobStatus = JobStatus.queued, job_id: UUID | None = None) -> JobPublic:
        job_model = JobPublic(
            id=job_id or uuid4(),
            task_name="puzzles.extract_mate_tag",
            status=status,
            queue="default",
            payload={},
            priority=0,
            run_at=now,
            attempts=0,
            max_attempts=25,
            created_by="user-1",
            created_at=now,
            updated_at=now,
            cancel_requested_at=None,
            last_error=None,
        )
        return job_model
    return _make_job


# ------------------------------------------------------------------
# Fake dependencies
# ------------------------------------------------------------------

@pytest.fixture
def fake_queue_client(job_factory):
    class FakeQueueClient(QueueClient):
        async def enqueue(self, *, created_by: str, req: EnqueueJobRequest) -> JobPublic:
            return job_factory(status=JobStatus.queued)
        
        async def get(self, *, created_by: str, job_id: UUID) -> JobPublic:
            return job_factory(status=JobStatus.succeeded, job_id=job_id)

        async def list(self, *, created_by: str, q: JobListQuery) -> JobListPage:
            return JobListPage(items=[job_factory()], next_cursor=None)

        async def cancel(self, *, created_by: str, job_id: UUID):
            return job_factory(status=JobStatus.running, job_id=job_id), True

    return FakeQueueClient()

@pytest.fixture
def override_auth_context():
    return AuthContext(principal_id="user-1")


@pytest.fixture
def app(fake_queue_client, override_auth_context) -> FastAPI:
    app = FastAPI()
    app.include_router(router)

    app.dependency_overrides[get_queue_client] = lambda: fake_queue_client
    app.dependency_overrides[get_auth_context] = lambda: override_auth_context

    return app

@pytest.fixture
def client(app: FastAPI) -> TestClient:
    return TestClient(app)

@pytest.fixture
def auth_headers() -> dict[str, str]:
    return {"Authorization": "Bearer test"}


# ------------------------------------------------------------------
# Tests
# ------------------------------------------------------------------

def test_enqueue_requires_auth():
    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)

    resp = client.post("/v1/jobs/", json={"task_name": "x", "queue": "q", "payload": {}})
    assert resp.status_code == 401



def test_enqueue_job_success(client: TestClient, auth_headers):
    resp = client.post(
        "/v1/jobs/",
        headers=auth_headers,
        json={"task_name": "puzzles.extract_mate_tag", "queue": "default", "payload": {}},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["status"] == "queued"
    assert body["task_name"] == "puzzles.extract_mate_tag"


def test_get_job_success(client: TestClient, auth_headers):
    job_id = str(uuid4())
    resp = client.get(f"/v1/jobs/{job_id}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == job_id


def test_list_jobs_success(client: TestClient, auth_headers):
    resp = client.get("/v1/jobs/?limit=10", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body["items"], list)
    assert len(body["items"]) == 1


def test_cancel_running_job_returns_202(client: TestClient, auth_headers):
    job_id = str(uuid4())
    resp = client.post(f"/v1/jobs/{job_id}/cancel", headers=auth_headers)
    assert resp.status_code == 202
    assert resp.json()["status"] == "running"