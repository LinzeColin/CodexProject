from __future__ import annotations

import importlib
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
PHASE_DIR = ROOT / "reports" / "pfi_v024" / "stage_9" / "phase_9_2"


def load_stage9_module():
    try:
        return importlib.import_module("pfi_v02.stage_v024_stage9_regression_freeze")
    except ModuleNotFoundError:
        return None


class TestV024Stage9Phase92DeliveryFreeze(unittest.TestCase):
    def test_phase92_contract_defines_delivery_freeze_without_user_acceptance(self) -> None:
        stage9 = load_stage9_module()
        self.assertIsNotNone(stage9, "stage_v024_stage9_regression_freeze module is required")
        self.assertTrue(hasattr(stage9, "build_v024_stage9_phase92_contract"))

        contract = stage9.build_v024_stage9_phase92_contract().to_dict()

        self.assertEqual(contract["target_version"], "v0.2.4")
        self.assertEqual(contract["source_package_version"], "v0.2.3-repair")
        self.assertEqual(contract["stage"], "Stage 9")
        self.assertEqual(contract["stage_name"], "回归防线与交付冻结")
        self.assertEqual(contract["phase_id"], "9.2")
        self.assertEqual(contract["phase_name"], "交付冻结")
        self.assertTrue(contract["current_phase_only"])
        self.assertEqual(contract["max_phases_per_run"], 1)
        self.assertTrue(contract["phase_9_1_required"])
        self.assertEqual(contract["task_ids"], ["T9.2.1", "T9.2.2", "T9.2.3", "T9.2.4"])
        self.assertEqual(
            contract["required_artifacts"],
            [
                "final_evidence_index.json",
                "closeout_candidate.md",
                "evidence.json",
                "terminal.log",
                "changed_files.txt",
                "risk_and_rollback.md",
            ],
        )
        self.assertFalse(contract["phase_9_3_started"])
        self.assertFalse(contract["user_acceptance_claimed"])
        self.assertFalse(contract["stage_9_whole_review_complete"])
        self.assertFalse(contract["github_main_uploaded"])
        self.assertFalse(contract["app_bundle_changes_allowed"])
        self.assertFalse(contract["data_logic_changes_allowed"])
        self.assertFalse(contract["formal_fake_financial_data_allowed"])
        self.assertIn("Stage 9 Phase 9.3 user acceptance", contract["explicitly_not_done"])

    def test_final_evidence_index_covers_repair_stages_and_stage9_guardrails(self) -> None:
        index_path = PHASE_DIR / "final_evidence_index.json"
        self.assertTrue(index_path.exists(), str(index_path))

        index = json.loads(index_path.read_text(encoding="utf-8"))
        required_refs = {entry["id"]: entry for entry in index["evidence"]}

        self.assertEqual(index["schema"], "PFIV024Stage9Phase92FinalEvidenceIndexV1")
        self.assertEqual(index["target_version"], "v0.2.4")
        self.assertEqual(index["stage"], "Stage 9")
        self.assertEqual(index["phase_id"], "9.2")
        self.assertEqual(index["status"], "candidate_pass")
        self.assertTrue(index["stage_8_github_main_uploaded_verified"])
        self.assertTrue(index["stage_9_phase_9_1_guardrails_passed"])
        self.assertFalse(index["phase_9_3_started"])
        self.assertFalse(index["user_acceptance_claimed"])
        self.assertFalse(index["github_main_uploaded"])
        self.assertEqual(index["screenshot_evidence_count"], 14)
        self.assertGreaterEqual(index["terminal_log_count"], 10)
        self.assertIn("stage_8_github_main_upload", required_refs)
        self.assertIn("stage_9_phase_9_1_regression_guardrails", required_refs)
        self.assertIn("stage_9_phase_9_2_delivery_freeze", required_refs)
        self.assertEqual(required_refs["stage_9_phase_9_2_delivery_freeze"]["status"], "candidate_pass")

    def test_closeout_candidate_lists_not_done_and_risks(self) -> None:
        closeout_path = PHASE_DIR / "closeout_candidate.md"
        self.assertTrue(closeout_path.exists(), str(closeout_path))
        closeout = closeout_path.read_text(encoding="utf-8")

        self.assertIn("候选完成，等待用户验收", closeout)
        self.assertIn("Phase 9.3 用户验收未执行", closeout)
        self.assertIn("Stage 9 whole-stage review 未执行", closeout)
        self.assertIn("Stage 9 GitHub main upload 未执行", closeout)
        self.assertIn("未重装 app bundle", closeout)
        self.assertIn("未修改真实财务数据", closeout)
        self.assertIn("后续风险", closeout)
        self.assertNotIn("用户已验收", closeout)

    def test_readme_uses_candidate_language_not_user_accepted_closeout(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn("Stage 9 delivery freeze candidate", readme)
        self.assertIn("waiting for Phase 9.3 user acceptance", readme)
        self.assertIn("Phase 9.3 user acceptance: not started", readme)
        self.assertNotIn("Stage 9 user acceptance: complete", readme)
        self.assertNotIn("Stage 9 final closeout complete", readme)

    def test_phase92_evidence_pack_is_machine_readable(self) -> None:
        evidence_path = PHASE_DIR / "evidence.json"
        terminal_path = PHASE_DIR / "terminal.log"
        changed_files_path = PHASE_DIR / "changed_files.txt"
        risk_path = PHASE_DIR / "risk_and_rollback.md"

        for path in (evidence_path, terminal_path, changed_files_path, risk_path):
            self.assertTrue(path.exists(), str(path))
            self.assertGreater(path.stat().st_size, 0, str(path))

        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        changed_files = [
            line.strip()
            for line in changed_files_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

        self.assertEqual(evidence["schema"], "PFIV024Stage9Phase92DeliveryFreezeEvidenceV1")
        self.assertEqual(evidence["version"], "v0.2.3-repair")
        self.assertEqual(evidence["target_version"], "v0.2.4")
        self.assertEqual(evidence["stage"], "Stage 9")
        self.assertEqual(evidence["phase_id"], "9.2")
        self.assertEqual(evidence["status"], "candidate_pass")
        self.assertTrue(evidence["current_phase_only"])
        self.assertTrue(evidence["phase_9_1_guardrails_verified"])
        self.assertFalse(evidence["phase_9_3_started"])
        self.assertFalse(evidence["user_acceptance_claimed"])
        self.assertFalse(evidence["stage_9_whole_review_complete"])
        self.assertFalse(evidence["github_main_uploaded"])
        self.assertFalse(evidence["app_bundle_reinstall_executed"])
        self.assertFalse(evidence["data_logic_changes_made"])
        self.assertFalse(evidence["formal_fake_financial_data_added"])
        self.assertEqual(evidence["changed_files"], changed_files)


if __name__ == "__main__":
    unittest.main()
