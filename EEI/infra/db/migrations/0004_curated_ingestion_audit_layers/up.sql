-- Add curated official ingestion audit layers.
-- Acceptance IDs: A202

CREATE TABLE raw_source_snapshots (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  ingestion_run_id uuid NOT NULL REFERENCES ingestion_runs(id) ON DELETE CASCADE,
  source_document_id uuid NOT NULL REFERENCES source_documents(id) ON DELETE CASCADE,
  anchor_id text NOT NULL,
  source_url text NOT NULL,
  source_date timestamptz,
  publisher text NOT NULL,
  title text NOT NULL,
  evidence_scope text NOT NULL,
  record_mode text NOT NULL
    CHECK (record_mode IN ('fixture','curated_official_fixture','dry_run','live')),
  validation_status text NOT NULL,
  parser_version text NOT NULL,
  content_hash text NOT NULL,
  raw_payload jsonb NOT NULL,
  retrieved_at timestamptz NOT NULL DEFAULT now(),
  review_status text NOT NULL
    CHECK (review_status IN ('unreviewed','machine_verified','human_verified','disputed')),
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE(anchor_id, content_hash)
);

CREATE INDEX raw_source_snapshots_mode_time_idx
  ON raw_source_snapshots(record_mode, retrieved_at DESC);
CREATE INDEX raw_source_snapshots_document_idx
  ON raw_source_snapshots(source_document_id);

CREATE TABLE entity_resolution_candidates (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  raw_snapshot_id uuid NOT NULL REFERENCES raw_source_snapshots(id) ON DELETE CASCADE,
  candidate_name text NOT NULL,
  normalized_name text NOT NULL,
  matched_entity_id uuid REFERENCES entities(id),
  matched_research_id text REFERENCES company_research_universe(research_id),
  match_method text NOT NULL
    CHECK (
      match_method IN (
        'anchor_subject',
        'canonical_exact',
        'alias_exact',
        'official_named_context',
        'stage_keyword',
        'unmatched_context'
      )
    ),
  confidence numeric(4,3) NOT NULL CHECK (confidence BETWEEN 0 AND 1),
  decision_reason text NOT NULL,
  review_status text NOT NULL
    CHECK (review_status IN ('unreviewed','machine_verified','human_verified','disputed')),
  parser_version text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE(raw_snapshot_id, candidate_name)
);

CREATE INDEX entity_resolution_candidates_snapshot_idx
  ON entity_resolution_candidates(raw_snapshot_id, confidence DESC);
CREATE INDEX entity_resolution_candidates_entity_idx
  ON entity_resolution_candidates(matched_entity_id)
  WHERE matched_entity_id IS NOT NULL;
CREATE INDEX entity_resolution_candidates_research_idx
  ON entity_resolution_candidates(matched_research_id)
  WHERE matched_research_id IS NOT NULL;

CREATE TABLE ingestion_evidence_chain (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  raw_snapshot_id uuid NOT NULL REFERENCES raw_source_snapshots(id) ON DELETE CASCADE,
  source_document_id uuid NOT NULL REFERENCES source_documents(id),
  subject_resolution_id uuid REFERENCES entity_resolution_candidates(id),
  object_resolution_id uuid REFERENCES entity_resolution_candidates(id),
  relationship_type text REFERENCES relationship_type_catalog(relationship_type),
  relationship_family text REFERENCES relationship_families(family_key),
  evidence_role evidence_role NOT NULL,
  locator text NOT NULL,
  support_excerpt text NOT NULL,
  structured_fact jsonb NOT NULL DEFAULT '{}'::jsonb,
  counter_evidence jsonb NOT NULL DEFAULT '[]'::jsonb,
  parser_version text NOT NULL,
  confidence numeric(4,3) NOT NULL CHECK (confidence BETWEEN 0 AND 1),
  review_status text NOT NULL
    CHECK (review_status IN ('unreviewed','machine_verified','human_verified','disputed')),
  created_at timestamptz NOT NULL DEFAULT now(),
  CHECK (jsonb_typeof(counter_evidence) = 'array'),
  UNIQUE(raw_snapshot_id, source_document_id, evidence_role, locator, parser_version)
);

CREATE INDEX ingestion_evidence_chain_snapshot_idx
  ON ingestion_evidence_chain(raw_snapshot_id, evidence_role);
CREATE INDEX ingestion_evidence_chain_source_document_idx
  ON ingestion_evidence_chain(source_document_id);
