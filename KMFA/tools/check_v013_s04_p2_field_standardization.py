#!/usr/bin/env python3
"""Validate KMFA v0.1.3 S04-P2 field standardization replay evidence."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

from KMFA.tools.check_v013_s04_p1_amount_precision import validate_v013_s04_p1_amount_precision
from KMFA.tools.v013_s03_p1_file_import_register import RAW_DIR
from KMFA.tools.v013_s04_p2_field_standardization import (
    ALIAS_DICTIONARY_PATH,
    FIELD_POLICY_PATH,
    FIELD_QUALITY_PROTOCOL_PATH,
    MANIFEST_PATH,
    REPORT_PATH,
    SCHEMA_VERSION,
    TASK_ID,
    TEST_RESULTS_PATH,
    replay_field_standardization_capability,
)


BOOLEAN_FALSE_KEYS = (
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


def validate_v013_s04_p2_field_standardization(manifest_path: Path = MANIFEST_PATH) -> dict[str, Any]:
    errors: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    manifest = read_json(manifest_path)
    s04_p1 = validate_v013_s04_p1_amount_precision()
    replay = replay_field_standardization_capability()

    require(manifest.get("schema_version") == SCHEMA_VERSION, "manifest schema mismatch")
    require(manifest.get("project_id") == "KMFA", "project_id mismatch")
    require(manifest.get("version") == "0.1.3", "version mismatch")
    require(manifest.get("stage_id") == "S04", "stage_id must be S04")
    require(manifest.get("phase_id") == "S04-P2", "phase_id must be S04-P2")
    require(
        manifest.get("phase_scope") == "v013_s04_p2_field_standardization_replay_only",
        "phase scope mismatch",
    )
    require(manifest.get("task_id") == TASK_ID, "task_id mismatch")
    require(manifest.get("status") == "completed_validated_local_only_no_go_upload_deferred", "status mismatch")
    require(manifest.get("completed_task_ids") == ["S4PBT01", "S4PBT02", "S4PBT03"], "completed task ids mismatch")

    require(s04_p1.get("phase_id") == "S04-P1", "S04-P1 dependency did not return phase S04-P1")
    require(s04_p1.get("github_upload_performed") is False, "S04-P1 upload boundary mismatch")
    require(manifest.get("s04_p1_dependency_validated") is True, "S04-P1 dependency must be true")

    require(manifest.get("field_standardization_dependency_validated") is True, "field dependency must be true")
    require(manifest.get("canonical_fields") == replay["canonical_fields"], "canonical fields mismatch")
    require(manifest.get("canonical_field_count") == replay["canonical_field_count"] == 6, "canonical field count mismatch")
    require(
        manifest.get("alias_dictionary_row_count") == replay["alias_dictionary_row_count"],
        "alias dictionary row count mismatch",
    )
    require(manifest.get("alias_dictionary_row_count", 0) >= 30, "alias dictionary row count too low")
    require(manifest.get("mapping_record_count") == replay["mapping_record_count"] == 6, "mapping record count mismatch")
    require(manifest.get("mapping_records_public_safe") is True, "mapping records must be public-safe")
    require(manifest.get("standardization_case_count") == replay["standardization_case_count"] == 6, "case count mismatch")
    require(
        manifest.get("standardization_case_passed_count") == replay["standardization_case_passed_count"] == 6,
        "case pass count mismatch",
    )
    require(
        manifest.get("standardization_case_results") == replay["standardization_case_results"],
        "standardization replay mismatch",
    )
    require(manifest.get("quality_status_count") == replay["quality_status_count"] == 5, "quality status count mismatch")
    require(
        manifest.get("quality_status_issue_types") == ["invalid_field_value", "missing_required_field"],
        "quality status issue type mismatch",
    )
    require(manifest.get("quality_statuses_public_safe") is True, "quality statuses must be public-safe")
    require(manifest.get("quality_passed_for_complete_synthetic_row") is True, "complete synthetic row must pass")
    require(manifest.get("quality_passed_for_incomplete_synthetic_row") is False, "incomplete synthetic row must fail")

    raw_boundary = manifest.get("raw_data_boundary", {})
    require(raw_boundary.get("local_raw_data_dir") == RAW_DIR, "raw directory mismatch")
    require(raw_boundary.get("codex_read_required_by_this_phase") is False, "raw read required flag must be false")
    require(raw_boundary.get("codex_accidental_listing_performed_by_this_run") is True, "raw listing deviation must be recorded")
    require(raw_boundary.get("codex_accidental_listing_temp_files_removed") is True, "raw listing temp cleanup must be recorded")
    require(raw_boundary.get("codex_modify_allowed") is False, "raw modify allowed must be false")
    require(raw_boundary.get("codex_delete_allowed") is False, "raw delete allowed must be false")
    require(raw_boundary.get("codex_move_allowed") is False, "raw move allowed must be false")
    require(raw_boundary.get("codex_rename_allowed") is False, "raw rename allowed must be false")
    require(raw_boundary.get("codex_overwrite_allowed") is False, "raw overwrite allowed must be false")
    require(raw_boundary.get("codex_generate_inside_allowed") is False, "raw generate-inside allowed must be false")
    require(raw_boundary.get("github_commit_allowed") is False, "raw GitHub commit allowed must be false")
    require(manifest.get("raw_dir_read_required") is False, "raw read required must be false")
    require(manifest.get("raw_dir_accidental_listing_performed") is True, "raw listing deviation must be true")
    require(manifest.get("raw_dir_accidental_listing_temp_files_removed") is True, "raw listing temp cleanup must be true")

    for key in BOOLEAN_FALSE_KEYS:
        require(manifest.get(key) is False, f"{key} must be false")
    safety = manifest.get("public_repo_safety", {})
    for key in PUBLIC_SAFETY_FALSE_KEYS:
        require(safety.get(key) is False, f"public_repo_safety.{key} must be false")

    require(manifest.get("current_data_quality_grade") == "Q2", "quality grade mismatch")
    require(manifest.get("current_report_grade") == "D", "report grade mismatch")
    require(manifest.get("release_permission") == "blocked", "release permission mismatch")
    require("S04-P3" in manifest.get("next_required_step", ""), "next step must point to S04-P3")
    require("GitHub upload" in manifest.get("next_required_step", ""), "next step must preserve upload boundary")

    for ref in manifest.get("field_standardization_refs", []):
        require(Path(ref).exists(), f"missing field standardization ref: {ref}")
    for ref in manifest.get("evidence_refs", []):
        require(Path(ref).exists(), f"missing evidence ref: {ref}")
    for ref in (ALIAS_DICTIONARY_PATH, FIELD_POLICY_PATH, FIELD_QUALITY_PROTOCOL_PATH):
        require(ref.exists(), f"missing field dependency file: {ref}")
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
        "status": manifest["status"],
        "s04_p1_dependency_validated": manifest["s04_p1_dependency_validated"],
        "field_standardization_dependency_validated": manifest["field_standardization_dependency_validated"],
        "canonical_field_count": manifest["canonical_field_count"],
        "alias_dictionary_row_count": manifest["alias_dictionary_row_count"],
        "standardization_case_count": manifest["standardization_case_count"],
        "standardization_case_passed_count": manifest["standardization_case_passed_count"],
        "quality_status_count": manifest["quality_status_count"],
        "raw_dir_read_required": manifest["raw_dir_read_required"],
        "raw_dir_accidental_listing_performed": manifest["raw_dir_accidental_listing_performed"],
        "raw_dir_accidental_listing_temp_files_removed": manifest["raw_dir_accidental_listing_temp_files_removed"],
        "raw_dir_mutation_performed": manifest["raw_dir_mutation_performed"],
        "raw_filename_publication_allowed": manifest["raw_filename_publication_allowed"],
        "field_plaintext_publication_allowed": manifest["field_plaintext_publication_allowed"],
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
    parser = argparse.ArgumentParser(description="Validate KMFA v0.1.3 S04-P2 field standardization evidence.")
    parser.add_argument("--manifest", default=str(MANIFEST_PATH))
    args = parser.parse_args(argv)
    result = validate_v013_s04_p2_field_standardization(Path(args.manifest))
    print(
        "PASS: KMFA v0.1.3 S04-P2 field standardization validator passed "
        f"(canonical_fields={result['canonical_field_count']}, "
        f"aliases={result['alias_dictionary_row_count']}, "
        f"cases={result['standardization_case_passed_count']}/{result['standardization_case_count']}, "
        f"quality_statuses={result['quality_status_count']}, "
        f"raw_mutation={str(result['raw_dir_mutation_performed']).lower()}, "
        f"github_upload={str(result['github_upload_performed']).lower()})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
