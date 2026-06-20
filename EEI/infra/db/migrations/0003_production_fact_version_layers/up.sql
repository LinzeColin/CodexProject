-- Add production snapshot and fact-version layers.
-- Acceptance IDs: A201

CREATE TABLE data_snapshots (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  snapshot_key text NOT NULL UNIQUE,
  scope text NOT NULL,
  record_mode text NOT NULL
    CHECK (record_mode IN ('fixture','curated_official_fixture','dry_run','live')),
  status text NOT NULL
    CHECK (status IN ('building','active','superseded','failed')),
  built_from_ingestion_run_id uuid REFERENCES ingestion_runs(id),
  source_hash text NOT NULL,
  as_of timestamptz NOT NULL,
  activated_at timestamptz,
  supersedes_snapshot_id uuid REFERENCES data_snapshots(id),
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  CHECK (
    (status = 'active' AND activated_at IS NOT NULL)
    OR (status <> 'active')
  )
);

CREATE UNIQUE INDEX data_snapshots_one_active_per_scope_mode_idx
  ON data_snapshots(scope, record_mode)
  WHERE status = 'active';

CREATE TABLE fact_versions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  snapshot_id uuid NOT NULL REFERENCES data_snapshots(id) ON DELETE CASCADE,
  object_type text NOT NULL
    CHECK (
      object_type IN (
        'entity','relationship','event','industry','source_document','score_result'
      )
    ),
  object_id uuid NOT NULL,
  version_no integer NOT NULL CHECK (version_no > 0),
  fact_status epistemic_status NOT NULL,
  record_mode text NOT NULL
    CHECK (record_mode IN ('fixture','curated_official_fixture','dry_run','live')),
  valid_from timestamptz,
  valid_to timestamptz,
  observed_at timestamptz NOT NULL,
  source_document_id uuid REFERENCES source_documents(id),
  ingestion_run_id uuid REFERENCES ingestion_runs(id),
  parser_version text,
  payload_hash text NOT NULL,
  payload jsonb NOT NULL,
  previous_fact_version_id uuid REFERENCES fact_versions(id),
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE(snapshot_id, object_type, object_id, version_no),
  CHECK (valid_to IS NULL OR valid_from IS NULL OR valid_to >= valid_from)
);

CREATE INDEX fact_versions_object_idx
  ON fact_versions(object_type, object_id, snapshot_id, version_no DESC);
CREATE INDEX fact_versions_snapshot_status_idx
  ON fact_versions(snapshot_id, fact_status, record_mode);
CREATE INDEX fact_versions_time_idx
  ON fact_versions(object_type, valid_from, valid_to, observed_at);

CREATE TABLE fact_version_evidence (
  fact_version_id uuid NOT NULL REFERENCES fact_versions(id) ON DELETE CASCADE,
  source_document_id uuid NOT NULL REFERENCES source_documents(id),
  role evidence_role NOT NULL,
  locator text,
  support_excerpt text,
  structured_fact jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (fact_version_id, source_document_id, role)
);
