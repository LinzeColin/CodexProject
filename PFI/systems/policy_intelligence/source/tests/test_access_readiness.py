from __future__ import annotations

import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import datetime, timezone
from pathlib import Path

from source_registry.access_readiness import (
    build_access_readiness,
    render_access_readiness_dashboard,
    write_access_readiness_dashboard,
)
from source_registry.cli import main as cli_main
from source_registry.content_db import connect_content, init_content_database


class AccessReadinessTest(unittest.TestCase):
    def test_missing_access_inputs_are_blocked_and_sanitized(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            content_conn = connect_content(root / "policy_documents.sqlite")
            init_content_database(content_conn)
            source_config = _write_chinese_source_config(root)
            report = build_access_readiness(
                content_conn=content_conn,
                search_secrets_file=root / "missing-search.json",
                platform_auth_file=root / "missing-auth.json",
                interpretation_source_file=source_config,
            )
            content_conn.close()
        encoded = json.dumps(report, ensure_ascii=False)
        self.assertEqual(report["overall_status"], "blocked")
        self.assertEqual(report["summary"]["search_ready"], 0)
        self.assertEqual(report["summary"]["bilibili_status"], "missing")
        self.assertEqual(report["summary"]["chinese_search_ready"], 3)
        self.assertGreaterEqual(report["summary"]["failed_tiers"], 1)
        self.assertIn("search-secret-bulk-import", report["commands"]["import_search_bundle"])
        self.assertIn("platform-auth-bundle-import", report["commands"]["import_platform_bundle"])
        self.assertNotIn("SESSDATA", encoded)
        self.assertNotIn("API_KEY=", encoded)

    def test_p0_ready_when_search_and_bilibili_are_available(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            search = root / "search.json"
            search.write_text(json.dumps({"SERPAPI_API_KEY": "serp-secret-value-123"}), encoding="utf-8")
            os.chmod(search, 0o600)
            cookie = root / "bilibili_cookie.txt"
            cookie.write_text("SESSDATA=secret-cookie-value", encoding="utf-8")
            os.chmod(cookie, 0o600)
            auth = root / "auth.json"
            auth.write_text(
                json.dumps({"platforms": {"bilibili": {"cookie_file": str(cookie)}}}),
                encoding="utf-8",
            )
            os.chmod(auth, 0o600)
            content_conn = connect_content(root / "policy_documents.sqlite")
            init_content_database(content_conn)
            report = build_access_readiness(
                content_conn=content_conn,
                search_secrets_file=search,
                platform_auth_file=auth,
                interpretation_source_file=_write_chinese_source_config(root),
            )
            content_conn.close()
        encoded = json.dumps(report, ensure_ascii=False)
        self.assertEqual(report["summary"]["search_ready"], 1)
        self.assertEqual(report["summary"]["bilibili_status"], "ready")
        self.assertIn(report["summary"]["p0_status"], {"p0_minimum_ready", "p0_complete"})
        self.assertNotEqual(report["overall_status"], "blocked")
        self.assertNotIn("serp-secret-value-123", encoded)
        self.assertNotIn("secret-cookie-value", encoded)
        self.assertNotIn("bilibili_cookie.txt", encoded)

    def test_bilibili_chrome_session_is_warn_not_direct_collector_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            search = root / "search.json"
            search.write_text(json.dumps({"SERPAPI_API_KEY": "serp-secret-value-123"}), encoding="utf-8")
            os.chmod(search, 0o600)
            profile = root / "ChromeProfile"
            profile.mkdir()
            auth = root / "auth.json"
            auth.write_text(
                json.dumps({"platforms": {"bilibili": {"chrome_profile_dir": str(profile)}}}),
                encoding="utf-8",
            )
            os.chmod(auth, 0o600)
            content_conn = connect_content(root / "policy_documents.sqlite")
            init_content_database(content_conn)
            report = build_access_readiness(
                content_conn=content_conn,
                search_secrets_file=search,
                platform_auth_file=auth,
                interpretation_source_file=_write_chinese_source_config(root),
            )
            content_conn.close()
        bilibili = next(row for row in report["tiers"] if row["area"] == "B站授权")
        encoded = json.dumps(report, ensure_ascii=False)
        self.assertEqual(report["summary"]["bilibili_status"], "session_only")
        self.assertEqual(bilibili["status"], "warn")
        self.assertIn("collector_ready=false", bilibili["evidence"])
        self.assertNotIn(str(profile), encoded)

    def test_render_dashboard_contains_high_value_sections(self) -> None:
        report = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "overall_status": "blocked",
            "summary": {
                "search_ready": 0,
                "platform_available": 0,
                "bilibili_status": "missing",
                "chinese_search_ready": 3,
                "missing_search_key": 1,
                "missing_platform_auth": 7,
                "p0_status": "p0_blocked",
            },
            "tiers": [
                {
                    "tier": "P0",
                    "area": "搜索 API",
                    "status": "fail",
                    "evidence": "ready 0/3",
                    "business_value": "补齐外部公开参考。",
                    "next_action": "补 key。",
                }
            ],
            "commands": {"credential_doctor": "PYTHONPATH=src python3 -m source_registry credential-doctor"},
            "next_actions": [{"priority": 95, "area": "搜索 API", "status": "fail", "action": "补 key"}],
            "security_boundary": "不展示 secret。",
        }
        rendered = render_access_readiness_dashboard(report)
        self.assertIn("全网接入 readiness", rendered)
        self.assertIn("分层接入验收", rendered)
        self.assertIn("验收命令矩阵", rendered)
        self.assertIn("安全与合规边界", rendered)

    def test_write_access_readiness_dashboard_creates_html(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            content_conn = connect_content(root / "policy_documents.sqlite")
            init_content_database(content_conn)
            output = root / "access.html"
            result = write_access_readiness_dashboard(
                output,
                content_conn=content_conn,
                search_secrets_file=root / "missing-search.json",
                platform_auth_file=root / "missing-auth.json",
                interpretation_source_file=_write_chinese_source_config(root),
            )
            content_conn.close()
            self.assertEqual(result, str(output))
            self.assertTrue(output.exists())
            self.assertIn("分层接入验收", output.read_text(encoding="utf-8"))

    def test_cli_access_readiness_generates_dashboard(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = root / "access.html"
            out = io.StringIO()
            with redirect_stdout(out):
                code = cli_main(
                    [
                        "--db",
                        str(root / "source_registry.sqlite"),
                        "access-readiness",
                        "--content-db",
                        str(root / "policy_documents.sqlite"),
                        "--interpretation-source-file",
                        str(_write_chinese_source_config(root)),
                        "--output",
                        str(output),
                        "--json",
                    ]
                )
            self.assertEqual(code, 0)
            payload = json.loads(out.getvalue())
            self.assertEqual(payload["dashboard_path"], str(output))
            self.assertEqual(payload["summary"]["chinese_search_ready"], 3)
            self.assertTrue(output.exists())


def _write_chinese_source_config(root: Path) -> Path:
    path = root / "interpretation_sources.json"
    path.write_text(
        json.dumps(
            {
                "sources": [
                    {"interpretation_source_id": "baidu_public", "platform": "baidu", "enabled": True},
                    {"interpretation_source_id": "sogou_public", "platform": "sogou", "enabled": True},
                    {"interpretation_source_id": "360_public", "platform": "360", "enabled": True},
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return path


if __name__ == "__main__":
    unittest.main()
