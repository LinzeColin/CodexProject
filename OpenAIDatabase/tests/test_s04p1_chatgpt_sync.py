from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SYNC_SCRIPT = REPO_ROOT / "scripts" / "sync_chatgpt_memory_data.py"
ATLASCTL_SCRIPT = REPO_ROOT / "scripts" / "atlasctl.py"


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


def write_export(path: Path, title: str = "普通 ChatGPT 讨论") -> None:
    payload = [
        {
            "id": "conv_001",
            "title": title,
            "create_time": 1760000000,
            "update_time": 1760000060,
            "mapping": {
                "root": {
                    "id": "root",
                    "message": {
                        "id": "msg_user",
                        "author": {"role": "user"},
                        "create_time": 1760000001,
                        "content": {"content_type": "text", "parts": ["请总结这个项目的下一步。"]},
                    },
                },
                "reply": {
                    "id": "reply",
                    "message": {
                        "id": "msg_assistant",
                        "author": {"role": "assistant"},
                        "create_time": 1760000002,
                        "content": {"content_type": "text", "parts": ["下一步应先做只读同步 dry-run。"]},
                    },
                },
            },
        }
    ]
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


class ChatGptSyncS04P1Test(unittest.TestCase):
    def test_official_export_dry_run_counts_conversations_without_writes(self) -> None:
        self.assertTrue(SYNC_SCRIPT.exists(), "sync_chatgpt_memory_data.py should exist")
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            export_path = root / "conversations.json"
            write_export(export_path)
            result = run_json([
                sys.executable,
                str(SYNC_SCRIPT),
                "--database-dir",
                str(root),
                "--official-export",
                str(export_path),
                "--dry-run",
            ])
            self.assertEqual(result["status"], "PASS")
            self.assertEqual(result["source_id"], "chatgpt")
            self.assertEqual(result["mode"], "official_export_fallback")
            self.assertTrue(result["dry_run"])
            self.assertEqual(result["conversation_count"], 1)
            self.assertFalse((root / "data/public_raw/chatgpt/conv_001.json").exists())

    def test_official_export_zip_dry_run_counts_conversations(self) -> None:
        self.assertTrue(SYNC_SCRIPT.exists(), "sync_chatgpt_memory_data.py should exist")
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            export_json = root / "conversations.json"
            export_zip = root / "chatgpt_export.zip"
            write_export(export_json)
            with zipfile.ZipFile(export_zip, "w") as archive:
                archive.write(export_json, "export/conversations.json")
            result = run_json([
                sys.executable,
                str(SYNC_SCRIPT),
                "--database-dir",
                str(root),
                "--official-export",
                str(export_zip),
                "--dry-run",
            ])
            self.assertEqual(result["status"], "PASS")
            self.assertEqual(result["conversation_count"], 1)
            self.assertFalse((root / "data/public_raw/chatgpt/conv_001.json").exists())

    def test_official_export_apply_writes_public_raw_summary_and_run_log(self) -> None:
        self.assertTrue(SYNC_SCRIPT.exists(), "sync_chatgpt_memory_data.py should exist")
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            export_path = root / "conversations.json"
            write_export(export_path)
            result = run_json([
                sys.executable,
                str(SYNC_SCRIPT),
                "--database-dir",
                str(root),
                "--official-export",
                str(export_path),
            ])
            self.assertEqual(result["status"], "PASS")
            raw_path = root / result["raw_paths"][0]
            self.assertTrue(raw_path.exists())
            self.assertRegex(raw_path.name, r"^conv_001\.[0-9a-f]{12}\.json$")
            raw = json.loads(raw_path.read_text(encoding="utf-8"))
            self.assertEqual(raw["source_id"], "chatgpt")
            self.assertEqual(raw["conversation_id"], "conv_001")
            self.assertEqual(len(raw["messages"]), 2)
            self.assertTrue((root / "data/derived/chatgpt/chatgpt_sync_summary.json").exists())
            self.assertTrue(any((root / "data/run_logs/sync_runs").glob("*.jsonl")))

    def test_credential_content_fails_before_public_raw_write(self) -> None:
        self.assertTrue(SYNC_SCRIPT.exists(), "sync_chatgpt_memory_data.py should exist")
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            export_path = root / "conversations.json"
            secret_title = "api_" + "key=" + "sk-" + "ABCDEFGHIJKLMNOP"
            write_export(export_path, title=secret_title)
            result = run_json([
                sys.executable,
                str(SYNC_SCRIPT),
                "--database-dir",
                str(root),
                "--official-export",
                str(export_path),
            ], expect_success=False)
            self.assertEqual(result["status"], "FAIL")
            self.assertEqual(result["reason"], "credential_is_not_memory")
            self.assertFalse((root / "data/public_raw/chatgpt/conv_001.json").exists())

    def test_browser_password_or_verification_state_fails_closed(self) -> None:
        self.assertTrue(SYNC_SCRIPT.exists(), "sync_chatgpt_memory_data.py should exist")
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_json([
                sys.executable,
                str(SYNC_SCRIPT),
                "--database-dir",
                tmpdir,
                "--browser-state",
                "verification_required",
                "--dry-run",
            ], expect_success=False)
            self.assertEqual(result["status"], "STOPPED")
            self.assertEqual(result["reason"], "browser_requires_human_authentication")
            self.assertTrue(result["no_browser_mutation"])

    def test_atlasctl_chatgpt_dry_run_contract_is_available(self) -> None:
        self.assertTrue(ATLASCTL_SCRIPT.exists(), "atlasctl.py should exist")
        result = run_json([
            sys.executable,
            str(ATLASCTL_SCRIPT),
            "sync",
            "--source",
            "chatgpt",
            "--dry-run",
        ])
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["source_id"], "chatgpt")
        self.assertTrue(result["dry_run"])
        self.assertEqual(result["browser_connector"], "readonly_contract")
        self.assertEqual(result["fallback"], "official_export")


if __name__ == "__main__":
    unittest.main()
