#!/usr/bin/env python3
"""Validate KMFA v0.1.4 S11-P3 public-safe project cost page evidence."""

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

from KMFA.tools.project_cost_page_runtime import REQUIRED_COST_CATEGORIES, REQUIRED_PROJECT_TABLE_COLUMNS
from KMFA.tools.v014_s11_p3_project_cost_page import (
    ACCEPTANCE_ID,
    HTML_OUTPUT_PATH,
    MANIFEST_PATH,
    NEXT_REQUIRED_STEP,
    PHASE_SCOPE,
    PROJECTS_PATH,
    REPORT_PATH,
    RISK_REGISTER_PATH,
    ROLLBACK_PATH,
    SCHEMA_VERSION,
    TASK_ID,
    TEST_RESULTS_PATH,
    _phase_boundaries,
    _public_repo_safety,
    _quality_gate,
    _raw_boundary,
    load_v14_html_uiux_baseline,
    validate_legacy_s11_p3_artifacts,
    validate_s11_p2_dependency,
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
    "quality_grade_bypass_forbidden",
    "raw_data_mutation_forbidden",
    "raw_value_publication_forbidden",
    "field_header_plaintext_publication_forbidden",
    "formal_report_release_blocked",
    "complete_trusted_report_display_blocked",
    "business_decision_basis_blocked",
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
    "connector_" + "token:",
    "connector_" + "password:",
    "api" + "_key:",
    "private" + "_key:",
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
    re.compile(r"(?i)(password|passwd|secret|api" + r"_key|token)\s*=\s*[^\s,;]{8,}"),
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
        "s11_p2_manifest",
        "legacy_manifest",
        "legacy_projects",
        "legacy_html",
        "v14_source_package_manifest",
        "v14_html_entry",
        "v14_html_audit_script",
        "v14_html_audit_report",
        "v14_roadmap",
        "v14_taskpack",
        "manifest",
        "projects",
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


def validate_v014_s11_p3_project_cost_page(manifest_path: Path = MANIFEST_PATH) -> dict[str, Any]:
    errors: list[str] = []
    manifest = read_json(manifest_path)
    s11_p2 = validate_s11_p2_dependency()
    legacy = validate_legacy_s11_p3_artifacts()
    baseline = load_v14_html_uiux_baseline()
    projects = read_jsonl(PROJECTS_PATH)
    html_text = HTML_OUTPUT_PATH.read_text(encoding="utf-8") if HTML_OUTPUT_PATH.exists() else ""

    require(manifest.get("schema_version") == SCHEMA_VERSION, "manifest schema mismatch", errors)
    require(manifest.get("project_id") == "KMFA", "project_id mismatch", errors)
    require(manifest.get("version") == "0.1.4", "version mismatch", errors)
    require(manifest.get("stage_id") == "S11", "stage_id must be S11", errors)
    require(manifest.get("phase_id") == "S11-P3", "phase_id must be S11-P3", errors)
    require(manifest.get("phase_scope") == PHASE_SCOPE, "phase scope mismatch", errors)
    require(manifest.get("task_id") == TASK_ID, "task_id mismatch", errors)
    require(
        manifest.get("status") == "completed_validated_local_only_no_go_upload_deferred_project_cost_page_locked",
        "status mismatch",
        errors,
    )
    require(manifest.get("completed_task_ids") == ["S11P3T01", "S11P3T02", "S11P3T03"], "tasks mismatch", errors)
    require(manifest.get("acceptance_ids") == [ACCEPTANCE_ID], "acceptance id mismatch", errors)
    require(manifest.get("s11_p2_dependency_validated") is True, "S11-P2 dependency flag mismatch", errors)
    require(s11_p2.get("phase_id") == "S11-P2", "S11-P2 dependency did not validate S11-P2", errors)
    require(manifest.get("legacy_s11_p3_dependency_validated") is True, "legacy S11-P3 flag mismatch", errors)

    progress = manifest.get("stage11_phase_progress", {})
    require(progress.get("completed_phase_count") == 3, "completed phase count mismatch", errors)
    require(progress.get("total_phase_count") == 3, "total phase count mismatch", errors)
    require(progress.get("derived_percent_bps") == 10000, "derived percent bps mismatch", errors)
    require(progress.get("derived_percent_label") == "100.00%", "derived percent label mismatch", errors)
    require(progress.get("s11_p1_performed") is True, "S11-P1 must be true", errors)
    require(progress.get("s11_p2_performed") is True, "S11-P2 must be true", errors)
    require(progress.get("s11_p3_performed") is True, "S11-P3 must be true", errors)
    require(progress.get("stage11_review_performed") is False, "Stage 11 review must be false", errors)

    summary = manifest.get("project_cost_page_summary", {})
    require(projects == legacy["projects"], "v014 projects must match legacy S11-P3 public-safe projects", errors)
    require(summary.get("project_row_count") == len(projects) == 4, "project row count mismatch", errors)
    require(summary.get("project_list_columns") == list(REQUIRED_PROJECT_TABLE_COLUMNS), "project columns mismatch", errors)
    require(summary.get("project_list_column_count") == 7, "project column count mismatch", errors)
    require(summary.get("cost_categories") == list(REQUIRED_COST_CATEGORIES), "cost categories mismatch", errors)
    require(summary.get("cost_category_count") == 9, "cost category count mismatch", errors)
    require(summary.get("margin_record_count") == 4, "margin record count mismatch", errors)
    require(summary.get("pending_reconciliation_count") == 12, "pending reconciliation count mismatch", errors)
    require(summary.get("pending_action_total") == 12, "pending action total mismatch", errors)
    require(summary.get("html_export_count") == 1, "HTML export count mismatch", errors)
    require(summary.get("project_detail_click_enabled") is True, "project detail click mismatch", errors)
    require(summary.get("source_evidence_panel_enabled") is True, "source evidence panel mismatch", errors)
    require(summary.get("pending_action_panel_enabled") is True, "pending action panel mismatch", errors)
    require(summary.get("report_preview_direct_view_allowed") is True, "report preview mismatch", errors)
    require(summary.get("report_section_switch_enabled") is True, "report section switch mismatch", errors)
    require(summary.get("report_section_button_count") == 4, "report section button count mismatch", errors)
    require(summary.get("appendix_export_feedback_enabled") is True, "appendix export mismatch", errors)
    require(summary.get("print_save_feedback_enabled") is True, "print/save mismatch", errors)
    require(summary.get("quality_gate_feedback_panel_count") == 1, "quality gate panel mismatch", errors)
    require(summary.get("control_event_panel_count") == 1, "control event panel mismatch", errors)
    require(summary.get("report_grade_visible") == "D", "report grade mismatch", errors)
    require(summary.get("quality_grade_bypass_allowed") is False, "quality bypass mismatch", errors)
    require(summary.get("blue_gray_surface_dominant") is True, "blue-gray style mismatch", errors)
    require(summary.get("large_yellow_surface_count") == 0, "large yellow surface count mismatch", errors)
    require(summary.get("km_brand_mark_present") is True, "KM brand must be present", errors)
    require(summary.get("single_k_brand_mark_present") is False, "single K brand must be false", errors)
    require(summary.get("formal_report_count") == 0, "formal report count mismatch", errors)
    require(summary.get("business_decision_basis_count") == 0, "business decision basis count mismatch", errors)
    require(summary.get("raw_business_value_count") == 0, "raw business value count mismatch", errors)
    require(summary.get("private_file_reference_count") == 0, "private file reference count mismatch", errors)

    for project in projects:
        require(project.get("stage_phase") == "S11-P3", f"project {project.get('project_order')} phase mismatch", errors)
        require(project.get("contains_raw_business_values") is False, "project raw value flag mismatch", errors)
        require(project.get("raw_layer_write_allowed") is False, "project raw write flag mismatch", errors)
        require(project.get("formal_report_allowed") is False, "project formal flag mismatch", errors)
        require(project.get("business_decision_basis_allowed") is False, "project decision-basis flag mismatch", errors)
        require(project.get("quality_grade_bypass_allowed") is False, "project quality bypass flag mismatch", errors)

    v14 = manifest.get("v14_html_uiux_baseline", {})
    for key, expected in baseline.items():
        if key.startswith("implementation_reflects_"):
            continue
        require(v14.get(key) == expected, f"v14 baseline {key} mismatch", errors)
    require(v14.get("audit_file_count") == 6, "v14 audit file count mismatch", errors)
    require(v14.get("audit_control_row_count") == 54, "v14 audit control count mismatch", errors)
    require(v14.get("audit_pass_count") == 54, "v14 audit pass count mismatch", errors)
    require(v14.get("audit_warn_count") == 0, "v14 audit warn count mismatch", errors)
    require(v14.get("audit_fail_count") == 0, "v14 audit fail count mismatch", errors)
    require(v14.get("implementation_reflects_project_detail_click") is True, "detail reflection mismatch", errors)
    require(v14.get("implementation_reflects_report_section_switch") is True, "section reflection mismatch", errors)
    require(v14.get("implementation_reflects_appendix_export_feedback") is True, "export reflection mismatch", errors)
    require(v14.get("implementation_reflects_print_save_feedback") is True, "print reflection mismatch", errors)
    require(v14.get("implementation_reflects_quality_gate_block") is True, "quality gate reflection mismatch", errors)

    require('id="projectSearch"' in html_text, "HTML project search input missing", errors)
    require("function selectProject" in html_text, "HTML selectProject function missing", errors)
    require("function switchReportSection" in html_text, "HTML switchReportSection function missing", errors)
    require("function exportAppendix" in html_text, "HTML exportAppendix function missing", errors)
    require("function printSavePreview" in html_text, "HTML printSavePreview function missing", errors)
    require("controlEvents.push" in html_text, "HTML control event log mutation missing", errors)
    require("rawLayerWrite: false" in html_text, "HTML raw write false event missing", errors)
    require("qualityGateBypass: false" in html_text, "HTML quality bypass false event missing", errors)
    require('id="qualityGateFeedback"' in html_text, "HTML quality gate feedback missing", errors)
    require('id="controlEventLog"' in html_text, "HTML control event panel missing", errors)
    for text in ("项目列表", "项目详情", "来源证据", "待处理事项", "报告预览", "报告等级 D", "不可绕过质量等级"):
        require(text in html_text, f"HTML missing required text: {text}", errors)
    for forbidden in ("private_ref://", "source_ref://", "validator", "manifest", "metadata", ".zip", ".xlsx", ".xls", ".pdf", ".sqlite", ".db"):
        require(forbidden not in html_text.lower(), f"HTML exposes forbidden marker {forbidden}", errors)
    require("yellow" not in html_text.lower(), "HTML must not use yellow surface", errors)

    phase = manifest.get("phase_boundaries", {})
    require(phase.get("s11_p1_home_navigation_dependency_included") is True, "S11-P1 dependency flag mismatch", errors)
    require(phase.get("s11_p2_source_check_board_dependency_included") is True, "S11-P2 dependency flag mismatch", errors)
    require(phase.get("s11_p3_project_cost_page_scope_included") is True, "S11-P3 scope flag mismatch", errors)
    for key in PHASE_FALSE_KEYS:
        require(phase.get(key) is False, f"phase boundary {key} must be false", errors)

    quality = manifest.get("quality_gate", {})
    require(quality.get("project_cost_page_export_allowed") is True, "project cost page export flag mismatch", errors)
    require(quality.get("report_preview_direct_view_allowed") is True, "report preview flag mismatch", errors)
    require(quality.get("current_report_grade") == "D", "current report grade mismatch", errors)
    require(quality.get("pending_reconciliation_count") == 12, "pending reconciliation gate mismatch", errors)
    for key in QUALITY_FALSE_KEYS:
        require(quality.get(key) is False, f"quality gate {key} must be false", errors)

    raw = manifest.get("raw_data_boundary", {})
    for key in RAW_BOUNDARY_FALSE_KEYS:
        require(raw.get(key) is False, f"raw boundary {key} must be false", errors)

    public = manifest.get("public_repo_safety", {})
    for key in PUBLIC_SAFETY_FALSE_KEYS:
        require(public.get(key) is False, f"public repo safety {key} must be false", errors)

    upload = manifest.get("github_upload", {})
    require(upload.get("github_upload_performed") is False, "GitHub upload must be false", errors)
    require(upload.get("github_upload_ready_next_gate") is False, "GitHub ready gate must be false", errors)
    require(upload.get("github_upload_deferred_until_v014_stage1_18_complete") is True, "GitHub deferral mismatch", errors)

    hard_blocks = set(manifest.get("hard_blocks", []))
    for block in REQUIRED_HARD_BLOCKS:
        require(block in hard_blocks, f"missing hard block: {block}", errors)
    require(manifest.get("hard_block_count") == len(manifest.get("hard_blocks", [])), "hard block count mismatch", errors)
    require(manifest.get("next_required_step") == NEXT_REQUIRED_STEP, "next step mismatch", errors)
    require(manifest.get("reviewed_head") == git_output(["rev-parse", "HEAD"]), "reviewed head is stale", errors)
    require(manifest.get("branch") == git_output(["branch", "--show-current"]), "branch mismatch", errors)
    require(manifest.get("remote") == git_output(["remote", "get-url", "origin"]), "remote mismatch", errors)

    _check_artifact_refs(manifest, errors)
    for path in (REPORT_PATH, TEST_RESULTS_PATH, RISK_REGISTER_PATH, ROLLBACK_PATH):
        check_public_evidence_text(path, errors)
    test_text = TEST_RESULTS_PATH.read_text(encoding="utf-8") if TEST_RESULTS_PATH.exists() else ""
    require("Stage 11 overall review, GitHub upload" in test_text, "phase boundary evidence missing", errors)
    require("PENDING" not in test_text, "test results must not contain pending marker", errors)

    if errors:
        raise ValidationError("\n".join(errors))
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA v0.1.4 S11-P3 project cost page evidence.")
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    args = parser.parse_args(argv)
    manifest = validate_v014_s11_p3_project_cost_page(args.manifest)
    summary = manifest["project_cost_page_summary"]
    baseline = manifest["v14_html_uiux_baseline"]
    print(
        "PASS: KMFA v0.1.4 S11-P3 project cost page validated "
        f"(projects={summary['project_row_count']}, "
        f"columns={summary['project_list_column_count']}, "
        f"cost_categories={summary['cost_category_count']}, "
        f"pending_reconciliations={summary['pending_reconciliation_count']}, "
        f"v14_audit_rows={baseline['audit_control_row_count']}, "
        "detail=true, report_preview=true, quality_bypass=false, "
        "stage11_review=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
