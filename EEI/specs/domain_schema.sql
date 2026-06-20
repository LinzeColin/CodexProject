-- Logical MVP schema. Codex may adapt indexes/types while preserving invariants.
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE TYPE entity_type AS ENUM (
  'legal_entity','brand','security','fund','government_body','person','theme',
  'facility','product','business_segment','industry','contract','standard','asset'
);
CREATE TYPE epistemic_status AS ENUM (
  'reported','derived','disputed','superseded','revoked','unknown'
);
CREATE TYPE evidence_role AS ENUM ('supports','contradicts','context');
CREATE TYPE change_type AS ENUM (
  'created','updated','superseded','revoked','conflict_detected','stale','ingestion_failed'
);

CREATE TABLE entities (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  canonical_name text NOT NULL,
  entity_type entity_type NOT NULL,
  jurisdiction text,
  status text NOT NULL DEFAULT 'active',
  description text,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE entity_aliases (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  entity_id uuid NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
  alias text NOT NULL,
  alias_type text NOT NULL DEFAULT 'name',
  valid_from date,
  valid_to date,
  UNIQUE(entity_id, alias, alias_type)
);

CREATE TABLE entity_identifiers (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  entity_id uuid NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
  scheme text NOT NULL,
  value text NOT NULL,
  issuer text,
  valid_from date,
  valid_to date,
  UNIQUE(scheme, value)
);

CREATE INDEX idx_entities_canonical_name_trgm
  ON entities USING gin (canonical_name gin_trgm_ops);
CREATE INDEX idx_entity_aliases_alias_trgm
  ON entity_aliases USING gin (alias gin_trgm_ops);
CREATE INDEX idx_entity_identifiers_value_trgm
  ON entity_identifiers USING gin (value gin_trgm_ops);

CREATE TABLE sources (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  code text NOT NULL UNIQUE,
  name text NOT NULL,
  base_url text NOT NULL,
  source_tier smallint NOT NULL CHECK (source_tier BETWEEN 1 AND 5),
  expected_cadence text,
  typical_disclosure_lag text,
  terms_notes text,
  active boolean NOT NULL DEFAULT true,
  last_verified_at timestamptz
);

CREATE TABLE source_documents (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  source_id uuid NOT NULL REFERENCES sources(id),
  external_id text,
  url text NOT NULL,
  title text,
  publisher text,
  document_date timestamptz,
  observed_at timestamptz NOT NULL,
  retrieved_at timestamptz NOT NULL DEFAULT now(),
  content_hash text NOT NULL,
  media_type text,
  raw_storage_uri text,
  parser_version text,
  UNIQUE(source_id, external_id, content_hash)
);

CREATE TABLE relationships (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  subject_entity_id uuid NOT NULL REFERENCES entities(id),
  object_entity_id uuid NOT NULL REFERENCES entities(id),
  relationship_type text NOT NULL,
  relationship_family text NOT NULL,
  status epistemic_status NOT NULL,
  confidence numeric(4,3) CHECK (confidence BETWEEN 0 AND 1),
  valid_from timestamptz,
  valid_to timestamptz,
  announced_at timestamptz,
  filed_at timestamptz,
  observed_at timestamptz NOT NULL,
  percentage numeric,
  amount numeric,
  currency char(3),
  amount_kind text,
  qualifiers jsonb NOT NULL DEFAULT '{}'::jsonb,
  derivation_rule text,
  derivation_version text,
  supersedes_id uuid REFERENCES relationships(id),
  created_at timestamptz NOT NULL DEFAULT now(),
  CHECK (valid_to IS NULL OR valid_from IS NULL OR valid_to >= valid_from),
  CHECK (percentage IS NULL OR (percentage >= 0 AND percentage <= 100)),
  CHECK (
    (amount IS NULL)
    OR (currency IS NOT NULL AND amount_kind IS NOT NULL)
  )
);

CREATE TABLE relationship_evidence (
  relationship_id uuid NOT NULL REFERENCES relationships(id) ON DELETE CASCADE,
  source_document_id uuid NOT NULL REFERENCES source_documents(id),
  role evidence_role NOT NULL,
  locator text,
  support_excerpt text,
  structured_fact jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (relationship_id, source_document_id, role)
);

CREATE TABLE events (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  event_type text NOT NULL,
  title text NOT NULL,
  status epistemic_status NOT NULL,
  announced_at timestamptz,
  effective_at timestamptz,
  period_start date,
  period_end date,
  observed_at timestamptz NOT NULL,
  amount numeric,
  currency char(3),
  amount_kind text,
  description text,
  qualifiers jsonb NOT NULL DEFAULT '{}'::jsonb,
  derivation_rule text,
  derivation_version text,
  supersedes_id uuid REFERENCES events(id),
  created_at timestamptz NOT NULL DEFAULT now(),
  CHECK (period_end IS NULL OR period_start IS NULL OR period_end >= period_start),
  CHECK (
    (amount IS NULL)
    OR (currency IS NOT NULL AND amount_kind IS NOT NULL)
  )
);

CREATE TABLE event_participants (
  event_id uuid NOT NULL REFERENCES events(id) ON DELETE CASCADE,
  entity_id uuid NOT NULL REFERENCES entities(id),
  role text NOT NULL,
  direction text,
  PRIMARY KEY (event_id, entity_id, role)
);

CREATE TABLE event_evidence (
  event_id uuid NOT NULL REFERENCES events(id) ON DELETE CASCADE,
  source_document_id uuid NOT NULL REFERENCES source_documents(id),
  role evidence_role NOT NULL,
  locator text,
  support_excerpt text,
  structured_fact jsonb,
  PRIMARY KEY (event_id, source_document_id, role)
);

CREATE TABLE ingestion_runs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  source_id uuid NOT NULL REFERENCES sources(id),
  connector_version text NOT NULL,
  mode text NOT NULL,
  checkpoint jsonb,
  started_at timestamptz NOT NULL,
  finished_at timestamptz,
  status text NOT NULL,
  counts jsonb NOT NULL DEFAULT '{}'::jsonb,
  error_class text,
  error_message text
);

CREATE TABLE changes (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  change_type change_type NOT NULL,
  object_type text NOT NULL,
  object_id uuid,
  old_value jsonb,
  new_value jsonb,
  source_document_id uuid REFERENCES source_documents(id),
  ingestion_run_id uuid REFERENCES ingestion_runs(id),
  review_required boolean NOT NULL DEFAULT false,
  created_at timestamptz NOT NULL DEFAULT now()
);



-- Industry classifications are versioned and multi-label. They are navigation aids, not legal facts.
CREATE TABLE industries (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  external_id text UNIQUE,
  slug text NOT NULL UNIQUE,
  name_zh text NOT NULL,
  name_en text NOT NULL,
  parent_id uuid REFERENCES industries(id),
  kind text NOT NULL DEFAULT 'industry',
  taxonomy_version text NOT NULL,
  active boolean NOT NULL DEFAULT true,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE entity_industry_memberships (
  entity_id uuid NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
  industry_id uuid NOT NULL REFERENCES industries(id),
  role text NOT NULL CHECK (role IN ('primary','secondary','supply_chain','historical')),
  confidence numeric(4,3) CHECK (confidence BETWEEN 0 AND 1),
  valid_from timestamptz,
  valid_to timestamptz,
  evidence_required boolean NOT NULL DEFAULT true,
  PRIMARY KEY (entity_id, industry_id, role, valid_from)
);

-- Structured supply-chain qualifiers remain attached to a relationship and preserve unknowns.
CREATE TABLE supply_chain_relationship_attributes (
  relationship_id uuid PRIMARY KEY REFERENCES relationships(id) ON DELETE CASCADE,
  stage_from text,
  stage_to text,
  supplier_role text,
  buyer_role text,
  tier text CHECK (tier IN ('direct','Tier-1','Tier-2','Tier-3','unknown')),
  materiality text CHECK (materiality IN ('critical','high','medium','low','unknown')),
  concentration_value numeric,
  concentration_kind text,
  substitutability_score numeric CHECK (substitutability_score BETWEEN 0 AND 100),
  lead_time_days numeric CHECK (lead_time_days IS NULL OR lead_time_days >= 0),
  capacity_value numeric,
  capacity_unit text,
  geographic_exposure jsonb NOT NULL DEFAULT '[]'::jsonb,
  coverage numeric(5,2) CHECK (coverage BETWEEN 0 AND 100),
  last_verified_at timestamptz
);

CREATE TABLE exploration_sessions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  namespace text NOT NULL DEFAULT 'local_user',
  title text,
  current_focus_entity_id uuid REFERENCES entities(id),
  active_layers text[] NOT NULL DEFAULT ARRAY[]::text[],
  state_version text NOT NULL DEFAULT 'exploration-state-v1',
  direction text NOT NULL DEFAULT 'both' CHECK (direction IN ('both','upstream','downstream','in','out')),
  hops integer NOT NULL DEFAULT 1 CHECK (hops BETWEEN 1 AND 2),
  budget jsonb NOT NULL DEFAULT '{"max_nodes":42,"max_edges":64,"expand_nodes":12}'::jsonb,
  as_of timestamptz,
  scoring_profile_version_id uuid,
  filters jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE exploration_steps (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id uuid NOT NULL REFERENCES exploration_sessions(id) ON DELETE CASCADE,
  sequence_no integer NOT NULL CHECK (sequence_no >= 0),
  from_entity_id uuid REFERENCES entities(id),
  to_entity_id uuid NOT NULL REFERENCES entities(id),
  action text NOT NULL CHECK (action IN ('start','reroot','back','forward','restore')),
  inherited_state jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE(session_id, sequence_no)
);

CREATE TABLE watchlists (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  namespace text NOT NULL DEFAULT 'local_user',
  name text NOT NULL,
  description text,
  default_scoring_profile_version_id uuid,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE(namespace, name)
);

CREATE TABLE watchlist_items (
  watchlist_id uuid NOT NULL REFERENCES watchlists(id) ON DELETE CASCADE,
  object_type text NOT NULL CHECK (object_type IN ('entity','industry','theme','facility')),
  object_id uuid NOT NULL,
  labels text[] NOT NULL DEFAULT ARRAY[]::text[],
  note text,
  saved_state jsonb NOT NULL DEFAULT '{}'::jsonb,
  added_at timestamptz NOT NULL DEFAULT now(),
  removed_at timestamptz,
  PRIMARY KEY (watchlist_id, object_type, object_id)
);

CREATE TABLE scoring_models (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  model_key text NOT NULL,
  version integer NOT NULL CHECK (version > 0),
  name text NOT NULL,
  formula jsonb NOT NULL,
  input_schema jsonb NOT NULL,
  status text NOT NULL CHECK (status IN ('draft','active','retired')),
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE(model_key, version)
);

CREATE TABLE scoring_profiles (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  namespace text NOT NULL DEFAULT 'local_user',
  profile_key text NOT NULL,
  name text NOT NULL,
  is_system_default boolean NOT NULL DEFAULT false,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE(namespace, profile_key)
);

CREATE TABLE scoring_profile_versions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  profile_id uuid NOT NULL REFERENCES scoring_profiles(id) ON DELETE CASCADE,
  model_id uuid NOT NULL REFERENCES scoring_models(id),
  version integer NOT NULL CHECK (version > 0),
  weights jsonb NOT NULL,
  thresholds jsonb NOT NULL DEFAULT '{}'::jsonb,
  half_lives jsonb NOT NULL DEFAULT '{}'::jsonb,
  missing_value_policy text NOT NULL CHECK (missing_value_policy IN ('renormalize_available','mark_unscored','conservative_penalty')),
  reason text NOT NULL,
  active boolean NOT NULL DEFAULT false,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE(profile_id, version)
);

ALTER TABLE exploration_sessions
  ADD CONSTRAINT exploration_profile_fk
  FOREIGN KEY (scoring_profile_version_id) REFERENCES scoring_profile_versions(id);
ALTER TABLE watchlists
  ADD CONSTRAINT watchlist_profile_fk
  FOREIGN KEY (default_scoring_profile_version_id) REFERENCES scoring_profile_versions(id);

CREATE TABLE scoring_runs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  model_id uuid NOT NULL REFERENCES scoring_models(id),
  profile_version_id uuid NOT NULL REFERENCES scoring_profile_versions(id),
  data_snapshot_at timestamptz NOT NULL,
  parameters jsonb NOT NULL DEFAULT '{}'::jsonb,
  status text NOT NULL,
  started_at timestamptz NOT NULL,
  finished_at timestamptz,
  content_hash text,
  UNIQUE(model_id, profile_version_id, data_snapshot_at, content_hash)
);

CREATE TABLE score_results (
  scoring_run_id uuid NOT NULL REFERENCES scoring_runs(id) ON DELETE CASCADE,
  object_type text NOT NULL,
  object_id uuid NOT NULL,
  raw_score numeric(6,3) CHECK (raw_score BETWEEN 0 AND 100),
  evidence_quality numeric(6,3) CHECK (evidence_quality BETWEEN 0 AND 100),
  adjusted_score numeric(6,3) CHECK (adjusted_score BETWEEN 0 AND 100),
  coverage numeric(6,3) CHECK (coverage BETWEEN 0 AND 100),
  contributions jsonb NOT NULL,
  missing_inputs jsonb NOT NULL DEFAULT '[]'::jsonb,
  PRIMARY KEY (scoring_run_id, object_type, object_id)
);

CREATE TABLE operation_logs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  occurred_at timestamptz NOT NULL DEFAULT now(),
  actor text NOT NULL CHECK (actor IN ('local_user','system','codex')),
  action_type text NOT NULL,
  object_type text NOT NULL,
  object_id uuid,
  old_value jsonb,
  new_value jsonb,
  diff jsonb,
  reason text,
  request_id text,
  session_id uuid REFERENCES exploration_sessions(id),
  model_version text,
  profile_version text,
  result_status text NOT NULL,
  error text
);

CREATE TABLE calibration_runs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  scheduled_for timestamptz,
  cadence_days integer NOT NULL DEFAULT 14 CHECK (cadence_days = 14),
  data_snapshot_at timestamptz NOT NULL,
  profile_version_id uuid REFERENCES scoring_profile_versions(id),
  status text NOT NULL CHECK (status IN ('scheduled','running','passed','warning','failed','cancelled')),
  metrics jsonb NOT NULL DEFAULT '{}'::jsonb,
  drift_report jsonb NOT NULL DEFAULT '{}'::jsonb,
  proposal jsonb,
  proposal_status text CHECK (proposal_status IN ('none','proposed','accepted','rejected')),
  started_at timestamptz,
  finished_at timestamptz,
  error text
);

CREATE TABLE relationship_families (
  family_key text PRIMARY KEY,
  family_id text NOT NULL UNIQUE,
  name_zh text NOT NULL,
  slug text NOT NULL UNIQUE,
  default_graph_zone text NOT NULL,
  definition text NOT NULL,
  relationship_type_count integer NOT NULL CHECK (relationship_type_count >= 0),
  default_evidence_threshold text NOT NULL,
  default_visual_encoding text NOT NULL,
  recursive_pivot boolean NOT NULL DEFAULT false,
  loaded_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE relationship_type_catalog (
  relationship_type text PRIMARY KEY,
  family_key text NOT NULL REFERENCES relationship_families(family_key),
  direction text NOT NULL CHECK (direction IN ('directed','undirected','bidirectional')),
  amount_allowed boolean NOT NULL,
  percentage_allowed boolean NOT NULL,
  definition text NOT NULL,
  loaded_at timestamptz NOT NULL DEFAULT now()
);

ALTER TABLE relationships
  ADD CONSTRAINT relationships_family_fk
  FOREIGN KEY (relationship_family) REFERENCES relationship_families(family_key);

ALTER TABLE relationships
  ADD CONSTRAINT relationships_type_fk
  FOREIGN KEY (relationship_type) REFERENCES relationship_type_catalog(relationship_type);

CREATE TABLE supply_chain_stages (
  stage_id text PRIMARY KEY,
  stage_order integer NOT NULL UNIQUE,
  slug text NOT NULL UNIQUE,
  name_zh text NOT NULL,
  name_en text NOT NULL,
  default_direction text NOT NULL
    CHECK (default_direction IN ('upstream','downstream','midstream','crosscutting')),
  examples text,
  loaded_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE company_research_universe (
  research_id text PRIMARY KEY,
  tier text NOT NULL CHECK (tier IN ('P0','P1','P2','X')),
  canonical_name text NOT NULL,
  power_system text NOT NULL,
  initial_form text NOT NULL,
  research_focus text NOT NULL,
  verification_status text NOT NULL,
  data_mode text NOT NULL DEFAULT 'research_target_not_verified_fact',
  source_path text NOT NULL,
  entity_id uuid REFERENCES entities(id),
  loaded_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE seed_runs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  seed_name text NOT NULL,
  source_path text NOT NULL,
  source_hash text NOT NULL,
  row_count integer NOT NULL CHECK (row_count >= 0),
  status text NOT NULL CHECK (status IN ('loaded','failed')),
  loaded_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE(source_path, source_hash)
);

CREATE TABLE fixture_datasets (
  dataset_key text PRIMARY KEY,
  description text NOT NULL,
  source_hash text NOT NULL,
  synthetic boolean NOT NULL DEFAULT true,
  loaded_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE fixture_entity_notices (
  entity_id uuid PRIMARY KEY REFERENCES entities(id) ON DELETE CASCADE,
  dataset_key text NOT NULL REFERENCES fixture_datasets(dataset_key),
  fixture_notice text NOT NULL,
  synthetic boolean NOT NULL DEFAULT true,
  loaded_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE fixture_relationship_notices (
  relationship_id uuid PRIMARY KEY REFERENCES relationships(id) ON DELETE CASCADE,
  dataset_key text NOT NULL REFERENCES fixture_datasets(dataset_key),
  fixture_notice text NOT NULL,
  synthetic boolean NOT NULL DEFAULT true,
  loaded_at timestamptz NOT NULL DEFAULT now()
);

-- Production snapshots and immutable fact versions keep facts, evidence, time validity,
-- record mode and version history separate for rollback-safe publication.
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

-- Curated official ingestion audit layers preserve raw source anchors, parser
-- version, entity-resolution confidence, review state, evidence and counter-evidence.
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

CREATE INDEX exploration_steps_session_idx ON exploration_steps(session_id, sequence_no);
CREATE INDEX operation_logs_object_idx ON operation_logs(object_type, object_id, occurred_at DESC);
CREATE INDEX calibration_runs_time_idx ON calibration_runs(scheduled_for DESC, status);
CREATE INDEX score_results_object_idx ON score_results(object_type, object_id, adjusted_score DESC);
CREATE INDEX company_research_universe_tier_idx ON company_research_universe(tier, canonical_name);
CREATE INDEX relationship_type_family_idx ON relationship_type_catalog(family_key, relationship_type);
CREATE INDEX fixture_relationship_dataset_idx ON fixture_relationship_notices(dataset_key, relationship_id);

CREATE INDEX relationships_subject_idx
  ON relationships(subject_entity_id, relationship_family, valid_from, valid_to);
CREATE INDEX relationships_object_idx
  ON relationships(object_entity_id, relationship_family, valid_from, valid_to);
CREATE INDEX events_time_idx
  ON events(COALESCE(effective_at, announced_at), event_type);
CREATE INDEX documents_observed_idx
  ON source_documents(source_id, observed_at DESC);

-- Public API/service invariant:
-- relationship/event is publishable only when at least one evidence row exists.
-- Implement as service validation plus deferred data-quality check.
