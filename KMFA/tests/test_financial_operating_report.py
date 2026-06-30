import json
import unittest

from KMFA.tools.financial_operating_report import (
    REPORT_SECTION_TITLES,
    REQUIRED_DRAFT_IDS,
    REQUIRED_SOURCE_LANES,
    FinancialOperatingReportError,
    build_default_financial_operating_report_artifacts,
    validate_financial_operating_report_artifacts,
)


class FinancialOperatingReportTests(unittest.TestCase):
    def test_default_runtime_covers_s13_p1_required_scope(self) -> None:
        manifest, source_lanes, drafts, html_outputs = build_default_financial_operating_report_artifacts(
            generated_at="2026-07-01T17:00:00+10:00"
        )
        validate_financial_operating_report_artifacts(manifest, source_lanes, drafts, html_outputs)

        self.assertEqual(manifest["stage_phase"], "S13-P1")
        self.assertEqual(tuple(manifest["required_source_lanes"]), REQUIRED_SOURCE_LANES)
        self.assertEqual(tuple(manifest["required_draft_ids"]), REQUIRED_DRAFT_IDS)
        self.assertEqual(tuple(manifest["required_section_titles"]), REPORT_SECTION_TITLES)
        self.assertEqual(manifest["summary"]["source_lane_count"], 4)
        self.assertEqual(manifest["summary"]["draft_report_count"], 2)
        self.assertEqual(manifest["summary"]["html_draft_count"], 2)
        self.assertEqual(manifest["summary"]["pending_reconciliation_count"], 12)
        self.assertEqual(manifest["summary"]["report_grade_visible"], "D")
        self.assertFalse(manifest["quality_gate"]["formal_report_allowed"])
        self.assertFalse(manifest["quality_gate"]["business_decision_basis_allowed"])
        self.assertFalse(manifest["quality_gate"]["s13_p2_allowed"])
        self.assertFalse(manifest["quality_gate"]["s13_p3_allowed"])
        self.assertFalse(manifest["stage_scope"]["stage13_review_scope_included"])
        self.assertFalse(manifest["stage_scope"]["github_upload_scope_included"])

    def test_source_lanes_cover_operating_expense_cash_and_loan_inputs(self) -> None:
        manifest, source_lanes, drafts, html_outputs = build_default_financial_operating_report_artifacts(
            generated_at="2026-07-01T17:00:00+10:00"
        )
        validate_financial_operating_report_artifacts(manifest, source_lanes, drafts, html_outputs)

        lane_by_id = {lane["lane_id"]: lane for lane in source_lanes}
        self.assertEqual(set(lane_by_id), set(REQUIRED_SOURCE_LANES))
        self.assertEqual(lane_by_id["operating_situation"]["finance_categories"], ["operating_analysis"])
        self.assertEqual(
            lane_by_id["expense_tax_asset"]["finance_categories"],
            ["journal", "tax", "account", "r_and_d_expense"],
        )
        self.assertEqual(lane_by_id["cash_situation"]["finance_categories"], ["cash", "account"])
        self.assertEqual(lane_by_id["loan_detail"]["finance_categories"], ["loan"])

        for lane in source_lanes:
            self.assertEqual(lane["record_type"], "financial_operating_source_lane")
            self.assertGreaterEqual(lane["source_count"], 1)
            self.assertGreaterEqual(lane["field_mapping_count"], 5)
            self.assertTrue(lane["all_sources_readonly"])
            self.assertFalse(lane["raw_business_values_allowed"])
            self.assertFalse(lane["public_amount_values_allowed"])
            self.assertFalse(lane["field_plaintext_allowed"])
            self.assertFalse(lane["formal_report_allowed"])
            self.assertFalse(lane["business_decision_basis_allowed"])

    def test_weekly_and_monthly_drafts_show_status_and_limitations(self) -> None:
        manifest, source_lanes, drafts, html_outputs = build_default_financial_operating_report_artifacts(
            generated_at="2026-07-01T17:00:00+10:00"
        )
        validate_financial_operating_report_artifacts(manifest, source_lanes, drafts, html_outputs)

        for draft in drafts:
            self.assertEqual(draft["record_type"], "financial_operating_report_draft")
            self.assertTrue(draft["draft_report_allowed"])
            self.assertEqual(draft["report_grade_visible"], "D")
            self.assertEqual(tuple(draft["visible_section_titles"]), REPORT_SECTION_TITLES)
            self.assertEqual(len(draft["data_status_cards"]), len(REQUIRED_SOURCE_LANES))
            self.assertFalse(draft["formal_report_allowed"])
            self.assertFalse(draft["complete_trusted_report_display_allowed"])
            self.assertFalse(draft["business_decision_basis_allowed"])
            self.assertFalse(draft["lineage_full_check_included"])
            self.assertFalse(draft["s13_p2_scope_included"])
            self.assertFalse(draft["s13_p3_scope_included"])
            self.assertFalse(draft["external_connector_included"])
            self.assertFalse(draft["payment_or_bank_operation_allowed"])
            self.assertFalse(draft["tax_filing_allowed"])

    def test_rendered_html_is_public_safe_and_business_readable(self) -> None:
        manifest, source_lanes, drafts, html_outputs = build_default_financial_operating_report_artifacts(
            generated_at="2026-07-01T17:00:00+10:00"
        )
        validate_financial_operating_report_artifacts(manifest, source_lanes, drafts, html_outputs)

        for draft_id, html_text in html_outputs.items():
            self.assertTrue(html_text.startswith("<!doctype html>"))
            self.assertIn('lang="zh-CN"', html_text)
            self.assertIn("KMFA 经营分析系统", html_text)
            self.assertIn("报告等级 D", html_text)
            self.assertIn("不可作为正式经营决策依据", html_text)
            self.assertIn("经营情况", html_text)
            self.assertIn("费用税金资产", html_text)
            self.assertIn("现金情况", html_text)
            self.assertIn("贷款明细", html_text)
            for forbidden_visible in ("source_ref://", "private://", "private_ref://", "validator", "manifest", "metadata"):
                self.assertNotIn(forbidden_visible, html_text.lower())
            for forbidden_suffix in (".zip", ".xlsx", ".xls", ".pdf", ".sqlite", ".db"):
                self.assertNotIn(forbidden_suffix, html_text.lower())

    def test_public_payload_has_no_raw_values_private_refs_or_credentials(self) -> None:
        manifest, source_lanes, drafts, html_outputs = build_default_financial_operating_report_artifacts(
            generated_at="2026-07-01T17:00:00+10:00"
        )
        payload = json.dumps([manifest, source_lanes, drafts, html_outputs], ensure_ascii=False, sort_keys=True)

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
            "identity_document_number",
            "password",
            "token",
            "api_key",
            "private_key",
        ):
            self.assertNotIn(forbidden_text, payload)

    def test_validator_rejects_formal_report_or_s13_p2_scope(self) -> None:
        manifest, source_lanes, drafts, html_outputs = build_default_financial_operating_report_artifacts(
            generated_at="2026-07-01T17:00:00+10:00"
        )

        broken_manifest = dict(manifest)
        broken_manifest["quality_gate"] = dict(manifest["quality_gate"])
        broken_manifest["quality_gate"]["formal_report_allowed"] = True
        with self.assertRaises(FinancialOperatingReportError):
            validate_financial_operating_report_artifacts(broken_manifest, source_lanes, drafts, html_outputs)

        broken_drafts = [dict(drafts[0]), *drafts[1:]]
        broken_drafts[0]["s13_p2_scope_included"] = True
        with self.assertRaises(FinancialOperatingReportError):
            validate_financial_operating_report_artifacts(manifest, source_lanes, broken_drafts, html_outputs)


if __name__ == "__main__":
    unittest.main()
