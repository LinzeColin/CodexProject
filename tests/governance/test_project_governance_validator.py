from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace


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


def test_all_registered_projects_pass_current_validator() -> None:
    result = run_validator("--all")
    assert result.returncode == 0, result.stdout
    assert "errors: 0" in result.stdout
    assert "warnings: 0" in result.stdout


def test_unknown_project_returns_nonzero() -> None:
    result = run_validator("--project", "__missing_project__")
    assert result.returncode != 0
    assert "Unknown project: __missing_project__" in result.stdout


def test_required_mode_promotes_missing_file_warning_to_error(tmp_path, monkeypatch) -> None:
    validator = load_validator_module()
    monkeypatch.setattr(validator, "ROOT", tmp_path)
    project_files = ["docs/governance/MODEL_SPEC.md"]
    project = {
        "project_id": "BROKEN",
        "path": "BROKEN",
        "ci_mode": "advisory",
        "status": "existing",
        "model_behavior_globs": [],
    }
    (tmp_path / "BROKEN").mkdir()

    advisory = validator.Validation()
    validator.validate_project(advisory, project, project_files, mode=None)
    assert not advisory.errors
    assert advisory.warnings

    required = validator.Validation()
    validator.validate_project(required, project, project_files, mode="required")
    assert required.errors


def test_changed_only_root_governance_change_selects_all_projects(monkeypatch) -> None:
    validator = load_validator_module()
    config = {
        "projects": [
            {"project_id": "A", "path": "A", "model_behavior_globs": []},
            {"project_id": "B", "path": "B", "model_behavior_globs": []},
        ]
    }
    args = SimpleNamespace(project=None, changed_only=True)
    monkeypatch.setattr(
        validator,
        "git_changed_files",
        lambda: ["docs/governance/STANDARD.md", "A/README.md"],
    )

    selected = validator.select_projects(config, args)
    assert [project["project_id"] for project in selected] == ["A", "B"]


def test_manual_acceptance_count_drift_is_reported(tmp_path, monkeypatch) -> None:
    validator = load_validator_module()
    monkeypatch.setattr(validator, "ROOT", tmp_path)
    docs = tmp_path / "P" / "docs" / "governance"
    docs.mkdir(parents=True)
    (docs / "DELIVERY_PLAN.md").write_text("machine_summary:\n- acceptance_count: 2\n", encoding="utf-8")
    parsed = {
        "models": [],
        "formulas": [],
        "parameters": [],
        "tasks": [{"task_id": "TASK-001", "acceptance_ids": ["ACC-001"]}],
    }

    validation = validator.Validation()
    validator.check_manual_counts(validation, tmp_path / "P", parsed, True, "P")
    assert validation.errors
    assert "acceptance_count=2, actual=1" in validation.errors[0].message
