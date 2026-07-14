#!/usr/bin/env python3
"""Validate KMFA v0.1.3 S03-P1 file import register evidence."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

from KMFA.tools.check_v013_s02_stage_review import validate_v013_s02_stage_review
from KMFA.tools.file_import_register import SUPPORTED_EXTENSIONS
from KMFA.tools.v013_s03_p1_file_import_register import (
    CORE_SUPPORTED_EXTENSIONS,
    MANIFEST_PATH,
    RAW_DIR,
    REPORT_PATH,
    REQUIRED_METADATA_FIELDS,
    SCHEMA_VERSION,
    TASK_ID,
    TEST_RESULTS_PATH,
    replay_file_import_register_capability,
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
BOOLEAN_FALSE_KEYS = (
    "raw_dir_read_performed",
    "raw_dir_mutation_performed",
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
    "source_check_matrix_performed",
    "source_priority_performed",
    "stage3_review_performed",
    "github_upload_performed",
    "delivery_allowed",
    "formal_report_allowed",
    "business_decision_basis_allowed",
    "business_execution_allowed",
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


def validate_v013_s03_p1_file_import_register(manifest_path: Path = MANIFEST_PATH) -> dict[str, Any]:
    errors: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    manifest = read_json(manifest_path)
    s02_review = validate_v013_s02_stage_review()
    capability = replay_file_import_register_capability()

    require(manifest.get("schema_version") == SCHEMA_VERSION, "manifest schema mismatch")
    require(manifest.get("project_id") == "KMFA", "project_id mismatch")
    require(manifest.get("version") == "0.1.3", "version mismatch")
    require(manifest.get("stage_id") == "S03", "stage_id must be S03")
    require(manifest.get("phase_id") == "S03-P1", "phase_id must be S03-P1")
    require(manifest.get("phase_scope") == "v013_s03_p1_file_import_register_only", "phase scope mismatch")
    require(manifest.get("task_id") == TASK_ID, "task_id mismatch")
    require(manifest.get("status") == "completed_validated_local_only_no_go_upload_deferred", "status mismatch")
    require(manifest.get("completed_task_ids") == ["S3PAT01", "S3PAT02", "S3PAT03"], "completed task ids mismatch")
    require(manifest.get("s02_stage_review_dependency_validated") is True, "S02 dependency flag must be true")
    require(s02_review.get("stage_id") == "S02", "S02 validator did not return Stage 2")
    require(s02_review.get("phase_results") == {"S02-P1": "PASS", "S02-P2": "PASS", "S02-P3": "PASS"}, "S02 phase results mismatch")
    require(s02_review.get("github_upload_performed") is False, "S02 review upload boundary mismatch")
    require(manifest.get("file_import_register_dependency_validated") is True, "file import dependency must be true")

    supported = manifest.get("supported_registration_extensions", [])
    require(supported == sorted(SUPPORTED_EXTENSIONS), "supported extensions mismatch")
    for suffix in CORE_SUPPORTED_EXTENSIONS:
        require(suffix in supported, f"missing core supported extension: {suffix}")
    require(manifest.get("core_supported_file_type_count") == 5, "core supported type count must be 5")
    require(manifest.get("core_supported_file_types") == CORE_SUPPORTED_EXTENSIONS, "core supported type list mismatch")
    require(manifest.get("synthetic_fixture_count") == capability["synthetic_fixture_count"] == 6, "synthetic fixture count mismatch")
    require(manifest.get("metadata_required_fields") == REQUIRED_METADATA_FIELDS, "required metadata fields mismatch")
    require(manifest.get("metadata_required_fields_validated") is True, "metadata field validation flag must be true")
    require(capability.get("metadata_required_fields_validated") is True, "runtime metadata field validation failed")
    require(manifest.get("safe_zip_extraction_validated") is True, "safe zip extraction flag must be true")
    require(capability.get("safe_zip_extraction_validated") is True, "runtime zip extraction validation failed")
    require(manifest.get("zip_traversal_blocked") is True, "zip traversal must be blocked")
    require(capability.get("zip_traversal_blocked") is True, "runtime zip traversal block failed")
    require(manifest.get("wps_ole_guidance_validated") is True, "WPS/OLE guidance flag must be true")
    require(capability.get("wps_ole_guidance_validated") is True, "runtime WPS/OLE guidance validation failed")

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
    require("S03-P2" in manifest.get("next_required_step", ""), "next step must point to S03-P2")
    require("GitHub upload" in manifest.get("next_required_step", ""), "next step must preserve upload boundary")

    for ref in manifest.get("file_import_register_refs", []):
        require(Path(ref).exists(), f"missing file import dependency ref: {ref}")
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
        "s02_stage_review_dependency_validated": manifest["s02_stage_review_dependency_validated"],
        "file_import_register_dependency_validated": manifest["file_import_register_dependency_validated"],
        "core_supported_file_type_count": manifest["core_supported_file_type_count"],
        "supported_registration_extensions": manifest["supported_registration_extensions"],
        "safe_zip_extraction_validated": manifest["safe_zip_extraction_validated"],
        "zip_traversal_blocked": manifest["zip_traversal_blocked"],
        "metadata_required_fields_validated": manifest["metadata_required_fields_validated"],
        "wps_ole_guidance_validated": manifest["wps_ole_guidance_validated"],
        "raw_dir_read_performed": manifest["raw_dir_read_performed"],
        "raw_dir_mutation_performed": manifest["raw_dir_mutation_performed"],
        "raw_file_bytes_committed": manifest["raw_file_bytes_committed"],
        "raw_filename_publication_allowed": manifest["raw_filename_publication_allowed"],
        "raw_file_hash_publication_allowed": manifest["raw_file_hash_publication_allowed"],
        "business_field_parsing_performed": manifest["business_field_parsing_performed"],
        "raw_value_matching_performed": manifest["raw_value_matching_performed"],
        "github_upload_performed": manifest["github_upload_performed"],
        "delivery_allowed": manifest["delivery_allowed"],
        "current_data_quality_grade": manifest["current_data_quality_grade"],
        "current_report_grade": manifest["current_report_grade"],
        "release_permission": manifest["release_permission"],
        "next_required_step": manifest["next_required_step"],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA v0.1.3 S03-P1 file import register evidence.")
    parser.add_argument("--manifest", default=str(MANIFEST_PATH))
    args = parser.parse_args(argv)
    result = validate_v013_s03_p1_file_import_register(Path(args.manifest))
    print(
        "PASS: KMFA v0.1.3 S03-P1 file import register validator passed "
        f"(core_types={result['core_supported_file_type_count']}, "
        f"zip_traversal_blocked={str(result['zip_traversal_blocked']).lower()}, "
        f"raw_read={str(result['raw_dir_read_performed']).lower()}, "
        f"github_upload={str(result['github_upload_performed']).lower()})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
