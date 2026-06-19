from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from source_registry.benchmark import (
    benchmark_model_rows,
    build_benchmark_status,
    render_benchmark_dashboard,
    write_benchmark_dashboard,
)
from source_registry.cli import main as cli_main


class BenchmarkTest(unittest.TestCase):
    def test_build_benchmark_status_contains_verified_sources(self) -> None:
        status = build_benchmark_status()
        summary = status["summary"]
        names = {item["name"] for item in status["models"]}
        self.assertGreaterEqual(summary["model_count"], 8)
        self.assertIn("PolicyInsight", names)
        self.assertIn("changedetection.io", names)
        self.assertIn("Heritrix3", names)
        self.assertIn("Scrapy", names)
        self.assertIn("Apache Tika", names)
        self.assertIn("GROBID", names)
        self.assertIn("Huginn", names)
        self.assertIn("Monity AI", names)
        self.assertGreaterEqual(summary["required_capability_count"], 10)
        self.assertTrue(any(row["capability"] == "authenticated_monitoring" for row in status["capability_rows"]))
        self.assertTrue(any(row["capability"] == "archival_crawl" for row in status["capability_rows"]))
        self.assertTrue(any(row["capability"] == "document_parsing" for row in status["capability_rows"]))
        self.assertGreaterEqual(summary["acceptance_check_count"], 8)

    def test_model_rows_are_sorted_and_sanitized(self) -> None:
        rows = benchmark_model_rows(limit=3)
        self.assertEqual(len(rows), 3)
        encoded = json.dumps(rows, ensure_ascii=False)
        self.assertIn("PolicyInsight", encoded)
        self.assertNotIn("API_KEY=", encoded)
        self.assertNotIn("SESSDATA=", encoded)

    def test_render_dashboard_contains_evidence_and_queue(self) -> None:
        rendered = render_benchmark_dashboard(build_benchmark_status())
        self.assertIn("开源/商业模型对标 dashboard", rendered)
        self.assertIn("证据来源矩阵", rendered)
        self.assertIn("吸收能力实施队列", rendered)
        self.assertIn("https://github.com/dgtlmoon/changedetection.io", rendered)
        self.assertIn("https://github.com/huginn/huginn", rendered)
        self.assertIn("https://github.com/internetarchive/heritrix3", rendered)
        self.assertIn("https://github.com/apache/tika", rendered)
        self.assertIn("验收标准", rendered)
        self.assertIn("合规边界", rendered)
        self.assertNotIn("sk-", rendered)

    def test_write_benchmark_dashboard_creates_html(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "benchmark.html"
            result = write_benchmark_dashboard(output)
            self.assertEqual(result, str(output))
            self.assertTrue(output.exists())
            self.assertIn("能力目标覆盖", output.read_text(encoding="utf-8"))

    def test_cli_benchmark_dashboard_generates_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = root / "benchmark.html"
            out = io.StringIO()
            with redirect_stdout(out):
                code = cli_main(
                    [
                        "--db",
                        str(root / "source_registry.sqlite"),
                        "benchmark-dashboard",
                        "--output",
                        str(output),
                        "--json",
                    ]
                )
            self.assertEqual(code, 0)
            payload = json.loads(out.getvalue())
            self.assertEqual(payload["dashboard_path"], str(output))
            self.assertGreaterEqual(payload["summary"]["model_count"], 8)
            self.assertTrue(output.exists())


if __name__ == "__main__":
    unittest.main()
