from __future__ import annotations

import unittest

from pfi_v02.stage2_contracts import (
    build_abc_bullion_non_csv_contract,
    build_alipay_fund_non_csv_contract,
    build_moomoo_read_only_contract,
    build_stage2_contract_summary,
    build_wechat_contract,
    default_cn_broker_profile,
    probe_moomoo_opend_contract,
    reconcile_abc_triangle,
    reconcile_alipay_fund_triangle,
    select_cn_broker_acquisition,
)


class Stage2NonCsvContractsTest(unittest.TestCase):
    def test_alipay_fund_contract_uses_transaction_holding_nav_triangle_without_csv_assumption(self) -> None:
        contract = build_alipay_fund_non_csv_contract()

        self.assertFalse(contract["csv_assumption"])
        self.assertIn("fund_transaction_line", contract["transaction_line"])
        self.assertIn("fund_page_read", contract["holding_line"])
        self.assertIn("external_nav_source", contract["nav_line"])
        self.assertIn("external_nav_does_not_replace_owner_transactions", contract["rules"])

    def test_alipay_fund_reconciliation_does_not_mark_missing_or_mismatched_inputs_successful(self) -> None:
        missing = reconcile_alipay_fund_triangle(
            transaction_refs=("txn_fund_1",),
            holding_snapshot_refs=(),
            nav_snapshot_refs=("nav_1",),
            expected_market_value=1000.0,
            observed_market_value=1000.0,
        )
        mismatch = reconcile_alipay_fund_triangle(
            transaction_refs=("txn_fund_1",),
            holding_snapshot_refs=("holding_1",),
            nav_snapshot_refs=("nav_1",),
            expected_market_value=1000.0,
            observed_market_value=1125.0,
        )
        matched = reconcile_alipay_fund_triangle(
            transaction_refs=("txn_fund_1",),
            holding_snapshot_refs=("holding_1",),
            nav_snapshot_refs=("nav_1",),
            expected_market_value=1000.0,
            observed_market_value=1005.0,
        )

        self.assertEqual(missing.status, "NEEDS_REVIEW")
        self.assertTrue(missing.requires_review)
        self.assertEqual(mismatch.status, "MISMATCH")
        self.assertTrue(mismatch.requires_review)
        self.assertEqual(matched.status, "MATCHED")
        self.assertFalse(matched.requires_review)

    def test_moomoo_read_only_contract_reuses_existing_qbvs_and_never_fabricates_probe_data(self) -> None:
        contract = build_moomoo_read_only_contract()
        probe = probe_moomoo_opend_contract(opend_available=False, sdk_available=False)

        self.assertTrue(contract["reuse_existing_qbvs"])
        self.assertIn("PFI/modules/qbvs_lab/qbvs/datasources.py", contract["existing_runtime_refs"])
        self.assertIn("no_live_order_submission", contract["boundaries"])
        self.assertEqual(probe["status"], "UNAVAILABLE")
        self.assertFalse(probe["can_emit_synthetic_data"])

    def test_cn_broker_profile_supports_non_csv_modes_holdings_fills_fees_and_profile_selection(self) -> None:
        profile = default_cn_broker_profile()
        modes = select_cn_broker_acquisition(profile)

        self.assertIn("CN_BROKER_QMT_READONLY", modes)
        self.assertIn("CN_BROKER_PDF_STATEMENT", modes)
        self.assertIn("CN_BROKER_EXCEL_STATEMENT", modes)
        self.assertIn("commission", profile.trade_fields)
        self.assertIn("stamp_tax", profile.trade_fields)
        self.assertEqual(profile.field_mapping["银证转账"], "TRANSFER")

    def test_abc_bullion_contract_and_triangle_keep_gold_and_silver_as_investment_assets(self) -> None:
        contract = build_abc_bullion_non_csv_contract()
        missing = reconcile_abc_triangle(statement_refs=("abc_stmt",), bank_payment_refs=(), valuation_refs=("gold_nav",))
        matched = reconcile_abc_triangle(statement_refs=("abc_stmt",), bank_payment_refs=("cba_payment",), valuation_refs=("gold_nav",))

        self.assertFalse(contract["csv_required"])
        self.assertIn("ABC_TRANSACTION_STATEMENT_PDF", contract["acquisition_modes"])
        self.assertIn("gold_silver_buy_is_buy_asset_not_consumption", contract["rules"])
        self.assertEqual(missing.status, "NEEDS_REVIEW")
        self.assertEqual(matched.status, "MATCHED")

    def test_wechat_contract_supports_zip_csv_xls_xlsx_and_transfer_refund_rules(self) -> None:
        contract = build_wechat_contract()

        for expected in ("EMAIL_ZIP", "CSV", "XLS", "XLSX", "WATCH_FOLDER"):
            self.assertIn(expected, contract["file_contracts"])
        self.assertIn("红包", contract["recognized_events"])
        self.assertIn("transfer_not_consumption", contract["rules"])
        self.assertIn("unknown_or_low_confidence_goes_to_review", contract["rules"])

    def test_stage2_contract_summary_covers_all_non_csv_or_external_contracts(self) -> None:
        summary = build_stage2_contract_summary()

        for expected in ("alipay_fund", "moomoo_au", "cn_broker", "abc_bullion", "wechat_pay"):
            self.assertIn(expected, summary)


if __name__ == "__main__":
    unittest.main()
