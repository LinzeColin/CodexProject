from __future__ import annotations

import importlib.util
import json
import sqlite3
import sys
import tempfile
import unittest
import datetime as dt
from argparse import Namespace
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "weixin_alipay_fund_ingest.py"


ALIPAY_FUND_SAMPLE = """支付宝交易明细
交易时间,交易分类,交易对方,对方账号,商品说明,收/支,金额,收/付款方式,交易状态,交易订单号,商家订单号,备注
2026-06-03 09:00:00,投资理财,蚂蚁财富,,纳斯达克100ETF买入,支出,88.00,余额,交易成功,ali_fund_001,,
"""

ALIPAY_LIST_OCR_SAMPLE = """搜索交易记录
6月
支出¥8,610.17
收入¥0.00
蚂蚁财富-易方达全⋯
投资理财
今天11:34
蚂蚁财富-易方达全.
投资理财
今天 11:23
蚂蚁财富-华夏新锦…
投资理财
今天 10:47
余额宝-收益发放
投资理财
今天 06:09
收支分析〉
20.00
付款成功，基金份额确认中
20.00
付款成功，
100.00
付款成功，基金份额确认中
2.12
"""


def load_ingest_module():
    spec = importlib.util.spec_from_file_location("weixin_alipay_fund_ingest", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("Cannot load weixin_alipay_fund_ingest.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["weixin_alipay_fund_ingest"] = module
    spec.loader.exec_module(module)
    return module


class WeixinIntakeIngestTests(unittest.TestCase):
    def test_non_alipay_text_is_ignored_by_finance_ingest(self) -> None:
        ingest = load_ingest_module()
        with tempfile.TemporaryDirectory() as tmp:
            ingest.PRIVATE_ROOT = Path(tmp) / "private"
            db = Path(tmp) / "ledger.sqlite"

            result = ingest.process_media(
                Namespace(
                    media_path="",
                    media_type="text/plain",
                    text="今天看到一笔公司个人混同支出，等我晚点确认。",
                    ledger_db=str(db),
                    ocr_helper=str(ROOT / "missing.swift"),
                    json=True,
                )
            )

            self.assertFalse(result["handled"])
            self.assertEqual(result["status"], "ignored_non_alipay_media")
            self.assertFalse(db.exists())

    def test_official_bill_reuses_existing_parser_and_records_intake_effect(self) -> None:
        ingest = load_ingest_module()
        with tempfile.TemporaryDirectory() as tmp:
            ingest.PRIVATE_ROOT = Path(tmp) / "private"
            root = Path(tmp)
            db = root / "ledger.sqlite"
            bill = root / "alipay_fund.csv"
            bill.write_text(ALIPAY_FUND_SAMPLE, encoding="utf-8")

            result = ingest.process_media(
                Namespace(
                    media_path=str(bill),
                    media_type="text/csv",
                    text="微信转发的支付宝基金账单",
                    ledger_db=str(db),
                    ocr_helper=str(ROOT / "missing.swift"),
                    json=True,
                )
            )

            self.assertEqual(result["status"], "inserted")
            self.assertEqual(result["record_count"], 1)
            self.assertEqual(result["inserted_records"], 1)
            with sqlite3.connect(db) as conn:
                intake = conn.execute(
                    "select source_kind, data_status, review_status, ledger_effect, record_count from weixin_intake_items"
                ).fetchone()
                fund = conn.execute("select action, fund_name, amount_cents, review_status from alipay_fund_records").fetchone()
                batch = conn.execute("select status, record_count from alipay_fund_intake_batches").fetchone()
                commit = conn.execute("select inserted_records, reviewed_records, integrity_check from alipay_fund_commits").fetchone()
                review_count = conn.execute("select count(*) from alipay_fund_review_runs where verdict='pass'").fetchone()[0]
                confirmed_count = conn.execute("select count(*) from v_alipay_fund_confirmed_trades").fetchone()[0]
            self.assertEqual(intake, ("official_bill", "PARSED_CANDIDATE", "auto_review_passed", "fund_record_inserted", 1))
            self.assertEqual(fund[0], "buy")
            self.assertIn("纳斯达克", fund[1])
            self.assertEqual(fund[2], 8800)
            self.assertEqual(fund[3], "auto_review_passed")
            self.assertEqual(batch, ("inserted", 1))
            self.assertEqual(commit, (1, 1, "ok"))
            self.assertEqual(review_count, 6)
            self.assertEqual(confirmed_count, 1)

            second = ingest.process_media(
                Namespace(
                    media_path=str(bill),
                    media_type="text/csv",
                    text="微信转发的支付宝基金账单",
                    ledger_db=str(db),
                    ocr_helper=str(ROOT / "missing.swift"),
                    json=True,
                )
            )
            self.assertEqual(second["status"], "idempotent_noop")
            self.assertEqual(second["inserted_records"], 0)
            with sqlite3.connect(db) as conn:
                fund_count = conn.execute("select count(*) from alipay_fund_records").fetchone()[0]
            self.assertEqual(fund_count, 1)

    def test_video_is_archived_but_not_written_without_frame_ocr(self) -> None:
        ingest = load_ingest_module()
        with tempfile.TemporaryDirectory() as tmp:
            ingest.PRIVATE_ROOT = Path(tmp) / "private"
            root = Path(tmp)
            db = root / "ledger.sqlite"
            video = root / "alipay_fund.mp4"
            video.write_bytes(b"not-a-real-video")

            result = ingest.process_media(
                Namespace(
                    media_path=str(video),
                    media_type="video/mp4",
                    text="支付宝基金交易明细视频",
                    ledger_db=str(db),
                    ocr_helper=str(ROOT / "missing.swift"),
                    json=True,
                )
            )

            self.assertTrue(result["handled"])
            self.assertEqual(result["status"], "blocked_review_failed")
            with sqlite3.connect(db) as conn:
                intake = conn.execute(
                    "select source_kind, review_status, ledger_effect, record_count from weixin_intake_items"
                ).fetchone()
                fund_count = conn.execute("select count(*) from alipay_fund_records").fetchone()[0]
            self.assertEqual(intake, ("video", "auto_review_failed", "archive_only", 0))
            self.assertEqual(fund_count, 0)

    def test_alipay_list_screenshot_uses_relative_dates_and_row_amounts(self) -> None:
        ingest = load_ingest_module()
        source = {
            "source_sha256": "a" * 64,
            "source_id": "a" * 16,
            "source_kind": "screenshot",
        }

        rows = ingest.extract_alipay_list_screenshot(ALIPAY_LIST_OCR_SAMPLE, source)

        self.assertEqual(len(rows), 4)
        self.assertTrue(all(row.trade_date == dt.datetime.now().astimezone().date().isoformat() for row in rows))
        self.assertEqual([row.amount_cents for row in rows], [2000, 2000, 10000, 212])
        self.assertNotIn(861017, [row.amount_cents for row in rows])
        self.assertTrue(all(row.extraction_method == "macos_vision_ocr_list" for row in rows))


if __name__ == "__main__":
    unittest.main()
