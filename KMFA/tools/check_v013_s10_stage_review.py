#!/usr/bin/env python3
"""Validate KMFA v0.1.3 Stage 10 review evidence."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

from KMFA.tools.check_s10_stage_review import validate_stage_review as validate_legacy_stage10_review
from KMFA.tools.check_v013_s10_p1_report_templates_replay import (
    validate_v013_s10_p1_report_templates_replay,
)
from KMFA.tools.check_v013_s10_p2_report_grade_runtime_replay import (
    validate_v013_s10_p2_report_grade_runtime_replay,
)
from KMFA.tools.check_v013_s10_p3_report_export_replay import (
    validate_v013_s10_p3_report_export_replay,
)
from KMFA.tools.v013_s10_stage_review import (
    LEGACY_STAGE10_REVIEW_MANIFEST_PATH,
    MANIFEST_PATH,
    NEXT_REQUIRED_STEP,
    RAW_DIR,
    REPORT_PATH,
    REVIEW_SCOPE,
    S10_P1_MANIFEST_PATH,
    S10_P2_MANIFEST_PATH,
    S10_P3_MANIFEST_PATH,
    SCHEMA_VERSION,
    TASK_ID,
    TEST_RESULTS_PATH,
)


PHASE_MANIFESTS = {
    "S10-P1": S10_P1_MANIFEST_PATH,
    "S10-P2": S10_P2_MANIFEST_PATH,
    "S10-P3": S10_P3_MANIFEST_PATH,
    "legacy_S10_review": LEGACY_STAGE10_REVIEW_MANIFEST_PATH,
}
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
REQUIRED_HARD_BLOCKS = (
    "report_grade_d_only",
    "zero_delta_failed",
    "unresolved_critical_difference",
    "missing_required_lineage",
    "missing_human_confirmation_for_A",
    "pending_reconciliation_blocks_formal_report",
    "raw_data_mutation_forbidden",
    "raw_value_publication_forbidden",
    "field_header_plaintext_publication_forbidden",
    "formal_report_release_blocked",
    "business_decision_basis_blocked",
    "stage1_10_batch_overall_review_not_performed",
    "lineage_full_check_not_performed",
    "raw_value_matching_not_performed",
    "github_upload_deferred_until_stage1_10_batch",
    "legacy_stage10_upload_artifacts_not_current_gate",
    "business_execution_blocked",
)
FORBIDDEN_EVIDENCE_TEXT = (
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


def validate_v013_s10_stage_review(manifest_path: Path = MANIFEST_PATH) -> dict[str, Any]:
    errors: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    manifest = read_json(manifest_path)
    p1 = validate_v013_s10_p1_report_templates_replay()
    p2 = validate_v013_s10_p2_report_grade_runtime_replay()
    p3 = validate_v013_s10_p3_report_export_replay()
    legacy_counts = validate_legacy_stage10_review()

    require(manifest.get("schema_version") == SCHEMA_VERSION, "manifest schema mismatch")
    require(manifest.get("project_id") == "KMFA", "project_id mismatch")
    require(manifest.get("version") == "0.1.3", "version mismatch")
    require(manifest.get("stage_id") == "S10", "stage_id must be S10")
    require(manifest.get("review_id") == TASK_ID, "review_id mismatch")
    require(manifest.get("task_id") == TASK_ID, "task_id mismatch")
    require(manifest.get("review_scope") == REVIEW_SCOPE, "review scope mismatch")
    require(
        manifest.get("status") == "review_passed_upload_deferred_until_stage1_10_batch_no_go",
        "status mismatch",
    )
    require(manifest.get("stage_review_performed") is True, "stage review must be performed")
    require(
        manifest.get("stage1_10_batch_overall_review_performed") is False,
        "Stage 1-10 batch review must not be performed",
    )
    require(manifest.get("github_upload_ready_next_gate") is False, "upload ready must stay false")
    require(
        manifest.get("github_upload_deferred_until_stage1_10_batch") is True,
        "upload must stay deferred until Stage 1-10 batch review",
    )
    require(manifest.get("github_upload_performed") is False, "GitHub upload must not be performed")
    require(
        manifest.get("github_upload_status") == "not_uploaded_deferred_until_stage1_10_batch",
        "GitHub upload status mismatch",
    )
    require(manifest.get("legacy_stage10_review_artifacts_validated") is True, "legacy Stage 10 review flag mismatch")
    require(
        manifest.get("legacy_stage10_upload_artifacts_current_gate") is False,
        "legacy Stage 10 upload artifacts must not be current gate",
    )
    require(
        manifest.get("legacy_stage10_upload_allowed_after_review_current") is False,
        "legacy upload allowed flag must be demoted for v0.1.3",
    )
    require(manifest.get("delivery_allowed") is False, "delivery_allowed must remain false")
    require(manifest.get("formal_report_allowed") is False, "formal_report_allowed must remain false")
    require(manifest.get("business_decision_basis_allowed") is False, "business basis must remain false")
    require(manifest.get("business_execution_allowed") is False, "business execution must remain false")
    require(manifest.get("lineage_full_check_completed") is False, "lineage full check must not be completed")
    require(manifest.get("raw_value_matching_performed") is False, "raw value matching must not be performed")
    require(manifest.get("phase_count") == 3, "phase_count must be 3")
    require(manifest.get("open_review_finding_count") == 0, "open review findings must be 0")
    require(manifest.get("fixed_review_finding_count") >= 1, "fixed review findings must be at least 1")
    require(manifest.get("next_required_step") == NEXT_REQUIRED_STEP, "next_required_step mismatch")

    findings = manifest.get("review_findings")
    require(isinstance(findings, list), "review_findings must be a list")
    require(
        any(
            finding.get("finding_id") == "KMFA-V013-S10-REV-F01" and finding.get("status") == "fixed"
            for finding in findings or []
        ),
        "missing fixed legacy upload finding",
    )

    phase_results = manifest.get("phase_results", {})
    require(phase_results == {"S10-P1": "PASS", "S10-P2": "PASS", "S10-P3": "PASS"}, "phase_results mismatch")
    require(manifest.get("s10_p1_dependency_validated") is True, "S10-P1 dependency flag mismatch")
    require(manifest.get("s10_p2_dependency_validated") is True, "S10-P2 dependency flag mismatch")
    require(manifest.get("s10_p3_dependency_validated") is True, "S10-P3 dependency flag mismatch")
    require(p1.get("phase_id") == "S10-P1", "S10-P1 validator did not return S10-P1")
    require(p2.get("phase_id") == "S10-P2", "S10-P2 validator did not return S10-P2")
    require(p3.get("phase_id") == "S10-P3", "S10-P3 validator did not return S10-P3")
    require(p1.get("stage10_review_performed") is False, "S10-P1 phase scope must not include review")
    require(p2.get("stage10_review_performed") is False, "S10-P2 phase scope must not include review")
    require(
        p3.get("stage10_phase_progress", {}).get("stage10_review_performed") is False,
        "S10-P3 phase scope must not include review",
    )
    require(p1.get("github_upload_performed") is False, "S10-P1 upload boundary mismatch")
    require(p2.get("github_upload_performed") is False, "S10-P2 upload boundary mismatch")
    require(p3.get("github_upload", {}).get("github_upload_performed") is False, "S10-P3 upload boundary mismatch")
    require(p1.get("raw_dir_read_performed") is False, "S10-P1 raw read boundary mismatch")
    require(p2.get("raw_dir_read_performed") is False, "S10-P2 raw read boundary mismatch")
    require(
        p3.get("raw_data_boundary", {}).get("codex_read_performed_by_this_phase") is False,
        "S10-P3 raw read boundary mismatch",
    )

    reviewed_phase_manifests = manifest.get("reviewed_phase_manifests", {})
    require(reviewed_phase_manifests == {key: path.as_posix() for key, path in PHASE_MANIFESTS.items()}, "phase manifests mismatch")
    for phase, path in PHASE_MANIFESTS.items():
        require(path.exists(), f"missing reviewed phase manifest for {phase}: {path}")

    require(manifest.get("current_data_quality_grade") == "Q4", "current data quality grade mismatch")
    require(manifest.get("current_report_grade") == "D", "current report grade mismatch")
    require(manifest.get("release_permission") == "blocked", "release permission mismatch")
    require(manifest.get("report_template_count") == 2, "report template count mismatch")
    require(manifest.get("report_template_section_count") == 11, "template section count mismatch")
    require(manifest.get("project_cost_section_count") == 4, "project cost section count mismatch")
    require(manifest.get("business_overview_section_count") == 7, "business overview section count mismatch")
    require(manifest.get("report_grade_record_count") == 2, "report grade record count mismatch")
    require(manifest.get("report_export_record_count") == 2, "report export record count mismatch")
    require(manifest.get("grade_distribution") == {"D": 2}, "grade distribution mismatch")
    require(manifest.get("html_export_count") == 2, "HTML export count mismatch")
    require(manifest.get("csv_appendix_count") == 2, "CSV appendix count mismatch")
    require(manifest.get("excel_compatible_download_count") == 2, "Excel-compatible CSV count mismatch")
    require(manifest.get("pdf_export_enabled_after_template_stable") is True, "PDF policy flag mismatch")
    require(manifest.get("committed_pdf_file_count") == 0, "committed PDF count mismatch")
    require(manifest.get("committed_excel_file_count") == 0, "committed Excel count mismatch")
    require(manifest.get("formal_report_count") == 0, "formal report count mismatch")
    require(manifest.get("business_decision_basis_count") == 0, "business decision basis count mismatch")
    require(manifest.get("pending_reconciliation_count") == 12, "pending reconciliation count mismatch")
    require(manifest.get("confirmed_resolution_count") == 0, "confirmed resolution count mismatch")
    require(manifest.get("legacy_review_counts") == legacy_counts, "legacy review counts mismatch")

    export_policy = manifest.get("report_export_policy", {})
    require(export_policy.get("record_version_binding_count") == 2, "record version binding count mismatch")
    require(export_policy.get("html_export_allowed") is True, "HTML export allowed mismatch")
    require(export_policy.get("csv_excel_export_allowed") is True, "CSV export allowed mismatch")
    require(export_policy.get("pdf_export_policy_enabled") is True, "PDF policy enabled mismatch")
    require(export_policy.get("pdf_private_runtime_only") is True, "PDF private runtime mismatch")
    require(export_policy.get("formal_report_allowed") is False, "export policy formal report mismatch")
    require(export_policy.get("business_decision_basis_allowed") is False, "export policy business basis mismatch")

    require(manifest.get("raw_dir_read_performed_by_stage_review") is False, "stage review raw read must be false")
    require(
        manifest.get("raw_dir_read_performed_by_dependency_validators") is False,
        "dependency validators must not read raw inbox in this review",
    )
    require(manifest.get("raw_dir_mutation_performed") is False, "raw directory mutation must not be performed")
    require(manifest.get("github_upload_count") == 0, "github upload count mismatch")

    safety = manifest.get("public_repo_safety", {})
    for key in PUBLIC_SAFETY_FALSE_KEYS:
        require(safety.get(key) is False, f"public_repo_safety.{key} must be false")
    require(safety.get("public_safe_csv_export_committed") is True, "public-safe CSV export flag mismatch")
    require(safety.get("html_report_export_committed") is True, "HTML export flag mismatch")

    hard_blocks = manifest.get("hard_blocks", [])
    require(isinstance(hard_blocks, list), "hard_blocks must be a list")
    for block in REQUIRED_HARD_BLOCKS:
        require(block in hard_blocks, f"missing hard block: {block}")
    require(manifest.get("hard_block_count") == len(REQUIRED_HARD_BLOCKS), "hard block count mismatch")

    raw_boundary = manifest.get("raw_data_boundary", {})
    require(raw_boundary.get("local_raw_data_dir") == RAW_DIR, "raw directory mismatch")
    require(
        raw_boundary.get("local_raw_data_dir_role") == "user_finance_raw_private_inbox",
        "raw directory role mismatch",
    )
    require(raw_boundary.get("codex_read_allowed_only_when_phase_requires") is True, "raw read policy mismatch")
    for key in (
        "codex_read_required_by_this_stage_review",
        "codex_read_performed_by_this_stage_review",
        "codex_list_performed_by_this_stage_review",
        "codex_modify_allowed",
        "codex_delete_allowed",
        "codex_move_allowed",
        "codex_rename_allowed",
        "codex_overwrite_allowed",
        "codex_generate_inside_allowed",
        "codex_create_extra_files_inside_allowed",
        "github_commit_allowed",
    ):
        require(raw_boundary.get(key) is False, f"raw boundary {key} must be false")

    for ref in manifest.get("governance_refs", []):
        require(Path(ref).exists(), f"missing governance ref: {ref}")
    for ref in manifest.get("evidence_refs", []):
        require(Path(ref).exists(), f"missing evidence ref: {ref}")
    for evidence in (MANIFEST_PATH, REPORT_PATH, TEST_RESULTS_PATH):
        require(evidence.exists(), f"missing public evidence: {evidence}")
        if evidence.exists():
            text = evidence.read_text(encoding="utf-8")
            lower = text.lower()
            for forbidden in FORBIDDEN_EVIDENCE_TEXT:
                require(forbidden.lower() not in lower, f"forbidden public evidence text {forbidden!r} in {evidence}")

    reviewed_head = str(manifest.get("reviewed_head", ""))
    require(
        len(reviewed_head) == 40 and all(character in "0123456789abcdef" for character in reviewed_head),
        "reviewed_head must be a lowercase 40-character git SHA",
    )
    require(manifest.get("branch") == git_output(["branch", "--show-current"]), "branch mismatch")
    require(manifest.get("remote") == git_output(["remote", "get-url", "origin"]), "remote mismatch")

    if errors:
        raise ValidationError("; ".join(errors))

    return {
        "project_id": manifest["project_id"],
        "version": manifest["version"],
        "stage_id": manifest["stage_id"],
        "review_scope": manifest["review_scope"],
        "phase_count": manifest["phase_count"],
        "phase_results": manifest["phase_results"],
        "s10_p1_dependency_validated": manifest["s10_p1_dependency_validated"],
        "s10_p2_dependency_validated": manifest["s10_p2_dependency_validated"],
        "s10_p3_dependency_validated": manifest["s10_p3_dependency_validated"],
        "stage_review_performed": manifest["stage_review_performed"],
        "stage1_10_batch_overall_review_performed": manifest["stage1_10_batch_overall_review_performed"],
        "open_review_finding_count": manifest["open_review_finding_count"],
        "fixed_review_finding_count": manifest["fixed_review_finding_count"],
        "current_data_quality_grade": manifest["current_data_quality_grade"],
        "current_report_grade": manifest["current_report_grade"],
        "release_permission": manifest["release_permission"],
        "report_template_count": manifest["report_template_count"],
        "report_template_section_count": manifest["report_template_section_count"],
        "report_grade_record_count": manifest["report_grade_record_count"],
        "report_export_record_count": manifest["report_export_record_count"],
        "html_export_count": manifest["html_export_count"],
        "csv_appendix_count": manifest["csv_appendix_count"],
        "excel_compatible_download_count": manifest["excel_compatible_download_count"],
        "pending_reconciliation_count": manifest["pending_reconciliation_count"],
        "confirmed_resolution_count": manifest["confirmed_resolution_count"],
        "formal_report_count": manifest["formal_report_count"],
        "business_decision_basis_count": manifest["business_decision_basis_count"],
        "raw_dir_read_performed_by_stage_review": manifest["raw_dir_read_performed_by_stage_review"],
        "raw_dir_read_performed_by_dependency_validators": manifest[
            "raw_dir_read_performed_by_dependency_validators"
        ],
        "raw_dir_mutation_performed": manifest["raw_dir_mutation_performed"],
        "github_upload_performed": manifest["github_upload_performed"],
        "github_upload_deferred_until_stage1_10_batch": manifest[
            "github_upload_deferred_until_stage1_10_batch"
        ],
        "github_upload_status": manifest["github_upload_status"],
        "legacy_stage10_upload_artifacts_current_gate": manifest["legacy_stage10_upload_artifacts_current_gate"],
        "delivery_allowed": manifest["delivery_allowed"],
        "formal_report_allowed": manifest["formal_report_allowed"],
        "business_execution_allowed": manifest["business_execution_allowed"],
        "next_required_step": manifest["next_required_step"],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA v0.1.3 Stage 10 review evidence.")
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    args = parser.parse_args(argv)
    try:
        result = validate_v013_s10_stage_review(args.manifest)
    except (OSError, json.JSONDecodeError, ValidationError, RuntimeError, ValueError) as exc:
        print(f"FAIL: KMFA v0.1.3 Stage 10 review validation failed ({exc})")
        return 1

    print(
        "PASS: KMFA v0.1.3 Stage 10 review validated "
        f"(phase_results={result['phase_results']}, "
        f"open_findings={result['open_review_finding_count']}, "
        f"exports={result['html_export_count']} html/{result['csv_appendix_count']} csv, "
        "stage1_10_batch_review=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
