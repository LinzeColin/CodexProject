#!/usr/bin/env python3
"""Fail-closed review gate for IDS v0.1 STAGE-031 through STAGE-040."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
from typing import Any, Mapping, Optional
from zipfile import BadZipFile, ZipFile


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PROJECT_ROOT.parent
PURSUE_ROOT = PROJECT_ROOT / "docs" / "pursuing_goal" / "ids_v0_1"
CONTRACT_PATH = (
    PURSUE_ROOT / "batch_review" / "stage031_040_batch_review_contract.json"
)
REVIEW_PATH = PURSUE_ROOT / "BATCH031_040_REVIEW_GATE.md"
BATCH_PATH = PURSUE_ROOT / "BATCH031_040_UPLOAD_LOCK.yaml"
ROADMAP_PATH = PROJECT_ROOT / "docs" / "governance" / "roadmap.yaml"
EVENTS_PATH = PROJECT_ROOT / "docs" / "governance" / "events.jsonl"
YAML_PARSER_PATH = PURSUE_ROOT / "validate_stage005_governance_regression.py"
STAGE005_TEST_PATH = (
    PURSUE_ROOT / "tests" / "test_stage005_governance_regression.py"
)
CHECKER_PATH = Path(__file__).resolve()

SCHEMA_VERSION = "ids.v0_1.batch031_040.review_contract.v1"
TASK_ID = "IDS-V0_1-BATCH-031-040-REVIEW-GATE"
REVIEW_GATE = TASK_ID
NEXT_GATE = "IDS-V0_1-BATCH-031-040-UPLOAD-GATE"
PASS_RESULT = "PASS_REVIEWED_READY_FOR_UPLOAD_GATE_NO_GITHUB_UPLOAD"
EVENT_ID = "EVT-IDS-V0_1-BATCH031-040-REVIEW-20260714-001"

ROOT_KEYS = {
    "schema_version",
    "batch_id",
    "task_id",
    "stage_range",
    "acceptance_range",
    "source_bindings",
    "stage_reviews",
    "cross_stage_contract",
    "governance_gate",
    "findings",
    "truth_contract",
}
SOURCE_BINDING_KEYS = {
    "taskpack_archive",
    "roadmap",
    "instructions",
    "metadata_path_only_boundary",
}
FILE_BINDING_KEYS = {"path", "sha256"}
METADATA_BINDING_KEYS = {"path", "content_access_allowed"}
STAGE_REVIEW_KEYS = {
    "stage_id",
    "acceptance_id",
    "status",
    "review_status",
    "review_task_id",
    "source_member",
    "source_member_sha256",
    "review_artifact_ref",
    "review_artifact_sha256",
    "checker_ref",
    "test_refs",
}
CROSS_STAGE_KEYS = {
    "state_registry_owner",
    "state_model_version",
    "job_types",
    "job_states",
    "terminal_states",
    "allowed_transition_count",
    "runtime_ownership",
    "production_runtime_allowed",
}
RUNTIME_OWNERSHIP_KEYS = {
    "queue_and_worker_transport",
    "retry_and_dead_letter_policy",
    "backpressure_decision_policy",
    "lock_lease_and_fencing_runtime",
    "automatic_resume_runtime",
    "crash_recovery_runtime",
    "cleanup_execution_runtime",
}
GOVERNANCE_GATE_KEYS = {
    "review_status",
    "reviewed_stage_count",
    "next_gate",
    "push_allowed",
    "github_upload_allowed",
    "app_reinstall_allowed",
    "stage041_started",
    "single_stage_upload_gate_allowed",
}
FINDING_KEYS = {
    "finding_id",
    "severity",
    "status",
    "summary",
    "repair_ref",
}
TRUTH_KEYS = {
    "taskpack_source_read_performed",
    "ids_business_source_read_performed",
    "raw_metadata_content_accessed",
    "fake_ids_business_data_used",
    "production_runtime_activation_performed",
    "database_connection_performed",
    "schema_change_performed",
    "runtime_output_written",
    "github_upload_performed",
    "pull_request_performed",
    "merge_performed",
    "issue_mutation_performed",
    "app_reinstall_performed",
    "stage041_started",
}

EXPECTED_STAGE_IDS = [f"STAGE-{stage:03d}" for stage in range(31, 41)]
EXPECTED_ACCEPTANCE_IDS = [f"ACC-STAGE-{stage:03d}" for stage in range(31, 41)]
EXPECTED_ACCEPTANCE_BY_STAGE = dict(
    zip(EXPECTED_STAGE_IDS, EXPECTED_ACCEPTANCE_IDS)
)
EXPECTED_JOB_TYPES = [
    "IMPORT",
    "ARCHIVE",
    "PARSE",
    "OCR",
    "CHUNK",
    "EMBED",
    "INDEX",
    "REPORT",
]
EXPECTED_JOB_STATES = [
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
]
EXPECTED_TERMINAL_STATES = [
    "SUCCEEDED",
    "FAILED",
    "DEAD_LETTERED",
    "CANCELLED",
]
EXPECTED_RUNTIME_OWNERSHIP = {
    "queue_and_worker_transport": "STAGE-038",
    "retry_and_dead_letter_policy": "STAGE-039",
    "backpressure_decision_policy": "STAGE-040",
    "lock_lease_and_fencing_runtime": "STAGE-041",
    "automatic_resume_runtime": "STAGE-042",
    "crash_recovery_runtime": "STAGE-043",
    "cleanup_execution_runtime": "STAGE-044",
}

STAGE036_INDEX = (
    PURSUE_ROOT
    / "database_quality_constraints"
    / "stage036_database_quality_constraints_index.json"
)
STAGE037_INDEX = (
    PURSUE_ROOT / "job_state_model" / "stage037_job_state_model_index.json"
)
STAGE038_INDEX = (
    PURSUE_ROOT
    / "worker_queue_baseline"
    / "stage038_worker_queue_baseline_index.json"
)
STAGE039_POLICY = (
    PURSUE_ROOT
    / "retry_dead_letter"
    / "stage039_retry_dead_letter_policy_contract.json"
)
STAGE039_RUNTIME = (
    PURSUE_ROOT
    / "retry_dead_letter"
    / "stage039_retry_dead_letter_runtime_contract.json"
)
STAGE039_SCENARIOS = (
    PURSUE_ROOT
    / "retry_dead_letter"
    / "stage039_retry_dead_letter_scenarios.json"
)
STAGE039_DELIVERY = (
    PURSUE_ROOT
    / "retry_dead_letter"
    / "stage039_retry_dead_letter_delivery_contract.json"
)
STAGE040_POLICY = (
    PURSUE_ROOT
    / "backpressure_policy"
    / "stage040_backpressure_policy_contract.json"
)
STAGE040_RUNTIME = (
    PURSUE_ROOT
    / "backpressure_policy"
    / "stage040_backpressure_runtime_contract.json"
)
STAGE040_SCENARIOS = (
    PURSUE_ROOT
    / "backpressure_policy"
    / "stage040_backpressure_scenarios.json"
)
STAGE040_DELIVERY = (
    PURSUE_ROOT
    / "backpressure_policy"
    / "stage040_backpressure_delivery_contract.json"
)


def _as_object(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _as_list(value: Any) -> list[Any]:
    return list(value) if isinstance(value, list) else []


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def load_contract() -> dict[str, Any]:
    return _load_json(CONTRACT_PATH)


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _sha256_file(path: Path) -> Optional[str]:
    try:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for block in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(block)
        return digest.hexdigest()
    except OSError:
        return None


def _repo_path(reference: Any) -> Optional[Path]:
    if not isinstance(reference, str) or not reference.startswith("KM_IDSystem/"):
        return None
    path = (REPO_ROOT / reference).resolve()
    try:
        path.relative_to(PROJECT_ROOT.resolve())
    except ValueError:
        return None
    return path


def _contract_shape_checks(contract: Mapping[str, Any]) -> dict[str, bool]:
    source_bindings = _as_object(contract.get("source_bindings"))
    stage_reviews = _as_list(contract.get("stage_reviews"))
    cross_stage = _as_object(contract.get("cross_stage_contract"))
    governance = _as_object(contract.get("governance_gate"))
    findings = _as_list(contract.get("findings"))
    truth = _as_object(contract.get("truth_contract"))
    return {
        "root_shape_exact": set(contract) == ROOT_KEYS,
        "identity_exact": (
            contract.get("schema_version") == SCHEMA_VERSION
            and contract.get("batch_id") == "IDS-V0_1-BATCH-031-040"
            and contract.get("task_id") == TASK_ID
            and contract.get("stage_range") == "STAGE-031..STAGE-040"
            and contract.get("acceptance_range") == "ACC-STAGE-031..ACC-STAGE-040"
        ),
        "source_binding_shape_exact": (
            set(source_bindings) == SOURCE_BINDING_KEYS
            and all(
                set(_as_object(source_bindings.get(name))) == FILE_BINDING_KEYS
                for name in ("taskpack_archive", "roadmap", "instructions")
            )
            and set(_as_object(source_bindings.get("metadata_path_only_boundary")))
            == METADATA_BINDING_KEYS
        ),
        "stage_review_shapes_exact": (
            len(stage_reviews) == 10
            and all(
                isinstance(item, Mapping) and set(item) == STAGE_REVIEW_KEYS
                for item in stage_reviews
            )
        ),
        "cross_stage_shape_exact": (
            set(cross_stage) == CROSS_STAGE_KEYS
            and set(_as_object(cross_stage.get("runtime_ownership")))
            == RUNTIME_OWNERSHIP_KEYS
        ),
        "governance_shape_exact": set(governance) == GOVERNANCE_GATE_KEYS,
        "finding_shapes_exact": (
            len(findings) == 3
            and all(isinstance(item, Mapping) and set(item) == FINDING_KEYS for item in findings)
        ),
        "truth_shape_exact": set(truth) == TRUTH_KEYS,
    }


def _source_checks(contract: Mapping[str, Any]) -> dict[str, bool]:
    bindings = _as_object(contract.get("source_bindings"))
    archive_binding = _as_object(bindings.get("taskpack_archive"))
    roadmap_binding = _as_object(bindings.get("roadmap"))
    instructions_binding = _as_object(bindings.get("instructions"))
    metadata_binding = _as_object(bindings.get("metadata_path_only_boundary"))
    archive = Path(str(archive_binding.get("path", "")))
    roadmap = Path(str(roadmap_binding.get("path", "")))
    instructions = Path(str(instructions_binding.get("path", "")))
    stage_reviews = _as_list(contract.get("stage_reviews"))

    member_matches: dict[str, int] = {}
    member_hashes: dict[str, Optional[str]] = {}
    member_semantics: dict[str, bool] = {}
    try:
        with ZipFile(archive) as zipped:
            names = zipped.namelist()
            for item in stage_reviews:
                stage = _as_object(item)
                stage_id = str(stage.get("stage_id", ""))
                member = stage.get("source_member")
                count = names.count(member) if isinstance(member, str) else 0
                member_matches[stage_id] = count
                payload = zipped.read(member) if count == 1 else b""
                member_hashes[stage_id] = _sha256_bytes(payload) if payload else None
                try:
                    text = payload.decode("utf-8")
                except UnicodeError:
                    text = ""
                member_semantics[stage_id] = (
                    stage_id in text
                    and str(stage.get("acceptance_id", "")) in text
                    and "## 验收标准" in text
                    and "## 停止条件" in text
                    and "## 回滚方式" in text
                )
    except (OSError, BadZipFile, KeyError, RuntimeError):
        pass

    expected_member_hashes = {
        str(_as_object(item).get("stage_id", "")): _as_object(item).get(
            "source_member_sha256"
        )
        for item in stage_reviews
    }
    return {
        "taskpack_archive_hash": (
            _sha256_file(archive) == archive_binding.get("sha256")
        ),
        "roadmap_hash": _sha256_file(roadmap) == roadmap_binding.get("sha256"),
        "instructions_hash": (
            _sha256_file(instructions) == instructions_binding.get("sha256")
        ),
        "ten_unique_stage_members": (
            set(member_matches) == set(EXPECTED_STAGE_IDS)
            and all(count == 1 for count in member_matches.values())
        ),
        "stage_member_hashes_match": (
            member_hashes == expected_member_hashes
        ),
        "stage_member_semantics_match": (
            set(member_semantics) == set(EXPECTED_STAGE_IDS)
            and all(member_semantics.values())
        ),
        "metadata_boundary_path_only": (
            metadata_binding.get("path")
            == "/Users/linzezhang/Downloads/IDS_MetaData"
            and metadata_binding.get("content_access_allowed") is False
        ),
    }


def _stage_artifact_checks(contract: Mapping[str, Any]) -> dict[str, bool]:
    checks: dict[str, bool] = {}
    for raw in _as_list(contract.get("stage_reviews")):
        item = _as_object(raw)
        stage_id = str(item.get("stage_id", ""))
        review_path = _repo_path(item.get("review_artifact_ref"))
        checker_path = _repo_path(item.get("checker_ref"))
        test_paths = [_repo_path(ref) for ref in _as_list(item.get("test_refs"))]
        try:
            review_text = review_path.read_text(encoding="utf-8") if review_path else ""
        except (OSError, UnicodeError):
            review_text = ""
        checks[stage_id] = bool(
            stage_id in EXPECTED_STAGE_IDS
            and item.get("acceptance_id")
            == EXPECTED_ACCEPTANCE_BY_STAGE.get(stage_id)
            and item.get("status") == "completed_reviewed_local"
            and item.get("review_status") == "passed"
            and review_path
            and _sha256_file(review_path) == item.get("review_artifact_sha256")
            and item.get("review_task_id") in review_text
            and item.get("acceptance_id") in review_text
            and "completed_reviewed_local" in review_text
            and checker_path
            and checker_path.is_file()
            and test_paths
            and all(path is not None and path.is_file() for path in test_paths)
        )
    return checks


def _run_stage_checkers(
    contract: Mapping[str, Any],
    overrides: Optional[Mapping[str, Any]] = None,
) -> dict[str, bool]:
    if overrides is not None:
        return {
            stage_id: overrides.get(stage_id) is True
            for stage_id in EXPECTED_STAGE_IDS
        }

    checks: dict[str, bool] = {}
    for raw in _as_list(contract.get("stage_reviews")):
        item = _as_object(raw)
        stage_id = str(item.get("stage_id", ""))
        checker = _repo_path(item.get("checker_ref"))
        if checker is None or not checker.is_file():
            checks[stage_id] = False
            continue
        try:
            completed = subprocess.run(
                [sys.executable, "-B", str(checker)],
                cwd=REPO_ROOT,
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=120,
            )
            checks[stage_id] = completed.returncode == 0
        except (OSError, subprocess.SubprocessError):
            checks[stage_id] = False
    return checks


def _resolve_hash_ref(reference: Any) -> Optional[Path]:
    if not isinstance(reference, str) or not reference:
        return None
    if reference.startswith("KM_IDSystem/"):
        return _repo_path(reference)
    if reference.startswith("docs/") or reference.startswith("scripts/"):
        path = (PROJECT_ROOT / reference).resolve()
        try:
            path.relative_to(PROJECT_ROOT.resolve())
        except ValueError:
            return None
        return path
    return None


def _binding_group_matches(bindings: Any) -> bool:
    binding_map = _as_object(bindings)
    if not binding_map:
        return False
    for raw in binding_map.values():
        binding = _as_object(raw)
        reference = binding.get("ref", binding.get("path"))
        expected = binding.get("sha256")
        path = _resolve_hash_ref(reference)
        if path is None or not isinstance(expected, str):
            return False
        if _sha256_file(path) != expected:
            return False
    return True


def _cross_stage_checks(contract: Mapping[str, Any]) -> dict[str, bool]:
    expected = _as_object(contract.get("cross_stage_contract"))
    stage036 = _load_json(STAGE036_INDEX)
    stage037 = _load_json(STAGE037_INDEX)
    stage038 = _load_json(STAGE038_INDEX)
    stage039_policy = _load_json(STAGE039_POLICY)
    stage039_runtime = _load_json(STAGE039_RUNTIME)
    stage039_scenarios = _load_json(STAGE039_SCENARIOS)
    stage039_delivery = _load_json(STAGE039_DELIVERY)
    stage040_policy = _load_json(STAGE040_POLICY)
    stage040_runtime = _load_json(STAGE040_RUNTIME)
    stage040_scenarios = _load_json(STAGE040_SCENARIOS)
    stage040_delivery = _load_json(STAGE040_DELIVERY)

    registry = _as_object(stage036.get("versioned_state_registry"))
    state_model = _as_object(stage037.get("state_model"))
    transitions = _as_object(state_model.get("allowed_transitions"))
    transition_count = sum(
        len(targets) for targets in transitions.values() if isinstance(targets, list)
    )
    stage038_contract = _as_object(stage038.get("worker_queue_contract"))
    stage038_truth = _as_object(stage038.get("truth_contract"))
    stage039_inheritance = _as_object(stage039_policy.get("state_model_inheritance"))
    stage040_inheritance = _as_object(stage040_policy.get("state_model_inheritance"))
    stage040_fairness = _as_object(stage040_policy.get("fairness_contract"))
    stage040_ownership = _as_object(stage040_policy.get("ownership_matrix"))

    hash_groups = [
        stage038.get("source_bindings"),
        stage039_policy.get("upstream_bindings"),
        stage039_runtime.get("upstream_bindings"),
        stage039_scenarios.get("upstream_bindings"),
        stage039_delivery.get("upstream_bindings"),
        stage040_policy.get("upstream_bindings"),
        stage040_runtime.get("upstream_bindings"),
        stage040_scenarios.get("upstream_bindings"),
        stage040_delivery.get("upstream_bindings"),
    ]

    return {
        "contract_matches_expected_interface": (
            expected.get("state_registry_owner") == "STAGE-037"
            and expected.get("state_model_version") == "ids.job_state.v1"
            and expected.get("job_types") == EXPECTED_JOB_TYPES
            and expected.get("job_states") == EXPECTED_JOB_STATES
            and expected.get("terminal_states") == EXPECTED_TERMINAL_STATES
            and expected.get("allowed_transition_count") == 21
            and expected.get("runtime_ownership") == EXPECTED_RUNTIME_OWNERSHIP
            and expected.get("production_runtime_allowed") is False
        ),
        "stage036_reserves_state_values_for_stage037": (
            registry.get("state_values_owner") == "STAGE-037"
            and registry.get("populated") is False
            and registry.get("state_values_defined") is False
            and registry.get("runtime_registry_write_allowed") is False
        ),
        "stage037_state_model_exact": (
            state_model.get("state_model_version") == "ids.job_state.v1"
            and state_model.get("job_types") == EXPECTED_JOB_TYPES
            and state_model.get("job_states") == EXPECTED_JOB_STATES
            and state_model.get("terminal_states") == EXPECTED_TERMINAL_STATES
            and transition_count == 21
            and state_model.get("terminal_state_mutation_allowed") is False
        ),
        "stage038_inherits_state_model_without_production_persistence": (
            stage038_contract.get("job_state_model_version") == "ids.job_state.v1"
            and stage038_contract.get("state_transition_owner") == "STAGE-037"
            and stage038_truth.get("production_runtime_activation_performed")
            is False
            and stage038_truth.get("persistent_queue_write_performed") is False
            and stage038_truth.get("database_connection_performed") is False
        ),
        "stage039_retry_paths_preserve_terminal_immutability": (
            stage039_inheritance.get("state_model_version") == "ids.job_state.v1"
            and stage039_inheritance.get("terminal_states")
            == EXPECTED_TERMINAL_STATES
            and stage039_inheritance.get("terminal_state_mutation_allowed") is False
            and stage039_inheritance.get("retryable_failure_path")
            == ["RUNNING", "RETRY_WAIT"]
            and stage039_inheritance.get("exhaustion_path")
            == ["RETRY_WAIT", "DEAD_LETTERED"]
        ),
        "stage040_pause_and_fairness_claims_are_bounded": (
            stage040_inheritance.get("state_model_version") == "ids.job_state.v1"
            and stage040_inheritance.get("terminal_state_mutation_allowed") is False
            and stage040_inheritance.get("active_job_pause_requires_safe_point")
            is True
            and stage040_fairness.get("starvation_prevention_proved") is False
            and stage040_fairness.get("scheduler_algorithm")
            == "NOT_IMPLEMENTED_IN_STAGE040"
        ),
        "stage041_044_runtime_ownership_remains_deferred": (
            stage040_ownership.get("lock_lease_and_fencing_runtime") == "STAGE-041"
            and stage040_ownership.get("automatic_resume_runtime") == "STAGE-042"
            and stage040_ownership.get("crash_recovery_runtime") == "STAGE-043"
            and stage040_ownership.get("cleanup_execution_runtime") == "STAGE-044"
        ),
        "all_upstream_hash_bindings_match": (
            bool(hash_groups) and all(_binding_group_matches(group) for group in hash_groups)
        ),
    }


_YAML_MODULE: Any = None


def _yaml_module() -> Any:
    global _YAML_MODULE
    if _YAML_MODULE is None:
        spec = importlib.util.spec_from_file_location(
            "batch031_040_yaml_parser", YAML_PARSER_PATH
        )
        if spec is None or spec.loader is None:
            raise RuntimeError("Stage005 YAML parser is unavailable")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        _YAML_MODULE = module
    return _YAML_MODULE


def _parse_yaml(path: Path) -> dict[str, Any]:
    try:
        value = _yaml_module()._parse_yaml_text(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, RuntimeError, AttributeError):
        return {}
    return value if isinstance(value, dict) else {}


def _find_by_id(items: Any, key: str, identifier: str) -> dict[str, Any]:
    for item in _as_list(items):
        candidate = _as_object(item)
        if candidate.get(key) == identifier:
            return candidate
    return {}


def _parse_events() -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    try:
        lines = EVENTS_PATH.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError):
        return []
    for line in lines:
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            return []
        if not isinstance(value, dict):
            return []
        events.append(value)
    return events


def _governance_checks(contract: Mapping[str, Any]) -> dict[str, bool]:
    expected = _as_object(contract.get("governance_gate"))
    batch = _parse_yaml(BATCH_PATH)
    roadmap = _parse_yaml(ROADMAP_PATH)
    stage_progress = _as_object(batch.get("stage_progress"))
    upload_gate = _as_object(batch.get("upload_gate"))
    decision = _as_object(batch.get("decision"))
    stages = _as_list(roadmap.get("stages"))
    stage040 = _find_by_id(stages, "stage_id", "IDS-STAGE040")
    batch_phase = _find_by_id(
        stage040.get("phases"), "phase_id", TASK_ID
    )
    events = [event for event in _parse_events() if event.get("event_id") == EVENT_ID]
    event = events[0] if len(events) == 1 else {}
    event_acceptance = event.get("acceptance_ids")

    stage_nodes_valid = all(
        _as_object(stage_progress.get(stage_id)).get("status")
        == "completed_reviewed_local"
        and _as_object(stage_progress.get(stage_id)).get("review_status") == "passed"
        and _as_object(stage_progress.get(stage_id)).get("acceptance_id")
        == acceptance_id
        and _as_object(stage_progress.get(stage_id)).get("acceptance_status")
        == "reviewed_local_passed"
        for stage_id, acceptance_id in zip(
            EXPECTED_STAGE_IDS, EXPECTED_ACCEPTANCE_IDS
        )
    )
    return {
        "contract_gate_truth_exact": (
            expected.get("review_status")
            == "reviewed_ready_for_upload_no_github_upload"
            and expected.get("reviewed_stage_count") == 10
            and expected.get("next_gate") == NEXT_GATE
            and expected.get("push_allowed") is False
            and expected.get("github_upload_allowed") is False
            and expected.get("app_reinstall_allowed") is False
            and expected.get("stage041_started") is False
            and expected.get("single_stage_upload_gate_allowed") is False
        ),
        "batch_state_reviewed_no_upload": (
            batch.get("batch_id") == "IDS-V0_1-BATCH-031-040"
            and batch.get("status")
            == "reviewed_ready_for_upload_no_github_upload"
            and batch.get("review_task_id") == TASK_ID
            and batch.get("review_evidence_ref")
            == "KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH031_040_REVIEW_GATE.md"
            and upload_gate.get("push_allowed") is False
            and upload_gate.get("review_gate") == "BATCH031_040_REVIEW_GATE"
            and upload_gate.get("gate_task_id") == NEXT_GATE
        ),
        "all_ten_stage_nodes_reviewed": stage_nodes_valid,
        "batch_decision_routes_only_to_upload_gate": (
            decision.get("current_task_id") == TASK_ID
            and decision.get("next_allowed_task_id") == NEXT_GATE
            and decision.get("github_upload_allowed") is False
        ),
        "roadmap_routes_only_to_upload_gate": (
            roadmap.get("current_stage_id") == "IDS-STAGE040"
            and roadmap.get("current_phase_id") == TASK_ID
            and roadmap.get("current_task_id") == TASK_ID
            and roadmap.get("next_gate_id") == NEXT_GATE
            and batch_phase.get("status") == "completed"
        ),
        "batch_review_event_exact": (
            len(events) == 1
            and event.get("event_type") == "batch_review"
            and event.get("task_id") == TASK_ID
            and event_acceptance == EXPECTED_ACCEPTANCE_IDS
            and event.get("fact_level") == "VERIFIED"
        ),
    }


def _git_path_check(path: Path, arguments: list[str]) -> bool:
    try:
        relative = path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return False
    try:
        completed = subprocess.run(
            ["git", "-C", str(REPO_ROOT), *arguments, "--", relative],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return completed.returncode == 0


def _source_binding_checks(contract: Mapping[str, Any]) -> dict[str, bool]:
    paths = {
        CONTRACT_PATH,
        REVIEW_PATH,
        CHECKER_PATH,
        BATCH_PATH,
        ROADMAP_PATH,
        EVENTS_PATH,
        YAML_PARSER_PATH,
        STAGE005_TEST_PATH,
    }
    for raw in _as_list(contract.get("stage_reviews")):
        item = _as_object(raw)
        for reference in (
            item.get("review_artifact_ref"),
            item.get("checker_ref"),
            *_as_list(item.get("test_refs")),
        ):
            path = _repo_path(reference)
            if path is not None:
                paths.add(path)
    tracked = {
        path.relative_to(REPO_ROOT).as_posix(): (
            path.is_file()
            and _git_path_check(path, ["ls-files", "--error-unmatch"])
        )
        for path in sorted(paths)
    }
    index_matches = {
        name: tracked[name]
        and _git_path_check(REPO_ROOT / name, ["diff", "--quiet"])
        for name in tracked
    }
    return {
        "all_review_sources_git_tracked": bool(tracked) and all(tracked.values()),
        "all_review_sources_match_git_index": bool(index_matches)
        and all(index_matches.values()),
    }


def _finding_checks(contract: Mapping[str, Any]) -> dict[str, bool]:
    findings = {
        item.get("finding_id"): item
        for item in _as_list(contract.get("findings"))
        if isinstance(item, Mapping)
    }
    return {
        "finding_ids_exact": set(findings)
        == {
            "BATCH031-040-REVIEW-F1",
            "BATCH031-040-REVIEW-F2",
            "BATCH031-040-REVIEW-F3",
        },
        "finding_severities_exact": (
            _as_object(findings.get("BATCH031-040-REVIEW-F1")).get("severity")
            == "Critical"
            and _as_object(findings.get("BATCH031-040-REVIEW-F2")).get(
                "severity"
            )
            == "Important"
            and _as_object(findings.get("BATCH031-040-REVIEW-F3")).get(
                "severity"
            )
            == "Important"
        ),
        "all_findings_repaired": bool(findings)
        and all(_as_object(item).get("status") == "repaired" for item in findings.values()),
        "all_repair_refs_exist": bool(findings)
        and all(
            (path := _repo_path(_as_object(item).get("repair_ref"))) is not None
            and path.is_file()
            for item in findings.values()
        ),
    }


def _truth_checks(contract: Mapping[str, Any]) -> dict[str, bool]:
    truth = _as_object(contract.get("truth_contract"))
    return {
        "taskpack_source_read_only": (
            truth.get("taskpack_source_read_performed") is True
            and truth.get("ids_business_source_read_performed") is False
        ),
        "raw_metadata_not_accessed": truth.get("raw_metadata_content_accessed")
        is False,
        "fake_ids_business_data_not_used": truth.get("fake_ids_business_data_used")
        is False,
        "no_runtime_or_database_side_effect": (
            truth.get("production_runtime_activation_performed") is False
            and truth.get("database_connection_performed") is False
            and truth.get("schema_change_performed") is False
            and truth.get("runtime_output_written") is False
        ),
        "no_github_or_app_action": (
            truth.get("github_upload_performed") is False
            and truth.get("pull_request_performed") is False
            and truth.get("merge_performed") is False
            and truth.get("issue_mutation_performed") is False
            and truth.get("app_reinstall_performed") is False
            and truth.get("stage041_started") is False
        ),
    }


def build_batch031_040_review_report(
    *,
    contract: Optional[Mapping[str, Any]] = None,
    stage_result_overrides: Optional[Mapping[str, Any]] = None,
) -> dict[str, Any]:
    effective = load_contract() if contract is None else dict(contract)
    shape_checks = _contract_shape_checks(effective)
    shape_valid = bool(shape_checks) and all(shape_checks.values())
    source_checks = _source_checks(effective) if shape_valid else {"contract_shape_valid": False}
    artifact_checks = (
        _stage_artifact_checks(effective)
        if shape_valid
        else {stage_id: False for stage_id in EXPECTED_STAGE_IDS}
    )
    checker_checks = (
        _run_stage_checkers(effective, stage_result_overrides)
        if shape_valid
        else {stage_id: False for stage_id in EXPECTED_STAGE_IDS}
    )
    stage_checks = {
        stage_id: artifact_checks.get(stage_id) is True
        and checker_checks.get(stage_id) is True
        for stage_id in EXPECTED_STAGE_IDS
    }
    cross_stage_checks = (
        _cross_stage_checks(effective)
        if shape_valid
        else {"contract_shape_valid": False}
    )
    governance_checks = (
        _governance_checks(effective)
        if shape_valid
        else {"contract_shape_valid": False}
    )
    source_binding_checks = (
        _source_binding_checks(effective)
        if shape_valid
        else {"contract_shape_valid": False}
    )
    finding_checks = (
        _finding_checks(effective)
        if shape_valid
        else {"contract_shape_valid": False}
    )
    truth_checks = (
        _truth_checks(effective)
        if shape_valid
        else {"contract_shape_valid": False}
    )
    groups = (
        shape_checks,
        source_checks,
        stage_checks,
        cross_stage_checks,
        governance_checks,
        source_binding_checks,
        finding_checks,
        truth_checks,
    )
    review_valid = all(bool(group) and all(value is True for value in group.values()) for group in groups)
    reviewed_stage_count = sum(value is True for value in stage_checks.values())
    return {
        "schema_version": "ids.v0_1.batch031_040.review_report.v1",
        "batch_id": "IDS-V0_1-BATCH-031-040",
        "task_id": TASK_ID,
        "acceptance_ids": EXPECTED_ACCEPTANCE_IDS,
        "review_valid": review_valid,
        "result": PASS_RESULT if review_valid else "FAIL_CLOSED",
        "status": (
            "reviewed_ready_for_upload_no_github_upload"
            if review_valid
            else "batch_review_blocked"
        ),
        "next_gate": NEXT_GATE if review_valid else REVIEW_GATE,
        "reviewed_stage_count": reviewed_stage_count,
        "contract_shape_checks": shape_checks,
        "source_checks": source_checks,
        "stage_artifact_checks": artifact_checks,
        "stage_checker_checks": checker_checks,
        "stage_checks": stage_checks,
        "cross_stage_checks": cross_stage_checks,
        "governance_checks": governance_checks,
        "source_binding_checks": source_binding_checks,
        "finding_checks": finding_checks,
        "truth_checks": truth_checks,
        "finding_counts": {"Critical": 1, "Important": 2, "Minor": 0},
        "all_findings_repaired": all(finding_checks.values())
        if finding_checks
        else False,
        "push_allowed": False,
        "github_upload_allowed": False,
        "app_reinstall_allowed": False,
        "stage041_started": False,
        "raw_metadata_content_accessed": False,
        "fake_ids_business_data_used": False,
        "production_runtime_activation_performed": False,
    }


def main() -> int:
    report = build_batch031_040_review_report()
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if report["review_valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
