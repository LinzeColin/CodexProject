#!/usr/bin/env python3
"""Validate the global residual replay phase and its private evidence boundary."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from KMFA.tools import (  # noqa: E402
    v014_global_residual_difference_queue_replay_or_authoritative_exclusion as phase,
)


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    _require(isinstance(value, dict), f"{path} must contain a JSON object")
    return value


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            value = json.loads(line)
            _require(isinstance(value, dict), f"{path} must contain JSON objects")
            rows.append(value)
    return rows


def _tracked(path: Path) -> bool:
    return subprocess.run(
        ["git", "ls-files", "--error-unmatch", path.as_posix()],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    ).returncode == 0


def _validate_public_artifacts() -> dict[str, Any]:
    public_paths = [
        phase.SUMMARY_PATH,
        phase.MANIFEST_PATH,
        phase.GO_NO_GO_PATH,
        phase.MATRIX_PATH,
        phase.METADATA_SUMMARY_PATH,
        phase.METADATA_MANIFEST_PATH,
        phase.METADATA_GO_NO_GO_PATH,
        phase.METADATA_MATRIX_PATH,
        phase.REPORT_PATH,
        phase.GO_NO_GO_RECORD_PATH,
        phase.TEST_RESULTS_PATH,
        phase.RISK_REGISTER_PATH,
        phase.ROLLBACK_PATH,
    ]
    for path in public_paths:
        _require(path.is_file(), f"missing public artifact: {path}")

    summary = _read_json(phase.SUMMARY_PATH)
    manifest = _read_json(phase.MANIFEST_PATH)
    go_no_go = _read_json(phase.GO_NO_GO_PATH)
    matrix = _read_json(phase.MATRIX_PATH)
    _require(summary == _read_json(phase.METADATA_SUMMARY_PATH), "summary mirror drift")
    _require(manifest == _read_json(phase.METADATA_MANIFEST_PATH), "manifest mirror drift")
    _require(go_no_go == _read_json(phase.METADATA_GO_NO_GO_PATH), "go/no-go mirror drift")
    _require(matrix == _read_json(phase.METADATA_MATRIX_PATH), "matrix mirror drift")

    expected = {
        "global_residual_queue_record_count": 72,
        "classified_residual_record_count": 72,
        "private_target_materialization_replay_count": 37,
        "integer_metric_formula_replay_count": 16,
        "replayed_numeric_record_count": 53,
        "owner_authorized_non_numeric_exclusion_count": 8,
        "queue_closed_or_excluded_count": 61,
        "open_residual_difference_count": 11,
        "open_ambiguous_source_count": 8,
        "open_final_difference_accepted_count": 3,
        "nonzero_delta_reconciliation_count": 9,
        "zero_delta_reconciliation_count": 2,
        "incomplete_reconciliation_count": 1,
        "forced_zero_materialization_count": 0,
    }
    for key, value in expected.items():
        _require(summary.get(key) == value, f"summary {key} changed")
    for key in (
        "source_private_inputs_unchanged",
        "existing_comparisons_unchanged",
        "owner_authorized_exclusion",
        "global_residual_queue_replay_performed",
        "raw_snapshot_exact_match",
        "private_outputs_gitignored",
    ):
        _require(summary.get(key) is True, f"summary {key} must be true")
    for key in (
        "global_residual_queue_fully_closed",
        "full_raw_to_processed_value_comparison_complete",
        "business_value_consistency_verified",
        "raw_inbox_mutated_by_this_phase",
        "stage_review_performed",
        "github_upload_performed",
        "app_reinstall_performed",
        "business_execution_performed",
    ):
        _require(summary.get(key) is False, f"summary {key} must be false")
    _require(summary.get("decision") == "NO_GO", "phase decision must remain NO_GO")
    _require(matrix.get("check_count") == 20, "matrix check count changed")
    _require(matrix.get("check_pass_count") == 20, "matrix must fully pass")
    _require(matrix.get("check_fail_count") == 0, "matrix must have no failures")
    _require(all(row.get("passed") is True for row in matrix.get("checks", [])), "matrix row failed")
    _require(go_no_go.get("decision") == "NO_GO", "go/no-go decision changed")
    _require(go_no_go.get("open_residual_difference_count") == 11, "go/no-go open count changed")

    safety = manifest.get("public_repo_safety", {})
    _require(safety.get("aggregate_only") is True, "manifest must remain aggregate-only")
    for key, value in safety.items():
        if key != "aggregate_only":
            _require(value is False, f"public safety flag {key} must be false")
    boundaries = manifest.get("phase_boundaries", {})
    _require(boundaries.get("single_phase_only") is True, "single-phase boundary missing")
    _require(boundaries.get("unproven_values_forced_closed") is False, "unproven values were forced closed")
    _require(boundaries.get("existing_nonzero_differences_overwritten") is False, "nonzero differences were overwritten")
    _require(boundaries.get("github_upload_performed") is False, "GitHub upload is out of scope")

    forbidden_public_tokens = (
        "target_slot_id",
        "canonical_value_fingerprint",
        "private_processed_ref",
        "raw_candidate_record_ref_hash",
        "authorization_basis_hash",
        ".codex_private_runtime",
    )
    for path in public_paths:
        text = path.read_text(encoding="utf-8")
        for token in forbidden_public_tokens:
            _require(token not in text, f"private token leaked to public artifact {path}: {token}")
    return summary


def _validate_private_evidence(summary: dict[str, Any]) -> None:
    for path in phase.phase_private_paths():
        _require(path.is_file(), f"missing private evidence: {path}")
        _require(phase._git_ignored(path), f"private evidence is not ignored: {path}")
        _require(not _tracked(path), f"private evidence is tracked: {path}")

    records = _read_jsonl(phase.PRIVATE_REPLAY_RECORDS_PATH)
    open_rows = _read_jsonl(phase.PRIVATE_OPEN_DIFFERENCES_PATH)
    receipt = _read_json(phase.PRIVATE_AUTHORIZATION_RECEIPT_PATH)
    diagnostic = _read_json(phase.PRIVATE_DIAGNOSTIC_PATH)
    _require(len(records) == 72, "private replay record count changed")
    _require(len(open_rows) == 11, "private open difference count changed")
    _require(len({row.get("target_slot_id") for row in records}) == 72, "private slots must be unique")
    status_counts = Counter(str(row.get("replay_status")) for row in records)
    _require(
        status_counts
        == Counter(
            {
                "replayed_private_integer_value": 37,
                "replayed_private_integer_formula": 16,
                "owner_authorized_non_numeric_exclusion": 8,
                "open_missing_unique_authoritative_source": 8,
                "open_final_difference_accepted": 3,
            }
        ),
        "private status counts changed",
    )
    _require(sum(row.get("queue_closed") is True for row in records) == 61, "closed count changed")
    _require(sum(row.get("queue_closed") is False for row in records) == 11, "open count changed")
    _require(all(row.get("forced_zero_applied") is False for row in records), "forced zero detected")
    _require(all(row.get("preserves_existing_nonzero_differences") is True for row in records), "nonzero guard missing")
    _require(not phase._contains_float(records), "private records contain floats")
    numeric = [row for row in records if row.get("evidence_kind") in {"materialized_target", "integer_metric"}]
    _require(len(numeric) == 53, "numeric replay count changed")
    for row in numeric:
        expected = phase.canonical_value_fingerprint(str(row.get("unit")), row.get("value"))
        _require(row.get("canonical_value_fingerprint") == expected, "canonical fingerprint mismatch")
        _require(row.get("source_reference_unique") is True, "numeric source must be unique")
        _require(row.get("integer_formula_replayable") is True, "numeric formula must replay")

    _require(receipt.get("owner_authorized_exclusion") is True, "owner authorization receipt missing")
    _require(receipt.get("source_authorization_item_count") == 72, "authorization item count changed")
    _require(receipt.get("authorization_plaintext_committed") is False, "authorization plaintext boundary failed")
    current_hashes = {path.as_posix(): phase._sha256_file(path) for path in phase.source_private_paths()}
    _require(diagnostic.get("source_hashes_before") == current_hashes, "source hash before drift")
    _require(diagnostic.get("source_hashes_after") == current_hashes, "source hash after drift")
    _require(diagnostic.get("source_private_inputs_unchanged") is True, "private inputs changed")
    _require(diagnostic.get("existing_comparisons_unchanged") is True, "comparisons changed")
    current_raw = phase._raw_snapshot("validator")
    _require(
        phase._snapshot_core(current_raw) == phase._snapshot_core(_read_json(phase.PRIVATE_RAW_AFTER_PATH)),
        "raw inbox changed after phase generation",
    )
    _require(summary.get("raw_source_file_count") == current_raw.get("file_count"), "raw file count drift")
    report = phase.PRIVATE_DIFFERENCE_REPORT_PATH.read_text(encoding="utf-8")
    _require("继续未决的 11 条记录" in report, "Chinese private difference report is incomplete")


def _validate_governance() -> None:
    events = _read_jsonl(phase.DEVELOPMENT_EVENTS_PATH)
    stage_rows = _read_jsonl(phase.STAGE_STATUS_PATH)
    task_rows = _read_jsonl(phase.TASK_STATUS_PATH)
    _require(any(row.get("phase_id") == phase.PHASE_ID for row in events), "development event missing")
    _require(any(row.get("phase_id") == phase.PHASE_ID for row in stage_rows), "stage status missing")
    _require(any(row.get("phase_id") == phase.PHASE_ID for row in task_rows), "task status missing")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-private-evidence", action="store_true")
    args = parser.parse_args()
    summary = _validate_public_artifacts()
    if args.require_private_evidence:
        _validate_private_evidence(summary)
    _validate_governance()
    print(
        "PASS: global residual replay validator "
        f"classified={summary['classified_residual_record_count']} "
        f"closed_or_excluded={summary['queue_closed_or_excluded_count']} "
        f"open={summary['open_residual_difference_count']} "
        f"decision={summary['decision']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
