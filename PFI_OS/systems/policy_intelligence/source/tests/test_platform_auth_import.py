from __future__ import annotations

import io
import json
import os
import stat
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from source_registry.cli import main as cli_main
from source_registry.platform_auth import platform_auth_state
from source_registry.platform_auth_import import (
    import_platform_auth_cookie,
    import_platform_auth_cookie_bundle,
    import_platform_auth_cookie_directory,
    import_platform_auth_session_reference,
)


class PlatformAuthImportTest(unittest.TestCase):
    def test_import_cookie_writes_private_file_and_updates_auth_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "exported_cookie.txt"
            source.write_text("SESSDATA=secret-cookie-value; DedeUserID=123", encoding="utf-8")
            auth = root / "policy-platform-auth.json"
            result = import_platform_auth_cookie(
                "bilibili",
                source_file=source,
                secure_dir=root,
                platform_auth_file=auth,
            )
            target = root / "cookies" / "bilibili_cookie.txt"
            payload = json.loads(auth.read_text(encoding="utf-8"))
            state = platform_auth_state("bilibili", auth)
            encoded = json.dumps(result, ensure_ascii=False)
            self.assertEqual(result["status"], "imported")
            self.assertEqual(result["marker_status"], "expected_marker_found")
            self.assertTrue(target.exists())
            self.assertEqual(stat.S_IMODE(target.stat().st_mode), 0o600)
            self.assertEqual(payload["platforms"]["bilibili"]["cookie_file"], str(target))
            self.assertTrue(state.available)
            self.assertNotIn("secret-cookie-value", encoded)
            self.assertNotIn(str(source), encoded)
            self.assertNotIn(str(target), encoded)
            self.assertNotIn(str(auth), encoded)

    def test_import_refuses_existing_target_without_force(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "cookie.txt"
            source.write_text("z_c0=secret-cookie-value", encoding="utf-8")
            import_platform_auth_cookie("zhihu", source_file=source, secure_dir=root)
            with self.assertRaises(ValueError):
                import_platform_auth_cookie("zhihu", source_file=source, secure_dir=root)

    def test_import_cookie_from_environment_without_printing_value(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            old = os.environ.get("POLICY_TEST_WEIBO_COOKIE")
            os.environ["POLICY_TEST_WEIBO_COOKIE"] = "SUB=secret-cookie-value"
            try:
                result = import_platform_auth_cookie("weibo", cookie_env="POLICY_TEST_WEIBO_COOKIE", secure_dir=root)
            finally:
                if old is None:
                    os.environ.pop("POLICY_TEST_WEIBO_COOKIE", None)
                else:
                    os.environ["POLICY_TEST_WEIBO_COOKIE"] = old
        self.assertEqual(result["status"], "imported")
        self.assertNotIn("secret-cookie-value", json.dumps(result, ensure_ascii=False))

    def test_cli_platform_auth_import_outputs_sanitized_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "bili_cookie.txt"
            source.write_text("SESSDATA=secret-cookie-value", encoding="utf-8")
            out = io.StringIO()
            with redirect_stdout(out):
                code = cli_main(
                    [
                        "--db",
                        str(root / "source_registry.sqlite"),
                        "platform-auth-import",
                        "--platform",
                        "bilibili",
                        "--source-file",
                        str(source),
                        "--secure-dir",
                        str(root),
                        "--json",
                    ]
                )
            payload = json.loads(out.getvalue())
        self.assertEqual(code, 0)
        self.assertEqual(payload["platform"], "bilibili")
        self.assertNotIn("secret-cookie-value", out.getvalue())
        self.assertNotIn(str(source), out.getvalue())

    def test_bulk_import_directory_imports_matching_platform_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_dir = root / "incoming"
            source_dir.mkdir()
            (source_dir / "bilibili_cookie.txt").write_text("SESSDATA=secret-cookie-value", encoding="utf-8")
            (source_dir / "zhihu_cookie.txt").write_text("z_c0=secret-cookie-value", encoding="utf-8")
            auth = root / "policy-platform-auth.json"
            result = import_platform_auth_cookie_directory(
                source_dir,
                platforms=["bilibili", "zhihu", "weibo"],
                secure_dir=root,
                platform_auth_file=auth,
            )
            payload = json.loads(auth.read_text(encoding="utf-8"))
            encoded = json.dumps(result, ensure_ascii=False)
        self.assertEqual(result["imported_count"], 2)
        self.assertEqual(result["missing_platforms"], ["weibo"])
        self.assertIn("bilibili", payload["platforms"])
        self.assertIn("zhihu", payload["platforms"])
        self.assertNotIn("secret-cookie-value", encoded)
        self.assertNotIn(str(source_dir), encoded)

    def test_bulk_import_dry_run_does_not_write_auth_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_dir = root / "incoming"
            source_dir.mkdir()
            (source_dir / "weibo_cookie.txt").write_text("SUB=secret-cookie-value", encoding="utf-8")
            auth = root / "policy-platform-auth.json"
            result = import_platform_auth_cookie_directory(
                source_dir,
                platforms=["weibo"],
                secure_dir=root,
                platform_auth_file=auth,
                dry_run=True,
            )
        self.assertEqual(result["status"], "dry_run")
        self.assertEqual(result["imported_count"], 1)
        self.assertFalse(auth.exists())

    def test_import_chrome_session_reference_updates_auth_without_copying_session(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = root / "ChromeProfile"
            profile.mkdir()
            auth = root / "policy-platform-auth.json"
            auth.write_text(
                json.dumps({"platforms": {"douyin": {"auth_method": "cookie_file", "cookie_file": str(root / "cookies" / "douyin_cookie.txt")}}}),
                encoding="utf-8",
            )
            result = import_platform_auth_session_reference(
                "douyin",
                session_file=profile,
                secure_dir=root,
                platform_auth_file=auth,
            )
            payload = json.loads(auth.read_text(encoding="utf-8"))
            state = platform_auth_state("douyin", auth)
            encoded = json.dumps(result, ensure_ascii=False)

        self.assertEqual(result["status"], "session_reference_imported")
        self.assertEqual(result["auth_method"], "chrome_profile_reference")
        self.assertEqual(payload["platforms"]["douyin"]["chrome_profile_dir"], str(profile))
        self.assertNotIn("cookie_file", payload["platforms"]["douyin"])
        self.assertTrue(state.available)
        self.assertFalse(state.as_metadata()["collector_ready"])
        self.assertNotIn(str(profile), encoded)
        self.assertNotIn(str(auth), encoded)

    def test_cli_platform_auth_session_import_outputs_sanitized_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            session = root / "storage_state.json"
            session.write_text('{"cookies":[]}', encoding="utf-8")
            out = io.StringIO()
            with redirect_stdout(out):
                code = cli_main(
                    [
                        "--db",
                        str(root / "source_registry.sqlite"),
                        "platform-auth-session-import",
                        "--platform",
                        "zhihu",
                        "--session-file",
                        str(session),
                        "--secure-dir",
                        str(root),
                        "--json",
                    ]
                )
            payload = json.loads(out.getvalue())

        self.assertEqual(code, 0)
        self.assertEqual(payload["platform"], "zhihu")
        self.assertEqual(payload["session_reference"], "<chrome_session_file>")
        self.assertFalse(payload["collector_ready"])
        self.assertNotIn(str(session), out.getvalue())

    def test_cli_platform_auth_bulk_import_outputs_sanitized_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_dir = root / "incoming"
            source_dir.mkdir()
            (source_dir / "toutiao_cookie.txt").write_text("sessionid=secret-cookie-value", encoding="utf-8")
            out = io.StringIO()
            with redirect_stdout(out):
                code = cli_main(
                    [
                        "--db",
                        str(root / "source_registry.sqlite"),
                        "platform-auth-bulk-import",
                        "--source-dir",
                        str(source_dir),
                        "--platform",
                        "toutiao",
                        "--secure-dir",
                        str(root),
                        "--json",
                    ]
                )
            payload = json.loads(out.getvalue())
        self.assertEqual(code, 0)
        self.assertEqual(payload["imported_count"], 1)
        self.assertEqual(payload["results"][0]["platform"], "toutiao")
        self.assertNotIn("secret-cookie-value", out.getvalue())
        self.assertNotIn(str(source_dir), out.getvalue())

    def test_bundle_import_imports_platform_cookie_paths_without_exposing_values(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bili = root / "bili_cookie.txt"
            zhihu = root / "zhihu_cookie.txt"
            bundle = root / "platform_auth_bundle.json"
            auth = root / "policy-platform-auth.json"
            bili.write_text("SESSDATA=secret-cookie-value", encoding="utf-8")
            zhihu.write_text("z_c0=secret-cookie-value", encoding="utf-8")
            bundle.write_text(
                json.dumps(
                    {
                        "bilibili": {"cookie_file": str(bili)},
                        "platforms": {"zhihu": str(zhihu)},
                    }
                ),
                encoding="utf-8",
            )
            result = import_platform_auth_cookie_bundle(
                bundle,
                platforms=["bilibili", "zhihu", "weibo"],
                secure_dir=root,
                platform_auth_file=auth,
            )
            payload = json.loads(auth.read_text(encoding="utf-8"))
            encoded = json.dumps(result, ensure_ascii=False)

        self.assertEqual(result["imported_count"], 2)
        self.assertEqual(result["missing_platforms"], ["weibo"])
        self.assertIn("bilibili", payload["platforms"])
        self.assertIn("zhihu", payload["platforms"])
        self.assertNotIn("secret-cookie-value", encoded)
        self.assertNotIn(str(bundle), encoded)
        self.assertNotIn(str(bili), encoded)
        self.assertNotIn(str(zhihu), encoded)

    def test_bundle_import_accepts_chrome_session_reference(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = root / "ChromeProfile"
            profile.mkdir()
            bundle = root / "platform_auth_bundle.json"
            auth = root / "policy-platform-auth.json"
            bundle.write_text(
                json.dumps({"platforms": {"douyin": {"chrome_profile_dir": str(profile)}}}),
                encoding="utf-8",
            )
            result = import_platform_auth_cookie_bundle(
                bundle,
                platforms=["douyin"],
                secure_dir=root,
                platform_auth_file=auth,
            )
            payload = json.loads(auth.read_text(encoding="utf-8"))
            encoded = json.dumps(result, ensure_ascii=False)

        self.assertEqual(result["imported_count"], 1)
        self.assertEqual(result["results"][0]["status"], "session_reference_imported")
        self.assertEqual(payload["platforms"]["douyin"]["auth_method"], "chrome_profile_reference")
        self.assertNotIn(str(profile), encoded)
        self.assertNotIn(str(bundle), encoded)

    def test_cli_platform_auth_bundle_import_outputs_sanitized_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "weibo_cookie.txt"
            bundle = root / "platform_auth_bundle.json"
            source.write_text("SUB=secret-cookie-value", encoding="utf-8")
            bundle.write_text(json.dumps({"weibo": str(source)}), encoding="utf-8")
            out = io.StringIO()
            with redirect_stdout(out):
                code = cli_main(
                    [
                        "--db",
                        str(root / "source_registry.sqlite"),
                        "platform-auth-bundle-import",
                        "--source-file",
                        str(bundle),
                        "--platform",
                        "weibo",
                        "--secure-dir",
                        str(root),
                        "--json",
                    ]
                )
            payload = json.loads(out.getvalue())

        self.assertEqual(code, 0)
        self.assertEqual(payload["imported_count"], 1)
        self.assertEqual(payload["results"][0]["platform"], "weibo")
        self.assertNotIn("secret-cookie-value", out.getvalue())
        self.assertNotIn(str(bundle), out.getvalue())
        self.assertNotIn(str(source), out.getvalue())


if __name__ == "__main__":
    unittest.main()
