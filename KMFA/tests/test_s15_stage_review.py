import unittest

from KMFA.tools.check_s15_stage_review import (
    DEFAULT_REVIEW_MANIFEST,
    validate_stage_review,
)


class S15StageReviewTests(unittest.TestCase):
    def test_stage15_review_manifest_matches_phase_evidence(self) -> None:
        counts = validate_stage_review(DEFAULT_REVIEW_MANIFEST)

        self.assertEqual(counts["field_definition_count"], 6)
        self.assertEqual(counts["field_binding_count"], 6)
        self.assertEqual(counts["manual_review_field_count"], 4)
        self.assertEqual(counts["performance_fact_row_count"], 4)
        self.assertEqual(counts["abnormal_review_item_count"], 16)
        self.assertEqual(counts["fact_interface_contract_count"], 1)
        self.assertEqual(counts["future_salary_system_readiness_row_count"], 4)
        self.assertEqual(counts["pending_review_item_count"], 16)
        self.assertEqual(counts["salary_calculation_count"], 0)
        self.assertEqual(counts["bonus_approval_count"], 0)
        self.assertEqual(counts["payroll_export_count"], 0)
        self.assertEqual(counts["final_compensation_decision_count"], 0)
        self.assertEqual(counts["full_kmfa_unit_tests"], 207)


if __name__ == "__main__":
    unittest.main()
