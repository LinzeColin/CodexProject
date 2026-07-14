import unittest

from KMFA.tools.check_v013_s10_p2_report_grade_runtime_replay import (
    validate_v013_s10_p2_report_grade_runtime_replay,
)
from KMFA.tools.v013_s10_p2_report_grade_runtime_replay import generate


class TestV013S10P2ReportGradeRuntimeReplay(unittest.TestCase):
    def test_replay_locks_d_grade_report_runtime_without_export_review_or_upload(self) -> None:
        generate()
        result = validate_v013_s10_p2_report_grade_runtime_replay()

        self.assertEqual(result["stage_id"], "S10")
        self.assertEqual(result["phase_id"], "S10-P2")
        self.assertEqual(result["phase_scope"], "v013_s10_p2_report_grade_runtime_replay_only")
        self.assertEqual(result["template_count"], 2)
        self.assertEqual(result["report_grade_record_count"], 2)
        self.assertEqual(result["grade_distribution"], {"D": 2})
        self.assertEqual(result["pending_reconciliation_count"], 12)
        self.assertEqual(result["confirmed_resolution_count"], 0)
        self.assertEqual(result["source_quality_grade"], "Q4")
        self.assertFalse(result["zero_delta_passed"])
        self.assertFalse(result["complete_trusted_report_display_allowed"])
        self.assertFalse(result["formal_report_allowed"])
        self.assertFalse(result["business_decision_basis_allowed"])
        self.assertFalse(result["s10_p3_export_scope_included"])
        self.assertFalse(result["s10_p3_performed"])
        self.assertFalse(result["stage10_review_performed"])
        self.assertFalse(result["github_upload_performed"])
        self.assertTrue(result["github_upload_deferred_until_stage10_batch"])
        self.assertFalse(result["raw_dir_read_performed"])
        self.assertFalse(result["raw_dir_mutation_performed"])
        self.assertIn("S10-P3", result["next_required_step"])
        self.assertIn("Stages 1-10", result["next_required_step"])
        self.assertIn("separate run", result["next_required_step"])


if __name__ == "__main__":
    unittest.main()
