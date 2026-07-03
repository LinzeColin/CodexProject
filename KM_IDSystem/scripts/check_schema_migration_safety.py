"""Static checks for IDS STAGE-031 schema migration safety.

This module validates tracked migration-safety contracts only. It does not
connect to PostgreSQL, execute migrations, inspect raw metadata, or write
runtime outputs.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "ids.stage031.schema_migration_safety.phase2.v1"
SCENARIO_SCHEMA_VERSION = "ids.stage031.schema_migration_safety.phase3.v1"
DELIVERY_SCHEMA_VERSION = "ids.stage031.schema_migration_safety.phase4.v1"
INDEX_SCHEMA_VERSION = "ids.stage031.schema_migration_safety.index.v1"
STAGE = "STAGE-031"
TASK_ID = "IDS-V0_1-STAGE031-P2"
ACCEPTANCE_ID = "ACC-STAGE-031"
MIGRATION_ID = "ids_stage030_001_control_plane"
RAW_METADATA_ROOT = "/Users/linzezhang/Downloads/IDS_MetaData"

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


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _has_all(text: str, terms: list[str]) -> bool:
    return all(term in text for term in terms)


def _source_refs_match(safety_index: dict[str, Any], control_index: dict[str, Any]) -> bool:
    source_change = safety_index.get("source_schema_change", {})
    migration = control_index.get("migration", {})
    return (
        source_change.get("migration_id") == MIGRATION_ID
        and migration.get("id") == MIGRATION_ID
        and source_change.get("schema_sql_ref") == "../postgresql_control_plane/001_control_plane_schema.sql"
        and source_change.get("schema_index_ref") == "../postgresql_control_plane/control_plane_schema_index.json"
    )


def _safety_gate_results(
    safety_index: dict[str, Any],
    control_sql: str,
    control_index: dict[str, Any],
) -> dict[str, bool]:
    migration = control_index.get("migration", {})
    dry_run_command = str(migration.get("dry_run_command_ref", ""))
    rollback_command = str(migration.get("rollback_command_ref", ""))
    owner_stop_gate = safety_index.get("owner_stop_gate", {})

    return {
        "dry_run_guard": (
            safety_index.get("dry_run_guard", {}).get("required") is True
            and migration.get("dry_run_required") is True
            and _has_all(control_sql, ["-- migrate:up", "-- migrate:down", "dry_run_required"])
            and "ON_ERROR_STOP=1" in dry_run_command
            and "--single-transaction" in dry_run_command
        ),
        "backup_checkpoint_guard": (
            safety_index.get("backup_checkpoint_guard", {}).get("required") is True
            and "recovery_checkpoint_ref" in control_sql
            and "ids_schema_migrations" in control_sql
        ),
        "validation_guard": (
            safety_index.get("validation_guard", {}).get("required") is True
            and _has_all(
                control_sql,
                [
                    "chk_payload_size_bytes",
                    "chk_no_raw_content_stored",
                    "chk_connection_pool_size",
                    "chk_fact_level",
                    "chk_index_state",
                ],
            )
        ),
        "rollback_guard": (
            safety_index.get("rollback_guard", {}).get("required") is True
            and migration.get("rollback_required") is True
            and "-- migrate:down" in control_sql
            and "DROP TABLE IF EXISTS ids_schema_migrations" in control_sql
            and "ON_ERROR_STOP=1" in rollback_command
            and "--single-transaction" in rollback_command
        ),
        "recovery_smoke_guard": (
            safety_index.get("recovery_smoke_guard", {}).get("required") is True
            and _has_all(control_sql, ["recovery_checkpoint_ref", "rollback_sql_ref"])
        ),
        "audit_guard": (
            safety_index.get("audit_guard", {}).get("required") is True
            and _has_all(control_sql, ["ids_audit_events", "ids_schema_migrations"])
        ),
        "owner_stop_gate": (
            owner_stop_gate.get("destructive_auto_approval_allowed") is False
            and migration.get("destructive_allowed") is False
            and "destructive boolean NOT NULL DEFAULT false" in control_sql
        ),
    }


def _guardrail_results(
    safety_index: dict[str, Any],
    control_sql: str,
    control_index: dict[str, Any],
) -> dict[str, bool]:
    lower_sql = control_sql.lower()
    connection_pool_guard = safety_index.get("connection_pool_guard", {})
    control_pool = control_index.get("connection_pool", {})
    database_size_guard = safety_index.get("database_size_guard", {})
    storage_quality_guard = safety_index.get("storage_quality_guard", {})
    raw_boundary = safety_index.get("raw_metadata_boundary", {})
    forbidden = storage_quality_guard.get("forbidden", [])

    return {
        "source_refs_match": _source_refs_match(safety_index, control_index),
        "connection_pool_guard": (
            int(connection_pool_guard.get("max_pool_size", 0)) <= 10
            and int(control_pool.get("max_pool_size", 0)) <= 10
            and int(connection_pool_guard.get("statement_timeout_ms", 0)) <= 30000
            and int(connection_pool_guard.get("lock_timeout_ms", 0)) <= 5000
            and int(connection_pool_guard.get("idle_timeout_ms", 0)) <= 60000
        ),
        "database_size_guard": (
            int(database_size_guard.get("max_control_plane_payload_bytes", 0)) <= 1048576
            and "chk_payload_size_bytes" in control_sql
        ),
        "storage_quality_guard": (
            "NO_RAW_DB_CONTENT" in storage_quality_guard.get("blocked_payloads", [])
            and "chk_no_raw_content_stored" in control_sql
            and all(token not in lower_sql for token in FORBIDDEN_SQL_TOKENS)
        ),
        "raw_metadata_boundary_guard": (
            raw_boundary.get("path") == RAW_METADATA_ROOT
            and raw_boundary.get("path_only") is True
            and raw_boundary.get("content_access_allowed") is False
            and raw_boundary.get("recursive_listing_allowed") is False
            and raw_boundary.get("hashing_allowed") is False
            and raw_boundary.get("copy_allowed") is False
            and raw_boundary.get("modify_allowed") is False
            and raw_boundary.get("dump_allowed") is False
        ),
        "real_data_only_guard": (
            "fake IDS business data" in forbidden
            and "fake database rows" in forbidden
            and "fabricated evidence" in forbidden
        ),
    }


def _scenario(status: bool, evidence: str, owner_explanation: str, **extra: Any) -> dict[str, Any]:
    payload = {
        "status": "PASS" if status else "FAIL",
        "evidence": evidence,
        "owner_explanation": owner_explanation,
    }
    payload.update(extra)
    return payload


def build_stage031_migration_safety_report(
    safety_index_path: Path,
    control_schema_sql_path: Path,
    control_schema_index_path: Path,
) -> dict[str, Any]:
    safety_index = _load_json(safety_index_path)
    control_index = _load_json(control_schema_index_path)
    control_sql = control_schema_sql_path.read_text(encoding="utf-8")
    raw_boundary = safety_index.get("raw_metadata_boundary", {})

    return {
        "schema_version": SCHEMA_VERSION,
        "index_schema_version": safety_index.get("schema_version"),
        "stage": STAGE,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "migration_id": safety_index.get("source_schema_change", {}).get("migration_id"),
        "safety_gate_results": _safety_gate_results(safety_index, control_sql, control_index),
        "guardrail_results": _guardrail_results(safety_index, control_sql, control_index),
        "raw_metadata_boundary": {
            "path": raw_boundary.get("path"),
            "path_only": raw_boundary.get("path_only") is True,
            "no_raw_content_access": raw_boundary.get("content_access_allowed") is False,
        },
        "safety_index_ref": safety_index_path.as_posix(),
        "control_schema_sql_ref": control_schema_sql_path.as_posix(),
        "control_schema_index_ref": control_schema_index_path.as_posix(),
        "does_not_connect_to_postgres": True,
        "does_not_execute_migration": True,
        "does_not_read_raw_metadata": True,
        "does_not_write_runtime_outputs": True,
        "does_not_use_fake_ids_business_data": True,
    }


def build_stage031_scenario_validation_report(
    safety_index_path: Path,
    control_schema_sql_path: Path,
    control_schema_index_path: Path,
) -> dict[str, Any]:
    safety_index = _load_json(safety_index_path)
    control_index = _load_json(control_schema_index_path)
    control_sql = control_schema_sql_path.read_text(encoding="utf-8")
    migration = control_index.get("migration", {})
    pool = safety_index.get("connection_pool_guard", {})
    phase2_report = build_stage031_migration_safety_report(
        safety_index_path,
        control_schema_sql_path,
        control_schema_index_path,
    )
    safety = phase2_report["safety_gate_results"]
    guardrails = phase2_report["guardrail_results"]
    dry_run_command = str(migration.get("dry_run_command_ref", ""))
    rollback_command = str(migration.get("rollback_command_ref", ""))
    single_transaction_required = "--single-transaction" in dry_run_command and "--single-transaction" in rollback_command
    on_error_stop_required = "ON_ERROR_STOP=1" in dry_run_command and "ON_ERROR_STOP=1" in rollback_command
    constraints_present = {
        constraint_id: constraint_id in control_sql for constraint_id in EXPLAINED_CONSTRAINTS
    }

    scenario_results = {
        "migration_dry_run": _scenario(
            safety["dry_run_guard"] and single_transaction_required and on_error_stop_required,
            f"dry_run_command_ref={dry_run_command}; dry_run_guard={safety['dry_run_guard']}",
            "迁移必须先以 fail-fast、单事务 dry-run 合同验证；本阶段只验证合同，不执行 dry-run。",
        ),
        "repeat_execution": _scenario(
            "CREATE TABLE IF NOT EXISTS" in control_sql and "ids_schema_migrations" in control_sql,
            "CREATE TABLE IF NOT EXISTS and ids_schema_migrations are present in the tracked schema contract.",
            "重复执行必须保持幂等或被 migration identity 拦截，不能重复污染控制面状态。",
        ),
        "failure_rollback": _scenario(
            safety["rollback_guard"] and "DROP TABLE IF EXISTS ids_schema_migrations" in control_sql,
            "rollback_guard is true and migrate:down contains DROP TABLE IF EXISTS ids_schema_migrations.",
            "失败回滚必须有 down migration、fail-fast 和单事务要求；本阶段只验证合同。",
        ),
        "backup_restore_checkpoint": _scenario(
            safety["backup_checkpoint_guard"]
            and safety_index.get("backup_checkpoint_guard", {}).get("restore_ref_required") is True,
            "backup_checkpoint_guard is true and restore_ref_required=true in the safety index.",
            "未来 apply 前必须有备份 checkpoint 和 restore ref；本阶段不生成或恢复备份。",
        ),
        "recovery_smoke": _scenario(
            safety["recovery_smoke_guard"] and "recovery_checkpoint_ref" in control_sql and "rollback_sql_ref" in control_sql,
            "recovery_checkpoint_ref and rollback_sql_ref are present in ids_schema_migrations.",
            "恢复冒烟必须能验证控制面 checkpoint/ref；本阶段不执行 live restore smoke。",
        ),
        "raw_payload_block": _scenario(
            guardrails["database_size_guard"]
            and guardrails["storage_quality_guard"]
            and "NO_RAW_DB_CONTENT" in safety_index.get("storage_quality_guard", {}).get("blocked_payloads", []),
            "database_size_guard and storage_quality_guard are true; NO_RAW_DB_CONTENT is blocked.",
            "数据库不会写入原始大文件、raw database rows、全文正文、OCR 全文、向量 payload、报告二进制或 secrets。",
        ),
        "connection_pool_boundary": _scenario(
            guardrails["connection_pool_guard"],
            f"max_pool_size={pool.get('max_pool_size')}; statement_timeout_ms={pool.get('statement_timeout_ms')}; lock_timeout_ms={pool.get('lock_timeout_ms')}; idle_timeout_ms={pool.get('idle_timeout_ms')}",
            "连接池和 timeout 超限时必须进入可解释 stop reason，而不是无限等待或吃满本机资源。",
            max_pool_size=int(pool.get("max_pool_size", 0)),
        ),
        "transaction_boundary": _scenario(
            single_transaction_required
            and on_error_stop_required
            and safety_index.get("owner_stop_gate", {}).get("destructive_auto_approval_allowed") is False,
            "ON_ERROR_STOP and --single-transaction are required; destructive_auto_approval_allowed=false.",
            "DDL 验证必须单事务和 fail-fast；破坏性迁移默认阻断并进入 owner stop-gate。",
        ),
        "constraint_error_explanations": _scenario(
            all(constraints_present.values()),
            "Required constraint ids are present and mapped to owner-facing explanations.",
            "约束错误必须能解释为 payload、连接池、raw content、证据等级或 index 状态问题。",
            constraint_refs=list(EXPLAINED_CONSTRAINTS),
            explanations=EXPLAINED_CONSTRAINTS,
        ),
    }

    return {
        "schema_version": SCENARIO_SCHEMA_VERSION,
        "stage": STAGE,
        "task_id": "IDS-V0_1-STAGE031-P3",
        "acceptance_id": ACCEPTANCE_ID,
        "scenario_results": scenario_results,
        "raw_metadata_boundary": phase2_report["raw_metadata_boundary"],
        "safety_index_ref": safety_index_path.as_posix(),
        "control_schema_sql_ref": control_schema_sql_path.as_posix(),
        "control_schema_index_ref": control_schema_index_path.as_posix(),
        "does_not_connect_to_postgres": True,
        "does_not_execute_migration": True,
        "does_not_read_raw_metadata": True,
        "does_not_write_runtime_outputs": True,
        "does_not_use_fake_ids_business_data": True,
    }


def build_stage031_delivery_report(
    safety_index_path: Path,
    control_schema_sql_path: Path,
    control_schema_index_path: Path,
) -> dict[str, Any]:
    safety_index = _load_json(safety_index_path)
    control_index = _load_json(control_schema_index_path)
    migration = control_index.get("migration", {})
    phase2_report = build_stage031_migration_safety_report(
        safety_index_path,
        control_schema_sql_path,
        control_schema_index_path,
    )
    scenario_report = build_stage031_scenario_validation_report(
        safety_index_path,
        control_schema_sql_path,
        control_schema_index_path,
    )
    safety_gates = phase2_report["safety_gate_results"]
    guardrails = phase2_report["guardrail_results"]
    scenario_results = scenario_report["scenario_results"]
    destructive_auto_allowed = safety_index.get("owner_stop_gate", {}).get("destructive_auto_approval_allowed")

    return {
        "schema_version": DELIVERY_SCHEMA_VERSION,
        "stage": STAGE,
        "phase": "Phase 4",
        "task_id": "IDS-V0_1-STAGE031-P4",
        "acceptance_id": ACCEPTANCE_ID,
        "next_gate": "IDS-STAGE031-REVIEW-GATE",
        "stage_review_status": "pending_next_run",
        "github_upload_allowed": False,
        "app_reinstall_allowed": False,
        "schema_diff": {
            "mode": "static_schema_migration_safety_diff_not_executed",
            "baseline": "STAGE-030 tracked PostgreSQL control-plane schema contract without STAGE-031 safety closeout evidence",
            "target_safety_index_ref": safety_index_path.as_posix(),
            "target_schema_sql_ref": control_schema_sql_path.as_posix(),
            "target_schema_index_ref": control_schema_index_path.as_posix(),
            "migration_id": safety_index.get("source_schema_change", {}).get("migration_id"),
            "safety_gates_added": sorted(safety_gates),
            "guardrails_added": sorted(guardrails),
            "constraints_added": sorted(EXPLAINED_CONSTRAINTS),
            "raw_payload_columns_added": [],
            "notes": "This is a tracked-contract schema migration safety diff only; no live database schema diff was executed.",
        },
        "migration_output": {
            "mode": "static_migration_safety_output_not_executed",
            "migration_id": safety_index.get("source_schema_change", {}).get("migration_id"),
            "dry_run_command_ref": migration.get("dry_run_command_ref"),
            "rollback_command_ref": migration.get("rollback_command_ref"),
            "expected_static_result": "all Phase2 safety gates and guardrails true; all Phase3 scenario statuses PASS",
            "safety_gate_results": safety_gates,
            "guardrail_results": guardrails,
            "scenario_results": scenario_results,
            "live_output_ref": "NOT_AVAILABLE_BY_POLICY_NO_LIVE_POSTGRESQL_CONNECTION",
        },
        "recovery_test_log": {
            "mode": "static_recovery_log_not_executed",
            "checks": [
                "dry_run_guard",
                "backup_checkpoint_guard",
                "validation_guard",
                "rollback_guard",
                "recovery_smoke_guard",
                "recovery_checkpoint_ref",
                "rollback_sql_ref",
                "ON_ERROR_STOP=1",
                "--single-transaction",
            ],
            "result": "static PASS from tracked safety index, SQL, and schema index contracts",
            "live_restore_log_ref": "NOT_AVAILABLE_BY_POLICY_NO_BACKUP_OR_RESTORE_EXECUTION",
        },
        "destructive_migration_confirmation": {
            "required": True,
            "destructive_allowed_by_default": destructive_auto_allowed is True,
            "current_contract_value": destructive_auto_allowed,
            "manual_confirmation_required_before_change": True,
            "owner_message": "任何 DROP、ALTER、数据删除、重建索引或不可逆 schema migration 必须单独人工确认，默认阻断。",
        },
        "rollback_backup_steps": [
            "Stop before live migration if the schema diff cannot be explained from tracked SQL/index/safety contracts.",
            "Create a PostgreSQL logical backup in a future authorized run before any apply.",
            "Record backup location, checksum, migration id, dry-run evidence, and owner approval in future run evidence.",
            "Run rollback_command_ref with ON_ERROR_STOP=1 and --single-transaction if apply fails.",
            "Restore from the approved backup only in a future authorized restore run.",
            "Re-run recovery smoke checks and keep /Users/linzezhang/Downloads/IDS_MetaData path-only after rollback.",
        ],
        "known_limits": [
            "PostgreSQL live connection, dry-run, apply, rollback, backup, restore, and schema diff were not executed in this phase.",
            "The report proves tracked schema migration safety contract readiness, not production database readiness.",
            "No runtime database rows, document/chunk/job rows, indexes, reports, screenshots, PDFs, manifests, ledgers, audit logs, or JSON output files were generated.",
            "Raw metadata remains path-only at /Users/linzezhang/Downloads/IDS_MetaData and was not inspected.",
            "STAGE-031 review is blocked until a separate stage review run; BATCH031_040 upload remains blocked until STAGE-031..040 are complete, reviewed, and repaired.",
        ],
        "chinese_owner_feedback": (
            "STAGE-031 已完成 Phase 4：当前交付的是 schema migration safety 的静态工程合同、"
            "schema diff 摘要、migration 输出说明、恢复测试日志、回滚/备份恢复步骤、破坏性迁移人工确认和中文反馈。"
            "它不是生产数据库迁移授权；下一步应进入 STAGE-031 复审，而不是 GitHub upload 或 app reinstall。"
        ),
        "phase2_report": phase2_report,
        "scenario_report": scenario_report,
        "does_not_connect_to_postgres": True,
        "does_not_execute_migration": True,
        "does_not_read_raw_metadata": True,
        "does_not_write_runtime_outputs": True,
        "does_not_use_fake_ids_business_data": True,
    }


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    pursue_root = root / "docs" / "pursuing_goal" / "ids_v0_1"
    safety_index = pursue_root / "schema_migration_safety" / "stage031_migration_safety_index.json"
    control_sql = pursue_root / "postgresql_control_plane" / "001_control_plane_schema.sql"
    control_index = pursue_root / "postgresql_control_plane" / "control_plane_schema_index.json"
    report = build_stage031_migration_safety_report(
        safety_index,
        control_sql,
        control_index,
    )
    scenario_report = build_stage031_scenario_validation_report(
        safety_index,
        control_sql,
        control_index,
    )
    delivery_report = build_stage031_delivery_report(
        safety_index,
        control_sql,
        control_index,
    )
    print(json.dumps(
        {
            "migration_safety_report": report,
            "scenario_report": scenario_report,
            "delivery_report": delivery_report,
        },
        ensure_ascii=False,
        sort_keys=True,
        indent=2,
    ))
    checks = (
        list(report["safety_gate_results"].values())
        + list(report["guardrail_results"].values())
        + [
            scenario["status"] == "PASS"
            for scenario in scenario_report["scenario_results"].values()
        ]
        + [
            delivery_report["schema_diff"]["mode"] == "static_schema_migration_safety_diff_not_executed",
            delivery_report["migration_output"]["mode"] == "static_migration_safety_output_not_executed",
            delivery_report["recovery_test_log"]["mode"] == "static_recovery_log_not_executed",
            delivery_report["stage_review_status"] == "pending_next_run",
            delivery_report["github_upload_allowed"] is False,
            delivery_report["app_reinstall_allowed"] is False,
            delivery_report["does_not_connect_to_postgres"],
            delivery_report["does_not_execute_migration"],
            delivery_report["does_not_read_raw_metadata"],
            delivery_report["does_not_write_runtime_outputs"],
            delivery_report["does_not_use_fake_ids_business_data"],
        ]
    )
    return 0 if all(checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
