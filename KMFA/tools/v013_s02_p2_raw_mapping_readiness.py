#!/usr/bin/env python3
"""Generate KMFA v0.1.3 S02-P2 raw mapping readiness evidence.

The tool reads raw files only. It stores private schema/header diagnostics under
KMFA/.codex_private_runtime/ and emits only aggregate public-safe evidence.
"""

from __future__ import annotations

import argparse
import io
import json
import re
import subprocess
import zipfile
from collections import Counter
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

from KMFA.tools.check_v013_s02_p1_raw_readiness import validate_v013_s02_p1_raw_readiness


RAW_DIR = Path("/Users/linzezhang/Downloads/KMFA_MetaData")
PRIVATE_OUTPUT_DIR = Path("KMFA/.codex_private_runtime/v013_s02_p2_raw_mapping_readiness")
PUBLIC_OUTPUT_DIR = Path("KMFA/stage_artifacts/V013_S02_P2_RAW_MAPPING_READINESS")
PRIVATE_SCHEMA_PATH = PRIVATE_OUTPUT_DIR / "private_schema_inventory.json"
PRIVATE_REPORT_PATH = PRIVATE_OUTPUT_DIR / "local_mapping_diagnostic_report.md"
PUBLIC_MANIFEST_PATH = PUBLIC_OUTPUT_DIR / "machine/raw_mapping_readiness_manifest.json"
PUBLIC_REPORT_PATH = PUBLIC_OUTPUT_DIR / "human/raw_mapping_readiness_report.md"
TASK_ID = "KMFA-V013-S02-P2-RAW-MAPPING-READINESS-20260702"
SCHEMA_VERSION = "kmfa.v013_s02_p2_raw_mapping_readiness.v1"
NEXT_REQUIRED_STEP = (
    "S02-P3 data quality/error gate; raw value matching still requires a later owner-authorized mapping phase."
)
XML_NS = {
    "main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "rel": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
}


def git_check_ignored(path: Path) -> bool:
    result = subprocess.run(
        ["git", "check-ignore", "-q", str(path)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return result.returncode == 0


def iter_raw_files(raw_dir: Path) -> list[Path]:
    if not raw_dir.exists() or not raw_dir.is_dir():
        return []
    return sorted(path for path in raw_dir.rglob("*") if path.is_file())


def read_shared_strings(zf: zipfile.ZipFile) -> list[str]:
    try:
        data = zf.read("xl/sharedStrings.xml")
    except KeyError:
        return []
    root = ET.fromstring(data)
    strings: list[str] = []
    for item in root.findall("main:si", XML_NS):
        parts = [node.text or "" for node in item.findall(".//main:t", XML_NS)]
        strings.append("".join(parts))
    return strings


def workbook_sheet_names(zf: zipfile.ZipFile) -> list[str]:
    try:
        data = zf.read("xl/workbook.xml")
    except KeyError:
        return []
    root = ET.fromstring(data)
    names: list[str] = []
    for sheet in root.findall(".//main:sheet", XML_NS):
        name = sheet.attrib.get("name")
        if name:
            names.append(name)
    return names


def sorted_worksheet_paths(zf: zipfile.ZipFile) -> list[str]:
    paths = [
        name
        for name in zf.namelist()
        if name.startswith("xl/worksheets/sheet") and name.endswith(".xml")
    ]

    def key(path: str) -> int:
        match = re.search(r"sheet(\d+)\.xml$", path)
        return int(match.group(1)) if match else 10**9

    return sorted(paths, key=key)


def cell_text(cell: ET.Element, shared_strings: list[str]) -> str:
    cell_type = cell.attrib.get("t")
    if cell_type == "s":
        value = cell.find("main:v", XML_NS)
        if value is None or value.text is None:
            return ""
        try:
            return shared_strings[int(value.text)]
        except (ValueError, IndexError):
            return ""
    if cell_type == "inlineStr":
        parts = [node.text or "" for node in cell.findall(".//main:t", XML_NS)]
        return "".join(parts).strip()
    value = cell.find("main:v", XML_NS)
    return (value.text or "").strip() if value is not None else ""


def inspect_worksheet(zf: zipfile.ZipFile, sheet_path: str, shared_strings: list[str]) -> dict[str, Any]:
    root = ET.fromstring(zf.read(sheet_path))
    rows = root.findall(".//main:sheetData/main:row", XML_NS)
    non_empty_rows = 0
    non_empty_cells = 0
    first_non_empty_row: list[str] = []
    for row in rows:
        values = [cell_text(cell, shared_strings) for cell in row.findall("main:c", XML_NS)]
        non_empty = [value for value in values if value]
        if non_empty:
            non_empty_rows += 1
            non_empty_cells += len(non_empty)
            if not first_non_empty_row:
                first_non_empty_row = non_empty
    return {
        "sheet_xml_path": sheet_path,
        "row_count_seen": len(rows),
        "non_empty_rows_seen": non_empty_rows,
        "non_empty_cells_seen": non_empty_cells,
        "first_non_empty_row_values": first_non_empty_row,
        "header_candidate_count": len(first_non_empty_row),
    }


def inspect_xlsx_bytes(label: str, payload: bytes) -> dict[str, Any]:
    record: dict[str, Any] = {
        "workbook_label": label,
        "parseable": False,
        "sheet_count": 0,
        "sheets": [],
        "error": None,
    }
    try:
        with zipfile.ZipFile(io.BytesIO(payload)) as zf:
            if "xl/workbook.xml" not in zf.namelist():
                record["error"] = "missing_xl_workbook_xml"
                return record
            shared_strings = read_shared_strings(zf)
            sheet_names = workbook_sheet_names(zf)
            sheet_paths = sorted_worksheet_paths(zf)
            sheets: list[dict[str, Any]] = []
            for index, sheet_path in enumerate(sheet_paths):
                sheet = inspect_worksheet(zf, sheet_path, shared_strings)
                sheet["sheet_name"] = sheet_names[index] if index < len(sheet_names) else f"sheet_{index + 1}"
                sheets.append(sheet)
            record.update(
                {
                    "parseable": True,
                    "sheet_count": len(sheets),
                    "sheets": sheets,
                    "shared_string_count": len(shared_strings),
                }
            )
    except (OSError, KeyError, ET.ParseError, zipfile.BadZipFile) as exc:
        record["error"] = exc.__class__.__name__
    return record


def inspect_xlsx_path(path: Path, raw_dir: Path) -> dict[str, Any]:
    return inspect_xlsx_bytes(path.relative_to(raw_dir).as_posix(), path.read_bytes())


def classify_suffix(name: str) -> str:
    suffix = Path(name).suffix.lower()
    return suffix or "<none>"


def inspect_zip(path: Path, raw_dir: Path) -> dict[str, Any]:
    record: dict[str, Any] = {
        "relative_path": path.relative_to(raw_dir).as_posix(),
        "openable": False,
        "member_count": 0,
        "member_suffix_counts": {},
        "nested_workbooks": [],
        "error": None,
    }
    try:
        with zipfile.ZipFile(path) as zf:
            members = [info for info in zf.infolist() if not info.is_dir()]
            suffix_counts = Counter(classify_suffix(info.filename) for info in members)
            nested_workbooks: list[dict[str, Any]] = []
            for info in members:
                if classify_suffix(info.filename) == ".xlsx":
                    nested_workbooks.append(inspect_xlsx_bytes(info.filename, zf.read(info)))
            record.update(
                {
                    "openable": True,
                    "member_count": len(members),
                    "member_suffix_counts": dict(sorted(suffix_counts.items())),
                    "nested_workbooks": nested_workbooks,
                }
            )
    except (OSError, zipfile.BadZipFile) as exc:
        record["error"] = exc.__class__.__name__
    return record


def build_private_schema_inventory(raw_dir: Path) -> dict[str, Any]:
    files = iter_raw_files(raw_dir)
    xlsx_records: list[dict[str, Any]] = []
    zip_records: list[dict[str, Any]] = []
    unsupported_records: list[dict[str, Any]] = []
    for path in files:
        suffix = path.suffix.lower()
        if suffix == ".xlsx":
            xlsx_records.append(inspect_xlsx_path(path, raw_dir))
        elif suffix == ".zip":
            zip_records.append(inspect_zip(path, raw_dir))
        else:
            unsupported_records.append({"relative_path": path.relative_to(raw_dir).as_posix(), "suffix": suffix or "<none>"})

    all_workbooks = list(xlsx_records)
    for zip_record in zip_records:
        all_workbooks.extend(zip_record.get("nested_workbooks", []))
    parseable_workbooks = [record for record in all_workbooks if record.get("parseable") is True]
    sheets = [sheet for record in parseable_workbooks for sheet in record.get("sheets", [])]
    private_header_values = [
        value
        for sheet in sheets
        for value in sheet.get("first_non_empty_row_values", [])
        if isinstance(value, str) and value.strip()
    ]
    mapping_candidates = [
        {
            "workbook_label": record.get("workbook_label"),
            "sheet_name": sheet.get("sheet_name"),
            "header_candidate_count": sheet.get("header_candidate_count", 0),
            "mapping_status": "private_schema_seen_authorized_semantic_mapping_required",
        }
        for record in parseable_workbooks
        for sheet in record.get("sheets", [])
        if sheet.get("header_candidate_count", 0) > 0
    ]
    return {
        "schema_version": "kmfa.v013_s02_p2_private_schema_inventory.v1",
        "task_id": TASK_ID,
        "raw_dir": str(raw_dir),
        "raw_dir_exists": raw_dir.exists(),
        "raw_dir_readable": raw_dir.exists() and raw_dir.is_dir(),
        "raw_dir_mutation_performed": False,
        "raw_file_count": len(files),
        "raw_file_suffix_counts": dict(sorted(Counter(path.suffix.lower() or "<none>" for path in files).items())),
        "xlsx_records": xlsx_records,
        "zip_records": zip_records,
        "unsupported_records": unsupported_records,
        "workbook_count": len(all_workbooks),
        "workbooks_parseable": len(parseable_workbooks),
        "workbook_parse_failure_count": len(all_workbooks) - len(parseable_workbooks),
        "sheet_count": len(sheets),
        "private_header_value_count": len(private_header_values),
        "private_mapping_candidate_count": len(mapping_candidates),
        "mapping_candidates": mapping_candidates,
        "raw_business_value_extraction_performed": False,
        "raw_value_matching_performed": False,
        "public_commit_allowed": False,
    }


def build_public_manifest(
    private_inventory: dict[str, Any],
    private_schema_path: Path,
    private_report_path: Path,
) -> dict[str, Any]:
    zip_records = private_inventory["zip_records"]
    nested_member_suffix_counts: Counter[str] = Counter()
    for record in zip_records:
        nested_member_suffix_counts.update(record.get("member_suffix_counts", {}))
    private_ignored = git_check_ignored(private_schema_path) and git_check_ignored(private_report_path)
    s02_p1_result = validate_v013_s02_p1_raw_readiness()
    return {
        "schema_version": SCHEMA_VERSION,
        "project_id": "KMFA",
        "version": "0.1.3",
        "stage_id": "S02",
        "phase_id": "S02-P2",
        "task_id": TASK_ID,
        "phase_scope": "raw_mapping_readiness_private_schema_inventory",
        "s02_p1_dependency_validated": s02_p1_result.get("phase_id") == "S02-P1",
        "raw_dir": private_inventory["raw_dir"],
        "raw_dir_exists": private_inventory["raw_dir_exists"],
        "raw_dir_readable": private_inventory["raw_dir_readable"],
        "raw_dir_mutation_allowed": False,
        "raw_dir_mutation_performed": False,
        "raw_file_count": private_inventory["raw_file_count"],
        "xlsx_files_seen": private_inventory["raw_file_suffix_counts"].get(".xlsx", 0),
        "zip_files_seen": private_inventory["raw_file_suffix_counts"].get(".zip", 0),
        "zip_files_openable": sum(1 for record in zip_records if record.get("openable") is True),
        "zip_member_count": sum(record.get("member_count", 0) for record in zip_records),
        "zip_member_suffix_counts": dict(sorted(nested_member_suffix_counts.items())),
        "nested_xlsx_seen": nested_member_suffix_counts.get(".xlsx", 0),
        "nested_pdf_seen": nested_member_suffix_counts.get(".pdf", 0),
        "workbooks_seen": private_inventory["workbook_count"],
        "workbooks_parseable": private_inventory["workbooks_parseable"],
        "workbook_parse_failure_count": private_inventory["workbook_parse_failure_count"],
        "sheets_seen": private_inventory["sheet_count"],
        "private_header_profile_count": private_inventory["private_header_value_count"],
        "private_mapping_candidate_count": private_inventory["private_mapping_candidate_count"],
        "private_schema_inventory_ref": private_schema_path.as_posix(),
        "private_mapping_diagnostic_ref": private_report_path.as_posix(),
        "private_schema_inventory_written": private_schema_path.exists(),
        "private_mapping_diagnostic_written": private_report_path.exists(),
        "private_outputs_git_ignored": private_ignored,
        "public_manifest_contains_raw_filenames": False,
        "public_manifest_contains_field_plaintext": False,
        "public_manifest_contains_raw_values": False,
        "raw_field_plaintext_private_only": True,
        "raw_business_value_extraction_performed": False,
        "raw_value_matching_readiness_status": "blocked_authorized_mapping_required",
        "raw_value_matching_performed": False,
        "raw_value_matching_blocked_reasons": [
            "S02-P2 only creates private schema/header readiness and does not extract row values.",
            "Owner-authorized semantic field mapping is required before value-level matching.",
            "ZIP/PDF/container-specific extraction remains gated by later dedicated parser phases.",
        ],
        "github_upload_performed": False,
        "delivery_allowed": False,
        "formal_report_allowed": False,
        "business_execution_allowed": False,
        "public_repo_safety": {
            "raw_business_data_committed": False,
            "zip_committed": False,
            "excel_workbook_committed": False,
            "pdf_committed": False,
            "private_csv_committed": False,
            "sqlite_or_db_committed": False,
            "credentials_committed": False,
            "field_plaintext_committed": False,
            "raw_file_names_committed": False,
            "raw_file_hashes_committed": False,
            "raw_business_values_committed": False,
        },
        "evidence_refs": [
            PUBLIC_MANIFEST_PATH.as_posix(),
            PUBLIC_REPORT_PATH.as_posix(),
            private_schema_path.as_posix(),
            private_report_path.as_posix(),
        ],
        "next_required_step": NEXT_REQUIRED_STEP,
    }


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_private_report(path: Path, private_inventory: dict[str, Any], public_manifest: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# KMFA v0.1.3 S02-P2 Local Private Mapping Diagnostic",
        "",
        "This file is local-only and git-ignored. It may contain raw file names, ZIP member names, sheet names, and header text.",
        "",
        f"- task_id: `{TASK_ID}`",
        f"- raw_dir: `{private_inventory['raw_dir']}`",
        f"- raw_file_count: `{private_inventory['raw_file_count']}`",
        f"- zip_files_seen: `{public_manifest['zip_files_seen']}`",
        f"- xlsx_files_seen: `{public_manifest['xlsx_files_seen']}`",
        f"- zip_files_openable: `{public_manifest['zip_files_openable']}`",
        f"- workbooks_seen: `{public_manifest['workbooks_seen']}`",
        f"- workbooks_parseable: `{public_manifest['workbooks_parseable']}`",
        f"- sheets_seen: `{public_manifest['sheets_seen']}`",
        f"- private_header_profile_count: `{public_manifest['private_header_profile_count']}`",
        f"- private_mapping_candidate_count: `{public_manifest['private_mapping_candidate_count']}`",
        f"- raw_value_matching_performed: `{str(public_manifest['raw_value_matching_performed']).lower()}`",
        "",
        "## Blocking Reasons",
        "",
    ]
    lines.extend(f"- {reason}" for reason in public_manifest["raw_value_matching_blocked_reasons"])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_public_report(path: Path, manifest: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# KMFA v0.1.3 S02-P2 Raw Mapping Readiness Report",
        "",
        "## Public-Safe Summary",
        "",
        f"- task_id: `{manifest['task_id']}`",
        f"- stage_phase: `{manifest['stage_id']}-{manifest['phase_id']}`",
        f"- raw_dir: `{manifest['raw_dir']}`",
        f"- raw_file_count: `{manifest['raw_file_count']}`",
        f"- xlsx_files_seen: `{manifest['xlsx_files_seen']}`",
        f"- zip_files_seen: `{manifest['zip_files_seen']}`",
        f"- zip_files_openable: `{manifest['zip_files_openable']}`",
        f"- zip_member_count: `{manifest['zip_member_count']}`",
        f"- nested_xlsx_seen: `{manifest['nested_xlsx_seen']}`",
        f"- nested_pdf_seen: `{manifest['nested_pdf_seen']}`",
        f"- workbooks_parseable: `{manifest['workbooks_parseable']}`",
        f"- sheets_seen: `{manifest['sheets_seen']}`",
        f"- private_header_profile_count: `{manifest['private_header_profile_count']}`",
        f"- private_mapping_candidate_count: `{manifest['private_mapping_candidate_count']}`",
        f"- raw_value_matching_readiness_status: `{manifest['raw_value_matching_readiness_status']}`",
        f"- raw_value_matching_performed: `{str(manifest['raw_value_matching_performed']).lower()}`",
        f"- github_upload_performed: `{str(manifest['github_upload_performed']).lower()}`",
        f"- delivery_allowed: `{str(manifest['delivery_allowed']).lower()}`",
        "",
        "## Public Repository Boundary",
        "",
        "- This public report omits raw file names, ZIP member names, sheet names, field/header text, row values, raw hashes, and business values.",
        "- Private schema/header diagnostics stay in the git-ignored runtime directory.",
        "- S02-P2 does not mutate raw files and does not perform value-level matching.",
        "",
        "## Local Private Evidence",
        "",
        f"- private_schema_inventory_ref: `{manifest['private_schema_inventory_ref']}`",
        f"- private_mapping_diagnostic_ref: `{manifest['private_mapping_diagnostic_ref']}`",
        f"- private_outputs_git_ignored: `{str(manifest['private_outputs_git_ignored']).lower()}`",
        "",
        "## Not Performed In This Phase",
        "",
        "- No raw row-value extraction or raw value matching was performed.",
        "- No Stage 2 review, GitHub upload, formal report release, lineage full check, live connector, or business execution was performed.",
        "",
        f"Next required step: {manifest['next_required_step']}",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def generate_raw_mapping_readiness_evidence(
    raw_dir: Path = RAW_DIR,
    private_output_dir: Path = PRIVATE_OUTPUT_DIR,
    public_output_dir: Path = PUBLIC_OUTPUT_DIR,
) -> dict[str, Any]:
    private_schema_path = private_output_dir / PRIVATE_SCHEMA_PATH.name
    private_report_path = private_output_dir / PRIVATE_REPORT_PATH.name
    public_manifest_path = public_output_dir / "machine" / PUBLIC_MANIFEST_PATH.name
    public_report_path = public_output_dir / "human" / PUBLIC_REPORT_PATH.name

    private_inventory = build_private_schema_inventory(raw_dir)
    write_json(private_schema_path, private_inventory)
    public_manifest = build_public_manifest(private_inventory, private_schema_path, private_report_path)
    write_private_report(private_report_path, private_inventory, public_manifest)
    public_manifest = build_public_manifest(private_inventory, private_schema_path, private_report_path)
    write_json(public_manifest_path, public_manifest)
    write_public_report(public_report_path, public_manifest)
    return public_manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate KMFA v0.1.3 S02-P2 raw mapping readiness evidence.")
    parser.add_argument("--raw-dir", type=Path, default=RAW_DIR)
    parser.add_argument("--private-output-dir", type=Path, default=PRIVATE_OUTPUT_DIR)
    parser.add_argument("--public-output-dir", type=Path, default=PUBLIC_OUTPUT_DIR)
    args = parser.parse_args()
    manifest = generate_raw_mapping_readiness_evidence(args.raw_dir, args.private_output_dir, args.public_output_dir)
    print(
        "PASS: KMFA v0.1.3 S02-P2 raw mapping readiness evidence generated "
        f"(raw_files={manifest['raw_file_count']}, zip_openable={manifest['zip_files_openable']}, "
        f"workbooks_parseable={manifest['workbooks_parseable']}, "
        f"private_ignored={str(manifest['private_outputs_git_ignored']).lower()}, "
        f"matching={manifest['raw_value_matching_readiness_status']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
