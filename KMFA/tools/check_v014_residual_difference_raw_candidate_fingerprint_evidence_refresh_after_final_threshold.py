#!/usr/bin/env python3
"""Validate raw-candidate fingerprint evidence refresh artifacts."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from KMFA.tools.v014_residual_difference_raw_candidate_fingerprint_evidence_refresh_after_final_threshold import (  # noqa: E402
    ACCEPTANCE_ID,
    DECISION,
    GO_NO_GO_PATH,
    GO_NO_GO_RECORD_PATH,
    MANIFEST_PATH,
    MATRIX_PATH,
    METADATA_GO_NO_GO_PATH,
    METADATA_MANIFEST_PATH,
    METADATA_MATRIX_PATH,
    METADATA_SUMMARY_PATH,
    NEXT_RECOMMENDED_PHASE,
    NEXT_REQUIRED_INPUT,
    PHASE_ID,
    PRIVATE_RAW_INDEX_PATH,
    PRIVATE_REFRESH_DIAGNOSTIC_PATH,
    PRIVATE_REFRESH_RECORDS_PATH,
    PRIVATE_REFRESH_REPORT_PATH,
    PRIVATE_SLOT_KEY,
    REFRESH_CONCLUSION,
    REPORT_PATH,
    RISK_REGISTER_PATH,
    ROLLBACK_PATH,
    SOURCE_PRIVATE_RESOLUTION_RECORDS_PATH,
    SOURCE_RESOLUTION_GO_NO_GO_PATH,
    SOURCE_RESOLUTION_MANIFEST_PATH,
    SOURCE_RESOLUTION_MATRIX_PATH,
    SOURCE_RESOLUTION_SUMMARY_PATH,
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
FORBIDDEN_PUBLIC_PATTERNS = [
    re.compile(re.escape(RAW_DOWNLOADS_MARKER)),
    re.compile(re.escape(RAW_INBOX_MARKER)),
    re.compile(re.escape(".codex_private_runtime")),
    re.compile(r"\.(xlsx|xlsm|xls|zip|pdf|sqlite|sqlite3|db)\b", re.IGNORECASE),
    re.compile(r"sha256:[0-9a-f]{64}"),
    re.compile(r'"[0-9a-f]{64}"'),
    re.compile(
        r'"(target_slot_id|raw_file_name|archive_member_name|sheet_name|cell_address|raw_value|normalized_decimal|'
        r"context_text|numeric_value_fingerprint|processed_value_fingerprint|raw_candidate_fingerprint|"
        r"value_fingerprint|raw_candidate_record_ref_hash|source_record_ref_hash|"
        + PRIVATE_SLOT_KEY
        + r")\"",
        re.IGNORECASE,
    ),
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile("-----BEGIN [A-Z ]*" + "PRIVATE" + " KEY-----"),
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


def _check_public_safety(public_safety: dict[str, Any]) -> None:
    _require_true("public_safety.public_safe_aggregate_only", public_safety.get("public_safe_aggregate_only"))
    for key, value in public_safety.items():
        if key != "public_safe_aggregate_only":
            _require_false(f"public_safety.{key}", value)


def _check_raw_boundary(raw_boundary: dict[str, Any]) -> None:
    for key in (
        "user_authorized_raw_data_read_for_this_phase",
        "user_declared_raw_data_immutable",
        "raw_data_root_readonly_policy_active",
        "source_resolution_public_artifacts_read_by_this_phase",
        "source_private_resolution_records_read_by_this_phase",
        "raw_inbox_read_performed_by_this_phase",
        "raw_inbox_list_performed_by_this_phase",
        "raw_inbox_stat_performed_by_this_phase",
        "raw_inbox_hash_or_value_fingerprint_performed_by_this_phase",
        "raw_inbox_parse_performed_by_this_phase",
        "raw_inbox_field_or_header_read_performed_by_this_phase",
        "raw_inbox_value_extraction_performed_by_this_phase",
        "raw_root_stat_unchanged_after_phase",
        "private_raw_index_written_by_this_phase",
        "private_refresh_records_written_by_this_phase",
    ):
        _require_true(f"raw_boundary.{key}", raw_boundary.get(key))
    for key in (
        "source_private_resolution_records_mutated_by_this_phase",
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


def _check_summary(summary: dict[str, Any], matrix: dict[str, Any], go_no_go: dict[str, Any], manifest: dict[str, Any]) -> None:
    _require_equal("summary.version", summary.get("version"), VERSION)
    _require_equal("summary.phase_id", summary.get("phase_id"), PHASE_ID)
    _require_equal("summary.task_id", summary.get("task_id"), TASK_ID)
    _require_equal("summary.acceptance_id", summary.get("acceptance_id"), ACCEPTANCE_ID)
    _require_equal("summary.status", summary.get("status"), STATUS)
    _require_equal("summary.decision", summary.get("decision"), DECISION)
    _require_equal("summary.refresh_conclusion", summary.get("refresh_conclusion"), REFRESH_CONCLUSION)
    _require_equal("summary.source_go_no_go", summary.get("source_go_no_go_decision"), "NO_GO")
    _require_equal("summary.source_matrix_fail", summary.get("source_matrix_check_fail_count"), 0)
    _require_equal("summary.source_attempts", summary.get("source_resolution_attempt_item_count"), 48)
    _require_equal("summary.source_auto_resolved", summary.get("source_auto_resolved_raw_candidate_fingerprint_count"), 0)
    _require_equal("summary.source_still_blocked", summary.get("source_still_blocked_raw_candidate_fingerprint_count"), 48)
    _require_equal("summary.source_private_rows", summary.get("source_private_resolution_record_count"), 48)
    _require_equal("summary.refresh_item_count", summary.get("refresh_item_count"), 48)
    if int(summary.get("raw_numeric_candidate_count") or 0) <= 0:
        raise ValidationError("summary.raw_numeric_candidate_count must be > 0")
    if int(summary.get("raw_unique_numeric_fingerprint_count") or 0) <= 0:
        raise ValidationError("summary.raw_unique_numeric_fingerprint_count must be > 0")
    _require_true("summary.raw_value_fingerprints_generated", summary.get("raw_value_fingerprints_generated"))
    _require_true("summary.raw_root_stat_unchanged_after_phase", summary.get("raw_root_stat_unchanged_after_phase"))
    _require_equal("summary.deterministic_matches", summary.get("deterministic_raw_candidate_fingerprint_match_count"), 0)
    _require_equal("summary.still_blocked_after_refresh", summary.get("still_blocked_after_raw_refresh_count"), 48)
    _require_equal("summary.retry_ready", summary.get("comparison_retry_ready_after_raw_refresh_count"), 0)
    _require_equal("summary.source_ref_required", summary.get("provide_authoritative_source_reference_or_owner_exclusion_count"), 40)
    _require_equal("summary.formula_required", summary.get("provide_formula_or_non_numeric_mapping_count"), 8)
    _require_equal("summary.unresolved", summary.get("unresolved_difference_count"), 72)
    for key in (
        "private_raw_index_gitignored",
        "private_refresh_diagnostic_gitignored",
        "private_refresh_records_gitignored",
        "private_refresh_report_gitignored",
        "source_private_resolution_records_gitignored",
    ):
        _require_true(f"summary.{key}", summary.get(key))
    for key in (
        "raw_to_processed_value_comparison_performed_by_this_phase",
        "full_raw_to_processed_value_comparison_complete",
        "processed_consistency_verified",
        "business_value_consistency_verified",
        "full_reconciliation_allowed",
        "lineage_full_check_complete",
        "formal_report_allowed",
        "github_upload_performed",
        "app_reinstall_performed",
        "business_execution_performed",
    ):
        _require_false(f"summary.{key}", summary.get(key))
    _check_raw_boundary(summary.get("raw_boundary", {}))
    _check_public_safety(summary.get("public_safety", {}))
    _require_equal("matrix.phase", matrix.get("phase_id"), PHASE_ID)
    _require_equal("matrix.check_count", matrix.get("check_count"), 15)
    _require_equal("matrix.check_fail_count", matrix.get("check_fail_count"), 0)
    _require_equal("matrix.check_pass_count", matrix.get("check_pass_count"), 15)
    _require_equal("go_no_go.decision", go_no_go.get("decision"), DECISION)
    _require_equal("go_no_go.next_required_input", go_no_go.get("next_required_input"), NEXT_REQUIRED_INPUT)
    _require_equal("go_no_go.next_recommended_phase", go_no_go.get("next_recommended_phase"), NEXT_RECOMMENDED_PHASE)
    _require_equal("manifest.phase", manifest.get("phase_id"), PHASE_ID)
    _require_equal("manifest.summary.phase", manifest.get("summary", {}).get("phase_id"), PHASE_ID)


def _check_private_outputs(require_private_refresh: bool) -> None:
    if not require_private_refresh:
        return
    for path in (
        PRIVATE_RAW_INDEX_PATH,
        PRIVATE_REFRESH_DIAGNOSTIC_PATH,
        PRIVATE_REFRESH_RECORDS_PATH,
        PRIVATE_REFRESH_REPORT_PATH,
        SOURCE_PRIVATE_RESOLUTION_RECORDS_PATH,
    ):
        if not path.exists():
            raise ValidationError(f"missing private artifact: {path}")
        if not _git_check_ignored(path):
            raise ValidationError(f"private artifact is not gitignored: {path}")
    records = _read_jsonl(PRIVATE_REFRESH_RECORDS_PATH)
    _require_equal("private.records", len(records), 48)
    status_counts = Counter(row.get("raw_refresh_status") for row in records)
    _require_equal(
        "private.blocked_status",
        status_counts["blocked_missing_authoritative_fingerprint_pair_after_raw_refresh"],
        48,
    )
    _require_equal("private.ready_count", sum(1 for row in records if row.get("comparison_retry_ready_after_raw_refresh")), 0)
    for row in records:
        _require_false("private.public_commit_allowed", row.get("public_commit_allowed"))
        if row.get(PRIVATE_SLOT_KEY):
            continue
        raise ValidationError("private refresh row missing private slot key")
    raw_index = _read_json(PRIVATE_RAW_INDEX_PATH)
    private_index = raw_index.get("source_raw_scan_private_index", {})
    numeric_records = private_index.get("numeric_records", [])
    if not isinstance(numeric_records, list) or len(numeric_records) == 0:
        raise ValidationError("private raw index must contain numeric_records")


def validate(*, require_private_refresh: bool = False) -> dict[str, Any]:
    _check_public_artifacts()
    _check_no_raw_private_files_tracked()
    for path in (
        SOURCE_RESOLUTION_SUMMARY_PATH,
        SOURCE_RESOLUTION_MANIFEST_PATH,
        SOURCE_RESOLUTION_GO_NO_GO_PATH,
        SOURCE_RESOLUTION_MATRIX_PATH,
    ):
        if not path.exists():
            raise ValidationError(f"missing source artifact: {path}")
    summary = _read_json(SUMMARY_PATH)
    matrix = _read_json(MATRIX_PATH)
    go_no_go = _read_json(GO_NO_GO_PATH)
    manifest = _read_json(MANIFEST_PATH)
    _check_summary(summary, matrix, go_no_go, manifest)
    _check_private_outputs(require_private_refresh)
    for metadata_path, source_path in (
        (METADATA_SUMMARY_PATH, SUMMARY_PATH),
        (METADATA_MANIFEST_PATH, MANIFEST_PATH),
        (METADATA_GO_NO_GO_PATH, GO_NO_GO_PATH),
        (METADATA_MATRIX_PATH, MATRIX_PATH),
    ):
        _require_equal(f"metadata copy {metadata_path}", _read_json(metadata_path), _read_json(source_path))
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-private-refresh", action="store_true")
    args = parser.parse_args()
    try:
        validate(require_private_refresh=args.require_private_refresh)
    except ValidationError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print("PASS: KMFA v0.1.4 raw candidate fingerprint evidence refresh artifacts validated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
