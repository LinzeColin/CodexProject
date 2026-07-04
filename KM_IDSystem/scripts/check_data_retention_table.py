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
INDEX_SCHEMA_VERSION = "ids.stage034.data_retention_table.index.v1"
STAGE = "STAGE-034"
PHASE = "Phase 2"
TASK_ID = "IDS-V0_1-STAGE034-P2"
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


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


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
    print(
        json.dumps(
            {"data_retention_table_report": report},
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
        ]
    )
    return 0 if all(checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
