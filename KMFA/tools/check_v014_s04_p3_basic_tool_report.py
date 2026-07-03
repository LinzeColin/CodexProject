#!/usr/bin/env python3
"""Validate KMFA v0.1.4 S04-P3 basic tool report evidence."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from KMFA.tools.check_v014_s03_stage_review import RAW_INBOX
from KMFA.tools.check_v014_s04_p1_amount_precision import validate_v014_s04_p1_amount_precision
from KMFA.tools.check_v014_s04_p2_field_standardization import validate_v014_s04_p2_field_standardization
from KMFA.tools.v014_s04_p3_basic_tool_report import (
    JSON_REPORT_PATH,
    MANIFEST_PATH,
    MARKDOWN_REPORT_PATH,
    REPORT_PATH,
    RISK_REGISTER_PATH,
    ROLLBACK_PATH,
    SCHEMA_VERSION,
    TASK_ID,
    TEST_RESULTS_PATH,
    replay_basic_tool_report,
)


BOOLEAN_FALSE_KEYS = (
    "raw_dir_read_required",
    "raw_dir_read_performed",
    "raw_dir_list_performed",
    "raw_dir_hash_performed",
    "raw_dir_mutation_performed",
    "raw_layer_write_allowed",
    "raw_source_mutation_allowed",
    "raw_file_bytes_committed",
    "raw_filename_publication_allowed",
    "raw_file_hash_publication_allowed",
    "field_plaintext_publication_allowed",
    "sheet_name_publication_allowed",
    "zip_member_name_publication_allowed",
    "row_value_publication_allowed",
    "business_value_publication_allowed",
    "business_field_parsing_performed",
    "raw_value_matching_performed",
    "raw_field_mapping_performed",
    "stage4_review_performed",
    "stage4_upload_gate_performed",
    "s05_started",
    "github_upload_performed",
    "github_main_upload_allowed",
    "delivery_allowed",
    "formal_report_allowed",
    "business_decision_basis_allowed",
    "business_execution_allowed",
)
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
    "sheet_names_committed",
    "zip_member_names_committed",
    "raw_business_values_committed",
)
REQUIRED_CATEGORIES = {
    "amount_decimal",
    "amount_negative",
    "amount_wan_yuan",
    "amount_abnormal_characters",
    "date_chinese",
    "period_chinese_year_month",
    "date_nullish",
}
FORBIDDEN_EVIDENCE_TEXT = (
    "raw_value:",
    "normalized_value:",
    "source_header_text:",
    "original_filename:",
    "member_path:",
    "member_name:",
    "sheet_name:",
    "cell_value:",
    "row_value:",
    "business_value:",
    "bank_statement",
    "contract_full_text",
    "salary_detail",
    "tax_filing",
    "connector_" + "to" + "ken:",
    "connector_" + "pass" + "word:",
    "api_" + "key:",
    "private_" + "key:",
    "-----" "BEGIN",
)
FORBIDDEN_PUBLIC_SUFFIXES = (".zip", ".xlsx", ".xls", ".xlsm", ".pdf", ".sqlite", ".sqlite3", ".db")


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


def check_public_safe_file(path: Path, errors: list[str]) -> None:
    require(path.exists(), f"missing evidence file: {path}", errors)
    if not path.exists():
        return
    require(path.suffix.lower() not in FORBIDDEN_PUBLIC_SUFFIXES, f"forbidden evidence extension: {path}", errors)
    if path.suffix.lower() in {".md", ".json", ".jsonl", ".csv", ".yaml", ".yml"}:
        text = path.read_text(encoding="utf-8", errors="ignore").lower()
        for forbidden in FORBIDDEN_EVIDENCE_TEXT:
            require(forbidden.lower() not in text, f"forbidden evidence text {forbidden!r} in {path}", errors)


def validate_v014_s04_p3_basic_tool_report(manifest_path: Path = MANIFEST_PATH) -> dict[str, Any]:
    errors: list[str] = []
    manifest = read_json(manifest_path)
    s04_p1 = validate_v014_s04_p1_amount_precision()
    s04_p2 = validate_v014_s04_p2_field_standardization()
    replay = replay_basic_tool_report()
    tool_report = read_json(JSON_REPORT_PATH)

    require(manifest.get("schema_version") == SCHEMA_VERSION, "manifest schema mismatch", errors)
    require(manifest.get("project_id") == "KMFA", "project_id mismatch", errors)
    require(manifest.get("version") == "0.1.4", "version mismatch", errors)
    require(manifest.get("stage_id") == "S04", "stage_id must be S04", errors)
    require(manifest.get("phase_id") == "S04-P3", "phase_id must be S04-P3", errors)
    require(
        manifest.get("phase_scope") == "v014_s04_p3_basic_tool_report_only",
        "phase scope mismatch",
        errors,
    )
    require(manifest.get("task_id") == TASK_ID, "task_id mismatch", errors)
    require(manifest.get("acceptance_id") == "ACC-V014-S04-P3-BASIC-TOOL-REPORT", "acceptance id mismatch", errors)
    require(manifest.get("status") == "completed_validated_local_only_no_go_upload_deferred", "status mismatch", errors)
    require(manifest.get("completed_task_ids") == ["S4PCT01", "S4PCT02", "S4PCT03"], "completed task ids mismatch", errors)

    require(s04_p1.get("phase_id") == "S04-P1", "S04-P1 dependency did not return phase S04-P1", errors)
    require(s04_p1.get("github_upload_performed") is False, "S04-P1 upload boundary mismatch", errors)
    require("S04-P2" in s04_p1.get("next_required_step", ""), "S04-P1 must point next step to S04-P2", errors)
    require(manifest.get("s04_p1_dependency_validated") is True, "S04-P1 dependency must be true", errors)
    require(s04_p2.get("phase_id") == "S04-P2", "S04-P2 dependency did not return phase S04-P2", errors)
    require(s04_p2.get("github_upload_performed") is False, "S04-P2 upload boundary mismatch", errors)
    require("S04-P3" in s04_p2.get("next_required_step", ""), "S04-P2 must point next step to S04-P3", errors)
    require(manifest.get("s04_p2_dependency_validated") is True, "S04-P2 dependency must be true", errors)

    require(manifest.get("basic_tool_boundary_dependency_validated") is True, "basic tool dependency must be true", errors)
    require(replay["basic_tool_boundary_dependency_validated"] is True, "basic tool replay did not validate", errors)
    require(manifest.get("synthetic_boundary_case_total") == replay["synthetic_boundary_case_total"] == 22, "case total mismatch", errors)
    require(manifest.get("synthetic_boundary_case_passed") == replay["synthetic_boundary_case_passed"] == 22, "case passed mismatch", errors)
    require(manifest.get("synthetic_boundary_case_failed") == replay["synthetic_boundary_case_failed"] == 0, "case failed mismatch", errors)
    require(manifest.get("amount_boundary_case_count") == replay["amount_boundary_case_count"] == 11, "amount case count mismatch", errors)
    require(
        manifest.get("date_period_boundary_case_count") == replay["date_period_boundary_case_count"] == 11,
        "date/period case count mismatch",
        errors,
    )
    require(REQUIRED_CATEGORIES.issubset(set(manifest.get("categories", []))), "required boundary categories missing", errors)
    require(tool_report.get("schema_version") == "kmfa.tool_function_test_report.v1", "tool report schema mismatch", errors)
    require(tool_report.get("stage") == "S04", "tool report stage mismatch", errors)
    require(tool_report.get("phase") == "S04-P3", "tool report phase mismatch", errors)
    require(tool_report.get("status") == "PASS", "tool report status mismatch", errors)
    require(tool_report.get("raw_business_data_used") is False, "tool report raw data flag mismatch", errors)
    require(tool_report.get("case_summary", {}).get("total") == 22, "tool report case total mismatch", errors)
    require(tool_report.get("case_summary", {}).get("failed") == 0, "tool report failed count mismatch", errors)

    require(manifest.get("json_report_generated") is True, "JSON report generated flag must be true", errors)
    require(manifest.get("markdown_report_generated") is True, "Markdown report generated flag must be true", errors)
    require(JSON_REPORT_PATH.exists(), "missing JSON tool report", errors)
    require(MARKDOWN_REPORT_PATH.exists(), "missing markdown tool report", errors)
    if MARKDOWN_REPORT_PATH.exists():
        markdown = MARKDOWN_REPORT_PATH.read_text(encoding="utf-8")
        require("S04-P3 Tool Function Test Report" in markdown, "markdown report title missing", errors)
        require("amount ten-thousand-yuan unit" in markdown, "markdown coverage missing", errors)

    raw_boundary = manifest.get("raw_data_boundary", {})
    require(raw_boundary.get("local_raw_data_dir") == RAW_INBOX, "raw directory mismatch", errors)
    require(
        raw_boundary.get("local_raw_data_dir_role") == "user_finance_raw_business_data_inbox",
        "raw directory role mismatch",
        errors,
    )
    require(raw_boundary.get("codex_read_allowed_only_when_phase_requires") is True, "raw read policy mismatch", errors)
    require(raw_boundary.get("codex_read_required_by_this_phase") is False, "raw read required flag must be false", errors)
    require(raw_boundary.get("codex_read_performed_by_this_phase") is False, "raw read performed flag must be false", errors)
    require(raw_boundary.get("codex_list_performed_by_this_phase") is False, "raw list performed flag must be false", errors)
    require(raw_boundary.get("codex_hash_performed_by_this_phase") is False, "raw hash performed flag must be false", errors)
    require(raw_boundary.get("codex_modify_allowed") is False, "raw modify allowed must be false", errors)
    require(raw_boundary.get("codex_delete_allowed") is False, "raw delete allowed must be false", errors)
    require(raw_boundary.get("codex_move_allowed") is False, "raw move allowed must be false", errors)
    require(raw_boundary.get("codex_rename_allowed") is False, "raw rename allowed must be false", errors)
    require(raw_boundary.get("codex_overwrite_allowed") is False, "raw overwrite allowed must be false", errors)
    require(raw_boundary.get("codex_generate_inside_allowed") is False, "raw generate-inside allowed must be false", errors)
    require(
        raw_boundary.get("codex_create_extra_files_inside_allowed") is False,
        "raw create-extra-files-inside allowed must be false",
        errors,
    )
    require(raw_boundary.get("github_commit_allowed") is False, "raw GitHub commit allowed must be false", errors)
    require(
        raw_boundary.get("private_runtime_output_dir") == "KMFA/.codex_private_runtime/",
        "private runtime output dir mismatch",
        errors,
    )

    for key in BOOLEAN_FALSE_KEYS:
        require(manifest.get(key) is False, f"{key} must be false", errors)
    safety = manifest.get("public_repo_safety", {})
    for key in PUBLIC_SAFETY_FALSE_KEYS:
        require(safety.get(key) is False, f"public_repo_safety.{key} must be false", errors)

    require(manifest.get("current_data_quality_grade") == "Q2", "quality grade mismatch", errors)
    require(manifest.get("current_report_grade") == "D", "report grade mismatch", errors)
    require(manifest.get("release_permission") == "blocked", "release permission mismatch", errors)
    require(manifest.get("current_go_no_go") == "NO_GO", "go/no-go mismatch", errors)
    require(
        manifest.get("github_upload_status") == "deferred_until_v014_stage1_18_complete_overall_review",
        "upload status mismatch",
        errors,
    )
    require("Stage 4 overall review" in manifest.get("next_required_step", ""), "next step must point to Stage 4 review", errors)
    require("separate run" in manifest.get("next_required_step", ""), "next step must preserve one-run boundary", errors)
    require("Stage 1-18 complete overall review" in manifest.get("next_required_step", ""), "next step must preserve upload boundary", errors)

    for ref in manifest.get("legacy_s04_p3_refs", []):
        require(Path(ref).exists(), f"missing legacy S04-P3 ref: {ref}", errors)
    for ref in manifest.get("evidence_refs", []):
        check_public_safe_file(Path(ref), errors)
    for evidence in (REPORT_PATH, TEST_RESULTS_PATH, RISK_REGISTER_PATH, ROLLBACK_PATH, MANIFEST_PATH):
        check_public_safe_file(evidence, errors)

    tracked_files = git_output(["ls-files", "KMFA"]).splitlines()
    forbidden_tracked = [
        path
        for path in tracked_files
        if path.lower().endswith(FORBIDDEN_PUBLIC_SUFFIXES) or ".codex_private_runtime/" in path
    ]
    require(not forbidden_tracked, f"forbidden public/private tracked files: {forbidden_tracked}", errors)
    require("codex/kmfa" in git_output(["status", "--short", "--branch"]), "git status must be on codex/kmfa", errors)

    if errors:
        raise ValidationError("\n".join(errors))

    return {
        "task_id": manifest["task_id"],
        "stage_id": manifest["stage_id"],
        "phase_id": manifest["phase_id"],
        "phase_scope": manifest["phase_scope"],
        "status": manifest["status"],
        "s04_p1_dependency_validated": manifest["s04_p1_dependency_validated"],
        "s04_p2_dependency_validated": manifest["s04_p2_dependency_validated"],
        "basic_tool_boundary_dependency_validated": manifest["basic_tool_boundary_dependency_validated"],
        "synthetic_boundary_case_total": manifest["synthetic_boundary_case_total"],
        "synthetic_boundary_case_passed": manifest["synthetic_boundary_case_passed"],
        "synthetic_boundary_case_failed": manifest["synthetic_boundary_case_failed"],
        "amount_boundary_case_count": manifest["amount_boundary_case_count"],
        "date_period_boundary_case_count": manifest["date_period_boundary_case_count"],
        "json_report_generated": manifest["json_report_generated"],
        "markdown_report_generated": manifest["markdown_report_generated"],
        "raw_dir_read_required": manifest["raw_dir_read_required"],
        "raw_dir_read_performed": manifest["raw_dir_read_performed"],
        "raw_dir_list_performed": manifest["raw_dir_list_performed"],
        "raw_dir_hash_performed": manifest["raw_dir_hash_performed"],
        "raw_dir_mutation_performed": manifest["raw_dir_mutation_performed"],
        "raw_field_mapping_performed": manifest["raw_field_mapping_performed"],
        "raw_filename_publication_allowed": manifest["raw_filename_publication_allowed"],
        "field_plaintext_publication_allowed": manifest["field_plaintext_publication_allowed"],
        "sheet_name_publication_allowed": manifest["sheet_name_publication_allowed"],
        "zip_member_name_publication_allowed": manifest["zip_member_name_publication_allowed"],
        "row_value_publication_allowed": manifest["row_value_publication_allowed"],
        "business_value_publication_allowed": manifest["business_value_publication_allowed"],
        "stage4_review_performed": manifest["stage4_review_performed"],
        "stage4_upload_gate_performed": manifest["stage4_upload_gate_performed"],
        "s05_started": manifest["s05_started"],
        "github_upload_performed": manifest["github_upload_performed"],
        "github_main_upload_allowed": manifest["github_main_upload_allowed"],
        "delivery_allowed": manifest["delivery_allowed"],
        "current_data_quality_grade": manifest["current_data_quality_grade"],
        "current_report_grade": manifest["current_report_grade"],
        "release_permission": manifest["release_permission"],
        "current_go_no_go": manifest["current_go_no_go"],
        "github_upload_status": manifest["github_upload_status"],
        "next_required_step": manifest["next_required_step"],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA v0.1.4 S04-P3 basic tool report evidence.")
    parser.add_argument("--manifest", default=str(MANIFEST_PATH))
    args = parser.parse_args(argv)
    try:
        result = validate_v014_s04_p3_basic_tool_report(Path(args.manifest))
    except ValidationError as exc:
        print("FAIL: KMFA v0.1.4 S04-P3 basic tool report validation failed")
        print(exc)
        return 1
    print(
        "PASS: KMFA v0.1.4 S04-P3 basic tool report validator passed "
        f"(cases={result['synthetic_boundary_case_passed']}/{result['synthetic_boundary_case_total']}, "
        f"amount_cases={result['amount_boundary_case_count']}, "
        f"date_period_cases={result['date_period_boundary_case_count']}, "
        f"raw_read={str(result['raw_dir_read_performed']).lower()}, "
        f"github_upload={str(result['github_upload_performed']).lower()})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
