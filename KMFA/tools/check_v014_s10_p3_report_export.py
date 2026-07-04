#!/usr/bin/env python3
"""Validate KMFA v0.1.4 S10-P3 public-safe report export evidence."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any

from KMFA.tools.v014_s10_p3_report_export import (
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
    validate_legacy_s10_p3_artifacts,
    validate_s10_p2_dependency,
    validate_v013_replay_dependency,
)


PUBLIC_SAFETY_FALSE_KEYS = (
    "protected_source_payload_committed",
    "zip_committed",
    "excel_workbook_committed",
    "wps_native_file_committed",
    "redcircle_native_file_committed",
    "raw_or_private_csv_committed",
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
    "spreadsheet_workbook_committed",
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
    "report_grade_d_only",
    "zero_delta_failed",
    "unresolved_critical_difference",
    "missing_required_lineage",
    "missing_human_confirmation_for_A",
    "raw_data_mutation_forbidden",
    "raw_value_publication_forbidden",
    "field_header_plaintext_publication_forbidden",
    "formal_report_release_blocked",
    "business_decision_basis_blocked",
    "stage10_review_not_performed",
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


def validate_v014_s10_p3_report_export(manifest_path: Path = MANIFEST_PATH) -> dict[str, Any]:
    errors: list[str] = []
    manifest = read_json(manifest_path)
    s10_p2 = validate_s10_p2_dependency()
    v013 = validate_v013_replay_dependency()
    legacy = validate_legacy_s10_p3_artifacts()

    require(manifest.get("schema_version") == SCHEMA_VERSION, "manifest schema mismatch", errors)
    require(manifest.get("project_id") == "KMFA", "project_id mismatch", errors)
    require(manifest.get("version") == "0.1.4", "version mismatch", errors)
    require(manifest.get("stage_id") == "S10", "stage_id must be S10", errors)
    require(manifest.get("phase_id") == "S10-P3", "phase_id must be S10-P3", errors)
    require(manifest.get("phase_scope") == PHASE_SCOPE, "phase scope mismatch", errors)
    require(manifest.get("task_id") == TASK_ID, "task_id mismatch", errors)
    require(
        manifest.get("status") == "completed_validated_local_only_no_go_upload_deferred_report_export_locked",
        "status mismatch",
        errors,
    )
    require(manifest.get("completed_task_ids") == ["S10P3T01", "S10P3T02", "S10P3T03"], "tasks mismatch", errors)
    require(manifest.get("acceptance_ids") == [ACCEPTANCE_ID], "acceptance id mismatch", errors)
    require(manifest.get("s10_p2_dependency_validated") is True, "S10-P2 dependency flag mismatch", errors)
    require(s10_p2.get("phase_id") == "S10-P2", "S10-P2 dependency did not validate", errors)
    require(manifest.get("legacy_s10_p3_dependency_validated") is True, "legacy S10-P3 flag mismatch", errors)
    require(manifest.get("v013_s10_p3_replay_validated") is True, "v013 replay flag mismatch", errors)
    require(v013.get("phase_id") == "S10-P3", "v013 S10-P3 replay did not validate", errors)

    progress = manifest.get("stage10_phase_progress", {})
    require(progress.get("completed_phase_count") == 3, "completed phase count mismatch", errors)
    require(progress.get("total_phase_count") == 3, "total phase count mismatch", errors)
    require(progress.get("derived_percent_bps") == 10000, "derived percent bps mismatch", errors)
    require(progress.get("derived_percent_label") == "100.00%", "derived percent label mismatch", errors)
    require(progress.get("s10_p1_performed") is True, "S10-P1 must be performed", errors)
    require(progress.get("s10_p2_performed") is True, "S10-P2 must be performed", errors)
    require(progress.get("s10_p3_performed") is True, "S10-P3 must be performed", errors)
    require(progress.get("stage10_review_performed") is False, "Stage 10 review must not be performed", errors)

    summary = manifest.get("report_export_summary", {})
    expected_summary = {
        "template_count": 2,
        "report_export_record_count": 2,
        "grade_distribution": {"D": 2},
        "html_export_count": 2,
        "csv_appendix_count": 2,
        "excel_compatible_download_count": 2,
        "pdf_export_enabled_after_template_stable": True,
        "committed_pdf_file_count": 0,
        "committed_excel_file_count": 0,
        "formal_report_count": 0,
        "business_decision_basis_count": 0,
        "pending_reconciliation_count": 12,
    }
    for key, expected in expected_summary.items():
        require(summary.get(key) == expected, f"summary.{key} mismatch", errors)
        require(summary.get(key) == legacy.get(key), f"legacy summary mismatch for {key}", errors)
    require(summary.get("required_template_ids") == legacy["required_template_ids"], "required template IDs mismatch", errors)

    policy = manifest.get("report_export_policy", {})
    for field_name in (
        "report_export_version",
        "template_version",
        "formula_version",
        "mapping_version",
        "html_template_version",
        "csv_appendix_schema_version",
        "pdf_export_policy_version",
        "content_hash",
        "upstream_template_content_hash",
        "grade_runtime_content_hash",
    ):
        require(policy.get(field_name) == legacy.get(field_name), f"policy legacy mismatch for {field_name}", errors)
    require(policy.get("record_version_binding_required") is True, "version binding flag mismatch", errors)
    require(policy.get("record_version_binding_count") == 2, "version binding count mismatch", errors)
    require(policy.get("html_export_allowed") is True, "HTML export must be allowed", errors)
    require(policy.get("html_export_count") == 2, "HTML export count mismatch", errors)
    require(policy.get("inherits_blue_business_sample_count") == 2, "blue sample inheritance count mismatch", errors)
    require(policy.get("csv_excel_export_allowed") is True, "CSV/Excel export must be allowed", errors)
    require(policy.get("csv_appendix_count") == 2, "CSV appendix count mismatch", errors)
    require(policy.get("excel_download_mode") == "excel_compatible_csv_no_workbook_committed", "Excel mode mismatch", errors)
    require(policy.get("excel_compatible_csv_count") == 2, "Excel compatible CSV count mismatch", errors)
    require(policy.get("excel_workbook_committed") is False, "Excel workbook must not be committed", errors)
    require(policy.get("committed_excel_workbook_count") == 0, "committed workbook count mismatch", errors)
    require(policy.get("pdf_export_policy_enabled") is True, "PDF policy must be enabled", errors)
    require(policy.get("pdf_private_runtime_only") is True, "PDF policy must remain private runtime only", errors)
    require(policy.get("pdf_private_runtime_only_count") == 2, "PDF private runtime count mismatch", errors)
    require(policy.get("pdf_file_committed") is False, "PDF file must not be committed", errors)
    require(policy.get("committed_pdf_file_count") == 0, "PDF file count mismatch", errors)
    require(policy.get("formal_report_allowed") is False, "formal report must be false", errors)
    require(policy.get("business_decision_basis_allowed") is False, "business decision basis must be false", errors)

    html = manifest.get("html_sample_inheritance", {})
    require(html.get("taskpack_html_requirement_read") is True, "HTML requirement read flag mismatch", errors)
    require(html.get("html_output_count") == 2, "HTML output count mismatch", errors)
    require(html.get("inherits_blue_business_sample_count") == 2, "HTML sample inheritance mismatch", errors)
    source_refs = html.get("source_taskpack_refs", {})
    for key in ("roadmap_s10_p3", "html_acceptance_inheritance", "html_acceptance_index"):
        require(key in source_refs, f"missing HTML/taskpack source ref: {key}", errors)

    phase = manifest.get("phase_boundaries", {})
    require(phase.get("s10_p1_report_templates_dependency_included") is True, "S10-P1 dependency flag mismatch", errors)
    require(phase.get("s10_p2_report_trust_grade_dependency_included") is True, "S10-P2 dependency flag mismatch", errors)
    require(phase.get("s10_p3_report_export_scope_included") is True, "S10-P3 scope flag mismatch", errors)
    for key in (
        "stage10_review_scope_included",
        "lineage_full_check_scope_included",
        "raw_value_matching_scope_included",
        "formal_report_scope_included",
        "ui_runtime_scope_included",
        "external_connector_scope_included",
        "app_reinstall_scope_included",
        "github_upload_scope_included",
    ):
        require(phase.get(key) is False, f"phase_boundaries.{key} must be false", errors)

    quality = manifest.get("quality_gate", {})
    require(quality.get("current_data_quality_grade") == "Q4", "quality grade mismatch", errors)
    require(quality.get("current_report_grade") == "D", "report grade mismatch", errors)
    require(quality.get("release_permission") == "blocked", "release permission mismatch", errors)
    require(quality.get("pending_reconciliation_count") == 12, "pending reconciliation count mismatch", errors)
    require(quality.get("confirmed_resolution_count") == 0, "confirmed resolution count mismatch", errors)
    require(quality.get("zero_delta_passed") is False, "zero delta mismatch", errors)
    require(quality.get("html_export_allowed") is True, "HTML export allowed mismatch", errors)
    require(quality.get("csv_excel_export_allowed") is True, "CSV/Excel export allowed mismatch", errors)
    require(quality.get("pdf_export_policy_enabled") is True, "PDF policy flag mismatch", errors)
    for key in (
        "complete_trusted_report_display_allowed",
        "full_trusted_report_allowed",
        "formal_report_allowed",
        "business_decision_basis_allowed",
        "business_execution_allowed",
        "delivery_allowed",
        "raw_layer_write_allowed",
        "automatic_external_action_allowed",
        "stage10_review_allowed",
        "github_upload_allowed",
    ):
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

    raw_boundary = manifest.get("raw_data_boundary", {})
    require(raw_boundary.get("raw_inbox_role") == "user_finance_raw_private_inbox", "raw role mismatch", errors)
    require(raw_boundary.get("raw_inbox_read_allowed_only_when_phase_requires") is True, "raw read policy mismatch", errors)
    for key in RAW_BOUNDARY_FALSE_KEYS:
        require(raw_boundary.get(key) is False, f"raw_data_boundary.{key} must be false", errors)
    require(raw_boundary.get("private_runtime_output_dir") == "KMFA/.codex_private_runtime/", "runtime dir mismatch", errors)

    safety = manifest.get("public_repo_safety", {})
    for key in PUBLIC_SAFETY_FALSE_KEYS:
        require(safety.get(key) is False, f"public_repo_safety.{key} must be false", errors)
    require(safety.get("public_safe_csv_export_committed") is True, "public-safe CSV export flag mismatch", errors)
    require(safety.get("html_report_export_committed") is True, "HTML export flag mismatch", errors)

    hard_blocks = manifest.get("hard_blocks", [])
    require(isinstance(hard_blocks, list), "hard_blocks must be a list", errors)
    for block in REQUIRED_HARD_BLOCKS:
        require(block in hard_blocks, f"missing hard block: {block}", errors)
    require(manifest.get("hard_block_count") == len(REQUIRED_HARD_BLOCKS), "hard block count mismatch", errors)
    require(manifest.get("next_required_step") == NEXT_REQUIRED_STEP, "next_required_step mismatch", errors)

    artifact_refs = manifest.get("artifact_refs", {})
    for key in (
        "legacy_manifest",
        "legacy_records",
        "legacy_stage_manifest",
        "legacy_completion_record",
        "legacy_test_results",
        "legacy_html_project_cost",
        "legacy_html_business_overview",
        "legacy_csv_project_cost",
        "legacy_csv_business_overview",
        "v013_s10_p3_replay_manifest",
        "v014_s10_p2_manifest",
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
    test_text = TEST_RESULTS_PATH.read_text(encoding="utf-8", errors="ignore")
    require("pending_final_validation" not in test_text, "test results must not remain pending", errors)
    require("completed_validated_local_only_no_go_upload_deferred" in test_text, "test results status missing", errors)
    require("check_v014_s10_p3_report_export.py" in test_text, "S10-P3 validator evidence missing", errors)
    require("test_v014_s10_p3_report_export" in test_text, "S10-P3 unit test evidence missing", errors)
    require("Stage 10 overall review and GitHub upload were intentionally not performed" in test_text, "phase boundary evidence missing", errors)

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
    parser = argparse.ArgumentParser(description="Validate KMFA v0.1.4 S10-P3 report export evidence.")
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    args = parser.parse_args(argv)
    try:
        manifest = validate_v014_s10_p3_report_export(args.manifest)
    except (OSError, json.JSONDecodeError, ValidationError, RuntimeError) as exc:
        print(f"FAIL: KMFA v0.1.4 S10-P3 report export validation failed ({exc})")
        return 1

    summary = manifest["report_export_summary"]
    print(
        "PASS: KMFA v0.1.4 S10-P3 report export validated "
        f"(export_records={summary['report_export_record_count']}, "
        f"html_exports={summary['html_export_count']}, "
        f"csv_appendices={summary['csv_appendix_count']}, "
        f"excel_compatible_downloads={summary['excel_compatible_download_count']}, "
        "stage10_review=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
