from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parent
NODE_CANDIDATE = "/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node"
STAGE7_DIR = ROOT / "reports" / "pfi_v024" / "stage_7"
REVIEW_DIR = STAGE7_DIR / "whole_stage_review"
REQUIRED_REPORT_IDS = {
    "net_worth_report",
    "cash_report",
    "investment_report",
    "consumption_report",
    "cashflow_report",
    "data_quality_report",
}


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def node_executable() -> str:
    candidates = [os.environ.get("PFI_NODE"), shutil.which("node"), NODE_CANDIDATE]
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return candidate
    raise AssertionError("Node runtime is required for Stage 7 whole-stage review tests")


def node_json(script: str, *args: str) -> dict[str, object]:
    completed = subprocess.run(
        [node_executable(), "-e", script, *args],
        cwd=REPO_ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    return json.loads(completed.stdout)


class TestV024Stage7WholeReviewContract(unittest.TestCase):
    def test_whole_stage_review_artifacts_exist_and_scope_is_bounded(self) -> None:
        expected_files = [
            ROOT / "docs" / "pfi_v024" / "STAGE7_WHOLE_STAGE_REVIEW.md",
            REVIEW_DIR / "evidence.json",
            REVIEW_DIR / "terminal.log",
            REVIEW_DIR / "changed_files.txt",
            REVIEW_DIR / "risk_and_rollback.md",
            STAGE7_DIR / "phase_7_3" / "formula_visibility.png",
            STAGE7_DIR / "phase_7_3" / "sample_data_quality_report.html",
        ]
        for path in expected_files:
            self.assertTrue(path.exists(), str(path))
            self.assertGreater(path.stat().st_size, 0, str(path))

        evidence = read_json(REVIEW_DIR / "evidence.json")
        self.assertEqual(evidence["schema"], "PFIV024Stage7WholeReviewEvidenceV1")
        self.assertEqual(evidence["target_version"], "v0.2.4")
        self.assertEqual(evidence["source_package_version"], "v0.2.3-repair")
        self.assertEqual(evidence["stage"], "Stage 7")
        self.assertEqual(evidence["review_id"], "stage_7_whole_review")
        self.assertEqual(evidence["current_run_unit"], "Stage 7 whole-stage review")
        self.assertTrue(evidence["current_run_only"])
        self.assertEqual(evidence["status"], "pass")
        self.assertTrue(evidence["stage_7_candidate_complete"])
        self.assertTrue(evidence["stage_7_whole_review_complete"])
        self.assertFalse(evidence["github_main_uploaded"])
        self.assertFalse(evidence["app_bundle_reinstall_executed"])
        self.assertFalse(evidence["data_logic_changes_made"])
        self.assertFalse(evidence["formal_fake_financial_data_added"])
        self.assertIn("GitHub main upload", evidence["explicitly_not_done"])

    def test_phase_evidence_and_quality_gates_prove_stage7_acceptance(self) -> None:
        phase71 = read_json(STAGE7_DIR / "phase_7_1" / "evidence.json")
        phase72 = read_json(STAGE7_DIR / "phase_7_2" / "evidence.json")
        phase73 = read_json(STAGE7_DIR / "phase_7_3" / "evidence.json")
        quality_gate = read_json(STAGE7_DIR / "phase_7_1" / "report_quality_gate.json")
        display_gate = read_json(STAGE7_DIR / "phase_7_2" / "page_display_validation.json")
        acceptance_gate = read_json(STAGE7_DIR / "phase_7_3" / "report_acceptance_gate.json")
        browser = read_json(STAGE7_DIR / "phase_7_3" / "browser_validation.json")
        evidence = read_json(REVIEW_DIR / "evidence.json")

        self.assertEqual(evidence["reviewed_phase_ids"], ["7.1", "7.2", "7.3"])
        self.assertEqual(evidence["phase_statuses"], {
            "phase_7_1": "candidate_pass",
            "phase_7_2": "candidate_pass",
            "phase_7_3": "candidate_pass",
        })
        self.assertTrue(phase71["phase_7_1_complete"])
        self.assertTrue(phase72["phase_7_2_page_display_complete"])
        self.assertTrue(phase73["phase_7_3_acceptance_complete"])
        self.assertEqual(quality_gate["status"], "pass")
        self.assertEqual(display_gate["status"], "pass")
        self.assertEqual(acceptance_gate["status"], "pass")
        self.assertEqual(browser["status"], "pass")
        self.assertEqual(set(quality_gate["missing_report_ids"]), set())
        self.assertEqual(set(display_gate["visible_report_ids"]), REQUIRED_REPORT_IDS)
        self.assertEqual(set(acceptance_gate["visible_report_ids"]), REQUIRED_REPORT_IDS)
        self.assertTrue(acceptance_gate["data_insufficient_report_test_passed"])
        self.assertTrue(acceptance_gate["formula_sample_visible"])
        self.assertTrue(browser["required_terms_visible"])
        self.assertTrue(browser["formula_visibility_screenshot"])
        self.assertGreater(browser["formula_visibility_screenshot_bytes"], 10000)

    def test_runtime_contract_rejects_stage7_stop_conditions(self) -> None:
        report_pack = read_json(STAGE7_DIR / "phase_7_1" / "report_schema.json")
        script = """
const reportsPage = require('./PFI/web/app/pages/reports.js');
const reportPack = JSON.parse(process.argv[1]);
const view = reportsPage.buildV024Stage7Phase72ReportCenterViewModel(reportPack);
const displayGate = reportsPage.validateV024Stage7Phase72ReportCenterViewModel(view);
const acceptanceGate = reportsPage.validateV024Stage7Phase73Acceptance(view);
const invalidView = JSON.parse(JSON.stringify(view));
invalidView.report_cards[0].conclusion_zh = "这是一段 " + "AI" + " 总结，缺少公式、参数、范围和样本量。";
invalidView.report_cards[0].formula_zh = "";
invalidView.report_cards[0].parameters = [];
invalidView.report_cards[0].metric_sources = invalidView.report_cards[0].metric_sources.concat(["mo" + "ck_financial_feed"]);
const invalidGate = reportsPage.validateV024Stage7Phase73Acceptance(invalidView);
console.log(JSON.stringify({ displayGate, acceptanceGate, invalidGate }));
"""
        result = node_json(script, json.dumps(report_pack, ensure_ascii=False))

        self.assertEqual(result["displayGate"]["status"], "pass")
        self.assertEqual(result["acceptanceGate"]["status"], "pass")
        self.assertEqual(result["acceptanceGate"]["ai_paragraph_report_ids"], [])
        self.assertEqual(result["acceptanceGate"]["single_paragraph_report_ids"], [])
        self.assertEqual(result["acceptanceGate"]["forbidden_source_terms"], [])
        self.assertEqual(result["acceptanceGate"]["financial_conclusion_when_blocked"], [])
        self.assertEqual(result["invalidGate"]["status"], "fail")
        self.assertIn("net_worth_report", result["invalidGate"]["ai_paragraph_report_ids"])
        self.assertIn("net_worth_report", result["invalidGate"]["single_paragraph_report_ids"])

    def test_stop_conditions_are_recorded_as_absent(self) -> None:
        evidence = read_json(REVIEW_DIR / "evidence.json")
        stop_conditions = evidence["stop_condition_audit"]

        self.assertEqual(stop_conditions["report_missing_formula_or_sample_size"], "absent")
        self.assertEqual(stop_conditions["single_ai_paragraph_report"], "absent")
        self.assertEqual(stop_conditions["data_insufficient_full_financial_conclusion"], "absent")
        self.assertEqual(stop_conditions["report_numbers_from_forbidden_source"], "absent")
        self.assertEqual(evidence["acceptance_checks"]["six_report_types_visible"]["result"], "pass")
        self.assertEqual(evidence["acceptance_checks"]["data_quality_report_generated"]["result"], "pass")
        self.assertEqual(evidence["acceptance_checks"]["formula_parameter_range_sample_visible"]["result"], "pass")
        self.assertEqual(evidence["acceptance_checks"]["no_forbidden_financial_data_added"]["result"], "pass")

    def test_review_findings_are_recorded_and_fixed_before_upload(self) -> None:
        evidence = read_json(REVIEW_DIR / "evidence.json")
        findings = evidence["review_findings"]

        self.assertGreaterEqual(len(findings), 3)
        for finding in findings:
            self.assertIn(finding["severity"], {"P1", "P2", "P3"})
            self.assertEqual(finding["status"], "fixed")
            self.assertTrue(finding["fix"])
            self.assertTrue(finding["verification"])

        command_status = {item["cmd"]: item["status"] for item in evidence["commands"]}
        self.assertEqual(command_status["pytest stage7 whole review red run"], "expected_fail")
        self.assertEqual(command_status["pytest stage7 whole review contract"], "pass")
        self.assertEqual(command_status["pytest stage7 phase regression"], "pass")
        self.assertEqual(command_status["node stage7 phase73 browser validation"], "pass")
        self.assertEqual(command_status["pytest stage6 adjacent regression"], "pass")
        self.assertEqual(command_status["node syntax checks"], "pass")
        self.assertEqual(command_status["json evidence checks"], "pass")
        self.assertEqual(command_status["git diff --check -- PFI"], "pass")

        self.assertFalse(evidence["github_main_uploaded"])
        self.assertIn("GitHub main upload", evidence["remaining_gates"])


if __name__ == "__main__":
    unittest.main()
