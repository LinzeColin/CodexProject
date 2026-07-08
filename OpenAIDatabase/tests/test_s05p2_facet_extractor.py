from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
FACET_SCRIPT = REPO_ROOT / "scripts" / "extract_memory_atlas_facets.py"
ATLASCTL_SCRIPT = REPO_ROOT / "scripts" / "atlasctl.py"
SCRIPTS_ROOT = REPO_ROOT / "scripts"


def load_facet_module():
    sys.path.insert(0, str(SCRIPTS_ROOT))
    spec = importlib.util.spec_from_file_location("extract_memory_atlas_facets", FACET_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def write_processed_fixtures(root: Path) -> None:
    write_jsonl(
        root / "data/processed/conversations/conversation_manifest.jsonl",
        [
            {
                "conversation_id": "conv_001",
                "title": "Memory Atlas 验收计划",
                "created_at": "2026-07-08T00:00:00Z",
                "updated_at": "2026-07-08T00:02:00Z",
                "message_count": 3,
                "user_message_count": 1,
                "source_path": "OpenAI-export.zip!conversations.json",
            }
        ],
    )
    write_jsonl(
        root / "data/processed/codex/codex_session_manifest.jsonl",
        [
            {
                "session_id": "session_001",
                "thread_name": "实现 Memory Atlas facet extractor",
                "started_at": "2026-07-08T00:03:00Z",
                "updated_at": "2026-07-08T00:05:00Z",
                "message_count": 8,
                "user_message_count": 2,
                "activity_score": 120,
                "topics": [{"id": "memory_atlas", "label": "Memory Atlas / 记忆可视化"}],
                "top_tools": [{"name": "exec_command", "count": 3}],
            }
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


class S05P2FacetExtractorTest(unittest.TestCase):
    def test_missing_sources_do_not_create_fake_events(self) -> None:
        module = load_facet_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            result = module.extract_facets(root, dry_run=True, generated_at="2026-07-08T00:00:00Z")
            self.assertEqual(result["status"], "phase_s05_p3_evidence_refs_completed_pending_s05_review")
            self.assertEqual(result["event_count"], 0)
            self.assertEqual(result["events"], [])
            self.assertEqual(result["source_status"]["chatgpt"]["status"], "missing")
            self.assertEqual(result["source_status"]["codex"]["status"], "missing")
            self.assertEqual(result["source_status"]["future_agent"]["status"], "missing")
            self.assertFalse((root / "data/derived/behavior_intelligence/events.json").exists())

    def test_processed_chatgpt_and_codex_manifests_generate_evidence_gap_events(self) -> None:
        module = load_facet_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_processed_fixtures(root)
            result = module.extract_facets(root, dry_run=True, generated_at="2026-07-08T00:00:00Z")
            self.assertEqual(result["event_count"], 2)
            by_source = {event["source"]: event for event in result["events"]}
            self.assertEqual(by_source["chatgpt"]["manifest_ref"], "data/processed/conversations/conversation_manifest.jsonl")
            self.assertEqual(by_source["codex"]["manifest_ref"], "data/processed/codex/codex_session_manifest.jsonl")
            self.assertEqual(by_source["chatgpt"]["evidence_missing_reason"], "processed_manifest_without_public_raw_ref")
            self.assertEqual(by_source["codex"]["evidence_missing_reason"], "processed_manifest_without_public_raw_ref")
            self.assertEqual(by_source["chatgpt"]["future_agent_source"], None)
            self.assertIn("evidence_gap", by_source["codex"]["friction"])
            for event in result["events"]:
                for field in result["required_fields"]:
                    self.assertIn(field, event)

    def test_future_agent_raw_generates_event_with_raw_ref_and_source_descriptor(self) -> None:
        module = load_facet_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_json(
                root / "data/public_raw/agents/research-agent/evt_001.json",
                {
                    "schema_version": "memory_atlas_public_raw_future_agent.v1",
                    "source_id": "future-agent",
                    "agent_id": "research-agent",
                    "agent_name": "Research Agent",
                    "adapter_mode": "minimal_adapter",
                    "event_id": "evt_001",
                    "title": "调研 Memory Atlas 后续 agent 接入",
                    "message_count": 2,
                },
            )
            result = module.extract_facets(root, dry_run=True, generated_at="2026-07-08T00:00:00Z")
            self.assertEqual(result["event_count"], 1)
            event = result["events"][0]
            self.assertEqual(event["source"], "future_agent")
            self.assertEqual(event["raw_ref"], "data/public_raw/agents/research-agent/evt_001.json")
            self.assertEqual(event["future_agent_source"]["agent_id"], "research-agent")
            self.assertNotIn("evidence_missing_reason", event)

    def test_atlasctl_analyze_facets_dry_run_and_apply(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_processed_fixtures(root)
            dry_run = run_json([
                sys.executable,
                str(ATLASCTL_SCRIPT),
                "analyze",
                "--stage",
                "facets",
                "--database-dir",
                str(root),
                "--dry-run",
            ])
            self.assertEqual(dry_run["acceptance_id"], "ACC-MA-V12-S05P3")
            self.assertTrue(dry_run["dry_run"])
            self.assertFalse(dry_run["writes_files"])
            self.assertFalse((root / "data/derived/behavior_intelligence/events.json").exists())

            applied = run_json([
                sys.executable,
                str(ATLASCTL_SCRIPT),
                "analyze",
                "--stage",
                "facets",
                "--database-dir",
                str(root),
            ])
            events_path = root / "data/derived/behavior_intelligence/events.json"
            self.assertEqual(applied["event_count"], 2)
            self.assertTrue(events_path.exists())
            written = json.loads(events_path.read_text(encoding="utf-8"))
            self.assertEqual(written["task_id"], "MA-V12-S05P3")
            self.assertEqual(written["event_count"], 2)


if __name__ == "__main__":
    unittest.main()
