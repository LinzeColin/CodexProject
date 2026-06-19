from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from source_registry.attachment_parser_registry import (
    build_attachment_parser_status,
    probe_attachment_parser_dependencies,
    render_attachment_parser_dashboard,
    write_attachment_parser_dashboard,
)
from source_registry.cli import main as cli_main


class AttachmentParserRegistryTest(unittest.TestCase):
    def test_build_status_tracks_ready_partial_and_planned_parsers(self) -> None:
        status = build_attachment_parser_status()
        summary = status["summary"]
        parser_ids = {item["parser_id"] for item in status["parser_queue"]}
        self.assertGreaterEqual(summary["parser_count"], 7)
        self.assertGreaterEqual(summary["ready_count"], 3)
        self.assertGreaterEqual(summary["partial_count"], 4)
        self.assertGreaterEqual(summary["planned_count"], 0)
        self.assertIn("apache_tika_bridge", parser_ids)
        self.assertIn("grobid_research_pdf", parser_ids)
        self.assertIn("pdf", status["formats"])
        self.assertIn("docx", status["formats"])
        self.assertIn("xlsx", status["formats"])
        self.assertGreaterEqual(summary["acceptance_check_count"], 7)
        self.assertIn("dependency_ready_count", summary)
        self.assertIn("dependency_missing_count", summary)
        self.assertTrue(status["dependency_rows"])
        self.assertTrue(
            any(row["capability"] == "ocr_extraction" for row in status["capability_rows"])
        )
        self.assertTrue(
            any(row["capability"] == "legacy_office_extraction" for row in status["capability_rows"])
        )

    def test_render_dashboard_is_business_focused_and_sanitized(self) -> None:
        rendered = render_attachment_parser_dashboard(build_attachment_parser_status())
        self.assertIn("附件解析能力 dashboard", rendered)
        self.assertIn("能力覆盖矩阵", rendered)
        self.assertIn("运行依赖验收", rendered)
        self.assertIn("解析器业务价值", rendered)
        self.assertIn("实施队列与验收", rendered)
        self.assertIn("Apache Tika", rendered)
        self.assertIn("GROBID", rendered)
        self.assertIn("不展示正文、cookie、API key", rendered)
        self.assertNotIn("SESSDATA=", rendered)
        self.assertNotIn("API_KEY=", rendered)
        self.assertNotIn("sk-", rendered)

    def test_dependency_probe_is_deterministic_with_injected_checks(self) -> None:
        rows = probe_attachment_parser_dependencies(
            environ={"TIKA_SERVER_URL": "http://secret-tika.local"},
            module_available=lambda name: name in {"pypdf", "fitz", "PIL"},
            binary_available=lambda name: False,
        )
        by_id = {row["dependency"]: row for row in rows}
        self.assertEqual(by_id["pypdf"]["status"], "ready")
        self.assertEqual(by_id["pytesseract"]["status"], "missing")
        self.assertEqual(by_id["tesseract_binary"]["status"], "missing")
        self.assertEqual(by_id["apache_tika"]["status"], "configured_not_checked")
        self.assertEqual(by_id["grobid"]["status"], "missing")
        self.assertNotIn("secret-tika", json.dumps(rows, ensure_ascii=False))

    def test_status_accepts_dependency_probe_for_dashboard_testing(self) -> None:
        status = build_attachment_parser_status(
            dependency_probe=lambda: [
                {
                    "dependency": "tesseract_binary",
                    "label": "OCR engine",
                    "kind": "system_binary",
                    "status": "missing",
                    "business_value": "OCR",
                    "next_action": "安装 tesseract。",
                }
            ]
        )
        self.assertEqual(status["summary"]["dependency_missing_count"], 1)
        rendered = render_attachment_parser_dashboard(status)
        self.assertIn("安装 tesseract", rendered)

    def test_write_dashboard_creates_html(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "attachment_parser.html"
            result = write_attachment_parser_dashboard(output)
            self.assertEqual(result, str(output))
            self.assertTrue(output.exists())
            self.assertIn("格式覆盖", output.read_text(encoding="utf-8"))

    def test_cli_attachment_parsers_generates_dashboard(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = root / "attachment_parser.html"
            out = io.StringIO()
            with redirect_stdout(out):
                code = cli_main(
                    [
                        "--db",
                        str(root / "source_registry.sqlite"),
                        "attachment-parsers",
                        "--output",
                        str(output),
                        "--json",
                    ]
                )
            self.assertEqual(code, 0)
            payload = json.loads(out.getvalue())
            self.assertEqual(payload["dashboard_path"], str(output))
            self.assertGreaterEqual(payload["summary"]["parser_count"], 7)
            self.assertTrue(output.exists())


if __name__ == "__main__":
    unittest.main()
