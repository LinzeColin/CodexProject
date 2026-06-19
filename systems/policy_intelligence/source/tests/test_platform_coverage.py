from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from source_registry.cli import main as cli_main
from source_registry.content_db import connect_content, init_content_database, upsert_external_reference_gaps
from source_registry.platform_coverage import (
    build_platform_coverage,
    render_platform_coverage_dashboard,
    write_platform_coverage_dashboard,
)


class PlatformCoverageTest(unittest.TestCase):
    def test_build_platform_coverage_classifies_sources_without_secrets(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sources = root / "sources.json"
            sources.write_text(
                json.dumps(
                    {
                        "sources": [
                            {
                                "interpretation_source_id": "bili",
                                "name": "B站",
                                "platform": "bilibili",
                                "collector_type": "bilibili_api",
                                "url_template": "https://search.bilibili.com/all?keyword={query}",
                                "enabled": True,
                            },
                            {
                                "interpretation_source_id": "bing",
                                "name": "Bing",
                                "platform": "bing",
                                "collector_type": "search_api_bing",
                                "url_template": "https://www.bing.com/search?q={query}",
                                "enabled": True,
                            },
                            {
                                "interpretation_source_id": "baidu",
                                "name": "百度",
                                "platform": "baidu",
                                "collector_type": "search_landing",
                                "url_template": "https://www.baidu.com/s?wd={query}",
                                "enabled": True,
                            },
                            {
                                "interpretation_source_id": "toutiao_public",
                                "name": "头条公开搜索",
                                "platform": "toutiao",
                                "collector_type": "public_search_html",
                                "url_template": "https://so.toutiao.com/search?keyword={query}",
                                "enabled": True,
                            },
                            {
                                "interpretation_source_id": "toutiao_auth",
                                "name": "头条授权搜索",
                                "platform": "toutiao",
                                "collector_type": "authorized_public_search",
                                "url_template": "https://so.toutiao.com/search?keyword={query}",
                                "enabled": True,
                            },
                        ]
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            conn = connect_content(root / "policy_documents.sqlite")
            init_content_database(conn)
            coverage = build_platform_coverage(content_conn=conn, interpretation_source_file=sources)
            conn.close()
        self.assertGreaterEqual(coverage["summary"]["total"], 11)
        self.assertEqual(coverage["summary"]["search_api_ready"], 0)
        platforms = {row["platform"]: row for row in coverage["rows"]}
        self.assertEqual(platforms["bing"]["status"], "blocked")
        self.assertIn("public_video_search", platforms["bilibili"]["implemented_capabilities"])
        self.assertEqual(platforms["baidu"]["status"], "lead_only")
        self.assertEqual(platforms["toutiao"]["status"], "partial")
        self.assertIn("authorized_public_search", platforms["toutiao"]["implemented_capabilities"])
        self.assertIn("public_article_extraction", platforms["toutiao"]["implemented_capabilities"])
        self.assertNotIn("API_KEY=", json.dumps(coverage, ensure_ascii=False))

    def test_authorized_only_platform_is_blocked_until_auth_available(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sources = root / "sources.json"
            sources.write_text(
                json.dumps(
                    {
                        "sources": [
                            {
                                "interpretation_source_id": "xhs_auth",
                                "name": "小红书授权搜索",
                                "platform": "xiaohongshu",
                                "collector_type": "authorized_public_search",
                                "url_template": "https://www.xiaohongshu.com/search_result?keyword={query}",
                                "enabled": True,
                            }
                        ]
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            conn = connect_content(root / "policy_documents.sqlite")
            init_content_database(conn)
            coverage = build_platform_coverage(content_conn=conn, interpretation_source_file=sources)
            conn.close()
        platforms = {row["platform"]: row for row in coverage["rows"]}
        self.assertEqual(platforms["xiaohongshu"]["status"], "blocked")
        self.assertEqual(platforms["xiaohongshu"]["blocker"], "auth_not_configured")
        self.assertIn("authorized_public_search", platforms["xiaohongshu"]["implemented_capabilities"])

    def test_render_platform_coverage_dashboard_contains_matrix(self) -> None:
        coverage = {
            "generated_at": "2026-06-04T00:00:00",
            "summary": {"total": 1, "ready": 0, "partial": 1, "lead_only": 0, "needs_parser": 0, "blocked": 0},
            "rows": [
                {
                    "platform": "bilibili",
                    "display_name": "B站",
                    "source_group": "external_platform",
                    "status": "partial",
                    "implemented_capabilities": ["public_video_search"],
                    "allowed_capabilities": ["video_detail"],
                    "blocker": "auth_optional_for_deeper_data",
                    "next_action": "补 cookie",
                }
            ],
            "next_actions": [],
            "compliance_boundary": "不绕过验证码、付费墙、登录访问控制。",
        }
        html = render_platform_coverage_dashboard(coverage)
        self.assertIn("平台覆盖矩阵", html)
        self.assertIn("合规边界", html)
        self.assertIn("平台覆盖明细", html)
        self.assertIn("B站", html)
        self.assertNotIn("cookie_file", html)

    def test_cli_platform_coverage_generates_dashboard(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_db = root / "source_registry.sqlite"
            content_db = root / "policy_documents.sqlite"
            output = root / "platform.html"
            conn = connect_content(content_db)
            init_content_database(conn)
            upsert_external_reference_gaps(
                conn,
                [
                    {
                        "gap_id": "gap_1",
                        "run_id": "2026060401",
                        "document_id": None,
                        "interpretation_source_id": None,
                        "platform": "bing",
                        "gap_type": "missing_api_key",
                        "title": "Bing key missing",
                        "url": "https://www.bing.com/search?q=test",
                        "query": "test",
                        "evidence_status": "missing_api_key:bing",
                        "required_action": "provide_search_api_key",
                        "priority_score": 95,
                    }
                ],
            )
            conn.close()
            out = io.StringIO()
            with redirect_stdout(out):
                code = cli_main(
                    [
                        "--db",
                        str(source_db),
                        "platform-coverage",
                        "--content-db",
                        str(content_db),
                        "--output",
                        str(output),
                        "--json",
                    ]
                )
            self.assertEqual(code, 0)
            payload = json.loads(out.getvalue())
            self.assertEqual(payload["dashboard_path"], str(output))
            self.assertEqual(payload["summary"]["pending_gaps"], 1)
            self.assertTrue(output.exists())
            self.assertIn("平台覆盖矩阵", output.read_text(encoding="utf-8"))

    def test_write_platform_coverage_dashboard_creates_html(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            conn = connect_content(root / "policy_documents.sqlite")
            init_content_database(conn)
            output = root / "platform.html"
            result = write_platform_coverage_dashboard(output, content_conn=conn)
            conn.close()
            self.assertEqual(result, str(output))
            self.assertTrue(output.exists())


if __name__ == "__main__":
    unittest.main()
