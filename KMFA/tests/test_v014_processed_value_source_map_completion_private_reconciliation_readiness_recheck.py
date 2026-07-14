from __future__ import annotations

import unittest

from KMFA.tools import v014_processed_value_source_map_completion_private_reconciliation_readiness_recheck as generator
from KMFA.tools.check_v014_processed_value_source_map_completion_private_reconciliation_readiness_recheck import validate


class PrivateReconciliationReadinessRecheckTest(unittest.TestCase):
    def setUp(self) -> None:
        self.manifest = generator.generate(generated_at="2026-07-06T00:00:00+10:00")

    def test_readiness_remains_no_go(self) -> None:
        summary = self.manifest["summary"]
        self.assertEqual(summary["decision"], "NO_GO")
        self.assertEqual(summary["decision_track_count"], 5)
        self.assertEqual(summary["keep_blocked_decision_count"], 5)
        self.assertEqual(summary["resolution_applied_decision_count"], 0)
        self.assertEqual(summary["private_decision_queue_count"], 113)
        self.assertEqual(summary["blocked_private_decision_count"], 113)
        self.assertEqual(summary["full_reconciliation_allowed_private_decision_count"], 0)

    def test_matrix_proves_full_reconciliation_not_ready(self) -> None:
        matrix = self.manifest["readiness_matrix"]
        self.assertEqual(matrix["readiness_check_count"], 8)
        self.assertEqual(matrix["readiness_pass_count"], 2)
        self.assertEqual(matrix["readiness_fail_count"], 6)
        self.assertFalse(matrix["full_reconciliation_ready"])
        self.assertFalse(matrix["full_reconciliation_allowed"])

    def test_downstream_gates_stay_closed(self) -> None:
        summary = self.manifest["summary"]
        self.assertFalse(summary["full_reconciliation_ready"])
        self.assertFalse(summary["full_reconciliation_allowed"])
        self.assertFalse(summary["full_raw_to_processed_reconciliation_performed_by_this_phase"])
        self.assertFalse(summary["raw_to_processed_value_comparison_performed_by_this_phase"])
        self.assertFalse(summary["processed_data_reconciliation_performed"])
        self.assertFalse(summary["business_value_consistency_verified"])
        self.assertFalse(summary["lineage_full_check_complete"])
        self.assertFalse(summary["formal_report_allowed"])
        self.assertFalse(summary["github_upload_performed"])
        self.assertFalse(summary["app_reinstall_performed"])
        self.assertFalse(summary["business_execution_performed"])

    def test_raw_boundary_and_private_outputs(self) -> None:
        summary = self.manifest["summary"]
        boundary = summary["raw_boundary"]
        self.assertFalse(boundary["raw_inbox_read_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_list_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_stat_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_parse_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_mutated_by_this_phase"])
        self.assertTrue(summary["private_diagnostic_gitignored"])
        self.assertTrue(summary["private_queue_status_gitignored"])

    def test_validator_accepts_private_diagnostic(self) -> None:
        manifest = validate(require_private_diagnostic=True)
        self.assertEqual(manifest["summary"]["blocked_private_decision_count"], 113)
        self.assertFalse(manifest["summary"]["full_reconciliation_ready"])


if __name__ == "__main__":
    unittest.main()
