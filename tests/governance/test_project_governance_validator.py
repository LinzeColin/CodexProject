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
        self.assertIn("validate_project_governance.py is missing", payload.get("reason", ""))

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
        self.assertEqual(first["generated_at"], second["generated_at"])
        self.assertEqual(first["commit"], second["commit"])
        self.assertEqual(first["outputs"], second["outputs"])
        owner_outputs = [path for path in first["outputs"] if path.endswith("/docs/governance/OWNER_STATUS.md")]
        status_outputs = [path for path in first["outputs"] if path.endswith("/docs/governance/STATUS.md")]
        self.assertEqual(len(owner_outputs), len(status_outputs))
        self.assertIn("PFI/大数据模拟器/docs/governance/OWNER_STATUS.md", owner_outputs)
        rendered = dashboard.render_dashboard([dashboard.load_project(project) for project in dashboard.structural.load_yaml(ROOT / "governance" / "projects.yaml")["projects"]], "CURRENT_CHECKOUT", "DETERMINISTIC_GENERATION")
        self.assertIn("Semantic coverage", rendered)
        self.assertIn("machine_verified", rendered)
        self.assertIn("planned", rendered)

    def test_review6_owner_status_is_readable_and_prioritized(self) -> None:
        dashboard = load_dashboard_module()
        config = dashboard.structural.load_yaml(ROOT / "governance" / "projects.yaml")
        serenity = next(project for project in config["projects"] if project["project_id"] == "Serenity-Alipay")
        info = dashboard.load_project(serenity)
        rendered = dashboard.render_owner_status(info, "CURRENT_CHECKOUT", "DETERMINISTIC_GENERATION")
        for marker in (
            "## 1. 当前结论",
            "## 4. 模型、公式、参数旧值到新值",
            "## 8. 需要项目所有者决定的事项",
            "## 10. 下一项可执行任务及 Acceptance",
            "## 12. UNKNOWN 与过期证据数量",
        ):
            self.assertIn(marker, rendered)
        self.assertIn("语义覆盖", rendered)
        self.assertIn("machine_verified", rendered)
        self.assertNotIn("['", rendered)
        self.assertNotIn("{'", rendered)
        self.assertEqual(info["next_task"], "TASK-B-001")

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


if __name__ == "__main__":
    unittest.main()
