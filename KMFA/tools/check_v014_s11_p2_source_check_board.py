#!/usr/bin/env python3
"""Validate KMFA v0.1.4 S11-P2 public-safe source check board evidence."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from KMFA.tools.source_check_board_runtime import ALLOWED_BOARD_STATUSES, REQUIRED_BOARD_COLUMNS
from KMFA.tools.v014_s11_p2_source_check_board import (
    ACCEPTANCE_ID,
    HTML_OUTPUT_PATH,
    MANIFEST_PATH,
    NEXT_REQUIRED_STEP,
    PHASE_SCOPE,
    REPORT_PATH,
    RISK_REGISTER_PATH,
    ROLLBACK_PATH,
    ROWS_PATH,
    SCHEMA_VERSION,
    TASK_ID,
    TEST_RESULTS_PATH,
    _phase_boundaries,
    _public_repo_safety,
    _quality_gate,
    _raw_boundary,
    load_v14_html_uiux_baseline,
    validate_legacy_s11_p2_artifacts,
    validate_s11_p1_dependency,
)


PUBLIC_SAFETY_FALSE_KEYS = tuple(_public_repo_safety().keys())
RAW_BOUNDARY_FALSE_KEYS = tuple(
    key for key, value in _raw_boundary().items() if isinstance(value, bool) and value is False
)
QUALITY_FALSE_KEYS = tuple(key for key, value in _quality_gate().items() if value is False)
PHASE_FALSE_KEYS = tuple(key for key, value in _phase_boundaries().items() if value is False)
REQUIRED_HARD_BLOCKS = (
    "report_grade_d_only",
    "pending_reconciliation_blocks_formal_report",
    "raw_data_mutation_forbidden",
    "raw_value_publication_forbidden",
    "field_header_plaintext_publication_forbidden",
    "formal_report_release_blocked",
    "business_decision_basis_blocked",
    "s11_p3_not_performed",
    "stage11_review_not_performed",
    "lineage_full_check_not_performed",
    "raw_value_matching_not_performed",
    "github_upload_deferred_until_v014_stage1_18_complete",
    "app_reinstall_not_performed",
    "business_execution_blocked",
)
FORBIDDEN_PUBLIC_TEXT = (
    "raw_value:",
    "normalized_value:",
    "source_header_text:",
    "original_filename",
    "member_sha256:",
    "actual_package_sha256",
    "authoritative_value_cents",
    "system_value_cents",
    "pdf_value_cents",
    "excel_value_cents",
    "amount_cents:",
    "amount_yuan:",
    "sheet_name:",
    "row_value:",
    "cell_value:",
    "business_data:",
    "bank_statement",
    "contract_full_text",
    "salary_detail",
    "tax_filing",
    "connector_token:",
    "connector_password:",
    "api_key:",
    "private_key:",
    "-----" "BEGIN",
    "s" "k-",
    "project_name_plaintext",
    "customer_name_plaintext",
    "counterparty_plaintext",
    "company_entity_plaintext",
    "account_number:",
    "KMFA" "_MetaData",
    "/Users/linzezhang/Downloads",
)
STRICT_SECRET_PATTERNS = (
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"(?i)(password|passwd|secret|api_key|token)\s*=\s*[^\s,;]{8,}"),
)


class ValidationError(Exception):
    pass


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ValidationError(f"missing JSON file: {path}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValidationError(f"{path} must contain a JSON object")
    return value


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise ValidationError(f"missing JSONL file: {path}")
    records: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValidationError(f"{path} contains a non-object JSONL record")
        records.append(value)
    return records


def git_output(args: list[str]) -> str:
    result = subprocess.run(
        ["git", "-c", "core.quotePath=false", *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise ValidationError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def check_public_evidence_text(path: Path, errors: list[str]) -> None:
    require(path.exists(), f"missing public evidence: {path}", errors)
    if not path.exists():
        return
    text = path.read_text(encoding="utf-8", errors="ignore")
    lower = text.lower()
    for forbidden in FORBIDDEN_PUBLIC_TEXT:
        require(forbidden.lower() not in lower, f"forbidden public evidence text {forbidden!r} in {path}", errors)
    for pattern in STRICT_SECRET_PATTERNS:
        require(pattern.search(text) is None, f"secret-like token found in {path}: {pattern.pattern}", errors)


def _check_artifact_refs(manifest: dict[str, Any], errors: list[str]) -> None:
    artifact_refs = manifest.get("artifact_refs", {})
    for key in (
        "s11_p1_manifest",
        "legacy_manifest",
        "legacy_rows",
        "legacy_html",
        "v14_source_package_manifest",
        "v14_html_entry",
        "v14_html_audit_script",
        "v14_html_audit_report",
        "manifest",
        "rows",
        "html",
        "report",
        "test_results",
        "risk_register",
        "rollback_plan",
        "generator",
        "validator",
        "unit_test",
    ):
        path = Path(artifact_refs.get(key, ""))
        require(path.exists(), f"missing artifact ref: {key} -> {path}", errors)
    for ref in manifest.get("evidence_refs", []):
        require(Path(ref).exists(), f"missing evidence ref: {ref}", errors)


def validate_v014_s11_p2_source_check_board(manifest_path: Path = MANIFEST_PATH) -> dict[str, Any]:
    errors: list[str] = []
    manifest = read_json(manifest_path)
    s11_p1 = validate_s11_p1_dependency()
    legacy = validate_legacy_s11_p2_artifacts()
    baseline = load_v14_html_uiux_baseline()
    rows = read_jsonl(ROWS_PATH)
    html_text = HTML_OUTPUT_PATH.read_text(encoding="utf-8") if HTML_OUTPUT_PATH.exists() else ""

    require(manifest.get("schema_version") == SCHEMA_VERSION, "manifest schema mismatch", errors)
    require(manifest.get("project_id") == "KMFA", "project_id mismatch", errors)
    require(manifest.get("version") == "0.1.4", "version mismatch", errors)
    require(manifest.get("stage_id") == "S11", "stage_id must be S11", errors)
    require(manifest.get("phase_id") == "S11-P2", "phase_id must be S11-P2", errors)
    require(manifest.get("phase_scope") == PHASE_SCOPE, "phase scope mismatch", errors)
    require(manifest.get("task_id") == TASK_ID, "task_id mismatch", errors)
    require(
        manifest.get("status") == "completed_validated_local_only_no_go_upload_deferred_source_check_board_locked",
        "status mismatch",
        errors,
    )
    require(manifest.get("completed_task_ids") == ["S11P2T01", "S11P2T02", "S11P2T03"], "tasks mismatch", errors)
    require(manifest.get("acceptance_ids") == [ACCEPTANCE_ID], "acceptance id mismatch", errors)
    require(manifest.get("s11_p1_dependency_validated") is True, "S11-P1 dependency flag mismatch", errors)
    require(s11_p1.get("phase_id") == "S11-P1", "S11-P1 dependency did not validate S11-P1", errors)
    require(manifest.get("legacy_s11_p2_dependency_validated") is True, "legacy S11-P2 flag mismatch", errors)

    progress = manifest.get("stage11_phase_progress", {})
    require(progress.get("completed_phase_count") == 2, "completed phase count mismatch", errors)
    require(progress.get("total_phase_count") == 3, "total phase count mismatch", errors)
    require(progress.get("derived_percent_bps") == 6667, "derived percent bps mismatch", errors)
    require(progress.get("derived_percent_label") == "66.67%", "derived percent label mismatch", errors)
    require(progress.get("s11_p1_performed") is True, "S11-P1 must be true", errors)
    require(progress.get("s11_p2_performed") is True, "S11-P2 must be true", errors)
    require(progress.get("s11_p3_performed") is False, "S11-P3 must be false", errors)
    require(progress.get("stage11_review_performed") is False, "Stage 11 review must be false", errors)

    summary = manifest.get("source_check_board_summary", {})
    require(rows == legacy["rows"], "v014 rows must match legacy S11-P2 public-safe rows", errors)
    require(summary.get("matrix_row_count") == len(legacy["rows"]) == 13, "matrix row count mismatch", errors)
    require(summary.get("required_columns") == list(REQUIRED_BOARD_COLUMNS), "required columns mismatch", errors)
    require(summary.get("required_column_count") == 11, "required column count mismatch", errors)
    require(summary.get("required_columns_covered") is True, "required columns coverage mismatch", errors)
    require(summary.get("allowed_statuses") == list(ALLOWED_BOARD_STATUSES), "allowed statuses mismatch", errors)
    require(summary.get("allowed_status_count") == 5, "allowed status count mismatch", errors)
    require(summary.get("status_counts") == legacy["status_counts"], "status counts mismatch", errors)
    require(sum(summary.get("status_counts", {}).values()) == 13, "status count total mismatch", errors)
    require(summary.get("html_export_count") == 1, "HTML export count mismatch", errors)
    require(summary.get("search_input_count") == 1, "search input count mismatch", errors)
    require(summary.get("search_feedback_enabled") is True, "search feedback mismatch", errors)
    require(summary.get("status_click_detail_enabled") is True, "status detail mismatch", errors)
    require(summary.get("status_change_action_count") == 5, "status action count mismatch", errors)
    require(summary.get("status_change_control_event_enabled") is True, "status control-event mismatch", errors)
    require(summary.get("control_event_panel_count") == 1, "control event panel mismatch", errors)
    require(summary.get("blue_gray_surface_dominant") is True, "blue-gray style mismatch", errors)
    require(summary.get("status_badges_only") is True, "status badge style mismatch", errors)
    require(summary.get("large_yellow_surface_count") == 0, "large yellow surface count mismatch", errors)
    require(summary.get("km_brand_mark_present") is True, "KM brand must be present", errors)
    require(summary.get("single_k_brand_mark_present") is False, "single K brand must be false", errors)
    require(summary.get("formal_report_count") == 0, "formal report count mismatch", errors)
    require(summary.get("business_decision_basis_count") == 0, "business decision basis count mismatch", errors)
    require(summary.get("raw_business_value_count") == 0, "raw business value count mismatch", errors)
    require(summary.get("private_file_reference_count") == 0, "private file reference count mismatch", errors)

    for row in rows:
        require(row.get("stage_phase") == "S11-P2", f"row {row.get('row_id')} phase mismatch", errors)
        require(row.get("status") in ALLOWED_BOARD_STATUSES, f"row {row.get('row_id')} status invalid", errors)
        require(row.get("contains_raw_business_values") is False, f"row {row.get('row_id')} raw value flag mismatch", errors)
        require(row.get("raw_layer_write_allowed") is False, f"row {row.get('row_id')} raw write flag mismatch", errors)
        require(row.get("formal_report_allowed") is False, f"row {row.get('row_id')} formal flag mismatch", errors)
        require(
            row.get("business_decision_basis_allowed") is False,
            f"row {row.get('row_id')} decision-basis flag mismatch",
            errors,
        )

    v14 = manifest.get("v14_html_uiux_baseline", {})
    for key, expected in baseline.items():
        if key in {
            "implementation_reflects_search_feedback",
            "implementation_reflects_status_change_feedback",
            "implementation_reflects_status_detail_preview",
        }:
            continue
        require(v14.get(key) == expected, f"v14 baseline {key} mismatch", errors)
    require(v14.get("taskpack_html_requirement_read") is True, "HTML requirement read mismatch", errors)
    require(v14.get("audit_file_count") == 6, "v14 audit file count mismatch", errors)
    require(v14.get("audit_control_row_count") == 54, "v14 audit control count mismatch", errors)
    require(v14.get("audit_pass_count") == 54, "v14 audit pass count mismatch", errors)
    require(v14.get("audit_warn_count") == 0, "v14 audit warn count mismatch", errors)
    require(v14.get("audit_fail_count") == 0, "v14 audit fail count mismatch", errors)
    require(v14.get("implementation_reflects_search_feedback") is True, "search reflection mismatch", errors)
    require(v14.get("implementation_reflects_status_change_feedback") is True, "status reflection mismatch", errors)
    require(v14.get("implementation_reflects_status_detail_preview") is True, "detail reflection mismatch", errors)

    require('id="sourceSearch"' in html_text, "HTML source search input missing", errors)
    require("function filterRows" in html_text, "HTML filterRows function missing", errors)
    require('id="filterFeedback"' in html_text, "HTML filter feedback missing", errors)
    require('id="statusFilter"' in html_text, "HTML status filter missing", errors)
    require("data-status-option" in html_text, "HTML status action buttons missing", errors)
    require("controlEvents.push" in html_text, "HTML control event log mutation missing", errors)
    require("rawLayerWrite: false" in html_text, "HTML raw write false event missing", errors)
    require("function showDetail" in html_text, "HTML status detail function missing", errors)
    require("data-impact" in html_text and "data-rule" in html_text and "data-next" in html_text, "HTML detail data missing", errors)
    require('id="controlEventLog"' in html_text, "HTML control event panel missing", errors)
    require("项目成本详情" in html_text and "正式报告" in html_text, "HTML boundary text missing", errors)

    phase = manifest.get("phase_boundaries", {})
    require(phase.get("s11_p1_home_navigation_dependency_included") is True, "S11-P1 dependency flag mismatch", errors)
    require(phase.get("s11_p2_source_check_board_scope_included") is True, "S11-P2 scope flag mismatch", errors)
    for key in PHASE_FALSE_KEYS:
        require(phase.get(key) is False, f"phase_boundaries.{key} must be false", errors)

    quality = manifest.get("quality_gate", {})
    require(quality.get("current_data_quality_grade") == "Q4", "quality grade mismatch", errors)
    require(quality.get("current_report_grade") == "D", "report grade mismatch", errors)
    require(quality.get("release_permission") == "blocked", "release permission mismatch", errors)
    require(quality.get("pending_reconciliation_count") == 12, "pending reconciliation count mismatch", errors)
    require(quality.get("confirmed_resolution_count") == 0, "confirmed resolution count mismatch", errors)
    require(quality.get("source_check_board_export_allowed") is True, "source check board export flag mismatch", errors)
    for key in QUALITY_FALSE_KEYS:
        require(quality.get(key) is False, f"quality_gate.{key} must be false", errors)

    upload = manifest.get("github_upload", {})
    require(upload.get("github_upload_ready_next_gate") is False, "upload ready must stay false", errors)
    require(upload.get("github_upload_deferred_until_v014_stage1_18_complete") is True, "upload must be deferred", errors)
    require(upload.get("github_upload_performed") is False, "upload performed must be false", errors)
    require(
        upload.get("github_upload_status") == "not_uploaded_deferred_until_v014_stage1_18_complete",
        "upload status mismatch",
        errors,
    )

    raw = manifest.get("raw_data_boundary", {})
    require(raw.get("raw_inbox_role") == "user_finance_raw_private_inbox", "raw role mismatch", errors)
    require(raw.get("raw_inbox_read_allowed_only_when_phase_requires") is True, "raw read policy mismatch", errors)
    for key in RAW_BOUNDARY_FALSE_KEYS:
        require(raw.get(key) is False, f"raw_data_boundary.{key} must be false", errors)
    require(raw.get("private_runtime_output_dir") == "KMFA/.codex_private_runtime/", "runtime dir mismatch", errors)

    safety = manifest.get("public_repo_safety", {})
    for key in PUBLIC_SAFETY_FALSE_KEYS:
        require(safety.get(key) is False, f"public_repo_safety.{key} must be false", errors)

    hard_blocks = manifest.get("hard_blocks", [])
    require(isinstance(hard_blocks, list), "hard_blocks must be a list", errors)
    for block in REQUIRED_HARD_BLOCKS:
        require(block in hard_blocks, f"missing hard block: {block}", errors)
    require(manifest.get("hard_block_count") == len(REQUIRED_HARD_BLOCKS), "hard block count mismatch", errors)
    require(manifest.get("next_required_step") == NEXT_REQUIRED_STEP, "next_required_step mismatch", errors)

    _check_artifact_refs(manifest, errors)
    for evidence in (MANIFEST_PATH, ROWS_PATH, HTML_OUTPUT_PATH, REPORT_PATH, TEST_RESULTS_PATH, RISK_REGISTER_PATH, ROLLBACK_PATH):
        check_public_evidence_text(evidence, errors)

    test_text = TEST_RESULTS_PATH.read_text(encoding="utf-8", errors="ignore") if TEST_RESULTS_PATH.exists() else ""
    require("pending_final_validation" not in test_text, "test results must not remain pending", errors)
    require("completed_validated_local_only_no_go_upload_deferred" in test_text, "test results status missing", errors)
    require("check_v014_s11_p2_source_check_board.py" in test_text, "S11-P2 validator evidence missing", errors)
    require("test_v014_s11_p2_source_check_board" in test_text, "S11-P2 unit test evidence missing", errors)
    require("S11-P3, Stage 11 overall review, GitHub upload" in test_text, "phase boundary evidence missing", errors)

    reviewed_head = str(manifest.get("reviewed_head", ""))
    require(
        len(reviewed_head) == 40 and all(character in "0123456789abcdef" for character in reviewed_head),
        "reviewed_head must be a lowercase 40-character git SHA",
        errors,
    )
    require(manifest.get("branch") == git_output(["branch", "--show-current"]), "branch mismatch", errors)
    require(manifest.get("remote") == git_output(["remote", "get-url", "origin"]), "remote mismatch", errors)

    if errors:
        raise ValidationError("; ".join(errors))
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA v0.1.4 S11-P2 source check board evidence.")
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    args = parser.parse_args(argv)
    try:
        manifest = validate_v014_s11_p2_source_check_board(args.manifest)
    except (OSError, json.JSONDecodeError, ValidationError, RuntimeError) as exc:
        print(f"FAIL: KMFA v0.1.4 S11-P2 source check board validation failed ({exc})")
        return 1

    summary = manifest["source_check_board_summary"]
    baseline = manifest["v14_html_uiux_baseline"]
    print(
        "PASS: KMFA v0.1.4 S11-P2 source check board validated "
        f"(matrix_rows={summary['matrix_row_count']}, "
        f"columns={summary['required_column_count']}, "
        f"statuses={summary['allowed_status_count']}, "
        f"v14_audit_rows={baseline['audit_control_row_count']}, "
        "search=true, status_change=true, detail=true, "
        "s11_p3=false, stage11_review=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
