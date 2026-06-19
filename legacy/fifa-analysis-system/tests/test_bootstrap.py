import os
import sqlite3
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, ROOT)

from app.bootstrap import seed_world_cup_2026
from app.database import init_db


class BootstrapTests(unittest.TestCase):
    def test_world_cup_seed_creates_48_teams_and_sources(self):
        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        try:
            init_db(conn)
            result = seed_world_cup_2026(conn)
            self.assertEqual(result["teams_total"], 48)
            self.assertGreaterEqual(result["sources_total"], 4)
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM competitions WHERE name = 'FIFA World Cup 2026'").fetchone()[0], 1)
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM news_articles WHERE source = 'system_seed'").fetchone()[0], 48)
        finally:
            conn.close()


if __name__ == "__main__":
    unittest.main()
