from __future__ import annotations

import importlib
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
PHASE_DIR = ROOT / "reports" / "pfi_v024" / "stage_8" / "phase_8_1"
EXPECTED_PRIMARY_LABELS = [
    "首页总览",
    "账户与资产",
    "账本流水",
    "投资管理",
    "消费管理",
    "数据源与上传",
    "建议与复盘",
    "报告与洞察",
    "市场与研究",
    "设置",
]
EXPECTED_TASK_IDS = ["T8.1.1", "T8.1.2", "T8.1.3", "T8.1.4"]


def load_stage8_module():
    try:
        return importlib.import_module("pfi_v02.stage_v024_stage8_e2e_acceptance")
    except ModuleNotFoundError:
        return None


class TestV024Stage8Phase81E2EAutoAcceptance(unittest.TestCase):
    def test_phase81_contract_is_current_phase_only(self) -> None:
        stage8 = load_stage8_module()
        self.assertIsNotNone(stage8, "stage_v024_stage8_e2e_acceptance module is required")
        self.assertTrue(hasattr(stage8, "build_v024_stage8_phase81_contract"))

        contract = stage8.build_v024_stage8_phase81_contract().to_dict()

        self.assertEqual(contract["target_version"], "v0.2.4")
        self.assertEqual(contract["source_package_version"], "v0.2.3-repair")
        self.assertEqual(contract["stage"], "Stage 8")
        self.assertEqual(contract["stage_name"], "端到端浏览器与 app 验收")
        self.assertEqual(contract["phase_id"], "8.1")
        self.assertEqual(contract["phase_name"], "自动验收")
        self.assertTrue(contract["current_phase_only"])
        self.assertTrue(contract["max_one_phase_per_run"])
        self.assertTrue(contract["stage_7_github_main_uploaded_required"])
        self.assertEqual(contract["task_ids"], EXPECTED_TASK_IDS)
        self.assertIn("route_click_test", contract["automated_checks"])
        self.assertIn("entry_version_test", contract["automated_checks"])
        self.assertIn("data_state_test", contract["automated_checks"])
        self.assertIn("report_center_test", contract["automated_checks"])
        self.assertFalse(contract["phase_8_2_started"])
        self.assertFalse(contract["phase_8_3_started"])
        self.assertFalse(contract["stage_8_whole_review_complete"])
        self.assertFalse(contract["github_main_uploaded"])
        self.assertFalse(contract["stage_9_started"])
        self.assertIn("Phase 8.2 screenshot acceptance", contract["explicitly_not_done"])
        self.assertIn("Phase 8.3 manual acceptance", contract["explicitly_not_done"])
        self.assertIn("Stage 8 whole-stage review", contract["explicitly_not_done"])
        self.assertIn("Stage 9 regression freeze", contract["explicitly_not_done"])
        self.assertIn("GitHub main upload", contract["explicitly_not_done"])
        self.assertIn("node PFI/scripts/validate_v024_stage8_phase81_e2e_auto.js", contract["validation_commands"])

    def test_phase81_evidence_pack_is_machine_readable(self) -> None:
        paths = [
            PHASE_DIR / "evidence.json",
            PHASE_DIR / "browser_validation.json",
            PHASE_DIR / "route_click_validation.json",
            PHASE_DIR / "entry_version_validation.json",
            PHASE_DIR / "data_state_validation.json",
            PHASE_DIR / "report_center_validation.json",
            PHASE_DIR / "terminal.log",
            PHASE_DIR / "changed_files.txt",
            PHASE_DIR / "risk_and_rollback.md",
        ]
        for path in paths:
            self.assertTrue(path.exists(), str(path))
            self.assertGreater(path.stat().st_size, 0, str(path))

        evidence = json.loads((PHASE_DIR / "evidence.json").read_text(encoding="utf-8"))
        changed_files = [
            line.strip()
            for line in (PHASE_DIR / "changed_files.txt").read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

        self.assertEqual(evidence["schema"], "PFIV024Stage8Phase81EvidenceV1")
        self.assertEqual(evidence["target_version"], "v0.2.4")
        self.assertEqual(evidence["source_package_version"], "v0.2.3-repair")
        self.assertEqual(evidence["stage"], "Stage 8")
        self.assertEqual(evidence["phase_id"], "8.1")
        self.assertEqual(evidence["status"], "candidate_pass")
        self.assertTrue(evidence["current_phase_only"])
        self.assertEqual(evidence["task_ids"], EXPECTED_TASK_IDS)
        self.assertTrue(evidence["stage_7_github_main_uploaded_required"])
        self.assertTrue(evidence["stage_7_github_main_uploaded_verified"])
        self.assertTrue(evidence["route_click_test_passed"])
        self.assertTrue(evidence["entry_version_test_passed"])
        self.assertTrue(evidence["data_state_test_passed"])
        self.assertTrue(evidence["report_center_test_passed"])
        self.assertFalse(evidence["phase_8_2_started"])
        self.assertFalse(evidence["phase_8_3_started"])
        self.assertFalse(evidence["stage_8_whole_review_complete"])
        self.assertFalse(evidence["github_main_uploaded"])
        self.assertFalse(evidence["stage_9_started"])
        self.assertFalse(evidence["app_bundle_reinstall_executed"])
        self.assertFalse(evidence["data_logic_changes_made"])
        self.assertFalse(evidence["formal_fake_financial_data_added"])
        self.assertEqual(evidence["changed_files"], changed_files)

    def test_browser_validation_covers_phase81_tasks(self) -> None:
        browser = json.loads((PHASE_DIR / "browser_validation.json").read_text(encoding="utf-8"))
        route = json.loads((PHASE_DIR / "route_click_validation.json").read_text(encoding="utf-8"))
        entry = json.loads((PHASE_DIR / "entry_version_validation.json").read_text(encoding="utf-8"))
        data_state = json.loads((PHASE_DIR / "data_state_validation.json").read_text(encoding="utf-8"))
        reports = json.loads((PHASE_DIR / "report_center_validation.json").read_text(encoding="utf-8"))

        self.assertEqual(browser["schema"], "PFIV024Stage8Phase81BrowserValidationV1")
        self.assertEqual(browser["status"], "pass")
        self.assertTrue(browser["automated_only"])
        self.assertTrue(browser["route_click_test_passed"])
        self.assertTrue(browser["entry_version_test_passed"])
        self.assertTrue(browser["data_state_test_passed"])
        self.assertTrue(browser["report_center_test_passed"])
        self.assertTrue(browser["history_back_forward_passed"])
        self.assertEqual(browser["console_errors"], [])
        self.assertEqual(browser["page_errors"], [])
        self.assertEqual(browser["http_errors"], [])

        self.assertEqual(route["status"], "pass")
        self.assertEqual(route["primary_entry_count"], 10)
        self.assertEqual(route["primary_labels"], EXPECTED_PRIMARY_LABELS)
        self.assertGreaterEqual(route["core_secondary_route_count"], 10)
        self.assertTrue(route["all_primary_routes_clicked"])
        self.assertTrue(route["all_core_secondary_routes_clicked"])

        self.assertEqual(entry["status"], "pass")
        self.assertEqual(entry["target_version"], "v0.2.4")
        self.assertEqual(entry["source_package_version"], "v0.2.3-repair")
        self.assertEqual(entry["repair_label"], "PFI v0.2.3 Repair")
        self.assertEqual(entry["build_id"], "pfi-v024-stage2-phase22")
        self.assertEqual(entry["ui_contract_version"], "PFI-V024-STAGE2-ENTRY-CONSISTENCY")
        self.assertTrue(entry["web_bundle_hash_present"])

        self.assertEqual(data_state["status"], "pass")
        self.assertEqual(data_state["source_record_count"], 8815)
        self.assertEqual(data_state["source_raw_file_count"], 4)
        self.assertEqual(data_state["source_date_range"], {"start": "2022-06-06", "end": "2026-06-03"})
        self.assertFalse(data_state["false_financial_zero_visible"])
        self.assertIn("net_worth_cny", data_state["blocked_metric_ids"])
        self.assertIn("cash_balance_cny", data_state["blocked_metric_ids"])
        self.assertIn("investment_market_value_cny", data_state["blocked_metric_ids"])

        self.assertEqual(reports["status"], "pass")
        self.assertEqual(reports["report_count"], 6)
        self.assertEqual(set(reports["visible_report_ids"]), {
            "net_worth_report",
            "cash_report",
            "investment_report",
            "consumption_report",
            "cashflow_report",
            "data_quality_report",
        })
        self.assertTrue(reports["formula_visible"])
        self.assertTrue(reports["parameters_and_sample_visible"])
        self.assertTrue(reports["data_range_visible"])
        self.assertTrue(reports["gaps_and_review_visible"])
        self.assertFalse(reports["full_financial_conclusion_when_blocked"])

    def test_phase81_boundary_docs_are_updated_without_starting_later_phases(self) -> None:
        doc = (ROOT / "docs" / "pfi_v024" / "STAGE8_E2E_ACCEPTANCE.md").read_text(encoding="utf-8")
        run_contract = (ROOT / "docs" / "pfi_v024" / "RUN_CONTRACT.md").read_text(encoding="utf-8")

        self.assertIn("Stage 8 Phase 8.1", doc)
        self.assertIn("自动验收", doc)
        self.assertIn("route_click_validation.json", doc)
        self.assertIn("entry_version_validation.json", doc)
        self.assertIn("data_state_validation.json", doc)
        self.assertIn("report_center_validation.json", doc)
        self.assertIn("Stage 8 / Phase 8.2 - 截图验收", run_contract)
        self.assertIn("不执行 Phase 8.3", run_contract)
        self.assertIn("不执行 Stage 9", run_contract)
        self.assertNotIn("Stage 8 whole-stage review complete", doc)


if __name__ == "__main__":
    unittest.main()
