import unittest

from KMFA.tools.check_v014_stage1_18_overall_review import validate_v014_stage1_18_overall_review
from KMFA.tools.v014_stage1_18_overall_review import generate


class V014Stage118OverallReviewTests(unittest.TestCase):
    def test_reviews_all_stage_reviews_and_blocks_upload_until_raw_alignment(self) -> None:
        manifest = generate(generated_at="2026-07-05T20:30:00+10:00")
        validated = validate_v014_stage1_18_overall_review()

        self.assertEqual(manifest, validated)
        self.assertEqual(validated["schema_version"], "kmfa.v014_stage1_18_overall_review.v1")
        self.assertEqual(validated["project_id"], "KMFA")
        self.assertEqual(validated["version"], "0.1.4")
        self.assertEqual(validated["stage_id"], "S01-S18")
        self.assertEqual(validated["phase_id"], "V014_STAGE1_18_OVERALL_REVIEW")
        self.assertEqual(validated["review_scope"], "v014_stage1_18_overall_review_only")
        self.assertEqual(validated["task_id"], "KMFA-V014-STAGE1-18-OVERALL-REVIEW-20260705")
        self.assertEqual(validated["acceptance_ids"], ["ACC-V014-STAGE1-18-OVERALL-REVIEW"])

        stage = validated["stage_review_summary"]
        self.assertEqual(stage["stage_review_count"], 18)
        self.assertEqual(stage["stage_review_pass_count"], 18)
        self.assertEqual(stage["completed_stage_ids"], [f"S{i:02d}" for i in range(1, 19)])
        self.assertEqual(stage["total_phase_count"], 54)
        self.assertEqual(stage["total_task_count"], 162)
        self.assertEqual(stage["open_stage_review_finding_count"], 0)

        gates = validated["final_readiness_gates"]
        self.assertTrue(gates["stage_reviews_all_passed"])
        self.assertFalse(gates["raw_alignment_complete"])
        self.assertFalse(gates["lineage_full_check_complete"])
        self.assertFalse(gates["official_report_release_allowed"])
        self.assertFalse(gates["github_main_upload_allowed"])
        self.assertFalse(gates["app_reinstall_allowed"])
        self.assertEqual(gates["current_go_no_go"], "NO_GO")
        self.assertEqual(gates["current_report_grade"], "D")
        self.assertEqual(gates["pending_reconciliation_count"], 12)

        raw = validated["raw_alignment_gate"]
        self.assertTrue(raw["s05_p1_private_raw_registration_evidence_present"])
        self.assertFalse(raw["raw_alignment_complete"])
        self.assertFalse(raw["local_raw_package_hash_matches_registered"])
        self.assertFalse(raw["local_raw_package_size_matches_registered"])
        self.assertFalse(raw["raw_publication_allowed"])
        self.assertFalse(raw["raw_inbox_read_by_this_overall_review"])
        self.assertFalse(raw["raw_inbox_mutated_by_this_overall_review"])

        go_no_go = validated["overall_go_no_go"]
        self.assertEqual(go_no_go["decision"], "NO_GO")
        self.assertFalse(go_no_go["github_upload_allowed"])
        self.assertFalse(go_no_go["app_reinstall_allowed"])
        self.assertFalse(go_no_go["delivery_allowed"])
        self.assertIn("RAW_ALIGNMENT_NOT_PROVEN_COMPLETE", go_no_go["blocker_ids"])
        self.assertIn("RAW_PACKAGE_HASH_OR_SIZE_MISMATCH", go_no_go["blocker_ids"])
        self.assertIn("LINEAGE_FULL_CHECK_NOT_COMPLETE", go_no_go["blocker_ids"])
        self.assertIn("OFFICIAL_REPORT_RELEASE_NOT_ALLOWED", go_no_go["blocker_ids"])
        self.assertIn("S09_PENDING_RECONCILIATION_12", go_no_go["blocker_ids"])
        self.assertNotIn("V014_STAGE1_18_OVERALL_REVIEW_PENDING", go_no_go["blocker_ids"])

        self.assertFalse(validated["github_upload_performed"])
        self.assertEqual(validated["github_upload_status"], "not_uploaded_blocked_by_raw_alignment_and_lineage")
        self.assertFalse(validated["app_reinstall_performed"])
        self.assertEqual(validated["next_phase"], "V014_RAW_ALIGNMENT_REMEDIATION")


if __name__ == "__main__":
    unittest.main()
