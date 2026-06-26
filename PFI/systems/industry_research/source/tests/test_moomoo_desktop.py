from __future__ import annotations

from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from src.integrations.moomoo_desktop import _fallback_only_timeout_seconds, _opend_fetch_timeout_seconds, _opend_subprocess_env, _port_listening_via_lsof, _port_open
from src.integrations.moomoo_opend_fetch import _fallback_budget_seconds, _diagnostic_rows, _group_quote_codes, _opend_error_category, _request_timeout, _to_moomoo_code, _write_csv


class MoomooDesktopTest(unittest.TestCase):
    def test_port_open_falls_back_to_lsof_when_socket_is_permission_blocked(self) -> None:
        class PermissionBlockedSocket:
            def settimeout(self, timeout: float) -> None:
                self.timeout = timeout

            def connect(self, address: tuple[str, int]) -> None:
                raise PermissionError("Operation not permitted")

            def close(self) -> None:
                self.closed = True

        with patch("src.integrations.moomoo_desktop.socket.socket", return_value=PermissionBlockedSocket()), \
            patch("src.integrations.moomoo_desktop._port_listening_via_lsof", return_value=True) as lsof_check:
            self.assertTrue(_port_open("127.0.0.1", 11111))

        lsof_check.assert_called_once_with(11111)

    def test_port_lsof_parser_detects_listening_port(self) -> None:
        result = SimpleNamespace(
            returncode=0,
            stdout="moomoo_Op 42298 user 68u IPv4 TCP 127.0.0.1:11111 (LISTEN)\n",
        )
        with patch("src.integrations.moomoo_desktop.subprocess.run", return_value=result):
            self.assertTrue(_port_listening_via_lsof(11111))

    def test_port_lsof_parser_rejects_missing_listener(self) -> None:
        result = SimpleNamespace(returncode=1, stdout="")
        with patch("src.integrations.moomoo_desktop.subprocess.run", return_value=result):
            self.assertFalse(_port_listening_via_lsof(11111))

    def test_opend_subprocess_env_uses_project_writable_home_and_sitecustomize(self) -> None:
        env = _opend_subprocess_env()

        self.assertIn("data/report_artifacts/automation_runtime/moomoo_home", env["HOME"])
        self.assertIn("data/report_artifacts/automation_runtime/sitecustomize", env["PYTHONPATH"])

    def test_opend_fetch_timeout_has_safe_default_and_floor(self) -> None:
        with patch.dict("src.integrations.moomoo_desktop.os.environ", {}, clear=True):
            self.assertEqual(_opend_fetch_timeout_seconds(), 90)
        with patch.dict("src.integrations.moomoo_desktop.os.environ", {"AI_RESEARCH_OPEND_FETCH_TIMEOUT_SECONDS": "5"}):
            self.assertEqual(_opend_fetch_timeout_seconds(), 15)
        with patch.dict("src.integrations.moomoo_desktop.os.environ", {"AI_RESEARCH_OPEND_FETCH_TIMEOUT_SECONDS": "abc"}):
            self.assertEqual(_opend_fetch_timeout_seconds(), 90)

    def test_fallback_only_timeout_has_safe_default_and_floor(self) -> None:
        with patch.dict("src.integrations.moomoo_desktop.os.environ", {}, clear=True):
            self.assertEqual(_fallback_only_timeout_seconds(), 70)
        with patch.dict("src.integrations.moomoo_desktop.os.environ", {"AI_RESEARCH_FALLBACK_ONLY_TIMEOUT_SECONDS": "5"}):
            self.assertEqual(_fallback_only_timeout_seconds(), 20)

    def test_opend_error_category_detects_quote_permission(self) -> None:
        self.assertEqual(_opend_error_category("No permission to get quotes for SH.000001"), "quote_permission")

    def test_fallback_budget_has_safe_default_and_floor(self) -> None:
        with patch.dict("src.integrations.moomoo_opend_fetch.os.environ", {}, clear=True):
            self.assertEqual(_fallback_budget_seconds(), 55.0)
        with patch.dict("src.integrations.moomoo_opend_fetch.os.environ", {"AI_RESEARCH_QUOTE_FALLBACK_BUDGET_SECONDS": "3"}):
            self.assertEqual(_fallback_budget_seconds(), 10.0)
        self.assertGreaterEqual(_request_timeout(None, default=5), 5.0)

    def test_group_quote_codes_batches_by_market_prefix(self) -> None:
        self.assertEqual(
            _group_quote_codes(["SZ.159995", "US.QQQ", "SH.512620", "US.VOO"]),
            [["SH.512620"], ["SZ.159995"], ["US.QQQ", "US.VOO"]],
        )

    def test_cn_opend_quotes_are_disabled_by_default_but_can_be_enabled(self) -> None:
        row = {"symbol": "159995", "exchange": "SZSE", "asset_class": "ETF"}
        with patch.dict("src.integrations.moomoo_opend_fetch.os.environ", {}, clear=True):
            self.assertEqual(_to_moomoo_code(row), "")
        with patch.dict("src.integrations.moomoo_opend_fetch.os.environ", {"AI_RESEARCH_OPEND_CN_QUOTES": "1"}):
            self.assertEqual(_to_moomoo_code(row), "SZ.159995")

    def test_diagnostic_rows_record_fallback_and_permission_reason(self) -> None:
        watchlist_row = {
            "symbol": "512620",
            "quote_code": "SH.512620",
            "name": "农业ETF天弘",
            "exchange": "SSE",
            "asset_class": "ETF",
        }
        rows = _diagnostic_rows(
            "2026-06-05",
            [(watchlist_row, "SH.512620")],
            {},
            {"SH.512620": "No permission to get quotes for SH.512620"},
            {"512620": {"source_name": "Yahoo Finance (US)", "source_time": "2026-06-05 07:00 UTC"}},
            [watchlist_row],
            {"512620"},
        )

        self.assertEqual(rows[0]["opend_status"], "failed")
        self.assertEqual(rows[0]["opend_error_category"], "quote_permission")
        self.assertEqual(rows[0]["fallback_status"], "used")
        self.assertIn("权限不足", rows[0]["diagnosis"])

    def test_write_csv_refuses_to_overwrite_with_no_actionable_prices(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "watchlist_snapshot.csv"
            original = (
                "date,symbol,quote_code,name,exchange,asset_class,research_group,close,daily_change_pct,open,high,low,volume,turnover,snapshot_note,source_name,source_url\n"
                "2026-06-05,QQQ,US.QQQ,纳指ETF,US,ETF,美股科技,100,0.01,99,101,98,1000,100000,ok,Moomoo OpenD,opend://127.0.0.1\n"
            )
            output.write_text(original, encoding="utf-8")

            with self.assertRaisesRegex(RuntimeError, "Refusing to overwrite"):
                _write_csv(
                    str(output),
                    [
                        {
                            "date": "2026-06-05",
                            "symbol": "QQQ",
                            "quote_code": "US.QQQ",
                            "name": "纳指ETF",
                            "exchange": "US",
                            "asset_class": "ETF",
                            "research_group": "美股科技",
                            "close": "",
                        }
                    ],
                )

            self.assertEqual(output.read_text(encoding="utf-8"), original)
            self.assertFalse((Path(tmp) / "watchlist_snapshot.csv.last_good").exists())

    def test_write_csv_backs_up_previous_actionable_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "watchlist_snapshot.csv"
            original = (
                "date,symbol,quote_code,name,exchange,asset_class,research_group,close,daily_change_pct,open,high,low,volume,turnover,snapshot_note,source_name,source_url\n"
                "2026-06-04,QQQ,US.QQQ,纳指ETF,US,ETF,美股科技,100,0.01,99,101,98,1000,100000,ok,Moomoo OpenD,opend://127.0.0.1\n"
            )
            output.write_text(original, encoding="utf-8")

            _write_csv(
                str(output),
                [
                    {
                        "date": "2026-06-05",
                        "symbol": "QQQ",
                        "quote_code": "US.QQQ",
                        "name": "纳指ETF",
                        "exchange": "US",
                        "asset_class": "ETF",
                        "research_group": "美股科技",
                        "close": "101",
                    }
                ],
            )

            self.assertEqual((Path(tmp) / "watchlist_snapshot.csv.last_good").read_text(encoding="utf-8"), original)
            self.assertIn("2026-06-05,QQQ", output.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
