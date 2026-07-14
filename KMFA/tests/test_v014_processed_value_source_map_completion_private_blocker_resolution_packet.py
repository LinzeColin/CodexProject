from __future__ import annotations

import unittest

from KMFA.tools import v014_processed_value_source_map_completion_private_blocker_resolution_packet as generator
from KMFA.tools.check_v014_processed_value_source_map_completion_private_blocker_resolution_packet import validate


class ProcessedValueSourceMapCompletionPrivateBlockerResolutionPacketTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = generator.generate(
            generated_at="2026-07-06T00:00:00+10:00",
            write_governance_event=False,
        )

    def test_resolution_packet_counts(self) -> None:
        summary = self.manifest["summary"]
        self.assertEqual(summary["decision"], "NO_GO")
        self.assertTrue(summary["blocker_resolution_packet_prepared"])
        self.assertEqual(summary["blocker_class_count"], 5)
        self.assertEqual(summary["resolution_track_count"], 5)
        self.assertEqual(summary["owner_or_agent_action_required_track_count"], 4)
        self.assertEqual(summary["auto_resolution_allowed_track_count"], 0)
        self.assertEqual(summary["private_blocker_record_count"], 113)
        self.assertEqual(summary["private_resolution_queue_count"], 113)
        self.assertEqual(
            summary["private_resolution_queue_status_counts"]["requires_corrected_source_or_owner_exclusion"],
            36,
        )
        self.assertEqual(summary["private_resolution_queue_status_counts"]["requires_private_disambiguation"], 77)

    def test_resolution_tracks_are_prepared_not_applied(self) -> None:
        tracks = self.manifest["resolution_tracks"]
        self.assertTrue(tracks["all_resolution_tracks_prepared"])
        self.assertFalse(tracks["any_resolution_applied_by_this_phase"])
        self.assertEqual(tracks["auto_resolution_allowed_track_count"], 0)
        self.assertEqual(tracks["owner_or_agent_action_required_track_count"], 4)
        for track in tracks["resolution_tracks"]:
            self.assertFalse(track["auto_resolution_allowed"])
            self.assertFalse(track["resolution_applied_by_this_phase"])
            self.assertFalse(track["delivery_claim_allowed_after_this_phase"])

    def test_gates_and_raw_boundary_remain_closed(self) -> None:
        summary = self.manifest["summary"]
        self.assertFalse(summary["resolution_applied_by_this_phase"])
        self.assertFalse(summary["raw_to_processed_value_comparison_performed_by_this_phase"])
        self.assertFalse(summary["full_raw_to_processed_reconciliation_complete"])
        self.assertFalse(summary["business_value_consistency_verified"])
        self.assertFalse(summary["lineage_full_check_complete"])
        self.assertFalse(summary["formal_report_allowed"])
        self.assertFalse(summary["github_upload_performed"])
        self.assertFalse(summary["app_reinstall_performed"])
        self.assertFalse(summary["business_execution_performed"])
        boundary = summary["raw_boundary"]
        self.assertFalse(boundary["raw_inbox_read_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_list_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_stat_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_write_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_mutated_by_this_phase"])

    def test_validator_accepts_private_packet(self) -> None:
        manifest = validate(require_private_packet=True)
        self.assertEqual(manifest["summary"]["resolution_track_count"], 5)
        self.assertEqual(manifest["summary"]["private_resolution_queue_count"], 113)


if __name__ == "__main__":
    unittest.main()
