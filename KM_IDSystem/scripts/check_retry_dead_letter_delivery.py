#!/usr/bin/env python3
"""Validate STAGE-039 Phase 4 retry/dead-letter delivery evidence."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
from typing import Any, Mapping, Optional


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PROJECT_ROOT.parent
PURSUE_ROOT = PROJECT_ROOT / "docs" / "pursuing_goal" / "ids_v0_1"
CONTRACT_PATH = (
    PURSUE_ROOT
    / "retry_dead_letter"
    / "stage039_retry_dead_letter_delivery_contract.json"
)
STATE_INDEX_PATH = (
    PURSUE_ROOT / "job_state_model" / "stage037_job_state_model_index.json"
)
PHASE1_CONTRACT_PATH = (
    PURSUE_ROOT
    / "retry_dead_letter"
    / "stage039_retry_dead_letter_policy_contract.json"
)
PHASE2_CHECKER = PROJECT_ROOT / "scripts" / "check_retry_dead_letter_runtime.py"
PHASE3_CHECKER = PROJECT_ROOT / "scripts" / "check_retry_dead_letter_scenarios.py"
STAGE038_DELIVERY_CHECKER = (
    PROJECT_ROOT / "scripts" / "check_worker_queue_delivery.py"
)

TASK_ID = "IDS-V0_1-STAGE039-P4"
ACCEPTANCE_ID = "ACC-STAGE-039"
POLICY_VERSION = "ids.retry_policy.v0_1.stage039.p2"
EXECUTION_MODE = "ISOLATED_NON_PRODUCTION_CLOSEOUT_EVIDENCE"
VALID_RESULT = "PASS_ISOLATED_CLOSEOUT_PRODUCTION_DISABLED"
REVIEW_GATE = "IDS-STAGE039-REVIEW-GATE"
PHASE4_GATE = "IDS-STAGE039-P4-GATE"

EXPECTED_UPSTREAM = {
    "stage037_state_index": (
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/job_state_model/"
        "stage037_job_state_model_index.json",
        "b70bf72ebe4212f45d380c13fbfe429791e1f4a5c73dccbba81211b7adc1c2d3",
    ),
    "stage038_delivery_contract": (
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/worker_queue_baseline/"
        "stage038_worker_queue_delivery_contract.json",
        "a4067c25b46340c33bee5017c286d6867d2b72e8fa208430c005d6b1a342c7e4",
    ),
    "stage038_delivery_checker": (
        "KM_IDSystem/scripts/check_worker_queue_delivery.py",
        "305536595643979e34be5b3fdbc8e1c850f9869d4cd656331f4af0c7e2c12fd6",
    ),
    "stage038_review_artifact": (
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE038_STAGE_REVIEW.md",
        "5bb4cb3382f97ded9228d278c4cfb34fc5f0a65b8858263ed0c9bbd6c035eb04",
    ),
    "stage039_phase1_policy_contract": (
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/retry_dead_letter/"
        "stage039_retry_dead_letter_policy_contract.json",
        "d9b1a1dc2d05eaf02cdc2a6ead6d46d6f1c469186b68106639f5bc48347d53e8",
    ),
    "stage039_phase1_evidence": (
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/"
        "STAGE039_PHASE1_RETRY_DEAD_LETTER_SCOPE_BOUNDARY.md",
        "4c647ad0bf200326f15d9aa5c339a41c14f9c0fb70bf1ff9b1e3ec699a8c44b4",
    ),
    "stage039_phase2_runtime_contract": (
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/retry_dead_letter/"
        "stage039_retry_dead_letter_runtime_contract.json",
        "237812d5fc16cd59e09d7261709d36ba6c98cd64340c98908112dfc85c9a39b9",
    ),
    "stage039_phase2_checker": (
        "KM_IDSystem/scripts/check_retry_dead_letter_runtime.py",
        "f549149e70a532ab61c1d639d9176f1ea9b8a5f0fc5be5dee228fa1a1db032f0",
    ),
    "stage039_phase2_evidence": (
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/"
        "STAGE039_PHASE2_RETRY_DEAD_LETTER_SLICE.md",
        "ac505e82d1bd915f4337ea6450d18cdee568c0be9eeb48b801003f74fcd44989",
    ),
    "stage039_phase3_scenario_contract": (
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/retry_dead_letter/"
        "stage039_retry_dead_letter_scenarios.json",
        "1799a3c6ca723d6157e86d9134842376f5bbf60ee42ed64c9538c62aa9fcb780",
    ),
    "stage039_phase3_checker": (
        "KM_IDSystem/scripts/check_retry_dead_letter_scenarios.py",
        "93a05d1c7abe82f88eefb95ad0a08c0da479ca702a1e4edfb94710567c5bc43b",
    ),
    "stage039_phase3_evidence": (
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/"
        "STAGE039_PHASE3_SCENARIO_VALIDATION.md",
        "46c323896d1269dd2a5c144855d3bec9dd8d71226e62c31a6fac7b5f6e52a6dd",
    ),
}
EXPECTED_FAILURE_CLASSES = [
    "TRANSIENT_RETRYABLE",
    "PERMANENT_NON_RETRYABLE",
    "RESOURCE_CONDITION_PAUSE",
    "RETRY_EXHAUSTED",
    "POLICY_OR_AUTHORIZATION_BLOCK",
    "INDETERMINATE_UNSAFE",
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
BACKPRESSURE_SIGNALS = [
    "QUEUE_CAPACITY_REACHED",
    "EXTERNAL_DRIVE_OFFLINE",
    "LOW_DISK",
    "EXTERNAL_API_BUDGET_INSUFFICIENT",
    "SAME_SOURCE_CONFLICT",
]
ELIGIBLE_CLEANUP_CLASSES = ["TEMPORARY_PARTIAL_OUTPUT", "REBUILDABLE_CACHE"]
PROTECTED_CLASSES = [
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
AUTOMATIC_RETRY_CODES = [
    "TRANSIENT_DEPENDENCY_UNAVAILABLE",
    "TRANSIENT_OPERATION_TIMEOUT",
]
AUTOMATIC_RETRY_CONDITIONS = [
    "EXACT_VERSIONED_POLICY",
    "EXACT_SAFE_ERROR_CODE_ALLOWLIST_MATCH",
    "RETRY_BUDGET_AVAILABLE",
    "RESOURCE_GATES_PASS",
    "COMPARE_AND_SET_PASS",
    "IDEMPOTENCY_KEY_PASS",
]
MANUAL_ACTION_CASES = [
    "RETRY_EXHAUSTED",
    "PERMANENT_NON_RETRYABLE_CONTINUATION",
    "UNKNOWN_OR_MISSING_SAFE_ERROR_CODE",
    "POLICY_OR_AUTHORIZATION_BLOCK",
    "WORKER_PROCESS_LOST",
    "RESOURCE_GATE_REVALIDATION",
    "SAME_SOURCE_CONFLICT",
    "TERMINAL_MANUAL_RERUN",
]
RETRY_SHUTDOWN_STEPS = [
    "STOP_NEW_RETRY_RESERVATIONS",
    "FREEZE_DUE_RETRY_ADMISSION",
    "PRESERVE_TERMINAL_AND_PENDING_SNAPSHOTS",
    "VERIFY_NO_PERSISTENT_OR_RUNTIME_OUTPUT",
    "REQUIRE_OWNER_REVALIDATION_BEFORE_NEW_SESSION",
]
RECOVERY_STEPS = [
    "VERIFY_EXACT_POLICY_AND_SOURCE_BINDINGS",
    "REVALIDATE_OWNER_AND_RESOURCE_GATES",
    "CREATE_NEW_LINKED_JOB_FOR_TERMINAL_SOURCE",
    "DO_NOT_REOPEN_TERMINAL_HISTORY",
    "DEFER_PROCESS_CRASH_RECOVERY_TO_STAGE043",
]
ROLLBACK_STEPS = [
    "STOP_ON_INVALID_DELIVERY_CONTRACT",
    "NO_AUTOMATIC_RETRY",
    "STOP_NEW_RETRY_RESERVATIONS",
    "REVERT_PHASE4_FILES_ONLY",
    "PRESERVE_PHASE1_PHASE3_EVIDENCE",
    "PRESERVE_RAW_DATA_AND_DURABLE_EVIDENCE",
]
KNOWN_LIMITS = [
    "NO_PERSISTENT_RETRY_OR_DEAD_LETTER_QUEUE",
    "NO_SUCCESSFUL_AUTOMATIC_RECOVERY_OBSERVED",
    "NO_MEASURED_BACKPRESSURE_OR_FAIRNESS_RUNTIME",
    "NO_PRODUCTION_LOCK_LEASE_OR_FENCING",
    "NO_AUTOMATIC_RESUME_OR_LIFECYCLE_RUNTIME",
    "NO_PROCESS_CRASH_RECOVERY",
    "NO_CLEANUP_RUNTIME",
    "NO_DATABASE_OR_RAW_SOURCE_ACCESS",
    "POLICY_PARAMETERS_REMAIN_UNCALIBRATED_ASSUMPTIONS",
    "STATIC_CLOSEOUT_IS_NOT_PRODUCTION_READINESS",
]
FALSE_TRUTH_FLAGS = {
    "ids_business_source_read_performed",
    "raw_metadata_content_accessed",
    "fake_ids_business_data_used",
    "real_ids_business_job_created",
    "production_runtime_activation_performed",
    "persistent_queue_write_performed",
    "database_connection_performed",
    "runtime_output_written",
    "measured_backpressure_runtime_performed",
    "production_lock_runtime_performed",
    "automatic_lifecycle_runtime_performed",
    "process_crash_recovery_performed",
    "cleanup_runtime_performed",
    "whole_stage_review_performed",
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
        raise RuntimeError(f"unable to load module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _phase2_module() -> Any:
    return _load_module(PHASE2_CHECKER, "stage039_phase4_phase2")


def _phase3_module() -> Any:
    return _load_module(PHASE3_CHECKER, "stage039_phase4_phase3")


def _stage038_delivery_module() -> Any:
    return _load_module(
        STAGE038_DELIVERY_CHECKER, "stage039_phase4_stage038_delivery"
    )


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def load_delivery_contract() -> dict[str, Any]:
    return _load_json(CONTRACT_PATH)


def _keys_exact(value: Any, expected: set[str]) -> bool:
    return isinstance(value, dict) and set(value) == expected


def _upstream_valid(value: Any) -> bool:
    if not isinstance(value, dict) or set(value) != set(EXPECTED_UPSTREAM):
        return False
    for key, (expected_ref, expected_hash) in EXPECTED_UPSTREAM.items():
        binding = value.get(key)
        if not _keys_exact(binding, {"ref", "sha256"}):
            return False
        if binding.get("ref") != expected_ref or binding.get("sha256") != expected_hash:
            return False
        path = REPO_ROOT / expected_ref
        if not path.is_file() or sha256_file(path) != expected_hash:
            return False
    return True


def _phase3_commit_is_ancestor(value: Any) -> bool:
    if not _keys_exact(value, {"commit", "required_ancestor_of_head"}):
        return False
    if (
        value.get("commit") != "75fc7c896e1403ae6865164f1a36c5c85bb2a956"
        or value.get("required_ancestor_of_head") is not True
    ):
        return False
    result = subprocess.run(
        ["git", "merge-base", "--is-ancestor", value["commit"], "HEAD"],
        cwd=REPO_ROOT,
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return result.returncode == 0


def validate_delivery_contract(contract: Any) -> dict[str, bool]:
    if not isinstance(contract, dict):
        return {"contract_is_object": False}
    source = contract.get("source_binding")
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
            == "ids.stage039.retry_dead_letter.phase4.delivery.v1"
            and contract.get("stage") == "STAGE-039"
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
        "source_binding_exact": (
            _keys_exact(
                source,
                {
                    "source_archive_path",
                    "source_archive_sha256",
                    "source_member",
                    "source_member_match_count",
                    "source_member_sha256",
                    "roadmap_path",
                    "roadmap_sha256",
                    "instructions_path",
                    "instructions_sha256",
                    "source_verification_status",
                },
            )
            and source.get("source_archive_path")
            == "/Users/linzezhang/Downloads/IDS_Taskpack_v0_1_only_中文修订版.zip"
            and source.get("source_archive_sha256")
            == "55b782e338610aab6361b7945bb5e290ba60038a06cc765c7c2da801734db6d3"
            and source.get("source_member")
            == "IDS_v0_1_Final_Chinese_Revised/stages/STAGE-039_重试与死信策略.md"
            and source.get("source_member_match_count") == 1
            and source.get("source_member_sha256")
            == "504caf72a6aeab67a650b4b096e728f03269f6ca8798f6e8a5c51210c8ddd7d9"
            and source.get("roadmap_path")
            == "/Users/linzezhang/Downloads/IDS_Codex开发Roadmap_v0_1_only_中文修订版.txt"
            and source.get("roadmap_sha256")
            == "a193fd2c44c51d634bf7887a1a6baf7e5199d9a8535e4211e35e97588e2e21a6"
            and source.get("instructions_path")
            == "/Users/linzezhang/Downloads/IDS_Codex使用说明_v0_1_only_中文修订版.txt"
            and source.get("instructions_sha256")
            == "ce456e06136d5ecc56cd7c9dc926abb5894817dda87bf7667588bf85211794f8"
            and source.get("source_verification_status") == "SOURCE_VERIFIED"
        ),
        "phase3_commit_bound": _phase3_commit_is_ancestor(
            contract.get("phase3_commit_binding")
        ),
        "upstream_bindings_exact": _upstream_valid(contract.get("upstream_bindings")),
        "delivery_contract_exact": (
            delivery
            == {
                "policy_version": POLICY_VERSION,
                "state_model_version": "ids.job_state.v1",
                "required_job_type_count": 8,
                "required_job_state_count": 11,
                "required_terminal_state_count": 4,
                "required_transition_count": 21,
                "required_failure_classes": EXPECTED_FAILURE_CLASSES,
                "required_state_history": EXPECTED_STATE_HISTORY,
                "expected_attempt_count": 3,
                "expected_retry_count": 2,
                "expected_max_retries": 2,
                "expected_final_state": "DEAD_LETTERED",
                "required_backpressure_signals": BACKPRESSURE_SIGNALS,
                "stage_review_must_run_separately": True,
            }
        ),
        "cleanup_allowlist_exact": (
            cleanup
            == {
                "eligible_artifact_classes": ELIGIBLE_CLEANUP_CLASSES,
                "protected_artifact_classes": PROTECTED_CLASSES,
                "cleanup_manifest_required": True,
                "required_preconditions": CLEANUP_PRECONDITIONS,
                "runtime_owner": "STAGE-044",
                "delete_execution_allowed": False,
            }
        ),
        "recovery_handling_exact": (
            recovery
            == {
                "automatic_retry_eligible_safe_error_codes": AUTOMATIC_RETRY_CODES,
                "automatic_retry_required_conditions": AUTOMATIC_RETRY_CONDITIONS,
                "successful_automatic_recovery_cases_observed": [],
                "manual_action_required_cases": MANUAL_ACTION_CASES,
                "manual_rerun_candidate_only": True,
                "manual_rerun_job_created": False,
                "automatic_resume_allowed": False,
                "automatic_resume_runtime_owner": "STAGE-042",
                "process_crash_recovery_runtime_owner": "STAGE-043",
            }
        ),
        "safe_shutdown_recovery_exact": (
            shutdown
            == {
                "transport_shutdown_source": "STAGE038_REVIEWED_ISOLATED_DELIVERY",
                "retry_shutdown_steps": RETRY_SHUTDOWN_STEPS,
                "recovery_steps": RECOVERY_STEPS,
                "persistent_retry_state_available_after_exit": False,
                "process_termination_allowed": False,
                "automatic_process_recovery_allowed": False,
            }
        ),
        "rollback_exact": (
            rollback
            == {"steps": ROLLBACK_STEPS, "destructive_rollback_allowed": False}
        ),
        "known_limits_exact": contract.get("known_limits") == KNOWN_LIMITS,
        "owner_feedback_exact": (
            _keys_exact(
                owner,
                {
                    "status_zh",
                    "automatic_eligibility_zh",
                    "manual_action_zh",
                    "limit_zh",
                },
            )
            and all(isinstance(value, str) and value for value in owner.values())
            and "本轮未观察到自动恢复成功" in owner["automatic_eligibility_zh"]
            and "不是生产运行或生产就绪证明" in owner["limit_zh"]
        ),
        "review_gate_exact": (
            review
            == {
                "next_task_id": "IDS-V0_1-STAGE039-REVIEW",
                "must_run_separately": True,
                "phase4_may_mark_stage_reviewed": False,
                "stage040_entry_allowed": False,
                "github_upload_allowed": False,
                "app_reinstall_allowed": False,
            }
        ),
        "truth_flags_exact": (
            isinstance(truth, dict)
            and set(truth) == FALSE_TRUTH_FLAGS | {"taskpack_source_read_performed"}
            and truth.get("taskpack_source_read_performed") is True
            and all(truth.get(key) is False for key in FALSE_TRUTH_FLAGS)
        ),
    }


def _flatten_transitions(value: Mapping[str, Any]) -> list[str]:
    result: list[str] = []
    for source, targets in value.items():
        for target in targets:
            result.append(f"{source}->{target}")
    return result


def _state_decision_graph() -> dict[str, Any]:
    state_index = _load_json(STATE_INDEX_PATH)
    phase1 = _load_json(PHASE1_CONTRACT_PATH)
    state_model = state_index["state_model"]
    transitions = state_model["allowed_transitions"]
    flat = _flatten_transitions(transitions)
    state_lines = ["stateDiagram-v2"] + [
        f"    {item.replace('->', ' --> ')}" for item in flat
    ]
    decision_lines = [
        "flowchart TD",
        '    F["Safe failure observation"] --> C{"Exact classification"}',
        '    C -->|TRANSIENT_RETRYABLE| R["SCHEDULE_RETRY -> RETRY_WAIT"]',
        '    C -->|PERMANENT_NON_RETRYABLE| X["FAIL_TERMINAL -> FAILED"]',
        '    C -->|RESOURCE_CONDITION_PAUSE| P["PAUSE_RESOURCE_GATE -> PAUSED"]',
        '    C -->|RETRY_EXHAUSTED| D["DEAD_LETTER -> DEAD_LETTERED"]',
        '    C -->|POLICY_OR_AUTHORIZATION_BLOCK| M["REQUIRE_MANUAL_REVIEW -> FAILED"]',
        '    C -->|INDETERMINATE_UNSAFE| M',
    ]
    return {
        "state_model_version": state_model["state_model_version"],
        "job_types": copy.deepcopy(state_model["job_types"]),
        "job_states": copy.deepcopy(state_model["job_states"]),
        "terminal_states": copy.deepcopy(state_model["terminal_states"]),
        "allowed_transitions": copy.deepcopy(transitions),
        "allowed_transitions_flat": flat,
        "allowed_transition_count": len(flat),
        "failure_decisions": copy.deepcopy(phase1["failure_classification"]),
        "mermaid_state_diagram": "\n".join(state_lines),
        "mermaid_decision_flow": "\n".join(decision_lines),
        "state_registry_write_performed": False,
    }


def _failure_retry_dead_letter_log(phase2: Mapping[str, Any]) -> dict[str, Any]:
    final = phase2["final_record"]
    history = phase2["state_history"]
    return {
        "source": "STAGE039_PHASE2_ACTUAL_ISOLATED_CONTROL_METADATA",
        "policy_version": phase2["policy_version"],
        "job_id": final["job_id"],
        "state_history": copy.deepcopy(history),
        "attempt_count": history.count("CLAIMED"),
        "retry_count": final["retry_count"],
        "max_retries": final["max_retries"],
        "final_state": final["machine_state"],
        "retry_disposition": final["retry_disposition"],
        "safe_error_code": final["safe_error_code"],
        "error_ref": final["error_ref"],
        "input_refs": copy.deepcopy(final["input_refs"]),
        "output_refs": copy.deepcopy(final["output_refs"]),
        "checkpoint_ref": final["checkpoint_ref"],
        "audit_ref": final["audit_ref"],
        "owner_status": copy.deepcopy(final["owner_status"]),
        "retry_reservation_performed": phase2["retry_reservation_performed"],
        "retry_admission_performed": phase2["retry_admission_performed"],
        "dead_letter_metadata_transition_performed": phase2[
            "dead_letter_metadata_transition_performed"
        ],
        "persisted": final["persisted"],
        "raw_payload_copied": False,
    }


def _backpressure_trigger_proof(
    stage038: Mapping[str, Any], phase3: Mapping[str, Any]
) -> dict[str, Any]:
    stage038_proof = stage038["backpressure_trigger_proof"]
    scenarios = phase3["scenario_results"]
    return {
        "capacity": copy.deepcopy(stage038_proof["capacity"]),
        "resource_pauses": {
            "external_drive_offline": copy.deepcopy(
                scenarios["external_drive_offline_pending_retry_pause"]
            ),
            "low_disk": copy.deepcopy(
                scenarios["actual_low_disk_pending_retry_pause_without_allocation"]
            ),
            "external_api_budget": copy.deepcopy(
                scenarios["external_api_budget_pending_retry_pause"]
            ),
        },
        "same_source_conflict": copy.deepcopy(
            scenarios["same_source_cross_operation_lock"]
        ),
        "retry_budget_consumed_by_resource_pause": False,
        "measured_backpressure_runtime_performed": False,
        "automatic_resume_performed": False,
        "runtime_owner": "STAGE-040",
    }


def _cleanup_allowlist(
    contract: Mapping[str, Any], phase3: Mapping[str, Any]
) -> dict[str, Any]:
    configured = contract["cleanup_allowlist"]
    protected = phase3["scenario_results"]["protected_cleanup_denied"]
    checks = {
        key: (
            value.get("git_tracked") is True
            and value.get("result_code") == "PROTECTED_ARTIFACT"
            and value.get("delete_allowed") is False
            and value.get("delete_attempted") is False
        )
        for key, value in protected["artifact_results"].items()
    }
    return {
        "eligible_artifact_classes": copy.deepcopy(
            configured["eligible_artifact_classes"]
        ),
        "protected_artifact_classes": copy.deepcopy(
            configured["protected_artifact_classes"]
        ),
        "cleanup_manifest_required": configured["cleanup_manifest_required"],
        "required_preconditions": copy.deepcopy(configured["required_preconditions"]),
        "phase3_protected_ref_checks": checks,
        "cleanup_runtime_performed": False,
        "delete_attempt_performed": False,
        "runtime_owner": configured["runtime_owner"],
    }


def _recovery_handling(
    contract: Mapping[str, Any], phase2: Mapping[str, Any], phase3: Mapping[str, Any]
) -> dict[str, Any]:
    configured = contract["recovery_handling"]
    rerun = phase3["scenario_results"]["manual_rerun_lineage_idempotent"]
    return {
        "automatic_retry_eligible_safe_error_codes": copy.deepcopy(
            configured["automatic_retry_eligible_safe_error_codes"]
        ),
        "automatic_retry_required_conditions": copy.deepcopy(
            configured["automatic_retry_required_conditions"]
        ),
        "controlled_retry_admission_observed": phase2["retry_admission_performed"],
        "successful_automatic_recovery_cases_observed": [],
        "manual_action_required_cases": copy.deepcopy(
            configured["manual_action_required_cases"]
        ),
        "manual_rerun_candidate_only": rerun["candidate_only"],
        "manual_rerun_first_result_code": rerun["first_result_code"],
        "manual_rerun_replay_idempotent": rerun["replay_idempotent"],
        "manual_rerun_job_created": rerun["job_created"],
        "manual_rerun_persisted": rerun["persisted"],
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
    contract: Mapping[str, Any], stage038: Mapping[str, Any]
) -> dict[str, Any]:
    configured = contract["safe_shutdown_and_recovery"]
    transport = stage038["safe_shutdown"]
    return {
        "transport_shutdown_source": configured["transport_shutdown_source"],
        "transport_orderly_shutdown_proved": (
            transport["final_record"]["machine_state"] == "SUCCEEDED"
            and transport["queue_closed"] is True
            and transport["all_resource_locks_released"] is True
            and transport["post_shutdown_submission"]["result_code"]
            == "QUEUE_CLOSED"
        ),
        "transport_queue_closed": transport["queue_closed"],
        "transport_resource_locks_released": transport[
            "all_resource_locks_released"
        ],
        "transport_active_work_cancelled": transport["active_work_cancelled"],
        "retry_shutdown_steps": copy.deepcopy(configured["retry_shutdown_steps"]),
        "recovery_steps": copy.deepcopy(configured["recovery_steps"]),
        "persistent_retry_state_available_after_exit": configured[
            "persistent_retry_state_available_after_exit"
        ],
        "process_termination_performed": False,
        "automatic_process_recovery_performed": False,
    }


def _delivery_checks(
    graph: Mapping[str, Any],
    log: Mapping[str, Any],
    backpressure: Mapping[str, Any],
    cleanup: Mapping[str, Any],
    recovery: Mapping[str, Any],
    shutdown: Mapping[str, Any],
) -> dict[str, bool]:
    pauses = backpressure.get("resource_pauses", {})
    return {
        "state_decision_graph_exact": (
            graph.get("state_model_version") == "ids.job_state.v1"
            and len(graph.get("job_types", [])) == 8
            and len(graph.get("job_states", [])) == 11
            and len(graph.get("terminal_states", [])) == 4
            and graph.get("allowed_transition_count") == 21
            and list(graph.get("failure_decisions", {})) == EXPECTED_FAILURE_CLASSES
        ),
        "failure_retry_dead_letter_log_actual_bounded": (
            log.get("state_history") == EXPECTED_STATE_HISTORY
            and log.get("attempt_count") == 3
            and log.get("retry_count") == 2
            and log.get("max_retries") == 2
            and log.get("final_state") == "DEAD_LETTERED"
            and log.get("persisted") is False
            and log.get("raw_payload_copied") is False
        ),
        "capacity_backpressure_proved": (
            backpressure.get("capacity", {}).get("result_code")
            == "QUEUE_CAPACITY_REACHED"
            and backpressure.get("capacity", {}).get("worker_started") is False
        ),
        "resource_pause_and_conflict_proved": (
            all(
                item.get("machine_state") == "PAUSED"
                and item.get("retry_count") == 0
                and item.get("retry_pending") is True
                for item in pauses.values()
            )
            and backpressure.get("same_source_conflict", {}).get(
                "resource_conflict_count"
            )
            == 3
            and backpressure.get("measured_backpressure_runtime_performed")
            is False
        ),
        "cleanup_allowlist_narrow_and_protected": (
            cleanup.get("eligible_artifact_classes") == ELIGIBLE_CLEANUP_CLASSES
            and cleanup.get("protected_artifact_classes") == PROTECTED_CLASSES
            and len(cleanup.get("phase3_protected_ref_checks", {})) == 5
            and all(cleanup.get("phase3_protected_ref_checks", {}).values())
            and cleanup.get("cleanup_runtime_performed") is False
            and cleanup.get("delete_attempt_performed") is False
        ),
        "automatic_and_manual_handling_truthful": (
            recovery.get("automatic_retry_eligible_safe_error_codes")
            == AUTOMATIC_RETRY_CODES
            and recovery.get("controlled_retry_admission_observed") is True
            and recovery.get("successful_automatic_recovery_cases_observed") == []
            and recovery.get("manual_action_required_cases") == MANUAL_ACTION_CASES
            and recovery.get("manual_rerun_candidate_only") is True
            and recovery.get("manual_rerun_job_created") is False
            and recovery.get("automatic_resume_performed") is False
            and recovery.get("process_crash_recovery_performed") is False
        ),
        "safe_shutdown_and_recovery_fail_closed": (
            shutdown.get("transport_orderly_shutdown_proved") is True
            and shutdown.get("transport_queue_closed") is True
            and shutdown.get("transport_resource_locks_released") is True
            and shutdown.get("transport_active_work_cancelled") is False
            and shutdown.get("retry_shutdown_steps") == RETRY_SHUTDOWN_STEPS
            and shutdown.get("recovery_steps") == RECOVERY_STEPS
            and shutdown.get("persistent_retry_state_available_after_exit") is False
            and shutdown.get("process_termination_performed") is False
            and shutdown.get("automatic_process_recovery_performed") is False
        ),
    }


def _blank_report(
    contract: Mapping[str, Any], checks: Mapping[str, bool]
) -> dict[str, Any]:
    delivery = contract.get("delivery_contract")
    policy_version = delivery.get("policy_version") if isinstance(delivery, dict) else None
    return {
        "schema_version": "ids.stage039.retry_dead_letter.phase4.report.v1",
        "stage": "STAGE-039",
        "phase": "Phase 4",
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "execution_mode": EXECUTION_MODE,
        "policy_version": policy_version,
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
        "failure_retry_dead_letter_log": {},
        "backpressure_trigger_proof": {},
        "cleanup_allowlist": {},
        "recovery_handling": {},
        "safe_shutdown_and_recovery": {},
        "rollback_steps": copy.deepcopy(ROLLBACK_STEPS),
        "known_limits": copy.deepcopy(KNOWN_LIMITS),
        "source_error_type": None,
        "production_runtime_activation_performed": False,
        "persistent_queue_write_performed": False,
        "database_connection_performed": False,
        "runtime_output_written": False,
        "ids_business_source_read_performed": False,
        "raw_metadata_content_accessed": False,
        "fake_ids_business_data_used": False,
        "real_ids_business_job_created": False,
        "measured_backpressure_runtime_performed": False,
        "production_lock_runtime_performed": False,
        "automatic_lifecycle_runtime_performed": False,
        "process_crash_recovery_performed": False,
        "cleanup_runtime_performed": False,
        "whole_stage_review_performed": False,
        "github_upload_allowed": False,
        "app_reinstall_allowed": False,
        "owner_feedback_zh": "交付合同未通过；保持停止并返回 Phase 4 修复。",
    }


def build_stage039_phase4_delivery_report(
    *,
    contract: Optional[dict[str, Any]] = None,
    execute_delivery_checks: bool = True,
) -> dict[str, Any]:
    try:
        contract = (
            copy.deepcopy(contract) if contract is not None else load_delivery_contract()
        )
    except (OSError, ValueError, json.JSONDecodeError):
        contract = {}
    checks = validate_delivery_contract(contract)
    report = _blank_report(contract, checks)
    if not report["contract_valid"] or not execute_delivery_checks:
        if report["contract_valid"]:
            report["stage_review_status"] = "blocked_delivery_checks_not_executed"
        return report

    try:
        phase2 = _phase2_module().build_stage039_phase2_report()
        phase3 = _phase3_module().build_stage039_phase3_report()
        stage038 = _stage038_delivery_module().build_stage038_phase4_delivery_report()
        if phase2.get("slice_valid") is not True:
            raise RuntimeError("invalid Stage039 Phase 2 prerequisite")
        if phase3.get("scenario_validation_valid") is not True:
            raise RuntimeError("invalid Stage039 Phase 3 prerequisite")
        if stage038.get("delivery_contract_valid") is not True:
            raise RuntimeError("invalid reviewed Stage038 delivery prerequisite")

        graph = _state_decision_graph()
        log = _failure_retry_dead_letter_log(phase2)
        backpressure = _backpressure_trigger_proof(stage038, phase3)
        cleanup = _cleanup_allowlist(contract, phase3)
        recovery = _recovery_handling(contract, phase2, phase3)
        shutdown = _safe_shutdown_and_recovery(contract, stage038)
        delivery_checks = _delivery_checks(
            graph, log, backpressure, cleanup, recovery, shutdown
        )
    except Exception as exc:
        report["source_error_type"] = type(exc).__name__
        report["stage_review_status"] = "blocked_upstream_or_delivery_failure"
        report["owner_feedback_zh"] = "上游或交付检查失败；保持停止并返回 Phase 4 修复。"
        return report

    valid = bool(delivery_checks) and all(delivery_checks.values())
    owner_contract = contract["owner_feedback_contract"]
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
            "failure_retry_dead_letter_log": log,
            "backpressure_trigger_proof": backpressure,
            "cleanup_allowlist": cleanup,
            "recovery_handling": recovery,
            "safe_shutdown_and_recovery": shutdown,
            "owner_feedback_zh": " ".join(
                [
                    owner_contract["status_zh"],
                    owner_contract["automatic_eligibility_zh"],
                    owner_contract["manual_action_zh"],
                    owner_contract["limit_zh"],
                ]
            ),
        }
    )
    return report


def main() -> int:
    report = build_stage039_phase4_delivery_report()
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0 if report["delivery_contract_valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
