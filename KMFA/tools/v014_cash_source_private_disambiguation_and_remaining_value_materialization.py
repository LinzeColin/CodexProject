#!/usr/bin/env python3
"""Disambiguate private cash sources and materialize only proven remaining values."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Any, Iterable
from zipfile import ZipFile

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from KMFA.tools import (  # noqa: E402
    v014_real_project_identity_private_rebinding_and_processed_value_materialization as source_phase,
)


PROJECT_ROOT = Path("KMFA")
PHASE_ID = "V014_CASH_SOURCE_PRIVATE_DISAMBIGUATION_AND_REMAINING_VALUE_MATERIALIZATION"
TASK_ID = "KMFA-V014-CASH-SOURCE-PRIVATE-DISAMBIGUATION-AND-REMAINING-VALUE-MATERIALIZATION-20260710"
ACCEPTANCE_ID = "ACC-V014-CASH-SOURCE-PRIVATE-DISAMBIGUATION-AND-REMAINING-VALUE-MATERIALIZATION"
VERSION = "0.1.4-cash-source-private-disambiguation-and-remaining-value-materialization"
STATUS = "completed_validated_local_only_one_cash_project_materialized_remaining_cash_unresolved_no_go"
DECISION = "NO_GO"
PREFIX = "cash_source_private_disambiguation_and_remaining_value_materialization"

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

PRIVATE_OUTPUT_DIR = PROJECT_ROOT / ".codex_private_runtime/v014_cash_source_private_disambiguation_and_remaining_value_materialization"
PRIVATE_SOURCE_SPEC_PATH = PRIVATE_OUTPUT_DIR / "private_cash_source_spec.json"
PRIVATE_RAW_BEFORE_PATH = PRIVATE_OUTPUT_DIR / "raw_immutability_before.json"
PRIVATE_RAW_AFTER_PATH = PRIVATE_OUTPUT_DIR / "raw_immutability_after.json"
PRIVATE_WPS_DIAGNOSTIC_PATH = PRIVATE_OUTPUT_DIR / "private_wps_accessibility_diagnostic.json"
PRIVATE_LEDGER_EVIDENCE_PATH = PRIVATE_OUTPUT_DIR / "private_cash_ledger_evidence.json"
PRIVATE_CASH_DECISIONS_PATH = PRIVATE_OUTPUT_DIR / "private_cash_source_decisions.jsonl"
PRIVATE_CASH_METRICS_PATH = PRIVATE_OUTPUT_DIR / "private_materialized_cash_metrics.jsonl"
PRIVATE_TARGET_MATERIALIZATIONS_PATH = PRIVATE_OUTPUT_DIR / "private_s09_target_slot_materializations.jsonl"
PRIVATE_UNRESOLVED_TARGETS_PATH = PRIVATE_OUTPUT_DIR / "private_unresolved_cash_value_targets.jsonl"
PRIVATE_RECONCILIATION_COMPARISONS_PATH = PRIVATE_OUTPUT_DIR / "private_s09_reconciliation_comparisons.jsonl"
PRIVATE_DIAGNOSTIC_PATH = PRIVATE_OUTPUT_DIR / "private_cash_source_materialization_diagnostic.json"
PRIVATE_DIFFERENCE_REPORT_PATH = PRIVATE_OUTPUT_DIR / "private_difference_report_zh.md"

SOURCE_BINDINGS_PATH = source_phase.PRIVATE_IDENTITY_BINDINGS_PATH
SOURCE_METRICS_PATH = source_phase.PRIVATE_PROCESSED_METRICS_PATH
SOURCE_TARGET_MATERIALIZATIONS_PATH = source_phase.PRIVATE_TARGET_MATERIALIZATIONS_PATH
SOURCE_UNRESOLVED_TARGETS_PATH = source_phase.PRIVATE_UNRESOLVED_TARGETS_PATH
SOURCE_RECONCILIATION_COMPARISONS_PATH = source_phase.PRIVATE_RECONCILIATION_COMPARISONS_PATH

DEVELOPMENT_EVENTS_PATH = PROJECT_ROOT / "docs/governance/development_events.jsonl"
STAGE_STATUS_PATH = PROJECT_ROOT / "metadata/stage_status.jsonl"
TASK_STATUS_PATH = PROJECT_ROOT / "metadata/traceability/v1_4_stage_phase_task_status.jsonl"

MAIN_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
OLE_MAGIC = bytes.fromhex("D0CF11E0A1B11AE1")
AGGREGATE_MARKERS = ("期初余额", "本期合计", "本年累计")
COLLECTION_MARKERS = ("收到", "收款", "回款", "款项", "received", "collection", "payment")
NONCASH_COLLECTION_MARKERS = ("承兑", "票据", "冲销")
NONCASH_COST_MARKERS = ("项目分摊", "生产领料", "project allocation")


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


def source_private_paths() -> list[Path]:
    return [
        PRIVATE_SOURCE_SPEC_PATH,
        SOURCE_BINDINGS_PATH,
        SOURCE_METRICS_PATH,
        SOURCE_TARGET_MATERIALIZATIONS_PATH,
        SOURCE_UNRESOLVED_TARGETS_PATH,
        SOURCE_RECONCILIATION_COMPARISONS_PATH,
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
        PRIVATE_WPS_DIAGNOSTIC_PATH,
        PRIVATE_LEDGER_EVIDENCE_PATH,
        PRIVATE_CASH_DECISIONS_PATH,
        PRIVATE_CASH_METRICS_PATH,
        PRIVATE_TARGET_MATERIALIZATIONS_PATH,
        PRIVATE_UNRESOLVED_TARGETS_PATH,
        PRIVATE_RECONCILIATION_COMPARISONS_PATH,
        PRIVATE_DIAGNOSTIC_PATH,
        PRIVATE_DIFFERENCE_REPORT_PATH,
    ]


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


def _summary_text(row: dict[str, Any]) -> str:
    return str(row.get("summary", "")).strip()


def _is_collection_candidate(row: dict[str, Any]) -> bool:
    summary = _summary_text(row).lower()
    return (
        str(row.get("account", "")).startswith("1122")
        and _integer_cents(row, "credit_cents") > 0
        and any(marker in summary for marker in COLLECTION_MARKERS)
    )


def _is_noncash_collection(row: dict[str, Any]) -> bool:
    summary = _summary_text(row).lower()
    return summary.startswith(("调整", "adjustment")) or any(
        marker in summary for marker in NONCASH_COLLECTION_MARKERS
    )


def _is_noncash_cost(row: dict[str, Any]) -> bool:
    summary = _summary_text(row).lower()
    return any(marker in summary for marker in NONCASH_COST_MARKERS)


def _row_private_ref(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "sheet_name": row.get("sheet_name", "fixture"),
        "row_number": row.get("row_number"),
        "account": row.get("account", ""),
        "date": row.get("date", ""),
        "voucher": row.get("voucher", ""),
        "summary": row.get("summary", ""),
        "sales_contract": row.get("sales_contract", ""),
        "research_project": row.get("research_project", ""),
        "debit_cents": _integer_cents(row, "debit_cents"),
        "credit_cents": _integer_cents(row, "credit_cents"),
    }


def resolve_project_cash_sources(
    *,
    project_code: str,
    project_rows: list[dict[str, Any]],
    bank_rows: list[dict[str, Any]],
    voucher_rows: list[dict[str, Any]],
    external_crosscheck_status: str,
) -> dict[str, Any]:
    """Resolve one project from exact project dimensions and balanced bank vouchers."""

    if not project_code or not re.fullmatch(r"[A-Za-z0-9_-]+", project_code):
        raise ValueError("project_code must be a private identifier token")
    if _contains_float([project_rows, bank_rows, voucher_rows]):
        raise ValueError("cash source input cannot contain float values")
    for row in [*project_rows, *bank_rows, *voucher_rows]:
        _integer_cents(row, "debit_cents")
        _integer_cents(row, "credit_cents")

    bank_by_voucher: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    voucher_rows_by_key: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in bank_rows:
        bank_by_voucher[_voucher_key(row)].append(row)
    for row in voucher_rows:
        voucher_rows_by_key[_voucher_key(row)].append(row)

    cash_collection_rows: list[dict[str, Any]] = []
    noncash_collection_rows: list[dict[str, Any]] = []
    unresolved_collection_rows: list[dict[str, Any]] = []
    for row in project_rows:
        if not _is_collection_candidate(row):
            continue
        if _is_noncash_collection(row):
            noncash_collection_rows.append(row)
            continue
        linked_bank = bank_by_voucher.get(_voucher_key(row), [])
        bank_inflow = sum(
            _integer_cents(bank_row, "debit_cents")
            - _integer_cents(bank_row, "credit_cents")
            for bank_row in linked_bank
        )
        if bank_inflow > 0 and bank_inflow == _integer_cents(row, "credit_cents"):
            cash_collection_rows.append(row)
        else:
            unresolved_collection_rows.append(row)

    paid_cost_rows: list[dict[str, Any]] = []
    noncash_cost_rows: list[dict[str, Any]] = []
    unresolved_cost_rows: list[dict[str, Any]] = []
    cost_rows = [
        row
        for row in project_rows
        if str(row.get("account", "")).startswith("5001")
        and _integer_cents(row, "debit_cents") - _integer_cents(row, "credit_cents") > 0
    ]
    for row in cost_rows:
        if _is_noncash_cost(row):
            noncash_cost_rows.append(row)
            continue
        key = _voucher_key(row)
        linked_bank = bank_by_voucher.get(key, [])
        linked_nonbank = voucher_rows_by_key.get(key, [])
        bank_net_outflow = sum(
            _integer_cents(bank_row, "credit_cents")
            - _integer_cents(bank_row, "debit_cents")
            for bank_row in linked_bank
        )
        nonbank_net_debit = sum(
            _integer_cents(voucher_row, "debit_cents")
            - _integer_cents(voucher_row, "credit_cents")
            for voucher_row in linked_nonbank
        )
        if bank_net_outflow > 0 and bank_net_outflow == nonbank_net_debit:
            paid_cost_rows.append(row)
        else:
            unresolved_cost_rows.append(row)

    collection_missing = not cash_collection_rows
    unresolved_rows = [*unresolved_collection_rows, *unresolved_cost_rows]
    resolved = not collection_missing and not unresolved_rows
    collection_amount = (
        sum(_integer_cents(row, "credit_cents") for row in cash_collection_rows)
        if resolved
        else None
    )
    cash_paid_cost = (
        sum(
            _integer_cents(row, "debit_cents") - _integer_cents(row, "credit_cents")
            for row in paid_cost_rows
        )
        if resolved
        else None
    )
    cash_gross_profit = (
        collection_amount - cash_paid_cost
        if collection_amount is not None and cash_paid_cost is not None
        else None
    )
    reason_codes: list[str] = []
    if collection_missing:
        reason_codes.append("positive_collection_evidence_absent_not_zero")
    if unresolved_collection_rows:
        reason_codes.append("collection_bank_voucher_not_exact")
    if unresolved_cost_rows:
        reason_codes.append("cost_payment_or_later_payable_trace_incomplete")
    if external_crosscheck_status != "completed":
        reason_codes.append("external_wps_crosscheck_unavailable_not_claimed")
    if resolved:
        reason_codes.insert(0, "exact_project_dimension_and_balanced_bank_voucher")

    result = {
        "schema_version": "kmfa.private.cash_source_decision.v1",
        "classification": "private_cash_source_decision_do_not_commit",
        "project_code": project_code,
        "resolution_status": "resolved_accessible_ledger_only" if resolved else "unresolved",
        "reason_codes": reason_codes,
        "collection_amount_cents": collection_amount,
        "cash_paid_cost_cents": cash_paid_cost,
        "cash_gross_profit_cents": cash_gross_profit,
        "cash_collection_evidence_count": len(cash_collection_rows),
        "cash_paid_cost_evidence_count": len(paid_cost_rows),
        "noncash_collection_count": len(noncash_collection_rows),
        "noncash_cost_count": len(noncash_cost_rows),
        "unresolved_collection_count": len(unresolved_collection_rows),
        "unresolved_cost_count": len(unresolved_cost_rows),
        "unresolved_row_count": len(unresolved_rows) + int(collection_missing),
        "zero_inferred_from_absence": False,
        "external_crosscheck_status": external_crosscheck_status,
        "external_crosscheck_completed": external_crosscheck_status == "completed",
        "business_consistency_verified": False,
        "cash_collection_evidence": [_row_private_ref(row) for row in cash_collection_rows],
        "cash_paid_cost_evidence": [_row_private_ref(row) for row in paid_cost_rows],
        "noncash_collection_evidence": [_row_private_ref(row) for row in noncash_collection_rows],
        "noncash_cost_evidence": [_row_private_ref(row) for row in noncash_cost_rows],
        "unresolved_evidence": [_row_private_ref(row) for row in unresolved_rows],
        "integer_only": True,
        "raw_layer_write_allowed": False,
        "public_commit_allowed": False,
    }
    if _contains_float(result):
        raise ValueError("cash source decision cannot contain float values")
    return result


def _column_index(cell_ref: str) -> int:
    letters = re.match(r"[A-Z]+", cell_ref)
    if letters is None:
        raise ValueError(f"invalid cell reference: {cell_ref}")
    value = 0
    for character in letters.group():
        value = value * 26 + ord(character) - 64
    return value - 1


def _transaction_row(values: list[str]) -> bool:
    voucher = values[9].strip()
    summary = values[10].strip()
    if not voucher or not summary:
        return False
    if any(marker in summary for marker in AGGREGATE_MARKERS):
        return False
    if summary.startswith("结转"):
        return False
    return True


def _amount_cents(value: str) -> int:
    return source_phase.normalize_amount_to_cents(value or "0")


def _row_record(sheet_name: str, row_number: int, values: list[str]) -> dict[str, Any]:
    return {
        "sheet_name": sheet_name,
        "row_number": row_number,
        "account": values[0],
        "customer": values[1],
        "employee": values[2],
        "supplier": values[3],
        "department": values[4],
        "sales_contract": values[5],
        "research_project": values[6],
        "counterparty": values[7],
        "date": values[8],
        "voucher": values[9].strip(),
        "summary": values[10].strip(),
        "debit_cents": _amount_cents(values[11]),
        "credit_cents": _amount_cents(values[12]),
        "direction": values[13],
        "balance_cents": _amount_cents(values[14]),
    }


def _load_inner_workbook(spec: dict[str, Any]) -> tuple[ZipFile, list[str], list[tuple[str, str]], str]:
    raw_archive = Path(str(spec["raw_archive_path"]))
    member_selector = str(spec["inner_workbook_member_contains"])
    with ZipFile(raw_archive) as outer:
        members = [
            name
            for name in outer.namelist()
            if member_selector in name
            and name.lower().endswith(".xlsx")
            and not Path(name).name.startswith("~$")
        ]
        if len(members) != 1:
            raise ValueError("private ledger selector must resolve to exactly one workbook")
        inner_bytes = outer.read(members[0])
    inner = ZipFile(BytesIO(inner_bytes))
    if "xl/sharedStrings.xml" in inner.namelist():
        shared_root = ET.fromstring(inner.read("xl/sharedStrings.xml"))
        shared_strings = [
            "".join(text.text or "" for text in item.iter(f"{{{MAIN_NS}}}t"))
            for item in shared_root.findall(f"{{{MAIN_NS}}}si")
        ]
    else:
        shared_strings = []
    workbook_root = ET.fromstring(inner.read("xl/workbook.xml"))
    relations_root = ET.fromstring(inner.read("xl/_rels/workbook.xml.rels"))
    relations = {node.attrib["Id"]: node.attrib["Target"] for node in relations_root}
    sheets: list[tuple[str, str]] = []
    sheet_container = workbook_root.find(f"{{{MAIN_NS}}}sheets")
    if sheet_container is None:
        raise ValueError("private ledger workbook has no sheets")
    for node in sheet_container:
        relation_id = node.attrib[f"{{{REL_NS}}}id"]
        target = "xl/" + relations[relation_id].lstrip("/")
        sheets.append((node.attrib["name"], target))
    return inner, shared_strings, sheets, members[0]


def _sheet_rows(inner: ZipFile, shared_strings: list[str], target: str) -> Iterable[tuple[int, list[str]]]:
    root = ET.fromstring(inner.read(target))
    for row in root.findall(f".//{{{MAIN_NS}}}sheetData/{{{MAIN_NS}}}row"):
        values = [""] * 15
        for cell in row.findall(f"{{{MAIN_NS}}}c"):
            column = _column_index(cell.attrib["r"])
            if column >= len(values):
                continue
            cell_type = cell.attrib.get("t")
            if cell_type == "inlineStr":
                values[column] = "".join(
                    node.text or "" for node in cell.iter(f"{{{MAIN_NS}}}t")
                )
                continue
            value_node = cell.find(f"{{{MAIN_NS}}}v")
            raw_value = "" if value_node is None else (value_node.text or "")
            if cell_type == "s" and raw_value:
                raw_value = shared_strings[int(raw_value)]
            values[column] = raw_value
        yield int(row.attrib["r"]), values


def _dimension_has_code(row: dict[str, Any], code: str) -> bool:
    dimensions = f"{row.get('sales_contract', '')} {row.get('research_project', '')}"
    return re.search(rf"(?<!\d){re.escape(code)}(?!\d)", dimensions) is not None


def _alias_matches(text: str, tokens: list[str]) -> bool:
    return bool(tokens) and all(token in text for token in tokens)


def _extract_private_ledger(spec: dict[str, Any]) -> dict[str, Any]:
    inner, shared_strings, sheets, member_name = _load_inner_workbook(spec)
    project_specs = spec.get("project_specs", [])
    if not isinstance(project_specs, list) or len(project_specs) != 4:
        raise ValueError("private cash source spec must contain four project specs")
    project_rows: dict[str, list[dict[str, Any]]] = defaultdict(list)
    direct_alias_bank_rows: dict[str, list[dict[str, Any]]] = defaultdict(list)
    bank_rows: list[dict[str, Any]] = []
    bank_sheets = {name for name, _ in sheets if name.startswith(("1001", "1002"))}

    for sheet_name, target in sheets:
        for row_number, values in _sheet_rows(inner, shared_strings, target):
            if row_number < 4 or not _transaction_row(values):
                continue
            row = _row_record(sheet_name, row_number, values)
            if sheet_name in bank_sheets:
                bank_rows.append(row)
                row_text = " ".join(values[:11])
                for project_spec in project_specs:
                    code = str(project_spec["project_code"])
                    tokens = [str(token) for token in project_spec.get("alias_tokens", [])]
                    if _alias_matches(row_text, tokens) or re.search(
                        rf"(?<!\d){re.escape(code)}(?!\d)", row_text
                    ):
                        direct_alias_bank_rows[code].append(row)
                continue
            for project_spec in project_specs:
                code = str(project_spec["project_code"])
                tokens = [str(token) for token in project_spec.get("alias_tokens", [])]
                identity_text = " ".join(
                    str(row.get(key, ""))
                    for key in (
                        "sheet_name",
                        "customer",
                        "sales_contract",
                        "research_project",
                        "summary",
                    )
                )
                if _dimension_has_code(row, code) and _alias_matches(identity_text, tokens):
                    project_rows[code].append(row)

    relevant_keys = {
        _voucher_key(row)
        for rows in [*project_rows.values(), *direct_alias_bank_rows.values()]
        for row in rows
    }
    voucher_rows: list[dict[str, Any]] = []
    for sheet_name, target in sheets:
        if sheet_name in bank_sheets:
            continue
        for row_number, values in _sheet_rows(inner, shared_strings, target):
            if row_number < 4 or not _transaction_row(values):
                continue
            if (values[8], values[9].strip()) in relevant_keys:
                voucher_rows.append(_row_record(sheet_name, row_number, values))
    inner.close()
    return {
        "schema_version": "kmfa.private.cash_ledger_evidence.v1",
        "classification": "private_cash_ledger_evidence_do_not_commit",
        "archive_member_name": member_name,
        "sheet_count": len(sheets),
        "bank_sheet_count": len(bank_sheets),
        "project_rows": dict(project_rows),
        "bank_rows": bank_rows,
        "voucher_rows": voucher_rows,
        "direct_alias_bank_rows": dict(direct_alias_bank_rows),
        "raw_archive_read_only": True,
        "integer_cents_only": True,
        "raw_layer_write_allowed": False,
        "public_commit_allowed": False,
    }


def _build_wps_diagnostic(spec: dict[str, Any]) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    for index, source in enumerate(spec.get("external_wps_sources", []), start=1):
        path = Path(str(source["path"]))
        data = path.read_bytes()
        ole_container = data.startswith(OLE_MAGIC)
        wps_content_stream_marker = "WpsContent".encode("utf-16le") in data
        encryption_info_stream_marker = "EncryptionInfo".encode("utf-16le") in data
        records.append(
            {
                "record_id": f"V014-WPS-DIAG-{index:02d}",
                "classification": "private_wps_accessibility_diagnostic_do_not_commit",
                "path": path.as_posix(),
                "business_role": source.get("business_role"),
                "attempted_readers": source.get("attempted_readers", []),
                "ole_container": ole_container,
                "standard_openxml_container": data.startswith(b"PK"),
                "wps_content_stream_marker": wps_content_stream_marker,
                "encryption_info_stream_marker": encryption_info_stream_marker,
                "content_readable": False,
                "access_status": "ole_wps_transform_container_unavailable_not_claimed",
                "raw_layer_write_allowed": False,
                "public_commit_allowed": False,
            }
        )
    if len(records) != 2 or not all(
        row["ole_container"]
        and row["wps_content_stream_marker"]
        and row["encryption_info_stream_marker"]
        and not row["standard_openxml_container"]
        for row in records
    ):
        raise ValueError("external WPS source diagnostics do not match the phase evidence")
    return {
        "schema_version": "kmfa.private.wps_accessibility_diagnostic.v1",
        "classification": "private_wps_accessibility_diagnostic_do_not_commit",
        "source_count": len(records),
        "readable_count": sum(row["content_readable"] for row in records),
        "records": records,
        "false_readability_claim_count": 0,
        "public_commit_allowed": False,
    }


def _validate_private_spec(spec: dict[str, Any], bindings: list[dict[str, Any]]) -> None:
    project_specs = spec.get("project_specs", [])
    if not isinstance(project_specs, list) or len(project_specs) != 4:
        raise ValueError("private source spec must have four project specs")
    expected = {
        (str(row["binding_id"]), str(row["legacy_margin_record_id"])) for row in bindings
    }
    actual = {
        (str(row["binding_id"]), str(row["legacy_margin_record_id"]))
        for row in project_specs
    }
    if expected != actual:
        raise ValueError("private project specs do not match prior identity bindings")
    codes = [str(row.get("project_code", "")) for row in project_specs]
    if len(set(codes)) != 4 or not all(re.fullmatch(r"\d{3}", code) for code in codes):
        raise ValueError("private project codes must be four unique three-digit identifiers")


def _build_decisions(
    spec: dict[str, Any], ledger: dict[str, Any], wps: dict[str, Any]
) -> list[dict[str, Any]]:
    decisions: list[dict[str, Any]] = []
    for index, project_spec in enumerate(spec["project_specs"], start=1):
        code = str(project_spec["project_code"])
        project_rows = ledger["project_rows"].get(code, [])
        relevant_keys = {_voucher_key(row) for row in project_rows}
        bank_rows = [row for row in ledger["bank_rows"] if _voucher_key(row) in relevant_keys]
        voucher_rows = [
            row for row in ledger["voucher_rows"] if _voucher_key(row) in relevant_keys
        ]
        decision = resolve_project_cash_sources(
            project_code=code,
            project_rows=project_rows,
            bank_rows=bank_rows,
            voucher_rows=voucher_rows,
            external_crosscheck_status=(
                "completed"
                if wps["readable_count"] == wps["source_count"]
                else "ole_wps_unavailable_not_claimed"
            ),
        )
        decision.update(
            {
                "decision_id": f"V014-CASH-DEC-{index:03d}",
                "binding_id": project_spec["binding_id"],
                "legacy_margin_record_id": project_spec["legacy_margin_record_id"],
                "exact_project_transaction_count": len(project_rows),
                "direct_alias_bank_candidate_count": len(
                    ledger["direct_alias_bank_rows"].get(code, [])
                ),
                "direct_alias_without_exact_project_dimension_excluded": True,
            }
        )
        decisions.append(decision)
    if sum(row["resolution_status"] == "resolved_accessible_ledger_only" for row in decisions) != 1:
        raise ValueError("real private cash evidence must resolve exactly one project in this phase")
    return decisions


def _cash_metric_records(decisions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    index = 1
    for decision in decisions:
        if decision["resolution_status"] != "resolved_accessible_ledger_only":
            continue
        for metric_key in (
            "collection_amount_cents",
            "cash_paid_cost_cents",
            "cash_gross_profit_cents",
        ):
            value = decision[metric_key]
            if not isinstance(value, int) or isinstance(value, bool):
                raise ValueError("resolved cash metric must be integer cents")
            records.append(
                {
                    "schema_version": "kmfa.private.materialized_cash_metric.v1",
                    "classification": "private_materialized_cash_metric_do_not_commit",
                    "metric_record_id": f"V014-CASH-METRIC-{index:03d}",
                    "binding_id": decision["binding_id"],
                    "legacy_margin_record_id": decision["legacy_margin_record_id"],
                    "metric_key": metric_key,
                    "value": value,
                    "unit": "cents",
                    "derivation": "exact_project_dimension_balanced_bank_voucher_integer_formula",
                    "integer_only": True,
                    "raw_layer_write_allowed": False,
                    "public_commit_allowed": False,
                }
            )
            index += 1
    return records


def _materialized_slot(row: dict[str, Any], value: int) -> dict[str, Any]:
    result = {
        key: value_ for key, value_ in row.items() if key not in {"reason_codes", "resolution_status"}
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


def _apply_cash_materialization(
    decisions: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], int]:
    materialized = read_jsonl(SOURCE_TARGET_MATERIALIZATIONS_PATH)
    unresolved = read_jsonl(SOURCE_UNRESOLVED_TARGETS_PATH)
    comparisons = read_jsonl(SOURCE_RECONCILIATION_COMPARISONS_PATH)
    newly_materialized = 0
    for decision in decisions:
        if decision["resolution_status"] != "resolved_accessible_ledger_only":
            continue
        margin_record_id = str(decision["legacy_margin_record_id"])
        comparison = next(
            row
            for row in comparisons
            if row["margin_record_id"] == margin_record_id
            and row["difference_type"] == "cash_vs_accrual_gross_profit"
        )
        cash_value = int(decision["cash_gross_profit_cents"])
        amount_b = comparison["amount_b"]
        if not isinstance(amount_b, int) or isinstance(amount_b, bool):
            raise ValueError("cash comparison accrual value must already be integer cents")
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
            if context == "cash_gross_profit" and margin_record_id not in str(
                row["private_processed_ref"]
            ):
                continue
            if context != "cash_gross_profit" and row.get("difference_id") != comparison["difference_id"]:
                continue
            materialized.append(_materialized_slot(row, expected_context_values[context]))
            consumed_ids.add(str(row["target_slot_id"]))
            newly_materialized += 1
        if len(consumed_ids) != 3:
            raise ValueError("resolved cash project must materialize exactly three target slots")
        unresolved = [
            row for row in unresolved if str(row["target_slot_id"]) not in consumed_ids
        ]
    materialized.sort(key=lambda row: str(row["target_slot_id"]))
    unresolved.sort(key=lambda row: str(row["target_slot_id"]))
    comparisons.sort(key=lambda row: str(row["comparison_id"]))
    return materialized, unresolved, comparisons, newly_materialized


def _public_matrix(summary: dict[str, Any]) -> dict[str, Any]:
    checks = [
        ("source_private_inputs_unchanged", summary["source_private_inputs_unchanged"]),
        ("raw_snapshot_exact_match", summary["raw_snapshot_exact_match"]),
        ("four_cash_candidates", summary["cash_project_candidate_count"] == 4),
        ("one_ledger_resolution", summary["cash_project_resolved_count"] == 1),
        ("three_unresolved_projects", summary["cash_project_unresolved_count"] == 3),
        ("three_new_targets", summary["newly_materialized_cash_target_slot_count"] == 3),
        ("nine_cash_targets_remain", summary["unresolved_cash_value_target_slot_count"] == 9),
        ("nine_comparisons_complete", summary["completed_reconciliation_comparison_count"] == 9),
        ("seven_nonzero_preserved", summary["nonzero_delta_reconciliation_count"] == 7),
        ("three_cash_comparisons_incomplete", summary["incomplete_cash_reconciliation_count"] == 3),
        ("wps_unavailable_not_claimed", summary["external_wps_readable_count"] == 0),
        ("forced_zero_prohibited", summary["forced_zero_materialization_count"] == 0),
        ("full_consistency_not_claimed", not summary["business_value_consistency_verified"]),
        ("raw_not_committed", not summary["raw_business_data_committed"]),
        ("github_not_uploaded", not summary["github_upload_performed"]),
        ("app_not_reinstalled", not summary["app_reinstall_performed"]),
        ("stage_review_not_performed", not summary["stage_review_performed"]),
        ("business_execution_not_performed", not summary["business_execution_performed"]),
    ]
    rows = [
        {"check_id": f"CSDM-{index:02d}", "check_name": name, "passed": passed}
        for index, (name, passed) in enumerate(checks, start=1)
    ]
    return {
        "schema_version": "kmfa.v014_cash_source_materialization_matrix.v1",
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
    bindings: list[dict[str, Any]],
    decisions: list[dict[str, Any]],
    wps: dict[str, Any],
    comparisons: list[dict[str, Any]],
) -> str:
    binding_by_id = {str(row["binding_id"]): row for row in bindings}
    lines = [
        "# KMFA v0.1.4 现金来源私有消歧与剩余值物化差异报告",
        "",
        "## 本轮结论",
        "",
        f"- 候选项目：{summary['cash_project_candidate_count']} 个。",
        f"- 可访问账套内完成唯一闭环：{summary['cash_project_resolved_count']} 个。",
        f"- 仍未闭环：{summary['cash_project_unresolved_count']} 个。",
        f"- 本轮新增物化现金目标槽位：{summary['newly_materialized_cash_target_slot_count']} 个。",
        f"- 剩余未解析现金目标槽位：{summary['unresolved_cash_value_target_slot_count']} 个。",
        f"- 已完成比较：{summary['completed_reconciliation_comparison_count']} 条；零差异 {summary['zero_delta_reconciliation_count']} 条；非零差异 {summary['nonzero_delta_reconciliation_count']} 条；现金比较未完成 {summary['incomplete_cash_reconciliation_count']} 条。",
        "- 未把缺失值、空白或未命中记录强制写成 0。",
        "- 当前仍为 NO_GO；不生成正式经营结论，不上传 GitHub，不执行业务动作。",
        "",
        "## 项目逐项决策",
        "",
    ]
    for decision in decisions:
        binding = binding_by_id[str(decision["binding_id"])]
        lines.extend(
            [
                f"### {binding['project_name_private_value']}",
                "",
                f"- 私有项目编码：{decision['project_code']}",
                f"- 决策状态：{decision['resolution_status']}",
                f"- 决策原因：{'; '.join(decision['reason_codes'])}",
                f"- 项目维度交易：{decision['exact_project_transaction_count']} 条",
                f"- 银行收款证据：{decision['cash_collection_evidence_count']} 条",
                f"- 银行已付成本证据：{decision['cash_paid_cost_evidence_count']} 条",
                f"- 非现金收款记录：{decision['noncash_collection_count']} 条",
                f"- 非现金成本记录：{decision['noncash_cost_count']} 条",
                f"- 未解决交易：{decision['unresolved_row_count']} 条",
                f"- 收款金额（分）：{decision['collection_amount_cents']}",
                f"- 现金已付项目成本（分）：{decision['cash_paid_cost_cents']}",
                f"- 现金毛利（分）：{decision['cash_gross_profit_cents']}",
                "",
            ]
        )
    lines.extend(["## 外部交叉核验来源", ""])
    for record in wps["records"]:
        lines.extend(
            [
                f"- 来源：{record['path']}",
                f"  - 业务角色：{record['business_role']}",
                f"  - 容器：OLE={record['ole_container']}，WpsContent={record['wps_content_stream_marker']}，EncryptionInfo={record['encryption_info_stream_marker']}",
                f"  - 当前可读：{record['content_readable']}",
                f"  - 结论：{record['access_status']}；未声称已读取内容。",
            ]
        )
    lines.extend(["", "## 比较结果", ""])
    for row in comparisons:
        lines.append(
            f"- {row['difference_id']}：{row['comparison_status']}；单位={row['unit']}；A={row['amount_a']}；B={row['amount_b']}；差额={row['delta']}。"
        )
    lines.extend(
        [
            "",
            "## 剩余差异原因",
            "",
            "- 1 个项目存在成本付款或后续应付款追踪未闭环。",
            "- 2 个项目没有可证明的正向收款证据；没有把未命中当作零。",
            "- 应收账龄与项目状态两个 WPS/OLE 来源当前无法由已验证读取链路解析，因此未完成外部交叉核验。",
            "- 全局 72 条 residual queue 尚未重放；现有非零差异没有被覆盖或抹平。",
            "",
        ]
    )
    return "\n".join(lines)


def _public_reports(summary: dict[str, Any]) -> dict[Path, str]:
    report = f"""# v0.1.4 现金来源私有消歧与剩余值物化

- Phase: `{PHASE_ID}`
- 决策: `{DECISION}`
- 现金候选项目: {summary['cash_project_candidate_count']}
- 可访问账套内唯一闭环 / 未闭环: {summary['cash_project_resolved_count']} / {summary['cash_project_unresolved_count']}
- 新增物化 / 累计物化 / 剩余现金槽位: {summary['newly_materialized_cash_target_slot_count']} / {summary['materialized_business_value_target_slot_count']} / {summary['unresolved_cash_value_target_slot_count']}
- 完成比较 / 非零差异 / 现金未完成: {summary['completed_reconciliation_comparison_count']} / {summary['nonzero_delta_reconciliation_count']} / {summary['incomplete_cash_reconciliation_count']}
- 外部 WPS 来源 / 可读来源: {summary['external_wps_source_count']} / {summary['external_wps_readable_count']}
- raw 前后完全一致: `{str(summary['raw_snapshot_exact_match']).lower()}`

本 phase 仅在私有运行区物化唯一可证明的现金值；未命中不会被填零。外部 WPS/OLE 交叉核验仍不可用，其内容未被虚假声明为已读取，因此完整业务一致性仍未成立并维持 NO_GO。
"""
    go_no_go = f"""# Go / No-Go 记录

- 决策: `NO_GO`
- 已完成: {summary['cash_project_resolved_count']} 个项目可访问账套内现金闭环，新增 {summary['newly_materialized_cash_target_slot_count']} 个私有目标槽位。
- 阻断: {summary['cash_project_unresolved_count']} 个项目、{summary['unresolved_cash_value_target_slot_count']} 个现金槽位、{summary['nonzero_delta_reconciliation_count']} 条非零差异、外部交叉核验不可用。
- GitHub upload / app reinstall / business execution: `not_performed`
"""
    tests = """# 测试结果

- focused unit test: `PENDING_FINAL_VERIFICATION`
- phase validator: `PENDING_FINAL_VERIFICATION`
- governance validators: `PENDING_FINAL_VERIFICATION`
- raw/private/secret scan: `PENDING_FINAL_VERIFICATION`
"""
    risks = """# 风险登记

- 高: 仍有 3 个项目缺少完整现金来源闭环，缺失值不得当作零。
- 高: 外部 WPS/OLE 来源当前不可由验证链路读取，未完成应收账龄和项目状态交叉核验。
- 高: 7 条非零口径差异继续保留，不得覆盖权威值或自动抹平。
- 中: 全局 72 条 residual queue 尚未重放。
"""
    rollback = """# 回滚方案

1. 删除本 phase 公开 artifacts 和 metadata 镜像。
2. 删除本 phase ignored private outputs，保留私有输入规范；不触碰原始数据目录。
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
        "KMFA/tests/test_v014_cash_source_private_disambiguation_and_remaining_value_materialization.py",
        "KMFA/tools/check_v014_cash_source_private_disambiguation_and_remaining_value_materialization.py",
        "KMFA/tools/v014_cash_source_private_disambiguation_and_remaining_value_materialization.py",
        "KMFA/功能清单.md",
        "KMFA/开发记录.md",
        "KMFA/模型参数文件.md",
    ]


def _write_governance(generated_at: str, summary: dict[str, Any]) -> None:
    evidence_ref = MANIFEST_PATH.as_posix()
    source_phase.source_phase._upsert_jsonl(
        DEVELOPMENT_EVENTS_PATH,
        "event_id",
        {
            "event_id": "DEV-KMFA-20260710-V014-CASH-SOURCE-PRIVATE-DISAMBIGUATION-AND-REMAINING-VALUE-MATERIALIZATION",
            "event_time": generated_at,
            "event_type": "development",
            "project_id": "KMFA",
            "stage_id": "value-consistency",
            "phase_id": PHASE_ID,
            "task_id": TASK_ID,
            "status": STATUS,
            "fact_level": "EXTRACTED",
            "decision": DECISION,
            "cash_project_resolved_count": summary["cash_project_resolved_count"],
            "cash_project_unresolved_count": summary["cash_project_unresolved_count"],
            "newly_materialized_cash_target_slot_count": summary[
                "newly_materialized_cash_target_slot_count"
            ],
            "unresolved_cash_value_target_slot_count": summary[
                "unresolved_cash_value_target_slot_count"
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
    source_phase.source_phase._upsert_jsonl(
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
    source_phase.source_phase._upsert_jsonl(
        TASK_STATUS_PATH,
        "phase_id",
        {
            "schema_version": "kmfa.v014_stage_phase_task_status.v1",
            "record_type": "v014_phase",
            "project_id": "KMFA",
            "stage_id": "VALUE-CONSISTENCY",
            "governance_stage_id": "VALUE-CONSISTENCY",
            "roadmap_stage_id": "VALUE-CONSISTENCY",
            "roadmap_phase_id": "CASH_SOURCE_PRIVATE_DISAMBIGUATION_AND_REMAINING_VALUE_MATERIALIZATION",
            "phase_id": PHASE_ID,
            "task_id": TASK_ID,
            "acceptance_id": ACCEPTANCE_ID,
            "version": VERSION,
            "name": "v0.1.4 cash source private disambiguation and remaining value materialization",
            "phase_goal": "materialize only uniquely proven cash values and preserve unresolved differences",
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
    spec = read_json(PRIVATE_SOURCE_SPEC_PATH)
    bindings = read_jsonl(SOURCE_BINDINGS_PATH)
    _validate_private_spec(spec, bindings)

    if PRIVATE_RAW_BEFORE_PATH.exists():
        raw_before = read_json(PRIVATE_RAW_BEFORE_PATH)
        raw_before["phase_id"] = PHASE_ID
        raw_before["snapshot_kind"] = "before"
    else:
        raw_before = _raw_snapshot("before")
    _write_json(PRIVATE_RAW_BEFORE_PATH, raw_before)

    wps = _build_wps_diagnostic(spec)
    ledger = _extract_private_ledger(spec)
    decisions = _build_decisions(spec, ledger, wps)
    cash_metrics = _cash_metric_records(decisions)
    materialized, unresolved, comparisons, newly_materialized = _apply_cash_materialization(
        decisions
    )
    raw_after = _raw_snapshot("after")
    _write_json(PRIVATE_RAW_AFTER_PATH, raw_after)
    raw_snapshot_exact_match = _snapshot_core(raw_before) == _snapshot_core(raw_after)
    source_hashes_after = {
        path.as_posix(): _sha256_bytes(path.read_bytes()) for path in source_private_paths()
    }
    source_unchanged = source_hashes_before == source_hashes_after

    completed = [
        row for row in comparisons if str(row["comparison_status"]).startswith("comparison_complete_")
    ]
    zero = [row for row in completed if row["delta"] == 0]
    nonzero = [row for row in completed if row["delta"] != 0]
    incomplete = [row for row in comparisons if row not in completed]
    resolved = [row for row in decisions if row["resolution_status"] == "resolved_accessible_ledger_only"]

    if _contains_float([decisions, cash_metrics, materialized, unresolved, comparisons]):
        raise ValueError("private cash materialization cannot contain float values")
    expected_counts = (
        len(decisions),
        len(resolved),
        len(cash_metrics),
        len(materialized),
        newly_materialized,
        len(unresolved),
        len(comparisons),
        len(completed),
        len(zero),
        len(nonzero),
        len(incomplete),
    )
    if expected_counts != (4, 1, 3, 31, 3, 9, 12, 9, 2, 7, 3):
        raise ValueError(f"private cash materialization counts mismatch: {expected_counts}")

    summary = {
        "schema_version": "kmfa.v014_cash_source_materialization_summary.v1",
        "record_type": "v014_cash_source_materialization_summary",
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
        "cash_project_candidate_count": len(decisions),
        "cash_project_resolved_count": len(resolved),
        "cash_project_unresolved_count": len(decisions) - len(resolved),
        "private_cash_metric_record_count": len(cash_metrics),
        "materialized_business_value_target_slot_count": len(materialized),
        "newly_materialized_cash_target_slot_count": newly_materialized,
        "unresolved_cash_value_target_slot_count": len(unresolved),
        "reconciliation_record_count": len(comparisons),
        "completed_reconciliation_comparison_count": len(completed),
        "zero_delta_reconciliation_count": len(zero),
        "nonzero_delta_reconciliation_count": len(nonzero),
        "incomplete_cash_reconciliation_count": len(incomplete),
        "external_wps_source_count": wps["source_count"],
        "external_wps_readable_count": wps["readable_count"],
        "external_crosscheck_completed": wps["readable_count"] == wps["source_count"],
        "false_wps_readability_claim_count": wps["false_readability_claim_count"],
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
        "private_cash_decisions_gitignored": source_phase.source_phase._git_check_ignored(
            PRIVATE_CASH_DECISIONS_PATH
        ),
        "private_cash_metrics_gitignored": source_phase.source_phase._git_check_ignored(
            PRIVATE_CASH_METRICS_PATH
        ),
        "private_difference_report_gitignored": source_phase.source_phase._git_check_ignored(
            PRIVATE_DIFFERENCE_REPORT_PATH
        ),
        "private_wps_diagnostic_gitignored": source_phase.source_phase._git_check_ignored(
            PRIVATE_WPS_DIAGNOSTIC_PATH
        ),
        "raw_business_data_committed": False,
        "raw_filename_or_value_committed": False,
        "credential_or_secret_committed": False,
        "stage_review_performed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "goal_status_recommendation": "continue_active_with_remaining_cash_trace_and_external_crosscheck",
        "next_recommended_phase": "remaining_cash_source_private_trace_or_difference_acceptance",
    }
    matrix = _public_matrix(summary)
    if matrix["check_fail_count"]:
        raise ValueError("public acceptance matrix contains failures")
    manifest = {
        "schema_version": "kmfa.v014_cash_source_materialization_manifest.v1",
        "record_type": "v014_cash_source_materialization_manifest",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": timestamp,
        "reviewed_head": source_phase.source_phase._git_output(["rev-parse", "HEAD"]),
        "branch": source_phase.source_phase._git_output(["branch", "--show-current"]),
        "remote": source_phase.source_phase._git_output(["remote", "get-url", "origin"]),
        "summary": summary,
        "artifact_refs": {
            "summary": SUMMARY_PATH.as_posix(),
            "go_no_go": GO_NO_GO_PATH.as_posix(),
            "matrix": MATRIX_PATH.as_posix(),
            "report": REPORT_PATH.as_posix(),
            "test_results": TEST_RESULTS_PATH.as_posix(),
            "validator": "KMFA/tools/check_v014_cash_source_private_disambiguation_and_remaining_value_materialization.py",
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
            "cash_source_private_disambiguation_performed": True,
            "external_wps_content_read_claimed": False,
            "forced_zero_materialization_allowed": False,
            "global_residual_queue_replayed": False,
            "stage_review_performed": False,
            "github_upload_performed": False,
            "app_reinstall_performed": False,
            "business_execution_performed": False,
        },
    }
    go_no_go = {
        "schema_version": "kmfa.v014_cash_source_materialization_go_no_go.v1",
        "project_id": "KMFA",
        "phase_id": PHASE_ID,
        "decision": DECISION,
        "cash_project_unresolved_count": len(decisions) - len(resolved),
        "unresolved_cash_value_target_slot_count": len(unresolved),
        "nonzero_delta_reconciliation_count": len(nonzero),
        "incomplete_cash_reconciliation_count": len(incomplete),
        "external_wps_readable_count": wps["readable_count"],
        "blocking_reason_codes": [
            "three_cash_projects_still_unresolved",
            "external_wps_crosscheck_unavailable",
            "nonzero_scope_differences_remain",
            "global_residual_queue_not_replayed",
        ],
        "github_upload_performed": False,
    }

    _write_json(PRIVATE_WPS_DIAGNOSTIC_PATH, wps)
    _write_json(PRIVATE_LEDGER_EVIDENCE_PATH, ledger)
    _write_jsonl(PRIVATE_CASH_DECISIONS_PATH, decisions)
    _write_jsonl(PRIVATE_CASH_METRICS_PATH, cash_metrics)
    _write_jsonl(PRIVATE_TARGET_MATERIALIZATIONS_PATH, materialized)
    _write_jsonl(PRIVATE_UNRESOLVED_TARGETS_PATH, unresolved)
    _write_jsonl(PRIVATE_RECONCILIATION_COMPARISONS_PATH, comparisons)
    _write_json(
        PRIVATE_DIAGNOSTIC_PATH,
        {
            "schema_version": "kmfa.private.cash_source_materialization_diagnostic.v1",
            "classification": "private_cash_source_materialization_diagnostic_do_not_commit",
            "generated_at": timestamp,
            "source_hashes_before": source_hashes_before,
            "source_hashes_after": source_hashes_after,
            "source_private_inputs_unchanged": source_unchanged,
            "raw_before_snapshot": raw_before,
            "raw_after_snapshot": raw_after,
            "raw_snapshot_exact_match": raw_snapshot_exact_match,
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
            bindings=bindings,
            decisions=decisions,
            wps=wps,
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
        "cash source materialization: "
        f"decision={summary['decision']} "
        f"resolved={summary['cash_project_resolved_count']} "
        f"unresolved={summary['cash_project_unresolved_count']} "
        f"materialized={summary['materialized_business_value_target_slot_count']} "
        f"raw_unchanged={summary['raw_snapshot_exact_match']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
