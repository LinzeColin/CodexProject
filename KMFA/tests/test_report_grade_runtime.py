import json
import unittest

from KMFA.tools.report_grade_runtime import (
    REQUIRED_TEMPLATE_IDS,
    ReportGradeRuntimeError,
    build_default_report_grade_runtime_artifacts,
    validate_report_grade_runtime_artifacts,
)


class ReportGradeRuntimeTests(unittest.TestCase):
    def test_default_runtime_locks_s10_p2_required_reports(self) -> None:
        manifest, records = build_default_report_grade_runtime_artifacts(
            generated_at="2026-06-30T23:59:50+10:00"
        )
        validate_report_grade_runtime_artifacts(manifest, records)

        self.assertEqual(manifest["stage_phase"], "S10-P2")
        self.assertEqual(set(manifest["required_template_ids"]), set(REQUIRED_TEMPLATE_IDS))
        self.assertEqual(manifest["summary"]["report_grade_record_count"], 2)
        self.assertEqual(manifest["summary"]["grade_distribution"], {"D": 2})
        self.assertEqual(manifest["summary"]["pending_reconciliation_count"], 12)
        self.assertEqual(manifest["summary"]["full_trusted_report_allowed_count"], 0)

        record_by_template = {record["template_id"]: record for record in records}
        self.assertEqual(set(record_by_template), set(REQUIRED_TEMPLATE_IDS))
        for record in records:
            self.assertEqual(record["computed_report_grade"], "D")
            self.assertEqual(record["release_permission"], "blocked_decision_use")
            self.assertFalse(record["complete_trusted_report_display_allowed"])
            self.assertFalse(record["formal_report_allowed"])
            self.assertFalse(record["business_decision_basis_allowed"])

    def test_versions_are_bound_per_report_record(self) -> None:
        manifest, records = build_default_report_grade_runtime_artifacts(
            generated_at="2026-06-30T23:59:50+10:00"
        )
        validate_report_grade_runtime_artifacts(manifest, records)

        for record in records:
            self.assertEqual(record["report_record_version"], "RPTREC-KMFA-S10P2-REPORT-GRADE-001")
            self.assertEqual(record["template_version"], manifest["template_version"])
            self.assertEqual(record["formula_version"], manifest["formula_version"])
            self.assertEqual(record["mapping_version"], manifest["mapping_version"])
            self.assertEqual(record["field_mapping_version"], manifest["field_mapping_version"])
            self.assertEqual(record["template_content_hash"], manifest["upstream_template_content_hash"])

    def test_hard_blocks_prevent_complete_trusted_report_display(self) -> None:
        manifest, records = build_default_report_grade_runtime_artifacts(
            generated_at="2026-06-30T23:59:50+10:00"
        )
        validate_report_grade_runtime_artifacts(manifest, records)

        expected_blocks = {
            "zero_delta_failed",
            "unresolved_critical_difference",
            "missing_required_lineage",
            "missing_human_confirmation_for_A",
        }
        for record in records:
            self.assertTrue(expected_blocks.issubset(set(record["hard_blocks"])))
            self.assertEqual(record["grade_inputs"]["source_quality_grade"], "Q4")
            self.assertFalse(record["grade_inputs"]["zero_delta_passed"])
            self.assertEqual(record["grade_inputs"]["unresolved_critical_difference_count"], 12)
            self.assertEqual(record["grade_inputs"]["human_confirmation_status"], "missing")
            self.assertEqual(record["grade_inputs"]["lineage_status"], "missing_required_lineage")

    def test_public_payload_has_no_raw_values_or_private_business_files(self) -> None:
        manifest, records = build_default_report_grade_runtime_artifacts(
            generated_at="2026-06-30T23:59:50+10:00"
        )
        payload = json.dumps([manifest, records], ensure_ascii=False, sort_keys=True)

        for forbidden_text in (
            '"amount_cents":',
            '"amount_yuan":',
            "raw_value",
            "normalized_value",
            "plaintext_value",
            "source_header_text",
            "original_filename",
            "private_csv",
            ".zip",
            ".xlsx",
            ".xls",
            ".pdf",
            ".sqlite",
            "bank_account_number",
            "identity_document_number",
        ):
            self.assertNotIn(forbidden_text, payload)
        self.assertIn("source_ref://", payload)

    def test_validator_rejects_a_grade_when_hard_blocks_exist(self) -> None:
        manifest, records = build_default_report_grade_runtime_artifacts(
            generated_at="2026-06-30T23:59:50+10:00"
        )
        broken_records = [dict(records[0]), *records[1:]]
        broken_records[0]["computed_report_grade"] = "A"
        broken_records[0]["release_permission"] = "formal_internal_report"
        broken_records[0]["complete_trusted_report_display_allowed"] = True
        broken_records[0]["formal_report_allowed"] = True
        broken_records[0]["business_decision_basis_allowed"] = True

        with self.assertRaises(ReportGradeRuntimeError):
            validate_report_grade_runtime_artifacts(manifest, broken_records)


if __name__ == "__main__":
    unittest.main()
