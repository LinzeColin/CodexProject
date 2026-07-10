#!/usr/bin/env python3
"""Validate KMFA v0.1.4 S11-P2 current public-safe source check board."""

from __future__ import annotations

import argparse
import csv
import functools
import json
import re
import struct
import subprocess
from pathlib import Path
from typing import Any

from KMFA.tools import v014_s11_p2_post_remediation_source_check_board as phase
from KMFA.tools.source_check_board_runtime import ALLOWED_BOARD_STATUSES, REQUIRED_BOARD_COLUMNS


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
SECRET_PATTERNS = (
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(
        r"(?i)(?:password|passwd|api[_-]?key|access[_-]?token|client[_-]?secret)"
        r"\s*[:=]\s*[\"'][^\"'\r\n]{8,}[\"']"
    ),
)
BUSINESS_AMOUNT_PATTERN = re.compile(r"(?:¥|￥|\bCNY\b|\bRMB\b|\d{1,3}(?:,\d{3})+\.\d{2})")
EXPECTED_STATUS_COUNTS = {"已就绪": 0, "部分/阻塞": 6, "失败/不适用": 1, "已过期": 2, "人工复核": 4}


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
                raise ValidationError(f"{path} must contain objects")
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


def _validate_public(errors: list[str]) -> dict[str, Any]:
    public_paths = (
        phase.SUMMARY_PATH,
        phase.MANIFEST_PATH,
        phase.ROWS_PATH,
        phase.GO_NO_GO_PATH,
        phase.HTML_PATH,
        phase.COMPLETION_PATH,
        phase.READ_ME_PATH,
        phase.TEST_RESULTS_PATH,
        phase.RISK_REGISTER_PATH,
        phase.ROLLBACK_PATH,
        phase.METADATA_SUMMARY_PATH,
        phase.METADATA_MANIFEST_PATH,
        phase.METADATA_ROWS_PATH,
        phase.METADATA_GO_NO_GO_PATH,
    )
    for path in public_paths:
        _check_public_file(path, errors)

    summary = _read_json(phase.SUMMARY_PATH)
    manifest = _read_json(phase.MANIFEST_PATH)
    rows_document = _read_json(phase.ROWS_PATH)
    go_no_go = _read_json(phase.GO_NO_GO_PATH)
    _require(summary == _read_json(phase.METADATA_SUMMARY_PATH), "summary mirror drift", errors)
    _require(manifest == _read_json(phase.METADATA_MANIFEST_PATH), "manifest mirror drift", errors)
    _require(rows_document == _read_json(phase.METADATA_ROWS_PATH), "rows mirror drift", errors)
    _require(go_no_go == _read_json(phase.METADATA_GO_NO_GO_PATH), "go/no-go mirror drift", errors)
    _require(manifest.get("summary") == summary, "manifest summary drift", errors)
    rows = rows_document.get("rows", [])
    _require(manifest.get("source_rows") == rows, "manifest rows drift", errors)

    expected = {
        "project_id": "KMFA",
        "stage_id": "S11",
        "phase_id": phase.PHASE_ID,
        "roadmap_phase_id": "S11-P2",
        "status": phase.STATUS,
        "decision": "NO_GO",
        "current_data_quality_grade": "Q4",
        "current_report_grade": "D",
        "open_final_difference_accepted_count": 3,
        "nonzero_delta_reconciliation_count": 9,
        "zero_delta_reconciliation_count": 2,
        "incomplete_reconciliation_count": 1,
        "hard_block_count": 12,
        "matrix_row_count": 13,
        "required_column_count": 11,
        "allowed_status_count": 5,
        "status_counts": EXPECTED_STATUS_COUNTS,
        "historical_ready_status_recomputed_count": 4,
        "current_status_changed_count": 5,
        "current_ready_row_count": 0,
        "contains_stale_pending_twelve": False,
        "contains_b_grade": False,
        "current_authority_record_count": 45,
        "current_source_adapter_record_count": 17,
        "raw_source_file_count": 5,
        "raw_snapshot_exact_match": True,
        "raw_cross_phase_snapshot_exact_match": True,
        "home_navigation_link_count": 1,
        "visible_feedback_panel_count": 3,
        "formal_report_count": 0,
        "business_decision_basis_allowed_count": 0,
    }
    for key, value in expected.items():
        _require(summary.get(key) == value, f"summary {key} mismatch", errors)
    _require(summary.get("required_columns") == list(REQUIRED_BOARD_COLUMNS), "required columns mismatch", errors)
    _require(summary.get("allowed_statuses") == list(ALLOWED_BOARD_STATUSES), "allowed statuses mismatch", errors)
    for key in (
        "current_source_state_overlay_applied",
        "km_brand_mark_present",
        "blue_gray_surface_dominant",
        "status_badges_only",
        "all_chinese_visible_copy",
    ):
        _require(summary.get(key) is True, f"summary {key} must be true", errors)
    for key in ("historical_dynamic_state_reused", "single_k_brand_mark_present"):
        _require(summary.get(key) is False, f"summary {key} must be false", errors)
    _require(summary.get("large_yellow_surface_count") == 0, "large yellow surface mismatch", errors)

    _require(isinstance(rows, list) and len(rows) == 13, "source row count mismatch", errors)
    expected_first = ["部分/阻塞", "部分/阻塞", "人工复核", "部分/阻塞"]
    _require([row.get("status") for row in rows[:4]] == expected_first, "first four current statuses mismatch", errors)
    _require(sum(row.get("current_status_changed") is True for row in rows) == 5, "changed status count mismatch", errors)
    for index, row in enumerate(rows, 1):
        _require(row.get("row_order") == index, f"row order mismatch: {index}", errors)
        _require(row.get("status") in ALLOWED_BOARD_STATUSES, f"row status invalid: {index}", errors)
        _require(row.get("status_basis") == "current_public_safe_evidence_overlay", f"status basis mismatch: {index}", errors)
        for key in (
            "source_system",
            "business_segment",
            "source_package_ref",
            "entity_ref",
            "bank_or_system_account",
            "account_or_report_ref",
            "frequency",
            "report_impact",
            "handling_rule",
            "next_step",
        ):
            _require(bool(str(row.get(key, "")).strip()), f"row {index} missing {key}", errors)
        for key in (
            "contains_raw_business_values",
            "contains_private_file_references",
            "raw_layer_write_allowed",
            "persistent_status_write_allowed",
            "formal_report_allowed",
            "business_decision_basis_allowed",
        ):
            _require(row.get(key) is False, f"row {index} {key} must be false", errors)

    interaction = manifest.get("interaction_contract", {})
    for key in (
        "search_feedback_enabled",
        "status_filter_enabled",
        "status_click_detail_enabled",
        "session_only_control_events",
    ):
        _require(interaction.get(key) is True, f"interaction {key} must be true", errors)
    _require(interaction.get("detail_panel_fields") == ["影响报告", "处理规则", "下一步"], "detail fields mismatch", errors)
    _require(interaction.get("session_status_preview_action_count") == 5, "preview action count mismatch", errors)
    for key in ("persistent_status_write_allowed", "raw_layer_write_allowed", "automatic_external_action_allowed"):
        _require(interaction.get(key) is False, f"interaction {key} must be false", errors)

    quality = manifest.get("quality_gate", {})
    _require(quality.get("current_data_quality_grade") == "Q4", "quality grade mismatch", errors)
    _require(quality.get("current_report_grade") == "D", "report grade mismatch", errors)
    _require(quality.get("decision") == "NO_GO", "quality decision mismatch", errors)
    _require(quality.get("source_check_board_display_allowed") is True, "board display gate mismatch", errors)
    for key in (
        "complete_trusted_report_display_allowed",
        "formal_report_allowed",
        "business_decision_basis_allowed",
        "business_execution_allowed",
        "persistent_status_write_allowed",
    ):
        _require(quality.get(key) is False, f"quality {key} must be false", errors)

    boundaries = manifest.get("phase_boundaries", {})
    for key in ("s11_p1_dependency_validated", "s11_p2_performed"):
        _require(boundaries.get(key) is True, f"boundary {key} must be true", errors)
    for key in (
        "s11_p3_performed",
        "stage11_review_performed",
        "github_upload_performed",
        "app_reinstall_performed",
        "formal_report_release_performed",
        "business_execution_performed",
        "persistent_status_write_performed",
        "raw_write_performed",
        "raw_delete_performed",
        "raw_move_performed",
        "raw_rename_performed",
        "raw_overwrite_performed",
    ):
        _require(boundaries.get(key) is False, f"boundary {key} must be false", errors)
    _require(go_no_go.get("decision") == "NO_GO", "go/no-go decision mismatch", errors)
    _require(go_no_go.get("source_check_board_display_allowed") is True, "go/no-go display mismatch", errors)
    for key in (
        "persistent_status_write_allowed",
        "formal_report_allowed",
        "business_decision_basis_allowed",
        "s11_p3_performed",
        "stage11_review_performed",
        "github_upload_performed",
    ):
        _require(go_no_go.get(key) is False, f"go/no-go {key} must be false", errors)
    return manifest


def _validate_html(errors: list[str]) -> None:
    text = phase.HTML_PATH.read_text(encoding="utf-8")
    _require(text.startswith("<!doctype html>"), "HTML doctype missing", errors)
    for token in (
        "KMFA 数据源检查板",
        "公开安全状态矩阵",
        "Q4 / D · NO_GO",
        "3 项最终接受未决",
        "9 项非零差异",
        "2 项零差异",
        "1 项比较未完成",
        "影响报告",
        "处理规则",
        "下一步",
        "仅影响当前浏览器会话",
        "不修改原始数据",
        "不写入持久业务状态",
        "source-search",
        "status-filter",
        "reset-filter",
        "filter-feedback",
        "detail-panel",
        "control-event-log",
        "applyFilters",
        "selectRow",
        "previewStatus",
        "browser_session_only",
        "persistent_write:false",
        "raw_layer_write:false",
    ):
        _require(token in text, f"HTML token missing: {token}", errors)
    for column in REQUIRED_BOARD_COLUMNS:
        _require(column in text, f"HTML column missing: {column}", errors)
    for status in ALLOWED_BOARD_STATUSES:
        _require(status in text, f"HTML status missing: {status}", errors)
    for token in ("B级", "12 pending", "pending_reconciliation_count", "reportGrade:'B'", RAW_ROOT_TOKEN):
        _require(token not in text, f"stale/private HTML token: {token}", errors)
    detail_buttons = re.findall(r'<button[^>]+data-status-detail="SCB-\d{3}"', text)
    matrix_rows = re.findall(r'<tr[^>]+data-row-id="SCB-\d{3}"', text)
    _require(len(detail_buttons) == 13, "HTML status detail count mismatch", errors)
    _require(text.count("data-status-preview=") == 5, "HTML preview action count mismatch", errors)
    _require(len(matrix_rows) == 13, "HTML row count mismatch", errors)
    _require('data-count-for="已就绪">0<' in text, "HTML ready count must be zero", errors)
    hrefs = re.findall(r'<a[^>]+href="([^"]+)"', text)
    _require(hrefs == [phase.HOME_HREF], "HTML link allowlist mismatch", errors)
    _require((phase.HTML_PATH.parent / phase.HOME_HREF).resolve().is_file(), "current home target missing", errors)
    _require("gradient(" not in text, "HTML gradient surface forbidden", errors)


def _validate_dependencies(errors: list[str]) -> None:
    home = phase._load_current_home_dependency()
    historical, historical_rows = phase._load_historical_framework()
    structural = phase._load_structural_dependencies()
    _require(home.get("summary", {}).get("current_report_grade") == "D", "current home dependency grade drift", errors)
    _require(home.get("summary", {}).get("nonzero_delta_reconciliation_count") == 9, "current home dependency difference drift", errors)
    _require(historical.get("phase_id") == "S11-P2" and len(historical_rows) == 13, "historical framework dependency failed", errors)
    _require(historical.get("quality_gate", {}).get("pending_reconciliation_count") == 12, "historical stale finding missing", errors)
    _require(structural.get("current_authority_record_count") == 45, "authority dependency drift", errors)
    _require(structural.get("current_source_adapter_record_count") == 17, "adapter dependency drift", errors)


def _validate_governance(errors: list[str]) -> None:
    events = _read_jsonl(phase.DEVELOPMENT_EVENTS_PATH)
    statuses = _read_jsonl(phase.STAGE_STATUS_PATH)
    tasks = _read_jsonl(phase.TASK_STATUS_PATH)
    _require(sum(row.get("phase_id") == phase.PHASE_ID for row in events) == 1, "development event missing or duplicated", errors)
    _require(sum(row.get("phase_id") == phase.PHASE_ID for row in statuses) == 1, "stage status missing or duplicated", errors)
    _require(sum(row.get("phase_id") == phase.PHASE_ID for row in tasks) == 1, "task status missing or duplicated", errors)

    formula_text = Path("KMFA/docs/governance/formula_registry.yaml").read_text(encoding="utf-8")
    model_text = Path("KMFA/docs/governance/model_registry.yaml").read_text(encoding="utf-8")
    metadata_model_text = Path("KMFA/metadata/model_registry.yaml").read_text(encoding="utf-8")
    _require(phase.FORMULA_ID in formula_text, "formula record missing", errors)
    for token in (
        "matrix_row_count == 13",
        "current_ready_row_count == 0",
        "historical_ready_status_recomputed_count == 4",
        "status_detail_interaction_count == 26",
        "persistent_status_write_performed == false",
        "current_grade == D",
    ):
        _require(token in formula_text, f"formula control missing: {token}", errors)
    _require(phase.MODEL_REGISTRY_KEY in model_text, "model registry record missing", errors)
    _require(phase.MODEL_REGISTRY_KEY in metadata_model_text, "metadata model registry record missing", errors)

    with Path("KMFA/docs/governance/parameter_registry.csv").open(encoding="utf-8", newline="") as handle:
        parameters = {row["parameter_id"]: row for row in csv.DictReader(handle)}
    expected = {
        "PARAM-KMFA-1711": "13;11;5;0;6;1;2;4;4;45;17;2;4;10;26;10;2;1;Q4;D;3;9;2;1;12;0;0;5;NO_GO",
        "PARAM-KMFA-1712": "true;true;true;true;false;true;true;true;true;true;false;false;false;false;false;false;false;NO_GO",
        "PARAM-KMFA-1713": "true;true;true;true;true;true;false;false;false;false;false;false;false;false;false;NO_GO",
    }
    for parameter_id, expected_value in expected.items():
        row = parameters.get(parameter_id, {})
        for field in ("default_value", "initial_or_prior_value", "active_value", "extracted_value"):
            _require(row.get(field) == expected_value, f"parameter drift: {parameter_id}:{field}", errors)

    _require(Path("KMFA/VERSION").read_text(encoding="utf-8").strip() == phase.VERSION, "VERSION drift", errors)
    matrix = Path("KMFA/docs/governance/VERSION_MATRIX.yaml").read_text(encoding="utf-8")
    _require(f'current_phase: "{phase.PHASE_ID}"' in matrix, "VERSION_MATRIX current phase drift", errors)
    handoff = Path("KMFA/HANDOFF.md").read_text(encoding="utf-8")
    _require(f"phase: `{phase.PHASE_ID}`" in handoff, "HANDOFF current phase drift", errors)
    _require("S11-P3" in handoff, "HANDOFF next phase missing", errors)
    _require("不得执行 GitHub upload" in handoff, "HANDOFF upload boundary missing", errors)


def _read_audit(path: Path, errors: list[str], expected_files: int, expected_rows: int = 0) -> None:
    _require(path.is_file(), f"browser audit missing: {path}", errors)
    if not path.is_file():
        return
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    _require(len({row.get("file") for row in rows}) == expected_files, f"browser audit file count mismatch: {path}", errors)
    if expected_rows:
        _require(len(rows) == expected_rows, f"browser audit row count mismatch: {path}", errors)
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
        phase.PRIVATE_VALIDATION_REPORT_PATH,
    )
    for path in private_paths:
        _require(path.is_file(), f"private evidence missing: {path}", errors)
        _require(_git_check_ignore(path), f"private evidence not ignored: {path}", errors)
        _require(not _git_tracked(path), f"private evidence tracked: {path}", errors)
    if all(path.is_file() for path in private_paths):
        before = _read_json(phase.PRIVATE_RAW_BEFORE_PATH)
        after = _read_json(phase.PRIVATE_RAW_AFTER_PATH)
        prior = _read_json(phase.p1.PRIVATE_RAW_AFTER_PATH)
        current = phase._raw_snapshot("validate_v014_s11_p2_post_remediation_source_check_board")
        normalize = phase._normalize_raw
        _require(normalize(before) == normalize(after), "raw before/after mismatch", errors)
        _require(normalize(before) == normalize(prior), "raw cross-phase mismatch", errors)
        _require(normalize(after) == normalize(current), "raw current mismatch", errors)
        _require(before.get("file_count") == 5, "raw file count mismatch", errors)
        report = phase.PRIVATE_VALIDATION_REPORT_PATH.read_text(encoding="utf-8")
        for token in ("无需生成最终差异报告", "3 / 9 / 2 / 1", "未写入原始层或持久业务状态"):
            _require(token in report, f"private report token missing: {token}", errors)

    if not require_browser_evidence:
        return
    browser_paths = (
        phase.PRIVATE_BASELINE_AUDIT_PATH,
        phase.PRIVATE_CURRENT_AUDIT_PATH,
        phase.PRIVATE_BROWSER_PATH,
    )
    for path in browser_paths:
        _require(path.is_file(), f"browser evidence missing: {path}", errors)
        _require(_git_check_ignore(path), f"browser evidence not ignored: {path}", errors)
        _require(not _git_tracked(path), f"browser evidence tracked: {path}", errors)
    _read_audit(phase.PRIVATE_BASELINE_AUDIT_PATH, errors, 6, 54)
    _read_audit(phase.PRIVATE_CURRENT_AUDIT_PATH, errors, 1)
    if phase.PRIVATE_CURRENT_AUDIT_PATH.is_file():
        with phase.PRIVATE_CURRENT_AUDIT_PATH.open(encoding="utf-8-sig", newline="") as handle:
            _require(len(list(csv.DictReader(handle))) >= 21, "current audit control coverage too small", errors)
    if phase.PRIVATE_BROWSER_PATH.is_file():
        browser = _read_json(phase.PRIVATE_BROWSER_PATH)
        _require(browser.get("status") == "PASS", "browser status mismatch", errors)
        expected_counts = {
            "viewport_checks": 2,
            "search_checks": 4,
            "status_filter_checks": 10,
            "status_detail_checks": 26,
            "status_preview_checks": 10,
            "keyboard_checks": 2,
            "home_link_http_checks": 1,
        }
        for key, count in expected_counts.items():
            _require(len(browser.get(key, [])) == count, f"browser {key} count mismatch", errors)
        for key in (
            "search_checks",
            "status_filter_checks",
            "status_detail_checks",
            "status_preview_checks",
            "keyboard_checks",
            "home_link_http_checks",
        ):
            _require(all(item.get("passed") is True for item in browser.get(key, [])), f"browser {key} failed", errors)
        _require(
            all(
                item.get("ui_ready") is True
                and item.get("console_error_count") == 0
                and item.get("no_horizontal_overflow") is True
                and item.get("matrix_scroll_contained") is True
                for item in browser.get("viewport_checks", [])
            ),
            "browser viewport safety failed",
            errors,
        )
    for name, width in (("kmfa_source_check_board_desktop.png", 1440), ("kmfa_source_check_board_mobile.png", 390)):
        path = phase.PRIVATE_SCREENSHOT_DIR / name
        _require(path.is_file(), f"browser screenshot missing: {path}", errors)
        _require(_git_check_ignore(path), f"browser screenshot not ignored: {path}", errors)
        _require(not _git_tracked(path), f"browser screenshot tracked: {path}", errors)
        if path.is_file():
            actual_width, height = _png_dimensions(path)
            _require(actual_width == width, f"screenshot width mismatch: {path}", errors)
            _require(height >= 700, f"screenshot height too small: {path}", errors)


@functools.lru_cache(maxsize=8)
def validate_v014_s11_p2_post_remediation_source_check_board(
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
        manifest = validate_v014_s11_p2_post_remediation_source_check_board(
            require_private_evidence=args.require_private_evidence,
            require_browser_evidence=args.require_browser_evidence,
            require_final_evidence=args.require_final_evidence,
        )
    except (OSError, ValueError, json.JSONDecodeError, ValidationError) as exc:
        print(f"FAIL: {exc}")
        return 1
    summary = manifest["summary"]
    print(
        "PASS: S11-P2 post-remediation source check board "
        f"rows={summary['matrix_row_count']} ready={summary['current_ready_row_count']} "
        f"grade={summary['current_report_grade']} decision={summary['decision']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
