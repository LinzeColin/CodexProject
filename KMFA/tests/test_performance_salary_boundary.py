import json
import unittest

from KMFA.tools.performance_salary_boundary import (
    REQUIRED_FACT_INTERFACE_FIELDS,
    PerformanceSalaryBoundaryError,
    build_default_performance_salary_boundary_artifacts,
    validate_performance_salary_boundary_artifacts,
)


class PerformanceSalaryBoundaryTests(unittest.TestCase):
    def test_default_runtime_covers_s15_p3_required_scope(self) -> None:
        manifest, interface_contract, readiness_rows = build_default_performance_salary_boundary_artifacts(
            generated_at="2026-07-01T23:55:00+10:00"
        )
        validate_performance_salary_boundary_artifacts(manifest, interface_contract, readiness_rows)

        self.assertEqual(manifest["stage_phase"], "S15-P3")
        self.assertEqual(tuple(interface_contract["fact_interface_fields"]), REQUIRED_FACT_INTERFACE_FIELDS)
        self.assertEqual(manifest["summary"]["fact_interface_contract_count"], 1)
        self.assertEqual(manifest["summary"]["future_salary_system_readiness_row_count"], 4)
        self.assertEqual(manifest["summary"]["human_approval_boundary_count"], 4)
        self.assertTrue(manifest["quality_gate"]["fact_output_interface_reserved"])
        self.assertTrue(manifest["quality_gate"]["future_salary_system_read_draft_allowed"])
        self.assertFalse(manifest["quality_gate"]["live_salary_system_integration_allowed"])
        self.assertFalse(manifest["quality_gate"]["salary_calculation_allowed"])
        self.assertFalse(manifest["quality_gate"]["wage_calculation_allowed"])
        self.assertFalse(manifest["quality_gate"]["bonus_approval_allowed"])
        self.assertFalse(manifest["quality_gate"]["payroll_export_allowed"])
        self.assertTrue(manifest["quality_gate"]["final_approval_must_be_human"])
        self.assertTrue(manifest["quality_gate"]["payment_release_must_be_human"])
        self.assertFalse(manifest["stage_scope"]["stage15_review_scope_included"])
        self.assertFalse(manifest["stage_scope"]["github_upload_scope_included"])

    def test_reserved_fact_output_interface_is_contract_only(self) -> None:
        manifest, interface_contract, readiness_rows = build_default_performance_salary_boundary_artifacts(
            generated_at="2026-07-01T23:55:00+10:00"
        )
        validate_performance_salary_boundary_artifacts(manifest, interface_contract, readiness_rows)

        self.assertEqual(interface_contract["record_type"], "performance_fact_output_interface_contract")
        self.assertEqual(interface_contract["interface_status"], "reserved_contract_only")
        self.assertEqual(interface_contract["source_artifact_ref"], "KMFA/metadata/reports/performance_fact_table.jsonl")
        self.assertEqual(interface_contract["value_policy"], "hash_ref_status_and_evidence_only_no_numeric_payload")
        self.assertFalse(interface_contract["api_endpoint_created"])
        self.assertFalse(interface_contract["file_export_created"])
        self.assertFalse(interface_contract["connector_enabled"])
        self.assertFalse(interface_contract["live_read_enabled"])
        self.assertFalse(interface_contract["automatic_compensation_decision_allowed"])

    def test_future_salary_system_readiness_draft_keeps_human_boundary(self) -> None:
        manifest, interface_contract, readiness_rows = build_default_performance_salary_boundary_artifacts(
            generated_at="2026-07-01T23:55:00+10:00"
        )
        validate_performance_salary_boundary_artifacts(manifest, interface_contract, readiness_rows)

        self.assertEqual(
            [row["readiness_row_id"] for row in readiness_rows],
            ["S15P3-READ-001", "S15P3-READ-002", "S15P3-READ-003", "S15P3-READ-004"],
        )
        for row in readiness_rows:
            self.assertEqual(row["record_type"], "future_salary_system_readiness_draft")
            self.assertEqual(row["stage_phase"], "S15-P3")
            self.assertTrue(row["performance_fact_row_ref"].startswith("KMFA/metadata/reports/performance_fact_table.jsonl#"))
            self.assertTrue(row["project_ref"].startswith("entity_ref://KMFA/S08-P2/project/"))
            self.assertEqual(row["future_read_status"], "draft_only_blocked_until_manual_review_and_human_approval")
            self.assertEqual(set(row["available_fact_fields"]), set(REQUIRED_FACT_INTERFACE_FIELDS))
            self.assertEqual(row["value_policy"], "no_numeric_salary_or_bonus_payload")
            self.assertTrue(row["final_approval_must_be_human"])
            self.assertTrue(row["payment_release_must_be_human"])
            self.assertFalse(row["salary_calculation_allowed"])
            self.assertFalse(row["bonus_approval_allowed"])
            self.assertFalse(row["payroll_export_allowed"])
            self.assertFalse(row["automatic_payment_allowed"])

    def test_public_payload_has_no_raw_values_files_credentials_or_compensation_amounts(self) -> None:
        manifest, interface_contract, readiness_rows = build_default_performance_salary_boundary_artifacts(
            generated_at="2026-07-01T23:55:00+10:00"
        )
        payload = json.dumps([manifest, interface_contract, readiness_rows], ensure_ascii=False, sort_keys=True)

        for forbidden_text in (
            '"amount_cents":',
            '"amount_yuan":',
            "salary_amount",
            "wage_amount",
            "bonus_amount",
            "payroll_amount",
            "employee_name",
            "employee_id",
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

    def test_validator_rejects_live_integration_payroll_export_and_raw_fields(self) -> None:
        manifest, interface_contract, readiness_rows = build_default_performance_salary_boundary_artifacts(
            generated_at="2026-07-01T23:55:00+10:00"
        )

        broken_manifest = dict(manifest)
        broken_manifest["quality_gate"] = dict(manifest["quality_gate"])
        broken_manifest["quality_gate"]["live_salary_system_integration_allowed"] = True
        with self.assertRaises(PerformanceSalaryBoundaryError):
            validate_performance_salary_boundary_artifacts(broken_manifest, interface_contract, readiness_rows)

        broken_contract = dict(interface_contract)
        broken_contract["api_endpoint_created"] = True
        with self.assertRaises(PerformanceSalaryBoundaryError):
            validate_performance_salary_boundary_artifacts(manifest, broken_contract, readiness_rows)

        broken_rows = [dict(row) for row in readiness_rows]
        broken_rows[0]["payroll_export_allowed"] = True
        with self.assertRaises(PerformanceSalaryBoundaryError):
            validate_performance_salary_boundary_artifacts(manifest, interface_contract, broken_rows)

        broken_rows = [dict(row) for row in readiness_rows]
        broken_rows[0]["salary_amount"] = "123"
        with self.assertRaises(PerformanceSalaryBoundaryError):
            validate_performance_salary_boundary_artifacts(manifest, interface_contract, broken_rows)


if __name__ == "__main__":
    unittest.main()
