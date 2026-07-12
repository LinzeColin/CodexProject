#!/usr/bin/env python3
"""Validate KMFA v0.1.4 S09-P1 project cost fact layer evidence."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any

from KMFA.tools.check_v014_s08_stage_review import validate_v014_s08_stage_review
from KMFA.tools.project_cost_fact_layer import REQUIRED_COST_CATEGORIES, REQUIRED_FACT_METRICS
from KMFA.tools.v014_s09_p1_project_cost_fact_layer import (
    ACCEPTANCE_ID,
    MANIFEST_PATH,
    NEXT_INSTRUCTION,
    NEXT_PHASE,
    PHASE_SCOPE,
    REPORT_PATH,
    RISK_REGISTER_PATH,
    ROLLBACK_PATH,
    SCHEMA_VERSION,
    TASK_ID,
    TEST_RESULTS_PATH,
    validate_legacy_s09_p1_artifacts,
)


FORBIDDEN_PUBLIC_SUFFIXES = (".zip", ".xlsx", ".xls", ".xlsm", ".pdf", ".sqlite", ".sqlite3", ".db")
RAW_INBOX_DIRECTORY_TOKEN = "KMFA" + "_MetaData"
LOCAL_DOWNLOADS_RAW_PATH_PATTERN = re.compile(r"/Users/[^\s\"'`]+/Downloads/[^\s\"'`]+")
STRICT_SECRET_PATTERNS = (
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"(?i)(password|passwd|secret|api_key|token)\s*=\s*[^\s,;]{8,}"),
)
FORBIDDEN_PUBLIC_KEYS = {
    "raw_value",
    "normalized_value",
    "original_value",
    "plaintext_value",
    "source_header_text",
    "field_key",
    "field_label",
    "file_hash",
    "sheet_name",
    "member_name",
    "member_path",
    "package_name",
    "business_value",
    "row_value",
    "cell_value",
    "plaintext_content",
    "full_file_text",
    "raw_file_bytes",
    "original_filename",
    "bank_account_number",
    "identity_document_number",
    "project_name_plaintext",
    "customer_name_plaintext",
    "counterparty_plaintext",
    "company_entity_plaintext",
}
FORBIDDEN_TEXT = (
    "raw_value:",
    "normalized_value:",
    "plaintext_value:",
    "source_header_text:",
    "field_key:",
    "field_label:",
    "file_hash:",
    "sheet_name:",
    "member_name:",
    "package_name:",
    "business_value:",
    "row_value:",
    "cell_value:",
    "authoritative_value_cents",
    "system_value_cents",
    "pdf_value_cents",
    "excel_value_cents",
    "bank_statement",
    "contract_full_text",
    "salary_detail",
    "tax_filing",
    "connector_token",
    "connector_password",
    "-----" "BEGIN",
    "s" "k-",
)
FALSE_BOUNDARY_KEYS = (
    "s09_p2_margin_cash_margin_scope_included",
    "s09_p3_scope_reconciliation_scope_included",
    "stage9_review_scope_included",
    "s10_report_scope_included",
    "lineage_full_check_scope_included",
    "formal_report_scope_included",
    "ui_scope_included",
    "external_connector_scope_included",
    "github_upload_scope_included",
    "app_reinstall_scope_included",
)
QUALITY_FALSE_KEYS = (
    "q5_formal_calculation_allowed",
    "formal_report_allowed",
    "business_decision_basis_allowed",
    "business_execution_allowed",
    "delivery_allowed",
    "raw_layer_write_allowed",
    "automatic_external_action_allowed",
)
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
PUBLIC_SAFETY_FALSE_KEYS = (
    "raw_business_data_committed",
    "raw_archive_or_workbook_committed",
    "raw_document_committed",
    "private_csv_committed",
    "private_table_or_database_committed",
    "credentials_committed",
    "connector_secret_committed",
    "field_plaintext_committed",
    "source_header_plaintext_committed",
    "raw_file_identifiers_committed",
    "raw_content_identifiers_committed",
    "private_record_content_committed",
    "business_amount_values_committed",
    "business_content_committed",
    "project_or_customer_plaintext_committed",
    "normalized_source_values_committed",
)
VALIDATION_KEYS = (
    "py_compile",
    "stage8_review_dependency_validator",
    "legacy_s09_p1_generator",
    "legacy_s09_p1_validator",
    "legacy_s09_p1_unit",
    "v014_s09_p1_generator",
    "v014_s09_p1_validator",
    "focused_unit_test",
    "no_omission_check",
    "no_float_money_check",
    "governance_validator",
    "lean_governance_validator",
    "governance_sync_validator",
    "structured_parse",
    "ruby_yaml_parse",
    "raw_private_scan",
    "secret_scan",
    "public_s09_p1_semantic_scan",
    "diff_check",
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
    "github_upload_deferred_until_v014_stage1_18_complete",
    "app_reinstall_not_performed",
    "business_execution_blocked",
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


def walk_forbidden_keys(value: Any, errors: list[str], path: str = "$") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key in FORBIDDEN_PUBLIC_KEYS:
                errors.append(f"forbidden public key {key!r} at {path}")
            walk_forbidden_keys(child, errors, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            walk_forbidden_keys(child, errors, f"{path}[{index}]")


def check_public_safe_file(path: Path, errors: list[str]) -> None:
    require(path.exists(), f"missing public-safe file: {path}", errors)
    if not path.exists():
        return
    require(path.suffix.lower() not in FORBIDDEN_PUBLIC_SUFFIXES, f"forbidden public extension: {path}", errors)
    if path.suffix.lower() not in {".md", ".json", ".jsonl", ".csv", ".yaml", ".yml"}:
        return
    text = path.read_text(encoding="utf-8", errors="ignore")
    lower = text.lower()
    for forbidden in FORBIDDEN_TEXT:
        require(forbidden.lower() not in lower, f"forbidden public text {forbidden!r} in {path}", errors)
    require(RAW_INBOX_DIRECTORY_TOKEN.lower() not in lower, f"forbidden raw inbox directory token in {path}", errors)
    require(LOCAL_DOWNLOADS_RAW_PATH_PATTERN.search(text) is None, f"forbidden local Downloads raw path in {path}", errors)
    for pattern in STRICT_SECRET_PATTERNS:
        require(pattern.search(text) is None, f"high-signal secret pattern in {path}: {pattern.pattern}", errors)


def validate_v014_s09_p1_project_cost_fact_layer(manifest_path: Path = MANIFEST_PATH) -> dict[str, Any]:
    errors: list[str] = []
    manifest = read_json(manifest_path)
    stage8 = validate_v014_s08_stage_review()
    legacy = validate_legacy_s09_p1_artifacts()
    walk_forbidden_keys(manifest, errors)

    require(manifest.get("schema_version") == SCHEMA_VERSION, "schema mismatch", errors)
    require(manifest.get("project_id") == "KMFA", "project_id mismatch", errors)
    require(manifest.get("version") == "0.1.4", "version mismatch", errors)
    require(manifest.get("stage_id") == "S09", "stage_id must be S09", errors)
    require(manifest.get("phase_id") == "S09-P1", "phase_id must be S09-P1", errors)
    require(manifest.get("task_id") == TASK_ID, "task id mismatch", errors)
    require(manifest.get("acceptance_id") == ACCEPTANCE_ID, "acceptance id mismatch", errors)
    require(manifest.get("phase_scope") == PHASE_SCOPE, "phase scope mismatch", errors)
    require(
        manifest.get("status") == "completed_validated_local_only_no_go_upload_deferred_project_cost_fact_layer",
        "status mismatch",
        errors,
    )
    require(stage8.get("stage_id") == "S08", "Stage 8 dependency did not validate", errors)
    require(manifest.get("s08_stage_review_dependency_validated") is True, "Stage 8 dependency flag mismatch", errors)
    require(manifest.get("legacy_s09_p1_dependency_validated") is True, "legacy S09-P1 flag mismatch", errors)
    require(manifest.get("completed_task_ids") == ["S9PAT01", "S9PAT02", "S9PAT03"], "task ids mismatch", errors)

    progress = manifest.get("stage9_phase_progress", {})
    require(progress.get("completed_phase_count") == 1, "completed phase count mismatch", errors)
    require(progress.get("total_phase_count") == 3, "total phase count mismatch", errors)
    require(progress.get("derived_percent_bps") == 3333, "derived percent bps mismatch", errors)
    require(progress.get("derived_percent_label") == "33.33%", "derived percent label mismatch", errors)
    require(progress.get("s09_p1_performed") is True, "S09-P1 must be true", errors)
    require(progress.get("s09_p2_performed") is False, "S09-P2 must be false", errors)
    require(progress.get("s09_p3_performed") is False, "S09-P3 must be false", errors)
    require(progress.get("stage9_review_performed") is False, "Stage 9 review must be false", errors)

    summary = manifest.get("project_cost_fact_layer_summary", {})
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
        require(summary.get(key) == expected, f"summary.{key} mismatch", errors)
        require(summary.get(key) == legacy.get(key), f"legacy summary.{key} mismatch", errors)
    require(tuple(summary.get("required_metrics", [])) == REQUIRED_FACT_METRICS, "required metrics mismatch", errors)
    require(
        tuple(summary.get("required_cost_categories", [])) == REQUIRED_COST_CATEGORIES,
        "cost categories mismatch",
        errors,
    )
    require(summary.get("formal_calculation_blocked") is True, "formal calculation must stay blocked", errors)
    require(
        summary.get("fact_layer_status") == "structural_fact_layer_blocked_for_formal_calculation",
        "fact layer status mismatch",
        errors,
    )

    policy = manifest.get("fact_layer_policy", {})
    expected_policy = {
        "metric_hash_ref_count": 24,
        "metric_private_ref_count": 24,
        "cost_category_hash_ref_count": 36,
        "cost_category_private_ref_count": 36,
        "formal_calculation_allowed_count": 0,
        "metric_values_public_committed_count": 0,
        "fact_raw_layer_write_allowed_count": 0,
        "pool_amount_public_committed_count": 0,
        "pool_raw_layer_write_allowed_count": 0,
        "pending_pool_assignment_count": 9,
    }
    for key, expected in expected_policy.items():
        require(policy.get(key) == expected, f"policy.{key} mismatch", errors)
        require(policy.get(key) == legacy.get(key), f"legacy policy.{key} mismatch", errors)
    require(policy.get("formal_calculation_allowed") is False, "formal calculation must be false", errors)

    boundaries = manifest.get("phase_boundaries", {})
    require(boundaries.get("s09_p1_scope_included") is True, "S09-P1 scope flag mismatch", errors)
    for key in FALSE_BOUNDARY_KEYS:
        require(boundaries.get(key) is False, f"phase_boundaries.{key} must be false", errors)

    quality = manifest.get("quality_gate", {})
    require(quality.get("current_go_no_go") == "NO_GO", "Go/No-Go mismatch", errors)
    require(quality.get("current_data_quality_grade") == "Q4", "data quality mismatch", errors)
    require(quality.get("current_report_grade") == "D", "report grade mismatch", errors)
    require(quality.get("release_permission") == "blocked", "release permission mismatch", errors)
    for key in QUALITY_FALSE_KEYS:
        require(quality.get(key) is False, f"quality_gate.{key} must be false", errors)
    require(quality.get("q5_formal_calculation_allowed_count") == 0, "Q5 calculation count mismatch", errors)
    require(quality.get("formal_report_allowed_count") == 0, "formal report count mismatch", errors)

    upload = manifest.get("github_upload", {})
    require(upload.get("github_upload_ready_next_gate") is False, "upload next gate must be false", errors)
    require(upload.get("github_upload_performed") is False, "upload performed must be false", errors)
    require(upload.get("github_upload_deferred_until_v014_stage1_18_complete") is True, "upload deferral mismatch", errors)
    require(
        upload.get("github_upload_status") == "not_uploaded_deferred_until_v014_stage1_18_complete",
        "upload status mismatch",
        errors,
    )

    raw = manifest.get("raw_data_boundary", {})
    require(raw.get("raw_inbox_ref") == "operator-designated raw/private inbox outside repository", "raw ref mismatch", errors)
    for key in RAW_FALSE_KEYS:
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

    validation = manifest.get("validation_summary", {})
    for key in VALIDATION_KEYS:
        require(validation.get(key) == "PASS", f"validation_summary.{key} must be PASS", errors)

    require(manifest.get("next_recommended_phase") == NEXT_PHASE, "next phase mismatch", errors)
    require(manifest.get("next_phase_instruction") == NEXT_INSTRUCTION, "next instruction mismatch", errors)

    artifact_refs = manifest.get("artifact_refs", {})
    for key in (
        "legacy_manifest",
        "legacy_fact_records",
        "legacy_unallocated_pool",
        "legacy_stage_manifest",
        "v013_replay_manifest",
        "manifest",
        "report",
        "test_results",
        "risk_register",
        "rollback_plan",
        "generator",
        "validator",
        "unit_test",
    ):
        path = Path(str(artifact_refs.get(key, "")))
        require(path.exists(), f"missing artifact ref: {key} -> {path}", errors)

    for ref in manifest.get("evidence_refs", []):
        require(Path(ref).exists(), f"missing evidence ref: {ref}", errors)
    for evidence in (MANIFEST_PATH, REPORT_PATH, TEST_RESULTS_PATH, RISK_REGISTER_PATH, ROLLBACK_PATH):
        check_public_safe_file(evidence, errors)

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
    parser = argparse.ArgumentParser(description="Validate KMFA v0.1.4 S09-P1 project cost fact layer.")
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    args = parser.parse_args(argv)

    manifest = validate_v014_s09_p1_project_cost_fact_layer(args.manifest)
    summary = manifest["project_cost_fact_layer_summary"]
    print(
        "PASS: KMFA v0.1.4 S09-P1 project cost fact layer validated "
        f"(metrics={summary['required_metric_count']}, categories={summary['cost_category_count']}, "
        f"fact_records={summary['fact_record_count']}, unallocated_pool={summary['unallocated_pool_count']}, "
        "s09p2=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
