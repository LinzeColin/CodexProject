#!/usr/bin/env python3
"""Validate KMFA v0.1.3 S04-P3 basic tool report replay evidence."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

from KMFA.tools.check_v013_s04_p1_amount_precision import validate_v013_s04_p1_amount_precision
from KMFA.tools.check_v013_s04_p2_field_standardization import validate_v013_s04_p2_field_standardization
from KMFA.tools.v013_s03_p1_file_import_register import RAW_DIR
from KMFA.tools.v013_s04_p3_basic_tool_report import (
    JSON_REPORT_PATH,
    MANIFEST_PATH,
    MARKDOWN_REPORT_PATH,
    REPORT_PATH,
    SCHEMA_VERSION,
    TASK_ID,
    TEST_RESULTS_PATH,
    replay_basic_tool_report,
)


BOOLEAN_FALSE_KEYS = (
    "raw_dir_read_required",
    "raw_dir_read_performed",
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
    "stage4_review_performed",
    "github_upload_performed",
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
FORBIDDEN_EVIDENCE_TEXT = (
    "raw_value:",
    "normalized_value:",
    "source_header_text:",
    "bank_statement",
    "contract_full_text",
    "salary_detail",
    "tax_filing",
    "-----" "BEGIN",
    "sk-",
)
FORBIDDEN_PUBLIC_SUFFIXES = (".zip", ".xlsx", ".xls", ".pdf", ".sqlite", ".db")


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


def validate_v013_s04_p3_basic_tool_report(manifest_path: Path = MANIFEST_PATH) -> dict[str, Any]:
    errors: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    manifest = read_json(manifest_path)
    s04_p1 = validate_v013_s04_p1_amount_precision()
    s04_p2 = validate_v013_s04_p2_field_standardization()
    replay = replay_basic_tool_report()
    tool_report = read_json(JSON_REPORT_PATH)

    require(manifest.get("schema_version") == SCHEMA_VERSION, "manifest schema mismatch")
    require(manifest.get("project_id") == "KMFA", "project_id mismatch")
    require(manifest.get("version") == "0.1.3", "version mismatch")
    require(manifest.get("stage_id") == "S04", "stage_id must be S04")
    require(manifest.get("phase_id") == "S04-P3", "phase_id must be S04-P3")
    require(
        manifest.get("phase_scope") == "v013_s04_p3_basic_tool_report_replay_only",
        "phase scope mismatch",
    )
    require(manifest.get("task_id") == TASK_ID, "task_id mismatch")
    require(manifest.get("status") == "completed_validated_local_only_no_go_upload_deferred", "status mismatch")
    require(manifest.get("completed_task_ids") == ["S4PCT01", "S4PCT02", "S4PCT03"], "completed task ids mismatch")

    require(s04_p1.get("phase_id") == "S04-P1", "S04-P1 dependency did not return phase S04-P1")
    require(s04_p1.get("github_upload_performed") is False, "S04-P1 upload boundary mismatch")
    require(manifest.get("s04_p1_dependency_validated") is True, "S04-P1 dependency must be true")
    require(s04_p2.get("phase_id") == "S04-P2", "S04-P2 dependency did not return phase S04-P2")
    require(s04_p2.get("github_upload_performed") is False, "S04-P2 upload boundary mismatch")
    require(manifest.get("s04_p2_dependency_validated") is True, "S04-P2 dependency must be true")

    require(manifest.get("basic_tool_boundary_dependency_validated") is True, "basic tool dependency must be true")
    require(replay["basic_tool_boundary_dependency_validated"] is True, "basic tool replay did not validate")
    require(manifest.get("synthetic_boundary_case_total") == replay["synthetic_boundary_case_total"] == 22, "case total mismatch")
    require(manifest.get("synthetic_boundary_case_passed") == replay["synthetic_boundary_case_passed"] == 22, "case passed mismatch")
    require(manifest.get("synthetic_boundary_case_failed") == replay["synthetic_boundary_case_failed"] == 0, "case failed mismatch")
    require(manifest.get("amount_boundary_case_count") == replay["amount_boundary_case_count"] == 11, "amount case count mismatch")
    require(
        manifest.get("date_period_boundary_case_count") == replay["date_period_boundary_case_count"] == 11,
        "date/period case count mismatch",
    )
    require(tool_report.get("stage") == "S04", "tool report stage mismatch")
    require(tool_report.get("phase") == "S04-P3", "tool report phase mismatch")
    require(tool_report.get("status") == "PASS", "tool report status mismatch")
    require(tool_report.get("raw_business_data_used") is False, "tool report raw data flag mismatch")
    require(tool_report.get("case_summary", {}).get("total") == 22, "tool report case total mismatch")
    require(tool_report.get("case_summary", {}).get("failed") == 0, "tool report failed count mismatch")

    require(manifest.get("json_report_generated") is True, "JSON report generated flag must be true")
    require(manifest.get("markdown_report_generated") is True, "Markdown report generated flag must be true")
    require(JSON_REPORT_PATH.exists(), "missing JSON tool report")
    require(MARKDOWN_REPORT_PATH.exists(), "missing markdown tool report")
    if MARKDOWN_REPORT_PATH.exists():
        markdown = MARKDOWN_REPORT_PATH.read_text(encoding="utf-8")
        require("S04-P3 Tool Function Test Report" in markdown, "markdown report title missing")
        require("amount ten-thousand-yuan unit" in markdown, "markdown coverage missing")

    raw_boundary = manifest.get("raw_data_boundary", {})
    require(raw_boundary.get("local_raw_data_dir") == RAW_DIR, "raw directory mismatch")
    require(
        raw_boundary.get("local_raw_data_dir_role") == "user_finance_raw_business_data_inbox",
        "raw directory role mismatch",
    )
    require(raw_boundary.get("codex_read_required_by_this_phase") is False, "raw read required flag must be false")
    require(raw_boundary.get("codex_read_performed_by_this_phase") is False, "raw read performed flag must be false")
    require(raw_boundary.get("codex_modify_allowed") is False, "raw modify allowed must be false")
    require(raw_boundary.get("codex_delete_allowed") is False, "raw delete allowed must be false")
    require(raw_boundary.get("codex_move_allowed") is False, "raw move allowed must be false")
    require(raw_boundary.get("codex_rename_allowed") is False, "raw rename allowed must be false")
    require(raw_boundary.get("codex_overwrite_allowed") is False, "raw overwrite allowed must be false")
    require(raw_boundary.get("codex_generate_inside_allowed") is False, "raw generate-inside allowed must be false")
    require(
        raw_boundary.get("codex_create_extra_files_inside_allowed") is False,
        "raw create-extra-files-inside allowed must be false",
    )
    require(raw_boundary.get("github_commit_allowed") is False, "raw GitHub commit allowed must be false")
    require(
        raw_boundary.get("private_runtime_output_dir") == "KMFA/.codex_private_runtime/",
        "private runtime output dir mismatch",
    )
    require(
        raw_boundary.get("extra_work_dir_requirement") == "must_be_project_controlled_and_gitignored",
        "extra work dir requirement mismatch",
    )

    for key in BOOLEAN_FALSE_KEYS:
        require(manifest.get(key) is False, f"{key} must be false")
    safety = manifest.get("public_repo_safety", {})
    for key in PUBLIC_SAFETY_FALSE_KEYS:
        require(safety.get(key) is False, f"public_repo_safety.{key} must be false")

    require(manifest.get("current_data_quality_grade") == "Q2", "quality grade mismatch")
    require(manifest.get("current_report_grade") == "D", "report grade mismatch")
    require(manifest.get("release_permission") == "blocked", "release permission mismatch")
    require("Stage 4 review" in manifest.get("next_required_step", ""), "next step must point to Stage 4 review")
    require("separate run" in manifest.get("next_required_step", ""), "next step must preserve one-run boundary")
    require("GitHub upload" in manifest.get("next_required_step", ""), "next step must preserve upload boundary")

    for ref in manifest.get("legacy_s04_p3_refs", []):
        require(Path(ref).exists(), f"missing legacy S04-P3 ref: {ref}")
    for ref in manifest.get("evidence_refs", []):
        require(Path(ref).exists(), f"missing evidence ref: {ref}")
    for evidence in (REPORT_PATH, TEST_RESULTS_PATH, MARKDOWN_REPORT_PATH):
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
        "raw_dir_mutation_performed": manifest["raw_dir_mutation_performed"],
        "raw_filename_publication_allowed": manifest["raw_filename_publication_allowed"],
        "field_plaintext_publication_allowed": manifest["field_plaintext_publication_allowed"],
        "sheet_name_publication_allowed": manifest["sheet_name_publication_allowed"],
        "zip_member_name_publication_allowed": manifest["zip_member_name_publication_allowed"],
        "row_value_publication_allowed": manifest["row_value_publication_allowed"],
        "business_value_publication_allowed": manifest["business_value_publication_allowed"],
        "stage4_review_performed": manifest["stage4_review_performed"],
        "github_upload_performed": manifest["github_upload_performed"],
        "delivery_allowed": manifest["delivery_allowed"],
        "current_data_quality_grade": manifest["current_data_quality_grade"],
        "current_report_grade": manifest["current_report_grade"],
        "release_permission": manifest["release_permission"],
        "next_required_step": manifest["next_required_step"],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA v0.1.3 S04-P3 basic tool report evidence.")
    parser.add_argument("--manifest", default=str(MANIFEST_PATH))
    args = parser.parse_args(argv)
    result = validate_v013_s04_p3_basic_tool_report(Path(args.manifest))
    print(
        "PASS: KMFA v0.1.3 S04-P3 basic tool report validator passed "
        f"(cases={result['synthetic_boundary_case_passed']}/{result['synthetic_boundary_case_total']}, "
        f"raw_read={str(result['raw_dir_read_performed']).lower()}, "
        f"github_upload={str(result['github_upload_performed']).lower()})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
