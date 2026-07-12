#!/usr/bin/env python3
"""Validate residual raw-to-processed comparison artifacts after owner anchors."""

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

from KMFA.tools.v014_residual_difference_raw_to_processed_comparison_after_owner_anchor_confirmation import (  # noqa: E402
    ACCEPTANCE_ID,
    COMPARISON_CONCLUSION,
    DECISION,
    EXPECTED_TRACK_COUNTS,
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
    PRIVATE_COMPARISON_BLOCKER_RECORDS_PATH,
    PRIVATE_COMPARISON_DIAGNOSTIC_PATH,
    PRIVATE_COMPARISON_RECORDS_PATH,
    PRIVATE_COMPARISON_REPORT_PATH,
    PRIVATE_SLOT_KEY,
    REPORT_PATH,
    RISK_REGISTER_PATH,
    ROLLBACK_PATH,
    SOURCE_GO_NO_GO_PATH,
    SOURCE_MANIFEST_PATH,
    SOURCE_MATRIX_PATH,
    SOURCE_PRIVATE_ANCHOR_DRAFT_PATH,
    SOURCE_PRIVATE_BLOCKER_QUEUE_PATH,
    SOURCE_PRIVATE_PRECHECK_DIAGNOSTIC_PATH,
    SOURCE_PRIVATE_PRECHECK_REPORT_PATH,
    SOURCE_PRIVATE_READY_QUEUE_PATH,
    SOURCE_SUMMARY_PATH,
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
        r'"(raw_file_name|archive_member_name|sheet_name|cell_address|raw_value|normalized_decimal|'
        r"context_text|numeric_value_fingerprint|processed_value_fingerprint|raw_candidate_fingerprint|"
        r"value_fingerprint|raw_candidate_record_ref_hash|source_ref_hash|source_cell_ref_hash|"
        r"source_record_ref_hash|private_processed_ref_hash|"
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


def _check_raw_boundary(raw_boundary: dict[str, Any]) -> None:
    for key in (
        "user_declared_raw_data_immutable",
        "raw_data_root_readonly_policy_active",
        "source_public_precheck_summary_read_by_this_phase",
        "source_public_precheck_manifest_read_by_this_phase",
        "source_public_precheck_go_no_go_read_by_this_phase",
        "source_public_precheck_matrix_read_by_this_phase",
        "source_private_precheck_diagnostic_read_by_this_phase",
        "source_private_ready_queue_read_by_this_phase",
        "source_private_blocker_queue_read_by_this_phase",
        "source_private_precheck_report_read_by_this_phase",
        "source_private_anchor_draft_read_by_this_phase",
        "private_comparison_diagnostic_written_by_this_phase",
        "private_comparison_records_written_by_this_phase",
        "private_comparison_blocker_records_written_by_this_phase",
        "private_comparison_report_written_by_this_phase",
    ):
        _require_true(f"raw_boundary.{key}", raw_boundary.get(key))
    for key, value in raw_boundary.items():
        if key.startswith("raw_inbox_") or key.endswith("_mutated_by_this_phase"):
            _require_false(f"raw_boundary.{key}", value)
    for key in (
        "source_private_ready_queue_mutated_by_this_phase",
        "source_private_blocker_queue_mutated_by_this_phase",
        "source_private_anchor_draft_mutated_by_this_phase",
    ):
        _require_false(f"raw_boundary.{key}", raw_boundary.get(key))


def _check_public_safety(public_safety: dict[str, Any]) -> None:
    _require_true("public_safety.public_safe_aggregate_only", public_safety.get("public_safe_aggregate_only"))
    for key, value in public_safety.items():
        if key != "public_safe_aggregate_only":
            _require_false(f"public_safety.{key}", value)


def _check_summary(summary: dict[str, Any], matrix: dict[str, Any], go_no_go: dict[str, Any], manifest: dict[str, Any]) -> None:
    _require_equal("summary.version", summary.get("version"), VERSION)
    _require_equal("summary.phase_id", summary.get("phase_id"), PHASE_ID)
    _require_equal("summary.task_id", summary.get("task_id"), TASK_ID)
    _require_equal("summary.acceptance_id", summary.get("acceptance_id"), ACCEPTANCE_ID)
    _require_equal("summary.status", summary.get("status"), STATUS)
    _require_equal("summary.decision", summary.get("decision"), DECISION)
    _require_equal("summary.comparison_conclusion", summary.get("comparison_conclusion"), COMPARISON_CONCLUSION)
    _require_equal("summary.source go no-go", summary.get("source_go_no_go_decision"), "NO_GO")
    _require_equal("summary.source matrix", summary.get("source_matrix_check_fail_count"), 0)
    _require_equal("summary.source ready", summary.get("source_comparison_precheck_ready_record_count"), 72)
    _require_equal("summary.source blockers", summary.get("source_comparison_precheck_blocker_record_count"), 0)
    _require_true("summary.source formal next", summary.get("source_formal_comparison_allowed_next_phase"))
    _require_false(
        "summary.source raw comparison performed",
        summary.get("source_raw_to_processed_value_comparison_performed_by_this_phase"),
    )
    _require_equal("summary.source private ready rows", summary.get("source_private_ready_queue_record_count"), 72)
    _require_equal("summary.source private blocker rows", summary.get("source_private_blocker_queue_record_count"), 0)
    _require_equal("summary.source anchor draft items", summary.get("source_anchor_draft_item_count"), 72)
    _require_equal("summary.source private fingerprint pairs", summary.get("source_anchor_draft_private_fingerprint_pair_count"), 0)
    _require_equal("summary.formal items", summary.get("formal_comparison_item_count"), 72)
    _require_equal("summary.result records", summary.get("formal_comparison_result_record_count"), 0)
    _require_equal("summary.exact matches", summary.get("formal_comparison_exact_match_count"), 0)
    _require_equal("summary.mismatches", summary.get("formal_comparison_mismatch_count"), 0)
    _require_equal("summary.blockers", summary.get("formal_comparison_blocker_count"), 72)
    _require_equal("summary.missing pairs", summary.get("missing_private_fingerprint_pair_count"), 72)
    _require_true("summary.formal attempt", summary.get("formal_raw_to_processed_comparison_attempted_by_this_phase"))
    _require_true(
        "summary.blocked missing pairs",
        summary.get("raw_to_processed_value_comparison_blocked_by_missing_private_fingerprint_pairs"),
    )
    for track, count in EXPECTED_TRACK_COUNTS.items():
        _require_equal(f"summary.{track}_count", summary.get(f"{track}_count"), count)
    _require_equal("summary.unresolved", summary.get("unresolved_difference_count"), 72)
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
    for key in (
        "private_comparison_diagnostic_written",
        "private_comparison_records_written",
        "private_comparison_blocker_records_written",
        "private_comparison_report_written",
        "private_comparison_diagnostic_gitignored",
        "private_comparison_records_gitignored",
        "private_comparison_blocker_records_gitignored",
        "private_comparison_report_gitignored",
        "source_private_precheck_diagnostic_gitignored",
        "source_private_ready_queue_gitignored",
        "source_private_blocker_queue_gitignored",
        "source_private_anchor_draft_gitignored",
    ):
        _require_true(f"summary.{key}", summary.get(key))
    _require_equal("summary.next_required_input", summary.get("next_required_input"), NEXT_REQUIRED_INPUT)
    _require_equal("summary.next_recommended_phase", summary.get("next_recommended_phase"), NEXT_RECOMMENDED_PHASE)
    _check_raw_boundary(summary.get("raw_boundary", {}))
    _check_public_safety(summary.get("public_safety", {}))

    _require_equal("matrix.phase_id", matrix.get("phase_id"), PHASE_ID)
    _require_equal("matrix.count", matrix.get("check_count"), 15)
    _require_equal("matrix.pass", matrix.get("check_pass_count"), 15)
    _require_equal("matrix.fail", matrix.get("check_fail_count"), 0)
    checks = {row.get("check_code"): row.get("status") for row in matrix.get("checks", []) if isinstance(row, dict)}
    for code in (
        "source_precheck_loaded",
        "source_precheck_valid",
        "source_ready_count_locked",
        "source_blockers_clear",
        "source_private_ready_queue_ignored",
        "source_anchor_draft_loaded",
        "source_anchor_draft_count_locked",
        "formal_attempt_recorded",
        "formal_items_locked",
        "comparison_blockers_locked",
        "missing_pairs_locked",
        "no_value_comparison_claimed",
        "raw_inbox_untouched",
        "public_safe_aggregate_only",
        "downstream_gates_closed",
    ):
        _require_equal(f"matrix.{code}", checks.get(code), "PASS")

    _require_equal("go_no_go.phase_id", go_no_go.get("phase_id"), PHASE_ID)
    _require_equal("go_no_go.decision", go_no_go.get("decision"), DECISION)
    _require_equal("go_no_go.conclusion", go_no_go.get("comparison_conclusion"), COMPARISON_CONCLUSION)
    _require_equal("go_no_go.formal items", go_no_go.get("formal_comparison_item_count"), 72)
    _require_equal("go_no_go.exact matches", go_no_go.get("formal_comparison_exact_match_count"), 0)
    _require_equal("go_no_go.mismatches", go_no_go.get("formal_comparison_mismatch_count"), 0)
    _require_equal("go_no_go.blockers", go_no_go.get("formal_comparison_blocker_count"), 72)
    _require_equal("go_no_go.missing pairs", go_no_go.get("missing_private_fingerprint_pair_count"), 72)
    _require_true("go_no_go.formal attempt", go_no_go.get("formal_raw_to_processed_comparison_attempted_by_this_phase"))
    _require_false("go_no_go.raw comparison performed", go_no_go.get("raw_to_processed_value_comparison_performed_by_this_phase"))
    _require_false("go_no_go.full comparison", go_no_go.get("full_raw_to_processed_value_comparison_complete"))
    _require_false("go_no_go.business consistency", go_no_go.get("business_value_consistency_verified"))
    _require_false("go_no_go.github upload", go_no_go.get("github_upload_allowed"))
    _require_false("go_no_go.app reinstall", go_no_go.get("app_reinstall_allowed"))
    _require_false("go_no_go.business execution", go_no_go.get("business_execution_allowed"))
    _require_equal("go_no_go.next_required_input", go_no_go.get("next_required_input"), NEXT_REQUIRED_INPUT)
    _require_equal("go_no_go.next_recommended_phase", go_no_go.get("next_recommended_phase"), NEXT_RECOMMENDED_PHASE)
    _require_equal("manifest.summary", manifest.get("summary"), summary)
    _require_equal("manifest.matrix", manifest.get("matrix"), matrix)
    _require_equal("manifest.go_no_go", manifest.get("go_no_go_report"), go_no_go)


def _anchor_draft_items() -> list[dict[str, Any]]:
    draft = _read_json(SOURCE_PRIVATE_ANCHOR_DRAFT_PATH)
    items = draft.get("anchor_draft_items")
    if not isinstance(items, list):
        raise ValidationError("anchor draft items must be a list")
    return [item for item in items if isinstance(item, dict)]


def _check_private_artifacts() -> None:
    private_paths = (
        SOURCE_PRIVATE_PRECHECK_DIAGNOSTIC_PATH,
        SOURCE_PRIVATE_READY_QUEUE_PATH,
        SOURCE_PRIVATE_BLOCKER_QUEUE_PATH,
        SOURCE_PRIVATE_PRECHECK_REPORT_PATH,
        SOURCE_PRIVATE_ANCHOR_DRAFT_PATH,
        PRIVATE_COMPARISON_DIAGNOSTIC_PATH,
        PRIVATE_COMPARISON_RECORDS_PATH,
        PRIVATE_COMPARISON_BLOCKER_RECORDS_PATH,
        PRIVATE_COMPARISON_REPORT_PATH,
    )
    for path in private_paths:
        if not path.exists():
            raise ValidationError(f"missing private artifact: {path}")
        if not _git_check_ignored(path):
            raise ValidationError(f"private artifact is not git-ignored: {path}")

    source_diagnostic = _read_json(SOURCE_PRIVATE_PRECHECK_DIAGNOSTIC_PATH)
    ready_rows = _read_jsonl(SOURCE_PRIVATE_READY_QUEUE_PATH)
    source_blocker_rows = _read_jsonl(SOURCE_PRIVATE_BLOCKER_QUEUE_PATH)
    anchor_draft_items = _anchor_draft_items()
    comparison_diagnostic = _read_json(PRIVATE_COMPARISON_DIAGNOSTIC_PATH)
    comparison_rows = _read_jsonl(PRIVATE_COMPARISON_RECORDS_PATH)
    blocker_rows = _read_jsonl(PRIVATE_COMPARISON_BLOCKER_RECORDS_PATH)

    _require_equal("source diagnostic ready count", source_diagnostic.get("comparison_precheck_ready_record_count"), 72)
    _require_equal("source diagnostic blocker count", source_diagnostic.get("comparison_precheck_blocker_record_count"), 0)
    _require_equal("ready rows", len(ready_rows), 72)
    _require_equal("source blocker rows", len(source_blocker_rows), 0)
    _require_equal("anchor draft items", len(anchor_draft_items), 72)
    _require_equal("comparison diagnostic items", comparison_diagnostic.get("formal_comparison_item_count"), 72)
    _require_equal("comparison diagnostic results", comparison_diagnostic.get("formal_comparison_result_record_count"), 0)
    _require_equal("comparison diagnostic blockers", comparison_diagnostic.get("formal_comparison_blocker_count"), 72)
    _require_equal("comparison rows", len(comparison_rows), 0)
    _require_equal("blocker rows", len(blocker_rows), 72)

    ready_slots = {row.get(PRIVATE_SLOT_KEY) for row in ready_rows}
    anchor_slots = {row.get(PRIVATE_SLOT_KEY) for row in anchor_draft_items}
    blocker_slots = {row.get(PRIVATE_SLOT_KEY) for row in blocker_rows}
    _require_equal("ready slots vs anchor slots", ready_slots, anchor_slots)
    _require_equal("ready slots vs blocker slots", ready_slots, blocker_slots)
    _require_equal("ready track counts", Counter(row.get("diagnostic_track") for row in ready_rows), Counter(EXPECTED_TRACK_COUNTS))
    _require_equal("blocker track counts", Counter(row.get("diagnostic_track") for row in blocker_rows), Counter(EXPECTED_TRACK_COUNTS))

    for row in blocker_rows:
        _require_equal(
            "blocker status",
            row.get("formal_comparison_status"),
            "missing_private_fingerprint_pair_for_formal_comparison",
        )
        _require_true("blocker formal attempt", row.get("formal_raw_to_processed_comparison_attempted_by_this_phase"))
        _require_false("blocker comparison performed", row.get("raw_to_processed_value_comparison_performed_by_this_phase"))
        _require_false("blocker full comparison", row.get("full_raw_to_processed_value_comparison_complete"))
        _require_false("blocker business verified", row.get("business_value_consistency_verified"))
        _require_false("blocker public", row.get("public_commit_allowed"))

    tracked = set(_git_output(["ls-files", "KMFA"]).splitlines())
    for path in private_paths:
        if path.as_posix() in tracked:
            raise ValidationError(f"private artifact is tracked: {path}")


def validate(*, require_private_comparison: bool = False) -> dict[str, Any]:
    summary = _read_json(SUMMARY_PATH)
    manifest = _read_json(MANIFEST_PATH)
    go_no_go = _read_json(GO_NO_GO_PATH)
    matrix = _read_json(MATRIX_PATH)
    for metadata_path, source in (
        (METADATA_SUMMARY_PATH, summary),
        (METADATA_MANIFEST_PATH, manifest),
        (METADATA_GO_NO_GO_PATH, go_no_go),
        (METADATA_MATRIX_PATH, matrix),
    ):
        _require_equal(f"{metadata_path}.content", _read_json(metadata_path), source)
    _read_json(SOURCE_SUMMARY_PATH)
    _read_json(SOURCE_MANIFEST_PATH)
    _read_json(SOURCE_GO_NO_GO_PATH)
    _read_json(SOURCE_MATRIX_PATH)
    _check_summary(summary, matrix, go_no_go, manifest)
    _check_public_artifacts()
    _check_no_raw_private_files_tracked()
    if require_private_comparison:
        _check_private_artifacts()
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-private-comparison", action="store_true")
    args = parser.parse_args()
    try:
        validate(require_private_comparison=args.require_private_comparison)
    except ValidationError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print("PASS: KMFA v0.1.4 raw comparison after owner anchor confirmation artifacts validated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
