#!/usr/bin/env python3
"""Validate current KMFA v0.1.4 Stage 16 post-remediation review evidence."""

from __future__ import annotations

import argparse
import csv
import functools
import json
import re
import struct
import subprocess
import sys
from pathlib import Path
from typing import Any

from KMFA.tools import v014_s16_post_remediation_stage_review as phase
from KMFA.tools.check_v014_s16_p1_post_remediation_subcontract_procurement import (
    validate_v014_s16_p1_post_remediation_subcontract_procurement,
)
from KMFA.tools.check_v014_s16_p2_post_remediation_project_status_lifecycle import (
    validate_v014_s16_p2_post_remediation_project_status_lifecycle,
)
from KMFA.tools.check_v014_s16_p3_post_remediation_customer_business_analysis import (
    validate_v014_s16_p3_post_remediation_customer_business_analysis,
)
from KMFA.tools.check_v014_s16_stage_review import validate_v014_s16_stage_review


FORBIDDEN_PUBLIC_SUFFIXES = {".zip", ".xlsx", ".xls", ".pdf", ".db", ".sqlite"}
FORBIDDEN_PUBLIC_TEXT = (
    "private_ref://",
    "original_filename",
    "sheet_name:",
    "source_header_text",
    "raw_value:",
    "normalized_value:",
    "customer_name_plaintext",
    "project_name_plaintext",
    "counterparty_name_plaintext",
    "supplier_name_plaintext",
    "contract_number",
    "invoice_number",
    "payment_account",
    "/Users/linzezhang/Downloads",
    "KMFA_MetaData",
)
FORBIDDEN_PUBLIC_KEYS = {
    "raw_file_name",
    "original_filename",
    "sheet_name",
    "source_header_text",
    "raw_value",
    "normalized_value",
    "project_ref",
    "customer_ref",
    "counterparty_ref",
    "customer_name_plaintext",
    "project_name_plaintext",
    "supplier_name_plaintext",
    "contract_number",
    "invoice_number",
    "payment_account",
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
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


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
        phase.MATRIX_PATH,
        phase.GO_NO_GO_PATH,
        phase.REPORT_PATH,
        phase.TEST_RESULTS_PATH,
        phase.RISK_REGISTER_PATH,
        phase.ROLLBACK_PATH,
        phase.METADATA_SUMMARY_PATH,
        phase.METADATA_MANIFEST_PATH,
        phase.METADATA_MATRIX_PATH,
        phase.METADATA_GO_NO_GO_PATH,
        phase.p1.HTML_PATH,
        phase.p2.HTML_PATH,
        phase.p3.HTML_PATH,
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
    if path.suffix == ".json":
        payload = json.loads(text)
        for key, value in _walk(payload):
            _require(key not in FORBIDDEN_PUBLIC_KEYS, f"forbidden key in {path}: {key}", errors)
            if isinstance(value, float):
                errors.append(f"public float value in {path}: {key}")


def _expected_summary() -> dict[str, Any]:
    return {
        "phase_results": {"S16-P1": "PASS", "S16-P2": "PASS", "S16-P3": "PASS"},
        "phase_focused_test_count": 32,
        "phase_focused_test_pass_count": 32,
        "phase_strict_validator_count": 3,
        "phase_strict_validator_pass_count": 3,
        "source_lane_count": 15,
        "phase_unique_candidate_sheet_count_sum": 6698,
        "authoritative_row_binding_count": 0,
        "authoritative_value_binding_count": 0,
        "project_match_record_count": 0,
        "unallocated_cost_pool_item_count": 0,
        "lifecycle_record_count": 0,
        "customer_summary_count": 0,
        "anomaly_or_risk_item_count": 0,
        "review_rule_count": 12,
        "handoff_guard_count": 7,
        "automatic_customer_ranking_count": 0,
        "public_business_value_count": 0,
        "review_finding_count": 9,
        "fixed_review_finding_count": 9,
        "open_review_finding_count": 0,
        "current_stage_page_count": 3,
        "cross_page_link_count": 6,
        "broken_cross_page_link_count": 0,
        "cross_page_navigation_strongly_connected": True,
        "browser_status": "PASS",
        "baseline_html_control_row_count": 54,
        "baseline_html_pass_count": 54,
        "current_html_control_row_count": 43,
        "current_html_pass_count": 43,
        "browser_viewport_check_count": 6,
        "representative_interaction_check_count": 6,
        "cross_page_link_http_check_count": 6,
        "cross_page_navigation_check_count": 6,
        "console_error_count": 0,
        "horizontal_overflow_count": 0,
        "raw_source_file_count": 5,
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
        "s16_p3_performed": True,
        "stage16_review_performed": True,
        "s17_p1_performed": False,
        "customer_ranking_performed": False,
        "customer_contact_performed": False,
        "collection_action_performed": False,
        "legal_decision_performed": False,
        "site_construction_performed": False,
        "safety_or_technical_signature_performed": False,
        "invoice_issuance_performed": False,
        "payment_or_bank_action_performed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "formal_report_release_performed": False,
        "difference_closure_performed": False,
        "persistent_business_write_performed": False,
        "business_execution_performed": False,
    }


def _validate_public(errors: list[str]) -> dict[str, Any]:
    for path in _public_paths():
        _scan_public(path, errors)
    if not phase.MANIFEST_PATH.is_file():
        return {}
    manifest = _read_json(phase.MANIFEST_PATH)
    summary = _read_json(phase.SUMMARY_PATH)
    matrix = _read_json(phase.MATRIX_PATH)
    go_no_go = _read_json(phase.GO_NO_GO_PATH)
    _require(manifest.get("phase_id") == phase.PHASE_ID, "phase identity drift", errors)
    _require(manifest.get("roadmap_phase_id") == "STAGE-REVIEW", "roadmap phase drift", errors)
    _require(manifest.get("task_id") == phase.TASK_ID, "task drift", errors)
    _require(manifest.get("acceptance_id") == phase.ACCEPTANCE_ID, "acceptance drift", errors)
    _require(manifest.get("version") == phase.VERSION, "version drift", errors)
    _require(manifest.get("status") == phase.STATUS, "status drift", errors)
    _require(manifest.get("decision") == "NO_GO", "decision drift", errors)
    _require(manifest.get("review_scope") == phase.REVIEW_SCOPE, "review scope drift", errors)
    _require(manifest.get("formula_id") == phase.FORMULA_ID, "formula identity drift", errors)
    _require(manifest.get("parameter_ids") == list(phase.PARAMETER_IDS), "parameter identity drift", errors)
    _require(manifest.get("model_registry_key") == phase.MODEL_REGISTRY_KEY, "model identity drift", errors)
    _require(manifest.get("summary") == summary, "summary mirror drift", errors)
    _require(manifest.get("acceptance_matrix") == matrix, "matrix mirror drift", errors)
    _require(manifest.get("go_no_go") == go_no_go, "go/no-go mirror drift", errors)
    for key, expected in _expected_summary().items():
        _require(summary.get(key) == expected, f"summary {key} drift", errors)
    findings = manifest.get("review_findings", [])
    _require(len(findings) == 9, "finding count drift", errors)
    _require(len({row.get("finding_id") for row in findings}) == 9, "finding identities not unique", errors)
    _require(all(row.get("status") == "fixed" for row in findings), "open finding remains", errors)
    _require(manifest.get("current_s16_chain_validated") is True, "current chain not validated", errors)
    _require(manifest.get("historical_s16_review_validated") is True, "historical review not validated", errors)
    _require(manifest.get("historical_s16_review_dynamic_state_is_authoritative") is False, "legacy dynamic state active", errors)
    _require(manifest.get("historical_five_project_matches_quarantined") is True, "legacy project matches not quarantined", errors)
    _require(manifest.get("historical_four_lifecycle_records_quarantined") is True, "legacy lifecycle records not quarantined", errors)
    _require(manifest.get("historical_four_customer_summaries_quarantined") is True, "legacy customer summaries not quarantined", errors)
    _require(manifest.get("quality_gate") == phase._quality_gate(), "quality gate drift", errors)
    _require(manifest.get("review_boundaries") == phase._review_boundaries(), "review boundary drift", errors)
    _require(manifest.get("public_repo_safety") == phase._public_safety(), "public safety drift", errors)
    _require(matrix.get("check_count") == 11 and matrix.get("check_pass_count") == 11, "acceptance matrix failed", errors)
    _require(matrix.get("check_fail_count") == 0, "acceptance failures detected", errors)
    _require(go_no_go.get("stage16_review_validated") is True, "review gate missing", errors)
    for key, value in go_no_go.items():
        if key.endswith("_allowed") or key.endswith("_allowed_in_this_run"):
            _require(value is False, f"go/no-go boundary opened: {key}", errors)
    _require(manifest.get("next_phase") == "S17-P1", "next phase drift", errors)
    for path, expected in (
        (phase.METADATA_SUMMARY_PATH, summary),
        (phase.METADATA_MANIFEST_PATH, manifest),
        (phase.METADATA_MATRIX_PATH, matrix),
        (phase.METADATA_GO_NO_GO_PATH, go_no_go),
    ):
        _require(_read_json(path) == expected, f"metadata mirror drift: {path}", errors)
    return manifest


def _validate_dependencies(errors: list[str]) -> None:
    p1_manifest = validate_v014_s16_p1_post_remediation_subcontract_procurement(
        require_private_evidence=True,
        require_browser_evidence=True,
        require_final_evidence=True,
    )
    p2_manifest = validate_v014_s16_p2_post_remediation_project_status_lifecycle(
        require_private_evidence=True,
        require_browser_evidence=True,
        require_final_evidence=True,
    )
    p3_manifest = validate_v014_s16_p3_post_remediation_customer_business_analysis(
        require_private_evidence=True,
        require_browser_evidence=True,
        require_final_evidence=True,
    )
    legacy = validate_v014_s16_stage_review()
    _require(p1_manifest["summary"]["project_match_record_count"] == 0, "P1 project match drift", errors)
    _require(p2_manifest["summary"]["materialized_project_lifecycle_record_count"] == 0, "P2 lifecycle drift", errors)
    _require(p3_manifest["summary"]["materialized_customer_summary_count"] == 0, "P3 customer summary drift", errors)
    _require(p3_manifest["summary"]["automatic_customer_ranking_count"] == 0, "P3 customer ranking drift", errors)
    _require(legacy.get("stage_gate", {}).get("project_match_count") == 5, "legacy project match fixture drift", errors)
    _require(legacy.get("stage_gate", {}).get("lifecycle_record_count") == 4, "legacy lifecycle fixture drift", errors)
    _require(legacy.get("stage_gate", {}).get("customer_summary_count") == 4, "legacy customer summary fixture drift", errors)


def _selector_parts(selector: str) -> tuple[str, str]:
    match = re.fullmatch(r'a\[data-(stage|dependency)-link="([^"]+)"\]', selector)
    if not match:
        raise ValidationError(f"unsupported selector: {selector}")
    return match.group(1), match.group(2)


def _validate_cross_page_html(errors: list[str]) -> None:
    stale = {
        "p1": "S16-P2 仅可在下一轮执行",
        "p2": "S16-P3 仅可在下一轮执行",
        "p3": "Stage 16 整体复审仅可在下一轮执行",
    }
    expected_stage_links = {"p1": 2, "p2": 1, "p3": 1}
    for page_id, spec in phase.PAGE_SPECS.items():
        path = spec["path"]
        text = path.read_text(encoding="utf-8")
        _require(spec["marker"] in text, f"page marker missing: {page_id}", errors)
        _require("Stage 16 三个 phase 与整体复审均已完成" in text, f"review status missing: {page_id}", errors)
        _require("S17 仅可在下一 run work" in text, f"S17 boundary missing: {page_id}", errors)
        _require(stale[page_id] not in text, f"stale footer remains: {page_id}", errors)
        _require(text.count("data-stage-link=") == expected_stage_links[page_id], f"stage link count drift: {page_id}", errors)
        _require("table{min-width:0;table-layout:fixed" in text, f"mobile table guard missing: {page_id}", errors)
        _require("word-break:break-word" in text, f"mobile wrapping guard missing: {page_id}", errors)
    for source_id, target_id, selector in phase.LINK_SPECS:
        kind, link_id = _selector_parts(selector)
        source_path = phase.PAGE_SPECS[source_id]["path"]
        text = source_path.read_text(encoding="utf-8")
        match = re.search(rf'data-{kind}-link="{re.escape(link_id)}" href="([^"]+)"', text)
        _require(match is not None, f"cross-page selector missing: {source_id}->{target_id}", errors)
        if match:
            target = (source_path.parent / match.group(1)).resolve()
            _require(target == phase.PAGE_SPECS[target_id]["path"].resolve(), f"cross-page target drift: {source_id}->{target_id}", errors)
            _require(target.is_file(), f"cross-page target missing: {source_id}->{target_id}", errors)


def _expected_parameters() -> dict[str, str]:
    return {
        "PARAM-KMFA-1789": "3;3;32;32;3;3;9;9;0;Q4;D;NO_GO",
        "PARAM-KMFA-1790": "15;6698;0;0;0;0;0;0;0;12;7;3;9;2;1",
        "PARAM-KMFA-1791": (
            "6;54;54;3;43;43;6;6;6;6;0;0;5;true;true;false;false;false;false;false;false;"
            "false;false;false;false;false;false;false;false;false;false;Q4;D;NO_GO"
        ),
    }


def _validate_governance(manifest: dict[str, Any], errors: list[str]) -> None:
    for path in (phase.DEVELOPMENT_EVENTS_PATH, phase.STAGE_STATUS_PATH, phase.TASK_STATUS_PATH):
        rows = [row for row in _read_jsonl(path) if row.get("phase_id") == phase.PHASE_ID]
        _require(len(rows) == 1, f"governance JSONL row count drift: {path}", errors)
        if rows:
            _require(rows[0].get("status") == phase.STATUS, f"governance status drift: {path}", errors)
    events = [row for row in _read_jsonl(phase.DEVELOPMENT_EVENTS_PATH) if row.get("phase_id") == phase.PHASE_ID]
    if events:
        _require(events[0].get("fixed_review_finding_count") == 9, "event finding count drift", errors)
        _require(events[0].get("open_review_finding_count") == 0, "event open finding drift", errors)
        _require(events[0].get("files_changed") == phase._phase_public_files(), "event file list drift", errors)

    formula_text = Path("KMFA/docs/governance/formula_registry.yaml").read_text(encoding="utf-8")
    _require(phase.FORMULA_ID in formula_text, "formula missing", errors)
    for token in (
        "phase_pass_count == 3",
        "project_match_record_count == 0",
        "lifecycle_record_count == 0",
        "customer_summary_count == 0",
        "automatic_customer_ranking_count == 0",
        "fixed_review_finding_count == 9",
        "open_review_finding_count == 0",
        "cross_page_link_count == 6",
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
        for field in ("default_value", "initial_or_prior_value", "active_value", "extracted_value"):
            _require(row.get(field) == expected, f"parameter drift: {parameter_id}:{field}", errors)

    version_matrix = Path("KMFA/docs/governance/VERSION_MATRIX.yaml").read_text(encoding="utf-8")
    _require(phase.MODEL_REGISTRY_KEY in version_matrix, "VERSION_MATRIX profile missing", errors)
    _require(phase.VERSION in version_matrix, "VERSION_MATRIX version missing", errors)
    current = f'current_phase: "{phase.PHASE_ID}"' in version_matrix
    if current:
        _require(Path("KMFA/VERSION").read_text(encoding="utf-8").strip() == phase.VERSION, "VERSION drift", errors)
        handoff = Path("KMFA/HANDOFF.md").read_text(encoding="utf-8")
        _require(phase.PHASE_ID in handoff, "HANDOFF phase drift", errors)
        _require("下一步只能执行 S17-P1" in handoff, "HANDOFF S17-P1 route missing", errors)
        _require("不得执行 S17-P2" in handoff, "HANDOFF later phase boundary missing", errors)
        _require("不得执行 GitHub upload" in handoff, "HANDOFF upload boundary missing", errors)
        agents = Path("KMFA/AGENTS.md").read_text(encoding="utf-8")
        _require("Stage 16 整体复审" in agents and "S17-P1" in agents, "AGENTS scope drift", errors)
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
        (Path("KMFA/功能清单.md"), "Stage 16 修补后整体复审"),
        (Path("KMFA/开发记录.md"), phase.TASK_ID),
        (Path("KMFA/模型参数文件.md"), phase.FORMULA_ID),
    ):
        _require(token in path.read_text(encoding="utf-8"), f"governance token missing: {path}", errors)


def _read_audit(path: Path, expected_files: int, expected_rows: int, errors: list[str]) -> None:
    _require(path.is_file(), f"audit missing: {path}", errors)
    if not path.is_file():
        return
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    _require(len(rows) == expected_rows, f"audit row count drift: {path}", errors)
    _require(len({row.get("file") for row in rows}) == expected_files, f"audit file count drift: {path}", errors)
    _require(all(row.get("status") == "PASS" for row in rows), f"audit non-pass row: {path}", errors)


def _png_dimensions(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValidationError(f"invalid PNG: {path}")
    return struct.unpack(">II", data[16:24])


def _validate_private(errors: list[str], require_browser: bool) -> None:
    paths = (
        phase.PRIVATE_RAW_BEFORE_PATH,
        phase.PRIVATE_RAW_AFTER_PATH,
        phase.PRIVATE_REVIEW_REPORT_PATH,
    )
    for path in paths:
        _require(path.is_file(), f"private evidence missing: {path}", errors)
        _require(_git_ignored(path), f"private evidence not ignored: {path}", errors)
        _require(not _git_tracked(path), f"private evidence tracked: {path}", errors)
    if all(path.is_file() for path in paths):
        before = _read_json(phase.PRIVATE_RAW_BEFORE_PATH)
        after = _read_json(phase.PRIVATE_RAW_AFTER_PATH)
        prior = _read_json(phase.p3.PRIVATE_RAW_AFTER_PATH)
        helper = phase.p1.s15_review.p1.s14_review.p1.s13_review.p1.s12_review.p1.s11_project
        current = helper._raw_snapshot("validate_v014_s16_post_remediation_stage_review")
        normalize = helper._normalize_raw
        _require(normalize(before) == normalize(after), "raw before/after mismatch", errors)
        _require(normalize(before) == normalize(prior), "raw cross-S16-P3 mismatch", errors)
        _require(normalize(after) == normalize(current), "raw current mismatch", errors)
        _require(before.get("file_count") == 5, "raw file count drift", errors)
        report = phase.PRIVATE_REVIEW_REPORT_PATH.read_text(encoding="utf-8")
        for token in ("review 前后快照：exact match", "与 S16-P3 快照：exact match", "3 / 9 / 2 / 1", "全中文最终差异报告"):
            _require(token in report, f"private report token missing: {token}", errors)
    if not require_browser:
        return
    for path, files, rows in (
        (phase.PRIVATE_BASELINE_AUDIT_PATH, 6, 54),
        (phase.PRIVATE_P1_AUDIT_PATH, 1, 15),
        (phase.PRIVATE_P2_AUDIT_PATH, 1, 15),
        (phase.PRIVATE_P3_AUDIT_PATH, 1, 13),
    ):
        _require(_git_ignored(path), f"audit not ignored: {path}", errors)
        _require(not _git_tracked(path), f"audit tracked: {path}", errors)
        _read_audit(path, files, rows, errors)
    _require(phase.PRIVATE_BROWSER_PATH.is_file(), "browser evidence missing", errors)
    _require(_git_ignored(phase.PRIVATE_BROWSER_PATH), "browser evidence not ignored", errors)
    if phase.PRIVATE_BROWSER_PATH.is_file():
        browser = _read_json(phase.PRIVATE_BROWSER_PATH)
        _require(browser.get("status") == "PASS", "browser status drift", errors)
        for key in ("viewport_checks", "representative_interaction_checks", "cross_page_link_http_checks", "cross_page_navigation_checks"):
            _require(len(browser.get(key, [])) == 6, f"browser {key} count drift", errors)
        for key in ("representative_interaction_checks", "cross_page_link_http_checks", "cross_page_navigation_checks"):
            _require(all(row.get("passed") is True for row in browser.get(key, [])), f"browser {key} failed", errors)
        _require(
            all(
                row.get("marker_visible") is True
                and row.get("d_no_go_visible") is True
                and row.get("stage_complete_visible") is True
                and row.get("s17_separate_run_visible") is True
                and row.get("console_error_count") == 0
                and row.get("no_horizontal_overflow") is True
                for row in browser.get("viewport_checks", [])
            ),
            "browser viewport safety failed",
            errors,
        )
    for page_id in phase.PAGE_SPECS:
        for mode, width in (("desktop", 1440), ("mobile", 390)):
            path = phase.PRIVATE_SCREENSHOT_DIR / f"{page_id}_{mode}.png"
            _require(path.is_file(), f"screenshot missing: {path}", errors)
            _require(_git_ignored(path), f"screenshot not ignored: {path}", errors)
            _require(not _git_tracked(path), f"screenshot tracked: {path}", errors)
            if path.is_file():
                actual_width, height = _png_dimensions(path)
                _require(actual_width == width, f"screenshot width drift: {path}", errors)
                _require(height >= 700, f"screenshot height too small: {path}", errors)


@functools.lru_cache(maxsize=8)
def validate_v014_s16_post_remediation_stage_review(
    *,
    require_private_evidence: bool = False,
    require_browser_evidence: bool = False,
    require_final_evidence: bool = False,
) -> dict[str, Any]:
    errors: list[str] = []
    manifest = _validate_public(errors)
    _validate_dependencies(errors)
    _validate_cross_page_html(errors)
    if manifest:
        _validate_governance(manifest, errors)
    if require_private_evidence:
        _validate_private(errors, require_browser_evidence)
    elif require_browser_evidence:
        errors.append("browser evidence requires private evidence")
    if require_final_evidence and manifest:
        validation = manifest.get("validation_summary", {})
        _require(validation.get("final_validation_recorded") is True, "final validation not recorded", errors)
        for key in (
            "phase_focused_tests",
            "phase_strict_validators",
            "review_focused_test",
            "review_strict_validator",
            "browser_desktop_mobile",
            "raw_alignment",
            "governance_and_safety_scans",
        ):
            _require(validation.get(key) == "PASS", f"final validation {key} drift", errors)
    if errors:
        raise ValidationError("; ".join(errors))
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-private-evidence", action="store_true")
    parser.add_argument("--require-browser-evidence", action="store_true")
    parser.add_argument("--require-final-evidence", action="store_true")
    args = parser.parse_args()
    manifest = validate_v014_s16_post_remediation_stage_review(
        require_private_evidence=args.require_private_evidence,
        require_browser_evidence=args.require_browser_evidence,
        require_final_evidence=args.require_final_evidence,
    )
    summary = manifest["summary"]
    print(
        "Stage 16 post-remediation strict validation PASS: "
        f"phases={summary['phase_strict_validator_pass_count']}/3 "
        f"findings={summary['fixed_review_finding_count']}/0 "
        f"links={summary['cross_page_link_count']} grade={summary['current_report_grade']} "
        f"decision={summary['decision']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
