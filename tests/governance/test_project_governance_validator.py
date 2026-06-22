from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = ROOT / "scripts" / "validate_project_governance.py"
STOP_HOOK = ROOT / ".codex" / "hooks" / "governance_stop.py"


def load_validator_module():
    spec = importlib.util.spec_from_file_location("validate_project_governance", VALIDATOR)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def load_sync_module():
    scripts_dir = str(ROOT / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    spec = importlib.util.spec_from_file_location("validate_governance_sync", ROOT / "scripts" / "validate_governance_sync.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def load_semantic_module():
    scripts_dir = str(ROOT / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    spec = importlib.util.spec_from_file_location("validate_semantic_extractors", ROOT / "scripts" / "validate_semantic_extractors.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def load_dashboard_module():
    scripts_dir = str(ROOT / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    spec = importlib.util.spec_from_file_location(
        "generate_governance_dashboard", ROOT / "scripts" / "generate_governance_dashboard.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def load_setup_doctor_module():
    spec = importlib.util.spec_from_file_location("governance_setup_doctor", ROOT / "scripts" / "governance_setup_doctor.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def load_information_quality_module():
    scripts_dir = str(ROOT / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    spec = importlib.util.spec_from_file_location(
        "validate_information_quality", ROOT / "scripts" / "validate_information_quality.py"
    )
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

    def test_review3_root_governance_framework_files_are_required(self) -> None:
        validator = load_validator_module()
        config = validator.load_yaml(ROOT / "governance" / "projects.yaml")
        required = set(config["root_governance"]["required_files"])
        for path in {
            "AGENTS.md",
            "docs/governance/STANDARD.md",
            "docs/governance/CODEX_SETUP.md",
            "docs/governance/templates/OWNER_STATUS.template.md",
            ".agents/skills/codex-dex/SKILL.md",
            ".codex/config.template.toml",
            ".codex/hooks.json",
            ".codex/hooks/governance_stop.py",
            ".github/workflows/project-governance.yml",
            "scripts/validate_project_governance.py",
            "scripts/validate_governance_sync.py",
            "scripts/validate_semantic_extractors.py",
            "scripts/validate_ci_attestation.py",
            "scripts/governance_setup_doctor.py",
            "governance/schemas/ci_attestation.schema.json",
        }:
            self.assertIn(path, required)
            self.assertTrue((ROOT / path).is_file(), path)

    def test_review6d_all_registered_projects_declare_semantic_coverage(self) -> None:
        validator = load_validator_module()
        config = validator.load_yaml(ROOT / "governance" / "projects.yaml")
        projects = [project for project in validator.as_list(config.get("projects")) if isinstance(project, dict)]
        self.assertGreaterEqual(len(projects), 9)
        for project in projects:
            coverage = project.get("semantic_coverage")
            self.assertIsInstance(coverage, dict, project.get("project_id"))
            self.assertIn(
                coverage.get("status"),
                validator.SEMANTIC_COVERAGE_STATES,
                project.get("project_id"),
            )

    def test_review6d_alpha_semantic_rollout_is_task_bound(self) -> None:
        validator = load_validator_module()
        config = validator.load_yaml(ROOT / "governance" / "projects.yaml")
        alpha = next(project for project in config["projects"] if project["project_id"] == "Alpha")
        self.assertTrue(alpha.get("semantic_extractors"))
        coverage = alpha["semantic_coverage"]
        self.assertEqual(coverage["status"], "in_progress")
        self.assertEqual(coverage["task_id"], "GOV-SEMANTIC-ALPHA-001")
        self.assertEqual(coverage["acceptance_id"], "ACC-SEMANTIC-ALPHA-001")
        self.assertEqual(
            coverage["evidence_ref"],
            "governance/run_manifests/GOV-SEMANTIC-ALPHA-EXTRACT-001.json",
        )

    def test_review6d_whkm_semantic_rollout_is_task_bound(self) -> None:
        validator = load_validator_module()
        config = validator.load_yaml(ROOT / "governance" / "projects.yaml")
        whkm = next(project for project in config["projects"] if project["project_id"] == "whkmSalary")
        self.assertTrue(whkm.get("semantic_extractors"))
        coverage = whkm["semantic_coverage"]
        self.assertEqual(coverage["status"], "in_progress")
        self.assertEqual(coverage["task_id"], "GOV-SEMANTIC-WHKM-001")
        self.assertEqual(coverage["acceptance_id"], "ACC-SEMANTIC-WHKM-001")
        self.assertEqual(
            coverage["evidence_ref"],
            "governance/run_manifests/GOV-SEMANTIC-WHKM-EXTRACT-001.json",
        )

    def test_review6d_openai_database_semantic_rollout_is_task_bound(self) -> None:
        validator = load_validator_module()
        config = validator.load_yaml(ROOT / "governance" / "projects.yaml")
        openai_database = next(project for project in config["projects"] if project["project_id"] == "OpenAIDatabase")
        self.assertTrue(openai_database.get("semantic_extractors"))
        coverage = openai_database["semantic_coverage"]
        self.assertEqual(coverage["status"], "in_progress")
        self.assertEqual(coverage["task_id"], "GOV-SEMANTIC-OAIDB-001")
        self.assertEqual(coverage["acceptance_id"], "ACC-SEMANTIC-OAIDB-001")
        self.assertEqual(
            coverage["evidence_ref"],
            "governance/run_manifests/GOV-SEMANTIC-OAIDB-EXTRACT-001.json",
        )

    def test_review6d_opme_semantic_rollout_is_task_bound(self) -> None:
        validator = load_validator_module()
        config = validator.load_yaml(ROOT / "governance" / "projects.yaml")
        opme = next(project for project in config["projects"] if project["project_id"] == "OpMe_System")
        self.assertTrue(opme.get("semantic_extractors"))
        coverage = opme["semantic_coverage"]
        self.assertEqual(coverage["status"], "in_progress")
        self.assertEqual(coverage["task_id"], "GOV-SEMANTIC-OPME-001")
        self.assertEqual(coverage["acceptance_id"], "ACC-SEMANTIC-OPME-001")
        self.assertEqual(
            coverage["evidence_ref"],
            "governance/run_manifests/GOV-SEMANTIC-OPME-EXTRACT-001.json",
        )

    def test_review6d_fifa_semantic_rollout_is_task_bound(self) -> None:
        validator = load_validator_module()
        config = validator.load_yaml(ROOT / "governance" / "projects.yaml")
        fifa = next(project for project in config["projects"] if project["project_id"] == "FIFA")
        self.assertTrue(fifa.get("semantic_extractors"))
        coverage = fifa["semantic_coverage"]
        self.assertEqual(coverage["status"], "in_progress")
        self.assertEqual(coverage["task_id"], "GOV-SEMANTIC-FIFA-001")
        self.assertEqual(coverage["acceptance_id"], "ACC-SEMANTIC-FIFA-001")
        self.assertEqual(
            coverage["evidence_ref"],
            "governance/run_manifests/GOV-SEMANTIC-FIFA-EXTRACT-001.json",
        )

    def test_review6d_required_project_missing_semantic_coverage_fails(self) -> None:
        validator = load_validator_module()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            (tmp_path / "P").mkdir()
            config = {
                "root_governance": {"ci_mode": "required", "required_files": []},
                "projects": [{"project_id": "P", "path": "P", "ci_mode": "required"}],
            }
            with patch.object(validator, "ROOT", tmp_path), patch.object(validator, "discover_project_dirs", return_value=["P"]):
                validation = validator.Validation()
                validator.validate_root(validation, config)
        self.assertTrue(any("semantic_coverage" in issue.message for issue in validation.errors), validation.errors)

    def test_review6d_machine_verified_requires_semantic_extractors(self) -> None:
        validator = load_validator_module()
        project = {
            "project_id": "P",
            "path": "P",
            "ci_mode": "required",
            "semantic_coverage": {
                "status": "machine_verified",
                "task_id": "GOV-SEMANTIC-P-001",
                "acceptance_id": "ACC-SEMANTIC-P-001",
                "target": "Machine-check active facts.",
                "owner": "project owner",
                "rationale": "test",
                "evidence_ref": "governance/run_manifests/example.json",
            },
        }
        validation = validator.Validation()
        validator.validate_semantic_coverage_config(validation, project, True, "P")
        self.assertTrue(any("semantic_extractors" in issue.message for issue in validation.errors), validation.errors)

    def test_review6d_semantic_extractors_may_be_in_progress(self) -> None:
        validator = load_validator_module()
        project = {
            "project_id": "P",
            "path": "P",
            "ci_mode": "required",
            "semantic_extractors": True,
            "semantic_coverage": {
                "status": "in_progress",
                "task_id": "GOV-SEMANTIC-P-001",
                "acceptance_id": "ACC-SEMANTIC-P-001",
                "target": "Partially machine-check active facts.",
                "owner": "project owner",
                "rationale": "test",
                "evidence_ref": "governance/run_manifests/example.json",
            },
        }
        validation = validator.Validation()
        validator.validate_semantic_coverage_config(validation, project, True, "P")
        self.assertFalse(validation.errors)

    def test_review6e_semantic_coverage_task_must_exist_in_project_tasks(self) -> None:
        validator = load_validator_module()
        project = {
            "project_id": "P",
            "path": "P",
            "ci_mode": "required",
            "semantic_coverage": {
                "status": "planned",
                "task_id": "GOV-SEMANTIC-P-001",
                "acceptance_id": "ACC-SEMANTIC-P-001",
                "target": "Add semantic extractors.",
                "owner": "project owner",
                "rationale": "test",
            },
        }
        validation = validator.Validation()
        validator.check_semantic_coverage_task_binding(validation, project, {"tasks": []}, True, "P")
        self.assertTrue(any("task_id not found" in issue.message for issue in validation.errors), validation.errors)

    def test_review6e_semantic_coverage_acceptance_must_bind_to_task(self) -> None:
        validator = load_validator_module()
        project = {
            "project_id": "P",
            "path": "P",
            "ci_mode": "required",
            "semantic_coverage": {
                "status": "planned",
                "task_id": "GOV-SEMANTIC-P-001",
                "acceptance_id": "ACC-SEMANTIC-P-001",
                "target": "Add semantic extractors.",
                "owner": "project owner",
                "rationale": "test",
            },
        }
        parsed = {"tasks": [{"task_id": "GOV-SEMANTIC-P-001", "status": "planned", "acceptance_ids": ["ACC-OTHER"]}]}
        validation = validator.Validation()
        validator.check_semantic_coverage_task_binding(validation, project, parsed, True, "P")
        self.assertTrue(any("acceptance_id ACC-SEMANTIC-P-001" in issue.message for issue in validation.errors), validation.errors)

    def test_review6e_machine_verified_semantic_coverage_requires_completed_task(self) -> None:
        validator = load_validator_module()
        project = {
            "project_id": "P",
            "path": "P",
            "ci_mode": "required",
            "semantic_extractors": True,
            "semantic_coverage": {
                "status": "machine_verified",
                "task_id": "GOV-SEMANTIC-P-001",
                "acceptance_id": "ACC-SEMANTIC-P-001",
                "target": "Add semantic extractors.",
                "owner": "project owner",
                "rationale": "test",
                "evidence_ref": "governance/run_manifests/example.json",
            },
        }
        parsed = {"tasks": [{"task_id": "GOV-SEMANTIC-P-001", "status": "planned", "acceptance_ids": ["ACC-SEMANTIC-P-001"]}]}
        validation = validator.Validation()
        validator.check_semantic_coverage_task_binding(validation, project, parsed, True, "P")
        self.assertTrue(any("requires task GOV-SEMANTIC-P-001 to be completed" in issue.message for issue in validation.errors), validation.errors)

    def test_unknown_project_returns_nonzero(self) -> None:
        result = run_validator("--project", "__missing_project__")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Unknown project: __missing_project__", result.stdout)

    def test_governance_stop_hook_blocks_enabled_repo_without_validator(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            subprocess.run(["git", "init"], cwd=tmp_path, stdout=subprocess.PIPE, check=True)
            (tmp_path / "governance").mkdir()
            (tmp_path / "governance" / "projects.yaml").write_text(
                "governance_spec_version: '1.0.0'\n",
                encoding="utf-8",
            )
            result = subprocess.run(
                [sys.executable, str(STOP_HOOK)],
                input=json.dumps({"cwd": str(tmp_path)}),
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload.get("decision"), "block")
        self.assertIn("required governance scripts are missing", payload.get("reason", ""))
        self.assertIn("validate_project_governance.py", payload.get("reason", ""))

    def test_governance_stop_hook_rechecks_recursive_stop_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            subprocess.run(["git", "init"], cwd=tmp_path, stdout=subprocess.PIPE, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True)
            subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, check=True)
            (tmp_path / "governance").mkdir()
            (tmp_path / "governance" / "projects.yaml").write_text("governance_spec_version: '1.0.0'\n", encoding="utf-8")
            scripts = tmp_path / "scripts"
            scripts.mkdir()
            validator = scripts / "validate_project_governance.py"
            validator.write_text("import sys\nprint('still failing')\nsys.exit(1)\n", encoding="utf-8")
            quality = scripts / "validate_information_quality.py"
            quality.write_text("import sys\nprint('still failing')\nsys.exit(1)\n", encoding="utf-8")
            generator = scripts / "generate_governance_dashboard.py"
            generator.write_text("import sys\nprint('generated')\nsys.exit(0)\n", encoding="utf-8")
            setup_doctor = scripts / "governance_setup_doctor.py"
            setup_doctor.write_text("import sys\nprint('{\"status\":\"PASS\"}')\nsys.exit(0)\n", encoding="utf-8")
            subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
            subprocess.run(["git", "commit", "-m", "init"], cwd=tmp_path, stdout=subprocess.PIPE, check=True)
            result = subprocess.run(
                [sys.executable, str(STOP_HOOK)],
                input=json.dumps({"cwd": str(tmp_path), "stop_hook_active": True}),
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload.get("decision"), "block")
        self.assertIn("recursive Stop pass", payload.get("reason", ""))

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

    def test_review5_model_behavior_change_requires_governance_bundle(self) -> None:
        sync = load_sync_module()
        project = {
            "project_id": "Serenity-Alipay",
            "path": "Serenity-Alipay",
            "model_behavior_globs": ["app/**/*.py", "tests/**/*.py"],
        }
        changes, _ = sync.classify_changes({"projects": [project]}, ["Serenity-Alipay/app/core/scoring.py"])
        validation = sync.SyncValidation()
        sync.validate_diff_contract(validation, changes)
        self.assertTrue(validation.errors)
        self.assertIn("MODEL_SPEC.md", validation.errors[0].message)

    def test_review5_config_active_value_change_requires_parameter_registry(self) -> None:
        sync = load_sync_module()
        project = {"project_id": "P", "path": "P", "model_behavior_globs": []}
        changes, _ = sync.classify_changes({"projects": [project]}, ["P/config/settings.yaml"])
        validation = sync.SyncValidation()
        sync.validate_diff_contract(validation, changes)
        self.assertTrue(validation.errors)
        self.assertIn("parameter_registry.csv", validation.errors[0].message)

    def test_review5_development_events_are_append_only(self) -> None:
        sync = load_sync_module()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            event_file = tmp_path / "P" / "docs" / "governance" / "development_events.jsonl"
            event_file.parent.mkdir(parents=True)
            event_file.write_text('{"event_id":"E2"}\n', encoding="utf-8")
            with patch.object(sync, "ROOT", tmp_path), patch.object(sync, "base_file_text", return_value='{"event_id":"E1"}\n'):
                validation = sync.SyncValidation()
                sync.validate_append_only(validation, ["P/docs/governance/development_events.jsonl"], "BASE")
        self.assertTrue(validation.errors)
        self.assertIn("append-only", validation.errors[0].message)

    def test_review5_event_files_changed_must_cover_actual_diff(self) -> None:
        sync = load_sync_module()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            event_file = tmp_path / "P" / "docs" / "governance" / "development_events.jsonl"
            event_file.parent.mkdir(parents=True)
            event_file.write_text(
                json.dumps({"event_id": "E1", "files_changed": ["P/docs/governance/development_events.jsonl"]}) + "\n",
                encoding="utf-8",
            )
            project = {"project_id": "P", "path": "P"}
            change = sync.ProjectChange(
                project=project,
                files=["P/app/scoring.py", "P/docs/governance/development_events.jsonl"],
                updated_governance_files={"docs/governance/development_events.jsonl"},
            )
            with patch.object(sync, "ROOT", tmp_path):
                validation = sync.SyncValidation()
                sync.validate_event_files_changed(validation, [change])
        self.assertTrue(validation.errors)
        self.assertIn("files_changed does not cover", validation.errors[0].message)

    def test_review5_root_governance_change_requires_sync_markers(self) -> None:
        sync = load_sync_module()
        changed = ["governance/projects.yaml", "GOVERNANCE_DASHBOARD.md"]
        validation = sync.SyncValidation()

        sync.root_sync_requirements(validation, ["governance/projects.yaml"], changed)

        messages = [issue.message for issue in validation.issues]
        self.assertIn("Root governance change requires updated run_manifest", messages)
        self.assertIn("Root governance change requires updated governance_tests", messages)

        covered = [
            *changed,
            "governance/run_manifests/ADP-PHASE1-FOUNDATION-20260621.json",
            "tests/governance/test_project_governance_validator.py",
        ]
        validation = sync.SyncValidation()
        sync.root_sync_requirements(validation, ["governance/projects.yaml"], covered)
        self.assertFalse(validation.errors)

    def test_review5_version_matrix_current_iteration_mismatch_fails(self) -> None:
        sync = load_sync_module()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            docs = tmp_path / "P" / "docs" / "governance"
            docs.mkdir(parents=True)
            (docs / "VERSION_MATRIX.yaml").write_text("current_iteration: ITER-OLD\n", encoding="utf-8")
            (docs / "development_events.jsonl").write_text(
                json.dumps({"event_id": "E1", "iteration_id": "ITER-NEW", "fact_level": "EXTRACTED"}) + "\n",
                encoding="utf-8",
            )
            with patch.object(sync, "ROOT", tmp_path), patch.object(sync.structural, "ROOT", tmp_path):
                validation = sync.SyncValidation()
                sync.validate_semantic_project(validation, {"project_id": "P", "path": "P"})
        self.assertTrue(validation.errors)
        self.assertIn("current_iteration", validation.errors[0].message)

    def test_review5_missing_code_ref_fails_semantic_check(self) -> None:
        sync = load_sync_module()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            docs = tmp_path / "P" / "docs" / "governance"
            docs.mkdir(parents=True)
            (docs / "model_registry.yaml").write_text(
                "models:\n  - model_id: MOD-001\n    code_refs: missing.py\n",
                encoding="utf-8",
            )
            with patch.object(sync, "ROOT", tmp_path), patch.object(sync.structural, "ROOT", tmp_path):
                validation = sync.SyncValidation()
                sync.validate_semantic_project(validation, {"project_id": "P", "path": "P"})
        self.assertTrue(validation.errors)
        self.assertIn("missing path", validation.errors[0].message)

    def test_review5_parameter_value_mismatch_has_detection_surface(self) -> None:
        sync = load_sync_module()
        project = {"project_id": "P", "path": "P", "model_behavior_globs": []}
        changes, _ = sync.classify_changes({"projects": [project]}, ["P/config/parameters.yaml"])
        validation = sync.SyncValidation()
        sync.validate_diff_contract(validation, changes)
        self.assertTrue(validation.errors)
        self.assertIn("parameter_registry.csv", validation.errors[0].message)

    def test_review5_completed_task_requires_same_run_evidence_surface(self) -> None:
        sync = load_sync_module()
        project = {"project_id": "P", "path": "P", "model_behavior_globs": []}
        changes, _ = sync.classify_changes({"projects": [project]}, ["P/tests/test_acceptance.py"])
        validation = sync.SyncValidation()
        sync.validate_diff_contract(validation, changes)
        self.assertTrue(validation.errors)
        self.assertIn("delivery_tasks.yaml", validation.errors[0].message)

    def test_review5_legal_behavior_change_bundle_passes_diff_contract(self) -> None:
        sync = load_sync_module()
        project = {"project_id": "P", "path": "P", "model_behavior_globs": ["app/**/*.py"]}
        files = [
            "P/app/scoring.py",
            "P/docs/governance/MODEL_SPEC.md",
            "P/docs/governance/model_registry.yaml",
            "P/docs/governance/formula_registry.yaml",
            "P/docs/governance/parameter_registry.csv",
            "P/docs/governance/DEVELOPMENT_LEDGER.md",
            "P/docs/governance/development_events.jsonl",
            "P/docs/governance/delivery_tasks.yaml",
            "P/docs/governance/TRACEABILITY_MATRIX.csv",
            "P/docs/governance/VERSION_MATRIX.yaml",
            "P/docs/governance/STATUS.md",
            "P/docs/governance/OWNER_STATUS.md",
            "P/CHANGELOG.md",
        ]
        changes, _ = sync.classify_changes({"projects": [project]}, files)
        validation = sync.SyncValidation()
        sync.validate_diff_contract(validation, changes)
        self.assertFalse(validation.errors)

    def test_review5_trivial_markdown_change_does_not_require_model_version(self) -> None:
        sync = load_sync_module()
        project = {"project_id": "P", "path": "P", "model_behavior_globs": []}
        changes, _ = sync.classify_changes({"projects": [project]}, ["P/notes.md"])
        validation = sync.SyncValidation()
        sync.validate_diff_contract(validation, changes)
        self.assertFalse(validation.errors)

    def test_review5_generated_release_artifacts_do_not_require_parameter_bundle(self) -> None:
        sync = load_sync_module()
        project = {"project_id": "P", "path": "P", "model_behavior_globs": []}
        files = [
            "P/CHECKSUMS.sha256",
            "P/DIRECTORY_TREE.txt",
            "P/manifest.txt",
            "P/artifacts/release_evidence_t1211.json",
            "P/artifacts/release_operation_log_t1211.jsonl",
            "P/artifacts/tests/a200/t1215_clean_room_release.json",
            "P/artifacts/tests/a200/Enterprise_Ecosystem_Intelligence_clean_room_t1215.zip",
        ]
        changes, _ = sync.classify_changes({"projects": [project]}, files)
        validation = sync.SyncValidation()
        sync.validate_diff_contract(validation, changes)
        self.assertFalse(validation.errors)
        self.assertEqual(changes[0].classifications, {"generated_artifact_change"})

    def test_review6_root_governance_change_does_not_require_dashboard_diff(self) -> None:
        sync = load_sync_module()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            (tmp_path / "GOVERNANCE_DASHBOARD.md").write_text("# Dashboard\n", encoding="utf-8")
            with patch.object(sync, "ROOT", tmp_path):
                validation = sync.SyncValidation()
                sync.root_sync_requirements(
                    validation,
                    ["scripts/validate_governance_sync.py"],
                    [
                        "scripts/validate_governance_sync.py",
                        "governance/run_manifests/GOV-TEST.json",
                        "tests/governance/test_project_governance_validator.py",
                    ],
                )
        self.assertFalse(validation.errors)

    def test_review6_explicit_missing_base_ref_fails_enforced_sync(self) -> None:
        sync = load_sync_module()
        with patch.object(sync, "load_projects", return_value={"projects": []}), patch.object(sync, "git_ref_exists", return_value=False):
            exit_code, _ = sync.validate(changed_only=True, enforce_sync=True, base_ref="missing-base")
        self.assertEqual(exit_code, 1)

    def test_review6_stale_pending_manifest_requires_ci_attestation(self) -> None:
        sync = load_sync_module()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            manifests = tmp_path / "governance" / "run_manifests"
            attestations = tmp_path / "governance" / "ci_attestations"
            manifests.mkdir(parents=True)
            attestations.mkdir(parents=True)
            old = (datetime.now(timezone.utc) - timedelta(days=3)).isoformat()
            (manifests / "GOV-OLD.json").write_text(
                json.dumps({"run_id": "GOV-OLD", "started_at": old, "finished_at": "PENDING_CI"}) + "\n",
                encoding="utf-8",
            )
            with patch.object(sync, "ROOT", tmp_path), patch.object(sync, "RUN_MANIFESTS_DIR", manifests), patch.object(sync, "CI_ATTESTATIONS_DIR", attestations):
                validation = sync.SyncValidation()
                sync.validate_pending_ci_bindings(validation)
        self.assertTrue(validation.errors)
        self.assertIn("PENDING_CI", validation.errors[0].message)

    def test_review6_success_attestation_clears_pending_manifest(self) -> None:
        sync = load_sync_module()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            manifests = tmp_path / "governance" / "run_manifests"
            attestations = tmp_path / "governance" / "ci_attestations"
            manifests.mkdir(parents=True)
            attestations.mkdir(parents=True)
            old = (datetime.now(timezone.utc) - timedelta(days=3)).isoformat()
            (manifests / "GOV-OLD.json").write_text(
                json.dumps({"run_id": "GOV-OLD", "started_at": old, "finished_at": "PENDING_CI"}) + "\n",
                encoding="utf-8",
            )
            (attestations / "GOV-OLD.json").write_text(
                json.dumps({"binds_run_manifest": "GOV-OLD", "conclusion": "success"}) + "\n",
                encoding="utf-8",
            )
            with patch.object(sync, "ROOT", tmp_path), patch.object(sync, "RUN_MANIFESTS_DIR", manifests), patch.object(sync, "CI_ATTESTATIONS_DIR", attestations):
                validation = sync.SyncValidation()
                sync.validate_pending_ci_bindings(validation)
                self.assertFalse(validation.errors)

    def test_review6_project_governance_workflow_uploads_ci_attestation_artifact(self) -> None:
        workflow = (ROOT / ".github" / "workflows" / "project-governance.yml").read_text(encoding="utf-8")
        self.assertIn("scripts/validate_ci_attestation.py write", workflow)
        self.assertIn("scripts/validate_ci_attestation.py validate", workflow)
        self.assertIn("actions/upload-artifact@v4", workflow)
        self.assertIn("project-governance-ci-attestation-${{ github.run_id }}-${{ github.run_attempt }}", workflow)
        self.assertIn("if-no-files-found: error", workflow)
        self.assertIn("scripts/governance_setup_doctor.py --json --check-github", workflow)

    def test_review6_setup_doctor_reports_entry_gate_contract(self) -> None:
        doctor = load_setup_doctor_module()
        report = doctor.workflow_entry_gate_status()
        self.assertEqual(report["status"], "PASS", report)
        checks = report["checks"]
        for check_name in {
            "pull_request_changed_only_enforce_sync_semantic",
            "main_push_changed_only_uses_event_before",
            "main_push_runs_all_semantic_drift_report",
            "manual_changed_only_accepts_base_ref",
            "manual_project_scope_requires_project",
            "ci_attestation_validated",
            "ci_attestation_uploaded_as_artifact",
            "setup_doctor_runs_in_ci",
            "required_failures_not_masked",
        }:
            self.assertTrue(checks[check_name], check_name)

    def test_review7_stop_hook_runs_full_closure_contract(self) -> None:
        text = STOP_HOOK.read_text(encoding="utf-8")
        for marker in {
            "generate_governance_dashboard.py",
            "--changed-only",
            "--enforce-sync",
            "--semantic",
            "validate_information_quality.py",
            "--all",
            "--drift-report",
            "governance_setup_doctor.py",
            "governance/binding_backlog.yaml",
            "ASSURANCE_STATUS.yaml",
        }:
            self.assertIn(marker, text)
        self.assertIn("This is a recursive Stop pass, but governance is still rechecked.", text)

    def test_review7_setup_doctor_reports_missing_hooks_unverified(self) -> None:
        doctor = load_setup_doctor_module()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            with patch.object(doctor, "ROOT", tmp_path):
                status = doctor.hook_status()
        self.assertEqual(status["hooks_enabled"], "UNVERIFIED")
        self.assertEqual(status["stop_hook_loaded"], "UNVERIFIED")
        self.assertEqual(status["repository_trusted"], "UNVERIFIED")

    def test_review7_v2_manifest_requires_content_tree_hash(self) -> None:
        sync = load_sync_module()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            manifests = tmp_path / "governance" / "run_manifests"
            manifests.mkdir(parents=True)
            manifest = {
                "schema_version": 2,
                "run_id": "GOV-REVIEW7-TEST",
                "project_id": "root",
                "task_id": "GOV-REVIEW7-TEST",
                "acceptance_ids": ["ACC-REVIEW7-TEST"],
                "iteration_id": "ITER-20260622-001",
                "generated_at": "2026-06-22T00:00:00Z",
                "implementation_base_sha": "a" * 40,
                "content_tree_hash": "PENDING",
                "changed_files_declared": ["README.md"],
                "changed_files_actual": ["README.md", "governance/run_manifests/GOV-REVIEW7-TEST.json"],
                "required_governance_files": ["README.md"],
                "updated_governance_files": ["README.md"],
                "test_commands": ["python3 scripts/validate_project_governance.py --all"],
                "test_results": [{"command": "python3 scripts/validate_project_governance.py --all", "exit_code": 0}],
                "evidence_refs": ["governance/run_manifests/GOV-REVIEW7-TEST.json"],
                "binding_status": "PRECOMMIT_TREE_BOUND",
                "ci_attestation_subject": "Project Governance workflow",
                "ci_run_reference": "PRECOMMIT_PENDING_CI_ATTESTATION",
            }
            (manifests / "GOV-REVIEW7-TEST.json").write_text(json.dumps(manifest) + "\n", encoding="utf-8")
            with patch.object(sync, "ROOT", tmp_path), patch.object(sync, "RUN_MANIFESTS_DIR", manifests):
                validation = sync.SyncValidation()
                sync.validate_run_manifests(validation, ["governance/run_manifests/GOV-REVIEW7-TEST.json"])
        self.assertTrue(any("lacks content_tree_hash" in issue.message for issue in validation.errors), validation.errors)

    def test_review7_v2_manifest_changed_files_actual_must_cover_diff(self) -> None:
        sync = load_sync_module()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            manifests = tmp_path / "governance" / "run_manifests"
            manifests.mkdir(parents=True)
            manifest = {
                "schema_version": 2,
                "run_id": "GOV-REVIEW7-TEST",
                "project_id": "root",
                "task_id": "GOV-REVIEW7-TEST",
                "acceptance_ids": ["ACC-REVIEW7-TEST"],
                "iteration_id": "ITER-20260622-001",
                "generated_at": "2026-06-22T00:00:00Z",
                "implementation_base_sha": "a" * 40,
                "content_tree_hash": "sha256:abcd",
                "changed_files_declared": ["README.md"],
                "changed_files_actual": ["governance/run_manifests/GOV-REVIEW7-TEST.json"],
                "required_governance_files": ["README.md"],
                "updated_governance_files": ["README.md"],
                "test_commands": ["python3 scripts/validate_project_governance.py --all"],
                "test_results": [{"command": "python3 scripts/validate_project_governance.py --all", "exit_code": 0}],
                "evidence_refs": ["governance/run_manifests/GOV-REVIEW7-TEST.json"],
                "binding_status": "PRECOMMIT_TREE_BOUND",
                "ci_attestation_subject": "Project Governance workflow",
                "ci_run_reference": "PRECOMMIT_PENDING_CI_ATTESTATION",
            }
            (manifests / "GOV-REVIEW7-TEST.json").write_text(json.dumps(manifest) + "\n", encoding="utf-8")
            changed = ["README.md", "governance/run_manifests/GOV-REVIEW7-TEST.json"]
            with patch.object(sync, "ROOT", tmp_path), patch.object(sync, "RUN_MANIFESTS_DIR", manifests):
                validation = sync.SyncValidation()
                sync.validate_run_manifests(validation, changed)
        self.assertTrue(any("changed_files_actual does not cover" in issue.message for issue in validation.errors), validation.errors)

    def test_review7_projects_yaml_stale_count_claim_fails(self) -> None:
        validator = load_validator_module()
        project = {"project_id": "P", "path": "P", "note": "Project currently has 2 active parameters."}
        counts = {
            "models": 1,
            "total_formulas": 1,
            "active_formulas": 1,
            "total_parameters": 1,
            "active_parameters": 1,
            "tasks": 1,
            "events": 1,
        }
        with patch.object(validator, "project_registry_counts", return_value=counts):
            validation = validator.Validation()
            validator.validate_projects_yaml_count_claims(validation, [project])
        self.assertTrue(any("declares 2 active_parameters" in issue.message for issue in validation.errors), validation.errors)

    def test_review7_readme_project_registry_drift_fails(self) -> None:
        validator = load_validator_module()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            (tmp_path / "README.md").write_text("| Project | Path |\n|---|---|\n| `A` | `A` |\n", encoding="utf-8")
            with patch.object(validator, "ROOT", tmp_path):
                validation = validator.Validation()
                validator.validate_readme_project_list(validation, [{"project_id": "A"}, {"project_id": "B"}])
        self.assertTrue(any("README project list drift" in issue.message for issue in validation.errors), validation.errors)

    def test_review7_assurance_status_rejects_legacy_machine_verified_status(self) -> None:
        validator = load_validator_module()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            docs = tmp_path / "P" / "docs" / "governance"
            docs.mkdir(parents=True)
            (docs / "ASSURANCE_STATUS.yaml").write_text(
                "\n".join(
                    [
                        "dimensions:",
                        "  structural_completeness:",
                        "    status: VERIFIED",
                        "  implementation_congruence:",
                        "    status: machine_verified",
                        "    total_active_parameters: 0",
                        "    total_active_formulas: 0",
                        "  parameter_source_quality:",
                        "    status: VERIFIED",
                        "  empirical_validation:",
                        "    status: VERIFIED",
                        "  operational_validation:",
                        "    status: VERIFIED",
                        "  delivery_evidence:",
                        "    status: VERIFIED",
                        "  evidence_freshness:",
                        "    status: VERIFIED",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            counts = {
                "models": 0,
                "total_formulas": 0,
                "active_formulas": 0,
                "total_parameters": 0,
                "active_parameters": 0,
                "tasks": 0,
                "events": 0,
            }
            with patch.object(validator, "ROOT", tmp_path), patch.object(validator, "project_registry_counts", return_value=counts):
                validation = validator.Validation()
                validator.validate_assurance_status(validation, {"project_id": "P", "path": "P"})
        self.assertTrue(any("legacy status machine_verified" in issue.message for issue in validation.errors), validation.errors)

    def test_review7_generated_views_reject_checkout_and_bare_pending(self) -> None:
        quality = load_information_quality_module()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            (tmp_path / "README.md").write_text(
                "source_base_commit\nsource_snapshot_hash\ngenerator_version\nPENDING\n",
                encoding="utf-8",
            )
            with patch.object(quality, "ROOT", tmp_path):
                gate = quality.Gate()
                quality.check_generated_views(gate, [])
        self.assertTrue(any(item.code == "BARE_PENDING" for item in gate.errors), gate.errors)

    def test_review7_binding_backlog_preserves_legacy_unbound_events(self) -> None:
        dashboard = load_dashboard_module()
        meta = {
            "source_base_commit": "a" * 40,
            "source_tree_hash": "b" * 40,
            "source_snapshot_hash": "sha256:" + "c" * 64,
        }
        rendered = dashboard.render_binding_backlog(
            [
                {
                    "project_id": "P",
                    "event_binding_counts": {
                        "tree_bound_events": 0,
                        "commit_bound_events": 0,
                        "legacy_unbound_events": 2,
                        "precommit_pending_events": 0,
                    },
                }
            ],
            meta,
        )
        self.assertIn("legacy_unbound_events: 2", rendered)
        self.assertIn("GOV-REVIEW7-BINDING-BACKLOG-001", rendered)

    def test_review6_serenity_semantic_extractors_pass_current_registry(self) -> None:
        semantic = load_semantic_module()
        issues, summary = semantic.validate_project_semantics(ROOT / "Serenity-Alipay", "Serenity-Alipay")
        self.assertFalse([issue for issue in issues if issue.level == "ERROR"], issues)
        self.assertEqual(summary["semantic_parameters_checked"], 49)
        self.assertEqual(summary["semantic_formulas_checked"], 12)

    def test_review6_parameter_active_value_mismatch_fails(self) -> None:
        semantic = load_semantic_module()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            project = tmp_path / "P"
            docs = project / "docs" / "governance"
            docs.mkdir(parents=True)
            (project / "impl.py").write_text(
                "from dataclasses import dataclass\n\n@dataclass(frozen=True)\nclass Settings:\n    threshold: float = 0.45\n",
                encoding="utf-8",
            )
            selector = "python_ast_attr:P/impl.py::Settings.threshold"
            expected_hash = semantic.parameter_evidence_hash("PARAM-X", selector, 0.45)
            (docs / "parameter_registry.csv").write_text(
                "\n".join(
                    [
                        "parameter_id,model_id,formula_id,symbol,name,category,data_type,unit,default_value,initial_or_prior_value,active_value,weight,weight_group,weight_group_target,weight_group_tolerance,min_value,max_value,formula_or_transform,source_or_rationale,calibration_method,sensitivity,code_ref,config_ref,test_ref,status,fact_level,unknown_task_ids,parameter_version,last_updated,source_selector,extracted_value,last_verified_commit,verified_at,evidence_hash",
                        f"PARAM-X,MOD-X,FORM-X,THRESHOLD,Threshold,threshold,float,ratio,0.45,0.45,0.40,NOT_APPLICABLE,,,,0,1,identity,test,test,medium,P/impl.py,P/impl.py,P/test_impl.py,active,EXTRACTED,,v1,2026-06-21,{selector},0.45,HEAD,2026-06-21T00:00:00Z,{expected_hash}",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            with patch.object(semantic, "ROOT", tmp_path), patch.object(semantic, "git_ref_exists", return_value=True):
                issues, _ = semantic.validate_project_semantics(project, "P")
        self.assertTrue(any("active_value='0.40'" in issue.message for issue in issues), issues)

    def test_review6_csv_cell_selector_checks_active_value(self) -> None:
        semantic = load_semantic_module()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            project = tmp_path / "P"
            docs = project / "docs" / "governance"
            docs.mkdir(parents=True)
            (project / "catalog.csv").write_text("parameter_key,default_value\nthreshold,0.45\n", encoding="utf-8")
            selector = "csv_cell:P/catalog.csv::parameter_key=threshold::default_value"
            expected_hash = semantic.parameter_evidence_hash("PARAM-X", selector, "0.45")
            (docs / "parameter_registry.csv").write_text(
                "\n".join(
                    [
                        "parameter_id,model_id,formula_id,symbol,name,category,data_type,unit,default_value,initial_or_prior_value,active_value,weight,weight_group,weight_group_target,weight_group_tolerance,min_value,max_value,formula_or_transform,source_or_rationale,calibration_method,sensitivity,code_ref,config_ref,test_ref,status,fact_level,unknown_task_ids,parameter_version,last_updated,source_selector,extracted_value,last_verified_commit,verified_at,evidence_hash",
                        f"PARAM-X,MOD-X,FORM-X,threshold,Threshold,threshold,float,ratio,0.45,0.45,0.45,NOT_APPLICABLE,,,,0,1,identity,test,test,medium,P/catalog.csv,P/catalog.csv,P/test_impl.py,active,EXTRACTED,,v1,2026-06-21,{selector},0.45,HEAD,2026-06-21T00:00:00Z,{expected_hash}",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            with patch.object(semantic, "ROOT", tmp_path), patch.object(semantic, "git_ref_exists", return_value=True):
                issues, summary = semantic.validate_project_semantics(project, "P")
        self.assertFalse([issue for issue in issues if issue.level == "ERROR"], issues)
        self.assertEqual(summary["semantic_parameters_checked"], 1)

    def test_review6_method_default_selector_checks_active_value(self) -> None:
        semantic = load_semantic_module()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            project = tmp_path / "P"
            docs = project / "docs" / "governance"
            docs.mkdir(parents=True)
            (project / "impl.py").write_text(
                "class Strategy:\n    def __init__(self, *, short_window: int = 20):\n        self.short_window = short_window\n",
                encoding="utf-8",
            )
            selector = "python_ast_method_default:P/impl.py::Strategy.__init__.short_window"
            expected_hash = semantic.parameter_evidence_hash("PARAM-X", selector, 20)
            (docs / "parameter_registry.csv").write_text(
                "\n".join(
                    [
                        "parameter_id,model_id,formula_id,symbol,name,category,data_type,unit,default_value,initial_or_prior_value,active_value,weight,weight_group,weight_group_target,weight_group_tolerance,min_value,max_value,formula_or_transform,source_or_rationale,calibration_method,sensitivity,code_ref,config_ref,test_ref,status,fact_level,unknown_task_ids,parameter_version,last_updated,source_selector,extracted_value,last_verified_commit,verified_at,evidence_hash",
                        f"PARAM-X,MOD-X,FORM-X,SHORT_WINDOW,Short window,window,int,periods,20,20,20,NOT_APPLICABLE,,,,1,500,identity,test,test,medium,P/impl.py,P/impl.py,P/test_impl.py,active,EXTRACTED,,v1,2026-06-21,{selector},20,HEAD,2026-06-21T00:00:00Z,{expected_hash}",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            with patch.object(semantic, "ROOT", tmp_path), patch.object(semantic, "git_ref_exists", return_value=True):
                issues, summary = semantic.validate_project_semantics(project, "P")
        self.assertFalse([issue for issue in issues if issue.level == "ERROR"], issues)
        self.assertEqual(summary["semantic_parameters_checked"], 1)

    def test_review6_assignment_selector_checks_set_active_value(self) -> None:
        semantic = load_semantic_module()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            project = tmp_path / "P"
            docs = project / "docs" / "governance"
            docs.mkdir(parents=True)
            (project / "impl.py").write_text('STATUSES = {"pass", "warn", "fail"}\n', encoding="utf-8")
            selector = "python_ast_assignment:P/impl.py::STATUSES"
            expected_hash = semantic.parameter_evidence_hash("PARAM-X", selector, {"pass", "warn", "fail"})
            (docs / "parameter_registry.csv").write_text(
                "\n".join(
                    [
                        "parameter_id,model_id,formula_id,symbol,name,category,data_type,unit,default_value,initial_or_prior_value,active_value,weight,weight_group,weight_group_target,weight_group_tolerance,min_value,max_value,formula_or_transform,source_or_rationale,calibration_method,sensitivity,code_ref,config_ref,test_ref,status,fact_level,unknown_task_ids,parameter_version,last_updated,source_selector,extracted_value,last_verified_commit,verified_at,evidence_hash",
                        f"PARAM-X,MOD-X,FORM-X,STATUSES,Statuses,enum,set,labels,fail|pass|warn,fail|pass|warn,fail|pass|warn,NOT_APPLICABLE,,,,NOT_APPLICABLE,NOT_APPLICABLE,identity,test,test,medium,P/impl.py,P/impl.py,P/test_impl.py,active,EXTRACTED,,v1,2026-06-21,{selector},fail|pass|warn,HEAD,2026-06-21T00:00:00Z,{expected_hash}",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            with patch.object(semantic, "ROOT", tmp_path), patch.object(semantic, "git_ref_exists", return_value=True):
                issues, summary = semantic.validate_project_semantics(project, "P")
        self.assertFalse([issue for issue in issues if issue.level == "ERROR"], issues)
        self.assertEqual(summary["semantic_parameters_checked"], 1)

    def test_review6_collection_key_selectors_extract_without_evaluating_values(self) -> None:
        semantic = load_semantic_module()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            (tmp_path / "P").mkdir()
            (tmp_path / "P" / "impl.py").write_text(
                "\n".join(
                    [
                        "import re",
                        "RULES = {'alpha': re.compile('a'), 'beta': re.compile('b')}",
                        "PAIRS = [('one', re.compile('1')), ('two', re.compile('2'))]",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            (tmp_path / "P" / "config.json").write_text(
                json.dumps(
                    {
                        "sources": [
                            {"id": "memory_atlas", "status": "active"},
                            {"id": "codex", "status": "active"},
                            {"id": "wechat", "status": "planned"},
                        ]
                    }
                ),
                encoding="utf-8",
            )
            with patch.object(semantic, "ROOT", tmp_path):
                self.assertEqual(
                    semantic.extract_selector("python_ast_dict_keys:P/impl.py::RULES|join=;"),
                    "alpha;beta",
                )
                self.assertEqual(
                    semantic.extract_selector("python_ast_sequence_firsts:P/impl.py::PAIRS|join=;"),
                    "one;two",
                )
                self.assertEqual(
                    semantic.extract_selector("json_path_list_field:P/config.json::sources::id|where=status=active|join=;"),
                    "memory_atlas;codex",
                )

    def test_review6_selector_options_can_check_contains_filter_and_order(self) -> None:
        semantic = load_semantic_module()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            (tmp_path / "P").mkdir()
            (tmp_path / "P" / "impl.py").write_text(
                "\n".join(
                    [
                        "FLAGS = {'blocked', 'failed', 'degraded'}",
                        "VARS = ('ADP_RELEASE_TARGET', 'ADP_ALLOW_SMTP_SEND', 'ADP_ALLOW_RELEASE_UPLOAD')",
                        "NAMES = {'.env', 'auth.json'}",
                        "SUFFIXES = frozenset({'.mp4', '.wav'})",
                        "TRANSITIONS = {'created': {'health_checked', 'blocked'}, 'health_checked': {'completed'}}",
                        "SCHEDULES = ({'local_time': '04:45'}, {'local_time': '05:00'})",
                        "TIMEZONE = 'Australia/Sydney'",
                        "def run():",
                        "    step('created')",
                        "    step('completed')",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            (tmp_path / "P" / "policy.txt").write_text(
                "permissions:\n  actions: read\npreflight-production\nRun project tests\n"
                "--default-branch-ref --runner-ref --trial-start-ref\n",
                encoding="utf-8",
            )
            with patch.object(semantic, "ROOT", tmp_path):
                self.assertTrue(semantic.extract_selector("text_file:P/policy.txt|contains=preflight-production"))
                self.assertTrue(semantic.extract_selector("text_file:P/policy.txt|contains_all=permissions,Run project tests"))
                self.assertTrue(semantic.extract_selector("text_file:P/policy.txt|before=preflight-production>>Run project tests"))
                self.assertTrue(semantic.extract_selector("text_file:P/policy.txt|not_contains=auth.json"))
                self.assertEqual(semantic.extract_selector("text_regex:P/policy.txt::(actions:\\s*read)|remove_spaces"), "actions:read")
                self.assertEqual(
                    semantic.extract_selector(
                        "text_file:P/policy.txt|tokens=--default-branch-ref,--runner-ref,--trial-start-ref|strip_prefix=--|join=;"
                    ),
                    "default-branch-ref;runner-ref;trial-start-ref",
                )
                self.assertEqual(
                    semantic.extract_selector("python_ast_assignment:P/impl.py::FLAGS|order=blocked,failed,degraded|join=;"),
                    "blocked;failed;degraded",
                )
                self.assertEqual(
                    semantic.extract_selector(
                        "python_ast_assignments_concat:P/impl.py::SUFFIXES,NAMES|order=.mp4,.wav,.env,auth.json|join=;"
                    ),
                    ".mp4;.wav;.env;auth.json",
                )
                self.assertEqual(
                    semantic.extract_selector(
                        "python_ast_dict_projection:P/impl.py::TRANSITIONS|exclude_values=blocked|exclude_empty=true|pair=>|sep=;|value_sep=pipe"
                    ),
                    "created>health_checked;health_checked>completed",
                )
                self.assertEqual(
                    semantic.extract_selector("python_ast_call_arg_sequence:P/impl.py::run::step::0|join=>"),
                    "created>completed",
                )
                self.assertEqual(
                    semantic.extract_selector(
                        "python_ast_sequence_dict_field:P/impl.py::SCHEDULES::local_time|prefix_assignment=TIMEZONE|prefix_first_separator=:|join=;"
                    ),
                    "Australia/Sydney:04:45;05:00",
                )
                self.assertEqual(
                    semantic.extract_selector(
                        "python_ast_tuple:P/impl.py::VARS|filter=ADP_ALLOW_SMTP_SEND,ADP_ALLOW_RELEASE_UPLOAD|join=;"
                    ),
                    "ADP_ALLOW_SMTP_SEND;ADP_ALLOW_RELEASE_UPLOAD",
                )

    def test_review6_python_dict_value_selector_checks_active_value(self) -> None:
        semantic = load_semantic_module()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            project = tmp_path / "P"
            docs = project / "docs" / "governance"
            docs.mkdir(parents=True)
            (project / "impl.py").write_text('REGIMES = {"bear": {"mu": -0.00035, "sigma": 0.016}}\n', encoding="utf-8")
            selector = "python_ast_dict_value:P/impl.py::REGIMES::bear.mu"
            expected_hash = semantic.parameter_evidence_hash("PARAM-X", selector, -0.00035)
            (docs / "parameter_registry.csv").write_text(
                "\n".join(
                    [
                        "parameter_id,model_id,formula_id,symbol,name,category,data_type,unit,default_value,initial_or_prior_value,active_value,weight,weight_group,weight_group_target,weight_group_tolerance,min_value,max_value,formula_or_transform,source_or_rationale,calibration_method,sensitivity,code_ref,config_ref,test_ref,status,fact_level,unknown_task_ids,parameter_version,last_updated,source_selector,extracted_value,last_verified_commit,verified_at,evidence_hash",
                        f"PARAM-X,MOD-X,FORM-X,bear_mu,Bear mu,regime,float,return,-0.00035,-0.00035,-0.00035,NOT_APPLICABLE,,,,NOT_APPLICABLE,NOT_APPLICABLE,identity,test,test,medium,P/impl.py,P/impl.py,P/test_impl.py,active,EXTRACTED,,v1,2026-06-21,{selector},-0.00035,HEAD,2026-06-21T00:00:00Z,{expected_hash}",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            with patch.object(semantic, "ROOT", tmp_path), patch.object(semantic, "git_ref_exists", return_value=True):
                issues, summary = semantic.validate_project_semantics(project, "P")
        self.assertFalse([issue for issue in issues if issue.level == "ERROR"], issues)
        self.assertEqual(summary["semantic_parameters_checked"], 1)

    def test_review6_unknown_active_parameter_with_task_may_defer_selector(self) -> None:
        semantic = load_semantic_module()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            project = tmp_path / "P"
            docs = project / "docs" / "governance"
            docs.mkdir(parents=True)
            (docs / "parameter_registry.csv").write_text(
                "\n".join(
                    [
                        "parameter_id,model_id,formula_id,symbol,name,category,data_type,unit,default_value,initial_or_prior_value,active_value,weight,weight_group,weight_group_target,weight_group_tolerance,min_value,max_value,formula_or_transform,source_or_rationale,calibration_method,sensitivity,code_ref,config_ref,test_ref,status,fact_level,unknown_task_ids,parameter_version,last_updated,source_selector,extracted_value,last_verified_commit,verified_at,evidence_hash",
                        "PARAM-X,MOD-X,FORM-X,threshold,Threshold,threshold,float,ratio,UNKNOWN,UNKNOWN,UNKNOWN (GOV-SEMANTIC-P-001: source not yet evidenced),NOT_APPLICABLE,,,,0,1,identity,test,test,medium,P/catalog.csv,P/catalog.csv,P/test_impl.py,active,UNKNOWN,GOV-SEMANTIC-P-001,v1,2026-06-21,,,,,",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            with patch.object(semantic, "ROOT", tmp_path), patch.object(semantic, "git_ref_exists", return_value=True):
                issues, summary = semantic.validate_project_semantics(project, "P")
        self.assertFalse([issue for issue in issues if issue.level == "ERROR"], issues)
        self.assertEqual(summary["semantic_parameters_checked"], 0)

    def test_review6_human_review_parameter_with_task_may_defer_selector(self) -> None:
        semantic = load_semantic_module()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            project = tmp_path / "P"
            docs = project / "docs" / "governance"
            docs.mkdir(parents=True)
            (docs / "parameter_registry.csv").write_text(
                "\n".join(
                    [
                        "parameter_id,model_id,formula_id,symbol,name,category,data_type,unit,default_value,initial_or_prior_value,active_value,weight,weight_group,weight_group_target,weight_group_tolerance,min_value,max_value,formula_or_transform,source_or_rationale,calibration_method,sensitivity,code_ref,config_ref,test_ref,status,fact_level,unknown_task_ids,parameter_version,last_updated,source_selector,extracted_value,last_verified_commit,verified_at,evidence_hash,semantic_status,semantic_review_task_ids",
                        "PARAM-X,MOD-X,FORM-X,THRESHOLD,Threshold,threshold,float,ratio,0.45,0.45,0.45,NOT_APPLICABLE,,,,0,1,identity,test,test,medium,P/impl.py,P/impl.py,P/test_impl.py,active,EXTRACTED,,v1,2026-06-21,,,,,,HUMAN_REVIEW_REQUIRED,GOV-SEMANTIC-P-001",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            with patch.object(semantic, "ROOT", tmp_path), patch.object(semantic, "git_ref_exists", return_value=True):
                issues, summary = semantic.validate_project_semantics(project, "P")
        self.assertFalse([issue for issue in issues if issue.level == "ERROR"], issues)
        self.assertEqual(summary["semantic_parameters_checked"], 0)

    def test_review6_formula_implementation_fingerprint_mismatch_fails(self) -> None:
        semantic = load_semantic_module()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            project = tmp_path / "P"
            docs = project / "docs" / "governance"
            docs.mkdir(parents=True)
            (project / "impl.py").write_text("def rule(value):\n    return value + 1\n", encoding="utf-8")
            (docs / "parameter_registry.csv").write_text(
                "parameter_id,model_id,formula_id,symbol,name,category,data_type,unit,default_value,initial_or_prior_value,active_value,weight,weight_group,weight_group_target,weight_group_tolerance,min_value,max_value,formula_or_transform,source_or_rationale,calibration_method,sensitivity,code_ref,config_ref,test_ref,status,fact_level,unknown_task_ids,parameter_version,last_updated\n",
                encoding="utf-8",
            )
            (docs / "formula_registry.yaml").write_text(
                "\n".join(
                    [
                        'governance_spec_version: "1.0.0"',
                        'project_id: "P"',
                        "formulas:",
                        '  - formula_id: "FORM-X"',
                        '    model_id: "MOD-X"',
                        "    assumption_ids: []",
                        '    status: "active"',
                        '    expression: "return value + 1"',
                        "    variables: []",
                        '    constraints: "none"',
                        '    missing_policy: "none"',
                        '    output_range: "number"',
                        '    code_refs: ["P/impl.py:1"]',
                        "    test_refs: []",
                        "    evidence_refs: []",
                        '    semantic_status: "MACHINE_VERIFIED"',
                        '    implementation_refs: ["P/impl.py::rule"]',
                        '    implementation_fingerprint: "sha256:bad"',
                        '    last_verified_commit: "HEAD"',
                        '    verified_at: "2026-06-21T00:00:00Z"',
                        '    evidence_hash: "sha256:bad"',
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            with patch.object(semantic, "ROOT", tmp_path), patch.object(semantic, "git_ref_exists", return_value=True):
                issues, _ = semantic.validate_project_semantics(project, "P")
        self.assertTrue(any("implementation_fingerprint" in issue.message for issue in issues), issues)

    def test_review6_csv_row_formula_fingerprint_mismatch_fails(self) -> None:
        semantic = load_semantic_module()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            project = tmp_path / "P"
            docs = project / "docs" / "governance"
            docs.mkdir(parents=True)
            (project / "formulas.csv").write_text("formula_id,formula\nF-X,value + 1\n", encoding="utf-8")
            (docs / "parameter_registry.csv").write_text(
                "parameter_id,model_id,formula_id,symbol,name,category,data_type,unit,default_value,initial_or_prior_value,active_value,weight,weight_group,weight_group_target,weight_group_tolerance,min_value,max_value,formula_or_transform,source_or_rationale,calibration_method,sensitivity,code_ref,config_ref,test_ref,status,fact_level,unknown_task_ids,parameter_version,last_updated\n",
                encoding="utf-8",
            )
            (docs / "formula_registry.yaml").write_text(
                "\n".join(
                    [
                        'governance_spec_version: "1.0.0"',
                        'project_id: "P"',
                        "formulas:",
                        '  - formula_id: "FORM-X"',
                        '    model_id: "MOD-X"',
                        "    assumption_ids: []",
                        '    status: "active"',
                        '    expression: "value + 1"',
                        "    variables: []",
                        '    constraints: "none"',
                        '    missing_policy: "none"',
                        '    output_range: "number"',
                        '    code_refs: ["P/formulas.csv:1"]',
                        "    test_refs: []",
                        "    evidence_refs: []",
                        '    semantic_status: "MACHINE_VERIFIED"',
                        '    implementation_refs: ["csv_row:P/formulas.csv::formula_id=F-X"]',
                        '    implementation_fingerprint: "sha256:bad"',
                        '    last_verified_commit: "HEAD"',
                        '    verified_at: "2026-06-21T00:00:00Z"',
                        '    evidence_hash: "sha256:bad"',
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            with patch.object(semantic, "ROOT", tmp_path), patch.object(semantic, "git_ref_exists", return_value=True):
                issues, _ = semantic.validate_project_semantics(project, "P")
        self.assertTrue(any("implementation_fingerprint" in issue.message for issue in issues), issues)

    def test_review5_dashboard_generation_is_deterministic(self) -> None:
        result = run_validator("--all")
        self.assertEqual(result.returncode, 0, result.stdout)
        dashboard = load_dashboard_module()
        first = dashboard.generate(write=False)
        second = dashboard.generate(write=False)
        self.assertEqual(first["snapshot_event_time"], second["snapshot_event_time"])
        self.assertEqual(first["source_base_commit"], second["source_base_commit"])
        self.assertEqual(first["source_snapshot_hash"], second["source_snapshot_hash"])
        self.assertEqual(first["outputs"], second["outputs"])
        owner_outputs = [path for path in first["outputs"] if path.endswith("/docs/governance/OWNER_STATUS.md")]
        status_outputs = [path for path in first["outputs"] if path.endswith("/docs/governance/STATUS.md")]
        self.assertEqual(len(owner_outputs), len(status_outputs))
        self.assertIn("PFI/大数据模拟器/docs/governance/OWNER_STATUS.md", owner_outputs)
        meta = {
            "source_base_commit": first["source_base_commit"],
            "source_tree_hash": dashboard.current_tree_hash(),
            "source_snapshot_hash": first["source_snapshot_hash"],
            "snapshot_event_time": first["snapshot_event_time"],
        }
        rendered = dashboard.render_dashboard([dashboard.load_project(project) for project in dashboard.structural.load_yaml(ROOT / "governance" / "projects.yaml")["projects"]], meta)
        self.assertIn("Implementation congruence", rendered)
        self.assertIn("Empirical", rendered)
        self.assertIn("Param Source", rendered)
        self.assertIn("Operational", rendered)
        self.assertNotIn("DETERMINISTIC_GENERATION", rendered)

    def test_review6_owner_status_is_readable_and_prioritized(self) -> None:
        dashboard = load_dashboard_module()
        config = dashboard.structural.load_yaml(ROOT / "governance" / "projects.yaml")
        serenity = next(project for project in config["projects"] if project["project_id"] == "Serenity-Alipay")
        info = dashboard.load_project(serenity)
        rendered = dashboard.render_owner_status(info)
        for marker in (
            "## 1. Current Conclusion",
            "## 2. This Run Change",
            "## 4. Decision Needed",
            "## 5. A/B/C Choice Matrix",
            "## 12. Next Unique Task",
        ):
            self.assertIn(marker, rendered)
        self.assertIn("实现一致性", rendered)
        self.assertIn("empirical_validation", rendered)
        self.assertIn("operational_validation", rendered)
        self.assertNotIn("['", rendered)
        self.assertNotIn("{'", rendered)
        self.assertEqual(info["assurance"]["next_executable_task"]["task_id"], "TASK-A-001")

    def test_arxiv_owner_status_uses_latest_event_manifest(self) -> None:
        dashboard = load_dashboard_module()
        config = dashboard.structural.load_yaml(ROOT / "governance" / "projects.yaml")
        project = next(project for project in config["projects"] if project["project_id"] == "arxiv-daily-push")
        info = dashboard.load_project(project)
        self.assertEqual(info["latest_event"]["event_id"], "EVENT-20260622-ADP-058")
        self.assertEqual(info["assurance"]["as_of_event_id"], "EVENT-20260622-ADP-058")
        self.assertEqual(info["product_version"], "0.12.4")
        self.assertEqual(info["current_gate"], "ADP-PHASE12-MANUAL-DELIVERY-INTERNAL-RELEASE-DEDUPE-PREPARED")
        self.assertEqual(
            info["latest_manifest"]["_path"],
            "governance/run_manifests/GOV-SEMANTIC-ADP-PLANNED-001.json",
        )
        rendered = dashboard.render_owner_status(info)
        self.assertIn("0.12.4", rendered)
        self.assertIn("ADP-PHASE12-MANUAL-DELIVERY-INTERNAL-RELEASE-DEDUPE-PREPARED", rendered)
        self.assertIn("production trial not started", rendered)
        self.assertIn("30-day acceptance absent", rendered)
        self.assertNotIn("DETERMINISTIC_GENERATION", rendered)

    def test_eei_a209_4h_soak_governance_stays_partial_until_24h_exists(self) -> None:
        validator = load_validator_module()
        matrix = validator.load_yaml(ROOT / "EEI" / "docs" / "governance" / "VERSION_MATRIX.yaml")
        self.assertEqual(matrix["current_iteration"], "ITER-20260621-017")
        self.assertEqual(matrix["current_gate"], "TASK-T1307-A209-4H-OPERATOR-SOAK-PARTIAL")

        events = [json.loads(line) for line in (ROOT / "EEI" / "docs" / "governance" / "development_events.jsonl").read_text(encoding="utf-8").splitlines()]
        soak_event = next(event for event in events if event.get("event_id") == "EVENT-20260621-019")
        self.assertEqual(soak_event["task_id"], "TASK-T1307")
        self.assertIn("PARTIAL", soak_event["result"])
        review6_event = next(event for event in events if event.get("event_id") == "EVT-REVIEW6-FINAL-EEI-001")
        self.assertEqual(review6_event["binding_status"], "pre_commit_pending")

        owner_text = (ROOT / "EEI" / "docs" / "governance" / "OWNER_STATUS.md").read_text(encoding="utf-8")
        self.assertIn("TASK-T1307-A209-4H-OPERATOR-SOAK-PARTIAL", owner_text)
        self.assertIn("24h operator soak evidence", owner_text)

        self.assertTrue((ROOT / "EEI" / "artifacts" / "tests" / "a209" / "t1307_operator_soak_4h.json").is_file())
        self.assertTrue((ROOT / "EEI" / "artifacts" / "tests" / "a209" / "t1307_operator_soak_4h.checkpoints.jsonl").is_file())
        self.assertFalse((ROOT / "EEI" / "artifacts" / "tests" / "a209" / "t1307_operator_soak_24h.json").exists())

    def test_review5_run_manifest_supports_post_commit_binding_fields(self) -> None:
        manifest = json.loads((ROOT / "governance" / "run_manifests" / "GOV-REVIEW5-SYNC-001.json").read_text())
        for field in {
            "run_id",
            "base_commit",
            "content_tree_hash",
            "changed_files_actual",
            "change_classification",
            "required_governance_files",
            "updated_governance_files",
            "tests_run",
            "observed_results",
            "evidence_refs",
        }:
            self.assertIn(field, manifest)

    def test_arxiv_daily_push_phase2_manifest_records_contract_gate(self) -> None:
        manifest = json.loads(
            (ROOT / "governance" / "run_manifests" / "ADP-PHASE2-DATA-CONTRACTS-20260621.json").read_text()
        )
        self.assertEqual(manifest["project_id"], "arxiv-daily-push")
        self.assertEqual(manifest["task_id"], "ADP-PHASE2-DATA-CONTRACTS-001")
        self.assertIn("MOD-ADP-004", manifest["model_delta"])

    def test_arxiv_daily_push_phase3_manifest_records_arxiv_adapter_gate(self) -> None:
        manifest = json.loads(
            (ROOT / "governance" / "run_manifests" / "ADP-PHASE3-ARXIV-ADAPTER-20260621.json").read_text()
        )
        self.assertEqual(manifest["project_id"], "arxiv-daily-push")
        self.assertEqual(manifest["task_id"], "ADP-PHASE3-ARXIV-ADAPTER-001")
        self.assertIn("MOD-ADP-005", manifest["model_delta"])

    def test_arxiv_daily_push_phase4_manifest_records_ranking_gate(self) -> None:
        manifest = json.loads((ROOT / "governance" / "run_manifests" / "ADP-PHASE4-RANKING-20260621.json").read_text())
        self.assertEqual(manifest["project_id"], "arxiv-daily-push")
        self.assertEqual(manifest["task_id"], "ADP-PHASE4-RANKING-001")
        self.assertIn("MOD-ADP-002", manifest["model_delta"])

    def test_arxiv_daily_push_phase5_manifest_records_evidence_gate(self) -> None:
        manifest = json.loads(
            (ROOT / "governance" / "run_manifests" / "ADP-PHASE5-EVIDENCE-GATE-20260621.json").read_text()
        )
        self.assertEqual(manifest["project_id"], "arxiv-daily-push")
        self.assertEqual(manifest["task_id"], "ADP-PHASE5-EVIDENCE-GATE-001")
        self.assertIn("MOD-ADP-003", manifest["model_delta"])

    def test_arxiv_daily_push_phase6_manifest_records_lesson_gate(self) -> None:
        manifest = json.loads((ROOT / "governance" / "run_manifests" / "ADP-PHASE6-LESSON-20260621.json").read_text())
        self.assertEqual(manifest["project_id"], "arxiv-daily-push")
        self.assertEqual(manifest["task_id"], "ADP-PHASE6-LESSON-001")
        self.assertIn("MOD-ADP-006", manifest["model_delta"])

    def test_arxiv_daily_push_phase7_manifest_records_narration_gate(self) -> None:
        manifest = json.loads((ROOT / "governance" / "run_manifests" / "ADP-PHASE7-TTS-20260621.json").read_text())
        self.assertEqual(manifest["project_id"], "arxiv-daily-push")
        self.assertEqual(manifest["task_id"], "ADP-PHASE7-TTS-001")
        self.assertIn("MOD-ADP-007", manifest["model_delta"])

    def test_arxiv_daily_push_phase8_manifest_records_video_gate(self) -> None:
        manifest = json.loads((ROOT / "governance" / "run_manifests" / "ADP-PHASE8-VIDEO-20260621.json").read_text())
        self.assertEqual(manifest["project_id"], "arxiv-daily-push")
        self.assertEqual(manifest["task_id"], "ADP-PHASE8-VIDEO-001")
        self.assertIn("MOD-ADP-008", manifest["model_delta"])

    def test_arxiv_daily_push_phase9_manifest_records_pipeline_gate(self) -> None:
        manifest = json.loads((ROOT / "governance" / "run_manifests" / "ADP-PHASE9-LOCAL-PIPELINE-20260621.json").read_text())
        self.assertEqual(manifest["project_id"], "arxiv-daily-push")
        self.assertEqual(manifest["task_id"], "ADP-PHASE9-LOCAL-PIPELINE-001")
        self.assertIn("MOD-ADP-009", manifest["model_delta"])

    def test_arxiv_daily_push_phase10_manifest_records_handoff_gate(self) -> None:
        manifest = json.loads(
            (ROOT / "governance" / "run_manifests" / "ADP-PHASE10-RUNNER-RELEASE-EMAIL-20260621.json").read_text()
        )
        self.assertEqual(manifest["project_id"], "arxiv-daily-push")
        self.assertEqual(manifest["task_id"], "ADP-PHASE10-RUNNER-RELEASE-EMAIL-001")
        self.assertIn("MOD-ADP-010", manifest["model_delta"])

    def test_arxiv_daily_push_phase11_manifest_records_acceptance_gate(self) -> None:
        manifest = json.loads(
            (ROOT / "governance" / "run_manifests" / "ADP-PHASE11-ACCEPTANCE-HANDOFF-20260621.json").read_text()
        )
        self.assertEqual(manifest["project_id"], "arxiv-daily-push")
        self.assertEqual(manifest["task_id"], "ADP-PHASE11-ACCEPTANCE-HANDOFF-001")
        self.assertIn("MOD-ADP-011", manifest["model_delta"])

    def test_arxiv_daily_push_phase11_manifest_records_evidence_ref_hardening(self) -> None:
        manifest = json.loads(
            (ROOT / "governance" / "run_manifests" / "ADP-PHASE11-EVIDENCE-REF-HARDENING-20260621.json").read_text()
        )
        self.assertEqual(manifest["project_id"], "arxiv-daily-push")
        self.assertEqual(manifest["task_id"], "ADP-PHASE11-EVIDENCE-REF-HARDENING-002")
        self.assertIn("MOD-ADP-011", manifest["model_delta"])

    def test_arxiv_daily_push_phase11_manifest_records_trial_evidence_validator(self) -> None:
        manifest = json.loads(
            (ROOT / "governance" / "run_manifests" / "ADP-PHASE11-TRIAL-EVIDENCE-VALIDATOR-20260621.json").read_text()
        )
        self.assertEqual(manifest["project_id"], "arxiv-daily-push")
        self.assertEqual(manifest["task_id"], "ADP-PHASE11-TRIAL-EVIDENCE-VALIDATOR-003")
        self.assertIn("MOD-ADP-012", manifest["model_delta"])

    def test_arxiv_daily_push_phase11_manifest_records_production_preflight(self) -> None:
        manifest = json.loads(
            (ROOT / "governance" / "run_manifests" / "ADP-PHASE11-PRODUCTION-PREFLIGHT-20260621.json").read_text()
        )
        self.assertEqual(manifest["project_id"], "arxiv-daily-push")
        self.assertEqual(manifest["task_id"], "ADP-PHASE11-PRODUCTION-PREFLIGHT-004")
        self.assertIn("MOD-ADP-013", manifest["model_delta"])

    def test_arxiv_daily_push_phase11_manifest_records_trial_bootstrap(self) -> None:
        manifest = json.loads(
            (ROOT / "governance" / "run_manifests" / "ADP-PHASE11-TRIAL-BOOTSTRAP-20260621.json").read_text()
        )
        self.assertEqual(manifest["project_id"], "arxiv-daily-push")
        self.assertEqual(manifest["task_id"], "ADP-PHASE11-TRIAL-BOOTSTRAP-005")
        self.assertIn("MOD-ADP-014", manifest["model_delta"])

    def test_arxiv_daily_push_phase11_manifest_records_live_arxiv_ingest(self) -> None:
        manifest = json.loads(
            (ROOT / "governance" / "run_manifests" / "ADP-PHASE11-LIVE-ARXIV-INGEST-20260621.json").read_text()
        )
        self.assertEqual(manifest["project_id"], "arxiv-daily-push")
        self.assertEqual(manifest["task_id"], "ADP-PHASE11-LIVE-ARXIV-INGEST-006")
        self.assertIn("MOD-ADP-015", manifest["model_delta"])

    def test_arxiv_daily_push_phase11_manifest_records_smtp_delivery(self) -> None:
        manifest = json.loads(
            (ROOT / "governance" / "run_manifests" / "ADP-PHASE11-SMTP-DELIVERY-20260621.json").read_text()
        )
        self.assertEqual(manifest["project_id"], "arxiv-daily-push")
        self.assertEqual(manifest["task_id"], "ADP-PHASE11-SMTP-DELIVERY-007")
        self.assertIn("MOD-ADP-016", manifest["model_delta"])

    def test_arxiv_daily_push_phase11_manifest_records_release_delivery(self) -> None:
        manifest = json.loads(
            (ROOT / "governance" / "run_manifests" / "ADP-PHASE11-RELEASE-DELIVERY-20260621.json").read_text()
        )
        self.assertEqual(manifest["project_id"], "arxiv-daily-push")
        self.assertEqual(manifest["task_id"], "ADP-PHASE11-RELEASE-DELIVERY-008")
        self.assertIn("MOD-ADP-017", manifest["model_delta"])

    def test_arxiv_daily_push_phase11_manifest_records_production_scheduler(self) -> None:
        manifest = json.loads(
            (ROOT / "governance" / "run_manifests" / "ADP-PHASE11-PRODUCTION-SCHEDULER-20260621.json").read_text()
        )
        self.assertEqual(manifest["project_id"], "arxiv-daily-push")
        self.assertEqual(manifest["task_id"], "ADP-PHASE11-PRODUCTION-SCHEDULER-009")
        self.assertIn("MOD-ADP-018", manifest["model_delta"])

    def test_arxiv_daily_push_phase11_manifest_records_scheduled_execution(self) -> None:
        manifest = json.loads(
            (ROOT / "governance" / "run_manifests" / "ADP-PHASE11-SCHEDULED-EXECUTION-20260621.json").read_text()
        )
        self.assertEqual(manifest["project_id"], "arxiv-daily-push")
        self.assertEqual(manifest["task_id"], "ADP-PHASE11-SCHEDULED-EXECUTION-010")
        self.assertIn("MOD-ADP-019", manifest["model_delta"])

    def test_arxiv_daily_push_phase11_manifest_records_daily_input_builder(self) -> None:
        manifest = json.loads(
            (ROOT / "governance" / "run_manifests" / "ADP-PHASE11-DAILY-INPUT-BUILDER-20260621.json").read_text()
        )
        self.assertEqual(manifest["project_id"], "arxiv-daily-push")
        self.assertEqual(manifest["task_id"], "ADP-PHASE11-DAILY-INPUT-BUILDER-011")
        self.assertIn("MOD-ADP-020", manifest["model_delta"])

    def test_arxiv_daily_push_phase11_manifest_records_trial_ledger(self) -> None:
        manifest = json.loads(
            (ROOT / "governance" / "run_manifests" / "ADP-PHASE11-TRIAL-LEDGER-20260621.json").read_text()
        )
        self.assertEqual(manifest["project_id"], "arxiv-daily-push")
        self.assertEqual(manifest["task_id"], "ADP-PHASE11-TRIAL-LEDGER-012")
        self.assertIn("MOD-ADP-021", manifest["model_delta"])

    def test_arxiv_daily_push_phase11_manifest_records_trial_ledger_state(self) -> None:
        manifest = json.loads(
            (ROOT / "governance" / "run_manifests" / "ADP-PHASE11-TRIAL-LEDGER-STATE-20260622.json").read_text()
        )
        self.assertEqual(manifest["project_id"], "arxiv-daily-push")
        self.assertEqual(manifest["task_id"], "ADP-PHASE11-TRIAL-LEDGER-STATE-013")
        self.assertIn("MOD-ADP-022", manifest["model_delta"])

    def test_arxiv_daily_push_phase11_manifest_records_trial_ops_evidence(self) -> None:
        manifest = json.loads(
            (ROOT / "governance" / "run_manifests" / "ADP-PHASE11-TRIAL-OPS-EVIDENCE-20260622.json").read_text()
        )
        self.assertEqual(manifest["project_id"], "arxiv-daily-push")
        self.assertEqual(manifest["task_id"], "ADP-PHASE11-TRIAL-OPS-EVIDENCE-014")
        self.assertIn("MOD-ADP-023", manifest["model_delta"])

    def test_arxiv_daily_push_phase11_manifest_records_trial_replay_evidence(self) -> None:
        manifest = json.loads(
            (ROOT / "governance" / "run_manifests" / "ADP-PHASE11-TRIAL-REPLAY-EVIDENCE-20260622.json").read_text()
        )
        self.assertEqual(manifest["project_id"], "arxiv-daily-push")
        self.assertEqual(manifest["task_id"], "ADP-PHASE11-TRIAL-REPLAY-EVIDENCE-015")
        self.assertIn("MOD-ADP-024", manifest["model_delta"])

    def test_arxiv_daily_push_phase11_manifest_records_trial_recovery_evidence(self) -> None:
        manifest = json.loads(
            (ROOT / "governance" / "run_manifests" / "ADP-PHASE11-TRIAL-RECOVERY-EVIDENCE-20260622.json").read_text()
        )
        self.assertEqual(manifest["project_id"], "arxiv-daily-push")
        self.assertEqual(manifest["task_id"], "ADP-PHASE11-TRIAL-RECOVERY-EVIDENCE-016")
        self.assertIn("MOD-ADP-025", manifest["model_delta"])

    def test_arxiv_daily_push_phase11_manifest_records_trial_resource_evidence(self) -> None:
        manifest = json.loads(
            (ROOT / "governance" / "run_manifests" / "ADP-PHASE11-TRIAL-RESOURCE-EVIDENCE-20260622.json").read_text()
        )
        self.assertEqual(manifest["project_id"], "arxiv-daily-push")
        self.assertEqual(manifest["task_id"], "ADP-PHASE11-TRIAL-RESOURCE-EVIDENCE-017")
        self.assertIn("MOD-ADP-026", manifest["model_delta"])

    def test_arxiv_daily_push_phase11_manifest_records_trial_start_gate(self) -> None:
        manifest = json.loads(
            (ROOT / "governance" / "run_manifests" / "ADP-PHASE11-TRIAL-START-GATE-20260622.json").read_text()
        )
        self.assertEqual(manifest["project_id"], "arxiv-daily-push")
        self.assertEqual(manifest["task_id"], "ADP-PHASE11-TRIAL-START-GATE-018")
        self.assertIn("MOD-ADP-027", manifest["model_delta"])

    def test_arxiv_daily_push_phase11_manifest_records_trial_start_workflow(self) -> None:
        manifest = json.loads(
            (ROOT / "governance" / "run_manifests" / "ADP-PHASE11-TRIAL-START-WORKFLOW-20260622.json").read_text()
        )
        self.assertEqual(manifest["project_id"], "arxiv-daily-push")
        self.assertEqual(manifest["task_id"], "ADP-PHASE11-TRIAL-START-WORKFLOW-019")
        self.assertIn("MOD-ADP-028", manifest["model_delta"])

    def test_arxiv_daily_push_phase11_manifest_records_production_launch_readiness(self) -> None:
        manifest = json.loads(
            (
                ROOT
                / "governance"
                / "run_manifests"
                / "ADP-PHASE11-PRODUCTION-LAUNCH-READINESS-20260622.json"
            ).read_text()
        )
        self.assertEqual(manifest["project_id"], "arxiv-daily-push")
        self.assertEqual(manifest["task_id"], "ADP-PHASE11-PRODUCTION-LAUNCH-READINESS-020")
        self.assertIn("MOD-ADP-029", manifest["model_delta"])

    def test_arxiv_daily_push_phase11_manifest_records_post_merge_launch_audit(self) -> None:
        manifest = json.loads(
            (
                ROOT
                / "governance"
                / "run_manifests"
                / "ADP-PHASE11-POST-MERGE-LAUNCH-AUDIT-20260622.json"
            ).read_text()
        )
        self.assertEqual(manifest["project_id"], "arxiv-daily-push")
        self.assertEqual(manifest["task_id"], "ADP-PHASE11-POST-MERGE-LAUNCH-AUDIT-021")
        self.assertTrue(manifest["pr_evidence"]["merged"])
        self.assertFalse(manifest["pr_evidence"]["draft"])
        self.assertIn("default_branch_ref", manifest["launch_gate"]["failed_gates"])
        self.assertIn("trial_start_workflow_ready", manifest["launch_gate"]["passed_gates"])

        trial_start_workflow = (ROOT / ".github" / "workflows" / "arxiv-daily-push-trial-start.yml").read_text(
            encoding="utf-8"
        )
        scheduled_workflow = (ROOT / ".github" / "workflows" / "arxiv-daily-push-scheduled.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn("contents: write", trial_start_workflow)
        self.assertIn("contents: write", scheduled_workflow)
        self.assertTrue(any("Production launch remains blocked" in risk for risk in manifest["risks"]))
        self.assertNotIn("draft and unmerged", " ".join(manifest["risks"]))

    def test_arxiv_daily_push_phase11_manifest_records_production_trial_start_precheck(self) -> None:
        manifest = json.loads(
            (
                ROOT
                / "governance"
                / "run_manifests"
                / "ADP-PHASE11-PRODUCTION-TRIAL-START-PRECHECK-20260622.json"
            ).read_text()
        )
        self.assertEqual(manifest["project_id"], "arxiv-daily-push")
        self.assertEqual(manifest["task_id"], "ADP-PHASE11-PRODUCTION-TRIAL-START-022")
        self.assertEqual(manifest["pr_evidence"]["pr_number"], 32)
        self.assertEqual(manifest["main_ci_evidence"]["conclusion"], "success")
        self.assertIn("default_branch_ref", manifest["launch_gate"]["passed_gates"])
        self.assertIn("trial_start_workflow_ref", manifest["launch_gate"]["passed_gates"])
        self.assertIn("runner_ref", manifest["launch_gate"]["failed_gates"])

    def test_arxiv_daily_push_phase11_manifest_records_production_refs_bundle(self) -> None:
        manifest = json.loads(
            (
                ROOT
                / "governance"
                / "run_manifests"
                / "ADP-PHASE11-PRODUCTION-REFS-BUNDLE-20260622.json"
            ).read_text()
        )
        self.assertEqual(manifest["project_id"], "arxiv-daily-push")
        self.assertEqual(manifest["task_id"], "ADP-PHASE11-PRODUCTION-REFS-BUNDLE-023")
        self.assertEqual(manifest["production_refs_gate"]["validator_id"], "adp-production-refs-v1")
        self.assertIn("ADP_SMTP_PASSWORD", manifest["production_refs_gate"]["required_smtp_secret_names"])
        self.assertFalse(manifest["production_refs_gate"]["secret_values_logged"])
        self.assertEqual(manifest["semantic_coverage"]["semantic_parameters_checked"], 158)
        self.assertEqual(manifest["semantic_coverage"]["semantic_formulas_checked"], 32)

    def test_arxiv_daily_push_phase11_manifest_records_release_permissions(self) -> None:
        manifest = json.loads(
            (
                ROOT
                / "governance"
                / "run_manifests"
                / "ADP-PHASE11-RELEASE-PERMISSIONS-20260622.json"
            ).read_text()
        )
        self.assertEqual(manifest["project_id"], "arxiv-daily-push")
        self.assertEqual(manifest["task_id"], "ADP-PHASE11-RELEASE-PERMISSIONS-024")
        self.assertEqual(manifest["release_permission_gate"]["permission"], "contents: write")
        self.assertIn(
            ".github/workflows/arxiv-daily-push-trial-start.yml",
            manifest["release_permission_gate"]["required_for"],
        )
        self.assertFalse(manifest["release_permission_gate"]["default_release_upload_enabled"])
        self.assertFalse(manifest["release_permission_gate"]["production_acceptance_claimed"])

    def test_arxiv_daily_push_phase11_manifest_records_production_refs_template(self) -> None:
        manifest = json.loads(
            (
                ROOT
                / "governance"
                / "run_manifests"
                / "ADP-PHASE11-PRODUCTION-REFS-TEMPLATE-20260622.json"
            ).read_text()
        )
        self.assertEqual(manifest["project_id"], "arxiv-daily-push")
        self.assertEqual(manifest["task_id"], "ADP-PHASE11-PRODUCTION-REFS-TEMPLATE-025")
        self.assertEqual(
            manifest["production_refs_template_gate"]["template_sections"],
            ["runner", "smtp_secrets", "release_target", "workflow_vars"],
        )
        self.assertIn("ADP_SMTP_PASSWORD", manifest["production_refs_template_gate"]["required_smtp_secret_names"])
        self.assertFalse(manifest["production_refs_template_gate"]["template_defaults_ready"])
        self.assertFalse(manifest["production_refs_template_gate"]["secret_values_logged"])

    def test_arxiv_daily_push_phase11_manifest_records_production_refs_github_discovery(self) -> None:
        manifest = json.loads(
            (
                ROOT
                / "governance"
                / "run_manifests"
                / "ADP-PHASE11-PRODUCTION-REFS-GITHUB-DISCOVERY-20260622.json"
            ).read_text()
        )
        self.assertEqual(manifest["project_id"], "arxiv-daily-push")
        self.assertEqual(manifest["task_id"], "ADP-PHASE11-PRODUCTION-REFS-GITHUB-DISCOVERY-026")
        gate = manifest["production_refs_github_discovery_gate"]
        self.assertEqual(gate["command"], "discover-production-refs")
        self.assertEqual(gate["default_repo"], "LinzeColin/CodexProject")
        self.assertEqual(gate["local_discovery_status"], "blocked_gh_missing")
        self.assertFalse(gate["secret_values_logged"])
        self.assertFalse(gate["gh_stdout_logged"])
        self.assertFalse(gate["gh_stderr_logged"])
        self.assertFalse(gate["production_acceptance_claimed"])

    def test_arxiv_daily_push_phase11_manifest_records_trial_start_launch_preflight(self) -> None:
        manifest = json.loads(
            (
                ROOT
                / "governance"
                / "run_manifests"
                / "ADP-PHASE11-TRIAL-START-LAUNCH-PREFLIGHT-20260622.json"
            ).read_text()
        )
        self.assertEqual(manifest["project_id"], "arxiv-daily-push")
        self.assertEqual(manifest["task_id"], "ADP-PHASE11-TRIAL-START-LAUNCH-PREFLIGHT-027")
        gate = manifest["trial_start_launch_preflight_gate"]
        self.assertIn("discover-production-refs", gate["pre_side_effect_commands"])
        self.assertIn("plan-production-launch", gate["pre_side_effect_commands"])
        self.assertIn("adp-trial-start-production-refs", gate["required_artifacts"])
        self.assertIn("adp-trial-start-launch-readiness", gate["required_artifacts"])
        self.assertFalse(gate["default_side_effects_enabled"])
        self.assertFalse(gate["secret_values_logged"])
        self.assertFalse(gate["codex_auth_read"])
        self.assertFalse(gate["workflow_dispatched"])
        self.assertFalse(gate["production_acceptance_claimed"])

    def test_arxiv_daily_push_phase11_manifest_records_provisioning_audit_workflow(self) -> None:
        manifest = json.loads(
            (
                ROOT
                / "governance"
                / "run_manifests"
                / "ADP-PHASE11-PROVISIONING-AUDIT-WORKFLOW-20260622.json"
            ).read_text()
        )
        self.assertEqual(manifest["project_id"], "arxiv-daily-push")
        self.assertEqual(manifest["task_id"], "ADP-PHASE11-PROVISIONING-AUDIT-WORKFLOW-028")
        gate = manifest["provisioning_audit_gate"]
        self.assertEqual(gate["workflow"], ".github/workflows/arxiv-daily-push-provisioning-audit.yml")
        self.assertEqual(gate["runner"], "ubuntu-latest")
        self.assertEqual(gate["command"], "discover-production-refs")
        self.assertEqual(gate["artifact"], "adp-production-provisioning-audit")
        self.assertFalse(gate["self_hosted_runner_started"])
        self.assertFalse(gate["secret_values_logged"])
        self.assertFalse(gate["codex_auth_read"])
        self.assertFalse(gate["trial_start_dispatched"])
        self.assertFalse(gate["smtp_sent"])
        self.assertFalse(gate["release_uploaded"])
        self.assertFalse(gate["production_acceptance_claimed"])

    def test_arxiv_daily_push_phase11_manifest_records_provisioning_audit_review(self) -> None:
        manifest = json.loads(
            (
                ROOT
                / "governance"
                / "run_manifests"
                / "ADP-PHASE11-PROVISIONING-AUDIT-REVIEW-20260622.json"
            ).read_text()
        )
        self.assertEqual(manifest["project_id"], "arxiv-daily-push")
        self.assertEqual(manifest["task_id"], "ADP-PHASE11-PROVISIONING-AUDIT-REVIEW-029")
        gate = manifest["provisioning_audit_review_gate"]
        self.assertEqual(gate["command"], "review-provisioning-audit")
        self.assertEqual(gate["validator_id"], "adp-provisioning-audit-review-v1")
        self.assertIn("production_refs_ready=true", gate["required_inputs"])
        self.assertIn("workflow_run_ref", gate["required_refs"])
        self.assertIn("artifact_ref", gate["required_refs"])
        self.assertFalse(gate["side_effects_performed"])
        self.assertFalse(gate["secret_values_logged"])
        self.assertFalse(gate["codex_auth_read"])
        self.assertFalse(gate["workflow_dispatched"])
        self.assertFalse(gate["smtp_sent"])
        self.assertFalse(gate["release_uploaded"])
        self.assertFalse(gate["production_acceptance_claimed"])

    def test_arxiv_daily_push_phase11_manifest_records_two_day_simulation(self) -> None:
        manifest = json.loads(
            (
                ROOT
                / "governance"
                / "run_manifests"
                / "ADP-PHASE11-TWO-DAY-SIMULATION-20260622.json"
            ).read_text()
        )
        self.assertEqual(manifest["project_id"], "arxiv-daily-push")
        self.assertEqual(manifest["task_id"], "ADP-PHASE11-TWO-DAY-SIMULATION-030")
        gate = manifest["two_day_simulation_gate"]
        self.assertEqual(gate["command"], "run-two-day-simulation")
        self.assertEqual(gate["model_id"], "adp-two-day-simulation-v1")
        self.assertEqual(gate["observed_day_count"], 2)
        self.assertEqual(gate["observed_dates"], ["2026-06-22", "2026-06-23"])
        self.assertTrue(gate["two_day_simulation_ready"])
        self.assertFalse(gate["network_fetch_performed"])
        self.assertFalse(gate["side_effects_performed"])
        self.assertFalse(gate["real_smtp_sent"])
        self.assertFalse(gate["real_release_uploaded"])
        self.assertFalse(gate["secret_values_logged"])
        self.assertFalse(gate["codex_auth_read"])
        self.assertFalse(gate["accepted_for_production"])
        self.assertFalse(gate["production_acceptance_claimed"])

    def test_arxiv_daily_push_phase12_manifest_records_all_arxiv_queue_delivery(self) -> None:
        manifest = json.loads(
            (
                ROOT
                / "governance"
                / "run_manifests"
                / "ADP-PHASE12-ALL-ARXIV-QUEUE-DELIVERY-20260622.json"
            ).read_text()
        )
        self.assertEqual(manifest["project_id"], "arxiv-daily-push")
        self.assertEqual(manifest["task_id"], "ADP-PHASE12-ALL-ARXIV-QUEUE-DELIVERY-031")
        acceptance = manifest["acceptance"]
        self.assertTrue(acceptance["all_arxiv_scan"])
        self.assertTrue(acceptance["candidate_queue_persistence"])
        self.assertTrue(acceptance["roi_ranking"])
        self.assertTrue(acceptance["one_daily_lead"])
        self.assertTrue(acceptance["queue_fallback"])
        self.assertTrue(acceptance["release_video_artifact_link_required"])
        self.assertTrue(acceptance["email_candidate_queue_summary_required"])
        self.assertTrue(acceptance["legacy_cs_ai_production_default_removed"])
        self.assertFalse(acceptance["production_enabled"])
        self.assertFalse(acceptance["scheduled_run_enabled"])
        self.assertFalse(acceptance["allow_smtp_send"])
        self.assertFalse(acceptance["allow_release_upload"])

    def test_arxiv_daily_push_phase12_manifest_records_cloud_production_enablement(self) -> None:
        manifest = json.loads(
            (
                ROOT
                / "governance"
                / "run_manifests"
                / "ADP-PHASE12-PRODUCTION-ENABLEMENT-CLOUD-20260622.json"
            ).read_text()
        )
        self.assertEqual(manifest["project_id"], "arxiv-daily-push")
        self.assertEqual(manifest["task_id"], "ADP-PHASE12-PRODUCTION-ENABLEMENT-032")
        self.assertEqual(manifest["version_after"], "0.12.1")
        self.assertEqual(manifest["model_ids_changed"], ["MOD-ADP-033"])
        self.assertIn("FORM-ADP-035", manifest["formula_ids_changed"])
        self.assertIn("PARAM-ADP-180", manifest["parameter_ids_changed"])
        self.assertFalse(manifest["production_flags"]["ADP_PRODUCTION_ENABLED"])
        self.assertFalse(manifest["production_flags"]["ADP_SCHEDULED_RUN_ENABLED"])
        self.assertFalse(manifest["production_flags"]["ADP_ALLOW_SMTP_SEND"])
        self.assertFalse(manifest["production_flags"]["ADP_ALLOW_RELEASE_UPLOAD"])
        self.assertTrue(manifest["live_cloud_dry_run_executed"])
        cloud_result = manifest["live_cloud_dry_run_result"]
        self.assertEqual(cloud_result["workflow_run_id"], 27924078126)
        self.assertEqual(cloud_result["conclusion"], "success")
        self.assertEqual(cloud_result["verified_archive_count"], 20)
        self.assertEqual(cloud_result["failed_archive_count"], 0)
        self.assertEqual(cloud_result["candidate_count"], 16)
        self.assertTrue(cloud_result["sample_daily_input_generated"])
        self.assertTrue(cloud_result["mp4_artifact_generated"])
        self.assertGreater(cloud_result["mp4_artifact_size_bytes"], 0)
        self.assertFalse(manifest["real_smtp_sent"])
        self.assertFalse(manifest["real_release_uploaded"])
        self.assertFalse(manifest["production_schedule_enabled"])
        self.assertIn(
            ".github/workflows/arxiv-daily-push-phase12-cloud-dry-run.yml",
            manifest["files_changed"],
        )

    def test_arxiv_daily_push_phase12_manifest_records_manual_delivery_test(self) -> None:
        manifest = json.loads(
            (
                ROOT
                / "governance"
                / "run_manifests"
                / "ADP-PHASE12-MANUAL-DELIVERY-TEST-20260622.json"
            ).read_text()
        )
        self.assertEqual(manifest["project_id"], "arxiv-daily-push")
        self.assertEqual(manifest["task_id"], "ADP-PHASE12-MANUAL-DELIVERY-TEST-033")
        self.assertEqual(manifest["version_after"], "0.12.2")
        self.assertEqual(manifest["model_ids_changed"], ["MOD-ADP-034"])
        self.assertIn("FORM-ADP-036", manifest["formula_ids_changed"])
        self.assertIn("PARAM-ADP-184", manifest["parameter_ids_changed"])
        self.assertTrue(manifest["manual_test_workflow_prepared"])
        self.assertTrue(manifest["manual_workflow_side_effect_flags"]["workflow_dispatch_only"])
        self.assertTrue(manifest["manual_workflow_side_effect_flags"]["default_branch_only"])
        self.assertFalse(manifest["real_smtp_sent"])
        self.assertFalse(manifest["real_release_uploaded"])
        self.assertFalse(manifest["production_schedule_enabled"])
        self.assertIn(
            ".github/workflows/arxiv-daily-push-manual-delivery-test.yml",
            manifest["files_changed"],
        )

    def test_arxiv_daily_push_phase12_manifest_records_manual_delivery_release_dedupe(self) -> None:
        manifest = json.loads(
            (
                ROOT
                / "governance"
                / "run_manifests"
                / "ADP-PHASE12-MANUAL-DELIVERY-RELEASE-DEDUPE-20260622.json"
            ).read_text()
        )
        self.assertEqual(manifest["project_id"], "arxiv-daily-push")
        self.assertEqual(manifest["task_id"], "ADP-PHASE12-MANUAL-DELIVERY-RELEASE-DEDUPE-034")
        self.assertEqual(manifest["version_after"], "0.12.3")
        self.assertEqual(manifest["model_ids_changed"], ["MOD-ADP-034"])
        self.assertIn("FORM-ADP-036", manifest["formula_ids_changed"])
        self.assertIn("PARAM-ADP-184", manifest["parameter_ids_changed"])
        self.assertTrue(manifest["release_asset_dedupe_enabled"])
        self.assertFalse(manifest["real_smtp_sent"])
        self.assertFalse(manifest["real_release_uploaded"])
        self.assertFalse(manifest["production_schedule_enabled"])
        self.assertEqual(manifest["failed_manual_run"]["run_id"], 27926461430)
        self.assertIn(
            ".github/workflows/arxiv-daily-push-manual-delivery-test.yml",
            manifest["files_changed"],
        )

    def test_arxiv_daily_push_phase12_manifest_records_internal_release_dedupe(self) -> None:
        manifest = json.loads(
            (
                ROOT
                / "governance"
                / "run_manifests"
                / "ADP-PHASE12-MANUAL-DELIVERY-INTERNAL-RELEASE-DEDUPE-20260622.json"
            ).read_text()
        )
        self.assertEqual(manifest["project_id"], "arxiv-daily-push")
        self.assertEqual(manifest["task_id"], "ADP-PHASE12-MANUAL-DELIVERY-INTERNAL-RELEASE-DEDUPE-035")
        self.assertEqual(manifest["version_after"], "0.12.4")
        self.assertIn("MOD-ADP-017", manifest["model_ids_changed"])
        self.assertIn("MOD-ADP-033", manifest["model_ids_changed"])
        self.assertIn("FORM-ADP-019", manifest["formula_ids_changed"])
        self.assertIn("FORM-ADP-035", manifest["formula_ids_changed"])
        self.assertIn("PARAM-ADP-185", manifest["parameter_ids_changed"])
        self.assertTrue(manifest["release_internal_asset_path_dedupe_enabled"])
        self.assertTrue(manifest["duplicate_release_filename_fail_closed"])
        self.assertTrue(manifest["live_all_arxiv_transient_retry_enabled"])
        self.assertFalse(manifest["real_smtp_sent"])
        self.assertFalse(manifest["real_release_uploaded"])
        self.assertFalse(manifest["production_schedule_enabled"])
        self.assertEqual(manifest["failed_manual_run"]["run_id"], 27927785092)
        self.assertEqual(manifest["failed_pr_cloud_dry_run"]["run_id"], 27928505758)
        self.assertIn(
            "arxiv-daily-push/src/arxiv_daily_push/release_delivery.py",
            manifest["files_changed"],
        )

    def test_arxiv_daily_push_semantic_extract_manifest_records_partial_coverage(self) -> None:
        manifest = json.loads(
            (
                ROOT
                / "governance"
                / "run_manifests"
                / "GOV-SEMANTIC-ADP-EXTRACT-001.json"
            ).read_text()
        )
        self.assertEqual(manifest["project_id"], "arxiv-daily-push")
        self.assertEqual(manifest["task_id"], "GOV-SEMANTIC-ADP-001")
        self.assertEqual(manifest["coverage_status"], "in_progress")
        self.assertEqual(manifest["semantic_parameters_checked"], 45)
        self.assertEqual(manifest["human_review_required_parameters"], 107)
        self.assertEqual(manifest["semantic_formulas_checked"], 9)
        self.assertEqual(manifest["human_review_required_formulas"], 22)

    def test_arxiv_daily_push_semantic_extract_manifest_records_expanded_coverage(self) -> None:
        manifest = json.loads(
            (
                ROOT
                / "governance"
                / "run_manifests"
                / "GOV-SEMANTIC-ADP-EXTRACT-002.json"
            ).read_text()
        )
        self.assertEqual(manifest["project_id"], "arxiv-daily-push")
        self.assertEqual(manifest["task_id"], "GOV-SEMANTIC-ADP-001")
        self.assertEqual(manifest["coverage_status"], "in_progress")
        self.assertEqual(manifest["semantic_parameters_checked"], 72)
        self.assertEqual(manifest["human_review_required_parameters"], 80)
        self.assertEqual(manifest["semantic_formulas_checked"], 31)
        self.assertEqual(manifest["human_review_required_formulas"], 0)

    def test_arxiv_daily_push_semantic_extract_manifest_records_narrowed_coverage(self) -> None:
        manifest = json.loads(
            (
                ROOT
                / "governance"
                / "run_manifests"
                / "GOV-SEMANTIC-ADP-EXTRACT-003.json"
            ).read_text()
        )
        self.assertEqual(manifest["project_id"], "arxiv-daily-push")
        self.assertEqual(manifest["task_id"], "GOV-SEMANTIC-ADP-001")
        self.assertEqual(manifest["coverage_status"], "in_progress")
        self.assertEqual(manifest["semantic_parameters_checked"], 93)
        self.assertEqual(manifest["human_review_required_parameters"], 59)
        self.assertEqual(manifest["semantic_formulas_checked"], 31)
        self.assertEqual(manifest["human_review_required_formulas"], 0)

    def test_arxiv_daily_push_semantic_extract_manifest_records_reduced_coverage(self) -> None:
        manifest = json.loads(
            (
                ROOT
                / "governance"
                / "run_manifests"
                / "GOV-SEMANTIC-ADP-EXTRACT-004.json"
            ).read_text()
        )
        self.assertEqual(manifest["project_id"], "arxiv-daily-push")
        self.assertEqual(manifest["task_id"], "GOV-SEMANTIC-ADP-001")
        self.assertEqual(manifest["coverage_status"], "in_progress")
        self.assertEqual(manifest["semantic_parameters_checked"], 131)
        self.assertEqual(manifest["human_review_required_parameters"], 21)
        self.assertEqual(manifest["semantic_formulas_checked"], 31)
        self.assertEqual(manifest["human_review_required_formulas"], 0)

    def test_arxiv_daily_push_semantic_extract_manifest_records_machine_verified_coverage(self) -> None:
        manifest = json.loads(
            (
                ROOT
                / "governance"
                / "run_manifests"
                / "GOV-SEMANTIC-ADP-EXTRACT-005.json"
            ).read_text()
        )
        self.assertEqual(manifest["project_id"], "arxiv-daily-push")
        self.assertEqual(manifest["task_id"], "GOV-SEMANTIC-ADP-001")
        self.assertEqual(manifest["coverage_status"], "machine_verified")
        self.assertEqual(manifest["semantic_parameters_checked"], 152)
        self.assertEqual(manifest["human_review_required_parameters"], 0)
        self.assertEqual(manifest["semantic_formulas_checked"], 31)
        self.assertEqual(manifest["human_review_required_formulas"], 0)

    def test_review6_final_information_quality_gate_passes(self) -> None:
        quality = load_information_quality_module()
        result = quality.run()
        self.assertEqual(result["status"], "PASS", result)
        self.assertEqual(result["errors"], 0, result)

    def test_review6_final_all_projects_have_assurance_status(self) -> None:
        validator = load_validator_module()
        config = validator.load_yaml(ROOT / "governance" / "projects.yaml")
        projects = [project for project in validator.as_list(config.get("projects")) if isinstance(project, dict)]
        self.assertEqual(len(projects), 10)
        for project in projects:
            path = ROOT / project["path"] / "docs" / "governance" / "ASSURANCE_STATUS.yaml"
            self.assertTrue(path.is_file(), path)
            data = validator.load_yaml(path)
            self.assertEqual(data["project_id"], project["project_id"])
            self.assertRegex(data["source_base_commit"], r"^[0-9a-f]{40}$")
            self.assertRegex(data["source_snapshot_hash"], r"^sha256:[0-9a-f]{64}$")

    def test_review6_final_generated_views_have_real_metadata(self) -> None:
        paths = [ROOT / "README.md", ROOT / "GOVERNANCE_DASHBOARD.md", ROOT / "OWNER_PORTFOLIO.md"]
        for path in paths:
            text = path.read_text(encoding="utf-8")
            self.assertIn("source_base_commit", text)
            self.assertIn("source_snapshot_hash", text)
            self.assertIn("generator_version", text)
            self.assertNotIn("DETERMINISTIC_GENERATION", text)
            self.assertNotIn("CURRENT_CHECKOUT", text)


if __name__ == "__main__":
    unittest.main()
