from __future__ import annotations

import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from source_registry.cli import main as cli_main
from source_registry.platform_auth_intake import (
    build_platform_auth_intake,
    render_platform_auth_intake_dashboard,
    write_platform_auth_intake_dashboard,
)


class PlatformAuthIntakeTest(unittest.TestCase):
    def test_build_platform_auth_intake_prioritizes_bilibili_without_secret_values(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cookie_dir = root / "cookies"
            cookie_dir.mkdir()
            cookie = cookie_dir / "bilibili_cookie.txt"
            cookie.write_text("SESSDATA=secret-cookie-value", encoding="utf-8")
            os.chmod(cookie, 0o600)
            auth = root / "platform_auth.json"
            auth.write_text(
                json.dumps({"platforms": {"bilibili": {"auth_method": "cookie_file", "cookie_file": str(cookie)}}}),
                encoding="utf-8",
            )
            report = build_platform_auth_intake(secure_dir=root, platform_auth_file=auth)
        encoded = json.dumps(report, ensure_ascii=False)
        bilibili = next(row for row in report["platforms"] if row["platform"] == "bilibili")
        self.assertEqual(bilibili["priority"], "P0")
        self.assertTrue(bilibili["available"])
        self.assertTrue(bilibili["collector_ready"])
        self.assertEqual(report["summary"]["p0_ready"], 1)
        self.assertEqual(report["summary"]["collector_ready_count"], 1)
        self.assertNotIn("secret-cookie-value", encoded)
        self.assertNotIn(str(cookie), encoded)

    def test_chrome_session_reference_is_session_only_in_intake(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = root / "ChromeProfile"
            profile.mkdir()
            auth = root / "platform_auth.json"
            auth.write_text(
                json.dumps({"platforms": {"douyin": {"chrome_profile_dir": str(profile)}}}),
                encoding="utf-8",
            )
            report = build_platform_auth_intake(secure_dir=root, platform_auth_file=auth)
        douyin = next(row for row in report["platforms"] if row["platform"] == "douyin")
        encoded = json.dumps(report, ensure_ascii=False)
        self.assertTrue(douyin["available"])
        self.assertFalse(douyin["collector_ready"])
        self.assertTrue(douyin["session_only"])
        self.assertEqual(douyin["status"], "session_only")
        self.assertEqual(report["summary"]["session_only_count"], 1)
        self.assertIn("platform-auth-session-import", encoded)
        self.assertNotIn(str(profile), encoded)

    def test_render_platform_auth_intake_dashboard_contains_checklist(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            auth = root / "platform_auth.json"
            auth.write_text(
                json.dumps(
                    {
                        "platforms": {
                            platform: {"auth_method": "cookie_file", "cookie_file": str(root / "cookies" / f"{platform}_cookie.txt")}
                            for platform in ["bilibili", "douyin", "kuaishou", "weibo", "zhihu", "wechat", "xiaohongshu", "toutiao"]
                        }
                    }
                ),
                encoding="utf-8",
            )
            report = build_platform_auth_intake(secure_dir=root, platform_auth_file=auth)
        self.assertEqual(report["summary"]["missing_file_count"], 8)
        rendered = render_platform_auth_intake_dashboard(report)
        self.assertIn("平台授权接入清单", rendered)
        self.assertIn("接入清单", rendered)
        self.assertIn("P0", rendered)
        self.assertIn("B站", rendered)
        self.assertIn("导入命令", rendered)
        self.assertIn("platform-auth-import", rendered)
        self.assertIn("platform-auth-bulk-import", rendered)
        self.assertIn("platform-auth-bundle-import", rendered)
        self.assertIn("platform-auth-session-import", rendered)
        self.assertIn("验收命令", rendered)
        self.assertNotIn("SESSDATA=", rendered)
        self.assertNotIn("secret-cookie-value", rendered)

    def test_write_platform_auth_intake_dashboard_creates_html(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "intake.html"
            result = write_platform_auth_intake_dashboard(output, secure_dir=Path(tmp) / "secure")
            self.assertEqual(result, str(output))
            self.assertTrue(output.exists())

    def test_cli_platform_auth_intake_generates_dashboard(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "intake.html"
            out = io.StringIO()
            with redirect_stdout(out):
                code = cli_main(
                    [
                        "--db",
                        str(Path(tmp) / "source_registry.sqlite"),
                        "platform-auth-intake",
                        "--secure-dir",
                        str(Path(tmp) / "secure"),
                        "--output",
                        str(output),
                        "--json",
                    ]
                )
            self.assertEqual(code, 0)
            payload = json.loads(out.getvalue())
            self.assertEqual(payload["dashboard_path"], str(output))
            self.assertEqual(payload["summary"]["total"], 8)
            self.assertTrue(output.exists())


if __name__ == "__main__":
    unittest.main()
