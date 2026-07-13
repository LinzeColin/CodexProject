#!/usr/bin/env python3
"""Validate STAGE-039 Phase 3 retry/dead-letter scenarios."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import time
from typing import Any, Mapping, MutableMapping, Optional


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PROJECT_ROOT.parent
PURSUE_ROOT = PROJECT_ROOT / "docs" / "pursuing_goal" / "ids_v0_1"
CONTRACT_PATH = (
    PURSUE_ROOT
    / "retry_dead_letter"
    / "stage039_retry_dead_letter_scenarios.json"
)
PHASE2_CHECKER = PROJECT_ROOT / "scripts" / "check_retry_dead_letter_runtime.py"
STAGE038_SCENARIO_CHECKER = (
    PROJECT_ROOT / "scripts" / "check_worker_queue_scenarios.py"
)

TASK_ID = "IDS-V0_1-STAGE039-P3"
ACCEPTANCE_ID = "ACC-STAGE-039"
POLICY_VERSION = "ids.retry_policy.v0_1.stage039.p2"
EXECUTION_MODE = "ISOLATED_NON_PRODUCTION_RETRY_DEAD_LETTER_SCENARIOS"
NEXT_GATE = "IDS-STAGE039-P4-GATE"
AUDIT_REF = (
    "KM_IDSystem/docs/pursuing_goal/ids_v0_1/"
    "STAGE039_PHASE3_SCENARIO_VALIDATION.md#Scenario-Evidence"
)

EXPECTED_SCENARIOS = (
    "duplicate_retry_reservation_and_admission",
    "worker_exception_crash_boundary",
    "external_drive_offline_pending_retry_pause",
    "actual_low_disk_pending_retry_pause_without_allocation",
    "external_api_budget_pending_retry_pause",
    "same_source_cross_operation_lock",
    "retry_exhaustion_dead_letter",
    "terminal_replay_blocked",
    "manual_rerun_lineage_idempotent",
    "protected_cleanup_denied",
)
EXPECTED_SCENARIO_RESULTS = {
    "duplicate_retry_reservation_and_admission": (
        "IDEMPOTENT_REPLAY_NO_DOUBLE_BUDGET"
    ),
    "worker_exception_crash_boundary": (
        "WORKER_EXCEPTION_OBSERVED_PROCESS_CRASH_RECOVERY_DEFERRED"
    ),
    "external_drive_offline_pending_retry_pause": "PAUSED_NO_RETRY_BUDGET",
    "actual_low_disk_pending_retry_pause_without_allocation": (
        "PAUSED_NO_ALLOCATION_NO_RETRY_BUDGET"
    ),
    "external_api_budget_pending_retry_pause": (
        "PAUSED_NO_API_CALL_NO_RETRY_BUDGET"
    ),
    "same_source_cross_operation_lock": "ONE_EXECUTION_THREE_RESOURCE_CONFLICTS",
    "retry_exhaustion_dead_letter": "DEAD_LETTERED_AT_RETRY_COUNT_TWO",
    "terminal_replay_blocked": "TERMINAL_STATE_IMMUTABLE",
    "manual_rerun_lineage_idempotent": (
        "NEW_LINKED_CANDIDATE_OWNER_AUTHORIZED_IDEMPOTENT"
    ),
    "protected_cleanup_denied": "ALL_PROTECTED_ARTIFACTS_DENIED_NO_DELETE",
}
EXPECTED_UPSTREAM = {
    "stage039_phase2_contract": (
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
    "stage038_scenario_contract": (
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/worker_queue_baseline/"
        "stage038_worker_queue_scenarios.json",
        "0ec9f1a0de6ec24d64d4108214ea426f9171b15eebdd6c3c60693fade62f2961",
    ),
    "stage038_scenario_checker": (
        "KM_IDSystem/scripts/check_worker_queue_scenarios.py",
        "b7e335039ecf65e4fe91df39e91cddd296296852bd3be8923237b8616db9517c",
    ),
    "stage038_review_artifact": (
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE038_STAGE_REVIEW.md",
        "5bb4cb3382f97ded9228d278c4cfb34fc5f0a65b8858263ed0c9bbd6c035eb04",
    ),
}
EXPECTED_PROTECTED_REFS = {
    "FACT_SOURCE": (
        "repo:KM_IDSystem/docs/pursuing_goal/ids_v0_1/"
        "STAGE039_PHASE1_RETRY_DEAD_LETTER_SCOPE_BOUNDARY.md"
    ),
    "MANIFEST": (
        "repo:KM_IDSystem/docs/pursuing_goal/ids_v0_1/"
        "STAGE026_PHASE2_ARCHIVE_MANIFEST_SLICE.md"
    ),
    "EVIDENCE_LEDGER": (
        "repo:KM_IDSystem/docs/pursuing_goal/ids_v0_1/retry_dead_letter/"
        "stage039_retry_dead_letter_runtime_contract.json"
    ),
    "REPORT_SNAPSHOT": (
        "repo:KM_IDSystem/docs/pursuing_goal/ids_v0_1/"
        "STAGE039_PHASE2_RETRY_DEAD_LETTER_SLICE.md"
    ),
    "AUDIT_LOG": "repo:KM_IDSystem/docs/governance/events.jsonl",
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
    "production_runtime_activation_performed",
    "persistent_queue_write_performed",
    "database_connection_performed",
    "runtime_output_written",
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
    "scenario_contract_id",
    "contract_state",
    "next_gate",
    "source_binding",
    "phase2_commit_binding",
    "upstream_bindings",
    "policy_version",
    "scenario_catalog",
    "scenario_expectations",
    "manual_rerun_contract",
    "physical_action_boundary",
    "protected_artifact_contract",
    "downstream_ownership",
    "human_status_contract",
    "phase4_entry_gate",
    "truth_flags",
}
RERUN_REQUEST_FIELD_ORDER = (
    "parent_job_id",
    "rerun_request_id",
    "owner_authorized",
    "new_job_id",
    "new_idempotency_key",
    "actor_ref",
    "audit_ref",
)
RERUN_REQUEST_FIELDS = set(RERUN_REQUEST_FIELD_ORDER)


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
    return _load_module(PHASE2_CHECKER, "stage039_phase3_phase2")


def _stage038_module() -> Any:
    return _load_module(
        STAGE038_SCENARIO_CHECKER, "stage039_phase3_stage038_scenarios"
    )


def load_scenario_contract() -> dict[str, Any]:
    value = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("STAGE039 Phase 3 scenario contract must be an object")
    return value


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


def _phase2_commit_is_ancestor(value: Any) -> bool:
    if not _keys_exact(value, {"commit", "required_ancestor_of_head"}):
        return False
    if (
        value.get("commit") != "27368f8e42522725dc97c76ea1a90481380d5d24"
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


def validate_scenario_contract(contract: Any) -> dict[str, bool]:
    if not isinstance(contract, dict):
        return {"contract_is_object": False}
    source = contract.get("source_binding")
    manual = contract.get("manual_rerun_contract")
    physical = contract.get("physical_action_boundary")
    protected = contract.get("protected_artifact_contract")
    ownership = contract.get("downstream_ownership")
    human = contract.get("human_status_contract")
    phase4 = contract.get("phase4_entry_gate")
    truth = contract.get("truth_flags")
    return {
        "root_shape_exact": set(contract) == EXPECTED_ROOT_KEYS,
        "identity_exact": (
            contract.get("schema_version")
            == "ids.stage039.retry_dead_letter.phase3.scenarios.v1"
            and contract.get("stage") == "STAGE-039"
            and contract.get("phase") == "Phase 3"
            and contract.get("task_id") == TASK_ID
            and contract.get("acceptance_id") == ACCEPTANCE_ID
            and contract.get("execution_mode") == EXECUTION_MODE
            and contract.get("scenario_contract_id")
            == "ids.retry_dead_letter.v0_1.p3.scenarios"
            and contract.get("contract_state")
            == "PHASE3_SCENARIOS_ENABLED_PRODUCTION_DISABLED"
            and contract.get("next_gate") == NEXT_GATE
            and contract.get("policy_version") == POLICY_VERSION
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
        "phase2_commit_bound": _phase2_commit_is_ancestor(
            contract.get("phase2_commit_binding")
        ),
        "upstream_bindings_exact": _upstream_valid(contract.get("upstream_bindings")),
        "scenario_catalog_exact": contract.get("scenario_catalog")
        == list(EXPECTED_SCENARIOS),
        "scenario_expectations_exact": contract.get("scenario_expectations")
        == EXPECTED_SCENARIO_RESULTS,
        "manual_rerun_fail_closed": (
            _keys_exact(
                manual,
                {
                    "required_terminal_states",
                    "required_request_fields",
                    "idempotency_scope",
                    "new_job_identity_required",
                    "new_idempotency_key_required",
                    "owner_authorization_required",
                    "candidate_only",
                    "job_creation_performed",
                    "database_write_performed",
                    "terminal_reopen_allowed",
                },
            )
            and manual.get("required_terminal_states")
            == ["FAILED", "DEAD_LETTERED", "SUCCEEDED", "CANCELLED"]
            and manual.get("required_request_fields")
            == list(RERUN_REQUEST_FIELD_ORDER)
            and manual.get("idempotency_scope") == "parent_job_id|rerun_request_id"
            and manual.get("new_job_identity_required") is True
            and manual.get("new_idempotency_key_required") is True
            and manual.get("owner_authorization_required") is True
            and manual.get("candidate_only") is True
            and manual.get("job_creation_performed") is False
            and manual.get("database_write_performed") is False
            and manual.get("terminal_reopen_allowed") is False
        ),
        "physical_actions_disabled": (
            _keys_exact(
                physical,
                {
                    "process_termination_allowed",
                    "physical_drive_removal_allowed",
                    "disk_allocation_allowed",
                    "external_api_call_allowed",
                    "cleanup_delete_allowed",
                    "production_runtime_allowed",
                    "worker_exception_in_isolated_stage038_allowed",
                    "actual_disk_free_observation_allowed",
                },
            )
            and all(
                physical.get(key) is False
                for key in (
                    "process_termination_allowed",
                    "physical_drive_removal_allowed",
                    "disk_allocation_allowed",
                    "external_api_call_allowed",
                    "cleanup_delete_allowed",
                    "production_runtime_allowed",
                )
            )
            and physical.get("worker_exception_in_isolated_stage038_allowed") is True
            and physical.get("actual_disk_free_observation_allowed") is True
        ),
        "protected_artifacts_exact": (
            _keys_exact(
                protected,
                {
                    "protected_refs",
                    "all_refs_must_be_git_tracked",
                    "delete_attempt_allowed",
                    "delete_api_call_allowed",
                    "runtime_owner",
                },
            )
            and protected.get("protected_refs") == EXPECTED_PROTECTED_REFS
            and protected.get("all_refs_must_be_git_tracked") is True
            and protected.get("delete_attempt_allowed") is False
            and protected.get("delete_api_call_allowed") is False
            and protected.get("runtime_owner") == "STAGE-044"
        ),
        "downstream_ownership_exact": (
            ownership
            == {
                "measured_backpressure_and_fairness": "STAGE-040",
                "production_lock_lease_and_fencing": "STAGE-041",
                "automatic_resume_and_lifecycle": "STAGE-042",
                "process_crash_recovery": "STAGE-043",
                "cleanup_execution": "STAGE-044",
                "phase3_may_take_downstream_runtime_ownership": False,
            }
        ),
        "human_status_exact": (
            human
            == {
                "PAUSED": "已暂停",
                "FAILED": "处理失败",
                "DEAD_LETTERED": "需要人工处理",
                "manual_rerun_candidate": "已记录人工重跑候选，尚未创建任务",
            }
        ),
        "phase4_gate_exact": (
            phase4
            == {
                "entry_authorized_after_scenario_pass": True,
                "required_task_id": "IDS-V0_1-STAGE039-P4",
                "required_acceptance_id": ACCEPTANCE_ID,
                "must_run_separately": True,
                "whole_stage_review_allowed_in_phase3": False,
                "github_upload_allowed": False,
                "app_reinstall_allowed": False,
                "next_gate": NEXT_GATE,
            }
        ),
        "truth_flags_exact": (
            isinstance(truth, dict)
            and set(truth) == FALSE_TRUTH_FLAGS | {"taskpack_source_read_performed"}
            and truth.get("taskpack_source_read_performed") is True
            and all(truth.get(key) is False for key in FALSE_TRUTH_FLAGS)
        ),
    }


def _canonical_fingerprint(value: Mapping[str, Any]) -> str:
    encoded = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _rerun_reject(result_code: str) -> dict[str, Any]:
    return {
        "accepted": False,
        "result_code": result_code,
        "idempotent_replay": False,
        "rerun_candidate": None,
        "job_created": False,
        "database_write_performed": False,
        "persistent_queue_write_performed": False,
    }


def evaluate_manual_rerun_candidate(
    terminal_snapshot: Mapping[str, Any],
    request: Any,
    *,
    ledger: Optional[MutableMapping[str, Mapping[str, Any]]] = None,
) -> dict[str, Any]:
    if terminal_snapshot.get("job_state") not in {
        "FAILED",
        "DEAD_LETTERED",
        "SUCCEEDED",
        "CANCELLED",
    }:
        return _rerun_reject("SOURCE_JOB_NOT_TERMINAL")
    if not isinstance(request, dict) or set(request) != RERUN_REQUEST_FIELDS:
        return _rerun_reject("INVALID_RERUN_REQUEST")
    if request.get("owner_authorized") is not True:
        return _rerun_reject("OWNER_AUTHORIZATION_REQUIRED")
    if request.get("parent_job_id") != terminal_snapshot.get("job_id"):
        return _rerun_reject("PARENT_JOB_MISMATCH")
    if (
        not isinstance(request.get("rerun_request_id"), str)
        or re.fullmatch(
            r"owner-rerun:[A-Za-z0-9._:-]{1,128}", request["rerun_request_id"]
        )
        is None
        or not isinstance(request.get("new_job_id"), str)
        or re.fullmatch(r"control:stage039:rerun:[0-9a-f]{24}", request["new_job_id"])
        is None
        or request["new_job_id"] == request["parent_job_id"]
        or not isinstance(request.get("new_idempotency_key"), str)
        or re.fullmatch(
            r"idempotency:stage039:rerun:[0-9a-f]{64}",
            request["new_idempotency_key"],
        )
        is None
        or not isinstance(request.get("actor_ref"), str)
        or not request["actor_ref"].startswith("owner:")
        or request.get("audit_ref") != AUDIT_REF
    ):
        return _rerun_reject("INVALID_RERUN_IDENTITY")

    ledger_key = f"{request['parent_job_id']}|{request['rerun_request_id']}"
    fingerprint = _canonical_fingerprint(request)
    if ledger is not None and ledger_key in ledger:
        prior = ledger[ledger_key]
        if prior.get("request_fingerprint_sha256") != fingerprint:
            return _rerun_reject("RERUN_REQUEST_CONFLICT")
        result = copy.deepcopy(dict(prior["result"]))
        result["result_code"] = "EXISTING_RERUN_CANDIDATE"
        result["idempotent_replay"] = True
        return result

    result = {
        "accepted": True,
        "result_code": "RERUN_CANDIDATE_ACCEPTED",
        "idempotent_replay": False,
        "rerun_candidate": {
            "candidate_only": True,
            "parent_job_id": request["parent_job_id"],
            "rerun_request_id": request["rerun_request_id"],
            "new_job_id": request["new_job_id"],
            "new_idempotency_key": request["new_idempotency_key"],
            "proposed_initial_state": "CREATED",
            "actor_ref": request["actor_ref"],
            "audit_ref": request["audit_ref"],
            "persisted": False,
        },
        "job_created": False,
        "database_write_performed": False,
        "persistent_queue_write_performed": False,
        "owner_status": {
            "label_zh": "已记录人工重跑候选，尚未创建任务",
            "owner_attention_required": True,
        },
    }
    if ledger is not None:
        ledger[ledger_key] = {
            "request_fingerprint_sha256": fingerprint,
            "result": copy.deepcopy(result),
        }
    return result


def _repo_path_from_ref(value: str) -> Optional[Path]:
    if not isinstance(value, str) or not value.startswith("repo:KM_IDSystem/"):
        return None
    relative = value.removeprefix("repo:")
    pure = PurePosixPath(relative)
    if pure.is_absolute() or ".." in pure.parts or pure.parts[0] != "KM_IDSystem":
        return None
    return Path(*pure.parts)


def _git_tracked_repo_ref(value: str) -> bool:
    path = _repo_path_from_ref(value)
    if path is None:
        return False
    result = subprocess.run(
        ["git", "ls-files", "--error-unmatch", "--", path.as_posix()],
        cwd=REPO_ROOT,
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return result.returncode == 0


def evaluate_protected_cleanup_candidate(
    artifact_class: str, artifact_ref: str, contract: Mapping[str, Any]
) -> dict[str, Any]:
    expected = contract["protected_artifact_contract"]["protected_refs"].get(
        artifact_class
    )
    git_tracked = _git_tracked_repo_ref(artifact_ref)
    protected = expected == artifact_ref and git_tracked
    return {
        "artifact_class": artifact_class,
        "artifact_ref": artifact_ref,
        "git_tracked": git_tracked,
        "delete_allowed": False,
        "result_code": "PROTECTED_ARTIFACT" if protected else "INVALID_CLEANUP_CANDIDATE",
        "delete_attempted": False,
    }


def _waiting_retry_snapshot(phase2: Any, contract: Mapping[str, Any]) -> dict[str, Any]:
    phase2_contract = phase2.load_runtime_contract()
    context = phase2.build_running_control_context(phase2_contract)
    observation = phase2.build_failure_observation(
        context["snapshot"],
        safe_error_code="TRANSIENT_OPERATION_TIMEOUT",
        observed_at_epoch_seconds=int(time.time()),
    )
    reserved = phase2.evaluate_failure(
        context["snapshot"], observation, contract=phase2_contract
    )
    if reserved.get("accepted") is not True:
        raise RuntimeError("unable to reserve controlled retry")
    return reserved["next_snapshot"]


def _duplicate_retry_scenario(phase2: Any) -> dict[str, Any]:
    phase2_contract = phase2.load_runtime_contract()
    context = phase2.build_running_control_context(phase2_contract)
    observation = phase2.build_failure_observation(
        context["snapshot"],
        safe_error_code="TRANSIENT_DEPENDENCY_UNAVAILABLE",
        observed_at_epoch_seconds=int(time.time()),
    )
    ledger: dict[str, Mapping[str, Any]] = {}
    first = phase2.evaluate_failure(
        context["snapshot"],
        observation,
        contract=phase2_contract,
        prior_results=ledger,
    )
    replay = phase2.evaluate_failure(
        context["snapshot"],
        observation,
        contract=phase2_contract,
        prior_results=ledger,
    )
    waiting = first["next_snapshot"]
    due_at = int(waiting["next_eligible_at"].split(":", 1)[1])
    admission_id = (
        f"acceptance:{ACCEPTANCE_ID}:{waiting['job_id']}:phase3-duplicate-admission"
    )
    admission = phase2.admit_due_retry(
        waiting,
        observed_at_epoch_seconds=due_at,
        transition_request_id=admission_id,
        contract=phase2_contract,
        prior_results=ledger,
    )
    admission_replay = phase2.admit_due_retry(
        waiting,
        observed_at_epoch_seconds=due_at,
        transition_request_id=admission_id,
        contract=phase2_contract,
        prior_results=ledger,
    )
    passed = (
        first.get("accepted") is True
        and replay.get("idempotent_replay") is True
        and replay["next_snapshot"]["retry_count"] == 0
        and admission.get("accepted") is True
        and admission_replay.get("idempotent_replay") is True
        and admission_replay["next_snapshot"]["retry_count"] == 1
        and len(ledger) == 2
    )
    return {
        "status": "PASS" if passed else "FAIL",
        "failure_replay_idempotent": bool(replay.get("idempotent_replay")),
        "admission_replay_idempotent": bool(
            admission_replay.get("idempotent_replay")
        ),
        "retry_count_after_reservation_replay": replay["next_snapshot"][
            "retry_count"
        ],
        "retry_count_after_admission_replay": admission_replay["next_snapshot"][
            "retry_count"
        ],
        "idempotency_ledger_entry_count": len(ledger),
        "database_write_performed": False,
        "persistent_queue_write_performed": False,
    }


def _worker_exception_boundary_scenario(
    phase2: Any, stage038_report: Mapping[str, Any]
) -> dict[str, Any]:
    source = stage038_report["scenario_results"][
        "worker_crash_exception_and_lock_release"
    ]
    phase2_contract = phase2.load_runtime_contract()
    context = phase2.build_running_control_context(phase2_contract)
    observation = phase2.build_failure_observation(
        context["snapshot"],
        safe_error_code="WORKER_PROCESS_LOST",
        observed_at_epoch_seconds=int(time.time()),
    )
    decision = phase2.evaluate_failure(
        context["snapshot"], observation, contract=phase2_contract
    )
    passed = (
        source.get("status") == "PASS"
        and stage038_report.get("actual_worker_exception_performed") is True
        and source.get("process_termination_performed") is False
        and decision.get("accepted") is True
        and decision.get("decision_action") == "REQUIRE_MANUAL_REVIEW"
        and decision["next_snapshot"]["job_state"] == "FAILED"
        and decision["next_snapshot"]["retry_count"] == 0
    )
    return {
        "status": "PASS" if passed else "FAIL",
        "actual_worker_exception_performed": bool(
            stage038_report.get("actual_worker_exception_performed")
        ),
        "process_termination_performed": False,
        "crash_recovery_runtime_performed": False,
        "crash_recovery_owner": "STAGE-043",
        "stage039_decision_action": decision.get("decision_action"),
        "stage039_machine_state": decision.get("next_snapshot", {}).get(
            "job_state"
        ),
        "retry_count": decision.get("next_snapshot", {}).get("retry_count"),
        "stage038_failed_error_ref": source.get("failed_record", {}).get(
            "error_ref"
        ),
    }


def _resource_pause_scenario(
    phase2: Any,
    stage038_source: Mapping[str, Any],
    *,
    pause_reason_code: str,
    physical_action_performed: bool,
) -> dict[str, Any]:
    phase2_contract = phase2.load_runtime_contract()
    waiting = _waiting_retry_snapshot(phase2, phase2_contract)
    decision = phase2.pause_pending_retry(
        waiting,
        pause_reason_code=pause_reason_code,
        transition_request_id=(
            f"acceptance:{ACCEPTANCE_ID}:{waiting['job_id']}:"
            f"phase3-{pause_reason_code}"
        ),
        contract=phase2_contract,
    )
    next_snapshot = decision.get("next_snapshot", {})
    passed = (
        stage038_source.get("status") == "PASS"
        and decision.get("accepted") is True
        and next_snapshot.get("job_state") == "PAUSED"
        and next_snapshot.get("pause_reason_code") == pause_reason_code
        and next_snapshot.get("retry_count") == 0
        and next_snapshot.get("retry_pending") is True
        and next_snapshot.get("retry_disposition") == "eligible"
        and physical_action_performed is False
    )
    result = {
        "status": "PASS" if passed else "FAIL",
        "machine_state": next_snapshot.get("job_state"),
        "pause_reason_code": next_snapshot.get("pause_reason_code"),
        "retry_count": next_snapshot.get("retry_count"),
        "retry_pending": next_snapshot.get("retry_pending"),
        "retry_disposition": next_snapshot.get("retry_disposition"),
        "physical_action_performed": physical_action_performed,
    }
    if "observed_free_bytes" in stage038_source:
        result["observed_free_bytes"] = stage038_source["observed_free_bytes"]
        result["allocation_performed"] = False
    return result


def _same_source_lock_scenario(stage038_report: Mapping[str, Any]) -> dict[str, Any]:
    source = stage038_report["scenario_results"]["same_source_cross_operation_lock"]
    decisions = source.get("decisions", [])
    conflict_count = sum(
        item.get("result_code") == "RESOURCE_CONFLICT_ACTIVE"
        for item in decisions
        if isinstance(item, dict)
    )
    passed = (
        source.get("status") == "PASS"
        and source.get("job_types") == ["ARCHIVE", "PARSE", "INDEX", "REPORT"]
        and source.get("shared_lock_key_count") == 1
        and source.get("record_count") == 1
        and source.get("operation_invocations") == 1
        and conflict_count == 3
    )
    return {
        "status": "PASS" if passed else "FAIL",
        "job_types": copy.deepcopy(source.get("job_types")),
        "shared_lock_key_count": source.get("shared_lock_key_count"),
        "record_count": source.get("record_count"),
        "operation_invocations": source.get("operation_invocations"),
        "resource_conflict_count": conflict_count,
        "production_lock_runtime_performed": False,
        "lock_runtime_owner": "STAGE-041",
    }


def _terminal_snapshot(phase2: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    phase2_contract = phase2.load_runtime_contract()
    context = phase2.build_running_control_context(phase2_contract, retry_count=2)
    observation = phase2.build_failure_observation(
        context["snapshot"],
        safe_error_code="TRANSIENT_OPERATION_TIMEOUT",
        observed_at_epoch_seconds=int(time.time()),
    )
    exhausted = phase2.evaluate_failure(
        context["snapshot"], observation, contract=phase2_contract
    )
    if exhausted.get("accepted") is not True:
        raise RuntimeError("unable to build controlled terminal snapshot")
    return exhausted["next_snapshot"], observation


def _terminal_replay_scenario(
    phase2: Any, terminal_snapshot: Mapping[str, Any], observation: Mapping[str, Any]
) -> dict[str, Any]:
    decision = phase2.evaluate_failure(
        terminal_snapshot,
        observation,
        contract=phase2.load_runtime_contract(),
    )
    passed = (
        decision.get("accepted") is False
        and decision.get("result_code") == "TERMINAL_STATE_IMMUTABLE"
        and decision.get("next_snapshot", {}).get("job_state") == "DEAD_LETTERED"
    )
    return {
        "status": "PASS" if passed else "FAIL",
        "result_code": decision.get("result_code"),
        "preserved_state": decision.get("next_snapshot", {}).get("job_state"),
        "new_job_created": False,
        "terminal_reopen_performed": False,
    }


def _manual_rerun_scenario(terminal_snapshot: Mapping[str, Any]) -> dict[str, Any]:
    parent = str(terminal_snapshot["job_id"])
    rerun_request_id = "owner-rerun:stage039-phase3-001"
    seed = hashlib.sha256(f"{parent}|{rerun_request_id}".encode("utf-8")).hexdigest()
    request = {
        "parent_job_id": parent,
        "rerun_request_id": rerun_request_id,
        "owner_authorized": True,
        "new_job_id": f"control:stage039:rerun:{seed[:24]}",
        "new_idempotency_key": f"idempotency:stage039:rerun:{seed}",
        "actor_ref": "owner:ids-operations",
        "audit_ref": AUDIT_REF,
    }
    ledger: dict[str, Mapping[str, Any]] = {}
    first = evaluate_manual_rerun_candidate(terminal_snapshot, request, ledger=ledger)
    replay = evaluate_manual_rerun_candidate(terminal_snapshot, request, ledger=ledger)
    conflicting = copy.deepcopy(request)
    conflict_seed = hashlib.sha256(f"{seed}|conflict".encode("utf-8")).hexdigest()
    conflicting["new_job_id"] = f"control:stage039:rerun:{conflict_seed[:24]}"
    conflict = evaluate_manual_rerun_candidate(
        terminal_snapshot, conflicting, ledger=ledger
    )
    unauthorized = copy.deepcopy(request)
    unauthorized["rerun_request_id"] = "owner-rerun:stage039-phase3-unauthorized"
    unauthorized["owner_authorized"] = False
    unauthorized_result = evaluate_manual_rerun_candidate(
        terminal_snapshot, unauthorized, ledger=ledger
    )
    candidate = first.get("rerun_candidate") or {}
    passed = (
        first.get("result_code") == "RERUN_CANDIDATE_ACCEPTED"
        and replay.get("result_code") == "EXISTING_RERUN_CANDIDATE"
        and replay.get("idempotent_replay") is True
        and conflict.get("result_code") == "RERUN_REQUEST_CONFLICT"
        and unauthorized_result.get("result_code") == "OWNER_AUTHORIZATION_REQUIRED"
        and candidate.get("new_job_id") != parent
        and candidate.get("candidate_only") is True
        and candidate.get("proposed_initial_state") == "CREATED"
        and "job_state" not in candidate
        and candidate.get("persisted") is False
        and first.get("job_created") is False
        and first.get("database_write_performed") is False
    )
    return {
        "status": "PASS" if passed else "FAIL",
        "first_result_code": first.get("result_code"),
        "replay_result_code": replay.get("result_code"),
        "replay_idempotent": bool(replay.get("idempotent_replay")),
        "conflict_result_code": conflict.get("result_code"),
        "unauthorized_result_code": unauthorized_result.get("result_code"),
        "parent_job_id": parent,
        "new_job_id": candidate.get("new_job_id"),
        "new_idempotency_key": candidate.get("new_idempotency_key"),
        "candidate_only": candidate.get("candidate_only"),
        "proposed_initial_state": candidate.get("proposed_initial_state"),
        "persisted": candidate.get("persisted"),
        "job_created": False,
        "database_write_performed": False,
        "persistent_queue_write_performed": False,
    }


def _protected_cleanup_scenario(contract: Mapping[str, Any]) -> dict[str, Any]:
    refs = contract["protected_artifact_contract"]["protected_refs"]
    results = {
        artifact_class: evaluate_protected_cleanup_candidate(
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
    contract: Mapping[str, Any], stage038_report: Mapping[str, Any]
) -> dict[str, dict[str, Any]]:
    phase2 = _phase2_module()
    stage038_results = stage038_report["scenario_results"]
    terminal_snapshot, terminal_observation = _terminal_snapshot(phase2)
    exhaustion_report = phase2.build_stage039_phase2_report()
    exhaustion_record = exhaustion_report.get("final_record") or {}
    exhaustion_passed = (
        exhaustion_report.get("slice_valid") is True
        and exhaustion_record.get("machine_state") == "DEAD_LETTERED"
        and exhaustion_record.get("retry_count") == 2
        and exhaustion_record.get("retry_pending") is False
    )
    results = {
        "duplicate_retry_reservation_and_admission": _duplicate_retry_scenario(
            phase2
        ),
        "worker_exception_crash_boundary": _worker_exception_boundary_scenario(
            phase2, stage038_report
        ),
        "external_drive_offline_pending_retry_pause": _resource_pause_scenario(
            phase2,
            stage038_results["external_drive_offline_pause_before_queue"],
            pause_reason_code="external_drive_offline",
            physical_action_performed=False,
        ),
        "actual_low_disk_pending_retry_pause_without_allocation": (
            _resource_pause_scenario(
                phase2,
                stage038_results[
                    "actual_low_disk_boundary_pause_without_allocation"
                ],
                pause_reason_code="disk_space_insufficient",
                physical_action_performed=False,
            )
        ),
        "external_api_budget_pending_retry_pause": _resource_pause_scenario(
            phase2,
            stage038_results[
                "external_api_budget_insufficient_pause_before_queue"
            ],
            pause_reason_code="external_api_budget_insufficient",
            physical_action_performed=False,
        ),
        "same_source_cross_operation_lock": _same_source_lock_scenario(
            stage038_report
        ),
        "retry_exhaustion_dead_letter": {
            "status": "PASS" if exhaustion_passed else "FAIL",
            "machine_state": exhaustion_record.get("machine_state"),
            "retry_count": exhaustion_record.get("retry_count"),
            "retry_pending": exhaustion_record.get("retry_pending"),
            "retry_disposition": exhaustion_record.get("retry_disposition"),
            "dead_letter_metadata_transition_performed": bool(
                exhaustion_report.get("dead_letter_metadata_transition_performed")
            ),
        },
        "terminal_replay_blocked": _terminal_replay_scenario(
            phase2, terminal_snapshot, terminal_observation
        ),
        "manual_rerun_lineage_idempotent": _manual_rerun_scenario(
            terminal_snapshot
        ),
        "protected_cleanup_denied": _protected_cleanup_scenario(contract),
    }
    return results


def _blank_report(
    contract: Mapping[str, Any], checks: Mapping[str, bool]
) -> dict[str, Any]:
    return {
        "schema_version": "ids.stage039.retry_dead_letter.phase3.report.v1",
        "stage": "STAGE-039",
        "phase": "Phase 3",
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "execution_mode": EXECUTION_MODE,
        "policy_version": contract.get("policy_version"),
        "contract_checks": dict(checks),
        "contract_valid": bool(checks) and all(checks.values()),
        "scenario_runtime_performed": False,
        "scenario_validation_valid": False,
        "scenario_count": 0,
        "passed_scenario_count": 0,
        "scenario_results": {},
        "scenario_error_type": None,
        "stage038_isolated_queue_runtime_performed": False,
        "actual_worker_exception_performed": False,
        "actual_disk_observation_performed": False,
        "process_termination_performed": False,
        "physical_drive_removal_performed": False,
        "disk_allocation_performed": False,
        "external_api_call_performed": False,
        "cleanup_runtime_performed": False,
        "protected_ref_delete_performed": False,
        "production_runtime_activation_performed": False,
        "persistent_queue_write_performed": False,
        "database_connection_performed": False,
        "runtime_output_written": False,
        "ids_business_source_read_performed": False,
        "raw_metadata_content_accessed": False,
        "fake_ids_business_data_used": False,
        "real_ids_business_job_created": False,
        "github_upload_allowed": False,
        "app_reinstall_allowed": False,
        "owner_feedback_zh": "场景尚未执行；生产运行保持禁用。",
        "next_gate": NEXT_GATE,
    }


def build_stage039_phase3_report(
    *,
    contract: Optional[dict[str, Any]] = None,
    execute_scenarios: bool = True,
) -> dict[str, Any]:
    try:
        contract = copy.deepcopy(contract) if contract is not None else load_scenario_contract()
    except (OSError, ValueError, json.JSONDecodeError):
        contract = {}
    checks = validate_scenario_contract(contract)
    report = _blank_report(contract, checks)
    if not report["contract_valid"] or not execute_scenarios:
        return report

    try:
        stage038_report = _stage038_module().build_stage038_phase3_report()
        if stage038_report.get("scenario_validation_valid") is not True:
            raise RuntimeError("invalid Stage038 scenario prerequisite")
        results = _run_scenarios(contract, stage038_report)
    except Exception as exc:
        report["scenario_error_type"] = type(exc).__name__
        report["owner_feedback_zh"] = "异常场景验证失败；保持停止并进入人工复核。"
        return report

    passed_count = sum(
        result.get("status") == "PASS" for result in results.values()
    )
    scenario_valid = (
        tuple(results) == EXPECTED_SCENARIOS
        and len(results) == 10
        and passed_count == 10
    )
    report.update(
        {
            "scenario_runtime_performed": True,
            "scenario_validation_valid": scenario_valid,
            "scenario_count": len(results),
            "passed_scenario_count": passed_count,
            "scenario_results": results,
            "stage038_isolated_queue_runtime_performed": bool(
                stage038_report.get("isolated_queue_runtime_performed")
            ),
            "actual_worker_exception_performed": bool(
                stage038_report.get("actual_worker_exception_performed")
            ),
            "actual_disk_observation_performed": bool(
                stage038_report.get("actual_disk_observation_performed")
            ),
            "owner_feedback_zh": (
                "重试与死信 Phase 3 十项隔离场景已通过；异常、暂停、锁、"
                "死信、终态和受保护证据均失败关闭，生产运行继续禁用。"
                if scenario_valid
                else "异常场景存在失败；保持停止并进入人工复核。"
            ),
        }
    )
    return report


def main() -> int:
    report = build_stage039_phase3_report()
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0 if report["scenario_validation_valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
