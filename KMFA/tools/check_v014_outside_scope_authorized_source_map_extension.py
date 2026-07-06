#!/usr/bin/env python3
"""Validate KMFA v0.1.4 outside-scope source-map extension artifacts."""

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

from KMFA.tools.v014_outside_scope_authorized_source_map_extension import (  # noqa: E402
    DECISION,
    DIAGNOSTIC_CONCLUSION,
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
    PRIVATE_PENDING_QUEUE_PATH,
    PRIVATE_REPORT_PATH,
    PRIVATE_TEMPLATE_PATH,
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
PRIVATE_ARTIFACTS = [PRIVATE_TEMPLATE_PATH, PRIVATE_PENDING_QUEUE_PATH, PRIVATE_DIAGNOSTIC_PATH, PRIVATE_REPORT_PATH]
FORBIDDEN_PUBLIC_PATTERNS = [
    re.compile(re.escape(RAW_DOWNLOADS_MARKER)),
    re.compile(re.escape(RAW_INBOX_MARKER)),
    re.compile(re.escape(".codex_private_runtime")),
    re.compile(r"\.(xlsx|xlsm|xls|zip|pdf)\b", re.IGNORECASE),
    re.compile(
        r'"(target_slot_id|private_processed_ref_hash|record_ref_hash|target_key_ref_hash|processed_value_fingerprint|raw_file_name|archive_member_name|sheet_name|cell_address|raw_value|normalized_decimal|context_text|business_value|field_header)"',
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
    "business_value",
    "field_header",
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
        "private_outside_scope_resolution_queue_read_by_this_phase",
        "private_authorized_extension_template_written_by_this_phase",
        "private_authorized_extension_pending_queue_written_by_this_phase",
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
    _require_equal("summary.diagnostic_conclusion", summary.get("diagnostic_conclusion"), DIAGNOSTIC_CONCLUSION)
    _require_equal("summary.next_required_input", summary.get("next_required_input"), NEXT_REQUIRED_INPUT)
    _require_equal("summary.source_outside_scope_resolution_queue_count", summary.get("source_outside_scope_resolution_queue_count"), 72)
    _require_equal(
        "summary.outside_scope_authorized_source_map_required_count",
        summary.get("outside_scope_authorized_source_map_required_count"),
        72,
    )
    _require_equal(
        "summary.private_authorized_extension_template_item_count",
        summary.get("private_authorized_extension_template_item_count"),
        72,
    )
    _require_equal(
        "summary.private_authorized_extension_pending_queue_count",
        summary.get("private_authorized_extension_pending_queue_count"),
        72,
    )
    _require_false("summary.owner_authorized_extension_input_present", summary.get("owner_authorized_extension_input_present"))
    _require_equal("summary.owner_authorized_extension_record_count", summary.get("owner_authorized_extension_record_count"), 0)
    _require_equal("summary.valid_authorized_extension_record_count", summary.get("valid_authorized_extension_record_count"), 0)
    _require_equal("summary.invalid_authorized_extension_record_count", summary.get("invalid_authorized_extension_record_count"), 0)
    _require_equal("summary.missing_authorized_extension_record_count", summary.get("missing_authorized_extension_record_count"), 72)
    _require_equal("summary.source_map_extension_applied_count", summary.get("source_map_extension_applied_count"), 0)
    _require_equal("summary.source_map_extension_pending_count", summary.get("source_map_extension_pending_count"), 72)
    for key in ("private_template_written", "private_template_gitignored", "private_pending_queue_written", "private_pending_queue_gitignored", "private_diagnostic_written", "private_diagnostic_gitignored"):
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
    _check_raw_boundary(summary["raw_boundary"])
    _check_public_safety(summary["public_safety"])
    _require_equal("matrix.phase_id", matrix.get("phase_id"), PHASE_ID)
    _require_equal("matrix.check_count", matrix.get("outside_scope_authorized_source_map_extension_check_count"), 8)
    _require_equal("matrix.pass_count", matrix.get("outside_scope_authorized_source_map_extension_check_pass_count"), 8)
    _require_equal("matrix.fail_count", matrix.get("outside_scope_authorized_source_map_extension_check_fail_count"), 0)
    _require_equal("go_no_go.next_required_input", go_no_go.get("next_required_input"), NEXT_REQUIRED_INPUT)
    _require_equal("go_no_go.valid", go_no_go.get("valid_authorized_extension_record_count"), 0)
    _require_equal("go_no_go.missing", go_no_go.get("missing_authorized_extension_record_count"), 72)
    _require_false("go_no_go.source map extension", go_no_go.get("source_map_extension_written_by_this_phase"))
    _require_false("go_no_go.full comparison", go_no_go.get("full_raw_to_processed_value_comparison_complete"))
    _require_equal("manifest.summary", manifest.get("summary"), summary)
    _require_equal("manifest.matrix", manifest.get("matrix"), matrix)
    _require_equal("manifest.go_no_go", manifest.get("go_no_go_report"), go_no_go)


def _check_private_template() -> None:
    for path in PRIVATE_ARTIFACTS:
        if not path.exists():
            raise ValidationError(f"missing private artifact: {path}")
        if not _git_check_ignored(path):
            raise ValidationError(f"private artifact is not gitignored: {path}")
    tracked = set(_git_output(["ls-files", "KMFA"]).splitlines())
    for path in PRIVATE_ARTIFACTS:
        if path.as_posix() in tracked:
            raise ValidationError(f"private artifact is tracked: {path}")
    template = _read_json(PRIVATE_TEMPLATE_PATH)
    diagnostic = _read_json(PRIVATE_DIAGNOSTIC_PATH)
    queue = _read_jsonl(PRIVATE_PENDING_QUEUE_PATH)
    rows = template.get("extension_rows")
    if not isinstance(rows, list):
        raise ValidationError("private extension_rows must be a list")
    _require_equal("private extension_rows count", len(rows), 72)
    _require_equal("private pending queue count", len(queue), 72)
    for row in rows + queue:
        forbidden = FORBIDDEN_PRIVATE_RAW_KEYS & set(row)
        if forbidden:
            raise ValidationError(f"private template copied raw fields: {sorted(forbidden)}")
        _require_equal("row.owner_decision_code", row.get("owner_decision_code"), "PENDING_AUTHORIZED_SOURCE_MAP_EXTENSION")
        _require_equal("row.required_action", row.get("required_action"), "supply_authorized_source_map_extension")
        _require_false("row.source_map_extension_written_by_this_phase", row.get("source_map_extension_written_by_this_phase"))
    _require_equal("diagnostic.count", diagnostic.get("private_summary", {}).get("private_authorized_extension_template_item_count"), 72)
    _check_raw_boundary(template.get("raw_boundary", {}))


def validate(*, require_private_template: bool = False) -> dict[str, Any]:
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
    if require_private_template:
        _check_private_template()
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--require-private-template", action="store_true")
    args = parser.parse_args()
    try:
        manifest = validate(require_private_template=args.require_private_template)
    except ValidationError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    summary = manifest["summary"]
    print(
        "PASS: KMFA v0.1.4 outside-scope authorized source-map extension artifacts validated "
        f"(template_items={summary['private_authorized_extension_template_item_count']}, "
        f"valid_extensions={summary['valid_authorized_extension_record_count']}, "
        f"decision={summary['decision']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
