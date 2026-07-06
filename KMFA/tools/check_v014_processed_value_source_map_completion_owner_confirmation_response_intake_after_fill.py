#!/usr/bin/env python3
"""Validate KMFA v0.1.4 owner confirmation response intake after fill."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PHASE_ID = "V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_OWNER_CONFIRMATION_RESPONSE_INTAKE_AFTER_FILL"
VERSION = "0.1.4-owner-confirmation-response-intake-after-fill"
DIAGNOSTIC_CONCLUSION = "owner_confirmation_responses_default_filled_keep_no_go"
NEXT_REQUIRED_INPUT = "non_actionable_groups_remain_unresolved_or_excluded_before_full_source_map_application"
DEFAULT_AUTHORITY_BASIS = "owner_delegated_codex_conservative_default_keep_no_go_no_raw_read"
DEFAULT_RESPONSE_CHOICE_CODE = "KEEP_PENDING"
DEFAULT_REASON_CODE = "OWNER_DELEGATED_CODEX_CONSERVATIVE_DEFAULT_KEEP_NO_GO"

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
QUALITY_DIR = PROJECT_ROOT / "metadata" / "quality"
PRIVATE_DIR = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_processed_value_source_map_completion_owner_confirmation_response_intake_after_fill"
)
PRIVATE_FILLED_DRAFT_PATH = PRIVATE_DIR / "private_owner_confirmation_response_draft_after_codex_default_fill.json"
PRIVATE_VALID_RESPONSE_QUEUE_PATH = PRIVATE_DIR / "private_owner_confirmation_valid_response_queue_after_fill.json"
PRIVATE_PENDING_RESPONSE_QUEUE_PATH = PRIVATE_DIR / "private_owner_confirmation_pending_response_queue_after_fill.json"
PRIVATE_DIAGNOSTIC_PATH = PRIVATE_DIR / "private_owner_confirmation_response_intake_after_fill_diagnostic.json"

SUMMARY_PATH = MACHINE_DIR / "processed_value_source_map_completion_owner_confirmation_response_intake_after_fill_summary.json"
MANIFEST_PATH = MACHINE_DIR / "processed_value_source_map_completion_owner_confirmation_response_intake_after_fill_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "processed_value_source_map_completion_owner_confirmation_response_intake_after_fill_go_no_go_report.json"

PUBLIC_ARTIFACTS = [
    SUMMARY_PATH,
    MANIFEST_PATH,
    GO_NO_GO_PATH,
    HUMAN_DIR / "processed_value_source_map_completion_owner_confirmation_response_intake_after_fill_report.md",
    HUMAN_DIR / "go_no_go_record.md",
    HUMAN_DIR / "test_results.md",
    HUMAN_DIR / "risk_register.md",
    HUMAN_DIR / "rollback_plan.md",
    QUALITY_DIR / "v014_owner_confirmation_response_intake_after_fill_summary.json",
    QUALITY_DIR / "v014_owner_confirmation_response_intake_after_fill_manifest.json",
    QUALITY_DIR / "v014_owner_confirmation_response_intake_after_fill_go_no_go_report.json",
]

FORBIDDEN_PUBLIC_PATTERNS = [
    re.compile(r"/Users/linzezhang/Downloads"),
    re.compile(r"KMFA_MetaData"),
    re.compile(r"\.(xlsx|xlsm|xls|zip|pdf)\b", re.IGNORECASE),
    re.compile(
        r'"(target_slot_id|target_slot_ids|review_group_id|raw_file_name|archive_member_name|sheet_name|cell_address|raw_value|normalized_decimal|context_text)"',
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


def _git_check_ignored(path: Path) -> bool:
    return subprocess.run(["git", "check-ignore", "-q", path.as_posix()], check=False).returncode == 0


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
    result = subprocess.run(
        ["git", "ls-files", "KMFA"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise ValidationError(result.stderr.strip() or "git ls-files failed")
    forbidden = re.compile(r"\.codex_private_runtime|/Users/linzezhang/Downloads|KMFA_MetaData|\.(zip|xlsx|xlsm|xls|pdf|sqlite|sqlite3|db|key|pem|p12|pfx)$", re.IGNORECASE)
    matches = [line for line in result.stdout.splitlines() if forbidden.search(line)]
    if matches:
        raise ValidationError("tracked raw/private files detected: " + ", ".join(matches[:10]))


def _check_private_after_fill() -> None:
    for path in (
        PRIVATE_FILLED_DRAFT_PATH,
        PRIVATE_VALID_RESPONSE_QUEUE_PATH,
        PRIVATE_PENDING_RESPONSE_QUEUE_PATH,
        PRIVATE_DIAGNOSTIC_PATH,
    ):
        if not path.exists():
            raise ValidationError(f"missing private after-fill artifact: {path}")
        if not _git_check_ignored(path):
            raise ValidationError(f"private after-fill artifact is not gitignored: {path}")
    filled = _read_json(PRIVATE_FILLED_DRAFT_PATH)
    valid_queue = _read_json(PRIVATE_VALID_RESPONSE_QUEUE_PATH)
    pending_queue = _read_json(PRIVATE_PENDING_RESPONSE_QUEUE_PATH)
    diagnostic = _read_json(PRIVATE_DIAGNOSTIC_PATH)
    _require_true("filled.default_fill.performed", filled.get("default_fill", {}).get("performed"))
    _require_equal("filled.default_fill.authority_basis", filled.get("default_fill", {}).get("authority_basis"), DEFAULT_AUTHORITY_BASIS)
    _require_equal("filled.default_fill.filled_item_count", filled.get("default_fill", {}).get("filled_item_count"), 3)
    _require_equal("filled.default_fill.choice_code_counts", filled.get("default_fill", {}).get("choice_code_counts"), {DEFAULT_RESPONSE_CHOICE_CODE: 3})
    _require_equal("valid_queue.valid_count", valid_queue.get("valid_owner_confirmation_response_count"), 3)
    _require_equal("pending_queue.pending_count", pending_queue.get("pending_owner_confirmation_response_count"), 0)
    _require_equal("diagnostic.valid_count", diagnostic.get("valid_owner_confirmation_response_count"), 3)
    _require_equal("diagnostic.pending_count", diagnostic.get("pending_owner_confirmation_response_count"), 0)
    _require_false("diagnostic.active_ready", diagnostic.get("active_owner_authorized_fill_record_ready"))
    _check_raw_boundary(diagnostic.get("raw_boundary", {}))


def validate(*, require_private_after_fill: bool = False) -> dict[str, Any]:
    summary = _read_json(SUMMARY_PATH)
    manifest = _read_json(MANIFEST_PATH)
    go_no_go = _read_json(GO_NO_GO_PATH)
    _require_equal("summary.phase_id", summary.get("phase_id"), PHASE_ID)
    _require_equal("summary.version", summary.get("version"), VERSION)
    _require_equal("summary.decision", summary.get("decision"), "NO_GO")
    _require_equal("summary.diagnostic_conclusion", summary.get("diagnostic_conclusion"), DIAGNOSTIC_CONCLUSION)
    _require_equal("summary.source_pending_count", summary.get("source_pending_owner_confirmation_response_count"), 3)
    _require_equal("summary.source_draft_count", summary.get("source_response_draft_item_count"), 3)
    _require_true("summary.default_fill", summary.get("default_confirmation_fill_performed"))
    _require_equal("summary.default_authority", summary.get("default_confirmation_fill_authority_basis"), DEFAULT_AUTHORITY_BASIS)
    _require_equal("summary.default_choice_counts", summary.get("default_confirmation_choice_code_counts"), {DEFAULT_RESPONSE_CHOICE_CODE: 3})
    _require_equal("summary.default_reason_counts", summary.get("default_confirmation_reason_code_counts"), {DEFAULT_REASON_CODE: 3})
    _require_true("summary.owner_response_supplied", summary.get("owner_confirmation_response_supplied"))
    _require_equal("summary.valid_count", summary.get("valid_owner_confirmation_response_count"), 3)
    _require_equal("summary.pending_count", summary.get("pending_owner_confirmation_response_count"), 0)
    _require_equal("summary.invalid_count", summary.get("invalid_owner_confirmation_response_count"), 0)
    for key in (
        "active_owner_authorized_fill_record_ready",
        "active_owner_authorized_fill_record_written",
        "canonical_source_map_mutated",
        "source_map_completion_reapplication_ready",
        "source_map_completion_reapplication_performed",
        "processed_value_materialization_replay_performed",
        "raw_to_processed_value_comparison_performed",
        "business_value_consistency_verified",
        "lineage_full_check_complete",
        "formal_report_allowed",
        "github_upload_performed",
        "app_reinstall_performed",
        "business_execution_performed",
    ):
        _require_false(f"summary.{key}", summary.get(key))
    _require_equal("summary.canonical_source_map_records_applied_count", summary.get("canonical_source_map_records_applied_count"), 0)
    for key in (
        "private_source_response_packet_gitignored",
        "private_source_response_draft_gitignored",
        "private_filled_draft_written",
        "private_filled_draft_gitignored",
        "private_valid_response_queue_written",
        "private_valid_response_queue_gitignored",
        "private_pending_response_queue_written",
        "private_pending_response_queue_gitignored",
        "private_diagnostic_written",
        "private_diagnostic_gitignored",
    ):
        _require_true(f"summary.{key}", summary.get(key))
    _check_raw_boundary(summary.get("raw_boundary", {}))
    _check_public_safety(summary.get("public_safety", {}))
    _require_equal("go_no_go.decision", go_no_go.get("decision"), "NO_GO")
    _require_true("go_no_go.default_fill", go_no_go.get("default_confirmation_fill_performed"))
    _require_true("go_no_go.owner_response_supplied", go_no_go.get("owner_confirmation_response_supplied"))
    _require_equal("go_no_go.valid_count", go_no_go.get("valid_owner_confirmation_response_count"), 3)
    _require_equal("go_no_go.pending_count", go_no_go.get("pending_owner_confirmation_response_count"), 0)
    _require_equal("go_no_go.blocked_until", go_no_go.get("blocked_until"), NEXT_REQUIRED_INPUT)
    for key in (
        "active_owner_authorized_fill_record_ready",
        "source_map_completion_reapplication_ready",
        "raw_to_processed_value_comparison_performed",
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
    if require_private_after_fill:
        _check_private_after_fill()
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-private-after-fill", action="store_true")
    args = parser.parse_args()
    manifest = validate(require_private_after_fill=args.require_private_after_fill)
    print(
        "PASS: KMFA v0.1.4 owner confirmation response intake after fill validated "
        f"(decision={manifest['go_no_go']['decision']}, "
        f"valid={manifest['summary']['valid_owner_confirmation_response_count']}, "
        f"pending={manifest['summary']['pending_owner_confirmation_response_count']})"
    )


if __name__ == "__main__":
    main()
