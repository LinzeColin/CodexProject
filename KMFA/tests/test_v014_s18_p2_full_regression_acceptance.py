import json
import unittest

from KMFA.tools.check_v014_s18_p2_full_regression_acceptance import (
    validate_v014_s18_p2_full_regression_acceptance,
)
from KMFA.tools.v014_s18_p2_full_regression_acceptance import (
    REQUIRED_V014_CHECK_CATEGORIES,
    REQUIRED_V014_STAGE_IDS,
    generate,
)


class V014S18P2FullRegressionAcceptanceTests(unittest.TestCase):
    def test_v014_s18_p2_locks_full_regression_without_upload_or_s18_p3(self) -> None:
        manifest = generate(generated_at="2026-07-05T17:30:00+10:00")
        validated = validate_v014_s18_p2_full_regression_acceptance()

        self.assertEqual(manifest, validated)
        self.assertEqual(validated["schema_version"], "kmfa.v014_s18_p2_full_regression_acceptance.v1")
        self.assertEqual(validated["project_id"], "KMFA")
        self.assertEqual(validated["version"], "0.1.4")
        self.assertEqual(validated["stage_id"], "S18")
        self.assertEqual(validated["phase_id"], "S18-P2")
        self.assertEqual(validated["phase_scope"], "v014_s18_p2_full_regression_acceptance_only")
        self.assertEqual(validated["task_id"], "KMFA-V014-S18-P2-FULL-REGRESSION-ACCEPTANCE-20260705")
        self.assertEqual(validated["acceptance_ids"], ["ACC-V014-S18-P2-FULL-REGRESSION-ACCEPTANCE"])
        self.assertEqual(validated["completed_task_ids"], ["S18P2T01", "S18P2T02", "S18P2T03"])

        self.assertTrue(validated["s18_p1_dependency_validated"])
        self.assertTrue(validated["historical_s18_p2_public_safe_baseline_validated"])
        self.assertEqual(tuple(validated["required_check_categories"]), REQUIRED_V014_CHECK_CATEGORIES)
        self.assertEqual(tuple(validated["required_stage_ids"]), REQUIRED_V014_STAGE_IDS)

        progress = validated["stage18_phase_progress"]
        self.assertEqual(progress["completed_phase_count"], 2)
        self.assertEqual(progress["total_phase_count"], 3)
        self.assertEqual(progress["derived_percent_bps"], 6667)
        self.assertEqual(progress["derived_percent_label"], "66.67%")
        self.assertTrue(progress["s18_p1_performed"])
        self.assertTrue(progress["s18_p2_performed"])
        self.assertFalse(progress["s18_p3_performed"])
        self.assertFalse(progress["stage18_review_performed"])

        summary = validated["full_regression_summary"]
        self.assertEqual(summary["check_category_count"], 5)
        self.assertEqual(summary["stage_evidence_count"], 18)
        self.assertEqual(summary["html_audit_fail_count"], 0)
        self.assertGreaterEqual(summary["html_audit_row_count"], 1)
        self.assertEqual(summary["go_no_go_decision"], "NO_GO")
        self.assertEqual(summary["maximum_report_grade"], "D")
        self.assertEqual(summary["next_required_phase"], "S18-P3")

        quality = validated["quality_gate"]
        for key in (
            "no_omission_check_passed",
            "zero_delta_check_ran",
            "schema_check_passed",
            "lineage_check_ran",
            "ui_check_passed",
            "stage_evidence_confirmed",
            "go_no_go_report_generated",
            "quality_not_passed_must_not_deliver",
            "html_human_flow_audit_executed",
            "html_human_flow_audit_fail_zero",
            "metadata_only",
            "public_safe_synthetic_only",
        ):
            self.assertTrue(quality[key], key)
        for key in (
            "lineage_full_check_complete",
            "official_report_release_allowed",
            "business_decision_basis_allowed",
            "github_upload_allowed",
            "phase_completion_upload_allowed",
            "s18_p3_scope_included",
            "stage18_review_allowed",
            "external_connector_allowed",
            "production_restore_allowed",
            "app_reinstall_allowed",
            "business_execution_allowed",
            "raw_business_data_used",
            "raw_inbox_read_by_this_phase",
            "raw_inbox_listed_by_this_phase",
            "raw_inbox_stat_by_this_phase",
            "raw_inbox_hashed_by_this_phase",
            "raw_inbox_mutated_by_this_phase",
            "raw_file_committed",
            "field_plaintext_committed",
        ):
            self.assertFalse(quality[key], key)

        boundaries = validated["phase_boundaries"]
        self.assertTrue(boundaries["s18_p1_dependency_reused"])
        self.assertTrue(boundaries["legacy_s18_p2_public_safe_baseline_reused"])
        self.assertTrue(boundaries["s18_p2_full_regression_scope_included"])
        for key in (
            "s18_p3_integration_scope_included",
            "stage18_review_scope_included",
            "github_upload_scope_included",
            "lineage_full_check_scope_included",
            "formal_report_runtime_scope_included",
            "business_execution_scope_included",
            "raw_inbox_access_scope_included",
            "production_restore_scope_included",
            "external_connector_scope_included",
            "app_reinstall_scope_included",
        ):
            self.assertFalse(boundaries[key], key)

        stage_ids = [row["stage_id"] for row in validated["stage_acceptance_evidence"]]
        self.assertEqual(tuple(stage_ids), REQUIRED_V014_STAGE_IDS)
        s18 = validated["stage_acceptance_evidence"][-1]
        self.assertEqual(s18["stage_id"], "S18")
        self.assertIn("S18-P1", s18["completed_phase_ids"])
        self.assertIn("S18-P2", s18["completed_phase_ids"])
        self.assertNotIn("S18-P3", s18["completed_phase_ids"])
        self.assertEqual(s18["pending_phase_ids"], ["S18-P3"])

        go_no_go = validated["go_no_go"]
        self.assertEqual(go_no_go["decision"], "NO_GO")
        self.assertIn("LINEAGE_FULL_CHECK_NOT_COMPLETE", go_no_go["blocker_ids"])
        self.assertIn("OFFICIAL_REPORT_RELEASE_NOT_ALLOWED", go_no_go["blocker_ids"])
        self.assertIn("S18_P3_PENDING", go_no_go["blocker_ids"])
        self.assertFalse(go_no_go["delivery_allowed"])
        self.assertFalse(go_no_go["business_decision_basis_allowed"])
        self.assertFalse(go_no_go["github_upload_allowed"])

        html_audit = validated["html_human_flow_audit"]
        self.assertTrue(html_audit["audit_executed"])
        self.assertEqual(html_audit["fail_count"], 0)
        self.assertGreaterEqual(html_audit["row_count"], 1)
        self.assertTrue(html_audit["audit_csv_ref"].endswith("html_human_flow_audit.csv"))

        raw_boundary = validated["raw_data_boundary"]
        self.assertFalse(raw_boundary["raw_inbox_read_by_this_phase"])
        self.assertFalse(raw_boundary["raw_inbox_listed_by_this_phase"])
        self.assertFalse(raw_boundary["raw_inbox_stat_by_this_phase"])
        self.assertFalse(raw_boundary["raw_inbox_hashed_by_this_phase"])
        self.assertFalse(raw_boundary["raw_inbox_mutated_by_this_phase"])

        payload = json.dumps(manifest, ensure_ascii=False, sort_keys=True)
        for forbidden in (
            "raw_value",
            "normalized_value",
            "source_header_text",
            "original_filename",
            "private_ref://",
            "member_sha256",
            "actual_package_sha256",
            "amount_cents:",
            "amount_yuan:",
            "customer_name_plaintext",
            "project_name_plaintext",
            "credential_payload",
        ):
            self.assertNotIn(forbidden, payload)

        self.assertFalse(validated["github_upload"]["github_upload_performed"])
        self.assertTrue(validated["github_upload"]["github_upload_deferred_until_v014_stage1_18_complete"])
        self.assertEqual(validated["next_phase"], "S18-P3")


if __name__ == "__main__":
    unittest.main()
