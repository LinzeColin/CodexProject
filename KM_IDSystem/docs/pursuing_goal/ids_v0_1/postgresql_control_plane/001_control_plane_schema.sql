-- IDS v0.1 STAGE-030 PostgreSQL control-plane schema contract.
-- Task: IDS-V0_1-STAGE030-P2
-- Migration id: ids_stage030_001_control_plane
-- connection_url_ref: ENV:IDS_POSTGRES_DSN
-- Raw metadata root is path-only: /Users/linzezhang/Downloads/IDS_MetaData
-- NO_RAW_DB_CONTENT: this schema stores control plane, state, refs, and hot index metadata only.
-- Dry-run command, apply command, and rollback command are recorded in control_plane_schema_index.json.

-- migrate:up

CREATE TABLE IF NOT EXISTS ids_schema_migrations (
  migration_id text PRIMARY KEY,
  checksum_sha256 text NOT NULL,
  dry_run_required boolean NOT NULL DEFAULT true,
  rollback_required boolean NOT NULL DEFAULT true,
  destructive boolean NOT NULL DEFAULT false,
  applied_at timestamptz,
  rollback_sql_ref text NOT NULL,
  recovery_checkpoint_ref text NOT NULL
);

CREATE TABLE IF NOT EXISTS ids_metadata_sources (
  source_id text PRIMARY KEY,
  source_uri text NOT NULL,
  source_boundary text NOT NULL,
  source_size_bytes bigint NOT NULL DEFAULT 0,
  storage_class text NOT NULL,
  is_raw_content_stored boolean NOT NULL DEFAULT false,
  payload_size_bytes integer NOT NULL DEFAULT 0,
  created_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT chk_source_size_nonnegative CHECK (source_size_bytes >= 0),
  CONSTRAINT chk_payload_size_bytes CHECK (payload_size_bytes <= 1048576),
  CONSTRAINT chk_no_raw_content_stored CHECK (is_raw_content_stored = false),
  CONSTRAINT chk_source_storage_class CHECK (
    storage_class IN ('CONTROL_PLANE_REF', 'STATUS', 'HOT_INDEX_REF')
  )
);

CREATE TABLE IF NOT EXISTS ids_jobs (
  job_id text PRIMARY KEY,
  job_type text NOT NULL,
  job_state text NOT NULL,
  parent_job_id text REFERENCES ids_jobs(job_id),
  retry_count integer NOT NULL DEFAULT 0,
  max_retries integer NOT NULL DEFAULT 3,
  connection_pool_size smallint NOT NULL DEFAULT 5,
  payload_size_bytes integer NOT NULL DEFAULT 0,
  stop_reason text,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT chk_retry_count CHECK (retry_count >= 0 AND retry_count <= max_retries),
  CONSTRAINT chk_connection_pool_size CHECK (connection_pool_size >= 1 AND connection_pool_size <= 10),
  CONSTRAINT chk_jobs_payload_size CHECK (payload_size_bytes <= 1048576)
);

CREATE TABLE IF NOT EXISTS ids_documents (
  document_id text PRIMARY KEY,
  source_id text NOT NULL REFERENCES ids_metadata_sources(source_id),
  source_uri text NOT NULL,
  parser_state text NOT NULL,
  evidence_ref text,
  report_ref text,
  lineage_ref text,
  payload_size_bytes integer NOT NULL DEFAULT 0,
  created_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT chk_documents_payload_size CHECK (payload_size_bytes <= 1048576)
);

CREATE TABLE IF NOT EXISTS ids_chunks (
  chunk_id text PRIMARY KEY,
  document_id text NOT NULL REFERENCES ids_documents(document_id),
  chunk_ordinal integer NOT NULL,
  parser_state text NOT NULL,
  byte_start bigint,
  byte_end bigint,
  evidence_ref text,
  payload_size_bytes integer NOT NULL DEFAULT 0,
  CONSTRAINT chk_chunk_ordinal CHECK (chunk_ordinal >= 0),
  CONSTRAINT chk_chunk_offsets CHECK (byte_start IS NULL OR byte_end IS NULL OR byte_end >= byte_start),
  CONSTRAINT chk_chunks_payload_size CHECK (payload_size_bytes <= 1048576)
);

CREATE TABLE IF NOT EXISTS ids_evidence_records (
  evidence_id text PRIMARY KEY,
  evidence_kind text NOT NULL,
  fact_level text NOT NULL,
  source_ref text NOT NULL,
  validation_state text NOT NULL,
  audit_ref text,
  created_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT chk_fact_level CHECK (fact_level IN ('VERIFIED', 'INFERRED', 'UNKNOWN'))
);

CREATE TABLE IF NOT EXISTS ids_audit_events (
  audit_id text PRIMARY KEY,
  actor_role text NOT NULL,
  action_type text NOT NULL,
  object_ref text NOT NULL,
  decision_state text NOT NULL,
  stop_reason text,
  occurred_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS ids_index_versions (
  index_id text NOT NULL,
  index_version text NOT NULL,
  index_state text NOT NULL,
  coverage_ref text NOT NULL,
  rollback_ref text,
  hot_index_pointer_ref text NOT NULL,
  payload_size_bytes integer NOT NULL DEFAULT 0,
  created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (index_id, index_version),
  CONSTRAINT chk_index_state CHECK (index_state IN ('DRAFT', 'READY', 'BLOCKED', 'ROLLBACK_READY')),
  CONSTRAINT chk_index_payload_size CHECK (payload_size_bytes <= 1048576)
);

-- migrate:down

DROP TABLE IF EXISTS ids_index_versions;
DROP TABLE IF EXISTS ids_audit_events;
DROP TABLE IF EXISTS ids_evidence_records;
DROP TABLE IF EXISTS ids_chunks;
DROP TABLE IF EXISTS ids_documents;
DROP TABLE IF EXISTS ids_jobs;
DROP TABLE IF EXISTS ids_metadata_sources;
DROP TABLE IF EXISTS ids_schema_migrations;
