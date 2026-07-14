#!/usr/bin/env python3
"""Validate KMFA v0.1.4 source-map authorized-fill gap-resolution evidence."""

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

from KMFA.tools.v014_private_processed_value_source_map_gap_resolution import (  # noqa: E402
    ACCEPTANCE_ID,
    GAP_MATRIX_PATH,
    GO_NO_GO_PATH,
    GO_NO_GO_RECORD_PATH,
    GO_NO_GO_SCHEMA_VERSION,
    MANIFEST_PATH,
    METADATA_GAP_MATRIX_PATH,
    METADATA_GO_NO_GO_PATH,
    METADATA_MANIFEST_PATH,
    METADATA_SUMMARY_PATH,
    NEXT_RECOMMENDED_PHASE,
    PHASE_ID,
    PRIVATE_GAP_DIAGNOSTIC_PATH,
    PRIVATE_OWNER_WORKLIST_PATH,
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


FORBIDDEN_PUBLIC_TEXT = (
    "raw_path",
    "raw_root_path",
    "sheet_name:",
    "worksheet_name",
    "member_name",
    "raw_value:",
    "normalized_value:",
    "source_header_text:",
    "cell_value:",
    "row_value:",
    "pdf_text",
    "business_value:",
    "project_name_plaintext",
    "customer_name_plaintext",
    "counterparty_plaintext",
    "company_entity_plaintext",
    "supplier_name_plaintext",
    "account_number:",
    "invoice_number:",
    "tax_identifier:",
    "private://",
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
FORBIDDEN_PUBLIC_KEYS = {
    "private_processed_ref",
    "raw_value",
    "normalized_value",
    "processed_value",
    "business_value",
    "source_header_text",
    "cell_value",
    "row_value",
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


def _contains_forbidden_public_key(value: Any) -> bool:
    if isinstance(value, dict):
        for key, child in value.items():
            if key in FORBIDDEN_PUBLIC_KEYS:
                return True
            if _contains_forbidden_public_key(child):
                return True
    elif isinstance(value, list):
        return any(_contains_forbidden_public_key(child) for child in value)
    return False


def check_private_worklist(*, require_private_owner_worklist: bool, expected_count: int, errors: list[str]) -> None:
    for path in (PRIVATE_OWNER_WORKLIST_PATH, PRIVATE_GAP_DIAGNOSTIC_PATH):
        require(".codex_private_runtime/" in path.as_posix(), f"private path mismatch: {path}", errors)
        require(not git_output(["ls-files", str(path)]), f"private artifact must not be tracked: {path}", errors)
        require(git_check_ignore(path), f"private artifact must be git-ignored: {path}", errors)
    if not require_private_owner_worklist:
        return
    for path in (PRIVATE_OWNER_WORKLIST_PATH, PRIVATE_GAP_DIAGNOSTIC_PATH):
        require(path.exists(), f"private gap artifact must exist: {path}", errors)
    if not PRIVATE_OWNER_WORKLIST_PATH.exists():
        return
    worklist = read_json(PRIVATE_OWNER_WORKLIST_PATH)
    require(worklist.get("schema_version") == PRIVATE_SCHEMA_VERSION, "private worklist schema mismatch", errors)
    require(
        worklist.get("classification") == "private_owner_authorized_fill_worklist_do_not_commit",
        "private worklist classification mismatch",
        errors,
    )
    summary = worklist.get("owner_worklist_summary", {})
    require(summary.get("owner_worklist_item_count") == expected_count, "private worklist item count mismatch", errors)
    require(summary.get("raw_to_processed_value_comparison_performed") is False, "private comparison flag must be false", errors)
    require(summary.get("business_value_consistency_verified") is False, "private business consistency flag must be false", errors)
    items = worklist.get("owner_worklist_items", [])
    require(isinstance(items, list), "owner worklist items must be list", errors)
    require(len(items) == expected_count, "owner worklist item list length mismatch", errors)
    for item in items:
        if not isinstance(item, dict):
            continue
        require(item.get("required_owner_action") == "supply_authorized_processed_value_fingerprint_or_authorized_private_source_pointer", "owner action mismatch", errors)
        for forbidden_key in ("raw_value", "normalized_value", "processed_value", "business_value", "value"):
            require(forbidden_key not in item, f"value-bearing key must not be in owner worklist: {forbidden_key}", errors)


def validate_v014_private_processed_value_source_map_gap_resolution(
    manifest_path: Path = MANIFEST_PATH,
    *,
    require_private_owner_worklist: bool = False,
) -> dict[str, Any]:
    errors: list[str] = []
    manifest = read_json(manifest_path)
    go_no_go = read_json(GO_NO_GO_PATH)
    summary = read_json(SUMMARY_PATH)
    gap_matrix = read_json(GAP_MATRIX_PATH)
    metadata_manifest = read_json(METADATA_MANIFEST_PATH)
    metadata_go_no_go = read_json(METADATA_GO_NO_GO_PATH)
    metadata_summary = read_json(METADATA_SUMMARY_PATH)
    metadata_gap_matrix = read_json(METADATA_GAP_MATRIX_PATH)

    require(metadata_manifest == manifest, "metadata manifest copy mismatch", errors)
    require(metadata_go_no_go == go_no_go, "metadata go/no-go copy mismatch", errors)
    require(metadata_summary == summary, "metadata summary copy mismatch", errors)
    require(metadata_gap_matrix == gap_matrix, "metadata gap matrix copy mismatch", errors)

    require(manifest.get("schema_version") == SCHEMA_VERSION, "schema mismatch", errors)
    require(manifest.get("project_id") == "KMFA", "project_id mismatch", errors)
    require(manifest.get("version") == "0.1.4", "version mismatch", errors)
    require(manifest.get("phase_id") == PHASE_ID, "phase id mismatch", errors)
    require(manifest.get("task_id") == TASK_ID, "task id mismatch", errors)
    require(manifest.get("acceptance_ids") == [ACCEPTANCE_ID], "acceptance ids mismatch", errors)
    require(manifest.get("status") == STATUS, "status mismatch", errors)
    require(manifest.get("next_recommended_phase") == NEXT_RECOMMENDED_PHASE, "next phase mismatch", errors)
    require(manifest.get("gap_resolution_summary") == summary, "manifest summary mismatch", errors)
    require(manifest.get("gap_resolution_matrix") == gap_matrix, "manifest gap matrix mismatch", errors)
    require(manifest.get("go_no_go") == go_no_go, "manifest go/no-go mismatch", errors)
    require(not _contains_forbidden_public_key(manifest), "forbidden public key present in manifest", errors)
    require(not _contains_forbidden_public_key(gap_matrix), "forbidden public key present in gap matrix", errors)

    require(go_no_go.get("schema_version") == GO_NO_GO_SCHEMA_VERSION, "go/no-go schema mismatch", errors)
    require(go_no_go.get("decision") == "NO_GO", "go/no-go decision mismatch", errors)
    require(go_no_go.get("next_recommended_phase") == NEXT_RECOMMENDED_PHASE, "go/no-go next phase mismatch", errors)
    require(go_no_go.get("unresolved_gap_item_count") == 113, "go/no-go unresolved gap count mismatch", errors)

    expected_summary = {
        "previous_fill_request_item_count": 149,
        "previous_authorized_filled_item_count": 36,
        "previous_authorized_unfilled_item_count": 113,
        "existing_source_map_record_count": 36,
        "unresolved_gap_item_count": 113,
        "unresolved_unique_private_ref_count": 101,
        "duplicate_unresolved_gap_item_count": 12,
        "gap_reason_count": 1,
        "private_owner_worklist_item_count": 113,
        "new_authorized_fingerprint_count": 0,
        "additional_source_map_records_written_count": 0,
    }
    for key, expected in expected_summary.items():
        require(summary.get(key) == expected, f"summary.{key} mismatch", errors)
    require(summary.get("source_root_bucket_count", 0) > 0, "source root bucket count must be positive", errors)
    require(summary.get("context_group_bucket_count", 0) > 0, "context group bucket count must be positive", errors)
    require(summary.get("private_ref_shape_bucket_count", 0) > 0, "shape bucket count must be positive", errors)
    require(summary.get("source_map_gap_resolution_complete") is False, "source map gap resolution must remain incomplete", errors)
    require(summary.get("owner_authorized_fill_intake_required") is True, "owner intake required flag mismatch", errors)
    require(summary.get("metadata_hash_sibling_backfill_required") is True, "metadata backfill required flag mismatch", errors)
    require(summary.get("processed_value_materialization_replay_ready") is False, "materialization ready flag must be false", errors)
    require(summary.get("raw_to_processed_value_comparison_ready") is False, "comparison ready flag must be false", errors)
    require(summary.get("business_value_consistency_verified") is False, "business consistency flag must be false", errors)

    reason_buckets = gap_matrix.get("gap_reason_buckets", [])
    require(isinstance(reason_buckets, list) and len(reason_buckets) == 1, "gap reason bucket count mismatch", errors)
    if isinstance(reason_buckets, list) and reason_buckets:
        bucket = reason_buckets[0]
        require(bucket.get("gap_reason") == "authorized_metadata_hash_sibling_not_found", "gap reason mismatch", errors)
        require(bucket.get("gap_item_count") == 113, "gap reason count mismatch", errors)
        require(bucket.get("auto_fill_allowed") is False, "auto fill must be false", errors)
    lanes = gap_matrix.get("resolution_lanes", [])
    require(isinstance(lanes, list) and len(lanes) == 3, "resolution lane count mismatch", errors)

    for key in (
        "processed_value_materialization_replay_allowed",
        "raw_to_processed_value_comparison_allowed",
        "business_value_consistency_verified",
        "lineage_full_check_complete",
        "formal_report_allowed",
        "github_upload_allowed",
        "app_reinstall_allowed",
        "business_execution_allowed",
    ):
        require(go_no_go.get(key) is False, f"go_no_go.{key} must be false", errors)

    scope = manifest.get("phase_scope_controls", {})
    for key in (
        "current_phase_only",
        "gap_resolution_only",
        "previous_authorized_fill_consumed",
        "previous_capture_diagnostic_consumed",
        "private_owner_worklist_written",
        "public_gap_matrix_written",
    ):
        require(scope.get(key) is True, f"phase_scope_controls.{key} must be true", errors)
    for key in (
        "new_fingerprints_materialized",
        "processed_value_materialization_replay_performed",
        "raw_to_processed_value_comparison_performed",
        "processed_data_reconciliation_performed",
        "lineage_full_check_performed",
        "formal_report_performed",
        "github_upload_performed",
        "app_reinstall_performed",
        "business_execution_performed",
        "next_phase_started",
    ):
        require(scope.get(key) is False, f"phase_scope_controls.{key} must be false", errors)

    for key, value in manifest.get("raw_readonly_boundary", {}).items():
        require(value is False, f"raw_readonly_boundary.{key} must be false", errors)

    safety = manifest.get("public_repo_safety", {})
    require(safety.get("public_safe_aggregate_only") is True, "public safe aggregate flag mismatch", errors)
    for key, value in safety.items():
        if key == "public_safe_aggregate_only":
            continue
        require(value is False, f"public_repo_safety.{key} must be false", errors)

    for path in (
        MANIFEST_PATH,
        GO_NO_GO_PATH,
        SUMMARY_PATH,
        GAP_MATRIX_PATH,
        REPORT_PATH,
        GO_NO_GO_RECORD_PATH,
        TEST_RESULTS_PATH,
        RISK_REGISTER_PATH,
        ROLLBACK_PATH,
        METADATA_MANIFEST_PATH,
        METADATA_GO_NO_GO_PATH,
        METADATA_SUMMARY_PATH,
        METADATA_GAP_MATRIX_PATH,
    ):
        check_public_evidence_text(path, errors)

    tracked = git_output(["ls-files", "KMFA"])
    for line in tracked.splitlines():
        lower = line.lower()
        require(".codex_private_runtime/" not in line, f"private runtime file is tracked: {line}", errors)
        require(not lower.endswith(FORBIDDEN_TRACKED_SUFFIXES), f"forbidden tracked raw/private artifact: {line}", errors)

    check_private_worklist(
        require_private_owner_worklist=require_private_owner_worklist,
        expected_count=int(summary.get("private_owner_worklist_item_count", 0)),
        errors=errors,
    )

    if errors:
        raise ValidationError("\n".join(errors))
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-private-owner-worklist", action="store_true")
    args = parser.parse_args(argv)
    manifest = validate_v014_private_processed_value_source_map_gap_resolution(
        require_private_owner_worklist=args.require_private_owner_worklist
    )
    summary = manifest["gap_resolution_summary"]
    print(
        "PASS: KMFA v0.1.4 source-map authorized-fill gap resolution validated "
        f"(unresolved={summary['unresolved_gap_item_count']}, "
        f"unique={summary['unresolved_unique_private_ref_count']}, "
        "owner_intake=true, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
