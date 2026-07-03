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


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


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


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    pursue_root = root / "docs" / "pursuing_goal" / "ids_v0_1"
    index_path = pursue_root / "database_size_guard" / "stage033_database_size_guard_index.json"
    report = build_stage033_database_size_guard_report(index_path)
    print(
        json.dumps(
            {"database_size_guard_report": report},
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
            report["does_not_run_size_queries"],
            report["does_not_execute_cleanup"],
        ]
    )
    return 0 if all(checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
