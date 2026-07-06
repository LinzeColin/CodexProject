from __future__ import annotations

import unittest

from KMFA.tools import v014_processed_value_source_map_completion_owner_confirmation_response_packet as generator
from KMFA.tools.check_v014_processed_value_source_map_completion_owner_confirmation_response_packet import validate


class ProcessedValueSourceMapCompletionOwnerConfirmationResponsePacketTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = generator.generate(
            generated_at="2026-07-06T00:00:00+10:00",
            write_governance_event=False,
        )

    def test_owner_confirmation_response_packet_counts(self) -> None:
        summary = self.manifest["summary"]
        self.assertEqual(summary["decision"], "NO_GO")
        self.assertEqual(summary["source_pending_owner_response_item_count"], 3)
        self.assertEqual(summary["source_pending_owner_response_target_slot_count"], 12)
        self.assertEqual(summary["source_owner_response_applied_item_count"], 0)
        self.assertEqual(summary["response_packet_item_count"], 3)
        self.assertEqual(summary["response_packet_target_slot_count"], 12)
        self.assertEqual(summary["response_draft_item_count"], 3)
        self.assertEqual(
            summary["missing_required_field_counts"],
            {
                "owner_or_authorized_delegate": 3,
                "ready_for_intake": 3,
                "resolution_reason_code": 3,
                "选择": 3,
            },
        )
        self.assertEqual(
            summary["recommendation_counts"],
            {
                "保持待定并补充授权人及原因": 2,
                "补充来源证据引用或确认无来源": 1,
            },
        )
        self.assertTrue(summary["owner_confirmation_response_packet_ready"])
        self.assertFalse(summary["owner_confirmation_response_supplied"])

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

    def test_validator_accepts_private_owner_confirmation_packet(self) -> None:
        manifest = validate(require_private_owner_confirmation_packet=True)
        self.assertEqual(manifest["summary"]["response_packet_item_count"], 3)
        self.assertEqual(manifest["summary"]["response_packet_target_slot_count"], 12)


if __name__ == "__main__":
    unittest.main()
