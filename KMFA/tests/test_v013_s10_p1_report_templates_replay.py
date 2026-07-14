import unittest

from KMFA.tools.check_v013_s10_p1_report_templates_replay import (
    validate_v013_s10_p1_report_templates_replay,
)
from KMFA.tools.v013_s10_p1_report_templates_replay import generate


class TestV013S10P1ReportTemplatesReplay(unittest.TestCase):
    def test_replay_locks_public_safe_report_templates_without_later_phase_or_upload(self) -> None:
        generate()
        result = validate_v013_s10_p1_report_templates_replay()

        self.assertEqual(result["stage_id"], "S10")
        self.assertEqual(result["phase_id"], "S10-P1")
        self.assertEqual(result["phase_scope"], "v013_s10_p1_report_templates_replay_only")
        self.assertEqual(result["template_count"], 2)
        self.assertEqual(result["section_count"], 11)
        self.assertEqual(result["project_cost_section_count"], 4)
        self.assertEqual(result["business_overview_section_count"], 7)
        self.assertEqual(result["pending_reconciliation_count"], 12)
        self.assertEqual(result["formal_report_count"], 0)
        self.assertEqual(result["export_artifact_count"], 0)
        self.assertFalse(result["formal_report_allowed"])
        self.assertFalse(result["trusted_grade_assignment_allowed"])
        self.assertFalse(result["report_runtime_scope_included"])
        self.assertFalse(result["s10_p2_performed"])
        self.assertFalse(result["s10_p3_performed"])
        self.assertFalse(result["stage10_review_performed"])
        self.assertFalse(result["github_upload_performed"])
        self.assertTrue(result["github_upload_deferred_until_stage10_batch"])
        self.assertFalse(result["raw_dir_read_performed"])
        self.assertFalse(result["raw_dir_mutation_performed"])
        self.assertIn("S10-P2", result["next_required_step"])
        self.assertIn("Stages 1-10", result["next_required_step"])
        self.assertIn("separate run", result["next_required_step"])


if __name__ == "__main__":
    unittest.main()
