from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CODEX_SYNC_SCRIPT = REPO_ROOT / "scripts" / "sync_codex_memory_data.py"
FUTURE_AGENT_SCRIPT = REPO_ROOT / "scripts" / "sync_future_agent_data.py"
ATLASCTL_SCRIPT = REPO_ROOT / "scripts" / "atlasctl.py"
SCRIPTS_ROOT = REPO_ROOT / "scripts"


def load_codex_module():
    sys.path.insert(0, str(SCRIPTS_ROOT))
    spec = importlib.util.spec_from_file_location("sync_codex_memory_data", CODEX_SYNC_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def write_codex_session(codex_home: Path) -> None:
    session_id = "01999999-aaaa-bbbb-cccc-444444444444"
    write_jsonl(codex_home / "session_index.jsonl", [{"id": session_id, "thread_name": "S04 P2 Codex sync"}])
    write_jsonl(
        codex_home / "sessions/2026/07/08/session.jsonl",
        [
            {
                "type": "session_meta",
                "timestamp": "2026-07-08T00:00:00Z",
                "payload": {"id": session_id, "cwd": "/Users/example/project", "originator": "codex_cli"},
            },
            {
                "type": "response_item",
                "timestamp": "2026-07-08T00:01:00Z",
                "payload": {
                    "type": "message",
                    "role": "user",
                    "content": [{"text": "请把 Memory Atlas 的 Codex local sync 做成可验证入口。"}],
                },
            },
        ],
    )


def run_json(command: list[str], cwd: Path = REPO_ROOT, expect_success: bool = True) -> dict:
    result = subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False)
    if expect_success and result.returncode != 0:
        raise AssertionError(f"command failed: {command}\nstdout={result.stdout}\nstderr={result.stderr}")
    if not expect_success and result.returncode == 0:
        raise AssertionError(f"command unexpectedly passed: {command}\nstdout={result.stdout}")
    start = result.stdout.find("{")
    if start < 0:
        raise AssertionError(f"command did not emit JSON: {command}\nstdout={result.stdout}\nstderr={result.stderr}")
    return json.loads(result.stdout[start:])


class S04P2CodexAgentSyncTest(unittest.TestCase):
    def test_codex_sync_dry_run_reports_raw_derived_run_log_without_writes(self) -> None:
        module = load_codex_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            db = root / "db"
            codex_home = root / ".codex"
            write_codex_session(codex_home)
            result = module.sync_codex_data(
                db,
                codex_home,
                build_atlas=False,
                commit=False,
                push=False,
                dry_run=True,
            )
            self.assertEqual(result["status"], "PASS")
            self.assertEqual(result["source_id"], "codex")
            self.assertTrue(result["dry_run"])
            self.assertFalse(result["writes_files"])
            self.assertEqual(result["raw_root"], "data/public_raw/codex")
            self.assertIn("public_raw_snapshot", result["outputs"])
            self.assertIn("sync_log", result["outputs"])
            self.assertFalse((db / "data/public_raw/codex").exists())
            self.assertFalse((db / "data/processed/codex").exists())

    def test_codex_sync_apply_writes_public_raw_derived_and_run_log(self) -> None:
        module = load_codex_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            db = root / "db"
            codex_home = root / ".codex"
            write_codex_session(codex_home)
            result = module.sync_codex_data(
                db,
                codex_home,
                build_atlas=False,
                commit=False,
                push=False,
                force_full_scan=True,
            )
            raw_path = db / result["outputs"]["public_raw_snapshot"]
            self.assertEqual(result["status"], "PASS")
            self.assertEqual(result["source_id"], "codex")
            self.assertFalse(result["dry_run"])
            self.assertTrue(raw_path.exists())
            public_raw = json.loads(raw_path.read_text(encoding="utf-8"))
            self.assertEqual(public_raw["source_id"], "codex")
            self.assertEqual(public_raw["session_count"], 1)
            self.assertTrue((db / "data/derived/codex/codex_activity_snapshot.json").exists())
            self.assertTrue(any((db / "data/run_logs/sync_runs").glob("*.jsonl")))

    def test_future_agent_adapter_apply_writes_raw_derived_and_run_log(self) -> None:
        self.assertTrue(FUTURE_AGENT_SCRIPT.exists(), "sync_future_agent_data.py should exist")
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            export_path = root / "future_agent_events.json"
            export_path.write_text(
                json.dumps(
                    [
                        {
                            "event_id": "evt_001",
                            "title": "后续 agent 公开事件",
                            "messages": [{"role": "assistant", "text": "这是一个公开的后续 agent 同步样本。"}],
                        }
                    ],
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            result = run_json([
                sys.executable,
                str(FUTURE_AGENT_SCRIPT),
                "--database-dir",
                str(root),
                "--agent-id",
                "research-agent",
                "--input",
                str(export_path),
            ])
            self.assertEqual(result["status"], "PASS")
            self.assertEqual(result["source_id"], "future-agent")
            raw_path = root / result["raw_paths"][0]
            self.assertTrue(raw_path.exists())
            self.assertTrue((root / "data/derived/agents/research-agent/agent_sync_summary.json").exists())
            self.assertTrue(any((root / "data/run_logs/sync_runs").glob("*.jsonl")))

    def test_atlasctl_codex_and_future_agent_dry_run_contracts_are_available(self) -> None:
        for source_id in ("codex", "future-agent"):
            result = run_json([
                sys.executable,
                str(ATLASCTL_SCRIPT),
                "sync",
                "--source",
                source_id,
                "--dry-run",
            ])
            self.assertEqual(result["status"], "PASS")
            self.assertEqual(result["source_id"], source_id)
            self.assertTrue(result["dry_run"])
            self.assertFalse(result["writes_files"])
            self.assertIn("raw_root", result)
            self.assertIn("derived_summary", result)
            self.assertEqual(result["run_log_dir"], "data/run_logs/sync_runs")


if __name__ == "__main__":
    unittest.main()
