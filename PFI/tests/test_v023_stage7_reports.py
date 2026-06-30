from __future__ import annotations

import importlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parent

REPORT_STATUSES = {"complete", "partial", "blocked", "outdated", "review_required"}
REQUIRED_REPORT_FIELDS = {
    "report_id",
    "title",
    "status",
    "conclusion_zh",
    "data_range",
    "sample_size",
    "core_metrics",
    "formulas",
    "parameters",
    "data_sources",
    "evidence_hash",
    "missing_data",
    "anomalies",
    "next_actions",
}
REQUIRED_REPORTS = {
    "net_worth_report",
    "cash_balance_report",
    "investment_market_value_report",
    "consumption_structure_report",
    "data_quality_report",
}
REQUIRED_FORMULAS = {
    "net_worth_cny",
    "cash_balance_cny",
    "investment_market_value_cny",
    "life_consumption_cny",
    "total_consumption_outflow_cny",
    "data_health",
}


def load_reports_module():
    spec = importlib.util.find_spec("pfi_v02.stage_v023_reports")
    if spec is None:
        raise AssertionError("PFI/src/pfi_v02/stage_v023_reports.py is required for Stage 7 Phase 7.1")
    return importlib.import_module("pfi_v02.stage_v023_reports")


def load_formula_module():
    spec = importlib.util.find_spec("pfi_v02.stage_v023_formula_registry")
    if spec is None:
        raise AssertionError("PFI/src/pfi_v02/stage_v023_formula_registry.py is required for Stage 7 Phase 7.1")
    return importlib.import_module("pfi_v02.stage_v023_formula_registry")


def node_executable() -> str | None:
    candidates = [
        os.environ.get("PFI_NODE"),
        shutil.which("node"),
        "/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return candidate
    return None


def node_json(script: str, *args: str) -> dict[str, object]:
    node = node_executable()
    if not node:
        raise AssertionError("Node runtime is required for Stage 7 report page contract tests")
    completed = subprocess.run(
        [node, "-e", script, *args],
        cwd=REPO_ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    return json.loads(completed.stdout)


class TestV023Stage7Reports(unittest.TestCase):
    def test_phase71_contract_is_limited_to_report_contract(self) -> None:
        module = load_reports_module()
        contract = module.build_stage7_phase71_contract()

        self.assertEqual(contract["version"], "v0.2.3")
        self.assertEqual(contract["stage"], "Stage 7")
        self.assertEqual(contract["phase_id"], "V023-S7-P7.1")
        self.assertEqual(contract["phase_name"], "报告合同")
        self.assertTrue(contract["current_phase_only"])
        self.assertTrue(contract["max_one_phase_per_run"])
        self.assertEqual(contract["task_ids"], ["T7.1.1", "T7.1.2", "T7.1.3", "T7.1.4"])
        self.assertIn("PFI/src/pfi_v02/stage_v023_reports.py", contract["allowed_files"])
        self.assertIn("PFI/src/pfi_v02/stage_v023_formula_registry.py", contract["allowed_files"])
        self.assertIn("PFI/web/app/pages/reports.js", contract["allowed_files"])
        self.assertIn("Phase 7.2 核心报告", contract["explicitly_not_done"])
        self.assertIn("Phase 7.3 数据质量与调参", contract["explicitly_not_done"])
        self.assertIn("GitHub main upload for intermediate phase", contract["explicitly_not_done"])

    def test_phase71_report_schema_covers_required_fields_and_statuses(self) -> None:
        module = load_reports_module()
        core_metrics = json.loads((ROOT / "reports" / "pfi_v023" / "stage_6" / "phase_6_1" / "core_metrics.json").read_text(encoding="utf-8"))
        contract = module.build_stage7_report_contract(core_metrics_read_model=core_metrics)

        self.assertEqual(contract["schema"], "PFIV023Stage7ReportContractV1")
        self.assertEqual(contract["phase_id"], "V023-S7-P7.1")
        self.assertEqual(set(contract["report_statuses"]), REPORT_STATUSES)
        self.assertEqual(set(contract["required_report_fields"]), REQUIRED_REPORT_FIELDS)
        reports = {item["report_id"]: item for item in contract["reports"]}
        self.assertTrue(REQUIRED_REPORTS.issubset(reports))

        for report in reports.values():
            self.assertTrue(REQUIRED_REPORT_FIELDS.issubset(report), report["report_id"])
            self.assertIn(report["status"], REPORT_STATUSES)
            self.assertRegex(report["conclusion_zh"], r"[\u4e00-\u9fff]")
            self.assertIsInstance(report["sample_size"], dict)
            self.assertIsInstance(report["parameters"], list)
            self.assertIsInstance(report["formulas"], list)
            self.assertIsInstance(report["missing_data"], list)
            if report["status"] in {"blocked", "partial"}:
                self.assertGreater(len(report["missing_data"]), 0, report["report_id"])
                self.assertNotRegex(report["conclusion_zh"], r"完整财务结论")

        self.assertEqual(reports["net_worth_report"]["status"], "blocked")
        self.assertEqual(reports["cash_balance_report"]["status"], "blocked")
        self.assertEqual(reports["investment_market_value_report"]["status"], "blocked")
        self.assertEqual(reports["consumption_structure_report"]["status"], "partial")
        self.assertIn("未挂载账户余额", json.dumps(reports["data_quality_report"], ensure_ascii=False))

    def test_phase71_formula_registry_exposes_formula_parameters_and_real_sources(self) -> None:
        module = load_formula_module()
        core_metrics = json.loads((ROOT / "reports" / "pfi_v023" / "stage_6" / "phase_6_1" / "core_metrics.json").read_text(encoding="utf-8"))
        registry = module.build_stage7_formula_registry(core_metrics_read_model=core_metrics)

        self.assertEqual(registry["schema"], "PFIV023Stage7FormulaRegistryV1")
        formulas = {item["metric_id"]: item for item in registry["formulas"]}
        self.assertEqual(set(formulas), REQUIRED_FORMULAS)

        for metric_id, formula in formulas.items():
            self.assertRegex(formula["formula_zh"], r"[\u4e00-\u9fff]")
            self.assertIn("parameters", formula)
            self.assertIn("data_sources", formula)
            self.assertIn("status_policy_zh", formula)
            for parameter in formula["parameters"]:
                self.assertIn("parameter_id", parameter)
                self.assertIn("value", parameter)
                self.assertIn("source", parameter)
                self.assertIn("adjustable", parameter)

        self.assertEqual(formulas["net_worth_cny"]["input_status"], "blocked")
        self.assertIn("cash_balance_cny", formulas["net_worth_cny"]["missing_inputs"])
        self.assertEqual(formulas["life_consumption_cny"]["input_status"], "ready")
        self.assertIn("生活消费流出减退款", formulas["life_consumption_cny"]["formula_zh"])
        self.assertIn("基金申购", formulas["total_consumption_outflow_cny"]["formula_zh"])

    def test_phase71_report_page_view_model_preserves_formula_parameter_and_blocked_status(self) -> None:
        reports = json.loads((ROOT / "reports" / "pfi_v023" / "stage_7" / "phase_7_1" / "report_contract.json").read_text(encoding="utf-8"))
        registry = json.loads((ROOT / "reports" / "pfi_v023" / "stage_7" / "phase_7_1" / "formula_registry.json").read_text(encoding="utf-8"))
        script = """
const reportsPage = require('./PFI/web/app/pages/reports.js');
const reports = JSON.parse(process.argv[1]);
const registry = JSON.parse(process.argv[2]);
console.log(JSON.stringify(reportsPage.buildStage7Phase71ReportsViewModel(reports, registry)));
"""
        view = node_json(script, json.dumps(reports, ensure_ascii=False), json.dumps(registry, ensure_ascii=False))

        self.assertEqual(view["schema"], "PFIV023Stage7ReportsPageViewModelV1")
        self.assertEqual(view["phase_id"], "V023-S7-P7.1")
        self.assertEqual(view["report_count"], 5)
        self.assertGreaterEqual(view["blocked_or_partial_count"], 4)
        text = json.dumps(view, ensure_ascii=False)
        for term in ("公式", "参数", "样本量", "数据范围", "缺口", "未挂载账户余额"):
            self.assertIn(term, text)
        self.assertNotIn("完整财务结论", text)
        self.assertNotIn("CNY 0.00", text)

    def test_phase71_doc_and_evidence_exist_before_candidate_pass(self) -> None:
        phase_dir = ROOT / "reports" / "pfi_v023" / "stage_7" / "phase_7_1"
        doc_path = ROOT / "docs" / "pfi_v023" / "STAGE7_REPORTS.md"
        evidence_path = phase_dir / "evidence.json"
        report_contract_path = phase_dir / "report_contract.json"
        formula_path = phase_dir / "formula_registry.json"
        page_model_path = phase_dir / "report_page_model.json"
        scan_path = phase_dir / "no_source_term_scan.json"
        changed_files_path = phase_dir / "changed_files.txt"
        terminal_log_path = phase_dir / "terminal.log"

        for path in (doc_path, evidence_path, report_contract_path, formula_path, page_model_path, scan_path, changed_files_path, terminal_log_path):
            self.assertTrue(path.exists(), str(path))

        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        report_contract = json.loads(report_contract_path.read_text(encoding="utf-8"))
        formula_registry = json.loads(formula_path.read_text(encoding="utf-8"))
        page_model = json.loads(page_model_path.read_text(encoding="utf-8"))
        scan = json.loads(scan_path.read_text(encoding="utf-8"))
        changed_files = [line.strip() for line in changed_files_path.read_text(encoding="utf-8").splitlines() if line.strip()]

        self.assertEqual(evidence["version"], "v0.2.3")
        self.assertEqual(evidence["stage"], "Stage 7")
        self.assertEqual(evidence["phase_id"], "V023-S7-P7.1")
        self.assertEqual(evidence["status"], "candidate_pass")
        self.assertTrue(evidence["current_phase_only"])
        self.assertTrue(evidence["max_one_phase_per_run"])
        self.assertFalse(evidence["stage_contract"]["phase_7_2_core_reports_done"])
        self.assertFalse(evidence["stage_contract"]["stage_7_whole_review_done"])
        self.assertFalse(evidence["stage_contract"]["github_main_upload_done"])
        self.assertEqual(evidence["changed_files"], changed_files)
        self.assertEqual(report_contract["schema"], "PFIV023Stage7ReportContractV1")
        self.assertEqual(formula_registry["schema"], "PFIV023Stage7FormulaRegistryV1")
        self.assertEqual(page_model["schema"], "PFIV023Stage7ReportsPageViewModelV1")
        self.assertEqual(scan["violations"], [])

        doc_text = doc_path.read_text(encoding="utf-8")
        self.assertIn("Stage 7 Phase 7.1", doc_text)
        self.assertIn("报告合同", doc_text)
        self.assertIn("Stage 7 Phase 7.2", doc_text)
        self.assertIn("Stage 7 Whole-stage Review", doc_text)
        self.assertIn("GitHub main 上传不写成提交内自引用事实", doc_text)

        terminal_log = terminal_log_path.read_text(encoding="utf-8")
        self.assertIn("PFI/tests/test_v023_stage7_reports.py -q", terminal_log)

    def test_phase71_new_files_do_not_contain_blocked_placeholder_terms(self) -> None:
        terms = ["mo" + "ck", "sam" + "ple", "synthe" + "tic", "fix" + "ture", "de" + "mo", "fa" + "ke"]
        paths = [
            ROOT / "src" / "pfi_v02" / "stage_v023_reports.py",
            ROOT / "src" / "pfi_v02" / "stage_v023_formula_registry.py",
            ROOT / "web" / "app" / "pages" / "reports.js",
            ROOT / "tests" / "test_v023_stage7_reports.py",
            ROOT / "docs" / "pfi_v023" / "STAGE7_REPORTS.md",
        ]
        for path in paths:
            self.assertTrue(path.exists(), str(path))
            text = path.read_text(encoding="utf-8").lower().replace("sample_size", "")
            for term in terms:
                self.assertIsNone(re.search(term, text), f"{path} contains blocked placeholder term {term}")

    def test_phase72_contract_is_limited_to_core_reports(self) -> None:
        module = load_reports_module()
        contract = module.build_stage7_phase72_contract()

        self.assertEqual(contract["version"], "v0.2.3")
        self.assertEqual(contract["stage"], "Stage 7")
        self.assertEqual(contract["phase_id"], "V023-S7-P7.2")
        self.assertEqual(contract["phase_name"], "核心报告")
        self.assertTrue(contract["current_phase_only"])
        self.assertTrue(contract["max_one_phase_per_run"])
        self.assertEqual(contract["task_ids"], ["T7.2.1", "T7.2.2", "T7.2.3", "T7.2.4"])
        self.assertIn("PFI/src/pfi_v02/stage_v023_reports.py", contract["allowed_files"])
        self.assertIn("PFI/web/app/pages/reports.js", contract["allowed_files"])
        self.assertNotIn("PFI/web/app/shell.js", contract["changed_in_this_phase"])
        self.assertIn("Phase 7.3 数据质量与调参", contract["explicitly_not_done"])
        self.assertIn("Stage 7 whole-stage review", contract["explicitly_not_done"])
        self.assertIn("GitHub main upload for intermediate phase", contract["explicitly_not_done"])

    def test_phase72_core_reports_preserve_blocked_status_and_real_consumption_inputs(self) -> None:
        module = load_reports_module()
        core_metrics = json.loads((ROOT / "reports" / "pfi_v023" / "stage_6" / "phase_6_1" / "core_metrics.json").read_text(encoding="utf-8"))
        payload = module.build_stage7_core_reports(core_metrics_read_model=core_metrics)

        self.assertEqual(payload["schema"], "PFIV023Stage7CoreReportsV1")
        self.assertEqual(payload["phase_id"], "V023-S7-P7.2")
        self.assertEqual(payload["source_core_metrics"]["read_model_hash"], core_metrics["read_model_hash"])
        reports = {item["report_id"]: item for item in payload["reports"]}
        self.assertEqual(set(reports), {"net_worth_report", "cash_balance_report", "investment_market_value_report", "consumption_structure_report"})

        for report_id in ("net_worth_report", "cash_balance_report", "investment_market_value_report"):
            report = reports[report_id]
            self.assertEqual(report["status"], "blocked", report_id)
            self.assertGreater(len(report["missing_data"]), 0, report_id)
            self.assertRegex(report["conclusion_zh"], r"未挂载|阻断")
            self.assertNotIn("CNY 0.00", json.dumps(report, ensure_ascii=False))
            self.assertNotRegex(report["conclusion_zh"], r"完整财务结论")

        consumption = reports["consumption_structure_report"]
        self.assertEqual(consumption["status"], "partial")
        self.assertEqual(consumption["data_range"], {"start": "2022-06-06", "end": "2026-06-03"})
        self.assertEqual(consumption["sample_size"]["transaction_count"], 8815)
        self.assertEqual(consumption["sample_size"]["raw_file_count"], 4)
        self.assertIn("life_consumption_cny", {item["metric_id"] for item in consumption["core_metrics"]})
        self.assertIn("total_consumption_outflow_cny", {item["metric_id"] for item in consumption["core_metrics"]})
        self.assertIn("CNY 1,545,600.44", consumption["conclusion_zh"])
        self.assertIn("CNY 1,727,278.37", consumption["conclusion_zh"])
        self.assertIn("分类结构", " ".join(consumption["missing_data"]))
        self.assertIn("生活消费流出减退款", json.dumps(consumption["formulas"], ensure_ascii=False))
        self.assertIn("基金申购", json.dumps(consumption["formulas"], ensure_ascii=False))

    def test_phase72_core_reports_page_model_highlights_one_real_partial_report(self) -> None:
        core_reports = json.loads((ROOT / "reports" / "pfi_v023" / "stage_7" / "phase_7_2" / "core_reports.json").read_text(encoding="utf-8"))
        script = """
const reportsPage = require('./PFI/web/app/pages/reports.js');
const payload = JSON.parse(process.argv[1]);
console.log(JSON.stringify(reportsPage.buildStage7Phase72CoreReportsViewModel(payload)));
"""
        view = node_json(script, json.dumps(core_reports, ensure_ascii=False))

        self.assertEqual(view["schema"], "PFIV023Stage7CoreReportsPageViewModelV1")
        self.assertEqual(view["phase_id"], "V023-S7-P7.2")
        self.assertEqual(view["report_count"], 4)
        self.assertEqual(view["blocked_count"], 3)
        self.assertEqual(view["partial_count"], 1)
        text = json.dumps(view, ensure_ascii=False)
        for term in ("净资产报告", "现金余额报告", "投资市值报告", "消费结构报告", "数据范围", "样本量", "公式", "缺口"):
            self.assertIn(term, text)
        self.assertIn("CNY 1,545,600.44", text)
        self.assertNotIn("完整财务结论", text)
        self.assertNotIn("CNY 0.00", text)

    def test_phase72_doc_and_evidence_exist_before_candidate_pass(self) -> None:
        phase_dir = ROOT / "reports" / "pfi_v023" / "stage_7" / "phase_7_2"
        evidence_path = phase_dir / "evidence.json"
        core_reports_path = phase_dir / "core_reports.json"
        page_model_path = phase_dir / "core_reports_page_model.json"
        scan_path = phase_dir / "no_source_term_scan.json"
        screenshot_path = phase_dir / "screenshots" / "core_reports.png"
        changed_files_path = phase_dir / "changed_files.txt"
        terminal_log_path = phase_dir / "terminal.log"

        for path in (evidence_path, core_reports_path, page_model_path, scan_path, screenshot_path, changed_files_path, terminal_log_path):
            self.assertTrue(path.exists(), str(path))

        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        core_reports = json.loads(core_reports_path.read_text(encoding="utf-8"))
        page_model = json.loads(page_model_path.read_text(encoding="utf-8"))
        scan = json.loads(scan_path.read_text(encoding="utf-8"))
        changed_files = [line.strip() for line in changed_files_path.read_text(encoding="utf-8").splitlines() if line.strip()]

        self.assertEqual(evidence["version"], "v0.2.3")
        self.assertEqual(evidence["stage"], "Stage 7")
        self.assertEqual(evidence["phase_id"], "V023-S7-P7.2")
        self.assertEqual(evidence["status"], "candidate_pass")
        self.assertTrue(evidence["current_phase_only"])
        self.assertTrue(evidence["max_one_phase_per_run"])
        self.assertFalse(evidence["stage_contract"]["phase_7_3_data_quality_tuning_done"])
        self.assertFalse(evidence["stage_contract"]["stage_7_whole_review_done"])
        self.assertFalse(evidence["stage_contract"]["github_main_upload_done"])
        self.assertEqual(evidence["changed_files"], changed_files)
        self.assertEqual(core_reports["schema"], "PFIV023Stage7CoreReportsV1")
        self.assertEqual(page_model["schema"], "PFIV023Stage7CoreReportsPageViewModelV1")
        self.assertEqual(scan["violations"], [])
        self.assertGreater(screenshot_path.stat().st_size, 10000)

        doc_text = (ROOT / "docs" / "pfi_v023" / "STAGE7_REPORTS.md").read_text(encoding="utf-8")
        self.assertIn("Stage 7 Phase 7.2", doc_text)
        self.assertIn("核心报告", doc_text)
        self.assertIn("Stage 7 Phase 7.3", doc_text)
        self.assertIn("Stage 7 Whole-stage Review", doc_text)

        terminal_log = terminal_log_path.read_text(encoding="utf-8")
        self.assertIn("PFI/tests/test_v023_stage7_reports.py -q", terminal_log)

    def test_phase73_contract_is_limited_to_data_quality_and_tuning(self) -> None:
        module = load_reports_module()
        contract = module.build_stage7_phase73_contract()

        self.assertEqual(contract["version"], "v0.2.3")
        self.assertEqual(contract["stage"], "Stage 7")
        self.assertEqual(contract["phase_id"], "V023-S7-P7.3")
        self.assertEqual(contract["phase_name"], "数据质量与调参")
        self.assertTrue(contract["current_phase_only"])
        self.assertTrue(contract["max_one_phase_per_run"])
        self.assertEqual(contract["task_ids"], ["T7.3.1", "T7.3.2", "T7.3.3", "T7.3.4"])
        self.assertIn("PFI/src/pfi_v02/stage_v023_reports.py", contract["allowed_files"])
        self.assertIn("PFI/web/app/pages/reports.js", contract["allowed_files"])
        self.assertNotIn("PFI/web/app/shell.js", contract["changed_in_this_phase"])
        self.assertIn("Stage 7 whole-stage review", contract["explicitly_not_done"])
        self.assertIn("GitHub main upload for intermediate phase", contract["explicitly_not_done"])

    def test_phase73_quality_and_tuning_uses_only_real_read_model_and_preserves_blockers(self) -> None:
        module = load_reports_module()
        core_metrics = json.loads((ROOT / "reports" / "pfi_v023" / "stage_6" / "phase_6_1" / "core_metrics.json").read_text(encoding="utf-8"))
        payload = module.build_stage7_quality_tuning(core_metrics_read_model=core_metrics)

        self.assertEqual(payload["schema"], "PFIV023Stage7QualityTuningV1")
        self.assertEqual(payload["phase_id"], "V023-S7-P7.3")
        self.assertEqual(payload["source_core_metrics"]["read_model_hash"], core_metrics["read_model_hash"])
        self.assertEqual(payload["data_quality_report"]["status"], "partial")
        self.assertEqual(payload["data_quality_report"]["data_range"], {"start": "2022-06-06", "end": "2026-06-03"})
        self.assertEqual(payload["data_quality_report"]["sample_size"]["transaction_count"], 8815)
        self.assertEqual(payload["data_quality_report"]["sample_size"]["raw_file_count"], 4)
        self.assertEqual(set(payload["data_quality_report"]["blocked_metric_ids"]), {"net_worth_cny", "cash_balance_cny", "investment_market_value_cny"})
        text = json.dumps(payload, ensure_ascii=False)
        for term in ("未挂载账户余额", "未挂载持仓市值", "数据质量报告", "公式解释", "参数影响预览", "导出/保存策略"):
            self.assertIn(term, text)
        self.assertNotIn("CNY 0.00", text)
        self.assertNotIn("完整财务结论", text)

    def test_phase73_formula_explanations_and_parameter_preview_are_actionable_without_recalculation(self) -> None:
        module = load_reports_module()
        core_metrics = json.loads((ROOT / "reports" / "pfi_v023" / "stage_6" / "phase_6_1" / "core_metrics.json").read_text(encoding="utf-8"))
        payload = module.build_stage7_quality_tuning(core_metrics_read_model=core_metrics)
        explanations = {item["metric_id"]: item for item in payload["formula_explanations"]}
        preview = {item["parameter_id"]: item for item in payload["parameter_impact_preview"]}

        self.assertIn("net_worth_cny", explanations)
        self.assertIn("life_consumption_cny", explanations)
        self.assertEqual(explanations["net_worth_cny"]["input_status"], "blocked")
        self.assertIn("cash_balance_cny", explanations["net_worth_cny"]["missing_inputs"])
        self.assertEqual(explanations["life_consumption_cny"]["input_status"], "ready")
        self.assertIn("生活消费流出减退款", explanations["life_consumption_cny"]["formula_zh"])
        self.assertIn("life_event_type", preview)
        self.assertIn(preview["life_event_type"]["impact_status"], {"not_adjustable", "blocked_by_read_model"})
        for item in payload["parameter_impact_preview"]:
            self.assertIn("current_value", item)
            self.assertIn("current_source", item)
            self.assertIn("impact_summary_zh", item)
            self.assertIsNone(item["preview_value"])
            self.assertIn(item["impact_status"], {"not_adjustable", "blocked_by_read_model"})

        export_policy = payload["export_save_policy"]
        self.assertEqual(export_policy["phase_id"], "V023-S7-P7.3")
        self.assertIn("quality_tuning.json", " ".join(export_policy["saved_artifacts"]))
        self.assertIn("PDF", " ".join(export_policy["explicitly_not_implemented"]))

    def test_phase73_quality_tuning_page_model_exposes_sections(self) -> None:
        payload = json.loads((ROOT / "reports" / "pfi_v023" / "stage_7" / "phase_7_3" / "quality_tuning.json").read_text(encoding="utf-8"))
        script = """
const reportsPage = require('./PFI/web/app/pages/reports.js');
const payload = JSON.parse(process.argv[1]);
console.log(JSON.stringify(reportsPage.buildStage7Phase73QualityTuningViewModel(payload)));
"""
        view = node_json(script, json.dumps(payload, ensure_ascii=False))

        self.assertEqual(view["schema"], "PFIV023Stage7QualityTuningPageViewModelV1")
        self.assertEqual(view["phase_id"], "V023-S7-P7.3")
        self.assertEqual(view["section_count"], 4)
        self.assertGreaterEqual(view["blocked_metric_count"], 3)
        text = json.dumps(view, ensure_ascii=False)
        for term in ("数据质量报告", "公式解释", "参数影响预览", "导出/保存策略", "未挂载账户余额", "PDF"):
            self.assertIn(term, text)
        self.assertNotIn("CNY 0.00", text)

    def test_phase73_doc_and_evidence_exist_before_candidate_pass(self) -> None:
        phase_dir = ROOT / "reports" / "pfi_v023" / "stage_7" / "phase_7_3"
        evidence_path = phase_dir / "evidence.json"
        quality_path = phase_dir / "quality_tuning.json"
        page_model_path = phase_dir / "quality_tuning_page_model.json"
        scan_path = phase_dir / "no_source_term_scan.json"
        screenshot_path = phase_dir / "screenshots" / "quality_tuning.png"
        changed_files_path = phase_dir / "changed_files.txt"
        terminal_log_path = phase_dir / "terminal.log"

        for path in (evidence_path, quality_path, page_model_path, scan_path, screenshot_path, changed_files_path, terminal_log_path):
            self.assertTrue(path.exists(), str(path))

        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        quality = json.loads(quality_path.read_text(encoding="utf-8"))
        page_model = json.loads(page_model_path.read_text(encoding="utf-8"))
        scan = json.loads(scan_path.read_text(encoding="utf-8"))
        changed_files = [line.strip() for line in changed_files_path.read_text(encoding="utf-8").splitlines() if line.strip()]

        self.assertEqual(evidence["version"], "v0.2.3")
        self.assertEqual(evidence["stage"], "Stage 7")
        self.assertEqual(evidence["phase_id"], "V023-S7-P7.3")
        self.assertEqual(evidence["status"], "candidate_pass")
        self.assertTrue(evidence["current_phase_only"])
        self.assertTrue(evidence["max_one_phase_per_run"])
        self.assertFalse(evidence["stage_contract"]["stage_7_whole_review_done"])
        self.assertFalse(evidence["stage_contract"]["github_main_upload_done"])
        self.assertEqual(evidence["changed_files"], changed_files)
        self.assertEqual(quality["schema"], "PFIV023Stage7QualityTuningV1")
        self.assertEqual(page_model["schema"], "PFIV023Stage7QualityTuningPageViewModelV1")
        self.assertEqual(scan["violations"], [])
        self.assertGreater(screenshot_path.stat().st_size, 10000)

        doc_text = (ROOT / "docs" / "pfi_v023" / "STAGE7_REPORTS.md").read_text(encoding="utf-8")
        self.assertIn("Stage 7 Phase 7.3", doc_text)
        self.assertIn("数据质量与调参", doc_text)
        self.assertIn("Stage 7 Whole-stage Review", doc_text)

        terminal_log = terminal_log_path.read_text(encoding="utf-8")
        self.assertIn("PFI/tests/test_v023_stage7_reports.py -q", terminal_log)

    def test_stage7_review_evidence_exists_before_stage_upload(self) -> None:
        review_dir = ROOT / "reports" / "pfi_v023" / "stage_7" / "stage7_review"
        evidence_path = review_dir / "evidence.json"
        audit_path = review_dir / "review_audit.json"
        scan_path = review_dir / "no_source_term_scan.json"
        terminal_log_path = review_dir / "terminal.log"
        changed_files_path = review_dir / "changed_files.txt"

        self.assertTrue(evidence_path.exists(), "Stage 7 whole-stage review evidence is required before upload")
        self.assertTrue(audit_path.exists(), "Stage 7 whole-stage review audit is required before upload")
        self.assertTrue(scan_path.exists(), "Stage 7 whole-stage no-source-term scan is required")
        self.assertTrue(terminal_log_path.exists(), "Stage 7 whole-stage review terminal log is required")
        self.assertTrue(changed_files_path.exists(), "Stage 7 whole-stage review changed files record is required")

        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        audit = json.loads(audit_path.read_text(encoding="utf-8"))
        scan = json.loads(scan_path.read_text(encoding="utf-8"))
        changed_files = [line.strip() for line in changed_files_path.read_text(encoding="utf-8").splitlines() if line.strip()]

        self.assertEqual(evidence["version"], "v0.2.3")
        self.assertEqual(evidence["stage"], "Stage 7")
        self.assertEqual(evidence["review_id"], "V023-S7-REVIEW")
        self.assertEqual(evidence["status"], "candidate_pass")
        self.assertTrue(evidence["stage7_whole_stage_review"])
        self.assertTrue(evidence["findings_fixed"])
        self.assertFalse(evidence["stage8_started"])
        self.assertFalse(evidence["github_main_uploaded_before_review"])
        self.assertEqual(evidence["changed_files"], changed_files)
        self.assertEqual(audit["review_id"], "V023-S7-REVIEW")
        self.assertEqual(audit["phase_status"], {"phase_7_1": "candidate_pass", "phase_7_2": "candidate_pass", "phase_7_3": "candidate_pass"})
        self.assertEqual(audit["review_findings"], [])
        self.assertEqual(scan["violations"], [])
        self.assertEqual(audit["report_status"]["blocked"], 3)
        self.assertEqual(audit["report_status"]["partial"], 2)
        self.assertEqual(audit["core_report_status"]["blocked"], 3)
        self.assertEqual(audit["core_report_status"]["partial"], 1)
        self.assertEqual(audit["quality_tuning"]["blocked_metric_count"], 3)
        self.assertEqual(audit["quality_tuning"]["section_count"], 4)
        self.assertTrue(audit["acceptance_checks"]["reports_have_formula_parameter_range_record_scope_gap"])
        self.assertTrue(audit["acceptance_checks"]["missing_data_stays_partial_or_blocked"])
        self.assertTrue(audit["acceptance_checks"]["export_or_unimplemented_scope_recorded"])
        self.assertTrue(audit["stop_condition_checks"]["no_cny_zero_for_blocked_metrics"])
        self.assertTrue(audit["stop_condition_checks"]["no_complete_conclusion_when_inputs_missing"])

        doc_text = (ROOT / "docs" / "pfi_v023" / "STAGE7_REPORTS.md").read_text(encoding="utf-8")
        self.assertIn("Stage 7 Whole-stage Review", doc_text)
        self.assertNotIn("Stage 7 whole-stage review 未执行", doc_text)

        terminal_log = terminal_log_path.read_text(encoding="utf-8")
        self.assertIn("Stage 7 whole-stage review", terminal_log)
        self.assertIn("PFI/tests/test_v023_stage7_reports.py -q", terminal_log)


if __name__ == "__main__":
    unittest.main()
