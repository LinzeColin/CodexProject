from __future__ import annotations

import unittest

from KMFA.tools import v014_processed_value_source_map_completion_non_actionable_default_resolution_application as generator
from KMFA.tools.check_v014_processed_value_source_map_completion_non_actionable_default_resolution_application import (
    validate,
)


class ProcessedValueSourceMapCompletionNonActionableDefaultResolutionApplicationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = generator.generate(
            generated_at="2026-07-06T00:00:00+10:00",
            write_governance_event=False,
        )

    def test_non_actionable_defaults_are_applied_as_keep_no_go(self) -> None:
        summary = self.manifest["summary"]
        self.assertEqual(summary["decision"], "NO_GO")
        self.assertTrue(summary["non_actionable_default_resolution_application_performed"])
        self.assertEqual(summary["source_after_fill_valid_owner_confirmation_response_count"], 3)
        self.assertEqual(summary["source_after_fill_pending_owner_confirmation_response_count"], 0)
        self.assertEqual(summary["non_actionable_default_resolution_item_count"], 3)
        self.assertEqual(summary["keep_no_go_resolution_count"], 3)
        self.assertEqual(summary["non_actionable_group_count"], 3)
        self.assertEqual(summary["non_actionable_target_slot_count"], 12)
        self.assertEqual(summary["actionable_partial_application_group_count"], 19)
        self.assertEqual(summary["actionable_partial_application_target_slot_count"], 101)

    def test_default_resolution_does_not_open_full_application_or_business_use(self) -> None:
        summary = self.manifest["summary"]
        self.assertEqual(summary["non_actionable_active_authorization_allowed_count"], 0)
        self.assertEqual(summary["non_actionable_canonical_source_map_mutation_allowed_count"], 0)
        self.assertFalse(summary["full_source_map_completion_reapplication_ready"])
        self.assertFalse(summary["full_raw_to_processed_comparison_ready"])
        self.assertFalse(summary["canonical_source_map_mutated"])
        self.assertEqual(summary["canonical_source_map_records_applied_count"], 0)
        self.assertFalse(summary["processed_value_materialization_replay_performed"])
        self.assertFalse(summary["raw_to_processed_value_comparison_performed_by_this_phase"])
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

    def test_validator_accepts_private_default_resolution(self) -> None:
        manifest = validate(require_private_default_resolution=True)
        self.assertEqual(manifest["summary"]["keep_no_go_resolution_count"], 3)
        self.assertEqual(manifest["summary"]["non_actionable_target_slot_count"], 12)
        self.assertFalse(manifest["summary"]["full_source_map_completion_reapplication_ready"])


if __name__ == "__main__":
    unittest.main()
