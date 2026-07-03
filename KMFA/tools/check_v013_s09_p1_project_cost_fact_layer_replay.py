#!/usr/bin/env python3
"""Validate KMFA v0.1.3 S09-P1 project cost fact layer replay evidence."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

from KMFA.tools.v013_s09_p1_project_cost_fact_layer_replay import (
    MANIFEST_PATH,
    NEXT_REQUIRED_STEP,
    PHASE_SCOPE,
    RAW_DIR,
    REPORT_PATH,
    SCHEMA_VERSION,
    TASK_ID,
    TEST_RESULTS_PATH,
    validate_legacy_s09_p1_artifacts,
    validate_stage8_dependency,
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
)
REQUIRED_HARD_BLOCKS = (
    "raw_data_mutation_forbidden",
    "raw_value_publication_forbidden",
    "field_header_plaintext_publication_forbidden",
    "business_amount_values_remain_private_ref_or_hash_only",
    "project_cost_fact_layer_structural_only",
    "upstream_zero_delta_failure_blocks_formal_calculation",
    "upstream_source_difference_blocks_formal_calculation",
    "upstream_entity_matching_review_queue_blocks_formal_calculation",
    "s09_p2_margin_cash_margin_not_performed",
    "s09_p3_scope_reconciliation_not_performed",
    "stage9_review_not_performed",
    "formal_report_release_blocked",
    "lineage_full_check_not_performed",
    "raw_value_matching_not_performed",
    "github_upload_deferred_until_stage10_batch",
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


def validate_v013_s09_p1_project_cost_fact_layer_replay(manifest_path: Path = MANIFEST_PATH) -> dict[str, Any]:
    errors: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    manifest = read_json(manifest_path)
    s08 = validate_stage8_dependency()
    legacy = validate_legacy_s09_p1_artifacts()

    require(manifest.get("schema_version") == SCHEMA_VERSION, "manifest schema mismatch")
    require(manifest.get("project_id") == "KMFA", "project_id mismatch")
    require(manifest.get("version") == "0.1.3", "version mismatch")
    require(manifest.get("stage_id") == "S09", "stage_id must be S09")
    require(manifest.get("phase_id") == "S09-P1", "phase_id must be S09-P1")
    require(manifest.get("task_id") == TASK_ID, "task_id mismatch")
    require(manifest.get("phase_scope") == PHASE_SCOPE, "phase scope mismatch")
    require(
        manifest.get("status")
        == "completed_validated_local_only_no_go_upload_deferred_project_cost_fact_layer_replayed",
        "status mismatch",
    )
    require(manifest.get("completed_task_ids") == ["S9PAT01", "S9PAT02", "S9PAT03"], "completed tasks mismatch")
    require(
        manifest.get("acceptance_ids") == ["ACC-V013-S09-P1-PROJECT-COST-FACT-LAYER-REPLAY"],
        "acceptance ids mismatch",
    )
    require(manifest.get("s08_stage_review_dependency_validated") is True, "Stage 8 dependency flag mismatch")
    require(s08.get("stage_id") == "S08", "Stage 8 dependency did not validate")
    require(manifest.get("legacy_s09_p1_dependency_validated") is True, "legacy S09-P1 dependency flag mismatch")

    progress = manifest.get("stage9_phase_progress", {})
    require(progress.get("completed_phase_count") == 1, "completed phase count mismatch")
    require(progress.get("total_phase_count") == 3, "total phase count mismatch")
    require(progress.get("derived_percent_bps") == 3333, "derived percent bps mismatch")
    require(progress.get("derived_percent_label") == "33.33%", "derived percent label mismatch")
    require(progress.get("s09_p1_performed") is True, "S09-P1 must be performed")
    require(progress.get("s09_p2_performed") is False, "S09-P2 must not be performed")
    require(progress.get("s09_p3_performed") is False, "S09-P3 must not be performed")
    require(progress.get("stage9_review_performed") is False, "Stage 9 review must not be performed")

    summary = manifest.get("legacy_s09_p1_summary", {})
    expected_summary = {
        "required_metric_count": 6,
        "cost_category_count": 9,
        "fact_record_count": 4,
        "unallocated_pool_count": 9,
        "authority_locked_field_count": 40,
        "authority_excluded_field_count": 5,
        "business_entity_type_count": 8,
        "project_identity_profile_count": 4,
        "manual_review_queue_count": 3,
        "unresolved_difference_count": 1,
        "zero_delta_fail_count": 1,
        "blocked_quality_result_count": 2,
    }
    for key, expected in expected_summary.items():
        require(summary.get(key) == expected, f"summary.{key} mismatch")
        require(summary.get(key) == legacy.get(key), f"legacy summary mismatch for {key}")
    require(summary.get("required_metrics") == legacy["required_metrics"], "required metrics mismatch")
    require(summary.get("required_cost_categories") == legacy["required_cost_categories"], "cost categories mismatch")
    require(summary.get("formal_calculation_blocked") is True, "formal calculation must stay blocked")
    require(
        summary.get("fact_layer_status") == "structural_fact_layer_blocked_for_formal_calculation",
        "fact layer status mismatch",
    )

    policy = manifest.get("fact_layer_policy", {})
    require(policy.get("metric_hash_ref_count") == 24, "metric hash ref count mismatch")
    require(policy.get("metric_private_ref_count") == 24, "metric private ref count mismatch")
    require(policy.get("cost_category_hash_ref_count") == 36, "cost category hash ref count mismatch")
    require(policy.get("cost_category_private_ref_count") == 36, "cost category private ref count mismatch")
    require(policy.get("formal_calculation_allowed") is False, "formal calculation must be false")
    require(policy.get("formal_calculation_allowed_count") == 0, "formal calculation allowed count mismatch")
    require(policy.get("metric_values_public_committed_count") == 0, "metric values public count mismatch")
    require(policy.get("fact_raw_layer_write_allowed_count") == 0, "fact raw write count mismatch")
    require(policy.get("pool_amount_public_committed_count") == 0, "pool public amount count mismatch")
    require(policy.get("pool_raw_layer_write_allowed_count") == 0, "pool raw write count mismatch")
    require(policy.get("pending_pool_assignment_count") == 9, "pending pool count mismatch")
    for key in (
        "metric_hash_ref_count",
        "metric_private_ref_count",
        "cost_category_hash_ref_count",
        "cost_category_private_ref_count",
        "formal_calculation_allowed_count",
        "metric_values_public_committed_count",
        "fact_raw_layer_write_allowed_count",
        "pool_amount_public_committed_count",
        "pool_raw_layer_write_allowed_count",
        "pending_pool_assignment_count",
        "quality_gate_false_count",
        "public_safety_false_count",
    ):
        require(policy.get(key) == legacy.get(key), f"legacy policy mismatch for {key}")

    phase_boundaries = manifest.get("phase_boundaries", {})
    require(phase_boundaries.get("s09_p1_scope_included") is True, "S09-P1 scope flag mismatch")
    for key in (
        "s09_p2_margin_cash_margin_scope_included",
        "s09_p3_scope_reconciliation_scope_included",
        "stage9_review_scope_included",
        "s10_report_scope_included",
        "lineage_full_check_scope_included",
        "formal_report_scope_included",
        "ui_scope_included",
        "external_connector_scope_included",
        "github_upload_scope_included",
    ):
        require(phase_boundaries.get(key) is False, f"phase_boundaries.{key} must be false")

    quality = manifest.get("quality_gate", {})
    require(quality.get("current_data_quality_grade") == "Q4", "quality grade mismatch")
    require(quality.get("current_report_grade") == "D", "report grade mismatch")
    require(quality.get("release_permission") == "blocked", "release permission mismatch")
    for key in (
        "q5_formal_calculation_allowed",
        "formal_report_allowed",
        "business_decision_basis_allowed",
        "business_execution_allowed",
        "delivery_allowed",
        "raw_layer_write_allowed",
        "automatic_external_action_allowed",
    ):
        require(quality.get(key) is False, f"quality_gate.{key} must be false")
    require(quality.get("q5_formal_calculation_allowed_count") == 0, "Q5 calculation count mismatch")
    require(quality.get("formal_report_allowed_count") == 0, "formal report count mismatch")

    upload = manifest.get("github_upload", {})
    require(upload.get("github_upload_ready_next_gate") is False, "upload ready must stay false")
    require(upload.get("github_upload_deferred_until_stage10_batch") is True, "upload must be deferred")
    require(upload.get("github_upload_performed") is False, "upload performed must be false")
    require(
        upload.get("github_upload_status") == "not_uploaded_deferred_until_stage10_batch",
        "upload status mismatch",
    )

    raw_boundary = manifest.get("raw_data_boundary", {})
    require(raw_boundary.get("local_raw_data_dir") == RAW_DIR, "raw directory mismatch")
    require(
        raw_boundary.get("local_raw_data_dir_role") == "user_finance_raw_private_inbox",
        "raw directory role mismatch",
    )
    require(raw_boundary.get("codex_read_allowed_only_when_phase_requires") is True, "raw read policy mismatch")
    for key in (
        "codex_read_required_by_this_phase",
        "codex_read_performed_by_this_phase",
        "codex_list_performed_by_this_phase",
        "codex_modify_allowed",
        "codex_delete_allowed",
        "codex_move_allowed",
        "codex_rename_allowed",
        "codex_overwrite_allowed",
        "codex_generate_inside_allowed",
        "codex_create_extra_files_inside_allowed",
        "github_commit_allowed",
    ):
        require(raw_boundary.get(key) is False, f"raw_data_boundary.{key} must be false")
    require(
        raw_boundary.get("private_runtime_output_dir") == "KMFA/.codex_private_runtime/",
        "private runtime output dir mismatch",
    )

    safety = manifest.get("public_repo_safety", {})
    for key in PUBLIC_SAFETY_FALSE_KEYS:
        require(safety.get(key) is False, f"public_repo_safety.{key} must be false")

    hard_blocks = manifest.get("hard_blocks", [])
    require(isinstance(hard_blocks, list), "hard_blocks must be a list")
    for block in REQUIRED_HARD_BLOCKS:
        require(block in hard_blocks, f"missing hard block: {block}")
    require(manifest.get("hard_block_count") == len(REQUIRED_HARD_BLOCKS), "hard block count mismatch")
    require(manifest.get("next_required_step") == NEXT_REQUIRED_STEP, "next_required_step mismatch")

    artifact_refs = manifest.get("artifact_refs", {})
    for key in (
        "legacy_manifest",
        "legacy_fact_records",
        "legacy_unallocated_pool",
        "legacy_stage_manifest",
        "manifest",
        "report",
        "test_results",
        "generator",
        "validator",
        "unit_test",
    ):
        path = Path(artifact_refs.get(key, ""))
        require(path.exists(), f"missing artifact ref: {key} -> {path}")

    for ref in manifest.get("evidence_refs", []):
        require(Path(ref).exists(), f"missing evidence ref: {ref}")
    for evidence in (MANIFEST_PATH, REPORT_PATH, TEST_RESULTS_PATH):
        require(evidence.exists(), f"missing public evidence: {evidence}")
        if evidence.exists():
            text = evidence.read_text(encoding="utf-8")
            for forbidden in FORBIDDEN_EVIDENCE_TEXT:
                require(forbidden not in text, f"forbidden public evidence text {forbidden!r} in {evidence}")

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
        "phase_id": manifest["phase_id"],
        "phase_scope": manifest["phase_scope"],
        "status": manifest["status"],
        "required_metric_count": summary["required_metric_count"],
        "cost_category_count": summary["cost_category_count"],
        "fact_record_count": summary["fact_record_count"],
        "unallocated_pool_count": summary["unallocated_pool_count"],
        "authority_locked_field_count": summary["authority_locked_field_count"],
        "authority_excluded_field_count": summary["authority_excluded_field_count"],
        "business_entity_type_count": summary["business_entity_type_count"],
        "manual_review_queue_count": summary["manual_review_queue_count"],
        "unresolved_difference_count": summary["unresolved_difference_count"],
        "zero_delta_fail_count": summary["zero_delta_fail_count"],
        "blocked_quality_result_count": summary["blocked_quality_result_count"],
        "formal_calculation_allowed": policy["formal_calculation_allowed"],
        "formal_report_allowed": quality["formal_report_allowed"],
        "s09_p2_performed": progress["s09_p2_performed"],
        "s09_p3_performed": progress["s09_p3_performed"],
        "stage9_review_performed": progress["stage9_review_performed"],
        "github_upload_performed": upload["github_upload_performed"],
        "github_upload_deferred_until_stage10_batch": upload["github_upload_deferred_until_stage10_batch"],
        "raw_dir_read_performed": raw_boundary["codex_read_performed_by_this_phase"],
        "raw_dir_mutation_performed": raw_boundary["codex_modify_allowed"],
        "next_required_step": manifest["next_required_step"],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA v0.1.3 S09-P1 project cost fact layer replay.")
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    args = parser.parse_args(argv)

    result = validate_v013_s09_p1_project_cost_fact_layer_replay(args.manifest)
    print(
        "PASS: KMFA v0.1.3 S09-P1 project cost fact layer replay validated "
        f"(metrics={result['required_metric_count']}, categories={result['cost_category_count']}, "
        f"fact_records={result['fact_record_count']}, unallocated_pool={result['unallocated_pool_count']}, "
        "s09p2=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
