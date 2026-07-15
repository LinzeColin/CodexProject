#!/usr/bin/env python3
"""Validate the STAGE-039 Phase 1 retry/dead-letter engineering contract."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


CONTRACT_RELATIVE = (
    "docs/pursuing_goal/ids_v0_1/retry_dead_letter/"
    "stage039_retry_dead_letter_policy_contract.json"
)

EXPECTED_ROOT_KEYS = {
    "schema_version",
    "stage",
    "phase",
    "task_id",
    "acceptance_id",
    "local_code",
    "domain",
    "entrance",
    "pursuing_goal",
    "retry_policy_contract_id",
    "contract_state",
    "execution_ready",
    "next_gate",
    "source_binding",
    "upstream_bindings",
    "state_model_inheritance",
    "input_contract",
    "identity_contract",
    "retry_budget_contract",
    "policy_parameter_contract",
    "failure_classification",
    "retry_eligibility_contract",
    "resource_pause_contract",
    "dead_letter_contract",
    "worker_boundary",
    "human_status_projection",
    "phase2_entry_gate",
    "truth_flags",
}

EXPECTED_SOURCE_BINDING = {
    "source_archive_path": (
        "/Users/linzezhang/Downloads/"
        "IDS_Taskpack_v0_1_only_中文修订版.zip"
    ),
    "source_archive_sha256": (
        "55b782e338610aab6361b7945bb5e290ba60038a06cc765c7c2da801734db6d3"
    ),
    "source_member": (
        "IDS_v0_1_Final_Chinese_Revised/stages/"
        "STAGE-039_重试与死信策略.md"
    ),
    "source_member_match_count": 1,
    "source_member_integrity": "OK",
    "source_member_sha256": (
        "504caf72a6aeab67a650b4b096e728f03269f6ca8798f6e8a5c51210c8ddd7d9"
    ),
    "roadmap_sha256": (
        "a193fd2c44c51d634bf7887a1a6baf7e5199d9a8535e4211e35e97588e2e21a6"
    ),
    "instructions_sha256": (
        "ce456e06136d5ecc56cd7c9dc926abb5894817dda87bf7667588bf85211794f8"
    ),
    "source_verification_status": "SOURCE_VERIFIED",
}

EXPECTED_UPSTREAM = {
    "stage037_state_index_ref": (
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/"
        "job_state_model/stage037_job_state_model_index.json",
        "b70bf72ebe4212f45d380c13fbfe429791e1f4a5c73dccbba81211b7adc1c2d3",
    ),
    "stage037_checker_ref": (
        "KM_IDSystem/scripts/check_job_state_model.py",
        "7de8746b70ca1eaba78b672deebd9973113cedeacf3edbba09d2afb90407f404",
    ),
    "stage038_queue_index_ref": (
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/"
        "worker_queue_baseline/stage038_worker_queue_baseline_index.json",
        "68513591996a51fea90cd2ea863f42f910c0c3a45b70fd1611655bb6d95911ab",
    ),
    "stage038_delivery_contract_ref": (
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/"
        "worker_queue_baseline/stage038_worker_queue_delivery_contract.json",
        "a4067c25b46340c33bee5017c286d6867d2b72e8fa208430c005d6b1a342c7e4",
    ),
    "stage038_review_checker_ref": (
        "KM_IDSystem/scripts/check_worker_queue_stage_review.py",
        "b406cb8500b22b62c2d8400b6bfcf24cf1ed1b06990313ee66483a91bf255f96",
    ),
    "stage038_review_artifact_ref": (
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE038_STAGE_REVIEW.md",
        "5bb4cb3382f97ded9228d278c4cfb34fc5f0a65b8858263ed0c9bbd6c035eb04",
    ),
}

FALSE_TRUTH_FLAGS = {
    "ids_business_source_read_performed",
    "raw_metadata_content_accessed",
    "retry_scheduler_performed",
    "dead_letter_runtime_performed",
    "queue_runtime_performed",
    "worker_runtime_performed",
    "database_connection_performed",
    "schema_change_performed",
    "state_registry_write_performed",
    "runtime_output_written",
    "real_ids_business_job_created",
    "fake_ids_business_data_used",
    "external_api_call_performed",
    "github_upload_allowed",
    "app_reinstall_allowed",
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _keys_exact(value: Any, expected: set[str]) -> bool:
    return isinstance(value, dict) and set(value) == expected


def _upstream_bindings_valid(contract: dict[str, Any], project_root: Path) -> bool:
    bindings = contract.get("upstream_bindings")
    if not isinstance(bindings, dict) or set(bindings) != set(EXPECTED_UPSTREAM):
        return False
    repo_root = project_root.parent
    for key, (expected_ref, expected_hash) in EXPECTED_UPSTREAM.items():
        binding = bindings.get(key)
        if not _keys_exact(binding, {"ref", "sha256"}):
            return False
        if binding["ref"] != expected_ref or binding["sha256"] != expected_hash:
            return False
        source = repo_root / expected_ref
        if not source.is_file() or _sha256(source) != expected_hash:
            return False
    return True


def evaluate_contract(contract: Any, project_root: Path | None = None) -> dict[str, bool]:
    project_root = (project_root or Path(__file__).resolve().parents[1]).resolve()
    if not isinstance(contract, dict):
        return {"contract_is_object": False}

    state = contract.get("state_model_inheritance")
    inputs = contract.get("input_contract")
    identity = contract.get("identity_contract")
    budget = contract.get("retry_budget_contract")
    parameters = contract.get("policy_parameter_contract")
    classifications = contract.get("failure_classification")
    eligibility = contract.get("retry_eligibility_contract")
    resource = contract.get("resource_pause_contract")
    dead_letter = contract.get("dead_letter_contract")
    worker = contract.get("worker_boundary")
    projection = contract.get("human_status_projection")
    phase2 = contract.get("phase2_entry_gate")
    truth = contract.get("truth_flags")

    expected_input_fields = [
        "job_id",
        "job_type",
        "job_state",
        "state_version",
        "idempotency_key",
        "attempt_id",
        "retry_count",
        "max_retries",
        "retry_pending",
        "retry_disposition",
        "failure_observation_ref",
        "safe_error_code",
        "error_ref",
        "checkpoint_ref",
        "next_eligible_at",
        "next_eligible_evidence_ref",
        "resource_gate_refs",
        "audit_ref",
        "transition_request_id",
        "policy_version",
    ]
    expected_classification = {
        "TRANSIENT_RETRYABLE": {
            "decision_action": "SCHEDULE_RETRY",
            "target_state": "RETRY_WAIT",
            "legal_transition_paths": [
                ["RUNNING", "RETRY_WAIT"],
                ["CLAIMED", "RETRY_WAIT"],
                ["PAUSE_REQUESTED", "RETRY_WAIT"],
            ],
            "manual_review_required": False,
        },
        "PERMANENT_NON_RETRYABLE": {
            "decision_action": "FAIL_TERMINAL",
            "target_state": "FAILED",
            "legal_transition_paths": [["RUNNING", "FAILED"]],
            "manual_review_required": False,
        },
        "RESOURCE_CONDITION_PAUSE": {
            "decision_action": "PAUSE_RESOURCE_GATE",
            "target_state": "PAUSED",
            "legal_transition_paths": [
                ["QUEUED", "PAUSED"],
                ["RETRY_WAIT", "PAUSED"],
                ["RUNNING", "PAUSE_REQUESTED", "PAUSED"],
                ["CLAIMED", "PAUSE_REQUESTED", "PAUSED"],
            ],
            "manual_review_required": False,
        },
        "RETRY_EXHAUSTED": {
            "decision_action": "DEAD_LETTER",
            "target_state": "DEAD_LETTERED",
            "legal_transition_paths": [["RETRY_WAIT", "DEAD_LETTERED"]],
            "manual_review_required": True,
        },
        "POLICY_OR_AUTHORIZATION_BLOCK": {
            "decision_action": "REQUIRE_MANUAL_REVIEW",
            "target_state": "FAILED",
            "legal_transition_paths": [["RUNNING", "FAILED"]],
            "manual_review_required": True,
        },
        "INDETERMINATE_UNSAFE": {
            "decision_action": "REQUIRE_MANUAL_REVIEW",
            "target_state": "FAILED",
            "legal_transition_paths": [["RUNNING", "FAILED"]],
            "manual_review_required": True,
        },
    }
    classifications_exact = (
        isinstance(classifications, dict)
        and set(classifications) == set(expected_classification)
        and all(
            _keys_exact(
                classifications[name],
                {
                    "decision_action",
                    "target_state",
                    "legal_transition_paths",
                    "manual_review_required",
                    "retry_budget_consumed",
                    "owner_message_zh",
                },
            )
            and classifications[name]["decision_action"]
            == values["decision_action"]
            and classifications[name]["target_state"] == values["target_state"]
            and classifications[name]["legal_transition_paths"]
            == values["legal_transition_paths"]
            and classifications[name]["manual_review_required"]
            is values["manual_review_required"]
            and classifications[name]["retry_budget_consumed"] is False
            and bool(classifications[name]["owner_message_zh"])
            for name, values in expected_classification.items()
        )
    )

    return {
        "contract_shape_exact": set(contract) == EXPECTED_ROOT_KEYS,
        "identity_exact": (
            contract.get("schema_version")
            == "ids.stage039.retry_dead_letter.phase1.v1"
            and contract.get("stage") == "STAGE-039"
            and contract.get("phase") == "Phase 1"
            and contract.get("task_id") == "IDS-V0_1-STAGE039-P1"
            and contract.get("acceptance_id") == "ACC-STAGE-039"
            and contract.get("retry_policy_contract_id")
            == "ids.retry_dead_letter.v0_1.p1"
            and contract.get("contract_state")
            == "PHASE1_ENGINEERING_CONTRACT_RUNTIME_DISABLED"
            and contract.get("execution_ready") is False
            and contract.get("next_gate") == "IDS-STAGE039-P2-GATE"
        ),
        "source_binding_exact": contract.get("source_binding") == EXPECTED_SOURCE_BINDING,
        "upstream_bindings_exact": _upstream_bindings_valid(contract, project_root),
        "state_model_inheritance_exact": (
            _keys_exact(
                state,
                {
                    "state_model_version",
                    "terminal_states",
                    "terminal_state_mutation_allowed",
                    "retryable_failure_path",
                    "retry_admission_path",
                    "exhaustion_path",
                    "permanent_failure_path",
                    "running_to_dead_letter_allowed",
                    "direct_running_cancel_allowed",
                },
            )
            and state["state_model_version"] == "ids.job_state.v1"
            and state["terminal_states"]
            == ["SUCCEEDED", "FAILED", "DEAD_LETTERED", "CANCELLED"]
            and state["terminal_state_mutation_allowed"] is False
            and state["retryable_failure_path"] == ["RUNNING", "RETRY_WAIT"]
            and state["retry_admission_path"] == ["RETRY_WAIT", "QUEUED"]
            and state["exhaustion_path"] == ["RETRY_WAIT", "DEAD_LETTERED"]
            and state["permanent_failure_path"] == ["RUNNING", "FAILED"]
            and state["running_to_dead_letter_allowed"] is False
            and state["direct_running_cancel_allowed"] is False
        ),
        "input_contract_fail_closed": (
            _keys_exact(
                inputs,
                {
                    "required_fields",
                    "raw_source_body_allowed",
                    "plaintext_secret_allowed",
                    "untracked_reference_allowed",
                    "missing_required_field_behavior",
                },
            )
            and inputs.get("required_fields") == expected_input_fields
            and inputs.get("raw_source_body_allowed") is False
            and inputs.get("plaintext_secret_allowed") is False
            and inputs.get("untracked_reference_allowed") is False
            and inputs.get("missing_required_field_behavior")
            == "FAIL_CLOSED_REQUIRE_MANUAL_REVIEW"
        ),
        "identity_contract_exact": (
            _keys_exact(
                identity,
                {
                    "job_id_scope",
                    "attempt_id_scope",
                    "idempotency_key_scope",
                    "transition_request_id_scope",
                    "duplicate_transition_behavior",
                    "terminal_manual_rerun",
                    "terminal_manual_rerun_required_fields",
                    "terminal_rerun_idempotency_scope",
                    "terminal_manual_rerun_owner_authorization_required",
                    "terminal_job_reopen_allowed",
                },
            )
            and identity.get("job_id_scope") == "stable_across_attempts"
            and identity.get("attempt_id_scope") == "unique_per_execution_attempt"
            and identity.get("idempotency_key_scope") == "stable_for_one_logical_job"
            and identity.get("transition_request_id_scope")
            == "unique_per_state_transition_request"
            and identity.get("duplicate_transition_behavior")
            == "RETURN_ORIGINAL_RESULT_NO_DOUBLE_BUDGET_CONSUMPTION"
            and identity.get("terminal_manual_rerun") == "NEW_LINKED_JOB_REQUIRED"
            and identity.get("terminal_manual_rerun_required_fields")
            == ["parent_job_id", "rerun_request_id", "new_job_id", "new_idempotency_key"]
            and identity.get("terminal_rerun_idempotency_scope")
            == "parent_job_id_plus_owner_rerun_request_id"
            and identity.get("terminal_manual_rerun_owner_authorization_required") is True
            and identity.get("terminal_job_reopen_allowed") is False
        ),
        "retry_budget_exact": (
            _keys_exact(
                budget,
                {
                    "max_retries_definition",
                    "total_attempt_limit_formula",
                    "initial_retry_count",
                    "max_retries_immutable_after_job_creation",
                    "reservation_increments_retry_count",
                    "admission_increments_retry_count",
                    "admission_increment_atomic_with_requeue",
                    "resource_pause_consumes_retry",
                    "exhaustion_condition",
                    "exhausted_requeue_allowed",
                    "missing_policy_behavior",
                },
            )
            and budget.get("max_retries_definition")
            == "number_of_retry_attempts_after_initial_attempt"
            and budget.get("total_attempt_limit_formula") == "1 + max_retries"
            and budget.get("initial_retry_count") == 0
            and budget.get("max_retries_immutable_after_job_creation") is True
            and budget.get("reservation_increments_retry_count") is False
            and budget.get("admission_increments_retry_count") is True
            and budget.get("admission_increment_atomic_with_requeue") is True
            and budget.get("resource_pause_consumes_retry") is False
            and budget.get("exhaustion_condition") == "retry_count == max_retries"
            and budget.get("exhausted_requeue_allowed") is False
            and budget.get("missing_policy_behavior") == "NO_AUTOMATIC_RETRY"
        ),
        "policy_parameters_deferred_fail_closed": (
            _keys_exact(
                parameters,
                {
                    "numeric_values_assigned_in_phase1",
                    "required_before_runtime",
                    "max_retries_validation",
                    "backoff_schedule_validation",
                    "jitter_validation",
                    "retryable_error_code_policy",
                    "unversioned_or_missing_policy_behavior",
                    "selection_owner",
                    "selection_evidence_required",
                },
            )
            and parameters.get("numeric_values_assigned_in_phase1") is False
            and parameters.get("required_before_runtime")
            == [
                "max_retries",
                "backoff_schedule_seconds",
                "jitter_policy",
                "retryable_safe_error_codes",
            ]
            and parameters.get("max_retries_validation")
            == "EXPLICIT_INTEGER_GTE_ZERO_IMMUTABLE_PER_JOB"
            and parameters.get("backoff_schedule_validation")
            == "EXPLICIT_BOUNDED_NONNEGATIVE_SCHEDULE_COVERS_MAX_RETRIES"
            and parameters.get("jitter_validation")
            == "EXPLICIT_BOUNDED_NO_NEGATIVE_EFFECTIVE_DELAY"
            and parameters.get("retryable_error_code_policy")
            == "VERSIONED_ALLOWLIST_DEFAULT_DENY"
            and parameters.get("unversioned_or_missing_policy_behavior")
            == "NO_AUTOMATIC_RETRY_REQUIRE_MANUAL_REVIEW"
            and parameters.get("selection_owner") == "IDS-V0_1-STAGE039-P2"
            and parameters.get("selection_evidence_required") is True
        ),
        "failure_classification_exact": classifications_exact,
        "retry_eligibility_exact": (
            _keys_exact(
                eligibility,
                {
                    "required_source_state",
                    "required_retry_disposition",
                    "required_retry_pending",
                    "required_budget_expression",
                    "next_eligible_at_required",
                    "next_eligible_evidence_required",
                    "versioned_policy_required",
                    "resource_gates_must_pass",
                    "previous_claim_deactivated",
                    "previous_lock_released_or_fenced",
                    "checkpoint_compatible_or_restart_safe_required",
                    "compare_and_set_required",
                    "append_only_audit_required",
                    "admission_transition",
                    "retry_counter_increment_point",
                    "terminal_reopen_allowed",
                },
            )
            and eligibility.get("required_source_state") == "RETRY_WAIT"
            and eligibility.get("required_retry_disposition") == "eligible"
            and eligibility.get("required_retry_pending") is True
            and eligibility.get("required_budget_expression")
            == "retry_count < max_retries"
            and eligibility.get("next_eligible_at_required") is True
            and eligibility.get("next_eligible_evidence_required") is True
            and eligibility.get("versioned_policy_required") is True
            and eligibility.get("resource_gates_must_pass") is True
            and eligibility.get("previous_claim_deactivated") is True
            and eligibility.get("previous_lock_released_or_fenced") is True
            and eligibility.get("checkpoint_compatible_or_restart_safe_required") is True
            and eligibility.get("compare_and_set_required") is True
            and eligibility.get("append_only_audit_required") is True
            and eligibility.get("admission_transition") == "RETRY_WAIT_TO_QUEUED"
            and eligibility.get("retry_counter_increment_point")
            == "ATOMIC_RETRY_ADMISSION"
            and eligibility.get("terminal_reopen_allowed") is False
        ),
        "resource_pause_exact": (
            _keys_exact(
                resource,
                {
                    "pause_reason_codes",
                    "retry_budget_consumed",
                    "retry_pending_preserved_when_applicable",
                    "automatic_resume_allowed",
                    "owner_revalidation_required",
                    "resume_runtime_owner",
                },
            )
            and resource.get("pause_reason_codes")
            == [
                "external_drive_offline",
                "disk_space_insufficient",
                "external_api_budget_insufficient",
            ]
            and resource.get("retry_budget_consumed") is False
            and resource.get("retry_pending_preserved_when_applicable") is True
            and resource.get("automatic_resume_allowed") is False
            and resource.get("owner_revalidation_required") is True
            and resource.get("resume_runtime_owner") == "STAGE-042"
        ),
        "dead_letter_evidence_safe": (
            _keys_exact(
                dead_letter,
                {
                    "required_source_state",
                    "required_failure_class",
                    "required_metadata_refs",
                    "raw_payload_copy_allowed",
                    "plaintext_secret_allowed",
                    "automatic_replay_allowed",
                    "manual_triage_required",
                    "append_only_audit_required",
                    "evidence_deletion_allowed",
                    "protected_artifact_classes",
                },
            )
            and dead_letter.get("required_source_state") == "RETRY_WAIT"
            and dead_letter.get("required_failure_class") == "RETRY_EXHAUSTED"
            and dead_letter.get("required_metadata_refs")
            == [
                "job_id",
                "attempt_id",
                "retry_count",
                "max_retries",
                "safe_error_code",
                "error_ref",
                "checkpoint_ref",
                "input_refs",
                "output_refs",
                "audit_ref",
                "policy_version",
            ]
            and dead_letter.get("raw_payload_copy_allowed") is False
            and dead_letter.get("plaintext_secret_allowed") is False
            and dead_letter.get("automatic_replay_allowed") is False
            and dead_letter.get("manual_triage_required") is True
            and dead_letter.get("append_only_audit_required") is True
            and dead_letter.get("evidence_deletion_allowed") is False
            and dead_letter.get("protected_artifact_classes")
            == ["FACT_SOURCE", "MANIFEST", "EVIDENCE_LEDGER", "AUDIT_LOG", "REPORT_SNAPSHOT"]
        ),
        "worker_and_downstream_ownership_exact": (
            _keys_exact(
                worker,
                {
                    "stage039_phase2_owns",
                    "queue_worker_owner",
                    "measured_backpressure_owner",
                    "lock_lease_fencing_owner",
                    "automatic_lifecycle_owner",
                    "worker_crash_recovery_owner",
                    "cleanup_execution_owner",
                    "production_worker_activation_allowed",
                    "database_persistence_allowed_in_phase1",
                },
            )
            and worker.get("stage039_phase2_owns")
            == [
                "FAILURE_CLASSIFICATION",
                "RETRY_DECISION",
                "RETRY_ELIGIBILITY",
                "DEAD_LETTER_DECISION",
                "MANUAL_TRIAGE_METADATA",
            ]
            and worker.get("queue_worker_owner") == "STAGE-038"
            and worker.get("measured_backpressure_owner") == "STAGE-040"
            and worker.get("lock_lease_fencing_owner") == "STAGE-041"
            and worker.get("automatic_lifecycle_owner") == "STAGE-042"
            and worker.get("worker_crash_recovery_owner") == "STAGE-043"
            and worker.get("cleanup_execution_owner") == "STAGE-044"
            and worker.get("production_worker_activation_allowed") is False
            and worker.get("database_persistence_allowed_in_phase1") is False
        ),
        "human_projection_exact": (
            isinstance(projection, dict)
            and set(projection)
            == {"RETRY_WAIT", "PAUSED", "FAILED", "DEAD_LETTERED", "CANCELLED"}
            and all(
                _keys_exact(
                    projection[state_name],
                    {"label_zh", "owner_action_zh", "owner_attention_required"},
                )
                for state_name in projection
            )
            and projection["RETRY_WAIT"]["label_zh"] == "等待重试"
            and projection["RETRY_WAIT"]["owner_action_zh"]
            == "查看安全错误与下次资格时间"
            and projection["RETRY_WAIT"]["owner_attention_required"] is False
            and projection["PAUSED"]["label_zh"] == "已暂停"
            and projection["PAUSED"]["owner_action_zh"] == "恢复资源并完成复核"
            and projection["PAUSED"]["owner_attention_required"] is True
            and projection["FAILED"]["label_zh"] == "处理失败"
            and projection["FAILED"]["owner_action_zh"]
            == "人工复核后可创建新的关联任务"
            and projection["FAILED"]["owner_attention_required"] is True
            and projection["DEAD_LETTERED"]["label_zh"] == "需要人工处理"
            and projection["DEAD_LETTERED"]["owner_action_zh"]
            == "人工复核，不自动继续"
            and projection["DEAD_LETTERED"]["owner_attention_required"] is True
            and projection["CANCELLED"]["label_zh"] == "已取消"
            and projection["CANCELLED"]["owner_action_zh"]
            == "查看停止原因与已保留证据"
            and projection["CANCELLED"]["owner_attention_required"] is False
        ),
        "phase2_gate_exact": (
            _keys_exact(
                phase2,
                {
                    "entry_authorized",
                    "must_run_separately",
                    "required_task_id",
                    "required_acceptance_id",
                    "required_contract_state",
                    "requires_versioned_policy_parameters",
                    "requires_isolated_non_production_execution",
                    "production_activation_allowed",
                    "next_gate",
                },
            )
            and phase2.get("entry_authorized") is True
            and phase2.get("must_run_separately") is True
            and phase2.get("required_task_id") == "IDS-V0_1-STAGE039-P2"
            and phase2.get("required_acceptance_id") == "ACC-STAGE-039"
            and phase2.get("required_contract_state")
            == "PHASE1_ENGINEERING_CONTRACT_RUNTIME_DISABLED"
            and phase2.get("requires_versioned_policy_parameters") is True
            and phase2.get("requires_isolated_non_production_execution") is True
            and phase2.get("production_activation_allowed") is False
            and phase2.get("next_gate") == "IDS-STAGE039-P2-GATE"
        ),
        "truth_flags_exact": (
            isinstance(truth, dict)
            and truth.get("taskpack_source_read_performed") is True
            and set(truth) == FALSE_TRUTH_FLAGS | {"taskpack_source_read_performed"}
            and all(truth.get(key) is False for key in FALSE_TRUTH_FLAGS)
        ),
    }


def build_stage039_phase1_report(project_root: Path | None = None) -> dict[str, Any]:
    project_root = (project_root or Path(__file__).resolve().parents[1]).resolve()
    contract_path = project_root / CONTRACT_RELATIVE
    try:
        contract = json.loads(contract_path.read_text(encoding="utf-8"))
        load_error = None
    except (OSError, json.JSONDecodeError) as exc:
        contract = {}
        load_error = f"{type(exc).__name__}: {exc}"
    checks = evaluate_contract(contract, project_root)
    truth = contract.get("truth_flags") if isinstance(contract, dict) else {}
    truth = truth if isinstance(truth, dict) else {}
    return {
        "schema_version": "ids.stage039.retry_dead_letter.phase1.report.v1",
        "stage": "STAGE-039",
        "phase": "Phase 1",
        "task_id": "IDS-V0_1-STAGE039-P1",
        "acceptance_id": "ACC-STAGE-039",
        "retry_policy_contract_id": contract.get("retry_policy_contract_id"),
        "contract_state": contract.get("contract_state"),
        "next_gate": contract.get("next_gate"),
        "load_error": load_error,
        "contract_checks": checks,
        "phase1_contract_valid": load_error is None and bool(checks) and all(checks.values()),
        **{key: truth.get(key, False) for key in sorted(FALSE_TRUTH_FLAGS)},
    }


def main() -> int:
    report = build_stage039_phase1_report()
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0 if report["phase1_contract_valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
