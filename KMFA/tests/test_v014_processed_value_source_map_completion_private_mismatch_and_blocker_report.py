from __future__ import annotations

import unittest

from KMFA.tools import v014_processed_value_source_map_completion_private_mismatch_and_blocker_report as generator
from KMFA.tools.check_v014_processed_value_source_map_completion_private_mismatch_and_blocker_report import validate


class ProcessedValueSourceMapCompletionPrivateMismatchAndBlockerReportTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = generator.generate(
            generated_at="2026-07-06T00:00:00+10:00",
            write_governance_event=False,
        )

    def test_public_safe_blocker_counts(self) -> None:
        summary = self.manifest["summary"]
        self.assertEqual(summary["decision"], "NO_GO")
        self.assertEqual(summary["private_matching_record_count"], 137)
        self.assertEqual(summary["dry_run_matched_target_count"], 101)
        self.assertEqual(summary["dry_run_unmatched_target_count"], 36)
        self.assertEqual(summary["dry_run_unique_raw_match_target_count"], 24)
        self.assertEqual(summary["dry_run_ambiguous_raw_match_target_count"], 77)
        self.assertEqual(summary["dry_run_confirmed_fingerprint_mismatch_count"], 0)
        self.assertEqual(summary["processed_materialization_target_slot_count"], 149)
        self.assertEqual(summary["processed_materialization_value_fingerprint_count"], 0)
        self.assertEqual(summary["partial_blocked_target_slot_count"], 12)
        self.assertEqual(summary["raw_parse_error_count"], 6)
        self.assertEqual(summary["blocker_class_count"], 5)
        self.assertEqual(summary["confirmed_value_mismatch_count"], 0)

    def test_blocker_matrix_is_public_safe_aggregate(self) -> None:
        matrix = self.manifest["blocker_matrix"]
        self.assertEqual(matrix["blocker_class_count"], 5)
        affected = {blocker["blocker_code"]: blocker["affected_count"] for blocker in matrix["blockers"]}
        self.assertEqual(affected["processed_materialization_value_fingerprints_missing"], 149)
        self.assertEqual(affected["owner_authorized_fill_targets_unmatched_in_private_raw_index"], 36)
        self.assertEqual(affected["ambiguous_private_raw_index_matches"], 77)
        self.assertEqual(affected["residual_partial_application_blocked_targets"], 12)
        self.assertEqual(affected["private_raw_index_parse_errors_present"], 6)
        self.assertFalse(matrix["confirmed_mismatch_report_required_now"])
        self.assertFalse(matrix["business_value_consistency_verified"])

    def test_gates_and_raw_boundary_remain_closed(self) -> None:
        summary = self.manifest["summary"]
        self.assertTrue(summary["mismatch_and_blocker_report_performed"])
        self.assertFalse(summary["confirmed_mismatch_report_required_now"])
        self.assertFalse(summary["final_goal_closeout_difference_report_required_now"])
        self.assertTrue(summary["final_goal_closeout_difference_report_required_if_repeated"])
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

    def test_validator_accepts_private_report(self) -> None:
        manifest = validate(require_private_report=True)
        self.assertEqual(manifest["summary"]["blocker_class_count"], 5)
        self.assertEqual(manifest["summary"]["confirmed_value_mismatch_count"], 0)


if __name__ == "__main__":
    unittest.main()
