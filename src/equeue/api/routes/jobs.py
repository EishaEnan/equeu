from __future__ import annotations

from typing import Annotated
from fastapi import APIRouter, Depends, Header, HTTPException, Response, status
from uuid import UUID

from equeue.api.models.jobs import (
    EnqueueJobRequest,
    JobListPage,
    JobListQuery,
    JobPublic,
)


router = APIRouter(prefix="/v1/jobs", tags=["jobs"])

# ------------------------------------------------------------------
# Auth context (signature-only placeholder)
# ------------------------------------------------------------------


class AuthContext:
    def __init__(self, principal_id: str):
        self.principal_id = principal_id

def get_auth_context(authorization: str | None = Header(default=None)) -> AuthContext:
    """
    Signature placeholder. Will get replaced with real auth (JWT).
    """
    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Authorization")
    # TODO: parse/verify token
    return AuthContext(principal_id="user-1")

# ------------------------------------------------------------------
# QueueClient dependancy (signature-only placeholder)
# ------------------------------------------------------------------

class QueueClient:
    async def enqueue(self, *, created_by: str, req: EnqueueJobRequest) -> JobPublic: ...
    async def get(self, *, created_by: str, job_id: UUID) -> JobPublic: ...
    async def list(self, *, created_by: str, q: JobListQuery) -> JobListPage: ...
    async def cancel(self, *, created_by: str, job_id: UUID) -> tuple[JobPublic, bool]: ...

def get_queue_client() -> QueueClient:
    """
    Signature placeholder. Later: inject real implementation with DB session.
    """
    return QueueClient()


# ------------------------------------------------------------------
# Re-usable annotated types
# ------------------------------------------------------------------
AuthDep = Annotated[AuthContext, Depends(get_auth_context)]
ClientDep = Annotated[QueueClient, Depends(get_queue_client)]


# ---- Routes ----
@router.post("/", response_model=JobPublic, status_code=status.HTTP_201_CREATED)
async def enqueue_job(req: EnqueueJobRequest, auth: AuthDep, qc: ClientDep) -> JobPublic:
    """
    Enqueue a job. Idempotency should be handled by QueueClient using (created_by, idempotency_key).
    """
    return await qc.enqueue(created_by=auth.principal_id, req=req)

@router.get("/{job_id}", response_model=JobPublic)
async def get_job(job_id: UUID, auth: AuthDep, qc: ClientDep) -> JobPublic:
    """
    Fetch a single job. Must enforce ownership in QueueClient (created_by).
    """
    return await qc.get(created_by=auth.principal_id, job_id=job_id)

@router.get("/", response_model=JobListPage)
async def list_jobs(auth: AuthDep, qc: ClientDep, q: JobListQuery = Depends()) -> JobListPage:
    """
    List jobs for the authenticated principal.
    """
    return await qc.list(created_by=auth.principal_id, q=q)

@router.post("/{job_id}/cancel", response_model=JobPublic)
async def cancel_job(job_id: UUID, response: Response, auth: AuthDep, qc: ClientDep) -> JobPublic:
    """
    Cancel semantics:
        - queued -> cancelled (200)
        - runnint -> cancel_requested_at set (202)
        - terminal -> no-op (200)
    We signal running-cancel with HTTP 202.
    """
    job, accepted = await qc.cancel(created_by=auth.principal_id, job_id=job_id)
    if accepted and job.status.value == "running":
        response.status_code = status.HTTP_202_ACCEPTED
    return job


