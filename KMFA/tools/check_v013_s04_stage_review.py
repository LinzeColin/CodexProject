#!/usr/bin/env python3
"""Validate KMFA v0.1.3 Stage 4 review evidence."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from KMFA.tools.check_v013_s04_p1_amount_precision import validate_v013_s04_p1_amount_precision
from KMFA.tools.check_v013_s04_p2_field_standardization import validate_v013_s04_p2_field_standardization
from KMFA.tools.check_v013_s04_p3_basic_tool_report import validate_v013_s04_p3_basic_tool_report
from KMFA.tools.v013_s04_stage_review import (
    MANIFEST_PATH,
    NEXT_REQUIRED_STEP,
    REPORT_PATH,
    REVIEW_SCOPE,
    SCHEMA_VERSION,
    TASK_ID,
    TEST_RESULTS_PATH,
)


PHASE_MANIFESTS = {
    "S04-P1": Path("KMFA/stage_artifacts/V013_S04_P1_AMOUNT_PRECISION/machine/amount_precision_manifest.json"),
    "S04-P2": Path(
        "KMFA/stage_artifacts/V013_S04_P2_FIELD_STANDARDIZATION/machine/field_standardization_manifest.json"
    ),
    "S04-P3": Path("KMFA/stage_artifacts/V013_S04_P3_BASIC_TOOL_REPORT/machine/basic_tool_report_manifest.json"),
}
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
    "tool_report_raw_rows_committed",
    "field_standardization_raw_rows_committed",
    "amount_raw_rows_committed",
)
REQUIRED_HARD_BLOCKS = (
    "raw_data_mutation_forbidden",
    "float_money_forbidden",
    "cent_difference_must_not_be_ignored",
    "raw_value_matching_not_performed",
    "business_field_parsing_not_performed",
    "lineage_full_check_not_performed",
    "formal_report_release_blocked",
    "business_execution_blocked",
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


def validate_v013_s04_stage_review(manifest_path: Path = MANIFEST_PATH) -> dict[str, Any]:
    errors: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    manifest = read_json(manifest_path)
    p1_result = validate_v013_s04_p1_amount_precision()
    p2_result = validate_v013_s04_p2_field_standardization()
    p3_result = validate_v013_s04_p3_basic_tool_report()

    require(manifest.get("schema_version") == SCHEMA_VERSION, "manifest schema mismatch")
    require(manifest.get("project_id") == "KMFA", "project_id mismatch")
    require(manifest.get("version") == "0.1.3", "version mismatch")
    require(manifest.get("stage_id") == "S04", "stage_id must be S04")
    require(manifest.get("review_id") == TASK_ID, "review_id mismatch")
    require(manifest.get("task_id") == TASK_ID, "task_id mismatch")
    require(manifest.get("review_scope") == REVIEW_SCOPE, "review scope mismatch")
    require(manifest.get("status") == "passed_local_stage_review_upload_deferred", "status mismatch")
    require(manifest.get("stage_review_performed") is True, "stage review must be performed")
    require(manifest.get("github_upload_ready_next_gate") is False, "GitHub upload must be deferred until Stage 1-10 batch")
    require(
        manifest.get("github_upload_deferred_until_stage10_batch") is True,
        "GitHub upload must be explicitly deferred until Stage 1-10 batch",
    )
    require(manifest.get("github_upload_performed") is False, "GitHub upload must not be performed")
    require(
        manifest.get("github_upload_status") == "not_uploaded_deferred_until_stage10_batch",
        "GitHub upload status must be not uploaded and batch deferred",
    )
    require(manifest.get("delivery_allowed") is False, "delivery_allowed must remain false")
    require(manifest.get("formal_report_allowed") is False, "formal_report_allowed must remain false")
    require(manifest.get("business_decision_basis_allowed") is False, "business decision basis must remain false")
    require(manifest.get("business_execution_allowed") is False, "business execution must remain false")
    require(manifest.get("lineage_full_check_completed") is False, "lineage full check must not be completed")
    require(manifest.get("raw_value_matching_performed") is False, "raw value matching must not be performed")
    require(manifest.get("raw_dir_read_performed_by_stage_review") is False, "stage review raw read must be false")
    require(
        manifest.get("raw_dir_read_performed_by_dependency_validators") is False,
        "dependency validator raw read flag must be false for S04 review replay",
    )
    require(manifest.get("raw_dir_mutation_performed") is False, "raw directory mutation must not be performed")
    require(manifest.get("s04_p2_raw_listing_deviation_recorded") is True, "S04-P2 raw listing deviation must be recorded")
    require(manifest.get("s04_p2_raw_listing_temp_files_removed") is True, "S04-P2 temp files removed flag must be true")
    require(manifest.get("phase_count") == 3, "phase_count must be 3")
    require(manifest.get("open_review_finding_count") == 0, "open review findings must be 0")
    require(manifest.get("fixed_review_finding_count") == 0, "fixed review findings must be 0")
    require(manifest.get("review_findings") == [], "review findings must be empty")
    require(manifest.get("next_required_step") == NEXT_REQUIRED_STEP, "next_required_step mismatch")

    phase_results = manifest.get("phase_results", {})
    require(phase_results == {"S04-P1": "PASS", "S04-P2": "PASS", "S04-P3": "PASS"}, "phase_results mismatch")
    require(manifest.get("s04_p1_dependency_validated") is True, "S04-P1 dependency flag mismatch")
    require(manifest.get("s04_p2_dependency_validated") is True, "S04-P2 dependency flag mismatch")
    require(manifest.get("s04_p3_dependency_validated") is True, "S04-P3 dependency flag mismatch")
    require(p1_result.get("phase_id") == "S04-P1", "S04-P1 validator did not return S04-P1")
    require(p2_result.get("phase_id") == "S04-P2", "S04-P2 validator did not return S04-P2")
    require(p3_result.get("phase_id") == "S04-P3", "S04-P3 validator did not return S04-P3")
    require(p1_result.get("github_upload_performed") is False, "S04-P1 upload boundary mismatch")
    require(p2_result.get("github_upload_performed") is False, "S04-P2 upload boundary mismatch")
    require(p3_result.get("github_upload_performed") is False, "S04-P3 upload boundary mismatch")
    require(p1_result.get("raw_dir_read_performed") is False, "S04-P1 raw read boundary mismatch")
    require(p1_result.get("raw_dir_mutation_performed") is False, "S04-P1 raw mutation boundary mismatch")
    require(p2_result.get("raw_dir_mutation_performed") is False, "S04-P2 raw mutation boundary mismatch")
    require(p2_result.get("raw_dir_accidental_listing_performed") is True, "S04-P2 listing deviation mismatch")
    require(p2_result.get("raw_dir_accidental_listing_temp_files_removed") is True, "S04-P2 temp cleanup mismatch")
    require(p3_result.get("raw_dir_read_performed") is False, "S04-P3 raw read boundary mismatch")
    require(p3_result.get("raw_dir_mutation_performed") is False, "S04-P3 raw mutation boundary mismatch")

    phase_summary = manifest.get("phase_summary", {})
    require(phase_summary.get("S04-P1", {}).get("amount_case_count") == 9, "S04-P1 amount case summary mismatch")
    require(phase_summary.get("S04-P1", {}).get("amount_rejection_count") == 9, "S04-P1 rejection summary mismatch")
    require(
        phase_summary.get("S04-P1", {}).get("repository_no_float_scan_passed") is True,
        "S04-P1 no-float summary mismatch",
    )
    require(phase_summary.get("S04-P2", {}).get("canonical_field_count") == 6, "S04-P2 field summary mismatch")
    require(phase_summary.get("S04-P2", {}).get("alias_dictionary_row_count", 0) >= 30, "S04-P2 alias summary mismatch")
    require(phase_summary.get("S04-P2", {}).get("standardization_case_passed_count") == 6, "S04-P2 case summary mismatch")
    require(phase_summary.get("S04-P2", {}).get("quality_status_count") == 5, "S04-P2 quality summary mismatch")
    require(
        phase_summary.get("S04-P2", {}).get("raw_dir_accidental_listing_performed") is True,
        "S04-P2 listing summary mismatch",
    )
    require(phase_summary.get("S04-P3", {}).get("synthetic_boundary_case_total") == 22, "S04-P3 case total mismatch")
    require(phase_summary.get("S04-P3", {}).get("synthetic_boundary_case_failed") == 0, "S04-P3 failed case mismatch")
    require(phase_summary.get("S04-P3", {}).get("amount_boundary_case_count") == 11, "S04-P3 amount summary mismatch")
    require(
        phase_summary.get("S04-P3", {}).get("date_period_boundary_case_count") == 11,
        "S04-P3 date/period summary mismatch",
    )
    require(phase_summary.get("S04-P3", {}).get("json_report_generated") is True, "S04-P3 JSON summary mismatch")
    require(phase_summary.get("S04-P3", {}).get("markdown_report_generated") is True, "S04-P3 Markdown summary mismatch")

    gate = manifest.get("stage_gate", {})
    require(gate.get("current_data_quality_grade") == "Q2", "stage gate quality mismatch")
    require(gate.get("current_report_grade") == "D", "stage gate report grade mismatch")
    require(gate.get("release_permission") == "blocked", "stage gate release permission mismatch")
    require(manifest.get("current_data_quality_grade") == p3_result.get("current_data_quality_grade") == "Q2", "quality grade mismatch")
    require(manifest.get("current_report_grade") == p3_result.get("current_report_grade") == "D", "report grade mismatch")
    require(manifest.get("release_permission") == p3_result.get("release_permission") == "blocked", "release permission mismatch")

    hard_blocks = manifest.get("hard_blocks", [])
    require(isinstance(hard_blocks, list), "hard_blocks must be a list")
    for block in REQUIRED_HARD_BLOCKS:
        require(block in hard_blocks, f"missing hard block: {block}")
    require(manifest.get("hard_block_count") == len(REQUIRED_HARD_BLOCKS), "hard block count mismatch")

    raw_boundary = manifest.get("raw_data_boundary", {})
    require(raw_boundary.get("local_raw_data_dir") == RAW_DIR, "raw directory mismatch")
    require(
        raw_boundary.get("local_raw_data_dir_role") == "user_finance_raw_business_data_inbox",
        "raw directory role mismatch",
    )
    require(raw_boundary.get("codex_read_allowed_only_when_phase_requires") is True, "raw read policy mismatch")
    require(raw_boundary.get("codex_modify_allowed") is False, "raw directory modify must be false")
    require(raw_boundary.get("codex_delete_allowed") is False, "raw directory delete must be false")
    require(raw_boundary.get("codex_move_allowed") is False, "raw directory move must be false")
    require(raw_boundary.get("codex_rename_allowed") is False, "raw directory rename must be false")
    require(raw_boundary.get("codex_overwrite_allowed") is False, "raw directory overwrite must be false")
    require(raw_boundary.get("codex_generate_inside_allowed") is False, "raw directory generate-inside must be false")
    require(
        raw_boundary.get("codex_create_extra_files_inside_allowed") is False,
        "raw directory extra-file creation must be false",
    )
    require(raw_boundary.get("github_commit_allowed") is False, "raw directory commit must be false")
    require(
        raw_boundary.get("private_runtime_output_dir") == "KMFA/.codex_private_runtime/",
        "private runtime output dir mismatch",
    )
    require(
        raw_boundary.get("extra_work_dir_requirement") == "must_be_project_controlled_and_gitignored",
        "extra work dir requirement mismatch",
    )

    safety = manifest.get("public_repo_safety", {})
    for key in PUBLIC_SAFETY_FALSE_KEYS:
        require(safety.get(key) is False, f"public_repo_safety.{key} must be false")

    reviewed_phase_manifests = manifest.get("reviewed_phase_manifests", {})
    for phase, path in PHASE_MANIFESTS.items():
        require(reviewed_phase_manifests.get(phase) == str(path), f"{phase} manifest ref mismatch")
        require(path.exists(), f"missing phase manifest: {path}")
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
        "review_scope": manifest["review_scope"],
        "phase_count": manifest["phase_count"],
        "phase_results": phase_results,
        "s04_p1_dependency_validated": manifest["s04_p1_dependency_validated"],
        "s04_p2_dependency_validated": manifest["s04_p2_dependency_validated"],
        "s04_p3_dependency_validated": manifest["s04_p3_dependency_validated"],
        "stage_review_performed": manifest["stage_review_performed"],
        "github_upload_ready_next_gate": manifest["github_upload_ready_next_gate"],
        "github_upload_deferred_until_stage10_batch": manifest["github_upload_deferred_until_stage10_batch"],
        "github_upload_performed": manifest["github_upload_performed"],
        "delivery_allowed": manifest["delivery_allowed"],
        "formal_report_allowed": manifest["formal_report_allowed"],
        "business_decision_basis_allowed": manifest["business_decision_basis_allowed"],
        "business_execution_allowed": manifest["business_execution_allowed"],
        "raw_value_matching_performed": manifest["raw_value_matching_performed"],
        "raw_dir_read_performed_by_stage_review": manifest["raw_dir_read_performed_by_stage_review"],
        "raw_dir_read_performed_by_dependency_validators": manifest[
            "raw_dir_read_performed_by_dependency_validators"
        ],
        "raw_dir_mutation_performed": manifest["raw_dir_mutation_performed"],
        "s04_p2_raw_listing_deviation_recorded": manifest["s04_p2_raw_listing_deviation_recorded"],
        "s04_p2_raw_listing_temp_files_removed": manifest["s04_p2_raw_listing_temp_files_removed"],
        "current_data_quality_grade": manifest["current_data_quality_grade"],
        "current_report_grade": manifest["current_report_grade"],
        "release_permission": manifest["release_permission"],
        "open_review_finding_count": manifest["open_review_finding_count"],
        "fixed_review_finding_count": manifest["fixed_review_finding_count"],
        "hard_blocks": hard_blocks,
        "next_required_step": manifest["next_required_step"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA v0.1.3 Stage 4 review evidence.")
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    args = parser.parse_args()
    try:
        result = validate_v013_s04_stage_review(args.manifest)
    except ValidationError as exc:
        print("FAIL: KMFA v0.1.3 Stage 4 review validation failed")
        print(exc)
        return 1
    print(
        "PASS: KMFA v0.1.3 Stage 4 review validated "
        f"(phases={result['phase_count']}, findings_open={result['open_review_finding_count']}, "
        f"quality={result['current_data_quality_grade']}, report={result['current_report_grade']}, "
        f"release={result['release_permission']}, upload_ready={str(result['github_upload_ready_next_gate']).lower()}, "
        f"github_upload={str(result['github_upload_performed']).lower()})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
