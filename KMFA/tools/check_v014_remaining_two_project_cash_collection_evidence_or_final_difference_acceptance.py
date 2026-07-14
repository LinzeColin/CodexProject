#!/usr/bin/env python3
"""Validate final remaining-project cash evidence and difference acceptance."""

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
    v014_remaining_two_project_cash_collection_evidence_or_final_difference_acceptance as phase,
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
        phase.PRIVATE_RAW_BEFORE_PATH,
        phase.PRIVATE_RAW_AFTER_PATH,
        phase.PRIVATE_COLLECTION_CANDIDATES_PATH,
        phase.PRIVATE_COLLECTION_LINKS_PATH,
        phase.PRIVATE_REJECTED_LINKS_PATH,
        phase.PRIVATE_CASH_DECISIONS_PATH,
        phase.PRIVATE_CASH_METRICS_PATH,
        phase.PRIVATE_TARGET_MATERIALIZATIONS_PATH,
        phase.PRIVATE_UNRESOLVED_TARGETS_PATH,
        phase.PRIVATE_RECONCILIATION_COMPARISONS_PATH,
        phase.PRIVATE_DIAGNOSTIC_PATH,
        phase.PRIVATE_FINAL_DIFFERENCE_REPORT_PATH,
    ]


def _raw_name_fragments(snapshot: dict[str, Any]) -> set[str]:
    fragments: set[str] = set()
    for record in snapshot.get("records", []):
        if not isinstance(record, dict):
            continue
        relative_path = str(record.get("relative_path", ""))
        digest = str(record.get("sha256", ""))
        if len(relative_path) >= 4:
            fragments.add(relative_path)
            fragments.add(Path(relative_path).name)
        if digest:
            fragments.add(digest)
    return {fragment for fragment in fragments if len(fragment) >= 4}


def _validate_public_artifacts(
    errors: list[str],
) -> tuple[dict[str, Any], dict[str, Any]]:
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
        "summary mirror mismatch",
        errors,
    )
    _require(
        manifest == _read_json(phase.METADATA_MANIFEST_PATH),
        "manifest mirror mismatch",
        errors,
    )
    _require(
        go_no_go == _read_json(phase.METADATA_GO_NO_GO_PATH),
        "go/no-go mirror mismatch",
        errors,
    )
    _require(
        matrix == _read_json(phase.METADATA_MATRIX_PATH),
        "matrix mirror mismatch",
        errors,
    )
    expected = {
        "phase_id": phase.PHASE_ID,
        "task_id": phase.TASK_ID,
        "status": phase.STATUS,
        "decision": "NO_GO",
        "source_private_inputs_unchanged": True,
        "raw_archive_count": 3,
        "raw_ole_xlsx_count": 2,
        "raw_ooxml_xlsx_count": 0,
        "accessible_nonledger_ooxml_workbook_count": 19,
        "bank_inflow_record_count": 993,
        "raw_collection_candidate_record_count": 48,
        "unique_balanced_collection_link_count": 2,
        "balanced_receivable_voucher_count": 2,
        "cash_project_candidate_count": 4,
        "cash_project_resolved_count": 3,
        "cash_project_unresolved_count": 1,
        "collection_evidence_project_resolved_count": 1,
        "final_difference_accepted_project_count": 1,
        "private_cash_metric_record_count": 9,
        "newly_materialized_cash_target_slot_count": 3,
        "materialized_business_value_target_slot_count": 37,
        "unresolved_cash_value_target_slot_count": 3,
        "reconciliation_record_count": 12,
        "completed_reconciliation_comparison_count": 11,
        "zero_delta_reconciliation_count": 2,
        "nonzero_delta_reconciliation_count": 9,
        "incomplete_cash_reconciliation_count": 1,
        "wps_source_count": 2,
        "office_compatibility_unlock_count": 2,
        "empty_compatibility_workbook_count": 2,
        "secure_wps_content_readable_count": 0,
        "partial_external_crosscheck_completed": True,
        "external_crosscheck_completed": False,
        "final_cash_difference_acceptance_completed": True,
        "forced_zero_materialization_count": 0,
        "global_unresolved_difference_count": 72,
        "global_residual_difference_queue_replayed": False,
        "full_processed_value_materialization_complete": False,
        "full_raw_to_processed_value_comparison_complete": False,
        "processed_consistency_verified": False,
        "business_value_consistency_verified": False,
        "raw_source_file_count": 5,
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
    _require(
        summary.get("zero_delta_reconciliation_count", 0)
        + summary.get("nonzero_delta_reconciliation_count", 0)
        == 11,
        "zero and nonzero comparison counts must total 11",
        errors,
    )
    _require(
        summary.get("nonzero_delta_reconciliation_count") == 9,
        "nonzero comparison count must be 9",
        errors,
    )
    _require(matrix.get("check_count") == 20, "matrix check count must be 20", errors)
    _require(
        matrix.get("check_pass_count") == 20,
        "matrix pass count must be 20",
        errors,
    )
    _require(matrix.get("check_fail_count") == 0, "matrix fail count must be 0", errors)
    _require(
        go_no_go.get("cash_project_unresolved_count") == 1,
        "go/no-go unresolved project count must be 1",
        errors,
    )
    _require(
        go_no_go.get("unresolved_cash_value_target_slot_count") == 3,
        "go/no-go unresolved target count must be 3",
        errors,
    )
    _require(
        go_no_go.get("final_difference_accepted_project_count") == 1,
        "go/no-go final accepted difference count must be 1",
        errors,
    )

    safety = manifest.get("public_repo_safety", {})
    _require(safety.get("aggregate_only") is True, "manifest must be aggregate-only", errors)
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
    for key in (
        "single_phase_only",
        "positive_collection_evidence_crosscheck_performed",
        "final_cash_difference_acceptance_performed",
    ):
        _require(boundaries.get(key) is True, f"boundary {key} must be true", errors)
    for key in (
        "forced_zero_materialization_allowed",
        "secure_wps_content_read_claimed",
        "global_residual_queue_replayed",
        "stage_review_performed",
        "github_upload_performed",
        "app_reinstall_performed",
        "business_execution_performed",
    ):
        _require(boundaries.get(key) is False, f"boundary {key} must be false", errors)

    public_text = "\n".join(path.read_text(encoding="utf-8") for path in _public_paths())
    forbidden_tokens = (
        "project_code",
        "alias_tokens",
        "archive_path",
        "archive_sha256",
        "member_name",
        "sheet_name",
        "customer_values",
        "project_values",
        "amount_cents\"",
        "bank_row",
        "voucher_rows",
        "source_hashes_before",
        "records_sha256",
    )
    for token in forbidden_tokens:
        _require(token not in public_text, f"private token leaked publicly: {token}", errors)
    return summary, manifest


def _validate_private_evidence(summary: dict[str, Any], errors: list[str]) -> None:
    for path in _private_paths():
        _require(path.exists(), f"missing private artifact: {path}", errors)
        _require(_git_ignored(path), f"private artifact not ignored: {path}", errors)
    if errors:
        return
    before = _read_json(phase.PRIVATE_RAW_BEFORE_PATH)
    after = _read_json(phase.PRIVATE_RAW_AFTER_PATH)
    current = phase._raw_snapshot("validator_read_only")
    _require(
        _snapshot_core(before) == _snapshot_core(after) == _snapshot_core(current),
        "raw snapshot changed",
        errors,
    )
    _require(before.get("file_count") == 5, "raw file count must be 5", errors)
    diagnostic = _read_json(phase.PRIVATE_DIAGNOSTIC_PATH)
    _require(
        diagnostic.get("source_hashes_before") == diagnostic.get("source_hashes_after"),
        "source private hashes changed",
        errors,
    )
    current_hashes = {
        path.as_posix(): _sha256_bytes(path.read_bytes()) for path in phase.source_private_paths()
    }
    _require(
        diagnostic.get("source_hashes_after") == current_hashes,
        "source private hashes do not match current files",
        errors,
    )

    candidates = _read_jsonl(phase.PRIVATE_COLLECTION_CANDIDATES_PATH)
    links = _read_jsonl(phase.PRIVATE_COLLECTION_LINKS_PATH)
    rejected = _read_jsonl(phase.PRIVATE_REJECTED_LINKS_PATH)
    decisions = _read_jsonl(phase.PRIVATE_CASH_DECISIONS_PATH)
    metrics = _read_jsonl(phase.PRIVATE_CASH_METRICS_PATH)
    materialized = _read_jsonl(phase.PRIVATE_TARGET_MATERIALIZATIONS_PATH)
    unresolved = _read_jsonl(phase.PRIVATE_UNRESOLVED_TARGETS_PATH)
    comparisons = _read_jsonl(phase.PRIVATE_RECONCILIATION_COMPARISONS_PATH)

    _require(len(candidates) == 48, "private candidate count must be 48", errors)
    _require(len(links) == 2, "accepted link count must be 2", errors)
    _require(not rejected, "strict collection groups must not be rejected", errors)
    _require(
        len({row.get("project_code") for row in links}) == 1,
        "accepted links must belong to one project",
        errors,
    )
    for link in links:
        _require(link.get("accepted") is True, "collection link must be accepted", errors)
        _require(
            link.get("classification")
            == "unique_project_customer_bank_receivable_collection",
            "collection link classification mismatch",
            errors,
        )
        _require(link.get("voucher_balanced") is True, "voucher must balance", errors)
        _require(
            link.get("bank_equals_receivable_credit") is True,
            "bank inflow must equal receivable credit",
            errors,
        )
        _require(
            link.get("noncumulative_source_record_count", 0) >= 1,
            "link needs a noncumulative source",
            errors,
        )
        _require(
            all(row.get("project_dimension_present") is True for row in link["source_records"]),
            "link source project dimension missing",
            errors,
        )
        _require(
            all(row.get("customer_dimension_present") is True for row in link["source_records"]),
            "link source customer dimension missing",
            errors,
        )
        _require(
            all(row.get("customer_bank_match") is True for row in link["source_records"]),
            "link source customer-bank match missing",
            errors,
        )

    _require(len(decisions) == 4, "cash decision count must be 4", errors)
    resolved = [
        row
        for row in decisions
        if str(row.get("resolution_status", "")).startswith("resolved_")
    ]
    final_pending = [
        row for row in decisions if row.get("resolution_status") == "difference_accepted_unresolved"
    ]
    _require(
        (len(resolved), len(final_pending)) == (3, 1),
        "cash project status counts must be 3/1",
        errors,
    )
    for row in resolved:
        values = (
            row.get("collection_amount_cents"),
            row.get("cash_paid_cost_cents"),
            row.get("cash_gross_profit_cents"),
        )
        _require(
            all(isinstance(value, int) and not isinstance(value, bool) for value in values),
            "resolved cash values must be integer cents",
            errors,
        )
        _require(values[2] == values[0] - values[1], "resolved cash formula mismatch", errors)
    for row in final_pending:
        _require(row.get("collection_amount_cents") is None, "final pending collection must be empty", errors)
        _require(row.get("cash_paid_cost_cents") is None, "final pending paid cost must be empty", errors)
        _require(row.get("cash_gross_profit_cents") is None, "final pending cash gross must be empty", errors)
        _require(row.get("zero_inferred_from_absence") is False, "absence cannot infer zero", errors)
        _require(row.get("final_difference_acceptance") is True, "final difference acceptance missing", errors)

    _require(len(metrics) == 9, "cash metric count must be 9", errors)
    metric_groups = Counter(row.get("legacy_margin_record_id") for row in metrics)
    _require(
        sorted(metric_groups.values()) == [3, 3, 3],
        "cash metrics must cover three projects",
        errors,
    )
    _require(len(materialized) == 37, "materialized target count must be 37", errors)
    _require(len(unresolved) == 3, "unresolved target count must be 3", errors)
    _require(len(comparisons) == 12, "comparison count must be 12", errors)
    materialized_ids = {row.get("target_slot_id") for row in materialized}
    unresolved_ids = {row.get("target_slot_id") for row in unresolved}
    _require(len(materialized_ids) == 37, "materialized target ids must be unique", errors)
    _require(len(unresolved_ids) == 3, "unresolved target ids must be unique", errors)
    _require(not materialized_ids.intersection(unresolved_ids), "target sets overlap", errors)

    completed = [
        row
        for row in comparisons
        if str(row.get("comparison_status", "")).startswith("comparison_complete_")
    ]
    zero = [row for row in completed if row.get("delta") == 0]
    nonzero = [row for row in completed if row.get("delta") != 0]
    incomplete = [row for row in comparisons if row not in completed]
    _require(len(completed) == 11, "completed comparison count must be 11", errors)
    _require(len(zero) + len(nonzero) == 11, "comparison split must total 11", errors)
    _require((len(zero), len(nonzero)) == (2, 9), "comparison split must be 2/9", errors)
    _require(len(incomplete) == 1, "incomplete comparison count must be 1", errors)
    _require(
        all(row.get("delta") == row.get("amount_a") - row.get("amount_b") for row in completed),
        "comparison deltas must replay",
        errors,
    )
    _require(
        all(row.get("amount_a") is None and row.get("delta") is None for row in incomplete),
        "incomplete comparison values must remain empty",
        errors,
    )
    _require(
        not _contains_float(
            [candidates, links, decisions, metrics, materialized, unresolved, comparisons]
        ),
        "private outputs cannot contain floats",
        errors,
    )

    report = phase.PRIVATE_FINAL_DIFFERENCE_REPORT_PATH.read_text(encoding="utf-8")
    for required in (
        "最终差异接受",
        "正向收款证据",
        "唯一银行入账链",
        "未写成零",
        "原始数据保持不变",
    ):
        _require(required in report, f"private Chinese report missing: {required}", errors)

    public_text = "\n".join(path.read_text(encoding="utf-8") for path in _public_paths())
    for fragment in _raw_name_fragments(before):
        _require(fragment not in public_text, "raw filename or hash leaked publicly", errors)
    sensitive_values: set[str] = set()
    for candidate in candidates:
        for key in (
            "archive_path",
            "member_name",
            "sheet_name",
            "collection_header",
        ):
            value = str(candidate.get(key, ""))
            if len(value) >= 4:
                sensitive_values.add(value)
        for key in ("project_values", "customer_values", "alias_hits"):
            sensitive_values.update(
                str(value) for value in candidate.get(key, []) if len(str(value)) >= 4
            )
        amount = candidate.get("amount_cents")
        if isinstance(amount, int) and abs(amount) >= 10_000:
            sensitive_values.add(str(abs(amount)))
    for value in sensitive_values:
        _require(value not in public_text, "private source value leaked publicly", errors)


def validate(*, require_private_evidence: bool = False) -> dict[str, Any]:
    errors: list[str] = []
    summary, manifest = _validate_public_artifacts(errors)
    if require_private_evidence:
        _validate_private_evidence(summary, errors)
    if errors:
        raise ValidationError("\n".join(f"- {error}" for error in errors))
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-private-evidence", action="store_true")
    args = parser.parse_args()
    manifest = validate(require_private_evidence=args.require_private_evidence)
    summary = manifest["summary"]
    print(
        "final collection evidence validation: PASS "
        f"resolved={summary['cash_project_resolved_count']} "
        f"unresolved={summary['cash_project_unresolved_count']} "
        f"links={summary['unique_balanced_collection_link_count']} "
        f"materialized={summary['materialized_business_value_target_slot_count']} "
        f"decision={summary['decision']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
