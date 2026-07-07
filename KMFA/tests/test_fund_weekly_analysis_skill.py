from __future__ import annotations

import re
import csv
import hashlib
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


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


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

    def test_runner_reports_private_source_candidates_when_expected_folder_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir) / "repo"
            one_drive = Path(temp_dir) / "OneDrive-Personal"
            missing_input = one_drive / "DWS_Outputs" / "付款请示群"
            archive_candidate = one_drive / "DWS_Archive" / "付款请示群" / "files" / "0708"
            archive_candidate.mkdir(parents=True)
            (archive_candidate / "20260708113000_杨婷_abc_image_real.png").write_bytes(b"real-image-bytes")
            (one_drive / "DWS_Outputs.zip").write_bytes(b"PK-real-placeholder")

            result = subprocess.run(
                [
                    sys.executable,
                    str(SKILL_ROOT / "tools" / "run_fund_weekly_analysis.py"),
                    "--repo-root",
                    str(repo_root),
                    "--input-dir",
                    str(missing_input),
                    "--run-id",
                    "missing_with_candidates",
                    "--timezone",
                    "Australia/Sydney",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 2)
            run_dir = repo_root / "KMFA/metadata/fund_weekly_analysis/private_runtime/runs/missing_with_candidates"
            manifest = json.loads((run_dir / "run_manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["status"], "SOURCE_MISSING")
            candidates = {item["kind"]: item for item in manifest["source_candidates"]}
            self.assertTrue(candidates["dws_outputs_zip"]["exists"])
            self.assertTrue(candidates["dws_archive_group"]["exists"])
            self.assertEqual(candidates["dws_archive_group"]["file_count_limited"], 1)
            self.assertIn("explicit materialization", manifest["data_quality_issues"][0]["action"])

    def test_runner_emits_no_hallucination_package_when_input_folder_exists(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir) / "repo"
            input_dir = Path(temp_dir) / "OneDrive-Personal" / "DWS_Outputs" / "付款请示群"
            source_day = input_dir / "files" / "0708"
            source_day.mkdir(parents=True)
            (source_day / "20260708113000_杨婷_abc_image_real.png").write_bytes(b"real-image-bytes")
            (source_day / "20260708113100_吴云霞_def_资金计划.xlsx").write_bytes(b"real-xlsx-placeholder")

            result = subprocess.run(
                [
                    sys.executable,
                    str(SKILL_ROOT / "tools" / "run_fund_weekly_analysis.py"),
                    "--repo-root",
                    str(repo_root),
                    "--input-dir",
                    str(input_dir),
                    "--run-id",
                    "indexed_package_test",
                    "--timezone",
                    "Australia/Sydney",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            run_dir = repo_root / "KMFA/metadata/fund_weekly_analysis/private_runtime/runs/indexed_package_test"
            manifest = json.loads((run_dir / "run_manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["status"], "INDEXED_PENDING_EXTRACTION")
            self.assertEqual(manifest["file_count"], 2)
            self.assertEqual(manifest["source_summary"]["kind_counts"]["screenshot"], 1)
            self.assertEqual(manifest["source_summary"]["kind_counts"]["tabular_finance_source"], 1)

            required_outputs = [
                "资金与税费管理母版_indexed_package_test.xlsx",
                "evidence_index.csv",
                "fund_ledger.csv",
                "net_flow_ledger.csv",
                "company_bank_matrix.csv",
                "tax_loan_risk.csv",
                "exception_tasks.csv",
                "cross_review.json",
                "audit_log.json",
                "run_summary.md",
            ]
            for name in required_outputs:
                self.assertTrue((run_dir / name).exists(), name)

            with zipfile.ZipFile(run_dir / "资金与税费管理母版_indexed_package_test.xlsx") as workbook:
                self.assertIn("xl/workbook.xml", workbook.namelist())

            with (run_dir / "exception_tasks.csv").open(encoding="utf-8-sig", newline="") as f:
                rows = list(csv.DictReader(f))
            self.assertEqual(len(rows), 2)
            self.assertTrue(all(row["task_type"] == "PENDING_OCR_OR_REVIEW" for row in rows))

            cross_review = json.loads((run_dir / "cross_review.json").read_text(encoding="utf-8"))
            self.assertFalse(cross_review["management_conclusion_allowed"])
            self.assertEqual(cross_review["generated_financial_amount_count"], 0)

    def test_runner_fails_closed_when_input_file_is_unreadable(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir) / "repo"
            input_dir = Path(temp_dir) / "OneDrive-Personal" / "DWS_Outputs" / "付款请示群"
            unreadable_file = input_dir / "files" / "0708" / "unreadable.png"
            unreadable_file.parent.mkdir(parents=True)
            unreadable_file.write_bytes(b"not-readable")
            unreadable_file.chmod(0)
            try:
                result = subprocess.run(
                    [
                        sys.executable,
                        str(SKILL_ROOT / "tools" / "run_fund_weekly_analysis.py"),
                        "--repo-root",
                        str(repo_root),
                        "--input-dir",
                        str(input_dir),
                        "--run-id",
                        "runner_unreadable_source",
                        "--timezone",
                        "Australia/Sydney",
                    ],
                    text=True,
                    capture_output=True,
                    check=False,
                )
            finally:
                unreadable_file.chmod(0o600)

            self.assertEqual(result.returncode, 5)
            run_dir = repo_root / "KMFA/metadata/fund_weekly_analysis/private_runtime/runs/runner_unreadable_source"
            manifest = json.loads((run_dir / "run_manifest.json").read_text(encoding="utf-8"))
            issues = json.loads((run_dir / "data_quality_issues.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["status"], "SOURCE_UNREADABLE")
            self.assertEqual(manifest["unreadable_count"], 1)
            self.assertEqual(issues[0]["issue_type"], "SOURCE_UNREADABLE")
            self.assertFalse((run_dir / "资金与税费管理母版_runner_unreadable_source.xlsx").exists())

    def test_materialize_archive_candidate_is_explicit_idempotent_and_no_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir) / "repo"
            one_drive = Path(temp_dir) / "OneDrive-Personal"
            source = one_drive / "DWS_Archive" / "付款请示群"
            source_file = source / "files" / "0708" / "20260708113000_杨婷_real_image.png"
            source_file.parent.mkdir(parents=True)
            source_payload = b"real-source-bytes"
            source_file.write_bytes(source_payload)
            target = one_drive / "DWS_Outputs" / "付款请示群"

            dry_run = subprocess.run(
                [
                    sys.executable,
                    str(SKILL_ROOT / "tools" / "materialize_fund_source.py"),
                    "--repo-root",
                    str(repo_root),
                    "--source-dir",
                    str(source),
                    "--target-dir",
                    str(target),
                    "--run-id",
                    "materialize_dry_run",
                    "--timezone",
                    "Australia/Sydney",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(dry_run.returncode, 0, dry_run.stderr)
            self.assertFalse(target.exists(), "dry-run must not create the target DWS_Outputs folder")
            dry_manifest = json.loads(
                (repo_root / "KMFA/metadata/fund_weekly_analysis/private_runtime/runs/materialize_dry_run/source_materialization_manifest.json").read_text(encoding="utf-8")
            )
            self.assertFalse(dry_manifest["applied"])
            self.assertEqual(dry_manifest["planned_copy_count"], 1)

            apply_run = subprocess.run(
                [
                    sys.executable,
                    str(SKILL_ROOT / "tools" / "materialize_fund_source.py"),
                    "--repo-root",
                    str(repo_root),
                    "--source-dir",
                    str(source),
                    "--target-dir",
                    str(target),
                    "--run-id",
                    "materialize_apply",
                    "--timezone",
                    "Australia/Sydney",
                    "--apply",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(apply_run.returncode, 0, apply_run.stderr)
            copied_file = target / "files" / "0708" / "20260708113000_杨婷_real_image.png"
            self.assertEqual(copied_file.read_bytes(), source_payload)
            apply_manifest = json.loads(
                (repo_root / "KMFA/metadata/fund_weekly_analysis/private_runtime/runs/materialize_apply/source_materialization_manifest.json").read_text(encoding="utf-8")
            )
            self.assertTrue(apply_manifest["applied"])
            self.assertEqual(apply_manifest["copied_count"], 1)
            self.assertEqual(apply_manifest["skipped_identical_count"], 0)
            self.assertEqual(apply_manifest["files"][0]["sha256"], sha256_bytes(source_payload))

            second_apply = subprocess.run(
                [
                    sys.executable,
                    str(SKILL_ROOT / "tools" / "materialize_fund_source.py"),
                    "--repo-root",
                    str(repo_root),
                    "--source-dir",
                    str(source),
                    "--target-dir",
                    str(target),
                    "--run-id",
                    "materialize_second_apply",
                    "--timezone",
                    "Australia/Sydney",
                    "--apply",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(second_apply.returncode, 0, second_apply.stderr)
            second_manifest = json.loads(
                (repo_root / "KMFA/metadata/fund_weekly_analysis/private_runtime/runs/materialize_second_apply/source_materialization_manifest.json").read_text(encoding="utf-8")
            )
            self.assertEqual(second_manifest["copied_count"], 0)
            self.assertEqual(second_manifest["skipped_identical_count"], 1)

            copied_file.write_bytes(b"different-target-bytes")
            conflict_run = subprocess.run(
                [
                    sys.executable,
                    str(SKILL_ROOT / "tools" / "materialize_fund_source.py"),
                    "--repo-root",
                    str(repo_root),
                    "--source-dir",
                    str(source),
                    "--target-dir",
                    str(target),
                    "--run-id",
                    "materialize_conflict",
                    "--timezone",
                    "Australia/Sydney",
                    "--apply",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(conflict_run.returncode, 3)
            conflict_manifest = json.loads(
                (repo_root / "KMFA/metadata/fund_weekly_analysis/private_runtime/runs/materialize_conflict/source_materialization_manifest.json").read_text(encoding="utf-8")
            )
            self.assertEqual(conflict_manifest["status"], "TARGET_CONFLICT")
            self.assertEqual(len(conflict_manifest["conflicts"]), 1)

    def test_materialize_fails_closed_when_source_file_is_unreadable(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir) / "repo"
            source = Path(temp_dir) / "DWS_Archive" / "付款请示群"
            target = Path(temp_dir) / "DWS_Outputs" / "付款请示群"
            unreadable_file = source / "files" / "0708" / "unreadable.png"
            unreadable_file.parent.mkdir(parents=True)
            unreadable_file.write_bytes(b"not-readable")
            unreadable_file.chmod(0)
            try:
                result = subprocess.run(
                    [
                        sys.executable,
                        str(SKILL_ROOT / "tools" / "materialize_fund_source.py"),
                        "--repo-root",
                        str(repo_root),
                        "--source-dir",
                        str(source),
                        "--target-dir",
                        str(target),
                        "--run-id",
                        "materialize_unreadable",
                        "--timezone",
                        "Australia/Sydney",
                    ],
                    text=True,
                    capture_output=True,
                    check=False,
                )
            finally:
                unreadable_file.chmod(0o600)
            self.assertEqual(result.returncode, 5)
            self.assertFalse(target.exists())
            manifest = json.loads(
                (repo_root / "KMFA/metadata/fund_weekly_analysis/private_runtime/runs/materialize_unreadable/source_materialization_manifest.json").read_text(encoding="utf-8")
            )
            self.assertEqual(manifest["status"], "SOURCE_UNREADABLE")
            self.assertEqual(manifest["unreadable_count"], 1)


if __name__ == "__main__":
    unittest.main()
