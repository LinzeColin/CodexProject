from __future__ import annotations

import importlib.util
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from OpenAIDatabase.tests.test_s06p3_opportunity_discovery import ATLASCTL_SCRIPT, REPO_ROOT, SCRIPTS_ROOT, run_json
from OpenAIDatabase.tests.test_s09p2_self_iteration import SELF_ITERATION_CONFIG, write_self_iteration_fixtures


DECISION_DEBT_SCRIPT = REPO_ROOT / "scripts" / "build_memory_atlas_decision_debt.py"
DECISION_DEBT_CONFIG = REPO_ROOT / "机器治理" / "行为智能模型" / "decision_debt.v1_2_s09_p3.json"


def load_decision_debt_module():
    sys.path.insert(0, str(SCRIPTS_ROOT))
    spec = importlib.util.spec_from_file_location("build_memory_atlas_decision_debt", DECISION_DEBT_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def write_decision_debt_fixtures(root: Path) -> None:
    write_self_iteration_fixtures(root)
    run_json([
        sys.executable,
        str(ATLASCTL_SCRIPT),
        "analyze",
        "--stage",
        "latent",
        "--database-dir",
        str(root),
    ])
    self_iteration_target = root / "机器治理" / "行为智能模型" / "self_iteration.v1_2_s09_p2.json"
    self_iteration_target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SELF_ITERATION_CONFIG, self_iteration_target)
    run_json([
        sys.executable,
        str(ATLASCTL_SCRIPT),
        "analyze",
        "--stage",
        "self-iteration",
        "--database-dir",
        str(root),
    ])
    target = root / "机器治理" / "行为智能模型" / "decision_debt.v1_2_s09_p3.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(DECISION_DEBT_CONFIG, target)


class S09P3DecisionDebtTest(unittest.TestCase):
    def test_builds_decision_debt_ledger_with_minimal_next_steps(self) -> None:
        self.assertTrue(DECISION_DEBT_SCRIPT.exists(), "S09 P3 decision debt builder is missing")
        self.assertTrue(DECISION_DEBT_CONFIG.exists(), "S09 P3 decision debt config is missing")
        module = load_decision_debt_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_decision_debt_fixtures(root)
            output = root / "data/derived/behavior_intelligence/decision_debt_ledger.json"
            result = module.build_decision_debt_ledger(
                root,
                dry_run=True,
                generated_at="2026-07-08T00:00:00Z",
            )
            self.assertEqual(result["task_id"], "MA-V12-S09P3")
            self.assertEqual(result["acceptance_id"], "ACC-MA-V12-S09P3")
            self.assertEqual(result["status"], "phase_s09_p3_decision_debt_completed_pending_s09_review")
            self.assertFalse(output.exists())
            self.assertGreaterEqual(result["decision_debt_count"], 3)
            self.assertEqual(result["phase_boundary"]["next_phase"], "S09 Review")
            self.assertTrue(result["phase_boundary"]["does_not_generate_pressure_list"])
            self.assertTrue(result["phase_boundary"]["does_not_apply_proposals"])
            self.assertTrue(result["phase_boundary"]["does_not_modify_raw"])
            self.assertTrue(result["safety_summary"]["all_items_have_minimal_next_step"])
            self.assertFalse(result["safety_summary"]["pressure_list_created"])

            for item in result["decision_debt_ledger"]:
                self.assertTrue(item["decision_debt_id"])
                self.assertTrue(item["source_debt_ids"])
                self.assertTrue(item["decision_area_zh"])
                self.assertTrue(item["repeated_discussion_signal_zh"])
                self.assertTrue(item["evidence_refs"])
                self.assertTrue(item["linked_self_iteration_suggestion_ids"])
                self.assertTrue(item["not_pressure_list"])
                self.assertTrue(item["not_psychological_diagnosis"])
                self.assertTrue(item["not_personality_label"])
                self.assertLessEqual(item["confidence"], 0.75)
                minimal_next_step = item["minimal_next_step"]
                self.assertTrue(minimal_next_step["step_zh"])
                self.assertTrue(minimal_next_step["expected_artifact_zh"])
                self.assertTrue(minimal_next_step["stop_condition_zh"])
                self.assertGreater(minimal_next_step["effort_minutes_max"], 0)
                joined = " ".join([
                    item["decision_area_zh"],
                    item["repeated_discussion_signal_zh"],
                    minimal_next_step["step_zh"],
                    minimal_next_step["stop_condition_zh"],
                ])
                for blocked in ["心理诊断", "人格诊断", "人格标签", "抑郁", "焦虑症"]:
                    self.assertNotIn(blocked, joined)

    def test_atlasctl_decision_debt_dry_run_apply_and_safety_audit(self) -> None:
        self.assertTrue(DECISION_DEBT_CONFIG.exists(), "S09 P3 decision debt config is missing")
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_decision_debt_fixtures(root)
            output = root / "data/derived/behavior_intelligence/decision_debt_ledger.json"
            dry_run = run_json([
                sys.executable,
                str(ATLASCTL_SCRIPT),
                "analyze",
                "--stage",
                "decision-debt",
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
                "decision-debt",
                "--database-dir",
                str(root),
            ])
            self.assertEqual(applied["task_id"], "MA-V12-S09P3")
            self.assertTrue(output.exists())

            audit = run_json([
                sys.executable,
                str(ATLASCTL_SCRIPT),
                "audit",
                "--check",
                "decision-debt-safety",
                "--database-dir",
                str(root),
            ])
            self.assertEqual(audit["status"], "PASS")
            self.assertEqual(audit["bad_items"], [])
            self.assertGreaterEqual(audit["decision_debt_count"], 3)
            self.assertTrue(audit["all_items_have_minimal_next_step"])
            self.assertFalse(audit["pressure_list_created"])
            self.assertFalse(audit["proposal_apply_execution"])
            self.assertFalse(audit["raw_mutation"])
            self.assertFalse(audit["psychological_diagnosis_output"])
            self.assertFalse(audit["personality_label_output"])


if __name__ == "__main__":
    unittest.main()
