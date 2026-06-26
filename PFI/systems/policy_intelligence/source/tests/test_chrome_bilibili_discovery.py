from __future__ import annotations

import io
import json
import sqlite3
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from source_registry.chrome_bilibili_discovery import (
    CHROME_EPOCH_OFFSET_SECONDS,
    build_chrome_bilibili_discovery,
    render_chrome_bilibili_discovery_dashboard,
    write_chrome_bilibili_discovery_dashboard,
)
from source_registry.cli import main as cli_main


class ChromeBilibiliDiscoveryTest(unittest.TestCase):
    def test_discovery_reads_history_and_cookie_counts_without_cookie_values(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            history = root / "History"
            cookies = root / "Cookies"
            _write_history(history)
            _write_cookies(cookies)
            report = build_chrome_bilibili_discovery(
                history_file=history,
                cookies_file=cookies,
                limit=5,
            )
        encoded = json.dumps(report, ensure_ascii=False)
        self.assertEqual(report["history"]["status"], "ok")
        self.assertEqual(report["cookies"]["status"], "ok")
        self.assertEqual(report["summary"]["bilibili_cookie_row_count"], 2)
        self.assertEqual(report["summary"]["candidate_count"], 3)
        self.assertIn("https://www.bilibili.com/video/BV123", encoded)
        self.assertIn("https://search.bilibili.com/all?keyword=人工智能政策", encoded)
        self.assertNotIn("SESSDATA", encoded)
        self.assertNotIn("secret-cookie-value", encoded)
        self.assertNotIn(str(history), encoded)
        self.assertNotIn(str(cookies), encoded)

    def test_keyword_filter_keeps_relevant_candidates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            history = root / "History"
            cookies = root / "Cookies"
            _write_history(history)
            _write_cookies(cookies)
            report = build_chrome_bilibili_discovery(
                history_file=history,
                cookies_file=cookies,
                keyword="芯片",
            )
        self.assertEqual(report["summary"]["candidate_count"], 1)
        self.assertIn("芯片", report["history"]["candidates"][0]["title"])

    def test_missing_files_are_reported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = build_chrome_bilibili_discovery(
                history_file=root / "missing-history",
                cookies_file=root / "missing-cookies",
            )
        self.assertEqual(report["history"]["status"], "missing_file")
        self.assertEqual(report["cookies"]["status"], "missing_file")
        self.assertFalse(report["summary"]["history_available"])
        self.assertFalse(report["summary"]["cookie_db_available"])

    def test_render_and_write_dashboard(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            history = root / "History"
            cookies = root / "Cookies"
            output = root / "dashboard.html"
            _write_history(history)
            _write_cookies(cookies)
            report = build_chrome_bilibili_discovery(history_file=history, cookies_file=cookies)
            rendered = render_chrome_bilibili_discovery_dashboard(report, title="B站 Chrome 本地证据发现")
            result = write_chrome_bilibili_discovery_dashboard(
                output,
                history_file=history,
                cookies_file=cookies,
            )
            self.assertEqual(result, str(output))
            self.assertTrue(output.exists())
            self.assertIn("候选公开 URL", rendered)
            self.assertIn("安全与合规边界", rendered)

    def test_cli_generates_sanitized_dashboard(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            history = root / "History"
            cookies = root / "Cookies"
            output = root / "dashboard.html"
            _write_history(history)
            _write_cookies(cookies)
            out = io.StringIO()
            with redirect_stdout(out):
                code = cli_main(
                    [
                        "--db",
                        str(root / "source_registry.sqlite"),
                        "chrome-bilibili-discovery",
                        "--history-file",
                        str(history),
                        "--cookies-file",
                        str(cookies),
                        "--output",
                        str(output),
                        "--json",
                    ]
                )
            payload = json.loads(out.getvalue())
        self.assertEqual(code, 0)
        self.assertEqual(payload["dashboard_path"], str(output))
        self.assertEqual(payload["summary"]["bilibili_cookie_row_count"], 2)
        self.assertNotIn("secret-cookie-value", out.getvalue())
        self.assertNotIn(str(history), out.getvalue())


def _write_history(path: Path) -> None:
    conn = sqlite3.connect(path)
    try:
        conn.execute(
            "CREATE TABLE urls (id INTEGER PRIMARY KEY, url TEXT, title TEXT, visit_count INTEGER, last_visit_time INTEGER)"
        )
        conn.executemany(
            "INSERT INTO urls(url, title, visit_count, last_visit_time) VALUES (?, ?, ?, ?)",
            [
                (
                    "https://www.bilibili.com/video/BV123/?spm_id_from=333",
                    "人工智能政策深度解读",
                    4,
                    _chrome_time(1_750_000_000),
                ),
                (
                    "https://search.bilibili.com/all?keyword=人工智能政策&from_source=web",
                    "人工智能政策 - 搜索",
                    2,
                    _chrome_time(1_750_000_100),
                ),
                (
                    "https://www.bilibili.com/video/BV456/?p=2",
                    "芯片政策解读",
                    1,
                    _chrome_time(1_750_000_200),
                ),
                (
                    "https://example.com/not-bilibili",
                    "其他页面",
                    1,
                    _chrome_time(1_750_000_300),
                ),
            ],
        )
        conn.commit()
    finally:
        conn.close()


def _write_cookies(path: Path) -> None:
    conn = sqlite3.connect(path)
    try:
        conn.execute("CREATE TABLE cookies (host_key TEXT, name TEXT, value TEXT, encrypted_value BLOB)")
        conn.executemany(
            "INSERT INTO cookies(host_key, name, value, encrypted_value) VALUES (?, ?, ?, ?)",
            [
                (".bilibili.com", "SESSDATA", "secret-cookie-value", b""),
                (".bilibili.com", "DedeUserID", "secret-user-id", b""),
                (".example.com", "sid", "other", b""),
            ],
        )
        conn.commit()
    finally:
        conn.close()


def _chrome_time(unix_seconds: int) -> int:
    return int((unix_seconds + CHROME_EPOCH_OFFSET_SECONDS) * 1_000_000)


if __name__ == "__main__":
    unittest.main()
