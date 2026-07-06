#!/usr/bin/env python3
"""Validate KMFA v0.1.4 outside linked-scope resolution artifacts."""

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

from KMFA.tools.v014_processed_target_outside_linked_scope_resolution import (  # noqa: E402
    DECISION,
    GO_NO_GO_PATH,
    GO_NO_GO_RECORD_PATH,
    MANIFEST_PATH,
    MATRIX_PATH,
    METADATA_GO_NO_GO_PATH,
    METADATA_MANIFEST_PATH,
    METADATA_MATRIX_PATH,
    METADATA_SUMMARY_PATH,
    NEXT_REQUIRED_INPUT,
    PHASE_ID,
    PRIVATE_DIAGNOSTIC_PATH,
    PRIVATE_QUEUE_PATH,
    PRIVATE_REPORT_PATH,
    PRIVATE_RESOLUTION_PATH,
    REPORT_PATH,
    RISK_REGISTER_PATH,
    ROLLBACK_PATH,
    STATUS,
    SUMMARY_PATH,
    TASK_ID,
    TEST_RESULTS_PATH,
    VERSION,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DOWNLOADS_MARKER = "/Users/" + "linzezhang/Downloads"
RAW_INBOX_MARKER = "KMFA" + "_MetaData"
PUBLIC_ARTIFACTS = [
    SUMMARY_PATH,
    MANIFEST_PATH,
    GO_NO_GO_PATH,
    MATRIX_PATH,
    REPORT_PATH,
    GO_NO_GO_RECORD_PATH,
    TEST_RESULTS_PATH,
    RISK_REGISTER_PATH,
    ROLLBACK_PATH,
    METADATA_SUMMARY_PATH,
    METADATA_MANIFEST_PATH,
    METADATA_GO_NO_GO_PATH,
    METADATA_MATRIX_PATH,
]
PRIVATE_ARTIFACTS = [PRIVATE_RESOLUTION_PATH, PRIVATE_DIAGNOSTIC_PATH, PRIVATE_QUEUE_PATH, PRIVATE_REPORT_PATH]
FORBIDDEN_PUBLIC_PATTERNS = [
    re.compile(re.escape(RAW_DOWNLOADS_MARKER)),
    re.compile(re.escape(RAW_INBOX_MARKER)),
    re.compile(re.escape(".codex_private_runtime")),
    re.compile(r"\.(xlsx|xlsm|xls|zip|pdf)\b", re.IGNORECASE),
    re.compile(
        r'"(raw_file_name|archive_member_name|sheet_name|cell_address|raw_value|normalized_decimal|context_text|value_fingerprint|processed_value_fingerprint|private_processed_ref_hash|record_ref_hash|target_key_ref_hash|target_slot_id|source_ref_hash|source_cell_ref_hash|source_sheet_ref_hash|source_record_ref_hash)"',
        re.IGNORECASE,
    ),
    re.compile(r"sha256:[0-9a-f]{64}"),
    re.compile(r'"[0-9a-f]{64}"'),
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
]
FORBIDDEN_PRIVATE_RAW_KEYS = {
    "raw_file_name",
    "archive_member_name",
    "sheet_name",
    "cell_address",
    "raw_value",
    "normalized_decimal",
    "context_text",
}


class ValidationError(Exception):
    pass


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ValidationError(f"missing artifact: {path}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValidationError(f"{path} must contain a JSON object")
    return value


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise ValidationError(f"missing JSONL artifact: {path}")
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValidationError(f"{path} must contain JSON objects")
        rows.append(value)
    return rows


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


def _check_public_artifacts() -> None:
    for path in PUBLIC_ARTIFACTS:
        if not path.exists():
            raise ValidationError(f"missing public artifact: {path}")
        text = path.read_text(encoding="utf-8")
        for pattern in FORBIDDEN_PUBLIC_PATTERNS:
            if pattern.search(text):
                raise ValidationError(f"forbidden public marker {pattern.pattern!r} in {path}")


def _check_no_raw_private_files_tracked() -> None:
    tracked = _git_output(["ls-files", "KMFA"]).splitlines()
    forbidden = re.compile(
        r"\.codex_private_runtime|"
        + re.escape(RAW_DOWNLOADS_MARKER)
        + "|"
        + re.escape(RAW_INBOX_MARKER)
        + r"|\.(zip|xlsx|xlsm|xls|pdf|sqlite|sqlite3|db|key|pem|p12|pfx)$",
        re.IGNORECASE,
    )
    hits = [path for path in tracked if forbidden.search(path)]
    if hits:
        raise ValidationError("tracked raw/private files detected: " + ", ".join(hits[:20]))


def _check_raw_boundary(raw_boundary: dict[str, Any]) -> None:
    for key in (
        "raw_data_root_readonly_policy_active",
        "private_staging_read_by_this_phase",
        "private_source_map_read_by_this_phase",
        "private_unmaterialized_scope_records_read_by_this_phase",
        "private_resolution_queue_written_by_this_phase",
    ):
        _require_true(f"raw_boundary.{key}", raw_boundary.get(key))
    for key in (
        "raw_inbox_read_performed_by_this_phase",
        "raw_inbox_list_performed_by_this_phase",
        "raw_inbox_stat_performed_by_this_phase",
        "raw_inbox_hash_or_value_fingerprint_performed_by_this_phase",
        "raw_inbox_file_content_hash_performed_by_this_phase",
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


def _check_summary(summary: dict[str, Any], matrix: dict[str, Any], go_no_go: dict[str, Any], manifest: dict[str, Any]) -> None:
    _require_equal("summary.phase_id", summary.get("phase_id"), PHASE_ID)
    _require_equal("summary.task_id", summary.get("task_id"), TASK_ID)
    _require_equal("summary.version", summary.get("version"), VERSION)
    _require_equal("summary.status", summary.get("status"), STATUS)
    _require_equal("summary.decision", summary.get("decision"), DECISION)
    _require_true("summary.source_dry_run_passed", summary.get("source_dry_run_passed"))
    _require_equal("summary.processed_target_slot_count", summary.get("processed_target_slot_count"), 149)
    _require_equal("summary.linked_scope_resolved_target_slot_count", summary.get("linked_scope_resolved_target_slot_count"), 77)
    _require_equal("summary.outside_linked_scope_target_slot_count", summary.get("outside_linked_scope_target_slot_count"), 72)
    _require_equal("summary.outside_scope_resolution_queue_record_count", summary.get("outside_scope_resolution_queue_record_count"), 72)
    _require_equal("summary.outside_scope_verified_against_staging_count", summary.get("outside_scope_verified_against_staging_count"), 72)
    _require_equal("summary.outside_scope_already_has_source_map_count", summary.get("outside_scope_already_has_source_map_count"), 0)
    _require_equal("summary.outside_scope_auto_resolvable_count", summary.get("outside_scope_auto_resolvable_count"), 0)
    _require_equal(
        "summary.outside_scope_authorized_source_map_required_count",
        summary.get("outside_scope_authorized_source_map_required_count"),
        72,
    )
    _require_equal("summary.outside_scope_resolution_applied_count", summary.get("outside_scope_resolution_applied_count"), 0)
    _require_equal("summary.outside_scope_resolution_pending_count", summary.get("outside_scope_resolution_pending_count"), 72)
    for key in ("private_resolution_written", "private_resolution_gitignored", "private_resolution_queue_written", "private_resolution_queue_gitignored", "private_diagnostic_written", "private_diagnostic_gitignored"):
        _require_true(f"summary.{key}", summary.get(key))
    for key in (
        "source_map_extension_written_by_this_phase",
        "raw_to_processed_value_comparison_performed_by_this_phase",
        "full_raw_to_processed_value_comparison_complete",
        "full_reconciliation_allowed",
        "business_value_consistency_verified",
        "lineage_full_check_complete",
        "formal_report_allowed",
        "github_upload_performed",
        "app_reinstall_performed",
        "business_execution_performed",
    ):
        _require_false(f"summary.{key}", summary.get(key))
    _require_equal("summary.next_required_input", summary.get("next_required_input"), NEXT_REQUIRED_INPUT)
    _check_raw_boundary(summary["raw_boundary"])
    _check_public_safety(summary["public_safety"])
    _require_equal("matrix.phase_id", matrix.get("phase_id"), PHASE_ID)
    _require_equal("matrix.check_count", matrix.get("outside_scope_resolution_check_count"), 8)
    _require_equal("matrix.pass_count", matrix.get("outside_scope_resolution_check_pass_count"), 8)
    _require_equal("matrix.fail_count", matrix.get("outside_scope_resolution_check_fail_count"), 0)
    _require_equal("go_no_go.next_required_input", go_no_go.get("next_required_input"), NEXT_REQUIRED_INPUT)
    _require_equal("go_no_go.outside", go_no_go.get("outside_linked_scope_target_slot_count"), 72)
    _require_false("go_no_go.source map extension", go_no_go.get("source_map_extension_written_by_this_phase"))
    _require_false("go_no_go.full comparison", go_no_go.get("full_raw_to_processed_value_comparison_complete"))
    _require_equal("manifest.summary", manifest.get("summary"), summary)
    _require_equal("manifest.matrix", manifest.get("matrix"), matrix)
    _require_equal("manifest.go_no_go", manifest.get("go_no_go_report"), go_no_go)


def _check_private_resolution() -> None:
    for path in PRIVATE_ARTIFACTS:
        if not path.exists():
            raise ValidationError(f"missing private artifact: {path}")
        if not _git_check_ignored(path):
            raise ValidationError(f"private artifact is not gitignored: {path}")
    tracked = set(_git_output(["ls-files", "KMFA"]).splitlines())
    for path in PRIVATE_ARTIFACTS:
        if path.as_posix() in tracked:
            raise ValidationError(f"private artifact is tracked: {path}")
    resolution = _read_json(PRIVATE_RESOLUTION_PATH)
    diagnostic = _read_json(PRIVATE_DIAGNOSTIC_PATH)
    queue = _read_jsonl(PRIVATE_QUEUE_PATH)
    _require_equal("private queue count", len(queue), 72)
    for row in queue:
        forbidden = FORBIDDEN_PRIVATE_RAW_KEYS & set(row)
        if forbidden:
            raise ValidationError(f"private queue copied raw fields: {sorted(forbidden)}")
        _require_equal("queue.resolution_status", row.get("resolution_status"), "requires_authorized_source_map_extension")
        _require_false("queue.auto_resolution_allowed", row.get("auto_resolution_allowed"))
        _require_false("queue.source_map_extension_written", row.get("source_map_extension_written_by_this_phase"))
        _require_false("queue.full_reconciliation_allowed", row.get("full_reconciliation_allowed"))
        _require_true("queue.staging_record_present", row.get("staging_record_present"))
        _require_false("queue.existing_source_map_record_present", row.get("existing_source_map_record_present"))
    _require_equal("resolution.queue", resolution.get("resolution_queue"), queue)
    _require_equal("diagnostic.count", diagnostic.get("private_summary", {}).get("outside_scope_resolution_queue_record_count"), 72)


def validate(*, require_private_resolution: bool = False) -> dict[str, Any]:
    _check_public_artifacts()
    _check_no_raw_private_files_tracked()
    summary = _read_json(SUMMARY_PATH)
    manifest = _read_json(MANIFEST_PATH)
    go_no_go = _read_json(GO_NO_GO_PATH)
    matrix = _read_json(MATRIX_PATH)
    _require_equal("metadata summary", _read_json(METADATA_SUMMARY_PATH), summary)
    _require_equal("metadata manifest", _read_json(METADATA_MANIFEST_PATH), manifest)
    _require_equal("metadata go/no-go", _read_json(METADATA_GO_NO_GO_PATH), go_no_go)
    _require_equal("metadata matrix", _read_json(METADATA_MATRIX_PATH), matrix)
    _check_summary(summary, matrix, go_no_go, manifest)
    if require_private_resolution:
        _check_private_resolution()
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--require-private-resolution", action="store_true")
    args = parser.parse_args()
    try:
        manifest = validate(require_private_resolution=args.require_private_resolution)
    except ValidationError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    summary = manifest["summary"]
    print(
        "PASS: KMFA v0.1.4 outside linked-scope resolution artifacts validated "
        f"(outside_scope={summary['outside_linked_scope_target_slot_count']}, "
        f"required_source_map={summary['outside_scope_authorized_source_map_required_count']}, "
        f"decision={summary['decision']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
