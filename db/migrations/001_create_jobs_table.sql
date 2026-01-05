-------For uuid generation ---
CREATE EXTENSION IF NOT EXISTS pgcrypto;

----------- Enum for status---
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'job_status') THEN
        CREATE TYPE job_status AS ENUM (
            'queued',
            'running',
            'succeeded',
            'dead',
            'cancelled'
        );
    END IF;
END $$;
------------Jobs Table -------
CREATE TABLE IF NOT EXISTS jobs(
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    
    status          job_status NOT NULL DEFAULT 'queued',
    queue           text NOT NULL,  -- aka topic
    payload         jsonb NOT NULL DEFAULT '{}'::jsonb,

    priority        integer NOT NULL DEFAULT 0, -- higher = sooner
    run_at          timestamptz NOT NULL DEFAULT now(),

    attempts        integer NOT NULL DEFAULT 0,
    max_attempts    integer NOT NULL DEFAULT 25,

    -- leasing/ownership 
    locked_until    timestamptz,
    locked_by       text,

    last_error      text,

    created_at      timestamptz NOT NULL DEFAULT now(),
    updated_at      timestamptz NOT NULL DEFAULT now(),

    -- sanity constraints
    CONSTRAINT attempts_nonneg CHECK (attempts >= 0),
    CONSTRAINT max_attempts_positive CHECK (max_attempts > 0),
    CONSTRAINT attempts_le_max CHECK (attempts <= max_attempts),

    -- ensuring ownership
    CONSTRAINT running_requires_lock CHECK (
        status <> 'running'
        OR (locked_until IS NOT NULL AND locked_by IS NOT NULL)
    ) 
);


----------- Indexes ----------

---- Claim scan: runnable queued jobs by queue. run_at, priority

CREATE INDEX IF NOT EXISTS jobs_runnable_idx
    ON jobs (queue, run_at, priority DESC, created_at)
    WHERE status = 'queued';

---  Re-claim 'stuck' running jobs whose lease expired: locked_until < now()
CREATE INDEX IF NOT EXISTS jobs_expired_lease_idx
    ON jobs (queue, locked_until)
    WHERE status = 'running' AND locked_until IS NOT NULL;

--- Dashboard filters
CREATE INDEX IF NOT EXISTS jobs_status_update_idx
    ON jobs (status, updated_at DESC);

CREATE INDEX IF NOT EXISTS jobs_queue_status_idx
    ON jobs (queue, status);

--- update_at trigger
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS trigger AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_jobs_update_at ON jobs;

CREATE TRIGGER trg_jobs_update_at
BEFORE UPDATE ON jobs
FOR EACH ROW
EXECUTE FUNCTION set_update_at();