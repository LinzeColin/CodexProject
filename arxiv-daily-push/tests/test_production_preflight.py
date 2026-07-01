from __future__ import annotations

import io
import json
import subprocess
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


def write_sparse_file(path: Path, *, mib: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as handle:
        handle.seek(mib * 1024 * 1024 - 1)
        handle.write(b"\0")


def init_git_repo(path: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=path, check=True)


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

    def test_preflight_accepts_reviewed_local_runner_secret_presence_without_leaking_values(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = build_production_preflight(
                Path(tmp),
                generated_at="2026-07-01T22:05:00+10:00",
                env={},
                command_resolver=command_resolver,
                disk_free_gib=120.0,
                memory_total_gib=16.0,
                git_scan=clean_git_scan(),
                secret_env_evidence={
                    "evidence_id": "adp_local_runner_env_file_secret_presence_v1",
                    "source": "local_runner_env_file",
                    "env_file_ref": "$HOME/.config/arxiv-daily-push/local-runner.env",
                    "present_keys": list(PRODUCTION_SECRET_ENV_KEYS),
                    "values_logged": False,
                    "reviewed": True,
                    "outside_repo": True,
                },
            )

        self.assertEqual(report["status"], "pass")
        secret_gate = next(gate for gate in report["gates"] if gate["gate_id"] == "secret_environment")
        self.assertTrue(secret_gate["passed"])
        self.assertEqual(secret_gate["evidence_id"], "adp_local_runner_env_file_secret_presence_v1")
        for key in PRODUCTION_SECRET_ENV_KEYS:
            key_record = next(item for item in secret_gate["keys"] if item["name"] == key)
            self.assertFalse(key_record["present_in_env"])
            self.assertTrue(key_record["present_in_evidence"])
        serialized = json.dumps(report)
        self.assertNotIn("smtp.example", serialized)
        self.assertNotIn("super-secret", serialized)
        self.assertFalse(validate_production_preflight(report))

    def test_git_artifact_scope_ignores_unrelated_large_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            init_git_repo(root)
            (root / "arxiv-daily-push/src").mkdir(parents=True)
            (root / "arxiv-daily-push/src/app.py").write_text("print('ok')\n", encoding="utf-8")
            write_sparse_file(
                root / "OpenAIDatabase/session_history/current-mac-20260630/current-mac-session-history.tar.gz",
                mib=21,
            )

            report = build_production_preflight(
                root,
                generated_at="2026-07-01T22:10:00+10:00",
                env=complete_env(),
                command_resolver=command_resolver,
                disk_free_gib=120.0,
                memory_total_gib=16.0,
                git_artifact_scope_roots=("arxiv-daily-push",),
            )

        self.assertEqual(report["status"], "pass")
        git_gate = next(gate for gate in report["gates"] if gate["gate_id"] == "git_artifact_hygiene")
        self.assertEqual(git_gate["scope_roots"], ["arxiv-daily-push"])
        self.assertEqual(git_gate["violations"], [])
        self.assertFalse(validate_production_preflight(report))

    def test_git_artifact_scope_blocks_large_files_inside_scope(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            init_git_repo(root)
            write_sparse_file(root / "arxiv-daily-push/media/large-runtime-artifact.bin", mib=21)

            report = build_production_preflight(
                root,
                generated_at="2026-07-01T22:15:00+10:00",
                env=complete_env(),
                command_resolver=command_resolver,
                disk_free_gib=120.0,
                memory_total_gib=16.0,
                git_artifact_scope_roots=("arxiv-daily-push",),
            )

        self.assertEqual(report["status"], "blocked")
        reasons = " ".join(report["blocking_reasons"])
        self.assertIn("git artifact hygiene violations: 1", reasons)
        self.assertIn(
            "arxiv-daily-push/media/large-runtime-artifact.bin",
            json.dumps(report),
        )
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
