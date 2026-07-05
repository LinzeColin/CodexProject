from __future__ import annotations

import unittest

from KMFA.tools.check_v014_private_processed_value_materialization import (
    validate_v014_private_processed_value_materialization,
)
from KMFA.tools.v014_private_processed_value_materialization import generate


class V014PrivateProcessedValueMaterializationTest(unittest.TestCase):
    def test_missing_private_value_source_map_keeps_no_go_without_comparison(self) -> None:
        manifest = generate(generated_at="2026-07-05T23:59:59+10:00")
        validated = validate_v014_private_processed_value_materialization(
            require_private_materialization=True
        )

        self.assertEqual(validated["phase_id"], "V014_PRIVATE_PROCESSED_VALUE_MATERIALIZATION")
        self.assertEqual(validated["status"], manifest["status"])
        summary = validated["processed_materialization_summary"]
        self.assertGreater(summary["processed_target_slot_count"], 0)
        self.assertEqual(summary["private_processed_value_source_count"], 0)
        self.assertFalse(summary["private_processed_value_source_map_present"])
        self.assertEqual(summary["materialized_processed_value_fingerprint_count"], 0)
        self.assertEqual(
            summary["unmaterialized_processed_target_slot_count"],
            summary["processed_target_slot_count"],
        )
        self.assertFalse(summary["processed_value_materialization_complete"])
        self.assertFalse(validated["value_matching_readiness"]["raw_to_processed_value_comparison_performed"])
        self.assertEqual(validated["value_matching_readiness"]["comparable_value_pair_count"], 0)
        self.assertFalse(validated["value_matching_readiness"]["business_value_consistency_verified"])
        self.assertEqual(validated["go_no_go"]["decision"], "NO_GO")

    def test_raw_inbox_and_release_actions_remain_blocked(self) -> None:
        manifest = validate_v014_private_processed_value_materialization(
            require_private_materialization=True
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
