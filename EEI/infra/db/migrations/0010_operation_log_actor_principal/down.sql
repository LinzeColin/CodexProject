-- Restore the pre-A207 local actor allow-list.

UPDATE operation_logs
SET actor = 'local_user'
WHERE actor NOT IN ('local_user', 'system', 'codex');

ALTER TABLE operation_logs
  DROP CONSTRAINT IF EXISTS operation_logs_actor_check;

ALTER TABLE operation_logs
  ADD CONSTRAINT operation_logs_actor_check
  CHECK (actor IN ('local_user', 'system', 'codex'));
