-- ADP-S2-P02-T025 DocumentVersion 版本链迁移（append-only；不覆盖历史）
-- schema_version: adp.document_version.v0_1
CREATE TABLE IF NOT EXISTS cn_documents (
  canonical_id TEXT PRIMARY KEY,
  title_norm   TEXT,
  sources_json TEXT NOT NULL DEFAULT '[]',
  current_version_no INTEGER NOT NULL DEFAULT 0,
  created_at   TEXT,
  first_seen_at TEXT
);
CREATE TABLE IF NOT EXISTS cn_document_versions (
  version_id    TEXT PRIMARY KEY,               -- canonical_id + '#' + version_no
  canonical_id  TEXT NOT NULL,                  -- -> cn_documents.canonical_id
  version_no    INTEGER NOT NULL,               -- 1,2,3... append-only
  content_hash  TEXT NOT NULL,                  -- sha256 of the substantive content
  status        TEXT,                           -- e.g. active/superseded/withdrawn
  doc_date      TEXT,                           -- content date (may change across versions)
  artifact_keys_json TEXT NOT NULL DEFAULT '[]',-- R2 object keys preserved per version
  created_at    TEXT,
  UNIQUE(canonical_id, version_no)
);
CREATE INDEX IF NOT EXISTS idx_docver_canonical ON cn_document_versions(canonical_id);
CREATE INDEX IF NOT EXISTS idx_docver_contenthash ON cn_document_versions(content_hash);
CREATE INDEX IF NOT EXISTS idx_docver_status ON cn_document_versions(status);
INSERT OR IGNORE INTO cn_meta(key,value) VALUES('document_version_schema','adp.document_version.v0_1');
