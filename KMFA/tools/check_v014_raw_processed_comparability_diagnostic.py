#!/usr/bin/env python3
"""Validate KMFA v0.1.4 raw/processed comparability diagnostic evidence."""

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

from KMFA.tools.v014_raw_processed_comparability_diagnostic import (  # noqa: E402
    ACCEPTANCE_ID,
    GO_NO_GO_PATH,
    GO_NO_GO_RECORD_PATH,
    GO_NO_GO_SCHEMA_VERSION,
    MANIFEST_PATH,
    METADATA_GO_NO_GO_PATH,
    METADATA_MANIFEST_PATH,
    METADATA_SUMMARY_PATH,
    NEXT_REQUIRED_INPUT,
    PHASE_ID,
    PRIVATE_DIAGNOSTIC_PATH,
    PRIVATE_LOCAL_REPORT_PATH,
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
    "raw_filename",
    "zip_member_name",
    "sheet_name",
    "cell_value",
    "row_value",
    "raw_value",
    "normalized_value",
    "business_value",
    "private_processed_ref",
    "raw_private_file_hash_records",
    "raw_private_snapshot",
    "sha256",
    "path_hash",
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
    "sheet name",
    "cell value",
    "row value",
    "raw filename",
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


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


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
    result = subprocess.run(["git", "check-ignore", "-q", str(path)], check=False)
    return result.returncode == 0


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


def validate_summary(summary: dict[str, Any], errors: list[str]) -> None:
    walk_forbidden_public_keys(summary, errors)
    expected = {
        "record_type": "v014_raw_processed_comparability_diagnostic_summary",
        "schema_version": SCHEMA_VERSION,
        "project_id": "KMFA",
        "version": "0.1.4",
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "status": STATUS,
        "raw_root_exists": True,
        "raw_root_file_count": 5,
        "raw_root_private_hash_record_count": 5,
        "raw_root_stat_unchanged_after_phase": True,
        "raw_inbox_mutation_detected": False,
        "prior_raw_value_fingerprint_record_count": 871,
        "prior_raw_unique_numeric_fingerprint_count": 330,
        "processed_target_slot_count": 149,
        "staged_processed_value_fingerprint_count": 0,
        "existing_processed_source_map_record_count": 36,
        "existing_processed_source_map_unique_fingerprint_count": 36,
        "unresolved_owner_worklist_item_count": 113,
        "active_fill_record_item_count": 113,
        "active_fill_record_keep_pending_count": 113,
        "raw_processed_staged_fingerprint_overlap_count": 0,
        "raw_processed_source_map_fingerprint_overlap_count": 0,
        "raw_structural_key_count": 248,
        "processed_structural_key_count": 202,
        "raw_processed_structural_key_intersection_count": 0,
        "comparable_value_pair_count": 0,
        "business_value_consistency_verified": False,
        "raw_to_processed_value_comparison_performed": False,
        "source_map_gap_resolution_complete": False,
        "diagnostic_conclusion": "blocked_no_authorized_processed_value_source_map",
        "blocker": "processed_target_slots_lack_authorized_value_fingerprints_and_shared_raw_join_keys",
        "next_required_input": NEXT_REQUIRED_INPUT,
    }
    for key, value in expected.items():
        require(summary.get(key) == value, f"summary {key} mismatch: {summary.get(key)!r} != {value!r}", errors)


def validate_go_no_go(go_no_go: dict[str, Any], errors: list[str]) -> None:
    walk_forbidden_public_keys(go_no_go, errors)
    require(go_no_go.get("record_type") == "v014_raw_processed_comparability_diagnostic_go_no_go", "go/no-go record_type mismatch", errors)
    require(go_no_go.get("schema_version") == GO_NO_GO_SCHEMA_VERSION, "go/no-go schema mismatch", errors)
    require(go_no_go.get("phase_id") == PHASE_ID, "go/no-go phase mismatch", errors)
    require(go_no_go.get("task_id") == TASK_ID, "go/no-go task mismatch", errors)
    require(go_no_go.get("decision") == "NO_GO", "decision must be NO_GO", errors)
    require(go_no_go.get("comparable_value_pair_count") == 0, "comparable pairs must be zero", errors)
    require(go_no_go.get("business_value_consistency_verified") is False, "business consistency must be false", errors)
    require(go_no_go.get("raw_to_processed_value_comparison_performed") is False, "comparison must not be performed", errors)
    require(go_no_go.get("github_upload_performed") is False, "github upload must be false", errors)
    require(go_no_go.get("app_reinstall_performed") is False, "app reinstall must be false", errors)
    require(go_no_go.get("business_execution_performed") is False, "business execution must be false", errors)
    require(go_no_go.get("next_required_input") == NEXT_REQUIRED_INPUT, "next input mismatch", errors)


def validate_manifest(manifest: dict[str, Any], summary: dict[str, Any], go_no_go: dict[str, Any], errors: list[str]) -> None:
    walk_forbidden_public_keys(manifest, errors)
    require(manifest.get("record_type") == "v014_raw_processed_comparability_diagnostic_manifest", "manifest record_type mismatch", errors)
    require(manifest.get("schema_version") == SCHEMA_VERSION, "manifest schema mismatch", errors)
    require(manifest.get("acceptance_id") == ACCEPTANCE_ID, "acceptance mismatch", errors)
    require(manifest.get("status") == STATUS, "status mismatch", errors)
    require(manifest.get("summary") == summary, "embedded summary mismatch", errors)
    require(manifest.get("go_no_go") == go_no_go, "embedded go/no-go mismatch", errors)
    controls = manifest.get("scope_controls", {})
    for key in (
        "raw_root_readonly_phase",
        "raw_inbox_read_performed_by_this_phase",
        "raw_inbox_list_performed_by_this_phase",
        "raw_inbox_stat_performed_by_this_phase",
        "raw_inbox_hash_performed_by_this_phase",
    ):
        require(controls.get(key) is True, f"{key} must be true", errors)
    for key in (
        "raw_inbox_write_performed_by_this_phase",
        "raw_inbox_delete_performed_by_this_phase",
        "raw_inbox_move_performed_by_this_phase",
        "raw_inbox_rename_performed_by_this_phase",
        "raw_inbox_copy_performed_by_this_phase",
        "raw_inbox_normalize_performed_by_this_phase",
        "raw_inbox_mutation_performed_by_this_phase",
        "raw_to_processed_value_comparison_performed",
        "business_value_consistency_verified",
        "lineage_full_check_complete",
        "formal_report_allowed",
        "github_upload_performed",
        "app_reinstall_performed",
        "business_execution_performed",
    ):
        require(controls.get(key) is False, f"{key} must be false", errors)


def validate_private_diagnostic(errors: list[str]) -> None:
    require(PRIVATE_DIAGNOSTIC_PATH.exists(), "private diagnostic missing", errors)
    require(PRIVATE_LOCAL_REPORT_PATH.exists(), "private local report missing", errors)
    require(git_check_ignore(PRIVATE_DIAGNOSTIC_PATH), "private diagnostic must be git-ignored", errors)
    require(git_check_ignore(PRIVATE_LOCAL_REPORT_PATH), "private local report must be git-ignored", errors)
    if PRIVATE_DIAGNOSTIC_PATH.exists():
        diagnostic = read_json(PRIVATE_DIAGNOSTIC_PATH)
        require(
            diagnostic.get("classification") == "private_raw_processed_comparability_diagnostic_do_not_commit",
            "private diagnostic classification mismatch",
            errors,
        )
        require(diagnostic.get("raw_processed_structural_key_intersection_count") == 0, "private structural intersection mismatch", errors)
        require(diagnostic.get("raw_inbox_mutation_detected") is False, "private raw mutation mismatch", errors)


def validate_git_boundaries(errors: list[str]) -> None:
    tracked = git_output(["ls-files", "KMFA"]).splitlines()
    forbidden_tracked = [
        path
        for path in tracked
        if path.startswith("KMFA/.codex_private_runtime/")
        or path.lower().endswith(FORBIDDEN_TRACKED_SUFFIXES)
        or "KMFA_MetaData" in path
    ]
    require(not forbidden_tracked, f"forbidden tracked raw/private files: {forbidden_tracked[:5]}", errors)


def validate() -> None:
    errors: list[str] = []
    summary = read_json(SUMMARY_PATH)
    go_no_go = read_json(GO_NO_GO_PATH)
    manifest = read_json(MANIFEST_PATH)
    validate_summary(summary, errors)
    validate_go_no_go(go_no_go, errors)
    validate_manifest(manifest, summary, go_no_go, errors)
    validate_private_diagnostic(errors)
    validate_git_boundaries(errors)
    for metadata_path, source_path in (
        (METADATA_SUMMARY_PATH, SUMMARY_PATH),
        (METADATA_MANIFEST_PATH, MANIFEST_PATH),
        (METADATA_GO_NO_GO_PATH, GO_NO_GO_PATH),
    ):
        require(metadata_path.exists(), f"missing metadata copy: {metadata_path}", errors)
        if metadata_path.exists():
            require(read_json(metadata_path) == read_json(source_path), f"metadata copy mismatch: {metadata_path}", errors)
    for text_path in (REPORT_PATH, GO_NO_GO_RECORD_PATH, TEST_RESULTS_PATH, RISK_REGISTER_PATH, ROLLBACK_PATH):
        check_public_text(text_path, errors)
    if errors:
        raise ValidationError("\n".join(errors))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.parse_args()
    try:
        validate()
    except ValidationError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print("PASS: KMFA v0.1.4 raw/processed comparability diagnostic validated (decision=NO_GO, comparable_pairs=0)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
