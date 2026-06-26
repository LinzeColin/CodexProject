from __future__ import annotations

import unittest
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from econ_bleed_analyzer.alipay import Transaction
from econ_bleed_analyzer.classifier import classify_transaction, classify_transactions, load_rules


RULES = load_rules(ROOT / "configs" / "classification_rules.json")


def tx(**overrides):
    base = dict(
        transaction_time=datetime(2026, 6, 3, 23, 20, 0),
        transaction_type="餐饮美食",
        counterparty="淘宝闪购",
        account="/",
        description="外卖订单",
        direction="支出",
        amount_cents=3600,
        payment_method="花呗",
        status="交易成功",
        order_id="1",
        merchant_order_id="",
        note="",
        source_file="sample.csv",
    )
    base.update(overrides)
    return Transaction(**base)


class ClassifierTests(unittest.TestCase):
    def test_platform_convenience_is_optimizable_and_risk(self):
        row = classify_transaction(tx(), RULES)
        self.assertEqual(row.primary_bucket, "optimizable_spending")
        self.assertEqual(row.mechanism, "平台便利溢价")
        self.assertTrue(row.is_optimizable_spending)
        self.assertTrue(row.is_risk_spending)

    def test_fund_same_day_buys_marked_investment_impulse(self):
        rows = classify_transactions(
            [
                tx(
                    transaction_type="投资理财",
                    counterparty="蚂蚁财富",
                    description=f"蚂蚁财富-基金{i}-买入",
                    direction="不计收支",
                    amount_cents=10000,
                    payment_method="余额宝",
                    order_id=str(i),
                )
                for i in range(3)
            ],
            RULES,
        )
        self.assertTrue(all(row.mechanism == "投资冲动" for row in rows))
        self.assertTrue(all(row.risk_level == "high" for row in rows))

    def test_account_transfer_is_not_real_consumption(self):
        row = classify_transaction(
            tx(transaction_type="账户存取", description="余额宝-转出到银行卡", direction="不计收支", payment_method="余额宝"),
            RULES,
        )
        self.assertEqual(row.primary_bucket, "account_transfer")
        self.assertFalse(row.is_real_consumption)


if __name__ == "__main__":
    unittest.main()
