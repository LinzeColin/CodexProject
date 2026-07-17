#!/usr/bin/env python3
"""Validate KMFA v1.5 S02-P2 end-to-end traceability evidence."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import subprocess
import sys
import zipfile
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

from KMFA.tools.build_v015_s02_p2_end_to_end_traceability import (
    DEFAULT_SOURCE_PACKAGE,
    FINAL_ARTIFACT_REFS,
    SOURCE_PACKAGE_NAME,
    SOURCE_PACKAGE_SHA256,
    expected_core_outputs,
)
from KMFA.tools.v015_s02_p2_formula_trace import (
    validate_formula_parameter_trace,
)
from KMFA.tools.v015_s02_p2_lineage_contract import (
    validate_lineage_contract_payload,
)
from KMFA.tools.v015_s02_p2_requirement_trace import (
    validate_requirement_task_trace,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = REPO_ROOT / "KMFA"
ARTIFACT_ROOT = PROJECT_ROOT / "stage_artifacts/V015_S02_P2_END_TO_END_TRACEABILITY"
MANIFEST_PATH = ARTIFACT_ROOT / "machine/s02_p2_end_to_end_traceability_manifest.json"
REQUIREMENT_PATH = ARTIFACT_ROOT / "machine/requirement_task_traceability_public_safe.csv"
LINEAGE_PATH = ARTIFACT_ROOT / "machine/data_report_lineage_field_contract_public_safe.json"
FORMULA_PATH = ARTIFACT_ROOT / "machine/formula_test_traceability_public_safe.csv"
PARAMETER_PATH = ARTIFACT_ROOT / "machine/formula_parameter_traceability_public_safe.csv"
VALIDATION_RESULTS_PATH = ARTIFACT_ROOT / "machine/validation_results.jsonl"
P1_MANIFEST_PATH = (
    PROJECT_ROOT
    / "stage_artifacts/V015_S02_P1_REQUIREMENTS_SCOPE_LOCK/machine/s02_p1_requirements_scope_lock_manifest.json"
)
PROJECT_GOVERNANCE_PATH = PROJECT_ROOT / "docs/governance/project.yaml"
ROADMAP_GOVERNANCE_PATH = PROJECT_ROOT / "docs/governance/roadmap.yaml"
AGENTS_PATH = PROJECT_ROOT / "AGENTS.md"
EVENTS_PATH = PROJECT_ROOT / "docs/governance/events.jsonl"
MODEL_SPEC_PATH = PROJECT_ROOT / "docs/governance/MODEL_SPEC.md"
PHASE_BASE_COMMIT = "1de399f35d1c0d2b7ee1ea6451c2be8d1c49a861"

EXPECTED_IDENTITY = {
    "schema_version": "kmfa.v015.s02_p2_end_to_end_traceability.v1",
    "project_id": "KMFA",
    "target_release": "v1.5",
    "stage_id": "S02",
    "roadmap_phase_id": "S02-P2",
    "run_phase_id": "V015_S02_P2_END_TO_END_TRACEABILITY",
    "task_id": "KMFA-V015-S02-P2-END-TO-END-TRACEABILITY-20260713",
    "acceptance_id": "ACC-KMFA-V015-S02-P2-END-TO-END-TRACEABILITY",
    "run_mode": "IMPLEMENT",
    "work_kind": "END_TO_END_TRACEABILITY_PLANNING",
    "phase_base_commit": PHASE_BASE_COMMIT,
}

EXPECTED_TASKS = {
    "S02P2T01": "需求映射到 Stage/Phase/Task",
    "S02P2T02": "建立数据到报告追溯链",
    "S02P2T03": "建立公式到测试追溯链",
}

EXPECTED_RECEIPTS = {
    "s02_p1_strict_dependency",
    "s02_p2_focused_tests",
    "s02_p2_requirement_mutations",
    "s02_p2_lineage_mutations",
    "s02_p2_formula_mutations",
    "roadmap_governance_check",
    "governance_project_check",
    "lean_check",
    "governance_sync_check",
    "no_float_check",
    "no_omission_check",
    "exact_core_rebuild_check",
}


class ValidationError(RuntimeError):
    """Raised when one or more S02-P2 gates fail closed."""


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical_content_hash(value: Mapping[str, Any]) -> str:
    payload = dict(value)
    payload.pop("content_hash", None)
    encoded = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValidationError(f"JSON object required: {path}")
    return value


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        row = json.loads(line)
        if not isinstance(row, dict):
            raise ValidationError(f"JSONL object required: {path}:{index}")
        rows.append(row)
    return rows


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _read_typed_csv(path: Path) -> list[dict[str, Any]]:
    list_fields = {
        "source_status_vocabulary",
        "requirement_refs",
        "planned_implementation_task_refs",
        "control_ids",
        "source_test_descriptions",
        "source_refs",
        "planned_fixture_refs",
        "executable_fixture_refs",
        "test_execution_refs",
        "planned_report_refs",
        "report_artifact_refs",
        "blocking_reasons",
        "parent_definition_ids",
    }
    bool_fields = {
        "source_status_in_declared_vocabulary",
        "runtime_implementation_present",
        "runtime_enablement",
        "product_implementation_claimed",
        "legacy_active_status_inherited",
        "explicitly_declared",
        "unknown_parameter",
        "requires_confirmation",
        "default_usage_allowed",
    }
    rows: list[dict[str, Any]] = []
    for row_number, source in enumerate(_read_csv(path), 2):
        row: dict[str, Any] = {}
        for key, value in source.items():
            if key in list_fields | bool_fields:
                try:
                    decoded = json.loads(value)
                except json.JSONDecodeError as error:
                    raise ValidationError(
                        f"typed CSV JSON decode failed: {path}:{row_number}:{key}"
                    ) from error
                expected_type = list if key in list_fields else bool
                if not isinstance(decoded, expected_type):
                    raise ValidationError(
                        f"typed CSV field type mismatch: {path}:{row_number}:{key}"
                    )
                row[key] = decoded
                continue
            row[key] = value
        rows.append(row)
    return rows


def _require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def _top_level_scalar(text: str, key: str) -> Optional[str]:
    match = re.search(
        rf"(?m)^{re.escape(key)}:\s*(?:\"([^\"]*)\"|'([^']*)'|([^#\n]*?))\s*$",
        text,
    )
    if not match:
        return None
    return next((part.strip() for part in match.groups() if part is not None), None)


def _validate_source_package(source_package: Path, errors: list[str]) -> None:
    _require(source_package.is_file(), "source package missing", errors)
    if not source_package.is_file():
        return
    _require(_sha256(source_package) == SOURCE_PACKAGE_SHA256, "source package hash drift", errors)
    with zipfile.ZipFile(source_package) as archive:
        names = [
            name
            for name in archive.namelist()
            if name.rsplit("/", 1)[-1].startswith("02B_") and name.endswith(".json")
        ]
        _require(len(names) == 1, "source roadmap member count drift", errors)
        if len(names) == 1:
            roadmap = json.loads(archive.read(names[0]).decode("utf-8-sig"))
            _require(
                (roadmap.get("stage_count"), roadmap.get("phase_count"), roadmap.get("task_count"))
                == (24, 72, 216),
                "source 24/72/216 drift",
                errors,
            )


def _validate_manifest(manifest: dict[str, Any], errors: list[str]) -> None:
    for key, expected in EXPECTED_IDENTITY.items():
        _require(manifest.get(key) == expected, f"manifest identity mismatch: {key}", errors)
    _require(bool(str(manifest.get("generated_at", "")).strip()), "manifest generated_at missing", errors)
    _require(manifest.get("content_hash") == _canonical_content_hash(manifest), "manifest content hash mismatch", errors)
    _require(
        manifest.get("source_package")
        == {
            "name": SOURCE_PACKAGE_NAME,
            "bytes": 118652,
            "sha256": SOURCE_PACKAGE_SHA256,
            "stage_count": 24,
            "phase_count": 72,
            "task_count": 216,
            "requirement_count": 55,
        },
        "manifest source package snapshot mismatch",
        errors,
    )
    dependency = manifest.get("dependency_evidence", {})
    rows = dependency.get("dependencies", [])
    _require(dependency.get("count") == 1 and len(rows) == 1, "dependency accounting mismatch", errors)
    if len(rows) == 1:
        row = rows[0]
        _require(row.get("dependency_id") == "s02_p1_requirements_scope_lock", "dependency ID drift", errors)
        _require(row.get("result_commit") == PHASE_BASE_COMMIT, "dependency result commit drift", errors)
        _require(row.get("content_hash") == "sha256:5e2450b41b5308e35a8a57307bfb763c07a38b0ad321f9ac495b9bd8f53e6a04", "dependency content hash drift", errors)
        _require(row.get("bytes") == P1_MANIFEST_PATH.stat().st_size, "dependency bytes drift", errors)
        _require(row.get("sha256") == _sha256(P1_MANIFEST_PATH), "dependency SHA drift", errors)

    phase_scope = manifest.get("phase_scope", {})
    expected_false_scope = {
        "actual_lineage_generated",
        "lineage_full_check_complete",
        "formula_runtime_enablement_performed",
        "product_implementation_allowed",
        "formal_report_allowed",
        "business_decision_basis_allowed",
    }
    _require(phase_scope.get("planning_traceability_only") is True, "planning scope missing", errors)
    for key in expected_false_scope:
        _require(phase_scope.get(key) is False, f"phase boundary violated: {key}", errors)

    accounting = manifest.get("task_accounting", {})
    _require(accounting == {"total": 3, "execution_complete": 3, "accepted": 3, "not_accepted": 0}, "task accounting mismatch", errors)
    tasks = manifest.get("tasks", [])
    by_id = {row.get("task_id"): row for row in tasks if isinstance(row, dict)}
    _require(set(by_id) == set(EXPECTED_TASKS), "S02-P2 task set mismatch", errors)
    for task_id, name in EXPECTED_TASKS.items():
        row = by_id.get(task_id, {})
        _require(row.get("name") == name, f"task name drift: {task_id}", errors)
        _require(row.get("execution_status") == "EXECUTION_COMPLETE", f"task execution drift: {task_id}", errors)
        _require(row.get("acceptance_status") == "PASSED", f"task acceptance drift: {task_id}", errors)
        _require(bool(row.get("evidence_refs")), f"task evidence missing: {task_id}", errors)

    trace = manifest.get("trace_accounting", {})
    expected_trace = {
        "requirement_count": 55,
        "normalized_binding_count": 134,
        "source_explicit_binding_count": 132,
        "controlled_stage_closure_binding_count": 2,
        "p0_p1_requirement_coverage_numerator": 54,
        "p0_p1_requirement_coverage_denominator": 54,
        "p0_p1_requirement_stage_coverage_numerator": 96,
        "p0_p1_requirement_stage_coverage_denominator": 96,
        "all_requirement_stage_coverage_numerator": 97,
        "all_requirement_stage_coverage_denominator": 97,
    }
    for key, expected in expected_trace.items():
        _require(trace.get(key) == expected, f"trace accounting drift: {key}", errors)

    lineage = manifest.get("lineage_accounting", {})
    for key, expected in {
        "actual_lineage_record_count": 0,
        "lineage_full_check_complete": False,
        "layer_count": 8,
        "allowed_edge_count": 10,
        "source_domain_row_count": 21,
        "source_system_count": 7,
        "formal_report_allowed": False,
    }.items():
        _require(lineage.get(key) == expected, f"lineage accounting drift: {key}", errors)

    formula = manifest.get("formula_accounting", {})
    for key, expected in {
        "formula_model_count": 22,
        "formula_count": 14,
        "model_count": 8,
        "source_proposed_count": 17,
        "source_verified_required_count": 5,
        "parameter_control_count": 38,
        "runtime_enabled_count": 0,
        "product_implementation_claim_count": 0,
        "unknown_parameter_default_count": 0,
    }.items():
        _require(formula.get(key) == expected, f"formula accounting drift: {key}", errors)

    _require(
        manifest.get("phase_result")
        == {
            "execution_status": "EXECUTION_COMPLETE",
            "evidence_validation_status": "PASS",
            "final_validation_status": "PASS",
            "acceptance_status": "PASSED",
            "decision": "CONTINUE_TO_S02_P3_ONLY",
        },
        "phase result mismatch",
        errors,
    )
    _require(
        manifest.get("stage_state")
        == {
            "stage_id": "S02",
            "stage_lifecycle_status": "IN_PROGRESS",
            "stage_acceptance_status": "PENDING",
            "stage_passed": False,
            "completed_phase_count": 2,
            "total_phase_count": 3,
        },
        "stage state mismatch",
        errors,
    )
    next_gate = manifest.get("next_entry_gate", {})
    _require(next_gate.get("next_allowed_taskpack_phase") == "S02-P3", "next gate drift", errors)
    _require(next_gate.get("s02_p3_entry_allowed") is True, "S02-P3 entry must open", errors)
    _require(next_gate.get("s02_p3_started_in_current_run") is False, "S02-P3 started in current run", errors)
    for key in ("s03_plus_entry_allowed", "product_implementation_allowed"):
        _require(next_gate.get(key) is False, f"downstream entry opened: {key}", errors)
    expected_downstream_actions = {
        "s02_p3_started",
        "s03_plus_started",
        "technology_stack_selected",
        "product_runtime_implementation_performed",
        "api_implementation_performed",
        "database_implementation_performed",
        "ui_implementation_performed",
        "raw_business_content_read",
        "raw_root_listed_or_inventoried",
        "raw_inbox_mutated",
        "business_execution_performed",
        "github_upload_performed",
        "app_reinstall_performed",
    }
    downstream = manifest.get("downstream_actions", {})
    _require(set(downstream) == expected_downstream_actions, "downstream action key set mismatch", errors)
    for key in expected_downstream_actions:
        _require(downstream.get(key) is False, f"downstream action performed: {key}", errors)


def _validate_artifacts(manifest: dict[str, Any], errors: list[str]) -> None:
    refs = manifest.get("artifact_refs", {})
    _require(refs == FINAL_ARTIFACT_REFS, "artifact refs must be exact", errors)
    expected_ref_values = set(FINAL_ARTIFACT_REFS.values())
    integrity = manifest.get("artifact_integrity", [])
    by_ref = {row.get("ref"): row for row in integrity if isinstance(row, dict)}
    expected_integrity_refs = expected_ref_values - {refs.get("manifest")}
    _require(set(by_ref) == expected_integrity_refs, "artifact integrity ref set mismatch", errors)
    for ref in expected_integrity_refs:
        path = REPO_ROOT / str(ref)
        _require(path.is_file(), f"artifact missing: {ref}", errors)
        if path.is_file():
            _require(
                by_ref.get(ref)
                == {"ref": ref, "bytes": path.stat().st_size, "sha256": _sha256(path)},
                f"artifact integrity mismatch: {ref}",
                errors,
            )


def _validate_governance(
    errors: list[str],
    *,
    project_text: Optional[str] = None,
    roadmap_text: Optional[str] = None,
    agents_text: Optional[str] = None,
    model_spec_text: Optional[str] = None,
) -> None:
    project = (
        PROJECT_GOVERNANCE_PATH.read_text(encoding="utf-8")
        if project_text is None
        else project_text
    )
    roadmap = (
        ROADMAP_GOVERNANCE_PATH.read_text(encoding="utf-8")
        if roadmap_text is None
        else roadmap_text
    )
    project_phase = _top_level_scalar(project, "current_phase_id")
    roadmap_phase = _top_level_scalar(roadmap, "current_phase_id")
    _require(project_phase == roadmap_phase, "project/roadmap current phase mismatch", errors)
    current_p2 = project_phase == "V015_S02_P2_END_TO_END_TRACEABILITY"
    current_p3_successor = project_phase == "V015_S02_P3_SCOPE_GATE"
    current_stage_review = project_phase == "V015_S02_STAGE_REVIEW"
    later_phase = re.fullmatch(
        r"V015_S(?P<stage>0[3-9]|1[0-9]|2[0-4])_P[123](?:_[A-Z0-9_]+)?",
        project_phase or "",
    )
    _require(
        current_p2 or current_p3_successor or current_stage_review or later_phase is not None,
        "illegal S02-P2 governance successor phase",
        errors,
    )

    expected_p2 = {
        "current_stage_id": "S02",
        "current_phase_id": "V015_S02_P2_END_TO_END_TRACEABILITY",
        "current_task_id": "KMFA-V015-S02-P2-END-TO-END-TRACEABILITY-20260713",
        "current_acceptance_id": "ACC-KMFA-V015-S02-P2-END-TO-END-TRACEABILITY",
        "run_mode": "IMPLEMENT",
        "work_kind": "END_TO_END_TRACEABILITY_PLANNING",
        "stage_lifecycle_status": "IN_PROGRESS",
        "stage_acceptance_status": "PENDING",
        "decision": "CONTINUE_TO_S02_P3_ONLY",
        "s02_p1_acceptance_status": "PASSED",
        "s02_p2_started": "true",
        "s02_p2_acceptance_status": "PASSED",
        "s02_p3_entry_allowed": "true",
        "product_implementation_allowed": "false",
        "next_gate_id": "S02-P3",
    }
    expected_p3_successor = {
        "current_stage_id": "S02",
        "current_phase_id": "V015_S02_P3_SCOPE_GATE",
        "current_task_id": "KMFA-V015-S02-P3-SCOPE-GATE-20260713",
        "current_acceptance_id": "ACC-KMFA-V015-S02-P3-SCOPE-GATE",
        "stage_lifecycle_status": "IN_PROGRESS",
        "stage_acceptance_status": "PENDING",
        "decision": "CONTINUE_TO_S02_STAGE_REVIEW_ONLY",
        "s02_p1_acceptance_status": "PASSED",
        "s02_p2_acceptance_status": "PASSED",
        "s02_p3_acceptance_status": "PASSED",
        "s02_p3_entry_allowed": "false",
        "s02_p3_started": "true",
        "s02_stage_review_entry_allowed": "true",
        "s02_stage_review_started_in_p3_run": "false",
        "s03_entry_allowed": "false",
        "product_implementation_allowed": "false",
        "next_gate_id": "S02-STAGE-REVIEW",
    }
    active_expected = (
        expected_p2
        if current_p2
        else expected_p3_successor
        if current_p3_successor
        else {}
    )
    for label, text in (("project", project), ("roadmap", roadmap)):
        for key, value in active_expected.items():
            message = (
                f"{label} S02-P2 historical acceptance drift"
                if current_p3_successor and key == "s02_p2_acceptance_status"
                else f"{label} governance drift: {key}"
            )
            _require(_top_level_scalar(text, key) == value, message, errors)
        if current_stage_review or later_phase is not None:
            expected_stage = "S02" if current_stage_review else f"S{later_phase.group('stage')}"
            _require(
                _top_level_scalar(text, "current_stage_id") == expected_stage,
                f"{label} successor stage/phase mismatch",
                errors,
            )
            for key in ("s02_p1_acceptance_status", "s02_p2_acceptance_status"):
                _require(
                    _top_level_scalar(text, key) == "PASSED",
                    f"{label} historical acceptance drift: {key}",
                    errors,
                )
        for key, value in {
            "s01_stage_review_lifecycle_status": "BLOCKED",
            "s01_stage_review_acceptance_status": "NOT_PASSED",
            "s01_stage_review_decision": "NO_GO",
            "s01_controlled_transition_amendment_acceptance_status": "PASSED",
            "s01_controlled_transition_amendment_decision": "GO_TO_S02_P1_ONLY",
        }.items():
            _require(_top_level_scalar(text, key) == value, f"{label} historical drift: {key}", errors)
    for key, value in (("active_stage_count", "24"), ("active_phase_count", "72"), ("active_task_count", "216")):
        _require(_top_level_scalar(roadmap, key) == value, f"roadmap count drift: {key}", errors)
    agents = AGENTS_PATH.read_text(encoding="utf-8") if agents_text is None else agents_text
    model = (
        MODEL_SPEC_PATH.read_text(encoding="utf-8")
        if model_spec_text is None
        else model_spec_text
    )
    agent_tokens = [
        "不得按单个 Stage 做 GitHub upload gate",
        SOURCE_PACKAGE_SHA256,
    ]
    if current_p2:
        agent_tokens.extend(
            ("V015_S02_P2_END_TO_END_TRACEABILITY", "S02-P3 only")
        )
    for token in agent_tokens:
        _require(token in agents, f"AGENTS token missing: {token}", errors)
    for token in ("FORM-KMFA-V015-S02-P2-END-TO-END-TRACEABILITY-001", "normalized_trace_binding_count == 134", "actual_lineage_record_count == 0", "formula_model_count == 22", "s02_p3_entry_allowed == true"):
        _require(token in model, f"MODEL_SPEC token missing: {token}", errors)


def _validate_events(errors: list[str]) -> None:
    rows = [row for row in _read_jsonl(EVENTS_PATH) if row.get("phase_id") == EXPECTED_IDENTITY["run_phase_id"]]
    _require(len(rows) == 2, "canonical S02-P2 event count mismatch", errors)
    if len(rows) != 2:
        return
    common = {
        "project_id": "KMFA",
        "target_release": "v1.5",
        "stage_id": "S02",
        "phase_id": EXPECTED_IDENTITY["run_phase_id"],
        "roadmap_phase_id": "S02-P2",
        "task_id": EXPECTED_IDENTITY["task_id"],
        "acceptance_id": EXPECTED_IDENTITY["acceptance_id"],
        "run_mode": "IMPLEMENT",
        "work_kind": "END_TO_END_TRACEABILITY_PLANNING",
        "stage_lifecycle_status": "IN_PROGRESS",
        "stage_acceptance_status": "PENDING",
        "s02_stage_passed": False,
        "s02_p3_started": False,
        "product_implementation_allowed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "raw_business_content_read": False,
        "raw_inbox_mutated": False,
        "business_execution_performed": False,
        "next_taskpack_phase": "S02-P3",
    }
    execution, final = rows
    _require(execution.get("event_id") == "EVENT-KMFA-20260713-V015-S02-P2-END-TO-END-TRACEABILITY-EXECUTION", "execution event ID drift", errors)
    _require(execution.get("event_type") == "phase_execution", "execution event type drift", errors)
    _require(final.get("event_id") == "EVENT-KMFA-20260713-V015-S02-P2-END-TO-END-TRACEABILITY-FINAL-VALIDATION", "final event ID drift", errors)
    _require(final.get("event_type") == "final_validation", "final event type drift", errors)
    for key, expected in common.items():
        _require(execution.get(key) == expected, f"execution event drift: {key}", errors)
        _require(final.get(key) == expected, f"final event drift: {key}", errors)
    _require(execution.get("phase_acceptance_status") == "PENDING_FINAL_VALIDATION", "execution event false pass", errors)
    _require(execution.get("s02_p3_entry_allowed") is False, "execution event early gate", errors)
    _require(final.get("phase_acceptance_status") == "PASSED", "final event acceptance drift", errors)
    _require(final.get("final_validation_status") == "PASS", "final event validation drift", errors)
    _require(final.get("decision") == "CONTINUE_TO_S02_P3_ONLY", "final event decision drift", errors)
    _require(final.get("s02_p3_entry_allowed") is True, "final event next gate drift", errors)
    try:
        execution_time = datetime.fromisoformat(str(execution.get("event_time", "")))
        final_time = datetime.fromisoformat(str(final.get("event_time", "")))
        _require(execution_time.tzinfo is not None, "execution event time must be offset-aware", errors)
        _require(final_time.tzinfo is not None, "final event time must be offset-aware", errors)
        _require(execution_time < final_time, "event chronology drift", errors)
    except ValueError:
        errors.append("event time is not ISO-8601")


def _validate_receipts(errors: list[str]) -> None:
    rows = _read_jsonl(VALIDATION_RESULTS_PATH)
    ids = [str(row.get("validation_id", "")) for row in rows]
    _require(len(ids) == len(set(ids)) == 12, "validation receipt count mismatch", errors)
    _require(set(ids) == EXPECTED_RECEIPTS, "validation receipt ID set mismatch", errors)
    for row in rows:
        _require(set(row) == {"validation_id", "command", "result", "exit_code"}, "validation receipt schema mismatch", errors)
        _require(bool(str(row.get("command", "")).strip()), "validation receipt command missing", errors)
        _require(row.get("result") == "PASS" and row.get("exit_code") == 0, "validation receipt not PASS", errors)


def _validate_clean_result(repo_root: Path, errors: list[str]) -> None:
    status = subprocess.run(["git", "status", "--short"], cwd=repo_root, capture_output=True, text=True, check=False)
    _require(status.returncode == 0 and not status.stdout.strip(), "Git worktree must be clean", errors)
    relative = MANIFEST_PATH.relative_to(repo_root).as_posix()
    result = subprocess.run(["git", "log", "-1", "--format=%H", "--", relative], cwd=repo_root, capture_output=True, text=True, check=False)
    commit = result.stdout.strip()
    _require(bool(re.fullmatch(r"[0-9a-f]{40}", commit)), "committed S02-P2 result not found", errors)
    if re.fullmatch(r"[0-9a-f]{40}", commit):
        _require(commit != PHASE_BASE_COMMIT, "S02-P2 result commit must differ from base", errors)
        _require(subprocess.run(["git", "merge-base", "--is-ancestor", PHASE_BASE_COMMIT, commit], cwd=repo_root, check=False).returncode == 0, "phase base not ancestor", errors)
        _require(subprocess.run(["git", "merge-base", "--is-ancestor", commit, "HEAD"], cwd=repo_root, check=False).returncode == 0, "result not ancestor of HEAD", errors)


def validate_v015_s02_p2_end_to_end_traceability(
    manifest_path: Path = MANIFEST_PATH,
    *,
    source_package: Path = DEFAULT_SOURCE_PACKAGE,
    require_core_rebuild: bool = True,
    require_clean_worktree: bool = False,
    repo_root: Path = REPO_ROOT,
) -> dict[str, Any]:
    errors: list[str] = []
    manifest = _read_json(manifest_path)
    _validate_manifest(manifest, errors)
    _validate_source_package(source_package, errors)

    p1 = _read_json(P1_MANIFEST_PATH)
    _require(p1.get("phase_result", {}).get("acceptance_status") == "PASSED", "S02-P1 dependency not passed", errors)
    _require(p1.get("content_hash") == "sha256:5e2450b41b5308e35a8a57307bfb763c07a38b0ad321f9ac495b9bd8f53e6a04", "S02-P1 dependency hash drift", errors)

    requirement_rows = _read_csv(REQUIREMENT_PATH)
    for error in validate_requirement_task_trace(requirement_rows):
        errors.append("requirement_trace:" + error)
    lineage = _read_json(LINEAGE_PATH)
    try:
        validate_lineage_contract_payload(lineage)
    except Exception as error:  # module supplies a typed fail-closed error
        errors.append("lineage_contract:" + str(error))
    formula_rows = _read_typed_csv(FORMULA_PATH)
    parameter_rows = _read_typed_csv(PARAMETER_PATH)
    for error in validate_formula_parameter_trace(
        formula_rows, parameter_rows, source_package=source_package
    ):
        errors.append("formula_trace:" + error)

    _validate_artifacts(manifest, errors)
    _validate_governance(errors)
    _validate_events(errors)
    _validate_receipts(errors)

    email_re = re.compile(rb"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
    for path in ARTIFACT_ROOT.rglob("*"):
        if path.is_file():
            payload = path.read_bytes()
            _require(
                not any(
                    token in payload
                    for token in (b"/Users/", b"/Volumes/", b"/private/", b"/tmp/", b"KMFA_MetaData")
                ),
                f"public-safe leak: {path.name}",
                errors,
            )
            _require(email_re.search(payload) is None, f"public-safe email leak: {path.name}", errors)

    if require_core_rebuild:
        try:
            for path, expected in expected_core_outputs(source_package=source_package).items():
                _require(path.is_file() and path.read_bytes() == expected, f"core rebuild drift: {path.name}", errors)
        except Exception as error:
            errors.append("core rebuild failed:" + str(error))
    if require_clean_worktree:
        _validate_clean_result(repo_root, errors)
    if errors:
        raise ValidationError("\n".join(errors))
    return manifest


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    parser.add_argument("--source-package", type=Path, default=DEFAULT_SOURCE_PACKAGE)
    parser.add_argument(
        "--skip-core-rebuild",
        action="store_true",
        help="development-only escape hatch; strict validation rebuilds core artifacts by default",
    )
    parser.add_argument("--require-clean-worktree", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = validate_v015_s02_p2_end_to_end_traceability(
            args.manifest,
            source_package=args.source_package,
            require_core_rebuild=not args.skip_core_rebuild,
            require_clean_worktree=args.require_clean_worktree,
        )
    except (OSError, ValueError, KeyError, json.JSONDecodeError, zipfile.BadZipFile, ValidationError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    result_label = "NON_STRICT_PASS" if args.skip_core_rebuild else "PASS"
    active_phase = _top_level_scalar(
        PROJECT_GOVERNANCE_PATH.read_text(encoding="utf-8"), "current_phase_id"
    )
    if active_phase == "V015_S02_P3_SCOPE_GATE":
        state_summary = (
            f"historical_phase={result['phase_result']['acceptance_status']}; "
            "active_phase=V015_S02_P3_SCOPE_GATE; "
            "S02=IN_PROGRESS/PENDING; next=S02-STAGE-REVIEW only"
        )
    elif active_phase == "V015_S02_P2_END_TO_END_TRACEABILITY":
        state_summary = (
            f"phase={result['phase_result']['acceptance_status']}; "
            "S02=IN_PROGRESS/PENDING; next=S02-P3 only"
        )
    else:
        state_summary = (
            f"historical_phase={result['phase_result']['acceptance_status']}; "
            f"active_phase={active_phase}"
        )
    print(
        f"{result_label}: KMFA v1.5 S02-P2 end-to-end traceability validated; "
        f"{state_summary}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
