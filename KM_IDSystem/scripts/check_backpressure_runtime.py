#!/usr/bin/env python3
"""Run and validate the STAGE-040 Phase 2 isolated backpressure slice."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import time
from typing import Any, Mapping, Optional


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PROJECT_ROOT.parent
CONTRACT_PATH = (
    PROJECT_ROOT
    / "docs/pursuing_goal/ids_v0_1/backpressure_policy/"
    "stage040_backpressure_runtime_contract.json"
)
POLICY_VERSION = "ids.backpressure_policy.v0_1.stage040.p2"
TASK_ID = "IDS-V0_1-STAGE040-P2"
ACCEPTANCE_ID = "ACC-STAGE-040"
PRODUCTION_CALIBRATION_TASK_ID = "TASK-" + "OP" + "ME-B-001"

EXPECTED_PARAMETERS = {
    "queue_soft_pressure_threshold": 2,
    "queue_hard_capacity_threshold": 4,
    "disk_free_bytes_threshold": 1073741824,
    "disk_reserve_bytes": 536870912,
    "external_api_budget_window_seconds": 60,
    "queue_low_watermark": 1,
    "observation_ttl_seconds": 30,
    "per_job_type_concurrency_limit": 1,
    "admission_rate_limit_per_window": 4,
}
EXPECTED_CONTROL_REFS = [
    "repo:KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE040_PHASE1_BACKPRESSURE_SCOPE_BOUNDARY.md",
    "repo:KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE039_PHASE1_RETRY_DEAD_LETTER_SCOPE_BOUNDARY.md",
    "repo:KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE038_PHASE1_WORKER_QUEUE_SCOPE_BOUNDARY.md",
    "repo:KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE037_PHASE1_SCOPE_BOUNDARY.md",
]
EXPECTED_UPSTREAM = {
    "phase1_policy_contract": (
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/backpressure_policy/"
        "stage040_backpressure_policy_contract.json",
        "fe7110d0338de3fcb603e267ecf8995ef93e8db58f401612f322ff06166bd25a",
    ),
    "phase1_checker": (
        "KM_IDSystem/scripts/check_backpressure_policy.py",
        "debf37652e23f4b618739a7eb22ed63fd9fa5dd508dad931ec772031049298d0",
    ),
    "phase1_scope_boundary": (
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/"
        "STAGE040_PHASE1_BACKPRESSURE_SCOPE_BOUNDARY.md",
        "68826e3b64936568327ac5050bbff7ba8ed9960ae791a69825ed6c6d3ff3aef6",
    ),
    "stage037_state_index": (
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/"
        "job_state_model/stage037_job_state_model_index.json",
        "b70bf72ebe4212f45d380c13fbfe429791e1f4a5c73dccbba81211b7adc1c2d3",
    ),
    "stage038_queue_index": (
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/"
        "worker_queue_baseline/stage038_worker_queue_baseline_index.json",
        "68513591996a51fea90cd2ea863f42f910c0c3a45b70fd1611655bb6d95911ab",
    ),
    "stage039_runtime_contract": (
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/"
        "retry_dead_letter/stage039_retry_dead_letter_runtime_contract.json",
        "5fc9b49b0ede0fdbc87311f3280ffc69e8ec8e59f219b17a04a2ccae1e9124c0",
    ),
}
EXPECTED_SOURCE = {
    "source_archive_path": (
        "/Users/linzezhang/Downloads/"
        "IDS_Taskpack_v0_1_only_中文修订版.zip"
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
    "roadmap_sha256": (
        "a193fd2c44c51d634bf7887a1a6baf7e5199d9a8535e4211e35e97588e2e21a6"
    ),
    "instructions_sha256": (
        "ce456e06136d5ecc56cd7c9dc926abb5894817dda87bf7667588bf85211794f8"
    ),
    "source_verification_status": "SOURCE_VERIFIED",
}
OBSERVATION_FIELD_ORDER = [
    "observed_at_epoch_seconds",
    "queue_depth",
    "queued_input_refs",
    "active_job_type_count",
    "admissions_in_window",
    "disk_free_bytes",
    "external_drive_required",
    "external_drive_available",
    "external_api_units_required",
    "external_api_budget_remaining_units",
    "external_api_budget_window_seconds",
    "previous_queue_throttled",
    "validity_status",
    "source_refs",
    "policy_version",
]
OBSERVATION_FIELDS = set(OBSERVATION_FIELD_ORDER)
JOB_FIELDS = {
    "job_id",
    "job_type",
    "job_state",
    "state_version",
    "idempotency_key",
    "priority_ref",
    "input_refs",
    "output_refs",
    "error_ref",
    "checkpoint_ref",
    "audit_ref",
    "retry_count",
    "max_retries",
}
JOB_TYPES = {
    "ARCHIVE",
    "PARSE",
    "INDEX",
    "REPORT",
    "DATABASE_MIGRATION",
    "DATABASE_RECOVERY",
    "CLEANUP",
    "OTHER",
}
JOB_STATES = {
    "CREATED",
    "QUEUED",
    "CLAIMED",
    "RUNNING",
    "PAUSE_REQUESTED",
    "PAUSED",
    "RETRY_WAIT",
    "SUCCEEDED",
    "FAILED",
    "DEAD_LETTERED",
    "CANCELLED",
}
TERMINAL_STATES = {"SUCCEEDED", "FAILED", "DEAD_LETTERED", "CANCELLED"}
FALSE_TRUTH_FLAGS = {
    "queue_runtime_performed",
    "worker_runtime_performed",
    "retry_scheduler_performed",
    "lock_runtime_performed",
    "automatic_resume_performed",
    "cleanup_runtime_performed",
    "database_connection_performed",
    "persistent_queue_write_performed",
    "state_registry_write_performed",
    "runtime_output_written",
    "external_api_call_performed",
    "ids_business_source_read_performed",
    "raw_metadata_content_accessed",
    "fake_ids_business_data_used",
    "real_ids_business_job_created",
    "production_runtime_activation_performed",
    "github_upload_allowed",
    "app_reinstall_allowed",
}
TRUE_TRUTH_FLAGS = {
    "parameter_values_assigned",
    "backpressure_decision_runtime_performed",
    "actual_disk_observation_performed",
    "isolated_control_metadata_evaluated",
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical_digest(value: Any) -> str:
    try:
        encoded = json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    except (TypeError, ValueError):
        encoded = b"INVALID_NON_JSON_CONTROL_METADATA"
    return hashlib.sha256(encoded).hexdigest()


def _keys_exact(value: Any, expected: set[str]) -> bool:
    return isinstance(value, dict) and set(value) == expected


def _is_nonnegative_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _git_tracked(relative: str) -> bool:
    completed = subprocess.run(
        ["git", "ls-files", "--error-unmatch", "--", relative],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    return completed.returncode == 0


def _repo_relative_ref(value: Any) -> Optional[str]:
    if not isinstance(value, str) or not value.startswith("repo:"):
        return None
    if "\\" in value or len(value) > 512:
        return None
    relative = value[len("repo:") :]
    pure = PurePosixPath(relative)
    normalized = pure.as_posix()
    if (
        pure.is_absolute()
        or ".." in pure.parts
        or not normalized.startswith("KM_IDSystem/")
        or "/users/linzezhang/downloads/ids_metadata" in normalized.lower()
    ):
        return None
    path = REPO_ROOT / normalized
    if not path.is_file() or not _git_tracked(normalized):
        return None
    return normalized


def _refs_valid(values: Any, *, allow_empty: bool = False) -> bool:
    return (
        isinstance(values, list)
        and (allow_empty or bool(values))
        and len(values) <= len(EXPECTED_CONTROL_REFS)
        and all(isinstance(value, str) for value in values)
        and len(values) == len(set(values))
        and all(_repo_relative_ref(value) is not None for value in values)
    )


def _upstream_valid(contract: Mapping[str, Any]) -> bool:
    bindings = contract.get("upstream_bindings")
    if not isinstance(bindings, dict) or set(bindings) != set(EXPECTED_UPSTREAM):
        return False
    for name, (relative, expected_hash) in EXPECTED_UPSTREAM.items():
        binding = bindings.get(name)
        if binding != {"ref": relative, "sha256": expected_hash}:
            return False
        path = REPO_ROOT / relative
        if not path.is_file() or _sha256(path) != expected_hash:
            return False
    return True


def load_contract(path: Path = CONTRACT_PATH) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("Stage040 Phase2 contract must be an object")
    return value


def evaluate_contract(contract: Any) -> dict[str, bool]:
    if not isinstance(contract, dict):
        return {"contract_is_object": False}
    policy = contract.get("policy")
    parameters = policy.get("parameters") if isinstance(policy, dict) else None
    observation = contract.get("observation_contract")
    decisions = contract.get("decision_contract")
    transitions = contract.get("state_transition_contract")
    idempotency = contract.get("idempotency_contract")
    control = contract.get("control_metadata_contract")
    projections = contract.get("human_status_projection")
    ownership = contract.get("ownership_matrix")
    registry = contract.get("registry_binding")
    runtime = contract.get("runtime_boundary")
    rollback = contract.get("rollback")
    truth = contract.get("truth_flags")
    expected_root_keys = {
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
        "upstream_bindings",
        "policy",
        "observation_contract",
        "decision_precedence",
        "decision_contract",
        "state_transition_contract",
        "idempotency_contract",
        "control_metadata_contract",
        "human_status_projection",
        "ownership_matrix",
        "registry_binding",
        "runtime_boundary",
        "rollback",
        "truth_flags",
    }
    expected_decisions = {
        "HEALTHY": ("ADMIT", "NO_POLICY_STATE_MUTATION", "可接收"),
        "QUEUE_SOFT_PRESSURE": (
            "THROTTLE_ADMISSION",
            "NO_LIFECYCLE_MUTATION",
            "限流中",
        ),
        "QUEUE_HARD_CAPACITY": (
            "DENY_NEW_ADMISSION",
            "NO_QUEUE_RECORD_CREATED",
            "暂不接收新任务",
        ),
        "EXTERNAL_DRIVE_OFFLINE": (
            "PAUSE_RESOURCE_GATE",
            "LEGAL_PAUSE_CANDIDATE_ONLY",
            "已暂停",
        ),
        "DISK_SPACE_INSUFFICIENT": (
            "PAUSE_RESOURCE_GATE",
            "LEGAL_PAUSE_CANDIDATE_ONLY",
            "已暂停",
        ),
        "EXTERNAL_API_BUDGET_INSUFFICIENT": (
            "PAUSE_RESOURCE_GATE",
            "LEGAL_PAUSE_CANDIDATE_ONLY",
            "已暂停",
        ),
        "UNKNOWN_OR_STALE_PRESSURE": (
            "REQUIRE_MANUAL_REVIEW",
            "NO_NEW_ADMISSION",
            "等待人工复核",
        ),
    }
    decision_exact = isinstance(decisions, dict) and set(decisions) == set(
        expected_decisions
    )
    if decision_exact:
        decision_exact = all(
            decisions[name]
            == {
                "decision_action": action,
                "state_effect": effect,
                "human_status": label,
            }
            for name, (action, effect, label) in expected_decisions.items()
        )
    return {
        "contract_is_object": True,
        "root_shape_exact": set(contract) == expected_root_keys,
        "identity_exact": (
            contract.get("schema_version") == "ids.stage040.backpressure.phase2.v1"
            and contract.get("stage") == "STAGE-040"
            and contract.get("phase") == "Phase 2"
            and contract.get("task_id") == TASK_ID
            and contract.get("acceptance_id") == ACCEPTANCE_ID
            and contract.get("execution_mode")
            == "ISOLATED_NON_PRODUCTION_BACKPRESSURE_DECISION_SLICE"
            and contract.get("policy_contract_id") == POLICY_VERSION
            and contract.get("contract_state")
            == "PHASE2_ISOLATED_DECISION_SLICE_ENABLED_PRODUCTION_DISABLED"
            and contract.get("next_gate") == "IDS-STAGE040-P3-GATE"
        ),
        "source_binding_exact": contract.get("source_binding") == EXPECTED_SOURCE,
        "upstream_bindings_current": _upstream_valid(contract),
        "parameters_exact_and_bounded": (
            isinstance(policy, dict)
            and parameters == EXPECTED_PARAMETERS
            and policy.get("policy_version") == POLICY_VERSION
            and policy.get("queue_high_watermark_alias")
            == "queue_soft_pressure_threshold"
            and policy.get("parameter_source")
            == "STAGE040_PHASE2_LOCAL_ENGINEERING_SAFETY_BOUNDARY"
            and isinstance(policy.get("selection_rationale"), str)
            and bool(policy.get("selection_rationale"))
            and policy.get("fact_level") == "PROPOSED"
            and policy.get("production_calibrated") is False
            and policy.get("production_calibration_required") is True
            and policy.get("rollback_policy")
            == "DENY_NEW_ADMISSION_REQUIRE_MANUAL_REVIEW"
            and parameters["queue_low_watermark"]
            < parameters["queue_soft_pressure_threshold"]
            < parameters["queue_hard_capacity_threshold"]
            <= 16
            and parameters["disk_reserve_bytes"]
            < parameters["disk_free_bytes_threshold"]
            and parameters["observation_ttl_seconds"]
            < parameters["external_api_budget_window_seconds"]
            and parameters["per_job_type_concurrency_limit"] >= 1
            and parameters["admission_rate_limit_per_window"]
            <= parameters["queue_hard_capacity_threshold"]
        ),
        "observation_contract_exact": (
            isinstance(observation, dict)
            and observation.get("required_fields") == OBSERVATION_FIELD_ORDER
            and set(observation.get("required_fields", [])) == OBSERVATION_FIELDS
            and observation.get("validity_status") == "VALID"
            and observation.get("unknown_or_stale_action")
            == "REQUIRE_MANUAL_REVIEW"
            and observation.get("future_timestamp_allowed") is False
            and observation.get("raw_observation_body_allowed") is False
            and observation.get("external_api_call_required_for_observation") is False
        ),
        "decision_precedence_exact": contract.get("decision_precedence")
        == [
            "INVALID_OR_STALE_OBSERVATION",
            "TERMINAL_STATE_GUARD",
            "EXTERNAL_DRIVE_OFFLINE",
            "DISK_SPACE_INSUFFICIENT",
            "EXTERNAL_API_BUDGET_INSUFFICIENT",
            "QUEUE_HARD_CAPACITY",
            "ADMISSION_RATE_LIMIT_REACHED",
            "JOB_TYPE_CONCURRENCY_LIMIT_REACHED",
            "QUEUE_SOFT_PRESSURE_OR_HYSTERESIS",
            "HEALTHY",
        ],
        "decision_contract_exact": decision_exact,
        "state_transition_boundary_exact": transitions
        == {
            "state_model_version": "ids.job_state.v1",
            "terminal_states": [
                "SUCCEEDED",
                "FAILED",
                "DEAD_LETTERED",
                "CANCELLED",
            ],
            "terminal_state_mutation_allowed": False,
            "queued_pause_path": ["QUEUED", "PAUSED"],
            "retry_wait_pause_path": ["RETRY_WAIT", "PAUSED"],
            "running_pause_path": ["RUNNING", "PAUSE_REQUESTED", "PAUSED"],
            "claimed_pause_path": ["CLAIMED", "PAUSE_REQUESTED", "PAUSED"],
            "candidate_only": True,
            "persistent_state_write_allowed": False,
        },
        "idempotency_boundary_exact": idempotency
        == {
            "decision_key_formula": (
                "sha256(idempotency_key|policy_version|"
                "canonical_pressure_observation)"
            ),
            "ledger_mode": "IN_MEMORY_DECISION_REPLAY_ONLY",
            "same_decision_returns_original": True,
            "different_observation_creates_distinct_decision_key": True,
            "idempotency_key_rotation_allowed": False,
            "persistent_ledger_allowed": False,
        },
        "control_metadata_exact": (
            isinstance(control, dict)
            and control.get("input_refs") == EXPECTED_CONTROL_REFS
            and control.get("input_refs_must_be_git_tracked") is True
            and control.get("raw_body_allowed") is False
            and control.get("output_refs") == []
            and control.get("checkpoint_ref_format")
            == "checkpoint:sha256:<canonical-decision-digest>"
            and control.get("error_ref_format")
            == "error:<safe-control-reason-code>"
            and control.get("audit_ref")
            == "KM_IDSystem/docs/pursuing_goal/ids_v0_1/"
            "STAGE040_PHASE2_BACKPRESSURE_DECISION_SLICE.md#Controlled-Evidence"
            and all(_repo_relative_ref(ref) is not None for ref in EXPECTED_CONTROL_REFS)
        ),
        "human_status_exact": projections
        == {
            "ADMIT": {
                "label_zh": "可接收",
                "owner_action_zh": "无需操作",
                "owner_attention_required": False,
            },
            "THROTTLE_ADMISSION": {
                "label_zh": "限流中",
                "owner_action_zh": "等待队列降至低水位",
                "owner_attention_required": False,
            },
            "DENY_NEW_ADMISSION": {
                "label_zh": "暂不接收新任务",
                "owner_action_zh": "查看容量与资源状态",
                "owner_attention_required": True,
            },
            "PAUSE_RESOURCE_GATE": {
                "label_zh": "已暂停",
                "owner_action_zh": "恢复资源并完成复核",
                "owner_attention_required": True,
            },
            "REQUEST_SAFE_PAUSE": {
                "label_zh": "暂停中",
                "owner_action_zh": "等待当前安全点",
                "owner_attention_required": True,
            },
            "REQUIRE_MANUAL_REVIEW": {
                "label_zh": "等待人工复核",
                "owner_action_zh": "补齐有效观测或检查任务状态",
                "owner_attention_required": True,
            },
        },
        "ownership_exact": ownership
        == {
            "backpressure_decision_policy": "STAGE-040",
            "queue_and_worker_transport": "STAGE-038",
            "retry_and_dead_letter_policy": "STAGE-039",
            "lock_lease_and_fencing_runtime": "STAGE-041",
            "automatic_resume_runtime": "STAGE-042",
            "crash_recovery_runtime": "STAGE-043",
            "cleanup_execution_runtime": "STAGE-044",
        },
        "registry_binding_exact": registry
        == {
            "model_id": "MOD-009",
            "formula_id": "FORM-009",
            "parameter_ids": [f"PARAM-{number:03d}" for number in range(56, 65)],
            "production_calibration_task_id": PRODUCTION_CALIBRATION_TASK_ID,
        },
        "runtime_boundary_fail_closed": (
            isinstance(runtime, dict)
            and runtime.get("isolated_decision_runtime_allowed") is True
            and runtime.get("actual_project_disk_observation_allowed") is True
            and all(
                runtime.get(key) is False
                for key in (
                    "queue_runtime_allowed",
                    "worker_runtime_allowed",
                    "retry_scheduler_allowed",
                    "lock_runtime_allowed",
                    "automatic_resume_allowed",
                    "cleanup_runtime_allowed",
                    "database_allowed",
                    "persistent_queue_write_allowed",
                    "runtime_output_write_allowed",
                    "external_api_allowed",
                    "raw_metadata_access_allowed",
                    "ids_business_job_allowed",
                    "fake_ids_business_data_allowed",
                    "production_activation_allowed",
                )
            )
        ),
        "rollback_exact": rollback
        == {
            "trigger": (
                "INVALID_CONTRACT_OR_PARAMETER_OR_OBSERVATION_OR_"
                "UPSTREAM_BINDING"
            ),
            "action": (
                "DENY_NEW_ADMISSION_REQUIRE_MANUAL_REVIEW_AND_"
                "REVERT_PHASE2_FILES_ONLY"
            ),
            "preserve_phase1": True,
            "preserve_stage037_stage039": True,
            "preserve_source_and_evidence": True,
            "github_action_allowed": False,
        },
        "truth_flags_exact": (
            isinstance(truth, dict)
            and set(truth) == FALSE_TRUTH_FLAGS | TRUE_TRUTH_FLAGS
            and all(truth.get(key) is False for key in FALSE_TRUTH_FLAGS)
            and all(truth.get(key) is True for key in TRUE_TRUTH_FLAGS)
        ),
    }


def build_control_job(
    input_ref: str,
    *,
    job_type: str = "PARSE",
    job_state: str = "QUEUED",
    priority_ref: str = "P1_HIGH_VALUE_ENGINEERING_DATA",
) -> dict[str, Any]:
    relative = _repo_relative_ref(input_ref)
    if relative is None:
        raise ValueError("control input ref must be a Git-tracked KM_IDSystem file")
    if job_type not in JOB_TYPES or job_state not in JOB_STATES:
        raise ValueError("unsupported control job type or state")
    seed = hashlib.sha256(
        f"{TASK_ID}|{input_ref}|{job_type}".encode("utf-8")
    ).hexdigest()
    return {
        "job_id": f"control:stage040:{seed[:24]}",
        "job_type": job_type,
        "job_state": job_state,
        "state_version": 0,
        "idempotency_key": f"idempotency:stage040:{seed}",
        "priority_ref": priority_ref,
        "input_refs": [input_ref],
        "output_refs": [],
        "error_ref": None,
        "checkpoint_ref": None,
        "audit_ref": (
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/"
            "STAGE040_PHASE2_BACKPRESSURE_DECISION_SLICE.md#Controlled-Evidence"
        ),
        "retry_count": 0,
        "max_retries": 0,
    }


def _job_valid(job: Any) -> bool:
    return (
        _keys_exact(job, JOB_FIELDS)
        and job.get("job_type") in JOB_TYPES
        and job.get("job_state") in JOB_STATES
        and _is_nonnegative_int(job.get("state_version"))
        and isinstance(job.get("job_id"), str)
        and job.get("job_id", "").startswith("control:stage040:")
        and isinstance(job.get("idempotency_key"), str)
        and job.get("idempotency_key", "").startswith("idempotency:stage040:")
        and _refs_valid(job.get("input_refs"))
        and job.get("output_refs") == []
        and job.get("error_ref") is None
        and job.get("checkpoint_ref") is None
        and job.get("retry_count") == 0
        and job.get("max_retries") == 0
    )


def _observation_valid(
    observation: Any,
    parameters: Mapping[str, int],
    *,
    now_epoch_seconds: int,
) -> bool:
    if not _keys_exact(observation, OBSERVATION_FIELDS):
        return False
    integer_fields = (
        "observed_at_epoch_seconds",
        "queue_depth",
        "active_job_type_count",
        "admissions_in_window",
        "disk_free_bytes",
        "external_api_units_required",
        "external_api_budget_remaining_units",
        "external_api_budget_window_seconds",
    )
    if any(not _is_nonnegative_int(observation.get(key)) for key in integer_fields):
        return False
    if (
        not isinstance(observation.get("external_drive_required"), bool)
        or not isinstance(observation.get("previous_queue_throttled"), bool)
    ):
        return False
    drive_available = observation.get("external_drive_available")
    if observation["external_drive_required"]:
        if not isinstance(drive_available, bool):
            return False
    elif drive_available is not None and not isinstance(drive_available, bool):
        return False
    if observation.get("validity_status") != "VALID":
        return False
    if observation.get("policy_version") != POLICY_VERSION:
        return False
    if (
        observation.get("external_api_budget_window_seconds")
        != parameters["external_api_budget_window_seconds"]
    ):
        return False
    age = now_epoch_seconds - observation["observed_at_epoch_seconds"]
    if age < 0 or age > parameters["observation_ttl_seconds"]:
        return False
    queued_refs = observation.get("queued_input_refs")
    if not _refs_valid(queued_refs, allow_empty=True):
        return False
    if observation["queue_depth"] != len(queued_refs):
        return False
    if not _refs_valid(observation.get("source_refs")):
        return False
    return True


def _projection(
    contract: Mapping[str, Any], action: str, *, active_pause: bool = False
) -> dict[str, Any]:
    key = "REQUEST_SAFE_PAUSE" if active_pause else action
    value = contract.get("human_status_projection", {}).get(key)
    if not isinstance(value, dict):
        return {
            "label_zh": "等待人工复核",
            "owner_action_zh": "检查策略合同",
            "owner_attention_required": True,
        }
    return copy.deepcopy(value)


def _pause_candidate(
    job_state: str, signal: str
) -> tuple[str, Optional[str], Optional[list[str]]]:
    if job_state == "QUEUED":
        return "RESOURCE_GATE_BLOCKED", "PAUSED", ["QUEUED", "PAUSED"]
    if job_state == "RETRY_WAIT":
        return "RESOURCE_GATE_BLOCKED", "PAUSED", ["RETRY_WAIT", "PAUSED"]
    if job_state == "RUNNING":
        return (
            "SAFE_PAUSE_REQUESTED",
            "PAUSE_REQUESTED",
            ["RUNNING", "PAUSE_REQUESTED", "PAUSED"],
        )
    if job_state == "CLAIMED":
        return (
            "SAFE_PAUSE_REQUESTED",
            "PAUSE_REQUESTED",
            ["CLAIMED", "PAUSE_REQUESTED", "PAUSED"],
        )
    return f"STATE_NOT_PAUSABLE_FOR_{signal}", None, None


class IsolatedDecisionLedger:
    """Memory-only replay ledger; it creates no queue, job, or durable record."""

    def __init__(self) -> None:
        self._entries: dict[str, dict[str, Any]] = {}

    @property
    def entry_count(self) -> int:
        return len(self._entries)

    def get(self, decision_key: str) -> Optional[dict[str, Any]]:
        value = self._entries.get(decision_key)
        return copy.deepcopy(value) if value is not None else None

    def store(self, decision_key: str, decision: Mapping[str, Any]) -> None:
        self._entries[decision_key] = copy.deepcopy(dict(decision))


def _decision_result(
    job: Mapping[str, Any],
    observation: Mapping[str, Any],
    contract: Mapping[str, Any],
    *,
    signal_code: str,
    reason_code: str,
    decision_action: str,
    state_effect: str,
    requested_state: Optional[str] = None,
    state_path: Optional[list[str]] = None,
) -> dict[str, Any]:
    observation_digest = _canonical_digest(observation)
    decision_key = hashlib.sha256(
        (
            f"{job.get('idempotency_key')}|{POLICY_VERSION}|"
            f"{observation_digest}"
        ).encode("utf-8")
    ).hexdigest()
    active_pause = requested_state == "PAUSE_REQUESTED"
    error_ref = None if signal_code == "HEALTHY" else f"error:{reason_code}"
    return {
        "schema_version": "ids.stage040.backpressure.decision.v1",
        "job_id": job.get("job_id"),
        "job_type": job.get("job_type"),
        "policy_version": POLICY_VERSION,
        "decision_key": decision_key,
        "signal_code": signal_code,
        "reason_code": reason_code,
        "decision_action": decision_action,
        "state_effect": state_effect,
        "machine_state_before": job.get("job_state"),
        "requested_state": requested_state,
        "candidate_state_version": (
            job.get("state_version", 0) + 1 if requested_state is not None else None
        ),
        "state_path": copy.deepcopy(state_path),
        "retry_budget_consumed": False,
        "job_created": False,
        "automatic_resume_allowed": False,
        "idempotency_key": job.get("idempotency_key"),
        "idempotent_replay": False,
        "human_status": _projection(
            contract,
            decision_action,
            active_pause=active_pause,
        ),
        "input_refs": copy.deepcopy(job.get("input_refs", [])),
        "output_refs": [],
        "error_ref": error_ref,
        "checkpoint_ref": f"checkpoint:sha256:{decision_key}",
        "audit_ref": job.get("audit_ref"),
        "observed_at_epoch_seconds": (
            observation.get("observed_at_epoch_seconds")
            if _is_nonnegative_int(observation.get("observed_at_epoch_seconds"))
            else None
        ),
    }


def evaluate_backpressure(
    job: Any,
    observation: Any,
    *,
    contract: Optional[Mapping[str, Any]] = None,
    ledger: Optional[IsolatedDecisionLedger] = None,
    now_epoch_seconds: Optional[int] = None,
) -> dict[str, Any]:
    contract_value = dict(contract) if isinstance(contract, Mapping) else load_contract()
    now = int(time.time()) if now_epoch_seconds is None else now_epoch_seconds
    parameters = contract_value.get("policy", {}).get("parameters", {})
    safe_job = job if isinstance(job, dict) else {}
    safe_observation = observation if isinstance(observation, dict) else {}
    contract_checks = evaluate_contract(contract_value)
    job_valid = _job_valid(safe_job)
    if not all(contract_checks.values()) or not job_valid:
        result = _decision_result(
            safe_job if job_valid else {},
            safe_observation,
            contract_value,
            signal_code="UNKNOWN_OR_STALE_PRESSURE",
            reason_code="INVALID_CONTRACT_OR_JOB",
            decision_action="REQUIRE_MANUAL_REVIEW",
            state_effect="NO_NEW_ADMISSION",
        )
    elif not _observation_valid(
        safe_observation,
        parameters,
        now_epoch_seconds=now,
    ):
        result = _decision_result(
            safe_job,
            safe_observation,
            contract_value,
            signal_code="UNKNOWN_OR_STALE_PRESSURE",
            reason_code="INVALID_PRESSURE_OBSERVATION",
            decision_action="REQUIRE_MANUAL_REVIEW",
            state_effect="NO_NEW_ADMISSION",
        )
    elif safe_job["job_state"] in TERMINAL_STATES:
        result = _decision_result(
            safe_job,
            safe_observation,
            contract_value,
            signal_code="UNKNOWN_OR_STALE_PRESSURE",
            reason_code="TERMINAL_STATE_IMMUTABLE",
            decision_action="REQUIRE_MANUAL_REVIEW",
            state_effect="NO_TERMINAL_STATE_MUTATION",
        )
    else:
        signal = "HEALTHY"
        reason = "ALL_PRESSURE_GATES_PASS"
        action = "ADMIT"
        effect = "NO_POLICY_STATE_MUTATION"
        requested_state: Optional[str] = None
        state_path: Optional[list[str]] = None
        if (
            safe_observation["external_drive_required"]
            and safe_observation["external_drive_available"] is False
        ):
            signal = "EXTERNAL_DRIVE_OFFLINE"
        else:
            usable_free = max(
                0,
                safe_observation["disk_free_bytes"]
                - parameters["disk_reserve_bytes"],
            )
            if usable_free < parameters["disk_free_bytes_threshold"]:
                signal = "DISK_SPACE_INSUFFICIENT"
            elif (
                safe_observation["external_api_units_required"]
                > safe_observation["external_api_budget_remaining_units"]
            ):
                signal = "EXTERNAL_API_BUDGET_INSUFFICIENT"
        if signal in {
            "EXTERNAL_DRIVE_OFFLINE",
            "DISK_SPACE_INSUFFICIENT",
            "EXTERNAL_API_BUDGET_INSUFFICIENT",
        }:
            reason, requested_state, state_path = _pause_candidate(
                safe_job["job_state"], signal
            )
            if requested_state is None:
                signal = "UNKNOWN_OR_STALE_PRESSURE"
                action = "REQUIRE_MANUAL_REVIEW"
                effect = "NO_NEW_ADMISSION"
            else:
                action = "PAUSE_RESOURCE_GATE"
                effect = "LEGAL_PAUSE_CANDIDATE_ONLY"
        elif safe_observation["queue_depth"] >= parameters[
            "queue_hard_capacity_threshold"
        ]:
            signal = "QUEUE_HARD_CAPACITY"
            reason = "QUEUE_HARD_CAPACITY_REACHED"
            action = "DENY_NEW_ADMISSION"
            effect = "NO_QUEUE_RECORD_CREATED"
        elif safe_observation["admissions_in_window"] >= parameters[
            "admission_rate_limit_per_window"
        ]:
            signal = "QUEUE_SOFT_PRESSURE"
            reason = "ADMISSION_RATE_LIMIT_REACHED"
            action = "THROTTLE_ADMISSION"
            effect = "NO_LIFECYCLE_MUTATION"
        elif safe_observation["active_job_type_count"] >= parameters[
            "per_job_type_concurrency_limit"
        ]:
            signal = "QUEUE_SOFT_PRESSURE"
            reason = "JOB_TYPE_CONCURRENCY_LIMIT_REACHED"
            action = "THROTTLE_ADMISSION"
            effect = "NO_LIFECYCLE_MUTATION"
        elif (
            safe_observation["queue_depth"]
            >= parameters["queue_soft_pressure_threshold"]
            or (
                safe_observation["previous_queue_throttled"]
                and safe_observation["queue_depth"]
                > parameters["queue_low_watermark"]
            )
        ):
            signal = "QUEUE_SOFT_PRESSURE"
            reason = "QUEUE_SOFT_PRESSURE_REACHED"
            action = "THROTTLE_ADMISSION"
            effect = "NO_LIFECYCLE_MUTATION"
        result = _decision_result(
            safe_job,
            safe_observation,
            contract_value,
            signal_code=signal,
            reason_code=reason,
            decision_action=action,
            state_effect=effect,
            requested_state=requested_state,
            state_path=state_path,
        )
    if ledger is not None:
        replay = ledger.get(result["decision_key"])
        if replay is not None:
            replay["idempotent_replay"] = True
            return replay
        ledger.store(result["decision_key"], result)
    return result


def _actual_observation(
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
    return {
        "observed_at_epoch_seconds": now,
        "queue_depth": queue_depth,
        "queued_input_refs": copy.deepcopy(queued_input_refs or []),
        "active_job_type_count": active_job_type_count,
        "admissions_in_window": admissions_in_window,
        "disk_free_bytes": disk_free_bytes,
        "external_drive_required": False,
        "external_drive_available": None,
        "external_api_units_required": api_required,
        "external_api_budget_remaining_units": api_remaining,
        "external_api_budget_window_seconds": 60,
        "previous_queue_throttled": False,
        "validity_status": "VALID",
        "source_refs": [EXPECTED_CONTROL_REFS[0]],
        "policy_version": POLICY_VERSION,
    }


def build_stage040_phase2_report(
    contract: Optional[Mapping[str, Any]] = None,
) -> dict[str, Any]:
    try:
        contract_value = (
            copy.deepcopy(dict(contract))
            if isinstance(contract, Mapping)
            else load_contract()
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        contract_value = {}
        load_error = f"{type(exc).__name__}: {exc}"
    else:
        load_error = None
    contract_checks = evaluate_contract(contract_value)
    contract_valid = bool(contract_checks) and all(contract_checks.values())
    actual_disk_free = shutil.disk_usage(PROJECT_ROOT).free
    now = int(time.time())
    if contract_valid:
        job = build_control_job(EXPECTED_CONTROL_REFS[0])
        running_job = build_control_job(
            EXPECTED_CONTROL_REFS[0], job_state="RUNNING"
        )
        actual = evaluate_backpressure(
            job,
            _actual_observation(now=now, disk_free_bytes=actual_disk_free),
            contract=contract_value,
            now_epoch_seconds=now,
        )
        soft_observation = _actual_observation(
            now=now,
            disk_free_bytes=actual_disk_free,
            queue_depth=2,
            queued_input_refs=EXPECTED_CONTROL_REFS[:2],
        )
        soft = evaluate_backpressure(
            job,
            soft_observation,
            contract=contract_value,
            now_epoch_seconds=now,
        )
        hard = evaluate_backpressure(
            job,
            _actual_observation(
                now=now,
                disk_free_bytes=actual_disk_free,
                queue_depth=4,
                queued_input_refs=EXPECTED_CONTROL_REFS,
            ),
            contract=contract_value,
            now_epoch_seconds=now,
        )
        api = evaluate_backpressure(
            running_job,
            _actual_observation(
                now=now,
                disk_free_bytes=actual_disk_free,
                api_required=1,
                api_remaining=0,
            ),
            contract=contract_value,
            now_epoch_seconds=now,
        )
        ledger = IsolatedDecisionLedger()
        first = evaluate_backpressure(
            job,
            soft_observation,
            contract=contract_value,
            ledger=ledger,
            now_epoch_seconds=now,
        )
        replay = evaluate_backpressure(
            job,
            copy.deepcopy(soft_observation),
            contract=contract_value,
            ledger=ledger,
            now_epoch_seconds=now,
        )
        parameters = contract_value["policy"]["parameters"]
        expected_actual_signal = (
            "DISK_SPACE_INSUFFICIENT"
            if max(0, actual_disk_free - parameters["disk_reserve_bytes"])
            < parameters["disk_free_bytes_threshold"]
            else "HEALTHY"
        )
        slice_checks = {
            "tracked_control_refs_exact": all(
                _repo_relative_ref(ref) is not None for ref in EXPECTED_CONTROL_REFS
            ),
            "actual_disk_observation_positive": actual_disk_free > 0,
            "actual_disk_decision_matches_formula": actual.get("signal_code")
            == expected_actual_signal,
            "soft_pressure_throttles": (
                soft.get("signal_code") == "QUEUE_SOFT_PRESSURE"
                and soft.get("decision_action") == "THROTTLE_ADMISSION"
            ),
            "hard_capacity_denies_without_job": (
                hard.get("signal_code") == "QUEUE_HARD_CAPACITY"
                and hard.get("decision_action") == "DENY_NEW_ADMISSION"
                and hard.get("job_created") is False
            ),
            "api_budget_requests_safe_pause": (
                api.get("signal_code")
                == "EXTERNAL_API_BUDGET_INSUFFICIENT"
                and api.get("requested_state") == "PAUSE_REQUESTED"
                and api.get("state_path")
                == ["RUNNING", "PAUSE_REQUESTED", "PAUSED"]
            ),
            "idempotent_replay_exact": (
                first.get("idempotent_replay") is False
                and replay.get("idempotent_replay") is True
                and first.get("decision_key") == replay.get("decision_key")
                and first.get("checkpoint_ref") == replay.get("checkpoint_ref")
                and ledger.entry_count == 1
            ),
            "bounded_refs_and_no_output": (
                soft.get("input_refs") == [EXPECTED_CONTROL_REFS[0]]
                and soft.get("output_refs") == []
                and isinstance(soft.get("checkpoint_ref"), str)
                and soft.get("checkpoint_ref", "").startswith("checkpoint:sha256:")
            ),
        }
    else:
        actual = {}
        soft = {}
        hard = {}
        api = {}
        replay = {}
        slice_checks = {"contract_required_before_slice": False}
    truth = contract_value.get("truth_flags", {})
    slice_valid = contract_valid and all(slice_checks.values())
    return {
        "schema_version": "ids.stage040.backpressure.phase2.report.v1",
        "stage": "STAGE-040",
        "phase": "Phase 2",
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "policy_version": POLICY_VERSION,
        "contract_valid": contract_valid,
        "slice_valid": slice_valid,
        "contract_checks": contract_checks,
        "slice_checks": slice_checks,
        "load_error": load_error,
        "execution_mode": (
            contract_value.get("execution_mode")
            if contract_valid
            else "BLOCKED_INVALID_BACKPRESSURE_CONTRACT"
        ),
        "contract_state": (
            contract_value.get("contract_state")
            if contract_valid
            else "BLOCKED_INVALID_BACKPRESSURE_CONTRACT"
        ),
        "next_gate": (
            "IDS-STAGE040-P3-GATE"
            if slice_valid
            else "IDS-STAGE040-P2-GATE"
        ),
        "tracked_control_ref_count": len(EXPECTED_CONTROL_REFS),
        "actual_disk_free_bytes": actual_disk_free,
        "actual_disk_observation_performed": bool(
            truth.get("actual_disk_observation_performed", False)
        ),
        "actual_disk_signal": actual.get("signal_code"),
        "soft_pressure_result": soft.get("decision_action"),
        "hard_capacity_result": hard.get("decision_action"),
        "api_budget_pause_requested_state": api.get("requested_state"),
        "idempotent_replay_proved": replay.get("idempotent_replay") is True,
        **{key: bool(truth.get(key, False)) for key in FALSE_TRUTH_FLAGS},
    }


def main() -> int:
    report = build_stage040_phase2_report()
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if report["slice_valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
