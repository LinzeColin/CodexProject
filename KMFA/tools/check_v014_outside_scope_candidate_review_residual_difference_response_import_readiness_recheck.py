#!/usr/bin/env python3
"""Validate residual-difference response-import readiness recheck."""

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

from KMFA.tools.v014_outside_scope_candidate_review_residual_difference_response_import_readiness_recheck import (  # noqa: E402
    ACCEPTANCE_ID,
    DECISION,
    EXPECTED_DECISION_COUNTS,
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
    PRIVATE_READINESS_DIAGNOSTIC_PATH,
    PRIVATE_REPORT_PATH,
    PRIVATE_SOURCE_MAP_BLOCKER_QUEUE_PATH,
    READINESS_CONCLUSION,
    REPORT_PATH,
    RISK_REGISTER_PATH,
    ROLLBACK_PATH,
    SOURCE_GO_NO_GO_PATH,
    SOURCE_MANIFEST_PATH,
    SOURCE_MATRIX_PATH,
    SOURCE_PRIVATE_NON_ACTIONABLE_QUEUE_PATH,
    SOURCE_PRIVATE_RESPONSE_ITEMS_PATH,
    SOURCE_PRIVATE_RESPONSE_RECORD_PATH,
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
    re.compile(r"\.(xlsx|xlsm|xls|zip|pdf)\b", re.IGNORECASE),
    re.compile(r"sha256:[0-9a-f]{64}"),
    re.compile(r'"[0-9a-f]{64}"'),
    re.compile(
        r'"(raw_file_name|archive_member_name|sheet_name|cell_address|raw_value|normalized_decimal|'
        r"context_text|numeric_value_fingerprint|processed_value_fingerprint|value_fingerprint|target_slot_id|"
        r"source_ref_hash|source_record_ref_hash|private_processed_ref_hash)\"",
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
        raise ValidationError(f"missing jsonl: {path}")
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
        "source_response_import_public_summary_read_by_this_phase",
        "source_response_import_public_manifest_read_by_this_phase",
        "source_response_import_private_record_read_by_this_phase",
        "source_response_import_private_items_read_by_this_phase",
        "source_response_import_private_non_actionable_queue_read_by_this_phase",
        "private_readiness_diagnostic_written_by_this_phase",
        "private_source_map_blocker_queue_written_by_this_phase",
    ):
        _require_true(f"raw_boundary.{key}", raw_boundary.get(key))
    for key, value in raw_boundary.items():
        if key.startswith("raw_inbox_") or key.endswith("_mutated_by_this_phase"):
            _require_false(f"raw_boundary.{key}", value)
    for key in (
        "source_response_import_private_record_mutated_by_this_phase",
        "source_response_import_private_items_mutated_by_this_phase",
        "source_response_import_private_non_actionable_queue_mutated_by_this_phase",
        "discrepancy_closure_written_by_this_phase",
        "source_map_correction_written_by_this_phase",
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
    _require_equal("summary.readiness_conclusion", summary.get("readiness_conclusion"), READINESS_CONCLUSION)
    _require_equal(
        "summary.source phase",
        summary.get("source_phase_id"),
        "V014_OUTSIDE_SCOPE_CANDIDATE_REVIEW_RESIDUAL_DIFFERENCE_OWNER_OR_AGENT_DIAGNOSTIC_RESPONSE_IMPORT",
    )
    _require_equal("summary.source go/no-go", summary.get("source_go_no_go_decision"), "NO_GO")
    _require_equal("summary.source matrix fail", summary.get("source_matrix_check_fail_count"), 0)
    _require_equal("summary.source record", summary.get("source_response_record_item_count"), 72)
    _require_equal("summary.source items", summary.get("source_response_item_count"), 72)
    _require_equal("summary.source non actionable", summary.get("source_non_actionable_queue_item_count"), 72)
    _require_equal("summary.valid", summary.get("valid_diagnostic_response_count"), 72)
    _require_equal("summary.imported", summary.get("valid_diagnostic_response_imported_count"), 72)
    _require_equal("summary.pending", summary.get("pending_diagnostic_response_count"), 0)
    _require_equal("summary.response blocker", summary.get("diagnostic_response_blocker_count"), 0)
    _require_equal("summary.invalid", summary.get("invalid_diagnostic_response_count"), 0)
    _require_equal("summary.non actionable", summary.get("non_actionable_diagnostic_response_count"), 72)
    _require_equal("summary.source map actionable", summary.get("source_map_actionable_response_count"), 0)
    _require_equal("summary.actionable", summary.get("actionable_resolution_count"), 0)
    _require_equal("summary.open", summary.get("open_residual_difference_count"), 72)
    _require_equal("summary.closed", summary.get("closed_discrepancy_count"), 0)
    _require_equal("summary.safe auto", summary.get("safe_auto_resolution_count"), 0)
    for track, count in EXPECTED_TRACK_COUNTS.items():
        _require_equal(f"summary.{track}_count", summary.get(f"{track}_count"), count)
    for decision, count in EXPECTED_DECISION_COUNTS.items():
        _require_equal(f"summary.{decision}_count", summary.get(f"{decision}_count"), count)
    for key in (
        "response_import_readiness_recheck_performed",
        "missing_response_blocker_cleared",
        "private_readiness_diagnostic_written",
        "private_source_map_blocker_queue_written",
        "private_report_written",
        "private_readiness_diagnostic_gitignored",
        "private_source_map_blocker_queue_gitignored",
        "private_report_gitignored",
    ):
        _require_true(f"summary.{key}", summary.get(key))
    _require_equal("summary.source map blocker count", summary.get("source_map_correction_blocker_count"), 72)
    for key in (
        "source_map_correction_ready",
        "source_map_correction_written_by_this_phase",
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
    _check_raw_boundary(summary.get("raw_boundary", {}))
    _check_public_safety(summary.get("public_safety", {}))

    _require_equal("matrix.count", matrix.get("check_count"), 13)
    _require_equal("matrix.pass", matrix.get("check_pass_count"), 13)
    _require_equal("matrix.fail", matrix.get("check_fail_count"), 0)
    checks = {row.get("check_code"): row.get("status") for row in matrix.get("checks", []) if isinstance(row, dict)}
    for code in (
        "source_response_import_loaded",
        "source_response_import_valid",
        "valid_responses_present",
        "missing_response_blocker_cleared",
        "all_responses_non_actionable",
        "source_map_actionability_absent",
        "all_residual_differences_still_open",
        "no_discrepancy_closure",
        "source_map_correction_blocked",
        "track_counts_locked",
        "decision_counts_locked",
        "raw_inbox_untouched",
        "downstream_gates_closed",
    ):
        _require_equal(f"matrix.{code}", checks.get(code), "PASS")

    _require_equal("go_no_go.phase_id", go_no_go.get("phase_id"), PHASE_ID)
    _require_equal("go_no_go.decision", go_no_go.get("decision"), DECISION)
    _require_true("go_no_go.missing response blocker cleared", go_no_go.get("missing_response_blocker_cleared"))
    _require_equal("go_no_go.source map blockers", go_no_go.get("source_map_correction_blocker_count"), 72)
    _require_false("go_no_go.source map ready", go_no_go.get("source_map_correction_ready"))
    _require_false("go_no_go.raw comparison", go_no_go.get("raw_to_processed_value_comparison_allowed"))
    _require_false("go_no_go.business consistency", go_no_go.get("business_value_consistency_verified"))
    _require_false("go_no_go.github upload", go_no_go.get("github_upload_allowed"))
    _require_false("go_no_go.app reinstall", go_no_go.get("app_reinstall_allowed"))
    _require_false("go_no_go.business execution", go_no_go.get("business_execution_allowed"))
    _require_equal("go_no_go.next_required_input", go_no_go.get("next_required_input"), NEXT_REQUIRED_INPUT)
    _require_equal("manifest.summary", manifest.get("summary"), summary)
    _require_equal("manifest.matrix", manifest.get("matrix"), matrix)
    _require_equal("manifest.go_no_go", manifest.get("go_no_go_report"), go_no_go)


def _check_private_artifacts() -> None:
    private_paths = (
        SOURCE_PRIVATE_RESPONSE_RECORD_PATH,
        SOURCE_PRIVATE_RESPONSE_ITEMS_PATH,
        SOURCE_PRIVATE_NON_ACTIONABLE_QUEUE_PATH,
        PRIVATE_READINESS_DIAGNOSTIC_PATH,
        PRIVATE_SOURCE_MAP_BLOCKER_QUEUE_PATH,
        PRIVATE_REPORT_PATH,
    )
    for path in private_paths:
        if not path.exists():
            raise ValidationError(f"missing private artifact: {path}")
        if not _git_check_ignored(path):
            raise ValidationError(f"private artifact is not git-ignored: {path}")
    _read_json(SOURCE_SUMMARY_PATH)
    _read_json(SOURCE_MANIFEST_PATH)
    _read_json(SOURCE_GO_NO_GO_PATH)
    _read_json(SOURCE_MATRIX_PATH)
    source_record = _read_json(SOURCE_PRIVATE_RESPONSE_RECORD_PATH)
    source_items = _read_jsonl(SOURCE_PRIVATE_RESPONSE_ITEMS_PATH)
    source_non_actionable = _read_jsonl(SOURCE_PRIVATE_NON_ACTIONABLE_QUEUE_PATH)
    diagnostic = _read_json(PRIVATE_READINESS_DIAGNOSTIC_PATH)
    blockers = _read_jsonl(PRIVATE_SOURCE_MAP_BLOCKER_QUEUE_PATH)
    _require_equal("source record rows", len(source_record.get("response_items", [])), 72)
    _require_equal("source item rows", len(source_items), 72)
    _require_equal("source non actionable rows", len(source_non_actionable), 72)
    _require_equal("diagnostic blocker rows", len(diagnostic.get("blocker_rows", [])), 72)
    _require_equal("blocker rows", len(blockers), 72)
    source_targets = {row.get("target_slot_id") for row in source_items}
    blocker_targets = {row.get("target_slot_id") for row in blockers}
    _require_equal("private target sets", source_targets, blocker_targets)
    for item in source_items:
        _require_true("source valid", item.get("valid_diagnostic_response"))
        _require_false("source actionable", item.get("actionable_resolution_ready"))
        _require_false("source map ready", item.get("source_map_correction_ready_after_import"))
        _require_false("source closed", item.get("discrepancy_closed_by_this_phase"))
    for blocker in blockers:
        _require_false("blocker source map", blocker.get("source_map_correction_ready_after_recheck"))
        _require_false("blocker closed", blocker.get("discrepancy_closed_after_recheck"))
        _require_false("blocker public", blocker.get("public_commit_allowed"))
    tracked = set(_git_output(["ls-files", "KMFA"]).splitlines())
    for path in private_paths:
        if path.as_posix() in tracked:
            raise ValidationError(f"private artifact is tracked: {path}")


def validate(*, require_private_readiness: bool = False) -> dict[str, Any]:
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
    _check_summary(summary, matrix, go_no_go, manifest)
    _check_public_artifacts()
    _check_no_raw_private_files_tracked()
    if require_private_readiness:
        _check_private_artifacts()
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-private-readiness", action="store_true")
    args = parser.parse_args()
    try:
        validate(require_private_readiness=args.require_private_readiness)
    except ValidationError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print("PASS: KMFA v0.1.4 residual difference response-import readiness recheck artifacts validated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
