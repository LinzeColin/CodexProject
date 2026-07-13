#!/usr/bin/env python3
"""Run the bounded STAGE-039 Phase 2 retry/dead-letter metadata slice."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import time
from typing import Any, Mapping, MutableMapping, Optional


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PROJECT_ROOT.parent
PURSUE_ROOT = PROJECT_ROOT / "docs" / "pursuing_goal" / "ids_v0_1"
CONTRACT_PATH = (
    PURSUE_ROOT
    / "retry_dead_letter"
    / "stage039_retry_dead_letter_runtime_contract.json"
)
STAGE037_CHECKER = PROJECT_ROOT / "scripts" / "check_job_state_model.py"
STAGE038_CHECKER = PROJECT_ROOT / "scripts" / "check_worker_queue_baseline.py"

TASK_ID = "IDS-V0_1-STAGE039-P2"
ACCEPTANCE_ID = "ACC-STAGE-039"
POLICY_VERSION = "ids.retry_policy.v0_1.stage039.p2"
EXECUTION_MODE = "ISOLATED_NON_PRODUCTION_RETRY_DEAD_LETTER_METADATA_SLICE"
CONTROL_INPUT_REF = (
    "repo:KM_IDSystem/docs/pursuing_goal/ids_v0_1/"
    "STAGE039_PHASE1_RETRY_DEAD_LETTER_SCOPE_BOUNDARY.md"
)
AUDIT_REF = (
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/"
    "STAGE039_PHASE2_RETRY_DEAD_LETTER_SLICE.md#Controlled-Evidence"
)
FAILURE_OBSERVATION_REF = f"{AUDIT_REF}-Failure-Observation"
RETRY_ELIGIBILITY_REF = f"{AUDIT_REF}-Retry-Eligibility"

EXPECTED_ROOT_KEYS = {
    "schema_version",
    "stage",
    "phase",
    "task_id",
    "acceptance_id",
    "execution_mode",
    "policy_contract_id",
    "contract_state",
    "next_gate",
    "source_binding",
    "identity_contract",
    "upstream_bindings",
    "policy",
    "classification",
    "retry_budget",
    "scheduler_contract",
    "dead_letter_contract",
    "runtime_boundary",
    "control_metadata_contract",
    "human_status_projection",
    "rollback",
    "truth_flags",
}
EXPECTED_UPSTREAM_BINDINGS = {
    "phase1_policy_contract": (
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/retry_dead_letter/"
        "stage039_retry_dead_letter_policy_contract.json",
        "d9b1a1dc2d05eaf02cdc2a6ead6d46d6f1c469186b68106639f5bc48347d53e8",
    ),
    "phase1_scope_boundary": (
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/"
        "STAGE039_PHASE1_RETRY_DEAD_LETTER_SCOPE_BOUNDARY.md",
        "4c647ad0bf200326f15d9aa5c339a41c14f9c0fb70bf1ff9b1e3ec699a8c44b4",
    ),
    "stage037_state_checker": (
        "KM_IDSystem/scripts/check_job_state_model.py",
        "7de8746b70ca1eaba78b672deebd9973113cedeacf3edbba09d2afb90407f404",
    ),
    "stage038_queue_checker": (
        "KM_IDSystem/scripts/check_worker_queue_baseline.py",
        "88a29aff19ee2465d6d5192c4fd9c352f85240689fede3a2216a754a1853e0f9",
    ),
    "stage038_queue_index": (
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/worker_queue_baseline/"
        "stage038_worker_queue_baseline_index.json",
        "68513591996a51fea90cd2ea863f42f910c0c3a45b70fd1611655bb6d95911ab",
    ),
}
EXPECTED_POLICY_KEYS = {
    "policy_version",
    "max_retries",
    "total_attempt_limit",
    "backoff_schedule_seconds",
    "jitter_policy",
    "jitter_formula",
    "retryable_safe_error_codes",
    "permanent_safe_error_codes",
    "resource_pause_reason_codes",
    "unknown_code_behavior",
    "parameter_source",
    "selection_rationale",
    "fact_level",
    "production_calibrated",
    "production_calibration_required",
    "rollback_policy_version",
}
EXPECTED_RETRYABLE_CODES = [
    "TRANSIENT_DEPENDENCY_UNAVAILABLE",
    "TRANSIENT_OPERATION_TIMEOUT",
]
EXPECTED_PERMANENT_CODES = [
    "INVALID_CONTROL_METADATA",
    "UNSUPPORTED_CONTROL_OPERATION",
]
EXPECTED_PAUSE_CODES = [
    "external_drive_offline",
    "disk_space_insufficient",
    "external_api_budget_insufficient",
]
EXPECTED_FALSE_TRUTH_FLAGS = {
    "ids_business_source_read_performed",
    "raw_metadata_content_accessed",
    "fake_ids_business_data_used",
    "real_ids_business_job_created",
    "database_connection_performed",
    "persistent_queue_write_performed",
    "runtime_output_written",
    "external_api_call_performed",
    "production_runtime_activation_performed",
    "github_upload_allowed",
    "app_reinstall_allowed",
}
OBSERVATION_KEYS = {
    "failure_observation_ref",
    "safe_error_code",
    "error_ref",
    "checkpoint_ref",
    "output_refs",
    "resource_gate_refs",
    "audit_ref",
    "transition_request_id",
    "policy_version",
    "observed_at_epoch_seconds",
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _stage037_module() -> Any:
    return _load_module(STAGE037_CHECKER, "stage039_phase2_stage037")


def _stage038_module() -> Any:
    return _load_module(STAGE038_CHECKER, "stage039_phase2_stage038")


def load_runtime_contract() -> dict[str, Any]:
    value = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("STAGE039 Phase 2 contract must be an object")
    return value


def _keys_exact(value: Any, expected: set[str]) -> bool:
    return isinstance(value, dict) and set(value) == expected


def _upstream_bindings_valid(value: Any) -> bool:
    if not isinstance(value, dict) or set(value) != set(EXPECTED_UPSTREAM_BINDINGS):
        return False
    for key, (expected_ref, expected_hash) in EXPECTED_UPSTREAM_BINDINGS.items():
        binding = value.get(key)
        if not _keys_exact(binding, {"ref", "sha256"}):
            return False
        if binding.get("ref") != expected_ref or binding.get("sha256") != expected_hash:
            return False
        path = REPO_ROOT / expected_ref
        if not path.is_file() or _sha256(path) != expected_hash:
            return False
    return True


def validate_runtime_contract(contract: Any) -> dict[str, bool]:
    if not isinstance(contract, dict):
        return {"contract_is_object": False}
    policy = contract.get("policy")
    classification = contract.get("classification")
    budget = contract.get("retry_budget")
    scheduler = contract.get("scheduler_contract")
    dead_letter = contract.get("dead_letter_contract")
    boundary = contract.get("runtime_boundary")
    control = contract.get("control_metadata_contract")
    projection = contract.get("human_status_projection")
    rollback = contract.get("rollback")
    truth = contract.get("truth_flags")
    source = contract.get("source_binding")
    identity = contract.get("identity_contract")

    return {
        "root_shape_exact": set(contract) == EXPECTED_ROOT_KEYS,
        "identity_exact": (
            contract.get("schema_version")
            == "ids.stage039.retry_dead_letter.phase2.v1"
            and contract.get("stage") == "STAGE-039"
            and contract.get("phase") == "Phase 2"
            and contract.get("task_id") == TASK_ID
            and contract.get("acceptance_id") == ACCEPTANCE_ID
            and contract.get("execution_mode") == EXECUTION_MODE
            and contract.get("policy_contract_id") == "ids.retry_dead_letter.v0_1.p2"
            and contract.get("contract_state")
            == "PHASE2_ISOLATED_SLICE_ENABLED_PRODUCTION_DISABLED"
            and contract.get("next_gate") == "IDS-STAGE039-P3-GATE"
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
                    "roadmap_sha256",
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
            and source.get("roadmap_sha256")
            == "a193fd2c44c51d634bf7887a1a6baf7e5199d9a8535e4211e35e97588e2e21a6"
            and source.get("instructions_sha256")
            == "ce456e06136d5ecc56cd7c9dc926abb5894817dda87bf7667588bf85211794f8"
            and source.get("source_verification_status") == "SOURCE_VERIFIED"
        ),
        "identity_immutable_across_policy_binding": (
            _keys_exact(
                identity,
                {
                    "stage038_admission_role",
                    "stage039_policy_job_id_derivation",
                    "stage038_and_stage039_job_ids_must_differ",
                    "stage038_queue_entry_ref_preserved",
                    "max_retries_bound_at_stage039_job_creation",
                    "max_retries_mutation_after_stage039_job_creation_allowed",
                },
            )
            and identity.get("stage038_admission_role")
            == "ISOLATED_TRANSPORT_PREREQUISITE_ONLY"
            and identity.get("stage039_policy_job_id_derivation")
            == "sha256(stage038_job_id|policy_version|acceptance_id)"
            and identity.get("stage038_and_stage039_job_ids_must_differ") is True
            and identity.get("stage038_queue_entry_ref_preserved") is True
            and identity.get("max_retries_bound_at_stage039_job_creation") is True
            and identity.get("max_retries_mutation_after_stage039_job_creation_allowed")
            is False
        ),
        "upstream_bindings_exact": _upstream_bindings_valid(
            contract.get("upstream_bindings")
        ),
        "policy_shape_exact": _keys_exact(policy, EXPECTED_POLICY_KEYS),
        "policy_values_bounded": (
            isinstance(policy, dict)
            and policy.get("policy_version") == POLICY_VERSION
            and policy.get("max_retries") == 2
            and policy.get("total_attempt_limit") == 3
            and policy.get("backoff_schedule_seconds") == [5, 30]
            and policy.get("jitter_policy")
            == "DETERMINISTIC_BOUNDED_HASH_JITTER_V1"
            and policy.get("jitter_formula")
            == (
                "lower=max(1,ceil(base_delay/2)); "
                "delay=lower+(sha256(policy_version|job_id|retry_ordinal) "
                "mod (base_delay-lower+1))"
            )
            and policy.get("retryable_safe_error_codes") == EXPECTED_RETRYABLE_CODES
            and policy.get("permanent_safe_error_codes") == EXPECTED_PERMANENT_CODES
            and policy.get("resource_pause_reason_codes") == EXPECTED_PAUSE_CODES
            and policy.get("unknown_code_behavior") == "NO_AUTOMATIC_RETRY"
            and policy.get("parameter_source")
            == "STAGE039_PHASE2_LOCAL_ENGINEERING_SAFETY_BOUNDARY"
            and bool(policy.get("selection_rationale"))
            and policy.get("fact_level") == "ASSUMPTION"
            and policy.get("production_calibrated") is False
            and policy.get("production_calibration_required") is True
            and policy.get("rollback_policy_version") == "NO_AUTOMATIC_RETRY"
        ),
        "classification_fail_closed": (
            _keys_exact(
                classification,
                {
                    "retryable_allowlist_match",
                    "permanent_allowlist_match",
                    "resource_pause_match",
                    "retry_budget_exhausted",
                    "unknown_or_missing_code",
                    "classification_source",
                    "message_substring_classification_allowed",
                    "default_allow",
                },
            )
            and classification.get("retryable_allowlist_match")
            == "TRANSIENT_RETRYABLE"
            and classification.get("permanent_allowlist_match")
            == "PERMANENT_NON_RETRYABLE"
            and classification.get("resource_pause_match")
            == "RESOURCE_CONDITION_PAUSE"
            and classification.get("retry_budget_exhausted") == "RETRY_EXHAUSTED"
            and classification.get("unknown_or_missing_code")
            == "INDETERMINATE_UNSAFE"
            and classification.get("classification_source")
            == "SAFE_ERROR_CODE_EXACT_MATCH_ONLY"
            and classification.get("message_substring_classification_allowed") is False
            and classification.get("default_allow") is False
        ),
        "retry_budget_atomic": (
            _keys_exact(
                budget,
                {
                    "definition",
                    "total_attempt_formula",
                    "reservation_increments_retry_count",
                    "due_admission_increments_retry_count",
                    "admission_compare_and_set_required",
                    "duplicate_request_increments_retry_count",
                    "resource_pause_increments_retry_count",
                    "exhausted_requeue_allowed",
                },
            )
            and budget.get("definition")
            == "max_retries counts attempts after the initial attempt"
            and budget.get("total_attempt_formula") == "1 + max_retries"
            and budget.get("reservation_increments_retry_count") is False
            and budget.get("due_admission_increments_retry_count") is True
            and budget.get("admission_compare_and_set_required") is True
            and budget.get("duplicate_request_increments_retry_count") is False
            and budget.get("resource_pause_increments_retry_count") is False
            and budget.get("exhausted_requeue_allowed") is False
        ),
        "scheduler_bounded": (
            _keys_exact(
                scheduler,
                {
                    "clock_input",
                    "sleep_or_wait_performed",
                    "next_eligible_encoding",
                    "early_admission_behavior",
                    "admission_transition",
                    "reservation_transition",
                    "resource_gates_required",
                    "idempotent_transition_request_required",
                },
            )
            and scheduler.get("clock_input") == "explicit observed_at_epoch_seconds"
            and scheduler.get("sleep_or_wait_performed") is False
            and scheduler.get("next_eligible_encoding")
            == "epoch:<nonnegative integer>"
            and scheduler.get("early_admission_behavior")
            == "RETRY_NOT_YET_ELIGIBLE"
            and scheduler.get("admission_transition") == "RETRY_WAIT->QUEUED"
            and scheduler.get("reservation_transition") == "RUNNING->RETRY_WAIT"
            and scheduler.get("resource_gates_required") is True
            and scheduler.get("idempotent_transition_request_required") is True
        ),
        "dead_letter_evidence_bounded": (
            _keys_exact(
                dead_letter,
                {
                    "transition_path",
                    "required_exhaustion_expression",
                    "raw_payload_copy_allowed",
                    "automatic_replay_allowed",
                    "manual_review_required",
                    "required_record_fields",
                },
            )
            and dead_letter.get("transition_path")
            == ["RUNNING", "RETRY_WAIT", "DEAD_LETTERED"]
            and dead_letter.get("required_exhaustion_expression")
            == "retry_count == max_retries"
            and dead_letter.get("raw_payload_copy_allowed") is False
            and dead_letter.get("automatic_replay_allowed") is False
            and dead_letter.get("manual_review_required") is True
            and dead_letter.get("required_record_fields")
            == [
                "job_id",
                "attempt_id",
                "retry_count",
                "max_retries",
                "input_refs",
                "output_refs",
                "safe_error_code",
                "error_ref",
                "checkpoint_ref",
                "audit_ref",
                "policy_version",
            ]
        ),
        "runtime_boundary_isolated": (
            _keys_exact(
                boundary,
                {
                    "stage038_queue_admission_allowed",
                    "stage037_candidate_transition_allowed",
                    "in_memory_only",
                    "production_activation_allowed",
                    "database_allowed",
                    "persistent_queue_write_allowed",
                    "runtime_output_write_allowed",
                    "external_api_allowed",
                    "raw_metadata_access_allowed",
                    "ids_business_job_allowed",
                    "fake_ids_business_data_allowed",
                    "measured_backpressure_owner",
                    "lock_lease_fencing_owner",
                    "automatic_resume_owner",
                    "worker_crash_recovery_owner",
                    "cleanup_execution_owner",
                },
            )
            and boundary.get("stage038_queue_admission_allowed") is True
            and boundary.get("stage037_candidate_transition_allowed") is True
            and boundary.get("in_memory_only") is True
            and all(
                boundary.get(key) is False
                for key in (
                    "production_activation_allowed",
                    "database_allowed",
                    "persistent_queue_write_allowed",
                    "runtime_output_write_allowed",
                    "external_api_allowed",
                    "raw_metadata_access_allowed",
                    "ids_business_job_allowed",
                    "fake_ids_business_data_allowed",
                )
            )
            and boundary.get("measured_backpressure_owner") == "STAGE-040"
            and boundary.get("lock_lease_fencing_owner") == "STAGE-041"
            and boundary.get("automatic_resume_owner") == "STAGE-042"
            and boundary.get("worker_crash_recovery_owner") == "STAGE-043"
            and boundary.get("cleanup_execution_owner") == "STAGE-044"
        ),
        "control_metadata_bounded": (
            _keys_exact(
                control,
                {
                    "input_ref",
                    "input_ref_must_be_git_tracked",
                    "raw_body_in_control_record_allowed",
                    "output_refs_on_controlled_failure",
                    "checkpoint_ref_format",
                    "error_ref_format",
                    "audit_ref",
                },
            )
            and control.get("input_ref") == CONTROL_INPUT_REF
            and control.get("input_ref_must_be_git_tracked") is True
            and control.get("raw_body_in_control_record_allowed") is False
            and control.get("output_refs_on_controlled_failure") == []
            and control.get("checkpoint_ref_format")
            == "checkpoint:sha256:<tracked-control-input-digest>"
            and control.get("error_ref_format") == "error:<safe_error_code>"
            and control.get("audit_ref") == AUDIT_REF
        ),
        "human_projection_exact": (
            isinstance(projection, dict)
            and set(projection) == {"RETRY_WAIT", "PAUSED", "FAILED", "DEAD_LETTERED"}
            and projection.get("RETRY_WAIT", {}).get("label_zh") == "等待重试"
            and projection.get("PAUSED", {}).get("label_zh") == "已暂停"
            and projection.get("FAILED", {}).get("label_zh") == "处理失败"
            and projection.get("DEAD_LETTERED", {}).get("label_zh")
            == "需要人工处理"
            and all(
                _keys_exact(
                    projection.get(state),
                    {"label_zh", "owner_action_zh", "owner_attention_required"},
                )
                for state in projection
            )
        ),
        "rollback_fail_closed": (
            _keys_exact(
                rollback,
                {
                    "trigger",
                    "action",
                    "preserve_phase1",
                    "preserve_stage037_stage038",
                    "preserve_source_and_evidence",
                    "github_action_allowed",
                },
            )
            and rollback.get("trigger")
            == "INVALID_CONTRACT_OR_POLICY_OR_UPSTREAM_BINDING"
            and rollback.get("action")
            == "DISABLE_AUTOMATIC_RETRY_AND_REVERT_PHASE2_FILES_ONLY"
            and rollback.get("preserve_phase1") is True
            and rollback.get("preserve_stage037_stage038") is True
            and rollback.get("preserve_source_and_evidence") is True
            and rollback.get("github_action_allowed") is False
        ),
        "truth_flags_exact": (
            isinstance(truth, dict)
            and set(truth)
            == EXPECTED_FALSE_TRUTH_FLAGS | {"taskpack_source_read_performed"}
            and truth.get("taskpack_source_read_performed") is True
            and all(truth.get(key) is False for key in EXPECTED_FALSE_TRUTH_FLAGS)
        ),
    }


def deterministic_delay_seconds(
    job_id: str, retry_ordinal: int, policy: Mapping[str, Any]
) -> int:
    if (
        not isinstance(job_id, str)
        or not job_id
        or isinstance(retry_ordinal, bool)
        or not isinstance(retry_ordinal, int)
        or retry_ordinal < 1
        or policy.get("policy_version") != POLICY_VERSION
        or policy.get("jitter_policy") != "DETERMINISTIC_BOUNDED_HASH_JITTER_V1"
    ):
        raise ValueError("invalid deterministic retry delay input")
    schedule = policy.get("backoff_schedule_seconds")
    if not isinstance(schedule, list) or retry_ordinal > len(schedule):
        raise ValueError("retry ordinal is outside the bounded schedule")
    ceiling = schedule[retry_ordinal - 1]
    if isinstance(ceiling, bool) or not isinstance(ceiling, int) or ceiling < 1:
        raise ValueError("invalid backoff ceiling")
    lower = max(1, (ceiling + 1) // 2)
    seed = f"{POLICY_VERSION}|{job_id}|{retry_ordinal}".encode("utf-8")
    value = int.from_bytes(hashlib.sha256(seed).digest()[:8], "big")
    return lower + value % (ceiling - lower + 1)


def _transition_request(
    snapshot: Mapping[str, Any],
    target_state: str,
    transition_request_id: str,
    *,
    guard_facts: Mapping[str, bool],
    reason_code: str,
    audit_ref: str = AUDIT_REF,
    output_refs: Optional[list[str]] = None,
    checkpoint_ref: Optional[str] = None,
    error_ref: Optional[str] = None,
    resource_gate_refs: Optional[list[str]] = None,
    pause_reason_code: Optional[str] = None,
    next_eligible_at: Optional[str] = None,
    next_eligible_evidence_ref: Optional[str] = None,
    candidate_claim: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    active = snapshot.get("job_state") in {"CLAIMED", "RUNNING", "PAUSE_REQUESTED"}
    return {
        "job_id": snapshot.get("job_id"),
        "transition_request_id": transition_request_id,
        "expected_state": snapshot.get("job_state"),
        "expected_state_version": snapshot.get("state_version"),
        "target_state": target_state,
        "actor_ref": f"task:{TASK_ID}",
        "reason_code": reason_code,
        "audit_ref": audit_ref,
        "guard_facts": dict(guard_facts),
        "input_refs": [],
        "output_refs": copy.deepcopy(output_refs or []),
        "checkpoint_ref": checkpoint_ref,
        "quarantine_ref": None,
        "error_ref": error_ref,
        "resource_gate_refs": copy.deepcopy(resource_gate_refs or []),
        "pause_reason_code": pause_reason_code,
        "stop_reason": None,
        "next_eligible_at": next_eligible_at,
        "next_eligible_evidence_ref": next_eligible_evidence_ref,
        "fencing_token": snapshot.get("fencing_token") if active else None,
        "candidate_claim": copy.deepcopy(candidate_claim),
    }


def _initial_snapshot(envelope: Mapping[str, Any], contract: Mapping[str, Any]) -> dict[str, Any]:
    stage037 = _stage037_module()
    identity_seed = hashlib.sha256(
        (
            f"{envelope['job_id']}|{contract['policy']['policy_version']}|"
            f"{ACCEPTANCE_ID}"
        ).encode("utf-8")
    ).hexdigest()
    return {
        "evaluation_mode": stage037.EVALUATION_MODE,
        "job_id": f"control:stage039:{identity_seed[:24]}",
        "job_type": envelope["job_type"],
        "job_state": "QUEUED",
        "state_version": 0,
        "retry_count": 0,
        "max_retries": contract["policy"]["max_retries"],
        "retry_pending": False,
        "retry_disposition": "none",
        "next_eligible_at": None,
        "lease_active": False,
        "lock_active": False,
        "fencing_token": 0,
        "attempt_id": None,
        "lease_owner_ref": None,
        "lease_expires_at": None,
        "lock_key": None,
        "pause_reason_code": None,
        "stop_reason": None,
        "input_refs": copy.deepcopy(envelope["input_refs"]),
        "output_refs": [],
        "checkpoint_ref": None,
        "quarantine_ref": None,
        "error_ref": None,
    }


def _advance_queued_to_running(
    snapshot: Mapping[str, Any],
    *,
    attempt_ordinal: int,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    stage037 = _stage037_module()
    state_contract = stage037.load_contract()
    candidate_claim = {
        "attempt_id": (
            f"acceptance:{ACCEPTANCE_ID}:{snapshot['job_id']}:attempt-{attempt_ordinal}"
        ),
        "lease_owner_ref": f"task:{TASK_ID}:isolated-worker",
        "lease_expires_at": "contract:isolated-process-lifetime",
        "fencing_token": snapshot["fencing_token"] + 1,
        "lock_key": f"resource:stage039:{snapshot['job_id']}",
    }
    claim_request = _transition_request(
        snapshot,
        "CLAIMED",
        f"acceptance:{ACCEPTANCE_ID}:{snapshot['job_id']}:claim-{attempt_ordinal}",
        guard_facts={
            "admission_gates_passed": True,
            "claim_lease_and_lock_acquired": True,
        },
        reason_code="STAGE039_PHASE2_CONTROL_CLAIM",
        candidate_claim=candidate_claim,
    )
    claim = stage037.evaluate_transition(
        dict(snapshot), claim_request, contract=state_contract
    )
    if claim.get("accepted") is not True:
        raise RuntimeError(f"control claim rejected: {claim.get('result_code')}")
    claimed = claim["next_snapshot"]
    running_request = _transition_request(
        claimed,
        "RUNNING",
        f"acceptance:{ACCEPTANCE_ID}:{snapshot['job_id']}:run-{attempt_ordinal}",
        guard_facts={"live_lease_valid": True, "fencing_token_matches": True},
        reason_code="STAGE039_PHASE2_CONTROL_RUNNING",
    )
    running = stage037.evaluate_transition(
        claimed, running_request, contract=state_contract
    )
    if running.get("accepted") is not True:
        raise RuntimeError(f"control run rejected: {running.get('result_code')}")
    return copy.deepcopy(running["next_snapshot"]), [claim, running]


def build_running_control_context(
    contract: Optional[dict[str, Any]] = None,
    *,
    retry_count: int = 0,
) -> dict[str, Any]:
    contract = copy.deepcopy(contract) if contract is not None else load_runtime_contract()
    checks = validate_runtime_contract(contract)
    if not checks or not all(checks.values()):
        raise ValueError("invalid STAGE039 Phase 2 contract")
    if (
        isinstance(retry_count, bool)
        or not isinstance(retry_count, int)
        or retry_count < 0
        or retry_count > contract["policy"]["max_retries"]
    ):
        raise ValueError("invalid retry_count")

    stage038 = _stage038_module()
    envelope = stage038.build_control_envelope(CONTROL_INPUT_REF)
    queue = stage038.IsolatedWorkerQueue(capacity=1)
    admission = queue.submit(envelope)
    if admission.get("accepted") is not True:
        raise RuntimeError(f"STAGE038 admission rejected: {admission.get('result_code')}")
    snapshot = _initial_snapshot(envelope, contract)
    stage038_record = queue.get_record(admission["queue_entry_ref"])
    if stage038_record["job_id"] == snapshot["job_id"]:
        raise RuntimeError("STAGE039 policy job must not mutate STAGE038 job identity")
    snapshot["retry_count"] = retry_count
    running, transitions = _advance_queued_to_running(
        snapshot, attempt_ordinal=retry_count + 1
    )
    stage037 = _stage037_module()
    return {
        "admission": admission,
        "snapshot": running,
        "state_history": ["QUEUED", "CLAIMED", "RUNNING"],
        "owner_status": copy.deepcopy(
            stage037.load_contract()["human_status_projection"]["RUNNING"]
        ),
        "transition_decisions": transitions,
        "stage038_queue_size": queue.queue_size,
        "stage038_record_count": queue.record_count,
        "stage038_record": stage038_record,
        "stage038_queue_entry_ref": admission["queue_entry_ref"],
        "identity_bridge": {
            "stage038_job_id": stage038_record["job_id"],
            "stage039_policy_job_id": running["job_id"],
            "same_logical_job": False,
            "max_retries_bound_at_stage039_job_creation": True,
        },
        "in_memory_only": True,
    }


def _path_from_repo_ref(value: str) -> Path:
    if not value.startswith("repo:KM_IDSystem/"):
        raise ValueError("control input must be a KM_IDSystem repo ref")
    path = REPO_ROOT / value.removeprefix("repo:")
    if not path.is_file():
        raise ValueError("control input ref is missing")
    return path


def build_failure_observation(
    snapshot: Mapping[str, Any],
    *,
    safe_error_code: str,
    observed_at_epoch_seconds: int,
) -> dict[str, Any]:
    if (
        not isinstance(safe_error_code, str)
        or re.fullmatch(r"[A-Z][A-Z0-9_]{2,63}", safe_error_code) is None
        or isinstance(observed_at_epoch_seconds, bool)
        or not isinstance(observed_at_epoch_seconds, int)
        or observed_at_epoch_seconds < 0
    ):
        raise ValueError("invalid bounded failure observation")
    input_refs = snapshot.get("input_refs")
    if not isinstance(input_refs, list) or input_refs != [CONTROL_INPUT_REF]:
        raise ValueError("snapshot does not reference the approved control input")
    checkpoint_digest = _sha256(_path_from_repo_ref(input_refs[0]))
    return {
        "failure_observation_ref": FAILURE_OBSERVATION_REF,
        "safe_error_code": safe_error_code,
        "error_ref": f"error:{safe_error_code}",
        "checkpoint_ref": f"checkpoint:sha256:{checkpoint_digest}",
        "output_refs": [],
        "resource_gate_refs": ["contract:stage039:control-resource-gates-pass"],
        "audit_ref": AUDIT_REF,
        "transition_request_id": (
            f"acceptance:{ACCEPTANCE_ID}:{snapshot.get('job_id')}:"
            f"failure-{snapshot.get('state_version')}-{safe_error_code}"
        ),
        "policy_version": POLICY_VERSION,
        "observed_at_epoch_seconds": observed_at_epoch_seconds,
    }


def _observation_valid(
    observation: Any, snapshot: Mapping[str, Any], contract: Mapping[str, Any]
) -> bool:
    if not isinstance(observation, dict) or set(observation) != OBSERVATION_KEYS:
        return False
    safe_code = observation.get("safe_error_code")
    return (
        isinstance(safe_code, str)
        and re.fullmatch(r"[A-Z][A-Z0-9_]{2,63}", safe_code) is not None
        and observation.get("error_ref") == f"error:{safe_code}"
        and isinstance(observation.get("checkpoint_ref"), str)
        and re.fullmatch(
            r"checkpoint:sha256:[0-9a-f]{64}", observation["checkpoint_ref"]
        )
        is not None
        and observation.get("output_refs") == []
        and observation.get("resource_gate_refs")
        == ["contract:stage039:control-resource-gates-pass"]
        and observation.get("audit_ref") == AUDIT_REF
        and observation.get("failure_observation_ref") == FAILURE_OBSERVATION_REF
        and isinstance(observation.get("transition_request_id"), str)
        and observation.get("policy_version")
        == contract.get("policy", {}).get("policy_version")
        and isinstance(observation.get("observed_at_epoch_seconds"), int)
        and not isinstance(observation.get("observed_at_epoch_seconds"), bool)
        and observation["observed_at_epoch_seconds"] >= 0
        and snapshot.get("max_retries") == contract.get("policy", {}).get("max_retries")
    )


def _owner_status(contract: Mapping[str, Any], state: str) -> dict[str, Any]:
    projection = contract.get("human_status_projection", {}).get(state, {})
    return copy.deepcopy(projection) if isinstance(projection, dict) else {}


def _blocked_failure_result(
    snapshot: Mapping[str, Any], result_code: str, contract: Mapping[str, Any]
) -> dict[str, Any]:
    return {
        "accepted": False,
        "result_code": result_code,
        "decision_action": "REQUIRE_MANUAL_REVIEW",
        "failure_class": "POLICY_OR_AUTHORIZATION_BLOCK",
        "next_snapshot": copy.deepcopy(dict(snapshot)),
        "owner_status": _owner_status(contract, str(snapshot.get("job_state"))),
        "state_history": [snapshot.get("job_state")],
        "transition_decisions": [],
        "idempotent_replay": False,
        "database_write_performed": False,
        "persistent_queue_write_performed": False,
    }


def evaluate_failure(
    snapshot: Mapping[str, Any],
    observation: Mapping[str, Any],
    *,
    contract: Optional[dict[str, Any]] = None,
    prior_results: Optional[MutableMapping[str, Mapping[str, Any]]] = None,
) -> dict[str, Any]:
    contract = copy.deepcopy(contract) if contract is not None else load_runtime_contract()
    checks = validate_runtime_contract(contract)
    if not checks or not all(checks.values()):
        return _blocked_failure_result(snapshot, "INVALID_RETRY_POLICY", contract)
    stage037 = _stage037_module()
    if snapshot.get("job_state") in set(stage037.TERMINAL_STATES):
        return _blocked_failure_result(snapshot, "TERMINAL_STATE_IMMUTABLE", contract)
    if snapshot.get("job_state") != "RUNNING" or not _observation_valid(
        observation, snapshot, contract
    ):
        return _blocked_failure_result(snapshot, "INVALID_FAILURE_OBSERVATION", contract)

    state_contract = stage037.load_contract()
    policy = contract["policy"]
    safe_code = observation["safe_error_code"]
    transition_decisions: list[dict[str, Any]] = []

    if safe_code in policy["retryable_safe_error_codes"]:
        retry_eligible = snapshot["retry_count"] < snapshot["max_retries"]
        next_eligible_at = None
        if retry_eligible:
            retry_ordinal = snapshot["retry_count"] + 1
            delay = deterministic_delay_seconds(
                snapshot["job_id"], retry_ordinal, policy
            )
            next_eligible_at = (
                f"epoch:{observation['observed_at_epoch_seconds'] + delay}"
            )
        request = _transition_request(
            snapshot,
            "RETRY_WAIT",
            observation["transition_request_id"],
            guard_facts={
                "lease_valid_or_expiry_evidence": True,
                "fencing_token_matches": True,
                "retryable_failure_recorded": True,
                "error_evidence_present": True,
            },
            reason_code=f"STAGE039_PHASE2_{safe_code}",
            checkpoint_ref=observation["checkpoint_ref"],
            error_ref=observation["error_ref"],
            next_eligible_at=next_eligible_at,
            next_eligible_evidence_ref=(
                RETRY_ELIGIBILITY_REF if retry_eligible else None
            ),
        )
        reserved = stage037.evaluate_transition(
            dict(snapshot),
            request,
            contract=state_contract,
            prior_results=prior_results,
        )
        transition_decisions.append(reserved)
        if reserved.get("accepted") is not True:
            return _blocked_failure_result(
                snapshot, str(reserved.get("result_code")), contract
            )
        if (
            prior_results is not None
            and observation["transition_request_id"] not in prior_results
        ):
            prior_results[observation["transition_request_id"]] = copy.deepcopy(
                reserved
            )
        waiting = reserved["next_snapshot"]
        if retry_eligible:
            return {
                "accepted": True,
                "result_code": "RETRY_RESERVED",
                "decision_action": "SCHEDULE_RETRY",
                "failure_class": "TRANSIENT_RETRYABLE",
                "next_snapshot": copy.deepcopy(waiting),
                "owner_status": _owner_status(contract, "RETRY_WAIT"),
                "state_history": ["RUNNING", "RETRY_WAIT"],
                "transition_decisions": transition_decisions,
                "safe_error_code": safe_code,
                "failure_observation_ref": observation["failure_observation_ref"],
                "policy_version": policy["policy_version"],
                "retry_budget_consumed": False,
                "idempotent_replay": bool(reserved.get("idempotent_replay")),
                "database_write_performed": False,
                "persistent_queue_write_performed": False,
            }

        dead_request = _transition_request(
            waiting,
            "DEAD_LETTERED",
            f"{observation['transition_request_id']}:dead-letter",
            guard_facts={
                "retry_exhaustion_confirmed": True,
                "no_active_claim_or_lock": True,
            },
            reason_code="STAGE039_PHASE2_RETRY_EXHAUSTED",
            checkpoint_ref=observation["checkpoint_ref"],
            error_ref=observation["error_ref"],
        )
        dead = stage037.evaluate_transition(
            waiting,
            dead_request,
            contract=state_contract,
            prior_results=prior_results,
        )
        transition_decisions.append(dead)
        if dead.get("accepted") is not True:
            return _blocked_failure_result(
                waiting, str(dead.get("result_code")), contract
            )
        dead_request_id = dead_request["transition_request_id"]
        if prior_results is not None and dead_request_id not in prior_results:
            prior_results[dead_request_id] = copy.deepcopy(dead)
        return {
            "accepted": True,
            "result_code": "RETRY_EXHAUSTED_DEAD_LETTERED",
            "decision_action": "DEAD_LETTER",
            "failure_class": "RETRY_EXHAUSTED",
            "next_snapshot": copy.deepcopy(dead["next_snapshot"]),
            "owner_status": _owner_status(contract, "DEAD_LETTERED"),
            "state_history": ["RUNNING", "RETRY_WAIT", "DEAD_LETTERED"],
            "transition_decisions": transition_decisions,
            "safe_error_code": safe_code,
            "failure_observation_ref": observation["failure_observation_ref"],
            "policy_version": policy["policy_version"],
            "retry_budget_consumed": False,
            "idempotent_replay": bool(
                reserved.get("idempotent_replay")
                and dead.get("idempotent_replay")
            ),
            "database_write_performed": False,
            "persistent_queue_write_performed": False,
        }

    permanent = safe_code in policy["permanent_safe_error_codes"]
    failure_class = "PERMANENT_NON_RETRYABLE" if permanent else "INDETERMINATE_UNSAFE"
    decision_action = "FAIL_TERMINAL" if permanent else "REQUIRE_MANUAL_REVIEW"
    fail_request = _transition_request(
        snapshot,
        "FAILED",
        observation["transition_request_id"],
        guard_facts={
            "live_lease_valid": True,
            "fencing_token_matches": True,
            "permanent_failure_recorded": True,
            "error_evidence_present": True,
        },
        reason_code=f"STAGE039_PHASE2_{failure_class}",
        checkpoint_ref=observation["checkpoint_ref"],
        error_ref=observation["error_ref"],
    )
    failed = stage037.evaluate_transition(
        dict(snapshot), fail_request, contract=state_contract, prior_results=prior_results
    )
    if failed.get("accepted") is not True:
        return _blocked_failure_result(snapshot, str(failed.get("result_code")), contract)
    if (
        prior_results is not None
        and observation["transition_request_id"] not in prior_results
    ):
        prior_results[observation["transition_request_id"]] = copy.deepcopy(failed)
    return {
        "accepted": True,
        "result_code": "FAILED_NO_AUTOMATIC_RETRY",
        "decision_action": decision_action,
        "failure_class": failure_class,
        "next_snapshot": copy.deepcopy(failed["next_snapshot"]),
        "owner_status": _owner_status(contract, "FAILED"),
        "state_history": ["RUNNING", "FAILED"],
        "transition_decisions": [failed],
        "safe_error_code": safe_code,
        "failure_observation_ref": observation["failure_observation_ref"],
        "policy_version": policy["policy_version"],
        "retry_budget_consumed": False,
        "idempotent_replay": bool(failed.get("idempotent_replay")),
        "database_write_performed": False,
        "persistent_queue_write_performed": False,
    }


def admit_due_retry(
    snapshot: Mapping[str, Any],
    *,
    observed_at_epoch_seconds: int,
    transition_request_id: str,
    contract: Optional[dict[str, Any]] = None,
    prior_results: Optional[MutableMapping[str, Mapping[str, Any]]] = None,
) -> dict[str, Any]:
    contract = copy.deepcopy(contract) if contract is not None else load_runtime_contract()
    checks = validate_runtime_contract(contract)
    if not checks or not all(checks.values()):
        return _blocked_failure_result(snapshot, "INVALID_RETRY_POLICY", contract)
    if (
        snapshot.get("job_state") != "RETRY_WAIT"
        or snapshot.get("retry_pending") is not True
        or snapshot.get("retry_disposition") != "eligible"
        or not isinstance(snapshot.get("next_eligible_at"), str)
        or re.fullmatch(r"epoch:[0-9]+", snapshot["next_eligible_at"]) is None
        or isinstance(observed_at_epoch_seconds, bool)
        or not isinstance(observed_at_epoch_seconds, int)
        or observed_at_epoch_seconds < 0
        or not isinstance(transition_request_id, str)
        or not transition_request_id
    ):
        return _blocked_failure_result(snapshot, "INVALID_RETRY_ADMISSION", contract)
    due_at = int(snapshot["next_eligible_at"].split(":", 1)[1])
    if observed_at_epoch_seconds < due_at:
        result = _blocked_failure_result(snapshot, "RETRY_NOT_YET_ELIGIBLE", contract)
        result["decision_action"] = "WAIT_UNTIL_ELIGIBLE"
        result["failure_class"] = "TRANSIENT_RETRYABLE"
        result["owner_status"] = _owner_status(contract, "RETRY_WAIT")
        return result

    request = _transition_request(
        snapshot,
        "QUEUED",
        transition_request_id,
        guard_facts={
            "next_eligible_reached": True,
            "resource_gates_passed": True,
            "no_active_claim_or_lock": True,
        },
        reason_code="STAGE039_PHASE2_DUE_RETRY_ADMISSION",
        next_eligible_evidence_ref=RETRY_ELIGIBILITY_REF,
    )
    stage037 = _stage037_module()
    decision = stage037.evaluate_transition(
        dict(snapshot),
        request,
        contract=stage037.load_contract(),
        prior_results=prior_results,
    )
    if decision.get("accepted") is not True:
        return _blocked_failure_result(snapshot, str(decision.get("result_code")), contract)
    if prior_results is not None and transition_request_id not in prior_results:
        prior_results[transition_request_id] = copy.deepcopy(decision)
    result = copy.deepcopy(decision)
    result.update(
        {
            "decision_action": "ADMIT_RETRY",
            "failure_class": "TRANSIENT_RETRYABLE",
            "owner_status": copy.deepcopy(
                stage037.load_contract()["human_status_projection"]["QUEUED"]
            ),
            "state_history": ["RETRY_WAIT", "QUEUED"],
            "retry_budget_consumed": True,
            "database_write_performed": False,
            "persistent_queue_write_performed": False,
        }
    )
    return result


def pause_pending_retry(
    snapshot: Mapping[str, Any],
    *,
    pause_reason_code: str,
    transition_request_id: str,
    contract: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    contract = copy.deepcopy(contract) if contract is not None else load_runtime_contract()
    checks = validate_runtime_contract(contract)
    if not checks or not all(checks.values()):
        return _blocked_failure_result(snapshot, "INVALID_RETRY_POLICY", contract)
    if (
        snapshot.get("job_state") != "RETRY_WAIT"
        or pause_reason_code not in contract["policy"]["resource_pause_reason_codes"]
    ):
        return _blocked_failure_result(snapshot, "INVALID_RESOURCE_PAUSE", contract)
    request = _transition_request(
        snapshot,
        "PAUSED",
        transition_request_id,
        guard_facts={"resource_gate_blocked": True, "no_active_claim_or_lock": True},
        reason_code="STAGE039_PHASE2_RESOURCE_PAUSE",
        resource_gate_refs=[f"contract:stage039:{pause_reason_code}"],
        pause_reason_code=pause_reason_code,
    )
    stage037 = _stage037_module()
    decision = stage037.evaluate_transition(
        dict(snapshot), request, contract=stage037.load_contract()
    )
    if decision.get("accepted") is not True:
        return _blocked_failure_result(snapshot, str(decision.get("result_code")), contract)
    result = copy.deepcopy(decision)
    result.update(
        {
            "decision_action": "PAUSE_RESOURCE_GATE",
            "failure_class": "RESOURCE_CONDITION_PAUSE",
            "owner_status": _owner_status(contract, "PAUSED"),
            "state_history": ["RETRY_WAIT", "PAUSED"],
            "retry_budget_consumed": False,
            "database_write_performed": False,
            "persistent_queue_write_performed": False,
        }
    )
    return result


def _blank_report(contract: Mapping[str, Any], checks: Mapping[str, bool]) -> dict[str, Any]:
    return {
        "schema_version": "ids.stage039.retry_dead_letter.phase2.report.v1",
        "stage": "STAGE-039",
        "phase": "Phase 2",
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "execution_mode": EXECUTION_MODE,
        "policy_version": contract.get("policy", {}).get("policy_version"),
        "contract_checks": dict(checks),
        "contract_valid": bool(checks) and all(checks.values()),
        "slice_executed": False,
        "slice_valid": False,
        "stage038_isolated_admission_performed": False,
        "retry_reservation_performed": False,
        "retry_admission_performed": False,
        "dead_letter_metadata_transition_performed": False,
        "production_runtime_activation_performed": False,
        "database_connection_performed": False,
        "persistent_queue_write_performed": False,
        "runtime_output_written": False,
        "ids_business_source_read_performed": False,
        "raw_metadata_content_accessed": False,
        "fake_ids_business_data_used": False,
        "real_ids_business_job_created": False,
        "external_api_call_performed": False,
        "github_upload_allowed": False,
        "app_reinstall_allowed": False,
        "final_record": None,
        "state_history": [],
        "next_gate": "IDS-STAGE039-P3-GATE",
    }


def build_stage039_phase2_report(
    *,
    contract: Optional[dict[str, Any]] = None,
    execute_slice: bool = True,
) -> dict[str, Any]:
    try:
        contract = copy.deepcopy(contract) if contract is not None else load_runtime_contract()
    except (OSError, ValueError, json.JSONDecodeError):
        contract = {}
    checks = validate_runtime_contract(contract)
    report = _blank_report(contract, checks)
    if not report["contract_valid"] or not execute_slice:
        return report

    context = build_running_control_context(contract)
    snapshot = context["snapshot"]
    history = list(context["state_history"])
    observed_at = int(time.time())
    prior_results: dict[str, Mapping[str, Any]] = {}

    for retry_ordinal in (1, 2):
        observation = build_failure_observation(
            snapshot,
            safe_error_code=EXPECTED_RETRYABLE_CODES[(retry_ordinal - 1) % 2],
            observed_at_epoch_seconds=observed_at,
        )
        reserved = evaluate_failure(snapshot, observation, contract=contract)
        if reserved.get("accepted") is not True:
            return report
        history.extend(reserved["state_history"][1:])
        waiting = reserved["next_snapshot"]
        due_at = int(waiting["next_eligible_at"].split(":", 1)[1])
        admission_id = (
            f"acceptance:{ACCEPTANCE_ID}:{snapshot['job_id']}:"
            f"retry-admission-{retry_ordinal}"
        )
        admitted = admit_due_retry(
            waiting,
            observed_at_epoch_seconds=due_at,
            transition_request_id=admission_id,
            contract=contract,
            prior_results=prior_results,
        )
        if admitted.get("accepted") is not True:
            return report
        replay = admit_due_retry(
            waiting,
            observed_at_epoch_seconds=due_at,
            transition_request_id=admission_id,
            contract=contract,
            prior_results=prior_results,
        )
        if replay.get("idempotent_replay") is not True:
            return report
        history.append("QUEUED")
        snapshot, transitions = _advance_queued_to_running(
            admitted["next_snapshot"], attempt_ordinal=retry_ordinal + 1
        )
        if len(transitions) != 2:
            return report
        history.extend(["CLAIMED", "RUNNING"])
        observed_at = due_at

    final_observation = build_failure_observation(
        snapshot,
        safe_error_code="TRANSIENT_OPERATION_TIMEOUT",
        observed_at_epoch_seconds=observed_at,
    )
    exhausted = evaluate_failure(snapshot, final_observation, contract=contract)
    if exhausted.get("accepted") is not True:
        return report
    history.extend(exhausted["state_history"][1:])
    final_snapshot = exhausted["next_snapshot"]
    final_record = {
        "job_id": final_snapshot["job_id"],
        "stage038_queue_entry_ref": context["stage038_queue_entry_ref"],
        "stage038_admission_job_id": context["stage038_record"]["job_id"],
        "machine_state": final_snapshot["job_state"],
        "owner_status": exhausted["owner_status"],
        "attempt_id": final_snapshot["attempt_id"],
        "retry_count": final_snapshot["retry_count"],
        "max_retries": final_snapshot["max_retries"],
        "retry_pending": final_snapshot["retry_pending"],
        "retry_disposition": final_snapshot["retry_disposition"],
        "input_refs": copy.deepcopy(final_snapshot["input_refs"]),
        "output_refs": copy.deepcopy(final_snapshot["output_refs"]),
        "safe_error_code": final_observation["safe_error_code"],
        "error_ref": final_snapshot["error_ref"],
        "checkpoint_ref": final_snapshot["checkpoint_ref"],
        "audit_ref": AUDIT_REF,
        "policy_version": POLICY_VERSION,
        "in_memory_only": True,
        "persisted": False,
    }
    slice_valid = (
        final_record["machine_state"] == "DEAD_LETTERED"
        and final_record["retry_count"] == 2
        and final_record["max_retries"] == 2
        and final_record["input_refs"] == [CONTROL_INPUT_REF]
        and final_record["output_refs"] == []
        and re.fullmatch(r"error:[A-Z0-9_]+", final_record["error_ref"] or "")
        is not None
        and re.fullmatch(
            r"checkpoint:sha256:[0-9a-f]{64}",
            final_record["checkpoint_ref"] or "",
        )
        is not None
        and history.count("QUEUED") == 3
        and history[-2:] == ["RETRY_WAIT", "DEAD_LETTERED"]
    )
    report.update(
        {
            "slice_executed": True,
            "slice_valid": slice_valid,
            "stage038_isolated_admission_performed": True,
            "retry_reservation_performed": True,
            "retry_admission_performed": True,
            "dead_letter_metadata_transition_performed": True,
            "final_record": final_record,
            "state_history": history,
        }
    )
    return report


def main() -> int:
    report = build_stage039_phase2_report()
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0 if report["slice_valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
