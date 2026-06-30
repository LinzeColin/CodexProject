import csv
import json
import unittest
from io import StringIO

from KMFA.tools.report_export_runtime import (
    REQUIRED_TEMPLATE_IDS,
    ReportExportRuntimeError,
    build_default_report_export_artifacts,
    validate_report_export_artifacts,
)


class ReportExportRuntimeTests(unittest.TestCase):
    def test_default_runtime_exports_s10_p3_required_reports(self) -> None:
        manifest, records, render_outputs = build_default_report_export_artifacts(
            generated_at="2026-06-30T23:59:55+10:00"
        )
        validate_report_export_artifacts(manifest, records, render_outputs)

        self.assertEqual(manifest["stage_phase"], "S10-P3")
        self.assertEqual(set(manifest["required_template_ids"]), set(REQUIRED_TEMPLATE_IDS))
        self.assertEqual(manifest["summary"]["report_export_record_count"], 2)
        self.assertEqual(manifest["summary"]["html_export_count"], 2)
        self.assertEqual(manifest["summary"]["csv_appendix_count"], 2)
        self.assertEqual(manifest["summary"]["excel_compatible_download_count"], 2)
        self.assertTrue(manifest["summary"]["pdf_export_enabled_after_template_stable"])
        self.assertEqual(manifest["summary"]["committed_pdf_file_count"], 0)
        self.assertEqual(manifest["summary"]["committed_excel_file_count"], 0)
        self.assertFalse(manifest["quality_gate"]["formal_report_allowed"])
        self.assertFalse(manifest["quality_gate"]["business_decision_basis_allowed"])

    def test_export_records_keep_d_grade_release_blocks_visible(self) -> None:
        manifest, records, render_outputs = build_default_report_export_artifacts(
            generated_at="2026-06-30T23:59:55+10:00"
        )
        validate_report_export_artifacts(manifest, records, render_outputs)

        record_by_template = {record["template_id"]: record for record in records}
        self.assertEqual(set(record_by_template), set(REQUIRED_TEMPLATE_IDS))
        for record in records:
            self.assertEqual(record["report_grade"], "D")
            self.assertEqual(record["release_permission"], "blocked_decision_use")
            self.assertFalse(record["complete_trusted_report_display_allowed"])
            self.assertFalse(record["formal_report_allowed"])
            self.assertFalse(record["business_decision_basis_allowed"])
            self.assertEqual(record["export_formats"]["html_report"]["status"], "stable_public_safe")
            self.assertEqual(record["export_formats"]["csv_appendix"]["status"], "downloadable_public_safe")
            self.assertEqual(record["export_formats"]["excel_appendix"]["download_mode"], "excel_compatible_csv")
            self.assertTrue(record["export_formats"]["pdf_report"]["enabled_after_template_stable"])
            self.assertTrue(record["export_formats"]["pdf_report"]["private_runtime_only"])
            self.assertIsNone(record["export_formats"]["pdf_report"]["committed_artifact_path"])

    def test_rendered_html_and_csv_outputs_are_public_safe(self) -> None:
        manifest, records, render_outputs = build_default_report_export_artifacts(
            generated_at="2026-06-30T23:59:55+10:00"
        )
        validate_report_export_artifacts(manifest, records, render_outputs)

        self.assertEqual(set(render_outputs["html"]), set(REQUIRED_TEMPLATE_IDS))
        self.assertEqual(set(render_outputs["csv"]), set(REQUIRED_TEMPLATE_IDS))

        for html_text in render_outputs["html"].values():
            self.assertTrue(html_text.startswith("<!doctype html>"))
            self.assertIn("KMFA 经营分析系统", html_text)
            self.assertIn("报告等级 D", html_text)
            self.assertIn("不可作为正式经营决策依据", html_text)
            self.assertNotIn("source_ref://", html_text)
            self.assertNotIn("validator", html_text.lower())
            self.assertNotIn("manifest", html_text.lower())

        for csv_text in render_outputs["csv"].values():
            reader = csv.DictReader(StringIO(csv_text))
            rows = list(reader)
            self.assertEqual(reader.fieldnames, [
                "report_id",
                "template_id",
                "visible_report_name",
                "report_grade",
                "release_permission",
                "export_notice",
            ])
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["report_grade"], "D")
            self.assertEqual(rows[0]["release_permission"], "blocked_decision_use")

    def test_public_payload_has_no_raw_values_or_private_business_files(self) -> None:
        manifest, records, render_outputs = build_default_report_export_artifacts(
            generated_at="2026-06-30T23:59:55+10:00"
        )
        payload = json.dumps([manifest, records, render_outputs], ensure_ascii=False, sort_keys=True)

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

    def test_validator_rejects_committed_excel_or_pdf_artifacts(self) -> None:
        manifest, records, render_outputs = build_default_report_export_artifacts(
            generated_at="2026-06-30T23:59:55+10:00"
        )
        broken_records = [dict(records[0]), *records[1:]]
        broken_formats = dict(broken_records[0]["export_formats"])
        broken_formats["excel_appendix"] = dict(broken_formats["excel_appendix"])
        broken_formats["excel_appendix"]["committed_artifact_path"] = "KMFA/private.xlsx"
        broken_records[0]["export_formats"] = broken_formats

        with self.assertRaises(ReportExportRuntimeError):
            validate_report_export_artifacts(manifest, broken_records, render_outputs)

    def test_validator_allows_pdf_suffix_in_policy_text_only(self) -> None:
        manifest, records, render_outputs = build_default_report_export_artifacts(
            generated_at="2026-06-30T23:59:55+10:00"
        )
        manifest = dict(manifest)
        manifest["limitations"] = [*manifest["limitations"], "公开仓库不提交 .pdf 文件。"]

        validate_report_export_artifacts(manifest, records, render_outputs)


if __name__ == "__main__":
    unittest.main()
