#!/usr/bin/env python3
"""Validate KMFA v0.1.4 S10-P2 report trust grade evidence."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any

from KMFA.tools.v014_s10_p2_report_trust_grade import (
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
    validate_legacy_s10_p2_artifacts,
    validate_s10_p1_dependency,
    validate_v013_replay_dependency,
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
    "zero_delta_failed",
    "unresolved_critical_difference",
    "missing_required_lineage",
    "missing_human_confirmation_for_A",
    "raw_data_mutation_forbidden",
    "raw_value_publication_forbidden",
    "field_header_plaintext_publication_forbidden",
    "complete_trusted_report_display_blocked",
    "formal_report_release_blocked",
    "business_decision_basis_blocked",
    "s10_p3_export_not_performed",
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


def validate_v014_s10_p2_report_trust_grade(manifest_path: Path = MANIFEST_PATH) -> dict[str, Any]:
    errors: list[str] = []
    manifest = read_json(manifest_path)
    s10_p1 = validate_s10_p1_dependency()
    v013 = validate_v013_replay_dependency()
    legacy = validate_legacy_s10_p2_artifacts()

    require(manifest.get("schema_version") == SCHEMA_VERSION, "manifest schema mismatch", errors)
    require(manifest.get("project_id") == "KMFA", "project_id mismatch", errors)
    require(manifest.get("version") == "0.1.4", "version mismatch", errors)
    require(manifest.get("stage_id") == "S10", "stage_id must be S10", errors)
    require(manifest.get("phase_id") == "S10-P2", "phase_id must be S10-P2", errors)
    require(manifest.get("phase_scope") == PHASE_SCOPE, "phase scope mismatch", errors)
    require(manifest.get("task_id") == TASK_ID, "task_id mismatch", errors)
    require(
        manifest.get("status") == "completed_validated_local_only_no_go_upload_deferred_report_trust_grade_locked",
        "status mismatch",
        errors,
    )
    require(manifest.get("completed_task_ids") == ["S10P2T01", "S10P2T02", "S10P2T03"], "tasks mismatch", errors)
    require(manifest.get("acceptance_ids") == [ACCEPTANCE_ID], "acceptance id mismatch", errors)
    require(manifest.get("s10_p1_dependency_validated") is True, "S10-P1 dependency flag mismatch", errors)
    require(s10_p1.get("phase_id") == "S10-P1", "S10-P1 dependency did not validate", errors)
    require(manifest.get("legacy_s10_p2_dependency_validated") is True, "legacy S10-P2 flag mismatch", errors)
    require(manifest.get("v013_s10_p2_replay_validated") is True, "v013 replay flag mismatch", errors)
    require(v013.get("phase_id") == "S10-P2", "v013 S10-P2 replay did not validate", errors)

    progress = manifest.get("stage10_phase_progress", {})
    require(progress.get("completed_phase_count") == 2, "completed phase count mismatch", errors)
    require(progress.get("total_phase_count") == 3, "total phase count mismatch", errors)
    require(progress.get("derived_percent_bps") == 6667, "derived percent bps mismatch", errors)
    require(progress.get("derived_percent_label") == "66.67%", "derived percent label mismatch", errors)
    require(progress.get("s10_p1_performed") is True, "S10-P1 must be performed", errors)
    require(progress.get("s10_p2_performed") is True, "S10-P2 must be performed", errors)
    require(progress.get("s10_p3_performed") is False, "S10-P3 must not be performed", errors)
    require(progress.get("stage10_review_performed") is False, "Stage 10 review must not be performed", errors)

    summary = manifest.get("report_trust_grade_summary", {})
    expected_summary = {
        "template_count": 2,
        "report_grade_record_count": 2,
        "grade_distribution": {"D": 2},
        "pending_reconciliation_count": 12,
        "confirmed_resolution_count": 0,
        "source_quality_grade": "Q4",
        "zero_delta_passed": False,
        "full_trusted_report_allowed_count": 0,
        "formal_report_count": 0,
        "export_artifact_count": 0,
        "complete_trusted_report_display_allowed_count": 0,
        "business_decision_basis_allowed_count": 0,
    }
    for key, expected in expected_summary.items():
        require(summary.get(key) == expected, f"summary.{key} mismatch", errors)
        require(summary.get(key) == legacy.get(key), f"legacy summary mismatch for {key}", errors)
    require(summary.get("computed_grades") == ["D"], "computed grades mismatch", errors)
    require(summary.get("release_permissions") == ["blocked_decision_use"], "release permissions mismatch", errors)
    hard_block_counts = summary.get("hard_block_counts", {})
    for block in (
        "zero_delta_failed",
        "unresolved_critical_difference",
        "missing_required_lineage",
        "missing_human_confirmation_for_A",
    ):
        require(hard_block_counts.get(block) == 2, f"legacy hard block count mismatch for {block}", errors)
    require(summary.get("hard_block_count") == 8, "legacy hard block count mismatch", errors)

    policy = manifest.get("report_trust_grade_policy", {})
    require(policy.get("allowed_report_grades") == ["A", "B", "C", "D"], "allowed grades mismatch", errors)
    require(policy.get("current_report_grade") == "D", "current report grade mismatch", errors)
    require(policy.get("current_data_quality_grade") == "Q4", "current data quality grade mismatch", errors)
    require(
        policy.get("grade_driver_dimensions") == ["data_quality", "difference_status", "human_confirmation", "timeliness"],
        "grade driver dimensions mismatch",
        errors,
    )
    require(
        policy.get("timeliness_status") == "current_metadata_timestamp_present_no_stale_signal",
        "timeliness status mismatch",
        errors,
    )
    for field_name in (
        "report_record_version",
        "template_version",
        "formula_version",
        "mapping_version",
        "field_mapping_version",
        "grade_policy_version",
        "release_gate_version",
        "content_hash",
    ):
        require(policy.get(field_name) == legacy.get(field_name), f"policy legacy mismatch for {field_name}", errors)
    require(policy.get("record_version_binding_required") is True, "version binding flag mismatch", errors)
    require(policy.get("record_version_binding_count") == 2, "version binding count mismatch", errors)
    require(policy.get("complete_trusted_report_display_allowed") is False, "complete trusted display must be false", errors)
    require(policy.get("full_trusted_report_allowed") is False, "full trusted report must be false", errors)
    require(policy.get("formal_report_allowed") is False, "formal report must be false", errors)
    require(policy.get("business_decision_basis_allowed") is False, "business decision basis must be false", errors)
    require(policy.get("s10_p3_export_allowed") is False, "S10-P3 export must be false", errors)
    require(policy.get("report_runtime_scope_count") == 2, "report runtime scope count mismatch", errors)
    require(policy.get("quality_gate_false_count") == legacy["quality_gate_false_count"], "quality false count mismatch", errors)
    require(policy.get("stage_scope_false_count") == legacy["stage_scope_false_count"], "scope false count mismatch", errors)
    require(policy.get("public_safety_false_count") == legacy["public_safety_false_count"], "safety false count mismatch", errors)

    version_binding = manifest.get("version_binding_requirements", {})
    for field_name in (
        "report_record_version",
        "formula_version",
        "mapping_version",
        "field_mapping_version",
        "grade_policy_version",
        "release_gate_version",
    ):
        require(version_binding.get(field_name) == policy.get(field_name), f"version binding {field_name} mismatch", errors)
    require(version_binding.get("record_version_binding_count") == 2, "version binding count mismatch", errors)

    phase = manifest.get("phase_boundaries", {})
    require(phase.get("s10_p1_report_templates_dependency_included") is True, "S10-P1 dependency flag mismatch", errors)
    require(phase.get("s10_p2_report_trust_grade_scope_included") is True, "S10-P2 scope flag mismatch", errors)
    for key in (
        "s10_p3_report_export_scope_included",
        "stage10_review_scope_included",
        "lineage_full_check_scope_included",
        "raw_value_matching_scope_included",
        "formal_report_scope_included",
        "report_export_scope_included",
        "ui_runtime_scope_included",
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
    require(quality.get("confirmed_resolution_count") == 0, "confirmed resolution count mismatch", errors)
    require(quality.get("zero_delta_passed") is False, "zero delta mismatch", errors)
    for key in (
        "complete_trusted_report_display_allowed",
        "full_trusted_report_allowed",
        "formal_report_allowed",
        "business_decision_basis_allowed",
        "business_execution_allowed",
        "delivery_allowed",
        "raw_layer_write_allowed",
        "automatic_external_action_allowed",
        "s10_p3_export_allowed",
        "html_export_allowed",
        "csv_excel_export_allowed",
        "pdf_export_allowed",
    ):
        require(quality.get(key) is False, f"quality_gate.{key} must be false", errors)

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
        "legacy_records",
        "legacy_stage_manifest",
        "v014_s10_p1_manifest",
        "v013_s10_p2_replay_manifest",
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
        "report_grade_record_count": summary["report_grade_record_count"],
        "grade_distribution": summary["grade_distribution"],
        "pending_reconciliation_count": summary["pending_reconciliation_count"],
        "confirmed_resolution_count": summary["confirmed_resolution_count"],
        "source_quality_grade": summary["source_quality_grade"],
        "zero_delta_passed": summary["zero_delta_passed"],
        "complete_trusted_report_display_allowed": quality["complete_trusted_report_display_allowed"],
        "full_trusted_report_allowed": quality["full_trusted_report_allowed"],
        "formal_report_allowed": quality["formal_report_allowed"],
        "business_decision_basis_allowed": quality["business_decision_basis_allowed"],
        "record_version_binding_count": policy["record_version_binding_count"],
        "s10_p3_export_scope_included": phase["s10_p3_report_export_scope_included"],
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
    parser = argparse.ArgumentParser(description="Validate KMFA v0.1.4 S10-P2 report trust grade.")
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    args = parser.parse_args(argv)

    result = validate_v014_s10_p2_report_trust_grade(args.manifest)
    print(
        "PASS: KMFA v0.1.4 S10-P2 report trust grade validated "
        f"(grade_records={result['report_grade_record_count']}, "
        f"grade_distribution={result['grade_distribution']}, "
        f"pending_reconciliation={result['pending_reconciliation_count']}, "
        "formal_report=false, s10_p3=false, stage10_review=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
