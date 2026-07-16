from __future__ import annotations

import importlib.util
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from OpenAIDatabase.tests.test_s06p3_opportunity_discovery import ATLASCTL_SCRIPT, REPO_ROOT, SCRIPTS_ROOT, run_json, write_opportunity_fixtures


ECONOMIC_PROXY_SCRIPT = REPO_ROOT / "scripts" / "build_memory_atlas_economic_proxy.py"
FORMULA_CONFIG = REPO_ROOT / "机器治理" / "参数与公式" / "personal_economic_proxy.v1_2_s07_p1.json"


def load_economic_proxy_module():
    sys.path.insert(0, str(SCRIPTS_ROOT))
    spec = importlib.util.spec_from_file_location("build_memory_atlas_economic_proxy", ECONOMIC_PROXY_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def write_formula_config(root: Path) -> None:
    target = root / "机器治理" / "参数与公式" / "personal_economic_proxy.v1_2_s07_p1.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(FORMULA_CONFIG, target)


def write_economic_proxy_fixtures(root: Path) -> None:
    write_formula_config(root)
    write_opportunity_fixtures(root)
    run_json([
        sys.executable,
        str(ATLASCTL_SCRIPT),
        "analyze",
        "--stage",
        "opportunities",
        "--database-dir",
        str(root),
        "--apply",
    ])


class S07P1EconomicProxyTest(unittest.TestCase):
    def test_builds_internal_proxy_with_formula_sources(self) -> None:
        module = load_economic_proxy_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_economic_proxy_fixtures(root)
            result = module.build_personal_economic_proxy(root, dry_run=True, generated_at="2026-07-08T00:00:00Z")
            self.assertEqual(result["task_id"], "MA-V12-S07P1")
            self.assertEqual(result["acceptance_id"], "ACC-MA-V12-S07P1")
            self.assertEqual(result["status"], "phase_s07_p1_economic_proxy_completed_pending_s07_p2")
            self.assertFalse(result["external_economic_database"]["current_dependency"])
            self.assertEqual(len(result["score_cards"]), 6)
            self.assertFalse((root / "data/derived/economic_proxy/personal_economic_proxy.json").exists())
            score_keys = {card["score_key"] for card in result["score_cards"]}
            self.assertEqual(
                score_keys,
                {
                    "time_saved_proxy",
                    "reuse_value_proxy",
                    "rework_cost_proxy",
                    "opportunity_score_proxy",
                    "skill_compounding_proxy",
                    "automation_enhancement_ratio_proxy",
                },
            )
            for card in result["score_cards"]:
                self.assertTrue(card["formula_id"])
                self.assertTrue(card["formula_source"].endswith("personal_economic_proxy.v1_2_s07_p1.json"))
                self.assertTrue(card["parameter_refs"])
                self.assertTrue(card["evidence_refs"])
                self.assertTrue(card["explanation_zh"])
                self.assertGreaterEqual(card["score"], 0)
                self.assertLessEqual(card["score"], 100)

    def test_atlasctl_economic_proxy_apply_and_formula_audit(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_economic_proxy_fixtures(root)
            dry_run = run_json([
                sys.executable,
                str(ATLASCTL_SCRIPT),
                "analyze",
                "--stage",
                "economic-proxy",
                "--database-dir",
                str(root),
                "--dry-run",
            ])
            self.assertTrue(dry_run["dry_run"])
            self.assertFalse(dry_run["writes_files"])
            self.assertFalse((root / "data/derived/economic_proxy/personal_economic_proxy.json").exists())

            applied = run_json([
                sys.executable,
                str(ATLASCTL_SCRIPT),
                "analyze",
                "--stage",
                "economic-proxy",
                "--database-dir",
                str(root),
                "--apply",
            ])
            self.assertEqual(applied["task_id"], "MA-V12-S07P1")
            self.assertTrue((root / "data/derived/economic_proxy/personal_economic_proxy.json").exists())

            audit = run_json([
                sys.executable,
                str(ATLASCTL_SCRIPT),
                "audit",
                "--check",
                "formulas",
                "--database-dir",
                str(root),
            ])
            self.assertEqual(audit["status"], "PASS")
            self.assertEqual(audit["bad_items"], [])
            self.assertEqual(audit["formula_count"], 6)
            self.assertEqual(audit["score_card_count"], 6)


if __name__ == "__main__":
    unittest.main()
