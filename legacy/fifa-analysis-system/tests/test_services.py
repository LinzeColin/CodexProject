import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, ROOT)

from app.database import init_db
from app.services import build_prediction, run_backtest
import sqlite3


class ServiceTests(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        init_db(self.conn)
        self.conn.execute("INSERT INTO teams(name, country, fifa_rank) VALUES ('Australia', 'AU', 25)")
        self.conn.execute("INSERT INTO teams(name, country, fifa_rank) VALUES ('Canada', 'CA', 60)")
        self.conn.execute("INSERT INTO competitions(name, season, region) VALUES ('World Cup', '2026', 'North America')")
        self.conn.execute(
            "INSERT INTO matches(competition_id, home_team_id, away_team_id, match_time, status, home_score, away_score) VALUES (1, 1, 2, '2026-06-12T20:00:00Z', 'finished', 2, 1)"
        )
        self.conn.execute(
            "INSERT INTO team_stats(team_id, matches_played, recent_points, recent_goals_for, recent_goals_against, injury_impact, fatigue_index, news_sentiment, trend_score) VALUES (1, 5, 10, 9, 4, 0.1, 0.2, 0.2, 0.1)"
        )
        self.conn.execute(
            "INSERT INTO team_stats(team_id, matches_played, recent_points, recent_goals_for, recent_goals_against, injury_impact, fatigue_index, news_sentiment, trend_score) VALUES (2, 5, 5, 5, 8, 0.3, 0.4, -0.1, -0.1)"
        )
        self.conn.commit()

    def tearDown(self):
        self.conn.close()

    def test_prediction_probabilities_sum_to_one(self):
        payload = build_prediction(self.conn, 1)
        total = payload["home_win_probability"] + payload["draw_probability"] + payload["away_win_probability"]
        self.assertAlmostEqual(total, 1.0, places=3)
        self.assertEqual(payload["recommended_result"], "home_win")
        self.assertIn("disclaimer", payload)
        self.assertGreater(len(payload["key_factors"]), 5)

    def test_backtest_metrics(self):
        build_prediction(self.conn, 1)
        result = run_backtest(self.conn)
        self.assertEqual(result["prediction_count"], 1)
        self.assertEqual(result["top_prediction_accuracy"], 1.0)
        self.assertIn("brier_score", result)
        self.assertIn("log_loss", result)


if __name__ == "__main__":
    unittest.main()
