#!/usr/bin/env python3
"""Validate KMFA v0.1.4 non-actionable default resolution application."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PHASE_ID = "V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_NON_ACTIONABLE_DEFAULT_RESOLUTION_APPLICATION"
VERSION = "0.1.4-non-actionable-default-resolution-application"
DIAGNOSTIC_CONCLUSION = "non_actionable_default_keep_no_go_resolution_applied_full_reapplication_blocked"
NEXT_REQUIRED_INPUT = "non_actionable_groups_keep_no_go_until_explicit_business_resolution"
DEFAULT_RESOLUTION_CODE = "KEEP_NO_GO_EXCLUDED_FROM_FULL_SOURCE_MAP_APPLICATION"

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
QUALITY_DIR = PROJECT_ROOT / "metadata" / "quality"
PRIVATE_DIR = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_processed_value_source_map_completion_non_actionable_default_resolution_application"
)
PRIVATE_RESULT_PATH = PRIVATE_DIR / "private_non_actionable_default_resolution_application_result.json"
PRIVATE_DIAGNOSTIC_PATH = PRIVATE_DIR / "private_non_actionable_default_resolution_application_diagnostic.json"

SUMMARY_PATH = MACHINE_DIR / "processed_value_source_map_completion_non_actionable_default_resolution_application_summary.json"
MANIFEST_PATH = MACHINE_DIR / "processed_value_source_map_completion_non_actionable_default_resolution_application_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "processed_value_source_map_completion_non_actionable_default_resolution_application_go_no_go_report.json"

PUBLIC_ARTIFACTS = [
    SUMMARY_PATH,
    MANIFEST_PATH,
    GO_NO_GO_PATH,
    HUMAN_DIR / "processed_value_source_map_completion_non_actionable_default_resolution_application_report.md",
    HUMAN_DIR / "go_no_go_record.md",
    HUMAN_DIR / "test_results.md",
    HUMAN_DIR / "risk_register.md",
    HUMAN_DIR / "rollback_plan.md",
    QUALITY_DIR / "v014_non_actionable_default_resolution_application_summary.json",
    QUALITY_DIR / "v014_non_actionable_default_resolution_application_manifest.json",
    QUALITY_DIR / "v014_non_actionable_default_resolution_application_go_no_go_report.json",
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
    for key in (
        "raw_inbox_read_performed_by_this_phase",
        "raw_inbox_list_performed_by_this_phase",
        "raw_inbox_stat_performed_by_this_phase",
        "raw_inbox_hash_or_value_fingerprint_performed_by_this_phase",
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
    forbidden = re.compile(r"\.codex_private_runtime|/Users/linzezhang/Downloads|KMFA_MetaData|\.(zip|xlsx|xlsm|xls|pdf|sqlite|sqlite3|db|key|pem|p12|pfx)$", re.IGNORECASE)
    matches = [path for path in tracked if forbidden.search(path)]
    if matches:
        raise ValidationError("tracked raw/private files detected: " + ", ".join(matches[:10]))


def _check_private_default_resolution() -> None:
    result = _read_json(PRIVATE_RESULT_PATH)
    diagnostic = _read_json(PRIVATE_DIAGNOSTIC_PATH)
    _require_equal("result.phase_id", result.get("phase_id"), PHASE_ID)
    _require_equal("diagnostic.phase_id", diagnostic.get("phase_id"), PHASE_ID)
    result_summary = result.get("result_summary", {})
    _require_equal("private.valid_response_count", result_summary.get("valid_response_count"), 3)
    _require_equal("private.keep_no_go_resolution_count", result_summary.get("keep_no_go_resolution_count"), 3)
    _require_equal("private.active_authorization_allowed_count", result_summary.get("active_authorization_allowed_count"), 0)
    _require_equal("private.canonical_mutation_allowed_count", result_summary.get("canonical_source_map_mutation_allowed_count"), 0)
    _require_equal("private.non_actionable_group_count", result_summary.get("non_actionable_group_count"), 3)
    _require_equal("private.non_actionable_target_slot_count", result_summary.get("non_actionable_target_slot_count"), 12)
    _require_equal("private.actionable_target_slot_count", result_summary.get("actionable_partial_application_target_slot_count"), 101)
    _require_false("private.full_reapplication_ready", result_summary.get("full_source_map_completion_reapplication_ready"))
    _require_false("private.canonical_source_map_mutated", result_summary.get("canonical_source_map_mutated"))
    rows = result.get("resolution_rows", [])
    if not isinstance(rows, list):
        raise ValidationError("private resolution_rows must be a list")
    _require_equal("private.resolution_rows length", len(rows), 3)
    for row in rows:
        if not isinstance(row, dict):
            raise ValidationError("private resolution row must be object")
        _require_equal("private.row.default_resolution_code", row.get("default_resolution_code"), DEFAULT_RESOLUTION_CODE)
        _require_false("private.row.active_authorization_allowed", row.get("active_authorization_allowed_by_resolution"))
        _require_false("private.row.canonical_source_map_mutation_allowed", row.get("canonical_source_map_mutation_allowed_by_resolution"))
        _require_false("private.row.raw_compare_allowed", row.get("raw_compare_allowed_by_resolution"))
    _check_raw_boundary(result.get("raw_boundary", {}))
    _check_raw_boundary(diagnostic.get("raw_boundary", {}))
    for path in (PRIVATE_RESULT_PATH, PRIVATE_DIAGNOSTIC_PATH):
        if not path.exists():
            raise ValidationError(f"missing private artifact: {path}")
        if not _git_check_ignored(path):
            raise ValidationError(f"private artifact is not gitignored: {path}")
        _require_equal(f"{path}.tracked", _git_output(["ls-files", path.as_posix()]), "")


def validate(*, require_private_default_resolution: bool = False) -> dict[str, Any]:
    summary = _read_json(SUMMARY_PATH)
    manifest = _read_json(MANIFEST_PATH)
    go_no_go = _read_json(GO_NO_GO_PATH)
    metadata_summary = _read_json(QUALITY_DIR / "v014_non_actionable_default_resolution_application_summary.json")
    metadata_manifest = _read_json(QUALITY_DIR / "v014_non_actionable_default_resolution_application_manifest.json")
    metadata_go_no_go = _read_json(QUALITY_DIR / "v014_non_actionable_default_resolution_application_go_no_go_report.json")
    _require_equal("metadata summary", metadata_summary, summary)
    _require_equal("metadata manifest", metadata_manifest, manifest)
    _require_equal("metadata go/no-go", metadata_go_no_go, go_no_go)
    _require_equal("summary.phase_id", summary.get("phase_id"), PHASE_ID)
    _require_equal("summary.version", summary.get("version"), VERSION)
    _require_equal("summary.decision", summary.get("decision"), "NO_GO")
    _require_equal("summary.diagnostic_conclusion", summary.get("diagnostic_conclusion"), DIAGNOSTIC_CONCLUSION)
    _require_equal("summary.source_after_fill_valid", summary.get("source_after_fill_valid_owner_confirmation_response_count"), 3)
    _require_equal("summary.source_after_fill_pending", summary.get("source_after_fill_pending_owner_confirmation_response_count"), 0)
    _require_true("summary.application_performed", summary.get("non_actionable_default_resolution_application_performed"))
    _require_equal("summary.default_resolution_code", summary.get("non_actionable_default_resolution_code"), DEFAULT_RESOLUTION_CODE)
    _require_equal("summary.item_count", summary.get("non_actionable_default_resolution_item_count"), 3)
    _require_equal("summary.keep_no_go_count", summary.get("keep_no_go_resolution_count"), 3)
    _require_equal("summary.active_auth_allowed_count", summary.get("non_actionable_active_authorization_allowed_count"), 0)
    _require_equal("summary.canonical_mutation_allowed_count", summary.get("non_actionable_canonical_source_map_mutation_allowed_count"), 0)
    _require_equal("summary.non_actionable_group_count", summary.get("non_actionable_group_count"), 3)
    _require_equal("summary.non_actionable_target_slot_count", summary.get("non_actionable_target_slot_count"), 12)
    _require_equal("summary.actionable_target_slot_count", summary.get("actionable_partial_application_target_slot_count"), 101)
    _require_true("summary.partial_followup_ready", summary.get("partial_followup_evidence_ready_for_blocker_audit"))
    for key in (
        "full_source_map_completion_reapplication_ready",
        "full_raw_to_processed_comparison_ready",
        "canonical_source_map_mutated",
        "processed_value_materialization_replay_performed",
        "raw_to_processed_value_comparison_performed_by_this_phase",
        "business_value_consistency_verified",
        "lineage_full_check_complete",
        "formal_report_allowed",
        "github_upload_performed",
        "app_reinstall_performed",
        "business_execution_performed",
    ):
        _require_false(f"summary.{key}", summary.get(key))
    _require_equal("summary.canonical_records_applied", summary.get("canonical_source_map_records_applied_count"), 0)
    for key in (
        "private_valid_response_queue_gitignored",
        "private_default_resolution_result_written",
        "private_default_resolution_result_gitignored",
        "private_diagnostic_written",
        "private_diagnostic_gitignored",
    ):
        _require_true(f"summary.{key}", summary.get(key))
    _check_public_safety(summary.get("public_safety", {}))
    _check_raw_boundary(summary.get("raw_boundary", {}))
    _require_equal("go_no_go.decision", go_no_go.get("decision"), "NO_GO")
    _require_equal("go_no_go.blocked_until", go_no_go.get("blocked_until"), NEXT_REQUIRED_INPUT)
    _require_true("go_no_go.application_performed", go_no_go.get("non_actionable_default_resolution_application_performed"))
    _require_equal("go_no_go.keep_no_go_count", go_no_go.get("keep_no_go_resolution_count"), 3)
    for key in (
        "full_source_map_completion_reapplication_ready",
        "canonical_source_map_mutated",
        "raw_to_processed_value_comparison_performed_by_this_phase",
        "business_value_consistency_verified",
        "github_upload_performed",
        "app_reinstall_performed",
        "business_execution_performed",
    ):
        _require_false(f"go_no_go.{key}", go_no_go.get(key))
    _require_equal("manifest.summary", manifest.get("summary"), summary)
    _require_equal("manifest.go_no_go", manifest.get("go_no_go"), go_no_go)
    _check_public_artifacts()
    _check_no_raw_private_files_tracked()
    if require_private_default_resolution:
        _check_private_default_resolution()
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-private-default-resolution", action="store_true")
    args = parser.parse_args()
    manifest = validate(require_private_default_resolution=args.require_private_default_resolution)
    print(
        "PASS: KMFA v0.1.4 non-actionable default resolution application validated "
        f"(decision={manifest['go_no_go']['decision']}, "
        f"keep_no_go={manifest['summary']['keep_no_go_resolution_count']}, "
        f"blocked_slots={manifest['summary']['non_actionable_target_slot_count']})"
    )


if __name__ == "__main__":
    main()
