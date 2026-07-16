from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CLUSTER_SCRIPT = REPO_ROOT / "scripts" / "build_memory_atlas_clusters.py"
ATLASCTL_SCRIPT = REPO_ROOT / "scripts" / "atlasctl.py"
SCRIPTS_ROOT = REPO_ROOT / "scripts"


def load_cluster_module():
    sys.path.insert(0, str(SCRIPTS_ROOT))
    spec = importlib.util.spec_from_file_location("build_memory_atlas_clusters", CLUSTER_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


def evidence_ref(source: str, record_id: str) -> dict:
    return {
        "evidence_level": "processed_manifest",
        "path": f"data/processed/{source}/manifest.jsonl",
        "record_id": record_id,
        "ref_id": f"{source}_{record_id}_ref",
        "ref_type": "manifest",
        "source_id": source,
    }


def event(
    event_id: str,
    source: str,
    topic: str,
    occurred_at: str,
    project: str | None = None,
    task_type: str = "engineering",
    language: str = "zh",
) -> dict:
    record_id = f"record_{event_id}"
    return {
        "event_id": event_id,
        "source": source,
        "source_id": source,
        "topic": topic,
        "occurred_at": occurred_at,
        "project": project,
        "task_type": task_type,
        "language": language,
        "intent": "build",
        "output_type": "code",
        "tool": source,
        "turn_count": 2,
        "friction": [],
        "value_signal": ["reuse"],
        "future_agent_source": None,
        "record_id": record_id,
        "evidence_refs": [evidence_ref(source, record_id)],
        "manifest_ref": f"data/processed/{source}/manifest.jsonl",
    }


def write_events_fixture(root: Path) -> None:
    write_json(
        root / "data/derived/behavior_intelligence/events.json",
        {
            "schema_version": "memory_atlas_behavior_events.v1",
            "task_id": "MA-V12-S05P3",
            "acceptance_id": "ACC-MA-V12-S05P3",
            "event_count": 4,
            "events": [
                event("evt_001", "chatgpt", "Memory Atlas cluster builder", "2026-07-08T00:00:00Z", "Memory Atlas", "engineering", "zh"),
                event("evt_002", "codex", "Memory Atlas validator", "2026-07-08T01:00:00Z", "Memory Atlas", "engineering", "en"),
                event("evt_003", "chatgpt", "业务流程自动化", "2026-07-09T00:00:00Z", None, "automation", "zh"),
                event("evt_004", "chatgpt", "财务价值分析", "2026-07-10T00:00:00Z", "Finance", "data", "mixed"),
            ],
        },
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


class S06P1ClusterBuilderTest(unittest.TestCase):
    def test_builds_topic_and_hierarchy_clusters_with_evidence_refs(self) -> None:
        module = load_cluster_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_events_fixture(root)
            result = module.build_clusters(root, dry_run=True, generated_at="2026-07-08T00:00:00Z")
            self.assertEqual(result["task_id"], "MA-V12-S06P1")
            self.assertEqual(result["acceptance_id"], "ACC-MA-V12-S06P1")
            self.assertEqual(result["filtered_event_count"], 4)
            self.assertGreaterEqual(result["topic_cluster_count"], 3)
            self.assertGreaterEqual(result["hierarchy_cluster_count"], 3)
            self.assertFalse((root / "data/derived/behavior_intelligence/clusters.json").exists())
            self.assertEqual(result["filter_contract"]["supported_filters"], ["source", "time", "project", "task", "language"])
            for cluster in [*result["topic_clusters"], *result["hierarchy_clusters"]]:
                self.assertIn("该", cluster["summary_zh"])
                self.assertNotIn("心理诊断", cluster["summary_zh"])
                self.assertTrue(cluster["evidence_refs"])
                for field in ["source", "time", "project", "task", "language"]:
                    self.assertIn(field, cluster["filter_dimensions"])

    def test_filters_source_language_and_time(self) -> None:
        module = load_cluster_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_events_fixture(root)
            result = module.build_clusters(
                root,
                dry_run=True,
                generated_at="2026-07-08T00:00:00Z",
                active_filters={
                    "source": "codex",
                    "language": "en",
                    "time_from": "2026-07-08T00:30:00Z",
                    "time_to": "2026-07-08T02:00:00Z",
                },
            )
            self.assertEqual(result["filtered_event_count"], 1)
            self.assertEqual(result["topic_clusters"][0]["representative_event_ids"], ["evt_002"])
            self.assertEqual(result["filter_contract"]["active_filters"]["source"], "codex")
            self.assertEqual(result["filter_contract"]["active_filters"]["language"], "en")

    def test_atlasctl_clusters_dry_run_apply_and_audit(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_events_fixture(root)
            dry_run = run_json([
                sys.executable,
                str(ATLASCTL_SCRIPT),
                "analyze",
                "--stage",
                "clusters",
                "--database-dir",
                str(root),
                "--dry-run",
                "--source",
                "chatgpt",
            ])
            self.assertTrue(dry_run["dry_run"])
            self.assertFalse(dry_run["writes_files"])
            self.assertEqual(dry_run["filter_contract"]["active_filters"]["source"], "chatgpt")
            self.assertFalse((root / "data/derived/behavior_intelligence/clusters.json").exists())

            applied = run_json([
                sys.executable,
                str(ATLASCTL_SCRIPT),
                "analyze",
                "--stage",
                "clusters",
                "--database-dir",
                str(root),
                "--apply",
            ])
            clusters_path = root / "data/derived/behavior_intelligence/clusters.json"
            self.assertEqual(applied["task_id"], "MA-V12-S06P1")
            self.assertTrue(clusters_path.exists())
            audit = run_json([
                sys.executable,
                str(ATLASCTL_SCRIPT),
                "audit",
                "--check",
                "insight-evidence",
                "--database-dir",
                str(root),
            ])
            self.assertEqual(audit["status"], "PASS")
            self.assertEqual(audit["bad_clusters"], [])


if __name__ == "__main__":
    unittest.main()
