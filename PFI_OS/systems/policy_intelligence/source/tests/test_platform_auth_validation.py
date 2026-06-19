from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from source_registry.cli import main as cli_main
from source_registry.platform_auth_validation import (
    build_platform_auth_validation,
    render_platform_auth_validation_dashboard,
    write_platform_auth_validation_dashboard,
)


class PlatformAuthValidationTest(unittest.TestCase):
    def test_offline_missing_auth_is_sanitized(self) -> None:
        report = build_platform_auth_validation(online=False)
        self.assertEqual(report["mode"], "offline")
        self.assertEqual(report["summary"]["missing_count"], 8)
        self.assertEqual(report["summary"]["online_checked_count"], 0)
        self.assertNotIn("cookie=", json.dumps(report, ensure_ascii=False).lower())

    def test_offline_available_cookie_does_not_expose_secret_or_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cookie = root / "bilibili_cookie.txt"
            cookie.write_text("SESSDATA=secret-cookie-value", encoding="utf-8")
            auth = root / "auth.json"
            auth.write_text(
                json.dumps({"platforms": {"bilibili": {"cookie_file": str(cookie)}}}),
                encoding="utf-8",
            )
            report = build_platform_auth_validation(platform_auth_file=auth, platforms=["bilibili"], online=False)
        row = report["platforms"][0]
        encoded = json.dumps(report, ensure_ascii=False)
        self.assertEqual(row["status"], "available_offline")
        self.assertTrue(row["available"])
        self.assertNotIn("secret-cookie-value", encoded)
        self.assertNotIn(str(cookie), encoded)

    def test_online_bilibili_success(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cookie = root / "bilibili_cookie.txt"
            cookie.write_text("SESSDATA=secret-cookie-value", encoding="utf-8")
            auth = root / "auth.json"
            auth.write_text(
                json.dumps({"platforms": {"bilibili": {"cookie_file": str(cookie)}}}),
                encoding="utf-8",
            )

            def fake_fetcher(cookie_file: str, timeout: int, allow_insecure_tls: bool, retries: int):
                self.assertEqual(cookie_file, str(cookie))
                return {"code": 0, "data": {"isLogin": True}}, "ok"

            report = build_platform_auth_validation(
                platform_auth_file=auth,
                platforms=["bilibili"],
                online=True,
                bilibili_nav_fetcher=fake_fetcher,
            )
        row = report["platforms"][0]
        self.assertEqual(row["status"], "passed")
        self.assertTrue(row["online_checked"])
        self.assertEqual(report["summary"]["passed_count"], 1)

    def test_online_bilibili_expired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cookie = root / "bilibili_cookie.txt"
            cookie.write_text("SESSDATA=old-cookie", encoding="utf-8")
            auth = root / "auth.json"
            auth.write_text(
                json.dumps({"platforms": {"bilibili": {"cookie_file": str(cookie)}}}),
                encoding="utf-8",
            )

            def fake_fetcher(cookie_file: str, timeout: int, allow_insecure_tls: bool, retries: int):
                return {"code": 0, "data": {"isLogin": False}}, "ok"

            report = build_platform_auth_validation(
                platform_auth_file=auth,
                platforms=["bilibili"],
                online=True,
                bilibili_nav_fetcher=fake_fetcher,
            )
        self.assertEqual(report["platforms"][0]["status"], "login_expired")
        self.assertEqual(report["summary"]["failed_count"], 1)

    def test_online_non_bilibili_without_validation_url_is_pending(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cookie = root / "zhihu_cookie.txt"
            cookie.write_text("z_c0=secret", encoding="utf-8")
            auth = root / "auth.json"
            auth.write_text(
                json.dumps({"platforms": {"zhihu": {"cookie_file": str(cookie)}}}),
                encoding="utf-8",
            )
            report = build_platform_auth_validation(platform_auth_file=auth, platforms=["zhihu"], online=True)
        row = report["platforms"][0]
        self.assertEqual(row["status"], "online_validator_pending")
        self.assertFalse(row["online_checked"])
        self.assertEqual(report["summary"]["pending_validator_count"], 1)

    def test_online_session_only_auth_is_pending_not_passed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = root / "ChromeProfile"
            profile.mkdir()
            auth = root / "auth.json"
            auth.write_text(
                json.dumps({"platforms": {"douyin": {"chrome_profile_dir": str(profile)}}}),
                encoding="utf-8",
            )
            report = build_platform_auth_validation(platform_auth_file=auth, platforms=["douyin"], online=True)
        row = report["platforms"][0]
        encoded = json.dumps(report, ensure_ascii=False)
        self.assertTrue(row["available"])
        self.assertEqual(row["credential_type"], "session_file")
        self.assertEqual(row["status"], "online_validator_pending")
        self.assertEqual(row["validation_scope"], "cookie_file_required_for_generic_validation")
        self.assertEqual(report["summary"]["pending_validator_count"], 1)
        self.assertNotIn(str(profile), encoded)

    def test_online_generic_platform_validation_success(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cookie = root / "zhihu_cookie.txt"
            cookie.write_text("z_c0=secret-cookie-value", encoding="utf-8")
            auth = root / "auth.json"
            auth.write_text(
                json.dumps(
                    {
                        "platforms": {
                            "zhihu": {
                                "cookie_file": str(cookie),
                                "validation_url": "https://www.zhihu.com/",
                                "success_markers": ["知乎首页"],
                                "login_required_markers": ["登录"],
                                "captcha_markers": ["验证码"],
                            }
                        }
                    }
                ),
                encoding="utf-8",
            )

            def fake_fetcher(cookie_file: str, url: str, timeout: int, allow_insecure_tls: bool, retries: int):
                self.assertEqual(cookie_file, str(cookie))
                self.assertEqual(url, "https://www.zhihu.com/")
                return "欢迎进入知乎首页", "ok"

            report = build_platform_auth_validation(
                platform_auth_file=auth,
                platforms=["zhihu"],
                online=True,
                generic_page_fetcher=fake_fetcher,
            )
        row = report["platforms"][0]
        encoded = json.dumps(report, ensure_ascii=False)
        self.assertEqual(row["status"], "passed")
        self.assertTrue(row["online_checked"])
        self.assertEqual(row["validation_scope"], "configured_validation_url")
        self.assertEqual(report["summary"]["passed_count"], 1)
        self.assertNotIn("secret-cookie-value", encoded)
        self.assertNotIn(str(cookie), encoded)

    def test_online_generic_platform_detects_login_or_captcha(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cookie = root / "weibo_cookie.txt"
            cookie.write_text("SUB=secret-cookie-value", encoding="utf-8")
            auth = root / "auth.json"
            auth.write_text(
                json.dumps(
                    {
                        "platforms": {
                            "weibo": {
                                "cookie_file": str(cookie),
                                "validation_url": "https://weibo.com/",
                                "success_markers": ["我的首页"],
                                "login_required_markers": ["登录"],
                                "captcha_markers": ["安全验证"],
                            }
                        }
                    }
                ),
                encoding="utf-8",
            )

            def login_fetcher(cookie_file: str, url: str, timeout: int, allow_insecure_tls: bool, retries: int):
                return "请先登录", "ok"

            login_report = build_platform_auth_validation(
                platform_auth_file=auth,
                platforms=["weibo"],
                online=True,
                generic_page_fetcher=login_fetcher,
            )

            def captcha_fetcher(cookie_file: str, url: str, timeout: int, allow_insecure_tls: bool, retries: int):
                return "安全验证", "ok"

            captcha_report = build_platform_auth_validation(
                platform_auth_file=auth,
                platforms=["weibo"],
                online=True,
                generic_page_fetcher=captcha_fetcher,
            )
        self.assertEqual(login_report["platforms"][0]["status"], "login_expired")
        self.assertEqual(captcha_report["platforms"][0]["status"], "captcha_or_security_check")
        self.assertEqual(captcha_report["summary"]["failed_count"], 1)

    def test_render_dashboard_contains_platform_panel(self) -> None:
        rendered = render_platform_auth_validation_dashboard(build_platform_auth_validation(online=False))
        self.assertIn("平台授权连通性验证", rendered)
        self.assertIn("平台授权验证明细", rendered)
        self.assertIn("安全与合规边界", rendered)
        self.assertIn("B站", rendered)
        self.assertNotIn("SESSDATA=", rendered)

    def test_write_platform_auth_validation_dashboard_creates_html(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "platform_auth.html"
            result = write_platform_auth_validation_dashboard(output, online=False)
            self.assertEqual(result, str(output))
            self.assertTrue(output.exists())

    def test_cli_platform_auth_validate_generates_dashboard(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = root / "platform_auth.html"
            out = io.StringIO()
            with redirect_stdout(out):
                code = cli_main(
                    [
                        "--db",
                        str(root / "source_registry.sqlite"),
                        "platform-auth-validate",
                        "--output",
                        str(output),
                        "--json",
                    ]
                )
            self.assertEqual(code, 0)
            payload = json.loads(out.getvalue())
            self.assertEqual(payload["dashboard_path"], str(output))
            self.assertTrue(output.exists())


if __name__ == "__main__":
    unittest.main()
