from __future__ import annotations

import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import datetime, timezone
from pathlib import Path

from source_registry.cli import main as cli_main
from source_registry.credential_doctor import (
    build_credential_doctor,
    render_credential_doctor_dashboard,
    write_credential_doctor_dashboard,
)


class CredentialDoctorTest(unittest.TestCase):
    def test_missing_files_report_errors_without_secret_values(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = build_credential_doctor(secure_dir=Path(tmp) / "secure")
        self.assertEqual(report["overall_status"], "needs_fix")
        self.assertEqual(report["summary"]["errors"], 2)
        self.assertEqual(report["search_secrets"]["status"], "missing")
        self.assertNotIn("sk-", json.dumps(report, ensure_ascii=False))

    def test_ready_files_do_not_expose_secret_values_or_cookie_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            search = root / "secrets.json"
            search.write_text(
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
            os.chmod(search, 0o600)
            cookie = root / "bilibili_cookie.txt"
            cookie.write_text("SESSDATA=secret-cookie", encoding="utf-8")
            os.chmod(cookie, 0o600)
            auth = root / "platform_auth.json"
            auth.write_text(
                json.dumps({"platforms": {"bilibili": {"cookie_file": str(cookie)}}}),
                encoding="utf-8",
            )
            os.chmod(auth, 0o600)
            report = build_credential_doctor(
                search_secrets_file=search,
                platform_auth_file=auth,
                now=datetime.now(timezone.utc),
            )
        encoded = json.dumps(report, ensure_ascii=False)
        self.assertEqual(report["summary"]["search_ready"], 3)
        self.assertEqual(report["summary"]["platform_available"], 1)
        self.assertEqual(report["p0_gate"]["status"], "p0_complete")
        self.assertTrue(report["p0_gate"]["minimum_ready"])
        self.assertNotIn("serp-secret", encoded)
        self.assertNotIn("secret-cookie", encoded)
        self.assertNotIn("bilibili_cookie.txt", encoded)

    def test_p0_gate_blocks_until_search_and_bilibili_are_available(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            search = root / "secrets.json"
            search.write_text(json.dumps({"SERPAPI_API_KEY": "present"}), encoding="utf-8")
            os.chmod(search, 0o600)
            auth = root / "platform_auth.json"
            auth.write_text(json.dumps({"platforms": {}}), encoding="utf-8")
            os.chmod(auth, 0o600)
            report = build_credential_doctor(
                search_secrets_file=search,
                platform_auth_file=auth,
                now=datetime.now(timezone.utc),
            )
        self.assertEqual(report["p0_gate"]["status"], "p0_blocked")
        actions = [item["action"] for item in report["next_actions"]]
        self.assertIn("provide_bilibili_auth", actions)
        self.assertNotIn("fill_one_search_api", actions)

    def test_permission_too_open_is_warning(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            search = root / "secrets.json"
            search.write_text(json.dumps({"SERPAPI_API_KEY": "present"}), encoding="utf-8")
            os.chmod(search, 0o644)
            report = build_credential_doctor(search_secrets_file=search, platform_auth_file=root / "missing.json")
        self.assertEqual(report["search_secrets"]["status"], "permission_warning")
        self.assertGreaterEqual(report["summary"]["warnings"], 1)

    def test_render_credential_doctor_dashboard_contains_panels(self) -> None:
        report = build_credential_doctor(secure_dir="/tmp/no-such-policy-secure")
        rendered = render_credential_doctor_dashboard(report)
        self.assertIn("本地凭据体检", rendered)
        self.assertIn("搜索 API 体检", rendered)
        self.assertIn("P0 接入门槛", rendered)
        self.assertIn("业务价值", rendered)
        self.assertIn("平台授权体检", rendered)
        self.assertIn("安全边界", rendered)
        self.assertNotIn("SESSDATA=", rendered)

    def test_cli_credential_doctor_generates_dashboard(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_db = root / "source_registry.sqlite"
            output = root / "doctor.html"
            out = io.StringIO()
            with redirect_stdout(out):
                code = cli_main(
                    [
                        "--db",
                        str(source_db),
                        "credential-doctor",
                        "--secure-dir",
                        str(root / "secure"),
                        "--output",
                        str(output),
                        "--json",
                    ]
                )
            self.assertEqual(code, 0)
            payload = json.loads(out.getvalue())
            self.assertEqual(payload["dashboard_path"], str(output))
            self.assertTrue(output.exists())

    def test_write_credential_doctor_dashboard_creates_html(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "doctor.html"
            result = write_credential_doctor_dashboard(output, secure_dir=Path(tmp) / "secure")
            self.assertEqual(result, str(output))
            self.assertTrue(output.exists())


if __name__ == "__main__":
    unittest.main()
