import unittest

from KMFA.tools.check_v014_s10_p2_report_trust_grade import (
    validate_v014_s10_p2_report_trust_grade,
)
from KMFA.tools.v014_s10_p2_report_trust_grade import generate


class TestV014S10P2ReportTrustGrade(unittest.TestCase):
    def test_locks_report_trust_grade_without_export_review_or_upload(self) -> None:
        generate()
        result = validate_v014_s10_p2_report_trust_grade()

        self.assertEqual(result["stage_id"], "S10")
        self.assertEqual(result["phase_id"], "S10-P2")
        self.assertEqual(result["phase_scope"], "v014_s10_p2_report_trust_grade_only")
        self.assertEqual(result["template_count"], 2)
        self.assertEqual(result["report_grade_record_count"], 2)
        self.assertEqual(result["grade_distribution"], {"D": 2})
        self.assertEqual(result["pending_reconciliation_count"], 12)
        self.assertEqual(result["confirmed_resolution_count"], 0)
        self.assertEqual(result["source_quality_grade"], "Q4")
        self.assertFalse(result["zero_delta_passed"])
        self.assertFalse(result["complete_trusted_report_display_allowed"])
        self.assertFalse(result["full_trusted_report_allowed"])
        self.assertFalse(result["formal_report_allowed"])
        self.assertFalse(result["business_decision_basis_allowed"])
        self.assertEqual(result["record_version_binding_count"], 2)
        self.assertFalse(result["s10_p3_export_scope_included"])
        self.assertFalse(result["s10_p3_performed"])
        self.assertFalse(result["stage10_review_performed"])
        self.assertFalse(result["github_upload_performed"])
        self.assertTrue(result["github_upload_deferred_until_v014_stage1_18_complete"])
        self.assertFalse(result["raw_inbox_read_performed"])
        self.assertFalse(result["raw_inbox_mutation_performed"])
        self.assertIn("S10-P3", result["next_required_step"])
        self.assertIn("v1.4 Stage 1-18", result["next_required_step"])
        self.assertIn("separate run", result["next_required_step"])


if __name__ == "__main__":
    unittest.main()
