from __future__ import annotations

import unittest

from KMFA.tools.check_v014_private_processed_value_source_resolution import (
    validate_v014_private_processed_value_source_resolution,
)
from KMFA.tools.v014_private_processed_value_source_resolution import generate


class V014PrivateProcessedValueSourceResolutionTest(unittest.TestCase):
    def test_missing_private_source_map_locks_resolution_gap_without_comparison(self) -> None:
        manifest = generate(generated_at="2026-07-05T23:59:59+10:00")
        validated = validate_v014_private_processed_value_source_resolution(
            require_private_source_resolution=True
        )

        self.assertEqual(validated["phase_id"], "V014_PRIVATE_PROCESSED_VALUE_SOURCE_RESOLUTION")
        self.assertEqual(validated["status"], manifest["status"])
        summary = validated["source_resolution_summary"]
        self.assertGreater(summary["processed_target_slot_count"], 0)
        self.assertEqual(
            summary["unmaterialized_processed_target_slot_count"],
            summary["processed_target_slot_count"],
        )
        self.assertEqual(summary["usable_private_processed_value_source_map_count"], 0)
        self.assertEqual(summary["resolved_processed_value_source_count"], 0)
        self.assertEqual(
            summary["unresolved_processed_value_source_count"],
            summary["processed_target_slot_count"],
        )
        self.assertTrue(summary["required_source_map_schema_locked"])
        self.assertFalse(summary["source_resolution_complete"])
        self.assertFalse(validated["value_matching_readiness"]["raw_to_processed_value_comparison_performed"])
        self.assertFalse(validated["value_matching_readiness"]["business_value_consistency_verified"])
        self.assertEqual(validated["go_no_go"]["decision"], "NO_GO")

    def test_raw_inbox_and_release_actions_remain_blocked(self) -> None:
        manifest = validate_v014_private_processed_value_source_resolution(
            require_private_source_resolution=True
        )
        raw_boundary = manifest["raw_readonly_boundary"]
        go_no_go = manifest["go_no_go"]

        for value in raw_boundary.values():
            self.assertFalse(value)
        self.assertFalse(go_no_go["lineage_full_check_complete"])
        self.assertFalse(go_no_go["formal_report_allowed"])
        self.assertFalse(go_no_go["github_upload_allowed"])
        self.assertFalse(go_no_go["app_reinstall_allowed"])
        self.assertFalse(go_no_go["business_execution_allowed"])


if __name__ == "__main__":
    unittest.main()
