from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = ROOT / "scripts" / "validate_project_governance.py"


def load_validator_module():
    spec = importlib.util.spec_from_file_location("validate_project_governance", VALIDATOR)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def run_validator(*args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.setdefault("PYTHONPYCACHEPREFIX", "/tmp/codex_governance_test_pycache")
    return subprocess.run(
        [sys.executable, str(VALIDATOR), *args],
        cwd=ROOT,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )


class ProjectGovernanceValidatorTests(unittest.TestCase):
    def test_all_registered_projects_pass_current_validator(self) -> None:
        result = run_validator("--all")
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("errors: 0", result.stdout)
        self.assertIn("warnings: 0", result.stdout)

    def test_unknown_project_returns_nonzero(self) -> None:
        result = run_validator("--project", "__missing_project__")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Unknown project: __missing_project__", result.stdout)

    def test_required_mode_promotes_missing_file_warning_to_error(self) -> None:
        validator = load_validator_module()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            project_files = ["docs/governance/MODEL_SPEC.md"]
            project = {
                "project_id": "BROKEN",
                "path": "BROKEN",
                "ci_mode": "advisory",
                "status": "existing",
                "model_behavior_globs": [],
            }
            (tmp_path / "BROKEN").mkdir()

            with patch.object(validator, "ROOT", tmp_path):
                advisory = validator.Validation()
                validator.validate_project(advisory, project, project_files, mode=None)
                self.assertFalse(advisory.errors)
                self.assertTrue(advisory.warnings)

                required = validator.Validation()
                validator.validate_project(required, project, project_files, mode="required")
                self.assertTrue(required.errors)

    def test_changed_only_root_governance_change_selects_all_projects(self) -> None:
        validator = load_validator_module()
        config = {
            "projects": [
                {"project_id": "A", "path": "A", "model_behavior_globs": []},
                {"project_id": "B", "path": "B", "model_behavior_globs": []},
            ]
        }
        args = SimpleNamespace(project=None, changed_only=True)

        with patch.object(
            validator,
            "git_changed_files",
            return_value=["docs/governance/STANDARD.md", "A/README.md"],
        ):
            selected = validator.select_projects(config, args)

        self.assertEqual([project["project_id"] for project in selected], ["A", "B"])

    def test_manual_acceptance_count_drift_is_reported(self) -> None:
        validator = load_validator_module()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            docs = tmp_path / "P" / "docs" / "governance"
            docs.mkdir(parents=True)
            (docs / "DELIVERY_PLAN.md").write_text(
                "machine_summary:\n- acceptance_count: 2\n",
                encoding="utf-8",
            )
            parsed = {
                "models": [],
                "formulas": [],
                "parameters": [],
                "tasks": [{"task_id": "TASK-001", "acceptance_ids": ["ACC-001"]}],
            }

            with patch.object(validator, "ROOT", tmp_path):
                validation = validator.Validation()
                validator.check_manual_counts(validation, tmp_path / "P", parsed, True, "P")

            self.assertTrue(validation.errors)
            self.assertIn("acceptance_count=2, actual=1", validation.errors[0].message)


if __name__ == "__main__":
    unittest.main()
