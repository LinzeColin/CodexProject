#!/usr/bin/env python3
"""Validate the STAGE-040 Phase 1 backpressure engineering contract."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


CONTRACT_RELATIVE = (
    "docs/pursuing_goal/ids_v0_1/backpressure_policy/"
    "stage040_backpressure_policy_contract.json"
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
    "backpressure_policy_contract_id",
    "contract_state",
    "execution_ready",
    "next_gate",
    "source_binding",
    "upstream_bindings",
    "state_model_inheritance",
    "input_contract",
    "pressure_observation_contract",
    "decision_matrix",
    "retry_budget_invariants",
    "policy_parameter_contract",
    "fairness_contract",
    "idempotency_contract",
    "lock_boundary",
    "partial_output_cleanup_boundary",
    "worker_boundary",
    "ownership_matrix",
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
        "STAGE-040_反压策略.md"
    ),
    "source_member_match_count": 1,
    "source_member_integrity": "OK",
    "source_member_sha256": (
        "f0ef128467300d7541796f8d51caca673f838cac2552eba2e415a94a07af614d"
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
    "stage038_delivery_contract_ref": (
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/"
        "worker_queue_baseline/stage038_worker_queue_delivery_contract.json",
        "a4067c25b46340c33bee5017c286d6867d2b72e8fa208430c005d6b1a342c7e4",
    ),
    "stage039_delivery_contract_ref": (
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/"
        "retry_dead_letter/stage039_retry_dead_letter_delivery_contract.json",
        "c4aad64a9283de683067aff07026d723c708285c57eef8a0eac4ee1b13f5cb96",
    ),
    "stage039_review_checker_ref": (
        "KM_IDSystem/scripts/check_retry_dead_letter_stage_review.py",
        "108bf11a4ec9de8c7d4378da421c75b30568c79e78e5bd368ae1bfb48dccc243",
    ),
    "stage039_review_artifact_ref": (
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE039_STAGE_REVIEW.md",
        "32e621db9d7d4ad87ff4f6788e1de22d7ada9c0f57ce756a76a9608a864c4b9b",
    ),
}

EXPECTED_INPUT_FIELDS = [
    "job_id",
    "job_type",
    "job_state",
    "state_version",
    "idempotency_key",
    "priority_ref",
    "pressure_observation_refs",
    "claim_lock_refs",
    "retry_refs",
    "checkpoint_ref",
    "input_ref",
    "output_ref",
    "error_ref",
    "audit_ref",
    "policy_version",
    "observation_time",
]

EXPECTED_OBSERVATION_FIELDS = [
    "signal_code",
    "observed_value_ref",
    "unit",
    "observed_at",
    "source_ref",
    "policy_version",
    "validity_status",
]

PAUSE_PATHS = [
    ["QUEUED", "PAUSED"],
    ["RETRY_WAIT", "PAUSED"],
    ["RUNNING", "PAUSE_REQUESTED", "PAUSED"],
    ["CLAIMED", "PAUSE_REQUESTED", "PAUSED"],
]

EXPECTED_DECISIONS = {
    "HEALTHY": ("ADMIT", "NO_POLICY_STATE_MUTATION", [], False),
    "QUEUE_SOFT_PRESSURE": (
        "THROTTLE_ADMISSION",
        "NO_LIFECYCLE_MUTATION",
        [],
        False,
    ),
    "QUEUE_HARD_CAPACITY": (
        "DENY_NEW_ADMISSION",
        "NO_QUEUE_RECORD_CREATED",
        [],
        False,
    ),
    "EXTERNAL_DRIVE_OFFLINE": (
        "PAUSE_RESOURCE_GATE",
        "LEGAL_PAUSE_PATH_REQUIRED",
        PAUSE_PATHS,
        False,
    ),
    "DISK_SPACE_INSUFFICIENT": (
        "PAUSE_RESOURCE_GATE",
        "LEGAL_PAUSE_PATH_REQUIRED",
        PAUSE_PATHS,
        False,
    ),
    "EXTERNAL_API_BUDGET_INSUFFICIENT": (
        "PAUSE_RESOURCE_GATE",
        "LEGAL_PAUSE_PATH_REQUIRED",
        PAUSE_PATHS,
        False,
    ),
    "UNKNOWN_OR_STALE_PRESSURE": (
        "REQUIRE_MANUAL_REVIEW",
        "NO_NEW_ADMISSION",
        [],
        True,
    ),
}

DEFERRED_PARAMETERS = [
    "queue_soft_pressure_threshold",
    "queue_hard_capacity_threshold",
    "disk_free_bytes_threshold",
    "disk_reserve_bytes",
    "external_api_budget_window",
    "high_low_watermarks",
    "observation_ttl",
    "per_job_type_concurrency",
    "admission_rate_limit",
]

FALSE_TRUTH_FLAGS = {
    "ids_business_source_read_performed",
    "raw_metadata_content_accessed",
    "backpressure_runtime_performed",
    "queue_runtime_performed",
    "worker_runtime_performed",
    "lock_runtime_performed",
    "automatic_resume_performed",
    "cleanup_runtime_performed",
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


def _decision_matrix_valid(value: Any) -> bool:
    if not isinstance(value, dict) or set(value) != set(EXPECTED_DECISIONS):
        return False
    expected_keys = {
        "decision_action",
        "state_effect",
        "legal_transition_paths",
        "manual_review_required",
    }
    for signal, (action, effect, paths, manual) in EXPECTED_DECISIONS.items():
        row = value.get(signal)
        if not _keys_exact(row, expected_keys):
            return False
        if row != {
            "decision_action": action,
            "state_effect": effect,
            "legal_transition_paths": paths,
            "manual_review_required": manual,
        }:
            return False
    return True


def evaluate_contract(contract: Any, project_root: Path | None = None) -> dict[str, bool]:
    project_root = (project_root or Path(__file__).resolve().parents[1]).resolve()
    if not isinstance(contract, dict):
        return {"contract_is_object": False}

    state = contract.get("state_model_inheritance")
    inputs = contract.get("input_contract")
    observation = contract.get("pressure_observation_contract")
    retry = contract.get("retry_budget_invariants")
    parameters = contract.get("policy_parameter_contract")
    fairness = contract.get("fairness_contract")
    idempotency = contract.get("idempotency_contract")
    locking = contract.get("lock_boundary")
    cleanup = contract.get("partial_output_cleanup_boundary")
    worker = contract.get("worker_boundary")
    ownership = contract.get("ownership_matrix")
    projection = contract.get("human_status_projection")
    phase2 = contract.get("phase2_entry_gate")
    truth = contract.get("truth_flags")

    checks = {
        "contract_is_object": True,
        "root_fields_exact": set(contract) == EXPECTED_ROOT_KEYS,
        "identity_exact": (
            contract.get("schema_version") == "ids.stage040.backpressure.phase1.v1"
            and contract.get("stage") == "STAGE-040"
            and contract.get("phase") == "Phase 1"
            and contract.get("task_id") == "IDS-V0_1-STAGE040-P1"
            and contract.get("acceptance_id") == "ACC-STAGE-040"
            and contract.get("local_code") == "D07-S004"
            and contract.get("backpressure_policy_contract_id")
            == "ids.backpressure_policy.v0_1.p1"
            and contract.get("contract_state")
            == "PHASE1_ENGINEERING_CONTRACT_RUNTIME_DISABLED"
            and contract.get("execution_ready") is False
            and contract.get("next_gate") == "IDS-STAGE040-P2-GATE"
        ),
        "source_binding_exact": contract.get("source_binding")
        == EXPECTED_SOURCE_BINDING,
        "upstream_bindings_current": _upstream_bindings_valid(contract, project_root),
        "state_model_inheritance_valid": (
            _keys_exact(
                state,
                {
                    "state_model_version",
                    "terminal_states",
                    "terminal_state_mutation_allowed",
                    "resource_pause_paths",
                    "active_job_pause_requires_safe_point",
                },
            )
            and state.get("state_model_version") == "ids.job_state.v1"
            and state.get("terminal_states")
            == ["SUCCEEDED", "FAILED", "DEAD_LETTERED", "CANCELLED"]
            and state.get("terminal_state_mutation_allowed") is False
            and state.get("resource_pause_paths") == PAUSE_PATHS
            and state.get("active_job_pause_requires_safe_point") is True
        ),
        "input_contract_valid": (
            _keys_exact(
                inputs,
                {
                    "required_fields",
                    "reference_only",
                    "raw_payload_allowed",
                    "missing_required_field_action",
                },
            )
            and inputs.get("required_fields") == EXPECTED_INPUT_FIELDS
            and inputs.get("reference_only") is True
            and inputs.get("raw_payload_allowed") is False
            and inputs.get("missing_required_field_action")
            == "REQUIRE_MANUAL_REVIEW"
        ),
        "pressure_observation_valid": (
            _keys_exact(
                observation,
                {
                    "required_fields",
                    "raw_source_body_allowed",
                    "unknown_or_stale_action",
                    "observation_ttl_policy",
                    "audit_reference_required",
                },
            )
            and observation.get("required_fields") == EXPECTED_OBSERVATION_FIELDS
            and observation.get("raw_source_body_allowed") is False
            and observation.get("unknown_or_stale_action")
            == "REQUIRE_MANUAL_REVIEW"
            and observation.get("observation_ttl_policy") == "DEFERRED_TO_PHASE2"
            and observation.get("audit_reference_required") is True
        ),
        "decision_matrix_valid": _decision_matrix_valid(
            contract.get("decision_matrix")
        ),
        "retry_budget_invariants_valid": (
            _keys_exact(
                retry,
                {
                    "throttle_consumes_retry",
                    "resource_pause_consumes_retry",
                    "admission_denial_consumes_retry",
                    "automatic_resume_allowed",
                    "automatic_resume_runtime_owner",
                    "retry_policy_runtime_owner",
                },
            )
            and retry.get("throttle_consumes_retry") is False
            and retry.get("resource_pause_consumes_retry") is False
            and retry.get("admission_denial_consumes_retry") is False
            and retry.get("automatic_resume_allowed") is False
            and retry.get("automatic_resume_runtime_owner") == "STAGE-042"
            and retry.get("retry_policy_runtime_owner") == "STAGE-039"
        ),
        "policy_parameters_deferred": (
            _keys_exact(
                parameters,
                {
                    "numeric_values_assigned",
                    "deferred_parameters",
                    "phase2_selection_requirements",
                    "implicit_default_allowed",
                    "production_calibrated",
                },
            )
            and parameters.get("numeric_values_assigned") is False
            and parameters.get("deferred_parameters") == DEFERRED_PARAMETERS
            and parameters.get("phase2_selection_requirements")
            == [
                "source",
                "rationale",
                "unit",
                "policy_version",
                "validation_evidence",
                "rollback",
                "high_low_watermark_ordering",
            ]
            and parameters.get("implicit_default_allowed") is False
            and parameters.get("production_calibrated") is False
        ),
        "fairness_boundary_valid": (
            _keys_exact(
                fairness,
                {
                    "priority_cannot_bypass_safety_gate",
                    "starvation_allowed",
                    "priority_vocabulary_owner",
                    "scheduler_algorithm",
                    "per_job_type_concurrency",
                },
            )
            and fairness.get("priority_cannot_bypass_safety_gate") is True
            and fairness.get("starvation_allowed") is False
            and fairness.get("priority_vocabulary_owner") == "STAGE-022"
            and fairness.get("scheduler_algorithm") == "DEFERRED_TO_PHASE2"
            and fairness.get("per_job_type_concurrency") == "DEFERRED_TO_PHASE2"
        ),
        "idempotency_boundary_valid": (
            _keys_exact(
                idempotency,
                {
                    "decision_key_formula",
                    "duplicate_decision_returns_original",
                    "throttle_rotates_idempotency_key",
                    "pause_rotates_idempotency_key",
                    "denied_admission_creates_job",
                },
            )
            and idempotency.get("decision_key_formula")
            == "idempotency_key + policy_version + pressure_observation_set_digest"
            and idempotency.get("duplicate_decision_returns_original") is True
            and idempotency.get("throttle_rotates_idempotency_key") is False
            and idempotency.get("pause_rotates_idempotency_key") is False
            and idempotency.get("denied_admission_creates_job") is False
        ),
        "lock_boundary_valid": (
            _keys_exact(
                locking,
                {
                    "runtime_owner",
                    "claim_lock_refs_read_only",
                    "lock_acquire_allowed",
                    "lock_renew_allowed",
                    "lock_release_allowed",
                    "fencing_token_issue_allowed",
                    "lock_runtime_performed",
                },
            )
            and locking.get("runtime_owner") == "STAGE-041"
            and locking.get("claim_lock_refs_read_only") is True
            and all(
                locking.get(key) is False
                for key in (
                    "lock_acquire_allowed",
                    "lock_renew_allowed",
                    "lock_release_allowed",
                    "fencing_token_issue_allowed",
                    "lock_runtime_performed",
                )
            )
        ),
        "cleanup_boundary_valid": (
            _keys_exact(
                cleanup,
                {
                    "runtime_owner",
                    "cleanup_allowlist_policy_only",
                    "cleanup_eligible_classes",
                    "protected_artifact_classes",
                    "protected_artifact_delete_allowed",
                    "cleanup_runtime_performed",
                },
            )
            and cleanup.get("runtime_owner") == "STAGE-044"
            and cleanup.get("cleanup_allowlist_policy_only") is True
            and cleanup.get("cleanup_eligible_classes")
            == ["TEMP_STAGING_OUTPUT", "INCOMPLETE_DERIVATIVE_OUTPUT"]
            and cleanup.get("protected_artifact_classes")
            == [
                "FACT_SOURCE",
                "MANIFEST",
                "EVIDENCE_LEDGER",
                "AUDIT_LOG",
                "REPORT_SNAPSHOT",
            ]
            and cleanup.get("protected_artifact_delete_allowed") is False
            and cleanup.get("cleanup_runtime_performed") is False
        ),
        "worker_boundary_valid": (
            _keys_exact(
                worker,
                {
                    "transport_runtime_owner",
                    "policy_output",
                    "queue_mutation_allowed",
                    "worker_control_performed",
                    "persistent_state_write_allowed",
                },
            )
            and worker.get("transport_runtime_owner") == "STAGE-038"
            and worker.get("policy_output") == "DECISION_METADATA_ONLY"
            and worker.get("queue_mutation_allowed") is False
            and worker.get("worker_control_performed") is False
            and worker.get("persistent_state_write_allowed") is False
        ),
        "ownership_matrix_valid": ownership
        == {
            "backpressure_decision_policy": "STAGE-040",
            "queue_and_worker_transport": "STAGE-038",
            "retry_and_dead_letter_policy": "STAGE-039",
            "lock_lease_and_fencing_runtime": "STAGE-041",
            "automatic_resume_runtime": "STAGE-042",
            "crash_recovery_runtime": "STAGE-043",
            "cleanup_execution_runtime": "STAGE-044",
        },
        "human_status_projection_valid": projection
        == {
            "ADMIT": "可接收",
            "THROTTLE_ADMISSION": "限流中",
            "DENY_NEW_ADMISSION": "暂不接收新任务",
            "PAUSE_RESOURCE_GATE": "已暂停",
            "REQUIRE_MANUAL_REVIEW": "等待人工复核",
        },
        "phase2_gate_valid": phase2
        == {
            "entry_authorized": True,
            "required_task_id": "IDS-V0_1-STAGE040-P2",
            "required_gate_id": "IDS-STAGE040-P2-GATE",
            "must_run_separately": True,
            "requires_upstream_hash_revalidation": True,
            "requires_versioned_parameter_selection": True,
            "production_activation_allowed": False,
        },
        "truth_flags_fail_closed": (
            isinstance(truth, dict)
            and set(truth) == FALSE_TRUTH_FLAGS | {"taskpack_source_read_performed"}
            and truth.get("taskpack_source_read_performed") is True
            and all(truth.get(key) is False for key in FALSE_TRUTH_FLAGS)
        ),
    }
    return checks


def build_stage040_phase1_report(
    contract_path: Path | None = None,
) -> dict[str, Any]:
    project_root = Path(__file__).resolve().parents[1]
    path = contract_path or project_root / CONTRACT_RELATIVE
    try:
        contract = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        contract = None
    checks = evaluate_contract(contract, project_root)
    truth = contract.get("truth_flags", {}) if isinstance(contract, dict) else {}
    return {
        "schema_version": "ids.stage040.backpressure.phase1.report.v1",
        "stage": "STAGE-040",
        "phase": "Phase 1",
        "task_id": "IDS-V0_1-STAGE040-P1",
        "acceptance_id": "ACC-STAGE-040",
        "phase1_contract_valid": bool(checks) and all(checks.values()),
        "contract_checks": checks,
        "contract_state": (
            contract.get("contract_state")
            if isinstance(contract, dict)
            else "CONTRACT_UNAVAILABLE"
        ),
        "next_gate": "IDS-STAGE040-P2-GATE",
        **{key: bool(truth.get(key, False)) for key in FALSE_TRUTH_FLAGS},
    }


def main() -> int:
    report = build_stage040_phase1_report()
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if report["phase1_contract_valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
