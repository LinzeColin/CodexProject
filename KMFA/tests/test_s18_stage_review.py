import unittest

from KMFA.tools.check_s18_stage_review import (
    DEFAULT_REVIEW_MANIFEST,
    validate_stage_review,
)


class S18StageReviewTests(unittest.TestCase):
    def test_stage18_review_manifest_closes_all_phases_without_delivery_or_upload(self) -> None:
        counts = validate_stage_review(DEFAULT_REVIEW_MANIFEST)

        self.assertEqual(counts["precision_scenario_count"], 5)
        self.assertEqual(counts["precision_import_run_count"], 3)
        self.assertEqual(counts["large_batch_file_count"], 1200)
        self.assertEqual(counts["full_regression_check_count"], 5)
        self.assertEqual(counts["stage_acceptance_evidence_count"], 18)
        self.assertEqual(counts["read_only_connector_plan_count"], 3)
        self.assertEqual(counts["opme_entry_surface_count"], 4)
        self.assertEqual(counts["next_stage_backlog_count"], 6)
        self.assertEqual(counts["stage18_go_no_go_blocker_count"], 4)
        self.assertEqual(counts["s18_p3_pending_current_count"], 0)
        self.assertEqual(counts["delivery_allowed_count"], 0)
        self.assertEqual(counts["official_report_count"], 0)
        self.assertEqual(counts["live_connector_count"], 0)
        self.assertEqual(counts["github_upload_count"], 0)
        self.assertEqual(counts["business_execution_count"], 0)
        self.assertEqual(counts["full_kmfa_unit_tests"], 268)


if __name__ == "__main__":
    unittest.main()
