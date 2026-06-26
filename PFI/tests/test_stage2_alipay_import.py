from __future__ import annotations

import io
import unittest
import zipfile

from pfi_v02.core_models import LedgerEventType
from pfi_v02.stage2_import import parse_alipay_bill_bytes


ALIPAY_CSV = """交易时间,商品说明,交易对方,交易类型,金额,收/支
2026-06-27 10:00:00,咖啡,本地商户,消费,18.50,支出
2026-06-27 11:00:00,支付宝基金申购,易方达基金,基金申购,800.00,支出
2026-06-28 12:00:00,基金赎回到账,易方达基金,基金赎回,500.00,收入
2026-06-28 13:00:00,退款,电商平台,退款,30.00,收入
2026-06-29 14:00:00,未知,,未知,12.00,支出
"""


class Stage2AlipayImportTest(unittest.TestCase):
    def test_alipay_csv_parser_handles_consumption_refund_transfer_and_fund_events(self) -> None:
        result = parse_alipay_bill_bytes(ALIPAY_CSV.encode("utf-8"))
        event_types = {txn.description: txn.event_type for txn in result.transactions}

        self.assertEqual(result.import_batch.source_id, "alipay_daily")
        self.assertEqual(result.import_batch.parser_version, "alipay_bill_csv_v1")
        self.assertEqual(len(result.transactions), 5)
        self.assertEqual(event_types["咖啡 本地商户 消费"], LedgerEventType.CASH)
        self.assertEqual(event_types["支付宝基金申购 易方达基金 基金申购"], LedgerEventType.FUND)
        self.assertEqual(event_types["基金赎回到账 易方达基金 基金赎回"], LedgerEventType.FUND)
        self.assertEqual(event_types["退款 电商平台 退款"], LedgerEventType.REFUND)

    def test_alipay_fund_subscription_and_redemption_are_investment_candidates_not_ordinary_income(self) -> None:
        result = parse_alipay_bill_bytes(ALIPAY_CSV.encode("utf-8"))
        fund_transactions = [txn for txn in result.transactions if txn.event_type == LedgerEventType.FUND]

        self.assertEqual(len(fund_transactions), 2)
        self.assertLess(fund_transactions[0].amount, 0)
        self.assertGreater(fund_transactions[1].amount, 0)
        for txn in fund_transactions:
            self.assertEqual(txn.source_id, "alipay_daily")
            self.assertGreaterEqual(txn.confidence, 0.9)

    def test_low_confidence_items_go_to_multiple_choice_review_queue(self) -> None:
        result = parse_alipay_bill_bytes(ALIPAY_CSV.encode("utf-8"))

        self.assertEqual(len(result.review_queue), 1)
        item = result.review_queue[0]
        self.assertIn("Alipay low-confidence", item.reason)
        self.assertEqual(item.choices[0], "A accept suggested classification")
        self.assertEqual(item.choices[-1], "D keep pending")

    def test_alipay_zip_parser_reads_inner_csv_bill(self) -> None:
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as archive:
            archive.writestr("alipay_bill.csv", ALIPAY_CSV)

        result = parse_alipay_bill_bytes(buffer.getvalue())

        self.assertEqual(len(result.transactions), 5)
        self.assertEqual(result.transactions[0].occurred_at, "2026-06-27")


if __name__ == "__main__":
    unittest.main()
