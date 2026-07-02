#!/usr/bin/env python3
"""Validate KMFA v0.1.3 S06-P1 zero-delta replay evidence."""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from KMFA.tools.check_v013_s05_stage_review import validate_v013_s05_stage_review
from KMFA.tools.v013_s06_p1_zero_delta_replay import (
    MANIFEST_PATH,
    MISMATCH_FIXTURE_PATH,
    MISMATCH_REPORT_PATH,
    MISMATCH_RESULT_PATH,
    NEXT_REQUIRED_STEP,
    PASS_FIXTURE_PATH,
    PASS_RESULT_PATH,
    PHASE_SCOPE,
    REPORT_PATH,
    SCHEMA_VERSION,
    TASK_ID,
    TEST_RESULTS_PATH,
)
from KMFA.tools.zero_delta_validator import validate_fixture_file


RAW_DIR = "/Users/linzezhang/Downloads/KMFA_MetaData"
PUBLIC_SAFETY_FALSE_KEYS = (
    "raw_business_data_committed",
    "zip_committed",
    "excel_workbook_committed",
    "pdf_committed",
    "private_csv_committed",
    "sqlite_or_db_committed",
    "credentials_committed",
    "field_plaintext_committed",
    "raw_file_names_committed",
    "raw_file_hashes_committed",
    "raw_business_values_committed",
    "sheet_names_committed",
    "zip_member_names_committed",
)
FORBIDDEN_PUBLIC_SUFFIXES = (".zip", ".xlsx", ".xls", ".xlsm", ".pdf", ".sqlite", ".db")
FORBIDDEN_EVIDENCE_TEXT = (
    "raw_value:",
    "normalized_value:",
    "source_header_text:",
    "actual_package_sha256",
    "member_sha256:",
    "bank_statement",
    "contract_full_text",
    "salary_detail",
    "tax_filing",
    "-----" "BEGIN",
    "s" "k-",
)
REQUIRED_REPORT_COLUMNS = (
    "record_id",
    "source",
    "field",
    "authoritative_value_cents",
    "system_value_cents",
    "difference_cents",
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


def _read_mismatch_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def validate_v013_s06_p1_zero_delta_replay(manifest_path: Path = MANIFEST_PATH) -> dict[str, Any]:
    errors: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    manifest = read_json(manifest_path)
    s05 = validate_v013_s05_stage_review()
    pass_fixture = read_json(PASS_FIXTURE_PATH)
    mismatch_fixture = read_json(MISMATCH_FIXTURE_PATH)
    pass_result = read_json(PASS_RESULT_PATH)
    mismatch_result = read_json(MISMATCH_RESULT_PATH)
    recomputed_pass = validate_fixture_file(PASS_FIXTURE_PATH)
    recomputed_mismatch = validate_fixture_file(MISMATCH_FIXTURE_PATH)
    mismatch_rows = _read_mismatch_rows(MISMATCH_REPORT_PATH)

    require(manifest.get("schema_version") == SCHEMA_VERSION, "manifest schema mismatch")
    require(manifest.get("project_id") == "KMFA", "project_id mismatch")
    require(manifest.get("version") == "0.1.3", "version mismatch")
    require(manifest.get("stage_id") == "S06", "stage_id must be S06")
    require(manifest.get("phase_id") == "S06-P1", "phase_id must be S06-P1")
    require(manifest.get("phase_scope") == PHASE_SCOPE, "phase scope mismatch")
    require(manifest.get("task_id") == TASK_ID, "task_id mismatch")
    require(
        manifest.get("status") == "completed_validated_local_only_upload_deferred_zero_delta_replay",
        "status mismatch",
    )
    require(manifest.get("completed_task_ids") == ["S6PAT01", "S6PAT02", "S6PAT03"], "task ids mismatch")
    require(
        manifest.get("acceptance_ids") == ["ACC-V013-S06-P1-ZERO-DELTA-REPLAY"],
        "acceptance ids mismatch",
    )
    require(manifest.get("next_required_step") == NEXT_REQUIRED_STEP, "next_required_step mismatch")

    require(manifest.get("s05_stage_review_dependency_validated") is True, "S05 dependency flag mismatch")
    require(s05.get("stage_id") == "S05", "S05 dependency stage mismatch")
    require(s05.get("open_review_finding_count") == 0, "S05 review must have zero open findings")
    require(s05.get("q5_locked_field_count") == 40, "S05 locked field dependency mismatch")
    require(s05.get("excluded_field_count") == 5, "S05 excluded field dependency mismatch")
    require(s05.get("github_upload_performed") is False, "S05 v0.1.3 upload must remain false")
    s05_summary = manifest.get("s05_dependency_summary", {})
    require(s05_summary.get("q5_locked_field_count") == 40, "manifest S05 locked count mismatch")
    require(s05_summary.get("excluded_field_count") == 5, "manifest S05 excluded count mismatch")
    require(s05_summary.get("github_upload_performed") is False, "manifest S05 upload summary mismatch")

    require(pass_fixture.get("public_safe_fixture_only") is True, "pass fixture must be public-safe")
    require(pass_fixture.get("raw_business_data_used") is False, "pass fixture raw flag mismatch")
    require(mismatch_fixture.get("public_safe_fixture_only") is True, "mismatch fixture must be public-safe")
    require(mismatch_fixture.get("raw_business_data_used") is False, "mismatch fixture raw flag mismatch")
    require(pass_result == recomputed_pass, "pass result must match recomputed zero-delta validator output")
    require(mismatch_result == recomputed_mismatch, "mismatch result must match recomputed zero-delta validator output")
    require(pass_result.get("zero_delta_passed") is True, "public-safe pass fixture must pass zero-delta")
    require(pass_result.get("mismatch_count") == 0, "pass fixture mismatch_count must be 0")
    require(mismatch_result.get("zero_delta_passed") is False, "one-cent mismatch fixture must fail")
    require(mismatch_result.get("minimum_fail_difference_cents") == 1, "minimum fail difference must be 1 cent")
    require(mismatch_result.get("mismatch_count") == 1, "mismatch fixture mismatch count must be 1")
    mismatch = mismatch_result.get("mismatches", [{}])[0]
    require(mismatch.get("difference_cents") == 1, "mismatch difference must be 1 cent")
    require(mismatch.get("authoritative_value_cents") == 10000, "authoritative synthetic cents mismatch")
    require(mismatch.get("system_value_cents") == 9999, "system synthetic cents mismatch")

    require(len(mismatch_rows) == 1, "mismatch report must contain one mismatch row")
    if mismatch_rows:
        row = mismatch_rows[0]
        for column in REQUIRED_REPORT_COLUMNS:
            require(column in row, f"missing mismatch report column: {column}")
        require(row.get("difference_cents") == "1", "mismatch report difference must be 1")
    for column in REQUIRED_REPORT_COLUMNS:
        require(column in manifest.get("mismatch_report_columns", []), f"manifest missing report column: {column}")
    require(manifest.get("mismatch_report_contains_required_columns") is True, "required column flag mismatch")

    require(manifest.get("pass_fixture_record_count") == 2, "pass fixture record count mismatch")
    require(manifest.get("pass_fixture_amount_field_count") == 4, "pass fixture field count mismatch")
    require(manifest.get("pass_fixture_field_comparison_count") == 8, "comparison count mismatch")
    require(manifest.get("zero_delta_passed_for_public_safe_fixture") is True, "pass fixture result flag mismatch")
    require(manifest.get("pass_fixture_mismatch_count") == 0, "pass fixture mismatch summary mismatch")
    require(manifest.get("one_cent_mismatch_detected") is True, "one-cent mismatch flag mismatch")
    require(manifest.get("minimum_fail_difference_cents") == 1, "minimum fail difference summary mismatch")
    require(manifest.get("mismatch_fixture_mismatch_count") == 1, "mismatch fixture count summary mismatch")
    require(manifest.get("mismatch_report_generated") is True, "mismatch report generated flag mismatch")
    require(manifest.get("integer_cent_comparison_only") is True, "integer-cent comparison flag mismatch")
    require(manifest.get("float_money_allowed") is False, "float money must be disallowed")
    require(manifest.get("raw_business_data_used") is False, "raw business data must not be used")
    require(manifest.get("raw_dir_read_performed") is False, "raw dir read must be false")
    require(manifest.get("raw_dir_mutation_performed") is False, "raw dir mutation must be false")
    require(manifest.get("metadata_quality_written") is False, "metadata quality write belongs to S06-P3")
    require(manifest.get("difference_queue_created") is False, "difference queue belongs to S06-P2")
    require(manifest.get("stage6_review_performed") is False, "Stage 6 review must not be performed")
    require(manifest.get("github_upload_performed") is False, "GitHub upload must not be performed")
    require(
        manifest.get("github_upload_deferred_until_stage10_batch") is True,
        "GitHub upload must be deferred until Stage 1-10 batch",
    )
    require(manifest.get("formal_report_allowed") is False, "formal report must remain blocked")
    require(manifest.get("business_decision_basis_allowed") is False, "business basis must remain false")
    require(manifest.get("business_execution_allowed") is False, "business execution must remain false")
    require(manifest.get("current_data_quality_grade") == "Q2", "data quality summary mismatch")
    require(manifest.get("current_report_grade") == "D", "report grade summary mismatch")
    require(manifest.get("release_permission") == "blocked", "release permission mismatch")

    raw_boundary = manifest.get("raw_data_boundary", {})
    require(raw_boundary.get("local_raw_data_dir") == RAW_DIR, "raw directory mismatch")
    require(raw_boundary.get("codex_read_allowed_only_when_phase_requires") is True, "raw read policy mismatch")
    require(raw_boundary.get("codex_read_required_by_this_phase") is False, "raw read required mismatch")
    require(raw_boundary.get("codex_read_performed_by_this_phase") is False, "raw read performed mismatch")
    require(raw_boundary.get("codex_modify_allowed") is False, "raw modify must be false")
    require(raw_boundary.get("codex_delete_allowed") is False, "raw delete must be false")
    require(raw_boundary.get("codex_move_allowed") is False, "raw move must be false")
    require(raw_boundary.get("codex_rename_allowed") is False, "raw rename must be false")
    require(raw_boundary.get("codex_overwrite_allowed") is False, "raw overwrite must be false")
    require(raw_boundary.get("codex_generate_inside_allowed") is False, "raw generate-inside must be false")
    require(raw_boundary.get("github_commit_allowed") is False, "raw GitHub commit must be false")

    safety = manifest.get("public_repo_safety", {})
    for key in PUBLIC_SAFETY_FALSE_KEYS:
        require(safety.get(key) is False, f"public_repo_safety.{key} must be false")

    for ref in manifest.get("evidence_refs", []):
        require(Path(ref).exists(), f"missing evidence ref: {ref}")
    for evidence in (REPORT_PATH, TEST_RESULTS_PATH):
        require(evidence.exists(), f"missing human evidence: {evidence}")
        if evidence.exists():
            text = evidence.read_text(encoding="utf-8")
            for forbidden in FORBIDDEN_EVIDENCE_TEXT:
                require(forbidden not in text, f"forbidden evidence text {forbidden!r} in {evidence}")

    tracked_files = git_output(["ls-files", "KMFA"]).splitlines()
    forbidden_tracked = [
        path
        for path in tracked_files
        if path.lower().endswith(FORBIDDEN_PUBLIC_SUFFIXES) or ".codex_private_runtime/" in path
    ]
    require(not forbidden_tracked, f"forbidden public/private tracked files: {forbidden_tracked}")
    require("codex/kmfa" in git_output(["status", "--short", "--branch"]), "git status must be on codex/kmfa")

    if errors:
        raise ValidationError("\n".join(errors))

    return {
        "task_id": manifest["task_id"],
        "stage_id": manifest["stage_id"],
        "phase_id": manifest["phase_id"],
        "phase_scope": manifest["phase_scope"],
        "s05_stage_review_dependency_validated": manifest["s05_stage_review_dependency_validated"],
        "pass_fixture_field_comparison_count": manifest["pass_fixture_field_comparison_count"],
        "zero_delta_passed_for_public_safe_fixture": manifest["zero_delta_passed_for_public_safe_fixture"],
        "pass_fixture_mismatch_count": manifest["pass_fixture_mismatch_count"],
        "one_cent_mismatch_detected": manifest["one_cent_mismatch_detected"],
        "minimum_fail_difference_cents": manifest["minimum_fail_difference_cents"],
        "mismatch_fixture_mismatch_count": manifest["mismatch_fixture_mismatch_count"],
        "mismatch_report_generated": manifest["mismatch_report_generated"],
        "metadata_quality_written": manifest["metadata_quality_written"],
        "difference_queue_created": manifest["difference_queue_created"],
        "stage6_review_performed": manifest["stage6_review_performed"],
        "github_upload_performed": manifest["github_upload_performed"],
        "raw_dir_read_performed": manifest["raw_dir_read_performed"],
        "raw_dir_mutation_performed": manifest["raw_dir_mutation_performed"],
        "formal_report_allowed": manifest["formal_report_allowed"],
        "business_execution_allowed": manifest["business_execution_allowed"],
        "next_required_step": manifest["next_required_step"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA v0.1.3 S06-P1 zero-delta replay evidence.")
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    args = parser.parse_args()
    try:
        result = validate_v013_s06_p1_zero_delta_replay(args.manifest)
    except ValidationError as exc:
        print("FAIL: KMFA v0.1.3 S06-P1 zero-delta replay validation failed")
        print(exc)
        return 1
    print(
        "PASS: KMFA v0.1.3 S06-P1 zero-delta replay validated "
        f"(comparisons={result['pass_fixture_field_comparison_count']}, "
        f"pass_mismatches={result['pass_fixture_mismatch_count']}, "
        f"one_cent_detected={str(result['one_cent_mismatch_detected']).lower()}, "
        f"metadata_quality_written={str(result['metadata_quality_written']).lower()}, "
        f"github_upload={str(result['github_upload_performed']).lower()})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
