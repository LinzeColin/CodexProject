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
        self.assertEqual(buffer.getvalue().strip(), "0.11.16")

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

    def test_send_notification_json_command_defaults_to_dry_run(self):
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            result = main(
                [
                    "send-notification",
                    "--run-id",
                    "run-001",
                    "--summary",
                    "Daily status",
                    "--date",
                    "2026-06-21",
                    "--generated-at",
                    "2026-06-21T05:00:00+10:00",
                    "--json",
                ]
            )
        self.assertEqual(result, 0)
        payload = json.loads(buffer.getvalue())
        self.assertEqual(payload["status"], "dry_run")
        self.assertFalse(payload["real_smtp_send_enabled"])

    def test_publish_release_json_command_defaults_to_dry_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            asset = Path(tmp) / "trial-evidence.json"
            asset.write_text('{"status":"pass"}\n', encoding="utf-8")
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                result = main(
                    [
                        "publish-release",
                        "--tag",
                        "adp-test-20260621",
                        "--title",
                        "ADP test release",
                        "--notes",
                        "Release notes",
                        "--asset",
                        str(asset),
                        "--generated-at",
                        "2026-06-21T05:00:00+10:00",
                        "--json",
                    ]
                )
        self.assertEqual(result, 0)
        payload = json.loads(buffer.getvalue())
        self.assertEqual(payload["status"], "dry_run")
        self.assertFalse(payload["release_upload_enabled"])
        self.assertFalse(payload["notes"]["notes_logged"])


if __name__ == "__main__":
    unittest.main()
