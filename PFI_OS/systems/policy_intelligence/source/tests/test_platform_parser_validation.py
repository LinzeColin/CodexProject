from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from source_registry.cli import main as cli_main
from source_registry.platform_parser_validation import (
    build_platform_parser_validation,
    render_platform_parser_validation_dashboard,
    write_platform_parser_validation_dashboard,
)


class PlatformParserValidationTest(unittest.TestCase):
    def test_validation_identifies_missing_keys_and_auth_without_secrets(self) -> None:
        report = build_platform_parser_validation()
        summary = report["summary"]
        statuses = {row["platform"]: row["validation_status"] for row in report["rows"]}
        self.assertEqual(summary["ready_search_provider_count"], 0)
        self.assertGreaterEqual(summary["missing_search_key_count"], 1)
        self.assertGreaterEqual(summary["missing_platform_auth_count"], 5)
        self.assertEqual(statuses["serpapi_bing_google"], "missing_search_key")
        self.assertEqual(statuses["douyin"], "missing_platform_auth")
        self.assertNotIn("SESSDATA=", json.dumps(report, ensure_ascii=False))
        self.assertNotIn("API_KEY=", json.dumps(report, ensure_ascii=False))

    def test_validation_uses_search_key_and_platform_auth_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            secrets = root / "search.json"
            secrets.write_text(json.dumps({"BING_SEARCH_API_KEY": "bing-secret-value"}), encoding="utf-8")
            cookie = root / "douyin_cookie.txt"
            cookie.write_text("douyin-cookie-secret", encoding="utf-8")
            auth = root / "auth.json"
            auth.write_text(
                json.dumps({"platforms": {"douyin": {"cookie_file": str(cookie)}}}),
                encoding="utf-8",
            )
            report = build_platform_parser_validation(
                search_secrets_file=secrets,
                platform_auth_file=auth,
            )
        rows = {row["platform"]: row for row in report["rows"]}
        encoded = json.dumps(report, ensure_ascii=False)
        self.assertIn(rows["serpapi_bing_google"]["validation_status"], {"current_ready", "current_partial"})
        self.assertEqual(rows["douyin"]["validation_status"], "implementation_pending_auth_ready")
        self.assertNotIn("bing-secret-value", encoded)
        self.assertNotIn("douyin-cookie-secret", encoded)
        self.assertNotIn(str(cookie), encoded)

    def test_render_dashboard_contains_acceptance_table(self) -> None:
        rendered = render_platform_parser_validation_dashboard(build_platform_parser_validation())
        self.assertIn("平台解析器验收 dashboard", rendered)
        self.assertIn("解析器验收明细", rendered)
        self.assertIn("缺搜索 key", rendered)
        self.assertIn("安全与合规边界", rendered)
        self.assertNotIn("secret-cookie-value", rendered)

    def test_write_dashboard_creates_html(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "parser_validation.html"
            result = write_platform_parser_validation_dashboard(output)
            self.assertEqual(result, str(output))
            self.assertTrue(output.exists())

    def test_cli_platform_parser_validate_generates_dashboard(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = root / "parser_validation.html"
            out = io.StringIO()
            with redirect_stdout(out):
                code = cli_main(
                    [
                        "--db",
                        str(root / "source_registry.sqlite"),
                        "platform-parser-validate",
                        "--output",
                        str(output),
                        "--json",
                    ]
                )
            self.assertEqual(code, 0)
            payload = json.loads(out.getvalue())
            self.assertEqual(payload["dashboard_path"], str(output))
            self.assertTrue(output.exists())
            self.assertGreaterEqual(payload["summary"]["parser_count"], 10)


if __name__ == "__main__":
    unittest.main()
