import os
import sqlite3
import sys
import unittest
from unittest.mock import patch

ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, ROOT)

from app.database import init_db
from app.scheduler import run_refresh_cycle


class SchedulerTests(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        init_db(self.conn)
        self.conn.execute("INSERT INTO teams(name, country, fifa_rank) VALUES ('Australia', 'AU', 25)")
        self.conn.execute("INSERT INTO teams(name, country, fifa_rank) VALUES ('Canada', 'CA', 60)")
        self.conn.execute("INSERT INTO competitions(name, season, region) VALUES ('World Cup', '2026', 'North America')")
        self.conn.execute(
            "INSERT INTO matches(competition_id, home_team_id, away_team_id, match_time, status) VALUES (1, 1, 2, '2026-06-12T20:00:00Z', 'scheduled')"
        )
        self.conn.execute(
            "INSERT INTO team_stats(team_id, matches_played, recent_points, recent_goals_for, recent_goals_against) VALUES (1, 5, 10, 9, 4)"
        )
        self.conn.execute(
            "INSERT INTO team_stats(team_id, matches_played, recent_points, recent_goals_for, recent_goals_against) VALUES (2, 5, 5, 5, 8)"
        )
        self.conn.execute(
            "INSERT INTO crawl_sources(name, base_url, source_type, enabled) VALUES ('Test RSS', 'https://example.com/rss.xml', 'rss', 1)"
        )
        self.conn.commit()

    def tearDown(self):
        self.conn.close()

    @patch("app.scheduler._run_source", return_value={"status": "completed", "inserted": 2, "summary": "ok"})
    def test_refresh_cycle_crawls_sources_and_creates_reports(self, _run_source):
        result = run_refresh_cycle(self.conn)
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["sources_checked"], 1)
        self.assertEqual(result["articles_inserted"], 2)
        self.assertEqual(result["matches_refreshed"], 1)
        self.assertEqual(result["reports_created"], 1)
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM predictions").fetchone()[0], 1)
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM reports").fetchone()[0], 1)


if __name__ == "__main__":
    unittest.main()
