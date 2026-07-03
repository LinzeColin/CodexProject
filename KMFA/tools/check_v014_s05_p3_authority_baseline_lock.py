#!/usr/bin/env python3
"""Validate KMFA v0.1.4 S05-P3 authority baseline lock evidence."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

from KMFA.tools.check_v014_s05_p2_field_golden_baseline import validate_v014_s05_p2_field_golden_baseline
from KMFA.tools.v014_s05_p1_a0_file_registration import RAW_INBOX
from KMFA.tools.v014_s05_p3_authority_baseline_lock import (
    ACCEPTANCE_ID,
    BASELINE_VERSION,
    LOCK_STATUS_EXCLUDED,
    LOCK_STATUS_Q5,
    MANIFEST_PATH,
    PUBLIC_AUTHORITY_MANIFEST_PATH,
    PUBLIC_AUTHORITY_RECORDS_PATH,
    RECORD_SCHEMA_VERSION,
    REPORT_PATH,
    RISK_REGISTER_PATH,
    ROLLBACK_PATH,
    SCHEMA_VERSION,
    TASK_ID,
    TEST_RESULTS_PATH,
    sha256_payload,
)


HASH_RE = re.compile(r"^sha256:[a-f0-9]{64}$")
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
    "source_or_normalized_values_committed",
    "row_or_cell_values_committed",
    "business_values_committed",
)
BOUNDARY_FALSE_KEYS = (
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
    "raw_inbox_generate_inside_by_this_phase",
    "raw_inbox_create_extra_files_inside_by_this_phase",
    "raw_inbox_mutated_by_this_phase",
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
PHASE_SCOPE_FALSE_KEYS = (
    "raw_inbox_read_required_by_this_phase",
    "raw_inbox_read_by_this_phase",
    "raw_inbox_listed_by_this_phase",
    "raw_inbox_stat_by_this_phase",
    "raw_inbox_hashed_by_this_phase",
    "raw_inbox_mutated_by_this_phase",
    "private_runtime_written_by_this_phase",
    "business_field_parsing_from_raw_performed",
    "source_value_matching_performed",
    "stage5_review_performed",
    "github_upload_performed",
    "lineage_full_check_performed",
    "zero_delta_validation_performed",
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
        lower = path.read_text(encoding="utf-8", errors="ignore").lower()
        for forbidden in FORBIDDEN_PUBLIC_TEXT:
            require(forbidden.lower() not in lower, f"forbidden public text {forbidden!r} in {path}", errors)


def validate_v014_s05_p3_authority_baseline_lock(manifest_path: Path = MANIFEST_PATH) -> dict[str, Any]:
    errors: list[str] = []
    manifest = read_json(manifest_path)
    authority_manifest = read_json(PUBLIC_AUTHORITY_MANIFEST_PATH)
    authority_records = read_jsonl(PUBLIC_AUTHORITY_RECORDS_PATH)
    s05_p2 = validate_v014_s05_p2_field_golden_baseline()

    for public_value in (manifest, authority_manifest, authority_records):
        walk_public(public_value, errors)

    require(manifest.get("schema_version") == SCHEMA_VERSION, "schema mismatch", errors)
    require(manifest.get("project_id") == "KMFA", "project_id mismatch", errors)
    require(manifest.get("version") == "0.1.4", "version mismatch", errors)
    require(manifest.get("stage_id") == "S05", "stage_id must be S05", errors)
    require(manifest.get("phase_id") == "S05-P3", "phase_id must be S05-P3", errors)
    require(
        manifest.get("phase_scope") == "v014_s05_p3_authority_baseline_lock_only",
        "phase scope mismatch",
        errors,
    )
    require(manifest.get("task_id") == TASK_ID, "task id mismatch", errors)
    require(manifest.get("acceptance_id") == ACCEPTANCE_ID, "acceptance id mismatch", errors)
    require(
        manifest.get("status")
        == "completed_validated_local_only_no_go_upload_deferred_authority_baseline_locked_public_safe",
        "status mismatch",
        errors,
    )
    require(manifest.get("completed_task_ids") == ["S05P3T01", "S05P3T02", "S05P3T03"], "task ids mismatch", errors)

    require(s05_p2.get("phase_id") == "S05-P2", "S05-P2 dependency phase mismatch", errors)
    require(s05_p2.get("github_upload_performed") is False, "S05-P2 upload boundary mismatch", errors)
    require(s05_p2.get("next_recommended_phase") == "S05-P3", "S05-P2 next phase mismatch", errors)
    require(manifest.get("s05_p2_dependency_validated") is True, "S05-P2 dependency flag must be true", errors)

    owner = manifest.get("owner_decision_summary", {})
    require(owner.get("active_actor_role_validated") is True, "active actor role must be validated", errors)
    require(owner.get("active_decision_present") is True, "active decision must be present", errors)
    require(owner.get("active_decision_code") == "downgrade_to_cross_source_support", "active decision mismatch", errors)
    require(owner.get("active_decision_public_safe") is True, "active decision public-safe mismatch", errors)
    require(
        owner.get("active_decision_raw_or_plaintext_values_included") is False,
        "active decision raw/plaintext flag mismatch",
        errors,
    )
    require(owner.get("active_preview_q5_exclusion_confirmed") is True, "owner q5 exclusion mismatch", errors)
    require(owner.get("completion_gate_ready") is True, "completion gate must be ready", errors)

    summary = manifest.get("authority_baseline_summary", {})
    expected_summary = {
        "authority_record_count": 45,
        "field_candidate_count": 45,
        "q5_calculation_baseline_locked_count": 40,
        "excluded_cross_source_support_only_count": 5,
        "q4_human_confirmed_count": 40,
        "q5_calculation_baseline_allowed_count": 40,
        "q5_full_quality_grade_allowed_count": 0,
        "formal_report_allowed_count": 0,
        "zero_delta_validated_count": 0,
        "lineage_full_check_completed_count": 0,
        "pdf_locked_field_count": 40,
        "excel_excluded_field_count": 5,
        "source_format_counts": {"pdf": 40, "xlsx": 5},
        "lock_status_counts": {LOCK_STATUS_EXCLUDED: 5, LOCK_STATUS_Q5: 40},
    }
    for key, expected in expected_summary.items():
        require(summary.get(key) == expected, f"authority summary {key} mismatch", errors)

    require(authority_manifest.get("schema_version") == "kmfa.v014_s05_p3_public_authority_baseline.v1", "authority manifest schema mismatch", errors)
    require(authority_manifest.get("baseline_version") == BASELINE_VERSION, "authority baseline version mismatch", errors)
    require(authority_manifest.get("authority_summary") == summary, "authority manifest summary mismatch", errors)
    require(authority_manifest.get("baseline_content_hash") == sha256_payload(authority_records), "baseline content hash mismatch", errors)
    require(manifest.get("baseline_content_hash") == authority_manifest.get("baseline_content_hash"), "manifest baseline hash mismatch", errors)
    require(HASH_RE.match(str(manifest.get("baseline_content_hash", ""))) is not None, "baseline hash must be sha256", errors)
    require(manifest.get("field_contract_count") == 5, "field contract count mismatch", errors)

    require(len(authority_records) == 45, "authority records must contain 45 rows", errors)
    q5_rows = [record for record in authority_records if record.get("lock_status") == LOCK_STATUS_Q5]
    excluded_rows = [record for record in authority_records if record.get("lock_status") == LOCK_STATUS_EXCLUDED]
    require(len(q5_rows) == 40, "Q5 calculation baseline row count mismatch", errors)
    require(len(excluded_rows) == 5, "excluded row count mismatch", errors)
    seen_refs: set[str] = set()
    for index, record in enumerate(authority_records, start=1):
        require(record.get("schema_version") == RECORD_SCHEMA_VERSION, "record schema mismatch", errors)
        require(record.get("authority_record_ref") == f"V014-S05P3-AUTH-LOCK-{index:03d}", "record ref order mismatch", errors)
        require(record.get("authority_record_ref") not in seen_refs, "duplicate authority record ref", errors)
        seen_refs.add(str(record.get("authority_record_ref")))
        require(record.get("baseline_version") == BASELINE_VERSION, "record baseline version mismatch", errors)
        require(HASH_RE.match(str(record.get("public_field_candidate_hash", ""))) is not None, "candidate public hash mismatch", errors)
        require(HASH_RE.match(str(record.get("authority_lock_public_hash", ""))) is not None, "authority public hash mismatch", errors)
        require(record.get("field_role_status") == "canonical_contract_role_not_raw_header_text", "field role status mismatch", errors)
        source_lock = record.get("source_lock", {})
        require(source_lock.get("source_locator_status") == "private_only_not_committed", "source locator status mismatch", errors)
        require(source_lock.get("page_sheet_cell_status") == "private_only_not_committed", "page/sheet/cell status mismatch", errors)
        require(source_lock.get("source_value_status") == "private_only_not_committed", "source value status mismatch", errors)
        require(source_lock.get("normalized_value_status") == "private_only_not_committed", "normalized value status mismatch", errors)
        quality = record.get("quality_state", {})
        require(quality.get("machine_candidate_quality_grade") == "Q3", "machine grade mismatch", errors)
        require(quality.get("q5_full_quality_grade_allowed") is False, "full Q5 quality must remain false", errors)
        require(quality.get("zero_delta_validated") is False, "zero-delta must remain false", errors)
        require(quality.get("lineage_full_check_completed") is False, "lineage full check must remain false", errors)
        require(quality.get("formal_report_allowed") is False, "formal report must remain false", errors)
        for key, expected in (
            ("raw_business_data_committed", False),
            ("raw_filenames_committed", False),
            ("raw_hashes_committed", False),
            ("source_header_plaintext_committed", False),
            ("sheet_names_committed", False),
            ("zip_member_names_committed", False),
            ("row_or_cell_values_committed", False),
            ("source_or_normalized_values_committed", False),
            ("business_values_committed", False),
            ("formal_report_committed", False),
        ):
            require(record.get("public_repo_safety", {}).get(key) is expected, f"record public safety {key} mismatch", errors)
    for record in q5_rows:
        quality = record.get("quality_state", {})
        require(record.get("source_file_format") == "pdf", "locked row must be PDF", errors)
        require(record.get("source_lock", {}).get("source_anchor_status") == "recorded_private_only", "locked source anchor mismatch", errors)
        require(record.get("source_lock", {}).get("private_value_hash_status") == "recorded_private_only", "locked private hash status mismatch", errors)
        require(quality.get("q4_human_confirmed") is True, "locked row must be Q4 confirmed", errors)
        require(quality.get("q5_calculation_baseline_allowed") is True, "locked row must allow calculation baseline", errors)
        require(record.get("owner_downgrade", {}).get("applied") is False, "locked row downgrade flag mismatch", errors)
    for record in excluded_rows:
        quality = record.get("quality_state", {})
        downgrade = record.get("owner_downgrade", {})
        require(record.get("source_file_format") == "xlsx", "excluded row must be Excel", errors)
        require(record.get("source_lock", {}).get("source_anchor_status") == "pending_downgraded", "excluded source anchor mismatch", errors)
        require(record.get("source_lock", {}).get("private_value_hash_status") == "pending_downgraded", "excluded private hash status mismatch", errors)
        require(quality.get("q4_human_confirmed") is False, "excluded row must not be Q4 confirmed", errors)
        require(quality.get("q5_calculation_baseline_allowed") is False, "excluded row must not allow calculation baseline", errors)
        require(downgrade.get("applied") is True, "excluded downgrade flag mismatch", errors)
        require(downgrade.get("decision_code") == "downgrade_to_cross_source_support", "excluded decision code mismatch", errors)
        require(downgrade.get("q5_exclusion_confirmed") is True, "excluded q5 exclusion mismatch", errors)
        require(downgrade.get("cross_source_support_only") is True, "excluded cross-source support mismatch", errors)

    scope = manifest.get("phase_scope_controls", {})
    require(scope.get("current_phase_only") is True, "current_phase_only must be true", errors)
    require(scope.get("authority_baseline_lock_performed") is True, "authority lock flag must be true", errors)
    require(scope.get("s05_p3_performed") is True, "S05-P3 flag must be true", errors)
    for key in PHASE_SCOPE_FALSE_KEYS:
        require(scope.get(key) is False, f"phase_scope_controls.{key} must be false", errors)

    boundary = manifest.get("raw_data_boundary", {})
    require(boundary.get("raw_inbox_path") == str(RAW_INBOX), "raw inbox path mismatch", errors)
    for key in BOUNDARY_FALSE_KEYS:
        require(boundary.get(key) is False, f"raw_data_boundary.{key} must be false", errors)

    for safety in (manifest.get("public_repo_safety", {}), authority_manifest.get("public_repo_safety", {})):
        for key in PUBLIC_FALSE_KEYS:
            require(safety.get(key) is False, f"public_repo_safety.{key} must be false", errors)

    release = manifest.get("release_state", {})
    require(release.get("current_data_quality_grade") == "Q4", "data quality grade must be Q4 after authority lock", errors)
    require(
        release.get("field_level_calculation_baseline_status")
        == "q5_calculation_baseline_locked_for_40_fields_not_full_q5_quality",
        "field-level baseline status mismatch",
        errors,
    )
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
    require(manifest.get("next_recommended_phase") == "S05-STAGE-REVIEW", "next phase mismatch", errors)
    next_instruction = manifest.get("next_phase_instruction", "")
    for required in ("Stage 5 whole review", "separate run", "Stage 1-18", "GitHub upload"):
        require(required in next_instruction, f"next instruction missing {required!r}", errors)

    for ref in manifest.get("s05_p2_dependency_refs", []):
        check_public_safe_file(Path(ref), errors)
    for ref in manifest.get("evidence_refs", []):
        check_public_safe_file(Path(ref), errors)
    for path in (
        REPORT_PATH,
        TEST_RESULTS_PATH,
        RISK_REGISTER_PATH,
        ROLLBACK_PATH,
        MANIFEST_PATH,
        PUBLIC_AUTHORITY_MANIFEST_PATH,
        PUBLIC_AUTHORITY_RECORDS_PATH,
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
    parser = argparse.ArgumentParser(description="Validate KMFA v0.1.4 S05-P3 authority baseline lock evidence.")
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    args = parser.parse_args(argv)
    try:
        manifest = validate_v014_s05_p3_authority_baseline_lock(args.manifest)
    except ValidationError as exc:
        print("FAIL: KMFA v0.1.4 S05-P3 authority baseline lock validation failed")
        print(exc)
        return 1
    summary = manifest["authority_baseline_summary"]
    print(
        "PASS: KMFA v0.1.4 S05-P3 authority baseline lock validated "
        f"(authority_records={summary['authority_record_count']}, "
        f"q5_calc_locked={summary['q5_calculation_baseline_locked_count']}, "
        f"excluded={summary['excluded_cross_source_support_only_count']}, "
        f"formal_report_allowed={summary['formal_report_allowed_count']}, "
        f"github_upload={str(manifest['github_upload_performed']).lower()})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
