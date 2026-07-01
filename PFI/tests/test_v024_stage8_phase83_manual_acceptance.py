from __future__ import annotations

import importlib
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
PHASE_DIR = ROOT / "reports" / "pfi_v024" / "stage_8" / "phase_8_3"
EXPECTED_TASK_IDS = ["T8.3.1", "T8.3.2", "T8.3.3"]


def load_stage8_module():
    try:
        return importlib.import_module("pfi_v02.stage_v024_stage8_e2e_acceptance")
    except ModuleNotFoundError:
        return None


class TestV024Stage8Phase83ManualAcceptance(unittest.TestCase):
    def test_phase83_contract_is_current_phase_only_and_does_not_claim_user_acceptance(self) -> None:
        stage8 = load_stage8_module()
        self.assertIsNotNone(stage8, "stage_v024_stage8_e2e_acceptance module is required")
        self.assertTrue(hasattr(stage8, "build_v024_stage8_phase83_contract"))

        contract = stage8.build_v024_stage8_phase83_contract().to_dict()

        self.assertEqual(contract["target_version"], "v0.2.4")
        self.assertEqual(contract["source_package_version"], "v0.2.3-repair")
        self.assertEqual(contract["stage"], "Stage 8")
        self.assertEqual(contract["stage_name"], "端到端浏览器与 app 验收")
        self.assertEqual(contract["phase_id"], "8.3")
        self.assertEqual(contract["phase_name"], "人工验收")
        self.assertTrue(contract["current_phase_only"])
        self.assertTrue(contract["max_one_phase_per_run"])
        self.assertTrue(contract["phase_8_1_required"])
        self.assertTrue(contract["phase_8_2_required"])
        self.assertEqual(contract["task_ids"], EXPECTED_TASK_IDS)
        self.assertFalse(contract["user_acceptance_claim_allowed_without_user_confirmation"])
        self.assertTrue(contract["no_auto_next_stage"])
        self.assertFalse(contract["stage_8_whole_review_complete"])
        self.assertFalse(contract["github_main_uploaded"])
        self.assertFalse(contract["stage_9_started"])
        self.assertIn("manual_acceptance.md", contract["required_artifacts"])
        self.assertIn("defects.md", contract["required_artifacts"])
        self.assertIn("Stage 8 whole-stage review", contract["explicitly_not_done"])
        self.assertIn("Stage 9 regression freeze", contract["explicitly_not_done"])
        self.assertIn("GitHub main upload", contract["explicitly_not_done"])

    def test_phase83_evidence_pack_is_machine_readable_and_pending_user_confirmation(self) -> None:
        paths = [
            PHASE_DIR / "evidence.json",
            PHASE_DIR / "manual_acceptance.md",
            PHASE_DIR / "defects.md",
            PHASE_DIR / "terminal.log",
            PHASE_DIR / "changed_files.txt",
            PHASE_DIR / "risk_and_rollback.md",
        ]
        for path in paths:
            self.assertTrue(path.exists(), str(path))
            self.assertGreater(path.stat().st_size, 0, str(path))

        evidence = json.loads((PHASE_DIR / "evidence.json").read_text(encoding="utf-8"))
        changed_files = [
            line.strip()
            for line in (PHASE_DIR / "changed_files.txt").read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

        self.assertEqual(evidence["schema"], "PFIV024Stage8Phase83EvidenceV1")
        self.assertEqual(evidence["target_version"], "v0.2.4")
        self.assertEqual(evidence["source_package_version"], "v0.2.3-repair")
        self.assertEqual(evidence["stage"], "Stage 8")
        self.assertEqual(evidence["phase_id"], "8.3")
        self.assertEqual(evidence["status"], "ready_for_user_acceptance")
        self.assertEqual(evidence["user_acceptance_status"], "pending_user_confirmation")
        self.assertFalse(evidence["user_acceptance_claimed"])
        self.assertTrue(evidence["phase_8_1_verified"])
        self.assertTrue(evidence["phase_8_2_verified"])
        self.assertEqual(evidence["task_ids"], EXPECTED_TASK_IDS)
        self.assertTrue(evidence["manual_acceptance_checklist_ready"])
        self.assertTrue(evidence["defects_file_ready"])
        self.assertTrue(evidence["no_auto_next_stage_rule_recorded"])
        self.assertFalse(evidence["stage_8_whole_review_complete"])
        self.assertFalse(evidence["github_main_uploaded"])
        self.assertFalse(evidence["stage_9_started"])
        self.assertFalse(evidence["app_bundle_reinstall_executed"])
        self.assertFalse(evidence["data_logic_changes_made"])
        self.assertFalse(evidence["formal_fake_financial_data_added"])
        self.assertEqual(evidence["changed_files"], changed_files)

    def test_manual_acceptance_checklist_has_real_user_steps_without_fake_pass_language(self) -> None:
        manual = (PHASE_DIR / "manual_acceptance.md").read_text(encoding="utf-8")

        required_phrases = [
            "待用户确认",
            "打开 PFI.app",
            "打开 localhost",
            "10 个一级入口",
            "核心二级页面",
            "浏览器后退/前进",
            "核心指标无假零",
            "报告中心",
            "亮色 UI",
            "移动端响应式",
            "不得进入 Stage 9",
        ]
        for phrase in required_phrases:
            self.assertIn(phrase, manual)

        forbidden_phrases = [
            "用户已验收",
            "用户验收通过",
            "Stage 8 whole-stage review complete",
            "Stage 9 started",
            "GitHub main uploaded",
        ]
        for phrase in forbidden_phrases:
            self.assertNotIn(phrase, manual)

    def test_defects_file_localizes_failures_and_open_items_without_claiming_none_unconditionally(self) -> None:
        defects = (PHASE_DIR / "defects.md").read_text(encoding="utf-8")

        self.assertIn("未确认产品缺陷", defects)
        self.assertIn("待用户人工验收", defects)
        self.assertIn("D8.3-PENDING-001", defects)
        self.assertIn("D8.3-ENV-001", defects)
        self.assertIn("/Applications/PFI.app", defects)
        self.assertIn("~/Downloads/PFI.app", defects)
        self.assertIn("不在本 phase 重装", defects)
        self.assertNotIn("无任何缺陷", defects)
        self.assertNotIn("用户已验收", defects)

    def test_stage8_docs_and_run_contract_are_phase83_current_and_stop_before_stage9(self) -> None:
        doc = (ROOT / "docs" / "pfi_v024" / "STAGE8_E2E_ACCEPTANCE.md").read_text(encoding="utf-8")
        run_contract = (ROOT / "docs" / "pfi_v024" / "RUN_CONTRACT.md").read_text(encoding="utf-8")

        self.assertIn("Stage 8 Phase 8.3", doc)
        self.assertIn("manual_acceptance.md", doc)
        self.assertIn("defects.md", doc)
        self.assertIn("待用户确认", doc)
        self.assertIn("Stage 8 / Phase 8.3 - 人工验收", run_contract)
        self.assertIn("不执行 Stage 8 whole-stage review", run_contract)
        self.assertIn("不执行 Stage 9", run_contract)
        self.assertNotIn("用户已验收", doc)
        self.assertNotIn("Stage 9 started", doc)


if __name__ == "__main__":
    unittest.main()
