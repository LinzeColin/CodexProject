from __future__ import annotations

import json
import unittest
from pathlib import Path

from pfi_v02.stage_v024_repair_contract import build_v024_stage0_phase03_contract


ROOT = Path(__file__).resolve().parents[1]


class TestV024Stage0Phase03Contract(unittest.TestCase):
    def test_phase03_contract_closes_stage0_candidate_without_final_review(self) -> None:
        contract = build_v024_stage0_phase03_contract().to_dict()

        self.assertEqual(contract["target_version"], "v0.2.4")
        self.assertEqual(contract["source_package_version"], "v0.2.3-repair")
        self.assertEqual(contract["stage_id"], "Stage 0")
        self.assertEqual(contract["phase_id"], "0.3")
        self.assertEqual(contract["task_ids"], ["T0.3.1", "T0.3.2", "T0.3.3", "T0.3.4"])
        self.assertTrue(contract["phase_0_1_complete"])
        self.assertTrue(contract["phase_0_2_complete"])
        self.assertTrue(contract["phase_0_3_complete"])
        self.assertTrue(contract["stage_0_candidate_complete"])
        self.assertFalse(contract["stage_0_complete"])
        self.assertTrue(contract["whole_stage_review_required"])
        self.assertEqual(contract["max_phases_per_run"], 1)
        self.assertFalse(contract["business_ui_changes_allowed"])
        self.assertFalse(contract["data_logic_changes_allowed"])
        self.assertTrue(contract["next_phase_requires_user_acceptance"])

    def test_phase03_tests_official_navigation_and_market_research(self) -> None:
        contract = build_v024_stage0_phase03_contract().to_dict()

        self.assertEqual(contract["official_nav_count"], 10)
        self.assertEqual(
            contract["official_nav"],
            [
                "首页总览",
                "账户与资产",
                "账本流水",
                "投资管理",
                "消费管理",
                "数据源与上传",
                "建议与复盘",
                "报告与洞察",
                "市场与研究",
                "设置",
            ],
        )
        self.assertTrue(contract["market_research_top_level"])
        self.assertEqual(contract["official_nav"][8], "市场与研究")

        deprecated_aliases = set(contract["deprecated_top_level_aliases"])
        official_nav = set(contract["official_nav"])
        self.assertEqual(deprecated_aliases & official_nav, set())

    def test_phase03_tests_no_mock_financial_data_policy(self) -> None:
        contract = build_v024_stage0_phase03_contract().to_dict()

        self.assertTrue(contract["no_mock_financial_data"])
        self.assertEqual(
            contract["forbidden_financial_data_labels"],
            ["mock", "sample", "demo", "synthetic", "fixture", "fake"],
        )
        self.assertEqual(
            contract["financial_data_acceptance_policy"]["allowed"],
            "real_data_or_real_empty_blocking_state",
        )
        self.assertIn("mock/sample/demo/synthetic/fixture/fake", contract["financial_data_acceptance_policy"]["forbidden"])
        self.assertIn("not_loaded", contract["financial_data_acceptance_policy"]["not_loaded_zero_policy"])

    def test_phase03_evidence_pack_exists_and_matches_changed_files(self) -> None:
        evidence_dir = ROOT / "reports" / "pfi_v024" / "stage_0" / "phase_0_3"
        evidence_path = evidence_dir / "evidence.json"
        terminal_path = evidence_dir / "terminal.log"
        changed_files_path = evidence_dir / "changed_files.txt"
        risk_path = evidence_dir / "risk_and_rollback.md"

        for path in (evidence_path, terminal_path, changed_files_path, risk_path):
            self.assertTrue(path.exists(), str(path))

        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        changed_files = [line.strip() for line in changed_files_path.read_text(encoding="utf-8").splitlines() if line.strip()]

        self.assertEqual(evidence["schema"], "PFIV024Stage0Phase03EvidenceV1")
        self.assertEqual(evidence["version"], "v0.2.3-repair")
        self.assertEqual(evidence["target_version"], "v0.2.4")
        self.assertEqual(evidence["stage"], "Stage 0")
        self.assertEqual(evidence["phase_id"], "0.3")
        self.assertEqual(evidence["status"], "candidate_pass")
        self.assertTrue(evidence["allowed_files_obeyed"])
        self.assertTrue(evidence["phase_0_1_complete"])
        self.assertTrue(evidence["phase_0_2_complete"])
        self.assertTrue(evidence["phase_0_3_complete"])
        self.assertTrue(evidence["stage_0_candidate_complete"])
        self.assertFalse(evidence["stage_0_complete"])
        self.assertTrue(evidence["requires_user_acceptance"])
        self.assertTrue(evidence["no_auto_next_phase"])
        self.assertTrue(evidence["no_auto_closeout"])
        self.assertEqual(evidence["changed_files"], changed_files)
        self.assertTrue(evidence["acceptance_checks"]["official_nav_count_is_10"])
        self.assertTrue(evidence["acceptance_checks"]["market_research_is_top_level"])
        self.assertTrue(evidence["acceptance_checks"]["no_mock_financial_data"])
        self.assertTrue(evidence["acceptance_checks"]["evidence_pack_present"])
        self.assertEqual(evidence["screenshots"], [])


if __name__ == "__main__":
    unittest.main()
