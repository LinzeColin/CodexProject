import json
import unittest

from KMFA.tools.performance_review_list import (
    REQUIRED_PERFORMANCE_REVIEW_FIELDS,
    PerformanceReviewListError,
    build_default_performance_review_list_artifacts,
    validate_performance_review_list_artifacts,
)


class PerformanceReviewListTests(unittest.TestCase):
    def test_default_runtime_covers_s15_p2_required_scope(self) -> None:
        manifest, fact_rows, review_items = build_default_performance_review_list_artifacts(
            generated_at="2026-07-01T23:45:00+10:00"
        )
        validate_performance_review_list_artifacts(manifest, fact_rows, review_items)

        self.assertEqual(manifest["stage_phase"], "S15-P2")
        self.assertEqual(tuple(manifest["required_review_fields"]), REQUIRED_PERFORMANCE_REVIEW_FIELDS)
        self.assertEqual(manifest["summary"]["performance_fact_row_count"], 4)
        self.assertEqual(manifest["summary"]["abnormal_review_item_count"], 16)
        self.assertEqual(manifest["summary"]["manual_review_field_count"], 4)
        self.assertTrue(manifest["quality_gate"]["performance_fact_table_output_allowed"])
        self.assertTrue(manifest["quality_gate"]["abnormal_project_review_list_allowed"])
        self.assertFalse(manifest["quality_gate"]["salary_calculation_allowed"])
        self.assertFalse(manifest["quality_gate"]["wage_calculation_allowed"])
        self.assertFalse(manifest["quality_gate"]["bonus_approval_allowed"])
        self.assertFalse(manifest["quality_gate"]["payroll_export_allowed"])
        self.assertFalse(manifest["quality_gate"]["final_compensation_decision_allowed"])
        self.assertFalse(manifest["stage_scope"]["s15_p3_salary_boundary_scope_included"])
        self.assertFalse(manifest["stage_scope"]["stage15_review_scope_included"])
        self.assertFalse(manifest["stage_scope"]["github_upload_scope_included"])

    def test_performance_fact_table_uses_public_safe_refs_and_statuses_only(self) -> None:
        manifest, fact_rows, review_items = build_default_performance_review_list_artifacts(
            generated_at="2026-07-01T23:45:00+10:00"
        )
        validate_performance_review_list_artifacts(manifest, fact_rows, review_items)

        self.assertEqual(
            [row["performance_fact_row_id"] for row in fact_rows],
            ["S15P2-FACT-001", "S15P2-FACT-002", "S15P2-FACT-003", "S15P2-FACT-004"],
        )
        for row in fact_rows:
            self.assertEqual(row["record_type"], "performance_fact_table_row")
            self.assertEqual(row["stage_phase"], "S15-P2")
            self.assertTrue(row["project_ref"].startswith("entity_ref://KMFA/S08-P2/project/"))
            self.assertEqual(set(row["fact_status_by_field"]), set(REQUIRED_PERFORMANCE_REVIEW_FIELDS))
            self.assertEqual(set(row["fact_hash_refs_by_field"]), {"invoice_amount", "gross_margin_rate"})
            self.assertEqual(set(row["manual_review_refs_by_field"]), set(REQUIRED_PERFORMANCE_REVIEW_FIELDS[2:]))
            self.assertFalse(row["raw_business_values_allowed"])
            self.assertFalse(row["public_numeric_values_allowed"])
            self.assertFalse(row["field_plaintext_allowed"])
            self.assertFalse(row["salary_calculation_allowed"])
            self.assertFalse(row["bonus_approval_allowed"])
            self.assertFalse(row["payroll_export_allowed"])

    def test_review_items_cover_abnormal_project_review_matters_without_actions(self) -> None:
        manifest, fact_rows, review_items = build_default_performance_review_list_artifacts(
            generated_at="2026-07-01T23:45:00+10:00"
        )
        validate_performance_review_list_artifacts(manifest, fact_rows, review_items)

        by_fact = {}
        for item in review_items:
            by_fact.setdefault(item["performance_fact_row_ref"], set()).add(item["field_key"])
            self.assertEqual(item["record_type"], "performance_review_item")
            self.assertEqual(item["stage_phase"], "S15-P2")
            self.assertEqual(item["resolution_status"], "pending_owner_or_authorized_review")
            self.assertEqual(item["review_mode"], "owner_or_authorized_delegate_review_only")
            self.assertTrue(item["abnormal_project_review_required"])
            self.assertFalse(item["auto_resolution_allowed"])
            self.assertFalse(item["salary_calculation_allowed"])
            self.assertFalse(item["bonus_approval_allowed"])
            self.assertFalse(item["payroll_export_allowed"])
            self.assertFalse(item["final_compensation_decision_allowed"])

        self.assertEqual(len(by_fact), 4)
        for field_keys in by_fact.values():
            self.assertEqual(field_keys, set(REQUIRED_PERFORMANCE_REVIEW_FIELDS[2:]))

    def test_public_payload_has_no_raw_values_private_refs_files_or_credentials(self) -> None:
        manifest, fact_rows, review_items = build_default_performance_review_list_artifacts(
            generated_at="2026-07-01T23:45:00+10:00"
        )
        payload = json.dumps([manifest, fact_rows, review_items], ensure_ascii=False, sort_keys=True)

        for forbidden_text in (
            '"amount_cents":',
            '"amount_yuan":',
            "raw_value",
            "normalized_value",
            "plaintext_value",
            "source_header_text",
            "original_filename",
            "private://",
            "private_ref://",
            "private_csv",
            ".zip",
            ".xlsx",
            ".xls",
            ".pdf",
            ".sqlite",
            ".db",
            "bank_account_number",
            "account_number",
            "identity_document_number",
            "password",
            "token",
            "api_key",
            "private_key",
        ):
            self.assertNotIn(forbidden_text, payload)

    def test_validator_rejects_payroll_or_next_phase_scope_and_raw_fields(self) -> None:
        manifest, fact_rows, review_items = build_default_performance_review_list_artifacts(
            generated_at="2026-07-01T23:45:00+10:00"
        )

        broken_manifest = dict(manifest)
        broken_manifest["quality_gate"] = dict(manifest["quality_gate"])
        broken_manifest["quality_gate"]["salary_calculation_allowed"] = True
        with self.assertRaises(PerformanceReviewListError):
            validate_performance_review_list_artifacts(broken_manifest, fact_rows, review_items)

        broken_manifest = dict(manifest)
        broken_manifest["quality_gate"] = dict(manifest["quality_gate"])
        broken_manifest["quality_gate"]["bonus_approval_allowed"] = True
        with self.assertRaises(PerformanceReviewListError):
            validate_performance_review_list_artifacts(broken_manifest, fact_rows, review_items)

        broken_manifest = dict(manifest)
        broken_manifest["stage_scope"] = dict(manifest["stage_scope"])
        broken_manifest["stage_scope"]["s15_p3_salary_boundary_scope_included"] = True
        with self.assertRaises(PerformanceReviewListError):
            validate_performance_review_list_artifacts(broken_manifest, fact_rows, review_items)

        broken_rows = [dict(row) for row in fact_rows]
        broken_rows[0]["raw_value"] = "123"
        with self.assertRaises(PerformanceReviewListError):
            validate_performance_review_list_artifacts(manifest, broken_rows, review_items)


if __name__ == "__main__":
    unittest.main()
