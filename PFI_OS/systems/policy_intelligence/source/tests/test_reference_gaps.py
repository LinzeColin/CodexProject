from __future__ import annotations

import sqlite3
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from source_registry.content_db import (
    begin_run,
    bulk_update_external_reference_gap_status,
    connect_content,
    init_content_database,
    list_external_reference_gaps,
    pending_external_reference_gaps,
    update_external_reference_gap_status,
    upsert_document,
    upsert_external_reference_gaps,
    upsert_interpretation_source,
)
from source_registry.cli import main as cli_main
from source_registry.reference_gaps import (
    external_reference_gap_for_item,
    external_reference_gap_summary_for_items,
    external_reference_gaps_for_items,
    gap_action_label,
    gap_type_label,
)


class ReferenceGapTest(unittest.TestCase):
    def test_gap_classification_and_sanitized_metadata(self) -> None:
        item = {
            "run_id": "2026060401",
            "document_id": "doc_a",
            "interpretation_source_id": "serpapi_google",
            "platform": "serpapi_google",
            "item_type": "search_entry",
            "title": "SerpAPI Google 全网政策解读搜索",
            "url": "https://www.google.com/search?q=test",
            "query": "政策解读",
            "evidence_status": "missing_api_key:serpapi",
            "summary": "需要搜索 API key。",
            "raw_metadata": {
                "provider": "serpapi",
                "cookie_file": "/private/secret/cookie.txt",
                "platform_auth": {
                    "platform": "bilibili",
                    "configured": True,
                    "available": False,
                    "status": "auth_cookie_file_missing",
                    "cookie_file_configured": True,
                },
            },
        }
        gap = external_reference_gap_for_item(item)
        self.assertIsNotNone(gap)
        self.assertEqual(gap["gap_type"], "missing_api_key")
        self.assertEqual(gap["required_action"], "provide_search_api_key")
        self.assertNotIn("cookie_file", gap["raw_metadata"])
        self.assertTrue(gap["raw_metadata"]["platform_auth"]["cookie_file_configured"])
        self.assertEqual(gap_type_label("missing_api_key"), "搜索 API key 缺口")
        self.assertEqual(gap_action_label("provide_search_api_key"), "补充搜索 API key")

    def test_gap_summary_excludes_effective_references(self) -> None:
        items = [
            {
                "run_id": "2026060401",
                "document_id": "doc_a",
                "interpretation_source_id": "bilibili",
                "platform": "bilibili",
                "item_type": "video",
                "title": "政策解读视频",
                "url": "https://www.bilibili.com/video/BV1",
                "query": "政策解读",
                "evidence_status": "公开视频搜索结果；字幕已摘录",
                "content_excerpt": "政策解读字幕和政策要点，足以作为外部参考。",
                "raw_metadata": {"subtitle_excerpt": "政策解读字幕。"},
            },
            {
                "run_id": "2026060401",
                "document_id": "doc_a",
                "interpretation_source_id": "douyin",
                "platform": "douyin",
                "item_type": "search_entry",
                "title": "抖音政策解读搜索",
                "url": "https://www.douyin.com/search/test",
                "query": "政策解读",
                "evidence_status": "需登录/反爬验证；未配置授权文件",
            },
        ]
        gaps = external_reference_gaps_for_items(items)
        self.assertEqual(len(gaps), 1)
        self.assertEqual(gaps[0]["gap_type"], "platform_auth_missing")
        summary = external_reference_gap_summary_for_items(items)
        self.assertEqual(summary["pending_count"], 1)
        self.assertEqual(summary["by_action"]["provide_platform_auth"], 1)

    def test_subject_mismatch_gap_classification(self) -> None:
        item = {
            "run_id": "2026060401",
            "document_id": "doc_drug",
            "interpretation_source_id": "local",
            "platform": "gd.gov.cn",
            "item_type": "article",
            "title": "农村集体土地留用地管理政策解读",
            "url": "https://www.gd.gov.cn/land-policy.html",
            "query": "广东省药品监督管理局 药品零售许可验收实施细则 政策解读",
            "evidence_status": "已入库公开相关文件/解读",
            "content_excerpt": "政策解读围绕农村集体土地留用地开发利用、规划管理和收益分配展开。",
            "relevance_score": 94,
        }
        gap = external_reference_gap_for_item(item)
        self.assertIsNotNone(gap)
        self.assertEqual(gap["gap_type"], "subject_mismatch")
        self.assertEqual(gap["required_action"], "review_candidate_url")
        self.assertEqual(gap_type_label("subject_mismatch"), "主题不匹配")

    def test_gap_queue_persists_pending_items(self) -> None:
        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
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
        gaps = external_reference_gaps_for_items(
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
        )
        upsert_external_reference_gaps(conn, gaps)
        rows = pending_external_reference_gaps(conn, limit=5)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["gap_type"], "missing_api_key")
        self.assertEqual(rows[0]["required_action"], "provide_search_api_key")
        filtered = list_external_reference_gaps(
            conn,
            required_action="provide_search_api_key",
            limit=5,
        )
        self.assertEqual(len(filtered), 1)
        updated = update_external_reference_gap_status(
            conn,
            rows[0]["gap_id"],
            "ignored",
            reviewer="test",
            note="manual triage",
        )
        self.assertEqual(updated["status"], "ignored")
        self.assertEqual(updated["reviewed_by"], "test")
        self.assertEqual(pending_external_reference_gaps(conn, limit=5), [])
        conn.close()

    def test_gap_upsert_is_idempotent_by_gap_id_when_nullable_unique_fields_repeat(self) -> None:
        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        init_content_database(conn)
        begin_run(conn, "2026060401", "test")
        gaps = external_reference_gaps_for_items(
            [
                {
                    "run_id": "2026060401",
                    "document_id": None,
                    "interpretation_source_id": None,
                    "platform": "sogou",
                    "item_type": "search_entry",
                    "title": "公开搜索未返回可用结果",
                    "url": "",
                    "query": "政策解读",
                    "evidence_status": "公开搜索未返回可用结果，保留搜索入口",
                },
                {
                    "run_id": "2026060402",
                    "document_id": None,
                    "interpretation_source_id": None,
                    "platform": "sogou",
                    "item_type": "search_entry",
                    "title": "公开搜索未返回可用结果",
                    "url": "",
                    "query": "政策解读",
                    "evidence_status": "公开搜索未返回可用结果，保留搜索入口",
                },
            ]
        )
        ids = upsert_external_reference_gaps(conn, gaps)
        self.assertEqual(len(set(ids)), 1)
        rows = list_external_reference_gaps(conn, status="all", limit=5)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["last_seen_run_id"], "2026060402")
        conn.close()

    def test_gap_upsert_resolves_stale_pending_gaps_for_same_run(self) -> None:
        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        init_content_database(conn)
        begin_run(conn, "2026060401", "test")
        items = [
            {
                "run_id": "2026060401",
                "document_id": None,
                "interpretation_source_id": None,
                "platform": "serpapi_google",
                "item_type": "search_entry",
                "title": "SerpAPI Google 全网政策解读搜索",
                "url": "https://www.google.com/search?q=test",
                "query": "测试政策 政策解读",
                "evidence_status": "missing_api_key:serpapi",
            },
            {
                "run_id": "2026060401",
                "document_id": None,
                "interpretation_source_id": None,
                "platform": "bilibili",
                "item_type": "search_entry",
                "title": "B站政策解读搜索",
                "url": "https://search.bilibili.com/all?keyword=test",
                "query": "测试政策 政策解读",
                "evidence_status": "需登录/反爬验证；未配置授权文件",
            },
        ]
        first_pass = external_reference_gaps_for_items(items)
        upsert_external_reference_gaps(conn, first_pass)
        self.assertEqual(len(pending_external_reference_gaps(conn, limit=10)), 2)

        second_pass = external_reference_gaps_for_items([items[0]])
        upsert_external_reference_gaps(conn, second_pass)

        pending = pending_external_reference_gaps(conn, limit=10)
        all_rows = list_external_reference_gaps(conn, status="all", limit=10)
        self.assertEqual(len(pending), 1)
        self.assertEqual(pending[0]["platform"], "serpapi_google")
        statuses = {row["platform"]: row["status"] for row in all_rows}
        self.assertEqual(statuses["bilibili"], "resolved")
        conn.close()

    def test_gap_upsert_ignores_superseded_same_source_gap_url(self) -> None:
        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        init_content_database(conn)
        begin_run(conn, "2026060401", "test")
        begin_run(conn, "2026060402", "test")
        upsert_interpretation_source(
            conn,
            {
                "interpretation_source_id": "bing",
                "name": "Bing",
                "platform": "bing",
                "url_template": "https://www.bing.com/search?q={query}",
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
        old_gap = external_reference_gaps_for_items(
            [
                {
                    "run_id": "2026060401",
                    "document_id": document_id,
                    "interpretation_source_id": "bing",
                    "platform": "bing",
                    "item_type": "search_entry",
                    "title": "Bing 旧查询",
                    "url": "https://www.bing.com/search?q=old",
                    "query": "旧查询 政策解读",
                    "evidence_status": "missing_api_key:bing",
                }
            ]
        )
        upsert_external_reference_gaps(conn, old_gap)
        new_gap = external_reference_gaps_for_items(
            [
                {
                    "run_id": "2026060402",
                    "document_id": document_id,
                    "interpretation_source_id": "bing",
                    "platform": "bing",
                    "item_type": "search_entry",
                    "title": "Bing 新查询",
                    "url": "https://www.bing.com/search?q=new",
                    "query": "新查询 政策解读",
                    "evidence_status": "missing_api_key:bing",
                }
            ]
        )
        new_id = upsert_external_reference_gaps(conn, new_gap)[0]
        rows = list_external_reference_gaps(conn, status="all", limit=10)
        statuses = {row["gap_id"]: row["status"] for row in rows}
        self.assertEqual(statuses[new_id], "pending")
        ignored = [row for row in rows if row["gap_id"] != new_id][0]
        self.assertEqual(ignored["status"], "ignored")
        self.assertIn("stale query/url", ignored["review_note"])
        conn.close()

    def test_cli_lists_and_reviews_reference_gaps(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_db = root / "source_registry.sqlite"
            content_db = root / "policy_documents.sqlite"
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
            gap_id = upsert_external_reference_gaps(
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
            )[0]
            conn.close()

            out = io.StringIO()
            with redirect_stdout(out):
                code = cli_main(
                    [
                        "--db",
                        str(source_db),
                        "gaps",
                        "--content-db",
                        str(content_db),
                        "--json",
                    ]
                )
            self.assertEqual(code, 0)
            rows = json.loads(out.getvalue())
            self.assertEqual(rows[0]["gap_id"], gap_id)
            self.assertEqual(rows[0]["required_action"], "provide_search_api_key")

            out = io.StringIO()
            with redirect_stdout(out):
                code = cli_main(
                    [
                        "--db",
                        str(source_db),
                        "gap-review",
                        gap_id,
                        "--content-db",
                        str(content_db),
                        "--status",
                        "resolved",
                        "--reviewer",
                        "tester",
                        "--note",
                        "key added",
                        "--json",
                    ]
                )
            self.assertEqual(code, 0)
            updated = json.loads(out.getvalue())
            self.assertEqual(updated["status"], "resolved")
            self.assertEqual(updated["reviewed_by"], "tester")

    def test_bulk_review_can_dry_run_and_update_filtered_gaps(self) -> None:
        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        init_content_database(conn)
        begin_run(conn, "2026060401", "test")
        for source_id, platform in [
            ("serpapi_google", "serpapi_google"),
            ("douyin", "douyin"),
        ]:
            upsert_interpretation_source(
                conn,
                {
                    "interpretation_source_id": source_id,
                    "name": source_id,
                    "platform": platform,
                    "url_template": "https://example.com/search?q={query}",
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
        gaps = external_reference_gaps_for_items(
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
                },
                {
                    "run_id": "2026060401",
                    "document_id": document_id,
                    "interpretation_source_id": "douyin",
                    "platform": "douyin",
                    "item_type": "search_entry",
                    "title": "抖音政策解读搜索",
                    "url": "https://www.douyin.com/search/test",
                    "query": "测试政策 政策解读",
                    "evidence_status": "需登录/反爬验证；未配置授权文件",
                },
            ]
        )
        upsert_external_reference_gaps(conn, gaps)
        dry_run = bulk_update_external_reference_gap_status(
            conn,
            status="ignored",
            required_action="provide_search_api_key",
            dry_run=True,
        )
        self.assertEqual(len(dry_run), 1)
        self.assertEqual(len(pending_external_reference_gaps(conn, limit=10)), 2)
        updated = bulk_update_external_reference_gap_status(
            conn,
            status="ignored",
            required_action="provide_search_api_key",
            reviewer="tester",
            note="search key handled elsewhere",
        )
        self.assertEqual(len(updated), 1)
        self.assertEqual(updated[0]["status"], "ignored")
        pending = pending_external_reference_gaps(conn, limit=10)
        self.assertEqual(len(pending), 1)
        self.assertEqual(pending[0]["required_action"], "provide_platform_auth")
        conn.close()


if __name__ == "__main__":
    unittest.main()
