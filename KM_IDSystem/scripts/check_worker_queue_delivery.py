#!/usr/bin/env python3
"""Build the fail-closed STAGE-038 Phase 4 delivery report."""

from __future__ import annotations

import asyncio
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any, Mapping, Optional


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PURSUE_ROOT = PROJECT_ROOT / "docs" / "pursuing_goal" / "ids_v0_1"
INDEX_PATH = (
    PURSUE_ROOT
    / "worker_queue_baseline"
    / "stage038_worker_queue_delivery_contract.json"
)
SCENARIO_CHECKER_PATH = PROJECT_ROOT / "scripts" / "check_worker_queue_scenarios.py"

INDEX_SCHEMA_VERSION = "ids.stage038.worker_queue_baseline.phase4.index.v1"
REPORT_SCHEMA_VERSION = "ids.stage038.worker_queue_baseline.phase4.report.v1"
DELIVERY_SCHEMA_VERSION = "ids.stage038.worker_queue_baseline.delivery.v1"
TASK_ID = "IDS-V0_1-STAGE038-P4"
ACCEPTANCE_ID = "ACC-STAGE-038"
EXECUTION_MODE = "ISOLATED_NON_PRODUCTION_CLOSEOUT_EVIDENCE"
VALID_RESULT = "PASS_ISOLATED_CLOSEOUT_PRODUCTION_DISABLED"
NEXT_GATE = "IDS-STAGE038-REVIEW-GATE"
PHASE4_GATE = "IDS-STAGE038-P4-GATE"
STAGE_REVIEW_STATUS = "pending_next_run"
SECOND_CONTROL_INPUT_REF = (
    "repo:KM_IDSystem/docs/pursuing_goal/ids_v0_1/"
    "STAGE038_PHASE1_SOURCE_REVERIFICATION.md"
)

EXPECTED_SOURCE_BINDINGS = {
    "stage037_state_index_ref": {
        "path": (
            "docs/pursuing_goal/ids_v0_1/job_state_model/"
            "stage037_job_state_model_index.json"
        ),
        "sha256": "b70bf72ebe4212f45d380c13fbfe429791e1f4a5c73dccbba81211b7adc1c2d3",
    },
    "phase2_index_ref": {
        "path": (
            "docs/pursuing_goal/ids_v0_1/worker_queue_baseline/"
            "stage038_worker_queue_baseline_index.json"
        ),
        "sha256": "68513591996a51fea90cd2ea863f42f910c0c3a45b70fd1611655bb6d95911ab",
    },
    "phase2_evidence_ref": {
        "path": (
            "docs/pursuing_goal/ids_v0_1/"
            "STAGE038_PHASE2_ASYNC_WORKER_QUEUE_SLICE.md"
        ),
        "sha256": "14ba679970ba5d56ab12874ecb4cd63f160c726c281bc952eb67db342fd13073",
    },
    "phase3_checker_ref": {
        "path": "scripts/check_worker_queue_scenarios.py",
        "sha256": "b7e335039ecf65e4fe91df39e91cddd296296852bd3be8923237b8616db9517c",
    },
    "phase3_index_ref": {
        "path": (
            "docs/pursuing_goal/ids_v0_1/worker_queue_baseline/"
            "stage038_worker_queue_scenarios.json"
        ),
        "sha256": "0ec9f1a0de6ec24d64d4108214ea426f9171b15eebdd6c3c60693fade62f2961",
    },
    "phase3_evidence_ref": {
        "path": (
            "docs/pursuing_goal/ids_v0_1/"
            "STAGE038_PHASE3_WORKER_QUEUE_SCENARIOS.md"
        ),
        "sha256": "8cc8c205aaca316a7abf1cbd714a13aac3463bc5dc004ceba43b9078250fcbe3",
    },
}
ELIGIBLE_ARTIFACT_CLASSES = ["TEMPORARY_PARTIAL_OUTPUT", "REBUILDABLE_CACHE"]
PROTECTED_ARTIFACT_CLASSES = [
    "ORIGINAL_RAW_DATA",
    "FACT_SOURCE",
    "MANIFEST",
    "EVIDENCE_LEDGER",
    "REPORT_SNAPSHOT",
    "AUDIT_LOG",
    "ACTIVE_INDEX",
    "REQUIRED_CHECKPOINT",
]
CLEANUP_PRECONDITIONS = [
    "APPROVED_ROOT_IDENTITY",
    "ROOT_RELATIVE_PATH",
    "IMMUTABLE_LSTAT_IDENTITY",
    "SYMLINK_BLOCKED",
    "EXCLUSIVE_NAMESPACE_LOCK",
    "WRITER_QUIESCENCE",
    "NO_FOLLOW_TRAVERSAL",
]
MANUAL_ACTION_CASES = [
    "WORKER_EXCEPTION",
    "EXTERNAL_DRIVE_OFFLINE",
    "LOW_DISK",
    "QUEUE_CAPACITY_REACHED",
    "SAME_SOURCE_CONFLICT",
    "PROCESS_RESTART",
]
SAFE_SHUTDOWN_STEPS = [
    "STOP_NEW_ADMISSION",
    "DRAIN_ACCEPTED_CONTROL_WORK",
    "VERIFY_TERMINAL_STATE_AND_RELEASED_LOCKS",
    "STOP_ISOLATED_WORKER",
]
ROLLBACK_STEPS = [
    "STOP_ON_INVALID_DELIVERY_CONTRACT",
    "REVERT_PHASE4_FILES_ONLY",
    "PRESERVE_PHASE1_PHASE3_EVIDENCE",
    "PRESERVE_RAW_DATA_AND_DURABLE_EVIDENCE",
]
KNOWN_LIMITS = [
    "NO_PERSISTENT_QUEUE_OR_CLAIM",
    "NO_AUTOMATIC_RETRY_OR_DEAD_LETTER_RUNTIME",
    "NO_MEASURED_BACKPRESSURE_OR_FAIRNESS_RUNTIME",
    "NO_PRODUCTION_LOCK_LEASE_OR_FENCING",
    "NO_AUTOMATIC_LIFECYCLE_OR_PROCESS_RECOVERY",
    "NO_CLEANUP_RUNTIME",
    "NO_DATABASE_OR_RAW_SOURCE_ACCESS",
    "STATIC_CLOSEOUT_IS_NOT_PRODUCTION_READINESS",
]
ZERO_SIDE_EFFECT_FIELDS = (
    "production_runtime_activation_performed",
    "claim_persistence_performed",
    "persistent_queue_write_performed",
    "retry_scheduler_performed",
    "dead_letter_runtime_performed",
    "measured_backpressure_runtime_performed",
    "production_lock_runtime_performed",
    "automatic_lifecycle_runtime_performed",
    "crash_recovery_runtime_performed",
    "cleanup_runtime_performed",
    "database_connection_performed",
    "schema_change_performed",
    "state_registry_write_performed",
    "runtime_output_written",
    "ids_business_source_read_performed",
    "external_api_call_performed",
    "raw_metadata_content_accessed",
    "fake_ids_business_data_used",
    "real_ids_business_job_created",
    "whole_stage_review_performed",
    "github_upload_allowed",
    "app_reinstall_allowed",
)
INDEX_FIELDS = {
    "schema_version",
    "stage",
    "phase",
    "task_id",
    "acceptance_id",
    "source_bindings",
    "delivery_contract",
    "cleanup_allowlist",
    "recovery_boundary",
    "rollback_contract",
    "known_limits",
    "truth_contract",
}
DELIVERY_CONTRACT_FIELDS = {
    "schema_version",
    "execution_mode",
    "valid_result",
    "stage_review_status",
    "next_gate",
    "state_model_version",
    "required_job_type_count",
    "required_job_state_count",
    "required_transition_count",
    "failure_retry_log_mode",
    "baseline_max_retries",
    "capacity_backpressure_result",
    "external_api_budget_insufficient_result",
    "resource_conflict_result",
}
CLEANUP_ALLOWLIST_FIELDS = {
    "eligible_artifact_classes",
    "protected_artifact_classes",
    "cleanup_manifest_required",
    "required_preconditions",
    "runtime_owner",
    "delete_execution_allowed",
}
RECOVERY_BOUNDARY_FIELDS = {
    "automatic_recovery_cases",
    "manual_action_required_cases",
    "safe_shutdown_steps",
    "persistent_recovery_available",
    "automatic_resume_allowed",
    "same_operation_resubmission_available",
    "same_operation_resubmission_owner",
    "crash_recovery_runtime_owner",
    "automatic_lifecycle_runtime_owner",
}
ROLLBACK_CONTRACT_FIELDS = {"steps", "destructive_rollback_allowed"}

_SCENARIO_MODULE: Any = None


def _load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _scenario_module() -> Any:
    global _SCENARIO_MODULE
    if _SCENARIO_MODULE is None:
        _SCENARIO_MODULE = _load_module(
            SCENARIO_CHECKER_PATH,
            "stage038_worker_queue_scenarios_for_delivery",
        )
    return _SCENARIO_MODULE


def _baseline_module() -> Any:
    return _scenario_module()._baseline_module()


def _parse_yaml_text(text: str) -> dict[str, Any]:
    return _scenario_module()._parse_yaml_text(text)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _load_index() -> dict[str, Any]:
    parsed = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    return parsed if isinstance(parsed, dict) else {}


def _source_integrity(index: Mapping[str, Any]) -> tuple[dict[str, bool], dict[str, str]]:
    bindings = index.get("source_bindings")
    bindings = bindings if isinstance(bindings, dict) else {}
    checks: dict[str, bool] = {}
    observed: dict[str, str] = {}
    for name, expected in EXPECTED_SOURCE_BINDINGS.items():
        actual = bindings.get(name)
        path = PROJECT_ROOT / expected["path"]
        digest = _sha256_file(path) if path.is_file() else ""
        observed[name] = digest
        checks[name] = actual == expected and digest == expected["sha256"]
    checks["exact_source_binding_keys"] = set(bindings) == set(
        EXPECTED_SOURCE_BINDINGS
    )
    return checks, observed


def _contract_checks(index: Mapping[str, Any]) -> dict[str, bool]:
    delivery = index.get("delivery_contract")
    delivery = delivery if isinstance(delivery, dict) else {}
    cleanup = index.get("cleanup_allowlist")
    cleanup = cleanup if isinstance(cleanup, dict) else {}
    recovery = index.get("recovery_boundary")
    recovery = recovery if isinstance(recovery, dict) else {}
    rollback = index.get("rollback_contract")
    rollback = rollback if isinstance(rollback, dict) else {}
    truth = index.get("truth_contract")
    truth = truth if isinstance(truth, dict) else {}
    source_checks, _ = _source_integrity(index)
    try:
        phase3_contract = _scenario_module().build_stage038_phase3_report(
            execute_scenarios=False
        )
    except (OSError, RuntimeError, ValueError, json.JSONDecodeError):
        phase3_contract = {}
    return {
        "contract_shape_exact": (
            set(index) == INDEX_FIELDS
            and set(delivery) == DELIVERY_CONTRACT_FIELDS
            and set(cleanup) == CLEANUP_ALLOWLIST_FIELDS
            and set(recovery) == RECOVERY_BOUNDARY_FIELDS
            and set(rollback) == ROLLBACK_CONTRACT_FIELDS
            and set(truth) == set(ZERO_SIDE_EFFECT_FIELDS)
        ),
        "identity_exact": (
            index.get("schema_version") == INDEX_SCHEMA_VERSION
            and index.get("stage") == "STAGE-038"
            and index.get("phase") == "Phase 4"
            and index.get("task_id") == TASK_ID
            and index.get("acceptance_id") == ACCEPTANCE_ID
        ),
        "source_integrity_exact": all(source_checks.values()),
        "phase3_contract_valid": phase3_contract.get("contract_valid") is True,
        "delivery_contract_exact": (
            delivery.get("schema_version") == DELIVERY_SCHEMA_VERSION
            and delivery.get("execution_mode") == EXECUTION_MODE
            and delivery.get("valid_result") == VALID_RESULT
            and delivery.get("stage_review_status") == STAGE_REVIEW_STATUS
            and delivery.get("next_gate") == NEXT_GATE
            and delivery.get("state_model_version") == "ids.job_state.v1"
            and delivery.get("required_job_type_count") == 8
            and delivery.get("required_job_state_count") == 11
            and delivery.get("required_transition_count") == 21
            and delivery.get("failure_retry_log_mode")
            == "ACTUAL_ISOLATED_FAILURE_NO_RETRY_RUNTIME"
            and delivery.get("baseline_max_retries") == 0
            and delivery.get("capacity_backpressure_result")
            == "QUEUE_CAPACITY_REACHED"
            and delivery.get("external_api_budget_insufficient_result")
            == "PAUSED_EXTERNAL_API_BUDGET_INSUFFICIENT"
            and delivery.get("resource_conflict_result")
            == "RESOURCE_CONFLICT_ACTIVE"
        ),
        "cleanup_allowlist_exact": (
            cleanup.get("eligible_artifact_classes") == ELIGIBLE_ARTIFACT_CLASSES
            and cleanup.get("protected_artifact_classes")
            == PROTECTED_ARTIFACT_CLASSES
            and cleanup.get("cleanup_manifest_required") is True
            and cleanup.get("required_preconditions") == CLEANUP_PRECONDITIONS
            and cleanup.get("runtime_owner") == "STAGE-044"
            and cleanup.get("delete_execution_allowed") is False
        ),
        "recovery_boundary_exact": (
            recovery.get("automatic_recovery_cases") == []
            and recovery.get("manual_action_required_cases")
            == MANUAL_ACTION_CASES
            and recovery.get("safe_shutdown_steps") == SAFE_SHUTDOWN_STEPS
            and recovery.get("persistent_recovery_available") is False
            and recovery.get("automatic_resume_allowed") is False
            and recovery.get("same_operation_resubmission_available") is False
            and recovery.get("same_operation_resubmission_owner") == "STAGE-039"
            and recovery.get("crash_recovery_runtime_owner") == "STAGE-043"
            and recovery.get("automatic_lifecycle_runtime_owner") == "STAGE-042"
        ),
        "rollback_contract_exact": (
            rollback.get("steps") == ROLLBACK_STEPS
            and rollback.get("destructive_rollback_allowed") is False
        ),
        "known_limits_exact": index.get("known_limits") == KNOWN_LIMITS,
        "truth_contract_exact": (
            set(truth) == set(ZERO_SIDE_EFFECT_FIELDS)
            and all(truth.get(field) is False for field in ZERO_SIDE_EFFECT_FIELDS)
        ),
    }


def _job_state_graph() -> dict[str, Any]:
    state_model = copy.deepcopy(
        _baseline_module()._stage037_module().load_contract()["state_model"]
    )
    allowed = state_model["allowed_transitions"]
    flattened = [
        {"source": source, "target": target}
        for source, targets in allowed.items()
        for target in targets
    ]
    mermaid_lines = ["stateDiagram-v2"]
    mermaid_lines.extend(
        f"    {edge['source']} --> {edge['target']}" for edge in flattened
    )
    return {
        "authority": "STAGE-037",
        "state_model_version": state_model["state_model_version"],
        "job_types": state_model["job_types"],
        "job_states": state_model["job_states"],
        "terminal_states": state_model["terminal_states"],
        "active_execution_states": state_model["active_execution_states"],
        "allowed_transitions": allowed,
        "allowed_transitions_flat": flattened,
        "allowed_transition_count": len(flattened),
        "mermaid_state_diagram": "\n".join(mermaid_lines),
        "state_registry_write_performed": False,
    }


async def _capacity_backpressure_proof() -> dict[str, Any]:
    baseline = _baseline_module()
    queue = baseline.IsolatedWorkerQueue(capacity=1)
    first = queue.submit(
        baseline.build_control_envelope(baseline.CONTROL_INPUT_REF, job_type="PARSE")
    )
    blocked = queue.submit(
        baseline.build_control_envelope(SECOND_CONTROL_INPUT_REF, job_type="INDEX")
    )
    record_count = queue.record_count
    await queue.shutdown()
    return {
        "first_admission_accepted": first.get("accepted") is True,
        "result_code": blocked.get("result_code"),
        "owner_status": blocked.get("owner_status"),
        "queue_record_count": record_count,
        "worker_started": False,
        "persistent_queue_write_performed": False,
    }


async def _safe_shutdown_proof() -> dict[str, Any]:
    baseline = _baseline_module()
    queue = baseline.IsolatedWorkerQueue(capacity=1)
    acknowledgement = queue.submit(
        baseline.build_control_envelope(baseline.CONTROL_INPUT_REF, job_type="PARSE")
    )
    await queue.start()
    await asyncio.wait_for(queue.shutdown(), timeout=2.0)
    final_record = queue.get_record(acknowledgement["queue_entry_ref"])
    all_locks_released = all(
        not lock.locked() for lock in queue._resource_locks.values()
    )
    post_shutdown = queue.submit(
        baseline.build_control_envelope(SECOND_CONTROL_INPUT_REF, job_type="INDEX")
    )
    return {
        "steps": copy.deepcopy(SAFE_SHUTDOWN_STEPS),
        "final_record": final_record,
        "queue_closed": queue._closed is True,
        "all_resource_locks_released": all_locks_released,
        "post_shutdown_submission": post_shutdown,
        "active_work_cancelled": False,
        "automatic_shutdown_runtime_performed": False,
        "persistent_recovery_available": False,
    }


def _failure_retry_log(phase3_report: Mapping[str, Any]) -> dict[str, Any]:
    scenario = phase3_report["scenario_results"][
        "worker_crash_exception_and_lock_release"
    ]
    failed_record = scenario["failed_record"]
    return {
        "mode": "ACTUAL_ISOLATED_FAILURE_NO_RETRY_RUNTIME",
        "actual_isolated_worker_exception_observed": (
            scenario.get("status") == "PASS"
            and failed_record.get("machine_state") == "FAILED"
        ),
        "state_history": copy.deepcopy(failed_record["state_history"]),
        "error_ref": failed_record["error_ref"],
        "output_refs": copy.deepcopy(failed_record["output_refs"]),
        "checkpoint_ref": failed_record["checkpoint_ref"],
        "transition_audit": copy.deepcopy(failed_record["transition_audit"]),
        "baseline_max_retries": 0,
        "retry_disposition": (
            "NOT_AVAILABLE_BASELINE_MAX_RETRIES_ZERO_STAGE039_OWNED"
        ),
        "owner_action": (
            "REVIEW_ERROR_NO_SAME_OPERATION_RESUBMISSION_UNTIL_STAGE039"
        ),
        "same_operation_resubmission_available": scenario[
            "same_operation_resubmission_available"
        ],
        "same_operation_resubmission_result": scenario[
            "same_operation_resubmission_decision"
        ]["result_code"],
        "automatic_retry_performed": False,
        "retry_scheduler_performed": False,
        "dead_letter_runtime_performed": False,
    }


def _backpressure_trigger_proof(
    phase3_report: Mapping[str, Any],
    capacity: Mapping[str, Any],
) -> dict[str, Any]:
    scenarios = phase3_report["scenario_results"]
    conflict = scenarios["same_source_cross_operation_lock"]
    return {
        "capacity": copy.deepcopy(dict(capacity)),
        "external_drive_offline": copy.deepcopy(
            scenarios["external_drive_offline_pause_before_queue"]
        ),
        "low_disk": copy.deepcopy(
            scenarios["actual_low_disk_boundary_pause_without_allocation"]
        ),
        "external_api_budget_insufficient": copy.deepcopy(
            scenarios["external_api_budget_insufficient_pause_before_queue"]
        ),
        "same_source_conflict": copy.deepcopy(conflict["decisions"][1]),
        "measured_backpressure_runtime_performed": False,
        "automatic_resume_performed": False,
        "runtime_owner": "STAGE-040",
    }


def _cleanup_allowlist(phase3_report: Mapping[str, Any]) -> dict[str, Any]:
    protected = phase3_report["scenario_results"]["protected_cleanup_denied"]
    checks = {
        artifact_class: (
            decision.get("result_code") == "PROTECTED_ARTIFACT"
            and decision.get("delete_allowed") is False
            and decision.get("delete_attempted") is False
        )
        for artifact_class, decision in protected["artifact_results"].items()
    }
    return {
        "eligible_artifact_classes": copy.deepcopy(ELIGIBLE_ARTIFACT_CLASSES),
        "protected_artifact_classes": copy.deepcopy(PROTECTED_ARTIFACT_CLASSES),
        "cleanup_manifest_required": True,
        "required_preconditions": copy.deepcopy(CLEANUP_PRECONDITIONS),
        "phase3_protected_ref_checks": checks,
        "runtime_owner": "STAGE-044",
        "cleanup_runtime_performed": False,
        "delete_attempt_performed": False,
    }


def _recovery_handling() -> dict[str, Any]:
    return {
        "automatic_recovery_cases": [],
        "manual_action_required_cases": copy.deepcopy(MANUAL_ACTION_CASES),
        "manual_action_contract": {
            "WORKER_EXCEPTION": (
                "REVIEW_ERROR_NO_SAME_OPERATION_RESUBMISSION_UNTIL_STAGE039"
            ),
            "EXTERNAL_DRIVE_OFFLINE": "RECONNECT_AND_OWNER_REVALIDATE",
            "LOW_DISK": "RESTORE_CAPACITY_AND_OWNER_REVALIDATE",
            "QUEUE_CAPACITY_REACHED": "WAIT_AND_RESUBMIT_AFTER_CAPACITY_REVIEW",
            "SAME_SOURCE_CONFLICT": "WAIT_FOR_TERMINAL_HOLDER_AND_RESUBMIT",
            "PROCESS_RESTART": "RECREATE_QUEUE_AND_NEW_JOB_FROM_DURABLE_SOURCE_REF",
        },
        "persistent_recovery_available": False,
        "automatic_resume_allowed": False,
        "same_operation_resubmission_available": False,
        "same_operation_resubmission_owner": "STAGE-039",
        "crash_recovery_runtime_performed": False,
        "automatic_lifecycle_runtime_performed": False,
        "crash_recovery_runtime_owner": "STAGE-043",
        "automatic_lifecycle_runtime_owner": "STAGE-042",
    }


def _delivery_checks(
    graph: Mapping[str, Any],
    failure: Mapping[str, Any],
    backpressure: Mapping[str, Any],
    cleanup: Mapping[str, Any],
    recovery: Mapping[str, Any],
    shutdown: Mapping[str, Any],
    phase2_report: Mapping[str, Any],
    phase3_report: Mapping[str, Any],
) -> dict[str, bool]:
    return {
        "phase2_contract_and_slice_valid": (
            phase2_report.get("contract_valid") is True
            and phase2_report.get("slice_valid") is True
        ),
        "phase3_contract_and_scenarios_valid": (
            phase3_report.get("contract_valid") is True
            and phase3_report.get("scenario_validation_valid") is True
        ),
        "state_graph_exact": (
            graph.get("state_model_version") == "ids.job_state.v1"
            and len(graph.get("job_types", [])) == 8
            and len(graph.get("job_states", [])) == 11
            and graph.get("allowed_transition_count") == 21
        ),
        "failure_retry_log_truthful": (
            failure.get("actual_isolated_worker_exception_observed") is True
            and failure.get("error_ref") == "error:RuntimeError"
            and failure.get("same_operation_resubmission_available") is False
            and failure.get("same_operation_resubmission_result")
            == "EXISTING_QUEUE_ENTRY"
            and failure.get("automatic_retry_performed") is False
        ),
        "capacity_backpressure_proved": (
            backpressure.get("capacity", {}).get("result_code")
            == "QUEUE_CAPACITY_REACHED"
            and backpressure.get("capacity", {}).get("worker_started") is False
        ),
        "resource_and_lock_backpressure_proved": (
            backpressure.get("external_drive_offline", {}).get("result_code")
            == "PAUSED_EXTERNAL_DRIVE_OFFLINE"
            and backpressure.get("low_disk", {}).get("result_code")
            == "PAUSED_LOW_DISK"
            and backpressure.get("external_api_budget_insufficient", {}).get(
                "result_code"
            )
            == "PAUSED_EXTERNAL_API_BUDGET_INSUFFICIENT"
            and backpressure.get("same_source_conflict", {}).get("result_code")
            == "RESOURCE_CONFLICT_ACTIVE"
        ),
        "cleanup_allowlist_narrow_and_protected": (
            cleanup.get("eligible_artifact_classes")
            == ELIGIBLE_ARTIFACT_CLASSES
            and all(cleanup.get("phase3_protected_ref_checks", {}).values())
            and cleanup.get("cleanup_runtime_performed") is False
        ),
        "recovery_boundary_manual_and_fail_closed": (
            recovery.get("automatic_recovery_cases") == []
            and recovery.get("manual_action_required_cases")
            == MANUAL_ACTION_CASES
            and recovery.get("persistent_recovery_available") is False
            and recovery.get("same_operation_resubmission_available") is False
            and recovery.get("same_operation_resubmission_owner") == "STAGE-039"
        ),
        "orderly_shutdown_proved": (
            shutdown.get("final_record", {}).get("machine_state") == "SUCCEEDED"
            and shutdown.get("queue_closed") is True
            and shutdown.get("all_resource_locks_released") is True
            and shutdown.get("post_shutdown_submission", {}).get("result_code")
            == "QUEUE_CLOSED"
        ),
    }


def build_stage038_phase4_delivery_report(
    *,
    index: Optional[dict[str, Any]] = None,
    execute_delivery_checks: bool = True,
) -> dict[str, Any]:
    load_error: Optional[str] = None
    if index is None:
        try:
            contract = _load_index()
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            contract = {}
            load_error = f"{type(exc).__name__}: {exc}"
    else:
        contract = copy.deepcopy(index) if isinstance(index, dict) else {}
        if not isinstance(index, dict):
            load_error = "index must be a JSON object"

    checks = _contract_checks(contract)
    source_integrity, observed_hashes = _source_integrity(contract)
    contract_valid = load_error is None and all(checks.values())
    report: dict[str, Any] = {
        "schema_version": REPORT_SCHEMA_VERSION,
        "stage": "STAGE-038",
        "phase": "Phase 4",
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "execution_mode": EXECUTION_MODE,
        "contract_valid": contract_valid,
        "contract_checks": checks,
        "source_integrity": source_integrity,
        "observed_source_sha256": observed_hashes,
        "load_error": load_error,
        "delivery_checks_performed": False,
        "delivery_check_results": {},
        "delivery_contract_valid": False,
        "result": "FAIL_CLOSED",
        "execution_ready": False,
        "execution_state": (
            "CONTRACT_VALID_DELIVERY_CHECKS_NOT_EXECUTED"
            if contract_valid and not execute_delivery_checks
            else "BLOCKED_INVALID_PHASE4_CONTRACT"
        ),
        "stage_review_status": (
            "blocked_invalid_delivery_contract"
            if not contract_valid
            else "blocked_delivery_checks_not_executed"
        ),
        "next_gate": PHASE4_GATE,
        "job_state_graph": {},
        "failure_retry_log": {},
        "backpressure_trigger_proof": {},
        "cleanup_allowlist": {},
        "recovery_handling": {},
        "safe_shutdown": {},
        "rollback_steps": copy.deepcopy(ROLLBACK_STEPS),
        "known_limits": copy.deepcopy(KNOWN_LIMITS),
        "isolated_queue_runtime_performed": False,
        "actual_worker_exception_performed": False,
        "actual_disk_observation_performed": False,
        **{field: False for field in ZERO_SIDE_EFFECT_FIELDS},
        "owner_feedback_zh": (
            "Worker 队列 Phase 4 合同无效；保持失败关闭，未执行交付检查。"
            if not contract_valid
            else "Worker 队列 Phase 4 合同有效；交付检查尚未执行。"
        ),
    }
    if not contract_valid or not execute_delivery_checks:
        return report

    try:
        phase2_report = _baseline_module().build_stage038_phase2_report()
        phase3_report = _scenario_module().build_stage038_phase3_report()
        graph = _job_state_graph()
        failure = _failure_retry_log(phase3_report)
        capacity = asyncio.run(_capacity_backpressure_proof())
        backpressure = _backpressure_trigger_proof(phase3_report, capacity)
        cleanup = _cleanup_allowlist(phase3_report)
        recovery = _recovery_handling()
        shutdown = asyncio.run(_safe_shutdown_proof())
        delivery_checks = _delivery_checks(
            graph,
            failure,
            backpressure,
            cleanup,
            recovery,
            shutdown,
            phase2_report,
            phase3_report,
        )
    except (OSError, RuntimeError, ValueError, KeyError, asyncio.TimeoutError) as exc:
        report["load_error"] = f"{type(exc).__name__}: {exc}"
        report["execution_state"] = "BLOCKED_PHASE4_DELIVERY_CHECK_FAILED"
        report["stage_review_status"] = "blocked_delivery_check_failed"
        report["next_gate"] = PHASE4_GATE
        report["owner_feedback_zh"] = (
            "Worker 队列 Phase 4 交付检查失败；生产运行、恢复与清理继续禁用。"
        )
        return report

    delivery_valid = all(delivery_checks.values())
    report.update(
        {
            "delivery_checks_performed": True,
            "delivery_check_results": delivery_checks,
            "delivery_contract_valid": delivery_valid,
            "result": VALID_RESULT if delivery_valid else "FAIL_CLOSED",
            "execution_state": (
                "ISOLATED_CLOSEOUT_VALID_PRODUCTION_DISABLED"
                if delivery_valid
                else "BLOCKED_INVALID_DELIVERY_EVIDENCE"
            ),
            "job_state_graph": graph,
            "failure_retry_log": failure,
            "backpressure_trigger_proof": backpressure,
            "cleanup_allowlist": cleanup,
            "recovery_handling": recovery,
            "safe_shutdown": shutdown,
            "stage_review_status": (
                STAGE_REVIEW_STATUS
                if delivery_valid
                else "blocked_invalid_delivery_evidence"
            ),
            "next_gate": NEXT_GATE if delivery_valid else PHASE4_GATE,
            "phase2_report": phase2_report,
            "phase3_report": phase3_report,
            "isolated_queue_runtime_performed": True,
            "actual_worker_exception_performed": True,
            "actual_disk_observation_performed": True,
            "owner_feedback_zh": (
                "Worker 队列 Phase 4 隔离交付证据已通过；自动恢复、生产运行和清理"
                "仍禁用，下一轮必须先做整阶段复审。"
                if delivery_valid
                else "Worker 队列 Phase 4 交付证据未通过；保持失败关闭。"
            ),
        }
    )
    return report


def main() -> int:
    report = build_stage038_phase4_delivery_report()
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0 if report["delivery_contract_valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
