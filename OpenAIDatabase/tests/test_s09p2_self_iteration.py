from __future__ import annotations

import importlib.util
import shutil
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from OpenAIDatabase.tests.test_s06p3_opportunity_discovery import ATLASCTL_SCRIPT, REPO_ROOT, SCRIPTS_ROOT, run_json
from OpenAIDatabase.tests.test_s09p1_latent_signals import write_latent_fixtures


SELF_ITERATION_SCRIPT = REPO_ROOT / "scripts" / "build_memory_atlas_self_iteration.py"
SELF_ITERATION_CONFIG = REPO_ROOT / "机器治理" / "行为智能模型" / "self_iteration.v1_2_s09_p2.json"


def load_self_iteration_module():
    sys.path.insert(0, str(SCRIPTS_ROOT))
    spec = importlib.util.spec_from_file_location("build_memory_atlas_self_iteration", SELF_ITERATION_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def write_self_iteration_fixtures(root: Path) -> None:
    write_latent_fixtures(root)
    run_json([
        sys.executable,
        str(ATLASCTL_SCRIPT),
        "analyze",
        "--stage",
        "latent",
        "--database-dir",
        str(root),
    ])
    target = root / "机器治理" / "行为智能模型" / "self_iteration.v1_2_s09_p2.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SELF_ITERATION_CONFIG, target)


class S09P2SelfIterationTest(unittest.TestCase):
    def test_builds_self_iteration_suggestions_with_expiring_proposals(self) -> None:
        self.assertTrue(SELF_ITERATION_SCRIPT.exists(), "S09 P2 self-iteration builder is missing")
        self.assertTrue(SELF_ITERATION_CONFIG.exists(), "S09 P2 self-iteration config is missing")
        module = load_self_iteration_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_self_iteration_fixtures(root)
            output = root / "data/derived/behavior_intelligence/self_iteration_suggestions.json"
            result = module.build_self_iteration_suggestions(
                root,
                dry_run=True,
                generated_at="2026-07-08T00:00:00Z",
            )
            self.assertEqual(result["task_id"], "MA-V12-S09P2")
            self.assertEqual(result["acceptance_id"], "ACC-MA-V12-S09P2")
            self.assertEqual(result["status"], "phase_s09_p2_self_iteration_completed_pending_s09_p3")
            self.assertFalse(output.exists())
            self.assertGreaterEqual(result["suggestion_count"], 5)
            self.assertEqual(result["phase_boundary"]["next_phase"], "S09 P3")
            self.assertTrue(result["phase_boundary"]["does_not_apply_proposals"])
            self.assertTrue(result["phase_boundary"]["does_not_create_decision_debt_ledger"])
            self.assertTrue(result["proposal_expiry_summary"]["all_proposals_have_expiry"])
            self.assertTrue(result["proposal_expiry_summary"]["all_suggestions_have_action_half_life"])

            target_types = {item["target_type"] for item in result["self_iteration_suggestions"]}
            self.assertGreaterEqual(target_types, {"memory", "config", "AGENTS", "style", "personalization"})
            for suggestion in result["self_iteration_suggestions"]:
                self.assertTrue(suggestion["evidence_refs"])
                self.assertTrue(suggestion["rationale_zh"])
                self.assertTrue(suggestion["expected_change_zh"])
                self.assertGreater(suggestion["action_half_life_days"], 0)
                proposal = suggestion["proposal"]
                self.assertEqual(proposal["state"], "pending_human_review")
                self.assertFalse(proposal["apply_execution_allowed"])
                self.assertFalse(proposal["raw_apply_target_allowed"])
                self.assertTrue(proposal["expires_at"])
                self.assertGreater(datetime.fromisoformat(proposal["expires_at"].replace("Z", "+00:00")), datetime.fromisoformat(proposal["created_at"].replace("Z", "+00:00")))
                self.assertIn("rollback_plan_zh", proposal)
                self.assertTrue(proposal["evidence_refs"])
                self.assertIn("validation_commands", proposal)
                self.assertTrue(proposal["validation_commands"])

    def test_atlasctl_self_iteration_dry_run_apply_and_safety_audit(self) -> None:
        self.assertTrue(SELF_ITERATION_CONFIG.exists(), "S09 P2 self-iteration config is missing")
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_self_iteration_fixtures(root)
            output = root / "data/derived/behavior_intelligence/self_iteration_suggestions.json"
            dry_run = run_json([
                sys.executable,
                str(ATLASCTL_SCRIPT),
                "analyze",
                "--stage",
                "self-iteration",
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
                "self-iteration",
                "--database-dir",
                str(root),
            ])
            self.assertEqual(applied["task_id"], "MA-V12-S09P2")
            self.assertTrue(output.exists())

            audit = run_json([
                sys.executable,
                str(ATLASCTL_SCRIPT),
                "audit",
                "--check",
                "self-iteration-safety",
                "--database-dir",
                str(root),
            ])
            self.assertEqual(audit["status"], "PASS")
            self.assertEqual(audit["bad_items"], [])
            self.assertGreaterEqual(audit["suggestion_count"], 5)
            self.assertTrue(audit["all_proposals_have_expiry"])
            self.assertTrue(audit["all_suggestions_have_action_half_life"])
            self.assertFalse(audit["proposal_apply_execution"])
            self.assertFalse(audit["decision_debt_ledger_created"])
            self.assertFalse(audit["raw_mutation"])


if __name__ == "__main__":
    unittest.main()
