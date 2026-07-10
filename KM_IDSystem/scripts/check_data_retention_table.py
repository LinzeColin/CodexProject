"""Static checks for IDS STAGE-034 data retention table.

This checker validates tracked retention-table contracts only. It does not
connect to PostgreSQL, execute migrations, run cleanup or deletion, inspect raw
metadata, or write runtime outputs.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "ids.stage034.data_retention_table.phase2.v1"
SCENARIO_SCHEMA_VERSION = "ids.stage034.data_retention_table.phase3.v1"
INDEX_SCHEMA_VERSION = "ids.stage034.data_retention_table.index.v1"
STAGE = "STAGE-034"
PHASE = "Phase 2"
SCENARIO_PHASE = "Phase 3"
TASK_ID = "IDS-V0_1-STAGE034-P2"
SCENARIO_TASK_ID = "IDS-V0_1-STAGE034-P3"
ACCEPTANCE_ID = "ACC-STAGE-034"
RAW_METADATA_ROOT = "/Users/linzezhang/Downloads/IDS_MetaData"

EXPECTED_SOURCE_REFS = {
    "phase1_scope_ref": "../STAGE034_PHASE1_SCOPE_BOUNDARY.md",
    "stage030_control_plane_schema_ref": "../postgresql_control_plane/001_control_plane_schema.sql",
    "stage030_control_plane_index_ref": "../postgresql_control_plane/control_plane_schema_index.json",
    "stage031_migration_safety_index_ref": "../schema_migration_safety/stage031_migration_safety_index.json",
    "stage031_migration_safety_checker_ref": "../../../../scripts/check_schema_migration_safety.py",
    "stage032_connection_pool_index_ref": "../database_connection_pool/stage032_connection_pool_index.json",
    "stage032_connection_pool_checker_ref": "../../../../scripts/check_database_connection_pool.py",
    "stage033_database_size_guard_index_ref": "../database_size_guard/stage033_database_size_guard_index.json",
    "stage033_database_size_guard_checker_ref": "../../../../scripts/check_database_size_guard.py",
    "raw_data_boundary_ref": "../IDS_METADATA_RAW_DATA_BOUNDARY.md",
    "phase2_checker_ref": "../../../../scripts/check_data_retention_table.py",
}

EXPECTED_SUBJECTS = {
    "temporary_file",
    "cache",
    "old_index",
    "log",
    "report_snapshot",
}

REQUIRED_GUARDRAILS = [
    "retention_subject_class_guard",
    "ttl_policy_guard",
    "owner_hold_guard",
    "cleanup_dry_run_guard",
    "deletion_stop_gate_guard",
    "audit_evidence_guard",
    "rollback_restore_guard",
    "postgres_storage_scope_guard",
    "database_size_guard_dependency",
    "connection_pool_budget_guard",
    "raw_metadata_boundary",
    "real_data_only_guard",
]

EXPLAINED_CONSTRAINTS = {
    "retention_subject_class_guard": "只允许 temporary_file/cache/old_index/log/report_snapshot 五类保留对象；未知对象和 raw payload subject 必须拒绝。",
    "ttl_policy_guard": "每类保留对象都必须有 TTL、keep-until、到期原因和 warning window，Phase 3 不运行实时 expiry scan。",
    "owner_hold_guard": "人工 hold 或合规 hold 会阻断 cleanup/deletion/compaction/eviction/pruning，且必须记录 owner reason。",
    "cleanup_dry_run_guard": "清理默认仅 dry-run；必须先产出 owner impact/no-delete proof，当前阶段不执行 cleanup。",
    "deletion_stop_gate_guard": "删除、日志压缩、缓存驱逐、旧索引重建和报告快照裁剪默认禁止，必须由后续 owner stop gate 单独授权。",
    "audit_evidence_guard": "保留状态变化必须引用 event/evidence/fact level/中文 owner reason，当前阶段不写 runtime audit。",
    "rollback_restore_guard": "未来清理或删除前必须具备 rollback/restore、backup restore plan 和 post-cleanup verification。",
    "postgres_storage_scope_guard": "PostgreSQL 只存控制面保留策略 metadata 和 refs，不存 raw files、OCR 全文、报告二进制或无限制派生产物。",
    "database_size_guard_dependency": "STAGE-034 不能覆盖 STAGE-033 数据库体积护栏，raw/OCR/大文件和无界派生产物仍被阻断。",
    "connection_pool_budget_guard": "STAGE-034 不增加 STAGE-032 连接池预算；max_pool_size<=10、max_overflow=0 且必须 backpressure。",
    "raw_metadata_boundary_guard": "原始数据库根只记录本机 path，不读取、列出、hash、打开、复制、修改、删除、dump、扫描或 normalize 内容。",
    "real_data_only_guard": "所有 IDS corpus、数据库内容、分析输入、报告、索引和证据必须来自真实用户批准数据，禁止 fake/placeholder/fabricated 数据。",
}


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _scenario(
    status_condition: bool,
    evidence: str,
    owner_explanation: str,
    **extra: Any,
) -> dict[str, Any]:
    result = {
        "status": "PASS" if status_condition else "FAIL",
        "evidence": evidence,
        "owner_explanation": owner_explanation,
    }
    result.update(extra)
    return result


def _guardrail_results(index: dict[str, Any]) -> dict[str, bool]:
    guardrails = index.get("guardrails", {})
    subjects = index.get("retention_subjects", {})
    source_refs = index.get("source_refs", {})
    schema_change = index.get("schema_change_plan", {})
    subject_guard = guardrails.get("retention_subject_class_guard", {})
    ttl = guardrails.get("ttl_policy_guard", {})
    owner_hold = guardrails.get("owner_hold_guard", {})
    cleanup = guardrails.get("cleanup_dry_run_guard", {})
    deletion = guardrails.get("deletion_stop_gate_guard", {})
    audit = guardrails.get("audit_evidence_guard", {})
    rollback = guardrails.get("rollback_restore_guard", {})
    storage = guardrails.get("postgres_storage_scope_guard", {})
    size_guard = guardrails.get("database_size_guard_dependency", {})
    pool = guardrails.get("connection_pool_budget_guard", {})
    raw_boundary = guardrails.get("raw_metadata_boundary", {})
    real_data = guardrails.get("real_data_only_guard", {})
    forbidden = real_data.get("forbidden", [])

    return {
        "required_guardrails_present": all(key in guardrails for key in REQUIRED_GUARDRAILS),
        "source_refs_match": source_refs == EXPECTED_SOURCE_REFS,
        "schema_change_plan_static": (
            schema_change.get("mode") == "static_data_retention_table_contract_only"
            and schema_change.get("sql_file_created") is False
            and schema_change.get("migration_executed") is False
            and schema_change.get("connection_config_created") is False
            and schema_change.get("recovery_smoke_executed") is False
            and schema_change.get("live_schema_diff_executed") is False
        ),
        "retention_subjects_complete": (
            set(subjects) == EXPECTED_SUBJECTS
            and all(subject.get("stores_raw_content") is False for subject in subjects.values())
            and all("ttl_policy" in subject for subject in subjects.values())
            and all("owner_hold_policy" in subject for subject in subjects.values())
            and all(subject.get("audit_evidence_required") is True for subject in subjects.values())
            and all(subject.get("rollback_restore_required") is True for subject in subjects.values())
        ),
        "retention_subject_class_guard": (
            set(subject_guard.get("allowed_subject_classes", [])) == EXPECTED_SUBJECTS
            and subject_guard.get("unknown_subject_allowed") is False
            and subject_guard.get("raw_payload_subject_allowed") is False
        ),
        "ttl_policy_guard": (
            ttl.get("ttl_required") is True
            and ttl.get("keep_until_required") is True
            and ttl.get("expiration_reason_required") is True
            and ttl.get("warning_window_required") is True
            and ttl.get("runtime_expiry_scan_allowed") is False
        ),
        "owner_hold_guard": (
            owner_hold.get("manual_hold_allowed") is True
            and owner_hold.get("compliance_hold_allowed") is True
            and owner_hold.get("owner_hold_blocks_cleanup") is True
            and owner_hold.get("owner_reason_required") is True
            and owner_hold.get("runtime_hold_update_allowed") is False
        ),
        "cleanup_dry_run_guard": (
            cleanup.get("cleanup_default_mode") == "dry_run_only"
            and cleanup.get("owner_impact_report_required") is True
            and cleanup.get("no_delete_proof_required") is True
            and cleanup.get("auto_delete_allowed") is False
            and cleanup.get("runtime_cleanup_allowed") is False
        ),
        "deletion_stop_gate_guard": (
            deletion.get("owner_stop_gate_required") is True
            and deletion.get("destructive_action_allowed_by_default") is False
            and deletion.get("retention_deletion_allowed") is False
            and deletion.get("log_compaction_allowed") is False
            and deletion.get("cache_eviction_allowed") is False
            and deletion.get("old_index_rebuild_allowed") is False
            and deletion.get("report_snapshot_pruning_allowed") is False
        ),
        "audit_evidence_guard": (
            audit.get("audit_evidence_ref_required") is True
            and audit.get("event_ref_required") is True
            and audit.get("fact_level_required") is True
            and audit.get("chinese_owner_reason_required") is True
            and audit.get("runtime_audit_write_allowed") is False
        ),
        "rollback_restore_guard": (
            rollback.get("rollback_restore_ref_required") is True
            and rollback.get("requires_stage031_migration_safety_ref") is True
            and rollback.get("requires_backup_restore_plan") is True
            and rollback.get("requires_post_cleanup_verification") is True
            and rollback.get("runtime_rollback_allowed") is False
            and rollback.get("runtime_restore_allowed") is False
        ),
        "postgres_storage_scope_guard": (
            storage.get("stores_control_plane_metadata") is True
            and storage.get("stores_retention_policy_metadata") is True
            and storage.get("stores_raw_files") is False
            and storage.get("stores_raw_database_rows") is False
            and storage.get("stores_document_bodies") is False
            and storage.get("stores_ocr_full_text") is False
            and storage.get("stores_vector_payloads") is False
            and storage.get("stores_report_binaries") is False
            and storage.get("stores_raw_log_bodies") is False
            and storage.get("stores_unbounded_derived_artifacts") is False
        ),
        "database_size_guard_dependency": (
            size_guard.get("stage033_database_size_guard_ref")
            == "../database_size_guard/stage033_database_size_guard_index.json"
            and size_guard.get("blocked_raw_large_ocr_payloads") is True
            and size_guard.get("retention_table_does_not_override_size_guard") is True
            and size_guard.get("runtime_size_query_allowed") is False
        ),
        "connection_pool_budget_guard": (
            pool.get("stage032_connection_pool_ref") == "../database_connection_pool/stage032_connection_pool_index.json"
            and int(pool.get("aggregate_max_pool_size", 0)) <= 10
            and int(pool.get("max_overflow", -1)) == 0
            and pool.get("backpressure_required") is True
            and pool.get("retention_table_does_not_increase_pool") is True
        ),
        "raw_metadata_boundary_guard": (
            raw_boundary.get("path") == RAW_METADATA_ROOT
            and raw_boundary.get("path_only") is True
            and raw_boundary.get("content_access_allowed") is False
            and raw_boundary.get("recursive_listing_allowed") is False
            and raw_boundary.get("hashing_allowed") is False
            and raw_boundary.get("copy_allowed") is False
            and raw_boundary.get("modify_allowed") is False
            and raw_boundary.get("delete_allowed") is False
            and raw_boundary.get("dump_allowed") is False
            and raw_boundary.get("scan_allowed") is False
            and raw_boundary.get("normalize_allowed") is False
        ),
        "real_data_only_guard": (
            "fake IDS business data" in forbidden
            and "fake database rows" in forbidden
            and "fake source documents" in forbidden
            and "placeholder corpus" in forbidden
            and "fabricated evidence" in forbidden
            and "plaintext secrets" in forbidden
        ),
    }


def _runtime_policy_results(index: dict[str, Any]) -> dict[str, bool]:
    runtime_policy = index.get("runtime_policy", {})
    return {
        "connect_to_postgres": runtime_policy.get("connect_to_postgres") is False,
        "execute_migration": runtime_policy.get("execute_migration") is False,
        "create_database": runtime_policy.get("create_database") is False,
        "create_schema": runtime_policy.get("create_schema") is False,
        "create_connection_config": runtime_policy.get("create_connection_config") is False,
        "execute_cleanup": runtime_policy.get("execute_cleanup") is False,
        "execute_deletion": runtime_policy.get("execute_deletion") is False,
        "execute_retention_scan": runtime_policy.get("execute_retention_scan") is False,
        "execute_log_compaction": runtime_policy.get("execute_log_compaction") is False,
        "execute_cache_eviction": runtime_policy.get("execute_cache_eviction") is False,
        "execute_index_rebuild": runtime_policy.get("execute_index_rebuild") is False,
        "execute_report_snapshot_pruning": runtime_policy.get("execute_report_snapshot_pruning") is False,
        "execute_backup": runtime_policy.get("execute_backup") is False,
        "execute_restore": runtime_policy.get("execute_restore") is False,
        "write_runtime_outputs": runtime_policy.get("write_runtime_outputs") is False,
        "read_raw_metadata": runtime_policy.get("read_raw_metadata") is False,
        "write_raw_metadata": runtime_policy.get("write_raw_metadata") is False,
        "install_dependencies": runtime_policy.get("install_dependencies") is False,
        "start_services": runtime_policy.get("start_services") is False,
        "github_upload": runtime_policy.get("github_upload") is False,
        "app_reinstall": runtime_policy.get("app_reinstall") is False,
    }


def build_stage034_data_retention_table_report(index_path: Path) -> dict[str, Any]:
    index = _load_json(index_path)
    raw_boundary = index.get("guardrails", {}).get("raw_metadata_boundary", {})
    subjects = index.get("retention_subjects", {})
    return {
        "schema_version": SCHEMA_VERSION,
        "index_schema_version": index.get("schema_version"),
        "stage": STAGE,
        "phase": PHASE,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "data_retention_table_contract_id": index.get("data_retention_table_contract_id"),
        "retention_subjects": sorted(subjects),
        "guardrail_results": _guardrail_results(index),
        "runtime_policy_results": _runtime_policy_results(index),
        "raw_metadata_boundary": {
            "path": raw_boundary.get("path"),
            "path_only": raw_boundary.get("path_only") is True,
            "no_raw_content_access": raw_boundary.get("content_access_allowed") is False,
        },
        "data_retention_table_index_ref": index_path.as_posix(),
        "does_not_connect_to_postgres": True,
        "does_not_execute_migration": True,
        "does_not_read_raw_metadata": True,
        "does_not_write_runtime_outputs": True,
        "does_not_use_fake_ids_business_data": True,
        "does_not_execute_cleanup": True,
        "does_not_execute_deletion": True,
    }


def build_stage034_scenario_validation_report(index_path: Path) -> dict[str, Any]:
    index = _load_json(index_path)
    phase2_report = build_stage034_data_retention_table_report(index_path)
    guardrails = phase2_report["guardrail_results"]
    runtime = phase2_report["runtime_policy_results"]

    scenario_results = {
        "migration_dry_run": _scenario(
            guardrails["schema_change_plan_static"]
            and runtime["execute_migration"]
            and runtime["connect_to_postgres"],
            "schema_change_plan.mode=static_data_retention_table_contract_only; migration_executed=false; connect_to_postgres=false",
            "本阶段只验证静态 migration 依赖边界，不执行 live dry-run、apply、rollback、backup、restore 或 schema diff。",
        ),
        "repeat_execution": _scenario(
            guardrails["source_refs_match"]
            and runtime["write_runtime_outputs"]
            and runtime["execute_retention_scan"],
            "checker reads the tracked data_retention_table index and writes stdout JSON only; write_runtime_outputs=false",
            "重复执行只会重新读取 Git 里的静态合同并输出 stdout，不创建数据库行、manifest、报告或 runtime artifact。",
        ),
        "failure_rollback": _scenario(
            guardrails["rollback_restore_guard"]
            and runtime["execute_backup"]
            and runtime["execute_restore"]
            and runtime["execute_migration"],
            "rollback_restore_guard requires backup/restore plan while runtime backup/restore/migration execution remains false",
            "失败回滚在当前阶段只验证 rollback/restore 证据要求，不执行真实备份、恢复或迁移回滚。",
        ),
        "recovery_smoke": _scenario(
            guardrails["rollback_restore_guard"]
            and runtime["execute_restore"]
            and index.get("schema_change_plan", {}).get("recovery_smoke_executed") is False,
            "schema_change_plan.recovery_smoke_executed=false and rollback_restore_guard is present",
            "恢复冒烟只作为后续门禁要求被记录；本阶段不启动服务、不恢复数据库、不运行 smoke 命令。",
        ),
        "raw_payload_block": _scenario(
            guardrails["postgres_storage_scope_guard"] and guardrails["raw_metadata_boundary_guard"],
            "postgres_storage_scope_guard stores_raw_files=false and raw_metadata_boundary content_access_allowed=false",
            "数据保留表只存 metadata/ref，不读取或写入 /Users/linzezhang/Downloads/IDS_MetaData 的原始数据库内容。",
        ),
        "unbounded_derived_artifact_block": _scenario(
            guardrails["postgres_storage_scope_guard"] and guardrails["database_size_guard_dependency"],
            "stores_unbounded_derived_artifacts=false and STAGE033 database-size guard remains authoritative",
            "缓存、旧索引、报告快照等派生产物必须有界，不允许绕过 STAGE-033 体积护栏。",
        ),
        "retention_subject_validation": _scenario(
            guardrails["retention_subjects_complete"] and guardrails["retention_subject_class_guard"],
            "retention subjects are exactly temporary_file/cache/old_index/log/report_snapshot",
            "保留表只接受五类对象；未知对象和 raw payload subject 不进入 PostgreSQL 控制面。",
        ),
        "ttl_owner_hold_policy": _scenario(
            guardrails["ttl_policy_guard"] and guardrails["owner_hold_guard"],
            "ttl_policy_guard and owner_hold_guard both pass for all tracked retention subjects",
            "每类保留对象必须有 TTL/keep-until/owner hold；hold 会阻断清理、删除、压缩、驱逐或裁剪。",
        ),
        "cleanup_dry_run": _scenario(
            guardrails["cleanup_dry_run_guard"] and runtime["execute_cleanup"],
            "cleanup_default_mode=dry_run_only and execute_cleanup=false",
            "当前阶段只验证 dry-run guardrail，不执行清理、不产生 cleanup output。",
        ),
        "deletion_stop_gate": _scenario(
            guardrails["deletion_stop_gate_guard"]
            and runtime["execute_deletion"]
            and runtime["execute_log_compaction"]
            and runtime["execute_cache_eviction"]
            and runtime["execute_index_rebuild"]
            and runtime["execute_report_snapshot_pruning"],
            "owner_stop_gate_required=true and deletion/compaction/eviction/rebuild/pruning runtime flags are false",
            "删除及所有派生破坏性动作必须等后续 owner stop gate；本阶段保持禁止。",
        ),
        "connection_pool_boundary": _scenario(
            guardrails["connection_pool_budget_guard"] and runtime["connect_to_postgres"],
            "connection pool budget max_pool_size<=10, max_overflow=0, and connect_to_postgres=false",
            "数据保留表不会增加 STAGE-032 连接池预算，也不会建立 PostgreSQL 连接。",
        ),
        "transaction_boundary": _scenario(
            guardrails["schema_change_plan_static"]
            and guardrails["connection_pool_budget_guard"]
            and runtime["connect_to_postgres"]
            and runtime["execute_migration"],
            "static schema-change plan plus no PostgreSQL connection and no migration execution",
            "事务边界只在静态合同层验证；当前阶段不打开事务、不提交、不回滚真实数据库事务。",
        ),
        "constraint_error_explanations": _scenario(
            (
                all(key in EXPLAINED_CONSTRAINTS for key in REQUIRED_GUARDRAILS if key != "raw_metadata_boundary")
                and "raw_metadata_boundary_guard" in EXPLAINED_CONSTRAINTS
            ),
            "every required retention guardrail has a Chinese owner-facing explanation",
            "约束错误必须能解释为保留对象、TTL/hold、清理 dry-run、删除 stop gate、raw boundary 或真实数据政策问题。",
            explanations=EXPLAINED_CONSTRAINTS,
        ),
    }

    raw_boundary = index.get("guardrails", {}).get("raw_metadata_boundary", {})
    return {
        "schema_version": SCENARIO_SCHEMA_VERSION,
        "index_schema_version": index.get("schema_version"),
        "stage": STAGE,
        "phase": SCENARIO_PHASE,
        "task_id": SCENARIO_TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "data_retention_table_contract_id": index.get("data_retention_table_contract_id"),
        "phase2_report": phase2_report,
        "scenario_results": scenario_results,
        "raw_metadata_boundary": {
            "path": raw_boundary.get("path"),
            "path_only": raw_boundary.get("path_only") is True,
            "no_raw_content_access": raw_boundary.get("content_access_allowed") is False,
        },
        "data_retention_table_index_ref": index_path.as_posix(),
        "does_not_connect_to_postgres": True,
        "does_not_execute_migration": True,
        "does_not_read_raw_metadata": True,
        "does_not_write_runtime_outputs": True,
        "does_not_use_fake_ids_business_data": True,
        "does_not_execute_cleanup": True,
        "does_not_execute_deletion": True,
    }


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    index_path = (
        root
        / "docs"
        / "pursuing_goal"
        / "ids_v0_1"
        / "data_retention_table"
        / "stage034_data_retention_table_index.json"
    )
    report = build_stage034_data_retention_table_report(index_path)
    scenario_report = build_stage034_scenario_validation_report(index_path)
    print(
        json.dumps(
            {
                "data_retention_table_report": report,
                "scenario_report": scenario_report,
            },
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
        )
    )
    checks = (
        list(report["guardrail_results"].values())
        + list(report["runtime_policy_results"].values())
        + [
            report["index_schema_version"] == INDEX_SCHEMA_VERSION,
            report["does_not_connect_to_postgres"],
            report["does_not_execute_migration"],
            report["does_not_read_raw_metadata"],
            report["does_not_write_runtime_outputs"],
            report["does_not_use_fake_ids_business_data"],
            report["does_not_execute_cleanup"],
            report["does_not_execute_deletion"],
            all(result["status"] == "PASS" for result in scenario_report["scenario_results"].values()),
            scenario_report["does_not_connect_to_postgres"],
            scenario_report["does_not_execute_migration"],
            scenario_report["does_not_read_raw_metadata"],
            scenario_report["does_not_write_runtime_outputs"],
            scenario_report["does_not_use_fake_ids_business_data"],
            scenario_report["does_not_execute_cleanup"],
            scenario_report["does_not_execute_deletion"],
        ]
    )
    return 0 if all(checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
