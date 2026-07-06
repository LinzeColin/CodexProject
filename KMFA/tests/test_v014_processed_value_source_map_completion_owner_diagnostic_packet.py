from __future__ import annotations

import unittest

from KMFA.tools import v014_processed_value_source_map_completion_owner_diagnostic_packet as generator
from KMFA.tools.check_v014_processed_value_source_map_completion_owner_diagnostic_packet import (
    validate,
)


class ProcessedValueSourceMapCompletionOwnerDiagnosticPacketTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = generator.generate(
            generated_at="2026-07-06T00:00:00+10:00",
            write_governance_event=False,
        )

    def test_owner_diagnostic_packet_is_ready(self) -> None:
        summary = self.manifest["summary"]
        self.assertEqual(summary["decision"], "NO_GO")
        self.assertTrue(summary["owner_diagnostic_packet_ready"])
        self.assertEqual(summary["owner_decision_item_count"], 1)
        self.assertTrue(summary["final_no_go_governance_lock_active"])
        self.assertTrue(summary["partial_evidence_chain_ready"])
        self.assertEqual(summary["blocker_count"], 4)
        self.assertEqual(summary["non_actionable_group_count"], 3)
        self.assertEqual(summary["non_actionable_target_slot_count"], 12)

    def test_delivery_and_execution_gates_remain_closed(self) -> None:
        summary = self.manifest["summary"]
        self.assertFalse(summary["delivery_allowed"])
        self.assertFalse(summary["formal_report_allowed"])
        self.assertFalse(summary["github_upload_allowed"])
        self.assertFalse(summary["github_upload_performed"])
        self.assertFalse(summary["app_reinstall_allowed"])
        self.assertFalse(summary["app_reinstall_performed"])
        self.assertFalse(summary["business_execution_allowed"])
        self.assertFalse(summary["business_execution_performed"])
        self.assertFalse(summary["full_source_map_completion_reapplication_ready"])
        self.assertFalse(summary["full_raw_to_processed_value_comparison_ready"])
        self.assertFalse(summary["business_value_consistency_verified"])
        self.assertFalse(summary["canonical_source_map_mutated"])
        self.assertEqual(summary["canonical_source_map_records_applied_count"], 0)

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

    def test_validator_accepts_private_packet(self) -> None:
        manifest = validate(require_private_packet=True)
        self.assertTrue(manifest["summary"]["owner_diagnostic_packet_ready"])
        self.assertEqual(manifest["summary"]["owner_decision_item_count"], 1)
        self.assertFalse(manifest["summary"]["delivery_allowed"])


if __name__ == "__main__":
    unittest.main()
