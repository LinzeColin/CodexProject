from __future__ import annotations

import json
import unittest
from importlib import import_module
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_DIR = ROOT / "reports" / "pfi_v024" / "stage_2" / "phase_2_3"
START_COMMAND = ROOT / "StartPFI.command"
START_SCRIPT = ROOT / "scripts" / "startPFI.sh"

EXPECTED_REPAIR_LABEL = "PFI v0.2.3 Repair"
EXPECTED_BUILD_ID = "pfi-v024-stage2-phase22"
EXPECTED_UI_CONTRACT = "PFI-V024-STAGE2-ENTRY-CONSISTENCY"
EXPECTED_BUNDLE_HASH_PATH = ROOT / "reports" / "pfi_v024" / "stage_2" / "phase_2_2" / "bundle_hash.txt"
EXPECTED_PROJECT_ROOT = str(ROOT)


def load_entry_consistency_module():
    return import_module("pfi_v02.stage_v024_stage2_entry_consistency")


class TestV024Stage2Phase23RealEntryValidation(unittest.TestCase):
    def test_phase23_contract_declares_real_app_browser_validation_scope(self) -> None:
        entry_consistency = load_entry_consistency_module()
        self.assertTrue(hasattr(entry_consistency, "build_v024_stage2_phase23_contract"))

        contract = entry_consistency.build_v024_stage2_phase23_contract().to_dict()

        self.assertEqual(contract["target_version"], "v0.2.4")
        self.assertEqual(contract["source_package_version"], "v0.2.3-repair")
        self.assertEqual(contract["stage_id"], "Stage 2")
        self.assertEqual(contract["phase_id"], "2.3")
        self.assertEqual(contract["phase_name"], "实机验收")
        self.assertEqual(contract["task_ids"], ["T2.3.1", "T2.3.2", "T2.3.3", "T2.3.4"])
        self.assertTrue(contract["phase_2_1_complete"])
        self.assertTrue(contract["phase_2_2_complete"])
        self.assertTrue(contract["phase_2_3_complete"])
        self.assertTrue(contract["stage_2_candidate_complete"])
        self.assertFalse(contract["stage_2_complete"])
        self.assertEqual(contract["max_phases_per_run"], 1)
        self.assertFalse(contract["app_bundle_changes_allowed"])
        self.assertFalse(contract["app_bundle_reinstall_allowed"])
        self.assertFalse(contract["data_logic_changes_allowed"])
        self.assertFalse(contract["github_main_upload_allowed"])
        self.assertEqual(
            contract["validation_paths"],
            ["localhost", "app", "clear_cache", "new_profile"],
        )

    def test_phase23_launchers_do_not_reuse_stale_same_cwd_service(self) -> None:
        launcher_sources = "\n".join(
            (
                START_COMMAND.read_text(encoding="utf-8"),
                START_SCRIPT.read_text(encoding="utf-8"),
            )
        )

        self.assertIn("pfi_active_service.env", launcher_sources)
        self.assertIn("PFI_ACTIVE_BUILD_ID", launcher_sources)
        self.assertIn(EXPECTED_BUILD_ID, launcher_sources)
        self.assertIn(EXPECTED_UI_CONTRACT, launcher_sources)
        self.assertIn("active_service_url_if_current_build", launcher_sources)

    def test_phase23_evidence_pack_and_screenshots_exist(self) -> None:
        required_paths = [
            EVIDENCE_DIR / "evidence.json",
            EVIDENCE_DIR / "browser_validation.json",
            EVIDENCE_DIR / "bundle_hash.txt",
            EVIDENCE_DIR / "changed_files.txt",
            EVIDENCE_DIR / "terminal.log",
            EVIDENCE_DIR / "risk_and_rollback.md",
            EVIDENCE_DIR / "screenshots" / "localhost_home.png",
            EVIDENCE_DIR / "screenshots" / "app_home.png",
            EVIDENCE_DIR / "screenshots" / "clear_cache_home.png",
            EVIDENCE_DIR / "screenshots" / "new_profile_home.png",
        ]
        for path in required_paths:
            self.assertTrue(path.exists(), str(path))

        for screenshot in required_paths[-4:]:
            self.assertGreater(screenshot.stat().st_size, 20_000, str(screenshot))

    def test_phase23_browser_validation_proves_four_entry_paths_match_current_bundle(self) -> None:
        browser_validation = json.loads((EVIDENCE_DIR / "browser_validation.json").read_text(encoding="utf-8"))
        expected_bundle_hash = EXPECTED_BUNDLE_HASH_PATH.read_text(encoding="utf-8").strip()

        self.assertEqual(browser_validation["schema"], "PFIV024Stage2Phase23BrowserValidationV1")
        self.assertEqual(browser_validation["phase_id"], "2.3")
        self.assertEqual(browser_validation["status"], "candidate_pass")
        self.assertEqual(browser_validation["service"]["health"], "ok")
        self.assertEqual(browser_validation["service"]["project_root"], EXPECTED_PROJECT_ROOT)
        self.assertRegex(browser_validation["service"]["url"], r"^http://127\.0\.0\.1:85\d{2}$")
        self.assertEqual(browser_validation["disk_runtime_metadata"]["webBundleHash"], expected_bundle_hash)

        paths = browser_validation["paths"]
        self.assertEqual(set(paths), {"localhost", "app", "clear_cache", "new_profile"})
        for path_name, payload in paths.items():
            with self.subTest(path_name=path_name):
                audit = payload["entry_audit"]
                self.assertTrue(payload["ok"])
                self.assertEqual(audit["repairLabel"], EXPECTED_REPAIR_LABEL)
                self.assertEqual(audit["buildId"], EXPECTED_BUILD_ID)
                self.assertEqual(audit["uiContractVersion"], EXPECTED_UI_CONTRACT)
                self.assertEqual(audit["webBundleHash"], expected_bundle_hash)
                self.assertEqual(payload["visible_entry_strip"]["repair_label"], EXPECTED_REPAIR_LABEL)
                self.assertIn(EXPECTED_BUILD_ID, payload["visible_entry_strip"]["build_id"])
                self.assertIn(EXPECTED_UI_CONTRACT, payload["visible_entry_strip"]["ui_contract"])
                self.assertGreater(payload["screenshot"]["bytes"], 20_000)
                self.assertTrue(payload["url"].startswith(browser_validation["service"]["url"]))
                self.assertNotIn("20260629-stage1", payload["html_signature_sample"])
                self.assertNotIn("PFI-V023-STAGE1-APP-ENTRY-BUNDLE-CONSISTENCY", payload["html_signature_sample"])

        app_entry = browser_validation["paths"]["app"]
        self.assertEqual(app_entry["app_binding"]["applications_project_root"], EXPECTED_PROJECT_ROOT)
        self.assertEqual(app_entry["app_binding"]["downloads_project_root"], EXPECTED_PROJECT_ROOT)
        self.assertEqual(app_entry["app_binding"]["desktop_project_root"], EXPECTED_PROJECT_ROOT)
        self.assertTrue(app_entry["app_binding"]["dry_run_exit_codes_ok"])
        self.assertTrue(browser_validation["all_paths_same_bundle_hash"])
        self.assertTrue(browser_validation["all_paths_same_build_id"])
        self.assertEqual(browser_validation["console_errors"], [])
        self.assertEqual(browser_validation["page_errors"], [])
        self.assertEqual(browser_validation["http_errors"], [])

    def test_phase23_evidence_records_boundaries_and_validation_results(self) -> None:
        evidence = json.loads((EVIDENCE_DIR / "evidence.json").read_text(encoding="utf-8"))
        changed_files = [
            line.strip()
            for line in (EVIDENCE_DIR / "changed_files.txt").read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

        self.assertEqual(evidence["schema"], "PFIV024Stage2Phase23EvidenceV1")
        self.assertEqual(evidence["phase_id"], "2.3")
        self.assertEqual(evidence["phase_name"], "实机验收")
        self.assertEqual(evidence["status"], "candidate_pass")
        self.assertEqual(evidence["changed_files"], changed_files)
        self.assertTrue(evidence["phase_2_1_complete"])
        self.assertTrue(evidence["phase_2_2_complete"])
        self.assertTrue(evidence["phase_2_3_complete"])
        self.assertTrue(evidence["stage_2_candidate_complete"])
        self.assertFalse(evidence["stage_2_complete"])
        self.assertFalse(evidence["app_bundle_changes_made"])
        self.assertFalse(evidence["app_bundle_reinstall_executed"])
        self.assertFalse(evidence["data_logic_changes_made"])
        self.assertFalse(evidence["github_main_uploaded"])
        self.assertIn("Stage 2 whole-stage review", evidence["explicitly_not_done"])
        self.assertIn("GitHub main upload", evidence["explicitly_not_done"])
        self.assertEqual(evidence["validation_results"]["browser_validation"], "pass")


if __name__ == "__main__":
    unittest.main()
