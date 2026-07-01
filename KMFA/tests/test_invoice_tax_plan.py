import json
import unittest

from KMFA.tools.invoice_tax_plan import (
    InvoiceTaxPlanError,
    REQUIRED_ISSUE_CANDIDATE_TYPES,
    REQUIRED_SOURCE_LANES,
    build_default_invoice_tax_plan_artifacts,
    validate_invoice_tax_plan_artifacts,
)


class InvoiceTaxPlanTests(unittest.TestCase):
    def test_default_runtime_covers_s14_p2_required_scope(self) -> None:
        manifest, source_lanes, issue_candidates, cash_summaries, html_outputs = (
            build_default_invoice_tax_plan_artifacts(generated_at="2026-07-01T23:00:00+10:00")
        )
        validate_invoice_tax_plan_artifacts(
            manifest, source_lanes, issue_candidates, cash_summaries, html_outputs
        )

        self.assertEqual(manifest["stage_phase"], "S14-P2")
        self.assertEqual(tuple(manifest["required_source_lanes"]), REQUIRED_SOURCE_LANES)
        self.assertEqual(tuple(manifest["required_issue_candidate_types"]), REQUIRED_ISSUE_CANDIDATE_TYPES)
        self.assertEqual(manifest["summary"]["source_lane_count"], 3)
        self.assertEqual(manifest["summary"]["issue_candidate_count"], 3)
        self.assertEqual(manifest["summary"]["cash_summary_count"], 3)
        self.assertEqual(manifest["summary"]["pending_reconciliation_count"], 12)
        self.assertEqual(manifest["summary"]["report_grade_visible"], "D")
        self.assertFalse(manifest["quality_gate"]["formal_report_allowed"])
        self.assertFalse(manifest["quality_gate"]["business_decision_basis_allowed"])
        self.assertFalse(manifest["quality_gate"]["tax_filing_allowed"])
        self.assertFalse(manifest["quality_gate"]["invoice_issuance_allowed"])
        self.assertFalse(manifest["quality_gate"]["invoice_operation_allowed"])
        self.assertFalse(manifest["stage_scope"]["s14_p3_scope_included"])
        self.assertFalse(manifest["stage_scope"]["stage14_review_scope_included"])
        self.assertFalse(manifest["stage_scope"]["github_upload_scope_included"])

    def test_source_lanes_cover_invoice_tax_and_cash_summary_inputs(self) -> None:
        manifest, source_lanes, issue_candidates, cash_summaries, html_outputs = (
            build_default_invoice_tax_plan_artifacts(generated_at="2026-07-01T23:00:00+10:00")
        )
        validate_invoice_tax_plan_artifacts(
            manifest, source_lanes, issue_candidates, cash_summaries, html_outputs
        )

        lane_by_id = {lane["lane_id"]: lane for lane in source_lanes}
        self.assertEqual(set(lane_by_id), set(REQUIRED_SOURCE_LANES))
        self.assertEqual(lane_by_id["invoice_plan"]["finance_categories"], ["invoice"])
        self.assertEqual(lane_by_id["tax_detail"]["finance_categories"], ["tax"])
        self.assertEqual(
            lane_by_id["invoice_tax_cash_summary"]["finance_categories"],
            ["invoice", "tax", "cash", "journal"],
        )

        for lane in source_lanes:
            self.assertEqual(lane["record_type"], "invoice_tax_source_lane")
            self.assertGreaterEqual(lane["source_count"], 1)
            self.assertGreaterEqual(lane["field_mapping_count"], 5)
            self.assertTrue(lane["all_sources_readonly"])
            self.assertFalse(lane["raw_business_values_allowed"])
            self.assertFalse(lane["public_amount_values_allowed"])
            self.assertFalse(lane["field_plaintext_allowed"])
            self.assertFalse(lane["formal_report_allowed"])
            self.assertFalse(lane["business_decision_basis_allowed"])
            self.assertFalse(lane["tax_filing_allowed"])
            self.assertFalse(lane["invoice_issuance_allowed"])

    def test_issue_candidates_and_cash_summaries_are_public_safe(self) -> None:
        manifest, source_lanes, issue_candidates, cash_summaries, html_outputs = (
            build_default_invoice_tax_plan_artifacts(generated_at="2026-07-01T23:00:00+10:00")
        )
        validate_invoice_tax_plan_artifacts(
            manifest, source_lanes, issue_candidates, cash_summaries, html_outputs
        )

        self.assertEqual({item["issue_type"] for item in issue_candidates}, set(REQUIRED_ISSUE_CANDIDATE_TYPES))
        self.assertEqual(
            [item["issue_candidate_id"] for item in issue_candidates],
            ["S14P2-ISS-001", "S14P2-ISS-002", "S14P2-ISS-003"],
        )
        self.assertEqual(
            [item["cash_summary_bucket"] for item in cash_summaries],
            ["invoice_expected_cash_inflow", "tax_expected_cash_outflow", "invoice_tax_net_pressure"],
        )

        for item in issue_candidates:
            self.assertEqual(item["record_type"], "invoice_tax_issue_candidate")
            self.assertEqual(item["stage_phase"], "S14-P2")
            self.assertFalse(item["raw_business_values_allowed"])
            self.assertFalse(item["public_amount_values_allowed"])
            self.assertFalse(item["field_plaintext_allowed"])
            self.assertFalse(item["invoice_issuance_allowed"])
            self.assertFalse(item["tax_filing_allowed"])
            self.assertFalse(item["business_decision_basis_allowed"])

        for item in cash_summaries:
            self.assertEqual(item["record_type"], "invoice_tax_cash_summary")
            self.assertEqual(item["stage_phase"], "S14-P2")
            self.assertFalse(item["amount_value_display_allowed"])
            self.assertFalse(item["payment_or_bank_operation_allowed"])
            self.assertFalse(item["invoice_issuance_allowed"])
            self.assertFalse(item["tax_filing_allowed"])
            self.assertFalse(item["business_decision_basis_allowed"])

    def test_rendered_html_is_business_readable_and_does_not_trigger_actions(self) -> None:
        manifest, source_lanes, issue_candidates, cash_summaries, html_outputs = (
            build_default_invoice_tax_plan_artifacts(generated_at="2026-07-01T23:00:00+10:00")
        )
        validate_invoice_tax_plan_artifacts(
            manifest, source_lanes, issue_candidates, cash_summaries, html_outputs
        )

        self.assertEqual(set(html_outputs), {"invoice_tax_plan_overview"})
        html_text = html_outputs["invoice_tax_plan_overview"]
        self.assertTrue(html_text.startswith("<!doctype html>"))
        self.assertIn('lang="zh-CN"', html_text)
        self.assertIn("KMFA 开票纳税", html_text)
        self.assertIn("待开票", html_text)
        self.assertIn("已开票未回款", html_text)
        self.assertIn("税率异常候选", html_text)
        self.assertIn("不做纳税申报和发票开具", html_text)
        self.assertIn("报告等级 D", html_text)
        for forbidden_visible in ("source_ref://", "private://", "private_ref://", "validator", "manifest", "metadata"):
            self.assertNotIn(forbidden_visible, html_text.lower())
        for forbidden_suffix in (".zip", ".xlsx", ".xls", ".pdf", ".sqlite", ".db"):
            self.assertNotIn(forbidden_suffix, html_text.lower())

    def test_public_payload_has_no_raw_values_private_refs_or_credentials(self) -> None:
        manifest, source_lanes, issue_candidates, cash_summaries, html_outputs = (
            build_default_invoice_tax_plan_artifacts(generated_at="2026-07-01T23:00:00+10:00")
        )
        payload = json.dumps(
            [manifest, source_lanes, issue_candidates, cash_summaries, html_outputs],
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

    def test_validator_rejects_tax_filing_invoice_issuance_or_s14_p3_scope(self) -> None:
        manifest, source_lanes, issue_candidates, cash_summaries, html_outputs = (
            build_default_invoice_tax_plan_artifacts(generated_at="2026-07-01T23:00:00+10:00")
        )

        broken_manifest = dict(manifest)
        broken_manifest["quality_gate"] = dict(manifest["quality_gate"])
        broken_manifest["quality_gate"]["tax_filing_allowed"] = True
        with self.assertRaises(InvoiceTaxPlanError):
            validate_invoice_tax_plan_artifacts(
                broken_manifest, source_lanes, issue_candidates, cash_summaries, html_outputs
            )

        broken_manifest = dict(manifest)
        broken_manifest["quality_gate"] = dict(manifest["quality_gate"])
        broken_manifest["quality_gate"]["invoice_issuance_allowed"] = True
        with self.assertRaises(InvoiceTaxPlanError):
            validate_invoice_tax_plan_artifacts(
                broken_manifest, source_lanes, issue_candidates, cash_summaries, html_outputs
            )

        broken_manifest = dict(manifest)
        broken_manifest["stage_scope"] = dict(manifest["stage_scope"])
        broken_manifest["stage_scope"]["s14_p3_scope_included"] = True
        with self.assertRaises(InvoiceTaxPlanError):
            validate_invoice_tax_plan_artifacts(
                broken_manifest, source_lanes, issue_candidates, cash_summaries, html_outputs
            )

        broken_candidates = [dict(issue_candidates[0]), *issue_candidates[1:]]
        broken_candidates[0]["invoice_issuance_allowed"] = True
        with self.assertRaises(InvoiceTaxPlanError):
            validate_invoice_tax_plan_artifacts(
                manifest, source_lanes, broken_candidates, cash_summaries, html_outputs
            )


if __name__ == "__main__":
    unittest.main()
