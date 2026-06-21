from __future__ import annotations

import importlib.util
import json
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
            ".agents/skills/codex-dex/SKILL.md",
            ".codex/config.template.toml",
            ".codex/hooks.json",
            ".codex/hooks/governance_stop.py",
            ".github/workflows/project-governance.yml",
            "scripts/validate_project_governance.py",
        }:
            self.assertIn(path, required)
            self.assertTrue((ROOT / path).is_file(), path)

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

    def test_review5_dashboard_generation_is_deterministic(self) -> None:
        result = run_validator("--all")
        self.assertEqual(result.returncode, 0, result.stdout)
        dashboard = load_dashboard_module()
        first = dashboard.generate(write=False)
        second = dashboard.generate(write=False)
        self.assertEqual(first["generated_at"], second["generated_at"])
        self.assertEqual(first["commit"], second["commit"])
        self.assertEqual(first["outputs"], second["outputs"])

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


if __name__ == "__main__":
    unittest.main()
