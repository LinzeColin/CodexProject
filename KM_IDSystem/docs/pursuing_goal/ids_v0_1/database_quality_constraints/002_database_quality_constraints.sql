-- IDS v0.1 STAGE-036 database-quality constraint migration contract.
-- Task: IDS-V0_1-STAGE036-P2
-- Migration id: ids_stage036_002_database_quality_constraints
-- This file is tracked but NOT EXECUTED in Phase 2.
-- Future apply requires owner-authorized real-data profile, backup, and rollback refs.

-- migrate:up

DO $ids_quality_gate$
DECLARE
  profile_ref text := current_setting('ids.owner_authorized_real_profile_ref', true);
  backup_ref text := current_setting('ids.migration_backup_checkpoint_ref', true);
  rollback_ref text := current_setting('ids.migration_rollback_plan_ref', true);
BEGIN
  IF profile_ref IS NULL OR btrim(profile_ref) = '' THEN
    RAISE EXCEPTION 'STAGE-036 apply blocked: owner-authorized real-data profile ref is required';
  END IF;
  IF backup_ref IS NULL OR btrim(backup_ref) = '' THEN
    RAISE EXCEPTION 'STAGE-036 apply blocked: migration backup checkpoint ref is required';
  END IF;
  IF rollback_ref IS NULL OR btrim(rollback_ref) = '' THEN
    RAISE EXCEPTION 'STAGE-036 apply blocked: migration rollback plan ref is required';
  END IF;
END
$ids_quality_gate$;

CREATE TABLE IF NOT EXISTS ids_state_value_registry (
  state_namespace text NOT NULL,
  state_value text NOT NULL,
  introduced_version text NOT NULL,
  retired_version text,
  is_active boolean NOT NULL DEFAULT true,
  owner_label_zh text NOT NULL,
  owner_description_zh text,
  created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (state_namespace, state_value),
  CONSTRAINT chk_ids_state_value_registry_identity CHECK (
    btrim(state_namespace) <> ''
    AND btrim(state_value) <> ''
    AND btrim(introduced_version) <> ''
    AND btrim(owner_label_zh) <> ''
  ),
  CONSTRAINT chk_ids_state_value_registry_version CHECK (
    retired_version IS NULL OR btrim(retired_version) <> ''
  )
);

CREATE INDEX IF NOT EXISTS idx_ids_state_value_registry_active
  ON ids_state_value_registry (state_namespace, is_active, state_value);

DO $ids_quality_constraint$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_ids_chunks_document_ordinal'
      AND conrelid = 'ids_chunks'::regclass
  ) THEN
    ALTER TABLE ids_chunks
      ADD CONSTRAINT uq_ids_chunks_document_ordinal
      UNIQUE (document_id, chunk_ordinal);
  END IF;
END
$ids_quality_constraint$;

DO $ids_quality_constraint$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'chk_ids_metadata_sources_quality_v2'
      AND conrelid = 'ids_metadata_sources'::regclass
  ) THEN
    ALTER TABLE ids_metadata_sources
      ADD CONSTRAINT chk_ids_metadata_sources_quality_v2 CHECK (
        btrim(source_id) <> ''
        AND btrim(source_uri) <> ''
        AND btrim(source_boundary) <> ''
        AND btrim(storage_class) <> ''
        AND source_size_bytes >= 0
        AND payload_size_bytes >= 0
        AND payload_size_bytes <= 1048576
        AND is_raw_content_stored = false
      ) NOT VALID;
  END IF;
END
$ids_quality_constraint$;

DO $ids_quality_constraint$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'chk_ids_jobs_quality_v2'
      AND conrelid = 'ids_jobs'::regclass
  ) THEN
    ALTER TABLE ids_jobs
      ADD CONSTRAINT chk_ids_jobs_quality_v2 CHECK (
        btrim(job_id) <> ''
        AND btrim(job_type) <> ''
        AND btrim(job_state) <> ''
        AND retry_count >= 0
        AND max_retries >= 0
        AND retry_count <= max_retries
        AND connection_pool_size >= 1
        AND connection_pool_size <= 10
        AND payload_size_bytes >= 0
        AND payload_size_bytes <= 1048576
      ) NOT VALID;
  END IF;
END
$ids_quality_constraint$;

DO $ids_quality_constraint$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'chk_ids_documents_quality_v2'
      AND conrelid = 'ids_documents'::regclass
  ) THEN
    ALTER TABLE ids_documents
      ADD CONSTRAINT chk_ids_documents_quality_v2 CHECK (
        btrim(document_id) <> ''
        AND btrim(source_id) <> ''
        AND btrim(source_uri) <> ''
        AND btrim(parser_state) <> ''
        AND payload_size_bytes >= 0
        AND payload_size_bytes <= 1048576
      ) NOT VALID;
  END IF;
END
$ids_quality_constraint$;

DO $ids_quality_constraint$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'chk_ids_chunks_quality_v2'
      AND conrelid = 'ids_chunks'::regclass
  ) THEN
    ALTER TABLE ids_chunks
      ADD CONSTRAINT chk_ids_chunks_quality_v2 CHECK (
        btrim(chunk_id) <> ''
        AND btrim(document_id) <> ''
        AND btrim(parser_state) <> ''
        AND chunk_ordinal >= 0
        AND payload_size_bytes >= 0
        AND payload_size_bytes <= 1048576
        AND (
          (byte_start IS NULL AND byte_end IS NULL)
          OR (
            byte_start IS NOT NULL
            AND byte_end IS NOT NULL
            AND byte_start >= 0
            AND byte_end >= byte_start
          )
        )
      ) NOT VALID;
  END IF;
END
$ids_quality_constraint$;

DO $ids_quality_constraint$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'chk_ids_evidence_records_quality_v2'
      AND conrelid = 'ids_evidence_records'::regclass
  ) THEN
    ALTER TABLE ids_evidence_records
      ADD CONSTRAINT chk_ids_evidence_records_quality_v2 CHECK (
        btrim(evidence_id) <> ''
        AND btrim(evidence_kind) <> ''
        AND btrim(fact_level) <> ''
        AND btrim(source_ref) <> ''
        AND btrim(validation_state) <> ''
      ) NOT VALID;
  END IF;
END
$ids_quality_constraint$;

DO $ids_quality_constraint$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'chk_ids_audit_events_quality_v2'
      AND conrelid = 'ids_audit_events'::regclass
  ) THEN
    ALTER TABLE ids_audit_events
      ADD CONSTRAINT chk_ids_audit_events_quality_v2 CHECK (
        btrim(audit_id) <> ''
        AND btrim(actor_role) <> ''
        AND btrim(action_type) <> ''
        AND btrim(object_ref) <> ''
        AND btrim(decision_state) <> ''
      ) NOT VALID;
  END IF;
END
$ids_quality_constraint$;

DO $ids_quality_constraint$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'chk_ids_index_versions_quality_v2'
      AND conrelid = 'ids_index_versions'::regclass
  ) THEN
    ALTER TABLE ids_index_versions
      ADD CONSTRAINT chk_ids_index_versions_quality_v2 CHECK (
        btrim(index_id) <> ''
        AND btrim(index_version) <> ''
        AND btrim(index_state) <> ''
        AND btrim(coverage_ref) <> ''
        AND btrim(hot_index_pointer_ref) <> ''
        AND payload_size_bytes >= 0
        AND payload_size_bytes <= 1048576
      ) NOT VALID;
  END IF;
END
$ids_quality_constraint$;

DO $ids_quality_constraint$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'chk_ids_schema_migrations_quality_v2'
      AND conrelid = 'ids_schema_migrations'::regclass
  ) THEN
    ALTER TABLE ids_schema_migrations
      ADD CONSTRAINT chk_ids_schema_migrations_quality_v2 CHECK (
        btrim(migration_id) <> ''
        AND btrim(checksum_sha256) <> ''
        AND btrim(rollback_sql_ref) <> ''
        AND btrim(recovery_checkpoint_ref) <> ''
        AND dry_run_required = true
        AND rollback_required = true
      ) NOT VALID;
  END IF;
END
$ids_quality_constraint$;

ALTER TABLE ids_metadata_sources
  VALIDATE CONSTRAINT chk_ids_metadata_sources_quality_v2;
ALTER TABLE ids_jobs
  VALIDATE CONSTRAINT chk_ids_jobs_quality_v2;
ALTER TABLE ids_documents
  VALIDATE CONSTRAINT chk_ids_documents_quality_v2;
ALTER TABLE ids_chunks
  VALIDATE CONSTRAINT chk_ids_chunks_quality_v2;
ALTER TABLE ids_evidence_records
  VALIDATE CONSTRAINT chk_ids_evidence_records_quality_v2;
ALTER TABLE ids_audit_events
  VALIDATE CONSTRAINT chk_ids_audit_events_quality_v2;
ALTER TABLE ids_index_versions
  VALIDATE CONSTRAINT chk_ids_index_versions_quality_v2;
ALTER TABLE ids_schema_migrations
  VALIDATE CONSTRAINT chk_ids_schema_migrations_quality_v2;

-- migrate:down

ALTER TABLE ids_schema_migrations
  DROP CONSTRAINT IF EXISTS chk_ids_schema_migrations_quality_v2;
ALTER TABLE ids_index_versions
  DROP CONSTRAINT IF EXISTS chk_ids_index_versions_quality_v2;
ALTER TABLE ids_audit_events
  DROP CONSTRAINT IF EXISTS chk_ids_audit_events_quality_v2;
ALTER TABLE ids_evidence_records
  DROP CONSTRAINT IF EXISTS chk_ids_evidence_records_quality_v2;
ALTER TABLE ids_chunks
  DROP CONSTRAINT IF EXISTS chk_ids_chunks_quality_v2;
ALTER TABLE ids_documents
  DROP CONSTRAINT IF EXISTS chk_ids_documents_quality_v2;
ALTER TABLE ids_jobs
  DROP CONSTRAINT IF EXISTS chk_ids_jobs_quality_v2;
ALTER TABLE ids_metadata_sources
  DROP CONSTRAINT IF EXISTS chk_ids_metadata_sources_quality_v2;
ALTER TABLE ids_chunks
  DROP CONSTRAINT IF EXISTS uq_ids_chunks_document_ordinal;

DO $ids_quality_rollback_gate$
DECLARE
  registry_has_rows boolean := false;
BEGIN
  IF to_regclass('public.ids_state_value_registry') IS NOT NULL THEN
    EXECUTE 'SELECT EXISTS (SELECT 1 FROM ids_state_value_registry)'
      INTO registry_has_rows;
    IF registry_has_rows THEN
      RAISE EXCEPTION 'STAGE-036 rollback blocked: ids_state_value_registry is not empty';
    END IF;
  END IF;
END
$ids_quality_rollback_gate$;

DROP TABLE IF EXISTS ids_state_value_registry;
