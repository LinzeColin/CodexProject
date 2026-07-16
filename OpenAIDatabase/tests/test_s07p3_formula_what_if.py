from __future__ import annotations

import importlib.util
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from OpenAIDatabase.tests.test_s07p1_economic_proxy import ATLASCTL_SCRIPT, REPO_ROOT, SCRIPTS_ROOT, run_json
from OpenAIDatabase.tests.test_s07p2_information_roi import write_information_roi_fixtures


FORMULA_WHAT_IF_SCRIPT = REPO_ROOT / "scripts" / "build_memory_atlas_formula_what_if.py"
WHAT_IF_CONFIG = REPO_ROOT / "机器治理" / "参数与公式" / "formula_what_if_defaults.v1_2_s07_p3.json"


def load_formula_what_if_module():
    sys.path.insert(0, str(SCRIPTS_ROOT))
    spec = importlib.util.spec_from_file_location("build_memory_atlas_formula_what_if", FORMULA_WHAT_IF_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def write_formula_what_if_fixtures(root: Path) -> None:
    write_information_roi_fixtures(root)
    target = root / "机器治理" / "参数与公式" / "formula_what_if_defaults.v1_2_s07_p3.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(WHAT_IF_CONFIG, target)
    run_json([
        sys.executable,
        str(ATLASCTL_SCRIPT),
        "analyze",
        "--stage",
        "information-roi",
        "--database-dir",
        str(root),
        "--apply",
    ])


class S07P3FormulaWhatIfTest(unittest.TestCase):
    def test_builds_formula_what_if_preview_without_active_config_write(self) -> None:
        module = load_formula_what_if_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_formula_what_if_fixtures(root)
            output = root / "data/derived/economic_proxy/formula_what_if_preview.json"
            result = module.build_formula_what_if(root, dry_run=True, generated_at="2026-07-08T00:00:00Z")
            self.assertEqual(result["task_id"], "MA-V12-S07P3")
            self.assertEqual(result["acceptance_id"], "ACC-MA-V12-S07P3")
            self.assertEqual(result["status"], "phase_s07_p3_formula_what_if_completed_pending_s07_review")
            self.assertFalse(output.exists())
            self.assertEqual(result["simulator_mode"], "config_preview_only")
            self.assertTrue(result["phase_boundary"]["does_not_mutate_active_formula_config"])
            self.assertTrue(result["phase_boundary"]["requires_proposal_before_apply"])
            self.assertTrue(result["phase_boundary"]["does_not_use_external_economic_database"])
            self.assertGreaterEqual(result["scenario_count"], 4)
            covered = set()
            for scenario in result["scenarios"]:
                self.assertGreaterEqual(scenario["weighted_proxy_score"], 0)
                self.assertLessEqual(scenario["weighted_proxy_score"], 100)
                self.assertFalse(scenario["parameter_change_proposal"]["active_config_write"])
                self.assertTrue(scenario["parameter_change_proposal"]["proposal_required_before_apply"])
                covered.update(scenario["adjustable_weights"])
            self.assertIn("time_saved_weight", covered)
            self.assertIn("reuse_value_weight", covered)
            self.assertIn("skill_compounding_weight", covered)

    def test_atlasctl_formula_what_if_apply_and_audit(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_formula_what_if_fixtures(root)
            output = root / "data/derived/economic_proxy/formula_what_if_preview.json"
            dry_run = run_json([
                sys.executable,
                str(ATLASCTL_SCRIPT),
                "analyze",
                "--stage",
                "formula-what-if",
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
                "formula-what-if",
                "--database-dir",
                str(root),
                "--apply",
            ])
            self.assertEqual(applied["task_id"], "MA-V12-S07P3")
            self.assertTrue(output.exists())

            audit = run_json([
                sys.executable,
                str(ATLASCTL_SCRIPT),
                "audit",
                "--check",
                "formula-what-if",
                "--database-dir",
                str(root),
            ])
            self.assertEqual(audit["status"], "PASS")
            self.assertEqual(audit["bad_items"], [])
            self.assertFalse(audit["active_config_write"])
            self.assertTrue(audit["proposal_required_before_apply"])


if __name__ == "__main__":
    unittest.main()
