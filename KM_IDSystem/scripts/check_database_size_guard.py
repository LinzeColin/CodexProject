"""Static checks for IDS STAGE-033 database size guard.

This module validates tracked database-size guard contracts only. It does not
connect to PostgreSQL, run size queries, execute cleanup, inspect raw metadata,
or write runtime outputs.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "ids.stage033.database_size_guard.phase2.v1"
SCENARIO_SCHEMA_VERSION = "ids.stage033.database_size_guard.phase3.v1"
DELIVERY_SCHEMA_VERSION = "ids.stage033.database_size_guard.phase4.v1"
INDEX_SCHEMA_VERSION = "ids.stage033.database_size_guard.index.v1"
STAGE = "STAGE-033"
PHASE = "Phase 2"
TASK_ID = "IDS-V0_1-STAGE033-P2"
ACCEPTANCE_ID = "ACC-STAGE-033"
RAW_METADATA_ROOT = "/Users/linzezhang/Downloads/IDS_MetaData"

EXPECTED_SOURCE_REFS = {
    "phase1_scope_ref": "../STAGE033_PHASE1_SCOPE_BOUNDARY.md",
    "stage030_control_plane_schema_ref": "../postgresql_control_plane/001_control_plane_schema.sql",
    "stage030_control_plane_index_ref": "../postgresql_control_plane/control_plane_schema_index.json",
    "stage031_migration_safety_index_ref": "../schema_migration_safety/stage031_migration_safety_index.json",
    "stage031_migration_safety_checker_ref": "../../../../scripts/check_schema_migration_safety.py",
    "stage032_connection_pool_index_ref": "../database_connection_pool/stage032_connection_pool_index.json",
    "stage032_connection_pool_checker_ref": "../../../../scripts/check_database_connection_pool.py",
    "raw_data_boundary_ref": "../IDS_METADATA_RAW_DATA_BOUNDARY.md",
    "phase2_checker_ref": "../../../../scripts/check_database_size_guard.py",
}

REQUIRED_GUARDRAILS = [
    "postgres_storage_scope_guard",
    "raw_content_block_guard",
    "ocr_full_text_block_guard",
    "large_file_block_guard",
    "derived_artifact_limit_guard",
    "database_size_budget_guard",
    "table_size_guard",
    "index_bloat_guard",
    "row_payload_guard",
    "retention_cleanup_guard",
    "connection_pool_budget_guard",
    "quality_constraint_guard",
    "rollback_verification_guard",
    "raw_metadata_boundary",
    "real_data_only_guard",
]

EXPLAINED_CONSTRAINTS = {
    "postgres_storage_scope_guard": "PostgreSQL 只能保存控制面 metadata、状态 refs、audit/evidence refs、migration/job state 和有界 hot-index metadata.",
    "database_size_budget_guard": "数据库体积阈值是 policy threshold，不是实测数据库大小；超过 warning/hard-stop 阈值必须给出 owner-readable stop reason.",
    "row_payload_guard": "单行 payload 和 scalar text 必须有上限；raw/OCR/vector/report binary body 必须改为 path-only ref 或可重建派生产物 ref.",
    "retention_cleanup_guard": "cleanup 默认 dry-run only；自动删除、VACUUM、reindex、backup/restore 或 retention deletion 需要后续 owner stop gate.",
    "connection_pool_budget_guard": "数据库体积护栏不得绕过 STAGE-032 连接池预算；连接池上限、overflow 和 backpressure 必须保持可解释.",
    "rollback_verification_guard": "体积相关 schema 或 cleanup 变化必须绑定 STAGE-031 migration safety、备份恢复计划和 post-cleanup verification.",
    "raw_metadata_boundary_guard": "/Users/linzezhang/Downloads/IDS_MetaData 只允许 path-only 边界记录，不得读取、列出、hash、复制、修改、删除、dump、scan 或 normalize.",
    "real_data_only_guard": "系统只允许使用 owner-approved 真实数据；fake IDS business data、fake rows、placeholder corpus 和 fabricated evidence 必须阻断.",
}


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _scenario(status: bool, evidence: str, owner_explanation: str, **extra: Any) -> dict[str, Any]:
    payload = {
        "status": "PASS" if status else "FAIL",
        "evidence": evidence,
        "owner_explanation": owner_explanation,
    }
    payload.update(extra)
    return payload


def _guardrail_results(index: dict[str, Any]) -> dict[str, bool]:
    guardrails = index.get("guardrails", {})
    source_refs = index.get("source_refs", {})
    schema_change = index.get("schema_change_plan", {})
    storage = guardrails.get("postgres_storage_scope_guard", {})
    raw = guardrails.get("raw_content_block_guard", {})
    ocr = guardrails.get("ocr_full_text_block_guard", {})
    large_file = guardrails.get("large_file_block_guard", {})
    derived = guardrails.get("derived_artifact_limit_guard", {})
    budget = guardrails.get("database_size_budget_guard", {})
    table = guardrails.get("table_size_guard", {})
    bloat = guardrails.get("index_bloat_guard", {})
    row = guardrails.get("row_payload_guard", {})
    cleanup = guardrails.get("retention_cleanup_guard", {})
    pool = guardrails.get("connection_pool_budget_guard", {})
    quality = guardrails.get("quality_constraint_guard", {})
    rollback = guardrails.get("rollback_verification_guard", {})
    raw_boundary = guardrails.get("raw_metadata_boundary", {})
    real_data = guardrails.get("real_data_only_guard", {})
    forbidden = real_data.get("forbidden", [])

    return {
        "required_guardrails_present": all(key in guardrails for key in REQUIRED_GUARDRAILS),
        "source_refs_match": source_refs == EXPECTED_SOURCE_REFS,
        "schema_change_plan_static": (
            schema_change.get("mode") == "static_database_size_guard_contract_only"
            and schema_change.get("sql_file_created") is False
            and schema_change.get("migration_executed") is False
            and schema_change.get("connection_config_created") is False
            and schema_change.get("recovery_smoke_executed") is False
            and schema_change.get("live_schema_diff_executed") is False
        ),
        "postgres_storage_scope_guard": (
            storage.get("stores_control_plane_metadata") is True
            and storage.get("stores_state_refs") is True
            and storage.get("stores_bounded_hot_index_metadata") is True
            and storage.get("stores_raw_files") is False
            and storage.get("stores_raw_database_rows") is False
            and storage.get("stores_document_bodies") is False
            and storage.get("stores_ocr_full_text") is False
            and storage.get("stores_vector_payloads") is False
            and storage.get("stores_report_binaries") is False
            and storage.get("stores_unbounded_derived_artifacts") is False
        ),
        "raw_content_block_guard": (
            raw.get("stores_raw_content_allowed") is False
            and "500GB raw files" in raw.get("blocked_payloads", [])
            and "raw metadata database content" in raw.get("blocked_payloads", [])
            and "raw database rows" in raw.get("blocked_payloads", [])
        ),
        "ocr_full_text_block_guard": (
            ocr.get("stores_ocr_full_text_allowed") is False
            and "OCR full text" in ocr.get("blocked_payloads", [])
            and "full document text" in ocr.get("blocked_payloads", [])
        ),
        "large_file_block_guard": (
            large_file.get("stores_large_files_allowed") is False
            and "report binaries" in large_file.get("blocked_payloads", [])
            and "large vector payloads" in large_file.get("blocked_payloads", [])
        ),
        "derived_artifact_limit_guard": (
            derived.get("unbounded_derived_artifacts_allowed") is False
            and derived.get("requires_recreatable_or_path_only_ref") is True
            and "bounded_hot_index_metadata" in derived.get("allowed_artifacts", [])
        ),
        "database_size_budget_guard": (
            budget.get("budget_mode") == "policy_threshold_not_measured_runtime_size"
            and int(budget.get("internal_disk_budget_gib", 0)) == 800
            and 0 < int(budget.get("warning_threshold_gib", 0)) <= int(budget.get("hard_stop_threshold_gib", 0))
            and int(budget.get("hard_stop_threshold_gib", 0)) <= int(budget.get("internal_disk_budget_gib", 0))
            and budget.get("runtime_size_query_allowed") is False
            and budget.get("auto_cleanup_allowed") is False
            and budget.get("protects_internal_disk") is True
        ),
        "table_size_guard": (
            int(table.get("max_control_plane_table_gib", 0)) <= 8
            and int(table.get("max_hot_index_table_gib", 0)) <= 12
            and table.get("raw_payload_columns_allowed") is False
            and table.get("owner_exception_required") is True
            and table.get("runtime_table_scan_allowed") is False
        ),
        "index_bloat_guard": (
            0 < int(bloat.get("warning_percent", 0)) <= int(bloat.get("hard_stop_percent", 0))
            and int(bloat.get("hard_stop_percent", 0)) <= 50
            and bloat.get("automatic_reindex_allowed") is False
            and bloat.get("owner_rebuild_decision_ref_required") is True
            and bloat.get("runtime_bloat_query_allowed") is False
        ),
        "row_payload_guard": (
            int(row.get("max_control_plane_payload_bytes", 0)) <= 1048576
            and int(row.get("max_single_scalar_text_bytes", 0)) <= 65536
            and row.get("stores_raw_content_allowed") is False
            and row.get("stores_ocr_full_text_allowed") is False
            and row.get("stores_vector_payloads_allowed") is False
            and row.get("stores_report_binaries_allowed") is False
        ),
        "retention_cleanup_guard": (
            cleanup.get("cleanup_default_mode") == "dry_run_only"
            and cleanup.get("auto_delete_allowed") is False
            and cleanup.get("owner_stop_gate_required") is True
            and cleanup.get("rollback_ref_required") is True
            and cleanup.get("backup_restore_ref_required") is True
            and cleanup.get("runtime_cleanup_allowed") is False
        ),
        "connection_pool_budget_guard": (
            pool.get("stage032_connection_pool_ref") == "../database_connection_pool/stage032_connection_pool_index.json"
            and int(pool.get("aggregate_max_pool_size", 0)) <= 10
            and int(pool.get("max_overflow", -1)) == 0
            and pool.get("backpressure_required") is True
            and pool.get("size_guard_does_not_increase_pool") is True
        ),
        "quality_constraint_guard": (
            quality.get("fake_data_allowed") is False
            and quality.get("fabricated_evidence_allowed") is False
            and "no_raw_content_stored" in quality.get("required_constraints", [])
            and "payload_size_bounded" in quality.get("required_constraints", [])
            and "real_data_only" in quality.get("required_constraints", [])
        ),
        "rollback_verification_guard": (
            rollback.get("requires_stage031_migration_safety_ref") is True
            and rollback.get("requires_backup_restore_plan") is True
            and rollback.get("requires_post_cleanup_verification") is True
            and rollback.get("requires_owner_stop_gate_for_deletion") is True
            and rollback.get("runtime_rollback_allowed") is False
            and rollback.get("runtime_restore_allowed") is False
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
        "run_size_queries": runtime_policy.get("run_size_queries") is False,
        "execute_cleanup": runtime_policy.get("execute_cleanup") is False,
        "execute_vacuum": runtime_policy.get("execute_vacuum") is False,
        "execute_reindex": runtime_policy.get("execute_reindex") is False,
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


def build_stage033_database_size_guard_report(index_path: Path) -> dict[str, Any]:
    index = _load_json(index_path)
    raw_boundary = index.get("guardrails", {}).get("raw_metadata_boundary", {})
    budget = index.get("guardrails", {}).get("database_size_budget_guard", {})
    return {
        "schema_version": SCHEMA_VERSION,
        "index_schema_version": index.get("schema_version"),
        "stage": STAGE,
        "phase": PHASE,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "database_size_guard_contract_id": index.get("database_size_guard_contract_id"),
        "guardrail_results": _guardrail_results(index),
        "runtime_policy_results": _runtime_policy_results(index),
        "policy_thresholds": {
            "budget_mode": budget.get("budget_mode"),
            "internal_disk_budget_gib": budget.get("internal_disk_budget_gib"),
            "warning_threshold_gib": budget.get("warning_threshold_gib"),
            "hard_stop_threshold_gib": budget.get("hard_stop_threshold_gib"),
            "measured_database_size_gib": "NOT_MEASURED_BY_POLICY",
        },
        "raw_metadata_boundary": {
            "path": raw_boundary.get("path"),
            "path_only": raw_boundary.get("path_only") is True,
            "no_raw_content_access": raw_boundary.get("content_access_allowed") is False,
        },
        "database_size_guard_index_ref": index_path.as_posix(),
        "does_not_connect_to_postgres": True,
        "does_not_execute_migration": True,
        "does_not_read_raw_metadata": True,
        "does_not_write_runtime_outputs": True,
        "does_not_use_fake_ids_business_data": True,
        "does_not_run_size_queries": True,
        "does_not_execute_cleanup": True,
    }


def build_stage033_scenario_validation_report(index_path: Path) -> dict[str, Any]:
    index = _load_json(index_path)
    phase2_report = build_stage033_database_size_guard_report(index_path)
    guardrails = phase2_report["guardrail_results"]
    runtime_policy = phase2_report["runtime_policy_results"]
    source_refs = index.get("source_refs", {})
    schema_change = index.get("schema_change_plan", {})
    policy_thresholds = phase2_report["policy_thresholds"]
    budget = index.get("guardrails", {}).get("database_size_budget_guard", {})
    row = index.get("guardrails", {}).get("row_payload_guard", {})
    cleanup = index.get("guardrails", {}).get("retention_cleanup_guard", {})
    pool = index.get("guardrails", {}).get("connection_pool_budget_guard", {})
    rollback = index.get("guardrails", {}).get("rollback_verification_guard", {})

    scenario_results = {
        "migration_dry_run": _scenario(
            guardrails["source_refs_match"]
            and guardrails["schema_change_plan_static"]
            and runtime_policy["execute_migration"],
            (
                f"future_migration_id={schema_change.get('future_migration_id')}; "
                "sql_file_created=false; migration_executed=false; execute_migration=false."
            ),
            "migration dry-run 只验证 tracked contract 依赖和 future migration identity；本阶段不执行 live dry-run。",
        ),
        "repeat_execution": _scenario(
            bool(index.get("database_size_guard_contract_id"))
            and guardrails["schema_change_plan_static"]
            and runtime_policy["write_runtime_outputs"],
            (
                f"database_size_guard_contract_id={index.get('database_size_guard_contract_id')}; "
                "write_runtime_outputs=false."
            ),
            "重复执行依赖稳定 contract id 和无 runtime 写入，避免重复生成体积统计、cleanup output 或数据库状态。",
        ),
        "failure_rollback": _scenario(
            guardrails["rollback_verification_guard"]
            and guardrails["retention_cleanup_guard"]
            and runtime_policy["execute_migration"]
            and runtime_policy["execute_restore"],
            (
                "rollback_verification_guard=true; retention_cleanup_guard=true; "
                "execute_migration=false; execute_restore=false."
            ),
            "失败回滚依赖 STAGE-031 migration safety、backup/restore plan 和 owner stop gate；本阶段不执行 live rollback。",
        ),
        "recovery_smoke": _scenario(
            guardrails["rollback_verification_guard"]
            and guardrails["raw_metadata_boundary_guard"]
            and schema_change.get("recovery_smoke_executed") is False
            and runtime_policy["connect_to_postgres"],
            "recovery_smoke_executed=false; connect_to_postgres=false; raw boundary remains path-only.",
            "恢复冒烟在本阶段是静态 contract 验证，不写数据库、不连接 PostgreSQL、不触碰原始资料。",
        ),
        "raw_large_file_block": _scenario(
            guardrails["postgres_storage_scope_guard"]
            and guardrails["raw_content_block_guard"]
            and guardrails["large_file_block_guard"],
            "storage scope, raw content block, and large-file block guardrails all pass.",
            "PostgreSQL 不会写入 500GB 原始文件、raw database rows、source bodies、archives、report binaries 或 media blobs。",
        ),
        "ocr_full_text_block": _scenario(
            guardrails["ocr_full_text_block_guard"]
            and guardrails["row_payload_guard"],
            (
                f"max_control_plane_payload_bytes={row.get('max_control_plane_payload_bytes')}; "
                f"max_single_scalar_text_bytes={row.get('max_single_scalar_text_bytes')}; "
                "stores_ocr_full_text_allowed=false."
            ),
            "OCR 全文、document body、unbounded extracted text 和 chunk body text 必须保持在 PostgreSQL 之外。",
        ),
        "derived_artifact_limit": _scenario(
            guardrails["derived_artifact_limit_guard"]
            and runtime_policy["write_runtime_outputs"],
            "derived_artifact_limit_guard=true; write_runtime_outputs=false; only bounded refs are allowed.",
            "无限制派生产物不入库；允许的仅是 manifest/evidence/audit/report/source refs 和可重建有界 hot-index metadata。",
        ),
        "database_size_budget": _scenario(
            guardrails["database_size_budget_guard"]
            and runtime_policy["run_size_queries"]
            and policy_thresholds["measured_database_size_gib"] == "NOT_MEASURED_BY_POLICY",
            (
                f"internal_disk_budget_gib={budget.get('internal_disk_budget_gib')}; "
                f"warning_threshold_gib={budget.get('warning_threshold_gib')}; "
                f"hard_stop_threshold_gib={budget.get('hard_stop_threshold_gib')}; "
                "run_size_queries=false; measured_database_size_gib=NOT_MEASURED_BY_POLICY."
            ),
            "体积阈值用于保护 800GB 内置盘，但不是实测数据库大小；未来 live 检查必须单独授权。",
        ),
        "connection_pool_boundary": _scenario(
            guardrails["connection_pool_budget_guard"]
            and runtime_policy["connect_to_postgres"]
            and source_refs.get("stage032_connection_pool_index_ref")
            == "../database_connection_pool/stage032_connection_pool_index.json",
            (
                f"aggregate_max_pool_size={pool.get('aggregate_max_pool_size')}; "
                f"max_overflow={pool.get('max_overflow')}; connect_to_postgres=false."
            ),
            "体积护栏不能放大连接池；任何并发、overflow 或 backpressure 变化必须由 STAGE-032 合同解释。",
        ),
        "transaction_boundary": _scenario(
            source_refs.get("stage031_migration_safety_index_ref")
            == "../schema_migration_safety/stage031_migration_safety_index.json"
            and guardrails["connection_pool_budget_guard"]
            and guardrails["rollback_verification_guard"]
            and cleanup.get("cleanup_default_mode") == "dry_run_only"
            and rollback.get("requires_post_cleanup_verification") is True,
            (
                "Stage031 migration safety ref and Stage032 pool budget ref are present; "
                "cleanup_default_mode=dry_run_only; post_cleanup_verification=true."
            ),
            "事务边界通过上游 migration safety、连接池预算、dry-run cleanup 和 rollback verification 共同约束。",
        ),
        "constraint_error_explanations": _scenario(
            all(guardrails.get(key, False) for key in EXPLAINED_CONSTRAINTS),
            "All required database-size guard constraints have owner-facing explanations.",
            "约束错误必须能解释为存储范围、体积阈值、row payload、cleanup、连接池、回滚、raw boundary 或真实数据问题。",
            constraint_refs=list(EXPLAINED_CONSTRAINTS),
            explanations=EXPLAINED_CONSTRAINTS,
        ),
    }

    return {
        "schema_version": SCENARIO_SCHEMA_VERSION,
        "stage": STAGE,
        "phase": "Phase 3",
        "task_id": "IDS-V0_1-STAGE033-P3",
        "acceptance_id": ACCEPTANCE_ID,
        "scenario_results": scenario_results,
        "raw_metadata_boundary": phase2_report["raw_metadata_boundary"],
        "database_size_guard_index_ref": index_path.as_posix(),
        "does_not_connect_to_postgres": True,
        "does_not_execute_migration": True,
        "does_not_read_raw_metadata": True,
        "does_not_write_runtime_outputs": True,
        "does_not_use_fake_ids_business_data": True,
        "does_not_run_size_queries": True,
        "does_not_execute_cleanup": True,
    }


def build_stage033_delivery_report(index_path: Path) -> dict[str, Any]:
    index = _load_json(index_path)
    phase2_report = build_stage033_database_size_guard_report(index_path)
    scenario_report = build_stage033_scenario_validation_report(index_path)
    guardrails = phase2_report["guardrail_results"]
    runtime_policy = phase2_report["runtime_policy_results"]
    scenario_results = scenario_report["scenario_results"]
    source_refs = index.get("source_refs", {})
    budget = index.get("guardrails", {}).get("database_size_budget_guard", {})
    table = index.get("guardrails", {}).get("table_size_guard", {})
    bloat = index.get("guardrails", {}).get("index_bloat_guard", {})
    row = index.get("guardrails", {}).get("row_payload_guard", {})
    cleanup = index.get("guardrails", {}).get("retention_cleanup_guard", {})
    rollback = index.get("guardrails", {}).get("rollback_verification_guard", {})
    raw_boundary = index.get("guardrails", {}).get("raw_metadata_boundary", {})

    return {
        "schema_version": DELIVERY_SCHEMA_VERSION,
        "stage": STAGE,
        "phase": "Phase 4",
        "task_id": "IDS-V0_1-STAGE033-P4",
        "acceptance_id": ACCEPTANCE_ID,
        "next_gate": "IDS-STAGE033-REVIEW-GATE",
        "stage_review_status": "pending_next_run",
        "github_upload_allowed": False,
        "app_reinstall_allowed": False,
        "schema_diff": {
            "mode": "static_database_size_guard_contract_diff_not_executed",
            "baseline": "STAGE-033 Phase 2/3 tracked database-size guard index and scenario validation without Phase 4 closeout evidence",
            "target_database_size_guard_index_ref": index_path.as_posix(),
            "database_size_guard_contract_id": index.get("database_size_guard_contract_id"),
            "source_refs": source_refs,
            "guardrails_added": sorted(guardrails),
            "scenario_ids": sorted(scenario_results),
            "warning_threshold_gib": budget.get("warning_threshold_gib"),
            "hard_stop_threshold_gib": budget.get("hard_stop_threshold_gib"),
            "max_control_plane_table_gib": table.get("max_control_plane_table_gib"),
            "max_hot_index_table_gib": table.get("max_hot_index_table_gib"),
            "index_bloat_hard_stop_percent": bloat.get("hard_stop_percent"),
            "max_control_plane_payload_bytes": row.get("max_control_plane_payload_bytes"),
            "raw_payload_columns_added": [],
            "large_file_columns_added": [],
            "credential_fields_added": [],
            "notes": "This is a tracked-contract database-size guard diff only; no live PostgreSQL schema diff was executed.",
        },
        "migration_output": {
            "mode": "static_database_size_guard_migration_output_not_executed",
            "migration_dependency_ref": source_refs.get("stage031_migration_safety_index_ref"),
            "expected_static_result": "all Phase2 guardrail/runtime policy checks true; all Phase3 scenario statuses PASS",
            "guardrail_results": guardrails,
            "runtime_policy_results": runtime_policy,
            "scenario_results": scenario_results,
            "live_output_ref": "NOT_AVAILABLE_BY_POLICY_NO_LIVE_POSTGRESQL_CONNECTION",
        },
        "recovery_test_log": {
            "mode": "static_database_size_guard_recovery_log_not_executed",
            "checks": [
                "raw_metadata_boundary_path_only",
                "runtime_size_query_blocked",
                "cleanup_default_mode_dry_run_only",
                "auto_delete_blocked",
                "rollback_verification_required",
                "backup_restore_steps_defined",
                "post_cleanup_verification_required",
                "no_raw_or_ocr_payloads_in_postgres",
            ],
            "result": "static PASS from tracked database-size guard index and scenario validation contracts",
            "cleanup_default_mode": cleanup.get("cleanup_default_mode"),
            "requires_backup_restore_plan": rollback.get("requires_backup_restore_plan"),
            "requires_post_cleanup_verification": rollback.get("requires_post_cleanup_verification"),
            "live_restore_log_ref": "NOT_AVAILABLE_BY_POLICY_NO_BACKUP_OR_RESTORE_EXECUTION",
        },
        "destructive_migration_confirmation": {
            "required": True,
            "destructive_allowed_by_default": False,
            "current_contract_value": False,
            "manual_confirmation_required_before_change": True,
            "owner_message": "任何破坏性 schema 迁移、自动清理、retention deletion、VACUUM/reindex、raw/OCR/large-file 入库或体积阈值放宽必须单独人工确认，默认阻断。",
        },
        "rollback_steps": [
            "Stop before any live PostgreSQL connection, migration, size query, cleanup, VACUUM, reindex, backup, restore, or schema diff if the static contract cannot explain the storage scope, table/index/payload limits, cleanup gate, raw-boundary, real-data-only policy, or rollback verification.",
            "Revert the Phase 4 helper, closeout evidence, batch lock, roadmap/event updates, Stage005 validator/tests, Stage033 focused tests, compatibility tests, and rendered owner files only.",
            "Do not touch PostgreSQL data directories, DSN/secret stores, runtime outputs, app entries, GitHub PR state, or /Users/linzezhang/Downloads/IDS_MetaData.",
            "Keep database_size_guard_contract_id stable unless a future authorized stage explicitly changes the database size-guard contract.",
        ],
        "backup_restore_steps": [
            "Before any future live PostgreSQL migration, size-policy rollout, cleanup, VACUUM, reindex, retention deletion, or raw-payload storage change, create an owner-approved logical backup in a separate authorized run.",
            "Record backup location, checksum, migration id, dry-run evidence, database_size_guard_contract_id, and owner approval in future run evidence.",
            "If a future apply or cleanup fails, stop writes immediately and run the approved rollback command from the migration-safety contract with ON_ERROR_STOP=1 and single-transaction semantics where supported.",
            "Restore from the approved backup only in a future authorized restore run, then re-run safe healthcheck, size-budget verification, and raw metadata path-only checks.",
        ],
        "known_limits": [
            "PostgreSQL live connection, migration dry-run, apply, rollback, backup, restore, schema diff, size queries, VACUUM, reindex, cleanup, retention deletion, and recovery smoke were not executed in this phase.",
            "The report proves tracked database-size guard contract readiness, not production database readiness or measured runtime database size.",
            "No DSN, credential-bearing config, runtime database rows, document/chunk/job rows, indexes, reports, screenshots, PDFs, manifests, ledgers, audit logs, JSON output files, size statistics, cleanup outputs, or service state were generated.",
            "Raw metadata remains path-only at /Users/linzezhang/Downloads/IDS_MetaData and was not inspected.",
            "STAGE-033 review is blocked until a separate stage review run; BATCH031_040 upload remains blocked until STAGE-031..040 are complete, reviewed, and repaired.",
        ],
        "chinese_owner_feedback": (
            "STAGE-033 已完成 Phase 4：当前交付的是数据库体积护栏的静态工程合同、schema diff 摘要、"
            "migration 输出说明、恢复测试日志、已知限制、破坏性迁移人工确认、数据库回滚步骤、"
            "备份恢复步骤和中文反馈。它不是生产 PostgreSQL 连接、迁移、体积统计或清理授权；"
            "下一步应进入 STAGE-033 复审，而不是 GitHub upload 或 app reinstall。"
        ),
        "phase2_report": phase2_report,
        "scenario_report": scenario_report,
        "raw_metadata_boundary": {
            "path": raw_boundary.get("path"),
            "path_only": raw_boundary.get("path_only") is True,
            "no_raw_content_access": raw_boundary.get("content_access_allowed") is False,
            "copy_allowed": raw_boundary.get("copy_allowed") is True,
            "modify_allowed": raw_boundary.get("modify_allowed") is True,
            "dump_allowed": raw_boundary.get("dump_allowed") is True,
        },
        "does_not_connect_to_postgres": True,
        "does_not_execute_migration": True,
        "does_not_read_raw_metadata": True,
        "does_not_write_runtime_outputs": True,
        "does_not_use_fake_ids_business_data": True,
        "does_not_run_size_queries": True,
        "does_not_execute_cleanup": True,
    }


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    pursue_root = root / "docs" / "pursuing_goal" / "ids_v0_1"
    index_path = pursue_root / "database_size_guard" / "stage033_database_size_guard_index.json"
    report = build_stage033_database_size_guard_report(index_path)
    scenario_report = build_stage033_scenario_validation_report(index_path)
    delivery_report = build_stage033_delivery_report(index_path)
    print(
        json.dumps(
            {
                "database_size_guard_report": report,
                "scenario_report": scenario_report,
                "delivery_report": delivery_report,
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
            scenario["status"] == "PASS"
            for scenario in scenario_report["scenario_results"].values()
        ]
        + [
            report["index_schema_version"] == INDEX_SCHEMA_VERSION,
            report["does_not_connect_to_postgres"],
            report["does_not_execute_migration"],
            report["does_not_read_raw_metadata"],
            report["does_not_write_runtime_outputs"],
            report["does_not_use_fake_ids_business_data"],
            report["does_not_run_size_queries"],
            report["does_not_execute_cleanup"],
            delivery_report["schema_diff"]["mode"] == "static_database_size_guard_contract_diff_not_executed",
            delivery_report["migration_output"]["mode"] == "static_database_size_guard_migration_output_not_executed",
            delivery_report["recovery_test_log"]["mode"] == "static_database_size_guard_recovery_log_not_executed",
            delivery_report["stage_review_status"] == "pending_next_run",
            delivery_report["github_upload_allowed"] is False,
            delivery_report["app_reinstall_allowed"] is False,
            delivery_report["does_not_run_size_queries"],
            delivery_report["does_not_execute_cleanup"],
        ]
    )
    return 0 if all(checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
