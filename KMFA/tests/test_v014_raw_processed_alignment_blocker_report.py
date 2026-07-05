from __future__ import annotations

import json
import unittest

from KMFA.tools import v014_raw_processed_alignment_blocker_report as generator
from KMFA.tools.check_v014_raw_processed_alignment_blocker_report import validate


class V014RawProcessedAlignmentBlockerReportTest(unittest.TestCase):
    def setUp(self) -> None:
        generator.generate(generated_at="2026-07-06T00:00:00+10:00")

    def test_summary_explains_no_comparable_pairs(self) -> None:
        summary = json.loads(generator.SUMMARY_PATH.read_text(encoding="utf-8"))
        self.assertEqual(summary["decision"], "NO_GO")
        self.assertEqual(summary["raw_value_fingerprint_count"], 871)
        self.assertEqual(summary["raw_unique_numeric_fingerprint_count"], 330)
        self.assertEqual(summary["processed_target_slot_count"], 149)
        self.assertEqual(summary["staged_processed_value_fingerprint_count"], 0)
        self.assertEqual(summary["usable_processed_source_map_count"], 0)
        self.assertEqual(summary["authorized_filled_item_count"], 36)
        self.assertEqual(summary["authorized_unfilled_item_count"], 113)
        self.assertEqual(summary["unresolved_gap_item_count"], 113)
        self.assertEqual(summary["active_fill_record_keep_pending_count"], 113)
        self.assertEqual(summary["comparable_value_pair_count"], 0)
        self.assertFalse(summary["business_value_consistency_verified"])
        self.assertTrue(summary["interim_report_generated_for_external_agent_diagnosis"])

    def test_go_no_go_keeps_downstream_actions_blocked(self) -> None:
        go_no_go = json.loads(generator.GO_NO_GO_PATH.read_text(encoding="utf-8"))
        self.assertEqual(go_no_go["decision"], "NO_GO")
        self.assertIn("RAW_TO_PROCESSED_COMPARISON_BLOCKED", go_no_go["blocker_ids"])
        self.assertFalse(go_no_go["raw_to_processed_value_comparison_performed"])
        self.assertFalse(go_no_go["github_upload_performed"])
        self.assertFalse(go_no_go["app_reinstall_performed"])
        self.assertFalse(go_no_go["business_execution_performed"])

    def test_validator_passes(self) -> None:
        validate()


if __name__ == "__main__":
    unittest.main()
