#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import posixpath
import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


NS = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
REL_NS = {"r": "http://schemas.openxmlformats.org/package/2006/relationships"}
OWNER_REVIEW_SHEET = "Owner Review"
REVIEW_SUMMARY_SHEET = "Review Summary"
OWNER_INPUT_FIELDS = [
    "owner_authorization_decision",
    "owner_corrected_company",
    "owner_corrected_bank",
    "owner_note",
]
LOCKED_EVIDENCE_FIELDS = [
    "review_batch_row_id",
    "source_ocr_text_excerpt",
    "owner_review_completion_status",
    "missing_owner_fields_current",
    "required_owner_fields",
    "management_conclusion_allowed",
]
WRITE_FLAG_FIELDS = [
    "fund_ledger_write_allowed",
    "financial_fact_promoted",
    "management_conclusion_allowed",
]


def emit(payload: dict) -> None:
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))


def base_payload(workbook_path: Path) -> dict:
    return {
        "status": "BLOCKED_OWNER_REVIEW_WORKBOOK",
        "workbook_path": str(workbook_path),
        "owner_review_sheet_present": False,
        "review_summary_sheet_present": False,
        "owner_review_sheet_protected": False,
        "review_summary_sheet_protected": False,
        "owner_input_cells_unlocked": False,
        "evidence_cells_locked": False,
        "owner_decision_validation_present": False,
        "write_flags_all_false": False,
        "owner_review_data_row_count": 0,
        "review_summary_data_row_count": 0,
        "apply_performed": False,
        "fund_ledger_write_allowed": False,
        "financial_fact_promoted": False,
        "management_conclusion_allowed": False,
        "failed_checks": [],
    }


def col_to_index(col: str) -> int:
    index = 0
    for char in col:
        index = index * 26 + (ord(char) - 64)
    return index


def index_to_col(index: int) -> str:
    letters = ""
    while index:
        index, remainder = divmod(index - 1, 26)
        letters = chr(65 + remainder) + letters
    return letters


def split_ref(ref: str) -> tuple[str, int]:
    match = re.fullmatch(r"([A-Z]+)([0-9]+)", ref)
    if not match:
        raise ValueError(f"invalid_cell_ref:{ref}")
    col, row = match.groups()
    return col, int(row)


def read_shared_strings(workbook: zipfile.ZipFile) -> list[str]:
    try:
        root = ET.fromstring(workbook.read("xl/sharedStrings.xml"))
    except KeyError:
        return []
    strings: list[str] = []
    for item in root.findall("x:si", NS):
        strings.append("".join(node.text or "" for node in item.findall(".//x:t", NS)))
    return strings


def workbook_sheet_paths(workbook: zipfile.ZipFile) -> dict[str, str]:
    workbook_root = ET.fromstring(workbook.read("xl/workbook.xml"))
    rel_root = ET.fromstring(workbook.read("xl/_rels/workbook.xml.rels"))
    rel_targets = {
        rel.attrib["Id"]: rel.attrib["Target"]
        for rel in rel_root.findall("r:Relationship", REL_NS)
        if "Id" in rel.attrib and "Target" in rel.attrib
    }
    paths: dict[str, str] = {}
    for sheet in workbook_root.findall(".//x:sheet", NS):
        name = sheet.attrib.get("name", "")
        rel_id = sheet.attrib.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id")
        target = rel_targets.get(rel_id or "")
        if not name or not target:
            continue
        target = target.lstrip("/")
        if not target.startswith("xl/"):
            target = posixpath.normpath(posixpath.join("xl", target))
        paths[name] = target
    return paths


def cell_text(cell: ET.Element, shared_strings: list[str]) -> str:
    inline_text = cell.find("x:is/x:t", NS)
    if inline_text is not None:
        return inline_text.text or ""
    value = cell.find("x:v", NS)
    if value is None or value.text is None:
        return ""
    if cell.attrib.get("t") == "s":
        try:
            return shared_strings[int(value.text)]
        except (ValueError, IndexError):
            return ""
    return value.text


def parse_sheet(
    workbook: zipfile.ZipFile,
    path: str,
    shared_strings: list[str],
) -> tuple[ET.Element, dict[str, dict[str, str]]]:
    root = ET.fromstring(workbook.read(path))
    cells: dict[str, dict[str, str]] = {}
    for cell in root.findall(".//x:c", NS):
        ref = cell.attrib.get("r", "")
        if not ref:
            continue
        formula = cell.find("x:f", NS)
        cells[ref] = {
            "value": cell_text(cell, shared_strings),
            "style": cell.attrib.get("s", "0"),
            "formula": formula.text or "" if formula is not None else "",
        }
    return root, cells


def data_row_count(root: ET.Element) -> int:
    row_numbers = []
    for row in root.findall(".//x:row", NS):
        try:
            row_numbers.append(int(row.attrib.get("r", "0")))
        except ValueError:
            continue
    if not row_numbers:
        return 0
    return max(0, max(row_numbers) - 1)


def header_map(cells: dict[str, dict[str, str]]) -> dict[str, str]:
    headers: dict[str, str] = {}
    for ref, cell in cells.items():
        col, row = split_ref(ref)
        if row == 1 and cell["value"]:
            headers[cell["value"]] = col
    return headers


def sheet_is_protected(root: ET.Element) -> bool:
    protection = root.find("x:sheetProtection", NS)
    return protection is not None and protection.attrib.get("sheet") in {"1", "true", "TRUE"}


def style_is_unlocked(styles_root: ET.Element, style_index: str) -> bool:
    try:
        index = int(style_index)
    except ValueError:
        return False
    styles = styles_root.findall("x:cellXfs/x:xf", NS)
    if index >= len(styles):
        return False
    protection = styles[index].find("x:protection", NS)
    return protection is not None and protection.attrib.get("locked") in {"0", "false", "FALSE"}


def fields_present(headers: dict[str, str], fields: list[str]) -> bool:
    return all(field in headers for field in fields)


def owner_input_cells_unlocked(
    cells: dict[str, dict[str, str]],
    headers: dict[str, str],
    styles_root: ET.Element,
) -> bool:
    if not fields_present(headers, OWNER_INPUT_FIELDS):
        return False
    for field in OWNER_INPUT_FIELDS:
        ref = f"{headers[field]}2"
        cell = cells.get(ref)
        if cell is None or not style_is_unlocked(styles_root, cell["style"]):
            return False
    return True


def evidence_cells_locked(
    cells: dict[str, dict[str, str]],
    headers: dict[str, str],
    styles_root: ET.Element,
) -> bool:
    if not fields_present(headers, LOCKED_EVIDENCE_FIELDS):
        return False
    for field in LOCKED_EVIDENCE_FIELDS:
        ref = f"{headers[field]}2"
        cell = cells.get(ref)
        if cell is None:
            return False
        if style_is_unlocked(styles_root, cell["style"]):
            return False
    return True


def owner_decision_validation_present(root: ET.Element) -> bool:
    for validation in root.findall(".//x:dataValidation", NS):
        formula = validation.find("x:formula1", NS)
        if formula is not None and "approve_for_review_authorization" in (formula.text or ""):
            return True
    return False


def flag_values_all_false(cells: dict[str, dict[str, str]], headers: dict[str, str], rows: int) -> bool:
    if not fields_present(headers, WRITE_FLAG_FIELDS):
        return False
    for field in WRITE_FLAG_FIELDS:
        col = headers[field]
        for row_number in range(2, rows + 2):
            value = cells.get(f"{col}{row_number}", {}).get("value", "")
            if value != "false":
                return False
    return True


def validate(workbook_path: Path) -> tuple[int, dict]:
    payload = base_payload(workbook_path)
    if not workbook_path.exists():
        payload["reason"] = "workbook_missing"
        payload["failed_checks"] = ["workbook_exists"]
        return 2, payload

    try:
        with zipfile.ZipFile(workbook_path) as workbook:
            shared_strings = read_shared_strings(workbook)
            sheet_paths = workbook_sheet_paths(workbook)
            payload["owner_review_sheet_present"] = OWNER_REVIEW_SHEET in sheet_paths
            payload["review_summary_sheet_present"] = REVIEW_SUMMARY_SHEET in sheet_paths
            if not payload["owner_review_sheet_present"]:
                payload["failed_checks"].append("owner_review_sheet_present")
            if not payload["review_summary_sheet_present"]:
                payload["failed_checks"].append("review_summary_sheet_present")
            if payload["failed_checks"]:
                return 2, payload

            styles_root = ET.fromstring(workbook.read("xl/styles.xml"))
            owner_root, owner_cells = parse_sheet(
                workbook,
                sheet_paths[OWNER_REVIEW_SHEET],
                shared_strings,
            )
            summary_root, summary_cells = parse_sheet(
                workbook,
                sheet_paths[REVIEW_SUMMARY_SHEET],
                shared_strings,
            )
            owner_headers = header_map(owner_cells)
            summary_headers = header_map(summary_cells)

            owner_rows = data_row_count(owner_root)
            summary_rows = data_row_count(summary_root)
            payload["owner_review_data_row_count"] = owner_rows
            payload["review_summary_data_row_count"] = summary_rows
            payload["owner_review_sheet_protected"] = sheet_is_protected(owner_root)
            payload["review_summary_sheet_protected"] = sheet_is_protected(summary_root)
            payload["owner_input_cells_unlocked"] = owner_rows > 0 and owner_input_cells_unlocked(
                owner_cells,
                owner_headers,
                styles_root,
            )
            payload["evidence_cells_locked"] = owner_rows > 0 and evidence_cells_locked(
                owner_cells,
                owner_headers,
                styles_root,
            )
            payload["owner_decision_validation_present"] = owner_decision_validation_present(owner_root)
            payload["write_flags_all_false"] = (
                owner_rows > 0
                and flag_values_all_false(owner_cells, owner_headers, owner_rows)
                and flag_values_all_false(summary_cells, summary_headers, summary_rows)
            )
    except (ET.ParseError, KeyError, OSError, zipfile.BadZipFile, ValueError) as exc:
        payload["reason"] = f"workbook_parse_failed:{exc}"
        payload["failed_checks"] = ["workbook_parse"]
        return 2, payload

    checks = [
        "owner_review_sheet_protected",
        "review_summary_sheet_protected",
        "owner_input_cells_unlocked",
        "evidence_cells_locked",
        "owner_decision_validation_present",
        "write_flags_all_false",
    ]
    payload["failed_checks"] = [check for check in checks if not payload[check]]
    if payload["owner_review_data_row_count"] <= 0:
        payload["failed_checks"].append("owner_review_data_row_count")
    if payload["review_summary_data_row_count"] <= 0:
        payload["failed_checks"].append("review_summary_data_row_count")

    if payload["failed_checks"]:
        return 2, payload
    payload["status"] = "OWNER_REVIEW_WORKBOOK_READY"
    return 0, payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workbook-path", required=True)
    args = parser.parse_args()
    workbook_path = Path(args.workbook_path).expanduser().resolve()
    exit_code, payload = validate(workbook_path)
    emit(payload)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
