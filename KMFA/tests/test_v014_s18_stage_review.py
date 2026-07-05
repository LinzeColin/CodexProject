import unittest

from KMFA.tools.check_v014_s18_stage_review import validate_v014_s18_stage_review
from KMFA.tools.v014_s18_stage_review import generate


class V014S18StageReviewTests(unittest.TestCase):
    def test_reviews_all_s18_phases_without_upload_release_or_operations(self) -> None:
        manifest = generate(generated_at="2026-07-05T18:00:00+10:00")
        validated = validate_v014_s18_stage_review()

        self.assertEqual(manifest, validated)
        self.assertEqual(validated["schema_version"], "kmfa.v014_s18_stage_review.v1")
        self.assertEqual(validated["project_id"], "KMFA")
        self.assertEqual(validated["version"], "0.1.4")
        self.assertEqual(validated["stage_id"], "S18")
        self.assertEqual(validated["phase_id"], "S18_STAGE_REVIEW")
        self.assertEqual(validated["review_scope"], "v014_s18_stage_review_only")
        self.assertEqual(validated["task_id"], "KMFA-V014-S18-STAGE-REVIEW-20260705")
        self.assertEqual(validated["acceptance_ids"], ["ACC-V014-S18-STAGE-REVIEW"])
        self.assertEqual(validated["completed_task_ids"], ["S18REVT01", "S18REVT02", "S18REVT03"])

        self.assertTrue(validated["stage_review_performed"])
        self.assertEqual(validated["phase_results"], {"S18-P1": "PASS", "S18-P2": "PASS", "S18-P3": "PASS"})
        self.assertEqual(validated["review_findings_summary"]["open_finding_count"], 0)
        self.assertGreaterEqual(validated["review_findings_summary"]["fixed_finding_count"], 1)

        progress = validated["stage18_phase_progress"]
        self.assertEqual(progress["completed_phase_count"], 3)
        self.assertEqual(progress["total_phase_count"], 3)
        self.assertEqual(progress["derived_percent_bps"], 10000)
        self.assertEqual(progress["derived_percent_label"], "100.00%")
        self.assertTrue(progress["s18_p1_performed"])
        self.assertTrue(progress["s18_p2_performed"])
        self.assertTrue(progress["s18_p3_performed"])
        self.assertTrue(progress["stage18_review_performed"])

        gate = validated["stage_gate"]
        self.assertEqual(gate["precision_scenario_count"], 5)
        self.assertEqual(gate["consecutive_import_run_count"], 3)
        self.assertEqual(gate["full_regression_check_category_count"], 5)
        self.assertEqual(gate["stage_evidence_count"], 18)
        self.assertEqual(gate["html_audit_fail_count"], 0)
        self.assertEqual(gate["connector_plan_count"], 3)
        self.assertEqual(gate["read_only_connector_count"], 3)
        self.assertEqual(gate["opme_entry_surface_count"], 4)
        self.assertEqual(gate["next_stage_backlog_item_count"], 6)
        self.assertEqual(gate["live_connector_call_count"], 0)
        self.assertEqual(gate["external_service_call_count"], 0)
        self.assertEqual(gate["source_mutation_allowed_count"], 0)
        self.assertFalse(gate["lineage_full_check_complete"])
        self.assertEqual(gate["current_go_no_go"], "NO_GO")
        self.assertEqual(gate["current_report_grade"], "D")

        release = validated["release_state"]
        for key in (
            "delivery_allowed",
            "formal_report_allowed",
            "business_decision_basis_allowed",
            "external_connector_allowed",
            "production_restore_allowed",
            "live_connector_allowed",
            "app_reinstall_allowed",
            "business_execution_allowed",
            "github_main_upload_allowed",
        ):
            self.assertFalse(release[key], key)

        raw_boundary = validated["raw_data_boundary"]
        self.assertFalse(raw_boundary["raw_inbox_read_by_this_review"])
        self.assertFalse(raw_boundary["raw_inbox_listed_by_this_review"])
        self.assertFalse(raw_boundary["raw_inbox_stat_by_this_review"])
        self.assertFalse(raw_boundary["raw_inbox_hashed_by_this_review"])
        self.assertFalse(raw_boundary["raw_inbox_mutated_by_this_review"])
        self.assertTrue(raw_boundary["s18_p1_raw_inbox_all_false"])
        self.assertTrue(raw_boundary["s18_p2_raw_inbox_all_false"])
        self.assertTrue(raw_boundary["s18_p3_raw_inbox_all_false"])

        go_no_go = validated["stage_review_go_no_go"]
        self.assertEqual(go_no_go["decision"], "NO_GO")
        self.assertFalse(go_no_go["delivery_allowed"])
        self.assertFalse(go_no_go["github_upload_allowed"])
        self.assertTrue(go_no_go["stage18_review_performed"])
        self.assertFalse(go_no_go["lineage_full_check_complete"])
        self.assertNotIn("STAGE18_REVIEW_PENDING", go_no_go["blocker_ids"])
        self.assertIn("LINEAGE_FULL_CHECK_NOT_COMPLETE", go_no_go["blocker_ids"])

        self.assertFalse(validated["github_upload_performed"])
        self.assertEqual(validated["github_upload_status"], "not_uploaded_deferred_until_v014_stage1_18_complete")
        self.assertTrue(validated["github_upload_deferred_until_v014_stage1_18_complete"])
        self.assertEqual(validated["next_phase"], "V014_STAGE1_18_OVERALL_REVIEW")


if __name__ == "__main__":
    unittest.main()
