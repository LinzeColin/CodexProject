#!/usr/bin/env python3
"""Validate the fail-closed KMFA v1.5 S01 controlled transition amendment."""

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
ARTIFACT_ROOT = PROJECT_ROOT / "stage_artifacts/V015_S01_CONTROLLED_TRANSITION_AMENDMENT"
MANIFEST_PATH = ARTIFACT_ROOT / "machine/s01_controlled_transition_amendment_manifest.json"
CONTRACT_PATH = ARTIFACT_ROOT / "machine/transition_contract_public_safe.json"
BLOCKER_DISPOSITIONS_PATH = ARTIFACT_ROOT / "machine/blocker_dispositions_public_safe.csv"
VALIDATION_RESULTS_PATH = ARTIFACT_ROOT / "machine/validation_results.jsonl"
STAGE_REVIEW_MANIFEST_PATH = (
    PROJECT_ROOT / "stage_artifacts/V015_S01_STAGE_REVIEW/machine/stage1_review_manifest.json"
)
PROJECT_GOVERNANCE_PATH = PROJECT_ROOT / "docs/governance/project.yaml"
ROADMAP_GOVERNANCE_PATH = PROJECT_ROOT / "docs/governance/roadmap.yaml"
AGENTS_PATH = PROJECT_ROOT / "AGENTS.md"
EVENTS_PATH = PROJECT_ROOT / "docs/governance/events.jsonl"
MODEL_SPEC_PATH = PROJECT_ROOT / "docs/governance/MODEL_SPEC.md"
SOURCE_PACKAGE = Path.home() / "Downloads/KMFA_ChatGPT_Stage3_Codex_TaskPack_Roadmap_v2_0_UIUX_FULL_REBUILD.zip"

SOURCE_PACKAGE_SHA256 = "e822c98bfe21445b4ddf7110ecf81d14c8fa8bd5f2cdeb00fab4a21e72df39f8"
SOURCE_PACKAGE_BYTES = 118652
AMENDMENT_BASE_COMMIT = "08ce4b2b7c2491b2685bab2f33c32f57de519b1b"
STAGE_REVIEW_MANIFEST_REF = (
    "KMFA/stage_artifacts/V015_S01_STAGE_REVIEW/machine/stage1_review_manifest.json"
)
STAGE_REVIEW_CONTENT_HASH = "sha256:542043139b1c4d86bc764f6b0341f205266284d7d119e6bdcf638ab2d17a91bb"
STAGE_REVIEW_SHA256 = "809ec47d052a80a492f1d5e9fdb6a8fe25409cc4e4d494a2afaa0c6a83514c3b"
STAGE_REVIEW_BYTES = 7553

EXPECTED_ARTIFACT_REFS = {
    "manifest": "KMFA/stage_artifacts/V015_S01_CONTROLLED_TRANSITION_AMENDMENT/machine/s01_controlled_transition_amendment_manifest.json",
    "transition_contract": "KMFA/stage_artifacts/V015_S01_CONTROLLED_TRANSITION_AMENDMENT/machine/transition_contract_public_safe.json",
    "blocker_dispositions": "KMFA/stage_artifacts/V015_S01_CONTROLLED_TRANSITION_AMENDMENT/machine/blocker_dispositions_public_safe.csv",
    "report": "KMFA/stage_artifacts/V015_S01_CONTROLLED_TRANSITION_AMENDMENT/human/controlled_transition_amendment_zh.md",
    "rollback_plan": "KMFA/stage_artifacts/V015_S01_CONTROLLED_TRANSITION_AMENDMENT/human/rollback_plan_zh.md",
    "test_results": "KMFA/stage_artifacts/V015_S01_CONTROLLED_TRANSITION_AMENDMENT/human/test_results_zh.md",
    "validation_results": "KMFA/stage_artifacts/V015_S01_CONTROLLED_TRANSITION_AMENDMENT/machine/validation_results.jsonl",
}
EXPECTED_INTEGRITY_REFS = set(EXPECTED_ARTIFACT_REFS.values()) - {EXPECTED_ARTIFACT_REFS["manifest"]}
EXPECTED_CLAUSES = {
    "S01CTA-C01": ("historical_stage_result_preserved", "S01 remains BLOCKED/NOT_PASSED/NO_GO"),
    "S01CTA-C02": ("stage_acceptance_not_recomputed", "amendment_is_stage_pass=false; stage_acceptance_recomputed=false"),
    "S01CTA-C03": ("taskpack_stage_gate_not_overridden", "Stage gate criteria remain unchanged and unsatisfied"),
    "S01CTA-C04": ("runtime_missing_remains_authoritative", "RUNTIME_OBJECT_MISSING; existing_runtime_refactor_authorized=false"),
    "S01CTA-C05": ("stage_review_artifacts_immutable", "review manifest bytes/SHA/content hash bound to commit 08ce4b2b7"),
    "S01CTA-C06": ("full_rebuild_scope_authority", "existing user objective authorizes FULL REBUILD planning scope"),
    "S01CTA-C07": ("no_redundant_owner_authorization", "additional_owner_authorization_required=false"),
    "S01CTA-C08": ("only_transition_blocker_resolved", "IB-005 RESOLVED_BY_AMENDMENT; IB-001 through IB-004 CARRIED_OPEN"),
    "S01CTA-C09": ("acceptance_blockers_remain_open", "four acceptance blockers continue blocking S01 acceptance and runtime implementation"),
    "S01CTA-C10": ("next_entry_s02_p1_planning_only", "S02-P1 planning allowed next Run; S02-P2/P3 and S03+ false"),
    "S01CTA-C11": ("no_product_or_business_implementation", "runtime/API/database/UI/stack selection/business execution all false"),
    "S01CTA-C12": ("no_release_or_raw_action", "GitHub upload/App reinstall/raw mutation all false"),
}
EXPECTED_CLAUSE_IDS = set(EXPECTED_CLAUSES)
EXPECTED_RECEIPT_IDS = {
    "stage_review_strict_dependency",
    "roadmap_governance_check",
    "amendment_focused_tests",
    "governance_project_check",
    "lean_check",
    "governance_sync_check",
    "no_float_check",
    "no_omission_check",
    "structured_public_diff_checks",
}
EXPECTED_TASKS = {
    "S01CTA-T01": (
        "冻结 authority 与 Stage 负面历史",
        "FULL REBUILD scope authority and immutable Stage review dependency binding",
    ),
    "S01CTA-T02": (
        "建立 planning-only transition edge",
        "five blocker dispositions and twelve transition clauses",
    ),
    "S01CTA-T03": (
        "验证下一入口与非动作边界",
        "S02-P1 planning-only next-entry gate with all downstream actions false",
    ),
}
EXPECTED_BLOCKERS = {
    **{
        f"S01REV-IB-{index:03d}": (
            "INHERITED_ACCEPTANCE_BLOCKER",
            "CARRIED_OPEN",
            "true",
            "true",
            "false",
        )
        for index in range(1, 5)
    },
    "S01REV-IB-005": (
        "INHERITED_TRANSITION_BLOCKER",
        "RESOLVED_BY_AMENDMENT",
        "false",
        "false",
        "false",
    ),
}
EXPECTED_TOP_LEVEL_KEYS = {
    "schema_version",
    "project_id",
    "target_release",
    "bridge_id",
    "task_id",
    "acceptance_id",
    "generated_at",
    "run_mode",
    "work_kind",
    "amendment_base_commit",
    "source_package",
    "dependency_evidence",
    "authority",
    "historical_stage_snapshot",
    "change_control_basis",
    "bridge_task_accounting",
    "bridge_tasks",
    "blocker_disposition_accounting",
    "risk_carry_forward",
    "amendment_result",
    "next_entry_gate",
    "future_obligation",
    "downstream_actions",
    "artifact_refs",
    "artifact_integrity",
    "content_hash",
}


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
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValidationError(f"expected JSON object at {path}:{line_number}")
        rows.append(value)
    return rows


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical_content_hash(value: dict[str, Any]) -> str:
    payload = dict(value)
    payload.pop("content_hash", None)
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _safe_ref_path(
    ref: Any,
    *,
    repo_root: Path,
    path_overrides: dict[str, Path],
    require_exists: bool = True,
) -> Path | None:
    if not isinstance(ref, str) or not ref.strip():
        return None
    relative = Path(ref)
    if relative.is_absolute() or ".." in relative.parts or not relative.parts or relative.parts[0] != "KMFA":
        return None
    if ref in path_overrides:
        path = path_overrides[ref]
    else:
        path = repo_root / relative
        repo = repo_root.resolve()
        try:
            path.resolve().relative_to(repo)
        except ValueError:
            return None
    if require_exists and not path.exists():
        return None
    return path


def _validate_evidence_refs(
    refs: Any,
    label: str,
    errors: list[str],
    *,
    repo_root: Path,
    path_overrides: dict[str, Path],
) -> None:
    _require(isinstance(refs, list) and bool(refs), f"{label}: evidence refs missing", errors)
    if not isinstance(refs, list):
        return
    _require(len(refs) == len(set(map(str, refs))), f"{label}: duplicate evidence refs", errors)
    for ref in refs:
        _require(
            _safe_ref_path(ref, repo_root=repo_root, path_overrides=path_overrides) is not None,
            f"{label}: unsafe or missing evidence ref {ref}",
            errors,
        )


def _validate_dependency(
    manifest: dict[str, Any],
    dependency_path: Path,
    errors: list[str],
) -> None:
    expected_dependency = {
        "count": 1,
        "stage_review_manifest_ref": STAGE_REVIEW_MANIFEST_REF,
        "stage_review_manifest_bytes": STAGE_REVIEW_BYTES,
        "stage_review_manifest_sha256": STAGE_REVIEW_SHA256,
        "stage_review_manifest_content_hash": STAGE_REVIEW_CONTENT_HASH,
        "stage_review_result_commit": AMENDMENT_BASE_COMMIT,
    }
    _require(manifest.get("dependency_evidence") == expected_dependency, "Stage review dependency binding mismatch", errors)
    _require(dependency_path.is_file(), "Stage review dependency manifest missing", errors)
    if not dependency_path.is_file():
        return
    dependency = _read_json(dependency_path)
    _require(dependency_path.stat().st_size == STAGE_REVIEW_BYTES, "Stage review dependency byte drift", errors)
    _require(_sha256(dependency_path) == STAGE_REVIEW_SHA256, "Stage review dependency SHA-256 drift", errors)
    _require(dependency.get("schema_version") == "kmfa.v015.s01_stage_review.v1", "Stage review dependency schema drift", errors)
    _require(dependency.get("content_hash") == STAGE_REVIEW_CONTENT_HASH, "Stage review dependency content hash drift", errors)
    _require(dependency.get("content_hash") == _canonical_content_hash(dependency), "Stage review dependency canonical hash invalid", errors)
    stage_gate = dependency.get("stage_gate", {})
    expected_stage = {
        "stage_lifecycle_status": "BLOCKED",
        "stage_acceptance_status": "NOT_PASSED",
        "decision": "NO_GO",
        "s02_entry_allowed": False,
    }
    _require({key: stage_gate.get(key) for key in expected_stage} == expected_stage, "Stage review negative result was rewritten", errors)
    next_gate = dependency.get("next_gate", {})
    _require(next_gate.get("next_allowed_run") == "S01_CONTROLLED_TRANSITION_AMENDMENT", "Stage review next gate dependency drift", errors)
    _require(next_gate.get("amendment_is_stage_pass") is False, "Stage review amendment boundary drift", errors)


def _validate_tasks(
    manifest: dict[str, Any],
    errors: list[str],
    *,
    repo_root: Path,
    path_overrides: dict[str, Path],
) -> None:
    tasks = manifest.get("bridge_tasks", [])
    by_id = {row.get("task_id"): row for row in tasks if isinstance(row, dict)} if isinstance(tasks, list) else {}
    _require(isinstance(tasks, list) and len(tasks) == len(by_id) == 3, "bridge tasks must contain three unique rows", errors)
    _require(set(by_id) == set(EXPECTED_TASKS), "bridge task ID set mismatch", errors)
    for task_id, (name, output) in EXPECTED_TASKS.items():
        row = by_id.get(task_id, {})
        _require(
            set(row) == {"task_id", "name", "execution_status", "acceptance_status", "output", "evidence_refs"},
            f"{task_id}: bridge task key set mismatch",
            errors,
        )
        _require(row.get("name") == name, f"{task_id}: task name mismatch", errors)
        _require(row.get("execution_status") == "EXECUTION_COMPLETE", f"{task_id}: execution status mismatch", errors)
        _require(row.get("acceptance_status") == "PASSED", f"{task_id}: acceptance status mismatch", errors)
        _require(row.get("output") == output, f"{task_id}: task output mismatch", errors)
        _validate_evidence_refs(
            row.get("evidence_refs"), task_id, errors, repo_root=repo_root, path_overrides=path_overrides
        )


def _validate_blockers(
    rows: list[dict[str, str]],
    errors: list[str],
    *,
    repo_root: Path,
    path_overrides: dict[str, Path],
) -> None:
    expected_header = {
        "finding_id",
        "historical_class",
        "historical_status",
        "current_disposition",
        "blocks_s01_acceptance",
        "blocks_runtime_implementation",
        "blocks_s02_p1_planning_under_amendment",
        "resolution_or_deferred_gate",
        "evidence_refs",
    }
    ids = [row.get("finding_id", "") for row in rows]
    _require(len(rows) == len(set(ids)) == 5, "blocker dispositions must contain five unique rows", errors)
    _require(set(ids) == set(EXPECTED_BLOCKERS), "blocker disposition ID set mismatch", errors)
    for row in rows:
        blocker_id = row.get("finding_id", "")
        _require(set(row) == expected_header, f"{blocker_id}: blocker disposition column set mismatch", errors)
        expected = EXPECTED_BLOCKERS.get(blocker_id)
        if expected is None:
            continue
        actual = (
            row.get("historical_class"),
            row.get("current_disposition"),
            row.get("blocks_s01_acceptance"),
            row.get("blocks_runtime_implementation"),
            row.get("blocks_s02_p1_planning_under_amendment"),
        )
        _require(actual == expected, f"{blocker_id}: blocker disposition drift", errors)
        _require(row.get("historical_status") == "OPEN_BLOCKING", f"{blocker_id}: historical blocker status drift", errors)
        _require(bool(row.get("resolution_or_deferred_gate", "").strip()), f"{blocker_id}: resolution/deferred gate missing", errors)
        refs = [item.strip() for item in row.get("evidence_refs", "").split(";") if item.strip()]
        _validate_evidence_refs(refs, blocker_id, errors, repo_root=repo_root, path_overrides=path_overrides)


def _validate_contract(
    contract: dict[str, Any],
    errors: list[str],
    *,
    repo_root: Path,
    path_overrides: dict[str, Path],
) -> None:
    _require(
        set(contract) == {"schema_version", "project_id", "target_release", "bridge_id", "clauses"},
        "transition contract key set mismatch",
        errors,
    )
    _require(contract.get("schema_version") == "kmfa.v015.s01_controlled_transition_contract.v1", "transition contract schema mismatch", errors)
    _require(contract.get("project_id") == "KMFA" and contract.get("target_release") == "v1.5", "transition contract identity mismatch", errors)
    _require(contract.get("bridge_id") == "S01-CTA", "transition contract bridge ID mismatch", errors)
    clauses = contract.get("clauses", [])
    by_id = {row.get("clause_id"): row for row in clauses if isinstance(row, dict)} if isinstance(clauses, list) else {}
    _require(isinstance(clauses, list) and len(clauses) == len(by_id) == 12, "transition contract must contain 12 unique clauses", errors)
    _require(set(by_id) == EXPECTED_CLAUSE_IDS, "transition clause ID set mismatch", errors)
    for clause_id, row in by_id.items():
        _require(set(row) == {"clause_id", "name", "result", "observed", "evidence_refs"}, f"{clause_id}: clause key set mismatch", errors)
        expected_name, expected_observed = EXPECTED_CLAUSES[clause_id]
        _require(row.get("name") == expected_name, f"{clause_id}: clause name mismatch", errors)
        _require(row.get("result") == "PASS", f"{clause_id}: contract clause failed", errors)
        _require(row.get("observed") == expected_observed, f"{clause_id}: observed evidence mismatch", errors)
        _validate_evidence_refs(
            row.get("evidence_refs"), clause_id, errors, repo_root=repo_root, path_overrides=path_overrides
        )


def _validate_artifacts(
    manifest: dict[str, Any],
    errors: list[str],
    *,
    repo_root: Path,
    path_overrides: dict[str, Path],
) -> None:
    _require(manifest.get("artifact_refs") == EXPECTED_ARTIFACT_REFS, "artifact refs must contain the exact seven refs", errors)
    rows = manifest.get("artifact_integrity", [])
    by_ref = {row.get("ref"): row for row in rows if isinstance(row, dict)} if isinstance(rows, list) else {}
    _require(isinstance(rows, list) and len(rows) == len(by_ref) == 6, "artifact integrity must contain six unique rows", errors)
    _require(set(by_ref) == EXPECTED_INTEGRITY_REFS, "artifact integrity ref set mismatch", errors)
    for ref, row in by_ref.items():
        _require(set(row) == {"ref", "bytes", "sha256"}, f"{ref}: artifact integrity key set mismatch", errors)
        path = _safe_ref_path(ref, repo_root=repo_root, path_overrides=path_overrides)
        _require(path is not None and path.is_file(), f"{ref}: artifact missing or unsafe", errors)
        if path is None or not path.is_file():
            continue
        _require(row.get("bytes") == path.stat().st_size, f"{ref}: artifact byte count mismatch", errors)
        _require(row.get("sha256") == _sha256(path), f"{ref}: artifact SHA-256 mismatch", errors)


def _validate_receipts(rows: list[dict[str, Any]], require_pass: bool, errors: list[str]) -> None:
    ids = [str(row.get("validation_id", "")) for row in rows]
    _require(len(rows) == len(set(ids)) == 9, "validation receipts must contain nine unique rows", errors)
    _require(set(ids) == EXPECTED_RECEIPT_IDS, "validation receipt ID set mismatch", errors)
    for row in rows:
        receipt_id = row.get("validation_id", "unknown")
        _require(set(row) == {"validation_id", "command", "result", "exit_code"}, f"{receipt_id}: receipt key set mismatch", errors)
        _require(bool(str(row.get("command", "")).strip()), f"{receipt_id}: receipt command missing", errors)
        allowed_results = {"PASS"} if require_pass else {"PASS", "PENDING"}
        _require(row.get("result") in allowed_results, f"{receipt_id}: receipt result mismatch", errors)
        if row.get("result") == "PASS":
            _require(row.get("exit_code") == 0, f"{receipt_id}: PASS receipt must have exit_code=0", errors)
        else:
            _require(row.get("exit_code") is None, f"{receipt_id}: PENDING receipt must have null exit_code", errors)


def _validate_governance(
    project_text: str,
    roadmap_text: str,
    agents_text: str,
    model_spec_text: str,
    errors: list[str],
) -> None:
    current_amendment_project_tokens = (
        'target_version: "v1.5"',
        'development_version: "1.5.0-dev-s01-transition-amendment"',
        'current_status: "v15_s01_controlled_transition_amendment_passed_s02_p1_only"',
        'current_stage_id: "S01"',
        'current_phase_id: "V015_S01_CONTROLLED_TRANSITION_AMENDMENT"',
        'run_mode: "IMPLEMENT"',
        'work_kind: "CONTROLLED_TRANSITION_AMENDMENT"',
        'stage_lifecycle_status: "BLOCKED"',
        'stage_acceptance_status: "NOT_PASSED"',
        'decision: "NO_GO"',
        'amendment_acceptance_status: "PASSED"',
        'taskpack_stage_gate_s02_entry_allowed: false',
        's02_p1_planning_entry_allowed_by_amendment: true',
        'next_gate_id: "S02-P1"',
    )
    current_amendment_roadmap_tokens = (
        'target_release: "v1.5"',
        "active_stage_count: 24",
        "active_phase_count: 72",
        "active_task_count: 216",
        'current_stage_id: "S01"',
        'current_phase_id: "V015_S01_CONTROLLED_TRANSITION_AMENDMENT"',
        'stage_lifecycle_status: "BLOCKED"',
        'stage_acceptance_status: "NOT_PASSED"',
        'decision: "NO_GO"',
        'taskpack_stage_gate_s02_entry_allowed: false',
        's02_p1_planning_entry_allowed_by_amendment: true',
        'next_gate_id: "S02-P1"',
    )

    def top_level_scalar(text: str, key: str) -> str | None:
        match = re.search(rf"(?m)^{re.escape(key)}:\s*(?:\"([^\"]*)\"|([^#\n]+))\s*$", text)
        if match is None:
            return None
        return (match.group(1) if match.group(1) is not None else match.group(2)).strip()

    project_phase = top_level_scalar(project_text, "current_phase_id")
    roadmap_phase = top_level_scalar(roadmap_text, "current_phase_id")
    _require(project_phase == roadmap_phase, "project/roadmap current phase mismatch", errors)
    current_amendment = project_phase == "V015_S01_CONTROLLED_TRANSITION_AMENDMENT"
    successor_match = re.fullmatch(
        r"V015_S(?P<stage>0[2-9]|1[0-9]|2[0-4])_P[123](?:_[A-Z0-9_]+)?",
        project_phase or "",
    )
    _require(current_amendment or successor_match is not None, "illegal amendment governance successor phase", errors)

    if current_amendment:
        for token in current_amendment_project_tokens:
            _require(token in project_text, f"project governance token missing: {token}", errors)
        for token in current_amendment_roadmap_tokens:
            _require(token in roadmap_text, f"roadmap governance token missing: {token}", errors)
    elif successor_match is not None:
        expected_stage = f"S{successor_match.group('stage')}"
        for token in ('target_version: "v1.5"',):
            _require(token in project_text, f"project successor token missing: {token}", errors)
        for token in (
            'target_release: "v1.5"',
            "active_stage_count: 24",
            "active_phase_count: 72",
            "active_task_count: 216",
        ):
            _require(token in roadmap_text, f"roadmap successor token missing: {token}", errors)
        _require(
            top_level_scalar(project_text, "current_stage_id") == expected_stage,
            "project successor stage/phase mismatch",
            errors,
        )
        _require(
            top_level_scalar(roadmap_text, "current_stage_id") == expected_stage,
            "roadmap successor stage/phase mismatch",
            errors,
        )
        successor_history = {
            "s01_stage_review_lifecycle_status": "BLOCKED",
            "s01_stage_review_acceptance_status": "NOT_PASSED",
            "s01_stage_review_decision": "NO_GO",
            "s01_stage_review_s02_entry_allowed": "false",
            "s01_controlled_transition_amendment_acceptance_status": "PASSED",
            "s01_controlled_transition_amendment_decision": "GO_TO_S02_P1_ONLY",
            "s01_controlled_transition_s02_p1_entry_allowed": "true",
            "s01_controlled_transition_product_implementation_allowed": "false",
        }
        for label, text in (("project", project_text), ("roadmap", roadmap_text)):
            for key, expected in successor_history.items():
                _require(
                    top_level_scalar(text, key) == expected,
                    f"{label} historical amendment field mismatch: {key}",
                    errors,
                )
    for token in (
        "BLOCKED / NOT_PASSED / NO_GO",
        "不得按单个 Stage 做 GitHub upload gate",
        SOURCE_PACKAGE_SHA256,
    ):
        _require(token in agents_text, f"AGENTS token missing: {token}", errors)
    for token in (
        "FORM-KMFA-V015-S01-CONTROLLED-TRANSITION-AMENDMENT-001",
        "bridge_task_count == 3",
        "carried_open_acceptance_blocker_count == 4",
        "resolved_transition_blocker_count == 1",
        "s02_p1_planning_entry_allowed_by_amendment == true",
    ):
        _require(token in model_spec_text, f"MODEL_SPEC transition token missing: {token}", errors)


def _validate_events(rows: list[dict[str, Any]], require_final: bool, errors: list[str]) -> None:
    relevant = [row for row in rows if row.get("phase_id") == "V015_S01_CONTROLLED_TRANSITION_AMENDMENT"]
    _require(len(relevant) in {1, 2}, "canonical transition amendment event count mismatch", errors)
    common = {
        "project_id": "KMFA",
        "phase_id": "V015_S01_CONTROLLED_TRANSITION_AMENDMENT",
        "run_mode": "IMPLEMENT",
        "work_kind": "CONTROLLED_TRANSITION_AMENDMENT",
        "amendment_execution_status": "EXECUTION_COMPLETE",
        "historical_stage_lifecycle_status": "BLOCKED",
        "historical_stage_acceptance_status": "NOT_PASSED",
        "historical_stage_decision": "NO_GO",
        "taskpack_stage_gate_s02_entry_allowed": False,
        "s02_started": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "next_taskpack_phase": "S02-P1",
    }
    execution_expected = {
        **common,
        "event_id": "EVENT-KMFA-20260713-V015-S01-CONTROLLED-TRANSITION-AMENDMENT-EXECUTION",
        "amendment_acceptance_status": "PENDING_FINAL_VALIDATION",
        "final_validation_status": "PENDING",
        "s02_p1_planning_entry_allowed_by_amendment": False,
    }
    execution = relevant[0] if relevant else {}
    _require(
        {key: execution.get(key) for key in execution_expected} == execution_expected,
        "canonical transition amendment execution event cohort drift",
        errors,
    )
    if len(relevant) == 2:
        final_expected = {
            **common,
            "event_id": "EVENT-KMFA-20260713-V015-S01-CONTROLLED-TRANSITION-AMENDMENT-FINAL-VALIDATION",
            "amendment_acceptance_status": "PASSED",
            "final_validation_status": "PASS",
            "s02_p1_planning_entry_allowed_by_amendment": True,
        }
        final = relevant[1]
        _require(
            {key: final.get(key) for key in final_expected} == final_expected,
            "canonical transition amendment final event cohort drift",
            errors,
        )
    if require_final:
        _require(len(relevant) == 2, "canonical final transition amendment event missing", errors)


def _validate_clean_result(
    *,
    repo_root: Path,
    manifest_path: Path,
    errors: list[str],
) -> None:
    status = subprocess.run(
        ["git", "status", "--short"], cwd=repo_root, capture_output=True, text=True, check=False
    )
    _require(status.returncode == 0 and not status.stdout.strip(), "Git worktree must be clean", errors)
    try:
        relative_manifest = manifest_path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        relative_manifest = manifest_path.name
    result = subprocess.run(
        ["git", "log", "-1", "--format=%H", "--", relative_manifest],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    result_commit = result.stdout.strip()
    valid_commit = bool(re.fullmatch(r"[0-9a-f]{40}", result_commit))
    _require(result.returncode == 0 and valid_commit, "committed amendment result not found", errors)
    if not valid_commit:
        return
    _require(result_commit != AMENDMENT_BASE_COMMIT, "amendment result commit must differ from base", errors)
    base_ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", AMENDMENT_BASE_COMMIT, result_commit],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    _require(base_ancestor.returncode == 0, "amendment base is not an ancestor of result commit", errors)
    result_ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", result_commit, "HEAD"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    _require(result_ancestor.returncode == 0, "amendment result commit is not an ancestor of HEAD", errors)
    committed = subprocess.run(
        ["git", "show", f"{result_commit}:{relative_manifest}"],
        cwd=repo_root,
        capture_output=True,
        check=False,
    )
    _require(
        committed.returncode == 0 and committed.stdout == manifest_path.read_bytes(),
        "committed amendment manifest differs from worktree",
        errors,
    )


def _run_dependency_validator(require_clean: bool, errors: list[str]) -> None:
    command = [
        sys.executable,
        "-B",
        "KMFA/tools/check_v015_s01_stage_review.py",
        "--require-validation-receipts",
        "--require-dependency-validators",
    ]
    if require_clean:
        command.append("--require-clean-worktree")
    result = subprocess.run(command, cwd=REPO_ROOT, capture_output=True, text=True, check=False)
    _require(
        result.returncode == 0,
        f"Stage review strict dependency validator failed: {result.stdout}{result.stderr}",
        errors,
    )


def validate_v015_s01_controlled_transition_amendment(
    manifest_path: Path = MANIFEST_PATH,
    *,
    contract_path: Path = CONTRACT_PATH,
    blocker_dispositions_path: Path = BLOCKER_DISPOSITIONS_PATH,
    validation_results_path: Path = VALIDATION_RESULTS_PATH,
    stage_review_manifest_path: Path = STAGE_REVIEW_MANIFEST_PATH,
    project_governance_path: Path = PROJECT_GOVERNANCE_PATH,
    roadmap_governance_path: Path = ROADMAP_GOVERNANCE_PATH,
    agents_path: Path = AGENTS_PATH,
    events_path: Path = EVENTS_PATH,
    model_spec_path: Path = MODEL_SPEC_PATH,
    artifact_path_overrides: dict[str, Path] | None = None,
    source_package: Path | None = SOURCE_PACKAGE,
    require_source_package: bool = False,
    require_validation_receipts: bool = False,
    require_dependency_validator: bool = False,
    require_clean_worktree: bool = False,
    repo_root: Path = REPO_ROOT,
) -> dict[str, Any]:
    errors: list[str] = []
    path_overrides = dict(artifact_path_overrides or {})
    path_overrides.setdefault(STAGE_REVIEW_MANIFEST_REF, stage_review_manifest_path)
    manifest = _read_json(manifest_path)
    contract = _read_json(contract_path)
    blockers = _read_csv(blocker_dispositions_path)
    receipts = _read_jsonl(validation_results_path)
    events = _read_jsonl(events_path)

    _require(set(manifest) == EXPECTED_TOP_LEVEL_KEYS, "manifest top-level key set mismatch", errors)
    _require(manifest.get("schema_version") == "kmfa.v015.s01_controlled_transition_amendment.v1", "manifest schema mismatch", errors)
    _require(manifest.get("project_id") == "KMFA" and manifest.get("target_release") == "v1.5", "manifest identity mismatch", errors)
    _require(manifest.get("bridge_id") == "S01-CTA", "manifest bridge ID mismatch", errors)
    _require(manifest.get("task_id") == "KMFA-V015-S01-CONTROLLED-TRANSITION-AMENDMENT-20260713", "manifest task ID mismatch", errors)
    _require(manifest.get("acceptance_id") == "ACC-KMFA-V015-S01-CONTROLLED-TRANSITION-AMENDMENT", "manifest acceptance ID mismatch", errors)
    _require(bool(str(manifest.get("generated_at", "")).strip()), "manifest generated_at missing", errors)
    _require(manifest.get("run_mode") == "IMPLEMENT", "amendment run_mode must be IMPLEMENT", errors)
    _require(manifest.get("work_kind") == "CONTROLLED_TRANSITION_AMENDMENT", "amendment work kind mismatch", errors)
    _require(manifest.get("amendment_base_commit") == AMENDMENT_BASE_COMMIT, "amendment base commit mismatch", errors)
    _require(manifest.get("content_hash") == _canonical_content_hash(manifest), "manifest content hash mismatch", errors)

    expected_source = {
        "name": SOURCE_PACKAGE.name,
        "bytes": SOURCE_PACKAGE_BYTES,
        "sha256": SOURCE_PACKAGE_SHA256,
        "stage_count": 24,
        "phase_count": 72,
        "task_count": 216,
    }
    _require(manifest.get("source_package") == expected_source, "source package/count binding mismatch", errors)
    _validate_dependency(manifest, stage_review_manifest_path, errors)
    _require(
        manifest.get("authority") == {
            "existing_full_rebuild_objective_is_scope_authority": True,
            "additional_owner_authorization_required": False,
            "taskpack_stage_gate_overridden": False,
            "taskpack_stage_gate_satisfied": False,
            "historical_evidence_mutated": False,
            "roadmap_counts_mutated": False,
            "bridge_counted_as_taskpack_phase": False,
        },
        "amendment authority boundary mismatch",
        errors,
    )
    _require(
        manifest.get("historical_stage_snapshot") == {
            "stage_lifecycle_status": "BLOCKED",
            "stage_acceptance_status": "NOT_PASSED",
            "decision": "NO_GO",
            "s02_entry_allowed": False,
            "task_total": 9,
            "task_accepted": 5,
            "task_not_accepted": 4,
            "triggered_stop_conditions": 3,
            "audit_conclusion": "RUNTIME_OBJECT_MISSING",
            "existing_runtime_refactor_authorized": False,
        },
        "historical Stage snapshot must remain fail-closed",
        errors,
    )
    _require(
        manifest.get("change_control_basis") == {
            "p3_greenfield_change_control_required": True,
            "transition_mode": "GREENFIELD_PLANNING_ONLY",
            "risk_id": "RISK-P3-RUN-001",
            "risk_resolution_stages": ["S02", "S15", "S20"],
            "runtime_business_flow_stop_preserved": True,
            "greenfield_rebuild_planning_authorized": True,
            "greenfield_rebuild_implementation_authorized": False,
            "technology_stack_selection_allowed": False,
        },
        "greenfield planning change-control basis mismatch",
        errors,
    )
    _validate_tasks(manifest, errors, repo_root=repo_root, path_overrides=path_overrides)
    _require(manifest.get("bridge_task_accounting") == {"total": 3, "accepted": 3, "not_accepted": 0}, "bridge task accounting mismatch", errors)
    _require(
        manifest.get("blocker_disposition_accounting") == {
            "historical_total": 5,
            "carried_open_acceptance_blockers": 4,
            "resolved_transition_blockers": 1,
            "historical_rows_mutated": 0,
            "s02_p1_planning_blockers": 0,
            "runtime_implementation_blockers": 4,
        },
        "blocker disposition accounting mismatch",
        errors,
    )
    _require(
        manifest.get("risk_carry_forward") == {
            "total": 24,
            "p0": 18,
            "p1": 6,
            "p0_plan_gap_count": 0,
            "resolved_by_amendment": 0,
            "all_remain_open_with_plan": True,
        },
        "risk carry-forward facts mismatch",
        errors,
    )
    result = manifest.get("amendment_result", {})
    _require(
        set(result) == {
            "execution_status", "evidence_validation_status", "final_validation_status", "acceptance_status",
            "decision", "amendment_is_stage_pass", "stage_acceptance_recomputed",
        },
        "amendment result key set mismatch",
        errors,
    )
    fixed_result = {
        "execution_status": "EXECUTION_COMPLETE",
        "amendment_is_stage_pass": False,
        "stage_acceptance_recomputed": False,
    }
    _require({key: result.get(key) for key in fixed_result} == fixed_result, "amendment fixed result facts mismatch", errors)
    pending_result = {
        "evidence_validation_status": "PENDING",
        "final_validation_status": "PENDING",
        "acceptance_status": "PENDING_FINAL_VALIDATION",
        "decision": "PENDING_FINAL_VALIDATION",
    }
    final_result = {
        "evidence_validation_status": "PASS",
        "final_validation_status": "PASS",
        "acceptance_status": "PASSED",
        "decision": "GO_TO_S02_P1_ONLY",
    }
    status_result = {key: result.get(key) for key in pending_result}
    _require(status_result in ([final_result] if require_validation_receipts else [pending_result, final_result]), "amendment result status cohort mismatch", errors)
    expected_next_gate = {
            "next_allowed_taskpack_phase": "S02-P1",
            "s02_p1_planning_entry_allowed_by_amendment": status_result == final_result,
            "s02_p1_started_in_amendment_run": False,
            "s02_p1_product_implementation_allowed": False,
            "s02_p2_entry_allowed": False,
            "s02_p3_entry_allowed": False,
            "s03_plus_entry_allowed": False,
            "product_implementation_allowed": False,
        }
    _require(
        manifest.get("next_entry_gate") == expected_next_gate,
        "next entry must remain scoped to S02-P1 planning",
        errors,
    )
    _require(
        manifest.get("future_obligation") == {
            "s01_deferred_revalidation_required": True,
            "revalidation_requires_tracked_runtime": True,
            "revalidation_requires_real_routes": True,
            "revalidation_requires_tracked_builder_installer": True,
            "revalidation_requires_complete_preaudit_telemetry": True,
            "revalidation_deadline": "BEFORE_S24_RELEASE_ACCEPTANCE_FINAL_OVERALL_REVIEW_GITHUB_UPLOAD_APP_REINSTALL",
            "historical_records_append_only": True,
            "new_evidence_required_to_change_acceptance": True,
        },
        "future S01 revalidation obligation mismatch",
        errors,
    )
    _require(
        manifest.get("downstream_actions") == {
            "s02_started": False,
            "technology_stack_selected": False,
            "product_runtime_implementation_performed": False,
            "api_implementation_performed": False,
            "database_implementation_performed": False,
            "ui_implementation_performed": False,
            "raw_business_content_read": False,
            "business_execution_performed": False,
            "github_upload_performed": False,
            "app_reinstall_performed": False,
            "raw_inbox_mutated": False,
        },
        "downstream action boundary drift",
        errors,
    )

    _validate_contract(contract, errors, repo_root=repo_root, path_overrides=path_overrides)
    _validate_blockers(blockers, errors, repo_root=repo_root, path_overrides=path_overrides)
    _validate_artifacts(manifest, errors, repo_root=repo_root, path_overrides=path_overrides)
    _validate_receipts(receipts, require_validation_receipts, errors)
    _validate_governance(
        project_governance_path.read_text(encoding="utf-8"),
        roadmap_governance_path.read_text(encoding="utf-8"),
        agents_path.read_text(encoding="utf-8"),
        model_spec_path.read_text(encoding="utf-8"),
        errors,
    )
    _validate_events(events, require_validation_receipts, errors)

    package_available = source_package is not None and source_package.is_file()
    if require_source_package:
        _require(package_available, "source package required but missing", errors)
    if package_available:
        _require(source_package.stat().st_size == SOURCE_PACKAGE_BYTES, "source package byte count mismatch", errors)
        _require(_sha256(source_package) == SOURCE_PACKAGE_SHA256, "source package SHA-256 mismatch", errors)

    if require_dependency_validator:
        _run_dependency_validator(require_clean_worktree, errors)
    if require_clean_worktree:
        _validate_clean_result(repo_root=repo_root, manifest_path=manifest_path, errors=errors)

    if errors:
        raise ValidationError("\n".join(errors))
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    parser.add_argument("--contract", type=Path, default=CONTRACT_PATH)
    parser.add_argument("--blocker-dispositions", type=Path, default=BLOCKER_DISPOSITIONS_PATH)
    parser.add_argument("--validation-results", type=Path, default=VALIDATION_RESULTS_PATH)
    parser.add_argument("--require-source-package", action="store_true")
    parser.add_argument("--require-validation-receipts", action="store_true")
    parser.add_argument("--require-dependency-validator", action="store_true")
    parser.add_argument("--require-clean-worktree", action="store_true")
    args = parser.parse_args()
    try:
        result = validate_v015_s01_controlled_transition_amendment(
            args.manifest,
            contract_path=args.contract,
            blocker_dispositions_path=args.blocker_dispositions,
            validation_results_path=args.validation_results,
            require_source_package=args.require_source_package,
            require_validation_receipts=args.require_validation_receipts,
            require_dependency_validator=args.require_dependency_validator,
            require_clean_worktree=args.require_clean_worktree,
        )
    except (OSError, ValueError, json.JSONDecodeError, ValidationError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    print(
        "PASS: KMFA v1.5 S01 controlled transition amendment validated; "
        f"amendment={result['amendment_result']['acceptance_status']}; "
        "historical Stage=BLOCKED/NOT_PASSED/NO_GO; next=S02-P1 only"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
