#!/usr/bin/env python3
"""Validate KMFA v0.1.4 Stage 9 review evidence."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any

from KMFA.tools.check_v013_s09_stage_review import validate_v013_s09_stage_review
from KMFA.tools.check_v014_s09_p1_project_cost_fact_layer import validate_v014_s09_p1_project_cost_fact_layer
from KMFA.tools.check_v014_s09_p2_margin_cash_margin import validate_v014_s09_p2_margin_cash_margin
from KMFA.tools.check_v014_s09_p3_scope_reconciliation import validate_v014_s09_p3_scope_reconciliation
from KMFA.tools.v014_s09_stage_review import (
    ACCEPTANCE_ID,
    LEGACY_STAGE9_REVIEW_MANIFEST,
    MANIFEST_PATH,
    NEXT_INSTRUCTION,
    NEXT_PHASE,
    PHASE_MANIFESTS,
    REPORT_PATH,
    REVIEW_SCOPE,
    RISK_REGISTER_PATH,
    ROLLBACK_PATH,
    SCHEMA_VERSION,
    TASK_ID,
    TEST_RESULTS_PATH,
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
    "amount_a_cents:",
    "amount_b_cents:",
    "delta_cents:",
    "bank_statement",
    "contract_full_text",
    "salary_detail",
    "tax_filing",
    "connector_token",
    "connector_password",
    "-----" "BEGIN",
    "s" "k-",
)
RAW_REVIEW_FALSE_KEYS = (
    "raw_inbox_read_by_this_review",
    "raw_inbox_listed_by_this_review",
    "raw_inbox_inventory_by_this_review",
    "raw_inbox_stat_by_this_review",
    "raw_inbox_hashed_by_this_review",
    "raw_inbox_modified_by_this_review",
    "raw_inbox_deleted_by_this_review",
    "raw_inbox_moved_by_this_review",
    "raw_inbox_renamed_by_this_review",
    "raw_inbox_overwritten_by_this_review",
    "raw_inbox_written_by_this_review",
    "raw_inbox_mutated_by_this_review",
)
RAW_REVIEW_TRUE_KEYS = (
    "s09_p1_raw_inbox_all_false",
    "s09_p2_raw_inbox_all_false",
    "s09_p3_raw_inbox_all_false",
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
    "business_content_committed",
    "business_amount_values_committed",
    "project_or_customer_plaintext_committed",
    "margin_or_reconciliation_source_values_committed",
    "formal_report_committed",
)
RELEASE_FALSE_KEYS = (
    "delivery_allowed",
    "formal_report_allowed",
    "business_decision_basis_allowed",
    "business_execution_allowed",
    "github_main_upload_allowed",
)
VALIDATION_KEYS = (
    "py_compile",
    "s09_p1_validator",
    "s09_p2_validator",
    "s09_p3_validator",
    "legacy_s09_p1_validator",
    "legacy_s09_p1_unit",
    "legacy_s09_p2_validator",
    "legacy_s09_p2_unit",
    "legacy_s09_p3_validator",
    "legacy_s09_p3_unit",
    "legacy_stage9_review_validator",
    "stage_review_validator",
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
    "public_stage9_semantic_scan",
    "diff_check",
)
REQUIRED_HARD_BLOCKS = (
    "raw_data_mutation_forbidden",
    "raw_value_publication_forbidden",
    "field_header_plaintext_publication_forbidden",
    "business_amount_values_remain_private_ref_or_hash_only",
    "project_cost_fact_layer_formal_calculation_blocked",
    "authority_system_overwrite_forbidden",
    "pending_owner_or_authorized_difference_review_blocks_rerun",
    "confirmed_resolution_count_zero_blocks_derived_metric_rerun",
    "formal_report_release_blocked",
    "lineage_full_check_not_performed",
    "raw_value_matching_not_performed",
    "s10_p1_not_performed",
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


def validate_v014_s09_stage_review(manifest_path: Path = MANIFEST_PATH) -> dict[str, Any]:
    errors: list[str] = []
    manifest = read_json(manifest_path)
    p1 = validate_v014_s09_p1_project_cost_fact_layer()
    p2 = validate_v014_s09_p2_margin_cash_margin()
    p3 = validate_v014_s09_p3_scope_reconciliation()
    legacy = validate_v013_s09_stage_review()
    walk_forbidden_keys(manifest, errors)

    require(manifest.get("schema_version") == SCHEMA_VERSION, "schema mismatch", errors)
    require(manifest.get("project_id") == "KMFA", "project_id mismatch", errors)
    require(manifest.get("version") == "0.1.4", "version mismatch", errors)
    require(manifest.get("stage_id") == "S09", "stage_id must be S09", errors)
    require(manifest.get("review_id") == TASK_ID, "review id mismatch", errors)
    require(manifest.get("task_id") == TASK_ID, "task id mismatch", errors)
    require(manifest.get("acceptance_id") == ACCEPTANCE_ID, "acceptance id mismatch", errors)
    require(manifest.get("review_scope") == REVIEW_SCOPE, "review scope mismatch", errors)
    require(
        manifest.get("status") == "review_passed_local_only_no_go_upload_deferred_until_v014_stage1_18_complete",
        "status mismatch",
        errors,
    )
    require(manifest.get("stage_review_performed") is True, "stage review must be true", errors)
    require(manifest.get("s10_p1_performed") is False, "S10-P1 must not be performed", errors)
    require(manifest.get("github_upload_ready_next_gate") is False, "upload ready next gate must be false", errors)
    require(
        manifest.get("github_upload_deferred_until_v014_stage1_18_complete") is True,
        "upload deferral flag mismatch",
        errors,
    )
    require(manifest.get("github_upload_performed") is False, "GitHub upload must not be performed", errors)
    require(
        manifest.get("github_upload_status") == "not_uploaded_deferred_until_v014_stage1_18_complete",
        "GitHub upload status mismatch",
        errors,
    )
    require(manifest.get("legacy_stage9_review_validated") is True, "legacy Stage 9 review flag mismatch", errors)
    require(manifest.get("legacy_stage9_review_manifest") == LEGACY_STAGE9_REVIEW_MANIFEST, "legacy manifest ref mismatch", errors)
    require(legacy.get("stage_id") == "S09", "legacy Stage 9 review did not validate", errors)
    require(
        manifest.get("legacy_stage9_upload_artifacts_current_gate") is False,
        "legacy upload artifacts must not be current",
        errors,
    )
    require(manifest.get("legacy_stage9_github_upload_performed") is False, "legacy upload performed flag mismatch", errors)
    for key in (
        "app_reinstall_performed",
        "raw_value_matching_performed",
        "raw_content_matching_performed",
        "lineage_full_check_completed",
        "formal_report_performed",
        "live_connector_called",
        "opme_deep_coupling_performed",
        "redcircle_automatic_connector_called",
        "business_execution_performed",
    ):
        require(manifest.get(key) is False, f"{key} must be false", errors)

    require(manifest.get("phase_count") == 3, "phase count mismatch", errors)
    require(
        manifest.get("phase_results") == {"S09-P1": "PASS", "S09-P2": "PASS", "S09-P3": "PASS"},
        "phase results mismatch",
        errors,
    )
    require(p1.get("phase_id") == "S09-P1", "S09-P1 validator did not return S09-P1", errors)
    require(p2.get("phase_id") == "S09-P2", "S09-P2 validator did not return S09-P2", errors)
    require(p3.get("phase_id") == "S09-P3", "S09-P3 validator did not return S09-P3", errors)
    for key in ("s09_p1_dependency_validated", "s09_p2_dependency_validated", "s09_p3_dependency_validated"):
        require(manifest.get(key) is True, f"{key} must be true", errors)

    reviewed = manifest.get("reviewed_phase_manifests", {})
    for phase, ref in PHASE_MANIFESTS.items():
        require(reviewed.get(phase) == ref, f"{phase} manifest ref mismatch", errors)
        require(Path(ref).exists(), f"missing phase manifest: {ref}", errors)

    require(manifest.get("open_review_finding_count") == 0, "open findings must be 0", errors)
    require(manifest.get("fixed_review_finding_count") == 1, "fixed findings must be 1", errors)
    findings = manifest.get("review_findings", [])
    require(isinstance(findings, list) and len(findings) == 1, "review findings must contain one fixed finding", errors)
    if isinstance(findings, list) and findings:
        require(findings[0].get("finding_id") == "KMFA-V014-S09-STAGE-REVIEW-F01", "finding id mismatch", errors)
        require(findings[0].get("status") == "fixed", "finding must be fixed", errors)

    gate = manifest.get("stage_gate", {})
    expected_gate = {
        "project_cost_required_metric_count": 6,
        "project_cost_category_count": 9,
        "project_cost_fact_record_count": 4,
        "project_cost_unallocated_pool_count": 9,
        "project_cost_authority_locked_field_count": 40,
        "project_cost_authority_excluded_field_count": 5,
        "project_cost_business_entity_type_count": 8,
        "project_cost_manual_review_queue_count": 3,
        "project_cost_unresolved_difference_count": 1,
        "project_cost_zero_delta_fail_count": 1,
        "project_cost_blocked_quality_result_count": 2,
        "project_cost_formal_calculation_allowed_count": 0,
        "margin_required_metric_count": 4,
        "margin_project_cost_fact_record_count": 4,
        "margin_record_count": 4,
        "margin_difference_summary_count": 12,
        "margin_authority_field_group_count": 8,
        "margin_authority_system_overwrite_allowed_count": 0,
        "margin_public_amount_values_committed_count": 0,
        "reconciliation_record_count": 12,
        "reconciliation_domain_control_count": 6,
        "reconciliation_required_domain_count": 6,
        "reconciliation_upstream_margin_record_count": 4,
        "reconciliation_source_difference_summary_count": 12,
        "reconciliation_confirmed_resolution_count": 0,
        "reconciliation_pending_resolution_count": 12,
        "reconciliation_derived_metric_rerun_allowed_count": 0,
        "reconciliation_formal_report_rerun_allowed_count": 0,
        "q5_calculation_baseline_allowed_count": 0,
        "formal_report_allowed_count": 0,
        "current_data_quality_grade": "Q4",
        "current_report_grade": "D",
        "release_permission": "blocked",
    }
    for key, value in expected_gate.items():
        require(gate.get(key) == value, f"stage_gate.{key} mismatch", errors)

    phase_summary = manifest.get("phase_summary", {})
    for phase in ("S09-P1", "S09-P2", "S09-P3"):
        summary = phase_summary.get(phase, {})
        require(summary.get("stage9_review_performed") is False, f"{phase} phase review flag mismatch", errors)
        require(summary.get("github_upload_performed") is False, f"{phase} upload flag mismatch", errors)
        require(summary.get("raw_inbox_read_performed") is False, f"{phase} raw read flag mismatch", errors)

    raw = manifest.get("raw_data_boundary", {})
    require(raw.get("raw_inbox_ref") == "operator-designated raw/private inbox outside repository", "raw inbox ref mismatch", errors)
    for key in RAW_REVIEW_FALSE_KEYS:
        require(raw.get(key) is False, f"raw_data_boundary.{key} must be false", errors)
    for key in RAW_REVIEW_TRUE_KEYS:
        require(raw.get(key) is True, f"raw_data_boundary.{key} must be true", errors)

    safety = manifest.get("public_repo_safety", {})
    for key in PUBLIC_SAFETY_FALSE_KEYS:
        require(safety.get(key) is False, f"public_repo_safety.{key} must be false", errors)

    release = manifest.get("release_state", {})
    for key in RELEASE_FALSE_KEYS:
        require(release.get(key) is False, f"release_state.{key} must be false", errors)
    require(release.get("current_go_no_go") == "NO_GO", "Go/No-Go mismatch", errors)
    require(release.get("current_data_quality_grade") == "Q4", "data quality mismatch", errors)
    require(release.get("current_report_grade") == "D", "report grade mismatch", errors)
    require(release.get("release_permission") == "blocked", "release permission mismatch", errors)

    hard_blocks = manifest.get("hard_blocks", [])
    require(isinstance(hard_blocks, list), "hard_blocks must be a list", errors)
    for block in REQUIRED_HARD_BLOCKS:
        require(block in hard_blocks, f"missing hard block: {block}", errors)
    require(manifest.get("hard_block_count") == len(REQUIRED_HARD_BLOCKS), "hard block count mismatch", errors)

    validation = manifest.get("validation_summary", {})
    for key in VALIDATION_KEYS:
        require(validation.get(key) == "PASS", f"validation_summary.{key} must be PASS", errors)

    for ref in manifest.get("evidence_refs", []):
        check_public_safe_file(Path(ref), errors)
    for path in (MANIFEST_PATH, REPORT_PATH, TEST_RESULTS_PATH, RISK_REGISTER_PATH, ROLLBACK_PATH):
        check_public_safe_file(path, errors)

    reviewed_head = str(manifest.get("reviewed_head", ""))
    require(len(reviewed_head) == 40 and all(char in "0123456789abcdef" for char in reviewed_head), "reviewed_head mismatch", errors)
    require("codex/kmfa" in git_output(["status", "--short", "--branch"]), "branch must be codex/kmfa", errors)
    require(manifest.get("next_recommended_phase") == NEXT_PHASE, "next phase mismatch", errors)
    require(manifest.get("next_phase_instruction") == NEXT_INSTRUCTION, "next instruction mismatch", errors)

    if errors:
        raise ValidationError("\n".join(errors))
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA v0.1.4 Stage 9 review evidence.")
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    args = parser.parse_args(argv)
    try:
        result = validate_v014_s09_stage_review(args.manifest)
    except ValidationError as exc:
        print("FAIL: KMFA v0.1.4 Stage 9 review validation failed")
        print(exc)
        return 1
    gate = result["stage_gate"]
    print(
        "PASS: KMFA v0.1.4 Stage 9 review validated "
        f"(cost_metrics={gate['project_cost_required_metric_count']}, "
        f"margin_metrics={gate['margin_required_metric_count']}, "
        f"reconciliation_records={gate['reconciliation_record_count']}, "
        "s10_p1=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
