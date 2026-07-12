#!/usr/bin/env python3
"""Validate current public-safe KMFA v0.1.4 S13-P2 receivable evidence."""

from __future__ import annotations

import argparse
import csv
import functools
import hashlib
import json
import re
import struct
import subprocess
from pathlib import Path
from typing import Any

from KMFA.tools import v014_s13_p2_post_remediation_collection_receivable_aging as phase
from KMFA.tools.check_v014_s13_p1_post_remediation_financial_operating_report import (
    validate_v014_s13_p1_post_remediation_financial_operating_report,
)


FORBIDDEN_PUBLIC_SUFFIXES = {
    ".zip",
    ".xls",
    ".xlsx",
    ".pdf",
    ".csv",
    ".db",
    ".sqlite",
    ".sqlite3",
}
FORBIDDEN_PUBLIC_KEYS = {
    "raw_value",
    "normalized_value",
    "original_value",
    "business_value",
    "amount_cents",
    "amount_yuan",
    "row_value",
    "cell_value",
    "sheet_name",
    "member_name",
    "private_member_name",
    "private_filename",
    "private_path",
    "original_filename",
    "file_hash",
    "field_key",
    "field_label",
    "source_header_text",
    "project_name_plaintext",
    "customer_name_plaintext",
}
RAW_ROOT_TOKEN = "KMFA" + "_MetaData"
LOCAL_DOWNLOADS_PATTERN = re.compile(r"/Users/[^\s\"'`]+/Downloads/[^\s\"'`]+")
SECRET_PATTERNS = (
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(
        r"(?i)(?:password|passwd|api[_-]?key|access[_-]?token|client[_-]?secret)"
        r"\s*[:=]\s*[\"'][^\"'\r\n]{8,}[\"']"
    ),
)
PUBLIC_BUSINESS_AMOUNT_MARKERS = ("￥", "¥", "CNY", "RMB", "万元", "元整")


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
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _walk_keys(value: Any):
    if isinstance(value, dict):
        for key, child in value.items():
            yield key
            yield from _walk_keys(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_keys(child)


def _git_check_ignore(path: Path) -> bool:
    return subprocess.run(
        ["git", "check-ignore", "-q", path.as_posix()],
        check=False,
    ).returncode == 0


def _git_tracked(path: Path) -> bool:
    return subprocess.run(
        ["git", "ls-files", "--error-unmatch", path.as_posix()],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    ).returncode == 0


def _phase_is_current(version_matrix_text: str) -> bool:
    match = re.search(r'^current_phase:\s*"([^"]+)"', version_matrix_text, re.MULTILINE)
    return bool(match and match.group(1) == phase.PHASE_ID)


def _check_public_file(path: Path, errors: list[str]) -> None:
    _require(path.is_file(), f"missing public artifact: {path}", errors)
    if not path.is_file():
        return
    _require(
        path.suffix.lower() not in FORBIDDEN_PUBLIC_SUFFIXES,
        f"forbidden public suffix: {path}",
        errors,
    )
    text = path.read_text(encoding="utf-8", errors="ignore")
    _require(RAW_ROOT_TOKEN not in text, f"raw root token leaked in {path}", errors)
    _require(
        LOCAL_DOWNLOADS_PATTERN.search(text) is None,
        f"local Downloads path leaked in {path}",
        errors,
    )
    for pattern in SECRET_PATTERNS:
        _require(pattern.search(text) is None, f"secret-like token in {path}", errors)
    if path.suffix.lower() == ".json":
        value = json.loads(text)
        for key in _walk_keys(value):
            _require(
                key not in FORBIDDEN_PUBLIC_KEYS,
                f"forbidden public key {key!r} in {path}",
                errors,
            )


def _validate_public(errors: list[str]) -> dict[str, Any]:
    public_paths = (
        phase.SUMMARY_PATH,
        phase.MANIFEST_PATH,
        phase.LANES_PATH,
        phase.ISSUES_PATH,
        phase.MATRIX_PATH,
        phase.GO_NO_GO_PATH,
        phase.HTML_PATH,
        phase.REPORT_PATH,
        phase.TEST_RESULTS_PATH,
        phase.RISK_REGISTER_PATH,
        phase.ROLLBACK_PATH,
        phase.METADATA_SUMMARY_PATH,
        phase.METADATA_MANIFEST_PATH,
        phase.METADATA_LANES_PATH,
        phase.METADATA_ISSUES_PATH,
        phase.METADATA_MATRIX_PATH,
        phase.METADATA_GO_NO_GO_PATH,
    )
    for path in public_paths:
        _check_public_file(path, errors)

    summary = _read_json(phase.SUMMARY_PATH)
    manifest = _read_json(phase.MANIFEST_PATH)
    lanes_wrapper = _read_json(phase.LANES_PATH)
    issues_wrapper = _read_json(phase.ISSUES_PATH)
    matrix = _read_json(phase.MATRIX_PATH)
    go_no_go = _read_json(phase.GO_NO_GO_PATH)
    _require(summary == _read_json(phase.METADATA_SUMMARY_PATH), "summary mirror drift", errors)
    _require(manifest == _read_json(phase.METADATA_MANIFEST_PATH), "manifest mirror drift", errors)
    _require(lanes_wrapper == _read_json(phase.METADATA_LANES_PATH), "lane mirror drift", errors)
    _require(issues_wrapper == _read_json(phase.METADATA_ISSUES_PATH), "issue mirror drift", errors)
    _require(matrix == _read_json(phase.METADATA_MATRIX_PATH), "matrix mirror drift", errors)
    _require(go_no_go == _read_json(phase.METADATA_GO_NO_GO_PATH), "go/no-go mirror drift", errors)
    _require(manifest.get("summary") == summary, "manifest summary drift", errors)
    _require(manifest.get("source_lane_status") == lanes_wrapper.get("lanes"), "lane wrapper drift", errors)
    _require(manifest.get("issue_definitions") == issues_wrapper.get("issues"), "issue wrapper drift", errors)
    _require(manifest.get("acceptance_matrix") == matrix, "manifest matrix drift", errors)

    expected = {
        "project_id": "KMFA",
        "stage_id": "S13",
        "phase_id": phase.PHASE_ID,
        "roadmap_phase_id": "S13-P2",
        "task_id": phase.TASK_ID,
        "acceptance_id": phase.ACCEPTANCE_ID,
        "version": phase.VERSION,
        "status": phase.STATUS,
        "decision": "NO_GO",
        "s13_p1_dependency_validated": True,
        "source_lane_count": 5,
        "structure_connected_lane_count": 5,
        "private_raw_parseable_lane_count": 3,
        "row_level_binding_proven_lane_count": 0,
        "required_issue_type_count": 4,
        "issue_definition_count": 4,
        "identified_business_item_count": 0,
        "priority_review_definition_count": 4,
        "actionable_collection_priority_item_count": 0,
        "responsibility_role_definition_count": 4,
        "assigned_responsibility_item_count": 0,
        "workbench_html_count": 1,
        "open_final_difference_accepted_count": 3,
        "nonzero_delta_reconciliation_count": 9,
        "zero_delta_reconciliation_count": 2,
        "incomplete_reconciliation_count": 1,
        "current_data_quality_grade": "Q4",
        "current_report_grade": "D",
        "formal_report_count": 0,
        "business_decision_basis_count": 0,
        "raw_source_file_count": 5,
        "wps_private_container_count": 2,
        "archive_workbook_member_count": 26,
        "openable_archive_workbook_member_count": 25,
        "archive_pdf_member_count": 8,
        "openable_archive_pdf_member_count": 8,
        "private_difference_item_count": 4,
        "private_workbook_structure_profile_performed": True,
        "raw_snapshot_exact_match": True,
        "raw_cross_phase_snapshot_exact_match": True,
        "browser_status": "PASS",
        "browser_viewport_check_count": 2,
        "issue_interaction_check_count": 4,
        "dependency_link_http_check_count": 3,
        "dependency_navigation_check_count": 3,
        "console_error_count": 0,
        "horizontal_overflow_count": 0,
        "s13_p3_performed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
    }
    for key, value in expected.items():
        _require(summary.get(key) == value, f"summary {key} mismatch", errors)
    _require(
        "pending_reconciliation_count" not in summary,
        "historical pending count leaked into current summary",
        errors,
    )

    lanes = manifest.get("source_lane_status", [])
    _require(len(lanes) == 5, "source lane count mismatch", errors)
    _require(
        {row.get("lane_id") for row in lanes} == {row["lane_id"] for row in phase.LANE_SPECS},
        "source lane IDs mismatch",
        errors,
    )
    _require(sum(row.get("private_raw_parseable") is True for row in lanes) == 3, "parseable lane count mismatch", errors)
    for lane in lanes:
        _require(lane.get("structure_connected") is True, "lane structure not connected", errors)
        _require(lane.get("row_level_binding_proven") is False, "lane row binding improperly claimed", errors)
        for key in (
            "contains_source_identity",
            "contains_field_plaintext",
            "contains_business_amounts",
            "business_priority_allowed",
            "responsibility_assignment_allowed",
            "business_decision_basis_allowed",
        ):
            _require(lane.get(key) is False, f"lane {key} must be false", errors)

    issues = manifest.get("issue_definitions", [])
    _require(len(issues) == 4, "issue definition count mismatch", errors)
    _require(
        {row.get("issue_type") for row in issues} == {row["issue_type"] for row in phase.ISSUE_SPECS},
        "issue type IDs mismatch",
        errors,
    )
    for issue in issues:
        _require(
            issue.get("identification_status") == "definition_locked_row_level_evidence_unproven",
            "issue identification status mismatch",
            errors,
        )
        _require(issue.get("identified_item_count") == 0, "issue item count mismatch", errors)
        _require(
            issue.get("priority_status") == "method_only_not_business_priority",
            "issue priority status mismatch",
            errors,
        )
        _require(
            issue.get("responsibility_status") == "role_definition_only_unassigned",
            "issue responsibility status mismatch",
            errors,
        )
        for key in (
            "business_priority_allowed",
            "responsibility_assignment_allowed",
            "collection_action_allowed",
            "legal_collection_decision_allowed",
            "contains_source_identity",
            "contains_field_plaintext",
            "contains_business_amounts",
        ):
            _require(issue.get(key) is False, f"issue {key} must be false", errors)

    _require(manifest.get("quality_gate") == phase._quality_gate(), "quality gate drift", errors)
    _require(manifest.get("phase_boundaries") == phase._phase_boundaries(), "phase boundary drift", errors)
    _require(manifest.get("public_repo_safety") == phase._public_repo_safety(), "public safety drift", errors)
    raw_boundary = manifest.get("raw_boundary", {})
    for key in (
        "raw_read_authorized",
        "raw_snapshot_validation_performed",
        "private_readonly_probe_performed",
        "private_workbook_structure_profile_performed",
        "private_difference_report_generated",
    ):
        _require(raw_boundary.get(key) is True, f"raw boundary {key} must be true", errors)
    for key in (
        "raw_write_performed",
        "raw_delete_performed",
        "raw_move_performed",
        "raw_rename_performed",
        "raw_overwrite_performed",
        "raw_mutation_performed",
    ):
        _require(raw_boundary.get(key) is False, f"raw boundary {key} must be false", errors)

    _require(matrix.get("check_count") == 26, "matrix check count mismatch", errors)
    _require(matrix.get("check_pass_count") == 26, "matrix pass count mismatch", errors)
    _require(matrix.get("check_fail_count") == 0, "matrix contains failures", errors)
    _require(all(row.get("passed") is True for row in matrix.get("checks", [])), "matrix row failed", errors)
    expected_go_no_go = {
        "decision": "NO_GO",
        "method_definition_allowed": True,
        "business_priority_allowed": False,
        "responsibility_assignment_allowed": False,
        "collection_action_allowed": False,
        "formal_report_allowed": False,
        "business_decision_basis_allowed": False,
        "s13_p3_performed": False,
        "stage13_review_performed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
    }
    for key, value in expected_go_no_go.items():
        _require(go_no_go.get(key) == value, f"go/no-go {key} mismatch", errors)

    browser = manifest.get("browser_review", {})
    browser_expected = {
        "status": "PASS",
        "baseline_file_count": 6,
        "baseline_control_row_count": 54,
        "baseline_pass_count": 54,
        "baseline_warn_count": 0,
        "baseline_fail_count": 0,
        "current_page_count": 1,
        "current_warn_count": 0,
        "current_fail_count": 0,
        "viewport_check_count": 2,
        "issue_interaction_check_count": 4,
        "dependency_link_http_check_count": 3,
        "dependency_navigation_check_count": 3,
        "console_error_count": 0,
        "horizontal_overflow_count": 0,
    }
    for key, value in browser_expected.items():
        _require(browser.get(key) == value, f"browser summary {key} mismatch", errors)
    _require(browser.get("current_control_row_count", 0) > 0, "current audit row count missing", errors)
    _require(
        browser.get("current_pass_count") == browser.get("current_control_row_count"),
        "current audit pass count mismatch",
        errors,
    )

    for key in (
        "s13_p1_dependency_validated",
        "historical_s13_p2_policy_fixture_validated",
        "historical_pending_twelve_quarantined",
        "historical_static_priority_and_responsibility_quarantined",
    ):
        _require(manifest.get(key) is True, f"manifest {key} must be true", errors)
    _require(
        manifest.get("historical_s13_p2_dynamic_state_is_authoritative") is False,
        "historical S13-P2 state became authoritative",
        errors,
    )
    _require(manifest.get("next_phase") == "S13-P3", "next phase drift", errors)
    return manifest


def _validate_html(errors: list[str]) -> None:
    text = phase.HTML_PATH.read_text(encoding="utf-8")
    for token in (
        "回款与应收账龄工作台",
        "Q4 / D",
        "NO_GO",
        "5 / 5",
        "3 / 5",
        "0 / 5",
        "0 项已证明",
        "不是业务催收优先级",
    ):
        _require(token in text, f"HTML token missing: {token}", errors)
    _require(text.count("data-issue-button=") == 4, "HTML issue button count mismatch", errors)
    _require(text.count("data-issue-panel=") == 4, "HTML issue panel count mismatch", errors)
    _require(text.count("data-report-link=") == 3, "HTML report link count mismatch", errors)
    for href in (phase.WEEKLY_HREF, phase.MONTHLY_HREF, phase.CROSS_TABLE_HREF):
        _require(href in text, f"HTML dependency href missing: {href}", errors)
        _require((phase.HTML_PATH.parent / href).resolve().is_file(), f"HTML dependency target missing: {href}", errors)
    _require("gradient(" not in text, "gradient surface found", errors)
    _require("pending_reconciliation_count" not in text, "historical pending leaked", errors)
    for marker in PUBLIC_BUSINESS_AMOUNT_MARKERS:
        _require(marker not in text, f"business amount marker leaked in HTML: {marker}", errors)


def _validate_dependencies(errors: list[str]) -> None:
    try:
        dependency = validate_v014_s13_p1_post_remediation_financial_operating_report(
            require_private_evidence=True,
            require_browser_evidence=True,
            require_final_evidence=True,
        )
    except Exception as exc:
        errors.append(f"current S13-P1 dependency failed: {exc}")
        return
    summary = dependency.get("summary", {})
    expected = {
        "current_data_quality_grade": "Q4",
        "current_report_grade": "D",
        "decision": "NO_GO",
        "open_final_difference_accepted_count": 3,
        "nonzero_delta_reconciliation_count": 9,
        "zero_delta_reconciliation_count": 2,
        "incomplete_reconciliation_count": 1,
        "raw_source_file_count": 5,
        "s13_p2_performed": False,
    }
    for key, value in expected.items():
        _require(summary.get(key) == value, f"S13-P1 dependency {key} mismatch", errors)
    try:
        current_manifest = _read_json(phase.MANIFEST_PATH)
        rebuilt_lanes = phase._build_source_lanes({"openable_archive_workbook_member_count": 2})
        rebuilt_issues = phase._build_issue_definitions()
        _require(current_manifest.get("source_lane_status") == rebuilt_lanes, "current source lanes drift", errors)
        _require(current_manifest.get("issue_definitions") == rebuilt_issues, "current issue definitions drift", errors)
    except Exception as exc:
        errors.append(f"current public-safe S13-P2 dependency build failed: {exc}")


def _validate_governance(errors: list[str]) -> None:
    events = [
        row for row in _read_jsonl(phase.DEVELOPMENT_EVENTS_PATH) if row.get("phase_id") == phase.PHASE_ID
    ]
    statuses = [
        row for row in _read_jsonl(phase.STAGE_STATUS_PATH) if row.get("phase_id") == phase.PHASE_ID
    ]
    tasks = [
        row for row in _read_jsonl(phase.TASK_STATUS_PATH) if row.get("phase_id") == phase.PHASE_ID
    ]
    _require(len(events) == 1, "development event missing or duplicated", errors)
    _require(len(statuses) == 1, "stage status missing or duplicated", errors)
    _require(len(tasks) == 1, "task status missing or duplicated", errors)
    if events:
        _require(events[0].get("status") == phase.STATUS, "development status mismatch", errors)
        _require(events[0].get("github_upload_performed") is False, "development upload flag mismatch", errors)
    if statuses:
        _require(statuses[0].get("status") == phase.STATUS, "stage status mismatch", errors)
        _require(statuses[0].get("derived_percent") == "66.67", "stage progress mismatch", errors)
    if tasks:
        _require(tasks[0].get("acceptance_id") == phase.ACCEPTANCE_ID, "task acceptance mismatch", errors)
        _require(tasks[0].get("completed_task_units") == 3, "task completion mismatch", errors)

    formula_path = Path("KMFA/docs/governance/formula_registry.yaml")
    formula_text = formula_path.read_text(encoding="utf-8")
    _require(phase.FORMULA_ID in formula_text, "formula record missing", errors)
    for token in (
        "source_lane_count == 5",
        "structure_connected_lane_count == 5",
        "private_raw_parseable_lane_count == 3",
        "row_level_binding_proven_lane_count == 0",
        "issue_definition_count == 4",
        "identified_business_item_count == 0",
        "actionable_collection_priority_item_count == 0",
        "assigned_responsibility_item_count == 0",
        "current_grade == D",
        "decision == NO_GO",
    ):
        _require(token in formula_text, f"formula control missing: {token}", errors)

    for path in (
        Path("KMFA/docs/governance/model_registry.yaml"),
        Path("KMFA/metadata/model_registry.yaml"),
    ):
        text = path.read_text(encoding="utf-8")
        _require(phase.MODEL_REGISTRY_KEY in text, f"model registry key missing: {path}", errors)
        _require(phase.FORMULA_ID in text, f"model formula ref missing: {path}", errors)
        for parameter_id in phase.PARAMETER_IDS:
            _require(parameter_id in text, f"model parameter ref missing: {path}:{parameter_id}", errors)

    with Path("KMFA/docs/governance/parameter_registry.csv").open(
        encoding="utf-8", newline=""
    ) as handle:
        parameters = {row["parameter_id"]: row for row in csv.DictReader(handle)}
    expected_parameter_values = {
        "PARAM-KMFA-1739": "5;5;3;0;4;4;0;4;0;4;0;2;4;5;Q4;D;NO_GO",
        "PARAM-KMFA-1740": "6;54;54;0;0;1;2;4;3;3;0;0",
        "PARAM-KMFA-1741": "true;true;true;true;true;true;false;false;false;false;false;false;NO_GO",
        "PARAM-KMFA-1742": "true;true;true;false;false;false;false;false;false;false;false;false;false;NO_GO",
    }
    for parameter_id, expected_value in expected_parameter_values.items():
        row = parameters.get(parameter_id, {})
        for field in ("default_value", "initial_or_prior_value", "active_value", "extracted_value"):
            _require(row.get(field) == expected_value, f"parameter drift: {parameter_id}:{field}", errors)

    version_matrix_path = Path("KMFA/docs/governance/VERSION_MATRIX.yaml")
    version_matrix = version_matrix_path.read_text(encoding="utf-8")
    _require(phase.MODEL_REGISTRY_KEY in version_matrix, "VERSION_MATRIX model missing", errors)
    _require(phase.VERSION in version_matrix, "VERSION_MATRIX version missing", errors)
    if _phase_is_current(version_matrix):
        _require(Path("KMFA/VERSION").read_text(encoding="utf-8").strip() == phase.VERSION, "VERSION drift", errors)
        handoff = Path("KMFA/HANDOFF.md").read_text(encoding="utf-8")
        _require(f"phase: `{phase.PHASE_ID}`" in handoff, "HANDOFF current phase drift", errors)
        _require("下一步只能执行 S13-P3" in handoff, "HANDOFF next phase boundary missing", errors)
        _require("不得执行 GitHub upload" in handoff, "HANDOFF upload boundary missing", errors)
        agents = Path("KMFA/AGENTS.md").read_text(encoding="utf-8")
        _require("S13-P2" in agents and "S13-P3" in agents, "AGENTS phase scope drift", errors)

    traceability = Path("KMFA/docs/governance/TRACEABILITY_MATRIX.csv").read_text(encoding="utf-8")
    delivery = Path("KMFA/docs/governance/delivery_tasks.yaml").read_text(encoding="utf-8")
    assurance = Path("KMFA/docs/governance/ASSURANCE_STATUS.yaml").read_text(encoding="utf-8")
    _require(phase.TASK_ID in traceability and phase.ACCEPTANCE_ID in traceability, "traceability record missing", errors)
    _require(phase.TASK_ID in delivery and phase.ACCEPTANCE_ID in delivery, "delivery task missing", errors)
    _require(phase.FORMULA_ID in assurance, "assurance formula ref missing", errors)
    for parameter_id in phase.PARAMETER_IDS:
        _require(parameter_id in assurance, f"assurance parameter ref missing: {parameter_id}", errors)

    for path, token in (
        (Path("KMFA/CHANGELOG.md"), phase.VERSION),
        (Path("KMFA/docs/governance/DEVELOPMENT_LEDGER.md"), phase.PHASE_ID),
        (Path("KMFA/docs/governance/MODEL_SPEC.md"), phase.FORMULA_ID),
        (Path("KMFA/功能清单.md"), "v0.1.4 S13-P2 修补后回款与应收账龄"),
        (Path("KMFA/开发记录.md"), phase.TASK_ID),
        (Path("KMFA/模型参数文件.md"), phase.FORMULA_ID),
    ):
        _require(token in path.read_text(encoding="utf-8"), f"governance token missing: {path}", errors)


def _read_audit(path: Path, errors: list[str], expected_files: int, expected_rows: int | None = None) -> None:
    _require(path.is_file(), f"browser audit missing: {path}", errors)
    if not path.is_file():
        return
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if expected_rows is not None:
        _require(len(rows) == expected_rows, f"browser audit row count mismatch: {path}", errors)
    else:
        _require(len(rows) > 0, f"browser audit is empty: {path}", errors)
    _require(len({row.get("file") for row in rows}) == expected_files, f"browser audit file count mismatch: {path}", errors)
    _require(sum(row.get("status") == "FAIL" for row in rows) == 0, f"browser audit failure: {path}", errors)
    _require(sum(row.get("status") == "WARN" for row in rows) == 0, f"browser audit warning: {path}", errors)


def _png_dimensions(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValidationError(f"invalid PNG: {path}")
    return struct.unpack(">II", data[16:24])


def _validate_private(errors: list[str], require_browser_evidence: bool) -> None:
    private_paths = (
        phase.PRIVATE_RAW_BEFORE_PATH,
        phase.PRIVATE_RAW_AFTER_PATH,
        phase.PRIVATE_SOURCE_PROBE_PATH,
        phase.PRIVATE_WORKBOOK_PROFILE_PATH,
        phase.PRIVATE_ALIGNMENT_PATH,
        phase.PRIVATE_DIFFERENCE_REPORT_PATH,
    )
    for path in private_paths:
        _require(path.is_file(), f"private evidence missing: {path}", errors)
        _require(_git_check_ignore(path), f"private evidence not ignored: {path}", errors)
        _require(not _git_tracked(path), f"private evidence tracked: {path}", errors)
    if all(path.is_file() for path in private_paths):
        before = _read_json(phase.PRIVATE_RAW_BEFORE_PATH)
        after = _read_json(phase.PRIVATE_RAW_AFTER_PATH)
        prior = _read_json(phase.s13_p1.PRIVATE_RAW_AFTER_PATH)
        current = phase.s13_p1.s12_review.p1.s11_project._raw_snapshot(
            "validate_v014_s13_p2_post_remediation_collection_receivable_aging"
        )
        normalize = phase.s13_p1.s12_review.p1.s11_project._normalize_raw
        _require(normalize(before) == normalize(after), "raw before/after mismatch", errors)
        _require(normalize(before) == normalize(prior), "raw cross-S13-P1 mismatch", errors)
        _require(normalize(after) == normalize(current), "raw current mismatch", errors)
        _require(before.get("file_count") == 5, "raw file count mismatch", errors)

        probe = _read_json(phase.PRIVATE_SOURCE_PROBE_PATH)
        fresh_probe = phase._probe_raw_sources(Path(before["raw_root"]))
        _require(probe == fresh_probe, "private raw source probe drift", errors)
        expected_probe = {
            "classification": "PRIVATE_RUNTIME_ONLY",
            "raw_source_file_count": 5,
            "wps_private_container_count": 2,
            "archive_workbook_member_count": 26,
            "openable_archive_workbook_member_count": 25,
            "archive_pdf_member_count": 8,
            "openable_archive_pdf_member_count": 8,
            "mutation_performed": False,
            "public_commit_allowed": False,
        }
        for key, value in expected_probe.items():
            _require(probe.get(key) == value, f"private probe {key} mismatch", errors)
        _require(len(probe.get("private_differences", [])) == 4, "private difference count mismatch", errors)

        profile = _read_json(phase.PRIVATE_WORKBOOK_PROFILE_PATH)
        raw_snapshot_hash = hashlib.sha256(
            json.dumps(
                normalize(before),
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        expected_profile = {
            "classification": "PRIVATE_RUNTIME_ONLY",
            "raw_snapshot_hash": raw_snapshot_hash,
            "raw_source_file_count": 5,
            "workbook_candidate_count": 26,
            "openable_workbook_count": 25,
            "candidate_signal_is_authoritative_business_item": False,
            "row_level_binding_proven": False,
            "mutation_performed": False,
            "public_commit_allowed": False,
        }
        for key, value in expected_profile.items():
            _require(profile.get(key) == value, f"private workbook profile {key} mismatch", errors)
        _require(
            set(profile.get("lane_document_counts", {}))
            == {row["lane_id"] for row in phase.LANE_SPECS},
            "private profile lane coverage mismatch",
            errors,
        )
        _require(
            all(value > 0 for value in profile.get("lane_document_counts", {}).values()),
            "private profile lane candidate missing",
            errors,
        )
        _require(
            len(profile.get("common_key_classes_across_all_lanes", [])) == 6,
            "private profile common key-class count mismatch",
            errors,
        )
        _require(
            profile.get("private_candidate_signal_count", 0) > 0,
            "private profile candidate signal missing",
            errors,
        )

        alignment = _read_json(phase.PRIVATE_ALIGNMENT_PATH)
        expected_alignment = {
            "classification": "PRIVATE_RUNTIME_ONLY",
            "raw_source_file_count": 5,
            "source_lane_count": 5,
            "structure_connected_lane_count": 5,
            "private_raw_parseable_lane_count": 3,
            "row_level_binding_proven_lane_count": 0,
            "identified_business_item_count": 0,
            "actionable_collection_priority_item_count": 0,
            "assigned_responsibility_item_count": 0,
            "private_difference_item_count": 4,
            "private_workbook_structure_profile_performed": True,
            "private_workbook_candidate_count": 26,
            "private_openable_workbook_count": 25,
            "private_common_key_class_count": 6,
            "private_candidate_signal_is_authoritative_business_item": False,
            "raw_snapshot_exact_match": True,
            "raw_cross_phase_snapshot_exact_match": True,
            "business_value_comparison_performed": False,
            "business_value_comparison_blocked_by_unproven_row_binding": True,
            "difference_report_required_for_this_phase": True,
            "final_goal_difference_report_required_if_unresolved": True,
        }
        for key, value in expected_alignment.items():
            _require(alignment.get(key) == value, f"private alignment {key} mismatch", errors)
        private_report = phase.PRIVATE_DIFFERENCE_REPORT_PATH.read_text(encoding="utf-8")
        _require(
            alignment.get("private_candidate_signal_count")
            == profile.get("private_candidate_signal_count"),
            "private candidate signal count drift",
            errors,
        )
        for token in (
            "WPS 私密复合文档",
            "共享行级主键",
            "跨来源期间口径",
            "仅候选，不是已识别业务事项",
            "全中文最终差异报告",
        ):
            _require(token in private_report, f"private difference report token missing: {token}", errors)

    if not require_browser_evidence:
        return
    browser_paths = (
        phase.PRIVATE_BROWSER_PATH,
        phase.PRIVATE_BASELINE_AUDIT_PATH,
        phase.PRIVATE_CURRENT_AUDIT_PATH,
    )
    for path in browser_paths:
        _require(path.is_file(), f"browser evidence missing: {path}", errors)
        _require(_git_check_ignore(path), f"browser evidence not ignored: {path}", errors)
        _require(not _git_tracked(path), f"browser evidence tracked: {path}", errors)
    _read_audit(phase.PRIVATE_BASELINE_AUDIT_PATH, errors, 6, 54)
    _read_audit(phase.PRIVATE_CURRENT_AUDIT_PATH, errors, 1)
    if phase.PRIVATE_BROWSER_PATH.is_file():
        browser = _read_json(phase.PRIVATE_BROWSER_PATH)
        _require(browser.get("status") == "PASS", "browser evidence status mismatch", errors)
        expected_counts = {
            "viewport_checks": 2,
            "issue_interaction_checks": 4,
            "dependency_link_http_checks": 3,
            "dependency_navigation_checks": 3,
        }
        for key, count in expected_counts.items():
            _require(len(browser.get(key, [])) == count, f"browser {key} count mismatch", errors)
        for key in (
            "issue_interaction_checks",
            "dependency_link_http_checks",
            "dependency_navigation_checks",
        ):
            _require(all(row.get("passed") is True for row in browser.get(key, [])), f"browser {key} failed", errors)
        _require(
            all(
                row.get("workbench_visible") is True
                and row.get("d_no_go_visible") is True
                and row.get("zero_business_items_visible") is True
                and row.get("console_error_count") == 0
                and row.get("no_horizontal_overflow") is True
                for row in browser.get("viewport_checks", [])
            ),
            "browser viewport safety failed",
            errors,
        )
    for mode, width in (("desktop", 1440), ("mobile", 390)):
        path = phase.PRIVATE_SCREENSHOT_DIR / f"workbench_{mode}.png"
        _require(path.is_file(), f"browser screenshot missing: {path}", errors)
        _require(_git_check_ignore(path), f"browser screenshot not ignored: {path}", errors)
        _require(not _git_tracked(path), f"browser screenshot tracked: {path}", errors)
        if path.is_file():
            actual_width, height = _png_dimensions(path)
            _require(actual_width == width, f"screenshot width mismatch: {path}", errors)
            _require(height >= 700, f"screenshot height too small: {path}", errors)


@functools.lru_cache(maxsize=8)
def validate_v014_s13_p2_post_remediation_collection_receivable_aging(
    *,
    require_private_evidence: bool = False,
    require_browser_evidence: bool = False,
    require_final_evidence: bool = False,
) -> dict[str, Any]:
    errors: list[str] = []
    manifest = _validate_public(errors)
    _validate_html(errors)
    _validate_dependencies(errors)
    _validate_governance(errors)
    if require_private_evidence:
        _validate_private(errors, require_browser_evidence)
    elif require_browser_evidence:
        errors.append("browser evidence requires private evidence")
    if require_final_evidence:
        validation = manifest.get("validation_summary", {})
        _require(validation.get("final_validation_recorded") is True, "final validation not recorded", errors)
        for key in (
            "focused_test",
            "strict_validator",
            "browser_desktop_mobile",
            "raw_alignment",
            "governance_and_safety_scans",
        ):
            _require(validation.get(key) == "PASS", f"final validation status mismatch: {key}", errors)
    if errors:
        raise ValidationError("; ".join(errors))
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-private-evidence", action="store_true")
    parser.add_argument("--require-browser-evidence", action="store_true")
    parser.add_argument("--require-final-evidence", action="store_true")
    args = parser.parse_args()
    try:
        manifest = validate_v014_s13_p2_post_remediation_collection_receivable_aging(
            require_private_evidence=args.require_private_evidence,
            require_browser_evidence=args.require_browser_evidence,
            require_final_evidence=args.require_final_evidence,
        )
    except (ValidationError, ValueError, KeyError, RuntimeError) as exc:
        print(f"FAIL: {exc}")
        return 1
    summary = manifest["summary"]
    print(
        "PASS: S13-P2 post-remediation collection receivable aging "
        f"lanes={summary['source_lane_count']} parseable={summary['private_raw_parseable_lane_count']} "
        f"bound={summary['row_level_binding_proven_lane_count']} "
        f"items={summary['identified_business_item_count']} decision={summary['decision']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
