from __future__ import annotations

import json
import unittest
from pathlib import Path

from pfi_v02.stage_v024_repair_contract import build_v024_stage0_phase02_contract


ROOT = Path(__file__).resolve().parents[1]


class TestV024Stage0Phase02Contract(unittest.TestCase):
    def test_phase02_contract_deprecates_conflicting_history_without_closing_stage0(self) -> None:
        contract = build_v024_stage0_phase02_contract().to_dict()

        self.assertEqual(contract["target_version"], "v0.2.4")
        self.assertEqual(contract["source_package_version"], "v0.2.3-repair")
        self.assertEqual(contract["stage_id"], "Stage 0")
        self.assertEqual(contract["phase_id"], "0.2")
        self.assertEqual(contract["task_ids"], ["T0.2.1", "T0.2.2", "T0.2.3", "T0.2.4"])
        self.assertTrue(contract["phase_0_1_complete"])
        self.assertTrue(contract["phase_0_2_complete"])
        self.assertFalse(contract["stage_0_complete"])
        self.assertEqual(contract["max_phases_per_run"], 1)
        self.assertFalse(contract["business_ui_changes_allowed"])
        self.assertFalse(contract["data_logic_changes_allowed"])
        self.assertTrue(contract["next_phase_requires_user_acceptance"])

    def test_deprecated_constraints_and_retained_principles_are_explicit(self) -> None:
        contract = build_v024_stage0_phase02_contract().to_dict()
        constraints = {item["constraint_id"]: item for item in contract["deprecated_constraints"]}

        self.assertEqual(constraints["old_nine_entry_primary_nav"]["status"], "deprecated")
        self.assertIn("10 个正式一级入口", constraints["old_nine_entry_primary_nav"]["replacement"])
        self.assertEqual(constraints["market_research_top_level_ban"]["status"], "deprecated")
        self.assertIn("市场与研究", constraints["market_research_top_level_ban"]["replacement"])
        self.assertEqual(constraints["dark_ai_console_default_direction"]["status"], "deprecated")
        self.assertEqual(contract["default_visual_direction"], "light_human_product_experience")
        self.assertTrue(contract["market_research_top_level"])
        self.assertEqual(len(contract["official_nav"]), 10)

        principles = "\n".join(contract["retained_reference_principles"])
        self.assertIn("不得用 README/docs 声明替代真实 evidence", principles)
        self.assertIn("mock/sample/demo/synthetic/fixture/fake", principles)
        self.assertIn("localStorage", principles)

    def test_phase02_doc_and_evidence_are_present(self) -> None:
        doc_path = ROOT / "docs" / "pfi_v024" / "HISTORY_DEPRECATION_POLICY.md"
        evidence_path = ROOT / "reports" / "pfi_v024" / "stage_0" / "phase_0_2" / "evidence.json"
        changed_files_path = ROOT / "reports" / "pfi_v024" / "stage_0" / "phase_0_2" / "changed_files.txt"
        risk_path = ROOT / "reports" / "pfi_v024" / "stage_0" / "phase_0_2" / "risk_and_rollback.md"

        for path in (doc_path, evidence_path, changed_files_path, risk_path):
            self.assertTrue(path.exists(), str(path))

        text = doc_path.read_text(encoding="utf-8")
        for phrase in (
            "历史 9 入口正式约束",
            "市场与研究",
            "暗色 AI 控制台",
            "Retained Reference Principles",
            "Stage 0 仍未完成",
        ):
            self.assertIn(phrase, text)

        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        changed_files = [line.strip() for line in changed_files_path.read_text(encoding="utf-8").splitlines() if line.strip()]

        self.assertEqual(evidence["schema"], "PFIV024Stage0Phase02EvidenceV1")
        self.assertEqual(evidence["target_version"], "v0.2.4")
        self.assertEqual(evidence["stage"], "Stage 0")
        self.assertEqual(evidence["phase_id"], "0.2")
        self.assertEqual(evidence["status"], "candidate_pass")
        self.assertTrue(evidence["phase_0_1_complete"])
        self.assertTrue(evidence["phase_0_2_complete"])
        self.assertFalse(evidence["phase_0_3_complete"])
        self.assertFalse(evidence["stage_0_complete"])
        self.assertTrue(evidence["requires_user_acceptance"])
        self.assertTrue(evidence["no_auto_next_phase"])
        self.assertEqual(evidence["changed_files"], changed_files)
        self.assertTrue(evidence["acceptance_checks"]["old_nine_entry_constraint_deprecated"])
        self.assertTrue(evidence["acceptance_checks"]["market_research_ban_deprecated"])
        self.assertTrue(evidence["acceptance_checks"]["dark_ai_console_direction_deprecated"])
        self.assertTrue(evidence["acceptance_checks"]["retained_reference_principles_present"])


if __name__ == "__main__":
    unittest.main()

