from __future__ import annotations

import unittest

from KMFA.tools import v014_processed_value_source_map_completion_owner_review_intake_prep as generator
from KMFA.tools.check_v014_processed_value_source_map_completion_owner_review_intake_prep import validate


class ProcessedValueSourceMapCompletionOwnerReviewIntakePrepTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = generator.generate(
            generated_at="2026-07-06T00:00:00+10:00",
            write_governance_event=False,
        )

    def test_review_intake_outputs_are_private_and_pending(self) -> None:
        summary = self.manifest["summary"]
        self.assertEqual(summary["decision"], "NO_GO")
        self.assertEqual(summary["source_candidate_draft_item_count"], 113)
        self.assertEqual(summary["review_group_count"], 22)
        self.assertEqual(summary["response_template_row_count"], 113)
        self.assertTrue(summary["private_grouped_review_written"])
        self.assertTrue(summary["private_response_template_written"])
        self.assertTrue(summary["private_candidate_catalog_written"])
        self.assertTrue(summary["private_grouped_question_list_written"])
        self.assertTrue(summary["private_response_template_gitignored"])
        self.assertFalse(summary["response_template_is_active_authorization_record"])
        self.assertFalse(summary["completion_template_overwritten"])
        self.assertFalse(summary["active_owner_authorized_fill_record_written"])

    def test_raw_boundary_and_downstream_gates_remain_closed(self) -> None:
        summary = self.manifest["summary"]
        boundary = summary["raw_boundary"]
        self.assertFalse(boundary["raw_inbox_read_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_mutated_by_this_phase"])
        self.assertFalse(summary["authorized_completion_record_supplied"])
        self.assertFalse(summary["source_map_completion_reapplication_ready"])
        self.assertFalse(summary["source_map_completion_reapplication_performed"])
        self.assertEqual(summary["source_map_records_applied_count"], 0)
        self.assertFalse(summary["raw_to_processed_value_comparison_performed"])
        self.assertFalse(summary["business_value_consistency_verified"])
        self.assertFalse(summary["github_upload_performed"])
        self.assertFalse(summary["app_reinstall_performed"])
        self.assertFalse(summary["business_execution_performed"])

    def test_validator_accepts_private_intake(self) -> None:
        manifest = validate(require_private_intake=True)
        self.assertEqual(manifest["summary"]["review_group_count"], 22)
        self.assertEqual(manifest["summary"]["response_template_row_count"], 113)


if __name__ == "__main__":
    unittest.main()
