#!/usr/bin/env python3
"""Validate the remaining private cash trace or difference acceptance phase."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from KMFA.tools import (  # noqa: E402
    v014_remaining_cash_source_private_trace_or_difference_acceptance as phase,
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
        phase.PRIVATE_TRACE_SPEC_PATH,
        phase.PRIVATE_RAW_BEFORE_PATH,
        phase.PRIVATE_RAW_AFTER_PATH,
        phase.PRIVATE_PAYABLE_TRACES_PATH,
        phase.PRIVATE_WPS_RECOVERY_DIAGNOSTIC_PATH,
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
            if not isinstance(value, str):
                continue
            if any(token in str(key).lower() for token in ("path", "name", "member", "sheet")):
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
    _require(summary == _read_json(phase.METADATA_SUMMARY_PATH), "summary mirror mismatch", errors)
    _require(manifest == _read_json(phase.METADATA_MANIFEST_PATH), "manifest mirror mismatch", errors)
    _require(go_no_go == _read_json(phase.METADATA_GO_NO_GO_PATH), "go/no-go mirror mismatch", errors)
    _require(matrix == _read_json(phase.METADATA_MATRIX_PATH), "matrix mirror mismatch", errors)

    expected = {
        "phase_id": phase.PHASE_ID,
        "task_id": phase.TASK_ID,
        "status": phase.STATUS,
        "decision": "NO_GO",
        "source_private_inputs_unchanged": True,
        "payable_trace_record_count": 3,
        "cash_paid_later_trace_count": 1,
        "noncash_note_settlement_trace_count": 1,
        "unpaid_at_cutoff_trace_count": 1,
        "cash_project_candidate_count": 4,
        "cash_project_resolved_count": 2,
        "cash_project_unresolved_count": 2,
        "private_cash_metric_record_count": 6,
        "materialized_business_value_target_slot_count": 34,
        "newly_materialized_cash_target_slot_count": 3,
        "unresolved_cash_value_target_slot_count": 6,
        "reconciliation_record_count": 12,
        "completed_reconciliation_comparison_count": 10,
        "zero_delta_reconciliation_count": 2,
        "nonzero_delta_reconciliation_count": 8,
        "incomplete_cash_reconciliation_count": 2,
        "wps_source_count": 2,
        "standard_office_encrypted_count": 2,
        "office_compatibility_unlock_count": 2,
        "empty_compatibility_workbook_count": 2,
        "wps_security_document_layer_count": 2,
        "secure_wps_content_readable_count": 0,
        "external_crosscheck_completed": False,
        "forced_zero_materialization_count": 0,
        "global_unresolved_difference_count": 72,
        "global_residual_difference_queue_replayed": False,
        "partial_processed_value_materialization_complete": True,
        "full_processed_value_materialization_complete": False,
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
    for key, value in expected.items():
        _require(summary.get(key) == value, f"summary {key} must equal {value!r}", errors)
    _require(matrix.get("check_count") == 18, "matrix check count must be 18", errors)
    _require(matrix.get("check_pass_count") == 18, "matrix pass count must be 18", errors)
    _require(matrix.get("check_fail_count") == 0, "matrix fail count must be 0", errors)
    _require(go_no_go.get("cash_project_unresolved_count") == 2, "go/no-go unresolved project count must be 2", errors)
    _require(go_no_go.get("unresolved_cash_value_target_slot_count") == 6, "go/no-go unresolved target count must be 6", errors)
    _require(go_no_go.get("nonzero_delta_reconciliation_count") == 8, "go/no-go nonzero count must be 8", errors)
    _require(go_no_go.get("secure_wps_content_readable_count") == 0, "go/no-go secure WPS readable count must be 0", errors)

    safety = manifest.get("public_repo_safety", {})
    _require(safety.get("aggregate_only") is True, "public manifest must be aggregate-only", errors)
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
    _require(boundaries.get("single_phase_only") is True, "single phase boundary missing", errors)
    _require(boundaries.get("secure_wps_content_read_claimed") is False, "secure WPS content must not be claimed", errors)
    _require(boundaries.get("forced_zero_materialization_allowed") is False, "forced zero must be prohibited", errors)
    for key in (
        "global_residual_queue_replayed",
        "stage_review_performed",
        "github_upload_performed",
        "app_reinstall_performed",
        "business_execution_performed",
    ):
        _require(boundaries.get(key) is False, f"boundary {key} must be false", errors)

    public_text = "\n".join(path.read_text(encoding="utf-8") for path in _public_paths())
    trace_spec = _read_json(phase.PRIVATE_TRACE_SPEC_PATH)
    forbidden = (
        str(trace_spec.get("office_compatibility_password", "")),
        "origin_cost_row",
        "origin_payable_rows",
        "bank_settlement_rows",
        "wps_ext_data",
        "wps_content_declared_length",
        "project_code",
        "alias_tokens",
        "supplier",
        "collection_amount_cents\"",
        "cash_paid_cost_cents\"",
        "cash_gross_profit_cents\"",
        "source_hashes_before",
        "records_sha256",
    )
    for fragment in forbidden:
        if fragment:
            _require(fragment not in public_text, f"private fragment leaked publicly: {fragment}", errors)
    return summary, manifest


def _validate_private_trace(summary: dict[str, Any], errors: list[str]) -> None:
    for path in _private_paths():
        _require(path.exists(), f"missing private artifact: {path}", errors)
        _require(_git_ignored(path), f"private artifact is not gitignored: {path}", errors)
    for path in phase.source_private_paths():
        _require(path.exists(), f"missing source private input: {path}", errors)
        _require(_git_ignored(path), f"source private input is not gitignored: {path}", errors)
    if errors:
        return

    before = _read_json(phase.PRIVATE_RAW_BEFORE_PATH)
    after = _read_json(phase.PRIVATE_RAW_AFTER_PATH)
    current = phase._raw_snapshot("validator")
    traces = _read_jsonl(phase.PRIVATE_PAYABLE_TRACES_PATH)
    wps = _read_json(phase.PRIVATE_WPS_RECOVERY_DIAGNOSTIC_PATH)
    decisions = _read_jsonl(phase.PRIVATE_CASH_DECISIONS_PATH)
    metrics = _read_jsonl(phase.PRIVATE_CASH_METRICS_PATH)
    materialized = _read_jsonl(phase.PRIVATE_TARGET_MATERIALIZATIONS_PATH)
    unresolved = _read_jsonl(phase.PRIVATE_UNRESOLVED_TARGETS_PATH)
    comparisons = _read_jsonl(phase.PRIVATE_RECONCILIATION_COMPARISONS_PATH)
    diagnostic = _read_json(phase.PRIVATE_DIAGNOSTIC_PATH)

    _require(_snapshot_core(before) == _snapshot_core(after), "private raw snapshots differ", errors)
    _require(_snapshot_core(after) == _snapshot_core(current), "current raw snapshot differs", errors)
    _require(diagnostic.get("raw_snapshot_exact_match") is True, "diagnostic raw match must be true", errors)
    _require(diagnostic.get("source_private_inputs_unchanged") is True, "source private inputs changed", errors)
    _require(summary.get("raw_source_file_count") == before.get("file_count"), "raw source count mismatch", errors)
    current_hashes = {
        path.as_posix(): _sha256_bytes(path.read_bytes()) for path in phase.source_private_paths()
    }
    _require(diagnostic.get("source_hashes_before") == current_hashes, "source hashes before mismatch", errors)
    _require(diagnostic.get("source_hashes_after") == current_hashes, "source hashes after mismatch", errors)

    _require(len(traces) == 3, "payable trace count must be 3", errors)
    trace_counts = Counter(row.get("trace_classification") for row in traces)
    _require(
        trace_counts
        == Counter(
            {"cash_paid_later": 1, "noncash_note_settlement": 1, "unpaid_at_cutoff": 1}
        ),
        "payable trace classification counts mismatch",
        errors,
    )
    for row in traces:
        _require(row.get("integer_only") is True, "payable trace must be integer-only", errors)
        _require(row.get("public_commit_allowed") is False, "payable trace must prohibit public commit", errors)
        classification = row.get("trace_classification")
        if classification == "cash_paid_later":
            _require(row.get("settlement_status") == "fully_settled_by_bank", "later cash trace status mismatch", errors)
            _require(row.get("cash_paid_project_cost_cents") == row.get("cost_amount_cents"), "later cash trace amount mismatch", errors)
            _require(bool(row.get("bank_settlement_rows")), "later cash trace needs bank evidence", errors)
        elif classification == "noncash_note_settlement":
            _require(row.get("cash_paid_project_cost_cents") == 0, "note settlement cash amount must be zero", errors)
            _require(bool(row.get("note_rows")), "note settlement needs note evidence", errors)
        elif classification == "unpaid_at_cutoff":
            _require(row.get("cash_paid_project_cost_cents") == 0, "unpaid trace cash amount must be zero", errors)
            _require(not row.get("settlement_rows"), "unpaid trace cannot contain settlement rows", errors)

    _require(wps.get("source_count") == 2, "WPS source count must be 2", errors)
    _require(wps.get("standard_office_encrypted_count") == 2, "standard Office encrypted count must be 2", errors)
    _require(wps.get("office_compatibility_unlock_count") == 2, "compatibility unlock count must be 2", errors)
    _require(wps.get("empty_compatibility_workbook_count") == 2, "empty compatibility count must be 2", errors)
    _require(wps.get("wps_security_document_layer_count") == 2, "WPS security layer count must be 2", errors)
    _require(wps.get("secure_wps_content_readable_count") == 0, "secure WPS content readable count must be 0", errors)
    for row in wps.get("records", []):
        _require(row.get("office_compatibility_unlock_succeeded") is True, "compatibility unlock must succeed", errors)
        _require(row.get("compatibility_workbook_empty") is True, "compatibility workbook must be empty", errors)
        _require(row.get("wps_security_document_layer_present") is True, "WPS security layer missing", errors)
        _require(row.get("secure_wps_content_readable") is False, "secure WPS content must remain unreadable", errors)

    _require(len(decisions) == 4, "cash decision count must be 4", errors)
    resolved = [row for row in decisions if str(row.get("resolution_status", "")).startswith("resolved_")]
    pending = [row for row in decisions if row.get("resolution_status") == "unresolved"]
    _require((len(resolved), len(pending)) == (2, 2), "cash project status counts must be 2/2", errors)
    for row in resolved:
        values = (
            row.get("collection_amount_cents"),
            row.get("cash_paid_cost_cents"),
            row.get("cash_gross_profit_cents"),
        )
        _require(all(isinstance(value, int) and not isinstance(value, bool) for value in values), "resolved cash values must be integers", errors)
        _require(values[2] == values[0] - values[1], "resolved cash formula mismatch", errors)
    for row in pending:
        _require(row.get("collection_amount_cents") is None, "pending collection must not be filled", errors)
        _require(row.get("cash_paid_cost_cents") is None, "pending paid cost must not be filled", errors)
        _require(row.get("cash_gross_profit_cents") is None, "pending cash gross profit must not be filled", errors)
        _require(row.get("zero_inferred_from_absence") is False, "pending absence cannot infer zero", errors)

    _require(len(metrics) == 6, "cash metric count must be 6", errors)
    metric_groups = Counter(row.get("legacy_margin_record_id") for row in metrics)
    _require(sorted(metric_groups.values()) == [3, 3], "cash metrics must cover two projects with three metrics each", errors)
    _require(all(isinstance(row.get("value"), int) and not isinstance(row.get("value"), bool) for row in metrics), "cash metric values must be integer-only", errors)

    _require(len(materialized) == 34, "materialized target count must be 34", errors)
    _require(len(unresolved) == 6, "unresolved target count must be 6", errors)
    _require(len(comparisons) == 12, "comparison count must be 12", errors)
    materialized_ids = {row.get("target_slot_id") for row in materialized}
    unresolved_ids = {row.get("target_slot_id") for row in unresolved}
    _require(len(materialized_ids) == 34, "materialized target ids must be unique", errors)
    _require(len(unresolved_ids) == 6, "unresolved target ids must be unique", errors)
    _require(not materialized_ids.intersection(unresolved_ids), "target sets overlap", errors)
    _require(all(row.get("materialization_status") == "materialized_private_only" for row in materialized), "materialized status mismatch", errors)
    _require(all(row.get("resolution_status") == "cash_source_disambiguation_required" for row in unresolved), "unresolved target status mismatch", errors)

    completed = [row for row in comparisons if str(row.get("comparison_status", "")).startswith("comparison_complete_")]
    zero = [row for row in completed if row.get("delta") == 0]
    nonzero = [row for row in completed if row.get("delta") != 0]
    incomplete = [row for row in comparisons if row not in completed]
    _require((len(completed), len(zero), len(nonzero), len(incomplete)) == (10, 2, 8, 2), "comparison counts must be 10/2/8/2", errors)
    _require(all(row.get("delta") == row.get("amount_a") - row.get("amount_b") for row in completed), "comparison deltas must replay", errors)
    _require(all(row.get("amount_a") is None and row.get("delta") is None for row in incomplete), "incomplete comparisons must remain empty", errors)

    _require(not _contains_float([traces, wps, decisions, metrics, materialized, unresolved, comparisons]), "private outputs cannot contain floats", errors)
    report = phase.PRIVATE_DIFFERENCE_REPORT_PATH.read_text(encoding="utf-8")
    for required in ("本轮结论", "应付与结算追踪", "WPS/OLE 恢复诊断", "剩余差异接受", "缺失收款证据仍未写成零"):
        _require(required in report, f"private Chinese report missing: {required}", errors)

    public_text = "\n".join(path.read_text(encoding="utf-8") for path in _public_paths())
    for fragment in _raw_name_fragments(before):
        _require(fragment not in public_text, "raw filename leaked publicly", errors)
    for row in traces:
        for source_row in (
            row.get("origin_cost_row", {}),
            *row.get("origin_payable_rows", []),
            *row.get("settlement_rows", []),
        ):
            for key in ("supplier", "summary", "sheet_name"):
                value = str(source_row.get(key, ""))
                if len(value) >= 4:
                    _require(value not in public_text, "payable trace plaintext leaked publicly", errors)


def validate(*, require_private_trace: bool = False) -> dict[str, Any]:
    errors: list[str] = []
    summary, manifest = _validate_public_artifacts(errors)
    if require_private_trace:
        _validate_private_trace(summary, errors)
    if errors:
        raise ValidationError("\n".join(f"- {error}" for error in errors))
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-private-trace", action="store_true")
    args = parser.parse_args()
    manifest = validate(require_private_trace=args.require_private_trace)
    summary = manifest["summary"]
    print(
        "remaining cash trace validation: PASS "
        f"resolved={summary['cash_project_resolved_count']} "
        f"unresolved={summary['cash_project_unresolved_count']} "
        f"materialized={summary['materialized_business_value_target_slot_count']} "
        f"decision={summary['decision']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
