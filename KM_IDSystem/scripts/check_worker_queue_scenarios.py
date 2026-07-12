#!/usr/bin/env python3
"""Validate isolated STAGE-038 Phase 3 worker-queue scenarios."""

from __future__ import annotations

import asyncio
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
from typing import Any, Mapping, Optional


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PROJECT_ROOT.parent
PURSUE_ROOT = PROJECT_ROOT / "docs" / "pursuing_goal" / "ids_v0_1"
INDEX_PATH = (
    PURSUE_ROOT
    / "worker_queue_baseline"
    / "stage038_worker_queue_scenarios.json"
)
BASELINE_CHECKER_PATH = PROJECT_ROOT / "scripts" / "check_worker_queue_baseline.py"

INDEX_SCHEMA_VERSION = "ids.stage038.worker_queue_baseline.phase3.index.v1"
REPORT_SCHEMA_VERSION = "ids.stage038.worker_queue_baseline.phase3.report.v1"
TASK_ID = "IDS-V0_1-STAGE038-P3"
ACCEPTANCE_ID = "ACC-STAGE-038"
NEXT_GATE = "IDS-STAGE038-P4-GATE"
EXECUTION_MODE = "ISOLATED_NON_PRODUCTION_WORKER_QUEUE_SCENARIOS"
CONTROL_INPUT_REF = (
    "repo:KM_IDSystem/docs/pursuing_goal/ids_v0_1/"
    "STAGE038_PHASE1_WORKER_QUEUE_SCOPE_BOUNDARY.md"
)
EXPECTED_SCENARIOS = (
    "duplicate_click_one_execution",
    "worker_crash_exception_and_lock_release",
    "external_drive_offline_pause_before_queue",
    "actual_low_disk_boundary_pause_without_allocation",
    "external_api_budget_insufficient_pause_before_queue",
    "same_source_cross_operation_lock",
    "protected_cleanup_denied",
)
CONFLICTING_JOB_TYPES = ("ARCHIVE", "PARSE", "INDEX", "REPORT")
EXPECTED_SOURCE_BINDINGS = {
    "phase2_checker_ref": {
        "path": "scripts/check_worker_queue_baseline.py",
        "sha256": "88a29aff19ee2465d6d5192c4fd9c352f85240689fede3a2216a754a1853e0f9",
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
}
EXPECTED_PROTECTED_ARTIFACTS = {
    "FACT_SOURCE": CONTROL_INPUT_REF,
    "EVIDENCE_LEDGER": (
        "repo:KM_IDSystem/docs/pursuing_goal/ids_v0_1/"
        "worker_queue_baseline/stage038_worker_queue_baseline_index.json"
    ),
    "REPORT_SNAPSHOT": (
        "repo:KM_IDSystem/docs/pursuing_goal/ids_v0_1/"
        "STAGE038_PHASE2_ASYNC_WORKER_QUEUE_SLICE.md"
    ),
    "AUDIT_LOG": "repo:KM_IDSystem/docs/governance/events.jsonl",
}
ZERO_SIDE_EFFECT_FIELDS = (
    "production_runtime_activation_performed",
    "persistent_queue_write_performed",
    "database_connection_performed",
    "schema_change_performed",
    "state_registry_write_performed",
    "runtime_output_written",
    "ids_business_source_read_performed",
    "external_api_call_performed",
    "raw_metadata_content_accessed",
    "fake_ids_business_data_used",
    "real_ids_business_job_created",
    "physical_drive_removal_performed",
    "disk_allocation_performed",
    "cleanup_runtime_performed",
    "protected_ref_delete_performed",
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
    "scenario_contract",
    "lock_contract",
    "resource_gate_contract",
    "cleanup_contract",
    "truth_contract",
}
SCENARIO_CONTRACT_FIELDS = {
    "execution_mode",
    "scenario_ids",
    "control_input_ref",
    "physical_drive_event_required",
    "disk_allocation_allowed",
    "cleanup_execution_allowed",
}
LOCK_CONTRACT_FIELDS = {
    "resource_identity_derivation",
    "job_identity_derivation",
    "conflicting_job_types",
    "resource_conflict_result",
    "terminal_record_releases_admission_conflict",
    "production_lock_runtime_owner",
}
RESOURCE_GATE_CONTRACT_FIELDS = {
    "external_drive_offline_result",
    "low_disk_result",
    "external_api_budget_insufficient_result",
    "pause_before_queue_record",
    "actual_disk_observation_required",
    "physical_drive_removal_claim_allowed",
    "external_api_call_required",
}
CLEANUP_CONTRACT_FIELDS = {
    "protected_artifacts",
    "protected_result",
    "delete_attempt_allowed",
    "runtime_owner",
}

_BASELINE_MODULE: Any = None


def _load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _baseline_module() -> Any:
    global _BASELINE_MODULE
    if _BASELINE_MODULE is None:
        _BASELINE_MODULE = _load_module(
            BASELINE_CHECKER_PATH,
            "stage038_worker_queue_baseline_for_phase3",
        )
    return _BASELINE_MODULE


def _parse_yaml_text(text: str) -> dict[str, Any]:
    return _baseline_module()._parse_yaml_text(text)


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
    scenario = index.get("scenario_contract")
    scenario = scenario if isinstance(scenario, dict) else {}
    lock = index.get("lock_contract")
    lock = lock if isinstance(lock, dict) else {}
    resource = index.get("resource_gate_contract")
    resource = resource if isinstance(resource, dict) else {}
    cleanup = index.get("cleanup_contract")
    cleanup = cleanup if isinstance(cleanup, dict) else {}
    truth = index.get("truth_contract")
    truth = truth if isinstance(truth, dict) else {}
    source_checks, _ = _source_integrity(index)
    try:
        baseline_report = _baseline_module().build_stage038_phase2_report(
            execute_slice=False
        )
    except (OSError, RuntimeError, ValueError, json.JSONDecodeError):
        baseline_report = {}
    return {
        "contract_shape_exact": (
            set(index) == INDEX_FIELDS
            and set(scenario) == SCENARIO_CONTRACT_FIELDS
            and set(lock) == LOCK_CONTRACT_FIELDS
            and set(resource) == RESOURCE_GATE_CONTRACT_FIELDS
            and set(cleanup) == CLEANUP_CONTRACT_FIELDS
            and set(truth) == set(ZERO_SIDE_EFFECT_FIELDS)
        ),
        "identity_exact": (
            index.get("schema_version") == INDEX_SCHEMA_VERSION
            and index.get("stage") == "STAGE-038"
            and index.get("phase") == "Phase 3"
            and index.get("task_id") == TASK_ID
            and index.get("acceptance_id") == ACCEPTANCE_ID
        ),
        "source_integrity_exact": all(source_checks.values()),
        "phase2_contract_valid": baseline_report.get("contract_valid") is True,
        "scenario_contract_exact": (
            scenario.get("execution_mode") == EXECUTION_MODE
            and scenario.get("scenario_ids") == list(EXPECTED_SCENARIOS)
            and scenario.get("control_input_ref") == CONTROL_INPUT_REF
            and scenario.get("physical_drive_event_required") is False
            and scenario.get("disk_allocation_allowed") is False
            and scenario.get("cleanup_execution_allowed") is False
        ),
        "lock_contract_exact": (
            lock.get("resource_identity_derivation") == "SHA256_TASK_INPUT_ONLY"
            and lock.get("job_identity_derivation")
            == "SHA256_TASK_INPUT_JOB_TYPE"
            and lock.get("conflicting_job_types") == list(CONFLICTING_JOB_TYPES)
            and lock.get("resource_conflict_result")
            == "RESOURCE_CONFLICT_ACTIVE"
            and lock.get("terminal_record_releases_admission_conflict") is True
            and lock.get("production_lock_runtime_owner") == "STAGE-041"
        ),
        "resource_gate_contract_exact": (
            resource.get("external_drive_offline_result")
            == "PAUSED_EXTERNAL_DRIVE_OFFLINE"
            and resource.get("low_disk_result") == "PAUSED_LOW_DISK"
            and resource.get("external_api_budget_insufficient_result")
            == "PAUSED_EXTERNAL_API_BUDGET_INSUFFICIENT"
            and resource.get("pause_before_queue_record") is True
            and resource.get("actual_disk_observation_required") is True
            and resource.get("physical_drive_removal_claim_allowed") is False
            and resource.get("external_api_call_required") is False
        ),
        "cleanup_contract_exact": (
            cleanup.get("protected_artifacts") == EXPECTED_PROTECTED_ARTIFACTS
            and cleanup.get("protected_result") == "PROTECTED_ARTIFACT"
            and cleanup.get("delete_attempt_allowed") is False
            and cleanup.get("runtime_owner") == "STAGE-044"
        ),
        "truth_contract_exact": (
            set(truth) == set(ZERO_SIDE_EFFECT_FIELDS)
            and all(truth.get(field) is False for field in ZERO_SIDE_EFFECT_FIELDS)
        ),
    }


def _paused_status() -> dict[str, Any]:
    stage037 = _baseline_module()._stage037_module()
    value = stage037.load_contract()["human_status_projection"]["PAUSED"]
    return copy.deepcopy(value)


def evaluate_resource_gate(
    *,
    external_drive_required: bool,
    external_drive_ready: bool,
    available_bytes: int,
    required_bytes: int,
    external_api_required: bool = False,
    external_api_budget_available: bool = True,
) -> dict[str, Any]:
    valid_bytes = (
        isinstance(external_drive_required, bool)
        and isinstance(external_drive_ready, bool)
        and isinstance(external_api_required, bool)
        and isinstance(external_api_budget_available, bool)
        and not isinstance(available_bytes, bool)
        and isinstance(available_bytes, int)
        and available_bytes >= 0
        and not isinstance(required_bytes, bool)
        and isinstance(required_bytes, int)
        and required_bytes >= 0
    )
    if not valid_bytes:
        return {
            "accepted": False,
            "result_code": "INVALID_RESOURCE_FACTS",
            "owner_status": _paused_status(),
            "queue_records_created": 0,
        }
    if external_drive_required and not external_drive_ready:
        return {
            "accepted": False,
            "result_code": "PAUSED_EXTERNAL_DRIVE_OFFLINE",
            "owner_status": _paused_status(),
            "queue_records_created": 0,
        }
    if required_bytes > available_bytes:
        return {
            "accepted": False,
            "result_code": "PAUSED_LOW_DISK",
            "owner_status": _paused_status(),
            "queue_records_created": 0,
        }
    if external_api_required and not external_api_budget_available:
        return {
            "accepted": False,
            "result_code": "PAUSED_EXTERNAL_API_BUDGET_INSUFFICIENT",
            "owner_status": _paused_status(),
            "queue_records_created": 0,
        }
    return {
        "accepted": True,
        "result_code": "RESOURCE_GATES_PASSED",
        "owner_status": {},
        "queue_records_created": 0,
    }


def evaluate_cleanup_candidate(
    artifact_class: str,
    artifact_ref: str,
) -> dict[str, Any]:
    baseline = _baseline_module()
    path = baseline._repo_path_from_ref(artifact_ref)
    git_tracked = path is not None and baseline._git_tracked(path)
    protected = EXPECTED_PROTECTED_ARTIFACTS.get(artifact_class) == artifact_ref
    return {
        "artifact_class": artifact_class,
        "artifact_ref": artifact_ref,
        "git_tracked": git_tracked,
        "delete_allowed": False,
        "result_code": (
            "PROTECTED_ARTIFACT" if protected and git_tracked else "INVALID_CLEANUP_CANDIDATE"
        ),
        "delete_attempted": False,
    }


async def _duplicate_click_scenario(index: Mapping[str, Any]) -> dict[str, Any]:
    baseline = _baseline_module()
    operation_invocations = 0

    async def operation(envelope: Mapping[str, Any]) -> dict[str, Any]:
        nonlocal operation_invocations
        operation_invocations += 1
        return await baseline._hash_tracked_control_file(envelope)

    queue = baseline.IsolatedWorkerQueue(capacity=2, operation=operation)
    envelope = baseline.build_control_envelope(CONTROL_INPUT_REF)
    first = queue.submit(envelope)
    duplicate = queue.submit(envelope)
    await queue.start()
    await asyncio.wait_for(queue.join(), timeout=2.0)
    record = queue.get_record(first["queue_entry_ref"])
    await queue.shutdown()
    passed = (
        first.get("accepted") is True
        and duplicate.get("accepted") is True
        and duplicate.get("duplicate") is True
        and first.get("queue_entry_ref") == duplicate.get("queue_entry_ref")
        and operation_invocations == 1
        and record.get("machine_state") == "SUCCEEDED"
        and queue.record_count == 1
    )
    return {
        "status": "PASS" if passed else "FAIL",
        "first_decision": first,
        "duplicate_decision": duplicate,
        "operation_invocations": operation_invocations,
        "record_count": queue.record_count,
        "final_record": record,
    }


async def _worker_exception_scenario(index: Mapping[str, Any]) -> dict[str, Any]:
    baseline = _baseline_module()
    invocation_count = 0

    async def fail_then_succeed(envelope: Mapping[str, Any]) -> dict[str, Any]:
        nonlocal invocation_count
        invocation_count += 1
        if invocation_count == 1:
            raise RuntimeError("isolated Stage038 worker exception")
        return await baseline._hash_tracked_control_file(envelope)

    queue = baseline.IsolatedWorkerQueue(capacity=2, operation=fail_then_succeed)
    await queue.start()
    failed_ack = queue.submit(
        baseline.build_control_envelope(CONTROL_INPUT_REF, job_type="PARSE")
    )
    await asyncio.wait_for(queue.join(), timeout=2.0)
    failed_record = queue.get_record(failed_ack["queue_entry_ref"])
    lock_key = failed_record["lock_key"]
    lock = queue._resource_locks.get(lock_key)
    lock_released = lock is not None and not lock.locked()
    same_operation_resubmission = queue.submit(
        baseline.build_control_envelope(CONTROL_INPUT_REF, job_type="PARSE")
    )
    followup_ack = queue.submit(
        baseline.build_control_envelope(CONTROL_INPUT_REF, job_type="REPORT")
    )
    await asyncio.wait_for(queue.join(), timeout=2.0)
    followup_record = queue.get_record(followup_ack["queue_entry_ref"])
    await queue.shutdown()
    passed = (
        failed_record.get("machine_state") == "FAILED"
        and failed_record.get("error_ref") == "error:RuntimeError"
        and failed_record.get("output_refs") == []
        and failed_record.get("checkpoint_ref") is None
        and lock_released
        and same_operation_resubmission.get("result_code")
        == "EXISTING_QUEUE_ENTRY"
        and same_operation_resubmission.get("duplicate") is True
        and followup_ack.get("accepted") is True
        and followup_record.get("machine_state") == "SUCCEEDED"
        and invocation_count == 2
    )
    return {
        "status": "PASS" if passed else "FAIL",
        "failed_record": failed_record,
        "lock_released_after_failure": lock_released,
        "same_operation_resubmission_available": False,
        "same_operation_resubmission_decision": same_operation_resubmission,
        "followup_same_source_admitted": followup_ack.get("accepted") is True,
        "followup_decision": followup_ack,
        "followup_record": followup_record,
        "operation_invocations": invocation_count,
        "process_termination_performed": False,
    }


def _external_drive_scenario() -> dict[str, Any]:
    decision = evaluate_resource_gate(
        external_drive_required=True,
        external_drive_ready=False,
        available_bytes=0,
        required_bytes=0,
    )
    passed = (
        decision.get("accepted") is False
        and decision.get("result_code") == "PAUSED_EXTERNAL_DRIVE_OFFLINE"
        and decision.get("queue_records_created") == 0
    )
    return {
        "status": "PASS" if passed else "FAIL",
        **decision,
        "scenario_mode": "CONTROL_GATE_INPUT_ONLY",
        "physical_drive_event_observed": False,
    }


def _low_disk_scenario() -> dict[str, Any]:
    observed_free = shutil.disk_usage(PROJECT_ROOT).free
    required = observed_free + 1
    decision = evaluate_resource_gate(
        external_drive_required=False,
        external_drive_ready=True,
        available_bytes=observed_free,
        required_bytes=required,
    )
    passed = (
        observed_free > 0
        and decision.get("accepted") is False
        and decision.get("result_code") == "PAUSED_LOW_DISK"
        and decision.get("queue_records_created") == 0
    )
    return {
        "status": "PASS" if passed else "FAIL",
        **decision,
        "observed_free_bytes": observed_free,
        "required_bytes": required,
        "allocation_performed": False,
    }


def _external_api_budget_scenario() -> dict[str, Any]:
    decision = evaluate_resource_gate(
        external_drive_required=False,
        external_drive_ready=True,
        available_bytes=1,
        required_bytes=1,
        external_api_required=True,
        external_api_budget_available=False,
    )
    passed = (
        decision.get("accepted") is False
        and decision.get("result_code")
        == "PAUSED_EXTERNAL_API_BUDGET_INSUFFICIENT"
        and decision.get("queue_records_created") == 0
    )
    return {
        "status": "PASS" if passed else "FAIL",
        **decision,
        "scenario_mode": "CONTROL_GATE_INPUT_ONLY",
        "external_api_call_performed": False,
    }


async def _same_source_lock_scenario(index: Mapping[str, Any]) -> dict[str, Any]:
    baseline = _baseline_module()
    operation_invocations = 0

    async def operation(envelope: Mapping[str, Any]) -> dict[str, Any]:
        nonlocal operation_invocations
        operation_invocations += 1
        return await baseline._hash_tracked_control_file(envelope)

    queue = baseline.IsolatedWorkerQueue(capacity=4, operation=operation)
    envelopes = [
        baseline.build_control_envelope(CONTROL_INPUT_REF, job_type=job_type)
        for job_type in CONFLICTING_JOB_TYPES
    ]
    decisions = [queue.submit(envelope) for envelope in envelopes]
    await queue.start()
    await asyncio.wait_for(queue.join(), timeout=2.0)
    first_record = queue.get_record(decisions[0]["queue_entry_ref"])
    await queue.shutdown()
    lock_keys = {envelope["lock_key"] for envelope in envelopes}
    passed = (
        len(lock_keys) == 1
        and decisions[0].get("accepted") is True
        and all(item.get("accepted") is False for item in decisions[1:])
        and all(
            item.get("result_code") == "RESOURCE_CONFLICT_ACTIVE"
            for item in decisions[1:]
        )
        and queue.record_count == 1
        and operation_invocations == 1
        and first_record.get("machine_state") == "SUCCEEDED"
    )
    return {
        "status": "PASS" if passed else "FAIL",
        "job_types": list(CONFLICTING_JOB_TYPES),
        "shared_lock_key_count": len(lock_keys),
        "decisions": decisions,
        "record_count": queue.record_count,
        "operation_invocations": operation_invocations,
        "final_record": first_record,
    }


def _protected_cleanup_scenario() -> dict[str, Any]:
    results = {
        artifact_class: evaluate_cleanup_candidate(artifact_class, artifact_ref)
        for artifact_class, artifact_ref in EXPECTED_PROTECTED_ARTIFACTS.items()
    }
    passed = all(
        item.get("git_tracked") is True
        and item.get("delete_allowed") is False
        and item.get("result_code") == "PROTECTED_ARTIFACT"
        and item.get("delete_attempted") is False
        for item in results.values()
    )
    return {
        "status": "PASS" if passed else "FAIL",
        "artifact_results": results,
        "delete_attempt_count": 0,
        "deleted_ref_count": 0,
    }


async def _run_scenarios(index: Mapping[str, Any]) -> dict[str, Any]:
    results = {
        "duplicate_click_one_execution": await _duplicate_click_scenario(index),
        "worker_crash_exception_and_lock_release": await _worker_exception_scenario(
            index
        ),
        "external_drive_offline_pause_before_queue": _external_drive_scenario(),
        "actual_low_disk_boundary_pause_without_allocation": _low_disk_scenario(),
        "external_api_budget_insufficient_pause_before_queue": (
            _external_api_budget_scenario()
        ),
        "same_source_cross_operation_lock": await _same_source_lock_scenario(index),
        "protected_cleanup_denied": _protected_cleanup_scenario(),
    }
    return {
        "scenario_results": results,
        "scenario_validation_valid": (
            tuple(results) == EXPECTED_SCENARIOS
            and all(item.get("status") == "PASS" for item in results.values())
        ),
    }


def build_stage038_phase3_report(
    *,
    index: Optional[dict[str, Any]] = None,
    execute_scenarios: bool = True,
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
        "phase": "Phase 3",
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "execution_mode": EXECUTION_MODE,
        "execution_state": (
            "CONTRACT_VALID_SCENARIOS_NOT_EXECUTED"
            if contract_valid and not execute_scenarios
            else "BLOCKED_INVALID_PHASE3_CONTRACT"
        ),
        "contract_valid": contract_valid,
        "contract_checks": checks,
        "source_integrity": source_integrity,
        "observed_source_sha256": observed_hashes,
        "load_error": load_error,
        "scenario_validation_valid": False,
        "scenario_results": {},
        "scenario_runtime_performed": False,
        "isolated_queue_runtime_performed": False,
        "actual_worker_exception_performed": False,
        "actual_disk_observation_performed": False,
        **{field: False for field in ZERO_SIDE_EFFECT_FIELDS},
        "next_gate": NEXT_GATE,
        "owner_feedback_zh": (
            "Worker 队列 Phase 3 合同无效；未运行隔离异常场景。"
            if not contract_valid
            else "Worker 队列 Phase 3 合同有效；隔离异常场景尚未运行。"
        ),
    }
    if not contract_valid or not execute_scenarios:
        return report
    try:
        scenario_run = asyncio.run(_run_scenarios(contract))
    except (OSError, RuntimeError, ValueError, asyncio.TimeoutError) as exc:
        report["execution_state"] = "BLOCKED_SCENARIO_EXECUTION_FAILED"
        report["load_error"] = f"{type(exc).__name__}: {exc}"
        report["owner_feedback_zh"] = (
            "隔离异常场景执行失败；生产队列、原始资料访问与清理继续禁用。"
        )
        return report
    report.update(
        {
            "scenario_results": scenario_run["scenario_results"],
            "scenario_validation_valid": scenario_run[
                "scenario_validation_valid"
            ],
            "scenario_runtime_performed": True,
            "isolated_queue_runtime_performed": True,
            "actual_worker_exception_performed": True,
            "actual_disk_observation_performed": True,
            "execution_state": (
                "ISOLATED_PHASE3_SCENARIOS_PASSED_PRODUCTION_DISABLED"
                if scenario_run["scenario_validation_valid"]
                else "BLOCKED_PHASE3_SCENARIO_INVALID"
            ),
            "owner_feedback_zh": (
                "Worker 队列 Phase 3 七类隔离场景已通过；同源任务冲突、异常终态、"
                "磁盘、移动硬盘及 API 预算暂停和受保护清理均失败关闭，生产运行继续禁用。"
                if scenario_run["scenario_validation_valid"]
                else "Worker 队列 Phase 3 未通过全部场景；生产运行继续禁用。"
            ),
        }
    )
    return report


def main() -> int:
    report = build_stage038_phase3_report()
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0 if report["scenario_validation_valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
