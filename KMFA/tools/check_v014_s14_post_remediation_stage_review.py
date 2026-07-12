#!/usr/bin/env python3
"""Validate KMFA v0.1.4 Stage 14 post-remediation review evidence."""

from __future__ import annotations

import argparse
import csv
import functools
import json
import re
import struct
import subprocess
from pathlib import Path
from typing import Any, Iterator

from KMFA.tools import v014_s14_post_remediation_stage_review as phase
from KMFA.tools.check_v014_s14_p1_post_remediation_fund_cash_loan_plan import (
    validate_v014_s14_p1_post_remediation_fund_cash_loan_plan,
)
from KMFA.tools.check_v014_s14_p2_post_remediation_invoice_tax_plan import (
    validate_v014_s14_p2_post_remediation_invoice_tax_plan,
)
from KMFA.tools.check_v014_s14_p3_post_remediation_policy_evidence_plan import (
    validate_v014_s14_p3_post_remediation_policy_evidence_plan,
)


FORBIDDEN_PUBLIC_SUFFIXES = {".zip", ".xls", ".xlsx", ".pdf", ".csv", ".db", ".sqlite", ".sqlite3"}
FORBIDDEN_PUBLIC_KEYS = {
    "raw_path_private",
    "raw_filename_private",
    "raw_sha256",
    "raw_root_private",
    "member_name_private",
    "member_sha256",
    "sheet_name_private",
    "matched_terms_private",
    "candidate_sheets_private",
    "classification_fingerprint",
    "field_plaintext",
    "header_plaintext",
    "business_amount",
    "invoice_number",
    "tax_declaration_number",
    "project_name",
    "customer_name",
    "original_filename",
}
SECRET_PATTERNS = (
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(
        r"(?i)(?:password|passwd|api[_-]?key|access[_-]?token|client[_-]?secret)"
        r"\s*[:=]\s*[\"'][^\"'\r\n]{8,}[\"']"
    ),
)


class ValidationError(Exception):
    pass


def _require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def _read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ValidationError(f"missing JSON: {path}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValidationError(f"{path} must contain an object")
    return value


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        raise ValidationError(f"missing JSONL: {path}")
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValidationError(f"{path} contains a non-object row")
            rows.append(value)
    return rows


def _walk_keys(value: Any) -> Iterator[str]:
    if isinstance(value, dict):
        for key, child in value.items():
            yield str(key)
            yield from _walk_keys(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_keys(child)


def _walk_floats(value: Any) -> Iterator[float]:
    if isinstance(value, float):
        yield value
    elif isinstance(value, dict):
        for child in value.values():
            yield from _walk_floats(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_floats(child)


def _git_output(args: list[str]) -> str:
    result = subprocess.run(
        ["git", "-c", "core.quotePath=false", *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise ValidationError(result.stderr.strip())
    return result.stdout.strip()


def _git_ignored(path: Path) -> bool:
    return subprocess.run(["git", "check-ignore", "-q", str(path)], check=False).returncode == 0


def _git_tracked(path: Path) -> bool:
    return bool(_git_output(["ls-files", "--", str(path)]))


def _phase_is_current(version_matrix_text: str) -> bool:
    return f'current_phase: "{phase.PHASE_ID}"' in version_matrix_text


def _check_public_file(path: Path, errors: list[str]) -> None:
    _require(path.is_file(), f"missing public artifact: {path}", errors)
    if not path.is_file():
        return
    _require(path.suffix.lower() not in FORBIDDEN_PUBLIC_SUFFIXES, f"forbidden suffix: {path}", errors)
    text = path.read_text(encoding="utf-8", errors="ignore")
    _require("/Users/linzezhang/Downloads" not in text, f"local raw path leaked: {path}", errors)
    _require("KMFA_MetaData" not in text, f"raw root token leaked: {path}", errors)
    for pattern in SECRET_PATTERNS:
        _require(pattern.search(text) is None, f"secret-like token: {path}", errors)
    if path.suffix.lower() == ".json":
        value = json.loads(text)
        _require(not list(_walk_floats(value)), f"float found: {path}", errors)
        for key in _walk_keys(value):
            _require(key not in FORBIDDEN_PUBLIC_KEYS, f"forbidden key {key}: {path}", errors)


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
    )


def _validate_public(errors: list[str]) -> dict[str, Any]:
    for path in _public_paths():
        _check_public_file(path, errors)
    if not phase.MANIFEST_PATH.is_file():
        return {}

    manifest = _read_json(phase.MANIFEST_PATH)
    summary = manifest.get("summary", {})
    expected_identity = {
        "project_id": "KMFA",
        "stage_id": "S14",
        "phase_id": phase.PHASE_ID,
        "roadmap_phase_id": "STAGE-REVIEW",
        "task_id": phase.TASK_ID,
        "acceptance_id": phase.ACCEPTANCE_ID,
        "version": phase.VERSION,
        "status": phase.STATUS,
        "decision": "NO_GO",
    }
    for key, expected in expected_identity.items():
        _require(manifest.get(key) == expected, f"manifest {key} mismatch", errors)
        _require(summary.get(key) == expected, f"summary {key} mismatch", errors)

    expected_summary = {
        "phase_results": {"S14-P1": "PASS", "S14-P2": "PASS", "S14-P3": "PASS"},
        "fund_source_lane_count": 4,
        "fund_private_parseable_lane_count": 4,
        "fund_row_binding_proven_lane_count": 0,
        "fund_value_binding_proven_lane_count": 0,
        "fund_planning_method_definition_count": 3,
        "fund_identified_business_item_count": 0,
        "fund_private_unique_candidate_sheet_count": 180,
        "invoice_tax_source_lane_count": 3,
        "invoice_tax_private_parseable_direct_lane_count": 2,
        "invoice_tax_row_binding_proven_lane_count": 0,
        "invoice_tax_value_binding_proven_lane_count": 0,
        "invoice_tax_issue_method_definition_count": 3,
        "invoice_tax_cash_method_definition_count": 3,
        "invoice_tax_identified_issue_candidate_count": 0,
        "invoice_tax_materialized_cash_summary_count": 0,
        "invoice_tax_private_unique_candidate_sheet_count": 612,
        "policy_program_count": 5,
        "policy_directory_definition_count": 5,
        "policy_required_evidence_category_count": 23,
        "policy_authoritative_evidence_bound_program_count": 0,
        "policy_evidence_complete_program_count": 0,
        "policy_evidence_gap_count": 5,
        "policy_risk_tip_count": 5,
        "policy_formal_qualification_conclusion_count": 0,
        "policy_private_unique_lexical_candidate_sheet_count": 3830,
        "current_stage_page_count": 3,
        "cross_page_link_count": 6,
        "broken_cross_page_link_count": 0,
        "cross_page_navigation_strongly_connected": True,
        "fixed_review_finding_count": 11,
        "open_review_finding_count": 0,
        "browser_status": "PASS",
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
        "stage14_review_performed": True,
        "s15_p1_performed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
    }
    for key, expected in expected_summary.items():
        _require(summary.get(key) == expected, f"summary {key} mismatch", errors)

    findings = manifest.get("review_findings", [])
    _require(len(findings) == 11, "review finding count mismatch", errors)
    _require(
        {row.get("finding_id") for row in findings}
        == {f"S14-POST-REVIEW-F{index:02d}" for index in range(1, 12)},
        "review finding ids mismatch",
        errors,
    )
    _require(all(row.get("status") == "fixed" for row in findings), "open review finding", errors)

    browser = manifest.get("browser_review", {})
    expected_browser = {
        "status": "PASS",
        "baseline_file_count": 6,
        "baseline_control_row_count": 54,
        "baseline_pass_count": 54,
        "baseline_warn_count": 0,
        "baseline_fail_count": 0,
        "current_page_count": 3,
        "current_control_row_count": 38,
        "current_pass_count": 38,
        "current_warn_count": 0,
        "current_fail_count": 0,
        "viewport_check_count": 6,
        "representative_interaction_check_count": 6,
        "cross_page_link_http_check_count": 6,
        "cross_page_navigation_check_count": 6,
        "console_error_count": 0,
        "horizontal_overflow_count": 0,
    }
    for key, expected in expected_browser.items():
        _require(browser.get(key) == expected, f"browser {key} mismatch", errors)
    _require(browser.get("current_page_audits", {}).get("p1", {}).get("pass_count") == 13, "P1 audit drift", errors)
    _require(browser.get("current_page_audits", {}).get("p2", {}).get("pass_count") == 12, "P2 audit drift", errors)
    _require(browser.get("current_page_audits", {}).get("p3", {}).get("pass_count") == 13, "P3 audit drift", errors)

    for key in (
        "historical_review_dependency_validated",
        "historical_pending_twelve_quarantined",
        "historical_static_business_items_quarantined",
        "historical_policy_mapping_semantics_quarantined",
        "historical_upload_ready_semantics_quarantined",
    ):
        _require(manifest.get(key) is True, f"historical quarantine missing: {key}", errors)
    _require(
        manifest.get("historical_review_dynamic_state_is_authoritative") is False,
        "historical review remains authoritative",
        errors,
    )
    _require(manifest.get("next_phase") == "S15-P1", "next phase mismatch", errors)
    matrix = manifest.get("acceptance_matrix", {})
    _require(matrix.get("check_count") == 13, "matrix check count mismatch", errors)
    _require(matrix.get("check_pass_count") == 13, "matrix pass count mismatch", errors)
    _require(matrix.get("check_fail_count") == 0, "matrix failure", errors)

    mirrors = (
        (phase.SUMMARY_PATH, summary),
        (phase.METADATA_SUMMARY_PATH, summary),
        (phase.METADATA_MANIFEST_PATH, manifest),
        (phase.MATRIX_PATH, matrix),
        (phase.METADATA_MATRIX_PATH, matrix),
        (phase.METADATA_GO_NO_GO_PATH, _read_json(phase.GO_NO_GO_PATH)),
    )
    for path, expected in mirrors:
        _require(_read_json(path) == expected, f"mirror drift: {path}", errors)
    return manifest


def _validate_dependencies(errors: list[str]) -> None:
    validators = (
        ("S14-P1", validate_v014_s14_p1_post_remediation_fund_cash_loan_plan),
        ("S14-P2", validate_v014_s14_p2_post_remediation_invoice_tax_plan),
        ("S14-P3", validate_v014_s14_p3_post_remediation_policy_evidence_plan),
    )
    for name, validator in validators:
        try:
            manifest = validator(
                require_private_evidence=True,
                require_browser_evidence=True,
                require_final_evidence=True,
            )
        except Exception as exc:
            errors.append(f"{name} dependency failed: {exc}")
            continue
        _require(manifest.get("decision") == "NO_GO", f"{name} decision drift", errors)
        _require(manifest.get("summary", {}).get("current_report_grade") == "D", f"{name} grade drift", errors)


def _validate_cross_page_html(errors: list[str]) -> None:
    for page_id, spec in phase.PAGE_SPECS.items():
        path = spec["path"]
        _require(path.is_file(), f"stage page missing: {page_id}", errors)
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        _require(spec["marker"] in text, f"stage marker missing: {page_id}", errors)
        _require("Stage 14 三个 phase 均已完成" in text, f"stage status missing: {page_id}", errors)
        _require("Q4 / D" in text and "NO_GO" in text, f"quality status missing: {page_id}", errors)
        _require("gradient(" not in text, f"gradient found: {page_id}", errors)
        _require("pending_reconciliation_count" not in text, f"legacy pending leaked: {page_id}", errors)
    p1_text = phase.p1.HTML_PATH.read_text(encoding="utf-8")
    p2_text = phase.p2.HTML_PATH.read_text(encoding="utf-8")
    p3_text = phase.p3.HTML_PATH.read_text(encoding="utf-8")
    _require(p1_text.count("data-stage-link=") == 2, "P1 stage link count mismatch", errors)
    _require(p2_text.count("data-stage-link=") == 1, "P2 stage link count mismatch", errors)
    _require(p3_text.count('data-dependency-link="fund-cash-loan"') == 2, "P3 P1 link mismatch", errors)
    _require(p3_text.count('data-dependency-link="invoice-tax"') == 2, "P3 P2 link mismatch", errors)
    for page_id, text in (("p1", p1_text), ("p2", p2_text), ("p3", p3_text)):
        _require("table{min-width:0;table-layout:fixed}" in text, f"mobile table guard missing: {page_id}", errors)
        _require("word-break:break-word" in text, f"mobile wrapping guard missing: {page_id}", errors)
    for source, target, selector in phase.LINK_SPECS:
        source_path = phase.PAGE_SPECS[source]["path"]
        source_text = source_path.read_text(encoding="utf-8")
        attribute = selector.split("[")[1].split("=")[0]
        value = selector.split('"')[1]
        match = re.search(rf'<a[^>]*{re.escape(attribute)}="{re.escape(value)}"[^>]*href="([^"]+)"', source_text)
        _require(match is not None, f"cross-page selector missing: {source}->{target}", errors)
        if match:
            _require((source_path.parent / match.group(1)).resolve().is_file(), f"cross-page target missing: {source}->{target}", errors)


def _validate_boundaries(manifest: dict[str, Any], errors: list[str]) -> None:
    _require(manifest.get("quality_gate") == phase._quality_gate(), "quality gate mismatch", errors)
    _require(manifest.get("review_boundaries") == phase._review_boundaries(), "review boundary mismatch", errors)
    _require(manifest.get("public_repo_safety") == phase._public_safety(), "public safety mismatch", errors)
    boundaries = manifest.get("review_boundaries", {})
    true_keys = {"s14_p1_validated", "s14_p2_validated", "s14_p3_validated", "stage14_review_performed"}
    for key, value in boundaries.items():
        _require(value is (key in true_keys), f"boundary drift: {key}", errors)


def _validate_governance(errors: list[str]) -> None:
    events = [row for row in _read_jsonl(phase.DEVELOPMENT_EVENTS_PATH) if row.get("phase_id") == phase.PHASE_ID]
    statuses = [row for row in _read_jsonl(phase.STAGE_STATUS_PATH) if row.get("phase_id") == phase.PHASE_ID]
    tasks = [row for row in _read_jsonl(phase.TASK_STATUS_PATH) if row.get("phase_id") == phase.PHASE_ID]
    _require(len(events) == 1, "development event missing or duplicated", errors)
    _require(len(statuses) == 1, "stage status missing or duplicated", errors)
    _require(len(tasks) == 1, "task status missing or duplicated", errors)
    if events:
        _require(events[0].get("fixed_review_finding_count") == 11, "event finding count mismatch", errors)
        _require(events[0].get("open_review_finding_count") == 0, "event open finding mismatch", errors)
        _require(events[0].get("files_changed") == phase._phase_public_files(), "event file list mismatch", errors)
        _require(events[0].get("github_upload_performed") is False, "event upload mismatch", errors)
    if statuses:
        _require(statuses[0].get("status") == phase.STATUS, "stage status mismatch", errors)
    if tasks:
        _require(tasks[0].get("acceptance_id") == phase.ACCEPTANCE_ID, "task acceptance mismatch", errors)

    formula_text = Path("KMFA/docs/governance/formula_registry.yaml").read_text(encoding="utf-8")
    _require(phase.FORMULA_ID in formula_text, "formula missing", errors)
    for token in (
        "phase_pass_count == 3",
        "fund_identified_business_item_count == 0",
        "invoice_tax_identified_issue_candidate_count == 0",
        "invoice_tax_materialized_cash_summary_count == 0",
        "policy_authoritative_evidence_bound_program_count == 0",
        "policy_formal_qualification_conclusion_count == 0",
        "cross_page_link_count == 6",
        "fixed_review_finding_count == 11",
        "open_review_finding_count == 0",
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
    expected = {
        "PARAM-KMFA-1762": (
            "4;4;0;0;3;0;180;3;2;0;0;3;3;0;0;612;5;5;23;0;0;5;5;0;3830;3;6;0;11;0;"
            "5;3;9;2;1;Q4;D;NO_GO"
        ),
        "PARAM-KMFA-1763": "6;54;54;0;0;3;38;38;0;0;6;6;6;6;0;0;13;12;13",
        "PARAM-KMFA-1764": (
            "true;true;true;true;false;false;false;false;false;false;false;false;false;false;false;"
            "false;false;true;true;Q4;D;NO_GO"
        ),
    }
    for parameter_id, expected_value in expected.items():
        row = parameters.get(parameter_id, {})
        for field in ("default_value", "initial_or_prior_value", "active_value", "extracted_value"):
            _require(row.get(field) == expected_value, f"parameter drift: {parameter_id}:{field}", errors)

    version_matrix = Path("KMFA/docs/governance/VERSION_MATRIX.yaml").read_text(encoding="utf-8")
    _require(phase.MODEL_REGISTRY_KEY in version_matrix, "VERSION_MATRIX profile missing", errors)
    _require(phase.VERSION in version_matrix, "VERSION_MATRIX version missing", errors)
    if _phase_is_current(version_matrix):
        _require(Path("KMFA/VERSION").read_text(encoding="utf-8").strip() == phase.VERSION, "VERSION drift", errors)
        handoff = Path("KMFA/HANDOFF.md").read_text(encoding="utf-8")
        _require(phase.PHASE_ID in handoff, "HANDOFF phase drift", errors)
        _require("下一步只能执行 S15-P1" in handoff, "HANDOFF S15-P1 routing missing", errors)
        _require("不得执行 S15-P2" in handoff, "HANDOFF later-phase boundary missing", errors)
        _require("不得执行 GitHub upload" in handoff, "HANDOFF upload boundary missing", errors)
        agents = Path("KMFA/AGENTS.md").read_text(encoding="utf-8")
        _require("Stage 14 整体复审" in agents and "S15-P1" in agents, "AGENTS scope drift", errors)

    traceability = Path("KMFA/docs/governance/TRACEABILITY_MATRIX.csv").read_text(encoding="utf-8")
    delivery = Path("KMFA/docs/governance/delivery_tasks.yaml").read_text(encoding="utf-8")
    assurance = Path("KMFA/docs/governance/ASSURANCE_STATUS.yaml").read_text(encoding="utf-8")
    _require(phase.TASK_ID in traceability and phase.ACCEPTANCE_ID in traceability, "traceability missing", errors)
    _require(phase.TASK_ID in delivery and phase.ACCEPTANCE_ID in delivery, "delivery task missing", errors)
    _require(phase.FORMULA_ID in assurance, "assurance formula missing", errors)
    for parameter_id in phase.PARAMETER_IDS:
        _require(parameter_id in assurance, f"assurance parameter missing: {parameter_id}", errors)
    for path, token in (
        (Path("KMFA/CHANGELOG.md"), phase.VERSION),
        (Path("KMFA/docs/governance/DEVELOPMENT_LEDGER.md"), phase.PHASE_ID),
        (Path("KMFA/docs/governance/MODEL_SPEC.md"), phase.FORMULA_ID),
        (Path("KMFA/功能清单.md"), "Stage 14 修补后整体复审"),
        (Path("KMFA/开发记录.md"), phase.TASK_ID),
        (Path("KMFA/模型参数文件.md"), phase.FORMULA_ID),
    ):
        _require(token in path.read_text(encoding="utf-8"), f"governance token missing: {path}", errors)


def _read_audit(path: Path, errors: list[str], expected_files: int, expected_rows: int) -> None:
    _require(path.is_file(), f"audit missing: {path}", errors)
    if not path.is_file():
        return
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    _require(len(rows) == expected_rows, f"audit row count mismatch: {path}", errors)
    _require(len({row.get("file") for row in rows}) == expected_files, f"audit file count mismatch: {path}", errors)
    _require(all(row.get("status") == "PASS" for row in rows), f"audit non-pass row: {path}", errors)


def _png_dimensions(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValidationError(f"invalid PNG: {path}")
    return struct.unpack(">II", data[16:24])


def _validate_private(errors: list[str], require_browser_evidence: bool) -> None:
    private_paths = (
        phase.PRIVATE_RAW_BEFORE_PATH,
        phase.PRIVATE_RAW_AFTER_PATH,
        phase.PRIVATE_REVIEW_REPORT_PATH,
    )
    for path in private_paths:
        _require(path.is_file(), f"private evidence missing: {path}", errors)
        _require(_git_ignored(path), f"private evidence not ignored: {path}", errors)
        _require(not _git_tracked(path), f"private evidence tracked: {path}", errors)
    if all(path.is_file() for path in private_paths):
        before = _read_json(phase.PRIVATE_RAW_BEFORE_PATH)
        after = _read_json(phase.PRIVATE_RAW_AFTER_PATH)
        prior = _read_json(phase.p3.PRIVATE_RAW_AFTER_PATH)
        helper = phase.p1.s13_review.p1.s12_review.p1.s11_project
        current = helper._raw_snapshot("validate_v014_s14_post_remediation_stage_review")
        normalize = helper._normalize_raw
        _require(normalize(before) == normalize(after), "raw before/after mismatch", errors)
        _require(normalize(before) == normalize(prior), "raw cross-S14-P3 mismatch", errors)
        _require(normalize(after) == normalize(current), "raw current mismatch", errors)
        _require(before.get("file_count") == 5, "raw file count mismatch", errors)
        report = phase.PRIVATE_REVIEW_REPORT_PATH.read_text(encoding="utf-8")
        for token in (
            "review 前后快照：exact match",
            "与 S14-P3 快照：exact match",
            "3 / 9 / 2 / 1",
            "全中文最终差异报告",
        ):
            _require(token in report, f"private report token missing: {token}", errors)

    if not require_browser_evidence:
        return
    audit_paths = (
        (phase.PRIVATE_BASELINE_AUDIT_PATH, 6, 54),
        (phase.PRIVATE_P1_AUDIT_PATH, 1, 13),
        (phase.PRIVATE_P2_AUDIT_PATH, 1, 12),
        (phase.PRIVATE_P3_AUDIT_PATH, 1, 13),
    )
    for path, files, rows in audit_paths:
        _require(_git_ignored(path), f"audit not ignored: {path}", errors)
        _require(not _git_tracked(path), f"audit tracked: {path}", errors)
        _read_audit(path, errors, files, rows)
    _require(phase.PRIVATE_BROWSER_PATH.is_file(), "browser evidence missing", errors)
    _require(_git_ignored(phase.PRIVATE_BROWSER_PATH), "browser evidence not ignored", errors)
    _require(not _git_tracked(phase.PRIVATE_BROWSER_PATH), "browser evidence tracked", errors)
    if phase.PRIVATE_BROWSER_PATH.is_file():
        browser = _read_json(phase.PRIVATE_BROWSER_PATH)
        _require(browser.get("status") == "PASS", "browser status mismatch", errors)
        expected_counts = {
            "viewport_checks": 6,
            "representative_interaction_checks": 6,
            "cross_page_link_http_checks": 6,
            "cross_page_navigation_checks": 6,
        }
        for key, count in expected_counts.items():
            _require(len(browser.get(key, [])) == count, f"browser {key} count mismatch", errors)
        for key in (
            "representative_interaction_checks",
            "cross_page_link_http_checks",
            "cross_page_navigation_checks",
        ):
            _require(all(row.get("passed") is True for row in browser.get(key, [])), f"browser {key} failed", errors)
        _require(
            all(
                row.get("marker_visible") is True
                and row.get("d_no_go_visible") is True
                and row.get("stage_complete_visible") is True
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
                _require(actual_width == width, f"screenshot width mismatch: {path}", errors)
                _require(height >= 700, f"screenshot height too small: {path}", errors)


@functools.lru_cache(maxsize=8)
def validate_v014_s14_post_remediation_stage_review(
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
        _validate_boundaries(manifest, errors)
    _validate_governance(errors)
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
            _require(validation.get(key) == "PASS", f"final validation {key} mismatch", errors)
    if errors:
        raise ValidationError("; ".join(errors))
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-private-evidence", action="store_true")
    parser.add_argument("--require-browser-evidence", action="store_true")
    parser.add_argument("--require-final-evidence", action="store_true")
    args = parser.parse_args()
    manifest = validate_v014_s14_post_remediation_stage_review(
        require_private_evidence=args.require_private_evidence,
        require_browser_evidence=args.require_browser_evidence,
        require_final_evidence=args.require_final_evidence,
    )
    summary = manifest["summary"]
    print(
        "Stage 14 post-remediation strict validation PASS: "
        f"phases={sum(value == 'PASS' for value in summary['phase_results'].values())}/3 "
        f"findings={summary['fixed_review_finding_count']}/0 links={summary['cross_page_link_count']} "
        f"grade={summary['current_report_grade']} decision={summary['decision']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
