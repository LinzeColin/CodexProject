from __future__ import annotations

import re
import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL_ROOT = REPO_ROOT / "KMFA" / "fund-weekly-analysis-skill"
TEMPLATE = SKILL_ROOT / "templates" / "资金与税费管理母版_真实数据预览_v2.xlsx"


class FundWeeklyAnalysisSkillContractTest(unittest.TestCase):
    def test_skill_package_uses_sydney_1130_local_schedule_and_real_input(self) -> None:
        self.assertTrue(SKILL_ROOT.exists(), "fund-weekly-analysis-skill package must exist under KMFA")
        skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        config = (SKILL_ROOT / "templates" / "fund_weekly_analysis_config.yaml").read_text(encoding="utf-8")
        plist = (SKILL_ROOT / "automation" / "launchd" / "com.kmfa.fund-weekly-analysis.plist").read_text(
            encoding="utf-8"
        )
        prompt = (SKILL_ROOT / "automation" / "daily_1130_sydney.prompt.md").read_text(encoding="utf-8")

        for text in (skill, config, prompt):
            self.assertIn("Australia/Sydney", text)
            self.assertIn("/Users/linzezhang/Library/CloudStorage/OneDrive-Personal/DWS_Outputs/付款请示群", text)
        self.assertIn("No simulation", skill)
        self.assertIn("Do not use simulated", prompt)

        self.assertRegex(config, r'schedule_local:\s*"11:30"')
        self.assertRegex(config, r'timezone:\s*Australia/Sydney')
        self.assertRegex(plist, r"<key>Hour</key>\s*<integer>11</integer>")
        self.assertRegex(plist, r"<key>Minute</key>\s*<integer>30</integer>")

    def test_latest_template_has_homepage_cards_two_line_charts_and_hidden_audit_sheets(self) -> None:
        self.assertTrue(TEMPLATE.exists(), "latest editable native Excel template must be present")
        ns_sheet = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
        ns_chart = {"c": "http://schemas.openxmlformats.org/drawingml/2006/chart"}
        ns_draw = {"xdr": "http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing"}

        with zipfile.ZipFile(TEMPLATE) as workbook:
            workbook_xml = ET.fromstring(workbook.read("xl/workbook.xml"))
            sheets = workbook_xml.findall(".//x:sheet", ns_sheet)
            self.assertEqual(
                [sheet.attrib["name"] for sheet in sheets],
                [
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
                ],
            )
            self.assertTrue(all(sheet.attrib.get("state") == "hidden" for sheet in sheets[6:]))

            for sheet_number in range(1, 7):
                visible_sheet = ET.fromstring(workbook.read(f"xl/worksheets/sheet{sheet_number}.xml"))
                row2_values = [
                    value.text or ""
                    for value in visible_sheet.findall(".//x:row[@r='2']/x:c/x:v", ns_sheet)
                    if value.text
                ]
                self.assertEqual(row2_values, [], f"visible sheet{sheet_number} row 2 must be blank")

            sheet1 = ET.fromstring(workbook.read("xl/worksheets/sheet1.xml"))

            def cell_text(ref: str) -> str:
                cell = sheet1.find(f".//x:c[@r='{ref}']", ns_sheet)
                self.assertIsNotNone(cell, ref)
                value = cell.find("x:v", ns_sheet)
                return value.text or "" if value is not None else ""

            self.assertEqual(cell_text("A2"), "")
            self.assertIn("可用现金占比", cell_text("B4"))
            self.assertIn("银行存款", cell_text("E4"))
            self.assertIn("票据/电子汇票", cell_text("H4"))
            self.assertIn("期末总资金", cell_text("K4"))
            self.assertIn("保证金可释放", cell_text("B8"))
            self.assertIn("外部净流出", cell_text("E8"))
            self.assertIn("内部调拨净额", cell_text("H8"))
            self.assertIn("资金缺口", cell_text("K8"))

            drawing = ET.fromstring(workbook.read("xl/drawings/drawing1.xml"))
            anchors = drawing.findall("xdr:oneCellAnchor", ns_draw)
            self.assertEqual(len(anchors), 2)
            for anchor in anchors:
                ext = anchor.find("xdr:ext", ns_draw)
                width_in = int(ext.attrib["cx"]) / 914400
                height_in = int(ext.attrib["cy"]) / 914400
                self.assertLessEqual(width_in, 18)
                self.assertLessEqual(height_in, 9)

            for chart_path, expected_title, expected_points in (
                ("xl/drawings/charts/chart1.xml", "最近15天资金余额折线图", "15"),
                ("xl/drawings/charts/chart7.xml", "最近30天资金余额折线图", "30"),
            ):
                chart = ET.fromstring(workbook.read(chart_path))
                text = "".join(t.text or "" for t in chart.findall(".//{http://schemas.openxmlformats.org/drawingml/2006/main}t"))
                self.assertIn(expected_title, text)
                series = chart.findall(".//c:lineChart/c:ser", ns_chart)
                self.assertEqual(len(series), 3)
                self.assertEqual(
                    [ser.find("c:cat/c:strLit/c:ptCount", ns_chart).attrib["val"] for ser in series],
                    [expected_points, expected_points, expected_points],
                )

    def test_runner_fails_closed_with_manifest_when_input_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            missing_input = repo_root / "missing付款请示群"
            result = subprocess.run(
                [
                    sys.executable,
                    str(SKILL_ROOT / "tools" / "run_fund_weekly_analysis.py"),
                    "--repo-root",
                    str(repo_root),
                    "--input-dir",
                    str(missing_input),
                    "--run-id",
                    "missing_source_test",
                    "--timezone",
                    "Australia/Sydney",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 2)
            run_dir = repo_root / "KMFA/metadata/fund_weekly_analysis/private_runtime/runs/missing_source_test"
            manifest = json.loads((run_dir / "run_manifest.json").read_text(encoding="utf-8"))
            issues = json.loads((run_dir / "data_quality_issues.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["status"], "SOURCE_MISSING")
            self.assertEqual(manifest["file_count"], 0)
            self.assertEqual(issues[0]["issue_type"], "SOURCE_MISSING")


if __name__ == "__main__":
    unittest.main()
