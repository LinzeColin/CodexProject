from __future__ import annotations

import io
import tempfile
import unittest
import zipfile
from pathlib import Path

from pfi_v02.core_models import LedgerEventType
from pfi_v02.local_imports import build_alipay_import_preview, write_private_alipay_import
from pfi_v02.stage2_import import parse_alipay_bill_bytes


ALIPAY_CSV = """交易时间,商品说明,交易对方,交易类型,金额,收/支
2026-06-27 10:00:00,咖啡,本地商户,消费,18.50,支出
2026-06-27 11:00:00,支付宝基金申购,易方达基金,基金申购,800.00,支出
2026-06-28 12:00:00,基金赎回到账,易方达基金,基金赎回,500.00,收入
2026-06-28 13:00:00,退款,电商平台,退款,30.00,收入
2026-06-29 14:00:00,未知,,未知,12.00,支出
"""

ALIPAY_REAL_EXPORT_CSV = """------------------------------------------------------------------------------------
导出信息：
姓名：张三
支付宝账户：13800000000
起始时间：[2023-01-01 00:00:00]    终止时间：[2023-12-31 23:59:59]
共3笔记录

------------------------支付宝（中国）网络技术有限公司  电子客户回单------------------------
交易时间,交易分类,交易对方,对方账号,商品说明,收/支,金额,收/付款方式,交易状态,交易订单号,商家订单号,备注,
2023-05-01 10:00:00,餐饮美食,咖啡店,shop@example.com,拿铁,支出,18.50,余额,交易成功,202305010001,,,
2023-05-02 11:00:00,投资理财,余额宝,/,余额宝-转入,不计收支,500.00,银行卡,交易成功,202305020001,,,
2023-05-03 12:00:00,退款,电商平台,store@example.com,订单退款,收入,30.00,余额,交易成功,202305030001,,,
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

    def test_real_alipay_export_parser_skips_preamble_and_trailing_empty_column(self) -> None:
        result = parse_alipay_bill_bytes(ALIPAY_REAL_EXPORT_CSV.encode("utf-8"))

        self.assertEqual(result.import_batch.raw_record_count, 3)
        self.assertEqual(len(result.transactions), 3)
        self.assertEqual(result.transactions[0].description, "拿铁 咖啡店 餐饮美食")
        self.assertEqual(result.transactions[0].amount, -18.5)
        self.assertEqual(result.transactions[1].event_type, LedgerEventType.FUND)
        self.assertEqual(result.transactions[2].event_type, LedgerEventType.REFUND)

    def test_private_alipay_import_writes_manifest_and_normalized_transactions(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            data_home = Path(temp_dir)
            metadatabase_root = data_home / "MetaDatabase" / "PFI" / "alipay_daily"
            manifest = write_private_alipay_import(
                (("支付宝交易明细.csv", ALIPAY_REAL_EXPORT_CSV.encode("utf-8")),),
                data_home,
                metadatabase_root=metadatabase_root,
            )

            self.assertEqual(manifest["schema"], "PFIAlipayLocalImportPreviewV1")
            self.assertEqual(manifest["transaction_count"], 3)
            self.assertEqual(manifest["review_count"], 0)
            self.assertEqual(manifest["date_start"], "2023-05-01")
            self.assertEqual(manifest["date_end"], "2023-05-03")
            self.assertEqual(manifest["privacy_boundary"], "owner_authorized_metadatabase_archive_and_local_private_runtime")
            self.assertTrue(Path(manifest["private_manifest_path"]).exists())
            transactions_path = Path(manifest["private_transactions_path"])
            self.assertTrue(transactions_path.exists())
            self.assertIn("拿铁 咖啡店 餐饮美食", transactions_path.read_text(encoding="utf-8"))
            self.assertTrue(Path(manifest["metadatabase_manifest_path"]).exists())
            self.assertTrue(Path(manifest["metadatabase_transactions_path"]).exists())
            self.assertEqual(len(manifest["metadatabase_files"]), 1)
            self.assertTrue(Path(manifest["metadatabase_files"][0]["metadatabase_path"]).exists())

    def test_upload_preview_reports_file_and_event_counts(self) -> None:
        preview = build_alipay_import_preview((("支付宝交易明细.csv", ALIPAY_REAL_EXPORT_CSV.encode("utf-8")),))

        self.assertEqual(preview.valid_file_count, 1)
        self.assertEqual(preview.raw_record_count, 3)
        self.assertEqual(preview.event_counts["CASH"], 1)
        self.assertEqual(preview.event_counts["FUND"], 1)
        self.assertEqual(preview.event_counts["REFUND"], 1)


if __name__ == "__main__":
    unittest.main()
