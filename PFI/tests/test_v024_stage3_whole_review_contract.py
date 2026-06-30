from __future__ import annotations

import json
from pathlib import Path
import unittest

import pfi_v02.stage_v024_stage3_navigation as navigation


ROOT = Path(__file__).resolve().parents[1]
REVIEW_DIR = ROOT / "reports" / "pfi_v024" / "stage_3" / "whole_stage_review"
PHASE31_DIR = ROOT / "reports" / "pfi_v024" / "stage_3" / "phase_3_1"
PHASE32_DIR = ROOT / "reports" / "pfi_v024" / "stage_3" / "phase_3_2"
PHASE33_DIR = ROOT / "reports" / "pfi_v024" / "stage_3" / "phase_3_3"


class TestV024Stage3WholeReviewContract(unittest.TestCase):
    def test_whole_review_contract_closes_stage3_without_stage4_or_upload(self) -> None:
        self.assertTrue(hasattr(navigation, "build_v024_stage3_whole_review_contract"))

        contract = navigation.build_v024_stage3_whole_review_contract().to_dict()

        self.assertEqual(contract["target_version"], "v0.2.4")
        self.assertEqual(contract["source_package_version"], "v0.2.3-repair")
        self.assertEqual(contract["stage_id"], "Stage 3")
        self.assertEqual(contract["review_id"], "stage_3_whole_review")
        self.assertEqual(contract["reviewed_phase_ids"], ["3.1", "3.2", "3.3"])
        self.assertTrue(contract["phase_3_1_complete"])
        self.assertTrue(contract["phase_3_2_complete"])
        self.assertTrue(contract["phase_3_3_complete"])
        self.assertTrue(contract["stage_3_candidate_complete"])
        self.assertTrue(contract["stage_3_review_complete"])
        self.assertTrue(contract["stage_3_complete"])
        self.assertFalse(contract["stage_4_allowed_without_user_instruction"])
        self.assertFalse(contract["github_main_upload_allowed"])
        self.assertFalse(contract["github_main_uploaded"])
        self.assertEqual(contract["max_phases_per_run"], 1)

    def test_whole_review_preserves_stage3_navigation_invariants(self) -> None:
        contract = navigation.build_v024_stage3_whole_review_contract().to_dict()

        self.assertEqual(contract["official_primary_entry_count"], 10)
        self.assertEqual(contract["market_research_primary_index"], 9)
        self.assertEqual(contract["legacy_alias_route_count"], 6)
        self.assertEqual(contract["browser_navigation_contract_version"], "PFI-V024-STAGE3-PHASE33-BROWSER-NAVIGATION")
        self.assertEqual(contract["route_contract_version"], "PFI-V024-STAGE3-PHASE32-ROUTES")
        self.assertEqual(contract["navigation_contract_version"], "PFI-V024-STAGE3-PHASE31-NAVIGATION")
        self.assertTrue(contract["browser_history_validation_done"])
        self.assertFalse(contract["app_bundle_changes_allowed"])
        self.assertFalse(contract["data_logic_changes_allowed"])
        self.assertFalse(contract["formal_fake_financial_data_allowed"])
        self.assertIn("node playwright stage3 phase33 browser validation", contract["validation_commands"])
        self.assertIn("pytest v024 regression through stage3 whole review", contract["validation_commands"])

    def test_whole_review_evidence_pack_and_findings_are_complete(self) -> None:
        evidence_path = REVIEW_DIR / "evidence.json"
        terminal_path = REVIEW_DIR / "terminal.log"
        changed_files_path = REVIEW_DIR / "changed_files.txt"
        risk_path = REVIEW_DIR / "risk_and_rollback.md"
        review_doc_path = ROOT / "docs" / "pfi_v024" / "STAGE3_WHOLE_STAGE_REVIEW.md"

        for path in (evidence_path, terminal_path, changed_files_path, risk_path, review_doc_path):
            self.assertTrue(path.exists(), str(path))

        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        changed_files = [line.strip() for line in changed_files_path.read_text(encoding="utf-8").splitlines() if line.strip()]

        self.assertEqual(evidence["schema"], "PFIV024Stage3WholeReviewEvidenceV1")
        self.assertEqual(evidence["target_version"], "v0.2.4")
        self.assertEqual(evidence["stage"], "Stage 3")
        self.assertEqual(evidence["review_id"], "stage_3_whole_review")
        self.assertEqual(evidence["status"], "pass")
        self.assertTrue(evidence["stage_3_candidate_complete"])
        self.assertTrue(evidence["stage_3_review_complete"])
        self.assertTrue(evidence["stage_3_complete"])
        self.assertFalse(evidence["stage_4_started"])
        self.assertFalse(evidence["stage_4_allowed_without_user_instruction"])
        self.assertFalse(evidence["github_main_uploaded"])
        self.assertEqual(evidence["changed_files"], changed_files)
        self.assertEqual({item["status"] for item in evidence["review_findings"]}, {"fixed"})
        self.assertTrue(evidence["acceptance_checks"]["all_phase_evidence_present"])
        self.assertTrue(evidence["acceptance_checks"]["official_primary_entries_are_10"])
        self.assertTrue(evidence["acceptance_checks"]["market_research_is_primary_index_9"])
        self.assertTrue(evidence["acceptance_checks"]["no_16_peer_primary_entries"])
        self.assertTrue(evidence["acceptance_checks"]["legacy_alias_routes_resolve"])
        self.assertTrue(evidence["acceptance_checks"]["browser_back_forward_passed"])
        self.assertTrue(evidence["acceptance_checks"]["direct_url_alias_passed"])
        self.assertTrue(evidence["acceptance_checks"]["not_anchor_scroll_only_navigation"])
        self.assertTrue(evidence["acceptance_checks"]["no_app_bundle_reinstall"])
        self.assertTrue(evidence["acceptance_checks"]["no_data_logic_changes"])
        self.assertTrue(evidence["acceptance_checks"]["github_main_not_uploaded"])

    def test_whole_review_evidence_matches_phase_evidence_and_browser_validation(self) -> None:
        evidence = json.loads((REVIEW_DIR / "evidence.json").read_text(encoding="utf-8"))
        phase31 = json.loads((PHASE31_DIR / "evidence.json").read_text(encoding="utf-8"))
        phase32 = json.loads((PHASE32_DIR / "evidence.json").read_text(encoding="utf-8"))
        phase33 = json.loads((PHASE33_DIR / "evidence.json").read_text(encoding="utf-8"))
        browser = json.loads((PHASE33_DIR / "browser_validation.json").read_text(encoding="utf-8"))
        legacy = json.loads((PHASE33_DIR / "legacy_routes_validation.json").read_text(encoding="utf-8"))

        self.assertEqual(evidence["reviewed_phase_ids"], ["3.1", "3.2", "3.3"])
        self.assertEqual([phase31["status"], phase32["status"], phase33["status"]], ["candidate_pass", "candidate_pass", "candidate_pass"])
        self.assertEqual(evidence["validation_surface"]["desktop_primary_count"], browser["desktop_primary_count"])
        self.assertEqual(evidence["validation_surface"]["mobile_primary_count"], browser["mobile_primary_count"])
        self.assertEqual(evidence["validation_surface"]["legacy_alias_count"], len(legacy["cases"]))
        self.assertEqual(evidence["validation_surface"]["browser_contract"], browser["contract"])
        self.assertEqual(evidence["validation_surface"]["browser_validation_status"], "pass")
        self.assertTrue(browser["back_forward_passed"])
        self.assertTrue(browser["direct_url_alias_passed"])
        self.assertEqual(browser["console_errors"], [])
        self.assertEqual(browser["page_errors"], [])

        command_status = {item["cmd"]: item["status"] for item in evidence["commands"]}
        self.assertEqual(command_status["node playwright stage3 phase33 browser validation"], "pass")
        self.assertEqual(command_status["pytest stage3 whole review contract"], "pass")
        self.assertEqual(command_status["pytest v024 regression through stage3 whole review"], "pass")
        self.assertEqual(command_status["pytest v023 stage3 navigation compatibility"], "pass")
        self.assertEqual(command_status["git diff --check -- PFI"], "pass")

    def test_whole_review_does_not_claim_upload_or_next_stage(self) -> None:
        evidence = json.loads((REVIEW_DIR / "evidence.json").read_text(encoding="utf-8"))

        self.assertTrue(evidence["no_auto_next_stage"])
        self.assertFalse(evidence["stage_4_started"])
        self.assertFalse(evidence["stage_4_allowed_without_user_instruction"])
        self.assertFalse(evidence["github_main_uploaded"])
        self.assertIn("Stage 4", evidence["explicitly_not_done"])
        self.assertIn("GitHub main upload", evidence["explicitly_not_done"])
        self.assertIn("app bundle reinstall", evidence["explicitly_not_done"])


if __name__ == "__main__":
    unittest.main()
