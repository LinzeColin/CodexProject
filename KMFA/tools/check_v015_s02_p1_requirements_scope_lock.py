#!/usr/bin/env python3
"""Validate KMFA v1.5 S02-P1 requirements merge and scope lock evidence."""

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
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = REPO_ROOT / "KMFA"
ARTIFACT_ROOT = PROJECT_ROOT / "stage_artifacts/V015_S02_P1_REQUIREMENTS_SCOPE_LOCK"
MANIFEST_PATH = ARTIFACT_ROOT / "machine/s02_p1_requirements_scope_lock_manifest.json"
REQUIREMENTS_PATH = ARTIFACT_ROOT / "machine/requirements_ledger_public_safe.csv"
BUSINESS_LINES_PATH = ARTIFACT_ROOT / "machine/business_line_matrix_public_safe.csv"
SCOPE_LOCK_PATH = ARTIFACT_ROOT / "machine/scope_lock_dispositions_public_safe.csv"
VALIDATION_RESULTS_PATH = ARTIFACT_ROOT / "machine/validation_results.jsonl"
PROJECT_GOVERNANCE_PATH = PROJECT_ROOT / "docs/governance/project.yaml"
ROADMAP_GOVERNANCE_PATH = PROJECT_ROOT / "docs/governance/roadmap.yaml"
AGENTS_PATH = PROJECT_ROOT / "AGENTS.md"
EVENTS_PATH = PROJECT_ROOT / "docs/governance/events.jsonl"
MODEL_SPEC_PATH = PROJECT_ROOT / "docs/governance/MODEL_SPEC.md"
AMENDMENT_MANIFEST_PATH = (
    PROJECT_ROOT
    / "stage_artifacts/V015_S01_CONTROLLED_TRANSITION_AMENDMENT/machine/s01_controlled_transition_amendment_manifest.json"
)
S01P2_MANIFEST_PATH = (
    PROJECT_ROOT
    / "stage_artifacts/V015_S01_P2_IMPLEMENTATION_SPEC_GAP_INVENTORY/machine/s01_p2_implementation_spec_gap_inventory_manifest.json"
)
S01P2_GAP_PATH = (
    PROJECT_ROOT
    / "stage_artifacts/V015_S01_P2_IMPLEMENTATION_SPEC_GAP_INVENTORY/machine/implementation_gap_matrix_public_safe.csv"
)
S01P2_MIGRATION_PATH = (
    PROJECT_ROOT
    / "stage_artifacts/V015_S01_P2_IMPLEMENTATION_SPEC_GAP_INVENTORY/machine/migration_decision_matrix_public_safe.csv"
)
SOURCE_PACKAGE = Path.home() / "Downloads/KMFA_ChatGPT_Stage3_Codex_TaskPack_Roadmap_v2_0_UIUX_FULL_REBUILD.zip"

SOURCE_PACKAGE_SHA256 = "e822c98bfe21445b4ddf7110ecf81d14c8fa8bd5f2cdeb00fab4a21e72df39f8"
SOURCE_PACKAGE_BYTES = 118652
PHASE_BASE_COMMIT = "74ce24a516f42cd5d8bf91c738166634199d8823"
S01P2_RESULT_COMMIT = "ef6c867dcba65c9e6d1f95adc823ace36ac93102"
RAW_ROOT_RE = re.compile(r"/Users/[^/\s]+/Downloads/KMFA_MetaData")
EMAIL_RE = re.compile(r"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")

EXPECTED_SOURCE_MEMBERS = {
    "taskpack": {
        "prefix": "01_KMFA_Codex_TaskPack",
        "bytes": 29768,
        "sha256": "1d488a7d98e70f8a69b99a6fc39d94d56fa8d78c754a7640e76b5f745fbb31fa",
    },
    "roadmap": {
        "prefix": "02B_KMFA_Codex_Development_Roadmap",
        "bytes": 107222,
        "sha256": "741fdf6a1dd6d04fdaaf916f8cf84ebce07207fbb50d7971736c1c9fc46a5145",
    },
    "requirements": {
        "prefix": "04_KMFA_",
        "bytes": 17281,
        "sha256": "2ff4eb93f83d52e9bd1c482dceb442d40686a9e2cc54ce9277dfee00e106ab41",
    },
    "scope_policy": {
        "prefix": "11_KMFA_",
        "bytes": 1887,
        "sha256": "96c733d0690f462d4c3e3ea852c9b6172c45f54a94506fe67a22066cb10555ad",
    },
    "inheritance": {
        "prefix": "13_KMFA_",
        "bytes": 3721,
        "sha256": "cc61d0daef141311bac67e2dbf54d751a6b8485cfc7c8ce05389538de5770262",
    },
}

EXPECTED_DEPENDENCIES = {
    "s01_controlled_transition_amendment": {
        "ref": "KMFA/stage_artifacts/V015_S01_CONTROLLED_TRANSITION_AMENDMENT/machine/s01_controlled_transition_amendment_manifest.json",
        "bytes": 8668,
        "sha256": "0933d035251b77a3b6811f5fd3d019526672da800d1f917df76edb72168e1965",
        "content_hash": "sha256:e744e9495133307de4aeef7f00a4845ed12783a1fc82e122a9ad0f4b508c583d",
        "result_commit": PHASE_BASE_COMMIT,
    },
    "s01_p2_gap_manifest": {
        "ref": "KMFA/stage_artifacts/V015_S01_P2_IMPLEMENTATION_SPEC_GAP_INVENTORY/machine/s01_p2_implementation_spec_gap_inventory_manifest.json",
        "bytes": 6050,
        "sha256": "2ec1fd24e43b9c6c659dbd363dd888e3ba6991358b3e8d1206a145441b6fd300",
        "content_hash": "sha256:0b73988c6a3580dfb4185a7bd55b79f0e0ca767c916772a8f0d0701ede0e5d86",
        "result_commit": S01P2_RESULT_COMMIT,
    },
    "s01_p2_gap_matrix": {
        "ref": "KMFA/stage_artifacts/V015_S01_P2_IMPLEMENTATION_SPEC_GAP_INVENTORY/machine/implementation_gap_matrix_public_safe.csv",
        "bytes": 14150,
        "sha256": "54b78da6dd0dac5de069e2a044fa4406b7f8f402048108cc354f1e1d7db83000",
        "content_hash": None,
        "result_commit": S01P2_RESULT_COMMIT,
    },
    "s01_p2_migration_matrix": {
        "ref": "KMFA/stage_artifacts/V015_S01_P2_IMPLEMENTATION_SPEC_GAP_INVENTORY/machine/migration_decision_matrix_public_safe.csv",
        "bytes": 9733,
        "sha256": "a08f970fbe1f857003ff8f72e2f3b2d2aef06925d30d2e6ddf2fc3669a2bfe0b",
        "content_hash": None,
        "result_commit": S01P2_RESULT_COMMIT,
    },
}

EXPECTED_ARTIFACT_REFS = {
    "manifest": "KMFA/stage_artifacts/V015_S02_P1_REQUIREMENTS_SCOPE_LOCK/machine/s02_p1_requirements_scope_lock_manifest.json",
    "requirements_ledger": "KMFA/stage_artifacts/V015_S02_P1_REQUIREMENTS_SCOPE_LOCK/machine/requirements_ledger_public_safe.csv",
    "requirements_report": "KMFA/stage_artifacts/V015_S02_P1_REQUIREMENTS_SCOPE_LOCK/human/requirements_ledger_zh.md",
    "business_line_matrix": "KMFA/stage_artifacts/V015_S02_P1_REQUIREMENTS_SCOPE_LOCK/machine/business_line_matrix_public_safe.csv",
    "scope_lock": "KMFA/stage_artifacts/V015_S02_P1_REQUIREMENTS_SCOPE_LOCK/machine/scope_lock_dispositions_public_safe.csv",
    "scope_lock_report": "KMFA/stage_artifacts/V015_S02_P1_REQUIREMENTS_SCOPE_LOCK/human/rebuild_scope_lock_zh.md",
    "completion_record": "KMFA/stage_artifacts/V015_S02_P1_REQUIREMENTS_SCOPE_LOCK/human/completion_record_zh.md",
    "rollback_plan": "KMFA/stage_artifacts/V015_S02_P1_REQUIREMENTS_SCOPE_LOCK/human/rollback_plan_zh.md",
    "test_results": "KMFA/stage_artifacts/V015_S02_P1_REQUIREMENTS_SCOPE_LOCK/human/test_results_zh.md",
    "validation_results": "KMFA/stage_artifacts/V015_S02_P1_REQUIREMENTS_SCOPE_LOCK/machine/validation_results.jsonl",
}
EXPECTED_INTEGRITY_REFS = set(EXPECTED_ARTIFACT_REFS.values()) - {EXPECTED_ARTIFACT_REFS["manifest"]}

EXPECTED_REQUIREMENT_HEADER = [
    "ledger_version",
    "requirement_id",
    "priority",
    "requirement_name",
    "normative_requirement",
    "source_refs",
    "source_member_sha256",
    "primary_stage_refs",
    "task_refs",
    "acceptance_requirement",
    "evidence_requirement",
    "current_implementation_status",
    "implementation_gap_type",
    "severity",
    "gap_impact",
    "current_evidence_refs",
    "migration_disposition",
    "conflict_status",
    "conflict_refs",
    "conflict_disposition",
    "resolution_target_stage",
    "v15_requirement_accepted",
    "implementation_allowed_by_s02_p1",
    "public_safe_status",
]
EXPECTED_BUSINESS_HEADER = [
    "business_line_id",
    "priority",
    "business_line_name",
    "first_manual_work_to_replace",
    "input_classes",
    "output_classes",
    "human_review_boundary",
    "prohibited_automatic_actions",
    "recommended_stage_ids",
    "routing_status",
    "source_refs",
    "product_acceptance_inherited",
    "implementation_allowed_by_s02_p1",
]
EXPECTED_SCOPE_HEADER = [
    "capability_id",
    "capability_name",
    "domain",
    "s01_p2_historical_decision",
    "v15_scope_class",
    "verification_status",
    "source_evidence_refs",
    "scope_rationale",
    "target_stage",
    "preservation_constraint",
    "product_acceptance_inherited",
    "implementation_allowed_by_s02_p1",
]

EXPECTED_BUSINESS_LINES = {
    "BL-01": ("P0", "项目成本分析"),
    "BL-02": ("P1", "财务经营报表"),
    "BL-03": ("P1", "回款与应收账龄"),
    "BL-04": ("P1", "销售绩效事实"),
    "BL-05": ("P1", "资金、现金与贷款"),
    "BL-06": ("P1", "开票、纳税与政策"),
    "BL-07": ("P1", "外协采购成本"),
    "BL-08": ("P1", "项目交付状态"),
    "BL-09": ("P2", "客户经营"),
    "BL-10": ("P2", "财务 SOP"),
}

EXPECTED_TASKS = {
    "S02P1T01": ("建立唯一需求总账", "版本化需求总账。"),
    "S02P1T02": ("登记业务线 1–10", "业务线矩阵。"),
    "S02P1T03": ("锁定当前版本边界", "重构范围锁。"),
}

EXPECTED_RECEIPT_IDS = {
    "s01_amendment_strict_dependency",
    "s01_p2_gap_dependency",
    "roadmap_governance_check",
    "s02_p1_focused_tests",
    "governance_project_check",
    "lean_check",
    "governance_sync_check",
    "no_float_check",
    "no_omission_check",
    "phase_diff_whitespace_check",
}

EXPECTED_TOP_LEVEL_KEYS = {
    "schema_version",
    "project_id",
    "target_release",
    "stage_id",
    "roadmap_phase_id",
    "run_phase_id",
    "task_id",
    "acceptance_id",
    "generated_at",
    "run_mode",
    "work_kind",
    "phase_base_commit",
    "source_package",
    "dependency_evidence",
    "source_scope_policy",
    "phase_scope",
    "task_accounting",
    "tasks",
    "requirement_ledger_accounting",
    "business_line_accounting",
    "scope_lock_accounting",
    "conflict_control",
    "phase_result",
    "stage_state",
    "next_entry_gate",
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


def _read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


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


def _sanitize_public_safe(value: Any) -> str:
    text = "" if value is None else str(value)
    text = RAW_ROOT_RE.sub("RAW_ROOT_TOKEN", text)
    return EMAIL_RE.sub("OWNER_NOTIFICATION_EMAIL_TOKEN", text)


def _parse_offset_datetime(value: Any, label: str, errors: list[str]) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{label}: timestamp missing")
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        errors.append(f"{label}: invalid ISO timestamp")
        return None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        errors.append(f"{label}: timezone offset required")
        return None
    return parsed


def _top_level_yaml_scalar(text: str, key: str) -> str | None:
    match = re.search(rf"^{re.escape(key)}:\s*(.+?)\s*$", text, re.MULTILINE)
    if not match:
        return None
    value = match.group(1).strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


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
    path = path_overrides.get(ref, repo_root / relative)
    try:
        path.resolve().relative_to(repo_root.resolve())
    except ValueError:
        if ref not in path_overrides:
            return None
    if require_exists and not path.exists():
        return None
    return path


def _validate_ref_list(
    refs: str,
    *,
    label: str,
    errors: list[str],
    repo_root: Path,
    path_overrides: dict[str, Path],
) -> None:
    values = [item.strip() for item in str(refs).split(";") if item.strip()]
    _require(bool(values), f"{label}: evidence refs missing", errors)
    _require(len(values) == len(set(values)), f"{label}: duplicate evidence refs", errors)
    for ref in values:
        _require(
            _safe_ref_path(ref, repo_root=repo_root, path_overrides=path_overrides) is not None,
            f"{label}: unsafe or missing evidence ref {ref}",
            errors,
        )


def _source_members(package: Path) -> tuple[dict[str, dict[str, Any]], list[dict[str, str]], dict[str, tuple[str, str]]]:
    with zipfile.ZipFile(package) as archive:
        members: dict[str, dict[str, Any]] = {}
        payloads: dict[str, bytes] = {}
        for label, spec in EXPECTED_SOURCE_MEMBERS.items():
            candidates = [
                name
                for name in archive.namelist()
                if name.rsplit("/", 1)[-1].startswith(str(spec["prefix"]))
            ]
            if len(candidates) != 1:
                raise ValidationError(f"source member count mismatch for {label}: {len(candidates)}")
            name = candidates[0]
            payload = archive.read(name)
            payloads[label] = payload
            members[label] = {
                "member": name,
                "bytes": len(payload),
                "sha256": hashlib.sha256(payload).hexdigest(),
            }
        requirement_text = payloads["requirements"].decode("utf-8-sig")
        reader = csv.DictReader(requirement_text.splitlines())
        requirements = list(reader)
        roadmap = json.loads(payloads["roadmap"].decode("utf-8-sig"))
        s02 = next(stage for stage in roadmap["stages"] if stage["id"] == "S02")
        p1 = next(phase for phase in s02["phases"] if phase["id"] == "P1")
        tasks = {f"S02P1{row['id']}": (row["name"], row["output"]) for row in p1["tasks"]}
        return members, requirements, tasks


def _validate_source_package(
    manifest: dict[str, Any],
    source_package: Path | None,
    require_source_package: bool,
    errors: list[str],
) -> dict[str, dict[str, str]]:
    expected_summary = {
        "name": SOURCE_PACKAGE.name,
        "bytes": SOURCE_PACKAGE_BYTES,
        "sha256": SOURCE_PACKAGE_SHA256,
        "stage_count": 24,
        "phase_count": 72,
        "task_count": 216,
        "requirement_count": 55,
        "priority_counts": {"P0": 46, "P1": 8, "P2": 1},
    }
    source = manifest.get("source_package", {})
    _require({key: source.get(key) for key in expected_summary} == expected_summary, "source package summary mismatch", errors)
    package_available = source_package is not None and source_package.is_file()
    if require_source_package:
        _require(package_available, "source package required but missing", errors)
    if not package_available:
        return {}
    assert source_package is not None
    _require(source_package.stat().st_size == SOURCE_PACKAGE_BYTES, "source package byte count mismatch", errors)
    _require(_sha256(source_package) == SOURCE_PACKAGE_SHA256, "source package SHA-256 mismatch", errors)
    try:
        members, source_rows, source_tasks = _source_members(source_package)
    except (KeyError, StopIteration, UnicodeDecodeError, zipfile.BadZipFile, ValidationError) as error:
        errors.append(str(error))
        return {}
    expected_member_summary = {
        label: {
            "member": row["member"],
            "bytes": EXPECTED_SOURCE_MEMBERS[label]["bytes"],
            "sha256": EXPECTED_SOURCE_MEMBERS[label]["sha256"],
        }
        for label, row in members.items()
    }
    _require(source.get("members") == expected_member_summary, "source member binding mismatch", errors)
    for label, row in members.items():
        _require(row == expected_member_summary[label], f"source member content drift: {label}", errors)
    _require(source_tasks == EXPECTED_TASKS, "source S02-P1 task contract drift", errors)
    by_id = {
        row.get("需求ID", ""): {
            "priority": row.get("优先级", ""),
            "name": row.get("需求名称", ""),
            "text": row.get("需求说明", ""),
            "stages": row.get("主要Stage", ""),
            "tasks": row.get("对应Task", ""),
            "acceptance": row.get("验收要求", ""),
            "evidence": row.get("证据要求", ""),
        }
        for row in source_rows
    }
    _require(set(by_id) == {f"R{index:03d}" for index in range(1, 56)}, "source requirement ID coverage drift", errors)
    return by_id


def _validate_dependencies(
    manifest: dict[str, Any],
    paths: dict[str, Path],
    errors: list[str],
) -> None:
    dependency = manifest.get("dependency_evidence", {})
    _require(dependency.get("count") == 4, "dependency count mismatch", errors)
    rows = dependency.get("dependencies", [])
    by_id = {str(row.get("dependency_id", "")): row for row in rows if isinstance(row, dict)}
    _require(len(rows) == len(by_id) == 4, "dependencies must be four unique rows", errors)
    _require(set(by_id) == set(EXPECTED_DEPENDENCIES), "dependency ID set mismatch", errors)
    for dependency_id, expected in EXPECTED_DEPENDENCIES.items():
        expected_row = {"dependency_id": dependency_id, **expected}
        _require(by_id.get(dependency_id) == expected_row, f"dependency binding mismatch: {dependency_id}", errors)
        path = paths[dependency_id]
        _require(path.is_file(), f"dependency file missing: {dependency_id}", errors)
        if not path.is_file():
            continue
        _require(path.stat().st_size == expected["bytes"], f"dependency byte drift: {dependency_id}", errors)
        _require(_sha256(path) == expected["sha256"], f"dependency SHA drift: {dependency_id}", errors)
        if expected["content_hash"] is not None:
            value = _read_json(path)
            _require(value.get("content_hash") == expected["content_hash"], f"dependency content hash drift: {dependency_id}", errors)
            _require(value.get("content_hash") == _canonical_content_hash(value), f"dependency canonical hash invalid: {dependency_id}", errors)
    if paths["s01_controlled_transition_amendment"].is_file():
        amendment = _read_json(paths["s01_controlled_transition_amendment"])
        _require(
            amendment.get("amendment_result", {}).get("acceptance_status") == "PASSED"
            and amendment.get("amendment_result", {}).get("decision") == "GO_TO_S02_P1_ONLY"
            and amendment.get("next_entry_gate", {}).get("s02_p1_planning_entry_allowed_by_amendment") is True,
            "amendment does not authorize S02-P1 planning",
            errors,
        )
    if paths["s01_p2_gap_manifest"].is_file():
        gap_manifest = _read_json(paths["s01_p2_gap_manifest"])
        _require(gap_manifest.get("requirement_gap_inventory", {}).get("total") == 55, "S01-P2 requirement dependency drift", errors)
        _require(gap_manifest.get("migration_inventory", {}).get("total") == 37, "S01-P2 migration dependency drift", errors)


def _validate_requirements(
    header: list[str],
    rows: list[dict[str, str]],
    source_by_id: dict[str, dict[str, str]],
    gap_rows: list[dict[str, str]],
    manifest: dict[str, Any],
    errors: list[str],
    *,
    repo_root: Path,
    path_overrides: dict[str, Path],
) -> None:
    _require(header == EXPECTED_REQUIREMENT_HEADER, "requirements CSV header mismatch", errors)
    ids = [row.get("requirement_id", "") for row in rows]
    expected_ids = {f"R{index:03d}" for index in range(1, 56)}
    _require(len(rows) == len(set(ids)) == 55, "requirements ledger must contain 55 unique rows", errors)
    _require(set(ids) == expected_ids, "requirements ledger ID coverage mismatch", errors)
    priorities = Counter(row.get("priority", "") for row in rows)
    _require(priorities == {"P0": 46, "P1": 8, "P2": 1}, "requirements priority counts mismatch", errors)
    normalized_names = [re.sub(r"\s+", "", row.get("requirement_name", "")).casefold() for row in rows]
    _require(len(normalized_names) == len(set(normalized_names)), "normalized duplicate requirement name", errors)
    gap_by_id = {row.get("requirement_id", ""): row for row in gap_rows}
    unresolved = 0
    implementation_claims = 0
    for row in rows:
        requirement_id = row.get("requirement_id", "")
        source = source_by_id.get(requirement_id)
        if source:
            _require(row.get("priority") == source["priority"], f"{requirement_id}: source priority drift", errors)
            _require(row.get("requirement_name") == _sanitize_public_safe(source["name"]), f"{requirement_id}: source name drift", errors)
            _require(row.get("normative_requirement") == _sanitize_public_safe(source["text"]), f"{requirement_id}: source text drift", errors)
            _require(row.get("primary_stage_refs") == source["stages"], f"{requirement_id}: source stage drift", errors)
            _require(row.get("task_refs") == source["tasks"], f"{requirement_id}: source task ref drift", errors)
            _require(row.get("acceptance_requirement") == _sanitize_public_safe(source["acceptance"]), f"{requirement_id}: source acceptance requirement drift", errors)
            _require(row.get("evidence_requirement") == _sanitize_public_safe(source["evidence"]), f"{requirement_id}: source evidence requirement drift", errors)
        _require(row.get("ledger_version") == "v1.5-s02-p1-r1", f"{requirement_id}: ledger version drift", errors)
        _require(row.get("source_member_sha256") == EXPECTED_SOURCE_MEMBERS["requirements"]["sha256"], f"{requirement_id}: source member SHA drift", errors)
        _require(bool(row.get("source_refs", "").strip()), f"{requirement_id}: source refs missing", errors)
        _require(bool(row.get("acceptance_requirement", "").strip()), f"{requirement_id}: acceptance requirement missing", errors)
        _require(bool(row.get("evidence_requirement", "").strip()), f"{requirement_id}: evidence requirement missing", errors)
        gap = gap_by_id.get(requirement_id, {})
        _require(row.get("current_implementation_status") == gap.get("current_status"), f"{requirement_id}: current implementation status drift", errors)
        _require(row.get("implementation_gap_type") == gap.get("gap_type"), f"{requirement_id}: implementation gap type drift", errors)
        _require(row.get("severity") == gap.get("severity"), f"{requirement_id}: severity drift", errors)
        _require(row.get("gap_impact") == _sanitize_public_safe(gap.get("impact")), f"{requirement_id}: gap impact drift", errors)
        _require(row.get("current_evidence_refs") == _sanitize_public_safe(gap.get("evidence_refs")), f"{requirement_id}: current evidence drift", errors)
        _require(row.get("migration_disposition") == gap.get("migration_hint"), f"{requirement_id}: migration disposition drift", errors)
        conflict_status = row.get("conflict_status")
        if conflict_status == "UNRESOLVED":
            unresolved += 1
        if requirement_id == "R007":
            _require(conflict_status == "RESOLVED_BY_V15_PRECEDENCE", "R007 normative conflict disposition mismatch", errors)
            _require(bool(row.get("conflict_refs", "").strip()), "R007 conflict refs missing", errors)
            _require("v1.5" in row.get("conflict_disposition", "") or "v2.0" in row.get("conflict_disposition", "") or "V15" in row.get("conflict_disposition", ""), "R007 conflict resolution missing precedence", errors)
            _require(row.get("current_implementation_status") == "CONFLICTING_POLICY", "R007 implementation remediation must remain OPEN", errors)
            _require(row.get("resolution_target_stage") == "S03", "R007 resolution target must remain S03", errors)
        else:
            _require(conflict_status == "NONE", f"{requirement_id}: unexpected normative conflict", errors)
            _require(not row.get("conflict_refs", "").strip(), f"{requirement_id}: unexpected conflict refs", errors)
        if row.get("implementation_allowed_by_s02_p1") != "false":
            implementation_claims += 1
        _require(row.get("v15_requirement_accepted") == "false", f"{requirement_id}: false requirement acceptance claim", errors)
        _require(row.get("public_safe_status") == "PUBLIC_SAFE", f"{requirement_id}: public-safe status drift", errors)
        _validate_ref_list(
            row.get("current_evidence_refs", ""),
            label=requirement_id,
            errors=errors,
            repo_root=repo_root,
            path_overrides=path_overrides,
        )
    expected_accounting = {
        "total": 55,
        "unique": 55,
        "p0": 46,
        "p1": 8,
        "p2": 1,
        "p0_p1_total": 54,
        "p0_p1_unique": 54,
        "duplicate_id_count": 0,
        "normalized_duplicate_count": 0,
        "unresolved_normative_conflict_count": 0,
        "resolved_normative_conflict_count": 1,
        "source_row_match_count": 55,
        "implementation_acceptance_claim_count": 0,
        "delivery_status": "SCOPE_LOCKED_NOT_IMPLEMENTED",
    }
    _require(manifest.get("requirement_ledger_accounting") == expected_accounting, "requirement ledger accounting mismatch", errors)
    _require(unresolved == 0, "unresolved normative conflict remains", errors)
    _require(implementation_claims == 0, "false requirement implementation claim", errors)


def _validate_business_lines(
    header: list[str],
    rows: list[dict[str, str]],
    manifest: dict[str, Any],
    errors: list[str],
    *,
    repo_root: Path,
    path_overrides: dict[str, Path],
) -> None:
    _require(header == EXPECTED_BUSINESS_HEADER, "business-line CSV header mismatch", errors)
    ids = [row.get("business_line_id", "") for row in rows]
    _require(len(rows) == len(set(ids)) == 10, "business-line matrix must contain 10 unique rows", errors)
    _require(set(ids) == set(EXPECTED_BUSINESS_LINES), "business-line ID coverage mismatch", errors)
    for row in rows:
        line_id = row.get("business_line_id", "")
        expected = EXPECTED_BUSINESS_LINES.get(line_id)
        if expected:
            _require((row.get("priority"), row.get("business_line_name")) == expected, f"{line_id}: identity drift", errors)
        for key in (
            "first_manual_work_to_replace",
            "input_classes",
            "output_classes",
            "human_review_boundary",
            "prohibited_automatic_actions",
            "recommended_stage_ids",
        ):
            _require(bool(row.get(key, "").strip()), f"{line_id}: {key} missing", errors)
        _require(row.get("routing_status") == "PROPOSED_FOR_S02_P2_TRACEABILITY", f"{line_id}: routing scope drift", errors)
        _require(row.get("product_acceptance_inherited") == "false", f"{line_id}: product acceptance inherited", errors)
        _require(row.get("implementation_allowed_by_s02_p1") == "false", f"{line_id}: high-risk automation authorized", errors)
        stages = [item for item in re.split(r"[;,]", row.get("recommended_stage_ids", "")) if item]
        _require(all(re.fullmatch(r"S(?:0[2-9]|1[0-9]|2[0-4])", item) for item in stages), f"{line_id}: invalid recommended stage", errors)
        _require(bool(row.get("source_refs", "").strip()), f"{line_id}: source refs missing", errors)
    _require(
        manifest.get("business_line_accounting") == {
            "total": 10,
            "unique": 10,
            "p0": 1,
            "p1": 7,
            "p2": 2,
            "required_input_complete": 10,
            "required_output_complete": 10,
            "human_review_boundary_complete": 10,
            "forbidden_automatic_action_complete": 10,
            "high_risk_automation_authorized_count": 0,
            "out_of_scope_business_line_count": 0,
        },
        "business-line accounting mismatch",
        errors,
    )


def _expected_scope_class(capability_id: str) -> str | None:
    if not re.fullmatch(r"CAP-\d{3}", capability_id):
        return None
    index = int(capability_id.rsplit("-", 1)[1])
    if index <= 12:
        return "KEEP_GOVERNANCE_BASELINE"
    if index <= 24:
        return "REBUILD"
    if index <= 29:
        return "DEPRECATE"
    return "DEFER"


def _validate_scope_lock(
    header: list[str],
    rows: list[dict[str, str]],
    migration_rows: list[dict[str, str]],
    manifest: dict[str, Any],
    errors: list[str],
    *,
    repo_root: Path,
    path_overrides: dict[str, Path],
) -> None:
    _require(header == EXPECTED_SCOPE_HEADER, "scope-lock CSV header mismatch", errors)
    ids = [row.get("capability_id", "") for row in rows]
    expected_ids = {f"CAP-{index:03d}" for index in range(1, 38)}
    _require(len(rows) == len(set(ids)) == 37, "scope lock must contain 37 unique capability rows", errors)
    _require(set(ids) == expected_ids, "scope capability ID coverage mismatch", errors)
    migration_by_id = {row.get("capability_id", ""): row for row in migration_rows}
    for row in rows:
        capability_id = row.get("capability_id", "")
        source = migration_by_id.get(capability_id, {})
        mapping = {
            "capability_name": "capability_name",
            "domain": "domain",
            "s01_p2_historical_decision": "decision",
            "verification_status": "verification_status",
            "source_evidence_refs": "evidence_refs",
            "scope_rationale": "rationale",
            "target_stage": "target_stage",
            "preservation_constraint": "preservation_constraint",
        }
        for current_key, source_key in mapping.items():
            _require(row.get(current_key) == _sanitize_public_safe(source.get(source_key)), f"{capability_id}: S01-P2 evidence drift: {current_key}", errors)
        _require(row.get("v15_scope_class") == _expected_scope_class(capability_id), f"{capability_id}: v1.5 scope class drift", errors)
        _require(row.get("product_acceptance_inherited") == "false", f"{capability_id}: product acceptance inherited", errors)
        _require(row.get("implementation_allowed_by_s02_p1") == "false", f"{capability_id}: implementation authorized", errors)
        _validate_ref_list(
            row.get("source_evidence_refs", ""),
            label=capability_id,
            errors=errors,
            repo_root=repo_root,
            path_overrides=path_overrides,
        )
    _require(
        manifest.get("scope_lock_accounting") == {
            "total": 37,
            "keep_governance_baseline": 12,
            "rebuild": 12,
            "defer": 8,
            "deprecate": 5,
            "product_acceptance_inherited_count": 0,
            "implementation_allowed_count": 0,
            "v15_product_capability_accepted_count": 0,
        },
        "scope-lock accounting mismatch",
        errors,
    )
    _require(
        manifest.get("source_scope_policy") == {
            "normative_keep_and_reverify_count": 15,
            "normative_rebuild_count": 15,
            "normative_deprecate_as_acceptance_baseline_count": 7,
            "evidence_qualified_capability_count": 37,
            "normative_list_counts_used_as_capability_counts": False,
            "deferred_requirement_ids": ["R052", "R053", "R054"],
        },
        "source scope policy accounting mismatch",
        errors,
    )


def _validate_tasks_and_gates(manifest: dict[str, Any], require_final: bool, errors: list[str]) -> None:
    tasks = manifest.get("tasks", [])
    by_id = {str(row.get("task_id", "")): row for row in tasks if isinstance(row, dict)}
    _require(len(tasks) == len(by_id) == 3 and set(by_id) == set(EXPECTED_TASKS), "S02-P1 task set mismatch", errors)
    for task_id, (name, output) in EXPECTED_TASKS.items():
        row = by_id.get(task_id, {})
        _require(set(row) == {"task_id", "name", "output", "execution_status", "acceptance_status", "evidence_refs"}, f"{task_id}: task key set mismatch", errors)
        _require((row.get("name"), row.get("output")) == (name, output), f"{task_id}: task contract drift", errors)
        _require(row.get("execution_status") == "EXECUTION_COMPLETE", f"{task_id}: execution status mismatch", errors)
        _require(row.get("acceptance_status") == "PASSED", f"{task_id}: acceptance status mismatch", errors)
        refs = row.get("evidence_refs", [])
        _require(isinstance(refs, list) and bool(refs) and len(refs) == len(set(map(str, refs))), f"{task_id}: evidence refs invalid", errors)
    _require(manifest.get("task_accounting") == {"total": 3, "execution_complete": 3, "accepted": 3, "not_accepted": 0}, "task accounting mismatch", errors)
    pending_result = {
        "execution_status": "EXECUTION_COMPLETE",
        "evidence_validation_status": "PENDING",
        "final_validation_status": "PENDING",
        "acceptance_status": "PENDING_FINAL_VALIDATION",
        "decision": "PENDING_FINAL_VALIDATION",
    }
    final_result = {
        "execution_status": "EXECUTION_COMPLETE",
        "evidence_validation_status": "PASS",
        "final_validation_status": "PASS",
        "acceptance_status": "PASSED",
        "decision": "CONTINUE_TO_S02_P2_ONLY",
    }
    result = manifest.get("phase_result")
    _require(result in ([final_result] if require_final else [pending_result, final_result]), "phase result cohort mismatch", errors)
    is_final = result == final_result
    _require(
        manifest.get("stage_state") == {
            "stage_id": "S02",
            "stage_lifecycle_status": "IN_PROGRESS",
            "stage_acceptance_status": "PENDING",
            "stage_passed": False,
            "completed_phase_count": 1,
            "total_phase_count": 3,
        },
        "S02 stage state mismatch",
        errors,
    )
    _require(
        manifest.get("next_entry_gate") == {
            "next_allowed_taskpack_phase": "S02-P2",
            "s02_p2_entry_allowed": is_final,
            "s02_p2_started_in_current_run": False,
            "s02_p3_entry_allowed": False,
            "s03_plus_entry_allowed": False,
            "product_implementation_allowed": False,
        },
        "next-entry gate mismatch",
        errors,
    )
    _require(
        manifest.get("phase_scope") == {
            "planning_only": True,
            "requirements_merge": True,
            "business_line_scope_lock": True,
            "v14_to_v15_scope_lock": True,
            "s02_p2_traceability_performed": False,
            "technology_stack_selection_allowed": False,
            "product_implementation_allowed": False,
        },
        "phase scope mismatch",
        errors,
    )
    _require(
        manifest.get("conflict_control") == {
            "total": 1,
            "resolved_normatively": 1,
            "implementation_open": 1,
            "unresolved_normative_conflicts": 0,
            "r007_disposition": "RESOLVED_BY_V15_PRECEDENCE_IMPLEMENTATION_OPEN",
        },
        "conflict control mismatch",
        errors,
    )
    expected_downstream = {
        "s02_p2_started": False,
        "s02_p3_started": False,
        "s03_plus_started": False,
        "technology_stack_selected": False,
        "product_runtime_implementation_performed": False,
        "api_implementation_performed": False,
        "database_implementation_performed": False,
        "ui_implementation_performed": False,
        "raw_business_content_read": False,
        "raw_root_listed_or_inventoried": False,
        "raw_inbox_mutated": False,
        "business_execution_performed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
    }
    _require(manifest.get("downstream_actions") == expected_downstream, "downstream boundary mismatch", errors)


def _validate_artifacts(
    manifest: dict[str, Any],
    errors: list[str],
    *,
    repo_root: Path,
    path_overrides: dict[str, Path],
) -> None:
    _require(manifest.get("artifact_refs") == EXPECTED_ARTIFACT_REFS, "artifact refs must be exact", errors)
    rows = manifest.get("artifact_integrity", [])
    by_ref = {str(row.get("ref", "")): row for row in rows if isinstance(row, dict)}
    _require(len(rows) == len(by_ref) == 9, "artifact integrity must contain nine unique rows", errors)
    _require(set(by_ref) == EXPECTED_INTEGRITY_REFS, "artifact integrity ref set mismatch", errors)
    for ref in EXPECTED_INTEGRITY_REFS:
        path = _safe_ref_path(ref, repo_root=repo_root, path_overrides=path_overrides)
        _require(path is not None, f"artifact ref unsafe or missing: {ref}", errors)
        row = by_ref.get(ref)
        if path is None or row is None:
            continue
        _require(row == {"ref": ref, "bytes": path.stat().st_size, "sha256": _sha256(path)}, f"artifact integrity mismatch: {ref}", errors)


def _validate_receipts(rows: list[dict[str, Any]], require_pass: bool, errors: list[str]) -> None:
    ids = [str(row.get("validation_id", "")) for row in rows]
    _require(len(rows) == len(set(ids)) == 10, "validation receipts must contain ten unique rows", errors)
    _require(set(ids) == EXPECTED_RECEIPT_IDS, "validation receipt ID set mismatch", errors)
    for row in rows:
        receipt_id = str(row.get("validation_id", "unknown"))
        _require(set(row) == {"validation_id", "command", "result", "exit_code"}, f"{receipt_id}: receipt key set mismatch", errors)
        _require(bool(str(row.get("command", "")).strip()), f"{receipt_id}: command missing", errors)
        allowed = {"PASS"} if require_pass else {"PENDING", "PASS"}
        _require(row.get("result") in allowed, f"{receipt_id}: result mismatch", errors)
        if row.get("result") == "PASS":
            _require(row.get("exit_code") == 0, f"{receipt_id}: PASS must have exit_code 0", errors)
        else:
            _require(row.get("exit_code") is None, f"{receipt_id}: PENDING must have null exit_code", errors)


def _validate_governance(project_text: str, roadmap_text: str, agents_text: str, model_spec_text: str, errors: list[str]) -> None:
    _require(_top_level_yaml_scalar(project_text, "target_version") == "v1.5", "project target version drift", errors)
    _require(_top_level_yaml_scalar(roadmap_text, "target_release") == "v1.5", "roadmap target release drift", errors)
    project_phase = _top_level_yaml_scalar(project_text, "current_phase_id")
    roadmap_phase = _top_level_yaml_scalar(roadmap_text, "current_phase_id")
    _require(project_phase == roadmap_phase, "project/roadmap current phase mismatch", errors)
    current_p1 = project_phase == "V015_S02_P1_REQUIREMENTS_SCOPE_LOCK"
    current_stage_review = project_phase == "V015_S02_STAGE_REVIEW"
    successor_match = re.fullmatch(
        r"V015_S(?P<stage>02|0[3-9]|1[0-9]|2[0-4])_P(?P<phase>[123])(?:_[A-Z0-9_]+)?",
        project_phase or "",
    )
    legal_successor = current_stage_review or (
        successor_match is not None
        and not (
            successor_match.group("stage") == "02"
            and successor_match.group("phase") == "1"
        )
    )
    _require(current_p1 or legal_successor, "illegal S02-P1 governance successor phase", errors)

    if current_p1:
        expected_common = {
            "current_stage_id": "S02",
            "current_phase_id": "V015_S02_P1_REQUIREMENTS_SCOPE_LOCK",
            "run_mode": "IMPLEMENT",
            "work_kind": "REQUIREMENTS_SCOPE_LOCK",
            "stage_lifecycle_status": "IN_PROGRESS",
            "stage_acceptance_status": "PENDING",
            "decision": "CONTINUE_TO_S02_P2_ONLY",
            "s02_p1_acceptance_status": "PASSED",
            "s02_p2_entry_allowed": "true",
            "s02_p3_entry_allowed": "false",
            "product_implementation_allowed": "false",
            "next_gate_id": "S02-P2",
        }
        for key, expected in expected_common.items():
            _require(_top_level_yaml_scalar(project_text, key) == expected, f"project governance drift: {key}", errors)
            _require(_top_level_yaml_scalar(roadmap_text, key) == expected, f"roadmap governance drift: {key}", errors)
    elif current_stage_review or successor_match is not None:
        expected_stage = (
            "S02" if current_stage_review else f"S{successor_match.group('stage')}"
        )
        for label, text in (("project", project_text), ("roadmap", roadmap_text)):
            _require(
                _top_level_yaml_scalar(text, "current_stage_id") == expected_stage,
                f"{label} successor stage/phase mismatch",
                errors,
            )
            _require(
                _top_level_yaml_scalar(text, "s02_p1_acceptance_status") == "PASSED",
                f"{label} S02-P1 historical acceptance drift",
                errors,
            )
    for key, expected in (("active_stage_count", "24"), ("active_phase_count", "72"), ("active_task_count", "216")):
        _require(_top_level_yaml_scalar(roadmap_text, key) == expected, f"roadmap count drift: {key}", errors)
    historical = {
        "s01_stage_review_lifecycle_status": "BLOCKED",
        "s01_stage_review_acceptance_status": "NOT_PASSED",
        "s01_stage_review_decision": "NO_GO",
        "s01_stage_review_s02_entry_allowed": "false",
        "s01_controlled_transition_amendment_acceptance_status": "PASSED",
        "s01_controlled_transition_amendment_decision": "GO_TO_S02_P1_ONLY",
    }
    for key, expected in historical.items():
        _require(_top_level_yaml_scalar(project_text, key) == expected, f"project historical fact drift: {key}", errors)
        _require(_top_level_yaml_scalar(roadmap_text, key) == expected, f"roadmap historical fact drift: {key}", errors)
    for token in (
        "V015_S02_P1_REQUIREMENTS_SCOPE_LOCK",
        "不得按单个 Stage 做 GitHub upload gate",
        SOURCE_PACKAGE_SHA256,
    ):
        _require(token in agents_text, f"AGENTS token missing: {token}", errors)
    for token in (
        "FORM-KMFA-V015-S02-P1-REQUIREMENTS-SCOPE-LOCK-001",
        "requirement_count == 55",
        "business_line_count == 10",
        "migration_capability_count == 37",
        "s02_p2_entry_allowed == true",
        "product_implementation_allowed == false",
    ):
        _require(token in model_spec_text, f"MODEL_SPEC token missing: {token}", errors)


def _validate_events(
    rows: list[dict[str, Any]],
    require_final: bool,
    manifest_generated_at: Any,
    errors: list[str],
) -> None:
    relevant = [row for row in rows if row.get("phase_id") == "V015_S02_P1_REQUIREMENTS_SCOPE_LOCK"]
    _require(len(relevant) in {1, 2}, "canonical S02-P1 event count mismatch", errors)
    common = {
        "project_id": "KMFA",
        "target_release": "v1.5",
        "stage_id": "S02",
        "phase_id": "V015_S02_P1_REQUIREMENTS_SCOPE_LOCK",
        "roadmap_phase_id": "S02-P1",
        "task_id": "KMFA-V015-S02-P1-REQUIREMENTS-SCOPE-LOCK-20260713",
        "acceptance_id": "ACC-KMFA-V015-S02-P1-REQUIREMENTS-SCOPE-LOCK",
        "run_mode": "IMPLEMENT",
        "work_kind": "REQUIREMENTS_SCOPE_LOCK",
        "stage_lifecycle_status": "IN_PROGRESS",
        "stage_acceptance_status": "PENDING",
        "s02_stage_passed": False,
        "s02_p2_started": False,
        "s02_p3_started": False,
        "product_implementation_allowed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "raw_business_content_read": False,
        "raw_inbox_mutated": False,
        "business_execution_performed": False,
        "next_taskpack_phase": "S02-P2",
    }
    execution_expected = {
        **common,
        "event_id": "EVENT-KMFA-20260713-V015-S02-P1-REQUIREMENTS-SCOPE-LOCK-EXECUTION",
        "event_type": "phase_execution",
        "phase_acceptance_status": "PENDING_FINAL_VALIDATION",
        "final_validation_status": "PENDING",
        "decision": "PENDING_FINAL_VALIDATION",
        "s02_p2_entry_allowed": False,
    }
    execution = relevant[0] if relevant else {}
    _require({key: execution.get(key) for key in execution_expected} == execution_expected, "S02-P1 execution event cohort drift", errors)
    execution_time = _parse_offset_datetime(execution.get("event_time"), "S02-P1 execution event", errors)
    generated_time = _parse_offset_datetime(manifest_generated_at, "S02-P1 manifest generated_at", errors)
    if len(relevant) == 2:
        final_expected = {
            **common,
            "event_id": "EVENT-KMFA-20260713-V015-S02-P1-REQUIREMENTS-SCOPE-LOCK-FINAL-VALIDATION",
            "event_type": "final_validation",
            "phase_acceptance_status": "PASSED",
            "final_validation_status": "PASS",
            "decision": "CONTINUE_TO_S02_P2_ONLY",
            "s02_p2_entry_allowed": True,
        }
        _require({key: relevant[1].get(key) for key in final_expected} == final_expected, "S02-P1 final event cohort drift", errors)
        final_time = _parse_offset_datetime(relevant[1].get("event_time"), "S02-P1 final event", errors)
        if execution_time is not None and final_time is not None:
            _require(execution_time < final_time, "S02-P1 execution event must precede final event", errors)
        if generated_time is not None and final_time is not None:
            _require(generated_time == final_time, "final manifest generated_at must equal final event_time", errors)
    elif execution_time is not None and generated_time is not None:
        _require(generated_time >= execution_time, "pending manifest generated_at precedes execution event", errors)
    if require_final:
        _require(len(relevant) == 2, "canonical final S02-P1 event missing", errors)


def _run_dependency_validators(require_clean: bool, errors: list[str]) -> None:
    amendment = [
        sys.executable,
        "-B",
        "KMFA/tools/check_v015_s01_controlled_transition_amendment.py",
        "--require-source-package",
        "--require-validation-receipts",
        "--require-dependency-validator",
    ]
    if require_clean:
        amendment.append("--require-clean-worktree")
    commands = [
        amendment,
        [
            sys.executable,
            "-B",
            "KMFA/tools/check_v015_s01_p2_implementation_spec_gap_inventory.py",
            "--require-source-package",
        ],
    ]
    for command in commands:
        result = subprocess.run(command, cwd=REPO_ROOT, capture_output=True, text=True, check=False)
        _require(result.returncode == 0, f"dependency validator failed: {' '.join(command)}\n{result.stdout}{result.stderr}", errors)


def _run_roadmap_sync(errors: list[str]) -> None:
    result = subprocess.run(
        [sys.executable, "-B", "KMFA/tools/v015_roadmap_governance_sync.py", "--check"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    _require(result.returncode == 0, f"Roadmap sync validator failed: {result.stdout}{result.stderr}", errors)


def _validate_clean_result(*, repo_root: Path, manifest_path: Path, errors: list[str]) -> None:
    status = subprocess.run(["git", "status", "--short"], cwd=repo_root, capture_output=True, text=True, check=False)
    _require(status.returncode == 0 and not status.stdout.strip(), "Git worktree must be clean", errors)
    try:
        relative = manifest_path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        relative = manifest_path.name
    result = subprocess.run(["git", "log", "-1", "--format=%H", "--", relative], cwd=repo_root, capture_output=True, text=True, check=False)
    result_commit = result.stdout.strip()
    valid_commit = bool(re.fullmatch(r"[0-9a-f]{40}", result_commit))
    _require(result.returncode == 0 and valid_commit, "committed S02-P1 result not found", errors)
    if not valid_commit:
        return
    _require(result_commit != PHASE_BASE_COMMIT, "S02-P1 result commit must differ from base", errors)
    base = subprocess.run(["git", "merge-base", "--is-ancestor", PHASE_BASE_COMMIT, result_commit], cwd=repo_root, check=False)
    _require(base.returncode == 0, "S02-P1 base is not an ancestor of result", errors)
    head = subprocess.run(["git", "merge-base", "--is-ancestor", result_commit, "HEAD"], cwd=repo_root, check=False)
    _require(head.returncode == 0, "S02-P1 result is not an ancestor of HEAD", errors)
    committed = subprocess.run(["git", "show", f"{result_commit}:{relative}"], cwd=repo_root, capture_output=True, check=False)
    _require(committed.returncode == 0 and committed.stdout == manifest_path.read_bytes(), "committed S02-P1 manifest differs from worktree", errors)


def validate_v015_s02_p1_requirements_scope_lock(
    manifest_path: Path = MANIFEST_PATH,
    *,
    requirements_path: Path = REQUIREMENTS_PATH,
    business_lines_path: Path = BUSINESS_LINES_PATH,
    scope_lock_path: Path = SCOPE_LOCK_PATH,
    validation_results_path: Path = VALIDATION_RESULTS_PATH,
    amendment_manifest_path: Path = AMENDMENT_MANIFEST_PATH,
    s01p2_manifest_path: Path = S01P2_MANIFEST_PATH,
    s01p2_gap_path: Path = S01P2_GAP_PATH,
    s01p2_migration_path: Path = S01P2_MIGRATION_PATH,
    project_governance_path: Path = PROJECT_GOVERNANCE_PATH,
    roadmap_governance_path: Path = ROADMAP_GOVERNANCE_PATH,
    agents_path: Path = AGENTS_PATH,
    events_path: Path = EVENTS_PATH,
    model_spec_path: Path = MODEL_SPEC_PATH,
    artifact_path_overrides: dict[str, Path] | None = None,
    source_package: Path | None = SOURCE_PACKAGE,
    require_source_package: bool = False,
    require_validation_receipts: bool = False,
    require_dependency_validators: bool = False,
    require_roadmap_sync: bool = False,
    require_clean_worktree: bool = False,
    repo_root: Path = REPO_ROOT,
) -> dict[str, Any]:
    errors: list[str] = []
    path_overrides = dict(artifact_path_overrides or {})
    manifest = _read_json(manifest_path)
    requirement_header, requirements = _read_csv(requirements_path)
    business_header, business_lines = _read_csv(business_lines_path)
    scope_header, scope_rows = _read_csv(scope_lock_path)
    _, gap_rows = _read_csv(s01p2_gap_path)
    _, migration_rows = _read_csv(s01p2_migration_path)
    receipts = _read_jsonl(validation_results_path)
    events = _read_jsonl(events_path)

    _require(set(manifest) == EXPECTED_TOP_LEVEL_KEYS, "manifest top-level key set mismatch", errors)
    identity = {
        "schema_version": "kmfa.v015.s02_p1_requirements_scope_lock.v1",
        "project_id": "KMFA",
        "target_release": "v1.5",
        "stage_id": "S02",
        "roadmap_phase_id": "S02-P1",
        "run_phase_id": "V015_S02_P1_REQUIREMENTS_SCOPE_LOCK",
        "task_id": "KMFA-V015-S02-P1-REQUIREMENTS-SCOPE-LOCK-20260713",
        "acceptance_id": "ACC-KMFA-V015-S02-P1-REQUIREMENTS-SCOPE-LOCK",
        "run_mode": "IMPLEMENT",
        "work_kind": "REQUIREMENTS_SCOPE_LOCK",
        "phase_base_commit": PHASE_BASE_COMMIT,
    }
    for key, expected in identity.items():
        _require(manifest.get(key) == expected, f"manifest identity mismatch: {key}", errors)
    _require(bool(str(manifest.get("generated_at", "")).strip()), "manifest generated_at missing", errors)
    _require(manifest.get("content_hash") == _canonical_content_hash(manifest), "manifest content hash mismatch", errors)

    source_by_id = _validate_source_package(manifest, source_package, require_source_package, errors)
    dependency_paths = {
        "s01_controlled_transition_amendment": amendment_manifest_path,
        "s01_p2_gap_manifest": s01p2_manifest_path,
        "s01_p2_gap_matrix": s01p2_gap_path,
        "s01_p2_migration_matrix": s01p2_migration_path,
    }
    _validate_dependencies(manifest, dependency_paths, errors)
    _validate_requirements(
        requirement_header,
        requirements,
        source_by_id,
        gap_rows,
        manifest,
        errors,
        repo_root=repo_root,
        path_overrides=path_overrides,
    )
    _validate_business_lines(
        business_header,
        business_lines,
        manifest,
        errors,
        repo_root=repo_root,
        path_overrides=path_overrides,
    )
    _validate_scope_lock(
        scope_header,
        scope_rows,
        migration_rows,
        manifest,
        errors,
        repo_root=repo_root,
        path_overrides=path_overrides,
    )
    _validate_tasks_and_gates(manifest, require_validation_receipts, errors)
    _validate_artifacts(manifest, errors, repo_root=repo_root, path_overrides=path_overrides)
    _validate_receipts(receipts, require_validation_receipts, errors)
    _validate_governance(
        project_governance_path.read_text(encoding="utf-8"),
        roadmap_governance_path.read_text(encoding="utf-8"),
        agents_path.read_text(encoding="utf-8"),
        model_spec_path.read_text(encoding="utf-8"),
        errors,
    )
    _validate_events(events, require_validation_receipts, manifest.get("generated_at"), errors)
    if require_dependency_validators:
        _run_dependency_validators(require_clean_worktree, errors)
    if require_roadmap_sync:
        _run_roadmap_sync(errors)
    if require_clean_worktree:
        _validate_clean_result(repo_root=repo_root, manifest_path=manifest_path, errors=errors)
    if errors:
        raise ValidationError("\n".join(errors))
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    parser.add_argument("--requirements", type=Path, default=REQUIREMENTS_PATH)
    parser.add_argument("--business-lines", type=Path, default=BUSINESS_LINES_PATH)
    parser.add_argument("--scope-lock", type=Path, default=SCOPE_LOCK_PATH)
    parser.add_argument("--validation-results", type=Path, default=VALIDATION_RESULTS_PATH)
    parser.add_argument("--require-source-package", action="store_true")
    parser.add_argument("--require-validation-receipts", action="store_true")
    parser.add_argument("--require-dependency-validators", action="store_true")
    parser.add_argument("--require-roadmap-sync", action="store_true")
    parser.add_argument("--require-clean-worktree", action="store_true")
    args = parser.parse_args()
    try:
        result = validate_v015_s02_p1_requirements_scope_lock(
            args.manifest,
            requirements_path=args.requirements,
            business_lines_path=args.business_lines,
            scope_lock_path=args.scope_lock,
            validation_results_path=args.validation_results,
            require_source_package=args.require_source_package,
            require_validation_receipts=args.require_validation_receipts,
            require_dependency_validators=args.require_dependency_validators,
            require_roadmap_sync=args.require_roadmap_sync,
            require_clean_worktree=args.require_clean_worktree,
        )
    except (OSError, ValueError, KeyError, json.JSONDecodeError, zipfile.BadZipFile, ValidationError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    print(
        "PASS: KMFA v1.5 S02-P1 requirements scope lock validated; "
        f"phase={result['phase_result']['acceptance_status']}; "
        "S02=IN_PROGRESS/PENDING; next=S02-P2 only"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
