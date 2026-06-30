#!/usr/bin/env python3
"""Build KMFA S07-P1 finance file adapter metadata.

The adapter records finance source categories, read-only workbook structure,
and field candidates. Public outputs keep hashes, private refs, controlled
field ids, and quality states only. They must not contain source headers,
raw business values, private filenames, or source file bytes.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import sys
import tempfile
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from xml.etree import ElementTree


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_MANIFEST = ROOT / "metadata" / "schema_maps" / "finance_file_adapter_manifest.json"
DEFAULT_OUTPUT_CANDIDATES = ROOT / "metadata" / "schema_maps" / "finance_field_candidates.jsonl"
DEFAULT_OUTPUT_REGISTRY = ROOT / "metadata" / "imports" / "finance_support_source_registry.json"
DEFAULT_OUTPUT_FIELD_REPORT = (
    ROOT
    / "stage_artifacts"
    / "S07_P1_finance_file_adapter"
    / "machine"
    / "finance_readonly_field_report.jsonl"
)

HASH_RE = re.compile(r"^sha256:[a-f0-9]{64}$")
CELL_REF_RE = re.compile(r"^([A-Z]+)")
FORBIDDEN_PUBLIC_KEYS = {
    "raw_value",
    "normalized_value",
    "original_value",
    "source_header_text",
    "plaintext_content",
    "full_file_text",
    "raw_file_bytes",
    "original_filename",
    "bank_account_number",
    "identity_document_number",
    "password",
    "token",
    "api_key",
    "private_key",
}
REQUIRED_FINANCE_CATEGORIES = (
    "operating_analysis",
    "journal",
    "customer_aging",
    "cash",
    "tax",
    "invoice",
    "account",
    "loan",
    "r_and_d_expense",
)


@dataclass(frozen=True)
class FinanceFieldSpec:
    field_key: str
    field_label: str
    value_kind: str
    field_role: str


@dataclass(frozen=True)
class FinanceCategorySpec:
    finance_category: str
    source_ref: str
    source_file_private_ref: str
    fields: tuple[FinanceFieldSpec, ...]


FINANCE_CATEGORY_SPECS = (
    FinanceCategorySpec(
        "operating_analysis",
        "SRC-FIN-OPERATING-001",
        "private://KMFA/S07-P1/source/SRC-FIN-OPERATING-001",
        (
            FinanceFieldSpec("period_ref", "period reference", "period", "dimension"),
            FinanceFieldSpec("revenue_amount", "revenue amount", "money_cents", "metric"),
            FinanceFieldSpec("contract_amount", "contract amount", "money_cents", "metric"),
            FinanceFieldSpec("total_expense", "total expense", "money_cents", "metric"),
            FinanceFieldSpec("gross_margin", "gross margin", "ratio_basis_points", "metric"),
        ),
    ),
    FinanceCategorySpec(
        "journal",
        "SRC-FIN-JOURNAL-001",
        "private://KMFA/S07-P1/source/SRC-FIN-JOURNAL-001",
        (
            FinanceFieldSpec("transaction_date", "transaction date", "date", "dimension"),
            FinanceFieldSpec("account_subject", "account subject", "category_string", "dimension"),
            FinanceFieldSpec("debit_amount", "debit amount", "money_cents", "metric"),
            FinanceFieldSpec("credit_amount", "credit amount", "money_cents", "metric"),
            FinanceFieldSpec("counterparty_ref", "counterparty reference", "entity_ref", "dimension"),
        ),
    ),
    FinanceCategorySpec(
        "customer_aging",
        "SRC-FIN-AGING-001",
        "private://KMFA/S07-P1/source/SRC-FIN-AGING-001",
        (
            FinanceFieldSpec("customer_ref", "customer reference", "entity_ref", "dimension"),
            FinanceFieldSpec("receivable_amount", "receivable amount", "money_cents", "metric"),
            FinanceFieldSpec("aging_bucket", "aging bucket", "category_string", "dimension"),
            FinanceFieldSpec("overdue_days", "overdue days", "integer_days", "metric"),
            FinanceFieldSpec("responsibility_ref", "responsibility reference", "entity_ref", "dimension"),
        ),
    ),
    FinanceCategorySpec(
        "cash",
        "SRC-FIN-CASH-001",
        "private://KMFA/S07-P1/source/SRC-FIN-CASH-001",
        (
            FinanceFieldSpec("period_ref", "period reference", "period", "dimension"),
            FinanceFieldSpec("account_ref", "account reference", "account_ref", "dimension"),
            FinanceFieldSpec("cash_balance", "cash balance", "money_cents", "metric"),
            FinanceFieldSpec("cash_inflow", "cash inflow", "money_cents", "metric"),
            FinanceFieldSpec("cash_outflow", "cash outflow", "money_cents", "metric"),
        ),
    ),
    FinanceCategorySpec(
        "tax",
        "SRC-FIN-TAX-001",
        "private://KMFA/S07-P1/source/SRC-FIN-TAX-001",
        (
            FinanceFieldSpec("tax_period", "tax period", "period", "dimension"),
            FinanceFieldSpec("tax_type", "tax type", "category_string", "dimension"),
            FinanceFieldSpec("taxable_amount", "taxable amount", "money_cents", "metric"),
            FinanceFieldSpec("tax_amount", "tax amount", "money_cents", "metric"),
            FinanceFieldSpec("tax_rate", "tax rate", "ratio_basis_points", "metric"),
        ),
    ),
    FinanceCategorySpec(
        "invoice",
        "SRC-FIN-INVOICE-001",
        "private://KMFA/S07-P1/source/SRC-FIN-INVOICE-001",
        (
            FinanceFieldSpec("invoice_ref", "invoice reference", "document_ref", "dimension"),
            FinanceFieldSpec("invoice_date", "invoice date", "date", "dimension"),
            FinanceFieldSpec("customer_ref", "customer reference", "entity_ref", "dimension"),
            FinanceFieldSpec("invoice_amount", "invoice amount", "money_cents", "metric"),
            FinanceFieldSpec("invoice_status", "invoice status", "category_string", "dimension"),
        ),
    ),
    FinanceCategorySpec(
        "account",
        "SRC-FIN-ACCOUNT-001",
        "private://KMFA/S07-P1/source/SRC-FIN-ACCOUNT-001",
        (
            FinanceFieldSpec("account_ref", "account reference", "account_ref", "dimension"),
            FinanceFieldSpec("account_type", "account type", "category_string", "dimension"),
            FinanceFieldSpec("institution_ref", "institution reference", "entity_ref", "dimension"),
            FinanceFieldSpec("currency_code", "currency code", "currency", "dimension"),
            FinanceFieldSpec("account_status", "account status", "category_string", "dimension"),
        ),
    ),
    FinanceCategorySpec(
        "loan",
        "SRC-FIN-LOAN-001",
        "private://KMFA/S07-P1/source/SRC-FIN-LOAN-001",
        (
            FinanceFieldSpec("loan_ref", "loan reference", "document_ref", "dimension"),
            FinanceFieldSpec("lender_ref", "lender reference", "entity_ref", "dimension"),
            FinanceFieldSpec("principal_amount", "principal amount", "money_cents", "metric"),
            FinanceFieldSpec("interest_rate", "interest rate", "ratio_basis_points", "metric"),
            FinanceFieldSpec("maturity_date", "maturity date", "date", "dimension"),
        ),
    ),
    FinanceCategorySpec(
        "r_and_d_expense",
        "SRC-FIN-RD-001",
        "private://KMFA/S07-P1/source/SRC-FIN-RD-001",
        (
            FinanceFieldSpec("period_ref", "period reference", "period", "dimension"),
            FinanceFieldSpec("project_ref", "project reference", "project_ref", "dimension"),
            FinanceFieldSpec("expense_category", "expense category", "category_string", "dimension"),
            FinanceFieldSpec("expense_amount", "expense amount", "money_cents", "metric"),
            FinanceFieldSpec("evidence_ref", "evidence reference", "document_ref", "dimension"),
        ),
    ),
)


def sha256_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def sha256_text(value: str) -> str:
    return sha256_bytes(value.encode("utf-8"))


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def require_category(finance_category: str) -> str:
    if finance_category not in REQUIRED_FINANCE_CATEGORIES:
        raise ValueError(f"unknown finance category: {finance_category!r}")
    return finance_category


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def zip_write_text(archive: zipfile.ZipFile, name: str, text: str) -> None:
    info = zipfile.ZipInfo(name)
    info.date_time = (2026, 1, 1, 0, 0, 0)
    info.compress_type = zipfile.ZIP_DEFLATED
    archive.writestr(info, text)


def build_minimal_xlsx_bytes(headers: list[str], *, sheet_name: str) -> bytes:
    cells = []
    for index, value in enumerate(headers, start=1):
        column = chr(ord("A") + index - 1)
        cells.append(f'<c r="{column}1" t="inlineStr"><is><t>{value}</t></is></c>')
    sheet_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        '<sheetData><row r="1">'
        + "".join(cells)
        + "</row></sheetData></worksheet>"
    )
    workbook_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        f'<sheets><sheet name="{sheet_name}" sheetId="1" r:id="rId1"/></sheets></workbook>'
    )
    rels_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
        'Target="worksheets/sheet1.xml"/></Relationships>'
    )
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        zip_write_text(archive, "[Content_Types].xml", "")
        zip_write_text(archive, "xl/workbook.xml", workbook_xml)
        zip_write_text(archive, "xl/_rels/workbook.xml.rels", rels_xml)
        zip_write_text(archive, "xl/worksheets/sheet1.xml", sheet_xml)
    return buffer.getvalue()


def xml_root(text: bytes) -> ElementTree.Element:
    return ElementTree.fromstring(text)


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def rel_targets(archive: zipfile.ZipFile) -> dict[str, str]:
    try:
        root = xml_root(archive.read("xl/_rels/workbook.xml.rels"))
    except KeyError:
        return {}
    targets: dict[str, str] = {}
    for child in root:
        if local_name(child.tag) == "Relationship":
            rel_id = str(child.attrib.get("Id", ""))
            target = str(child.attrib.get("Target", ""))
            if rel_id and target:
                targets[rel_id] = target
    return targets


def workbook_sheets(archive: zipfile.ZipFile) -> list[tuple[str, str]]:
    root = xml_root(archive.read("xl/workbook.xml"))
    namespace = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
    rels = rel_targets(archive)
    sheets: list[tuple[str, str]] = []
    for element in root.iter():
        if local_name(element.tag) != "sheet":
            continue
        sheet_name = str(element.attrib.get("name", "sheet"))
        rel_id = str(element.attrib.get(namespace + "id", ""))
        target = rels.get(rel_id)
        if not target:
            continue
        sheet_path = "xl/" + target.lstrip("/")
        if sheet_path.startswith("xl/../"):
            raise ValueError("invalid worksheet relationship target")
        sheets.append((sheet_name, sheet_path))
    return sheets


def shared_strings(archive: zipfile.ZipFile) -> list[str]:
    try:
        root = xml_root(archive.read("xl/sharedStrings.xml"))
    except KeyError:
        return []
    values: list[str] = []
    for item in root:
        if local_name(item.tag) != "si":
            continue
        values.append("".join(text.text or "" for text in item.iter() if local_name(text.tag) == "t"))
    return values


def cell_text(cell: ElementTree.Element, shared: list[str]) -> str:
    cell_type = cell.attrib.get("t")
    if cell_type == "inlineStr":
        return "".join(text.text or "" for text in cell.iter() if local_name(text.tag) == "t")
    value = ""
    for child in cell:
        if local_name(child.tag) == "v":
            value = child.text or ""
            break
    if cell_type == "s" and value:
        index = int(value)
        return shared[index] if 0 <= index < len(shared) else ""
    return value


def column_ref(cell_ref: str, fallback_index: int) -> str:
    match = CELL_REF_RE.match(cell_ref)
    if match:
        return match.group(1)
    return chr(ord("A") + fallback_index)


def parse_sheet_headers(archive: zipfile.ZipFile, sheet_path: str, shared: list[str]) -> list[dict[str, Any]]:
    root = xml_root(archive.read(sheet_path))
    first_row: ElementTree.Element | None = None
    for element in root.iter():
        if local_name(element.tag) == "row":
            first_row = element
            break
    if first_row is None:
        return []

    headers: list[dict[str, Any]] = []
    cell_index = 0
    for cell in first_row:
        if local_name(cell.tag) != "c":
            continue
        text = cell_text(cell, shared).strip()
        if not text:
            cell_index += 1
            continue
        col = column_ref(str(cell.attrib.get("r", "")), cell_index)
        headers.append(
            {
                "column_ref": col,
                "header_index": len(headers) + 1,
                "source_header_hash": sha256_text("S07-P1:source-header:" + text),
            }
        )
        cell_index += 1
    return headers


def parse_xlsx_structure(
    workbook_path: Path,
    *,
    source_ref: str,
    finance_category: str,
    private_source_ref: str,
) -> dict[str, Any]:
    category = require_category(finance_category)
    data = workbook_path.read_bytes()
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        shared = shared_strings(archive)
        sheets = []
        for sheet_index, (sheet_name, sheet_path) in enumerate(workbook_sheets(archive), start=1):
            headers = parse_sheet_headers(archive, sheet_path, shared)
            sheet_hash = sha256_text(f"S07-P1:sheet:{source_ref}:{sheet_index}:{sheet_name}")
            for header in headers:
                header["source_header_private_ref"] = (
                    f"{private_source_ref}/sheet-{sheet_index}/header-{header['column_ref']}"
                )
            sheets.append(
                {
                    "sheet_ref": f"sheet:{sheet_index}:{sheet_hash}",
                    "sheet_name_hash": sheet_hash,
                    "headers": headers,
                }
            )
    return {
        "record_type": "finance_file_readonly_structure",
        "schema_version": "kmfa.finance_file_structure.v1",
        "project_id": "KMFA",
        "stage_phase": "S07-P1",
        "source_ref": source_ref,
        "finance_category": category,
        "file_format": "xlsx",
        "file_hash": sha256_bytes(data),
        "source_file_private_ref": private_source_ref,
        "read_only_parse": True,
        "raw_layer_write_allowed": False,
        "raw_source_mutation_allowed": False,
        "source_header_plaintext_committed": False,
        "sheets": sheets,
    }


def synthetic_headers_for(spec: FinanceCategorySpec) -> list[str]:
    return [f"S07P1_{spec.finance_category}_{field.field_key}_header_probe" for field in spec.fields]


def build_default_structures() -> list[dict[str, Any]]:
    structures: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        for spec in FINANCE_CATEGORY_SPECS:
            workbook_bytes = build_minimal_xlsx_bytes(
                synthetic_headers_for(spec),
                sheet_name=f"S07P1_{spec.finance_category}",
            )
            workbook_path = tmp_path / f"{spec.source_ref}.xlsx"
            workbook_path.write_bytes(workbook_bytes)
            structures.append(
                parse_xlsx_structure(
                    workbook_path,
                    source_ref=spec.source_ref,
                    finance_category=spec.finance_category,
                    private_source_ref=spec.source_file_private_ref,
                )
            )
    return structures


def build_mapping_id(source_ref: str, field_key: str, source_header_hash: str) -> str:
    seed = f"{source_ref}:{field_key}:{source_header_hash}"
    return "FIN-FLD-" + hashlib.sha256(seed.encode("utf-8")).hexdigest()[:12].upper()


def build_candidate_records(structures: list[dict[str, Any]]) -> list[dict[str, Any]]:
    spec_by_category = {spec.finance_category: spec for spec in FINANCE_CATEGORY_SPECS}
    candidates: list[dict[str, Any]] = []
    for structure in structures:
        spec = spec_by_category[str(structure["finance_category"])]
        if not structure["sheets"]:
            raise ValueError(f"source has no sheets: {structure['source_ref']}")
        headers = structure["sheets"][0]["headers"]
        if len(headers) < len(spec.fields):
            raise ValueError(f"source has fewer headers than field specs: {structure['source_ref']}")
        for index, field in enumerate(spec.fields):
            header = headers[index]
            source_header_hash = str(header["source_header_hash"])
            candidates.append(
                {
                    "record_type": "finance_field_candidate_mapping",
                    "schema_version": "kmfa.finance_field_candidate.v1",
                    "project_id": "KMFA",
                    "stage_phase": "S07-P1",
                    "mapping_id": build_mapping_id(spec.source_ref, field.field_key, source_header_hash),
                    "finance_category": spec.finance_category,
                    "source_ref": spec.source_ref,
                    "canonical_field": {
                        "field_key": field.field_key,
                        "field_label": field.field_label,
                        "value_kind": field.value_kind,
                        "field_role": field.field_role,
                    },
                    "source_binding": {
                        "source_file_private_ref": structure["source_file_private_ref"],
                        "file_format": structure["file_format"],
                        "file_hash": structure["file_hash"],
                        "sheet_ref": structure["sheets"][0]["sheet_ref"],
                        "column_ref": header["column_ref"],
                        "source_header_hash": source_header_hash,
                        "source_header_private_ref": header["source_header_private_ref"],
                        "source_anchor_status": "hash_only_from_readonly_parse",
                    },
                    "quality_state": {
                        "machine_candidate_quality_grade": "Q2_structure_candidate",
                        "q4_human_confirmed": False,
                        "q5_calculation_baseline_allowed": False,
                        "formal_report_allowed": False,
                    },
                    "public_repo_safety": {
                        "raw_business_values_committed": False,
                        "normalized_business_values_committed": False,
                        "source_header_plaintext_committed": False,
                        "raw_file_committed": False,
                        "private_csv_committed": False,
                    },
                    "next_required_phase": "S07 stage review before downstream lineage or fact layer use",
                }
            )
    return candidates


def build_field_report(structures: list[dict[str, Any]], candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    candidates_by_category: dict[str, list[dict[str, Any]]] = {}
    for candidate in candidates:
        candidates_by_category.setdefault(str(candidate["finance_category"]), []).append(candidate)
    reports: list[dict[str, Any]] = []
    for structure in structures:
        category = str(structure["finance_category"])
        source_candidates = candidates_by_category.get(category, [])
        header_count = sum(len(sheet.get("headers", [])) for sheet in structure.get("sheets", []))
        reports.append(
            {
                "record_type": "finance_file_field_report",
                "schema_version": "kmfa.finance_file_field_report.v1",
                "project_id": "KMFA",
                "stage_phase": "S07-P1",
                "source_ref": structure["source_ref"],
                "finance_category": category,
                "file_format": structure["file_format"],
                "file_hash": structure["file_hash"],
                "parse_status": "parsed_structure_from_xlsx",
                "read_only_parse": True,
                "raw_layer_write_allowed": False,
                "raw_source_mutation_allowed": False,
                "source_header_plaintext_committed": False,
                "sheet_count": len(structure.get("sheets", [])),
                "source_header_hash_count": header_count,
                "field_candidate_count": len(source_candidates),
                "canonical_field_keys": [
                    candidate["canonical_field"]["field_key"] for candidate in source_candidates
                ],
                "stage_scope": {
                    "finance_file_adapter": True,
                    "wps_scope_included": False,
                    "redcircle_scope_included": False,
                    "external_connector_included": False,
                },
            }
        )
    return reports


def build_source_registry(structures: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "record_type": "finance_support_source_registry",
        "schema_version": "kmfa.finance_support_source_registry.v1",
        "project_id": "KMFA",
        "stage_phase": "S07-P1",
        "sources": [
            {
                "source_ref": structure["source_ref"],
                "finance_category": structure["finance_category"],
                "file_format": structure["file_format"],
                "file_hash": structure["file_hash"],
                "source_file_private_ref": structure["source_file_private_ref"],
                "read_only_parse": True,
                "raw_layer_write_allowed": False,
                "raw_source_mutation_allowed": False,
                "source_header_plaintext_committed": False,
                "parse_status": "parsed_structure_from_xlsx",
            }
            for structure in structures
        ],
        "public_repo_safety": {
            "raw_business_values_committed": False,
            "normalized_business_values_committed": False,
            "source_header_plaintext_committed": False,
            "raw_file_committed": False,
            "private_csv_committed": False,
        },
    }


def build_default_finance_adapter(
    *, generated_at: str | None = None
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    generated_timestamp = generated_at or datetime.now(timezone.utc).isoformat()
    structures = build_default_structures()
    candidates = build_candidate_records(structures)
    field_report = build_field_report(structures, candidates)
    registry = build_source_registry(structures)
    manifest = {
        "record_type": "finance_file_adapter_manifest",
        "schema_version": "kmfa.finance_file_adapter.v1",
        "project_id": "KMFA",
        "stage_phase": "S07-P1",
        "generated_at": generated_timestamp,
        "finance_categories": list(REQUIRED_FINANCE_CATEGORIES),
        "source_registry_ref": display_path(DEFAULT_OUTPUT_REGISTRY),
        "field_candidates_ref": display_path(DEFAULT_OUTPUT_CANDIDATES),
        "field_report_ref": display_path(DEFAULT_OUTPUT_FIELD_REPORT),
        "source_registry": registry["sources"],
        "summary": {
            "source_category_count": len({item["finance_category"] for item in registry["sources"]}),
            "source_registry_count": len(registry["sources"]),
            "field_candidate_count": len(candidates),
            "field_report_count": len(field_report),
            "source_header_hash_count": sum(record["source_header_hash_count"] for record in field_report),
        },
        "stage_scope": {
            "finance_file_adapter": True,
            "wps_scope_included": False,
            "redcircle_scope_included": False,
            "external_connector_included": False,
            "facts_layer_write_included": False,
            "formal_report_generation_included": False,
        },
        "quality_gate": {
            "candidate_quality_grade": "Q2_structure_candidate",
            "requires_stage7_review_before_downstream_use": True,
            "formal_report_allowed": False,
            "q5_calculation_baseline_allowed": False,
        },
        "public_repo_safety": {
            "raw_business_values_committed": False,
            "normalized_business_values_committed": False,
            "source_header_plaintext_committed": False,
            "raw_file_committed": False,
            "private_csv_committed": False,
            "xlsx_committed": False,
            "pdf_committed": False,
            "zip_committed": False,
        },
    }
    validate_finance_adapter(manifest, candidates, field_report, registry=registry)
    return manifest, candidates, field_report


def walk_forbidden_keys(value: Any, path: str = "$") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key in FORBIDDEN_PUBLIC_KEYS:
                raise ValueError(f"forbidden public metadata key {key!r} at {path}")
            walk_forbidden_keys(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            walk_forbidden_keys(child, f"{path}[{index}]")


def ensure_hash(value: Any, field_name: str) -> None:
    if not HASH_RE.match(str(value or "")):
        raise ValueError(f"{field_name} must be sha256:<64 hex>")


def validate_finance_adapter(
    manifest: dict[str, Any],
    candidates: list[dict[str, Any]],
    field_report: list[dict[str, Any]],
    *,
    registry: dict[str, Any] | None = None,
) -> None:
    walk_forbidden_keys(manifest)
    walk_forbidden_keys(candidates)
    walk_forbidden_keys(field_report)
    if registry is not None:
        walk_forbidden_keys(registry)

    if manifest.get("schema_version") != "kmfa.finance_file_adapter.v1":
        raise ValueError("invalid finance adapter manifest schema_version")
    if manifest.get("stage_phase") != "S07-P1":
        raise ValueError("finance adapter manifest must be S07-P1")
    if set(manifest.get("finance_categories", [])) != set(REQUIRED_FINANCE_CATEGORIES):
        raise ValueError("finance adapter manifest must cover all required S07-P1 categories")
    if manifest.get("stage_scope", {}).get("wps_scope_included") is not False:
        raise ValueError("S07-P1 must not include WPS scope")
    if manifest.get("stage_scope", {}).get("redcircle_scope_included") is not False:
        raise ValueError("S07-P1 must not include redcircle scope")
    if manifest.get("quality_gate", {}).get("formal_report_allowed") is not False:
        raise ValueError("S07-P1 must not allow formal reports")
    safety = manifest.get("public_repo_safety") or {}
    for key in (
        "raw_business_values_committed",
        "normalized_business_values_committed",
        "source_header_plaintext_committed",
        "raw_file_committed",
        "private_csv_committed",
        "xlsx_committed",
        "pdf_committed",
        "zip_committed",
    ):
        if safety.get(key) is not False:
            raise ValueError(f"public_repo_safety.{key} must be false")

    registry_sources = manifest.get("source_registry") or []
    if len(registry_sources) != len(REQUIRED_FINANCE_CATEGORIES):
        raise ValueError("source registry count must match required finance categories")
    if {item.get("finance_category") for item in registry_sources} != set(REQUIRED_FINANCE_CATEGORIES):
        raise ValueError("source registry categories must match required finance categories")
    for item in registry_sources:
        ensure_hash(item.get("file_hash"), "source_registry.file_hash")
        if item.get("read_only_parse") is not True:
            raise ValueError("source registry rows must be read-only parses")
        if item.get("raw_layer_write_allowed") is not False:
            raise ValueError("source registry rows must not write raw layer")

    candidate_categories = {item.get("finance_category") for item in candidates}
    if candidate_categories != set(REQUIRED_FINANCE_CATEGORIES):
        raise ValueError("field candidates must cover all required finance categories")
    seen_ids: set[str] = set()
    for item in candidates:
        if item.get("schema_version") != "kmfa.finance_field_candidate.v1":
            raise ValueError("invalid field candidate schema_version")
        mapping_id = str(item.get("mapping_id", ""))
        if not mapping_id.startswith("FIN-FLD-"):
            raise ValueError("field candidate mapping_id must start with FIN-FLD-")
        if mapping_id in seen_ids:
            raise ValueError(f"duplicate field candidate mapping_id: {mapping_id}")
        seen_ids.add(mapping_id)
        source_binding = item.get("source_binding") or {}
        ensure_hash(source_binding.get("file_hash"), "field_candidate.file_hash")
        ensure_hash(source_binding.get("source_header_hash"), "field_candidate.source_header_hash")
        if "source_header_private_ref" not in source_binding:
            raise ValueError("field candidates must keep source_header_private_ref")
        if item.get("quality_state", {}).get("q4_human_confirmed") is not False:
            raise ValueError("S07-P1 field candidates must not claim Q4 confirmation")
        if item.get("quality_state", {}).get("q5_calculation_baseline_allowed") is not False:
            raise ValueError("S07-P1 field candidates must not claim Q5 baseline")
        if item.get("quality_state", {}).get("formal_report_allowed") is not False:
            raise ValueError("S07-P1 field candidates must not allow formal reports")

    report_categories = {item.get("finance_category") for item in field_report}
    if report_categories != set(REQUIRED_FINANCE_CATEGORIES):
        raise ValueError("field reports must cover all required finance categories")
    for item in field_report:
        if item.get("schema_version") != "kmfa.finance_file_field_report.v1":
            raise ValueError("invalid field report schema_version")
        ensure_hash(item.get("file_hash"), "field_report.file_hash")
        if item.get("parse_status") != "parsed_structure_from_xlsx":
            raise ValueError("S07-P1 default report must be parsed_structure_from_xlsx")
        if item.get("read_only_parse") is not True:
            raise ValueError("field reports must be read-only")
        if item.get("raw_layer_write_allowed") is not False:
            raise ValueError("field reports must not write raw layer")
        if item.get("source_header_plaintext_committed") is not False:
            raise ValueError("field reports must not commit source header plaintext")

    summary = manifest.get("summary") or {}
    if summary.get("source_category_count") != len(REQUIRED_FINANCE_CATEGORIES):
        raise ValueError("summary.source_category_count mismatch")
    if summary.get("field_candidate_count") != len(candidates):
        raise ValueError("summary.field_candidate_count mismatch")
    if summary.get("field_report_count") != len(field_report):
        raise ValueError("summary.field_report_count mismatch")


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        payload = json.loads(line)
        if not isinstance(payload, dict):
            raise ValueError(f"{path}:{line_no} must contain a JSON object")
        records.append(payload)
    return records


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(json.dumps(item, ensure_ascii=False, sort_keys=True) for item in records) + "\n",
        encoding="utf-8",
    )


def write_outputs(
    manifest: dict[str, Any],
    candidates: list[dict[str, Any]],
    field_report: list[dict[str, Any]],
    *,
    output_manifest: Path = DEFAULT_OUTPUT_MANIFEST,
    output_candidates: Path = DEFAULT_OUTPUT_CANDIDATES,
    output_registry: Path = DEFAULT_OUTPUT_REGISTRY,
    output_field_report: Path = DEFAULT_OUTPUT_FIELD_REPORT,
) -> None:
    registry = {
        "record_type": "finance_support_source_registry",
        "schema_version": "kmfa.finance_support_source_registry.v1",
        "project_id": "KMFA",
        "stage_phase": "S07-P1",
        "sources": manifest["source_registry"],
        "public_repo_safety": {
            "raw_business_values_committed": False,
            "normalized_business_values_committed": False,
            "source_header_plaintext_committed": False,
            "raw_file_committed": False,
            "private_csv_committed": False,
        },
    }
    validate_finance_adapter(manifest, candidates, field_report, registry=registry)
    write_json(output_manifest, manifest)
    write_jsonl(output_candidates, candidates)
    write_json(output_registry, registry)
    write_jsonl(output_field_report, field_report)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build KMFA S07-P1 finance file adapter metadata.")
    parser.add_argument("--output-manifest", type=Path, default=DEFAULT_OUTPUT_MANIFEST)
    parser.add_argument("--output-candidates", type=Path, default=DEFAULT_OUTPUT_CANDIDATES)
    parser.add_argument("--output-registry", type=Path, default=DEFAULT_OUTPUT_REGISTRY)
    parser.add_argument("--output-field-report", type=Path, default=DEFAULT_OUTPUT_FIELD_REPORT)
    parser.add_argument("--generated-at")
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args(argv)

    manifest, candidates, field_report = build_default_finance_adapter(generated_at=args.generated_at)
    if not args.check_only:
        write_outputs(
            manifest,
            candidates,
            field_report,
            output_manifest=args.output_manifest,
            output_candidates=args.output_candidates,
            output_registry=args.output_registry,
            output_field_report=args.output_field_report,
        )
    print(
        "PASS: KMFA S07-P1 finance adapter built "
        f"(categories={manifest['summary']['source_category_count']}, "
        f"field_candidates={manifest['summary']['field_candidate_count']}, "
        f"field_reports={manifest['summary']['field_report_count']}, "
        "formal_report_allowed=false)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
