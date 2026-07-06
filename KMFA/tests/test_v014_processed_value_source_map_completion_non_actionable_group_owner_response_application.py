from __future__ import annotations

import unittest

from KMFA.tools import v014_processed_value_source_map_completion_non_actionable_group_owner_response_application as generator
from KMFA.tools.check_v014_processed_value_source_map_completion_non_actionable_group_owner_response_application import validate


class ProcessedValueSourceMapCompletionNonActionableGroupOwnerResponseApplicationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = generator.generate(
            generated_at="2026-07-06T00:00:00+10:00",
            write_governance_event=False,
        )

    def test_owner_response_application_counts(self) -> None:
        summary = self.manifest["summary"]
        self.assertEqual(summary["decision"], "NO_GO")
        self.assertEqual(summary["source_checklist_item_count"], 3)
        self.assertEqual(summary["source_checklist_target_slot_count"], 12)
        self.assertEqual(summary["checklist_item_count"], 3)
        self.assertEqual(summary["checklist_target_slot_count"], 12)
        self.assertEqual(summary["filled_choice_count"], 0)
        self.assertEqual(summary["filled_owner_or_authorized_delegate_count"], 0)
        self.assertEqual(summary["ready_for_intake_flag_count"], 0)
        self.assertTrue(summary["owner_response_application_attempted"])
        self.assertEqual(summary["owner_response_applied_item_count"], 0)
        self.assertEqual(summary["owner_response_applied_target_slot_count"], 0)
        self.assertEqual(summary["pending_owner_response_item_count"], 3)
        self.assertEqual(summary["pending_owner_response_target_slot_count"], 12)
        self.assertEqual(summary["invalid_owner_response_item_count"], 0)
        self.assertEqual(summary["invalid_owner_response_target_slot_count"], 0)
        self.assertEqual(
            summary["missing_required_field_counts"],
            {
                "owner_or_authorized_delegate": 3,
                "ready_for_intake": 3,
                "resolution_reason_code": 3,
                "选择": 3,
            },
        )
        self.assertFalse(summary["owner_or_authorized_delegate_response_supplied"])

    def test_downstream_gates_remain_closed(self) -> None:
        summary = self.manifest["summary"]
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

    def test_validator_accepts_private_owner_response_application(self) -> None:
        manifest = validate(require_private_owner_response_application=True)
        self.assertEqual(manifest["summary"]["owner_response_applied_item_count"], 0)
        self.assertEqual(manifest["summary"]["pending_owner_response_item_count"], 3)


if __name__ == "__main__":
    unittest.main()
