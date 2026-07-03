"""Static checks for IDS STAGE-030 PostgreSQL control-plane slice.

This module validates tracked SQL/index contracts only. It does not connect to
PostgreSQL, create databases, inspect raw metadata, or write runtime outputs.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "ids.stage030.postgresql_control_plane.phase2.v1"
MIGRATION_ID = "ids_stage030_001_control_plane"
RAW_METADATA_ROOT = "/Users/linzezhang/Downloads/IDS_MetaData"

REQUIRED_TABLES = [
    "ids_metadata_sources",
    "ids_jobs",
    "ids_documents",
    "ids_chunks",
    "ids_evidence_records",
    "ids_audit_events",
    "ids_index_versions",
    "ids_schema_migrations",
]

FORBIDDEN_SQL_TOKENS = [
    "raw_file_body",
    "raw_database_dump",
    "document_body",
    "chunk_text",
    "embedding_vector",
    "api_key",
    "password=",
    "postgresql://",
]


def _load_index(index_path: Path) -> dict[str, Any]:
    return json.loads(index_path.read_text(encoding="utf-8"))


def _table_presence(sql: str) -> dict[str, bool]:
    return {
        table: f"CREATE TABLE IF NOT EXISTS {table}" in sql
        for table in REQUIRED_TABLES
    }


def _migration_guards(sql: str, index: dict[str, Any]) -> dict[str, bool]:
    migration = index.get("migration", {})
    return {
        "has_up": "-- migrate:up" in sql,
        "has_down": "-- migrate:down" in sql,
        "has_dry_run": bool(migration.get("dry_run_required"))
        and "dry_run_required" in sql,
        "has_rollback": bool(migration.get("rollback_required"))
        and "rollback_required" in sql
        and "DROP TABLE IF EXISTS ids_schema_migrations" in sql,
        "migration_id_matches": migration.get("id") == MIGRATION_ID,
        "destructive_migration_blocked": migration.get("destructive_allowed") is False
        and "destructive boolean NOT NULL DEFAULT false" in sql,
    }


def _connection_pool_guards(index: dict[str, Any]) -> dict[str, bool]:
    connection = index.get("connection", {})
    pool = index.get("connection_pool", {})
    return {
        "dsn_is_env_ref_only": connection.get("connection_url_ref") == "ENV:IDS_POSTGRES_DSN",
        "secrets_forbidden": connection.get("secrets_forbidden") is True,
        "max_pool_size_guard": int(pool.get("max_pool_size", 0)) <= 10,
        "statement_timeout_guard": int(pool.get("statement_timeout_ms", 0)) <= 30000,
        "lock_timeout_guard": int(pool.get("lock_timeout_ms", 0)) <= 5000,
        "idle_timeout_guard": int(pool.get("idle_timeout_ms", 0)) <= 60000,
    }


def _storage_quality_guards(sql: str, index: dict[str, Any]) -> dict[str, bool]:
    lower_sql = sql.lower()
    size_guard = index.get("database_size_guard", {})
    storage_boundary = index.get("storage_boundary", {})
    quality_guards = index.get("quality_guards", {})
    forbidden = quality_guards.get("forbidden", [])
    blocked_payloads = storage_boundary.get("blocked_payloads", [])
    forbidden_sql_clear = all(token not in lower_sql for token in FORBIDDEN_SQL_TOKENS)
    return {
        "required_tables_present": all(_table_presence(sql).values()),
        "payload_size_guard": int(size_guard.get("max_control_plane_payload_bytes", 0)) <= 1048576
        and "chk_payload_size_bytes" in sql,
        "no_raw_content_check": "chk_no_raw_content_stored" in sql
        and "NO_RAW_DB_CONTENT" in sql,
        "hot_index_state_guard": "chk_index_state" in sql,
        "fact_level_guard": "chk_fact_level" in sql,
        "forbidden_sql_tokens_absent": forbidden_sql_clear,
        "raw_content_blocked_in_index": "NO_RAW_DB_CONTENT" in blocked_payloads,
        "fake_data_forbidden": "fake IDS business data" in forbidden,
    }


def build_stage030_control_plane_report(schema_sql_path: Path, schema_index_path: Path) -> dict[str, Any]:
    sql = schema_sql_path.read_text(encoding="utf-8")
    index = _load_index(schema_index_path)
    raw_boundary = index.get("raw_metadata_boundary", {})

    return {
        "schema_version": SCHEMA_VERSION,
        "stage": "STAGE-030",
        "task_id": "IDS-V0_1-STAGE030-P2",
        "acceptance_id": "ACC-STAGE-030",
        "migration_id": MIGRATION_ID,
        "required_tables": REQUIRED_TABLES,
        "table_presence": _table_presence(sql),
        "migration_guards": _migration_guards(sql, index),
        "connection_pool_guards": _connection_pool_guards(index),
        "storage_quality_guards": _storage_quality_guards(sql, index),
        "raw_metadata_boundary": {
            "path": raw_boundary.get("path"),
            "path_only": raw_boundary.get("path_only") is True,
            "no_raw_content_access": raw_boundary.get("content_access_allowed") is False,
        },
        "index_schema_version": index.get("schema_version"),
        "schema_sql_ref": schema_sql_path.as_posix(),
        "schema_index_ref": schema_index_path.as_posix(),
        "does_not_connect_to_postgres": True,
        "does_not_read_raw_metadata": True,
        "does_not_write_runtime_outputs": True,
        "does_not_use_fake_ids_business_data": True,
    }


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    pursue_root = root / "docs" / "pursuing_goal" / "ids_v0_1" / "postgresql_control_plane"
    report = build_stage030_control_plane_report(
        pursue_root / "001_control_plane_schema.sql",
        pursue_root / "control_plane_schema_index.json",
    )
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    checks = (
        list(report["table_presence"].values())
        + list(report["migration_guards"].values())
        + list(report["connection_pool_guards"].values())
        + list(report["storage_quality_guards"].values())
        + [
            report["raw_metadata_boundary"]["path"] == RAW_METADATA_ROOT,
            report["raw_metadata_boundary"]["path_only"],
            report["raw_metadata_boundary"]["no_raw_content_access"],
        ]
    )
    return 0 if all(checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
