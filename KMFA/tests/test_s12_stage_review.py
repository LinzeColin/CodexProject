import unittest

from KMFA.tools.check_s12_stage_review import (
    DEFAULT_REVIEW_MANIFEST,
    validate_stage_review,
)


class S12StageReviewTests(unittest.TestCase):
    def test_stage12_review_manifest_matches_phase_evidence(self) -> None:
        counts = validate_stage_review(DEFAULT_REVIEW_MANIFEST)

        self.assertEqual(counts["manual_resolution_event_count"], 5)
        self.assertEqual(counts["manual_impact_preview_count"], 5)
        self.assertEqual(counts["eligible_rerun_event_count"], 2)
        self.assertEqual(counts["blocked_preview_count"], 3)
        self.assertEqual(counts["cache_invalidation_count"], 2)
        self.assertEqual(counts["rerun_step_count"], 8)
        self.assertEqual(counts["same_source_consistency_check_count"], 2)
        self.assertEqual(counts["html_export_count"], 3)
        self.assertEqual(counts["full_kmfa_unit_tests"], 152)


if __name__ == "__main__":
    unittest.main()
