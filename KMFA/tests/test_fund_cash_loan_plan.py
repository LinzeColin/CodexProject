import json
import unittest

from KMFA.tools.fund_cash_loan_plan import (
    FundCashLoanPlanError,
    REQUIRED_OUTPUT_RECORD_TYPES,
    REQUIRED_SOURCE_LANES,
    build_default_fund_cash_loan_plan_artifacts,
    validate_fund_cash_loan_plan_artifacts,
)


class FundCashLoanPlanTests(unittest.TestCase):
    def test_default_runtime_covers_s14_p1_required_scope(self) -> None:
        manifest, source_lanes, cash_pressure, loan_due_alerts, account_summaries, html_outputs = (
            build_default_fund_cash_loan_plan_artifacts(generated_at="2026-07-01T22:00:00+10:00")
        )
        validate_fund_cash_loan_plan_artifacts(
            manifest,
            source_lanes,
            cash_pressure,
            loan_due_alerts,
            account_summaries,
            html_outputs,
        )

        self.assertEqual(manifest["stage_phase"], "S14-P1")
        self.assertEqual(tuple(manifest["required_source_lanes"]), REQUIRED_SOURCE_LANES)
        self.assertEqual(tuple(manifest["required_output_record_types"]), REQUIRED_OUTPUT_RECORD_TYPES)
        self.assertEqual(manifest["summary"]["source_lane_count"], 4)
        self.assertEqual(manifest["summary"]["cash_pressure_record_count"], 4)
        self.assertEqual(manifest["summary"]["loan_due_alert_count"], 3)
        self.assertEqual(manifest["summary"]["account_balance_summary_count"], 3)
        self.assertEqual(manifest["summary"]["report_grade_visible"], "D")
        self.assertFalse(manifest["quality_gate"]["formal_report_allowed"])
        self.assertFalse(manifest["quality_gate"]["payment_approval_allowed"])
        self.assertFalse(manifest["quality_gate"]["bank_operation_allowed"])
        self.assertFalse(manifest["quality_gate"]["loan_management_action_allowed"])
        self.assertFalse(manifest["stage_scope"]["s14_p2_scope_included"])
        self.assertFalse(manifest["stage_scope"]["s14_p3_scope_included"])
        self.assertFalse(manifest["stage_scope"]["stage14_review_scope_included"])
        self.assertFalse(manifest["stage_scope"]["github_upload_scope_included"])

    def test_source_lanes_cover_account_monthly_cash_fund_plan_and_loan_detail(self) -> None:
        manifest, source_lanes, cash_pressure, loan_due_alerts, account_summaries, html_outputs = (
            build_default_fund_cash_loan_plan_artifacts(generated_at="2026-07-01T22:00:00+10:00")
        )
        validate_fund_cash_loan_plan_artifacts(
            manifest,
            source_lanes,
            cash_pressure,
            loan_due_alerts,
            account_summaries,
            html_outputs,
        )

        lane_by_id = {lane["lane_id"]: lane for lane in source_lanes}
        self.assertEqual(set(lane_by_id), set(REQUIRED_SOURCE_LANES))
        self.assertEqual(lane_by_id["account_list"]["finance_categories"], ["account"])
        self.assertEqual(lane_by_id["monthly_cash"]["finance_categories"], ["cash"])
        self.assertEqual(lane_by_id["fund_plan"]["finance_categories"], ["cash", "journal"])
        self.assertEqual(lane_by_id["loan_detail"]["finance_categories"], ["loan"])

        for lane in source_lanes:
            self.assertEqual(lane["record_type"], "fund_cash_loan_source_lane")
            self.assertGreaterEqual(lane["source_count"], 1)
            self.assertGreaterEqual(lane["field_mapping_count"], 5)
            self.assertTrue(lane["all_sources_readonly"])
            self.assertFalse(lane["raw_business_values_allowed"])
            self.assertFalse(lane["public_amount_values_allowed"])
            self.assertFalse(lane["field_plaintext_allowed"])
            self.assertFalse(lane["payment_approval_allowed"])
            self.assertFalse(lane["bank_operation_allowed"])

    def test_cash_pressure_loan_due_and_account_summary_outputs_are_public_safe(self) -> None:
        manifest, source_lanes, cash_pressure, loan_due_alerts, account_summaries, html_outputs = (
            build_default_fund_cash_loan_plan_artifacts(generated_at="2026-07-01T22:00:00+10:00")
        )
        validate_fund_cash_loan_plan_artifacts(
            manifest,
            source_lanes,
            cash_pressure,
            loan_due_alerts,
            account_summaries,
            html_outputs,
        )

        self.assertEqual([row["pressure_window"] for row in cash_pressure], ["current_week", "four_week", "eight_week", "twelve_week"])
        self.assertEqual({row["record_type"] for row in cash_pressure}, {"cash_pressure_signal"})
        self.assertEqual({row["record_type"] for row in loan_due_alerts}, {"loan_due_alert"})
        self.assertEqual({row["record_type"] for row in account_summaries}, {"account_balance_summary"})

        for row in [*cash_pressure, *loan_due_alerts, *account_summaries]:
            self.assertEqual(row["stage_phase"], "S14-P1")
            self.assertFalse(row["formal_report_allowed"])
            self.assertFalse(row["business_decision_basis_allowed"])
            self.assertFalse(row["payment_approval_allowed"])
            self.assertFalse(row["bank_operation_allowed"])
            self.assertFalse(row["contains_true_amounts"])
            self.assertFalse(row["contains_account_identifiers"])

    def test_rendered_html_is_business_readable_and_does_not_trigger_operations(self) -> None:
        manifest, source_lanes, cash_pressure, loan_due_alerts, account_summaries, html_outputs = (
            build_default_fund_cash_loan_plan_artifacts(generated_at="2026-07-01T22:00:00+10:00")
        )
        validate_fund_cash_loan_plan_artifacts(
            manifest,
            source_lanes,
            cash_pressure,
            loan_due_alerts,
            account_summaries,
            html_outputs,
        )

        html_text = html_outputs["fund_cash_loan_plan_overview"]
        self.assertTrue(html_text.startswith("<!doctype html>"))
        self.assertIn('lang="zh-CN"', html_text)
        self.assertIn("KMFA 资金计划现金贷款", html_text)
        self.assertIn("现金压力", html_text)
        self.assertIn("贷款到期", html_text)
        self.assertIn("账户余额汇总", html_text)
        self.assertIn("不做付款审批和银行操作", html_text)
        self.assertIn("报告等级 D", html_text)
        for forbidden_visible in ("source_ref://", "private://", "private_ref://", "validator", "manifest", "metadata"):
            self.assertNotIn(forbidden_visible, html_text.lower())
        for forbidden_suffix in (".zip", ".xlsx", ".xls", ".pdf", ".sqlite", ".db"):
            self.assertNotIn(forbidden_suffix, html_text.lower())

    def test_public_payload_has_no_raw_values_private_refs_or_credentials(self) -> None:
        manifest, source_lanes, cash_pressure, loan_due_alerts, account_summaries, html_outputs = (
            build_default_fund_cash_loan_plan_artifacts(generated_at="2026-07-01T22:00:00+10:00")
        )
        payload = json.dumps(
            [manifest, source_lanes, cash_pressure, loan_due_alerts, account_summaries, html_outputs],
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

    def test_validator_rejects_payment_or_s14_p2_scope(self) -> None:
        manifest, source_lanes, cash_pressure, loan_due_alerts, account_summaries, html_outputs = (
            build_default_fund_cash_loan_plan_artifacts(generated_at="2026-07-01T22:00:00+10:00")
        )

        broken_manifest = dict(manifest)
        broken_manifest["quality_gate"] = dict(manifest["quality_gate"])
        broken_manifest["quality_gate"]["payment_approval_allowed"] = True
        with self.assertRaises(FundCashLoanPlanError):
            validate_fund_cash_loan_plan_artifacts(
                broken_manifest,
                source_lanes,
                cash_pressure,
                loan_due_alerts,
                account_summaries,
                html_outputs,
            )

        broken_manifest = dict(manifest)
        broken_manifest["stage_scope"] = dict(manifest["stage_scope"])
        broken_manifest["stage_scope"]["s14_p2_scope_included"] = True
        with self.assertRaises(FundCashLoanPlanError):
            validate_fund_cash_loan_plan_artifacts(
                broken_manifest,
                source_lanes,
                cash_pressure,
                loan_due_alerts,
                account_summaries,
                html_outputs,
            )


if __name__ == "__main__":
    unittest.main()
