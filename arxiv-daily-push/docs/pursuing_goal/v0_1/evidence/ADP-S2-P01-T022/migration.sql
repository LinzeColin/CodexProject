-- ADP-S2-P01-T022 migration: cn_artifacts (R2 dual-write ledger; object_key PK => idempotent)
CREATE TABLE IF NOT EXISTS cn_artifacts (
  object_key TEXT PRIMARY KEY, sha256 TEXT NOT NULL, source_id TEXT NOT NULL,
  url TEXT, mime TEXT, content_length INTEGER, compression TEXT,
  content_version TEXT DEFAULT 'v1', created_at TEXT
);
