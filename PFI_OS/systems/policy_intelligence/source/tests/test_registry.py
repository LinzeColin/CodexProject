from __future__ import annotations

import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from source_registry.db import (
    connect,
    get_current_authority,
    init_database,
    list_sources,
    review_source,
    seed_sources,
    source_snapshot,
)
from source_registry.normalization import canonical_domain, normalize_url


class SourceRegistryTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmp.name) / "source_registry.sqlite"
        self.conn = connect(self.db_path)
        init_database(self.conn)

    def tearDown(self) -> None:
        self.conn.close()
        self.tmp.cleanup()

    def test_schema_initializes(self) -> None:
        version = self.conn.execute(
            "SELECT value FROM metadata WHERE key = 'schema_version'"
        ).fetchone()["value"]
        self.assertEqual(version, "1")

    def test_url_normalization_and_domain(self) -> None:
        self.assertEqual(
            normalize_url("HTTPS://WWW.GOV.CN:443/zhengce#section"),
            "https://www.gov.cn/zhengce",
        )
        self.assertEqual(canonical_domain("www.gov.cn"), "www.gov.cn")

    def test_seed_import_is_idempotent_and_scores_central_a(self) -> None:
        source_ids = seed_sources(self.conn, [_central_source()])
        second_ids = seed_sources(self.conn, [_central_source()])
        self.assertEqual(source_ids, second_ids)

        current = get_current_authority(self.conn, source_ids[0])
        self.assertEqual(current["effective_tier"], "A")
        self.assertGreaterEqual(current["effective_score"], 90)

        count = self.conn.execute("SELECT COUNT(*) AS count FROM sources").fetchone()[
            "count"
        ]
        self.assertEqual(count, 1)

    def test_provincial_portal_scores_a_or_b(self) -> None:
        source_id = seed_sources(self.conn, [_provincial_source()])[0]
        current = get_current_authority(self.conn, source_id)
        self.assertIn(current["effective_tier"], {"A", "B"})
        self.assertGreaterEqual(current["effective_score"], 75)

    def test_low_evidence_association_scores_c_or_d(self) -> None:
        source_id = seed_sources(self.conn, [_association_source()])[0]
        current = get_current_authority(self.conn, source_id)
        self.assertIn(current["effective_tier"], {"C", "D", "E"})
        self.assertLess(current["effective_score"], 75)

    def test_manual_review_final_score_overrides_display(self) -> None:
        source_id = seed_sources(self.conn, [_central_source()])[0]
        reviewed = review_source(
            self.conn,
            source_id,
            final_score=88,
            status="user_confirmed",
            reviewer="test",
            note="manual adjustment",
        )
        self.assertGreaterEqual(reviewed["system_score"], 90)
        self.assertEqual(reviewed["final_score"], 88)
        self.assertEqual(reviewed["effective_score"], 88)
        self.assertEqual(reviewed["effective_tier"], "B")
        self.assertEqual(reviewed["review_status"], "user_confirmed")

    def test_snapshot_contains_document_linkage_fields(self) -> None:
        source_id = seed_sources(self.conn, [_central_source()])[0]
        snapshot = source_snapshot(self.conn, source_id)
        self.assertEqual(snapshot["source_id"], source_id)
        self.assertEqual(snapshot["authority_tier_snapshot"], "A")
        self.assertGreaterEqual(snapshot["authority_score_snapshot"], 90)
        self.assertEqual(snapshot["scoring_version"], "authority-v1")

    def test_crawler_can_filter_enabled_sources(self) -> None:
        seed_sources(self.conn, [_central_source(), _disabled_source()])
        enabled = list_sources(self.conn, crawl_enabled=True)
        self.assertEqual(len(enabled), 1)
        self.assertEqual(enabled[0]["name"], "中国政府网")


def _central_source() -> dict:
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
        "evidence": [
            {
                "type": "official_directory",
                "value": "中央人民政府门户网站",
                "url": "https://www.gov.cn/",
            },
            {"type": "organization_page", "value": "国务院"},
            {"type": "sponsor_unit", "value": "国务院办公厅"},
        ],
        "aliases": [{"type": "column_url", "value": "政策", "url": "https://www.gov.cn/zhengce/"}],
    }


def _provincial_source() -> dict:
    return {
        "name": "广东省人民政府门户网站",
        "country_code": "CN",
        "country_name": "China",
        "region": "广东省",
        "administrative_level": "provincial",
        "source_type": "provincial_portal",
        "sponsor_unit": "广东省人民政府办公厅",
        "official_url": "https://www.gd.gov.cn/",
        "publishes_original_documents": True,
        "crawl_enabled": True,
        "status": "active",
        "evidence": [
            {"type": "official_directory", "value": "中国政府网地方政府网站目录"},
            {"type": "sponsor_unit", "value": "广东省人民政府办公厅"},
        ],
    }


def _association_source() -> dict:
    return {
        "name": "示例行业协会",
        "country_code": "CN",
        "country_name": "China",
        "region": "China",
        "administrative_level": "unknown",
        "source_type": "association",
        "official_url": "https://example.org/",
        "publishes_original_documents": False,
        "crawl_enabled": False,
        "status": "candidate",
        "evidence": [{"type": "manual_note", "value": "待核验"}],
    }


def _disabled_source() -> dict:
    source = _association_source()
    source["name"] = "禁用来源"
    source["official_url"] = "https://disabled.example.org/"
    return source


if __name__ == "__main__":
    unittest.main()
