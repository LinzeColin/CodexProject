"""Static checks for IDS STAGE-032 database connection-pool baseline.

This module validates tracked connection-pool contracts only. It does not
connect to PostgreSQL, execute migrations, inspect raw metadata, instantiate
connection pools, or write runtime outputs.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "ids.stage032.database_connection_pool.phase2.v1"
INDEX_SCHEMA_VERSION = "ids.stage032.database_connection_pool.index.v1"
STAGE = "STAGE-032"
PHASE = "Phase 2"
TASK_ID = "IDS-V0_1-STAGE032-P2"
ACCEPTANCE_ID = "ACC-STAGE-032"
RAW_METADATA_ROOT = "/Users/linzezhang/Downloads/IDS_MetaData"

REQUIRED_PROFILES = [
    "backend_connection_profile",
    "worker_connection_profile",
    "report_task_connection_profile",
    "retrieval_task_connection_profile",
]

EXPECTED_SOURCE_REFS = {
    "phase1_scope_ref": "../STAGE032_PHASE1_SCOPE_BOUNDARY.md",
    "stage030_control_plane_schema_ref": "../postgresql_control_plane/001_control_plane_schema.sql",
    "stage030_control_plane_index_ref": "../postgresql_control_plane/control_plane_schema_index.json",
    "stage031_migration_safety_index_ref": "../schema_migration_safety/stage031_migration_safety_index.json",
    "stage031_migration_safety_checker_ref": "../../../../scripts/check_schema_migration_safety.py",
}


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _profile_valid(profile: dict[str, Any], guardrails: dict[str, Any]) -> bool:
    pool_guard = guardrails.get("pool_size_guard", {})
    timeout_guard = guardrails.get("timeout_guard", {})
    credential_guard = guardrails.get("credential_guard", {})
    return (
        profile.get("connection_url_ref") == credential_guard.get("connection_url_ref") == "ENV:IDS_POSTGRES_DSN"
        and profile.get("credential_source_policy") == "environment_or_approved_local_secret_store"
        and int(profile.get("min_pool_size", -1)) >= 0
        and int(profile.get("max_pool_size", 0)) > 0
        and int(profile.get("max_pool_size", 0)) <= int(pool_guard.get("max_pool_size", 0))
        and int(profile.get("max_overflow", -1)) <= int(pool_guard.get("max_overflow", -1))
        and int(profile.get("statement_timeout_ms", 0)) <= int(timeout_guard.get("statement_timeout_ms", 0))
        and int(profile.get("lock_timeout_ms", 0)) <= int(timeout_guard.get("lock_timeout_ms", 0))
        and int(profile.get("idle_timeout_ms", 0)) <= int(timeout_guard.get("idle_timeout_ms", 0))
        and bool(profile.get("transaction_boundary"))
        and bool(profile.get("retry_policy"))
        and bool(profile.get("healthcheck_mode"))
        and profile.get("stores_raw_content") is False
        and profile.get("uses_plaintext_credentials") is False
        and profile.get("runtime_execution_allowed") is False
    )


def _profile_results(index: dict[str, Any]) -> dict[str, bool]:
    profiles = index.get("connection_profiles", {})
    guardrails = index.get("guardrails", {})
    return {
        profile_name: isinstance(profiles.get(profile_name), dict)
        and _profile_valid(profiles[profile_name], guardrails)
        for profile_name in REQUIRED_PROFILES
    }


def _guardrail_results(index: dict[str, Any]) -> dict[str, bool]:
    guardrails = index.get("guardrails", {})
    profiles = index.get("connection_profiles", {})
    credential_guard = guardrails.get("credential_guard", {})
    pool_guard = guardrails.get("pool_size_guard", {})
    timeout_guard = guardrails.get("timeout_guard", {})
    transaction_guard = guardrails.get("transaction_guard", {})
    retry_guard = guardrails.get("retry_backoff_guard", {})
    healthcheck_guard = guardrails.get("healthcheck_guard", {})
    storage_guard = guardrails.get("storage_boundary_guard", {})
    raw_boundary = guardrails.get("raw_metadata_boundary", {})
    real_data_guard = guardrails.get("real_data_only_guard", {})
    source_refs = index.get("source_refs", {})
    aggregate_pool_size = sum(int(profile.get("max_pool_size", 0)) for profile in profiles.values())
    forbidden = real_data_guard.get("forbidden", [])

    return {
        "source_refs_match": source_refs == EXPECTED_SOURCE_REFS,
        "credential_guard": (
            credential_guard.get("connection_url_ref") == "ENV:IDS_POSTGRES_DSN"
            and credential_guard.get("secrets_forbidden") is True
            and credential_guard.get("plaintext_dsn_forbidden") is True
            and credential_guard.get("cloud_credentials_forbidden") is True
            and credential_guard.get("committed_connection_config_allowed") is False
        ),
        "pool_size_guard": (
            int(pool_guard.get("max_pool_size", 0)) <= 10
            and int(pool_guard.get("aggregate_max_pool_size", 0)) <= 10
            and aggregate_pool_size <= int(pool_guard.get("aggregate_max_pool_size", 0))
            and int(pool_guard.get("max_overflow", -1)) == 0
            and pool_guard.get("unbounded_pool_allowed") is False
            and pool_guard.get("backpressure_required") is True
        ),
        "timeout_guard": (
            int(timeout_guard.get("statement_timeout_ms", 0)) <= 30000
            and int(timeout_guard.get("lock_timeout_ms", 0)) <= 5000
            and int(timeout_guard.get("idle_timeout_ms", 0)) <= 60000
            and int(timeout_guard.get("shutdown_timeout_ms", 0)) <= 15000
        ),
        "transaction_guard": (
            transaction_guard.get("fail_fast_required") is True
            and transaction_guard.get("rollback_required") is True
            and transaction_guard.get("request_scoped_transactions_required") is True
            and transaction_guard.get("worker_job_scoped_transactions_required") is True
            and transaction_guard.get("report_task_idempotency_required") is True
            and transaction_guard.get("retrieval_batch_guard_required") is True
        ),
        "retry_backoff_guard": (
            int(retry_guard.get("max_attempts", 0)) <= 3
            and retry_guard.get("exponential_backoff_required") is True
            and retry_guard.get("owner_stop_reason_required") is True
            and "raw_metadata_boundary_violation" in retry_guard.get("non_retryable_errors", [])
        ),
        "healthcheck_guard": (
            healthcheck_guard.get("safe_healthcheck_only") is True
            and healthcheck_guard.get("touches_raw_metadata") is False
            and healthcheck_guard.get("writes_database") is False
            and healthcheck_guard.get("requires_secret_echo") is False
            and "SELECT 1" in str(healthcheck_guard.get("future_query_ref", ""))
        ),
        "storage_boundary_guard": (
            storage_guard.get("stores_control_plane_refs") is True
            and storage_guard.get("stores_hot_index_metadata") is True
            and storage_guard.get("stores_raw_files") is False
            and storage_guard.get("stores_raw_database_rows") is False
            and storage_guard.get("stores_document_bodies") is False
            and storage_guard.get("stores_ocr_full_text") is False
            and storage_guard.get("stores_vector_payloads") is False
            and storage_guard.get("stores_report_binaries") is False
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
        "instantiate_connection_pool": runtime_policy.get("instantiate_connection_pool") is False,
        "write_runtime_outputs": runtime_policy.get("write_runtime_outputs") is False,
        "read_raw_metadata": runtime_policy.get("read_raw_metadata") is False,
        "install_dependencies": runtime_policy.get("install_dependencies") is False,
        "start_services": runtime_policy.get("start_services") is False,
        "github_upload": runtime_policy.get("github_upload") is False,
        "app_reinstall": runtime_policy.get("app_reinstall") is False,
    }


def build_stage032_connection_pool_report(index_path: Path) -> dict[str, Any]:
    index = _load_json(index_path)
    guardrails = index.get("guardrails", {})
    raw_boundary = guardrails.get("raw_metadata_boundary", {})
    return {
        "schema_version": SCHEMA_VERSION,
        "index_schema_version": index.get("schema_version"),
        "stage": STAGE,
        "phase": PHASE,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "connection_pool_contract_id": index.get("connection_pool_contract_id"),
        "profile_results": _profile_results(index),
        "guardrail_results": _guardrail_results(index),
        "runtime_policy_results": _runtime_policy_results(index),
        "raw_metadata_boundary": {
            "path": raw_boundary.get("path"),
            "path_only": raw_boundary.get("path_only") is True,
            "no_raw_content_access": raw_boundary.get("content_access_allowed") is False,
        },
        "connection_pool_index_ref": index_path.as_posix(),
        "does_not_connect_to_postgres": True,
        "does_not_execute_migration": True,
        "does_not_read_raw_metadata": True,
        "does_not_write_runtime_outputs": True,
        "does_not_use_fake_ids_business_data": True,
    }


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    pursue_root = root / "docs" / "pursuing_goal" / "ids_v0_1"
    index_path = pursue_root / "database_connection_pool" / "stage032_connection_pool_index.json"
    report = build_stage032_connection_pool_report(index_path)
    print(json.dumps(
        {"connection_pool_report": report},
        ensure_ascii=False,
        sort_keys=True,
        indent=2,
    ))
    checks = (
        list(report["profile_results"].values())
        + list(report["guardrail_results"].values())
        + list(report["runtime_policy_results"].values())
        + [
            report["index_schema_version"] == INDEX_SCHEMA_VERSION,
            report["does_not_connect_to_postgres"],
            report["does_not_execute_migration"],
            report["does_not_read_raw_metadata"],
            report["does_not_write_runtime_outputs"],
            report["does_not_use_fake_ids_business_data"],
        ]
    )
    return 0 if all(checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
