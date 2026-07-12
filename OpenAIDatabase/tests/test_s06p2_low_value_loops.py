from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
LOOP_SCRIPT = REPO_ROOT / "scripts" / "build_memory_atlas_low_value_loops.py"
ATLASCTL_SCRIPT = REPO_ROOT / "scripts" / "atlasctl.py"
SCRIPTS_ROOT = REPO_ROOT / "scripts"


def load_loop_module():
    sys.path.insert(0, str(SCRIPTS_ROOT))
    spec = importlib.util.spec_from_file_location("build_memory_atlas_low_value_loops", LOOP_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


def evidence_ref(record_id: str) -> dict:
    return {
        "evidence_level": "processed_manifest",
        "path": "data/processed/test/manifest.jsonl",
        "record_id": record_id,
        "ref_id": f"ref_{record_id}",
        "ref_type": "manifest",
        "source_id": "chatgpt",
    }


def event(event_id: str, source: str, topic: str, occurred_at: str, task_type: str, output_type: str = "unknown") -> dict:
    return {
        "event_id": event_id,
        "source": source,
        "source_id": source,
        "topic": topic,
        "occurred_at": occurred_at,
        "project": None,
        "task_type": task_type,
        "language": "zh",
        "intent": "plan",
        "output_type": output_type,
        "tool": source,
        "turn_count": 3,
        "friction": [],
        "value_signal": [],
        "future_agent_source": None,
        "record_id": f"record_{event_id}",
        "evidence_refs": [evidence_ref(f"record_{event_id}")],
        "manifest_ref": "data/processed/test/manifest.jsonl",
    }


def cluster(cluster_id: str, label: str, event_ids: list[str], event_count: int, months: list[str], tasks: list[str], sources: list[str]) -> dict:
    return {
        "cluster_id": cluster_id,
        "cluster_type": "topic",
        "level": 1,
        "label_zh": label,
        "summary_zh": f"该行为簇基于 {event_count} 条事件，围绕「{label}」反复出现。",
        "event_count": event_count,
        "representative_event_ids": event_ids,
        "evidence_refs": [evidence_ref(cluster_id)],
        "filter_dimensions": {
            "source": sources,
            "time": {"start": "2026-01-01T00:00:00Z", "end": "2026-04-20T00:00:00Z", "months": months},
            "project": ["未标注"],
            "task": tasks,
            "language": ["zh"],
        },
    }


def write_loop_fixtures(root: Path) -> None:
    events = [
        event("evt_rework_1", "codex", "Memory Atlas 反复重做", "2026-01-01T00:00:00Z", "engineering", "code"),
        event("evt_rework_2", "codex", "Memory Atlas 反复重做", "2026-02-01T00:00:00Z", "engineering", "test"),
        event("evt_rework_3", "codex", "Memory Atlas 反复重做", "2026-03-01T00:00:00Z", "design", "code"),
        event("evt_discuss_1", "chatgpt", "经营管理反复讨论", "2026-01-05T00:00:00Z", "unknown"),
        event("evt_discuss_2", "chatgpt", "经营管理反复讨论", "2026-02-05T00:00:00Z", "unknown"),
        event("evt_discuss_3", "chatgpt", "经营管理反复讨论", "2026-03-05T00:00:00Z", "unknown"),
        event("evt_opt_1", "codex", "界面细节过度优化", "2026-01-10T00:00:00Z", "design", "ui"),
        event("evt_opt_2", "codex", "界面细节过度优化", "2026-01-12T00:00:00Z", "design", "ui"),
        event("evt_opt_3", "codex", "界面细节过度优化", "2026-01-14T00:00:00Z", "design", "ui"),
        event("evt_scope_1", "chatgpt", "范围扩张", "2026-01-20T00:00:00Z", "design"),
        event("evt_scope_2", "codex", "范围扩张", "2026-02-20T00:00:00Z", "engineering", "code"),
        event("evt_scope_3", "chatgpt", "范围扩张", "2026-03-20T00:00:00Z", "automation"),
    ]
    write_json(
        root / "data/derived/behavior_intelligence/events.json",
        {
            "schema_version": "memory_atlas_behavior_events.v1",
            "task_id": "MA-V12-S05P3",
            "acceptance_id": "ACC-MA-V12-S05P3",
            "event_count": len(events),
            "events": events,
        },
    )
    topic_clusters = [
        cluster("topic_rework", "Memory Atlas 重复返工", ["evt_rework_1", "evt_rework_2", "evt_rework_3"], 6, ["2026-01", "2026-02", "2026-03"], ["engineering", "design"], ["codex"]),
        cluster("topic_discuss", "反复讨论未落地", ["evt_discuss_1", "evt_discuss_2", "evt_discuss_3"], 5, ["2026-01", "2026-02", "2026-03"], ["未标注"], ["chatgpt"]),
        cluster("topic_opt", "过度优化", ["evt_opt_1", "evt_opt_2", "evt_opt_3"], 4, ["2026-01"], ["design"], ["codex"]),
        cluster("topic_scope", "scope creep", ["evt_scope_1", "evt_scope_2", "evt_scope_3"], 4, ["2026-01", "2026-02", "2026-03"], ["design", "engineering", "automation"], ["chatgpt", "codex"]),
    ]
    write_json(
        root / "data/derived/behavior_intelligence/clusters.json",
        {
            "schema_version": "memory_atlas_behavior_clusters.v1",
            "task_id": "MA-V12-S06P1",
            "acceptance_id": "ACC-MA-V12-S06P1",
            "status": "phase_s06_p1_cluster_builder_completed_pending_s06_p2",
            "cluster_count": len(topic_clusters),
            "topic_cluster_count": len(topic_clusters),
            "hierarchy_cluster_count": 0,
            "topic_clusters": topic_clusters,
            "hierarchy_clusters": [],
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


class S06P2LowValueLoopsTest(unittest.TestCase):
    def test_builds_low_value_loops_debt_ledger_and_half_life(self) -> None:
        module = load_loop_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_loop_fixtures(root)
            result = module.build_low_value_loops(root, dry_run=True, generated_at="2026-07-08T00:00:00Z")
            self.assertEqual(result["task_id"], "MA-V12-S06P2")
            self.assertEqual(result["acceptance_id"], "ACC-MA-V12-S06P2")
            self.assertGreaterEqual(result["loop_cluster_count"], 4)
            self.assertGreaterEqual(result["decision_debt_count"], 1)
            self.assertGreaterEqual(result["action_half_life_count"], 1)
            self.assertFalse((root / "data/derived/behavior_intelligence/low_value_loops.json").exists())
            loop_types = {loop["loop_type"] for loop in result["loop_clusters"]}
            self.assertIn("repeated_rework", loop_types)
            self.assertIn("discussion_without_landing", loop_types)
            self.assertIn("over_optimization", loop_types)
            self.assertIn("scope_creep", loop_types)
            for loop in result["loop_clusters"]:
                self.assertTrue(loop["evidence_refs"])
                self.assertIn("候选", loop["summary_zh"])
                self.assertNotIn("心理诊断", loop["summary_zh"])
                self.assertIn(loop["loop_id"], {debt["loop_id"] for debt in result["decision_debt_ledger"]})
            for item in result["action_half_life"]:
                self.assertGreater(item["action_half_life_days"], 0)
                self.assertTrue(item["evidence_refs"])

    def test_atlasctl_low_value_loops_dry_run_apply_and_audit(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_loop_fixtures(root)
            dry_run = run_json([
                sys.executable,
                str(ATLASCTL_SCRIPT),
                "analyze",
                "--stage",
                "low-value-loops",
                "--database-dir",
                str(root),
                "--dry-run",
            ])
            self.assertTrue(dry_run["dry_run"])
            self.assertFalse(dry_run["writes_files"])
            self.assertFalse((root / "data/derived/behavior_intelligence/low_value_loops.json").exists())

            applied = run_json([
                sys.executable,
                str(ATLASCTL_SCRIPT),
                "analyze",
                "--stage",
                "low-value-loops",
                "--database-dir",
                str(root),
            ])
            loops_path = root / "data/derived/behavior_intelligence/low_value_loops.json"
            self.assertEqual(applied["task_id"], "MA-V12-S06P2")
            self.assertTrue(loops_path.exists())
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
            self.assertEqual(audit["bad_items"], [])


if __name__ == "__main__":
    unittest.main()
