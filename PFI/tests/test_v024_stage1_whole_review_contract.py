from __future__ import annotations

import json
import unittest
from pathlib import Path

import pfi_v02.stage_v024_stage1_shell_integrity as shell_integrity


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_DIR = ROOT / "reports" / "pfi_v024" / "stage_1" / "whole_stage_review"


class TestV024Stage1WholeReviewContract(unittest.TestCase):
    def test_whole_review_contract_closes_stage1_without_uploading_main(self) -> None:
        contract = shell_integrity.build_v024_stage1_whole_review_contract().to_dict()

        self.assertEqual(contract["target_version"], "v0.2.4")
        self.assertEqual(contract["source_package_version"], "v0.2.3-repair")
        self.assertEqual(contract["stage_id"], "Stage 1")
        self.assertEqual(contract["review_id"], "stage_1_whole_review")
        self.assertEqual(contract["reviewed_phase_ids"], ["1.1", "1.2", "1.3"])
        self.assertTrue(contract["phase_1_1_complete"])
        self.assertTrue(contract["phase_1_2_complete"])
        self.assertTrue(contract["phase_1_3_complete"])
        self.assertTrue(contract["stage_1_candidate_complete"])
        self.assertTrue(contract["stage_1_review_complete"])
        self.assertTrue(contract["stage_1_complete"])
        self.assertFalse(contract["stage_2_allowed_without_user_instruction"])
        self.assertFalse(contract["github_main_upload_allowed"])
        self.assertFalse(contract["github_main_uploaded"])
        self.assertTrue(contract["next_stage_requires_user_acceptance"])
        self.assertEqual(contract["max_phases_per_run"], 1)

    def test_whole_review_preserves_stage1_shell_acceptance_invariants(self) -> None:
        contract = shell_integrity.build_v024_stage1_whole_review_contract().to_dict()

        self.assertEqual(contract["shell_js_path"], "PFI/web/app/shell.js")
        self.assertEqual(contract["version_js_path"], "PFI/web/app/version.js")
        self.assertEqual(contract["shell_integrity_api"], "window.PFI_STAGE1_SHELL")
        self.assertEqual(contract["version_read_interface"], "window.PFI_READ_STAGE1_VERSION")
        self.assertEqual(contract["initialization_entry"], "initializePFIStage1Shell")
        self.assertEqual(contract["route_mount_entry"], "mountPFIStage1Route")
        self.assertEqual(contract["error_boundary_entry"], "handlePFIStage1ShellError")
        self.assertFalse(contract["business_ui_changes_allowed"])
        self.assertFalse(contract["data_logic_changes_allowed"])
        self.assertFalse(contract["app_bundle_changes_allowed"])
        self.assertFalse(contract["formal_fake_financial_data_allowed"])
        self.assertIn("node --check PFI/web/app/shell.js", contract["validation_commands"])
        self.assertIn("node --check PFI/web/app/version.js", contract["validation_commands"])
        self.assertIn("pytest v024 pre-stage0 stage0 stage1 regression", contract["validation_commands"])

    def test_whole_review_evidence_pack_and_findings_are_complete(self) -> None:
        evidence_path = EVIDENCE_DIR / "evidence.json"
        terminal_path = EVIDENCE_DIR / "terminal.log"
        changed_files_path = EVIDENCE_DIR / "changed_files.txt"
        risk_path = EVIDENCE_DIR / "risk_and_rollback.md"
        review_doc_path = ROOT / "docs" / "pfi_v024" / "STAGE1_WHOLE_STAGE_REVIEW.md"

        for path in (evidence_path, terminal_path, changed_files_path, risk_path, review_doc_path):
            self.assertTrue(path.exists(), str(path))

        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        changed_files = [line.strip() for line in changed_files_path.read_text(encoding="utf-8").splitlines() if line.strip()]

        self.assertEqual(evidence["schema"], "PFIV024Stage1WholeReviewEvidenceV1")
        self.assertEqual(evidence["target_version"], "v0.2.4")
        self.assertEqual(evidence["stage"], "Stage 1")
        self.assertEqual(evidence["review_id"], "stage_1_whole_review")
        self.assertEqual(evidence["status"], "pass")
        self.assertTrue(evidence["stage_1_candidate_complete"])
        self.assertTrue(evidence["stage_1_review_complete"])
        self.assertTrue(evidence["stage_1_complete"])
        self.assertFalse(evidence["stage_2_allowed_without_user_instruction"])
        self.assertFalse(evidence["github_main_uploaded"])
        self.assertEqual(evidence["changed_files"], changed_files)
        self.assertEqual({item["status"] for item in evidence["review_findings"]}, {"fixed"})
        self.assertTrue(evidence["acceptance_checks"]["all_phase_evidence_present"])
        self.assertTrue(evidence["acceptance_checks"]["shell_js_syntax_passes"])
        self.assertTrue(evidence["acceptance_checks"]["version_js_syntax_passes"])
        self.assertTrue(evidence["acceptance_checks"]["shell_integrity_api_present"])
        self.assertTrue(evidence["acceptance_checks"]["no_fake_financial_data_added"])
        self.assertTrue(evidence["acceptance_checks"]["no_business_ui_or_data_logic_changes"])
        self.assertTrue(evidence["acceptance_checks"]["github_main_not_uploaded"])

    def test_whole_review_evidence_records_review_time_shell_artifacts(self) -> None:
        evidence = json.loads((EVIDENCE_DIR / "evidence.json").read_text(encoding="utf-8"))

        self.assertRegex(evidence["validation_surface"]["shell_js_sha256"], r"^[0-9a-f]{64}$")
        self.assertRegex(evidence["validation_surface"]["version_js_sha256"], r"^[0-9a-f]{64}$")
        self.assertEqual(evidence["validation_surface"]["shell_integrity_api"], "window.PFI_STAGE1_SHELL")
        self.assertEqual(evidence["validation_surface"]["version_read_interface"], "window.PFI_READ_STAGE1_VERSION")
        command_status = {item["cmd"]: item["status"] for item in evidence["commands"]}
        self.assertEqual(command_status["node --check PFI/web/app/shell.js"], "pass")
        self.assertEqual(command_status["node --check PFI/web/app/version.js"], "pass")
        self.assertEqual(command_status["pytest stage1 whole review contract"], "pass")
        self.assertEqual(command_status["pytest v024 pre-stage0 stage0 stage1 regression"], "pass")
        self.assertEqual(command_status["git diff --check -- PFI"], "pass")

    def test_whole_review_does_not_claim_stage2_or_upload(self) -> None:
        evidence = json.loads((EVIDENCE_DIR / "evidence.json").read_text(encoding="utf-8"))

        self.assertTrue(evidence["no_auto_next_stage"])
        self.assertFalse(evidence["stage_2_started"])
        self.assertFalse(evidence["stage_2_allowed_without_user_instruction"])
        self.assertFalse(evidence["github_main_uploaded"])
        self.assertIn("Stage 2 entry consistency", evidence["explicitly_not_done"])
        self.assertIn("GitHub main upload", evidence["explicitly_not_done"])


if __name__ == "__main__":
    unittest.main()
