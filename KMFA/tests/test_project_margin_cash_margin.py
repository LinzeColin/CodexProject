import json
import unittest

from KMFA.tools.project_margin_cash_margin import (
    REQUIRED_MARGIN_METRICS,
    calculate_margin_metrics,
    build_default_project_margin_cash_margin_layer,
    validate_project_margin_cash_margin_artifacts,
)


class ProjectMarginCashMarginTests(unittest.TestCase):
    def test_integer_margin_math_calculates_gross_cash_and_rate(self) -> None:
        metrics = calculate_margin_metrics(
            revenue_cents=1_000_00,
            management_project_cost_cents=650_00,
            collection_amount_cents=800_00,
            cash_paid_cost_cents=500_00,
        )

        self.assertEqual(metrics["system_recomputed_gross_profit_cents"], 350_00)
        self.assertEqual(metrics["cash_gross_profit_cents"], 300_00)
        self.assertEqual(metrics["gross_margin_rate_basis_points"], 3500)

    def test_default_layer_preserves_authority_and_system_values_separately(self) -> None:
        manifest, margin_records, difference_summary = build_default_project_margin_cash_margin_layer(
            generated_at="2026-06-30T23:45:00+10:00"
        )
        validate_project_margin_cash_margin_artifacts(manifest, margin_records, difference_summary)

        self.assertEqual(set(manifest["required_margin_metrics"]), set(REQUIRED_MARGIN_METRICS))
        self.assertEqual(manifest["summary"]["margin_record_count"], len(margin_records))
        self.assertGreaterEqual(manifest["summary"]["margin_record_count"], 1)
        self.assertEqual(manifest["summary"]["difference_summary_count"], len(difference_summary))

        for record in margin_records:
            self.assertEqual(set(record["margin_metric_slots"]), set(REQUIRED_MARGIN_METRICS))
            self.assertFalse(record["public_amount_values_committed"])
            self.assertFalse(record["raw_layer_write_allowed"])
            self.assertFalse(record["authority_system_overwrite_allowed"])
            self.assertIn("authority_value_private_refs", record)
            self.assertIn("system_recomputed_value_private_refs", record)
            self.assertIn("cash_margin_value_private_refs", record)
            self.assertNotEqual(
                record["authority_value_private_refs"]["gross_profit"],
                record["system_recomputed_value_private_refs"]["gross_profit"],
            )
            self.assertNotEqual(
                record["authority_value_hash_refs"]["gross_profit"],
                record["system_recomputed_value_hash_refs"]["gross_profit"],
            )

    def test_differences_enter_summary_without_s09_p3_resolution(self) -> None:
        manifest, margin_records, difference_summary = build_default_project_margin_cash_margin_layer(
            generated_at="2026-06-30T23:45:00+10:00"
        )

        self.assertTrue(difference_summary)
        self.assertFalse(manifest["stage_scope"]["s09_p3_scope_difference_reconciliation_scope_included"])
        self.assertFalse(manifest["quality_gate"]["s09_p3_reconciliation_allowed"])
        self.assertIn(
            "authority_vs_system_gross_profit",
            {item["difference_type"] for item in difference_summary},
        )
        self.assertIn(
            "authority_vs_system_gross_margin_rate",
            {item["difference_type"] for item in difference_summary},
        )
        for item in difference_summary:
            self.assertEqual(item["record_type"], "scope_difference_summary_item")
            self.assertEqual(item["stage_phase"], "S09-P2")
            self.assertEqual(item["status"], "queued_pending_s09_p3_reconciliation")
            self.assertFalse(item["s09_p3_reconciliation_performed"])

    def test_public_payload_has_no_raw_values_or_private_business_files(self) -> None:
        manifest, margin_records, difference_summary = build_default_project_margin_cash_margin_layer(
            generated_at="2026-06-30T23:45:00+10:00"
        )
        payload = json.dumps([manifest, margin_records, difference_summary], ensure_ascii=False, sort_keys=True)

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
        self.assertFalse(manifest["quality_gate"]["formal_report_allowed"])
        self.assertFalse(manifest["quality_gate"]["github_upload_allowed"])
        self.assertFalse(manifest["stage_scope"]["stage9_review_scope_included"])
        self.assertFalse(manifest["stage_scope"]["formal_report_scope_included"])
        self.assertFalse(manifest["stage_scope"]["ui_scope_included"])


if __name__ == "__main__":
    unittest.main()
