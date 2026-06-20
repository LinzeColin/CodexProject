-- Background scheduler, retry and dead-letter state.
-- Acceptance IDs: A206

CREATE TABLE background_jobs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  job_type text NOT NULL,
  idempotency_key text NOT NULL,
  payload jsonb NOT NULL DEFAULT '{}'::jsonb,
  priority integer NOT NULL DEFAULT 100 CHECK (priority BETWEEN 0 AND 1000),
  status text NOT NULL CHECK (
    status IN ('queued','running','succeeded','dead_letter','cancelled')
  ),
  scheduled_for timestamptz NOT NULL DEFAULT now(),
  attempt_count integer NOT NULL DEFAULT 0 CHECK (attempt_count >= 0),
  max_attempts integer NOT NULL DEFAULT 5 CHECK (max_attempts BETWEEN 1 AND 12),
  dead_letter_after_attempts integer NOT NULL DEFAULT 5
    CHECK (dead_letter_after_attempts BETWEEN 1 AND 12),
  lease_owner text,
  lease_token uuid,
  lease_expires_at timestamptz,
  heartbeat_at timestamptz,
  last_error_class text,
  last_error_message text,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  finished_at timestamptz,
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  UNIQUE (job_type, idempotency_key),
  CHECK (dead_letter_after_attempts <= max_attempts)
);

CREATE INDEX background_jobs_due_idx
  ON background_jobs(status, scheduled_for, priority, created_at)
  WHERE status = 'queued';

CREATE INDEX background_jobs_lease_expiry_idx
  ON background_jobs(status, lease_expires_at)
  WHERE status = 'running';

CREATE INDEX background_jobs_type_status_idx
  ON background_jobs(job_type, status, updated_at DESC);

CREATE TABLE background_job_attempts (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  job_id uuid NOT NULL REFERENCES background_jobs(id) ON DELETE CASCADE,
  attempt_no integer NOT NULL CHECK (attempt_no >= 1),
  worker_id text NOT NULL,
  lease_token uuid NOT NULL,
  status text NOT NULL CHECK (
    status IN ('running','succeeded','failed','released','expired')
  ),
  started_at timestamptz NOT NULL DEFAULT now(),
  heartbeat_at timestamptz,
  finished_at timestamptz,
  error_class text,
  error_message text,
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  UNIQUE (job_id, attempt_no)
);

CREATE INDEX background_job_attempts_job_idx
  ON background_job_attempts(job_id, attempt_no DESC);

CREATE TABLE dead_letter_jobs (
  job_id uuid PRIMARY KEY REFERENCES background_jobs(id) ON DELETE CASCADE,
  dead_lettered_at timestamptz NOT NULL DEFAULT now(),
  final_attempt_no integer NOT NULL CHECK (final_attempt_no >= 1),
  error_class text NOT NULL,
  error_message text NOT NULL,
  payload jsonb NOT NULL DEFAULT '{}'::jsonb,
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX dead_letter_jobs_time_idx
  ON dead_letter_jobs(dead_lettered_at DESC);
