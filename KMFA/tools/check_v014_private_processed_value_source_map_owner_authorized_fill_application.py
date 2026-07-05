#!/usr/bin/env python3
"""Validate KMFA v0.1.4 owner-authorized fill application evidence."""

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

from KMFA.tools.v014_private_processed_value_source_map_owner_authorized_fill_application import (  # noqa: E402
    ACCEPTANCE_ID,
    ACTIVE_FILL_RECORD_CANDIDATE_PATHS,
    APPLICATION_PREVIEW_PATH,
    CURRENT_GATE,
    GO_NO_GO_PATH,
    GO_NO_GO_RECORD_PATH,
    GO_NO_GO_SCHEMA_VERSION,
    MANIFEST_PATH,
    METADATA_GO_NO_GO_PATH,
    METADATA_MANIFEST_PATH,
    METADATA_PREVIEW_PATH,
    METADATA_SUMMARY_PATH,
    NEXT_RECOMMENDED_PHASE,
    PHASE_ID,
    PREVIEW_SCHEMA_VERSION,
    PRIVATE_APPLICATION_DIAGNOSTIC_PATH,
    PRIVATE_SCHEMA_VERSION,
    REPORT_PATH,
    RISK_REGISTER_PATH,
    ROLLBACK_PATH,
    SCHEMA_VERSION,
    STATUS,
    SUMMARY_PATH,
    TASK_ID,
    TEST_RESULTS_PATH,
)


FORBIDDEN_PUBLIC_KEYS = {
    "private_processed_ref",
    "raw_value",
    "normalized_value",
    "processed_value",
    "business_value",
    "source_header_text",
    "cell_value",
    "row_value",
    "plaintext_content",
    "raw_file_bytes",
    "raw_filename",
    "zip_member_name",
    "sheet_name",
    "bank_account_number",
    "password",
    "token",
    "api_key",
    "private_key",
}
FORBIDDEN_PUBLIC_TEXT = (
    "KMFA_MetaData",
    "/Users/linzezhang/Downloads",
    ".xlsx",
    ".xls",
    ".zip",
    ".pdf",
    ".sqlite",
    ".db",
    "private://",
    "private_ref://",
    "raw path",
    "raw filename",
    "sheet name",
    "cell value",
)
SECRET_PATTERNS = (
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"(?i)\b(password|passwd|secret|api" + r"_key|token)\s*=\s*[^\s,;]{8,}"),
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


def git_check_ignore(path: Path) -> bool:
    result = subprocess.run(
        ["git", "check-ignore", "-q", str(path)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return result.returncode == 0


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def walk_forbidden_public_keys(value: Any, errors: list[str], path: str = "$") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key in FORBIDDEN_PUBLIC_KEYS:
                errors.append(f"forbidden public metadata key {key!r} at {path}")
            walk_forbidden_public_keys(child, errors, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            walk_forbidden_public_keys(child, errors, f"{path}[{index}]")


def check_public_text(path: Path, errors: list[str]) -> None:
    require(path.exists(), f"missing public evidence: {path}", errors)
    if not path.exists():
        return
    text = path.read_text(encoding="utf-8", errors="ignore")
    lower = text.lower()
    for forbidden in FORBIDDEN_PUBLIC_TEXT:
        require(forbidden.lower() not in lower, f"forbidden public text {forbidden!r} in {path}", errors)
    for pattern in SECRET_PATTERNS:
        require(pattern.search(text) is None, f"secret-like token found in {path}: {pattern.pattern}", errors)


def _validate_summary(summary: dict[str, Any], errors: list[str]) -> None:
    expected_summary = {
        "source_unresolved_gap_item_count": 113,
        "source_unresolved_unique_private_ref_count": 101,
        "source_duplicate_unresolved_gap_item_count": 12,
        "source_existing_source_map_record_count": 36,
        "private_intake_request_item_count": 113,
        "candidate_active_fill_record_path_count": 2,
        "existing_active_fill_record_path_count": 0,
        "owner_authorized_fill_intake_ready": True,
        "owner_authorized_fill_record_supplied": False,
        "active_authorized_fill_record_found": False,
        "fill_application_performed": False,
        "source_map_records_applied_count": 0,
        "new_authorized_fingerprint_count": 0,
        "source_map_gap_resolution_complete": False,
        "processed_value_materialization_replay_ready": False,
        "raw_to_processed_value_comparison_ready": False,
        "raw_processed_consistency_cross_validation_performed": False,
        "processed_raw_consistency_verified": False,
        "final_discrepancy_report_required_if_later_cross_validation_fails": True,
        "application_status": "blocked_no_active_owner_authorized_fill_record",
    }
    for key, expected in expected_summary.items():
        require(summary.get(key) == expected, f"summary {key} mismatch: {summary.get(key)!r} != {expected!r}", errors)


def _validate_preview(preview: dict[str, Any], summary: dict[str, Any], errors: list[str]) -> None:
    walk_forbidden_public_keys(preview, errors)
    require(
        preview.get("record_type") == "v014_private_processed_value_source_map_owner_authorized_fill_application_preview",
        "preview record_type mismatch",
        errors,
    )
    require(preview.get("schema_version") == PREVIEW_SCHEMA_VERSION, "preview schema mismatch", errors)
    require(preview.get("project_id") == "KMFA", "preview project mismatch", errors)
    require(preview.get("phase_id") == PHASE_ID, "preview phase mismatch", errors)
    require(preview.get("task_id") == TASK_ID, "preview task mismatch", errors)
    require(preview.get("current_gate") == CURRENT_GATE, "preview gate mismatch", errors)
    require(preview.get("application_status") == summary.get("application_status"), "preview status mismatch", errors)
    require(preview.get("next_required_input") == "active_owner_or_authorized_delegate_fill_record", "preview next input mismatch", errors)
    for key in (
        "owner_authorized_fill_record_supplied",
        "active_authorized_fill_record_found",
        "fill_application_performed",
        "source_map_gap_resolution_complete",
        "processed_value_materialization_replay_allowed_by_application",
        "raw_to_processed_value_comparison_allowed_by_application",
        "raw_processed_consistency_cross_validation_allowed_by_application",
        "lineage_full_check_allowed_by_application",
        "formal_report_allowed_by_application",
        "github_upload_allowed_by_application",
        "app_reinstall_allowed_by_application",
        "business_execution_allowed_by_application",
    ):
        require(preview.get(key) is False, f"preview.{key} must be false", errors)
    require(preview.get("source_map_records_applied_count") == 0, "preview applied count mismatch", errors)
    require(preview.get("new_authorized_fingerprint_count") == 0, "preview fingerprint count mismatch", errors)


def check_private_application_diagnostic(*, require_private_application_diagnostic: bool, errors: list[str]) -> None:
    require(".codex_private_runtime/" in PRIVATE_APPLICATION_DIAGNOSTIC_PATH.as_posix(), "private diagnostic path mismatch", errors)
    require(not git_output(["ls-files", str(PRIVATE_APPLICATION_DIAGNOSTIC_PATH)]), "private diagnostic must not be tracked", errors)
    require(git_check_ignore(PRIVATE_APPLICATION_DIAGNOSTIC_PATH), "private diagnostic must be git-ignored", errors)
    for path in ACTIVE_FILL_RECORD_CANDIDATE_PATHS:
        require(".codex_private_runtime/" in path.as_posix(), f"active record candidate path mismatch: {path}", errors)
        require(git_check_ignore(path), f"active record candidate must be git-ignored: {path}", errors)
        require(not path.exists(), f"active record candidate unexpectedly exists for this NO_GO phase: {path}", errors)
    if not require_private_application_diagnostic:
        return
    require(PRIVATE_APPLICATION_DIAGNOSTIC_PATH.exists(), f"private diagnostic must exist: {PRIVATE_APPLICATION_DIAGNOSTIC_PATH}", errors)
    if not PRIVATE_APPLICATION_DIAGNOSTIC_PATH.exists():
        return
    diagnostic = read_json(PRIVATE_APPLICATION_DIAGNOSTIC_PATH)
    require(diagnostic.get("schema_version") == PRIVATE_SCHEMA_VERSION, "private diagnostic schema mismatch", errors)
    require(
        diagnostic.get("classification") == "private_owner_authorized_fill_application_diagnostic_do_not_commit",
        "private diagnostic classification mismatch",
        errors,
    )
    summary = diagnostic.get("application_diagnostic_summary", {})
    require(summary.get("candidate_active_fill_record_path_count") == 2, "private diagnostic candidate count mismatch", errors)
    require(summary.get("active_fill_record_found") is False, "private diagnostic active record flag must be false", errors)
    require(summary.get("existing_active_fill_record_path_count") == 0, "private diagnostic active path count mismatch", errors)
    require(summary.get("private_intake_request_summary_item_count") == 113, "private diagnostic intake count mismatch", errors)
    require(summary.get("raw_inbox_read_performed_by_this_phase") is False, "private diagnostic raw read flag must be false", errors)
    require(summary.get("raw_inbox_mutation_performed_by_this_phase") is False, "private diagnostic raw mutation flag must be false", errors)
    require(summary.get("fill_application_performed") is False, "private diagnostic application flag must be false", errors)


def check_tracked_sensitive_suffixes(errors: list[str]) -> None:
    tracked = git_output(["ls-files", "KMFA"])
    for filename in tracked.splitlines():
        lower = filename.lower()
        if any(lower.endswith(suffix) for suffix in FORBIDDEN_TRACKED_SUFFIXES) or ".codex_private_runtime/" in filename:
            errors.append(f"forbidden raw/private tracked artifact: {filename}")


def validate_v014_private_processed_value_source_map_owner_authorized_fill_application(
    manifest_path: Path = MANIFEST_PATH,
    *,
    require_private_application_diagnostic: bool = False,
) -> dict[str, Any]:
    errors: list[str] = []
    manifest = read_json(manifest_path)
    go_no_go = read_json(GO_NO_GO_PATH)
    summary = read_json(SUMMARY_PATH)
    preview = read_json(APPLICATION_PREVIEW_PATH)
    metadata_manifest = read_json(METADATA_MANIFEST_PATH)
    metadata_go_no_go = read_json(METADATA_GO_NO_GO_PATH)
    metadata_summary = read_json(METADATA_SUMMARY_PATH)
    metadata_preview = read_json(METADATA_PREVIEW_PATH)

    require(metadata_manifest == manifest, "metadata manifest copy mismatch", errors)
    require(metadata_go_no_go == go_no_go, "metadata go/no-go copy mismatch", errors)
    require(metadata_summary == summary, "metadata summary copy mismatch", errors)
    require(metadata_preview == preview, "metadata preview copy mismatch", errors)

    walk_forbidden_public_keys(manifest, errors)
    walk_forbidden_public_keys(go_no_go, errors)
    walk_forbidden_public_keys(summary, errors)
    require(manifest.get("schema_version") == SCHEMA_VERSION, "manifest schema mismatch", errors)
    require(manifest.get("record_type") == "v014_private_processed_value_source_map_owner_authorized_fill_application_manifest", "manifest record type mismatch", errors)
    require(manifest.get("project_id") == "KMFA", "manifest project mismatch", errors)
    require(manifest.get("version") == "0.1.4", "manifest version mismatch", errors)
    require(manifest.get("phase_id") == PHASE_ID, "manifest phase mismatch", errors)
    require(manifest.get("task_id") == TASK_ID, "manifest task mismatch", errors)
    require(manifest.get("acceptance_ids") == [ACCEPTANCE_ID], "manifest acceptance mismatch", errors)
    require(manifest.get("status") == STATUS, "manifest status mismatch", errors)
    require(manifest.get("owner_authorized_fill_application_summary") == summary, "manifest summary mismatch", errors)
    require(manifest.get("application_preview") == preview, "manifest preview mismatch", errors)
    require(manifest.get("go_no_go") == go_no_go, "manifest go/no-go mismatch", errors)
    require(manifest.get("next_recommended_phase") == NEXT_RECOMMENDED_PHASE, "manifest next phase mismatch", errors)

    _validate_summary(summary, errors)
    _validate_preview(preview, summary, errors)

    basis = manifest.get("basis_summary", {})
    require(basis.get("source_phase_id") == "V014_PRIVATE_PROCESSED_VALUE_SOURCE_MAP_OWNER_AUTHORIZED_FILL_INTAKE", "basis source phase mismatch", errors)
    require(basis.get("source_decision") == "NO_GO", "basis source decision mismatch", errors)
    require(basis.get("private_intake_request_file_present") is True, "basis private intake request presence mismatch", errors)
    require(basis.get("private_intake_request_summary_item_count") == 113, "basis private intake count mismatch", errors)
    require(basis.get("owner_authorized_fill_intake_ready") is True, "basis intake readiness mismatch", errors)
    require(basis.get("source_owner_authorized_fill_record_supplied") is False, "basis source supplied flag must be false", errors)
    require(basis.get("source_active_authorized_fill_record_created") is False, "basis source active flag must be false", errors)

    require(go_no_go.get("schema_version") == GO_NO_GO_SCHEMA_VERSION, "go/no-go schema mismatch", errors)
    require(go_no_go.get("record_type") == "v014_private_processed_value_source_map_owner_authorized_fill_application_go_no_go_report", "go/no-go record type mismatch", errors)
    require(go_no_go.get("decision") == "NO_GO", "go/no-go decision mismatch", errors)
    require(go_no_go.get("application_status") == summary.get("application_status"), "go/no-go status mismatch", errors)
    require(go_no_go.get("owner_authorized_fill_intake_ready") is True, "go/no-go intake readiness mismatch", errors)
    require(go_no_go.get("owner_authorized_fill_record_supplied") is False, "go/no-go supplied flag mismatch", errors)
    require(go_no_go.get("active_authorized_fill_record_found") is False, "go/no-go active flag mismatch", errors)
    require(go_no_go.get("fill_application_performed") is False, "go/no-go application flag mismatch", errors)
    require("ACTIVE_OWNER_AUTHORIZED_FILL_RECORD_NOT_FOUND" in go_no_go.get("blocker_ids", []), "missing active-record blocker", errors)
    for key in (
        "source_map_gap_resolution_complete",
        "processed_value_materialization_replay_allowed",
        "raw_to_processed_value_comparison_allowed",
        "raw_processed_consistency_cross_validation_performed",
        "business_value_consistency_verified",
        "lineage_full_check_complete",
        "formal_report_allowed",
        "github_upload_allowed",
        "app_reinstall_allowed",
        "business_execution_allowed",
    ):
        require(go_no_go.get(key) is False, f"go_no_go.{key} must be false", errors)

    scope = manifest.get("phase_scope_controls", {})
    require(scope.get("current_phase_only") is True, "scope current_phase_only must be true", errors)
    require(scope.get("owner_authorized_fill_application_gate_only") is True, "scope application gate flag must be true", errors)
    for key in (
        "active_fill_record_authored_by_codex",
        "active_fill_record_created_by_this_phase",
        "active_fill_record_materialized_from_user_input_by_this_phase",
        "private_source_map_records_applied_by_this_phase",
        "new_fingerprints_materialized",
        "processed_value_materialization_replay_performed",
        "raw_to_processed_value_comparison_performed",
        "raw_processed_consistency_cross_validation_performed",
        "processed_data_reconciliation_performed",
        "lineage_full_check_performed",
        "formal_report_performed",
        "github_upload_performed",
        "app_reinstall_performed",
        "business_execution_performed",
        "next_phase_started",
    ):
        require(scope.get(key) is False, f"phase_scope_controls.{key} must be false", errors)

    raw_boundary = manifest.get("raw_readonly_boundary", {})
    for key in (
        "user_declared_raw_data_immutable",
        "raw_data_root_readonly_policy_active",
        "later_processed_outputs_must_reconcile_to_raw",
        "final_discrepancy_report_required_if_repeated_cross_validation_diverges",
    ):
        require(raw_boundary.get(key) is True, f"raw_readonly_boundary.{key} must be true", errors)
    for key in (
        "raw_inbox_read_performed_by_this_phase",
        "raw_inbox_list_performed_by_this_phase",
        "raw_inbox_stat_performed_by_this_phase",
        "raw_inbox_hash_or_value_fingerprint_performed_by_this_phase",
        "raw_inbox_write_performed_by_this_phase",
        "raw_inbox_delete_performed_by_this_phase",
        "raw_inbox_move_performed_by_this_phase",
        "raw_inbox_rename_performed_by_this_phase",
        "raw_inbox_mutation_performed_by_this_phase",
    ):
        require(raw_boundary.get(key) is False, f"raw_readonly_boundary.{key} must be false", errors)

    public_safety = manifest.get("public_repo_safety", {})
    require(public_safety.get("public_safe_application_status_only") is True, "public safety status flag mismatch", errors)
    require(public_safety.get("public_safe_aggregate_only") is True, "public safety aggregate flag mismatch", errors)
    for key, value in public_safety.items():
        if key.startswith("public_safe_"):
            continue
        require(value is False, f"public_repo_safety.{key} must be false", errors)

    raw_requirement = manifest.get("raw_data_consistency_requirement", {})
    require(raw_requirement.get("raw_data_immutable_for_codex") is True, "raw requirement immutable flag mismatch", errors)
    require(raw_requirement.get("comparison_performed_in_this_phase") is False, "raw requirement comparison flag mismatch", errors)
    require(raw_requirement.get("later_cross_validation_required_before_release") is True, "raw requirement later validation flag mismatch", errors)
    require(
        raw_requirement.get("final_discrepancy_report_required_if_repeated_cross_validation_diverges") is True,
        "raw requirement discrepancy report flag mismatch",
        errors,
    )

    for path in (
        REPORT_PATH,
        GO_NO_GO_RECORD_PATH,
        TEST_RESULTS_PATH,
        RISK_REGISTER_PATH,
        ROLLBACK_PATH,
        MANIFEST_PATH,
        GO_NO_GO_PATH,
        SUMMARY_PATH,
        APPLICATION_PREVIEW_PATH,
        METADATA_MANIFEST_PATH,
        METADATA_GO_NO_GO_PATH,
        METADATA_SUMMARY_PATH,
        METADATA_PREVIEW_PATH,
    ):
        check_public_text(path, errors)
    for ref in manifest.get("source_evidence_refs", []):
        require(Path(ref).exists(), f"missing source evidence ref: {ref}", errors)

    check_private_application_diagnostic(
        require_private_application_diagnostic=require_private_application_diagnostic,
        errors=errors,
    )
    check_tracked_sensitive_suffixes(errors)
    require("codex/kmfa" in git_output(["status", "--short", "--branch"]), "git status must be on codex/kmfa", errors)
    if errors:
        raise ValidationError("\n".join(f"- {error}" for error in errors))
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    parser.add_argument("--require-private-application-diagnostic", action="store_true")
    args = parser.parse_args(argv)
    try:
        manifest = validate_v014_private_processed_value_source_map_owner_authorized_fill_application(
            args.manifest,
            require_private_application_diagnostic=args.require_private_application_diagnostic,
        )
    except ValidationError as exc:
        print("FAIL: KMFA v0.1.4 owner-authorized fill application validation failed")
        print(exc)
        return 1
    summary = manifest["owner_authorized_fill_application_summary"]
    print(
        "PASS: KMFA v0.1.4 owner-authorized fill application validated "
        f"(active_record={str(summary['active_authorized_fill_record_found']).lower()}, "
        f"applied={str(summary['fill_application_performed']).lower()}, "
        f"github_upload={str(manifest['go_no_go']['github_upload_allowed']).lower()})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
