-- Restore the pre-A202 operator-capture CHECK constraints.
-- Operator capture rows are downgraded to dry-run, machine-verified audit rows.

UPDATE ingestion_evidence_chain
SET review_status = 'machine_verified'
WHERE review_status = 'operator_verified';

UPDATE entity_resolution_candidates
SET review_status = 'machine_verified'
WHERE review_status = 'operator_verified';

UPDATE raw_source_snapshots
SET review_status = 'machine_verified'
WHERE review_status = 'operator_verified';

UPDATE raw_source_snapshots
SET record_mode = 'dry_run'
WHERE record_mode = 'operator_source_capture';

ALTER TABLE ingestion_evidence_chain
  DROP CONSTRAINT IF EXISTS ingestion_evidence_chain_review_status_check;

ALTER TABLE ingestion_evidence_chain
  ADD CONSTRAINT ingestion_evidence_chain_review_status_check
  CHECK (review_status IN ('unreviewed','machine_verified','human_verified','disputed'));

ALTER TABLE entity_resolution_candidates
  DROP CONSTRAINT IF EXISTS entity_resolution_candidates_review_status_check;

ALTER TABLE entity_resolution_candidates
  ADD CONSTRAINT entity_resolution_candidates_review_status_check
  CHECK (review_status IN ('unreviewed','machine_verified','human_verified','disputed'));

ALTER TABLE raw_source_snapshots
  DROP CONSTRAINT IF EXISTS raw_source_snapshots_review_status_check;

ALTER TABLE raw_source_snapshots
  ADD CONSTRAINT raw_source_snapshots_review_status_check
  CHECK (review_status IN ('unreviewed','machine_verified','human_verified','disputed'));

ALTER TABLE raw_source_snapshots
  DROP CONSTRAINT IF EXISTS raw_source_snapshots_record_mode_check;

ALTER TABLE raw_source_snapshots
  ADD CONSTRAINT raw_source_snapshots_record_mode_check
  CHECK (record_mode IN ('fixture','curated_official_fixture','dry_run','live'));
