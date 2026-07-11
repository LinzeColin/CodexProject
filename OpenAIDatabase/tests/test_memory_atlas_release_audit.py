import importlib.util
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/audit_memory_atlas_release.py"


def load_module():
    spec = importlib.util.spec_from_file_location("audit_memory_atlas_release", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def valid_atlas() -> dict:
    return {
        "schema_version": "memory_atlas.v1",
        "source_contract": {
            "mode": "public_redacted_read_only_visualization",
            "writeback_policy": {
                "frontend_can_request_writeback": True,
                "writeback_must_use_proposals": True,
                "direct_frontend_mutation_of_active_memory": False,
            },
        },
        "nodes": [],
        "edges": [],
        "timeline": [],
        "contribution": {"daily": []},
        "metrics": [],
    }


class MemoryAtlasReleaseAuditTests(unittest.TestCase):
    def test_release_audit_accepts_only_ledgered_sanitized_public_raw_sessions(self) -> None:
        module = load_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir) / "database"
            publish_dir = repo_root / "dist"
            raw_file = repo_root / "data/public_raw/codex/sessions/session-001.jsonl"
            ledger_dir = repo_root / "机器治理/证据与日志/raw_archive_manifests"
            publish_dir.mkdir(parents=True)
            raw_file.parent.mkdir(parents=True)
            ledger_dir.mkdir(parents=True)

            raw_payload = json.dumps({"text": "sanitized transcript"}, sort_keys=True) + "\n"
            raw_file.write_text(raw_payload, encoding="utf-8")
            ledger_row = {
                "source_id": "codex",
                "relative_path": "codex/sessions/session-001.jsonl",
                "sha256": hashlib.sha256(raw_payload.encode("utf-8")).hexdigest(),
                "imported_at": "2026-07-11T00:00:00Z",
                "size_bytes": len(raw_payload.encode("utf-8")),
            }
            ledger_payload = json.dumps(ledger_row, sort_keys=True) + "\n"
            (ledger_dir / "raw_hash_ledger.jsonl").write_text(ledger_payload, encoding="utf-8")
            (ledger_dir / "raw_manifest.release-test.jsonl").write_text(
                ledger_payload,
                encoding="utf-8",
            )

            (publish_dir / "index.html").write_text("<!doctype html>", encoding="utf-8")
            (publish_dir / "memory_atlas.json").write_text(
                json.dumps(valid_atlas()),
                encoding="utf-8",
            )
            subprocess.run(["git", "init", "--quiet"], cwd=repo_root, check=True)
            subprocess.run(
                ["git", "add", "data/public_raw", "机器治理/证据与日志/raw_archive_manifests"],
                cwd=repo_root,
                check=True,
            )

            result = module.audit_release(repo_root, publish_dir)

        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["public_raw"]["content_audit"]["file_count"], 1)
        self.assertEqual(result["public_raw"]["append_only_audit"]["new_raw_file_count"], 0)

    def test_governed_public_raw_audit_fails_closed_without_ledger_and_manifest(self) -> None:
        module = load_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            raw_file = repo_root / "data/public_raw/codex/sessions/session-001.jsonl"
            raw_file.parent.mkdir(parents=True)
            raw_file.write_text('{"text":"sanitized transcript"}\n', encoding="utf-8")

            result, problems = module.audit_governed_public_raw(repo_root)

        self.assertEqual(result["status"], "FAIL")
        self.assertIn("public raw contains files missing from the hash ledger", problems)
        self.assertIn("public raw has no immutable manifest matching the hash ledger", problems)

    def test_public_raw_session_exception_does_not_allow_other_sensitive_names(self) -> None:
        module = load_module()

        self.assertIsNone(
            module.forbidden_name_pattern(
                "data/public_raw/codex/sessions/session-001.jsonl",
                allow_public_raw_sessions=True,
            )
        )
        self.assertIsNotNone(
            module.forbidden_name_pattern(
                "data/public_raw/codex/sessions/cookies.json",
                allow_public_raw_sessions=True,
            )
        )

    def test_tracked_audit_rejects_failed_zero_part_session_history_metadata(self) -> None:
        module = load_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            manifest = repo_root / "session_history/failed-run/MANIFEST.txt"
            manifest.parent.mkdir(parents=True)
            manifest.write_text(
                "part_count=0\nrisk_scan=SENSITIVE_SCAN_BLOCKED\nsource_sessions=/Users/example/.codex/sessions\n",
                encoding="utf-8",
            )
            subprocess.run(["git", "init", "--quiet"], cwd=repo_root, check=True)
            subprocess.run(["git", "add", "session_history"], cwd=repo_root, check=True)

            problems = module.audit_tracked_files(repo_root)

        self.assertTrue(
            any("failed zero-part session history metadata" in problem for problem in problems),
            problems,
        )

    def test_release_audit_passes_for_static_redacted_output(self) -> None:
        module = load_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir) / "database"
            publish_dir = repo_root / "dist"
            publish_dir.mkdir(parents=True)
            (publish_dir / "index.html").write_text("<!doctype html><div id='root'></div>", encoding="utf-8")
            (publish_dir / "assets").mkdir()
            (publish_dir / "assets/app.js").write_text("console.log('memory atlas')", encoding="utf-8")
            (publish_dir / "memory_atlas.json").write_text(json.dumps(valid_atlas()), encoding="utf-8")
            subprocess.run(["git", "init", "--quiet"], cwd=repo_root, check=True)

            result = module.audit_release(repo_root, publish_dir)

        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["file_count"], 3)

    def test_release_audit_rejects_raw_or_sensitive_output(self) -> None:
        module = load_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir) / "database"
            publish_dir = repo_root / "dist"
            publish_dir.mkdir(parents=True)
            (publish_dir / "index.html").write_text("<!doctype html>", encoding="utf-8")
            (publish_dir / "memory_atlas.json").write_text(
                json.dumps({**valid_atlas(), "evidence": [{"source": "raw should not ship"}]}),
                encoding="utf-8",
            )
            (publish_dir / "OpenAI-export.zip").write_bytes(b"not really a zip")

            with self.assertRaises(module.AuditError) as raised:
                module.audit_release(repo_root, publish_dir)

        message = str(raised.exception)
        self.assertIn("forbidden publish suffix", message)
        self.assertIn("forbidden JSON key 'evidence'", message)


if __name__ == "__main__":
    unittest.main()
