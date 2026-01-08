#src/equeue/api/models/jobs.py

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict, field_validator, ValidationError


# ----------- Shared types -----------

class JobStatus(str, Enum):
    queued = "queued"
    running = "running"
    succeeded = "succeeded"
    dead = "dead"
    cancelled = "cancelled"


class JobError(BaseModel):
    """
    Stored in jobs.last_error (jsonb). Keeping it flexible for starter.
    """
    model_config = ConfigDict(extra="allow")

    type: str | None = None
    message: str | None = None
    retryable: bool | None = None
    happened_at: datetime | None = None


# ----------- Requests ----------------

class EnqueueJobRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    task_name: str = Field(..., description="Namespaced task identifier, e.g. puzzles.extract_mate_tag")
    queue: str = Field(..., description="Routing topic/queue name")
    payload: dict[str, Any] = Field(default_factory=dict)

    priority: int = Field(0, description="Higher runs sooner (within same run_at)")
    run_at: datetime | None = Field(None, description="If omitted, run as soon as possible")

    idempotency_key: str | None = Field(None, description="Optional; unique per (created_by, idempotency_key)")

    @field_validator("task_name", "queue")
    @classmethod
    def non_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("must be non-empty")
        return v
    

class CancelJobResponse(BaseModel):
    """
    To signal 'accepted' when cancelling a running job.
    """
    model_config = ConfigDict(extra="forbid")

    job: "JobPublic"
    accepted: bool = Field(..., description="True if cancellation was requested/recorded")


# ---------------- Responses -------------------

class JobPublic(BaseModel):
    """
    What the API returns. Mirrors the jobs table but avoids leaking internal lock details unless expected.
    """
    model_config = ConfigDict(extra="forbid")

    id: UUID
    task_name: str
    status: JobStatus
    queue: str
    payload: dict[str, Any]

    priority: int
    run_at: datetime

    attempts: int
    max_attempts: int

    # ownership / adult
    created_by: str
    created_at: datetime
    updated_at: datetime

    # cancellation
    cancel_requested_at: datetime | None = None

    # debugging
    last_error: dict[str, Any] | JobError | None = None

    # when added 
    # results: dict[str, Any] | None = None


class JobListPage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[JobPublic]
    next_cursor: str | None = None


# ------------- Query params model ----------

class JobListQuery(BaseModel):
    
    model_config = ConfigDict(extra="forbid")

    status: list[JobStatus] | None = None
    task_name: str | None = None
    queue: str | None = None

    created_after: datetime | None = None
    created_before: datetime | None = None

    limit: int = Field(50, ge=1, le=200)
    cursor: str | None = None

    @field_validator("task_name", "queue")
    @classmethod
    def strip_optional(cls, v: str | None) -> str | None:
        return v.strip() if v is not None else None
