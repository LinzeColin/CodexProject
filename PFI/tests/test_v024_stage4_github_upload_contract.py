from __future__ import annotations

import json
from pathlib import Path
import unittest

import pfi_v02.stage_v024_stage4_data_state as data_state


ROOT = Path(__file__).resolve().parents[1]
UPLOAD_DIR = ROOT / "reports" / "pfi_v024" / "stage_4" / "github_main_upload"


class TestV024Stage4GithubUploadContract(unittest.TestCase):
    def test_upload_contract_marks_stage4_uploaded_without_stage5(self) -> None:
        self.assertTrue(hasattr(data_state, "build_v024_stage4_github_upload_contract"))

        contract = data_state.build_v024_stage4_github_upload_contract().to_dict()

        self.assertEqual(contract["target_version"], "v0.2.4")
        self.assertEqual(contract["source_package_version"], "v0.2.3-repair")
        self.assertEqual(contract["stage_id"], "Stage 4")
        self.assertEqual(contract["upload_id"], "stage_4_github_main_upload")
        self.assertEqual(contract["review_id"], "stage_4_whole_review")
        self.assertEqual(contract["reviewed_phase_ids"], ["4.1", "4.2", "4.3"])
        self.assertTrue(contract["stage_4_candidate_complete"])
        self.assertTrue(contract["stage_4_review_complete"])
        self.assertTrue(contract["stage_4_complete"])
        self.assertTrue(contract["github_main_uploaded"])
        self.assertTrue(contract["rebased_on_current_origin_main"])
        self.assertTrue(contract["remote_main_verification_required"])
        self.assertFalse(contract["stage_5_started"])
        self.assertFalse(contract["stage_5_allowed_without_user_instruction"])
        self.assertFalse(contract["app_bundle_changes_allowed"])
        self.assertFalse(contract["data_logic_changes_allowed"])
        self.assertFalse(contract["formal_fake_financial_data_allowed"])
        self.assertEqual(contract["max_phases_per_run"], 1)
        self.assertIn("git push origin HEAD:main", contract["validation_commands"])
        self.assertIn("git ls-remote origin refs/heads/main", contract["validation_commands"])

    def test_upload_evidence_pack_is_machine_readable(self) -> None:
        evidence_path = UPLOAD_DIR / "evidence.json"
        terminal_path = UPLOAD_DIR / "terminal.log"
        changed_files_path = UPLOAD_DIR / "changed_files.txt"
        risk_path = UPLOAD_DIR / "risk_and_rollback.md"

        for path in (evidence_path, terminal_path, changed_files_path, risk_path):
            self.assertTrue(path.exists(), str(path))

        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        changed_files = [line.strip() for line in changed_files_path.read_text(encoding="utf-8").splitlines() if line.strip()]

        self.assertEqual(evidence["schema"], "PFIV024Stage4GithubMainUploadEvidenceV1")
        self.assertEqual(evidence["target_version"], "v0.2.4")
        self.assertEqual(evidence["stage"], "Stage 4")
        self.assertEqual(evidence["upload_id"], "stage_4_github_main_upload")
        self.assertEqual(evidence["status"], "pass")
        self.assertEqual(evidence["completed_gate"], "Stage 4 GitHub main upload")
        self.assertEqual(evidence["reviewed_phase_ids"], ["4.1", "4.2", "4.3"])
        self.assertTrue(evidence["stage_4_candidate_complete"])
        self.assertTrue(evidence["stage_4_review_complete"])
        self.assertTrue(evidence["stage_4_complete"])
        self.assertTrue(evidence["github_main_uploaded"])
        self.assertTrue(evidence["rebased_on_current_origin_main"])
        self.assertTrue(evidence["remote_main_verification_required"])
        self.assertTrue(evidence["remote_main_verified_by_terminal"])
        self.assertTrue(evidence["head_origin_remote_equal_verified"])
        self.assertFalse(evidence["stage_5_started"])
        self.assertFalse(evidence["stage_5_allowed_without_user_instruction"])
        self.assertEqual(evidence["changed_files"], changed_files)

    def test_upload_gate_preserves_stage4_data_trust_boundaries(self) -> None:
        evidence = json.loads((UPLOAD_DIR / "evidence.json").read_text(encoding="utf-8"))

        self.assertTrue(evidence["no_auto_next_stage"])
        self.assertFalse(evidence["app_bundle_changes_made"])
        self.assertFalse(evidence["app_bundle_reinstall_executed"])
        self.assertFalse(evidence["launcher_c_or_plist_changes_made"])
        self.assertFalse(evidence["data_logic_changes_made"])
        self.assertFalse(evidence["formal_fake_financial_data_added"])
        self.assertEqual(evidence["source_summary"]["status"], "ready")
        self.assertEqual(evidence["source_summary"]["record_count"], 8815)
        self.assertEqual(evidence["source_summary"]["raw_file_count"], 4)
        self.assertEqual(evidence["read_model"]["real_confirmed_zero_metric_count"], 0)
        self.assertIn("Stage 5", evidence["explicitly_not_done"])
        self.assertIn("app bundle reinstall", evidence["explicitly_not_done"])
        self.assertIn("financial data or metric logic changes", evidence["explicitly_not_done"])


if __name__ == "__main__":
    unittest.main()
