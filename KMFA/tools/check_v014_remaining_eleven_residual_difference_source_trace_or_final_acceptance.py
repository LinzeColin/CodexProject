#!/usr/bin/env python3
"""Validate the remaining-eleven source trace and final acceptance phase."""

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
    v014_remaining_eleven_residual_difference_source_trace_or_final_acceptance as phase,
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
    paths = [
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
    for path in paths:
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
        "source_open_residual_difference_count": 11,
        "source_open_ambiguous_cost_component_count": 8,
        "source_open_final_difference_accepted_count": 3,
        "authority_project_source_count": 4,
        "unique_authority_table_count": 4,
        "cost_component_source_evidence_count": 8,
        "cost_component_materialization_count": 8,
        "travel_materialization_count": 4,
        "interest_materialization_count": 4,
        "unique_source_record_count": 8,
        "pdf_table_engine_match_count": 8,
        "pdf_text_engine_match_count": 8,
        "pdf_cross_engine_match_count": 8,
        "travel_child_sum_exact_count": 4,
        "direct_expense_category_sum_exact_count": 4,
        "current_bound_authority_total_exact_count": 4,
        "authority_full_total_formula_exact_count": 4,
        "authority_full_total_formula_difference_count": 0,
        "classified_residual_record_count": 72,
        "prior_private_target_materialization_replay_count": 37,
        "prior_integer_metric_formula_replay_count": 16,
        "new_unique_authority_cost_component_replay_count": 8,
        "replayed_numeric_record_count": 61,
        "owner_authorized_non_numeric_exclusion_count": 8,
        "queue_closed_or_excluded_count": 69,
        "open_residual_difference_count": 3,
        "open_final_difference_accepted_count": 3,
        "nonzero_delta_reconciliation_count": 9,
        "zero_delta_reconciliation_count": 2,
        "incomplete_reconciliation_count": 1,
        "forced_zero_materialization_count": 0,
        "raw_source_file_count": 5,
    }
    for key, value in expected.items():
        _require(summary.get(key) == value, f"summary {key} changed")
    for key in (
        "source_private_inputs_unchanged",
        "existing_comparisons_unchanged",
        "raw_snapshot_chain_exact",
        "raw_snapshot_exact_match",
        "global_residual_queue_replay_performed",
        "global_residual_queue_final_disposition_complete",
        "private_outputs_gitignored",
    ):
        _require(summary.get(key) is True, f"summary {key} must be true")
    for key in (
        "raw_inbox_mutated_by_this_phase",
        "global_residual_queue_fully_closed",
        "full_raw_to_processed_value_comparison_complete",
        "business_value_consistency_verified",
        "stage_review_performed",
        "github_upload_performed",
        "app_reinstall_performed",
        "business_execution_performed",
    ):
        _require(summary.get(key) is False, f"summary {key} must be false")
    _require(summary.get("decision") == "NO_GO", "decision must remain NO_GO")
    _require(matrix.get("check_count") == 25, "matrix check count changed")
    _require(matrix.get("check_pass_count") == 25, "matrix must fully pass")
    _require(matrix.get("check_fail_count") == 0, "matrix must have no failures")
    _require(all(row.get("passed") is True for row in matrix.get("checks", [])), "matrix row failed")
    _require(go_no_go.get("decision") == "NO_GO", "go/no-go decision changed")
    _require(go_no_go.get("open_final_difference_accepted_count") == 3, "go/no-go open count changed")

    safety = manifest.get("public_repo_safety", {})
    _require(safety.get("aggregate_only") is True, "manifest must remain aggregate-only")
    for key, value in safety.items():
        if key != "aggregate_only":
            _require(value is False, f"public safety flag {key} must be false")
    boundaries = manifest.get("phase_boundaries", {})
    _require(boundaries.get("single_phase_only") is True, "single-phase boundary missing")
    _require(boundaries.get("cost_component_source_trace_performed") is True, "source trace missing")
    _require(boundaries.get("final_cash_difference_acceptance_preserved") is True, "final acceptance missing")
    _require(boundaries.get("unproven_cash_values_materialized") is False, "unproven cash was materialized")
    _require(boundaries.get("forced_zero_materialization_allowed") is False, "forced zero is allowed")
    _require(boundaries.get("existing_nonzero_differences_overwritten") is False, "nonzero differences overwritten")

    forbidden_tokens = (
        "target_slot_id",
        "source_record_ref_hash",
        "raw_file_name",
        "archive_member_name",
        "candidate_label",
        "canonical_value_fingerprint",
        "private_processed_ref",
        ".codex_private_runtime",
    )
    for path in paths:
        text = path.read_text(encoding="utf-8")
        for token in forbidden_tokens:
            _require(token not in text, f"private token leaked to {path}: {token}")
    return summary


def _validate_private_evidence(summary: dict[str, Any]) -> None:
    for path in phase.phase_private_paths():
        _require(path.is_file(), f"missing private evidence: {path}")
        _require(phase._git_ignored(path), f"private evidence not ignored: {path}")
        _require(not _tracked(path), f"private evidence is tracked: {path}")

    tables = _read_json(phase.PRIVATE_AUTHORITY_TABLES_PATH).get("records", [])
    evidence = _read_jsonl(phase.PRIVATE_SOURCE_EVIDENCE_PATH)
    materializations = _read_jsonl(phase.PRIVATE_MATERIALIZATIONS_PATH)
    final_records = _read_jsonl(phase.PRIVATE_FINAL_REPLAY_RECORDS_PATH)
    open_rows = _read_jsonl(phase.PRIVATE_OPEN_CASH_DIFFERENCES_PATH)
    diagnostic = _read_json(phase.PRIVATE_DIAGNOSTIC_PATH)
    _require(len(tables) == 4, "private authority table count changed")
    _require(len(evidence) == 8, "private source evidence count changed")
    _require(len(materializations) == 8, "private materialization count changed")
    _require(len(final_records) == 72, "private final replay count changed")
    _require(len(open_rows) == 3, "private final accepted cash count changed")
    _require(len({row.get("target_slot_id") for row in materializations}) == 8, "materialization slots not unique")
    _require(len({row.get("source_record_ref_hash") for row in evidence}) == 8, "source records not unique")
    for row in evidence:
        _require(row.get("project_binding_unique") is True, "project binding is not unique")
        _require(row.get("source_table_unique") is True, "authority table is not unique")
        _require(row.get("component_row_unique") is True, "component row is not unique")
        _require(row.get("amount_column_unique") is True, "amount column is not unique")
        _require(row.get("pdf_table_engine_match") is True, "table engine mismatch")
        _require(row.get("pdf_text_engine_match") is True, "text engine mismatch")
        _require(row.get("direct_expense_category_sum_exact") is True, "direct expense formula mismatch")
        _require(row.get("current_bound_authority_total_exact") is True, "authority total mismatch")
        _require(row.get("full_table_total_formula_exact") is True, "full authority table formula mismatch")
        value = row.get("value_cents")
        _require(isinstance(value, int) and not isinstance(value, bool), "source value is not integer cents")
        expected = phase.prior_phase.canonical_value_fingerprint("cents", value)
        _require(row.get("value_fingerprint") == expected, "source fingerprint mismatch")
        if row.get("context_group") == "travel":
            _require(row.get("travel_child_sum_exact") is True, "travel child sum mismatch")
    for row in materializations:
        value = row.get("value")
        _require(isinstance(value, int) and not isinstance(value, bool), "materialized value is not integer")
        _require(row.get("unit") == "cents", "materialized unit changed")
        _require(
            row.get("value_fingerprint")
            == phase.prior_phase.canonical_value_fingerprint("cents", value),
            "materialized fingerprint mismatch",
        )
        _require(row.get("materialization_status") == "materialized_from_unique_authority_pdf_table", "materialization status changed")
    status_counts = Counter(str(row.get("replay_status")) for row in final_records)
    _require(
        status_counts
        == Counter(
            {
                "replayed_private_integer_value": 37,
                "replayed_private_integer_formula": 16,
                "owner_authorized_non_numeric_exclusion": 8,
                "replayed_unique_authority_cost_component": 8,
                "open_final_difference_accepted": 3,
            }
        ),
        "final private status counts changed",
    )
    _require(sum(row.get("queue_closed") is True for row in final_records) == 69, "closed count changed")
    _require(sum(row.get("queue_closed") is False for row in final_records) == 3, "open count changed")
    _require(all(row.get("forced_zero_applied") is False for row in final_records), "forced zero detected")
    for row in open_rows:
        _require(row.get("final_acceptance_status") == "accepted_without_proven_numeric_value", "cash acceptance changed")
        _require(row.get("new_raw_evidence_available") is False, "unexpected new cash evidence claimed")
        _require(row.get("raw_snapshot_chain_exact") is True, "raw snapshot chain changed")
        _require(row.get("source_reference_unique") is False, "unproven cash source marked unique")
        _require("value" not in row or row.get("value") is None, "unproven cash value was materialized")
    _require(not phase._contains_float([tables, evidence, materializations, final_records]), "private outputs contain floats")

    current_hashes = {path.as_posix(): phase._sha256_file(path) for path in phase.source_private_paths()}
    _require(diagnostic.get("source_hashes_before") == current_hashes, "source hash before drift")
    _require(diagnostic.get("source_hashes_after") == current_hashes, "source hash after drift")
    _require(diagnostic.get("source_private_inputs_unchanged") is True, "source inputs changed")
    _require(diagnostic.get("existing_comparisons_unchanged") is True, "comparison input changed")
    _require(diagnostic.get("raw_snapshot_chain_exact") is True, "raw chain is not exact")
    current_raw = phase.prior_phase._raw_snapshot("validator")
    _require(
        phase._normalize_snapshot(current_raw)
        == phase._normalize_snapshot(_read_json(phase.PRIVATE_RAW_AFTER_PATH)),
        "raw inbox changed after generation",
    )
    _require(current_raw.get("file_count") == summary.get("raw_source_file_count"), "raw file count drift")
    report = phase.PRIVATE_FINAL_DIFFERENCE_REPORT_PATH.read_text(encoding="utf-8")
    _require("最终接受但不生成数值的现金差异" in report, "Chinese final difference report incomplete")


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
        "PASS: remaining eleven trace validator "
        f"resolved={summary['cost_component_materialization_count']} "
        f"closed_or_excluded={summary['queue_closed_or_excluded_count']} "
        f"open={summary['open_residual_difference_count']} "
        f"decision={summary['decision']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
