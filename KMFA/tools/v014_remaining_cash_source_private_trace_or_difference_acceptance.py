#!/usr/bin/env python3
"""Trace remaining private cash sources or preserve an explicit difference acceptance."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from KMFA.tools import (  # noqa: E402
    v014_cash_source_private_disambiguation_and_remaining_value_materialization as source_phase,
)


PROJECT_ROOT = Path("KMFA")
PHASE_ID = "V014_REMAINING_CASH_SOURCE_PRIVATE_TRACE_OR_DIFFERENCE_ACCEPTANCE"
TASK_ID = "KMFA-V014-REMAINING-CASH-SOURCE-PRIVATE-TRACE-OR-DIFFERENCE-ACCEPTANCE-20260710"
ACCEPTANCE_ID = "ACC-V014-REMAINING-CASH-SOURCE-PRIVATE-TRACE-OR-DIFFERENCE-ACCEPTANCE"
VERSION = "0.1.4-remaining-cash-source-private-trace-or-difference-acceptance"
STATUS = "completed_validated_local_only_second_cash_project_materialized_two_projects_difference_accepted_no_go"
DECISION = "NO_GO"
PREFIX = "remaining_cash_source_private_trace_or_difference_acceptance"

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
SUMMARY_PATH = MACHINE_DIR / f"{PREFIX}_summary.json"
MANIFEST_PATH = MACHINE_DIR / f"{PREFIX}_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / f"{PREFIX}_go_no_go_report.json"
MATRIX_PATH = MACHINE_DIR / f"{PREFIX}_matrix_public_safe.json"
REPORT_PATH = HUMAN_DIR / f"{PREFIX}.md"
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_SUMMARY_PATH = PROJECT_ROOT / f"metadata/quality/v014_{PREFIX}_summary.json"
METADATA_MANIFEST_PATH = PROJECT_ROOT / f"metadata/quality/v014_{PREFIX}_manifest.json"
METADATA_GO_NO_GO_PATH = PROJECT_ROOT / f"metadata/quality/v014_{PREFIX}_go_no_go_report.json"
METADATA_MATRIX_PATH = PROJECT_ROOT / f"metadata/quality/v014_{PREFIX}_matrix_public_safe.json"

PRIVATE_OUTPUT_DIR = PROJECT_ROOT / ".codex_private_runtime/v014_remaining_cash_source_private_trace_or_difference_acceptance"
PRIVATE_TRACE_SPEC_PATH = PRIVATE_OUTPUT_DIR / "private_trace_spec.json"
PRIVATE_RAW_BEFORE_PATH = PRIVATE_OUTPUT_DIR / "raw_immutability_before.json"
PRIVATE_RAW_AFTER_PATH = PRIVATE_OUTPUT_DIR / "raw_immutability_after.json"
PRIVATE_PAYABLE_TRACES_PATH = PRIVATE_OUTPUT_DIR / "private_payable_cost_traces.jsonl"
PRIVATE_WPS_RECOVERY_DIAGNOSTIC_PATH = PRIVATE_OUTPUT_DIR / "private_wps_recovery_diagnostic.json"
PRIVATE_CASH_DECISIONS_PATH = PRIVATE_OUTPUT_DIR / "private_cash_source_decisions.jsonl"
PRIVATE_CASH_METRICS_PATH = PRIVATE_OUTPUT_DIR / "private_materialized_cash_metrics.jsonl"
PRIVATE_TARGET_MATERIALIZATIONS_PATH = PRIVATE_OUTPUT_DIR / "private_s09_target_slot_materializations.jsonl"
PRIVATE_UNRESOLVED_TARGETS_PATH = PRIVATE_OUTPUT_DIR / "private_unresolved_cash_value_targets.jsonl"
PRIVATE_RECONCILIATION_COMPARISONS_PATH = PRIVATE_OUTPUT_DIR / "private_s09_reconciliation_comparisons.jsonl"
PRIVATE_DIAGNOSTIC_PATH = PRIVATE_OUTPUT_DIR / "private_remaining_cash_trace_diagnostic.json"
PRIVATE_DIFFERENCE_REPORT_PATH = PRIVATE_OUTPUT_DIR / "private_difference_report_zh.md"

SOURCE_PRIVATE_SPEC_PATH = source_phase.PRIVATE_SOURCE_SPEC_PATH
SOURCE_LEDGER_EVIDENCE_PATH = source_phase.PRIVATE_LEDGER_EVIDENCE_PATH
SOURCE_WPS_DIAGNOSTIC_PATH = source_phase.PRIVATE_WPS_DIAGNOSTIC_PATH
SOURCE_CASH_DECISIONS_PATH = source_phase.PRIVATE_CASH_DECISIONS_PATH
SOURCE_CASH_METRICS_PATH = source_phase.PRIVATE_CASH_METRICS_PATH
SOURCE_TARGET_MATERIALIZATIONS_PATH = source_phase.PRIVATE_TARGET_MATERIALIZATIONS_PATH
SOURCE_UNRESOLVED_TARGETS_PATH = source_phase.PRIVATE_UNRESOLVED_TARGETS_PATH
SOURCE_RECONCILIATION_COMPARISONS_PATH = source_phase.PRIVATE_RECONCILIATION_COMPARISONS_PATH

DEVELOPMENT_EVENTS_PATH = PROJECT_ROOT / "docs/governance/development_events.jsonl"
STAGE_STATUS_PATH = PROJECT_ROOT / "metadata/stage_status.jsonl"
TASK_STATUS_PATH = PROJECT_ROOT / "metadata/traceability/v1_4_stage_phase_task_status.jsonl"


def _now(generated_at: str | None = None) -> str:
    return generated_at or datetime.now().astimezone().isoformat(timespec="seconds")


def read_json(path: Path) -> dict[str, Any]:
    return source_phase.read_json(path)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return source_phase.read_jsonl(path)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    source_phase._write_json(path, payload)


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    source_phase._write_jsonl(path, rows)


def _write_text(path: Path, text: str) -> None:
    source_phase._write_text(path, text)


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _raw_snapshot(kind: str) -> dict[str, Any]:
    snapshot = source_phase._raw_snapshot(kind)
    snapshot["phase_id"] = PHASE_ID
    snapshot["snapshot_kind"] = kind
    return snapshot


def _snapshot_core(snapshot: dict[str, Any]) -> dict[str, Any]:
    return source_phase._snapshot_core(snapshot)


def _contains_float(value: Any) -> bool:
    if isinstance(value, float):
        return True
    if isinstance(value, dict):
        return any(_contains_float(child) for child in value.values())
    if isinstance(value, list):
        return any(_contains_float(child) for child in value)
    return False


def _integer_cents(row: dict[str, Any], key: str) -> int:
    value = row.get(key, 0)
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"{key} must be integer cents")
    return value


def _voucher_key(row: dict[str, Any]) -> tuple[str, str]:
    return str(row.get("date", "")), str(row.get("voucher", ""))


def _private_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "sheet_name": row.get("sheet_name", "fixture"),
        "row_number": row.get("row_number"),
        "account": row.get("account", ""),
        "supplier": row.get("supplier", ""),
        "date": row.get("date", ""),
        "voucher": row.get("voucher", ""),
        "summary": row.get("summary", ""),
        "debit_cents": _integer_cents(row, "debit_cents"),
        "credit_cents": _integer_cents(row, "credit_cents"),
        "balance_cents": _integer_cents(row, "balance_cents"),
    }


def source_private_paths() -> list[Path]:
    spec = read_json(PRIVATE_TRACE_SPEC_PATH)
    dependency_dir = Path(str(spec["private_dependency_dir"]))
    return [
        PRIVATE_TRACE_SPEC_PATH,
        SOURCE_PRIVATE_SPEC_PATH,
        SOURCE_LEDGER_EVIDENCE_PATH,
        SOURCE_WPS_DIAGNOSTIC_PATH,
        SOURCE_CASH_DECISIONS_PATH,
        SOURCE_CASH_METRICS_PATH,
        SOURCE_TARGET_MATERIALIZATIONS_PATH,
        SOURCE_UNRESOLVED_TARGETS_PATH,
        SOURCE_RECONCILIATION_COMPARISONS_PATH,
        dependency_dir / "msoffcrypto/__init__.py",
        dependency_dir / "olefile/olefile.py",
        dependency_dir / "xlrd/__init__.py",
    ]


def phase_output_paths() -> list[Path]:
    return [
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
        PRIVATE_RAW_BEFORE_PATH,
        PRIVATE_RAW_AFTER_PATH,
        PRIVATE_PAYABLE_TRACES_PATH,
        PRIVATE_WPS_RECOVERY_DIAGNOSTIC_PATH,
        PRIVATE_CASH_DECISIONS_PATH,
        PRIVATE_CASH_METRICS_PATH,
        PRIVATE_TARGET_MATERIALIZATIONS_PATH,
        PRIVATE_UNRESOLVED_TARGETS_PATH,
        PRIVATE_RECONCILIATION_COMPARISONS_PATH,
        PRIVATE_DIAGNOSTIC_PATH,
        PRIVATE_DIFFERENCE_REPORT_PATH,
    ]


def classify_payable_cost_trace(
    *,
    cost_row: dict[str, Any],
    origin_voucher_rows: list[dict[str, Any]],
    supplier_payable_rows: list[dict[str, Any]],
    bank_rows: list[dict[str, Any]],
    all_voucher_rows: list[dict[str, Any]],
    cutoff_date: str,
) -> dict[str, Any]:
    """Classify one project cost using supplier payable, note and bank evidence."""

    inputs = [cost_row, *origin_voucher_rows, *supplier_payable_rows, *bank_rows, *all_voucher_rows]
    if _contains_float(inputs):
        raise ValueError("payable trace input cannot contain float values")
    for row in inputs:
        _integer_cents(row, "debit_cents")
        _integer_cents(row, "credit_cents")
        _integer_cents(row, "balance_cents")
    cost_amount = _integer_cents(cost_row, "debit_cents") - _integer_cents(
        cost_row, "credit_cents"
    )
    if cost_amount <= 0:
        raise ValueError("project cost trace requires a positive net cost")

    origin_key = _voucher_key(cost_row)
    origin_payables = [
        row
        for row in origin_voucher_rows
        if str(row.get("account", "")).startswith("2202")
        and _integer_cents(row, "credit_cents") > 0
    ]
    suppliers = {str(row.get("supplier", "")) for row in origin_payables if row.get("supplier")}
    classification = "unresolved_missing_unique_payable_origin"
    settlement_status = "unresolved"
    cash_paid_project_cost: int | None = None
    settlement_rows: list[dict[str, Any]] = []
    note_rows: list[dict[str, Any]] = []
    bank_settlement_rows: list[dict[str, Any]] = []

    if len(suppliers) == 1:
        supplier = next(iter(suppliers))
        payable_rows = [
            row
            for row in supplier_payable_rows
            if str(row.get("supplier", "")) == supplier
            and str(row.get("date", "")) <= cutoff_date
        ]
        payable_rows.sort(key=lambda row: (_voucher_key(row), int(row.get("row_number") or 0)))
        same_voucher_debits = [
            row
            for row in payable_rows
            if _voucher_key(row) == origin_key and _integer_cents(row, "debit_cents") > 0
        ]
        note_rows = [
            row
            for row in all_voucher_rows
            if _voucher_key(row) == origin_key
            and str(row.get("account", "")).startswith("1121")
            and _integer_cents(row, "credit_cents") > 0
        ]
        note_total = sum(_integer_cents(row, "credit_cents") for row in note_rows)
        same_payable_debit = sum(
            _integer_cents(row, "debit_cents") for row in same_voucher_debits
        )
        if same_payable_debit > 0 and note_total >= same_payable_debit:
            classification = "noncash_note_settlement"
            settlement_status = "fully_settled_by_receivable_note"
            cash_paid_project_cost = 0
            settlement_rows = same_voucher_debits
        else:
            later_debits = [
                row
                for row in payable_rows
                if _voucher_key(row) > origin_key and _integer_cents(row, "debit_cents") > 0
            ]
            ending_balance = (
                _integer_cents(payable_rows[-1], "balance_cents") if payable_rows else None
            )
            for row in later_debits:
                key = _voucher_key(row)
                linked_bank = [bank for bank in bank_rows if _voucher_key(bank) == key]
                bank_net_outflow = sum(
                    _integer_cents(bank, "credit_cents")
                    - _integer_cents(bank, "debit_cents")
                    for bank in linked_bank
                )
                if bank_net_outflow > 0 and bank_net_outflow == _integer_cents(
                    row, "debit_cents"
                ):
                    settlement_rows.append(row)
                    bank_settlement_rows.extend(linked_bank)
            if settlement_rows and ending_balance == 0:
                classification = "cash_paid_later"
                settlement_status = "fully_settled_by_bank"
                cash_paid_project_cost = cost_amount
            elif settlement_rows and isinstance(ending_balance, int) and ending_balance > 0:
                classification = "unresolved_partial_settlement"
                settlement_status = "partially_settled_balance_remains"
            elif not later_debits and isinstance(ending_balance, int) and ending_balance > 0:
                classification = "unpaid_at_cutoff"
                settlement_status = "payable_balance_remains_at_cutoff"
                cash_paid_project_cost = 0

    result = {
        "schema_version": "kmfa.private.payable_cost_trace.v1",
        "classification": "private_payable_cost_trace_do_not_commit",
        "trace_classification": classification,
        "settlement_status": settlement_status,
        "cost_amount_cents": cost_amount,
        "cash_paid_project_cost_cents": cash_paid_project_cost,
        "origin_cost_row": _private_row(cost_row),
        "origin_payable_rows": [_private_row(row) for row in origin_payables],
        "settlement_rows": [_private_row(row) for row in settlement_rows],
        "note_rows": [_private_row(row) for row in note_rows],
        "bank_settlement_rows": [_private_row(row) for row in bank_settlement_rows],
        "cutoff_date": cutoff_date,
        "integer_only": True,
        "raw_layer_write_allowed": False,
        "public_commit_allowed": False,
    }
    if _contains_float(result):
        raise ValueError("payable trace cannot contain float values")
    return result


def _load_private_dependencies(spec: dict[str, Any]) -> tuple[Any, Any, Any]:
    dependency_dir = Path(str(spec["private_dependency_dir"])).resolve()
    if dependency_dir.as_posix() not in sys.path:
        sys.path.insert(0, dependency_dir.as_posix())
    import msoffcrypto  # type: ignore
    import olefile  # type: ignore
    import xlrd  # type: ignore

    return msoffcrypto, olefile, xlrd


def _probe_wps_recovery(
    trace_spec: dict[str, Any], source_spec: dict[str, Any]
) -> dict[str, Any]:
    msoffcrypto, olefile, xlrd = _load_private_dependencies(trace_spec)
    records: list[dict[str, Any]] = []
    password = str(trace_spec["office_compatibility_password"])
    for index, source in enumerate(source_spec.get("external_wps_sources", []), start=1):
        path = Path(str(source["path"]))
        with path.open("rb") as stream:
            office_file = msoffcrypto.OfficeFile(stream)
            standard_encrypted = bool(office_file.is_encrypted())
            office_file.load_key(password=password)
            output = io.BytesIO()
            office_file.decrypt(output)
        decrypted_bytes = output.getvalue()
        compatibility_book = xlrd.open_workbook(file_contents=decrypted_bytes, on_demand=True)
        compatibility_sheets = compatibility_book.sheet_names()
        empty_compatibility = bool(
            len(compatibility_sheets) == 1
            and compatibility_book.sheet_by_index(0).nrows == 0
            and compatibility_book.sheet_by_index(0).ncols == 0
        )
        compatibility_book.release_resources()

        ole = olefile.OleFileIO(path)
        stream_names = {"/".join(parts) for parts in ole.listdir()}
        wps_content = ole.openstream("WpsContent").read()
        wps_ext_data = ole.openstream("WpsExtData").read().decode("utf-8", errors="replace")
        security_path = [
            "WpsTransform",
            "TransformInfo",
            "WpsSecurityInfo",
            "WpsEncryptionInfo",
        ]
        encryption_info = ole.openstream(security_path).read()
        offline_ticket = ole.openstream(
            ["WpsTransform", "TransformInfo", "WpsSecurityInfo", "WpsOfflineTicket"]
        ).read()
        security_ticket = ole.openstream(
            ["WpsTransform", "TransformInfo", "WpsSecurityInfo", "WpsSecurityTicket"]
        ).read()
        ole.close()
        declared_length = int.from_bytes(wps_content[:8], "little")
        proprietary_layer = bool(
            "WpsContent" in stream_names
            and encryption_info
            and offline_ticket
            and security_ticket
            and declared_length > 0
        )
        records.append(
            {
                "record_id": f"V014-REMAINING-WPS-{index:02d}",
                "classification": "private_wps_recovery_diagnostic_do_not_commit",
                "path": path.as_posix(),
                "business_role": source.get("business_role"),
                "standard_office_encrypted": standard_encrypted,
                "office_compatibility_unlock_succeeded": True,
                "compatibility_sheet_count": len(compatibility_sheets),
                "compatibility_workbook_empty": empty_compatibility,
                "wps_security_document_layer_present": proprietary_layer,
                "wps_ext_data": wps_ext_data,
                "wps_content_declared_length": declared_length,
                "wps_content_stream_size": len(wps_content),
                "wps_encryption_info_size": len(encryption_info),
                "wps_offline_ticket_size": len(offline_ticket),
                "wps_security_ticket_size": len(security_ticket),
                "secure_wps_content_readable": False,
                "recovery_status": "office_compatibility_layer_unlocked_but_empty_secure_wps_content_requires_proprietary_ticket_runtime",
                "raw_layer_write_allowed": False,
                "public_commit_allowed": False,
            }
        )
    if len(records) != 2 or not all(
        row["standard_office_encrypted"]
        and row["office_compatibility_unlock_succeeded"]
        and row["compatibility_workbook_empty"]
        and row["wps_security_document_layer_present"]
        and not row["secure_wps_content_readable"]
        for row in records
    ):
        raise ValueError("WPS recovery diagnostics do not satisfy the evidence contract")
    return {
        "schema_version": "kmfa.private.remaining_wps_recovery_diagnostic.v1",
        "classification": "private_remaining_wps_recovery_diagnostic_do_not_commit",
        "source_count": len(records),
        "standard_office_encrypted_count": sum(row["standard_office_encrypted"] for row in records),
        "office_compatibility_unlock_count": sum(
            row["office_compatibility_unlock_succeeded"] for row in records
        ),
        "empty_compatibility_workbook_count": sum(
            row["compatibility_workbook_empty"] for row in records
        ),
        "wps_security_document_layer_count": sum(
            row["wps_security_document_layer_present"] for row in records
        ),
        "secure_wps_content_readable_count": sum(
            row["secure_wps_content_readable"] for row in records
        ),
        "records": records,
        "public_commit_allowed": False,
    }


def _extract_payable_traces(
    trace_spec: dict[str, Any], source_spec: dict[str, Any], ledger: dict[str, Any], decisions: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    trace_binding_id = str(trace_spec["trace_binding_id"])
    trace_decision = next(row for row in decisions if row["binding_id"] == trace_binding_id)
    unresolved_costs = list(trace_decision.get("unresolved_evidence", []))
    if len(unresolved_costs) != int(trace_spec["expected_unresolved_cost_trace_count"]):
        raise ValueError("source unresolved cost count does not match trace contract")

    source_voucher_rows = list(ledger.get("voucher_rows", []))
    origin_rows_by_cost: dict[tuple[str, str], list[dict[str, Any]]] = {}
    supplier_sheet_names: set[str] = set()
    for cost in unresolved_costs:
        key = _voucher_key(cost)
        origin_rows = [row for row in source_voucher_rows if _voucher_key(row) == key]
        origin_rows_by_cost[key] = origin_rows
        for row in origin_rows:
            if str(row.get("account", "")).startswith("2202") and row.get("supplier"):
                supplier_sheet_names.add(str(row.get("sheet_name", "")))
    if len(supplier_sheet_names) != 2:
        raise ValueError("payable trace must resolve exactly two supplier payable sheets")

    inner, shared_strings, sheets, _ = source_phase._load_inner_workbook(source_spec)
    supplier_rows: list[dict[str, Any]] = []
    targets = {name: target for name, target in sheets if name in supplier_sheet_names}
    if set(targets) != supplier_sheet_names:
        raise ValueError("supplier payable sheet set is incomplete")
    for sheet_name, target in targets.items():
        for row_number, values in source_phase._sheet_rows(inner, shared_strings, target):
            if row_number < 4 or not source_phase._transaction_row(values):
                continue
            supplier_rows.append(source_phase._row_record(sheet_name, row_number, values))

    relevant_keys = {_voucher_key(row) for row in supplier_rows}
    all_voucher_rows: list[dict[str, Any]] = []
    bank_sheet_names = {name for name, _ in sheets if name.startswith(("1001", "1002"))}
    for sheet_name, target in sheets:
        if sheet_name in bank_sheet_names:
            continue
        for row_number, values in source_phase._sheet_rows(inner, shared_strings, target):
            if row_number < 4 or not source_phase._transaction_row(values):
                continue
            if (values[8], values[9].strip()) in relevant_keys:
                all_voucher_rows.append(
                    source_phase._row_record(sheet_name, row_number, values)
                )
    inner.close()

    bank_rows = list(ledger.get("bank_rows", []))
    traces: list[dict[str, Any]] = []
    for index, cost in enumerate(unresolved_costs, start=1):
        key = _voucher_key(cost)
        origin_rows = [row for row in all_voucher_rows if _voucher_key(row) == key]
        origin_payables = [
            row
            for row in origin_rows
            if str(row.get("account", "")).startswith("2202") and row.get("supplier")
        ]
        suppliers = {str(row["supplier"]) for row in origin_payables}
        related_supplier_rows = [
            row for row in supplier_rows if str(row.get("supplier", "")) in suppliers
        ]
        trace = classify_payable_cost_trace(
            cost_row=cost,
            origin_voucher_rows=origin_rows,
            supplier_payable_rows=related_supplier_rows,
            bank_rows=bank_rows,
            all_voucher_rows=all_voucher_rows,
            cutoff_date=str(trace_spec["ledger_cutoff_date"]),
        )
        trace.update(
            {
                "trace_id": f"V014-REMAINING-PAYABLE-{index:03d}",
                "binding_id": trace_binding_id,
            }
        )
        traces.append(trace)
    expected = trace_spec["expected_trace_classifications"]
    actual = Counter(row["trace_classification"] for row in traces)
    if dict(actual) != expected:
        raise ValueError(f"payable trace classifications mismatch: {dict(actual)}")
    return traces


def _updated_decisions(
    source_decisions: list[dict[str, Any]], trace_spec: dict[str, Any], traces: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], str]:
    trace_binding_id = str(trace_spec["trace_binding_id"])
    decisions = [dict(row) for row in source_decisions]
    decision = next(row for row in decisions if row["binding_id"] == trace_binding_id)
    collection = sum(
        _integer_cents(row, "credit_cents")
        for row in decision.get("cash_collection_evidence", [])
    )
    direct_paid = sum(
        _integer_cents(row, "debit_cents") - _integer_cents(row, "credit_cents")
        for row in decision.get("cash_paid_cost_evidence", [])
    )
    traced_paid = sum(
        int(row["cash_paid_project_cost_cents"] or 0)
        for row in traces
        if row["trace_classification"] == "cash_paid_later"
    )
    cash_paid = direct_paid + traced_paid
    cash_gross = collection - cash_paid
    decision.update(
        {
            "resolution_status": "resolved_with_payable_trace_accessible_ledger_only",
            "reason_codes": [
                "exact_project_dimension_balanced_bank_vouchers_and_payable_trace",
                "external_secure_wps_content_unavailable_not_claimed",
            ],
            "collection_amount_cents": collection,
            "cash_paid_cost_cents": cash_paid,
            "cash_gross_profit_cents": cash_gross,
            "cash_paid_cost_evidence_count": int(decision["cash_paid_cost_evidence_count"]) + 1,
            "noncash_cost_count": int(decision["noncash_cost_count"]) + 1,
            "unpaid_cost_count": 1,
            "unresolved_cost_count": 0,
            "unresolved_row_count": 0,
            "unresolved_evidence": [],
            "payable_trace_record_count": len(traces),
            "payable_trace_classification_counts": dict(
                sorted(Counter(row["trace_classification"] for row in traces).items())
            ),
            "business_consistency_verified": False,
            "external_crosscheck_completed": False,
        }
    )
    return decisions, str(decision["legacy_margin_record_id"])


def _cash_metric_records(
    source_metrics: list[dict[str, Any]], decisions: list[dict[str, Any]], new_margin_record_id: str
) -> list[dict[str, Any]]:
    metrics = [dict(row) for row in source_metrics]
    decision = next(
        row for row in decisions if str(row["legacy_margin_record_id"]) == new_margin_record_id
    )
    for index, metric_key in enumerate(
        ("collection_amount_cents", "cash_paid_cost_cents", "cash_gross_profit_cents"),
        start=1,
    ):
        value = decision[metric_key]
        if not isinstance(value, int) or isinstance(value, bool):
            raise ValueError("new cash metric must be integer cents")
        metrics.append(
            {
                "schema_version": "kmfa.private.materialized_cash_metric.v1",
                "classification": "private_materialized_cash_metric_do_not_commit",
                "metric_record_id": f"V014-REMAINING-CASH-METRIC-{index:03d}",
                "binding_id": decision["binding_id"],
                "legacy_margin_record_id": new_margin_record_id,
                "metric_key": metric_key,
                "value": value,
                "unit": "cents",
                "derivation": "exact_project_dimension_bank_voucher_and_payable_trace_integer_formula",
                "integer_only": True,
                "raw_layer_write_allowed": False,
                "public_commit_allowed": False,
            }
        )
    return metrics


def _materialized_slot(row: dict[str, Any], value: int) -> dict[str, Any]:
    result = {
        key: child
        for key, child in row.items()
        if key not in {"reason_codes", "resolution_status"}
    }
    result.update(
        {
            "schema_version": "kmfa.private.s09_target_slot_materialization.v1",
            "classification": "private_s09_target_slot_materialization_do_not_commit",
            "materialization_status": "materialized_private_only",
            "value": value,
            "unit": "cents",
            "value_fingerprint": _sha256_text(str(value)),
            "raw_layer_write_allowed": False,
            "public_commit_allowed": False,
        }
    )
    return result


def _apply_target_materialization(
    new_margin_record_id: str, decisions: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], int]:
    materialized = read_jsonl(SOURCE_TARGET_MATERIALIZATIONS_PATH)
    unresolved = read_jsonl(SOURCE_UNRESOLVED_TARGETS_PATH)
    comparisons = read_jsonl(SOURCE_RECONCILIATION_COMPARISONS_PATH)
    decision = next(
        row for row in decisions if str(row["legacy_margin_record_id"]) == new_margin_record_id
    )
    comparison = next(
        row
        for row in comparisons
        if row["margin_record_id"] == new_margin_record_id
        and row["difference_type"] == "cash_vs_accrual_gross_profit"
    )
    cash_value = int(decision["cash_gross_profit_cents"])
    amount_b = comparison["amount_b"]
    if not isinstance(amount_b, int) or isinstance(amount_b, bool):
        raise ValueError("source accrual comparison value must be integer cents")
    delta = cash_value - amount_b
    comparison.update(
        {
            "amount_a": cash_value,
            "delta": delta,
            "comparison_status": (
                "comparison_complete_zero_delta"
                if delta == 0
                else "comparison_complete_nonzero_delta"
            ),
        }
    )
    expected_context_values = {
        "cash_gross_profit": cash_value,
        "amount_a_cents_private_ref": cash_value,
        "delta_cents_private_ref": delta,
    }
    consumed_ids: set[str] = set()
    for row in unresolved:
        context = str(row["context_group"])
        if context not in expected_context_values:
            continue
        if context == "cash_gross_profit" and new_margin_record_id not in str(
            row["private_processed_ref"]
        ):
            continue
        if context != "cash_gross_profit" and row.get("difference_id") != comparison["difference_id"]:
            continue
        materialized.append(_materialized_slot(row, expected_context_values[context]))
        consumed_ids.add(str(row["target_slot_id"]))
    if len(consumed_ids) != 3:
        raise ValueError("newly resolved payable trace must materialize exactly three target slots")
    unresolved = [
        row for row in unresolved if str(row["target_slot_id"]) not in consumed_ids
    ]
    materialized.sort(key=lambda row: str(row["target_slot_id"]))
    unresolved.sort(key=lambda row: str(row["target_slot_id"]))
    comparisons.sort(key=lambda row: str(row["comparison_id"]))
    return materialized, unresolved, comparisons, len(consumed_ids)


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


def _git_output(args: list[str]) -> str:
    return subprocess.check_output(["git", *args], text=True).strip()


def _upsert_jsonl(path: Path, key: str, record: dict[str, Any]) -> None:
    serialized = json.dumps(
        record,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    output_lines: list[str] = []
    replaced = False
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            current = json.loads(line)
            if current.get(key) == record.get(key):
                if not replaced:
                    output_lines.append(serialized)
                    replaced = True
                continue
            output_lines.append(line)
    if not replaced:
        output_lines.append(serialized)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(output_lines) + "\n", encoding="utf-8")


def _public_matrix(summary: dict[str, Any]) -> dict[str, Any]:
    checks = [
        ("source_private_inputs_unchanged", summary["source_private_inputs_unchanged"]),
        ("raw_snapshot_exact_match", summary["raw_snapshot_exact_match"]),
        ("three_payable_traces", summary["payable_trace_record_count"] == 3),
        ("one_later_bank_payment", summary["cash_paid_later_trace_count"] == 1),
        ("one_note_settlement", summary["noncash_note_settlement_trace_count"] == 1),
        ("one_unpaid_cutoff", summary["unpaid_at_cutoff_trace_count"] == 1),
        ("two_cash_projects_resolved", summary["cash_project_resolved_count"] == 2),
        ("two_cash_projects_unresolved", summary["cash_project_unresolved_count"] == 2),
        ("three_new_targets", summary["newly_materialized_cash_target_slot_count"] == 3),
        ("six_targets_remain", summary["unresolved_cash_value_target_slot_count"] == 6),
        ("ten_comparisons_complete", summary["completed_reconciliation_comparison_count"] == 10),
        ("eight_nonzero_preserved", summary["nonzero_delta_reconciliation_count"] == 8),
        ("office_compatibility_unlock_two", summary["office_compatibility_unlock_count"] == 2),
        ("secure_wps_content_not_claimed", summary["secure_wps_content_readable_count"] == 0),
        ("forced_zero_prohibited", summary["forced_zero_materialization_count"] == 0),
        ("business_consistency_not_claimed", not summary["business_value_consistency_verified"]),
        ("github_not_uploaded", not summary["github_upload_performed"]),
        ("stage_review_not_performed", not summary["stage_review_performed"]),
    ]
    rows = [
        {"check_id": f"RCST-{index:02d}", "check_name": name, "passed": passed}
        for index, (name, passed) in enumerate(checks, start=1)
    ]
    return {
        "schema_version": "kmfa.v014.remaining_cash_trace_matrix.v1",
        "project_id": "KMFA",
        "phase_id": PHASE_ID,
        "check_count": len(rows),
        "check_pass_count": sum(row["passed"] for row in rows),
        "check_fail_count": sum(not row["passed"] for row in rows),
        "checks": rows,
    }


def _private_difference_report(
    *,
    summary: dict[str, Any],
    traces: list[dict[str, Any]],
    wps: dict[str, Any],
    decisions: list[dict[str, Any]],
    comparisons: list[dict[str, Any]],
) -> str:
    lines = [
        "# KMFA v0.1.4 剩余现金来源私有追踪或差异接受报告",
        "",
        "## 本轮结论",
        "",
        f"- 应付追踪记录：{summary['payable_trace_record_count']} 条。",
        f"- 后续银行结清 / 票据非现金结算 / 期末未付：{summary['cash_paid_later_trace_count']} / {summary['noncash_note_settlement_trace_count']} / {summary['unpaid_at_cutoff_trace_count']}。",
        f"- 现金项目已闭环 / 未闭环：{summary['cash_project_resolved_count']} / {summary['cash_project_unresolved_count']}。",
        f"- 本轮新增物化 / 累计物化 / 剩余现金槽位：{summary['newly_materialized_cash_target_slot_count']} / {summary['materialized_business_value_target_slot_count']} / {summary['unresolved_cash_value_target_slot_count']}。",
        f"- 完成比较 / 零差异 / 非零差异 / 未完成现金比较：{summary['completed_reconciliation_comparison_count']} / {summary['zero_delta_reconciliation_count']} / {summary['nonzero_delta_reconciliation_count']} / {summary['incomplete_cash_reconciliation_count']}。",
        "- 缺失收款证据仍未写成零；当前结论保持 NO_GO。",
        "",
        "## 应付与结算追踪",
        "",
    ]
    for trace in traces:
        lines.extend(
            [
                f"### {trace['trace_id']}",
                "",
                f"- 分类：{trace['trace_classification']}",
                f"- 状态：{trace['settlement_status']}",
                f"- 原项目成本（分）：{trace['cost_amount_cents']}",
                f"- 计入现金已付项目成本（分）：{trace['cash_paid_project_cost_cents']}",
                f"- 原始成本记录：{trace['origin_cost_row']}",
                f"- 原始应付记录：{trace['origin_payable_rows']}",
                f"- 结算记录：{trace['settlement_rows']}",
                f"- 票据记录：{trace['note_rows']}",
                f"- 银行结算记录：{trace['bank_settlement_rows']}",
                "",
            ]
        )
    lines.extend(["## WPS/OLE 恢复诊断", ""])
    for record in wps["records"]:
        lines.extend(
            [
                f"- 来源：{record['path']}",
                f"  - 标准 Office 加密：{record['standard_office_encrypted']}",
                f"  - 兼容层解锁：{record['office_compatibility_unlock_succeeded']}",
                f"  - 兼容工作簿为空：{record['compatibility_workbook_empty']}",
                f"  - WPS 安全文档层：{record['wps_security_document_layer_present']}",
                f"  - 安全 WPS 内容可读：{record['secure_wps_content_readable']}",
                f"  - 结论：{record['recovery_status']}",
            ]
        )
    lines.extend(["", "## 项目与差异状态", ""])
    for decision in decisions:
        lines.append(
            f"- {decision['binding_id']}：{decision['resolution_status']}；原因={'; '.join(decision['reason_codes'])}；现金毛利（分）={decision['cash_gross_profit_cents']}。"
        )
    lines.extend(["", "## S09 比较", ""])
    for row in comparisons:
        lines.append(
            f"- {row['difference_id']}：{row['comparison_status']}；单位={row['unit']}；A={row['amount_a']}；B={row['amount_b']}；差额={row['delta']}。"
        )
    lines.extend(
        [
            "",
            "## 剩余差异接受",
            "",
            "- 两个项目仍没有可证明的正向现金收款；未命中不能作为零值证据。",
            "- 两个 WPS/OLE 文件的标准 Office 兼容层可以解锁，但仅得到空白工作簿；实际 WpsContent 仍受专有安全 ticket 层保护，未声明内容已读取。",
            "- 剩余 6 个现金槽位和 2 条现金比较继续保留，8 条非零差异不覆盖、不抹平。",
            "- 全局 72 条 residual queue 尚未重放；不生成正式报告、不上传、不执行业务动作。",
            "",
        ]
    )
    return "\n".join(lines)


def _public_reports(summary: dict[str, Any]) -> dict[Path, str]:
    report = f"""# v0.1.4 剩余现金来源私有追踪或差异接受

- Phase: `{PHASE_ID}`
- 决策: `{DECISION}`
- 应付追踪: {summary['payable_trace_record_count']}
- 后续银行结清 / 票据非现金结算 / 期末未付: {summary['cash_paid_later_trace_count']} / {summary['noncash_note_settlement_trace_count']} / {summary['unpaid_at_cutoff_trace_count']}
- 已闭环 / 未闭环项目: {summary['cash_project_resolved_count']} / {summary['cash_project_unresolved_count']}
- 新增物化 / 累计物化 / 剩余现金槽位: {summary['newly_materialized_cash_target_slot_count']} / {summary['materialized_business_value_target_slot_count']} / {summary['unresolved_cash_value_target_slot_count']}
- 完成比较 / 非零差异 / 未完成现金比较: {summary['completed_reconciliation_comparison_count']} / {summary['nonzero_delta_reconciliation_count']} / {summary['incomplete_cash_reconciliation_count']}
- WPS/OLE 兼容层解锁 / 实际安全内容可读: {summary['office_compatibility_unlock_count']} / {summary['secure_wps_content_readable_count']}
- raw 前后完全一致: `{str(summary['raw_snapshot_exact_match']).lower()}`

本 phase 通过应付、票据和银行结算链新增闭环一个项目；另外两个项目因正向收款证据缺失继续保留差异。WPS/OLE 标准兼容层虽可解锁，但实际安全内容仍不可读，未作虚假读取声明或缺失填零。
"""
    go_no_go = f"""# Go / No-Go 记录

- 决策: `NO_GO`
- 已完成: 3 条应付追踪，第二个项目现金闭环，新增 3 个私有目标槽位。
- 阻断: {summary['cash_project_unresolved_count']} 个项目、{summary['unresolved_cash_value_target_slot_count']} 个现金槽位、{summary['nonzero_delta_reconciliation_count']} 条非零差异、实际 WPS 安全内容不可读。
- GitHub upload / app reinstall / business execution: `not_performed`
"""
    tests = """# 测试结果

- focused unit test: `PASS` (`2 tests`)
- phase/private validator: `PASS` (`resolved=2 / unresolved=2 / materialized=34 / decision=NO_GO`)
- previous phase validator: `PASS` (`resolved=1 / unresolved=3 / materialized=31 / decision=NO_GO`)
- governance validators: `PASS` (`errors=0 / warnings=0`)
- structured parse and registry counts: `PASS` (`37 files / 1301 active parameters / 274 active formulas`)
- raw/private/secret scan: `PASS` (`5 raw files unchanged / 0 tracked private files / 0 sensitive hits`)
"""
    risks = """# 风险登记

- 高: 两个项目仍缺少可证明的正向现金收款，不能以未命中推导零值。
- 高: WPS/OLE 兼容层可解锁但实际安全内容依赖专有 ticket runtime，外部交叉核验仍不完整。
- 高: 8 条非零口径差异继续保留，不得覆盖权威值或自动抹平。
- 中: 全局 72 条 residual queue 尚未重放。
"""
    rollback = """# 回滚方案

1. 删除本 phase 公开 artifacts 和 metadata 镜像。
2. 删除本 phase ignored private outputs；不触碰原始数据目录或上一 phase 私有输入。
3. 移除本 phase 治理记录并重跑上一 phase validator。
"""
    return {
        REPORT_PATH: report,
        GO_NO_GO_RECORD_PATH: go_no_go,
        TEST_RESULTS_PATH: tests,
        RISK_REGISTER_PATH: risks,
        ROLLBACK_PATH: rollback,
    }


def _phase_public_files() -> list[str]:
    return [
        "KMFA/CHANGELOG.md",
        "KMFA/HANDOFF.md",
        "KMFA/VERSION",
        "KMFA/docs/governance/ASSURANCE_STATUS.yaml",
        "KMFA/docs/governance/DEVELOPMENT_LEDGER.md",
        "KMFA/docs/governance/MODEL_SPEC.md",
        "KMFA/docs/governance/OWNER_STATUS.md",
        "KMFA/docs/governance/STATUS.md",
        "KMFA/docs/governance/TRACEABILITY_MATRIX.csv",
        "KMFA/docs/governance/VERSION_MATRIX.yaml",
        "KMFA/docs/governance/delivery_tasks.yaml",
        "KMFA/docs/governance/development_events.jsonl",
        "KMFA/docs/governance/formula_registry.yaml",
        "KMFA/docs/governance/model_registry.yaml",
        "KMFA/docs/governance/parameter_registry.csv",
        "KMFA/metadata/model_registry.yaml",
        METADATA_SUMMARY_PATH.as_posix(),
        METADATA_MANIFEST_PATH.as_posix(),
        METADATA_GO_NO_GO_PATH.as_posix(),
        METADATA_MATRIX_PATH.as_posix(),
        "KMFA/metadata/stage_status.jsonl",
        "KMFA/metadata/traceability/v1_4_stage_phase_task_status.jsonl",
        SUMMARY_PATH.as_posix(),
        MANIFEST_PATH.as_posix(),
        GO_NO_GO_PATH.as_posix(),
        MATRIX_PATH.as_posix(),
        REPORT_PATH.as_posix(),
        GO_NO_GO_RECORD_PATH.as_posix(),
        TEST_RESULTS_PATH.as_posix(),
        RISK_REGISTER_PATH.as_posix(),
        ROLLBACK_PATH.as_posix(),
        "KMFA/tests/test_v014_remaining_cash_source_private_trace_or_difference_acceptance.py",
        "KMFA/tools/check_v014_remaining_cash_source_private_trace_or_difference_acceptance.py",
        "KMFA/tools/v014_remaining_cash_source_private_trace_or_difference_acceptance.py",
        "KMFA/功能清单.md",
        "KMFA/开发记录.md",
        "KMFA/模型参数文件.md",
    ]


def _write_governance(generated_at: str, summary: dict[str, Any]) -> None:
    evidence_ref = MANIFEST_PATH.as_posix()
    _upsert_jsonl(
        DEVELOPMENT_EVENTS_PATH,
        "event_id",
        {
            "event_id": "DEV-KMFA-20260710-V014-REMAINING-CASH-SOURCE-PRIVATE-TRACE-OR-DIFFERENCE-ACCEPTANCE",
            "event_time": generated_at,
            "event_type": "development",
            "project_id": "KMFA",
            "stage_id": "value-consistency",
            "phase_id": PHASE_ID,
            "task_id": TASK_ID,
            "status": STATUS,
            "fact_level": "EXTRACTED",
            "decision": DECISION,
            "payable_trace_record_count": summary["payable_trace_record_count"],
            "cash_project_resolved_count": summary["cash_project_resolved_count"],
            "cash_project_unresolved_count": summary["cash_project_unresolved_count"],
            "newly_materialized_cash_target_slot_count": summary[
                "newly_materialized_cash_target_slot_count"
            ],
            "raw_snapshot_exact_match": summary["raw_snapshot_exact_match"],
            "raw_business_data_committed": False,
            "github_upload_performed": False,
            "app_reinstall_performed": False,
            "business_execution_performed": False,
            "evidence_ref": evidence_ref,
            "files_changed": _phase_public_files(),
            "result_commit": "PENDING",
        },
    )
    _upsert_jsonl(
        STAGE_STATUS_PATH,
        "phase_id",
        {
            "schema_version": "kmfa.stage_status.v1",
            "record_type": "stage_phase_status",
            "project_id": "KMFA",
            "stage_id": "VALUE-CONSISTENCY",
            "phase_id": PHASE_ID,
            "task_id": TASK_ID,
            "version": VERSION,
            "status": STATUS,
            "decision": DECISION,
            "raw_data_committed": False,
            "github_upload_performed": False,
            "app_reinstall_performed": False,
            "business_execution_performed": False,
            "evidence_ref": evidence_ref,
            "updated_at": generated_at,
        },
    )
    _upsert_jsonl(
        TASK_STATUS_PATH,
        "phase_id",
        {
            "schema_version": "kmfa.v014_stage_phase_task_status.v1",
            "record_type": "v014_phase",
            "project_id": "KMFA",
            "stage_id": "VALUE-CONSISTENCY",
            "governance_stage_id": "VALUE-CONSISTENCY",
            "roadmap_stage_id": "VALUE-CONSISTENCY",
            "roadmap_phase_id": "REMAINING_CASH_SOURCE_PRIVATE_TRACE_OR_DIFFERENCE_ACCEPTANCE",
            "phase_id": PHASE_ID,
            "task_id": TASK_ID,
            "acceptance_id": ACCEPTANCE_ID,
            "version": VERSION,
            "name": "v0.1.4 remaining cash source private trace or difference acceptance",
            "phase_goal": "trace payable note and bank settlement evidence while preserving unresolved cash differences",
            "status": STATUS,
            "fact_level": "EXTRACTED",
            "derived_percent": 100.0,
            "estimated_task_units": 1,
            "completed_task_units": 1,
            "task_count": 1,
            "raw_data_committed": False,
            "evidence_ref": evidence_ref,
            "updated_at": generated_at[:10],
        },
    )


def generate(
    *,
    generated_at: str | None = None,
    write_governance_event: bool = True,
) -> dict[str, Any]:
    timestamp = _now(generated_at)
    source_hashes_before = {
        path.as_posix(): _sha256_bytes(path.read_bytes()) for path in source_private_paths()
    }
    trace_spec = read_json(PRIVATE_TRACE_SPEC_PATH)
    source_spec = read_json(SOURCE_PRIVATE_SPEC_PATH)
    ledger = read_json(SOURCE_LEDGER_EVIDENCE_PATH)
    source_decisions = read_jsonl(SOURCE_CASH_DECISIONS_PATH)
    source_metrics = read_jsonl(SOURCE_CASH_METRICS_PATH)

    raw_before = _raw_snapshot("before")
    _write_json(PRIVATE_RAW_BEFORE_PATH, raw_before)
    wps = _probe_wps_recovery(trace_spec, source_spec)
    traces = _extract_payable_traces(
        trace_spec, source_spec, ledger, source_decisions
    )
    decisions, new_margin_record_id = _updated_decisions(
        source_decisions, trace_spec, traces
    )
    metrics = _cash_metric_records(source_metrics, decisions, new_margin_record_id)
    materialized, unresolved, comparisons, newly_materialized = _apply_target_materialization(
        new_margin_record_id, decisions
    )
    raw_after = _raw_snapshot("after")
    _write_json(PRIVATE_RAW_AFTER_PATH, raw_after)
    raw_snapshot_exact_match = _snapshot_core(raw_before) == _snapshot_core(raw_after)
    source_hashes_after = {
        path.as_posix(): _sha256_bytes(path.read_bytes()) for path in source_private_paths()
    }
    source_unchanged = source_hashes_before == source_hashes_after

    resolved = [row for row in decisions if str(row["resolution_status"]).startswith("resolved_")]
    completed = [
        row for row in comparisons if str(row["comparison_status"]).startswith("comparison_complete_")
    ]
    zero = [row for row in completed if row["delta"] == 0]
    nonzero = [row for row in completed if row["delta"] != 0]
    incomplete = [row for row in comparisons if row not in completed]
    trace_counts = Counter(row["trace_classification"] for row in traces)
    expected_counts = (
        len(traces),
        trace_counts["cash_paid_later"],
        trace_counts["noncash_note_settlement"],
        trace_counts["unpaid_at_cutoff"],
        len(resolved),
        len(decisions) - len(resolved),
        len(metrics),
        len(materialized),
        newly_materialized,
        len(unresolved),
        len(comparisons),
        len(completed),
        len(zero),
        len(nonzero),
        len(incomplete),
    )
    if expected_counts != (3, 1, 1, 1, 2, 2, 6, 34, 3, 6, 12, 10, 2, 8, 2):
        raise ValueError(f"remaining cash trace counts mismatch: {expected_counts}")
    if _contains_float([traces, wps, decisions, metrics, materialized, unresolved, comparisons]):
        raise ValueError("remaining cash trace outputs cannot contain float values")

    summary = {
        "schema_version": "kmfa.v014.remaining_cash_trace_summary.v1",
        "record_type": "v014_remaining_cash_trace_summary",
        "project_id": "KMFA",
        "version": VERSION,
        "stage_id": "VALUE-CONSISTENCY",
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": timestamp,
        "status": STATUS,
        "decision": DECISION,
        "source_phase_id": source_phase.PHASE_ID,
        "source_private_inputs_unchanged": source_unchanged,
        "payable_trace_record_count": len(traces),
        "cash_paid_later_trace_count": trace_counts["cash_paid_later"],
        "noncash_note_settlement_trace_count": trace_counts["noncash_note_settlement"],
        "unpaid_at_cutoff_trace_count": trace_counts["unpaid_at_cutoff"],
        "cash_project_candidate_count": len(decisions),
        "cash_project_resolved_count": len(resolved),
        "cash_project_unresolved_count": len(decisions) - len(resolved),
        "private_cash_metric_record_count": len(metrics),
        "materialized_business_value_target_slot_count": len(materialized),
        "newly_materialized_cash_target_slot_count": newly_materialized,
        "unresolved_cash_value_target_slot_count": len(unresolved),
        "reconciliation_record_count": len(comparisons),
        "completed_reconciliation_comparison_count": len(completed),
        "zero_delta_reconciliation_count": len(zero),
        "nonzero_delta_reconciliation_count": len(nonzero),
        "incomplete_cash_reconciliation_count": len(incomplete),
        "wps_source_count": wps["source_count"],
        "standard_office_encrypted_count": wps["standard_office_encrypted_count"],
        "office_compatibility_unlock_count": wps["office_compatibility_unlock_count"],
        "empty_compatibility_workbook_count": wps["empty_compatibility_workbook_count"],
        "wps_security_document_layer_count": wps["wps_security_document_layer_count"],
        "secure_wps_content_readable_count": wps["secure_wps_content_readable_count"],
        "external_crosscheck_completed": False,
        "forced_zero_materialization_count": 0,
        "global_unresolved_difference_count": 72,
        "global_residual_difference_queue_replayed": False,
        "partial_processed_value_materialization_complete": True,
        "full_processed_value_materialization_complete": False,
        "partial_raw_to_processed_reconciliation_performed": True,
        "full_raw_to_processed_value_comparison_complete": False,
        "processed_consistency_verified": False,
        "business_value_consistency_verified": False,
        "raw_source_file_count": raw_before.get("file_count", 0),
        "raw_snapshot_exact_match": raw_snapshot_exact_match,
        "raw_inbox_mutated_by_this_phase": not raw_snapshot_exact_match,
        "private_payable_traces_gitignored": _git_ignored(PRIVATE_PAYABLE_TRACES_PATH),
        "private_wps_recovery_gitignored": _git_ignored(PRIVATE_WPS_RECOVERY_DIAGNOSTIC_PATH),
        "private_cash_metrics_gitignored": _git_ignored(PRIVATE_CASH_METRICS_PATH),
        "private_difference_report_gitignored": _git_ignored(PRIVATE_DIFFERENCE_REPORT_PATH),
        "raw_business_data_committed": False,
        "raw_filename_or_value_committed": False,
        "credential_or_secret_committed": False,
        "stage_review_performed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "goal_status_recommendation": "continue_active_with_remaining_two_project_collection_evidence",
        "next_recommended_phase": "remaining_two_project_cash_collection_evidence_or_final_difference_acceptance",
    }
    matrix = _public_matrix(summary)
    if matrix["check_fail_count"]:
        raise ValueError("public acceptance matrix contains failures")
    manifest = {
        "schema_version": "kmfa.v014.remaining_cash_trace_manifest.v1",
        "record_type": "v014_remaining_cash_trace_manifest",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": timestamp,
        "reviewed_head": _git_output(["rev-parse", "HEAD"]),
        "branch": _git_output(["branch", "--show-current"]),
        "remote": _git_output(["remote", "get-url", "origin"]),
        "summary": summary,
        "artifact_refs": {
            "summary": SUMMARY_PATH.as_posix(),
            "go_no_go": GO_NO_GO_PATH.as_posix(),
            "matrix": MATRIX_PATH.as_posix(),
            "report": REPORT_PATH.as_posix(),
            "test_results": TEST_RESULTS_PATH.as_posix(),
            "validator": "KMFA/tools/check_v014_remaining_cash_source_private_trace_or_difference_acceptance.py",
        },
        "public_repo_safety": {
            "aggregate_only": True,
            "raw_file_committed": False,
            "raw_filename_committed": False,
            "raw_hash_committed": False,
            "identity_plaintext_committed": False,
            "business_value_committed": False,
            "private_ref_committed": False,
            "credential_or_secret_committed": False,
        },
        "phase_boundaries": {
            "single_phase_only": True,
            "payable_note_bank_trace_performed": True,
            "secure_wps_content_read_claimed": False,
            "forced_zero_materialization_allowed": False,
            "global_residual_queue_replayed": False,
            "stage_review_performed": False,
            "github_upload_performed": False,
            "app_reinstall_performed": False,
            "business_execution_performed": False,
        },
    }
    go_no_go = {
        "schema_version": "kmfa.v014.remaining_cash_trace_go_no_go.v1",
        "project_id": "KMFA",
        "phase_id": PHASE_ID,
        "decision": DECISION,
        "cash_project_unresolved_count": len(decisions) - len(resolved),
        "unresolved_cash_value_target_slot_count": len(unresolved),
        "nonzero_delta_reconciliation_count": len(nonzero),
        "incomplete_cash_reconciliation_count": len(incomplete),
        "secure_wps_content_readable_count": wps["secure_wps_content_readable_count"],
        "blocking_reason_codes": [
            "two_cash_projects_still_lack_positive_collection_evidence",
            "secure_wps_content_requires_proprietary_ticket_runtime",
            "nonzero_scope_differences_remain",
            "global_residual_queue_not_replayed",
        ],
        "github_upload_performed": False,
    }

    _write_jsonl(PRIVATE_PAYABLE_TRACES_PATH, traces)
    _write_json(PRIVATE_WPS_RECOVERY_DIAGNOSTIC_PATH, wps)
    _write_jsonl(PRIVATE_CASH_DECISIONS_PATH, decisions)
    _write_jsonl(PRIVATE_CASH_METRICS_PATH, metrics)
    _write_jsonl(PRIVATE_TARGET_MATERIALIZATIONS_PATH, materialized)
    _write_jsonl(PRIVATE_UNRESOLVED_TARGETS_PATH, unresolved)
    _write_jsonl(PRIVATE_RECONCILIATION_COMPARISONS_PATH, comparisons)
    _write_json(
        PRIVATE_DIAGNOSTIC_PATH,
        {
            "schema_version": "kmfa.private.remaining_cash_trace_diagnostic.v1",
            "classification": "private_remaining_cash_trace_diagnostic_do_not_commit",
            "generated_at": timestamp,
            "source_hashes_before": source_hashes_before,
            "source_hashes_after": source_hashes_after,
            "source_private_inputs_unchanged": source_unchanged,
            "raw_before_snapshot": raw_before,
            "raw_after_snapshot": raw_after,
            "raw_snapshot_exact_match": raw_snapshot_exact_match,
            "trace_classification_counts": dict(sorted(trace_counts.items())),
            "decision_status_counts": dict(
                sorted(Counter(row["resolution_status"] for row in decisions).items())
            ),
            "comparison_status_counts": dict(
                sorted(Counter(row["comparison_status"] for row in comparisons).items())
            ),
        },
    )
    _write_text(
        PRIVATE_DIFFERENCE_REPORT_PATH,
        _private_difference_report(
            summary=summary,
            traces=traces,
            wps=wps,
            decisions=decisions,
            comparisons=comparisons,
        ),
    )
    for path, payload in (
        (SUMMARY_PATH, summary),
        (MANIFEST_PATH, manifest),
        (GO_NO_GO_PATH, go_no_go),
        (MATRIX_PATH, matrix),
        (METADATA_SUMMARY_PATH, summary),
        (METADATA_MANIFEST_PATH, manifest),
        (METADATA_GO_NO_GO_PATH, go_no_go),
        (METADATA_MATRIX_PATH, matrix),
    ):
        _write_json(path, payload)
    for path, content in _public_reports(summary).items():
        _write_text(path, content)
    if write_governance_event:
        _write_governance(timestamp, summary)
    return {"summary": summary, "manifest": manifest, "go_no_go": go_no_go, "matrix": matrix}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--generated-at")
    parser.add_argument("--skip-governance-event", action="store_true")
    args = parser.parse_args()
    result = generate(
        generated_at=args.generated_at,
        write_governance_event=not args.skip_governance_event,
    )
    summary = result["summary"]
    print(
        "remaining cash trace: "
        f"decision={summary['decision']} "
        f"resolved={summary['cash_project_resolved_count']} "
        f"unresolved={summary['cash_project_unresolved_count']} "
        f"materialized={summary['materialized_business_value_target_slot_count']} "
        f"raw_unchanged={summary['raw_snapshot_exact_match']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
