import tempfile
import unittest
from pathlib import Path

from arxiv_daily_push.release_delivery import deliver_release, validate_release_delivery_report


class ReleaseDeliveryTests(unittest.TestCase):
    def test_release_delivery_dry_run_does_not_call_gh(self):
        with tempfile.TemporaryDirectory() as tmp:
            asset = Path(tmp) / "trial-evidence.json"
            asset.write_text('{"status":"pass"}\n', encoding="utf-8")
            called = []

            report = deliver_release(
                tag="adp-test-20260621",
                title="ADP test release",
                notes="Dry-run release notes",
                asset_paths=[asset],
                generated_at="2026-06-21T05:00:00+10:00",
                command_resolver=lambda _name: None,
                command_runner=lambda command: called.append(command) or {"returncode": 0},
            )

        self.assertEqual(report["status"], "dry_run")
        self.assertFalse(report["release_upload_enabled"])
        self.assertEqual(called, [])
        self.assertFalse(report["notes"]["notes_logged"])
        self.assertEqual(len(report["assets"][0]["sha256"]), 64)
        self.assertEqual(validate_release_delivery_report(report), [])

    def test_release_delivery_blocks_real_upload_without_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            asset = Path(tmp) / "run-record.json"
            asset.write_text('{"run_id":"run-001"}\n', encoding="utf-8")

            report = deliver_release(
                tag="adp-test-20260621",
                title="ADP test release",
                notes="Release notes",
                asset_paths=[asset],
                generated_at="2026-06-21T05:00:00+10:00",
                allow_upload=True,
                env={},
                command_resolver=lambda _name: "/usr/bin/gh",
            )

        self.assertEqual(report["status"], "blocked")
        self.assertIn("ADP_RELEASE_TARGET", " ".join(report["blocking_reasons"]))
        self.assertEqual(validate_release_delivery_report(report), [])

    def test_release_delivery_blocks_secret_like_asset(self):
        with tempfile.TemporaryDirectory() as tmp:
            asset = Path(tmp) / "id_rsa"
            asset.write_text("private-key-material", encoding="utf-8")

            report = deliver_release(
                tag="adp-test-20260621",
                title="ADP test release",
                notes="Release notes",
                asset_paths=[asset],
                generated_at="2026-06-21T05:00:00+10:00",
                command_resolver=lambda _name: "/usr/bin/gh",
            )

        self.assertEqual(report["status"], "blocked")
        self.assertIn("forbidden", " ".join(report["blocking_reasons"]))
        self.assertNotIn("private-key-material", str(report))
        self.assertEqual(validate_release_delivery_report(report), [])

    def test_release_delivery_creates_release_with_mocked_gh(self):
        commands = []

        def fake_runner(command):
            commands.append(list(command))
            return {"returncode": 0}

        with tempfile.TemporaryDirectory() as tmp:
            asset = Path(tmp) / "trial-evidence.json"
            asset.write_text('{"status":"pass"}\n', encoding="utf-8")

            report = deliver_release(
                tag="adp-test-20260621",
                title="ADP test release",
                notes="Release notes",
                asset_paths=[asset],
                generated_at="2026-06-21T05:00:00+10:00",
                allow_upload=True,
                env={"ADP_RELEASE_TARGET": "abc123"},
                command_resolver=lambda _name: "/usr/bin/gh",
                command_runner=fake_runner,
            )

        self.assertEqual(report["status"], "created")
        self.assertEqual(report["release_ref"], "github-release://LinzeColin/CodexProject/adp-test-20260621")
        self.assertEqual(commands[0][:4], ["gh", "release", "create", "adp-test-20260621"])
        self.assertIn("--target", commands[0])
        self.assertIn("abc123", commands[0])
        self.assertIn("--draft", commands[0])
        self.assertNotIn("--clobber", commands[0])
        self.assertFalse(report["command"]["stdout_logged"])
        self.assertEqual(validate_release_delivery_report(report), [])


if __name__ == "__main__":
    unittest.main()
