-- Persist canonical exploration state for session and URL restoration.
-- Acceptance IDs: A041,A051

ALTER TABLE exploration_sessions
  ADD COLUMN IF NOT EXISTS state_version text NOT NULL DEFAULT 'exploration-state-v1',
  ADD COLUMN IF NOT EXISTS direction text NOT NULL DEFAULT 'both',
  ADD COLUMN IF NOT EXISTS hops integer NOT NULL DEFAULT 1,
  ADD COLUMN IF NOT EXISTS budget jsonb NOT NULL DEFAULT '{"max_nodes":42,"max_edges":64,"expand_nodes":12}'::jsonb;

ALTER TABLE exploration_sessions
  DROP CONSTRAINT IF EXISTS exploration_sessions_direction_check,
  ADD CONSTRAINT exploration_sessions_direction_check
  CHECK (direction IN ('both','upstream','downstream','in','out'));

ALTER TABLE exploration_sessions
  DROP CONSTRAINT IF EXISTS exploration_sessions_hops_check,
  ADD CONSTRAINT exploration_sessions_hops_check
  CHECK (hops BETWEEN 1 AND 2);
