import unittest

from KMFA.tools.check_v014_s04_p3_basic_tool_report import (
    validate_v014_s04_p3_basic_tool_report,
)


class TestV014S04P3BasicToolReport(unittest.TestCase):
    def test_basic_tool_report_locks_public_safe_boundaries(self) -> None:
        result = validate_v014_s04_p3_basic_tool_report()

        self.assertEqual(result["stage_id"], "S04")
        self.assertEqual(result["phase_id"], "S04-P3")
        self.assertEqual(result["phase_scope"], "v014_s04_p3_basic_tool_report_only")
        self.assertTrue(result["s04_p1_dependency_validated"])
        self.assertTrue(result["s04_p2_dependency_validated"])
        self.assertTrue(result["basic_tool_boundary_dependency_validated"])
        self.assertEqual(result["synthetic_boundary_case_total"], 22)
        self.assertEqual(result["synthetic_boundary_case_passed"], 22)
        self.assertEqual(result["synthetic_boundary_case_failed"], 0)
        self.assertEqual(result["amount_boundary_case_count"], 11)
        self.assertEqual(result["date_period_boundary_case_count"], 11)
        self.assertTrue(result["json_report_generated"])
        self.assertTrue(result["markdown_report_generated"])
        self.assertFalse(result["raw_dir_read_required"])
        self.assertFalse(result["raw_dir_read_performed"])
        self.assertFalse(result["raw_dir_list_performed"])
        self.assertFalse(result["raw_dir_hash_performed"])
        self.assertFalse(result["raw_dir_mutation_performed"])
        self.assertFalse(result["raw_field_mapping_performed"])
        self.assertFalse(result["raw_filename_publication_allowed"])
        self.assertFalse(result["field_plaintext_publication_allowed"])
        self.assertFalse(result["sheet_name_publication_allowed"])
        self.assertFalse(result["zip_member_name_publication_allowed"])
        self.assertFalse(result["row_value_publication_allowed"])
        self.assertFalse(result["business_value_publication_allowed"])
        self.assertFalse(result["stage4_review_performed"])
        self.assertFalse(result["stage4_upload_gate_performed"])
        self.assertFalse(result["s05_started"])
        self.assertFalse(result["github_upload_performed"])
        self.assertFalse(result["github_main_upload_allowed"])
        self.assertFalse(result["delivery_allowed"])
        self.assertEqual(result["current_data_quality_grade"], "Q2")
        self.assertEqual(result["current_report_grade"], "D")
        self.assertEqual(result["release_permission"], "blocked")
        self.assertEqual(result["current_go_no_go"], "NO_GO")
        self.assertEqual(result["github_upload_status"], "deferred_until_v014_stage1_18_complete_overall_review")
        self.assertIn("Stage 4 overall review", result["next_required_step"])
        self.assertIn("separate run", result["next_required_step"])
        self.assertIn("Stage 1-18 complete overall review", result["next_required_step"])


if __name__ == "__main__":
    unittest.main()
