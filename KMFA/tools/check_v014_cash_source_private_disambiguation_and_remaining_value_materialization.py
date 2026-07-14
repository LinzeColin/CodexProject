#!/usr/bin/env python3
"""Validate private cash-source disambiguation and remaining value materialization."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from KMFA.tools import (  # noqa: E402
    v014_cash_source_private_disambiguation_and_remaining_value_materialization as phase,
)


class ValidationError(RuntimeError):
    pass


def _require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValidationError(f"{path} must contain a JSON object")
    return value


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if not all(isinstance(row, dict) for row in rows):
        raise ValidationError(f"{path} must contain JSON objects")
    return rows


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _git_ignored(path: Path) -> bool:
    return (
        subprocess.run(
            ["git", "check-ignore", "-q", path.as_posix()],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        ).returncode
        == 0
    )


def _contains_float(value: Any) -> bool:
    if isinstance(value, float):
        return True
    if isinstance(value, dict):
        return any(_contains_float(child) for child in value.values())
    if isinstance(value, list):
        return any(_contains_float(child) for child in value)
    return False


def _snapshot_core(snapshot: dict[str, Any]) -> dict[str, Any]:
    return {
        "file_count": snapshot.get("file_count"),
        "total_bytes": snapshot.get("total_bytes"),
        "extension_counts": snapshot.get("extension_counts"),
        "records_sha256": snapshot.get("records_sha256"),
        "records": snapshot.get("records"),
    }


def _public_paths() -> list[Path]:
    return [
        phase.SUMMARY_PATH,
        phase.MANIFEST_PATH,
        phase.GO_NO_GO_PATH,
        phase.MATRIX_PATH,
        phase.REPORT_PATH,
        phase.GO_NO_GO_RECORD_PATH,
        phase.TEST_RESULTS_PATH,
        phase.RISK_REGISTER_PATH,
        phase.ROLLBACK_PATH,
        phase.METADATA_SUMMARY_PATH,
        phase.METADATA_MANIFEST_PATH,
        phase.METADATA_GO_NO_GO_PATH,
        phase.METADATA_MATRIX_PATH,
    ]


def _private_paths() -> list[Path]:
    return [
        phase.PRIVATE_SOURCE_SPEC_PATH,
        phase.PRIVATE_RAW_BEFORE_PATH,
        phase.PRIVATE_RAW_AFTER_PATH,
        phase.PRIVATE_WPS_DIAGNOSTIC_PATH,
        phase.PRIVATE_LEDGER_EVIDENCE_PATH,
        phase.PRIVATE_CASH_DECISIONS_PATH,
        phase.PRIVATE_CASH_METRICS_PATH,
        phase.PRIVATE_TARGET_MATERIALIZATIONS_PATH,
        phase.PRIVATE_UNRESOLVED_TARGETS_PATH,
        phase.PRIVATE_RECONCILIATION_COMPARISONS_PATH,
        phase.PRIVATE_DIAGNOSTIC_PATH,
        phase.PRIVATE_DIFFERENCE_REPORT_PATH,
    ]


def _raw_name_fragments(snapshot: dict[str, Any]) -> set[str]:
    fragments: set[str] = set()
    for record in snapshot.get("records", []):
        if not isinstance(record, dict):
            continue
        for key, value in record.items():
            normalized_key = str(key).lower()
            if not isinstance(value, str):
                continue
            if any(token in normalized_key for token in ("path", "name", "member", "sheet")):
                fragments.add(value)
                fragments.add(Path(value).name)
    return {fragment for fragment in fragments if len(fragment) >= 4}


def _validate_public_artifacts(errors: list[str]) -> tuple[dict[str, Any], dict[str, Any]]:
    for path in _public_paths():
        _require(path.exists(), f"missing public artifact: {path}", errors)
    if errors:
        raise ValidationError("\n".join(f"- {error}" for error in errors))

    summary = _read_json(phase.SUMMARY_PATH)
    manifest = _read_json(phase.MANIFEST_PATH)
    go_no_go = _read_json(phase.GO_NO_GO_PATH)
    matrix = _read_json(phase.MATRIX_PATH)
    _require(
        summary == _read_json(phase.METADATA_SUMMARY_PATH),
        "summary metadata mirror mismatch",
        errors,
    )
    _require(
        manifest == _read_json(phase.METADATA_MANIFEST_PATH),
        "manifest metadata mirror mismatch",
        errors,
    )
    _require(
        go_no_go == _read_json(phase.METADATA_GO_NO_GO_PATH),
        "go/no-go metadata mirror mismatch",
        errors,
    )
    _require(
        matrix == _read_json(phase.METADATA_MATRIX_PATH),
        "matrix metadata mirror mismatch",
        errors,
    )

    expected_summary = {
        "phase_id": phase.PHASE_ID,
        "task_id": phase.TASK_ID,
        "status": phase.STATUS,
        "decision": "NO_GO",
        "source_private_inputs_unchanged": True,
        "cash_project_candidate_count": 4,
        "cash_project_resolved_count": 1,
        "cash_project_unresolved_count": 3,
        "private_cash_metric_record_count": 3,
        "materialized_business_value_target_slot_count": 31,
        "newly_materialized_cash_target_slot_count": 3,
        "unresolved_cash_value_target_slot_count": 9,
        "reconciliation_record_count": 12,
        "completed_reconciliation_comparison_count": 9,
        "zero_delta_reconciliation_count": 2,
        "nonzero_delta_reconciliation_count": 7,
        "incomplete_cash_reconciliation_count": 3,
        "external_wps_source_count": 2,
        "external_wps_readable_count": 0,
        "external_crosscheck_completed": False,
        "false_wps_readability_claim_count": 0,
        "forced_zero_materialization_count": 0,
        "global_unresolved_difference_count": 72,
        "global_residual_difference_queue_replayed": False,
        "partial_processed_value_materialization_complete": True,
        "full_processed_value_materialization_complete": False,
        "partial_raw_to_processed_reconciliation_performed": True,
        "full_raw_to_processed_value_comparison_complete": False,
        "processed_consistency_verified": False,
        "business_value_consistency_verified": False,
        "raw_snapshot_exact_match": True,
        "raw_inbox_mutated_by_this_phase": False,
        "raw_business_data_committed": False,
        "raw_filename_or_value_committed": False,
        "credential_or_secret_committed": False,
        "stage_review_performed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
    }
    for key, expected in expected_summary.items():
        _require(summary.get(key) == expected, f"summary {key} must equal {expected!r}", errors)

    _require(matrix.get("check_count") == 18, "matrix check count must be 18", errors)
    _require(matrix.get("check_pass_count") == 18, "matrix pass count must be 18", errors)
    _require(matrix.get("check_fail_count") == 0, "matrix must have zero failures", errors)
    _require(go_no_go.get("decision") == "NO_GO", "go/no-go decision must be NO_GO", errors)
    _require(go_no_go.get("cash_project_unresolved_count") == 3, "go/no-go unresolved project count must be 3", errors)
    _require(go_no_go.get("unresolved_cash_value_target_slot_count") == 9, "go/no-go unresolved cash target count must be 9", errors)
    _require(go_no_go.get("nonzero_delta_reconciliation_count") == 7, "go/no-go nonzero count must be 7", errors)
    _require(go_no_go.get("incomplete_cash_reconciliation_count") == 3, "go/no-go incomplete comparison count must be 3", errors)

    safety = manifest.get("public_repo_safety", {})
    _require(safety.get("aggregate_only") is True, "manifest must remain aggregate-only", errors)
    for key in (
        "raw_file_committed",
        "raw_filename_committed",
        "raw_hash_committed",
        "identity_plaintext_committed",
        "business_value_committed",
        "private_ref_committed",
        "credential_or_secret_committed",
    ):
        _require(safety.get(key) is False, f"manifest safety flag {key} must be false", errors)
    boundaries = manifest.get("phase_boundaries", {})
    _require(boundaries.get("single_phase_only") is True, "single-phase boundary missing", errors)
    _require(boundaries.get("external_wps_content_read_claimed") is False, "WPS content must not be claimed readable", errors)
    _require(boundaries.get("forced_zero_materialization_allowed") is False, "forced zero must be prohibited", errors)
    for key in (
        "global_residual_queue_replayed",
        "stage_review_performed",
        "github_upload_performed",
        "app_reinstall_performed",
        "business_execution_performed",
    ):
        _require(boundaries.get(key) is False, f"phase boundary {key} must be false", errors)

    public_text = "\n".join(path.read_text(encoding="utf-8") for path in _public_paths())
    forbidden_public_fragments = (
        "project_code",
        "alias_tokens",
        "raw_archive_path",
        "inner_workbook_member_contains",
        "archive_member_name",
        "sheet_name",
        "cell_address",
        "project_name_private_value",
        "private_processed_ref\"",
        "collection_amount_cents\"",
        "cash_paid_cost_cents\"",
        "cash_gross_profit_cents\"",
        "source_hashes_before",
        "records_sha256",
    )
    for fragment in forbidden_public_fragments:
        _require(fragment not in public_text, f"private fragment leaked to public artifacts: {fragment}", errors)
    return summary, manifest


def _validate_private_materialization(summary: dict[str, Any], errors: list[str]) -> None:
    for path in _private_paths():
        _require(path.exists(), f"missing private artifact: {path}", errors)
        _require(_git_ignored(path), f"private artifact is not gitignored: {path}", errors)
    for path in phase.source_private_paths():
        _require(path.exists(), f"missing private source input: {path}", errors)
        _require(_git_ignored(path), f"private source input is not gitignored: {path}", errors)
    if errors:
        return

    before = _read_json(phase.PRIVATE_RAW_BEFORE_PATH)
    after = _read_json(phase.PRIVATE_RAW_AFTER_PATH)
    current = phase._raw_snapshot("validator")
    wps = _read_json(phase.PRIVATE_WPS_DIAGNOSTIC_PATH)
    ledger = _read_json(phase.PRIVATE_LEDGER_EVIDENCE_PATH)
    decisions = _read_jsonl(phase.PRIVATE_CASH_DECISIONS_PATH)
    cash_metrics = _read_jsonl(phase.PRIVATE_CASH_METRICS_PATH)
    materialized = _read_jsonl(phase.PRIVATE_TARGET_MATERIALIZATIONS_PATH)
    unresolved = _read_jsonl(phase.PRIVATE_UNRESOLVED_TARGETS_PATH)
    comparisons = _read_jsonl(phase.PRIVATE_RECONCILIATION_COMPARISONS_PATH)
    diagnostic = _read_json(phase.PRIVATE_DIAGNOSTIC_PATH)

    _require(_snapshot_core(before) == _snapshot_core(after), "private raw snapshots differ", errors)
    _require(_snapshot_core(after) == _snapshot_core(current), "current raw snapshot differs from phase after snapshot", errors)
    _require(diagnostic.get("raw_snapshot_exact_match") is True, "diagnostic raw match must be true", errors)
    _require(diagnostic.get("source_private_inputs_unchanged") is True, "private source inputs changed", errors)
    _require(summary.get("raw_source_file_count") == before.get("file_count"), "raw file count mismatch", errors)

    current_source_hashes = {
        path.as_posix(): _sha256_bytes(path.read_bytes()) for path in phase.source_private_paths()
    }
    _require(diagnostic.get("source_hashes_before") == current_source_hashes, "source hashes before mismatch", errors)
    _require(diagnostic.get("source_hashes_after") == current_source_hashes, "source hashes after mismatch", errors)

    _require(wps.get("source_count") == 2, "WPS diagnostic source count must be 2", errors)
    _require(wps.get("readable_count") == 0, "WPS diagnostic readable count must be 0", errors)
    _require(wps.get("false_readability_claim_count") == 0, "WPS false readability claim count must be 0", errors)
    wps_records = wps.get("records", [])
    _require(len(wps_records) == 2, "WPS diagnostic must contain two records", errors)
    for row in wps_records:
        _require(row.get("ole_container") is True, "WPS source must be an OLE container", errors)
        _require(row.get("standard_openxml_container") is False, "WPS source must not be claimed OpenXML", errors)
        _require(row.get("wps_content_stream_marker") is True, "WPS content marker missing", errors)
        _require(row.get("encryption_info_stream_marker") is True, "WPS transform marker missing", errors)
        _require(row.get("content_readable") is False, "WPS content must remain unreadable", errors)

    _require(ledger.get("raw_archive_read_only") is True, "ledger extraction must be read-only", errors)
    _require(ledger.get("integer_cents_only") is True, "ledger extraction must use integer cents", errors)
    _require(ledger.get("sheet_count", 0) > 0, "ledger sheet count must be positive", errors)
    _require(ledger.get("bank_sheet_count", 0) > 0, "ledger bank sheet count must be positive", errors)

    _require(len(decisions) == 4, "private cash decision count must be 4", errors)
    resolved = [row for row in decisions if row.get("resolution_status") == "resolved_accessible_ledger_only"]
    pending = [row for row in decisions if row.get("resolution_status") == "unresolved"]
    _require((len(resolved), len(pending)) == (1, 3), "cash decision status counts must be 1/3", errors)
    _require(all(row.get("zero_inferred_from_absence") is False for row in decisions), "absence must never be inferred as zero", errors)
    _require(all(row.get("external_crosscheck_completed") is False for row in decisions), "external crosscheck must remain incomplete", errors)
    _require(all(row.get("business_consistency_verified") is False for row in decisions), "business consistency must not be claimed", errors)
    _require(all(row.get("public_commit_allowed") is False for row in decisions), "cash decisions must prohibit public commit", errors)
    _require(all(row.get("raw_layer_write_allowed") is False for row in decisions), "cash decisions must prohibit raw writes", errors)
    for row in resolved:
        collection = row.get("collection_amount_cents")
        cash_paid = row.get("cash_paid_cost_cents")
        cash_gross = row.get("cash_gross_profit_cents")
        _require(all(isinstance(value, int) and not isinstance(value, bool) for value in (collection, cash_paid, cash_gross)), "resolved cash values must be integer cents", errors)
        _require(cash_gross == collection - cash_paid, "resolved cash gross profit formula mismatch", errors)
        _require(row.get("unresolved_row_count") == 0, "resolved project cannot retain unresolved rows", errors)
    for row in pending:
        _require(row.get("collection_amount_cents") is None, "unresolved collection must not be filled", errors)
        _require(row.get("cash_paid_cost_cents") is None, "unresolved paid cost must not be filled", errors)
        _require(row.get("cash_gross_profit_cents") is None, "unresolved cash gross profit must not be filled", errors)

    _require(len(cash_metrics) == 3, "private cash metric count must be 3", errors)
    _require(
        {row.get("metric_key") for row in cash_metrics}
        == {"collection_amount_cents", "cash_paid_cost_cents", "cash_gross_profit_cents"},
        "private cash metric keys mismatch",
        errors,
    )
    _require(all(isinstance(row.get("value"), int) and not isinstance(row.get("value"), bool) for row in cash_metrics), "cash metrics must be integer-only", errors)
    _require(all(row.get("public_commit_allowed") is False for row in cash_metrics), "cash metrics must prohibit public commit", errors)

    _require(len(materialized) == 31, "private target materialization count must be 31", errors)
    _require(len(unresolved) == 9, "private unresolved target count must be 9", errors)
    _require(len(comparisons) == 12, "private comparison count must be 12", errors)
    _require(not _contains_float([wps, ledger, decisions, cash_metrics, materialized, unresolved, comparisons]), "private outputs must not contain floats", errors)

    materialized_ids = {row.get("target_slot_id") for row in materialized}
    unresolved_ids = {row.get("target_slot_id") for row in unresolved}
    _require(len(materialized_ids) == 31, "materialized target ids must be unique", errors)
    _require(len(unresolved_ids) == 9, "unresolved target ids must be unique", errors)
    _require(not materialized_ids.intersection(unresolved_ids), "materialized and unresolved targets overlap", errors)
    _require(all(row.get("materialization_status") == "materialized_private_only" for row in materialized), "materialized targets must remain private-only", errors)
    _require(all(isinstance(row.get("value"), int) and not isinstance(row.get("value"), bool) for row in materialized), "materialized target values must be integer-only", errors)
    _require(all(row.get("public_commit_allowed") is False for row in materialized), "materialized targets must prohibit public commit", errors)
    _require(all(row.get("resolution_status") == "cash_source_disambiguation_required" for row in unresolved), "remaining targets must stay unresolved", errors)
    _require(all(row.get("public_commit_allowed") is False for row in unresolved), "unresolved targets must prohibit public commit", errors)

    completed = [row for row in comparisons if str(row.get("comparison_status", "")).startswith("comparison_complete_")]
    zero = [row for row in completed if row.get("delta") == 0]
    nonzero = [row for row in completed if row.get("delta") != 0]
    incomplete = [row for row in comparisons if row not in completed]
    _require((len(completed), len(zero), len(nonzero), len(incomplete)) == (9, 2, 7, 3), "comparison counts must be 9/2/7/3", errors)
    _require(all(row.get("delta") == row.get("amount_a") - row.get("amount_b") for row in completed), "completed comparison deltas must replay", errors)
    _require(all(row.get("difference_type") == "cash_vs_accrual_gross_profit" for row in incomplete), "incomplete comparisons must be cash-vs-accrual", errors)
    _require(all(row.get("amount_a") is None and row.get("delta") is None for row in incomplete), "incomplete comparisons must not be filled", errors)

    report = phase.PRIVATE_DIFFERENCE_REPORT_PATH.read_text(encoding="utf-8")
    for required_text in ("本轮结论", "项目逐项决策", "外部交叉核验来源", "剩余差异原因", "未把缺失值"):
        _require(required_text in report, f"private Chinese difference report missing: {required_text}", errors)

    public_text = "\n".join(path.read_text(encoding="utf-8") for path in _public_paths())
    for fragment in _raw_name_fragments(before):
        _require(fragment not in public_text, "raw filename or sheet name leaked to public artifacts", errors)


def validate(*, require_private_materialization: bool = False) -> dict[str, Any]:
    errors: list[str] = []
    summary, manifest = _validate_public_artifacts(errors)
    if require_private_materialization:
        _validate_private_materialization(summary, errors)
    if errors:
        raise ValidationError("\n".join(f"- {error}" for error in errors))
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-private-materialization", action="store_true")
    args = parser.parse_args()
    manifest = validate(require_private_materialization=args.require_private_materialization)
    summary = manifest["summary"]
    print(
        "cash source materialization validation: PASS "
        f"resolved={summary['cash_project_resolved_count']} "
        f"unresolved={summary['cash_project_unresolved_count']} "
        f"materialized={summary['materialized_business_value_target_slot_count']} "
        f"decision={summary['decision']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
