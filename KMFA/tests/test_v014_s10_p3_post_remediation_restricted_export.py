from __future__ import annotations

import csv
import importlib
import io
import unittest


class TestV014S10P3PostRemediationRestrictedExport(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.import_error = None
        try:
            phase = importlib.import_module("KMFA.tools.v014_s10_p3_post_remediation_restricted_export")
            validator = importlib.import_module(
                "KMFA.tools.check_v014_s10_p3_post_remediation_restricted_export"
            )
        except ModuleNotFoundError as exc:
            cls.import_error = exc
            return
        cls.payloads = phase.build_payloads()
        cls.manifest = validator.validate_payloads(cls.payloads)

    def setUp(self) -> None:
        if self.import_error is not None and self._testMethodName != "test_phase_implementation_is_available":
            self.skipTest("implementation availability is covered by the RED assertion")

    def test_phase_implementation_is_available(self) -> None:
        self.assertIsNone(
            self.import_error,
            "S10-P3 post-remediation restricted export is not implemented",
        )

    def test_current_state_replaces_stale_historical_export_state(self) -> None:
        summary = self.manifest["summary"]

        self.assertEqual(summary["report_export_record_count"], 2)
        self.assertEqual(summary["grade_distribution"], {"D": 2})
        self.assertEqual(summary["current_data_quality_grade"], "Q4")
        self.assertEqual(summary["current_report_grade"], "D")
        self.assertEqual(summary["open_final_difference_accepted_count"], 3)
        self.assertEqual(summary["nonzero_delta_reconciliation_count"], 9)
        self.assertEqual(summary["zero_delta_reconciliation_count"], 2)
        self.assertEqual(summary["incomplete_reconciliation_count"], 1)
        self.assertEqual(summary["hard_block_count"], 12)
        self.assertNotIn("pending_reconciliation_count", summary)

    def test_required_export_formats_are_restricted_and_public_safe(self) -> None:
        summary = self.manifest["summary"]
        policy = self.manifest["export_policy"]

        self.assertEqual(summary["html_restricted_preview_count"], 2)
        self.assertEqual(summary["csv_restricted_appendix_count"], 2)
        self.assertEqual(summary["excel_compatible_csv_download_count"], 2)
        self.assertEqual(summary["committed_pdf_file_count"], 0)
        self.assertEqual(summary["committed_excel_workbook_count"], 0)
        self.assertEqual(summary["formal_report_count"], 0)
        self.assertEqual(summary["business_decision_basis_allowed_count"], 0)
        self.assertTrue(policy["html_restricted_preview_allowed"])
        self.assertTrue(policy["csv_restricted_appendix_allowed"])
        self.assertTrue(policy["excel_compatible_csv_download_allowed"])
        self.assertEqual(policy["excel_download_mode"], "excel_compatible_csv_no_workbook")
        self.assertTrue(policy["pdf_private_runtime_policy_available"])
        self.assertFalse(policy["pdf_export_performed"])
        self.assertFalse(policy["formal_report_export_allowed"])

    def test_export_records_propagate_d_grade_and_complete_version_chain(self) -> None:
        records = self.manifest["export_records"]
        version_fields = (
            "report_export_version",
            "report_entry_version",
            "report_grade_record_version",
            "template_version",
            "formula_version",
            "mapping_version",
            "field_mapping_version",
            "html_template_version",
            "csv_appendix_schema_version",
            "pdf_export_policy_version",
        )

        self.assertEqual(len(records), 2)
        for record in records:
            self.assertEqual(record["report_grade"], "D")
            self.assertEqual(record["visible_status_label"], "D级（未放行）")
            self.assertEqual(record["export_mode"], "restricted_internal_review_preview")
            self.assertEqual(len(record["hard_blocks"]), 6)
            self.assertTrue(record["restricted_preview_export_allowed"])
            self.assertFalse(record["complete_trusted_report_display_allowed"])
            self.assertFalse(record["formal_report_allowed"])
            self.assertFalse(record["business_decision_basis_allowed"])
            for field in version_fields:
                self.assertTrue(record[field], f"missing version field: {field}")

    def test_html_exports_show_limits_before_any_report_sections(self) -> None:
        outputs = self.payloads["html_outputs"]

        self.assertEqual(set(outputs), {"project_cost_special_report", "business_overview_report"})
        for html_text in outputs.values():
            self.assertTrue(html_text.startswith("<!doctype html>"))
            for token in (
                "D级",
                "未放行",
                "仅供内部复核",
                "关键现金数据缺失",
                "九项非零差异",
                "一项比较未完成",
                "下载CSV附表",
                "PDF导出未执行",
            ):
                self.assertIn(token, html_text)
            self.assertLess(html_text.index("D级"), html_text.index("报告章节"))
            self.assertNotIn("B级", html_text)
            self.assertNotIn("报告等级 B", html_text)
            for token in ("validator", "manifest", "metadata", "source_ref", "S10-P3"):
                self.assertNotIn(token, html_text)

    def test_csv_exports_use_chinese_headers_and_only_aggregate_status(self) -> None:
        expected_headers = [
            "报告名称",
            "报告等级",
            "发布状态",
            "最终接受未决数",
            "非零差异数",
            "零差异数",
            "未完成比较数",
            "使用限制",
        ]
        outputs = self.payloads["csv_outputs"]

        self.assertEqual(len(outputs), 2)
        for csv_text in outputs.values():
            self.assertTrue(csv_text.startswith("\ufeff"))
            reader = csv.DictReader(io.StringIO(csv_text.lstrip("\ufeff")))
            self.assertEqual(reader.fieldnames, expected_headers)
            rows = list(reader)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["报告等级"], "D级")
            self.assertEqual(rows[0]["发布状态"], "未放行")
            self.assertEqual(rows[0]["最终接受未决数"], "3")
            self.assertEqual(rows[0]["非零差异数"], "9")
            self.assertEqual(rows[0]["零差异数"], "2")
            self.assertEqual(rows[0]["未完成比较数"], "1")
            self.assertIn("仅供内部复核", rows[0]["使用限制"])
            for token in ("template_id", "source_ref", "validator", "manifest"):
                self.assertNotIn(token, csv_text)

    def test_current_dependencies_and_downstream_boundaries_are_explicit(self) -> None:
        dependencies = self.manifest["dependencies"]
        boundaries = self.manifest["phase_boundaries"]
        summary = self.manifest["summary"]

        self.assertTrue(dependencies["current_s10_p1_entry_validated"])
        self.assertTrue(dependencies["current_s10_p2_grade_lock_validated"])
        self.assertTrue(dependencies["historical_s10_p3_export_framework_validated"])
        self.assertTrue(dependencies["human_flow_baseline_validated"])
        self.assertFalse(dependencies["historical_dynamic_state_reused"])
        self.assertTrue(boundaries["s10_p3_performed"])
        self.assertFalse(boundaries["stage10_review_performed"])
        self.assertFalse(boundaries["github_upload_performed"])
        self.assertFalse(boundaries["app_reinstall_performed"])
        self.assertFalse(boundaries["business_execution_performed"])
        self.assertEqual(summary["raw_source_file_count"], 5)
        self.assertTrue(summary["raw_snapshot_exact_match"])
        self.assertTrue(summary["raw_cross_phase_snapshot_exact_match"])


if __name__ == "__main__":
    unittest.main()
