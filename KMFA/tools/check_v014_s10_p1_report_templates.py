#!/usr/bin/env python3
"""Validate KMFA v0.1.4 S10-P1 report template evidence."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any

from KMFA.tools.v014_s10_p1_report_templates import (
    ACCEPTANCE_ID,
    MANIFEST_PATH,
    NEXT_REQUIRED_STEP,
    PHASE_SCOPE,
    REPORT_PATH,
    RISK_REGISTER_PATH,
    ROLLBACK_PATH,
    SCHEMA_VERSION,
    TASK_ID,
    TEST_RESULTS_PATH,
    validate_legacy_s10_p1_artifacts,
    validate_stage9_dependency,
    validate_v14_html_uiux_baseline,
)


PUBLIC_SAFETY_FALSE_KEYS = (
    "protected_source_payload_committed",
    "zip_committed",
    "excel_workbook_committed",
    "wps_native_file_committed",
    "redcircle_native_file_committed",
    "csv_committed",
    "pdf_committed",
    "private_csv_committed",
    "sqlite_or_db_committed",
    "credentials_committed",
    "connector_secret_committed",
    "field_plaintext_committed",
    "source_header_plaintext_committed",
    "raw_file_names_committed",
    "raw_file_hashes_committed",
    "tab_labels_committed",
    "zip_member_names_committed",
    "source_record_payload_committed",
    "normalized_source_values_committed",
    "business_amount_values_committed",
    "project_or_customer_plaintext_committed",
    "formal_report_committed",
    "report_export_committed",
    "html_report_export_committed",
    "spreadsheet_report_export_committed",
)
RAW_BOUNDARY_FALSE_KEYS = (
    "raw_inbox_read_required_by_this_phase",
    "raw_inbox_read_by_this_phase",
    "raw_inbox_listed_by_this_phase",
    "raw_inbox_inventory_by_this_phase",
    "raw_inbox_stat_by_this_phase",
    "raw_inbox_hashed_by_this_phase",
    "raw_inbox_modified_by_this_phase",
    "raw_inbox_deleted_by_this_phase",
    "raw_inbox_moved_by_this_phase",
    "raw_inbox_renamed_by_this_phase",
    "raw_inbox_overwritten_by_this_phase",
    "raw_inbox_written_by_this_phase",
    "raw_inbox_mutated_by_this_phase",
)
REQUIRED_HARD_BLOCKS = (
    "raw_data_mutation_forbidden",
    "raw_value_publication_forbidden",
    "field_header_plaintext_publication_forbidden",
    "report_templates_structural_only",
    "report_runtime_not_performed",
    "trusted_grade_assignment_blocked",
    "s10_p2_report_grade_runtime_not_performed",
    "s10_p3_report_export_not_performed",
    "stage10_review_not_performed",
    "formal_report_release_blocked",
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
    "sheet_name",
    "row_value",
    "cell_value",
    "business_data",
    "bank_statement",
    "contract_full_text",
    "salary_detail",
    "tax_filing",
    "connector_token",
    "connector_password",
    "api_key",
    "private_key",
    "-----" "BEGIN",
    "s" "k-",
    "project_name_plaintext",
    "customer_name_plaintext",
    "counterparty_plaintext",
    "company_entity_plaintext",
    "account_number",
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


def validate_v014_s10_p1_report_templates(manifest_path: Path = MANIFEST_PATH) -> dict[str, Any]:
    errors: list[str] = []
    manifest = read_json(manifest_path)
    s09 = validate_stage9_dependency()
    legacy = validate_legacy_s10_p1_artifacts()
    html = validate_v14_html_uiux_baseline()

    require(manifest.get("schema_version") == SCHEMA_VERSION, "manifest schema mismatch", errors)
    require(manifest.get("project_id") == "KMFA", "project_id mismatch", errors)
    require(manifest.get("version") == "0.1.4", "version mismatch", errors)
    require(manifest.get("stage_id") == "S10", "stage_id must be S10", errors)
    require(manifest.get("phase_id") == "S10-P1", "phase_id must be S10-P1", errors)
    require(manifest.get("phase_scope") == PHASE_SCOPE, "phase scope mismatch", errors)
    require(manifest.get("task_id") == TASK_ID, "task_id mismatch", errors)
    require(
        manifest.get("status") == "completed_validated_local_only_no_go_upload_deferred_report_templates_locked",
        "status mismatch",
        errors,
    )
    require(manifest.get("completed_task_ids") == ["S10PAT01", "S10PAT02", "S10PAT03"], "tasks mismatch", errors)
    require(manifest.get("acceptance_ids") == [ACCEPTANCE_ID], "acceptance id mismatch", errors)
    require(manifest.get("s09_stage_review_dependency_validated") is True, "S09 dependency flag mismatch", errors)
    require(s09.get("stage_id") == "S09", "S09 dependency did not validate", errors)
    require(s09.get("stage_review_performed") is True, "S09 review flag mismatch", errors)
    require(manifest.get("legacy_s10_p1_dependency_validated") is True, "legacy S10-P1 flag mismatch", errors)
    require(manifest.get("v14_html_uiux_dependency_validated") is True, "v1.4 HTML/UIUX flag mismatch", errors)

    progress = manifest.get("stage10_phase_progress", {})
    require(progress.get("completed_phase_count") == 1, "completed phase count mismatch", errors)
    require(progress.get("total_phase_count") == 3, "total phase count mismatch", errors)
    require(progress.get("derived_percent_bps") == 3333, "derived percent bps mismatch", errors)
    require(progress.get("derived_percent_label") == "33.33%", "derived percent label mismatch", errors)
    require(progress.get("s10_p1_performed") is True, "S10-P1 must be performed", errors)
    require(progress.get("s10_p2_performed") is False, "S10-P2 must not be performed", errors)
    require(progress.get("s10_p3_performed") is False, "S10-P3 must not be performed", errors)
    require(progress.get("stage10_review_performed") is False, "Stage 10 review must not be performed", errors)

    summary = manifest.get("report_template_summary", {})
    expected_summary = {
        "template_count": 2,
        "section_count": 11,
        "project_cost_section_count": 4,
        "business_overview_section_count": 7,
        "pending_reconciliation_count": 12,
        "formal_report_count": 0,
        "export_artifact_count": 0,
    }
    for key, expected in expected_summary.items():
        require(summary.get(key) == expected, f"summary.{key} mismatch", errors)
        require(summary.get(key) == legacy.get(key), f"legacy summary mismatch for {key}", errors)
    require(summary.get("required_template_ids") == legacy["required_template_ids"], "template ids mismatch", errors)
    require(
        summary.get("required_project_cost_section_titles") == legacy["required_project_cost_section_titles"],
        "project cost section titles mismatch",
        errors,
    )
    require(
        summary.get("required_business_overview_section_titles") == legacy["required_business_overview_section_titles"],
        "business overview section titles mismatch",
        errors,
    )

    policy = manifest.get("report_template_policy", {})
    for key in (
        "formal_report_allowed_count",
        "trusted_grade_assignment_allowed_count",
        "report_runtime_scope_count",
        "s10_p2_scope_count",
        "s10_p3_scope_count",
        "ui_scope_count",
        "external_connector_scope_count",
        "internal_title_visible_count",
        "raw_business_values_allowed_count",
        "public_numeric_values_allowed_count",
        "quality_gate_false_count",
        "stage_scope_false_count",
        "public_safety_false_count",
    ):
        require(policy.get(key) == legacy.get(key), f"legacy policy mismatch for {key}", errors)
    require(policy.get("formal_report_allowed") is False, "formal report must be false", errors)
    require(policy.get("trusted_grade_assignment_allowed") is False, "trusted grade must be false", errors)
    require(policy.get("formal_report_allowed_count") == 0, "formal report count mismatch", errors)
    require(policy.get("report_runtime_scope_count") == 0, "report runtime scope count mismatch", errors)
    require(policy.get("s10_p2_scope_count") == 0, "S10-P2 scope count mismatch", errors)
    require(policy.get("s10_p3_scope_count") == 0, "S10-P3 scope count mismatch", errors)

    html_policy = manifest.get("v14_html_uiux_baseline", {})
    for key in ("html_file_count", "control_row_count", "pass_count", "warn_count", "fail_count"):
        require(html_policy.get(key) == html.get(key), f"v1.4 HTML/UIUX {key} mismatch", errors)
    require(html_policy.get("html_file_count") == 6, "v1.4 HTML file count mismatch", errors)
    require(html_policy.get("control_row_count") == 54, "v1.4 control row count mismatch", errors)
    require(html_policy.get("pass_count") == 54, "v1.4 pass count mismatch", errors)
    require(html_policy.get("warn_count") == 0, "v1.4 warn count mismatch", errors)
    require(html_policy.get("fail_count") == 0, "v1.4 fail count mismatch", errors)
    require(html_policy.get("report_chapter_switch_required") is True, "chapter switch requirement missing", errors)
    require(html_policy.get("report_csv_download_required") is True, "CSV download requirement missing", errors)
    require(html_policy.get("report_print_or_save_required") is True, "print/save requirement missing", errors)
    require(html_policy.get("real_frontend_runtime_performed") is False, "UI runtime must not be performed", errors)
    require(html_policy.get("html_export_generated_by_this_phase") is False, "HTML export must not be generated", errors)
    for ref in html_policy.get("refs", {}).values():
        require(Path(ref).exists(), f"missing v1.4 HTML/UIUX ref: {ref}", errors)

    phase = manifest.get("phase_boundaries", {})
    require(phase.get("s10_p1_report_templates_scope_included") is True, "S10-P1 scope flag mismatch", errors)
    for key in (
        "s10_p2_report_grade_runtime_scope_included",
        "s10_p3_report_export_scope_included",
        "stage10_review_scope_included",
        "lineage_full_check_scope_included",
        "formal_report_scope_included",
        "ui_runtime_scope_included",
        "html_export_scope_included",
        "csv_export_scope_included",
        "pdf_export_scope_included",
        "external_connector_scope_included",
        "github_upload_scope_included",
        "app_reinstall_scope_included",
    ):
        require(phase.get(key) is False, f"phase_boundaries.{key} must be false", errors)

    quality = manifest.get("quality_gate", {})
    require(quality.get("current_data_quality_grade") == "Q4", "quality grade mismatch", errors)
    require(quality.get("current_report_grade") == "D", "report grade mismatch", errors)
    require(quality.get("release_permission") == "blocked", "release permission mismatch", errors)
    require(quality.get("pending_reconciliation_count") == 12, "pending reconciliation count mismatch", errors)
    for key in (
        "formal_report_allowed",
        "trusted_grade_assignment_allowed",
        "business_decision_basis_allowed",
        "business_execution_allowed",
        "delivery_allowed",
        "raw_layer_write_allowed",
        "automatic_external_action_allowed",
    ):
        require(quality.get(key) is False, f"quality_gate.{key} must be false", errors)
    require(quality.get("formal_report_allowed_count") == 0, "formal report count mismatch", errors)

    upload = manifest.get("github_upload", {})
    require(upload.get("github_upload_ready_next_gate") is False, "upload ready must be false", errors)
    require(
        upload.get("github_upload_deferred_until_v014_stage1_18_complete") is True,
        "upload deferred flag mismatch",
        errors,
    )
    require(upload.get("github_upload_performed") is False, "upload performed must be false", errors)
    require(
        upload.get("github_upload_status") == "not_uploaded_deferred_until_v014_stage1_18_complete",
        "upload status mismatch",
        errors,
    )

    raw = manifest.get("raw_data_boundary", {})
    require(raw.get("raw_inbox_ref") == "operator-designated raw/private inbox outside repository", "raw ref mismatch", errors)
    for key in RAW_BOUNDARY_FALSE_KEYS:
        require(raw.get(key) is False, f"raw_data_boundary.{key} must be false", errors)
    require(raw.get("private_runtime_output_dir") == "KMFA/.codex_private_runtime/", "private runtime mismatch", errors)

    safety = manifest.get("public_repo_safety", {})
    for key in PUBLIC_SAFETY_FALSE_KEYS:
        require(safety.get(key) is False, f"public_repo_safety.{key} must be false", errors)

    hard_blocks = manifest.get("hard_blocks", [])
    require(isinstance(hard_blocks, list), "hard_blocks must be a list", errors)
    for block in REQUIRED_HARD_BLOCKS:
        require(block in hard_blocks, f"missing hard block: {block}", errors)
    require(manifest.get("hard_block_count") == len(REQUIRED_HARD_BLOCKS), "hard block count mismatch", errors)
    require(manifest.get("next_required_step") == NEXT_REQUIRED_STEP, "next step mismatch", errors)

    artifact_refs = manifest.get("artifact_refs", {})
    for key in (
        "legacy_manifest",
        "legacy_templates",
        "legacy_sections",
        "legacy_stage_manifest",
        "manifest",
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
    for evidence in (MANIFEST_PATH, REPORT_PATH, TEST_RESULTS_PATH, RISK_REGISTER_PATH, ROLLBACK_PATH):
        check_public_evidence_text(evidence, errors)

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

    return {
        "project_id": manifest["project_id"],
        "version": manifest["version"],
        "stage_id": manifest["stage_id"],
        "phase_id": manifest["phase_id"],
        "phase_scope": manifest["phase_scope"],
        "status": manifest["status"],
        "template_count": summary["template_count"],
        "section_count": summary["section_count"],
        "project_cost_section_count": summary["project_cost_section_count"],
        "business_overview_section_count": summary["business_overview_section_count"],
        "pending_reconciliation_count": summary["pending_reconciliation_count"],
        "formal_report_count": summary["formal_report_count"],
        "export_artifact_count": summary["export_artifact_count"],
        "v14_html_uiux_audit_fail_count": html_policy["fail_count"],
        "v14_html_uiux_audit_pass_count": html_policy["pass_count"],
        "formal_report_allowed": quality["formal_report_allowed"],
        "trusted_grade_assignment_allowed": quality["trusted_grade_assignment_allowed"],
        "report_runtime_scope_included": phase["s10_p2_report_grade_runtime_scope_included"],
        "s10_p2_performed": progress["s10_p2_performed"],
        "s10_p3_performed": progress["s10_p3_performed"],
        "stage10_review_performed": progress["stage10_review_performed"],
        "github_upload_performed": upload["github_upload_performed"],
        "github_upload_deferred_until_v014_stage1_18_complete": upload[
            "github_upload_deferred_until_v014_stage1_18_complete"
        ],
        "raw_inbox_read_performed": raw["raw_inbox_read_by_this_phase"],
        "raw_inbox_mutation_performed": raw["raw_inbox_mutated_by_this_phase"],
        "next_required_step": manifest["next_required_step"],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA v0.1.4 S10-P1 report templates.")
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    args = parser.parse_args(argv)

    result = validate_v014_s10_p1_report_templates(args.manifest)
    print(
        "PASS: KMFA v0.1.4 S10-P1 report templates validated "
        f"(templates={result['template_count']}, sections={result['section_count']}, "
        f"project_cost_sections={result['project_cost_section_count']}, "
        f"business_overview_sections={result['business_overview_section_count']}, "
        f"v14_html_fail={result['v14_html_uiux_audit_fail_count']}, "
        "formal_report=false, s10_p2=false, s10_p3=false, "
        "stage10_review=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
