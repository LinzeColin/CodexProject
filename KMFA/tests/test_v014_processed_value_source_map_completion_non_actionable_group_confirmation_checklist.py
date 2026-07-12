from __future__ import annotations

import unittest

from KMFA.tools import v014_processed_value_source_map_completion_non_actionable_group_confirmation_checklist as generator
from KMFA.tools.check_v014_processed_value_source_map_completion_non_actionable_group_confirmation_checklist import validate


class ProcessedValueSourceMapCompletionNonActionableGroupConfirmationChecklistTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = generator.generate(
            generated_at="2026-07-06T00:00:00+10:00",
            write_governance_event=False,
        )

    def test_confirmation_checklist_counts(self) -> None:
        summary = self.manifest["summary"]
        self.assertEqual(summary["decision"], "NO_GO")
        self.assertEqual(summary["source_response_group_count"], 3)
        self.assertEqual(summary["source_response_target_slot_count"], 12)
        self.assertEqual(summary["source_ready_for_intake_group_count"], 0)
        self.assertEqual(summary["source_pending_response_group_count"], 3)
        self.assertEqual(summary["source_invalid_response_group_count"], 0)
        self.assertEqual(summary["checklist_item_count"], 3)
        self.assertEqual(summary["checklist_target_slot_count"], 12)
        self.assertEqual(summary["missing_required_key_counts"], {"additional_evidence_ref": 1, "owner_or_authorized_delegate": 3})
        self.assertEqual(
            summary["resolution_decision_code_counts"],
            {"KEEP_PENDING_WITH_REASON": 2, "REQUEST_ADDITIONAL_SOURCE_EVIDENCE": 1},
        )
        self.assertEqual(
            summary["candidate_status_group_counts"],
            {"auto_unmatched_requires_owner_review": 1, "requires_non_numeric_owner_mapping": 2},
        )
        self.assertTrue(summary["private_chinese_checklist_ready"])
        self.assertTrue(summary["owner_or_authorized_delegate_response_required"])

    def test_downstream_gates_remain_closed(self) -> None:
        summary = self.manifest["summary"]
        self.assertFalse(summary["codex_default_business_resolution_applied"])
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

    def test_validator_accepts_private_confirmation_checklist(self) -> None:
        manifest = validate(require_private_confirmation_checklist=True)
        self.assertEqual(manifest["summary"]["checklist_item_count"], 3)
        self.assertEqual(manifest["summary"]["checklist_target_slot_count"], 12)


if __name__ == "__main__":
    unittest.main()
