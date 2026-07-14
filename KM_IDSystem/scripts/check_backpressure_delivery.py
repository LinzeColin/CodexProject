#!/usr/bin/env python3
"""Build and validate STAGE-040 Phase 4 isolated closeout evidence."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
from typing import Any, Mapping, Optional


REPO_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = Path(__file__).resolve().parents[1]
BASE = PROJECT_ROOT / "docs" / "pursuing_goal" / "ids_v0_1"
CONTRACT_PATH = (
    BASE / "backpressure_policy" / "stage040_backpressure_delivery_contract.json"
)
STATE_INDEX_PATH = BASE / "job_state_model" / "stage037_job_state_model_index.json"
PHASE1_CONTRACT_PATH = (
    BASE / "backpressure_policy" / "stage040_backpressure_policy_contract.json"
)
PHASE2_CHECKER = PROJECT_ROOT / "scripts" / "check_backpressure_runtime.py"
PHASE3_CHECKER = PROJECT_ROOT / "scripts" / "check_backpressure_scenarios.py"
STAGE039_DELIVERY_CHECKER = (
    PROJECT_ROOT / "scripts" / "check_retry_dead_letter_delivery.py"
)

TASK_ID = "IDS-V0_1-STAGE040-P4"
ACCEPTANCE_ID = "ACC-STAGE-040"
POLICY_VERSION = "ids.backpressure_policy.v0_1.stage040.p2"
EXECUTION_MODE = "ISOLATED_NON_PRODUCTION_CLOSEOUT_EVIDENCE"
VALID_RESULT = "PASS_ISOLATED_CLOSEOUT_PRODUCTION_DISABLED"
PHASE4_GATE = "IDS-STAGE040-P4-GATE"
REVIEW_GATE = "IDS-STAGE040-REVIEW-GATE"
PHASE3_COMMIT = "e3509e932ce3b67e85f20cb18ca703e8b3a19f24"

PRESSURE_SIGNALS = [
    "QUEUE_SOFT_PRESSURE",
    "QUEUE_HARD_CAPACITY",
    "EXTERNAL_DRIVE_OFFLINE",
    "DISK_SPACE_INSUFFICIENT",
    "EXTERNAL_API_BUDGET_INSUFFICIENT",
    "JOB_TYPE_CONCURRENCY_LIMIT_REACHED",
    "SAME_SOURCE_CONFLICT",
]
DECISION_ACTIONS = [
    "ADMIT",
    "THROTTLE_ADMISSION",
    "DENY_NEW_ADMISSION",
    "PAUSE_RESOURCE_GATE",
    "REQUIRE_MANUAL_REVIEW",
]
EXPECTED_STATE_HISTORY = [
    "QUEUED",
    "CLAIMED",
    "RUNNING",
    "RETRY_WAIT",
    "QUEUED",
    "CLAIMED",
    "RUNNING",
    "RETRY_WAIT",
    "QUEUED",
    "CLAIMED",
    "RUNNING",
    "RETRY_WAIT",
    "DEAD_LETTERED",
]
CLEANUP_CLASSES = ["TEMP_STAGING_OUTPUT", "INCOMPLETE_DERIVATIVE_OUTPUT"]
PROTECTED_CLASSES = [
    "FACT_SOURCE",
    "MANIFEST",
    "EVIDENCE_LEDGER",
    "REPORT_SNAPSHOT",
    "AUDIT_LOG",
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
REEVALUATION_CANDIDATES = [
    "QUEUE_SOFT_PRESSURE_CLEARED",
    "QUEUE_HARD_CAPACITY_CLEARED",
    "ADMISSION_RATE_WINDOW_RESET",
    "JOB_TYPE_CONCURRENCY_CLEARED",
    "RESOURCE_GATE_REVALIDATED",
    "SAME_SOURCE_CONFLICT_CLEARED",
]
MANUAL_ACTION_CASES = [
    "UNKNOWN_OR_STALE_OBSERVATION",
    "TERMINAL_STATE_IMMUTABLE",
    "RESOURCE_GATE_OWNER_REVALIDATION",
    "WORKER_PROCESS_EXCEPTION",
    "SAME_SOURCE_CONFLICT_REVALIDATION",
    "UNCALIBRATED_POLICY",
    "INVALID_OR_MISSING_CONTRACT",
    "PROCESS_CRASH_RECOVERY",
]
SHUTDOWN_STEPS = [
    "STOP_NEW_ADMISSION_DECISIONS",
    "FREEZE_OBSERVATION_SNAPSHOT",
    "PRESERVE_DECISION_AND_AUDIT_REFS",
    "WAIT_FOR_ACCEPTED_ISOLATED_CONTROL_WORK",
    "CLOSE_REVIEWED_ISOLATED_TRANSPORT",
    "VERIFY_NO_PERSISTENT_OR_RUNTIME_OUTPUT",
]
RECOVERY_STEPS = [
    "VERIFY_EXACT_SOURCE_POLICY_AND_UPSTREAM_HASHES",
    "REOBSERVE_QUEUE_DISK_DRIVE_AND_API_BUDGET",
    "REJECT_UNKNOWN_OR_STALE_OBSERVATIONS",
    "REQUIRE_OWNER_REVALIDATION_FOR_MANUAL_CASES",
    "RERUN_IDEMPOTENT_DECISION_EVALUATION",
    "DEFER_AUTOMATIC_RESUME_TO_STAGE042",
    "DEFER_PROCESS_CRASH_RECOVERY_TO_STAGE043",
]
ROLLBACK_STEPS = [
    "STOP_ON_INVALID_DELIVERY_CONTRACT",
    "DENY_NEW_ADMISSION_REQUIRE_MANUAL_REVIEW",
    "STOP_NEW_ADMISSION_DECISIONS",
    "REVERT_PHASE4_FILES_ONLY",
    "PRESERVE_PHASE1_PHASE3_EVIDENCE",
    "PRESERVE_RAW_DATA_AND_DURABLE_EVIDENCE",
]
KNOWN_LIMITS = [
    "NO_PERSISTENT_BACKPRESSURE_STATE",
    "NO_PRODUCTION_QUEUE_OR_WORKER_RUNTIME",
    "NO_PRODUCTION_CALIBRATION",
    "NO_MEASURED_THROUGHPUT_OR_FAIRNESS",
    "NO_PRODUCTION_LOCK_LEASE_OR_FENCING",
    "NO_AUTOMATIC_RESUME_OR_LIFECYCLE_RUNTIME",
    "NO_PROCESS_CRASH_RECOVERY",
    "NO_CLEANUP_RUNTIME",
    "NO_DATABASE_OR_RAW_SOURCE_ACCESS",
    "STATIC_CLOSEOUT_IS_NOT_PRODUCTION_READINESS",
]

EXPECTED_SOURCE = {
    "source_archive_path": "/Users/linzezhang/Downloads/IDS_Taskpack_v0_1_only_中文修订版.zip",
    "source_archive_sha256": "55b782e338610aab6361b7945bb5e290ba60038a06cc765c7c2da801734db6d3",
    "source_member": "IDS_v0_1_Final_Chinese_Revised/stages/STAGE-040_反压策略.md",
    "source_member_match_count": 1,
    "source_member_sha256": "f0ef128467300d7541796f8d51caca673f838cac2552eba2e415a94a07af614d",
    "roadmap_path": "/Users/linzezhang/Downloads/IDS_Codex开发Roadmap_v0_1_only_中文修订版.txt",
    "roadmap_sha256": "a193fd2c44c51d634bf7887a1a6baf7e5199d9a8535e4211e35e97588e2e21a6",
    "instructions_path": "/Users/linzezhang/Downloads/IDS_Codex使用说明_v0_1_only_中文修订版.txt",
    "instructions_sha256": "ce456e06136d5ecc56cd7c9dc926abb5894817dda87bf7667588bf85211794f8",
    "source_verification_status": "SOURCE_VERIFIED",
}
EXPECTED_UPSTREAM = {
    "stage037_state_index": (
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/job_state_model/stage037_job_state_model_index.json",
        "b70bf72ebe4212f45d380c13fbfe429791e1f4a5c73dccbba81211b7adc1c2d3",
    ),
    "stage039_delivery_contract": (
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/retry_dead_letter/stage039_retry_dead_letter_delivery_contract.json",
        "c4aad64a9283de683067aff07026d723c708285c57eef8a0eac4ee1b13f5cb96",
    ),
    "stage039_delivery_checker": (
        "KM_IDSystem/scripts/check_retry_dead_letter_delivery.py",
        "babff5f0be9e6be06508cbe4efbe355c354a65324d0895e7c9c5f3322621e4da",
    ),
    "stage039_review_artifact": (
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE039_STAGE_REVIEW.md",
        "32e621db9d7d4ad87ff4f6788e1de22d7ada9c0f57ce756a76a9608a864c4b9b",
    ),
    "stage040_phase1_contract": (
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/backpressure_policy/stage040_backpressure_policy_contract.json",
        "9298a248fb8a63d159ceef105b6081ba257086646d296fb0697e6747a0c394b4",
    ),
    "stage040_phase1_evidence": (
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE040_PHASE1_BACKPRESSURE_SCOPE_BOUNDARY.md",
        "80d220ef937ce890e47758f23bf993156c6882b0d3ed4ee2875f0d0766b68cf6",
    ),
    "stage040_phase2_contract": (
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/backpressure_policy/stage040_backpressure_runtime_contract.json",
        "2fb9437f85a8c86cbfc8d6002e031554683bdf9b4a421b06c6b9503c6c40b6c1",
    ),
    "stage040_phase2_checker": (
        "KM_IDSystem/scripts/check_backpressure_runtime.py",
        "8442ef6b9ff63e3999205151d5bf8deddbe3085730dc864b5627e6b4ff06da06",
    ),
    "stage040_phase2_evidence": (
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE040_PHASE2_BACKPRESSURE_DECISION_SLICE.md",
        "5b8f1a030034a6cb9f8becc5e42ee4e354d51fb0ac394366e641ebb90fa31c41",
    ),
    "stage040_phase3_contract": (
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/backpressure_policy/stage040_backpressure_scenarios.json",
        "f3f1898cf0fd2b091ccfe0bd1a41253d80e8028990ef29079c69098ef45aa5f4",
    ),
    "stage040_phase3_checker": (
        "KM_IDSystem/scripts/check_backpressure_scenarios.py",
        "c51afd6fb080e0eddb68f4ce584ec4586ba349ca1716cf9e8d86cac38ab9a051",
    ),
    "stage040_phase3_evidence": (
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE040_PHASE3_SCENARIO_VALIDATION.md",
        "d1967211ba0be57f36bb9f510448a53cbab32963ad80abc39f2dbb4fe365707f",
    ),
}
POSITIVE_TRUTH_FLAGS = {
    "taskpack_source_read_performed",
    "backpressure_decision_runtime_performed",
    "actual_disk_observation_performed",
    "actual_isolated_worker_exception_replayed",
    "reviewed_failure_retry_log_replayed",
    "reviewed_transport_shutdown_replayed",
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
    "persistent_queue_write_performed",
    "database_connection_performed",
    "runtime_output_written",
    "measured_throughput_or_fairness_performed",
    "production_lock_runtime_performed",
    "automatic_resume_performed",
    "process_crash_recovery_performed",
    "production_runtime_activation_performed",
    "whole_stage_review_performed",
    "batch_review_performed",
    "github_upload_allowed",
    "app_reinstall_allowed",
}
EXPECTED_ROOT_KEYS = {
    "schema_version",
    "stage",
    "phase",
    "task_id",
    "acceptance_id",
    "execution_mode",
    "valid_result",
    "contract_state",
    "stage_review_status",
    "next_gate",
    "source_binding",
    "phase3_commit_binding",
    "upstream_bindings",
    "delivery_contract",
    "cleanup_allowlist",
    "recovery_handling",
    "safe_shutdown_and_recovery",
    "rollback_contract",
    "known_limits",
    "owner_feedback_contract",
    "review_gate",
    "truth_flags",
}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _phase2_module() -> Any:
    return _load_module(PHASE2_CHECKER, "stage040_phase2_for_delivery")


def _phase3_module() -> Any:
    return _load_module(PHASE3_CHECKER, "stage040_phase3_for_delivery")


def _stage039_delivery_module() -> Any:
    return _load_module(STAGE039_DELIVERY_CHECKER, "stage039_delivery_for_stage040")


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def load_delivery_contract() -> dict[str, Any]:
    return _load_json(CONTRACT_PATH)


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


def _phase3_commit_is_ancestor(value: Any) -> bool:
    if value != {"commit": PHASE3_COMMIT, "required_ancestor_of_head": True}:
        return False
    completed = subprocess.run(
        ["git", "merge-base", "--is-ancestor", PHASE3_COMMIT, "HEAD"],
        cwd=REPO_ROOT,
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return completed.returncode == 0


def validate_delivery_contract(contract: Any) -> dict[str, bool]:
    if not isinstance(contract, dict):
        return {"contract_is_object": False}
    delivery = contract.get("delivery_contract")
    cleanup = contract.get("cleanup_allowlist")
    recovery = contract.get("recovery_handling")
    shutdown = contract.get("safe_shutdown_and_recovery")
    rollback = contract.get("rollback_contract")
    owner = contract.get("owner_feedback_contract")
    review = contract.get("review_gate")
    truth = contract.get("truth_flags")
    return {
        "root_shape_exact": set(contract) == EXPECTED_ROOT_KEYS,
        "identity_exact": (
            contract.get("schema_version")
            == "ids.stage040.backpressure.phase4.delivery.v1"
            and contract.get("stage") == "STAGE-040"
            and contract.get("phase") == "Phase 4"
            and contract.get("task_id") == TASK_ID
            and contract.get("acceptance_id") == ACCEPTANCE_ID
            and contract.get("execution_mode") == EXECUTION_MODE
            and contract.get("valid_result") == VALID_RESULT
            and contract.get("contract_state")
            == "PHASE4_CLOSEOUT_EVIDENCE_REVIEW_PENDING"
            and contract.get("stage_review_status") == "pending_next_run"
            and contract.get("next_gate") == REVIEW_GATE
        ),
        "source_binding_exact": contract.get("source_binding") == EXPECTED_SOURCE,
        "phase3_commit_bound": _phase3_commit_is_ancestor(
            contract.get("phase3_commit_binding")
        ),
        "upstream_bindings_exact": _upstream_valid(
            contract.get("upstream_bindings")
        ),
        "delivery_contract_exact": delivery
        == {
            "policy_version": POLICY_VERSION,
            "state_model_version": "ids.job_state.v1",
            "required_job_type_count": 8,
            "required_job_state_count": 11,
            "required_terminal_state_count": 4,
            "required_transition_count": 21,
            "required_pressure_signals": PRESSURE_SIGNALS,
            "required_decision_actions": DECISION_ACTIONS,
            "failure_retry_log_source": "STAGE039_REVIEWED_PHASE4_ACTUAL_ISOLATED_CONTROL_METADATA",
            "expected_attempt_count": 3,
            "expected_retry_count": 2,
            "expected_max_retries": 2,
            "expected_final_state": "DEAD_LETTERED",
            "actual_project_disk_observation_required": True,
            "production_calibrated": False,
            "stage_review_must_run_separately": True,
        },
        "cleanup_allowlist_exact": cleanup
        == {
            "cleanup_eligible_classes": CLEANUP_CLASSES,
            "protected_artifact_classes": PROTECTED_CLASSES,
            "cleanup_manifest_required": True,
            "required_preconditions": CLEANUP_PRECONDITIONS,
            "runtime_owner": "STAGE-044",
            "delete_execution_allowed": False,
        },
        "recovery_handling_exact": recovery
        == {
            "healthy_new_admission_observed": True,
            "automatic_recovery_eligible_cases": [],
            "successful_automatic_recovery_cases_observed": [],
            "future_automatic_reevaluation_candidates": REEVALUATION_CANDIDATES,
            "manual_action_required_cases": MANUAL_ACTION_CASES,
            "automatic_resume_allowed": False,
            "automatic_resume_runtime_owner": "STAGE-042",
            "process_crash_recovery_runtime_owner": "STAGE-043",
        },
        "safe_shutdown_recovery_exact": shutdown
        == {
            "transport_shutdown_source": "STAGE039_REVIEWED_PHASE4_DELIVERY",
            "shutdown_steps": SHUTDOWN_STEPS,
            "recovery_steps": RECOVERY_STEPS,
            "persistent_backpressure_state_available_after_exit": False,
            "process_termination_allowed": False,
            "automatic_process_recovery_allowed": False,
        },
        "rollback_exact": rollback
        == {"steps": ROLLBACK_STEPS, "destructive_rollback_allowed": False},
        "known_limits_exact": contract.get("known_limits") == KNOWN_LIMITS,
        "owner_feedback_exact": (
            isinstance(owner, dict)
            and set(owner)
            == {"status_zh", "automatic_eligibility_zh", "manual_action_zh", "limit_zh"}
            and all(isinstance(value, str) and value for value in owner.values())
            and "未观察到自动恢复成功" in owner["automatic_eligibility_zh"]
            and "不是生产运行或生产就绪证明" in owner["limit_zh"]
        ),
        "review_gate_exact": review
        == {
            "next_task_id": "IDS-V0_1-STAGE040-REVIEW",
            "must_run_separately": True,
            "phase4_may_mark_stage_reviewed": False,
            "batch_review_allowed": False,
            "stage041_entry_allowed": False,
            "github_upload_allowed": False,
            "app_reinstall_allowed": False,
        },
        "truth_flags_exact": (
            isinstance(truth, dict)
            and set(truth) == POSITIVE_TRUTH_FLAGS | FALSE_TRUTH_FLAGS
            and all(truth.get(key) is True for key in POSITIVE_TRUTH_FLAGS)
            and all(truth.get(key) is False for key in FALSE_TRUTH_FLAGS)
        ),
    }


def _flatten_transitions(value: Mapping[str, Any]) -> list[str]:
    return [
        f"{source}->{target}"
        for source, targets in value.items()
        for target in targets
    ]


def _state_decision_graph(contract: Mapping[str, Any]) -> dict[str, Any]:
    state_model = _load_json(STATE_INDEX_PATH)["state_model"]
    phase1 = _load_json(PHASE1_CONTRACT_PATH)
    transitions = state_model["allowed_transitions"]
    flat = _flatten_transitions(transitions)
    state_lines = ["stateDiagram-v2"] + [
        f"    {item.replace('->', ' --> ')}" for item in flat
    ]
    decision_lines = [
        "flowchart TD",
        '    O["Versioned pressure observation"] --> V{"Valid and fresh?"}',
        '    V -->|No| M["REQUIRE_MANUAL_REVIEW"]',
        '    V -->|Yes| T{"Terminal state?"}',
        '    T -->|Yes| M',
        '    T -->|No| R{"Resource pressure?"}',
        '    R -->|Drive, disk or API| P["PAUSE_RESOURCE_GATE"]',
        '    R -->|No| H{"Hard queue capacity?"}',
        '    H -->|Yes| D["DENY_NEW_ADMISSION"]',
        '    H -->|No| S{"Soft, rate, concurrency or conflict?"}',
        '    S -->|Yes| L["THROTTLE_ADMISSION"]',
        '    S -->|No| A["ADMIT"]',
    ]
    return {
        "state_model_version": state_model["state_model_version"],
        "job_types": copy.deepcopy(state_model["job_types"]),
        "job_states": copy.deepcopy(state_model["job_states"]),
        "terminal_states": copy.deepcopy(state_model["terminal_states"]),
        "allowed_transitions": copy.deepcopy(transitions),
        "allowed_transitions_flat": flat,
        "allowed_transition_count": len(flat),
        "pressure_signals": copy.deepcopy(
            contract["delivery_contract"]["required_pressure_signals"]
        ),
        "decision_actions": copy.deepcopy(
            contract["delivery_contract"]["required_decision_actions"]
        ),
        "phase1_decision_matrix": copy.deepcopy(phase1["decision_matrix"]),
        "mermaid_state_diagram": "\n".join(state_lines),
        "mermaid_backpressure_flow": "\n".join(decision_lines),
        "state_registry_write_performed": False,
    }


def _failure_retry_log(stage039: Mapping[str, Any]) -> dict[str, Any]:
    source = copy.deepcopy(stage039["failure_retry_dead_letter_log"])
    source["source"] = "STAGE039_REVIEWED_PHASE4_ACTUAL_ISOLATED_CONTROL_METADATA"
    source["reviewed_stage039_delivery_valid"] = (
        stage039.get("delivery_contract_valid") is True
        and stage039.get("result") == VALID_RESULT
        and stage039.get("next_gate") == "IDS-STAGE039-REVIEW-GATE"
    )
    return source


def _backpressure_trigger_proof(
    phase2: Mapping[str, Any], phase3: Mapping[str, Any]
) -> dict[str, Any]:
    scenarios = phase3["scenario_results"]
    drive = scenarios["external_drive_offline_pause_candidate"]
    disk = scenarios["actual_disk_observation_and_low_disk_boundary"]
    api = scenarios["external_api_budget_pause_candidate"]
    concurrency = scenarios["same_source_cross_operation_concurrency_throttle"]
    conflict = scenarios["reviewed_lock_conflict_proof"]
    return {
        "QUEUE_SOFT_PRESSURE": {
            "decision_action": phase2["soft_pressure_result"],
            "retry_budget_consumed": False,
            "persistent_write_performed": False,
        },
        "QUEUE_HARD_CAPACITY": {
            "decision_action": phase2["hard_capacity_result"],
            "job_created": False,
            "retry_budget_consumed": False,
            "persistent_write_performed": False,
        },
        "EXTERNAL_DRIVE_OFFLINE": {
            "decision_action": drive["decision_action"],
            "requested_state": drive["requested_state"],
            "state_path": copy.deepcopy(drive["state_path"]),
            "retry_budget_consumed": drive["retry_budget_consumed"],
            "physical_drive_removal_performed": False,
        },
        "DISK_SPACE_INSUFFICIENT": {
            "decision_action": disk["boundary_decision_action"],
            "requested_state": disk["boundary_requested_state"],
            "retry_budget_consumed": disk["retry_budget_consumed"],
            "actual_disk_observation_performed": True,
            "actual_disk_free_bytes": disk["actual_disk_free_bytes"],
            "disk_allocation_performed": False,
        },
        "EXTERNAL_API_BUDGET_INSUFFICIENT": {
            "decision_action": api["decision_action"],
            "requested_state": api["requested_state"],
            "state_path": copy.deepcopy(api["state_path"]),
            "retry_budget_consumed": api["retry_budget_consumed"],
            "external_api_call_performed": False,
        },
        "JOB_TYPE_CONCURRENCY_LIMIT_REACHED": {
            "decision_action": "THROTTLE_ADMISSION",
            "throttled_decision_count": concurrency["throttled_decision_count"],
            "created_job_count": concurrency["created_job_count"],
            "retry_budget_consumed_count": concurrency[
                "retry_budget_consumed_count"
            ],
            "production_lock_runtime_performed": False,
        },
        "SAME_SOURCE_CONFLICT": {
            "decision_action": "THROTTLE_ADMISSION",
            "operation_invocations": conflict["operation_invocations"],
            "conflict_count": conflict["resource_conflict_count"],
            "shared_lock_key_count": conflict["shared_lock_key_count"],
            "production_lock_runtime_performed": False,
        },
    }


def _cleanup_allowlist(
    contract: Mapping[str, Any], phase3: Mapping[str, Any]
) -> dict[str, Any]:
    configured = contract["cleanup_allowlist"]
    protected = phase3["scenario_results"]["protected_cleanup_denied"]
    checks = {
        name: (
            value.get("git_tracked") is True
            and value.get("result_code") == "PROTECTED_ARTIFACT"
            and value.get("delete_allowed") is False
            and value.get("delete_attempted") is False
        )
        for name, value in protected["artifact_results"].items()
    }
    return {
        "cleanup_eligible_classes": copy.deepcopy(
            configured["cleanup_eligible_classes"]
        ),
        "protected_artifact_classes": copy.deepcopy(
            configured["protected_artifact_classes"]
        ),
        "cleanup_manifest_required": configured["cleanup_manifest_required"],
        "required_preconditions": copy.deepcopy(configured["required_preconditions"]),
        "protected_ref_count": len(checks),
        "phase3_protected_ref_checks": checks,
        "cleanup_runtime_performed": False,
        "delete_attempt_performed": False,
        "runtime_owner": configured["runtime_owner"],
    }


def _recovery_handling(
    contract: Mapping[str, Any], phase2: Mapping[str, Any]
) -> dict[str, Any]:
    configured = contract["recovery_handling"]
    return {
        "healthy_new_admission_observed": (
            phase2.get("actual_disk_signal") == "HEALTHY"
            and phase2.get("slice_valid") is True
        ),
        "automatic_recovery_eligible_cases": [],
        "successful_automatic_recovery_cases_observed": [],
        "future_automatic_reevaluation_candidates": copy.deepcopy(
            configured["future_automatic_reevaluation_candidates"]
        ),
        "manual_action_required_cases": copy.deepcopy(
            configured["manual_action_required_cases"]
        ),
        "automatic_resume_allowed": configured["automatic_resume_allowed"],
        "automatic_resume_performed": False,
        "automatic_resume_runtime_owner": configured[
            "automatic_resume_runtime_owner"
        ],
        "process_crash_recovery_performed": False,
        "process_crash_recovery_runtime_owner": configured[
            "process_crash_recovery_runtime_owner"
        ],
    }


def _safe_shutdown_and_recovery(
    contract: Mapping[str, Any], stage039: Mapping[str, Any]
) -> dict[str, Any]:
    configured = contract["safe_shutdown_and_recovery"]
    source = stage039["safe_shutdown_and_recovery"]
    return {
        "transport_shutdown_source": configured["transport_shutdown_source"],
        "transport_orderly_shutdown_proved": source[
            "transport_orderly_shutdown_proved"
        ],
        "transport_queue_closed": source["transport_queue_closed"],
        "transport_resource_locks_released": source[
            "transport_resource_locks_released"
        ],
        "transport_active_work_cancelled": source[
            "transport_active_work_cancelled"
        ],
        "shutdown_steps": copy.deepcopy(configured["shutdown_steps"]),
        "recovery_steps": copy.deepcopy(configured["recovery_steps"]),
        "persistent_backpressure_state_available_after_exit": configured[
            "persistent_backpressure_state_available_after_exit"
        ],
        "process_termination_performed": False,
        "automatic_process_recovery_performed": False,
    }


def _delivery_checks(
    graph: Mapping[str, Any],
    log: Mapping[str, Any],
    proof: Mapping[str, Any],
    cleanup: Mapping[str, Any],
    recovery: Mapping[str, Any],
    shutdown: Mapping[str, Any],
) -> dict[str, bool]:
    return {
        "state_and_decision_graph_exact": (
            graph.get("state_model_version") == "ids.job_state.v1"
            and len(graph.get("job_types", [])) == 8
            and len(graph.get("job_states", [])) == 11
            and len(graph.get("terminal_states", [])) == 4
            and graph.get("allowed_transition_count") == 21
            and graph.get("pressure_signals") == PRESSURE_SIGNALS
            and graph.get("decision_actions") == DECISION_ACTIONS
        ),
        "failure_retry_log_reviewed_actual_bounded": (
            log.get("source")
            == "STAGE039_REVIEWED_PHASE4_ACTUAL_ISOLATED_CONTROL_METADATA"
            and log.get("reviewed_stage039_delivery_valid") is True
            and log.get("state_history") == EXPECTED_STATE_HISTORY
            and log.get("attempt_count") == 3
            and log.get("retry_count") == 2
            and log.get("max_retries") == 2
            and log.get("final_state") == "DEAD_LETTERED"
            and log.get("persisted") is False
        ),
        "queue_pressure_proof_exact": (
            proof.get("QUEUE_SOFT_PRESSURE", {}).get("decision_action")
            == "THROTTLE_ADMISSION"
            and proof.get("QUEUE_HARD_CAPACITY", {}).get("decision_action")
            == "DENY_NEW_ADMISSION"
            and proof.get("QUEUE_HARD_CAPACITY", {}).get("job_created") is False
        ),
        "resource_pressure_proof_exact": all(
            proof.get(signal, {}).get("decision_action") == "PAUSE_RESOURCE_GATE"
            and proof.get(signal, {}).get("retry_budget_consumed") is False
            for signal in (
                "EXTERNAL_DRIVE_OFFLINE",
                "DISK_SPACE_INSUFFICIENT",
                "EXTERNAL_API_BUDGET_INSUFFICIENT",
            )
        ),
        "concurrency_and_conflict_proof_exact": (
            proof.get("JOB_TYPE_CONCURRENCY_LIMIT_REACHED", {}).get(
                "throttled_decision_count"
            )
            == 4
            and proof.get("JOB_TYPE_CONCURRENCY_LIMIT_REACHED", {}).get(
                "created_job_count"
            )
            == 0
            and proof.get("SAME_SOURCE_CONFLICT", {}).get("operation_invocations")
            == 1
            and proof.get("SAME_SOURCE_CONFLICT", {}).get("conflict_count") == 3
        ),
        "cleanup_allowlist_narrow_and_protected": (
            cleanup.get("cleanup_eligible_classes") == CLEANUP_CLASSES
            and cleanup.get("protected_artifact_classes") == PROTECTED_CLASSES
            and cleanup.get("protected_ref_count") == 5
            and all(cleanup.get("phase3_protected_ref_checks", {}).values())
            and cleanup.get("cleanup_runtime_performed") is False
            and cleanup.get("delete_attempt_performed") is False
        ),
        "automatic_and_manual_handling_truthful": (
            recovery.get("healthy_new_admission_observed") is True
            and recovery.get("automatic_recovery_eligible_cases") == []
            and recovery.get("successful_automatic_recovery_cases_observed") == []
            and recovery.get("manual_action_required_cases") == MANUAL_ACTION_CASES
            and recovery.get("automatic_resume_allowed") is False
            and recovery.get("automatic_resume_performed") is False
            and recovery.get("process_crash_recovery_performed") is False
        ),
        "safe_shutdown_and_recovery_fail_closed": (
            shutdown.get("transport_orderly_shutdown_proved") is True
            and shutdown.get("transport_queue_closed") is True
            and shutdown.get("transport_resource_locks_released") is True
            and shutdown.get("transport_active_work_cancelled") is False
            and shutdown.get("shutdown_steps") == SHUTDOWN_STEPS
            and shutdown.get("recovery_steps") == RECOVERY_STEPS
            and shutdown.get("persistent_backpressure_state_available_after_exit")
            is False
            and shutdown.get("process_termination_performed") is False
            and shutdown.get("automatic_process_recovery_performed") is False
        ),
    }


def _blank_report(
    contract: Mapping[str, Any], checks: Mapping[str, bool]
) -> dict[str, Any]:
    truth = contract.get("truth_flags")
    truth = truth if isinstance(truth, dict) else {}
    return {
        "schema_version": "ids.stage040.backpressure.phase4.report.v1",
        "stage": "STAGE-040",
        "phase": "Phase 4",
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "execution_mode": EXECUTION_MODE,
        "policy_version": POLICY_VERSION,
        "contract_checks": dict(checks),
        "contract_valid": bool(checks) and all(checks.values()),
        "delivery_checks_performed": False,
        "delivery_checks": {},
        "delivery_contract_valid": False,
        "result": "BLOCKED_INVALID_OR_UNCHECKED_DELIVERY_CONTRACT",
        "stage_review_status": "blocked_invalid_delivery_contract",
        "next_gate": PHASE4_GATE,
        "execution_ready": False,
        "state_decision_graph": {},
        "failure_retry_log": {},
        "backpressure_trigger_proof": {},
        "cleanup_allowlist": {},
        "recovery_handling": {},
        "safe_shutdown_and_recovery": {},
        "rollback_steps": copy.deepcopy(ROLLBACK_STEPS),
        "known_limits": copy.deepcopy(KNOWN_LIMITS),
        "source_error_type": None,
        **{key: bool(truth.get(key, False)) for key in POSITIVE_TRUTH_FLAGS},
        **{key: bool(truth.get(key, False)) for key in FALSE_TRUTH_FLAGS},
        "owner_feedback_zh": "交付合同未通过；保持停止并返回 Phase 4 修复。",
    }


def build_stage040_phase4_delivery_report(
    *,
    contract: Optional[Any] = None,
    execute_delivery_checks: bool = True,
) -> dict[str, Any]:
    try:
        contract_value = (
            copy.deepcopy(contract) if contract is not None else load_delivery_contract()
        )
    except (OSError, ValueError, json.JSONDecodeError):
        contract_value = {}
    checks = validate_delivery_contract(contract_value)
    safe_contract = contract_value if isinstance(contract_value, dict) else {}
    report = _blank_report(safe_contract, checks)
    if not report["contract_valid"] or not execute_delivery_checks:
        if report["contract_valid"]:
            report["stage_review_status"] = "blocked_delivery_checks_not_executed"
        return report

    try:
        phase2 = _phase2_module().build_stage040_phase2_report()
        phase3 = _phase3_module().build_stage040_phase3_report()
        stage039 = _stage039_delivery_module().build_stage039_phase4_delivery_report()
        if phase2.get("slice_valid") is not True:
            raise RuntimeError("invalid Stage040 Phase 2 prerequisite")
        if phase3.get("scenario_validation_valid") is not True:
            raise RuntimeError("invalid Stage040 Phase 3 prerequisite")
        if stage039.get("delivery_contract_valid") is not True:
            raise RuntimeError("invalid reviewed Stage039 delivery prerequisite")

        graph = _state_decision_graph(safe_contract)
        log = _failure_retry_log(stage039)
        proof = _backpressure_trigger_proof(phase2, phase3)
        cleanup = _cleanup_allowlist(safe_contract, phase3)
        recovery = _recovery_handling(safe_contract, phase2)
        shutdown = _safe_shutdown_and_recovery(safe_contract, stage039)
        delivery_checks = _delivery_checks(
            graph, log, proof, cleanup, recovery, shutdown
        )
    except Exception as exc:
        report["source_error_type"] = type(exc).__name__
        report["stage_review_status"] = "blocked_upstream_or_delivery_failure"
        report["owner_feedback_zh"] = (
            "上游或交付检查失败；保持停止并返回 Phase 4 修复。"
        )
        return report

    valid = bool(delivery_checks) and all(delivery_checks.values())
    owner = safe_contract["owner_feedback_contract"]
    report.update(
        {
            "delivery_checks_performed": True,
            "delivery_checks": delivery_checks,
            "delivery_contract_valid": valid,
            "result": VALID_RESULT if valid else "FAIL_CLOSEOUT_CHECKS",
            "stage_review_status": (
                "pending_next_run" if valid else "blocked_delivery_check_failure"
            ),
            "next_gate": REVIEW_GATE if valid else PHASE4_GATE,
            "state_decision_graph": graph,
            "failure_retry_log": log,
            "backpressure_trigger_proof": proof,
            "cleanup_allowlist": cleanup,
            "recovery_handling": recovery,
            "safe_shutdown_and_recovery": shutdown,
            "owner_feedback_zh": " ".join(
                [
                    owner["status_zh"],
                    owner["automatic_eligibility_zh"],
                    owner["manual_action_zh"],
                    owner["limit_zh"],
                ]
            ),
        }
    )
    return report


def main() -> int:
    report = build_stage040_phase4_delivery_report()
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if report["delivery_contract_valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
