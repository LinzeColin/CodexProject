from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from source_registry.cli import main as cli_main
from source_registry.content_db import (
    begin_run,
    connect_content,
    init_content_database,
    upsert_interpretation_item,
    upsert_interpretation_source,
)
from source_registry.platform_parser_samples import (
    build_platform_parser_sample_acceptance,
    render_platform_parser_sample_dashboard,
    write_platform_parser_sample_dashboard,
)


class PlatformParserSamplesTest(unittest.TestCase):
    def test_sample_acceptance_classifies_parser_output_without_secrets(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            parser_file = _parser_file(root)
            conn = _sample_content_db(root)
            try:
                report = build_platform_parser_sample_acceptance(conn, parser_file=parser_file)
            finally:
                conn.close()
        rows = {row["platform"]: row for row in report["rows"]}
        self.assertEqual(rows["serpapi_bing_google"]["sample_status"], "sample_passed")
        self.assertEqual(rows["bilibili"]["sample_status"], "partial_sample")
        self.assertEqual(rows["zhihu"]["sample_status"], "no_samples")
        self.assertGreaterEqual(report["summary"]["reference_item_count"], 1)
        encoded = json.dumps(report, ensure_ascii=False)
        self.assertNotIn("SESSDATA=", encoded)
        self.assertNotIn("sk-", encoded)

    def test_render_dashboard_contains_business_acceptance_panels(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            conn = _sample_content_db(root)
            try:
                rendered = render_platform_parser_sample_dashboard(
                    build_platform_parser_sample_acceptance(conn, parser_file=_parser_file(root))
                )
            finally:
                conn.close()
        self.assertIn("平台解析样本验收 dashboard", rendered)
        self.assertIn("解析样本验收明细", rendered)
        self.assertIn("可计入报告质量门槛", rendered)
        self.assertNotIn("SESSDATA=", rendered)

    def test_write_dashboard_creates_html(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            conn = _sample_content_db(root)
            output = root / "samples.html"
            try:
                result = write_platform_parser_sample_dashboard(output, conn, parser_file=_parser_file(root))
            finally:
                conn.close()
            self.assertEqual(result, str(output))
            self.assertTrue(output.exists())

    def test_cli_platform_parser_samples_generates_dashboard(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db_path = root / "policy_documents.sqlite"
            conn = _sample_content_db(root, db_path=db_path)
            conn.close()
            output = root / "samples.html"
            out = io.StringIO()
            with redirect_stdout(out):
                code = cli_main(
                    [
                        "--db",
                        str(root / "source_registry.sqlite"),
                        "platform-parser-samples",
                        "--content-db",
                        str(db_path),
                        "--parser-file",
                        str(_parser_file(root)),
                        "--output",
                        str(output),
                        "--json",
                    ]
                )
            self.assertEqual(code, 0)
            payload = json.loads(out.getvalue())
            self.assertEqual(payload["dashboard_path"], str(output))
            self.assertTrue(output.exists())
            self.assertGreaterEqual(payload["summary"]["sample_item_count"], 2)


def _sample_content_db(root: Path, *, db_path: Path | None = None):
    conn = connect_content(db_path or root / "policy_documents.sqlite")
    init_content_database(conn)
    begin_run(conn, "2026060401", "test")
    upsert_interpretation_source(
        conn,
        {
            "interpretation_source_id": "src_bilibili",
            "name": "B站",
            "platform": "bilibili",
            "url_template": "https://search.bilibili.com/all?keyword={query}",
            "collector_type": "bilibili_api",
        },
    )
    upsert_interpretation_source(
        conn,
        {
            "interpretation_source_id": "src_bing",
            "name": "Bing",
            "platform": "bing",
            "url_template": "https://api.bing.microsoft.com/v7.0/search?q={query}",
            "collector_type": "search_api_bing",
        },
    )
    upsert_interpretation_item(
        conn,
        {
            "run_id": "2026060401",
            "interpretation_source_id": "src_bilibili",
            "platform": "bilibili",
            "item_type": "video",
            "title": "人工智能产业政策解读：算力、芯片与企业影响",
            "url": "https://www.bilibili.com/video/BVtest",
            "query": "人工智能产业政策 解读",
            "evidence_status": "公开视频搜索结果；互动摘录已采集",
            "summary": "围绕人工智能产业政策、算力建设、芯片企业、投资影响和实施路径进行公开解读。",
            "author_name": "政策研究员",
            "view_count": 1200,
            "relevance_score": 88,
            "raw_metadata": {"bvid": "BVtest", "like": 12, "danmaku": 2},
        },
    )
    upsert_interpretation_item(
        conn,
        {
            "run_id": "2026060401",
            "interpretation_source_id": "src_bing",
            "platform": "bing",
            "item_type": "article",
            "title": "人工智能产业政策专业解读与企业影响分析",
            "url": "https://example.com/policy-ai-analysis",
            "query": "人工智能产业政策 解读",
            "evidence_status": "公开搜索结果；正文已摘录",
            "content_excerpt": "这是一篇针对人工智能产业政策的专业解读，重点分析政策目标、产业链影响、企业合规要求、投资节奏、算力和芯片供给约束，以及后续落地风险。" * 2,
            "author_name": "研究机构",
            "relevance_score": 90,
            "raw_metadata": {"article_fetch_status": "article_excerpt_extracted"},
        },
    )
    return conn


def _parser_file(root: Path) -> Path:
    path = root / "platform_parsers.json"
    path.write_text(
        json.dumps(
            {
                "last_refreshed": "2026-06-04",
                "parsers": [
                    {
                        "parser_id": "bilibili_public_video_parser",
                        "platform": "bilibili",
                        "name": "B站公开视频解析器",
                        "status": "partial",
                        "priority": 100,
                        "implemented_capabilities": ["public_search", "video_metadata", "subtitle_extraction", "comment_extraction", "author_profile", "interaction_metrics", "failure_audit", "no_secret_logging"],
                        "next_action": "补字幕、评论和弹幕稳定解析。",
                    },
                    {
                        "parser_id": "search_api_article_parser",
                        "platform": "serpapi_bing_google",
                        "name": "搜索 API 公开文章解析器",
                        "status": "ready",
                        "priority": 95,
                        "implemented_capabilities": ["public_search", "article_body", "author_profile", "failure_audit", "no_secret_logging"],
                    },
                    {
                        "parser_id": "zhihu_authorized_content_parser",
                        "platform": "zhihu",
                        "name": "知乎授权内容解析器",
                        "status": "planned",
                        "priority": 64,
                        "implemented_capabilities": ["public_search", "article_body", "author_profile", "failure_audit", "no_secret_logging"],
                    },
                ],
                "capability_targets": [],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return path


if __name__ == "__main__":
    unittest.main()
