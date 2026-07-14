#!/usr/bin/env python3
"""Validate KMFA v0.1.4 private raw-comparison preflight."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PHASE_ID = "V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_PRIVATE_RAW_COMPARISON_PREFLIGHT"
VERSION = "0.1.4-private-raw-comparison-preflight"
DIAGNOSTIC_CONCLUSION = "private_raw_inventory_hash_preflight_ready_value_matching_still_blocked"
PREVIOUS_REQUIRED_INPUT = "private_raw_comparison_preflight_before_any_raw_value_matching_or_delivery_claim"
NEXT_REQUIRED_INPUT = "private_raw_value_matching_dry_run_before_any_delivery_claim"

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
QUALITY_DIR = PROJECT_ROOT / "metadata" / "quality"
PRIVATE_DIR = PROJECT_ROOT / ".codex_private_runtime/v014_processed_value_source_map_completion_private_raw_comparison_preflight"
PRIVATE_RAW_MANIFEST_PATH = PRIVATE_DIR / "private_raw_inventory_manifest.json"
PRIVATE_RAW_MANIFEST_JSONL_PATH = PRIVATE_DIR / "private_raw_inventory_records.jsonl"
PRIVATE_PREFLIGHT_DIAGNOSTIC_PATH = PRIVATE_DIR / "private_raw_comparison_preflight_diagnostic.json"
PRIVATE_PREFLIGHT_MARKDOWN_PATH = PRIVATE_DIR / "private_raw_comparison_preflight.md"

SUMMARY_PATH = MACHINE_DIR / "processed_value_source_map_completion_private_raw_comparison_preflight_summary.json"
MANIFEST_PATH = MACHINE_DIR / "processed_value_source_map_completion_private_raw_comparison_preflight_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "processed_value_source_map_completion_private_raw_comparison_preflight_go_no_go_report.json"

PUBLIC_ARTIFACTS = [
    SUMMARY_PATH,
    MANIFEST_PATH,
    GO_NO_GO_PATH,
    HUMAN_DIR / "processed_value_source_map_completion_private_raw_comparison_preflight_report.md",
    HUMAN_DIR / "private_raw_comparison_preflight_public_safe.md",
    HUMAN_DIR / "go_no_go_record.md",
    HUMAN_DIR / "test_results.md",
    HUMAN_DIR / "risk_register.md",
    HUMAN_DIR / "rollback_plan.md",
    QUALITY_DIR / "v014_private_raw_comparison_preflight_summary.json",
    QUALITY_DIR / "v014_private_raw_comparison_preflight_manifest.json",
    QUALITY_DIR / "v014_private_raw_comparison_preflight_go_no_go_report.json",
]

FORBIDDEN_PUBLIC_PATTERNS = [
    re.compile(r"/Users/linzezhang/Downloads"),
    re.compile(r"KMFA_MetaData"),
    re.compile(r"\.(xlsx|xlsm|xls|zip|pdf)\b", re.IGNORECASE),
    re.compile(
        r'"(relative_path|file_name|raw_root_path|raw_file_name|archive_member_name|sheet_name|cell_address|raw_value|normalized_decimal|context_text|sha256_private)"',
        re.IGNORECASE,
    ),
    re.compile(r"sha256:[0-9a-f]{64}"),
    re.compile(r'"[0-9a-f]{64}"'),
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


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise ValidationError(f"missing JSONL artifact: {path}")
    records: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValidationError(f"{path} must contain JSON objects")
        records.append(value)
    return records


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
    for key in (
        "raw_root_exists_checked_by_this_phase",
        "raw_inbox_list_performed_by_this_phase",
        "raw_inbox_file_stat_performed_by_this_phase",
        "raw_inbox_hash_or_value_fingerprint_performed_by_this_phase",
        "raw_inbox_file_content_hash_performed_by_this_phase",
    ):
        _require_true(f"raw_boundary.{key}", raw_boundary.get(key))
    for key in (
        "raw_inbox_parse_performed_by_this_phase",
        "raw_inbox_field_or_header_read_performed_by_this_phase",
        "raw_inbox_value_extraction_performed_by_this_phase",
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


def _check_private_manifest() -> None:
    manifest = _read_json(PRIVATE_RAW_MANIFEST_PATH)
    records = _read_jsonl(PRIVATE_RAW_MANIFEST_JSONL_PATH)
    diagnostic = _read_json(PRIVATE_PREFLIGHT_DIAGNOSTIC_PATH)
    markdown = PRIVATE_PREFLIGHT_MARKDOWN_PATH.read_text(encoding="utf-8") if PRIVATE_PREFLIGHT_MARKDOWN_PATH.exists() else ""
    _require_equal("private manifest.phase_id", manifest.get("phase_id"), PHASE_ID)
    _require_equal("diagnostic.phase_id", diagnostic.get("phase_id"), PHASE_ID)
    inventory = manifest.get("inventory_summary", {})
    _require_true("inventory.raw_root_exists", inventory.get("raw_root_exists"))
    _require_true("inventory.raw_root_is_directory", inventory.get("raw_root_is_directory"))
    file_count = inventory.get("file_count")
    _require_equal("records length", len(records), file_count)
    if not isinstance(file_count, int) or file_count <= 0:
        raise ValidationError("private raw inventory must contain at least one file")
    if not isinstance(inventory.get("directory_count"), int):
        raise ValidationError("private raw directory count must be an integer")
    if not isinstance(inventory.get("total_size_bytes"), int) or inventory["total_size_bytes"] <= 0:
        raise ValidationError("private raw total size must be positive")
    if not isinstance(inventory.get("type_bucket_counts"), dict) or not inventory["type_bucket_counts"]:
        raise ValidationError("private type bucket counts must be non-empty")
    for record in records:
        for key in ("relative_path", "file_name", "type_bucket", "size_bytes", "mtime_ns", "sha256_private"):
            if key not in record:
                raise ValidationError(f"private raw record missing {key}")
        if not re.fullmatch(r"[0-9a-f]{64}", str(record["sha256_private"])):
            raise ValidationError("private raw record has invalid sha256")
    _require_true("diagnostic.raw_inventory_ready", diagnostic.get("raw_inventory_ready"))
    _require_equal("diagnostic.record_count", diagnostic.get("raw_manifest_record_count"), file_count)
    _require_true("diagnostic.stable", diagnostic.get("raw_root_stable_after_inventory"))
    _require_false("diagnostic.value_matching_allowed", diagnostic.get("raw_value_matching_allowed_by_this_phase"))
    _require_false("diagnostic.delivery_allowed", diagnostic.get("delivery_allowed"))
    _check_raw_boundary(manifest.get("raw_boundary", {}))
    _check_raw_boundary(diagnostic.get("raw_boundary", {}))
    if "Private Raw Comparison Preflight" not in markdown:
        raise ValidationError("private markdown missing title")
    for path in (
        PRIVATE_RAW_MANIFEST_PATH,
        PRIVATE_RAW_MANIFEST_JSONL_PATH,
        PRIVATE_PREFLIGHT_DIAGNOSTIC_PATH,
        PRIVATE_PREFLIGHT_MARKDOWN_PATH,
    ):
        if not path.exists():
            raise ValidationError(f"missing private artifact: {path}")
        if not _git_check_ignored(path):
            raise ValidationError(f"private artifact is not gitignored: {path}")
        _require_equal(f"{path}.tracked", _git_output(["ls-files", path.as_posix()]), "")


def validate(*, require_private_manifest: bool = False) -> dict[str, Any]:
    summary = _read_json(SUMMARY_PATH)
    manifest = _read_json(MANIFEST_PATH)
    go_no_go = _read_json(GO_NO_GO_PATH)
    metadata_summary = _read_json(QUALITY_DIR / "v014_private_raw_comparison_preflight_summary.json")
    metadata_manifest = _read_json(QUALITY_DIR / "v014_private_raw_comparison_preflight_manifest.json")
    metadata_go_no_go = _read_json(QUALITY_DIR / "v014_private_raw_comparison_preflight_go_no_go_report.json")
    _require_equal("metadata summary", metadata_summary, summary)
    _require_equal("metadata manifest", metadata_manifest, manifest)
    _require_equal("metadata go/no-go", metadata_go_no_go, go_no_go)
    _require_equal("summary.phase_id", summary.get("phase_id"), PHASE_ID)
    _require_equal("summary.version", summary.get("version"), VERSION)
    _require_equal("summary.decision", summary.get("decision"), "NO_GO")
    _require_equal("summary.diagnostic_conclusion", summary.get("diagnostic_conclusion"), DIAGNOSTIC_CONCLUSION)
    _require_true("summary.private_scope_read", summary.get("source_private_scope_read_performed_by_this_phase"))
    _require_equal("summary.previous_required_input", summary.get("previous_required_input"), PREVIOUS_REQUIRED_INPUT)
    _require_true("summary.previous_input_resolved", summary.get("previous_required_input_resolved_by_this_phase"))
    _require_true("summary.raw_inventory_ready", summary.get("raw_inventory_ready"))
    _require_true("summary.raw_manifest_private_written", summary.get("raw_manifest_private_written"))
    if not isinstance(summary.get("raw_manifest_record_count"), int) or summary["raw_manifest_record_count"] <= 0:
        raise ValidationError("summary raw manifest record count must be positive")
    if not isinstance(summary.get("raw_manifest_directory_count"), int):
        raise ValidationError("summary raw directory count must be an integer")
    if not isinstance(summary.get("raw_total_size_bytes"), int) or summary["raw_total_size_bytes"] <= 0:
        raise ValidationError("summary raw total size must be positive")
    if not isinstance(summary.get("raw_type_bucket_counts"), dict) or not summary["raw_type_bucket_counts"]:
        raise ValidationError("summary type bucket counts must be non-empty")
    _require_true("summary.raw_root_exists", summary.get("raw_root_exists_private"))
    _require_true("summary.raw_root_is_directory", summary.get("raw_root_is_directory_private"))
    _require_true("summary.raw_root_stable", summary.get("raw_root_stable_after_inventory"))
    _require_false("summary.value_matching_allowed", summary.get("raw_value_matching_allowed_by_this_phase"))
    _require_false("summary.raw_compare_performed", summary.get("raw_to_processed_value_comparison_performed_by_this_phase"))
    _require_false("summary.raw_field_header_read", summary.get("raw_field_or_header_read_performed_by_this_phase"))
    _require_false("summary.raw_value_extraction", summary.get("raw_value_extraction_performed_by_this_phase"))
    _require_true("summary.dry_run_ready", summary.get("private_raw_value_matching_dry_run_ready"))
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
        "private_raw_manifest_gitignored",
        "private_raw_records_jsonl_written",
        "private_raw_records_jsonl_gitignored",
        "private_diagnostic_written",
        "private_diagnostic_gitignored",
        "private_markdown_written",
        "private_markdown_gitignored",
    ):
        _require_true(f"summary.{key}", summary.get(key))
    _check_public_safety(summary.get("public_safety", {}))
    _check_raw_boundary(summary.get("raw_boundary", {}))
    _require_equal("summary.next_required_input", summary.get("next_required_input"), NEXT_REQUIRED_INPUT)
    _require_equal("go_no_go.decision", go_no_go.get("decision"), "NO_GO")
    _require_equal("go_no_go.blocked_until", go_no_go.get("blocked_until"), NEXT_REQUIRED_INPUT)
    _require_true("go_no_go.raw_inventory_ready", go_no_go.get("raw_inventory_ready"))
    _require_equal("go_no_go.record_count", go_no_go.get("raw_manifest_record_count"), summary["raw_manifest_record_count"])
    _require_true("go_no_go.dry_run_ready", go_no_go.get("private_raw_value_matching_dry_run_ready"))
    for key in (
        "delivery_allowed",
        "github_upload_allowed",
        "app_reinstall_allowed",
        "business_execution_allowed",
    ):
        _require_false(f"go_no_go.{key}", go_no_go.get(key))
    _require_equal("manifest.summary", manifest.get("summary"), summary)
    _require_equal("manifest.go_no_go", manifest.get("go_no_go"), go_no_go)
    _check_public_artifacts()
    _check_no_raw_private_files_tracked()
    if require_private_manifest:
        _check_private_manifest()
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-private-manifest", action="store_true")
    args = parser.parse_args()
    manifest = validate(require_private_manifest=args.require_private_manifest)
    print(
        "PASS: KMFA v0.1.4 private raw comparison preflight validated "
        f"(decision={manifest['go_no_go']['decision']}, "
        f"records={manifest['summary']['raw_manifest_record_count']}, "
        f"dry_run_ready={manifest['summary']['private_raw_value_matching_dry_run_ready']})"
    )


if __name__ == "__main__":
    main()
