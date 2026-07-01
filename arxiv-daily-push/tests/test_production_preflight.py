from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from arxiv_daily_push.production_preflight import (
    PRODUCTION_REQUIRED_COMMANDS,
    PRODUCTION_SECRET_ENV_KEYS,
    build_production_preflight,
    validate_production_preflight,
)


def complete_env() -> dict[str, str]:
    return {key: f"present-{key.lower()}" for key in PRODUCTION_SECRET_ENV_KEYS}


def command_resolver(command: str) -> str | None:
    return f"/usr/local/bin/{command}" if command in PRODUCTION_REQUIRED_COMMANDS else None


def clean_git_scan() -> dict:
    return {"gate_id": "git_artifact_hygiene", "passed": True, "blocking_reasons": [], "violations": []}


class ProductionPreflightTests(unittest.TestCase):
    def test_preflight_passes_with_all_required_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = build_production_preflight(
                Path(tmp),
                generated_at="2026-07-01T04:45:00+10:00",
                env=complete_env(),
                command_resolver=command_resolver,
                disk_free_gib=120.0,
                memory_total_gib=16.0,
                git_scan=clean_git_scan(),
            )

        self.assertEqual(report["status"], "pass")
        self.assertTrue(report["production_run_allowed"])
        self.assertFalse(report["secret_policy"]["secret_values_logged"])
        self.assertFalse(validate_production_preflight(report))

    def test_preflight_blocks_missing_command_and_secret_without_leaking_value(self) -> None:
        env = complete_env()
        env.pop("ADP_SMTP_PASSWORD")

        def missing_gh(command: str) -> str | None:
            if command == "gh":
                return None
            return command_resolver(command)

        with tempfile.TemporaryDirectory() as tmp:
            report = build_production_preflight(
                Path(tmp),
                generated_at="2026-07-01T04:45:00+10:00",
                env=env,
                command_resolver=missing_gh,
                disk_free_gib=120.0,
                memory_total_gib=16.0,
                git_scan=clean_git_scan(),
            )

        self.assertEqual(report["status"], "blocked")
        self.assertFalse(report["production_run_allowed"])
        reasons = " ".join(report["blocking_reasons"])
        self.assertIn("missing production runtime commands: gh", reasons)
        self.assertIn("ADP_SMTP_PASSWORD", reasons)
        self.assertNotIn("present-", json.dumps(report))
        self.assertFalse(validate_production_preflight(report))

    def test_preflight_accepts_reviewed_github_pr_equivalent_when_gh_is_missing(self) -> None:
        def missing_gh(command: str) -> str | None:
            if command == "gh":
                return None
            return command_resolver(command)

        with tempfile.TemporaryDirectory() as tmp:
            report = build_production_preflight(
                Path(tmp),
                generated_at="2026-07-01T21:05:00+10:00",
                env=complete_env(),
                command_resolver=missing_gh,
                disk_free_gib=120.0,
                memory_total_gib=16.0,
                git_scan=clean_git_scan(),
                github_cli_equivalent={
                    "equivalent_id": "github_open_pr_count_zero_api_v1",
                    "source": "github_api",
                    "open_pr_count": 0,
                    "reviewed": True,
                },
            )

        self.assertEqual(report["status"], "pass")
        self.assertTrue(report["production_run_allowed"])
        command_gate = next(gate for gate in report["gates"] if gate["gate_id"] == "required_commands")
        gh_command = next(command for command in command_gate["commands"] if command["command"] == "gh")
        self.assertFalse(gh_command["available"])
        self.assertTrue(gh_command["equivalent_accepted"])
        self.assertEqual(gh_command["equivalent_id"], "github_open_pr_count_zero_api_v1")
        self.assertNotIn("missing production runtime commands: gh", " ".join(report["blocking_reasons"]))
        self.assertFalse(validate_production_preflight(report))

    def test_preflight_blocks_low_disk_and_memory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = build_production_preflight(
                Path(tmp),
                generated_at="2026-07-01T04:45:00+10:00",
                env=complete_env(),
                command_resolver=command_resolver,
                disk_free_gib=4.0,
                memory_total_gib=4.0,
                git_scan=clean_git_scan(),
            )

        reasons = " ".join(report["blocking_reasons"])
        self.assertIn("free disk 4.00 GiB is below required 8.00 GiB", reasons)
        self.assertIn("memory 4.00 GiB is below required 8.00 GiB", reasons)

    def test_cli_preflight_production_outputs_blocked_json(self) -> None:
        from arxiv_daily_push.cli import main

        buffer = io.StringIO()
        with redirect_stdout(buffer):
            result = main(["preflight-production", "--path", ".", "--generated-at", "2026-07-01T04:45:00+10:00", "--json"])

        payload = json.loads(buffer.getvalue())
        self.assertEqual(result, 2)
        self.assertEqual(payload["validator_id"], "adp-production-preflight-v1")
        self.assertEqual(payload["status"], "blocked")
        self.assertIn("blocking_reasons", payload)


if __name__ == "__main__":
    unittest.main()
