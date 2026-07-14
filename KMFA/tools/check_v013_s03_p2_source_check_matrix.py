#!/usr/bin/env python3
"""Validate KMFA v0.1.3 S03-P2 source check matrix evidence."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

from KMFA.tools.check_v013_s03_p1_file_import_register import validate_v013_s03_p1_file_import_register
from KMFA.tools.source_check_matrix import ALLOWED_STATUSES, REQUIRED_DIMENSIONS
from KMFA.tools.v013_s03_p1_file_import_register import RAW_DIR
from KMFA.tools.v013_s03_p2_source_check_matrix import (
    MANIFEST_PATH,
    REPORT_PATH,
    SCHEMA_VERSION,
    TASK_ID,
    TEST_RESULTS_PATH,
    replay_source_check_matrix_capability,
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
    "source_check_matrix_rows_committed",
    "source_status_event_rows_committed",
)
BOOLEAN_FALSE_KEYS = (
    "raw_dir_read_performed",
    "raw_dir_mutation_performed",
    "raw_layer_write_allowed",
    "raw_source_mutation_allowed",
    "raw_file_bytes_committed",
    "raw_filename_publication_allowed",
    "raw_file_hash_publication_allowed",
    "source_package_hash_publication_allowed",
    "source_package_storage_ref_publication_allowed",
    "field_plaintext_publication_allowed",
    "sheet_name_publication_allowed",
    "zip_member_name_publication_allowed",
    "row_value_publication_allowed",
    "business_value_publication_allowed",
    "business_field_parsing_performed",
    "raw_value_matching_performed",
    "source_priority_performed",
    "stage3_review_performed",
    "github_upload_performed",
    "delivery_allowed",
    "formal_report_allowed",
    "business_decision_basis_allowed",
    "business_execution_allowed",
    "published_synthetic_matrix_row",
    "published_synthetic_status_event",
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
    "private-synthetic-file-hash-not-published",
    "private-synthetic-package-hash-not-published",
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


def validate_v013_s03_p2_source_check_matrix(manifest_path: Path = MANIFEST_PATH) -> dict[str, Any]:
    errors: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    manifest = read_json(manifest_path)
    s03_p1 = validate_v013_s03_p1_file_import_register()
    capability = replay_source_check_matrix_capability()

    require(manifest.get("schema_version") == SCHEMA_VERSION, "manifest schema mismatch")
    require(manifest.get("project_id") == "KMFA", "project_id mismatch")
    require(manifest.get("version") == "0.1.3", "version mismatch")
    require(manifest.get("stage_id") == "S03", "stage_id must be S03")
    require(manifest.get("phase_id") == "S03-P2", "phase_id must be S03-P2")
    require(manifest.get("phase_scope") == "v013_s03_p2_source_check_matrix_only", "phase scope mismatch")
    require(manifest.get("task_id") == TASK_ID, "task_id mismatch")
    require(manifest.get("status") == "completed_validated_local_only_no_go_upload_deferred", "status mismatch")
    require(manifest.get("completed_task_ids") == ["S3PBT01", "S3PBT02", "S3PBT03"], "completed task ids mismatch")

    require(manifest.get("s03_p1_dependency_validated") is True, "S03-P1 dependency flag must be true")
    require(s03_p1.get("stage_id") == "S03", "S03-P1 validator did not return Stage 3")
    require(s03_p1.get("phase_id") == "S03-P1", "S03-P1 dependency phase mismatch")
    require(s03_p1.get("github_upload_performed") is False, "S03-P1 upload boundary mismatch")
    require(s03_p1.get("raw_dir_read_performed") is False, "S03-P1 raw read boundary mismatch")

    require(manifest.get("source_check_matrix_dependency_validated") is True, "source check dependency must be true")
    require(manifest.get("required_dimensions") == list(REQUIRED_DIMENSIONS), "required dimensions mismatch")
    require(manifest.get("required_dimension_count") == len(REQUIRED_DIMENSIONS) == 6, "required dimension count mismatch")
    require(manifest.get("allowed_statuses") == list(ALLOWED_STATUSES), "allowed statuses mismatch")
    require(manifest.get("allowed_status_count") == len(ALLOWED_STATUSES) == 5, "allowed status count mismatch")
    require(manifest.get("synthetic_matrix_row_count") == capability["synthetic_matrix_row_count"] == 1, "synthetic row count mismatch")
    require(manifest.get("synthetic_status_event_count") == capability["synthetic_status_event_count"] == 1, "synthetic event count mismatch")
    require(
        manifest.get("matrix_row_required_dimensions_validated") is True
        and capability["matrix_row_required_dimensions_validated"] is True,
        "matrix row required dimensions not validated",
    )
    require(
        manifest.get("matrix_row_public_safe_controls_validated") is True
        and capability["matrix_row_public_safe_controls_validated"] is True,
        "matrix row public-safe controls not validated",
    )
    require(
        manifest.get("metadata_status_event_validated") is True
        and capability["metadata_status_event_validated"] is True,
        "metadata status event not validated",
    )
    require(
        manifest.get("status_change_append_only") is True and capability["status_change_append_only"] is True,
        "status change must be append-only",
    )
    require(
        manifest.get("status_change_target_layer") == capability["status_change_target_layer"] == "metadata",
        "status change target layer mismatch",
    )
    require(manifest.get("status_event_private_temp_write_only") is True, "status event replay must be temp-only")

    raw_boundary = manifest.get("raw_data_boundary", {})
    require(raw_boundary.get("local_raw_data_dir") == RAW_DIR, "raw directory mismatch")
    require(raw_boundary.get("codex_read_allowed_only_when_phase_requires") is True, "raw read policy mismatch")
    require(raw_boundary.get("codex_read_performed_by_this_phase") is False, "raw read performed flag must be false")
    require(raw_boundary.get("codex_modify_allowed") is False, "raw modify allowed must be false")
    require(raw_boundary.get("codex_delete_allowed") is False, "raw delete allowed must be false")
    require(raw_boundary.get("codex_move_allowed") is False, "raw move allowed must be false")
    require(raw_boundary.get("codex_rename_allowed") is False, "raw rename allowed must be false")
    require(raw_boundary.get("codex_overwrite_allowed") is False, "raw overwrite allowed must be false")
    require(raw_boundary.get("codex_generate_inside_allowed") is False, "raw generate-inside allowed must be false")
    require(raw_boundary.get("github_commit_allowed") is False, "raw GitHub commit allowed must be false")

    for key in BOOLEAN_FALSE_KEYS:
        require(manifest.get(key) is False, f"{key} must be false")
    safety = manifest.get("public_repo_safety", {})
    for key in PUBLIC_SAFETY_FALSE_KEYS:
        require(safety.get(key) is False, f"public_repo_safety.{key} must be false")

    require(manifest.get("current_data_quality_grade") == "Q2", "quality grade mismatch")
    require(manifest.get("current_report_grade") == "D", "report grade mismatch")
    require(manifest.get("release_permission") == "blocked", "release permission mismatch")
    require("S03-P3" in manifest.get("next_required_step", ""), "next step must point to S03-P3")
    require("GitHub upload" in manifest.get("next_required_step", ""), "next step must preserve upload boundary")

    for ref in manifest.get("source_check_matrix_refs", []):
        require(Path(ref).exists(), f"missing source check dependency ref: {ref}")
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
        "status": manifest["status"],
        "s03_p1_dependency_validated": manifest["s03_p1_dependency_validated"],
        "source_check_matrix_dependency_validated": manifest["source_check_matrix_dependency_validated"],
        "required_dimensions": manifest["required_dimensions"],
        "required_dimension_count": manifest["required_dimension_count"],
        "allowed_statuses": manifest["allowed_statuses"],
        "allowed_status_count": manifest["allowed_status_count"],
        "metadata_status_event_validated": manifest["metadata_status_event_validated"],
        "status_change_append_only": manifest["status_change_append_only"],
        "status_change_target_layer": manifest["status_change_target_layer"],
        "raw_dir_read_performed": manifest["raw_dir_read_performed"],
        "raw_dir_mutation_performed": manifest["raw_dir_mutation_performed"],
        "raw_layer_write_allowed": manifest["raw_layer_write_allowed"],
        "raw_source_mutation_allowed": manifest["raw_source_mutation_allowed"],
        "raw_filename_publication_allowed": manifest["raw_filename_publication_allowed"],
        "raw_file_hash_publication_allowed": manifest["raw_file_hash_publication_allowed"],
        "business_field_parsing_performed": manifest["business_field_parsing_performed"],
        "raw_value_matching_performed": manifest["raw_value_matching_performed"],
        "source_priority_performed": manifest["source_priority_performed"],
        "stage3_review_performed": manifest["stage3_review_performed"],
        "github_upload_performed": manifest["github_upload_performed"],
        "delivery_allowed": manifest["delivery_allowed"],
        "current_data_quality_grade": manifest["current_data_quality_grade"],
        "current_report_grade": manifest["current_report_grade"],
        "release_permission": manifest["release_permission"],
        "next_required_step": manifest["next_required_step"],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA v0.1.3 S03-P2 source check matrix evidence.")
    parser.add_argument("--manifest", default=str(MANIFEST_PATH))
    args = parser.parse_args(argv)
    result = validate_v013_s03_p2_source_check_matrix(Path(args.manifest))
    print(
        "PASS: KMFA v0.1.3 S03-P2 source check matrix validator passed "
        f"(dimensions={result['required_dimension_count']}, "
        f"statuses={result['allowed_status_count']}, "
        f"metadata_event={str(result['metadata_status_event_validated']).lower()}, "
        f"raw_read={str(result['raw_dir_read_performed']).lower()}, "
        f"github_upload={str(result['github_upload_performed']).lower()})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
