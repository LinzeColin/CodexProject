#!/usr/bin/env python3
"""Validate the current KMFA v0.1.4 S11-P3 public-safe project cost page."""

from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
from pathlib import Path
from typing import Any

from KMFA.tools import v014_s11_p3_post_remediation_project_cost_page as phase
from KMFA.tools.project_cost_page_runtime import (
    REQUIRED_COST_CATEGORIES,
    REQUIRED_PROJECT_TABLE_COLUMNS,
)


FORBIDDEN_PUBLIC_SUFFIXES = {".zip", ".xls", ".xlsx", ".pdf", ".db", ".sqlite", ".sqlite3"}
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
    "original_filename",
    "file_hash",
    "field_key",
    "field_label",
    "source_header_text",
    "project_name_plaintext",
    "customer_name_plaintext",
    "account_number",
}
RAW_ROOT_TOKEN = "KMFA" + "_MetaData"
LOCAL_DOWNLOADS_PATTERN = re.compile(r"/Users/[^\s\"'`]+/Downloads/[^\s\"'`]+")
BUSINESS_AMOUNT_PATTERN = re.compile(r"(?:¥|￥|\bCNY\b|\bRMB\b|\d{1,3}(?:,\d{3})+\.\d{2})")
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
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValidationError(f"{path} must contain object rows")
            rows.append(value)
    return rows


def _walk_keys(value: Any):
    if isinstance(value, dict):
        for key, child in value.items():
            yield key
            yield from _walk_keys(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_keys(child)


def _check_public_file(path: Path, errors: list[str]) -> None:
    _require(path.is_file(), f"missing public artifact: {path}", errors)
    if not path.is_file():
        return
    _require(path.suffix.lower() not in FORBIDDEN_PUBLIC_SUFFIXES, f"forbidden public suffix: {path}", errors)
    text = path.read_text(encoding="utf-8", errors="ignore")
    _require(RAW_ROOT_TOKEN not in text, f"raw root token leaked in {path}", errors)
    _require(LOCAL_DOWNLOADS_PATTERN.search(text) is None, f"local Downloads path leaked in {path}", errors)
    _require(BUSINESS_AMOUNT_PATTERN.search(text) is None, f"business amount pattern in {path}", errors)
    for pattern in SECRET_PATTERNS:
        _require(pattern.search(text) is None, f"secret-like token in {path}", errors)
    if path.suffix.lower() == ".json":
        for key in _walk_keys(json.loads(text)):
            _require(key not in FORBIDDEN_PUBLIC_KEYS, f"forbidden public key {key!r} in {path}", errors)


def _git_check_ignore(path: Path) -> bool:
    return subprocess.run(["git", "check-ignore", "-q", path.as_posix()], check=False).returncode == 0


def _git_tracked(path: Path) -> bool:
    return (
        subprocess.run(
            ["git", "ls-files", "--error-unmatch", path.as_posix()],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        ).returncode
        == 0
    )


def _phase_is_current(version_matrix_text: str) -> bool:
    match = re.search(r'^current_phase:\s*"([^"]+)"', version_matrix_text, re.MULTILINE)
    return bool(match and match.group(1) == phase.PHASE_ID)


def _validate_public(errors: list[str]) -> dict[str, Any]:
    public_paths = (
        phase.SUMMARY_PATH,
        phase.MANIFEST_PATH,
        phase.PROJECTS_PATH,
        phase.GO_NO_GO_PATH,
        phase.HTML_PATH,
        phase.COMPLETION_PATH,
        phase.READ_ME_PATH,
        phase.TEST_RESULTS_PATH,
        phase.RISK_REGISTER_PATH,
        phase.ROLLBACK_PATH,
        phase.METADATA_SUMMARY_PATH,
        phase.METADATA_MANIFEST_PATH,
        phase.METADATA_PROJECTS_PATH,
        phase.METADATA_GO_NO_GO_PATH,
    )
    for path in public_paths:
        _check_public_file(path, errors)

    summary = _read_json(phase.SUMMARY_PATH)
    manifest = _read_json(phase.MANIFEST_PATH)
    projects_document = _read_json(phase.PROJECTS_PATH)
    go_no_go = _read_json(phase.GO_NO_GO_PATH)
    rows = projects_document.get("project_rows", [])

    _require(manifest.get("schema_version") == "kmfa.v014.s11_p3.post_remediation_project_cost_page_manifest.v1", "manifest schema mismatch", errors)
    _require(manifest.get("phase_id") == phase.PHASE_ID, "manifest phase mismatch", errors)
    _require(manifest.get("task_id") == phase.TASK_ID, "manifest task mismatch", errors)
    _require(manifest.get("acceptance_id") == phase.ACCEPTANCE_ID, "manifest acceptance mismatch", errors)
    _require(manifest.get("version") == phase.VERSION, "manifest version mismatch", errors)
    _require(manifest.get("status") == phase.STATUS, "manifest status mismatch", errors)
    _require(manifest.get("summary") == summary, "manifest summary mirror mismatch", errors)
    _require(manifest.get("project_rows") == rows, "manifest project rows mirror mismatch", errors)
    _require(_read_json(phase.METADATA_SUMMARY_PATH) == summary, "metadata summary mirror mismatch", errors)
    _require(_read_json(phase.METADATA_MANIFEST_PATH) == manifest, "metadata manifest mirror mismatch", errors)
    _require(_read_json(phase.METADATA_PROJECTS_PATH) == projects_document, "metadata project mirror mismatch", errors)
    _require(_read_json(phase.METADATA_GO_NO_GO_PATH) == go_no_go, "metadata go/no-go mirror mismatch", errors)

    expected_summary = {
        "stage_id": "S11",
        "roadmap_phase_id": "S11-P3",
        "current_data_quality_grade": "Q4",
        "current_report_grade": "D",
        "decision": "NO_GO",
        "open_final_difference_accepted_count": 3,
        "nonzero_delta_reconciliation_count": 9,
        "zero_delta_reconciliation_count": 2,
        "incomplete_reconciliation_count": 1,
        "hard_block_count": 12,
        "project_row_count": 4,
        "project_list_column_count": 7,
        "cost_category_count": 9,
        "margin_record_count": 4,
        "cost_component_materialization_count": 8,
        "project_specific_attributed_difference_count": 0,
        "project_specific_unknown_allocation_count": 4,
        "current_evidence_label_count": 6,
        "global_pending_item_count": 5,
        "report_section_count": 4,
        "restricted_report_link_count": 1,
        "public_appendix_link_count": 1,
        "linked_artifact_count": 4,
        "raw_source_file_count": 5,
        "formal_report_count": 0,
        "business_decision_basis_allowed_count": 0,
    }
    for key, expected in expected_summary.items():
        _require(summary.get(key) == expected, f"summary {key} mismatch", errors)
    _require(summary.get("project_list_columns") == list(REQUIRED_PROJECT_TABLE_COLUMNS), "project columns mismatch", errors)
    _require(summary.get("cost_categories") == list(REQUIRED_COST_CATEGORIES), "cost categories mismatch", errors)
    for key in (
        "historical_pending_twelve_recomputed",
        "report_preview_direct_view_allowed",
        "raw_snapshot_exact_match",
        "raw_cross_phase_snapshot_exact_match",
        "km_brand_mark_present",
        "blue_gray_surface_dominant",
        "all_chinese_visible_copy",
    ):
        _require(summary.get(key) is True, f"summary {key} must be true", errors)
    for key in ("contains_stale_pending_twelve", "contains_b_grade", "historical_dynamic_state_reused", "single_k_brand_mark_present"):
        _require(summary.get(key) is False, f"summary {key} must be false", errors)
    _require("pending_reconciliation_count" not in summary, "stale pending field leaked into summary", errors)

    _require(len(rows) == 4, "project row count mismatch", errors)
    for index, row in enumerate(rows, 1):
        _require(row.get("row_id") == f"PCP-{index:03d}", f"row {index} id mismatch", errors)
        _require(row.get("project_display_ref") == f"项目分组 {index:03d}", f"row {index} alias mismatch", errors)
        _require(row.get("project_specific_allocation_status") == "not_publicly_attributed", f"row {index} allocation status mismatch", errors)
        _require(row.get("project_specific_difference_count") is None, f"row {index} difference count must be null", errors)
        _require(row.get("global_state_ref") == {
            "open_final_difference_accepted_count": 3,
            "nonzero_delta_reconciliation_count": 9,
            "zero_delta_reconciliation_count": 2,
            "incomplete_reconciliation_count": 1,
        }, f"row {index} global state mismatch", errors)
        _require(len(row.get("source_evidence_labels", [])) == 6, f"row {index} evidence labels mismatch", errors)
        _require(len(row.get("source_evidence_refs", [])) == 6, f"row {index} evidence refs mismatch", errors)
        _require(len(row.get("pending_items", [])) == 5, f"row {index} pending items mismatch", errors)
        for key in (
            "contains_raw_business_values",
            "contains_private_file_references",
            "raw_layer_write_allowed",
            "persistent_business_write_allowed",
            "formal_report_allowed",
            "business_decision_basis_allowed",
            "quality_grade_bypass_allowed",
        ):
            _require(row.get(key) is False, f"row {index} {key} must be false", errors)

    interaction = manifest.get("interaction_contract", {})
    expected_interaction = {
        "project_search_enabled": True,
        "project_detail_click_enabled": True,
        "project_detail_button_count": 4,
        "detail_panel_fields": ["来源证据", "待处理事项", "报告预览"],
        "current_evidence_label_count": 6,
        "global_pending_items_visible": True,
        "project_level_false_attribution_blocked": True,
        "report_section_switch_enabled": True,
        "session_only_control_events": True,
        "persistent_business_write_allowed": False,
        "raw_layer_write_allowed": False,
        "automatic_external_action_allowed": False,
    }
    for key, expected in expected_interaction.items():
        _require(interaction.get(key) == expected, f"interaction {key} mismatch", errors)

    quality = manifest.get("quality_gate", {})
    for key, expected in {
        "current_data_quality_grade": "Q4",
        "current_report_grade": "D",
        "decision": "NO_GO",
        "release_permission": "blocked",
        "project_cost_page_display_allowed": True,
        "restricted_internal_preview_allowed": True,
        "quality_grade_bypass_allowed": False,
        "complete_trusted_report_display_allowed": False,
        "formal_report_allowed": False,
        "business_decision_basis_allowed": False,
        "business_execution_allowed": False,
    }.items():
        _require(quality.get(key) == expected, f"quality gate {key} mismatch", errors)

    boundaries = manifest.get("phase_boundaries", {})
    for key in ("s11_p1_dependency_validated", "s11_p2_dependency_validated", "s11_p3_performed"):
        _require(boundaries.get(key) is True, f"boundary {key} must be true", errors)
    for key in (
        "stage11_review_performed",
        "s12_p1_performed",
        "github_upload_performed",
        "app_reinstall_performed",
        "formal_report_release_performed",
        "business_execution_performed",
        "persistent_business_write_performed",
        "raw_write_performed",
        "raw_delete_performed",
        "raw_move_performed",
        "raw_rename_performed",
        "raw_overwrite_performed",
    ):
        _require(boundaries.get(key) is False, f"boundary {key} must be false", errors)

    _require(go_no_go.get("decision") == "NO_GO", "go/no-go decision mismatch", errors)
    _require(go_no_go.get("project_cost_page_display_allowed") is True, "go/no-go display mismatch", errors)
    _require(go_no_go.get("project_level_difference_attribution_allowed") is False, "go/no-go attribution mismatch", errors)
    return manifest


def _validate_html(errors: list[str]) -> None:
    text = phase.HTML_PATH.read_text(encoding="utf-8")
    required_tokens = (
        "KMFA 项目成本页面",
        "Q4 / D · NO_GO",
        "项目列表",
        "项目成本详情",
        "来源证据",
        "待处理事项",
        "报告预览",
        "项目级归属未公开",
        "不可绕过 D 级或 NO_GO",
        "公开安全边界",
        "function selectProject",
        "function switchReportSection",
        "function openReportPreview",
        "function closeReportPreview",
        "persistent_write:false",
        "raw_layer_write:false",
        "quality_grade_bypass:false",
    )
    for token in required_tokens:
        _require(token in text, f"HTML token missing: {token}", errors)
    _require(len(re.findall(r'<button[^>]+data-project-detail="PCP-\d{3}"', text)) == 4, "HTML project detail button count mismatch", errors)
    _require(len(re.findall(r'<button[^>]+data-project-preview="PCP-\d{3}"', text)) == 4, "HTML project preview button count mismatch", errors)
    _require(len(re.findall(r'<button[^>]+data-report-section="[^"]+"', text)) == 4, "HTML report section button count mismatch", errors)
    _require(len(re.findall(r'<a[^>]+data-linked-artifact', text)) == 4, "HTML linked artifact count mismatch", errors)
    _require(text.count("<iframe") == 1, "HTML iframe count mismatch", errors)
    for forbidden in (
        "pending_reconciliation_count",
        "报告等级 B",
        "private_ref://",
        "source_ref://",
        ".xlsx",
        ".xls",
        ".pdf",
        ".sqlite",
        ".db",
    ):
        _require(forbidden not in text, f"stale/private HTML token: {forbidden}", errors)
    _require("gradient(" not in text, "HTML gradient surface forbidden", errors)


def _validate_dependencies(errors: list[str]) -> None:
    try:
        values = phase._load_dependencies()
    except Exception as exc:
        errors.append(f"current dependency validation failed: {exc}")
        return
    _require(values.get("project_row_count") == 4, "dependency project row count mismatch", errors)
    _require(values.get("historical_pending_reconciliation_count") == 12, "historical pending finding missing", errors)
    _require(values.get("cost_component_materialization_count") == 8, "materialization dependency mismatch", errors)


def _validate_governance(errors: list[str]) -> None:
    version_matrix_text = Path("KMFA/docs/governance/VERSION_MATRIX.yaml").read_text(encoding="utf-8")
    phase_is_current = _phase_is_current(version_matrix_text)
    if phase_is_current:
        _require(Path("KMFA/VERSION").read_text(encoding="utf-8").strip() == phase.VERSION, "VERSION mismatch", errors)
    _require(phase.MODEL_REGISTRY_KEY in version_matrix_text, "VERSION_MATRIX phase profile missing", errors)
    _require(phase.VERSION in version_matrix_text, "VERSION_MATRIX phase version missing", errors)
    events = [row for row in _read_jsonl(phase.DEVELOPMENT_EVENTS_PATH) if row.get("phase_id") == phase.PHASE_ID]
    statuses = [row for row in _read_jsonl(phase.STAGE_STATUS_PATH) if row.get("phase_id") == phase.PHASE_ID]
    tasks = [row for row in _read_jsonl(phase.TASK_STATUS_PATH) if row.get("phase_id") == phase.PHASE_ID]
    _require(len(events) == 1, "development event count mismatch", errors)
    _require(len(statuses) == 1, "stage status count mismatch", errors)
    _require(len(tasks) == 1, "task status count mismatch", errors)
    if events:
        _require(events[0].get("github_upload_performed") is False, "development event upload flag mismatch", errors)
    if statuses:
        _require(statuses[0].get("status") == phase.STATUS, "stage status value mismatch", errors)
    if tasks:
        _require(tasks[0].get("acceptance_id") == phase.ACCEPTANCE_ID, "task acceptance mismatch", errors)

    with Path("KMFA/docs/governance/parameter_registry.csv").open(encoding="utf-8", newline="") as handle:
        parameters = {row["parameter_id"]: row for row in csv.DictReader(handle)}
    for parameter_id in phase.PARAMETER_IDS:
        _require(parameter_id in parameters, f"missing parameter {parameter_id}", errors)
    formula_text = Path("KMFA/docs/governance/formula_registry.yaml").read_text(encoding="utf-8")
    _require(phase.FORMULA_ID in formula_text, "formula registry entry missing", errors)
    for token in (
        "project_row_count == 4",
        "project_specific_attributed_difference_count == 0",
        "current_report_grade == D",
        "decision == NO_GO",
        "quality_grade_bypass_allowed == false",
    ):
        _require(token in formula_text, f"formula token missing: {token}", errors)
    for path in (Path("KMFA/docs/governance/model_registry.yaml"), Path("KMFA/metadata/model_registry.yaml")):
        text = path.read_text(encoding="utf-8")
        _require(phase.MODEL_REGISTRY_KEY in text, f"model registry key missing in {path}", errors)
        _require(phase.FORMULA_ID in text, f"formula ref missing in {path}", errors)
        for parameter_id in phase.PARAMETER_IDS:
            _require(parameter_id in text, f"parameter ref missing in {path}: {parameter_id}", errors)
    traceability_text = Path("KMFA/docs/governance/TRACEABILITY_MATRIX.csv").read_text(encoding="utf-8")
    _require(phase.TASK_ID in traceability_text, "traceability task missing", errors)
    _require(phase.ACCEPTANCE_ID in traceability_text, "traceability acceptance missing", errors)
    delivery_text = Path("KMFA/docs/governance/delivery_tasks.yaml").read_text(encoding="utf-8")
    _require(phase.TASK_ID in delivery_text, "delivery task missing", errors)
    _require(phase.ACCEPTANCE_ID in delivery_text, "delivery acceptance missing", errors)
    for path, token in (
        (Path("KMFA/CHANGELOG.md"), phase.VERSION),
        (Path("KMFA/docs/governance/DEVELOPMENT_LEDGER.md"), phase.PHASE_ID),
        (Path("KMFA/docs/governance/MODEL_SPEC.md"), phase.FORMULA_ID),
        (Path("KMFA/功能清单.md"), "S11-P3 修补后项目成本页面"),
        (Path("KMFA/开发记录.md"), phase.TASK_ID),
        (Path("KMFA/模型参数文件.md"), phase.FORMULA_ID),
    ):
        _require(token in path.read_text(encoding="utf-8"), f"governance token missing in {path}", errors)
    if phase_is_current:
        for path in (
            Path("KMFA/HANDOFF.md"),
            Path("KMFA/docs/governance/STATUS.md"),
            Path("KMFA/docs/governance/OWNER_STATUS.md"),
        ):
            _require(phase.PHASE_ID in path.read_text(encoding="utf-8"), f"current phase token missing in {path}", errors)


def _validate_private(errors: list[str], require_browser_evidence: bool) -> None:
    private_paths = (
        phase.PRIVATE_RAW_BEFORE_PATH,
        phase.PRIVATE_RAW_AFTER_PATH,
        phase.PRIVATE_VALIDATION_REPORT_PATH,
        phase.PRIVATE_BROWSER_PATH,
        phase.PRIVATE_BASELINE_AUDIT_PATH,
        phase.PRIVATE_CURRENT_AUDIT_PATH,
    )
    for path in private_paths:
        _require(path.is_file(), f"private evidence missing: {path}", errors)
        _require(_git_check_ignore(path), f"private evidence not ignored: {path}", errors)
        _require(not _git_tracked(path), f"private evidence tracked: {path}", errors)
    if all(path.is_file() for path in (phase.PRIVATE_RAW_BEFORE_PATH, phase.PRIVATE_RAW_AFTER_PATH, phase.p2.PRIVATE_RAW_AFTER_PATH)):
        before = _read_json(phase.PRIVATE_RAW_BEFORE_PATH)
        after = _read_json(phase.PRIVATE_RAW_AFTER_PATH)
        prior = _read_json(phase.p2.PRIVATE_RAW_AFTER_PATH)
        current = phase._raw_snapshot("validate_v014_s11_p3_post_remediation_project_cost_page")
        normalize = phase._normalize_raw
        _require(normalize(before) == normalize(after), "raw before/after mismatch", errors)
        _require(normalize(before) == normalize(prior), "raw cross-phase mismatch", errors)
        _require(normalize(after) == normalize(current), "raw current mismatch", errors)
        _require(before.get("file_count") == 5, "raw file count mismatch", errors)
    if require_browser_evidence and phase.PRIVATE_BROWSER_PATH.is_file():
        browser = _read_json(phase.PRIVATE_BROWSER_PATH)
        _require(browser.get("status") == "PASS", "private browser status mismatch", errors)
        _require(len(browser.get("viewport_checks", [])) == 2, "private viewport count mismatch", errors)
        _require(len(browser.get("search_checks", [])) == 4, "private search count mismatch", errors)
        _require(len(browser.get("project_detail_checks", [])) == 8, "private detail count mismatch", errors)
        _require(len(browser.get("report_section_checks", [])) == 8, "private section count mismatch", errors)
        _require(len(browser.get("report_preview_open_checks", [])) == 2, "private preview open count mismatch", errors)
        _require(len(browser.get("report_preview_close_checks", [])) == 2, "private preview close count mismatch", errors)
        _require(len(browser.get("keyboard_checks", [])) == 2, "private keyboard count mismatch", errors)
        _require(len(browser.get("linked_artifact_http_checks", [])) == 4, "private linked artifact count mismatch", errors)
        for mode in ("desktop", "mobile"):
            screenshot = phase.PRIVATE_SCREENSHOT_DIR / f"kmfa_project_cost_page_{mode}.png"
            _require(screenshot.is_file(), f"private screenshot missing: {screenshot}", errors)
            _require(_git_check_ignore(screenshot), f"private screenshot not ignored: {screenshot}", errors)


def validate_v014_s11_p3_post_remediation_project_cost_page(
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
        for key in ("focused_tests", "strict_validator", "browser_desktop_mobile", "governance_and_safety_scans"):
            _require(validation.get(key) == "PASS", f"final validation {key} mismatch", errors)
    if errors:
        raise ValidationError("\n".join(errors))
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-private-evidence", action="store_true")
    parser.add_argument("--require-browser-evidence", action="store_true")
    parser.add_argument("--require-final-evidence", action="store_true")
    args = parser.parse_args()
    manifest = validate_v014_s11_p3_post_remediation_project_cost_page(
        require_private_evidence=args.require_private_evidence,
        require_browser_evidence=args.require_browser_evidence,
        require_final_evidence=args.require_final_evidence,
    )
    summary = manifest["summary"]
    print(
        "PASS: S11-P3 post-remediation project cost page "
        f"projects={summary['project_row_count']} unknown={summary['project_specific_unknown_allocation_count']} "
        f"grade={summary['current_report_grade']} decision={summary['decision']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
