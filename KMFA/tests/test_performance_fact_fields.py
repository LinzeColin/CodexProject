import json
import unittest

from KMFA.tools.performance_fact_fields import (
    PerformanceFactFieldError,
    REQUIRED_PERFORMANCE_FACT_FIELDS,
    REQUIRED_MANUAL_REVIEW_FIELDS,
    build_default_performance_fact_field_artifacts,
    validate_performance_fact_field_artifacts,
)


class PerformanceFactFieldTests(unittest.TestCase):
    def test_default_runtime_covers_s15_p1_required_scope(self) -> None:
        manifest, field_definitions, field_bindings, manual_review_fields = (
            build_default_performance_fact_field_artifacts(generated_at="2026-07-01T23:30:00+10:00")
        )
        validate_performance_fact_field_artifacts(
            manifest,
            field_definitions,
            field_bindings,
            manual_review_fields,
        )

        self.assertEqual(manifest["stage_phase"], "S15-P1")
        self.assertEqual(tuple(manifest["required_performance_fact_fields"]), REQUIRED_PERFORMANCE_FACT_FIELDS)
        self.assertEqual(tuple(manifest["required_manual_review_fields"]), REQUIRED_MANUAL_REVIEW_FIELDS)
        self.assertEqual(manifest["summary"]["field_definition_count"], 6)
        self.assertEqual(manifest["summary"]["field_binding_count"], 6)
        self.assertEqual(manifest["summary"]["manual_review_field_count"], 4)
        self.assertEqual(manifest["summary"]["performance_fact_table_count"], 0)
        self.assertEqual(manifest["summary"]["salary_calculation_count"], 0)
        self.assertEqual(manifest["summary"]["bonus_approval_count"], 0)
        self.assertFalse(manifest["quality_gate"]["performance_fact_table_output_allowed"])
        self.assertFalse(manifest["quality_gate"]["salary_calculation_allowed"])
        self.assertFalse(manifest["quality_gate"]["bonus_approval_allowed"])
        self.assertFalse(manifest["quality_gate"]["payroll_export_allowed"])
        self.assertFalse(manifest["stage_scope"]["s15_p2_review_list_scope_included"])
        self.assertFalse(manifest["stage_scope"]["s15_p3_salary_boundary_scope_included"])
        self.assertFalse(manifest["stage_scope"]["stage15_review_scope_included"])
        self.assertFalse(manifest["stage_scope"]["github_upload_scope_included"])

    def test_bindings_tie_required_fields_to_cost_collection_invoice_and_audit_sources(self) -> None:
        manifest, field_definitions, field_bindings, manual_review_fields = (
            build_default_performance_fact_field_artifacts(generated_at="2026-07-01T23:30:00+10:00")
        )
        validate_performance_fact_field_artifacts(
            manifest,
            field_definitions,
            field_bindings,
            manual_review_fields,
        )

        bindings_by_key = {binding["field_key"]: binding for binding in field_bindings}
        self.assertEqual(set(bindings_by_key), set(REQUIRED_PERFORMANCE_FACT_FIELDS))

        for binding in field_bindings:
            self.assertEqual(binding["record_type"], "performance_fact_field_binding")
            self.assertEqual(
                binding["project_cost_fact_binding"]["artifact_ref"],
                "KMFA/metadata/lineage/project_cost_fact_records.jsonl",
            )
            self.assertEqual(
                binding["collection_fact_binding"]["artifact_ref"],
                "KMFA/metadata/reports/collection_receivable_aging_priority_items.jsonl",
            )
            self.assertFalse(binding["raw_business_values_allowed"])
            self.assertFalse(binding["public_numeric_values_allowed"])
            self.assertFalse(binding["field_plaintext_allowed"])
            self.assertFalse(binding["salary_calculation_allowed"])
            self.assertFalse(binding["bonus_approval_allowed"])
            self.assertFalse(binding["payroll_export_allowed"])

        self.assertIn(
            "KMFA/metadata/reports/invoice_tax_plan_manifest.json",
            bindings_by_key["invoice_amount"]["source_artifact_refs"],
        )
        self.assertIn(
            "KMFA/metadata/reports/project_margin_cash_margin_manifest.json",
            bindings_by_key["gross_margin_rate"]["source_artifact_refs"],
        )
        self.assertIn(
            "KMFA/metadata/reports/collection_receivable_aging_manifest.json",
            bindings_by_key["settlement_speed"]["source_artifact_refs"],
        )
        self.assertIn(
            "KMFA/metadata/reports/collection_receivable_aging_manifest.json",
            bindings_by_key["collection_speed"]["source_artifact_refs"],
        )
        self.assertIn(
            "KMFA/metadata/reports/cross_table_review_manifest.json",
            bindings_by_key["audit_variance"]["source_artifact_refs"],
        )

    def test_missing_or_unlocked_fields_are_marked_for_manual_review(self) -> None:
        manifest, field_definitions, field_bindings, manual_review_fields = (
            build_default_performance_fact_field_artifacts(generated_at="2026-07-01T23:30:00+10:00")
        )
        validate_performance_fact_field_artifacts(
            manifest,
            field_definitions,
            field_bindings,
            manual_review_fields,
        )

        manual_by_key = {item["field_key"]: item for item in manual_review_fields}
        self.assertEqual(set(manual_by_key), set(REQUIRED_MANUAL_REVIEW_FIELDS))
        for field_key in REQUIRED_MANUAL_REVIEW_FIELDS:
            self.assertTrue(manual_by_key[field_key]["manual_review_required"])
            self.assertEqual(manual_by_key[field_key]["review_mode"], "owner_or_authorized_delegate_review_only")
            self.assertFalse(manual_by_key[field_key]["auto_fill_allowed"])
            self.assertFalse(manual_by_key[field_key]["salary_or_bonus_action_allowed"])

        bindings_by_key = {binding["field_key"]: binding for binding in field_bindings}
        for field_key in REQUIRED_MANUAL_REVIEW_FIELDS:
            self.assertTrue(bindings_by_key[field_key]["manual_review_required"])
            self.assertEqual(
                bindings_by_key[field_key]["manual_review_ref"],
                f"KMFA/metadata/reports/performance_fact_manual_review_fields.jsonl#{field_key}",
            )

        self.assertFalse(bindings_by_key["invoice_amount"]["manual_review_required"])
        self.assertFalse(bindings_by_key["gross_margin_rate"]["manual_review_required"])

    def test_public_payload_has_no_raw_values_private_refs_files_or_credentials(self) -> None:
        manifest, field_definitions, field_bindings, manual_review_fields = (
            build_default_performance_fact_field_artifacts(generated_at="2026-07-01T23:30:00+10:00")
        )
        payload = json.dumps(
            [manifest, field_definitions, field_bindings, manual_review_fields],
            ensure_ascii=False,
            sort_keys=True,
        )

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

    def test_validator_rejects_review_list_salary_bonus_or_unmarked_missing_fields(self) -> None:
        manifest, field_definitions, field_bindings, manual_review_fields = (
            build_default_performance_fact_field_artifacts(generated_at="2026-07-01T23:30:00+10:00")
        )

        broken_manifest = dict(manifest)
        broken_manifest["quality_gate"] = dict(manifest["quality_gate"])
        broken_manifest["quality_gate"]["salary_calculation_allowed"] = True
        with self.assertRaises(PerformanceFactFieldError):
            validate_performance_fact_field_artifacts(
                broken_manifest, field_definitions, field_bindings, manual_review_fields
            )

        broken_manifest = dict(manifest)
        broken_manifest["quality_gate"] = dict(manifest["quality_gate"])
        broken_manifest["quality_gate"]["bonus_approval_allowed"] = True
        with self.assertRaises(PerformanceFactFieldError):
            validate_performance_fact_field_artifacts(
                broken_manifest, field_definitions, field_bindings, manual_review_fields
            )

        broken_manifest = dict(manifest)
        broken_manifest["stage_scope"] = dict(manifest["stage_scope"])
        broken_manifest["stage_scope"]["s15_p2_review_list_scope_included"] = True
        with self.assertRaises(PerformanceFactFieldError):
            validate_performance_fact_field_artifacts(
                broken_manifest, field_definitions, field_bindings, manual_review_fields
            )

        broken_bindings = [dict(item) for item in field_bindings]
        for item in broken_bindings:
            if item["field_key"] == "customer_relationship_rate":
                item["manual_review_required"] = False
        with self.assertRaises(PerformanceFactFieldError):
            validate_performance_fact_field_artifacts(
                manifest, field_definitions, broken_bindings, manual_review_fields
            )


if __name__ == "__main__":
    unittest.main()
