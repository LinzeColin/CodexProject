-- Transactional model activation and atomic refresh state.
-- Acceptance IDs: A204,A205

CREATE UNIQUE INDEX scoring_profile_versions_one_global_active_idx
  ON scoring_profile_versions(active)
  WHERE active = true;

CREATE TABLE active_analysis_contexts (
  context_key text PRIMARY KEY CHECK (context_key = 'global'),
  active_scoring_profile_version_id uuid NOT NULL
    REFERENCES scoring_profile_versions(id),
  active_data_snapshot_id uuid REFERENCES data_snapshots(id),
  active_scoring_run_id uuid REFERENCES scoring_runs(id),
  refresh_token uuid NOT NULL DEFAULT gen_random_uuid(),
  refresh_generation integer NOT NULL DEFAULT 1 CHECK (refresh_generation > 0),
  status text NOT NULL CHECK (status IN ('active','refreshing','failed')),
  activated_at timestamptz NOT NULL DEFAULT now(),
  activated_by text NOT NULL CHECK (activated_by IN ('local_user','system','codex')),
  affected_modules jsonb NOT NULL DEFAULT '[]'::jsonb,
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX active_analysis_context_profile_idx
  ON active_analysis_contexts(active_scoring_profile_version_id, refresh_generation DESC);
