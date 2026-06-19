import io
import json
import os
import sqlite3
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from types import SimpleNamespace
from unittest.mock import patch

ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, ROOT)

from app import cli


class CliTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp.name, "fifa_cli.db")
        self.database_url = f"sqlite:///{self.db_path}"

    def tearDown(self):
        self.tmp.cleanup()

    def run_cli(self, *args):
        buf = io.StringIO()
        test_settings = SimpleNamespace(database_url=self.database_url, model_version="rules-test")
        with patch("app.database.settings", test_settings):
            with redirect_stdout(buf):
                code = cli.main(list(args))
        return code, json.loads(buf.getvalue())

    def test_status_initializes_database(self):
        code, payload = self.run_cli("status")
        self.assertEqual(code, 0)
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["counts"]["teams"], 0)
        self.assertTrue(os.path.exists(self.db_path))

    def test_bootstrap_world_cup_and_status(self):
        code, payload = self.run_cli("bootstrap-world-cup")
        self.assertEqual(code, 0)
        self.assertEqual(payload["bootstrap"]["teams_total"], 48)

        code, status = self.run_cli("status")
        self.assertEqual(code, 0)
        self.assertEqual(status["counts"]["teams"], 48)

    def test_predict_missing_match_returns_error(self):
        code, payload = self.run_cli("predict", "--match-id", "999")
        self.assertEqual(code, 1)
        self.assertEqual(payload["status"], "error")
        self.assertIn("match not found", payload["error"])


if __name__ == "__main__":
    unittest.main()
