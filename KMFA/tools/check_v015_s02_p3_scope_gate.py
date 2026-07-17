#!/usr/bin/env python3
"""Validate KMFA v1.5 S02-P3 scope-gate and change-control evidence.

Strict validation rebuilds all deterministic core artifacts and the final
manifest.  ``--skip-exact-rebuild`` is deliberately labelled non-strict and
exists only for diagnostics.  This phase is governance/planning only: it does
not install a runtime or CI hook and does not authorize S03 or business work.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import subprocess
import sys
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

from KMFA.tools.build_v015_s02_p3_scope_gate import (
    DEFAULT_SOURCE_PACKAGE,
    FINAL_ARTIFACT_REFS,
    MANIFEST_RELATIVE,
    OUTPUT_ROOT_RELATIVE,
    PHASE_BASE_COMMIT,
    SOURCE_PACKAGE_NAME,
    SOURCE_PACKAGE_SHA256,
    _content_hash,
    _json_bytes,
    build_final_manifest,
    expected_core_outputs,
)
from KMFA.tools.v015_s02_p3_scope_gate import (
    PROHIBITION_COLUMNS,
    SCOPE_COLUMNS,
    load_s02_p3_task_contract,
    validate_change_control_protocol,
    validate_prohibited_action_rows,
    validate_scope_priority_rows,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = REPO_ROOT / "KMFA"
ARTIFACT_ROOT = PROJECT_ROOT / OUTPUT_ROOT_RELATIVE
MANIFEST_PATH = ARTIFACT_ROOT / MANIFEST_RELATIVE
SCOPE_PATH = ARTIFACT_ROOT / "machine/scope_priority_gate_public_safe.csv"
PROHIBITION_PATH = ARTIFACT_ROOT / "machine/prohibited_action_hard_stops_public_safe.csv"
CHANGE_PROTOCOL_PATH = ARTIFACT_ROOT / "machine/change_control_protocol_public_safe.json"
ACCEPTANCE_PATH = ARTIFACT_ROOT / "machine/acceptance_matrix_public_safe.json"
VALIDATION_RESULTS_PATH = ARTIFACT_ROOT / "machine/validation_results.jsonl"

P1_MANIFEST_PATH = (
    PROJECT_ROOT
    / "stage_artifacts/V015_S02_P1_REQUIREMENTS_SCOPE_LOCK/machine/"
    "s02_p1_requirements_scope_lock_manifest.json"
)
P2_MANIFEST_PATH = (
    PROJECT_ROOT
    / "stage_artifacts/V015_S02_P2_END_TO_END_TRACEABILITY/machine/"
    "s02_p2_end_to_end_traceability_manifest.json"
)
PROJECT_GOVERNANCE_PATH = PROJECT_ROOT / "docs/governance/project.yaml"
ROADMAP_GOVERNANCE_PATH = PROJECT_ROOT / "docs/governance/roadmap.yaml"
EVENTS_PATH = PROJECT_ROOT / "docs/governance/events.jsonl"
DEVELOPMENT_EVENTS_PATH = PROJECT_ROOT / "docs/governance/development_events.jsonl"
AGENTS_PATH = PROJECT_ROOT / "AGENTS.md"
MODEL_SPEC_PATH = PROJECT_ROOT / "docs/governance/MODEL_SPEC.md"

EXPECTED_IDENTITY = {
    "schema_version": "kmfa.v015.s02_p3_scope_gate.v1",
    "project_id": "KMFA",
    "target_release": "v1.5",
    "stage_id": "S02",
    "roadmap_phase_id": "S02-P3",
    "run_phase_id": "V015_S02_P3_SCOPE_GATE",
    "task_id": "KMFA-V015-S02-P3-SCOPE-GATE-20260713",
    "acceptance_id": "ACC-KMFA-V015-S02-P3-SCOPE-GATE",
    "run_mode": "IMPLEMENT",
    "work_kind": "SCOPE_GATE_CHANGE_CONTROL_PLANNING",
    "phase_base_commit": "833c8a12203a837ae20afa6ba22ab114a636c846",
}

EXPECTED_TASKS = {
    "S02P3T01": "锁定 P0/P1/P2 范围",
    "S02P3T02": "锁定禁止事项",
    "S02P3T03": "建立变更控制",
}

EXPECTED_RECEIPTS = {
    "s02_p1_strict_dependency",
    "s02_p2_strict_dependency",
    "s02_p3_focused_tests",
    "s02_p3_scope_mutations",
    "s02_p3_prohibition_mutations",
    "s02_p3_change_control_mutations",
    "roadmap_governance_check",
    "governance_project_check",
    "lean_check",
    "governance_sync_check",
    "no_float_check",
    "no_omission_check",
    "phase_diff_whitespace_check",
}

PUBLIC_SAFE_TOKENS = (
    b"/Users/",
    b"/Volumes/",
    b"/private/",
    b"/tmp/",
    b"/home/",
    b"KMFA_MetaData",
)
EMAIL_RE = re.compile(
    rb"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"
)

ALLOWED_PHASE_PATHS = {
    "KMFA/AGENTS.md",
    "KMFA/CHANGELOG.md",
    "KMFA/HANDOFF.md",
    "KMFA/README.md",
    "KMFA/功能清单.md",
    "KMFA/开发记录.md",
    "KMFA/模型参数文件.md",
    "KMFA/metadata/model_registry.yaml",
    "KMFA/metadata/project/project.yaml",
    "KMFA/metadata/stage_status.jsonl",
    "KMFA/stage_artifacts/V015_S02_P1_REQUIREMENTS_SCOPE_LOCK/human/test_results_zh.md",
    "KMFA/stage_artifacts/V015_S02_P1_REQUIREMENTS_SCOPE_LOCK/machine/s02_p1_requirements_scope_lock_manifest.json",
    "KMFA/stage_artifacts/V015_S02_P1_REQUIREMENTS_SCOPE_LOCK/machine/validation_results.jsonl",
    "KMFA/stage_artifacts/V015_S02_P2_END_TO_END_TRACEABILITY/human/test_results_zh.md",
    "KMFA/stage_artifacts/V015_S02_P2_END_TO_END_TRACEABILITY/machine/s02_p2_end_to_end_traceability_manifest.json",
    "KMFA/stage_artifacts/V015_S02_P2_END_TO_END_TRACEABILITY/machine/validation_results.jsonl",
    "KMFA/docs/governance/ASSURANCE_STATUS.yaml",
    "KMFA/docs/governance/DEVELOPMENT_LEDGER.md",
    "KMFA/docs/governance/MODEL_SPEC.md",
    "KMFA/docs/governance/OWNER_STATUS.md",
    "KMFA/docs/governance/STATUS.md",
    "KMFA/docs/governance/TRACEABILITY_MATRIX.csv",
    "KMFA/docs/governance/VERSION_MATRIX.yaml",
    "KMFA/docs/governance/delivery_tasks.yaml",
    "KMFA/docs/governance/development_events.jsonl",
    "KMFA/docs/governance/events.jsonl",
    "KMFA/docs/governance/formula_registry.yaml",
    "KMFA/docs/governance/model_registry.yaml",
    "KMFA/docs/governance/parameter_registry.csv",
    "KMFA/docs/governance/project.yaml",
    "KMFA/docs/governance/roadmap.yaml",
    "KMFA/tests/test_v015_roadmap_governance_sync.py",
    "KMFA/tests/test_v015_s02_p2_end_to_end_traceability.py",
    "KMFA/tests/test_v015_s02_p2_formula_trace.py",
    "KMFA/tests/test_v015_s02_p3_scope_gate.py",
    "KMFA/tests/test_v015_s02_p3_scope_gate_evidence.py",
    "KMFA/tests/test_v015_s02_stage_review.py",
    "KMFA/tools/build_v015_s02_p3_scope_gate.py",
    "KMFA/tools/build_v015_s02_stage_review.py",
    "KMFA/tools/check_v015_s02_p1_requirements_scope_lock.py",
    "KMFA/tools/check_v015_s02_p2_end_to_end_traceability.py",
    "KMFA/tools/check_v015_s02_p3_scope_gate.py",
    "KMFA/tools/check_v015_s02_stage_review.py",
    "KMFA/tools/v015_roadmap_governance_sync.py",
    "KMFA/tools/v015_s02_p2_formula_trace.py",
    "KMFA/tools/v015_s02_p3_scope_gate.py",
}
ALLOWED_PHASE_PREFIXES = (
    "KMFA/stage_artifacts/V015_S02_P3_SCOPE_GATE/",
    "KMFA/stage_artifacts/V015_S02_STAGE_REVIEW/",
)


class ValidationError(RuntimeError):
    """Raised when one or more S02-P3 gates fail closed."""


def _require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical_content_hash(value: Mapping[str, Any]) -> str:
    return _content_hash(value)


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValidationError(f"JSON object required: {path}")
    return value


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(
        path.read_text(encoding="utf-8").splitlines(), 1
    ):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValidationError(f"JSONL object required: {path}:{line_number}")
        rows.append(value)
    return rows


def _read_typed_csv(
    path: Path,
    *,
    list_fields: set[str],
    bool_fields: set[str],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for line_number, source in enumerate(reader, 2):
            row: dict[str, Any] = {}
            for key, value in source.items():
                if key in list_fields | bool_fields:
                    try:
                        decoded = json.loads(value)
                    except json.JSONDecodeError as error:
                        raise ValidationError(
                            f"typed CSV decode failed: {path}:{line_number}:{key}"
                        ) from error
                    expected = list if key in list_fields else bool
                    if not isinstance(decoded, expected):
                        raise ValidationError(
                            f"typed CSV type mismatch: {path}:{line_number}:{key}"
                        )
                    row[key] = decoded
                else:
                    row[key] = value
            rows.append(row)
    return rows


def _top_level_scalar(text: str, key: str) -> Optional[str]:
    match = re.search(
        rf"(?m)^{re.escape(key)}:\s*(?:\"([^\"]*)\"|'([^']*)'|([^#\n]*?))\s*$",
        text,
    )
    if not match:
        return None
    return next((part.strip() for part in match.groups() if part is not None), None)


def _offset_time(value: Any, label: str, errors: list[str]) -> Optional[datetime]:
    try:
        parsed = datetime.fromisoformat(str(value))
    except ValueError:
        errors.append(f"{label}: invalid ISO-8601 timestamp")
        return None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        errors.append(f"{label}: timezone offset required")
        return None
    return parsed


def _mapping_value(
    value: Mapping[str, Any], keys: Sequence[str], expected: Any, label: str, errors: list[str]
) -> None:
    present = [key for key in keys if key in value]
    _require(bool(present), f"{label}: accounting key missing", errors)
    if present:
        _require(value.get(present[0]) == expected, f"{label}: accounting drift", errors)


def _validate_manifest(manifest: dict[str, Any], errors: list[str]) -> None:
    for key, expected in EXPECTED_IDENTITY.items():
        _require(manifest.get(key) == expected, f"manifest identity mismatch: {key}", errors)
    _offset_time(manifest.get("generated_at"), "manifest generated_at", errors)
    _require(
        manifest.get("content_hash") == _canonical_content_hash(manifest),
        "manifest content hash mismatch",
        errors,
    )

    source = manifest.get("source_package", {})
    for key, expected in {
        "name": SOURCE_PACKAGE_NAME,
        "bytes": 118652,
        "sha256": SOURCE_PACKAGE_SHA256,
        "stage_count": 24,
        "phase_count": 72,
        "task_count": 216,
        "requirement_count": 55,
    }.items():
        _require(source.get(key) == expected, f"source package drift: {key}", errors)
    for key, expected in {
        "sha_manifest_declared_member_count": 21,
        "sha_manifest_verified_member_count": 21,
        "sha_manifest_mismatch_count": 0,
        "unmanifested_member_count": 0,
    }.items():
        _require(source.get(key) == expected, f"source 21/21 verification drift: {key}", errors)

    dependencies = manifest.get("dependency_evidence", {}).get("dependencies", [])
    _require(len(dependencies) == 2, "dependency count mismatch", errors)
    expected_dependencies = {
        "s02_p1_requirements_scope_lock": (
            P1_MANIFEST_PATH,
            "1de399f35d1c0d2b7ee1ea6451c2be8d1c49a861",
        ),
        "s02_p2_end_to_end_traceability": (P2_MANIFEST_PATH, PHASE_BASE_COMMIT),
    }
    by_id = {
        row.get("dependency_id"): row for row in dependencies if isinstance(row, dict)
    }
    _require(set(by_id) == set(expected_dependencies), "dependency ID set mismatch", errors)
    for dependency_id, (path, commit) in expected_dependencies.items():
        row = by_id.get(dependency_id, {})
        upstream = _read_json(path)
        _require(row.get("result_commit") == commit, f"dependency commit drift: {dependency_id}", errors)
        _require(row.get("bytes") == path.stat().st_size, f"dependency bytes drift: {dependency_id}", errors)
        _require(row.get("sha256") == _sha256(path), f"dependency SHA drift: {dependency_id}", errors)
        _require(row.get("content_hash") == upstream.get("content_hash"), f"dependency content hash drift: {dependency_id}", errors)
        _require(upstream.get("phase_result", {}).get("acceptance_status") == "PASSED", f"dependency not passed: {dependency_id}", errors)

    phase_scope = manifest.get("phase_scope", {})
    for key in (
        "planning_only",
        "scope_priority_lock_built",
        "prohibited_action_hard_stops_built",
        "change_control_protocol_built",
    ):
        _require(phase_scope.get(key) is True, f"phase planning scope missing: {key}", errors)
    for key in (
        "product_implementation_allowed",
        "runtime_or_ci_hook_implemented",
        "formal_report_allowed",
        "business_execution_allowed",
        "s02_stage_review_performed",
        "s03_started",
    ):
        _require(phase_scope.get(key) is False, f"phase boundary violated: {key}", errors)

    _require(
        manifest.get("task_accounting")
        == {"total": 3, "execution_complete": 3, "accepted": 3, "not_accepted": 0},
        "task accounting mismatch",
        errors,
    )
    tasks = manifest.get("tasks", [])
    task_map = {row.get("task_id"): row for row in tasks if isinstance(row, dict)}
    _require(set(task_map) == set(EXPECTED_TASKS), "S02-P3 task set mismatch", errors)
    for task_id, name in EXPECTED_TASKS.items():
        row = task_map.get(task_id, {})
        _require(row.get("name") == name, f"task name drift: {task_id}", errors)
        _require(row.get("execution_status") == "EXECUTION_COMPLETE", f"task execution drift: {task_id}", errors)
        _require(row.get("acceptance_status") == "PASSED", f"task acceptance drift: {task_id}", errors)
        _require(bool(row.get("evidence_refs")), f"task evidence missing: {task_id}", errors)

    scope = manifest.get("scope_accounting", {})
    _mapping_value(scope, ("scope_row_count",), 103, "scope total", errors)
    for keys, expected, label in (
        (("requirement_count",), 55, "requirements"),
        (("business_line_count",), 10, "business lines"),
        (("capability_count",), 37, "capabilities"),
        (("deferred_policy_count",), 1, "deferred policy"),
    ):
        _mapping_value(scope, keys, expected, label, errors)
    for key in (
        "time_pressure_quality_tradeoff_allowed_count",
        "implementation_authorized_count",
    ):
        _require(scope.get(key) == 0, f"scope boundary drift: {key}", errors)
    for key, expected in {
        "requirement_p0_count": 46,
        "requirement_p1_count": 8,
        "requirement_p2_count": 1,
        "business_line_p0_count": 1,
        "business_line_p1_count": 7,
        "business_line_p2_count": 2,
    }.items():
        _require(scope.get(key) == expected, f"scope priority drift: {key}", errors)

    prohibitions = manifest.get("prohibition_accounting", {})
    _mapping_value(prohibitions, ("prohibition_row_count",), 51, "prohibition total", errors)
    _mapping_value(prohibitions, ("explicit_prohibition_count",), 6, "explicit prohibitions", errors)
    _mapping_value(prohibitions, ("business_line_prohibition_count",), 45, "business-line prohibitions", errors)
    _require(prohibitions.get("covered_business_line_count") == 10, "prohibition business-line coverage drift", errors)
    _require(prohibitions.get("hard_stop_required_count") == 51, "prohibition hard-stop count drift", errors)
    for key in (
        "runtime_guard_implemented_count",
        "prohibited_action_implemented_count",
        "product_action_authorized_count",
        "override_allowed_count",
    ):
        if key in prohibitions:
            _require(prohibitions.get(key) == 0, f"prohibition boundary drift: {key}", errors)

    change = manifest.get("change_control_accounting", {})
    _mapping_value(change, ("auditable_domain_count",), 4, "auditable domains", errors)
    _mapping_value(change, ("change_type_count",), 5, "change types", errors)
    _mapping_value(
        change,
        ("required_change_field_count",),
        36,
        "required change fields",
        errors,
    )
    for key in (
        "runtime_or_ci_hook_implemented",
        "unregistered_change_merge_allowed",
        "unapproved_change_merge_allowed",
        "unvalidated_change_merge_allowed",
    ):
        _require(change.get(key) is False, f"change-control boundary drift: {key}", errors)

    _require(
        manifest.get("phase_result")
        == {
            "execution_status": "EXECUTION_COMPLETE",
            "evidence_validation_status": "PASS",
            "final_validation_status": "PASS",
            "acceptance_status": "PASSED",
            "decision": "CONTINUE_TO_S02_STAGE_REVIEW_ONLY",
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
            "completed_phase_count": 3,
            "total_phase_count": 3,
            "execution_percentage": 100,
            "stage_review_performed": False,
        },
        "stage state mismatch",
        errors,
    )
    next_gate = manifest.get("next_entry_gate", {})
    _require(next_gate.get("next_allowed_run") == "S02-STAGE-REVIEW", "next run drift", errors)
    _require(next_gate.get("next_gate_id") == "S02-STAGE-REVIEW", "next gate drift", errors)
    _require(next_gate.get("s02_stage_review_entry_allowed") is True, "S02 review entry closed", errors)
    for key in (
        "s02_stage_review_started_in_current_run",
        "s03_entry_allowed",
        "s03_plus_entry_allowed",
        "product_implementation_allowed",
    ):
        if key in next_gate or key in ("s02_stage_review_started_in_current_run", "s03_entry_allowed"):
            _require(next_gate.get(key) is False, f"downstream entry opened: {key}", errors)

    downstream = manifest.get("downstream_actions", {})
    _require(bool(downstream), "downstream action contract missing", errors)
    for key, value in downstream.items():
        _require(value is False, f"downstream action performed: {key}", errors)

    manifest_text = json.dumps(manifest, ensure_ascii=False, sort_keys=True).encode("utf-8")
    for token in PUBLIC_SAFE_TOKENS:
        _require(token not in manifest_text, f"manifest public-safe leak: {token!r}", errors)
    _require(EMAIL_RE.search(manifest_text) is None, "manifest public-safe email leak", errors)


def _validate_core_artifacts(source_package: Path, errors: list[str]) -> None:
    scope_rows = _read_typed_csv(
        SCOPE_PATH,
        list_fields=set(),
        bool_fields={
            "in_scope_registry",
            "priority_locked_by_s02_p3",
            "quality_gate_required",
            "change_control_required",
            "time_pressure_quality_tradeoff_allowed",
            "product_acceptance_inherited",
            "implementation_authorized_by_s02_p3",
        },
    )
    for error in validate_scope_priority_rows(scope_rows):
        errors.append("scope_priority:" + error)

    prohibition_rows = _read_typed_csv(
        PROHIBITION_PATH,
        list_fields={"detection_tokens"},
        bool_fields={
            key
            for key in PROHIBITION_COLUMNS
            if key
            in {
                "hard_stop_required",
                "planning_gate_defined",
                "automatic_execution_allowed",
                "runtime_guard_implemented",
                "prohibited_action_implemented_in_s02_p3",
                "product_action_authorized",
                "merge_allowed_on_detection",
                "stop_triggered_in_s02_p3",
                "change_control_can_override",
                "owner_authorization_can_override",
            }
        },
    )
    for error in validate_prohibited_action_rows(prohibition_rows):
        errors.append("prohibitions:" + error)

    protocol = _read_json(CHANGE_PROTOCOL_PATH)
    for error in validate_change_control_protocol(protocol):
        errors.append("change_control:" + error)
    _require(
        protocol.get("auditable_domains")
        == ["FRONTEND", "BACKEND", "FORMULA", "DATA_CONTRACT"],
        "change-control auditable domains drift",
        errors,
    )
    _require(
        protocol.get("change_types")
        == ["REQUIREMENT", "FRONTEND", "BACKEND", "FORMULA", "DATA_CONTRACT"],
        "change-control types drift",
        errors,
    )

    acceptance = _read_json(ACCEPTANCE_PATH)
    source_contract = load_s02_p3_task_contract(source_package)
    encoded = json.dumps(acceptance, ensure_ascii=False, sort_keys=True)
    for task_id, contract in source_contract.items():
        _require(task_id in encoded, f"acceptance task missing: {task_id}", errors)
        for field, value in contract.items():
            _require(value in encoded, f"acceptance source clause missing: {task_id}:{field}", errors)
    for token in (
        "CONTINUE_TO_S02_STAGE_REVIEW_ONLY",
        "IN_PROGRESS",
        "PENDING",
    ):
        _require(token in encoded, f"acceptance gate token missing: {token}", errors)
    for key, expected in {
        "phase_acceptance_eligible": True,
        "stage_acceptance_allowed": False,
        "stage_review_required": True,
        "stage_review_performed": False,
        "s03_entry_allowed": False,
        "product_implementation_allowed": False,
        "public_safe_status": "PUBLIC_SAFE",
    }.items():
        _require(acceptance.get(key) == expected, f"acceptance boundary drift: {key}", errors)


def _validate_artifact_integrity(manifest: Mapping[str, Any], errors: list[str]) -> None:
    refs = manifest.get("artifact_refs", {})
    _require(refs == FINAL_ARTIFACT_REFS, "artifact refs must be exact", errors)
    expected_refs = set(FINAL_ARTIFACT_REFS.values()) - {FINAL_ARTIFACT_REFS["manifest"]}
    integrity = manifest.get("artifact_integrity", [])
    by_ref = {row.get("ref"): row for row in integrity if isinstance(row, dict)}
    _require(set(by_ref) == expected_refs, "artifact integrity ref set mismatch", errors)
    for ref in expected_refs:
        path = REPO_ROOT / ref
        _require(path.is_file(), f"artifact missing: {ref}", errors)
        if path.is_file():
            _require(
                by_ref.get(ref)
                == {"ref": ref, "bytes": path.stat().st_size, "sha256": _sha256(path)},
                f"artifact integrity mismatch: {ref}",
                errors,
            )


def _validate_governance(errors: list[str]) -> None:
    current_expected = {
        "current_stage_id": "S02",
        "current_phase_id": "V015_S02_P3_SCOPE_GATE",
        "current_task_id": "KMFA-V015-S02-P3-SCOPE-GATE-20260713",
        "current_acceptance_id": "ACC-KMFA-V015-S02-P3-SCOPE-GATE",
        "run_mode": "IMPLEMENT",
        "work_kind": "SCOPE_GATE_CHANGE_CONTROL_PLANNING",
        "stage_lifecycle_status": "IN_PROGRESS",
        "stage_acceptance_status": "PENDING",
        "decision": "CONTINUE_TO_S02_STAGE_REVIEW_ONLY",
        "s02_p1_acceptance_status": "PASSED",
        "s02_p2_acceptance_status": "PASSED",
        "s02_p3_acceptance_status": "PASSED",
        "s02_p3_entry_allowed": "false",
        "s02_stage_review_entry_allowed": "true",
        "s02_stage_review_started_in_p3_run": "false",
        "s03_entry_allowed": "false",
        "product_implementation_allowed": "false",
        "next_gate_id": "S02-STAGE-REVIEW",
    }
    project_text = PROJECT_GOVERNANCE_PATH.read_text(encoding="utf-8")
    roadmap_text = ROADMAP_GOVERNANCE_PATH.read_text(encoding="utf-8")
    current_phase = _top_level_scalar(project_text, "current_phase_id")
    _require(
        current_phase == _top_level_scalar(roadmap_text, "current_phase_id"),
        "project/roadmap current phase mismatch",
        errors,
    )
    current_p3 = current_phase == "V015_S02_P3_SCOPE_GATE"
    current_stage_review = current_phase == "V015_S02_STAGE_REVIEW"
    later_phase = re.fullmatch(
        r"V015_S(?P<stage>0[3-9]|1[0-9]|2[0-4])_P[123](?:_[A-Z0-9_]+)?",
        current_phase or "",
    )
    _require(
        current_p3 or current_stage_review or later_phase is not None,
        "illegal S02-P3 governance successor phase",
        errors,
    )
    for label, path in (
        ("project", PROJECT_GOVERNANCE_PATH),
        ("roadmap", ROADMAP_GOVERNANCE_PATH),
    ):
        text = path.read_text(encoding="utf-8")
        if current_p3:
            for key, value in current_expected.items():
                _require(_top_level_scalar(text, key) == value, f"{label} governance drift: {key}", errors)
        else:
            expected_stage = "S02" if current_stage_review else f"S{later_phase.group('stage')}"
            _require(
                _top_level_scalar(text, "current_stage_id") == expected_stage,
                f"{label} successor stage/phase mismatch",
                errors,
            )
            for key in (
                "s02_p1_acceptance_status",
                "s02_p2_acceptance_status",
                "s02_p3_acceptance_status",
            ):
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
    roadmap = ROADMAP_GOVERNANCE_PATH.read_text(encoding="utf-8")
    for key, value in (
        ("active_stage_count", "24"),
        ("active_phase_count", "72"),
        ("active_task_count", "216"),
    ):
        _require(_top_level_scalar(roadmap, key) == value, f"roadmap count drift: {key}", errors)
    agents = AGENTS_PATH.read_text(encoding="utf-8")
    model = MODEL_SPEC_PATH.read_text(encoding="utf-8")
    for token in (
        "V015_S02_P3_SCOPE_GATE",
        "S02 Stage review",
        SOURCE_PACKAGE_SHA256,
    ):
        _require(token in agents, f"AGENTS token missing: {token}", errors)
    for token in (
        "V015_S02_P3_SCOPE_GATE",
        "scope_item_count == 103",
        "prohibition_count == 51",
        "auditable implementation domains=`4`",
        "runtime_or_ci_hook_implemented=false",
    ):
        _require(token in model, f"MODEL_SPEC token missing: {token}", errors)


def _validate_event_pair(
    rows: Sequence[Mapping[str, Any]],
    *,
    prefix: str,
    generated_at: str,
    errors: list[str],
) -> None:
    _require(len(rows) == 2, f"{prefix}: event count mismatch", errors)
    if len(rows) != 2:
        return
    by_type = {row.get("event_type"): row for row in rows}
    execution = by_type.get("phase_execution", {})
    final = by_type.get("final_validation", {})
    _require(bool(execution) and bool(final), f"{prefix}: event types mismatch", errors)
    common = {
        "project_id": "KMFA",
        "target_release": "v1.5",
        "stage_id": "S02",
        "phase_id": "V015_S02_P3_SCOPE_GATE",
        "roadmap_phase_id": "S02-P3",
        "task_id": "KMFA-V015-S02-P3-SCOPE-GATE-20260713",
        "acceptance_id": "ACC-KMFA-V015-S02-P3-SCOPE-GATE",
        "run_mode": "IMPLEMENT",
        "work_kind": "SCOPE_GATE_CHANGE_CONTROL_PLANNING",
        "stage_lifecycle_status": "IN_PROGRESS",
        "stage_acceptance_status": "PENDING",
        "s02_stage_passed": False,
        "scope_item_count": 103,
        "prohibition_count": 51,
        "auditable_domain_count": 4,
        "product_implementation_allowed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "raw_business_content_read": False,
        "raw_inbox_mutated": False,
        "business_execution_performed": False,
    }
    for label, row in (("execution", execution), ("final", final)):
        for key, expected in common.items():
            _require(row.get(key) == expected, f"{prefix} {label} event drift: {key}", errors)
    _require(execution.get("phase_acceptance_status") == "PENDING_FINAL_VALIDATION", f"{prefix}: execution false pass", errors)
    _require(execution.get("s02_stage_review_entry_allowed") is False, f"{prefix}: review opened early", errors)
    _require(final.get("phase_acceptance_status") == "PASSED", f"{prefix}: final acceptance drift", errors)
    _require(final.get("final_validation_status") == "PASS", f"{prefix}: final validation drift", errors)
    _require(final.get("decision") == "CONTINUE_TO_S02_STAGE_REVIEW_ONLY", f"{prefix}: final decision drift", errors)
    _require(final.get("s02_stage_review_entry_allowed") is True, f"{prefix}: review entry closed", errors)
    _require(final.get("s03_entry_allowed") is False, f"{prefix}: S03 opened", errors)
    execution_time = _offset_time(execution.get("event_time"), f"{prefix} execution", errors)
    final_time = _offset_time(final.get("event_time"), f"{prefix} final", errors)
    if execution_time is not None and final_time is not None:
        _require(execution_time < final_time, f"{prefix}: event chronology drift", errors)
    if prefix == "canonical":
        _require(final.get("event_time") == generated_at, "canonical final event/manifest time drift", errors)


def _validate_events(manifest: Mapping[str, Any], errors: list[str]) -> None:
    canonical = [
        row
        for row in _read_jsonl(EVENTS_PATH)
        if row.get("phase_id") == EXPECTED_IDENTITY["run_phase_id"]
    ]
    development = [
        row
        for row in _read_jsonl(DEVELOPMENT_EVENTS_PATH)
        if row.get("phase_id") == EXPECTED_IDENTITY["run_phase_id"]
    ]
    _validate_event_pair(
        canonical,
        prefix="canonical",
        generated_at=str(manifest.get("generated_at", "")),
        errors=errors,
    )
    _validate_event_pair(
        development,
        prefix="development",
        generated_at=str(manifest.get("generated_at", "")),
        errors=errors,
    )


def _validate_receipts(errors: list[str]) -> None:
    rows = _read_jsonl(VALIDATION_RESULTS_PATH)
    ids = [str(row.get("validation_id", "")) for row in rows]
    _require(len(ids) == len(set(ids)) == 13, "validation receipt count mismatch", errors)
    _require(set(ids) == EXPECTED_RECEIPTS, "validation receipt ID set mismatch", errors)
    for row in rows:
        _require(
            set(row) == {"validation_id", "command", "result", "exit_code"},
            f"validation receipt schema mismatch: {row.get('validation_id')}",
            errors,
        )
        _require(bool(str(row.get("command", "")).strip()), "validation receipt command missing", errors)
        _require(row.get("result") == "PASS" and row.get("exit_code") == 0, f"validation receipt not PASS: {row.get('validation_id')}", errors)


def _validate_public_safe(errors: list[str]) -> None:
    for path in ARTIFACT_ROOT.rglob("*"):
        if not path.is_file():
            continue
        payload = path.read_bytes()
        for token in PUBLIC_SAFE_TOKENS:
            _require(token not in payload, f"public-safe leak: {path.name}:{token!r}", errors)
        _require(EMAIL_RE.search(payload) is None, f"public-safe email leak: {path.name}", errors)


def _validate_phase_diff_allowlist(repo_root: Path, errors: list[str]) -> None:
    ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", PHASE_BASE_COMMIT, "HEAD"],
        cwd=repo_root,
        check=False,
    )
    _require(ancestor.returncode == 0, "phase base is not an ancestor of HEAD", errors)
    tracked = subprocess.run(
        [
            "git",
            "-c",
            "core.quotePath=false",
            "diff",
            "--name-only",
            PHASE_BASE_COMMIT,
            "--",
        ],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    untracked = subprocess.run(
        [
            "git",
            "-c",
            "core.quotePath=false",
            "ls-files",
            "--others",
            "--exclude-standard",
        ],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    _require(tracked.returncode == 0 and untracked.returncode == 0, "phase diff inventory failed", errors)
    changed = {
        path.strip()
        for path in (tracked.stdout + "\n" + untracked.stdout).splitlines()
        if path.strip()
    }
    unexpected = sorted(
        path
        for path in changed
        if path not in ALLOWED_PHASE_PATHS
        and not any(path.startswith(prefix) for prefix in ALLOWED_PHASE_PREFIXES)
    )
    _require(not unexpected, "phase diff allowlist violation: " + ", ".join(unexpected), errors)


def _validate_exact_rebuild(
    manifest: Mapping[str, Any], source_package: Path, errors: list[str]
) -> None:
    try:
        outputs = expected_core_outputs(
            project_root=PROJECT_ROOT,
            source_package=source_package,
            output_root=ARTIFACT_ROOT,
        )
        for path, expected in outputs.items():
            _require(path.is_file(), f"exact core artifact missing: {path.name}", errors)
            if path.is_file():
                _require(path.read_bytes() == expected, f"exact core rebuild drift: {path.name}", errors)
        expected_manifest = build_final_manifest(
            generated_at=str(manifest.get("generated_at", "")),
            project_root=PROJECT_ROOT,
            source_package=source_package,
        )
        _require(MANIFEST_PATH.read_bytes() == _json_bytes(expected_manifest), "exact final manifest rebuild drift", errors)
    except Exception as error:  # builder has a typed fail-closed error
        errors.append("exact rebuild failed: " + str(error))


def _validate_clean_result(repo_root: Path, errors: list[str]) -> None:
    status = subprocess.run(
        ["git", "status", "--short"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    _require(status.returncode == 0 and not status.stdout.strip(), "Git worktree must be clean", errors)
    relative = MANIFEST_PATH.relative_to(repo_root).as_posix()
    log = subprocess.run(
        ["git", "log", "-1", "--format=%H", "--", relative],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    commit = log.stdout.strip()
    valid_commit = bool(re.fullmatch(r"[0-9a-f]{40}", commit))
    _require(log.returncode == 0 and valid_commit, "committed S02-P3 result not found", errors)
    if not valid_commit:
        return
    _require(commit != PHASE_BASE_COMMIT, "S02-P3 result commit must differ from base", errors)
    _require(
        subprocess.run(
            ["git", "merge-base", "--is-ancestor", PHASE_BASE_COMMIT, commit],
            cwd=repo_root,
            check=False,
        ).returncode
        == 0,
        "phase base not ancestor of S02-P3 result",
        errors,
    )
    _require(
        subprocess.run(
            ["git", "merge-base", "--is-ancestor", commit, "HEAD"],
            cwd=repo_root,
            check=False,
        ).returncode
        == 0,
        "S02-P3 result not ancestor of HEAD",
        errors,
    )
    committed = subprocess.run(
        ["git", "show", f"{commit}:{relative}"],
        cwd=repo_root,
        capture_output=True,
        check=False,
    )
    _require(
        committed.returncode == 0 and committed.stdout == MANIFEST_PATH.read_bytes(),
        "committed S02-P3 manifest differs from worktree",
        errors,
    )


def validate_v015_s02_p3_scope_gate(
    manifest_path: Path = MANIFEST_PATH,
    *,
    source_package: Path = DEFAULT_SOURCE_PACKAGE,
    require_exact_rebuild: bool = True,
    require_clean_worktree: bool = False,
    repo_root: Path = REPO_ROOT,
) -> dict[str, Any]:
    errors: list[str] = []
    manifest = _read_json(Path(manifest_path))
    _validate_manifest(manifest, errors)
    _require(Path(source_package).is_file(), "source package missing", errors)
    if Path(source_package).is_file():
        _require(_sha256(Path(source_package)) == SOURCE_PACKAGE_SHA256, "source package SHA drift", errors)
        try:
            load_s02_p3_task_contract(Path(source_package))
        except Exception as error:
            errors.append("source contract invalid: " + str(error))
    _validate_core_artifacts(Path(source_package), errors)
    _validate_artifact_integrity(manifest, errors)
    _validate_governance(errors)
    _validate_events(manifest, errors)
    _validate_receipts(errors)
    _validate_public_safe(errors)
    _validate_phase_diff_allowlist(Path(repo_root), errors)
    if require_exact_rebuild:
        _validate_exact_rebuild(manifest, Path(source_package), errors)
    if require_clean_worktree:
        _validate_clean_result(Path(repo_root), errors)
    if errors:
        raise ValidationError("\n".join(errors))
    return manifest


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    parser.add_argument("--source-package", type=Path, default=DEFAULT_SOURCE_PACKAGE)
    parser.add_argument(
        "--skip-exact-rebuild",
        action="store_true",
        help="development-only escape hatch; result is NON_STRICT_PASS",
    )
    parser.add_argument("--require-clean-worktree", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = validate_v015_s02_p3_scope_gate(
            args.manifest,
            source_package=args.source_package,
            require_exact_rebuild=not args.skip_exact_rebuild,
            require_clean_worktree=args.require_clean_worktree,
        )
    except (
        OSError,
        ValueError,
        KeyError,
        json.JSONDecodeError,
        zipfile.BadZipFile,
        ValidationError,
    ) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    label = "NON_STRICT_PASS" if args.skip_exact_rebuild else "PASS"
    print(
        f"{label}: KMFA v1.5 S02-P3 scope gate validated; "
        f"phase={result['phase_result']['acceptance_status']}; "
        f"active_phase={_top_level_scalar(PROJECT_GOVERNANCE_PATH.read_text(encoding='utf-8'), 'current_phase_id')}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
