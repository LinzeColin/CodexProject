from __future__ import annotations

import unittest

from KMFA.tools import v014_processed_value_source_map_completion_owner_group_actionable_application_plan as generator
from KMFA.tools.check_v014_processed_value_source_map_completion_owner_group_actionable_application_plan import validate


class ProcessedValueSourceMapCompletionOwnerGroupActionableApplicationPlanTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = generator.generate(
            generated_at="2026-07-06T00:00:00+10:00",
            write_governance_event=False,
        )

    def test_actionable_and_non_actionable_counts(self) -> None:
        summary = self.manifest["summary"]
        self.assertEqual(summary["decision"], "NO_GO")
        self.assertEqual(summary["review_group_count"], 22)
        self.assertEqual(summary["response_row_count"], 113)
        self.assertEqual(
            summary["decision_code_counts"],
            {
                "CONFIRM_GROUP_CANDIDATE_RANK": 19,
                "KEEP_PENDING": 2,
                "REQUEST_MORE_DIAGNOSTICS": 1,
            },
        )
        self.assertEqual(
            summary["decision_code_target_slot_counts"],
            {
                "CONFIRM_GROUP_CANDIDATE_RANK": 101,
                "KEEP_PENDING": 8,
                "REQUEST_MORE_DIAGNOSTICS": 4,
            },
        )
        self.assertEqual(summary["actionable_group_count"], 19)
        self.assertEqual(summary["actionable_target_slot_count"], 101)
        self.assertEqual(summary["non_actionable_group_count"], 3)
        self.assertEqual(summary["non_actionable_target_slot_count"], 12)
        self.assertTrue(summary["partial_actionable_application_plan_ready"])

    def test_downstream_gates_remain_closed(self) -> None:
        summary = self.manifest["summary"]
        self.assertFalse(summary["active_owner_authorized_fill_record_ready"])
        self.assertFalse(summary["active_owner_authorized_fill_record_written"])
        self.assertFalse(summary["source_map_completion_reapplication_ready"])
        self.assertFalse(summary["source_map_completion_reapplication_performed"])
        self.assertEqual(summary["source_map_records_applied_count"], 0)
        self.assertFalse(summary["processed_value_materialization_replay_performed"])
        self.assertFalse(summary["raw_to_processed_value_comparison_performed"])
        self.assertFalse(summary["business_value_consistency_verified"])
        self.assertFalse(summary["lineage_full_check_complete"])
        self.assertFalse(summary["formal_report_allowed"])
        self.assertFalse(summary["github_upload_performed"])
        self.assertFalse(summary["app_reinstall_performed"])
        self.assertFalse(summary["business_execution_performed"])

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

    def test_validator_accepts_private_plan(self) -> None:
        manifest = validate(require_private_plan=True)
        self.assertEqual(manifest["summary"]["actionable_group_count"], 19)
        self.assertEqual(manifest["summary"]["non_actionable_group_count"], 3)


if __name__ == "__main__":
    unittest.main()
