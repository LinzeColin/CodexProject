#!/usr/bin/env python3
"""Run and validate STAGE-040 Phase 3 isolated backpressure scenarios."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import time
from typing import Any, Mapping, Optional


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PROJECT_ROOT.parent
CONTRACT_PATH = (
    PROJECT_ROOT
    / "docs/pursuing_goal/ids_v0_1/backpressure_policy/"
    "stage040_backpressure_scenarios.json"
)
PHASE2_CHECKER = PROJECT_ROOT / "scripts/check_backpressure_runtime.py"
STAGE039_SCENARIO_CHECKER = (
    PROJECT_ROOT / "scripts/check_retry_dead_letter_scenarios.py"
)
POLICY_VERSION = "ids.backpressure_policy.v0_1.stage040.p2"
TASK_ID = "IDS-V0_1-STAGE040-P3"
ACCEPTANCE_ID = "ACC-STAGE-040"
PHASE2_COMMIT = "647445f9e0bb5cfcbfbfaa0f8180df872c3ece5f"
CONTROL_REF = (
    "repo:KM_IDSystem/docs/pursuing_goal/ids_v0_1/"
    "STAGE040_PHASE1_BACKPRESSURE_SCOPE_BOUNDARY.md"
)

EXPECTED_SOURCE = {
    "source_archive_path": (
        "/Users/linzezhang/Downloads/IDS_Taskpack_v0_1_only_中文修订版.zip"
    ),
    "source_archive_sha256": (
        "55b782e338610aab6361b7945bb5e290ba60038a06cc765c7c2da801734db6d3"
    ),
    "source_member": (
        "IDS_v0_1_Final_Chinese_Revised/stages/STAGE-040_反压策略.md"
    ),
    "source_member_match_count": 1,
    "source_member_sha256": (
        "f0ef128467300d7541796f8d51caca673f838cac2552eba2e415a94a07af614d"
    ),
    "roadmap_path": (
        "/Users/linzezhang/Downloads/IDS_Codex开发Roadmap_v0_1_only_中文修订版.txt"
    ),
    "roadmap_sha256": (
        "a193fd2c44c51d634bf7887a1a6baf7e5199d9a8535e4211e35e97588e2e21a6"
    ),
    "instructions_path": (
        "/Users/linzezhang/Downloads/IDS_Codex使用说明_v0_1_only_中文修订版.txt"
    ),
    "instructions_sha256": (
        "ce456e06136d5ecc56cd7c9dc926abb5894817dda87bf7667588bf85211794f8"
    ),
    "source_verification_status": "SOURCE_VERIFIED",
}
EXPECTED_UPSTREAM = {
    "stage040_phase2_contract": (
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/backpressure_policy/"
        "stage040_backpressure_runtime_contract.json",
        "2fb9437f85a8c86cbfc8d6002e031554683bdf9b4a421b06c6b9503c6c40b6c1",
    ),
    "stage040_phase2_checker": (
        "KM_IDSystem/scripts/check_backpressure_runtime.py",
        "8442ef6b9ff63e3999205151d5bf8deddbe3085730dc864b5627e6b4ff06da06",
    ),
    "stage040_phase2_evidence": (
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/"
        "STAGE040_PHASE2_BACKPRESSURE_DECISION_SLICE.md",
        "5b8f1a030034a6cb9f8becc5e42ee4e354d51fb0ac394366e641ebb90fa31c41",
    ),
    "stage039_scenario_contract": (
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/retry_dead_letter/"
        "stage039_retry_dead_letter_scenarios.json",
        "045cc67295c4918996b8439e0b2ea857edf2f998e836fbc7b4bbcbbedd660b3e",
    ),
    "stage039_scenario_checker": (
        "KM_IDSystem/scripts/check_retry_dead_letter_scenarios.py",
        "2502d8fde4016be717c72ad079ec338c80e1ed8fec9a9c27f5494dfb34eef862",
    ),
    "stage038_scenario_contract": (
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/worker_queue_baseline/"
        "stage038_worker_queue_scenarios.json",
        "0ec9f1a0de6ec24d64d4108214ea426f9171b15eebdd6c3c60693fade62f2961",
    ),
    "stage038_scenario_checker": (
        "KM_IDSystem/scripts/check_worker_queue_scenarios.py",
        "b7e335039ecf65e4fe91df39e91cddd296296852bd3be8923237b8616db9517c",
    ),
}
SCENARIO_CATALOG = [
    "duplicate_click_decision_replay",
    "worker_exception_crash_boundary",
    "external_drive_offline_pause_candidate",
    "actual_disk_observation_and_low_disk_boundary",
    "external_api_budget_pause_candidate",
    "same_source_cross_operation_concurrency_throttle",
    "reviewed_lock_conflict_proof",
    "protected_cleanup_denied",
]
SCENARIO_EXPECTATIONS = {
    "duplicate_click_decision_replay": (
        "ONE_IN_MEMORY_DECISION_IDEMPOTENT_REPLAY_NO_JOB_OR_WRITE"
    ),
    "worker_exception_crash_boundary": (
        "ACTUAL_ISOLATED_EXCEPTION_TERMINAL_IMMUTABLE_CRASH_RECOVERY_DEFERRED"
    ),
    "external_drive_offline_pause_candidate": (
        "QUEUED_TO_PAUSED_CANDIDATE_NO_PHYSICAL_REMOVAL"
    ),
    "actual_disk_observation_and_low_disk_boundary": (
        "ACTUAL_OBSERVATION_PLUS_BOUNDARY_PAUSE_NO_ALLOCATION"
    ),
    "external_api_budget_pause_candidate": (
        "RUNNING_TO_PAUSE_REQUESTED_CANDIDATE_NO_API_CALL"
    ),
    "same_source_cross_operation_concurrency_throttle": (
        "FOUR_CROSS_OPERATION_ADMISSIONS_THROTTLED_NO_JOB_CREATED"
    ),
    "reviewed_lock_conflict_proof": (
        "ONE_CONTROL_EXECUTION_THREE_CONFLICTS_PRODUCTION_LOCK_DEFERRED"
    ),
    "protected_cleanup_denied": "ALL_PROTECTED_REFS_GIT_TRACKED_NO_DELETE_PATH",
}
PHYSICAL_ACTION_BOUNDARY = {
    "process_termination_allowed": False,
    "physical_drive_removal_allowed": False,
    "disk_allocation_allowed": False,
    "external_api_call_allowed": False,
    "cleanup_delete_allowed": False,
    "production_runtime_allowed": False,
    "stage040_queue_worker_runtime_allowed": False,
    "stage038_isolated_worker_exception_replay_allowed": True,
    "actual_project_disk_observation_allowed": True,
}
STATE_INVARIANTS = {
    "state_model_version": "ids.job_state.v1",
    "terminal_states_immutable": [
        "SUCCEEDED",
        "FAILED",
        "DEAD_LETTERED",
        "CANCELLED",
    ],
    "queued_resource_pause_path": ["QUEUED", "PAUSED"],
    "active_resource_pause_path": ["RUNNING", "PAUSE_REQUESTED", "PAUSED"],
    "resource_pause_consumes_retry_budget": False,
    "duplicate_decision_consumes_retry_budget": False,
    "duplicate_decision_creates_job": False,
    "decision_replay_ledger": "IN_MEMORY_ONLY",
}
LOCK_BOUNDARY = {
    "same_source_operations": ["ARCHIVE", "PARSE", "INDEX", "REPORT"],
    "source_identity": "EXACT_GIT_TRACKED_INPUT_REF",
    "reviewed_control_proof_source": (
        "STAGE039_PHASE3_REPLAYING_STAGE038_ISOLATED_LOCK_REGISTRY"
    ),
    "expected_operation_invocations": 1,
    "expected_resource_conflicts": 3,
    "production_lock_runtime_allowed": False,
    "runtime_owner": "STAGE-041",
}
PROTECTED_ARTIFACT_CONTRACT = {
    "protected_refs": {
        "FACT_SOURCE": CONTROL_REF,
        "MANIFEST": (
            "repo:KM_IDSystem/docs/pursuing_goal/ids_v0_1/"
            "STAGE026_PHASE2_ARCHIVE_MANIFEST_SLICE.md"
        ),
        "EVIDENCE_LEDGER": (
            "repo:KM_IDSystem/docs/pursuing_goal/ids_v0_1/backpressure_policy/"
            "stage040_backpressure_runtime_contract.json"
        ),
        "REPORT_SNAPSHOT": (
            "repo:KM_IDSystem/docs/pursuing_goal/ids_v0_1/"
            "STAGE040_PHASE2_BACKPRESSURE_DECISION_SLICE.md"
        ),
        "AUDIT_LOG": "repo:KM_IDSystem/docs/governance/events.jsonl",
    },
    "all_refs_must_be_git_tracked": True,
    "delete_attempt_allowed": False,
    "delete_api_call_allowed": False,
    "runtime_owner": "STAGE-044",
}
DOWNSTREAM_OWNERSHIP = {
    "production_lock_lease_and_fencing": "STAGE-041",
    "automatic_resume_and_lifecycle": "STAGE-042",
    "process_crash_recovery": "STAGE-043",
    "cleanup_execution": "STAGE-044",
    "phase3_may_take_downstream_runtime_ownership": False,
}
HUMAN_STATUS_CONTRACT = {
    "THROTTLE_ADMISSION": "限流中",
    "PAUSE_RESOURCE_GATE": "已暂停",
    "REQUEST_SAFE_PAUSE": "暂停中",
    "REQUIRE_MANUAL_REVIEW": "等待人工复核",
}
PHASE4_ENTRY_GATE = {
    "entry_authorized_after_scenario_pass": True,
    "required_task_id": "IDS-V0_1-STAGE040-P4",
    "required_acceptance_id": ACCEPTANCE_ID,
    "must_run_separately": True,
    "whole_stage_review_allowed_in_phase3": False,
    "github_upload_allowed": False,
    "app_reinstall_allowed": False,
    "next_gate": "IDS-STAGE040-P4-GATE",
}
TRUE_TRUTH_FLAGS = {
    "taskpack_source_read_performed",
    "actual_isolated_worker_exception_performed",
    "stage038_isolated_worker_exception_replayed",
    "actual_disk_observation_performed",
    "isolated_control_metadata_evaluated",
    "reviewed_control_lock_proof_replayed",
}
FALSE_TRUTH_FLAGS = {
    "ids_business_source_read_performed",
    "raw_metadata_content_accessed",
    "fake_ids_business_data_used",
    "real_ids_business_job_created",
    "process_termination_performed",
    "physical_drive_removal_performed",
    "disk_allocation_performed",
    "external_api_call_performed",
    "cleanup_runtime_performed",
    "protected_ref_delete_performed",
    "stage040_queue_runtime_performed",
    "stage040_worker_runtime_performed",
    "production_lock_runtime_performed",
    "crash_recovery_runtime_performed",
    "production_runtime_activation_performed",
    "persistent_queue_write_performed",
    "database_connection_performed",
    "runtime_output_written",
    "github_upload_allowed",
    "app_reinstall_allowed",
}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _phase2_module() -> Any:
    return _load_module(PHASE2_CHECKER, "stage040_phase2_runtime")


def _stage039_module() -> Any:
    return _load_module(
        STAGE039_SCENARIO_CHECKER,
        "stage039_retry_dead_letter_scenarios_for_stage040",
    )


def load_scenario_contract(path: Path = CONTRACT_PATH) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("Stage040 Phase3 scenario contract must be an object")
    return value


def _git_tracked_repo_ref(value: Any) -> bool:
    if not isinstance(value, str) or not value.startswith("repo:KM_IDSystem/"):
        return False
    relative = value.removeprefix("repo:")
    pure = Path(relative)
    if pure.is_absolute() or ".." in pure.parts:
        return False
    result = subprocess.run(
        ["git", "ls-files", "--error-unmatch", "--", relative],
        cwd=REPO_ROOT,
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return result.returncode == 0


def _upstream_valid(value: Any) -> bool:
    if not isinstance(value, dict) or set(value) != set(EXPECTED_UPSTREAM):
        return False
    for name, (relative, expected_hash) in EXPECTED_UPSTREAM.items():
        if value.get(name) != {"ref": relative, "sha256": expected_hash}:
            return False
        path = REPO_ROOT / relative
        if not path.is_file() or sha256_file(path) != expected_hash:
            return False
    return True


def _phase2_commit_is_ancestor(value: Any) -> bool:
    if value != {"commit": PHASE2_COMMIT, "required_ancestor_of_head": True}:
        return False
    result = subprocess.run(
        ["git", "merge-base", "--is-ancestor", PHASE2_COMMIT, "HEAD"],
        cwd=REPO_ROOT,
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return result.returncode == 0


def validate_scenario_contract(contract: Any) -> dict[str, bool]:
    if not isinstance(contract, dict):
        return {"contract_is_object": False}
    expected_root = {
        "schema_version",
        "stage",
        "phase",
        "task_id",
        "acceptance_id",
        "execution_mode",
        "scenario_contract_id",
        "contract_state",
        "next_gate",
        "source_binding",
        "phase2_commit_binding",
        "upstream_bindings",
        "policy_version",
        "scenario_catalog",
        "scenario_expectations",
        "physical_action_boundary",
        "state_retry_idempotency_invariants",
        "lock_boundary",
        "protected_artifact_contract",
        "downstream_ownership",
        "human_status_contract",
        "phase4_entry_gate",
        "truth_flags",
    }
    protected = contract.get("protected_artifact_contract")
    protected_refs = (
        protected.get("protected_refs") if isinstance(protected, dict) else {}
    )
    truth = contract.get("truth_flags")
    return {
        "contract_is_object": True,
        "root_shape_exact": set(contract) == expected_root,
        "identity_exact": (
            contract.get("schema_version")
            == "ids.stage040.backpressure.phase3.scenarios.v1"
            and contract.get("stage") == "STAGE-040"
            and contract.get("phase") == "Phase 3"
            and contract.get("task_id") == TASK_ID
            and contract.get("acceptance_id") == ACCEPTANCE_ID
            and contract.get("execution_mode")
            == "ISOLATED_NON_PRODUCTION_BACKPRESSURE_SCENARIOS"
            and contract.get("scenario_contract_id")
            == "ids.backpressure_policy.v0_1.stage040.p3.scenarios"
            and contract.get("contract_state")
            == "PHASE3_SCENARIOS_ENABLED_PRODUCTION_DISABLED"
            and contract.get("next_gate") == "IDS-STAGE040-P4-GATE"
        ),
        "source_binding_exact": contract.get("source_binding") == EXPECTED_SOURCE,
        "phase2_commit_bound": _phase2_commit_is_ancestor(
            contract.get("phase2_commit_binding")
        ),
        "upstream_bindings_current": _upstream_valid(
            contract.get("upstream_bindings")
        ),
        "policy_version_exact": contract.get("policy_version") == POLICY_VERSION,
        "scenario_catalog_exact": contract.get("scenario_catalog")
        == SCENARIO_CATALOG,
        "scenario_expectations_exact": contract.get("scenario_expectations")
        == SCENARIO_EXPECTATIONS,
        "physical_action_boundary_exact": contract.get("physical_action_boundary")
        == PHYSICAL_ACTION_BOUNDARY,
        "state_retry_idempotency_exact": contract.get(
            "state_retry_idempotency_invariants"
        )
        == STATE_INVARIANTS,
        "lock_boundary_exact": contract.get("lock_boundary") == LOCK_BOUNDARY,
        "protected_artifact_contract_exact": protected
        == PROTECTED_ARTIFACT_CONTRACT,
        "protected_refs_git_tracked": (
            isinstance(protected_refs, dict)
            and set(protected_refs)
            == {"FACT_SOURCE", "MANIFEST", "EVIDENCE_LEDGER", "REPORT_SNAPSHOT", "AUDIT_LOG"}
            and all(_git_tracked_repo_ref(ref) for ref in protected_refs.values())
        ),
        "downstream_ownership_exact": contract.get("downstream_ownership")
        == DOWNSTREAM_OWNERSHIP,
        "human_status_exact": contract.get("human_status_contract")
        == HUMAN_STATUS_CONTRACT,
        "phase4_gate_exact": contract.get("phase4_entry_gate") == PHASE4_ENTRY_GATE,
        "truth_flags_exact": (
            isinstance(truth, dict)
            and set(truth) == TRUE_TRUTH_FLAGS | FALSE_TRUTH_FLAGS
            and all(truth.get(key) is True for key in TRUE_TRUTH_FLAGS)
            and all(truth.get(key) is False for key in FALSE_TRUTH_FLAGS)
        ),
    }


def _observation(
    phase2: Any,
    *,
    now: int,
    disk_free_bytes: int,
    queue_depth: int = 0,
    queued_input_refs: Optional[list[str]] = None,
    active_job_type_count: int = 0,
    admissions_in_window: int = 0,
    api_required: int = 0,
    api_remaining: int = 0,
) -> dict[str, Any]:
    return phase2._actual_observation(
        now=now,
        disk_free_bytes=disk_free_bytes,
        queue_depth=queue_depth,
        queued_input_refs=queued_input_refs,
        active_job_type_count=active_job_type_count,
        admissions_in_window=admissions_in_window,
        api_required=api_required,
        api_remaining=api_remaining,
    )


def _duplicate_click_scenario(
    phase2: Any,
    phase2_contract: Mapping[str, Any],
    *,
    now: int,
    disk_free_bytes: int,
) -> dict[str, Any]:
    job = phase2.build_control_job(CONTROL_REF)
    observation = _observation(
        phase2, now=now, disk_free_bytes=disk_free_bytes
    )
    ledger = phase2.IsolatedDecisionLedger()
    first = phase2.evaluate_backpressure(
        job,
        observation,
        contract=phase2_contract,
        ledger=ledger,
        now_epoch_seconds=now,
    )
    second = phase2.evaluate_backpressure(
        job,
        copy.deepcopy(observation),
        contract=phase2_contract,
        ledger=ledger,
        now_epoch_seconds=now,
    )
    passed = (
        first.get("decision_action") == "ADMIT"
        and first.get("idempotent_replay") is False
        and second.get("idempotent_replay") is True
        and first.get("decision_key") == second.get("decision_key")
        and first.get("checkpoint_ref") == second.get("checkpoint_ref")
        and ledger.entry_count == 1
        and first.get("job_created") is False
        and first.get("retry_budget_consumed") is False
    )
    return {
        "status": "PASS" if passed else "FAIL",
        "first_decision_action": first.get("decision_action"),
        "first_idempotent_replay": first.get("idempotent_replay"),
        "second_idempotent_replay": second.get("idempotent_replay"),
        "first_decision_key": first.get("decision_key"),
        "second_decision_key": second.get("decision_key"),
        "ledger_entry_count": ledger.entry_count,
        "retry_budget_consumed": first.get("retry_budget_consumed"),
        "job_created": first.get("job_created"),
        "persistent_write_performed": False,
    }


def _worker_exception_scenario(
    phase2: Any,
    phase2_contract: Mapping[str, Any],
    stage039_report: Mapping[str, Any],
    *,
    now: int,
    disk_free_bytes: int,
) -> dict[str, Any]:
    source = stage039_report.get("scenario_results", {}).get(
        "worker_exception_crash_boundary", {}
    )
    failed_job = phase2.build_control_job(CONTROL_REF, job_state="FAILED")
    decision = phase2.evaluate_backpressure(
        failed_job,
        _observation(phase2, now=now, disk_free_bytes=disk_free_bytes),
        contract=phase2_contract,
        now_epoch_seconds=now,
    )
    passed = (
        stage039_report.get("scenario_validation_valid") is True
        and source.get("status") == "PASS"
        and source.get("actual_worker_exception_performed") is True
        and source.get("stage038_failed_error_ref") == "error:RuntimeError"
        and source.get("process_termination_performed") is False
        and source.get("crash_recovery_runtime_performed") is False
        and decision.get("decision_action") == "REQUIRE_MANUAL_REVIEW"
        and decision.get("reason_code") == "TERMINAL_STATE_IMMUTABLE"
    )
    return {
        "status": "PASS" if passed else "FAIL",
        "actual_isolated_worker_exception_performed": bool(
            source.get("actual_worker_exception_performed")
        ),
        "worker_error_ref": source.get("stage038_failed_error_ref"),
        "backpressure_decision_action": decision.get("decision_action"),
        "backpressure_reason_code": decision.get("reason_code"),
        "terminal_state_preserved": failed_job.get("job_state"),
        "process_termination_performed": False,
        "crash_recovery_runtime_performed": False,
        "crash_recovery_owner": "STAGE-043",
    }


def _drive_offline_scenario(
    phase2: Any,
    phase2_contract: Mapping[str, Any],
    *,
    now: int,
    disk_free_bytes: int,
) -> dict[str, Any]:
    job = phase2.build_control_job(CONTROL_REF)
    observation = _observation(
        phase2, now=now, disk_free_bytes=disk_free_bytes
    )
    observation["external_drive_required"] = True
    observation["external_drive_available"] = False
    decision = phase2.evaluate_backpressure(
        job,
        observation,
        contract=phase2_contract,
        now_epoch_seconds=now,
    )
    passed = (
        decision.get("signal_code") == "EXTERNAL_DRIVE_OFFLINE"
        and decision.get("decision_action") == "PAUSE_RESOURCE_GATE"
        and decision.get("requested_state") == "PAUSED"
        and decision.get("state_path") == ["QUEUED", "PAUSED"]
        and decision.get("retry_budget_consumed") is False
    )
    return {
        "status": "PASS" if passed else "FAIL",
        "signal_code": decision.get("signal_code"),
        "decision_action": decision.get("decision_action"),
        "requested_state": decision.get("requested_state"),
        "state_path": decision.get("state_path"),
        "retry_budget_consumed": decision.get("retry_budget_consumed"),
        "physical_drive_removal_performed": False,
    }


def _disk_scenario(
    phase2: Any,
    phase2_contract: Mapping[str, Any],
    *,
    now: int,
    actual_disk_free_bytes: int,
) -> dict[str, Any]:
    job = phase2.build_control_job(CONTROL_REF)
    parameters = phase2_contract["policy"]["parameters"]
    actual = phase2.evaluate_backpressure(
        job,
        _observation(
            phase2,
            now=now,
            disk_free_bytes=actual_disk_free_bytes,
        ),
        contract=phase2_contract,
        now_epoch_seconds=now,
    )
    expected_actual_signal = (
        "DISK_SPACE_INSUFFICIENT"
        if max(0, actual_disk_free_bytes - parameters["disk_reserve_bytes"])
        < parameters["disk_free_bytes_threshold"]
        else "HEALTHY"
    )
    boundary_free_bytes = (
        parameters["disk_reserve_bytes"]
        + parameters["disk_free_bytes_threshold"]
        - 1
    )
    boundary = phase2.evaluate_backpressure(
        job,
        _observation(
            phase2,
            now=now,
            disk_free_bytes=boundary_free_bytes,
        ),
        contract=phase2_contract,
        now_epoch_seconds=now,
    )
    passed = (
        actual_disk_free_bytes > 0
        and actual.get("signal_code") == expected_actual_signal
        and boundary.get("signal_code") == "DISK_SPACE_INSUFFICIENT"
        and boundary.get("decision_action") == "PAUSE_RESOURCE_GATE"
        and boundary.get("requested_state") == "PAUSED"
        and boundary.get("retry_budget_consumed") is False
    )
    return {
        "status": "PASS" if passed else "FAIL",
        "actual_disk_free_bytes": actual_disk_free_bytes,
        "actual_disk_signal_code": actual.get("signal_code"),
        "expected_actual_signal_code": expected_actual_signal,
        "actual_disk_decision_matches_formula": (
            actual.get("signal_code") == expected_actual_signal
        ),
        "boundary_disk_free_bytes": boundary_free_bytes,
        "boundary_signal_code": boundary.get("signal_code"),
        "boundary_decision_action": boundary.get("decision_action"),
        "boundary_requested_state": boundary.get("requested_state"),
        "retry_budget_consumed": boundary.get("retry_budget_consumed"),
        "disk_allocation_performed": False,
    }


def _api_budget_scenario(
    phase2: Any,
    phase2_contract: Mapping[str, Any],
    *,
    now: int,
    disk_free_bytes: int,
) -> dict[str, Any]:
    running = phase2.build_control_job(CONTROL_REF, job_state="RUNNING")
    decision = phase2.evaluate_backpressure(
        running,
        _observation(
            phase2,
            now=now,
            disk_free_bytes=disk_free_bytes,
            api_required=1,
            api_remaining=0,
        ),
        contract=phase2_contract,
        now_epoch_seconds=now,
    )
    passed = (
        decision.get("signal_code") == "EXTERNAL_API_BUDGET_INSUFFICIENT"
        and decision.get("decision_action") == "PAUSE_RESOURCE_GATE"
        and decision.get("requested_state") == "PAUSE_REQUESTED"
        and decision.get("state_path")
        == ["RUNNING", "PAUSE_REQUESTED", "PAUSED"]
        and decision.get("retry_budget_consumed") is False
    )
    return {
        "status": "PASS" if passed else "FAIL",
        "signal_code": decision.get("signal_code"),
        "decision_action": decision.get("decision_action"),
        "requested_state": decision.get("requested_state"),
        "state_path": decision.get("state_path"),
        "retry_budget_consumed": decision.get("retry_budget_consumed"),
        "external_api_call_performed": False,
    }


def _same_source_concurrency_scenario(
    phase2: Any,
    phase2_contract: Mapping[str, Any],
    *,
    now: int,
    disk_free_bytes: int,
) -> dict[str, Any]:
    job_types = ["ARCHIVE", "PARSE", "INDEX", "REPORT"]
    decisions = []
    for job_type in job_types:
        decision = phase2.evaluate_backpressure(
            phase2.build_control_job(CONTROL_REF, job_type=job_type),
            _observation(
                phase2,
                now=now,
                disk_free_bytes=disk_free_bytes,
                active_job_type_count=1,
            ),
            contract=phase2_contract,
            now_epoch_seconds=now,
        )
        decisions.append(decision)
    throttled = sum(
        item.get("decision_action") == "THROTTLE_ADMISSION"
        and item.get("reason_code") == "JOB_TYPE_CONCURRENCY_LIMIT_REACHED"
        for item in decisions
    )
    created = sum(item.get("job_created") is True for item in decisions)
    input_refs = {
        tuple(item.get("input_refs", []))
        for item in decisions
        if isinstance(item, dict)
    }
    passed = throttled == 4 and created == 0 and input_refs == {(CONTROL_REF,)}
    return {
        "status": "PASS" if passed else "FAIL",
        "job_types": job_types,
        "shared_input_ref_count": len(input_refs),
        "throttled_decision_count": throttled,
        "created_job_count": created,
        "retry_budget_consumed_count": sum(
            item.get("retry_budget_consumed") is True for item in decisions
        ),
        "production_lock_runtime_performed": False,
        "lock_runtime_owner": "STAGE-041",
    }


def _reviewed_lock_scenario(
    stage039_report: Mapping[str, Any],
) -> dict[str, Any]:
    source = stage039_report.get("scenario_results", {}).get(
        "same_source_cross_operation_lock", {}
    )
    passed = (
        stage039_report.get("scenario_validation_valid") is True
        and source.get("status") == "PASS"
        and source.get("job_types") == ["ARCHIVE", "PARSE", "INDEX", "REPORT"]
        and source.get("shared_lock_key_count") == 1
        and source.get("record_count") == 1
        and source.get("operation_invocations") == 1
        and source.get("resource_conflict_count") == 3
        and source.get("production_lock_runtime_performed") is False
        and source.get("lock_runtime_owner") == "STAGE-041"
    )
    return {
        "status": "PASS" if passed else "FAIL",
        "job_types": copy.deepcopy(source.get("job_types")),
        "shared_lock_key_count": source.get("shared_lock_key_count"),
        "record_count": source.get("record_count"),
        "operation_invocations": source.get("operation_invocations"),
        "resource_conflict_count": source.get("resource_conflict_count"),
        "production_lock_runtime_performed": False,
        "lock_runtime_owner": "STAGE-041",
    }


def _protected_cleanup_scenario(
    contract: Mapping[str, Any], stage039: Any
) -> dict[str, Any]:
    refs = contract["protected_artifact_contract"]["protected_refs"]
    results = {
        artifact_class: stage039.evaluate_protected_cleanup_candidate(
            artifact_class, artifact_ref, contract
        )
        for artifact_class, artifact_ref in refs.items()
    }
    passed = all(
        item.get("git_tracked") is True
        and item.get("result_code") == "PROTECTED_ARTIFACT"
        and item.get("delete_allowed") is False
        and item.get("delete_attempted") is False
        for item in results.values()
    )
    return {
        "status": "PASS" if passed else "FAIL",
        "artifact_results": results,
        "delete_attempt_count": 0,
        "deleted_ref_count": 0,
        "cleanup_runtime_performed": False,
        "runtime_owner": "STAGE-044",
    }


def _run_scenarios(
    contract: Mapping[str, Any]
) -> tuple[dict[str, dict[str, Any]], bool]:
    phase2 = _phase2_module()
    stage039 = _stage039_module()
    phase2_contract = phase2.load_contract()
    stage039_report = stage039.build_stage039_phase3_report()
    now = int(time.time())
    actual_disk_free_bytes = shutil.disk_usage(PROJECT_ROOT).free
    results = {
        "duplicate_click_decision_replay": _duplicate_click_scenario(
            phase2,
            phase2_contract,
            now=now,
            disk_free_bytes=actual_disk_free_bytes,
        ),
        "worker_exception_crash_boundary": _worker_exception_scenario(
            phase2,
            phase2_contract,
            stage039_report,
            now=now,
            disk_free_bytes=actual_disk_free_bytes,
        ),
        "external_drive_offline_pause_candidate": _drive_offline_scenario(
            phase2,
            phase2_contract,
            now=now,
            disk_free_bytes=actual_disk_free_bytes,
        ),
        "actual_disk_observation_and_low_disk_boundary": _disk_scenario(
            phase2,
            phase2_contract,
            now=now,
            actual_disk_free_bytes=actual_disk_free_bytes,
        ),
        "external_api_budget_pause_candidate": _api_budget_scenario(
            phase2,
            phase2_contract,
            now=now,
            disk_free_bytes=actual_disk_free_bytes,
        ),
        "same_source_cross_operation_concurrency_throttle": (
            _same_source_concurrency_scenario(
                phase2,
                phase2_contract,
                now=now,
                disk_free_bytes=actual_disk_free_bytes,
            )
        ),
        "reviewed_lock_conflict_proof": _reviewed_lock_scenario(stage039_report),
        "protected_cleanup_denied": _protected_cleanup_scenario(
            contract, stage039
        ),
    }
    return results, stage039_report.get("scenario_validation_valid") is True


def _blank_report(
    contract_checks: Mapping[str, bool], *, load_error: Optional[str]
) -> dict[str, Any]:
    return {
        "schema_version": "ids.stage040.backpressure.phase3.report.v1",
        "stage": "STAGE-040",
        "phase": "Phase 3",
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "policy_version": POLICY_VERSION,
        "contract_valid": False,
        "scenario_runtime_performed": False,
        "scenario_validation_valid": False,
        "contract_checks": dict(contract_checks),
        "scenario_count": 0,
        "passed_scenario_count": 0,
        "scenario_results": {},
        "stage039_scenario_replay_valid": False,
        "execution_mode": "BLOCKED_INVALID_SCENARIO_CONTRACT",
        "contract_state": "BLOCKED_INVALID_SCENARIO_CONTRACT",
        "load_error": load_error,
        "next_gate": "IDS-STAGE040-P3-GATE",
        "owner_feedback_zh": "反压场景合同无效；保持 Phase 3 失败关闭。",
        **{key: False for key in TRUE_TRUTH_FLAGS | FALSE_TRUTH_FLAGS},
    }


def build_stage040_phase3_report(
    contract: Optional[Mapping[str, Any]] = None,
) -> dict[str, Any]:
    try:
        contract_value = (
            copy.deepcopy(dict(contract))
            if isinstance(contract, Mapping)
            else load_scenario_contract()
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return _blank_report(
            {"contract_loadable": False},
            load_error=f"{type(exc).__name__}: {exc}",
        )
    contract_checks = validate_scenario_contract(contract_value)
    contract_valid = bool(contract_checks) and all(contract_checks.values())
    if not contract_valid:
        return _blank_report(contract_checks, load_error=None)
    try:
        results, stage039_valid = _run_scenarios(contract_value)
    except (OSError, ValueError, KeyError, TypeError, RuntimeError) as exc:
        report = _blank_report(
            contract_checks,
            load_error=f"{type(exc).__name__}: {exc}",
        )
        report["contract_valid"] = True
        report["scenario_runtime_performed"] = True
        report["execution_mode"] = contract_value["execution_mode"]
        report["contract_state"] = contract_value["contract_state"]
        return report
    passed = sum(item.get("status") == "PASS" for item in results.values())
    scenario_valid = (
        list(results) == SCENARIO_CATALOG
        and len(results) == len(SCENARIO_CATALOG)
        and passed == len(SCENARIO_CATALOG)
        and stage039_valid
    )
    truth = contract_value["truth_flags"]
    worker = results["worker_exception_crash_boundary"]
    disk = results["actual_disk_observation_and_low_disk_boundary"]
    return {
        "schema_version": "ids.stage040.backpressure.phase3.report.v1",
        "stage": "STAGE-040",
        "phase": "Phase 3",
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "policy_version": POLICY_VERSION,
        "contract_valid": contract_valid,
        "scenario_runtime_performed": True,
        "scenario_validation_valid": scenario_valid,
        "contract_checks": contract_checks,
        "scenario_count": len(results),
        "passed_scenario_count": passed,
        "scenario_results": results,
        "stage039_scenario_replay_valid": stage039_valid,
        "execution_mode": contract_value["execution_mode"],
        "contract_state": contract_value["contract_state"],
        "load_error": None,
        "next_gate": (
            "IDS-STAGE040-P4-GATE"
            if scenario_valid
            else "IDS-STAGE040-P3-GATE"
        ),
        "owner_feedback_zh": (
            "反压策略 Phase 3 的八项隔离场景已通过；重复请求、资源压力、"
            "同源冲突和受保护证据均失败关闭，生产运行继续禁用。"
            if scenario_valid
            else "反压策略 Phase 3 场景证据无效；保持失败关闭。"
        ),
        "actual_isolated_worker_exception_performed": (
            worker.get("actual_isolated_worker_exception_performed") is True
            and truth["actual_isolated_worker_exception_performed"] is True
        ),
        "stage038_isolated_worker_exception_replayed": (
            worker.get("actual_isolated_worker_exception_performed") is True
            and truth["stage038_isolated_worker_exception_replayed"] is True
        ),
        "actual_disk_observation_performed": (
            disk.get("actual_disk_free_bytes", 0) > 0
            and truth["actual_disk_observation_performed"] is True
        ),
        "isolated_control_metadata_evaluated": truth[
            "isolated_control_metadata_evaluated"
        ],
        "reviewed_control_lock_proof_replayed": (
            results["reviewed_lock_conflict_proof"].get("status") == "PASS"
            and truth["reviewed_control_lock_proof_replayed"] is True
        ),
        "taskpack_source_read_performed": truth[
            "taskpack_source_read_performed"
        ],
        **{key: bool(truth.get(key, False)) for key in FALSE_TRUTH_FLAGS},
    }


def main() -> int:
    report = build_stage040_phase3_report()
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if report["scenario_validation_valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
