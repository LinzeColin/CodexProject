from __future__ import annotations

import importlib.util
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from OpenAIDatabase.tests.test_s06p3_opportunity_discovery import (
    ATLASCTL_SCRIPT,
    REPO_ROOT,
    SCRIPTS_ROOT,
    run_json,
    write_opportunity_fixtures,
)


LATENT_SCRIPT = REPO_ROOT / "scripts" / "build_memory_atlas_latent_signals.py"
LATENT_CONFIG = REPO_ROOT / "机器治理" / "行为智能模型" / "latent_signals.v1_2_s09_p1.json"


def load_latent_module():
    sys.path.insert(0, str(SCRIPTS_ROOT))
    spec = importlib.util.spec_from_file_location("build_memory_atlas_latent_signals", LATENT_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def write_latent_fixtures(root: Path) -> None:
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
    target = root / "机器治理" / "行为智能模型" / "latent_signals.v1_2_s09_p1.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(LATENT_CONFIG, target)


class S09P1LatentSignalsTest(unittest.TestCase):
    def test_builds_falsifiable_latent_signals_with_evidence_badges(self) -> None:
        self.assertTrue(LATENT_SCRIPT.exists(), "S09 P1 latent signal builder is missing")
        self.assertTrue(LATENT_CONFIG.exists(), "S09 P1 latent signal config is missing")
        module = load_latent_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_latent_fixtures(root)
            output = root / "data/derived/behavior_intelligence/latent_signals.json"
            result = module.build_latent_signals(root, dry_run=True, generated_at="2026-07-08T00:00:00Z")
            self.assertEqual(result["task_id"], "MA-V12-S09P1")
            self.assertEqual(result["acceptance_id"], "ACC-MA-V12-S09P1")
            self.assertEqual(result["status"], "phase_s09_p1_latent_signals_completed_pending_s09_p2")
            self.assertFalse(output.exists())
            self.assertGreaterEqual(result["signal_count"], 4)
            self.assertTrue(result["safety_audit"]["psychological_diagnosis_output_blocked"])
            self.assertTrue(result["safety_audit"]["personality_label_output_blocked"])
            self.assertEqual(result["phase_boundary"]["next_phase"], "S09 P2")
            self.assertTrue(result["phase_boundary"]["does_not_create_self_iteration_suggestions"])
            self.assertTrue(result["phase_boundary"]["does_not_create_decision_debt_ledger"])

            badges = {signal["evidence_strength_badge"] for signal in result["latent_signals"]}
            self.assertLessEqual(badges, {"A", "B", "C", "D"})
            banned_terms = ["心理诊断", "人格诊断", "抑郁", "焦虑症", "人格标签"]
            for signal in result["latent_signals"]:
                self.assertTrue(signal["claim_zh"])
                self.assertTrue(signal["supporting_evidence_refs"])
                self.assertTrue(signal["contradicting_evidence_refs"])
                self.assertTrue(signal["alternative_explanation_zh"])
                self.assertTrue(signal["next_validation_zh"])
                self.assertIsInstance(signal["confidence"], (int, float))
                self.assertGreaterEqual(signal["confidence"], 0)
                self.assertLessEqual(signal["confidence"], 0.85)
                self.assertTrue(signal["not_psychological_diagnosis"])
                self.assertTrue(signal["not_personality_label"])
                self.assertNotIn("diagnosis", signal["claim_type"])
                joined = " ".join([
                    signal["claim_zh"],
                    signal["alternative_explanation_zh"],
                    signal["next_validation_zh"],
                ])
                self.assertFalse(any(term in joined for term in banned_terms), signal)

    def test_atlasctl_latent_signals_dry_run_apply_and_safety_audit(self) -> None:
        self.assertTrue(LATENT_CONFIG.exists(), "S09 P1 latent signal config is missing")
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_latent_fixtures(root)
            output = root / "data/derived/behavior_intelligence/latent_signals.json"
            dry_run = run_json([
                sys.executable,
                str(ATLASCTL_SCRIPT),
                "analyze",
                "--stage",
                "latent",
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
                "latent",
                "--database-dir",
                str(root),
                "--apply",
            ])
            self.assertEqual(applied["task_id"], "MA-V12-S09P1")
            self.assertTrue(output.exists())

            audit = run_json([
                sys.executable,
                str(ATLASCTL_SCRIPT),
                "audit",
                "--check",
                "latent-safety",
                "--database-dir",
                str(root),
            ])
            self.assertEqual(audit["status"], "PASS")
            self.assertEqual(audit["bad_items"], [])
            self.assertGreaterEqual(audit["signal_count"], 4)
            self.assertFalse(audit["psychological_diagnosis_output"])
            self.assertFalse(audit["personality_label_output"])
            self.assertTrue(audit["has_contradicting_evidence"])


if __name__ == "__main__":
    unittest.main()
