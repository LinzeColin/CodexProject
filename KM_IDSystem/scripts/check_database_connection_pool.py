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
SCENARIO_SCHEMA_VERSION = "ids.stage032.database_connection_pool.phase3.v1"
DELIVERY_SCHEMA_VERSION = "ids.stage032.database_connection_pool.phase4.v1"
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

EXPLAINED_CONSTRAINTS = {
    "credential_guard": "连接凭证必须来自 ENV:IDS_POSTGRES_DSN 或批准的本地 secret store；提交明文 DSN、密码或云凭证必须阻断。",
    "pool_size_guard": "连接池总上限超过 10、出现 overflow 或无 backpressure 时必须停止并给出 owner-readable reason。",
    "timeout_guard": "statement、lock、idle 和 shutdown timeout 必须有上限，避免无限等待或占满本机资源。",
    "transaction_guard": "backend、worker、report task 和 retrieval task 必须有明确事务边界、rollback 和幂等要求。",
    "retry_backoff_guard": "重试必须有上限、backoff 和 non-retryable 分类，认证、schema、migration 或 raw boundary 错误不能盲目重试。",
    "healthcheck_guard": "healthcheck 只能验证安全 readiness，不得写数据库、echo secret 或触碰 raw metadata。",
    "storage_boundary_guard": "PostgreSQL 只能保存控制面 refs 和热索引 metadata，不得保存 raw files、raw database rows、正文、OCR、向量或报告二进制。",
    "raw_metadata_boundary_guard": "/Users/linzezhang/Downloads/IDS_MetaData 只能作为 path-only 边界记录，不得读取、列出、hash、复制、修改或 dump。",
    "real_data_only_guard": "系统只能使用真实 owner-approved 数据；fake IDS business data、fake rows、placeholder corpus 和 fabricated evidence 必须阻断。",
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


def build_stage032_scenario_validation_report(index_path: Path) -> dict[str, Any]:
    index = _load_json(index_path)
    phase2_report = build_stage032_connection_pool_report(index_path)
    profiles = phase2_report["profile_results"]
    guardrails = phase2_report["guardrail_results"]
    runtime_policy = phase2_report["runtime_policy_results"]
    source_refs = index.get("source_refs", {})
    retry_guard = index.get("guardrails", {}).get("retry_backoff_guard", {})
    healthcheck_guard = index.get("guardrails", {}).get("healthcheck_guard", {})
    storage_guard = index.get("guardrails", {}).get("storage_boundary_guard", {})
    pool_guard = index.get("guardrails", {}).get("pool_size_guard", {})
    timeout_guard = index.get("guardrails", {}).get("timeout_guard", {})

    scenario_results = {
        "migration_dry_run": _scenario(
            guardrails["source_refs_match"]
            and runtime_policy["execute_migration"]
            and "stage030_control_plane_schema_ref" in source_refs
            and "stage031_migration_safety_index_ref" in source_refs,
            "Stage030 schema and Stage031 migration-safety refs are present; runtime execute_migration=false.",
            "migration dry-run 只作为上游 tracked contract 依赖验证；本阶段不执行 live dry-run。",
        ),
        "repeat_execution": _scenario(
            bool(index.get("connection_pool_contract_id"))
            and guardrails["source_refs_match"]
            and runtime_policy["instantiate_connection_pool"],
            f"connection_pool_contract_id={index.get('connection_pool_contract_id')}; instantiate_connection_pool=false.",
            "重复执行必须由稳定 contract id、上游 migration identity 和无 runtime pool 行为共同约束。",
        ),
        "failure_rollback": _scenario(
            guardrails["transaction_guard"]
            and runtime_policy["execute_migration"]
            and "stage031_migration_safety_index_ref" in source_refs,
            "transaction_guard=true; Stage031 migration safety ref is present; execute_migration=false.",
            "失败回滚依赖 Stage031 的 rollback contract 和本阶段事务 rollback 要求；当前不执行 live rollback。",
        ),
        "recovery_smoke": _scenario(
            guardrails["healthcheck_guard"]
            and guardrails["raw_metadata_boundary_guard"]
            and healthcheck_guard.get("safe_healthcheck_only") is True
            and healthcheck_guard.get("writes_database") is False,
            "safe healthcheck contract is present; healthcheck writes_database=false and touches_raw_metadata=false.",
            "恢复冒烟只验证 future safe readiness contract，不写数据库、不触碰原始资料。",
        ),
        "raw_payload_block": _scenario(
            guardrails["storage_boundary_guard"]
            and guardrails["raw_metadata_boundary_guard"]
            and guardrails["real_data_only_guard"],
            "storage, raw metadata, and real-data-only guardrails all pass.",
            "数据库不会写入原始大文件、raw database rows、正文、OCR 全文、向量 payload、报告二进制、secrets 或 fake data。",
        ),
        "derived_output_limit": _scenario(
            runtime_policy["write_runtime_outputs"]
            and storage_guard.get("stores_report_binaries") is False
            and storage_guard.get("stores_vector_payloads") is False,
            "write_runtime_outputs=false; report binaries and vector payloads are blocked in storage boundary.",
            "派生产物必须保持有界、可重建、可解释；本阶段不生成 JSON output、report、PDF、audit log 或 index runtime 文件。",
        ),
        "connection_pool_boundary": _scenario(
            all(profiles.values())
            and guardrails["pool_size_guard"]
            and guardrails["timeout_guard"],
            f"aggregate_max_pool_size={pool_guard.get('aggregate_max_pool_size')}; statement_timeout_ms={timeout_guard.get('statement_timeout_ms')}; lock_timeout_ms={timeout_guard.get('lock_timeout_ms')}.",
            "后端、worker、报告任务和检索任务的连接池与 timeout 超限时必须进入可解释 stop reason。",
        ),
        "transaction_boundary": _scenario(
            guardrails["transaction_guard"]
            and guardrails["retry_backoff_guard"]
            and "raw_metadata_boundary_violation" in retry_guard.get("non_retryable_errors", []),
            "transaction_guard and retry_backoff_guard are true; raw_metadata_boundary_violation is non-retryable.",
            "事务边界、rollback、幂等与 non-retryable 错误分类必须先定义，不能用重试掩盖 schema 或 raw boundary 错误。",
        ),
        "constraint_error_explanations": _scenario(
            all(guardrails.get(key, False) for key in EXPLAINED_CONSTRAINTS),
            "All required guardrail ids have owner-facing explanations.",
            "约束错误必须能解释为凭证、连接池、timeout、事务、重试、healthcheck、存储、raw boundary 或真实数据问题。",
            constraint_refs=list(EXPLAINED_CONSTRAINTS),
            explanations=EXPLAINED_CONSTRAINTS,
        ),
    }

    return {
        "schema_version": SCENARIO_SCHEMA_VERSION,
        "stage": STAGE,
        "phase": "Phase 3",
        "task_id": "IDS-V0_1-STAGE032-P3",
        "acceptance_id": ACCEPTANCE_ID,
        "scenario_results": scenario_results,
        "raw_metadata_boundary": phase2_report["raw_metadata_boundary"],
        "connection_pool_index_ref": index_path.as_posix(),
        "does_not_connect_to_postgres": True,
        "does_not_execute_migration": True,
        "does_not_read_raw_metadata": True,
        "does_not_write_runtime_outputs": True,
        "does_not_use_fake_ids_business_data": True,
    }


def build_stage032_delivery_report(index_path: Path) -> dict[str, Any]:
    index = _load_json(index_path)
    phase2_report = build_stage032_connection_pool_report(index_path)
    scenario_report = build_stage032_scenario_validation_report(index_path)
    profiles = phase2_report["profile_results"]
    guardrails = phase2_report["guardrail_results"]
    runtime_policy = phase2_report["runtime_policy_results"]
    scenario_results = scenario_report["scenario_results"]
    source_refs = index.get("source_refs", {})
    pool_guard = index.get("guardrails", {}).get("pool_size_guard", {})
    timeout_guard = index.get("guardrails", {}).get("timeout_guard", {})
    retry_guard = index.get("guardrails", {}).get("retry_backoff_guard", {})
    healthcheck_guard = index.get("guardrails", {}).get("healthcheck_guard", {})
    storage_guard = index.get("guardrails", {}).get("storage_boundary_guard", {})
    raw_boundary = index.get("guardrails", {}).get("raw_metadata_boundary", {})

    return {
        "schema_version": DELIVERY_SCHEMA_VERSION,
        "stage": STAGE,
        "phase": "Phase 4",
        "task_id": "IDS-V0_1-STAGE032-P4",
        "acceptance_id": ACCEPTANCE_ID,
        "next_gate": "IDS-STAGE032-REVIEW-GATE",
        "stage_review_status": "pending_next_run",
        "github_upload_allowed": False,
        "app_reinstall_allowed": False,
        "schema_diff": {
            "mode": "static_connection_pool_contract_diff_not_executed",
            "baseline": "STAGE-032 Phase 2/3 tracked connection-pool index and scenario validation without Phase 4 closeout evidence",
            "target_connection_pool_index_ref": index_path.as_posix(),
            "connection_pool_contract_id": index.get("connection_pool_contract_id"),
            "source_refs": source_refs,
            "profiles_added": sorted(profiles),
            "guardrails_added": sorted(guardrails),
            "scenario_ids": sorted(scenario_results),
            "aggregate_max_pool_size": pool_guard.get("aggregate_max_pool_size"),
            "statement_timeout_ms": timeout_guard.get("statement_timeout_ms"),
            "raw_payload_columns_added": [],
            "credential_fields_added": [],
            "notes": "This is a tracked-contract connection-pool diff only; no live database schema diff was executed.",
        },
        "migration_output": {
            "mode": "static_connection_pool_migration_output_not_executed",
            "migration_dependency_ref": source_refs.get("stage031_migration_safety_index_ref"),
            "expected_static_result": "all Phase2 profiles/guardrails/runtime policy checks true; all Phase3 scenario statuses PASS",
            "profile_results": profiles,
            "guardrail_results": guardrails,
            "runtime_policy_results": runtime_policy,
            "scenario_results": scenario_results,
            "live_output_ref": "NOT_AVAILABLE_BY_POLICY_NO_LIVE_POSTGRESQL_CONNECTION",
        },
        "recovery_test_log": {
            "mode": "static_connection_pool_recovery_log_not_executed",
            "checks": [
                "safe_healthcheck_only",
                "healthcheck_writes_database_false",
                "raw_metadata_boundary_path_only",
                "transaction_rollback_required",
                "retry_non_retryable_raw_boundary_violation",
                "storage_boundary_no_raw_payloads",
                "backup_restore_steps_defined",
                "rollback_steps_defined",
            ],
            "result": "static PASS from tracked connection-pool index and scenario validation contracts",
            "healthcheck_future_query_ref": healthcheck_guard.get("future_query_ref"),
            "live_restore_log_ref": "NOT_AVAILABLE_BY_POLICY_NO_BACKUP_OR_RESTORE_EXECUTION",
        },
        "destructive_migration_confirmation": {
            "required": True,
            "destructive_allowed_by_default": False,
            "current_contract_value": False,
            "manual_confirmation_required_before_change": True,
            "non_retryable_ref": "destructive_migration_required"
            in retry_guard.get("non_retryable_errors", []),
            "owner_message": "任何破坏性 schema 迁移、连接池上限放大、raw payload 存储或凭证策略放宽必须单独人工确认，默认阻断。",
        },
        "rollback_steps": [
            "Stop before live database connection or pool rollout if the static contract cannot explain the schema, pool, timeout, transaction, retry, healthcheck, storage, raw-boundary, or real-data-only change.",
            "Revert the Phase 4 helper, closeout evidence, batch lock, roadmap/event updates, Stage005 validator/tests, Stage032 focused tests, compatibility tests, and rendered owner files only.",
            "Do not touch PostgreSQL data directories, DSN/secret stores, runtime outputs, app entries, GitHub PR state, or /Users/linzezhang/Downloads/IDS_MetaData.",
            "Keep connection_pool_contract_id stable unless a future authorized stage explicitly changes the pool contract.",
        ],
        "backup_restore_steps": [
            "Before any future live PostgreSQL migration or pool rollout, create an owner-approved logical backup in a separate authorized run.",
            "Record backup location, checksum, migration id, dry-run evidence, pool contract id, and owner approval in future run evidence.",
            "If a future apply fails, run the approved rollback command from the migration-safety contract with ON_ERROR_STOP=1 and single-transaction semantics where supported.",
            "Restore from the approved backup only in a future authorized restore run, then re-run safe healthcheck and keep raw metadata path-only.",
        ],
        "known_limits": [
            "PostgreSQL live connection, pool instantiation, migration dry-run, apply, rollback, backup, restore, and schema diff were not executed in this phase.",
            "The report proves tracked connection-pool contract readiness, not production database readiness.",
            "No DSN, credential-bearing config, runtime database rows, document/chunk/job rows, indexes, reports, screenshots, PDFs, manifests, ledgers, audit logs, JSON output files, or service state were generated.",
            "Raw metadata remains path-only at /Users/linzezhang/Downloads/IDS_MetaData and was not inspected.",
            "STAGE-032 review is blocked until a separate stage review run; BATCH031_040 upload remains blocked until STAGE-031..040 are complete, reviewed, and repaired.",
        ],
        "chinese_owner_feedback": (
            "STAGE-032 已完成 Phase 4：当前交付的是数据库连接与连接池基线的静态工程合同、"
            "schema diff 摘要、migration 输出说明、恢复测试日志、已知限制、破坏性迁移人工确认、"
            "数据库回滚步骤、备份恢复步骤和中文反馈。它不是生产 PostgreSQL 连接、迁移或连接池上线授权；"
            "下一步应进入 STAGE-032 复审，而不是 GitHub upload 或 app reinstall。"
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
    }


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    pursue_root = root / "docs" / "pursuing_goal" / "ids_v0_1"
    index_path = pursue_root / "database_connection_pool" / "stage032_connection_pool_index.json"
    report = build_stage032_connection_pool_report(index_path)
    scenario_report = build_stage032_scenario_validation_report(index_path)
    delivery_report = build_stage032_delivery_report(index_path)
    print(json.dumps(
        {
            "connection_pool_report": report,
            "scenario_report": scenario_report,
            "delivery_report": delivery_report,
        },
        ensure_ascii=False,
        sort_keys=True,
        indent=2,
    ))
    checks = (
        list(report["profile_results"].values())
        + list(report["guardrail_results"].values())
        + list(report["runtime_policy_results"].values())
        + [
            scenario["status"] == "PASS"
            for scenario in scenario_report["scenario_results"].values()
        ]
        + [
            delivery_report["schema_diff"]["mode"] == "static_connection_pool_contract_diff_not_executed",
            delivery_report["migration_output"]["mode"] == "static_connection_pool_migration_output_not_executed",
            delivery_report["recovery_test_log"]["mode"] == "static_connection_pool_recovery_log_not_executed",
            delivery_report["stage_review_status"] == "pending_next_run",
            delivery_report["github_upload_allowed"] is False,
            delivery_report["app_reinstall_allowed"] is False,
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
