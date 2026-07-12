#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


EXPECTED_RRULE = "RRULE:FREQ=WEEKLY;BYDAY=MO,SA;BYHOUR=11;BYMINUTE=0"
EXPECTED_SOURCE_DIR = "/Users/linzezhang/Library/CloudStorage/OneDrive-Personal/DWS_Outputs/付款请示群"
EXPECTED_ROW4 = ["可用现金占比", "银行存款", "票据/电子汇票", "期末总资金"]
EXPECTED_ROW8 = ["保证金可释放", "外部净流出", "内部调拨净额", "资金缺口"]
EXPECTED_CHART_TITLES = ["最近15天资金余额折线图", "最近30天资金余额折线图"]
ZIP_REQUIRED = [
    "SKILL.md",
    "TASKPACK.md",
    "templates/excel_sheet_spec.yaml",
    "tools/run_fund_weekly_analysis.py",
    "tools/check_delivery_acceptance.py",
    "tools/check_codex_app_automation.py",
    "tools/check_source_readiness.py",
    "tools/validate_taskpack.py",
    "automation/weekly_mon_sat_1100_sydney.prompt.md",
]


def run_json_command(command: list[str], cwd: Path) -> tuple[dict, str]:
    result = subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False)
    if result.returncode != 0:
        raise RuntimeError((result.stderr or result.stdout or "").strip())
    output = result.stdout.strip()
    return json.loads(output), output


def run_text_command(command: list[str], cwd: Path) -> str:
    result = subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False)
    if result.returncode != 0:
        raise RuntimeError((result.stderr or result.stdout or "").strip())
    return result.stdout.strip()


def row_count(path: Path) -> int:
    if not path.exists():
        return -1
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return max(sum(1 for _ in csv.DictReader(handle)), 0)


def csv_all_false(path: Path, columns: list[str]) -> bool:
    if not path.exists():
        return False
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            for column in columns:
                if str(row.get(column, "")).strip().lower() not in {"", "false", "0", "no"}:
                    return False
    return True


def shared_strings(workbook: zipfile.ZipFile) -> list[str]:
    if "xl/sharedStrings.xml" not in workbook.namelist():
        return []
    root = ET.fromstring(workbook.read("xl/sharedStrings.xml"))
    strings: list[str] = []
    for item in root.findall("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}si"):
        text = "".join(
            node.text or ""
            for node in item.findall(".//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t")
        )
        strings.append(text)
    return strings


def cell_text(sheet: ET.Element, ref: str, strings: list[str]) -> str:
    ns = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    cell = sheet.find(f".//x:c[@r='{ref}']", ns)
    if cell is None:
        return ""
    inline_text = cell.find("x:is/x:t", ns)
    if inline_text is not None:
        return inline_text.text or ""
    value = cell.find("x:v", ns)
    if value is None or value.text is None:
        return ""
    if cell.attrib.get("t") == "s":
        index = int(value.text)
        return strings[index] if index < len(strings) else ""
    return value.text or ""


def validate_excel_workbook(path: Path) -> list[str]:
    errors: list[str] = []
    ns = {
        "x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
        "xdr": "http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing",
    }
    try:
        with zipfile.ZipFile(path) as workbook:
            names = workbook.namelist()
            strings = shared_strings(workbook)
            sheet1 = ET.fromstring(workbook.read("xl/worksheets/sheet1.xml"))

            if any(cell_text(sheet1, "A2", strings).strip() for _ in [0]):
                errors.append("homepage row 2 is not blank")

            row4 = [cell_text(sheet1, ref, strings).splitlines()[0] for ref in ["B4", "E4", "H4", "K4"]]
            row8 = [cell_text(sheet1, ref, strings).splitlines()[0] for ref in ["B8", "E8", "H8", "K8"]]
            if row4 != EXPECTED_ROW4:
                errors.append(f"homepage row 4 labels mismatch: {row4}")
            if row8 != EXPECTED_ROW8:
                errors.append(f"homepage row 8 labels mismatch: {row8}")

            for sheet_number in range(1, 7):
                sheet_path = f"xl/worksheets/sheet{sheet_number}.xml"
                if sheet_path not in names:
                    errors.append(f"missing visible worksheet {sheet_path}")
                    continue
                sheet = ET.fromstring(workbook.read(sheet_path))
                row2_values = [
                    value.text or ""
                    for value in sheet.findall(".//x:row[@r='2']/x:c/x:v", ns)
                    if value.text
                ]
                if row2_values:
                    errors.append(f"visible sheet{sheet_number} row 2 is not blank")

            if "xl/drawings/drawing1.xml" in names:
                drawing = ET.fromstring(workbook.read("xl/drawings/drawing1.xml"))
                anchors = drawing.findall("xdr:oneCellAnchor", ns)
                if len(anchors) != 2:
                    errors.append(f"homepage chart count mismatch: {len(anchors)}")
            else:
                errors.append("missing homepage drawing")

            chart_text = ""
            for chart_path in [name for name in names if name.startswith("xl/drawings/charts/chart")]:
                chart = ET.fromstring(workbook.read(chart_path))
                chart_text += "".join(
                    node.text or ""
                    for node in chart.findall(".//{http://schemas.openxmlformats.org/drawingml/2006/main}t")
                )
            for title in EXPECTED_CHART_TITLES:
                if title not in chart_text:
                    errors.append(f"missing chart title: {title}")
    except Exception as exc:
        errors.append(f"excel validation failed: {exc}")
    return errors


def add_check(checks: list[dict], name: str, passed: bool, evidence: dict | None = None, severity: str = "fail") -> None:
    status = "PASS" if passed else "FAIL"
    if severity == "owner_blocker":
        status = "OWNER_BLOCKED" if passed else "FAIL"
    checks.append(
        {
            "name": name,
            "status": status,
            "evidence": evidence or {},
        }
    )


def latest_run_dir(runs_dir: Path) -> Path | None:
    candidates = [
        path
        for path in runs_dir.iterdir()
        if path.is_dir() and (path / "run_manifest.json").exists() and (path / "cross_review.json").exists()
    ] if runs_dir.exists() else []
    if not candidates:
        return None
    return max(candidates, key=lambda path: path.stat().st_mtime)


def validate_git(repo_root: Path, checks: list[dict]) -> None:
    branch = run_text_command(["git", "branch", "--show-current"], repo_root)
    status = run_text_command(["git", "status", "--porcelain"], repo_root)
    head = run_text_command(["git", "rev-parse", "HEAD"], repo_root)
    origin = run_text_command(["git", "rev-parse", "origin/main"], repo_root)
    remote = run_text_command(["git", "ls-remote", "origin", "refs/heads/main"], repo_root).split()[0]
    add_check(checks, "git_main_clean_origin_remote_parity", branch == "main" and not status and head == origin == remote, {
        "branch": branch,
        "dirty": bool(status),
        "head": head,
        "origin_main": origin,
        "remote_main": remote,
    })


def validate_zip(zip_path: Path, checks: list[dict]) -> None:
    if not zip_path.exists():
        add_check(checks, "taskpack_zip_exists", False, {"zip_path": str(zip_path)})
        return
    with zipfile.ZipFile(zip_path) as archive:
        names = archive.namelist()
    missing = [name for name in ZIP_REQUIRED if name not in names]
    binary_workbook_entries = [
        name for name in names
        if name.lower().endswith((".xls", ".xlsx"))
    ]
    disallowed = [
        name for name in names
        if "__pycache__" in name
        or name.endswith(".pyc")
        or "private_runtime" in name
        or "daily_1130" in name
        or name.lower().endswith((".xls", ".xlsx"))
    ]
    generated_reports = [
        name for name in names
        if name.startswith("资金与税费管理报告_") or name.startswith("资金与税费管理母版_")
    ]
    add_check(checks, "taskpack_zip_required_files", not missing, {
        "missing": missing,
        "binary_workbook_entries": binary_workbook_entries,
        "entry_count": len(names),
    })
    add_check(checks, "taskpack_zip_public_safe", not disallowed and not generated_reports, {
        "disallowed": disallowed[:10],
        "generated_reports": generated_reports[:10],
    })


def validate_static_contract(repo_root: Path, checks: list[dict]) -> None:
    skill_root = repo_root / "KMFA" / "fund-weekly-analysis-skill"
    config = (skill_root / "templates" / "fund_weekly_analysis_config.yaml").read_text(encoding="utf-8")
    prompt = (skill_root / "automation" / "weekly_mon_sat_1100_sydney.prompt.md").read_text(encoding="utf-8")
    contract = (skill_root / "automation" / "codex_app_automation.contract.toml").read_text(encoding="utf-8")
    text = "\n".join([config, prompt, contract])
    add_check(checks, "static_contract_schedule_and_source", EXPECTED_RRULE in contract and EXPECTED_SOURCE_DIR in text, {
        "expected_rrule": EXPECTED_RRULE,
        "source_dir_present": EXPECTED_SOURCE_DIR in text,
    })


def validate_runtime_gates(repo_root: Path, checks: list[dict]) -> dict:
    automation, _ = run_json_command([
        sys.executable,
        "KMFA/fund-weekly-analysis-skill/tools/check_codex_app_automation.py",
        "--repo-root",
        str(repo_root),
    ], repo_root)
    add_check(checks, "live_automation_ready", automation.get("status") == "CODEX_AUTOMATION_READY" and automation.get("rrule") == EXPECTED_RRULE, automation)

    source, _ = run_json_command([
        sys.executable,
        "KMFA/fund-weekly-analysis-skill/tools/check_source_readiness.py",
        "--repo-root",
        str(repo_root),
        "--timezone",
        "Australia/Sydney",
    ], repo_root)
    add_check(checks, "source_readiness_ready", source.get("status") == "READY" and source.get("file_count", 0) > 0 and source.get("unreadable_count") == 0, source)
    return {"automation": automation, "source": source}


def validate_run_dir(run_dir: Path, checks: list[dict], expected_file_count: int | None = None) -> dict:
    manifest = json.loads((run_dir / "run_manifest.json").read_text(encoding="utf-8"))
    cross = json.loads((run_dir / "cross_review.json").read_text(encoding="utf-8"))
    run_id = manifest.get("run_id") or run_dir.name
    workbook_name = cross.get("workbook") or f"资金与税费管理母版_{run_id}.xlsx"
    pdf_name = manifest.get("human_report_pdf") or cross.get("human_report_pdf") or f"资金与税费管理报告_{run_id}.pdf"
    workbook_path = run_dir / workbook_name
    pdf_path = run_dir / pdf_name

    file_count_ok = manifest.get("file_count", 0) > 0
    if expected_file_count is not None:
        file_count_ok = manifest.get("file_count") == expected_file_count
    add_check(checks, "run_indexes_real_source_files", file_count_ok, {
        "run_id": run_id,
        "status": manifest.get("status"),
        "file_count": manifest.get("file_count"),
        "expected_file_count": expected_file_count,
    })

    pdf_ok = (
        manifest.get("human_report_pdf_generated") is True
        and cross.get("human_report_pdf_generated") is True
        and pdf_path.exists()
        and pdf_path.stat().st_size > 1000
        and pdf_path.read_bytes()[:5] == b"%PDF-"
    )
    add_check(checks, "human_readable_pdf_generated", pdf_ok, {
        "pdf": pdf_name,
        "exists": pdf_path.exists(),
        "size": pdf_path.stat().st_size if pdf_path.exists() else 0,
    })

    excel_errors = validate_excel_workbook(workbook_path) if workbook_path.exists() else ["missing workbook"]
    add_check(checks, "native_excel_structure", not excel_errors, {
        "workbook": workbook_name,
        "errors": excel_errors,
    })

    workbook_quality_ok = manifest.get("workbook_quality_blocking_count") == 0 or cross.get("workbook_quality_blocking_count") == 0
    add_check(checks, "workbook_quality_gate_passes", workbook_quality_ok, {
        "manifest_blocking": manifest.get("workbook_quality_blocking_count"),
        "cross_blocking": cross.get("workbook_quality_blocking_count"),
    })

    ocr_ok = (
        manifest.get("screenshot_ocr_ready_count", 0) > 0
        and manifest.get("screenshot_ocr_missing_count") == 0
        and manifest.get("ocr_financial_fact_candidate_count", 0) > 0
    )
    add_check(checks, "ocr_reuse_and_candidates_ready", ocr_ok, {
        "ready": manifest.get("screenshot_ocr_ready_count"),
        "missing": manifest.get("screenshot_ocr_missing_count"),
        "ocr_fact_candidates": manifest.get("ocr_financial_fact_candidate_count"),
    })

    generated_amount_ok = cross.get("generated_financial_amount_count") == 0
    add_check(checks, "no_hallucinated_financial_amounts", generated_amount_ok, {
        "generated_financial_amount_count": cross.get("generated_financial_amount_count"),
    })

    worklist_count = row_count(run_dir / "ocr_fact_candidate_owner_worklist.csv")
    review_all_count = row_count(run_dir / "ocr_fact_candidate_owner_decision_review_all.csv")
    review_xlsx_ready = manifest.get("ocr_fact_candidate_owner_decision_review_all_xlsx_ready") is True
    add_check(checks, "owner_review_all_packet_ready", worklist_count > 0 and worklist_count == review_all_count and review_xlsx_ready, {
        "worklist_count": worklist_count,
        "review_all_count": review_all_count,
        "xlsx_ready": review_xlsx_ready,
    })

    no_write_flags_ok = csv_all_false(
        run_dir / "ocr_fact_candidate_owner_decision_review_all.csv",
        ["fund_ledger_write_allowed", "financial_fact_promoted", "management_conclusion_allowed"],
    )
    add_check(checks, "owner_review_all_no_write_flags", no_write_flags_ok, {})

    fail_closed_ok = (
        cross.get("management_conclusion_allowed") is False
        and cross.get("formal_fund_ledger_row_count") == 0
        and manifest.get("owner_decision_readiness_status") == "blocked_missing_owner_decision_manifest"
        and manifest.get("owner_decision_readiness_gate_blocking_count", 0) > 0
    )
    add_check(checks, "owner_blockers_fail_closed", fail_closed_ok, {
        "management_conclusion_allowed": cross.get("management_conclusion_allowed"),
        "formal_fund_ledger_row_count": cross.get("formal_fund_ledger_row_count"),
        "owner_decision_readiness_status": manifest.get("owner_decision_readiness_status"),
        "owner_decision_readiness_gate_blocking_count": manifest.get("owner_decision_readiness_gate_blocking_count"),
    }, severity="owner_blocker")
    return {"manifest": manifest, "cross_review": cross}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Check KMFA fund weekly delivery acceptance evidence.")
    default_repo = Path(__file__).resolve().parents[3]
    parser.add_argument("--repo-root", type=Path, default=default_repo)
    parser.add_argument("--run-id", default="")
    parser.add_argument("--zip-path", type=Path, default=Path("/Users/linzezhang/Downloads/fund-weekly-analysis-skill-taskpack.zip"))
    parser.add_argument("--skip-git", action="store_true")
    parser.add_argument("--skip-runtime-gates", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    repo_root = args.repo_root.resolve()
    checks: list[dict] = []
    runtime: dict = {}

    try:
        if not args.skip_git:
            validate_git(repo_root, checks)
        validate_static_contract(repo_root, checks)
        validate_zip(args.zip_path, checks)
        if not args.skip_runtime_gates:
            runtime = validate_runtime_gates(repo_root, checks)

        runs_dir = repo_root / "KMFA" / "metadata" / "fund_weekly_analysis" / "private_runtime" / "runs"
        run_dir = runs_dir / args.run_id if args.run_id else latest_run_dir(runs_dir)
        if run_dir is None or not run_dir.exists():
            add_check(checks, "run_dir_exists", False, {"run_id": args.run_id})
        else:
            validate_run_dir(run_dir, checks, runtime.get("source", {}).get("file_count"))
    except Exception as exc:
        add_check(checks, "delivery_acceptance_checker_exception", False, {"error": str(exc)})

    fail_count = sum(1 for check in checks if check["status"] == "FAIL")
    owner_blocker_count = sum(1 for check in checks if check["status"] == "OWNER_BLOCKED")
    status = "DELIVERY_ACCEPTANCE_FAILED" if fail_count else (
        "DELIVERY_ACCEPTANCE_READY_WITH_OWNER_BLOCKERS" if owner_blocker_count else "DELIVERY_ACCEPTANCE_READY"
    )
    output = {
        "status": status,
        "fail_count": fail_count,
        "owner_blocker_count": owner_blocker_count,
        "checks": checks,
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 2 if fail_count else 0


if __name__ == "__main__":
    raise SystemExit(main())
