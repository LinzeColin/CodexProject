from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from econ_bleed_analyzer.alipay import load_transactions, read_bill_xlsx, read_wechat_csv
from econ_bleed_analyzer.classifier import classify_transaction, load_rules


RULES = load_rules(ROOT / "configs" / "classification_rules.json")


WECHAT_SAMPLE = """微信支付账单明细
微信昵称：[测试]
交易时间,交易类型,交易对方,商品,收/支,金额(元),支付方式,当前状态,交易单号,商户单号,备注
2026-06-01 12:30:00,餐饮美食,美团外卖,午餐外卖订单,支出,¥36.50,零钱,支付成功,wx001,mch001,
2026-06-02 08:00:00,退款,美团外卖,午餐外卖订单退款,收入,￥12.00,零钱,已退款,wx002,mch002,
"""


ALIPAY_SAMPLE = """支付宝交易明细
交易时间,交易分类,交易对方,对方账号,商品说明,收/支,金额,收/付款方式,交易状态,交易订单号,商家订单号,备注
2026-06-03 09:00:00,餐饮美食,早餐店,,早餐,支出,8.00,余额,交易成功,ali001,,
"""


def write_minimal_xlsx(path: Path, rows: list[list[str]]) -> None:
    def col_name(index: int) -> str:
        value = ""
        index += 1
        while index:
            index, rem = divmod(index - 1, 26)
            value = chr(ord("A") + rem) + value
        return value

    sheet_rows = []
    for row_index, row in enumerate(rows, start=1):
        cells = []
        for col_index, value in enumerate(row):
            escaped = value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            cells.append(f'<c r="{col_name(col_index)}{row_index}" t="inlineStr"><is><t>{escaped}</t></is></c>')
        sheet_rows.append(f'<row r="{row_index}">{"".join(cells)}</row>')
    sheet_xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f'<sheetData>{"".join(sheet_rows)}</sheetData>'
        "</worksheet>"
    )
    with ZipFile(path, "w") as archive:
        archive.writestr("xl/worksheets/sheet1.xml", sheet_xml)


class BillImportTests(unittest.TestCase):
    def test_read_wechat_csv_maps_to_common_transaction_schema(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "wechat.csv"
            path.write_text(WECHAT_SAMPLE, encoding="utf-8")

            rows = read_wechat_csv(path)

        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0].transaction_type, "餐饮美食")
        self.assertEqual(rows[0].counterparty, "美团外卖")
        self.assertEqual(rows[0].description, "午餐外卖订单")
        self.assertEqual(rows[0].direction, "支出")
        self.assertEqual(rows[0].amount_cents, 3650)
        self.assertEqual(rows[0].payment_method, "零钱")
        self.assertEqual(rows[0].status, "支付成功")
        self.assertEqual(rows[0].order_id, "wx001")

    def test_wechat_transactions_reuse_existing_classification_rules(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "wechat.csv"
            path.write_text(WECHAT_SAMPLE, encoding="utf-8")
            row = classify_transaction(read_wechat_csv(path)[0], RULES)

        self.assertEqual(row.primary_bucket, "optimizable_spending")
        self.assertEqual(row.main_category, "可优化消费")
        self.assertEqual(row.cash_flow_type, "expense")

    def test_load_transactions_merges_alipay_and_wechat_csv_in_one_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "wechat.csv").write_text(WECHAT_SAMPLE, encoding="utf-8")
            (root / "alipay.csv").write_text(ALIPAY_SAMPLE, encoding="utf-8")

            rows = load_transactions([root])

        self.assertEqual(len(rows), 3)
        self.assertEqual([row.order_id for row in rows], ["wx001", "wx002", "ali001"])

    def test_read_wechat_xlsx_maps_to_common_transaction_schema(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "wechat.xlsx"
            write_minimal_xlsx(
                path,
                [
                    ["微信支付账单明细"],
                    ["交易时间", "交易类型", "交易对方", "商品", "收/支", "金额(元)", "支付方式", "当前状态", "交易单号", "商户单号", "备注"],
                    ["2026/06/04 19:15:00", "餐饮美食", "瑞幸咖啡", "拿铁", "支出", "￥18.00", "零钱", "支付成功", "wx_xlsx_001", "mch_xlsx_001", ""],
                ],
            )

            rows = read_bill_xlsx(path)

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].source_platform, "wechat")
        self.assertEqual(rows[0].counterparty, "瑞幸咖啡")
        self.assertEqual(rows[0].amount_cents, 1800)
        self.assertEqual(rows[0].order_id, "wx_xlsx_001")

    def test_load_transactions_merges_csv_and_xlsx_in_one_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "alipay.csv").write_text(ALIPAY_SAMPLE, encoding="utf-8")
            write_minimal_xlsx(
                root / "wechat.xlsx",
                [
                    ["交易时间", "交易类型", "交易对方", "商品", "收/支", "金额(元)", "支付方式", "当前状态", "交易单号", "商户单号", "备注"],
                    ["2026-06-04 12:00:00", "餐饮美食", "微信商户", "午餐", "支出", "22.30", "零钱", "支付成功", "wx_xlsx_002", "mch_xlsx_002", ""],
                ],
            )

            rows = load_transactions([root])

        self.assertEqual(len(rows), 2)
        self.assertEqual([row.source_platform for row in rows], ["alipay", "wechat"])


if __name__ == "__main__":
    unittest.main()
