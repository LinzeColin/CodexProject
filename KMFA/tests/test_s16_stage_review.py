import unittest

from KMFA.tools.check_s16_stage_review import (
    DEFAULT_REVIEW_MANIFEST,
    validate_stage_review,
)


class S16StageReviewTests(unittest.TestCase):
    def test_stage16_review_manifest_matches_phase_evidence(self) -> None:
        counts = validate_stage_review(DEFAULT_REVIEW_MANIFEST)

        self.assertEqual(counts["subcontract_source_lane_count"], 4)
        self.assertEqual(counts["subcontract_project_match_count"], 5)
        self.assertEqual(counts["unallocated_cost_pool_count"], 2)
        self.assertEqual(counts["subcontract_anomaly_candidate_count"], 4)
        self.assertEqual(counts["project_status_source_lane_count"], 6)
        self.assertEqual(counts["project_lifecycle_record_count"], 4)
        self.assertEqual(counts["project_lifecycle_exception_item_count"], 3)
        self.assertEqual(counts["project_lifecycle_handoff_guard_count"], 3)
        self.assertEqual(counts["customer_analysis_source_lane_count"], 5)
        self.assertEqual(counts["customer_operating_summary_count"], 4)
        self.assertEqual(counts["customer_analysis_exception_item_count"], 4)
        self.assertEqual(counts["formal_report_count"], 0)
        self.assertEqual(counts["business_decision_basis_count"], 0)
        self.assertEqual(counts["payment_execution_count"], 0)
        self.assertEqual(counts["bank_operation_count"], 0)
        self.assertEqual(counts["collection_action_count"], 0)
        self.assertEqual(counts["legal_collection_decision_count"], 0)
        self.assertEqual(counts["github_upload_count"], 0)
        self.assertEqual(counts["full_kmfa_unit_tests"], 227)


if __name__ == "__main__":
    unittest.main()
