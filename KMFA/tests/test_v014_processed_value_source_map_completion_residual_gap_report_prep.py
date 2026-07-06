from __future__ import annotations

import unittest

from KMFA.tools import v014_processed_value_source_map_completion_residual_gap_report_prep as generator
from KMFA.tools.check_v014_processed_value_source_map_completion_residual_gap_report_prep import (
    validate,
)


class ProcessedValueSourceMapCompletionResidualGapReportPrepTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = generator.generate(
            generated_at="2026-07-06T00:00:00+10:00",
            write_governance_event=False,
        )

    def test_gap_report_is_ready_without_release(self) -> None:
        summary = self.manifest["summary"]
        self.assertEqual(summary["decision"], "NO_GO")
        self.assertTrue(summary["residual_gap_report_ready"])
        self.assertTrue(summary["public_gap_matrix_ready"])
        self.assertTrue(summary["previous_required_input_resolved_by_this_phase"])
        self.assertEqual(summary["gap_category_count"], 4)
        self.assertEqual(summary["blocker_count"], 4)
        self.assertEqual(summary["non_actionable_group_count"], 3)
        self.assertEqual(summary["non_actionable_target_slot_count"], 12)
        self.assertTrue(summary["corrected_source_package_required_or_raw_scope_required"])

    def test_gap_matrix_blocks_delivery(self) -> None:
        matrix = self.manifest["public_gap_matrix"]
        self.assertEqual(matrix["gap_category_count"], 4)
        self.assertEqual(matrix["aggregate_blocker_count"], 4)
        codes = {item["gap_code"] for item in matrix["categories"]}
        self.assertEqual(
            codes,
            {
                "NON_ACTIONABLE_GROUPS",
                "FULL_RECONCILIATION_BLOCKED",
                "FORMAL_REPORT_BLOCKED",
                "UPLOAD_AND_APP_BLOCKED",
            },
        )
        self.assertTrue(all(item["blocks_delivery"] for item in matrix["categories"]))

    def test_delivery_and_execution_gates_remain_closed(self) -> None:
        summary = self.manifest["summary"]
        self.assertFalse(summary["delivery_allowed"])
        self.assertFalse(summary["formal_report_allowed"])
        self.assertFalse(summary["github_upload_allowed"])
        self.assertFalse(summary["github_upload_performed"])
        self.assertFalse(summary["app_reinstall_allowed"])
        self.assertFalse(summary["app_reinstall_performed"])
        self.assertFalse(summary["business_execution_allowed"])
        self.assertFalse(summary["business_execution_performed"])
        self.assertFalse(summary["full_source_map_completion_reapplication_ready"])
        self.assertFalse(summary["full_raw_to_processed_value_comparison_ready"])
        self.assertFalse(summary["business_value_consistency_verified"])
        self.assertFalse(summary["canonical_source_map_mutated"])
        self.assertEqual(summary["canonical_source_map_records_applied_count"], 0)

    def test_raw_boundary_is_closed_for_this_phase(self) -> None:
        boundary = self.manifest["summary"]["raw_boundary"]
        self.assertTrue(boundary["raw_data_root_readonly_policy_active"])
        self.assertFalse(boundary["raw_inbox_read_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_list_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_stat_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_hash_or_value_fingerprint_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_write_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_delete_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_move_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_rename_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_overwrite_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_copy_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_normalize_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_mutated_by_this_phase"])

    def test_validator_accepts_private_gap_report(self) -> None:
        manifest = validate(require_private_gap_report=True)
        self.assertTrue(manifest["summary"]["residual_gap_report_ready"])
        self.assertEqual(manifest["summary"]["gap_category_count"], 4)
        self.assertFalse(manifest["summary"]["delivery_allowed"])


if __name__ == "__main__":
    unittest.main()
