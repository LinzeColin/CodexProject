from __future__ import annotations

import unittest

from KMFA.tools import v014_processed_value_source_map_completion_non_actionable_group_resolution_packet as generator
from KMFA.tools.check_v014_processed_value_source_map_completion_non_actionable_group_resolution_packet import validate


class ProcessedValueSourceMapCompletionNonActionableGroupResolutionPacketTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = generator.generate(
            generated_at="2026-07-06T00:00:00+10:00",
            write_governance_event=False,
        )

    def test_non_actionable_resolution_counts(self) -> None:
        summary = self.manifest["summary"]
        self.assertEqual(summary["decision"], "NO_GO")
        self.assertEqual(summary["review_group_count"], 22)
        self.assertEqual(summary["response_row_count"], 113)
        self.assertEqual(summary["source_partial_comparable_pair_count"], 101)
        self.assertEqual(summary["source_partial_exact_match_count"], 101)
        self.assertEqual(summary["source_partial_mismatch_count"], 0)
        self.assertEqual(summary["source_partial_missing_candidate_count"], 0)
        self.assertEqual(summary["non_actionable_group_count"], 3)
        self.assertEqual(summary["non_actionable_target_slot_count"], 12)
        self.assertEqual(summary["decision_code_group_counts"], {"KEEP_PENDING": 2, "REQUEST_MORE_DIAGNOSTICS": 1})
        self.assertEqual(summary["decision_code_target_slot_counts"], {"KEEP_PENDING": 8, "REQUEST_MORE_DIAGNOSTICS": 4})
        self.assertEqual(
            summary["candidate_status_group_counts"],
            {"auto_unmatched_requires_owner_review": 1, "requires_non_numeric_owner_mapping": 2},
        )
        self.assertEqual(
            summary["candidate_status_target_slot_counts"],
            {"auto_unmatched_requires_owner_review": 4, "requires_non_numeric_owner_mapping": 8},
        )
        self.assertTrue(summary["non_actionable_resolution_packet_ready"])
        self.assertFalse(summary["codex_default_business_resolution_applied"])

    def test_downstream_gates_remain_closed(self) -> None:
        summary = self.manifest["summary"]
        self.assertTrue(summary["owner_or_authorized_delegate_resolution_required"])
        self.assertFalse(summary["active_owner_authorized_fill_record_ready"])
        self.assertFalse(summary["active_owner_authorized_fill_record_written"])
        self.assertFalse(summary["canonical_source_map_mutated"])
        self.assertEqual(summary["canonical_source_map_records_applied_count"], 0)
        self.assertFalse(summary["source_map_completion_reapplication_ready"])
        self.assertFalse(summary["source_map_completion_reapplication_performed"])
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

    def test_validator_accepts_private_resolution_packet(self) -> None:
        manifest = validate(require_private_resolution_packet=True)
        self.assertEqual(manifest["summary"]["non_actionable_group_count"], 3)
        self.assertEqual(manifest["summary"]["non_actionable_target_slot_count"], 12)
        self.assertFalse(manifest["summary"]["codex_default_business_resolution_applied"])


if __name__ == "__main__":
    unittest.main()
