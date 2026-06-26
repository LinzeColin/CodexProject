from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from source_registry.analyzer import TEMPLATE_ANALYSIS_MODE
from source_registry.cli import main as cli_main
from source_registry.content_db import (
    begin_run,
    complete_run,
    connect_content,
    init_content_database,
    upsert_document,
    upsert_external_reference_gaps,
    upsert_interpretation_source,
    upsert_report_queue_item,
)
from source_registry.ops_dashboard import render_ops_dashboard, write_ops_dashboard


class OpsDashboardTest(unittest.TestCase):
    def test_render_ops_dashboard_contains_operational_panels(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            conn = _sample_content_db(Path(tmp) / "policy_documents.sqlite")
            rendered = render_ops_dashboard(conn, data_dir=tmp, analysis_mode=TEMPLATE_ANALYSIS_MODE)
            conn.close()
        self.assertIn("政策智能运营总览", rendered)
        self.assertIn("质量门槛与外部采集", rendered)
        self.assertIn("规则化质量门槛", rendered)
        self.assertIn("商务高价值信息密度", rendered)
        self.assertIn("quality_gates_dashboard.html", rendered)
        self.assertIn("下一步动作", rendered)
        self.assertIn("队列序", rendered)
        self.assertIn("行业优先级", rendered)
        self.assertIn("实际生产顺序", rendered)
        self.assertIn("缺搜索 Key", rendered)
        self.assertIn("缺平台授权", rendered)
        self.assertNotIn("<span>运行总数</span>", rendered)
        self.assertNotIn("<span>已生成报告</span>", rendered)
        self.assertNotIn("<h2>最近运行</h2>", rendered)
        self.assertNotIn("<span>最近运行</span>", rendered)
        self.assertNotIn("最近运行质量", rendered)
        self.assertIn("benchmark_dashboard.html", rendered)
        self.assertIn("access_readiness_dashboard.html", rendered)
        self.assertIn("platform_parser_dashboard.html", rendered)
        self.assertIn("platform_parser_validation_dashboard.html", rendered)
        self.assertIn("platform_parser_sample_dashboard.html", rendered)
        self.assertIn("attachment_parser_dashboard.html", rendered)
        self.assertIn("gap_foo", rendered)
        self.assertNotIn("API_KEY=", rendered)

    def test_write_ops_dashboard_creates_html(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            conn = _sample_content_db(root / "policy_documents.sqlite")
            output = root / "ops.html"
            result = write_ops_dashboard(output, conn, data_dir=root, analysis_mode=TEMPLATE_ANALYSIS_MODE)
            conn.close()
            self.assertEqual(result, str(output))
            self.assertTrue(output.exists())
            html = output.read_text(encoding="utf-8")
            self.assertIn("下一步动作", html)
            self.assertNotIn("刷新命令", html)

    def test_cli_ops_dashboard_generates_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_db = root / "source_registry.sqlite"
            content_db = root / "policy_documents.sqlite"
            output = root / "ops.html"
            conn = _sample_content_db(content_db)
            conn.close()
            out = io.StringIO()
            with redirect_stdout(out):
                code = cli_main(
                    [
                        "--db",
                        str(source_db),
                        "ops-dashboard",
                        "--content-db",
                        str(content_db),
                        "--data-dir",
                        str(root),
                        "--output",
                        str(output),
                        "--json",
                    ]
                )
            self.assertEqual(code, 0)
            payload = json.loads(out.getvalue())
            self.assertEqual(payload["run_total"], 1)
            self.assertEqual(payload["pending_gaps"], 1)
            self.assertTrue(output.exists())


def _sample_content_db(path: Path):
    conn = connect_content(path)
    init_content_database(conn)
    begin_run(conn, "2026060401", "automation")
    complete_run(
        conn,
        "2026060401",
        "completed",
        "reports/sample.pdf",
        {
            "sources_considered": 1,
            "pages_fetched": 1,
            "documents_discovered": 1,
            "new_documents": 1,
            "analyzed_documents": 1,
        },
    )
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
    upsert_report_queue_item(
        conn,
        {
            "document_id": document_id,
            "analysis_mode": TEMPLATE_ANALYSIS_MODE,
            "primary_industry": "AI / 人工智能",
            "industry_bucket": "AI / 人工智能",
            "industry_rank": 2,
            "administrative_level": "central",
            "level_rank": 1,
            "sort_time": "2026-06-04",
            "priority_score": 90,
            "first_queued_run_id": "2026060401",
        },
    )
    upsert_external_reference_gaps(
        conn,
        [
            {
                "gap_id": "gap_foo",
                "run_id": "2026060401",
                "document_id": document_id,
                "interpretation_source_id": "bing",
                "platform": "bing",
                "gap_type": "missing_api_key",
                "title": "Bing key missing",
                "url": "https://www.bing.com/search?q=test",
                "query": "测试政策 政策解读",
                "evidence_status": "missing_api_key:bing",
                "required_action": "provide_search_api_key",
                "priority_score": 95,
            }
        ],
    )
    return conn


if __name__ == "__main__":
    unittest.main()
