#!/usr/bin/env python3
"""Validate KMFA v0.1.4 raw source identity decision application evidence."""

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

from KMFA.tools.v014_raw_source_identity_decision_application import (  # noqa: E402
    ACCEPTANCE_ID,
    APPLICATION_PREVIEW_PATH,
    CURRENT_GATE,
    GO_NO_GO_PATH,
    GO_NO_GO_RECORD_PATH,
    GO_NO_GO_SCHEMA_VERSION,
    MANIFEST_PATH,
    METADATA_GO_NO_GO_PATH,
    METADATA_MANIFEST_PATH,
    METADATA_OWNER_DECISION_RECORD_PATH,
    METADATA_PREVIEW_PATH,
    OWNER_DECISION_RECORD_PATH,
    PHASE_ID,
    PREVIEW_SCHEMA_VERSION,
    REPORT_PATH,
    RISK_REGISTER_PATH,
    ROLLBACK_PATH,
    SCHEMA_VERSION,
    STATUS,
    TASK_ID,
    TEST_RESULTS_PATH,
)
from KMFA.tools.check_v014_owner_raw_source_identity_decision import (  # noqa: E402
    validate_owner_decision_payload,
)
from KMFA.tools.v014_owner_raw_source_identity_decision import ALLOWED_DECISION_CODES  # noqa: E402


FORBIDDEN_PUBLIC_KEYS = {
    "actual_package_sha256",
    "expected_package_sha256",
    "member_sha256",
    "member_name_sha256",
    "raw_value",
    "normalized_value",
    "plaintext_content",
    "full_file_text",
    "raw_file_bytes",
    "raw_filename",
    "zip_member_name",
    "sheet_name",
    "bank_account_number",
    "identity_document_number",
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
    "actual_package_sha256",
    "expected_package_sha256",
    "member_sha256",
    "member_name_sha256",
    "private_ref://",
    "raw path",
    "raw filename",
)
SECRET_PATTERNS = (
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"(?i)\b(password|passwd|secret|api" + r"_key|token)\s*=\s*[^\s,;]{8,}"),
)
SHA256_VALUE = re.compile(r"\b[a-f0-9]{64}\b")
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


def walk_forbidden_keys(value: Any, errors: list[str], path: str = "$") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key in FORBIDDEN_PUBLIC_KEYS:
                errors.append(f"forbidden public metadata key {key!r} at {path}")
            walk_forbidden_keys(child, errors, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            walk_forbidden_keys(child, errors, f"{path}[{index}]")


def check_public_text(path: Path, errors: list[str]) -> None:
    require(path.exists(), f"missing public evidence: {path}", errors)
    if not path.exists():
        return
    text = path.read_text(encoding="utf-8", errors="ignore")
    lower = text.lower()
    for forbidden in FORBIDDEN_PUBLIC_TEXT:
        require(forbidden.lower() not in lower, f"forbidden public text {forbidden!r} in {path}", errors)
    require(SHA256_VALUE.search(text) is None, f"raw/hash-like 64 hex value found in {path}", errors)
    for pattern in SECRET_PATTERNS:
        require(pattern.search(text) is None, f"secret-like token found in {path}: {pattern.pattern}", errors)


def _validate_preview(preview: dict[str, Any], errors: list[str]) -> None:
    walk_forbidden_keys(preview, errors)
    require(preview.get("record_type") == "v014_raw_source_identity_decision_application_preview", "preview record_type mismatch", errors)
    require(preview.get("schema_version") == PREVIEW_SCHEMA_VERSION, "preview schema mismatch", errors)
    require(preview.get("project_id") == "KMFA", "preview project_id mismatch", errors)
    require(preview.get("phase_id") == PHASE_ID, "preview phase_id mismatch", errors)
    require(preview.get("task_id") == TASK_ID, "preview task_id mismatch", errors)
    require(preview.get("current_gate") == CURRENT_GATE, "preview gate mismatch", errors)
    decision_code = preview.get("decision_code")
    require(decision_code in {"none", *ALLOWED_DECISION_CODES}, "preview decision_code mismatch", errors)
    if decision_code == "none":
        require(preview.get("application_status") == "blocked_no_active_owner_decision", "preview application status mismatch", errors)
        require(preview.get("owner_decision_supplied") is False, "preview owner_decision_supplied must be false", errors)
        require(preview.get("decision_applied") is False, "preview decision_applied must be false", errors)
        require(preview.get("active_owner_decision_record_ref") is None, "preview decision ref must be none without decision", errors)
    elif decision_code == "keep_pending":
        require(preview.get("application_status") == "blocked_by_owner_keep_pending", "preview keep_pending status mismatch", errors)
        require(preview.get("owner_decision_supplied") is True, "preview owner_decision_supplied must be true", errors)
        require(preview.get("decision_applied") is False, "preview keep_pending must not apply", errors)
        require(preview.get("active_owner_decision_record_ref") == OWNER_DECISION_RECORD_PATH.as_posix(), "preview decision ref mismatch", errors)
    elif decision_code == "confirm_current_container_as_authoritative":
        require(
            preview.get("application_status") == "owner_confirmation_recorded_for_separate_backfill_gate",
            "preview owner confirmation status mismatch",
            errors,
        )
        require(preview.get("owner_decision_supplied") is True, "preview owner_decision_supplied must be true", errors)
        require(preview.get("decision_applied") is True, "preview owner confirmation must be applied", errors)
        require(preview.get("active_owner_decision_record_ref") == OWNER_DECISION_RECORD_PATH.as_posix(), "preview decision ref mismatch", errors)
    elif decision_code == "register_corrected_source_package":
        require(
            preview.get("application_status") == "blocked_corrected_source_registration_required",
            "preview corrected-source status mismatch",
            errors,
        )
        require(preview.get("owner_decision_supplied") is True, "preview owner_decision_supplied must be true", errors)
        require(preview.get("decision_applied") is False, "preview corrected-source must not apply current container", errors)
        require(preview.get("active_owner_decision_record_ref") == OWNER_DECISION_RECORD_PATH.as_posix(), "preview decision ref mismatch", errors)
    for key in (
        "raw_alignment_complete_claimed_by_application",
        "public_member_hash_backfill_allowed_by_application",
        "lineage_full_check_complete_by_application",
        "formal_report_allowed_by_application",
        "github_upload_allowed_by_application",
        "app_reinstall_allowed_by_application",
        "business_execution_allowed_by_application",
    ):
        require(preview.get(key) is False, f"preview.{key} must be false", errors)
    public_safety = preview.get("public_repo_safety", {})
    require(public_safety.get("public_safe_application_status_only") is True, "preview public safety status flag mismatch", errors)
    require(public_safety.get("public_safe_owner_decision_metadata_only") is True, "preview public safety decision metadata flag mismatch", errors)
    for key, value in public_safety.items():
        if key in {"public_safe_application_status_only", "public_safe_owner_decision_metadata_only"}:
            continue
        require(value is False, f"preview.public_repo_safety.{key} must be false", errors)


def validate_v014_raw_source_identity_decision_application(
    manifest_path: Path = MANIFEST_PATH,
) -> dict[str, Any]:
    errors: list[str] = []
    manifest = read_json(manifest_path)
    metadata_manifest = read_json(METADATA_MANIFEST_PATH)
    go_no_go = read_json(GO_NO_GO_PATH)
    metadata_go_no_go = read_json(METADATA_GO_NO_GO_PATH)
    preview = read_json(APPLICATION_PREVIEW_PATH)
    metadata_preview = read_json(METADATA_PREVIEW_PATH)

    require(metadata_manifest == manifest, "metadata manifest copy mismatch", errors)
    require(metadata_go_no_go == go_no_go, "metadata go/no-go copy mismatch", errors)
    require(metadata_preview == preview, "metadata preview copy mismatch", errors)
    walk_forbidden_keys(manifest, errors)
    walk_forbidden_keys(go_no_go, errors)
    _validate_preview(preview, errors)

    require(manifest.get("schema_version") == SCHEMA_VERSION, "manifest schema mismatch", errors)
    require(manifest.get("project_id") == "KMFA", "manifest project_id mismatch", errors)
    require(manifest.get("version") == "0.1.4", "manifest version mismatch", errors)
    require(manifest.get("phase_id") == PHASE_ID, "manifest phase_id mismatch", errors)
    require(manifest.get("task_id") == TASK_ID, "manifest task_id mismatch", errors)
    require(manifest.get("acceptance_ids") == [ACCEPTANCE_ID], "acceptance ids mismatch", errors)
    require(manifest.get("status") == STATUS, "manifest status mismatch", errors)
    require(manifest.get("decision_application") == preview, "embedded preview mismatch", errors)
    require(manifest.get("go_no_go") == go_no_go, "embedded go/no-go mismatch", errors)
    decision_code = preview.get("decision_code")
    owner_decision = manifest.get("active_owner_decision_record", {})
    require(owner_decision.get("decision_code") == decision_code, "active owner decision code mismatch", errors)
    if decision_code == "none":
        require(owner_decision.get("supplied") is False, "owner decision supplied must be false", errors)
        require(owner_decision.get("record_ref") is None, "owner decision record ref must be none", errors)
    else:
        require(owner_decision.get("supplied") is True, "owner decision supplied must be true", errors)
        require(owner_decision.get("record_ref") == OWNER_DECISION_RECORD_PATH.as_posix(), "owner decision record ref mismatch", errors)
        require(owner_decision.get("metadata_record_ref") == METADATA_OWNER_DECISION_RECORD_PATH.as_posix(), "owner decision metadata ref mismatch", errors)
        require(owner_decision.get("owner_decision_authored_by_codex") is False, "owner decision must not be authored by Codex", errors)
        require(
            owner_decision.get("materialized_from_user_safe_decision_code") is True,
            "owner decision materialization flag mismatch",
            errors,
        )
        require(owner_decision.get("raw_plaintext_or_hash_in_decision_record") is False, "owner decision raw/hash flag must be false", errors)
        decision_record = read_json(OWNER_DECISION_RECORD_PATH)
        metadata_decision_record = read_json(METADATA_OWNER_DECISION_RECORD_PATH)
        require(metadata_decision_record == decision_record, "metadata owner decision record copy mismatch", errors)
        validate_owner_decision_payload(decision_record)
        require(decision_record.get("decision_code") == decision_code, "persisted owner decision code mismatch", errors)

    basis = manifest.get("basis_summary", {})
    require(basis.get("source_phase_id") == "V014_OWNER_RAW_SOURCE_IDENTITY_DECISION", "basis source phase mismatch", errors)
    require(basis.get("source_decision") == "NO_GO", "basis source decision mismatch", errors)
    require(basis.get("owner_decision_intake_ready") is True, "basis intake ready flag mismatch", errors)
    require(basis.get("owner_decision_supplied") is False, "basis owner decision supplied must remain false for source intake phase", errors)
    require(basis.get("decision_record_status") == "no_owner_decision_recorded", "basis decision record status mismatch", errors)
    require(basis.get("allowed_decision_count") == 3, "basis allowed decision count mismatch", errors)
    require(basis.get("allowed_actor_role_count") == 2, "basis actor role count mismatch", errors)
    require(basis.get("business_shape_matches_expected_a0") is True, "basis business shape mismatch", errors)
    require(basis.get("package_hash_matches_registered") is False, "basis package hash flag must be false", errors)
    require(basis.get("package_size_matches_registered") is False, "basis package size flag must be false", errors)
    require(basis.get("raw_alignment_complete") is False, "basis raw alignment complete must be false", errors)
    require(basis.get("public_member_hash_backfill_allowed") is False, "basis backfill flag must be false", errors)
    require(basis.get("business_member_count") == 9, "basis business member count mismatch", errors)

    scope = manifest.get("phase_scope_controls", {})
    require(scope.get("current_phase_only") is True, "scope current_phase_only must be true", errors)
    require(scope.get("application_gate_only") is True, "scope application_gate_only must be true", errors)
    for key in (
        "source_container_selected_by_this_phase",
        "raw_inbox_read_performed_by_this_phase",
        "raw_inbox_list_performed_by_this_phase",
        "raw_inbox_stat_performed_by_this_phase",
        "raw_inbox_hash_performed_by_this_phase",
        "raw_inbox_mutated_by_this_phase",
        "public_hash_backfill_performed",
        "lineage_full_check_performed",
        "formal_report_performed",
        "github_upload_performed",
        "app_reinstall_performed",
        "business_execution_performed",
        "next_phase_started",
    ):
        require(scope.get(key) is False, f"scope.{key} must be false", errors)
    if decision_code == "none":
        require(
            scope.get("owner_decision_record_materialized_from_user_input_by_this_phase") is False,
            "scope materialized decision flag must be false",
            errors,
        )
        require(scope.get("owner_decision_record_authored_by_codex") is None, "scope authored flag must be none without decision", errors)
    else:
        require(
            scope.get("owner_decision_record_materialized_from_user_input_by_this_phase") is True,
            "scope materialized decision flag must be true",
            errors,
        )
        require(scope.get("owner_decision_record_authored_by_codex") is False, "scope authored flag must be false", errors)

    public_safety = manifest.get("public_repo_safety", {})
    require(public_safety.get("public_safe_application_status_only") is True, "public safety status flag mismatch", errors)
    require(public_safety.get("public_safe_owner_decision_metadata_only") is True, "public safety decision metadata flag mismatch", errors)
    for key, value in public_safety.items():
        if key in {"public_safe_application_status_only", "public_safe_owner_decision_metadata_only"}:
            continue
        require(value is False, f"public_repo_safety.{key} must be false", errors)

    require(go_no_go.get("record_type") == "v014_raw_source_identity_decision_application_go_no_go_report", "go/no-go record type mismatch", errors)
    require(go_no_go.get("schema_version") == GO_NO_GO_SCHEMA_VERSION, "go/no-go schema mismatch", errors)
    require(go_no_go.get("decision") == "NO_GO", "go/no-go decision mismatch", errors)
    require(go_no_go.get("application_status") == preview.get("application_status"), "go/no-go application status mismatch", errors)
    require(go_no_go.get("decision_code") == decision_code, "go/no-go decision code mismatch", errors)
    require(go_no_go.get("owner_decision_intake_ready") is True, "go/no-go intake ready flag mismatch", errors)
    require(go_no_go.get("owner_decision_supplied") is preview.get("owner_decision_supplied"), "go/no-go supplied flag mismatch", errors)
    require(go_no_go.get("decision_applied") is preview.get("decision_applied"), "go/no-go applied flag mismatch", errors)
    blocker_ids = go_no_go.get("blocker_ids", [])
    if decision_code == "none":
        require("RAW_SOURCE_IDENTITY_OWNER_DECISION_NOT_SUPPLIED" in blocker_ids, "missing owner decision blocker", errors)
        require("RAW_SOURCE_IDENTITY_DECISION_APPLICATION_BLOCKED" in blocker_ids, "missing application blocker", errors)
    elif decision_code == "keep_pending":
        require("RAW_SOURCE_IDENTITY_OWNER_DECISION_KEPT_PENDING" in blocker_ids, "missing keep-pending blocker", errors)
        require("RAW_SOURCE_IDENTITY_DECISION_APPLICATION_BLOCKED" in blocker_ids, "missing application blocker", errors)
    elif decision_code == "confirm_current_container_as_authoritative":
        require("PUBLIC_MEMBER_HASH_BACKFILL_SEPARATE_GATE_REQUIRED" in blocker_ids, "missing separate backfill blocker", errors)
        require("RAW_SOURCE_IDENTITY_DECISION_APPLICATION_BLOCKED" not in blocker_ids, "confirmation should not keep application blocker", errors)
        require(
            "RAW_SOURCE_IDENTITY_OWNER_CONFIRMATION_APPLIED" in go_no_go.get("resolved_blocker_ids", []),
            "missing owner confirmation resolved marker",
            errors,
        )
    elif decision_code == "register_corrected_source_package":
        require("CORRECTED_SOURCE_REGISTRY_GATE_REQUIRED" in blocker_ids, "missing corrected-source registry blocker", errors)
        require("RAW_SOURCE_IDENTITY_DECISION_APPLICATION_BLOCKED" in blocker_ids, "missing application blocker", errors)
    require("OWNER_DECISION_INTAKE_READY" in go_no_go.get("resolved_blocker_ids", []), "missing intake-ready resolved marker", errors)
    for key in (
        "raw_alignment_complete",
        "public_member_hash_backfill_allowed",
        "lineage_full_check_complete",
        "github_upload_allowed",
        "app_reinstall_allowed",
        "formal_report_allowed",
        "business_execution_allowed",
    ):
        require(go_no_go.get(key) is False, f"go_no_go.{key} must be false", errors)
    require(manifest.get("github_upload_performed") is False, "manifest github upload must be false", errors)
    require(manifest.get("github_upload_status") == "not_uploaded_blocked_by_raw_source_identity_application", "github upload status mismatch", errors)
    require(
        manifest.get("raw_data_consistency_verification_status")
        == "not_performed_in_this_phase_deferred_to_later_cross_validation_gate",
        "raw data consistency verification status mismatch",
        errors,
    )

    for ref in manifest.get("evidence_refs", []):
        check_public_text(Path(ref), errors)
    for path in (
        MANIFEST_PATH,
        GO_NO_GO_PATH,
        APPLICATION_PREVIEW_PATH,
        METADATA_MANIFEST_PATH,
        METADATA_GO_NO_GO_PATH,
        METADATA_PREVIEW_PATH,
        *( [OWNER_DECISION_RECORD_PATH, METADATA_OWNER_DECISION_RECORD_PATH] if decision_code != "none" else [] ),
        REPORT_PATH,
        GO_NO_GO_RECORD_PATH,
        TEST_RESULTS_PATH,
        RISK_REGISTER_PATH,
        ROLLBACK_PATH,
    ):
        check_public_text(path, errors)

    for ref in manifest.get("source_evidence_refs", []):
        require(Path(ref).exists(), f"missing source evidence ref: {ref}", errors)

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
    parser = argparse.ArgumentParser(description="Validate KMFA v0.1.4 raw source identity decision application evidence.")
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    args = parser.parse_args(argv)
    try:
        manifest = validate_v014_raw_source_identity_decision_application(args.manifest)
    except ValidationError as exc:
        print("FAIL: KMFA v0.1.4 raw source identity decision application validation failed")
        print(exc)
        return 1
    print(
        "PASS: KMFA v0.1.4 raw source identity decision application validated "
        f"(decision={manifest['go_no_go']['decision']}, "
        f"application_status={manifest['go_no_go']['application_status']}, "
        f"owner_decision_supplied={str(manifest['go_no_go']['owner_decision_supplied']).lower()}, "
        f"github_upload={str(manifest['go_no_go']['github_upload_allowed']).lower()})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
