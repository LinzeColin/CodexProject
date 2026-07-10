#!/usr/bin/env python3
"""Validate KMFA v0.1.4 S11-P1 post-remediation home navigation."""

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

from KMFA.tools import v014_s11_p1_post_remediation_home_navigation as phase
from KMFA.tools.home_navigation_runtime import REQUIRED_NAVIGATION_LABELS


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
HISTORICAL_FUTURE_TOKENS = (
    "S11_P2",
    "S11_P3",
    "S12_P1",
    "S13_P1",
    "S13_P2",
    "S14_P1",
    "S14_P2",
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
    rows = []
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
        phase.MODULES_PATH,
        phase.GO_NO_GO_PATH,
        phase.HTML_PATH,
        phase.COMPLETION_PATH,
        phase.READ_ME_PATH,
        phase.TEST_RESULTS_PATH,
        phase.RISK_REGISTER_PATH,
        phase.ROLLBACK_PATH,
        phase.METADATA_SUMMARY_PATH,
        phase.METADATA_MANIFEST_PATH,
        phase.METADATA_MODULES_PATH,
        phase.METADATA_GO_NO_GO_PATH,
    )
    for path in public_paths:
        _check_public_file(path, errors)

    summary = _read_json(phase.SUMMARY_PATH)
    manifest = _read_json(phase.MANIFEST_PATH)
    modules = _read_json(phase.MODULES_PATH)
    go_no_go = _read_json(phase.GO_NO_GO_PATH)
    _require(summary == _read_json(phase.METADATA_SUMMARY_PATH), "summary mirror drift", errors)
    _require(manifest == _read_json(phase.METADATA_MANIFEST_PATH), "manifest mirror drift", errors)
    _require(modules == _read_json(phase.METADATA_MODULES_PATH), "modules mirror drift", errors)
    _require(go_no_go == _read_json(phase.METADATA_GO_NO_GO_PATH), "go/no-go mirror drift", errors)
    _require(manifest.get("summary") == summary, "manifest summary drift", errors)
    _require(manifest.get("navigation_modules") == modules.get("modules"), "manifest modules drift", errors)

    expected = {
        "project_id": "KMFA",
        "stage_id": "S11",
        "phase_id": phase.PHASE_ID,
        "roadmap_phase_id": "S11-P1",
        "status": phase.STATUS,
        "decision": "NO_GO",
        "navigation_module_count": 8,
        "navigation_view_count": 8,
        "nav_button_count": 8,
        "module_action_button_count": 8,
        "visible_feedback_panel_count": 1,
        "report_link_count": 4,
        "unique_report_target_count": 2,
        "historical_future_target_link_count": 0,
        "open_final_difference_accepted_count": 3,
        "nonzero_delta_reconciliation_count": 9,
        "zero_delta_reconciliation_count": 2,
        "incomplete_reconciliation_count": 1,
        "hard_block_count": 12,
        "current_data_quality_grade": "Q4",
        "current_report_grade": "D",
        "formal_report_count": 0,
        "business_decision_basis_allowed_count": 0,
        "raw_source_file_count": 5,
    }
    for key, value in expected.items():
        _require(summary.get(key) == value, f"summary {key} mismatch", errors)
    _require(summary.get("required_navigation_labels") == list(REQUIRED_NAVIGATION_LABELS), "navigation labels mismatch", errors)
    for key in (
        "current_s10_restricted_report_links_only",
        "km_brand_mark_present",
        "blue_business_style",
        "all_chinese_visible_copy",
        "raw_snapshot_exact_match",
        "raw_cross_phase_snapshot_exact_match",
    ):
        _require(summary.get(key) is True, f"summary {key} must be true", errors)
    for key in ("contains_stale_pending_twelve", "contains_b_grade", "single_k_brand_mark_present"):
        _require(summary.get(key) is False, f"summary {key} must be false", errors)
    _require("pending_reconciliation_count" not in summary, "stale pending count leaked into summary", errors)

    records = manifest.get("navigation_modules", [])
    _require(len(records) == 8, "navigation module count mismatch", errors)
    _require([record.get("visible_label") for record in records] == list(REQUIRED_NAVIGATION_LABELS), "module order mismatch", errors)
    _require(len({record.get("module_id") for record in records}) == 8, "module ids not unique", errors)
    _require(len({record.get("route_hash") for record in records}) == 8, "route hashes not unique", errors)
    for record in records:
        module_id = record.get("module_id")
        _require(record.get("visible_feedback_required") is True, f"visible feedback missing: {module_id}", errors)
        _require(record.get("current_report_grade") == "D", f"module grade drift: {module_id}", errors)
        _require(record.get("decision") == "NO_GO", f"module decision drift: {module_id}", errors)
        _require(record.get("formal_report_allowed") is False, f"module formal report opened: {module_id}", errors)
        _require(record.get("business_decision_basis_allowed") is False, f"module decision basis opened: {module_id}", errors)
        _require(record.get("raw_business_values_included") is False, f"module contains raw values: {module_id}", errors)
    _require(modules.get("module_count") == 8, "modules payload count mismatch", errors)

    quality = manifest.get("quality_gate", {})
    _require(quality.get("home_navigation_allowed") is True, "home navigation not allowed", errors)
    for key in (
        "complete_trusted_report_display_allowed",
        "formal_report_allowed",
        "business_decision_basis_allowed",
        "business_execution_allowed",
    ):
        _require(quality.get(key) is False, f"quality gate {key} must be false", errors)
    _require(quality.get("release_permission") == "blocked", "release permission mismatch", errors)
    boundaries = manifest.get("phase_boundaries", {})
    _require(boundaries.get("s11_p1_performed") is True, "S11-P1 boundary missing", errors)
    for key in (
        "s11_p2_performed",
        "s11_p3_performed",
        "stage11_review_performed",
        "github_upload_performed",
        "app_reinstall_performed",
        "formal_report_release_performed",
        "business_execution_performed",
    ):
        _require(boundaries.get(key) is False, f"boundary {key} must be false", errors)
    safety = manifest.get("public_repo_safety", {})
    _require(safety.get("aggregate_only") is True, "public evidence must be aggregate-only", errors)
    _require(all(value is False for key, value in safety.items() if key != "aggregate_only"), "public safety drift", errors)
    dependencies = manifest.get("dependencies", {})
    for key in (
        "current_s10_post_remediation_review_validated",
        "historical_s11_p1_framework_validated",
        "v14_human_flow_baseline_rerun",
    ):
        _require(dependencies.get(key) is True, f"dependency {key} must be true", errors)
    _require(dependencies.get("historical_dynamic_state_reused") is False, "historical state was reused", errors)
    _require(go_no_go.get("decision") == "NO_GO", "go/no-go decision mismatch", errors)
    _require(go_no_go.get("home_navigation_allowed") is True, "go/no-go home navigation mismatch", errors)
    for key in ("formal_report_allowed", "business_decision_basis_allowed", "s11_p2_performed", "github_upload_performed"):
        _require(go_no_go.get(key) is False, f"go/no-go {key} must be false", errors)
    return manifest


def _validate_html(errors: list[str]) -> None:
    text = phase.HTML_PATH.read_text(encoding="utf-8")
    _require(text.startswith("<!doctype html>"), "HTML doctype missing", errors)
    for label in REQUIRED_NAVIGATION_LABELS:
        _require(label in text, f"navigation label missing: {label}", errors)
    for token in (
        "KMFA",
        ">KM<",
        "Q4 / D",
        "NO_GO",
        "D级（未放行）",
        "关键现金数据仍不完整",
        "九项非零差异",
        "一项比较未完成",
        "仅供内部复核",
        'role="tablist"',
        'aria-live="polite"',
        "ArrowDown",
        "hashchange",
    ):
        _require(token in text, f"HTML token missing: {token}", errors)
    for token in ("B级", "12 pending", "pending_reconciliation_count", *HISTORICAL_FUTURE_TOKENS):
        _require(token not in text, f"stale/future token in HTML: {token}", errors)
    _require(text.count("data-module-id=") == 8, "HTML nav button count mismatch", errors)
    _require(text.count("data-module-view=") == 8, "HTML view count mismatch", errors)
    _require(text.count("data-module-action=") == 8, "HTML action count mismatch", errors)
    hrefs = re.findall(r'<a[^>]+data-report-link[^>]+href="([^"]+)"', text)
    _require(len(hrefs) == 4, "HTML report link count mismatch", errors)
    _require(set(hrefs) == {phase.BUSINESS_REPORT_HREF, phase.PROJECT_REPORT_HREF}, "HTML report targets mismatch", errors)
    for href in hrefs:
        _require((phase.HTML_PATH.parent / href).resolve().is_file(), f"report target missing: {href}", errors)


def _validate_dependencies(errors: list[str]) -> None:
    current = phase._validate_s10_dependency()
    historical = phase.validate_v014_s11_p1_home_navigation()
    summary = current.get("summary", {})
    _require(summary.get("current_report_grade") == "D", "Stage 10 grade dependency drift", errors)
    _require(summary.get("open_final_difference_accepted_count") == 3, "Stage 10 open count drift", errors)
    _require(historical.get("stage_id") == "S11", "historical S11-P1 dependency failed", errors)
    _require(historical.get("home_navigation_summary", {}).get("navigation_module_count") == 8, "historical navigation framework drift", errors)


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
        "navigation_module_count == 8",
        "navigation_interaction_count == 16",
        "module_action_interaction_count == 16",
        "current_grade == D",
        "historical_future_target_link_count == 0",
    ):
        _require(token in formula_text, f"formula control missing: {token}", errors)
    _require(phase.MODEL_REGISTRY_KEY in model_text, "model registry record missing", errors)
    _require(phase.MODEL_REGISTRY_KEY in metadata_model_text, "metadata model registry record missing", errors)

    with Path("KMFA/docs/governance/parameter_registry.csv").open(encoding="utf-8", newline="") as handle:
        parameters = {row["parameter_id"]: row for row in csv.DictReader(handle)}
    expected = {
        "PARAM-KMFA-1708": "8;8;8;8;1;4;2;2;16;16;4;4;Q4;D;3;9;2;1;12;0;0;5;NO_GO",
        "PARAM-KMFA-1709": "true;true;true;true;false;false;true;true;false;false;false;false;false;false;NO_GO",
        "PARAM-KMFA-1710": "true;true;true;true;true;true;false;false;false;false;false;false;false;false;NO_GO",
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
    _require("S11-P2" in handoff, "HANDOFF next phase missing", errors)
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
        prior = _read_json(phase.s10_phase.PRIVATE_RAW_AFTER_PATH)
        current = phase._raw_snapshot("validate_v014_s11_p1_post_remediation_home_navigation")
        normalize = phase._normalize_raw
        _require(normalize(before) == normalize(after), "raw before/after mismatch", errors)
        _require(normalize(before) == normalize(prior), "raw cross-phase mismatch", errors)
        _require(normalize(after) == normalize(current), "raw current mismatch", errors)
        _require(before.get("file_count") == 5, "raw file count mismatch", errors)
        report = phase.PRIVATE_VALIDATION_REPORT_PATH.read_text(encoding="utf-8")
        for token in ("无需生成最终差异报告", "不推断、不平均、不补零", "3 / 9 / 2 / 1"):
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
    if phase.PRIVATE_BROWSER_PATH.is_file():
        browser = _read_json(phase.PRIVATE_BROWSER_PATH)
        _require(browser.get("status") == "PASS", "browser status mismatch", errors)
        _require(len(browser.get("viewport_checks", [])) == 2, "browser viewport count mismatch", errors)
        _require(len(browser.get("navigation_checks", [])) == 16, "browser navigation count mismatch", errors)
        _require(len(browser.get("module_action_checks", [])) == 16, "browser action count mismatch", errors)
        _require(len(browser.get("keyboard_navigation_checks", [])) == 4, "browser keyboard count mismatch", errors)
        _require(len(browser.get("report_link_http_checks", [])) == 4, "browser link count mismatch", errors)
        for key in ("navigation_checks", "module_action_checks", "keyboard_navigation_checks", "report_link_http_checks"):
            _require(all(item.get("passed") is True for item in browser.get(key, [])), f"browser {key} failed", errors)
        _require(
            all(item.get("console_error_count") == 0 and item.get("no_horizontal_overflow") is True for item in browser.get("viewport_checks", [])),
            "browser viewport safety failed",
            errors,
        )
    for name, width in (
        ("kmfa_home_navigation_desktop.png", 1440),
        ("kmfa_home_navigation_mobile.png", 390),
    ):
        path = phase.PRIVATE_SCREENSHOT_DIR / name
        _require(path.is_file(), f"browser screenshot missing: {path}", errors)
        _require(_git_check_ignore(path), f"browser screenshot not ignored: {path}", errors)
        _require(not _git_tracked(path), f"browser screenshot tracked: {path}", errors)
        if path.is_file():
            actual_width, height = _png_dimensions(path)
            _require(actual_width == width, f"screenshot width mismatch: {path}", errors)
            _require(height >= 700, f"screenshot height too small: {path}", errors)


@functools.lru_cache(maxsize=8)
def validate_v014_s11_p1_post_remediation_home_navigation(
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
        manifest = validate_v014_s11_p1_post_remediation_home_navigation(
            require_private_evidence=args.require_private_evidence,
            require_browser_evidence=args.require_browser_evidence,
            require_final_evidence=args.require_final_evidence,
        )
    except (ValidationError, ValueError, KeyError, RuntimeError) as exc:
        print(f"FAIL: {exc}")
        return 1
    summary = manifest["summary"]
    print(
        "PASS: S11-P1 post-remediation home navigation "
        f"modules={summary['navigation_module_count']} views={summary['navigation_view_count']} "
        f"grade={summary['current_report_grade']} decision={summary['decision']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
