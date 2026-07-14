#!/usr/bin/env python3
"""Validate KMFA v0.1.3 Stage 9 review evidence."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

from KMFA.tools.check_v013_s09_p1_project_cost_fact_layer_replay import (
    validate_v013_s09_p1_project_cost_fact_layer_replay,
)
from KMFA.tools.check_v013_s09_p2_margin_cash_margin_replay import (
    validate_v013_s09_p2_margin_cash_margin_replay,
)
from KMFA.tools.check_v013_s09_p3_scope_reconciliation_replay import (
    validate_v013_s09_p3_scope_reconciliation_replay,
)
from KMFA.tools.v013_s09_stage_review import (
    LEGACY_STAGE9_REVIEW_MANIFEST_PATH,
    MANIFEST_PATH,
    NEXT_REQUIRED_STEP,
    RAW_DIR,
    REPORT_PATH,
    REVIEW_SCOPE,
    S09_P1_MANIFEST_PATH,
    S09_P2_MANIFEST_PATH,
    S09_P3_MANIFEST_PATH,
    SCHEMA_VERSION,
    TASK_ID,
    TEST_RESULTS_PATH,
)


PHASE_MANIFESTS = {
    "S09-P1": S09_P1_MANIFEST_PATH,
    "S09-P2": S09_P2_MANIFEST_PATH,
    "S09-P3": S09_P3_MANIFEST_PATH,
    "legacy_S09_review": LEGACY_STAGE9_REVIEW_MANIFEST_PATH,
}
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
    "business_fact_values_committed",
    "scope_reconciliation_business_values_committed",
    "formal_report_committed",
)
REQUIRED_HARD_BLOCKS = (
    "raw_data_mutation_forbidden",
    "raw_value_publication_forbidden",
    "field_header_plaintext_publication_forbidden",
    "business_amount_values_remain_private_ref_or_hash_only",
    "project_cost_fact_layer_formal_calculation_blocked",
    "pending_reconciliation_blocks_derived_metric_rerun",
    "confirmed_resolution_count_zero_blocks_rerun",
    "formal_report_release_blocked",
    "lineage_full_check_not_performed",
    "raw_value_matching_not_performed",
    "github_upload_deferred_until_stage10_batch",
    "s10_p1_not_performed",
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
    "amount_a_cents:",
    "amount_b_cents:",
    "delta_cents:",
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


def validate_v013_s09_stage_review(manifest_path: Path = MANIFEST_PATH) -> dict[str, Any]:
    errors: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    manifest = read_json(manifest_path)
    p1 = validate_v013_s09_p1_project_cost_fact_layer_replay()
    p2 = validate_v013_s09_p2_margin_cash_margin_replay()
    p3 = validate_v013_s09_p3_scope_reconciliation_replay()

    require(manifest.get("schema_version") == SCHEMA_VERSION, "manifest schema mismatch")
    require(manifest.get("project_id") == "KMFA", "project_id mismatch")
    require(manifest.get("version") == "0.1.3", "version mismatch")
    require(manifest.get("stage_id") == "S09", "stage_id must be S09")
    require(manifest.get("review_id") == TASK_ID, "review_id mismatch")
    require(manifest.get("task_id") == TASK_ID, "task_id mismatch")
    require(manifest.get("review_scope") == REVIEW_SCOPE, "review scope mismatch")
    require(manifest.get("status") == "review_passed_upload_deferred_until_stage10_batch_no_go", "status mismatch")
    require(manifest.get("stage_review_performed") is True, "stage review must be performed")
    require(manifest.get("s10_p1_performed") is False, "S10-P1 must not be performed")
    require(manifest.get("github_upload_ready_next_gate") is False, "upload ready must stay false")
    require(
        manifest.get("github_upload_deferred_until_stage10_batch") is True,
        "upload must stay deferred until Stage 1-10 batch",
    )
    require(manifest.get("github_upload_performed") is False, "GitHub upload must not be performed")
    require(
        manifest.get("github_upload_status") == "not_uploaded_deferred_until_stage10_batch",
        "GitHub upload status mismatch",
    )
    require(manifest.get("legacy_stage9_review_artifacts_validated") is True, "legacy Stage 9 review flag mismatch")
    require(manifest.get("legacy_stage9_upload_artifacts_current_gate") is False, "legacy upload must not be current")
    require(manifest.get("delivery_allowed") is False, "delivery_allowed must remain false")
    require(manifest.get("formal_report_allowed") is False, "formal_report_allowed must remain false")
    require(manifest.get("business_decision_basis_allowed") is False, "business basis must remain false")
    require(manifest.get("business_execution_allowed") is False, "business execution must remain false")
    require(manifest.get("lineage_full_check_completed") is False, "lineage full check must not be completed")
    require(manifest.get("raw_value_matching_performed") is False, "raw value matching must not be performed")
    require(manifest.get("raw_dir_read_performed_by_stage_review") is False, "stage review raw read must be false")
    require(
        manifest.get("raw_dir_read_performed_by_dependency_validators") is False,
        "dependency validators must not read raw inbox in this review",
    )
    require(manifest.get("raw_dir_mutation_performed") is False, "raw directory mutation must not be performed")
    require(manifest.get("phase_count") == 3, "phase_count must be 3")
    require(manifest.get("open_review_finding_count") == 0, "open review findings must be 0")
    require(manifest.get("fixed_review_finding_count") == 1, "fixed review findings must be 1")
    require(manifest.get("next_required_step") == NEXT_REQUIRED_STEP, "next_required_step mismatch")

    findings = manifest.get("review_findings")
    require(isinstance(findings, list), "review_findings must be a list")
    require(
        any(
            finding.get("finding_id") == "KMFA-V013-S09-REV-F01" and finding.get("status") == "fixed"
            for finding in findings or []
        ),
        "missing fixed legacy upload finding",
    )

    phase_results = manifest.get("phase_results", {})
    require(phase_results == {"S09-P1": "PASS", "S09-P2": "PASS", "S09-P3": "PASS"}, "phase_results mismatch")
    require(manifest.get("s09_p1_dependency_validated") is True, "S09-P1 dependency flag mismatch")
    require(manifest.get("s09_p2_dependency_validated") is True, "S09-P2 dependency flag mismatch")
    require(manifest.get("s09_p3_dependency_validated") is True, "S09-P3 dependency flag mismatch")
    require(p1.get("phase_id") == "S09-P1", "S09-P1 validator did not return S09-P1")
    require(p2.get("phase_id") == "S09-P2", "S09-P2 validator did not return S09-P2")
    require(p3.get("phase_id") == "S09-P3", "S09-P3 validator did not return S09-P3")
    for result, label in ((p1, "S09-P1"), (p2, "S09-P2"), (p3, "S09-P3")):
        require(result.get("stage9_review_performed") is False, f"{label} phase scope must not include review")
        require(result.get("github_upload_performed") is False, f"{label} upload boundary mismatch")
        require(result.get("raw_dir_read_performed") is False, f"{label} raw read boundary mismatch")
        require(result.get("raw_dir_mutation_performed") is False, f"{label} raw mutation boundary mismatch")

    reviewed_phase_manifests = manifest.get("reviewed_phase_manifests", {})
    require(reviewed_phase_manifests == {key: path.as_posix() for key, path in PHASE_MANIFESTS.items()}, "phase manifests mismatch")
    for phase, path in PHASE_MANIFESTS.items():
        require(path.exists(), f"missing reviewed phase manifest for {phase}: {path}")

    require(manifest.get("current_data_quality_grade") == "Q4", "current data quality grade mismatch")
    require(manifest.get("current_report_grade") == "D", "current report grade mismatch")
    require(manifest.get("release_permission") == "blocked", "release permission mismatch")
    require(manifest.get("formal_calculation_allowed_count") == 0, "formal calculation count mismatch")
    require(manifest.get("formal_report_allowed_count") == 0, "formal report count mismatch")
    require(manifest.get("derived_metric_rerun_allowed_count") == 0, "derived rerun count mismatch")
    require(manifest.get("formal_report_rerun_allowed_count") == 0, "formal report rerun count mismatch")
    require(manifest.get("github_upload_count") == 0, "github upload count mismatch")
    require(manifest.get("pending_resolution_count") == 12, "pending resolution count mismatch")
    require(manifest.get("confirmed_resolution_count") == 0, "confirmed resolution count mismatch")

    phase_summary = manifest.get("phase_summary", {})
    p1_summary = phase_summary.get("S09-P1", {})
    require(p1_summary.get("required_metric_count") == 6, "S09-P1 metric count mismatch")
    require(p1_summary.get("cost_category_count") == 9, "S09-P1 cost category count mismatch")
    require(p1_summary.get("fact_record_count") == 4, "S09-P1 fact record count mismatch")
    require(p1_summary.get("unallocated_pool_count") == 9, "S09-P1 unallocated pool count mismatch")
    require(p1_summary.get("authority_locked_field_count") == 40, "S09-P1 authority locked field count mismatch")
    require(p1_summary.get("authority_excluded_field_count") == 5, "S09-P1 excluded field count mismatch")
    require(p1_summary.get("manual_review_queue_count") == 3, "S09-P1 manual review queue count mismatch")
    require(p1_summary.get("unresolved_difference_count") == 1, "S09-P1 unresolved difference count mismatch")
    require(p1_summary.get("formal_calculation_allowed") is False, "S09-P1 formal calculation mismatch")

    p2_summary = phase_summary.get("S09-P2", {})
    require(p2_summary.get("required_margin_metric_count") == 4, "S09-P2 metric count mismatch")
    require(p2_summary.get("project_cost_fact_record_count") == 4, "S09-P2 fact record count mismatch")
    require(p2_summary.get("margin_record_count") == 4, "S09-P2 margin record count mismatch")
    require(p2_summary.get("difference_summary_count") == 12, "S09-P2 difference summary mismatch")
    require(p2_summary.get("authority_field_group_count") == 8, "S09-P2 authority field group mismatch")
    require(p2_summary.get("authority_system_overwrite_allowed_count") == 0, "S09-P2 overwrite count mismatch")
    require(p2_summary.get("public_amount_values_committed_count") == 0, "S09-P2 public amount count mismatch")

    p3_summary = phase_summary.get("S09-P3", {})
    require(p3_summary.get("reconciliation_record_count") == 12, "S09-P3 reconciliation record count mismatch")
    require(p3_summary.get("domain_control_count") == 6, "S09-P3 domain control count mismatch")
    require(p3_summary.get("required_reconciliation_domain_count") == 6, "S09-P3 required domain count mismatch")
    require(p3_summary.get("source_difference_summary_count") == 12, "S09-P3 difference summary count mismatch")
    require(p3_summary.get("confirmed_resolution_count") == 0, "S09-P3 confirmed resolution count mismatch")
    require(p3_summary.get("pending_resolution_count") == 12, "S09-P3 pending resolution count mismatch")
    require(p3_summary.get("derived_metric_rerun_allowed") is False, "S09-P3 derived rerun mismatch")
    require(p3_summary.get("formal_report_rerun_allowed") is False, "S09-P3 formal rerun mismatch")
    require(
        p3_summary.get("reconciliation_records_by_domain")
        == {
            "authority_pdf_excel_vs_system_recomputed": 8,
            "bank_collection_vs_receivable_aging": 4,
        },
        "S09-P3 records by domain mismatch",
    )

    public_safety = manifest.get("public_repo_safety", {})
    for key in PUBLIC_SAFETY_FALSE_KEYS:
        require(public_safety.get(key) is False, f"public safety key must be false: {key}")

    hard_blocks = manifest.get("hard_blocks", [])
    require(isinstance(hard_blocks, list), "hard_blocks must be a list")
    for block in REQUIRED_HARD_BLOCKS:
        require(block in hard_blocks, f"missing hard block: {block}")
    require(manifest.get("hard_block_count") == len(hard_blocks), "hard_block_count mismatch")

    raw_boundary = manifest.get("raw_data_boundary", {})
    require(raw_boundary.get("local_raw_data_dir") == RAW_DIR, "raw dir mismatch")
    require(raw_boundary.get("codex_read_required_by_this_stage_review") is False, "raw read required mismatch")
    require(raw_boundary.get("codex_read_performed_by_this_stage_review") is False, "raw read performed mismatch")
    for key in (
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

    for ref in manifest.get("evidence_refs", []):
        require(Path(ref).exists(), f"missing evidence ref: {ref}")

    for path in (REPORT_PATH, TEST_RESULTS_PATH, manifest_path):
        text = path.read_text(encoding="utf-8")
        lower = text.lower()
        for token in FORBIDDEN_EVIDENCE_TEXT:
            require(token.lower() not in lower, f"forbidden evidence text {token!r} in {path}")

    if errors:
        raise ValidationError("; ".join(errors))

    return {
        "project_id": manifest["project_id"],
        "version": manifest["version"],
        "stage_id": manifest["stage_id"],
        "review_scope": manifest["review_scope"],
        "phase_count": manifest["phase_count"],
        "phase_results": manifest["phase_results"],
        "s09_p1_dependency_validated": manifest["s09_p1_dependency_validated"],
        "s09_p2_dependency_validated": manifest["s09_p2_dependency_validated"],
        "s09_p3_dependency_validated": manifest["s09_p3_dependency_validated"],
        "stage_review_performed": manifest["stage_review_performed"],
        "s10_p1_performed": manifest["s10_p1_performed"],
        "open_review_finding_count": manifest["open_review_finding_count"],
        "fixed_review_finding_count": manifest["fixed_review_finding_count"],
        "formal_calculation_allowed_count": manifest["formal_calculation_allowed_count"],
        "formal_report_allowed_count": manifest["formal_report_allowed_count"],
        "derived_metric_rerun_allowed_count": manifest["derived_metric_rerun_allowed_count"],
        "pending_resolution_count": manifest["pending_resolution_count"],
        "current_data_quality_grade": manifest["current_data_quality_grade"],
        "current_report_grade": manifest["current_report_grade"],
        "release_permission": manifest["release_permission"],
        "raw_dir_read_performed_by_stage_review": manifest["raw_dir_read_performed_by_stage_review"],
        "raw_dir_read_performed_by_dependency_validators": manifest[
            "raw_dir_read_performed_by_dependency_validators"
        ],
        "raw_dir_mutation_performed": manifest["raw_dir_mutation_performed"],
        "github_upload_performed": manifest["github_upload_performed"],
        "github_upload_deferred_until_stage10_batch": manifest["github_upload_deferred_until_stage10_batch"],
        "legacy_stage9_upload_artifacts_current_gate": manifest["legacy_stage9_upload_artifacts_current_gate"],
        "delivery_allowed": manifest["delivery_allowed"],
        "formal_report_allowed": manifest["formal_report_allowed"],
        "business_execution_allowed": manifest["business_execution_allowed"],
        "next_required_step": manifest["next_required_step"],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA v0.1.3 Stage 9 review evidence.")
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    args = parser.parse_args(argv)
    try:
        result = validate_v013_s09_stage_review(args.manifest)
    except (OSError, json.JSONDecodeError, ValidationError) as exc:
        print(f"FAIL: KMFA v0.1.3 Stage 9 review validation failed ({exc})")
        return 1

    print(
        "PASS: KMFA v0.1.3 Stage 9 review validated "
        f"(phase_results={result['phase_results']}, "
        f"open_findings={result['open_review_finding_count']}, "
        f"pending_resolutions={result['pending_resolution_count']}, "
        "s10_p1=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
