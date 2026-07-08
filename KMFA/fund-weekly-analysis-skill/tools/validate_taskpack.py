#!/usr/bin/env python3
from __future__ import annotations

import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

REQUIRED = [
    "README.md",
    "SKILL.md",
    "references/runbook.md",
    "references/configuration.md",
    "references/operating_contract.md",
    "references/source_of_truth_contract.md",
    "references/validation_checks.md",
    "templates/excel_sheet_spec.yaml",
    "templates/fund_weekly_analysis_config.yaml",
    "automation/codex_app_automation.contract.toml",
    "automation/daily_1130_sydney.prompt.md",
    "tools/check_codex_app_automation.py",
    "tools/check_source_readiness.py",
    "tools/run_daily_local.sh",
    "tools/run_fund_weekly_analysis.py",
    "tools/materialize_fund_source.py",
    "tools/install_to_kmfa_main.sh",
    "templates/资金与税费管理母版_真实数据预览_v2.xlsx",
]
REQUIRED_SKILL_STRINGS = [
    "Do not create branches",
    "main",
    "Australia/Sydney",
    "11:30",
    "No simulation",
    "01_首页总览",
    "05_公司银行矩阵",
    "hidden",
    "1728",
    "--source-zip",
    "ocr_text_candidates.csv",
    "ocr_value_candidates.csv",
    "chat_text_candidates.csv",
    "chat_value_candidates.csv",
]
EXPECTED_SHEETS = [
    "01_首页总览",
    "02_资金趋势预测",
    "03_三层净流余额",
    "04_税费融资风险",
    "05_公司银行矩阵",
    "06_CodexSkill流程",
    "H01_资金事实主表",
    "H02_异常任务池",
    "H03_钉钉证据索引",
    "H04_客户合同辅助",
    "H05_复审检查",
    "H06_配置规则",
]


def validate_template(root: Path) -> list[str]:
    errors: list[str] = []
    template = root / "templates/资金与税费管理母版_真实数据预览_v2.xlsx"
    ns_sheet = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    ns_chart = {"c": "http://schemas.openxmlformats.org/drawingml/2006/chart"}
    ns_draw = {"xdr": "http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing"}

    try:
        with zipfile.ZipFile(template) as workbook:
            workbook_xml = ET.fromstring(workbook.read("xl/workbook.xml"))
            sheets = workbook_xml.findall(".//x:sheet", ns_sheet)
            names = [sheet.attrib["name"] for sheet in sheets]
            if names != EXPECTED_SHEETS:
                errors.append(f"sheet order mismatch: {names}")
            if not all(sheet.attrib.get("state") == "hidden" for sheet in sheets[6:]):
                errors.append("hidden audit/review sheets are not hidden")

            for sheet_number in range(1, 7):
                visible_sheet = ET.fromstring(workbook.read(f"xl/worksheets/sheet{sheet_number}.xml"))
                row2_values = [
                    value.text or ""
                    for value in visible_sheet.findall(".//x:row[@r='2']/x:c/x:v", ns_sheet)
                    if value.text
                ]
                if row2_values:
                    errors.append(f"visible sheet{sheet_number} row 2 is not blank: {row2_values[:3]}")

            sheet1 = ET.fromstring(workbook.read("xl/worksheets/sheet1.xml"))

            def cell_text(ref: str) -> str:
                cell = sheet1.find(f".//x:c[@r='{ref}']", ns_sheet)
                if cell is None:
                    return ""
                value = cell.find("x:v", ns_sheet)
                return value.text or "" if value is not None else ""

            expected_cards = {
                "B4": "可用现金占比",
                "E4": "银行存款",
                "H4": "票据/电子汇票",
                "K4": "期末总资金",
                "B8": "保证金可释放",
                "E8": "外部净流出",
                "H8": "内部调拨净额",
                "K8": "资金缺口",
            }
            if cell_text("A2"):
                errors.append("visible homepage row 2 text is not cleared")
            for ref, phrase in expected_cards.items():
                if phrase not in cell_text(ref):
                    errors.append(f"homepage card mismatch at {ref}: expected {phrase!r}, got {cell_text(ref)!r}")

            drawing = ET.fromstring(workbook.read("xl/drawings/drawing1.xml"))
            anchors = drawing.findall("xdr:oneCellAnchor", ns_draw)
            if len(anchors) != 2:
                errors.append(f"homepage chart count mismatch: {len(anchors)}")
            for anchor in anchors:
                ext = anchor.find("xdr:ext", ns_draw)
                width_in = int(ext.attrib["cx"]) / 914400
                height_in = int(ext.attrib["cy"]) / 914400
                if width_in > 18 or height_in > 9:
                    errors.append(f"chart exceeds size limit: {width_in:.2f}x{height_in:.2f} in")

            for chart_path, expected_title, expected_points in (
                ("xl/drawings/charts/chart1.xml", "最近15天资金余额折线图", "15"),
                ("xl/drawings/charts/chart7.xml", "最近30天资金余额折线图", "30"),
            ):
                chart = ET.fromstring(workbook.read(chart_path))
                title = "".join(
                    node.text or ""
                    for node in chart.findall(".//{http://schemas.openxmlformats.org/drawingml/2006/main}t")
                )
                if expected_title not in title:
                    errors.append(f"chart title mismatch in {chart_path}: {title}")
                series = chart.findall(".//c:lineChart/c:ser", ns_chart)
                if len(series) != 3:
                    errors.append(f"chart series count mismatch in {chart_path}: {len(series)}")
                counts = [
                    ser.find("c:cat/c:strLit/c:ptCount", ns_chart).attrib["val"]
                    for ser in series
                ]
                if counts != [expected_points, expected_points, expected_points]:
                    errors.append(f"chart point count mismatch in {chart_path}: {counts}")
    except Exception as exc:
        errors.append(f"template validation failed: {exc}")
    return errors


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    missing = [p for p in REQUIRED if not (root / p).exists()]
    if missing:
        print("missing files:", missing)
        return 2
    skill = (root / "SKILL.md").read_text(encoding="utf-8")
    miss = [s for s in REQUIRED_SKILL_STRINGS if s not in skill]
    if miss:
        print("missing required SKILL strings:", miss)
        return 3
    template_errors = validate_template(root)
    if template_errors:
        print("template validation errors:")
        for error in template_errors:
            print("-", error)
        return 4
    print("PASS: taskpack static validation")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
