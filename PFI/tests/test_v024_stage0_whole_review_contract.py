from __future__ import annotations

import json
import unittest
from pathlib import Path

from pfi_v02.stage_v024_repair_contract import build_v024_stage0_whole_review_contract


ROOT = Path(__file__).resolve().parents[1]


class TestV024Stage0WholeReviewContract(unittest.TestCase):
    def test_whole_review_marks_stage0_complete_without_opening_stage1(self) -> None:
        contract = build_v024_stage0_whole_review_contract().to_dict()

        self.assertEqual(contract["target_version"], "v0.2.4")
        self.assertEqual(contract["source_package_version"], "v0.2.3-repair")
        self.assertEqual(contract["stage_id"], "Stage 0")
        self.assertEqual(contract["review_id"], "stage_0_whole_review")
        self.assertEqual(contract["reviewed_phase_ids"], ["0.1", "0.2", "0.3"])
        self.assertTrue(contract["phase_0_1_complete"])
        self.assertTrue(contract["phase_0_2_complete"])
        self.assertTrue(contract["phase_0_3_complete"])
        self.assertTrue(contract["stage_0_candidate_complete"])
        self.assertTrue(contract["stage_0_review_complete"])
        self.assertTrue(contract["stage_0_complete"])
        self.assertFalse(contract["stage_1_allowed_without_user_instruction"])
        self.assertTrue(contract["next_stage_requires_user_acceptance"])
        self.assertFalse(contract["business_ui_changes_allowed"])
        self.assertFalse(contract["data_logic_changes_allowed"])
        self.assertFalse(contract["app_bundle_changes_allowed"])

    def test_whole_review_preserves_repair_contract_invariants(self) -> None:
        contract = build_v024_stage0_whole_review_contract().to_dict()

        self.assertEqual(contract["official_nav_count"], 10)
        self.assertEqual(contract["official_nav"][8], "市场与研究")
        self.assertTrue(contract["market_research_top_level"])
        self.assertTrue(contract["no_mock_financial_data"])
        self.assertEqual(
            contract["forbidden_financial_data_labels"],
            ["mock", "sample", "demo", "synthetic", "fixture", "fake"],
        )

        constraints = {item["constraint_id"]: item for item in contract["deprecated_constraints"]}
        self.assertEqual(constraints["old_nine_entry_primary_nav"]["status"], "deprecated")
        self.assertEqual(constraints["market_research_top_level_ban"]["status"], "deprecated")
        self.assertEqual(constraints["dark_ai_console_default_direction"]["status"], "deprecated")
        self.assertEqual(constraints["sample_data_acceptance"]["status"], "deprecated")

    def test_whole_review_evidence_and_findings_are_present(self) -> None:
        evidence_dir = ROOT / "reports" / "pfi_v024" / "stage_0" / "whole_stage_review"
        evidence_path = evidence_dir / "evidence.json"
        terminal_path = evidence_dir / "terminal.log"
        changed_files_path = evidence_dir / "changed_files.txt"
        risk_path = evidence_dir / "risk_and_rollback.md"
        review_doc_path = ROOT / "docs" / "pfi_v024" / "STAGE0_WHOLE_STAGE_REVIEW.md"

        for path in (evidence_path, terminal_path, changed_files_path, risk_path, review_doc_path):
            self.assertTrue(path.exists(), str(path))

        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        changed_files = [line.strip() for line in changed_files_path.read_text(encoding="utf-8").splitlines() if line.strip()]

        self.assertEqual(evidence["schema"], "PFIV024Stage0WholeReviewEvidenceV1")
        self.assertEqual(evidence["version"], "v0.2.3-repair")
        self.assertEqual(evidence["target_version"], "v0.2.4")
        self.assertEqual(evidence["stage"], "Stage 0")
        self.assertEqual(evidence["review_id"], "stage_0_whole_review")
        self.assertEqual(evidence["status"], "pass")
        self.assertTrue(evidence["stage_0_review_complete"])
        self.assertTrue(evidence["stage_0_complete"])
        self.assertFalse(evidence["stage_1_allowed_without_user_instruction"])
        self.assertTrue(evidence["next_stage_requires_user_acceptance"])
        self.assertEqual(evidence["changed_files"], changed_files)
        self.assertEqual({item["status"] for item in evidence["review_findings"]}, {"fixed"})
        self.assertTrue(evidence["acceptance_checks"]["all_phase_evidence_present"])
        self.assertTrue(evidence["acceptance_checks"]["official_nav_count_is_10"])
        self.assertTrue(evidence["acceptance_checks"]["market_research_is_top_level"])
        self.assertTrue(evidence["acceptance_checks"]["deprecated_constraints_recorded"])
        self.assertTrue(evidence["acceptance_checks"]["no_mock_financial_data"])
        self.assertTrue(evidence["acceptance_checks"]["no_business_ui_or_data_logic_changes"])


if __name__ == "__main__":
    unittest.main()
