#!/usr/bin/env python3
"""Validate the fail-closed KMFA v1.5 S01 Stage review remediation."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = REPO_ROOT / "KMFA"
ARTIFACT_ROOT = PROJECT_ROOT / "stage_artifacts/V015_S01_STAGE_REVIEW"
MANIFEST_PATH = ARTIFACT_ROOT / "machine/stage1_review_manifest.json"
MATRIX_PATH = ARTIFACT_ROOT / "machine/stage1_review_matrix_public_safe.json"
FINDINGS_PATH = ARTIFACT_ROOT / "machine/stage1_review_findings_public_safe.csv"
CONTRACTS_PATH = ARTIFACT_ROOT / "machine/cross_phase_contracts_public_safe.json"
VALIDATION_RESULTS_PATH = ARTIFACT_ROOT / "machine/validation_results.jsonl"
ROADMAP_SOURCE_PATH = PROJECT_ROOT / "taskpack/v1_5/roadmap_v2_0.json"
SOURCE_MANIFEST_PATH = PROJECT_ROOT / "taskpack/v1_5/source_manifest.json"
PROJECT_GOVERNANCE_PATH = PROJECT_ROOT / "docs/governance/project.yaml"
ROADMAP_GOVERNANCE_PATH = PROJECT_ROOT / "docs/governance/roadmap.yaml"
AGENTS_PATH = PROJECT_ROOT / "AGENTS.md"
EVENTS_PATH = PROJECT_ROOT / "docs/governance/events.jsonl"
MODEL_SPEC_PATH = PROJECT_ROOT / "docs/governance/MODEL_SPEC.md"
SOURCE_PACKAGE = Path.home() / "Downloads/KMFA_ChatGPT_Stage3_Codex_TaskPack_Roadmap_v2_0_UIUX_FULL_REBUILD.zip"
SOURCE_PACKAGE_SHA256 = "e822c98bfe21445b4ddf7110ecf81d14c8fa8bd5f2cdeb00fab4a21e72df39f8"
REVIEW_BASE_COMMIT = "5aba436c3e7f1a98bb1a3ad88735b8ad2b279d46"
REVIEW_RESULT_COMMIT = "08ce4b2b7c2491b2685bab2f33c32f57de519b1b"
REVIEW_MANIFEST_BYTES = 7553
REVIEW_MANIFEST_SHA256 = "809ec47d052a80a492f1d5e9fdb6a8fe25409cc4e4d494a2afaa0c6a83514c3b"
REVIEW_MANIFEST_CONTENT_HASH = "sha256:542043139b1c4d86bc764f6b0341f205266284d7d119e6bdcf638ab2d17a91bb"
REVIEW_EVENT_SHA256 = {
    "EVENT-KMFA-20260713-V015-S01-STAGE-REVIEW-REMEDIATION-GOVERNANCE-SYNC": "9ca385645f756c5283e1a70b9152a7122f783c114226552d8847af71add177b5",
    "EVENT-KMFA-20260713-V015-S01-STAGE-REVIEW-FINAL-VALIDATION": "1933b0d5a15964b38e5ede3396b31459dbb8d5db78cfcdc9c17f6ba4d801d6b9",
}

P1_MANIFEST_REF = "KMFA/stage_artifacts/V015_S01_P1_LEGACY_REFERENCE_BASELINE_FREEZE/machine/s01_p1_legacy_reference_baseline_manifest.json"
P2_MANIFEST_REF = "KMFA/stage_artifacts/V015_S01_P2_IMPLEMENTATION_SPEC_GAP_INVENTORY/machine/s01_p2_implementation_spec_gap_inventory_manifest.json"
P3_MANIFEST_REF = "KMFA/stage_artifacts/V015_S01_P3_READ_ONLY_AUDIT_GATE/machine/s01_p3_read_only_audit_gate_manifest.json"
PHASE_CONTRACTS = {
    "s01p1": (P1_MANIFEST_REF, "sha256:fb533ea2170880f7ba89d69819ffc5239e0fbdc66c60af46ff22ca9d7fa42452", "NOT_PASSED", "NO_GO"),
    "s01p2": (P2_MANIFEST_REF, "sha256:0b73988c6a3580dfb4185a7bd55b79f0e0ca767c916772a8f0d0701ede0e5d86", "PASSED", "CONTINUE_TO_S01_P3_ONLY"),
    "s01p3": (P3_MANIFEST_REF, "sha256:e4f33027260dbcac2dbd8fad362ae4c883e516884d368c2f3793c5aaa16b5ef4", "NOT_PASSED", "NO_GO_STAGE_01_REVIEW_REQUIRED"),
}

EXPECTED_ARTIFACT_REFS = {
    "manifest": "KMFA/stage_artifacts/V015_S01_STAGE_REVIEW/machine/stage1_review_manifest.json",
    "review_matrix": "KMFA/stage_artifacts/V015_S01_STAGE_REVIEW/machine/stage1_review_matrix_public_safe.json",
    "review_findings": "KMFA/stage_artifacts/V015_S01_STAGE_REVIEW/machine/stage1_review_findings_public_safe.csv",
    "cross_phase_contracts": "KMFA/stage_artifacts/V015_S01_STAGE_REVIEW/machine/cross_phase_contracts_public_safe.json",
    "review_report": "KMFA/stage_artifacts/V015_S01_STAGE_REVIEW/human/stage1_review_report_zh.md",
    "rollback_plan": "KMFA/stage_artifacts/V015_S01_STAGE_REVIEW/human/rollback_plan_zh.md",
    "test_results": "KMFA/stage_artifacts/V015_S01_STAGE_REVIEW/human/test_results_zh.md",
    "validation_results": "KMFA/stage_artifacts/V015_S01_STAGE_REVIEW/machine/validation_results.jsonl",
}
REQUIRED_INTEGRITY_REFS = set(EXPECTED_ARTIFACT_REFS.values()) - {EXPECTED_ARTIFACT_REFS["manifest"]}
EXPECTED_VALIDATION_IDS = {
    "p1_strict_validator",
    "p2_strict_validator",
    "p3_strict_validator",
    "phase_focused_tests",
    "roadmap_governance_check",
    "roadmap_governance_tests",
    "stage_review_tests",
    "governance_project_check",
    "lean_check",
    "governance_sync_check",
    "no_float_check",
    "no_omission_check",
    "structured_public_diff_checks",
}
EXPECTED_TASKS = {
    "S01P1T01": ("S01-P1", "COMPLETE", "NOT_PASSED", "RUNTIME_NOT_FOUND", True),
    "S01P1T02": ("S01-P1", "STOPPED_BY_CONTRACT", "NOT_PASSED", "STATIC_SAMPLE_ONLY", True),
    "S01P1T03": ("S01-P1", "COMPLETE_WITH_LIMITATIONS", "NOT_PASSED", "PARTIAL_REPO_REBUILDABLE_APP_RESTORE_ONLY", False),
    "S01P2T01": ("S01-P2", "EXECUTION_COMPLETE", "PASSED", "TASK_ACCEPTED", False),
    "S01P2T02": ("S01-P2", "EXECUTION_COMPLETE", "PASSED", "TASK_ACCEPTED", False),
    "S01P2T03": ("S01-P2", "EXECUTION_COMPLETE", "PASSED", "TASK_ACCEPTED", False),
    "S01P3T01": ("S01-P3", "EXECUTION_COMPLETE", "PASSED", "RUNTIME_OBJECT_MISSING", False),
    "S01P3T02": ("S01-P3", "EXECUTION_COMPLETE", "PASSED", "OPEN_RISKS_PLANNED_NOT_RESOLVED", False),
    "S01P3T03": ("S01-P3", "EXECUTION_COMPLETE", "NOT_PASSED", "UNEXPECTED_LOCAL_GIT_STATE_CHANGE_AND_INSUFFICIENT_PREAUDIT_TELEMETRY", True),
}
EXPECTED_PHASES = {
    "S01-P1": ("EXECUTION_COMPLETE", "NOT_PASSED", 0, 3),
    "S01-P2": ("EXECUTION_COMPLETE", "PASSED", 3, 3),
    "S01-P3": ("EXECUTION_COMPLETE", "NOT_PASSED", 2, 3),
}
EXPECTED_REVIEW_FINDINGS = {f"S01REV-RD-{index:03d}" for index in range(1, 18)}
EXPECTED_INHERITED_FINDINGS = {f"S01REV-IB-{index:03d}" for index in range(1, 6)}
EXPECTED_CONTRACTS = {f"S01REV-C{index:02d}" for index in range(1, 19)}
MUTATION_TEST_PATHS = tuple((PROJECT_ROOT / "tests").glob("test_v015_s01_*.py"))


class ValidationError(RuntimeError):
    pass


def _require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValidationError(f"expected JSON object: {path}")
    return value


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValidationError(f"expected JSON object at {path}:{number}")
        rows.append(value)
    return rows


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical_content_hash(value: dict[str, Any]) -> str:
    payload = dict(value)
    payload.pop("content_hash", None)
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _is_safe_repo_ref(ref: Any, *, require_exists: bool = True) -> bool:
    if not isinstance(ref, str) or not ref.strip():
        return False
    relative = Path(ref)
    if relative.is_absolute() or ".." in relative.parts or not relative.parts or relative.parts[0] != "KMFA":
        return False
    repo = REPO_ROOT.resolve()
    resolved = (repo / relative).resolve()
    try:
        resolved.relative_to(repo)
    except ValueError:
        return False
    return resolved != repo and (not require_exists or resolved.exists())


def _validate_evidence_refs(refs: Any, label: str, errors: list[str]) -> None:
    _require(isinstance(refs, list) and bool(refs), f"{label}: evidence refs missing", errors)
    if not isinstance(refs, list):
        return
    _require(len(refs) == len(set(map(str, refs))), f"{label}: duplicate evidence refs", errors)
    for ref in refs:
        _require(_is_safe_repo_ref(ref), f"{label}: unsafe or missing evidence ref {ref}", errors)


def _validate_phase_dependencies(manifest: dict[str, Any], errors: list[str]) -> None:
    dependencies = manifest.get("phase_evidence", [])
    by_phase = {
        str(item.get("phase_id", "")).lower().replace("-", ""): item
        for item in dependencies
        if isinstance(item, dict)
    } if isinstance(dependencies, list) else {}
    _require(isinstance(dependencies, list) and len(dependencies) == len(by_phase) == 3, "phase evidence must contain three unique rows", errors)
    _require(set(by_phase) == set(PHASE_CONTRACTS), "phase evidence ID set mismatch", errors)
    for phase, (ref, content_hash, acceptance, _) in PHASE_CONTRACTS.items():
        item = by_phase.get(phase, {})
        _require(item.get("manifest_ref") == ref, f"{phase}: manifest ref mismatch", errors)
        _require(item.get("manifest_content_hash") == content_hash, f"{phase}: content hash binding mismatch", errors)
        _require(item.get("acceptance_status") == acceptance, f"{phase}: acceptance drift", errors)
        expected_accepted = {"s01p1": 0, "s01p2": 3, "s01p3": 2}[phase]
        _require(item.get("execution_status") == "EXECUTION_COMPLETE", f"{phase}: execution status drift", errors)
        _require(item.get("accepted_tasks") == expected_accepted and item.get("total_tasks") == 3, f"{phase}: task count drift", errors)
        phase_path = REPO_ROOT / ref
        _require(phase_path.is_file(), f"{phase}: dependency manifest missing", errors)
        if phase_path.is_file():
            phase_manifest = _read_json(phase_path)
            _require(phase_manifest.get("content_hash") == content_hash, f"{phase}: live manifest hash drift", errors)
            _require(phase_manifest.get("content_hash") == _canonical_content_hash(phase_manifest), f"{phase}: invalid live manifest content hash", errors)
            _require(item.get("manifest_bytes") == phase_path.stat().st_size, f"{phase}: manifest byte binding mismatch", errors)
            _require(item.get("manifest_sha256") == _sha256(phase_path), f"{phase}: manifest SHA-256 binding mismatch", errors)


def _validate_matrix(matrix: dict[str, Any], errors: list[str]) -> None:
    _require(matrix.get("schema_version") == "kmfa.v015.s01_stage_review_matrix.v1", "matrix schema mismatch", errors)
    _require(matrix.get("project_id") == "KMFA" and matrix.get("target_release") == "v1.5", "matrix identity mismatch", errors)
    _require(matrix.get("stage_id") == "S01" and matrix.get("review_base_commit") == REVIEW_BASE_COMMIT, "matrix Stage/base mismatch", errors)
    _require(matrix.get("task_status_accounted_count") == 9, "matrix task count mismatch", errors)
    _require(matrix.get("task_acceptance_passed_count") == 5, "matrix accepted count mismatch", errors)
    _require(matrix.get("task_acceptance_not_passed_count") == 4, "matrix not-passed count mismatch", errors)
    _require(matrix.get("triggered_stop_condition_count") == 3, "matrix stop count mismatch", errors)
    rows = matrix.get("tasks", [])
    rows_by_id = {row.get("task_id"): row for row in rows if isinstance(row, dict)} if isinstance(rows, list) else {}
    _require(isinstance(rows, list) and len(rows) == len(rows_by_id) == 9, "matrix must contain nine unique tasks", errors)
    _require(set(rows_by_id) == set(EXPECTED_TASKS), "matrix task ID set mismatch", errors)
    for task_id, expected in EXPECTED_TASKS.items():
        item = rows_by_id.get(task_id, {})
        actual = (
            item.get("phase_id"), item.get("execution_status"), item.get("acceptance_status"),
            item.get("terminal_finding"), item.get("stop_condition_triggered"),
        )
        _require(actual == expected, f"{task_id}: task review facts drift", errors)
        _validate_evidence_refs(item.get("evidence_refs"), task_id, errors)
    phase_rows = matrix.get("phase_summaries", [])
    phases = {row.get("phase_id"): row for row in phase_rows if isinstance(row, dict)} if isinstance(phase_rows, list) else {}
    _require(len(phase_rows) == len(phases) == 3 and set(phases) == set(EXPECTED_PHASES), "phase summary set mismatch", errors)
    for phase_id, expected in EXPECTED_PHASES.items():
        item = phases.get(phase_id, {})
        actual = (item.get("execution_status"), item.get("acceptance_status"), item.get("accepted_tasks"), item.get("total_tasks"))
        _require(actual == expected, f"{phase_id}: phase summary drift", errors)
    result = matrix.get("stage_result", {})
    expected_result = {
        "review_execution_status": "EXECUTION_COMPLETE",
        "evidence_validation_status": "PASS",
        "stage_lifecycle_status": "BLOCKED",
        "stage_acceptance_status": "NOT_PASSED",
        "decision": "NO_GO",
        "s02_entry_allowed": False,
    }
    _require(result == expected_result, "matrix Stage result must remain fail-closed", errors)


def _available_mutation_test_ids() -> set[str]:
    pattern = re.compile(r"^\s*def\s+(test_[A-Za-z0-9_]+)\s*\(", re.MULTILINE)
    return {
        match.group(1)
        for path in MUTATION_TEST_PATHS
        for match in pattern.finditer(path.read_text(encoding="utf-8"))
    }


def _validate_findings(rows: list[dict[str, str]], errors: list[str]) -> None:
    ids = [row.get("finding_id", "") for row in rows]
    _require(len(rows) == len(set(ids)) == 22, "findings must contain 22 unique rows", errors)
    _require(set(ids) == EXPECTED_REVIEW_FINDINGS | EXPECTED_INHERITED_FINDINGS, "finding ID set mismatch", errors)
    mutation_test_ids = [
        row.get("mutation_test_id", "").strip()
        for row in rows
        if row.get("finding_id", "") in EXPECTED_REVIEW_FINDINGS
    ]
    _require(len(mutation_test_ids) == len(set(mutation_test_ids)), "review defect mutation test IDs must be unique", errors)
    available_tests = _available_mutation_test_ids()
    for row in rows:
        finding_id = row.get("finding_id", "")
        refs = [item.strip() for item in row.get("evidence_refs", "").split(";") if item.strip()]
        _validate_evidence_refs(refs, finding_id, errors)
        if finding_id in EXPECTED_REVIEW_FINDINGS:
            _require(row.get("finding_class") == "REVIEW_DEFECT", f"{finding_id}: class mismatch", errors)
            _require(row.get("status") == "FIXED_VALIDATED", f"{finding_id}: review defect not fixed", errors)
            _require(bool(row.get("mutation_test_id", "").strip()), f"{finding_id}: mutation test missing", errors)
            _require(row.get("mutation_test_id", "").strip() in available_tests, f"{finding_id}: mutation test method does not exist", errors)
            _require(row.get("blocks_stage_pass") == "false" and row.get("blocks_s02_entry") == "false", f"{finding_id}: review defect block flags mismatch", errors)
        else:
            _require(row.get("finding_class") in {"INHERITED_ACCEPTANCE_BLOCKER", "INHERITED_TRANSITION_BLOCKER"}, f"{finding_id}: inherited class mismatch", errors)
            _require(row.get("status") == "OPEN_BLOCKING", f"{finding_id}: inherited blocker falsely closed", errors)
            _require(not row.get("mutation_test_id", "").strip(), f"{finding_id}: inherited blocker must not masquerade as remediated", errors)
            _require(row.get("blocks_stage_pass") == "true" and row.get("blocks_s02_entry") == "true", f"{finding_id}: blocker flags mismatch", errors)


def _validate_contracts(contracts: dict[str, Any], errors: list[str]) -> None:
    _require(contracts.get("schema_version") == "kmfa.v015.s01_cross_phase_contracts.v1", "contracts schema mismatch", errors)
    rows = contracts.get("contracts", [])
    by_id = {row.get("contract_id"): row for row in rows if isinstance(row, dict)} if isinstance(rows, list) else {}
    _require(isinstance(rows, list) and len(rows) == len(by_id) == 18, "contracts must contain 18 unique rows", errors)
    _require(set(by_id) == EXPECTED_CONTRACTS, "cross-phase contract ID set mismatch", errors)
    _require(all(row.get("result") == "PASS" and str(row.get("observed", "")).strip() for row in rows), "cross-phase contracts must all be evidenced PASS", errors)
    _require("17" in str(by_id.get("S01REV-C14", {}).get("observed", "")), "review-defect contract count drift", errors)
    _require("5" in str(by_id.get("S01REV-C15", {}).get("observed", "")), "inherited-blocker contract count drift", errors)
    _require("BLOCKED/NOT_PASSED/NO_GO" in str(by_id.get("S01REV-C16", {}).get("observed", "")), "negative Stage gate contract drift", errors)
    _require("false" in str(by_id.get("S01REV-C17", {}).get("observed", "")).lower(), "S02 contract must remain false", errors)
    c18 = str(by_id.get("S01REV-C18", {}).get("observed", ""))
    _require("IMPLEMENT" in c18 and "STAGE_REVIEW_REMEDIATION" in c18, "review-remediation run contract drift", errors)


def _validate_roadmap(roadmap: dict[str, Any], source_manifest: dict[str, Any], errors: list[str]) -> None:
    _require((roadmap.get("stage_count"), roadmap.get("phase_count"), roadmap.get("task_count")) == (24, 72, 216), "roadmap declared counts mismatch", errors)
    stages = roadmap.get("stages", [])
    stage_ids: list[str] = []
    phase_ids: list[str] = []
    task_ids: list[str] = []
    if isinstance(stages, list):
        for stage in stages:
            stage_id = str(stage.get("id", ""))
            stage_ids.append(stage_id)
            for phase in stage.get("phases", []):
                phase_id = str(phase.get("id", ""))
                phase_ids.append(f"{stage_id}-{phase_id}")
                for task in phase.get("tasks", []):
                    task_ids.append(f"{stage_id}{phase_id}{task.get('id', '')}")
    _require(stage_ids == [f"S{index:02d}" for index in range(1, 25)], "roadmap Stage identity/order mismatch", errors)
    _require(len(phase_ids) == len(set(phase_ids)) == 72, "roadmap phase identity mismatch", errors)
    _require(len(task_ids) == len(set(task_ids)) == 216, "roadmap task identity mismatch", errors)
    _require(set(task_ids) == {f"S{stage:02d}P{phase}T{task:02d}" for stage in range(1, 25) for phase in range(1, 4) for task in range(1, 4)}, "roadmap task set mismatch", errors)
    expected_source = {
        "schema_version": "kmfa.v015.taskpack_source_manifest.v1",
        "project_id": "KMFA",
        "target_release": "v1.5",
        "source_package_file": SOURCE_PACKAGE.name,
        "source_package_sha256": SOURCE_PACKAGE_SHA256,
        "roadmap_member": "KMFA_ChatGPT_Stage3_UIUX_REBUILD_Delivery_v2_0/02B_KMFA_Codex_Development_Roadmap_v2_0.json",
        "roadmap_sha256": "a0efdddc6e54a167751938353f71bb60a9cd4b43cbcf444d4c915a45b8b1ec06",
        "stage_count": 24,
        "phase_count": 72,
        "task_count": 216,
    }
    _require(source_manifest == expected_source, "tracked TaskPack source manifest mismatch", errors)


def _top_level_yaml_scalar(text: str, key: str) -> str | None:
    match = re.search(rf"^{re.escape(key)}:\s*(.+?)\s*$", text, re.MULTILINE)
    if not match:
        return None
    value = match.group(1).strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'\"', "'"}:
        return value[1:-1]
    return value


def _is_legal_current_v15_position(stage_id: str | None, phase_id: str | None) -> bool:
    if stage_id == "S01":
        return phase_id in {"V015_S01_STAGE_REVIEW", "V015_S01_CONTROLLED_TRANSITION_AMENDMENT"}
    if not stage_id or not phase_id or not re.fullmatch(r"S(?:0[2-9]|1[0-9]|2[0-4])", stage_id):
        return False
    if re.fullmatch(rf"{stage_id}-P[1-3]", phase_id):
        return True
    if re.fullmatch(rf"V015_{stage_id}_[A-Z0-9_]+", phase_id):
        return True
    return stage_id == "S24" and phase_id in {
        "V015_FINAL_OVERALL_REVIEW",
        "V015_ONE_TIME_GITHUB_MAIN_UPLOAD",
        "V015_APP_REINSTALL_AND_PARITY",
    }


def _validate_historical_stage_result(text: str, *, current_is_review: bool, label: str, errors: list[str]) -> None:
    prefix = "" if current_is_review else "s01_stage_review_"
    expected = {
        f"{prefix}lifecycle_status": "BLOCKED",
        f"{prefix}acceptance_status": "NOT_PASSED",
        f"{prefix}decision": "NO_GO",
        f"{prefix}s02_entry_allowed": "false",
    }
    for key, value in expected.items():
        _require(_top_level_yaml_scalar(text, key) == value, f"{label} historical Stage review fact drift: {key}", errors)


def _validate_governance(project_text: str, roadmap_text: str, agents_text: str, model_spec_text: str, errors: list[str]) -> None:
    _require(_top_level_yaml_scalar(project_text, "target_version") == "v1.5", "project target version drift", errors)
    _require(_top_level_yaml_scalar(roadmap_text, "target_release") == "v1.5", "roadmap target release drift", errors)
    for key, expected in (("active_stage_count", "24"), ("active_phase_count", "72"), ("active_task_count", "216")):
        _require(_top_level_yaml_scalar(roadmap_text, key) == expected, f"roadmap governance count drift: {key}", errors)
    for key, expected in (("stage_count", 24), ("phase_count", 72), ("task_count", 216)):
        _require(
            bool(re.search(rf"^  {key}: {expected}\s*$", roadmap_text, re.MULTILINE)),
            f"active roadmap count drift: {key}",
            errors,
        )

    project_stage = _top_level_yaml_scalar(project_text, "current_stage_id")
    project_phase = _top_level_yaml_scalar(project_text, "current_phase_id")
    roadmap_stage = _top_level_yaml_scalar(roadmap_text, "current_stage_id")
    roadmap_phase = _top_level_yaml_scalar(roadmap_text, "current_phase_id")
    _require((project_stage, project_phase) == (roadmap_stage, roadmap_phase), "project/roadmap current v1.5 position mismatch", errors)
    _require(_is_legal_current_v15_position(project_stage, project_phase), "current v1.5 governance position is not a legal Stage-review successor", errors)
    if project_phase:
        _require(f'  current_phase_id: "{project_phase}"' in roadmap_text, "active roadmap current phase drift", errors)

    current_is_review = project_phase == "V015_S01_STAGE_REVIEW"
    _validate_historical_stage_result(project_text, current_is_review=current_is_review, label="project", errors=errors)
    _validate_historical_stage_result(roadmap_text, current_is_review=current_is_review, label="roadmap", errors=errors)
    if current_is_review:
        _require(_top_level_yaml_scalar(project_text, "next_gate_id") == "S01_CONTROLLED_TRANSITION_AMENDMENT", "project review next gate drift", errors)
        _require(_top_level_yaml_scalar(roadmap_text, "next_gate_id") == "S01_CONTROLLED_TRANSITION_AMENDMENT", "roadmap review next gate drift", errors)

    for token in ("Stage 1-24", "不得按单个 Stage 做 GitHub upload gate", SOURCE_PACKAGE_SHA256):
        _require(token in agents_text, f"AGENTS token missing: {token}", errors)
    _require("review_defect_count == 17" in model_spec_text, "MODEL_SPEC review formula count drift", errors)
    _require("17 个 review defects" in model_spec_text, "MODEL_SPEC review rationale count drift", errors)


def _validate_canonical_events(rows: list[dict[str, Any]], require_final: bool, errors: list[str]) -> None:
    stage_rows = [row for row in rows if row.get("phase_id") == "V015_S01_STAGE_REVIEW"]
    by_id = {str(row.get("event_id", "")): row for row in stage_rows}
    expected_ids = {
        "EVENT-KMFA-20260713-V015-S01-STAGE-REVIEW-REMEDIATION-GOVERNANCE-SYNC",
        "EVENT-KMFA-20260713-V015-S01-STAGE-REVIEW-FINAL-VALIDATION",
    }
    _require(len(stage_rows) == len(by_id) == 2 and set(by_id) == expected_ids, "canonical Stage review event history drift", errors)
    shared_expected = {
        "project_id": "KMFA",
        "phase_id": "V015_S01_STAGE_REVIEW",
        "run_mode": "IMPLEMENT",
        "work_kind": "STAGE_REVIEW_REMEDIATION",
        "review_execution_status": "EXECUTION_COMPLETE",
        "stage_lifecycle_status": "BLOCKED",
        "stage_acceptance_status": "NOT_PASSED",
        "decision": "NO_GO",
        "s02_entry_allowed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "accepted_task_count": 5,
        "not_passed_task_count": 4,
        "triggered_stop_condition_count": 3,
        "next_gate_id": "S01_CONTROLLED_TRANSITION_AMENDMENT",
    }
    for event_id in expected_ids:
        event = by_id.get(event_id, {})
        _require({key: event.get(key) for key in shared_expected} == shared_expected, f"canonical Stage review event facts drift: {event_id}", errors)
        encoded = json.dumps(event, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        _require(hashlib.sha256(encoded).hexdigest() == REVIEW_EVENT_SHA256[event_id], f"canonical Stage review event content drift: {event_id}", errors)
    latest = by_id.get("EVENT-KMFA-20260713-V015-S01-STAGE-REVIEW-FINAL-VALIDATION", {})
    if require_final:
        _require(latest.get("evidence_validation_status") == "PASS", "canonical final event validation status mismatch", errors)
        _require(latest.get("review_defect_count") == 17 and latest.get("inherited_blocker_count") == 5, "canonical final event finding counts mismatch", errors)


def _validate_frozen_canonical_manifest(manifest_path: Path, manifest: dict[str, Any], errors: list[str]) -> None:
    if manifest_path.resolve() != MANIFEST_PATH.resolve():
        return
    _require(manifest.get("content_hash") == REVIEW_MANIFEST_CONTENT_HASH, "canonical Stage review manifest content hash drift", errors)
    _require(manifest_path.stat().st_size == REVIEW_MANIFEST_BYTES, "canonical Stage review manifest byte count drift", errors)
    _require(_sha256(manifest_path) == REVIEW_MANIFEST_SHA256, "canonical Stage review manifest SHA-256 drift", errors)
    relative_manifest = MANIFEST_PATH.relative_to(REPO_ROOT).as_posix()
    committed = subprocess.run(
        ["git", "show", f"{REVIEW_RESULT_COMMIT}:{relative_manifest}"],
        cwd=REPO_ROOT,
        capture_output=True,
        check=False,
    )
    _require(committed.returncode == 0 and committed.stdout == manifest_path.read_bytes(), "canonical Stage review manifest is not frozen to result commit", errors)
    ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", REVIEW_RESULT_COMMIT, "HEAD"],
        cwd=REPO_ROOT,
        capture_output=True,
        check=False,
    )
    _require(ancestor.returncode == 0, "Stage review result commit is not in current history", errors)


def _validate_artifact_integrity(
    manifest: dict[str, Any],
    path_overrides: dict[str, Path],
    errors: list[str],
) -> None:
    refs = manifest.get("artifact_refs", {})
    _require(refs == EXPECTED_ARTIFACT_REFS, "manifest artifact refs mismatch", errors)
    integrity_rows = manifest.get("artifact_integrity", [])
    integrity = {
        str(item.get("ref", "")): item
        for item in integrity_rows
        if isinstance(item, dict)
    } if isinstance(integrity_rows, list) else {}
    _require(isinstance(integrity_rows, list) and len(integrity_rows) == len(integrity), "artifact_integrity must contain unique rows", errors)
    if not isinstance(integrity_rows, list):
        return
    _require(REQUIRED_INTEGRITY_REFS.issubset(set(integrity)), "required artifact integrity bindings missing", errors)
    _require(set(integrity).issubset(set(EXPECTED_ARTIFACT_REFS.values())), "unknown artifact integrity binding", errors)
    for ref, expected in integrity.items():
        _require(set(expected) == {"ref", "bytes", "sha256"}, f"{ref}: artifact integrity shape mismatch", errors)
        path = path_overrides.get(ref, REPO_ROOT / ref)
        _require(path.is_file(), f"{ref}: artifact missing", errors)
        if not path.is_file() or not isinstance(expected, dict):
            continue
        _require(expected.get("bytes") == path.stat().st_size, f"{ref}: byte count mismatch", errors)
        _require(expected.get("sha256") == _sha256(path), f"{ref}: SHA-256 mismatch", errors)


def _validate_receipts(rows: list[dict[str, Any]], require_pass: bool, errors: list[str]) -> None:
    ids = [str(row.get("validation_id", "")) for row in rows]
    _require(len(rows) == len(set(ids)), "duplicate validation receipt ID", errors)
    _require(set(ids) == EXPECTED_VALIDATION_IDS, "validation receipt ID set mismatch", errors)
    for row in rows:
        validation_id = row.get("validation_id", "unknown")
        _require(str(row.get("command", "")).strip(), f"{validation_id}: command missing", errors)
        _require(row.get("result") in ({"PASS"} if require_pass else {"PASS", "PENDING"}), f"{validation_id}: invalid validation result", errors)
        if row.get("result") == "PASS":
            _require(row.get("exit_code") == 0, f"{validation_id}: PASS receipt exit code mismatch", errors)
        else:
            _require(row.get("exit_code") is None, f"{validation_id}: PENDING receipt must not claim exit code", errors)


def validate_v015_s01_stage_review(
    manifest_path: Path = MANIFEST_PATH,
    *,
    matrix_path: Path = MATRIX_PATH,
    findings_path: Path = FINDINGS_PATH,
    contracts_path: Path = CONTRACTS_PATH,
    validation_results_path: Path = VALIDATION_RESULTS_PATH,
    roadmap_source_path: Path = ROADMAP_SOURCE_PATH,
    source_manifest_path: Path = SOURCE_MANIFEST_PATH,
    project_governance_path: Path = PROJECT_GOVERNANCE_PATH,
    roadmap_governance_path: Path = ROADMAP_GOVERNANCE_PATH,
    agents_path: Path = AGENTS_PATH,
    events_path: Path = EVENTS_PATH,
    model_spec_path: Path = MODEL_SPEC_PATH,
    source_package: Path | None = SOURCE_PACKAGE,
    require_source_package: bool = False,
    require_validation_receipts: bool = False,
    require_clean_worktree: bool = False,
    require_dependency_validators: bool = False,
) -> dict[str, Any]:
    errors: list[str] = []
    manifest = _read_json(manifest_path)
    matrix = _read_json(matrix_path)
    findings = _read_csv(findings_path)
    contracts = _read_json(contracts_path)
    receipts = _read_jsonl(validation_results_path)
    roadmap = _read_json(roadmap_source_path)
    source_manifest = _read_json(source_manifest_path)
    canonical_events = _read_jsonl(events_path)

    _require(manifest.get("schema_version") == "kmfa.v015.s01_stage_review.v1", "manifest schema mismatch", errors)
    _require(manifest.get("project_id") == "KMFA" and manifest.get("target_release") == "v1.5", "manifest identity mismatch", errors)
    _require(manifest.get("stage_id") == "S01" and manifest.get("review_base_commit") == REVIEW_BASE_COMMIT, "manifest Stage/base mismatch", errors)
    _require(manifest.get("run_mode") == "IMPLEMENT", "review run_mode must be IMPLEMENT", errors)
    _require(manifest.get("work_kind") == "STAGE_REVIEW_REMEDIATION", "review work_kind mismatch", errors)
    _require(manifest.get("content_hash") == _canonical_content_hash(manifest), "manifest content hash mismatch", errors)
    _validate_frozen_canonical_manifest(manifest_path, manifest, errors)
    source = manifest.get("source_package", {})
    _require(source == {
        "name": SOURCE_PACKAGE.name,
        "bytes": 118652,
        "sha256": SOURCE_PACKAGE_SHA256,
        "taskpack_version": "v2.0",
        "roadmap_stage_count": 24,
        "roadmap_phase_count": 72,
        "roadmap_task_count": 216,
    }, "manifest source package/count binding mismatch", errors)
    _validate_phase_dependencies(manifest, errors)

    _require(manifest.get("task_accounting") == {
        "total": 9, "accepted": 5, "not_accepted": 4,
        "triggered_stop_conditions": 3, "all_tasks_explicitly_indexed": True,
    }, "manifest task accounting mismatch", errors)
    _require(manifest.get("review_findings") == {
        "total": 22, "review_defect_total": 17, "review_defect_fixed_validated": 17,
        "review_defect_open": 0, "inherited_blocker_total": 5,
        "inherited_blocker_open_blocking": 5,
    }, "manifest review finding summary mismatch", errors)
    _require(manifest.get("open_risk_plan") == {
        "total": 24, "p0": 18, "p1": 6, "p0_plan_gap_count": 0,
        "risks_resolved_by_review": False,
    }, "manifest open risk plan mismatch", errors)
    expected_stage_result = {
        "review_execution_status": "EXECUTION_COMPLETE",
        "evidence_validation_status": "PASS",
        "stage_lifecycle_status": "BLOCKED",
        "stage_acceptance_status": "NOT_PASSED",
        "decision": "NO_GO",
        "s02_entry_allowed": False,
    }
    stage_gate = manifest.get("stage_gate", {})
    _require({key: stage_gate.get(key) for key in expected_stage_result} == expected_stage_result, "manifest Stage result must remain fail-closed", errors)
    _require(stage_gate.get("final_validation_status") in ({"PASS"} if require_validation_receipts else {"PASS", "PENDING"}), "manifest final validation state mismatch", errors)
    _require(set(stage_gate) == set(expected_stage_result) | {"final_validation_status"}, "manifest Stage gate key set mismatch", errors)
    _require(manifest.get("next_gate") == {
        "next_allowed_run": "S01_CONTROLLED_TRANSITION_AMENDMENT",
        "existing_full_rebuild_objective_is_scope_authority": True,
        "additional_owner_authorization_requested": False,
        "stage_history_must_remain_blocked_not_passed_no_go": True,
        "amendment_is_stage_pass": False,
    }, "next run must remain controlled S01 transition amendment", errors)
    _require(manifest.get("downstream_actions") == {
        "s02_started": False,
        "product_runtime_implementation_performed": False,
        "api_implementation_performed": False,
        "database_implementation_performed": False,
        "ui_implementation_performed": False,
        "business_execution_performed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "raw_inbox_mutated": False,
    }, "downstream action boundary drift", errors)
    correction = manifest.get("review_correction_binding", {})
    _require(correction.get("correction_kind") == "REVIEW_REMEDIATION_NOT_SILENT_HISTORICAL_REWRITE", "review correction kind mismatch", errors)
    _require(correction.get("historical_phase_conclusions_preserved") is True, "historical phase conclusions not preserved", errors)
    _require(correction.get("focused_mutation_test_counts") == {"s01_p1": 13, "s01_p2": 28, "s01_p3": 56, "total": 97}, "phase mutation test count binding mismatch", errors)
    corrected_refs = correction.get("corrected_validator_and_test_refs", [])
    _require(isinstance(corrected_refs, list) and len(corrected_refs) == 6 and len(set(corrected_refs)) == 6, "corrected validator/test refs mismatch", errors)
    if isinstance(corrected_refs, list):
        for ref in corrected_refs:
            _require(_is_safe_repo_ref(ref), f"unsafe corrected validator/test ref: {ref}", errors)
    human_refs = correction.get("corrected_human_test_result_refs", [])
    _require(isinstance(human_refs, list) and len(human_refs) == 3 and len(set(human_refs)) == 3, "corrected human result refs mismatch", errors)
    if isinstance(human_refs, list):
        for ref in human_refs:
            _require(_is_safe_repo_ref(ref), f"unsafe corrected human result ref: {ref}", errors)

    _validate_matrix(matrix, errors)
    _validate_findings(findings, errors)
    _validate_contracts(contracts, errors)
    _validate_roadmap(roadmap, source_manifest, errors)
    _validate_governance(
        project_governance_path.read_text(encoding="utf-8"),
        roadmap_governance_path.read_text(encoding="utf-8"),
        agents_path.read_text(encoding="utf-8"),
        model_spec_path.read_text(encoding="utf-8"),
        errors,
    )
    _validate_canonical_events(canonical_events, require_validation_receipts, errors)
    path_overrides = {
        EXPECTED_ARTIFACT_REFS["review_matrix"]: matrix_path,
        EXPECTED_ARTIFACT_REFS["review_findings"]: findings_path,
        EXPECTED_ARTIFACT_REFS["cross_phase_contracts"]: contracts_path,
        EXPECTED_ARTIFACT_REFS["validation_results"]: validation_results_path,
    }
    _validate_artifact_integrity(manifest, path_overrides, errors)
    _validate_receipts(receipts, require_validation_receipts, errors)

    package_available = source_package is not None and source_package.is_file()
    if require_source_package:
        _require(package_available, "source package required but missing", errors)
    if package_available:
        _require(_sha256(source_package) == SOURCE_PACKAGE_SHA256, "source package SHA-256 mismatch", errors)

    if require_dependency_validators:
        commands = [
            [sys.executable, "-B", "KMFA/tools/check_v015_s01_p1_legacy_reference_baseline.py"],
            [sys.executable, "-B", "KMFA/tools/check_v015_s01_p2_implementation_spec_gap_inventory.py"],
            [sys.executable, "-B", "KMFA/tools/check_v015_s01_p3_read_only_audit_gate.py"],
            [sys.executable, "-B", "KMFA/tools/v015_roadmap_governance_sync.py", "--check"],
        ]
        for command in commands:
            result = subprocess.run(command, cwd=REPO_ROOT, capture_output=True, text=True, check=False)
            _require(result.returncode == 0, f"dependency validator failed: {' '.join(command)}: {result.stdout}{result.stderr}", errors)

    if require_clean_worktree:
        status = subprocess.run(["git", "status", "--short"], cwd=REPO_ROOT, capture_output=True, text=True, check=False)
        _require(status.returncode == 0 and not status.stdout.strip(), "Git worktree must be clean", errors)
        relative_manifest = manifest_path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()
        result_commit = subprocess.run(["git", "log", "-1", "--format=%H", "--", relative_manifest], cwd=REPO_ROOT, capture_output=True, text=True, check=False).stdout.strip()
        _require(bool(re.fullmatch(r"[0-9a-f]{40}", result_commit)), "committed Stage review result not found", errors)
        if result_commit:
            ancestor = subprocess.run(["git", "merge-base", "--is-ancestor", REVIEW_BASE_COMMIT, result_commit], cwd=REPO_ROOT, check=False)
            _require(ancestor.returncode == 0 and result_commit != REVIEW_BASE_COMMIT, "Stage review result commit ancestry mismatch", errors)
            committed = subprocess.run(["git", "show", f"{result_commit}:{relative_manifest}"], cwd=REPO_ROOT, capture_output=True, check=False)
            _require(committed.returncode == 0 and committed.stdout == manifest_path.read_bytes(), "committed Stage review manifest differs from worktree", errors)

    if errors:
        raise ValidationError("\n".join(errors))
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    parser.add_argument("--matrix", type=Path, default=MATRIX_PATH)
    parser.add_argument("--findings", type=Path, default=FINDINGS_PATH)
    parser.add_argument("--contracts", type=Path, default=CONTRACTS_PATH)
    parser.add_argument("--validation-results", type=Path, default=VALIDATION_RESULTS_PATH)
    parser.add_argument("--require-source-package", action="store_true")
    parser.add_argument("--require-validation-receipts", action="store_true")
    parser.add_argument("--require-clean-worktree", action="store_true")
    parser.add_argument("--require-dependency-validators", action="store_true")
    args = parser.parse_args()
    try:
        result = validate_v015_s01_stage_review(
            args.manifest,
            matrix_path=args.matrix,
            findings_path=args.findings,
            contracts_path=args.contracts,
            validation_results_path=args.validation_results,
            require_source_package=args.require_source_package,
            require_validation_receipts=args.require_validation_receipts,
            require_clean_worktree=args.require_clean_worktree,
            require_dependency_validators=args.require_dependency_validators,
        )
    except (OSError, ValueError, json.JSONDecodeError, ValidationError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    print(
        "PASS: KMFA v1.5 S01 Stage review remediation validated; "
        f"Stage={result['stage_gate']['stage_lifecycle_status']}/"
        f"{result['stage_gate']['stage_acceptance_status']}/"
        f"{result['stage_gate']['decision']}; S02=false"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
