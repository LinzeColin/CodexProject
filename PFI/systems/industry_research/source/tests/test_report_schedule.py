from __future__ import annotations

from datetime import datetime
import unittest
from argparse import Namespace
import io
from contextlib import redirect_stdout
from unittest.mock import patch

from src.cli import (
    _assert_actionable_snapshot,
    _assert_report_generation_due,
    _report_generation_is_due,
    _report_not_due_message,
    _requires_actionable_quote,
    generate_weekly_suite,
)
from src.reporting.analysis import daily_session_analysis, report_meta
from src.reporting.schedule import REPORT_DUE_TIMES, SESSION_TIMES


class ReportScheduleTest(unittest.TestCase):
    def test_report_meta_uses_current_required_report_times(self) -> None:
        cases = [
            ("monday_pre_open", "2026-06-01", "2026-06-01 周一08:30 Australia/Sydney"),
            ("post_close", "2026-06-05", "2026-06-05 16:05 Australia/Sydney"),
            ("friday_post_close", "2026-06-05", "2026-06-05 周五16:15 Australia/Sydney"),
        ]
        for session, as_of, expected in cases:
            with self.subTest(session=session):
                self.assertIn(f"计划报告时间：{expected}", report_meta(as_of, session))

    def test_due_times_and_report_display_times_share_same_schedule(self) -> None:
        expected = {
            "monday_pre_open": "08:30",
            "pre_open": "08:45",
            "midday": "12:05",
            "post_close": "16:05",
            "kline": "16:45",
            "friday_post_close": "16:15",
        }
        for session, hhmm in expected.items():
            with self.subTest(session=session):
                self.assertEqual(REPORT_DUE_TIMES[session].strftime("%H:%M"), hhmm)
                self.assertIn(hhmm, SESSION_TIMES[session]["report"])

    def test_post_close_session_analysis_uses_1605(self) -> None:
        self.assertIn("分析时间：16:05 Australia/Sydney", daily_session_analysis("post_close", [], []))

    def test_generation_due_gate_rejects_same_day_before_due_time(self) -> None:
        with self.assertRaises(SystemExit) as ctx:
            _assert_report_generation_due("pre_open", "2026-06-05", now=datetime(2026, 6, 5, 8, 44))

        self.assertIn("REPORT_NOT_DUE: pre_open 2026-06-05 due_at=08:45", str(ctx.exception))

    def test_generation_due_gate_accepts_same_day_at_due_time(self) -> None:
        _assert_report_generation_due("pre_open", "2026-06-05", now=datetime(2026, 6, 5, 8, 45))
        self.assertTrue(_report_generation_is_due("kline", "2026-06-05", now=datetime(2026, 6, 5, 16, 45)))

    def test_actionable_snapshot_requires_user_tradable_index_quotes(self) -> None:
        watchlist = [
            {"symbol": "000688", "exchange": "SSE", "asset_class": "Index"},
            {"symbol": "399986", "exchange": "SZSE", "asset_class": "Index"},
            {"symbol": "000001", "exchange": "SSE", "asset_class": "Index"},
            {"symbol": "TQQQ", "exchange": "US", "asset_class": "ETF"},
        ]

        self.assertTrue(_requires_actionable_quote(watchlist[0]))
        self.assertTrue(_requires_actionable_quote(watchlist[1]))
        self.assertFalse(_requires_actionable_quote(watchlist[2]))
        self.assertTrue(_requires_actionable_quote(watchlist[3]))
        with self.assertRaises(RuntimeError) as ctx:
            _assert_actionable_snapshot(
                [
                    {"symbol": "000688", "date": "2026-06-05", "close": "1000"},
                    {"symbol": "TQQQ", "date": "2026-06-05", "close": "100"},
                ],
                watchlist,
                "2026-06-05",
            )

        self.assertIn("缺少行情：399986", str(ctx.exception))
        self.assertNotIn("000001", str(ctx.exception))

    def test_generation_due_gate_treats_future_date_as_not_due_and_past_as_due(self) -> None:
        self.assertFalse(_report_generation_is_due("midday", "2026-06-06", now=datetime(2026, 6, 5, 18, 0)))
        self.assertTrue(_report_generation_is_due("midday", "2026-06-04", now=datetime(2026, 6, 5, 8, 0)))
        self.assertFalse(_report_generation_is_due("midday", "2026-06-04", now=datetime(2026, 6, 5, 8, 0), allow_historical=False))

    def test_generation_due_gate_can_disallow_historical_dates_for_automation_repair(self) -> None:
        with self.assertRaises(SystemExit) as ctx:
            _assert_report_generation_due(
                "midday",
                "2026-06-04",
                now=datetime(2026, 6, 5, 8, 0),
                allow_historical=False,
            )

        self.assertIn("REPORT_NOT_DUE: midday 2026-06-04", str(ctx.exception))

    def test_not_due_skip_message_is_explicit_for_suite_commands(self) -> None:
        message = _report_not_due_message("post_close", "2026-06-05", skipped=True)
        self.assertEqual(message, "REPORT_NOT_DUE_SKIPPED: post_close 2026-06-05 due_at=16:05 timezone=Australia/Sydney")

    def test_weekly_suite_does_not_backfill_monday_when_run_later_in_week(self) -> None:
        args = Namespace(date="2026-06-03", no_sync_moomoo=True, skip_quality_check=True)
        with patch("src.cli.load_research_context") as load_context, redirect_stdout(io.StringIO()) as stdout:
            generate_weekly_suite(args)

        load_context.assert_not_called()
        self.assertIn("NO_DUE_REPORTS: 2026-06-03", stdout.getvalue())

    def test_weekly_suite_generates_only_current_day_weekly_session(self) -> None:
        args = Namespace(date="2026-06-05", no_sync_moomoo=True, skip_quality_check=True)
        context = {
            "watchlist": [],
            "factors": [],
            "events": [],
            "advice": [],
            "sources": [],
            "account_update_summary": "",
            "account_summary": {},
        }
        with patch("src.cli._report_generation_is_due", return_value=True), patch("src.cli.load_research_context", return_value=context), patch(
            "src.cli.generate_watchlist_weekly_report", return_value="/tmp/friday.pdf"
        ) as generate_report, patch("src.cli._run_quality_gate_unless_skipped") as quality_gate, redirect_stdout(io.StringIO()) as stdout:
            generate_weekly_suite(args)

        self.assertIn("/tmp/friday.pdf", stdout.getvalue())
        generate_report.assert_called_once()
        self.assertEqual(generate_report.call_args.kwargs["session"], "friday_post_close")
        self.assertEqual(generate_report.call_args.kwargs["as_of"], "2026-06-05")
        quality_gate.assert_called_once()


if __name__ == "__main__":
    unittest.main()
