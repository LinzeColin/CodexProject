-- Roll back persisted exploration state columns.

ALTER TABLE exploration_sessions
  DROP CONSTRAINT IF EXISTS exploration_sessions_hops_check,
  DROP CONSTRAINT IF EXISTS exploration_sessions_direction_check;

ALTER TABLE exploration_sessions
  DROP COLUMN IF EXISTS budget,
  DROP COLUMN IF EXISTS hops,
  DROP COLUMN IF EXISTS direction,
  DROP COLUMN IF EXISTS state_version;
