from __future__ import annotations

import unittest

from KMFA.tools import v014_processed_value_source_map_completion_owner_group_decision_input_kit as generator
from KMFA.tools.check_v014_processed_value_source_map_completion_owner_group_decision_input_kit import validate


class ProcessedValueSourceMapCompletionOwnerGroupDecisionInputKitTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = generator.generate(
            generated_at="2026-07-06T00:00:00+10:00",
            write_governance_event=False,
        )

    def test_private_input_kit_aggregate_counts(self) -> None:
        summary = self.manifest["summary"]
        self.assertEqual(summary["decision"], "NO_GO")
        self.assertEqual(summary["source_decision"], "NO_GO")
        self.assertEqual(summary["review_group_count"], 22)
        self.assertEqual(summary["response_row_count"], 113)
        self.assertEqual(summary["pending_group_template_count"], 22)
        self.assertEqual(summary["allowed_owner_group_decision_code_count"], 5)
        self.assertEqual(summary["candidate_status_group_counts"]["auto_ambiguous_multiple_candidates_requires_owner_review"], 19)
        self.assertEqual(summary["candidate_status_group_counts"]["requires_non_numeric_owner_mapping"], 2)
        self.assertEqual(summary["candidate_status_group_counts"]["auto_unmatched_requires_owner_review"], 1)
        self.assertEqual(summary["candidate_status_response_row_counts"]["auto_ambiguous_multiple_candidates_requires_owner_review"], 101)
        self.assertEqual(summary["candidate_status_response_row_counts"]["requires_non_numeric_owner_mapping"], 8)
        self.assertEqual(summary["candidate_status_response_row_counts"]["auto_unmatched_requires_owner_review"], 4)

    def test_downstream_gates_remain_closed(self) -> None:
        summary = self.manifest["summary"]
        self.assertFalse(summary["owner_group_decisions_supplied"])
        self.assertFalse(summary["owner_group_decision_applied"])
        self.assertFalse(summary["active_owner_authorized_fill_record_ready"])
        self.assertFalse(summary["active_owner_authorized_fill_record_written"])
        self.assertFalse(summary["owner_response_template_modified"])
        self.assertFalse(summary["completion_template_overwritten"])
        self.assertFalse(summary["authorized_completion_record_supplied"])
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

    def test_validator_accepts_private_kit(self) -> None:
        manifest = validate(require_private_kit=True)
        self.assertEqual(manifest["summary"]["pending_group_template_count"], 22)
        self.assertFalse(manifest["summary"]["owner_group_decisions_supplied"])


if __name__ == "__main__":
    unittest.main()
