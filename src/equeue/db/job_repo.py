#src/equeue/db/job_repo.py

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from equeue.api.models.jobs import (
    EnqueueJobRequest,
    JobListPage,
    JobListQuery,
    JobPublic,
    JobStatus,
)

from equeue.db.cursor import decode_cursor, encode_cursor



def _row_to_job(row: Any) -> JobPublic:
    """
    SQLAlchemy row -> JobPublic
    Assumes row has columns matching jobs table.
    """
    # row may be RowMapping or similar
    r = dict(row)

    # last_error: allow dict;
    last_error = r.get("last_error")

    model = JobPublic(
        id=r["id"],
        task_name=r["task_name"],
        status=JobStatus(r["status"]) if not isinstance(r["status"], JobStatus) else r["status"],
        queue=r["queue"],
        payload=r["payload"] or {},
        priority=r["priority"],
        run_at=r["run_at"],
        attempts=r["attempts"],
        max_attempts=r["max_attempts"],
        created_by=r["created_by"],
        created_at=r["created_at"],
        updated_at=r["updated_at"],
        cancel_requested_at=r.get("cancel_requested_at"),
        last_error=last_error,  # can be dict; model will normalize if typed as JobError|None
    )

    return model


@dataclass(frozen=True)
class SQLAlchemyJobRepo:
    """
    Non-leaky repo: get/cancel are scoped by created_by in SQL.
    """
    session: AsyncSession

    async def insert_job(self, *, created_by: str, req: EnqueueJobRequest, now: datetime) -> JobPublic:
        sql = text(
            """
            INSERT INTO jobs (
                task_name, status, queue, payload, priority, run_at, attempts, max_attempts,
                last_error, created_by, cancel_requested_at, idempotency_key
            )
            VALUES (
                :task_name, 'queued', :queue, :payload::jsonb, :priority, :run_at,
                0, :max_attempts, NULL, :created_by, NULL, :idempotency_key     
            )
            ON CONFLICT (created_by, idempotency_key)
            WHERE idempotency_key is NOT NULL
            DO UPDATE SET idempotency_key = EXCLUDED.idempotency_key
            RETURNING *
            """
        )

        params = {
            "task_name": req.task_name,
            "queue": req.queue,
            "payload": req.payload,
            "priority": req.priority,
            "run_at": req.run_at if req.run_at is not None else now,
            "max_attempts": 25,
            "created_by": created_by,
            "idempotency_key": req.idempotency_key,
        }

        res = await self.session.execute(sql, params)
        row = res.mappings().one()
        return _row_to_job(row)

    async def get_job(self, *, created_by: str, job_id: UUID) -> JobPublic | None:
        sql = text(
            """
            SELECT *
            FROM jobs
            WHERE id = :job_id
                AND created_by = :created_by
            """
        )

        res = await self.session.execute(sql, {"job_id": job_id, "created_by": created_by})
        row = res.mappings().first()
        return _row_to_job(row) if row else None
    
    async def list_jobs(self, *, created_by: str, q: JobListQuery) -> JobListPage:
        cursor_created_at = None
        cursor_id = None
        if q.cursor:
            c = decode_cursor(q.cursor)
            cursor_created_at = c.created_at
            cursor_id = c.id
        
        statuses = [s.value for s in q.status] if q.status else None
        limit_plus_one = q.limit + 1

        sql = text(
            """
            SELECT *
            FROM jobs
            WHERE created_by = :created_by
                AND (:statuses_is_null OR  status = ANY(:statuses::job_status[]))
                AND (:queue_is_null OR queue = :queue)
                AND (:task_is_null OR task_name = :task_name)
                AND (:created_after_is_null OR created_at >= :created_after)
                AND (:created_before_is_null OR created_at <= :created_before)
                AND (
                        :cursor_created_at_is_null
                        OR (created_at, id) < (:cursor_created_at, :cursor_id)
                )
            ORDER BY created_at DESC, id DESC
            LIMIT :limit_plus_one
            """
        )

        params = {
            "created_by": created_by,
            "statuses_is_null": statuses is None,
            "statuses": statuses if statuses is not None else [],
            "queue_is_null": q.queue is None,
            "queue": q.queue,
            "task_is_null": q.task_name is None,
            "task_name": q.task_name,
            "created_after_is_null": q.created_after is None,
            "created_after": q.created_after,
            "created_before_is_null": q.created_before is None,
            "created_before": q.created_before,
            "cursor_created_at_is_null": cursor_created_at is None,
            "cursor_created_at": cursor_created_at,
            "cursor_id": cursor_id,
            "limit_plus_one": limit_plus_one,
        }

        res = await self.session.execute(sql, params)
        rows = res.mappings().all()

        items = [_row_to_job(r) for r in rows[: q.limit]]
        next_cursor = None
        if len(rows) > q.limit:
            last = items[-1]
            next_cursor = encode_cursor(last.created_at, last.id)
        
        return JobListPage(items=items, next_cursor=next_cursor)
    
    async def cancel_job(self, *, created_by: str, job_id: UUID, now: datetime) -> tuple[JobPublic | None, bool]:
        sql = text(
            """
            UPDATE jobs
            SET
                status = CASE
                    WHEN status = 'queued' THEN 'cancelled'::job_status
                    ELSE status
                END,
                cancel_requested_at = CASE
                    WHEN status = 'running' THEN COALESCE(cancel_requested_at, :now)
                    ELSE cancel_requested_at
                END,
                updated_at = :now
            WHERE id = :job_id
                AND created_by = :created_by
            RETURNING *
            """
        )

        res = await self.session.execute(sql, {"job_id": job_id, "created_by": created_by, "now": now})
        row = res.mappings().first()
        if not row:
            return None, False
        
        job = _row_to_job(row)
        accepted = (job.status == JobStatus.running) and (job.cancel_requested_at is not None)
        return job, accepted
    