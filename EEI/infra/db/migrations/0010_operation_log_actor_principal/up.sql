-- Allow audited user/workspace principals for saved-view namespace isolation.
-- Acceptance IDs: A207

ALTER TABLE operation_logs
  DROP CONSTRAINT IF EXISTS operation_logs_actor_check;

ALTER TABLE operation_logs
  ADD CONSTRAINT operation_logs_actor_check
  CHECK (actor ~ '^[A-Za-z0-9][A-Za-z0-9_.:@-]{0,119}$');
