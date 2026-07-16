from __future__ import annotations

import importlib.util
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from OpenAIDatabase.tests.test_s07p1_economic_proxy import ATLASCTL_SCRIPT, REPO_ROOT, SCRIPTS_ROOT, run_json
from OpenAIDatabase.tests.test_s07p3_formula_what_if import write_formula_what_if_fixtures


AGENT_COLLABORATION_SCRIPT = REPO_ROOT / "scripts" / "build_memory_atlas_agent_collaboration.py"
METRICS_CONFIG = REPO_ROOT / "机器治理" / "行为智能模型" / "agent_collaboration_metrics.v1_2_s08_p1.json"


def load_agent_collaboration_module():
    sys.path.insert(0, str(SCRIPTS_ROOT))
    spec = importlib.util.spec_from_file_location("build_memory_atlas_agent_collaboration", AGENT_COLLABORATION_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def write_agent_collaboration_fixtures(root: Path) -> None:
    write_formula_what_if_fixtures(root)
    target = root / "机器治理" / "行为智能模型" / "agent_collaboration_metrics.v1_2_s08_p1.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(METRICS_CONFIG, target)


class S08P1AgentCollaborationTest(unittest.TestCase):
    def test_builds_agent_collaboration_report_with_evidence_and_chinese_summary(self) -> None:
        module = load_agent_collaboration_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_agent_collaboration_fixtures(root)
            output = root / "data/derived/agent_collaboration/agent_collaboration_quality_report.json"
            result = module.build_agent_collaboration_report(root, dry_run=True, generated_at="2026-07-08T00:00:00Z")
            self.assertEqual(result["task_id"], "MA-V12-S08P1")
            self.assertEqual(result["acceptance_id"], "ACC-MA-V12-S08P1")
            self.assertEqual(result["status"], "phase_s08_p1_collaboration_metrics_completed_pending_s08_p2")
            self.assertFalse(output.exists())
            self.assertTrue(result["phase_boundary"]["does_not_create_multi_agent_system"])
            self.assertTrue(result["phase_boundary"]["does_not_implement_complex_delegation_contract_ui"])
            self.assertTrue(result["phase_boundary"]["does_not_define_authorization_apply_boundary"])
            self.assertTrue(result["phase_boundary"]["does_not_generate_stage_flight_recorder"])
            self.assertTrue(result["phase_boundary"]["does_not_modify_raw"])
            metric_keys = {item["metric_key"] for item in result["overall_metrics"]}
            self.assertEqual(metric_keys, {
                "planning_clarity",
                "execution_clarity",
                "review_burden",
                "rework_count",
                "scope_clarity",
                "testability",
                "rollbackability",
            })
            for metric in result["overall_metrics"]:
                self.assertTrue(metric["formula_id"])
                self.assertTrue(metric["formula_source"].endswith("agent_collaboration_metrics.v1_2_s08_p1.json"))
                self.assertTrue(metric["explanation_zh"])
                self.assertTrue(metric["evidence_refs"])
                self.assertGreaterEqual(metric["score"], 0)
                self.assertLessEqual(metric["score"], 100)
            source_types = {item["source_type"] for item in result["source_summaries"]}
            self.assertTrue({"chatgpt", "codex", "other_agent"}.issubset(source_types))
            self.assertIn("人负责", result["chinese_summary"]["human_responsibility_zh"])
            self.assertIn("Agent 负责", result["chinese_summary"]["agent_responsibility_zh"])

    def test_atlasctl_agent_collaboration_apply_and_audit(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_agent_collaboration_fixtures(root)
            output = root / "data/derived/agent_collaboration/agent_collaboration_quality_report.json"
            dry_run = run_json([
                sys.executable,
                str(ATLASCTL_SCRIPT),
                "analyze",
                "--stage",
                "agent-collaboration",
                "--database-dir",
                str(root),
                "--dry-run",
            ])
            self.assertTrue(dry_run["dry_run"])
            self.assertFalse(dry_run["writes_files"])
            self.assertFalse(output.exists())

            applied = run_json([
                sys.executable,
                str(ATLASCTL_SCRIPT),
                "analyze",
                "--stage",
                "agent-collaboration",
                "--database-dir",
                str(root),
                "--apply",
            ])
            self.assertEqual(applied["task_id"], "MA-V12-S08P1")
            self.assertTrue(output.exists())

            audit = run_json([
                sys.executable,
                str(ATLASCTL_SCRIPT),
                "audit",
                "--check",
                "agent-collaboration",
                "--database-dir",
                str(root),
            ])
            self.assertEqual(audit["status"], "PASS")
            self.assertEqual(audit["bad_items"], [])
            self.assertEqual(audit["metric_count"], 7)
            self.assertGreaterEqual(audit["source_summary_count"], 3)
            self.assertFalse(audit["complex_delegation_contract_ui"])
            self.assertFalse(audit["multi_agent_system_implementation"])
            self.assertFalse(audit["raw_mutation"])


if __name__ == "__main__":
    unittest.main()
