from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from source_registry.cli import main as cli_main
from source_registry.search_secret_intake import (
    build_search_secret_intake,
    render_search_secret_intake_dashboard,
    write_search_secret_intake_dashboard,
)


class SearchSecretIntakeTest(unittest.TestCase):
    def test_build_search_secret_intake_has_import_commands_without_secrets(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            secrets = root / "policy-search-secrets.json"
            secrets.write_text(
                json.dumps({"BING_SEARCH_API_KEY": "bing-secret-value-123"}),
                encoding="utf-8",
            )
            report = build_search_secret_intake(secure_dir=root, search_secrets_file=secrets)
        encoded = json.dumps(report, ensure_ascii=False)
        self.assertEqual(report["summary"]["ready_count"], 1)
        self.assertTrue(report["summary"]["p0_minimum_ready"])
        self.assertIn("bulk_import_keys", report["commands"])
        self.assertIn("search-secret-bulk-import", report["commands"]["bulk_import_keys"])
        self.assertIn("import_bing_key", report["commands"])
        self.assertIn("import_google_cse", report["commands"])
        self.assertNotIn("bing-secret-value-123", encoded)
        self.assertNotIn(str(secrets), encoded)

    def test_render_search_secret_intake_dashboard_contains_checklist(self) -> None:
        report = build_search_secret_intake(secure_dir="/tmp/no-such-policy-secure")
        rendered = render_search_secret_intake_dashboard(report)
        self.assertIn("搜索 API 接入清单", rendered)
        self.assertIn("Provider 接入清单", rendered)
        self.assertIn("search-secret-import", rendered)
        self.assertIn("search-secret-bulk-import", rendered)
        self.assertIn("Google CSE", rendered)
        self.assertNotIn("API_KEY=", rendered)
        self.assertNotIn("secret-value", rendered)

    def test_write_search_secret_intake_dashboard_creates_html(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "search_intake.html"
            result = write_search_secret_intake_dashboard(output, secure_dir=Path(tmp) / "secure")
            self.assertEqual(result, str(output))
            self.assertTrue(output.exists())

    def test_cli_search_secret_intake_generates_dashboard(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "search_intake.html"
            out = io.StringIO()
            with redirect_stdout(out):
                code = cli_main(
                    [
                        "--db",
                        str(Path(tmp) / "source_registry.sqlite"),
                        "search-secret-intake",
                        "--secure-dir",
                        str(Path(tmp) / "secure"),
                        "--output",
                        str(output),
                        "--json",
                    ]
                )
            payload = json.loads(out.getvalue())
            self.assertEqual(code, 0)
            self.assertEqual(payload["dashboard_path"], str(output))
            self.assertEqual(payload["summary"]["total"], 3)
            self.assertTrue(output.exists())


if __name__ == "__main__":
    unittest.main()
