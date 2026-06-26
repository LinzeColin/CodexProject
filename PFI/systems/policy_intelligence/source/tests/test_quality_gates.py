from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from source_registry.cli import main as cli_main
from source_registry.content_db import begin_run, complete_run, connect_content, init_content_database
from source_registry.quality_gates import (
    build_quality_gate_status,
    load_quality_rules,
    quality_rule_thresholds,
    render_quality_gates_dashboard,
    write_quality_gates_dashboard,
)


class QualityGatesTest(unittest.TestCase):
    def test_load_quality_rules_and_thresholds(self) -> None:
        rules = load_quality_rules()
        thresholds = quality_rule_thresholds()
        self.assertEqual(rules["version"], "quality-gates-v1")
        self.assertEqual(thresholds["external_reference_count"], 5)
        self.assertEqual(thresholds["external_platform_count"], 2)
        self.assertEqual(thresholds["business_value_density_score"], 95)
        self.assertGreaterEqual(len(rules["compliance_guardrails"]), 5)

    def test_build_quality_gate_status_pass_fail_not_checked(self) -> None:
        status = build_quality_gate_status(
            metrics={
                "external_reference_count": 5,
                "external_platform_count": 1,
                "report_document_count": 1,
                "primary_report_suffix": ".pdf",
                "deep_chapter_count": 10,
                "business_value_density_score": 96,
            }
        )
        rows = {item["id"]: item for item in status["gate_results"]}
        self.assertEqual(rows["external_references_minimum"]["status"], "passed")
        self.assertEqual(rows["external_platforms_minimum"]["status"], "failed")
        self.assertEqual(rows["business_value_density"]["status"], "passed")
        self.assertEqual(rows["pdf_body_pages"]["status"], "not_checked")
        self.assertEqual(status["summary"]["failed_count"], 1)

    def test_render_quality_gates_dashboard_contains_guardrails(self) -> None:
        rendered = render_quality_gates_dashboard(build_quality_gate_status(metrics={}))
        self.assertIn("报告质量门槛规则 dashboard", rendered)
        self.assertIn("硬门槛明细", rendered)
        self.assertIn("商务高价值信息密度", rendered)
        self.assertIn("不绕过验证码", rendered)
        self.assertIn("not_checked", rendered)
        self.assertNotIn("SESSDATA=", rendered)

    def test_write_quality_gates_dashboard_creates_html(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "quality.html"
            result = write_quality_gates_dashboard(output, metrics={"external_reference_count": 5})
            self.assertEqual(result, str(output))
            self.assertTrue(output.exists())
            self.assertIn("合规护栏", output.read_text(encoding="utf-8"))

    def test_cli_quality_gates_generates_dashboard(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            content_db = root / "policy_documents.sqlite"
            conn = connect_content(content_db)
            init_content_database(conn)
            begin_run(conn, "2026060401", "automation")
            complete_run(
                conn,
                "2026060401",
                "completed",
                "reports/sample.pdf",
                {
                    "sources_considered": 1,
                    "pages_fetched": 1,
                    "documents_discovered": 1,
                    "new_documents": 1,
                    "analyzed_documents": 1,
                },
            )
            conn.close()
            output = root / "quality.html"
            out = io.StringIO()
            with redirect_stdout(out):
                code = cli_main(
                    [
                        "--db",
                        str(root / "source_registry.sqlite"),
                        "quality-gates",
                        "--content-db",
                        str(content_db),
                        "--data-dir",
                        str(root / "data"),
                        "--output",
                        str(output),
                        "--json",
                    ]
                )
            self.assertEqual(code, 0)
            payload = json.loads(out.getvalue())
            self.assertEqual(payload["dashboard_path"], str(output))
            self.assertGreaterEqual(payload["summary"]["hard_gate_count"], 6)
            self.assertTrue(output.exists())


if __name__ == "__main__":
    unittest.main()
