from __future__ import annotations

import importlib
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
UPLOAD_DIR = ROOT / "reports" / "pfi_v024" / "stage_9" / "github_main_upload"
EXPECTED_PHASE_IDS = ["9.1", "9.2", "9.3"]


def load_stage9_module():
    return importlib.import_module("pfi_v02.stage_v024_stage9_regression_freeze")


class TestV024Stage9GithubUploadContract(unittest.TestCase):
    def test_upload_contract_marks_stage9_uploaded_without_future_version(self) -> None:
        stage9 = load_stage9_module()
        self.assertTrue(hasattr(stage9, "build_v024_stage9_github_upload_contract"))

        contract = stage9.build_v024_stage9_github_upload_contract().to_dict()

        self.assertEqual(contract["target_version"], "v0.2.4")
        self.assertEqual(contract["source_package_version"], "v0.2.3-repair")
        self.assertEqual(contract["stage_id"], "Stage 9")
        self.assertEqual(contract["stage_name"], "回归防线与交付冻结")
        self.assertEqual(contract["upload_id"], "stage_9_github_main_upload")
        self.assertEqual(contract["review_id"], "stage_9_whole_review")
        self.assertEqual(contract["reviewed_phase_ids"], EXPECTED_PHASE_IDS)
        self.assertTrue(contract["stage_9_candidate_complete"])
        self.assertTrue(contract["stage_9_review_complete"])
        self.assertTrue(contract["stage_9_complete"])
        self.assertTrue(contract["github_main_uploaded"])
        self.assertTrue(contract["rebased_on_current_origin_main"])
        self.assertTrue(contract["remote_main_verification_required"])
        self.assertFalse(contract["future_version_started"])
        self.assertFalse(contract["future_version_allowed_before_upload_verification"])
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
            self.assertGreater(path.stat().st_size, 0, str(path))

        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        changed_files = [
            line.strip()
            for line in changed_files_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

        self.assertEqual(evidence["schema"], "PFIV024Stage9GithubMainUploadEvidenceV1")
        self.assertEqual(evidence["target_version"], "v0.2.4")
        self.assertEqual(evidence["stage"], "Stage 9")
        self.assertEqual(evidence["upload_id"], "stage_9_github_main_upload")
        self.assertEqual(evidence["review_id"], "stage_9_whole_review")
        self.assertEqual(evidence["status"], "pass")
        self.assertEqual(evidence["completed_gate"], "Stage 9 GitHub main upload")
        self.assertEqual(evidence["reviewed_phase_ids"], EXPECTED_PHASE_IDS)
        self.assertTrue(evidence["stage_9_candidate_complete"])
        self.assertTrue(evidence["stage_9_review_complete"])
        self.assertTrue(evidence["stage_9_complete"])
        self.assertTrue(evidence["github_main_uploaded"])
        self.assertTrue(evidence["rebased_on_current_origin_main"])
        self.assertTrue(evidence["remote_main_verification_required"])
        self.assertTrue(evidence["remote_main_verified_by_terminal"])
        self.assertTrue(evidence["head_origin_remote_equal_verified"])
        self.assertFalse(evidence["future_version_started"])
        self.assertFalse(evidence["future_version_allowed_before_upload_verification"])
        self.assertEqual(evidence["changed_files"], changed_files)

    def test_upload_gate_preserves_stage9_boundaries(self) -> None:
        evidence = json.loads((UPLOAD_DIR / "evidence.json").read_text(encoding="utf-8"))

        self.assertTrue(evidence["no_auto_next_stage"])
        self.assertFalse(evidence["app_bundle_changes_made"])
        self.assertFalse(evidence["app_bundle_reinstall_executed"])
        self.assertFalse(evidence["launcher_c_or_plist_changes_made"])
        self.assertFalse(evidence["data_logic_changes_made"])
        self.assertFalse(evidence["formal_fake_financial_data_added"])
        self.assertEqual(evidence["whole_stage_review"]["status"], "pass")
        self.assertEqual(evidence["whole_stage_review"]["review_findings_fixed"], 3)
        self.assertTrue(evidence["whole_stage_review"]["phase_9_3_user_confirmed"])
        self.assertEqual(evidence["whole_stage_review"]["final_evidence_index_status"], "candidate_pass")
        self.assertTrue(evidence["whole_stage_review"]["all_guardrails_passed"])
        self.assertIn("future version work", evidence["explicitly_not_done"])
        self.assertIn("app bundle reinstall", evidence["explicitly_not_done"])
        self.assertIn("financial data or metric logic changes", evidence["explicitly_not_done"])


if __name__ == "__main__":
    unittest.main()
