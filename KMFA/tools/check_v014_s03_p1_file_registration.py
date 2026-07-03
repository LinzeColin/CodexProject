#!/usr/bin/env python3
"""Validate KMFA v1.4 S03-P1 file registration evidence."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

from KMFA.tools.check_v014_s02_stage_review import validate_v014_s02_stage_review


TASK_ID = "KMFA-V014-S03-P1-FILE-REGISTRATION-20260703"
ACCEPTANCE_ID = "ACC-V014-S03-P1-FILE-REGISTRATION"
RAW_INBOX = "/Users/linzezhang/Downloads/KMFA_MetaData"
MANIFEST_PATH = Path(
    "KMFA/stage_artifacts/V014_S03_P1_FILE_REGISTRATION/machine/s03_p1_file_registration_manifest.json"
)
PUBLIC_REGISTER_PATH = Path("KMFA/metadata/imports/v014_s03_p1_public_raw_file_register.json")
PROTOCOL_PATH = Path("KMFA/metadata/protocol/raw_data_roots_v1_4_s03_p1.json")
REPORT_PATH = Path("KMFA/stage_artifacts/V014_S03_P1_FILE_REGISTRATION/human/s03_p1_completion_record.md")
TEST_RESULTS_PATH = Path("KMFA/stage_artifacts/V014_S03_P1_FILE_REGISTRATION/human/test_results.md")
RISK_REGISTER_PATH = Path("KMFA/stage_artifacts/V014_S03_P1_FILE_REGISTRATION/human/risk_register.md")
ROLLBACK_PATH = Path("KMFA/stage_artifacts/V014_S03_P1_FILE_REGISTRATION/human/rollback_plan.md")
KMFA_GITIGNORE_PATH = Path("KMFA/.gitignore")
FORBIDDEN_EXTENSIONS = {".zip", ".xlsx", ".xls", ".xlsm", ".pdf", ".sqlite", ".sqlite3", ".db"}
PUBLIC_FORBIDDEN_TEXT = (
    "original_filename",
    "relative_path",
    "content_sha256",
    "member_path",
    "sheet_name",
    "source_header_text",
    "raw_value:",
    "normalized_value:",
    "cell_value:",
    "row_value:",
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
PUBLIC_SAFETY_FALSE_KEYS = (
    "raw_business_data_committed",
    "raw_filenames_committed",
    "raw_hashes_committed",
    "directory_tree_plaintext_committed",
    "zip_member_names_committed",
    "field_or_header_plaintext_committed",
    "raw_or_normalized_values_committed",
    "zip_committed",
    "excel_workbook_committed",
    "pdf_committed",
    "private_csv_committed",
    "sqlite_or_db_committed",
    "credentials_committed",
)
NON_SCOPE_FALSE_KEYS = (
    "s03_p2_source_check_matrix_started",
    "s03_p3_source_priority_started",
    "stage3_review_performed",
    "github_upload_performed",
    "raw_value_matching_performed",
    "field_mapping_performed",
    "formal_report_performed",
    "business_execution_performed",
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
        text = path.read_text(encoding="utf-8").lower()
        for forbidden in PUBLIC_FORBIDDEN_TEXT:
            require(forbidden.lower() not in text, f"forbidden public text {forbidden!r} in {path}", errors)


def check_private_manifest_if_present(path_text: str, public_file_count: int, errors: list[str]) -> None:
    path = Path(path_text)
    require(".codex_private_runtime/" in path.as_posix(), "private manifest must be under ignored private runtime", errors)
    if not path.exists():
        return
    value = read_json(path)
    require(value.get("schema_version") == "kmfa.v014_s03_p1.private_raw_file_inventory.v1", "private schema mismatch", errors)
    require(value.get("phase_id") == "S03-P1", "private manifest phase mismatch", errors)
    require(value.get("entry_count") == public_file_count, "private/public entry count mismatch", errors)
    guard = value.get("raw_root_mutation_guard", {})
    require(guard.get("root_stat_unchanged") is True, "private mutation guard must show unchanged root stat", errors)
    entries = value.get("entries")
    require(isinstance(entries, list), "private entries must be list", errors)
    if isinstance(entries, list):
        require(len(entries) == public_file_count, "private entries length mismatch", errors)
        for entry in entries:
            require("relative_path" in entry, "private entry must keep relative_path", errors)
            require(re.fullmatch(r"[a-f0-9]{64}", str(entry.get("content_sha256", ""))) is not None, "private hash missing", errors)


def validate_v014_s03_p1_file_registration(manifest_path: Path = MANIFEST_PATH) -> dict[str, Any]:
    errors: list[str] = []
    manifest = read_json(manifest_path)
    public_register = read_json(PUBLIC_REGISTER_PATH)
    protocol = read_json(PROTOCOL_PATH)
    dependency = validate_v014_s02_stage_review()

    require(manifest.get("schema_version") == "kmfa.v014_s03_p1_file_registration.v1", "schema mismatch", errors)
    require(manifest.get("project_id") == "KMFA", "project_id mismatch", errors)
    require(manifest.get("version") == "0.1.4", "version mismatch", errors)
    require(manifest.get("stage_id") == "S03", "stage_id must be S03", errors)
    require(manifest.get("phase_id") == "S03-P1", "phase_id must be S03-P1", errors)
    require(manifest.get("task_id") == TASK_ID, "task_id mismatch", errors)
    require(manifest.get("acceptance_id") == ACCEPTANCE_ID, "acceptance_id mismatch", errors)
    require(manifest.get("status") == "completed_validated_local_only_no_go_upload_deferred", "status mismatch", errors)
    require(dependency.get("stage_id") == "S02", "dependency did not return S02", errors)
    dependency_manifest = manifest.get("dependency", {})
    require(
        dependency_manifest.get("dependency_manifest")
        == "KMFA/stage_artifacts/V014_S02_STAGE_REVIEW/machine/stage2_review_manifest.json",
        "dependency manifest mismatch",
        errors,
    )

    phase_scope = manifest.get("phase_scope", {})
    require(phase_scope.get("current_phase_only") is True, "current_phase_only must be true", errors)
    require(phase_scope.get("file_registration_only") is True, "file_registration_only must be true", errors)
    require(phase_scope.get("raw_root_read_only_inventory_authorized") is True, "raw inventory authorization missing", errors)
    require(phase_scope.get("safe_zip_extract_capability_in_scope") is True, "safe zip capability missing", errors)
    require(phase_scope.get("safe_zip_extract_performed") is False, "safe zip extraction must not be performed in public run", errors)
    for key in (
        "s03_p2_started",
        "s03_p3_started",
        "stage3_review_performed",
        "github_upload_performed",
        "raw_value_matching_performed",
        "field_mapping_performed",
        "formal_report_performed",
        "business_execution_performed",
        "next_phase_started",
    ):
        require(phase_scope.get(key) is False, f"phase_scope.{key} must be false", errors)
    require(phase_scope.get("next_phase") == "S03-P2", "next phase mismatch", errors)

    raw_status = manifest.get("raw_root_status", {})
    for key in ("read_only_scan_performed", "list_performed", "stat_performed", "hash_performed"):
        require(raw_status.get(key) is True, f"raw_root_status.{key} must be true", errors)
    for key in ("write_performed", "delete_performed", "move_performed", "rename_performed", "overwrite_performed"):
        require(raw_status.get(key) is False, f"raw_root_status.{key} must be false", errors)
    require(raw_status.get("raw_root_path") == RAW_INBOX, "raw inbox path mismatch", errors)
    require(raw_status.get("raw_root_stat_unchanged_after_scan") is True, "raw root stat must remain unchanged", errors)

    public_status = public_register.get("raw_root_status", {})
    require(public_register.get("schema_version") == "kmfa.v014_s03_p1.public_raw_file_register.v1", "public schema mismatch", errors)
    require(public_register.get("phase_id") == "S03-P1", "public phase mismatch", errors)
    require(public_status == raw_status, "public raw root status must match stage manifest", errors)

    summary = manifest.get("scan_summary", {})
    public_summary = public_register.get("scan_summary", {})
    require(summary == public_summary, "scan summary mismatch", errors)
    file_count = summary.get("file_count")
    require(isinstance(file_count, int) and file_count >= 0, "file_count must be non-negative int", errors)
    require(summary.get("supported_file_count", 0) + summary.get("unsupported_file_count", 0) == file_count, "supported/unsupported count mismatch", errors)
    require(isinstance(summary.get("total_size_bytes"), int) and summary.get("total_size_bytes", -1) >= 0, "total size must be int", errors)
    require(isinstance(summary.get("extension_counts"), dict), "extension counts missing", errors)
    require(isinstance(summary.get("file_format_counts"), dict), "format counts missing", errors)

    public_records = public_register.get("public_file_records")
    require(isinstance(public_records, list), "public_file_records must be list", errors)
    if isinstance(public_records, list):
        require(len(public_records) == file_count, "public record count mismatch", errors)
        seen_ids: set[str] = set()
        for record in public_records:
            public_file_id = record.get("public_file_id")
            require(re.fullmatch(r"RAW-FILE-[0-9]{6}", str(public_file_id)) is not None, "bad public_file_id", errors)
            require(public_file_id not in seen_ids, "duplicate public_file_id", errors)
            seen_ids.add(str(public_file_id))
            require(record.get("content_hash_status") == "computed_private_only", "content hash must be private only", errors)
            require(record.get("path_status") == "private_only", "path status must be private only", errors)
            require(record.get("raw_filename_committed") is False, "raw filename must not be committed", errors)
            require(record.get("raw_hash_committed") is False, "raw hash must not be committed", errors)
            require(record.get("field_or_header_plaintext_committed") is False, "field/header plaintext forbidden", errors)
            require(record.get("raw_value_committed") is False, "raw value forbidden", errors)

    for safety in (manifest.get("public_repo_safety", {}), public_register.get("public_repo_safety", {})):
        for key in PUBLIC_SAFETY_FALSE_KEYS:
            require(safety.get(key) is False, f"public_repo_safety.{key} must be false", errors)
    for key in NON_SCOPE_FALSE_KEYS:
        require(public_register.get("non_scope", {}).get(key) is False, f"non_scope.{key} must be false", errors)

    zip_support = manifest.get("safe_zip_support", {})
    require(zip_support.get("safe_zip_extract_supported") is True, "safe zip extraction support missing", errors)
    require(zip_support.get("safe_zip_extract_performed") is False, "safe zip extraction must be false", errors)
    require(zip_support.get("zip_member_names_committed") is False, "zip member names must not be committed", errors)
    require(len(zip_support.get("unsafe_member_policy") or []) == 4, "unsafe member policy count mismatch", errors)

    release = manifest.get("release_state", {})
    for key in (
        "delivery_allowed",
        "formal_report_allowed",
        "business_decision_basis_allowed",
        "business_execution_allowed",
        "github_main_upload_allowed",
    ):
        require(release.get(key) is False, f"release_state.{key} must be false", errors)
    require(release.get("current_go_no_go") == "NO_GO", "Go/No-Go must remain NO_GO", errors)
    require(release.get("current_data_quality_grade") == "Q1", "S03-P1 quality grade must be Q1", errors)
    require(release.get("current_report_grade") == "D", "report grade must remain D", errors)

    require(protocol.get("schema_version") == "kmfa.raw_data_roots.v1_4.s03_p1", "protocol schema mismatch", errors)
    require(protocol.get("stage_phase") == "S03-P1", "protocol phase mismatch", errors)
    require(protocol.get("raw_root", {}) == raw_status, "protocol raw root status mismatch", errors)
    require(protocol.get("forbidden_operations_performed") == [], "forbidden operations must be empty", errors)
    require(".codex_private_runtime/" in KMFA_GITIGNORE_PATH.read_text(encoding="utf-8"), "private runtime missing from gitignore", errors)

    check_private_manifest_if_present(str(manifest.get("private_runtime_ref")), int(file_count or 0), errors)
    for path in (MANIFEST_PATH, PUBLIC_REGISTER_PATH, PROTOCOL_PATH, REPORT_PATH, TEST_RESULTS_PATH, RISK_REGISTER_PATH, ROLLBACK_PATH):
        check_public_safe_file(path, errors)
    for ref in manifest.get("evidence_refs", []):
        check_public_safe_file(Path(ref), errors)

    tracked_files = git_output(["ls-files", "KMFA"]).splitlines()
    forbidden_tracked = [
        path for path in tracked_files if path.lower().endswith(tuple(FORBIDDEN_EXTENSIONS)) or ".codex_private_runtime/" in path
    ]
    require(not forbidden_tracked, f"forbidden tracked raw/private files: {forbidden_tracked}", errors)
    require("codex/kmfa" in git_output(["status", "--short", "--branch"]), "git status must be on codex/kmfa", errors)

    validation = manifest.get("validation_summary", {})
    for key in (
        "s02_stage_review_dependency",
        "v014_s03_p1_validator",
        "focused_unit_test",
        "governance_validator",
        "raw_private_scan",
        "secret_scan",
        "diff_check",
    ):
        require(validation.get(key) in {"PENDING", "PASS"}, f"validation_summary.{key} must be PENDING or PASS", errors)

    if errors:
        raise ValidationError("\n".join(errors))
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA v1.4 S03-P1 file registration evidence.")
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    args = parser.parse_args()
    try:
        manifest = validate_v014_s03_p1_file_registration(args.manifest)
    except ValidationError as exc:
        print("FAIL: KMFA v1.4 S03-P1 validation failed")
        print(exc)
        return 1
    summary = manifest["scan_summary"]
    print(
        "PASS: KMFA v1.4 S03-P1 file registration validated "
        f"(files={summary['file_count']}, supported={summary['supported_file_count']}, "
        f"unsupported={summary['unsupported_file_count']}, raw_write=false, "
        f"github_upload=false, next={manifest['next_recommended_phase']})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
