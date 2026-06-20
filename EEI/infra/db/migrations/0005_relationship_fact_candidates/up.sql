-- Add reviewed relationship fact candidate and manual review queue layers.
-- Acceptance IDs: A202

CREATE TABLE relationship_fact_candidates (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  candidate_key text NOT NULL UNIQUE,
  subject_resolution_id uuid NOT NULL REFERENCES entity_resolution_candidates(id),
  object_resolution_id uuid NOT NULL REFERENCES entity_resolution_candidates(id),
  relationship_type text NOT NULL REFERENCES relationship_type_catalog(relationship_type),
  relationship_family text NOT NULL REFERENCES relationship_families(family_key),
  record_mode text NOT NULL
    CHECK (record_mode IN ('fixture','curated_official_fixture','dry_run','live')),
  fact_status epistemic_status NOT NULL DEFAULT 'reported',
  publication_status text NOT NULL
    CHECK (
      publication_status IN (
        'candidate','ready_for_review','approved_for_publication','rejected','published'
      )
    ),
  confidence numeric(4,3) NOT NULL CHECK (confidence BETWEEN 0 AND 1),
  independent_source_count integer NOT NULL DEFAULT 0 CHECK (independent_source_count >= 0),
  source_threshold_met boolean NOT NULL DEFAULT false,
  review_status text NOT NULL
    CHECK (review_status IN ('unreviewed','machine_verified','human_verified','disputed')),
  parser_version text NOT NULL,
  structured_fact jsonb NOT NULL DEFAULT '{}'::jsonb,
  counter_evidence jsonb NOT NULL DEFAULT '[]'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CHECK (jsonb_typeof(counter_evidence) = 'array'),
  CHECK (
    publication_status <> 'published'
    OR (source_threshold_met = true AND review_status = 'human_verified')
  ),
  UNIQUE(subject_resolution_id, object_resolution_id, relationship_type, parser_version)
);

CREATE INDEX relationship_fact_candidates_type_idx
  ON relationship_fact_candidates(relationship_family, relationship_type, publication_status);
CREATE INDEX relationship_fact_candidates_review_idx
  ON relationship_fact_candidates(review_status, source_threshold_met, confidence DESC);

CREATE TABLE relationship_fact_candidate_evidence (
  candidate_id uuid NOT NULL REFERENCES relationship_fact_candidates(id) ON DELETE CASCADE,
  ingestion_evidence_chain_id uuid NOT NULL REFERENCES ingestion_evidence_chain(id),
  source_document_id uuid NOT NULL REFERENCES source_documents(id),
  role evidence_role NOT NULL,
  locator text NOT NULL,
  support_excerpt text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (candidate_id, ingestion_evidence_chain_id, role)
);

CREATE INDEX relationship_fact_candidate_evidence_source_idx
  ON relationship_fact_candidate_evidence(source_document_id, role);

CREATE TABLE manual_review_queue (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  queue_key text NOT NULL UNIQUE,
  object_type text NOT NULL
    CHECK (
      object_type IN (
        'relationship_fact_candidate','entity_resolution_candidate','raw_source_snapshot'
      )
    ),
  object_id uuid NOT NULL,
  reason text NOT NULL,
  priority text NOT NULL CHECK (priority IN ('P0','P1','P2')),
  status text NOT NULL CHECK (status IN ('open','resolved','rejected')),
  requested_by text NOT NULL DEFAULT 'system',
  reviewer text,
  decision text,
  created_at timestamptz NOT NULL DEFAULT now(),
  resolved_at timestamptz,
  CHECK (
    (status = 'open' AND resolved_at IS NULL)
    OR (status <> 'open' AND resolved_at IS NOT NULL)
  )
);

CREATE INDEX manual_review_queue_status_idx
  ON manual_review_queue(status, priority, created_at);
