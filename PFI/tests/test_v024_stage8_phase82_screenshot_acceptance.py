from __future__ import annotations

import importlib
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
PHASE_DIR = ROOT / "reports" / "pfi_v024" / "stage_8" / "phase_8_2"
SCREENSHOT_DIR = PHASE_DIR / "screenshots"
EXPECTED_TASK_IDS = ["T8.2.1", "T8.2.2", "T8.2.3", "T8.2.4"]
EXPECTED_PRIMARY_SCREENSHOT_IDS = [
    "primary_01_home",
    "primary_02_accounts",
    "primary_03_ledger",
    "primary_04_investment",
    "primary_05_consumption",
    "primary_06_sources_upload",
    "primary_07_review",
    "primary_08_reports",
    "primary_09_market_research",
    "primary_10_settings",
]


def load_stage8_module():
    try:
        return importlib.import_module("pfi_v02.stage_v024_stage8_e2e_acceptance")
    except ModuleNotFoundError:
        return None


class TestV024Stage8Phase82ScreenshotAcceptance(unittest.TestCase):
    def test_phase82_contract_is_current_phase_only(self) -> None:
        stage8 = load_stage8_module()
        self.assertIsNotNone(stage8, "stage_v024_stage8_e2e_acceptance module is required")
        self.assertTrue(hasattr(stage8, "build_v024_stage8_phase82_contract"))

        contract = stage8.build_v024_stage8_phase82_contract().to_dict()

        self.assertEqual(contract["target_version"], "v0.2.4")
        self.assertEqual(contract["source_package_version"], "v0.2.3-repair")
        self.assertEqual(contract["stage"], "Stage 8")
        self.assertEqual(contract["stage_name"], "端到端浏览器与 app 验收")
        self.assertEqual(contract["phase_id"], "8.2")
        self.assertEqual(contract["phase_name"], "截图验收")
        self.assertTrue(contract["current_phase_only"])
        self.assertTrue(contract["max_one_phase_per_run"])
        self.assertTrue(contract["phase_8_1_required"])
        self.assertEqual(contract["task_ids"], EXPECTED_TASK_IDS)
        self.assertEqual(contract["required_screenshot_groups"], ["app", "localhost", "primary_entries", "mobile"])
        self.assertFalse(contract["phase_8_3_started"])
        self.assertFalse(contract["stage_8_whole_review_complete"])
        self.assertFalse(contract["github_main_uploaded"])
        self.assertFalse(contract["stage_9_started"])
        self.assertFalse(contract["app_bundle_changes_allowed"])
        self.assertFalse(contract["data_logic_changes_allowed"])
        self.assertIn("Phase 8.3 manual acceptance", contract["explicitly_not_done"])
        self.assertIn("Stage 8 whole-stage review", contract["explicitly_not_done"])
        self.assertIn("Stage 9 regression freeze", contract["explicitly_not_done"])
        self.assertIn("GitHub main upload", contract["explicitly_not_done"])
        self.assertIn("node PFI/scripts/validate_v024_stage8_phase82_screenshots.js", contract["validation_commands"])

    def test_phase82_evidence_pack_is_machine_readable(self) -> None:
        paths = [
            PHASE_DIR / "evidence.json",
            PHASE_DIR / "browser_validation.json",
            PHASE_DIR / "screenshot_index.json",
            PHASE_DIR / "app_entry_validation.json",
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

        self.assertEqual(evidence["schema"], "PFIV024Stage8Phase82EvidenceV1")
        self.assertEqual(evidence["target_version"], "v0.2.4")
        self.assertEqual(evidence["source_package_version"], "v0.2.3-repair")
        self.assertEqual(evidence["stage"], "Stage 8")
        self.assertEqual(evidence["phase_id"], "8.2")
        self.assertEqual(evidence["status"], "candidate_pass")
        self.assertTrue(evidence["current_phase_only"])
        self.assertTrue(evidence["phase_8_1_verified"])
        self.assertEqual(evidence["task_ids"], EXPECTED_TASK_IDS)
        self.assertTrue(evidence["app_screenshot_captured"])
        self.assertTrue(evidence["localhost_screenshot_captured"])
        self.assertEqual(evidence["primary_entry_screenshot_count"], 10)
        self.assertTrue(evidence["mobile_responsive_screenshot_captured"])
        self.assertTrue(evidence["app_localhost_same_bundle_hash"])
        self.assertFalse(evidence["phase_8_3_started"])
        self.assertFalse(evidence["stage_8_whole_review_complete"])
        self.assertFalse(evidence["github_main_uploaded"])
        self.assertFalse(evidence["stage_9_started"])
        self.assertFalse(evidence["app_bundle_reinstall_executed"])
        self.assertFalse(evidence["data_logic_changes_made"])
        self.assertFalse(evidence["formal_fake_financial_data_added"])
        self.assertEqual(evidence["changed_files"], changed_files)

    def test_screenshot_index_covers_app_localhost_primary_and_mobile(self) -> None:
        index = json.loads((PHASE_DIR / "screenshot_index.json").read_text(encoding="utf-8"))
        self.assertEqual(index["schema"], "PFIV024Stage8Phase82ScreenshotIndexV1")
        self.assertEqual(index["status"], "pass")
        self.assertEqual(index["screenshot_count"], len(index["screenshots"]))
        self.assertGreaterEqual(index["screenshot_count"], 13)

        by_id = {item["screenshot_id"]: item for item in index["screenshots"]}
        for screenshot_id in ["app_home", "localhost_home", "mobile_responsive", "desktop_all_pages", *EXPECTED_PRIMARY_SCREENSHOT_IDS]:
            self.assertIn(screenshot_id, by_id)
            item = by_id[screenshot_id]
            path = ROOT.parent / item["path"]
            self.assertTrue(path.exists(), item["path"])
            self.assertEqual(path.stat().st_size, item["bytes"], item["path"])
            self.assertGreater(item["bytes"], 20_000, item["path"])
            self.assertRegex(item["sha256"], r"^[0-9a-f]{64}$")

        primary_items = [item for item in index["screenshots"] if item["group"] == "primary_entries"]
        self.assertEqual(len(primary_items), 10)
        self.assertEqual([item["screenshot_id"] for item in primary_items], EXPECTED_PRIMARY_SCREENSHOT_IDS)
        self.assertEqual(index["groups"]["app"]["count"], 1)
        self.assertEqual(index["groups"]["localhost"]["count"], 1)
        self.assertEqual(index["groups"]["primary_entries"]["count"], 10)
        self.assertGreaterEqual(index["groups"]["mobile"]["count"], 1)
        self.assertEqual(index["groups"]["desktop_all_pages"]["count"], 1)
        self.assertGreater(by_id["desktop_all_pages"]["bytes"], 100_000)

    def test_browser_validation_proves_version_hash_and_visual_health(self) -> None:
        browser = json.loads((PHASE_DIR / "browser_validation.json").read_text(encoding="utf-8"))
        app_entry = json.loads((PHASE_DIR / "app_entry_validation.json").read_text(encoding="utf-8"))

        self.assertEqual(browser["schema"], "PFIV024Stage8Phase82BrowserValidationV1")
        self.assertEqual(browser["status"], "pass")
        self.assertEqual(browser["phase_id"], "8.2")
        self.assertTrue(browser["app_screenshot_captured"])
        self.assertTrue(browser["localhost_screenshot_captured"])
        self.assertEqual(browser["primary_entry_screenshot_count"], 10)
        self.assertTrue(browser["mobile_responsive_screenshot_captured"])
        self.assertTrue(browser["app_localhost_same_bundle_hash"])
        self.assertTrue(browser["desktop_light_ui"])
        self.assertEqual(browser["mobile_horizontal_overflow_px"], 0)
        self.assertEqual(browser["console_errors"], [])
        self.assertEqual(browser["page_errors"], [])
        self.assertEqual(browser["http_errors"], [])
        self.assertFalse(browser["phase_8_3_started"])
        self.assertFalse(browser["stage_9_started"])

        self.assertEqual(app_entry["status"], "pass")
        self.assertEqual(app_entry["target_version"], "v0.2.4")
        self.assertEqual(app_entry["source_package_version"], "v0.2.3-repair")
        self.assertEqual(app_entry["build_id"], "pfi-v024-stage2-phase22")
        self.assertEqual(app_entry["ui_contract_version"], "PFI-V024-STAGE2-ENTRY-CONSISTENCY")
        self.assertTrue(app_entry["app_localhost_same_bundle_hash"])
        self.assertTrue(app_entry["selected_app_points_to_current_checkout"])
        self.assertIn(app_entry["selected_app_path"], ["/Applications/PFI.app", str(Path.home() / "Downloads" / "PFI.app")])

    def test_phase82_docs_do_not_claim_manual_acceptance_or_upload(self) -> None:
        doc = (ROOT / "docs" / "pfi_v024" / "STAGE8_E2E_ACCEPTANCE.md").read_text(encoding="utf-8")
        run_contract = (ROOT / "docs" / "pfi_v024" / "RUN_CONTRACT.md").read_text(encoding="utf-8")

        self.assertIn("Stage 8 Phase 8.2", doc)
        self.assertIn("截图验收", doc)
        self.assertIn("screenshot_index.json", doc)
        self.assertIn("app_home.png", doc)
        self.assertIn("localhost_home.png", doc)
        self.assertIn("mobile_responsive.png", doc)
        self.assertIn("Stage 8 / Phase 8.2 - 截图验收", run_contract)
        self.assertIn("不执行 Phase 8.3", run_contract)
        self.assertIn("不执行 Stage 9", run_contract)
        self.assertNotIn("用户已验收", doc)
        self.assertNotIn("Stage 8 whole-stage review complete", doc)


if __name__ == "__main__":
    unittest.main()
