import os
import sqlite3
import sys
import unittest
from unittest.mock import patch

ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, ROOT)

from app.crawler import crawl_source
from app.database import init_db


RSS = b"""<?xml version="1.0"?>
<rss version="2.0">
  <channel>
    <item>
      <title>Team injury update before qualifier</title>
      <link>https://example.com/injury</link>
      <pubDate>Wed, 03 Jun 2026 10:00:00 GMT</pubDate>
    </item>
  </channel>
</rss>
"""


class CrawlerTests(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        self.conn.row_factory = sqlite3.Row
        init_db(self.conn)
        self.conn.execute(
            "INSERT INTO crawl_sources(name, base_url, source_type, enabled) VALUES ('Test RSS', 'https://example.com/rss.xml', 'rss', 1)"
        )
        self.conn.execute("INSERT INTO crawl_jobs(source_id, status) VALUES (1, 'running')")
        self.conn.commit()

    def tearDown(self):
        self.conn.close()

    @patch("app.crawler._robots_allowed", return_value=(True, "ok"))
    @patch("app.crawler._fetch", return_value=RSS)
    def test_rss_crawl_inserts_news_articles(self, _fetch, _robots):
        source = dict(self.conn.execute("SELECT * FROM crawl_sources WHERE id = 1").fetchone())
        result = crawl_source(self.conn, source, 1)
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["inserted"], 1)
        article = self.conn.execute("SELECT * FROM news_articles").fetchone()
        self.assertEqual(article["title"], "Team injury update before qualifier")
        self.assertEqual(article["source"], "Test RSS")


if __name__ == "__main__":
    unittest.main()
