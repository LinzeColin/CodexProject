import unittest

from KMFA.tools.check_s13_stage_review import (
    DEFAULT_REVIEW_MANIFEST,
    validate_stage_review,
)


class S13StageReviewTests(unittest.TestCase):
    def test_stage13_review_manifest_matches_phase_evidence(self) -> None:
        counts = validate_stage_review(DEFAULT_REVIEW_MANIFEST)

        self.assertEqual(counts["financial_operating_source_lane_count"], 4)
        self.assertEqual(counts["financial_operating_draft_count"], 2)
        self.assertEqual(counts["collection_receivable_source_lane_count"], 5)
        self.assertEqual(counts["collection_receivable_priority_item_count"], 4)
        self.assertEqual(counts["cross_table_review_dimension_count"], 4)
        self.assertEqual(counts["cross_table_difference_queue_count"], 4)
        self.assertEqual(counts["operating_quality_report_count"], 1)
        self.assertEqual(counts["pending_reconciliation_count"], 12)
        self.assertEqual(counts["html_export_count"], 4)
        self.assertEqual(counts["full_kmfa_unit_tests"], 172)


if __name__ == "__main__":
    unittest.main()
