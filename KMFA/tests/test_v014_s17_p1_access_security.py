import unittest

from KMFA.tools.check_v014_s17_p1_access_security import read_jsonl, validate_v014_s17_p1_access_security
from KMFA.tools.v014_s17_p1_access_security import (
    ROLE_PERMISSION_LOCK_PATH,
    SENSITIVE_POLICY_LOCK_PATH,
    generate,
)


class V014S17P1AccessSecurityTests(unittest.TestCase):
    def test_locks_access_security_without_notification_delivery_or_upload(self) -> None:
        manifest = generate()
        validated = validate_v014_s17_p1_access_security()

        self.assertEqual(manifest, validated)
        self.assertEqual(validated["project_id"], "KMFA")
        self.assertEqual(validated["version"], "0.1.4")
        self.assertEqual(validated["stage_id"], "S17")
        self.assertEqual(validated["phase_id"], "S17-P1")
        self.assertEqual(validated["phase_scope"], "v014_s17_p1_access_security_only")
        self.assertEqual(validated["task_id"], "KMFA-V014-S17-P1-ACCESS-SECURITY-20260705")
        self.assertEqual(validated["acceptance_ids"], ["ACC-V014-S17-P1-ACCESS-SECURITY"])
        self.assertEqual(validated["completed_task_ids"], ["S17P1T01", "S17P1T02", "S17P1T03"])
        self.assertTrue(validated["s16_stage_review_dependency_validated"])
        self.assertTrue(validated["historical_s17_p1_public_safe_baseline_validated"])

        role_locks = read_jsonl(ROLE_PERMISSION_LOCK_PATH)
        for row in role_locks:
            expected_scope = "none" if row["role_id"] == "readonly" else "metadata_only"
            self.assertEqual(row["max_write_scope"], expected_scope)
            self.assertFalse(row["raw_business_data_access_in_public_repo"])
            self.assertFalse(row["sensitive_file_public_commit_allowed"])

        sensitive_locks = read_jsonl(SENSITIVE_POLICY_LOCK_PATH)
        for row in sensitive_locks:
            self.assertFalse(row["public_repo_allowed"])
            self.assertFalse(row["git_upload_allowed"])
            self.assertFalse(row["value_plaintext_allowed"])
            self.assertTrue(row["metadata_hash_or_ref_only_allowed"])
            self.assertEqual(row["handling"], "private_storage_or_hash_only_metadata")

        progress = validated["stage17_phase_progress"]
        self.assertEqual(progress["completed_phase_count"], 1)
        self.assertEqual(progress["total_phase_count"], 3)
        self.assertEqual(progress["derived_percent_bps"], 3333)
        self.assertEqual(progress["derived_percent_label"], "33.33%")
        self.assertTrue(progress["s17_p1_performed"])
        self.assertFalse(progress["s17_p2_performed"])
        self.assertFalse(progress["s17_p3_performed"])
        self.assertFalse(progress["stage17_review_performed"])

        summary = validated["access_security_summary"]
        self.assertEqual(summary["role_count"], 4)
        self.assertEqual(summary["sensitive_policy_category_count"], 15)
        self.assertEqual(summary["audit_action_type_count"], 5)
        self.assertEqual(summary["report_grade_visible"], "D")
        self.assertEqual(summary["notification_delivery_count"], 0)
        self.assertEqual(summary["external_connector_count"], 0)
        self.assertEqual(summary["business_execution_count"], 0)

        quality = validated["quality_gate"]
        self.assertTrue(quality["role_permission_matrix_complete"])
        self.assertTrue(quality["sensitive_public_repo_policy_enforced"])
        self.assertTrue(quality["audit_log_policy_complete"])
        self.assertFalse(quality["raw_sensitive_public_repo_allowed"])
        self.assertFalse(quality["notification_delivery_allowed"])
        self.assertFalse(quality["notification_full_report_body_allowed"])
        self.assertFalse(quality["formal_report_allowed"])
        self.assertFalse(quality["business_decision_basis_allowed"])
        self.assertFalse(quality["business_execution_allowed"])
        self.assertFalse(quality["external_connector_allowed"])
        self.assertFalse(quality["s17_p2_allowed"])
        self.assertFalse(quality["s17_p3_allowed"])
        self.assertFalse(quality["stage17_review_allowed"])
        self.assertFalse(quality["github_upload_allowed"])

        boundaries = validated["phase_boundaries"]
        self.assertTrue(boundaries["s16_stage_review_dependency_reused"])
        self.assertTrue(boundaries["legacy_s17_p1_public_safe_baseline_reused"])
        self.assertTrue(boundaries["s17_p1_access_security_scope_included"])
        self.assertFalse(boundaries["s17_p2_notification_scope_included"])
        self.assertFalse(boundaries["s17_p3_operations_scope_included"])
        self.assertFalse(boundaries["stage17_review_scope_included"])
        self.assertFalse(boundaries["github_upload_scope_included"])
        self.assertFalse(boundaries["notification_delivery_scope_included"])

        raw_boundary = validated["raw_data_boundary"]
        self.assertFalse(raw_boundary["raw_inbox_read_by_this_phase"])
        self.assertFalse(raw_boundary["raw_inbox_listed_by_this_phase"])
        self.assertFalse(raw_boundary["raw_inbox_mutated_by_this_phase"])

        upload = validated["github_upload"]
        self.assertFalse(upload["github_upload_performed"])
        self.assertFalse(upload["github_upload_ready_next_gate"])
        self.assertTrue(upload["github_upload_deferred_until_v014_stage1_18_complete"])
        self.assertEqual(validated["next_phase"], "S17-P2")


if __name__ == "__main__":
    unittest.main()
