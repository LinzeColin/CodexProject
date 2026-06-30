from __future__ import annotations

import json
import unittest
from pathlib import Path

from pfi_v02.stage_v024_repair_contract import build_v024_stage0_phase01_contract


ROOT = Path(__file__).resolve().parents[1]


class TestV024Stage0Phase01Contract(unittest.TestCase):
    def test_phase01_contract_freezes_repair_scope_without_closing_stage0(self) -> None:
        contract = build_v024_stage0_phase01_contract().to_dict()

        self.assertEqual(contract["target_version"], "v0.2.4")
        self.assertEqual(contract["source_package_version"], "v0.2.3-repair")
        self.assertEqual(contract["stage_id"], "Stage 0")
        self.assertEqual(contract["phase_id"], "0.1")
        self.assertEqual(contract["task_ids"], ["T0.1.1", "T0.1.2", "T0.1.3", "T0.1.4"])
        self.assertTrue(contract["phase_0_1_complete"])
        self.assertFalse(contract["stage_0_complete"])
        self.assertEqual(contract["max_phases_per_run"], 1)
        self.assertFalse(contract["business_ui_changes_allowed"])
        self.assertFalse(contract["data_logic_changes_allowed"])
        self.assertTrue(contract["next_phase_requires_user_acceptance"])

    def test_phase01_contract_locks_navigation_and_data_trust_rules(self) -> None:
        contract = build_v024_stage0_phase01_contract().to_dict()

        self.assertEqual(len(contract["official_nav"]), 10)
        self.assertEqual(contract["official_nav"][8], "市场与研究")
        self.assertTrue(contract["market_research_top_level"])
        self.assertTrue(contract["no_mock_financial_data"])
        self.assertEqual(
            contract["forbidden_financial_data_labels"],
            ["mock", "sample", "demo", "synthetic", "fixture", "fake"],
        )
        self.assertIn("confirmed_zero", contract["data_state_requirements"])
        self.assertIn("not_loaded", contract["data_state_requirements"])
        self.assertIn("path_error", contract["data_state_requirements"])
        self.assertIn("ready", contract["data_state_requirements"])
        self.assertTrue(contract["one_stage_per_round_rule"])

    def test_phase01_docs_and_evidence_are_present_and_phase_bounded(self) -> None:
        scope_doc = ROOT / "docs" / "pfi_v024" / "REPAIR_SCOPE_LOCK.md"
        evidence_path = ROOT / "reports" / "pfi_v024" / "stage_0" / "phase_0_1" / "evidence.json"
        changed_files_path = ROOT / "reports" / "pfi_v024" / "stage_0" / "phase_0_1" / "changed_files.txt"
        risk_path = ROOT / "reports" / "pfi_v024" / "stage_0" / "phase_0_1" / "risk_and_rollback.md"

        for path in (scope_doc, evidence_path, changed_files_path, risk_path):
            self.assertTrue(path.exists(), str(path))

        text = scope_doc.read_text(encoding="utf-8")
        for phrase in (
            "v0.2.4",
            "v0.2.3-repair",
            "市场与研究",
            "每次 run work 最多只完成一个 phase",
            "Stage 0 未完成",
        ):
            self.assertIn(phrase, text)

        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        changed_files = [line.strip() for line in changed_files_path.read_text(encoding="utf-8").splitlines() if line.strip()]

        self.assertEqual(evidence["schema"], "PFIV024Stage0Phase01EvidenceV1")
        self.assertEqual(evidence["target_version"], "v0.2.4")
        self.assertEqual(evidence["stage"], "Stage 0")
        self.assertEqual(evidence["phase_id"], "0.1")
        self.assertEqual(evidence["status"], "candidate_pass")
        self.assertTrue(evidence["phase_0_1_complete"])
        self.assertFalse(evidence["stage_0_complete"])
        self.assertTrue(evidence["requires_user_acceptance"])
        self.assertTrue(evidence["no_auto_next_phase"])
        self.assertEqual(evidence["changed_files"], changed_files)
        self.assertTrue(evidence["acceptance_checks"]["repair_scope_lock_present"])
        self.assertTrue(evidence["acceptance_checks"]["machine_contract_present"])
        self.assertTrue(evidence["acceptance_checks"]["no_business_ui_or_data_logic_changes"])


if __name__ == "__main__":
    unittest.main()

