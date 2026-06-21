import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from arxiv_daily_push.cli import main
from arxiv_daily_push.state_machine import initial_run_record


class CliTests(unittest.TestCase):
    def test_version_command(self):
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            result = main(["version"])
        self.assertEqual(result, 0)
        self.assertEqual(buffer.getvalue().strip(), "0.2.0")

    def test_doctor_json_command_warns_without_blocking_phase1(self):
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            result = main(["doctor", "--json", "--path", "."])
        self.assertIn(result, (0, 2))
        output = buffer.getvalue()
        self.assertIn('"phase": "1"', output)
        self.assertIn('"future_runtime_commands"', output)

    def test_validate_record_json_command(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "run_record.json"
            path.write_text(json.dumps(initial_run_record("run-001", "2026-06-21", "Australia/Sydney")), encoding="utf-8")
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                result = main(["validate-record", "--path", str(path), "--json"])
        self.assertEqual(result, 0)
        self.assertIn('"status": "pass"', buffer.getvalue())


if __name__ == "__main__":
    unittest.main()
