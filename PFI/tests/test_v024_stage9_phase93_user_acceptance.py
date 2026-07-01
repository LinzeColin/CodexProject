from __future__ import annotations

import importlib
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
PHASE_DIR = ROOT / "reports" / "pfi_v024" / "stage_9" / "phase_9_3"


def load_stage9_module():
    try:
        return importlib.import_module("pfi_v02.stage_v024_stage9_regression_freeze")
    except ModuleNotFoundError:
        return None


class TestV024Stage9Phase93UserAcceptance(unittest.TestCase):
    def test_phase93_contract_prepares_user_acceptance_without_claiming_it(self) -> None:
        stage9 = load_stage9_module()
        self.assertIsNotNone(stage9, "stage_v024_stage9_regression_freeze module is required")
        self.assertTrue(hasattr(stage9, "build_v024_stage9_phase93_contract"))

        contract = stage9.build_v024_stage9_phase93_contract().to_dict()

        self.assertEqual(contract["target_version"], "v0.2.4")
        self.assertEqual(contract["source_package_version"], "v0.2.3-repair")
        self.assertEqual(contract["stage"], "Stage 9")
        self.assertEqual(contract["stage_name"], "回归防线与交付冻结")
        self.assertEqual(contract["phase_id"], "9.3")
        self.assertEqual(contract["phase_name"], "用户验收")
        self.assertTrue(contract["current_phase_only"])
        self.assertEqual(contract["max_phases_per_run"], 1)
        self.assertTrue(contract["phase_9_1_required"])
        self.assertTrue(contract["phase_9_2_required"])
        self.assertEqual(contract["task_ids"], ["T9.3.1", "T9.3.2", "T9.3.3"])
        self.assertEqual(
            contract["required_artifacts"],
            [
                "manual_acceptance.md",
                "reply_protocol.md",
                "evidence.json",
                "terminal.log",
                "changed_files.txt",
                "risk_and_rollback.md",
            ],
        )
        self.assertEqual(contract["acceptance_state"], "waiting_for_user_response")
        self.assertFalse(contract["user_acceptance_claimed"])
        self.assertFalse(contract["stage_9_whole_review_complete"])
        self.assertFalse(contract["github_main_uploaded"])
        self.assertFalse(contract["future_version_started"])
        self.assertFalse(contract["app_bundle_changes_allowed"])
        self.assertFalse(contract["data_logic_changes_allowed"])
        self.assertFalse(contract["formal_fake_financial_data_allowed"])
        self.assertIn("Stage 9 whole-stage review", contract["explicitly_not_done"])
        self.assertIn("future version work", contract["explicitly_not_done"])

    def test_manual_acceptance_checklist_requires_human_response_and_covers_stage8_9(self) -> None:
        manual_path = PHASE_DIR / "manual_acceptance.md"
        reply_path = PHASE_DIR / "reply_protocol.md"
        self.assertTrue(manual_path.exists(), str(manual_path))
        self.assertTrue(reply_path.exists(), str(reply_path))

        manual = manual_path.read_text(encoding="utf-8")
        reply = reply_path.read_text(encoding="utf-8")

        self.assertIn("等待用户验收", manual)
        self.assertIn("用户尚未确认交付冻结", manual)
        self.assertIn("10 个正式一级入口", manual)
        self.assertIn("app/浏览器 E2E", manual)
        self.assertIn("旧 UI、假零、入口堆叠", manual)
        self.assertIn("mock/sample/demo/synthetic/fixture/fake", manual)
        self.assertIn("不自动进入未来版本", manual)
        self.assertIn("回复 `1`", reply)
        self.assertIn("回复 `2`", reply)
        self.assertIn("回复 `3`", reply)
        self.assertNotIn("用户已验收", manual)
        self.assertNotIn("Stage 9 final closeout complete", manual)

    def test_phase93_evidence_pack_is_machine_readable_and_waiting(self) -> None:
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

        self.assertEqual(evidence["schema"], "PFIV024Stage9Phase93UserAcceptanceEvidenceV1")
        self.assertEqual(evidence["version"], "v0.2.3-repair")
        self.assertEqual(evidence["target_version"], "v0.2.4")
        self.assertEqual(evidence["stage"], "Stage 9")
        self.assertEqual(evidence["phase_id"], "9.3")
        self.assertEqual(evidence["status"], "waiting_for_user_acceptance")
        self.assertTrue(evidence["current_phase_only"])
        self.assertTrue(evidence["phase_9_1_guardrails_verified"])
        self.assertTrue(evidence["phase_9_2_delivery_freeze_verified"])
        self.assertFalse(evidence["user_acceptance_claimed"])
        self.assertFalse(evidence["stage_9_whole_review_complete"])
        self.assertFalse(evidence["github_main_uploaded"])
        self.assertFalse(evidence["future_version_started"])
        self.assertFalse(evidence["app_bundle_reinstall_executed"])
        self.assertFalse(evidence["data_logic_changes_made"])
        self.assertFalse(evidence["formal_fake_financial_data_added"])
        self.assertEqual(evidence["changed_files"], changed_files)

    def test_readme_and_handoff_stop_at_user_acceptance_wait_state(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        handoff = (ROOT / "HANDOFF.md").read_text(encoding="utf-8")

        self.assertIn("Stage 9 / Phase 9.3 - 用户验收", readme)
        self.assertIn("waiting for user response", readme)
        self.assertIn("Stage 9 whole-stage review: not started", readme)
        self.assertIn("GitHub main upload for Stage 9: not executed", readme)
        self.assertIn("Phase 9.3 用户验收材料已准备，等待用户回复", handoff)
        self.assertNotIn("Stage 9 user acceptance: complete", readme)
        self.assertNotIn("Stage 9 final closeout complete", readme)


if __name__ == "__main__":
    unittest.main()
