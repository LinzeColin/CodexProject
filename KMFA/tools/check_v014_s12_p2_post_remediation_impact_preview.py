#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Validate current public-safe KMFA S12-P2 impact-preview evidence."""

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

from KMFA.tools import v014_s12_p2_post_remediation_impact_preview as phase


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


def _walk_keys(value: Any):
    if isinstance(value, dict):
        for key, child in value.items():
            yield key
            yield from _walk_keys(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_keys(child)


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


def _check_public_file(path: Path, errors: list[str]) -> None:
    _require(path.is_file(), f"missing public artifact: {path}", errors)
    if not path.is_file():
        return
    _require(path.suffix.lower() not in FORBIDDEN_PUBLIC_SUFFIXES, f"forbidden public suffix: {path}", errors)
    text = path.read_text(encoding="utf-8", errors="ignore")
    _require(RAW_ROOT_TOKEN not in text, f"raw root token leaked in {path}", errors)
    _require(LOCAL_DOWNLOADS_PATTERN.search(text) is None, f"local Downloads path leaked in {path}", errors)
    for pattern in SECRET_PATTERNS:
        _require(pattern.search(text) is None, f"secret-like token in {path}", errors)
    if path.suffix.lower() == ".json":
        for key in _walk_keys(json.loads(text)):
            _require(key not in FORBIDDEN_PUBLIC_KEYS, f"forbidden public key {key!r} in {path}", errors)


def _validate_public(errors: list[str]) -> dict[str, Any]:
    public_paths = (
        phase.SUMMARY_PATH,
        phase.MANIFEST_PATH,
        phase.PREVIEWS_PATH,
        phase.GO_NO_GO_PATH,
        phase.HTML_PATH,
        phase.REPORT_PATH,
        phase.TEST_RESULTS_PATH,
        phase.RISK_REGISTER_PATH,
        phase.ROLLBACK_PATH,
        phase.METADATA_SUMMARY_PATH,
        phase.METADATA_MANIFEST_PATH,
        phase.METADATA_PREVIEWS_PATH,
        phase.METADATA_GO_NO_GO_PATH,
    )
    for path in public_paths:
        _check_public_file(path, errors)
    manifest = _read_json(phase.MANIFEST_PATH)
    summary = _read_json(phase.SUMMARY_PATH)
    previews = _read_json(phase.PREVIEWS_PATH)
    go_no_go = _read_json(phase.GO_NO_GO_PATH)
    _require(summary == _read_json(phase.METADATA_SUMMARY_PATH), "summary mirror drift", errors)
    _require(manifest == _read_json(phase.METADATA_MANIFEST_PATH), "manifest mirror drift", errors)
    _require(previews == _read_json(phase.METADATA_PREVIEWS_PATH), "preview mirror drift", errors)
    _require(go_no_go == _read_json(phase.METADATA_GO_NO_GO_PATH), "go/no-go mirror drift", errors)
    _require(manifest.get("summary") == summary, "manifest summary drift", errors)
    _require(manifest.get("impact_preview_definitions") == previews.get("previews"), "manifest preview drift", errors)
    return manifest


def _validate_summary(manifest: dict[str, Any], errors: list[str]) -> None:
    summary = manifest.get("summary", {})
    expected = {
        "project_id": "KMFA",
        "stage_id": "S12",
        "roadmap_phase_id": "S12-P2",
        "phase_id": phase.PHASE_ID,
        "task_id": phase.TASK_ID,
        "acceptance_id": phase.ACCEPTANCE_ID,
        "version": phase.VERSION,
        "status": phase.STATUS,
        "current_data_quality_grade": "Q4",
        "current_report_grade": "D",
        "decision": "NO_GO",
        "source_pending_action_group_count": 6,
        "source_event_template_count": 4,
        "impact_preview_definition_count": 6,
        "high_risk_preview_count": 5,
        "medium_risk_preview_count": 1,
        "second_confirmation_required_count": 5,
        "potential_affected_project_slot_count": 4,
        "unique_affected_metric_count": 16,
        "unique_affected_report_count": 6,
        "current_session_preview_count_at_rest": 0,
        "current_session_second_confirmation_count_at_rest": 0,
        "current_approved_business_event_count": 0,
        "current_published_business_event_count": 0,
        "open_final_difference_accepted_count": 3,
        "nonzero_delta_reconciliation_count": 9,
        "zero_delta_reconciliation_count": 2,
        "incomplete_reconciliation_count": 1,
        "hard_block_count": 12,
        "raw_source_file_count": 5,
        "raw_snapshot_exact_match": True,
        "raw_cross_phase_snapshot_exact_match": True,
        "formal_report_count": 0,
        "business_decision_basis_count": 0,
        "s12_p1_performed": True,
        "s12_p2_performed": True,
        "s12_p3_performed": False,
        "stage12_review_performed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
    }
    for key, value in expected.items():
        _require(summary.get(key) == value, f"summary {key} mismatch", errors)
    _require("pending_reconciliation_count" not in summary, "stale pending=12 field present", errors)
    _require(manifest.get("s12_p1_post_remediation_dependency_validated") is True, "S12-P1 dependency flag mismatch", errors)
    _require(manifest.get("legacy_s12_p2_policy_fixture_validated") is True, "legacy fixture flag mismatch", errors)
    _require(manifest.get("next_phase") == "S12-P3", "next phase mismatch", errors)


def _validate_previews(manifest: dict[str, Any], errors: list[str]) -> None:
    previews = manifest.get("impact_preview_definitions", [])
    _require(len(previews) == 6, "preview definition count mismatch", errors)
    _require(len({row.get("preview_id") for row in previews}) == 6, "preview ids not unique", errors)
    _require(
        {row.get("source_group_id") for row in previews}
        == {f"PEND-S12P1-{index:03d}" for index in range(1, 7)},
        "source group coverage mismatch",
        errors,
    )
    _require(
        {row.get("manual_action_kind") for row in previews}
        == {"field_mapping", "project_matching", "difference_handling", "note"},
        "manual action kind coverage mismatch",
        errors,
    )
    _require(sum(row.get("risk_level") == "high" for row in previews) == 5, "high-risk count mismatch", errors)
    _require(sum(row.get("second_confirmation_required") is True for row in previews) == 5, "confirmation count mismatch", errors)
    for row in previews:
        _require(row.get("project_attribution") == "unproven_or_not_applicable", "project attribution drift", errors)
        _require(row.get("project_scope_semantics") == "potential_impact_not_attribution", "project scope semantics drift", errors)
        for key in ("affected_project_scope", "affected_metrics", "affected_reports"):
            _require(isinstance(row.get(key), list) and len(row[key]) > 0, f"preview {key} missing", errors)
        _require(row.get("preview_status") == "definition_ready_session_preview_required", "preview status drift", errors)
        _require(row.get("preview_passed_persistently") is False, "persistent preview pass forbidden", errors)
        _require(row.get("session_preview_allowed") is True, "session preview must be allowed", errors)
        for key in (
            "publish_allowed",
            "business_event_approval_allowed",
            "derived_rerun_allowed",
            "persistent_business_write_allowed",
            "raw_layer_write_allowed",
            "business_value_committed",
        ):
            _require(row.get(key) is False, f"preview {key} must be false", errors)
        if row.get("risk_level") == "high":
            _require(row.get("second_confirmation_status") == "required_in_session", "high-risk confirmation status drift", errors)
        else:
            _require(row.get("second_confirmation_status") == "not_required", "medium confirmation status drift", errors)


def _validate_html(errors: list[str]) -> None:
    text = phase.HTML_PATH.read_text(encoding="utf-8")
    for token in (
        "data-preview-search",
        "data-risk-filter",
        "data-generate-preview",
        "data-high-risk-ack",
        "data-confirm-preview",
        "data-check-publish",
        "data-reset-session",
        "受影响项目",
        "受影响指标",
        "受影响报告",
        "高风险二次确认",
        "未通过影响预览不得发布",
        "Q4 / D · NO_GO",
        "Stage 12 三个 phase 均已完成",
    ):
        _require(token in text, f"HTML token missing: {token}", errors)
    for token in ("data-rerun", "localStorage", "sessionStorage", "indexedDB", "fetch(", "XMLHttpRequest"):
        _require(token not in text, f"forbidden HTML behavior: {token}", errors)
    _require(text.count("data-generate-preview=") == 6, "HTML preview button count mismatch", errors)
    _require(text.count("data-return-link=") == 5, "HTML return link count mismatch", errors)


def _validate_dependencies(errors: list[str]) -> None:
    dependency = phase._load_s12_p1_dependency()
    _require(dependency.get("phase_id") == s12_p1_phase_id(), "current S12-P1 dependency mismatch", errors)
    contract = phase._load_contract()
    _require(contract.get("roadmap_contract_read") is True, "roadmap contract not read", errors)
    _require(contract.get("legacy_policy_fixture_confirmation_rule_validated") is True, "legacy confirmation fixture invalid", errors)
    _require(contract.get("legacy_dynamic_counts_applied_to_current_state") is False, "legacy dynamic state reused", errors)


def s12_p1_phase_id() -> str:
    return "V014_S12_P1_POST_REMEDIATION_PENDING_ACTIONS"


def _validate_boundaries(manifest: dict[str, Any], errors: list[str]) -> None:
    quality = manifest.get("quality_gate", {})
    expected_quality = phase._quality_gate()
    for key, value in expected_quality.items():
        _require(quality.get(key) == value, f"quality {key} mismatch", errors)
    boundaries = manifest.get("phase_boundaries", {})
    for key, value in phase._phase_boundaries().items():
        _require(boundaries.get(key) == value, f"phase boundary {key} mismatch", errors)
    safety = manifest.get("public_repo_safety", {})
    _require(safety.get("aggregate_only") is True, "public evidence not aggregate-only", errors)
    _require(all(value is False for key, value in safety.items() if key != "aggregate_only"), "public safety drift", errors)


def _validate_governance(errors: list[str]) -> None:
    matrix = phase.VERSION_MATRIX_PATH.read_text(encoding="utf-8")
    _require(phase.MODEL_REGISTRY_KEY in matrix, "VERSION_MATRIX profile missing", errors)
    _require(phase.VERSION in matrix, "VERSION_MATRIX version missing", errors)
    _require(phase.FORMULA_ID in Path("KMFA/docs/governance/formula_registry.yaml").read_text(encoding="utf-8"), "formula missing", errors)
    for path in (Path("KMFA/docs/governance/model_registry.yaml"), Path("KMFA/metadata/model_registry.yaml")):
        _require(phase.MODEL_REGISTRY_KEY in path.read_text(encoding="utf-8"), f"model registry missing: {path}", errors)
    parameter_text = Path("KMFA/docs/governance/parameter_registry.csv").read_text(encoding="utf-8")
    for parameter_id in phase.PARAMETER_IDS:
        _require(parameter_id in parameter_text, f"parameter missing: {parameter_id}", errors)
    _require(phase.TASK_ID in Path("KMFA/docs/governance/delivery_tasks.yaml").read_text(encoding="utf-8"), "delivery task missing", errors)
    _require(phase.TASK_ID in Path("KMFA/docs/governance/TRACEABILITY_MATRIX.csv").read_text(encoding="utf-8"), "traceability missing", errors)
    for path in (
        Path("KMFA/CHANGELOG.md"),
        Path("KMFA/docs/governance/DEVELOPMENT_LEDGER.md"),
        Path("KMFA/docs/governance/MODEL_SPEC.md"),
        Path("KMFA/功能清单.md"),
        Path("KMFA/开发记录.md"),
        Path("KMFA/模型参数文件.md"),
    ):
        _require(phase.PHASE_ID in path.read_text(encoding="utf-8"), f"governance doc missing phase: {path}", errors)
    if _phase_is_current(matrix):
        _require(Path("KMFA/VERSION").read_text(encoding="utf-8").strip() == phase.VERSION, "VERSION drift", errors)
        handoff = Path("KMFA/HANDOFF.md").read_text(encoding="utf-8")
        _require(f"phase: `{phase.PHASE_ID}`" in handoff, "HANDOFF phase drift", errors)
        _require("S12-P3" in handoff, "HANDOFF next phase missing", errors)
        _require("不得执行 GitHub upload" in handoff, "HANDOFF upload boundary missing", errors)


def _read_audit(path: Path, errors: list[str], expected_files: int, expected_rows: int = 0) -> None:
    _require(path.is_file(), f"audit missing: {path}", errors)
    if not path.is_file():
        return
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    _require(len({row.get("file") for row in rows if row.get("file")}) == expected_files, f"audit file count mismatch: {path}", errors)
    if expected_rows:
        _require(len(rows) == expected_rows, f"audit row count mismatch: {path}", errors)
    _require(sum(row.get("status") == "FAIL" for row in rows) == 0, f"audit failure: {path}", errors)
    _require(sum(row.get("status") == "WARN" for row in rows) == 0, f"audit warning: {path}", errors)


def _png_dimensions(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValidationError(f"invalid PNG: {path}")
    return struct.unpack(">II", data[16:24])


def _validate_private(errors: list[str], require_browser_evidence: bool) -> None:
    before = _read_json(phase.PRIVATE_RAW_BEFORE_PATH)
    after = _read_json(phase.PRIVATE_RAW_AFTER_PATH)
    previous = _read_json(phase.s12_p1.PRIVATE_RAW_AFTER_PATH)
    normalize_raw = phase.s12_p1.s11_project._normalize_raw
    _require(normalize_raw(before) == normalize_raw(after), "phase raw snapshot drift", errors)
    _require(normalize_raw(before) == normalize_raw(previous), "cross-S12-P1 raw snapshot drift", errors)
    _require(before.get("file_count") == 5, "raw file count mismatch", errors)
    for path in (
        phase.PRIVATE_RAW_BEFORE_PATH,
        phase.PRIVATE_RAW_AFTER_PATH,
        phase.PRIVATE_VALIDATION_REPORT_PATH,
        phase.PRIVATE_BASELINE_AUDIT_PATH,
        phase.PRIVATE_CURRENT_AUDIT_PATH,
    ):
        _require(path.is_file(), f"private evidence missing: {path}", errors)
        _require(_git_check_ignore(path), f"private evidence not ignored: {path}", errors)
        _require(not _git_tracked(path), f"private evidence tracked: {path}", errors)
    _read_audit(phase.PRIVATE_BASELINE_AUDIT_PATH, errors, expected_files=6, expected_rows=54)
    manifest = _read_json(phase.MANIFEST_PATH)
    current_rows = manifest.get("browser_review", {}).get("current_html_control_row_count", 0)
    _read_audit(phase.PRIVATE_CURRENT_AUDIT_PATH, errors, expected_files=1, expected_rows=current_rows)
    if not require_browser_evidence:
        return
    browser = _read_json(phase.PRIVATE_BROWSER_PATH)
    _require(browser.get("status") == "PASS", "browser evidence not PASS", errors)
    expected_counts = {
        "viewport_checks": 2,
        "search_checks": 2,
        "risk_filter_checks": 2,
        "medium_preview_checks": 2,
        "high_preview_checks": 2,
        "preconfirmation_block_checks": 2,
        "second_confirmation_checks": 2,
        "publish_block_checks": 4,
        "reload_reset_checks": 2,
        "return_link_http_checks": 5,
        "actual_navigation_checks": 5,
    }
    for key, count in expected_counts.items():
        rows = browser.get(key, [])
        _require(len(rows) == count, f"browser {key} count mismatch", errors)
        _require(all(row.get("passed") for row in rows), f"browser {key} failure", errors)
    _require(all(row.get("console_error_count") == 0 for row in browser["viewport_checks"]), "browser console error", errors)
    _require(all(row.get("no_horizontal_overflow") is True for row in browser["viewport_checks"]), "browser overflow", errors)
    for mode, width in (("desktop", 1440), ("mobile", 390)):
        for suffix in ("", "_high_confirmed"):
            path = phase.PRIVATE_SCREENSHOT_DIR / f"impact_preview_{mode}{suffix}.png"
            _require(path.is_file(), f"screenshot missing: {path}", errors)
            _require(_git_check_ignore(path), f"screenshot not ignored: {path}", errors)
            _require(not _git_tracked(path), f"screenshot tracked: {path}", errors)
            if path.is_file():
                actual_width, height = _png_dimensions(path)
                _require(actual_width == width, f"screenshot width mismatch: {path}", errors)
                _require(height >= 700, f"screenshot height too small: {path}", errors)


@functools.lru_cache(maxsize=8)
def validate_v014_s12_p2_post_remediation_impact_preview(
    *,
    require_private_evidence: bool = False,
    require_browser_evidence: bool = False,
    require_final_evidence: bool = False,
) -> dict[str, Any]:
    errors: list[str] = []
    manifest = _validate_public(errors)
    _validate_summary(manifest, errors)
    _validate_previews(manifest, errors)
    _validate_html(errors)
    _validate_dependencies(errors)
    _validate_boundaries(manifest, errors)
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
        manifest = validate_v014_s12_p2_post_remediation_impact_preview(
            require_private_evidence=args.require_private_evidence,
            require_browser_evidence=args.require_browser_evidence,
            require_final_evidence=args.require_final_evidence,
        )
    except (ValidationError, ValueError, KeyError, RuntimeError) as exc:
        print(f"FAIL: {exc}")
        return 1
    summary = manifest["summary"]
    print(
        "PASS: S12-P2 post-remediation impact preview "
        f"definitions={summary['impact_preview_definition_count']} "
        f"high_risk={summary['high_risk_preview_count']} "
        f"published={summary['current_published_business_event_count']} "
        f"grade={summary['current_report_grade']} decision={summary['decision']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
