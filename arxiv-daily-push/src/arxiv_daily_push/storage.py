"""Local SQLite storage for the Review8 Stage 1 document/event model."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Union

from .contracts import stable_content_hash, validate_source_item


STORAGE_MODEL_ID = "adp-sqlite-data-model-v1"
STORAGE_SCHEMA_VERSION = 1
STORAGE_DEFAULT_DB_FILENAME = "adp.sqlite3"
STORAGE_JOURNAL_MODE = "wal"
STORAGE_FTS5_REQUIRED = True
STORAGE_ROLLBACK_TARGET_VERSION = 0
STORAGE_RELATION_TYPES = (
    "VERSION_OF",
    "REPLACES",
    "SUPERSEDES",
    "AMENDS",
    "REPEALS",
    "CORRECTS",
    "WITHDRAWS",
    "RETRACTS",
    "PUBLISHED_AS",
    "CITES",
    "SUPPORTS",
    "CONTRADICTS",
    "FUNDED_BY",
    "ASSOCIATED_TRIAL",
    "ASSOCIATED_PATENT",
    "COMMERCIALIZED_BY",
    "IMPLEMENTS",
    "INTERPRETS",
    "ENFORCES",
    "RESPONDS_TO",
    "AFFECTS_ENTITY",
    "AFFECTS_SECTOR",
    "AFFECTS_ASSET",
    "SAME_TOPIC_AS",
    "DERIVED_FROM",
)
STORAGE_TIME_FIELDS = (
    "published_at",
    "updated_at",
    "effective_at",
    "expires_at",
    "deadline_at",
    "retrieved_at",
    "observed_at",
    "known_at",
    "as_of_at",
)
STORAGE_OBJECT_TABLES = (
    "source_definitions",
    "fetch_runs",
    "raw_records",
    "canonical_documents",
    "document_versions",
    "events",
    "entities",
    "relations",
    "theme_clusters",
    "claims",
    "evidence_bindings",
    "score_snapshots",
    "queue_entries",
    "report_artifacts",
    "email_artifacts",
    "media_artifacts",
    "run_manifests",
    "development_iterations",
)
DatabasePath = Union[str, Path]


class StorageError(ValueError):
    """Raised when the local storage contract cannot be satisfied."""


def connect_database(db_path: DatabasePath) -> sqlite3.Connection:
    """Open a SQLite connection with deterministic row and foreign-key behavior."""

    path = Path(db_path)
    if path.parent and str(path.parent) not in {"", "."}:
        path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def migrate_database(db_path: DatabasePath) -> dict[str, Any]:
    """Create or upgrade the Stage 1 local database to the current schema."""

    conn = connect_database(db_path)
    try:
        _require_fts5(conn)
        journal_mode = str(conn.execute(f"PRAGMA journal_mode={STORAGE_JOURNAL_MODE}").fetchone()[0]).lower()
        _create_schema(conn)
        conn.execute(
            "INSERT OR REPLACE INTO schema_migrations(version, name, applied_at) VALUES (?, ?, datetime('now'))",
            (STORAGE_SCHEMA_VERSION, "stage1_document_event_model"),
        )
        conn.commit()
        return _report(conn, Path(db_path), action="migrate", journal_mode=journal_mode)
    finally:
        conn.close()


def inspect_database(db_path: DatabasePath) -> dict[str, Any]:
    """Inspect a migrated database without changing application rows."""

    if not Path(db_path).exists():
        return {
            "model_id": STORAGE_MODEL_ID,
            "action": "inspect",
            "status": "blocked",
            "db_path": str(db_path),
            "schema_version": 0,
            "blocking_reasons": ["database file does not exist"],
        }
    conn = connect_database(db_path)
    try:
        journal_mode = str(conn.execute("PRAGMA journal_mode").fetchone()[0]).lower()
        return _report(conn, Path(db_path), action="inspect", journal_mode=journal_mode)
    finally:
        conn.close()


def rollback_database(db_path: DatabasePath, *, target_version: int = STORAGE_ROLLBACK_TARGET_VERSION) -> dict[str, Any]:
    """Rollback the S1-04 schema to an empty local database."""

    if target_version != STORAGE_ROLLBACK_TARGET_VERSION:
        raise StorageError(f"only rollback target {STORAGE_ROLLBACK_TARGET_VERSION} is supported")
    conn = connect_database(db_path)
    try:
        existing = _existing_tables(conn)
        for table_name in ["document_fts", *reversed(STORAGE_OBJECT_TABLES), "schema_migrations"]:
            if table_name in existing:
                conn.execute(f"DROP TABLE IF EXISTS {table_name}")
        conn.commit()
        return {
            "model_id": STORAGE_MODEL_ID,
            "action": "rollback",
            "status": "pass",
            "db_path": str(db_path),
            "target_version": target_version,
            "schema_version": 0,
            "dropped_tables": [name for name in ["document_fts", *STORAGE_OBJECT_TABLES, "schema_migrations"] if name in existing],
            "blocking_reasons": [],
        }
    finally:
        conn.close()


def store_source_item(db_path: DatabasePath, source_item: Mapping[str, Any], *, fetch_run_id: str) -> dict[str, Any]:
    """Persist one SourceItem as raw, canonical, version, and FTS rows."""

    errors = validate_source_item(source_item)
    if errors:
        raise StorageError("; ".join(errors))
    conn = connect_database(db_path)
    try:
        _ensure_schema_ready(conn)
        source_id = str(source_item["source_id"])
        source_adapter = str(source_item["source_adapter"])
        source_type = str(source_item["source_type"])
        stable_id = str(source_item["stable_id"])
        retrieved_at = str(source_item["retrieved_at"])
        title = str(source_item["title"])
        canonical_url = str(source_item["canonical_url"])
        raw_payload = json.dumps(source_item, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        raw_sha256 = hashlib.sha256(raw_payload.encode("utf-8")).hexdigest()
        document_id = f"doc:{source_id}"
        version_id = f"ver:{source_id}:{raw_sha256[:12]}"
        content_hash = stable_content_hash(source_item)
        metadata_json = _json_text(source_item.get("metadata", {}))
        license_json = _json_text(source_item.get("license", {}))
        time_json = _json_text({field: source_item.get(field) for field in STORAGE_TIME_FIELDS if source_item.get(field)})

        conn.execute(
            """
            INSERT OR IGNORE INTO source_definitions(source_id, source_type, source_adapter, title, status, created_at)
            VALUES (?, ?, ?, ?, 'active', ?)
            """,
            (source_type, source_type, source_adapter, source_type, retrieved_at),
        )
        conn.execute(
            """
            INSERT OR IGNORE INTO fetch_runs(fetch_run_id, source_id, started_at, status, request_json)
            VALUES (?, ?, ?, 'completed', ?)
            """,
            (fetch_run_id, source_type, retrieved_at, _json_text({"source_adapter": source_adapter})),
        )
        conn.execute(
            """
            INSERT OR IGNORE INTO raw_records(raw_record_id, fetch_run_id, source_id, stable_id, raw_sha256, raw_payload, retrieved_at, known_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (f"raw:{raw_sha256}", fetch_run_id, source_id, stable_id, raw_sha256, raw_payload, retrieved_at, retrieved_at),
        )
        conn.execute(
            """
            INSERT INTO canonical_documents(
                document_id, source_id, stable_id, title, canonical_url, metadata_json, license_json,
                current_version_id, time_json, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(document_id) DO UPDATE SET
                title=excluded.title,
                canonical_url=excluded.canonical_url,
                metadata_json=excluded.metadata_json,
                license_json=excluded.license_json,
                current_version_id=excluded.current_version_id,
                time_json=excluded.time_json,
                updated_at=excluded.updated_at
            """,
            (
                document_id,
                source_id,
                stable_id,
                title,
                canonical_url,
                metadata_json,
                license_json,
                version_id,
                time_json,
                retrieved_at,
                retrieved_at,
            ),
        )
        conn.execute(
            """
            INSERT OR IGNORE INTO document_versions(
                version_id, document_id, version_label, content_hash, title, abstract, source_payload_hash,
                published_at, updated_at, retrieved_at, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                version_id,
                document_id,
                str(source_item.get("version") or "v1"),
                content_hash,
                title,
                str(source_item.get("summary") or source_item.get("metadata", {}).get("summary") or ""),
                raw_sha256,
                str(source_item.get("published_at") or ""),
                str(source_item.get("updated_at") or ""),
                retrieved_at,
                retrieved_at,
            ),
        )
        conn.execute(
            "INSERT OR REPLACE INTO document_fts(rowid, document_id, title, abstract, content) VALUES ((SELECT rowid FROM canonical_documents WHERE document_id=?), ?, ?, ?, ?)",
            (
                document_id,
                document_id,
                title,
                str(source_item.get("summary") or source_item.get("metadata", {}).get("summary") or ""),
                raw_payload,
            ),
        )
        conn.commit()
        return {
            "model_id": STORAGE_MODEL_ID,
            "action": "store_source_item",
            "status": "pass",
            "db_path": str(db_path),
            "document_id": document_id,
            "version_id": version_id,
            "raw_sha256": raw_sha256,
            "blocking_reasons": [],
        }
    finally:
        conn.close()


def validate_storage_report(report: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("model_id") != STORAGE_MODEL_ID:
        errors.append("storage report model_id must be adp-sqlite-data-model-v1")
    if report.get("status") not in {"pass", "blocked"}:
        errors.append("storage report status must be pass or blocked")
    if report.get("status") == "blocked" and not report.get("blocking_reasons"):
        errors.append("blocked storage report requires blocking_reasons")
    if report.get("action") in {"migrate", "inspect"} and report.get("status") == "pass":
        if report.get("schema_version") != STORAGE_SCHEMA_VERSION:
            errors.append("passing storage report must use schema version 1")
        if str(report.get("journal_mode") or "").lower() != STORAGE_JOURNAL_MODE:
            errors.append("passing storage report must use WAL journal mode")
        missing = sorted(set(STORAGE_OBJECT_TABLES) - set(report.get("object_tables") or []))
        if missing:
            errors.append(f"passing storage report missing object tables: {', '.join(missing)}")
        if report.get("fts5_ready") is not True:
            errors.append("passing storage report requires FTS5")
    return errors


def _create_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA_SQL)


def _ensure_schema_ready(conn: sqlite3.Connection) -> None:
    if _schema_version(conn) != STORAGE_SCHEMA_VERSION:
        raise StorageError("database is not migrated to the S1-04 schema")
    _require_fts5(conn)


def _require_fts5(conn: sqlite3.Connection) -> None:
    try:
        conn.execute("CREATE VIRTUAL TABLE IF NOT EXISTS fts5_probe USING fts5(value)")
        conn.execute("DROP TABLE IF EXISTS fts5_probe")
    except sqlite3.DatabaseError as exc:
        raise StorageError("SQLite FTS5 extension is required") from exc


def _report(conn: sqlite3.Connection, db_path: Path, *, action: str, journal_mode: str) -> dict[str, Any]:
    tables = _existing_tables(conn)
    object_tables = [name for name in STORAGE_OBJECT_TABLES if name in tables]
    missing_tables = [name for name in STORAGE_OBJECT_TABLES if name not in tables]
    schema_version = _schema_version(conn)
    fts5_ready = "document_fts" in tables
    status = "pass" if schema_version == STORAGE_SCHEMA_VERSION and not missing_tables and fts5_ready else "blocked"
    blocking_reasons: list[str] = []
    if schema_version != STORAGE_SCHEMA_VERSION:
        blocking_reasons.append(f"schema_version is {schema_version}, expected {STORAGE_SCHEMA_VERSION}")
    if missing_tables:
        blocking_reasons.append(f"missing object tables: {', '.join(missing_tables)}")
    if not fts5_ready:
        blocking_reasons.append("document_fts table missing")
    if journal_mode.lower() != STORAGE_JOURNAL_MODE:
        blocking_reasons.append(f"journal_mode is {journal_mode}, expected {STORAGE_JOURNAL_MODE}")
    return {
        "model_id": STORAGE_MODEL_ID,
        "action": action,
        "status": status,
        "db_path": str(db_path),
        "schema_version": schema_version,
        "journal_mode": journal_mode.lower(),
        "fts5_ready": fts5_ready,
        "object_tables": object_tables,
        "missing_tables": missing_tables,
        "time_fields": list(STORAGE_TIME_FIELDS),
        "relation_types": list(STORAGE_RELATION_TYPES),
        "blocking_reasons": blocking_reasons,
    }


def _existing_tables(conn: sqlite3.Connection) -> set[str]:
    rows = conn.execute("SELECT name FROM sqlite_master WHERE type IN ('table', 'view')").fetchall()
    return {str(row["name"]) for row in rows}


def _schema_version(conn: sqlite3.Connection) -> int:
    if "schema_migrations" not in _existing_tables(conn):
        return 0
    row = conn.execute("SELECT MAX(version) AS version FROM schema_migrations").fetchone()
    return int(row["version"] or 0)


def _json_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS schema_migrations (
  version INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  applied_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS source_definitions (
  source_id TEXT PRIMARY KEY,
  source_type TEXT NOT NULL,
  source_adapter TEXT NOT NULL,
  title TEXT NOT NULL,
  status TEXT NOT NULL,
  policy_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS fetch_runs (
  fetch_run_id TEXT PRIMARY KEY,
  source_id TEXT NOT NULL REFERENCES source_definitions(source_id),
  started_at TEXT NOT NULL,
  finished_at TEXT NOT NULL DEFAULT '',
  status TEXT NOT NULL,
  request_json TEXT NOT NULL,
  response_ref TEXT NOT NULL DEFAULT '',
  error_json TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS raw_records (
  raw_record_id TEXT PRIMARY KEY,
  fetch_run_id TEXT NOT NULL REFERENCES fetch_runs(fetch_run_id),
  source_id TEXT NOT NULL,
  stable_id TEXT NOT NULL,
  raw_sha256 TEXT NOT NULL UNIQUE,
  raw_payload TEXT NOT NULL,
  retrieved_at TEXT NOT NULL,
  observed_at TEXT NOT NULL DEFAULT '',
  known_at TEXT NOT NULL DEFAULT '',
  as_of_at TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS canonical_documents (
  document_id TEXT PRIMARY KEY,
  source_id TEXT NOT NULL,
  stable_id TEXT NOT NULL,
  title TEXT NOT NULL,
  canonical_url TEXT NOT NULL,
  metadata_json TEXT NOT NULL,
  license_json TEXT NOT NULL,
  current_version_id TEXT NOT NULL,
  time_json TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  UNIQUE(source_id, stable_id)
);

CREATE TABLE IF NOT EXISTS document_versions (
  version_id TEXT PRIMARY KEY,
  document_id TEXT NOT NULL REFERENCES canonical_documents(document_id) ON DELETE CASCADE,
  version_label TEXT NOT NULL,
  content_hash TEXT NOT NULL,
  title TEXT NOT NULL,
  abstract TEXT NOT NULL DEFAULT '',
  source_payload_hash TEXT NOT NULL,
  published_at TEXT NOT NULL DEFAULT '',
  updated_at TEXT NOT NULL DEFAULT '',
  effective_at TEXT NOT NULL DEFAULT '',
  expires_at TEXT NOT NULL DEFAULT '',
  retrieved_at TEXT NOT NULL,
  known_at TEXT NOT NULL DEFAULT '',
  as_of_at TEXT NOT NULL DEFAULT '',
  created_at TEXT NOT NULL,
  UNIQUE(document_id, content_hash)
);

CREATE TABLE IF NOT EXISTS events (
  event_id TEXT PRIMARY KEY,
  document_id TEXT NOT NULL REFERENCES canonical_documents(document_id),
  event_type TEXT NOT NULL,
  observed_at TEXT NOT NULL,
  effective_at TEXT NOT NULL DEFAULT '',
  known_at TEXT NOT NULL DEFAULT '',
  payload_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS entities (
  entity_id TEXT PRIMARY KEY,
  entity_type TEXT NOT NULL,
  canonical_name TEXT NOT NULL,
  aliases_json TEXT NOT NULL DEFAULT '[]',
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS relations (
  relation_id TEXT PRIMARY KEY,
  relation_type TEXT NOT NULL,
  subject_id TEXT NOT NULL,
  object_id TEXT NOT NULL,
  evidence_json TEXT NOT NULL,
  observed_at TEXT NOT NULL,
  CHECK (relation_type IN (
    'VERSION_OF','REPLACES','SUPERSEDES','AMENDS','REPEALS','CORRECTS','WITHDRAWS','RETRACTS',
    'PUBLISHED_AS','CITES','SUPPORTS','CONTRADICTS','FUNDED_BY','ASSOCIATED_TRIAL','ASSOCIATED_PATENT',
    'COMMERCIALIZED_BY','IMPLEMENTS','INTERPRETS','ENFORCES','RESPONDS_TO','AFFECTS_ENTITY',
    'AFFECTS_SECTOR','AFFECTS_ASSET','SAME_TOPIC_AS','DERIVED_FROM'
  ))
);

CREATE TABLE IF NOT EXISTS theme_clusters (
  cluster_id TEXT PRIMARY KEY,
  label TEXT NOT NULL,
  method_version TEXT NOT NULL,
  document_ids_json TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS claims (
  claim_id TEXT PRIMARY KEY,
  document_id TEXT NOT NULL REFERENCES canonical_documents(document_id),
  statement TEXT NOT NULL,
  priority TEXT NOT NULL,
  support_status TEXT NOT NULL,
  extracted_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS evidence_bindings (
  evidence_binding_id TEXT PRIMARY KEY,
  claim_id TEXT NOT NULL REFERENCES claims(claim_id) ON DELETE CASCADE,
  raw_record_id TEXT NOT NULL REFERENCES raw_records(raw_record_id),
  locator_json TEXT NOT NULL,
  evidence_sha256 TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS score_snapshots (
  score_snapshot_id TEXT PRIMARY KEY,
  document_id TEXT NOT NULL REFERENCES canonical_documents(document_id),
  model_id TEXT NOT NULL,
  parameter_profile_version TEXT NOT NULL,
  score_json TEXT NOT NULL,
  as_of_at TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS queue_entries (
  queue_entry_id TEXT PRIMARY KEY,
  document_id TEXT NOT NULL REFERENCES canonical_documents(document_id),
  queue_name TEXT NOT NULL,
  status TEXT NOT NULL,
  priority_score REAL NOT NULL,
  rank INTEGER NOT NULL,
  entered_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  reason_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS report_artifacts (
  report_artifact_id TEXT PRIMARY KEY,
  run_id TEXT NOT NULL,
  document_id TEXT NOT NULL,
  artifact_ref TEXT NOT NULL,
  sha256 TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS email_artifacts (
  email_artifact_id TEXT PRIMARY KEY,
  run_id TEXT NOT NULL,
  report_artifact_id TEXT NOT NULL,
  artifact_ref TEXT NOT NULL,
  sha256 TEXT NOT NULL,
  sent_status TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS media_artifacts (
  media_artifact_id TEXT PRIMARY KEY,
  run_id TEXT NOT NULL,
  report_artifact_id TEXT NOT NULL,
  artifact_ref TEXT NOT NULL,
  sha256 TEXT NOT NULL,
  media_status TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS run_manifests (
  run_manifest_id TEXT PRIMARY KEY,
  run_id TEXT NOT NULL,
  manifest_json TEXT NOT NULL,
  status TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS development_iterations (
  iteration_id TEXT PRIMARY KEY,
  task_id TEXT NOT NULL,
  status TEXT NOT NULL,
  evidence_ref TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE VIRTUAL TABLE IF NOT EXISTS document_fts USING fts5(
  document_id UNINDEXED,
  title,
  abstract,
  content
);
"""
