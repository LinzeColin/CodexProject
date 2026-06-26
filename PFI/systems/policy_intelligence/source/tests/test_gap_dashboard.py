from __future__ import annotations

import io
import json
import sqlite3
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from source_registry.cli import main as cli_main
from source_registry.content_db import (
    begin_run,
    connect_content,
    init_content_database,
    upsert_document,
    upsert_external_reference_gaps,
    upsert_interpretation_source,
)
from source_registry.gap_dashboard import render_gap_dashboard, write_gap_dashboard
from source_registry.reference_gaps import external_reference_gaps_for_items


class GapDashboardTest(unittest.TestCase):
    def test_render_gap_dashboard_contains_panels_and_commands(self) -> None:
        html = render_gap_dashboard(
            [
                {
                    "gap_id": "gap_1",
                    "status": "pending",
                    "priority_score": 95,
                    "platform": "bing",
                    "gap_type": "missing_api_key",
                    "required_action": "provide_search_api_key",
                    "title": "Bing 搜索缺口",
                },
                {
                    "gap_id": "gap_2",
                    "status": "pending",
                    "priority_score": 90,
                    "platform": "douyin",
                    "gap_type": "platform_auth_missing",
                    "required_action": "provide_platform_auth",
                    "title": "抖音授权缺口",
                },
            ]
        )
        self.assertIn("外部参考缺口管理仪表盘", html)
        self.assertIn("按建议动作", html)
        self.assertIn("按平台", html)
        self.assertIn("最高优先级缺口", html)
        self.assertIn("缺口复核工作台", html)
        self.assertIn('id="gap-data"', html)
        self.assertIn('id="filter-action"', html)
        self.assertIn('id="select-visible"', html)
        self.assertIn('id="build-bulk-command"', html)
        self.assertIn('id="build-single-command"', html)
        self.assertIn('id="command-output"', html)
        self.assertIn('data-gap-id', html)
        self.assertIn("gap-bulk-review", html)
        self.assertIn("gap_1", html)
        self.assertNotIn("API_KEY=", html)

    def test_render_gap_dashboard_escapes_script_boundary(self) -> None:
        rendered = render_gap_dashboard(
            [
                {
                    "gap_id": "gap_script",
                    "status": "pending",
                    "priority_score": 80,
                    "platform": "web",
                    "gap_type": "other_unverified_lead",
                    "required_action": "review_source",
                    "title": "</script><script>alert('x')</script>",
                }
            ]
        )
        self.assertIn("<\\/script>", rendered)
        self.assertNotIn("</script><script>alert", rendered)
        self.assertIn("&lt;/script&gt;&lt;script&gt;alert", rendered)

    def test_write_gap_dashboard_creates_html(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "gap-dashboard.html"
            result = write_gap_dashboard(path, [])
            self.assertEqual(result, str(path))
            self.assertTrue(path.exists())
            self.assertIn("暂无数据", path.read_text(encoding="utf-8"))

    def test_cli_gap_dashboard_generates_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_db = root / "source_registry.sqlite"
            content_db = root / "policy_documents.sqlite"
            output = root / "gap-dashboard.html"
            conn = connect_content(content_db)
            init_content_database(conn)
            begin_run(conn, "2026060401", "test")
            upsert_interpretation_source(
                conn,
                {
                    "interpretation_source_id": "serpapi_google",
                    "name": "SerpAPI Google",
                    "platform": "serpapi_google",
                    "url_template": "https://www.google.com/search?q={query}",
                },
            )
            document_id, _ = upsert_document(
                conn,
                {
                    "source_id": "src_test",
                    "source_name": "Test Gov",
                    "source_url": "https://example.gov.cn/",
                    "authority_tier_snapshot": "A",
                    "authority_score_snapshot": 95,
                    "title": "测试政策",
                    "url": "https://example.gov.cn/policy/a.html",
                    "document_type": "webpage",
                },
                "2026060401",
            )
            upsert_external_reference_gaps(
                conn,
                external_reference_gaps_for_items(
                    [
                        {
                            "run_id": "2026060401",
                            "document_id": document_id,
                            "interpretation_source_id": "serpapi_google",
                            "platform": "serpapi_google",
                            "item_type": "search_entry",
                            "title": "SerpAPI Google 全网政策解读搜索",
                            "url": "https://www.google.com/search?q=test",
                            "query": "测试政策 政策解读",
                            "evidence_status": "missing_api_key:serpapi",
                        }
                    ]
                ),
            )
            conn.close()
            out = io.StringIO()
            with redirect_stdout(out):
                code = cli_main(
                    [
                        "--db",
                        str(source_db),
                        "gap-dashboard",
                        "--content-db",
                        str(content_db),
                        "--output",
                        str(output),
                        "--json",
                    ]
                )
            self.assertEqual(code, 0)
            payload = json.loads(out.getvalue())
            self.assertEqual(payload["gap_count"], 1)
            self.assertTrue(output.exists())
            self.assertIn("SerpAPI", output.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
