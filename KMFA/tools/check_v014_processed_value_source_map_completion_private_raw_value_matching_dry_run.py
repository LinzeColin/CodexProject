#!/usr/bin/env python3
"""Validate KMFA v0.1.4 private raw value matching dry-run evidence."""

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

from KMFA.tools.v014_processed_value_source_map_completion_private_raw_value_matching_dry_run import (  # noqa: E402
    ACCEPTANCE_ID,
    DECISION,
    DIAGNOSTIC_CONCLUSION,
    GAP_SUMMARY_PATH,
    GO_NO_GO_PATH,
    GO_NO_GO_RECORD_PATH,
    MANIFEST_PATH,
    METADATA_GAP_SUMMARY_PATH,
    METADATA_GO_NO_GO_PATH,
    METADATA_MANIFEST_PATH,
    METADATA_SUMMARY_PATH,
    NEXT_REQUIRED_INPUT,
    PHASE_ID,
    PRIVATE_DIAGNOSTIC_PATH,
    PRIVATE_DRY_RUN_JSONL_PATH,
    PRIVATE_DRY_RUN_PATH,
    PRIVATE_GAP_REPORT_PATH,
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
PUBLIC_ARTIFACTS = [
    SUMMARY_PATH,
    MANIFEST_PATH,
    GO_NO_GO_PATH,
    GAP_SUMMARY_PATH,
    REPORT_PATH,
    GO_NO_GO_RECORD_PATH,
    TEST_RESULTS_PATH,
    RISK_REGISTER_PATH,
    ROLLBACK_PATH,
    METADATA_SUMMARY_PATH,
    METADATA_MANIFEST_PATH,
    METADATA_GO_NO_GO_PATH,
    METADATA_GAP_SUMMARY_PATH,
]
RAW_DOWNLOADS_MARKER = "/Users/" + "linzezhang/Downloads"
RAW_INBOX_MARKER = "KMFA" + "_MetaData"
FORBIDDEN_PUBLIC_PATTERNS = [
    re.compile(re.escape(RAW_DOWNLOADS_MARKER)),
    re.compile(re.escape(RAW_INBOX_MARKER)),
    re.compile(r"\.(xlsx|xlsm|xls|zip|pdf)\b", re.IGNORECASE),
    re.compile(
        r'"(raw_file_name|archive_member_name|sheet_name|cell_address|raw_value|normalized_decimal|context_text|numeric_value_fingerprint|processed_value_fingerprint|value_fingerprint|sha256_private)"',
        re.IGNORECASE,
    ),
    re.compile(r"sha256:[0-9a-f]{64}"),
    re.compile(r'"[0-9a-f]{64}"'),
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
]
SHA256 = re.compile(r"^sha256:[0-9a-f]{64}$")


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
    matches = [path for path in tracked if forbidden.search(path)]
    if matches:
        raise ValidationError("tracked raw/private files detected: " + ", ".join(matches[:20]))


def _check_raw_boundary(raw_boundary: dict[str, Any]) -> None:
    _require_true("raw_boundary.raw_data_root_readonly_policy_active", raw_boundary.get("raw_data_root_readonly_policy_active"))
    _require_true(
        "raw_boundary.private_raw_source_index_read_performed_by_this_phase",
        raw_boundary.get("private_raw_source_index_read_performed_by_this_phase"),
    )
    _require_true(
        "raw_boundary.private_processed_artifact_read_performed_by_this_phase",
        raw_boundary.get("private_processed_artifact_read_performed_by_this_phase"),
    )
    _require_true(
        "raw_boundary.private_runtime_diagnostic_written_by_this_phase",
        raw_boundary.get("private_runtime_diagnostic_written_by_this_phase"),
    )
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


def _check_private_dry_run(summary: dict[str, Any]) -> None:
    dry_run = _read_json(PRIVATE_DRY_RUN_PATH)
    diagnostic = _read_json(PRIVATE_DIAGNOSTIC_PATH)
    rows = _read_jsonl(PRIVATE_DRY_RUN_JSONL_PATH)
    gap_report = PRIVATE_GAP_REPORT_PATH.read_text(encoding="utf-8") if PRIVATE_GAP_REPORT_PATH.exists() else ""
    _require_equal("private dry run.phase_id", dry_run.get("phase_id"), PHASE_ID)
    _require_equal("private diagnostic.phase_id", diagnostic.get("phase_id"), PHASE_ID)
    _require_equal("private row count", len(rows), summary["dry_run_processed_fingerprint_target_count"])
    _require_equal("private dry run summary", dry_run.get("dry_run_summary"), diagnostic.get("dry_run_summary"))
    for key in (
        "raw_numeric_record_count",
        "raw_numeric_fingerprint_record_count",
        "raw_unique_numeric_fingerprint_count",
        "dry_run_processed_fingerprint_target_count",
        "dry_run_matched_target_count",
        "dry_run_unmatched_target_count",
        "dry_run_unique_raw_match_target_count",
        "dry_run_ambiguous_raw_match_target_count",
    ):
        _require_equal(f"private summary.{key}", dry_run["dry_run_summary"].get(key), summary[key])
    for index, row in enumerate(rows):
        if not isinstance(row.get("value_fingerprint"), str) or not SHA256.fullmatch(row["value_fingerprint"]):
            raise ValidationError(f"private row {index} has invalid value fingerprint")
        if row.get("match_status") not in {
            "no_raw_index_fingerprint_match",
            "unique_raw_index_fingerprint_match",
            "ambiguous_raw_index_fingerprint_match",
        }:
            raise ValidationError(f"private row {index} has invalid match status")
        if not isinstance(row.get("raw_index_occurrence_count"), int) or row["raw_index_occurrence_count"] < 0:
            raise ValidationError(f"private row {index} has invalid occurrence count")
    if "Private Raw Value Matching Gap Report" not in gap_report:
        raise ValidationError("private gap report missing title")
    _check_raw_boundary(dry_run.get("raw_boundary", {}))
    for path in (PRIVATE_DRY_RUN_PATH, PRIVATE_DRY_RUN_JSONL_PATH, PRIVATE_DIAGNOSTIC_PATH, PRIVATE_GAP_REPORT_PATH):
        if not path.exists():
            raise ValidationError(f"missing private artifact: {path}")
        if not _git_check_ignored(path):
            raise ValidationError(f"private artifact is not gitignored: {path}")
        _require_equal(f"{path}.tracked", _git_output(["ls-files", path.as_posix()]), "")


def validate(*, require_private_dry_run: bool = False) -> dict[str, Any]:
    summary = _read_json(SUMMARY_PATH)
    manifest = _read_json(MANIFEST_PATH)
    go_no_go = _read_json(GO_NO_GO_PATH)
    gap_summary = _read_json(GAP_SUMMARY_PATH)
    _require_equal("metadata summary", _read_json(METADATA_SUMMARY_PATH), summary)
    _require_equal("metadata manifest", _read_json(METADATA_MANIFEST_PATH), manifest)
    _require_equal("metadata go/no-go", _read_json(METADATA_GO_NO_GO_PATH), go_no_go)
    _require_equal("metadata gap summary", _read_json(METADATA_GAP_SUMMARY_PATH), gap_summary)

    _require_equal("summary.phase_id", summary.get("phase_id"), PHASE_ID)
    _require_equal("summary.task_id", summary.get("task_id"), TASK_ID)
    _require_equal("summary.acceptance_id", summary.get("acceptance_id"), ACCEPTANCE_ID)
    _require_equal("summary.version", summary.get("version"), VERSION)
    _require_equal("summary.status", summary.get("status"), STATUS)
    _require_equal("summary.decision", summary.get("decision"), DECISION)
    _require_equal("summary.diagnostic_conclusion", summary.get("diagnostic_conclusion"), DIAGNOSTIC_CONCLUSION)
    _require_equal("summary.previous_required_input", summary.get("previous_required_input"), "private_raw_value_matching_dry_run_before_any_delivery_claim")
    _require_true("summary.previous_required_input_resolved", summary.get("previous_required_input_resolved_by_this_phase"))
    _require_equal("summary.next_required_input", summary.get("next_required_input"), NEXT_REQUIRED_INPUT)

    _require_true("summary.private_raw_index_ready", summary.get("private_raw_index_ready"))
    _require_equal("summary.raw_numeric_record_count", summary.get("raw_numeric_record_count"), 351453)
    _require_equal("summary.raw_numeric_fingerprint_record_count", summary.get("raw_numeric_fingerprint_record_count"), 351453)
    _require_equal("summary.raw_unique_numeric_fingerprint_count", summary.get("raw_unique_numeric_fingerprint_count"), 22453)
    _require_equal("summary.raw_source_record_count", summary.get("raw_source_record_count"), 11)
    _require_equal("summary.raw_parse_error_count", summary.get("raw_parse_error_count"), 6)

    _require_equal("summary.processed_materialization_target_slot_count", summary.get("processed_materialization_target_slot_count"), 149)
    _require_equal("summary.processed_materialization_value_fingerprint_count", summary.get("processed_materialization_value_fingerprint_count"), 0)
    _require_false("summary.processed_materialization_complete", summary.get("processed_materialization_complete"))
    _require_equal("summary.owner_authorized_fill_target_count", summary.get("owner_authorized_fill_target_count"), 36)
    _require_equal("summary.owner_authorized_fill_value_fingerprint_count", summary.get("owner_authorized_fill_value_fingerprint_count"), 36)
    _require_equal("summary.owner_authorized_unfilled_target_count", summary.get("owner_authorized_unfilled_target_count"), 113)
    _require_equal("summary.partial_exact_replay_target_count", summary.get("partial_exact_replay_target_count"), 101)
    _require_equal("summary.partial_blocked_target_slot_count", summary.get("partial_blocked_target_slot_count"), 12)
    _require_equal("summary.dry_run_processed_fingerprint_target_count", summary.get("dry_run_processed_fingerprint_target_count"), 137)
    _require_equal("summary.dry_run_unique_processed_fingerprint_count", summary.get("dry_run_unique_processed_fingerprint_count"), 50)
    _require_true("summary.raw_value_matching_dry_run_performed", summary.get("raw_value_matching_dry_run_performed"))
    _require_equal("summary.dry_run_target_source_counts.owner_authorized_fill", summary["dry_run_target_source_counts"].get("owner_authorized_fill"), 36)
    _require_equal(
        "summary.dry_run_target_source_counts.partial_exact_comparison_replay",
        summary["dry_run_target_source_counts"].get("partial_exact_comparison_replay"),
        101,
    )
    _require_equal("summary.dry_run_matched_target_count", summary.get("dry_run_matched_target_count"), 101)
    _require_equal("summary.dry_run_unmatched_target_count", summary.get("dry_run_unmatched_target_count"), 36)
    _require_equal("summary.dry_run_unique_raw_match_target_count", summary.get("dry_run_unique_raw_match_target_count"), 24)
    _require_equal("summary.dry_run_ambiguous_raw_match_target_count", summary.get("dry_run_ambiguous_raw_match_target_count"), 77)
    _require_equal("summary.dry_run_confirmed_fingerprint_mismatch_count", summary.get("dry_run_confirmed_fingerprint_mismatch_count"), 0)
    _require_false("summary.repeated_cross_validation_mismatch_confirmed", summary.get("repeated_cross_validation_mismatch_confirmed"))
    _require_false(
        "summary.full_raw_to_processed_value_comparison_performed_by_this_phase",
        summary.get("full_raw_to_processed_value_comparison_performed_by_this_phase"),
    )
    _require_false("summary.business_value_consistency_verified", summary.get("business_value_consistency_verified"))
    for key in (
        "private_dry_run_written",
        "private_dry_run_gitignored",
        "private_dry_run_jsonl_written",
        "private_dry_run_jsonl_gitignored",
        "private_diagnostic_written",
        "private_diagnostic_gitignored",
        "private_gap_report_written",
        "private_gap_report_gitignored",
    ):
        _require_true(f"summary.{key}", summary.get(key))
    for key in (
        "canonical_source_map_mutated",
        "full_raw_to_processed_reconciliation_complete",
        "lineage_full_check_complete",
        "formal_report_allowed",
        "github_upload_performed",
        "app_reinstall_performed",
        "business_execution_performed",
    ):
        _require_false(f"summary.{key}", summary.get(key))
    _require_equal("summary.canonical_source_map_records_applied_count", summary.get("canonical_source_map_records_applied_count"), 0)

    _require_equal("go_no_go.decision", go_no_go.get("decision"), DECISION)
    _require_equal("go_no_go.blocked_until", go_no_go.get("blocked_until"), NEXT_REQUIRED_INPUT)
    _require_equal("go_no_go.dry_run_processed_fingerprint_target_count", go_no_go.get("dry_run_processed_fingerprint_target_count"), 137)
    _require_equal("go_no_go.dry_run_matched_target_count", go_no_go.get("dry_run_matched_target_count"), 101)
    _require_equal("go_no_go.dry_run_unmatched_target_count", go_no_go.get("dry_run_unmatched_target_count"), 36)
    _require_false("go_no_go.business_value_consistency_verified", go_no_go.get("business_value_consistency_verified"))
    _require_false("go_no_go.github_upload_performed", go_no_go.get("github_upload_performed"))
    _require_false("go_no_go.app_reinstall_performed", go_no_go.get("app_reinstall_performed"))
    _require_false("go_no_go.business_execution_performed", go_no_go.get("business_execution_performed"))

    _require_equal("manifest.summary", manifest.get("summary"), summary)
    _require_equal("manifest.go_no_go", manifest.get("go_no_go"), go_no_go)
    _require_equal("manifest.gap_summary", manifest.get("gap_summary"), gap_summary)
    _require_equal("gap_summary.gap_count", gap_summary.get("gap_count"), 4)
    _require_false(
        "gap_summary.repeated_cross_validation_mismatch_confirmed",
        gap_summary.get("repeated_cross_validation_mismatch_confirmed"),
    )
    _require_true(
        "gap_summary.final_goal_closeout_difference_report_required_if_repeated",
        gap_summary.get("final_goal_closeout_difference_report_required_if_repeated"),
    )
    _require_false("gap_summary.business_value_consistency_verified", gap_summary.get("business_value_consistency_verified"))
    _check_raw_boundary(summary.get("raw_boundary", {}))
    _check_public_safety(summary.get("public_safety", {}))
    _check_public_artifacts()
    _check_no_raw_private_files_tracked()
    if require_private_dry_run:
        _check_private_dry_run(summary)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-private-dry-run", action="store_true")
    args = parser.parse_args()
    manifest = validate(require_private_dry_run=args.require_private_dry_run)
    print(
        "PASS: KMFA v0.1.4 private raw value matching dry-run artifacts validated "
        f"(decision={manifest['go_no_go']['decision']}, "
        f"targets={manifest['summary']['dry_run_processed_fingerprint_target_count']}, "
        f"matched={manifest['summary']['dry_run_matched_target_count']}, "
        f"unmatched={manifest['summary']['dry_run_unmatched_target_count']})"
    )


if __name__ == "__main__":
    main()
