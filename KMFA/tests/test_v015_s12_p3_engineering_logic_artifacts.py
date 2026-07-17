from __future__ import annotations

import json
import unittest

from KMFA.tools import build_v015_s12_p3_engineering_logic as builder


class S12P3ArtifactTests(unittest.TestCase):
    def test_builder_outputs_are_deterministic(self) -> None:
        builder.check_outputs()

    def test_dependency_is_accepted_s12_p2(self) -> None:
        dependency = builder.dependency()
        self.assertEqual(dependency["acceptance_status"], "PASSED")
        self.assertEqual(dependency["validation_receipt_count"], 21)
        self.assertTrue(dependency["s12_p3_entry_allowed"])
        self.assertFalse(dependency["s12_p3_started"])

    def test_accepted_manifest_opens_only_stage_review(self) -> None:
        manifest = json.loads(builder.MANIFEST_PATH.read_text(encoding="utf-8"))
        self.assertEqual(manifest["phase_acceptance_status"], "PASSED")
        self.assertEqual(manifest["stage_execution_percentage"], 100)
        self.assertEqual(manifest["overall_accepted_phase_count"], 34)
        self.assertTrue(manifest["s12_stage_review_entry_allowed"])
        self.assertFalse(manifest["s12_stage_review_started"])
        self.assertFalse(manifest["github_upload_performed"])
        self.assertFalse(manifest["app_reinstall_performed"])

    def test_change_chain_excludes_unsupported_change(self) -> None:
        evidence = json.loads(builder.CHANGE_CHAIN_PATH.read_text(encoding="utf-8"))
        result = evidence["confirmed_case"]
        self.assertEqual(result["confirmed_change_amount_cents"], 20000)
        self.assertEqual(result["unconfirmed_change_amount_cents"], 15000)
        self.assertEqual(result["unsupported_change_recognized_cents"], 0)
        self.assertEqual(result["settlement_difference_cents"], -5000)
        self.assertEqual(result["invoice_collection_rate_bps"], 7778)

    def test_cost_chain_identifies_required_anomalies(self) -> None:
        evidence = json.loads(builder.COST_CHAIN_PATH.read_text(encoding="utf-8"))["result"]
        self.assertEqual(evidence["duplicate_record_count"], 1)
        self.assertEqual(evidence["requires_confirmation_count"], 1)
        self.assertEqual(evidence["cross_project_anomaly_count"], 1)
        self.assertEqual(evidence["automatic_low_confidence_allocation_count"], 0)
        self.assertEqual(evidence["inventory_conservation_delta_cents"], 0)

    def test_explanation_is_consistent_and_tampering_is_detected(self) -> None:
        evidence = json.loads(builder.EXPLANATION_PATH.read_text(encoding="utf-8"))
        self.assertTrue(evidence["consistency"]["consistency_pass"])
        self.assertEqual(evidence["consistency"]["mismatch_count"], 0)
        self.assertFalse(evidence["tampered_case_consistency"]["consistency_pass"])
        self.assertGreaterEqual(evidence["tampered_case_consistency"]["mismatch_count"], 1)

    def test_public_evidence_has_exact_check_accounting(self) -> None:
        evidence = json.loads(builder.VERIFICATION_PATH.read_text(encoding="utf-8"))
        self.assertEqual(evidence["accounting"], {"total": 63, "passed": 63, "failed": 0})
        self.assertEqual(evidence["failed_checks"], [])
        self.assertEqual(evidence["raw_root_access_count"], 0)
        self.assertEqual(evidence["live_source_read_count"], 0)

    def test_task_matrix_has_exact_three_accepted_tasks(self) -> None:
        matrix = json.loads(builder.TASK_MATRIX_PATH.read_text(encoding="utf-8"))
        self.assertEqual(matrix["task_count"], 3)
        self.assertEqual(matrix["task_accepted_count"], 3)
        self.assertEqual([row["task_id"] for row in matrix["tasks"]], ["S12P3T01", "S12P3T02", "S12P3T03"])
        self.assertEqual({row["status"] for row in matrix["tasks"]}, {"PASSED"})


if __name__ == "__main__":
    unittest.main()
