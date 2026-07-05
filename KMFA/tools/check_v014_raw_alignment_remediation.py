#!/usr/bin/env python3
"""Validate KMFA v0.1.4 raw alignment remediation evidence."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from KMFA.tools.v014_raw_alignment_remediation import (  # noqa: E402
    ACCEPTANCE_ID,
    GO_NO_GO_PATH,
    GO_NO_GO_RECORD_PATH,
    MANIFEST_PATH,
    METADATA_GO_NO_GO_PATH,
    METADATA_MANIFEST_PATH,
    PHASE_ID,
    PRIVATE_DIAGNOSTIC_PATH,
    PRIVATE_SCHEMA_VERSION,
    REPORT_PATH,
    RISK_REGISTER_PATH,
    ROLLBACK_PATH,
    SCHEMA_VERSION,
    STATUS,
    TASK_ID,
    TEST_RESULTS_PATH,
)


FORBIDDEN_PUBLIC_TEXT = (
    "actual_package_sha256",
    "expected_package_sha256",
    "member_sha256",
    "member_name_sha256",
    "member_name:",
    "raw_path",
    "raw_root_path",
    "sheet_name:",
    "raw_value:",
    "normalized_value:",
    "source_header_text:",
    "cell_value:",
    "row_value:",
    "business_value:",
    "project_name_plaintext",
    "customer_name_plaintext",
    "counterparty_plaintext",
    "company_entity_plaintext",
    "supplier_name_plaintext",
    "account_number:",
    "invoice_number:",
    "tax_identifier:",
    "private_ref://",
    "connector_" + "token:",
    "connector_" + "pass" + "word:",
    "api" + "_key:",
    "private" + "_key:",
    "-----" "BEGIN",
    "s" "k-",
    "KMFA" "_MetaData",
    "/Users/linzezhang/Downloads",
    ".xlsx",
    ".xls",
    ".zip",
    ".pdf",
    ".sqlite",
    ".db",
)
STRICT_SECRET_PATTERNS = (
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"(?i)(password|passwd|secret|api" + r"_key|token)\s*=\s*[^\s,;]{8,}"),
)
FORBIDDEN_TRACKED_SUFFIXES = (
    ".zip",
    ".xlsx",
    ".xls",
    ".xlsm",
    ".pdf",
    ".sqlite",
    ".sqlite3",
    ".sqlite-shm",
    ".sqlite-wal",
    ".db",
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


def check_public_evidence_text(path: Path, errors: list[str]) -> None:
    require(path.exists(), f"missing public evidence: {path}", errors)
    if not path.exists():
        return
    text = path.read_text(encoding="utf-8", errors="ignore")
    lower = text.lower()
    for forbidden in FORBIDDEN_PUBLIC_TEXT:
        require(forbidden.lower() not in lower, f"forbidden public evidence text {forbidden!r} in {path}", errors)
    for pattern in STRICT_SECRET_PATTERNS:
        require(pattern.search(text) is None, f"secret-like token found in {path}: {pattern.pattern}", errors)


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
    require(diagnostic.get("schema_version") == PRIVATE_SCHEMA_VERSION, "private diagnostic schema mismatch", errors)
    require(
        diagnostic.get("classification") == "private_raw_diagnostic_do_not_commit",
        "private diagnostic classification mismatch",
        errors,
    )
    require("actual_package_sha256" in diagnostic, "private diagnostic missing actual package hash", errors)
    require("expected_package_sha256" in diagnostic, "private diagnostic missing expected package hash", errors)
    require(
        diagnostic.get("raw_root_before") == diagnostic.get("raw_root_after"),
        "private diagnostic raw root stat changed",
        errors,
    )
    require(
        diagnostic.get("selected_source_before") == diagnostic.get("selected_source_after"),
        "private diagnostic selected source stat changed",
        errors,
    )
    member_records = diagnostic.get("member_records")
    require(isinstance(member_records, list), "private member_records must be list", errors)
    if isinstance(member_records, list):
        business_records = [item for item in member_records if not item.get("hidden_or_system")]
        require(len(business_records) == 9, "private business member hash count mismatch", errors)
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


def validate_v014_raw_alignment_remediation(
    manifest_path: Path = MANIFEST_PATH,
    *,
    require_private_diagnostic: bool = False,
) -> dict[str, Any]:
    errors: list[str] = []
    manifest = read_json(manifest_path)
    metadata_manifest = read_json(METADATA_MANIFEST_PATH)
    go_no_go = read_json(GO_NO_GO_PATH)
    metadata_go_no_go = read_json(METADATA_GO_NO_GO_PATH)

    require(metadata_manifest == manifest, "metadata manifest copy mismatch", errors)
    require(metadata_go_no_go == go_no_go, "metadata go/no-go copy mismatch", errors)
    require(manifest.get("schema_version") == SCHEMA_VERSION, "schema mismatch", errors)
    require(manifest.get("project_id") == "KMFA", "project_id mismatch", errors)
    require(manifest.get("version") == "0.1.4", "version mismatch", errors)
    require(manifest.get("phase_id") == PHASE_ID, "phase_id mismatch", errors)
    require(manifest.get("task_id") == TASK_ID, "task_id mismatch", errors)
    require(manifest.get("acceptance_ids") == [ACCEPTANCE_ID], "acceptance ids mismatch", errors)
    require(manifest.get("status") == STATUS, "status mismatch", errors)

    scope = manifest.get("phase_scope_controls", {})
    for key in (
        "current_phase_only",
        "raw_source_identity_remediation_only",
        "raw_root_read_only_hash_authorized",
    ):
        require(scope.get(key) is True, f"phase_scope_controls.{key} must be true", errors)
    for key in (
        "public_hash_backfill_performed",
        "lineage_full_check_performed",
        "formal_report_performed",
        "github_upload_performed",
        "app_reinstall_performed",
        "business_execution_performed",
        "next_phase_started",
    ):
        require(scope.get(key) is False, f"phase_scope_controls.{key} must be false", errors)

    raw = manifest.get("raw_source_identity_summary", {})
    require(raw.get("raw_root_exists") is True, "raw root must exist", errors)
    require(raw.get("raw_root_is_readable") is True, "raw root must be readable", errors)
    require(raw.get("raw_root_file_count") == 5, "raw root file count mismatch", errors)
    require(raw.get("raw_root_archive_count") == 3, "raw archive count mismatch", errors)
    require(raw.get("raw_root_spreadsheet_count") == 2, "raw spreadsheet count mismatch", errors)
    require(raw.get("selected_candidate_count") == 1, "selected candidate count mismatch", errors)
    require(raw.get("selected_archive_openable") is True, "selected archive must be openable", errors)
    require(raw.get("business_member_count") == 9, "business member count mismatch", errors)
    require(raw.get("business_document_member_count") == 8, "business document member count mismatch", errors)
    require(raw.get("business_spreadsheet_member_count") == 1, "business spreadsheet member count mismatch", errors)
    require(isinstance(raw.get("hidden_or_system_member_count"), int), "hidden/system member count must be int", errors)
    require(raw.get("business_shape_matches_expected_a0") is True, "business shape must match expected A0", errors)
    require(raw.get("package_hash_matches_registered") is False, "package hash match must be false", errors)
    require(raw.get("package_size_matches_registered") is False, "package size match must be false", errors)
    require(raw.get("private_member_hashes_recorded") is True, "private member hashes must be recorded", errors)
    require(raw.get("public_member_hash_backfill_allowed") is False, "public member hash backfill must be blocked", errors)
    require(raw.get("raw_alignment_complete") is False, "raw alignment must remain incomplete", errors)
    require(
        raw.get("remediation_status")
        == "container_mismatch_business_shape_match_private_only_owner_identity_decision_required",
        "remediation status mismatch",
        errors,
    )

    boundary = manifest.get("raw_boundary", {})
    for key in (
        "raw_inbox_read_performed_by_this_phase",
        "raw_inbox_list_performed_by_this_phase",
        "raw_inbox_stat_performed_by_this_phase",
        "raw_inbox_hash_performed_by_this_phase",
        "raw_root_stat_unchanged_after_scan",
        "selected_source_stat_unchanged_after_scan",
    ):
        require(boundary.get(key) is True, f"raw_boundary.{key} must be true", errors)
    for key in (
        "raw_inbox_write_performed_by_this_phase",
        "raw_inbox_delete_performed_by_this_phase",
        "raw_inbox_move_performed_by_this_phase",
        "raw_inbox_rename_performed_by_this_phase",
        "raw_inbox_overwrite_performed_by_this_phase",
        "raw_inbox_create_extra_files_inside_by_this_phase",
        "raw_inbox_mutated_by_this_phase",
    ):
        require(boundary.get(key) is False, f"raw_boundary.{key} must be false", errors)

    public_safety = manifest.get("public_repo_safety", {})
    require(public_safety.get("public_safe_aggregate_only") is True, "public-safe aggregate flag mismatch", errors)
    for key in (
        "raw_business_data_committed",
        "compressed_raw_package_committed",
        "office_workbook_committed",
        "source_document_committed",
        "raw_or_private_table_committed",
        "local_database_committed",
        "credential_or_secret_committed",
        "raw_filenames_committed",
        "raw_hashes_committed",
        "directory_tree_plaintext_committed",
        "zip_member_names_committed",
        "sheet_names_committed",
        "field_or_header_plaintext_committed",
        "row_or_cell_values_committed",
        "business_values_committed",
    ):
        require(public_safety.get(key) is False, f"public_repo_safety.{key} must be false", errors)

    require(manifest.get("go_no_go") == go_no_go, "embedded go/no-go mismatch", errors)
    require(go_no_go.get("decision") == "NO_GO", "go/no-go decision mismatch", errors)
    require("RAW_CONTAINER_HASH_SIZE_MISMATCH" in go_no_go.get("blocker_ids", []), "missing raw mismatch blocker", errors)
    require(
        "RAW_SOURCE_IDENTITY_OWNER_DECISION_REQUIRED" in go_no_go.get("blocker_ids", []),
        "missing owner decision blocker",
        errors,
    )
    for key in (
        "github_upload_allowed",
        "app_reinstall_allowed",
        "formal_report_allowed",
        "business_execution_allowed",
        "raw_alignment_complete",
        "lineage_full_check_complete",
    ):
        require(go_no_go.get(key) is False, f"go_no_go.{key} must be false", errors)
    require(manifest.get("github_upload_performed") is False, "GitHub upload must not be performed", errors)
    require(manifest.get("next_recommended_phase") == "V014_OWNER_RAW_SOURCE_IDENTITY_DECISION", "next phase mismatch", errors)

    check_private_diagnostic(require_private_diagnostic, errors)
    for ref in manifest.get("evidence_refs", []):
        check_public_evidence_text(Path(ref), errors)
    for path in (
        MANIFEST_PATH,
        GO_NO_GO_PATH,
        METADATA_MANIFEST_PATH,
        METADATA_GO_NO_GO_PATH,
        REPORT_PATH,
        GO_NO_GO_RECORD_PATH,
        TEST_RESULTS_PATH,
        RISK_REGISTER_PATH,
        ROLLBACK_PATH,
    ):
        check_public_evidence_text(path, errors)

    tracked_files = git_output(["ls-files", "KMFA"]).splitlines()
    forbidden = [
        path for path in tracked_files if path.lower().endswith(FORBIDDEN_TRACKED_SUFFIXES) or ".codex_private_runtime/" in path
    ]
    require(not forbidden, "forbidden raw/private tracked artifacts: " + ", ".join(forbidden[:20]), errors)
    require("codex/kmfa" in git_output(["status", "--short", "--branch"]), "git status must be on codex/kmfa", errors)

    if errors:
        raise ValidationError("\n".join(f"- {error}" for error in errors))
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA v0.1.4 raw alignment remediation evidence.")
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    parser.add_argument("--require-private-diagnostic", action="store_true")
    args = parser.parse_args(argv)
    try:
        manifest = validate_v014_raw_alignment_remediation(
            args.manifest,
            require_private_diagnostic=args.require_private_diagnostic,
        )
    except ValidationError as exc:
        print("FAIL: KMFA v0.1.4 raw alignment remediation validation failed")
        print(exc)
        return 1
    raw = manifest["raw_source_identity_summary"]
    print(
        "PASS: KMFA v0.1.4 raw alignment remediation validated "
        f"(decision={manifest['go_no_go']['decision']}, "
        f"business_members={raw['business_member_count']}, "
        f"raw_alignment_complete={str(raw['raw_alignment_complete']).lower()}, "
        f"github_upload={str(manifest['github_upload_performed']).lower()})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
