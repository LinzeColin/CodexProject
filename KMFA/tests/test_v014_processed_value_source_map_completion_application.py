from __future__ import annotations

import unittest

from KMFA.tools import v014_processed_value_source_map_completion_application as generator
from KMFA.tools.check_v014_processed_value_source_map_completion_application import validate


class ProcessedValueSourceMapCompletionApplicationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.manifest = generator.generate(generated_at="2026-07-06T00:00:00+10:00")

    def test_summary_counts(self) -> None:
        summary = self.manifest["summary"]
        self.assertEqual(summary["decision"], "NO_GO")
        self.assertEqual(summary["completion_template_item_count"], 113)
        self.assertEqual(summary["pending_selected_action_count"], 113)
        self.assertEqual(summary["valid_completion_item_count"], 0)
        self.assertEqual(summary["source_map_records_applied_count"], 0)
        self.assertEqual(summary["comparable_value_pair_count"], 0)

    def test_downstream_gates_remain_closed(self) -> None:
        summary = self.manifest["summary"]
        self.assertFalse(summary["source_map_completion_application_ready"])
        self.assertTrue(summary["source_map_completion_application_performed"])
        self.assertFalse(summary["processed_value_materialization_replay_performed"])
        self.assertFalse(summary["raw_to_processed_value_comparison_performed"])
        self.assertFalse(summary["processed_data_reconciliation_performed"])
        self.assertFalse(summary["business_value_consistency_verified"])
        self.assertFalse(summary["github_upload_performed"])
        self.assertFalse(summary["app_reinstall_performed"])
        self.assertFalse(summary["business_execution_performed"])

    def test_validator_accepts_private_diagnostic(self) -> None:
        manifest = validate(require_private_diagnostic=True)
        self.assertEqual(manifest["summary"]["valid_completion_item_count"], 0)


if __name__ == "__main__":
    unittest.main()
