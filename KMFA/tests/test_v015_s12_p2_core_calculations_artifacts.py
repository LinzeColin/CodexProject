from __future__ import annotations

import json
import unittest

from KMFA.tools import build_v015_s12_p2_core_calculations as builder


class S12P2ArtifactTests(unittest.TestCase):
    def test_builder_outputs_are_deterministic(self) -> None:
        builder.check_outputs()

    def test_dependency_is_accepted_s12_p1(self) -> None:
        dependency = builder.dependency()
        self.assertEqual(dependency["acceptance_status"], "PASSED")
        self.assertEqual(dependency["validation_receipt_count"], 21)
        self.assertTrue(dependency["s12_p2_entry_allowed"])
        self.assertFalse(dependency["s12_p2_started"])

    def test_final_manifest_opens_only_s12_p3(self) -> None:
        manifest = json.loads(builder.MANIFEST_PATH.read_text(encoding="utf-8"))
        self.assertEqual(manifest["phase_acceptance_status"], "PASSED")
        self.assertEqual(manifest["stage_execution_percentage"], 67)
        self.assertEqual(manifest["overall_accepted_phase_count"], 33)
        self.assertTrue(manifest["s12_p3_entry_allowed"])
        self.assertFalse(manifest["s12_p3_started"])
        self.assertFalse(manifest["github_upload_performed"])
        self.assertFalse(manifest["app_reinstall_performed"])

    def test_margin_baseline_is_zero_difference(self) -> None:
        evidence = json.loads(builder.MARGIN_BASELINE_PATH.read_text(encoding="utf-8"))
        self.assertTrue(evidence["comparison"]["zero_difference_pass"])
        self.assertEqual(set(evidence["comparison"]["differences_cents"].values()), {0})

    def test_cash_chain_excludes_uncollected_money(self) -> None:
        evidence = json.loads(builder.CASH_CHAIN_PATH.read_text(encoding="utf-8"))
        self.assertEqual(evidence["confirmed_case"]["uncollected_amount_counted_as_cash_cents"], 0)
        self.assertEqual(evidence["unresolved_account_case"]["calculation_status"], "DEGRADED_REQUIRES_CONFIRMATION")
        self.assertFalse(evidence["unresolved_account_case"]["business_decision_allowed"])

    def test_cost_risk_policy_is_external_and_adjustable(self) -> None:
        policy = json.loads(builder.RISK_POLICY_PATH.read_text(encoding="utf-8"))
        evidence = json.loads(builder.RISK_RULE_PATH.read_text(encoding="utf-8"))
        self.assertTrue(policy["thresholds_external_and_adjustable"])
        self.assertEqual(evidence["default_policy_case"]["conclusion"], "DETERMINATE_ALERT")
        self.assertEqual(evidence["adjusted_policy_case"]["conclusion"], "DETERMINATE_CLEAR")
        self.assertEqual(evidence["missing_data_case"]["conclusion"], "INSUFFICIENT_DATA")

    def test_public_evidence_has_exact_check_accounting(self) -> None:
        evidence = json.loads(builder.VERIFICATION_PATH.read_text(encoding="utf-8"))
        self.assertEqual(evidence["accounting"], {"total": 48, "passed": 48, "failed": 0})
        self.assertEqual(evidence["failed_checks"], [])
        self.assertEqual(evidence["raw_root_access_count"], 0)
        self.assertEqual(evidence["live_source_read_count"], 0)

    def test_task_matrix_has_exact_three_tasks(self) -> None:
        matrix = json.loads(builder.TASK_MATRIX_PATH.read_text(encoding="utf-8"))
        self.assertEqual(matrix["task_count"], 3)
        self.assertEqual([row["task_id"] for row in matrix["tasks"]], ["S12P2T01", "S12P2T02", "S12P2T03"])


if __name__ == "__main__":
    unittest.main()
