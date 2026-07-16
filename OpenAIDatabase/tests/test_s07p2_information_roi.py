from __future__ import annotations

import importlib.util
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from OpenAIDatabase.tests.memory_test_support import write_canonical_memory
from OpenAIDatabase.tests.test_s07p1_economic_proxy import (
    ATLASCTL_SCRIPT,
    REPO_ROOT,
    SCRIPTS_ROOT,
    run_json,
    write_economic_proxy_fixtures,
)


INFORMATION_ROI_SCRIPT = REPO_ROOT / "scripts" / "build_memory_atlas_information_roi.py"
FORMULA_CONFIG = REPO_ROOT / "机器治理" / "参数与公式" / "information_roi.v1_2_s07_p2.json"
VISUAL_GATE_CONFIG = REPO_ROOT / "机器治理" / "可视化配置" / "visual_roi_gate.v1_2_s07_p2.json"


def load_information_roi_module():
    sys.path.insert(0, str(SCRIPTS_ROOT))
    spec = importlib.util.spec_from_file_location("build_memory_atlas_information_roi", INFORMATION_ROI_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def copy_s07p2_configs(root: Path) -> None:
    formula_target = root / "机器治理" / "参数与公式" / "information_roi.v1_2_s07_p2.json"
    visual_target = root / "机器治理" / "可视化配置" / "visual_roi_gate.v1_2_s07_p2.json"
    formula_target.parent.mkdir(parents=True, exist_ok=True)
    visual_target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(FORMULA_CONFIG, formula_target)
    shutil.copy2(VISUAL_GATE_CONFIG, visual_target)


def write_information_roi_fixtures(root: Path) -> None:
    write_economic_proxy_fixtures(root)
    copy_s07p2_configs(root)
    write_canonical_memory(
        root,
        [
            {
                "id": "mem_information_roi_fixture",
                "statement": "Synthetic Memory Atlas information ROI fixture.",
                "category": "project_context",
                "status": "active",
                "date": "2026-07-08",
                "importance": "中",
                "confidence": "high",
                "memory_tier": "一般",
                "sensitivity": "public",
            }
        ],
    )
    run_json([
        sys.executable,
        str(ATLASCTL_SCRIPT),
        "analyze",
        "--stage",
        "economic-proxy",
        "--database-dir",
        str(root),
        "--apply",
    ])
    atlas_output = root / "data" / "derived" / "visualization" / "memory_atlas.json"
    run_json([
        sys.executable,
        str(REPO_ROOT / "scripts" / "build_memory_atlas_data.py"),
        "--database-dir",
        str(root),
        "--output",
        atlas_output.relative_to(root).as_posix(),
    ])


class S07P2InformationRoiTest(unittest.TestCase):
    def test_builds_information_roi_for_insights_cards_and_charts(self) -> None:
        module = load_information_roi_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_information_roi_fixtures(root)
            result = module.build_information_roi(root, dry_run=True, generated_at="2026-07-08T00:00:00Z")
            self.assertEqual(result["task_id"], "MA-V12-S07P2")
            self.assertEqual(result["acceptance_id"], "ACC-MA-V12-S07P2")
            self.assertEqual(result["status"], "phase_s07_p2_information_roi_completed_pending_s07_p3")
            self.assertFalse(result["external_economic_database"]["current_dependency"])
            self.assertFalse((root / "data/derived/information_roi/information_roi_gate.json").exists())
            item_types = {item["item_type"] for item in result["roi_items"]}
            self.assertEqual(item_types, {"insight", "card", "chart"})
            self.assertGreaterEqual(result["roi_summary"]["item_count"], 20)
            self.assertEqual(result["visual_roi_gate"]["failed_p0_count"], 0)
            self.assertEqual(result["visual_roi_gate"]["p0_candidate_count"], 10)
            self.assertTrue(result["visual_roi_gate"]["excluded_from_p0"])
            for item in result["roi_items"]:
                self.assertTrue(item["formula_id"])
                self.assertTrue(item["formula_source"].endswith("information_roi.v1_2_s07_p2.json"))
                self.assertTrue(item["decision_summary_zh"])
                self.assertTrue(item["evidence_refs"])
                self.assertGreaterEqual(item["information_roi_score"], 0)
                self.assertLessEqual(item["information_roi_score"], 100)
                if item["item_type"] == "chart" and item["p0_candidate"]:
                    self.assertTrue(item["human_question"])
                    self.assertTrue(item["action_zh"])
                    self.assertTrue(item["visual_roi_gate_pass"])

    def test_atlasctl_information_roi_apply_and_visual_roi_audit(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_information_roi_fixtures(root)
            dry_run = run_json([
                sys.executable,
                str(ATLASCTL_SCRIPT),
                "analyze",
                "--stage",
                "information-roi",
                "--database-dir",
                str(root),
                "--dry-run",
            ])
            self.assertTrue(dry_run["dry_run"])
            self.assertFalse(dry_run["writes_files"])
            self.assertFalse((root / "data/derived/information_roi/information_roi_gate.json").exists())

            applied = run_json([
                sys.executable,
                str(ATLASCTL_SCRIPT),
                "analyze",
                "--stage",
                "information-roi",
                "--database-dir",
                str(root),
                "--apply",
            ])
            self.assertEqual(applied["task_id"], "MA-V12-S07P2")
            self.assertTrue((root / "data/derived/information_roi/information_roi_gate.json").exists())

            audit = run_json([
                sys.executable,
                str(ATLASCTL_SCRIPT),
                "audit",
                "--check",
                "visual-roi",
                "--database-dir",
                str(root),
            ])
            self.assertEqual(audit["status"], "PASS")
            self.assertEqual(audit["bad_items"], [])
            self.assertEqual(audit["p0_visual_count"], 10)
            self.assertEqual(audit["failed_p0_count"], 0)


if __name__ == "__main__":
    unittest.main()
