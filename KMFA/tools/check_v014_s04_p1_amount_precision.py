#!/usr/bin/env python3
"""Validate KMFA v0.1.4 S04-P1 amount precision evidence."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from KMFA.tools.check_v014_s03_stage_review import RAW_INBOX, validate_v014_s03_stage_review
from KMFA.tools.v014_s04_p1_amount_precision import (
    MANIFEST_PATH,
    REPORT_PATH,
    RISK_REGISTER_PATH,
    ROLLBACK_PATH,
    SCHEMA_VERSION,
    TASK_ID,
    TEST_RESULTS_PATH,
    replay_amount_precision_capability,
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
    "business_amount_values_committed",
)
BOOLEAN_FALSE_KEYS = (
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
    "business_amount_value_publication_allowed",
    "business_field_parsing_performed",
    "raw_value_matching_performed",
    "field_mapping_performed",
    "s04_p2_started",
    "s04_p3_started",
    "stage4_review_performed",
    "github_upload_performed",
    "github_main_upload_allowed",
    "delivery_allowed",
    "formal_report_allowed",
    "business_decision_basis_allowed",
    "business_execution_allowed",
)
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
    "business_amount_value:",
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


def check_public_safe_file(path: Path, errors: list[str]) -> None:
    require(path.exists(), f"missing evidence file: {path}", errors)
    if not path.exists():
        return
    require(path.suffix.lower() not in FORBIDDEN_PUBLIC_SUFFIXES, f"forbidden evidence extension: {path}", errors)
    if path.suffix.lower() in {".md", ".json", ".jsonl", ".csv", ".yaml", ".yml"}:
        text = path.read_text(encoding="utf-8", errors="ignore").lower()
        for forbidden in FORBIDDEN_EVIDENCE_TEXT:
            require(forbidden.lower() not in text, f"forbidden evidence text {forbidden!r} in {path}", errors)


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def validate_v014_s04_p1_amount_precision(manifest_path: Path = MANIFEST_PATH) -> dict[str, Any]:
    errors: list[str] = []
    manifest = read_json(manifest_path)
    s03_review = validate_v014_s03_stage_review()
    capability = replay_amount_precision_capability()

    require(manifest.get("schema_version") == SCHEMA_VERSION, "manifest schema mismatch", errors)
    require(manifest.get("project_id") == "KMFA", "project_id mismatch", errors)
    require(manifest.get("version") == "0.1.4", "version mismatch", errors)
    require(manifest.get("stage_id") == "S04", "stage_id must be S04", errors)
    require(manifest.get("phase_id") == "S04-P1", "phase_id must be S04-P1", errors)
    require(manifest.get("phase_scope") == "v014_s04_p1_amount_precision_only", "phase scope mismatch", errors)
    require(manifest.get("task_id") == TASK_ID, "task_id mismatch", errors)
    require(manifest.get("acceptance_id") == "ACC-V014-S04-P1-AMOUNT-PRECISION", "acceptance id mismatch", errors)
    require(manifest.get("status") == "completed_validated_local_only_no_go_upload_deferred", "status mismatch", errors)
    require(manifest.get("completed_task_ids") == ["S4PAT01", "S4PAT02", "S4PAT03"], "completed task ids mismatch", errors)

    require(manifest.get("s03_stage_review_dependency_validated") is True, "S03 stage review dependency flag must be true", errors)
    require(s03_review.get("stage_id") == "S03", "S03 review validator did not return Stage 3", errors)
    require(s03_review.get("stage_review_performed") is True, "S03 review must be complete", errors)
    require(s03_review.get("open_review_finding_count") == 0, "S03 review open findings must be zero", errors)
    require(s03_review.get("github_upload_performed") is False, "S03 review upload boundary mismatch", errors)
    require(s03_review.get("next_recommended_phase") == "S04-P1", "S03 review must point next phase to S04-P1", errors)

    require(manifest.get("amount_tools_dependency_validated") is True, "amount tools dependency must be true", errors)
    require(manifest.get("amount_case_count") == capability["amount_case_count"] == 9, "amount case count mismatch", errors)
    require(manifest.get("amount_case_passed_count") == capability["amount_case_passed_count"] == 9, "amount pass count mismatch", errors)
    require(manifest.get("amount_case_results") == capability["amount_case_results"], "amount case replay mismatch", errors)
    require(manifest.get("amount_rejection_count") == capability["amount_rejection_count"] == 9, "amount rejection count mismatch", errors)
    require(
        manifest.get("amount_rejection_passed_count") == capability["amount_rejection_passed_count"] == 9,
        "amount rejection pass count mismatch",
        errors,
    )
    require(manifest.get("amount_rejection_results") == capability["amount_rejection_results"], "rejection replay mismatch", errors)

    require(manifest.get("no_float_dependency_validated") is True, "no-float dependency must be true", errors)
    require(
        manifest.get("scan_fixture_forbidden_float_findings")
        == capability["scan_fixture_forbidden_float_findings"]
        == 3,
        "forbidden fixture finding count mismatch",
        errors,
    )
    require(manifest.get("repository_no_float_scan_passed") is True, "repository no-float scan must pass", errors)
    require(manifest.get("repository_no_float_finding_count") == 0, "repository no-float findings must be zero", errors)
    require(capability["repository_no_float_scan_passed"] is True, "replayed repository no-float scan must pass", errors)

    raw_boundary = manifest.get("raw_data_boundary", {})
    require(raw_boundary.get("local_raw_data_dir") == RAW_INBOX, "raw directory mismatch", errors)
    require(raw_boundary.get("codex_read_allowed_only_when_phase_requires") is True, "raw read policy mismatch", errors)
    require(raw_boundary.get("codex_read_performed_by_this_phase") is False, "raw read performed flag must be false", errors)
    require(raw_boundary.get("codex_list_performed_by_this_phase") is False, "raw list performed flag must be false", errors)
    require(raw_boundary.get("codex_hash_performed_by_this_phase") is False, "raw hash performed flag must be false", errors)
    require(raw_boundary.get("codex_modify_allowed") is False, "raw modify allowed must be false", errors)
    require(raw_boundary.get("codex_delete_allowed") is False, "raw delete allowed must be false", errors)
    require(raw_boundary.get("codex_move_allowed") is False, "raw move allowed must be false", errors)
    require(raw_boundary.get("codex_rename_allowed") is False, "raw rename allowed must be false", errors)
    require(raw_boundary.get("codex_overwrite_allowed") is False, "raw overwrite allowed must be false", errors)
    require(raw_boundary.get("codex_generate_inside_allowed") is False, "raw generate-inside allowed must be false", errors)
    require(raw_boundary.get("github_commit_allowed") is False, "raw GitHub commit allowed must be false", errors)

    for key in BOOLEAN_FALSE_KEYS:
        require(manifest.get(key) is False, f"{key} must be false", errors)
    safety = manifest.get("public_repo_safety", {})
    for key in PUBLIC_SAFETY_FALSE_KEYS:
        require(safety.get(key) is False, f"public_repo_safety.{key} must be false", errors)

    require(manifest.get("current_data_quality_grade") == "Q2", "quality grade mismatch", errors)
    require(manifest.get("current_report_grade") == "D", "report grade mismatch", errors)
    require(manifest.get("release_permission") == "blocked", "release permission mismatch", errors)
    require(manifest.get("current_go_no_go") == "NO_GO", "go/no-go mismatch", errors)
    require("S04-P2" in manifest.get("next_required_step", ""), "next step must point to S04-P2", errors)
    require("GitHub upload" in manifest.get("next_required_step", ""), "next step must preserve upload boundary", errors)

    for ref in manifest.get("amount_tool_refs", []):
        require(Path(ref).exists(), f"missing amount dependency ref: {ref}", errors)
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
        "s03_stage_review_dependency_validated": manifest["s03_stage_review_dependency_validated"],
        "amount_tools_dependency_validated": manifest["amount_tools_dependency_validated"],
        "no_float_dependency_validated": manifest["no_float_dependency_validated"],
        "amount_case_count": manifest["amount_case_count"],
        "amount_case_passed_count": manifest["amount_case_passed_count"],
        "amount_rejection_count": manifest["amount_rejection_count"],
        "amount_rejection_passed_count": manifest["amount_rejection_passed_count"],
        "scan_fixture_forbidden_float_findings": manifest["scan_fixture_forbidden_float_findings"],
        "repository_no_float_scan_passed": manifest["repository_no_float_scan_passed"],
        "raw_dir_read_performed": manifest["raw_dir_read_performed"],
        "raw_dir_list_performed": manifest["raw_dir_list_performed"],
        "raw_dir_hash_performed": manifest["raw_dir_hash_performed"],
        "raw_dir_mutation_performed": manifest["raw_dir_mutation_performed"],
        "raw_layer_write_allowed": manifest["raw_layer_write_allowed"],
        "raw_source_mutation_allowed": manifest["raw_source_mutation_allowed"],
        "raw_value_matching_performed": manifest["raw_value_matching_performed"],
        "field_mapping_performed": manifest["field_mapping_performed"],
        "s04_p2_started": manifest["s04_p2_started"],
        "s04_p3_started": manifest["s04_p3_started"],
        "stage4_review_performed": manifest["stage4_review_performed"],
        "github_upload_performed": manifest["github_upload_performed"],
        "delivery_allowed": manifest["delivery_allowed"],
        "current_data_quality_grade": manifest["current_data_quality_grade"],
        "current_report_grade": manifest["current_report_grade"],
        "release_permission": manifest["release_permission"],
        "current_go_no_go": manifest["current_go_no_go"],
        "next_required_step": manifest["next_required_step"],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA v0.1.4 S04-P1 amount precision evidence.")
    parser.add_argument("--manifest", default=str(MANIFEST_PATH))
    args = parser.parse_args(argv)
    try:
        result = validate_v014_s04_p1_amount_precision(Path(args.manifest))
    except ValidationError as exc:
        print("FAIL: KMFA v0.1.4 S04-P1 amount precision validation failed")
        print(exc)
        return 1
    print(
        "PASS: KMFA v0.1.4 S04-P1 amount precision validator passed "
        f"(amount_cases={result['amount_case_count']}, "
        f"rejections={result['amount_rejection_count']}, "
        f"no_float={str(result['repository_no_float_scan_passed']).lower()}, "
        f"raw_read={str(result['raw_dir_read_performed']).lower()}, "
        f"github_upload={str(result['github_upload_performed']).lower()})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
