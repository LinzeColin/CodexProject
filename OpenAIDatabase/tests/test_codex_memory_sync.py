import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_ROOT = ROOT / "scripts"
SCRIPT = ROOT / "scripts/sync_codex_memory_data.py"


def load_module():
    if str(SCRIPTS_ROOT) not in sys.path:
        sys.path.insert(0, str(SCRIPTS_ROOT))
    spec = importlib.util.spec_from_file_location("sync_codex_memory_data", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def write_jsonl(path: Path, rows: list[dict]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


class CodexMemorySyncTests(unittest.TestCase):
    def test_syncs_real_codex_shape_with_redaction_and_recommendations(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            db = root / "db"
            codex_home = root / ".codex"
            session_id = "01999999-aaaa-bbbb-cccc-111111111111"
            write_jsonl(
                codex_home / "session_index.jsonl",
                [
                    {
                        "id": session_id,
                        "thread_name": "Memory Atlas 真实 Codex 数据",
                    }
                ],
            )
            write_jsonl(
                codex_home / "sessions/2026/06/17/session.jsonl",
                [
                    {
                        "type": "session_meta",
                        "timestamp": "2026-06-17T00:00:00Z",
                        "payload": {
                            "id": session_id,
                            "cwd": "/Users/linzezhang/private/project",
                            "originator": "codex_cli",
                        },
                    },
                    {
                        "type": "response_item",
                        "timestamp": "2026-06-17T00:01:00Z",
                        "payload": {
                            "type": "message",
                            "role": "user",
                            "content": [
                                {
                                    "text": "请用真实 Codex 数据，不要 mock。默认中文输出，同步到 GitHub OpenAIDatabase。secret fake-openai-key-for-redaction-test"
                                }
                            ],
                        },
                    },
                    {
                        "type": "response_item",
                        "timestamp": "2026-06-17T00:02:00Z",
                        "payload": {"type": "function_call", "name": "functions.exec_command"},
                    },
                    {
                        "type": "event_msg",
                        "timestamp": "2026-06-17T00:03:00Z",
                        "payload": {"type": "turn_aborted"},
                    },
                ],
            )

            result = module.sync_codex_data(db, codex_home, build_atlas=False, commit=False, push=False)
            self.assertEqual(result["status"], "PASS")
            self.assertEqual(result["session_count"], 1)
            self.assertEqual(result["message_count"], 1)
            self.assertEqual(result["cache"]["parsed"], 1)
            self.assertEqual(result["cache"]["cached"], 0)
            session_manifest = (db / module.SESSION_OUTPUT).read_text(encoding="utf-8")
            recommendations = json.loads((db / module.RECOMMENDATION_OUTPUT).read_text(encoding="utf-8"))
            report = (db / module.REPORT_OUTPUT).read_text(encoding="utf-8")

        self.assertNotIn("fake-openai-key-for-redaction-test", session_manifest)
        self.assertNotIn("/Users/linzezhang/private/project", session_manifest)
        self.assertIn("真实数据优先", report)
        self.assertGreaterEqual(len(recommendations["memory"]["current"]), 1)
        self.assertGreaterEqual(len(recommendations["meta_data"]["current"]), 1)

    def test_reuses_cached_session_rows_when_file_signature_is_unchanged(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            db = root / "db"
            codex_home = root / ".codex"
            session_id = "01999999-aaaa-bbbb-cccc-222222222222"
            session_path = codex_home / "sessions/2026/06/18/session.jsonl"
            write_jsonl(codex_home / "session_index.jsonl", [{"id": session_id, "thread_name": "cache test"}])
            write_jsonl(
                session_path,
                [
                    {
                        "type": "session_meta",
                        "timestamp": "2026-06-18T00:00:00Z",
                        "payload": {"id": session_id},
                    },
                    {
                        "type": "response_item",
                        "timestamp": "2026-06-18T00:01:00Z",
                        "payload": {"type": "message", "role": "user", "content": [{"text": "默认中文输出"}]},
                    },
                ],
            )

            first = module.sync_codex_data(db, codex_home, build_atlas=False, commit=False, push=False)
            self.assertEqual(first["cache"], {"cached": 0, "parsed": 1, "skipped": 0})

            original_parse = module.parse_session_file

            def guarded_parse(path, *_args, **_kwargs):
                if path == session_path:
                    raise AssertionError("unchanged session should be served from cache")
                return original_parse(path, *_args, **_kwargs)

            module.parse_session_file = guarded_parse
            second = module.sync_codex_data(db, codex_home, build_atlas=False, commit=False, push=False)

        self.assertEqual(second["status"], "PASS")
        self.assertEqual(second["cache"], {"cached": 1, "parsed": 0, "skipped": 0})

    def test_snapshot_range_starts_from_first_session_start_day(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            db = root / "db"
            codex_home = root / ".codex"
            session_id = "01999999-aaaa-bbbb-cccc-333333333333"
            write_jsonl(
                codex_home / "sessions/2026/06/02/session.jsonl",
                [
                    {
                        "type": "session_meta",
                        "timestamp": "2026-06-02T07:00:00Z",
                        "payload": {"id": session_id},
                    },
                    {
                        "type": "response_item",
                        "timestamp": "2026-06-09T07:00:00Z",
                        "payload": {"type": "message", "role": "user", "content": [{"text": "默认中文输出"}]},
                    },
                ],
            )

            result = module.sync_codex_data(db, codex_home, build_atlas=False, commit=False, push=False)
            snapshot = json.loads((db / module.SNAPSHOT_OUTPUT).read_text(encoding="utf-8"))
            rows = [json.loads(line) for line in (db / module.SESSION_OUTPUT).read_text(encoding="utf-8").splitlines()]

        self.assertEqual(result["range_start"], "2026-06-02")
        self.assertEqual(result["range_end"], "2026-06-09")
        self.assertEqual(snapshot["session_started_range_start"], "2026-06-02")
        self.assertEqual(snapshot["activity_range_start"], "2026-06-09")
        self.assertEqual(rows[0]["started_day"], "2026-06-02")
        self.assertEqual(rows[0]["updated_day"], "2026-06-09")

    def test_push_targets_github_main_from_runtime_worktree_branch(self):
        module = load_module()
        commands = []

        class DiffWithChanges:
            returncode = 1

        def fake_run_command(args, cwd):
            commands.append((args, cwd))

        original_run_command = module.run_command
        original_subprocess_run = module.subprocess.run
        try:
            module.run_command = fake_run_command
            module.subprocess.run = lambda *_args, **_kwargs: DiffWithChanges()

            with tempfile.TemporaryDirectory() as td:
                repo = Path(td)
                (repo / "data/public_raw/codex").mkdir(parents=True)
                (repo / "data/processed/codex").mkdir(parents=True)
                result = module.git_commit_and_push(repo, push=True)
        finally:
            module.run_command = original_run_command
            module.subprocess.run = original_subprocess_run

        self.assertEqual(result, {"committed": True, "pushed": True, "reason": "updated"})
        self.assertIn("data/public_raw/codex", commands[0][0])
        self.assertEqual(commands[-1][0], ["git", "push", "origin", "HEAD:main"])

    def test_git_add_skips_missing_untracked_optional_exports(self):
        module = load_module()
        commands = []

        class CleanDiff:
            returncode = 0

        class MissingPath:
            returncode = 1

        def fake_run_command(args, cwd):
            commands.append((args, cwd))

        def fake_subprocess_run(args, *_args, **_kwargs):
            if args[:3] == ["git", "ls-files", "--error-unmatch"]:
                return MissingPath()
            return CleanDiff()

        original_run_command = module.run_command
        original_subprocess_run = module.subprocess.run
        try:
            module.run_command = fake_run_command
            module.subprocess.run = fake_subprocess_run

            with tempfile.TemporaryDirectory() as td:
                repo = Path(td)
                (repo / "token_usage/current-mac-latest").mkdir(parents=True)
                result = module.git_commit_and_push(repo, push=False)
        finally:
            module.run_command = original_run_command
            module.subprocess.run = original_subprocess_run

        self.assertEqual(result, {"committed": False, "pushed": False, "reason": "no_changes"})
        self.assertEqual(commands[0][0], ["git", "add", "token_usage/current-mac-latest"])


if __name__ == "__main__":
    unittest.main()
