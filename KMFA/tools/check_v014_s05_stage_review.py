#!/usr/bin/env python3
"""Validate KMFA v0.1.4 Stage 5 review evidence."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from KMFA.tools.check_v014_s05_p1_a0_file_registration import validate_v014_s05_p1_a0_file_registration
from KMFA.tools.check_v014_s05_p2_field_golden_baseline import validate_v014_s05_p2_field_golden_baseline
from KMFA.tools.check_v014_s05_p3_authority_baseline_lock import validate_v014_s05_p3_authority_baseline_lock
from KMFA.tools.v014_s05_stage_review import (
    MANIFEST_PATH,
    NEXT_INSTRUCTION,
    NEXT_PHASE,
    PHASE_MANIFESTS,
    RAW_INBOX,
    REPORT_PATH,
    RISK_REGISTER_PATH,
    ROLLBACK_PATH,
    SCHEMA_VERSION,
    TASK_ID,
    TEST_RESULTS_PATH,
)


FORBIDDEN_EXTENSIONS = {".zip", ".xlsx", ".xls", ".xlsm", ".pdf", ".sqlite", ".sqlite3", ".db"}
FORBIDDEN_TEXT = (
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
    "s05_p2_raw_inbox_read_by_phase",
    "s05_p3_raw_inbox_read_by_phase",
    "raw_inbox_mutated_by_stage5",
    "raw_filenames_committed",
    "raw_hashes_committed",
    "directory_tree_plaintext_committed",
    "zip_member_names_committed",
    "sheet_names_committed",
    "source_header_plaintext_committed",
    "row_or_cell_values_committed",
    "source_or_normalized_values_committed",
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
    "sheet_names_committed",
    "source_header_plaintext_committed",
    "row_or_cell_values_committed",
    "source_or_normalized_values_committed",
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
    "s05_p1_validator",
    "s05_p2_validator",
    "s05_p3_validator",
    "stage_review_validator",
    "focused_unit_test",
    "py_compile",
    "no_omission_check",
    "no_float_money_check",
    "governance_validator",
    "lean_governance_validator",
    "governance_sync_validator",
    "structured_parse",
    "ruby_yaml_parse",
    "raw_private_scan",
    "secret_scan",
    "public_stage5_semantic_scan",
    "diff_check",
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
}


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
    require(path.suffix.lower() not in FORBIDDEN_EXTENSIONS, f"forbidden evidence extension: {path}", errors)
    if path.suffix.lower() in {".md", ".json", ".jsonl", ".csv", ".yaml", ".yml"}:
        lower = path.read_text(encoding="utf-8", errors="ignore").lower()
        for forbidden in FORBIDDEN_TEXT:
            require(forbidden.lower() not in lower, f"forbidden evidence text {forbidden!r} in {path}", errors)


def validate_v014_s05_stage_review(manifest_path: Path = MANIFEST_PATH) -> dict[str, Any]:
    errors: list[str] = []
    manifest = read_json(manifest_path)
    p1 = validate_v014_s05_p1_a0_file_registration()
    p2 = validate_v014_s05_p2_field_golden_baseline()
    p3 = validate_v014_s05_p3_authority_baseline_lock()
    p1_files = p1["a0_file_summary"]
    p1_candidates = p1["a0_candidate_summary"]
    p2_fields = p2["field_candidate_summary"]
    p3_authority = p3["authority_baseline_summary"]

    walk_public(manifest, errors)
    require(manifest.get("schema_version") == SCHEMA_VERSION, "schema mismatch", errors)
    require(manifest.get("project_id") == "KMFA", "project_id mismatch", errors)
    require(manifest.get("version") == "0.1.4", "version mismatch", errors)
    require(manifest.get("stage_id") == "S05", "stage_id must be S05", errors)
    require(manifest.get("review_id") == TASK_ID, "review_id mismatch", errors)
    require(manifest.get("task_id") == TASK_ID, "task_id mismatch", errors)
    require(manifest.get("acceptance_id") == "ACC-V014-S05-STAGE-REVIEW", "acceptance id mismatch", errors)
    require(manifest.get("review_scope") == "v014_s05_stage_review_only", "review scope mismatch", errors)
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
    require(manifest.get("s06_p1_started") is False, "S06-P1 must not be started", errors)
    require(manifest.get("raw_value_matching_performed") is False, "raw value matching must not be performed", errors)
    require(manifest.get("zero_delta_validation_performed") is False, "zero-delta must not be performed", errors)
    require(manifest.get("lineage_full_check_performed") is False, "lineage full check must not be performed", errors)
    require(manifest.get("formal_report_performed") is False, "formal report must not be performed", errors)
    require(manifest.get("live_connector_called") is False, "live connector must not be called", errors)
    require(manifest.get("opme_deep_coupling_performed") is False, "OpMe deep coupling must not be performed", errors)
    require(manifest.get("business_execution_performed") is False, "business execution must not be performed", errors)
    require(manifest.get("phase_count") == 3, "phase_count must be 3", errors)
    require(
        manifest.get("phase_results") == {"S05-P1": "PASS", "S05-P2": "PASS", "S05-P3": "PASS"},
        "phase_results mismatch",
        errors,
    )
    require(p1.get("phase_id") == "S05-P1", "S05-P1 validator did not return S05-P1", errors)
    require(p2.get("phase_id") == "S05-P2", "S05-P2 validator did not return S05-P2", errors)
    require(p3.get("phase_id") == "S05-P3", "S05-P3 validator did not return S05-P3", errors)
    require(manifest.get("open_review_finding_count") == 0, "open findings must be 0", errors)
    require(manifest.get("fixed_review_finding_count") == 0, "fixed findings must be 0", errors)
    require(manifest.get("review_findings") == [], "review findings must be empty", errors)

    reviewed = manifest.get("reviewed_phase_manifests", {})
    for phase, path in PHASE_MANIFESTS.items():
        require(reviewed.get(phase) == str(path), f"{phase} manifest ref mismatch", errors)
        require(Path(path).exists(), f"missing phase manifest: {path}", errors)

    gate = manifest.get("stage_gate", {})
    require(gate.get("a0_total_files") == p1_files.get("total_files") == 9, "A0 total file count mismatch", errors)
    require(gate.get("a0_pdf_files") == p1_files.get("pdf_files") == 8, "A0 PDF count mismatch", errors)
    require(gate.get("a0_excel_files") == p1_files.get("excel_files") == 1, "A0 Excel count mismatch", errors)
    require(
        gate.get("private_business_member_hash_record_count")
        == p1_files.get("private_business_member_hash_record_count")
        == 9,
        "private member hash diagnostic count mismatch",
        errors,
    )
    require(gate.get("a0_q3_candidate_count") == p1_candidates.get("q3_machine_candidate_count") == 9, "Q3 candidate count mismatch", errors)
    require(gate.get("a0_q4_locked_count") == p1_candidates.get("q4_human_locked_count") == 0, "S05-P1 Q4 count mismatch", errors)
    require(gate.get("field_contract_count") == p2_fields.get("required_field_contract_count") == 5, "field contract count mismatch", errors)
    require(gate.get("field_candidate_count") == p2_fields.get("field_candidate_count") == 45, "field candidate count mismatch", errors)
    require(gate.get("pdf_field_candidate_count") == p2_fields.get("pdf_field_candidate_count") == 40, "PDF candidate count mismatch", errors)
    require(gate.get("excel_field_candidate_count") == p2_fields.get("excel_field_candidate_count") == 5, "Excel candidate count mismatch", errors)
    require(
        gate.get("source_anchor_recorded_private_only_count") == p2_fields.get("source_anchor_recorded_private_only_count") == 40,
        "source anchor count mismatch",
        errors,
    )
    require(
        gate.get("owner_downgraded_excel_field_count") == p2_fields.get("owner_downgraded_excel_field_count") == 5,
        "owner downgraded field count mismatch",
        errors,
    )
    require(gate.get("s05_p2_completion_gate_ready") is True, "S05-P2 completion gate must be ready", errors)
    require(gate.get("authority_record_count") == p3_authority.get("authority_record_count") == 45, "authority count mismatch", errors)
    require(
        gate.get("q5_calculation_baseline_locked_count")
        == p3_authority.get("q5_calculation_baseline_locked_count")
        == 40,
        "Q5 calculation baseline lock count mismatch",
        errors,
    )
    require(
        gate.get("excluded_cross_source_support_only_count")
        == p3_authority.get("excluded_cross_source_support_only_count")
        == 5,
        "excluded field count mismatch",
        errors,
    )
    require(gate.get("q4_human_confirmed_count") == p3_authority.get("q4_human_confirmed_count") == 40, "Q4 count mismatch", errors)
    require(gate.get("q5_full_quality_grade_allowed_count") == 0, "full Q5 count must be 0", errors)
    require(gate.get("zero_delta_validated_count") == 0, "zero-delta count must be 0", errors)
    require(gate.get("lineage_full_check_completed_count") == 0, "lineage count must be 0", errors)
    require(gate.get("formal_report_allowed_count") == 0, "formal report count must be 0", errors)
    require(gate.get("current_data_quality_grade") == "Q4", "stage gate data quality mismatch", errors)
    require(gate.get("current_report_grade") == "D", "stage gate report grade mismatch", errors)
    require(gate.get("release_permission") == "blocked", "stage gate release permission mismatch", errors)

    release = manifest.get("release_state", {})
    for key in RELEASE_FALSE_KEYS:
        require(release.get(key) is False, f"release_state.{key} must be false", errors)
    require(release.get("current_go_no_go") == "NO_GO", "current Go/No-Go must be NO_GO", errors)
    require(release.get("current_data_quality_grade") == "Q4", "current data quality grade must be Q4", errors)
    require(release.get("current_report_grade") == "D", "current report grade must be D", errors)
    require(release.get("release_permission") == "blocked", "release permission must be blocked", errors)

    raw = manifest.get("raw_data_boundary", {})
    require(raw.get("raw_inbox_path") == str(RAW_INBOX), "raw inbox path mismatch", errors)
    require(raw.get("private_runtime_output_dir") == "KMFA/.codex_private_runtime/", "private runtime ref mismatch", errors)
    for key in RAW_REVIEW_FALSE_KEYS:
        require(raw.get(key) is False, f"raw_data_boundary.{key} must be false", errors)
    for key in (
        "s05_p1_raw_read_list_stat_hash_authorized",
        "s05_p1_raw_inbox_read_by_phase",
        "s05_p1_raw_inbox_listed_by_phase",
        "s05_p1_raw_inbox_stat_by_phase",
        "s05_p1_raw_inbox_hashed_by_phase",
    ):
        require(raw.get(key) is True, f"raw_data_boundary.{key} must be true", errors)

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
    parser = argparse.ArgumentParser(description="Validate KMFA v0.1.4 Stage 5 review evidence.")
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    args = parser.parse_args()
    try:
        manifest = validate_v014_s05_stage_review(args.manifest)
    except ValidationError as exc:
        print("FAIL: KMFA v0.1.4 Stage 5 review validation failed")
        print(exc)
        return 1
    gate = manifest["stage_gate"]
    print(
        "PASS: KMFA v0.1.4 Stage 5 review validated "
        f"(phases={manifest['phase_count']}, findings_open={manifest['open_review_finding_count']}, "
        f"a0_files={gate['a0_total_files']}, field_candidates={gate['field_candidate_count']}, "
        f"q5_calc_locked={gate['q5_calculation_baseline_locked_count']}, "
        f"excluded={gate['excluded_cross_source_support_only_count']}, "
        f"github_upload={str(manifest['github_upload_performed']).lower()}, "
        f"next={manifest['next_recommended_phase']}, go_no_go={manifest['release_state']['current_go_no_go']})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
