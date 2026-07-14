from __future__ import annotations

import unittest

from KMFA.tools import v014_processed_value_source_map_completion_auto_candidate_draft as generator
from KMFA.tools.check_v014_processed_value_source_map_completion_auto_candidate_draft import validate


class ProcessedValueSourceMapCompletionAutoCandidateDraftTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = generator.generate(
            generated_at="2026-07-06T00:00:00+10:00",
            write_governance_event=False,
        )

    def test_candidate_draft_is_private_and_owner_review_required(self) -> None:
        summary = self.manifest["summary"]
        self.assertEqual(summary["decision"], "NO_GO")
        self.assertEqual(summary["candidate_draft_item_count"], 113)
        self.assertEqual(summary["owner_review_required_item_count"], 113)
        self.assertTrue(summary["private_raw_index_written"])
        self.assertTrue(summary["private_candidate_draft_written"])
        self.assertTrue(summary["private_match_diagnostic_written"])
        self.assertTrue(summary["private_question_list_written"])
        self.assertTrue(summary["private_candidate_draft_gitignored"])
        self.assertFalse(summary["completion_template_overwritten"])
        self.assertFalse(summary["active_owner_authorized_fill_record_written"])

    def test_raw_boundary_and_downstream_gates(self) -> None:
        summary = self.manifest["summary"]
        raw_summary = summary["raw_private_extraction_summary"]
        self.assertGreater(raw_summary["raw_root_file_count"], 0)
        self.assertGreater(raw_summary["raw_numeric_candidate_count"], 0)
        self.assertTrue(raw_summary["raw_value_fingerprints_generated"])
        self.assertTrue(raw_summary["raw_root_stat_unchanged_after_auto_candidate_draft"])
        boundary = summary["raw_boundary"]
        self.assertTrue(boundary["user_authorized_raw_data_read_for_this_phase"])
        self.assertTrue(boundary["raw_inbox_read_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_mutated_by_this_phase"])
        self.assertFalse(summary["source_map_completion_reapplication_ready"])
        self.assertFalse(summary["source_map_completion_reapplication_performed"])
        self.assertFalse(summary["raw_to_processed_value_comparison_performed"])
        self.assertFalse(summary["business_value_consistency_verified"])
        self.assertFalse(summary["github_upload_performed"])
        self.assertFalse(summary["app_reinstall_performed"])
        self.assertFalse(summary["business_execution_performed"])

    def test_validator_accepts_private_draft(self) -> None:
        manifest = validate(require_private_draft=True)
        self.assertEqual(manifest["summary"]["candidate_draft_item_count"], 113)
        self.assertEqual(manifest["go_no_go"]["decision"], "NO_GO")


if __name__ == "__main__":
    unittest.main()
