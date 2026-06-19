from __future__ import annotations

import json
import sqlite3
import sys
import tempfile
import unittest
from http import HTTPStatus
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from econ_bleed_analyzer.api import LedgerApiHandler, _safe_static_path


def make_api_db(path: Path) -> None:
    with sqlite3.connect(path) as conn:
        conn.execute("create table ledger_metadata (key text, value text)")
        conn.executemany(
            "insert into ledger_metadata values (?,?)",
            [
                ("schema_version", "test"),
                ("transaction_count", "2"),
                ("date_start", "2026-01-01"),
                ("date_end", "2026-01-02"),
            ],
        )
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
        conn.execute("insert into summary_by_month values ('2026-01','2026-01-01','2026-01-31','2','100.00','20.00','-80.00','0.00','0.00','100.00','10.00','5.00','0.00','0.00')")
        for table in ["summary_by_week", "summary_by_quarter", "summary_by_half", "summary_by_year"]:
            conn.execute(f"create table {table} as select * from summary_by_month")
        conn.execute("create table summary_by_category (main_category text, sub_category text, amount text, count text, main_pct text, sub_pct text)")
        conn.execute("insert into summary_by_category values ('生活刚需','','100.00','1','100.00%','100.00%')")
        conn.execute("create table summary_by_risk_tag (risk_tag text, amount text, count text, expense_pct text)")
        conn.execute("insert into summary_by_risk_tag values ('基础支出','100.00','1','100.00%')")
        conn.execute("create table spending_control_plan (priority text, focus_area text, trigger_metric text, current_amount text, current_pct text, recommended_action text, suggested_cap text, estimated_saving text, review_needed text)")
        conn.execute("insert into spending_control_plan values ('P3','观察','无','0','0.00%','观察','0','0','否')")
        conn.execute("create table manual_review_queue (transaction_time text, counterparty text, description text, amount text, main_category text, sub_category text, risk_tags text, order_id text, amount_cents text)")
        conn.execute("insert into manual_review_queue values ('2026-01-02','x','review','20000.00','社交家庭','亲情卡人情往来','社交家庭','r1','2000000')")
        conn.execute("create table manual_review_status_summary (status text, status_label text, count text, amount text, count_pct text, amount_pct text, production_effect text, next_action text)")
        conn.execute("insert into manual_review_status_summary values ('pending_review','仍待复核','1','20000.00','100.00%','100.00%','隔离不入账','确认')")
        conn.execute("create table manual_review_decision_candidates (review_key text, candidate_action text, candidate_label text, candidate_confidence text, candidate_reason text, candidate_main_category text, candidate_sub_category text, candidate_risk_tags text, amount text, transaction_time text, source_platform text, counterparty text, description text, order_id text)")
        conn.execute("insert into manual_review_decision_candidates values ('r1','manual_review','保持人工复核','low','person','社交家庭','亲情卡人情往来','社交家庭','20000.00','2026-01-02','alipay','x','review','r1')")
        conn.execute("create table manual_review_decision_candidate_groups (group_type text, group_key text, count text, amount text, include_candidate_count text, manual_review_count text, high_confidence_count text, medium_confidence_count text, low_confidence_count text, top_reason text)")
        conn.execute("insert into manual_review_decision_candidate_groups values ('counterparty','x','1','20000.00','0','1','0','0','1','person')")
        conn.execute("create table source_platform_summary (platform text, transaction_count text, source_file_count text, production_expense text, expense_pct text, pending_review_count text)")
        conn.execute("insert into source_platform_summary values ('alipay','2','1','100.00','100.00%','1')")
        conn.execute("create table production_expense_allocations (date text, transaction_time text, counterparty text, description text, allocated_amount text, main_category text, sub_category text, risk_tags text, review_decision text, review_key text)")
        conn.execute("insert into production_expense_allocations values ('2026-01-01','2026-01-01 12:00:00','merchant','food','100.00','生活刚需','餐饮日用','基础支出','auto','p1')")
        conn.execute("create table v_mart_daily_cashflow (date text, month text, year text, total_expense text, total_income text, net_cash_flow text, total_transfer text, pending_review text)")
        conn.execute("insert into v_mart_daily_cashflow values ('2026-01-01','2026-01','2026','100.00','20.00','-80.00','0.00','0.00')")
        conn.commit()


class ApiTests(unittest.TestCase):
    def test_readonly_api_routes_without_binding_socket(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db = root / "ledger.sqlite"
            reports = root / "reports"
            reports.mkdir()
            (reports / "index.html").write_text("<html>reports</html>", encoding="utf-8")
            make_api_db(db)
            handler = object.__new__(LedgerApiHandler)
            handler.server = SimpleNamespace(db_path=db, report_dir=reports)
            sent: list[tuple[HTTPStatus, object]] = []
            handler._send_json = lambda status, payload: sent.append((status, payload))  # type: ignore[method-assign]
            handler._send_error = lambda status, message: sent.append((status, {"ok": False, "error": message}))  # type: ignore[method-assign]

            handler._serve_api("health", {})
            self.assertEqual(sent[-1][0], HTTPStatus.OK)
            self.assertEqual(sent[-1][1]["transaction_count"], "2")

            handler._serve_api("stats", {"period": ["month"], "limit": ["1"]})
            self.assertEqual(sent[-1][1]["data"][0]["period"], "2026-01")

            handler._serve_api("review-status", {})
            self.assertEqual(sent[-1][1]["data"][0]["status"], "pending_review")

            handler._serve_api("review-candidates", {"limit": ["1"]})
            self.assertEqual(sent[-1][1]["data"][0]["review_key"], "r1")

            handler._serve_api("review-candidate-groups", {"limit": ["1"]})
            self.assertEqual(sent[-1][1]["data"][0]["group_type"], "counterparty")

            handler._serve_api("question-templates", {})
            self.assertEqual(sent[-1][0], HTTPStatus.OK)
            self.assertTrue(any(item["id"] == "pending_large_review" for item in sent[-1][1]["data"]))

            handler._serve_api("ask", {"q": ["本月现金流如何"], "limit": ["1"]})
            self.assertEqual(sent[-1][0], HTTPStatus.OK)
            self.assertEqual(sent[-1][1]["matched_template"], "latest_month_cashflow")

            handler._serve_api("sql", {"query": ["drop"]})
            self.assertEqual(sent[-1][0], HTTPStatus.NOT_FOUND)

            self.assertEqual(_safe_static_path(reports, "/reports/index.html"), reports.resolve() / "index.html")
            self.assertIsNone(_safe_static_path(reports, "/reports/../ledger.sqlite"))


if __name__ == "__main__":
    unittest.main()
