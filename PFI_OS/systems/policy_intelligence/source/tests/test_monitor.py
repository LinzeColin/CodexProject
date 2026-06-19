from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

from source_registry.collector import FixtureFetcher
from source_registry.content_db import begin_run, connect_content
from source_registry.db import connect, init_database, seed_sources
from source_registry.monitor import build_monitor_status
from source_registry.pipeline import PipelineConfig, run_pipeline


class MonitorTest(unittest.TestCase):
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

    def test_pipeline_writes_latest_monitor_status(self) -> None:
        result = run_pipeline(_config(self.source_db, self.content_db, self.root), fetcher=_fetcher())
        status_path = Path(result["monitor_status_path"])
        self.assertTrue(status_path.exists())
        status = json.loads(status_path.read_text(encoding="utf-8"))
        self.assertEqual(status["latest_run"]["run_id"], result["run_id"])
        self.assertEqual(status["latest_run"]["status"], "completed")
        self.assertTrue(status["report"]["exists"])
        self.assertGreaterEqual(status["queue"]["pending_count"], 0)
        self.assertIn("quality_gate", status)
        self.assertIn("quality_gate_rules", status)
        self.assertIn("external_reference_gaps", status)

    def test_monitor_status_reports_quality_gap(self) -> None:
        run_pipeline(_config(self.source_db, self.content_db, self.root), fetcher=_fetcher())
        conn = connect_content(self.content_db)
        status = build_monitor_status(
            conn,
            self.root / "data",
            "template_zh_single_v1",
            min_external_references=5,
            min_external_platforms=2,
        )
        conn.close()
        self.assertEqual(status["overall_status"], "attention")
        self.assertFalse(status["quality_gate"]["met"])
        self.assertGreaterEqual(status["quality_gate_rules"]["summary"]["hard_gate_count"], 6)
        self.assertGreaterEqual(status["external_reference_gaps"]["pending_count"], 1)
        self.assertTrue(any(alert["code"] == "quality_gate_gap" for alert in status["alerts"]))
        self.assertTrue(
            any(alert["code"] == "external_reference_gap_queue" for alert in status["alerts"])
        )

    def test_monitor_uses_latest_completed_report_when_newer_run_is_running(self) -> None:
        result = run_pipeline(_config(self.source_db, self.content_db, self.root), fetcher=_fetcher())
        conn = connect_content(self.content_db)
        running_run_id = str(int(result["run_id"]) + 1)
        begin_run(conn, running_run_id, "automation")
        status = build_monitor_status(
            conn,
            self.root / "data",
            "template_zh_single_v1",
            min_external_references=0,
            min_external_platforms=0,
        )
        conn.close()
        self.assertEqual(status["latest_run"]["run_id"], running_run_id)
        self.assertEqual(status["latest_report_run"]["run_id"], result["run_id"])
        self.assertEqual(status["report"]["path"], result["report_path"])
        self.assertTrue(any(alert["code"] == "latest_run_not_completed" for alert in status["alerts"]))


def _config(source_db: Path, content_db: Path, root: Path) -> PipelineConfig:
    return PipelineConfig(
        source_db_path=source_db,
        content_db_path=content_db,
        data_dir=root / "data",
        report_dir=root / "reports",
        max_sources=1,
        max_pages_per_source=1,
        max_links_per_page=5,
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
                    <a href="/policy/notice.html">关于推进先进制造业发展的通知</a>
                  </body>
                </html>
            """,
            "https://example.gov.cn/policy/notice.html": """
                <html>
                  <head><title>关于推进先进制造业发展的通知</title></head>
                  <body>围绕先进制造、装备制造和工业母机出台支持政策。</body>
                </html>
            """,
        }
    )


def _source() -> dict:
    return {
        "name": "Example Gov",
        "country_code": "CN",
        "country_name": "China",
        "region": "China",
        "administrative_level": "national",
        "source_type": "government_portal",
        "sponsor_unit": "国务院办公厅",
        "official_url": "https://example.gov.cn/",
        "publishes_original_documents": True,
        "crawl_enabled": True,
        "crawl_priority": 1,
        "status": "active",
        "evidence": [{"type": "official_directory", "value": "Example"}],
        "aliases": [{"type": "column_url", "value": "政策", "url": "https://example.gov.cn/"}],
    }


if __name__ == "__main__":
    unittest.main()
