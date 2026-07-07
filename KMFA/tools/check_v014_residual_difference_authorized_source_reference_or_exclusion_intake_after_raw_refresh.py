#!/usr/bin/env python3
"""Validate authorized source-reference / exclusion intake after raw refresh."""

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

from KMFA.tools.v014_residual_difference_authorized_source_reference_or_exclusion_intake_after_raw_refresh import (  # noqa: E402
    ACCEPTANCE_ID,
    DECISION,
    FORMULA_MAPPING_TRACK,
    GO_NO_GO_PATH,
    GO_NO_GO_RECORD_PATH,
    INTAKE_CONCLUSION,
    MANIFEST_PATH,
    MATRIX_PATH,
    METADATA_GO_NO_GO_PATH,
    METADATA_MANIFEST_PATH,
    METADATA_MATRIX_PATH,
    METADATA_SUMMARY_PATH,
    NEXT_RECOMMENDED_PHASE,
    NEXT_REQUIRED_INPUT,
    PHASE_ID,
    PRIVATE_ACTIVE_RECORD_PATH,
    PRIVATE_DIAGNOSTIC_PATH,
    PRIVATE_INTAKE_QUEUE_PATH,
    PRIVATE_REPORT_PATH,
    PRIVATE_SLOT_KEY,
    REPORT_PATH,
    RISK_REGISTER_PATH,
    ROLLBACK_PATH,
    SOURCE_PRIVATE_REFRESH_RECORDS_PATH,
    SOURCE_REFRESH_GO_NO_GO_PATH,
    SOURCE_REFRESH_MANIFEST_PATH,
    SOURCE_REFRESH_MATRIX_PATH,
    SOURCE_REFRESH_SUMMARY_PATH,
    SOURCE_REFERENCE_TRACK,
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
        "user_declared_raw_data_immutable",
        "raw_data_root_readonly_policy_active",
        "source_refresh_public_artifacts_read_by_this_phase",
        "source_private_refresh_records_read_by_this_phase",
        "private_active_record_written_by_this_phase",
        "private_intake_queue_written_by_this_phase",
        "private_diagnostic_written_by_this_phase",
    ):
        _require_true(f"raw_boundary.{key}", raw_boundary.get(key))
    for key in (
        "source_private_refresh_records_mutated_by_this_phase",
        "raw_inbox_read_performed_by_this_phase",
        "raw_inbox_list_performed_by_this_phase",
        "raw_inbox_stat_performed_by_this_phase",
        "raw_inbox_hash_or_value_fingerprint_performed_by_this_phase",
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


def _check_summary(summary: dict[str, Any], matrix: dict[str, Any], go_no_go: dict[str, Any], manifest: dict[str, Any]) -> None:
    _require_equal("summary.version", summary.get("version"), VERSION)
    _require_equal("summary.phase_id", summary.get("phase_id"), PHASE_ID)
    _require_equal("summary.task_id", summary.get("task_id"), TASK_ID)
    _require_equal("summary.acceptance_id", summary.get("acceptance_id"), ACCEPTANCE_ID)
    _require_equal("summary.status", summary.get("status"), STATUS)
    _require_equal("summary.decision", summary.get("decision"), DECISION)
    _require_equal("summary.intake_conclusion", summary.get("intake_conclusion"), INTAKE_CONCLUSION)
    _require_equal("summary.source_go_no_go", summary.get("source_go_no_go_decision"), "NO_GO")
    _require_equal("summary.source_matrix_fail", summary.get("source_matrix_check_fail_count"), 0)
    _require_equal("summary.source_refresh_items", summary.get("source_refresh_item_count"), 48)
    _require_equal("summary.source_still_blocked", summary.get("source_still_blocked_after_raw_refresh_count"), 48)
    _require_equal("summary.source_deterministic", summary.get("source_deterministic_match_count"), 0)
    _require_equal("summary.source_retry_ready", summary.get("source_comparison_retry_ready_count"), 0)
    _require_equal("summary.source_private_rows", summary.get("source_private_refresh_record_count"), 48)
    _require_equal("summary.intake_item_count", summary.get("intake_item_count"), 48)
    _require_equal("summary.private_active_record_item_count", summary.get("private_active_record_item_count"), 48)
    _require_equal("summary.source_reference_or_owner_exclusion", summary.get("source_reference_or_owner_exclusion_intake_count"), 40)
    _require_equal("summary.formula_or_mapping", summary.get("formula_or_non_numeric_mapping_intake_count"), 8)
    _require_equal("summary.active_authoritative_decision_count", summary.get("active_authoritative_decision_count"), 0)
    _require_equal("summary.binding_ready_after_intake_count", summary.get("binding_ready_after_intake_count"), 0)
    _require_equal("summary.comparison_retry_ready_after_intake_count", summary.get("comparison_retry_ready_after_intake_count"), 0)
    _require_equal("summary.unresolved", summary.get("unresolved_difference_count"), 72)
    for key in (
        "private_active_record_gitignored",
        "private_intake_queue_gitignored",
        "private_diagnostic_gitignored",
        "private_report_gitignored",
        "source_private_refresh_records_gitignored",
    ):
        _require_true(f"summary.{key}", summary.get(key))
    for key in (
        "authoritative_source_reference_applied_by_this_phase",
        "owner_exclusion_applied_by_this_phase",
        "formula_mapping_applied_by_this_phase",
        "raw_candidate_fingerprint_bound_by_this_phase",
        "raw_to_processed_value_comparison_ready",
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
    _require_equal("summary.next_required_input", summary.get("next_required_input"), NEXT_REQUIRED_INPUT)
    _require_equal("summary.next_recommended_phase", summary.get("next_recommended_phase"), NEXT_RECOMMENDED_PHASE)
    _check_raw_boundary(summary.get("raw_boundary") or {})
    _check_public_safety(summary.get("public_safety") or {})
    _require_equal("matrix.check_count", matrix.get("check_count"), 15)
    _require_equal("matrix.check_pass_count", matrix.get("check_pass_count"), 15)
    _require_equal("matrix.check_fail_count", matrix.get("check_fail_count"), 0)
    _require_equal("go_no_go.decision", go_no_go.get("decision"), DECISION)
    _require_equal("go_no_go.intake_item_count", go_no_go.get("intake_item_count"), 48)
    _require_equal("manifest.phase_id", manifest.get("phase_id"), PHASE_ID)
    _require_equal("manifest.summary.phase_id", (manifest.get("summary") or {}).get("phase_id"), PHASE_ID)


def _check_private_intake(summary: dict[str, Any], require_private_intake: bool) -> None:
    if not require_private_intake:
        return
    for path in (PRIVATE_ACTIVE_RECORD_PATH, PRIVATE_INTAKE_QUEUE_PATH, PRIVATE_DIAGNOSTIC_PATH, PRIVATE_REPORT_PATH):
        if not path.exists():
            raise ValidationError(f"missing private intake artifact: {path}")
        if not _git_check_ignored(path):
            raise ValidationError(f"private intake artifact is not ignored: {path}")
    active = _read_json(PRIVATE_ACTIVE_RECORD_PATH)
    rows = _read_jsonl(PRIVATE_INTAKE_QUEUE_PATH)
    diagnostic = _read_json(PRIVATE_DIAGNOSTIC_PATH)
    _require_equal("private.active.phase_id", active.get("phase_id"), PHASE_ID)
    _require_equal("private.active.intake_item_count", active.get("intake_item_count"), 48)
    _require_equal("private.diagnostic.phase_id", diagnostic.get("phase_id"), PHASE_ID)
    _require_equal("private.queue.count", len(rows), 48)
    track_counts = Counter(row.get("intake_track") for row in rows)
    _require_equal("private.queue.source_reference_or_owner_exclusion", track_counts["source_reference_or_owner_exclusion"], 40)
    _require_equal("private.queue.formula_or_non_numeric_mapping", track_counts["formula_or_non_numeric_mapping"], 8)
    source_tracks = Counter(row.get("source_diagnostic_track") for row in rows)
    _require_equal("private.queue.source_track_source_ref", source_tracks[SOURCE_REFERENCE_TRACK], 40)
    _require_equal("private.queue.source_track_formula", source_tracks[FORMULA_MAPPING_TRACK], 8)
    for row in rows:
        _require_equal("private.queue.phase_id", row.get("phase_id"), PHASE_ID)
        _require_true("private.queue.owner_authorization", row.get("owner_authorization_recorded_for_private_intake"))
        _require_false("private.queue.authoritative_binding", row.get("authoritative_binding_applied_by_this_phase"))
        _require_false("private.queue.retry_ready", row.get("comparison_retry_ready_after_intake"))
        _require_false("private.queue.public_commit_allowed", row.get("public_commit_allowed"))
    _require_equal("summary.intake_item_count", summary.get("intake_item_count"), len(rows))


def validate(*, require_private_intake: bool = False) -> dict[str, Any]:
    summary = _read_json(SUMMARY_PATH)
    manifest = _read_json(MANIFEST_PATH)
    go_no_go = _read_json(GO_NO_GO_PATH)
    matrix = _read_json(MATRIX_PATH)
    for source in (
        SOURCE_REFRESH_SUMMARY_PATH,
        SOURCE_REFRESH_MANIFEST_PATH,
        SOURCE_REFRESH_GO_NO_GO_PATH,
        SOURCE_REFRESH_MATRIX_PATH,
        SOURCE_PRIVATE_REFRESH_RECORDS_PATH,
    ):
        if not source.exists():
            raise ValidationError(f"missing source artifact: {source}")
    metadata_pairs = [
        (SUMMARY_PATH, METADATA_SUMMARY_PATH),
        (MANIFEST_PATH, METADATA_MANIFEST_PATH),
        (GO_NO_GO_PATH, METADATA_GO_NO_GO_PATH),
        (MATRIX_PATH, METADATA_MATRIX_PATH),
    ]
    for public_path, metadata_path in metadata_pairs:
        if _read_json(public_path) != _read_json(metadata_path):
            raise ValidationError(f"metadata copy mismatch: {metadata_path}")
    _check_summary(summary, matrix, go_no_go, manifest)
    _check_private_intake(summary, require_private_intake)
    _check_public_artifacts()
    _check_no_raw_private_files_tracked()
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-private-intake", action="store_true")
    args = parser.parse_args()
    try:
        validate(require_private_intake=args.require_private_intake)
    except ValidationError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print("PASS: KMFA v0.1.4 authorized source reference or exclusion intake after raw refresh artifacts validated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
