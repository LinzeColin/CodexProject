from __future__ import annotations

import unittest

from KMFA.tools import v014_processed_value_source_map_completion_owner_response_readiness_recheck as generator
from KMFA.tools.check_v014_processed_value_source_map_completion_owner_response_readiness_recheck import validate


class ProcessedValueSourceMapCompletionOwnerResponseReadinessRecheckTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = generator.generate(
            generated_at="2026-07-06T00:00:00+10:00",
            write_governance_event=False,
        )

    def test_response_template_is_still_pending(self) -> None:
        summary = self.manifest["summary"]
        self.assertEqual(summary["decision"], "NO_GO")
        self.assertEqual(summary["response_row_count"], 113)
        self.assertEqual(summary["pending_owner_decision_count"], 113)
        self.assertEqual(summary["valid_owner_decision_count"], 0)
        self.assertEqual(summary["invalid_owner_decision_count"], 0)
        self.assertFalse(summary["active_owner_authorized_fill_record_ready"])
        self.assertTrue(summary["response_template_gitignored"])
        self.assertTrue(summary["private_diagnostic_gitignored"])

    def test_no_downstream_or_raw_operations(self) -> None:
        summary = self.manifest["summary"]
        boundary = summary["raw_boundary"]
        self.assertFalse(boundary["raw_inbox_read_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_mutated_by_this_phase"])
        self.assertFalse(summary["active_owner_authorized_fill_record_written"])
        self.assertFalse(summary["completion_template_overwritten"])
        self.assertFalse(summary["authorized_completion_record_supplied"])
        self.assertFalse(summary["source_map_completion_reapplication_ready"])
        self.assertFalse(summary["source_map_completion_reapplication_performed"])
        self.assertEqual(summary["source_map_records_applied_count"], 0)
        self.assertFalse(summary["raw_to_processed_value_comparison_performed"])
        self.assertFalse(summary["business_value_consistency_verified"])
        self.assertFalse(summary["github_upload_performed"])
        self.assertFalse(summary["app_reinstall_performed"])
        self.assertFalse(summary["business_execution_performed"])

    def test_validator_accepts_private_diagnostic(self) -> None:
        manifest = validate(require_private_diagnostic=True)
        self.assertEqual(manifest["summary"]["pending_owner_decision_count"], 113)
        self.assertEqual(manifest["go_no_go"]["decision"], "NO_GO")


if __name__ == "__main__":
    unittest.main()
