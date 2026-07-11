#!/usr/bin/env python3
"""Strict validator for current KMFA v0.1.4 S16-P2 evidence."""

from __future__ import annotations

import argparse
import csv
import json
import re
import struct
import subprocess
from pathlib import Path
from typing import Any

from KMFA.tools import v014_s16_p2_post_remediation_project_status_lifecycle as phase


FORBIDDEN_PUBLIC_SUFFIXES = {".zip", ".xlsx", ".xls", ".pdf", ".db", ".sqlite"}
FORBIDDEN_PUBLIC_TEXT = (
    "private_ref://",
    "original_filename",
    "sheet_name_private",
    "source_header_text",
    "raw_value",
    "normalized_value",
    "amount_cents",
    "amount_yuan",
    "payment_account",
    "invoice_number",
    "project_name_plaintext",
    "/Users/linzezhang/Downloads",
    "KMFA_MetaData",
)
FORBIDDEN_PUBLIC_KEYS = {
    "raw_path_private",
    "raw_filename_private",
    "member_name_private",
    "sheet_name_private",
    "matched_terms_private",
    "preview_rows_private",
    "candidate_sheets_private",
    "raw_files_private",
    "unparseable_xlsx_private",
    "raw_value",
    "normalized_value",
    "amount_cents",
    "amount_yuan",
    "payment_account",
    "invoice_number",
    "project_name_plaintext",
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
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValidationError(f"non-object JSONL row: {path}")
            rows.append(value)
    return rows


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
        phase.SOURCE_LANES_PATH,
        phase.LIFECYCLE_CONTRACT_PATH,
        phase.EXCEPTION_RULES_PATH,
        phase.HANDOFF_GUARDS_PATH,
        phase.MATRIX_PATH,
        phase.GO_NO_GO_PATH,
        phase.REPORT_PATH,
        phase.TEST_RESULTS_PATH,
        phase.RISK_REGISTER_PATH,
        phase.ROLLBACK_PATH,
        phase.HTML_PATH,
        phase.METADATA_SUMMARY_PATH,
        phase.METADATA_MANIFEST_PATH,
        phase.METADATA_SOURCE_LANES_PATH,
        phase.METADATA_LIFECYCLE_CONTRACT_PATH,
        phase.METADATA_EXCEPTION_RULES_PATH,
        phase.METADATA_HANDOFF_GUARDS_PATH,
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
    if b"\x00" in data:
        return
    text = data.decode("utf-8")
    for token in FORBIDDEN_PUBLIC_TEXT:
        _require(token not in text, f"forbidden public text in {path}: {token}", errors)
    for pattern in SECRET_PATTERNS:
        _require(pattern.search(text) is None, f"secret-like text in {path}", errors)
    if path.suffix == ".json":
        payload = json.loads(text)
        for key, value in _walk(payload):
            _require(key not in FORBIDDEN_PUBLIC_KEYS, f"forbidden key in {path}: {key}", errors)
            if isinstance(value, float):
                errors.append(f"public float value in {path}: {key}")


def _expected_summary() -> dict[str, Any]:
    return {
        "s16_p1_post_remediation_dependency_validated": True,
        "source_lane_count": 6,
        "private_candidate_covered_lane_count": 6,
        "private_candidate_sheet_count_by_lane": {
            "collection": 1621,
            "commencement": 18,
            "completion": 33,
            "invoice": 553,
            "project_status": 16,
            "settlement": 36,
        },
        "raw_source_file_count": 5,
        "private_xlsx_container_count": 48,
        "private_parseable_xlsx_count": 25,
        "private_unparseable_xlsx_count": 23,
        "private_parseable_sheet_count": 4198,
        "private_unique_candidate_sheet_count": 2021,
        "private_candidate_lane_association_count": 2277,
        "private_multi_lane_candidate_sheet_count": 224,
        "private_probe_roundtrip_mismatch_count": 0,
        "processed_candidate_sheet_count": 2021,
        "processed_candidate_lane_association_count": 2277,
        "processed_private_structure_alignment_exact": True,
        "lifecycle_state_count": 6,
        "lifecycle_transition_count": 5,
        "authoritative_row_binding_count": 0,
        "authoritative_value_binding_count": 0,
        "materialized_project_lifecycle_record_count": 0,
        "lifecycle_exception_rule_count": 4,
        "lifecycle_exception_item_count": 0,
        "commenced_not_completed_count": 0,
        "completed_not_settled_count": 0,
        "settled_not_invoiced_count": 0,
        "invoiced_not_collected_count": 0,
        "handoff_guard_count": 3,
        "public_business_value_count": 0,
        "workbench_html_count": 1,
        "browser_status": "PASS",
        "baseline_html_file_count": 6,
        "baseline_html_control_row_count": 54,
        "baseline_html_pass_count": 54,
        "current_html_file_count": 1,
        "current_html_control_row_count": 14,
        "current_html_pass_count": 14,
        "browser_viewport_check_count": 2,
        "lane_interaction_check_count": 12,
        "rule_interaction_check_count": 8,
        "dependency_link_http_check_count": 4,
        "dependency_navigation_check_count": 4,
        "console_error_count": 0,
        "horizontal_overflow_count": 0,
        "raw_snapshot_exact_match": True,
        "raw_cross_phase_snapshot_exact_match": True,
        "open_final_difference_accepted_count": 3,
        "nonzero_delta_reconciliation_count": 9,
        "zero_delta_reconciliation_count": 2,
        "incomplete_reconciliation_count": 1,
        "current_data_quality_grade": "Q4",
        "current_report_grade": "D",
        "s16_p1_performed": True,
        "s16_p2_performed": True,
        "s16_p3_performed": False,
        "stage16_review_performed": False,
        "site_construction_performed": False,
        "safety_signature_performed": False,
        "technical_signature_performed": False,
        "invoice_issuance_performed": False,
        "collection_action_performed": False,
        "payment_execution_performed": False,
        "bank_operation_performed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "formal_report_release_performed": False,
        "difference_closure_performed": False,
        "business_execution_performed": False,
    }


def _validate_public(errors: list[str]) -> dict[str, Any]:
    for path in _public_paths():
        _scan_public(path, errors)
    if not phase.MANIFEST_PATH.is_file():
        return {}
    manifest = _read_json(phase.MANIFEST_PATH)
    summary = _read_json(phase.SUMMARY_PATH)
    lanes_doc = _read_json(phase.SOURCE_LANES_PATH)
    lifecycle = _read_json(phase.LIFECYCLE_CONTRACT_PATH)
    rules_doc = _read_json(phase.EXCEPTION_RULES_PATH)
    guards_doc = _read_json(phase.HANDOFF_GUARDS_PATH)
    matrix = _read_json(phase.MATRIX_PATH)
    go_no_go = _read_json(phase.GO_NO_GO_PATH)

    _require(manifest.get("phase_id") == phase.PHASE_ID, "phase identity drift", errors)
    _require(manifest.get("roadmap_phase_id") == "S16-P2", "roadmap phase drift", errors)
    _require(manifest.get("task_id") == phase.TASK_ID, "task drift", errors)
    _require(manifest.get("acceptance_id") == phase.ACCEPTANCE_ID, "acceptance drift", errors)
    _require(manifest.get("version") == phase.VERSION, "version drift", errors)
    _require(manifest.get("status") == phase.STATUS, "status drift", errors)
    _require(manifest.get("decision") == "NO_GO", "decision drift", errors)
    _require(manifest.get("formula_id") == phase.FORMULA_ID, "formula drift", errors)
    _require(manifest.get("parameter_ids") == list(phase.PARAMETER_IDS), "parameter drift", errors)
    _require(manifest.get("model_registry_key") == phase.MODEL_REGISTRY_KEY, "model key drift", errors)
    _require(manifest.get("summary") == summary, "manifest/summary mismatch", errors)
    for key, expected in _expected_summary().items():
        _require(summary.get(key) == expected, f"summary drift: {key}", errors)

    lanes = lanes_doc.get("source_lanes", [])
    rules = rules_doc.get("rules", [])
    guards = guards_doc.get("guards", [])
    _require(lanes == manifest.get("source_lanes"), "lane document mismatch", errors)
    _require(lifecycle == manifest.get("lifecycle_contract"), "lifecycle document mismatch", errors)
    _require(rules == manifest.get("exception_rules"), "exception document mismatch", errors)
    _require(guards == manifest.get("handoff_guards"), "guard document mismatch", errors)
    _require(matrix == manifest.get("acceptance_matrix"), "matrix mismatch", errors)
    _require(go_no_go == manifest.get("go_no_go"), "go/no-go mismatch", errors)
    _require({row.get("lane_id") for row in lanes} == set(phase.LANE_IDS), "source lane set drift", errors)
    _require(all(row.get("manual_review_required") is True for row in lanes), "lane review gate drift", errors)
    _require(all(row.get("materialized_lifecycle_record_count") == 0 for row in lanes), "lane materialization drift", errors)
    _require(
        [row.get("state_id") for row in lifecycle.get("states", [])] == [state_id for state_id, _ in phase.LIFECYCLE_STATES],
        "lifecycle state order drift",
        errors,
    )
    _require(lifecycle.get("record_materialization_allowed") is False, "lifecycle materialization opened", errors)
    _require({row.get("rule_id") for row in rules} == {row["rule_id"] for row in phase.EXCEPTION_SPECS}, "exception rule set drift", errors)
    _require(all(row.get("materialized_exception_item_count") == 0 for row in rules), "exception item materialized", errors)
    _require(all(row.get("automatic_business_action_allowed") is False for row in rules), "exception action opened", errors)
    _require({row.get("guard_id") for row in guards} == {row[0] for row in phase.HANDOFF_GUARD_SPECS}, "handoff guard set drift", errors)
    for row in guards:
        _require(row.get("delegated_to_system") is False, "handoff delegated to system", errors)
        _require(row.get("signature_authority_allowed") is False, "signature authority opened", errors)
        _require(row.get("operation_execution_allowed") is False, "handoff execution opened", errors)
    _require(matrix.get("check_count") == 15, "acceptance check count drift", errors)
    _require(matrix.get("check_pass_count") == 15 and matrix.get("check_fail_count") == 0, "acceptance matrix failed", errors)
    _require(go_no_go.get("decision") == "NO_GO", "go/no-go decision drift", errors)
    for key, value in go_no_go.items():
        if key.endswith("_allowed") or key.endswith("_allowed_in_this_run"):
            if key != "structure_candidate_review_allowed":
                _require(value is False, f"go/no-go gate opened: {key}", errors)
    _require(manifest.get("quality_gate") == phase._quality_gate(), "quality gate drift", errors)
    _require(manifest.get("phase_boundaries") == phase._phase_boundaries(), "phase boundary drift", errors)
    _require(manifest.get("raw_boundary") == phase._raw_boundary(), "raw boundary drift", errors)
    _require(manifest.get("public_repo_safety") == phase._public_safety(), "public safety drift", errors)
    _require(manifest.get("historical_s16_p2_fixture_validated") is True, "historical fixture not validated", errors)
    _require(manifest.get("historical_s16_p2_dynamic_state_is_authoritative") is False, "historical state authoritative", errors)
    _require(manifest.get("historical_four_lifecycle_records_quarantined") is True, "historical lifecycle quarantine drift", errors)
    _require(manifest.get("historical_three_exception_items_quarantined") is True, "historical exception quarantine drift", errors)
    _require(manifest.get("historical_three_handoff_guards_quarantined") is True, "historical guard quarantine drift", errors)
    _require(manifest.get("next_phase") == "S16-P3", "next phase drift", errors)

    metadata_pairs = (
        (phase.SUMMARY_PATH, phase.METADATA_SUMMARY_PATH),
        (phase.MANIFEST_PATH, phase.METADATA_MANIFEST_PATH),
        (phase.SOURCE_LANES_PATH, phase.METADATA_SOURCE_LANES_PATH),
        (phase.LIFECYCLE_CONTRACT_PATH, phase.METADATA_LIFECYCLE_CONTRACT_PATH),
        (phase.EXCEPTION_RULES_PATH, phase.METADATA_EXCEPTION_RULES_PATH),
        (phase.HANDOFF_GUARDS_PATH, phase.METADATA_HANDOFF_GUARDS_PATH),
        (phase.MATRIX_PATH, phase.METADATA_MATRIX_PATH),
        (phase.GO_NO_GO_PATH, phase.METADATA_GO_NO_GO_PATH),
    )
    for left, right in metadata_pairs:
        _require(left.read_bytes() == right.read_bytes(), f"metadata copy mismatch: {right}", errors)
    return manifest


def _validate_dependencies(errors: list[str]) -> None:
    try:
        upstream = phase.validate_v014_s16_p1_post_remediation_subcontract_procurement(
            require_private_evidence=True,
            require_browser_evidence=True,
            require_final_evidence=True,
        )
        _require(upstream.get("phase_id") == phase.p1.PHASE_ID, "S16-P1 dependency phase drift", errors)
        _require(upstream.get("next_phase") == "S16-P2", "S16-P1 next phase drift", errors)
        _require(upstream.get("summary", {}).get("authoritative_row_binding_count") == 0, "S16-P1 row binding drift", errors)
    except Exception as exc:
        errors.append(f"S16-P1 dependency failed: {exc}")
    try:
        historical = phase.validate_historical_s16_p2()
        historical_summary = historical["project_status_lifecycle_summary"]
        _require(historical_summary.get("lifecycle_record_count") == 4, "historical lifecycle fixture drift", errors)
        _require(historical_summary.get("exception_item_count") == 3, "historical exception fixture drift", errors)
        _require(historical_summary.get("handoff_guard_count") == 3, "historical guard fixture drift", errors)
    except Exception as exc:
        errors.append(f"historical S16-P2 fixture failed: {exc}")


def _validate_html(errors: list[str]) -> None:
    if not phase.HTML_PATH.is_file():
        return
    text = phase.HTML_PATH.read_text(encoding="utf-8")
    for marker in (
        "项目状态生命周期工作台",
        "生产项目状态",
        "生命周期状态机",
        "生命周期异常规则",
        "人工交接门禁",
        "Q4 / D",
        "NO_GO",
        "S16-P3 仅可在下一轮执行",
    ):
        _require(marker in text, f"HTML marker missing: {marker}", errors)
    _require(text.count("data-lane-button=") == 6, "HTML lane button count drift", errors)
    _require(text.count("data-rule-button=") == 4, "HTML rule button count drift", errors)
    _require(text.count("data-dependency-link=") == 4, "HTML dependency link count drift", errors)
    _require("linear-gradient" not in text and "radial-gradient" not in text, "HTML gradient decoration found", errors)


def _expected_parameter_values(manifest: dict[str, Any]) -> dict[str, str]:
    summary = manifest["summary"]
    counts = summary["private_candidate_sheet_count_by_lane"]
    return {
        "PARAM-KMFA-1783": ";".join(
            str(value)
            for value in (
                6, 6, 5, 48, 25, 23, 4198, 2021, 2277, 224, 0,
                counts["project_status"], counts["commencement"], counts["completion"],
                counts["settlement"], counts["invoice"], counts["collection"],
            )
        ),
        "PARAM-KMFA-1784": "6;5;0;0;0;4;0;0;0;0;0;3;0;3;9;2;1;Q4;D;NO_GO",
        "PARAM-KMFA-1785": (
            "6;54;54;1;14;14;2;12;8;4;4;0;0;5;true;true;true;true;true;false;false;false;false;false;"
            "false;false;false;false;false;false;false;false;false;false;false;Q4;D;NO_GO"
        ),
    }


def _validate_governance(manifest: dict[str, Any], errors: list[str]) -> None:
    formula_text = Path("KMFA/docs/governance/formula_registry.yaml").read_text(encoding="utf-8")
    _require(phase.FORMULA_ID in formula_text, "formula registry missing phase formula", errors)
    for model_path in (Path("KMFA/docs/governance/model_registry.yaml"), Path("KMFA/metadata/model_registry.yaml")):
        text = model_path.read_text(encoding="utf-8")
        _require(phase.MODEL_REGISTRY_KEY in text, f"model registry key missing: {model_path}", errors)
        _require(phase.FORMULA_ID in text, f"model formula missing: {model_path}", errors)
        for parameter_id in phase.PARAMETER_IDS:
            _require(parameter_id in text, f"model parameter missing in {model_path}: {parameter_id}", errors)

    with Path("KMFA/docs/governance/parameter_registry.csv").open(encoding="utf-8-sig", newline="") as handle:
        rows = {row["parameter_id"]: row for row in csv.DictReader(handle) if row.get("parameter_id") in phase.PARAMETER_IDS}
    expected_values = _expected_parameter_values(manifest)
    _require(set(rows) == set(phase.PARAMETER_IDS), "parameter registry row set drift", errors)
    for parameter_id, expected in expected_values.items():
        row = rows.get(parameter_id, {})
        _require(row.get("formula_id") == phase.FORMULA_ID, f"parameter formula drift: {parameter_id}", errors)
        _require(row.get("active_value") == expected, f"parameter active value drift: {parameter_id}", errors)
        _require(row.get("extracted_value") == expected, f"parameter extracted value drift: {parameter_id}", errors)
        _require(row.get("status") == "active", f"parameter status drift: {parameter_id}", errors)

    text_checks = (
        (Path("KMFA/docs/governance/TRACEABILITY_MATRIX.csv"), phase.ACCEPTANCE_ID),
        (Path("KMFA/docs/governance/VERSION_MATRIX.yaml"), f'current_phase: "{phase.PHASE_ID}"'),
        (Path("KMFA/docs/governance/delivery_tasks.yaml"), phase.TASK_ID),
        (Path("KMFA/docs/governance/DEVELOPMENT_LEDGER.md"), phase.PHASE_ID),
        (Path("KMFA/docs/governance/MODEL_SPEC.md"), phase.FORMULA_ID),
        (Path("KMFA/AGENTS.md"), phase.PHASE_ID),
        (Path("KMFA/功能清单.md"), phase.PHASE_ID),
        (Path("KMFA/开发记录.md"), phase.TASK_ID),
        (Path("KMFA/模型参数文件.md"), phase.FORMULA_ID),
        (Path("KMFA/HANDOFF.md"), phase.PHASE_ID),
        (Path("KMFA/CHANGELOG.md"), phase.PHASE_ID),
    )
    for path, marker in text_checks:
        _require(path.is_file() and marker in path.read_text(encoding="utf-8"), f"governance marker missing: {path}", errors)
    _require(Path("KMFA/VERSION").read_text(encoding="utf-8").strip() == phase.VERSION, "VERSION drift", errors)

    event_rows = _read_jsonl(phase.DEVELOPMENT_EVENTS_PATH)
    stage_rows = _read_jsonl(phase.STAGE_STATUS_PATH)
    task_rows = _read_jsonl(phase.TASK_STATUS_PATH)
    event = [row for row in event_rows if row.get("phase_id") == phase.PHASE_ID]
    stage = [row for row in stage_rows if row.get("phase_id") == phase.PHASE_ID]
    task = [row for row in task_rows if row.get("phase_id") == phase.PHASE_ID]
    _require(len(event) == 1 and event[0].get("status") == phase.STATUS, "development event drift", errors)
    _require(len(stage) == 1 and stage[0].get("s16_p2_performed") is True, "stage status drift", errors)
    _require(len(task) == 1 and task[0].get("s16_p3_performed") is False, "task status drift", errors)


def _read_audit(path: Path, expected_rows: int, errors: list[str]) -> None:
    _require(path.is_file(), f"audit missing: {path}", errors)
    if not path.is_file():
        return
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    _require(len(rows) == expected_rows, f"audit row count drift: {path}", errors)
    _require(all(row.get("status") == "PASS" for row in rows), f"audit non-PASS row: {path}", errors)


def _png_dimensions(path: Path) -> tuple[int, int]:
    data = path.read_bytes()[:24]
    if len(data) != 24 or data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValidationError(f"invalid PNG: {path}")
    return struct.unpack(">II", data[16:24])


def _validate_private(manifest: dict[str, Any], errors: list[str], require_browser: bool) -> None:
    private_paths = (
        phase.PRIVATE_RAW_BEFORE_PATH,
        phase.PRIVATE_RAW_AFTER_PATH,
        phase.PRIVATE_PROBE_PATH,
        phase.PRIVATE_DIFFERENCE_REPORT_PATH,
        phase.PRIVATE_BASELINE_AUDIT_PATH,
        phase.PRIVATE_CURRENT_AUDIT_PATH,
    )
    for path in private_paths:
        _require(path.is_file(), f"private evidence missing: {path}", errors)
        _require(_git_ignored(path), f"private evidence not ignored: {path}", errors)
        _require(not _git_tracked(path), f"private evidence tracked: {path}", errors)
    probe = _read_json(phase.PRIVATE_PROBE_PATH)
    summary = manifest["summary"]
    for key in (
        "raw_source_file_count",
        "private_xlsx_container_count",
        "private_parseable_xlsx_count",
        "private_unparseable_xlsx_count",
        "private_parseable_sheet_count",
        "private_candidate_sheet_count_by_lane",
        "private_candidate_covered_lane_count",
        "private_unique_candidate_sheet_count",
        "private_candidate_lane_association_count",
        "private_multi_lane_candidate_sheet_count",
        "private_probe_roundtrip_mismatch_count",
    ):
        _require(probe.get(key) == summary.get(key), f"private/public probe mismatch: {key}", errors)
    _require(probe.get("authoritative_row_binding_count") == 0, "private row binding drift", errors)
    _require(probe.get("authoritative_value_binding_count") == 0, "private value binding drift", errors)
    _require(probe.get("materialized_project_lifecycle_record_count") == 0, "private lifecycle materialized", errors)
    _require(probe.get("lifecycle_exception_item_count") == 0, "private exception item materialized", errors)
    _require(len(probe.get("candidate_sheets_private", [])) == 2021, "private candidate list count drift", errors)

    raw_helper = phase.p1.s15_review.p1.s14_review.p1.s13_review.p1.s12_review.p1.s11_project
    before = _read_json(phase.PRIVATE_RAW_BEFORE_PATH)
    after = _read_json(phase.PRIVATE_RAW_AFTER_PATH)
    prior = _read_json(phase.p1.PRIVATE_RAW_AFTER_PATH)
    current = raw_helper._raw_snapshot("validator_v014_s16_p2_post_remediation_project_status_lifecycle")
    normalize = raw_helper._normalize_raw
    _require(normalize(before) == normalize(after), "raw before/after mismatch", errors)
    _require(normalize(before) == normalize(prior) == normalize(current), "raw cross-phase mismatch", errors)

    if not require_browser:
        return
    _require(phase.PRIVATE_BROWSER_PATH.is_file(), "browser evidence missing", errors)
    _require(_git_ignored(phase.PRIVATE_BROWSER_PATH), "browser evidence not ignored", errors)
    _require(not _git_tracked(phase.PRIVATE_BROWSER_PATH), "browser evidence tracked", errors)
    browser = _read_json(phase.PRIVATE_BROWSER_PATH)
    _require(browser.get("status") == "PASS", "browser status failed", errors)
    _require(len(browser.get("viewport_checks", [])) == 2, "browser viewport count drift", errors)
    _require(len(browser.get("lane_interaction_checks", [])) == 12, "browser lane count drift", errors)
    _require(len(browser.get("rule_interaction_checks", [])) == 8, "browser rule count drift", errors)
    _require(len(browser.get("dependency_link_http_checks", [])) == 4, "browser HTTP count drift", errors)
    _require(len(browser.get("dependency_navigation_checks", [])) == 4, "browser navigation count drift", errors)
    _require(all(row.get("passed") is True for row in browser.get("lane_interaction_checks", [])), "browser lane interaction failed", errors)
    _require(all(row.get("passed") is True for row in browser.get("rule_interaction_checks", [])), "browser rule interaction failed", errors)
    _require(all(row.get("passed") is True for row in browser.get("dependency_link_http_checks", [])), "browser HTTP failed", errors)
    _require(all(row.get("passed") is True for row in browser.get("dependency_navigation_checks", [])), "browser navigation failed", errors)
    _read_audit(phase.PRIVATE_BASELINE_AUDIT_PATH, 54, errors)
    _read_audit(phase.PRIVATE_CURRENT_AUDIT_PATH, 14, errors)
    for mode, expected_width in (("desktop", 1440), ("mobile", 390)):
        screenshot = phase.PRIVATE_SCREENSHOT_DIR / f"project_status_lifecycle_{mode}.png"
        _require(screenshot.is_file(), f"screenshot missing: {mode}", errors)
        if screenshot.is_file():
            _require(_git_ignored(screenshot), f"screenshot not ignored: {mode}", errors)
            width, height = _png_dimensions(screenshot)
            _require(width == expected_width and height > 0, f"screenshot dimensions drift: {mode}", errors)


def validate_v014_s16_p2_post_remediation_project_status_lifecycle(
    *,
    require_private_evidence: bool = False,
    require_browser_evidence: bool = False,
    require_final_evidence: bool = False,
) -> dict[str, Any]:
    errors: list[str] = []
    manifest = _validate_public(errors)
    _validate_dependencies(errors)
    _validate_html(errors)
    if manifest:
        _validate_governance(manifest, errors)
        if require_private_evidence:
            _validate_private(manifest, errors, require_browser_evidence)
        if require_final_evidence:
            validation = manifest.get("validation_summary", {})
            _require(validation.get("final_validation_recorded") is True, "final validation not recorded", errors)
            for key in (
                "focused_test",
                "strict_validator",
                "browser_desktop_mobile",
                "raw_alignment",
                "processed_private_structure_alignment",
                "governance_and_safety_scans",
            ):
                _require(validation.get(key) == "PASS", f"final validation drift: {key}", errors)
    if errors:
        raise ValidationError("; ".join(errors))
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-private-evidence", action="store_true")
    parser.add_argument("--require-browser-evidence", action="store_true")
    parser.add_argument("--require-final-evidence", action="store_true")
    args = parser.parse_args()
    manifest = validate_v014_s16_p2_post_remediation_project_status_lifecycle(
        require_private_evidence=args.require_private_evidence,
        require_browser_evidence=args.require_browser_evidence,
        require_final_evidence=args.require_final_evidence,
    )
    summary = manifest["summary"]
    print(
        "PASS: KMFA v0.1.4 S16-P2 post-remediation project status lifecycle validated "
        f"(source_lanes={summary['source_lane_count']}, candidates={summary['private_unique_candidate_sheet_count']}, "
        f"lifecycle_records={summary['materialized_project_lifecycle_record_count']}, "
        f"exception_items={summary['lifecycle_exception_item_count']}, handoff_guards={summary['handoff_guard_count']}, "
        f"grade={summary['current_report_grade']}, decision={summary['decision']}, "
        f"s16_p3={summary['s16_p3_performed']}, github_upload={summary['github_upload_performed']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
