#!/usr/bin/env python3
"""Validate KMFA v0.1.4 S06-P1 zero-delta validator evidence."""

from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

from KMFA.tools.check_v014_s05_stage_review import validate_v014_s05_stage_review
from KMFA.tools.v014_s06_p1_zero_delta_validator import (
    ACCEPTANCE_ID,
    MANIFEST_PATH,
    MISMATCH_FIXTURE_PATH,
    MISMATCH_REPORT_PATH,
    MISMATCH_RESULT_PATH,
    NEXT_INSTRUCTION,
    NEXT_PHASE,
    PASS_FIXTURE_PATH,
    PASS_RESULT_PATH,
    PHASE_SCOPE,
    REPORT_PATH,
    REQUIRED_REPORT_COLUMNS,
    RISK_REGISTER_PATH,
    ROLLBACK_PATH,
    SCHEMA_VERSION,
    TASK_ID,
    TEST_RESULTS_PATH,
)
from KMFA.tools.zero_delta_validator import validate_fixture_file


RAW_INBOX = "/Users/linzezhang/Downloads/KMFA_MetaData"
FORBIDDEN_TRACKED_SUFFIXES = (".zip", ".xlsx", ".xls", ".xlsm", ".pdf", ".sqlite", ".sqlite3", ".db")
PUBLIC_FALSE_KEYS = (
    "raw_business_data_committed",
    "zip_committed",
    "excel_workbook_committed",
    "pdf_committed",
    "private_csv_committed",
    "sqlite_or_db_committed",
    "credentials_committed",
    "raw_filenames_committed",
    "raw_hashes_committed",
    "directory_tree_plaintext_committed",
    "zip_member_names_committed",
    "sheet_names_committed",
    "source_header_plaintext_committed",
    "row_or_cell_values_committed",
    "source_or_normalized_values_committed",
    "business_values_committed",
)
BOUNDARY_FALSE_KEYS = (
    "raw_inbox_read_required_by_this_phase",
    "raw_inbox_read_by_this_phase",
    "raw_inbox_listed_by_this_phase",
    "raw_inbox_stat_by_this_phase",
    "raw_inbox_hashed_by_this_phase",
    "raw_inbox_modified_by_this_phase",
    "raw_inbox_deleted_by_this_phase",
    "raw_inbox_moved_by_this_phase",
    "raw_inbox_renamed_by_this_phase",
    "raw_inbox_overwritten_by_this_phase",
    "raw_inbox_written_by_this_phase",
    "raw_inbox_mutated_by_this_phase",
    "private_runtime_written_by_this_phase",
    "github_commit_allowed_for_raw",
)
FORBIDDEN_PUBLIC_KEYS = {
    "actual_package_sha256",
    "expected_package_sha256",
    "member_sha256",
    "member_name",
    "member_path",
    "package_name",
    "candidate_label",
    "candidate_label_hash",
    "sheet_name",
    "raw_value",
    "normalized_value",
    "source_header_text",
    "cell_value",
    "row_value",
    "business_value",
    "bank_account_number",
    "identity_document_number",
    "connector_token",
    "connector_password",
    "api_key",
    "private_key",
}
FORBIDDEN_PUBLIC_TEXT = (
    "actual_package_sha256",
    "expected_package_sha256",
    "member_sha256:",
    "member_name:",
    "member_path:",
    "package_name:",
    "candidate_label:",
    "candidate_label_hash:",
    "sheet_name:",
    "raw_value:",
    "normalized_value:",
    "source_header_text:",
    "cell_value:",
    "row_value:",
    "business_value:",
    "bank_statement:",
    "contract_full_text:",
    "salary_detail:",
    "tax_filing:",
    "connector_token:",
    "connector_password:",
    "api_key:",
    "private_key:",
    "-----" "BEGIN",
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


def walk_public(value: Any, errors: list[str], path: str = "$") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key in FORBIDDEN_PUBLIC_KEYS:
                errors.append(f"forbidden public key {key!r} at {path}")
            walk_public(child, errors, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            walk_public(child, errors, f"{path}[{index}]")


def check_public_safe_file(path: Path, errors: list[str]) -> None:
    require(path.exists(), f"missing evidence file: {path}", errors)
    if not path.exists():
        return
    require(path.suffix.lower() not in FORBIDDEN_TRACKED_SUFFIXES, f"forbidden evidence extension: {path}", errors)
    if path.suffix.lower() in {".md", ".json", ".jsonl", ".csv", ".yaml", ".yml"}:
        text = path.read_text(encoding="utf-8", errors="ignore")
        lower = text.lower()
        for forbidden in FORBIDDEN_PUBLIC_TEXT:
            require(forbidden.lower() not in lower, f"forbidden public text {forbidden!r} in {path}", errors)
        for pattern in STRICT_SECRET_PATTERNS:
            require(pattern.search(text) is None, f"high-signal secret pattern in {path}: {pattern.pattern}", errors)


def read_mismatch_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise ValidationError(f"missing mismatch report: {path}")
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def validate_v014_s06_p1_zero_delta_validator(manifest_path: Path = MANIFEST_PATH) -> dict[str, Any]:
    errors: list[str] = []
    manifest = read_json(manifest_path)
    s05 = validate_v014_s05_stage_review()
    pass_fixture = read_json(PASS_FIXTURE_PATH)
    mismatch_fixture = read_json(MISMATCH_FIXTURE_PATH)
    pass_result = read_json(PASS_RESULT_PATH)
    mismatch_result = read_json(MISMATCH_RESULT_PATH)
    recomputed_pass = validate_fixture_file(PASS_FIXTURE_PATH)
    recomputed_mismatch = validate_fixture_file(MISMATCH_FIXTURE_PATH)
    mismatch_rows = read_mismatch_rows(MISMATCH_REPORT_PATH)

    for public_value in (manifest, pass_fixture, mismatch_fixture, pass_result, mismatch_result):
        walk_public(public_value, errors)

    require(manifest.get("schema_version") == SCHEMA_VERSION, "schema mismatch", errors)
    require(manifest.get("project_id") == "KMFA", "project_id mismatch", errors)
    require(manifest.get("version") == "0.1.4", "version mismatch", errors)
    require(manifest.get("stage_id") == "S06", "stage_id must be S06", errors)
    require(manifest.get("phase_id") == "S06-P1", "phase_id must be S06-P1", errors)
    require(manifest.get("phase_scope") == PHASE_SCOPE, "phase scope mismatch", errors)
    require(manifest.get("task_id") == TASK_ID, "task id mismatch", errors)
    require(manifest.get("acceptance_id") == ACCEPTANCE_ID, "acceptance id mismatch", errors)
    require(
        manifest.get("status") == "completed_validated_local_only_no_go_upload_deferred_zero_delta_validator",
        "status mismatch",
        errors,
    )
    require(manifest.get("completed_task_ids") == ["S06P1T01", "S06P1T02", "S06P1T03"], "task ids mismatch", errors)

    require(manifest.get("s05_stage_review_dependency_validated") is True, "S05 dependency flag mismatch", errors)
    require(s05.get("stage_id") == "S05", "S05 dependency stage mismatch", errors)
    require(s05.get("status") == manifest.get("s05_dependency_summary", {}).get("status"), "S05 status mismatch", errors)
    require(s05.get("open_review_finding_count") == 0, "S05 review must have zero open findings", errors)
    require(s05.get("github_upload_performed") is False, "S05 upload must remain deferred", errors)
    require(s05.get("next_recommended_phase") == "S06-P1", "S05 next phase must point to S06-P1", errors)
    s05_gate = s05.get("stage_gate", {})
    require(s05_gate.get("authority_record_count") == 45, "S05 authority count mismatch", errors)
    require(s05_gate.get("q5_calculation_baseline_locked_count") == 40, "S05 locked baseline count mismatch", errors)
    require(s05_gate.get("excluded_cross_source_support_only_count") == 5, "S05 excluded count mismatch", errors)
    require(s05_gate.get("zero_delta_validated_count") == 0, "S05 pre-S06 zero-delta count mismatch", errors)

    require(pass_fixture.get("public_safe_fixture_only") is True, "pass fixture public-safe flag mismatch", errors)
    require(pass_fixture.get("raw_business_data_used") is False, "pass fixture raw flag mismatch", errors)
    require(mismatch_fixture.get("public_safe_fixture_only") is True, "mismatch fixture public-safe flag mismatch", errors)
    require(mismatch_fixture.get("raw_business_data_used") is False, "mismatch fixture raw flag mismatch", errors)
    require(pass_result == recomputed_pass, "pass result must match recomputed validator output", errors)
    require(mismatch_result == recomputed_mismatch, "mismatch result must match recomputed validator output", errors)
    require(pass_result.get("zero_delta_passed") is True, "pass fixture must pass zero-delta", errors)
    require(pass_result.get("mismatch_count") == 0, "pass fixture mismatch count must be 0", errors)
    require(mismatch_result.get("zero_delta_passed") is False, "one-cent fixture must fail zero-delta", errors)
    require(mismatch_result.get("minimum_fail_difference_cents") == 1, "minimum fail difference must be 1 cent", errors)
    require(mismatch_result.get("mismatch_count") == 1, "mismatch fixture must have one mismatch", errors)
    mismatch = mismatch_result.get("mismatches", [{}])[0]
    require(mismatch.get("difference_cents") == 1, "mismatch difference must be 1 cent", errors)
    require(mismatch.get("authoritative_value_cents") == 10000, "authoritative cents mismatch", errors)
    require(mismatch.get("system_value_cents") == 9999, "system cents mismatch", errors)
    require(len(mismatch_rows) == 1, "mismatch report must contain one row", errors)
    if mismatch_rows:
        row = mismatch_rows[0]
        for column in REQUIRED_REPORT_COLUMNS:
            require(column in row, f"missing mismatch report column: {column}", errors)
        require(row.get("difference_cents") == "1", "mismatch report difference must be 1", errors)

    require(manifest.get("pass_fixture_record_count") == 2, "pass fixture record count mismatch", errors)
    require(manifest.get("pass_fixture_amount_field_count") == 4, "pass fixture amount field count mismatch", errors)
    require(manifest.get("pass_fixture_field_comparison_count") == 8, "comparison count mismatch", errors)
    require(manifest.get("zero_delta_passed_for_public_safe_fixture") is True, "pass fixture summary mismatch", errors)
    require(manifest.get("pass_fixture_mismatch_count") == 0, "pass fixture mismatch summary mismatch", errors)
    require(manifest.get("one_cent_mismatch_detected") is True, "one cent mismatch flag mismatch", errors)
    require(manifest.get("minimum_fail_difference_cents") == 1, "minimum fail summary mismatch", errors)
    require(manifest.get("mismatch_fixture_mismatch_count") == 1, "mismatch summary mismatch", errors)
    require(manifest.get("mismatch_report_generated") is True, "mismatch report generated flag mismatch", errors)
    require(manifest.get("mismatch_report_contains_required_columns") is True, "mismatch column flag mismatch", errors)
    for column in REQUIRED_REPORT_COLUMNS:
        require(column in manifest.get("mismatch_report_columns", []), f"manifest missing report column: {column}", errors)
    require(manifest.get("integer_cent_comparison_only") is True, "integer cent flag mismatch", errors)
    require(manifest.get("float_money_allowed") is False, "float money must be false", errors)
    require(manifest.get("zero_delta_validator_available") is True, "validator availability mismatch", errors)
    require(manifest.get("actual_business_zero_delta_validated") is False, "actual business zero-delta belongs to later gated work", errors)
    require(manifest.get("raw_business_data_used") is False, "raw business data must be false", errors)

    for key in (
        "difference_queue_created",
        "metadata_quality_written",
        "s06_p2_started",
        "s06_p3_started",
        "stage6_review_performed",
        "github_upload_performed",
        "raw_value_matching_performed",
        "lineage_full_check_performed",
        "formal_report_performed",
        "live_connector_called",
        "opme_deep_coupling_performed",
        "business_execution_performed",
    ):
        require(manifest.get(key) is False, f"{key} must be false", errors)
    require(
        manifest.get("github_upload_status") == "not_uploaded_deferred_until_v014_stage1_18_complete",
        "github upload status mismatch",
        errors,
    )

    boundary = manifest.get("raw_data_boundary", {})
    require(boundary.get("raw_inbox_path") == RAW_INBOX, "raw inbox path mismatch", errors)
    for key in BOUNDARY_FALSE_KEYS:
        require(boundary.get(key) is False, f"raw_data_boundary.{key} must be false", errors)

    safety = manifest.get("public_repo_safety", {})
    for key in PUBLIC_FALSE_KEYS:
        require(safety.get(key) is False, f"public_repo_safety.{key} must be false", errors)

    release = manifest.get("release_state", {})
    require(release.get("current_data_quality_grade") == "Q4", "data quality grade mismatch", errors)
    require(release.get("current_report_grade") == "D", "report grade mismatch", errors)
    require(release.get("current_go_no_go") == "NO_GO", "Go/No-Go mismatch", errors)
    require(release.get("release_permission") == "blocked", "release permission mismatch", errors)
    for key in (
        "delivery_allowed",
        "formal_report_allowed",
        "business_decision_basis_allowed",
        "business_execution_allowed",
        "github_main_upload_allowed",
    ):
        require(release.get(key) is False, f"release_state.{key} must be false", errors)

    require(manifest.get("next_recommended_phase") == NEXT_PHASE, "next phase mismatch", errors)
    require(manifest.get("next_phase_instruction") == NEXT_INSTRUCTION, "next instruction mismatch", errors)

    for ref in manifest.get("evidence_refs", []):
        check_public_safe_file(Path(ref), errors)
    for path in (
        REPORT_PATH,
        TEST_RESULTS_PATH,
        RISK_REGISTER_PATH,
        ROLLBACK_PATH,
        MANIFEST_PATH,
        PASS_FIXTURE_PATH,
        PASS_RESULT_PATH,
        MISMATCH_FIXTURE_PATH,
        MISMATCH_RESULT_PATH,
        MISMATCH_REPORT_PATH,
    ):
        check_public_safe_file(path, errors)

    tracked_files = git_output(["ls-files", "KMFA"]).splitlines()
    forbidden_tracked = [
        path for path in tracked_files if path.lower().endswith(FORBIDDEN_TRACKED_SUFFIXES) or ".codex_private_runtime/" in path
    ]
    require(not forbidden_tracked, f"forbidden tracked raw/private artifacts: {forbidden_tracked}", errors)
    require("codex/kmfa" in git_output(["status", "--short", "--branch"]), "git status must be on codex/kmfa", errors)

    if errors:
        raise ValidationError("\n".join(f"- {error}" for error in errors))
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA v0.1.4 S06-P1 zero-delta validator evidence.")
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    args = parser.parse_args(argv)
    try:
        manifest = validate_v014_s06_p1_zero_delta_validator(args.manifest)
    except ValidationError as exc:
        print("FAIL: KMFA v0.1.4 S06-P1 zero-delta validator validation failed")
        print(exc)
        return 1
    print(
        "PASS: KMFA v0.1.4 S06-P1 zero-delta validator validated "
        f"(comparisons={manifest['pass_fixture_field_comparison_count']}, "
        f"one_cent_mismatch={str(manifest['one_cent_mismatch_detected']).lower()}, "
        f"difference_queue={str(manifest['difference_queue_created']).lower()}, "
        f"github_upload={str(manifest['github_upload_performed']).lower()})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
