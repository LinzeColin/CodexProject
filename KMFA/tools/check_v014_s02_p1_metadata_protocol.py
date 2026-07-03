#!/usr/bin/env python3
"""Validate KMFA v1.4 S02-P1 metadata protocol evidence."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from KMFA.tools import metadata_protocol_check
from KMFA.tools.check_v014_s01_stage_review import validate_v014_s01_stage_review


MANIFEST_PATH = Path(
    "KMFA/stage_artifacts/V014_S02_P1_METADATA_PROTOCOL/machine/"
    "s02_p1_metadata_protocol_manifest.json"
)
COMPLETION_RECORD_PATH = Path("KMFA/stage_artifacts/V014_S02_P1_METADATA_PROTOCOL/human/s02_p1_completion_record.md")
TEST_RESULTS_PATH = Path("KMFA/stage_artifacts/V014_S02_P1_METADATA_PROTOCOL/human/test_results.md")
RISK_REGISTER_PATH = Path("KMFA/stage_artifacts/V014_S02_P1_METADATA_PROTOCOL/human/risk_register.md")
ROLLBACK_PATH = Path("KMFA/stage_artifacts/V014_S02_P1_METADATA_PROTOCOL/human/rollback_plan.md")
RAW_ROOTS_POLICY_PATH = Path("KMFA/metadata/protocol/raw_data_roots_v1_4.json")
METADATA_PROTOCOL_PATH = Path("KMFA/metadata/protocol/metadata_protocol.yaml")
DIRECTORY_MANIFEST_PATH = Path("KMFA/metadata/protocol/directory_manifest.json")
KMFA_GITIGNORE_PATH = Path("KMFA/.gitignore")
EXPECTED_REQUIRED_DIRS = [
    "metadata/sources",
    "metadata/imports",
    "metadata/schema_maps",
    "metadata/quality",
    "metadata/lineage",
    "metadata/reports",
    "metadata/approvals",
]
EXPECTED_IDENTIFIERS = [
    "import_run_id",
    "source_id",
    "file_hash",
    "formula_version",
    "mapping_version",
]
FORBIDDEN_EXTENSIONS = {".zip", ".xlsx", ".xls", ".xlsm", ".pdf", ".sqlite", ".sqlite3", ".db"}
FORBIDDEN_TEXT = (
    "raw_value:",
    "normalized_value:",
    "source_header_text:",
    "original_filename",
    "member_path",
    "member_name",
    "sheet_name:",
    "row_value:",
    "cell_value:",
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
FALSE_BOUNDARY_KEYS = (
    "raw_inbox_read_by_this_phase",
    "raw_inbox_listed_by_this_phase",
    "raw_inbox_modified_by_this_phase",
    "raw_inbox_deleted_by_this_phase",
    "raw_inbox_moved_by_this_phase",
    "raw_inbox_renamed_by_this_phase",
    "raw_inbox_overwritten_by_this_phase",
    "raw_inbox_written_by_this_phase",
    "raw_inventory_performed",
    "raw_payload_extracted_from_delivery_zip",
    "raw_filenames_committed",
    "raw_hashes_committed",
    "field_or_header_plaintext_committed",
    "business_values_committed",
    "zip_committed",
    "excel_workbook_committed",
    "pdf_committed",
    "private_csv_committed",
    "sqlite_or_db_committed",
    "credentials_committed",
)
PHASE_SCOPE_FALSE_KEYS = (
    "s02_p2_started",
    "s02_p3_started",
    "stage2_review_performed",
    "github_upload_performed",
    "raw_inventory_performed",
    "raw_value_matching_performed",
    "formal_report_performed",
    "business_execution_performed",
    "next_phase_started",
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
    "field_plaintext_committed",
    "normalized_business_values_committed",
)
CODE_OR_TEST_EVIDENCE = {
    Path("KMFA/tools/check_v014_s02_p1_metadata_protocol.py"),
    Path("KMFA/tests/test_v014_s02_p1_metadata_protocol.py"),
    Path("KMFA/tools/metadata_protocol_check.py"),
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


def check_public_safe_file(path: Path, errors: list[str]) -> None:
    require(path.exists(), f"missing evidence file: {path}", errors)
    if not path.exists():
        return
    require(path.suffix.lower() not in FORBIDDEN_EXTENSIONS, f"forbidden evidence extension: {path}", errors)
    if path in CODE_OR_TEST_EVIDENCE:
        return
    if path.suffix.lower() in {".md", ".json", ".jsonl", ".csv", ".yaml", ".yml"}:
        text = path.read_text(encoding="utf-8").lower()
        for forbidden in FORBIDDEN_TEXT:
            require(forbidden.lower() not in text, f"forbidden evidence text {forbidden!r} in {path}", errors)


def run_existing_metadata_protocol_check(errors: list[str]) -> None:
    try:
        metadata_protocol_check.check_required_paths()
        metadata_protocol_check.check_identifier_protocol()
        metadata_protocol_check.check_jsonl_and_csv_files()
        metadata_protocol_check.check_manifest_alignment()
        metadata_protocol_check.check_privacy_boundary()
    except SystemExit as exc:
        errors.append(f"metadata_protocol_check failed with exit={exc.code}")


def check_metadata_protocol_files(errors: list[str]) -> None:
    protocol = read_json(METADATA_PROTOCOL_PATH)
    manifest = read_json(DIRECTORY_MANIFEST_PATH)
    require(protocol.get("project_id") == "KMFA", "metadata protocol project mismatch", errors)
    require(protocol.get("stage_phase") == "S02-P1", "metadata protocol stage_phase must remain S02-P1", errors)
    identifiers = protocol.get("identifiers")
    require(isinstance(identifiers, dict), "metadata identifiers must be object", errors)
    if isinstance(identifiers, dict):
        require(list(identifiers.keys()) == EXPECTED_IDENTIFIERS, "metadata identifier order/content mismatch", errors)
    policy = protocol.get("metadata_storage_policy")
    require(isinstance(policy, dict), "metadata storage policy missing", errors)
    if isinstance(policy, dict):
        require(
            policy.get("public_repo_sensitive_plaintext_allowed") is False,
            "sensitive plaintext must be forbidden in public repo",
            errors,
        )
    require(set(manifest.get("directories") or []) >= set(EXPECTED_REQUIRED_DIRS), "directory manifest missing required dirs", errors)
    require(manifest.get("raw_sensitive_data_public_repo_allowed") is False, "raw sensitive data must be forbidden", errors)
    require(manifest.get("business_records_committed") is False, "business records must not be committed", errors)


def check_raw_roots_policy(errors: list[str]) -> None:
    policy = read_json(RAW_ROOTS_POLICY_PATH)
    require(policy.get("schema_version") == "kmfa.raw_data_roots.v1_4", "raw roots schema mismatch", errors)
    require(policy.get("stage_phase") == "S02-P1", "raw roots stage_phase mismatch", errors)
    raw_roots = policy.get("raw_roots")
    require(isinstance(raw_roots, list) and len(raw_roots) == 1, "raw roots policy must contain one public-safe root", errors)
    if isinstance(raw_roots, list) and raw_roots:
        root = raw_roots[0]
        require(root.get("path") == "/Users/linzezhang/Downloads/KMFA_MetaData", "raw root path mismatch", errors)
        require(root.get("access_policy") == "read_only_when_phase_authorized", "raw root access policy mismatch", errors)
        for key in (
            "current_phase_read_performed",
            "current_phase_list_performed",
            "current_phase_mutation_performed",
            "current_phase_inventory_performed",
        ):
            require(root.get(key) is False, f"raw roots {key} must be false", errors)
    runtime = policy.get("private_runtime_policy", {})
    require(runtime.get("preferred_project_runtime") == "KMFA/.codex_private_runtime/", "private runtime path mismatch", errors)
    require(runtime.get("git_ignore_required") is True, "private runtime git ignore must be required", errors)
    require(runtime.get("public_repo_private_runtime_commit_allowed") is False, "private runtime commit must be forbidden", errors)
    phase = policy.get("phase_boundary", {})
    require(phase.get("s02_p1_protocol_only") is True, "raw roots phase must be protocol only", errors)
    for key in PHASE_SCOPE_FALSE_KEYS:
        if key in phase:
            require(phase.get(key) is False, f"raw roots phase_boundary.{key} must be false", errors)
    require(KMFA_GITIGNORE_PATH.exists(), "KMFA/.gitignore missing", errors)
    if KMFA_GITIGNORE_PATH.exists():
        require(".codex_private_runtime/" in KMFA_GITIGNORE_PATH.read_text(encoding="utf-8"), "private runtime not git-ignored", errors)


def validate_v014_s02_p1_metadata_protocol(manifest_path: Path = MANIFEST_PATH) -> dict[str, Any]:
    errors: list[str] = []
    manifest = read_json(manifest_path)
    dependency = validate_v014_s01_stage_review()
    run_existing_metadata_protocol_check(errors)
    check_metadata_protocol_files(errors)
    check_raw_roots_policy(errors)

    require(manifest.get("schema_version") == "kmfa.v014_s02_p1_metadata_protocol.v1", "schema mismatch", errors)
    require(manifest.get("project_id") == "KMFA", "project_id mismatch", errors)
    require(manifest.get("version") == "0.1.4", "version mismatch", errors)
    require(manifest.get("stage_id") == "S02", "stage_id must be S02", errors)
    require(manifest.get("phase_id") == "S02-P1", "phase_id must be S02-P1", errors)
    require(manifest.get("task_id") == "KMFA-V014-S02-P1-METADATA-PROTOCOL-20260703", "task_id mismatch", errors)
    require(manifest.get("acceptance_id") == "ACC-V014-S02-P1-METADATA-PROTOCOL", "acceptance_id mismatch", errors)
    require(manifest.get("status") == "completed_validated_local_only_no_go_upload_deferred", "status mismatch", errors)
    require(dependency.get("stage_id") == "S01", "Stage 1 dependency did not return S01", errors)

    manifest_dependency = manifest.get("dependency", {})
    require(
        manifest_dependency.get("dependency_manifest")
        == "KMFA/stage_artifacts/V014_S01_STAGE_REVIEW/machine/stage1_review_manifest.json",
        "dependency manifest mismatch",
        errors,
    )
    require(
        manifest_dependency.get("dependency_expected_status")
        == "review_passed_local_only_no_go_upload_deferred_until_v014_stage1_18_complete",
        "dependency expected status mismatch",
        errors,
    )

    phase_scope = manifest.get("phase_scope", {})
    require(phase_scope.get("current_phase_only") is True, "current_phase_only must be true", errors)
    require(phase_scope.get("metadata_protocol_only") is True, "metadata_protocol_only must be true", errors)
    require(phase_scope.get("next_phase") == "S02-P2", "next phase must be S02-P2", errors)
    for key in PHASE_SCOPE_FALSE_KEYS:
        require(phase_scope.get(key) is False, f"phase_scope.{key} must be false", errors)

    metadata = manifest.get("metadata_protocol", {})
    require(metadata.get("required_directories") == EXPECTED_REQUIRED_DIRS, "required metadata dirs mismatch", errors)
    require(metadata.get("protocol_directory") == "metadata/protocol", "protocol directory mismatch", errors)
    require(metadata.get("required_identifiers") == EXPECTED_IDENTIFIERS, "required identifiers mismatch", errors)
    require(
        metadata.get("metadata_storage_policy_public_repo_sensitive_plaintext_allowed") is False,
        "public repo sensitive plaintext flag must be false",
        errors,
    )
    require(metadata.get("business_records_committed") is False, "business records flag must be false", errors)
    require(metadata.get("raw_data_roots_policy") == str(RAW_ROOTS_POLICY_PATH), "raw roots policy ref mismatch", errors)

    raw_boundary = manifest.get("raw_data_boundary", {})
    require(raw_boundary.get("raw_inbox_path") == "/Users/linzezhang/Downloads/KMFA_MetaData", "raw inbox path mismatch", errors)
    for key in FALSE_BOUNDARY_KEYS:
        require(raw_boundary.get(key) is False, f"raw_data_boundary.{key} must be false", errors)

    safety = manifest.get("public_repo_safety", {})
    for key in PUBLIC_SAFETY_FALSE_KEYS:
        require(safety.get(key) is False, f"public_repo_safety.{key} must be false", errors)

    release = manifest.get("release_state", {})
    for key in (
        "delivery_allowed",
        "formal_report_allowed",
        "business_decision_basis_allowed",
        "business_execution_allowed",
        "github_main_upload_allowed",
    ):
        require(release.get(key) is False, f"release_state.{key} must be false", errors)
    require(release.get("current_go_no_go") == "NO_GO", "current Go/No-Go must be NO_GO", errors)
    require(release.get("current_report_grade") == "D", "current report grade must be D", errors)
    require(release.get("release_permission") == "blocked", "release permission must be blocked", errors)

    for ref in manifest.get("evidence_refs", []):
        check_public_safe_file(Path(ref), errors)
    for path in (COMPLETION_RECORD_PATH, TEST_RESULTS_PATH, RISK_REGISTER_PATH, ROLLBACK_PATH, MANIFEST_PATH, RAW_ROOTS_POLICY_PATH):
        check_public_safe_file(path, errors)

    status = git_output(["status", "--short", "--branch"])
    require("codex/kmfa" in status, "git status must be on codex/kmfa", errors)

    if errors:
        raise ValidationError("\n".join(errors))
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA v1.4 S02-P1 metadata protocol evidence.")
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    args = parser.parse_args()
    try:
        manifest = validate_v014_s02_p1_metadata_protocol(args.manifest)
    except ValidationError as exc:
        print("FAIL: KMFA v1.4 S02-P1 metadata protocol validation failed")
        print(exc)
        return 1
    metadata = manifest["metadata_protocol"]
    print(
        "PASS: KMFA v1.4 S02-P1 metadata protocol validated "
        f"(dirs={len(metadata['required_directories'])}, identifiers={len(metadata['required_identifiers'])}, "
        f"raw_inventory={str(manifest['phase_scope']['raw_inventory_performed']).lower()}, "
        f"github_upload={str(manifest['phase_scope']['github_upload_performed']).lower()}, "
        f"next={manifest['next_recommended_phase']}, go_no_go={manifest['release_state']['current_go_no_go']})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
