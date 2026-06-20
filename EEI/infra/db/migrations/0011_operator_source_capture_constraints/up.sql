-- Allow operator-supplied official source captures to be stored as audited raw inputs.
-- Acceptance IDs: A202

ALTER TABLE raw_source_snapshots
  DROP CONSTRAINT IF EXISTS raw_source_snapshots_record_mode_check;

ALTER TABLE raw_source_snapshots
  ADD CONSTRAINT raw_source_snapshots_record_mode_check
  CHECK (
    record_mode IN (
      'fixture',
      'curated_official_fixture',
      'dry_run',
      'operator_source_capture',
      'live'
    )
  );

ALTER TABLE raw_source_snapshots
  DROP CONSTRAINT IF EXISTS raw_source_snapshots_review_status_check;

ALTER TABLE raw_source_snapshots
  ADD CONSTRAINT raw_source_snapshots_review_status_check
  CHECK (
    review_status IN (
      'unreviewed',
      'machine_verified',
      'operator_verified',
      'human_verified',
      'disputed'
    )
  );

ALTER TABLE entity_resolution_candidates
  DROP CONSTRAINT IF EXISTS entity_resolution_candidates_review_status_check;

ALTER TABLE entity_resolution_candidates
  ADD CONSTRAINT entity_resolution_candidates_review_status_check
  CHECK (
    review_status IN (
      'unreviewed',
      'machine_verified',
      'operator_verified',
      'human_verified',
      'disputed'
    )
  );

ALTER TABLE ingestion_evidence_chain
  DROP CONSTRAINT IF EXISTS ingestion_evidence_chain_review_status_check;

ALTER TABLE ingestion_evidence_chain
  ADD CONSTRAINT ingestion_evidence_chain_review_status_check
  CHECK (
    review_status IN (
      'unreviewed',
      'machine_verified',
      'operator_verified',
      'human_verified',
      'disputed'
    )
  );
