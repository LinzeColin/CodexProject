from __future__ import annotations

import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from econ_bleed_analyzer.query import (
    connect_readonly,
    query_question,
    query_categories,
    query_months,
    query_review,
    query_risks,
    query_transactions,
)


def make_db(path: Path) -> None:
    with sqlite3.connect(path) as conn:
        conn.execute(
            """
            create table summary_by_month (
                period text, period_start text, period_end text, transactions text,
                total_expense text, total_income text, net_cash_flow text,
                total_transfer text, pending_review text, real_consumption text,
                risk_spending text, optimizable_spending text, social_spending text,
                financial_spending text
            )
            """
        )
        conn.execute("insert into summary_by_month values ('2026-06','2026-06-01','2026-06-30','1','60.00','0.00','-60.00','0.00','20000.00','60.00','0.00','0.00','0.00','0.00')")
        conn.execute("create table summary_by_category (main_category text, sub_category text, amount text, count text, main_pct text, sub_pct text)")
        conn.execute("insert into summary_by_category values ('生活刚需','', '100.00', '2', '80.00%', '100.00%')")
        conn.execute("insert into summary_by_category values ('','餐饮日用', '60.00', '1', '', '60.00%')")
        conn.execute("create table summary_by_risk_tag (risk_tag text, amount text, count text, expense_pct text)")
        conn.execute("insert into summary_by_risk_tag values ('餐饮日用','60.00','1','60.00%')")
        conn.execute("create table spending_control_plan (priority text, focus_area text, trigger_metric text, current_amount text, current_pct text, recommended_action text, suggested_cap text, estimated_saving text, review_needed text)")
        conn.execute("insert into spending_control_plan values ('P1','可优化消费','超预算','60.00','60.00%','压缩','45.00','15.00','否')")
        conn.execute(
            """
            create table production_expense_allocations (
                transaction_time text, date text, counterparty text, description text,
                allocated_amount text, main_category text, sub_category text,
                risk_tags text, review_decision text, review_key text
            )
            """
        )
        conn.execute(
            """
            insert into production_expense_allocations values
            ('2026-06-02 12:00:00','2026-06-02','便利店','午餐','60.00','生活刚需','餐饮日用','餐饮日用|基础支出','auto','k1')
            """
        )
        conn.execute(
            """
            create table manual_review_queue (
                transaction_time text, counterparty text, description text, amount text,
                amount_cents text, main_category text, sub_category text, risk_tags text, order_id text
            )
            """
        )
        conn.execute(
            """
            insert into manual_review_queue values
            ('2026-06-03 10:00:00','待确认','大额转账','20000.00','2000000','社交家庭','亲情卡人情往来','社交家庭','r1')
            """
        )
        conn.execute("create table manual_review_status_summary (status text, status_label text, count text, amount text, count_pct text, amount_pct text, production_effect text, next_action text)")
        conn.execute("insert into manual_review_status_summary values ('pending_review','仍待复核','1','20000.00','100.00%','100.00%','隔离不入账','确认')")
        conn.execute("create table manual_review_decision_candidate_groups (group_type text, group_key text, count text, amount text, include_candidate_count text, manual_review_count text, high_confidence_count text, medium_confidence_count text, low_confidence_count text, top_reason text)")
        conn.execute("insert into manual_review_decision_candidate_groups values ('counterparty','待确认','1','20000.00','0','1','0','0','1','person')")
        conn.execute("create table v_mart_daily_cashflow (date text, month text, year text, total_expense text, total_income text, net_cash_flow text, total_transfer text, pending_review text)")
        conn.execute("insert into v_mart_daily_cashflow values ('2026-06-02','2026-06','2026','60.00','0.00','-60.00','0.00','0.00')")
        conn.commit()


class QueryTests(unittest.TestCase):
    def test_readonly_queries_return_expected_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "consumption.sqlite"
            make_db(db)
            with connect_readonly(db) as conn:
                self.assertEqual(query_months(conn)[0]["period"], "2026-06")
                self.assertEqual(query_categories(conn, 2)[0]["main_category"], "生活刚需")
                self.assertEqual(query_risks(conn, 1)[0]["risk_tag"], "餐饮日用")
                txs = query_transactions(conn, month="2026-06", main_category="生活刚需", risk_tag="餐饮日用")
                self.assertEqual(txs[0]["counterparty"], "便利店")
                self.assertEqual(query_review(conn, 1)[0]["order_id"], "r1")
                self.assertEqual(query_question(conn, "本月现金流怎么样", 2)["matched_template"], "latest_month_cashflow")
                pending = query_question(conn, "有哪些一万以上大额待复核", 2)
                self.assertEqual(pending["matched_template"], "pending_large_review")
                self.assertEqual(pending["data"]["status"][0]["status"], "pending_review")
                unknown = query_question(conn, "请执行 drop table", 2)
                self.assertFalse(unknown["ok"])
                self.assertIn("不会执行任意 SQL", unknown["message"])
                with self.assertRaises(sqlite3.OperationalError):
                    conn.execute("create table should_fail (id text)")


if __name__ == "__main__":
    unittest.main()
