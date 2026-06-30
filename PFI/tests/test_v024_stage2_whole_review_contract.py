from __future__ import annotations

import json
import unittest
from pathlib import Path

import pfi_v02.stage_v024_stage2_entry_consistency as entry_consistency


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_DIR = ROOT / "reports" / "pfi_v024" / "stage_2" / "whole_stage_review"
PHASE_23_DIR = ROOT / "reports" / "pfi_v024" / "stage_2" / "phase_2_3"


class TestV024Stage2WholeReviewContract(unittest.TestCase):
    def test_whole_review_contract_closes_stage2_without_stage3_or_upload(self) -> None:
        contract = entry_consistency.build_v024_stage2_whole_review_contract().to_dict()

        self.assertEqual(contract["target_version"], "v0.2.4")
        self.assertEqual(contract["source_package_version"], "v0.2.3-repair")
        self.assertEqual(contract["stage_id"], "Stage 2")
        self.assertEqual(contract["review_id"], "stage_2_whole_review")
        self.assertEqual(contract["reviewed_phase_ids"], ["2.1", "2.2", "2.3"])
        self.assertTrue(contract["phase_2_1_complete"])
        self.assertTrue(contract["phase_2_2_complete"])
        self.assertTrue(contract["phase_2_3_complete"])
        self.assertTrue(contract["stage_2_candidate_complete"])
        self.assertTrue(contract["stage_2_review_complete"])
        self.assertTrue(contract["stage_2_complete"])
        self.assertFalse(contract["stage_3_allowed_without_user_instruction"])
        self.assertFalse(contract["github_main_upload_allowed"])
        self.assertFalse(contract["github_main_uploaded"])
        self.assertTrue(contract["next_stage_requires_user_acceptance"])
        self.assertEqual(contract["max_phases_per_run"], 1)

    def test_whole_review_preserves_stage2_entry_invariants(self) -> None:
        contract = entry_consistency.build_v024_stage2_whole_review_contract().to_dict()
        phase23_contract = entry_consistency.build_v024_stage2_phase23_contract().to_dict()

        self.assertEqual(contract["repair_label"], "PFI v0.2.3 Repair")
        self.assertEqual(contract["build_id"], "pfi-v024-stage2-phase22")
        self.assertEqual(contract["ui_contract_version"], "PFI-V024-STAGE2-ENTRY-CONSISTENCY")
        self.assertEqual(contract["validation_paths"], ["localhost", "app", "clear_cache", "new_profile"])
        self.assertEqual(contract["entry_audit_interface"], "window.PFI_READ_STAGE2_ENTRY_AUDIT")
        self.assertEqual(contract["visible_identity_fields"], ["repairLabel", "buildId", "webBundleHash", "uiContractVersion"])
        self.assertEqual(contract["validation_paths"], phase23_contract["validation_paths"])
        self.assertFalse(contract["app_bundle_changes_allowed"])
        self.assertFalse(contract["app_bundle_reinstall_allowed"])
        self.assertFalse(contract["launcher_c_or_plist_changes_allowed"])
        self.assertFalse(contract["data_logic_changes_allowed"])
        self.assertFalse(contract["formal_fake_financial_data_allowed"])
        self.assertIn("real browser validation for localhost/app/clear-cache/new-profile", contract["validation_commands"])
        self.assertIn("old Stage 1 entry signature runtime scan", contract["validation_commands"])

    def test_whole_review_evidence_pack_and_findings_are_complete(self) -> None:
        evidence_path = EVIDENCE_DIR / "evidence.json"
        terminal_path = EVIDENCE_DIR / "terminal.log"
        changed_files_path = EVIDENCE_DIR / "changed_files.txt"
        risk_path = EVIDENCE_DIR / "risk_and_rollback.md"
        review_doc_path = ROOT / "docs" / "pfi_v024" / "STAGE2_WHOLE_STAGE_REVIEW.md"

        for path in (evidence_path, terminal_path, changed_files_path, risk_path, review_doc_path):
            self.assertTrue(path.exists(), str(path))

        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        changed_files = [line.strip() for line in changed_files_path.read_text(encoding="utf-8").splitlines() if line.strip()]

        self.assertEqual(evidence["schema"], "PFIV024Stage2WholeReviewEvidenceV1")
        self.assertEqual(evidence["target_version"], "v0.2.4")
        self.assertEqual(evidence["stage"], "Stage 2")
        self.assertEqual(evidence["review_id"], "stage_2_whole_review")
        self.assertEqual(evidence["status"], "pass")
        self.assertTrue(evidence["stage_2_candidate_complete"])
        self.assertTrue(evidence["stage_2_review_complete"])
        self.assertTrue(evidence["stage_2_complete"])
        self.assertFalse(evidence["stage_3_allowed_without_user_instruction"])
        self.assertFalse(evidence["github_main_uploaded"])
        self.assertEqual(evidence["changed_files"], changed_files)
        self.assertEqual({item["status"] for item in evidence["review_findings"]}, {"fixed"})
        self.assertTrue(evidence["acceptance_checks"]["all_phase_evidence_present"])
        self.assertTrue(evidence["acceptance_checks"]["visible_repair_label_present"])
        self.assertTrue(evidence["acceptance_checks"]["visible_build_id_present"])
        self.assertTrue(evidence["acceptance_checks"]["visible_bundle_hash_present"])
        self.assertTrue(evidence["acceptance_checks"]["all_real_entry_paths_same_bundle_and_build"])
        self.assertTrue(evidence["acceptance_checks"]["old_stage1_entry_signature_absent_from_runtime_sources"])
        self.assertTrue(evidence["acceptance_checks"]["no_console_page_http_errors"])
        self.assertTrue(evidence["acceptance_checks"]["no_app_bundle_reinstall"])
        self.assertTrue(evidence["acceptance_checks"]["no_data_logic_changes"])
        self.assertTrue(evidence["acceptance_checks"]["github_main_not_uploaded"])

    def test_whole_review_evidence_matches_real_browser_validation(self) -> None:
        evidence = json.loads((EVIDENCE_DIR / "evidence.json").read_text(encoding="utf-8"))
        browser_validation = json.loads((PHASE_23_DIR / "browser_validation.json").read_text(encoding="utf-8"))
        expected_bundle_hash = (PHASE_23_DIR / "bundle_hash.txt").read_text(encoding="utf-8").strip()

        self.assertEqual(evidence["validation_surface"]["web_bundle_hash"], expected_bundle_hash)
        self.assertEqual(evidence["validation_surface"]["service_url"], browser_validation["service"]["url"])
        self.assertEqual(evidence["validation_surface"]["browser_validation_status"], "candidate_pass")
        self.assertEqual(evidence["validation_surface"]["browser_validation_paths"], ["localhost", "app", "clear_cache", "new_profile"])
        self.assertEqual(evidence["validation_surface"]["screenshot_count"], 4)
        self.assertTrue(browser_validation["all_paths_same_bundle_hash"])
        self.assertTrue(browser_validation["all_paths_same_build_id"])
        self.assertEqual(browser_validation["console_errors"], [])
        self.assertEqual(browser_validation["page_errors"], [])
        self.assertEqual(browser_validation["http_errors"], [])

        command_status = {item["cmd"]: item["status"] for item in evidence["commands"]}
        self.assertEqual(command_status["real browser validation for localhost/app/clear-cache/new-profile"], "pass")
        self.assertEqual(command_status["pytest stage2 whole review contract"], "pass")
        self.assertEqual(command_status["pytest v024 regression through stage2 whole review"], "pass")
        self.assertEqual(command_status["old Stage 1 entry signature runtime scan"], "pass")
        self.assertEqual(command_status["git diff --check -- PFI"], "pass")

    def test_whole_review_does_not_claim_stage3_or_upload(self) -> None:
        evidence = json.loads((EVIDENCE_DIR / "evidence.json").read_text(encoding="utf-8"))

        self.assertTrue(evidence["no_auto_next_stage"])
        self.assertFalse(evidence["stage_3_started"])
        self.assertFalse(evidence["stage_3_allowed_without_user_instruction"])
        self.assertFalse(evidence["github_main_uploaded"])
        self.assertIn("Stage 3 navigation repair", evidence["explicitly_not_done"])
        self.assertIn("GitHub main upload", evidence["explicitly_not_done"])
        self.assertIn("app bundle reinstall", evidence["explicitly_not_done"])


if __name__ == "__main__":
    unittest.main()
