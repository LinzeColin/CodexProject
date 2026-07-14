#!/usr/bin/env python3
"""Validate private real-project rebinding and proven S09 value materialization."""

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
    v014_real_project_identity_private_rebinding_and_processed_value_materialization as phase,
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


def _snapshot_core(snapshot: dict[str, Any]) -> dict[str, Any]:
    return {
        "file_count": snapshot.get("file_count"),
        "total_bytes": snapshot.get("total_bytes"),
        "extension_counts": snapshot.get("extension_counts"),
        "records_sha256": snapshot.get("records_sha256"),
        "records": snapshot.get("records"),
    }


def _contains_float(value: Any) -> bool:
    if isinstance(value, float):
        return True
    if isinstance(value, dict):
        return any(_contains_float(child) for child in value.values())
    if isinstance(value, list):
        return any(_contains_float(child) for child in value)
    return False


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
        phase.PRIVATE_RAW_BEFORE_PATH,
        phase.PRIVATE_RAW_AFTER_PATH,
        phase.PRIVATE_PRECHECK_PATH,
        phase.PRIVATE_IDENTITY_BINDINGS_PATH,
        phase.PRIVATE_PROCESSED_METRICS_PATH,
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
    public_paths = _public_paths()
    for path in public_paths:
        _require(path.exists(), f"missing public artifact: {path}", errors)
    if errors:
        raise ValidationError("\n".join(f"- {error}" for error in errors))

    summary = _read_json(phase.SUMMARY_PATH)
    manifest = _read_json(phase.MANIFEST_PATH)
    go_no_go = _read_json(phase.GO_NO_GO_PATH)
    matrix = _read_json(phase.MATRIX_PATH)
    _require(summary == _read_json(phase.METADATA_SUMMARY_PATH), "summary metadata mirror mismatch", errors)
    _require(manifest == _read_json(phase.METADATA_MANIFEST_PATH), "manifest metadata mirror mismatch", errors)
    _require(go_no_go == _read_json(phase.METADATA_GO_NO_GO_PATH), "go/no-go metadata mirror mismatch", errors)
    _require(matrix == _read_json(phase.METADATA_MATRIX_PATH), "matrix metadata mirror mismatch", errors)

    expected_summary = {
        "phase_id": phase.PHASE_ID,
        "task_id": phase.TASK_ID,
        "status": phase.STATUS,
        "decision": "NO_GO",
        "source_private_inputs_unchanged": True,
        "authority_candidate_group_count": 4,
        "unique_authority_pdf_source_count": 4,
        "real_project_identity_binding_count": 4,
        "synthetic_project_identity_replaced_private_overlay_count": 4,
        "authority_margin_formula_exact_count": 4,
        "authority_gross_profit_system_formula_exact_count": 1,
        "workbook_identity_match_group_count": 3,
        "workbook_unique_sheet_binding_count": 0,
        "private_processed_metric_record_count": 32,
        "materialized_business_value_target_slot_count": 28,
        "unresolved_cash_value_target_slot_count": 12,
        "reconciliation_record_count": 12,
        "completed_reconciliation_comparison_count": 8,
        "zero_delta_reconciliation_count": 2,
        "nonzero_delta_reconciliation_count": 6,
        "incomplete_cash_reconciliation_count": 4,
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

    _require(matrix.get("check_count") == 16, "matrix check count must be 16", errors)
    _require(matrix.get("check_pass_count") == 16, "matrix pass count must be 16", errors)
    _require(matrix.get("check_fail_count") == 0, "matrix must have zero failures", errors)
    _require(go_no_go.get("decision") == "NO_GO", "go/no-go decision must be NO_GO", errors)
    _require(go_no_go.get("unresolved_cash_value_target_slot_count") == 12, "go/no-go cash target count must be 12", errors)
    _require(go_no_go.get("nonzero_delta_reconciliation_count") == 6, "go/no-go nonzero count must be 6", errors)
    _require(go_no_go.get("incomplete_cash_reconciliation_count") == 4, "go/no-go incomplete count must be 4", errors)

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

    public_text = "\n".join(path.read_text(encoding="utf-8") for path in public_paths)
    forbidden_public_fragments = (
        "project_name_private_value",
        "amount_signature_private_hash",
        "source_ref_hash",
        "private_source\"",
        "raw_value",
        "normalized_value_hash",
        "raw_value_hash",
        "private_processed_ref\"",
        "archive_member_name",
        "sheet_name",
        "cell_address",
        "context_text",
        "numeric_value_fingerprint",
    )
    for fragment in forbidden_public_fragments:
        _require(fragment not in public_text, f"private fragment leaked to public artifacts: {fragment}", errors)
    return summary, manifest


def _validate_private_materialization(summary: dict[str, Any], errors: list[str]) -> None:
    for path in _private_paths():
        _require(path.exists(), f"missing private artifact: {path}", errors)
        _require(_git_ignored(path), f"private artifact is not gitignored: {path}", errors)
    for path in phase.source_private_paths():
        _require(path.exists(), f"missing source private input: {path}", errors)
    if errors:
        return

    before = _read_json(phase.PRIVATE_RAW_BEFORE_PATH)
    after = _read_json(phase.PRIVATE_RAW_AFTER_PATH)
    precheck = _read_json(phase.PRIVATE_PRECHECK_PATH)
    diagnostic = _read_json(phase.PRIVATE_DIAGNOSTIC_PATH)
    bindings = _read_jsonl(phase.PRIVATE_IDENTITY_BINDINGS_PATH)
    metrics = _read_jsonl(phase.PRIVATE_PROCESSED_METRICS_PATH)
    materialized = _read_jsonl(phase.PRIVATE_TARGET_MATERIALIZATIONS_PATH)
    unresolved = _read_jsonl(phase.PRIVATE_UNRESOLVED_TARGETS_PATH)
    comparisons = _read_jsonl(phase.PRIVATE_RECONCILIATION_COMPARISONS_PATH)

    _require(_snapshot_core(before) == _snapshot_core(after), "private raw snapshots differ", errors)
    _require(diagnostic.get("raw_snapshot_exact_match") is True, "diagnostic raw match must be true", errors)
    _require(diagnostic.get("source_private_inputs_unchanged") is True, "source private inputs changed", errors)
    _require(summary.get("raw_source_file_count") == before.get("file_count"), "raw file count mismatch", errors)

    current_source_hashes = {
        path.as_posix(): _sha256_bytes(path.read_bytes()) for path in phase.source_private_paths()
    }
    _require(diagnostic.get("source_hashes_before") == current_source_hashes, "source hashes before mismatch", errors)
    _require(diagnostic.get("source_hashes_after") == current_source_hashes, "source hashes after mismatch", errors)

    precheck_records = precheck.get("records", [])
    _require(isinstance(precheck_records, list) and len(precheck_records) == 4, "precheck must contain four records", errors)
    if isinstance(precheck_records, list):
        _require(all(row.get("shared_pdf_source_count") == 1 for row in precheck_records), "each precheck record must have one PDF authority source", errors)
        _require(all(row.get("authority_margin_formula_exact") is True for row in precheck_records), "authority margin formula must replay exactly", errors)
        _require(sum(row.get("gross_profit_formula_exact") is True for row in precheck_records) == 1, "exact authority/system gross-profit count must be one", errors)

    _require(len(bindings) == 4, "private binding count must be 4", errors)
    _require(len(metrics) == 32, "private processed metric count must be 32", errors)
    _require(len(materialized) == 28, "private target materialization count must be 28", errors)
    _require(len(unresolved) == 12, "private unresolved cash target count must be 12", errors)
    _require(len(comparisons) == 12, "private comparison count must be 12", errors)
    _require(not _contains_float([bindings, metrics, materialized, unresolved, comparisons]), "private outputs must not contain floats", errors)

    _require(len({row.get("binding_id") for row in bindings}) == 4, "binding ids must be unique", errors)
    _require(all(row.get("synthetic_identity_replaced_in_private_overlay") is True for row in bindings), "all bindings must replace synthetic identities privately", errors)
    _require(all(row.get("public_commit_allowed") is False for row in bindings), "bindings must prohibit public commit", errors)
    _require(all(row.get("raw_layer_write_allowed") is False for row in bindings), "bindings must prohibit raw writes", errors)

    expected_metric_keys = {
        "contract_amount_cents",
        "cost_total_cents",
        "authority_gross_profit_cents",
        "authority_gross_margin_basis_points",
        "system_revenue_cents",
        "system_cost_total_cents",
        "system_recomputed_gross_profit_cents",
        "system_recomputed_gross_margin_basis_points",
    }
    for binding_id in {row.get("binding_id") for row in bindings}:
        binding_metrics = [row for row in metrics if row.get("binding_id") == binding_id]
        _require(len(binding_metrics) == 8, f"binding {binding_id} must have eight metrics", errors)
        _require({row.get("metric_key") for row in binding_metrics} == expected_metric_keys, f"binding {binding_id} metric keys mismatch", errors)
    _require(all(isinstance(row.get("value"), int) and not isinstance(row.get("value"), bool) for row in metrics), "metric values must be integer-only", errors)
    _require(all(row.get("integer_only") is True for row in metrics), "metrics must declare integer-only", errors)
    _require(all(row.get("public_commit_allowed") is False for row in metrics), "metrics must prohibit public commit", errors)
    _require(all(row.get("raw_layer_write_allowed") is False for row in metrics), "metrics must prohibit raw writes", errors)

    completed = [row for row in comparisons if str(row.get("comparison_status", "")).startswith("comparison_complete_")]
    zero = [row for row in completed if row.get("delta") == 0]
    nonzero = [row for row in completed if row.get("delta") != 0]
    incomplete = [row for row in comparisons if row not in completed]
    _require((len(completed), len(zero), len(nonzero), len(incomplete)) == (8, 2, 6, 4), "comparison status counts must be 8/2/6/4", errors)
    _require(all(row.get("delta") == row.get("amount_a") - row.get("amount_b") for row in completed), "completed comparison deltas must replay", errors)
    _require(all(row.get("difference_type") == "cash_vs_accrual_gross_profit" for row in incomplete), "incomplete comparisons must be cash-vs-accrual", errors)
    _require(all(row.get("amount_a") is None and row.get("delta") is None and isinstance(row.get("amount_b"), int) for row in incomplete), "incomplete cash comparison shape mismatch", errors)
    _require(all(row.get("public_commit_allowed") is False for row in comparisons), "comparisons must prohibit public commit", errors)

    materialized_ids = {row.get("target_slot_id") for row in materialized}
    unresolved_ids = {row.get("target_slot_id") for row in unresolved}
    _require(len(materialized_ids) == 28, "materialized target slot ids must be unique", errors)
    _require(len(unresolved_ids) == 12, "unresolved target slot ids must be unique", errors)
    _require(not materialized_ids.intersection(unresolved_ids), "materialized and unresolved target slots overlap", errors)
    _require(all(row.get("materialization_status") == "materialized_private_only" for row in materialized), "materialized slots must remain private-only", errors)
    _require(all(isinstance(row.get("value"), int) and not isinstance(row.get("value"), bool) for row in materialized), "materialized values must be integer-only", errors)
    _require(all(row.get("public_commit_allowed") is False for row in materialized), "materializations must prohibit public commit", errors)
    _require(all(row.get("resolution_status") == "cash_source_disambiguation_required" for row in unresolved), "unresolved targets must require cash-source disambiguation", errors)
    _require(all(row.get("public_commit_allowed") is False for row in unresolved), "unresolved targets must prohibit public commit", errors)

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
        "real project identity materialization validation: PASS "
        f"bindings={summary['real_project_identity_binding_count']} "
        f"materialized={summary['materialized_business_value_target_slot_count']} "
        f"unresolved_cash={summary['unresolved_cash_value_target_slot_count']} "
        f"decision={summary['decision']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
