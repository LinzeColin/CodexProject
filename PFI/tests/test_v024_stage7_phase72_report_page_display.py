from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parent
PHASE71_DIR = ROOT / "reports" / "pfi_v024" / "stage_7" / "phase_7_1"
PHASE72_DIR = ROOT / "reports" / "pfi_v024" / "stage_7" / "phase_7_2"

REQUIRED_REPORT_IDS = {
    "net_worth_report",
    "cash_report",
    "investment_report",
    "consumption_report",
    "cashflow_report",
    "data_quality_report",
}
REQUIRED_CARD_FIELDS = {
    "report_id",
    "title_zh",
    "status",
    "status_zh",
    "conclusion_zh",
    "formula_zh",
    "parameters",
    "parameter_summary_zh",
    "sample_size",
    "sample_size_zh",
    "data_range",
    "data_range_zh",
    "metric_sources",
    "confidence",
    "gaps",
    "gap_summary_zh",
    "review_entry",
    "review_entry_zh",
}
REQUIRED_SECTION_IDS = {
    "report-cards",
    "formula-explanations",
    "parameters-and-samples",
    "gaps-and-review",
}


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
        raise AssertionError("Node runtime is required for Stage 7 Phase 7.2 page display tests")
    completed = subprocess.run(
        [node, "-e", script, *args],
        cwd=REPO_ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    return json.loads(completed.stdout)


class TestV024Stage7Phase72ReportPageDisplay(unittest.TestCase):
    def test_phase72_js_contract_is_current_phase_only(self) -> None:
        script = """
const reportsPage = require('./PFI/web/app/pages/reports.js');
console.log(JSON.stringify(reportsPage.buildV024Stage7Phase72Contract()));
"""
        contract = node_json(script)

        self.assertEqual(contract["target_version"], "v0.2.4")
        self.assertEqual(contract["source_package_version"], "v0.2.3-repair")
        self.assertEqual(contract["stage"], "Stage 7")
        self.assertEqual(contract["phase_id"], "7.2")
        self.assertEqual(contract["phase_name"], "页面展示")
        self.assertEqual(contract["task_ids"], ["T7.2.1", "T7.2.2", "T7.2.3", "T7.2.4"])
        self.assertTrue(contract["current_phase_only"])
        self.assertTrue(contract["max_one_phase_per_run"])
        self.assertTrue(contract["phase_7_1_complete_required"])
        self.assertTrue(contract["phase_7_2_page_display_complete"])
        self.assertFalse(contract["phase_7_3_started"])
        self.assertFalse(contract["stage_7_whole_review_complete"])
        self.assertFalse(contract["github_main_uploaded"])
        self.assertIn("PFI/web/app/pages/reports.js", contract["allowed_files"])
        self.assertIn("PFI/web/app/shell.js", contract["allowed_files"])
        self.assertIn("PFI/src/pfi_os/app/streamlit_app.py", contract["allowed_files"])
        self.assertIn("Phase 7.3 验收", contract["explicitly_not_done"])
        self.assertIn("Stage 7 whole-stage review", contract["explicitly_not_done"])

    def test_phase72_report_center_view_model_exposes_required_page_sections(self) -> None:
        report_pack = json.loads((PHASE71_DIR / "report_schema.json").read_text(encoding="utf-8"))
        script = """
const reportsPage = require('./PFI/web/app/pages/reports.js');
const reportPack = JSON.parse(process.argv[1]);
console.log(JSON.stringify(reportsPage.buildV024Stage7Phase72ReportCenterViewModel(reportPack)));
"""
        view = node_json(script, json.dumps(report_pack, ensure_ascii=False))

        self.assertEqual(view["schema"], "PFIV024Stage7Phase72ReportCenterViewModelV1")
        self.assertEqual(view["target_version"], "v0.2.4")
        self.assertEqual(view["phase_id"], "7.2")
        self.assertEqual(view["contract_version"], "PFI-V024-STAGE7-PHASE72-PAGE-DISPLAY")
        self.assertTrue(view["current_phase_only"])
        self.assertTrue(view["phase_7_1_complete_required"])
        self.assertTrue(view["phase_7_2_page_display_complete"])
        self.assertFalse(view["phase_7_3_started"])
        self.assertFalse(view["stage_7_whole_review_complete"])
        self.assertEqual(view["source"]["record_count"], 8815)
        self.assertEqual(view["source"]["raw_file_count"], 4)
        self.assertEqual(view["source"]["date_range"]["end"], "2026-06-03")
        self.assertEqual(view["report_count"], 6)
        self.assertEqual({item["report_id"] for item in view["report_cards"]}, REQUIRED_REPORT_IDS)
        self.assertEqual({item["id"] for item in view["sections"]}, REQUIRED_SECTION_IDS)

        for card in view["report_cards"]:
            self.assertTrue(REQUIRED_CARD_FIELDS.issubset(card), card["report_id"])
            self.assertRegex(card["title_zh"], r"[\u4e00-\u9fff]")
            self.assertRegex(card["formula_zh"], r"[\u4e00-\u9fff]")
            self.assertRegex(card["sample_size_zh"], r"样本量")
            self.assertRegex(card["data_range_zh"], r"数据范围")
            self.assertRegex(card["parameter_summary_zh"], r"参数")
            self.assertRegex(card["gap_summary_zh"], r"缺口")
            self.assertRegex(card["review_entry_zh"], r"复核")
            self.assertTrue(card["review_entry"]["route"].startswith("/"))

        view_text = json.dumps(view, ensure_ascii=False)
        for term in ("净资产报告", "现金报告", "投资报告", "消费报告", "现金流报告", "数据质量报告"):
            self.assertIn(term, view_text)
        for term in ("结论", "公式", "参数", "样本量", "数据范围", "置信度", "缺口", "复核入口"):
            self.assertIn(term, view_text)
        self.assertNotIn("完整财务结论", view_text)
        self.assertNotIn("CNY 0.00", view_text)

    def test_phase72_shell_and_bundle_load_report_page_before_shell_runtime(self) -> None:
        index_text = (ROOT / "web" / "index.html").read_text(encoding="utf-8")
        streamlit_text = (ROOT / "src" / "pfi_os" / "app" / "streamlit_app.py").read_text(encoding="utf-8")
        shell_text = (ROOT / "web" / "app" / "shell.js").read_text(encoding="utf-8")

        self.assertIn('<script src="./app/pages/reports.js"></script>', index_text)
        self.assertLess(
            index_text.index('<script src="./app/pages/reports.js"></script>'),
            index_text.index('<script src="./app/shell.js"></script>'),
        )
        self.assertIn('ROOT / "web" / "app" / "pages" / "reports.js"', streamlit_text)
        self.assertIn("reports_page_js", streamlit_text)
        self.assertIn('<script src="./app/pages/reports.js"></script>', streamlit_text)
        self.assertIn("PFI_V024_STAGE7_REPORTS", shell_text)
        self.assertIn("buildV024Stage7Phase72ReportCenterViewModel", shell_text)
        self.assertIn("applyV024Stage7Phase72ReportCenter", shell_text)

        for visible_term in ("公式", "参数", "样本量", "数据范围", "置信度", "缺口", "复核入口"):
            self.assertIn(visible_term, shell_text)

    def test_phase72_evidence_pack_is_machine_readable(self) -> None:
        expected_paths = [
            PHASE72_DIR / "evidence.json",
            PHASE72_DIR / "report_center_view_model.json",
            PHASE72_DIR / "page_display_validation.json",
            PHASE72_DIR / "changed_files.txt",
            PHASE72_DIR / "terminal.log",
            PHASE72_DIR / "risk_and_rollback.md",
        ]
        for path in expected_paths:
            self.assertTrue(path.exists(), str(path))

        evidence = json.loads((PHASE72_DIR / "evidence.json").read_text(encoding="utf-8"))
        view = json.loads((PHASE72_DIR / "report_center_view_model.json").read_text(encoding="utf-8"))
        validation = json.loads((PHASE72_DIR / "page_display_validation.json").read_text(encoding="utf-8"))
        changed_files = [
            line.strip()
            for line in (PHASE72_DIR / "changed_files.txt").read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

        self.assertEqual(evidence["schema"], "PFIV024Stage7Phase72EvidenceV1")
        self.assertEqual(evidence["target_version"], "v0.2.4")
        self.assertEqual(evidence["stage"], "Stage 7")
        self.assertEqual(evidence["phase_id"], "7.2")
        self.assertEqual(evidence["status"], "candidate_pass")
        self.assertTrue(evidence["current_phase_only"])
        self.assertTrue(evidence["phase_7_1_complete_required"])
        self.assertTrue(evidence["phase_7_2_page_display_complete"])
        self.assertFalse(evidence["phase_7_3_started"])
        self.assertFalse(evidence["stage_7_whole_review_complete"])
        self.assertFalse(evidence["github_main_uploaded"])
        self.assertFalse(evidence["app_bundle_reinstall_executed"])
        self.assertFalse(evidence["data_logic_changes_made"])
        self.assertFalse(evidence["formal_fake_financial_data_added"])
        self.assertEqual(evidence["changed_files"], changed_files)
        self.assertEqual(view["schema"], "PFIV024Stage7Phase72ReportCenterViewModelV1")
        self.assertEqual(validation["status"], "pass")
        self.assertEqual(set(validation["visible_report_ids"]), REQUIRED_REPORT_IDS)
        self.assertTrue(validation["formula_visible"])
        self.assertTrue(validation["parameters_and_sample_visible"])
        self.assertTrue(validation["gaps_and_review_visible"])

        doc_text = (ROOT / "docs" / "pfi_v024" / "STAGE7_REPORT_ANALYSIS.md").read_text(encoding="utf-8")
        run_contract = (ROOT / "docs" / "pfi_v024" / "RUN_CONTRACT.md").read_text(encoding="utf-8")
        self.assertIn("Stage 7 Phase 7.2", doc_text)
        self.assertIn("页面展示", doc_text)
        self.assertIn("公式解释区", doc_text)
        self.assertIn("参数与样本量区", doc_text)
        self.assertIn("缺口/复核入口", doc_text)
        self.assertIn("Phase 7.3 验收", doc_text)
        self.assertIn("Stage 7 whole-stage review", run_contract)


if __name__ == "__main__":
    unittest.main()
