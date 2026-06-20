-- Reliable transactional outbox for refresh and worker events.
-- Acceptance IDs: A204, A205, A206

CREATE TABLE transactional_outbox (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  event_type text NOT NULL,
  aggregate_type text NOT NULL,
  aggregate_id uuid,
  idempotency_key text NOT NULL UNIQUE,
  payload jsonb NOT NULL DEFAULT '{}'::jsonb,
  priority integer NOT NULL DEFAULT 100 CHECK (priority BETWEEN 0 AND 1000),
  status text NOT NULL DEFAULT 'pending' CHECK (
    status IN ('pending','processing','dispatched','failed','dead_letter')
  ),
  scheduled_for timestamptz NOT NULL DEFAULT now(),
  attempt_count integer NOT NULL DEFAULT 0 CHECK (attempt_count >= 0),
  max_attempts integer NOT NULL DEFAULT 5 CHECK (max_attempts BETWEEN 1 AND 12),
  lease_owner text,
  lease_token uuid,
  lease_expires_at timestamptz,
  heartbeat_at timestamptz,
  last_error_class text,
  last_error_message text,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  dispatched_at timestamptz,
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX transactional_outbox_pending_idx
  ON transactional_outbox(status, scheduled_for, priority, created_at)
  WHERE status IN ('pending','failed');

CREATE INDEX transactional_outbox_event_status_idx
  ON transactional_outbox(event_type, status, updated_at DESC);

CREATE INDEX transactional_outbox_lease_expiry_idx
  ON transactional_outbox(status, lease_expires_at)
  WHERE status = 'processing';
