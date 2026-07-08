#!/usr/bin/env python3
"""Export a small no-write owner decision review CSV from OCR owner worklist rows."""
from __future__ import annotations

import argparse
import csv
import json
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape


DEFAULT_OUTPUT_NAME = "ocr_fact_candidate_owner_decision_review_batch.csv"
DEFAULT_XLSX_OUTPUT_NAME = "ocr_fact_candidate_owner_decision_review_batch.xlsx"
WORKLIST_NAME = "ocr_fact_candidate_owner_worklist.csv"

OUTPUT_FIELDS = [
    "review_batch_row_id",
    "owner_worklist_id",
    "ocr_fact_evidence_review_queue_id",
    "fact_candidate_id",
    "candidate_metric",
    "source_evidence_id",
    "source_ocr_text_relative_path",
    "source_ocr_text_excerpt",
    "business_date",
    "amount",
    "currency",
    "company",
    "bank",
    "account_alias",
    "proposed_amount_role",
    "proposed_liquidity_tier",
    "proposed_flow_type",
    "owner_authorization_decision",
    "owner_corrected_company",
    "owner_corrected_bank",
    "owner_review_completion_status",
    "missing_owner_fields_current",
    "required_owner_fields",
    "owner_note",
    "fund_ledger_write_allowed",
    "financial_fact_promoted",
    "management_conclusion_allowed",
    "recommended_owner_action",
]


def emit(payload: dict) -> None:
    print(json.dumps(payload, ensure_ascii=False))


def run_dir(repo_root: Path, run_id: str) -> Path:
    return repo_root / "KMFA/metadata/fund_weekly_analysis/private_runtime/runs" / run_id


def safe_output_name(name: str) -> str:
    path = Path(name)
    if path.name != name or path.is_absolute() or name in {"", ".", ".."}:
        raise ValueError("output_name_must_be_a_plain_filename")
    if path.suffix.lower() != ".csv":
        raise ValueError("output_name_must_end_with_csv")
    return name


def safe_xlsx_output_name(name: str) -> str:
    path = Path(name)
    if path.name != name or path.is_absolute() or name in {"", ".", ".."}:
        raise ValueError("xlsx_output_name_must_be_a_plain_filename")
    if path.suffix.lower() != ".xlsx":
        raise ValueError("xlsx_output_name_must_end_with_xlsx")
    return name


def parse_metrics(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def read_worklist(path: Path) -> list[dict]:
    try:
        with path.open(encoding="utf-8-sig", newline="") as f:
            return list(csv.DictReader(f))
    except FileNotFoundError as exc:
        raise ValueError("owner_worklist_missing") from exc


def required_owner_fields(row: dict) -> str:
    missing = []
    if not str(row.get("company", "")).strip():
        missing.append("owner_corrected_company")
    if not str(row.get("bank", "")).strip():
        missing.append("owner_corrected_bank")
    return ",".join(missing)


def is_within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def ocr_excerpt(repo_root: Path, run_id: str, relative_path: str, limit: int = 600) -> str:
    raw = str(relative_path or "").strip()
    if not raw:
        return ""
    path = Path(raw)
    if path.is_absolute():
        candidates = [path]
    else:
        run_root = run_dir(repo_root, run_id)
        candidates = [
            run_root / path,
            repo_root / path,
        ]
    for candidate in candidates:
        resolved = candidate.expanduser().resolve()
        if not is_within(resolved, repo_root):
            continue
        if not resolved.is_file():
            continue
        try:
            text = resolved.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            return ""
        compact = " | ".join(line.strip() for line in text.splitlines() if line.strip())
        return compact[:limit]
    return ""


def review_completion_status(owner_decision: str, missing_fields: str) -> str:
    if missing_fields:
        return "blocked_missing_owner_values"
    if owner_decision != "approve_for_review_authorization":
        return "blocked_owner_decision_not_approved"
    return "ready_for_private_owner_decision_manifest_no_write"


def select_rows(rows: list[dict], metrics: list[str], limit_per_metric: int) -> list[dict]:
    if not metrics:
        selected = rows
        return selected if limit_per_metric <= 0 else selected[:limit_per_metric]
    selected: list[dict] = []
    for metric in metrics:
        metric_rows = [row for row in rows if row.get("candidate_metric") == metric]
        selected.extend(metric_rows if limit_per_metric <= 0 else metric_rows[:limit_per_metric])
    return selected


def build_review_rows(repo_root: Path, run_id: str, selected_rows: list[dict]) -> list[dict]:
    output_rows: list[dict] = []
    for row in selected_rows:
        owner_decision = "pending_owner_review"
        missing_fields = required_owner_fields(row)
        source_ocr_text_relative_path = row.get("source_ocr_text_relative_path", "")
        output_rows.append({
            "review_batch_row_id": f"OCROWNERREVIEWCSV-{run_id}-{len(output_rows) + 1:05d}",
            "owner_worklist_id": row.get("owner_worklist_id", ""),
            "ocr_fact_evidence_review_queue_id": row.get("ocr_fact_evidence_review_queue_id", ""),
            "fact_candidate_id": row.get("fact_candidate_id", ""),
            "candidate_metric": row.get("candidate_metric", ""),
            "source_evidence_id": row.get("source_evidence_id", ""),
            "source_ocr_text_relative_path": source_ocr_text_relative_path,
            "source_ocr_text_excerpt": ocr_excerpt(repo_root, run_id, source_ocr_text_relative_path),
            "business_date": row.get("business_date", ""),
            "amount": row.get("amount", ""),
            "currency": row.get("currency", ""),
            "company": row.get("company", ""),
            "bank": row.get("bank", ""),
            "account_alias": row.get("account_alias", ""),
            "proposed_amount_role": row.get("proposed_amount_role", ""),
            "proposed_liquidity_tier": row.get("proposed_liquidity_tier", ""),
            "proposed_flow_type": row.get("proposed_flow_type", ""),
            "owner_authorization_decision": owner_decision,
            "owner_corrected_company": "",
            "owner_corrected_bank": "",
            "owner_review_completion_status": review_completion_status(owner_decision, missing_fields),
            "missing_owner_fields_current": missing_fields,
            "required_owner_fields": missing_fields,
            "owner_note": "",
            "fund_ledger_write_allowed": "false",
            "financial_fact_promoted": "false",
            "management_conclusion_allowed": "false",
            "recommended_owner_action": (
                "Fill owner_authorization_decision and required owner fields, then run "
                "install_owner_decision_manifest.py --draft-csv-path as a dry-run first."
            ),
        })
    return output_rows


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def column_letter(index: int) -> str:
    letters = ""
    while index:
        index, remainder = divmod(index - 1, 26)
        letters = chr(65 + remainder) + letters
    return letters


def write_xlsx(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    strings: list[str] = []
    string_index: dict[str, int] = {}

    def string_id(value: object) -> int:
        text = str(value if value is not None else "")
        if text not in string_index:
            string_index[text] = len(strings)
            strings.append(text)
        return string_index[text]

    all_rows = [OUTPUT_FIELDS] + [[row.get(field, "") for field in OUTPUT_FIELDS] for row in rows]
    decision_col = column_letter(OUTPUT_FIELDS.index("owner_authorization_decision") + 1)
    company_col = column_letter(OUTPUT_FIELDS.index("owner_corrected_company") + 1)
    bank_col = column_letter(OUTPUT_FIELDS.index("owner_corrected_bank") + 1)
    missing_current_col = column_letter(OUTPUT_FIELDS.index("missing_owner_fields_current") + 1)
    required_col = column_letter(OUTPUT_FIELDS.index("required_owner_fields") + 1)
    note_col = column_letter(OUTPUT_FIELDS.index("owner_note") + 1)
    last_col = column_letter(len(OUTPUT_FIELDS))

    def missing_fields_formula(row_number: int) -> str:
        return (
            'TEXTJOIN(",",TRUE,'
            f'IF(AND(ISNUMBER(SEARCH("owner_corrected_company",${required_col}{row_number})),${company_col}{row_number}=""),'
            '"owner_corrected_company",""),'
            f'IF(AND(ISNUMBER(SEARCH("owner_corrected_bank",${required_col}{row_number})),${bank_col}{row_number}=""),'
            '"owner_corrected_bank",""))'
        )

    def status_formula(row_number: int) -> str:
        return (
            f'IF({missing_fields_formula(row_number)}<>"","blocked_missing_owner_values",'
            f'IF(${decision_col}{row_number}<>"approve_for_review_authorization",'
            '"blocked_owner_decision_not_approved","ready_for_private_owner_decision_manifest_no_write"))'
        )

    def formula_for(field: str, row_number: int) -> str:
        if field == "owner_review_completion_status":
            return status_formula(row_number)
        if field == "missing_owner_fields_current":
            return missing_fields_formula(row_number)
        return ""

    row_xml: list[str] = []
    for row_number, values in enumerate(all_rows, 1):
        cells: list[str] = []
        for column_number, value in enumerate(values, 1):
            cell_ref = f"{column_letter(column_number)}{row_number}"
            style = ' s="1"' if row_number == 1 else ""
            field = OUTPUT_FIELDS[column_number - 1]
            formula = formula_for(field, row_number) if row_number > 1 else ""
            if formula:
                cells.append(
                    f'<c r="{cell_ref}" t="str"><f>{escape(formula)}</f><v>{escape(str(value))}</v></c>'
                )
                continue
            cells.append(f'<c r="{cell_ref}" t="s"{style}><v>{string_id(value)}</v></c>')
        row_xml.append(f'<row r="{row_number}">{"".join(cells)}</row>')

    max_row = max(2, len(all_rows))
    validations = (
        '<dataValidations count="1">'
        f'<dataValidation type="list" allowBlank="0" showErrorMessage="1" sqref="{decision_col}2:{decision_col}{max_row}">'
        '<formula1>"pending_owner_review,approve_for_review_authorization,needs_correction,reject_candidate"</formula1>'
        '</dataValidation>'
        '</dataValidations>'
    )
    sheet_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        '<sheetViews><sheetView workbookViewId="0"><pane ySplit="1" topLeftCell="A2" activePane="bottomLeft" state="frozenSplit"/></sheetView></sheetViews>'
        '<cols>'
        '<col min="1" max="6" width="24" customWidth="1"/>'
        '<col min="7" max="16" width="18" customWidth="1"/>'
        f'<col min="{OUTPUT_FIELDS.index("owner_authorization_decision") + 1}" max="{OUTPUT_FIELDS.index("owner_note") + 1}" width="28" customWidth="1"/>'
        '<col min="22" max="24" width="18" customWidth="1"/>'
        '</cols>'
        f'<sheetData>{"".join(row_xml)}</sheetData>'
        f'<autoFilter ref="A1:{last_col}{max_row}"/>'
        f'<ignoredErrors><ignoredError sqref="{company_col}2:{note_col}{max_row}" numberStoredAsText="1"/></ignoredErrors>'
        f'{validations}'
        '</worksheet>'
    )
    shared_items = "".join(f'<si><t>{escape(text)}</t></si>' for text in strings)
    shared_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" count="{len(strings)}" uniqueCount="{len(strings)}">'
        f'{shared_items}</sst>'
    )
    workbook_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        '<sheets><sheet name="Owner Review" sheetId="1" r:id="rId1"/></sheets>'
        '</workbook>'
    )
    styles_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        '<fonts count="2"><font><sz val="11"/><name val="Arial"/></font><font><b/><sz val="11"/><name val="Arial"/></font></fonts>'
        '<fills count="1"><fill><patternFill patternType="none"/></fill></fills>'
        '<borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders>'
        '<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>'
        '<cellXfs count="2"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>'
        '<xf numFmtId="0" fontId="1" fillId="0" borderId="0" xfId="0" applyFont="1"/></cellXfs>'
        '<cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles>'
        '<dxfs count="0"/><tableStyles count="0" defaultTableStyle="TableStyleMedium2" defaultPivotStyle="PivotStyleLight16"/>'
        '</styleSheet>'
    )
    content_types = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
        '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        '<Override PartName="/xl/sharedStrings.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sharedStrings+xml"/>'
        '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
        '</Types>'
    )
    root_rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
        '</Relationships>'
    )
    workbook_rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>'
        '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
        '<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/sharedStrings" Target="sharedStrings.xml"/>'
        '</Relationships>'
    )
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as workbook:
        workbook.writestr("[Content_Types].xml", content_types)
        workbook.writestr("_rels/.rels", root_rels)
        workbook.writestr("xl/workbook.xml", workbook_xml)
        workbook.writestr("xl/_rels/workbook.xml.rels", workbook_rels)
        workbook.writestr("xl/worksheets/sheet1.xml", sheet_xml)
        workbook.writestr("xl/sharedStrings.xml", shared_xml)
        workbook.writestr("xl/styles.xml", styles_xml)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--metrics", default="")
    parser.add_argument("--limit-per-metric", type=int, default=5)
    parser.add_argument("--output-name", default=DEFAULT_OUTPUT_NAME)
    parser.add_argument("--xlsx", action="store_true")
    parser.add_argument("--xlsx-output-name", default=DEFAULT_XLSX_OUTPUT_NAME)
    args = parser.parse_args()

    repo_root = Path(args.repo_root).expanduser().resolve()
    try:
        output_name = safe_output_name(args.output_name)
        xlsx_output_name = safe_xlsx_output_name(args.xlsx_output_name)
        rows = read_worklist(run_dir(repo_root, args.run_id) / WORKLIST_NAME)
    except ValueError as exc:
        emit({
            "status": "BLOCKED_REVIEW_CSV_EXPORT",
            "run_id": args.run_id,
            "reason": str(exc),
            "apply_performed": False,
            "fund_ledger_write_allowed": False,
            "financial_fact_promoted": False,
            "management_conclusion_allowed": False,
        })
        return 2

    metrics = parse_metrics(args.metrics)
    selected = select_rows(rows, metrics, args.limit_per_metric)
    review_rows = build_review_rows(repo_root, args.run_id, selected)
    output_relative_path = (
        Path("KMFA/metadata/fund_weekly_analysis/private_runtime/runs")
        / args.run_id
        / output_name
    )
    output_path = repo_root / output_relative_path
    write_csv(output_path, review_rows)
    payload = {
        "status": "READY_REVIEW_CSV",
        "run_id": args.run_id,
        "source_worklist_relative_path": str(
            Path("KMFA/metadata/fund_weekly_analysis/private_runtime/runs") / args.run_id / WORKLIST_NAME
        ),
        "output_relative_path": str(output_relative_path),
        "metrics": metrics,
        "limit_per_metric": args.limit_per_metric,
        "source_count": len(rows),
        "selected_count": len(review_rows),
        "apply_performed": False,
        "fund_ledger_write_allowed": False,
        "financial_fact_promoted": False,
        "management_conclusion_allowed": False,
    }
    if args.xlsx:
        xlsx_output_relative_path = (
            Path("KMFA/metadata/fund_weekly_analysis/private_runtime/runs")
            / args.run_id
            / xlsx_output_name
        )
        write_xlsx(repo_root / xlsx_output_relative_path, review_rows)
        payload["xlsx_output_relative_path"] = str(xlsx_output_relative_path)
    emit(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
