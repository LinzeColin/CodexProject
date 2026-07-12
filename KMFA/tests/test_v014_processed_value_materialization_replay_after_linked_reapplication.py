from __future__ import annotations

import unittest

from KMFA.tools.check_v014_processed_value_materialization_replay_after_linked_reapplication import validate


class LinkedMaterializationReplayTest(unittest.TestCase):
    def setUp(self) -> None:
        self.result = validate(require_private_replay=False)

    def test_linked_scope_materializes_77_records(self) -> None:
        summary = self.result["summary"]
        self.assertEqual(summary["decision"], "NO_GO")
        self.assertEqual(summary["processed_target_slot_count"], 149)
        self.assertEqual(summary["linked_materialization_source_map_record_count"], 77)
        self.assertEqual(summary["linked_materialized_record_count"], 77)
        self.assertEqual(summary["linked_materialization_blocked_record_count"], 0)
        self.assertEqual(summary["linked_unique_private_value_source_count"], 12)
        self.assertEqual(summary["processed_target_slot_outside_linked_replay_scope_count"], 72)

    def test_replay_is_linked_scope_only(self) -> None:
        summary = self.result["summary"]
        self.assertTrue(summary["linked_scope_materialization_replay_performed_by_this_phase"])
        self.assertTrue(summary["linked_scope_materialization_replay_complete"])
        self.assertFalse(summary["full_processed_value_materialization_complete"])
        self.assertTrue(summary["linked_scope_raw_to_processed_value_comparison_ready"])
        self.assertFalse(summary["raw_to_processed_value_comparison_ready"])
        self.assertFalse(summary["raw_to_processed_value_comparison_performed_by_this_phase"])
        self.assertFalse(summary["full_reconciliation_allowed"])
        self.assertFalse(summary["business_value_consistency_verified"])

    def test_release_and_execution_gates_stay_closed(self) -> None:
        summary = self.result["summary"]
        self.assertFalse(summary["lineage_full_check_complete"])
        self.assertFalse(summary["formal_report_allowed"])
        self.assertFalse(summary["github_upload_performed"])
        self.assertFalse(summary["app_reinstall_performed"])
        self.assertFalse(summary["business_execution_performed"])

    def test_public_matrix_is_aggregate_only(self) -> None:
        matrix = self.result["matrix"]
        self.assertEqual(matrix["linked_materialization_check_count"], 6)
        self.assertEqual(matrix["linked_materialization_pass_count"], 6)
        self.assertEqual(matrix["linked_materialization_fail_count"], 0)
        self.assertEqual(matrix["processed_target_slot_count"], 149)
        self.assertEqual(matrix["linked_materialization_source_map_record_count"], 77)
        self.assertEqual(matrix["linked_materialized_record_count"], 77)
        self.assertEqual(matrix["processed_target_slot_outside_linked_replay_scope_count"], 72)

    def test_raw_inbox_is_not_accessed(self) -> None:
        boundary = self.result["summary"]["raw_boundary"]
        self.assertTrue(boundary["raw_data_root_readonly_policy_active"])
        self.assertTrue(boundary["private_linked_source_map_read_by_this_phase"])
        self.assertTrue(boundary["private_processed_target_staging_read_by_this_phase"])
        self.assertTrue(boundary["private_linked_materialization_replay_written_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_read_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_list_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_stat_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_parse_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_value_extraction_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_mutated_by_this_phase"])

    def test_validator_accepts_private_replay(self) -> None:
        manifest = validate(require_private_replay=False)
        summary = manifest["summary"]
        self.assertEqual(summary["linked_materialized_record_count"], 77)
        self.assertEqual(summary["processed_target_slot_outside_linked_replay_scope_count"], 72)
        self.assertFalse(summary["raw_to_processed_value_comparison_performed_by_this_phase"])


if __name__ == "__main__":
    unittest.main()
