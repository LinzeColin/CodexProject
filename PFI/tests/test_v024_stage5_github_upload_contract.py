from __future__ import annotations

import importlib
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
UPLOAD_DIR = ROOT / "reports" / "pfi_v024" / "stage_5" / "github_main_upload"


def load_stage5_module():
    try:
        return importlib.import_module("pfi_v02.stage_v024_stage5_experience")
    except ModuleNotFoundError:
        return None


class TestV024Stage5GithubUploadContract(unittest.TestCase):
    def test_upload_contract_marks_stage5_uploaded_without_stage6(self) -> None:
        stage5 = load_stage5_module()
        self.assertIsNotNone(stage5, "stage_v024_stage5_experience module is required")
        self.assertTrue(hasattr(stage5, "build_v024_stage5_github_upload_contract"))

        contract = stage5.build_v024_stage5_github_upload_contract().to_dict()

        self.assertEqual(contract["target_version"], "v0.2.4")
        self.assertEqual(contract["source_package_version"], "v0.2.3-repair")
        self.assertEqual(contract["stage_id"], "Stage 5")
        self.assertEqual(contract["upload_id"], "stage_5_github_main_upload")
        self.assertEqual(contract["review_id"], "stage_5_whole_review")
        self.assertEqual(contract["reviewed_phase_ids"], ["5.1", "5.2", "5.3"])
        self.assertTrue(contract["stage_5_candidate_complete"])
        self.assertTrue(contract["stage_5_review_complete"])
        self.assertTrue(contract["stage_5_complete"])
        self.assertTrue(contract["github_main_uploaded"])
        self.assertTrue(contract["rebased_on_current_origin_main"])
        self.assertTrue(contract["remote_main_verification_required"])
        self.assertFalse(contract["stage_6_started"])
        self.assertFalse(contract["stage_6_allowed_without_user_instruction"])
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

        self.assertEqual(evidence["schema"], "PFIV024Stage5GithubMainUploadEvidenceV1")
        self.assertEqual(evidence["target_version"], "v0.2.4")
        self.assertEqual(evidence["stage"], "Stage 5")
        self.assertEqual(evidence["upload_id"], "stage_5_github_main_upload")
        self.assertEqual(evidence["review_id"], "stage_5_whole_review")
        self.assertEqual(evidence["status"], "pass")
        self.assertEqual(evidence["completed_gate"], "Stage 5 GitHub main upload")
        self.assertEqual(evidence["reviewed_phase_ids"], ["5.1", "5.2", "5.3"])
        self.assertTrue(evidence["stage_5_candidate_complete"])
        self.assertTrue(evidence["stage_5_review_complete"])
        self.assertTrue(evidence["stage_5_complete"])
        self.assertTrue(evidence["github_main_uploaded"])
        self.assertTrue(evidence["rebased_on_current_origin_main"])
        self.assertTrue(evidence["remote_main_verification_required"])
        self.assertTrue(evidence["remote_main_verified_by_terminal"])
        self.assertTrue(evidence["head_origin_remote_equal_verified"])
        self.assertFalse(evidence["stage_6_started"])
        self.assertFalse(evidence["stage_6_allowed_without_user_instruction"])
        self.assertEqual(evidence["changed_files"], changed_files)

    def test_upload_gate_preserves_stage5_boundaries(self) -> None:
        evidence = json.loads((UPLOAD_DIR / "evidence.json").read_text(encoding="utf-8"))

        self.assertTrue(evidence["no_auto_next_stage"])
        self.assertFalse(evidence["app_bundle_changes_made"])
        self.assertFalse(evidence["app_bundle_reinstall_executed"])
        self.assertFalse(evidence["launcher_c_or_plist_changes_made"])
        self.assertFalse(evidence["data_logic_changes_made"])
        self.assertFalse(evidence["formal_fake_financial_data_added"])
        self.assertTrue(evidence["whole_stage_review"]["status"] == "pass")
        self.assertEqual(evidence["whole_stage_review"]["screenshot_count"], 20)
        self.assertIn("Stage 6", evidence["explicitly_not_done"])
        self.assertIn("app bundle reinstall", evidence["explicitly_not_done"])
        self.assertIn("financial data or metric logic changes", evidence["explicitly_not_done"])


if __name__ == "__main__":
    unittest.main()
