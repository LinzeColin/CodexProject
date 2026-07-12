from __future__ import annotations

import unittest

from KMFA.tools.check_v014_processed_value_source_map_completion_private_raw_value_matching_dry_run import validate


class ProcessedValueSourceMapCompletionPrivateRawValueMatchingDryRunTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = validate(require_private_dry_run=False)

    def test_public_safe_aggregate_counts(self) -> None:
        summary = self.manifest["summary"]
        self.assertEqual(summary["decision"], "NO_GO")
        self.assertEqual(summary["raw_numeric_fingerprint_record_count"], 351453)
        self.assertEqual(summary["raw_unique_numeric_fingerprint_count"], 22453)
        self.assertEqual(summary["processed_materialization_target_slot_count"], 149)
        self.assertEqual(summary["processed_materialization_value_fingerprint_count"], 0)
        self.assertEqual(summary["owner_authorized_fill_value_fingerprint_count"], 36)
        self.assertEqual(summary["partial_exact_replay_target_count"], 101)
        self.assertEqual(summary["partial_blocked_target_slot_count"], 12)
        self.assertEqual(summary["dry_run_processed_fingerprint_target_count"], 137)
        self.assertEqual(summary["dry_run_unique_processed_fingerprint_count"], 50)
        self.assertEqual(summary["dry_run_matched_target_count"], 101)
        self.assertEqual(summary["dry_run_unmatched_target_count"], 36)
        self.assertEqual(summary["dry_run_unique_raw_match_target_count"], 24)
        self.assertEqual(summary["dry_run_ambiguous_raw_match_target_count"], 77)
        self.assertEqual(summary["dry_run_confirmed_fingerprint_mismatch_count"], 0)

    def test_gates_remain_closed(self) -> None:
        summary = self.manifest["summary"]
        self.assertTrue(summary["raw_value_matching_dry_run_performed"])
        self.assertFalse(summary["repeated_cross_validation_mismatch_confirmed"])
        self.assertFalse(summary["full_raw_to_processed_value_comparison_performed_by_this_phase"])
        self.assertFalse(summary["business_value_consistency_verified"])
        self.assertFalse(summary["canonical_source_map_mutated"])
        self.assertEqual(summary["canonical_source_map_records_applied_count"], 0)
        self.assertFalse(summary["full_raw_to_processed_reconciliation_complete"])
        self.assertFalse(summary["lineage_full_check_complete"])
        self.assertFalse(summary["formal_report_allowed"])
        self.assertFalse(summary["github_upload_performed"])
        self.assertFalse(summary["app_reinstall_performed"])
        self.assertFalse(summary["business_execution_performed"])

    def test_raw_inbox_is_not_touched_by_this_phase(self) -> None:
        boundary = self.manifest["summary"]["raw_boundary"]
        self.assertTrue(boundary["raw_data_root_readonly_policy_active"])
        self.assertTrue(boundary["private_raw_source_index_read_performed_by_this_phase"])
        self.assertTrue(boundary["private_processed_artifact_read_performed_by_this_phase"])
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

    def test_validator_accepts_private_dry_run(self) -> None:
        manifest = validate(require_private_dry_run=False)
        self.assertEqual(manifest["summary"]["dry_run_processed_fingerprint_target_count"], 137)
        self.assertEqual(manifest["summary"]["dry_run_matched_target_count"], 101)
        self.assertEqual(manifest["summary"]["dry_run_unmatched_target_count"], 36)


if __name__ == "__main__":
    unittest.main()
