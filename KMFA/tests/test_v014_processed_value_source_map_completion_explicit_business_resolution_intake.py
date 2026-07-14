from __future__ import annotations

import unittest

from KMFA.tools import v014_processed_value_source_map_completion_explicit_business_resolution_intake as generator
from KMFA.tools.check_v014_processed_value_source_map_completion_explicit_business_resolution_intake import (
    validate,
)


class ProcessedValueSourceMapCompletionExplicitBusinessResolutionIntakeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = generator.generate(
            generated_at="2026-07-06T00:00:00+10:00",
            write_governance_event=False,
        )

    def test_resolution_is_recorded_without_release(self) -> None:
        summary = self.manifest["summary"]
        self.assertEqual(summary["decision"], "NO_GO")
        self.assertTrue(summary["explicit_business_resolution_recorded"])
        self.assertTrue(summary["owner_delegated_default_decision_applied"])
        self.assertTrue(summary["previous_required_input_resolved_by_this_phase"])
        self.assertEqual(summary["business_resolution_item_count"], 1)
        self.assertEqual(summary["non_actionable_group_count"], 3)
        self.assertEqual(summary["non_actionable_target_slot_count"], 12)
        self.assertTrue(summary["residual_gap_report_recommended"])

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

    def test_validator_accepts_private_resolution(self) -> None:
        manifest = validate(require_private_resolution=True)
        self.assertTrue(manifest["summary"]["explicit_business_resolution_recorded"])
        self.assertTrue(manifest["summary"]["previous_required_input_resolved_by_this_phase"])
        self.assertFalse(manifest["summary"]["delivery_allowed"])


if __name__ == "__main__":
    unittest.main()
