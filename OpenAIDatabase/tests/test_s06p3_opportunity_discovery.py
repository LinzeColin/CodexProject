from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

from OpenAIDatabase.tests.test_s06p2_low_value_loops import ATLASCTL_SCRIPT, REPO_ROOT, SCRIPTS_ROOT, run_json, write_loop_fixtures


OPPORTUNITY_SCRIPT = REPO_ROOT / "scripts" / "build_memory_atlas_opportunities.py"


def load_opportunity_module():
    sys.path.insert(0, str(SCRIPTS_ROOT))
    spec = importlib.util.spec_from_file_location("build_memory_atlas_opportunities", OPPORTUNITY_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def write_opportunity_fixtures(root: Path) -> None:
    write_loop_fixtures(root)
    run_json([
        sys.executable,
        str(ATLASCTL_SCRIPT),
        "analyze",
        "--stage",
        "low-value-loops",
        "--database-dir",
        str(root),
        "--apply",
    ])


class S06P3OpportunityDiscoveryTest(unittest.TestCase):
    def test_builds_opportunities_and_why_not_now_cards(self) -> None:
        module = load_opportunity_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_opportunity_fixtures(root)
            result = module.build_opportunities(root, dry_run=True, generated_at="2026-07-08T00:00:00Z")
            self.assertEqual(result["task_id"], "MA-V12-S06P3")
            self.assertEqual(result["acceptance_id"], "ACC-MA-V12-S06P3")
            self.assertGreaterEqual(result["opportunity_count"], 5)
            self.assertGreaterEqual(result["defer_card_count"], 1)
            self.assertFalse((root / "data/derived/behavior_intelligence/opportunities.json").exists())
            opportunity_types = {item["opportunity_type"] for item in result["opportunity_clusters"]}
            self.assertIn("automation", opportunity_types)
            self.assertIn("productization", opportunity_types)
            self.assertIn("template", opportunity_types)
            self.assertIn("compounding", opportunity_types)
            self.assertIn("defer", opportunity_types)
            for opportunity in result["opportunity_clusters"]:
                self.assertTrue(opportunity["evidence_refs"])
                self.assertIn("候选机会", opportunity["summary_zh"])
                self.assertTrue(opportunity["next_step_zh"])
                self.assertNotIn("心理诊断", opportunity["summary_zh"])
                self.assertTrue(
                    opportunity.get("opportunity_half_life_days", 0) > 0 or opportunity.get("defer_reason_zh"),
                    opportunity,
                )
                card = opportunity.get("why_not_now_card")
                self.assertTrue(card)
                self.assertTrue(card["reason_zh"])
                self.assertTrue(card["not_pressure_list"])

    def test_atlasctl_opportunities_dry_run_apply_and_audit(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_opportunity_fixtures(root)
            dry_run = run_json([
                sys.executable,
                str(ATLASCTL_SCRIPT),
                "analyze",
                "--stage",
                "opportunities",
                "--database-dir",
                str(root),
                "--dry-run",
            ])
            self.assertTrue(dry_run["dry_run"])
            self.assertFalse(dry_run["writes_files"])
            self.assertFalse((root / "data/derived/behavior_intelligence/opportunities.json").exists())

            applied = run_json([
                sys.executable,
                str(ATLASCTL_SCRIPT),
                "analyze",
                "--stage",
                "opportunities",
                "--database-dir",
                str(root),
                "--apply",
            ])
            opportunities_path = root / "data/derived/behavior_intelligence/opportunities.json"
            self.assertEqual(applied["task_id"], "MA-V12-S06P3")
            self.assertTrue(opportunities_path.exists())
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
            self.assertEqual(audit["opportunity_task_id"], "MA-V12-S06P3")


if __name__ == "__main__":
    unittest.main()
