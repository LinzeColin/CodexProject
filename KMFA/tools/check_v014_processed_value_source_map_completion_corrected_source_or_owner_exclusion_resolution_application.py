#!/usr/bin/env python3
"""Validate KMFA v0.1.4 owner-exclusion resolution application artifacts."""

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

from KMFA.tools.v014_processed_value_source_map_completion_corrected_source_or_owner_exclusion_resolution_application import (  # noqa: E402
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
    OWNER_EXCLUSION_DECISION,
    PHASE_ID,
    PRIVATE_APPLIED_QUEUE_PATH,
    PRIVATE_BLOCKER_QUEUE_PATH,
    PRIVATE_DIAGNOSTIC_PATH,
    PRIVATE_REPORT_PATH,
    PRIVATE_RESULT_PATH,
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
PRIVATE_ARTIFACTS = [
    PRIVATE_DIAGNOSTIC_PATH,
    PRIVATE_RESULT_PATH,
    PRIVATE_APPLIED_QUEUE_PATH,
    PRIVATE_BLOCKER_QUEUE_PATH,
    PRIVATE_REPORT_PATH,
]
FORBIDDEN_PUBLIC_PATTERNS = [
    re.compile(re.escape(RAW_DOWNLOADS_MARKER)),
    re.compile(re.escape(RAW_INBOX_MARKER)),
    re.compile(re.escape(".codex_private_runtime")),
    re.compile(r"\.(xlsx|xlsm|xls|zip|pdf)\b", re.IGNORECASE),
    re.compile(
        r'"(raw_file_name|archive_member_name|sheet_name|cell_address|raw_value|normalized_decimal|context_text|numeric_value_fingerprint|processed_value_fingerprint|value_fingerprint|sha256_private|target_slot_id|review_group_id|context_group|owner_exclusion_basis_ref)"',
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
        "private_retry_application_readiness_diagnostic_read_by_this_phase",
        "private_retry_application_ready_queue_read_by_this_phase",
        "private_retry_application_blocker_queue_read_by_this_phase",
        "private_resolution_application_diagnostic_written_by_this_phase",
        "private_resolution_application_applied_queue_written_by_this_phase",
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


def _check_private_application(summary: dict[str, Any]) -> None:
    for path in PRIVATE_ARTIFACTS:
        if not path.exists():
            raise ValidationError(f"missing private artifact: {path}")
        if not _git_check_ignored(path):
            raise ValidationError(f"private artifact is not gitignored: {path}")
        tracked = _git_output(["ls-files", "--", path.as_posix()])
        if tracked:
            raise ValidationError(f"private artifact is tracked: {path}")
    diagnostic = _read_json(PRIVATE_DIAGNOSTIC_PATH)
    result = _read_json(PRIVATE_RESULT_PATH)
    applied_queue = _read_jsonl(PRIVATE_APPLIED_QUEUE_PATH)
    blocker_queue = _read_jsonl(PRIVATE_BLOCKER_QUEUE_PATH)
    _require_equal("diagnostic.phase_id", diagnostic.get("phase_id"), PHASE_ID)
    _require_equal("diagnostic.task_id", diagnostic.get("task_id"), TASK_ID)
    _require_equal("diagnostic.decision", diagnostic.get("decision"), DECISION)
    _require_equal("diagnostic.private_retry_item_count", diagnostic.get("private_retry_item_count"), 36)
    _require_equal("diagnostic.source_ready_queue_count", diagnostic.get("source_ready_queue_count"), 36)
    _require_equal("diagnostic.source_blocker_queue_count", diagnostic.get("source_blocker_queue_count"), 0)
    _require_equal("diagnostic.owner_exclusion_resolution_applied_count", diagnostic.get("owner_exclusion_resolution_applied_count"), 36)
    _require_equal("diagnostic.corrected_source_resolution_applied_count", diagnostic.get("corrected_source_resolution_applied_count"), 0)
    _require_true("diagnostic.resolution_application_performed", diagnostic.get("resolution_application_performed_by_this_phase"))
    _require_false("diagnostic.source_map_mutation", diagnostic.get("source_map_mutation_performed_by_this_phase"))
    _require_equal("diagnostic.source_map_records_applied_count", diagnostic.get("source_map_records_applied_count"), 0)
    _require_false("diagnostic.raw_inbox_accessed", diagnostic.get("raw_inbox_accessed"))
    _require_equal("result.owner_exclusion_resolution_applied_count", result.get("owner_exclusion_resolution_applied_count"), 36)
    _require_equal("result.corrected_source_resolution_applied_count", result.get("corrected_source_resolution_applied_count"), 0)
    _require_equal("private applied queue length", len(applied_queue), 36)
    _require_equal("private blocker queue length", len(blocker_queue), 0)
    for row in applied_queue:
        _require_equal("applied decision", row.get("application_decision_code"), OWNER_EXCLUSION_DECISION)
        _require_true("applied resolution flag", row.get("resolution_application_performed"))
        _require_true("applied owner exclusion flag", row.get("owner_exclusion_applied"))
        _require_false("applied corrected source flag", row.get("corrected_source_applied"))
        _require_false("applied source-map mutation", row.get("source_map_mutation_performed_by_this_phase"))
        _require_false("applied source-map record", row.get("source_map_record_applied"))
        _require_false("applied raw comparison", row.get("raw_to_processed_value_comparison_performed"))
        _require_false("applied full reconciliation", row.get("full_reconciliation_allowed"))
    _require_equal("summary owner exclusion applied count", summary.get("owner_exclusion_resolution_applied_count"), len(applied_queue))
    _require_equal("summary blocker queue count", summary.get("resolution_application_blocker_queue_count"), len(blocker_queue))


def _check_summary(summary: dict[str, Any], matrix: dict[str, Any], go_no_go: dict[str, Any], manifest: dict[str, Any]) -> None:
    _require_equal("summary.phase_id", summary.get("phase_id"), PHASE_ID)
    _require_equal("summary.task_id", summary.get("task_id"), TASK_ID)
    _require_equal("summary.version", summary.get("version"), VERSION)
    _require_equal("summary.status", summary.get("status"), STATUS)
    _require_equal("summary.decision", summary.get("decision"), DECISION)
    _require_equal("summary.private_retry_item_count", summary.get("private_retry_item_count"), 36)
    _require_equal("summary.retry_application_ready_item_count", summary.get("retry_application_ready_item_count"), 36)
    _require_equal("summary.source_retry_application_blocker_queue_count", summary.get("source_retry_application_blocker_queue_count"), 0)
    _require_equal("summary.owner_exclusion_resolution_applied_count", summary.get("owner_exclusion_resolution_applied_count"), 36)
    _require_equal("summary.corrected_source_resolution_applied_count", summary.get("corrected_source_resolution_applied_count"), 0)
    _require_equal("summary.resolution_application_blocker_queue_count", summary.get("resolution_application_blocker_queue_count"), 0)
    for key in (
        "source_resolution_application_ready",
        "source_readiness_diagnostic_ready",
        "resolution_application_performed_by_this_phase",
        "owner_exclusion_resolution_application_performed_by_this_phase",
        "all_36_unlinked_blockers_resolved_by_owner_exclusion",
        "post_resolution_readiness_recheck_required",
        "post_resolution_readiness_recheck_ready",
        "source_map_completion_reapplication_ready",
        "private_application_diagnostic_written",
        "private_application_diagnostic_gitignored",
        "private_application_result_written",
        "private_application_result_gitignored",
        "private_application_applied_queue_written",
        "private_application_applied_queue_gitignored",
        "private_application_blocker_queue_written",
        "private_application_blocker_queue_gitignored",
    ):
        _require_true(f"summary.{key}", summary.get(key))
    for key in (
        "corrected_source_resolution_application_performed_by_this_phase",
        "source_map_mutation_performed_by_this_phase",
        "processed_value_materialization_replay_ready",
        "raw_to_processed_value_comparison_performed_by_this_phase",
        "raw_to_processed_value_comparison_ready",
        "full_reconciliation_allowed",
        "business_value_consistency_verified",
        "lineage_full_check_complete",
        "formal_report_allowed",
        "github_upload_performed",
        "app_reinstall_performed",
        "business_execution_performed",
    ):
        _require_false(f"summary.{key}", summary.get(key))
    _require_equal("summary.source_map_records_applied_count", summary.get("source_map_records_applied_count"), 0)
    _require_equal("summary.next_required_input", summary.get("next_required_input"), NEXT_REQUIRED_INPUT)
    _check_raw_boundary(summary["raw_boundary"])
    _check_public_safety(summary["public_safety"])
    _require_equal("matrix.phase_id", matrix.get("phase_id"), PHASE_ID)
    _require_equal("matrix.application_check_count", matrix.get("application_check_count"), 8)
    _require_equal("matrix.application_pass_count", matrix.get("application_pass_count"), 8)
    _require_equal("matrix.application_fail_count", matrix.get("application_fail_count"), 0)
    _require_equal("matrix.owner_exclusion_resolution_applied_count", matrix.get("owner_exclusion_resolution_applied_count"), 36)
    _require_equal("matrix.corrected_source_resolution_applied_count", matrix.get("corrected_source_resolution_applied_count"), 0)
    _require_equal("matrix.application_blocker_queue_count", matrix.get("application_blocker_queue_count"), 0)
    _require_true("matrix.resolution_application_performed", matrix.get("resolution_application_performed_by_this_phase"))
    _require_false("matrix.source_map_mutation", matrix.get("source_map_mutation_performed_by_this_phase"))
    _require_equal("matrix.source_map_records_applied_count", matrix.get("source_map_records_applied_count"), 0)
    _require_false("matrix.raw comparison", matrix.get("raw_to_processed_value_comparison_performed_by_this_phase"))
    _require_false("matrix.full reconciliation", matrix.get("full_reconciliation_allowed"))
    _require_equal("go_no_go.next_required_input", go_no_go.get("next_required_input"), NEXT_REQUIRED_INPUT)
    _require_equal("go_no_go.owner_exclusion_resolution_applied_count", go_no_go.get("owner_exclusion_resolution_applied_count"), 36)
    _require_equal("go_no_go.corrected_source_resolution_applied_count", go_no_go.get("corrected_source_resolution_applied_count"), 0)
    _require_equal("go_no_go.source_map_records_applied_count", go_no_go.get("source_map_records_applied_count"), 0)
    _require_true("go_no_go.resolution_application_performed", go_no_go.get("resolution_application_performed_by_this_phase"))
    _require_false("go_no_go.source_map_mutation", go_no_go.get("source_map_mutation_performed_by_this_phase"))
    _require_false("go_no_go.raw comparison", go_no_go.get("raw_to_processed_value_comparison_performed_by_this_phase"))
    _require_equal("manifest.phase_id", manifest.get("phase_id"), PHASE_ID)
    _require_equal("manifest.summary", manifest.get("summary"), summary)
    _require_equal("manifest.matrix", manifest.get("matrix"), matrix)
    _require_equal("manifest.go_no_go_report", manifest.get("go_no_go_report"), go_no_go)


def validate(*, require_private_application: bool = False) -> dict[str, Any]:
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
    if require_private_application:
        _check_private_application(summary)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--require-private-application", action="store_true")
    args = parser.parse_args()
    try:
        manifest = validate(require_private_application=args.require_private_application)
    except ValidationError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    summary = manifest["summary"]
    print(
        "PASS: KMFA v0.1.4 resolution application artifacts validated "
        f"(decision={summary['decision']}, owner_exclusions={summary['owner_exclusion_resolution_applied_count']}, "
        f"source_map_records={summary['source_map_records_applied_count']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
