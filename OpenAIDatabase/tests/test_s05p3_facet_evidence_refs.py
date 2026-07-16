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


def run_json(command: list[str], cwd: Path = REPO_ROOT) -> dict:
    result = subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False)
    if result.returncode != 0:
        raise AssertionError(f"command failed: {command}\nstdout={result.stdout}\nstderr={result.stderr}")
    start = result.stdout.find("{")
    if start < 0:
        raise AssertionError(f"command did not emit JSON: {command}\nstdout={result.stdout}\nstderr={result.stderr}")
    return json.loads(result.stdout[start:])


class S05P3FacetEvidenceRefsTest(unittest.TestCase):
    def test_manifest_events_have_lightweight_evidence_refs(self) -> None:
        module = load_facet_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_jsonl(
                root / "data/processed/conversations/conversation_manifest.jsonl",
                [
                    {
                        "conversation_id": "conv_001",
                        "title": "Memory Atlas evidence refs",
                        "updated_at": "2026-07-08T00:02:00Z",
                        "message_count": 3,
                        "user_message_count": 1,
                    }
                ],
            )
            result = module.extract_facets(root, dry_run=True, generated_at="2026-07-08T00:00:00Z")
            self.assertEqual(result["task_id"], "MA-V12-S05P3")
            self.assertEqual(result["acceptance_id"], "ACC-MA-V12-S05P3")
            self.assertEqual(result["evidence_ref_count"], 2)
            event = result["events"][0]
            self.assertEqual(event["source_id"], "chatgpt")
            self.assertEqual(event["manifest_ref"], "data/processed/conversations/conversation_manifest.jsonl")
            self.assertEqual(event["evidence_missing_reason"], "processed_manifest_without_public_raw_ref")
            self.assertEqual({ref["ref_type"] for ref in event["evidence_refs"]}, {"manifest", "missing_reason"})
            self.assertTrue(all(ref["source_id"] == event["source_id"] for ref in event["evidence_refs"]))
            self.assertTrue(all(ref["record_id"] == event["record_id"] for ref in event["evidence_refs"]))

    def test_public_raw_event_has_raw_evidence_ref_without_missing_reason(self) -> None:
        module = load_facet_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_json(
                root / "data/public_raw/agents/research-agent/evt_001.json",
                {
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
            event = result["events"][0]
            self.assertEqual(event["source"], "future_agent")
            self.assertEqual(event["raw_ref"], "data/public_raw/agents/research-agent/evt_001.json")
            self.assertNotIn("evidence_missing_reason", event)
            self.assertEqual(len(event["evidence_refs"]), 1)
            self.assertEqual(event["evidence_refs"][0]["ref_type"], "raw")
            self.assertEqual(event["evidence_refs"][0]["evidence_level"], "raw")

    def test_atlasctl_apply_writes_s05p3_evidence_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_jsonl(
                root / "data/processed/codex/codex_session_manifest.jsonl",
                [
                    {
                        "session_id": "session_001",
                        "thread_name": "实现 Memory Atlas evidence refs",
                        "updated_at": "2026-07-08T00:05:00Z",
                        "message_count": 8,
                        "user_message_count": 2,
                    }
                ],
            )
            applied = run_json([
                sys.executable,
                str(ATLASCTL_SCRIPT),
                "analyze",
                "--stage",
                "facets",
                "--database-dir",
                str(root),
                "--apply",
            ])
            events_path = root / "data/derived/behavior_intelligence/events.json"
            self.assertEqual(applied["status"], "phase_s05_p3_evidence_refs_completed_pending_s05_review")
            self.assertEqual(applied["evidence_contract"]["phase"], "S05 P3")
            self.assertEqual(applied["evidence_ref_count"], 2)
            written = json.loads(events_path.read_text(encoding="utf-8"))
            self.assertEqual(written["task_id"], "MA-V12-S05P3")
            self.assertEqual(written["phase_boundary"]["next_phase"], "S05 Review")


if __name__ == "__main__":
    unittest.main()
