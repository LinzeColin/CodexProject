import unittest

from KMFA.tools.check_s11_stage_review import (
    DEFAULT_REVIEW_MANIFEST,
    validate_stage_review,
)


class S11StageReviewTests(unittest.TestCase):
    def test_stage11_review_manifest_matches_phase_evidence(self) -> None:
        counts = validate_stage_review(DEFAULT_REVIEW_MANIFEST)

        self.assertEqual(counts["home_navigation_module_count"], 8)
        self.assertEqual(counts["source_check_board_row_count"], 13)
        self.assertEqual(counts["project_cost_page_project_count"], 4)
        self.assertEqual(counts["html_export_count"], 3)
        self.assertEqual(counts["pending_reconciliation_count"], 12)
        self.assertEqual(counts["full_kmfa_unit_tests"], 132)


if __name__ == "__main__":
    unittest.main()
