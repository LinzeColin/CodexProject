-- Server-side saved views with optimistic conflict control and recovery.
-- Acceptance IDs: A207

CREATE TABLE saved_views (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  namespace text NOT NULL DEFAULT 'local_user',
  workspace_key text NOT NULL DEFAULT 'default',
  name text NOT NULL,
  description text,
  state jsonb NOT NULL,
  schema_version text NOT NULL DEFAULT 'saved-view-v1',
  current_version integer NOT NULL DEFAULT 1 CHECK (current_version >= 1),
  active boolean NOT NULL DEFAULT true,
  created_by text NOT NULL DEFAULT 'local_user',
  updated_by text NOT NULL DEFAULT 'local_user',
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  last_restored_at timestamptz,
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  UNIQUE (namespace, workspace_key, name)
);

CREATE INDEX saved_views_namespace_updated_idx
  ON saved_views(namespace, workspace_key, updated_at DESC);

CREATE INDEX saved_views_active_idx
  ON saved_views(namespace, workspace_key, active, updated_at DESC)
  WHERE active = true;

CREATE TABLE saved_view_versions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  saved_view_id uuid NOT NULL REFERENCES saved_views(id) ON DELETE CASCADE,
  version_no integer NOT NULL CHECK (version_no >= 1),
  state jsonb NOT NULL,
  schema_version text NOT NULL DEFAULT 'saved-view-v1',
  action_type text NOT NULL CHECK (action_type IN ('create','update','restore')),
  restored_from_version_no integer CHECK (restored_from_version_no IS NULL OR restored_from_version_no >= 1),
  change_note text,
  created_by text NOT NULL DEFAULT 'local_user',
  created_at timestamptz NOT NULL DEFAULT now(),
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  UNIQUE (saved_view_id, version_no)
);

CREATE INDEX saved_view_versions_view_idx
  ON saved_view_versions(saved_view_id, version_no DESC);
