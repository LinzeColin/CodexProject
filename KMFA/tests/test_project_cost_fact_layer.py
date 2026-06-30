import json
import unittest

from KMFA.tools.project_cost_fact_layer import (
    REQUIRED_COST_CATEGORIES,
    REQUIRED_FACT_METRICS,
    build_default_project_cost_fact_layer,
    validate_project_cost_fact_layer_artifacts,
)


class ProjectCostFactLayerTests(unittest.TestCase):
    def test_default_fact_layer_covers_required_project_cost_metrics_and_categories(self) -> None:
        manifest, fact_records, unallocated_pool = build_default_project_cost_fact_layer(
            generated_at="2026-06-30T23:30:00+10:00"
        )
        validate_project_cost_fact_layer_artifacts(manifest, fact_records, unallocated_pool)

        self.assertEqual(
            set(REQUIRED_FACT_METRICS),
            {
                "revenue",
                "contract_amount",
                "invoice_amount",
                "collection_amount",
                "cost_total",
                "cost_category",
            },
        )
        self.assertEqual(manifest["summary"]["required_metric_count"], len(REQUIRED_FACT_METRICS))
        self.assertEqual(manifest["summary"]["cost_category_count"], len(REQUIRED_COST_CATEGORIES))
        self.assertGreaterEqual(manifest["summary"]["fact_record_count"], 1)
        self.assertEqual(manifest["summary"]["unallocated_pool_count"], len(unallocated_pool))
        self.assertEqual(set(manifest["required_cost_categories"]), set(REQUIRED_COST_CATEGORIES))

        for record in fact_records:
            self.assertEqual(set(record["metric_slots"]), set(REQUIRED_FACT_METRICS))
            self.assertEqual(set(record["cost_category_slots"]), set(REQUIRED_COST_CATEGORIES))
            self.assertFalse(record["formal_calculation_allowed"])
            self.assertFalse(record["raw_layer_write_allowed"])
            self.assertIn("authority_baseline_ref", record)
            self.assertIn("project_identity_profile_ref", record)
            self.assertIn("business_entity_schema_ref", record)

    def test_quality_blocks_keep_fact_layer_structural_and_queue_unallocated_costs(self) -> None:
        manifest, fact_records, unallocated_pool = build_default_project_cost_fact_layer(
            generated_at="2026-06-30T23:30:00+10:00"
        )

        self.assertEqual(manifest["fact_layer_status"], "structural_fact_layer_blocked_for_formal_calculation")
        self.assertFalse(manifest["quality_gate"]["formal_report_allowed"])
        self.assertFalse(manifest["quality_gate"]["github_upload_allowed"])
        self.assertFalse(manifest["quality_gate"]["s09_p2_margin_calculation_allowed"])
        self.assertFalse(manifest["quality_gate"]["s09_p3_scope_difference_reconciliation_allowed"])
        self.assertGreaterEqual(manifest["upstream_quality_summary"]["manual_review_queue_count"], 1)
        self.assertGreaterEqual(manifest["upstream_quality_summary"]["unresolved_difference_count"], 1)

        self.assertTrue(unallocated_pool)
        for pool_item in unallocated_pool:
            self.assertEqual(pool_item["pool_type"], "unallocated_project_cost_pool")
            self.assertEqual(pool_item["assignment_status"], "pending_project_assignment_or_quality_resolution")
            self.assertFalse(pool_item["amount_value_public_committed"])
            self.assertFalse(pool_item["raw_layer_write_allowed"])
            self.assertIn("source_difference_queue_ref", pool_item)

        for record in fact_records:
            self.assertEqual(record["calculation_status"], "blocked_pending_quality_resolution")
            self.assertFalse(record["metric_values_public_committed"])

    def test_public_payload_has_no_raw_values_or_private_business_files(self) -> None:
        manifest, fact_records, unallocated_pool = build_default_project_cost_fact_layer(
            generated_at="2026-06-30T23:30:00+10:00"
        )
        payload = json.dumps([manifest, fact_records, unallocated_pool], ensure_ascii=False, sort_keys=True)

        for forbidden_key in (
            "raw_value",
            "normalized_value",
            "plaintext_value",
            "source_header_text",
            "original_filename",
            "private_csv",
            "bank_account_number",
            "identity_document_number",
            "account_number",
            "raw_file_bytes",
        ):
            self.assertNotIn(forbidden_key, payload)
        self.assertIn("sha256:", payload)
        self.assertIn("private_ref://", payload)
        self.assertIn("source_ref://", payload)

    def test_scope_excludes_later_phases_review_report_ui_connector_and_upload(self) -> None:
        manifest, fact_records, unallocated_pool = build_default_project_cost_fact_layer(
            generated_at="2026-06-30T23:30:00+10:00"
        )

        self.assertTrue(manifest["stage_scope"]["s09_p1_project_cost_fact_layer_scope_included"])
        for flag in (
            "s09_p2_margin_calculation_scope_included",
            "s09_p3_scope_difference_reconciliation_scope_included",
            "stage9_review_scope_included",
            "lineage_full_check_scope_included",
            "formal_report_scope_included",
            "ui_scope_included",
            "external_connector_scope_included",
        ):
            self.assertFalse(manifest["stage_scope"][flag])


if __name__ == "__main__":
    unittest.main()
