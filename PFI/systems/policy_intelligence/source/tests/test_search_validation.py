from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from source_registry.cli import main as cli_main
from source_registry.search_validation import (
    build_search_validation,
    render_search_validation_dashboard,
    write_search_validation_dashboard,
)
from source_registry.web_search import SearchResult


class SearchValidationTest(unittest.TestCase):
    def test_offline_missing_keys_are_not_checked_online(self) -> None:
        report = build_search_validation(online=False)
        self.assertEqual(report["mode"], "offline")
        self.assertEqual(report["summary"]["missing_count"], 3)
        self.assertEqual(report["summary"]["online_checked_count"], 0)
        self.assertEqual(report["summary"]["public_entrance_passed_count"], 3)

    def test_online_success_does_not_expose_secret(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            secrets = Path(tmp) / "secrets.json"
            secrets.write_text(
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

            def fake_collector(**kwargs):
                return [SearchResult(title="测试结果", url="https://example.com/a")], "ok"

            report = build_search_validation(search_secrets_file=secrets, collector=fake_collector)
        encoded = json.dumps(report, ensure_ascii=False)
        self.assertEqual(report["summary"]["passed_count"], 3)
        self.assertEqual(report["summary"]["online_checked_count"], 3)
        self.assertNotIn("serp-secret", encoded)
        self.assertNotIn("bing-secret", encoded)
        self.assertEqual(report["providers"][0]["sample_domain"], "example.com")

    def test_online_failed_status_is_sanitized(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            secrets = Path(tmp) / "secrets.json"
            secrets.write_text(json.dumps({"SERPAPI_API_KEY": "secret"}), encoding="utf-8")

            def fake_collector(**kwargs):
                return [], "request_failed:serpapi:HTTPError"

            report = build_search_validation(search_secrets_file=secrets, collector=fake_collector)
        serpapi = next(item for item in report["providers"] if item["provider"] == "serpapi")
        self.assertEqual(serpapi["status"], "failed")
        self.assertEqual(serpapi["error_class"], "HTTPError")

    def test_render_search_validation_dashboard_contains_provider_panel(self) -> None:
        html = render_search_validation_dashboard(build_search_validation(online=False))
        self.assertIn("搜索 API 连通性验证", html)
        self.assertIn("Provider 验证明细", html)
        self.assertIn("中文公开入口解析自检", html)
        self.assertIn("baidu_public_html", html)
        self.assertIn("parser_ready", html)
        self.assertIn("安全边界", html)
        self.assertNotIn("API_KEY=", html)

    def test_cli_search_validate_generates_dashboard(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = root / "search.html"
            out = io.StringIO()
            with redirect_stdout(out):
                code = cli_main(
                    [
                        "--db",
                        str(root / "source_registry.sqlite"),
                        "search-validate",
                        "--offline",
                        "--output",
                        str(output),
                        "--json",
                    ]
                )
            self.assertEqual(code, 0)
            payload = json.loads(out.getvalue())
            self.assertEqual(payload["dashboard_path"], str(output))
            self.assertTrue(output.exists())

    def test_write_search_validation_dashboard_creates_html(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "search.html"
            result = write_search_validation_dashboard(output, online=False)
            self.assertEqual(result, str(output))
            self.assertTrue(output.exists())


if __name__ == "__main__":
    unittest.main()
