from __future__ import annotations

import json
import io
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from typing import Any
from unittest.mock import patch


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from memory_atlas_owner_daily import (  # noqa: E402
    MAX_RESULT_BYTES,
    OWNER_DAILY_API_VERSION,
    OWNER_DAILY_RESULT_VERSION,
    OWNER_DAILY_STEP_IDS,
    OwnerDailyContext,
    OwnerDailyRequestError,
    OwnerDailyRunner,
    build_child_environment,
    owner_daily_profile_contract,
)
import atlasctl  # noqa: E402


EXPECTED_STEP_IDS = (
    "sync",
    "analyze",
    "build-atlas",
    "audit",
    "push",
    "proposals",
    "generate-personalization-prompt",
    "deep-explore",
)


def step_id_from_argv(argv: list[str]) -> str:
    for step_id in EXPECTED_STEP_IDS:
        if step_id in argv:
            return step_id
    raise AssertionError(f"unknown fixed owner-daily argv: {argv}")


def safe_payload(step_id: str) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "status": "PASS",
        "command": step_id,
        "dry_run": True,
        "writes_files": False,
    }
    if step_id == "sync":
        payload.update(source_id="chatgpt")
    elif step_id == "analyze":
        payload.update(
            status="phase_s05_p3_evidence_refs_completed_pending_s05_review",
            task_id="MA-V12-S05P3",
            event_count=278,
            events=[{"event_id": f"event-{index}"} for index in range(50)],
            phase_boundary={"does_not_modify_raw": True},
        )
    elif step_id == "build-atlas":
        payload.update(output="data/derived/visualization/memory_atlas.json")
    elif step_id == "audit":
        payload.update(
            task_id="MA-V12-S14P2",
            raw_mutation=False,
            remote_push=False,
            gates=[{"gate_id": "fixture"}] * 50,
        )
    elif step_id == "push":
        payload.update(remote_push=False, github_main_upload=False, changed_file_count=3)
    elif step_id == "proposals":
        payload.update(raw_mutation=False, proposal_count=2, proposal_apply_execution=False)
    elif step_id == "generate-personalization-prompt":
        payload.update(raw_mutation=False, sends_to_chatgpt=False, targets=["chatgpt", "codex", "other-agent"])
    elif step_id == "deep-explore":
        payload.update(raw_mutation=False, sends_to_chatgpt=False, opens_browser=False, mode="prefill_only")
    return payload


class RecordingRunner:
    def __init__(self, overrides: dict[str, Any] | None = None) -> None:
        self.calls: list[dict[str, Any]] = []
        self.overrides = overrides or {}

    def __call__(
        self,
        argv: list[str],
        *,
        cwd: Path,
        env: dict[str, str],
        timeout_seconds: int,
        shell: bool,
        max_output_bytes: int,
    ) -> Any:
        step_id = step_id_from_argv(argv)
        self.calls.append(
            {
                "step_id": step_id,
                "argv": list(argv),
                "cwd": cwd,
                "env": dict(env),
                "timeout_seconds": timeout_seconds,
                "shell": shell,
                "max_output_bytes": max_output_bytes,
            }
        )
        override = self.overrides.get(step_id)
        if isinstance(override, BaseException):
            raise override
        if callable(override):
            return override(step_id)
        payload = override if isinstance(override, dict) else safe_payload(step_id)
        return subprocess.CompletedProcess(argv, 0, json.dumps(payload, ensure_ascii=False), "")


class OwnerDailyRunnerTests(unittest.TestCase):
    def make_runner(self, root: Path, process_runner: RecordingRunner) -> OwnerDailyRunner:
        (root / "scripts").mkdir(parents=True, exist_ok=True)
        (root / "scripts" / "atlasctl.py").write_text("# fixture\n", encoding="utf-8")
        return OwnerDailyRunner(
            OwnerDailyContext(
                source_root=root,
                python_executable="/fixed/python3",
                timeout_seconds=17,
            ),
            process_runner=process_runner,
            base_env={
                "PATH": "/usr/bin:/bin",
                "HOME": "/tmp/owner-home",
                "LANG": "zh_CN.UTF-8",
                "OPENAI_API_KEY": "must-not-pass",
                "SESSION_COOKIE": "must-not-pass",
            },
        )

    def test_registry_preserves_historical_order_and_fixed_dry_run_argv(self) -> None:
        contract = owner_daily_profile_contract()
        self.assertEqual(OWNER_DAILY_API_VERSION, "memory_atlas_owner_daily_api.v1_2_r5")
        self.assertEqual(OWNER_DAILY_RESULT_VERSION, "memory_atlas_owner_daily_result.v1_2_r5")
        self.assertEqual(OWNER_DAILY_STEP_IDS, EXPECTED_STEP_IDS)
        self.assertEqual(contract["task_id"], "MA-V12-S14P1")
        self.assertEqual(contract["acceptance_id"], "ACC-MA-V12-S14P1")
        self.assertEqual(contract["contract_version"], "atlasctl_unified_cli.v1_2_s14_p1")
        self.assertEqual(contract["phase_status"], "phase_s14_p1_unified_cli_completed_pending_s14_p2")
        self.assertEqual([item["command_id"] for item in contract["commands"]], list(EXPECTED_STEP_IDS))
        for item in contract["commands"]:
            self.assertTrue(item["dry_run"])
            self.assertEqual(item["invocation"][:2], ["python3", "scripts/atlasctl.py"])
            self.assertIn("--dry-run", item["invocation"])
        self.assertFalse(contract["writes_files"])
        self.assertFalse(contract["remote_push"])
        self.assertFalse(contract["github_main_upload"])
        self.assertTrue(contract["phase_boundary"]["does_not_run_final_audit"])

    def test_run_executes_all_eight_steps_sequentially_and_returns_bounded_pass(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            process_runner = RecordingRunner()
            runner = self.make_runner(root, process_runner)
            result = runner.run()

        self.assertEqual([call["step_id"] for call in process_runner.calls], list(EXPECTED_STEP_IDS))
        self.assertTrue(all(call["shell"] is False for call in process_runner.calls))
        self.assertTrue(all(call["cwd"] == root.resolve() for call in process_runner.calls))
        self.assertTrue(all(call["timeout_seconds"] == 17 for call in process_runner.calls))
        self.assertFalse(any("KEY" in key or "COOKIE" in key for key in process_runner.calls[0]["env"]))
        self.assertEqual(result["schema_version"], OWNER_DAILY_RESULT_VERSION)
        self.assertEqual(result["action"], "run")
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["completed_count"], 8)
        self.assertEqual(result["failed_count"], 0)
        self.assertEqual(result["retryable_step_ids"], [])
        self.assertRegex(result["conclusion_zh"], r"[\u4e00-\u9fff]")
        self.assertEqual([step["status"] for step in result["steps"]], ["pass"] * 8)
        self.assertEqual(
            result["safety"],
            {
                "writes_files": False,
                "remote_push": False,
                "raw_mutation": False,
                "sends_to_chatgpt": False,
                "proposal_apply_execution": False,
                "canonical_repo_mutation": False,
            },
        )
        serialized = json.dumps(result, ensure_ascii=False).encode("utf-8")
        self.assertLessEqual(len(serialized), MAX_RESULT_BYTES)
        self.assertNotIn("gates", result["steps"][3]["metrics"])

    def test_partial_failure_continues_later_steps_and_does_not_leak_stderr(self) -> None:
        def failed_audit(_step_id: str) -> subprocess.CompletedProcess[str]:
            return subprocess.CompletedProcess(
                ["fixture"],
                2,
                json.dumps({"status": "FAIL", "dry_run": True, "writes_files": False}),
                "private-token=must-not-leak",
            )

        with tempfile.TemporaryDirectory() as temp_dir:
            process_runner = RecordingRunner({"audit": failed_audit})
            result = self.make_runner(Path(temp_dir), process_runner).run()

        self.assertEqual([call["step_id"] for call in process_runner.calls], list(EXPECTED_STEP_IDS))
        self.assertEqual(result["status"], "PARTIAL_FAILURE")
        self.assertEqual(result["completed_count"], 7)
        self.assertEqual(result["failed_count"], 1)
        self.assertEqual(result["retryable_step_ids"], ["audit"])
        failed = next(step for step in result["steps"] if step["step_id"] == "audit")
        self.assertEqual(failed["status"], "failed")
        self.assertTrue(failed["retryable"])
        self.assertRegex(failed["failure_zh"], r"[\u4e00-\u9fff]")
        self.assertNotIn("private-token", json.dumps(result, ensure_ascii=False))

    def test_retry_runs_only_one_known_fixed_step(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            process_runner = RecordingRunner()
            runner = self.make_runner(Path(temp_dir), process_runner)
            result = runner.retry("audit")
            self.assertEqual([call["step_id"] for call in process_runner.calls], ["audit"])
            self.assertEqual(result["action"], "retry")
            self.assertEqual(result["requested_step_id"], "audit")
            self.assertEqual([step["step_id"] for step in result["steps"]], ["audit"])
            with self.assertRaises(OwnerDailyRequestError):
                runner.retry("audit; rm -rf /")
            with self.assertRaises(OwnerDailyRequestError):
                runner.retry("")
            self.assertEqual([call["step_id"] for call in process_runner.calls], ["audit"])

    def test_malformed_oversized_timeout_and_unsafe_outputs_fail_closed(self) -> None:
        cases: dict[str, Any] = {
            "malformed": lambda _step_id: subprocess.CompletedProcess(["fixture"], 0, "not-json", ""),
            "oversized": lambda _step_id: subprocess.CompletedProcess(
                ["fixture"], 0, "{" + ("x" * (2 * 1024 * 1024)) + "}", ""
            ),
            "timeout": subprocess.TimeoutExpired(["fixture"], 1),
            "unsafe": {"status": "PASS", "command": "audit", "dry_run": True, "writes_files": True},
        }
        for label, override in cases.items():
            with self.subTest(label=label), tempfile.TemporaryDirectory() as temp_dir:
                process_runner = RecordingRunner({"audit": override})
                result = self.make_runner(Path(temp_dir), process_runner).retry("audit")
                self.assertEqual(result["status"], "PARTIAL_FAILURE")
                self.assertEqual(result["failed_count"], 1)
                self.assertEqual(result["retryable_step_ids"], ["audit"])
                self.assertRegex(result["steps"][0]["failure_zh"], r"[\u4e00-\u9fff]")
                self.assertLessEqual(len(json.dumps(result, ensure_ascii=False).encode("utf-8")), MAX_RESULT_BYTES)

    def test_child_environment_keeps_only_safe_runtime_keys(self) -> None:
        environment = build_child_environment(
            {
                "PATH": "/usr/bin:/bin",
                "HOME": "/tmp/home",
                "TMPDIR": "/tmp",
                "LANG": "zh_CN.UTF-8",
                "OPENAI_API_KEY": "secret",
                "CF_API_TOKEN": "secret",
                "AUTH_HEADER": "secret",
                "SESSION_COOKIE": "secret",
            }
        )
        self.assertEqual(environment["PATH"], "/usr/bin:/bin")
        self.assertEqual(environment["PYTHONDONTWRITEBYTECODE"], "1")
        self.assertFalse(any(marker in key.upper() for key in environment for marker in ("TOKEN", "SECRET", "KEY", "COOKIE", "AUTH")))


class OwnerDailyAtlasctlTests(unittest.TestCase):
    def test_cli_delegates_full_run_and_fixed_retry_to_shared_runner(self) -> None:
        class FakeOwnerDailyRunner:
            instances: list["FakeOwnerDailyRunner"] = []

            def __init__(self, context: OwnerDailyContext) -> None:
                self.context = context
                self.calls: list[str] = []
                self.instances.append(self)

            def run(self) -> dict[str, Any]:
                self.calls.append("run")
                return {"status": "PASS", "action": "run", "steps": []}

            def retry(self, step_id: str) -> dict[str, Any]:
                self.calls.append(step_id)
                return {"status": "PASS", "action": "retry", "requested_step_id": step_id, "steps": []}

        with patch.object(atlasctl, "OwnerDailyRunner", FakeOwnerDailyRunner):
            full_args = atlasctl.parse_args(["run", "--profile", "owner-daily", "--dry-run"])
            full_stdout = io.StringIO()
            with redirect_stdout(full_stdout):
                self.assertEqual(atlasctl.run_profile(full_args), 0)
            self.assertEqual(json.loads(full_stdout.getvalue())["action"], "run")
            self.assertEqual(FakeOwnerDailyRunner.instances[-1].calls, ["run"])

            retry_args = atlasctl.parse_args(
                ["run", "--profile", "owner-daily", "--dry-run", "--step", "audit"]
            )
            retry_stdout = io.StringIO()
            with redirect_stdout(retry_stdout):
                self.assertEqual(atlasctl.run_profile(retry_args), 0)
            self.assertEqual(json.loads(retry_stdout.getvalue())["requested_step_id"], "audit")
            self.assertEqual(FakeOwnerDailyRunner.instances[-1].calls, ["audit"])

    def test_cli_rejects_unknown_retry_step_before_runner_execution(self) -> None:
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            atlasctl.parse_args(["run", "--profile", "owner-daily", "--dry-run", "--step", "audit;rm"])

    def test_cli_non_dry_run_remains_fail_closed(self) -> None:
        args = atlasctl.parse_args(["run", "--profile", "owner-daily"])
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            self.assertEqual(atlasctl.run_profile(args), 2)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["status"], "FAIL_CLOSED")
        self.assertFalse(payload["writes_files"])
        self.assertFalse(payload["remote_push"])


if __name__ == "__main__":
    unittest.main()
