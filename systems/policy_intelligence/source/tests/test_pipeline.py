from __future__ import annotations

import sqlite3
import tempfile
import unittest
import os
import re
import zipfile
from io import BytesIO
from pathlib import Path

from source_registry.collector import FixtureFetcher
from source_registry.content_db import connect_content
from source_registry.db import connect, init_database, seed_sources
from source_registry.interpretation import (
    count_reference_items,
    interpretation_health_stats,
    reference_platforms,
)
from source_registry.pipeline import PipelineConfig, _next_generation_candidates, _pipeline_lock, run_pipeline


class PipelineTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self._old_disable_chrome_pdf = os.environ.get("POLICY_REPORT_DISABLE_CHROME_PDF")
        os.environ["POLICY_REPORT_DISABLE_CHROME_PDF"] = "1"
        self.source_db = self.root / "source_registry.sqlite"
        self.content_db = self.root / "policy_documents.sqlite"
        conn = connect(self.source_db)
        init_database(conn)
        seed_sources(conn, [_source()])
        conn.close()

    def tearDown(self) -> None:
        if self._old_disable_chrome_pdf is None:
            os.environ.pop("POLICY_REPORT_DISABLE_CHROME_PDF", None)
        else:
            os.environ["POLICY_REPORT_DISABLE_CHROME_PDF"] = self._old_disable_chrome_pdf
        self.tmp.cleanup()

    def test_run_pipeline_writes_content_db_and_report(self) -> None:
        result = run_pipeline(self._config(), fetcher=_fetcher())
        self.assertEqual(result["status"], "completed")
        self.assertRegex(result["run_id"], r"^\d{10}$")
        self.assertEqual(result["stats"]["sources_considered"], 1)
        self.assertEqual(result["stats"]["pages_fetched"], 1)
        self.assertGreaterEqual(result["stats"]["documents_discovered"], 2)
        self.assertEqual(result["stats"]["analyzed_documents"], 1)
        self.assertEqual(result["stats"]["document_since"], "2025-01-01")
        self.assertEqual(result["stats"]["active_industry_rank"], 11)
        self.assertEqual(result["stats"]["min_external_platforms"], 0)
        self.assertIn("external_platform_count", result["stats"])
        self.assertIn("external_reference_gaps", result["stats"])
        self.assertIn("interpretation_attempts", result["stats"])
        self.assertIn("queue_preview", result)

        report = Path(result["report_path"])
        self.assertTrue(report.exists())
        self.assertEqual(report.suffix, ".pdf")
        self.assertIn("研究报告", report.name)
        self.assertIn("先进制造业", report.name)
        self.assertTrue(report.read_bytes().startswith(b"%PDF"))

        html_report = Path(result["report_artifacts"]["html_path"])
        markdown_report = Path(result["report_artifacts"]["markdown_path"])
        dashboard_report = Path(result["report_artifacts"]["dashboard_path"])
        self.assertTrue(html_report.exists())
        self.assertTrue(markdown_report.exists())
        self.assertTrue(dashboard_report.exists())
        text = html_report.read_text(encoding="utf-8")
        dashboard_text = dashboard_report.read_text(encoding="utf-8")
        self.assertIn("中国政策文件单文件研究分析报告", text)
        self.assertIn("本报告研究文件数：1", markdown_report.read_text(encoding="utf-8"))
        self.assertIn("<nav class=\"toc\">", text)
        self.assertIn("研究质量与交付状态", text)
        self.assertNotIn("运行可视化仪表盘", text)
        self.assertNotIn("采集漏斗", text)
        self.assertIn("采集漏斗", dashboard_text)
        self.assertIn("规则化质量门槛", text)
        self.assertIn("外部采集健康度", dashboard_text)
        self.assertIn("外部参考缺口队列", text)
        self.assertIn("外部参考缺口队列", dashboard_text)
        self.assertNotIn("开源/商业参考能力矩阵", text)
        self.assertIn("开源/商业参考能力矩阵", dashboard_text)
        self.assertIn("政策监测运营仪表盘", dashboard_text)
        self.assertIn("规则化质量门槛", dashboard_text)
        self.assertIn("PolicyInsight", dashboard_text)
        self.assertIn("href=\"#doc-1\"", text)
        self.assertIn("外部研究与解读资料来源", text)
        self.assertIn("外部平台", text)
        self.assertIn("1. 原文定位、权威性与研究边界", text)
        self.assertIn("10. 后续任务队列、监测指标与结论", text)
        self.assertEqual(text.count("class=\"deep-chapter\""), 10)
        self.assertNotIn("chapter-print-spacer", text)
        self.assertIn("待生产研究报告队列", text)
        self.assertNotIn("报告生成时间线", text)
        self.assertIn("哔哩哔哩政策解读视频搜索", text)
        self.assertIn("来源权威 A/", text)
        self.assertIn("Example Gov", text)
        self.assertNotIn("English Summary", text)

        conn = connect_content(self.content_db)
        doc_count = conn.execute("SELECT COUNT(*) AS count FROM documents").fetchone()["count"]
        run_count = conn.execute("SELECT COUNT(*) AS count FROM pipeline_runs").fetchone()["count"]
        analysis_count = conn.execute("SELECT COUNT(*) AS count FROM analyses").fetchone()["count"]
        mode = conn.execute("SELECT analysis_mode FROM analyses LIMIT 1").fetchone()["analysis_mode"]
        material_count = conn.execute("SELECT COUNT(*) AS count FROM interpretation_items").fetchone()["count"]
        gap_count = conn.execute("SELECT COUNT(*) AS count FROM external_reference_gaps").fetchone()["count"]
        generated_queue = conn.execute(
            "SELECT industry_rank, primary_industry FROM report_queue WHERE status = 'generated' LIMIT 1"
        ).fetchone()
        self.assertGreaterEqual(doc_count, 2)
        self.assertEqual(run_count, 1)
        self.assertEqual(analysis_count, 1)
        self.assertEqual(mode, "template_zh_single_v1")
        self.assertGreaterEqual(material_count, 2)
        self.assertGreaterEqual(gap_count, 1)
        self.assertEqual(generated_queue["industry_rank"], 11)
        self.assertEqual(generated_queue["primary_industry"], "高端装备 / 工业母机")
        conn.close()

    def test_pipeline_lock_removes_stale_pid_file(self) -> None:
        lock_path = self.root / "data" / "pipeline.lock"
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        lock_path.write_text("999999", encoding="utf-8")
        with _pipeline_lock(lock_path):
            self.assertTrue(lock_path.exists())
            self.assertEqual(lock_path.read_text(encoding="utf-8"), str(os.getpid()))
        self.assertFalse(lock_path.exists())

    def test_repeated_run_is_idempotent_for_known_urls(self) -> None:
        first = run_pipeline(self._config(), fetcher=_fetcher())
        second = run_pipeline(self._config(), fetcher=_fetcher())
        self.assertGreaterEqual(first["stats"]["new_documents"], 2)
        self.assertEqual(second["stats"]["new_documents"], 0)

    def test_generation_candidate_selection_keeps_queue_order(self) -> None:
        queue = [
            {"document_id": "doc_first", "industry_rank": 14, "title": "第一份待生产"},
            {"document_id": "doc_second", "industry_rank": 14, "title": "第二份待生产"},
            {"document_id": "doc_third", "industry_rank": 16, "title": "第三份待生产"},
        ]
        selected = _next_generation_candidates(queue)
        self.assertEqual([item["document_id"] for item in selected], ["doc_first"])

    def test_attachment_is_fetched_and_parsed_before_report(self) -> None:
        fetcher = FixtureFetcher(
            {
                "https://example.gov.cn/": """
                    <html>
                      <head><title>Example Gov 附件栏目</title></head>
                      <body>
                        <a href="/files/industrial-machine-policy.docx">高端装备工业母机政策规划</a>
                      </body>
                    </html>
                """,
                "https://example.gov.cn/files/industrial-machine-policy.docx": _docx_bytes(
                    "高端装备工业母机政策规划",
                    "推进工业母机、机器人和先进制造业重点项目。",
                ),
            }
        )
        result = run_pipeline(self._config(), fetcher=fetcher)
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["stats"]["attachments_parsed"], 1)

        conn = connect_content(self.content_db)
        row = conn.execute(
            """
            SELECT document_type, text_excerpt, snapshot_path
            FROM documents
            WHERE canonical_url = ?
            """,
            ("https://example.gov.cn/files/industrial-machine-policy.docx",),
        ).fetchone()
        self.assertEqual(row["document_type"], "attachment")
        self.assertIn("工业母机", row["text_excerpt"])
        self.assertTrue(Path(row["snapshot_path"]).exists())
        conn.close()

    def test_reference_count_excludes_search_landings(self) -> None:
        items = [
            {
                "platform": "bilibili",
                "item_type": "video",
                "title": "政策解读视频",
                "url": "https://www.bilibili.com/video/BV1",
                "evidence_status": "公开视频搜索结果；字幕已摘录",
                "content_excerpt": "具备可读简介和标签。字幕摘录：这里是政策解读字幕。",
                "raw_metadata": {
                    "detail_enriched": True,
                    "subtitle_excerpt": "这里是政策解读字幕。",
                },
            },
            {
                "platform": "douyin",
                "item_type": "search_entry",
                "title": "抖音政策解读搜索",
                "url": "https://www.douyin.com/search/test",
                "evidence_status": "需登录/反爬验证",
                "summary": "需要授权。",
            },
            {
                "platform": "serpapi_google",
                "item_type": "search_entry",
                "title": "SerpAPI Google 全网政策解读搜索",
                "url": "https://www.google.com/search?q=test",
                "evidence_status": "missing_api_key:serpapi",
                "summary": "需要搜索 API key。",
            },
            {
                "platform": "bilibili",
                "item_type": "video",
                "title": "好久不见",
                "url": "https://www.bilibili.com/video/BV2",
                "query": "农业农村现代化 政策解读",
                "evidence_status": "公开视频搜索结果",
                "content_excerpt": "生活记录，农村，助农。",
            },
        ]
        self.assertEqual(count_reference_items(items), 1)
        self.assertEqual(reference_platforms(items), ["bilibili"])
        health = interpretation_health_stats(items)
        self.assertEqual(health["interpretation_reference_successes"], 1)
        self.assertEqual(health["interpretation_missing_api_keys"], 1)
        self.assertEqual(health["interpretation_auth_required"], 1)
        self.assertEqual(health["interpretation_leads"], 3)
        self.assertEqual(health["video_details_enriched"], 1)
        self.assertEqual(health["video_subtitles_extracted"], 1)

    def _config(self) -> PipelineConfig:
        return PipelineConfig(
            source_db_path=self.source_db,
            content_db_path=self.content_db,
            data_dir=self.root / "data",
            report_dir=self.root / "reports",
            max_sources=1,
            max_pages_per_source=1,
            max_links_per_page=5,
            max_analyze=10,
            min_authority_score=60,
            analysis_mode="template",
            mode="automation",
            min_external_references_per_report=0,
            min_external_platforms_per_report=0,
        )


def _fetcher() -> FixtureFetcher:
    return FixtureFetcher(
        {
            "https://example.gov.cn/": """
                <html>
                  <head><title>Example Gov 政策文件栏目</title></head>
                  <body>
                    <a href="/policy/2026-notice.html">关于推进先进制造业发展的通知</a>
                    <a href="/report/white-paper.pdf">数字经济白皮书</a>
                    <a href="/about.html">机构介绍</a>
                  </body>
                </html>
            """,
            "https://example.gov.cn/policy/2026-notice.html": """
                <html>
                  <head><title>关于推进先进制造业发展的通知</title></head>
                  <body>围绕先进制造、装备制造和工业母机出台支持政策。</body>
                </html>
            """,
        }
    )


def _docx_bytes(*paragraphs: str) -> bytes:
    body = "".join(f"<w:p><w:r><w:t>{paragraph}</w:t></w:r></w:p>" for paragraph in paragraphs)
    payload = f"""
    <w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
      <w:body>{body}</w:body>
    </w:document>
    """
    buf = BytesIO()
    with zipfile.ZipFile(buf, "w") as archive:
        archive.writestr("word/document.xml", payload)
    return buf.getvalue()


def _source() -> dict:
    return {
        "name": "Example Gov",
        "country_code": "CN",
        "country_name": "China",
        "region": "China",
        "administrative_level": "national",
        "source_type": "government_portal",
        "sponsor_unit": "国务院办公厅",
        "supervisor_unit": "国务院办公厅",
        "official_url": "https://example.gov.cn/",
        "publishes_original_documents": True,
        "crawl_enabled": True,
        "crawl_priority": 1,
        "status": "active",
        "evidence": [
            {"type": "official_directory", "value": "测试官方目录"},
            {"type": "organization_page", "value": "测试组织机构"},
            {"type": "sponsor_unit", "value": "国务院办公厅"},
            {"type": "supervisor_unit", "value": "国务院办公厅"},
        ],
    }


if __name__ == "__main__":
    unittest.main()
