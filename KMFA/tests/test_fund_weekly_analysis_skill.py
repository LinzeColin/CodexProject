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


def load_owner_review_export_module():
    module_path = SKILL_ROOT / "tools" / "export_owner_decision_review_csv.py"
    spec = importlib.util.spec_from_file_location("owner_review_export_for_test", module_path)
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
    def run_daily_with_stubbed_tools(
        self,
        readiness_exit: int,
        generated_sidecar_count: int = 0,
        env_overrides: dict[str, str] | None = None,
    ) -> tuple[subprocess.CompletedProcess[str], Path]:
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
            "  *generate_screenshot_ocr_sidecars.py) echo '{\"generated_sidecar_count\":"
            f"{generated_sidecar_count}"
            "}'; exit 0 ;;\n"
            "  *) exit 8 ;;\n"
            "esac\n",
            encoding="utf-8",
        )
        python_stub.chmod(0o755)

        codex_stub = bin_dir / "codex"
        codex_stub.write_text(
            "#!/usr/bin/env bash\n"
            "set -euo pipefail\n"
            f"echo codex:$* >> {call_log}\n"
            "cat >/dev/null\n"
            "exit 0\n",
            encoding="utf-8",
        )
        codex_stub.chmod(0o755)

        env = os.environ.copy()
        env["KMFA_REPO_ROOT"] = str(repo_root)
        env["KMFA_FUND_INPUT_DIR"] = str(temp_root / "OneDrive-Personal" / "DWS_Outputs" / "付款请示群")
        env["PATH"] = f"{bin_dir}:/usr/bin:/bin"
        if env_overrides:
            env.update(env_overrides)
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
        self.assertIn("--retry-timeout-seconds 30", ocr_call)
        self.assertIn("--retry-batch-size 1", ocr_call)
        self.assertIn("--retry-max-rows 24", ocr_call)
        self.assertNotIn("--limit", ocr_call)

    def test_daily_entrypoint_supports_vision_limit_for_validation_runs(self) -> None:
        result, call_log = self.run_daily_with_stubbed_tools(
            readiness_exit=0,
            env_overrides={"KMFA_FUND_VISION_LIMIT": "4"},
        )
        calls = call_log.read_text(encoding="utf-8").splitlines()
        ocr_call = next(call for call in calls if "generate_screenshot_ocr_sidecars.py" in call)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--limit 4", ocr_call)

    def test_daily_entrypoint_reruns_runner_after_new_private_vision_sidecars(self) -> None:
        result, call_log = self.run_daily_with_stubbed_tools(readiness_exit=0, generated_sidecar_count=1)
        calls = call_log.read_text(encoding="utf-8").splitlines()
        runner_indexes = [i for i, call in enumerate(calls) if "run_fund_weekly_analysis.py" in call]
        ocr_index = next(i for i, call in enumerate(calls) if "generate_screenshot_ocr_sidecars.py" in call)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(runner_indexes), 2, calls)
        self.assertLess(runner_indexes[0], ocr_index)
        self.assertLess(ocr_index, runner_indexes[1])
        self.assertIn("--run-id daily_stub", calls[runner_indexes[1]])

    def test_daily_entrypoint_supports_explicit_run_id_and_skip_codex_for_validation(self) -> None:
        result, call_log = self.run_daily_with_stubbed_tools(
            readiness_exit=0,
            env_overrides={
                "KMFA_FUND_RUN_ID": "s55_validation_run",
                "KMFA_SKIP_CODEX_EXEC": "1",
            },
        )
        calls = call_log.read_text(encoding="utf-8").splitlines()
        runner_call = next(call for call in calls if "run_fund_weekly_analysis.py" in call)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--run-id s55_validation_run", runner_call)
        self.assertFalse(any(call.startswith("codex:") for call in calls), calls)

    def test_skill_package_uses_sydney_weekly_mon_sat_1100_local_schedule_and_real_input(self) -> None:
        self.assertTrue(SKILL_ROOT.exists(), "fund-weekly-analysis-skill package must exist under KMFA")
        skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        config = (SKILL_ROOT / "templates" / "fund_weekly_analysis_config.yaml").read_text(encoding="utf-8")
        plist = (SKILL_ROOT / "automation" / "launchd" / "com.kmfa.fund-weekly-analysis.plist").read_text(
            encoding="utf-8"
        )
        prompt = (SKILL_ROOT / "automation" / "weekly_mon_sat_1100_sydney.prompt.md").read_text(encoding="utf-8")

        for text in (skill, config, prompt):
            self.assertIn("Australia/Sydney", text)
            self.assertIn("11:00", text)
            self.assertIn("/Users/linzezhang/Library/CloudStorage/OneDrive-Personal/DWS_Outputs/付款请示群", text)
        self.assertIn("Monday and Saturday", prompt)
        self.assertIn("No simulation", skill)
        self.assertIn("Do not use simulated", prompt)

        self.assertRegex(config, r'schedule_local:\s*"11:00"')
        self.assertRegex(config, r'schedule_days:\s*\["Monday", "Saturday"\]')
        self.assertRegex(config, r'timezone:\s*Australia/Sydney')
        self.assertRegex(plist, r"<key>Hour</key>\s*<integer>11</integer>")
        self.assertRegex(plist, r"<key>Minute</key>\s*<integer>0</integer>")
        self.assertRegex(plist, r"<key>Weekday</key>\s*<integer>1</integer>")
        self.assertRegex(plist, r"<key>Weekday</key>\s*<integer>6</integer>")

    def test_taskpack_validator_requires_daily_shell_entrypoint(self) -> None:
        validator = (SKILL_ROOT / "tools" / "validate_taskpack.py").read_text(encoding="utf-8")
        self.assertIn('"tools/run_daily_local.sh"', validator)

    def test_codex_app_automation_contract_mirrors_weekly_mon_sat_1100_local_cron(self) -> None:
        contract_path = SKILL_ROOT / "automation" / "codex_app_automation.contract.toml"
        self.assertTrue(contract_path.exists(), "public-safe Codex App automation contract must be tracked")
        contract = tomllib.loads(contract_path.read_text(encoding="utf-8"))

        self.assertEqual(contract["id"], "kmfa")
        self.assertEqual(contract["name"], "KMFA资金周报自动化")
        self.assertEqual(contract["kind"], "cron")
        self.assertEqual(contract["status"], "ACTIVE")
        self.assertEqual(contract["rrule"], "FREQ=WEEKLY;BYDAY=MO,SA;BYHOUR=11;BYMINUTE=0")
        self.assertEqual(contract["timezone"], "Australia/Sydney")
        self.assertEqual(contract["execution_environment"], "local")
        self.assertEqual(
            contract["cwds"],
            [
                "/Users/linzezhang/Documents/Codex/workspaces/dws-kmfa-automation/dws-archive",
                "/Users/linzezhang/Documents/Codex/workspaces/dws-kmfa-automation/kmfa-codexproject",
            ],
        )
        self.assertEqual(contract["prompt_file"], "automation/weekly_mon_sat_1100_sydney.prompt.md")
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

    def test_codex_app_automation_check_fails_closed_on_timezone_drift(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            repo_root = temp_root / "repo"
            contract_dir = repo_root / "KMFA/fund-weekly-analysis-skill/automation"
            contract_dir.mkdir(parents=True)
            contract = (SKILL_ROOT / "automation" / "codex_app_automation.contract.toml").read_text(encoding="utf-8")
            (contract_dir / "codex_app_automation.contract.toml").write_text(contract, encoding="utf-8")
            automation_dir = temp_root / "automations" / "kmfa"
            automation_dir.mkdir(parents=True)
            live = contract.replace('timezone = "Australia/Sydney"', 'timezone = "Asia/Shanghai"')
            (automation_dir / "automation.toml").write_text(live, encoding="utf-8")

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

            self.assertEqual(result.returncode, 4)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["status"], "CODEX_AUTOMATION_MISMATCH")
            self.assertIn("timezone", {row["field"] for row in payload["mismatches"]})

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
            contract_dir = repo_root / "KMFA/fund-weekly-analysis-skill/automation"
            contract_dir.mkdir(parents=True)
            contract = (SKILL_ROOT / "automation" / "codex_app_automation.contract.toml").read_text(encoding="utf-8")
            prompt = (SKILL_ROOT / "automation" / "weekly_mon_sat_1100_sydney.prompt.md").read_text(encoding="utf-8")
            (contract_dir / "codex_app_automation.contract.toml").write_text(contract, encoding="utf-8")
            (contract_dir / "weekly_mon_sat_1100_sydney.prompt.md").write_text(prompt, encoding="utf-8")
            automation_root = Path(temp_dir) / "automations"
            automation_dir = automation_root / "kmfa"
            automation_dir.mkdir(parents=True)
            (automation_dir / "automation.toml").write_text(contract + "\nprompt = '''" + prompt + "'''\n", encoding="utf-8")
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
                    "--automation-root",
                    str(automation_root),
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
                "ocr_financial_fact_candidates.csv",
                "ocr_fact_cross_review.csv",
                "ocr_fact_owner_review_batch.csv",
                "ocr_fact_evidence_review_queue.csv",
                "ocr_fact_candidate_owner_worklist.csv",
                "ocr_fact_candidate_owner_decision_template.json",
                "ocr_fact_candidate_owner_decision_preview.csv",
                "ocr_fact_candidate_owner_decision_progress_summary.csv",
                "ocr_fact_candidate_owner_authorization_update_draft.json",
                "ocr_fact_candidate_owner_authorization_update_preview.csv",
                "ocr_fact_ledger_staging_preview.csv",
                "ocr_fact_controlled_ledger_row_preview.csv",
                "ocr_fact_controlled_ledger_apply_gate.csv",
                "ocr_fact_owner_decision_correction_queue.csv",
                "ocr_fact_owner_decision_correction_draft.json",
                "ocr_fact_owner_decision_correction_apply_preview.csv",
                "ocr_fact_owner_decision_correction_roundtrip_audit.csv",
                "ocr_fact_owner_decision_correction_evidence_packet.csv",
                "ocr_fact_owner_decision_correction_ocr_line_context.csv",
                "ocr_fact_owner_decision_correction_chat_context.csv",
                "ocr_fact_owner_decision_correction_chat_neighbor_context.csv",
                "ocr_fact_owner_decision_correction_owner_review_packet.csv",
                "ocr_fact_owner_decision_correction_manifest_readiness.csv",
                "ocr_fact_review_apply_gate.csv",
                "ocr_fact_review_authorization_template.json",
                "ocr_fact_review_authorization_preview.csv",
                "chat_text_candidates.csv",
                "chat_value_candidates.csv",
                "chat_evidence_links.csv",
                "attachment_evidence_reconciliation.csv",
                "attachment_reconciliation_remediation.csv",
                "attachment_repair_source_locator.csv",
                "attachment_remediation_dry_run.csv",
                "attachment_repair_plan.csv",
                "attachment_repair_apply_gate.csv",
                "attachment_repair_authorization_template.json",
                "attachment_repair_authorization_preview.csv",
                "workbook_quality_checks.csv",
                "kmfa_metadata_signals.csv",
                "automation_readiness.csv",
                "goal_completion_audit.csv",
                "evidence_cross_review_resolution_plan.csv",
                "management_conclusion_gate.csv",
                "owner_action_queue.csv",
                "fact_promotion_review_packet.csv",
                "fact_promotion_owner_review_batch.csv",
                "fact_promotion_authorization_template.json",
                "fact_promotion_authorization_preview.csv",
                "fact_promotion_execution_gate.csv",
                "fact_promotion_execution_dry_run.csv",
                "fact_promotion_execution_plan.csv",
                "fact_promotion_execution_authorization_template.json",
                "fact_promotion_execution_authorization_preview.csv",
                "fact_promotion_execution_apply_gate.csv",
                "fact_promotion_execution_result.csv",
                "formal_fund_ledger.csv",
                "management_conclusion_authorization_template.json",
                "management_conclusion_authorization_preview.csv",
                "exception_tasks.csv",
                "cross_review.json",
                "audit_log.json",
                "run_summary.md",
            ]
            for name in required_outputs:
                self.assertTrue((run_dir / name).exists(), name)

            with zipfile.ZipFile(run_dir / "资金与税费管理母版_indexed_package_test.xlsx") as workbook:
                self.assertIn("xl/workbook.xml", workbook.namelist())
                self.assertEqual(xlsx_cell_text(workbook, "xl/worksheets/sheet12.xml", "A2"), "run_id")
                self.assertEqual(xlsx_cell_text(workbook, "xl/worksheets/sheet12.xml", "B2"), "indexed_package_test")
                self.assertEqual(xlsx_cell_text(workbook, "xl/worksheets/sheet12.xml", "A5"), "schedule_rrule")
                self.assertEqual(
                    xlsx_cell_text(workbook, "xl/worksheets/sheet12.xml", "B5"),
                    "FREQ=WEEKLY;BYDAY=MO,SA;BYHOUR=11;BYMINUTE=0",
                )
                self.assertEqual(xlsx_cell_text(workbook, "xl/worksheets/sheet12.xml", "A8"), "fact_promotion_execution_allowed")
                self.assertEqual(xlsx_cell_text(workbook, "xl/worksheets/sheet12.xml", "B8"), "false")
                self.assertEqual(xlsx_cell_text(workbook, "xl/worksheets/sheet12.xml", "A9"), "management_conclusion_allowed")
                self.assertEqual(xlsx_cell_text(workbook, "xl/worksheets/sheet12.xml", "B9"), "false")

            with (run_dir / "exception_tasks.csv").open(encoding="utf-8-sig", newline="") as f:
                rows = list(csv.DictReader(f))
            task_type_counts = {task_type: sum(row["task_type"] == task_type for row in rows) for task_type in {row["task_type"] for row in rows}}
            self.assertEqual(task_type_counts["PENDING_OCR_OR_REVIEW"], 2)
            self.assertEqual(task_type_counts["SCREENSHOT_OCR_MISSING"], 1)

            cross_review = json.loads((run_dir / "cross_review.json").read_text(encoding="utf-8"))
            self.assertFalse(cross_review["management_conclusion_allowed"])
            self.assertEqual(cross_review["generated_financial_amount_count"], 0)
            self.assertEqual(cross_review["screenshot_ocr_missing_count"], 1)

            with (run_dir / "evidence_cross_review_resolution_plan.csv").open(encoding="utf-8-sig", newline="") as f:
                evidence_plan_rows = list(csv.DictReader(f))
            self.assertEqual(len(evidence_plan_rows), 1)
            self.assertEqual(evidence_plan_rows[0]["evidence_area"], "screenshot_ocr_coverage")
            self.assertEqual(evidence_plan_rows[0]["source_artifact"], "screenshot_ocr_coverage.csv")
            self.assertEqual(evidence_plan_rows[0]["blocker_count"], "1")
            self.assertEqual(evidence_plan_rows[0]["resolution_status"], "blocked_missing_ocr_sidecars")
            self.assertEqual(evidence_plan_rows[0]["required_owner_action"], "run_or_attach_reviewed_ocr_sidecars")
            self.assertEqual(evidence_plan_rows[0]["management_conclusion_allowed"], "false")
            self.assertEqual(cross_review["evidence_cross_review_resolution_plan_count"], 1)
            self.assertEqual(cross_review["evidence_cross_review_resolution_plan_blocker_count"], 1)

            with (run_dir / "goal_completion_audit.csv").open(encoding="utf-8-sig", newline="") as f:
                audit_rows = list(csv.DictReader(f))
            audit_by_id = {row["requirement_id"]: row for row in audit_rows}
            self.assertEqual(audit_by_id["no_hallucinated_data"]["audit_status"], "pass")
            self.assertEqual(audit_by_id["automation_schedule"]["audit_status"], "pass")
            self.assertEqual(audit_by_id["automation_schedule"]["blocking"], "false")
            self.assertEqual(audit_by_id["formal_financial_fact_promotion"]["audit_status"], "blocked")
            self.assertEqual(audit_by_id["management_conclusion"]["audit_status"], "blocked")
            self.assertEqual(audit_by_id["management_conclusion"]["blocking"], "true")

            with (run_dir / "fact_promotion_review_packet.csv").open(encoding="utf-8-sig", newline="") as f:
                review_packet_rows = list(csv.DictReader(f))
            packet_by_area = {row["review_area"]: row for row in review_packet_rows}
            self.assertEqual(packet_by_area["screenshot_ocr_coverage"]["candidate_count"], "1")
            self.assertEqual(packet_by_area["screenshot_ocr_coverage"]["ready_count"], "0")
            self.assertEqual(packet_by_area["screenshot_ocr_coverage"]["blocked_count"], "1")
            self.assertEqual(packet_by_area["screenshot_ocr_coverage"]["review_status"], "blocked_ocr_sidecar_missing")
            self.assertEqual(packet_by_area["screenshot_ocr_coverage"]["authorization_required"], "false")
            self.assertEqual(packet_by_area["screenshot_ocr_coverage"]["fund_ledger_write_allowed"], "false")

            with (run_dir / "automation_readiness.csv").open(encoding="utf-8-sig", newline="") as f:
                automation_rows = list(csv.DictReader(f))
            self.assertEqual(len(automation_rows), 1)
            self.assertEqual(automation_rows[0]["status"], "CODEX_AUTOMATION_READY")
            self.assertEqual(automation_rows[0]["rrule"], "FREQ=WEEKLY;BYDAY=MO,SA;BYHOUR=11;BYMINUTE=0")
            self.assertEqual(automation_rows[0]["expected_timezone"], "Australia/Sydney")
            self.assertEqual(automation_rows[0]["schedule_ready"], "true")
            self.assertEqual(automation_rows[0]["management_conclusion_allowed"], "false")
            self.assertEqual(cross_review["automation_readiness_status"], "CODEX_AUTOMATION_READY")
            self.assertEqual(cross_review["automation_readiness_ready_count"], 1)
            self.assertEqual(cross_review["automation_readiness_blocking_count"], 0)

            with (run_dir / "management_conclusion_gate.csv").open(encoding="utf-8-sig", newline="") as f:
                management_gate_rows = list(csv.DictReader(f))
            self.assertEqual(len(management_gate_rows), 8)
            gate_by_area = {row["gate_area"]: row for row in management_gate_rows}
            self.assertEqual(gate_by_area["source_readiness"]["gate_status"], "ready")
            self.assertEqual(gate_by_area["native_workbook_quality"]["gate_status"], "ready")
            self.assertEqual(
                gate_by_area["formal_fact_promotion_execution"]["gate_status"],
                "blocked_fact_promotion_not_executed",
            )
            self.assertEqual(
                gate_by_area["management_conclusion_final_authorization"]["gate_status"],
                "blocked_management_conclusion_release_not_authorized",
            )
            self.assertIn(
                "release_authorization_preview_status=blocked_release_preconditions_not_ready",
                gate_by_area["management_conclusion_final_authorization"]["evidence"],
            )
            self.assertEqual(gate_by_area["automation_schedule"]["gate_status"], "ready")
            self.assertTrue(all(row["management_conclusion_allowed"] == "false" for row in management_gate_rows))
            self.assertEqual(cross_review["management_conclusion_gate_count"], 8)
            self.assertEqual(cross_review["management_conclusion_gate_ready_count"], 3)
            self.assertEqual(cross_review["management_conclusion_gate_blocked_count"], 5)
            self.assertFalse(cross_review["management_conclusion_allowed"])

            release_template = json.loads(
                (run_dir / "management_conclusion_authorization_template.json").read_text(encoding="utf-8")
            )
            self.assertEqual(release_template["authorization_scope"], "management_conclusion_release_validation_only")
            self.assertFalse(release_template["management_conclusion_allowed"])
            self.assertEqual(len(release_template["release_authorizations"]), 1)
            self.assertEqual(release_template["release_authorizations"][0]["pre_release_blocking_count"], 4)

            with (run_dir / "management_conclusion_authorization_preview.csv").open(
                encoding="utf-8-sig",
                newline="",
            ) as f:
                release_preview_rows = list(csv.DictReader(f))
            self.assertEqual(len(release_preview_rows), 1)
            self.assertEqual(release_preview_rows[0]["authorization_validation_status"], "missing_release_authorization_manifest")
            self.assertEqual(release_preview_rows[0]["preview_status"], "blocked_release_preconditions_not_ready")
            self.assertEqual(release_preview_rows[0]["pre_release_blocking_count"], "4")
            self.assertEqual(release_preview_rows[0]["management_conclusion_allowed"], "false")
            self.assertEqual(cross_review["management_conclusion_release_authorization_preview_count"], 1)
            self.assertEqual(cross_review["management_conclusion_release_authorization_preview_ready_count"], 0)
            self.assertEqual(cross_review["management_conclusion_release_authorization_preview_blocked_count"], 1)

            with (run_dir / "owner_action_queue.csv").open(encoding="utf-8-sig", newline="") as f:
                owner_action_rows = list(csv.DictReader(f))
            self.assertEqual(len(owner_action_rows), 5)
            action_by_gate = {row["source_gate"]: row for row in owner_action_rows}
            self.assertEqual(
                action_by_gate["formal_fact_promotion_execution"]["action_type"],
                "APPROVE_CONTROLLED_FACT_PROMOTION_EXECUTION",
            )
            self.assertEqual(
                action_by_gate["management_conclusion_final_authorization"]["action_type"],
                "APPROVE_MANAGEMENT_CONCLUSION_RELEASE",
            )
            self.assertNotIn("automation_schedule", action_by_gate)
            self.assertTrue(all(row["automation_safe"] == "false" for row in owner_action_rows))
            self.assertTrue(all(row["source_mutation_allowed"] == "false" for row in owner_action_rows))
            self.assertTrue(all(row["fact_promotion_allowed"] == "false" for row in owner_action_rows))
            self.assertTrue(all(row["fund_ledger_write_allowed"] == "false" for row in owner_action_rows))
            self.assertTrue(all(row["management_conclusion_allowed"] == "false" for row in owner_action_rows))
            self.assertEqual(cross_review["owner_action_queue_count"], 5)
            self.assertEqual(cross_review["owner_action_queue_blocking_count"], 5)
            self.assertEqual(cross_review["owner_action_queue_automation_safe_count"], 0)

            with (run_dir / "fact_promotion_owner_review_batch.csv").open(encoding="utf-8-sig", newline="") as f:
                owner_review_batch_rows = list(csv.DictReader(f))
            self.assertEqual(len(owner_review_batch_rows), 7)
            batch_by_area = {row["review_area"]: row for row in owner_review_batch_rows}
            self.assertEqual(batch_by_area["screenshot_ocr_coverage"]["source_artifact"], "screenshot_ocr_coverage.csv")
            self.assertEqual(batch_by_area["screenshot_ocr_coverage"]["blocked_count"], "1")
            self.assertEqual(batch_by_area["screenshot_ocr_coverage"]["owner_authorization_required"], "false")
            self.assertEqual(batch_by_area["screenshot_ocr_coverage"]["owner_review_status"], "blocked_review_required")
            self.assertEqual(batch_by_area["ocr_fact_ledger_staging"]["owner_review_status"], "no_candidate_rows")
            self.assertEqual(batch_by_area["chat_value_candidates"]["source_artifact"], "chat_value_candidates.csv")
            self.assertTrue(all(row["financial_fact_promotion_allowed"] == "false" for row in owner_review_batch_rows))
            self.assertTrue(all(row["fund_ledger_write_allowed"] == "false" for row in owner_review_batch_rows))
            self.assertTrue(all(row["management_conclusion_allowed"] == "false" for row in owner_review_batch_rows))
            self.assertEqual(cross_review["fact_promotion_owner_review_batch_count"], 7)
            self.assertEqual(cross_review["fact_promotion_owner_review_batch_authorization_required_count"], 1)
            self.assertEqual(cross_review["fact_promotion_owner_review_batch_blocking_count"], 2)

            with (run_dir / "fact_promotion_execution_dry_run.csv").open(encoding="utf-8-sig", newline="") as f:
                execution_dry_run_rows = list(csv.DictReader(f))
            self.assertEqual(len(execution_dry_run_rows), 7)
            dry_run_by_area = {row["review_area"]: row for row in execution_dry_run_rows}
            self.assertEqual(
                dry_run_by_area["structured_csv_facts"]["dry_run_status"],
                "not_required_no_candidate_facts",
            )
            self.assertEqual(
                dry_run_by_area["screenshot_ocr_coverage"]["dry_run_status"],
                "not_required_no_ready_facts",
            )
            self.assertEqual(
                dry_run_by_area["ocr_fact_ledger_staging"]["dry_run_status"],
                "not_required_no_candidate_facts",
            )
            self.assertTrue(all(row["dry_run_impact_count"] == "0" for row in execution_dry_run_rows))
            self.assertTrue(all(row["fact_promotion_execution_allowed"] == "false" for row in execution_dry_run_rows))
            self.assertTrue(all(row["fund_ledger_write_allowed"] == "false" for row in execution_dry_run_rows))
            self.assertTrue(all(row["financial_fact_promoted"] == "false" for row in execution_dry_run_rows))
            self.assertTrue(all(row["management_conclusion_allowed"] == "false" for row in execution_dry_run_rows))
            self.assertEqual(cross_review["fact_promotion_execution_dry_run_count"], 7)
            self.assertEqual(cross_review["fact_promotion_execution_dry_run_impact_count"], 0)
            self.assertEqual(cross_review["fact_promotion_execution_dry_run_write_allowed_count"], 0)

            with (run_dir / "fact_promotion_execution_plan.csv").open(encoding="utf-8-sig", newline="") as f:
                execution_plan_rows = list(csv.DictReader(f))
            self.assertEqual(len(execution_plan_rows), 7)
            plan_by_area = {row["review_area"]: row for row in execution_plan_rows}
            self.assertEqual(
                plan_by_area["structured_csv_facts"]["execution_plan_status"],
                "not_required_no_execution_plan",
            )
            self.assertEqual(
                plan_by_area["screenshot_ocr_coverage"]["execution_plan_status"],
                "not_required_no_execution_plan",
            )
            self.assertEqual(
                plan_by_area["ocr_fact_ledger_staging"]["execution_plan_status"],
                "not_required_no_execution_plan",
            )
            self.assertTrue(all(row["planned_impact_count"] == "0" for row in execution_plan_rows))
            self.assertTrue(all(row["source_mutation_allowed"] == "false" for row in execution_plan_rows))
            self.assertTrue(all(row["fact_promotion_execution_allowed"] == "false" for row in execution_plan_rows))
            self.assertTrue(all(row["fund_ledger_write_allowed"] == "false" for row in execution_plan_rows))
            self.assertTrue(all(row["financial_fact_promoted"] == "false" for row in execution_plan_rows))
            self.assertTrue(all(row["management_conclusion_allowed"] == "false" for row in execution_plan_rows))
            self.assertEqual(cross_review["fact_promotion_execution_plan_count"], 7)
            self.assertEqual(cross_review["fact_promotion_execution_plan_planned_impact_count"], 0)
            self.assertEqual(cross_review["fact_promotion_execution_plan_write_allowed_count"], 0)

            execution_auth_template = json.loads(
                (run_dir / "fact_promotion_execution_authorization_template.json").read_text(encoding="utf-8")
            )
            self.assertEqual(execution_auth_template["authorization_manifest_version"], "1")
            self.assertEqual(execution_auth_template["run_id"], "indexed_package_test")
            self.assertEqual(
                execution_auth_template["authorization_scope"],
                "controlled_fact_promotion_execution",
            )
            self.assertFalse(execution_auth_template["source_mutation_allowed"])
            self.assertFalse(execution_auth_template["fact_promotion_execution_allowed"])
            self.assertFalse(execution_auth_template["fund_ledger_write_allowed"])
            self.assertFalse(execution_auth_template["financial_fact_promoted"])
            self.assertFalse(execution_auth_template["management_conclusion_allowed"])
            self.assertEqual(
                execution_auth_template["output_authorization_manifest_relative_path"],
                "KMFA/metadata/fund_weekly_analysis/private_runtime/"
                "fact_promotion_execution_authorizations/indexed_package_test.json",
            )
            self.assertEqual(len(execution_auth_template["execution_plan_authorizations"]), 7)
            self.assertTrue(
                all(row["authorized"] is False for row in execution_auth_template["execution_plan_authorizations"])
            )

            with (run_dir / "fact_promotion_execution_authorization_preview.csv").open(
                encoding="utf-8-sig",
                newline="",
            ) as f:
                execution_auth_preview_rows = list(csv.DictReader(f))
            self.assertEqual(len(execution_auth_preview_rows), 7)
            self.assertTrue(all(row["source_mutation_allowed"] == "false" for row in execution_auth_preview_rows))
            self.assertTrue(all(row["fact_promotion_execution_allowed"] == "false" for row in execution_auth_preview_rows))
            self.assertTrue(all(row["fund_ledger_write_allowed"] == "false" for row in execution_auth_preview_rows))
            self.assertTrue(all(row["financial_fact_promoted"] == "false" for row in execution_auth_preview_rows))
            self.assertTrue(all(row["management_conclusion_allowed"] == "false" for row in execution_auth_preview_rows))
            self.assertEqual(cross_review["fact_promotion_execution_authorization_preview_count"], 7)
            self.assertEqual(cross_review["fact_promotion_execution_authorization_preview_ready_count"], 0)
            self.assertEqual(cross_review["fact_promotion_execution_authorization_write_allowed_count"], 0)

            with (run_dir / "fact_promotion_execution_apply_gate.csv").open(
                encoding="utf-8-sig",
                newline="",
            ) as f:
                execution_apply_gate_rows = list(csv.DictReader(f))
            self.assertEqual(len(execution_apply_gate_rows), 7)
            self.assertTrue(all(row["planned_apply_count"] == "0" for row in execution_apply_gate_rows))
            self.assertTrue(all(row["source_mutation_allowed"] == "false" for row in execution_apply_gate_rows))
            self.assertTrue(all(row["fact_promotion_execution_allowed"] == "false" for row in execution_apply_gate_rows))
            self.assertTrue(all(row["fund_ledger_write_allowed"] == "false" for row in execution_apply_gate_rows))
            self.assertTrue(all(row["financial_fact_promoted"] == "false" for row in execution_apply_gate_rows))
            self.assertTrue(all(row["management_conclusion_allowed"] == "false" for row in execution_apply_gate_rows))
            self.assertEqual(cross_review["fact_promotion_execution_apply_gate_count"], 7)
            self.assertEqual(cross_review["fact_promotion_execution_apply_gate_ready_count"], 0)
            self.assertEqual(cross_review["fact_promotion_execution_apply_gate_planned_apply_count"], 0)
            self.assertEqual(cross_review["fact_promotion_execution_apply_gate_write_allowed_count"], 0)
            self.assertEqual(cross_review["fact_promotion_execution_result_count"], 7)
            self.assertEqual(cross_review["fact_promotion_execution_result_formalized_area_count"], 0)
            self.assertEqual(cross_review["formal_fund_ledger_row_count"], 0)

            with (run_dir / "fact_promotion_execution_result.csv").open(
                encoding="utf-8-sig",
                newline="",
            ) as f:
                execution_result_rows = list(csv.DictReader(f))
            self.assertEqual(len(execution_result_rows), 7)
            self.assertTrue(all(row["formal_ledger_row_count"] == "0" for row in execution_result_rows))
            self.assertTrue(all(row["source_mutation_allowed"] == "false" for row in execution_result_rows))
            self.assertTrue(all(row["fund_ledger_mutation_allowed"] == "false" for row in execution_result_rows))
            self.assertTrue(all(row["management_conclusion_allowed"] == "false" for row in execution_result_rows))

            with (run_dir / "formal_fund_ledger.csv").open(encoding="utf-8-sig", newline="") as f:
                formal_rows = list(csv.DictReader(f))
            self.assertEqual(formal_rows, [])

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

    def test_runner_indexes_private_vision_ocr_sidecars_without_copying_to_source(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir) / "repo"
            input_dir = Path(temp_dir) / "OneDrive-Personal" / "DWS_Outputs" / "付款请示群"
            source_day = input_dir / "files" / "0708"
            source_day.mkdir(parents=True)
            screenshot = source_day / "20260708113000_杨婷_资金账户截图.png"
            screenshot.write_bytes(b"real-image-bytes")

            run_id = "private_vision_ocr_reindex_test"
            run_dir = repo_root / "KMFA/metadata/fund_weekly_analysis/private_runtime/runs" / run_id
            run_dir.mkdir(parents=True)
            private_rel = Path(
                "KMFA/metadata/fund_weekly_analysis/private_runtime/ocr_sidecars/"
                "private_vision_ocr_source_run/OCRGEN-private_vision_ocr_source_run-00001.ocr.txt"
            )
            private_sidecar = repo_root / private_rel
            private_sidecar.parent.mkdir(parents=True)
            private_text = "\n".join([
                "日期 2026-07-08 招商银行 基本户",
                "期末余额 12,345.67 可用余额 12,000.00",
            ])
            private_sidecar.write_text(private_text + "\n", encoding="utf-8")
            with (run_dir / "screenshot_ocr_sidecar_generation_plan.csv").open("w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=[
                    "ocr_generation_id",
                    "evidence_id",
                    "source_image_relative_path",
                    "engine",
                    "generation_status",
                    "ocr_text_private_relative_path",
                    "text_length",
                    "text_sha256",
                    "apply_performed",
                    "financial_fact_promoted",
                    "review_status",
                    "reason",
                ])
                writer.writeheader()
                writer.writerow({
                    "ocr_generation_id": "OCRGEN-private_vision_ocr_source_run-00001",
                    "evidence_id": "previous-run-evidence-id",
                    "source_image_relative_path": "files/0708/20260708113000_杨婷_资金账户截图.png",
                    "engine": "vision",
                    "generation_status": "ocr_text_generated_pending_review",
                    "ocr_text_private_relative_path": str(private_rel),
                    "text_length": str(len(private_text)),
                    "text_sha256": hashlib.sha256(private_text.encode("utf-8")).hexdigest(),
                    "apply_performed": "true",
                    "financial_fact_promoted": "false",
                    "review_status": "pending_human_review",
                    "reason": "",
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
            self.assertFalse((source_day / "20260708113000_杨婷_资金账户截图.png.ocr.txt").exists())

            with (run_dir / "screenshot_ocr_coverage.csv").open(encoding="utf-8-sig", newline="") as f:
                coverage_rows = list(csv.DictReader(f))
            self.assertEqual(coverage_rows[0]["ocr_coverage_status"], "ocr_text_sidecar_present_pending_review")
            self.assertEqual(coverage_rows[0]["ocr_text_relative_path"], str(private_rel))
            self.assertEqual(coverage_rows[0]["next_action"], "review_private_ocr_text_candidate")

            with (run_dir / "ocr_text_candidates.csv").open(encoding="utf-8-sig", newline="") as f:
                ocr_rows = list(csv.DictReader(f))
            self.assertEqual(len(ocr_rows), 1)
            self.assertEqual(ocr_rows[0]["ocr_text_relative_path"], str(private_rel))
            self.assertEqual(ocr_rows[0]["ocr_text_sha256"], hashlib.sha256(private_text.encode("utf-8")).hexdigest())
            self.assertEqual(ocr_rows[0]["extraction_status"], "private_ocr_text_sidecar_indexed_pending_review")
            self.assertEqual(ocr_rows[0]["financial_fact_promoted"], "false")
            self.assertIn("期末余额", ocr_rows[0]["text_excerpt"])

            with (run_dir / "ocr_value_candidates.csv").open(encoding="utf-8-sig", newline="") as f:
                value_rows = list(csv.DictReader(f))
            self.assertEqual([row["candidate_type"] for row in value_rows], ["date", "amount", "amount"])
            self.assertTrue(all(row["financial_fact_promoted"] == "false" for row in value_rows))

            with (run_dir / "fund_ledger.csv").open(encoding="utf-8-sig", newline="") as f:
                fund_rows = list(csv.DictReader(f))
            self.assertEqual(fund_rows, [])

            cross_review = json.loads((run_dir / "cross_review.json").read_text(encoding="utf-8"))
            self.assertFalse(cross_review["management_conclusion_allowed"])
            self.assertEqual(cross_review["generated_financial_amount_count"], 0)
            self.assertEqual(cross_review["screenshot_ocr_ready_count"], 1)
            self.assertEqual(cross_review["screenshot_ocr_missing_count"], 0)
            self.assertEqual(cross_review["ocr_text_candidate_count"], 1)
            self.assertEqual(cross_review["ocr_value_candidate_count"], 3)

    def test_runner_builds_pending_ocr_financial_fact_candidates_without_promoting(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir) / "repo"
            input_dir = Path(temp_dir) / "OneDrive-Personal" / "DWS_Outputs" / "付款请示群"
            source_day = input_dir / "files" / "0708"
            source_day.mkdir(parents=True)
            screenshot = source_day / "20260708113000_杨婷_资金账户截图.png"
            screenshot.write_bytes(b"real-image-bytes")

            run_id = "ocr_financial_fact_candidate_test"
            run_dir = repo_root / "KMFA/metadata/fund_weekly_analysis/private_runtime/runs" / run_id
            run_dir.mkdir(parents=True)
            private_rel = Path(
                "KMFA/metadata/fund_weekly_analysis/private_runtime/ocr_sidecars/"
                "ocr_financial_fact_candidate_test/OCRGEN-ocr_financial_fact_candidate_test-00001.ocr.txt"
            )
            private_sidecar = repo_root / private_rel
            private_sidecar.parent.mkdir(parents=True)
            private_text = "\n".join([
                "2026年07月08日 武汉开明 招商银行 银行存款 12,345.67",
                "武汉彤烨 电子汇票 8,000.00",
                "申请支付金额 500.00",
            ])
            private_sidecar.write_text(private_text + "\n", encoding="utf-8")
            with (run_dir / "screenshot_ocr_sidecar_generation_plan.csv").open("w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=[
                    "ocr_generation_id",
                    "evidence_id",
                    "source_image_relative_path",
                    "engine",
                    "generation_status",
                    "ocr_text_private_relative_path",
                    "text_length",
                    "text_sha256",
                    "apply_performed",
                    "financial_fact_promoted",
                    "review_status",
                    "reason",
                ])
                writer.writeheader()
                writer.writerow({
                    "ocr_generation_id": "OCRGEN-ocr_financial_fact_candidate_test-00001",
                    "evidence_id": "previous-run-evidence-id",
                    "source_image_relative_path": "files/0708/20260708113000_杨婷_资金账户截图.png",
                    "engine": "vision",
                    "generation_status": "ocr_text_generated_pending_review",
                    "ocr_text_private_relative_path": str(private_rel),
                    "text_length": str(len(private_text)),
                    "text_sha256": hashlib.sha256(private_text.encode("utf-8")).hexdigest(),
                    "apply_performed": "true",
                    "financial_fact_promoted": "false",
                    "review_status": "pending_human_review",
                    "reason": "",
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
            with (run_dir / "ocr_financial_fact_candidates.csv").open(encoding="utf-8-sig", newline="") as f:
                fact_rows = list(csv.DictReader(f))
            self.assertEqual([row["candidate_metric"] for row in fact_rows], [
                "bank_deposit",
                "electronic_bill",
                "payment_outflow",
            ])
            self.assertEqual([row["amount"] for row in fact_rows], ["12345.67", "8000.00", "500.00"])
            self.assertEqual(fact_rows[0]["business_date"], "2026-07-08")
            self.assertEqual(fact_rows[0]["company"], "武汉开明")
            self.assertEqual(fact_rows[0]["bank"], "招商银行")
            self.assertEqual(fact_rows[1]["company"], "武汉彤烨")
            self.assertTrue(all(row["review_status"] == "pending_human_review" for row in fact_rows))
            self.assertTrue(all(row["financial_fact_promoted"] == "false" for row in fact_rows))

            template = json.loads((run_dir / "ocr_fact_review_authorization_template.json").read_text(encoding="utf-8"))
            self.assertEqual(template["authorization_scope"], "ocr_financial_fact_review_validation_only")
            self.assertEqual(
                template["output_authorization_manifest_relative_path"],
                f"KMFA/metadata/fund_weekly_analysis/private_runtime/ocr_fact_review_authorizations/{run_id}.json",
            )
            self.assertEqual(len(template["fact_candidate_authorizations"]), 3)
            self.assertTrue(all(row["authorized"] is False for row in template["fact_candidate_authorizations"]))

            with (run_dir / "ocr_fact_review_apply_gate.csv").open(encoding="utf-8-sig", newline="") as f:
                gate_rows = list(csv.DictReader(f))
            self.assertEqual(len(gate_rows), 3)
            self.assertTrue(all(row["operator_authorization_required"] == "true" for row in gate_rows))
            self.assertTrue(all(row["operator_authorization_present"] == "false" for row in gate_rows))
            self.assertTrue(all(row["review_gate_status"] == "blocked_missing_operator_authorization" for row in gate_rows))
            self.assertTrue(all(row["staging_allowed"] == "false" for row in gate_rows))
            self.assertTrue(all(row["financial_fact_promoted"] == "false" for row in gate_rows))

            with (run_dir / "ocr_fact_review_authorization_preview.csv").open(encoding="utf-8-sig", newline="") as f:
                preview_rows = list(csv.DictReader(f))
            self.assertEqual(len(preview_rows), 3)
            self.assertTrue(all(row["preview_status"] == "blocked_missing_operator_authorization" for row in preview_rows))
            self.assertTrue(all(row["staging_allowed"] == "false" for row in preview_rows))
            self.assertTrue(all(row["financial_fact_promoted"] == "false" for row in preview_rows))

            with (run_dir / "ocr_fact_cross_review.csv").open(encoding="utf-8-sig", newline="") as f:
                cross_rows = list(csv.DictReader(f))
            self.assertEqual([row["candidate_metric"] for row in cross_rows], [
                "bank_deposit",
                "electronic_bill",
                "payment_outflow",
            ])
            cross_by_metric = {row["candidate_metric"]: row for row in cross_rows}
            self.assertEqual(cross_by_metric["bank_deposit"]["candidate_count"], "1")
            self.assertEqual(cross_by_metric["bank_deposit"]["candidate_amount_total"], "12345.67")
            self.assertEqual(cross_by_metric["bank_deposit"]["company_present_count"], "1")
            self.assertEqual(cross_by_metric["bank_deposit"]["bank_present_count"], "1")
            self.assertEqual(cross_by_metric["electronic_bill"]["candidate_amount_total"], "8000.00")
            self.assertEqual(cross_by_metric["payment_outflow"]["candidate_amount_total"], "500.00")
            self.assertTrue(all(row["operator_authorized_count"] == "0" for row in cross_rows))
            self.assertTrue(all(row["fund_ledger_write_allowed"] == "false" for row in cross_rows))
            self.assertTrue(all(row["financial_fact_promoted"] == "false" for row in cross_rows))
            self.assertTrue(all(row["review_status"] == "pending_human_cross_review" for row in cross_rows))

            with (run_dir / "ocr_fact_owner_review_batch.csv").open(encoding="utf-8-sig", newline="") as f:
                owner_batch_rows = list(csv.DictReader(f))
            self.assertEqual([row["candidate_metric"] for row in owner_batch_rows], [
                "bank_deposit",
                "electronic_bill",
                "payment_outflow",
            ])
            owner_batch_by_metric = {row["candidate_metric"]: row for row in owner_batch_rows}
            self.assertEqual(owner_batch_by_metric["bank_deposit"]["candidate_count"], "1")
            self.assertEqual(owner_batch_by_metric["bank_deposit"]["candidate_amount_total"], "12345.67")
            self.assertEqual(owner_batch_by_metric["bank_deposit"]["priority"], "P0")
            self.assertEqual(owner_batch_by_metric["bank_deposit"]["owner_review_status"], "blocked_metric_review_required")
            self.assertEqual(owner_batch_by_metric["bank_deposit"]["owner_authorization_required"], "true")
            self.assertEqual(
                owner_batch_by_metric["bank_deposit"]["authorization_manifest_relative_path"],
                f"KMFA/metadata/fund_weekly_analysis/private_runtime/ocr_fact_review_authorizations/{run_id}.json",
            )
            self.assertTrue(all(row["fund_ledger_write_allowed"] == "false" for row in owner_batch_rows))
            self.assertTrue(all(row["financial_fact_promoted"] == "false" for row in owner_batch_rows))
            self.assertTrue(all(row["management_conclusion_allowed"] == "false" for row in owner_batch_rows))

            with (run_dir / "ocr_fact_evidence_review_queue.csv").open(encoding="utf-8-sig", newline="") as f:
                evidence_queue_rows = list(csv.DictReader(f))
            self.assertEqual([row["candidate_metric"] for row in evidence_queue_rows], [
                "bank_deposit",
                "electronic_bill",
                "payment_outflow",
            ])
            evidence_queue_by_metric = {row["candidate_metric"]: row for row in evidence_queue_rows}
            self.assertEqual(evidence_queue_by_metric["bank_deposit"]["candidate_count"], "1")
            self.assertEqual(evidence_queue_by_metric["bank_deposit"]["candidate_amount_total"], "12345.67")
            self.assertEqual(evidence_queue_by_metric["bank_deposit"]["authorization_blocked_count"], "1")
            self.assertEqual(evidence_queue_by_metric["bank_deposit"]["priority"], "P0")
            self.assertEqual(
                evidence_queue_by_metric["bank_deposit"]["evidence_review_status"],
                "blocked_evidence_review_required",
            )
            self.assertEqual(
                evidence_queue_by_metric["bank_deposit"]["authorization_manifest_relative_path"],
                f"KMFA/metadata/fund_weekly_analysis/private_runtime/ocr_fact_review_authorizations/{run_id}.json",
            )
            self.assertTrue(all(row["fund_ledger_write_allowed"] == "false" for row in evidence_queue_rows))
            self.assertTrue(all(row["financial_fact_promoted"] == "false" for row in evidence_queue_rows))
            self.assertTrue(all(row["management_conclusion_allowed"] == "false" for row in evidence_queue_rows))

            with (run_dir / "ocr_fact_candidate_owner_worklist.csv").open(encoding="utf-8-sig", newline="") as f:
                owner_worklist_rows = list(csv.DictReader(f))
            self.assertEqual([row["candidate_metric"] for row in owner_worklist_rows], [
                "bank_deposit",
                "electronic_bill",
                "payment_outflow",
            ])
            worklist_by_id = {row["fact_candidate_id"]: row for row in owner_worklist_rows}
            self.assertEqual(
                worklist_by_id[f"OCRFACT-{run_id}-00001"]["ocr_fact_evidence_review_queue_id"],
                evidence_queue_by_metric["bank_deposit"]["ocr_fact_evidence_review_queue_id"],
            )
            self.assertEqual(worklist_by_id[f"OCRFACT-{run_id}-00001"]["owner_authorization_decision"], "pending_owner_review")
            self.assertEqual(worklist_by_id[f"OCRFACT-{run_id}-00001"]["authorization_validation_status"], "missing_authorization_manifest")
            self.assertEqual(worklist_by_id[f"OCRFACT-{run_id}-00001"]["staging_preview_status"], "blocked_missing_operator_authorization")
            self.assertEqual(worklist_by_id[f"OCRFACT-{run_id}-00001"]["owner_corrected_company"], "")
            self.assertEqual(worklist_by_id[f"OCRFACT-{run_id}-00001"]["owner_corrected_bank"], "")
            self.assertEqual(
                worklist_by_id[f"OCRFACT-{run_id}-00001"]["authorization_manifest_relative_path"],
                f"KMFA/metadata/fund_weekly_analysis/private_runtime/ocr_fact_review_authorizations/{run_id}.json",
            )
            self.assertTrue(all(row["authorization_scope"] == "ocr_financial_fact_review_validation_only" for row in owner_worklist_rows))
            self.assertTrue(all(row["fund_ledger_write_allowed"] == "false" for row in owner_worklist_rows))
            self.assertTrue(all(row["financial_fact_promoted"] == "false" for row in owner_worklist_rows))
            self.assertTrue(all(row["management_conclusion_allowed"] == "false" for row in owner_worklist_rows))

            decision_template = json.loads((run_dir / "ocr_fact_candidate_owner_decision_template.json").read_text(encoding="utf-8"))
            self.assertEqual(decision_template["decision_scope"], "ocr_fact_candidate_owner_worklist_validation_only")
            self.assertEqual(
                decision_template["output_decision_manifest_relative_path"],
                f"KMFA/metadata/fund_weekly_analysis/private_runtime/ocr_fact_candidate_owner_decisions/{run_id}.json",
            )
            self.assertEqual(len(decision_template["owner_decisions"]), 3)
            self.assertTrue(
                all(row["owner_authorization_decision"] == "pending_owner_review" for row in decision_template["owner_decisions"])
            )
            self.assertFalse(decision_template["financial_fact_promotion_allowed"])
            self.assertFalse(decision_template["fund_ledger_write_allowed"])
            self.assertFalse(decision_template["management_conclusion_allowed"])

            with (run_dir / "ocr_fact_candidate_owner_decision_preview.csv").open(encoding="utf-8-sig", newline="") as f:
                decision_preview_rows = list(csv.DictReader(f))
            self.assertEqual(len(decision_preview_rows), 3)
            self.assertTrue(all(row["decision_validation_status"] == "missing_decision_manifest" for row in decision_preview_rows))
            self.assertTrue(all(row["decision_preview_status"] == "blocked_missing_owner_decision_manifest" for row in decision_preview_rows))
            self.assertTrue(all(row["fund_ledger_write_allowed"] == "false" for row in decision_preview_rows))
            self.assertTrue(all(row["financial_fact_promoted"] == "false" for row in decision_preview_rows))
            self.assertTrue(all(row["management_conclusion_allowed"] == "false" for row in decision_preview_rows))

            with (run_dir / "ocr_fact_candidate_owner_decision_progress_summary.csv").open(
                encoding="utf-8-sig",
                newline="",
            ) as f:
                decision_progress_rows = list(csv.DictReader(f))
            self.assertEqual(len(decision_progress_rows), 4)
            progress_by_scope = {
                (row["summary_level"], row["candidate_metric"]): row
                for row in decision_progress_rows
            }
            all_progress = progress_by_scope[("all_candidates", "ALL")]
            self.assertEqual(all_progress["candidate_count"], "3")
            self.assertEqual(all_progress["ready_count"], "0")
            self.assertEqual(all_progress["blocking_count"], "3")
            self.assertEqual(all_progress["missing_owner_decision_manifest_count"], "3")
            self.assertEqual(all_progress["pending_owner_review_count"], "3")
            self.assertEqual(all_progress["approved_for_authorization_count"], "0")
            self.assertEqual(all_progress["needs_correction_count"], "0")
            self.assertEqual(all_progress["rejected_count"], "0")
            self.assertEqual(all_progress["missing_company_count"], "3")
            self.assertEqual(all_progress["missing_bank_count"], "3")
            self.assertEqual(all_progress["authorization_update_ready_count"], "0")
            self.assertEqual(all_progress["fund_ledger_write_allowed"], "false")
            self.assertEqual(all_progress["financial_fact_promoted"], "false")
            self.assertEqual(all_progress["management_conclusion_allowed"], "false")
            self.assertIn("owner decision manifest", all_progress["recommended_next_step"])
            self.assertEqual(progress_by_scope[("candidate_metric", "bank_deposit")]["candidate_count"], "1")
            self.assertEqual(progress_by_scope[("candidate_metric", "electronic_bill")]["candidate_count"], "1")
            self.assertEqual(progress_by_scope[("candidate_metric", "payment_outflow")]["candidate_count"], "1")

            authorization_update_draft = json.loads(
                (run_dir / "ocr_fact_candidate_owner_authorization_update_draft.json").read_text(encoding="utf-8")
            )
            self.assertEqual(authorization_update_draft["authorization_scope"], "ocr_financial_fact_review_validation_only")
            self.assertEqual(
                authorization_update_draft["output_authorization_manifest_relative_path"],
                f"KMFA/metadata/fund_weekly_analysis/private_runtime/ocr_fact_review_authorizations/{run_id}.json",
            )
            self.assertEqual(authorization_update_draft["generated_from"], "ocr_fact_candidate_owner_decision_preview.csv")
            self.assertEqual(authorization_update_draft["fact_candidate_authorizations"], [])
            self.assertFalse(authorization_update_draft["financial_fact_promotion_allowed"])
            self.assertFalse(authorization_update_draft["fund_ledger_write_allowed"])
            self.assertFalse(authorization_update_draft["management_conclusion_allowed"])

            with (run_dir / "ocr_fact_candidate_owner_authorization_update_preview.csv").open(encoding="utf-8-sig", newline="") as f:
                authorization_update_preview_rows = list(csv.DictReader(f))
            self.assertEqual(len(authorization_update_preview_rows), 3)
            self.assertTrue(
                all(row["authorization_update_preview_status"] == "blocked_owner_decision_not_approved" for row in authorization_update_preview_rows)
            )
            self.assertTrue(all(row["authorization_update_allowed"] == "false" for row in authorization_update_preview_rows))
            self.assertTrue(all(row["fund_ledger_write_allowed"] == "false" for row in authorization_update_preview_rows))
            self.assertTrue(all(row["financial_fact_promoted"] == "false" for row in authorization_update_preview_rows))
            self.assertTrue(all(row["management_conclusion_allowed"] == "false" for row in authorization_update_preview_rows))

            with (run_dir / "ocr_fact_controlled_ledger_row_preview.csv").open(encoding="utf-8-sig", newline="") as f:
                controlled_ledger_rows = list(csv.DictReader(f))
            self.assertEqual(controlled_ledger_rows, [])

            with (run_dir / "ocr_fact_controlled_ledger_apply_gate.csv").open(encoding="utf-8-sig", newline="") as f:
                controlled_apply_gate_rows = list(csv.DictReader(f))
            self.assertEqual(controlled_apply_gate_rows, [])

            with (run_dir / "ocr_fact_owner_decision_correction_queue.csv").open(encoding="utf-8-sig", newline="") as f:
                correction_queue_rows = list(csv.DictReader(f))
            self.assertEqual(correction_queue_rows, [])

            with (run_dir / "ocr_fact_owner_decision_correction_evidence_packet.csv").open(encoding="utf-8-sig", newline="") as f:
                correction_evidence_packet_rows = list(csv.DictReader(f))
            self.assertEqual(correction_evidence_packet_rows, [])

            with (run_dir / "ocr_fact_owner_decision_correction_ocr_line_context.csv").open(encoding="utf-8-sig", newline="") as f:
                correction_ocr_line_context_rows = list(csv.DictReader(f))
            self.assertEqual(correction_ocr_line_context_rows, [])

            with (run_dir / "ocr_fact_owner_decision_correction_chat_context.csv").open(encoding="utf-8-sig", newline="") as f:
                correction_chat_context_rows = list(csv.DictReader(f))
            self.assertEqual(correction_chat_context_rows, [])

            with (run_dir / "ocr_fact_owner_decision_correction_chat_neighbor_context.csv").open(encoding="utf-8-sig", newline="") as f:
                correction_chat_neighbor_context_rows = list(csv.DictReader(f))
            self.assertEqual(correction_chat_neighbor_context_rows, [])

            with (run_dir / "ocr_fact_owner_decision_correction_owner_review_packet.csv").open(encoding="utf-8-sig", newline="") as f:
                correction_owner_review_packet_rows = list(csv.DictReader(f))
            self.assertEqual(correction_owner_review_packet_rows, [])

            with (run_dir / "ocr_fact_owner_decision_correction_manifest_readiness.csv").open(encoding="utf-8-sig", newline="") as f:
                correction_manifest_readiness_rows = list(csv.DictReader(f))
            self.assertEqual(correction_manifest_readiness_rows, [])

            correction_draft = json.loads(
                (run_dir / "ocr_fact_owner_decision_correction_draft.json").read_text(encoding="utf-8")
            )
            self.assertEqual(correction_draft["owner_decisions"], [])
            self.assertFalse(correction_draft["financial_fact_promotion_allowed"])
            self.assertFalse(correction_draft["fund_ledger_write_allowed"])
            self.assertFalse(correction_draft["management_conclusion_allowed"])

            with (run_dir / "ocr_fact_owner_decision_correction_apply_preview.csv").open(encoding="utf-8-sig", newline="") as f:
                correction_apply_preview_rows = list(csv.DictReader(f))
            self.assertEqual(correction_apply_preview_rows, [])

            with (run_dir / "fund_ledger.csv").open(encoding="utf-8-sig", newline="") as f:
                fund_rows = list(csv.DictReader(f))
            self.assertEqual(fund_rows, [])

            with (run_dir / "exception_tasks.csv").open(encoding="utf-8-sig", newline="") as f:
                task_rows = list(csv.DictReader(f))
            self.assertTrue(any(row["task_type"] == "OCR_FACT_CANDIDATE_PENDING_REVIEW" for row in task_rows))

            cross_review = json.loads((run_dir / "cross_review.json").read_text(encoding="utf-8"))
            self.assertEqual(cross_review["ocr_financial_fact_candidate_count"], 3)
            self.assertEqual(cross_review["ocr_fact_cross_review_group_count"], 3)
            self.assertEqual(cross_review["ocr_fact_owner_review_batch_count"], 3)
            self.assertEqual(cross_review["ocr_fact_owner_review_batch_blocking_count"], 3)
            self.assertEqual(cross_review["ocr_fact_evidence_review_queue_count"], 3)
            self.assertEqual(cross_review["ocr_fact_evidence_review_queue_blocking_count"], 3)
            self.assertEqual(cross_review["ocr_fact_candidate_owner_worklist_count"], 3)
            self.assertEqual(cross_review["ocr_fact_candidate_owner_worklist_ready_count"], 0)
            self.assertEqual(cross_review["ocr_fact_candidate_owner_worklist_blocking_count"], 3)
            self.assertEqual(cross_review["ocr_fact_candidate_owner_decision_template_count"], 3)
            self.assertEqual(cross_review["ocr_fact_candidate_owner_decision_preview_count"], 3)
            self.assertEqual(cross_review["ocr_fact_candidate_owner_decision_preview_ready_count"], 0)
            self.assertEqual(cross_review["ocr_fact_candidate_owner_decision_preview_blocking_count"], 3)
            self.assertEqual(cross_review["ocr_fact_candidate_owner_decision_progress_summary_count"], 4)
            self.assertEqual(cross_review["ocr_fact_candidate_owner_decision_progress_summary_candidate_count"], 3)
            self.assertEqual(cross_review["ocr_fact_candidate_owner_decision_progress_summary_ready_count"], 0)
            self.assertEqual(cross_review["ocr_fact_candidate_owner_decision_progress_summary_blocking_count"], 3)
            self.assertEqual(cross_review["ocr_fact_candidate_owner_decision_progress_summary_missing_manifest_count"], 3)
            self.assertEqual(cross_review["ocr_fact_candidate_owner_authorization_update_draft_count"], 0)
            self.assertEqual(cross_review["ocr_fact_candidate_owner_authorization_update_preview_count"], 3)
            self.assertEqual(cross_review["ocr_fact_candidate_owner_authorization_update_preview_ready_count"], 0)
            self.assertEqual(cross_review["ocr_fact_candidate_owner_authorization_update_preview_blocking_count"], 3)
            self.assertEqual(cross_review["ocr_fact_controlled_ledger_row_preview_count"], 0)
            self.assertEqual(cross_review["ocr_fact_controlled_ledger_row_preview_ready_count"], 0)
            self.assertEqual(cross_review["ocr_fact_controlled_ledger_row_preview_blocking_count"], 0)
            self.assertEqual(cross_review["ocr_fact_controlled_ledger_apply_gate_count"], 0)
            self.assertEqual(cross_review["ocr_fact_controlled_ledger_apply_gate_ready_count"], 0)
            self.assertEqual(cross_review["ocr_fact_controlled_ledger_apply_gate_blocking_count"], 0)
            self.assertEqual(cross_review["ocr_fact_controlled_ledger_apply_gate_planned_apply_count"], 0)
            self.assertEqual(cross_review["ocr_fact_controlled_ledger_apply_gate_write_allowed_count"], 0)
            self.assertEqual(cross_review["ocr_fact_owner_decision_correction_queue_count"], 0)
            self.assertEqual(cross_review["ocr_fact_owner_decision_correction_queue_blocking_count"], 0)
            self.assertEqual(cross_review["ocr_fact_owner_decision_correction_queue_write_allowed_count"], 0)
            self.assertEqual(cross_review["ocr_fact_owner_decision_correction_draft_count"], 0)
            self.assertEqual(cross_review["ocr_fact_owner_decision_correction_draft_write_allowed_count"], 0)
            self.assertEqual(cross_review["ocr_fact_owner_decision_correction_apply_preview_count"], 0)
            self.assertEqual(cross_review["ocr_fact_owner_decision_correction_apply_preview_ready_count"], 0)
            self.assertEqual(cross_review["ocr_fact_owner_decision_correction_apply_preview_blocking_count"], 0)
            self.assertEqual(cross_review["ocr_fact_owner_decision_correction_apply_preview_write_allowed_count"], 0)
            self.assertEqual(cross_review["ocr_fact_review_apply_gate_count"], 3)
            self.assertEqual(cross_review["ocr_fact_review_authorization_present_count"], 0)
            self.assertEqual(cross_review["ocr_fact_review_authorization_template_count"], 3)
            self.assertEqual(cross_review["ocr_fact_review_authorization_preview_blocked_count"], 3)
            self.assertEqual(cross_review["generated_financial_amount_count"], 0)
            self.assertFalse(cross_review["management_conclusion_allowed"])

            with (run_dir / "fact_promotion_review_packet.csv").open(encoding="utf-8-sig", newline="") as f:
                review_packet_rows = list(csv.DictReader(f))
            packet_by_area = {row["review_area"]: row for row in review_packet_rows}
            self.assertEqual(packet_by_area["ocr_fact_ledger_staging"]["candidate_count"], "3")
            self.assertEqual(packet_by_area["ocr_fact_ledger_staging"]["ready_count"], "0")
            self.assertEqual(packet_by_area["ocr_fact_ledger_staging"]["blocked_count"], "3")
            self.assertEqual(packet_by_area["ocr_fact_ledger_staging"]["review_status"], "blocked_missing_operator_authorization")
            self.assertEqual(packet_by_area["ocr_fact_ledger_staging"]["fund_ledger_write_allowed"], "false")
            self.assertEqual(packet_by_area["ocr_fact_ledger_staging"]["financial_fact_promoted"], "false")
            self.assertEqual(packet_by_area["screenshot_ocr_coverage"]["candidate_count"], "1")
            self.assertEqual(packet_by_area["screenshot_ocr_coverage"]["ready_count"], "1")
            self.assertEqual(packet_by_area["screenshot_ocr_coverage"]["blocked_count"], "0")
            self.assertEqual(packet_by_area["screenshot_ocr_coverage"]["review_status"], "pass")
            self.assertEqual(packet_by_area["screenshot_ocr_coverage"]["authorization_required"], "false")

            template = json.loads((run_dir / "fact_promotion_authorization_template.json").read_text(encoding="utf-8"))
            self.assertEqual(template["authorization_manifest_version"], "1")
            self.assertEqual(template["run_id"], run_id)
            self.assertEqual(template["authorization_scope"], "fact_promotion_review_packet_validation_only")
            self.assertFalse(template["financial_fact_promotion_allowed"])
            self.assertFalse(template["fund_ledger_write_allowed"])
            self.assertFalse(template["management_conclusion_allowed"])
            self.assertEqual(
                template["output_authorization_manifest_relative_path"],
                f"KMFA/metadata/fund_weekly_analysis/private_runtime/fact_promotion_authorizations/{run_id}.json",
            )
            self.assertEqual(len(template["review_packet_authorizations"]), 7)
            auth_by_area = {row["review_area"]: row for row in template["review_packet_authorizations"]}
            self.assertEqual(auth_by_area["screenshot_ocr_coverage"]["authorization_required"], "false")
            self.assertEqual(auth_by_area["ocr_fact_ledger_staging"]["candidate_count"], "3")
            self.assertEqual(auth_by_area["ocr_fact_ledger_staging"]["blocked_count"], "3")
            self.assertFalse(auth_by_area["ocr_fact_ledger_staging"]["authorized"])
            self.assertEqual(auth_by_area["ocr_fact_ledger_staging"]["authorization_note"], "")

            with (run_dir / "fact_promotion_authorization_preview.csv").open(encoding="utf-8-sig", newline="") as f:
                fact_promotion_preview_rows = list(csv.DictReader(f))
            self.assertEqual(len(fact_promotion_preview_rows), 7)
            promotion_preview_by_area = {row["review_area"]: row for row in fact_promotion_preview_rows}
            self.assertEqual(
                promotion_preview_by_area["structured_csv_facts"]["preview_status"],
                "authorization_not_required_no_candidate_facts",
            )
            self.assertEqual(
                promotion_preview_by_area["ocr_fact_ledger_staging"]["preview_status"],
                "blocked_missing_operator_authorization",
            )
            self.assertEqual(
                promotion_preview_by_area["screenshot_ocr_coverage"]["preview_status"],
                "authorization_not_required_review_area_ready",
            )
            self.assertEqual(
                promotion_preview_by_area["workbook_quality"]["preview_status"],
                "authorization_not_required_review_area_ready",
            )
            self.assertEqual(
                promotion_preview_by_area["ocr_fact_ledger_staging"]["authorization_validation_status"],
                "missing_authorization_manifest",
            )
            self.assertEqual(promotion_preview_by_area["ocr_fact_ledger_staging"]["operator_authorization_present"], "false")
            self.assertTrue(all(row["financial_fact_promotion_allowed"] == "false" for row in fact_promotion_preview_rows))
            self.assertTrue(all(row["fund_ledger_write_allowed"] == "false" for row in fact_promotion_preview_rows))
            self.assertTrue(all(row["financial_fact_promoted"] == "false" for row in fact_promotion_preview_rows))
            self.assertTrue(all(row["management_conclusion_allowed"] == "false" for row in fact_promotion_preview_rows))
            self.assertEqual(cross_review["fact_promotion_authorization_present_count"], 0)
            self.assertEqual(cross_review["fact_promotion_authorization_valid_count"], 0)
            self.assertEqual(cross_review["fact_promotion_authorization_preview_count"], 7)
            self.assertEqual(cross_review["fact_promotion_authorization_preview_ready_count"], 0)
            self.assertEqual(cross_review["fact_promotion_authorization_preview_blocked_count"], 2)

            with (run_dir / "fact_promotion_execution_gate.csv").open(encoding="utf-8-sig", newline="") as f:
                execution_gate_rows = list(csv.DictReader(f))
            self.assertEqual(len(execution_gate_rows), 7)
            execution_gate_by_area = {row["review_area"]: row for row in execution_gate_rows}
            self.assertEqual(
                execution_gate_by_area["ocr_fact_ledger_staging"]["execution_gate_status"],
                "blocked_missing_operator_authorization",
            )
            self.assertEqual(
                execution_gate_by_area["structured_csv_facts"]["execution_gate_status"],
                "not_required_no_candidate_facts",
            )
            self.assertEqual(
                execution_gate_by_area["workbook_quality"]["execution_gate_status"],
                "not_required_review_area_ready",
            )
            self.assertEqual(
                execution_gate_by_area["screenshot_ocr_coverage"]["execution_gate_status"],
                "not_required_review_area_ready",
            )
            self.assertEqual(
                execution_gate_by_area["ocr_fact_ledger_staging"]["authorization_validation_status"],
                "missing_authorization_manifest",
            )
            self.assertTrue(all(row["fact_promotion_execution_allowed"] == "false" for row in execution_gate_rows))
            self.assertTrue(all(row["fund_ledger_write_allowed"] == "false" for row in execution_gate_rows))
            self.assertTrue(all(row["financial_fact_promoted"] == "false" for row in execution_gate_rows))
            self.assertTrue(all(row["management_conclusion_allowed"] == "false" for row in execution_gate_rows))
            self.assertEqual(cross_review["fact_promotion_execution_gate_count"], 7)
            self.assertEqual(cross_review["fact_promotion_execution_gate_ready_count"], 0)
            self.assertEqual(cross_review["fact_promotion_execution_gate_blocked_count"], 2)
            self.assertEqual(cross_review["fact_promotion_execution_allowed_count"], 0)

    def test_runner_validates_private_fact_promotion_authorization_without_promoting_facts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir) / "repo"
            input_dir = Path(temp_dir) / "OneDrive-Personal" / "DWS_Outputs" / "付款请示群"
            source_day = input_dir / "files" / "0708"
            auth_dir = repo_root / "KMFA/metadata/fund_weekly_analysis/private_runtime/fact_promotion_authorizations"
            execution_auth_dir = (
                repo_root
                / "KMFA/metadata/fund_weekly_analysis/private_runtime/fact_promotion_execution_authorizations"
            )
            source_day.mkdir(parents=True)
            auth_dir.mkdir(parents=True)
            execution_auth_dir.mkdir(parents=True)
            screenshot = source_day / "20260708113000_杨婷_资金账户截图.png"
            screenshot.write_bytes(b"real-image-bytes")

            run_id = "fact_promotion_authorization_test"
            run_dir = repo_root / "KMFA/metadata/fund_weekly_analysis/private_runtime/runs" / run_id
            run_dir.mkdir(parents=True)
            private_rel = Path(
                "KMFA/metadata/fund_weekly_analysis/private_runtime/ocr_sidecars/"
                "fact_promotion_authorization_test/OCRGEN-fact_promotion_authorization_test-00001.ocr.txt"
            )
            private_sidecar = repo_root / private_rel
            private_sidecar.parent.mkdir(parents=True)
            private_text = "\n".join([
                "2026年07月08日 武汉开明 招商银行 银行存款 12,345.67",
                "武汉彤烨 电子汇票 8,000.00",
                "申请支付金额 500.00",
            ])
            private_sidecar.write_text(private_text + "\n", encoding="utf-8")
            with (run_dir / "screenshot_ocr_sidecar_generation_plan.csv").open("w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=[
                    "ocr_generation_id",
                    "evidence_id",
                    "source_image_relative_path",
                    "engine",
                    "generation_status",
                    "ocr_text_private_relative_path",
                    "text_length",
                    "text_sha256",
                    "apply_performed",
                    "financial_fact_promoted",
                    "review_status",
                    "reason",
                ])
                writer.writeheader()
                writer.writerow({
                    "ocr_generation_id": "OCRGEN-fact_promotion_authorization_test-00001",
                    "evidence_id": "previous-run-evidence-id",
                    "source_image_relative_path": "files/0708/20260708113000_杨婷_资金账户截图.png",
                    "engine": "vision",
                    "generation_status": "ocr_text_generated_pending_review",
                    "ocr_text_private_relative_path": str(private_rel),
                    "text_length": str(len(private_text)),
                    "text_sha256": hashlib.sha256(private_text.encode("utf-8")).hexdigest(),
                    "apply_performed": "true",
                    "financial_fact_promoted": "false",
                    "review_status": "pending_human_review",
                    "reason": "",
                })

            authorization_manifest = {
                "authorization_manifest_version": "1",
                "run_id": run_id,
                "authorization_scope": "fact_promotion_review_packet_validation_only",
                "authorized_by": "operator-fixture",
                "authorized_at": "2026-07-08T11:40:00+10:00",
                "authorization_ticket": "S51-TEST",
                "financial_fact_promotion_allowed": False,
                "fund_ledger_write_allowed": False,
                "management_conclusion_allowed": False,
                "review_packet_authorizations": [
                    {
                        "review_packet_id": f"FPRP-{run_id}-00002",
                        "review_area": "ocr_fact_ledger_staging",
                        "authorized": True,
                    },
                    {
                        "review_packet_id": f"FPRP-{run_id}-00005",
                        "review_area": "workbook_quality",
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
            with (run_dir / "fact_promotion_authorization_preview.csv").open(encoding="utf-8-sig", newline="") as f:
                preview_rows = list(csv.DictReader(f))
            self.assertEqual(len(preview_rows), 7)
            preview_by_area = {row["review_area"]: row for row in preview_rows}
            self.assertEqual(
                preview_by_area["ocr_fact_ledger_staging"]["authorization_validation_status"],
                "valid_manifest_validation_only",
            )
            self.assertEqual(
                preview_by_area["ocr_fact_ledger_staging"]["preview_status"],
                "ready_for_owner_review_no_fact_promotion",
            )
            self.assertEqual(preview_by_area["ocr_fact_ledger_staging"]["operator_authorization_present"], "true")
            self.assertEqual(
                preview_by_area["workbook_quality"]["preview_status"],
                "authorization_not_required_review_area_ready",
            )
            self.assertEqual(
                preview_by_area["chat_value_candidates"]["preview_status"],
                "authorization_not_required_no_candidate_facts",
            )
            self.assertTrue(all(row["financial_fact_promotion_allowed"] == "false" for row in preview_rows))
            self.assertTrue(all(row["fund_ledger_write_allowed"] == "false" for row in preview_rows))
            self.assertTrue(all(row["financial_fact_promoted"] == "false" for row in preview_rows))
            self.assertTrue(all(row["management_conclusion_allowed"] == "false" for row in preview_rows))

            with (run_dir / "fund_ledger.csv").open(encoding="utf-8-sig", newline="") as f:
                fund_rows = list(csv.DictReader(f))
            self.assertEqual(fund_rows, [])

            cross_review = json.loads((run_dir / "cross_review.json").read_text(encoding="utf-8"))
            self.assertEqual(cross_review["fact_promotion_authorization_present_count"], 1)
            self.assertEqual(cross_review["fact_promotion_authorization_valid_count"], 1)
            self.assertEqual(cross_review["fact_promotion_authorization_preview_count"], 7)
            self.assertEqual(cross_review["fact_promotion_authorization_preview_ready_count"], 1)
            self.assertEqual(cross_review["fact_promotion_authorization_preview_blocked_count"], 1)
            self.assertEqual(cross_review["generated_financial_amount_count"], 0)
            self.assertFalse(cross_review["management_conclusion_allowed"])

            with (run_dir / "fact_promotion_execution_gate.csv").open(encoding="utf-8-sig", newline="") as f:
                execution_rows = list(csv.DictReader(f))
            execution_by_area = {row["review_area"]: row for row in execution_rows}
            self.assertEqual(
                execution_by_area["ocr_fact_ledger_staging"]["authorization_validation_status"],
                "valid_manifest_validation_only",
            )
            self.assertEqual(
                execution_by_area["ocr_fact_ledger_staging"]["execution_gate_status"],
                "blocked_unresolved_review_area",
            )
            self.assertEqual(
                execution_by_area["workbook_quality"]["execution_gate_status"],
                "not_required_review_area_ready",
            )
            self.assertTrue(all(row["fact_promotion_execution_allowed"] == "false" for row in execution_rows))
            self.assertTrue(all(row["fund_ledger_write_allowed"] == "false" for row in execution_rows))
            self.assertTrue(all(row["financial_fact_promoted"] == "false" for row in execution_rows))
            self.assertTrue(all(row["management_conclusion_allowed"] == "false" for row in execution_rows))
            self.assertEqual(cross_review["fact_promotion_execution_gate_count"], 7)
            self.assertEqual(cross_review["fact_promotion_execution_gate_ready_count"], 0)
            self.assertEqual(cross_review["fact_promotion_execution_gate_blocked_count"], 2)
            self.assertEqual(cross_review["fact_promotion_execution_allowed_count"], 0)

    def test_runner_validates_private_ocr_fact_review_authorization_without_ledger_promotion(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir) / "repo"
            input_dir = Path(temp_dir) / "OneDrive-Personal" / "DWS_Outputs" / "付款请示群"
            source_day = input_dir / "files" / "0708"
            auth_dir = repo_root / "KMFA/metadata/fund_weekly_analysis/private_runtime/ocr_fact_review_authorizations"
            decision_dir = repo_root / "KMFA/metadata/fund_weekly_analysis/private_runtime/ocr_fact_candidate_owner_decisions"
            source_day.mkdir(parents=True)
            auth_dir.mkdir(parents=True)
            decision_dir.mkdir(parents=True)
            screenshot = source_day / "20260708113000_杨婷_资金账户截图.png"
            screenshot.write_bytes(b"real-image-bytes")

            run_id = "ocr_fact_review_authorization_test"
            run_dir = repo_root / "KMFA/metadata/fund_weekly_analysis/private_runtime/runs" / run_id
            run_dir.mkdir(parents=True)
            private_rel = Path(
                "KMFA/metadata/fund_weekly_analysis/private_runtime/ocr_sidecars/"
                "ocr_fact_review_authorization_test/OCRGEN-ocr_fact_review_authorization_test-00001.ocr.txt"
            )
            private_sidecar = repo_root / private_rel
            private_sidecar.parent.mkdir(parents=True)
            private_text = "\n".join([
                "2026年07月08日 武汉开明 招商银行 银行存款 12,345.67",
                "武汉彤烨 电子汇票 8,000.00",
                "申请支付金额 500.00",
            ])
            private_sidecar.write_text(private_text + "\n", encoding="utf-8")
            with (run_dir / "screenshot_ocr_sidecar_generation_plan.csv").open("w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=[
                    "ocr_generation_id",
                    "evidence_id",
                    "source_image_relative_path",
                    "engine",
                    "generation_status",
                    "ocr_text_private_relative_path",
                    "text_length",
                    "text_sha256",
                    "apply_performed",
                    "financial_fact_promoted",
                    "review_status",
                    "reason",
                ])
                writer.writeheader()
                writer.writerow({
                    "ocr_generation_id": "OCRGEN-ocr_fact_review_authorization_test-00001",
                    "evidence_id": "previous-run-evidence-id",
                    "source_image_relative_path": "files/0708/20260708113000_杨婷_资金账户截图.png",
                    "engine": "vision",
                    "generation_status": "ocr_text_generated_pending_review",
                    "ocr_text_private_relative_path": str(private_rel),
                    "text_length": str(len(private_text)),
                    "text_sha256": hashlib.sha256(private_text.encode("utf-8")).hexdigest(),
                    "apply_performed": "true",
                    "financial_fact_promoted": "false",
                    "review_status": "pending_human_review",
                    "reason": "",
                })

            authorization_manifest = {
                "authorization_manifest_version": "1",
                "run_id": run_id,
                "authorization_scope": "ocr_financial_fact_review_validation_only",
                "authorized_by": "operator-fixture",
                "authorized_at": "2026-07-08T11:33:00+10:00",
                "authorization_ticket": "S43-TEST",
                "financial_fact_promotion_allowed": False,
                "fund_ledger_write_allowed": False,
                "fact_candidate_authorizations": [
                    {
                        "fact_candidate_id": f"OCRFACT-{run_id}-00001",
                        "candidate_metric": "bank_deposit",
                        "authorized": True,
                    },
                    {
                        "fact_candidate_id": f"OCRFACT-{run_id}-00002",
                        "candidate_metric": "electronic_bill",
                        "authorized": True,
                    },
                ],
            }
            (auth_dir / f"{run_id}.json").write_text(
                json.dumps(authorization_manifest, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            decision_manifest = {
                "decision_manifest_version": "1",
                "run_id": run_id,
                "decision_scope": "ocr_fact_candidate_owner_worklist_validation_only",
                "source_artifact": "ocr_fact_candidate_owner_worklist.csv",
                "financial_fact_promotion_allowed": False,
                "fund_ledger_write_allowed": False,
                "management_conclusion_allowed": False,
                "owner_decisions": [
                    {
                        "fact_candidate_id": f"OCRFACT-{run_id}-00001",
                        "candidate_metric": "bank_deposit",
                        "owner_authorization_decision": "approve_for_review_authorization",
                        "owner_corrected_company": "武汉开明",
                        "owner_corrected_bank": "招商银行",
                        "owner_note": "fixture approval",
                    },
                    {
                        "fact_candidate_id": f"OCRFACT-{run_id}-00002",
                        "candidate_metric": "electronic_bill",
                        "owner_authorization_decision": "approve_for_review_authorization",
                        "owner_corrected_company": "武汉彤烨",
                        "owner_corrected_bank": "汉口银行",
                        "owner_note": "fixture approval",
                    },
                ],
            }
            (decision_dir / f"{run_id}.json").write_text(
                json.dumps(decision_manifest, ensure_ascii=False, indent=2),
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
            with (run_dir / "ocr_fact_review_apply_gate.csv").open(encoding="utf-8-sig", newline="") as f:
                gate_rows = list(csv.DictReader(f))
            gates_by_id = {row["fact_candidate_id"]: row for row in gate_rows}
            self.assertEqual(gates_by_id[f"OCRFACT-{run_id}-00001"]["operator_authorization_present"], "true")
            self.assertEqual(gates_by_id[f"OCRFACT-{run_id}-00001"]["authorization_validation_status"], "valid_manifest_validation_only")
            self.assertEqual(gates_by_id[f"OCRFACT-{run_id}-00001"]["review_gate_status"], "ready_for_review_staging_no_ledger_promotion")
            self.assertEqual(gates_by_id[f"OCRFACT-{run_id}-00002"]["authorization_validation_status"], "valid_manifest_validation_only")
            self.assertEqual(gates_by_id[f"OCRFACT-{run_id}-00003"]["operator_authorization_present"], "false")
            self.assertEqual(gates_by_id[f"OCRFACT-{run_id}-00003"]["authorization_validation_status"], "fact_candidate_not_authorized")
            self.assertTrue(all(row["staging_allowed"] == "false" for row in gate_rows))
            self.assertTrue(all(row["fund_ledger_write_allowed"] == "false" for row in gate_rows))
            self.assertTrue(all(row["financial_fact_promoted"] == "false" for row in gate_rows))

            with (run_dir / "ocr_fact_review_authorization_preview.csv").open(encoding="utf-8-sig", newline="") as f:
                preview_rows = list(csv.DictReader(f))
            previews_by_id = {row["fact_candidate_id"]: row for row in preview_rows}
            self.assertEqual(
                previews_by_id[f"OCRFACT-{run_id}-00001"]["preview_status"],
                "ready_for_operator_review_no_ledger_promotion",
            )
            self.assertEqual(
                previews_by_id[f"OCRFACT-{run_id}-00002"]["preview_status"],
                "ready_for_operator_review_no_ledger_promotion",
            )
            self.assertEqual(
                previews_by_id[f"OCRFACT-{run_id}-00003"]["preview_status"],
                "blocked_fact_candidate_not_authorized",
            )
            self.assertTrue(all(row["staging_allowed"] == "false" for row in preview_rows))
            self.assertTrue(all(row["fund_ledger_write_allowed"] == "false" for row in preview_rows))
            self.assertTrue(all(row["financial_fact_promoted"] == "false" for row in preview_rows))

            with (run_dir / "ocr_fact_ledger_staging_preview.csv").open(encoding="utf-8-sig", newline="") as f:
                staging_rows = list(csv.DictReader(f))
            staging_by_id = {row["fact_candidate_id"]: row for row in staging_rows}
            self.assertEqual(staging_by_id[f"OCRFACT-{run_id}-00001"]["staging_preview_status"], "ready_for_ledger_staging_review_no_write")
            self.assertEqual(staging_by_id[f"OCRFACT-{run_id}-00001"]["proposed_amount_role"], "balance")
            self.assertEqual(staging_by_id[f"OCRFACT-{run_id}-00001"]["proposed_liquidity_tier"], "bank_deposit")
            self.assertEqual(staging_by_id[f"OCRFACT-{run_id}-00002"]["staging_preview_status"], "ready_for_ledger_staging_review_no_write")
            self.assertEqual(staging_by_id[f"OCRFACT-{run_id}-00002"]["proposed_amount_role"], "balance")
            self.assertEqual(staging_by_id[f"OCRFACT-{run_id}-00002"]["proposed_liquidity_tier"], "electronic_bill")
            self.assertEqual(staging_by_id[f"OCRFACT-{run_id}-00003"]["staging_preview_status"], "blocked_fact_candidate_not_authorized")
            self.assertEqual(staging_by_id[f"OCRFACT-{run_id}-00003"]["proposed_amount_role"], "outflow")
            self.assertTrue(all(row["fund_ledger_write_allowed"] == "false" for row in staging_rows))
            self.assertTrue(all(row["financial_fact_promoted"] == "false" for row in staging_rows))
            self.assertTrue(all(row["review_status"] == "pending_human_ledger_staging_review" for row in staging_rows))

            with (run_dir / "ocr_fact_owner_review_batch.csv").open(encoding="utf-8-sig", newline="") as f:
                owner_batch_rows = list(csv.DictReader(f))
            owner_by_metric = {row["candidate_metric"]: row for row in owner_batch_rows}
            self.assertEqual(
                owner_by_metric["bank_deposit"]["owner_review_status"],
                "ready_for_owner_review_no_ledger_promotion",
            )
            self.assertEqual(owner_by_metric["bank_deposit"]["priority"], "P1")
            self.assertEqual(owner_by_metric["bank_deposit"]["operator_authorized_count"], "1")
            self.assertEqual(owner_by_metric["bank_deposit"]["authorization_blocked_count"], "0")
            self.assertEqual(
                owner_by_metric["electronic_bill"]["owner_review_status"],
                "ready_for_owner_review_no_ledger_promotion",
            )
            self.assertEqual(
                owner_by_metric["payment_outflow"]["owner_review_status"],
                "blocked_metric_review_required",
            )
            self.assertTrue(all(row["fund_ledger_write_allowed"] == "false" for row in owner_batch_rows))
            self.assertTrue(all(row["financial_fact_promoted"] == "false" for row in owner_batch_rows))
            self.assertTrue(all(row["management_conclusion_allowed"] == "false" for row in owner_batch_rows))

            with (run_dir / "ocr_fact_evidence_review_queue.csv").open(encoding="utf-8-sig", newline="") as f:
                evidence_queue_rows = list(csv.DictReader(f))
            evidence_queue_by_metric = {row["candidate_metric"]: row for row in evidence_queue_rows}
            self.assertEqual(
                evidence_queue_by_metric["bank_deposit"]["evidence_review_status"],
                "ready_for_owner_evidence_review_no_ledger_promotion",
            )
            self.assertEqual(evidence_queue_by_metric["bank_deposit"]["priority"], "P1")
            self.assertEqual(evidence_queue_by_metric["bank_deposit"]["operator_authorized_count"], "1")
            self.assertEqual(evidence_queue_by_metric["bank_deposit"]["authorization_blocked_count"], "0")
            self.assertEqual(
                evidence_queue_by_metric["electronic_bill"]["evidence_review_status"],
                "ready_for_owner_evidence_review_no_ledger_promotion",
            )
            self.assertEqual(
                evidence_queue_by_metric["payment_outflow"]["evidence_review_status"],
                "blocked_evidence_review_required",
            )
            self.assertTrue(all(row["fund_ledger_write_allowed"] == "false" for row in evidence_queue_rows))
            self.assertTrue(all(row["financial_fact_promoted"] == "false" for row in evidence_queue_rows))
            self.assertTrue(all(row["management_conclusion_allowed"] == "false" for row in evidence_queue_rows))

            with (run_dir / "ocr_fact_candidate_owner_worklist.csv").open(encoding="utf-8-sig", newline="") as f:
                owner_worklist_rows = list(csv.DictReader(f))
            worklist_by_id = {row["fact_candidate_id"]: row for row in owner_worklist_rows}
            self.assertEqual(len(owner_worklist_rows), 3)
            self.assertEqual(
                worklist_by_id[f"OCRFACT-{run_id}-00001"]["ocr_fact_evidence_review_queue_id"],
                evidence_queue_by_metric["bank_deposit"]["ocr_fact_evidence_review_queue_id"],
            )
            self.assertEqual(worklist_by_id[f"OCRFACT-{run_id}-00001"]["authorization_validation_status"], "valid_manifest_validation_only")
            self.assertEqual(worklist_by_id[f"OCRFACT-{run_id}-00001"]["staging_preview_status"], "ready_for_ledger_staging_review_no_write")
            self.assertEqual(worklist_by_id[f"OCRFACT-{run_id}-00001"]["owner_authorization_decision"], "pending_owner_review")
            self.assertEqual(worklist_by_id[f"OCRFACT-{run_id}-00002"]["authorization_validation_status"], "valid_manifest_validation_only")
            self.assertEqual(worklist_by_id[f"OCRFACT-{run_id}-00003"]["authorization_validation_status"], "fact_candidate_not_authorized")
            self.assertEqual(worklist_by_id[f"OCRFACT-{run_id}-00003"]["staging_preview_status"], "blocked_fact_candidate_not_authorized")
            self.assertTrue(all(row["authorization_scope"] == "ocr_financial_fact_review_validation_only" for row in owner_worklist_rows))
            self.assertTrue(all(row["fund_ledger_write_allowed"] == "false" for row in owner_worklist_rows))
            self.assertTrue(all(row["financial_fact_promoted"] == "false" for row in owner_worklist_rows))
            self.assertTrue(all(row["management_conclusion_allowed"] == "false" for row in owner_worklist_rows))

            with (run_dir / "ocr_fact_candidate_owner_decision_preview.csv").open(encoding="utf-8-sig", newline="") as f:
                decision_preview_rows = list(csv.DictReader(f))
            decisions_by_id = {row["fact_candidate_id"]: row for row in decision_preview_rows}
            self.assertEqual(len(decision_preview_rows), 3)
            self.assertEqual(
                decisions_by_id[f"OCRFACT-{run_id}-00001"]["decision_preview_status"],
                "ready_for_private_ocr_fact_authorization_update_no_write",
            )
            self.assertEqual(decisions_by_id[f"OCRFACT-{run_id}-00001"]["decision_validation_status"], "valid_owner_decision_validation_only")
            self.assertEqual(decisions_by_id[f"OCRFACT-{run_id}-00001"]["owner_corrected_company"], "武汉开明")
            self.assertEqual(
                decisions_by_id[f"OCRFACT-{run_id}-00002"]["decision_preview_status"],
                "ready_for_private_ocr_fact_authorization_update_no_write",
            )
            self.assertEqual(
                decisions_by_id[f"OCRFACT-{run_id}-00003"]["decision_preview_status"],
                "blocked_missing_candidate_owner_decision",
            )
            self.assertEqual(decisions_by_id[f"OCRFACT-{run_id}-00003"]["decision_validation_status"], "fact_candidate_owner_decision_missing")
            self.assertTrue(all(row["fund_ledger_write_allowed"] == "false" for row in decision_preview_rows))
            self.assertTrue(all(row["financial_fact_promoted"] == "false" for row in decision_preview_rows))
            self.assertTrue(all(row["management_conclusion_allowed"] == "false" for row in decision_preview_rows))

            authorization_update_draft = json.loads(
                (run_dir / "ocr_fact_candidate_owner_authorization_update_draft.json").read_text(encoding="utf-8")
            )
            self.assertEqual(len(authorization_update_draft["fact_candidate_authorizations"]), 2)
            self.assertEqual(
                [row["fact_candidate_id"] for row in authorization_update_draft["fact_candidate_authorizations"]],
                [f"OCRFACT-{run_id}-00001", f"OCRFACT-{run_id}-00002"],
            )
            self.assertTrue(all(row["authorized"] is True for row in authorization_update_draft["fact_candidate_authorizations"]))
            self.assertFalse(authorization_update_draft["financial_fact_promotion_allowed"])
            self.assertFalse(authorization_update_draft["fund_ledger_write_allowed"])
            self.assertFalse(authorization_update_draft["management_conclusion_allowed"])

            with (run_dir / "ocr_fact_candidate_owner_authorization_update_preview.csv").open(encoding="utf-8-sig", newline="") as f:
                authorization_update_preview_rows = list(csv.DictReader(f))
            update_preview_by_id = {row["fact_candidate_id"]: row for row in authorization_update_preview_rows}
            self.assertEqual(
                update_preview_by_id[f"OCRFACT-{run_id}-00001"]["authorization_update_preview_status"],
                "ready_for_private_ocr_fact_authorization_manifest_update_no_write",
            )
            self.assertEqual(update_preview_by_id[f"OCRFACT-{run_id}-00001"]["authorization_update_allowed"], "false")
            self.assertEqual(
                update_preview_by_id[f"OCRFACT-{run_id}-00003"]["authorization_update_preview_status"],
                "blocked_owner_decision_not_approved",
            )
            self.assertTrue(all(row["fund_ledger_write_allowed"] == "false" for row in authorization_update_preview_rows))
            self.assertTrue(all(row["financial_fact_promoted"] == "false" for row in authorization_update_preview_rows))
            self.assertTrue(all(row["management_conclusion_allowed"] == "false" for row in authorization_update_preview_rows))

            with (run_dir / "ocr_fact_controlled_ledger_row_preview.csv").open(encoding="utf-8-sig", newline="") as f:
                controlled_ledger_rows = list(csv.DictReader(f))
            controlled_by_id = {row["fact_candidate_id"]: row for row in controlled_ledger_rows}
            self.assertEqual(len(controlled_ledger_rows), 2)
            self.assertEqual(
                controlled_by_id[f"OCRFACT-{run_id}-00001"]["ledger_preview_status"],
                "ready_for_controlled_ledger_apply_gate_no_write",
            )
            self.assertEqual(controlled_by_id[f"OCRFACT-{run_id}-00001"]["date"], "2026-07-08")
            self.assertEqual(controlled_by_id[f"OCRFACT-{run_id}-00001"]["company"], "武汉开明")
            self.assertEqual(controlled_by_id[f"OCRFACT-{run_id}-00001"]["bank"], "招商银行")
            self.assertEqual(controlled_by_id[f"OCRFACT-{run_id}-00001"]["liquidity_tier"], "bank_deposit")
            self.assertEqual(controlled_by_id[f"OCRFACT-{run_id}-00001"]["ending_balance"], "12345.67")
            self.assertEqual(controlled_by_id[f"OCRFACT-{run_id}-00001"]["inflow"], "")
            self.assertEqual(controlled_by_id[f"OCRFACT-{run_id}-00001"]["outflow"], "")
            self.assertEqual(
                controlled_by_id[f"OCRFACT-{run_id}-00002"]["ledger_preview_status"],
                "ready_for_controlled_ledger_apply_gate_no_write",
            )
            self.assertEqual(controlled_by_id[f"OCRFACT-{run_id}-00002"]["liquidity_tier"], "electronic_bill")
            self.assertEqual(controlled_by_id[f"OCRFACT-{run_id}-00002"]["company"], "武汉彤烨")
            self.assertEqual(controlled_by_id[f"OCRFACT-{run_id}-00002"]["bank"], "汉口银行")
            self.assertEqual(controlled_by_id[f"OCRFACT-{run_id}-00002"]["ending_balance"], "8000.00")
            self.assertEqual(controlled_by_id[f"OCRFACT-{run_id}-00002"]["inflow"], "")
            self.assertEqual(controlled_by_id[f"OCRFACT-{run_id}-00002"]["outflow"], "")
            self.assertTrue(all(row["fund_ledger_write_allowed"] == "false" for row in controlled_ledger_rows))
            self.assertTrue(all(row["formal_fund_ledger_write_allowed"] == "false" for row in controlled_ledger_rows))
            self.assertTrue(all(row["financial_fact_promoted"] == "false" for row in controlled_ledger_rows))
            self.assertTrue(all(row["management_conclusion_allowed"] == "false" for row in controlled_ledger_rows))

            with (run_dir / "ocr_fact_controlled_ledger_apply_gate.csv").open(encoding="utf-8-sig", newline="") as f:
                controlled_apply_gate_rows = list(csv.DictReader(f))
            controlled_apply_by_id = {row["fact_candidate_id"]: row for row in controlled_apply_gate_rows}
            self.assertEqual(len(controlled_apply_gate_rows), 2)
            self.assertEqual(
                controlled_apply_by_id[f"OCRFACT-{run_id}-00001"]["apply_gate_status"],
                "ready_for_controlled_ledger_apply_no_write",
            )
            self.assertEqual(controlled_apply_by_id[f"OCRFACT-{run_id}-00001"]["planned_apply_count"], "1")
            self.assertEqual(controlled_apply_by_id[f"OCRFACT-{run_id}-00001"]["company"], "武汉开明")
            self.assertEqual(controlled_apply_by_id[f"OCRFACT-{run_id}-00001"]["bank"], "招商银行")
            self.assertEqual(
                controlled_apply_by_id[f"OCRFACT-{run_id}-00002"]["apply_gate_status"],
                "ready_for_controlled_ledger_apply_no_write",
            )
            self.assertEqual(controlled_apply_by_id[f"OCRFACT-{run_id}-00002"]["planned_apply_count"], "1")
            self.assertEqual(controlled_apply_by_id[f"OCRFACT-{run_id}-00002"]["bank"], "汉口银行")
            self.assertTrue(all(row["source_mutation_allowed"] == "false" for row in controlled_apply_gate_rows))
            self.assertTrue(all(row["fund_ledger_write_allowed"] == "false" for row in controlled_apply_gate_rows))
            self.assertTrue(all(row["formal_fund_ledger_write_allowed"] == "false" for row in controlled_apply_gate_rows))
            self.assertTrue(all(row["financial_fact_promoted"] == "false" for row in controlled_apply_gate_rows))
            self.assertTrue(all(row["management_conclusion_allowed"] == "false" for row in controlled_apply_gate_rows))

            with (run_dir / "ocr_fact_owner_decision_correction_roundtrip_audit.csv").open(encoding="utf-8-sig", newline="") as f:
                roundtrip_rows = list(csv.DictReader(f))
            roundtrip_by_id = {row["fact_candidate_id"]: row for row in roundtrip_rows}
            self.assertEqual(len(roundtrip_rows), 2)
            self.assertEqual(
                roundtrip_by_id[f"OCRFACT-{run_id}-00001"]["correction_roundtrip_status"],
                "owner_correction_resolved_apply_gate_ready_no_write",
            )
            self.assertEqual(roundtrip_by_id[f"OCRFACT-{run_id}-00001"]["owner_correction_applied"], "true")
            self.assertEqual(roundtrip_by_id[f"OCRFACT-{run_id}-00001"]["company_source"], "owner_decision_preview")
            self.assertEqual(roundtrip_by_id[f"OCRFACT-{run_id}-00001"]["bank_source"], "owner_decision_preview")
            self.assertEqual(roundtrip_by_id[f"OCRFACT-{run_id}-00001"]["fund_ledger_write_allowed"], "false")
            self.assertEqual(roundtrip_by_id[f"OCRFACT-{run_id}-00001"]["formal_fund_ledger_write_allowed"], "false")
            self.assertEqual(roundtrip_by_id[f"OCRFACT-{run_id}-00001"]["financial_fact_promoted"], "false")
            self.assertEqual(roundtrip_by_id[f"OCRFACT-{run_id}-00001"]["management_conclusion_allowed"], "false")
            self.assertTrue(
                all(row["correction_roundtrip_status"] == "owner_correction_resolved_apply_gate_ready_no_write" for row in roundtrip_rows)
            )
            self.assertTrue(all(row["owner_decision_manifest_write_allowed"] == "false" for row in roundtrip_rows))
            self.assertTrue(all(row["fund_ledger_write_allowed"] == "false" for row in roundtrip_rows))

            with (run_dir / "ocr_fact_owner_decision_correction_queue.csv").open(encoding="utf-8-sig", newline="") as f:
                correction_queue_rows = list(csv.DictReader(f))
            self.assertEqual(correction_queue_rows, [])

            correction_draft = json.loads(
                (run_dir / "ocr_fact_owner_decision_correction_draft.json").read_text(encoding="utf-8")
            )
            self.assertEqual(correction_draft["owner_decisions"], [])
            self.assertFalse(correction_draft["financial_fact_promotion_allowed"])
            self.assertFalse(correction_draft["fund_ledger_write_allowed"])
            self.assertFalse(correction_draft["management_conclusion_allowed"])

            with (run_dir / "ocr_fact_owner_decision_correction_apply_preview.csv").open(encoding="utf-8-sig", newline="") as f:
                correction_apply_preview_rows = list(csv.DictReader(f))
            self.assertEqual(correction_apply_preview_rows, [])

            with (run_dir / "fund_ledger.csv").open(encoding="utf-8-sig", newline="") as f:
                fund_rows = list(csv.DictReader(f))
            self.assertEqual(fund_rows, [])

            cross_review = json.loads((run_dir / "cross_review.json").read_text(encoding="utf-8"))
            self.assertEqual(cross_review["ocr_fact_review_apply_gate_count"], 3)
            self.assertEqual(cross_review["ocr_fact_review_authorization_present_count"], 2)
            self.assertEqual(cross_review["ocr_fact_review_authorization_valid_count"], 2)
            self.assertEqual(cross_review["ocr_fact_review_authorization_preview_ready_count"], 2)
            self.assertEqual(cross_review["ocr_fact_review_authorization_preview_blocked_count"], 1)
            self.assertEqual(cross_review["ocr_fact_ledger_staging_preview_count"], 3)
            self.assertEqual(cross_review["ocr_fact_ledger_staging_preview_ready_count"], 2)
            self.assertEqual(cross_review["ocr_fact_ledger_staging_preview_blocked_count"], 1)
            self.assertEqual(cross_review["ocr_fact_owner_review_batch_count"], 3)
            self.assertEqual(cross_review["ocr_fact_owner_review_batch_blocking_count"], 1)
            self.assertEqual(cross_review["ocr_fact_evidence_review_queue_count"], 3)
            self.assertEqual(cross_review["ocr_fact_evidence_review_queue_blocking_count"], 1)
            self.assertEqual(cross_review["ocr_fact_candidate_owner_worklist_count"], 3)
            self.assertEqual(cross_review["ocr_fact_candidate_owner_worklist_ready_count"], 2)
            self.assertEqual(cross_review["ocr_fact_candidate_owner_worklist_blocking_count"], 1)
            self.assertEqual(cross_review["ocr_fact_candidate_owner_decision_template_count"], 3)
            self.assertEqual(cross_review["ocr_fact_candidate_owner_decision_preview_count"], 3)
            self.assertEqual(cross_review["ocr_fact_candidate_owner_decision_preview_ready_count"], 2)
            self.assertEqual(cross_review["ocr_fact_candidate_owner_decision_preview_blocking_count"], 1)
            self.assertEqual(cross_review["ocr_fact_candidate_owner_authorization_update_draft_count"], 2)
            self.assertEqual(cross_review["ocr_fact_candidate_owner_authorization_update_preview_count"], 3)
            self.assertEqual(cross_review["ocr_fact_candidate_owner_authorization_update_preview_ready_count"], 2)
            self.assertEqual(cross_review["ocr_fact_candidate_owner_authorization_update_preview_blocking_count"], 1)
            self.assertEqual(cross_review["ocr_fact_controlled_ledger_row_preview_count"], 2)
            self.assertEqual(cross_review["ocr_fact_controlled_ledger_row_preview_ready_count"], 2)
            self.assertEqual(cross_review["ocr_fact_controlled_ledger_row_preview_blocking_count"], 0)
            self.assertEqual(cross_review["ocr_fact_controlled_ledger_apply_gate_count"], 2)
            self.assertEqual(cross_review["ocr_fact_controlled_ledger_apply_gate_ready_count"], 2)
            self.assertEqual(cross_review["ocr_fact_controlled_ledger_apply_gate_blocking_count"], 0)
            self.assertEqual(cross_review["ocr_fact_controlled_ledger_apply_gate_planned_apply_count"], 2)
            self.assertEqual(cross_review["ocr_fact_controlled_ledger_apply_gate_write_allowed_count"], 0)
            self.assertEqual(cross_review["ocr_fact_owner_decision_correction_queue_count"], 0)
            self.assertEqual(cross_review["ocr_fact_owner_decision_correction_queue_blocking_count"], 0)
            self.assertEqual(cross_review["ocr_fact_owner_decision_correction_queue_write_allowed_count"], 0)
            self.assertEqual(cross_review["ocr_fact_owner_decision_correction_draft_count"], 0)
            self.assertEqual(cross_review["ocr_fact_owner_decision_correction_draft_write_allowed_count"], 0)
            self.assertEqual(cross_review["ocr_fact_owner_decision_correction_apply_preview_count"], 0)
            self.assertEqual(cross_review["ocr_fact_owner_decision_correction_apply_preview_ready_count"], 0)
            self.assertEqual(cross_review["ocr_fact_owner_decision_correction_apply_preview_blocking_count"], 0)
            self.assertEqual(cross_review["ocr_fact_owner_decision_correction_apply_preview_write_allowed_count"], 0)
            self.assertEqual(cross_review["ocr_fact_owner_decision_correction_roundtrip_audit_count"], 2)
            self.assertEqual(cross_review["ocr_fact_owner_decision_correction_roundtrip_audit_ready_count"], 2)
            self.assertEqual(cross_review["ocr_fact_owner_decision_correction_roundtrip_audit_blocking_count"], 0)
            self.assertEqual(cross_review["ocr_fact_owner_decision_correction_roundtrip_audit_write_allowed_count"], 0)
            self.assertEqual(cross_review["ocr_fact_owner_decision_correction_evidence_packet_count"], 0)
            self.assertEqual(cross_review["ocr_fact_owner_decision_correction_evidence_packet_ready_count"], 0)
            self.assertEqual(cross_review["ocr_fact_owner_decision_correction_evidence_packet_blocking_count"], 0)
            self.assertEqual(cross_review["ocr_fact_owner_decision_correction_evidence_packet_write_allowed_count"], 0)
            self.assertEqual(cross_review["ocr_fact_owner_decision_correction_ocr_line_context_count"], 0)
            self.assertEqual(cross_review["ocr_fact_owner_decision_correction_ocr_line_context_ready_count"], 0)
            self.assertEqual(cross_review["ocr_fact_owner_decision_correction_ocr_line_context_blocking_count"], 0)
            self.assertEqual(cross_review["ocr_fact_owner_decision_correction_ocr_line_context_write_allowed_count"], 0)
            self.assertEqual(cross_review["ocr_fact_owner_decision_correction_chat_context_count"], 0)
            self.assertEqual(cross_review["ocr_fact_owner_decision_correction_chat_context_ready_count"], 0)
            self.assertEqual(cross_review["ocr_fact_owner_decision_correction_chat_context_blocking_count"], 0)
            self.assertEqual(cross_review["ocr_fact_owner_decision_correction_chat_context_write_allowed_count"], 0)
            self.assertEqual(cross_review["ocr_fact_owner_decision_correction_chat_neighbor_context_count"], 0)
            self.assertEqual(cross_review["ocr_fact_owner_decision_correction_chat_neighbor_context_ready_count"], 0)
            self.assertEqual(cross_review["ocr_fact_owner_decision_correction_chat_neighbor_context_blocking_count"], 0)
            self.assertEqual(cross_review["ocr_fact_owner_decision_correction_chat_neighbor_context_write_allowed_count"], 0)
            self.assertEqual(cross_review["ocr_fact_owner_decision_correction_owner_review_packet_count"], 0)
            self.assertEqual(cross_review["ocr_fact_owner_decision_correction_owner_review_packet_ready_count"], 0)
            self.assertEqual(cross_review["ocr_fact_owner_decision_correction_owner_review_packet_blocking_count"], 0)
            self.assertEqual(cross_review["ocr_fact_owner_decision_correction_owner_review_packet_write_allowed_count"], 0)
            self.assertEqual(cross_review["ocr_fact_owner_decision_correction_manifest_readiness_count"], 0)
            self.assertEqual(cross_review["ocr_fact_owner_decision_correction_manifest_readiness_ready_count"], 0)
            self.assertEqual(cross_review["ocr_fact_owner_decision_correction_manifest_readiness_blocking_count"], 0)
            self.assertEqual(cross_review["ocr_fact_owner_decision_correction_manifest_readiness_write_allowed_count"], 0)
            self.assertEqual(cross_review["generated_financial_amount_count"], 0)
            self.assertFalse(cross_review["management_conclusion_allowed"])

    def test_runner_emits_owner_decision_correction_queue_for_missing_ledger_fields(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir) / "repo"
            input_dir = Path(temp_dir) / "OneDrive-Personal" / "DWS_Outputs" / "付款请示群"
            source_day = input_dir / "files" / "0708"
            auth_dir = repo_root / "KMFA/metadata/fund_weekly_analysis/private_runtime/ocr_fact_review_authorizations"
            decision_dir = repo_root / "KMFA/metadata/fund_weekly_analysis/private_runtime/ocr_fact_candidate_owner_decisions"
            source_day.mkdir(parents=True)
            auth_dir.mkdir(parents=True)
            decision_dir.mkdir(parents=True)
            (source_day / "20260708113000_杨婷_资金账户截图.png").write_bytes(b"real-image-bytes")
            manifest_dir = input_dir / "_manifest"
            chat_dir = input_dir / "chat_records"
            manifest_dir.mkdir(parents=True)
            chat_dir.mkdir(parents=True)
            with (manifest_dir / "manifest.csv").open("w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([
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
                writer.writerow([
                    "付款请示群",
                    "cid-fixture",
                    "msg-fixture-001",
                    "2026-07-08 11:30:00",
                    "杨婷",
                    "sender-fixture",
                    "media",
                    "image",
                    "@fixture-media",
                    "资金账户截图.png",
                    "data/archive/付款请示群/files/2026/07/08/20260708113000_杨婷_资金账户截图.png",
                    "files/0708/20260708113000_杨婷_资金账户截图.png",
                    "",
                    "16",
                    "dws_chat_message_download_media",
                    "downloaded",
                ])
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
                writer.writerows([
                    [
                        "付款请示群",
                        "cid-fixture",
                        "msg-fixture-prev-002",
                        "2026-07-08 11:28:00",
                        "马祥荣",
                        "sender-prev-2",
                        "前序消息：今日资金明细待核对",
                        "",
                        "",
                        "",
                        "0",
                        "",
                    ],
                    [
                        "付款请示群",
                        "cid-fixture",
                        "msg-fixture-prev-001",
                        "2026-07-08 11:29:00",
                        "杨婷",
                        "sender-prev-1",
                        "前序消息：保证金退回待确认收款银行",
                        "",
                        "",
                        "",
                        "0",
                        "",
                    ],
                    [
                        "付款请示群",
                        "cid-fixture",
                        "msg-fixture-001",
                        "2026-07-08 11:30:00",
                        "杨婷",
                        "sender-fixture",
                        "[图片消息](mediaId=@fixture-media) 武汉开明资金账户截图，银行待财务确认",
                        "",
                        "",
                        "",
                        "1",
                        "image",
                    ],
                    [
                        "付款请示群",
                        "cid-fixture",
                        "msg-fixture-next-001",
                        "2026-07-08 11:31:00",
                        "张霖泽",
                        "sender-next-1",
                        "后续消息：请确认收款银行",
                        "",
                        "",
                        "",
                        "0",
                        "",
                    ],
                    [
                        "付款请示群",
                        "cid-fixture",
                        "msg-fixture-next-002",
                        "2026-07-08 11:32:00",
                        "杨婷",
                        "sender-next-2",
                        "后续消息：收到后补银行名称",
                        "",
                        "",
                        "",
                        "0",
                        "",
                    ],
                ])

            run_id = "ocr_owner_correction_queue_test"
            run_dir = repo_root / "KMFA/metadata/fund_weekly_analysis/private_runtime/runs" / run_id
            run_dir.mkdir(parents=True)
            private_rel = Path(
                "KMFA/metadata/fund_weekly_analysis/private_runtime/ocr_sidecars/"
                "ocr_owner_correction_queue_test/OCRGEN-ocr_owner_correction_queue_test-00001.ocr.txt"
            )
            private_sidecar = repo_root / private_rel
            private_sidecar.parent.mkdir(parents=True)
            private_text = "\n".join([
                "户名 武汉开明",
                "开户行 中国银行汉口支行",
                "用途 投标保证金退回",
                "2026年07月08日 武汉开明 银行存款 12,345.67",
                "备注 银行待财务确认",
                "附件 资金账户截图",
                "人工复核",
            ])
            private_sidecar.write_text(private_text + "\n", encoding="utf-8")
            with (run_dir / "screenshot_ocr_sidecar_generation_plan.csv").open("w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=[
                    "ocr_generation_id",
                    "evidence_id",
                    "source_image_relative_path",
                    "engine",
                    "generation_status",
                    "ocr_text_private_relative_path",
                    "text_length",
                    "text_sha256",
                    "apply_performed",
                    "financial_fact_promoted",
                    "review_status",
                    "reason",
                ])
                writer.writeheader()
                writer.writerow({
                    "ocr_generation_id": "OCRGEN-ocr_owner_correction_queue_test-00001",
                    "evidence_id": "previous-run-evidence-id",
                    "source_image_relative_path": "files/0708/20260708113000_杨婷_资金账户截图.png",
                    "engine": "vision",
                    "generation_status": "ocr_text_generated_pending_review",
                    "ocr_text_private_relative_path": str(private_rel),
                    "text_length": str(len(private_text)),
                    "text_sha256": hashlib.sha256(private_text.encode("utf-8")).hexdigest(),
                    "apply_performed": "true",
                    "financial_fact_promoted": "false",
                    "review_status": "pending_human_review",
                    "reason": "",
                })
            (auth_dir / f"{run_id}.json").write_text(
                json.dumps({
                    "authorization_manifest_version": "1",
                    "run_id": run_id,
                    "authorization_scope": "ocr_financial_fact_review_validation_only",
                    "authorized_by": "operator-fixture",
                    "authorized_at": "2026-07-08T11:33:00+10:00",
                    "authorization_ticket": "S86-TEST",
                    "financial_fact_promotion_allowed": False,
                    "fund_ledger_write_allowed": False,
                    "fact_candidate_authorizations": [
                        {
                            "fact_candidate_id": f"OCRFACT-{run_id}-00001",
                            "candidate_metric": "bank_deposit",
                            "authorized": True,
                        },
                    ],
                }, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            (decision_dir / f"{run_id}.json").write_text(
                json.dumps({
                    "decision_manifest_version": "1",
                    "run_id": run_id,
                    "decision_scope": "ocr_fact_candidate_owner_worklist_validation_only",
                    "source_artifact": "ocr_fact_candidate_owner_worklist.csv",
                    "financial_fact_promotion_allowed": False,
                    "fund_ledger_write_allowed": False,
                    "management_conclusion_allowed": False,
                    "owner_decisions": [
                        {
                            "fact_candidate_id": f"OCRFACT-{run_id}-00001",
                            "candidate_metric": "bank_deposit",
                            "owner_authorization_decision": "approve_for_review_authorization",
                            "owner_corrected_company": "武汉开明",
                            "owner_corrected_bank": "",
                            "owner_note": "bank still needs owner correction",
                        },
                    ],
                }, ensure_ascii=False, indent=2),
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

            with (run_dir / "ocr_fact_owner_decision_correction_queue.csv").open(encoding="utf-8-sig", newline="") as f:
                correction_queue_rows = list(csv.DictReader(f))
            self.assertEqual(len(correction_queue_rows), 1)
            row = correction_queue_rows[0]
            self.assertEqual(row["fact_candidate_id"], f"OCRFACT-{run_id}-00001")
            self.assertEqual(row["correction_queue_status"], "blocked_owner_correction_required")
            self.assertIn("bank", row["missing_required_fields"])
            self.assertIn("owner_corrected_bank", row["required_owner_fields"])
            self.assertEqual(row["current_company"], "武汉开明")
            self.assertEqual(row["current_bank"], "")
            self.assertEqual(row["owner_decision_manifest_relative_path"], f"KMFA/metadata/fund_weekly_analysis/private_runtime/ocr_fact_candidate_owner_decisions/{run_id}.json")
            self.assertEqual(row["fund_ledger_write_allowed"], "false")
            self.assertEqual(row["formal_fund_ledger_write_allowed"], "false")
            self.assertEqual(row["financial_fact_promoted"], "false")
            self.assertEqual(row["management_conclusion_allowed"], "false")

            with (run_dir / "ocr_fact_owner_decision_correction_evidence_packet.csv").open(encoding="utf-8-sig", newline="") as f:
                correction_evidence_packet_rows = list(csv.DictReader(f))
            self.assertEqual(len(correction_evidence_packet_rows), 1)
            evidence_packet = correction_evidence_packet_rows[0]
            self.assertEqual(evidence_packet["fact_candidate_id"], f"OCRFACT-{run_id}-00001")
            self.assertEqual(evidence_packet["candidate_metric"], "bank_deposit")
            self.assertEqual(evidence_packet["source_correction_queue_id"], row["correction_queue_id"])
            self.assertTrue(evidence_packet["source_evidence_id"].startswith("FWocr_owner_correction_queue_test-"))
            self.assertEqual(evidence_packet["source_image_relative_path"], "files/0708/20260708113000_杨婷_资金账户截图.png")
            self.assertEqual(evidence_packet["candidate_business_date"], "2026-07-08")
            self.assertEqual(evidence_packet["candidate_amount"], "12345.67")
            self.assertEqual(evidence_packet["candidate_line_number"], "4")
            self.assertIn("武汉开明", evidence_packet["candidate_line_text_excerpt"])
            self.assertEqual(evidence_packet["current_company"], "武汉开明")
            self.assertEqual(evidence_packet["current_bank"], "")
            self.assertEqual(evidence_packet["missing_required_fields"], "bank")
            self.assertEqual(evidence_packet["required_owner_fields"], "owner_corrected_bank")
            self.assertEqual(
                evidence_packet["owner_decision_manifest_relative_path"],
                f"KMFA/metadata/fund_weekly_analysis/private_runtime/ocr_fact_candidate_owner_decisions/{run_id}.json",
            )
            self.assertEqual(evidence_packet["evidence_packet_status"], "ready_for_owner_field_review_no_write")
            self.assertEqual(evidence_packet["owner_decision_manifest_write_allowed"], "false")
            self.assertEqual(evidence_packet["fund_ledger_write_allowed"], "false")
            self.assertEqual(evidence_packet["formal_fund_ledger_write_allowed"], "false")
            self.assertEqual(evidence_packet["financial_fact_promoted"], "false")
            self.assertEqual(evidence_packet["management_conclusion_allowed"], "false")
            self.assertIn('"owner_authorization_decision":"needs_correction"', evidence_packet["owner_decision_json_fragment"])

            with (run_dir / "ocr_fact_owner_decision_correction_ocr_line_context.csv").open(encoding="utf-8-sig", newline="") as f:
                correction_ocr_line_context_rows = list(csv.DictReader(f))
            self.assertEqual(len(correction_ocr_line_context_rows), 7)
            self.assertEqual(
                [row["ocr_line_offset"] for row in correction_ocr_line_context_rows],
                ["-3", "-2", "-1", "0", "1", "2", "3"],
            )
            self.assertEqual(
                [row["ocr_line_number"] for row in correction_ocr_line_context_rows],
                ["1", "2", "3", "4", "5", "6", "7"],
            )
            target_ocr_line = correction_ocr_line_context_rows[3]
            self.assertEqual(target_ocr_line["source_evidence_packet_id"], evidence_packet["evidence_packet_id"])
            self.assertEqual(target_ocr_line["fact_candidate_id"], f"OCRFACT-{run_id}-00001")
            self.assertEqual(target_ocr_line["target_ocr_line_number"], "4")
            self.assertIn("银行存款 12,345.67", target_ocr_line["ocr_line_text_excerpt"])
            self.assertEqual(target_ocr_line["ocr_line_context_status"], "ready_ocr_line_context_no_write")
            self.assertTrue(all(row["owner_field_autofill_allowed"] == "false" for row in correction_ocr_line_context_rows))
            self.assertTrue(all(row["owner_decision_manifest_write_allowed"] == "false" for row in correction_ocr_line_context_rows))
            self.assertTrue(all(row["fund_ledger_write_allowed"] == "false" for row in correction_ocr_line_context_rows))
            self.assertTrue(all(row["formal_fund_ledger_write_allowed"] == "false" for row in correction_ocr_line_context_rows))
            self.assertTrue(all(row["financial_fact_promoted"] == "false" for row in correction_ocr_line_context_rows))
            self.assertTrue(all(row["management_conclusion_allowed"] == "false" for row in correction_ocr_line_context_rows))

            with (run_dir / "ocr_fact_owner_decision_correction_chat_context.csv").open(encoding="utf-8-sig", newline="") as f:
                correction_chat_context_rows = list(csv.DictReader(f))
            self.assertEqual(len(correction_chat_context_rows), 1)
            chat_context = correction_chat_context_rows[0]
            self.assertEqual(chat_context["fact_candidate_id"], f"OCRFACT-{run_id}-00001")
            self.assertEqual(chat_context["source_evidence_packet_id"], evidence_packet["evidence_packet_id"])
            self.assertEqual(chat_context["open_message_id"], "msg-fixture-001")
            self.assertEqual(chat_context["message_time"], "2026-07-08 11:30:00")
            self.assertEqual(chat_context["sender_name"], "杨婷")
            self.assertEqual(chat_context["resource_type"], "image")
            self.assertEqual(chat_context["resource_status"], "downloaded")
            self.assertEqual(chat_context["manifest_row_number"], "2")
            self.assertEqual(chat_context["chat_record_row_number"], "4")
            self.assertIn("武汉开明资金账户截图", chat_context["chat_content_excerpt"])
            self.assertEqual(chat_context["context_status"], "ready_chat_context_no_write")
            self.assertEqual(chat_context["owner_field_autofill_allowed"], "false")
            self.assertEqual(chat_context["owner_decision_manifest_write_allowed"], "false")
            self.assertEqual(chat_context["fund_ledger_write_allowed"], "false")
            self.assertEqual(chat_context["formal_fund_ledger_write_allowed"], "false")
            self.assertEqual(chat_context["financial_fact_promoted"], "false")
            self.assertEqual(chat_context["management_conclusion_allowed"], "false")

            with (run_dir / "ocr_fact_owner_decision_correction_chat_neighbor_context.csv").open(encoding="utf-8-sig", newline="") as f:
                correction_chat_neighbor_context_rows = list(csv.DictReader(f))
            self.assertEqual(len(correction_chat_neighbor_context_rows), 5)
            self.assertEqual(
                [row["neighbor_offset"] for row in correction_chat_neighbor_context_rows],
                ["-2", "-1", "0", "1", "2"],
            )
            self.assertEqual(
                [row["neighbor_chat_record_row_number"] for row in correction_chat_neighbor_context_rows],
                ["2", "3", "4", "5", "6"],
            )
            target_neighbor = correction_chat_neighbor_context_rows[2]
            self.assertEqual(target_neighbor["source_chat_context_id"], chat_context["chat_context_id"])
            self.assertEqual(target_neighbor["source_evidence_packet_id"], evidence_packet["evidence_packet_id"])
            self.assertEqual(target_neighbor["fact_candidate_id"], f"OCRFACT-{run_id}-00001")
            self.assertEqual(target_neighbor["target_chat_record_row_number"], "4")
            self.assertEqual(target_neighbor["open_message_id"], "msg-fixture-001")
            self.assertIn("武汉开明资金账户截图", target_neighbor["content_excerpt"])
            self.assertEqual(target_neighbor["neighbor_context_status"], "ready_neighbor_context_no_write")
            self.assertTrue(all(row["owner_field_autofill_allowed"] == "false" for row in correction_chat_neighbor_context_rows))
            self.assertTrue(all(row["owner_decision_manifest_write_allowed"] == "false" for row in correction_chat_neighbor_context_rows))
            self.assertTrue(all(row["fund_ledger_write_allowed"] == "false" for row in correction_chat_neighbor_context_rows))
            self.assertTrue(all(row["formal_fund_ledger_write_allowed"] == "false" for row in correction_chat_neighbor_context_rows))
            self.assertTrue(all(row["financial_fact_promoted"] == "false" for row in correction_chat_neighbor_context_rows))
            self.assertTrue(all(row["management_conclusion_allowed"] == "false" for row in correction_chat_neighbor_context_rows))

            with (run_dir / "ocr_fact_owner_decision_correction_owner_review_packet.csv").open(encoding="utf-8-sig", newline="") as f:
                correction_owner_review_packet_rows = list(csv.DictReader(f))
            self.assertEqual(len(correction_owner_review_packet_rows), 1)
            owner_review_packet = correction_owner_review_packet_rows[0]
            self.assertEqual(owner_review_packet["fact_candidate_id"], f"OCRFACT-{run_id}-00001")
            self.assertEqual(owner_review_packet["source_evidence_packet_id"], evidence_packet["evidence_packet_id"])
            self.assertEqual(owner_review_packet["missing_required_fields"], "bank")
            self.assertEqual(owner_review_packet["required_owner_fields"], "owner_corrected_bank")
            self.assertEqual(owner_review_packet["current_company"], "武汉开明")
            self.assertEqual(owner_review_packet["current_bank"], "")
            self.assertEqual(owner_review_packet["candidate_business_date"], "2026-07-08")
            self.assertEqual(owner_review_packet["candidate_amount"], "12345.67")
            self.assertEqual(owner_review_packet["ocr_line_context_ready_count"], "7")
            self.assertEqual(owner_review_packet["chat_context_ready_count"], "1")
            self.assertEqual(owner_review_packet["chat_neighbor_context_ready_count"], "5")
            self.assertIn("银行存款 12,345.67", owner_review_packet["ocr_line_context_excerpt"])
            self.assertIn("武汉开明资金账户截图", owner_review_packet["chat_context_excerpt"])
            self.assertIn("请确认收款银行", owner_review_packet["chat_neighbor_context_excerpt"])
            self.assertEqual(owner_review_packet["owner_review_packet_status"], "ready_for_owner_field_decision_no_write")
            self.assertEqual(owner_review_packet["owner_field_autofill_allowed"], "false")
            self.assertEqual(owner_review_packet["owner_decision_manifest_write_allowed"], "false")
            self.assertEqual(owner_review_packet["fund_ledger_write_allowed"], "false")
            self.assertEqual(owner_review_packet["formal_fund_ledger_write_allowed"], "false")
            self.assertEqual(owner_review_packet["financial_fact_promoted"], "false")
            self.assertEqual(owner_review_packet["management_conclusion_allowed"], "false")

            with (run_dir / "ocr_fact_owner_decision_correction_manifest_readiness.csv").open(encoding="utf-8-sig", newline="") as f:
                correction_manifest_readiness_rows = list(csv.DictReader(f))
            self.assertEqual(len(correction_manifest_readiness_rows), 1)
            manifest_readiness = correction_manifest_readiness_rows[0]
            self.assertEqual(manifest_readiness["source_owner_review_packet_id"], owner_review_packet["owner_review_packet_id"])
            self.assertEqual(manifest_readiness["source_evidence_packet_id"], evidence_packet["evidence_packet_id"])
            self.assertEqual(manifest_readiness["fact_candidate_id"], f"OCRFACT-{run_id}-00001")
            self.assertEqual(manifest_readiness["candidate_metric"], "bank_deposit")
            self.assertEqual(manifest_readiness["missing_required_fields"], "bank")
            self.assertEqual(manifest_readiness["required_owner_fields"], "owner_corrected_bank")
            self.assertEqual(
                manifest_readiness["decision_manifest_relative_path"],
                f"KMFA/metadata/fund_weekly_analysis/private_runtime/ocr_fact_candidate_owner_decisions/{run_id}.json",
            )
            self.assertEqual(manifest_readiness["decision_manifest_status"], "valid_decision_manifest")
            self.assertEqual(manifest_readiness["owner_decision_entry_status"], "owner_decision_entry_present")
            self.assertEqual(manifest_readiness["owner_authorization_decision"], "approve_for_review_authorization")
            self.assertEqual(manifest_readiness["owner_corrected_company"], "武汉开明")
            self.assertEqual(manifest_readiness["owner_corrected_bank"], "")
            self.assertEqual(manifest_readiness["missing_owner_values"], "owner_corrected_bank")
            self.assertEqual(
                manifest_readiness["manifest_readiness_status"],
                "blocked_owner_decision_missing_required_values",
            )
            self.assertEqual(manifest_readiness["owner_decision_manifest_write_allowed"], "false")
            self.assertEqual(manifest_readiness["source_mutation_allowed"], "false")
            self.assertEqual(manifest_readiness["fund_ledger_write_allowed"], "false")
            self.assertEqual(manifest_readiness["formal_fund_ledger_write_allowed"], "false")
            self.assertEqual(manifest_readiness["financial_fact_promoted"], "false")
            self.assertEqual(manifest_readiness["management_conclusion_allowed"], "false")

            correction_draft = json.loads(
                (run_dir / "ocr_fact_owner_decision_correction_draft.json").read_text(encoding="utf-8")
            )
            self.assertEqual(correction_draft["draft_status"], "owner_decision_correction_manifest_draft")
            self.assertEqual(correction_draft["generated_from"], "ocr_fact_owner_decision_correction_queue.csv")
            self.assertEqual(
                correction_draft["output_decision_manifest_relative_path"],
                f"KMFA/metadata/fund_weekly_analysis/private_runtime/ocr_fact_candidate_owner_decisions/{run_id}.json",
            )
            self.assertFalse(correction_draft["financial_fact_promotion_allowed"])
            self.assertFalse(correction_draft["fund_ledger_write_allowed"])
            self.assertFalse(correction_draft["management_conclusion_allowed"])
            self.assertEqual(len(correction_draft["owner_decisions"]), 1)
            draft_decision = correction_draft["owner_decisions"][0]
            self.assertEqual(draft_decision["fact_candidate_id"], f"OCRFACT-{run_id}-00001")
            self.assertEqual(draft_decision["candidate_metric"], "bank_deposit")
            self.assertEqual(draft_decision["owner_authorization_decision"], "needs_correction")
            self.assertEqual(draft_decision["owner_corrected_company"], "武汉开明")
            self.assertEqual(draft_decision["owner_corrected_bank"], "")
            self.assertIn("owner_corrected_bank", draft_decision["required_owner_fields"])
            self.assertEqual(draft_decision["source_correction_queue_id"], row["correction_queue_id"])

            with (run_dir / "ocr_fact_owner_decision_correction_apply_preview.csv").open(encoding="utf-8-sig", newline="") as f:
                correction_apply_preview_rows = list(csv.DictReader(f))
            self.assertEqual(len(correction_apply_preview_rows), 1)
            apply_preview = correction_apply_preview_rows[0]
            self.assertEqual(apply_preview["fact_candidate_id"], f"OCRFACT-{run_id}-00001")
            self.assertEqual(apply_preview["draft_owner_authorization_decision"], "needs_correction")
            self.assertEqual(apply_preview["correction_apply_preview_status"], "blocked_draft_still_needs_owner_values")
            self.assertEqual(apply_preview["manual_save_ready"], "false")
            self.assertEqual(apply_preview["owner_decision_manifest_write_allowed"], "false")
            self.assertIn("owner_corrected_bank", apply_preview["missing_owner_values"])
            self.assertEqual(apply_preview["fund_ledger_write_allowed"], "false")
            self.assertEqual(apply_preview["formal_fund_ledger_write_allowed"], "false")
            self.assertEqual(apply_preview["financial_fact_promoted"], "false")
            self.assertEqual(apply_preview["management_conclusion_allowed"], "false")

            with (run_dir / "ocr_fact_controlled_ledger_apply_gate.csv").open(encoding="utf-8-sig", newline="") as f:
                apply_gate_rows = list(csv.DictReader(f))
            self.assertEqual(apply_gate_rows[0]["apply_gate_status"], "blocked_missing_required_ledger_fields")
            self.assertEqual(apply_gate_rows[0]["planned_apply_count"], "0")

            with (run_dir / "ocr_fact_owner_decision_correction_roundtrip_audit.csv").open(encoding="utf-8-sig", newline="") as f:
                roundtrip_rows = list(csv.DictReader(f))
            self.assertEqual(len(roundtrip_rows), 1)
            self.assertEqual(roundtrip_rows[0]["fact_candidate_id"], f"OCRFACT-{run_id}-00001")
            self.assertEqual(
                roundtrip_rows[0]["correction_roundtrip_status"],
                "owner_correction_present_apply_gate_still_blocked",
            )
            self.assertEqual(roundtrip_rows[0]["owner_correction_applied"], "true")
            self.assertEqual(roundtrip_rows[0]["company_source"], "owner_decision_preview")
            self.assertEqual(roundtrip_rows[0]["bank_source"], "ocr_fact_candidate")
            self.assertEqual(roundtrip_rows[0]["fund_ledger_write_allowed"], "false")
            self.assertEqual(roundtrip_rows[0]["formal_fund_ledger_write_allowed"], "false")
            self.assertEqual(roundtrip_rows[0]["financial_fact_promoted"], "false")
            self.assertEqual(roundtrip_rows[0]["management_conclusion_allowed"], "false")

            cross_review = json.loads((run_dir / "cross_review.json").read_text(encoding="utf-8"))
            self.assertEqual(cross_review["ocr_fact_owner_decision_correction_queue_count"], 1)
            self.assertEqual(cross_review["ocr_fact_owner_decision_correction_queue_blocking_count"], 1)
            self.assertEqual(cross_review["ocr_fact_owner_decision_correction_queue_write_allowed_count"], 0)
            self.assertEqual(cross_review["ocr_fact_owner_decision_correction_draft_count"], 1)
            self.assertEqual(cross_review["ocr_fact_owner_decision_correction_draft_write_allowed_count"], 0)
            self.assertEqual(cross_review["ocr_fact_owner_decision_correction_apply_preview_count"], 1)
            self.assertEqual(cross_review["ocr_fact_owner_decision_correction_apply_preview_ready_count"], 0)
            self.assertEqual(cross_review["ocr_fact_owner_decision_correction_apply_preview_blocking_count"], 1)
            self.assertEqual(cross_review["ocr_fact_owner_decision_correction_apply_preview_write_allowed_count"], 0)
            self.assertEqual(cross_review["ocr_fact_owner_decision_correction_roundtrip_audit_count"], 1)
            self.assertEqual(cross_review["ocr_fact_owner_decision_correction_roundtrip_audit_ready_count"], 0)
            self.assertEqual(cross_review["ocr_fact_owner_decision_correction_roundtrip_audit_blocking_count"], 1)
            self.assertEqual(cross_review["ocr_fact_owner_decision_correction_roundtrip_audit_write_allowed_count"], 0)
            self.assertEqual(cross_review["ocr_fact_owner_decision_correction_evidence_packet_count"], 1)
            self.assertEqual(cross_review["ocr_fact_owner_decision_correction_evidence_packet_ready_count"], 1)
            self.assertEqual(cross_review["ocr_fact_owner_decision_correction_evidence_packet_blocking_count"], 0)
            self.assertEqual(cross_review["ocr_fact_owner_decision_correction_evidence_packet_write_allowed_count"], 0)
            self.assertEqual(cross_review["ocr_fact_owner_decision_correction_ocr_line_context_count"], 7)
            self.assertEqual(cross_review["ocr_fact_owner_decision_correction_ocr_line_context_ready_count"], 7)
            self.assertEqual(cross_review["ocr_fact_owner_decision_correction_ocr_line_context_blocking_count"], 0)
            self.assertEqual(cross_review["ocr_fact_owner_decision_correction_ocr_line_context_write_allowed_count"], 0)
            self.assertEqual(cross_review["ocr_fact_owner_decision_correction_chat_context_count"], 1)
            self.assertEqual(cross_review["ocr_fact_owner_decision_correction_chat_context_ready_count"], 1)
            self.assertEqual(cross_review["ocr_fact_owner_decision_correction_chat_context_blocking_count"], 0)
            self.assertEqual(cross_review["ocr_fact_owner_decision_correction_chat_context_write_allowed_count"], 0)
            self.assertEqual(cross_review["ocr_fact_owner_decision_correction_chat_neighbor_context_count"], 5)
            self.assertEqual(cross_review["ocr_fact_owner_decision_correction_chat_neighbor_context_ready_count"], 5)
            self.assertEqual(cross_review["ocr_fact_owner_decision_correction_chat_neighbor_context_blocking_count"], 0)
            self.assertEqual(cross_review["ocr_fact_owner_decision_correction_chat_neighbor_context_write_allowed_count"], 0)
            self.assertEqual(cross_review["ocr_fact_owner_decision_correction_owner_review_packet_count"], 1)
            self.assertEqual(cross_review["ocr_fact_owner_decision_correction_owner_review_packet_ready_count"], 1)
            self.assertEqual(cross_review["ocr_fact_owner_decision_correction_owner_review_packet_blocking_count"], 0)
            self.assertEqual(cross_review["ocr_fact_owner_decision_correction_owner_review_packet_write_allowed_count"], 0)
            self.assertEqual(cross_review["ocr_fact_owner_decision_correction_manifest_readiness_count"], 1)
            self.assertEqual(cross_review["ocr_fact_owner_decision_correction_manifest_readiness_ready_count"], 0)
            self.assertEqual(cross_review["ocr_fact_owner_decision_correction_manifest_readiness_blocking_count"], 1)
            self.assertEqual(cross_review["ocr_fact_owner_decision_correction_manifest_readiness_write_allowed_count"], 0)
            self.assertEqual(cross_review["generated_financial_amount_count"], 0)
            self.assertFalse(cross_review["management_conclusion_allowed"])

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
                    "2026-07-08T11:00:00+10:00",
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

    def test_ocr_sidecar_generation_preserves_existing_plan_rows_and_appends_batches(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir) / "repo"
            input_dir = Path(temp_dir) / "OneDrive-Personal" / "DWS_Outputs" / "付款请示群"
            run_dir = repo_root / "KMFA/metadata/fund_weekly_analysis/private_runtime/runs/vision_ocr_resume_test"
            image_dir = input_dir / "files" / "0708"
            image_dir.mkdir(parents=True)
            run_dir.mkdir(parents=True)
            existing_image = image_dir / "image_0.png"
            new_image = image_dir / "image_1.png"
            existing_image.write_bytes(b"real-image-0")
            new_image.write_bytes(b"real-image-1")

            existing_rel = Path(
                "KMFA/metadata/fund_weekly_analysis/private_runtime/ocr_sidecars/"
                "vision_ocr_resume_test/OCRGEN-vision_ocr_resume_test-00001.ocr.txt"
            )
            existing_sidecar = repo_root / existing_rel
            existing_sidecar.parent.mkdir(parents=True)
            existing_sidecar.write_text("已有文本\n", encoding="utf-8")
            with (run_dir / "screenshot_ocr_sidecar_generation_plan.csv").open("w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=[
                    "ocr_generation_id",
                    "evidence_id",
                    "source_image_relative_path",
                    "engine",
                    "generation_status",
                    "ocr_text_private_relative_path",
                    "text_length",
                    "text_sha256",
                    "apply_performed",
                    "financial_fact_promoted",
                    "review_status",
                    "reason",
                ])
                writer.writeheader()
                writer.writerow({
                    "ocr_generation_id": "OCRGEN-vision_ocr_resume_test-00001",
                    "evidence_id": "FW-00000",
                    "source_image_relative_path": "files/0708/image_0.png",
                    "engine": "vision",
                    "generation_status": "ocr_text_generated_pending_review",
                    "ocr_text_private_relative_path": str(existing_rel),
                    "text_length": str(len("已有文本")),
                    "text_sha256": hashlib.sha256("已有文本".encode("utf-8")).hexdigest(),
                    "apply_performed": "true",
                    "financial_fact_promoted": "false",
                    "review_status": "pending_human_review",
                    "reason": "",
                })

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
                for index in range(2):
                    writer.writerow({
                        "ocr_coverage_id": f"OCRCOV-vision_ocr_resume_test-{index:05d}",
                        "evidence_id": f"FW-{index:05d}",
                        "source_image_relative_path": f"files/0708/image_{index}.png",
                        "ocr_sidecar_candidates": f"files/0708/image_{index}.png.ocr.txt",
                        "ocr_text_relative_path": "",
                        "ocr_coverage_status": "ocr_text_sidecar_missing",
                        "next_action": "run_ocr_or_attach_real_ocr_sidecar",
                        "review_status": "pending_ocr_extraction",
                        "financial_fact_promoted": "false",
                    })

            fake_vision = Path(temp_dir) / "fake_vision.py"
            fake_vision.write_text(
                "import json, sys\n"
                "for path in sys.argv[1:]:\n"
                "    print(json.dumps({'path': path, 'status': 'ocr_text_available', 'text': '新增文本 456.78', 'reason': ''}, ensure_ascii=False))\n",
                encoding="utf-8",
            )
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
            self.assertEqual(existing_sidecar.read_text(encoding="utf-8"), "已有文本\n")
            with (run_dir / "screenshot_ocr_sidecar_generation_plan.csv").open(encoding="utf-8-sig", newline="") as f:
                plan_rows = list(csv.DictReader(f))
            self.assertEqual([row["ocr_generation_id"] for row in plan_rows], [
                "OCRGEN-vision_ocr_resume_test-00001",
                "OCRGEN-vision_ocr_resume_test-00002",
            ])
            self.assertEqual(plan_rows[0]["source_image_relative_path"], "files/0708/image_0.png")
            self.assertEqual(plan_rows[1]["source_image_relative_path"], "files/0708/image_1.png")
            self.assertTrue((repo_root / plan_rows[1]["ocr_text_private_relative_path"]).exists())

            summary = json.loads((run_dir / "screenshot_ocr_sidecar_generation_summary.json").read_text(encoding="utf-8"))
            self.assertEqual(summary["planned_count"], 2)
            self.assertEqual(summary["generated_sidecar_count"], 1)
            self.assertEqual(summary["text_available_count"], 2)

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

    def test_vision_ocr_timeout_rows_are_retried_in_smaller_batches(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir) / "repo"
            input_dir = Path(temp_dir) / "OneDrive-Personal" / "DWS_Outputs" / "付款请示群"
            run_dir = repo_root / "KMFA/metadata/fund_weekly_analysis/private_runtime/runs/vision_ocr_retry_test"
            image_dir = input_dir / "files" / "0708"
            image_dir.mkdir(parents=True)
            run_dir.mkdir(parents=True)
            call_log = Path(temp_dir) / "vision_retry_calls.jsonl"
            fake_vision = Path(temp_dir) / "retry_vision.py"
            fake_vision.write_text(
                "import json, os, sys, time\n"
                "paths = sys.argv[1:]\n"
                "with open(os.environ['VISION_CALL_LOG'], 'a', encoding='utf-8') as f:\n"
                "    f.write(json.dumps({'count': len(paths)}) + '\\n')\n"
                "if len(paths) > 1:\n"
                "    time.sleep(2)\n"
                "for path in paths:\n"
                "    print(json.dumps({'path': path, 'status': 'ocr_text_available', 'text': 'retry text 123.45', 'reason': ''}))\n",
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
                for index in range(2):
                    image = image_dir / f"image_{index}.png"
                    image.write_bytes(b"real-image-bytes")
                    writer.writerow({
                        "ocr_coverage_id": f"OCRCOV-vision_ocr_retry_test-{index:05d}",
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
                    "--timeout-seconds",
                    "1",
                    "--vision-batch-size",
                    "2",
                    "--retry-timeout-seconds",
                    "3",
                    "--retry-batch-size",
                    "1",
                ],
                text=True,
                capture_output=True,
                check=False,
                env=env,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            calls = [json.loads(line)["count"] for line in call_log.read_text(encoding="utf-8").splitlines()]
            self.assertEqual(calls, [2, 1, 1])
            with (run_dir / "screenshot_ocr_sidecar_generation_plan.csv").open(encoding="utf-8-sig", newline="") as f:
                plan_rows = list(csv.DictReader(f))
            self.assertEqual([row["generation_status"] for row in plan_rows], ["ocr_text_generated_pending_review"] * 2)
            self.assertTrue(all(row["apply_performed"] == "true" for row in plan_rows))
            self.assertTrue(all(row["financial_fact_promoted"] == "false" for row in plan_rows))
            self.assertTrue(all((repo_root / row["ocr_text_private_relative_path"]).exists() for row in plan_rows))

            summary = json.loads((run_dir / "screenshot_ocr_sidecar_generation_summary.json").read_text(encoding="utf-8"))
            self.assertEqual(summary["timeout_retry_attempt_count"], 2)
            self.assertEqual(summary["timeout_retry_generated_count"], 2)
            self.assertEqual(summary["generated_sidecar_count"], 2)

    def test_vision_ocr_retry_budget_defers_excess_timeout_rows_and_writes_progress(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir) / "repo"
            input_dir = Path(temp_dir) / "OneDrive-Personal" / "DWS_Outputs" / "付款请示群"
            run_dir = repo_root / "KMFA/metadata/fund_weekly_analysis/private_runtime/runs/vision_ocr_retry_budget_test"
            image_dir = input_dir / "files" / "0708"
            image_dir.mkdir(parents=True)
            run_dir.mkdir(parents=True)
            call_log = Path(temp_dir) / "vision_retry_budget_calls.jsonl"
            fake_vision = Path(temp_dir) / "retry_budget_vision.py"
            fake_vision.write_text(
                "import json, os, sys, time\n"
                "paths = sys.argv[1:]\n"
                "with open(os.environ['VISION_CALL_LOG'], 'a', encoding='utf-8') as f:\n"
                "    f.write(json.dumps({'count': len(paths)}) + '\\n')\n"
                "if len(paths) > 1:\n"
                "    time.sleep(2)\n"
                "for path in paths:\n"
                "    print(json.dumps({'path': path, 'status': 'ocr_text_available', 'text': 'retry text 123.45', 'reason': ''}))\n",
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
                        "ocr_coverage_id": f"OCRCOV-vision_ocr_retry_budget_test-{index:05d}",
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
                    "--retry-timeout-seconds",
                    "3",
                    "--retry-batch-size",
                    "1",
                    "--retry-max-rows",
                    "1",
                ],
                text=True,
                capture_output=True,
                check=False,
                env=env,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertLess(time.monotonic() - started, 5)
            calls = [json.loads(line)["count"] for line in call_log.read_text(encoding="utf-8").splitlines()]
            self.assertEqual(calls, [3, 1])
            with (run_dir / "screenshot_ocr_sidecar_generation_plan.csv").open(encoding="utf-8-sig", newline="") as f:
                plan_rows = list(csv.DictReader(f))
            self.assertEqual([row["generation_status"] for row in plan_rows], [
                "ocr_text_generated_pending_review",
                "ocr_retry_deferred_due_retry_budget",
                "ocr_retry_deferred_due_retry_budget",
            ])
            self.assertTrue((repo_root / plan_rows[0]["ocr_text_private_relative_path"]).exists())
            self.assertTrue(all(row["financial_fact_promoted"] == "false" for row in plan_rows))

            progress_path = run_dir / "screenshot_ocr_sidecar_generation_progress.jsonl"
            self.assertTrue(progress_path.exists())
            progress_text = progress_path.read_text(encoding="utf-8")
            self.assertIn("retry_deferred_due_retry_budget", progress_text)
            self.assertNotIn("retry text 123.45", progress_text)

            summary = json.loads((run_dir / "screenshot_ocr_sidecar_generation_summary.json").read_text(encoding="utf-8"))
            self.assertEqual(summary["retry_max_rows"], 1)
            self.assertEqual(summary["timeout_retry_attempt_count"], 1)
            self.assertEqual(summary["timeout_retry_deferred_count"], 2)
            self.assertEqual(summary["generated_sidecar_count"], 1)

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
                    "2026-07-08T11:00:00+10:00",
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
                    "message_time": "2026-07-08T11:00:00+10:00",
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
                    "message_time": "2026-07-08T11:00:00+10:00",
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
                    "message_time": "2026-07-08T11:01:00+10:00",
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
                    "message_time": "2026-07-08T11:02:00+10:00",
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
                    "message_time": "2026-07-08T11:00:00+10:00",
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
                    "message_time": "2026-07-08T11:01:00+10:00",
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
                    "message_time": "2026-07-08T11:02:00+10:00",
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
                    "message_time": "2026-07-08T11:00:00+10:00",
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
                    "message_time": "2026-07-08T11:01:00+10:00",
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
                    "message_time": "2026-07-08T11:02:00+10:00",
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
                    "message_time": "2026-07-08T11:00:00+10:00",
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
                    "message_time": "2026-07-08T11:01:00+10:00",
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
                    "message_time": "2026-07-08T11:02:00+10:00",
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

    def test_runner_locates_attachment_repair_source_candidates_without_applying(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir) / "repo"
            one_drive_root = Path(temp_dir) / "OneDrive-Personal"
            input_dir = one_drive_root / "DWS_Outputs" / "付款请示群"
            manifest_dir = input_dir / "_manifest"
            file_dir = input_dir / "files" / "0708"
            manifest_dir.mkdir(parents=True)
            file_dir.mkdir(parents=True)

            missing_rel = "files/0708/20260708113200_missing_image.png"
            zip_path = one_drive_root / "DWS_Outputs.zip"
            with zipfile.ZipFile(zip_path, "w") as zf:
                zf.writestr(f"DWS_Outputs/付款请示群/{missing_rel}", b"recoverable-image")

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
                    "message_time": "2026-07-08T11:00:00+10:00",
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
                    "message_time": "2026-07-08T11:01:00+10:00",
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
                    "attachment_source_locator_test",
                    "--timezone",
                    "Australia/Sydney",
                ],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            run_dir = repo_root / "KMFA/metadata/fund_weekly_analysis/private_runtime/runs/attachment_source_locator_test"
            with (run_dir / "attachment_repair_source_locator.csv").open(encoding="utf-8-sig", newline="") as f:
                locator_rows = list(csv.DictReader(f))
            self.assertEqual(len(locator_rows), 2)
            locator_by_message = {row["open_message_id"]: row for row in locator_rows}
            self.assertEqual(locator_by_message["msg-missing-file"]["locator_status"], "candidate_in_source_zip")
            self.assertEqual(locator_by_message["msg-missing-file"]["source_zip_member"], f"DWS_Outputs/付款请示群/{missing_rel}")
            self.assertEqual(locator_by_message["msg-missing-file"]["local_input_exists"], "false")
            self.assertEqual(locator_by_message["msg-missing-file"]["safe_to_apply"], "false")
            self.assertEqual(locator_by_message["msg-missing-file"]["apply_performed"], "false")
            self.assertEqual(locator_by_message["msg-missing-output"]["locator_status"], "requires_dws_attachment_rerun")
            self.assertEqual(locator_by_message["msg-missing-output"]["source_zip_member"], "")
            self.assertTrue(all(row["source_mutation_allowed"] == "false" for row in locator_rows))
            self.assertTrue(all(row["formal_fact_allowed"] == "false" for row in locator_rows))

            self.assertFalse((input_dir / missing_rel).exists())
            cross_review = json.loads((run_dir / "cross_review.json").read_text(encoding="utf-8"))
            self.assertEqual(cross_review["attachment_repair_source_locator_count"], 2)
            self.assertEqual(cross_review["attachment_repair_source_locator_candidate_count"], 1)
            self.assertEqual(cross_review["attachment_repair_source_locator_apply_allowed_count"], 0)
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
                    "message_time": "2026-07-08T11:00:00+10:00",
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
                    "message_time": "2026-07-08T11:01:00+10:00",
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
                    "message_time": "2026-07-08T11:02:00+10:00",
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
                    "message_time": "2026-07-08T11:00:00+10:00",
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
                    "message_time": "2026-07-08T11:01:00+10:00",
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
            auth_dir = repo_root / "KMFA/metadata/fund_weekly_analysis/private_runtime/fact_promotion_authorizations"
            execution_auth_dir = (
                repo_root
                / "KMFA/metadata/fund_weekly_analysis/private_runtime/fact_promotion_execution_authorizations"
            )
            contract_dir = repo_root / "KMFA/fund-weekly-analysis-skill/automation"
            source_day.mkdir(parents=True)
            auth_dir.mkdir(parents=True)
            execution_auth_dir.mkdir(parents=True)
            contract_dir.mkdir(parents=True)
            contract = (SKILL_ROOT / "automation" / "codex_app_automation.contract.toml").read_text(encoding="utf-8")
            prompt = (SKILL_ROOT / "automation" / "weekly_mon_sat_1100_sydney.prompt.md").read_text(encoding="utf-8")
            (contract_dir / "codex_app_automation.contract.toml").write_text(contract, encoding="utf-8")
            (contract_dir / "weekly_mon_sat_1100_sydney.prompt.md").write_text(prompt, encoding="utf-8")
            automation_root = Path(temp_dir) / "automations"
            automation_dir = automation_root / "kmfa"
            automation_dir.mkdir(parents=True)
            (automation_dir / "automation.toml").write_text(contract + "\nprompt = '''" + prompt + "'''\n", encoding="utf-8")
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
            authorization_manifest = {
                "authorization_manifest_version": "1",
                "run_id": "structured_csv_test",
                "authorization_scope": "fact_promotion_review_packet_validation_only",
                "authorized_by": "operator-fixture",
                "authorized_at": "2026-07-08T11:50:00+10:00",
                "authorization_ticket": "S61-TEST",
                "financial_fact_promotion_allowed": False,
                "fund_ledger_write_allowed": False,
                "management_conclusion_allowed": False,
                "review_packet_authorizations": [
                    {
                        "review_packet_id": "FPRP-structured_csv_test-00001",
                        "review_area": "structured_csv_facts",
                        "authorized": True,
                    },
                ],
            }
            (auth_dir / "structured_csv_test.json").write_text(
                json.dumps(authorization_manifest, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            execution_authorization_manifest = {
                "authorization_manifest_version": "1",
                "run_id": "structured_csv_test",
                "authorization_scope": "controlled_fact_promotion_execution",
                "authorized_by": "operator-fixture",
                "authorized_at": "2026-07-08T12:00:00+10:00",
                "authorization_ticket": "S63-TEST",
                "source_mutation_allowed": False,
                "fact_promotion_execution_allowed": False,
                "fund_ledger_write_allowed": False,
                "financial_fact_promoted": False,
                "management_conclusion_allowed": False,
                "execution_plan_authorizations": [
                    {
                        "execution_plan_id": "FPEXECPLAN-structured_csv_test-00001",
                        "review_area": "structured_csv_facts",
                        "authorized": True,
                    },
                ],
            }
            (execution_auth_dir / "structured_csv_test.json").write_text(
                json.dumps(execution_authorization_manifest, ensure_ascii=False, indent=2),
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
                    "--automation-root",
                    str(automation_root),
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
            self.assertEqual(cross_review["fact_promotion_execution_dry_run_count"], 7)
            self.assertEqual(cross_review["fact_promotion_execution_dry_run_ready_count"], 1)
            self.assertEqual(cross_review["fact_promotion_execution_dry_run_impact_count"], 4)
            self.assertEqual(cross_review["fact_promotion_execution_dry_run_write_allowed_count"], 0)
            self.assertEqual(cross_review["fact_promotion_execution_plan_count"], 7)
            self.assertEqual(cross_review["fact_promotion_execution_plan_ready_count"], 1)
            self.assertEqual(cross_review["fact_promotion_execution_plan_planned_impact_count"], 4)
            self.assertEqual(cross_review["fact_promotion_execution_plan_write_allowed_count"], 0)
            self.assertEqual(cross_review["fact_promotion_execution_authorization_preview_count"], 7)
            self.assertEqual(cross_review["fact_promotion_execution_authorization_preview_ready_count"], 1)
            self.assertEqual(cross_review["fact_promotion_execution_authorization_write_allowed_count"], 0)
            self.assertEqual(cross_review["fact_promotion_execution_apply_gate_count"], 7)
            self.assertEqual(cross_review["fact_promotion_execution_apply_gate_ready_count"], 1)
            self.assertEqual(cross_review["fact_promotion_execution_apply_gate_planned_apply_count"], 4)
            self.assertEqual(cross_review["fact_promotion_execution_apply_gate_write_allowed_count"], 0)
            self.assertEqual(cross_review["fact_promotion_execution_result_count"], 7)
            self.assertEqual(cross_review["fact_promotion_execution_result_formalized_area_count"], 1)
            self.assertEqual(cross_review["formal_fund_ledger_row_count"], 4)

            with (run_dir / "fact_promotion_execution_dry_run.csv").open(encoding="utf-8-sig", newline="") as f:
                dry_run_rows = list(csv.DictReader(f))
            dry_run_by_area = {row["review_area"]: row for row in dry_run_rows}
            self.assertEqual(
                dry_run_by_area["structured_csv_facts"]["dry_run_status"],
                "ready_for_controlled_execution_preview_no_write",
            )
            self.assertEqual(dry_run_by_area["structured_csv_facts"]["dry_run_impact_count"], "4")
            self.assertTrue(all(row["fact_promotion_execution_allowed"] == "false" for row in dry_run_rows))
            self.assertTrue(all(row["fund_ledger_write_allowed"] == "false" for row in dry_run_rows))
            self.assertTrue(all(row["financial_fact_promoted"] == "false" for row in dry_run_rows))
            self.assertTrue(all(row["management_conclusion_allowed"] == "false" for row in dry_run_rows))

            with (run_dir / "fact_promotion_execution_plan.csv").open(encoding="utf-8-sig", newline="") as f:
                execution_plan_rows = list(csv.DictReader(f))
            plan_by_area = {row["review_area"]: row for row in execution_plan_rows}
            self.assertEqual(
                plan_by_area["structured_csv_facts"]["execution_plan_status"],
                "ready_for_owner_execution_authorization_no_write",
            )
            self.assertEqual(
                plan_by_area["structured_csv_facts"]["required_authorization_scope"],
                "controlled_fact_promotion_execution",
            )
            self.assertEqual(plan_by_area["structured_csv_facts"]["planned_impact_count"], "4")
            self.assertTrue(all(row["source_mutation_allowed"] == "false" for row in execution_plan_rows))
            self.assertTrue(all(row["fact_promotion_execution_allowed"] == "false" for row in execution_plan_rows))
            self.assertTrue(all(row["fund_ledger_write_allowed"] == "false" for row in execution_plan_rows))
            self.assertTrue(all(row["financial_fact_promoted"] == "false" for row in execution_plan_rows))
            self.assertTrue(all(row["management_conclusion_allowed"] == "false" for row in execution_plan_rows))

            execution_auth_template = json.loads(
                (run_dir / "fact_promotion_execution_authorization_template.json").read_text(encoding="utf-8")
            )
            self.assertEqual(len(execution_auth_template["execution_plan_authorizations"]), 7)
            self.assertFalse(execution_auth_template["fact_promotion_execution_allowed"])
            self.assertFalse(execution_auth_template["fund_ledger_write_allowed"])

            with (run_dir / "fact_promotion_execution_authorization_preview.csv").open(
                encoding="utf-8-sig",
                newline="",
            ) as f:
                execution_auth_preview_rows = list(csv.DictReader(f))
            execution_auth_by_area = {row["review_area"]: row for row in execution_auth_preview_rows}
            self.assertEqual(
                execution_auth_by_area["structured_csv_facts"]["authorization_validation_status"],
                "valid_execution_authorization_manifest",
            )
            self.assertEqual(
                execution_auth_by_area["structured_csv_facts"]["preview_status"],
                "ready_for_controlled_execution_run_no_write",
            )
            self.assertEqual(execution_auth_by_area["structured_csv_facts"]["operator_authorization_present"], "true")
            self.assertTrue(all(row["source_mutation_allowed"] == "false" for row in execution_auth_preview_rows))
            self.assertTrue(
                all(row["fact_promotion_execution_allowed"] == "false" for row in execution_auth_preview_rows)
            )
            self.assertTrue(all(row["fund_ledger_write_allowed"] == "false" for row in execution_auth_preview_rows))
            self.assertTrue(all(row["financial_fact_promoted"] == "false" for row in execution_auth_preview_rows))
            self.assertTrue(all(row["management_conclusion_allowed"] == "false" for row in execution_auth_preview_rows))

            with (run_dir / "fact_promotion_execution_apply_gate.csv").open(
                encoding="utf-8-sig",
                newline="",
            ) as f:
                execution_apply_gate_rows = list(csv.DictReader(f))
            apply_gate_by_area = {row["review_area"]: row for row in execution_apply_gate_rows}
            self.assertEqual(
                apply_gate_by_area["structured_csv_facts"]["apply_gate_status"],
                "ready_for_controlled_execution_apply_no_write",
            )
            self.assertEqual(apply_gate_by_area["structured_csv_facts"]["planned_apply_count"], "4")
            self.assertTrue(all(row["source_mutation_allowed"] == "false" for row in execution_apply_gate_rows))
            self.assertTrue(all(row["fact_promotion_execution_allowed"] == "false" for row in execution_apply_gate_rows))
            self.assertTrue(all(row["fund_ledger_write_allowed"] == "false" for row in execution_apply_gate_rows))
            self.assertTrue(all(row["financial_fact_promoted"] == "false" for row in execution_apply_gate_rows))
            self.assertTrue(all(row["management_conclusion_allowed"] == "false" for row in execution_apply_gate_rows))

            with (run_dir / "fact_promotion_execution_result.csv").open(
                encoding="utf-8-sig",
                newline="",
            ) as f:
                execution_result_rows = list(csv.DictReader(f))
            execution_result_by_area = {row["review_area"]: row for row in execution_result_rows}
            self.assertEqual(
                execution_result_by_area["structured_csv_facts"]["execution_result_status"],
                "structured_csv_formal_ledger_sidecar_written",
            )
            self.assertEqual(execution_result_by_area["structured_csv_facts"]["formal_ledger_row_count"], "4")
            self.assertTrue(all(row["source_mutation_allowed"] == "false" for row in execution_result_rows))
            self.assertTrue(all(row["fund_ledger_mutation_allowed"] == "false" for row in execution_result_rows))
            self.assertTrue(all(row["management_conclusion_allowed"] == "false" for row in execution_result_rows))

            with (run_dir / "formal_fund_ledger.csv").open(encoding="utf-8-sig", newline="") as f:
                formal_rows = list(csv.DictReader(f))
            self.assertEqual(len(formal_rows), 4)
            self.assertEqual(formal_rows[0]["source_ledger_id"], "FL-structured_csv_test-00001")
            self.assertTrue(all(row["formal_fact_source"] == "structured_csv_facts" for row in formal_rows))
            self.assertTrue(
                all(row["formal_write_status"] == "structured_csv_formal_ledger_sidecar_written" for row in formal_rows)
            )
            self.assertTrue(all(row["source_mutation_allowed"] == "false" for row in formal_rows))
            self.assertTrue(all(row["fund_ledger_mutation_allowed"] == "false" for row in formal_rows))
            self.assertTrue(all(row["management_conclusion_allowed"] == "false" for row in formal_rows))

            with (run_dir / "management_conclusion_gate.csv").open(encoding="utf-8-sig", newline="") as f:
                management_gate_rows = list(csv.DictReader(f))
            self.assertEqual(len(management_gate_rows), 8)
            management_gate_by_area = {row["gate_area"]: row for row in management_gate_rows}
            self.assertEqual(
                management_gate_by_area["formal_fact_promotion_execution"]["gate_status"],
                "ready_formal_ledger_sidecar_written",
            )
            self.assertIn(
                "fact_promotion_execution_result_formalized_area_count=1",
                management_gate_by_area["formal_fact_promotion_execution"]["evidence"],
            )
            self.assertEqual(
                management_gate_by_area["formal_ledger_population"]["gate_status"],
                "ready_formal_ledger_sidecar",
            )
            self.assertIn(
                "formal_fund_ledger_row_count=4",
                management_gate_by_area["formal_ledger_population"]["evidence"],
            )
            self.assertEqual(
                management_gate_by_area["management_conclusion_final_authorization"]["gate_status"],
                "blocked_management_conclusion_release_not_authorized",
            )
            self.assertIn(
                "release_authorization_preview_status=blocked_missing_release_authorization",
                management_gate_by_area["management_conclusion_final_authorization"]["evidence"],
            )
            self.assertTrue(all(row["management_conclusion_allowed"] == "false" for row in management_gate_rows))

            release_template = json.loads(
                (run_dir / "management_conclusion_authorization_template.json").read_text(encoding="utf-8")
            )
            self.assertEqual(release_template["authorization_scope"], "management_conclusion_release_validation_only")
            self.assertFalse(release_template["management_conclusion_allowed"])
            self.assertEqual(release_template["release_authorizations"][0]["pre_release_blocking_count"], 0)

            with (run_dir / "management_conclusion_authorization_preview.csv").open(
                encoding="utf-8-sig",
                newline="",
            ) as f:
                release_preview_rows = list(csv.DictReader(f))
            self.assertEqual(len(release_preview_rows), 1)
            self.assertEqual(release_preview_rows[0]["authorization_validation_status"], "missing_release_authorization_manifest")
            self.assertEqual(release_preview_rows[0]["preview_status"], "blocked_missing_release_authorization")
            self.assertEqual(release_preview_rows[0]["pre_release_blocking_count"], "0")
            self.assertEqual(release_preview_rows[0]["management_conclusion_allowed"], "false")
            self.assertEqual(cross_review["management_conclusion_release_authorization_preview_count"], 1)
            self.assertEqual(cross_review["management_conclusion_release_authorization_preview_ready_count"], 0)
            self.assertEqual(cross_review["management_conclusion_release_authorization_preview_blocked_count"], 1)

            with (run_dir / "evidence_cross_review_resolution_plan.csv").open(encoding="utf-8-sig", newline="") as f:
                evidence_plan_rows = list(csv.DictReader(f))
            self.assertEqual(evidence_plan_rows, [])
            self.assertEqual(cross_review["evidence_cross_review_resolution_plan_count"], 0)
            self.assertEqual(cross_review["evidence_cross_review_resolution_plan_blocker_count"], 0)

            with (run_dir / "attachment_repair_source_locator.csv").open(encoding="utf-8-sig", newline="") as f:
                locator_rows = list(csv.DictReader(f))
            self.assertEqual(locator_rows, [])
            self.assertEqual(cross_review["attachment_repair_source_locator_count"], 0)
            self.assertEqual(cross_review["attachment_repair_source_locator_candidate_count"], 0)
            self.assertEqual(cross_review["attachment_repair_source_locator_apply_allowed_count"], 0)

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
                    "2026-07-08,开明一公司,招商银行,基本户,T0_BANK_CASH,0,2700.00,9000.00,project_cost,2026-07-12,project_cost_payment",
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
            self.assertEqual([row["period_date"] for row in forecast_rows], ["2026-07-09", "2026-07-10", "2026-07-11", "2026-07-12"])
            self.assertEqual([row["known_inflow"] for row in forecast_rows], ["500.00", "0.00", "0.00", "0.00"])
            self.assertEqual([row["known_outflow"] for row in forecast_rows], ["0.00", "800.00", "13000.00", "2700.00"])
            self.assertEqual([row["projected_bank_cash"] for row in forecast_rows], ["9500.00", "8700.00", "-4300.00", "-7000.00"])
            self.assertEqual([row["funding_gap"] for row in forecast_rows], ["0.00", "0.00", "4300.00", "7000.00"])
            self.assertTrue(all(row["forecast_basis"] == "known_due_date_structured_csv" for row in forecast_rows))
            self.assertTrue(all(row["review_status"] == "structured_csv_forecast_pending_review" for row in forecast_rows))
            self.assertEqual(forecast_rows[3]["risk_types"], "project_cost_payment")

            with (run_dir / "tax_loan_risk.csv").open(encoding="utf-8-sig", newline="") as f:
                risk_rows = list(csv.DictReader(f))
            self.assertIn("project_cost_payment", [row["risk_type"] for row in risk_rows])

            cross_review = json.loads((run_dir / "cross_review.json").read_text(encoding="utf-8"))
            self.assertFalse(cross_review["management_conclusion_allowed"])
            self.assertEqual(cross_review["forecast_row_count"], 4)

            workbook_path = run_dir / "资金与税费管理母版_funding_forecast_test.xlsx"
            with zipfile.ZipFile(workbook_path) as workbook:
                self.assertEqual(xlsx_cell_text(workbook, "xl/worksheets/sheet2.xml", "A4"), "预测/到期日")
                self.assertEqual(xlsx_cell_text(workbook, "xl/worksheets/sheet2.xml", "A5"), "2026-07-09")
                self.assertEqual(xlsx_cell_text(workbook, "xl/worksheets/sheet2.xml", "B5"), "500.00")
                self.assertEqual(xlsx_cell_text(workbook, "xl/worksheets/sheet2.xml", "D7"), "-4300.00")
                self.assertEqual(xlsx_cell_text(workbook, "xl/worksheets/sheet2.xml", "E7"), "4300.00")
                self.assertEqual(xlsx_cell_text(workbook, "xl/worksheets/sheet2.xml", "F8"), "project_cost_payment")
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
                "WQ-HOMEPAGE-CHART-SEMANTICS",
                "WQ-FORMULA-ERRORS",
                "WQ-VISIBLE-SENSITIVE-TEXT",
            ):
                self.assertEqual(checks[check_id]["status"], "PASS", check_id)
            self.assertIn("最近15天资金余额折线图:15,15,15", checks["WQ-HOMEPAGE-CHART-SEMANTICS"]["details"])
            self.assertIn("最近30天资金余额折线图:30,30,30", checks["WQ-HOMEPAGE-CHART-SEMANTICS"]["details"])
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

    def test_owner_decision_manifest_install_blocks_missing_required_values(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir) / "repo"
            run_id = "owner_manifest_missing_values"
            run_dir = repo_root / "KMFA/metadata/fund_weekly_analysis/private_runtime/runs" / run_id
            run_dir.mkdir(parents=True)
            draft = {
                "decision_manifest_version": "1",
                "run_id": run_id,
                "decision_scope": "ocr_fact_candidate_owner_worklist_validation_only",
                "draft_status": "owner_decision_correction_manifest_draft",
                "generated_from": "ocr_fact_owner_decision_correction_queue.csv",
                "source_artifact": "ocr_fact_candidate_owner_worklist.csv",
                "output_decision_manifest_relative_path": (
                    f"KMFA/metadata/fund_weekly_analysis/private_runtime/"
                    f"ocr_fact_candidate_owner_decisions/{run_id}.json"
                ),
                "financial_fact_promotion_allowed": False,
                "fund_ledger_write_allowed": False,
                "management_conclusion_allowed": False,
                "owner_decisions": [
                    {
                        "fact_candidate_id": f"OCRFACT-{run_id}-00001",
                        "candidate_metric": "deposit_release",
                        "owner_authorization_decision": "approve_for_review_authorization",
                        "owner_corrected_company": "",
                        "owner_corrected_bank": "",
                        "required_owner_fields": "owner_corrected_company,owner_corrected_bank",
                        "owner_note": "owner values intentionally missing",
                    }
                ],
            }
            (run_dir / "ocr_fact_owner_decision_correction_draft.json").write_text(
                json.dumps(draft, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(SKILL_ROOT / "tools" / "install_owner_decision_manifest.py"),
                    "--repo-root",
                    str(repo_root),
                    "--run-id",
                    run_id,
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 3)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["status"], "BLOCKED_OWNER_VALUES_MISSING")
            self.assertEqual(payload["missing_owner_values"], ["owner_corrected_company", "owner_corrected_bank"])
            self.assertFalse(
                (
                    repo_root / "KMFA/metadata/fund_weekly_analysis/private_runtime/"
                    f"ocr_fact_candidate_owner_decisions/{run_id}.json"
                ).exists()
            )

    def test_owner_decision_manifest_install_accepts_candidate_template_as_pending_review(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir) / "repo"
            run_id = "owner_manifest_candidate_template"
            run_dir = repo_root / "KMFA/metadata/fund_weekly_analysis/private_runtime/runs" / run_id
            run_dir.mkdir(parents=True)
            template = {
                "decision_manifest_version": "1",
                "run_id": run_id,
                "decision_scope": "ocr_fact_candidate_owner_worklist_validation_only",
                "template_status": "owner_decision_required",
                "template_generated_from": "ocr_fact_candidate_owner_worklist.csv",
                "source_artifact": "ocr_fact_candidate_owner_worklist.csv",
                "output_decision_manifest_relative_path": (
                    f"KMFA/metadata/fund_weekly_analysis/private_runtime/"
                    f"ocr_fact_candidate_owner_decisions/{run_id}.json"
                ),
                "allowed_owner_authorization_decisions": [
                    "pending_owner_review",
                    "needs_correction",
                    "reject_candidate",
                    "approve_for_review_authorization",
                ],
                "financial_fact_promotion_allowed": False,
                "fund_ledger_write_allowed": False,
                "management_conclusion_allowed": False,
                "owner_decisions": [
                    {
                        "owner_worklist_id": f"OCROWNERWORK-{run_id}-00001",
                        "ocr_fact_evidence_review_queue_id": f"OCREVIDQUEUE-{run_id}-00001",
                        "fact_candidate_id": f"OCRFACT-{run_id}-00001",
                        "candidate_metric": "tax_payment",
                        "business_date": "2026-05-11",
                        "company": "",
                        "bank": "",
                        "account_alias": "",
                        "amount": "4381.02",
                        "currency": "CNY",
                        "owner_authorization_decision": "pending_owner_review",
                        "owner_corrected_company": "",
                        "owner_corrected_bank": "",
                        "owner_note": "",
                    }
                ],
            }
            template_path = run_dir / "ocr_fact_candidate_owner_decision_template.json"
            template_path.write_text(json.dumps(template, ensure_ascii=False, indent=2), encoding="utf-8")

            result = subprocess.run(
                [
                    sys.executable,
                    str(SKILL_ROOT / "tools" / "install_owner_decision_manifest.py"),
                    "--repo-root",
                    str(repo_root),
                    "--run-id",
                    run_id,
                    "--draft-path",
                    str(template_path),
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 3, result.stdout)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["status"], "BLOCKED_OWNER_DECISION_NOT_APPROVED")
            self.assertEqual(payload["not_approved_fact_candidate_ids"], [f"OCRFACT-{run_id}-00001"])
            self.assertFalse(
                (
                    repo_root / "KMFA/metadata/fund_weekly_analysis/private_runtime/"
                    f"ocr_fact_candidate_owner_decisions/{run_id}.json"
                ).exists()
            )

    def test_owner_decision_manifest_install_defaults_to_candidate_template_when_correction_draft_empty(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir) / "repo"
            run_id = "owner_manifest_default_candidate_template"
            run_dir = repo_root / "KMFA/metadata/fund_weekly_analysis/private_runtime/runs" / run_id
            run_dir.mkdir(parents=True)
            output_relative_path = (
                f"KMFA/metadata/fund_weekly_analysis/private_runtime/"
                f"ocr_fact_candidate_owner_decisions/{run_id}.json"
            )
            empty_correction_draft = {
                "decision_manifest_version": "1",
                "run_id": run_id,
                "decision_scope": "ocr_fact_candidate_owner_worklist_validation_only",
                "draft_status": "owner_decision_correction_manifest_draft",
                "generated_from": "ocr_fact_owner_decision_correction_queue.csv",
                "source_artifact": "ocr_fact_candidate_owner_worklist.csv",
                "output_decision_manifest_relative_path": output_relative_path,
                "financial_fact_promotion_allowed": False,
                "fund_ledger_write_allowed": False,
                "management_conclusion_allowed": False,
                "owner_decisions": [],
            }
            candidate_template = {
                "decision_manifest_version": "1",
                "run_id": run_id,
                "decision_scope": "ocr_fact_candidate_owner_worklist_validation_only",
                "template_status": "owner_decision_required",
                "template_generated_from": "ocr_fact_candidate_owner_worklist.csv",
                "source_artifact": "ocr_fact_candidate_owner_worklist.csv",
                "output_decision_manifest_relative_path": output_relative_path,
                "financial_fact_promotion_allowed": False,
                "fund_ledger_write_allowed": False,
                "management_conclusion_allowed": False,
                "owner_decisions": [
                    {
                        "fact_candidate_id": f"OCRFACT-{run_id}-00001",
                        "candidate_metric": "tax_payment",
                        "owner_authorization_decision": "pending_owner_review",
                        "owner_corrected_company": "",
                        "owner_corrected_bank": "",
                        "owner_note": "",
                    }
                ],
            }
            (run_dir / "ocr_fact_owner_decision_correction_draft.json").write_text(
                json.dumps(empty_correction_draft, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            (run_dir / "ocr_fact_candidate_owner_decision_template.json").write_text(
                json.dumps(candidate_template, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(SKILL_ROOT / "tools" / "install_owner_decision_manifest.py"),
                    "--repo-root",
                    str(repo_root),
                    "--run-id",
                    run_id,
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 3, result.stdout)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["status"], "BLOCKED_OWNER_DECISION_NOT_APPROVED")
            self.assertIn("ocr_fact_candidate_owner_decision_template.json", payload["draft_path"])
            self.assertEqual(payload["owner_decision_count"], 1)

    def test_owner_decision_manifest_install_dry_run_does_not_write(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir) / "repo"
            run_id = "owner_manifest_dry_run"
            run_dir = repo_root / "KMFA/metadata/fund_weekly_analysis/private_runtime/runs" / run_id
            run_dir.mkdir(parents=True)
            draft = {
                "decision_manifest_version": "1",
                "run_id": run_id,
                "decision_scope": "ocr_fact_candidate_owner_worklist_validation_only",
                "draft_status": "owner_decision_correction_manifest_draft",
                "generated_from": "ocr_fact_owner_decision_correction_queue.csv",
                "source_artifact": "ocr_fact_candidate_owner_worklist.csv",
                "output_decision_manifest_relative_path": (
                    f"KMFA/metadata/fund_weekly_analysis/private_runtime/"
                    f"ocr_fact_candidate_owner_decisions/{run_id}.json"
                ),
                "financial_fact_promotion_allowed": False,
                "fund_ledger_write_allowed": False,
                "management_conclusion_allowed": False,
                "owner_decisions": [
                    {
                        "fact_candidate_id": f"OCRFACT-{run_id}-00001",
                        "candidate_metric": "deposit_release",
                        "owner_authorization_decision": "approve_for_review_authorization",
                        "owner_corrected_company": "武汉开明",
                        "owner_corrected_bank": "湖北中行",
                        "required_owner_fields": "owner_corrected_company,owner_corrected_bank",
                        "owner_note": "owner reviewed values",
                    }
                ],
            }
            (run_dir / "ocr_fact_owner_decision_correction_draft.json").write_text(
                json.dumps(draft, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(SKILL_ROOT / "tools" / "install_owner_decision_manifest.py"),
                    "--repo-root",
                    str(repo_root),
                    "--run-id",
                    run_id,
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["status"], "READY_DRY_RUN")
            self.assertFalse(payload["apply_performed"])
            self.assertEqual(payload["owner_decision_count"], 1)
            self.assertFalse(
                (
                    repo_root / "KMFA/metadata/fund_weekly_analysis/private_runtime/"
                    f"ocr_fact_candidate_owner_decisions/{run_id}.json"
                ).exists()
            )

    def test_owner_decision_manifest_install_accepts_reviewed_csv_dry_run(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir) / "repo"
            run_id = "owner_manifest_csv_dry_run"
            run_dir = repo_root / "KMFA/metadata/fund_weekly_analysis/private_runtime/runs" / run_id
            run_dir.mkdir(parents=True)
            csv_path = run_dir / "owner_reviewed_decisions.csv"
            with csv_path.open("w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=[
                    "fact_candidate_id",
                    "candidate_metric",
                    "owner_authorization_decision",
                    "owner_corrected_company",
                    "owner_corrected_bank",
                    "required_owner_fields",
                    "owner_note",
                ])
                writer.writeheader()
                writer.writerow({
                    "fact_candidate_id": f"OCRFACT-{run_id}-00001",
                    "candidate_metric": "deposit_release",
                    "owner_authorization_decision": "approve_for_review_authorization",
                    "owner_corrected_company": "武汉开明",
                    "owner_corrected_bank": "湖北中行",
                    "required_owner_fields": "owner_corrected_company,owner_corrected_bank",
                    "owner_note": "owner reviewed from spreadsheet csv",
                })

            result = subprocess.run(
                [
                    sys.executable,
                    str(SKILL_ROOT / "tools" / "install_owner_decision_manifest.py"),
                    "--repo-root",
                    str(repo_root),
                    "--run-id",
                    run_id,
                    "--draft-csv-path",
                    str(csv_path),
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["status"], "READY_DRY_RUN")
            self.assertFalse(payload["apply_performed"])
            self.assertEqual(payload["owner_decision_count"], 1)
            self.assertEqual(payload["draft_format"], "csv")
            self.assertFalse(payload["fund_ledger_write_allowed"])
            self.assertFalse(payload["management_conclusion_allowed"])
            self.assertFalse(
                (
                    repo_root / "KMFA/metadata/fund_weekly_analysis/private_runtime/"
                    f"ocr_fact_candidate_owner_decisions/{run_id}.json"
                ).exists()
            )

    def test_owner_decision_review_csv_export_selects_small_no_write_batch(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir) / "repo"
            run_id = "owner_review_export"
            run_dir = repo_root / "KMFA/metadata/fund_weekly_analysis/private_runtime/runs" / run_id
            run_dir.mkdir(parents=True)
            worklist_path = run_dir / "ocr_fact_candidate_owner_worklist.csv"
            with worklist_path.open("w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=[
                    "owner_worklist_id",
                    "ocr_fact_evidence_review_queue_id",
                    "fact_candidate_id",
                    "candidate_metric",
                    "source_evidence_id",
                    "source_ocr_text_relative_path",
                    "business_date",
                    "company",
                    "bank",
                    "account_alias",
                    "amount",
                    "currency",
                    "proposed_amount_role",
                    "proposed_liquidity_tier",
                    "proposed_flow_type",
                    "authorization_validation_status",
                    "staging_preview_status",
                    "owner_authorization_decision",
                    "owner_corrected_company",
                    "owner_corrected_bank",
                    "owner_note",
                    "authorization_manifest_relative_path",
                    "authorization_scope",
                    "fund_ledger_write_allowed",
                    "financial_fact_promoted",
                    "management_conclusion_allowed",
                    "recommended_owner_action",
                ])
                writer.writeheader()
                for idx, metric in enumerate(["deposit_release", "bank_deposit", "tax_payment"], 1):
                    writer.writerow({
                        "owner_worklist_id": f"OCROWNERWORK-{run_id}-{idx:05d}",
                        "ocr_fact_evidence_review_queue_id": f"OCREVIDQUEUE-{run_id}-{idx:05d}",
                        "fact_candidate_id": f"OCRFACT-{run_id}-{idx:05d}",
                        "candidate_metric": metric,
                        "source_evidence_id": f"FW{run_id}-{idx:05d}",
                        "source_ocr_text_relative_path": f"private/OCRGEN-{idx:05d}.ocr.txt",
                        "business_date": f"2026-06-{idx:02d}",
                        "company": "",
                        "bank": "",
                        "account_alias": "",
                        "amount": f"{idx}.00",
                        "currency": "CNY",
                        "proposed_amount_role": "amount",
                        "proposed_liquidity_tier": "T0_BANK_CASH",
                        "proposed_flow_type": "inflow",
                        "authorization_validation_status": "missing_authorization_manifest",
                        "staging_preview_status": "blocked_missing_operator_authorization",
                        "owner_authorization_decision": "pending_owner_review",
                        "owner_corrected_company": "",
                        "owner_corrected_bank": "",
                        "owner_note": "",
                        "authorization_manifest_relative_path": f"KMFA/metadata/fund_weekly_analysis/private_runtime/ocr_fact_review_authorizations/{run_id}.json",
                        "authorization_scope": "ocr_financial_fact_review_validation_only",
                        "fund_ledger_write_allowed": "false",
                        "financial_fact_promoted": "false",
                        "management_conclusion_allowed": "false",
                        "recommended_owner_action": "Review candidate",
                    })

            result = subprocess.run(
                [
                    sys.executable,
                    str(SKILL_ROOT / "tools" / "export_owner_decision_review_csv.py"),
                    "--repo-root",
                    str(repo_root),
                    "--run-id",
                    run_id,
                    "--metrics",
                    "deposit_release,bank_deposit",
                    "--limit-per-metric",
                    "1",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["status"], "READY_REVIEW_CSV")
            self.assertEqual(payload["selected_count"], 2)
            self.assertFalse(payload["apply_performed"])
            self.assertFalse(payload["fund_ledger_write_allowed"])
            self.assertFalse(payload["management_conclusion_allowed"])

            output_path = repo_root / payload["output_relative_path"]
            self.assertTrue(output_path.exists())
            with output_path.open(encoding="utf-8-sig", newline="") as f:
                rows = list(csv.DictReader(f))
            self.assertEqual([row["candidate_metric"] for row in rows], ["deposit_release", "bank_deposit"])
            self.assertEqual([row["owner_authorization_decision"] for row in rows], [
                "pending_owner_review",
                "pending_owner_review",
            ])
            self.assertTrue(all(row["required_owner_fields"] == "owner_corrected_company,owner_corrected_bank" for row in rows))
            self.assertTrue(all(row["fund_ledger_write_allowed"] == "false" for row in rows))
            self.assertTrue(all(row["financial_fact_promoted"] == "false" for row in rows))
            self.assertTrue(all(row["management_conclusion_allowed"] == "false" for row in rows))
            self.assertFalse(
                (
                    repo_root / "KMFA/metadata/fund_weekly_analysis/private_runtime/"
                    f"ocr_fact_candidate_owner_decisions/{run_id}.json"
                ).exists()
            )

    def test_owner_decision_review_export_can_emit_native_xlsx_no_write_packet(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir) / "repo"
            run_id = "owner_review_xlsx_export"
            run_dir = repo_root / "KMFA/metadata/fund_weekly_analysis/private_runtime/runs" / run_id
            run_dir.mkdir(parents=True)
            sidecar_dir = run_dir / "private"
            sidecar_dir.mkdir(parents=True)
            (sidecar_dir / "OCRGEN-00001.ocr.txt").write_text(
                "\n".join(
                    [f"无关页眉{i}" for i in range(80)]
                    + ["真实OCR公司A", "湖北中行", "付款金额 1.00"]
                ),
                encoding="utf-8",
            )
            worklist_path = run_dir / "ocr_fact_candidate_owner_worklist.csv"
            with worklist_path.open("w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=[
                    "owner_worklist_id",
                    "ocr_fact_evidence_review_queue_id",
                    "fact_candidate_id",
                    "candidate_metric",
                    "source_evidence_id",
                    "source_ocr_text_relative_path",
                    "business_date",
                    "company",
                    "bank",
                    "account_alias",
                    "amount",
                    "currency",
                    "proposed_amount_role",
                    "proposed_liquidity_tier",
                    "proposed_flow_type",
                    "fund_ledger_write_allowed",
                    "financial_fact_promoted",
                    "management_conclusion_allowed",
                    "recommended_owner_action",
                ])
                writer.writeheader()
                for idx, metric in enumerate(["deposit_release", "bank_deposit"], 1):
                    writer.writerow({
                        "owner_worklist_id": f"OCROWNERWORK-{run_id}-{idx:05d}",
                        "ocr_fact_evidence_review_queue_id": f"OCREVIDQUEUE-{run_id}-{idx:05d}",
                        "fact_candidate_id": f"OCRFACT-{run_id}-{idx:05d}",
                        "candidate_metric": metric,
                        "source_evidence_id": f"FW{run_id}-{idx:05d}",
                        "source_ocr_text_relative_path": f"private/OCRGEN-{idx:05d}.ocr.txt",
                        "business_date": f"2026-06-{idx:02d}",
                        "company": "",
                        "bank": "",
                        "account_alias": "",
                        "amount": f"{idx}.00",
                        "currency": "CNY",
                        "proposed_amount_role": "amount",
                        "proposed_liquidity_tier": "T0_BANK_CASH",
                        "proposed_flow_type": "inflow",
                        "fund_ledger_write_allowed": "false",
                        "financial_fact_promoted": "false",
                        "management_conclusion_allowed": "false",
                        "recommended_owner_action": "Review candidate",
                    })

            result = subprocess.run(
                [
                    sys.executable,
                    str(SKILL_ROOT / "tools" / "export_owner_decision_review_csv.py"),
                    "--repo-root",
                    str(repo_root),
                    "--run-id",
                    run_id,
                    "--metrics",
                    "deposit_release,bank_deposit",
                    "--limit-per-metric",
                    "1",
                    "--xlsx",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["status"], "READY_REVIEW_CSV")
            self.assertEqual(payload["selected_count"], 2)
            self.assertIn("xlsx_output_relative_path", payload)
            self.assertFalse(payload["fund_ledger_write_allowed"])
            self.assertFalse(payload["financial_fact_promoted"])
            self.assertFalse(payload["management_conclusion_allowed"])

            csv_path = repo_root / payload["output_relative_path"]
            with csv_path.open(encoding="utf-8-sig", newline="") as f:
                review_rows = list(csv.DictReader(f))
            self.assertIn("source_ocr_text_excerpt", review_rows[0])
            self.assertIn("source_ocr_excerpt_focus_status", review_rows[0])
            self.assertIn("source_ocr_excerpt_line_range", review_rows[0])
            self.assertIn("source_ocr_excerpt_focus_line_number", review_rows[0])
            self.assertIn("source_ocr_excerpt_match_value", review_rows[0])
            self.assertIn("真实OCR公司A", review_rows[0]["source_ocr_text_excerpt"])
            self.assertIn("付款金额 1.00", review_rows[0]["source_ocr_text_excerpt"])
            self.assertNotIn("无关页眉0", review_rows[0]["source_ocr_text_excerpt"])
            self.assertEqual(review_rows[0]["source_ocr_excerpt_focus_status"], "focused_amount")
            self.assertEqual(review_rows[0]["source_ocr_excerpt_line_range"], "81-83")
            self.assertEqual(review_rows[0]["source_ocr_excerpt_focus_line_number"], "83")
            self.assertEqual(review_rows[0]["source_ocr_excerpt_match_value"], "1.00")
            self.assertEqual(review_rows[1]["source_ocr_excerpt_focus_status"], "missing_ocr_sidecar")
            self.assertEqual(review_rows[1]["source_ocr_excerpt_line_range"], "")
            self.assertEqual(review_rows[1]["source_ocr_excerpt_focus_line_number"], "")
            self.assertEqual(review_rows[1]["source_ocr_excerpt_match_value"], "")

            xlsx_path = repo_root / payload["xlsx_output_relative_path"]
            self.assertTrue(xlsx_path.exists())
            with zipfile.ZipFile(xlsx_path) as workbook:
                names = set(workbook.namelist())
                self.assertIn("xl/workbook.xml", names)
                self.assertIn("xl/worksheets/sheet1.xml", names)
                self.assertIn("xl/worksheets/sheet2.xml", names)
                self.assertIn("xl/sharedStrings.xml", names)
                self.assertIn("xl/styles.xml", names)
                workbook_xml = workbook.read("xl/workbook.xml").decode("utf-8")
                sheet_xml = workbook.read("xl/worksheets/sheet1.xml").decode("utf-8")
                summary_sheet_xml = workbook.read("xl/worksheets/sheet2.xml").decode("utf-8")
                shared_xml = workbook.read("xl/sharedStrings.xml").decode("utf-8")
                self.assertIn("Owner Review", workbook_xml)
                self.assertIn("Review Summary", workbook_xml)
                self.assertIn("owner_authorization_decision", shared_xml)
                self.assertIn("owner_corrected_company", shared_xml)
                self.assertIn("owner_corrected_bank", shared_xml)
                self.assertIn("owner_review_completion_status", shared_xml)
                self.assertIn("missing_owner_fields_current", shared_xml)
                self.assertIn("source_ocr_text_excerpt", shared_xml)
                self.assertIn("source_ocr_excerpt_focus_status", shared_xml)
                self.assertIn("source_ocr_excerpt_line_range", shared_xml)
                self.assertIn("source_ocr_excerpt_focus_line_number", shared_xml)
                self.assertIn("source_ocr_excerpt_match_value", shared_xml)
                self.assertIn("真实OCR公司A", shared_xml)
                self.assertIn("focused_amount", shared_xml)
                self.assertIn("missing_ocr_sidecar", shared_xml)
                self.assertIn("81-83", shared_xml)
                self.assertIn("summary_scope", shared_xml)
                self.assertIn("candidate_metric", shared_xml)
                self.assertIn("source_ocr_excerpt_focus_status", shared_xml)
                self.assertIn("all", shared_xml)
                self.assertIn("Fill required owner fields before intake dry-run.", shared_xml)
                self.assertIn("blocked_missing_owner_values", sheet_xml)
                self.assertIn('<sheetProtection sheet="1" objects="1" scenarios="1"', sheet_xml)
                self.assertIn('<c r="V2" t="s" s="2">', sheet_xml)
                self.assertIn('<c r="W2" t="s" s="2">', sheet_xml)
                self.assertIn('<c r="X2" t="s" s="2">', sheet_xml)
                self.assertIn('<c r="AB2" t="s" s="2">', sheet_xml)
                self.assertIn('<autoFilter ref="A1:L6"', summary_sheet_xml)
                self.assertIn('<sheetProtection sheet="1" objects="1" scenarios="1"', summary_sheet_xml)
                self.assertIn("pending_owner_review", shared_xml)
                self.assertIn("fund_ledger_write_allowed", shared_xml)
                self.assertIn("management_conclusion_allowed", shared_xml)
                self.assertIn("<dataValidations", sheet_xml)
                self.assertIn("approve_for_review_authorization", sheet_xml)
                self.assertIn("frozenSplit", sheet_xml)
                sheet_root = ET.fromstring(sheet_xml)
                ns = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
                status_formula = sheet_root.find(".//x:c[@r='Y2']/x:f", ns)
                missing_formula = sheet_root.find(".//x:c[@r='Z2']/x:f", ns)
                self.assertIsNotNone(status_formula)
                self.assertIsNotNone(missing_formula)
                self.assertIn("V2", status_formula.text or "")
                self.assertIn("W2", status_formula.text or "")
                self.assertIn("X2", status_formula.text or "")
                self.assertIn("AA2", status_formula.text or "")
                self.assertIn("W2", missing_formula.text or "")
                self.assertIn("X2", missing_formula.text or "")
                self.assertIn("AA2", missing_formula.text or "")
            self.assertFalse(
                (
                    repo_root / "KMFA/metadata/fund_weekly_analysis/private_runtime/"
                    f"ocr_fact_candidate_owner_decisions/{run_id}.json"
                ).exists()
            )

    def test_owner_decision_manifest_install_apply_requires_ack_and_writes_validation_only_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir) / "repo"
            run_id = "owner_manifest_apply"
            run_dir = repo_root / "KMFA/metadata/fund_weekly_analysis/private_runtime/runs" / run_id
            run_dir.mkdir(parents=True)
            draft = {
                "decision_manifest_version": "1",
                "run_id": run_id,
                "decision_scope": "ocr_fact_candidate_owner_worklist_validation_only",
                "draft_status": "owner_decision_correction_manifest_draft",
                "generated_from": "ocr_fact_owner_decision_correction_queue.csv",
                "source_artifact": "ocr_fact_candidate_owner_worklist.csv",
                "output_decision_manifest_relative_path": (
                    f"KMFA/metadata/fund_weekly_analysis/private_runtime/"
                    f"ocr_fact_candidate_owner_decisions/{run_id}.json"
                ),
                "financial_fact_promotion_allowed": False,
                "fund_ledger_write_allowed": False,
                "management_conclusion_allowed": False,
                "owner_decisions": [
                    {
                        "fact_candidate_id": f"OCRFACT-{run_id}-00001",
                        "candidate_metric": "deposit_release",
                        "owner_authorization_decision": "approve_for_review_authorization",
                        "owner_corrected_company": "武汉开明",
                        "owner_corrected_bank": "湖北中行",
                        "required_owner_fields": "owner_corrected_company,owner_corrected_bank",
                        "owner_note": "owner reviewed values",
                    }
                ],
            }
            (run_dir / "ocr_fact_owner_decision_correction_draft.json").write_text(
                json.dumps(draft, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

            missing_ack = subprocess.run(
                [
                    sys.executable,
                    str(SKILL_ROOT / "tools" / "install_owner_decision_manifest.py"),
                    "--repo-root",
                    str(repo_root),
                    "--run-id",
                    run_id,
                    "--apply",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(missing_ack.returncode, 2)
            self.assertEqual(json.loads(missing_ack.stdout)["status"], "ACK_REQUIRED")

            apply_run = subprocess.run(
                [
                    sys.executable,
                    str(SKILL_ROOT / "tools" / "install_owner_decision_manifest.py"),
                    "--repo-root",
                    str(repo_root),
                    "--run-id",
                    run_id,
                    "--apply",
                    "--acknowledge-owner-reviewed-values",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(apply_run.returncode, 0, apply_run.stderr)
            payload = json.loads(apply_run.stdout)
            self.assertEqual(payload["status"], "APPLIED")
            self.assertTrue(payload["apply_performed"])
            manifest_path = (
                repo_root / "KMFA/metadata/fund_weekly_analysis/private_runtime/"
                f"ocr_fact_candidate_owner_decisions/{run_id}.json"
            )
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(manifest["decision_manifest_version"], "1")
            self.assertEqual(manifest["run_id"], run_id)
            self.assertEqual(manifest["decision_scope"], "ocr_fact_candidate_owner_worklist_validation_only")
            self.assertEqual(manifest["source_artifact"], "ocr_fact_candidate_owner_worklist.csv")
            self.assertFalse(manifest["financial_fact_promotion_allowed"])
            self.assertFalse(manifest["fund_ledger_write_allowed"])
            self.assertFalse(manifest["management_conclusion_allowed"])
            self.assertEqual(manifest["owner_decisions"][0]["owner_corrected_company"], "武汉开明")
            self.assertEqual(manifest["owner_decisions"][0]["owner_corrected_bank"], "湖北中行")

    def test_owner_decision_manifest_intake_accepts_reviewed_xlsx_dry_run_no_write(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir) / "repo"
            run_id = "owner_manifest_xlsx_dry_run"
            run_dir = repo_root / "KMFA/metadata/fund_weekly_analysis/private_runtime/runs" / run_id
            run_dir.mkdir(parents=True)
            xlsx_path = run_dir / "reviewed_owner_decisions.xlsx"
            export_module = load_owner_review_export_module()
            export_module.write_xlsx(
                xlsx_path,
                [
                    {
                        "owner_worklist_id": f"OCROWNERWORK-{run_id}-00001",
                        "ocr_fact_evidence_review_queue_id": f"OCREVIDQUEUE-{run_id}-00001",
                        "fact_candidate_id": f"OCRFACT-{run_id}-00001",
                        "candidate_metric": "bank_deposit",
                        "source_evidence_id": f"FW{run_id}-00001",
                        "source_ocr_text_relative_path": "private/OCRGEN-00001.ocr.txt",
                        "source_ocr_text_excerpt": "武汉开明 | 招商银行 | 银行存款 123.45",
                        "source_ocr_excerpt_focus_status": "focused_amount",
                        "source_ocr_excerpt_line_range": "10-12",
                        "source_ocr_excerpt_focus_line_number": "12",
                        "source_ocr_excerpt_match_value": "123.45",
                        "business_date": "2026-07-08",
                        "company": "",
                        "bank": "",
                        "account_alias": "",
                        "amount": "123.45",
                        "currency": "CNY",
                        "proposed_amount_role": "ending_balance",
                        "proposed_liquidity_tier": "T0_BANK_CASH",
                        "proposed_flow_type": "balance",
                        "fund_ledger_write_allowed": "false",
                        "financial_fact_promoted": "false",
                        "management_conclusion_allowed": "false",
                        "required_owner_fields": "owner_corrected_company,owner_corrected_bank",
                        "owner_authorization_decision": "approve_for_review_authorization",
                        "owner_corrected_company": "武汉开明",
                        "owner_corrected_bank": "湖北中行",
                        "owner_note": "owner reviewed in xlsx",
                        "review_packet_status": "pending_owner_review",
                    }
                ],
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(SKILL_ROOT / "tools" / "install_owner_decision_manifest.py"),
                    "--repo-root",
                    str(repo_root),
                    "--run-id",
                    run_id,
                    "--draft-xlsx-path",
                    str(xlsx_path),
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["status"], "READY_DRY_RUN")
            self.assertEqual(payload["draft_format"], "xlsx")
            self.assertEqual(payload["owner_decision_count"], 1)
            self.assertFalse(payload["apply_performed"])
            self.assertFalse(payload["financial_fact_promotion_allowed"])
            self.assertFalse(payload["fund_ledger_write_allowed"])
            self.assertFalse(payload["management_conclusion_allowed"])
            self.assertFalse(
                (
                    repo_root / "KMFA/metadata/fund_weekly_analysis/private_runtime/"
                    f"ocr_fact_candidate_owner_decisions/{run_id}.json"
                ).exists()
            )

    def test_owner_decision_manifest_xlsx_intake_writes_row_validation_report_no_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir) / "repo"
            run_id = "owner_manifest_xlsx_validation_report"
            run_dir = repo_root / "KMFA/metadata/fund_weekly_analysis/private_runtime/runs" / run_id
            run_dir.mkdir(parents=True)
            xlsx_path = run_dir / "reviewed_owner_decisions.xlsx"
            export_module = load_owner_review_export_module()
            export_module.write_xlsx(
                xlsx_path,
                [
                    {
                        "owner_worklist_id": f"OCROWNERWORK-{run_id}-00001",
                        "ocr_fact_evidence_review_queue_id": f"OCREVIDQUEUE-{run_id}-00001",
                        "fact_candidate_id": f"OCRFACT-{run_id}-00001",
                        "candidate_metric": "bank_deposit",
                        "source_evidence_id": f"FW{run_id}-00001",
                        "source_ocr_text_relative_path": "private/OCRGEN-00001.ocr.txt",
                        "source_ocr_text_excerpt": "武汉开明 | 招商银行 | 银行存款 123.45",
                        "source_ocr_excerpt_focus_status": "focused_amount",
                        "source_ocr_excerpt_line_range": "10-12",
                        "source_ocr_excerpt_focus_line_number": "12",
                        "source_ocr_excerpt_match_value": "123.45",
                        "business_date": "2026-07-08",
                        "company": "",
                        "bank": "",
                        "account_alias": "",
                        "amount": "123.45",
                        "currency": "CNY",
                        "proposed_amount_role": "ending_balance",
                        "proposed_liquidity_tier": "T0_BANK_CASH",
                        "proposed_flow_type": "balance",
                        "fund_ledger_write_allowed": "false",
                        "financial_fact_promoted": "false",
                        "management_conclusion_allowed": "false",
                        "required_owner_fields": "owner_corrected_company,owner_corrected_bank",
                        "owner_authorization_decision": "approve_for_review_authorization",
                        "owner_corrected_company": "",
                        "owner_corrected_bank": "",
                        "owner_note": "missing owner values",
                        "review_packet_status": "pending_owner_review",
                    }
                ],
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(SKILL_ROOT / "tools" / "install_owner_decision_manifest.py"),
                    "--repo-root",
                    str(repo_root),
                    "--run-id",
                    run_id,
                    "--draft-xlsx-path",
                    str(xlsx_path),
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 3, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["status"], "BLOCKED_OWNER_VALUES_MISSING")
            self.assertEqual(payload["draft_format"], "xlsx")
            report_path = repo_root / payload["validation_report_relative_path"]
            summary_path = repo_root / payload["validation_summary_relative_path"]
            self.assertTrue(report_path.exists())
            self.assertTrue(summary_path.exists())
            with report_path.open(encoding="utf-8-sig", newline="") as f:
                rows = list(csv.DictReader(f))
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["fact_candidate_id"], f"OCRFACT-{run_id}-00001")
            self.assertEqual(rows[0]["input_row_number"], "2")
            self.assertEqual(rows[0]["decision_validation_status"], "blocked_missing_owner_values")
            self.assertEqual(rows[0]["source_evidence_id"], f"FW{run_id}-00001")
            self.assertEqual(rows[0]["source_ocr_text_relative_path"], "private/OCRGEN-00001.ocr.txt")
            self.assertEqual(rows[0]["source_ocr_text_excerpt"], "武汉开明 | 招商银行 | 银行存款 123.45")
            self.assertEqual(rows[0]["source_ocr_excerpt_focus_status"], "focused_amount")
            self.assertEqual(rows[0]["source_ocr_excerpt_line_range"], "10-12")
            self.assertEqual(rows[0]["source_ocr_excerpt_focus_line_number"], "12")
            self.assertEqual(rows[0]["source_ocr_excerpt_match_value"], "123.45")
            self.assertEqual(rows[0]["business_date"], "2026-07-08")
            self.assertEqual(rows[0]["amount"], "123.45")
            self.assertEqual(rows[0]["currency"], "CNY")
            self.assertEqual(rows[0]["missing_owner_fields"], "owner_corrected_company,owner_corrected_bank")
            self.assertEqual(rows[0]["owner_decision_manifest_write_allowed"], "false")
            self.assertEqual(rows[0]["fund_ledger_write_allowed"], "false")
            self.assertEqual(rows[0]["financial_fact_promoted"], "false")
            self.assertEqual(rows[0]["management_conclusion_allowed"], "false")
            with summary_path.open(encoding="utf-8-sig", newline="") as f:
                summary_rows = list(csv.DictReader(f))
            self.assertEqual(len(summary_rows), 3)
            self.assertEqual(summary_rows[0]["summary_scope"], "all")
            self.assertEqual(summary_rows[0]["summary_key"], "all")
            self.assertEqual(summary_rows[0]["candidate_count"], "1")
            self.assertEqual(summary_rows[0]["blocking_count"], "1")
            self.assertEqual(summary_rows[0]["ready_count"], "0")
            self.assertEqual(summary_rows[0]["missing_owner_fields"], "owner_corrected_company,owner_corrected_bank")
            self.assertEqual(summary_rows[0]["owner_decision_manifest_write_allowed"], "false")
            self.assertEqual(summary_rows[1]["summary_scope"], "candidate_metric")
            self.assertEqual(summary_rows[1]["summary_key"], "bank_deposit")
            self.assertEqual(summary_rows[1]["candidate_count"], "1")
            self.assertEqual(summary_rows[1]["blocking_count"], "1")
            self.assertEqual(summary_rows[1]["top_recommended_owner_action"], "Fill required owner fields before dry-run can be ready")
            self.assertEqual(summary_rows[2]["summary_scope"], "source_ocr_excerpt_focus_status")
            self.assertEqual(summary_rows[2]["summary_key"], "focused_amount")
            self.assertEqual(summary_rows[2]["candidate_count"], "1")
            self.assertEqual(summary_rows[2]["blocking_count"], "1")
            self.assertEqual(summary_rows[2]["missing_owner_fields"], "owner_corrected_company,owner_corrected_bank")
            self.assertFalse(
                (
                    repo_root / "KMFA/metadata/fund_weekly_analysis/private_runtime/"
                    f"ocr_fact_candidate_owner_decisions/{run_id}.json"
                ).exists()
            )

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
