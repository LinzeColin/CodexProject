#!/usr/bin/env python3
"""Install reviewed OCR owner decision corrections into private runtime.

Dry-run is the default. The tool writes only the private owner decision
manifest, and only after the owner-reviewed draft has complete required fields
and the operator passes an explicit acknowledgement flag.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


DECISION_SCOPE = "ocr_fact_candidate_owner_worklist_validation_only"
SOURCE_ARTIFACT = "ocr_fact_candidate_owner_worklist.csv"
PRIVATE_DECISION_PREFIX = Path(
    "KMFA/metadata/fund_weekly_analysis/private_runtime/ocr_fact_candidate_owner_decisions"
)
XLSX_NS = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
VALIDATION_REPORT_FIELDS = [
    "input_row_number",
    "fact_candidate_id",
    "candidate_metric",
    "source_evidence_id",
    "source_ocr_text_relative_path",
    "source_ocr_text_excerpt",
    "source_ocr_excerpt_focus_status",
    "source_ocr_excerpt_line_range",
    "source_ocr_excerpt_focus_line_number",
    "source_ocr_excerpt_match_value",
    "business_date",
    "amount",
    "currency",
    "owner_authorization_decision",
    "owner_corrected_company",
    "owner_corrected_bank",
    "required_owner_fields",
    "missing_owner_fields",
    "decision_validation_status",
    "recommended_owner_action",
    "owner_decision_manifest_write_allowed",
    "fund_ledger_write_allowed",
    "financial_fact_promoted",
    "management_conclusion_allowed",
]
OWNER_DECISION_CONTEXT_FIELDS = [
    "source_evidence_id",
    "source_ocr_text_relative_path",
    "source_ocr_text_excerpt",
    "source_ocr_excerpt_focus_status",
    "source_ocr_excerpt_line_range",
    "source_ocr_excerpt_focus_line_number",
    "source_ocr_excerpt_match_value",
    "business_date",
    "amount",
    "currency",
]


def emit(payload: dict) -> None:
    print(json.dumps(payload, ensure_ascii=False))


def default_run_dir(repo_root: Path, run_id: str) -> Path:
    return repo_root / "KMFA/metadata/fund_weekly_analysis/private_runtime/runs" / run_id


def default_draft_path(repo_root: Path, run_id: str) -> Path:
    return default_run_dir(repo_root, run_id) / "ocr_fact_owner_decision_correction_draft.json"


def candidate_template_path(repo_root: Path, run_id: str) -> Path:
    return default_run_dir(repo_root, run_id) / "ocr_fact_candidate_owner_decision_template.json"


def default_output_relative_path(run_id: str) -> str:
    return str(PRIVATE_DECISION_PREFIX / f"{run_id}.json")


def default_validation_report_relative_path(run_id: str) -> str:
    return str(
        Path("KMFA/metadata/fund_weekly_analysis/private_runtime/runs")
        / run_id
        / "ocr_fact_candidate_owner_decision_intake_validation_report.csv"
    )


def safe_relative_path(value: str) -> Path:
    path = Path(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise ValueError("output_decision_manifest_relative_path must be a safe relative path")
    return path


def load_draft(path: Path) -> dict:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError("draft_missing") from exc
    except json.JSONDecodeError as exc:
        raise ValueError("draft_invalid_json") from exc
    if not isinstance(payload, dict):
        raise ValueError("draft_invalid_schema")
    return payload


def load_csv_draft(path: Path, run_id: str) -> dict:
    try:
        with path.open(encoding="utf-8-sig", newline="") as f:
            rows = list(csv.DictReader(f))
    except FileNotFoundError as exc:
        raise ValueError("draft_missing") from exc
    except csv.Error as exc:
        raise ValueError("draft_invalid_csv") from exc
    if not rows:
        raise ValueError("draft_has_no_owner_decisions")
    decisions: list[dict] = []
    for index, row in enumerate(rows, 1):
        if not isinstance(row, dict):
            raise ValueError(f"draft_invalid_schema:csv_row[{index}]")
        decision = {
            "input_row_number": str(index + 1),
            "fact_candidate_id": str(row.get("fact_candidate_id", "")),
            "candidate_metric": str(row.get("candidate_metric", "")),
            "owner_authorization_decision": str(row.get("owner_authorization_decision", "")),
            "owner_corrected_company": str(row.get("owner_corrected_company", "")),
            "owner_corrected_bank": str(row.get("owner_corrected_bank", "")),
            "required_owner_fields": str(row.get("required_owner_fields", "")),
            "owner_note": str(row.get("owner_note", "")),
        }
        for field in OWNER_DECISION_CONTEXT_FIELDS:
            decision[field] = str(row.get(field, ""))
        decisions.append(decision)
    return {
        "decision_manifest_version": "1",
        "run_id": run_id,
        "decision_scope": DECISION_SCOPE,
        "draft_status": "owner_decision_csv_intake",
        "generated_from": path.name,
        "source_artifact": SOURCE_ARTIFACT,
        "output_decision_manifest_relative_path": default_output_relative_path(run_id),
        "financial_fact_promotion_allowed": False,
        "fund_ledger_write_allowed": False,
        "management_conclusion_allowed": False,
        "owner_decisions": decisions,
    }


def column_index(cell_ref: str) -> int:
    letters = "".join(ch for ch in cell_ref if ch.isalpha())
    if not letters:
        return 0
    index = 0
    for char in letters:
        index = index * 26 + (ord(char.upper()) - 64)
    return index - 1


def xlsx_shared_strings(workbook: zipfile.ZipFile) -> list[str]:
    try:
        root = ET.fromstring(workbook.read("xl/sharedStrings.xml"))
    except KeyError:
        return []
    strings: list[str] = []
    for item in root.findall("x:si", XLSX_NS):
        strings.append("".join(node.text or "" for node in item.findall(".//x:t", XLSX_NS)))
    return strings


def xlsx_cell_text(cell: ET.Element, shared_strings: list[str]) -> str:
    if cell.attrib.get("t") == "inlineStr":
        return "".join(node.text or "" for node in cell.findall(".//x:t", XLSX_NS))
    value = cell.find("x:v", XLSX_NS)
    if value is None or value.text is None:
        return ""
    if cell.attrib.get("t") == "s":
        try:
            return shared_strings[int(value.text)]
        except (IndexError, ValueError) as exc:
            raise ValueError("draft_invalid_xlsx:shared_string_index") from exc
    return value.text


def load_xlsx_rows(path: Path) -> list[dict]:
    try:
        with zipfile.ZipFile(path) as workbook:
            shared_strings = xlsx_shared_strings(workbook)
            sheet = ET.fromstring(workbook.read("xl/worksheets/sheet1.xml"))
    except FileNotFoundError as exc:
        raise ValueError("draft_missing") from exc
    except (KeyError, zipfile.BadZipFile, ET.ParseError) as exc:
        raise ValueError("draft_invalid_xlsx") from exc

    table: list[list[str]] = []
    for row in sheet.findall(".//x:sheetData/x:row", XLSX_NS):
        values: list[str] = []
        for cell in row.findall("x:c", XLSX_NS):
            index = column_index(cell.attrib.get("r", ""))
            while len(values) <= index:
                values.append("")
            values[index] = xlsx_cell_text(cell, shared_strings)
        if values:
            table.append(values)
    if len(table) < 2:
        raise ValueError("draft_has_no_owner_decisions")
    header = [value.strip() for value in table[0]]
    rows: list[dict] = []
    for raw_row in table[1:]:
        if not any(value.strip() for value in raw_row):
            continue
        rows.append({
            header[index]: raw_row[index] if index < len(raw_row) else ""
            for index in range(len(header))
            if header[index]
        })
    if not rows:
        raise ValueError("draft_has_no_owner_decisions")
    return rows


def load_xlsx_draft(path: Path, run_id: str) -> dict:
    rows = load_xlsx_rows(path)
    decisions: list[dict] = []
    for index, row in enumerate(rows, 1):
        if not isinstance(row, dict):
            raise ValueError(f"draft_invalid_schema:xlsx_row[{index}]")
        decision = {
            "input_row_number": str(index + 1),
            "fact_candidate_id": str(row.get("fact_candidate_id", "")),
            "candidate_metric": str(row.get("candidate_metric", "")),
            "owner_authorization_decision": str(row.get("owner_authorization_decision", "")),
            "owner_corrected_company": str(row.get("owner_corrected_company", "")),
            "owner_corrected_bank": str(row.get("owner_corrected_bank", "")),
            "required_owner_fields": str(row.get("required_owner_fields", "")),
            "owner_note": str(row.get("owner_note", "")),
        }
        for field in OWNER_DECISION_CONTEXT_FIELDS:
            decision[field] = str(row.get(field, ""))
        decisions.append(decision)
    return {
        "decision_manifest_version": "1",
        "run_id": run_id,
        "decision_scope": DECISION_SCOPE,
        "draft_status": "owner_decision_xlsx_intake",
        "generated_from": path.name,
        "source_artifact": SOURCE_ARTIFACT,
        "output_decision_manifest_relative_path": default_output_relative_path(run_id),
        "financial_fact_promotion_allowed": False,
        "fund_ledger_write_allowed": False,
        "management_conclusion_allowed": False,
        "owner_decisions": decisions,
    }


def resolve_default_draft_path(repo_root: Path, run_id: str) -> Path:
    correction_path = default_draft_path(repo_root, run_id)
    template_path = candidate_template_path(repo_root, run_id)
    try:
        correction_draft = load_draft(correction_path)
    except ValueError:
        return template_path if template_path.exists() else correction_path
    if not correction_draft.get("owner_decisions") and template_path.exists():
        return template_path
    return correction_path


def required_fields_from(decision: dict) -> list[str]:
    raw = str(decision.get("required_owner_fields", ""))
    return [field.strip() for field in raw.split(",") if field.strip()]


def validate_draft(draft: dict, run_id: str) -> tuple[dict, list[dict]]:
    required = {
        "decision_manifest_version": "1",
        "run_id": run_id,
        "decision_scope": DECISION_SCOPE,
        "source_artifact": SOURCE_ARTIFACT,
        "financial_fact_promotion_allowed": False,
        "fund_ledger_write_allowed": False,
        "management_conclusion_allowed": False,
    }
    for key, expected in required.items():
        if draft.get(key) != expected:
            raise ValueError(f"draft_invalid_schema:{key}")
    output_relative_path = draft.get("output_decision_manifest_relative_path")
    if output_relative_path != default_output_relative_path(run_id):
        raise ValueError("draft_invalid_schema:output_decision_manifest_relative_path")
    output_path = safe_relative_path(str(output_relative_path))
    if output_path.parent != PRIVATE_DECISION_PREFIX:
        raise ValueError("draft_invalid_schema:output_decision_manifest_relative_path")

    raw_decisions = draft.get("owner_decisions")
    if not isinstance(raw_decisions, list) or not raw_decisions:
        raise ValueError("draft_has_no_owner_decisions")

    seen_ids: set[str] = set()
    decisions: list[dict] = []
    validation_rows: list[dict] = []
    missing_values: list[str] = []
    not_approved: list[str] = []
    for index, decision in enumerate(raw_decisions, 1):
        if not isinstance(decision, dict):
            raise ValueError(f"draft_invalid_schema:owner_decisions[{index}]")
        fact_candidate_id = str(decision.get("fact_candidate_id", ""))
        candidate_metric = str(decision.get("candidate_metric", ""))
        if not fact_candidate_id or not candidate_metric:
            raise ValueError(f"draft_invalid_schema:owner_decisions[{index}]")
        if fact_candidate_id in seen_ids:
            raise ValueError(f"draft_invalid_schema:duplicate_fact_candidate_id:{fact_candidate_id}")
        seen_ids.add(fact_candidate_id)
        owner_decision = str(decision.get("owner_authorization_decision", ""))
        if owner_decision != "approve_for_review_authorization":
            not_approved.append(fact_candidate_id)
        required_owner_fields = required_fields_from(decision)
        if not required_owner_fields and draft.get("draft_status") == "owner_decision_correction_manifest_draft":
            raise ValueError(f"draft_invalid_schema:required_owner_fields:{fact_candidate_id}")
        missing_fields: list[str] = []
        for field in required_owner_fields:
            if not str(decision.get(field, "")).strip():
                missing_fields.append(field)
                if field not in missing_values:
                    missing_values.append(field)
        if missing_fields:
            validation_status = "blocked_missing_owner_values"
            recommended_action = "Fill required owner fields before dry-run can be ready"
        elif owner_decision != "approve_for_review_authorization":
            validation_status = "blocked_owner_decision_not_approved"
            recommended_action = "Set owner_authorization_decision to approve_for_review_authorization or remove the row"
        else:
            validation_status = "ready_for_private_owner_decision_manifest_no_write"
            recommended_action = "Ready for validation-only manifest apply if operator explicitly authorizes apply"
        validation_rows.append({
            "input_row_number": str(decision.get("input_row_number", index + 1)),
            "fact_candidate_id": fact_candidate_id,
            "candidate_metric": candidate_metric,
            "source_evidence_id": str(decision.get("source_evidence_id", "")),
            "source_ocr_text_relative_path": str(decision.get("source_ocr_text_relative_path", "")),
            "source_ocr_text_excerpt": str(decision.get("source_ocr_text_excerpt", "")),
            "source_ocr_excerpt_focus_status": str(decision.get("source_ocr_excerpt_focus_status", "")),
            "source_ocr_excerpt_line_range": str(decision.get("source_ocr_excerpt_line_range", "")),
            "source_ocr_excerpt_focus_line_number": str(decision.get("source_ocr_excerpt_focus_line_number", "")),
            "source_ocr_excerpt_match_value": str(decision.get("source_ocr_excerpt_match_value", "")),
            "business_date": str(decision.get("business_date", "")),
            "amount": str(decision.get("amount", "")),
            "currency": str(decision.get("currency", "")),
            "owner_authorization_decision": owner_decision,
            "owner_corrected_company": str(decision.get("owner_corrected_company", "")),
            "owner_corrected_bank": str(decision.get("owner_corrected_bank", "")),
            "required_owner_fields": ",".join(required_owner_fields),
            "missing_owner_fields": ",".join(missing_fields),
            "decision_validation_status": validation_status,
            "recommended_owner_action": recommended_action,
            "owner_decision_manifest_write_allowed": "false",
            "fund_ledger_write_allowed": "false",
            "financial_fact_promoted": "false",
            "management_conclusion_allowed": "false",
        })
        decisions.append({
            "fact_candidate_id": fact_candidate_id,
            "candidate_metric": candidate_metric,
            "owner_authorization_decision": owner_decision,
            "owner_corrected_company": str(decision.get("owner_corrected_company", "")),
            "owner_corrected_bank": str(decision.get("owner_corrected_bank", "")),
            "owner_note": str(decision.get("owner_note", "")),
        })
    return (
        {
            "output_relative_path": str(output_path),
            "validation_report_relative_path": default_validation_report_relative_path(run_id),
            "missing_owner_values": missing_values,
            "not_approved_fact_candidate_ids": not_approved,
            "validation_rows": validation_rows,
        },
        decisions,
    )


def build_manifest(run_id: str, decisions: list[dict]) -> dict:
    return {
        "decision_manifest_version": "1",
        "run_id": run_id,
        "decision_scope": DECISION_SCOPE,
        "source_artifact": SOURCE_ARTIFACT,
        "financial_fact_promotion_allowed": False,
        "fund_ledger_write_allowed": False,
        "management_conclusion_allowed": False,
        "owner_decisions": decisions,
    }


def write_validation_report(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=VALIDATION_REPORT_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=os.environ.get("KMFA_REPO_ROOT", "."))
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--draft-path", default="")
    parser.add_argument("--draft-csv-path", default="")
    parser.add_argument("--draft-xlsx-path", default="")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--acknowledge-owner-reviewed-values", action="store_true")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).expanduser().resolve()
    selected_draft_args = [value for value in (args.draft_path, args.draft_csv_path, args.draft_xlsx_path) if value]
    if len(selected_draft_args) > 1:
        emit({
            "status": "INVALID_ARGUMENTS",
            "run_id": args.run_id,
            "reason": "choose only one of --draft-path, --draft-csv-path, or --draft-xlsx-path",
            "apply_performed": False,
            "financial_fact_promotion_allowed": False,
            "fund_ledger_write_allowed": False,
            "management_conclusion_allowed": False,
        })
        return 2
    draft_format = "xlsx" if args.draft_xlsx_path else "csv" if args.draft_csv_path else "json"
    draft_path = (
        Path(args.draft_xlsx_path or args.draft_csv_path or args.draft_path).expanduser().resolve()
        if selected_draft_args
        else resolve_default_draft_path(repo_root, args.run_id)
    )
    try:
        if args.draft_xlsx_path:
            draft = load_xlsx_draft(draft_path, args.run_id)
        elif args.draft_csv_path:
            draft = load_csv_draft(draft_path, args.run_id)
        else:
            draft = load_draft(draft_path)
        validation, decisions = validate_draft(draft, args.run_id)
    except ValueError as exc:
        reason = str(exc)
        status = "DRAFT_MISSING" if reason == "draft_missing" else "INVALID_DRAFT_SCHEMA"
        emit({
            "status": status,
            "run_id": args.run_id,
            "draft_path": str(draft_path),
            "draft_format": draft_format,
            "reason": reason,
            "apply_performed": False,
            "financial_fact_promotion_allowed": False,
            "fund_ledger_write_allowed": False,
            "management_conclusion_allowed": False,
        })
        return 2

    base_payload = {
        "run_id": args.run_id,
        "draft_path": str(draft_path),
        "draft_format": draft_format,
        "output_decision_manifest_relative_path": validation["output_relative_path"],
        "output_decision_manifest_path": str(repo_root / validation["output_relative_path"]),
        "validation_report_relative_path": validation["validation_report_relative_path"],
        "validation_report_path": str(repo_root / validation["validation_report_relative_path"]),
        "validation_report_row_count": len(validation["validation_rows"]),
        "owner_decision_count": len(decisions),
        "financial_fact_promotion_allowed": False,
        "fund_ledger_write_allowed": False,
        "management_conclusion_allowed": False,
    }
    write_validation_report(repo_root / validation["validation_report_relative_path"], validation["validation_rows"])
    if validation["missing_owner_values"]:
        emit({
            **base_payload,
            "status": "BLOCKED_OWNER_VALUES_MISSING",
            "missing_owner_values": validation["missing_owner_values"],
            "apply_performed": False,
        })
        return 3
    if validation["not_approved_fact_candidate_ids"]:
        emit({
            **base_payload,
            "status": "BLOCKED_OWNER_DECISION_NOT_APPROVED",
            "not_approved_fact_candidate_ids": validation["not_approved_fact_candidate_ids"],
            "apply_performed": False,
        })
        return 3
    if args.apply and not args.acknowledge_owner_reviewed_values:
        emit({
            **base_payload,
            "status": "ACK_REQUIRED",
            "apply_performed": False,
        })
        return 2

    output_path = repo_root / validation["output_relative_path"]
    if not args.apply:
        emit({
            **base_payload,
            "status": "READY_DRY_RUN",
            "apply_performed": False,
        })
        return 0
    if output_path.exists():
        emit({
            **base_payload,
            "status": "TARGET_EXISTS",
            "apply_performed": False,
        })
        return 4

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(build_manifest(args.run_id, decisions), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    emit({
        **base_payload,
        "status": "APPLIED",
        "apply_performed": True,
    })
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
