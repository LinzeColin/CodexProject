from __future__ import annotations

import json
import unittest

from KMFA.tools import v014_raw_processed_comparability_diagnostic as generator
from KMFA.tools.check_v014_raw_processed_comparability_diagnostic import validate


class V014RawProcessedComparabilityDiagnosticTest(unittest.TestCase):
    def setUp(self) -> None:
        generator.generate(generated_at="2026-07-06T00:00:00+10:00")

    def test_summary_locks_no_go_comparability_counts(self) -> None:
        summary = json.loads(generator.SUMMARY_PATH.read_text(encoding="utf-8"))
        self.assertEqual(summary["status"], generator.STATUS)
        self.assertEqual(summary["raw_root_file_count"], 5)
        self.assertEqual(summary["prior_raw_value_fingerprint_record_count"], 871)
        self.assertEqual(summary["prior_raw_unique_numeric_fingerprint_count"], 330)
        self.assertEqual(summary["processed_target_slot_count"], 149)
        self.assertEqual(summary["existing_processed_source_map_record_count"], 36)
        self.assertEqual(summary["unresolved_owner_worklist_item_count"], 113)
        self.assertEqual(summary["active_fill_record_keep_pending_count"], 113)
        self.assertEqual(summary["raw_processed_structural_key_intersection_count"], 0)
        self.assertEqual(summary["comparable_value_pair_count"], 0)
        self.assertFalse(summary["business_value_consistency_verified"])
        self.assertFalse(summary["raw_inbox_mutation_detected"])

    def test_go_no_go_blocks_downstream_release(self) -> None:
        go_no_go = json.loads(generator.GO_NO_GO_PATH.read_text(encoding="utf-8"))
        self.assertEqual(go_no_go["decision"], "NO_GO")
        self.assertEqual(go_no_go["next_required_input"], generator.NEXT_REQUIRED_INPUT)
        self.assertFalse(go_no_go["raw_to_processed_value_comparison_performed"])
        self.assertFalse(go_no_go["github_upload_performed"])
        self.assertFalse(go_no_go["app_reinstall_performed"])
        self.assertFalse(go_no_go["business_execution_performed"])

    def test_validator_passes(self) -> None:
        validate()


if __name__ == "__main__":
    unittest.main()
