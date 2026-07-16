from __future__ import annotations

import inspect
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

OPENAI_DATABASE_ROOT = Path(__file__).resolve().parents[2]
MACDATA_ROOT = OPENAI_DATABASE_ROOT / "macdata"
if str(OPENAI_DATABASE_ROOT) not in sys.path:
    sys.path.insert(0, str(OPENAI_DATABASE_ROOT))

from macdata import automation_c


def load_config(device: str) -> dict:
    return json.loads(
        (MACDATA_ROOT / device / "config" / "device_config.json").read_text(
            encoding="utf-8"
        )
    )


class AutomationCPublisherTests(unittest.TestCase):
    def test_device_configs_are_main_only_and_namespaced(self):
        for device in ("airM2", "proM2"):
            with self.subTest(device=device):
                config = automation_c.validate_config(load_config(device))
                self.assertEqual(config["base_branch"], "main")
                self.assertEqual(
                    config["transaction_task_id"],
                    "TSK.OpenAIDatabase.CLEAN1.0001",
                )
                self.assertEqual(
                    config["transaction_acceptance_id"],
                    "ACC.OpenAIDatabase.CLEAN1.0001",
                )
                self.assertEqual(
                    config["legacy_archive_branch"], f"macdata-{device}"
                )
                self.assertTrue(
                    config["transaction_branch_prefix"].startswith("automation-c/")
                )

    def test_real_snapshot_simulation_is_local_only_and_device_scoped(self):
        for device in ("airM2", "proM2"):
            with self.subTest(device=device), mock.patch.object(
                automation_c,
                "_run",
                side_effect=AssertionError("simulation must not call git or gh"),
            ):
                plan = automation_c.simulate_snapshot(
                    MACDATA_ROOT / device,
                    load_config(device),
                    "raw",
                    f"{device}-20260716-010000",
                )
                self.assertEqual(plan["mode"], "LOCAL_SIMULATION_NO_REMOTE_WRITE")
                self.assertEqual(plan["base_branch"], "main")
                self.assertEqual(plan["issue_mutations"], 0)
                self.assertTrue(
                    plan["transaction_branch"].startswith(
                        f"automation-c/macdata-{device}-"
                    )
                )
                self.assertNotEqual(
                    plan["transaction_branch"], plan["legacy_archive_branch"]
                )
                self.assertEqual(plan["snapshot"]["file_count"], 17)
                self.assertGreater(plan["snapshot"]["total_bytes"], 0)

    def test_transaction_branch_is_deterministic_and_not_duplicated(self):
        config = load_config("airM2")
        branch = automation_c.transaction_branch_name(
            config, "report", "airM2-20260716-011000"
        )
        self.assertEqual(
            branch,
            "automation-c/macdata-airM2-20260716-011000-report",
        )

    def test_config_rejects_path_escape_and_persistent_transaction_branch(self):
        config = load_config("airM2")
        config["published_paths"] = ["../proM2"]
        with self.assertRaises(automation_c.AutomationCError):
            automation_c.validate_config(config)

        config = load_config("airM2")
        config["transaction_branch_prefix"] = "macdata-airM2"
        with self.assertRaises(automation_c.AutomationCError):
            automation_c.validate_config(config)

    def test_secret_scan_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "record.json"
            path.write_text(
                json.dumps({"credential": "sk-" + ("a" * 32)}),
                encoding="utf-8",
            )
            self.assertEqual(automation_c.scan_for_secrets([path]), [path.as_posix()])

    def test_at_rest_gate_rejects_any_non_main_branch(self):
        with mock.patch.object(automation_c, "_open_counts", return_value=(0, 0)), mock.patch.object(
            automation_c,
            "_remote_heads",
            return_value={"main": "a" * 40, "macdata-airM2": "b" * 40},
        ):
            with self.assertRaisesRegex(
                automation_c.AutomationCError, "non_main"
            ):
                automation_c._require_at_rest("LinzeColin/CodexProject", "origin", "main")

    def test_pr_marker_binds_exact_head_and_base(self):
        config = load_config("proM2")
        body = automation_c._automation_c_body(
            config,
            stage="raw",
            run_value="proM2-test",
            head_sha="a" * 40,
            base_sha="b" * 40,
            manifest={
                "file_count": 1,
                "total_bytes": 2,
                "aggregate_sha256": "c" * 64,
            },
        )
        self.assertIn("task_id=TSK.OpenAIDatabase.CLEAN1.0001", body)
        self.assertIn("acceptance_id=ACC.OpenAIDatabase.CLEAN1.0001", body)
        self.assertIn(f"head_sha={'a' * 40}", body)
        self.assertIn(f"base_sha={'b' * 40}", body)

    def test_publisher_pushes_only_generated_transaction_ref(self):
        source = inspect.getsource(automation_c.publish_snapshot)
        self.assertIn('HEAD:refs/heads/{branch}', source)
        self.assertNotIn("HEAD:main", source)
        self.assertNotIn("HEAD:{normalized['legacy_archive_branch']}", source)

    def test_settlement_requires_exact_head_and_trusted_actor(self):
        payload = {
            "state": "MERGED",
            "mergedAt": "2026-07-16T00:00:00Z",
            "mergedBy": {"login": "github-actions[bot]"},
            "mergeCommit": {"oid": "c" * 40},
            "headRefName": "automation-c/macdata-airM2-test-raw",
            "headRefOid": "a" * 40,
            "baseRefName": "main",
        }
        with mock.patch.object(automation_c, "_gh_json", return_value=payload):
            settled = automation_c._wait_for_settlement(
                "LinzeColin/CodexProject",
                1,
                expected_branch="automation-c/macdata-airM2-test-raw",
                expected_head_sha="a" * 40,
                timeout_seconds=60,
                poll_seconds=2,
                cwd=MACDATA_ROOT,
            )
        self.assertEqual(settled["mergeCommit"]["oid"], "c" * 40)

    def test_settlement_rejects_manual_merge(self):
        payload = {
            "state": "MERGED",
            "mergedAt": "2026-07-16T00:00:00Z",
            "mergedBy": {"login": "human-admin"},
            "mergeCommit": {"oid": "c" * 40},
            "headRefName": "automation-c/macdata-proM2-test-raw",
            "headRefOid": "a" * 40,
            "baseRefName": "main",
        }
        with mock.patch.object(automation_c, "_gh_json", return_value=payload):
            with self.assertRaisesRegex(
                automation_c.AutomationCError, "trusted Settlement"
            ):
                automation_c._wait_for_settlement(
                    "LinzeColin/CodexProject",
                    2,
                    expected_branch="automation-c/macdata-proM2-test-raw",
                    expected_head_sha="a" * 40,
                    timeout_seconds=60,
                    poll_seconds=2,
                    cwd=MACDATA_ROOT,
                )


if __name__ == "__main__":
    unittest.main()
