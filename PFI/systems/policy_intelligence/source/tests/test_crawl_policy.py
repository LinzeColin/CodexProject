from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from source_registry import crawl_policy as crawl_policy_module
from source_registry.cli import main as cli_main
from source_registry.crawl_policy import (
    build_crawl_policy_status,
    render_crawl_policy_dashboard,
    write_crawl_policy_dashboard,
)
from source_registry.db import connect, init_database, seed_sources


class CrawlPolicyTest(unittest.TestCase):
    def test_build_crawl_policy_matches_profiles_without_secrets(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            conn = connect(root / "source_registry.sqlite")
            init_database(conn)
            seed_sources(conn, [_gov_source(), _media_source()])
            status = build_crawl_policy_status(conn, policy_file="config/crawl_policies.json")
            conn.close()
        rows = {row["domain"]: row for row in status["rows"]}
        self.assertEqual(rows["www.gov.cn"]["profile"], "official_government")
        self.assertEqual(rows["www.people.cn"]["profile"], "public_media_or_site")
        self.assertEqual(status["summary"]["source_count"], 2)
        self.assertEqual(status["summary"]["policy_ready"], 2)
        self.assertEqual(status["summary"]["robots_checked_count"], 0)
        self.assertEqual(rows["www.gov.cn"]["robots_check_status"], "not_checked")
        encoded = json.dumps(status, ensure_ascii=False)
        self.assertNotIn("SESSDATA=", encoded)
        self.assertNotIn("API_KEY=", encoded)

    def test_build_crawl_policy_online_robots_check_marks_disallowed(self) -> None:
        class FakeResponse:
            status = 200

            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def read(self, _limit: int) -> bytes:
                return b"User-agent: *\nDisallow: /\n"

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            conn = connect(root / "source_registry.sqlite")
            init_database(conn)
            seed_sources(conn, [_gov_source()])
            with patch.object(crawl_policy_module.urllib.request, "urlopen", return_value=FakeResponse()):
                status = build_crawl_policy_status(conn, check_robots=True)
            conn.close()
        row = status["rows"][0]
        self.assertEqual(status["summary"]["robots_checked_count"], 1)
        self.assertEqual(status["summary"]["robots_disallowed_count"], 1)
        self.assertEqual(row["robots_check_status"], "disallowed")
        self.assertFalse(row["robots_allowed"])

    def test_render_crawl_policy_dashboard_contains_compliance_boundary(self) -> None:
        status = {
            "generated_at": "2026-06-04T00:00:00",
            "operator_contact": "本地占位联系人",
            "default_user_agent": "PolicyIntelligenceBot/0.1",
            "summary": {
                "source_count": 1,
                "policy_ready": 1,
                "needs_review": 0,
                "respect_robots_count": 1,
                "rate_limited_count": 1,
                "long_retention_count": 1,
            },
            "profile_counts": {"official_government": 1},
            "blocked_handling_counts": {"record_gap_only": 1},
            "rows": [
                {
                    "name": "中国政府网",
                    "domain": "www.gov.cn",
                    "profile": "official_government",
                    "policy_status": "ready",
                    "respect_robots": True,
                    "min_delay_seconds": 1.0,
                    "max_retries": 2,
                    "snapshot_retention_days": 1825,
                    "blocked_handling": "record_gap_only",
                    "robots_url": "https://www.gov.cn/robots.txt",
                }
            ],
            "compliance_boundary": "不绕过验证码、付费墙、登录访问控制。",
        }
        rendered = render_crawl_policy_dashboard(status)
        self.assertIn("抓取策略与合规边界", rendered)
        self.assertIn("来源抓取策略明细", rendered)
        self.assertIn("Robots", rendered)
        self.assertIn("在线结果", rendered)
        self.assertIn("https://www.gov.cn/robots.txt", rendered)
        self.assertNotIn("cookie_file", rendered)

    def test_cli_crawl_policy_generates_dashboard(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db_path = root / "source_registry.sqlite"
            output = root / "crawl_policy.html"
            conn = connect(db_path)
            init_database(conn)
            seed_sources(conn, [_gov_source()])
            conn.close()
            out = io.StringIO()
            with redirect_stdout(out):
                code = cli_main(
                    [
                        "--db",
                        str(db_path),
                        "crawl-policy",
                        "--output",
                        str(output),
                        "--json",
                    ]
                )
            self.assertEqual(code, 0)
            payload = json.loads(out.getvalue())
            self.assertEqual(payload["dashboard_path"], str(output))
            self.assertEqual(payload["summary"]["source_count"], 1)
            self.assertTrue(output.exists())

    def test_write_crawl_policy_dashboard_creates_html(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            conn = connect(root / "source_registry.sqlite")
            init_database(conn)
            seed_sources(conn, [_gov_source()])
            output = root / "crawl_policy.html"
            result = write_crawl_policy_dashboard(output, conn)
            conn.close()
            self.assertEqual(result, str(output))
            self.assertTrue(output.exists())


def _gov_source() -> dict:
    return {
        "name": "中国政府网",
        "country_code": "CN",
        "country_name": "China",
        "region": "China",
        "administrative_level": "national",
        "source_type": "government_portal",
        "sponsor_unit": "国务院办公厅",
        "supervisor_unit": "国务院办公厅",
        "official_url": "https://www.gov.cn/",
        "publishes_original_documents": True,
        "crawl_enabled": True,
        "crawl_priority": 1,
        "status": "active",
        "evidence": [{"type": "official_directory", "value": "中央人民政府门户网站", "url": "https://www.gov.cn/"}],
    }


def _media_source() -> dict:
    return {
        "name": "人民网",
        "country_code": "CN",
        "country_name": "China",
        "administrative_level": "national",
        "source_type": "official_media",
        "official_url": "https://www.people.cn/",
        "publishes_original_documents": False,
        "crawl_enabled": True,
        "crawl_priority": 40,
        "status": "active",
        "evidence": [{"type": "about_page", "value": "public media site", "url": "https://www.people.cn/"}],
    }


if __name__ == "__main__":
    unittest.main()
