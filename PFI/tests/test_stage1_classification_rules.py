from __future__ import annotations

import unittest

from pfi_v02.classification_rules import (
    ClassificationInput,
    build_ledger_classification_standard,
    classify_transaction,
    stage1_classification_fixtures,
)
from pfi_v02.core_models import AssetType, LedgerEventType


class Stage1ClassificationRulesTest(unittest.TestCase):
    def test_cba_to_moomoo_transfer_is_not_consumption(self) -> None:
        result = classify_transaction(
            ClassificationInput("cba_bank", "CBA transfer to Moomoo brokerage", -5000.0, "AUD", "CBA", "Moomoo AU")
        )

        self.assertEqual(result.event_type, LedgerEventType.TRANSFER)
        self.assertFalse(result.affects_consumption)
        self.assertTrue(result.affects_investment)
        self.assertEqual(result.review_state, "ACCEPTED")

    def test_bank_to_broker_and_alipay_to_bank_transfers_are_not_spending(self) -> None:
        examples = [
            ClassificationInput("cba_bank", "bank transfer to brokerage account", -2500.0, "AUD"),
            ClassificationInput("alipay_daily", "支付宝到银行 转账", -3000.0, "CNY"),
        ]

        for example in examples:
            with self.subTest(example=example.description):
                result = classify_transaction(example)
                self.assertEqual(result.event_type, LedgerEventType.TRANSFER)
                self.assertFalse(result.affects_consumption)

    def test_alipay_fund_subscription_and_redemption_are_investment_events(self) -> None:
        for description, amount in [("支付宝基金申购 易方达基金", -800.0), ("fund redemption received", 900.0)]:
            with self.subTest(description=description):
                result = classify_transaction(ClassificationInput("alipay_daily", description, amount, "CNY"))
                self.assertEqual(result.event_type, LedgerEventType.FUND)
                self.assertFalse(result.affects_consumption)
                self.assertTrue(result.affects_investment)
                self.assertEqual(result.asset_type, AssetType.FUND)

    def test_abc_bullion_gold_or_silver_trade_is_investment_asset_event(self) -> None:
        result = classify_transaction(
            ClassificationInput("abc_bullion", "ABC Bullion gold purchase", -1200.0, "AUD", "ABC Bullion", "Gold")
        )

        self.assertEqual(result.event_type, LedgerEventType.BUY_ASSET)
        self.assertFalse(result.affects_consumption)
        self.assertTrue(result.affects_investment)
        self.assertEqual(result.asset_type, AssetType.BULLION)

    def test_credit_card_repayment_is_not_double_counted_as_consumption(self) -> None:
        result = classify_transaction(
            ClassificationInput("cba_bank", "Credit card repayment from CBA account", -2200.0, "AUD", "CBA", "Credit Card")
        )

        self.assertEqual(result.event_type, LedgerEventType.TRANSFER)
        self.assertFalse(result.affects_consumption)
        self.assertFalse(result.affects_investment)
        self.assertEqual(result.asset_type, AssetType.CREDIT)
        self.assertTrue(result.dedupe_key.startswith("credit_repayment:"))

    def test_default_cash_spending_still_classifies_regular_consumption(self) -> None:
        result = classify_transaction(ClassificationInput("wechat_pay", "coffee shop", -5.5, "AUD"))

        self.assertEqual(result.event_type, LedgerEventType.CASH)
        self.assertTrue(result.affects_consumption)
        self.assertFalse(result.affects_investment)

    def test_stage1_fixtures_cover_all_required_rule_groups(self) -> None:
        results = [classify_transaction(item) for item in stage1_classification_fixtures()]

        self.assertEqual(len(results), 4)
        self.assertIn(LedgerEventType.TRANSFER, [result.event_type for result in results])
        self.assertIn(LedgerEventType.FUND, [result.event_type for result in results])
        self.assertIn(LedgerEventType.BUY_ASSET, [result.event_type for result in results])
        self.assertEqual(sum(1 for result in results if result.affects_consumption), 0)

    def test_ledger_classification_standard_documents_priority_and_effects(self) -> None:
        standard = build_ledger_classification_standard()
        rule_ids = [rule["rule_id"] for rule in standard]
        priorities = [rule["priority"] for rule in standard]
        by_id = {rule["rule_id"]: rule for rule in standard}

        self.assertEqual(rule_ids, ["LCS-001", "LCS-002", "LCS-003", "LCS-004", "LCS-005"])
        self.assertEqual(priorities, sorted(priorities))
        self.assertFalse(by_id["LCS-001"]["affects_consumption"])
        self.assertTrue(by_id["LCS-001"]["dedupe_required"])
        self.assertFalse(by_id["LCS-003"]["affects_consumption"])
        self.assertTrue(by_id["LCS-003"]["affects_investment"])
        self.assertEqual(by_id["LCS-005"]["review_state"], "NEEDS_REVIEW when abs(amount) >= 1000 else ACCEPTED")


if __name__ == "__main__":
    unittest.main()
