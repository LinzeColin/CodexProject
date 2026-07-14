#!/usr/bin/env python3
"""Validate KMFA v0.1.4 S05-P1 A0 file registration evidence."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

from KMFA.tools.check_v014_s04_stage_review import validate_v014_s04_stage_review
from KMFA.tools.v014_s05_p1_a0_file_registration import (
    ACCEPTANCE_ID,
    EXPECTED_BUSINESS_MEMBER_COUNT,
    EXPECTED_EXCEL_COUNT,
    EXPECTED_PDF_COUNT,
    MANIFEST_PATH,
    PRIVATE_DIAGNOSTIC_PATH,
    PUBLIC_CANDIDATES_PATH,
    PUBLIC_REGISTER_PATH,
    RAW_INBOX,
    REPORT_PATH,
    RISK_REGISTER_PATH,
    ROLLBACK_PATH,
    SCHEMA_VERSION,
    TASK_ID,
    TEST_RESULTS_PATH,
)


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
    "field_or_header_plaintext_committed",
    "raw_or_normalized_values_committed",
    "business_values_committed",
)
BOUNDARY_FALSE_KEYS = (
    "raw_inbox_modified_by_this_phase",
    "raw_inbox_deleted_by_this_phase",
    "raw_inbox_moved_by_this_phase",
    "raw_inbox_renamed_by_this_phase",
    "raw_inbox_overwritten_by_this_phase",
    "raw_inbox_written_by_this_phase",
    "raw_inbox_generate_inside_by_this_phase",
    "raw_inbox_create_extra_files_inside_by_this_phase",
    "raw_inbox_mutated_by_this_phase",
    "raw_filenames_committed",
    "raw_hashes_committed",
    "directory_tree_plaintext_committed",
    "zip_member_names_committed",
    "sheet_names_committed",
    "field_or_header_plaintext_committed",
    "row_or_cell_values_committed",
    "business_values_committed",
)
PHASE_SCOPE_FALSE_KEYS = (
    "business_field_parsing_performed",
    "field_level_golden_baseline_performed",
    "s05_p2_performed",
    "s05_p3_performed",
    "stage5_review_performed",
    "github_upload_performed",
    "raw_value_matching_performed",
    "lineage_full_check_performed",
    "formal_report_performed",
    "live_connector_called",
    "opme_deep_coupling_performed",
    "business_execution_performed",
    "next_phase_started",
)
FORBIDDEN_PUBLIC_KEYS = {
    "actual_package_sha256",
    "expected_package_sha256",
    "member_sha256",
    "member_name",
    "member_path",
    "package_name",
    "public_inventory_path",
    "source_package_name",
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
FORBIDDEN_PUBLIC_TEXT = (
    "actual_package_sha256",
    "expected_package_sha256",
    "member_sha256:",
    "member_name:",
    "member_path:",
    "package_name:",
    "public_inventory_path:",
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
FORBIDDEN_TRACKED_SUFFIXES = (".zip", ".xlsx", ".xls", ".xlsm", ".pdf", ".sqlite", ".sqlite3", ".db")


class ValidationError(Exception):
    pass


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ValidationError(f"missing JSON file: {path}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValidationError(f"{path} must contain a JSON object")
    return value


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise ValidationError(f"missing JSONL file: {path}")
    records: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValidationError(f"{path} contains non-object JSONL row")
        records.append(value)
    return records


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


def check_private_diagnostic(require_private_diagnostic: bool, errors: list[str]) -> None:
    require(".codex_private_runtime/" in PRIVATE_DIAGNOSTIC_PATH.as_posix(), "private diagnostic path mismatch", errors)
    tracked = git_output(["ls-files", str(PRIVATE_DIAGNOSTIC_PATH)]).strip()
    require(not tracked, "private diagnostic must not be tracked", errors)
    if not require_private_diagnostic:
        return
    require(PRIVATE_DIAGNOSTIC_PATH.exists(), "private diagnostic must exist for local acceptance", errors)
    if not PRIVATE_DIAGNOSTIC_PATH.exists():
        return
    diagnostic = read_json(PRIVATE_DIAGNOSTIC_PATH)
    require(
        diagnostic.get("schema_version") == "kmfa.private.v014_s05_p1_a0_zip_registration.v1",
        "private diagnostic schema mismatch",
        errors,
    )
    require(
        diagnostic.get("classification") == "private_raw_diagnostic_do_not_commit",
        "private diagnostic classification mismatch",
        errors,
    )
    require("actual_package_sha256" in diagnostic, "private diagnostic missing package hash", errors)
    member_records = diagnostic.get("member_records")
    require(isinstance(member_records, list), "private member_records must be list", errors)
    if isinstance(member_records, list):
        business_records = [item for item in member_records if not item.get("hidden_or_macos_metadata")]
        require(len(business_records) == EXPECTED_BUSINESS_MEMBER_COUNT, "private business member hash count mismatch", errors)
        for record in business_records:
            require(
                re.fullmatch(r"[a-f0-9]{64}", str(record.get("member_sha256", ""))) is not None,
                "private member hash missing",
                errors,
            )
            require(
                re.fullmatch(r"[a-f0-9]{64}", str(record.get("member_name_sha256", ""))) is not None,
                "private member name hash missing",
                errors,
            )


def validate_v014_s05_p1_a0_file_registration(
    manifest_path: Path = MANIFEST_PATH,
    *,
    require_private_diagnostic: bool = False,
) -> dict[str, Any]:
    errors: list[str] = []
    manifest = read_json(manifest_path)
    public_register = read_json(PUBLIC_REGISTER_PATH)
    public_candidates = read_jsonl(PUBLIC_CANDIDATES_PATH)
    stage4 = validate_v014_s04_stage_review()

    for public_value in (manifest, public_register, public_candidates):
        walk_public(public_value, errors)

    require(manifest.get("schema_version") == SCHEMA_VERSION, "schema mismatch", errors)
    require(manifest.get("project_id") == "KMFA", "project_id mismatch", errors)
    require(manifest.get("version") == "0.1.4", "version mismatch", errors)
    require(manifest.get("stage_id") == "S05", "stage_id must be S05", errors)
    require(manifest.get("phase_id") == "S05-P1", "phase_id must be S05-P1", errors)
    require(manifest.get("phase_scope") == "v014_s05_p1_a0_file_registration_only", "phase scope mismatch", errors)
    require(manifest.get("task_id") == TASK_ID, "task_id mismatch", errors)
    require(manifest.get("acceptance_id") == ACCEPTANCE_ID, "acceptance id mismatch", errors)
    require(
        manifest.get("status") == "completed_validated_local_only_no_go_upload_deferred_private_hashes_computed_package_mismatch",
        "status mismatch",
        errors,
    )
    require(stage4.get("stage_id") == "S04", "Stage 4 dependency did not return S04", errors)
    require(stage4.get("stage_review_performed") is True, "Stage 4 review dependency not passed", errors)
    require(stage4.get("github_upload_performed") is False, "Stage 4 dependency upload mismatch", errors)
    require(manifest.get("stage4_review_dependency_validated") is True, "stage4 dependency flag must be true", errors)

    scope = manifest.get("phase_scope_controls", {})
    require(scope.get("current_phase_only") is True, "current_phase_only must be true", errors)
    require(scope.get("a0_file_registration_only") is True, "a0_file_registration_only must be true", errors)
    require(scope.get("raw_root_read_only_hash_authorized") is True, "raw hash authorization missing", errors)
    for key in PHASE_SCOPE_FALSE_KEYS:
        require(scope.get(key) is False, f"phase_scope_controls.{key} must be false", errors)

    file_summary = manifest.get("a0_file_summary", {})
    require(file_summary.get("total_files") == EXPECTED_BUSINESS_MEMBER_COUNT, "A0 file count must be 9", errors)
    require(file_summary.get("pdf_files") == EXPECTED_PDF_COUNT, "A0 PDF count must be 8", errors)
    require(file_summary.get("excel_files") == EXPECTED_EXCEL_COUNT, "A0 Excel count must be 1", errors)
    require(file_summary.get("private_business_member_hash_record_count") == 9, "private member hash count mismatch", errors)
    require(file_summary.get("public_actual_raw_package_hash_committed_count") == 0, "public package hash count must be 0", errors)
    require(file_summary.get("public_actual_raw_member_hash_committed_count") == 0, "public member hash count must be 0", errors)
    require(file_summary.get("raw_member_name_committed_count") == 0, "raw member name committed count must be 0", errors)

    candidate_summary = manifest.get("a0_candidate_summary", {})
    require(candidate_summary.get("candidate_count") == 9, "candidate count must be 9", errors)
    require(candidate_summary.get("q3_machine_candidate_count") == 9, "Q3 candidate count must be 9", errors)
    require(candidate_summary.get("q4_human_locked_count") == 0, "Q4 count must be 0", errors)
    require(candidate_summary.get("q5_calculation_baseline_allowed_count") == 0, "Q5 calculation count must be 0", errors)
    require(candidate_summary.get("q5_formal_report_allowed_count") == 0, "Q5 formal report count must be 0", errors)

    raw = manifest.get("raw_alignment", {})
    require(raw.get("raw_data_inbox_read_required") is True, "raw read required flag must be true", errors)
    for key in ("raw_data_inbox_read_performed", "raw_data_inbox_list_performed", "raw_data_inbox_stat_performed", "raw_data_inbox_hash_performed"):
        require(raw.get(key) is True, f"raw_alignment.{key} must be true", errors)
    for key in (
        "raw_data_inbox_mutation_performed",
        "raw_data_inbox_write_performed",
        "raw_data_inbox_delete_performed",
        "raw_data_inbox_move_performed",
        "raw_data_inbox_rename_performed",
        "raw_data_inbox_overwrite_performed",
        "public_actual_raw_package_hash_committed",
        "public_actual_raw_member_hashes_committed",
        "public_raw_member_names_committed",
        "member_hash_public_backfill_performed",
    ):
        require(raw.get(key) is False, f"raw_alignment.{key} must be false", errors)
    require(raw.get("local_raw_zip_present") is True, "local raw zip must be present", errors)
    require(raw.get("local_raw_zip_openable") is True, "local raw zip must be openable", errors)
    require(raw.get("local_raw_business_member_count") == 9, "business member count must be 9", errors)
    require(raw.get("local_raw_pdf_member_count") == 8, "PDF member count must be 8", errors)
    require(raw.get("local_raw_excel_member_count") == 1, "Excel member count must be 1", errors)
    require(raw.get("private_package_hash_recorded") is True, "private package hash must be recorded", errors)
    require(raw.get("private_business_member_hash_record_count") == 9, "private business member hash count must be 9", errors)
    require(raw.get("private_diagnostic_written") is True, "private diagnostic must be written", errors)
    require(raw.get("raw_root_stat_unchanged_after_scan") is True, "raw root stat must be unchanged", errors)
    require(raw.get("selected_raw_zip_stat_unchanged_after_scan") is True, "selected raw zip stat must be unchanged", errors)
    require(
        raw.get("member_hash_public_backfill_blocked_reason") == "local_raw_package_hash_or_size_mismatch",
        "public hash backfill blocked reason mismatch",
        errors,
    )

    boundary = manifest.get("raw_data_boundary", {})
    require(boundary.get("raw_inbox_path") == str(RAW_INBOX), "raw inbox path mismatch", errors)
    for key in ("raw_inbox_read_by_this_phase", "raw_inbox_listed_by_this_phase", "raw_inbox_stat_by_this_phase", "raw_inbox_hashed_by_this_phase"):
        require(boundary.get(key) is True, f"raw_data_boundary.{key} must be true", errors)
    for key in BOUNDARY_FALSE_KEYS:
        require(boundary.get(key) is False, f"raw_data_boundary.{key} must be false", errors)

    public_summary = public_register.get("file_summary", {})
    require(public_register.get("schema_version") == "kmfa.v014_s05_p1_a0_public_file_register.v1", "public register schema mismatch", errors)
    require(public_register.get("phase_id") == "S05-P1", "public register phase mismatch", errors)
    require(public_summary == file_summary, "public file summary must match manifest", errors)
    file_records = public_register.get("file_records")
    require(isinstance(file_records, list) and len(file_records) == 9, "public file records must contain 9 rows", errors)
    if isinstance(file_records, list):
        for index, record in enumerate(file_records, start=1):
            require(record.get("public_file_ref") == f"V014-A0-FILE-{index:03d}", "public file ref order mismatch", errors)
            require(record.get("content_hash_status") == "computed_private_only", "content hash status mismatch", errors)
            require(record.get("member_name_status") == "private_only_not_committed", "member name status mismatch", errors)
            for key in (
                "q3_machine_candidate",
                "q4_human_locked",
                "q5_calculation_baseline_allowed",
                "field_extraction_allowed_in_s05p1",
                "raw_file_committed",
                "raw_content_committed",
                "raw_filename_committed",
                "raw_hash_committed",
                "zip_member_name_committed",
                "sheet_name_committed",
                "field_or_header_plaintext_committed",
                "row_or_cell_value_committed",
                "business_value_committed",
            ):
                expected = True if key == "q3_machine_candidate" else False
                require(record.get(key) is expected, f"file_record.{key} mismatch", errors)

    require(len(public_candidates) == 9, "public candidates must contain 9 rows", errors)
    for index, record in enumerate(public_candidates, start=1):
        require(record.get("candidate_public_ref") == f"V014-A0-CAND-{index:03d}", "candidate ref order mismatch", errors)
        require(record.get("source_public_file_ref") == f"V014-A0-FILE-{index:03d}", "candidate source file ref mismatch", errors)
        require(record.get("candidate_label_committed") is False, "candidate label must not be committed", errors)
        require(record.get("candidate_label_hash_committed") is False, "candidate label hash must not be committed", errors)
        require(record.get("machine_candidate_quality_grade") == "Q3", "candidate grade must be Q3", errors)
        require(record.get("q4_human_locked") is False, "Q4 must be false", errors)
        require(record.get("q5_calculation_baseline_allowed") is False, "Q5 calc must be false", errors)
        require(record.get("q5_formal_report_allowed") is False, "Q5 report must be false", errors)

    for safety in (manifest.get("public_repo_safety", {}), public_register.get("public_repo_safety", {})):
        for key in PUBLIC_FALSE_KEYS:
            require(safety.get(key) is False, f"public_repo_safety.{key} must be false", errors)

    release = manifest.get("release_state", {})
    require(release.get("current_data_quality_grade") == "Q3", "data quality grade must be Q3", errors)
    require(release.get("current_report_grade") == "D", "report grade must be D", errors)
    require(release.get("current_go_no_go") == "NO_GO", "Go/No-Go must be NO_GO", errors)
    for key in (
        "delivery_allowed",
        "formal_report_allowed",
        "business_decision_basis_allowed",
        "business_execution_allowed",
        "github_main_upload_allowed",
    ):
        require(release.get(key) is False, f"release_state.{key} must be false", errors)
    require(manifest.get("github_upload_performed") is False, "GitHub upload must be false", errors)
    require(
        manifest.get("github_upload_status") == "not_uploaded_deferred_until_v014_stage1_18_complete",
        "GitHub upload status mismatch",
        errors,
    )
    require(manifest.get("next_recommended_phase") == "S05-P2", "next phase mismatch", errors)
    require("Stage 1-18" in manifest.get("next_phase_instruction", ""), "next phase instruction must preserve upload deferral", errors)

    check_private_diagnostic(require_private_diagnostic, errors)
    for ref in manifest.get("evidence_refs", []):
        check_public_safe_file(Path(ref), errors)
    for path in (REPORT_PATH, TEST_RESULTS_PATH, RISK_REGISTER_PATH, ROLLBACK_PATH, MANIFEST_PATH, PUBLIC_REGISTER_PATH, PUBLIC_CANDIDATES_PATH):
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
    parser = argparse.ArgumentParser(description="Validate KMFA v0.1.4 S05-P1 A0 file registration evidence.")
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    parser.add_argument("--require-private-diagnostic", action="store_true")
    args = parser.parse_args(argv)
    try:
        manifest = validate_v014_s05_p1_a0_file_registration(
            args.manifest,
            require_private_diagnostic=args.require_private_diagnostic,
        )
    except ValidationError as exc:
        print("FAIL: KMFA v0.1.4 S05-P1 A0 file registration validation failed")
        print(exc)
        return 1
    print(
        "PASS: KMFA v0.1.4 S05-P1 A0 file registration validated "
        f"(files={manifest['a0_file_summary']['total_files']}, "
        f"pdf={manifest['a0_file_summary']['pdf_files']}, "
        f"excel={manifest['a0_file_summary']['excel_files']}, "
        f"private_hashes={manifest['a0_file_summary']['private_business_member_hash_record_count']}, "
        f"q3={manifest['a0_candidate_summary']['q3_machine_candidate_count']}, "
        f"q4={manifest['a0_candidate_summary']['q4_human_locked_count']}, "
        f"github_upload={str(manifest['github_upload_performed']).lower()})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
