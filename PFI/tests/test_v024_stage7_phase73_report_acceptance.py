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
PHASE73_DIR = ROOT / "reports" / "pfi_v024" / "stage_7" / "phase_7_3"

REQUIRED_REPORT_IDS = {
    "net_worth_report",
    "cash_report",
    "investment_report",
    "consumption_report",
    "cashflow_report",
    "data_quality_report",
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
        raise AssertionError("Node runtime is required for Stage 7 Phase 7.3 acceptance tests")
    completed = subprocess.run(
        [node, "-e", script, *args],
        cwd=REPO_ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    return json.loads(completed.stdout)


class TestV024Stage7Phase73ReportAcceptance(unittest.TestCase):
    def test_phase73_js_contract_is_acceptance_only(self) -> None:
        script = """
const reportsPage = require('./PFI/web/app/pages/reports.js');
console.log(JSON.stringify(reportsPage.buildV024Stage7Phase73Contract()));
"""
        contract = node_json(script)

        self.assertEqual(contract["target_version"], "v0.2.4")
        self.assertEqual(contract["source_package_version"], "v0.2.3-repair")
        self.assertEqual(contract["stage"], "Stage 7")
        self.assertEqual(contract["phase_id"], "7.3")
        self.assertEqual(contract["phase_name"], "验收")
        self.assertEqual(contract["task_ids"], ["T7.3.1", "T7.3.2", "T7.3.3"])
        self.assertTrue(contract["current_phase_only"])
        self.assertTrue(contract["max_one_phase_per_run"])
        self.assertTrue(contract["phase_7_1_complete_required"])
        self.assertTrue(contract["phase_7_2_complete_required"])
        self.assertTrue(contract["phase_7_3_acceptance_complete"])
        self.assertFalse(contract["stage_7_whole_review_complete"])
        self.assertFalse(contract["github_main_uploaded"])
        self.assertFalse(contract["app_bundle_reinstall_executed"])
        self.assertFalse(contract["data_logic_changes_allowed"])
        self.assertFalse(contract["formal_fake_financial_data_allowed"])
        self.assertIn("Stage 7 whole-stage review", contract["explicitly_not_done"])
        self.assertIn("GitHub main upload", contract["explicitly_not_done"])

    def test_phase73_acceptance_gate_passes_real_report_center_and_rejects_bad_reports(self) -> None:
        report_pack = json.loads((PHASE71_DIR / "report_schema.json").read_text(encoding="utf-8"))
        script = """
const reportsPage = require('./PFI/web/app/pages/reports.js');
const reportPack = JSON.parse(process.argv[1]);
const view = reportsPage.buildV024Stage7Phase72ReportCenterViewModel(reportPack);
const gate = reportsPage.validateV024Stage7Phase73Acceptance(view);
const invalidView = JSON.parse(JSON.stringify(view));
invalidView.report_cards[0].conclusion_zh = "这是一段 " + "AI" + " 总结，缺少公式、参数、范围和样本量。";
invalidView.report_cards[0].formula_zh = "";
invalidView.report_cards[0].parameters = [];
invalidView.report_cards[0].metric_sources = invalidView.report_cards[0].metric_sources.concat(["mo" + "ck_financial_feed"]);
const invalidGate = reportsPage.validateV024Stage7Phase73Acceptance(invalidView);
console.log(JSON.stringify({ gate, invalidGate }));
"""
        result = node_json(script, json.dumps(report_pack, ensure_ascii=False))
        gate = result["gate"]
        invalid_gate = result["invalidGate"]

        self.assertEqual(gate["schema"], "PFIV024Stage7Phase73AcceptanceGateV1")
        self.assertEqual(gate["target_version"], "v0.2.4")
        self.assertEqual(gate["stage"], "Stage 7")
        self.assertEqual(gate["phase_id"], "7.3")
        self.assertEqual(gate["status"], "pass")
        self.assertEqual(set(gate["visible_report_ids"]), REQUIRED_REPORT_IDS)
        self.assertTrue(gate["data_insufficient_report_test_passed"])
        self.assertTrue(gate["data_quality_report_generated"])
        self.assertTrue(gate["blocked_reports_without_full_financial_conclusion"])
        self.assertTrue(gate["formula_sample_visible"])
        self.assertEqual(gate["ai_paragraph_report_ids"], [])
        self.assertEqual(gate["single_paragraph_report_ids"], [])
        self.assertEqual(gate["forbidden_source_terms"], [])
        self.assertEqual(gate["financial_conclusion_when_blocked"], [])

        self.assertEqual(invalid_gate["status"], "fail")
        self.assertIn("net_worth_report", invalid_gate["ai_paragraph_report_ids"])
        self.assertIn("net_worth_report", invalid_gate["single_paragraph_report_ids"])
        self.assertIn("net_worth_report", json.dumps(invalid_gate["forbidden_source_terms"], ensure_ascii=False))

    def test_phase73_evidence_pack_and_browser_validation_exist(self) -> None:
        expected_paths = [
            PHASE73_DIR / "evidence.json",
            PHASE73_DIR / "report_acceptance_gate.json",
            PHASE73_DIR / "browser_validation.json",
            PHASE73_DIR / "sample_data_quality_report.html",
            PHASE73_DIR / "formula_visibility.png",
            PHASE73_DIR / "changed_files.txt",
            PHASE73_DIR / "terminal.log",
            PHASE73_DIR / "risk_and_rollback.md",
        ]
        for path in expected_paths:
            self.assertTrue(path.exists(), str(path))
            self.assertGreater(path.stat().st_size, 0, str(path))

        evidence = json.loads((PHASE73_DIR / "evidence.json").read_text(encoding="utf-8"))
        gate = json.loads((PHASE73_DIR / "report_acceptance_gate.json").read_text(encoding="utf-8"))
        browser = json.loads((PHASE73_DIR / "browser_validation.json").read_text(encoding="utf-8"))
        changed_files = [
            line.strip()
            for line in (PHASE73_DIR / "changed_files.txt").read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        html = (PHASE73_DIR / "sample_data_quality_report.html").read_text(encoding="utf-8")

        self.assertEqual(evidence["schema"], "PFIV024Stage7Phase73EvidenceV1")
        self.assertEqual(evidence["target_version"], "v0.2.4")
        self.assertEqual(evidence["stage"], "Stage 7")
        self.assertEqual(evidence["phase_id"], "7.3")
        self.assertEqual(evidence["status"], "candidate_pass")
        self.assertTrue(evidence["current_phase_only"])
        self.assertTrue(evidence["phase_7_1_complete_required"])
        self.assertTrue(evidence["phase_7_2_complete_required"])
        self.assertTrue(evidence["phase_7_3_acceptance_complete"])
        self.assertFalse(evidence["stage_7_whole_review_complete"])
        self.assertFalse(evidence["github_main_uploaded"])
        self.assertFalse(evidence["app_bundle_reinstall_executed"])
        self.assertFalse(evidence["data_logic_changes_made"])
        self.assertFalse(evidence["formal_fake_financial_data_added"])
        self.assertEqual(evidence["changed_files"], changed_files)

        self.assertEqual(gate["status"], "pass")
        self.assertEqual(set(gate["visible_report_ids"]), REQUIRED_REPORT_IDS)
        self.assertTrue(gate["data_quality_report_generated"])
        self.assertTrue(gate["formula_sample_visible"])
        self.assertEqual(browser["status"], "pass")
        self.assertTrue(browser["formula_visibility_screenshot"])
        self.assertGreater(browser["formula_visibility_screenshot_bytes"], 10000)
        self.assertEqual(browser["console_errors"], [])
        self.assertEqual(browser["page_errors"], [])
        self.assertEqual(browser["http_errors"], [])
        self.assertIn("数据质量报告", html)
        self.assertIn("真实 Stage 4 read model", html)
        self.assertNotIn("完整财务结论", html)
        self.assertNotIn("CNY 0.00", html)

        doc_text = (ROOT / "docs" / "pfi_v024" / "STAGE7_REPORT_ANALYSIS.md").read_text(encoding="utf-8")
        run_contract = (ROOT / "docs" / "pfi_v024" / "RUN_CONTRACT.md").read_text(encoding="utf-8")
        self.assertIn("Stage 7 Phase 7.3", doc_text)
        self.assertIn("验收", doc_text)
        self.assertIn("report_acceptance_gate.json", doc_text)
        self.assertIn("formula_visibility.png", doc_text)
        self.assertIn("Stage 7 / Phase 7.3 - 验收", run_contract)
        self.assertIn("Stage 7 whole-stage review", run_contract)


if __name__ == "__main__":
    unittest.main()
