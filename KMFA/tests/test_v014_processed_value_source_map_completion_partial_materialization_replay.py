from __future__ import annotations

import unittest

from KMFA.tools import v014_processed_value_source_map_completion_partial_materialization_replay as generator
from KMFA.tools.check_v014_processed_value_source_map_completion_partial_materialization_replay import validate


class ProcessedValueSourceMapCompletionPartialMaterializationReplayTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = generator.generate(
            generated_at="2026-07-06T00:00:00+10:00",
            write_governance_event=False,
        )

    def test_replay_counts(self) -> None:
        summary = self.manifest["summary"]
        self.assertEqual(summary["decision"], "NO_GO")
        self.assertTrue(summary["source_recheck_replay_ready"])
        self.assertEqual(summary["source_recheck_materializable_target_slot_count"], 101)
        self.assertTrue(summary["partial_materialization_replay_performed"])
        self.assertTrue(summary["partial_materialization_replay_complete"])
        self.assertEqual(summary["partial_materialized_target_slot_count"], 101)
        self.assertEqual(summary["partial_unmaterialized_target_slot_count"], 0)
        self.assertEqual(summary["partial_materialized_unique_value_source_count"], 14)
        self.assertEqual(summary["partial_application_blocked_target_slot_count"], 12)
        self.assertEqual(summary["rejected_materialization_row_count"], 0)
        self.assertTrue(summary["partial_raw_to_processed_value_comparison_ready"])

    def test_downstream_gates_remain_closed(self) -> None:
        summary = self.manifest["summary"]
        self.assertTrue(summary["processed_value_materialization_replay_performed"])
        self.assertFalse(summary["raw_to_processed_value_comparison_ready"])
        self.assertFalse(summary["raw_to_processed_value_comparison_performed"])
        self.assertFalse(summary["canonical_source_map_mutated"])
        self.assertEqual(summary["canonical_source_map_records_applied_count"], 0)
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

    def test_validator_accepts_private_replay(self) -> None:
        manifest = validate(require_private_replay=True)
        self.assertEqual(manifest["summary"]["partial_materialized_target_slot_count"], 101)
        self.assertEqual(manifest["summary"]["partial_unmaterialized_target_slot_count"], 0)
        self.assertTrue(manifest["summary"]["partial_raw_to_processed_value_comparison_ready"])


if __name__ == "__main__":
    unittest.main()
