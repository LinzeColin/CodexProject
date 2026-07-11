#!/usr/bin/env python3
"""Behavior tests for current KMFA v0.1.4 Stage 17 review."""

from __future__ import annotations

import json
import unittest
from pathlib import Path


GENERATOR_PATH = Path("KMFA/tools/v014_s17_post_remediation_stage_review.py")
CHECKER_PATH = Path("KMFA/tools/check_v014_s17_post_remediation_stage_review.py")
IMPLEMENTATION_EXISTS = GENERATOR_PATH.is_file() and CHECKER_PATH.is_file()


class V014S17PostRemediationStageReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not IMPLEMENTATION_EXISTS:
            return
        from KMFA.tools import v014_s17_post_remediation_stage_review as review
        from KMFA.tools.check_v014_s17_post_remediation_stage_review import (
            validate_v014_s17_post_remediation_stage_review,
        )

        cls.review = review
        cls.manifest = validate_v014_s17_post_remediation_stage_review(
            require_private_evidence=True,
            require_final_evidence=True,
        )
        cls.summary = json.loads(review.SUMMARY_PATH.read_text(encoding="utf-8"))
        cls.contracts = cls._read_jsonl(review.CONTRACT_MATRIX_PATH)
        cls.phase_results = cls._read_jsonl(review.PHASE_RESULTS_PATH)

    @staticmethod
    def _read_jsonl(path: Path) -> list[dict[str, object]]:
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]

    def test_implementation_exists(self) -> None:
        self.assertTrue(GENERATOR_PATH.is_file(), f"missing generator: {GENERATOR_PATH}")
        self.assertTrue(CHECKER_PATH.is_file(), f"missing checker: {CHECKER_PATH}")

    @unittest.skipUnless(IMPLEMENTATION_EXISTS, "implementation not written yet")
    def test_identity_and_current_phase_chain(self) -> None:
        self.assertEqual(self.manifest["phase_id"], self.review.PHASE_ID)
        self.assertEqual(self.manifest["roadmap_phase_id"], "STAGE-REVIEW")
        self.assertEqual(self.manifest["task_id"], self.review.TASK_ID)
        self.assertEqual(self.manifest["acceptance_id"], self.review.ACCEPTANCE_ID)
        self.assertEqual(self.summary["phase_results"], {"S17-P1": "PASS", "S17-P2": "PASS", "S17-P3": "PASS"})
        self.assertTrue(self.manifest["historical_stage17_review_validated"])
        self.assertFalse(self.manifest["historical_stage17_dynamic_state_is_authoritative"])

    @unittest.skipUnless(IMPLEMENTATION_EXISTS, "implementation not written yet")
    def test_all_phase_tests_and_validators_are_replayed(self) -> None:
        self.assertEqual(len(self.phase_results), 3)
        self.assertEqual(sum(row["focused_test_count"] for row in self.phase_results), 30)
        self.assertTrue(all(row["focused_test_status"] == "PASS" for row in self.phase_results))
        self.assertTrue(all(row["strict_validator_status"] == "PASS" for row in self.phase_results))
        self.assertEqual(self.summary["phase_focused_test_pass_count"], 30)
        self.assertEqual(self.summary["phase_strict_validator_pass_count"], 3)

    @unittest.skipUnless(IMPLEMENTATION_EXISTS, "implementation not written yet")
    def test_cross_phase_role_and_audit_contracts_are_exact(self) -> None:
        self.assertEqual(len(self.contracts), 6)
        self.assertTrue(all(row["status"] == "PASS" for row in self.contracts))
        self.assertEqual(self.summary["canonical_role_count"], 4)
        self.assertEqual(self.summary["notification_recipient_role_match_count"], 3)
        self.assertEqual(self.summary["runbook_owner_role_match_count"], 4)
        self.assertEqual(self.summary["knowledge_owner_role_match_count"], 2)
        self.assertEqual(self.summary["runbook_audit_mapping_match_count"], 4)
        self.assertEqual(self.summary["cross_phase_contract_mismatch_count"], 0)

    @unittest.skipUnless(IMPLEMENTATION_EXISTS, "implementation not written yet")
    def test_review_findings_are_real_and_closed(self) -> None:
        findings = self.manifest["review_findings"]
        self.assertEqual(len(findings), 11)
        self.assertEqual(sum(row["status"] == "fixed" for row in findings), 7)
        self.assertEqual(sum(row["status"] == "passed" for row in findings), 4)
        self.assertEqual(sum(row["status"] == "open" for row in findings), 0)
        self.assertEqual(self.summary["fixed_review_finding_count"], 7)
        self.assertEqual(self.summary["open_review_finding_count"], 0)

    @unittest.skipUnless(IMPLEMENTATION_EXISTS, "implementation not written yet")
    def test_stage_gate_preserves_current_business_state(self) -> None:
        self.assertEqual(self.summary["role_count"], 4)
        self.assertEqual(self.summary["notification_rule_count"], 3)
        self.assertEqual(self.summary["metadata_outbox_log_count"], 3)
        self.assertEqual(self.summary["operation_runbook_count"], 4)
        self.assertEqual(self.summary["knowledge_item_count"], 2)
        self.assertEqual(self.summary["error_drill_scenario_count"], 2)
        self.assertEqual(self.summary["backup_restore_drill_count"], 1)
        self.assertEqual(self.summary["real_notification_delivery_count"], 0)
        self.assertEqual(self.summary["production_restore_count"], 0)
        self.assertEqual(self.summary["business_execution_count"], 0)

    @unittest.skipUnless(IMPLEMENTATION_EXISTS, "implementation not written yet")
    def test_raw_quality_and_downstream_boundaries_are_locked(self) -> None:
        self.assertEqual(self.summary["raw_source_file_count"], 5)
        self.assertTrue(self.summary["raw_snapshot_exact_match"])
        self.assertTrue(self.summary["raw_cross_phase_snapshot_exact_match"])
        self.assertEqual(self.summary["current_data_quality_grade"], "Q4")
        self.assertEqual(self.summary["current_report_grade"], "D")
        self.assertEqual(self.summary["decision"], "NO_GO")
        self.assertTrue(self.summary["stage17_review_performed"])
        for key, value in self.review._review_boundaries().items():
            if key in {"s17_p1_performed", "s17_p2_performed", "s17_p3_performed", "stage17_review_performed"}:
                self.assertTrue(value, key)
            else:
                self.assertFalse(value, key)

    @unittest.skipUnless(IMPLEMENTATION_EXISTS, "implementation not written yet")
    def test_acceptance_governance_and_next_phase_are_locked(self) -> None:
        self.assertEqual(self.manifest["acceptance_matrix"]["check_fail_count"], 0)
        self.assertEqual(self.manifest["go_no_go"]["decision"], "NO_GO")
        self.assertEqual(self.manifest["next_phase"], "S18-P1")
        self.assertFalse(self.manifest["go_no_go"]["s18_p1_allowed_in_this_run"])
        self.assertFalse(self.manifest["go_no_go"]["github_upload_allowed"])
        formula = Path("KMFA/docs/governance/formula_registry.yaml").read_text(encoding="utf-8")
        parameters = Path("KMFA/docs/governance/parameter_registry.csv").read_text(encoding="utf-8")
        handoff = Path("KMFA/HANDOFF.md").read_text(encoding="utf-8")
        self.assertIn(self.review.FORMULA_ID, formula)
        for parameter_id in self.review.PARAMETER_IDS:
            self.assertIn(parameter_id, parameters)
        self.assertIn("下一步只能执行 S18-P1", handoff)
        self.assertIn("不得执行 S18-P2", handoff)
        self.assertIn("不得执行 GitHub upload", handoff)


if __name__ == "__main__":
    unittest.main()
