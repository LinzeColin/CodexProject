#!/usr/bin/env python3
"""Validate KMFA v0.1.4 Stage 4 review evidence."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from KMFA.tools.check_v014_s04_p1_amount_precision import validate_v014_s04_p1_amount_precision
from KMFA.tools.check_v014_s04_p2_field_standardization import validate_v014_s04_p2_field_standardization
from KMFA.tools.check_v014_s04_p3_basic_tool_report import validate_v014_s04_p3_basic_tool_report
from KMFA.tools.v014_s04_stage_review import (
    MANIFEST_PATH,
    NEXT_INSTRUCTION,
    NEXT_PHASE,
    RAW_INBOX,
    REPORT_PATH,
    RISK_REGISTER_PATH,
    ROLLBACK_PATH,
    SCHEMA_VERSION,
    TASK_ID,
    TEST_RESULTS_PATH,
)


PHASE_MANIFESTS = {
    "S04-P1": Path("KMFA/stage_artifacts/V014_S04_P1_AMOUNT_PRECISION/machine/amount_precision_manifest.json"),
    "S04-P2": Path("KMFA/stage_artifacts/V014_S04_P2_FIELD_STANDARDIZATION/machine/field_standardization_manifest.json"),
    "S04-P3": Path("KMFA/stage_artifacts/V014_S04_P3_BASIC_TOOL_REPORT/machine/basic_tool_report_manifest.json"),
}
FORBIDDEN_EXTENSIONS = {".zip", ".xlsx", ".xls", ".xlsm", ".pdf", ".sqlite", ".sqlite3", ".db"}
FORBIDDEN_TEXT = (
    "raw_" "value:",
    "normalized_" "value:",
    "source_" "header_" "text:",
    "original_" "filename:",
    "member_" "path:",
    "member_" "name:",
    "sheet_" "name:",
    "cell_" "value:",
    "row_" "value:",
    "business_" "value:",
    "bank_" "statement:",
    "contract_" "full_" "text:",
    "salary_" "detail:",
    "tax_" "filing:",
    "connector_" "token:",
    "connector_" "password:",
    "api_" "key:",
    "private_" "key:",
    "-----" "BEGIN",
    "s" "k-",
)
RAW_BOUNDARY_FALSE_KEYS = (
    "raw_inbox_read_by_this_review",
    "raw_inbox_listed_by_this_review",
    "raw_inbox_inventory_by_this_review",
    "raw_inbox_hashed_by_this_review",
    "raw_inbox_modified_by_this_review",
    "raw_inbox_deleted_by_this_review",
    "raw_inbox_moved_by_this_review",
    "raw_inbox_renamed_by_this_review",
    "raw_inbox_overwritten_by_this_review",
    "raw_inbox_written_by_this_review",
    "s04_p1_raw_read_performed",
    "s04_p2_raw_read_performed",
    "s04_p3_raw_read_performed",
    "raw_inbox_mutated_by_stage4",
    "raw_filenames_committed",
    "raw_hashes_committed",
    "directory_tree_plaintext_committed",
    "zip_member_names_committed",
    "field_or_header_plaintext_committed",
    "row_or_cell_values_committed",
    "business_values_committed",
    "zip_committed",
    "excel_workbook_committed",
    "pdf_committed",
    "private_csv_committed",
    "sqlite_or_db_committed",
    "credentials_committed",
)
PUBLIC_SAFETY_FALSE_KEYS = (
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
    "field_or_header_plaintext_committed",
    "raw_or_normalized_values_committed",
    "business_values_committed",
)
RELEASE_FALSE_KEYS = (
    "delivery_allowed",
    "formal_report_allowed",
    "business_decision_basis_allowed",
    "business_execution_allowed",
    "github_main_upload_allowed",
)
VALIDATION_KEYS = (
    "s04_p1_validator",
    "s04_p2_validator",
    "s04_p3_validator",
    "stage_review_validator",
    "focused_unit_test",
    "py_compile",
    "basic_tool_boundary_test",
    "tool_report_json_render",
    "tool_report_markdown_render",
    "no_omission_check",
    "no_float_money_check",
    "governance_validator",
    "lean_governance_validator",
    "governance_sync_validator",
    "structured_parse",
    "ruby_yaml_parse",
    "raw_private_scan",
    "secret_scan",
    "diff_check",
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


def check_public_safe_file(path: Path, errors: list[str]) -> None:
    require(path.exists(), f"missing evidence file: {path}", errors)
    if not path.exists():
        return
    require(path.suffix.lower() not in FORBIDDEN_EXTENSIONS, f"forbidden evidence extension: {path}", errors)
    if path.suffix.lower() in {".md", ".json", ".jsonl", ".csv", ".yaml", ".yml"}:
        text = path.read_text(encoding="utf-8", errors="ignore").lower()
        for forbidden in FORBIDDEN_TEXT:
            require(forbidden.lower() not in text, f"forbidden evidence text {forbidden!r} in {path}", errors)


def validate_v014_s04_stage_review(manifest_path: Path = MANIFEST_PATH) -> dict[str, Any]:
    errors: list[str] = []
    manifest = read_json(manifest_path)
    p1 = validate_v014_s04_p1_amount_precision()
    p2 = validate_v014_s04_p2_field_standardization()
    p3 = validate_v014_s04_p3_basic_tool_report()

    require(manifest.get("schema_version") == SCHEMA_VERSION, "schema mismatch", errors)
    require(manifest.get("project_id") == "KMFA", "project_id mismatch", errors)
    require(manifest.get("version") == "0.1.4", "version mismatch", errors)
    require(manifest.get("stage_id") == "S04", "stage_id must be S04", errors)
    require(manifest.get("review_id") == TASK_ID, "review_id mismatch", errors)
    require(manifest.get("task_id") == TASK_ID, "task_id mismatch", errors)
    require(manifest.get("acceptance_id") == "ACC-V014-S04-STAGE-REVIEW", "acceptance id mismatch", errors)
    require(manifest.get("review_scope") == "v014_s04_stage_review_only", "review scope mismatch", errors)
    require(
        manifest.get("status") == "review_passed_local_only_no_go_upload_deferred_until_v014_stage1_18_complete",
        "status mismatch",
        errors,
    )
    require(manifest.get("stage_review_performed") is True, "stage_review_performed must be true", errors)
    require(manifest.get("github_upload_performed") is False, "GitHub upload must not be performed", errors)
    require(
        manifest.get("github_upload_status") == "not_uploaded_deferred_until_v014_stage1_18_complete",
        "GitHub upload status mismatch",
        errors,
    )
    require(manifest.get("s05_p1_started") is False, "S05-P1 must not be started", errors)
    require(manifest.get("raw_value_matching_performed") is False, "raw value matching must not be performed", errors)
    require(
        manifest.get("field_mapping_beyond_s04_performed") is False,
        "field mapping beyond S04 must not be performed",
        errors,
    )
    require(manifest.get("lineage_full_check_performed") is False, "lineage full check must not be performed", errors)
    require(manifest.get("formal_report_performed") is False, "formal report must not be performed", errors)
    require(manifest.get("live_connector_called") is False, "live connector must not be called", errors)
    require(manifest.get("opme_deep_coupling_performed") is False, "OpMe deep coupling must not be performed", errors)
    require(manifest.get("business_execution_performed") is False, "business execution must not be performed", errors)
    require(manifest.get("phase_count") == 3, "phase_count must be 3", errors)
    require(
        manifest.get("phase_results") == {"S04-P1": "PASS", "S04-P2": "PASS", "S04-P3": "PASS"},
        "phase_results mismatch",
        errors,
    )
    require(p1.get("phase_id") == "S04-P1", "S04-P1 validator did not return S04-P1", errors)
    require(p2.get("phase_id") == "S04-P2", "S04-P2 validator did not return S04-P2", errors)
    require(p3.get("phase_id") == "S04-P3", "S04-P3 validator did not return S04-P3", errors)
    require(manifest.get("open_review_finding_count") == 0, "open findings must be 0", errors)
    require(manifest.get("fixed_review_finding_count") == 0, "fixed findings must be 0", errors)
    require(manifest.get("review_findings") == [], "review findings must be empty", errors)

    reviewed = manifest.get("reviewed_phase_manifests", {})
    for phase, path in PHASE_MANIFESTS.items():
        require(reviewed.get(phase) == str(path), f"{phase} manifest ref mismatch", errors)
        require(path.exists(), f"missing phase manifest: {path}", errors)

    gate = manifest.get("stage_gate", {})
    require(gate.get("amount_case_count") == p1.get("amount_case_count") == 9, "amount case count mismatch", errors)
    require(gate.get("amount_rejection_count") == p1.get("amount_rejection_count") == 9, "amount rejection count mismatch", errors)
    require(gate.get("repository_no_float_scan_passed") is True, "no-float scan summary mismatch", errors)
    require(gate.get("canonical_field_count") == p2.get("canonical_field_count") == 6, "canonical field count mismatch", errors)
    require(gate.get("alias_dictionary_row_count") == p2.get("alias_dictionary_row_count") == 32, "alias count mismatch", errors)
    require(gate.get("mapping_record_count") == p2.get("mapping_record_count") == 6, "mapping count mismatch", errors)
    require(gate.get("field_quality_status_count") == p2.get("quality_status_count") == 5, "quality status mismatch", errors)
    require(gate.get("synthetic_boundary_case_total") == p3.get("synthetic_boundary_case_total") == 22, "case total mismatch", errors)
    require(gate.get("synthetic_boundary_case_passed") == p3.get("synthetic_boundary_case_passed") == 22, "case pass mismatch", errors)
    require(gate.get("synthetic_boundary_case_failed") == p3.get("synthetic_boundary_case_failed") == 0, "case failed mismatch", errors)
    require(gate.get("amount_boundary_case_count") == p3.get("amount_boundary_case_count") == 11, "amount boundary mismatch", errors)
    require(gate.get("date_period_boundary_case_count") == p3.get("date_period_boundary_case_count") == 11, "date/period boundary mismatch", errors)
    require(gate.get("json_report_generated") is True, "JSON report flag mismatch", errors)
    require(gate.get("markdown_report_generated") is True, "Markdown report flag mismatch", errors)
    require(gate.get("current_data_quality_grade") == "Q2", "stage gate data quality mismatch", errors)
    require(gate.get("current_report_grade") == "D", "stage gate report grade mismatch", errors)
    require(gate.get("release_permission") == "blocked", "stage gate release permission mismatch", errors)

    release = manifest.get("release_state", {})
    for key in RELEASE_FALSE_KEYS:
        require(release.get(key) is False, f"release_state.{key} must be false", errors)
    require(release.get("current_go_no_go") == "NO_GO", "current Go/No-Go must be NO_GO", errors)
    require(release.get("current_data_quality_grade") == "Q2", "current data quality grade must be Q2", errors)
    require(release.get("current_report_grade") == "D", "current report grade must be D", errors)
    require(release.get("release_permission") == "blocked", "release permission must be blocked", errors)

    raw = manifest.get("raw_data_boundary", {})
    require(raw.get("raw_inbox_path") == RAW_INBOX, "raw inbox path mismatch", errors)
    require(raw.get("private_runtime_output_dir") == "KMFA/.codex_private_runtime/", "private runtime ref mismatch", errors)
    for key in RAW_BOUNDARY_FALSE_KEYS:
        require(raw.get(key) is False, f"raw_data_boundary.{key} must be false", errors)

    safety = manifest.get("public_repo_safety", {})
    for key in PUBLIC_SAFETY_FALSE_KEYS:
        require(safety.get(key) is False, f"public_repo_safety.{key} must be false", errors)

    validation = manifest.get("validation_summary", {})
    for key in VALIDATION_KEYS:
        require(validation.get(key) == "PASS", f"validation_summary.{key} must be PASS", errors)

    require(manifest.get("next_recommended_phase") == NEXT_PHASE, "next recommended phase mismatch", errors)
    require(manifest.get("next_phase_instruction") == NEXT_INSTRUCTION, "next phase instruction mismatch", errors)

    for ref in manifest.get("evidence_refs", []):
        check_public_safe_file(Path(ref), errors)
    for path in (REPORT_PATH, TEST_RESULTS_PATH, RISK_REGISTER_PATH, ROLLBACK_PATH, MANIFEST_PATH):
        check_public_safe_file(path, errors)

    tracked_files = git_output(["ls-files", "KMFA"]).splitlines()
    forbidden_tracked = [
        path for path in tracked_files if path.lower().endswith(tuple(FORBIDDEN_EXTENSIONS)) or ".codex_private_runtime/" in path
    ]
    require(not forbidden_tracked, f"forbidden public/private tracked files: {forbidden_tracked}", errors)
    require("codex/kmfa" in git_output(["status", "--short", "--branch"]), "git status must be on codex/kmfa", errors)

    if errors:
        raise ValidationError("\n".join(errors))
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA v0.1.4 Stage 4 review evidence.")
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    args = parser.parse_args()
    try:
        manifest = validate_v014_s04_stage_review(args.manifest)
    except ValidationError as exc:
        print("FAIL: KMFA v0.1.4 Stage 4 review validation failed")
        print(exc)
        return 1
    gate = manifest["stage_gate"]
    print(
        "PASS: KMFA v0.1.4 Stage 4 review validated "
        f"(phases={manifest['phase_count']}, findings_open={manifest['open_review_finding_count']}, "
        f"amount={gate['amount_case_count']}/{gate['amount_rejection_count']}, "
        f"fields={gate['canonical_field_count']}/{gate['alias_dictionary_row_count']}, "
        f"tool_cases={gate['synthetic_boundary_case_passed']}/{gate['synthetic_boundary_case_total']}, "
        f"github_upload={str(manifest['github_upload_performed']).lower()}, "
        f"next={manifest['next_recommended_phase']}, go_no_go={manifest['release_state']['current_go_no_go']})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
