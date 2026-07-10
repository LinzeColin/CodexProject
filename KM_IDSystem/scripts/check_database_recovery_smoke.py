"""Validate the static IDS STAGE-035 database recovery smoke contract.

The checker reads Git-tracked contracts and prints JSON to stdout only. It does
not inspect a metadata dump, connect to PostgreSQL, execute restore commands, or
write runtime outputs.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "ids.stage035.database_recovery_smoke.phase2.v1"
SCENARIO_SCHEMA_VERSION = "ids.stage035.database_recovery_smoke.phase3.v1"
INDEX_SCHEMA_VERSION = "ids.stage035.database_recovery_smoke.index.v1"
STAGE = "STAGE-035"
TASK_ID = "IDS-V0_1-STAGE035-P2"
SCENARIO_TASK_ID = "IDS-V0_1-STAGE035-P3"
ACCEPTANCE_ID = "ACC-STAGE-035"
CONTRACT_ID = "ids_stage035_database_recovery_smoke_static_preflight"
RAW_METADATA_ROOT = "/Users/linzezhang/Downloads/IDS_MetaData"
BLOCKED_PENDING_DUMP = "BLOCKED_PENDING_OWNER_AUTHORIZED_REAL_METADATA_DUMP"
BLOCKED_INVALID_CONTRACT = "BLOCKED_INVALID_RECOVERY_CONTRACT"

EXPECTED_SOURCE_REFS = {
    "phase1_scope_ref": "../STAGE035_PHASE1_SCOPE_BOUNDARY.md",
    "stage030_control_plane_schema_ref": "../postgresql_control_plane/001_control_plane_schema.sql",
    "stage030_control_plane_index_ref": "../postgresql_control_plane/control_plane_schema_index.json",
    "stage030_control_plane_checker_ref": "../../../../scripts/check_postgresql_control_plane.py",
    "stage031_migration_safety_index_ref": "../schema_migration_safety/stage031_migration_safety_index.json",
    "stage031_migration_safety_checker_ref": "../../../../scripts/check_schema_migration_safety.py",
    "stage032_connection_pool_index_ref": "../database_connection_pool/stage032_connection_pool_index.json",
    "stage032_connection_pool_checker_ref": "../../../../scripts/check_database_connection_pool.py",
    "stage033_database_size_guard_index_ref": "../database_size_guard/stage033_database_size_guard_index.json",
    "stage033_database_size_guard_checker_ref": "../../../../scripts/check_database_size_guard.py",
    "stage034_data_retention_table_index_ref": "../data_retention_table/stage034_data_retention_table_index.json",
    "stage034_data_retention_table_checker_ref": "../../../../scripts/check_data_retention_table.py",
    "raw_data_boundary_ref": "../IDS_METADATA_RAW_DATA_BOUNDARY.md",
    "phase2_checker_ref": "../../../../scripts/check_database_recovery_smoke.py",
}

EXPECTED_CONTROL_PLANE_TABLES = {
    "ids_metadata_sources",
    "ids_jobs",
    "ids_documents",
    "ids_chunks",
    "ids_evidence_records",
    "ids_audit_events",
    "ids_index_versions",
    "ids_schema_migrations",
}

EXPECTED_DUMP_IDENTITY_REQUIREMENTS = {
    "owner_approval_ref",
    "metadata_dump_id",
    "bounded_content_scope",
    "source_database_ref",
    "source_schema_version",
    "migration_head",
    "dump_format",
    "postgres_tool_version",
    "created_at",
    "checksum_evidence_ref",
}

EXPECTED_PREFLIGHT_CHECKS = {
    "owner_authorized_real_dump",
    "dump_identity_complete",
    "checksum_evidence_valid",
    "dump_format_compatible",
    "postgres_tool_version_compatible",
    "schema_version_compatible",
    "migration_head_compatible",
    "bounded_storage_scope",
    "secret_ref_present_without_echo",
    "isolated_target_identity",
    "target_capacity_guard",
}

EXPECTED_VALIDATION_CHECKS = {
    "schema_version",
    "migration_ledger",
    "required_control_plane_tables",
    "constraints",
    "indexes",
    "bounded_real_metadata_counts",
    "audit_and_evidence_refs",
    "health_and_readiness",
    "no_raw_payloads",
    "source_non_interference",
}

EXPECTED_RUNTIME_POLICY_KEYS = {
    "read_metadata_dump",
    "hash_metadata_dump",
    "copy_metadata_dump",
    "connect_to_postgres",
    "create_restore_target",
    "create_database",
    "create_schema",
    "create_connection_config",
    "execute_pg_dump",
    "execute_pg_restore",
    "execute_psql",
    "execute_migration",
    "execute_backup",
    "execute_restore",
    "execute_schema_diff",
    "execute_healthcheck",
    "execute_constraint_checks",
    "execute_index_checks",
    "execute_row_count_checks",
    "execute_cleanup",
    "write_runtime_outputs",
    "read_raw_metadata",
    "write_raw_metadata",
    "install_dependencies",
    "start_services",
    "github_upload",
    "app_reinstall",
}

SCENARIO_EXPLANATIONS = {
    "migration_dry_run": "migration dry-run 只验证 STAGE-031 的静态要求和当前禁止执行状态；不连接 PostgreSQL，不运行 dry-run、apply、rollback、backup、restore 或 schema diff。",
    "repeat_execution": "重复执行只重新读取 Git 已追踪合同并输出 stdout JSON，不创建数据库行、文件、manifest、报告或 runtime artifact。",
    "failure_rollback": "失败回滚只验证 rollback、隔离目标、source preservation、backup checkpoint 和 post-rollback evidence 要求，不执行真实回滚或恢复。",
    "recovery_smoke": "无 owner 授权真实 metadata dump 时，恢复冒烟必须按预期阻断；场景 PASS 仅证明阻断合同有效，不代表执行过恢复。",
    "owner_dump_absence_stop_gate": "owner 授权真实 dump 身份、checksum evidence 和批准引用缺失时必须停止，禁止用 fake rows、fabricated dump 或 placeholder corpus 替代。",
    "raw_large_file_block": "PostgreSQL 只存有界控制面 metadata、状态和 refs，不存 500GB 原始文件、raw rows、OCR 全文、报告二进制或 vector payload。",
    "unbounded_derived_artifact_block": "无限制派生产物继续由 STAGE-033 体积护栏阻断，恢复合同不得覆盖该边界。",
    "connection_pool_boundary": "恢复验证不增加 STAGE-032 连接池预算，aggregate max pool 为 10、overflow 为 0，并保持 backpressure 和无连接状态。",
    "transaction_boundary": "事务边界只在 schema/migration/pool 静态合同层验证；当前不打开、提交或回滚真实数据库事务。",
    "constraint_error_explanations": "每个专项场景必须提供中文 owner 解释，区分合同通过、执行阻断、输入缺失和安全边界失败。",
    "source_non_interference": "恢复目标必须与 source database 分离；当前禁止 source migration、mutation、deletion 和任何真实 restore 写入。",
}


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _resolve_source_refs(index_path: Path, source_refs: dict[str, str]) -> dict[str, Path]:
    return {
        key: (index_path.parent / ref).resolve()
        for key, ref in source_refs.items()
    }


def _dependency_results(index_path: Path, index: dict[str, Any]) -> dict[str, bool]:
    source_refs = index.get("source_refs", {})
    dependency = index.get("dependency_contract", {})
    resolved = _resolve_source_refs(index_path, source_refs)

    required_dependency_keys = {
        "stage030_control_plane_index_ref",
        "stage031_migration_safety_index_ref",
        "stage032_connection_pool_index_ref",
        "stage033_database_size_guard_index_ref",
        "stage034_data_retention_table_index_ref",
    }
    if not required_dependency_keys.issubset(resolved):
        return {
            "source_refs_match": source_refs == EXPECTED_SOURCE_REFS,
            "source_refs_resolve": False,
            "stage030_control_plane_contract": False,
            "stage031_migration_safety_contract": False,
            "stage032_connection_pool_contract": False,
            "stage033_database_size_guard_contract": False,
            "stage034_data_retention_table_contract": False,
        }

    stage030 = _load_json(resolved["stage030_control_plane_index_ref"])
    stage031 = _load_json(resolved["stage031_migration_safety_index_ref"])
    stage032 = _load_json(resolved["stage032_connection_pool_index_ref"])
    stage033 = _load_json(resolved["stage033_database_size_guard_index_ref"])
    stage034 = _load_json(resolved["stage034_data_retention_table_index_ref"])

    stage030_storage = stage030.get("storage_boundary", {})
    stage030_migration = stage030.get("migration", {})
    stage031_recovery = stage031.get("recovery_smoke_guard", {})
    stage031_backup = stage031.get("backup_checkpoint_guard", {})
    stage031_rollback = stage031.get("rollback_guard", {})
    stage032_pool = stage032.get("guardrails", {}).get("pool_size_guard", {})
    stage032_storage = stage032.get("guardrails", {}).get("storage_boundary_guard", {})
    stage033_guards = stage033.get("guardrails", {})
    stage034_guards = stage034.get("guardrails", {})

    return {
        "source_refs_match": source_refs == EXPECTED_SOURCE_REFS,
        "source_refs_resolve": (
            len(resolved) == len(EXPECTED_SOURCE_REFS)
            and all(path.is_file() for path in resolved.values())
        ),
        "stage030_control_plane_contract": (
            stage030.get("schema_version") == dependency.get("stage030_schema_version")
            and set(stage030.get("required_tables", [])) == EXPECTED_CONTROL_PLANE_TABLES
            and stage030_migration.get("id") == dependency.get("stage030_migration_id")
            and stage030_migration.get("dry_run_required") is True
            and stage030_migration.get("rollback_required") is True
            and stage030_migration.get("destructive_allowed") is False
            and "500GB raw files" in stage030_storage.get("blocked_payloads", [])
            and "raw database rows" in stage030_storage.get("blocked_payloads", [])
        ),
        "stage031_migration_safety_contract": (
            stage031.get("schema_version") == dependency.get("stage031_schema_version")
            and stage031_recovery.get("required") is True
            and stage031_recovery.get("runtime_smoke_allowed") is False
            and stage031_backup.get("required") is True
            and stage031_backup.get("restore_ref_required") is True
            and stage031_rollback.get("required") is True
            and stage031_rollback.get("runtime_rollback_allowed") is False
        ),
        "stage032_connection_pool_contract": (
            stage032.get("schema_version") == dependency.get("stage032_schema_version")
            and stage032.get("connection_pool_contract_id")
            == dependency.get("stage032_connection_pool_contract_id")
            and stage032_pool.get("aggregate_max_pool_size") == 10
            and stage032_pool.get("max_overflow") == 0
            and stage032_pool.get("backpressure_required") is True
            and stage032_storage.get("stores_raw_files") is False
            and stage032_storage.get("stores_raw_database_rows") is False
        ),
        "stage033_database_size_guard_contract": (
            stage033.get("schema_version") == dependency.get("stage033_schema_version")
            and stage033.get("database_size_guard_contract_id")
            == dependency.get("stage033_database_size_guard_contract_id")
            and stage033_guards.get("raw_content_block_guard", {}).get(
                "stores_raw_content_allowed"
            )
            is False
            and stage033_guards.get("derived_artifact_limit_guard", {}).get(
                "unbounded_derived_artifacts_allowed"
            )
            is False
        ),
        "stage034_data_retention_table_contract": (
            stage034.get("schema_version") == dependency.get("stage034_schema_version")
            and stage034.get("data_retention_table_contract_id")
            == dependency.get("stage034_data_retention_table_contract_id")
            and stage034_guards.get("deletion_stop_gate_guard", {}).get(
                "destructive_action_allowed_by_default"
            )
            is False
            and stage034_guards.get("rollback_restore_guard", {}).get(
                "requires_backup_restore_plan"
            )
            is True
        ),
    }


def _contract_results(index: dict[str, Any]) -> dict[str, bool]:
    dependency = index.get("dependency_contract", {})
    metadata_dump = index.get("metadata_dump_contract", {})
    target = index.get("restore_target_contract", {})
    migration = index.get("schema_migration_compatibility", {})
    pool = index.get("connection_pool_guard", {})
    size = index.get("database_size_guard", {})
    quality = index.get("quality_constraint_guard", {})
    storage = index.get("storage_boundary", {})
    preflight = index.get("restore_preflight_contract", {})
    validation = index.get("restore_validation_contract", {})
    rollback = index.get("rollback_contract", {})
    audit = index.get("audit_contract", {})
    raw = index.get("raw_metadata_boundary", {})
    real_data = index.get("real_data_only_guard", {})
    forbidden = set(real_data.get("forbidden", []))

    return {
        "contract_identity_guard": (
            index.get("database_recovery_smoke_contract_id") == CONTRACT_ID
            and set(dependency.get("required_control_plane_tables", []))
            == EXPECTED_CONTROL_PLANE_TABLES
        ),
        "metadata_dump_contract_guard": (
            metadata_dump.get("owner_authorized_real_dump_required") is True
            and metadata_dump.get("owner_authorized_real_dump_available") is False
            and metadata_dump.get("metadata_dump_ref_recorded") is False
            and metadata_dump.get("dump_content_access_allowed") is False
            and metadata_dump.get("dump_bytes_committed") is False
            and metadata_dump.get("dump_path_committed") is False
            and metadata_dump.get("dump_checksum_computed_in_current_run") is False
            and metadata_dump.get("fabricated_dump_allowed") is False
            and metadata_dump.get("fake_rows_allowed") is False
            and metadata_dump.get("placeholder_corpus_allowed") is False
            and metadata_dump.get("execution_state") == BLOCKED_PENDING_DUMP
            and set(metadata_dump.get("identity_requirements", []))
            == EXPECTED_DUMP_IDENTITY_REQUIREMENTS
        ),
        "isolated_restore_target_guard": (
            target.get("isolated_non_production_target_required") is True
            and target.get("distinct_from_source_required") is True
            and target.get("production_target_allowed") is False
            and target.get("source_database_mutation_allowed") is False
            and target.get("source_database_migration_allowed") is False
            and target.get("source_database_deletion_allowed") is False
            and target.get("target_creation_allowed_in_current_run") is False
            and target.get("credential_bearing_config_in_git_allowed") is False
            and target.get("automatic_target_cleanup_allowed") is False
            and target.get("target_cleanup_owner_stop_gate_required") is True
        ),
        "schema_migration_compatibility_guard": (
            migration.get("mode") == "reuse_stage030_control_plane_schema_no_new_schema_change"
            and migration.get("new_schema_file_created") is False
            and migration.get("new_migration_file_created") is False
            and migration.get("connection_config_created") is False
            and migration.get("migration_executed") is False
            and migration.get("backup_executed") is False
            and migration.get("restore_executed") is False
            and migration.get("schema_diff_executed") is False
            and migration.get("dry_run_required_before_future_restore") is True
            and migration.get("rollback_required") is True
            and migration.get("backup_checkpoint_required") is True
            and migration.get("recovery_smoke_required") is True
            and migration.get("destructive_migration_allowed") is False
        ),
        "connection_pool_guard": (
            pool.get("stage032_guard_authoritative") is True
            and pool.get("aggregate_max_pool_size") == 10
            and pool.get("max_overflow") == 0
            and pool.get("backpressure_required") is True
            and pool.get("instantiate_connection_pool_allowed_in_current_run") is False
            and pool.get("plaintext_dsn_allowed") is False
            and pool.get("credential_echo_allowed") is False
        ),
        "database_size_guard": (
            size.get("stage033_guard_authoritative") is True
            and size.get("raw_large_ocr_payloads_blocked") is True
            and size.get("unbounded_derived_artifacts_blocked") is True
            and size.get("restore_does_not_override_size_guard") is True
            and size.get("runtime_size_query_allowed") is False
            and size.get("vacuum_allowed") is False
            and size.get("reindex_allowed") is False
        ),
        "quality_constraint_guard": (
            quality.get("required_tables_exact") is True
            and quality.get("schema_migration_ledger_required") is True
            and quality.get("constraint_validation_required") is True
            and quality.get("index_validation_required") is True
            and quality.get("bounded_real_metadata_count_comparison_required") is True
            and quality.get("source_non_interference_required") is True
            and quality.get("no_raw_payload_proof_required") is True
            and quality.get("chinese_failure_reason_required") is True
            and quality.get("runtime_validation_allowed_in_current_run") is False
        ),
        "storage_boundary_guard": (
            storage.get("stores_control_plane_metadata") is True
            and storage.get("stores_status_and_state") is True
            and storage.get("stores_hot_index_metadata") is True
            and storage.get("stores_raw_files") is False
            and storage.get("stores_raw_database_rows") is False
            and storage.get("stores_document_bodies") is False
            and storage.get("stores_ocr_full_text") is False
            and storage.get("stores_vector_payloads") is False
            and storage.get("stores_report_binaries") is False
            and storage.get("stores_unbounded_derived_artifacts") is False
        ),
        "restore_preflight_guard": (
            preflight.get("required") is True
            and set(preflight.get("required_checks", [])) == EXPECTED_PREFLIGHT_CHECKS
            and preflight.get("owner_authorized_real_dump_check_currently_passed") is False
            and preflight.get("execution_ready") is False
            and preflight.get("execution_state") == BLOCKED_PENDING_DUMP
        ),
        "restore_validation_guard": (
            validation.get("required") is True
            and set(validation.get("required_checks", [])) == EXPECTED_VALIDATION_CHECKS
            and validation.get("same_owner_approved_real_dump_evidence_required") is True
            and validation.get("fabricated_count_comparison_allowed") is False
            and validation.get("fake_row_fixture_allowed") is False
            and validation.get("runtime_validation_allowed_in_current_run") is False
        ),
        "rollback_guard": (
            rollback.get("fail_closed_required") is True
            and rollback.get("stop_further_writes_required") is True
            and rollback.get("isolated_target_quarantine_required") is True
            and rollback.get("source_preservation_required") is True
            and rollback.get("rollback_plan_ref_required") is True
            and rollback.get("post_rollback_verification_required") is True
            and rollback.get("automatic_target_deletion_allowed") is False
            and rollback.get("target_cleanup_owner_stop_gate_required") is True
            and rollback.get("runtime_rollback_allowed_in_current_run") is False
        ),
        "audit_guard": (
            audit.get("event_ref_required") is True
            and audit.get("evidence_ref_required") is True
            and audit.get("fact_level_required") is True
            and audit.get("actor_role_required") is True
            and audit.get("state_transition_required") is True
            and audit.get("chinese_owner_reason_required") is True
            and audit.get("runtime_audit_write_allowed_in_current_run") is False
        ),
        "raw_metadata_boundary_guard": (
            raw.get("path") == RAW_METADATA_ROOT
            and raw.get("path_only") is True
            and raw.get("content_access_allowed") is False
            and raw.get("recursive_listing_allowed") is False
            and raw.get("hashing_allowed") is False
            and raw.get("copy_allowed") is False
            and raw.get("modify_allowed") is False
            and raw.get("delete_allowed") is False
            and raw.get("dump_allowed") is False
            and raw.get("scan_allowed") is False
            and raw.get("normalize_allowed") is False
        ),
        "real_data_only_guard": {
            "fake IDS business data",
            "fake database rows",
            "fabricated metadata dump",
            "fake source documents",
            "placeholder corpus",
            "fabricated evidence",
            "plaintext secrets",
        }.issubset(forbidden),
        "phase_and_upload_gate_guard": (
            index.get("contract_state") == "STATIC_RECOVERY_PREFLIGHT_CONTRACT_VALID"
            and index.get("next_gate") == "IDS-STAGE035-P3-GATE"
            and index.get("github_upload_allowed") is False
            and index.get("app_reinstall_allowed") is False
        ),
    }


def _runtime_policy_results(index: dict[str, Any]) -> dict[str, bool]:
    runtime = index.get("runtime_policy", {})
    results = {
        key: runtime.get(key) is False
        for key in sorted(EXPECTED_RUNTIME_POLICY_KEYS)
    }
    results["keys_exact"] = set(runtime) == EXPECTED_RUNTIME_POLICY_KEYS
    return results


def _scenario_result(
    condition: bool,
    evidence: str,
    owner_explanation_zh: str,
    *,
    observed_state: str = "STATIC_CONTRACT_VALIDATED",
    expected_block: bool = False,
) -> dict[str, Any]:
    return {
        "status": "PASS" if condition else "FAIL",
        "evidence": evidence,
        "owner_explanation_zh": owner_explanation_zh,
        "observed_state": observed_state,
        "expected_block": expected_block,
        "live_execution_performed": False,
    }


def build_stage035_database_recovery_smoke_report(index_path: Path) -> dict[str, Any]:
    index = _load_json(index_path)
    dependency_results = _dependency_results(index_path, index)
    contract_results = _contract_results(index)
    runtime_policy_results = _runtime_policy_results(index)
    contract_valid = (
        index.get("schema_version") == INDEX_SCHEMA_VERSION
        and index.get("stage") == STAGE
        and index.get("task_id") == TASK_ID
        and index.get("acceptance_id") == ACCEPTANCE_ID
        and bool(runtime_policy_results)
        and all(dependency_results.values())
        and all(contract_results.values())
        and all(runtime_policy_results.values())
    )

    metadata_dump = index.get("metadata_dump_contract", {})
    execution_ready = bool(
        contract_valid
        and metadata_dump.get("owner_authorized_real_dump_available") is True
        and index.get("restore_preflight_contract", {}).get("execution_ready") is True
    )
    if not contract_valid:
        execution_state = BLOCKED_INVALID_CONTRACT
        block_reason_zh = "恢复工程合同无效，执行保持阻断。"
    elif not execution_ready:
        execution_state = BLOCKED_PENDING_DUMP
        block_reason_zh = "无 owner 授权真实 metadata dump，恢复执行保持阻断。"
    else:
        execution_state = "READY_FOR_SEPARATE_OWNER_AUTHORIZED_RECOVERY_RUN"
        block_reason_zh = ""

    return {
        "schema_version": SCHEMA_VERSION,
        "index_schema_version": index.get("schema_version"),
        "stage": STAGE,
        "phase": "Phase 2",
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "database_recovery_smoke_contract_id": index.get(
            "database_recovery_smoke_contract_id"
        ),
        "contract_valid": contract_valid,
        "execution_ready": execution_ready,
        "execution_state": execution_state,
        "block_reason_zh": block_reason_zh,
        "dependency_results": dependency_results,
        "contract_results": contract_results,
        "runtime_policy_results": runtime_policy_results,
        "required_control_plane_tables": sorted(EXPECTED_CONTROL_PLANE_TABLES),
        "raw_metadata_boundary": {
            "path": index.get("raw_metadata_boundary", {}).get("path"),
            "path_only": index.get("raw_metadata_boundary", {}).get("path_only") is True,
            "no_raw_content_access": index.get("raw_metadata_boundary", {}).get(
                "content_access_allowed"
            )
            is False,
        },
        "does_not_read_metadata_dump": runtime_policy_results.get(
            "read_metadata_dump", False
        ),
        "does_not_connect_to_postgres": runtime_policy_results.get(
            "connect_to_postgres", False
        ),
        "does_not_execute_restore": runtime_policy_results.get("execute_restore", False),
        "does_not_execute_migration": runtime_policy_results.get(
            "execute_migration", False
        ),
        "does_not_write_runtime_outputs": runtime_policy_results.get(
            "write_runtime_outputs", False
        ),
        "does_not_use_fake_ids_data": contract_results.get("real_data_only_guard", False)
        and contract_results.get("metadata_dump_contract_guard", False),
        "github_upload_allowed": index.get("github_upload_allowed"),
        "app_reinstall_allowed": index.get("app_reinstall_allowed"),
        "next_gate": index.get("next_gate"),
        "machine_index_ref": index_path.as_posix(),
    }


def build_stage035_scenario_validation_report(index_path: Path) -> dict[str, Any]:
    phase2_report = build_stage035_database_recovery_smoke_report(index_path)
    dependency = phase2_report["dependency_results"]
    contract = phase2_report["contract_results"]
    runtime = phase2_report["runtime_policy_results"]
    execution_state = phase2_report["execution_state"]

    scenario_results = {
        "migration_dry_run": _scenario_result(
            phase2_report["contract_valid"]
            and dependency["stage031_migration_safety_contract"]
            and contract["schema_migration_compatibility_guard"]
            and runtime["connect_to_postgres"]
            and runtime["execute_migration"]
            and runtime["execute_backup"]
            and runtime["execute_restore"]
            and runtime["execute_schema_diff"],
            "STAGE031 dry-run/rollback/backup requirements are present; all live migration, backup, restore, schema-diff, and PostgreSQL connection actions remain false",
            SCENARIO_EXPLANATIONS["migration_dry_run"],
        ),
        "repeat_execution": _scenario_result(
            phase2_report["contract_valid"]
            and dependency["source_refs_match"]
            and dependency["source_refs_resolve"]
            and runtime["write_runtime_outputs"]
            and runtime["read_metadata_dump"],
            "checker deterministically reads the same tracked index/dependencies and writes stdout JSON only",
            SCENARIO_EXPLANATIONS["repeat_execution"],
        ),
        "failure_rollback": _scenario_result(
            phase2_report["contract_valid"]
            and dependency["stage031_migration_safety_contract"]
            and contract["rollback_guard"]
            and contract["isolated_restore_target_guard"]
            and runtime["execute_backup"]
            and runtime["execute_restore"]
            and runtime["execute_migration"],
            "rollback/source-preservation/quarantine evidence is required while backup, restore, and migration execution remain false",
            SCENARIO_EXPLANATIONS["failure_rollback"],
        ),
        "recovery_smoke": _scenario_result(
            phase2_report["contract_valid"]
            and phase2_report["execution_ready"] is False
            and execution_state == BLOCKED_PENDING_DUMP
            and runtime["execute_pg_restore"]
            and runtime["execute_psql"]
            and runtime["execute_restore"]
            and runtime["execute_healthcheck"],
            "contract_valid=true, execution_ready=false, no restore/healthcheck actions, and execution state remains blocked pending an owner-authorized real metadata dump",
            SCENARIO_EXPLANATIONS["recovery_smoke"],
            observed_state=execution_state,
            expected_block=execution_state == BLOCKED_PENDING_DUMP,
        ),
        "owner_dump_absence_stop_gate": _scenario_result(
            phase2_report["contract_valid"]
            and contract["metadata_dump_contract_guard"]
            and contract["restore_preflight_guard"]
            and phase2_report["execution_ready"] is False
            and execution_state == BLOCKED_PENDING_DUMP,
            "owner_authorized_real_dump_available=false and preflight execution_ready=false",
            SCENARIO_EXPLANATIONS["owner_dump_absence_stop_gate"],
            observed_state=execution_state,
            expected_block=execution_state == BLOCKED_PENDING_DUMP,
        ),
        "raw_large_file_block": _scenario_result(
            phase2_report["contract_valid"]
            and dependency["stage030_control_plane_contract"]
            and dependency["stage033_database_size_guard_contract"]
            and contract["storage_boundary_guard"]
            and contract["raw_metadata_boundary_guard"]
            and runtime["read_raw_metadata"]
            and runtime["write_raw_metadata"],
            "STAGE030/STAGE033 storage guards pass; raw metadata remains path-only and raw read/write actions remain false",
            SCENARIO_EXPLANATIONS["raw_large_file_block"],
        ),
        "unbounded_derived_artifact_block": _scenario_result(
            phase2_report["contract_valid"]
            and dependency["stage033_database_size_guard_contract"]
            and contract["database_size_guard"]
            and contract["storage_boundary_guard"]
            and runtime["write_runtime_outputs"],
            "STAGE033 remains authoritative and stores_unbounded_derived_artifacts=false",
            SCENARIO_EXPLANATIONS["unbounded_derived_artifact_block"],
        ),
        "connection_pool_boundary": _scenario_result(
            phase2_report["contract_valid"]
            and dependency["stage032_connection_pool_contract"]
            and contract["connection_pool_guard"]
            and runtime["connect_to_postgres"]
            and runtime["create_connection_config"],
            "STAGE032 pool budget is authoritative; aggregate max=10, overflow=0, and no connection/config is created",
            SCENARIO_EXPLANATIONS["connection_pool_boundary"],
        ),
        "transaction_boundary": _scenario_result(
            phase2_report["contract_valid"]
            and contract["schema_migration_compatibility_guard"]
            and contract["connection_pool_guard"]
            and runtime["connect_to_postgres"]
            and runtime["execute_migration"]
            and runtime["execute_psql"],
            "schema/migration/pool contracts pass while PostgreSQL, migration, and psql execution remain false",
            SCENARIO_EXPLANATIONS["transaction_boundary"],
        ),
        "constraint_error_explanations": _scenario_result(
            phase2_report["contract_valid"]
            and set(SCENARIO_EXPLANATIONS)
            == {
                "migration_dry_run",
                "repeat_execution",
                "failure_rollback",
                "recovery_smoke",
                "owner_dump_absence_stop_gate",
                "raw_large_file_block",
                "unbounded_derived_artifact_block",
                "connection_pool_boundary",
                "transaction_boundary",
                "constraint_error_explanations",
                "source_non_interference",
            }
            and all(SCENARIO_EXPLANATIONS.values()),
            "all eleven required recovery-smoke scenarios have non-empty Chinese owner explanations",
            SCENARIO_EXPLANATIONS["constraint_error_explanations"],
        ),
        "source_non_interference": _scenario_result(
            phase2_report["contract_valid"]
            and contract["isolated_restore_target_guard"]
            and contract["rollback_guard"]
            and runtime["connect_to_postgres"]
            and runtime["execute_migration"]
            and runtime["execute_restore"],
            "isolated target and source preservation guards pass while all source-affecting execution remains false",
            SCENARIO_EXPLANATIONS["source_non_interference"],
        ),
    }

    scenario_validation_valid = bool(
        phase2_report["contract_valid"]
        and all(result["status"] == "PASS" for result in scenario_results.values())
        and scenario_results["recovery_smoke"]["observed_state"]
        == BLOCKED_PENDING_DUMP
        and scenario_results["recovery_smoke"]["expected_block"] is True
    )
    return {
        "schema_version": SCENARIO_SCHEMA_VERSION,
        "index_schema_version": phase2_report["index_schema_version"],
        "stage": STAGE,
        "phase": "Phase 3",
        "task_id": SCENARIO_TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "phase2_contract_valid": phase2_report["contract_valid"],
        "scenario_validation_valid": scenario_validation_valid,
        "scenario_results": scenario_results,
        "execution_ready": phase2_report["execution_ready"],
        "execution_state": execution_state,
        "block_reason_zh": phase2_report["block_reason_zh"],
        "execution_mode": "STATIC_TRACKED_CONTRACT_VALIDATION_ONLY",
        "live_execution_performed": False,
        "does_not_read_metadata_dump": phase2_report["does_not_read_metadata_dump"],
        "does_not_connect_to_postgres": phase2_report["does_not_connect_to_postgres"],
        "does_not_execute_restore": phase2_report["does_not_execute_restore"],
        "does_not_execute_migration": phase2_report["does_not_execute_migration"],
        "does_not_write_runtime_outputs": phase2_report["does_not_write_runtime_outputs"],
        "does_not_use_fake_ids_data": phase2_report["does_not_use_fake_ids_data"],
        "raw_metadata_boundary": phase2_report["raw_metadata_boundary"],
        "machine_index_ref": index_path.as_posix(),
        "next_gate": "IDS-STAGE035-P4-GATE",
        "github_upload_allowed": False,
        "app_reinstall_allowed": False,
    }


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    index_path = (
        root
        / "docs"
        / "pursuing_goal"
        / "ids_v0_1"
        / "database_recovery_smoke"
        / "stage035_database_recovery_smoke_index.json"
    )
    report = build_stage035_database_recovery_smoke_report(index_path)
    scenario_report = build_stage035_scenario_validation_report(index_path)
    payload = dict(report)
    payload["scenario_report"] = scenario_report
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2))
    checks = [
        report["contract_valid"],
        report["execution_ready"] is False,
        report["execution_state"] == BLOCKED_PENDING_DUMP,
        report["does_not_read_metadata_dump"],
        report["does_not_connect_to_postgres"],
        report["does_not_execute_restore"],
        report["does_not_execute_migration"],
        report["does_not_write_runtime_outputs"],
        report["does_not_use_fake_ids_data"],
        report["github_upload_allowed"] is False,
        report["app_reinstall_allowed"] is False,
        report["next_gate"] == "IDS-STAGE035-P3-GATE",
        scenario_report["scenario_validation_valid"],
        all(
            result["status"] == "PASS"
            for result in scenario_report["scenario_results"].values()
        ),
        scenario_report["execution_ready"] is False,
        scenario_report["execution_state"] == BLOCKED_PENDING_DUMP,
        scenario_report["live_execution_performed"] is False,
        scenario_report["next_gate"] == "IDS-STAGE035-P4-GATE",
        scenario_report["github_upload_allowed"] is False,
        scenario_report["app_reinstall_allowed"] is False,
    ]
    return 0 if all(checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
