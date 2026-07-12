import unittest

from KMFA.tools.check_v014_s10_stage_review import validate_v014_s10_stage_review


class TestV014S10StageReview(unittest.TestCase):
    def test_stage10_review_closes_report_generation_without_upload_or_formal_release(self) -> None:
        manifest = validate_v014_s10_stage_review()

        self.assertEqual(manifest["stage_id"], "S10")
        self.assertEqual(manifest["status"], "review_passed_local_only_no_go_upload_deferred_until_v014_stage1_18_complete")
        self.assertTrue(manifest["stage_review_performed"])
        self.assertEqual(
            manifest["phase_results"],
            {"S10-P1": "PASS", "S10-P2": "PASS", "S10-P3": "PASS"},
        )
        self.assertEqual(manifest["review_findings_summary"]["open_finding_count"], 0)
        self.assertGreaterEqual(manifest["review_findings_summary"]["fixed_finding_count"], 1)
        self.assertEqual(manifest["stage_gate"]["report_template_count"], 2)
        self.assertEqual(manifest["stage_gate"]["report_grade_record_count"], 2)
        self.assertEqual(manifest["stage_gate"]["report_export_record_count"], 2)
        self.assertEqual(manifest["stage_gate"]["html_export_count"], 2)
        self.assertEqual(manifest["stage_gate"]["csv_appendix_count"], 2)
        self.assertEqual(manifest["stage_gate"]["excel_compatible_download_count"], 2)
        self.assertEqual(manifest["stage_gate"]["pending_reconciliation_count"], 12)
        self.assertEqual(manifest["stage_gate"]["confirmed_resolution_count"], 0)
        self.assertEqual(manifest["stage_gate"]["formal_report_count"], 0)
        self.assertEqual(manifest["stage_gate"]["business_decision_basis_count"], 0)
        self.assertEqual(manifest["stage_gate"]["current_report_grade"], "D")
        self.assertFalse(manifest["s11_p1_performed"])
        self.assertFalse(manifest["github_upload_performed"])
        self.assertEqual(manifest["github_upload_status"], "not_uploaded_deferred_until_v014_stage1_18_complete")
        self.assertTrue(manifest["raw_data_boundary"]["s10_p1_raw_inbox_all_false"])
        self.assertTrue(manifest["raw_data_boundary"]["s10_p2_raw_inbox_all_false"])
        self.assertTrue(manifest["raw_data_boundary"]["s10_p3_raw_inbox_all_false"])


if __name__ == "__main__":
    unittest.main()
