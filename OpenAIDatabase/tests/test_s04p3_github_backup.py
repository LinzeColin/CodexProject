from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
GITHUB_BACKUP_SCRIPT = REPO_ROOT / "scripts" / "github_backup.py"
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


def git(repo: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()


def create_backup_fixture(root: Path) -> None:
    files = {
        "data/public_raw/chatgpt/conversation_001.json": {"source_id": "chatgpt", "message_count": 1},
        "data/derived/visualization/memory_atlas.json": {"nodes": [], "edges": []},
        "data/derived/chat_reports/latest.json": {"status": "PASS"},
        "data/run_logs/sync_runs/2026-07-08.jsonl": '{"status":"PASS"}\n',
        "docs/reviews/sample_report.md": "# Sample report\n",
    }
    for relative_path, payload in files.items():
        path = root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(payload, str):
            path.write_text(payload, encoding="utf-8")
        else:
            path.write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


class S04P3GithubBackupTest(unittest.TestCase):
    def test_atlasctl_push_dry_run_reports_backup_contract_without_writes(self) -> None:
        result = run_json([sys.executable, str(ATLASCTL_SCRIPT), "push", "--dry-run"])
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["command"], "push")
        self.assertTrue(result["dry_run"])
        self.assertFalse(result["writes_files"])
        self.assertFalse(result["remote_push"])
        self.assertIn("data/public_raw", result["backup_targets"])
        self.assertIn("data/derived", result["backup_targets"])
        self.assertIn("data/run_logs", result["backup_targets"])
        self.assertIn("docs/reviews", result["backup_targets"])
        self.assertIn("git push origin HEAD:main", result["manual_push_command"])

    def test_backup_apply_commits_only_local_backup_scope_without_remote_push(self) -> None:
        self.assertTrue(GITHUB_BACKUP_SCRIPT.exists(), "github_backup.py should exist")
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            git(root, "init")
            git(root, "config", "user.email", "codex@example.invalid")
            git(root, "config", "user.name", "Codex Test")
            create_backup_fixture(root)

            result = run_json([
                sys.executable,
                str(GITHUB_BACKUP_SCRIPT),
                "--database-dir",
                str(root),
                "--apply",
                "--message",
                "S04 P3 test backup",
            ])

            self.assertEqual(result["status"], "PASS")
            self.assertFalse(result["dry_run"])
            self.assertTrue(result["apply"])
            self.assertTrue(result["committed"])
            self.assertFalse(result["pushed"])
            self.assertFalse(result["remote_push"])
            self.assertEqual(git(root, "log", "-1", "--pretty=%s"), "S04 P3 test backup")
            self.assertEqual(git(root, "status", "--short"), "")
            self.assertIn("data/public_raw/chatgpt/conversation_001.json", result["committed_files"])
            self.assertIn("data/derived/visualization/memory_atlas.json", result["committed_files"])
            self.assertIn("data/run_logs/sync_runs/2026-07-08.jsonl", result["committed_files"])
            self.assertIn("docs/reviews/sample_report.md", result["committed_files"])

    def test_backup_apply_fails_closed_outside_git_worktree_with_chinese_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            create_backup_fixture(root)
            result = run_json([
                sys.executable,
                str(GITHUB_BACKUP_SCRIPT),
                "--database-dir",
                str(root),
                "--apply",
            ], expect_success=False)

            self.assertEqual(result["status"], "FAIL")
            self.assertEqual(result["reason"], "not_git_worktree")
            self.assertFalse(result["writes_files"])
            self.assertFalse(result["remote_push"])
            self.assertIn("中文原因", result)
            self.assertIn("fallback建议", result)


if __name__ == "__main__":
    unittest.main()
