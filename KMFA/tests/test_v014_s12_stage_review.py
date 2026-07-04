import unittest

from KMFA.tools.check_v014_s12_stage_review import validate_v014_s12_stage_review


class TestV014S12StageReview(unittest.TestCase):
    def test_stage12_review_closes_manual_workbench_without_upload_or_release(self) -> None:
        manifest = validate_v014_s12_stage_review()

        self.assertEqual(manifest["stage_id"], "S12")
        self.assertEqual(manifest["status"], "review_passed_local_only_no_go_upload_deferred_until_v014_stage1_18_complete")
        self.assertTrue(manifest["stage_review_performed"])
        self.assertEqual(
            manifest["phase_results"],
            {"S12-P1": "PASS", "S12-P2": "PASS", "S12-P3": "PASS"},
        )
        self.assertEqual(manifest["review_findings_summary"]["open_finding_count"], 0)
        self.assertGreaterEqual(manifest["review_findings_summary"]["fixed_finding_count"], 1)

        gate = manifest["stage_gate"]
        self.assertEqual(gate["manual_event_count"], 5)
        self.assertEqual(gate["manual_action_kind_count"], 4)
        self.assertEqual(gate["approved_event_count"], 1)
        self.assertEqual(gate["reverse_event_count"], 1)
        self.assertEqual(gate["impact_preview_count"], 5)
        self.assertEqual(gate["affected_project_count"], 8)
        self.assertEqual(gate["affected_metric_count"], 11)
        self.assertEqual(gate["affected_report_count"], 5)
        self.assertEqual(gate["high_risk_count"], 3)
        self.assertEqual(gate["blocked_publish_count"], 3)
        self.assertEqual(gate["publish_allowed_count"], 2)
        self.assertEqual(gate["eligible_event_count"], 2)
        self.assertEqual(gate["cache_invalidation_count"], 2)
        self.assertEqual(gate["rerun_chain_layer_count"], 4)
        self.assertEqual(gate["rerun_step_count"], 8)
        self.assertEqual(gate["same_source_consistency_check_count"], 2)
        self.assertEqual(gate["old_version_retained_count"], 8)
        self.assertEqual(gate["new_version_appended_count"], 8)
        self.assertEqual(gate["html_export_count"], 3)
        self.assertEqual(gate["formal_report_count"], 0)
        self.assertEqual(gate["business_decision_basis_count"], 0)
        self.assertEqual(gate["current_report_grade"], "D")
        self.assertEqual(gate["release_permission"], "blocked")

        self.assertFalse(manifest["s13_p1_performed"])
        self.assertFalse(manifest["github_upload_performed"])
        self.assertEqual(manifest["github_upload_status"], "not_uploaded_deferred_until_v014_stage1_18_complete")
        self.assertTrue(manifest["raw_data_boundary"]["s12_p1_raw_inbox_all_false"])
        self.assertTrue(manifest["raw_data_boundary"]["s12_p2_raw_inbox_all_false"])
        self.assertTrue(manifest["raw_data_boundary"]["s12_p3_raw_inbox_all_false"])


if __name__ == "__main__":
    unittest.main()
