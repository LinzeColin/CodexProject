#!/usr/bin/env python3
"""Validate KMFA v1.5 S01-P3 read-only audit gate evidence."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_ROOT = REPO_ROOT / "KMFA/stage_artifacts/V015_S01_P3_READ_ONLY_AUDIT_GATE"
MANIFEST_PATH = ARTIFACT_ROOT / "machine/s01_p3_read_only_audit_gate_manifest.json"
ACCEPTANCE_PATH = ARTIFACT_ROOT / "machine/acceptance_matrix_public_safe.json"
RISK_PATH = ARTIFACT_ROOT / "machine/open_risk_unknown_register_public_safe.csv"
SIDE_EFFECT_PATH = ARTIFACT_ROOT / "machine/side_effect_snapshot_public_safe.json"
METADATA_PATH = REPO_ROOT / "KMFA/metadata/baseline/v015_s01_p3_read_only_audit_gate.json"
STAGE_STATUS_PATH = REPO_ROOT / "KMFA/metadata/stage_status.jsonl"
P1_MANIFEST_PATH = REPO_ROOT / "KMFA/stage_artifacts/V015_S01_P1_LEGACY_REFERENCE_BASELINE_FREEZE/machine/s01_p1_legacy_reference_baseline_manifest.json"
P2_MANIFEST_PATH = REPO_ROOT / "KMFA/stage_artifacts/V015_S01_P2_IMPLEMENTATION_SPEC_GAP_INVENTORY/machine/s01_p2_implementation_spec_gap_inventory_manifest.json"
P2_GAP_PATH = REPO_ROOT / "KMFA/stage_artifacts/V015_S01_P2_IMPLEMENTATION_SPEC_GAP_INVENTORY/machine/implementation_gap_matrix_public_safe.csv"
P2_MIGRATION_PATH = REPO_ROOT / "KMFA/stage_artifacts/V015_S01_P2_IMPLEMENTATION_SPEC_GAP_INVENTORY/machine/migration_decision_matrix_public_safe.csv"
SOURCE_PACKAGE = Path("/Users/linzezhang/Downloads/KMFA_ChatGPT_Stage3_Codex_TaskPack_Roadmap_v2_0_UIUX_FULL_REBUILD.zip")
SOURCE_PACKAGE_SHA256 = "e822c98bfe21445b4ddf7110ecf81d14c8fa8bd5f2cdeb00fab4a21e72df39f8"
V014_BASE_COMMIT = "d6f379ad11d486d8a7ebde9e61b2fc7b3aaf9d05"
P1_COMMIT = "0e309502f21f12e2deba0931acd3fe1bafd0614c"
P3_PRE_PHASE_COMMIT = "ef6c867dcba65c9e6d1f95adc823ace36ac93102"
P3_RESULT_COMMIT = "5aba436c3e7f1a98bb1a3ad88735b8ad2b279d46"
ORIGIN_MAIN_EXPECTED = V014_BASE_COMMIT
REMOTE_MAIN_SNAPSHOT = "d0a098b7e1b38763ee07ad264b28ce54a7c06022"
APP_PATH = Path("/Users/linzezhang/Downloads/KMFA.app")
APP_AGGREGATE_SHA256 = "848521287dfaafd93f64872ce96cec6cc9996becddfc31df15ff8bbff8877779"
RAW_ROOT = Path("/Users/linzezhang/Downloads/KMFA_MetaData")
RAW_SENTINEL = {"device": 16777234, "inode": 13660536, "size": 224, "mtime_epoch": 1782967639}
RAW_SENTINEL_FULL = {**RAW_SENTINEL, "mode": "drwxr-xr-x"}
PRE_P3_CHANGED_PATH_COUNT = 41
PRE_P3_PATH_LIST_SHA256 = "4bb4121c2ea6e2402beff6fb8b925e298dc61b2740e38d0e89fb50bb1630fdba"
EXPECTED_RISK_CATEGORIES = {
    "FIELD": 4,
    "DATA_SOURCE": 5,
    "ACCESS": 4,
    "RUNTIME_DEPENDENCY": 6,
    "UI_BREAKPOINT": 5,
}
EXPECTED_PRIORITY_COUNTS = {"P0": 18, "P1": 6}
EXPECTED_RISK_IDS = {
    "RISK-P3-FLD-001", "RISK-P3-FLD-002", "RISK-P3-FLD-003", "RISK-P3-FLD-004",
    "RISK-P3-DAT-001", "RISK-P3-DAT-002", "RISK-P3-DAT-003", "RISK-P3-DAT-004", "RISK-P3-DAT-005",
    "RISK-P3-ACC-001", "RISK-P3-ACC-002", "RISK-P3-ACC-003", "RISK-P3-ACC-004",
    "RISK-P3-RUN-001", "RISK-P3-RUN-002", "RISK-P3-RUN-003", "RISK-P3-RUN-004", "RISK-P3-RUN-005", "RISK-P3-RUN-006",
    "RISK-P3-UI-001", "RISK-P3-UI-002", "RISK-P3-UI-003", "RISK-P3-UI-004", "RISK-P3-UI-005",
}
CRITICAL_RISK_IDS = {
    "RISK-P3-DAT-001",
    "RISK-P3-DAT-003",
    "RISK-P3-ACC-001",
    "RISK-P3-RUN-001",
    "RISK-P3-UI-001",
}
EXPECTED_TASK_OUTCOMES = {
    "S01P3T01": ("PASSED", "RUNTIME_OBJECT_MISSING", "human/read_only_audit_report_zh.md"),
    "S01P3T02": ("PASSED", "OPEN_RISKS_PLANNED_NOT_RESOLVED", "machine/open_risk_unknown_register_public_safe.csv"),
    "S01P3T03": ("NOT_PASSED", "UNEXPECTED_LOCAL_GIT_STATE_CHANGE_AND_INSUFFICIENT_PREAUDIT_TELEMETRY", "machine/side_effect_snapshot_public_safe.json"),
}
EXPECTED_ACCEPTANCE_CHECKS = {
    "taskpack_fingerprint_locked": ("PASS", None),
    "s01p1_negative_findings_preserved": ("PASS", None),
    "s01p2_inventory_preserved": ("PASS", None),
    "audit_conclusion_allowed_enum": ("PASS", None),
    "audit_conclusion_runtime_evidence_based": ("PASS", None),
    "button_and_static_dom_not_acceptance_evidence": ("PASS", None),
    "risk_register_unique_complete": ("PASS", None),
    "five_unknown_categories_covered": ("PASS", None),
    "risk_owner_stage_stop_complete": ("PASS", None),
    "p0_without_resolution_plan_zero": ("PASS", None),
    "high_risk_requirement_coverage": ("PASS", None),
    "tracked_diff_expected_classification": ("PASS", None),
    "expected_audit_code_metadata_writes_disclosed": ("PASS", None),
    "installed_app_fingerprint_and_signature_unchanged": ("PASS", None),
    "raw_root_shallow_sentinel_match": ("PASS", None),
    "current_persistent_app_process_listener_zero": ("PASS", None),
    "product_database_unexpected_change_zero": ("PASS", None),
    "private_audit_writes_explicit": ("PASS", None),
    "remote_main_external_drift_disclosed": ("PASS", None),
    "local_tracking_ref_stable": ("FAIL", "UNEXPECTED_LOCAL_TRACKING_REF_CHANGE_ATTRIBUTION_UNVERIFIED"),
    "raw_recursive_integrity_proven": ("FAIL", "INSUFFICIENT_PREAUDIT_RAW_FINGERPRINT"),
    "historical_process_monitoring_complete": ("FAIL", "INSUFFICIENT_HISTORICAL_PROCESS_LOG"),
}
EXPECTED_RELEASE_STATE_KEYS = {
    "delivery_allowed",
    "business_decision_basis_allowed",
    "business_execution_allowed",
    "formal_report_allowed",
    "github_upload_allowed",
    "app_reinstall_allowed",
    "s02_entry_allowed",
}
EXPECTED_PUBLIC_SAFETY_KEYS = {
    "raw_file_name_committed",
    "raw_file_hash_committed",
    "raw_business_value_committed",
    "source_document_committed",
    "credential_committed",
    "private_evidence_payload_committed",
}
EXPECTED_ARTIFACT_REFS = {
    "audit_report": "KMFA/stage_artifacts/V015_S01_P3_READ_ONLY_AUDIT_GATE/human/read_only_audit_report_zh.md",
    "risk_report": "KMFA/stage_artifacts/V015_S01_P3_READ_ONLY_AUDIT_GATE/human/open_risk_unknown_register_zh.md",
    "no_side_effect_report": "KMFA/stage_artifacts/V015_S01_P3_READ_ONLY_AUDIT_GATE/human/no_side_effect_proof_zh.md",
    "test_results": "KMFA/stage_artifacts/V015_S01_P3_READ_ONLY_AUDIT_GATE/human/test_results_zh.md",
    "risk_register": "KMFA/stage_artifacts/V015_S01_P3_READ_ONLY_AUDIT_GATE/machine/open_risk_unknown_register_public_safe.csv",
    "side_effect_snapshot": "KMFA/stage_artifacts/V015_S01_P3_READ_ONLY_AUDIT_GATE/machine/side_effect_snapshot_public_safe.json",
    "acceptance_matrix": "KMFA/stage_artifacts/V015_S01_P3_READ_ONLY_AUDIT_GATE/machine/acceptance_matrix_public_safe.json",
    "metadata_snapshot": "KMFA/metadata/baseline/v015_s01_p3_read_only_audit_gate.json",
}
EXPECTED_P3_PHASE_BOUNDARY_KEYS = {
    "p3_product_fix_performed",
    "stage_01_review_performed",
    "s02_started",
    "github_upload_performed",
    "app_reinstall_performed",
    "business_execution_performed",
}
EXPECTED_MANIFEST_PHASE_GATE_KEYS = {
    "task_execution_complete_count",
    "task_acceptance_passed_count",
    "s01p3_acceptance_passed",
    "stage_01_phase_execution_complete",
    "stage_01_passed",
    "stage_01_review_required",
    "stage_01_review_performed",
    "next_stage_started",
    "product_fix_performed",
    "github_upload_performed",
    "app_reinstall_performed",
    "business_execution_performed",
    "next_allowed_run",
}
EXPECTED_LATEST_STAGE_STATUS_KEYS = {
    "schema_version", "record_type", "project_id", "target_release", "stage_id", "phase_id",
    "roadmap_phase_id", "task_id", "acceptance_id", "version", "status", "fact_level", "decision",
    "audit_conclusion", "task_execution_complete_count", "task_acceptance_passed_count", "risk_total",
    "p0_without_plan_count", "t03_acceptance_passed", "terminal_finding",
    "unexpected_worktree_product_change_count", "unexpected_shared_git_ref_change_count",
    "historical_tracking_main_oid", "local_tracking_ref_oid_observed", "remote_main_oid_observed",
    "fetch_attribution", "current_task_push_performed", "raw_recursive_integrity",
    "historical_process_monitoring", "stage_01_phase_execution_complete", "stage_01_passed",
    "s02_entry_allowed", "raw_data_committed", "github_upload_performed", "app_reinstall_performed",
    "business_execution_performed", "evidence_ref", "updated_at",
}
TOP_LEVEL_GOVERNANCE_FILES = {
    "KMFA/CHANGELOG.md",
    "KMFA/HANDOFF.md",
    "KMFA/功能清单.md",
    "KMFA/开发记录.md",
    "KMFA/模型参数文件.md",
}
P3_GOVERNANCE_FILES = {
    *TOP_LEVEL_GOVERNANCE_FILES,
    "KMFA/docs/governance/ASSURANCE_STATUS.yaml",
    "KMFA/docs/governance/DEVELOPMENT_LEDGER.md",
    "KMFA/docs/governance/MODEL_SPEC.md",
    "KMFA/docs/governance/OWNER_STATUS.md",
    "KMFA/docs/governance/STATUS.md",
    "KMFA/docs/governance/TRACEABILITY_MATRIX.csv",
    "KMFA/docs/governance/VERSION_MATRIX.yaml",
    "KMFA/docs/governance/delivery_tasks.yaml",
    "KMFA/docs/governance/development_events.jsonl",
    "KMFA/docs/governance/formula_registry.yaml",
    "KMFA/docs/governance/model_registry.yaml",
    "KMFA/docs/governance/parameter_registry.csv",
    "KMFA/metadata/stage_status.jsonl",
}
P3_EXACT_FILES = {
    "KMFA/tools/check_v015_s01_p3_read_only_audit_gate.py",
    "KMFA/tests/test_v015_s01_p3_read_only_audit_gate.py",
    "KMFA/metadata/baseline/v015_s01_p3_read_only_audit_gate.json",
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


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical_content_hash(value: dict[str, Any]) -> str:
    payload = dict(value)
    payload.pop("content_hash", None)
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _git_bytes(args: list[str]) -> bytes:
    result = subprocess.run(["git", "-c", "core.quotepath=false", *args], cwd=REPO_ROOT, capture_output=True, check=False)
    if result.returncode != 0:
        raise ValidationError(result.stderr.decode("utf-8", errors="replace").strip())
    return result.stdout


def _git_text(args: list[str]) -> str:
    return _git_bytes(args).decode("utf-8").strip()


def _git_lines(args: list[str]) -> list[str]:
    text = _git_text(args)
    return text.splitlines() if text else []


def _pre_p3_paths() -> list[str]:
    return _git_lines(["diff", "--name-only", f"{V014_BASE_COMMIT}..{P3_PRE_PHASE_COMMIT}", "--", "KMFA"])


def _classify_pre_p3_paths(paths: list[str]) -> dict[str, list[str]]:
    result = {
        "stage_artifacts": [],
        "governance_docs": [],
        "audit_metadata": [],
        "audit_validator_tests": [],
        "top_level_delivery_docs": [],
        "unexpected": [],
    }
    for path in paths:
        if path.startswith(("KMFA/stage_artifacts/V015_S01_P1_", "KMFA/stage_artifacts/V015_S01_P2_")):
            result["stage_artifacts"].append(path)
        elif path.startswith("KMFA/docs/governance/"):
            result["governance_docs"].append(path)
        elif path.startswith("KMFA/metadata/baseline/v015_s01_p") or path == "KMFA/metadata/stage_status.jsonl":
            result["audit_metadata"].append(path)
        elif path.startswith(("KMFA/tools/check_v015_s01_p", "KMFA/tests/test_v015_s01_p")):
            result["audit_validator_tests"].append(path)
        elif path in TOP_LEVEL_GOVERNANCE_FILES:
            result["top_level_delivery_docs"].append(path)
        else:
            result["unexpected"].append(path)
    return result


def _phase_paths() -> list[str]:
    return sorted(set(_git_lines(["diff", "--name-only", P3_PRE_PHASE_COMMIT, P3_RESULT_COMMIT, "--", "KMFA"])))


def _classify_phase_paths(paths: list[str]) -> tuple[list[str], list[str]]:
    allowed: list[str] = []
    unexpected: list[str] = []
    for path in paths:
        if (
            path.startswith("KMFA/stage_artifacts/V015_S01_P3_READ_ONLY_AUDIT_GATE/")
            or path in P3_EXACT_FILES
            or path in P3_GOVERNANCE_FILES
        ):
            allowed.append(path)
        else:
            unexpected.append(path)
    return allowed, unexpected


def _tree_fingerprint(root: Path) -> tuple[int, int, str]:
    files = sorted(path for path in root.rglob("*") if path.is_file())
    aggregate = hashlib.sha256()
    total = 0
    for path in files:
        data = path.read_bytes()
        relative = path.relative_to(root).as_posix()
        total += len(data)
        aggregate.update(f"{relative}\0{len(data)}\0{hashlib.sha256(data).hexdigest()}\n".encode())
    return len(files), total, aggregate.hexdigest()


def _current_app_process_snapshot() -> tuple[int, int]:
    ps = subprocess.run(["ps", "-axo", "pid=,ppid=,command="], capture_output=True, text=True, check=True)
    processes = [line for line in ps.stdout.splitlines() if "/Users/linzezhang/Downloads/KMFA.app/" in line]
    lsof = subprocess.run(["lsof", "-nP", "-iTCP", "-sTCP:LISTEN"], capture_output=True, text=True, check=False)
    listeners = [
        line
        for line in lsof.stdout.splitlines()
        if line.split() and line.split()[0].lower().startswith("kmfa")
    ]
    return len(processes), len(listeners)


def _remote_main_oid() -> str:
    result = subprocess.run(
        ["git", "ls-remote", "origin", "refs/heads/main"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise ValidationError(result.stderr.strip() or "cannot read remote main")
    fields = result.stdout.strip().split()
    if len(fields) != 2 or fields[1] != "refs/heads/main":
        raise ValidationError("unexpected remote main response")
    return fields[0]


def _commit_is_visible(oid: str) -> bool:
    result = subprocess.run(
        ["git", "cat-file", "-e", f"{oid}^{{commit}}"],
        cwd=REPO_ROOT,
        capture_output=True,
        check=False,
    )
    return result.returncode == 0


def _is_ancestor(ancestor: str, descendant: str) -> bool:
    result = subprocess.run(
        ["git", "merge-base", "--is-ancestor", ancestor, descendant],
        cwd=REPO_ROOT,
        capture_output=True,
        check=False,
    )
    return result.returncode == 0


def _validate_evidence_refs(rows: list[dict[str, str]], errors: list[str]) -> None:
    repo_root = REPO_ROOT.resolve()
    for row in rows:
        risk_id = row.get("risk_id", "unknown")
        refs = [item.strip() for item in row.get("evidence_refs", "").split(";") if item.strip()]
        _require(bool(refs), f"{risk_id}: evidence refs missing", errors)
        for ref in refs:
            relative = Path(ref)
            safe_relative = (
                not relative.is_absolute()
                and ".." not in relative.parts
                and relative.parts
                and relative.parts[0] == "KMFA"
            )
            _require(safe_relative, f"{risk_id}: evidence ref must be repository-relative {ref}", errors)
            if not safe_relative:
                continue
            resolved = (REPO_ROOT / relative).resolve()
            _require(resolved != repo_root, f"{risk_id}: evidence ref cannot be repository root {ref}", errors)
            try:
                resolved.relative_to(repo_root)
            except ValueError:
                _require(False, f"{risk_id}: evidence ref escapes repository {ref}", errors)
                continue
            _require(resolved.exists(), f"{risk_id}: missing evidence path {ref}", errors)


def validate_v015_s01_p3_read_only_audit_gate(
    manifest_path: Path = MANIFEST_PATH,
    *,
    acceptance_path: Path = ACCEPTANCE_PATH,
    risk_path: Path = RISK_PATH,
    side_effect_path: Path = SIDE_EFFECT_PATH,
    metadata_path: Path = METADATA_PATH,
    stage_status_path: Path = STAGE_STATUS_PATH,
    source_package: Path | None = SOURCE_PACKAGE,
    require_source_package: bool = False,
    require_local_environment: bool = False,
    require_remote_observation: bool = False,
    require_clean_worktree: bool = False,
    require_dependency_validators: bool = False,
) -> dict[str, Any]:
    errors: list[str] = []
    manifest = _read_json(manifest_path)
    acceptance = _read_json(acceptance_path)
    side_effect = _read_json(side_effect_path)
    metadata = _read_json(metadata_path)
    p1 = _read_json(P1_MANIFEST_PATH)
    p2 = _read_json(P2_MANIFEST_PATH)
    gaps = _read_csv(P2_GAP_PATH)
    migrations = _read_csv(P2_MIGRATION_PATH)
    risks = _read_csv(risk_path)
    stage_status_records = [
        json.loads(line)
        for line in stage_status_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    _require(manifest.get("schema_version") == "kmfa.v015.s01_p3_read_only_audit_gate.v1", "manifest schema mismatch", errors)
    _require(manifest.get("project_id") == "KMFA", "manifest project mismatch", errors)
    _require(manifest.get("target_release") == "v1.5", "manifest target release mismatch", errors)
    _require(manifest.get("roadmap_phase_id") == "S01-P3", "manifest phase mismatch", errors)
    _require(manifest.get("execution_status") == "EXECUTION_COMPLETE", "execution status mismatch", errors)
    _require(manifest.get("acceptance_status") == "NOT_PASSED", "S01-P3 must remain NOT_PASSED", errors)
    _require(manifest.get("decision") == "NO_GO_STAGE_01_REVIEW_REQUIRED", "manifest decision mismatch", errors)
    _require(manifest.get("content_hash") == _canonical_content_hash(manifest), "manifest content hash mismatch", errors)
    _require(manifest.get("source_package", {}).get("sha256") == SOURCE_PACKAGE_SHA256, "manifest source package hash mismatch", errors)
    dependencies = manifest.get("dependencies", {})
    _require(dependencies.get("s01p1_manifest_ref") == P1_MANIFEST_PATH.relative_to(REPO_ROOT).as_posix(), "manifest S01P1 dependency ref mismatch", errors)
    _require(dependencies.get("s01p2_manifest_ref") == P2_MANIFEST_PATH.relative_to(REPO_ROOT).as_posix(), "manifest S01P2 dependency ref mismatch", errors)
    _require(dependencies.get("s01p1_acceptance_status") == "NOT_PASSED", "manifest S01P1 dependency status mismatch", errors)
    _require(dependencies.get("s01p2_acceptance_status") == "PASSED", "manifest S01P2 dependency status mismatch", errors)
    _require(dependencies.get("p3_pre_phase_commit") == P3_PRE_PHASE_COMMIT, "manifest P3 pre-phase commit mismatch", errors)

    _require(p1.get("acceptance_status") == "NOT_PASSED", "S01-P1 negative acceptance drift", errors)
    _require(p1.get("decision") == "NO_GO", "S01-P1 decision drift", errors)
    p1_findings = {item.get("terminal_finding") for item in p1.get("task_outcomes", [])}
    _require(
        p1_findings == {"RUNTIME_NOT_FOUND", "STATIC_SAMPLE_ONLY", "PARTIAL_REPO_REBUILDABLE_APP_RESTORE_ONLY"},
        "S01-P1 findings drift",
        errors,
    )
    _require(p2.get("acceptance_status") == "PASSED", "S01-P2 acceptance drift", errors)
    _require(p2.get("requirement_gap_inventory", {}).get("total") == 55, "S01-P2 requirement count drift", errors)
    _require(p2.get("requirement_gap_inventory", {}).get("accepted_v15_requirement_count") == 0, "false v1.5 accepted requirements", errors)
    _require(p2.get("migration_inventory", {}).get("total") == 37, "S01-P2 migration count drift", errors)

    conclusion = manifest.get("audit_conclusion", {})
    _require(conclusion.get("allowed_values") == ["REFACTORABLE", "RUNTIME_OBJECT_MISSING", "AUDIT_BLOCKED"], "audit conclusion enum drift", errors)
    _require(conclusion.get("selected_value") == "RUNTIME_OBJECT_MISSING", "audit conclusion must be runtime object missing", errors)
    _require(conclusion.get("selected_label_zh") == "运行对象缺失", "audit conclusion label mismatch", errors)
    for key in ("existing_runtime_refactor_authorized", "greenfield_rebuild_authorized", "audit_itself_blocked", "static_button_or_dom_used_as_acceptance"):
        _require(conclusion.get(key) is False, f"audit conclusion boundary drift: {key}", errors)
    _require(conclusion.get("audit_evidence_complete_for_conclusion") is True, "audit conclusion evidence incomplete", errors)
    _require(conclusion.get("change_control_required_for_greenfield") is True, "greenfield change control must be required", errors)

    risk_ids = [row.get("risk_id", "") for row in risks]
    _require(len(risks) == 24, "risk row count must be 24", errors)
    _require(len(risk_ids) == len(set(risk_ids)), "duplicate risk ID", errors)
    _require(set(risk_ids) == EXPECTED_RISK_IDS, "risk ID set mismatch", errors)
    _require(dict(Counter(row.get("priority") for row in risks)) == EXPECTED_PRIORITY_COUNTS, "risk priority counts mismatch", errors)
    _require(dict(Counter(row.get("unknown_category") for row in risks)) == EXPECTED_RISK_CATEGORIES, "risk category counts mismatch", errors)
    migration_ids = {row["capability_id"] for row in migrations}
    covered_requirements: set[str] = set()
    for row in risks:
        risk_id = row.get("risk_id", "")
        _require(row.get("status") == "OPEN_WITH_PLAN", f"{risk_id}: risk must remain OPEN_WITH_PLAN", errors)
        _require(bool(re.fullmatch(r"[A-Z][A-Z0-9_]+", row.get("owner_role", ""))), f"{risk_id}: invalid owner role", errors)
        stages = [item for item in row.get("resolution_stages", "").split(";") if item]
        _require(bool(stages), f"{risk_id}: resolution Stage missing", errors)
        _require(all(re.fullmatch(r"S(?:0[2-9]|1[0-9]|2[0-4])", item) for item in stages), f"{risk_id}: invalid resolution Stage", errors)
        _require(bool(row.get("stop_condition", "").strip()), f"{risk_id}: stop condition missing", errors)
        requirement_ids = [item for item in row.get("related_requirement_ids", "").split(";") if item]
        capability_ids = [item for item in row.get("related_capability_ids", "").split(";") if item]
        _require(bool(requirement_ids), f"{risk_id}: related requirement IDs missing", errors)
        _require(all(re.fullmatch(r"R0(?:0[1-9]|[1-4][0-9]|5[0-5])", item) for item in requirement_ids), f"{risk_id}: invalid requirement ID", errors)
        _require(all(item in migration_ids for item in capability_ids), f"{risk_id}: unknown capability ID", errors)
        covered_requirements.update(requirement_ids)
    _validate_evidence_refs(risks, errors)
    _require(CRITICAL_RISK_IDS.issubset(set(risk_ids)), "critical risk IDs missing", errors)
    high_risk_requirements = {
        row["requirement_id"]
        for row in gaps
        if row["priority"] in {"P0", "P1"}
        and (
            row["severity"] in {"CRITICAL", "HIGH"}
            or row["current_status"] in {"MISSING", "UNVERIFIED", "CONFLICTING_POLICY"}
        )
    }
    _require(high_risk_requirements.issubset(covered_requirements), "high-risk requirement coverage incomplete", errors)
    recommended_stage_by_requirement = {row["requirement_id"]: row["recommended_stage"] for row in gaps}
    resolution_stage_coverage: dict[str, set[str]] = {}
    for row in risks:
        row_stages = {item for item in row.get("resolution_stages", "").split(";") if item}
        for requirement_id in row.get("related_requirement_ids", "").split(";"):
            if requirement_id:
                resolution_stage_coverage.setdefault(requirement_id, set()).update(row_stages)
    stage_chain_gaps = sorted(
        requirement_id
        for requirement_id in high_risk_requirements
        if recommended_stage_by_requirement.get(requirement_id)
        not in resolution_stage_coverage.get(requirement_id, set())
    )
    _require(not stage_chain_gaps, f"recommended resolution Stage chain incomplete: {stage_chain_gaps}", errors)
    p0_without_plan = sum(
        row.get("priority") == "P0"
        and (
            not row.get("owner_role", "").strip()
            or not row.get("resolution_stages", "").strip()
            or not row.get("stop_condition", "").strip()
        )
        for row in risks
    )
    _require(p0_without_plan == 0, "P0 risk without plan", errors)

    _require(side_effect.get("schema_version") == "kmfa.v015.s01_p3_side_effect_snapshot.v1", "side-effect schema mismatch", errors)
    _require(side_effect.get("snapshot_status") == "UNEXPECTED_LOCAL_GIT_TRACKING_REF_CHANGE_DETECTED_WITH_UNVERIFIED_ATTRIBUTION", "side-effect result must retain local Git change and attribution limitation", errors)
    _require(side_effect.get("execution_status") == "EXECUTION_COMPLETE", "T03 execution status mismatch", errors)
    _require(side_effect.get("acceptance_status") == "NOT_PASSED", "T03 acceptance must remain NOT_PASSED", errors)
    _require(side_effect.get("terminal_finding") == "UNEXPECTED_LOCAL_GIT_STATE_CHANGE_AND_INSUFFICIENT_PREAUDIT_TELEMETRY", "T03 finding mismatch", errors)
    pre_paths = _pre_p3_paths()
    classified = _classify_pre_p3_paths(pre_paths)
    _require(len(pre_paths) == PRE_P3_CHANGED_PATH_COUNT, "pre-P3 changed path count mismatch", errors)
    _require(hashlib.sha256("\n".join(pre_paths).encode()).hexdigest() == PRE_P3_PATH_LIST_SHA256, "pre-P3 path list hash mismatch", errors)
    expected_pre_counts = {
        "stage_artifacts": 17,
        "governance_docs": 12,
        "audit_metadata": 3,
        "audit_validator_tests": 4,
        "top_level_delivery_docs": 5,
        "unexpected": 0,
    }
    _require({key: len(value) for key, value in classified.items()} == expected_pre_counts, "pre-P3 path classification mismatch", errors)
    tracked = side_effect.get("tracked_diff_before_p3", {})
    _require(tracked.get("changed_file_count") == 41, "side-effect tracked count mismatch", errors)
    _require(tracked.get("changed_path_list_sha256") == PRE_P3_PATH_LIST_SHA256, "side-effect path hash mismatch", errors)
    expected_side_counts = {"stage_artifacts": 17, "governance_docs": 12, "audit_metadata": 3, "audit_validator_tests": 4, "top_level_delivery_docs": 5, "unexpected": 0, "product_runtime_code": 0, "database_files": 0}
    _require(tracked.get("categories") == expected_side_counts, "side-effect category counts mismatch", errors)
    _require(tracked.get("expected_audit_code_writes_nonzero") is True, "audit code writes must be disclosed", errors)
    _require(tracked.get("expected_governance_metadata_writes_nonzero") is True, "metadata writes must be disclosed", errors)
    _require(tracked.get("zero_code_change_claim_allowed") is False, "zero code change claim forbidden", errors)
    _require(tracked.get("zero_metadata_change_claim_allowed") is False, "zero metadata change claim forbidden", errors)

    phase_paths = _phase_paths()
    _, unexpected_phase_paths = _classify_phase_paths(phase_paths)
    _require(not unexpected_phase_paths, f"unexpected P3 paths: {unexpected_phase_paths}", errors)
    _require(not any(Path(path).suffix.lower() in {".db", ".sqlite", ".sqlite3", ".duckdb", ".mdb"} for path in phase_paths), "database file changed in P3", errors)
    observed_summary = side_effect.get("p3_observed_change_summary")
    _require(isinstance(observed_summary, dict), "P3 observed change summary missing", errors)
    if isinstance(observed_summary, dict):
        expected_p3_counts = {
            "stage_artifacts": 8,
            "governance_docs": 12,
            "audit_metadata": 2,
            "audit_validator_tests": 2,
            "top_level_delivery_docs": 5,
            "unexpected": 0,
            "product_runtime_code": 0,
            "database_files": 0,
        }
        _require(observed_summary.get("changed_file_count") == len(phase_paths), "P3 observed path count mismatch", errors)
        _require(observed_summary.get("changed_path_list_sha256") == hashlib.sha256("\n".join(phase_paths).encode()).hexdigest(), "P3 observed path hash mismatch", errors)
        _require(observed_summary.get("categories") == expected_p3_counts, "P3 observed path category mismatch", errors)
        _require(observed_summary.get("expected_code_or_metadata_writes_detected") is True, "P3 expected code/metadata writes not disclosed", errors)
        _require(observed_summary.get("literal_taskpack_zero_code_condition_met") is False, "P3 false zero-code condition", errors)
        _require(observed_summary.get("literal_taskpack_zero_metadata_condition_met") is False, "P3 false zero-metadata condition", errors)
        _require(observed_summary.get("unexpected_worktree_product_path_count") == 0, "P3 unexpected worktree/product path count mismatch", errors)
        _require(observed_summary.get("product_runtime_source_change_count") == 0, "P3 product source change count mismatch", errors)
        _require(observed_summary.get("database_file_change_count") == 0, "P3 database change count mismatch", errors)
    expected_scope = side_effect.get("p3_expected_change_scope", {})
    for key in ("product_source_change_allowed", "database_change_allowed", "app_change_allowed", "raw_change_allowed"):
        _require(expected_scope.get(key) is False, f"P3 expected scope boundary drift: {key}", errors)

    private = side_effect.get("private_runtime_observation", {})
    _require(private.get("expected_evidence_file_count") == 16, "private evidence count mismatch", errors)
    _require(private.get("s01p1_t01_file_count") == 5, "private T01 count mismatch", errors)
    _require(private.get("s01p1_t02_file_count") == 10, "private T02 count mismatch", errors)
    _require(private.get("one_shot_launch_receipt_count") == 1, "one-shot receipt count mismatch", errors)
    _require(private.get("unexpected_private_write_count") == 0, "unexpected private write count mismatch", errors)
    _require(private.get("private_payload_committed") is False, "private payload must not be committed", errors)

    app = side_effect.get("installed_app", {})
    _require(app.get("aggregate_sha256_pre") == APP_AGGREGATE_SHA256, "App pre hash mismatch", errors)
    _require(app.get("aggregate_sha256_post_observed") == APP_AGGREGATE_SHA256, "App post hash mismatch", errors)
    _require(app.get("regular_file_count_pre") == app.get("regular_file_count_post_observed") == 13, "App file count mismatch", errors)
    _require(app.get("regular_file_bytes_pre") == app.get("regular_file_bytes_post_observed") == 830331, "App byte count mismatch", errors)
    _require(app.get("aggregate_match") is True, "App aggregate must match", errors)
    _require(app.get("code_signature_valid") is True, "App signature status mismatch", errors)
    _require(app.get("reinstalled") is False and app.get("modified") is False, "App mutation boundary drift", errors)

    raw = side_effect.get("raw_root", {})
    _require(raw.get("pre_sentinel") == RAW_SENTINEL_FULL, "raw pre-sentinel document drift", errors)
    _require(raw.get("post_observed_sentinel") == RAW_SENTINEL_FULL, "raw post-sentinel document drift", errors)
    _require(raw.get("shallow_sentinel_match") is True, "raw shallow sentinel must match", errors)
    _require(raw.get("recursive_pre_snapshot_available") is False, "raw recursive pre-snapshot must remain unavailable", errors)
    _require(raw.get("recursive_integrity") == "UNVERIFIED", "raw recursive integrity must remain UNVERIFIED", errors)
    for key in ("names_captured", "contents_read", "hashes_computed", "mutation_performed"):
        _require(raw.get(key) is False, f"raw boundary drift: {key}", errors)

    process = side_effect.get("process_observation", {})
    _require(process.get("expected_one_shot_app_launch") is True, "one-shot App launch must be disclosed", errors)
    _require(process.get("historical_process_monitoring") == "PARTIAL_RECEIPT_ONLY", "historical process monitoring must remain partial", errors)
    _require(process.get("complete_continuous_monitoring_available") is False, "continuous monitoring false claim", errors)
    _require(process.get("current_persistent_app_process_count_post_observed") == 0, "persistent App process recorded", errors)
    _require(process.get("current_app_listener_count_post_observed") == 0, "App listener recorded", errors)
    _require(process.get("current_persistent_app_process_count_pre") == 0, "pre-phase persistent App process mismatch", errors)
    _require(process.get("current_app_listener_count_pre") == 0, "pre-phase App listener mismatch", errors)

    database = side_effect.get("database_observation", {})
    _require(database.get("runtime_database_bound") is False, "runtime DB binding false claim", errors)
    _require(database.get("tracked_database_file_change_count") == 0, "tracked DB change mismatch", errors)
    _require(database.get("app_bundle_database_file_count") == 0, "App DB file count mismatch", errors)
    _require(database.get("external_database_integrity") == "UNVERIFIED_OR_NOT_APPLICABLE", "external DB integrity false claim", errors)
    _require(database.get("product_database_mutation_detected") is False, "product DB mutation detected", errors)
    remote = side_effect.get("remote_repository_observation", {})
    _require(remote.get("historical_tracking_main_oid") == ORIGIN_MAIN_EXPECTED, "remote tracking baseline mismatch", errors)
    _require(remote.get("local_tracking_ref_oid_observed") == REMOTE_MAIN_SNAPSHOT, "local tracking snapshot mismatch", errors)
    _require(remote.get("remote_main_oid_observed") == REMOTE_MAIN_SNAPSHOT, "remote main observation mismatch", errors)
    _require(remote.get("remote_main_external_drift_detected") is True, "remote main drift must be disclosed", errors)
    _require(remote.get("local_tracking_ref_changed_during_p3") is True, "local tracking ref drift must be disclosed", errors)
    _require(remote.get("local_tracking_ref_reflog_operation") == "fetch origin main: fast-forward", "local tracking reflog operation mismatch", errors)
    _require(remote.get("local_tracking_ref_reflog_time") == "2026-07-13T10:51:52+10:00", "local tracking reflog time mismatch", errors)
    _require(remote.get("fetch_attribution") == "UNVERIFIED_CONCURRENT_SHARED_REPOSITORY_CHANGE", "fetch attribution must remain unverified", errors)
    _require(remote.get("current_task_push_performed") is False, "current task push boundary drift", errors)
    _require(remote.get("classification") == "CONCURRENT_SHARED_REPOSITORY_CHANGE_ATTRIBUTION_UNVERIFIED", "repository drift classification mismatch", errors)
    _require(remote.get("final_merge_rebase_and_upload_revalidation_required") is True, "final merge revalidation must be required", errors)

    classification = side_effect.get("side_effect_classification", {})
    _require(classification.get("expected_audit_evidence_writes_detected") is True, "expected audit writes not disclosed", errors)
    _require(classification.get("p3_audit_validator_test_writes_detected") is True, "P3 validator/test writes not disclosed", errors)
    _require(classification.get("p3_audit_metadata_writes_detected") is True, "P3 metadata writes not disclosed", errors)
    _require(classification.get("literal_zero_code_change_condition_met") is False, "false zero-code classification", errors)
    _require(classification.get("literal_zero_metadata_change_condition_met") is False, "false zero-metadata classification", errors)
    _require(classification.get("governance_audit_metadata_writes_detected") is True, "governance metadata writes not disclosed", errors)
    _require(classification.get("external_remote_main_drift_detected") is True, "external remote drift not disclosed", errors)
    _require(classification.get("unexpected_local_tracking_ref_change_detected") is True, "unexpected local tracking ref change not disclosed", errors)
    _require(classification.get("unexpected_worktree_product_change_count") == 0, "unexpected worktree/product change count mismatch", errors)
    _require(classification.get("unexpected_shared_git_ref_change_count") == 1, "unexpected shared Git ref change count mismatch", errors)
    for key in ("product_runtime_source_mutation_detected", "product_database_mutation_detected", "business_metadata_mutation_detected", "app_mutation_detected", "raw_root_sentinel_mutation_detected", "persistent_app_process_or_listener_detected"):
        _require(classification.get(key) is False, f"side-effect mutation boundary drift: {key}", errors)
    boundaries = side_effect.get("phase_boundaries", {})
    _require(set(boundaries) == EXPECTED_P3_PHASE_BOUNDARY_KEYS, "P3 phase boundary key set mismatch", errors)
    for key, value in boundaries.items():
        _require(value is False, f"phase boundary must remain false: {key}", errors)
    limitations = side_effect.get("limitations", [])
    _require(isinstance(limitations, list) and len(limitations) == 4, "side-effect limitations count mismatch", errors)
    limitations_text = "\n".join(str(item) for item in limitations)
    for token in ("raw 递归指纹", "持续进程监控", "零代码或零 metadata", "归因未验证"):
        _require(token in limitations_text, f"side-effect limitation missing: {token}", errors)

    _require(acceptance.get("schema_version") == "kmfa.v015.s01_p3_acceptance_matrix.v1", "acceptance schema mismatch", errors)
    _require(acceptance.get("phase_acceptance_status") == "NOT_PASSED", "acceptance Phase must remain NOT_PASSED", errors)
    _require(acceptance.get("quality_gate_passed") is False, "quality gate must remain false", errors)
    checks = acceptance.get("checks", [])
    _require(len(checks) == acceptance.get("check_count") == 22, "acceptance check count mismatch", errors)
    _require(sum(item.get("result") == "PASS" for item in checks) == acceptance.get("check_pass_count") == 19, "acceptance PASS count mismatch", errors)
    _require(sum(item.get("result") == "FAIL" for item in checks) == acceptance.get("check_fail_count") == 3, "acceptance FAIL count mismatch", errors)
    checks_by_id = {str(item.get("check_id")): item for item in checks}
    _require(len(checks_by_id) == len(checks), "duplicate acceptance check ID", errors)
    _require(set(checks_by_id) == set(EXPECTED_ACCEPTANCE_CHECKS), "acceptance check ID set mismatch", errors)
    for check_id, (result, finding) in EXPECTED_ACCEPTANCE_CHECKS.items():
        item = checks_by_id.get(check_id, {})
        _require(item.get("result") == result, f"acceptance result mismatch: {check_id}", errors)
        _require(item.get("finding") == finding, f"acceptance finding mismatch: {check_id}", errors)
        _require(bool(str(item.get("evidence", "")).strip()), f"acceptance evidence missing: {check_id}", errors)
    _require(acceptance.get("stage_01_passed") is False, "Stage 01 must remain false", errors)
    _require(acceptance.get("stage_01_review_required") is True, "Stage review must be required", errors)
    _require(acceptance.get("stage_01_review_performed") is False, "Stage review must not be performed", errors)
    _require(acceptance.get("s02_entry_allowed") is False, "S02 entry must remain false", errors)
    _require(acceptance.get("next_allowed_run") == "STAGE-01-REVIEW only", "acceptance next run mismatch", errors)
    acceptance_outcome_list = acceptance.get("task_outcomes", [])
    acceptance_outcomes = {item.get("task_id"): item for item in acceptance_outcome_list}
    _require(len(acceptance_outcome_list) == len(acceptance_outcomes) == 3, "acceptance task outcomes must be three unique rows", errors)
    _require(set(acceptance_outcomes) == set(EXPECTED_TASK_OUTCOMES), "acceptance task IDs mismatch", errors)
    for task_id, (status, finding, _) in EXPECTED_TASK_OUTCOMES.items():
        item = acceptance_outcomes.get(task_id, {})
        _require(item.get("acceptance_status") == status, f"acceptance task status mismatch: {task_id}", errors)
        _require(item.get("terminal_finding") == finding, f"acceptance task finding mismatch: {task_id}", errors)

    outcomes = manifest.get("task_outcomes", [])
    outcomes_by_id = {item.get("task_id"): item for item in outcomes}
    _require(len(outcomes) == len(outcomes_by_id) == 3, "manifest task outcomes must be three unique rows", errors)
    _require(set(outcomes_by_id) == set(EXPECTED_TASK_OUTCOMES), "manifest task IDs mismatch", errors)
    for task_id, (status, finding, evidence) in EXPECTED_TASK_OUTCOMES.items():
        item = outcomes_by_id.get(task_id, {})
        _require(item.get("acceptance_status") == status, f"task acceptance mismatch: {task_id}", errors)
        _require(item.get("terminal_finding") == finding, f"task finding mismatch: {task_id}", errors)
        _require(item.get("evidence") == evidence, f"task evidence mismatch: {task_id}", errors)
        _require((ARTIFACT_ROOT / evidence).is_file(), f"task evidence missing: {task_id}", errors)
    risk_summary = manifest.get("risk_register", {})
    _require(risk_summary.get("total") == 24, "manifest risk total mismatch", errors)
    _require(risk_summary.get("priority_counts") == EXPECTED_PRIORITY_COUNTS, "manifest risk priority mismatch", errors)
    _require(risk_summary.get("category_counts") == EXPECTED_RISK_CATEGORIES, "manifest risk category mismatch", errors)
    _require(risk_summary.get("p0_without_owner_stage_stop_count") == 0, "manifest P0 plan gap", errors)
    _require(risk_summary.get("risk_plan_complete") is True and risk_summary.get("risk_resolution_complete") is False, "manifest risk state mismatch", errors)
    side_summary = manifest.get("side_effect_assessment", {})
    _require(side_summary.get("selected_result") == "UNEXPECTED_LOCAL_GIT_TRACKING_REF_CHANGE_DETECTED_WITH_UNVERIFIED_ATTRIBUTION", "manifest side-effect result mismatch", errors)
    _require(side_summary.get("t03_acceptance_status") == "NOT_PASSED", "manifest T03 acceptance mismatch", errors)
    _require(side_summary.get("unexpected_worktree_product_change_count") == 0, "manifest worktree/product change count mismatch", errors)
    _require(side_summary.get("unexpected_shared_git_ref_change_count") == 1, "manifest shared Git ref change count mismatch", errors)
    _require(side_summary.get("raw_recursive_integrity") == "UNVERIFIED", "manifest raw recursive status mismatch", errors)
    _require(side_summary.get("historical_process_monitoring") == "PARTIAL_RECEIPT_ONLY", "manifest process history mismatch", errors)
    _require(
        side_summary.get("secondary_findings")
        == ["EXPECTED_AUDIT_CODE_METADATA_WRITES", "UNEXPECTED_LOCAL_TRACKING_REF_CHANGE_ATTRIBUTION_UNVERIFIED", "REMOTE_MAIN_EXTERNAL_DRIFT"],
        "manifest secondary findings mismatch",
        errors,
    )
    _require(side_summary.get("remote_main_external_drift_detected") is True, "manifest remote drift mismatch", errors)
    _require(side_summary.get("local_tracking_ref_changed_during_p3") is True, "manifest local tracking drift mismatch", errors)
    _require(side_summary.get("fetch_attribution") == "UNVERIFIED_CONCURRENT_SHARED_REPOSITORY_CHANGE", "manifest fetch attribution mismatch", errors)
    _require(side_summary.get("current_task_push_performed") is False, "manifest push boundary drift", errors)
    gate = manifest.get("phase_gate", {})
    _require(set(gate) == EXPECTED_MANIFEST_PHASE_GATE_KEYS, "manifest phase gate key set mismatch", errors)
    _require(gate.get("task_execution_complete_count") == 3, "phase execution count mismatch", errors)
    _require(gate.get("task_acceptance_passed_count") == 2, "phase accepted task count mismatch", errors)
    _require(gate.get("s01p3_acceptance_passed") is False, "S01-P3 pass flag must be false", errors)
    _require(gate.get("stage_01_phase_execution_complete") is True, "Stage phase execution flag mismatch", errors)
    _require(gate.get("stage_01_passed") is False, "Stage 01 pass flag must be false", errors)
    _require(gate.get("stage_01_review_required") is True, "Stage review required flag mismatch", errors)
    _require(gate.get("next_allowed_run") == "STAGE-01-REVIEW", "manifest next run mismatch", errors)
    for key in ("stage_01_review_performed", "next_stage_started", "product_fix_performed", "github_upload_performed", "app_reinstall_performed", "business_execution_performed"):
        _require(gate.get(key) is False, f"manifest boundary drift: {key}", errors)
    release_state = manifest.get("release_state", {})
    _require(set(release_state) == EXPECTED_RELEASE_STATE_KEYS, "release state key set mismatch", errors)
    _require(all(value is False for value in release_state.values()), "release state must remain false", errors)
    public_safety = manifest.get("public_repo_safety", {})
    _require(set(public_safety) == EXPECTED_PUBLIC_SAFETY_KEYS, "public safety key set mismatch", errors)
    _require(all(value is False for value in public_safety.values()), "public safety boundary drift", errors)
    artifact_refs = manifest.get("artifact_refs", {})
    _require(artifact_refs == EXPECTED_ARTIFACT_REFS, "manifest artifact refs mismatch", errors)
    for label, ref in artifact_refs.items():
        _require((REPO_ROOT / str(ref)).is_file(), f"missing artifact ref {label}: {ref}", errors)

    _require(metadata.get("schema_version") == "kmfa.metadata.v015.s01_p3_read_only_audit_gate.v1", "metadata schema mismatch", errors)
    _require(metadata.get("manifest_ref") == MANIFEST_PATH.relative_to(REPO_ROOT).as_posix(), "metadata manifest ref mismatch", errors)
    _require(metadata.get("acceptance_ref") == ACCEPTANCE_PATH.relative_to(REPO_ROOT).as_posix(), "metadata acceptance ref mismatch", errors)
    _require(metadata.get("audit_conclusion") == "RUNTIME_OBJECT_MISSING", "metadata conclusion mismatch", errors)
    _require(metadata.get("acceptance_status") == "NOT_PASSED", "metadata acceptance mismatch", errors)
    _require(metadata.get("accepted_task_count") == 2 and metadata.get("total_task_count") == 3, "metadata task counts mismatch", errors)
    _require(metadata.get("terminal_finding") == "UNEXPECTED_LOCAL_GIT_STATE_CHANGE_AND_INSUFFICIENT_PREAUDIT_TELEMETRY", "metadata finding mismatch", errors)
    _require(metadata.get("no_side_effects_fully_proven") is False, "metadata false no-side-effect proof", errors)
    _require(metadata.get("no_unexpected_change_detected") is False, "metadata must disclose unexpected shared Git ref change", errors)
    _require(metadata.get("unexpected_worktree_product_change_count") == 0, "metadata worktree/product change count mismatch", errors)
    _require(metadata.get("unexpected_shared_git_ref_change_count") == 1, "metadata shared Git ref change count mismatch", errors)
    _require(metadata.get("raw_recursive_integrity") == "UNVERIFIED", "metadata raw recursive mismatch", errors)
    _require(metadata.get("historical_process_monitoring") == "PARTIAL_RECEIPT_ONLY", "metadata process history mismatch", errors)
    _require(metadata.get("remote_main_external_drift_detected") is True, "metadata remote drift mismatch", errors)
    _require(metadata.get("historical_tracking_main_oid") == ORIGIN_MAIN_EXPECTED, "metadata historical tracking mismatch", errors)
    _require(metadata.get("local_tracking_ref_oid_observed") == REMOTE_MAIN_SNAPSHOT, "metadata local tracking snapshot mismatch", errors)
    _require(metadata.get("remote_main_oid_observed") == REMOTE_MAIN_SNAPSHOT, "metadata remote main mismatch", errors)
    _require(metadata.get("local_tracking_ref_changed_during_p3") is True, "metadata local tracking drift mismatch", errors)
    _require(metadata.get("local_tracking_ref_reflog_operation") == "fetch origin main: fast-forward", "metadata local tracking reflog mismatch", errors)
    _require(metadata.get("local_tracking_ref_reflog_time") == "2026-07-13T10:51:52+10:00", "metadata local tracking reflog time mismatch", errors)
    _require(metadata.get("fetch_attribution") == "UNVERIFIED_CONCURRENT_SHARED_REPOSITORY_CHANGE", "metadata fetch attribution mismatch", errors)
    _require(metadata.get("current_task_push_performed") is False, "metadata push boundary drift", errors)
    _require(metadata.get("stage_01_passed") is False and metadata.get("s02_entry_allowed") is False, "metadata Stage/S02 boundary drift", errors)
    _require(metadata.get("next_allowed_run") == "STAGE-01-REVIEW", "metadata next run mismatch", errors)

    p3_status_records = [
        row for row in stage_status_records
        if row.get("phase_id") == "V015_S01_P3_READ_ONLY_AUDIT_GATE"
    ]
    _require(len(p3_status_records) >= 2, "post-ref-change P3 stage status missing", errors)
    latest_p3_status = p3_status_records[-1] if p3_status_records else {}
    _require(set(latest_p3_status) == EXPECTED_LATEST_STAGE_STATUS_KEYS, "latest P3 stage status key set mismatch", errors)
    _require(latest_p3_status.get("schema_version") == "kmfa.stage_status.v1", "latest P3 stage status schema mismatch", errors)
    _require(latest_p3_status.get("record_type") == "phase_status", "latest P3 stage status record type mismatch", errors)
    _require(latest_p3_status.get("task_id") == "KMFA-V015-S01-P3-READ-ONLY-AUDIT-GATE-20260713", "latest P3 stage status task mismatch", errors)
    _require(latest_p3_status.get("acceptance_id") == "ACC-KMFA-V015-S01-P3-READ-ONLY-AUDIT-GATE", "latest P3 stage status acceptance mismatch", errors)
    _require(latest_p3_status.get("updated_at") == "2026-07-13T11:05:05+10:00", "latest P3 stage status time mismatch", errors)
    _require(latest_p3_status.get("evidence_ref") == MANIFEST_PATH.relative_to(REPO_ROOT).as_posix(), "latest P3 stage status evidence mismatch", errors)
    _require(latest_p3_status.get("terminal_finding") == "UNEXPECTED_LOCAL_GIT_STATE_CHANGE_AND_INSUFFICIENT_PREAUDIT_TELEMETRY", "latest P3 stage status finding mismatch", errors)
    _require(latest_p3_status.get("unexpected_worktree_product_change_count") == 0, "latest P3 stage status worktree/product count mismatch", errors)
    _require(latest_p3_status.get("unexpected_shared_git_ref_change_count") == 1, "latest P3 stage status shared Git ref count mismatch", errors)
    _require(latest_p3_status.get("fetch_attribution") == "UNVERIFIED_CONCURRENT_SHARED_REPOSITORY_CHANGE", "latest P3 stage status fetch attribution mismatch", errors)
    _require(latest_p3_status.get("local_tracking_ref_oid_observed") == REMOTE_MAIN_SNAPSHOT, "latest P3 stage status local tracking mismatch", errors)
    _require(latest_p3_status.get("remote_main_oid_observed") == REMOTE_MAIN_SNAPSHOT, "latest P3 stage status remote snapshot mismatch", errors)
    _require(latest_p3_status.get("current_task_push_performed") is False, "latest P3 stage status push boundary mismatch", errors)
    _require(latest_p3_status.get("stage_01_passed") is False and latest_p3_status.get("s02_entry_allowed") is False, "latest P3 stage status downstream boundary mismatch", errors)

    package_available = source_package is not None and source_package.is_file()
    if require_source_package:
        _require(package_available, "source package required but missing", errors)
    if package_available:
        _require(_sha256_file(source_package) == SOURCE_PACKAGE_SHA256, "source package SHA-256 mismatch", errors)

    if require_local_environment:
        _require(APP_PATH.is_dir(), "installed App missing", errors)
        if APP_PATH.is_dir():
            count, byte_count, aggregate = _tree_fingerprint(APP_PATH)
            _require((count, byte_count, aggregate) == (13, 830331, APP_AGGREGATE_SHA256), "installed App fingerprint drift", errors)
            signature = subprocess.run(["codesign", "--verify", "--deep", "--strict", str(APP_PATH)], capture_output=True, check=False)
            _require(signature.returncode == 0, "installed App signature invalid", errors)
            app_db_count = sum(path.suffix.lower() in {".db", ".sqlite", ".sqlite3", ".duckdb"} for path in APP_PATH.rglob("*") if path.is_file())
            _require(app_db_count == 0, "unexpected App database file", errors)
        _require(RAW_ROOT.is_dir(), "raw root missing", errors)
        if RAW_ROOT.is_dir():
            stat_value = RAW_ROOT.stat()
            _require(stat_value.st_dev == RAW_SENTINEL["device"], "raw device drift", errors)
            _require(stat_value.st_ino == RAW_SENTINEL["inode"], "raw inode drift", errors)
            _require(stat_value.st_size == RAW_SENTINEL["size"], "raw size drift", errors)
            _require(int(stat_value.st_mtime) == RAW_SENTINEL["mtime_epoch"], "raw mtime drift", errors)
        process_count, listener_count = _current_app_process_snapshot()
        _require(process_count == 0, "persistent KMFA App process detected", errors)
        _require(listener_count == 0, "KMFA listener detected", errors)
        t01_count = sum(1 for path in (REPO_ROOT / "KMFA/.codex_private_runtime/V015_S01_P1_T01_RUNTIME_FACTS").rglob("*") if path.is_file())
        t02_count = sum(1 for path in (REPO_ROOT / "KMFA/.codex_private_runtime/V015_S01_P1_T02_STATIC_ROUTE_AUDIT").rglob("*") if path.is_file())
        receipt = REPO_ROOT / "KMFA/.codex_private_runtime/v014_app_reinstall_and_parity/latest_app_launch_receipt.txt"
        _require((t01_count, t02_count, receipt.is_file()) == (5, 10, True), "private audit evidence observation drift", errors)
        local_tracking_oid = _git_text(["rev-parse", "origin/main"])
        _require(bool(re.fullmatch(r"[0-9a-f]{40}", local_tracking_oid)), "local origin/main tracking ref invalid", errors)
        if _commit_is_visible(local_tracking_oid):
            _require(_is_ancestor(ORIGIN_MAIN_EXPECTED, local_tracking_oid), "v0.1.4 baseline is not an ancestor of local origin/main", errors)

    if require_remote_observation:
        live_remote_oid = _remote_main_oid()
        _require(bool(re.fullmatch(r"[0-9a-f]{40}", live_remote_oid)), "live remote main OID invalid", errors)
        _require(live_remote_oid != ORIGIN_MAIN_EXPECTED, "recorded external remote drift is no longer observable", errors)
        _require(_commit_is_visible(live_remote_oid), "live remote main commit is not locally verifiable", errors)
        if _commit_is_visible(live_remote_oid):
            _require(_is_ancestor(ORIGIN_MAIN_EXPECTED, live_remote_oid), "v0.1.4 baseline is not an ancestor of live remote main", errors)

    if require_dependency_validators:
        from KMFA.tools.check_v015_s01_p1_legacy_reference_baseline import validate_v015_s01_p1_legacy_reference_baseline
        from KMFA.tools.check_v015_s01_p2_implementation_spec_gap_inventory import validate_v015_s01_p2_implementation_spec_gap_inventory
        validate_v015_s01_p1_legacy_reference_baseline(
            require_private_evidence=True,
            require_installed_app=True,
            require_raw_root=True,
            require_remote_main=False,
            source_package=SOURCE_PACKAGE,
        )
        validate_v015_s01_p2_implementation_spec_gap_inventory(
            source_package=SOURCE_PACKAGE,
            require_source_package=True,
            require_raw_root=True,
        )

    if require_clean_worktree:
        _require(not _git_text(["status", "--porcelain=v1"]), "worktree must be clean", errors)
        head = _git_text(["rev-parse", "HEAD"])
        result_parent = _git_text(["rev-parse", f"{P3_RESULT_COMMIT}^"])
        _require(result_parent == P3_PRE_PHASE_COMMIT, "P3 result commit provenance mismatch", errors)
        _require(_is_ancestor(P3_RESULT_COMMIT, head), "P3 result commit must remain an ancestor of HEAD", errors)

    if errors:
        raise ValidationError("\n".join(errors))
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    parser.add_argument("--acceptance", type=Path, default=ACCEPTANCE_PATH)
    parser.add_argument("--risk-register", type=Path, default=RISK_PATH)
    parser.add_argument("--side-effect", type=Path, default=SIDE_EFFECT_PATH)
    parser.add_argument("--metadata", type=Path, default=METADATA_PATH)
    parser.add_argument("--source-package", type=Path, default=SOURCE_PACKAGE)
    parser.add_argument("--require-source-package", action="store_true")
    parser.add_argument("--require-local-environment", action="store_true")
    parser.add_argument("--require-remote-observation", action="store_true")
    parser.add_argument("--require-clean-worktree", action="store_true")
    parser.add_argument("--require-dependency-validators", action="store_true")
    args = parser.parse_args()
    try:
        result = validate_v015_s01_p3_read_only_audit_gate(
            args.manifest,
            acceptance_path=args.acceptance,
            risk_path=args.risk_register,
            side_effect_path=args.side_effect,
            metadata_path=args.metadata,
            source_package=args.source_package,
            require_source_package=args.require_source_package,
            require_local_environment=args.require_local_environment,
            require_remote_observation=args.require_remote_observation,
            require_clean_worktree=args.require_clean_worktree,
            require_dependency_validators=args.require_dependency_validators,
        )
    except (OSError, ValueError, ValidationError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    print(json.dumps({
        "status": "PASS",
        "phase": result["roadmap_phase_id"],
        "execution_status": result["execution_status"],
        "acceptance_status": result["acceptance_status"],
        "audit_conclusion": result["audit_conclusion"]["selected_value"],
        "accepted_tasks": result["phase_gate"]["task_acceptance_passed_count"],
        "total_tasks": result["phase_gate"]["task_execution_complete_count"],
        "next_allowed_run": result["phase_gate"]["next_allowed_run"],
    }, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
