import unittest

from KMFA.tools.check_s10_stage_review import (
    DEFAULT_REVIEW_MANIFEST,
    validate_stage_review,
)


class S10StageReviewTests(unittest.TestCase):
    def test_stage10_review_manifest_matches_phase_evidence(self) -> None:
        counts = validate_stage_review(DEFAULT_REVIEW_MANIFEST)

        self.assertEqual(counts["report_template_count"], 2)
        self.assertEqual(counts["report_template_section_count"], 11)
        self.assertEqual(counts["report_grade_record_count"], 2)
        self.assertEqual(counts["report_export_record_count"], 2)
        self.assertEqual(counts["html_export_count"], 2)
        self.assertEqual(counts["csv_appendix_count"], 2)
        self.assertEqual(counts["full_kmfa_unit_tests"], 116)


if __name__ == "__main__":
    unittest.main()
