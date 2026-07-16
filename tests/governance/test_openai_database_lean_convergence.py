from __future__ import annotations

import hashlib
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = ROOT / "OpenAIDatabase"
sys.path.insert(0, str(ROOT / "scripts"))

import generate_governance_dashboard as dashboard  # noqa: E402
import lean_governance as lean  # noqa: E402
import validate_governance_sync as sync  # noqa: E402
import validate_information_quality as quality  # noqa: E402
import validate_project_governance as governance  # noqa: E402


BASELINE_BYTES = {
    "功能清单.md": 9000,
    "开发记录.md": 20770,
    "模型参数文件.md": 32500,
}
MAX_RENDERED_TOTAL_BYTES = 46000
BASELINE_TASK_COUNT = 21
MAX_BYTES_PER_ADDITIONAL_TASK = 1600
MAX_FEATURE_BYTES_PER_ADDITIONAL_TASK = 200
MAX_MODEL_BYTES_PER_ADDITIONAL_TASK = 201


class OpenAIDatabaseLeanConvergenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.project, cls.roadmap, cls.events = lean.load_project_facts(PROJECT_ROOT)
        cls.rendered = lean.rendered_project_texts(cls.project, cls.roadmap, cls.events)
        cls.disposition = json.loads(
            (PROJECT_ROOT / "docs" / "governance" / "legacy_disposition.json").read_text(
                encoding="utf-8"
            )
        )

    def test_legacy_disposition_is_exact_and_byte_locked(self) -> None:
        self.assertEqual(
            self.disposition["schema_version"],
            "openai_database.legacy_governance_disposition.v1",
        )
        self.assertEqual(self.disposition["legacy_dashboard_mode"], "frozen_read_only")
        self.assertEqual(len(self.disposition["canonical_editable_truth"]), 5)
        self.assertEqual(len(self.disposition["derived_human_views"]), 3)
        self.assertEqual(self.disposition["disposition"]["editable_legacy_truth_count"], 0)
        self.assertEqual(self.disposition["disposition"]["files_deleted"], 3)
        self.assertEqual(self.disposition["disposition"]["files_moved"], 0)
        legacy = self.disposition["retained_legacy_files"]
        self.assertEqual(len(legacy), 14)
        self.assertEqual(sum(item["bytes"] for item in legacy), 334805)
        for item in legacy:
            path = ROOT / item["path"]
            payload = path.read_bytes()
            self.assertEqual(len(payload), item["bytes"], item["path"])
            self.assertEqual(hashlib.sha256(payload).hexdigest(), item["sha256"], item["path"])

    def test_frozen_legacy_version_matrix_does_not_override_canonical_version(self) -> None:
        validation = governance.Validation()
        parsed = governance.parse_project_governance(
            PROJECT_ROOT,
            validation,
            required=True,
            scope="OpenAIDatabase",
        )
        governance.check_versions(
            validation,
            PROJECT_ROOT,
            parsed,
            required=True,
            scope="OpenAIDatabase",
        )
        self.assertEqual(validation.errors, [])

    def test_human_views_are_deterministic_complete_and_compressed(self) -> None:
        tasks = {
            task["task_id"]: task
            for stage in governance.as_list(self.roadmap.get("stages"))
            for phase in governance.as_list(stage.get("phases"))
            for task in governance.as_list(phase.get("tasks"))
        }
        self.assertEqual(tasks["TSK.OpenAIDatabase.CLEAN1.0001"]["status"], "in_progress")
        self.assertEqual(tasks["TSK.OpenAIDatabase.CLEAN1.0004"]["status"], "completed")
        self.assertEqual(tasks["TSK.OpenAIDatabase.CLEAN1.0005"]["status"], "completed")
        self.assertEqual(tasks["TSK.OpenAIDatabase.CLEAN1.0006"]["status"], "completed")
        self.assertEqual(tasks["TSK.OpenAIDatabase.CLEAN1.0007"]["status"], "completed")
        self.assertEqual(tasks["TSK.OpenAIDatabase.CLEAN1.0008"]["status"], "completed")
        self.assertEqual(tasks["TSK.OpenAIDatabase.CLEAN1.0009"]["status"], "completed")
        self.assertEqual(tasks["TSK.OpenAIDatabase.CLEAN1.0010"]["status"], "completed")
        self.assertEqual(tasks["TSK.OpenAIDatabase.PAM1.0001"]["status"], "completed")
        self.assertEqual(tasks["TSK.OpenAIDatabase.PAM1.0002"]["status"], "completed")
        self.assertEqual(tasks["TSK.OpenAIDatabase.PAM1.0003"]["status"], "completed")
        self.assertEqual(tasks["TSK.OpenAIDatabase.PAM1.0004"]["status"], "completed")
        self.assertEqual(tasks["TSK.OpenAIDatabase.PAM1.0005"]["status"], "completed")
        self.assertEqual(tasks["TSK.OpenAIDatabase.PAM1.0006"]["status"], "completed")
        self.assertEqual(tasks["TSK.OpenAIDatabase.PAM1.0007"]["status"], "completed")
        self.assertEqual(tasks["TSK.OpenAIDatabase.PAM1.0008"]["status"], "completed")
        self.assertEqual(tasks["TSK.OpenAIDatabase.PAM1.0009"]["status"], "completed")
        self.assertEqual(tasks["TSK.OpenAIDatabase.PAM1.0010"]["status"], "completed")
        self.assertEqual(tasks["TSK.OpenAIDatabase.PAM1.0011"]["status"], "completed")
        self.assertEqual(tasks["TSK.OpenAIDatabase.PAM1.0012"]["status"], "completed")
        self.assertEqual(tasks["TSK.OpenAIDatabase.PAM1.0013"]["status"], "completed")
        self.assertEqual(tasks["TSK.OpenAIDatabase.PAM1.0014"]["status"], "completed")
        self.assertEqual(tasks["TSK.OpenAIDatabase.PAM1.0015"]["status"], "completed")
        self.assertEqual(tasks["TSK.OpenAIDatabase.PAM1.0016"]["status"], "completed")
        self.assertEqual(tasks["TSK.OpenAIDatabase.PAM1.0017"]["status"], "completed")
        self.assertEqual(tasks["TSK.OpenAIDatabase.PAM1.0018"]["status"], "completed")
        self.assertEqual(tasks["TSK.OpenAIDatabase.PAM1.0019"]["status"], "in_progress")
        self.assertEqual(self.roadmap["current_task_id"], "TSK.OpenAIDatabase.PAM1.0019")
        self.assertEqual(lean.roadmap_totals(self.roadmap), {"total": 255.0, "completed": 241.0})
        self.assertEqual(self.roadmap["completed_estimated_hours"], 241)
        second = lean.rendered_project_texts(self.project, self.roadmap, self.events)
        self.assertEqual(self.rendered, second)
        sizes = {name: len(text.encode("utf-8")) for name, text in self.rendered.items()}
        additional_tasks = max(0, len(tasks) - BASELINE_TASK_COUNT)
        per_view_limits = {
            **BASELINE_BYTES,
            "功能清单.md": BASELINE_BYTES["功能清单.md"]
            + additional_tasks * MAX_FEATURE_BYTES_PER_ADDITIONAL_TASK,
            "模型参数文件.md": BASELINE_BYTES["模型参数文件.md"]
            + additional_tasks * MAX_MODEL_BYTES_PER_ADDITIONAL_TASK,
        }
        for name, baseline in per_view_limits.items():
            self.assertLess(sizes[name], baseline, name)
        total_limit = MAX_RENDERED_TOTAL_BYTES + additional_tasks * MAX_BYTES_PER_ADDITIONAL_TASK
        self.assertLessEqual(sum(sizes.values()), total_limit, sizes)

        features = self.rendered["功能清单.md"]
        development = self.rendered["开发记录.md"]
        models = self.rendered["模型参数文件.md"]
        self.assertGreater(len(features), 3000)
        self.assertGreater(len(development), 5000)
        self.assertGreater(len(models), 10000)
        for field in ("Gate", "Acceptance", "Result", "Evidence", "Rollback"):
            self.assertIn(field, development)
        for feature in governance.as_list(self.project.get("features")):
            self.assertIn(str(feature["feature_id"]), features)
        for stage in governance.as_list(self.roadmap.get("stages")):
            self.assertIn(str(stage["stage_id"]), development)
            stop_gate = stage.get("stop_gate") or {}
            if stop_gate.get("gate_id"):
                self.assertIn(str(stop_gate["gate_id"]), development)
            for phase in governance.as_list(stage.get("phases")):
                self.assertIn(str(phase["phase_id"]), development)
                phase_gate = phase.get("stop_gate") or {}
                if phase_gate.get("gate_id"):
                    self.assertIn(str(phase_gate["gate_id"]), development)
                for task in governance.as_list(phase.get("tasks")):
                    self.assertIn(str(task["task_id"]), development)
                    for acceptance_id in governance.as_list(task.get("acceptance_ids")):
                        self.assertIn(str(acceptance_id), development)
        for section, id_field in (
            ("models", "model_id"),
            ("formulas", "formula_id"),
            ("parameters", "parameter_id"),
        ):
            for item in governance.as_list(self.project.get(section)):
                self.assertIn(str(item[id_field]), models)
        for parameter in governance.as_list(self.project.get("parameters")):
            self.assertIn(str(parameter.get("source") or ""), models)

    def test_legacy_dashboard_writer_has_zero_project_outputs(self) -> None:
        result = dashboard.generate(False, project_filter="OpenAIDatabase")
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["outputs"], [])

    def test_disposition_is_project_governance_not_product_config(self) -> None:
        project = {"project_id": "OpenAIDatabase", "path": "OpenAIDatabase"}
        classification = sync.classify_project_file(
            project,
            "OpenAIDatabase/docs/governance/legacy_disposition.json",
        )
        self.assertEqual(classification, {"governance_only_change"})

    def test_frozen_lean_project_requires_canonical_bundle_not_locked_legacy(self) -> None:
        project = {"project_id": "OpenAIDatabase", "path": "OpenAIDatabase"}
        files = [
            "OpenAIDatabase/scripts/export_codex_history_archives.py",
            "OpenAIDatabase/data/run_logs/token_usage/data/summary.json",
            "OpenAIDatabase/docs/governance/project.yaml",
            "OpenAIDatabase/docs/governance/roadmap.yaml",
            "OpenAIDatabase/docs/governance/events.jsonl",
            "OpenAIDatabase/CHANGELOG.md",
            "OpenAIDatabase/VERSION",
            "OpenAIDatabase/功能清单.md",
            "OpenAIDatabase/开发记录.md",
            "OpenAIDatabase/模型参数文件.md",
        ]
        changes, _ = sync.classify_changes({"projects": [project]}, files)
        validation = sync.SyncValidation()
        sync.validate_diff_contract(validation, changes)
        self.assertEqual(validation.errors, [])
        self.assertTrue(sync.uses_frozen_lean_governance(project))
        self.assertNotIn(
            "docs/governance/parameter_registry.csv",
            sync.LEAN_FROZEN_REQUIRED_FILES,
        )
        for retired_view in ("功能清单.md", "开发记录.md", "模型参数文件.md"):
            self.assertNotIn(retired_view, sync.LEAN_FROZEN_REQUIRED_FILES)
            self.assertFalse((PROJECT_ROOT / retired_view).exists())

    def test_frozen_legacy_event_ledger_is_not_a_current_diff_writer(self) -> None:
        project = {"project_id": "OpenAIDatabase", "path": "OpenAIDatabase"}
        changes, _ = sync.classify_changes(
            {"projects": [project]},
            [
                "OpenAIDatabase/scripts/memory.py",
                "OpenAIDatabase/docs/governance/project.yaml",
                "OpenAIDatabase/docs/governance/roadmap.yaml",
                "OpenAIDatabase/docs/governance/events.jsonl",
                "OpenAIDatabase/VERSION",
                "OpenAIDatabase/CHANGELOG.md",
            ],
        )
        validation = sync.SyncValidation()
        sync.validate_event_files_changed(validation, changes, changed_only=True)
        self.assertEqual(validation.errors, [])

    def test_information_quality_reads_canonical_events_after_freeze(self) -> None:
        gate = quality.Gate()
        quality.check_events(
            gate,
            {"project_id": "OpenAIDatabase", "path": "OpenAIDatabase"},
        )
        self.assertEqual(gate.errors, [])

    def test_stable_entry_points_do_not_publish_temporary_task_state(self) -> None:
        readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
        agents = (PROJECT_ROOT / "AGENTS.md").read_text(encoding="utf-8")
        for stale in (
            "S6PAT02",
            "v1.2 S01 P3 Requirements Freeze Bridge",
            "S5PBT02 Structure Boundary",
            "下一步是 S01",
        ):
            self.assertNotIn(stale, readme)
            self.assertNotIn(stale, agents)
        self.assertIn("Lean Governance Boundary", agents)
        self.assertIn("legacy_disposition.json", readme)


if __name__ == "__main__":
    unittest.main()
