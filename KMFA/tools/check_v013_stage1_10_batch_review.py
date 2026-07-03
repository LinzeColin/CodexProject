#!/usr/bin/env python3
"""Validate KMFA v0.1.3 Stage 1-10 batch overall review evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from KMFA.tools.v013_stage1_10_batch_review import (
    MANIFEST_PATH,
    NEXT_REQUIRED_STEP,
    RAW_DIR,
    REPORT_PATH,
    REVIEW_SCOPE,
    SCHEMA_VERSION,
    STAGE_MANIFESTS,
    TASK_ID,
    TEST_RESULTS_PATH,
    VALIDATED_STAGE_IDS,
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
REQUIRED_HARD_BLOCKS = (
    "current_report_grade_d",
    "current_data_quality_q4",
    "pending_reconciliations_unresolved",
    "confirmed_resolutions_zero",
    "lineage_full_check_not_performed",
    "raw_value_matching_not_performed",
    "formal_report_release_blocked",
    "business_decision_basis_blocked",
    "delivery_blocked",
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


def validate_v013_stage1_10_batch_review(manifest_path: Path = MANIFEST_PATH) -> dict[str, Any]:
    errors: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    manifest = read_json(manifest_path)
    require(manifest.get("schema_version") == SCHEMA_VERSION, "schema_version mismatch")
    require(manifest.get("project_id") == "KMFA", "project_id mismatch")
    require(manifest.get("version") == "0.1.3", "version mismatch")
    require(manifest.get("review_id") == TASK_ID, "review_id mismatch")
    require(manifest.get("task_id") == TASK_ID, "task_id mismatch")
    require(manifest.get("review_scope") == REVIEW_SCOPE, "review_scope mismatch")
    require(
        manifest.get("status") == "batch_review_passed_local_only_upload_ready_next_gate_no_go",
        "status mismatch",
    )
    require(manifest.get("stage1_10_batch_overall_review_performed") is True, "batch review must be performed")
    require(manifest.get("stage_count") == 10, "stage_count must be 10")
    require(manifest.get("validated_stage_ids") == VALIDATED_STAGE_IDS, "validated_stage_ids mismatch")
    require(manifest.get("all_stage_reviews_validated") is True, "all stage reviews must be validated")
    require(manifest.get("open_stage_review_finding_count") == 0, "stage review findings must be closed")
    require(manifest.get("open_batch_finding_count") == 0, "batch review findings must be closed")
    require(manifest.get("fixed_batch_finding_count", 0) >= 1, "expected at least one fixed batch finding")
    require(
        manifest.get("legacy_individual_stage_upload_artifacts_current_gate") is False,
        "individual stage upload artifacts must not be current gate",
    )
    require(manifest.get("github_upload_ready_next_gate") is True, "GitHub upload next gate should be ready")
    require(manifest.get("github_upload_performed") is False, "GitHub upload must not be performed")
    require(manifest.get("github_upload_performed_count") == 0, "stage upload count must be 0")
    require(
        manifest.get("github_upload_status") == "not_uploaded_ready_for_separate_stage1_10_github_upload_gate",
        "GitHub upload status mismatch",
    )
    require(manifest.get("github_upload_gate_scope") == "separate_run_required", "upload gate scope mismatch")
    require(manifest.get("github_main_uploaded_for_v013_stage1_10") is False, "GitHub main must not be uploaded")
    require(manifest.get("delivery_allowed") is False, "delivery_allowed must remain false")
    require(manifest.get("delivery_allowed_count") == 0, "delivery_allowed_count must be 0")
    require(manifest.get("formal_report_allowed") is False, "formal report must remain blocked")
    require(manifest.get("formal_report_allowed_count") == 0, "formal report allowed count must be 0")
    require(manifest.get("business_decision_basis_allowed") is False, "business decision basis must remain blocked")
    require(manifest.get("business_execution_allowed") is False, "business execution must remain blocked")
    require(manifest.get("business_execution_allowed_count") == 0, "business execution count must be 0")
    require(manifest.get("lineage_full_check_completed") is False, "lineage full check must not be completed")
    require(manifest.get("raw_value_matching_performed") is False, "raw value matching must not be performed")
    require(manifest.get("current_report_grade") == "D", "current report grade mismatch")
    require(manifest.get("current_data_quality_grade") == "Q4", "current data quality grade mismatch")
    require(manifest.get("release_permission") == "blocked", "release permission mismatch")
    require(manifest.get("pending_reconciliation_count") == 12, "pending reconciliation count mismatch")
    require(manifest.get("confirmed_resolution_count") == 0, "confirmed resolution count mismatch")
    require(manifest.get("html_export_count") == 2, "HTML export count mismatch")
    require(manifest.get("csv_appendix_count") == 2, "CSV appendix count mismatch")
    require(manifest.get("excel_compatible_download_count") == 2, "Excel-compatible download count mismatch")
    require(manifest.get("raw_dir_read_performed_by_batch_review") is False, "batch review raw read must be false")
    require(manifest.get("raw_dir_read_performed_by_stage_validators") is False, "stage validator raw read must be false")
    require(manifest.get("raw_dir_mutation_performed") is False, "raw mutation must be false")
    require(manifest.get("next_required_step") == NEXT_REQUIRED_STEP, "next_required_step mismatch")

    stage_results = manifest.get("stage_results")
    require(isinstance(stage_results, dict), "stage_results must be a dict")
    require(list(stage_results.keys()) == VALIDATED_STAGE_IDS, "stage_results keys mismatch")
    require(set(stage_results.values()) == {"PASS"}, "all stage results must be PASS")
    reviewed_manifests = manifest.get("reviewed_stage_manifests")
    require(
        reviewed_manifests == {stage_id: path.as_posix() for stage_id, path in STAGE_MANIFESTS.items()},
        "reviewed_stage_manifests mismatch",
    )
    for stage_id, path in STAGE_MANIFESTS.items():
        stage_manifest = read_json(path)
        require(stage_manifest.get("stage_id") == stage_id, f"{stage_id} stage_id mismatch")
        require(stage_manifest.get("github_upload_performed") is False, f"{stage_id} GitHub upload must be false")
        require(stage_manifest.get("open_review_finding_count", 0) == 0, f"{stage_id} open findings must be 0")
        require(stage_manifest.get("delivery_allowed") is False, f"{stage_id} delivery_allowed must be false")
        require(stage_manifest.get("formal_report_allowed") is False, f"{stage_id} formal_report_allowed must be false")
        require(stage_manifest.get("business_execution_allowed") is False, f"{stage_id} business_execution_allowed must be false")
        phase_results = stage_manifest.get("phase_results", {})
        require(isinstance(phase_results, dict) and set(phase_results.values()) == {"PASS"}, f"{stage_id} phase results mismatch")

    raw_boundary = manifest.get("raw_data_boundary", {})
    require(raw_boundary.get("local_raw_data_dir") == RAW_DIR, "raw data dir mismatch")
    for key in (
        "codex_read_required_by_this_batch_review",
        "codex_read_performed_by_this_batch_review",
        "codex_list_performed_by_this_batch_review",
        "codex_modify_allowed",
        "codex_delete_allowed",
        "codex_move_allowed",
        "codex_rename_allowed",
        "codex_overwrite_allowed",
        "codex_generate_inside_allowed",
        "github_commit_allowed",
    ):
        require(raw_boundary.get(key) is False, f"raw boundary {key} must be false")

    public_safety = manifest.get("public_repo_safety", {})
    for key in PUBLIC_SAFETY_FALSE_KEYS:
        require(public_safety.get(key) is False, f"public safety key {key} must be false")

    hard_blocks = set(manifest.get("hard_blocks", []))
    for block in REQUIRED_HARD_BLOCKS:
        require(block in hard_blocks, f"missing hard block {block}")
    require(manifest.get("hard_block_count") == len(hard_blocks), "hard block count mismatch")

    for path in (REPORT_PATH, TEST_RESULTS_PATH):
        require(path.exists(), f"missing evidence file: {path}")
        if path.exists():
            text = path.read_text(encoding="utf-8")
            lowered = text.lower()
            for forbidden in FORBIDDEN_EVIDENCE_TEXT:
                require(forbidden.lower() not in lowered, f"forbidden evidence token {forbidden} in {path}")

    if errors:
        raise ValidationError("; ".join(errors))
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    args = parser.parse_args(argv)
    try:
        manifest = validate_v013_stage1_10_batch_review(args.manifest)
    except ValidationError as exc:
        print(f"FAIL: {exc}")
        return 1
    print(
        "PASS: KMFA v0.1.3 Stage 1-10 batch review validated "
        f"(stages={manifest['stage_count']}, open_batch_findings={manifest['open_batch_finding_count']}, "
        f"upload_ready_next_gate={str(manifest['github_upload_ready_next_gate']).lower()}, "
        f"github_upload={str(manifest['github_upload_performed']).lower()})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
