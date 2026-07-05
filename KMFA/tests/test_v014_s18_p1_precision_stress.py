import json
import unittest

from KMFA.tools.check_v014_s18_p1_precision_stress import (
    validate_v014_s18_p1_precision_stress,
)
from KMFA.tools.v014_s18_p1_precision_stress import (
    REQUIRED_V014_SCENARIO_TYPES,
    generate,
)


class V014S18P1PrecisionStressTests(unittest.TestCase):
    def test_v014_s18_p1_locks_precision_stress_without_upload_or_s18_p2(self) -> None:
        manifest = generate(generated_at="2026-07-05T16:30:00+10:00")
        validated = validate_v014_s18_p1_precision_stress()

        self.assertEqual(manifest, validated)
        self.assertEqual(validated["schema_version"], "kmfa.v014_s18_p1_precision_stress.v1")
        self.assertEqual(validated["project_id"], "KMFA")
        self.assertEqual(validated["version"], "0.1.4")
        self.assertEqual(validated["stage_id"], "S18")
        self.assertEqual(validated["phase_id"], "S18-P1")
        self.assertEqual(validated["phase_scope"], "v014_s18_p1_precision_stress_only")
        self.assertEqual(validated["task_id"], "KMFA-V014-S18-P1-PRECISION-STRESS-20260705")
        self.assertEqual(validated["acceptance_ids"], ["ACC-V014-S18-P1-PRECISION-STRESS"])
        self.assertEqual(validated["completed_task_ids"], ["S18P1T01", "S18P1T02", "S18P1T03"])

        self.assertTrue(validated["s17_stage_review_dependency_validated"])
        self.assertTrue(validated["historical_s18_p1_public_safe_baseline_validated"])
        self.assertEqual(tuple(validated["required_scenario_types"]), REQUIRED_V014_SCENARIO_TYPES)

        progress = validated["stage18_phase_progress"]
        self.assertEqual(progress["completed_phase_count"], 1)
        self.assertEqual(progress["total_phase_count"], 3)
        self.assertEqual(progress["derived_percent_bps"], 3333)
        self.assertEqual(progress["derived_percent_label"], "33.33%")
        self.assertTrue(progress["s18_p1_performed"])
        self.assertFalse(progress["s18_p2_performed"])
        self.assertFalse(progress["s18_p3_performed"])
        self.assertFalse(progress["stage18_review_performed"])

        summary = validated["precision_stress_summary"]
        self.assertEqual(summary["scenario_count"], 5)
        self.assertEqual(summary["scenario_type_count"], 5)
        self.assertEqual(summary["consecutive_import_run_count"], 3)
        self.assertEqual(summary["unique_import_result_hash_count"], 1)
        self.assertEqual(summary["large_batch_file_count"], 1200)
        self.assertEqual(summary["large_batch_elapsed_ms"], 348)
        self.assertEqual(summary["large_batch_performance_budget_ms"], 500)
        self.assertEqual(summary["error_report_count"], 2)
        self.assertEqual(summary["html_baseline_ref_count"], 3)
        self.assertEqual(summary["minimum_fail_difference_cents"], 1)
        self.assertEqual(summary["report_grade_visible"], "D")

        quality = validated["quality_gate"]
        for key in (
            "amount_precision_extreme_test_passed",
            "zero_delta_extreme_test_passed",
            "duplicate_import_idempotency_passed",
            "bad_file_error_report_passed",
            "missing_field_error_report_passed",
            "three_consecutive_imports_consistent",
            "large_batch_performance_within_budget",
            "blocking_error_reports_recorded",
            "metadata_only",
            "public_safe_synthetic_only",
            "html_baseline_read",
            "one_cent_difference_fails",
            "blank_dash_hash_not_zero",
        ):
            self.assertTrue(quality[key], key)
        for key in (
            "raw_business_data_used",
            "raw_inbox_read_by_this_phase",
            "raw_inbox_listed_by_this_phase",
            "raw_inbox_stat_by_this_phase",
            "raw_inbox_hashed_by_this_phase",
            "raw_inbox_mutated_by_this_phase",
            "true_money_used",
            "raw_file_committed",
            "raw_file_name_committed",
            "raw_file_hash_committed",
            "field_plaintext_committed",
            "formal_report_allowed",
            "business_decision_basis_allowed",
            "lineage_full_check_completed",
            "s18_p2_scope_included",
            "s18_p3_scope_included",
            "stage18_review_allowed",
            "github_upload_allowed",
            "external_connector_allowed",
            "production_restore_allowed",
            "app_reinstall_allowed",
            "business_execution_allowed",
        ):
            self.assertFalse(quality[key], key)

        boundaries = validated["phase_boundaries"]
        self.assertTrue(boundaries["s17_stage_review_dependency_reused"])
        self.assertTrue(boundaries["legacy_s18_p1_public_safe_baseline_reused"])
        self.assertTrue(boundaries["s18_p1_precision_stress_scope_included"])
        for key in (
            "s18_p2_full_regression_scope_included",
            "s18_p3_integration_scope_included",
            "stage18_review_scope_included",
            "github_upload_scope_included",
            "lineage_full_check_scope_included",
            "formal_report_runtime_scope_included",
            "business_execution_scope_included",
            "raw_inbox_access_scope_included",
        ):
            self.assertFalse(boundaries[key], key)

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
        self.assertEqual(validated["next_phase"], "S18-P2")


if __name__ == "__main__":
    unittest.main()
