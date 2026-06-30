from __future__ import annotations

import json
from pathlib import Path
import unittest

import pfi_v02.stage_v024_stage3_navigation as navigation


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_DIR = ROOT / "reports" / "pfi_v024" / "stage_3" / "phase_3_3"
SCRIPT_PATH = ROOT / "scripts" / "validate_v024_stage3_phase33_browser.js"

OFFICIAL_PRIMARY_LABELS = [
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

LEGACY_ALIAS_CASES = [
    ("/home/today", "/home", "home"),
    ("/market/watch", "/market-research?tab=market", "market_research"),
    ("/market/research", "/market-research?tab=research", "market_research"),
    ("/investment/holdings", "/investment?tab=holdings", "investment"),
    ("/market/lab", "/market-research/strategy-lab", "market_research"),
    ("/settings/data", "/settings?tab=data-system", "settings"),
]


class TestV024Stage3Phase33NavigationAcceptance(unittest.TestCase):
    def test_phase33_python_contract_declares_navigation_acceptance_scope(self) -> None:
        self.assertTrue(hasattr(navigation, "build_v024_stage3_phase33_contract"))

        contract = navigation.build_v024_stage3_phase33_contract().to_dict()

        self.assertEqual(contract["target_version"], "v0.2.4")
        self.assertEqual(contract["source_package_version"], "v0.2.3-repair")
        self.assertEqual(contract["stage_id"], "Stage 3")
        self.assertEqual(contract["phase_id"], "3.3")
        self.assertEqual(contract["phase_name"], "导航验收")
        self.assertEqual(contract["task_ids"], ["T3.3.1", "T3.3.2", "T3.3.3"])
        self.assertTrue(contract["phase_3_1_complete"])
        self.assertTrue(contract["phase_3_2_complete"])
        self.assertTrue(contract["phase_3_3_complete"])
        self.assertTrue(contract["stage_3_candidate_complete"])
        self.assertFalse(contract["stage_3_complete"])
        self.assertTrue(contract["browser_history_validation_done"])
        self.assertFalse(contract["github_main_upload_allowed"])
        self.assertEqual(contract["max_phases_per_run"], 1)
        self.assertEqual(contract["official_primary_entry_count"], 10)
        self.assertEqual(contract["desktop_primary_entry_count"], 10)
        self.assertEqual(contract["mobile_primary_entry_count"], 10)
        self.assertEqual(contract["legacy_alias_route_count"], 6)
        self.assertEqual(contract["evidence_files"], [
            "browser_validation.json",
            "legacy_routes_validation.json",
            "desktop_nav.png",
            "browser_back_after_forward.png",
        ])

    def test_phase33_browser_validation_script_is_present(self) -> None:
        self.assertTrue(SCRIPT_PATH.exists(), str(SCRIPT_PATH))
        script_text = SCRIPT_PATH.read_text(encoding="utf-8")

        self.assertIn("PFI-V024-STAGE3-PHASE33-BROWSER-NAVIGATION", script_text)
        self.assertIn("chromium.launch", script_text)
        self.assertIn("data-primary-entry", script_text)
        self.assertIn("goBack", script_text)
        self.assertIn("goForward", script_text)
        self.assertIn("browser_validation.json", script_text)
        self.assertIn("legacy_routes_validation.json", script_text)

    def test_phase33_browser_evidence_records_dom_alias_and_history_acceptance(self) -> None:
        evidence_path = EVIDENCE_DIR / "evidence.json"
        browser_path = EVIDENCE_DIR / "browser_validation.json"
        legacy_path = EVIDENCE_DIR / "legacy_routes_validation.json"
        changed_files_path = EVIDENCE_DIR / "changed_files.txt"
        terminal_path = EVIDENCE_DIR / "terminal.log"
        risk_path = EVIDENCE_DIR / "risk_and_rollback.md"
        desktop_nav = EVIDENCE_DIR / "screenshots" / "desktop_nav.png"
        browser_back = EVIDENCE_DIR / "screenshots" / "browser_back_after_forward.png"
        doc_path = ROOT / "docs" / "pfi_v024" / "STAGE3_NAVIGATION_ROUTING.md"

        for path in (
            evidence_path,
            browser_path,
            legacy_path,
            changed_files_path,
            terminal_path,
            risk_path,
            desktop_nav,
            browser_back,
            doc_path,
        ):
            self.assertTrue(path.exists(), str(path))

        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        browser = json.loads(browser_path.read_text(encoding="utf-8"))
        legacy = json.loads(legacy_path.read_text(encoding="utf-8"))
        changed_files = [line.strip() for line in changed_files_path.read_text(encoding="utf-8").splitlines() if line.strip()]

        self.assertEqual(evidence["schema"], "PFIV024Stage3Phase33BrowserNavigationEvidenceV1")
        self.assertEqual(evidence["target_version"], "v0.2.4")
        self.assertEqual(evidence["stage"], "Stage 3")
        self.assertEqual(evidence["phase_id"], "3.3")
        self.assertEqual(evidence["phase_name"], "导航验收")
        self.assertEqual(evidence["status"], "candidate_pass")
        self.assertTrue(evidence["current_phase_only"])
        self.assertTrue(evidence["max_one_phase_per_run"])
        self.assertEqual(evidence["changed_files"], changed_files)
        self.assertTrue(evidence["phase_3_1_complete"])
        self.assertTrue(evidence["phase_3_2_complete"])
        self.assertTrue(evidence["phase_3_3_complete"])
        self.assertTrue(evidence["stage_3_candidate_complete"])
        self.assertFalse(evidence["stage_3_complete"])
        self.assertFalse(evidence["github_main_uploaded"])
        self.assertTrue(evidence["acceptance_checks"]["dom_primary_entries_are_10"])
        self.assertTrue(evidence["acceptance_checks"]["legacy_alias_routes_resolve"])
        self.assertTrue(evidence["acceptance_checks"]["browser_back_forward_passed"])
        self.assertTrue(evidence["acceptance_checks"]["direct_url_alias_passed"])
        self.assertFalse(evidence["app_bundle_changes_made"])
        self.assertFalse(evidence["data_logic_changes_made"])
        self.assertFalse(evidence["formal_fake_financial_data_added"])
        self.assertIn("Stage 3 whole-stage review", evidence["explicitly_not_done"])
        self.assertIn("GitHub main upload", evidence["explicitly_not_done"])

        self.assertEqual(browser["contract"], "PFI-V024-STAGE3-PHASE33-BROWSER-NAVIGATION")
        self.assertEqual(browser["desktop_primary_count"], 10)
        self.assertEqual(browser["mobile_primary_count"], 10)
        self.assertEqual(browser["desktop_primary_labels"], OFFICIAL_PRIMARY_LABELS)
        self.assertEqual(browser["market_research_index"], 9)
        self.assertTrue(browser["legacy_labels_absent_as_primary_exact"])
        self.assertTrue(browser["click_navigation_passed"])
        self.assertTrue(browser["back_forward_passed"])
        self.assertTrue(browser["direct_url_alias_passed"])
        self.assertEqual(browser["console_errors"], [])
        self.assertEqual(browser["page_errors"], [])
        self.assertTrue(browser["screenshots"]["desktop_nav"].endswith("desktop_nav.png"))
        self.assertTrue(browser["screenshots"]["browser_back_after_forward"].endswith("browser_back_after_forward.png"))

        self.assertEqual(len(legacy["cases"]), len(LEGACY_ALIAS_CASES))
        for route_alias, resolved_route, workspace in LEGACY_ALIAS_CASES:
            with self.subTest(route_alias=route_alias):
                case = legacy["cases"][route_alias]
                self.assertEqual(case["status"], "resolved")
                self.assertEqual(case["routeAlias"], resolved_route)
                self.assertEqual(case["workspace"], workspace)
                self.assertEqual(case["routeType"], "legacy_redirect")


if __name__ == "__main__":
    unittest.main()
