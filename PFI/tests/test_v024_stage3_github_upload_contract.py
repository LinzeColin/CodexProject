from __future__ import annotations

import json
from pathlib import Path
import unittest

import pfi_v02.stage_v024_stage3_navigation as navigation


ROOT = Path(__file__).resolve().parents[1]
UPLOAD_DIR = ROOT / "reports" / "pfi_v024" / "stage_3" / "github_main_upload"


class TestV024Stage3GithubUploadContract(unittest.TestCase):
    def test_upload_contract_marks_stage3_uploaded_without_stage4(self) -> None:
        self.assertTrue(hasattr(navigation, "build_v024_stage3_github_upload_contract"))

        contract = navigation.build_v024_stage3_github_upload_contract().to_dict()

        self.assertEqual(contract["target_version"], "v0.2.4")
        self.assertEqual(contract["source_package_version"], "v0.2.3-repair")
        self.assertEqual(contract["stage_id"], "Stage 3")
        self.assertEqual(contract["upload_id"], "stage_3_github_main_upload")
        self.assertTrue(contract["stage_3_complete"])
        self.assertTrue(contract["stage_3_review_complete"])
        self.assertTrue(contract["github_main_uploaded"])
        self.assertTrue(contract["rebased_on_current_origin_main"])
        self.assertFalse(contract["stage_4_started"])
        self.assertFalse(contract["stage_4_allowed_without_user_instruction"])
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

        self.assertEqual(evidence["schema"], "PFIV024Stage3GithubMainUploadEvidenceV1")
        self.assertEqual(evidence["target_version"], "v0.2.4")
        self.assertEqual(evidence["stage"], "Stage 3")
        self.assertEqual(evidence["upload_id"], "stage_3_github_main_upload")
        self.assertEqual(evidence["status"], "pass")
        self.assertTrue(evidence["stage_3_complete"])
        self.assertTrue(evidence["stage_3_review_complete"])
        self.assertTrue(evidence["github_main_uploaded"])
        self.assertTrue(evidence["rebased_on_current_origin_main"])
        self.assertFalse(evidence["stage_4_started"])
        self.assertFalse(evidence["stage_4_allowed_without_user_instruction"])
        self.assertEqual(evidence["changed_files"], changed_files)
        self.assertIn("GitHub main upload", evidence["completed_gate"])

    def test_upload_gate_keeps_non_goals_closed(self) -> None:
        evidence = json.loads((UPLOAD_DIR / "evidence.json").read_text(encoding="utf-8"))

        self.assertTrue(evidence["no_auto_next_stage"])
        self.assertFalse(evidence["app_bundle_changes_made"])
        self.assertFalse(evidence["app_bundle_reinstall_executed"])
        self.assertFalse(evidence["launcher_c_or_plist_changes_made"])
        self.assertFalse(evidence["data_logic_changes_made"])
        self.assertFalse(evidence["formal_fake_financial_data_added"])
        self.assertIn("Stage 4", evidence["explicitly_not_done"])
        self.assertIn("app bundle reinstall", evidence["explicitly_not_done"])
        self.assertIn("financial data or metric logic changes", evidence["explicitly_not_done"])


if __name__ == "__main__":
    unittest.main()
