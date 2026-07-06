from __future__ import annotations

import unittest

from KMFA.tools import v014_processed_value_source_map_completion_private_blocker_resolution_decision_intake as generator
from KMFA.tools.check_v014_processed_value_source_map_completion_private_blocker_resolution_decision_intake import validate


class ProcessedValueSourceMapCompletionPrivateBlockerResolutionDecisionIntakeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = generator.generate(
            generated_at="2026-07-06T00:00:00+10:00",
            write_governance_event=False,
        )

    def test_conservative_decision_counts(self) -> None:
        summary = self.manifest["summary"]
        self.assertEqual(summary["decision"], "NO_GO")
        self.assertTrue(summary["blocker_resolution_decision_intake_performed"])
        self.assertEqual(summary["decision_track_count"], 5)
        self.assertEqual(summary["keep_blocked_decision_count"], 5)
        self.assertEqual(summary["resolution_applied_decision_count"], 0)
        self.assertFalse(summary["corrected_private_source_provided"])
        self.assertFalse(summary["owner_exclusion_or_disambiguation_provided"])
        self.assertEqual(summary["private_resolution_queue_count"], 113)
        self.assertEqual(summary["private_decision_queue_count"], 113)
        self.assertEqual(
            summary["private_decision_status_counts"]["keep_blocked_pending_corrected_source_or_owner_exclusion"],
            36,
        )
        self.assertEqual(
            summary["private_decision_status_counts"]["keep_blocked_pending_private_disambiguation"],
            77,
        )

    def test_decision_matrix_keeps_all_tracks_blocked(self) -> None:
        matrix = self.manifest["decision_matrix"]
        self.assertTrue(matrix["all_decisions_intaken"])
        self.assertEqual(matrix["keep_blocked_decision_count"], 5)
        self.assertEqual(matrix["resolution_applied_decision_count"], 0)
        self.assertFalse(matrix["corrected_private_source_provided"])
        self.assertFalse(matrix["owner_exclusion_or_disambiguation_provided"])
        for row in matrix["decision_rows"]:
            self.assertEqual(row["decision_code"], "keep_blocked_no_resolution_evidence")
            self.assertFalse(row["resolution_applied"])
            self.assertFalse(row["full_reconciliation_allowed_after_decision"])
            self.assertFalse(row["delivery_claim_allowed_after_decision"])

    def test_gates_and_raw_boundary_remain_closed(self) -> None:
        summary = self.manifest["summary"]
        self.assertFalse(summary["resolution_applied_by_this_phase"])
        self.assertFalse(summary["raw_to_processed_value_comparison_performed_by_this_phase"])
        self.assertFalse(summary["full_raw_to_processed_reconciliation_complete"])
        self.assertFalse(summary["business_value_consistency_verified"])
        self.assertFalse(summary["lineage_full_check_complete"])
        self.assertFalse(summary["formal_report_allowed"])
        self.assertFalse(summary["github_upload_performed"])
        self.assertFalse(summary["app_reinstall_performed"])
        self.assertFalse(summary["business_execution_performed"])
        boundary = summary["raw_boundary"]
        self.assertFalse(boundary["raw_inbox_read_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_list_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_stat_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_write_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_mutated_by_this_phase"])

    def test_validator_accepts_private_intake(self) -> None:
        manifest = validate(require_private_intake=True)
        self.assertEqual(manifest["summary"]["decision_track_count"], 5)
        self.assertEqual(manifest["summary"]["keep_blocked_decision_count"], 5)


if __name__ == "__main__":
    unittest.main()
