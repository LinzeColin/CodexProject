from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from source_registry.cli import main as cli_main
from source_registry.platform_parser_registry import (
    build_platform_parser_status,
    render_platform_parser_dashboard,
    write_platform_parser_dashboard,
)


class PlatformParserRegistryTest(unittest.TestCase):
    def test_build_status_contains_core_platform_capabilities(self) -> None:
        status = build_platform_parser_status()
        summary = status["summary"]
        platforms = {item["platform"] for item in status["parser_queue"]}
        self.assertGreaterEqual(summary["parser_count"], 10)
        self.assertGreaterEqual(summary["platform_count"], 8)
        self.assertGreaterEqual(summary["partial_count"], 3)
        self.assertGreaterEqual(summary["planned_count"], 6)
        self.assertIn("bilibili", platforms)
        self.assertIn("douyin", platforms)
        self.assertIn("wechat", platforms)
        self.assertTrue(any(row["capability"] == "subtitle_extraction" for row in status["capability_rows"]))
        self.assertTrue(any(row["capability"] == "interaction_metrics" for row in status["capability_rows"]))
        self.assertGreaterEqual(summary["acceptance_check_count"], 10)

    def test_render_dashboard_is_sanitized(self) -> None:
        rendered = render_platform_parser_dashboard(build_platform_parser_status())
        self.assertIn("平台解析器能力 dashboard", rendered)
        self.assertIn("能力覆盖矩阵", rendered)
        self.assertIn("平台能力摘要", rendered)
        self.assertIn("解析器实施队列", rendered)
        self.assertIn("B站公开视频解析器", rendered)
        self.assertIn("抖音授权视频解析器", rendered)
        self.assertNotIn("SESSDATA=", rendered)
        self.assertNotIn("API_KEY=", rendered)
        self.assertNotIn("sk-", rendered)

    def test_write_dashboard_creates_html(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "platform_parser.html"
            result = write_platform_parser_dashboard(output)
            self.assertEqual(result, str(output))
            self.assertTrue(output.exists())
            self.assertIn("合规边界", output.read_text(encoding="utf-8"))

    def test_cli_platform_parsers_generates_dashboard(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = root / "platform_parser.html"
            out = io.StringIO()
            with redirect_stdout(out):
                code = cli_main(
                    [
                        "--db",
                        str(root / "source_registry.sqlite"),
                        "platform-parsers",
                        "--output",
                        str(output),
                        "--json",
                    ]
                )
            self.assertEqual(code, 0)
            payload = json.loads(out.getvalue())
            self.assertEqual(payload["dashboard_path"], str(output))
            self.assertGreaterEqual(payload["summary"]["parser_count"], 10)
            self.assertTrue(output.exists())


if __name__ == "__main__":
    unittest.main()
