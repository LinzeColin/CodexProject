from __future__ import annotations

import re
import contextlib
import csv
import hashlib
import importlib.util
import io
import json
import os
import subprocess
import sys
import tomllib
import tempfile
import time
import unittest
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL_ROOT = REPO_ROOT / "KMFA" / "fund-weekly-analysis-skill"
TEMPLATE = SKILL_ROOT / "templates" / "资金与税费管理母版_真实数据预览_v2.xlsx"
XLSX_NS = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_materialize_module():
    module_path = SKILL_ROOT / "tools" / "materialize_fund_source.py"
    spec = importlib.util.spec_from_file_location("materialize_fund_source_for_test", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def load_ocr_sidecar_module():
    module_path = SKILL_ROOT / "tools" / "generate_screenshot_ocr_sidecars.py"
    spec = importlib.util.spec_from_file_location("generate_screenshot_ocr_sidecars_for_test", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def xlsx_cell_text(workbook: zipfile.ZipFile, sheet_path: str, ref: str) -> str:
    sheet = ET.fromstring(workbook.read(sheet_path))
    cell = sheet.find(f".//x:c[@r='{ref}']", XLSX_NS)
    if cell is None:
        return ""
    inline_text = cell.find("x:is/x:t", XLSX_NS)
    if inline_text is not None:
        return inline_text.text or ""
    value = cell.find("x:v", XLSX_NS)
    return value.text or "" if value is not None else ""


class FundWeeklyAnalysisSkillContractTest(unittest.TestCase):
    def run_daily_with_stubbed_tools(self, readiness_exit: int) -> tuple[subprocess.CompletedProcess[str], Path]:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        temp_root = Path(temp_dir.name)
        repo_root = temp_root / "repo"
        repo_root.mkdir()
        bin_dir = temp_root / "bin"
        bin_dir.mkdir()
        call_log = temp_root / "calls.log"

        git_stub = bin_dir / "git"
        git_stub.write_text(
            "#!/usr/bin/env bash\n"
            "set -euo pipefail\n"
            f"echo git:$* >> {call_log}\n"
            "if [[ \"$1 $2\" == \"branch --show-current\" ]]; then echo main; exit 0; fi\n"
            "if [[ \"$1\" == \"fetch\" || \"$1\" == \"merge\" ]]; then exit 0; fi\n"
            "exit 9\n",
            encoding="utf-8",
        )
        git_stub.chmod(0o755)

        python_stub = bin_dir / "python3"
        python_stub.write_text(
            "#!/usr/bin/env bash\n"
            "set -euo pipefail\n"
            f"echo python:$@ >> {call_log}\n"
            "case \"$1\" in\n"
            f"  *check_source_readiness.py) exit {readiness_exit} ;;\n"
            "  *run_fund_weekly_analysis.py) echo '{\"run_id\":\"daily_stub\",\"run_dir\":\""
            f"{repo_root}/KMFA/metadata/fund_weekly_analysis/private_runtime/runs/daily_stub"
            "\"}'; exit 0 ;;\n"
            "  *generate_screenshot_ocr_sidecars.py) exit 0 ;;\n"
            "  *) exit 8 ;;\n"
            "esac\n",
            encoding="utf-8",
        )
        python_stub.chmod(0o755)

        env = os.environ.copy()
        env["KMFA_REPO_ROOT"] = str(repo_root)
        env["KMFA_FUND_INPUT_DIR"] = str(temp_root / "OneDrive-Personal" / "DWS_Outputs" / "付款请示群")
        env["PATH"] = f"{bin_dir}:/usr/bin:/bin"
        result = subprocess.run(
            [str(SKILL_ROOT / "tools" / "run_daily_local.sh")],
            text=True,
            capture_output=True,
            check=False,
            env=env,
        )
        return result, call_log

    def test_daily_entrypoint_stops_before_runner_when_readiness_is_not_ready(self) -> None:
        result, call_log = self.run_daily_with_stubbed_tools(readiness_exit=2)
        calls = call_log.read_text(encoding="utf-8").splitlines()

        self.assertEqual(result.returncode, 2)
        self.assertTrue(any("check_source_readiness.py" in call for call in calls), calls)
        self.assertFalse(any("run_fund_weekly_analysis.py" in call for call in calls), calls)

    def test_daily_entrypoint_runs_readiness_before_runner_when_ready(self) -> None:
        result, call_log = self.run_daily_with_stubbed_tools(readiness_exit=0)
        calls = call_log.read_text(encoding="utf-8").splitlines()
        readiness_index = next(i for i, call in enumerate(calls) if "check_source_readiness.py" in call)
        runner_index = next(i for i, call in enumerate(calls) if "run_fund_weekly_analysis.py" in call)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertLess(readiness_index, runner_index)

    def test_daily_entrypoint_runs_ocr_sidecar_generation_plan_after_runner_when_ready(self) -> None:
        result, call_log = self.run_daily_with_stubbed_tools(readiness_exit=0)
        calls = call_log.read_text(encoding="utf-8").splitlines()
        runner_index = next(i for i, call in enumerate(calls) if "run_fund_weekly_analysis.py" in call)
        ocr_index = next(i for i, call in enumerate(calls) if "generate_screenshot_ocr_sidecars.py" in call)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertLess(runner_index, ocr_index)

    def test_daily_entrypoint_uses_vision_ocr_engine_by_default_when_ready(self) -> None:
        result, call_log = self.run_daily_with_stubbed_tools(readiness_exit=0)
        calls = call_log.read_text(encoding="utf-8").splitlines()
        ocr_call = next(call for call in calls if "generate_screenshot_ocr_sidecars.py" in call)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--engine vision", ocr_call)
        self.assertIn("--apply", ocr_call)

    def test_skill_package_uses_sydney_monday_saturday_1100_local_schedule_and_real_input(self) -> None:
        self.assertTrue(SKILL_ROOT.exists(), "fund-weekly-analysis-skill package must exist under KMFA")
        skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        config = (SKILL_ROOT / "templates" / "fund_weekly_analysis_config.yaml").read_text(encoding="utf-8")
        plist = (SKILL_ROOT / "automation" / "launchd" / "com.kmfa.fund-weekly-analysis.plist").read_text(
            encoding="utf-8"
        )
        prompt = (SKILL_ROOT / "automation" / "weekly_1100_sydney.prompt.md").read_text(encoding="utf-8")

        for text in (skill, config, prompt):
            self.assertIn("Australia/Sydney", text)
            self.assertIn("11:00", text)
            self.assertIn("/Users/linzezhang/Library/CloudStorage/OneDrive-Personal/DWS_Outputs/付款请示群", text)
        self.assertIn("Monday", prompt)
        self.assertIn("Saturday", prompt)
        self.assertIn("No simulation", skill)
        self.assertIn("Do not use simulated", prompt)

        self.assertRegex(config, r'schedule_local:\s*"11:00"')
        self.assertRegex(config, r'timezone:\s*Australia/Sydney')
        self.assertRegex(plist, r"<key>Hour</key>\s*<integer>11</integer>")
        self.assertRegex(plist, r"<key>Minute</key>\s*<integer>0</integer>")
        self.assertRegex(plist, r"<key>Weekday</key>\s*<integer>1</integer>")
        self.assertRegex(plist, r"<key>Weekday</key>\s*<integer>6</integer>")

    def test_taskpack_validator_requires_daily_shell_entrypoint(self) -> None:
        validator = (SKILL_ROOT / "tools" / "validate_taskpack.py").read_text(encoding="utf-8")
        self.assertIn('"tools/run_daily_local.sh"', validator)

    def test_codex_app_automation_contract_mirrors_monday_saturday_1100_local_cron(self) -> None:
        contract_path = SKILL_ROOT / "automation" / "codex_app_automation.contract.toml"
        self.assertTrue(contract_path.exists(), "public-safe Codex App automation contract must be tracked")
        contract = tomllib.loads(contract_path.read_text(encoding="utf-8"))

        self.assertEqual(contract["id"], "kmfa")
        self.assertEqual(contract["name"], "KMFA资金周报自动化")
        self.assertEqual(contract["kind"], "cron")
        self.assertEqual(contract["status"], "ACTIVE")
        self.assertEqual(contract["rrule"], "FREQ=WEEKLY;BYHOUR=11;BYMINUTE=0;BYDAY=MO,SA")
        self.assertEqual(contract["timezone"], "Australia/Sydney")
        self.assertEqual(contract["execution_environment"], "local")
        self.assertEqual(
            contract["cwds"],
            [
                "/Users/linzezhang/Documents/Codex/workspaces/dws-kmfa-automation/dws-archive",
                "/Users/linzezhang/Documents/Codex/workspaces/dws-kmfa-automation/kmfa-codexproject",
            ],
        )
        self.assertEqual(contract["prompt_file"], "automation/weekly_1100_sydney.prompt.md")
        self.assertEqual(contract["source_readiness_gate"], "tools/check_source_readiness.py")
        self.assertEqual(
            contract["input_dir"],
            "/Users/linzezhang/Library/CloudStorage/OneDrive-Personal/DWS_Outputs/付款请示群",
        )
        prompt = (SKILL_ROOT / contract["prompt_file"]).read_text(encoding="utf-8")
        self.assertIn("干净显示入口", prompt)
        self.assertIn("/Users/linzezhang/Documents/Codex/workspaces/dws-kmfa-automation/kmfa-codexproject", prompt)
        self.assertIn("真实目录 `/Users/linzezhang/CodexProject`", prompt)

    def test_codex_app_automation_check_passes_when_local_state_matches_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            repo_root = temp_root / "repo"
            contract_dir = repo_root / "KMFA/fund-weekly-analysis-skill/automation"
            contract_dir.mkdir(parents=True)
            contract = (SKILL_ROOT / "automation" / "codex_app_automation.contract.toml").read_text(encoding="utf-8")
            (contract_dir / "codex_app_automation.contract.toml").write_text(contract, encoding="utf-8")
            automation_dir = temp_root / "automations" / "kmfa"
            automation_dir.mkdir(parents=True)
            (automation_dir / "automation.toml").write_text(contract, encoding="utf-8")

            result = subprocess.run(
                [
                    sys.executable,
                    str(SKILL_ROOT / "tools" / "check_codex_app_automation.py"),
                    "--repo-root",
                    str(repo_root),
                    "--automation-root",
                    str(temp_root / "automations"),
                ],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["status"], "CODEX_AUTOMATION_READY")

    def test_codex_app_automation_check_fails_closed_when_local_state_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            repo_root = temp_root / "repo"
            contract_dir = repo_root / "KMFA/fund-weekly-analysis-skill/automation"
            contract_dir.mkdir(parents=True)
            contract = (SKILL_ROOT / "automation" / "codex_app_automation.contract.toml").read_text(encoding="utf-8")
            (contract_dir / "codex_app_automation.contract.toml").write_text(contract, encoding="utf-8")

            result = subprocess.run(
                [
                    sys.executable,
                    str(SKILL_ROOT / "tools" / "check_codex_app_automation.py"),
                    "--repo-root",
                    str(repo_root),
                    "--automation-root",
                    str(temp_root / "automations"),
                ],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 2)
            self.assertEqual(json.loads(result.stdout)["status"], "CODEX_AUTOMATION_MISSING")

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
                "funding_forecast.csv",
                "cashflow_validation.csv",
                "screenshot_ocr_coverage.csv",
                "ocr_text_candidates.csv",
                "ocr_value_candidates.csv",
                "chat_text_candidates.csv",
                "chat_value_candidates.csv",
                "chat_evidence_links.csv",
                "attachment_evidence_reconciliation.csv",
                "attachment_reconciliation_remediation.csv",
                "attachment_remediation_dry_run.csv",
                "attachment_repair_plan.csv",
                "attachment_repair_apply_gate.csv",
                "attachment_repair_authorization_template.json",
                "attachment_repair_authorization_preview.csv",
                "workbook_quality_checks.csv",
                "kmfa_metadata_signals.csv",
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
            task_type_counts = {task_type: sum(row["task_type"] == task_type for row in rows) for task_type in {row["task_type"] for row in rows}}
            self.assertEqual(task_type_counts["PENDING_OCR_OR_REVIEW"], 2)
            self.assertEqual(task_type_counts["SCREENSHOT_OCR_MISSING"], 1)

            cross_review = json.loads((run_dir / "cross_review.json").read_text(encoding="utf-8"))
            self.assertFalse(cross_review["management_conclusion_allowed"])
            self.assertEqual(cross_review["generated_financial_amount_count"], 0)
            self.assertEqual(cross_review["screenshot_ocr_missing_count"], 1)

    def test_runner_collects_real_ocr_text_sidecars_without_promoting_amounts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir) / "repo"
            input_dir = Path(temp_dir) / "OneDrive-Personal" / "DWS_Outputs" / "付款请示群"
            source_day = input_dir / "files" / "0708"
            source_day.mkdir(parents=True)
            screenshot = source_day / "20260708113000_杨婷_资金账户截图.png"
            screenshot.write_bytes(b"real-image-bytes")
            sidecar = source_day / "20260708113000_杨婷_资金账户截图.png.ocr.txt"
            sidecar.write_text(
                "招商银行 基本户 2026-07-08 期末余额 12345.67 可用余额 12000.00",
                encoding="utf-8",
            )
            missing_ocr_screenshot = source_day / "20260708113100_杨婷_银行账户截图.png"
            missing_ocr_screenshot.write_bytes(b"real-image-without-ocr-sidecar")

            result = subprocess.run(
                [
                    sys.executable,
                    str(SKILL_ROOT / "tools" / "run_fund_weekly_analysis.py"),
                    "--repo-root",
                    str(repo_root),
                    "--input-dir",
                    str(input_dir),
                    "--run-id",
                    "ocr_sidecar_test",
                    "--timezone",
                    "Australia/Sydney",
                ],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            run_dir = repo_root / "KMFA/metadata/fund_weekly_analysis/private_runtime/runs/ocr_sidecar_test"
            with (run_dir / "screenshot_ocr_coverage.csv").open(encoding="utf-8-sig", newline="") as f:
                coverage_rows = list(csv.DictReader(f))
            self.assertEqual(len(coverage_rows), 2)
            coverage_by_path = {row["source_image_relative_path"]: row for row in coverage_rows}
            self.assertEqual(
                coverage_by_path["files/0708/20260708113000_杨婷_资金账户截图.png"]["ocr_coverage_status"],
                "ocr_text_sidecar_present_pending_review",
            )
            self.assertEqual(
                coverage_by_path["files/0708/20260708113000_杨婷_资金账户截图.png"]["ocr_text_relative_path"],
                "files/0708/20260708113000_杨婷_资金账户截图.png.ocr.txt",
            )
            self.assertEqual(
                coverage_by_path["files/0708/20260708113100_杨婷_银行账户截图.png"]["ocr_coverage_status"],
                "ocr_text_sidecar_missing",
            )
            self.assertEqual(
                coverage_by_path["files/0708/20260708113100_杨婷_银行账户截图.png"]["next_action"],
                "run_ocr_or_attach_real_ocr_sidecar",
            )
            self.assertTrue(all(row["financial_fact_promoted"] == "false" for row in coverage_rows))

            with (run_dir / "ocr_text_candidates.csv").open(encoding="utf-8-sig", newline="") as f:
                ocr_rows = list(csv.DictReader(f))
            self.assertEqual(len(ocr_rows), 1)
            self.assertEqual(ocr_rows[0]["source_image_relative_path"], "files/0708/20260708113000_杨婷_资金账户截图.png")
            self.assertEqual(ocr_rows[0]["ocr_text_relative_path"], "files/0708/20260708113000_杨婷_资金账户截图.png.ocr.txt")
            self.assertEqual(ocr_rows[0]["ocr_text_sha256"], sha256_bytes(sidecar.read_bytes()))
            self.assertEqual(ocr_rows[0]["extraction_status"], "ocr_text_sidecar_indexed_pending_review")
            self.assertEqual(ocr_rows[0]["financial_fact_promoted"], "false")
            self.assertIn("期末余额", ocr_rows[0]["text_excerpt"])

            with (run_dir / "fund_ledger.csv").open(encoding="utf-8-sig", newline="") as f:
                fund_rows = list(csv.DictReader(f))
            self.assertEqual(fund_rows, [])

            with (run_dir / "evidence_index.csv").open(encoding="utf-8-sig", newline="") as f:
                evidence_rows = list(csv.DictReader(f))
            self.assertEqual(evidence_rows[0]["review_status"], "ocr_text_candidate_pending_review")

            with (run_dir / "exception_tasks.csv").open(encoding="utf-8-sig", newline="") as f:
                task_rows = list(csv.DictReader(f))
            self.assertTrue(any(row["task_type"] == "OCR_TEXT_PENDING_REVIEW" for row in task_rows))

            cross_review = json.loads((run_dir / "cross_review.json").read_text(encoding="utf-8"))
            self.assertFalse(cross_review["management_conclusion_allowed"])
            self.assertEqual(cross_review["generated_financial_amount_count"], 0)
            self.assertEqual(cross_review["screenshot_ocr_coverage_count"], 2)
            self.assertEqual(cross_review["screenshot_ocr_ready_count"], 1)
            self.assertEqual(cross_review["screenshot_ocr_missing_count"], 1)
            self.assertEqual(cross_review["ocr_text_candidate_count"], 1)
            self.assertEqual(cross_review["structured_financial_fact_count"], 0)

    def test_runner_extracts_pending_values_from_real_ocr_text_sidecars(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir) / "repo"
            input_dir = Path(temp_dir) / "OneDrive-Personal" / "DWS_Outputs" / "付款请示群"
            source_day = input_dir / "files" / "0708"
            source_day.mkdir(parents=True)
            screenshot = source_day / "20260708113000_杨婷_资金账户截图.png"
            screenshot.write_bytes(b"real-image-bytes")
            (source_day / "20260708113000_杨婷_资金账户截图.png.ocr.txt").write_text(
                "\n".join([
                    "日期 2026-07-08 招商银行 基本户",
                    "期末余额 12,345.67 可用余额 ￥12,000.00",
                    "税费待缴 800.00",
                ]),
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(SKILL_ROOT / "tools" / "run_fund_weekly_analysis.py"),
                    "--repo-root",
                    str(repo_root),
                    "--input-dir",
                    str(input_dir),
                    "--run-id",
                    "ocr_value_test",
                    "--timezone",
                    "Australia/Sydney",
                ],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            run_dir = repo_root / "KMFA/metadata/fund_weekly_analysis/private_runtime/runs/ocr_value_test"
            with (run_dir / "ocr_value_candidates.csv").open(encoding="utf-8-sig", newline="") as f:
                value_rows = list(csv.DictReader(f))
            self.assertEqual([row["candidate_type"] for row in value_rows], ["date", "amount", "amount", "amount"])
            self.assertEqual(value_rows[0]["normalized_value"], "2026-07-08")
            self.assertEqual([row["normalized_value"] for row in value_rows[1:]], ["12345.67", "12000.00", "800.00"])
            self.assertTrue(all(row["extraction_status"] == "ocr_value_candidate_pending_review" for row in value_rows))
            self.assertTrue(all(row["financial_fact_promoted"] == "false" for row in value_rows))

            with (run_dir / "fund_ledger.csv").open(encoding="utf-8-sig", newline="") as f:
                fund_rows = list(csv.DictReader(f))
            self.assertEqual(fund_rows, [])

            with (run_dir / "exception_tasks.csv").open(encoding="utf-8-sig", newline="") as f:
                task_rows = list(csv.DictReader(f))
            self.assertTrue(any(row["task_type"] == "OCR_VALUE_PENDING_REVIEW" for row in task_rows))

            cross_review = json.loads((run_dir / "cross_review.json").read_text(encoding="utf-8"))
            self.assertFalse(cross_review["management_conclusion_allowed"])
            self.assertEqual(cross_review["generated_financial_amount_count"], 0)
            self.assertEqual(cross_review["ocr_value_candidate_count"], 4)
            self.assertEqual(cross_review["structured_financial_fact_count"], 0)

    def test_runner_extracts_pending_values_from_real_chat_records_without_promoting_facts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir) / "repo"
            input_dir = Path(temp_dir) / "OneDrive-Personal" / "DWS_Outputs" / "付款请示群"
            chat_dir = input_dir / "chat_records"
            chat_dir.mkdir(parents=True)
            chat_text = "2026-07-08 付款请示 招商银行 可用余额 ￥12,345.67 税费待缴 800.00"
            chat_csv = chat_dir / "chat_records.csv"
            with chat_csv.open("w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "group_name",
                    "open_conversation_id",
                    "open_message_id",
                    "message_time",
                    "sender_name",
                    "sender_id",
                    "content",
                    "quoted_message_id",
                    "quoted_sender",
                    "quoted_content",
                    "resource_count",
                    "resource_types",
                ])
                writer.writerow([
                    "付款请示群",
                    "conv-1",
                    "msg-1",
                    "2026-07-08T11:30:00+10:00",
                    "杨婷",
                    "sender-1",
                    chat_text,
                    "",
                    "",
                    "",
                    "0",
                    "",
                ])

            result = subprocess.run(
                [
                    sys.executable,
                    str(SKILL_ROOT / "tools" / "run_fund_weekly_analysis.py"),
                    "--repo-root",
                    str(repo_root),
                    "--input-dir",
                    str(input_dir),
                    "--run-id",
                    "chat_value_test",
                    "--timezone",
                    "Australia/Sydney",
                ],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            run_dir = repo_root / "KMFA/metadata/fund_weekly_analysis/private_runtime/runs/chat_value_test"
            with (run_dir / "chat_text_candidates.csv").open(encoding="utf-8-sig", newline="") as f:
                chat_rows = list(csv.DictReader(f))
            self.assertEqual(len(chat_rows), 1)
            self.assertEqual(chat_rows[0]["source_csv_relative_path"], "chat_records/chat_records.csv")
            self.assertEqual(chat_rows[0]["source_row_number"], "2")
            self.assertEqual(chat_rows[0]["open_message_id"], "msg-1")
            self.assertEqual(chat_rows[0]["text_role"], "content")
            self.assertEqual(chat_rows[0]["text_sha256"], sha256_bytes(chat_text.encode("utf-8")))
            self.assertIn("付款请示", chat_rows[0]["text_excerpt"])
            self.assertEqual(chat_rows[0]["financial_fact_promoted"], "false")

            with (run_dir / "chat_value_candidates.csv").open(encoding="utf-8-sig", newline="") as f:
                value_rows = list(csv.DictReader(f))
            self.assertEqual([row["candidate_type"] for row in value_rows], ["date", "amount", "amount"])
            self.assertEqual(value_rows[0]["normalized_value"], "2026-07-08")
            self.assertEqual([row["normalized_value"] for row in value_rows[1:]], ["12345.67", "800.00"])
            self.assertTrue(all(row["extraction_status"] == "chat_value_candidate_pending_review" for row in value_rows))
            self.assertTrue(all(row["financial_fact_promoted"] == "false" for row in value_rows))

            with (run_dir / "fund_ledger.csv").open(encoding="utf-8-sig", newline="") as f:
                fund_rows = list(csv.DictReader(f))
            self.assertEqual(fund_rows, [])

            with (run_dir / "exception_tasks.csv").open(encoding="utf-8-sig", newline="") as f:
                task_rows = list(csv.DictReader(f))
            self.assertTrue(any(row["task_type"] == "CHAT_TEXT_PENDING_REVIEW" for row in task_rows))
            self.assertTrue(any(row["task_type"] == "CHAT_VALUE_PENDING_REVIEW" for row in task_rows))

            cross_review = json.loads((run_dir / "cross_review.json").read_text(encoding="utf-8"))
            self.assertFalse(cross_review["management_conclusion_allowed"])
            self.assertEqual(cross_review["generated_financial_amount_count"], 0)
            self.assertEqual(cross_review["chat_text_candidate_count"], 1)
            self.assertEqual(cross_review["chat_value_candidate_count"], 3)
            self.assertEqual(cross_review["structured_financial_fact_count"], 0)

    def test_ocr_sidecar_generation_plan_fails_closed_without_text_engine(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir) / "repo"
            input_dir = Path(temp_dir) / "OneDrive-Personal" / "DWS_Outputs" / "付款请示群"
            run_dir = repo_root / "KMFA/metadata/fund_weekly_analysis/private_runtime/runs/ocr_generation_plan_test"
            image_dir = input_dir / "files" / "0708"
            image_dir.mkdir(parents=True)
            run_dir.mkdir(parents=True)
            image = image_dir / "20260708113000_杨婷_资金账户截图.png"
            image.write_bytes(b"real-image-bytes")

            with (run_dir / "screenshot_ocr_coverage.csv").open("w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=[
                    "ocr_coverage_id",
                    "evidence_id",
                    "source_image_relative_path",
                    "ocr_sidecar_candidates",
                    "ocr_text_relative_path",
                    "ocr_coverage_status",
                    "next_action",
                    "review_status",
                    "financial_fact_promoted",
                ])
                writer.writeheader()
                writer.writerow({
                    "ocr_coverage_id": "OCRCOV-ocr_generation_plan_test-00001",
                    "evidence_id": "FW-00001",
                    "source_image_relative_path": "files/0708/20260708113000_杨婷_资金账户截图.png",
                    "ocr_sidecar_candidates": "files/0708/20260708113000_杨婷_资金账户截图.png.ocr.txt",
                    "ocr_text_relative_path": "",
                    "ocr_coverage_status": "ocr_text_sidecar_missing",
                    "next_action": "run_ocr_or_attach_real_ocr_sidecar",
                    "review_status": "pending_ocr_extraction",
                    "financial_fact_promoted": "false",
                })

            result = subprocess.run(
                [
                    sys.executable,
                    str(SKILL_ROOT / "tools" / "generate_screenshot_ocr_sidecars.py"),
                    "--repo-root",
                    str(repo_root),
                    "--input-dir",
                    str(input_dir),
                    "--run-dir",
                    str(run_dir),
                    "--engine",
                    "none",
                ],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            with (run_dir / "screenshot_ocr_sidecar_generation_plan.csv").open(encoding="utf-8-sig", newline="") as f:
                plan_rows = list(csv.DictReader(f))
            self.assertEqual(len(plan_rows), 1)
            self.assertEqual(plan_rows[0]["generation_status"], "ocr_engine_unavailable")
            self.assertEqual(plan_rows[0]["apply_performed"], "false")
            self.assertEqual(plan_rows[0]["financial_fact_promoted"], "false")
            self.assertEqual(plan_rows[0]["ocr_text_private_relative_path"], "")
            self.assertFalse((repo_root / "KMFA/metadata/fund_weekly_analysis/private_runtime/ocr_sidecars").exists())

            summary = json.loads((run_dir / "screenshot_ocr_sidecar_generation_summary.json").read_text(encoding="utf-8"))
            self.assertEqual(summary["planned_count"], 1)
            self.assertEqual(summary["generated_sidecar_count"], 0)
            self.assertEqual(summary["engine_unavailable_count"], 1)
            self.assertFalse(summary["financial_fact_promoted"])

    def test_ocr_sidecar_generation_can_write_private_vision_sidecar_without_promoting_facts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir) / "repo"
            input_dir = Path(temp_dir) / "OneDrive-Personal" / "DWS_Outputs" / "付款请示群"
            run_dir = repo_root / "KMFA/metadata/fund_weekly_analysis/private_runtime/runs/vision_ocr_generation_test"
            image_dir = input_dir / "files" / "0708"
            image_dir.mkdir(parents=True)
            run_dir.mkdir(parents=True)
            image = image_dir / "20260708113000_杨婷_资金账户截图.png"
            image.write_bytes(b"real-image-bytes")
            fake_vision = Path(temp_dir) / "fake_vision.py"
            fake_vision.write_text(
                "import json, sys\n"
                "for path in sys.argv[1:]:\n"
                "    print(json.dumps({"
                "'path': path, "
                "'status': 'ocr_text_available', "
                "'text': '可用现金 123.45\\n银行存款 67.89', "
                "'reason': ''"
                "}, ensure_ascii=False))\n",
                encoding="utf-8",
            )

            with (run_dir / "screenshot_ocr_coverage.csv").open("w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=[
                    "ocr_coverage_id",
                    "evidence_id",
                    "source_image_relative_path",
                    "ocr_sidecar_candidates",
                    "ocr_text_relative_path",
                    "ocr_coverage_status",
                    "next_action",
                    "review_status",
                    "financial_fact_promoted",
                ])
                writer.writeheader()
                writer.writerow({
                    "ocr_coverage_id": "OCRCOV-vision_ocr_generation_test-00001",
                    "evidence_id": "FW-00001",
                    "source_image_relative_path": "files/0708/20260708113000_杨婷_资金账户截图.png",
                    "ocr_sidecar_candidates": "files/0708/20260708113000_杨婷_资金账户截图.png.ocr.txt",
                    "ocr_text_relative_path": "",
                    "ocr_coverage_status": "ocr_text_sidecar_missing",
                    "next_action": "run_ocr_or_attach_real_ocr_sidecar",
                    "review_status": "pending_ocr_extraction",
                    "financial_fact_promoted": "false",
                })

            env = os.environ.copy()
            env["KMFA_FUND_VISION_OCR_COMMAND"] = f"{sys.executable} {fake_vision}"
            result = subprocess.run(
                [
                    sys.executable,
                    str(SKILL_ROOT / "tools" / "generate_screenshot_ocr_sidecars.py"),
                    "--repo-root",
                    str(repo_root),
                    "--input-dir",
                    str(input_dir),
                    "--run-dir",
                    str(run_dir),
                    "--engine",
                    "vision",
                    "--apply",
                ],
                text=True,
                capture_output=True,
                check=False,
                env=env,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            with (run_dir / "screenshot_ocr_sidecar_generation_plan.csv").open(encoding="utf-8-sig", newline="") as f:
                plan_rows = list(csv.DictReader(f))
            self.assertEqual(len(plan_rows), 1)
            self.assertEqual(plan_rows[0]["generation_status"], "ocr_text_generated_pending_review")
            self.assertEqual(plan_rows[0]["apply_performed"], "true")
            self.assertEqual(plan_rows[0]["financial_fact_promoted"], "false")
            self.assertEqual(plan_rows[0]["text_length"], str(len("可用现金 123.45\n银行存款 67.89")))
            self.assertNotIn("可用现金", (run_dir / "screenshot_ocr_sidecar_generation_plan.csv").read_text(encoding="utf-8-sig"))

            sidecar_rel = Path(plan_rows[0]["ocr_text_private_relative_path"])
            sidecar = repo_root / sidecar_rel
            self.assertTrue(sidecar.exists())
            self.assertEqual(sidecar.read_text(encoding="utf-8"), "可用现金 123.45\n银行存款 67.89\n")

            summary = json.loads((run_dir / "screenshot_ocr_sidecar_generation_summary.json").read_text(encoding="utf-8"))
            self.assertEqual(summary["engine"], "vision")
            self.assertTrue(summary["apply"])
            self.assertEqual(summary["planned_count"], 1)
            self.assertEqual(summary["generated_sidecar_count"], 1)
            self.assertEqual(summary["text_available_count"], 1)
            self.assertFalse(summary["financial_fact_promoted"])

    def test_vision_ocr_generation_runs_in_bounded_batches(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir) / "repo"
            input_dir = Path(temp_dir) / "OneDrive-Personal" / "DWS_Outputs" / "付款请示群"
            run_dir = repo_root / "KMFA/metadata/fund_weekly_analysis/private_runtime/runs/vision_ocr_batch_test"
            image_dir = input_dir / "files" / "0708"
            image_dir.mkdir(parents=True)
            run_dir.mkdir(parents=True)
            call_log = Path(temp_dir) / "vision_calls.jsonl"
            fake_vision = Path(temp_dir) / "fake_vision.py"
            fake_vision.write_text(
                "import json, os, sys\n"
                "with open(os.environ['VISION_CALL_LOG'], 'a', encoding='utf-8') as f:\n"
                "    f.write(json.dumps({'count': len(sys.argv[1:])}) + '\\n')\n"
                "for path in sys.argv[1:]:\n"
                "    print(json.dumps({'path': path, 'status': 'ocr_text_available', 'text': '文本', 'reason': ''}, ensure_ascii=False))\n",
                encoding="utf-8",
            )

            with (run_dir / "screenshot_ocr_coverage.csv").open("w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=[
                    "ocr_coverage_id",
                    "evidence_id",
                    "source_image_relative_path",
                    "ocr_sidecar_candidates",
                    "ocr_text_relative_path",
                    "ocr_coverage_status",
                    "next_action",
                    "review_status",
                    "financial_fact_promoted",
                ])
                writer.writeheader()
                for index in range(3):
                    image = image_dir / f"image_{index}.png"
                    image.write_bytes(b"real-image-bytes")
                    writer.writerow({
                        "ocr_coverage_id": f"OCRCOV-vision_ocr_batch_test-{index:05d}",
                        "evidence_id": f"FW-{index:05d}",
                        "source_image_relative_path": f"files/0708/image_{index}.png",
                        "ocr_sidecar_candidates": f"files/0708/image_{index}.png.ocr.txt",
                        "ocr_text_relative_path": "",
                        "ocr_coverage_status": "ocr_text_sidecar_missing",
                        "next_action": "run_ocr_or_attach_real_ocr_sidecar",
                        "review_status": "pending_ocr_extraction",
                        "financial_fact_promoted": "false",
                    })

            env = os.environ.copy()
            env["KMFA_FUND_VISION_OCR_COMMAND"] = f"{sys.executable} {fake_vision}"
            env["VISION_CALL_LOG"] = str(call_log)
            result = subprocess.run(
                [
                    sys.executable,
                    str(SKILL_ROOT / "tools" / "generate_screenshot_ocr_sidecars.py"),
                    "--repo-root",
                    str(repo_root),
                    "--input-dir",
                    str(input_dir),
                    "--run-dir",
                    str(run_dir),
                    "--engine",
                    "vision",
                    "--apply",
                    "--vision-batch-size",
                    "2",
                ],
                text=True,
                capture_output=True,
                check=False,
                env=env,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            calls = [json.loads(line)["count"] for line in call_log.read_text(encoding="utf-8").splitlines()]
            self.assertEqual(calls, [2, 1])
            summary = json.loads((run_dir / "screenshot_ocr_sidecar_generation_summary.json").read_text(encoding="utf-8"))
            self.assertEqual(summary["generated_sidecar_count"], 3)
            self.assertEqual(summary["text_available_count"], 3)

    def test_vision_ocr_batch_timeout_is_per_batch_not_per_image(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir) / "repo"
            input_dir = Path(temp_dir) / "OneDrive-Personal" / "DWS_Outputs" / "付款请示群"
            run_dir = repo_root / "KMFA/metadata/fund_weekly_analysis/private_runtime/runs/vision_ocr_timeout_test"
            image_dir = input_dir / "files" / "0708"
            image_dir.mkdir(parents=True)
            run_dir.mkdir(parents=True)
            fake_vision = Path(temp_dir) / "slow_vision.py"
            fake_vision.write_text(
                "import json, sys, time\n"
                "time.sleep(2)\n"
                "for path in sys.argv[1:]:\n"
                "    print(json.dumps({'path': path, 'status': 'ocr_text_available', 'text': 'late text', 'reason': ''}))\n",
                encoding="utf-8",
            )

            with (run_dir / "screenshot_ocr_coverage.csv").open("w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=[
                    "ocr_coverage_id",
                    "evidence_id",
                    "source_image_relative_path",
                    "ocr_sidecar_candidates",
                    "ocr_text_relative_path",
                    "ocr_coverage_status",
                    "next_action",
                    "review_status",
                    "financial_fact_promoted",
                ])
                writer.writeheader()
                for index in range(3):
                    image = image_dir / f"image_{index}.png"
                    image.write_bytes(b"real-image-bytes")
                    writer.writerow({
                        "ocr_coverage_id": f"OCRCOV-vision_ocr_timeout_test-{index:05d}",
                        "evidence_id": f"FW-{index:05d}",
                        "source_image_relative_path": f"files/0708/image_{index}.png",
                        "ocr_sidecar_candidates": f"files/0708/image_{index}.png.ocr.txt",
                        "ocr_text_relative_path": "",
                        "ocr_coverage_status": "ocr_text_sidecar_missing",
                        "next_action": "run_ocr_or_attach_real_ocr_sidecar",
                        "review_status": "pending_ocr_extraction",
                        "financial_fact_promoted": "false",
                    })

            env = os.environ.copy()
            env["KMFA_FUND_VISION_OCR_COMMAND"] = f"{sys.executable} {fake_vision}"
            started = time.monotonic()
            result = subprocess.run(
                [
                    sys.executable,
                    str(SKILL_ROOT / "tools" / "generate_screenshot_ocr_sidecars.py"),
                    "--repo-root",
                    str(repo_root),
                    "--input-dir",
                    str(input_dir),
                    "--run-dir",
                    str(run_dir),
                    "--engine",
                    "vision",
                    "--apply",
                    "--timeout-seconds",
                    "1",
                    "--vision-batch-size",
                    "3",
                ],
                text=True,
                capture_output=True,
                check=False,
                env=env,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertLess(time.monotonic() - started, 2)
            with (run_dir / "screenshot_ocr_sidecar_generation_plan.csv").open(encoding="utf-8-sig", newline="") as f:
                plan_rows = list(csv.DictReader(f))
            self.assertEqual([row["generation_status"] for row in plan_rows], ["ocr_engine_timeout"] * 3)
            self.assertFalse((repo_root / "KMFA/metadata/fund_weekly_analysis/private_runtime/ocr_sidecars").exists())

    def test_runner_links_chat_candidates_to_real_manifest_evidence_without_promoting_facts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir) / "repo"
            input_dir = Path(temp_dir) / "OneDrive-Personal" / "DWS_Outputs" / "付款请示群"
            chat_dir = input_dir / "chat_records"
            manifest_dir = input_dir / "_manifest"
            file_dir = input_dir / "files" / "0708"
            chat_dir.mkdir(parents=True)
            manifest_dir.mkdir(parents=True)
            file_dir.mkdir(parents=True)

            screenshot_rel = "files/0708/20260708113000_杨婷_real_image.png"
            screenshot = input_dir / screenshot_rel
            screenshot.write_bytes(b"real-linked-image")
            chat_text = "2026-07-08 付款请示 招商银行 可用余额 ￥12,345.67 税费待缴 800.00"
            with (chat_dir / "chat_records.csv").open("w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "group_name",
                    "open_conversation_id",
                    "open_message_id",
                    "message_time",
                    "sender_name",
                    "sender_id",
                    "content",
                    "quoted_message_id",
                    "quoted_sender",
                    "quoted_content",
                    "resource_count",
                    "resource_types",
                ])
                writer.writerow([
                    "付款请示群",
                    "conv-1",
                    "msg-1",
                    "2026-07-08T11:30:00+10:00",
                    "杨婷",
                    "sender-1",
                    chat_text,
                    "",
                    "",
                    "",
                    "1",
                    "image",
                ])
            with (manifest_dir / "manifest.csv").open("w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=[
                    "group_name",
                    "open_conversation_id",
                    "message_id",
                    "message_time",
                    "sender_name",
                    "sender_id",
                    "msg_type",
                    "resource_type",
                    "resource_id",
                    "original_filename",
                    "local_archive_path",
                    "output_path",
                    "sha256",
                    "size_bytes",
                    "download_method",
                    "status",
                ])
                writer.writeheader()
                writer.writerow({
                    "group_name": "付款请示群",
                    "open_conversation_id": "conv-1",
                    "message_id": "msg-1",
                    "message_time": "2026-07-08T11:30:00+10:00",
                    "sender_name": "杨婷",
                    "sender_id": "sender-1",
                    "msg_type": "image",
                    "resource_type": "image",
                    "resource_id": "resource-1",
                    "original_filename": "real_image.png",
                    "local_archive_path": "",
                    "output_path": screenshot_rel,
                    "sha256": sha256_bytes(screenshot.read_bytes()),
                    "size_bytes": str(screenshot.stat().st_size),
                    "download_method": "dws",
                    "status": "downloaded",
                })

            result = subprocess.run(
                [
                    sys.executable,
                    str(SKILL_ROOT / "tools" / "run_fund_weekly_analysis.py"),
                    "--repo-root",
                    str(repo_root),
                    "--input-dir",
                    str(input_dir),
                    "--run-id",
                    "chat_evidence_link_test",
                    "--timezone",
                    "Australia/Sydney",
                ],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            run_dir = repo_root / "KMFA/metadata/fund_weekly_analysis/private_runtime/runs/chat_evidence_link_test"
            with (run_dir / "chat_text_candidates.csv").open(encoding="utf-8-sig", newline="") as f:
                chat_rows = list(csv.DictReader(f))
            with (run_dir / "chat_value_candidates.csv").open(encoding="utf-8-sig", newline="") as f:
                value_rows = list(csv.DictReader(f))
            with (run_dir / "chat_evidence_links.csv").open(encoding="utf-8-sig", newline="") as f:
                link_rows = list(csv.DictReader(f))

            self.assertEqual(len(chat_rows), 1)
            self.assertEqual(len(value_rows), 3)
            self.assertEqual(len(link_rows), 1)
            self.assertEqual(link_rows[0]["chat_text_candidate_id"], chat_rows[0]["chat_text_candidate_id"])
            self.assertEqual(link_rows[0]["chat_value_candidate_ids"], ";".join(row["value_candidate_id"] for row in value_rows))
            self.assertEqual(link_rows[0]["open_message_id"], "msg-1")
            self.assertEqual(link_rows[0]["linked_relative_path"], screenshot_rel)
            self.assertTrue(link_rows[0]["linked_evidence_id"].startswith("FWchat_evidence_link_test-"))
            self.assertEqual(link_rows[0]["link_status"], "linked_pending_review")
            self.assertEqual(link_rows[0]["financial_fact_promoted"], "false")

            with (run_dir / "fund_ledger.csv").open(encoding="utf-8-sig", newline="") as f:
                fund_rows = list(csv.DictReader(f))
            self.assertEqual(fund_rows, [])

            with (run_dir / "exception_tasks.csv").open(encoding="utf-8-sig", newline="") as f:
                task_rows = list(csv.DictReader(f))
            self.assertTrue(any(row["task_type"] == "CHAT_EVIDENCE_LINK_PENDING_REVIEW" for row in task_rows))

            cross_review = json.loads((run_dir / "cross_review.json").read_text(encoding="utf-8"))
            self.assertFalse(cross_review["management_conclusion_allowed"])
            self.assertEqual(cross_review["generated_financial_amount_count"], 0)
            self.assertEqual(cross_review["chat_evidence_link_count"], 1)
            self.assertEqual(cross_review["chat_evidence_linked_count"], 1)
            self.assertEqual(cross_review["structured_financial_fact_count"], 0)

    def test_runner_reconciles_manifest_attachments_to_evidence_index_without_promoting_facts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir) / "repo"
            input_dir = Path(temp_dir) / "OneDrive-Personal" / "DWS_Outputs" / "付款请示群"
            manifest_dir = input_dir / "_manifest"
            file_dir = input_dir / "files" / "0708"
            manifest_dir.mkdir(parents=True)
            file_dir.mkdir(parents=True)

            ok_rel = "files/0708/20260708113000_ok_image.png"
            mismatch_rel = "files/0708/20260708113100_mismatch_image.png"
            (input_dir / ok_rel).write_bytes(b"real-ok-image")
            (input_dir / mismatch_rel).write_bytes(b"real-mismatch-image")
            missing_rel = "files/0708/20260708113200_missing_image.png"

            with (manifest_dir / "manifest.csv").open("w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=[
                    "group_name",
                    "open_conversation_id",
                    "message_id",
                    "message_time",
                    "sender_name",
                    "sender_id",
                    "msg_type",
                    "resource_type",
                    "resource_id",
                    "original_filename",
                    "local_archive_path",
                    "output_path",
                    "sha256",
                    "size_bytes",
                    "download_method",
                    "status",
                ])
                writer.writeheader()
                writer.writerow({
                    "group_name": "付款请示群",
                    "open_conversation_id": "conv-1",
                    "message_id": "msg-ok",
                    "message_time": "2026-07-08T11:30:00+10:00",
                    "sender_name": "杨婷",
                    "sender_id": "sender-1",
                    "msg_type": "image",
                    "resource_type": "image",
                    "resource_id": "resource-ok",
                    "original_filename": "ok_image.png",
                    "local_archive_path": "",
                    "output_path": ok_rel,
                    "sha256": sha256_bytes((input_dir / ok_rel).read_bytes()),
                    "size_bytes": str((input_dir / ok_rel).stat().st_size),
                    "download_method": "dws",
                    "status": "downloaded",
                })
                writer.writerow({
                    "group_name": "付款请示群",
                    "open_conversation_id": "conv-1",
                    "message_id": "msg-missing",
                    "message_time": "2026-07-08T11:31:00+10:00",
                    "sender_name": "杨婷",
                    "sender_id": "sender-1",
                    "msg_type": "image",
                    "resource_type": "image",
                    "resource_id": "resource-missing",
                    "original_filename": "missing_image.png",
                    "local_archive_path": "",
                    "output_path": missing_rel,
                    "sha256": "0" * 64,
                    "size_bytes": "123",
                    "download_method": "dws",
                    "status": "downloaded",
                })
                writer.writerow({
                    "group_name": "付款请示群",
                    "open_conversation_id": "conv-1",
                    "message_id": "msg-mismatch",
                    "message_time": "2026-07-08T11:32:00+10:00",
                    "sender_name": "杨婷",
                    "sender_id": "sender-1",
                    "msg_type": "image",
                    "resource_type": "image",
                    "resource_id": "resource-mismatch",
                    "original_filename": "mismatch_image.png",
                    "local_archive_path": "",
                    "output_path": mismatch_rel,
                    "sha256": "f" * 64,
                    "size_bytes": str((input_dir / mismatch_rel).stat().st_size),
                    "download_method": "dws",
                    "status": "downloaded",
                })

            result = subprocess.run(
                [
                    sys.executable,
                    str(SKILL_ROOT / "tools" / "run_fund_weekly_analysis.py"),
                    "--repo-root",
                    str(repo_root),
                    "--input-dir",
                    str(input_dir),
                    "--run-id",
                    "attachment_reconcile_test",
                    "--timezone",
                    "Australia/Sydney",
                ],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            run_dir = repo_root / "KMFA/metadata/fund_weekly_analysis/private_runtime/runs/attachment_reconcile_test"
            with (run_dir / "attachment_evidence_reconciliation.csv").open(encoding="utf-8-sig", newline="") as f:
                rows = list(csv.DictReader(f))
            self.assertEqual(len(rows), 3)
            status_by_message = {row["open_message_id"]: row["reconciliation_status"] for row in rows}
            self.assertEqual(status_by_message["msg-ok"], "evidence_linked_pending_review")
            self.assertEqual(status_by_message["msg-missing"], "evidence_missing_blocking")
            self.assertEqual(status_by_message["msg-mismatch"], "evidence_hash_mismatch_blocking")
            self.assertTrue(all(row["financial_fact_promoted"] == "false" for row in rows))

            with (run_dir / "exception_tasks.csv").open(encoding="utf-8-sig", newline="") as f:
                task_rows = list(csv.DictReader(f))
            reconciliation_tasks = [row for row in task_rows if row["task_type"] == "ATTACHMENT_EVIDENCE_RECONCILIATION_FAIL"]
            self.assertEqual(len(reconciliation_tasks), 2)

            with (run_dir / "fund_ledger.csv").open(encoding="utf-8-sig", newline="") as f:
                fund_rows = list(csv.DictReader(f))
            self.assertEqual(fund_rows, [])

            cross_review = json.loads((run_dir / "cross_review.json").read_text(encoding="utf-8"))
            self.assertFalse(cross_review["management_conclusion_allowed"])
            self.assertEqual(cross_review["generated_financial_amount_count"], 0)
            self.assertEqual(cross_review["attachment_reconciliation_count"], 3)
            self.assertEqual(cross_review["attachment_reconciliation_blocking_count"], 2)
            self.assertEqual(cross_review["attachment_reconciliation_linked_count"], 1)
            self.assertEqual(cross_review["structured_financial_fact_count"], 0)

    def test_runner_turns_attachment_reconciliation_blocks_into_actionable_remediation_queue(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir) / "repo"
            input_dir = Path(temp_dir) / "OneDrive-Personal" / "DWS_Outputs" / "付款请示群"
            manifest_dir = input_dir / "_manifest"
            file_dir = input_dir / "files" / "0708"
            manifest_dir.mkdir(parents=True)
            file_dir.mkdir(parents=True)

            mismatch_rel = "files/0708/20260708113100_mismatch_image.png"
            (input_dir / mismatch_rel).write_bytes(b"real-mismatch-image")
            missing_rel = "files/0708/20260708113200_missing_image.png"

            with (manifest_dir / "manifest.csv").open("w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=[
                    "group_name",
                    "open_conversation_id",
                    "message_id",
                    "message_time",
                    "sender_name",
                    "sender_id",
                    "msg_type",
                    "resource_type",
                    "resource_id",
                    "original_filename",
                    "local_archive_path",
                    "output_path",
                    "sha256",
                    "size_bytes",
                    "download_method",
                    "status",
                ])
                writer.writeheader()
                writer.writerow({
                    "group_name": "付款请示群",
                    "open_conversation_id": "conv-1",
                    "message_id": "msg-missing-output",
                    "message_time": "2026-07-08T11:30:00+10:00",
                    "sender_name": "杨婷",
                    "sender_id": "sender-1",
                    "msg_type": "image",
                    "resource_type": "image",
                    "resource_id": "resource-missing-output",
                    "original_filename": "missing_output.png",
                    "local_archive_path": "",
                    "output_path": "",
                    "sha256": "",
                    "size_bytes": "",
                    "download_method": "dws",
                    "status": "failed",
                })
                writer.writerow({
                    "group_name": "付款请示群",
                    "open_conversation_id": "conv-1",
                    "message_id": "msg-missing-file",
                    "message_time": "2026-07-08T11:31:00+10:00",
                    "sender_name": "杨婷",
                    "sender_id": "sender-1",
                    "msg_type": "image",
                    "resource_type": "image",
                    "resource_id": "resource-missing-file",
                    "original_filename": "missing_file.png",
                    "local_archive_path": "",
                    "output_path": missing_rel,
                    "sha256": "0" * 64,
                    "size_bytes": "123",
                    "download_method": "dws",
                    "status": "downloaded",
                })
                writer.writerow({
                    "group_name": "付款请示群",
                    "open_conversation_id": "conv-1",
                    "message_id": "msg-hash-mismatch",
                    "message_time": "2026-07-08T11:32:00+10:00",
                    "sender_name": "杨婷",
                    "sender_id": "sender-1",
                    "msg_type": "image",
                    "resource_type": "image",
                    "resource_id": "resource-hash-mismatch",
                    "original_filename": "mismatch_image.png",
                    "local_archive_path": "",
                    "output_path": mismatch_rel,
                    "sha256": "f" * 64,
                    "size_bytes": str((input_dir / mismatch_rel).stat().st_size),
                    "download_method": "dws",
                    "status": "downloaded",
                })

            result = subprocess.run(
                [
                    sys.executable,
                    str(SKILL_ROOT / "tools" / "run_fund_weekly_analysis.py"),
                    "--repo-root",
                    str(repo_root),
                    "--input-dir",
                    str(input_dir),
                    "--run-id",
                    "attachment_remediation_test",
                    "--timezone",
                    "Australia/Sydney",
                ],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            run_dir = repo_root / "KMFA/metadata/fund_weekly_analysis/private_runtime/runs/attachment_remediation_test"
            with (run_dir / "attachment_reconciliation_remediation.csv").open(encoding="utf-8-sig", newline="") as f:
                remediation_rows = list(csv.DictReader(f))
            self.assertEqual(len(remediation_rows), 3)
            actions_by_message = {row["open_message_id"]: row["action_code"] for row in remediation_rows}
            self.assertEqual(actions_by_message["msg-missing-output"], "rerun_dws_attachment_download")
            self.assertEqual(actions_by_message["msg-missing-file"], "restore_or_materialize_output_file")
            self.assertEqual(actions_by_message["msg-hash-mismatch"], "quarantine_and_recollect_hash_mismatch")
            self.assertTrue(all(row["automation_safe"] == "false" for row in remediation_rows))
            self.assertTrue(all(row["formal_fact_allowed"] == "false" for row in remediation_rows))
            self.assertTrue(all(row["review_status"] == "pending_operator_action" for row in remediation_rows))

            cross_review = json.loads((run_dir / "cross_review.json").read_text(encoding="utf-8"))
            self.assertEqual(cross_review["attachment_remediation_count"], 3)
            self.assertEqual(cross_review["attachment_remediation_open_count"], 3)
            self.assertFalse(cross_review["management_conclusion_allowed"])
            self.assertEqual(cross_review["generated_financial_amount_count"], 0)

    def test_runner_emits_attachment_remediation_dry_run_without_applying_repairs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir) / "repo"
            input_dir = Path(temp_dir) / "OneDrive-Personal" / "DWS_Outputs" / "付款请示群"
            manifest_dir = input_dir / "_manifest"
            file_dir = input_dir / "files" / "0708"
            manifest_dir.mkdir(parents=True)
            file_dir.mkdir(parents=True)

            mismatch_rel = "files/0708/20260708113100_mismatch_image.png"
            (input_dir / mismatch_rel).write_bytes(b"real-mismatch-image")
            missing_rel = "files/0708/20260708113200_missing_image.png"

            with (manifest_dir / "manifest.csv").open("w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=[
                    "group_name",
                    "open_conversation_id",
                    "message_id",
                    "message_time",
                    "sender_name",
                    "sender_id",
                    "msg_type",
                    "resource_type",
                    "resource_id",
                    "original_filename",
                    "local_archive_path",
                    "output_path",
                    "sha256",
                    "size_bytes",
                    "download_method",
                    "status",
                ])
                writer.writeheader()
                writer.writerow({
                    "group_name": "付款请示群",
                    "open_conversation_id": "conv-1",
                    "message_id": "msg-missing-output",
                    "message_time": "2026-07-08T11:30:00+10:00",
                    "sender_name": "杨婷",
                    "sender_id": "sender-1",
                    "msg_type": "image",
                    "resource_type": "image",
                    "resource_id": "resource-missing-output",
                    "original_filename": "missing_output.png",
                    "local_archive_path": "",
                    "output_path": "",
                    "sha256": "",
                    "size_bytes": "",
                    "download_method": "dws",
                    "status": "failed",
                })
                writer.writerow({
                    "group_name": "付款请示群",
                    "open_conversation_id": "conv-1",
                    "message_id": "msg-missing-file",
                    "message_time": "2026-07-08T11:31:00+10:00",
                    "sender_name": "杨婷",
                    "sender_id": "sender-1",
                    "msg_type": "image",
                    "resource_type": "image",
                    "resource_id": "resource-missing-file",
                    "original_filename": "missing_file.png",
                    "local_archive_path": "",
                    "output_path": missing_rel,
                    "sha256": "0" * 64,
                    "size_bytes": "123",
                    "download_method": "dws",
                    "status": "downloaded",
                })
                writer.writerow({
                    "group_name": "付款请示群",
                    "open_conversation_id": "conv-1",
                    "message_id": "msg-hash-mismatch",
                    "message_time": "2026-07-08T11:32:00+10:00",
                    "sender_name": "杨婷",
                    "sender_id": "sender-1",
                    "msg_type": "image",
                    "resource_type": "image",
                    "resource_id": "resource-hash-mismatch",
                    "original_filename": "mismatch_image.png",
                    "local_archive_path": "",
                    "output_path": mismatch_rel,
                    "sha256": "f" * 64,
                    "size_bytes": str((input_dir / mismatch_rel).stat().st_size),
                    "download_method": "dws",
                    "status": "downloaded",
                })

            result = subprocess.run(
                [
                    sys.executable,
                    str(SKILL_ROOT / "tools" / "run_fund_weekly_analysis.py"),
                    "--repo-root",
                    str(repo_root),
                    "--input-dir",
                    str(input_dir),
                    "--run-id",
                    "attachment_remediation_dry_run_test",
                    "--timezone",
                    "Australia/Sydney",
                ],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            run_dir = repo_root / "KMFA/metadata/fund_weekly_analysis/private_runtime/runs/attachment_remediation_dry_run_test"
            with (run_dir / "attachment_remediation_dry_run.csv").open(encoding="utf-8-sig", newline="") as f:
                dry_run_rows = list(csv.DictReader(f))
            self.assertEqual(len(dry_run_rows), 3)
            statuses_by_message = {row["open_message_id"]: row["dry_run_status"] for row in dry_run_rows}
            self.assertEqual(statuses_by_message["msg-missing-output"], "dws_rerun_required")
            self.assertEqual(statuses_by_message["msg-missing-file"], "source_restore_required")
            self.assertEqual(statuses_by_message["msg-hash-mismatch"], "hash_mismatch_quarantine_required")
            self.assertTrue(all(row["safe_to_apply"] == "false" for row in dry_run_rows))
            self.assertTrue(all(row["apply_performed"] == "false" for row in dry_run_rows))
            self.assertTrue(all(row["formal_fact_allowed"] == "false" for row in dry_run_rows))

            cross_review = json.loads((run_dir / "cross_review.json").read_text(encoding="utf-8"))
            self.assertEqual(cross_review["attachment_remediation_dry_run_count"], 3)
            self.assertEqual(cross_review["attachment_remediation_apply_allowed_count"], 0)
            self.assertFalse(cross_review["management_conclusion_allowed"])
            self.assertEqual(cross_review["generated_financial_amount_count"], 0)

    def test_runner_emits_plan_only_attachment_repair_plan_from_dry_run_rows(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir) / "repo"
            input_dir = Path(temp_dir) / "OneDrive-Personal" / "DWS_Outputs" / "付款请示群"
            manifest_dir = input_dir / "_manifest"
            file_dir = input_dir / "files" / "0708"
            manifest_dir.mkdir(parents=True)
            file_dir.mkdir(parents=True)

            mismatch_rel = "files/0708/20260708113100_mismatch_image.png"
            (input_dir / mismatch_rel).write_bytes(b"real-mismatch-image")
            missing_rel = "files/0708/20260708113200_missing_image.png"

            with (manifest_dir / "manifest.csv").open("w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=[
                    "group_name",
                    "open_conversation_id",
                    "message_id",
                    "message_time",
                    "sender_name",
                    "sender_id",
                    "msg_type",
                    "resource_type",
                    "resource_id",
                    "original_filename",
                    "local_archive_path",
                    "output_path",
                    "sha256",
                    "size_bytes",
                    "download_method",
                    "status",
                ])
                writer.writeheader()
                writer.writerow({
                    "group_name": "付款请示群",
                    "open_conversation_id": "conv-1",
                    "message_id": "msg-missing-output",
                    "message_time": "2026-07-08T11:30:00+10:00",
                    "sender_name": "杨婷",
                    "sender_id": "sender-1",
                    "msg_type": "image",
                    "resource_type": "image",
                    "resource_id": "resource-missing-output",
                    "original_filename": "missing_output.png",
                    "local_archive_path": "",
                    "output_path": "",
                    "sha256": "",
                    "size_bytes": "",
                    "download_method": "dws",
                    "status": "failed",
                })
                writer.writerow({
                    "group_name": "付款请示群",
                    "open_conversation_id": "conv-1",
                    "message_id": "msg-missing-file",
                    "message_time": "2026-07-08T11:31:00+10:00",
                    "sender_name": "杨婷",
                    "sender_id": "sender-1",
                    "msg_type": "image",
                    "resource_type": "image",
                    "resource_id": "resource-missing-file",
                    "original_filename": "missing_file.png",
                    "local_archive_path": "",
                    "output_path": missing_rel,
                    "sha256": "0" * 64,
                    "size_bytes": "123",
                    "download_method": "dws",
                    "status": "downloaded",
                })
                writer.writerow({
                    "group_name": "付款请示群",
                    "open_conversation_id": "conv-1",
                    "message_id": "msg-hash-mismatch",
                    "message_time": "2026-07-08T11:32:00+10:00",
                    "sender_name": "杨婷",
                    "sender_id": "sender-1",
                    "msg_type": "image",
                    "resource_type": "image",
                    "resource_id": "resource-hash-mismatch",
                    "original_filename": "mismatch_image.png",
                    "local_archive_path": "",
                    "output_path": mismatch_rel,
                    "sha256": "f" * 64,
                    "size_bytes": str((input_dir / mismatch_rel).stat().st_size),
                    "download_method": "dws",
                    "status": "downloaded",
                })

            result = subprocess.run(
                [
                    sys.executable,
                    str(SKILL_ROOT / "tools" / "run_fund_weekly_analysis.py"),
                    "--repo-root",
                    str(repo_root),
                    "--input-dir",
                    str(input_dir),
                    "--run-id",
                    "attachment_repair_plan_test",
                    "--timezone",
                    "Australia/Sydney",
                ],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            run_dir = repo_root / "KMFA/metadata/fund_weekly_analysis/private_runtime/runs/attachment_repair_plan_test"
            with (run_dir / "attachment_repair_plan.csv").open(encoding="utf-8-sig", newline="") as f:
                plan_rows = list(csv.DictReader(f))
            self.assertEqual(len(plan_rows), 3)
            plan_by_message = {row["open_message_id"]: row for row in plan_rows}
            self.assertEqual(plan_by_message["msg-missing-output"]["repair_plan_status"], "plan_only_dws_rerun_pending")
            self.assertEqual(plan_by_message["msg-missing-file"]["repair_plan_status"], "plan_only_source_restore_pending")
            self.assertEqual(plan_by_message["msg-hash-mismatch"]["repair_plan_status"], "plan_only_quarantine_pending")
            self.assertTrue(all(row["operator_confirmation_required"] == "true" for row in plan_rows))
            self.assertTrue(all(row["source_mutation_allowed"] == "false" for row in plan_rows))
            self.assertTrue(all(row["apply_performed"] == "false" for row in plan_rows))
            self.assertTrue(all(row["formal_fact_allowed"] == "false" for row in plan_rows))

            with (run_dir / "attachment_repair_apply_gate.csv").open(encoding="utf-8-sig", newline="") as f:
                gate_rows = list(csv.DictReader(f))
            self.assertEqual(len(gate_rows), 3)
            self.assertTrue(all(row["operator_authorization_required"] == "true" for row in gate_rows))
            self.assertTrue(all(row["operator_authorization_present"] == "false" for row in gate_rows))
            self.assertTrue(all(row["apply_gate_status"] == "blocked_missing_operator_authorization" for row in gate_rows))
            self.assertTrue(all(row["apply_allowed"] == "false" for row in gate_rows))
            self.assertTrue(all(row["source_mutation_allowed"] == "false" for row in gate_rows))
            self.assertTrue(all(row["apply_performed"] == "false" for row in gate_rows))
            self.assertTrue(all(row["formal_fact_allowed"] == "false" for row in gate_rows))

            cross_review = json.loads((run_dir / "cross_review.json").read_text(encoding="utf-8"))
            self.assertEqual(cross_review["attachment_repair_plan_count"], 3)
            self.assertEqual(cross_review["attachment_repair_plan_open_count"], 3)
            self.assertEqual(cross_review["attachment_repair_apply_allowed_count"], 0)
            self.assertEqual(cross_review["attachment_repair_apply_gate_count"], 3)
            self.assertEqual(cross_review["attachment_repair_apply_blocked_count"], 3)
            self.assertEqual(cross_review["attachment_repair_authorization_present_count"], 0)
            self.assertFalse(cross_review["management_conclusion_allowed"])
            self.assertEqual(cross_review["generated_financial_amount_count"], 0)

    def test_runner_validates_private_attachment_repair_authorization_manifest_without_applying(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir) / "repo"
            input_dir = Path(temp_dir) / "OneDrive-Personal" / "DWS_Outputs" / "付款请示群"
            manifest_dir = input_dir / "_manifest"
            file_dir = input_dir / "files" / "0708"
            auth_dir = repo_root / "KMFA/metadata/fund_weekly_analysis/private_runtime/attachment_repair_authorizations"
            manifest_dir.mkdir(parents=True)
            file_dir.mkdir(parents=True)
            auth_dir.mkdir(parents=True)

            run_id = "attachment_authorization_schema_test"
            mismatch_rel = "files/0708/20260708113100_mismatch_image.png"
            (input_dir / mismatch_rel).write_bytes(b"real-mismatch-image")
            missing_rel = "files/0708/20260708113200_missing_image.png"

            with (manifest_dir / "manifest.csv").open("w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=[
                    "group_name",
                    "open_conversation_id",
                    "message_id",
                    "message_time",
                    "sender_name",
                    "sender_id",
                    "msg_type",
                    "resource_type",
                    "resource_id",
                    "original_filename",
                    "local_archive_path",
                    "output_path",
                    "sha256",
                    "size_bytes",
                    "download_method",
                    "status",
                ])
                writer.writeheader()
                writer.writerow({
                    "group_name": "付款请示群",
                    "open_conversation_id": "conv-1",
                    "message_id": "msg-missing-output",
                    "message_time": "2026-07-08T11:30:00+10:00",
                    "sender_name": "杨婷",
                    "sender_id": "sender-1",
                    "msg_type": "image",
                    "resource_type": "image",
                    "resource_id": "resource-missing-output",
                    "original_filename": "missing_output.png",
                    "local_archive_path": "",
                    "output_path": "",
                    "sha256": "",
                    "size_bytes": "",
                    "download_method": "dws",
                    "status": "failed",
                })
                writer.writerow({
                    "group_name": "付款请示群",
                    "open_conversation_id": "conv-1",
                    "message_id": "msg-missing-file",
                    "message_time": "2026-07-08T11:31:00+10:00",
                    "sender_name": "杨婷",
                    "sender_id": "sender-1",
                    "msg_type": "image",
                    "resource_type": "image",
                    "resource_id": "resource-missing-file",
                    "original_filename": "missing_file.png",
                    "local_archive_path": "",
                    "output_path": missing_rel,
                    "sha256": "0" * 64,
                    "size_bytes": "123",
                    "download_method": "dws",
                    "status": "downloaded",
                })
                writer.writerow({
                    "group_name": "付款请示群",
                    "open_conversation_id": "conv-1",
                    "message_id": "msg-hash-mismatch",
                    "message_time": "2026-07-08T11:32:00+10:00",
                    "sender_name": "杨婷",
                    "sender_id": "sender-1",
                    "msg_type": "image",
                    "resource_type": "image",
                    "resource_id": "resource-hash-mismatch",
                    "original_filename": "mismatch_image.png",
                    "local_archive_path": "",
                    "output_path": mismatch_rel,
                    "sha256": "f" * 64,
                    "size_bytes": str((input_dir / mismatch_rel).stat().st_size),
                    "download_method": "dws",
                    "status": "downloaded",
                })

            authorization_manifest = {
                "authorization_manifest_version": "1",
                "run_id": run_id,
                "authorization_scope": "attachment_repair_plan_validation_only",
                "authorized_by": "operator-fixture",
                "authorized_at": "2026-07-08T11:33:00+10:00",
                "authorization_ticket": "S33-TEST",
                "source_mutation_allowed": False,
                "apply_execution_allowed": False,
                "repair_plan_authorizations": [
                    {
                        "repair_plan_id": f"ATTACHPLAN-{run_id}-00001",
                        "required_command_family": "dws_archive_controlled_rerun",
                        "authorized": True,
                    },
                    {
                        "repair_plan_id": f"ATTACHPLAN-{run_id}-00002",
                        "required_command_family": "source_materialization_plan",
                        "authorized": True,
                    },
                ],
            }
            (auth_dir / f"{run_id}.json").write_text(
                json.dumps(authorization_manifest, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(SKILL_ROOT / "tools" / "run_fund_weekly_analysis.py"),
                    "--repo-root",
                    str(repo_root),
                    "--input-dir",
                    str(input_dir),
                    "--run-id",
                    run_id,
                    "--timezone",
                    "Australia/Sydney",
                ],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            run_dir = repo_root / f"KMFA/metadata/fund_weekly_analysis/private_runtime/runs/{run_id}"
            with (run_dir / "attachment_repair_apply_gate.csv").open(encoding="utf-8-sig", newline="") as f:
                gate_rows = list(csv.DictReader(f))
            self.assertEqual(len(gate_rows), 3)
            gates_by_plan = {row["repair_plan_id"]: row for row in gate_rows}
            self.assertEqual(gates_by_plan[f"ATTACHPLAN-{run_id}-00001"]["operator_authorization_present"], "true")
            self.assertEqual(gates_by_plan[f"ATTACHPLAN-{run_id}-00001"]["authorization_validation_status"], "valid_manifest_validation_only")
            self.assertEqual(gates_by_plan[f"ATTACHPLAN-{run_id}-00001"]["apply_gate_status"], "blocked_apply_engine_not_enabled")
            self.assertEqual(gates_by_plan[f"ATTACHPLAN-{run_id}-00002"]["operator_authorization_present"], "true")
            self.assertEqual(gates_by_plan[f"ATTACHPLAN-{run_id}-00003"]["operator_authorization_present"], "false")
            self.assertEqual(gates_by_plan[f"ATTACHPLAN-{run_id}-00003"]["authorization_validation_status"], "repair_plan_not_authorized")
            self.assertTrue(all(row["apply_allowed"] == "false" for row in gate_rows))
            self.assertTrue(all(row["source_mutation_allowed"] == "false" for row in gate_rows))
            self.assertTrue(all(row["apply_performed"] == "false" for row in gate_rows))
            self.assertTrue(all(row["formal_fact_allowed"] == "false" for row in gate_rows))

            with (run_dir / "attachment_repair_authorization_preview.csv").open(encoding="utf-8-sig", newline="") as f:
                preview_rows = list(csv.DictReader(f))
            self.assertEqual(len(preview_rows), 3)
            previews_by_plan = {row["repair_plan_id"]: row for row in preview_rows}
            self.assertEqual(
                previews_by_plan[f"ATTACHPLAN-{run_id}-00001"]["authorization_validation_status"],
                "valid_manifest_validation_only",
            )
            self.assertEqual(
                previews_by_plan[f"ATTACHPLAN-{run_id}-00001"]["preview_status"],
                "ready_for_operator_review_no_apply",
            )
            self.assertEqual(
                previews_by_plan[f"ATTACHPLAN-{run_id}-00002"]["preview_status"],
                "ready_for_operator_review_no_apply",
            )
            self.assertEqual(
                previews_by_plan[f"ATTACHPLAN-{run_id}-00003"]["preview_status"],
                "blocked_repair_plan_not_authorized",
            )
            self.assertTrue(all(row["apply_allowed"] == "false" for row in preview_rows))
            self.assertTrue(all(row["source_mutation_allowed"] == "false" for row in preview_rows))
            self.assertTrue(all(row["apply_performed"] == "false" for row in preview_rows))
            self.assertTrue(all(row["formal_fact_allowed"] == "false" for row in preview_rows))

            cross_review = json.loads((run_dir / "cross_review.json").read_text(encoding="utf-8"))
            self.assertEqual(cross_review["attachment_repair_apply_gate_count"], 3)
            self.assertEqual(cross_review["attachment_repair_apply_blocked_count"], 3)
            self.assertEqual(cross_review["attachment_repair_authorization_present_count"], 2)
            self.assertEqual(cross_review["attachment_repair_authorization_valid_count"], 2)
            self.assertEqual(cross_review["attachment_repair_authorization_preview_count"], 3)
            self.assertEqual(cross_review["attachment_repair_authorization_preview_ready_count"], 2)
            self.assertEqual(cross_review["attachment_repair_authorization_preview_blocked_count"], 1)
            self.assertEqual(cross_review["attachment_repair_apply_allowed_count"], 0)
            self.assertFalse(cross_review["management_conclusion_allowed"])
            self.assertEqual(cross_review["generated_financial_amount_count"], 0)

    def test_runner_emits_attachment_repair_authorization_template_without_authorizing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir) / "repo"
            input_dir = Path(temp_dir) / "OneDrive-Personal" / "DWS_Outputs" / "付款请示群"
            manifest_dir = input_dir / "_manifest"
            file_dir = input_dir / "files" / "0708"
            manifest_dir.mkdir(parents=True)
            file_dir.mkdir(parents=True)

            run_id = "attachment_authorization_template_test"
            missing_rel = "files/0708/20260708113200_missing_image.png"

            with (manifest_dir / "manifest.csv").open("w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=[
                    "group_name",
                    "open_conversation_id",
                    "message_id",
                    "message_time",
                    "sender_name",
                    "sender_id",
                    "msg_type",
                    "resource_type",
                    "resource_id",
                    "original_filename",
                    "local_archive_path",
                    "output_path",
                    "sha256",
                    "size_bytes",
                    "download_method",
                    "status",
                ])
                writer.writeheader()
                writer.writerow({
                    "group_name": "付款请示群",
                    "open_conversation_id": "conv-1",
                    "message_id": "msg-missing-output",
                    "message_time": "2026-07-08T11:30:00+10:00",
                    "sender_name": "杨婷",
                    "sender_id": "sender-1",
                    "msg_type": "image",
                    "resource_type": "image",
                    "resource_id": "resource-missing-output",
                    "original_filename": "missing_output.png",
                    "local_archive_path": "",
                    "output_path": "",
                    "sha256": "",
                    "size_bytes": "",
                    "download_method": "dws",
                    "status": "failed",
                })
                writer.writerow({
                    "group_name": "付款请示群",
                    "open_conversation_id": "conv-1",
                    "message_id": "msg-missing-file",
                    "message_time": "2026-07-08T11:31:00+10:00",
                    "sender_name": "杨婷",
                    "sender_id": "sender-1",
                    "msg_type": "image",
                    "resource_type": "image",
                    "resource_id": "resource-missing-file",
                    "original_filename": "missing_file.png",
                    "local_archive_path": "",
                    "output_path": missing_rel,
                    "sha256": "0" * 64,
                    "size_bytes": "123",
                    "download_method": "dws",
                    "status": "downloaded",
                })

            result = subprocess.run(
                [
                    sys.executable,
                    str(SKILL_ROOT / "tools" / "run_fund_weekly_analysis.py"),
                    "--repo-root",
                    str(repo_root),
                    "--input-dir",
                    str(input_dir),
                    "--run-id",
                    run_id,
                    "--timezone",
                    "Australia/Sydney",
                ],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            run_dir = repo_root / f"KMFA/metadata/fund_weekly_analysis/private_runtime/runs/{run_id}"
            template = json.loads((run_dir / "attachment_repair_authorization_template.json").read_text(encoding="utf-8"))
            self.assertEqual(template["authorization_manifest_version"], "1")
            self.assertEqual(template["run_id"], run_id)
            self.assertEqual(template["authorization_scope"], "attachment_repair_plan_validation_only")
            self.assertEqual(template["template_status"], "operator_review_required")
            self.assertFalse(template["source_mutation_allowed"])
            self.assertFalse(template["apply_execution_allowed"])
            self.assertEqual(
                template["output_authorization_manifest_relative_path"],
                f"KMFA/metadata/fund_weekly_analysis/private_runtime/attachment_repair_authorizations/{run_id}.json",
            )
            self.assertEqual(len(template["repair_plan_authorizations"]), 2)
            self.assertTrue(all(row["authorized"] is False for row in template["repair_plan_authorizations"]))

            with (run_dir / "attachment_repair_apply_gate.csv").open(encoding="utf-8-sig", newline="") as f:
                gate_rows = list(csv.DictReader(f))
            self.assertTrue(all(row["apply_allowed"] == "false" for row in gate_rows))
            self.assertTrue(all(row["apply_performed"] == "false" for row in gate_rows))

            cross_review = json.loads((run_dir / "cross_review.json").read_text(encoding="utf-8"))
            self.assertEqual(cross_review["attachment_repair_authorization_template_count"], 2)
            self.assertEqual(cross_review["attachment_repair_authorization_template_authorized_count"], 0)
            self.assertEqual(cross_review["attachment_repair_apply_allowed_count"], 0)
            self.assertFalse(cross_review["management_conclusion_allowed"])

    def test_runner_extracts_real_structured_csv_facts_without_management_conclusion(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir) / "repo"
            input_dir = Path(temp_dir) / "OneDrive-Personal" / "DWS_Outputs" / "付款请示群"
            source_day = input_dir / "files" / "0708"
            source_day.mkdir(parents=True)
            structured_csv = source_day / "20260708113000_吴云霞_资金日报.csv"
            structured_csv.write_text(
                "\n".join([
                    "date,company,bank,account_alias,liquidity_tier,inflow,outflow,ending_balance,flow_type,due_date,risk_type",
                    "2026-07-08,开明一公司,招商银行,基本户,T0_BANK_CASH,0,1000.00,9000.00,operating,,",
                    "2026-07-08,开明一公司,招商银行,基本户,T0_BANK_CASH,3000.00,0,12000.00,internal_transfer,,",
                    "2026-07-08,开明一公司,招商银行,基本户,T0_BANK_CASH,0,800.00,11200.00,tax,2026-07-15,tax_payable",
                    "2026-07-08,开明一公司,招商银行,基本户,T0_BANK_CASH,500.00,0,11700.00,deposit,2026-07-20,deposit_release",
                ]),
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(SKILL_ROOT / "tools" / "run_fund_weekly_analysis.py"),
                    "--repo-root",
                    str(repo_root),
                    "--input-dir",
                    str(input_dir),
                    "--run-id",
                    "structured_csv_test",
                    "--timezone",
                    "Australia/Sydney",
                ],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            run_dir = repo_root / "KMFA/metadata/fund_weekly_analysis/private_runtime/runs/structured_csv_test"
            manifest = json.loads((run_dir / "run_manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["status"], "STRUCTURED_FACTS_EXTRACTED_PENDING_REVIEW")
            self.assertEqual(manifest["structured_fact_count"], 4)

            with (run_dir / "fund_ledger.csv").open(encoding="utf-8-sig", newline="") as f:
                fund_rows = list(csv.DictReader(f))
            self.assertEqual(len(fund_rows), 4)
            self.assertEqual(fund_rows[0]["outflow"], "1000.00")
            self.assertTrue(all(row["extraction_status"] == "structured_csv_extracted_pending_review" for row in fund_rows))

            with (run_dir / "net_flow_ledger.csv").open(encoding="utf-8-sig", newline="") as f:
                net_rows = list(csv.DictReader(f))
            self.assertEqual(net_rows[0]["external_inflow"], "500.00")
            self.assertEqual(net_rows[0]["external_outflow"], "1800.00")
            self.assertEqual(net_rows[0]["internal_transfer_in"], "3000.00")
            self.assertEqual(net_rows[0]["internal_transfer_net"], "3000.00")

            with (run_dir / "company_bank_matrix.csv").open(encoding="utf-8-sig", newline="") as f:
                matrix_rows = list(csv.DictReader(f))
            self.assertEqual(len(matrix_rows), 1)
            self.assertEqual(matrix_rows[0]["ending_balance"], "11700.00")
            self.assertEqual(matrix_rows[0]["evidence_count"], "4")

            with (run_dir / "tax_loan_risk.csv").open(encoding="utf-8-sig", newline="") as f:
                risk_rows = list(csv.DictReader(f))
            self.assertEqual([row["risk_type"] for row in risk_rows], ["tax_payable", "deposit_release"])
            self.assertEqual([row["amount"] for row in risk_rows], ["800.00", "500.00"])

            with (run_dir / "evidence_index.csv").open(encoding="utf-8-sig", newline="") as f:
                evidence_rows = list(csv.DictReader(f))
            self.assertEqual(evidence_rows[0]["review_status"], "structured_csv_extracted_pending_review")

            cross_review = json.loads((run_dir / "cross_review.json").read_text(encoding="utf-8"))
            self.assertFalse(cross_review["management_conclusion_allowed"])
            self.assertEqual(cross_review["generated_financial_amount_count"], 0)
            self.assertEqual(cross_review["structured_financial_fact_count"], 4)

            workbook_path = run_dir / "资金与税费管理母版_structured_csv_test.xlsx"
            with zipfile.ZipFile(workbook_path) as workbook:
                self.assertIn("xl/drawings/drawing1.xml", workbook.namelist(), "homepage charts must remain attached")
                self.assertIn("可用现金占比", xlsx_cell_text(workbook, "xl/worksheets/sheet1.xml", "B4"))
                self.assertIn("100.00%", xlsx_cell_text(workbook, "xl/worksheets/sheet1.xml", "B4"))
                self.assertIn("银行存款", xlsx_cell_text(workbook, "xl/worksheets/sheet1.xml", "E4"))
                self.assertIn("¥11,700.00", xlsx_cell_text(workbook, "xl/worksheets/sheet1.xml", "E4"))
                self.assertIn("期末总资金", xlsx_cell_text(workbook, "xl/worksheets/sheet1.xml", "K4"))
                self.assertIn("¥11,700.00", xlsx_cell_text(workbook, "xl/worksheets/sheet1.xml", "K4"))
                self.assertIn("保证金可释放", xlsx_cell_text(workbook, "xl/worksheets/sheet1.xml", "B8"))
                self.assertIn("¥500.00", xlsx_cell_text(workbook, "xl/worksheets/sheet1.xml", "B8"))
                self.assertIn("外部净流出", xlsx_cell_text(workbook, "xl/worksheets/sheet1.xml", "E8"))
                self.assertIn("¥-1,300.00", xlsx_cell_text(workbook, "xl/worksheets/sheet1.xml", "E8"))
                self.assertIn("内部调拨净额", xlsx_cell_text(workbook, "xl/worksheets/sheet1.xml", "H8"))
                self.assertIn("¥3,000.00", xlsx_cell_text(workbook, "xl/worksheets/sheet1.xml", "H8"))

                self.assertEqual(
                    xlsx_cell_text(workbook, "xl/worksheets/sheet7.xml", "A2"),
                    "FL-structured_csv_test-00001",
                )
                self.assertEqual(xlsx_cell_text(workbook, "xl/worksheets/sheet7.xml", "B2"), "2026-07-08")
                self.assertEqual(xlsx_cell_text(workbook, "xl/worksheets/sheet7.xml", "C2"), "开明一公司")
                self.assertEqual(xlsx_cell_text(workbook, "xl/worksheets/sheet7.xml", "G2"), "-1000.00")
                self.assertTrue(
                    xlsx_cell_text(workbook, "xl/worksheets/sheet9.xml", "A4").startswith("FWstructured_csv_test")
                )
                self.assertIn(
                    "资金日报.csv",
                    xlsx_cell_text(workbook, "xl/worksheets/sheet9.xml", "B4"),
                )
                self.assertEqual(
                    xlsx_cell_text(workbook, "xl/worksheets/sheet9.xml", "K4"),
                    "structured_csv_extracted_pending_review",
                )

    def test_runner_builds_known_due_date_funding_forecast_from_structured_csv(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir) / "repo"
            input_dir = Path(temp_dir) / "OneDrive-Personal" / "DWS_Outputs" / "付款请示群"
            source_day = input_dir / "files" / "0708"
            source_day.mkdir(parents=True)
            structured_csv = source_day / "20260708113000_吴云霞_资金预测.csv"
            structured_csv.write_text(
                "\n".join([
                    "date,company,bank,account_alias,liquidity_tier,inflow,outflow,ending_balance,flow_type,due_date,risk_type",
                    "2026-07-08,开明一公司,招商银行,基本户,T0_BANK_CASH,0,1000.00,9000.00,operating,,",
                    "2026-07-08,开明一公司,招商银行,基本户,T0_BANK_CASH,3000.00,0,12000.00,internal_transfer,,",
                    "2026-07-08,开明一公司,招商银行,基本户,T0_BANK_CASH,0,800.00,11200.00,tax,2026-07-10,tax_payable",
                    "2026-07-08,开明一公司,招商银行,基本户,T0_BANK_CASH,500.00,0,11700.00,deposit,2026-07-09,deposit_release",
                    "2026-07-08,开明一公司,招商银行,基本户,T0_BANK_CASH,0,13000.00,11700.00,loan,2026-07-11,loan_repayment",
                ]),
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(SKILL_ROOT / "tools" / "run_fund_weekly_analysis.py"),
                    "--repo-root",
                    str(repo_root),
                    "--input-dir",
                    str(input_dir),
                    "--run-id",
                    "funding_forecast_test",
                    "--timezone",
                    "Australia/Sydney",
                ],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            run_dir = repo_root / "KMFA/metadata/fund_weekly_analysis/private_runtime/runs/funding_forecast_test"
            with (run_dir / "funding_forecast.csv").open(encoding="utf-8-sig", newline="") as f:
                forecast_rows = list(csv.DictReader(f))
            self.assertEqual([row["period_date"] for row in forecast_rows], ["2026-07-09", "2026-07-10", "2026-07-11"])
            self.assertEqual([row["known_inflow"] for row in forecast_rows], ["500.00", "0.00", "0.00"])
            self.assertEqual([row["known_outflow"] for row in forecast_rows], ["0.00", "800.00", "13000.00"])
            self.assertEqual([row["projected_bank_cash"] for row in forecast_rows], ["12200.00", "11400.00", "-1600.00"])
            self.assertEqual([row["funding_gap"] for row in forecast_rows], ["0.00", "0.00", "1600.00"])
            self.assertTrue(all(row["forecast_basis"] == "known_due_date_structured_csv" for row in forecast_rows))
            self.assertTrue(all(row["review_status"] == "structured_csv_forecast_pending_review" for row in forecast_rows))

            cross_review = json.loads((run_dir / "cross_review.json").read_text(encoding="utf-8"))
            self.assertFalse(cross_review["management_conclusion_allowed"])
            self.assertEqual(cross_review["forecast_row_count"], 3)

            workbook_path = run_dir / "资金与税费管理母版_funding_forecast_test.xlsx"
            with zipfile.ZipFile(workbook_path) as workbook:
                self.assertEqual(xlsx_cell_text(workbook, "xl/worksheets/sheet2.xml", "A4"), "预测/到期日")
                self.assertEqual(xlsx_cell_text(workbook, "xl/worksheets/sheet2.xml", "A5"), "2026-07-09")
                self.assertEqual(xlsx_cell_text(workbook, "xl/worksheets/sheet2.xml", "B5"), "500.00")
                self.assertEqual(xlsx_cell_text(workbook, "xl/worksheets/sheet2.xml", "D7"), "-1600.00")
                self.assertEqual(xlsx_cell_text(workbook, "xl/worksheets/sheet2.xml", "E7"), "1600.00")
                self.assertEqual(
                    xlsx_cell_text(workbook, "xl/worksheets/sheet2.xml", "H7"),
                    "structured_csv_forecast_pending_review",
                )

    def test_runner_validates_balance_continuity_and_operating_cashflow_without_conclusion(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir) / "repo"
            input_dir = Path(temp_dir) / "OneDrive-Personal" / "DWS_Outputs" / "付款请示群"
            source_day = input_dir / "files" / "0708"
            source_day.mkdir(parents=True)
            structured_csv = source_day / "20260708113000_吴云霞_现金流校验.csv"
            structured_csv.write_text(
                "\n".join([
                    "date,company,bank,account_alias,liquidity_tier,inflow,outflow,ending_balance,flow_type,due_date,risk_type",
                    "2026-07-08,开明一公司,招商银行,基本户,T0_BANK_CASH,0,0,1000.00,operating,,",
                    "2026-07-09,开明一公司,招商银行,基本户,T0_BANK_CASH,300.00,100.00,1200.00,operating,,",
                    "2026-07-10,开明一公司,招商银行,基本户,T0_BANK_CASH,500.00,0,1700.00,internal_transfer,,",
                    "2026-07-11,开明一公司,招商银行,基本户,T0_BANK_CASH,0,200.00,1600.00,operating,,",
                ]),
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(SKILL_ROOT / "tools" / "run_fund_weekly_analysis.py"),
                    "--repo-root",
                    str(repo_root),
                    "--input-dir",
                    str(input_dir),
                    "--run-id",
                    "cashflow_validation_test",
                    "--timezone",
                    "Australia/Sydney",
                ],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            run_dir = repo_root / "KMFA/metadata/fund_weekly_analysis/private_runtime/runs/cashflow_validation_test"
            with (run_dir / "cashflow_validation.csv").open(encoding="utf-8-sig", newline="") as f:
                validation_rows = list(csv.DictReader(f))
            self.assertEqual(len(validation_rows), 4)
            self.assertEqual(validation_rows[0]["validation_status"], "BASELINE")
            self.assertEqual(validation_rows[1]["validation_status"], "PASS")
            self.assertEqual(validation_rows[1]["operating_cashflow_effect"], "200.00")
            self.assertEqual(validation_rows[2]["flow_type"], "internal_transfer")
            self.assertEqual(validation_rows[2]["internal_transfer_excluded"], "true")
            self.assertEqual(validation_rows[2]["operating_cashflow_effect"], "0.00")
            self.assertEqual(validation_rows[3]["validation_status"], "FAIL")
            self.assertEqual(validation_rows[3]["continuity_diff"], "100.00")
            self.assertEqual(validation_rows[3]["review_status"], "balance_continuity_gap_pending_review")

            with (run_dir / "exception_tasks.csv").open(encoding="utf-8-sig", newline="") as f:
                task_rows = list(csv.DictReader(f))
            self.assertTrue(any(row["task_type"] == "BALANCE_CONTINUITY_GAP" for row in task_rows))

            cross_review = json.loads((run_dir / "cross_review.json").read_text(encoding="utf-8"))
            self.assertFalse(cross_review["management_conclusion_allowed"])
            self.assertEqual(cross_review["cashflow_validation_row_count"], 4)
            self.assertEqual(cross_review["balance_continuity_fail_count"], 1)
            self.assertEqual(cross_review["internal_transfer_excluded_count"], 1)

            workbook_path = run_dir / "资金与税费管理母版_cashflow_validation_test.xlsx"
            with zipfile.ZipFile(workbook_path) as workbook:
                self.assertEqual(
                    xlsx_cell_text(workbook, "xl/worksheets/sheet11.xml", "A12"),
                    "CV-cashflow_validation_test-00001",
                )
                self.assertEqual(xlsx_cell_text(workbook, "xl/worksheets/sheet11.xml", "D13"), "PASS")
                self.assertEqual(xlsx_cell_text(workbook, "xl/worksheets/sheet11.xml", "D15"), "FAIL")
                self.assertEqual(xlsx_cell_text(workbook, "xl/worksheets/sheet11.xml", "F15"), "是")

    def test_runner_emits_workbook_quality_checks_for_generated_package(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir) / "repo"
            input_dir = Path(temp_dir) / "OneDrive-Personal" / "DWS_Outputs" / "付款请示群"
            source_day = input_dir / "files" / "0708"
            source_day.mkdir(parents=True)
            structured_csv = source_day / "20260708113000_吴云霞_质量门禁.csv"
            structured_csv.write_text(
                "\n".join([
                    "date,company,bank,account_alias,liquidity_tier,inflow,outflow,ending_balance,flow_type,due_date,risk_type",
                    "2026-07-08,开明一公司,招商银行,基本户,T0_BANK_CASH,0,0,1000.00,operating,,",
                    "2026-07-09,开明一公司,招商银行,基本户,T0_BANK_CASH,100.00,0,1100.00,operating,,",
                ]),
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(SKILL_ROOT / "tools" / "run_fund_weekly_analysis.py"),
                    "--repo-root",
                    str(repo_root),
                    "--input-dir",
                    str(input_dir),
                    "--run-id",
                    "workbook_quality_test",
                    "--timezone",
                    "Australia/Sydney",
                ],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            run_dir = repo_root / "KMFA/metadata/fund_weekly_analysis/private_runtime/runs/workbook_quality_test"
            with (run_dir / "workbook_quality_checks.csv").open(encoding="utf-8-sig", newline="") as f:
                quality_rows = list(csv.DictReader(f))
            checks = {row["check_id"]: row for row in quality_rows}
            for check_id in (
                "WQ-SHEET-ORDER",
                "WQ-HIDDEN-SHEETS",
                "WQ-HOMEPAGE-CHART-SIZE",
                "WQ-FORMULA-ERRORS",
                "WQ-VISIBLE-SENSITIVE-TEXT",
            ):
                self.assertEqual(checks[check_id]["status"], "PASS", check_id)
            self.assertTrue(all(row["management_blocking"] == "false" for row in quality_rows))

            cross_review = json.loads((run_dir / "cross_review.json").read_text(encoding="utf-8"))
            self.assertFalse(cross_review["management_conclusion_allowed"])
            self.assertEqual(cross_review["workbook_quality_check_count"], len(quality_rows))
            self.assertEqual(cross_review["workbook_quality_blocking_count"], 0)

    def test_runner_carries_kmfa_metadata_signals_without_management_conclusion(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir) / "repo"
            input_dir = Path(temp_dir) / "OneDrive-Personal" / "DWS_Outputs" / "付款请示群"
            source_day = input_dir / "files" / "0708"
            source_day.mkdir(parents=True)
            (source_day / "20260708113000_杨婷_资金截图.png").write_bytes(b"real-image-bytes")

            reports_dir = repo_root / "KMFA/metadata/reports"
            lineage_dir = repo_root / "KMFA/metadata/lineage"
            quality_dir = repo_root / "KMFA/metadata/quality"
            reports_dir.mkdir(parents=True)
            lineage_dir.mkdir(parents=True)
            quality_dir.mkdir(parents=True)
            (reports_dir / "fund_cash_pressure_signals.jsonl").write_text(
                json.dumps({
                    "record_type": "cash_pressure_signal",
                    "pressure_level": "blocked",
                    "pressure_window": "twelve_week",
                    "visible_window": "12周",
                    "status_label": "缺 lineage full check 时不输出正式资金结论",
                    "report_grade_visible": "D",
                    "formal_report_allowed": False,
                    "bank_operation_allowed": False,
                    "stage_phase": "S14-P1",
                    "source_lane_refs": ["account_list", "fund_plan"],
                }, ensure_ascii=False)
                + "\n",
                encoding="utf-8",
            )
            (reports_dir / "project_cost_fact_layer_manifest.json").write_text(
                json.dumps({
                    "record_type": "project_cost_fact_layer_manifest",
                    "fact_layer_status": "structural_fact_layer_blocked_for_formal_calculation",
                    "stage_phase": "S09-P1",
                    "quality_gate": {"formal_report_allowed": False},
                    "required_fact_metrics": ["revenue", "cost_total"],
                }, ensure_ascii=False),
                encoding="utf-8",
            )
            (lineage_dir / "project_cost_fact_records.jsonl").write_text(
                json.dumps({
                    "record_type": "project_cost_fact_record",
                    "fact_record_id": "PCF-S09P1-001",
                    "calculation_status": "blocked_pending_quality_resolution",
                    "formal_calculation_allowed": False,
                    "project_entity_ref": "entity_ref://KMFA/S08-P2/project/001",
                    "stage_phase": "S09-P1",
                }, ensure_ascii=False)
                + "\n",
                encoding="utf-8",
            )
            (reports_dir / "report_grade_runtime_records.jsonl").write_text(
                json.dumps({
                    "record_type": "report_grade_runtime_record",
                    "report_record_id": "S10P2-GRADE-BUSINESS-OVERVIEW-REPORT",
                    "computed_report_grade": "D",
                    "release_permission": "blocked_decision_use",
                    "formal_report_allowed": True,
                    "business_decision_basis_allowed": True,
                    "stage_phase": "S10-P2",
                }, ensure_ascii=False)
                + "\n",
                encoding="utf-8",
            )
            (quality_dir / "scope_reconciliation_records.jsonl").write_text(
                json.dumps({
                    "record_type": "scope_reconciliation_record",
                    "difference_id": "S09P3-REC-001",
                    "resolution_status": "pending_owner_or_authorized_review",
                    "formal_report_rerun_allowed": False,
                    "impact_scope": "project_margin_formal_report_blocked_until_reconciled",
                    "stage_phase": "S09-P3",
                }, ensure_ascii=False)
                + "\n",
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(SKILL_ROOT / "tools" / "run_fund_weekly_analysis.py"),
                    "--repo-root",
                    str(repo_root),
                    "--input-dir",
                    str(input_dir),
                    "--run-id",
                    "metadata_signal_test",
                    "--timezone",
                    "Australia/Sydney",
                ],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            run_dir = repo_root / "KMFA/metadata/fund_weekly_analysis/private_runtime/runs/metadata_signal_test"
            manifest = json.loads((run_dir / "run_manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["status"], "INDEXED_PENDING_EXTRACTION")
            self.assertEqual(manifest["metadata_signal_count"], 5)

            with (run_dir / "kmfa_metadata_signals.csv").open(encoding="utf-8-sig", newline="") as f:
                metadata_rows = list(csv.DictReader(f))
            self.assertEqual(len(metadata_rows), 5)
            self.assertEqual(metadata_rows[0]["signal_type"], "cash_pressure_signal")
            self.assertEqual(metadata_rows[0]["status"], "blocked")
            self.assertEqual(metadata_rows[1]["signal_type"], "project_cost_fact_layer_manifest")
            self.assertTrue(all(row["formal_action_allowed"] == "false" for row in metadata_rows))
            self.assertTrue(all(row["review_status"] == "kmfa_metadata_pending_review" for row in metadata_rows))
            self.assertIn("s21_review_gate=false", metadata_rows[3]["remark"])

            cross_review = json.loads((run_dir / "cross_review.json").read_text(encoding="utf-8"))
            self.assertFalse(cross_review["management_conclusion_allowed"])
            self.assertEqual(cross_review["metadata_signal_count"], 5)

            workbook_path = run_dir / "资金与税费管理母版_metadata_signal_test.xlsx"
            with zipfile.ZipFile(workbook_path) as workbook:
                self.assertIn("KMFA元数据风险信号", xlsx_cell_text(workbook, "xl/worksheets/sheet4.xml", "A4"))
                self.assertIn("5条", xlsx_cell_text(workbook, "xl/worksheets/sheet4.xml", "A4"))
                self.assertEqual(
                    xlsx_cell_text(workbook, "xl/worksheets/sheet8.xml", "A4"),
                    "META-metadata_signal_test-00001",
                )
                self.assertEqual(
                    xlsx_cell_text(workbook, "xl/worksheets/sheet8.xml", "K4"),
                    "kmfa_metadata_pending_review",
                )

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

    def test_materialize_zip_candidate_is_explicit_and_group_scoped(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir) / "repo"
            one_drive = Path(temp_dir) / "OneDrive-Personal"
            source_zip = one_drive / "DWS_Outputs.zip"
            source_zip.parent.mkdir(parents=True)
            target = one_drive / "DWS_Outputs" / "付款请示群"
            group_payload = b"real-zipped-finance-evidence"
            with zipfile.ZipFile(source_zip, "w") as archive:
                archive.writestr("付款请示群/files/0708/20260708113000_杨婷_real_image.png", group_payload)
                archive.writestr("生产管理群/files/0708/ignore.png", b"other-group")
                archive.writestr("/付款请示群/files/0708/absolute.png", b"unsafe-absolute")
                archive.writestr("付款请示群/files/../unsafe.png", b"unsafe-parent")

            dry_run = subprocess.run(
                [
                    sys.executable,
                    str(SKILL_ROOT / "tools" / "materialize_fund_source.py"),
                    "--repo-root",
                    str(repo_root),
                    "--source-zip",
                    str(source_zip),
                    "--zip-prefix",
                    "付款请示群",
                    "--target-dir",
                    str(target),
                    "--run-id",
                    "materialize_zip_dry_run",
                    "--timezone",
                    "Australia/Sydney",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(dry_run.returncode, 0, dry_run.stderr)
            self.assertFalse(target.exists(), "zip dry-run must not create the target folder")
            dry_manifest = json.loads(
                (repo_root / "KMFA/metadata/fund_weekly_analysis/private_runtime/runs/materialize_zip_dry_run/source_materialization_manifest.json").read_text(encoding="utf-8")
            )
            self.assertEqual(dry_manifest["source_kind"], "zip")
            self.assertEqual(dry_manifest["zip_prefix"], "付款请示群")
            self.assertEqual(dry_manifest["planned_copy_count"], 1)
            self.assertEqual(dry_manifest["files"][0]["relative_path"], "files/0708/20260708113000_杨婷_real_image.png")
            self.assertEqual(dry_manifest["files"][0]["sha256"], sha256_bytes(group_payload))

            apply_run = subprocess.run(
                [
                    sys.executable,
                    str(SKILL_ROOT / "tools" / "materialize_fund_source.py"),
                    "--repo-root",
                    str(repo_root),
                    "--source-zip",
                    str(source_zip),
                    "--zip-prefix",
                    "付款请示群",
                    "--target-dir",
                    str(target),
                    "--run-id",
                    "materialize_zip_apply",
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
            self.assertEqual(copied_file.read_bytes(), group_payload)
            self.assertFalse((target.parent / "生产管理群").exists())

    def test_materialize_zip_accepts_dws_outputs_root_with_group_prefix(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir) / "repo"
            one_drive = Path(temp_dir) / "OneDrive-Personal"
            source_zip = one_drive / "DWS_Outputs.zip"
            source_zip.parent.mkdir(parents=True)
            target = one_drive / "DWS_Outputs" / "付款请示群"
            group_payload = b"real-zipped-finance-evidence-under-root"
            with zipfile.ZipFile(source_zip, "w") as archive:
                archive.writestr("DWS_Outputs/付款请示群/files/0708/20260708113000_杨婷_real_image.png", group_payload)
                archive.writestr("DWS_Outputs/生产管理群/files/0708/ignore.png", b"other-group")

            dry_run = subprocess.run(
                [
                    sys.executable,
                    str(SKILL_ROOT / "tools" / "materialize_fund_source.py"),
                    "--repo-root",
                    str(repo_root),
                    "--source-zip",
                    str(source_zip),
                    "--zip-prefix",
                    "付款请示群",
                    "--target-dir",
                    str(target),
                    "--run-id",
                    "materialize_zip_root_dry_run",
                    "--timezone",
                    "Australia/Sydney",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(dry_run.returncode, 0, dry_run.stderr)
            self.assertFalse(target.exists(), "zip dry-run must not create the target folder")
            dry_manifest = json.loads(
                (repo_root / "KMFA/metadata/fund_weekly_analysis/private_runtime/runs/materialize_zip_root_dry_run/source_materialization_manifest.json").read_text(encoding="utf-8")
            )
            self.assertEqual(dry_manifest["planned_copy_count"], 1)
            self.assertEqual(dry_manifest["files"][0]["relative_path"], "files/0708/20260708113000_杨婷_real_image.png")
            self.assertEqual(dry_manifest["files"][0]["zip_member"], "DWS_Outputs/付款请示群/files/0708/20260708113000_杨婷_real_image.png")
            self.assertEqual(dry_manifest["files"][0]["sha256"], sha256_bytes(group_payload))

    def test_materialize_zip_fails_fast_when_source_zip_is_dataless(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            materialize_module = load_materialize_module()
            materialize_module.macos_file_flags = lambda _path: "compressed,dataless"
            run_dir = Path(temp_dir) / "repo" / "KMFA/metadata/fund_weekly_analysis/private_runtime/runs/dataless_zip"
            source_zip = Path(temp_dir) / "OneDrive-Personal" / "DWS_Outputs.zip"
            source_zip.parent.mkdir(parents=True)
            with zipfile.ZipFile(source_zip, "w") as archive:
                archive.writestr("付款请示群/files/0708/real.png", b"real-source")
            target = Path(temp_dir) / "OneDrive-Personal" / "DWS_Outputs" / "付款请示群"

            with contextlib.redirect_stdout(io.StringIO()):
                exit_code = materialize_module.materialize_zip(
                    source_zip,
                    "付款请示群",
                    target,
                    run_dir,
                    "Australia/Sydney",
                    False,
                )

            self.assertEqual(exit_code, 5)
            self.assertFalse(target.exists())
            manifest = json.loads((run_dir / "source_materialization_manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["status"], "SOURCE_UNREADABLE")
            self.assertEqual(manifest["source_kind"], "zip")
            self.assertEqual(manifest["unreadable_count"], 1)
            self.assertEqual(manifest["unreadable"][0]["error_type"], "DatalessFile")

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

    def test_source_readiness_reports_missing_target_and_private_candidates(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir) / "repo"
            one_drive = Path(temp_dir) / "OneDrive-Personal"
            target = one_drive / "DWS_Outputs" / "付款请示群"
            archive = one_drive / "DWS_Archive" / "付款请示群"
            archive_file = archive / "files" / "0708" / "real.png"
            archive_file.parent.mkdir(parents=True)
            archive_file.write_bytes(b"real-source")
            (one_drive / "DWS_Outputs.zip").write_bytes(b"zip-placeholder")

            result = subprocess.run(
                [
                    sys.executable,
                    str(SKILL_ROOT / "tools" / "check_source_readiness.py"),
                    "--repo-root",
                    str(repo_root),
                    "--target-dir",
                    str(target),
                    "--run-id",
                    "readiness_missing",
                    "--timezone",
                    "Australia/Sydney",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 2, result.stderr)
            report = json.loads(
                (repo_root / "KMFA/metadata/fund_weekly_analysis/private_runtime/runs/readiness_missing/source_readiness.json").read_text(encoding="utf-8")
            )
            self.assertEqual(report["status"], "SOURCE_MISSING")
            candidates = {item["kind"]: item for item in report["source_candidates"]}
            self.assertTrue(candidates["dws_archive_group"]["exists"])
            self.assertEqual(candidates["dws_archive_group"]["file_count"], 1)
            self.assertTrue(candidates["dws_outputs_zip"]["exists"])

    def test_source_readiness_ready_when_target_files_are_local_and_readable(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir) / "repo"
            target = Path(temp_dir) / "OneDrive-Personal" / "DWS_Outputs" / "付款请示群"
            file_path = target / "files" / "0708" / "real.png"
            file_path.parent.mkdir(parents=True)
            file_path.write_bytes(b"real-source")

            result = subprocess.run(
                [
                    sys.executable,
                    str(SKILL_ROOT / "tools" / "check_source_readiness.py"),
                    "--repo-root",
                    str(repo_root),
                    "--target-dir",
                    str(target),
                    "--run-id",
                    "readiness_ready",
                    "--timezone",
                    "Australia/Sydney",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(
                (repo_root / "KMFA/metadata/fund_weekly_analysis/private_runtime/runs/readiness_ready/source_readiness.json").read_text(encoding="utf-8")
            )
            self.assertEqual(report["status"], "READY")
            self.assertEqual(report["target"]["file_count"], 1)
            self.assertEqual(report["target"]["unreadable_count"], 0)

    def test_source_readiness_fails_closed_when_target_has_unreadable_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir) / "repo"
            target = Path(temp_dir) / "OneDrive-Personal" / "DWS_Outputs" / "付款请示群"
            unreadable_file = target / "files" / "0708" / "unreadable.png"
            unreadable_file.parent.mkdir(parents=True)
            unreadable_file.write_bytes(b"not-readable")
            unreadable_file.chmod(0)
            try:
                result = subprocess.run(
                    [
                        sys.executable,
                        str(SKILL_ROOT / "tools" / "check_source_readiness.py"),
                        "--repo-root",
                        str(repo_root),
                        "--target-dir",
                        str(target),
                        "--run-id",
                        "readiness_unreadable",
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
            report = json.loads(
                (repo_root / "KMFA/metadata/fund_weekly_analysis/private_runtime/runs/readiness_unreadable/source_readiness.json").read_text(encoding="utf-8")
            )
            self.assertEqual(report["status"], "SOURCE_UNREADABLE")
            self.assertEqual(report["target"]["unreadable_count"], 1)


if __name__ == "__main__":
    unittest.main()
