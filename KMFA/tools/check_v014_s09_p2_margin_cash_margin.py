#!/usr/bin/env python3
"""Validate KMFA v0.1.4 S09-P2 margin and cash margin evidence."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any

from KMFA.tools.v014_s09_p2_margin_cash_margin import (
    ACCEPTANCE_ID,
    MANIFEST_PATH,
    NEXT_INSTRUCTION,
    NEXT_PHASE,
    PHASE_SCOPE,
    RAW_INBOX_REF,
    REPORT_PATH,
    RISK_REGISTER_PATH,
    ROLLBACK_PLAN_PATH,
    SCHEMA_VERSION,
    TASK_ID,
    TEST_RESULTS_PATH,
    validate_legacy_s09_p2_artifacts,
    validate_s09_p1_dependency,
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
    "authority_system_overwrite_forbidden",
    "public_margin_amount_values_forbidden",
    "upstream_zero_delta_failure_blocks_formal_calculation",
    "upstream_source_difference_blocks_formal_calculation",
    "upstream_entity_matching_review_queue_blocks_formal_calculation",
    "s09_p3_scope_reconciliation_not_performed",
    "stage9_review_not_performed",
    "formal_report_release_blocked",
    "lineage_full_check_not_performed",
    "raw_value_matching_not_performed",
    "github_upload_deferred_until_v014_stage1_18_complete",
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
RAW_INBOX_DIRECTORY_TOKEN = "KMFA" + "_MetaData"
LOCAL_DOWNLOADS_RAW_PATH_PATTERN = re.compile(r"/Users/[^\s\"'`]+/Downloads/[^\s\"'`]+")
RAW_FALSE_KEYS = (
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


def validate_v014_s09_p2_margin_cash_margin(manifest_path: Path = MANIFEST_PATH) -> dict[str, Any]:
    errors: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    manifest = read_json(manifest_path)
    s09_p1 = validate_s09_p1_dependency()
    legacy = validate_legacy_s09_p2_artifacts()

    require(manifest.get("schema_version") == SCHEMA_VERSION, "manifest schema mismatch")
    require(manifest.get("project_id") == "KMFA", "project_id mismatch")
    require(manifest.get("version") == "0.1.4", "version mismatch")
    require(manifest.get("stage_id") == "S09", "stage_id must be S09")
    require(manifest.get("phase_id") == "S09-P2", "phase_id must be S09-P2")
    require(manifest.get("task_id") == TASK_ID, "task_id mismatch")
    require(manifest.get("phase_scope") == PHASE_SCOPE, "phase scope mismatch")
    require(
        manifest.get("status") == "completed_validated_local_only_no_go_upload_deferred_margin_cash_margin",
        "status mismatch",
    )
    require(manifest.get("completed_task_ids") == ["S9PBT01", "S9PBT02", "S9PBT03"], "completed tasks mismatch")
    require(manifest.get("acceptance_id") == ACCEPTANCE_ID, "acceptance id mismatch")
    require(manifest.get("s09_p1_dependency_validated") is True, "S09-P1 dependency flag mismatch")
    require(s09_p1.get("phase_id") == "S09-P1", "S09-P1 dependency did not validate")
    require(manifest.get("legacy_s09_p2_dependency_validated") is True, "legacy S09-P2 flag mismatch")

    progress = manifest.get("stage9_phase_progress", {})
    require(progress.get("completed_phase_count") == 2, "completed phase count mismatch")
    require(progress.get("total_phase_count") == 3, "total phase count mismatch")
    require(progress.get("derived_percent_bps") == 6667, "derived percent bps mismatch")
    require(progress.get("derived_percent_label") == "66.67%", "derived percent label mismatch")
    require(progress.get("s09_p1_performed") is True, "S09-P1 must be performed")
    require(progress.get("s09_p2_performed") is True, "S09-P2 must be performed")
    require(progress.get("s09_p3_performed") is False, "S09-P3 must not be performed")
    require(progress.get("stage9_review_performed") is False, "Stage 9 review must not be performed")

    summary = manifest.get("legacy_s09_p2_summary", {})
    expected_summary = {
        "required_margin_metric_count": 4,
        "project_cost_fact_record_count": 4,
        "margin_record_count": 4,
        "difference_summary_count": 12,
        "authority_field_group_count": 8,
        "upstream_manual_review_queue_count": 3,
        "upstream_unresolved_difference_count": 1,
        "zero_delta_fail_count": 1,
        "blocked_quality_result_count": 2,
    }
    for key, expected in expected_summary.items():
        require(summary.get(key) == expected, f"summary.{key} mismatch")
        require(summary.get(key) == legacy.get(key), f"legacy summary mismatch for {key}")
    require(summary.get("required_margin_metrics") == legacy["required_margin_metrics"], "margin metrics mismatch")
    require(summary.get("formal_calculation_blocked") is True, "formal calculation must stay blocked")
    require(summary.get("calculation_status") == "margin_slots_recorded_blocked_for_formal_report", "status mismatch")

    policy = manifest.get("margin_cash_margin_policy", {})
    require(policy.get("difference_type_count") == 3, "difference type count mismatch")
    require(
        policy.get("difference_records_by_type")
        == {
            "authority_vs_system_gross_margin_rate": 4,
            "authority_vs_system_gross_profit": 4,
            "cash_vs_accrual_gross_profit": 4,
        },
        "difference records by type mismatch",
    )
    require(policy.get("authority_hash_ref_count") == 8, "authority hash ref count mismatch")
    require(policy.get("authority_private_ref_count") == 8, "authority private ref count mismatch")
    require(policy.get("system_hash_ref_count") == 8, "system hash ref count mismatch")
    require(policy.get("system_private_ref_count") == 8, "system private ref count mismatch")
    require(policy.get("cash_hash_ref_count") == 8, "cash hash ref count mismatch")
    require(policy.get("cash_private_ref_count") == 8, "cash private ref count mismatch")
    require(policy.get("authority_system_overwrite_allowed") is False, "overwrite policy must be false")
    require(policy.get("authority_system_overwrite_allowed_count") == 0, "overwrite count mismatch")
    require(policy.get("public_amount_values_committed_count") == 0, "public amount count mismatch")
    require(policy.get("raw_layer_write_allowed_count") == 0, "raw write count mismatch")
    require(policy.get("formal_report_allowed_count") == 0, "formal report count mismatch")
    require(policy.get("s09_p3_reconciliation_performed_count") == 0, "S09-P3 performed count mismatch")
    for key in (
        "difference_type_count",
        "difference_records_by_type",
        "authority_hash_ref_count",
        "authority_private_ref_count",
        "system_hash_ref_count",
        "system_private_ref_count",
        "cash_hash_ref_count",
        "cash_private_ref_count",
        "authority_system_overwrite_allowed_count",
        "public_amount_values_committed_count",
        "raw_layer_write_allowed_count",
        "formal_report_allowed_count",
        "s09_p3_reconciliation_performed_count",
        "quality_gate_false_count",
        "public_safety_false_count",
        "record_public_safety_false_count",
        "difference_public_safety_false_count",
    ):
        require(policy.get(key) == legacy.get(key), f"legacy policy mismatch for {key}")

    phase_boundaries = manifest.get("phase_boundaries", {})
    require(phase_boundaries.get("s09_p1_dependency_included") is True, "S09-P1 dependency flag mismatch")
    require(
        phase_boundaries.get("s09_p2_margin_cash_margin_scope_included") is True,
        "S09-P2 scope flag mismatch",
    )
    for key in (
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
    require(upload.get("github_upload_deferred_until_v014_stage1_18_complete") is True, "upload must be deferred")
    require(upload.get("github_upload_performed") is False, "upload performed must be false")
    require(
        upload.get("github_upload_status") == "not_uploaded_deferred_until_v014_stage1_18_complete",
        "upload status mismatch",
    )

    raw_boundary = manifest.get("raw_data_boundary", {})
    require(raw_boundary.get("raw_inbox_ref") == RAW_INBOX_REF, "raw inbox ref mismatch")
    for key in RAW_FALSE_KEYS:
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
    require(manifest.get("next_recommended_phase") == NEXT_PHASE, "next phase mismatch")
    require(manifest.get("next_phase_instruction") == NEXT_INSTRUCTION, "next instruction mismatch")

    artifact_refs = manifest.get("artifact_refs", {})
    for key in (
        "legacy_manifest",
        "legacy_margin_records",
        "legacy_difference_summary",
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
        require(path.exists(), f"missing artifact ref: {key} -> {path}")

    for ref in manifest.get("evidence_refs", []):
        require(Path(ref).exists(), f"missing evidence ref: {ref}")
    for evidence in (MANIFEST_PATH, REPORT_PATH, TEST_RESULTS_PATH, RISK_REGISTER_PATH, ROLLBACK_PLAN_PATH):
        require(evidence.exists(), f"missing public evidence: {evidence}")
        if evidence.exists():
            text = evidence.read_text(encoding="utf-8")
            for forbidden in FORBIDDEN_EVIDENCE_TEXT:
                require(forbidden not in text, f"forbidden public evidence text {forbidden!r} in {evidence}")
            require(
                RAW_INBOX_DIRECTORY_TOKEN not in text,
                f"forbidden raw inbox directory token in {evidence}",
            )
            require(
                LOCAL_DOWNLOADS_RAW_PATH_PATTERN.search(text) is None,
                f"forbidden local Downloads raw path in {evidence}",
            )

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
        "required_margin_metric_count": summary["required_margin_metric_count"],
        "project_cost_fact_record_count": summary["project_cost_fact_record_count"],
        "margin_record_count": summary["margin_record_count"],
        "difference_summary_count": summary["difference_summary_count"],
        "authority_field_group_count": summary["authority_field_group_count"],
        "upstream_manual_review_queue_count": summary["upstream_manual_review_queue_count"],
        "upstream_unresolved_difference_count": summary["upstream_unresolved_difference_count"],
        "zero_delta_fail_count": summary["zero_delta_fail_count"],
        "blocked_quality_result_count": summary["blocked_quality_result_count"],
        "authority_system_overwrite_allowed_count": policy["authority_system_overwrite_allowed_count"],
        "public_amount_values_committed_count": policy["public_amount_values_committed_count"],
        "formal_report_allowed": quality["formal_report_allowed"],
        "s09_p3_performed": progress["s09_p3_performed"],
        "stage9_review_performed": progress["stage9_review_performed"],
        "github_upload_performed": upload["github_upload_performed"],
        "github_upload_deferred_until_v014_stage1_18_complete": upload["github_upload_deferred_until_v014_stage1_18_complete"],
        "raw_inbox_read_performed": raw_boundary["raw_inbox_read_by_this_phase"],
        "raw_inbox_mutation_performed": raw_boundary["raw_inbox_mutated_by_this_phase"],
        "next_recommended_phase": manifest["next_recommended_phase"],
        "next_phase_instruction": manifest["next_phase_instruction"],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA v0.1.4 S09-P2 margin and cash margin.")
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    args = parser.parse_args(argv)

    result = validate_v014_s09_p2_margin_cash_margin(args.manifest)
    print(
        "PASS: KMFA v0.1.4 S09-P2 margin and cash margin validated "
        f"(margin_metrics={result['required_margin_metric_count']}, "
        f"margin_records={result['margin_record_count']}, "
        f"difference_summary={result['difference_summary_count']}, "
        "s09p3=false, stage9_review=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
