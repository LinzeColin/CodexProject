#!/usr/bin/env python3
"""Validate KMFA v0.1.4 corrected-source or raw-scope intake."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PHASE_ID = "V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_CORRECTED_SOURCE_OR_RAW_SCOPE_INTAKE"
VERSION = "0.1.4-corrected-source-or-raw-scope-intake"
DIAGNOSTIC_CONCLUSION = "private_raw_comparison_scope_registered_delivery_still_blocked"
PREVIOUS_REQUIRED_INPUT = "corrected_source_package_or_owner_authorized_private_raw_comparison_scope"
NEXT_REQUIRED_INPUT = "private_raw_comparison_preflight_before_any_raw_value_matching_or_delivery_claim"

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
QUALITY_DIR = PROJECT_ROOT / "metadata" / "quality"
PRIVATE_DIR = PROJECT_ROOT / ".codex_private_runtime/v014_processed_value_source_map_completion_corrected_source_or_raw_scope_intake"
PRIVATE_SCOPE_RECORD_PATH = PRIVATE_DIR / "private_corrected_source_or_raw_scope_intake.json"
PRIVATE_SCOPE_MARKDOWN_PATH = PRIVATE_DIR / "private_corrected_source_or_raw_scope_intake.md"
PRIVATE_DIAGNOSTIC_PATH = PRIVATE_DIR / "private_corrected_source_or_raw_scope_intake_diagnostic.json"

SUMMARY_PATH = MACHINE_DIR / "processed_value_source_map_completion_corrected_source_or_raw_scope_intake_summary.json"
MANIFEST_PATH = MACHINE_DIR / "processed_value_source_map_completion_corrected_source_or_raw_scope_intake_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "processed_value_source_map_completion_corrected_source_or_raw_scope_intake_go_no_go_report.json"
SCOPE_MATRIX_PATH = MACHINE_DIR / "processed_value_source_map_completion_raw_scope_matrix_public_safe.json"

PUBLIC_ARTIFACTS = [
    SUMMARY_PATH,
    MANIFEST_PATH,
    GO_NO_GO_PATH,
    SCOPE_MATRIX_PATH,
    HUMAN_DIR / "processed_value_source_map_completion_corrected_source_or_raw_scope_intake_report.md",
    HUMAN_DIR / "raw_scope_intake_public_safe.md",
    HUMAN_DIR / "go_no_go_record.md",
    HUMAN_DIR / "test_results.md",
    HUMAN_DIR / "risk_register.md",
    HUMAN_DIR / "rollback_plan.md",
    QUALITY_DIR / "v014_corrected_source_or_raw_scope_intake_summary.json",
    QUALITY_DIR / "v014_corrected_source_or_raw_scope_intake_manifest.json",
    QUALITY_DIR / "v014_corrected_source_or_raw_scope_intake_go_no_go_report.json",
    QUALITY_DIR / "v014_raw_scope_matrix_public_safe.json",
]

FORBIDDEN_PUBLIC_PATTERNS = [
    re.compile(r"/Users/linzezhang/Downloads"),
    re.compile(r"KMFA_MetaData"),
    re.compile(r"\.(xlsx|xlsm|xls|zip|pdf)\b", re.IGNORECASE),
    re.compile(
        r'"(target_slot_id|target_slot_ids|review_group_id|response_item_id|raw_file_name|archive_member_name|sheet_name|cell_address|raw_value|normalized_decimal|context_text)"',
        re.IGNORECASE,
    ),
    re.compile(r"sha256:[0-9a-f]{64}"),
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
]


class ValidationError(Exception):
    pass


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ValidationError(f"missing JSON artifact: {path}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValidationError(f"{path} must contain a JSON object")
    return value


def _require_equal(label: str, actual: Any, expected: Any) -> None:
    if actual != expected:
        raise ValidationError(f"{label}: expected {expected!r}, got {actual!r}")


def _require_true(label: str, value: Any) -> None:
    if value is not True:
        raise ValidationError(f"{label}: expected true, got {value!r}")


def _require_false(label: str, value: Any) -> None:
    if value is not False:
        raise ValidationError(f"{label}: expected false, got {value!r}")


def _git_output(args: list[str]) -> str:
    result = subprocess.run(
        ["git", "-c", "core.quotePath=false", *args],
        cwd=PROJECT_ROOT.parent,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise ValidationError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def _git_check_ignored(path: Path) -> bool:
    return subprocess.run(["git", "check-ignore", "-q", path.as_posix()], cwd=PROJECT_ROOT.parent, check=False).returncode == 0


def _check_raw_boundary(raw_boundary: dict[str, Any]) -> None:
    _require_true("raw_boundary.raw_data_root_readonly_policy_active", raw_boundary.get("raw_data_root_readonly_policy_active"))
    _require_true("raw_boundary.raw_root_existence_stat_performed_by_this_phase", raw_boundary.get("raw_root_existence_stat_performed_by_this_phase"))
    for key in (
        "raw_inbox_read_performed_by_this_phase",
        "raw_inbox_list_performed_by_this_phase",
        "raw_inbox_file_stat_performed_by_this_phase",
        "raw_inbox_hash_or_value_fingerprint_performed_by_this_phase",
        "raw_inbox_parse_performed_by_this_phase",
        "raw_inbox_write_performed_by_this_phase",
        "raw_inbox_delete_performed_by_this_phase",
        "raw_inbox_move_performed_by_this_phase",
        "raw_inbox_rename_performed_by_this_phase",
        "raw_inbox_overwrite_performed_by_this_phase",
        "raw_inbox_copy_performed_by_this_phase",
        "raw_inbox_normalize_performed_by_this_phase",
        "raw_inbox_mutated_by_this_phase",
    ):
        _require_false(f"raw_boundary.{key}", raw_boundary.get(key))


def _check_public_safety(public_safety: dict[str, Any]) -> None:
    _require_true("public_safety.public_safe_aggregate_only", public_safety.get("public_safe_aggregate_only"))
    for key, value in public_safety.items():
        if key == "public_safe_aggregate_only":
            continue
        _require_false(f"public_safety.{key}", value)


def _check_public_artifacts() -> None:
    for path in PUBLIC_ARTIFACTS:
        if not path.exists():
            raise ValidationError(f"missing public artifact: {path}")
        text = path.read_text(encoding="utf-8")
        for pattern in FORBIDDEN_PUBLIC_PATTERNS:
            if pattern.search(text):
                raise ValidationError(f"forbidden public pattern {pattern.pattern!r} in {path}")


def _check_no_raw_private_files_tracked() -> None:
    tracked = _git_output(["ls-files", "KMFA"]).splitlines()
    forbidden = re.compile(
        r"\.codex_private_runtime|/Users/linzezhang/Downloads|KMFA_MetaData|\.(zip|xlsx|xlsm|xls|pdf|sqlite|sqlite3|db|key|pem|p12|pfx)$",
        re.IGNORECASE,
    )
    matches = [path for path in tracked if forbidden.search(path)]
    if matches:
        raise ValidationError("tracked raw/private files detected: " + ", ".join(matches[:10]))


def _check_scope_matrix(matrix: dict[str, Any]) -> None:
    _require_equal("scope_matrix.phase_id", matrix.get("phase_id"), PHASE_ID)
    _require_equal("scope_matrix.decision", matrix.get("decision"), "NO_GO")
    _require_equal("scope_matrix.scope_item_count", matrix.get("scope_item_count"), 5)
    _require_equal("scope_matrix.allowed_next_phase", matrix.get("allowed_next_phase"), "V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_PRIVATE_RAW_COMPARISON_PREFLIGHT")
    items = matrix.get("scope_items", [])
    if not isinstance(items, list):
        raise ValidationError("scope matrix items must be a list")
    _require_equal("scope_matrix.items length", len(items), 5)
    by_code = {item.get("scope_code"): item for item in items if isinstance(item, dict)}
    _require_true("root precheck allowed", by_code["RAW_ROOT_EXISTENCE_PRECHECK"].get("allowed_this_phase"))
    _require_true("root precheck performed", by_code["RAW_ROOT_EXISTENCE_PRECHECK"].get("performed_this_phase"))
    for code in (
        "RAW_FILE_LISTING",
        "RAW_FILE_HASHING_OR_PARSE",
        "RAW_TO_PROCESSED_COMPARISON",
    ):
        _require_false(f"{code}.allowed", by_code[code].get("allowed_this_phase"))
        _require_false(f"{code}.performed", by_code[code].get("performed_this_phase"))
    _require_true("corrected source registration allowed", by_code["CORRECTED_SOURCE_PACKAGE_REGISTRATION"].get("allowed_this_phase"))
    _require_false("corrected source registration performed", by_code["CORRECTED_SOURCE_PACKAGE_REGISTRATION"].get("performed_this_phase"))


def _check_private_scope() -> None:
    scope = _read_json(PRIVATE_SCOPE_RECORD_PATH)
    diagnostic = _read_json(PRIVATE_DIAGNOSTIC_PATH)
    markdown = PRIVATE_SCOPE_MARKDOWN_PATH.read_text(encoding="utf-8") if PRIVATE_SCOPE_MARKDOWN_PATH.exists() else ""
    _require_equal("scope.phase_id", scope.get("phase_id"), PHASE_ID)
    _require_equal("diagnostic.phase_id", diagnostic.get("phase_id"), PHASE_ID)
    _require_true("scope.previous_input_resolved", scope.get("previous_required_input_resolved_by_this_phase"))
    _require_false("scope.corrected_source_supplied", scope.get("corrected_source_package_supplied"))
    _require_true("scope.raw_scope_registered", scope.get("owner_authorized_private_raw_comparison_scope_registered"))
    _require_true("scope.raw_root_exists", scope.get("raw_root_exists"))
    _require_true("scope.raw_root_is_directory", scope.get("raw_root_is_directory"))
    _require_true("scope.raw_root_stat", scope.get("raw_root_existence_stat_performed_by_this_phase"))
    _require_false("scope.raw_file_listing", scope.get("raw_file_listing_performed_by_this_phase"))
    _require_false("scope.raw_file_hash_allowed", scope.get("raw_file_hash_or_parse_allowed_by_this_phase"))
    _require_false("scope.raw_compare_allowed", scope.get("raw_to_processed_comparison_allowed_by_this_phase"))
    _require_true("scope.preflight_ready", scope.get("private_raw_comparison_preflight_ready"))
    _require_true("diagnostic.raw_scope_registered", diagnostic.get("raw_scope_registered"))
    _require_true("diagnostic.preflight_ready", diagnostic.get("private_raw_comparison_preflight_ready"))
    _check_scope_matrix(scope.get("public_scope_matrix", {}))
    _check_raw_boundary(scope.get("raw_boundary", {}))
    _check_raw_boundary(diagnostic.get("raw_boundary", {}))
    if "Private Corrected Source Or Raw Scope Intake" not in markdown:
        raise ValidationError("private scope markdown missing title")
    for path in (PRIVATE_SCOPE_RECORD_PATH, PRIVATE_SCOPE_MARKDOWN_PATH, PRIVATE_DIAGNOSTIC_PATH):
        if not path.exists():
            raise ValidationError(f"missing private artifact: {path}")
        if not _git_check_ignored(path):
            raise ValidationError(f"private artifact is not gitignored: {path}")
        _require_equal(f"{path}.tracked", _git_output(["ls-files", path.as_posix()]), "")


def validate(*, require_private_scope: bool = False) -> dict[str, Any]:
    summary = _read_json(SUMMARY_PATH)
    manifest = _read_json(MANIFEST_PATH)
    go_no_go = _read_json(GO_NO_GO_PATH)
    scope_matrix = _read_json(SCOPE_MATRIX_PATH)
    metadata_summary = _read_json(QUALITY_DIR / "v014_corrected_source_or_raw_scope_intake_summary.json")
    metadata_manifest = _read_json(QUALITY_DIR / "v014_corrected_source_or_raw_scope_intake_manifest.json")
    metadata_go_no_go = _read_json(QUALITY_DIR / "v014_corrected_source_or_raw_scope_intake_go_no_go_report.json")
    metadata_scope_matrix = _read_json(QUALITY_DIR / "v014_raw_scope_matrix_public_safe.json")
    _require_equal("metadata summary", metadata_summary, summary)
    _require_equal("metadata manifest", metadata_manifest, manifest)
    _require_equal("metadata go/no-go", metadata_go_no_go, go_no_go)
    _require_equal("metadata scope matrix", metadata_scope_matrix, scope_matrix)
    _require_equal("summary.phase_id", summary.get("phase_id"), PHASE_ID)
    _require_equal("summary.version", summary.get("version"), VERSION)
    _require_equal("summary.decision", summary.get("decision"), "NO_GO")
    _require_equal("summary.diagnostic_conclusion", summary.get("diagnostic_conclusion"), DIAGNOSTIC_CONCLUSION)
    _require_true("summary.private_gap_read", summary.get("source_private_gap_report_read_performed_by_this_phase"))
    _require_equal("summary.previous_required_input", summary.get("previous_required_input"), PREVIOUS_REQUIRED_INPUT)
    _require_true("summary.previous_input_resolved", summary.get("previous_required_input_resolved_by_this_phase"))
    _require_false("summary.corrected_source_supplied", summary.get("corrected_source_package_supplied"))
    _require_true("summary.raw_scope_registered", summary.get("owner_authorized_private_raw_comparison_scope_registered"))
    _require_true("summary.raw_root_exists_private", summary.get("raw_root_exists_private"))
    _require_true("summary.raw_root_is_directory_private", summary.get("raw_root_is_directory_private"))
    _require_true("summary.raw_root_stat", summary.get("raw_root_existence_stat_performed_by_this_phase"))
    _require_false("summary.raw_listing", summary.get("raw_file_listing_performed_by_this_phase"))
    _require_false("summary.raw_hash_parse", summary.get("raw_file_hash_or_parse_performed_by_this_phase"))
    _require_false("summary.raw_compare", summary.get("raw_to_processed_value_comparison_performed_by_this_phase"))
    _require_true("summary.preflight_ready", summary.get("private_raw_comparison_preflight_ready"))
    _require_equal("summary.scope_item_count", summary.get("scope_item_count"), 5)
    for key in (
        "delivery_allowed",
        "formal_report_allowed",
        "github_upload_allowed",
        "github_upload_performed",
        "app_reinstall_allowed",
        "app_reinstall_performed",
        "business_execution_allowed",
        "business_execution_performed",
        "full_source_map_completion_reapplication_ready",
        "full_raw_to_processed_value_comparison_ready",
        "business_value_consistency_verified",
        "canonical_source_map_mutated",
    ):
        _require_false(f"summary.{key}", summary.get(key))
    _require_equal("summary.canonical_records_applied", summary.get("canonical_source_map_records_applied_count"), 0)
    for key in (
        "private_scope_record_written",
        "private_scope_record_gitignored",
        "private_scope_markdown_written",
        "private_scope_markdown_gitignored",
        "private_diagnostic_written",
        "private_diagnostic_gitignored",
    ):
        _require_true(f"summary.{key}", summary.get(key))
    _check_public_safety(summary.get("public_safety", {}))
    _check_raw_boundary(summary.get("raw_boundary", {}))
    _require_equal("summary.next_required_input", summary.get("next_required_input"), NEXT_REQUIRED_INPUT)
    _require_equal("go_no_go.decision", go_no_go.get("decision"), "NO_GO")
    _require_equal("go_no_go.blocked_until", go_no_go.get("blocked_until"), NEXT_REQUIRED_INPUT)
    _require_false("go_no_go.corrected_source_supplied", go_no_go.get("corrected_source_package_supplied"))
    _require_true("go_no_go.preflight_ready", go_no_go.get("private_raw_comparison_preflight_ready"))
    for key in (
        "delivery_allowed",
        "github_upload_allowed",
        "app_reinstall_allowed",
        "business_execution_allowed",
    ):
        _require_false(f"go_no_go.{key}", go_no_go.get(key))
    _require_equal("manifest.summary", manifest.get("summary"), summary)
    _require_equal("manifest.go_no_go", manifest.get("go_no_go"), go_no_go)
    _require_equal("manifest.scope_matrix", manifest.get("scope_matrix"), scope_matrix)
    _check_scope_matrix(scope_matrix)
    _check_public_artifacts()
    _check_no_raw_private_files_tracked()
    if require_private_scope:
        _check_private_scope()
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-private-scope", action="store_true")
    args = parser.parse_args()
    manifest = validate(require_private_scope=args.require_private_scope)
    print(
        "PASS: KMFA v0.1.4 corrected source or raw scope intake validated "
        f"(decision={manifest['go_no_go']['decision']}, "
        f"preflight={manifest['summary']['private_raw_comparison_preflight_ready']}, "
        f"scope_items={manifest['summary']['scope_item_count']})"
    )


if __name__ == "__main__":
    main()
