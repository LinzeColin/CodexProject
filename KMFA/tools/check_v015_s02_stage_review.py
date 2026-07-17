#!/usr/bin/env python3
"""Strict fail-closed validator for the KMFA v1.5 S02 Stage review."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Mapping, Optional, Sequence
from zipfile import BadZipFile, ZipFile

from KMFA.tools import build_v015_s02_stage_review as builder


REPO_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = REPO_ROOT / "KMFA"
ARTIFACT_ROOT = PROJECT_ROOT / builder.OUTPUT_ROOT_RELATIVE
MANIFEST_PATH = ARTIFACT_ROOT / builder.MANIFEST_RELATIVE
MATRIX_PATH = ARTIFACT_ROOT / builder.MATRIX_RELATIVE
FINDINGS_PATH = ARTIFACT_ROOT / builder.FINDINGS_RELATIVE
CONTRACTS_PATH = ARTIFACT_ROOT / builder.CONTRACTS_RELATIVE
RISKS_PATH = ARTIFACT_ROOT / builder.RISKS_RELATIVE
TASK_EVIDENCE_PATH = ARTIFACT_ROOT / builder.TASK_EVIDENCE_RELATIVE
VALIDATION_RESULTS_PATH = ARTIFACT_ROOT / builder.VALIDATION_RESULTS_RELATIVE
ROADMAP_SOURCE_PATH = PROJECT_ROOT / "taskpack/v1_5/roadmap_v2_0.json"
SOURCE_MANIFEST_PATH = PROJECT_ROOT / "taskpack/v1_5/source_manifest.json"
PROJECT_GOVERNANCE_PATH = PROJECT_ROOT / "docs/governance/project.yaml"
ROADMAP_GOVERNANCE_PATH = PROJECT_ROOT / "docs/governance/roadmap.yaml"
EVENTS_PATH = PROJECT_ROOT / "docs/governance/events.jsonl"
DEVELOPMENT_EVENTS_PATH = PROJECT_ROOT / "docs/governance/development_events.jsonl"
README_PATH = PROJECT_ROOT / "README.md"
METADATA_PROJECT_PATH = PROJECT_ROOT / "metadata/project/project.yaml"
METADATA_STAGE_STATUS_PATH = PROJECT_ROOT / "metadata/stage_status.jsonl"
METADATA_MODEL_REGISTRY_PATH = PROJECT_ROOT / "metadata/model_registry.yaml"
S01_REVIEW_PATH = REPO_ROOT / builder.S01_REVIEW_REF

PHASE_MANIFESTS = {
    phase_id: REPO_ROOT / values["manifest_ref"]
    for phase_id, values in builder.PHASES.items()
}
PHASE_VALIDATORS = {
    "S02-P1": [
        sys.executable, "-B", "KMFA/tools/check_v015_s02_p1_requirements_scope_lock.py",
        "--require-source-package", "--require-validation-receipts", "--require-roadmap-sync",
    ],
    "S02-P2": [sys.executable, "-B", "KMFA/tools/check_v015_s02_p2_end_to_end_traceability.py"],
    "S02-P3": [sys.executable, "-B", "KMFA/tools/check_v015_s02_p3_scope_gate.py"],
}

EXPECTED_STAGE_GATE = {
    "review_execution_status": "COMPLETED",
    "evidence_validation_status": "PASS",
    "stage_lifecycle_status": "COMPLETED",
    "stage_acceptance_status": "PASSED",
    "decision": "GO_TO_S03_P1_ONLY",
    "s03_p1_entry_allowed": True,
}
FALSE_DOWNSTREAM_KEYS = {
    "s03_started", "s03_p1_started", "s03_plus_started",
    "product_implementation_allowed", "product_runtime_implementation_performed",
    "api_implementation_performed", "database_implementation_performed",
    "ui_implementation_performed", "github_upload_performed",
    "app_reinstall_performed", "raw_business_content_read",
    "raw_root_listed_or_inventoried", "raw_inbox_mutated",
    "business_execution_performed", "formal_report_generated",
}
FORBIDDEN_PUBLIC_TOKENS = (
    b"/" + b"Users/", b"/" + b"Volumes/", b"/" + b"private/",
    b"/" + b"tmp/", b"/" + b"home/",
    b"KMFA_" + b"MetaData", b"OWNER_NOTIFICATION_EMAIL_" + b"TOKEN@",
)
EMAIL_RE = re.compile(rb"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
SECRET_RE = re.compile(rb"(?i)(?:api[_-]?key|password|secret|token)\s*[:=]\s*['\"][^'\"]{8,}")


class ValidationError(RuntimeError):
    """Raised when any S02 Stage-review invariant fails."""


def _require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValidationError(f"expected JSON object: {path}")
    return value


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


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical_content_hash(value: Mapping[str, Any]) -> str:
    return builder._content_hash(value)


def _safe_ref(ref: Any, *, require_exists: bool = True) -> bool:
    if not isinstance(ref, str) or not ref.strip():
        return False
    relative = Path(ref)
    if relative.is_absolute() or ".." in relative.parts or not relative.parts or relative.parts[0] != "KMFA":
        return False
    path = (REPO_ROOT / relative).resolve()
    try:
        path.relative_to(REPO_ROOT.resolve())
    except ValueError:
        return False
    return not require_exists or path.exists()


def _source_task_contracts(roadmap: Mapping[str, Any]) -> dict[str, dict[str, str]]:
    contracts: dict[str, dict[str, str]] = {}
    for stage in roadmap.get("stages", []):
        if not isinstance(stage, dict) or stage.get("id") != "S02":
            continue
        for phase in stage.get("phases", []):
            if not isinstance(phase, dict):
                continue
            phase_id = str(phase.get("id", ""))
            for task in phase.get("tasks", []):
                if not isinstance(task, dict):
                    continue
                task_id = "S02" + phase_id + str(task.get("id", ""))
                contracts[task_id] = {
                    key: str(task.get(key, ""))
                    for key in ("name", "action", "output", "acceptance", "evidence", "stop")
                }
    return contracts


def _validate_source_package(source_package: Path, source_binding: Any, errors: list[str]) -> None:
    _require(source_package.is_file(), "source package missing", errors)
    if not source_package.is_file():
        return
    _require(source_package.stat().st_size == 118652, "source package byte count drift", errors)
    _require(_sha256(source_package) == builder.SOURCE_PACKAGE_SHA256, "source package SHA-256 drift", errors)
    try:
        with ZipFile(source_package) as archive:
            names = [item.filename for item in archive.infolist() if not item.is_dir()]
            manifests = [
                name for name in names
                if name.rsplit("/", 1)[-1].startswith("15_MANIFEST_SHA256_") and name.endswith(".csv")
            ]
            _require(len(manifests) == 1, "source SHA manifest member count drift", errors)
            if len(manifests) != 1:
                return
            manifest_payload = archive.read(manifests[0])
            _require(hashlib.sha256(manifest_payload).hexdigest() == builder.SOURCE_MANIFEST_SHA256, "source SHA manifest hash drift", errors)
            reader = csv.DictReader(io.StringIO(manifest_payload.decode("utf-8-sig"), newline=""))
            rows = [dict(row) for row in reader]
            _require(reader.fieldnames == ["相对路径", "字节数", "SHA256"], "source SHA manifest header drift", errors)
            _require(len(rows) == 21, "source SHA manifest must declare 21 members", errors)
            declared: set[str] = set()
            verified = 0
            for row in rows:
                relative = str(row.get("相对路径", ""))
                pure = PurePosixPath(relative)
                _require(bool(relative) and not pure.is_absolute() and ".." not in pure.parts, f"unsafe source member path: {relative}", errors)
                _require(relative not in declared, f"duplicate source member path: {relative}", errors)
                declared.add(relative)
                candidates = [name for name in names if name == relative or name.endswith("/" + relative)]
                _require(len(candidates) == 1, f"source member resolution drift: {relative}", errors)
                if len(candidates) != 1:
                    continue
                payload = archive.read(candidates[0])
                try:
                    size_ok = len(payload) == int(str(row.get("字节数", "")))
                except ValueError:
                    size_ok = False
                hash_ok = hashlib.sha256(payload).hexdigest() == str(row.get("SHA256", "")).lower()
                _require(size_ok, f"source member byte drift: {relative}", errors)
                _require(hash_ok, f"source member SHA drift: {relative}", errors)
                verified += int(size_ok and hash_ok)
            _require(verified == 21, "source package 21/21 integrity not verified", errors)
    except BadZipFile as error:
        errors.append(f"source package invalid ZIP: {error}")
        return
    if isinstance(source_binding, Mapping):
        _require(source_binding.get("sha256") == builder.SOURCE_PACKAGE_SHA256, "manifest source binding SHA drift", errors)
        declared = source_binding.get("sha_manifest_declared_member_count", source_binding.get("declared_member_count", source_binding.get("manifest_member_count")))
        verified = source_binding.get("sha_manifest_verified_member_count", source_binding.get("verified_member_count"))
        mismatch = source_binding.get("sha_manifest_mismatch_count", source_binding.get("mismatch_count", source_binding.get("unmanifested_member_count")))
        _require(declared == 21, "manifest source 21-member binding drift", errors)
        _require(verified == 21, "manifest source 21/21 result drift", errors)
        _require(mismatch == 0, "manifest source mismatch count drift", errors)
    else:
        errors.append("manifest source_package binding missing")


def _validate_phase_evidence(manifest: Mapping[str, Any], errors: list[str]) -> dict[str, dict[str, Any]]:
    rows = manifest.get("phase_evidence", [])
    by_phase = {
        str(row.get("phase_id", row.get("roadmap_phase_id", ""))): row
        for row in rows if isinstance(row, dict)
    } if isinstance(rows, list) else {}
    _require(isinstance(rows, list) and len(rows) == len(by_phase) == 3, "phase_evidence must contain three unique phases", errors)
    _require(set(by_phase) == set(PHASE_MANIFESTS), "phase_evidence ID set mismatch", errors)
    for phase_id, path in PHASE_MANIFESTS.items():
        item = by_phase.get(phase_id, {})
        expected_ref = builder.PHASES[phase_id]["manifest_ref"]
        _require(item.get("manifest_ref") == expected_ref, f"{phase_id}: manifest ref drift", errors)
        _require(path.is_file(), f"{phase_id}: live manifest missing", errors)
        if not path.is_file():
            continue
        live = _read_json(path)
        _require(live.get("content_hash") == _canonical_content_hash(live), f"{phase_id}: live content hash invalid", errors)
        _require(item.get("manifest_content_hash") == live.get("content_hash"), f"{phase_id}: content hash binding drift", errors)
        _require(item.get("manifest_sha256") == _sha256(path), f"{phase_id}: SHA-256 binding drift", errors)
        _require(item.get("manifest_bytes") == path.stat().st_size, f"{phase_id}: byte binding drift", errors)
        _require(live.get("phase_result", {}).get("acceptance_status") == "PASSED", f"{phase_id}: phase not PASSED", errors)
        _require(live.get("task_accounting") == {"total": 3, "execution_complete": 3, "accepted": 3, "not_accepted": 0}, f"{phase_id}: 3/3 task acceptance drift", errors)
    return by_phase


def _validate_cross_phase_live_truth(manifest: Mapping[str, Any], errors: list[str]) -> None:
    p1 = _read_json(PHASE_MANIFESTS["S02-P1"])
    p2 = _read_json(PHASE_MANIFESTS["S02-P2"])
    p3 = _read_json(PHASE_MANIFESTS["S02-P3"])
    _require((p1.get("requirement_ledger_accounting", {}).get("total"), p1.get("business_line_accounting", {}).get("total"), p1.get("scope_lock_accounting", {}).get("total")) == (55, 10, 37), "P1 55/10/37 accounting drift", errors)
    _require(p2.get("trace_accounting", {}).get("requirement_count") == 55, "P2 requirement join drift", errors)
    _require(p2.get("trace_accounting", {}).get("normalized_binding_count") == 134, "P2 134 binding join drift", errors)
    lineage = p2.get("lineage_accounting", {})
    formula = p2.get("formula_accounting", {})
    _require(lineage.get("actual_lineage_record_count") == 0 and lineage.get("lineage_full_check_complete") is False and lineage.get("formal_report_allowed") is False, "P2 actual-lineage/formal-report truth drift", errors)
    _require(formula.get("runtime_enabled_count") == 0 and formula.get("product_implementation_claim_count") == 0, "P2 runtime/product truth drift", errors)
    _require((p3.get("scope_accounting", {}).get("scope_row_count"), p3.get("prohibition_accounting", {}).get("prohibition_row_count")) == (103, 51), "P3 103/51 join drift", errors)
    change = p3.get("change_control_accounting", {})
    _require(change.get("runtime_or_ci_hook_implemented") is False, "P3 runtime/CI truth drift", errors)
    _require(change.get("unapproved_change_merge_allowed") is False and change.get("unregistered_change_merge_allowed") is False and change.get("unvalidated_change_merge_allowed") is False, "P3 fail-closed merge truth drift", errors)
    summary = manifest.get("cross_phase_accounting", manifest.get("cross_phase_summary", {}))
    if isinstance(summary, Mapping):
        encoded = json.dumps(summary, ensure_ascii=False, sort_keys=True)
        for token in ("55", "10", "37", "134", "103", "51"):
            _require(token in encoded, f"manifest cross-phase summary missing {token}", errors)


def _validate_matrix(
    matrix: Mapping[str, Any],
    roadmap: Mapping[str, Any],
    errors: list[str],
) -> None:
    _require(matrix.get("schema_version") == "kmfa.v015.s02_stage_review_matrix.v1", "matrix schema drift", errors)
    _require((matrix.get("project_id"), matrix.get("target_release"), matrix.get("stage_id")) == ("KMFA", "v1.5", "S02"), "matrix identity drift", errors)
    _require(matrix.get("run_phase_id") == builder.RUN_PHASE_ID and matrix.get("review_base_commit") == builder.REVIEW_BASE_COMMIT, "matrix run/base drift", errors)
    _require(matrix.get("counted_as_taskpack_task") is False and matrix.get("current_phase_kind") == "GOVERNANCE_OVERLAY", "review must remain governance overlay, not P4/tenth Task", errors)
    expected_contracts = _source_task_contracts(roadmap)
    rows = matrix.get("tasks", [])
    by_id = {str(row.get("task_id", "")): row for row in rows if isinstance(row, dict)} if isinstance(rows, list) else {}
    _require(isinstance(rows, list) and len(rows) == len(by_id) == 9, "matrix must contain nine unique Tasks", errors)
    _require(set(by_id) == set(expected_contracts), "matrix Task ID set drift", errors)
    for task_id, source in expected_contracts.items():
        row = by_id.get(task_id, {})
        _require(row.get("phase_id") == "S02-" + task_id[3:5], f"{task_id}: phase ID drift", errors)
        _require(row.get("name") == source["name"], f"{task_id}: source name drift", errors)
        _require(row.get("source_contract") == {key: source[key] for key in ("action", "output", "acceptance", "evidence", "stop")}, f"{task_id}: exact source contract drift", errors)
        observed = row.get("observed", {})
        _require(isinstance(observed, Mapping), f"{task_id}: observed block missing", errors)
        if isinstance(observed, Mapping):
            _require(observed.get("execution_status") == "EXECUTION_COMPLETE" and observed.get("acceptance_status") == "PASSED", f"{task_id}: not execution-complete/PASSED", errors)
            refs = observed.get("evidence_refs", [])
            _require(isinstance(refs, list) and bool(refs) and len(refs) == len(set(map(str, refs))), f"{task_id}: evidence refs missing/duplicate", errors)
            if isinstance(refs, list):
                for ref in refs:
                    _require(_safe_ref(ref), f"{task_id}: unsafe or missing evidence ref {ref}", errors)
            _require(observed.get("phase_manifest_ref") == builder.PHASES[row.get("phase_id", "S02-P1")]["manifest_ref"] if row.get("phase_id") in builder.PHASES else False, f"{task_id}: phase manifest binding drift", errors)
        _require(row.get("evidence_pack_ref") == builder.FINAL_ARTIFACT_REFS["task_evidence_contract"], f"{task_id}: evidence pack binding drift", errors)
    accounting = matrix.get("task_accounting", {})
    _require(accounting.get("total") == 9 and accounting.get("accepted") == 9 and accounting.get("not_accepted") == 0, "matrix 9/9 accounting drift", errors)
    phase_rows = matrix.get("phase_summaries", [])
    phase_by_id = {str(row.get("phase_id", "")): row for row in phase_rows if isinstance(row, dict)} if isinstance(phase_rows, list) else {}
    _require(isinstance(phase_rows, list) and len(phase_rows) == len(phase_by_id) == 3 and set(phase_by_id) == set(builder.PHASES), "matrix phase summary drift", errors)
    for phase_id, row in phase_by_id.items():
        _require(row.get("execution_status") == "EXECUTION_COMPLETE" and row.get("acceptance_status") == "PASSED", f"{phase_id}: phase summary not PASSED", errors)
        _require(row.get("accepted_tasks") == 3 and row.get("total_tasks") == 3, f"{phase_id}: phase task summary drift", errors)
    _validate_stage_boundary(matrix, errors, label="matrix")


def _validate_task_evidence(task_evidence: Mapping[str, Any], roadmap: Mapping[str, Any], errors: list[str]) -> None:
    _require(task_evidence.get("schema_version") == "kmfa.v015.s02_task_evidence_contract.v1", "task-evidence schema drift", errors)
    required_slots = task_evidence.get("source_required_slots", [])
    _require(isinstance(required_slots, list) and bool(required_slots) and len(required_slots) == len(set(map(str, required_slots))), "source evidence-slot definition missing/duplicate", errors)
    rows = task_evidence.get("tasks", [])
    by_id = {str(row.get("task_id", "")): row for row in rows if isinstance(row, dict)} if isinstance(rows, list) else {}
    expected = _source_task_contracts(roadmap)
    _require(task_evidence.get("task_count") == 9 and isinstance(rows, list) and len(rows) == len(by_id) == 9 and set(by_id) == set(expected), "task-evidence must cover exact nine Tasks", errors)
    for task_id, row in by_id.items():
        _require(row.get("physical_task_directory_materialized") is False, f"{task_id}: duplicate physical evidence pack unexpectedly materialized", errors)
        slots = row.get("slots", [])
        slot_by_id = {str(slot.get("slot", "")): slot for slot in slots if isinstance(slot, dict)} if isinstance(slots, list) else {}
        _require(isinstance(slots, list) and len(slots) == len(slot_by_id) == len(required_slots) and set(slot_by_id) == set(required_slots), f"{task_id}: §5 evidence-slot coverage drift", errors)
        for slot_name, slot in slot_by_id.items():
            status = slot.get("status")
            indexed_statuses = {"INDEXED_EXISTING_EVIDENCE", "INDEXED_BY_PHASE_MANIFEST", "INDEXED_BY_STAGE_REVIEW"}
            _require(status in indexed_statuses | {"NOT_APPLICABLE_WITH_REASON"}, f"{task_id}/{slot_name}: invalid slot status", errors)
            refs = slot.get("evidence_refs", [])
            reason = str(slot.get("not_applicable_reason", "")).strip()
            if status in indexed_statuses:
                _require(isinstance(refs, list) and bool(refs), f"{task_id}/{slot_name}: evidence missing", errors)
                if isinstance(refs, list):
                    for ref in refs:
                        _require(_safe_ref(ref), f"{task_id}/{slot_name}: unsafe/missing evidence {ref}", errors)
            else:
                _require(bool(reason), f"{task_id}/{slot_name}: N/A rationale missing", errors)
                _require(not refs, f"{task_id}/{slot_name}: N/A slot must not claim evidence", errors)
    accounting = task_evidence.get("accounting", {})
    _require(accounting.get("task_count") == 9, "task-evidence accounting drift", errors)


def _validate_findings_and_risks(
    manifest: Mapping[str, Any],
    matrix: Mapping[str, Any],
    findings: list[dict[str, str]],
    risks: list[dict[str, str]],
    errors: list[str],
) -> None:
    finding_ids = [row.get("finding_id", "") for row in findings]
    _require(bool(findings) and len(finding_ids) == len(set(finding_ids)), "findings must be nonempty and uniquely identified", errors)
    blocking = 0
    open_p0_p1 = 0
    for row in findings:
        finding_id = row.get("finding_id", "")
        _require(set(row) == set(builder.FINDING_COLUMNS), f"{finding_id}: finding columns drift", errors)
        _require(row.get("severity") in {"P0", "P1", "P2"}, f"{finding_id}: severity drift", errors)
        _require(row.get("status") in {"FIXED_VALIDATED", "ROUTED_RESIDUAL", "ACCEPTED_RESIDUAL"}, f"{finding_id}: unresolved/unknown status", errors)
        _require(bool(row.get("source_ref", "").strip()) and bool(row.get("revalidation_ref", "").strip()), f"{finding_id}: source/revalidation route missing", errors)
        for ref in [item.strip() for item in row.get("source_ref", "").split(";") + row.get("fix_ref", "").split(";") + row.get("revalidation_ref", "").split(";") if item.strip().startswith("KMFA/")]:
            _require(_safe_ref(ref), f"{finding_id}: unsafe/missing finding ref {ref}", errors)
        is_blocking = row.get("blocks_stage_acceptance", "").lower() == "true"
        blocking += int(is_blocking)
        open_p0_p1 += int(row.get("severity") in {"P0", "P1"} and row.get("status") != "FIXED_VALIDATED")
    _require(blocking == 0 and open_p0_p1 == 0, "Stage PASS requires zero blocking and zero open P0/P1 findings", errors)

    risk_ids = [row.get("risk_id", "") for row in risks]
    _require(bool(risks) and len(risk_ids) == len(set(risk_ids)), "risk register must be nonempty and uniquely identified", errors)
    for row in risks:
        risk_id = row.get("risk_id", "")
        _require(set(row) == set(builder.RISK_COLUMNS), f"{risk_id}: risk columns drift", errors)
        _require(row.get("severity") in {"P0", "P1", "P2"}, f"{risk_id}: risk severity drift", errors)
        _require(row.get("plan_complete", "").lower() == "true", f"{risk_id}: risk route incomplete", errors)
        _require(bool(row.get("follow_up_stage_task", "").strip()) and bool(row.get("control", "").strip()), f"{risk_id}: owner/target/control route missing", errors)
        _require(row.get("blocks_s02_stage_acceptance", "").lower() == "false", f"{risk_id}: blocking risk contradicts PASS", errors)
        refs = [item.strip() for item in row.get("evidence_refs", "").split(";") if item.strip()]
        _require(bool(refs), f"{risk_id}: risk evidence missing", errors)
        for ref in refs:
            _require(_safe_ref(ref), f"{risk_id}: unsafe/missing risk evidence {ref}", errors)
    manifest_findings = manifest.get("review_findings", {})
    _require(manifest_findings.get("total") == len(findings) and manifest_findings.get("blocking_open") == 0, "manifest finding accounting drift", errors)
    matrix_findings = matrix.get("review_finding_accounting", {})
    _require(matrix_findings.get("total") == len(findings) and matrix_findings.get("blocking_open") == 0, "matrix finding accounting drift", errors)
    for owner, label in ((manifest, "manifest"), (matrix, "matrix")):
        risk_accounting = owner.get("open_risk_accounting", {})
        _require(risk_accounting.get("total") == len(risks), f"{label} risk accounting total drift", errors)
        _require(risk_accounting.get("p0_p1_plan_gap_count") == 0, f"{label} P0/P1 risk plan gap", errors)


def _validate_contracts(contracts: Mapping[str, Any], errors: list[str]) -> None:
    _require(contracts.get("schema_version") == "kmfa.v015.s02_cross_phase_contracts.v1", "contracts schema drift", errors)
    rows = contracts.get("contracts", [])
    ids = [str(row.get("contract_id", "")) for row in rows if isinstance(row, dict)] if isinstance(rows, list) else []
    _require(bool(rows) and len(ids) == len(set(ids)), "cross-phase contracts missing/duplicate", errors)
    for row in rows:
        if not isinstance(row, dict):
            errors.append("cross-phase contract row must be object")
            continue
        contract_id = str(row.get("contract_id", ""))
        _require(row.get("status") == "PASS", f"{contract_id}: cross-phase contract not PASS", errors)
        _require(isinstance(row.get("blocking"), bool), f"{contract_id}: blocking policy must be boolean", errors)
        _require(str(row.get("expected", "")).strip() and str(row.get("observed", "")).strip(), f"{contract_id}: expected/observed missing", errors)
        refs = row.get("evidence_refs", [])
        _require(isinstance(refs, list), f"{contract_id}: contract evidence must be a list", errors)
        if isinstance(refs, list):
            for ref in refs:
                _require(_safe_ref(ref), f"{contract_id}: unsafe/missing evidence {ref}", errors)
    accounting = contracts.get("accounting", {})
    _require(accounting.get("total") == len(rows) and accounting.get("passed") == len(rows) and accounting.get("blocking_failed", accounting.get("blocking")) == 0, "contract accounting drift", errors)


def _validate_stage_boundary(owner: Mapping[str, Any], errors: list[str], *, label: str) -> None:
    gate = owner.get("stage_gate", {})
    for key, expected in EXPECTED_STAGE_GATE.items():
        _require(gate.get(key) == expected, f"{label}: Stage gate drift {key}", errors)
    _require(gate.get("final_validation_status") in {None, "PASS"}, f"{label}: final validation not PASS", errors)
    next_gate = owner.get("next_entry_gate", {})
    _require(next_gate.get("next_allowed_run", next_gate.get("next_allowed_taskpack_phase")) == "S03-P1", f"{label}: next run must be S03-P1 only", errors)
    _require(next_gate.get("s03_p1_entry_allowed") is True, f"{label}: S03-P1 entry gate drift", errors)
    _require(next_gate.get("s03_p1_started", next_gate.get("s03_started_in_current_run", next_gate.get("s03_p1_started_in_current_run", False))) is False, f"{label}: S03 started prematurely", errors)
    _require(next_gate.get("s03_plus_entry_allowed", next_gate.get("s03_p2_plus_entry_allowed", False)) is False, f"{label}: S03-P2+ opened prematurely", errors)
    _require(next_gate.get("product_implementation_allowed") is False, f"{label}: product implementation opened", errors)
    downstream = owner.get("downstream_actions", {})
    _require(isinstance(downstream, Mapping) and bool(downstream), f"{label}: downstream contract missing", errors)
    if isinstance(downstream, Mapping):
        for key, value in downstream.items():
            _require(value is False, f"{label}: downstream action true: {key}", errors)
        for key in FALSE_DOWNSTREAM_KEYS & set(downstream):
            _require(downstream.get(key) is False, f"{label}: forbidden action true: {key}", errors)


def _top_level_scalar(text: str, key: str) -> Optional[str]:
    match = re.search(rf"(?m)^{re.escape(key)}:\s*(.+?)\s*$", text)
    if match is None:
        return None
    return match.group(1).strip().strip('"\'')


def _validate_governance_overlay(errors: list[str]) -> None:
    project = PROJECT_GOVERNANCE_PATH.read_text(encoding="utf-8")
    roadmap = ROADMAP_GOVERNANCE_PATH.read_text(encoding="utf-8")
    metadata_project = METADATA_PROJECT_PATH.read_text(encoding="utf-8")
    readme = README_PATH.read_text(encoding="utf-8")
    model_registry = METADATA_MODEL_REGISTRY_PATH.read_text(encoding="utf-8")
    for label, text in (("project governance", project), ("roadmap governance", roadmap)):
        _require(_top_level_scalar(text, "current_phase_id") == builder.RUN_PHASE_ID, f"{label}: current phase drift", errors)
        _require(_top_level_scalar(text, "current_stage_id") in {None, "S02"}, f"{label}: current Stage drift", errors)
        _require("GO_TO_S03_P1_ONLY" in text and "PASSED" in text and "COMPLETED" in text, f"{label}: final Stage result missing", errors)
        _require("product_implementation_allowed: false" in text, f"{label}: product boundary missing", errors)
    _require(_top_level_scalar(metadata_project, "current_phase") == builder.RUN_PHASE_ID, "metadata project current phase drift", errors)
    _require(_top_level_scalar(metadata_project, "current_stage") == "S02", "metadata project current Stage drift", errors)
    _require(_top_level_scalar(metadata_project, "current_phase_kind") == "GOVERNANCE_OVERLAY", "metadata project phase-kind drift", errors)
    _require(_top_level_scalar(metadata_project, "current_stage_status") == "completed_acceptance_passed", "metadata project Stage result drift", errors)
    _require(
        _top_level_scalar(metadata_project, "s03_p1_entry_allowed") == "true"
        and _top_level_scalar(metadata_project, "s03_p1_started") == "false"
        and _top_level_scalar(metadata_project, "next_gate_id") == "S03-P1"
        and _top_level_scalar(metadata_project, "product_implementation_allowed") == "false",
        "metadata project final/boundary drift", errors,
    )
    _require("v1.5" in readme and builder.RUN_PHASE_ID in readme and "GO_TO_S03_P1_ONLY" in readme, "README Stage-review truth drift", errors)
    registry_lower = model_registry.lower()
    _require("v015_s02_stage_review" in registry_lower or "v015-s02-stage-review" in registry_lower, "metadata model registry lacks V015 S02 review mirror", errors)

    stage_rows = [row for row in _read_jsonl(METADATA_STAGE_STATUS_PATH) if row.get("phase_id") == builder.RUN_PHASE_ID]
    _require(bool(stage_rows), "metadata stage-status review row missing", errors)
    if stage_rows:
        final = stage_rows[-1]
        _require(final.get("stage_lifecycle_status") == "COMPLETED" and final.get("stage_acceptance_status") == "PASSED" and final.get("decision") == "GO_TO_S03_P1_ONLY", "metadata stage-status final truth drift", errors)
        _require(final.get("s03_p1_entry_allowed") is True and final.get("s03_started", final.get("s03_p1_started")) is False, "metadata S03 boundary drift", errors)
        for key in ("product_implementation_allowed", "github_upload_performed", "app_reinstall_performed", "business_execution_performed"):
            _require(final.get(key) is False, f"metadata final action drift: {key}", errors)

    s01 = _read_json(S01_REVIEW_PATH).get("stage_gate", {})
    _require((s01.get("stage_lifecycle_status"), s01.get("stage_acceptance_status"), s01.get("decision"), s01.get("s02_entry_allowed")) == ("BLOCKED", "NOT_PASSED", "NO_GO", False), "S01 historical Stage result rewritten", errors)
    for text in (project, roadmap, metadata_project):
        _require("s01_stage_review_lifecycle_status" not in text or "BLOCKED" in text, "S01 lifecycle history drift", errors)
        _require("s01_stage_review_acceptance_status" not in text or "NOT_PASSED" in text, "S01 acceptance history drift", errors)
        _require("s01_stage_review_decision" not in text or "NO_GO" in text, "S01 decision history drift", errors)


def _validate_event_chain(path: Path, *, development: bool, errors: list[str]) -> None:
    rows = [row for row in _read_jsonl(path) if row.get("phase_id") == builder.RUN_PHASE_ID]
    prefix = "DEV-KMFA-20260713-V015-S02-STAGE-REVIEW" if development else "EVENT-KMFA-20260713-V015-S02-STAGE-REVIEW"
    expected_ids = {prefix + "-EXECUTION", prefix + "-FINAL-VALIDATION"}
    by_id = {str(row.get("event_id", "")): row for row in rows}
    _require(len(rows) == len(by_id) == 2 and set(by_id) == expected_ids, f"{path.name}: exact execution/final event pair drift", errors)
    execution = by_id.get(prefix + "-EXECUTION", {})
    final = by_id.get(prefix + "-FINAL-VALIDATION", {})
    for event_id, row in by_id.items():
        _require((row.get("project_id"), row.get("target_release"), row.get("stage_id"), row.get("phase_id")) == ("KMFA", "v1.5", "S02", builder.RUN_PHASE_ID), f"{path.name}/{event_id}: identity drift", errors)
        _require(row.get("task_id") == builder.TASK_ID and row.get("acceptance_id") == builder.ACCEPTANCE_ID, f"{path.name}/{event_id}: task/acceptance drift", errors)
        _require(row.get("run_mode") == "IMPLEMENT" and "STAGE_REVIEW" in str(row.get("work_kind", "")), f"{path.name}/{event_id}: run contract drift", errors)
    _require(execution.get("s03_p1_entry_allowed", False) is False and execution.get("s03_started", False) is False, f"{path.name}: execution event opened S03", errors)
    _require(final.get("stage_lifecycle_status") == "COMPLETED" and final.get("stage_acceptance_status") == "PASSED" and final.get("decision") == "GO_TO_S03_P1_ONLY", f"{path.name}: final Stage result drift", errors)
    _require(final.get("s03_p1_entry_allowed") is True and final.get("s03_started") is False, f"{path.name}: final S03 boundary drift", errors)
    for key in ("product_implementation_allowed", "github_upload_performed", "app_reinstall_performed", "raw_inbox_mutated", "business_execution_performed"):
        _require(final.get(key) is False, f"{path.name}: final action drift {key}", errors)
    if execution and final:
        _require(str(execution.get("event_time", "")) < str(final.get("event_time", "")), f"{path.name}: event time order drift", errors)


def _validate_receipts(rows: list[dict[str, Any]], *, require_pass: bool, errors: list[str]) -> None:
    by_id = {str(row.get("validation_id", "")): row for row in rows}
    _require(len(rows) == len(by_id), "validation receipt IDs duplicate", errors)
    _require(set(by_id) == set(builder.EXPECTED_VALIDATION_RECEIPTS), "validation receipt ID set drift", errors)
    for validation_id, expected_command in builder.EXPECTED_VALIDATION_RECEIPTS.items():
        row = by_id.get(validation_id, {})
        _require(row.get("command") == expected_command, f"{validation_id}: exact command drift", errors)
        allowed = {"PASS"} if require_pass else {"PASS", "PENDING"}
        _require(row.get("result") in allowed, f"{validation_id}: result drift", errors)
        if row.get("result") == "PASS":
            _require(row.get("exit_code") == 0, f"{validation_id}: PASS exit code drift", errors)
        else:
            _require(row.get("exit_code") is None, f"{validation_id}: PENDING exit code must be null", errors)


def _validate_artifact_integrity(manifest: Mapping[str, Any], path_overrides: Mapping[str, Path], errors: list[str]) -> None:
    refs = manifest.get("artifact_refs", {})
    _require(refs == builder.FINAL_ARTIFACT_REFS, "artifact refs drift", errors)
    rows = manifest.get("artifact_integrity", [])
    by_ref = {str(row.get("ref", "")): row for row in rows if isinstance(row, dict)} if isinstance(rows, list) else {}
    required = set(builder.FINAL_ARTIFACT_REFS.values()) - {builder.FINAL_ARTIFACT_REFS["manifest"]}
    _require(isinstance(rows, list) and len(rows) == len(by_ref) and set(by_ref) == required, "artifact integrity coverage drift", errors)
    for ref, binding in by_ref.items():
        _require(set(binding) == {"ref", "bytes", "sha256"}, f"{ref}: integrity shape drift", errors)
        path = path_overrides.get(ref, REPO_ROOT / ref)
        _require(path.is_file(), f"{ref}: artifact missing", errors)
        if path.is_file():
            _require(binding.get("bytes") == path.stat().st_size and binding.get("sha256") == _sha256(path), f"{ref}: artifact integrity drift", errors)


def _validate_public_safe_payload(payload: bytes, errors: list[str], *, label: str) -> None:
    for token in FORBIDDEN_PUBLIC_TOKENS:
        _require(token not in payload, f"public-safe token leak in {label}: {token!r}", errors)
    _require(EMAIL_RE.search(payload) is None, f"email leak in {label}", errors)
    _require(SECRET_RE.search(payload) is None, f"secret-like assignment in {label}", errors)


def _validate_public_safe(paths: Iterable[Path], errors: list[str]) -> None:
    for path in paths:
        if not path.is_file():
            errors.append(f"public-safe artifact missing: {path}")
            continue
        _validate_public_safe_payload(path.read_bytes(), errors, label=str(path))


ALLOWED_REVIEW_DIFF_PREFIXES = (
    "KMFA/stage_artifacts/V015_S02_",
    "KMFA/tools/build_v015_s02_", "KMFA/tools/check_v015_s02_", "KMFA/tools/v015_s02_",
    "KMFA/tools/v015_roadmap_governance_sync.py",
    "KMFA/tests/test_v015_s02_", "KMFA/tests/test_v015_roadmap_governance_sync.py",
    "KMFA/docs/governance/", "KMFA/metadata/project/project.yaml",
    "KMFA/metadata/stage_status.jsonl", "KMFA/metadata/model_registry.yaml",
    "KMFA/README.md", "KMFA/HANDOFF.md", "KMFA/CHANGELOG.md", "KMFA/AGENTS.md",
    "KMFA/功能清单.md", "KMFA/开发记录.md", "KMFA/模型参数文件.md",
)


def run_structured_public_diff_check(base_ref: str, *, repo_root: Path = REPO_ROOT) -> None:
    errors: list[str] = []
    _require(base_ref == builder.REVIEW_BASE_COMMIT, "review diff base must be frozen REVIEW_BASE_COMMIT", errors)
    diff_check = subprocess.run(["git", "diff", "--check", base_ref, "--", "KMFA"], cwd=repo_root, capture_output=True, text=True, check=False)
    _require(diff_check.returncode == 0, "git diff --check failed: " + (diff_check.stdout + diff_check.stderr).strip(), errors)
    changed = subprocess.run(["git", "-c", "core.quotepath=false", "diff", "--name-only", base_ref, "--", "KMFA"], cwd=repo_root, capture_output=True, text=True, check=False)
    _require(changed.returncode == 0, "git diff name scan failed", errors)
    paths = [line.strip() for line in changed.stdout.splitlines() if line.strip()]
    for relative in paths:
        _require(any(relative == prefix or relative.startswith(prefix) for prefix in ALLOWED_REVIEW_DIFF_PREFIXES), f"review diff path outside allowlist: {relative}", errors)
        path = repo_root / relative
        if path.is_file():
            suffix = path.suffix.lower()
            try:
                if suffix == ".json":
                    json.loads(path.read_text(encoding="utf-8"))
                elif suffix == ".jsonl":
                    _read_jsonl(path)
                elif suffix == ".csv":
                    _read_csv(path)
            except (OSError, ValueError, json.JSONDecodeError) as error:
                errors.append(f"structured parse failed for {relative}: {error}")
    added = subprocess.run(
        ["git", "diff", "--unified=0", "--no-color", base_ref, "--", "KMFA"],
        cwd=repo_root, capture_output=True, check=False,
    )
    _require(added.returncode == 0, "git diff added-line scan failed", errors)
    added_payload = b"\n".join(
        line[1:] for line in added.stdout.splitlines()
        if line.startswith(b"+") and not line.startswith(b"+++")
    )
    _validate_public_safe_payload(added_payload, errors, label="review diff")
    review_root = repo_root / "KMFA/stage_artifacts/V015_S02_STAGE_REVIEW"
    if review_root.is_dir():
        _validate_public_safe((path for path in review_root.rglob("*") if path.is_file()), errors)
    if errors:
        raise ValidationError("\n".join(errors))


def _validate_exact_rebuild(
    manifest: Mapping[str, Any],
    *,
    source_package: Path,
    output_root: Path,
    errors: list[str],
) -> None:
    if not hasattr(builder, "expected_core_outputs"):
        errors.append("builder expected_core_outputs API missing")
        return
    try:
        expected = builder.expected_core_outputs(
            project_root=PROJECT_ROOT,
            source_package=source_package,
            output_root=output_root,
        )
    except Exception as error:
        errors.append(f"builder core rebuild failed: {error}")
        return
    _require(isinstance(expected, Mapping) and bool(expected), "builder core outputs empty", errors)
    if isinstance(expected, Mapping):
        for path, payload in expected.items():
            actual_path = Path(path)
            _require(actual_path.is_file(), f"exact core output missing: {actual_path}", errors)
            if actual_path.is_file():
                _require(actual_path.read_bytes() == payload, f"exact core output drift: {actual_path}", errors)
    if not hasattr(builder, "build_final_manifest"):
        errors.append("builder build_final_manifest API missing")
        return
    try:
        rebuilt = builder.build_final_manifest(
            project_root=PROJECT_ROOT,
            source_package=source_package,
            output_root=output_root,
            generated_at=str(manifest.get("generated_at", "")),
        )
    except Exception as error:
        errors.append(f"builder final manifest rebuild failed: {error}")
        return
    if isinstance(rebuilt, Mapping):
        _require(dict(rebuilt) == dict(manifest), "exact final manifest object drift", errors)
    elif isinstance(rebuilt, (bytes, bytearray)):
        _require(bytes(rebuilt) == MANIFEST_PATH.read_bytes(), "exact final manifest bytes drift", errors)
    else:
        errors.append("builder final manifest API returned unsupported value")


def _validate_dependency_validators(*, require_clean: bool, errors: list[str]) -> None:
    for phase_id, command in PHASE_VALIDATORS.items():
        current = list(command)
        if require_clean and "--require-clean-worktree" not in current:
            current.append("--require-clean-worktree")
        result = subprocess.run(current, cwd=REPO_ROOT, capture_output=True, text=True, check=False)
        _require(result.returncode == 0, f"{phase_id} strict replay failed: {(result.stdout + result.stderr).strip()}", errors)


def _validate_clean_committed_blobs(manifest: Mapping[str, Any], *, repo_root: Path, errors: list[str]) -> None:
    status = subprocess.run(["git", "status", "--short"], cwd=repo_root, capture_output=True, text=True, check=False)
    _require(status.returncode == 0 and not status.stdout.strip(), "Git worktree must be clean", errors)
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo_root, capture_output=True, text=True, check=False).stdout.strip()
    _require(bool(re.fullmatch(r"[0-9a-f]{40}", head)), "HEAD resolution failed", errors)
    ancestor = subprocess.run(["git", "merge-base", "--is-ancestor", builder.REVIEW_BASE_COMMIT, head], cwd=repo_root, capture_output=True, check=False)
    _require(ancestor.returncode == 0 and head != builder.REVIEW_BASE_COMMIT, "review result ancestry drift", errors)
    refs = set(builder.FINAL_ARTIFACT_REFS.values()) | {values["manifest_ref"] for values in builder.PHASES.values()}
    for ref in refs:
        path = repo_root / ref
        committed = subprocess.run(["git", "show", f"{head}:{ref}"], cwd=repo_root, capture_output=True, check=False)
        _require(path.is_file() and committed.returncode == 0 and committed.stdout == path.read_bytes(), f"committed blob drift: {ref}", errors)
    relative_manifest = builder.FINAL_ARTIFACT_REFS["manifest"]
    result_commit = subprocess.run(["git", "log", "-1", "--format=%H", "--", relative_manifest], cwd=repo_root, capture_output=True, text=True, check=False).stdout.strip()
    _require(result_commit == head, "Stage-review manifest result commit must equal HEAD", errors)
    try:
        run_structured_public_diff_check(builder.REVIEW_BASE_COMMIT, repo_root=repo_root)
    except ValidationError as error:
        errors.append(str(error))


def validate_v015_s02_stage_review(
    manifest_path: Path = MANIFEST_PATH,
    *,
    matrix_path: Path = MATRIX_PATH,
    findings_path: Path = FINDINGS_PATH,
    contracts_path: Path = CONTRACTS_PATH,
    risks_path: Path = RISKS_PATH,
    task_evidence_path: Path = TASK_EVIDENCE_PATH,
    validation_results_path: Path = VALIDATION_RESULTS_PATH,
    source_package: Path = builder.DEFAULT_SOURCE_PACKAGE,
    require_validation_receipts: bool = False,
    require_dependency_validators: bool = False,
    require_governance_overlay: bool = True,
    require_exact_rebuild: bool = True,
    require_clean_worktree: bool = False,
    repo_root: Path = REPO_ROOT,
) -> dict[str, Any]:
    errors: list[str] = []
    manifest_path = Path(manifest_path)
    matrix_path = Path(matrix_path)
    findings_path = Path(findings_path)
    contracts_path = Path(contracts_path)
    risks_path = Path(risks_path)
    task_evidence_path = Path(task_evidence_path)
    validation_results_path = Path(validation_results_path)
    manifest = _read_json(manifest_path)
    matrix = _read_json(matrix_path)
    findings = _read_csv(findings_path)
    contracts = _read_json(contracts_path)
    risks = _read_csv(risks_path)
    task_evidence = _read_json(task_evidence_path)
    receipts = _read_jsonl(validation_results_path)
    roadmap = _read_json(ROADMAP_SOURCE_PATH)

    _require(manifest.get("schema_version") == "kmfa.v015.s02_stage_review.v1", "manifest schema drift", errors)
    _require((manifest.get("project_id"), manifest.get("target_release"), manifest.get("stage_id")) == ("KMFA", "v1.5", "S02"), "manifest identity drift", errors)
    _require((manifest.get("run_phase_id"), manifest.get("task_id"), manifest.get("acceptance_id")) == (builder.RUN_PHASE_ID, builder.TASK_ID, builder.ACCEPTANCE_ID), "manifest run identity drift", errors)
    _require(manifest.get("review_base_commit") == builder.REVIEW_BASE_COMMIT, "manifest review base drift", errors)
    _require(manifest.get("run_mode") == "IMPLEMENT" and "STAGE_REVIEW" in str(manifest.get("work_kind", "")), "manifest run contract drift", errors)
    _require(manifest.get("content_hash") == _canonical_content_hash(manifest), "manifest content hash drift", errors)
    _validate_source_package(Path(source_package), manifest.get("source_package"), errors)
    _validate_phase_evidence(manifest, errors)
    _validate_cross_phase_live_truth(manifest, errors)
    accounting = manifest.get("task_accounting", {})
    _require(accounting.get("total") == 9 and accounting.get("accepted") == 9 and accounting.get("not_accepted") == 0, "manifest 9/9 Task accounting drift", errors)
    _validate_stage_boundary(manifest, errors, label="manifest")
    _validate_matrix(matrix, roadmap, errors)
    _validate_task_evidence(task_evidence, roadmap, errors)
    _validate_findings_and_risks(manifest, matrix, findings, risks, errors)
    _validate_contracts(contracts, errors)
    _validate_receipts(receipts, require_pass=require_validation_receipts, errors=errors)
    path_overrides = {
        builder.FINAL_ARTIFACT_REFS["manifest"]: manifest_path,
        builder.FINAL_ARTIFACT_REFS["review_matrix"]: matrix_path,
        builder.FINAL_ARTIFACT_REFS["review_findings"]: findings_path,
        builder.FINAL_ARTIFACT_REFS["cross_phase_contracts"]: contracts_path,
        builder.FINAL_ARTIFACT_REFS["open_risk_register"]: risks_path,
        builder.FINAL_ARTIFACT_REFS["task_evidence_contract"]: task_evidence_path,
        builder.FINAL_ARTIFACT_REFS["validation_results"]: validation_results_path,
    }
    _validate_artifact_integrity(manifest, path_overrides, errors)
    artifact_paths = [path_overrides.get(ref, REPO_ROOT / ref) for ref in builder.FINAL_ARTIFACT_REFS.values()]
    _validate_public_safe(artifact_paths, errors)
    if require_governance_overlay:
        _validate_governance_overlay(errors)
        _validate_event_chain(EVENTS_PATH, development=False, errors=errors)
        _validate_event_chain(DEVELOPMENT_EVENTS_PATH, development=True, errors=errors)
    if require_exact_rebuild:
        _validate_exact_rebuild(manifest, source_package=Path(source_package), output_root=manifest_path.parents[2], errors=errors)
    if require_dependency_validators:
        _validate_dependency_validators(require_clean=require_clean_worktree, errors=errors)
    if require_clean_worktree:
        _validate_clean_committed_blobs(manifest, repo_root=Path(repo_root), errors=errors)
    if errors:
        raise ValidationError("\n".join(errors))
    return manifest


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    parser.add_argument("--matrix", type=Path, default=MATRIX_PATH)
    parser.add_argument("--findings", type=Path, default=FINDINGS_PATH)
    parser.add_argument("--contracts", type=Path, default=CONTRACTS_PATH)
    parser.add_argument("--risks", type=Path, default=RISKS_PATH)
    parser.add_argument("--task-evidence", type=Path, default=TASK_EVIDENCE_PATH)
    parser.add_argument("--validation-results", type=Path, default=VALIDATION_RESULTS_PATH)
    parser.add_argument("--source-package", type=Path, default=builder.DEFAULT_SOURCE_PACKAGE)
    parser.add_argument("--require-validation-receipts", action="store_true")
    parser.add_argument("--require-dependency-validators", action="store_true")
    parser.add_argument("--require-clean-worktree", action="store_true")
    parser.add_argument("--skip-governance-overlay", action="store_true")
    parser.add_argument("--skip-exact-rebuild", action="store_true")
    parser.add_argument("--structured-public-diff-check", action="store_true")
    parser.add_argument("--base-ref", default=builder.REVIEW_BASE_COMMIT)
    args = parser.parse_args(argv)
    try:
        if args.structured_public_diff_check:
            run_structured_public_diff_check(args.base_ref)
            print("PASS: S02 Stage-review structured/public/diff checks")
            return 0
        result = validate_v015_s02_stage_review(
            args.manifest,
            matrix_path=args.matrix,
            findings_path=args.findings,
            contracts_path=args.contracts,
            risks_path=args.risks,
            task_evidence_path=args.task_evidence,
            validation_results_path=args.validation_results,
            source_package=args.source_package,
            require_validation_receipts=args.require_validation_receipts,
            require_dependency_validators=args.require_dependency_validators,
            require_governance_overlay=not args.skip_governance_overlay,
            require_exact_rebuild=not args.skip_exact_rebuild,
            require_clean_worktree=args.require_clean_worktree,
        )
    except (OSError, ValueError, KeyError, json.JSONDecodeError, BadZipFile, ValidationError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    gate = result["stage_gate"]
    print(
        "PASS: KMFA v1.5 S02 Stage review validated; "
        f"Stage={gate['stage_lifecycle_status']}/{gate['stage_acceptance_status']}/{gate['decision']}; "
        "S03-P1 entry=true started=false"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
