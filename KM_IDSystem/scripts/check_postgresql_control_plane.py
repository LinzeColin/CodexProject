"""Static checks for IDS STAGE-030 PostgreSQL control-plane slice.

This module validates tracked SQL/index contracts only. It does not connect to
PostgreSQL, create databases, inspect raw metadata, or write runtime outputs.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "ids.stage030.postgresql_control_plane.phase2.v1"
SCENARIO_SCHEMA_VERSION = "ids.stage030.postgresql_control_plane.phase3.v1"
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

EXPLAINED_CONSTRAINTS = {
    "chk_payload_size_bytes": "控制面 payload 超过 1 MiB，需要改为 path-only ref、manifest ref 或 hot index pointer.",
    "chk_connection_pool_size": "连接池超出上限，需要降低并发或进入 backpressure/safe mode.",
    "chk_no_raw_content_stored": "发现 raw content 存储企图，必须阻断并保留 owner-facing stop reason.",
    "chk_fact_level": "证据等级不在允许集合内，需要转为 VERIFIED、INFERRED 或 UNKNOWN.",
    "chk_index_state": "热索引状态不在允许集合内，需要保持 DRAFT、READY、BLOCKED 或 ROLLBACK_READY.",
}


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


def _scenario(status: bool, evidence: str, owner_explanation: str, **extra: Any) -> dict[str, Any]:
    payload = {
        "status": "PASS" if status else "FAIL",
        "evidence": evidence,
        "owner_explanation": owner_explanation,
    }
    payload.update(extra)
    return payload


def build_stage030_scenario_report(schema_sql_path: Path, schema_index_path: Path) -> dict[str, Any]:
    sql = schema_sql_path.read_text(encoding="utf-8")
    index = _load_index(schema_index_path)
    migration = index.get("migration", {})
    pool = index.get("connection_pool", {})
    control_report = build_stage030_control_plane_report(schema_sql_path, schema_index_path)
    migration_guards = control_report["migration_guards"]
    storage_guards = control_report["storage_quality_guards"]
    connection_guards = control_report["connection_pool_guards"]

    dry_run_ref = str(migration.get("dry_run_command_ref", ""))
    rollback_ref = str(migration.get("rollback_command_ref", ""))
    single_transaction_required = "--single-transaction" in dry_run_ref and "--single-transaction" in rollback_ref
    on_error_stop_required = "ON_ERROR_STOP=1" in dry_run_ref and "ON_ERROR_STOP=1" in rollback_ref
    constraints_present = {
        constraint_id: constraint_id in sql for constraint_id in EXPLAINED_CONSTRAINTS
    }

    scenario_results = {
        "migration_dry_run": _scenario(
            migration_guards["has_up"]
            and migration_guards["has_down"]
            and migration_guards["has_dry_run"]
            and single_transaction_required,
            f"-- migrate:up/down present; dry_run_command_ref={dry_run_ref}",
            "迁移只能在后续授权 run 中以 dry-run 方式先验证，且必须单事务执行。",
            checks=["has_up", "has_down", "dry_run_required", "single_transaction_required"],
        ),
        "repeat_execution": _scenario(
            all(control_report["table_presence"].values())
            and "CREATE TABLE IF NOT EXISTS" in sql
            and "ids_schema_migrations" in sql,
            "CREATE TABLE IF NOT EXISTS guards every control-plane table; ids_schema_migrations tracks migration identity.",
            "重复执行必须保持幂等或被 schema_migrations 拦截，不能重复污染控制面状态。",
        ),
        "failure_rollback": _scenario(
            migration_guards["has_rollback"] and "DROP TABLE IF EXISTS ids_schema_migrations" in sql,
            "rollback_required=true; DROP TABLE IF EXISTS ids_schema_migrations is present in migrate:down.",
            "失败时必须能回滚控制面 schema，并给 owner 明确失败阶段和恢复入口。",
        ),
        "recovery_smoke": _scenario(
            "recovery_checkpoint_ref" in sql and "rollback_sql_ref" in sql,
            "ids_schema_migrations records recovery_checkpoint_ref and rollback_sql_ref.",
            "恢复冒烟只验证控制面 checkpoint/ref 是否存在，不触碰原始资料或 raw 数据库内容。",
        ),
        "raw_payload_block": _scenario(
            storage_guards["payload_size_guard"]
            and storage_guards["no_raw_content_check"]
            and storage_guards["forbidden_sql_tokens_absent"],
            "NO_RAW_DB_CONTENT, chk_no_raw_content_stored, and 1048576-byte payload guards are present.",
            "数据库不会写入原始大文件、raw database rows、全文正文、OCR 全文、向量 payload 或无限制派生产物。",
        ),
        "connection_pool_boundary": _scenario(
            all(connection_guards.values()),
            f"max_pool_size={pool.get('max_pool_size')}; statement_timeout_ms={pool.get('statement_timeout_ms')}; lock_timeout_ms={pool.get('lock_timeout_ms')}; idle_timeout_ms={pool.get('idle_timeout_ms')}",
            "连接池和 timeout 超限时必须进入可解释 stop reason，而不是无限等待或吃满本机资源。",
            max_pool_size=int(pool.get("max_pool_size", 0)),
        ),
        "transaction_boundary": _scenario(
            single_transaction_required
            and on_error_stop_required
            and migration.get("destructive_allowed") is False,
            f"ON_ERROR_STOP and --single-transaction required by migration refs; destructive_allowed={migration.get('destructive_allowed')}.",
            "DDL 必须在单事务和 fail-fast 条件下验证；破坏性迁移默认被阻断。",
        ),
        "constraint_error_explanations": _scenario(
            all(constraints_present.values()),
            "Constraint ids are mapped to owner-facing explanations.",
            "约束错误必须能解释为 payload、连接池、raw content、证据等级或 index 状态问题。",
            constraint_refs=list(EXPLAINED_CONSTRAINTS),
            explanations=EXPLAINED_CONSTRAINTS,
        ),
    }

    return {
        "schema_version": SCENARIO_SCHEMA_VERSION,
        "stage": "STAGE-030",
        "task_id": "IDS-V0_1-STAGE030-P3",
        "acceptance_id": "ACC-STAGE-030",
        "scenario_results": scenario_results,
        "raw_metadata_boundary": control_report["raw_metadata_boundary"],
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
    scenario_report = build_stage030_scenario_report(
        pursue_root / "001_control_plane_schema.sql",
        pursue_root / "control_plane_schema_index.json",
    )
    print(json.dumps(
        {"control_plane_report": report, "scenario_report": scenario_report},
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    ))
    checks = (
        list(report["table_presence"].values())
        + list(report["migration_guards"].values())
        + list(report["connection_pool_guards"].values())
        + list(report["storage_quality_guards"].values())
        + [
            scenario["status"] == "PASS"
            for scenario in scenario_report["scenario_results"].values()
        ]
        + [
            report["raw_metadata_boundary"]["path"] == RAW_METADATA_ROOT,
            report["raw_metadata_boundary"]["path_only"],
            report["raw_metadata_boundary"]["no_raw_content_access"],
        ]
    )
    return 0 if all(checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
