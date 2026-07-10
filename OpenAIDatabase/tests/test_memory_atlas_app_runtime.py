from __future__ import annotations

import http.client
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import threading
import time
import unittest
import zipfile
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
COMMAND_BRIDGE_PATH = REPO_ROOT / "scripts" / "memory_atlas_command_bridge.py"
RUNTIME_SERVER_PATH = REPO_ROOT / "scripts" / "memory_atlas_runtime_server.py"
PROPOSAL_WORKFLOW_PATH = REPO_ROOT / "scripts" / "memory_atlas_proposal_workflow.py"
OWNER_DAILY_PATH = REPO_ROOT / "scripts" / "memory_atlas_owner_daily.py"
WEEKLY_REPORT_PATH = REPO_ROOT / "scripts" / "build_memory_atlas_weekly_report.py"
COMMAND_VALIDATOR_PATH = REPO_ROOT / "apps/memory-atlas/scripts/validate_memory_atlas_v1_2_command_workflows.cjs"


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def make_installed_workspace(root: Path) -> tuple[Path, Path, Path]:
    app_support = root / "app-support"
    source_root = app_support / "source"
    runtime_dir = app_support / "runtime"
    (source_root / "scripts").mkdir(parents=True)
    (source_root / "scripts" / "atlasctl.py").write_text("# installed fixture\n", encoding="utf-8")
    runtime_dir.mkdir(parents=True)
    (source_root / "memory_atlas_source_workspace.json").write_text(
        json.dumps(
            {
                "schema_version": "memory_atlas_source_workspace.v1",
                "original_repo_root": "/temporary/canonical/repo",
                "installed_git_commit": "fixture",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (runtime_dir / "index.html").write_text("<!doctype html><title>fixture</title>\n", encoding="utf-8")
    (runtime_dir / "memory_atlas.json").write_text(
        json.dumps(
            {
                "schema_version": "fixture",
                "overview": {"generated_at": "2026-07-10T00:00:00Z"},
                "nodes": [],
                "edges": [],
                "source_contract": {"raw_private_data_included": False},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    return app_support, source_root, runtime_dir


class RecordingRunner:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def __call__(
        self,
        argv: list[str],
        *,
        cwd: Path,
        env: dict[str, str],
        timeout_seconds: int,
        shell: bool,
    ) -> Any:
        self.calls.append(
            {
                "argv": list(argv),
                "cwd": cwd,
                "env": dict(env),
                "timeout_seconds": timeout_seconds,
                "shell": shell,
            }
        )
        if "chatgpt-deep-explore" in argv:
            payload = {
                "status": "PASS",
                "command": "chatgpt-deep-explore",
                "mode": "prefill_only",
                "launch_url": "https://chatgpt.com/?q=Memory+Atlas+fixture",
                "sends_to_chatgpt": False,
                "outputs": ["data/derived/chatgpt_deep_explore/latest_prompt.md"],
            }
        elif "generate-personalization-prompt" in argv:
            payload = {
                "status": "PASS",
                "outputs": [
                    "data/derived/personalization/chatgpt.md",
                    "data/derived/personalization/codex.md",
                    "data/derived/personalization/other_agent.md",
                ],
            }
        elif "proposals" in argv:
            payload = {"status": "PASS", "proposal_count": 2, "applies_proposals": False}
        elif "build_memory_atlas_weekly_report.py" in " ".join(argv):
            payload = {
                "status": "PASS",
                "output": "data/derived/weekly/2026-07-06.memory_atlas_weekly_report.md",
                "raw_mutation": False,
            }
        else:
            payload = {"status": "PASS", "writes_files": True}
        return type(
            "ProcessResult",
            (),
            {"returncode": 0, "stdout": json.dumps(payload, ensure_ascii=False), "stderr": ""},
        )()


class MemoryAtlasCommandBridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.proposal_module = load_module("memory_atlas_proposal_workflow", PROPOSAL_WORKFLOW_PATH)
        cls.bridge_module = load_module("memory_atlas_command_bridge_test", COMMAND_BRIDGE_PATH)

    def test_registry_is_exact_and_rejects_command_injection(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            app_support, source_root, runtime_dir = make_installed_workspace(Path(temp_dir))
            bridge = self.bridge_module.CommandBridge(
                self.bridge_module.CommandContext(
                    source_root=source_root,
                    runtime_dir=runtime_dir,
                    app_support=app_support,
                    codex_home=Path(temp_dir) / "codex-home",
                ),
                runner=RecordingRunner(),
            )
            self.assertEqual(
                tuple(bridge.command_ids),
                (
                    "sync_chatgpt",
                    "sync_codex",
                    "generate_weekly_report",
                    "view_pending_proposals",
                    "generate_personalization_prompt",
                    "chatgpt_deep_explore",
                ),
            )
            with self.assertRaises(self.bridge_module.CommandRequestError):
                bridge.execute("sync_codex; rm -rf /")
            with self.assertRaises(self.bridge_module.CommandRequestError):
                bridge.execute("apply")

    def test_child_environment_drops_credentials(self) -> None:
        child_env = self.bridge_module.build_child_environment(
            {
                "PATH": "/usr/bin:/bin",
                "HOME": "/tmp/home",
                "LANG": "zh_CN.UTF-8",
                "TMPDIR": "/tmp",
                "OPENAI_API_KEY": "must-not-pass",
                "CF_API_TOKEN": "must-not-pass",
                "SESSION_COOKIE": "must-not-pass",
                "AUTH_HEADER": "must-not-pass",
            }
        )
        self.assertEqual(child_env["PATH"], "/usr/bin:/bin")
        self.assertEqual(child_env["HOME"], "/tmp/home")
        self.assertFalse(any(marker in key.upper() for key in child_env for marker in ("TOKEN", "SECRET", "KEY", "COOKIE", "AUTH")))

    def test_workspace_must_be_installer_shaped(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_root = root / "canonical"
            runtime_dir = root / "runtime"
            source_root.mkdir()
            runtime_dir.mkdir()
            context = self.bridge_module.CommandContext(
                source_root=source_root,
                runtime_dir=runtime_dir,
                app_support=root,
                codex_home=root / "codex-home",
            )
            with self.assertRaises(self.bridge_module.CommandWorkspaceError):
                self.bridge_module.CommandBridge(context, runner=RecordingRunner())

    def test_symlinked_source_workspace_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            app_support = root / "app-support"
            canonical = root / "canonical"
            runtime_dir = app_support / "runtime"
            canonical.mkdir(parents=True)
            runtime_dir.mkdir(parents=True)
            (canonical / "memory_atlas_source_workspace.json").write_text(
                json.dumps(
                    {
                        "schema_version": "memory_atlas_source_workspace.v1",
                        "original_repo_root": "/different/canonical/path",
                        "installed_git_commit": "fixture",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            (app_support / "source").symlink_to(canonical, target_is_directory=True)
            context = self.bridge_module.CommandContext(
                source_root=app_support / "source",
                runtime_dir=runtime_dir,
                app_support=app_support,
                codex_home=root / "codex-home",
            )
            with self.assertRaises(self.bridge_module.CommandWorkspaceError):
                self.bridge_module.CommandBridge(context, runner=RecordingRunner())

    def test_source_workspace_with_git_metadata_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            app_support, source_root, runtime_dir = make_installed_workspace(root)
            (source_root / ".git").mkdir()
            context = self.bridge_module.CommandContext(
                source_root=source_root,
                runtime_dir=runtime_dir,
                app_support=app_support,
                codex_home=root / "codex-home",
            )
            with self.assertRaises(self.bridge_module.CommandWorkspaceError):
                self.bridge_module.CommandBridge(context, runner=RecordingRunner())

    def test_timeout_terminates_descendant_writer_before_returning(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            marker = root / "orphan-writer.txt"
            parent = root / "parent.py"
            parent.write_text(
                "import subprocess, sys, time\n"
                "child = 'import pathlib, sys, time; time.sleep(0.5); pathlib.Path(sys.argv[1]).write_text(\"orphan\", encoding=\"utf-8\")'\n"
                "subprocess.Popen([sys.executable, '-c', child, sys.argv[1]])\n"
                "time.sleep(30)\n",
                encoding="utf-8",
            )
            with self.assertRaises(subprocess.TimeoutExpired):
                self.bridge_module.default_process_runner(
                    [sys.executable, str(parent), str(marker)],
                    cwd=root,
                    env=self.bridge_module.build_child_environment(dict(os.environ)),
                    timeout_seconds=0.1,
                    shell=False,
                )
            time.sleep(0.8)
            self.assertFalse(marker.exists(), "timed-out descendant continued writing after the bridge returned")

    def test_chatgpt_sync_requires_one_fixed_regular_zip(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            app_support, source_root, runtime_dir = make_installed_workspace(root)
            runner = RecordingRunner()
            bridge = self.bridge_module.CommandBridge(
                self.bridge_module.CommandContext(
                    source_root=source_root,
                    runtime_dir=runtime_dir,
                    app_support=app_support,
                    codex_home=root / "codex-home",
                ),
                runner=runner,
            )
            result = bridge.execute("sync_chatgpt")
            self.assertEqual(result["status"], "needs_input")
            self.assertIn("官方导出", result["message_zh"])
            self.assertEqual(runner.calls, [])

            inbox = app_support / "imports" / "chatgpt"
            with zipfile.ZipFile(inbox / "official-export.zip", "w") as archive:
                archive.writestr("conversations.json", "[]")
            with zipfile.ZipFile(inbox / "second-export.zip", "w") as archive:
                archive.writestr("conversations.json", "[]")
            result = bridge.execute("sync_chatgpt")
            self.assertEqual(result["status"], "needs_input")
            self.assertIn("只保留一个", result["message_zh"])
            self.assertEqual(runner.calls, [])

    def test_deep_explore_is_prefill_only_and_never_opens_or_submits_in_python(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            app_support, source_root, runtime_dir = make_installed_workspace(root)
            runner = RecordingRunner()
            bridge = self.bridge_module.CommandBridge(
                self.bridge_module.CommandContext(
                    source_root=source_root,
                    runtime_dir=runtime_dir,
                    app_support=app_support,
                    codex_home=root / "codex-home",
                ),
                runner=runner,
            )
            result = bridge.execute("chatgpt_deep_explore")
            self.assertEqual(result["status"], "success")
            self.assertEqual(result["action"]["type"], "open_url")
            self.assertTrue(result["action"]["url"].startswith("https://chatgpt.com/?q="))
            self.assertFalse(result["safety"]["sends_to_chatgpt"])
            argv = runner.calls[0]["argv"]
            self.assertIn("prefill_only", argv)
            self.assertNotIn("auto_submit", argv)
            self.assertNotIn("--open", argv)
            self.assertFalse(runner.calls[0]["shell"])

    def test_bad_deep_explore_url_fails_closed_with_chinese_explanation(self) -> None:
        class BadUrlRunner(RecordingRunner):
            def __call__(self, argv: list[str], **kwargs: Any) -> Any:
                result = super().__call__(argv, **kwargs)
                if "chatgpt-deep-explore" in argv:
                    result.stdout = json.dumps(
                        {
                            "status": "PASS",
                            "mode": "prefill_only",
                            "launch_url": "https://evil.example/?q=secret",
                            "sends_to_chatgpt": False,
                        }
                    )
                return result

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            app_support, source_root, runtime_dir = make_installed_workspace(root)
            bridge = self.bridge_module.CommandBridge(
                self.bridge_module.CommandContext(
                    source_root=source_root,
                    runtime_dir=runtime_dir,
                    app_support=app_support,
                    codex_home=root / "codex-home",
                ),
                runner=BadUrlRunner(),
            )
            result = bridge.execute("chatgpt_deep_explore")
            self.assertEqual(result["status"], "error")
            self.assertRegex(result["message_zh"], r"[\u4e00-\u9fff]")
            self.assertNotIn("action", result)

    def test_zero_exit_fail_payload_is_not_reported_as_success(self) -> None:
        class FailPayloadRunner(RecordingRunner):
            def __call__(self, argv: list[str], **kwargs: Any) -> Any:
                result = super().__call__(argv, **kwargs)
                result.stdout = json.dumps({"status": "FAIL", "error": "private diagnostic"})
                return result

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            app_support, source_root, runtime_dir = make_installed_workspace(root)
            bridge = self.bridge_module.CommandBridge(
                self.bridge_module.CommandContext(
                    source_root=source_root,
                    runtime_dir=runtime_dir,
                    app_support=app_support,
                    codex_home=root / "codex-home",
                ),
                runner=FailPayloadRunner(),
            )
            result = bridge.execute("generate_personalization_prompt")
            self.assertEqual(result["status"], "error")
            self.assertRegex(result["message_zh"], r"[\u4e00-\u9fff]")
            self.assertNotIn("private diagnostic", json.dumps(result, ensure_ascii=False))

    def test_concurrent_command_is_rejected_before_second_runner_call(self) -> None:
        started = threading.Event()
        release = threading.Event()

        class BlockingRunner(RecordingRunner):
            def __call__(self, argv: list[str], **kwargs: Any) -> Any:
                started.set()
                release.wait(timeout=3)
                return super().__call__(argv, **kwargs)

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            app_support, source_root, runtime_dir = make_installed_workspace(root)
            runner = BlockingRunner()
            bridge = self.bridge_module.CommandBridge(
                self.bridge_module.CommandContext(
                    source_root=source_root,
                    runtime_dir=runtime_dir,
                    app_support=app_support,
                    codex_home=root / "codex-home",
                ),
                runner=runner,
            )
            worker = threading.Thread(target=bridge.execute, args=("generate_personalization_prompt",))
            worker.start()
            self.assertTrue(started.wait(timeout=2))
            with self.assertRaises(self.bridge_module.CommandBusyError):
                bridge.execute("view_pending_proposals")
            release.set()
            worker.join(timeout=3)
            self.assertFalse(worker.is_alive())
            self.assertEqual(len(runner.calls), 1)

    def test_proposal_review_uses_the_existing_read_command_without_expanding_registry(self) -> None:
        class FakeProposalWorkflow:
            def review(self) -> dict[str, Any]:
                return {
                    "schema_version": "memory_atlas_proposal_review.v1_2_r4",
                    "status": "success",
                    "proposals": [
                        {
                            "proposal_id": "proposal_fixture",
                            "apply_ready": True,
                            "target_files": ["config/fixture.json"],
                            "review_token": "fixture-token",
                        }
                    ],
                    "summary": {"proposal_count": 1, "apply_ready_count": 1},
                }

            def approve_and_apply(self, **_kwargs: Any) -> dict[str, Any]:
                raise AssertionError("review command must not apply")

            def rollback(self, **_kwargs: Any) -> dict[str, Any]:
                raise AssertionError("review command must not rollback")

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            app_support, source_root, runtime_dir = make_installed_workspace(root)
            bridge = self.bridge_module.CommandBridge(
                self.bridge_module.CommandContext(
                    source_root=source_root,
                    runtime_dir=runtime_dir,
                    app_support=app_support,
                ),
                runner=RecordingRunner(),
                proposal_workflow=FakeProposalWorkflow(),
            )
            result = bridge.execute("view_pending_proposals")
            self.assertEqual(tuple(bridge.command_ids), (
                "sync_chatgpt",
                "sync_codex",
                "generate_weekly_report",
                "view_pending_proposals",
                "generate_personalization_prompt",
                "chatgpt_deep_explore",
            ))
            self.assertEqual(result["status"], "success")
            self.assertEqual(result["proposal_review"]["proposals"][0]["proposal_id"], "proposal_fixture")
            self.assertFalse(result["safety"]["proposal_apply_execution"])

    def test_proposal_action_and_r3_command_share_one_operation_lock(self) -> None:
        started = threading.Event()
        release = threading.Event()

        class BlockingProposalWorkflow:
            def review(self) -> dict[str, Any]:
                return {"status": "success", "proposals": [], "summary": {"proposal_count": 0}}

            def approve_and_apply(self, **_kwargs: Any) -> dict[str, Any]:
                started.set()
                release.wait(timeout=3)
                return {
                    "schema_version": "memory_atlas_proposal_result.v1_2_r4",
                    "action": "approve_apply",
                    "status": "success",
                    "proposal_id": "proposal_fixture",
                }

            def rollback(self, **_kwargs: Any) -> dict[str, Any]:
                raise AssertionError("not used")

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            app_support, source_root, runtime_dir = make_installed_workspace(root)
            runner = RecordingRunner()
            bridge = self.bridge_module.CommandBridge(
                self.bridge_module.CommandContext(
                    source_root=source_root,
                    runtime_dir=runtime_dir,
                    app_support=app_support,
                ),
                runner=runner,
                proposal_workflow=BlockingProposalWorkflow(),
            )
            payload = {
                "action": "approve_apply",
                "proposal_id": "proposal_fixture",
                "review_token": "fixture-token",
                "confirmation": "授权应用 proposal_fixture",
            }
            worker = threading.Thread(target=bridge.execute_proposal_action, args=(payload,))
            worker.start()
            self.assertTrue(started.wait(timeout=2))
            with self.assertRaises(self.bridge_module.CommandBusyError):
                bridge.execute("generate_weekly_report")
            release.set()
            worker.join(timeout=3)
            self.assertFalse(worker.is_alive())
            self.assertEqual(runner.calls, [])

    def test_owner_daily_uses_fixed_request_contract_metadata_audit_and_existing_lock(self) -> None:
        started = threading.Event()
        release = threading.Event()

        class BlockingOwnerDailyRunner:
            def __init__(self) -> None:
                self.calls: list[str] = []

            def run(self) -> dict[str, Any]:
                self.calls.append("run")
                started.set()
                release.wait(timeout=3)
                return {
                    "schema_version": "memory_atlas_owner_daily_result.v1_2_r5",
                    "action": "run",
                    "status": "PASS",
                    "completed_count": 8,
                    "failed_count": 0,
                    "steps": [],
                }

            def retry(self, step_id: str) -> dict[str, Any]:
                self.calls.append(step_id)
                return {
                    "schema_version": "memory_atlas_owner_daily_result.v1_2_r5",
                    "action": "retry",
                    "requested_step_id": step_id,
                    "status": "PASS",
                    "completed_count": 1,
                    "failed_count": 0,
                    "steps": [],
                }

        class UnusedProposalWorkflow:
            def review(self) -> dict[str, Any]:
                raise AssertionError("shared lock must reject before proposal review")

            def approve_and_apply(self, **_kwargs: Any) -> dict[str, Any]:
                raise AssertionError("shared lock must reject before proposal apply")

            def rollback(self, **_kwargs: Any) -> dict[str, Any]:
                raise AssertionError("shared lock must reject before proposal rollback")

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            app_support, source_root, runtime_dir = make_installed_workspace(root)
            owner_runner = BlockingOwnerDailyRunner()
            bridge = self.bridge_module.CommandBridge(
                self.bridge_module.CommandContext(
                    source_root=source_root,
                    runtime_dir=runtime_dir,
                    app_support=app_support,
                ),
                runner=RecordingRunner(),
                proposal_workflow=UnusedProposalWorkflow(),
                owner_daily_runner=owner_runner,
            )
            worker = threading.Thread(target=bridge.execute_owner_daily, args=({"action": "run"},))
            worker.start()
            self.assertTrue(started.wait(timeout=2))
            with self.assertRaises(self.bridge_module.CommandBusyError):
                bridge.execute("generate_weekly_report")
            with self.assertRaises(self.bridge_module.CommandBusyError):
                bridge.execute_proposal_action(
                    {
                        "action": "approve_apply",
                        "proposal_id": "proposal_fixture",
                        "review_token": "fixture-token",
                        "confirmation": "授权应用 proposal_fixture",
                    }
                )
            release.set()
            worker.join(timeout=3)
            self.assertFalse(worker.is_alive())
            self.assertEqual(owner_runner.calls, ["run"])

            retry = bridge.execute_owner_daily({"action": "retry", "step_id": "audit"})
            self.assertEqual(retry["requested_step_id"], "audit")
            self.assertEqual(owner_runner.calls, ["run", "audit"])
            for bad_payload in (
                {"action": "run", "argv": ["rm", "-rf", "/"]},
                {"action": "retry", "step_id": "audit;rm"},
                {"action": "retry"},
                {"action": "unknown"},
            ):
                with self.subTest(payload=bad_payload), self.assertRaises(self.bridge_module.CommandRequestError):
                    bridge.execute_owner_daily(bad_payload)
            self.assertEqual(owner_runner.calls, ["run", "audit"])

            audit_path = app_support / "owner_daily_audit.jsonl"
            rows = [json.loads(line) for line in audit_path.read_text(encoding="utf-8").splitlines()]
            self.assertEqual([row["action"] for row in rows], ["run", "retry"])
            self.assertEqual(rows[1]["requested_step_id"], "audit")
            audit_text = audit_path.read_text(encoding="utf-8")
            self.assertNotIn(str(source_root), audit_text)
            self.assertNotIn("stdout", audit_text)
            self.assertNotIn("steps", audit_text)


class MemoryAtlasRuntimeServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.server_module = load_module("memory_atlas_runtime_server_test", RUNTIME_SERVER_PATH)

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        root = Path(self.temp_dir.name)
        self.app_support, self.source_root, self.runtime_dir = make_installed_workspace(root)

        class FakeBridge:
            command_ids = (
                "sync_chatgpt",
                "sync_codex",
                "generate_weekly_report",
                "view_pending_proposals",
                "generate_personalization_prompt",
                "chatgpt_deep_explore",
            )

            def __init__(self) -> None:
                self.calls: list[str] = []
                self.proposal_calls: list[dict[str, Any]] = []
                self.owner_daily_calls: list[dict[str, Any]] = []
                self.owner_daily_error: BaseException | None = None

            def execute(self, command_id: str) -> dict[str, Any]:
                self.calls.append(command_id)
                return {
                    "schema_version": "memory_atlas_command_result.v1_2_r3",
                    "command_id": command_id,
                    "status": "success",
                    "title_zh": "操作完成",
                    "message_zh": "本地受控操作已完成。",
                    "safety": {"sends_to_chatgpt": False},
                }

            def execute_proposal_action(self, payload: dict[str, Any]) -> dict[str, Any]:
                self.proposal_calls.append(dict(payload))
                return {
                    "schema_version": "memory_atlas_proposal_result.v1_2_r4",
                    "action": payload["action"],
                    "status": "success",
                    "proposal_id": payload.get("proposal_id"),
                    "transaction_id": payload.get("transaction_id", "txn_0123456789abcdef0123"),
                    "message_zh": "proposal 本地操作完成。",
                }

            def execute_owner_daily(self, payload: dict[str, Any]) -> dict[str, Any]:
                if self.owner_daily_error is not None:
                    raise self.owner_daily_error
                self.owner_daily_calls.append(dict(payload))
                step_id = payload.get("step_id")
                return {
                    "schema_version": "memory_atlas_owner_daily_result.v1_2_r5",
                    "api_version": "memory_atlas_owner_daily_api.v1_2_r5",
                    "action": payload["action"],
                    "requested_step_id": step_id,
                    "status": "PASS",
                    "completed_count": 1 if step_id else 8,
                    "failed_count": 0,
                    "steps": [],
                }

        self.bridge = FakeBridge()
        self.server = self.server_module.create_server(
            runtime_dir=self.runtime_dir,
            source_root=self.source_root,
            port=0,
            ttl_seconds=0,
            idle_seconds=0,
            command_bridge=self.bridge,
        )
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.port = int(self.server.server_address[1])

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        self.temp_dir.cleanup()

    def request(
        self,
        method: str,
        path: str,
        *,
        body: bytes | None = None,
        headers: dict[str, str] | None = None,
    ) -> tuple[int, dict[str, str], bytes]:
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=3)
        connection.request(method, path, body=body, headers=headers or {})
        response = connection.getresponse()
        response_body = response.read()
        response_headers = {key.lower(): value for key, value in response.getheaders()}
        connection.close()
        return response.status, response_headers, response_body

    def valid_headers(self) -> dict[str, str]:
        return {
            "Content-Type": "application/json",
            "Origin": f"http://127.0.0.1:{self.port}",
        }

    def test_runtime_state_advertises_loopback_command_api(self) -> None:
        self.assertEqual(self.server.server_address[0], "127.0.0.1")
        status, headers, body = self.request("GET", "/__memory_atlas_runtime_state")
        payload = json.loads(body)
        self.assertEqual(status, 200)
        self.assertEqual(payload["command_api_version"], "memory_atlas_command_api.v1_2_r3")
        self.assertEqual(payload["command_ids"], list(self.bridge.command_ids))
        self.assertEqual(payload["proposal_api_version"], "memory_atlas_proposal_api.v1_2_r4")
        self.assertEqual(payload["owner_daily_api_version"], "memory_atlas_owner_daily_api.v1_2_r5")
        self.assertEqual(payload["owner_daily_scope"], "fixed_eight_step_no_write_profile")
        self.assertNotIn("access-control-allow-origin", headers)

    def test_valid_command_request_executes_once(self) -> None:
        body = json.dumps({"command_id": "sync_codex"}).encode()
        status, headers, response_body = self.request(
            "POST",
            "/__memory_atlas_command",
            body=body,
            headers=self.valid_headers(),
        )
        payload = json.loads(response_body)
        self.assertEqual(status, 200)
        self.assertEqual(payload["command_id"], "sync_codex")
        self.assertEqual(self.bridge.calls, ["sync_codex"])
        self.assertNotIn("access-control-allow-origin", headers)

    def test_valid_proposal_approve_apply_request_executes_once(self) -> None:
        payload = {
            "action": "approve_apply",
            "proposal_id": "proposal_fixture",
            "review_token": "fixture-token",
            "confirmation": "授权应用 proposal_fixture",
        }
        body = json.dumps(payload, ensure_ascii=False).encode()
        status, headers, response_body = self.request(
            "POST",
            "/__memory_atlas_proposal_action",
            body=body,
            headers=self.valid_headers(),
        )
        result = json.loads(response_body)
        self.assertEqual(status, 200)
        self.assertEqual(result["action"], "approve_apply")
        self.assertEqual(self.bridge.proposal_calls, [payload])
        self.assertNotIn("access-control-allow-origin", headers)

    def test_valid_proposal_rollback_request_executes_once(self) -> None:
        payload = {
            "action": "rollback",
            "transaction_id": "txn_0123456789abcdef0123",
            "rollback_token": "fixture-token",
            "confirmation": "确认回滚 txn_0123456789abcdef0123",
        }
        body = json.dumps(payload, ensure_ascii=False).encode()
        status, _headers, response_body = self.request(
            "POST",
            "/__memory_atlas_proposal_action",
            body=body,
            headers=self.valid_headers(),
        )
        result = json.loads(response_body)
        self.assertEqual(status, 200)
        self.assertEqual(result["action"], "rollback")
        self.assertEqual(self.bridge.proposal_calls, [payload])

    def test_valid_owner_daily_run_and_fixed_retry_execute_once(self) -> None:
        for payload in ({"action": "run"}, {"action": "retry", "step_id": "audit"}):
            with self.subTest(payload=payload):
                status, headers, response_body = self.request(
                    "POST",
                    "/__memory_atlas_owner_daily",
                    body=json.dumps(payload).encode(),
                    headers=self.valid_headers(),
                )
                result = json.loads(response_body)
                self.assertEqual(status, 200)
                self.assertEqual(result["action"], payload["action"])
                self.assertNotIn("access-control-allow-origin", headers)
        self.assertEqual(self.bridge.owner_daily_calls, [{"action": "run"}, {"action": "retry", "step_id": "audit"}])

    def test_owner_daily_endpoint_rejects_origin_shape_step_and_busy_operation(self) -> None:
        cases = [
            ({"action": "run"}, {"Content-Type": "application/json", "Origin": "https://evil.example"}, 403),
            ({"action": "run", "argv": ["rm", "-rf", "/"]}, self.valid_headers(), 400),
            ({"action": "retry"}, self.valid_headers(), 400),
            ({"action": "retry", "step_id": "audit;rm"}, self.valid_headers(), 400),
            ({"action": "unknown"}, self.valid_headers(), 400),
        ]
        for payload, headers, expected_status in cases:
            with self.subTest(payload=payload):
                status, _response_headers, response_body = self.request(
                    "POST",
                    "/__memory_atlas_owner_daily",
                    body=json.dumps(payload).encode(),
                    headers=headers,
                )
                self.assertEqual(status, expected_status)
                self.assertRegex(json.loads(response_body)["message_zh"], r"[\u4e00-\u9fff]")
        self.assertEqual(self.bridge.owner_daily_calls, [])

        busy_error = type("CommandBusyError", (RuntimeError,), {})("private busy detail")
        self.bridge.owner_daily_error = busy_error
        status, _headers, response_body = self.request(
            "POST",
            "/__memory_atlas_owner_daily",
            body=json.dumps({"action": "run"}).encode(),
            headers=self.valid_headers(),
        )
        self.assertEqual(status, 409)
        self.assertNotIn("private busy detail", response_body.decode("utf-8"))

    def test_proposal_endpoint_rejects_remote_origin_extra_fields_unknown_action_and_wrong_shape(self) -> None:
        valid = {
            "action": "approve_apply",
            "proposal_id": "proposal_fixture",
            "review_token": "fixture-token",
            "confirmation": "授权应用 proposal_fixture",
        }
        cases = [
            (valid, {"Content-Type": "application/json", "Origin": "https://evil.example"}, 403),
            ({**valid, "target_file": "data/raw/transcript.json"}, self.valid_headers(), 400),
            ({**valid, "action": "run_argv"}, self.valid_headers(), 400),
            ({"action": "approve_apply", "proposal_id": "proposal_fixture"}, self.valid_headers(), 400),
            (
                {
                    "action": "rollback",
                    "transaction_id": "txn_0123456789abcdef0123",
                    "rollback_token": "fixture-token",
                    "confirmation": "确认回滚 txn_0123456789abcdef0123",
                    "argv": ["rm", "-rf", "/"],
                },
                self.valid_headers(),
                400,
            ),
        ]
        for payload, headers, expected_status in cases:
            with self.subTest(payload=payload):
                body = json.dumps(payload, ensure_ascii=False).encode()
                status, _response_headers, response_body = self.request(
                    "POST",
                    "/__memory_atlas_proposal_action",
                    body=body,
                    headers=headers,
                )
                self.assertEqual(status, expected_status)
                self.assertRegex(json.loads(response_body)["message_zh"], r"[\u4e00-\u9fff]")
        self.assertEqual(self.bridge.proposal_calls, [])

    def test_remote_origin_extra_fields_and_unknown_commands_fail_closed(self) -> None:
        cases = [
            (
                {"command_id": "sync_codex"},
                {"Content-Type": "application/json", "Origin": "https://evil.example"},
                403,
            ),
            (
                {"command_id": "sync_codex", "argv": ["rm", "-rf", "/"]},
                self.valid_headers(),
                400,
            ),
            ({"command_id": "apply"}, self.valid_headers(), 400),
            ({"command_id": "sync_codex; rm -rf /"}, self.valid_headers(), 400),
        ]
        for payload, headers, expected_status in cases:
            with self.subTest(payload=payload, headers=headers):
                status, _response_headers, response_body = self.request(
                    "POST",
                    "/__memory_atlas_command",
                    body=json.dumps(payload).encode(),
                    headers=headers,
                )
                self.assertEqual(status, expected_status)
                result = json.loads(response_body)
                self.assertRegex(result["message_zh"], r"[\u4e00-\u9fff]")
        self.assertEqual(self.bridge.calls, [])

    def test_host_and_origin_must_match_exactly_for_mutating_endpoints(self) -> None:
        cases = [
            ("/__memory_atlas_command", {"command_id": "sync_codex"}),
            ("/__memory_atlas_owner_daily", {"action": "run"}),
            (
                "/__memory_atlas_proposal_action",
                {
                    "action": "approve_apply",
                    "proposal_id": "proposal_fixture",
                    "review_token": "fixture-token",
                    "confirmation": "授权应用 proposal_fixture",
                },
            ),
        ]
        for path, payload in cases:
            with self.subTest(path=path):
                status, _headers, response_body = self.request(
                    "POST",
                    path,
                    body=json.dumps(payload, ensure_ascii=False).encode(),
                    headers={
                        "Content-Type": "application/json",
                        "Host": f"127.0.0.1:{self.port}",
                        "Origin": f"http://localhost:{self.port}",
                    },
                )
                self.assertEqual(status, 403)
                self.assertRegex(json.loads(response_body)["message_zh"], r"[\u4e00-\u9fff]")
        self.assertEqual(self.bridge.calls, [])
        self.assertEqual(self.bridge.owner_daily_calls, [])
        self.assertEqual(self.bridge.proposal_calls, [])

    def test_bad_content_type_and_oversized_body_fail_closed(self) -> None:
        body = json.dumps({"command_id": "sync_codex"}).encode()
        status, _headers, _response = self.request(
            "POST",
            "/__memory_atlas_command",
            body=body,
            headers={"Content-Type": "text/plain", "Origin": f"http://127.0.0.1:{self.port}"},
        )
        self.assertEqual(status, 415)

        oversized = b"{" + b" " * 4096 + b"}"
        status, _headers, _response = self.request(
            "POST",
            "/__memory_atlas_command",
            body=oversized,
            headers=self.valid_headers(),
        )
        self.assertEqual(status, 413)
        self.assertEqual(self.bridge.calls, [])

    def test_bad_host_fails_closed(self) -> None:
        headers = self.valid_headers()
        headers["Host"] = "evil.example"
        status, _response_headers, response_body = self.request(
            "POST",
            "/__memory_atlas_command",
            body=json.dumps({"command_id": "sync_codex"}).encode(),
            headers=headers,
        )
        self.assertEqual(status, 403)
        self.assertRegex(json.loads(response_body)["message_zh"], r"[\u4e00-\u9fff]")
        self.assertEqual(self.bridge.calls, [])

    def test_remote_origin_cannot_heartbeat_or_release_local_server(self) -> None:
        for path in ("/__memory_atlas_heartbeat", "/__memory_atlas_release"):
            with self.subTest(path=path):
                status, _headers, response_body = self.request(
                    "POST",
                    path,
                    body=b"",
                    headers={"Origin": "https://evil.example"},
                )
                self.assertEqual(status, 403)
                self.assertRegex(json.loads(response_body)["message_zh"], r"[\u4e00-\u9fff]")
        status, _headers, _body = self.request("GET", "/__memory_atlas_runtime_state")
        self.assertEqual(status, 200, "remote release probe must not stop the local server")

    def test_same_origin_heartbeat_remains_available(self) -> None:
        status, _headers, response_body = self.request(
            "POST",
            "/__memory_atlas_heartbeat",
            body=b"",
            headers={"Origin": f"http://127.0.0.1:{self.port}"},
        )
        self.assertEqual(status, 204)
        self.assertEqual(response_body, b"")


class MemoryAtlasCommandValidatorContractTests(unittest.TestCase):
    def test_validator_builds_current_frontend_before_copying_dist(self) -> None:
        source = COMMAND_VALIDATOR_PATH.read_text(encoding="utf-8")
        self.assertIn('spawnSync("npm", ["run", "build"]', source)
        self.assertIn("runFrontendBuild();", source)
        self.assertLess(source.index("runFrontendBuild();"), source.index("const fixture = prepareFixture();"))


class MemoryAtlasWeeklyReportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.weekly_module = load_module("memory_atlas_weekly_report_test", WEEKLY_REPORT_PATH)

    def test_builds_deterministic_report_from_redacted_snapshot_only(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database_dir = Path(temp_dir) / "source"
            snapshot = database_dir / "data/derived/visualization/memory_atlas.json"
            snapshot.parent.mkdir(parents=True)
            snapshot.write_text(
                json.dumps(
                    {
                        "overview": {"generated_at": "2026-07-10T08:00:00Z"},
                        "nodes": [
                            {
                                "id": "memory:decision",
                                "kind": "memory",
                                "date": "2026-07-10",
                                "category": "decision",
                                "importance": "高",
                                "label": "发布决策",
                                "statement": "先完成真实浏览器验收，再发布。",
                            },
                            {
                                "id": "memory:proposal",
                                "kind": "memory",
                                "date": "2026-07-09",
                                "category": "pending_proposal",
                                "importance": "中",
                                "label": "待授权提案",
                                "statement": "等待人工授权。",
                            },
                            {
                                "id": "memory:old",
                                "kind": "memory",
                                "date": "2026-06-01",
                                "category": "note",
                                "importance": "低",
                                "label": "旧资料",
                                "statement": "不应进入本周重点。",
                            },
                        ],
                        "agent_recommendations": [
                            {"title": "验证入口", "reason": "避免只验证字符串。"}
                        ],
                        "source_contract": {"raw_private_data_included": False},
                    },
                    ensure_ascii=False,
                )
                + "\n",
                encoding="utf-8",
            )
            result = self.weekly_module.build_weekly_report(database_dir)
            self.assertEqual(result["status"], "PASS")
            self.assertFalse(result["raw_mutation"])
            output = database_dir / result["output"]
            self.assertTrue(output.exists())
            text = output.read_text(encoding="utf-8")
            self.assertIn("Memory Atlas 本周报告", text)
            self.assertIn("先完成真实浏览器验收，再发布。", text)
            self.assertIn("等待人工授权。", text)
            self.assertNotIn("不应进入本周重点。", text)
            self.assertIn("仅使用脱敏派生快照", text)


if __name__ == "__main__":
    unittest.main()
