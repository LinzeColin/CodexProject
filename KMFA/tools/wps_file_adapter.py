#!/usr/bin/env python3
"""Build KMFA S07-P2 WPS file adapter metadata.

The adapter records WPS export types, read-only converted-workbook structure,
field mappings, conversion guidance, and mapping rule versions. Public outputs
keep hashes, private refs, controlled field ids, and quality states only.
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
DEFAULT_OUTPUT_MANIFEST = ROOT / "metadata" / "schema_maps" / "wps_file_adapter_manifest.json"
DEFAULT_OUTPUT_MAPPINGS = ROOT / "metadata" / "schema_maps" / "wps_field_mappings.jsonl"
DEFAULT_OUTPUT_RULE_VERSIONS = ROOT / "metadata" / "schema_maps" / "wps_mapping_rule_versions.json"
DEFAULT_OUTPUT_REGISTRY = ROOT / "metadata" / "imports" / "wps_export_source_registry.json"
DEFAULT_OUTPUT_CONVERSION_GUIDANCE = (
    ROOT
    / "stage_artifacts"
    / "S07_P2_wps_file_adapter"
    / "machine"
    / "wps_conversion_guidance.jsonl"
)
DEFAULT_OUTPUT_FIELD_REPORT = (
    ROOT
    / "stage_artifacts"
    / "S07_P2_wps_file_adapter"
    / "machine"
    / "wps_readonly_field_report.jsonl"
)

ACTIVE_MAPPING_RULE_VERSION = "MAP-SRC-kmfa-wps-file-adapter-s07p2-v0.1.0"
HASH_RE = re.compile(r"^sha256:[a-f0-9]{64}$")
CELL_REF_RE = re.compile(r"^([A-Z]+)")
OLE_MAGIC = bytes.fromhex("d0cf11e0a1b11ae1")
ZIP_MAGIC = b"PK\x03\x04"
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
REQUIRED_WPS_EXPORT_TYPES = (
    "collection",
    "receivable_aging",
    "production_project_status",
    "deposit",
)


@dataclass(frozen=True)
class WpsFieldSpec:
    field_key: str
    field_label: str
    value_kind: str
    field_role: str


@dataclass(frozen=True)
class WpsExportSpec:
    export_type: str
    source_ref: str
    source_file_private_ref: str
    fields: tuple[WpsFieldSpec, ...]


WPS_EXPORT_SPECS = (
    WpsExportSpec(
        "collection",
        "SRC-WPS-COLLECTION-001",
        "private://KMFA/S07-P2/source/SRC-WPS-COLLECTION-001",
        (
            WpsFieldSpec("collection_date", "collection date", "date", "dimension"),
            WpsFieldSpec("project_ref", "project reference", "project_ref", "dimension"),
            WpsFieldSpec("customer_ref", "customer reference", "entity_ref", "dimension"),
            WpsFieldSpec("collection_amount", "collection amount", "money_cents", "metric"),
            WpsFieldSpec("receipt_status", "receipt status", "category_string", "dimension"),
        ),
    ),
    WpsExportSpec(
        "receivable_aging",
        "SRC-WPS-AGING-001",
        "private://KMFA/S07-P2/source/SRC-WPS-AGING-001",
        (
            WpsFieldSpec("customer_ref", "customer reference", "entity_ref", "dimension"),
            WpsFieldSpec("project_ref", "project reference", "project_ref", "dimension"),
            WpsFieldSpec("receivable_amount", "receivable amount", "money_cents", "metric"),
            WpsFieldSpec("aging_bucket", "aging bucket", "category_string", "dimension"),
            WpsFieldSpec("overdue_days", "overdue days", "integer_days", "metric"),
        ),
    ),
    WpsExportSpec(
        "production_project_status",
        "SRC-WPS-PROJECT-STATUS-001",
        "private://KMFA/S07-P2/source/SRC-WPS-PROJECT-STATUS-001",
        (
            WpsFieldSpec("project_ref", "project reference", "project_ref", "dimension"),
            WpsFieldSpec("production_status", "production status", "category_string", "dimension"),
            WpsFieldSpec("planned_finish_date", "planned finish date", "date", "dimension"),
            WpsFieldSpec("actual_progress_rate", "actual progress rate", "ratio_basis_points", "metric"),
            WpsFieldSpec("responsible_team_ref", "responsible team reference", "entity_ref", "dimension"),
        ),
    ),
    WpsExportSpec(
        "deposit",
        "SRC-WPS-DEPOSIT-001",
        "private://KMFA/S07-P2/source/SRC-WPS-DEPOSIT-001",
        (
            WpsFieldSpec("deposit_ref", "deposit reference", "document_ref", "dimension"),
            WpsFieldSpec("project_ref", "project reference", "project_ref", "dimension"),
            WpsFieldSpec("counterparty_ref", "counterparty reference", "entity_ref", "dimension"),
            WpsFieldSpec("deposit_amount", "deposit amount", "money_cents", "metric"),
            WpsFieldSpec("deposit_status", "deposit status", "category_string", "dimension"),
        ),
    ),
)


def sha256_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def sha256_text(value: str) -> str:
    return sha256_bytes(value.encode("utf-8"))


def require_export_type(export_type: str) -> str:
    if export_type not in REQUIRED_WPS_EXPORT_TYPES:
        raise ValueError(f"unknown WPS export type: {export_type!r}")
    return export_type


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
        if local_name(item.tag) == "si":
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
                "source_header_hash": sha256_text("S07-P2:source-header:" + text),
            }
        )
        cell_index += 1
    return headers


def parse_xlsx_structure(
    workbook_path: Path,
    *,
    source_ref: str,
    export_type: str,
    private_source_ref: str,
) -> dict[str, Any]:
    required_export_type = require_export_type(export_type)
    data = workbook_path.read_bytes()
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        shared = shared_strings(archive)
        sheets = []
        for sheet_index, (sheet_name, sheet_path) in enumerate(workbook_sheets(archive), start=1):
            headers = parse_sheet_headers(archive, sheet_path, shared)
            sheet_hash = sha256_text(f"S07-P2:sheet:{source_ref}:{sheet_index}:{sheet_name}")
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
        "record_type": "wps_file_readonly_structure",
        "schema_version": "kmfa.wps_file_structure.v1",
        "project_id": "KMFA",
        "stage_phase": "S07-P2",
        "source_ref": source_ref,
        "export_type": required_export_type,
        "file_format": "xlsx",
        "file_hash": sha256_bytes(data),
        "source_file_private_ref": private_source_ref,
        "read_only_parse": True,
        "raw_layer_write_allowed": False,
        "raw_source_mutation_allowed": False,
        "source_header_plaintext_committed": False,
        "sheets": sheets,
    }


def classify_wps_file(path: str | Path, *, source_ref: str, export_type: str) -> dict[str, Any]:
    required_export_type = require_export_type(export_type)
    file_path = Path(path)
    data = file_path.read_bytes()
    extension = file_path.suffix.lower()
    magic = data[:8]
    if extension in {".et", ".wps", ".dps"}:
        file_format = "wps"
        container_type = "wps_native"
        parse_status = "requires_conversion_to_xlsx_or_csv"
        guidance = "识别为 WPS 原生格式；请先用 WPS 导出为 .xlsx 或 .csv，再进入 S07-P2 字段映射。"
    elif extension == ".xls" and magic.startswith(OLE_MAGIC):
        file_format = "xls"
        container_type = "ole_compound"
        parse_status = "requires_conversion_to_xlsx_or_csv"
        guidance = "识别为 OLE 旧版表格；请先转换为 .xlsx 或 .csv，再进入 S07-P2 字段映射。"
    elif extension == ".xlsx":
        file_format = "xlsx"
        container_type = "office_open_xml_zip" if magic.startswith(ZIP_MAGIC) else "xlsx_unknown_magic"
        parse_status = "parsed_structure_from_xlsx" if magic.startswith(ZIP_MAGIC) else "requires_reexport"
        guidance = "可对转换后的 .xlsx 做只读结构解析；公开仓库只保存 hash/private refs。"
    elif extension == ".csv":
        file_format = "csv"
        container_type = "flat_text"
        parse_status = "parsed_structure_from_csv_header"
        guidance = "可对转换后的 .csv 做只读表头映射；公开仓库只保存 hash/private refs。"
    else:
        file_format = extension.lstrip(".") or "unknown"
        container_type = "unsupported"
        parse_status = "requires_conversion_to_xlsx_or_csv"
        guidance = "不支持直接解析；请重新导出为 .xlsx 或 .csv 后再进入 S07-P2 字段映射。"
    return {
        "record_type": "wps_file_parse_plan",
        "schema_version": "kmfa.wps_file_parse_plan.v1",
        "project_id": "KMFA",
        "stage_phase": "S07-P2",
        "source_ref": source_ref,
        "export_type": required_export_type,
        "file_format": file_format,
        "container_type": container_type,
        "file_hash": sha256_bytes(data),
        "file_size_bytes": len(data),
        "filename_hash": sha256_text(file_path.name),
        "parse_status": parse_status,
        "operator_guidance": guidance,
        "read_only_parse": parse_status.startswith("parsed_structure"),
        "raw_layer_write_allowed": False,
        "raw_source_mutation_allowed": False,
    }


def synthetic_headers_for(spec: WpsExportSpec) -> list[str]:
    return [f"S07P2_{spec.export_type}_{field.field_key}_header_probe" for field in spec.fields]


def build_default_structures() -> list[dict[str, Any]]:
    structures: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        for spec in WPS_EXPORT_SPECS:
            workbook_bytes = build_minimal_xlsx_bytes(
                synthetic_headers_for(spec),
                sheet_name=f"S07P2_{spec.export_type}",
            )
            workbook_path = tmp_path / f"{spec.source_ref}.xlsx"
            workbook_path.write_bytes(workbook_bytes)
            structures.append(
                parse_xlsx_structure(
                    workbook_path,
                    source_ref=spec.source_ref,
                    export_type=spec.export_type,
                    private_source_ref=spec.source_file_private_ref,
                )
            )
    return structures


def build_mapping_id(source_ref: str, field_key: str, source_header_hash: str) -> str:
    seed = f"{source_ref}:{field_key}:{source_header_hash}:{ACTIVE_MAPPING_RULE_VERSION}"
    return "WPS-FLD-" + hashlib.sha256(seed.encode("utf-8")).hexdigest()[:12].upper()


def build_mapping_records(structures: list[dict[str, Any]]) -> list[dict[str, Any]]:
    spec_by_type = {spec.export_type: spec for spec in WPS_EXPORT_SPECS}
    mappings: list[dict[str, Any]] = []
    for structure in structures:
        spec = spec_by_type[str(structure["export_type"])]
        if not structure["sheets"]:
            raise ValueError(f"source has no sheets: {structure['source_ref']}")
        headers = structure["sheets"][0]["headers"]
        if len(headers) < len(spec.fields):
            raise ValueError(f"source has fewer headers than field specs: {structure['source_ref']}")
        for index, field in enumerate(spec.fields):
            header = headers[index]
            source_header_hash = str(header["source_header_hash"])
            mappings.append(
                {
                    "record_type": "wps_field_mapping",
                    "schema_version": "kmfa.wps_field_mapping.v1",
                    "project_id": "KMFA",
                    "stage_phase": "S07-P2",
                    "mapping_id": build_mapping_id(spec.source_ref, field.field_key, source_header_hash),
                    "mapping_rule_version_id": ACTIVE_MAPPING_RULE_VERSION,
                    "export_type": spec.export_type,
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
                        "source_anchor_status": "hash_only_from_readonly_converted_xlsx",
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
    return mappings


def build_conversion_guidance() -> list[dict[str, Any]]:
    guidance = []
    for spec in WPS_EXPORT_SPECS:
        guidance.append(
            {
                "record_type": "wps_conversion_guidance",
                "schema_version": "kmfa.wps_conversion_guidance.v1",
                "project_id": "KMFA",
                "stage_phase": "S07-P2",
                "source_ref": spec.source_ref,
                "export_type": spec.export_type,
                "native_wps_file_format": "wps",
                "native_wps_container_type": "wps_native",
                "native_wps_parse_status": "requires_conversion_to_xlsx_or_csv",
                "accepted_converted_formats": [".xlsx", ".csv"],
                "operator_guidance": "WPS 原生文件不能直接进入字段映射；请用 WPS 导出为 .xlsx 或 .csv 并保留原文件 hash/private ref。",
                "read_only_after_conversion": True,
                "raw_layer_write_allowed": False,
                "raw_source_mutation_allowed": False,
                "source_file_private_ref": spec.source_file_private_ref,
            }
        )
    return guidance


def build_field_report(structures: list[dict[str, Any]], mappings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    mappings_by_type: dict[str, list[dict[str, Any]]] = {}
    for mapping in mappings:
        mappings_by_type.setdefault(str(mapping["export_type"]), []).append(mapping)
    reports: list[dict[str, Any]] = []
    for structure in structures:
        export_type = str(structure["export_type"])
        source_mappings = mappings_by_type.get(export_type, [])
        header_count = sum(len(sheet.get("headers", [])) for sheet in structure.get("sheets", []))
        reports.append(
            {
                "record_type": "wps_file_field_report",
                "schema_version": "kmfa.wps_file_field_report.v1",
                "project_id": "KMFA",
                "stage_phase": "S07-P2",
                "source_ref": structure["source_ref"],
                "export_type": export_type,
                "file_format": structure["file_format"],
                "file_hash": structure["file_hash"],
                "parse_status": "parsed_structure_from_converted_xlsx",
                "native_wps_parse_status": "requires_conversion_to_xlsx_or_csv",
                "read_only_parse": True,
                "raw_layer_write_allowed": False,
                "raw_source_mutation_allowed": False,
                "source_header_plaintext_committed": False,
                "sheet_count": len(structure.get("sheets", [])),
                "source_header_hash_count": header_count,
                "field_mapping_count": len(source_mappings),
                "mapping_rule_version_id": ACTIVE_MAPPING_RULE_VERSION,
                "canonical_field_keys": [mapping["canonical_field"]["field_key"] for mapping in source_mappings],
                "stage_scope": {
                    "finance_scope_included": False,
                    "wps_scope_included": True,
                    "redcircle_scope_included": False,
                    "external_connector_included": False,
                },
            }
        )
    return reports


def build_source_registry(structures: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "record_type": "wps_export_source_registry",
        "schema_version": "kmfa.wps_export_source_registry.v1",
        "project_id": "KMFA",
        "stage_phase": "S07-P2",
        "sources": [
            {
                "source_ref": structure["source_ref"],
                "export_type": structure["export_type"],
                "converted_file_format": structure["file_format"],
                "converted_file_hash": structure["file_hash"],
                "source_file_private_ref": structure["source_file_private_ref"],
                "read_only_parse": True,
                "native_wps_conversion_required": True,
                "native_wps_parse_status": "requires_conversion_to_xlsx_or_csv",
                "raw_layer_write_allowed": False,
                "raw_source_mutation_allowed": False,
                "source_header_plaintext_committed": False,
                "parse_status": "parsed_structure_from_converted_xlsx",
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


def build_rule_versions(generated_at: str) -> dict[str, Any]:
    return {
        "record_type": "wps_mapping_rule_versions",
        "schema_version": "kmfa.wps_mapping_rule_versions.v1",
        "project_id": "KMFA",
        "stage_phase": "S07-P2",
        "active_mapping_rule_version": ACTIVE_MAPPING_RULE_VERSION,
        "versions": [
            {
                "mapping_rule_version_id": ACTIVE_MAPPING_RULE_VERSION,
                "version_status": "active",
                "created_at": generated_at,
                "change_type": "initial_s07p2_wps_mapping_rule_version",
                "covered_export_types": list(REQUIRED_WPS_EXPORT_TYPES),
                "mapping_records_ref": display_path(DEFAULT_OUTPUT_MAPPINGS),
                "public_repo_safety": {
                    "raw_business_values_committed": False,
                    "normalized_business_values_committed": False,
                    "source_header_plaintext_committed": False,
                    "raw_file_committed": False,
                    "private_csv_committed": False,
                },
            }
        ],
    }


def build_default_wps_adapter(
    *, generated_at: str | None = None
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    generated_timestamp = generated_at or datetime.now(timezone.utc).isoformat()
    structures = build_default_structures()
    mappings = build_mapping_records(structures)
    conversion_guidance = build_conversion_guidance()
    field_report = build_field_report(structures, mappings)
    registry = build_source_registry(structures)
    rule_versions = build_rule_versions(generated_timestamp)
    manifest = {
        "record_type": "wps_file_adapter_manifest",
        "schema_version": "kmfa.wps_file_adapter.v1",
        "project_id": "KMFA",
        "stage_phase": "S07-P2",
        "generated_at": generated_timestamp,
        "wps_export_types": list(REQUIRED_WPS_EXPORT_TYPES),
        "active_mapping_rule_version": ACTIVE_MAPPING_RULE_VERSION,
        "source_registry_ref": display_path(DEFAULT_OUTPUT_REGISTRY),
        "field_mappings_ref": display_path(DEFAULT_OUTPUT_MAPPINGS),
        "conversion_guidance_ref": display_path(DEFAULT_OUTPUT_CONVERSION_GUIDANCE),
        "field_report_ref": display_path(DEFAULT_OUTPUT_FIELD_REPORT),
        "mapping_rule_versions_ref": display_path(DEFAULT_OUTPUT_RULE_VERSIONS),
        "source_registry": registry["sources"],
        "summary": {
            "source_export_type_count": len({item["export_type"] for item in registry["sources"]}),
            "source_registry_count": len(registry["sources"]),
            "field_mapping_count": len(mappings),
            "field_report_count": len(field_report),
            "conversion_guidance_count": len(conversion_guidance),
            "mapping_rule_version_count": len(rule_versions["versions"]),
            "source_header_hash_count": sum(record["source_header_hash_count"] for record in field_report),
        },
        "stage_scope": {
            "finance_scope_included": False,
            "wps_scope_included": True,
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
    validate_wps_adapter(manifest, mappings, conversion_guidance, field_report, rule_versions, registry=registry)
    return manifest, mappings, conversion_guidance, field_report, rule_versions


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


def validate_wps_adapter(
    manifest: dict[str, Any],
    mappings: list[dict[str, Any]],
    conversion_guidance: list[dict[str, Any]],
    field_report: list[dict[str, Any]],
    rule_versions: dict[str, Any],
    *,
    registry: dict[str, Any] | None = None,
) -> None:
    walk_forbidden_keys(manifest)
    walk_forbidden_keys(mappings)
    walk_forbidden_keys(conversion_guidance)
    walk_forbidden_keys(field_report)
    walk_forbidden_keys(rule_versions)
    if registry is not None:
        walk_forbidden_keys(registry)

    if manifest.get("schema_version") != "kmfa.wps_file_adapter.v1":
        raise ValueError("invalid WPS adapter manifest schema_version")
    if manifest.get("stage_phase") != "S07-P2":
        raise ValueError("WPS adapter manifest must be S07-P2")
    if set(manifest.get("wps_export_types", [])) != set(REQUIRED_WPS_EXPORT_TYPES):
        raise ValueError("WPS adapter manifest must cover all required S07-P2 exports")
    if manifest.get("stage_scope", {}).get("finance_scope_included") is not False:
        raise ValueError("S07-P2 must not reopen finance scope")
    if manifest.get("stage_scope", {}).get("wps_scope_included") is not True:
        raise ValueError("S07-P2 must include WPS scope")
    if manifest.get("stage_scope", {}).get("redcircle_scope_included") is not False:
        raise ValueError("S07-P2 must not include redcircle scope")
    if manifest.get("quality_gate", {}).get("formal_report_allowed") is not False:
        raise ValueError("S07-P2 must not allow formal reports")
    if manifest.get("active_mapping_rule_version") != ACTIVE_MAPPING_RULE_VERSION:
        raise ValueError("active mapping rule version mismatch")
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
    if len(registry_sources) != len(REQUIRED_WPS_EXPORT_TYPES):
        raise ValueError("source registry count must match required WPS export types")
    if {item.get("export_type") for item in registry_sources} != set(REQUIRED_WPS_EXPORT_TYPES):
        raise ValueError("source registry export types must match required WPS export types")
    for item in registry_sources:
        ensure_hash(item.get("converted_file_hash"), "source_registry.converted_file_hash")
        if item.get("native_wps_conversion_required") is not True:
            raise ValueError("source registry rows must require native WPS conversion")
        if item.get("read_only_parse") is not True:
            raise ValueError("source registry rows must be read-only parses")
        if item.get("raw_layer_write_allowed") is not False:
            raise ValueError("source registry rows must not write raw layer")

    active_version = rule_versions.get("active_mapping_rule_version")
    if active_version != ACTIVE_MAPPING_RULE_VERSION:
        raise ValueError("rule_versions.active_mapping_rule_version mismatch")
    versions = rule_versions.get("versions") or []
    if len(versions) != 1:
        raise ValueError("S07-P2 must create exactly one initial WPS mapping rule version")
    version = versions[0]
    if version.get("mapping_rule_version_id") != ACTIVE_MAPPING_RULE_VERSION:
        raise ValueError("invalid WPS mapping rule version id")
    if set(version.get("covered_export_types", [])) != set(REQUIRED_WPS_EXPORT_TYPES):
        raise ValueError("WPS mapping rule version must cover all required exports")

    mapping_export_types = {item.get("export_type") for item in mappings}
    if mapping_export_types != set(REQUIRED_WPS_EXPORT_TYPES):
        raise ValueError("field mappings must cover all required WPS export types")
    seen_ids: set[str] = set()
    for item in mappings:
        if item.get("schema_version") != "kmfa.wps_field_mapping.v1":
            raise ValueError("invalid WPS field mapping schema_version")
        if item.get("mapping_rule_version_id") != ACTIVE_MAPPING_RULE_VERSION:
            raise ValueError("field mappings must bind active mapping rule version")
        mapping_id = str(item.get("mapping_id", ""))
        if not mapping_id.startswith("WPS-FLD-"):
            raise ValueError("WPS field mapping_id must start with WPS-FLD-")
        if mapping_id in seen_ids:
            raise ValueError(f"duplicate WPS field mapping_id: {mapping_id}")
        seen_ids.add(mapping_id)
        source_binding = item.get("source_binding") or {}
        ensure_hash(source_binding.get("file_hash"), "field_mapping.file_hash")
        ensure_hash(source_binding.get("source_header_hash"), "field_mapping.source_header_hash")
        if "source_header_private_ref" not in source_binding:
            raise ValueError("WPS field mappings must keep source_header_private_ref")
        if item.get("quality_state", {}).get("q4_human_confirmed") is not False:
            raise ValueError("S07-P2 field mappings must not claim Q4 confirmation")
        if item.get("quality_state", {}).get("q5_calculation_baseline_allowed") is not False:
            raise ValueError("S07-P2 field mappings must not claim Q5 baseline")
        if item.get("quality_state", {}).get("formal_report_allowed") is not False:
            raise ValueError("S07-P2 field mappings must not allow formal reports")

    guidance_export_types = {item.get("export_type") for item in conversion_guidance}
    if guidance_export_types != set(REQUIRED_WPS_EXPORT_TYPES):
        raise ValueError("conversion guidance must cover all required WPS export types")
    for item in conversion_guidance:
        if item.get("native_wps_parse_status") != "requires_conversion_to_xlsx_or_csv":
            raise ValueError("WPS native guidance must require conversion")
        guidance_text = str(item.get("operator_guidance", ""))
        if ".xlsx" not in guidance_text or ".csv" not in guidance_text:
            raise ValueError("WPS conversion guidance must mention .xlsx and .csv")
        if item.get("raw_layer_write_allowed") is not False:
            raise ValueError("conversion guidance must not write raw layer")

    report_export_types = {item.get("export_type") for item in field_report}
    if report_export_types != set(REQUIRED_WPS_EXPORT_TYPES):
        raise ValueError("field reports must cover all required WPS export types")
    for item in field_report:
        if item.get("schema_version") != "kmfa.wps_file_field_report.v1":
            raise ValueError("invalid WPS field report schema_version")
        ensure_hash(item.get("file_hash"), "field_report.file_hash")
        if item.get("parse_status") != "parsed_structure_from_converted_xlsx":
            raise ValueError("S07-P2 default report must parse converted xlsx structure")
        if item.get("native_wps_parse_status") != "requires_conversion_to_xlsx_or_csv":
            raise ValueError("S07-P2 field report must record native WPS conversion requirement")
        if item.get("read_only_parse") is not True:
            raise ValueError("WPS field reports must be read-only")
        if item.get("raw_layer_write_allowed") is not False:
            raise ValueError("WPS field reports must not write raw layer")
        if item.get("source_header_plaintext_committed") is not False:
            raise ValueError("WPS field reports must not commit source header plaintext")

    summary = manifest.get("summary") or {}
    if summary.get("source_export_type_count") != len(REQUIRED_WPS_EXPORT_TYPES):
        raise ValueError("summary.source_export_type_count mismatch")
    if summary.get("field_mapping_count") != len(mappings):
        raise ValueError("summary.field_mapping_count mismatch")
    if summary.get("field_report_count") != len(field_report):
        raise ValueError("summary.field_report_count mismatch")
    if summary.get("conversion_guidance_count") != len(conversion_guidance):
        raise ValueError("summary.conversion_guidance_count mismatch")


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
    mappings: list[dict[str, Any]],
    conversion_guidance: list[dict[str, Any]],
    field_report: list[dict[str, Any]],
    rule_versions: dict[str, Any],
    *,
    output_manifest: Path = DEFAULT_OUTPUT_MANIFEST,
    output_mappings: Path = DEFAULT_OUTPUT_MAPPINGS,
    output_rule_versions: Path = DEFAULT_OUTPUT_RULE_VERSIONS,
    output_registry: Path = DEFAULT_OUTPUT_REGISTRY,
    output_conversion_guidance: Path = DEFAULT_OUTPUT_CONVERSION_GUIDANCE,
    output_field_report: Path = DEFAULT_OUTPUT_FIELD_REPORT,
) -> None:
    registry = {
        "record_type": "wps_export_source_registry",
        "schema_version": "kmfa.wps_export_source_registry.v1",
        "project_id": "KMFA",
        "stage_phase": "S07-P2",
        "sources": manifest["source_registry"],
        "public_repo_safety": {
            "raw_business_values_committed": False,
            "normalized_business_values_committed": False,
            "source_header_plaintext_committed": False,
            "raw_file_committed": False,
            "private_csv_committed": False,
        },
    }
    validate_wps_adapter(
        manifest,
        mappings,
        conversion_guidance,
        field_report,
        rule_versions,
        registry=registry,
    )
    write_json(output_manifest, manifest)
    write_jsonl(output_mappings, mappings)
    write_json(output_rule_versions, rule_versions)
    write_json(output_registry, registry)
    write_jsonl(output_conversion_guidance, conversion_guidance)
    write_jsonl(output_field_report, field_report)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build KMFA S07-P2 WPS file adapter metadata.")
    parser.add_argument("--output-manifest", type=Path, default=DEFAULT_OUTPUT_MANIFEST)
    parser.add_argument("--output-mappings", type=Path, default=DEFAULT_OUTPUT_MAPPINGS)
    parser.add_argument("--output-rule-versions", type=Path, default=DEFAULT_OUTPUT_RULE_VERSIONS)
    parser.add_argument("--output-registry", type=Path, default=DEFAULT_OUTPUT_REGISTRY)
    parser.add_argument("--output-conversion-guidance", type=Path, default=DEFAULT_OUTPUT_CONVERSION_GUIDANCE)
    parser.add_argument("--output-field-report", type=Path, default=DEFAULT_OUTPUT_FIELD_REPORT)
    parser.add_argument("--generated-at")
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args(argv)

    manifest, mappings, conversion_guidance, field_report, rule_versions = build_default_wps_adapter(
        generated_at=args.generated_at
    )
    if not args.check_only:
        write_outputs(
            manifest,
            mappings,
            conversion_guidance,
            field_report,
            rule_versions,
            output_manifest=args.output_manifest,
            output_mappings=args.output_mappings,
            output_rule_versions=args.output_rule_versions,
            output_registry=args.output_registry,
            output_conversion_guidance=args.output_conversion_guidance,
            output_field_report=args.output_field_report,
        )
    print(
        "PASS: KMFA S07-P2 WPS adapter built "
        f"(exports={manifest['summary']['source_export_type_count']}, "
        f"field_mappings={manifest['summary']['field_mapping_count']}, "
        f"conversion_guidance={manifest['summary']['conversion_guidance_count']}, "
        f"rule_versions={manifest['summary']['mapping_rule_version_count']}, "
        "formal_report_allowed=false)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
