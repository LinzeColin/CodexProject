#!/usr/bin/env python3
"""Validate current KMFA v0.1.4 S17-P3 operations SOP evidence."""

from __future__ import annotations

import argparse
import csv
import functools
import json
import re
import subprocess
from pathlib import Path
from typing import Any

from KMFA.tools import v014_s17_p3_post_remediation_operations_sop as phase
from KMFA.tools.check_v014_s17_p2_post_remediation_notification import (
    validate_v014_s17_p2_post_remediation_notification,
)
from KMFA.tools.check_v014_s17_p3_operations_sop import (
    validate_v014_s17_p3_operations_sop as validate_historical_s17_p3,
)


FORBIDDEN_PUBLIC_SUFFIXES = {".zip", ".xlsx", ".xls", ".pdf", ".db", ".sqlite"}
FORBIDDEN_PUBLIC_TEXT = (
    "private_ref://",
    "original_filename",
    "sheet_name_private",
    "source_header_text",
    "raw_value",
    "normalized_value",
    "customer_name_plaintext",
    "project_name_plaintext",
    "counterparty_name_plaintext",
    "supplier_name_plaintext",
    "payment_account",
    "bank_account_number",
    "contract_number",
    "invoice_number",
    "/Users/linzezhang/Downloads",
    "KMFA_MetaData",
)
FORBIDDEN_PUBLIC_KEYS = {
    "raw_path_private",
    "raw_filename_private",
    "member_name_private",
    "sheet_name_private",
    "preview_rows_private",
    "raw_value",
    "normalized_value",
    "amount_cents",
    "amount_yuan",
    "payment_account",
    "bank_account_number",
    "contract_number",
    "invoice_number",
    "source_sha256",
    "backup_sha256",
    "restored_sha256",
}
SECRET_PATTERNS = (
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"\b(?:sk|ghp|github_pat)_[A-Za-z0-9_=-]{20,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"(?i)\b(password|secret|token)\s*[:=]\s*['\"]?[A-Za-z0-9_./+=-]{16,}"),
)


class ValidationError(Exception):
    pass


def _read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ValidationError(f"missing JSON: {path}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValidationError(f"expected JSON object: {path}")
    return value


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        raise ValidationError(f"missing JSONL: {path}")
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def _git_ignored(path: Path) -> bool:
    return subprocess.run(
        ["git", "check-ignore", "-q", str(path)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    ).returncode == 0


def _git_tracked(path: Path) -> bool:
    return subprocess.run(
        ["git", "ls-files", "--error-unmatch", str(path)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    ).returncode == 0


def _walk(value: Any, key: str = "") -> list[tuple[str, Any]]:
    rows = [(key, value)]
    if isinstance(value, dict):
        for child_key, child in value.items():
            rows.extend(_walk(child, str(child_key)))
    elif isinstance(value, list):
        for child in value:
            rows.extend(_walk(child, key))
    return rows


def _public_paths() -> tuple[Path, ...]:
    return (
        phase.SUMMARY_PATH,
        phase.MANIFEST_PATH,
        phase.RUNBOOK_PATH,
        phase.KNOWLEDGE_INDEX_PATH,
        phase.ERROR_DRILL_PATH,
        phase.BACKUP_DRILL_PATH,
        phase.MATRIX_PATH,
        phase.GO_NO_GO_PATH,
        phase.REPORT_PATH,
        phase.TEST_RESULTS_PATH,
        phase.RISK_REGISTER_PATH,
        phase.ROLLBACK_PATH,
        phase.METADATA_SUMMARY_PATH,
        phase.METADATA_MANIFEST_PATH,
        phase.METADATA_RUNBOOK_PATH,
        phase.METADATA_KNOWLEDGE_INDEX_PATH,
        phase.METADATA_ERROR_DRILL_PATH,
        phase.METADATA_BACKUP_DRILL_PATH,
        phase.METADATA_MATRIX_PATH,
        phase.METADATA_GO_NO_GO_PATH,
    )


def _scan_public(path: Path, errors: list[str]) -> None:
    _require(path.is_file(), f"public evidence missing: {path}", errors)
    if not path.is_file():
        return
    _require(path.suffix.lower() not in FORBIDDEN_PUBLIC_SUFFIXES, f"forbidden suffix: {path}", errors)
    data = path.read_bytes()
    _require(b"\x00" not in data, f"binary public evidence: {path}", errors)
    text = data.decode("utf-8")
    for token in FORBIDDEN_PUBLIC_TEXT:
        _require(token not in text, f"forbidden public text in {path}: {token}", errors)
    for pattern in SECRET_PATTERNS:
        _require(pattern.search(text) is None, f"secret-like text in {path}", errors)
    if path.suffix in {".json", ".jsonl"}:
        payloads = [json.loads(line) for line in text.splitlines() if line.strip()] if path.suffix == ".jsonl" else [json.loads(text)]
        for payload in payloads:
            for key, value in _walk(payload):
                _require(key not in FORBIDDEN_PUBLIC_KEYS, f"forbidden key in {path}: {key}", errors)
                if isinstance(value, float):
                    errors.append(f"public float value in {path}: {key}")


def _expected_summary() -> dict[str, Any]:
    return {
        "current_s17_p2_validated": True,
        "historical_s17_p3_validated": True,
        "operation_runbook_count": 4,
        "runbook_type_count": 4,
        "runbook_step_count": 20,
        "knowledge_item_count": 2,
        "knowledge_item_type_count": 2,
        "knowledge_checklist_item_count": 12,
        "canonical_role_count": 4,
        "audit_action_type_count": 5,
        "runbook_owner_role_match_count": 4,
        "knowledge_owner_role_match_count": 2,
        "runbook_audit_mapping_match_count": 4,
        "cross_phase_contract_mismatch_count": 0,
        "notification_delivery_scope": "audit_log_contract_only_no_delivery",
        "error_handling_drill_count": 1,
        "error_drill_scenario_count": 2,
        "error_drill_rejected_count": 2,
        "error_drill_unexpected_accept_count": 0,
        "backup_restore_drill_count": 1,
        "synthetic_fixture_count": 1,
        "backup_created_count": 1,
        "corruption_detected_count": 1,
        "restore_completed_count": 1,
        "restored_byte_exact_count": 1,
        "production_restore_count": 0,
        "raw_copy_or_backup_count": 0,
        "external_service_call_count": 0,
        "persistent_business_write_count": 0,
        "business_execution_count": 0,
        "formal_report_count": 0,
        "raw_source_file_count": 5,
        "raw_snapshot_exact_match": True,
        "raw_cross_phase_snapshot_exact_match": True,
        "current_data_quality_grade": "Q4",
        "current_report_grade": "D",
        "open_final_difference_accepted_count": 3,
        "nonzero_delta_reconciliation_count": 9,
        "zero_delta_reconciliation_count": 2,
        "incomplete_reconciliation_count": 1,
        **phase._phase_boundaries(),
    }


def _validate_runbooks(errors: list[str]) -> None:
    rows = _read_jsonl(phase.RUNBOOK_PATH)
    by_type = {row.get("runbook_type"): row for row in rows}
    _require(len(rows) == 4 and set(by_type) == set(phase.REQUIRED_RUNBOOK_TYPES), "runbook set drift", errors)
    for runbook_type, row in by_type.items():
        _require(row.get("record_type") == "v014_s17_p3_post_remediation_operation_runbook", f"runbook record drift: {runbook_type}", errors)
        _require(row.get("execution_mode") == "manual_sop_only", f"runbook mode drift: {runbook_type}", errors)
        _require(len(row.get("steps_zh", [])) == 5, f"runbook steps drift: {runbook_type}", errors)
        _require(row.get("owner_role") in {"management", "finance", "reviewer", "readonly"}, f"runbook role drift: {runbook_type}", errors)
        _require(row.get("audit_action_type") in {"import", "processing", "report", "export", "notification"}, f"runbook audit mapping drift: {runbook_type}", errors)
        _require(row.get("audit_required_fields") == list(phase.s17_p2.AUDIT_REQUIRED_FIELDS), f"runbook audit fields drift: {runbook_type}", errors)
        _require(row.get("audit_contract_ref") == phase.s17_p2.s17_p1.AUDIT_CONTRACT_PATH.as_posix(), f"runbook audit ref drift: {runbook_type}", errors)
        for key in ("precheck_required", "evidence_required", "rollback_required", "append_only_audit_required"):
            _require(row.get(key) is True, f"runbook control missing: {runbook_type}:{key}", errors)
        for key in (
            "raw_mutation_allowed",
            "external_service_allowed",
            "production_restore_allowed",
            "business_execution_allowed",
            "formal_report_release_allowed",
        ):
            _require(row.get(key) is False, f"runbook boundary opened: {runbook_type}:{key}", errors)
        _require(bool(row.get("rollback_zh")), f"runbook rollback missing: {runbook_type}", errors)


def _validate_knowledge(errors: list[str]) -> None:
    rows = _read_jsonl(phase.KNOWLEDGE_INDEX_PATH)
    by_type = {row.get("item_type"): row for row in rows}
    _require(len(rows) == 2 and set(by_type) == set(phase.REQUIRED_KNOWLEDGE_TYPES), "knowledge set drift", errors)
    for item_type, row in by_type.items():
        _require(row.get("record_type") == "v014_s17_p3_post_remediation_knowledge_index", f"knowledge record drift: {item_type}", errors)
        _require(row.get("storage_mode") == "public_safe_knowledge_index_only", f"knowledge mode drift: {item_type}", errors)
        _require(row.get("execution_mode") == "knowledge_and_checklist_only", f"knowledge execution drift: {item_type}", errors)
        _require(len(row.get("checklist_zh", [])) == 6, f"knowledge checklist drift: {item_type}", errors)
        _require(row.get("owner_role") in {"management", "finance", "reviewer", "readonly"}, f"knowledge role drift: {item_type}", errors)
        for key in ("automated_finance_execution_allowed", "business_decision_basis_allowed", "private_document_committed", "raw_business_data_committed", "credential_material_committed"):
            _require(row.get(key) is False, f"knowledge boundary opened: {item_type}:{key}", errors)


def _validate_drills(errors: list[str]) -> None:
    error_rows = _read_jsonl(phase.ERROR_DRILL_PATH)
    backup_rows = _read_jsonl(phase.BACKUP_DRILL_PATH)
    _require(len(error_rows) == 1, "error drill count drift", errors)
    _require(len(backup_rows) == 1, "backup drill count drift", errors)
    if error_rows:
        row = error_rows[0]
        for key, expected in (
            ("execution_mode", "isolated_synthetic_runtime_drill"),
            ("scenario_count", 2),
            ("rejected_candidate_count", 2),
            ("unexpected_accept_count", 0),
            ("result_status", "PASS"),
        ):
            _require(row.get(key) == expected, f"error drill drift: {key}", errors)
        for key in ("raw_source_used", "external_service_called", "persistent_business_write_performed", "business_execution_performed"):
            _require(row.get(key) is False, f"error drill boundary opened: {key}", errors)
    if backup_rows:
        row = backup_rows[0]
        for key, expected in (
            ("execution_mode", "isolated_synthetic_runtime_drill"),
            ("synthetic_fixture_count", 1),
            ("backup_created_count", 1),
            ("corruption_detected_count", 1),
            ("restore_completed_count", 1),
            ("restored_byte_exact", True),
            ("result_status", "PASS"),
        ):
            _require(row.get(key) == expected, f"backup drill drift: {key}", errors)
        for key in ("raw_source_used", "production_restore_performed", "external_service_called", "persistent_business_write_performed", "business_execution_performed"):
            _require(row.get(key) is False, f"backup drill boundary opened: {key}", errors)


def _validate_public(errors: list[str]) -> dict[str, Any]:
    for path in _public_paths():
        _scan_public(path, errors)
    if not phase.MANIFEST_PATH.is_file():
        return {}
    manifest = _read_json(phase.MANIFEST_PATH)
    summary = _read_json(phase.SUMMARY_PATH)
    matrix = _read_json(phase.MATRIX_PATH)
    go_no_go = _read_json(phase.GO_NO_GO_PATH)
    for key, expected in (
        ("phase_id", phase.PHASE_ID),
        ("roadmap_phase_id", phase.ROADMAP_PHASE_ID),
        ("task_id", phase.TASK_ID),
        ("acceptance_id", phase.ACCEPTANCE_ID),
        ("version", phase.VERSION),
        ("status", phase.STATUS),
        ("decision", phase.DECISION),
        ("formula_id", phase.FORMULA_ID),
        ("parameter_ids", list(phase.PARAMETER_IDS)),
        ("model_registry_key", phase.MODEL_REGISTRY_KEY),
    ):
        _require(manifest.get(key) == expected, f"manifest {key} drift", errors)
    _require(manifest.get("summary") == summary, "summary mirror drift", errors)
    _require(manifest.get("acceptance_matrix") == matrix, "matrix mirror drift", errors)
    _require(manifest.get("go_no_go") == go_no_go, "go/no-go mirror drift", errors)
    for key, expected in _expected_summary().items():
        _require(summary.get(key) == expected, f"summary {key} drift", errors)
    _require(manifest.get("current_s17_p2_validated") is True, "current S17-P2 dependency missing", errors)
    _require(manifest.get("historical_s17_p3_validated") is True, "historical S17-P3 missing", errors)
    _require(manifest.get("historical_s17_p3_dynamic_state_is_authoritative") is False, "historical S17-P3 active", errors)
    _require(manifest.get("historical_structure_quarantined") == {"runbook_count": 4, "knowledge_item_count": 2, "drill_log_count": 2}, "historical structure drift", errors)
    _require(manifest.get("required_runbook_types") == list(phase.REQUIRED_RUNBOOK_TYPES), "required runbooks drift", errors)
    _require(manifest.get("required_knowledge_types") == list(phase.REQUIRED_KNOWLEDGE_TYPES), "required knowledge drift", errors)
    _require(manifest.get("quality_gate") == phase._quality_gate(), "quality gate drift", errors)
    _require(manifest.get("phase_boundaries") == phase._phase_boundaries(), "phase boundary drift", errors)
    _require(manifest.get("public_repo_safety") == phase._public_safety(), "public safety drift", errors)
    _require(manifest.get("raw_boundary") == phase._raw_boundary(), "raw boundary drift", errors)
    _require(manifest.get("repo_tracking_scan", {}).get("status") == "PASS", "repo tracking scan failed", errors)
    _require(matrix.get("check_count") == 17 and matrix.get("check_pass_count") == 17 and matrix.get("check_fail_count") == 0, "acceptance matrix failed", errors)
    _require(manifest.get("cross_phase_contract_state", {}).get("cross_phase_contract_mismatch_count") == 0, "cross-phase contract mismatch", errors)
    _require(go_no_go.get("s17_p3_validated") is True, "S17-P3 go/no-go missing", errors)
    for key, value in go_no_go.items():
        if key.endswith("_allowed") or key.endswith("_allowed_in_this_run"):
            if key not in {"manual_sop_and_knowledge_index_allowed", "isolated_synthetic_drill_allowed"}:
                _require(value is False, f"go/no-go boundary opened: {key}", errors)
    _require(manifest.get("next_phase") == "S17_STAGE_REVIEW", "next phase drift", errors)
    _require("下一轮只能执行 Stage 17 整体复审" in str(manifest.get("next_required_step")), "next step drift", errors)
    for path, expected in (
        (phase.METADATA_SUMMARY_PATH, summary),
        (phase.METADATA_MANIFEST_PATH, manifest),
        (phase.METADATA_MATRIX_PATH, matrix),
        (phase.METADATA_GO_NO_GO_PATH, go_no_go),
    ):
        _require(_read_json(path) == expected, f"metadata mirror drift: {path}", errors)
    for public_path, metadata_path in (
        (phase.RUNBOOK_PATH, phase.METADATA_RUNBOOK_PATH),
        (phase.KNOWLEDGE_INDEX_PATH, phase.METADATA_KNOWLEDGE_INDEX_PATH),
        (phase.ERROR_DRILL_PATH, phase.METADATA_ERROR_DRILL_PATH),
        (phase.BACKUP_DRILL_PATH, phase.METADATA_BACKUP_DRILL_PATH),
    ):
        _require(_read_jsonl(public_path) == _read_jsonl(metadata_path), f"metadata JSONL mirror drift: {metadata_path}", errors)
    _validate_runbooks(errors)
    _validate_knowledge(errors)
    _validate_drills(errors)
    return manifest


def _validate_dependencies(errors: list[str]) -> None:
    current = validate_v014_s17_p2_post_remediation_notification(
        require_private_evidence=True,
        require_final_evidence=True,
    )
    _require(current.get("phase_id") == phase.s17_p2.PHASE_ID, "current S17-P2 identity drift", errors)
    _require(current.get("next_phase") == "S17-P3", "current S17-P2 route drift", errors)
    _require(current.get("summary", {}).get("s17_p3_performed") is False, "current S17-P2 boundary drift", errors)
    historical = validate_historical_s17_p3()
    historical_summary = historical.get("operations_sop_summary", {})
    _require(historical_summary.get("operation_runbook_count") == 4, "historical runbook fixture drift", errors)
    _require(historical_summary.get("knowledge_item_count") == 2, "historical knowledge fixture drift", errors)
    _require(historical_summary.get("drill_log_count") == 2, "historical drill fixture drift", errors)


def _expected_parameters() -> dict[str, str]:
    boundary_values = ["true" if value else "false" for value in phase._phase_boundaries().values()]
    return {
        "PARAM-KMFA-1800": "4;4;20;2;2;12",
        "PARAM-KMFA-1801": "1;2;2;0;1;1;1;1;1",
        "PARAM-KMFA-1802": "0;0;0;0;0;0;3;9;2;1;Q4;D;NO_GO",
        "PARAM-KMFA-1803": ";".join(["5", "true", "true", *boundary_values, "Q4", "D", "NO_GO"]),
    }


def _validate_governance(manifest: dict[str, Any], errors: list[str]) -> None:
    for path in (phase.DEVELOPMENT_EVENTS_PATH, phase.STAGE_STATUS_PATH, phase.TASK_STATUS_PATH):
        rows = [row for row in _read_jsonl(path) if row.get("phase_id") == phase.PHASE_ID]
        _require(len(rows) == 1, f"governance JSONL row count drift: {path}", errors)
        if rows:
            _require(rows[0].get("status") == phase.STATUS, f"governance status drift: {path}", errors)
    events = [row for row in _read_jsonl(phase.DEVELOPMENT_EVENTS_PATH) if row.get("phase_id") == phase.PHASE_ID]
    if events:
        _require(events[0].get("files_changed") == phase._phase_public_files(), "event file list drift", errors)
        _require(events[0].get("operation_runbook_count") == 4, "event runbook count drift", errors)
        _require(events[0].get("backup_restore_drill_count") == 1, "event backup drill drift", errors)
        _require(events[0].get("production_restore_count") == 0, "event production restore drift", errors)

    formula_text = Path("KMFA/docs/governance/formula_registry.yaml").read_text(encoding="utf-8")
    _require(phase.FORMULA_ID in formula_text, "formula missing", errors)
    for token in (
        "operation_runbook_count == 4",
        "runbook_step_count == 20",
        "knowledge_item_count == 2",
        "cross_phase_contract_mismatch_count == 0",
        "error_drill_rejected_count == 2",
        "restored_byte_exact_count == 1",
        "production_restore_count == 0",
        "raw_copy_or_backup_count == 0",
        "current_grade == D",
        "decision == NO_GO",
    ):
        _require(token in formula_text, f"formula control missing: {token}", errors)
    for path in (Path("KMFA/docs/governance/model_registry.yaml"), Path("KMFA/metadata/model_registry.yaml")):
        text = path.read_text(encoding="utf-8")
        _require(phase.MODEL_REGISTRY_KEY in text, f"model missing: {path}", errors)
        _require(phase.FORMULA_ID in text, f"formula ref missing: {path}", errors)
        for parameter_id in phase.PARAMETER_IDS:
            _require(parameter_id in text, f"parameter ref missing: {path}:{parameter_id}", errors)
    with Path("KMFA/docs/governance/parameter_registry.csv").open(encoding="utf-8", newline="") as handle:
        parameters = {row["parameter_id"]: row for row in csv.DictReader(handle)}
    for parameter_id, expected in _expected_parameters().items():
        row = parameters.get(parameter_id, {})
        _require(row.get("formula_id") == phase.FORMULA_ID, f"parameter formula drift: {parameter_id}", errors)
        for field in ("default_value", "initial_or_prior_value", "active_value", "extracted_value"):
            _require(row.get(field) == expected, f"parameter drift: {parameter_id}:{field}", errors)
        _require(row.get("status") == "active", f"parameter status drift: {parameter_id}", errors)

    version_matrix = Path("KMFA/docs/governance/VERSION_MATRIX.yaml").read_text(encoding="utf-8")
    _require(phase.MODEL_REGISTRY_KEY in version_matrix and phase.VERSION in version_matrix, "VERSION_MATRIX profile missing", errors)
    current = f'current_phase: "{phase.PHASE_ID}"' in version_matrix
    if current:
        _require(Path("KMFA/VERSION").read_text(encoding="utf-8").strip() == phase.VERSION, "VERSION drift", errors)
        handoff = Path("KMFA/HANDOFF.md").read_text(encoding="utf-8")
        for token in (phase.PHASE_ID, "下一步只能执行 Stage 17 整体复审", "不得执行 Stage 18", "不得执行 GitHub upload"):
            _require(token in handoff, f"HANDOFF token missing: {token}", errors)
        agents = Path("KMFA/AGENTS.md").read_text(encoding="utf-8")
        _require(phase.PHASE_ID in agents and "Stage 17 整体复审" in agents, "AGENTS scope drift", errors)
    trace = Path("KMFA/docs/governance/TRACEABILITY_MATRIX.csv").read_text(encoding="utf-8")
    delivery = Path("KMFA/docs/governance/delivery_tasks.yaml").read_text(encoding="utf-8")
    assurance = Path("KMFA/docs/governance/ASSURANCE_STATUS.yaml").read_text(encoding="utf-8")
    _require(phase.TASK_ID in trace and phase.ACCEPTANCE_ID in trace, "traceability missing", errors)
    _require(phase.TASK_ID in delivery and phase.ACCEPTANCE_ID in delivery, "delivery task missing", errors)
    if current:
        _require(f'snapshot_event_time: "{manifest["generated_at"]}"' in assurance, "assurance time drift", errors)
    _require(phase.FORMULA_ID in assurance, "assurance formula missing", errors)
    for parameter_id in phase.PARAMETER_IDS:
        _require(parameter_id in assurance, f"assurance parameter missing: {parameter_id}", errors)
    for path, token in (
        (Path("KMFA/CHANGELOG.md"), phase.VERSION),
        (Path("KMFA/docs/governance/DEVELOPMENT_LEDGER.md"), phase.PHASE_ID),
        (Path("KMFA/docs/governance/MODEL_SPEC.md"), phase.FORMULA_ID),
        (Path("KMFA/docs/governance/OWNER_STATUS.md"), phase.PHASE_ID),
        (Path("KMFA/docs/governance/STATUS.md"), phase.PHASE_ID),
        (Path("KMFA/功能清单.md"), "S17-P3 运维与 SOP"),
        (Path("KMFA/开发记录.md"), phase.TASK_ID),
        (Path("KMFA/模型参数文件.md"), phase.FORMULA_ID),
    ):
        _require(token in path.read_text(encoding="utf-8"), f"governance token missing: {path}", errors)


def _validate_private(errors: list[str]) -> None:
    paths = (
        phase.PRIVATE_RAW_BEFORE_PATH,
        phase.PRIVATE_RAW_AFTER_PATH,
        phase.PRIVATE_DRILL_SOURCE_PATH,
        phase.PRIVATE_DRILL_WORKING_PATH,
        phase.PRIVATE_DRILL_BACKUP_PATH,
        phase.PRIVATE_DRILL_RESTORED_PATH,
        phase.PRIVATE_DRILL_DIAGNOSTIC_PATH,
        phase.PRIVATE_SCAN_REPORT_PATH,
    )
    for path in paths:
        _require(path.is_file(), f"private evidence missing: {path}", errors)
        _require(_git_ignored(path), f"private evidence not ignored: {path}", errors)
        _require(not _git_tracked(path), f"private evidence tracked: {path}", errors)
    if not all(path.is_file() for path in paths):
        return
    before = _read_json(phase.PRIVATE_RAW_BEFORE_PATH)
    after = _read_json(phase.PRIVATE_RAW_AFTER_PATH)
    prior = _read_json(phase.s17_p2.PRIVATE_RAW_AFTER_PATH)
    helper = phase.s17_p2.s17_p1.s16_review.p1.s15_review.p1.s14_review.p1.s13_review.p1.s12_review.p1.s11_project
    current = helper._raw_snapshot("validate_v014_s17_p3_post_remediation_operations_sop")
    normalize = helper._normalize_raw
    _require(normalize(before) == normalize(after), "raw before/after mismatch", errors)
    _require(normalize(before) == normalize(prior) == normalize(current), "raw cross-phase mismatch", errors)
    _require(before.get("file_count") == 5, "raw file count drift", errors)
    source = phase.PRIVATE_DRILL_SOURCE_PATH.read_bytes()
    backup = phase.PRIVATE_DRILL_BACKUP_PATH.read_bytes()
    restored = phase.PRIVATE_DRILL_RESTORED_PATH.read_bytes()
    working = phase.PRIVATE_DRILL_WORKING_PATH.read_bytes()
    _require(source == backup == restored, "synthetic backup restore not byte exact", errors)
    _require(working != backup, "synthetic corruption not retained for evidence", errors)
    diagnostic = _read_json(phase.PRIVATE_DRILL_DIAGNOSTIC_PATH)
    _require(diagnostic.get("raw_source_used") is False, "private drill raw boundary drift", errors)
    _require(diagnostic.get("error_drill_passed") is True, "private error drill failed", errors)
    _require(diagnostic.get("backup_restore_drill_passed") is True, "private backup drill failed", errors)
    _require(diagnostic.get("corruption_detected") is True, "private corruption detection failed", errors)
    _require(diagnostic.get("restored_byte_exact") is True, "private restore exactness failed", errors)
    scan = phase.s17_p2.s17_p1._repo_tracking_scan()
    _require(scan.get("tracked_forbidden_suffix_count") == 0, "current tracked forbidden suffix found", errors)
    _require(scan.get("tracked_private_runtime_path_count") == 0, "current tracked private runtime found", errors)
    report = phase.PRIVATE_SCAN_REPORT_PATH.read_text(encoding="utf-8")
    for token in (
        "phase 前后快照：exact match",
        "与 S17-P2 快照：exact match",
        "备份恢复演练：合成夹具 byte-exact 恢复",
        "全中文最终差异报告",
    ):
        _require(token in report, f"private report token missing: {token}", errors)


@functools.lru_cache(maxsize=8)
def validate_v014_s17_p3_post_remediation_operations_sop(
    *,
    require_private_evidence: bool = False,
    require_final_evidence: bool = False,
) -> dict[str, Any]:
    errors: list[str] = []
    manifest = _validate_public(errors)
    _validate_dependencies(errors)
    if manifest:
        _validate_governance(manifest, errors)
    if require_private_evidence:
        _validate_private(errors)
    if require_final_evidence and manifest:
        validation = manifest.get("validation_summary", {})
        _require(validation.get("final_validation_recorded") is True, "final validation not recorded", errors)
        for key in (
            "focused_test",
            "strict_validator",
            "isolated_error_and_backup_drills",
            "raw_alignment",
            "governance_and_safety_scans",
        ):
            _require(validation.get(key) == "PASS", f"final validation drift: {key}", errors)
    if errors:
        raise ValidationError("; ".join(errors))
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-private-evidence", action="store_true")
    parser.add_argument("--require-final-evidence", action="store_true")
    args = parser.parse_args()
    manifest = validate_v014_s17_p3_post_remediation_operations_sop(
        require_private_evidence=args.require_private_evidence,
        require_final_evidence=args.require_final_evidence,
    )
    summary = manifest["summary"]
    print(
        "S17-P3 strict validation PASS: "
        f"runbooks={summary['operation_runbook_count']} knowledge={summary['knowledge_item_count']} "
        f"error_scenarios={summary['error_drill_scenario_count']} backup_restore={summary['backup_restore_drill_count']} "
        f"production_restore={summary['production_restore_count']} grade={summary['current_report_grade']} "
        f"decision={summary['decision']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
