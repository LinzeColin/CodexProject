from __future__ import annotations

import io
import json
import sqlite3
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from source_registry.cli import main as cli_main
from source_registry.content_db import begin_run, init_content_database
from source_registry.readiness import build_readiness_status
from source_registry.web_search import search_provider_status


class ReadinessTest(unittest.TestCase):
    def test_search_provider_status_uses_secret_presence_without_exposing_values(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "secrets.json"
            path.write_text(
                json.dumps(
                    {
                        "SERPAPI_API_KEY": "serp-secret",
                        "BING_SEARCH_API_KEY": "bing-secret",
                        "GOOGLE_SEARCH_API_KEY": "google-secret",
                        "GOOGLE_CSE_ID": "cse-secret",
                    }
                ),
                encoding="utf-8",
            )
            status = search_provider_status(path)
            self.assertTrue(all(item["ready"] for item in status))
            encoded = json.dumps(status, ensure_ascii=False)
            self.assertNotIn("serp-secret", encoded)
            self.assertNotIn("bing-secret", encoded)
            self.assertNotIn("google-secret", encoded)
            self.assertNotIn("cse-secret", encoded)

    def test_readiness_status_checks_platform_files_and_chinese_entries(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cookie = root / "bilibili_cookie.txt"
            cookie.write_text("SESSDATA=secret", encoding="utf-8")
            auth = root / "platform_auth.json"
            auth.write_text(
                json.dumps(
                    {
                        "platforms": {
                            "bilibili": {
                                "auth_method": "cookie_file",
                                "cookie_file": str(cookie),
                            }
                        }
                    }
                ),
                encoding="utf-8",
            )
            sources = root / "interpretation_sources.json"
            sources.write_text(
                json.dumps(
                    {
                        "sources": [
                            {"interpretation_source_id": "baidu", "platform": "baidu", "url_template": "x"},
                            {"interpretation_source_id": "sogou", "platform": "sogou", "url_template": "x"},
                            {"interpretation_source_id": "360", "platform": "360", "url_template": "x"},
                        ]
                    }
                ),
                encoding="utf-8",
            )
            conn = sqlite3.connect(":memory:")
            conn.row_factory = sqlite3.Row
            init_content_database(conn)
            begin_run(conn, "2026060401", "test")
            status = build_readiness_status(
                content_conn=conn,
                platform_auth_file=auth,
                interpretation_source_file=sources,
            )
            self.assertEqual(status["platform_auth"]["available_count"], 1)
            self.assertEqual(status["chinese_search_entries"]["configured_count"], 3)
            encoded = json.dumps(status, ensure_ascii=False)
            self.assertNotIn("SESSDATA=secret", encoded)
            self.assertNotIn(str(cookie), encoded)
            conn.close()

    def test_cli_readiness_outputs_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_db = root / "source_registry.sqlite"
            content_db = root / "policy_documents.sqlite"
            out = io.StringIO()
            with redirect_stdout(out):
                code = cli_main(
                    [
                        "--db",
                        str(source_db),
                        "readiness",
                        "--content-db",
                        str(content_db),
                        "--json",
                    ]
                )
            self.assertEqual(code, 0)
            status = json.loads(out.getvalue())
            self.assertIn("search_api", status)
            self.assertIn("platform_auth", status)
            self.assertIn("next_actions", status)


if __name__ == "__main__":
    unittest.main()
