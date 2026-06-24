from __future__ import annotations

import contextlib
import csv
import importlib.util
import io
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from collections import Counter
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


def load_lean_governance_module():
    scripts_dir = str(ROOT / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    spec = importlib.util.spec_from_file_location("lean_governance", ROOT / "scripts" / "lean_governance.py")
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
            "scripts/lean_governance.py",
            "governance/schemas/project.schema.json",
            "governance/schemas/roadmap.schema.json",
            "governance/schemas/events.schema.json",
            "docs/governance/templates/功能清单.template.md",
            "docs/governance/templates/开发记录.template.md",
            "docs/governance/templates/模型参数文件.template.md",
            "docs/governance/templates/Roadmap.template.md",
            "governance/schemas/ci_attestation.schema.json",
        }:
            self.assertIn(path, required)
            self.assertTrue((ROOT / path).is_file(), path)

    def test_review9_s2_project_schema_declares_lean_v2_fact_contract(self) -> None:
        schema = json.loads((ROOT / "governance" / "schemas" / "project.schema.json").read_text(encoding="utf-8"))
        self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
        self.assertEqual(schema["properties"]["schema_version"]["const"], "codexproject.project.v1")
        self.assertFalse(schema["additionalProperties"])
        for required in {
            "features",
            "models",
            "assumptions",
            "formulas",
            "parameters",
            "strategies",
            "validations",
            "evidence_refs",
        }:
            self.assertIn(required, schema["required"])
            self.assertIn(required, schema["properties"])
        for definition in {
            "feature",
            "model",
            "assumption",
            "formula",
            "parameter",
            "strategy",
            "validation",
            "evidence_ref",
        }:
            self.assertIn(definition, schema["$defs"])
        self.assertIn("UNKNOWN", schema["$defs"]["fact_level"]["enum"])
        self.assertIn("VERIFIED", schema["$defs"]["fact_level"]["enum"])

    def test_review9_s2_roadmap_schema_declares_stage_phase_task_contract(self) -> None:
        schema = json.loads((ROOT / "governance" / "schemas" / "roadmap.schema.json").read_text(encoding="utf-8"))
        self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
        self.assertEqual(schema["properties"]["schema_version"]["const"], "codexproject.roadmap.v1")
        self.assertEqual(schema["properties"]["roadmap_kind"]["const"], "product")
        self.assertFalse(schema["additionalProperties"])
        for required in {
            "roadmap_kind",
            "total_estimated_hours",
            "current_stage_id",
            "current_phase_id",
            "current_task_id",
            "stages",
        }:
            self.assertIn(required, schema["required"])
        self.assertEqual(schema["properties"]["current_stage_id"]["pattern"], "^S[1-9][0-9]*$")
        self.assertEqual(schema["properties"]["current_phase_id"]["pattern"], "^S[1-9][0-9]*P[A-Z]$")
        self.assertEqual(schema["properties"]["current_task_id"]["pattern"], "^S[1-9][0-9]*P[A-Z]T[0-9]{2}$")
        for definition in {"stage", "phase", "task", "stop_gate", "acceptance"}:
            self.assertIn(definition, schema["$defs"])
        for definition in ("stage", "phase", "task"):
            required_fields = set(schema["$defs"][definition]["required"])
            self.assertIn("estimated_hours", required_fields)
            self.assertIn("estimated_pct", required_fields)
        self.assertIn("stop_conditions", schema["$defs"]["stage"]["required"])
        self.assertIn("stop_gate", schema["$defs"]["phase"]["required"])
        self.assertIn("acceptance_ids", schema["$defs"]["task"]["required"])
        self.assertIn("rollback", schema["$defs"]["task"]["required"])

    def test_review9_s2_events_schema_declares_meaningful_event_contract(self) -> None:
        schema = json.loads((ROOT / "governance" / "schemas" / "events.schema.json").read_text(encoding="utf-8"))
        self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
        self.assertEqual(schema["properties"]["schema_version"]["const"], "codexproject.event.v1")
        self.assertFalse(schema["additionalProperties"])
        for required in {
            "event_id",
            "project_id",
            "occurred_at",
            "event_type",
            "summary",
            "fact_level",
            "task_id",
            "acceptance_ids",
            "changed_files",
            "evidence_refs",
        }:
            self.assertIn(required, schema["required"])
        self.assertEqual(schema["properties"]["task_id"]["pattern"], "^S[1-9][0-9]*P[A-Z]T[0-9]{2}$")
        for event_type in {
            "decision",
            "implementation",
            "validation",
            "migration",
            "release",
            "incident",
            "owner_acceptance",
            "evidence_update",
            "rollback",
        }:
            self.assertIn(event_type, schema["properties"]["event_type"]["enum"])
        self.assertEqual(
            set(schema["$defs"]["fact_level"]["enum"]),
            {"VERIFIED", "RECONSTRUCTED", "PROPOSED", "UNKNOWN"},
        )
        evidence_ref = schema["$defs"]["evidence_ref"]
        self.assertIn("kind", evidence_ref["required"])
        self.assertIn("fact_level", evidence_ref["required"])
        self.assertIn("unknown", evidence_ref["properties"]["kind"]["enum"])

    def test_review9_s2_human_entry_templates_are_owner_readable(self) -> None:
        feature_text = (ROOT / "docs" / "governance" / "templates" / "功能清单.template.md").read_text(
            encoding="utf-8"
        )
        model_text = (ROOT / "docs" / "governance" / "templates" / "模型参数文件.template.md").read_text(
            encoding="utf-8"
        )
        for required in {
            "project_id",
            "product_version",
            "current_stage",
            "current_phase",
            "current_task",
            "blockers",
            "next_gate",
            "next_unique_task",
            "evidence_status",
        }:
            self.assertIn(required, feature_text[:600])
            self.assertIn(required, model_text[:700])
        feature_order = ["## 摘要", "## Owner 决策", "## 功能概览", "## 证据", "## 限制与风险", "## 功能详情"]
        model_order = ["## 摘要", "## 证据", "## 限制与未知", "## 模型", "## 公式", "## 参数", "## 验证"]
        self.assertEqual(
            [feature_text.index(item) for item in feature_order],
            sorted(feature_text.index(item) for item in feature_order),
        )
        self.assertEqual(
            [model_text.index(item) for item in model_order],
            sorted(model_text.index(item) for item in model_order),
        )
        for text in (feature_text, model_text):
            self.assertNotIn("兼容索引", text)
            self.assertNotIn("详见 docs/governance", text)
            self.assertNotIn("link page", text.lower())

    def test_review9_git_changed_files_decodes_utf8_paths(self) -> None:
        validator = load_validator_module()
        with patch.object(validator, "explicit_base_ref", return_value=None), patch.object(
            validator, "git_ref_exists", return_value=False
        ), patch.object(
            validator.subprocess,
            "check_output",
            return_value="docs/governance/templates/功能清单.template.md\n",
        ) as check_output:
            self.assertEqual(validator.git_changed_files(), ["docs/governance/templates/功能清单.template.md"])
        self.assertTrue(check_output.called)
        for call in check_output.call_args_list:
            self.assertEqual(call.kwargs.get("encoding"), "utf-8")
            self.assertTrue(call.kwargs.get("text"))

    def test_review9_s2_dev_record_and_roadmap_templates_are_owner_readable(self) -> None:
        dev_text = (ROOT / "docs" / "governance" / "templates" / "开发记录.template.md").read_text(
            encoding="utf-8"
        )
        roadmap_text = (ROOT / "docs" / "governance" / "templates" / "Roadmap.template.md").read_text(
            encoding="utf-8"
        )
        for required in {
            "project_id",
            "product_version",
            "current_stage",
            "current_phase",
            "current_task",
            "blockers",
            "next_gate",
            "next_unique_task",
            "evidence_status",
        }:
            self.assertIn(required, dev_text[:700])
            self.assertIn(required, roadmap_text[:700])
        dev_order = ["## 摘要", "## Owner 决策", "## 进度总览", "## Roadmap", "## 近期事件", "## 风险与阻塞"]
        roadmap_order = ["## 摘要", "## 计算规则", "## Stages", "## Phases", "## Tasks", "## Stop Gates", "## Acceptance And Evidence"]
        self.assertEqual(
            [dev_text.index(item) for item in dev_order],
            sorted(dev_text.index(item) for item in dev_order),
        )
        self.assertEqual(
            [roadmap_text.index(item) for item in roadmap_order],
            sorted(roadmap_text.index(item) for item in roadmap_order),
        )
        for text in (dev_text, roadmap_text):
            self.assertIn("Stage -> Phase -> Task", text)
            self.assertIn("stop_gate", text)
            self.assertIn("evidence_refs", text)
            self.assertNotIn("兼容索引", text)
            self.assertNotIn("详见 docs/governance", text)
            self.assertNotIn("link page", text.lower())

    def test_review9_s3_baseline_all_is_read_only_compact_json(self) -> None:
        cli = load_lean_governance_module()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            project_path = tmp_path / "ProjectA"
            governance_path = tmp_path / "governance"
            project_governance_path = project_path / "docs" / "governance"
            governance_path.mkdir(parents=True)
            project_governance_path.mkdir(parents=True)
            (tmp_path / "AGENTS.md").write_text("root contract\n", encoding="utf-8")
            (project_path / "功能清单").write_text("features\n", encoding="utf-8")
            (project_path / "开发记录").write_text("roadmap\n", encoding="utf-8")
            (project_path / "模型参数文件").write_text("models\n", encoding="utf-8")
            (project_path / "VERSION").write_text("0.1.0\n", encoding="utf-8")
            (project_path / "CHANGELOG.md").write_text("change\n", encoding="utf-8")
            (project_governance_path / "project.yaml").write_text("project_id: ProjectA\n", encoding="utf-8")
            projects_yaml = governance_path / "projects.yaml"
            projects_yaml.write_text(
                "\n".join(
                    [
                        "root_governance:",
                        "  ci_mode: required",
                        "  required_files:",
                        "    - AGENTS.md",
                        "project_governance_files:",
                        "  - docs/governance/MODEL_SPEC.md",
                        "projects:",
                        "  - project_id: ProjectA",
                        "    path: ProjectA",
                        "    ci_mode: advisory",
                        "    migration:",
                        "      version: legacy-v1-pending-lean-v2",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            before = sorted(path.relative_to(tmp_path).as_posix() for path in tmp_path.rglob("*"))
            stream = io.StringIO()
            with patch.object(cli, "ROOT", tmp_path), patch.object(cli, "PROJECTS_FILE", projects_yaml):
                with contextlib.redirect_stdout(stream):
                    self.assertEqual(cli.main(["baseline", "--all"]), 0)
            after = sorted(path.relative_to(tmp_path).as_posix() for path in tmp_path.rglob("*"))
        self.assertEqual(before, after)
        summary = json.loads(stream.getvalue())
        self.assertEqual(summary["command"], "baseline")
        self.assertEqual(summary["scope"], "all")
        self.assertEqual(summary["totals"]["projects"], 1)
        self.assertEqual(summary["totals"]["human_entry_missing"], 0)
        self.assertEqual(summary["totals"]["canonical_missing"], 2)
        self.assertEqual(summary["projects"][0]["project_id"], "ProjectA")

    def test_review9_s3_validate_cli_reuses_existing_rules_and_exit_codes(self) -> None:
        cli = load_lean_governance_module()
        with patch.object(cli.governance, "main", return_value=7) as validator_main:
            self.assertEqual(
                cli.main(["validate", "--all", "--semantic", "--enforce-sync", "--base-ref", "origin/main"]),
                7,
            )
        validator_main.assert_called_once_with(["--all", "--base-ref", "origin/main", "--enforce-sync", "--semantic"])

    def test_review9_s3_validate_cli_defaults_to_changed_only(self) -> None:
        cli = load_lean_governance_module()
        with patch.object(cli.governance, "main", return_value=0) as validator_main:
            self.assertEqual(cli.main(["validate"]), 0)
        validator_main.assert_called_once_with(["--changed-only"])

    def test_review9_s3_changed_scope_root_change_selects_all_projects(self) -> None:
        cli = load_lean_governance_module()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            projects_yaml = tmp_path / "governance" / "projects.yaml"
            projects_yaml.parent.mkdir(parents=True)
            projects_yaml.write_text(
                "\n".join(
                    [
                        "root_governance:",
                        "  required_files:",
                        "    - scripts/lean_governance.py",
                        "projects:",
                        "  - project_id: A",
                        "    path: A",
                        "    ci_mode: advisory",
                        "  - project_id: B",
                        "    path: B",
                        "    ci_mode: advisory",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            with patch.object(cli.governance, "git_changed_files", return_value=["scripts/lean_governance.py"]):
                scope = cli.build_changed_scope("origin/main", tmp_path, projects_yaml)
        self.assertTrue(scope["root_governance_changed"])
        self.assertTrue(scope["all_projects_required"])
        self.assertEqual(scope["selected_project_count"], 2)
        self.assertEqual([project["project_id"] for project in scope["selected_projects"]], ["A", "B"])

    def test_other8_s2pct01_root_change_respects_configured_project_exclusions(self) -> None:
        cli = load_lean_governance_module()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            projects_yaml = tmp_path / "governance" / "projects.yaml"
            projects_yaml.parent.mkdir(parents=True)
            projects_yaml.write_text(
                "\n".join(
                    [
                        "root_governance:",
                        "  changed_scope_excluded_projects:",
                        "    - EEI",
                        "    - arxiv-daily-push",
                        "  required_files:",
                        "    - scripts/lean_governance.py",
                        "projects:",
                        "  - project_id: A",
                        "    path: A",
                        "    ci_mode: required",
                        "  - project_id: EEI",
                        "    path: EEI",
                        "    ci_mode: required",
                        "  - project_id: arxiv-daily-push",
                        "    path: arxiv-daily-push",
                        "    ci_mode: required",
                        "  - project_id: B",
                        "    path: B",
                        "    ci_mode: required",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            with patch.object(cli.governance, "git_changed_files", return_value=["scripts/lean_governance.py"]):
                scope = cli.build_changed_scope("origin/main", tmp_path, projects_yaml)
        self.assertTrue(scope["root_governance_changed"])
        self.assertFalse(scope["all_projects_required"])
        self.assertEqual(scope["root_scope_excluded_projects"], ["EEI", "arxiv-daily-push"])
        self.assertEqual([project["project_id"] for project in scope["selected_projects"]], ["A", "B"])

    def test_other8_s2pct01_current_root_test_change_excludes_parallel_projects(self) -> None:
        cli = load_lean_governance_module()
        with patch.object(cli.governance, "git_changed_files", return_value=["tests/governance/test_project_governance_validator.py"]):
            scope = cli.build_changed_scope("origin/main", ROOT, ROOT / "governance" / "projects.yaml")
        selected_ids = {project["project_id"] for project in scope["selected_projects"]}
        self.assertTrue(scope["root_governance_changed"])
        self.assertFalse(scope["all_projects_required"])
        self.assertEqual(scope["selected_project_count"], 8)
        self.assertNotIn("EEI", selected_ids)
        self.assertNotIn("arxiv-daily-push", selected_ids)

    def test_review9_s3_changed_scope_project_change_selects_only_matching_project(self) -> None:
        cli = load_lean_governance_module()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            projects_yaml = tmp_path / "governance" / "projects.yaml"
            projects_yaml.parent.mkdir(parents=True)
            projects_yaml.write_text(
                "\n".join(
                    [
                        "root_governance:",
                        "  required_files:",
                        "    - AGENTS.md",
                        "projects:",
                        "  - project_id: A",
                        "    path: A",
                        "    ci_mode: advisory",
                        "  - project_id: B",
                        "    path: nested/B",
                        "    ci_mode: advisory",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            with patch.object(cli.governance, "git_changed_files", return_value=["nested/B/app.py"]):
                scope = cli.build_changed_scope("origin/main", tmp_path, projects_yaml)
        self.assertFalse(scope["root_governance_changed"])
        self.assertFalse(scope["all_projects_required"])
        self.assertEqual(scope["selected_project_count"], 1)
        self.assertEqual(scope["selected_projects"][0]["project_id"], "B")

    def test_review9_s3_renderer_writes_only_with_explicit_write_and_computes_percentages(self) -> None:
        cli = load_lean_governance_module()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            project_root = tmp_path / "ProjectA"
            governance_root = project_root / "docs" / "governance"
            governance_root.mkdir(parents=True)
            (tmp_path / "governance").mkdir()
            (tmp_path / "governance" / "projects.yaml").write_text(
                "\n".join(
                    [
                        "projects:",
                        "  - project_id: ProjectA",
                        "    path: ProjectA",
                        "    ci_mode: advisory",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            (governance_root / "project.yaml").write_text(
                "\n".join(
                    [
                        "schema_version: codexproject.project.v1",
                        "project_id: ProjectA",
                        "project_name: Project A",
                        "summary: Test project",
                        "version: 0.1.0",
                        "fact_level: VERIFIED",
                        "features:",
                        "  - feature_id: FEAT-A",
                        "    name: Feature A",
                        "    description: Owner value",
                        "    status: active",
                        "    fact_level: VERIFIED",
                        "    evidence_refs: [EVID-A]",
                        "models:",
                        "  - model_id: MOD-A",
                        "    name: Model A",
                        "    purpose: Score",
                        "    status: active",
                        "    fact_level: VERIFIED",
                        "    formula_ids: [FORM-A]",
                        "    parameter_ids: [PARAM-A]",
                        "    evidence_refs: [EVID-A]",
                        "formulas:",
                        "  - formula_id: FORM-A",
                        "    model_id: MOD-A",
                        "    description: Score formula",
                        "    status: active",
                        "    fact_level: VERIFIED",
                        "    expression: x * w",
                        "    variables: []",
                        "    evidence_refs: [EVID-A]",
                        "parameters:",
                        "  - parameter_id: PARAM-A",
                        "    symbol: w",
                        "    name: Weight",
                        "    status: active",
                        "    fact_level: VERIFIED",
                        "    value: 2",
                        "    source: owner",
                        "    evidence_refs: [EVID-A]",
                        "evidence_refs:",
                        "  - evidence_id: EVID-A",
                        "    kind: owner",
                        "    ref: owner-note",
                        "    fact_level: VERIFIED",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            (governance_root / "roadmap.yaml").write_text(
                "\n".join(
                    [
                        "schema_version: codexproject.roadmap.v1",
                        "roadmap_kind: product",
                        "project_id: ProjectA",
                        "total_estimated_hours: 999",
                        "current_stage_id: S1",
                        "current_phase_id: S1PA",
                        "current_task_id: S1PAT02",
                        "next_gate_id: S1-GATE",
                        "stages:",
                        "  - stage_id: S1",
                        "    name: Stage One",
                        "    person_goal: Ship",
                        "    status: in_progress",
                        "    estimated_hours: 999",
                        "    estimated_pct: 99",
                        "    stop_conditions: [stop]",
                        "    stop_gate:",
                        "      gate_id: S1-GATE",
                        "      pass_criteria: [pass]",
                        "      evidence: [EVID-A]",
                        "      failure_action: blocked",
                        "    phases:",
                        "      - phase_id: S1PA",
                        "        name: Phase A",
                        "        objective: Do work",
                        "        status: in_progress",
                        "        estimated_hours: 999",
                        "        estimated_pct: 99",
                        "        stop_conditions: [stop]",
                        "        stop_gate:",
                        "          gate_id: S1PA-GATE",
                        "          pass_criteria: [pass]",
                        "          evidence: [EVID-A]",
                        "          failure_action: remain_in_phase",
                        "        tasks:",
                        "          - task_id: S1PAT01",
                        "            name: Done",
                        "            objective: Finish first",
                        "            status: completed",
                        "            estimated_hours: 1",
                        "            estimated_pct: 99",
                        "            dependencies: [none]",
                        "            acceptance_ids: [ACC-A]",
                        "            acceptance: []",
                        "            test_commands: [test]",
                        "            test_results: [pass]",
                        "            evidence_refs: [EVID-A]",
                        "            risks: [none]",
                        "            rollback: revert",
                        "          - task_id: S1PAT02",
                        "            name: Next",
                        "            objective: Finish next",
                        "            status: planned",
                        "            estimated_hours: 3",
                        "            estimated_pct: 99",
                        "            dependencies: [S1PAT01]",
                        "            acceptance_ids: [ACC-B]",
                        "            acceptance: []",
                        "            test_commands: [test]",
                        "            test_results: [pending]",
                        "            evidence_refs: [EVID-A]",
                        "            risks: [none]",
                        "            rollback: revert",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            (governance_root / "events.jsonl").write_text(
                json.dumps(
                    {
                        "schema_version": "codexproject.event.v1",
                        "event_id": "EVT-A",
                        "project_id": "ProjectA",
                        "occurred_at": "2026-06-23T00:00:00Z",
                        "event_type": "implementation",
                        "summary": "Implemented",
                        "fact_level": "VERIFIED",
                        "task_id": "S1PAT01",
                        "acceptance_ids": ["ACC-A"],
                        "changed_files": ["ProjectA/app.py"],
                        "evidence_refs": [{"evidence_id": "EVID-A", "kind": "owner", "ref": "owner-note", "fact_level": "VERIFIED"}],
                    },
                    ensure_ascii=False,
                )
                + "\n",
                encoding="utf-8",
            )
            dry = cli.render_registered_project("ProjectA", write=False, root=tmp_path, projects_file=tmp_path / "governance" / "projects.yaml")
            self.assertFalse(dry["write"])
            for path in ("功能清单", "开发记录", "模型参数文件"):
                self.assertFalse((project_root / path).exists(), path)
            written = cli.render_registered_project("ProjectA", write=True, root=tmp_path, projects_file=tmp_path / "governance" / "projects.yaml")
            self.assertTrue(written["write"])
            dev_record = (project_root / "开发记录").read_text(encoding="utf-8")
        self.assertIn("progress: `25.00%`", dev_record)
        self.assertIn("| S1PAT02 | Next | planned | 3.00 | 75.00%", dev_record)

    def test_review9_s3_check_render_is_read_only_and_reports_drift_and_refs(self) -> None:
        cli = load_lean_governance_module()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            project_root = tmp_path / "ProjectA"
            governance_root = project_root / "docs" / "governance"
            governance_root.mkdir(parents=True)
            (governance_root / "project.yaml").write_text(
                "\n".join(
                    [
                        "schema_version: codexproject.project.v1",
                        "project_id: ProjectA",
                        "project_name: Project A",
                        "summary: Test project",
                        "version: 0.1.0",
                        "fact_level: VERIFIED",
                        "features:",
                        "  - feature_id: FEAT-A",
                        "    name: Feature A",
                        "    description: Owner value",
                        "    status: active",
                        "    fact_level: VERIFIED",
                        "    evidence_refs: [EVID-MISSING]",
                        "models: []",
                        "formulas: []",
                        "parameters: []",
                        "strategies: []",
                        "validations: []",
                        "evidence_refs: []",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            (governance_root / "roadmap.yaml").write_text(
                "\n".join(
                    [
                        "schema_version: codexproject.roadmap.v1",
                        "roadmap_kind: product",
                        "project_id: ProjectA",
                        "total_estimated_hours: 1",
                        "current_stage_id: S1",
                        "current_phase_id: S1PA",
                        "current_task_id: S1PAT01",
                        "next_gate_id: S1-GATE",
                        "stages:",
                        "  - stage_id: S1",
                        "    name: Stage One",
                        "    person_goal: Ship",
                        "    status: in_progress",
                        "    estimated_hours: 1",
                        "    estimated_pct: 100",
                        "    stop_conditions: [stop]",
                        "    stop_gate:",
                        "      gate_id: S1-GATE",
                        "      pass_criteria: [pass]",
                        "      evidence: [EVID-MISSING]",
                        "      failure_action: blocked",
                        "    phases:",
                        "      - phase_id: S1PA",
                        "        name: Phase A",
                        "        objective: Do work",
                        "        status: in_progress",
                        "        estimated_hours: 1",
                        "        estimated_pct: 100",
                        "        stop_conditions: [stop]",
                        "        stop_gate:",
                        "          gate_id: S1PA-GATE",
                        "          pass_criteria: [pass]",
                        "          evidence: [EVID-MISSING]",
                        "          failure_action: remain_in_phase",
                        "        tasks:",
                        "          - task_id: S1PAT01",
                        "            name: Task",
                        "            objective: Finish",
                        "            status: planned",
                        "            estimated_hours: 1",
                        "            estimated_pct: 100",
                        "            dependencies: [none]",
                        "            acceptance_ids: [ACC-A]",
                        "            acceptance: []",
                        "            test_commands: [test]",
                        "            test_results: [pending]",
                        "            evidence_refs: [EVID-MISSING]",
                        "            risks: [none]",
                        "            rollback: revert",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            cli.render_project_files(project_root, write=True)
            before = (project_root / "开发记录").read_text(encoding="utf-8")
            clean = cli.check_render_project_files(project_root)
            (project_root / "开发记录").write_text(before + "\nmanual drift\n", encoding="utf-8")
            drifted = cli.check_render_project_files(project_root)
            after = (project_root / "开发记录").read_text(encoding="utf-8")
        self.assertEqual(clean["drift_count"], 0)
        self.assertEqual(clean["reference_issue_count"], 1)
        self.assertEqual(drifted["drift_count"], 1)
        self.assertEqual(after, before + "\nmanual drift\n")

    def test_review9_s3_ci_changed_only_orchestrates_read_only_gates(self) -> None:
        cli = load_lean_governance_module()
        baseline = {
            "totals": {
                "projects": 1,
                "human_entry_missing": 0,
                "canonical_missing": 0,
                "legacy_governance_missing": 0,
            }
        }
        scope = {
            "selected_projects": [
                {
                    "project_id": "ProjectA",
                    "path": "ProjectA",
                    "ci_mode": "required",
                }
            ]
        }
        check_render = {
            "write": False,
            "drift": [],
            "drift_count": 0,
            "reference_issues": [],
            "reference_issue_count": 0,
        }
        with (
            patch.object(cli, "build_baseline", return_value=baseline) as build_baseline,
            patch.object(cli, "build_changed_scope", return_value=scope) as build_changed_scope,
            patch.object(cli, "has_check_render_inputs", return_value=True),
            patch.object(cli, "check_render_project_files", return_value=check_render) as check_render_project,
            patch.object(cli, "git_status_porcelain", return_value=[]),
            patch.object(cli.governance, "main", return_value=0) as validator_main,
        ):
            exit_code, summary = cli.run_changed_only_ci("BASE", root=Path("root"), projects_file=Path("projects.yaml"))

        self.assertEqual(exit_code, 0)
        build_baseline.assert_called_once_with(Path("root"), Path("projects.yaml"))
        build_changed_scope.assert_called_once_with("BASE", Path("root"), Path("projects.yaml"))
        validator_main.assert_called_once_with(["--changed-only", "--enforce-sync", "--semantic", "--base-ref", "BASE"])
        check_render_project.assert_called_once_with(Path("root") / "ProjectA")
        self.assertFalse(summary["write"])
        self.assertTrue(summary["zero_diff"]["clean"])
        self.assertEqual(summary["check_render"]["checked_count"], 1)
        self.assertEqual(summary["budget_telemetry"]["mode"], "changed-only-fast-gate")
        self.assertEqual(summary["budget_telemetry"]["semantic_scope"], "changed-only")
        self.assertEqual(summary["budget_telemetry"]["selected_project_count"], 1)
        self.assertEqual(summary["budget_telemetry"]["total_project_count"], 1)
        self.assertEqual(summary["budget_telemetry"]["full_governance_location"], "schedule_or_workflow_dispatch_all")

    def test_review9_s3_ci_changed_only_skips_unmigrated_check_render(self) -> None:
        cli = load_lean_governance_module()
        baseline = {
            "totals": {
                "projects": 1,
                "human_entry_missing": 0,
                "canonical_missing": 2,
                "legacy_governance_missing": 0,
            }
        }
        scope = {
            "selected_projects": [
                {
                    "project_id": "LegacyProject",
                    "path": "LegacyProject",
                    "ci_mode": "advisory",
                }
            ]
        }
        with (
            patch.object(cli, "build_baseline", return_value=baseline),
            patch.object(cli, "build_changed_scope", return_value=scope),
            patch.object(cli, "has_check_render_inputs", return_value=False),
            patch.object(cli, "check_render_project_files") as check_render_project,
            patch.object(cli, "git_status_porcelain", return_value=[]),
            patch.object(cli.governance, "main", return_value=0),
        ):
            exit_code, summary = cli.run_changed_only_ci("BASE", root=Path("root"), projects_file=Path("projects.yaml"))

        self.assertEqual(exit_code, 0)
        check_render_project.assert_not_called()
        self.assertEqual(summary["check_render"]["checked_count"], 0)
        self.assertEqual(summary["check_render"]["skipped_count"], 1)
        self.assertEqual(summary["check_render"]["skipped"][0]["reason"], "missing_lean_canonical_facts")
        self.assertEqual(summary["budget_telemetry"]["check_render_checked_count"], 0)
        self.assertEqual(summary["budget_telemetry"]["check_render_skipped_count"], 1)

    def test_review9_s4pat01_serenity_evidence_index_bounds_read_scope(self) -> None:
        validator = load_validator_module()
        path = ROOT / "Serenity-Alipay" / "docs" / "governance" / "evidence_index.yaml"
        data = validator.load_yaml(path)
        self.assertEqual(data["schema_version"], "codexproject.evidence_index.v1")
        self.assertEqual(data["project_id"], "Serenity-Alipay")
        self.assertEqual(data["task_id"], "S4PAT01")
        self.assertEqual(data["acceptance_id"], "ACC-S4PAT01")

        read_scope = data["read_scope"]
        self.assertEqual(read_scope["mode"], "bounded_pilot_read")
        for category in {
            "README_and_handoff",
            "existing_governance",
            "model_implementation",
            "runtime_config",
            "focused_tests",
            "limited_related_git_history",
        }:
            self.assertIn(category, read_scope["allowed_categories"])
        for forbidden in {
            "business_behavior_changes",
            "broad_git_history_mining",
            "generated_output_archives",
        }:
            self.assertIn(forbidden, read_scope["excluded_categories"])

        refs: set[str] = set()
        evidence_ids: set[str] = set()
        for item in data["evidence_refs"]:
            evidence_ids.add(item["evidence_id"])
            refs.update(item.get("refs", []))
        for required_id in {
            "EVID-SER-README-HANDOFF",
            "EVID-SER-EXISTING-GOVERNANCE",
            "EVID-SER-SCORING-CODE",
            "EVID-SER-RANKING-CODE",
            "EVID-SER-METRICS-CODE",
            "EVID-SER-COMPARISON-DISCIPLINE-CODE",
            "EVID-SER-SCHEDULER-CODE",
            "EVID-SER-LIMITED-HISTORY",
        }:
            self.assertIn(required_id, evidence_ids)
        for required_ref in {
            "Serenity-Alipay/README.md",
            "Serenity-Alipay/HANDOFF.md",
            "Serenity-Alipay/docs/governance/MODEL_SPEC.md",
            "Serenity-Alipay/docs/governance/model_registry.yaml",
            "Serenity-Alipay/docs/governance/formula_registry.yaml",
            "Serenity-Alipay/docs/governance/parameter_registry.csv",
            "Serenity-Alipay/app/core/scoring.py",
            "Serenity-Alipay/app/core/pipeline.py",
            "Serenity-Alipay/app/core/metrics.py",
            "Serenity-Alipay/app/core/comparison.py",
            "Serenity-Alipay/app/core/discipline.py",
            "Serenity-Alipay/app/scheduler.py",
            "Serenity-Alipay/app/core/scheduler_runner.py",
            "Serenity-Alipay/app/core/automation_tick.py",
            "Serenity-Alipay/app/config.py",
            "Serenity-Alipay/tests/test_pipeline_serenity_priority.py",
        }:
            self.assertIn(required_ref, refs)
        for ref in refs:
            self.assertTrue((ROOT / ref).exists(), ref)

        self.assertEqual(
            set(data["model_fact_targets"]["active_model_ids"]),
            {"MOD-001", "MOD-002", "MOD-003", "MOD-004", "MOD-005"},
        )
        self.assertEqual(data["model_fact_targets"]["extraction_task_id"], "S4PAT02")
        watchlist = data["contradiction_watchlist"]
        self.assertEqual(watchlist[0]["issue_id"], "S4PAT01-WATCH-FORM-008-CAP")
        self.assertEqual(watchlist[0]["followup_task_id"], "S4PAT02")
        self.assertIn("0.30", watchlist[0]["summary"])
        self.assertIn("no_technology_stack_as_model_parameter", data["fact_policy"]["forbidden_claims"])
        self.assertIn("no_invented_iteration_or_hours", data["fact_policy"]["forbidden_claims"])
        self.assertFalse(data["acceptance"]["stop_conditions_checked"]["code_doc_contradiction_unmarked"])

    def test_review9_s4pat01_manifest_records_bounded_pilot_scope(self) -> None:
        manifest = json.loads(
            (
                ROOT
                / "governance"
                / "run_manifests"
                / "GOV-REVIEW9-S4PAT01-EVIDENCE-INDEX-20260623.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(manifest["project_id"], "Serenity-Alipay")
        self.assertEqual(manifest["task_id"], "S4PAT01")
        self.assertEqual(manifest["acceptance_ids"], ["ACC-S4PAT01"])
        self.assertEqual(manifest["binding_status"], "PRECOMMIT_TREE_BOUND")
        self.assertIn("bounded_evidence_index", manifest["change_classification"])
        self.assertIn("no_business_behavior_change", manifest["change_classification"])
        self.assertTrue(str(manifest["content_tree_hash"]).startswith("sha256-changed-files-excluding-this-manifest:"))
        changed = set(manifest["changed_files_actual"])
        self.assertIn("Serenity-Alipay/docs/governance/evidence_index.yaml", changed)
        self.assertIn("tests/governance/test_project_governance_validator.py", changed)
        self.assertIn(
            "governance/run_manifests/GOV-REVIEW9-S4PAT01-EVIDENCE-INDEX-20260623.json",
            changed,
        )
        self.assertIn("Serenity-Alipay/docs/governance/formula_registry.yaml", manifest["evidence_refs"])
        self.assertIn("Serenity-Alipay/app/core/pipeline.py", manifest["evidence_refs"])
        self.assertIn("S4PAT02 still must extract formulas", " ".join(manifest["unresolved_risks"]))

    def test_review9_s4pat01_evidence_index_is_project_governance_only(self) -> None:
        sync = load_sync_module()
        project = {
            "project_id": "Serenity-Alipay",
            "path": "Serenity-Alipay",
            "model_behavior_globs": ["app/**/*.py", "tests/**/*.py"],
        }
        changes, _ = sync.classify_changes(
            {"projects": [project]},
            ["Serenity-Alipay/docs/governance/evidence_index.yaml"],
        )
        self.assertEqual(len(changes), 1)
        self.assertEqual(changes[0].classifications, {"governance_only_change"})
        self.assertEqual(changes[0].updated_governance_files, {"docs/governance/evidence_index.yaml"})
        validation = sync.SyncValidation()
        sync.validate_diff_contract(validation, changes)
        self.assertFalse(validation.errors)

    def test_review9_s4pat02_serenity_model_extraction_matches_registry(self) -> None:
        validator = load_validator_module()
        extraction = validator.load_yaml(ROOT / "Serenity-Alipay" / "docs" / "governance" / "model_extraction.yaml")
        registry = validator.load_yaml(ROOT / "Serenity-Alipay" / "docs" / "governance" / "model_registry.yaml")
        self.assertEqual(extraction["schema_version"], "codexproject.model_extraction.v1")
        self.assertEqual(extraction["project_id"], "Serenity-Alipay")
        self.assertEqual(extraction["task_id"], "S4PAT02")
        self.assertEqual(extraction["acceptance_id"], "ACC-S4PAT02")
        self.assertEqual(extraction["source_evidence_index_task_id"], "S4PAT01")
        self.assertEqual(extraction["coverage"]["active_model_count"], 5)
        self.assertEqual(extraction["coverage"]["active_formula_count"], 12)
        self.assertEqual(extraction["coverage"]["active_parameter_count"], 49)
        self.assertTrue(extraction["coverage"]["all_active_models_have_formula_or_exact_pseudocode"])
        self.assertTrue(extraction["coverage"]["all_parameters_source_bound"])

        registry_models = {model["model_id"]: model for model in registry["models"] if model["status"] == "active"}
        extracted_models = {model["model_id"]: model for model in extraction["model_extractions"]}
        self.assertEqual(set(extracted_models), set(registry_models))
        formula_ids: set[str] = set()
        parameter_ids: set[str] = set()
        for model_id, model in extracted_models.items():
            source_model = registry_models[model_id]
            self.assertEqual(model["formula_ids"], source_model["formula_ids"])
            self.assertEqual(model["parameter_ids"], source_model["parameter_ids"])
            self.assertTrue(model["exact_pseudocode"], model_id)
            self.assertTrue(model["strategies"], model_id)
            formula_ids.update(model["formula_ids"])
            parameter_ids.update(model["parameter_ids"])
            for field in ("code_refs", "config_refs", "test_refs", "source_refs"):
                for ref in model.get(field, []):
                    if ref == "NOT_APPLICABLE":
                        continue
                    ref_path = str(ref).split(":", 1)[0]
                    self.assertTrue((ROOT / ref_path).exists(), ref)
        self.assertEqual(len(formula_ids), 12)
        self.assertEqual(len(parameter_ids), 49)

        required_fields = set(extraction["parameter_source_contract"]["required_binding_fields"])
        for field in {"parameter_id", "model_id", "active_value", "code_ref", "test_ref", "source_selector"}:
            self.assertIn(field, required_fields)
        serialized = json.dumps(extraction, ensure_ascii=False)
        self.assertIn("no_tech_stack_as_model_parameter", serialized)
        self.assertIn("Python, SQLite, macOS Mail", serialized)

    def test_review9_s4pat02_serenity_model_extraction_preserves_formula_008_caveat(self) -> None:
        validator = load_validator_module()
        extraction = validator.load_yaml(ROOT / "Serenity-Alipay" / "docs" / "governance" / "model_extraction.yaml")
        caveats = {item["issue_id"]: item for item in extraction["caveats"]}
        caveat = caveats["S4PAT01-WATCH-FORM-008-CAP"]
        self.assertEqual(caveat["formula_id"], "FORM-008")
        self.assertFalse(caveat["post_renormalization_cap_holds"])
        self.assertEqual(caveat["missing_target_weight_test_candidate_counts"], [1, 2, 3, 4])
        self.assertIn("does not claim a universal post-renormalization cap", caveat["statement"])

    def test_review9_s4pat02_model_extraction_is_project_governance_only(self) -> None:
        sync = load_sync_module()
        project = {
            "project_id": "Serenity-Alipay",
            "path": "Serenity-Alipay",
            "model_behavior_globs": ["app/**/*.py", "tests/**/*.py"],
        }
        changes, _ = sync.classify_changes(
            {"projects": [project]},
            ["Serenity-Alipay/docs/governance/model_extraction.yaml"],
        )
        self.assertEqual(len(changes), 1)
        self.assertEqual(changes[0].classifications, {"governance_only_change"})
        self.assertEqual(changes[0].updated_governance_files, {"docs/governance/model_extraction.yaml"})
        validation = sync.SyncValidation()
        sync.validate_diff_contract(validation, changes)
        self.assertFalse(validation.errors)

    def test_review9_s4pat02_manifest_records_model_extraction_scope(self) -> None:
        manifest = json.loads(
            (
                ROOT
                / "governance"
                / "run_manifests"
                / "GOV-REVIEW9-S4PAT02-MODEL-EXTRACTION-20260623.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(manifest["project_id"], "Serenity-Alipay")
        self.assertEqual(manifest["task_id"], "S4PAT02")
        self.assertEqual(manifest["acceptance_ids"], ["ACC-S4PAT02"])
        self.assertEqual(manifest["binding_status"], "PRECOMMIT_TREE_BOUND")
        self.assertIn("model_extraction", manifest["change_classification"])
        self.assertIn("no_business_behavior_change", manifest["change_classification"])
        self.assertTrue(str(manifest["content_tree_hash"]).startswith("sha256-changed-files-excluding-this-manifest:"))
        changed = set(manifest["changed_files_actual"])
        self.assertIn("Serenity-Alipay/docs/governance/model_extraction.yaml", changed)
        self.assertIn("scripts/validate_governance_sync.py", changed)
        self.assertIn("tests/governance/test_project_governance_validator.py", changed)
        self.assertIn(
            "governance/run_manifests/GOV-REVIEW9-S4PAT02-MODEL-EXTRACTION-20260623.json",
            changed,
        )
        self.assertIn("Serenity-Alipay/docs/governance/model_extraction.yaml", manifest["evidence_refs"])
        self.assertIn("S4PAT03 still must reconstruct Roadmap", " ".join(manifest["unresolved_risks"]))

    def test_review9_s4pat03_serenity_roadmap_draft_separates_event_truth_levels(self) -> None:
        validator = load_validator_module()
        roadmap = validator.load_yaml(ROOT / "Serenity-Alipay" / "docs" / "governance" / "roadmap_draft.yaml")
        self.assertEqual(roadmap["schema_version"], "codexproject.roadmap_draft.v1")
        self.assertEqual(roadmap["project_id"], "Serenity-Alipay")
        self.assertEqual(roadmap["task_id"], "S4PAT03")
        self.assertEqual(roadmap["acceptance_id"], "ACC-S4PAT03")
        self.assertFalse(roadmap["estimate_policy"]["historical_hours_inferred"])
        self.assertFalse(roadmap["estimate_policy"]["git_commit_count_used_as_iteration_count"])

        confirmed = {event["event_id"]: event for event in roadmap["confirmed_events"]}
        reconstructed = {event["event_id"]: event for event in roadmap["reconstructed_events"]}
        unknowns = {item["unknown_id"]: item for item in roadmap["unknowns"]}
        self.assertIn("ITER-20260621-001", confirmed)
        self.assertIn("ITER-20260621-002", confirmed)
        self.assertEqual(confirmed["ITER-20260621-001"]["binding_status"], "stale_unbound")
        self.assertEqual(confirmed["ITER-20260621-002"]["binding_status"], "stale_unbound")
        self.assertEqual(confirmed["REVIEW9-S4PAT01"]["binding_status"], "commit_and_ci_bound")
        self.assertEqual(confirmed["REVIEW9-S4PAT02"]["binding_status"], "commit_and_ci_bound")
        self.assertIn("EVENT-RECON-20260612-001", reconstructed)
        self.assertIn("EVENT-RECON-20260614-001", reconstructed)
        self.assertIn("UNKNOWN-SER-HISTORY-001", unknowns)
        self.assertEqual(unknowns["UNKNOWN-SER-HISTORY-001"]["fact_level"], "UNKNOWN")
        self.assertEqual(unknowns["UNKNOWN-SER-HISTORY-001"]["followup_task_id"], "S4PBT01")
        self.assertTrue(roadmap["acceptance"]["confirmed_and_reconstructed_separated"])
        self.assertTrue(roadmap["acceptance"]["legacy_pending_not_promoted"])

    def test_review9_s4pat03_serenity_roadmap_draft_has_valid_stage_phase_task_gates(self) -> None:
        validator = load_validator_module()
        roadmap = validator.load_yaml(ROOT / "Serenity-Alipay" / "docs" / "governance" / "roadmap_draft.yaml")
        draft = roadmap["roadmap_draft"]
        self.assertEqual(draft["stage_id"], "S4")
        self.assertEqual(draft["stop_gate"]["gate_id"], "S4-GATE")
        phase_ids = [phase["phase_id"] for phase in draft["phases"]]
        self.assertEqual(phase_ids, ["S4PA", "S4PB", "S4PC"])
        expected_tasks = {
            "S4PAT01",
            "S4PAT02",
            "S4PAT03",
            "S4PBT01",
            "S4PBT02",
            "S4PBT03",
            "S4PCT01",
            "S4PCT02",
        }
        observed_tasks: set[str] = set()
        for phase in draft["phases"]:
            self.assertRegex(phase["phase_id"], r"^S4P[A-Z]$")
            self.assertTrue(phase["stop_gate"]["gate_id"].startswith(phase["phase_id"]))
            for task in phase["tasks"]:
                observed_tasks.add(task["task_id"])
                self.assertRegex(task["task_id"], r"^S4P[A-Z]T[0-9]{2}$")
                self.assertIn("estimated_hours", task)
                self.assertIn("estimated_pct", task)
                self.assertTrue(task["acceptance_ids"])
        self.assertEqual(observed_tasks, expected_tasks)
        completed = {
            task["task_id"]: task
            for phase in draft["phases"]
            for task in phase["tasks"]
            if task["status"] == "completed"
        }
        self.assertEqual(set(completed), {"S4PAT01", "S4PAT02"})
        self.assertIn("PR-95", completed["S4PAT01"]["evidence_refs"])
        self.assertIn("ci_run:28027304921", completed["S4PAT01"]["evidence_refs"])
        self.assertIn("PR-96", completed["S4PAT02"]["evidence_refs"])
        self.assertIn("ci_run:28027843674", completed["S4PAT02"]["evidence_refs"])

    def test_review9_s4pat03_roadmap_draft_is_project_governance_only(self) -> None:
        sync = load_sync_module()
        project = {
            "project_id": "Serenity-Alipay",
            "path": "Serenity-Alipay",
            "model_behavior_globs": ["app/**/*.py", "tests/**/*.py"],
        }
        changes, _ = sync.classify_changes(
            {"projects": [project]},
            ["Serenity-Alipay/docs/governance/roadmap_draft.yaml"],
        )
        self.assertEqual(len(changes), 1)
        self.assertEqual(changes[0].classifications, {"governance_only_change"})
        self.assertEqual(changes[0].updated_governance_files, {"docs/governance/roadmap_draft.yaml"})
        validation = sync.SyncValidation()
        sync.validate_diff_contract(validation, changes)
        self.assertFalse(validation.errors)

    def test_review9_s4pat03_manifest_records_roadmap_reconstruction_scope(self) -> None:
        manifest = json.loads(
            (
                ROOT
                / "governance"
                / "run_manifests"
                / "GOV-REVIEW9-S4PAT03-ROADMAP-DRAFT-20260623.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(manifest["project_id"], "Serenity-Alipay")
        self.assertEqual(manifest["task_id"], "S4PAT03")
        self.assertEqual(manifest["acceptance_ids"], ["ACC-S4PAT03"])
        self.assertEqual(manifest["binding_status"], "PRECOMMIT_TREE_BOUND")
        self.assertIn("roadmap_draft", manifest["change_classification"])
        self.assertIn("no_invented_history", manifest["change_classification"])
        changed = set(manifest["changed_files_actual"])
        self.assertIn("Serenity-Alipay/docs/governance/roadmap_draft.yaml", changed)
        self.assertIn("scripts/validate_governance_sync.py", changed)
        self.assertIn("tests/governance/test_project_governance_validator.py", changed)
        self.assertIn(
            "governance/run_manifests/GOV-REVIEW9-S4PAT03-ROADMAP-DRAFT-20260623.json",
            changed,
        )
        self.assertIn("Serenity-Alipay/docs/governance/roadmap_draft.yaml", manifest["evidence_refs"])
        self.assertIn("S4PBT01 still must create canonical", " ".join(manifest["unresolved_risks"]))

    def test_review9_s4pb_serenity_project_yaml_contains_canonical_model_facts(self) -> None:
        validator = load_validator_module()
        project = validator.load_yaml(ROOT / "Serenity-Alipay" / "docs" / "governance" / "project.yaml")
        self.assertEqual(project["schema_version"], "codexproject.project.v1")
        self.assertEqual(project["project_id"], "Serenity-Alipay")
        self.assertEqual(project["fact_level"], "EXTRACTED")
        self.assertEqual(len(project["models"]), 5)
        self.assertEqual(len(project["formulas"]), 12)
        self.assertEqual(len(project["parameters"]), 49)
        self.assertEqual(len(project["strategies"]), 5)
        self.assertEqual(len(project["assumptions"]), 6)

        model_ids = {item["model_id"] for item in project["models"]}
        formula_ids = {item["formula_id"] for item in project["formulas"]}
        parameter_ids = {item["parameter_id"] for item in project["parameters"]}
        self.assertEqual(model_ids, {"MOD-001", "MOD-002", "MOD-003", "MOD-004", "MOD-005"})
        self.assertEqual({f"FORM-{index:03d}" for index in range(1, 13)}, formula_ids)
        self.assertEqual({f"PARAM-{index:03d}" for index in range(1, 50)}, parameter_ids)

        formula_008 = next(item for item in project["formulas"] if item["formula_id"] == "FORM-008")
        self.assertIn("Normalize capped weights again", formula_008["expression"])
        limitations = " ".join(item["statement"] for item in project["limitations"])
        self.assertIn("one-to-four candidate scenarios can exceed 0.30", limitations)
        parameter_blob = " ".join(
            f"{item['parameter_id']} {item['symbol']} {item['name']} {item['source']}" for item in project["parameters"]
        )
        for forbidden in {"Python", "SQLite", "macOS Mail"}:
            self.assertNotIn(forbidden, parameter_blob)

        evidence_ids = {item["evidence_id"] for item in project["evidence_refs"]}
        self.assertIn("EVID-REVIEW9-S4PAT03-CI", evidence_ids)
        for section in ("features", "models", "formulas", "parameters", "strategies", "validations"):
            for item in project[section]:
                for evidence_id in item["evidence_refs"]:
                    self.assertIn(evidence_id, evidence_ids)

    def test_review9_s4pb_serenity_roadmap_tracks_canonical_render_phase(self) -> None:
        validator = load_validator_module()
        roadmap = validator.load_yaml(ROOT / "Serenity-Alipay" / "docs" / "governance" / "roadmap.yaml")
        self.assertEqual(roadmap["schema_version"], "codexproject.roadmap.v1")
        self.assertEqual(roadmap["project_id"], "Serenity-Alipay")

        tasks = {
            task["task_id"]: task
            for stage in roadmap["stages"]
            for phase in stage["phases"]
            for task in phase["tasks"]
        }
        self.assertEqual(tasks["S4PAT03"]["status"], "completed")
        self.assertEqual(tasks["S4PAT03"]["completed_commit"], "e0a6782efee3c2945abaa261eb0b28fce7bff2df")
        self.assertEqual(tasks["S4PBT01"]["status"], "completed")
        self.assertEqual(tasks["S4PBT02"]["status"], "completed")
        self.assertEqual(tasks["S4PBT03"]["status"], "completed")
        self.assertEqual(tasks["S4PBT03"]["completed_commit"], "00f3a8a59fcbeb37bcb41959da10549d844da0c2")
        self.assertIn("governance/run_manifests/GOV-REVIEW9-S4PB-CANONICAL-RENDER-20260623.json", tasks["S4PBT03"]["evidence_refs"])

    def test_review9_s4pb_serenity_events_preserve_truth_levels(self) -> None:
        events = [
            json.loads(line)
            for line in (ROOT / "Serenity-Alipay" / "docs" / "governance" / "events.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
            if line.strip()
        ]
        self.assertGreaterEqual(len(events), 7)
        self.assertEqual({event["schema_version"] for event in events}, {"codexproject.event.v1"})
        self.assertTrue({event["fact_level"] for event in events}.issubset({"VERIFIED", "RECONSTRUCTED", "PROPOSED", "UNKNOWN"}))
        by_id = {event["event_id"]: event for event in events}
        self.assertEqual(by_id["EVT-SER-LEGACY-20260621-001"]["fact_level"], "UNKNOWN")
        self.assertIn("stale_unbound", by_id["EVT-SER-LEGACY-20260621-001"]["summary"])
        self.assertEqual(by_id["EVT-SER-REVIEW9-S4PB-LOCAL"]["fact_level"], "PROPOSED")
        self.assertIn("must remain PROPOSED", by_id["EVT-SER-REVIEW9-S4PB-LOCAL"]["notes"])
        self.assertEqual(by_id["EVT-SER-REVIEW9-S4PAT03"]["fact_level"], "VERIFIED")

    def test_review9_s4pb_serenity_human_files_render_without_drift(self) -> None:
        cli = load_lean_governance_module()
        result = cli.check_render_project_files(ROOT / "Serenity-Alipay")
        self.assertEqual(result["drift_count"], 0, result["drift"])
        self.assertEqual(result["reference_issue_count"], 0, result["reference_issues"])

        feature_text = (ROOT / "Serenity-Alipay" / "功能清单").read_text(encoding="utf-8")
        dev_text = (ROOT / "Serenity-Alipay" / "开发记录").read_text(encoding="utf-8")
        model_text = (ROOT / "Serenity-Alipay" / "模型参数文件").read_text(encoding="utf-8")
        self.assertIn("# 功能清单", feature_text)
        self.assertIn("Stage -> Phase -> Task", dev_text)
        self.assertIn("S4PBT03", dev_text)
        self.assertIn("FORM-008", model_text)
        for text in (feature_text, dev_text, model_text):
            self.assertNotIn("docs/governance/", text.splitlines()[0])

    def test_review9_s4pb_git_status_porcelain_decodes_chinese_paths_as_utf8(self) -> None:
        cli = load_lean_governance_module()
        completed = SimpleNamespace(stdout=" M Serenity-Alipay/功能清单\n", stderr="", returncode=0)
        with patch.object(cli.subprocess, "run", return_value=completed) as run:
            lines = cli.git_status_porcelain(ROOT)
        self.assertEqual(lines, [" M Serenity-Alipay/功能清单"])
        kwargs = run.call_args.kwargs
        self.assertEqual(kwargs["encoding"], "utf-8")
        self.assertEqual(kwargs["errors"], "replace")

    def test_review9_s4pb_canonical_files_are_project_governance_only(self) -> None:
        sync = load_sync_module()
        project = {
            "project_id": "Serenity-Alipay",
            "path": "Serenity-Alipay",
            "model_behavior_globs": ["app/**/*.py", "tests/**/*.py"],
        }
        changes, _ = sync.classify_changes(
            {"projects": [project]},
            [
                "Serenity-Alipay/docs/governance/project.yaml",
                "Serenity-Alipay/docs/governance/roadmap.yaml",
                "Serenity-Alipay/docs/governance/events.jsonl",
            ],
        )
        self.assertEqual(len(changes), 1)
        self.assertEqual(changes[0].classifications, {"governance_only_change"})
        self.assertEqual(
            changes[0].updated_governance_files,
            {"docs/governance/project.yaml", "docs/governance/roadmap.yaml", "docs/governance/events.jsonl"},
        )
        validation = sync.SyncValidation()
        sync.validate_diff_contract(validation, changes)
        self.assertFalse(validation.errors)

    def test_review9_s4pb_manifest_records_canonical_render_scope(self) -> None:
        manifest = json.loads(
            (
                ROOT
                / "governance"
                / "run_manifests"
                / "GOV-REVIEW9-S4PB-CANONICAL-RENDER-20260623.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(manifest["project_id"], "Serenity-Alipay")
        self.assertEqual(manifest["task_id"], "S4PB")
        self.assertEqual(manifest["acceptance_ids"], ["ACC-S4PBT01", "ACC-S4PBT02", "ACC-S4PBT03"])
        self.assertEqual(manifest["binding_status"], "PRECOMMIT_TREE_BOUND")
        self.assertIn("canonical_project_facts", manifest["change_classification"])
        self.assertIn("human_entry_render", manifest["change_classification"])
        changed = set(manifest["changed_files_actual"])
        for path in {
            "Serenity-Alipay/docs/governance/project.yaml",
            "Serenity-Alipay/docs/governance/roadmap.yaml",
            "Serenity-Alipay/docs/governance/events.jsonl",
            "Serenity-Alipay/功能清单",
            "Serenity-Alipay/开发记录",
            "Serenity-Alipay/模型参数文件",
            "scripts/lean_governance.py",
            "scripts/validate_governance_sync.py",
            "tests/governance/test_project_governance_validator.py",
            "governance/run_manifests/GOV-REVIEW9-S4PB-CANONICAL-RENDER-20260623.json",
        }:
            self.assertIn(path, changed)
        self.assertIn("S4PC still must record owner readability", " ".join(manifest["unresolved_risks"]))

    def test_review9_s4pc_serenity_records_owner_acceptance_truthfully(self) -> None:
        validator = load_validator_module()
        review = validator.load_yaml(ROOT / "Serenity-Alipay" / "docs" / "governance" / "owner_roa_review.yaml")
        self.assertEqual(review["schema_version"], "codexproject.owner_roa_review.v1")
        self.assertEqual(review["task_id"], "S4PCT01")
        self.assertEqual(review["acceptance_id"], "ACC-S4PCT01")
        self.assertEqual(review["agent_roa_result"]["status"], "PASS_LOCAL_AGENT_REVIEW")
        self.assertEqual(review["agent_roa_result"]["owner_acceptance_status"], "ACCEPTED")
        self.assertTrue(review["agent_roa_result"]["owner_confirmed"])
        self.assertEqual(
            review["agent_roa_result"]["owner_acceptance_statement"],
            "ACCEPT S4PC owner readability for Serenity-Alipay Review9 Lean v2 migration.",
        )
        self.assertTrue(review["acceptance"]["owner_acceptance_recorded"])
        self.assertTrue(review["acceptance"]["false_acceptance_prevented"])

    def test_review9_s4pc_serenity_roadmap_and_project_bind_s4pb_ci(self) -> None:
        validator = load_validator_module()
        project = validator.load_yaml(ROOT / "Serenity-Alipay" / "docs" / "governance" / "project.yaml")
        roadmap = validator.load_yaml(ROOT / "Serenity-Alipay" / "docs" / "governance" / "roadmap.yaml")
        evidence = {item["evidence_id"]: item for item in project["evidence_refs"]}
        validations = {item["validation_id"]: item for item in project["validations"]}
        self.assertEqual(evidence["EVID-REVIEW9-S4PB-MANIFEST"]["fact_level"], "VERIFIED")
        self.assertEqual(evidence["EVID-REVIEW9-S4PB-CI"]["kind"], "ci")
        self.assertIn("28029791587", evidence["EVID-REVIEW9-S4PB-CI"]["ref"])
        self.assertEqual(validations["VAL-SER-S4PB"]["fact_level"], "VERIFIED")
        self.assertEqual(evidence["EVID-REVIEW9-S4PC-OWNER-ACCEPTED"]["fact_level"], "VERIFIED")
        self.assertEqual(evidence["EVID-REVIEW9-S4PC-OWNER-ACCEPTED"]["kind"], "owner")
        self.assertIn("28030744188", evidence["EVID-REVIEW9-S4PC-CI"]["ref"])
        self.assertEqual(validations["VAL-SER-S4PC"]["fact_level"], "VERIFIED")

        self.assertEqual(roadmap["current_phase_id"], "S4PC")
        self.assertEqual(roadmap["current_task_id"], "S4PCT02")
        self.assertEqual(roadmap["next_gate_id"], "S4-GATE-PASSED")
        self.assertEqual(roadmap["completed_estimated_hours"], 32)
        tasks = {
            task["task_id"]: task
            for stage in roadmap["stages"]
            for phase in stage["phases"]
            for task in phase["tasks"]
        }
        self.assertEqual(tasks["S4PBT03"]["status"], "completed")
        self.assertEqual(tasks["S4PBT03"]["completed_commit"], "00f3a8a59fcbeb37bcb41959da10549d844da0c2")
        self.assertEqual(tasks["S4PCT01"]["status"], "completed")
        self.assertEqual(tasks["S4PCT02"]["status"], "completed")

    def test_review9_s4pc_serenity_performance_and_rollback_evidence_are_local_only(self) -> None:
        validator = load_validator_module()
        performance = validator.load_yaml(ROOT / "Serenity-Alipay" / "docs" / "governance" / "performance_report.yaml")
        rollback = validator.load_yaml(ROOT / "Serenity-Alipay" / "docs" / "governance" / "rollback_test.yaml")
        self.assertEqual(performance["task_id"], "S4PCT02")
        self.assertEqual(performance["token_proxy"]["current_root_change_caveat"].count("selected all registered projects"), 1)
        self.assertEqual(performance["quality_result"]["owner_acceptance_status"], "ACCEPTED")
        self.assertTrue(performance["acceptance"]["owner_acceptance_recorded"])
        self.assertEqual(rollback["rollback_check"]["exit_code"], 0)
        self.assertEqual(rollback["rollback_check"]["result"], "PASS")
        self.assertFalse(rollback["rollback_check"]["destructive_action_performed"])
        self.assertTrue(rollback["acceptance"]["rollback_path_executable"])
        self.assertTrue(rollback["acceptance"]["owner_acceptance_recorded"])

    def test_review9_s4pc_serenity_events_mark_owner_acceptance_as_proposed(self) -> None:
        events = [
            json.loads(line)
            for line in (ROOT / "Serenity-Alipay" / "docs" / "governance" / "events.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
            if line.strip()
        ]
        by_id = {event["event_id"]: event for event in events}
        self.assertEqual(by_id["EVT-SER-REVIEW9-S4PB-CI"]["fact_level"], "VERIFIED")
        self.assertEqual(by_id["EVT-SER-REVIEW9-S4PC-PREP"]["fact_level"], "PROPOSED")
        self.assertIn("must not be treated as owner approval", by_id["EVT-SER-REVIEW9-S4PC-PREP"]["notes"])
        self.assertEqual(by_id["EVT-SER-REVIEW9-S4PC-OWNER-ACCEPTED"]["fact_level"], "VERIFIED")
        self.assertEqual(by_id["EVT-SER-REVIEW9-S4PC-OWNER-ACCEPTED"]["actor_role"], "owner")
        self.assertIn(
            "ACCEPT S4PC owner readability",
            by_id["EVT-SER-REVIEW9-S4PC-OWNER-ACCEPTED"]["evidence_refs"][0]["description"],
        )

    def test_review9_s4pc_serenity_human_files_render_without_drift(self) -> None:
        cli = load_lean_governance_module()
        result = cli.check_render_project_files(ROOT / "Serenity-Alipay")
        self.assertEqual(result["drift_count"], 0, result["drift"])
        self.assertEqual(result["reference_issue_count"], 0, result["reference_issues"])

    def test_review9_s4pc_files_are_project_governance_only(self) -> None:
        sync = load_sync_module()
        project = {
            "project_id": "Serenity-Alipay",
            "path": "Serenity-Alipay",
            "model_behavior_globs": ["app/**/*.py", "tests/**/*.py"],
        }
        changes, _ = sync.classify_changes(
            {"projects": [project]},
            [
                "Serenity-Alipay/docs/governance/owner_roa_review.yaml",
                "Serenity-Alipay/docs/governance/performance_report.yaml",
                "Serenity-Alipay/docs/governance/rollback_test.yaml",
            ],
        )
        self.assertEqual(len(changes), 1)
        self.assertEqual(changes[0].classifications, {"governance_only_change"})
        self.assertEqual(
            changes[0].updated_governance_files,
            {
                "docs/governance/owner_roa_review.yaml",
                "docs/governance/performance_report.yaml",
                "docs/governance/rollback_test.yaml",
            },
        )
        validation = sync.SyncValidation()
        sync.validate_diff_contract(validation, changes)
        self.assertFalse(validation.errors)

    def test_review9_s4pc_manifest_records_pending_owner_gate(self) -> None:
        manifest = json.loads(
            (
                ROOT
                / "governance"
                / "run_manifests"
                / "GOV-REVIEW9-S4PC-OWNER-ACCEPTANCE-20260623.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(manifest["project_id"], "Serenity-Alipay")
        self.assertEqual(manifest["task_id"], "S4PC")
        self.assertEqual(manifest["acceptance_ids"], ["ACC-S4PCT01", "ACC-S4PCT02"])
        self.assertIn("owner_acceptance_pending", manifest["change_classification"])
        self.assertIn("PENDING_OWNER_CONFIRMATION", " ".join(manifest["unresolved_risks"]))
        self.assertFalse(manifest["owner_acceptance_recorded"])

    def test_review9_s5pat01_alpha_project_yaml_contains_canonical_model_facts(self) -> None:
        validator = load_validator_module()
        project = validator.load_yaml(ROOT / "Alpha" / "docs" / "governance" / "project.yaml")
        self.assertEqual(project["schema_version"], "codexproject.project.v1")
        self.assertEqual(project["project_id"], "Alpha")
        self.assertEqual(project["fact_level"], "EXTRACTED")
        self.assertEqual(project["current_status"], "blocked_for_live_readiness")
        self.assertEqual(len(project["features"]), 6)
        self.assertEqual(len(project["models"]), 9)
        self.assertEqual(len(project["formulas"]), 9)
        self.assertEqual(len(project["parameters"]), 55)
        self.assertEqual(len(project["strategies"]), 4)

        model_ids = {item["model_id"] for item in project["models"]}
        formula_ids = {item["formula_id"] for item in project["formulas"]}
        parameter_ids = {item["parameter_id"] for item in project["parameters"]}
        self.assertEqual({f"MOD-{index:03d}" for index in range(1, 10)}, model_ids)
        self.assertEqual({f"FORM-{index:03d}" for index in range(1, 10)}, formula_ids)
        self.assertEqual({f"PARAM-{index:03d}" for index in range(1, 56)}, parameter_ids)

        evidence_ids = {item["evidence_id"] for item in project["evidence_refs"]}
        self.assertIn("EVID-REVIEW9-S5PAT01-MANIFEST", evidence_ids)
        self.assertIn("EVID-ALPHA-SEMANTIC-MANIFEST", evidence_ids)
        for section in ("features", "models", "formulas", "parameters", "strategies", "validations"):
            for item in project[section]:
                for evidence_id in item["evidence_refs"]:
                    self.assertIn(evidence_id, evidence_ids)

        semantic_counts = Counter(item["semantic_status"] for item in project["parameters"])
        self.assertEqual(semantic_counts["MACHINE_VERIFIED"], 42)
        self.assertEqual(semantic_counts["HUMAN_REVIEW_REQUIRED"], 13)
        limitations = " ".join(item["statement"] for item in project["limitations"])
        self.assertIn("不声明实盘就绪", project["summary"])
        self.assertIn("13 个 branch-rule 参数", limitations)
        self.assertEqual(project["validations"][1]["fact_level"], "PROPOSED")

    def test_review9_s5pat01_alpha_roadmap_tracks_single_project_task(self) -> None:
        validator = load_validator_module()
        roadmap = validator.load_yaml(ROOT / "Alpha" / "docs" / "governance" / "roadmap.yaml")
        self.assertEqual(roadmap["schema_version"], "codexproject.roadmap.v1")
        self.assertEqual(roadmap["project_id"], "Alpha")
        self.assertEqual(roadmap["current_stage_id"], "S5")
        self.assertEqual(roadmap["current_phase_id"], "S5PA")
        self.assertEqual(roadmap["current_task_id"], "S5PAT01")
        self.assertEqual(roadmap["next_gate_id"], "S5PA-GATE-IN-PROGRESS")
        self.assertEqual(roadmap["total_estimated_hours"], 5)
        self.assertEqual(roadmap["completed_estimated_hours"], 5)

        tasks = [
            task
            for stage in roadmap["stages"]
            for phase in stage["phases"]
            for task in phase["tasks"]
        ]
        self.assertEqual([task["task_id"] for task in tasks], ["S5PAT01"])
        task = tasks[0]
        self.assertEqual(task["status"], "completed")
        self.assertEqual(task["acceptance_ids"], ["ACC-S5PAT01"])
        self.assertIn("Alpha/docs/governance/project.yaml", task["evidence_refs"])
        self.assertIn("一次 PR 同时迁移多个项目", roadmap["stages"][0]["stop_conditions"])
        self.assertIn("批量脚本产生无证据事实", roadmap["stages"][0]["phases"][0]["stop_conditions"])

    def test_review9_s5pat01_alpha_events_preserve_truth_levels(self) -> None:
        events = [
            json.loads(line)
            for line in (ROOT / "Alpha" / "docs" / "governance" / "events.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
            if line.strip()
        ]
        self.assertEqual(len(events), 5)
        self.assertEqual({event["schema_version"] for event in events}, {"codexproject.event.v1"})
        self.assertTrue({event["fact_level"] for event in events}.issubset({"VERIFIED", "RECONSTRUCTED", "PROPOSED", "UNKNOWN"}))
        by_id = {event["event_id"]: event for event in events}
        self.assertEqual(by_id["EVT-ALPHA-SEMANTIC-20260621-001"]["fact_level"], "RECONSTRUCTED")
        self.assertIn("in_progress, not machine_verified", by_id["EVT-ALPHA-SEMANTIC-20260621-001"]["notes"])
        self.assertEqual(by_id["EVT-ALPHA-REVIEW9-S5PAT01-LOCAL"]["fact_level"], "PROPOSED")
        self.assertIn("Must remain PROPOSED", by_id["EVT-ALPHA-REVIEW9-S5PAT01-LOCAL"]["notes"])
        self.assertFalse(any(event["runtime_behavior_changed"] for event in events))

    def test_review9_s5pat01_alpha_human_files_render_without_drift(self) -> None:
        cli = load_lean_governance_module()
        result = cli.check_render_project_files(ROOT / "Alpha")
        self.assertEqual(result["drift_count"], 0, result["drift"])
        self.assertEqual(result["reference_issue_count"], 0, result["reference_issues"])

        feature_text = (ROOT / "Alpha" / "功能清单").read_text(encoding="utf-8")
        dev_text = (ROOT / "Alpha" / "开发记录").read_text(encoding="utf-8")
        model_text = (ROOT / "Alpha" / "模型参数文件").read_text(encoding="utf-8")
        self.assertIn("# 功能清单", feature_text)
        self.assertIn("FEAT-ALPHA-003", feature_text)
        self.assertIn("Stage -> Phase -> Task", dev_text)
        self.assertIn("S5PAT01", dev_text)
        self.assertIn("MOD-004", model_text)
        self.assertIn("PARAM-023", model_text)
        for text in (feature_text, dev_text, model_text):
            self.assertNotIn("docs/governance/", text.splitlines()[0])

    def test_review9_s5pat01_files_are_project_governance_only(self) -> None:
        sync = load_sync_module()
        project = {
            "project_id": "Alpha",
            "path": "Alpha",
            "model_behavior_globs": ["backend/**/*.py", "tests/**/*.py"],
        }
        changes, _ = sync.classify_changes(
            {"projects": [project]},
            [
                "Alpha/docs/governance/project.yaml",
                "Alpha/docs/governance/roadmap.yaml",
                "Alpha/docs/governance/events.jsonl",
                "Alpha/功能清单",
                "Alpha/开发记录",
                "Alpha/模型参数文件",
            ],
        )
        self.assertEqual(len(changes), 1)
        self.assertEqual(changes[0].classifications, {"governance_only_change", "trivial_change"})
        self.assertEqual(
            changes[0].updated_governance_files,
            {
                "docs/governance/project.yaml",
                "docs/governance/roadmap.yaml",
                "docs/governance/events.jsonl",
            },
        )
        validation = sync.SyncValidation()
        sync.validate_diff_contract(validation, changes)
        self.assertFalse(validation.errors)

    def test_review9_s5pat01_manifest_records_alpha_only_scope(self) -> None:
        manifest = json.loads(
            (
                ROOT
                / "governance"
                / "run_manifests"
                / "GOV-REVIEW9-S5PAT01-ALPHA-CANONICAL-RENDER-20260624.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(manifest["project_id"], "Alpha")
        self.assertEqual(manifest["task_id"], "S5PAT01")
        self.assertEqual(manifest["acceptance_ids"], ["ACC-S5PAT01"])
        self.assertEqual(manifest["binding_status"], "PRECOMMIT_TREE_BOUND")
        self.assertIn("review9_stage5_single_project_migration", manifest["change_classification"])
        self.assertIn("alpha_only_scope", manifest["change_classification"])
        changed = set(manifest["changed_files_actual"])
        for path in {
            "Alpha/docs/governance/project.yaml",
            "Alpha/docs/governance/roadmap.yaml",
            "Alpha/docs/governance/events.jsonl",
            "Alpha/功能清单",
            "Alpha/开发记录",
            "Alpha/模型参数文件",
            "tests/governance/test_project_governance_validator.py",
            "governance/run_manifests/GOV-REVIEW9-S5PAT01-ALPHA-CANONICAL-RENDER-20260624.json",
        }:
            self.assertIn(path, changed)
        self.assertFalse(any(path.startswith(("EVA_OS/", "OpMe_System/", "whkmSalary/")) for path in changed))
        self.assertIn("S5PA-GATE remains in_progress", " ".join(manifest["unresolved_risks"]))
        self.assertIn("Alpha live execution policy", " ".join(manifest["unresolved_risks"]))

    def test_review9_s5pat02_eva_os_project_yaml_contains_canonical_model_facts(self) -> None:
        validator = load_validator_module()
        project = validator.load_yaml(ROOT / "EVA_OS" / "docs" / "governance" / "project.yaml")
        self.assertEqual(project["schema_version"], "codexproject.project.v1")
        self.assertEqual(project["project_id"], "EVA_OS")
        self.assertEqual(project["fact_level"], "EXTRACTED")
        self.assertEqual(project["current_status"], "blocked_for_delivery_readiness")
        self.assertEqual(len(project["features"]), 5)
        self.assertEqual(len(project["models"]), 16)
        self.assertEqual(len(project["formulas"]), 16)
        self.assertEqual(len(project["parameters"]), 189)
        self.assertEqual(len(project["strategies"]), 3)

        model_ids = {item["model_id"] for item in project["models"]}
        formula_ids = {item["formula_id"] for item in project["formulas"]}
        parameter_ids = {item["parameter_id"] for item in project["parameters"]}
        self.assertEqual({f"MOD-{index:03d}" for index in range(1, 17)}, model_ids)
        self.assertEqual({f"FORM-{index:03d}" for index in range(1, 17)}, formula_ids)
        self.assertEqual({f"PARAM-{index:03d}" for index in range(1, 190)}, parameter_ids)

        evidence_ids = {item["evidence_id"] for item in project["evidence_refs"]}
        self.assertIn("EVID-REVIEW9-S5PAT02-MANIFEST", evidence_ids)
        self.assertIn("EVID-EVA-SEMANTIC-MANIFEST", evidence_ids)
        for section in ("features", "models", "formulas", "parameters", "strategies", "validations"):
            for item in project[section]:
                for evidence_id in item["evidence_refs"]:
                    self.assertIn(evidence_id, evidence_ids)

        semantic_counts = Counter(item["semantic_status"] for item in project["parameters"])
        self.assertEqual(semantic_counts["MACHINE_VERIFIED"], 52)
        self.assertEqual(semantic_counts["HUMAN_REVIEW_REQUIRED"], 137)
        limitations = " ".join(item["statement"] for item in project["limitations"])
        self.assertIn("不声明生产交付就绪", project["summary"])
        self.assertIn("137 个参数仍为 HUMAN_REVIEW_REQUIRED", limitations)
        self.assertIn("delivery_readiness 仍为 FAILED", limitations)
        self.assertEqual(project["validations"][1]["fact_level"], "PROPOSED")

    def test_review9_s5pat02_eva_os_roadmap_tracks_single_project_task(self) -> None:
        validator = load_validator_module()
        roadmap = validator.load_yaml(ROOT / "EVA_OS" / "docs" / "governance" / "roadmap.yaml")
        self.assertEqual(roadmap["schema_version"], "codexproject.roadmap.v1")
        self.assertEqual(roadmap["project_id"], "EVA_OS")
        self.assertEqual(roadmap["current_stage_id"], "S5")
        self.assertEqual(roadmap["current_phase_id"], "S5PA")
        self.assertEqual(roadmap["current_task_id"], "S5PAT02")
        self.assertEqual(roadmap["next_gate_id"], "S5PA-GATE-IN-PROGRESS")
        self.assertEqual(roadmap["total_estimated_hours"], 5)
        self.assertEqual(roadmap["completed_estimated_hours"], 5)

        tasks = [
            task
            for stage in roadmap["stages"]
            for phase in stage["phases"]
            for task in phase["tasks"]
        ]
        self.assertEqual([task["task_id"] for task in tasks], ["S5PAT02"])
        task = tasks[0]
        self.assertEqual(task["status"], "completed")
        self.assertEqual(task["dependencies"], ["S5PAT01"])
        self.assertEqual(task["acceptance_ids"], ["ACC-S5PAT02"])
        self.assertIn("EVA_OS/docs/governance/project.yaml", task["evidence_refs"])
        self.assertIn("一次 PR 同时迁移多个项目", roadmap["stages"][0]["stop_conditions"])
        self.assertIn("批量脚本产生无证据事实", roadmap["stages"][0]["phases"][0]["stop_conditions"])

    def test_review9_s5pat02_eva_os_events_preserve_truth_levels(self) -> None:
        events = [
            json.loads(line)
            for line in (ROOT / "EVA_OS" / "docs" / "governance" / "events.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
            if line.strip()
        ]
        self.assertEqual(len(events), 4)
        self.assertEqual({event["schema_version"] for event in events}, {"codexproject.event.v1"})
        self.assertTrue({event["fact_level"] for event in events}.issubset({"VERIFIED", "RECONSTRUCTED", "PROPOSED", "UNKNOWN"}))
        by_id = {event["event_id"]: event for event in events}
        self.assertEqual(by_id["EVT-EVA-SEMANTIC-20260621-001"]["fact_level"], "RECONSTRUCTED")
        self.assertIn("in_progress, not machine_verified", by_id["EVT-EVA-SEMANTIC-20260621-001"]["notes"])
        self.assertEqual(by_id["EVT-EVA-REVIEW9-S5PAT02-LOCAL"]["fact_level"], "PROPOSED")
        self.assertIn("Must remain PROPOSED", by_id["EVT-EVA-REVIEW9-S5PAT02-LOCAL"]["notes"])
        self.assertFalse(any(event["runtime_behavior_changed"] for event in events))

    def test_review9_s5pat02_eva_os_human_files_render_without_drift(self) -> None:
        cli = load_lean_governance_module()
        result = cli.check_render_project_files(ROOT / "EVA_OS")
        self.assertEqual(result["drift_count"], 0, result["drift"])
        self.assertEqual(result["reference_issue_count"], 0, result["reference_issues"])

        feature_text = (ROOT / "EVA_OS" / "功能清单").read_text(encoding="utf-8")
        dev_text = (ROOT / "EVA_OS" / "开发记录").read_text(encoding="utf-8")
        model_text = (ROOT / "EVA_OS" / "模型参数文件").read_text(encoding="utf-8")
        self.assertIn("# 功能清单", feature_text)
        self.assertIn("FEAT-EVA-004", feature_text)
        self.assertIn("Stage -> Phase -> Task", dev_text)
        self.assertIn("S5PAT02", dev_text)
        self.assertIn("MOD-010", model_text)
        self.assertIn("PARAM-189", model_text)
        for text in (feature_text, dev_text, model_text):
            self.assertNotIn("docs/governance/", text.splitlines()[0])

    def test_review9_s5pat02_files_are_project_governance_only(self) -> None:
        sync = load_sync_module()
        project = {
            "project_id": "EVA_OS",
            "path": "EVA_OS",
            "model_behavior_globs": ["src/**/*.py", "tests/**/*.py"],
        }
        changes, _ = sync.classify_changes(
            {"projects": [project]},
            [
                "EVA_OS/docs/governance/project.yaml",
                "EVA_OS/docs/governance/roadmap.yaml",
                "EVA_OS/docs/governance/events.jsonl",
                "EVA_OS/功能清单",
                "EVA_OS/开发记录",
                "EVA_OS/模型参数文件",
            ],
        )
        self.assertEqual(len(changes), 1)
        self.assertEqual(changes[0].classifications, {"governance_only_change", "trivial_change"})
        self.assertEqual(
            changes[0].updated_governance_files,
            {
                "docs/governance/project.yaml",
                "docs/governance/roadmap.yaml",
                "docs/governance/events.jsonl",
            },
        )
        validation = sync.SyncValidation()
        sync.validate_diff_contract(validation, changes)
        self.assertFalse(validation.errors)

    def test_review9_s5pat02_manifest_records_eva_only_scope(self) -> None:
        manifest = json.loads(
            (
                ROOT
                / "governance"
                / "run_manifests"
                / "GOV-REVIEW9-S5PAT02-EVA-OS-CANONICAL-RENDER-20260624.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(manifest["project_id"], "EVA_OS")
        self.assertEqual(manifest["task_id"], "S5PAT02")
        self.assertEqual(manifest["acceptance_ids"], ["ACC-S5PAT02"])
        self.assertEqual(manifest["binding_status"], "PRECOMMIT_TREE_BOUND")
        self.assertIn("review9_stage5_single_project_migration", manifest["change_classification"])
        self.assertIn("eva_os_only_scope", manifest["change_classification"])
        changed = set(manifest["changed_files_actual"])
        for path in {
            "EVA_OS/docs/governance/project.yaml",
            "EVA_OS/docs/governance/roadmap.yaml",
            "EVA_OS/docs/governance/events.jsonl",
            "EVA_OS/功能清单",
            "EVA_OS/开发记录",
            "EVA_OS/模型参数文件",
            "tests/governance/test_project_governance_validator.py",
            "governance/run_manifests/GOV-REVIEW9-S5PAT02-EVA-OS-CANONICAL-RENDER-20260624.json",
        }:
            self.assertIn(path, changed)
        self.assertFalse(any(path.startswith(("OpMe_System/", "whkmSalary/", "EEI/")) for path in changed))
        self.assertIn("S5PA-GATE remains in_progress", " ".join(manifest["unresolved_risks"]))
        self.assertIn("EVA_OS delivery readiness remains FAILED", " ".join(manifest["unresolved_risks"]))

    def test_review9_s5pat03_opme_project_yaml_contains_real_model_facts(self) -> None:
        validator = load_validator_module()
        project = validator.load_yaml(ROOT / "OpMe_System" / "docs" / "governance" / "project.yaml")
        self.assertEqual(project["schema_version"], "codexproject.project.v1")
        self.assertEqual(project["project_id"], "OpMe_System")
        self.assertEqual(project["fact_level"], "EXTRACTED")
        self.assertEqual(project["current_status"], "blocked_for_operational_validation")
        self.assertIn("不把 FastAPI、React、Docker 等技术栈误作模型参数", project["summary"])
        self.assertIn("不声明生产安全交付就绪", project["summary"])
        self.assertEqual(len(project["features"]), 5)
        self.assertEqual(len(project["models"]), 7)
        self.assertEqual(len(project["formulas"]), 7)
        self.assertEqual(len(project["parameters"]), 49)
        self.assertEqual(len(project["strategies"]), 3)

        model_ids = {item["model_id"] for item in project["models"]}
        formula_ids = {item["formula_id"] for item in project["formulas"]}
        parameter_ids = {item["parameter_id"] for item in project["parameters"]}
        self.assertEqual({f"MOD-{index:03d}" for index in range(1, 8)}, model_ids)
        self.assertEqual({f"FORM-{index:03d}" for index in range(1, 8)}, formula_ids)
        self.assertEqual({f"PARAM-{index:03d}" for index in range(1, 50)}, parameter_ids)

        evidence_ids = {item["evidence_id"] for item in project["evidence_refs"]}
        self.assertIn("EVID-REVIEW9-S5PAT03-MANIFEST", evidence_ids)
        self.assertIn("EVID-OPME-SEMANTIC-MANIFEST", evidence_ids)
        for section in ("features", "models", "formulas", "parameters", "strategies", "validations"):
            for item in project[section]:
                for evidence_id in item["evidence_refs"]:
                    self.assertIn(evidence_id, evidence_ids)

        semantic_counts = Counter(item["semantic_status"] for item in project["parameters"])
        fact_counts = Counter(item["fact_level"] for item in project["parameters"])
        self.assertEqual(semantic_counts["MACHINE_VERIFIED"], 49)
        self.assertEqual(fact_counts["UNKNOWN"], 42)
        self.assertEqual(fact_counts["EXTRACTED"], 7)
        limitations = " ".join(item["statement"] for item in project["limitations"])
        self.assertIn("42 个参数的校准依据仍为 UNKNOWN", limitations)
        self.assertIn("delivery_readiness 仍为 UNVERIFIED", limitations)
        self.assertIn("不读取 API key", limitations)
        self.assertEqual(project["validations"][0]["status"], "VERIFIED")
        self.assertEqual(project["delivery_readiness"]["status"], "UNVERIFIED")
        self.assertTrue(project["delivery_readiness"]["owner_decision_required"])

    def test_review9_s5pat03_opme_roadmap_tracks_single_project_task(self) -> None:
        validator = load_validator_module()
        roadmap = validator.load_yaml(ROOT / "OpMe_System" / "docs" / "governance" / "roadmap.yaml")
        self.assertEqual(roadmap["schema_version"], "codexproject.roadmap.v1")
        self.assertEqual(roadmap["project_id"], "OpMe_System")
        self.assertEqual(roadmap["current_stage_id"], "S5")
        self.assertEqual(roadmap["current_phase_id"], "S5PA")
        self.assertEqual(roadmap["current_task_id"], "S5PAT03")
        self.assertEqual(roadmap["next_gate_id"], "S5PA-GATE-IN-PROGRESS")
        self.assertEqual(roadmap["total_estimated_hours"], 5)
        self.assertEqual(roadmap["completed_estimated_hours"], 5)

        tasks = [
            task
            for stage in roadmap["stages"]
            for phase in stage["phases"]
            for task in phase["tasks"]
        ]
        self.assertEqual([task["task_id"] for task in tasks], ["S5PAT03"])
        task = tasks[0]
        self.assertEqual(task["status"], "completed")
        self.assertEqual(task["dependencies"], ["S5PAT02"])
        self.assertEqual(task["acceptance_ids"], ["ACC-S5PAT03"])
        self.assertIn("OpMe_System/docs/governance/project.yaml", task["evidence_refs"])
        self.assertIn("一次 PR 同时迁移多个项目", roadmap["stages"][0]["stop_conditions"])
        self.assertIn("批量脚本产生无证据事实", roadmap["stages"][0]["phases"][0]["stop_conditions"])

    def test_review9_s5pat03_opme_events_preserve_truth_levels(self) -> None:
        events = [
            json.loads(line)
            for line in (ROOT / "OpMe_System" / "docs" / "governance" / "events.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
            if line.strip()
        ]
        self.assertEqual(len(events), 4)
        self.assertEqual({event["schema_version"] for event in events}, {"codexproject.event.v1"})
        self.assertTrue({event["fact_level"] for event in events}.issubset({"VERIFIED", "RECONSTRUCTED", "PROPOSED", "UNKNOWN"}))
        by_id = {event["event_id"]: event for event in events}
        self.assertEqual(by_id["EVT-OPME-SEMANTIC-20260621-001"]["fact_level"], "RECONSTRUCTED")
        self.assertIn("not production readiness", by_id["EVT-OPME-SEMANTIC-20260621-001"]["notes"])
        self.assertEqual(by_id["EVT-OPME-REVIEW8-OWNER-DECISION-20260622-001"]["fact_level"], "UNKNOWN")
        self.assertEqual(by_id["EVT-OPME-REVIEW9-S5PAT03-LOCAL"]["fact_level"], "PROPOSED")
        self.assertIn("Must remain PROPOSED", by_id["EVT-OPME-REVIEW9-S5PAT03-LOCAL"]["notes"])
        self.assertFalse(any(event["runtime_behavior_changed"] for event in events))

    def test_review9_s5pat03_opme_human_files_render_without_drift(self) -> None:
        cli = load_lean_governance_module()
        result = cli.check_render_project_files(ROOT / "OpMe_System")
        self.assertEqual(result["drift_count"], 0, result["drift"])
        self.assertEqual(result["reference_issue_count"], 0, result["reference_issues"])

        feature_text = (ROOT / "OpMe_System" / "功能清单").read_text(encoding="utf-8")
        dev_text = (ROOT / "OpMe_System" / "开发记录").read_text(encoding="utf-8")
        model_text = (ROOT / "OpMe_System" / "模型参数文件").read_text(encoding="utf-8")
        self.assertIn("# 功能清单", feature_text)
        self.assertIn("FEAT-OPME-005", feature_text)
        self.assertIn("Stage -> Phase -> Task", dev_text)
        self.assertIn("S5PAT03", dev_text)
        self.assertIn("MOD-007", model_text)
        self.assertIn("PARAM-049", model_text)
        for text in (feature_text, dev_text, model_text):
            self.assertNotIn("docs/governance/", text.splitlines()[0])

    def test_review9_s5pat03_files_are_project_governance_only(self) -> None:
        sync = load_sync_module()
        project = {
            "project_id": "OpMe_System",
            "path": "OpMe_System",
            "model_behavior_globs": ["backend/**/*.py", "frontend/**/*.jsx", "frontend/**/*.js"],
        }
        changes, _ = sync.classify_changes(
            {"projects": [project]},
            [
                "OpMe_System/docs/governance/project.yaml",
                "OpMe_System/docs/governance/roadmap.yaml",
                "OpMe_System/docs/governance/events.jsonl",
                "OpMe_System/功能清单",
                "OpMe_System/开发记录",
                "OpMe_System/模型参数文件",
            ],
        )
        self.assertEqual(len(changes), 1)
        self.assertEqual(changes[0].classifications, {"governance_only_change", "trivial_change"})
        self.assertEqual(
            changes[0].updated_governance_files,
            {
                "docs/governance/project.yaml",
                "docs/governance/roadmap.yaml",
                "docs/governance/events.jsonl",
            },
        )
        validation = sync.SyncValidation()
        sync.validate_diff_contract(validation, changes)
        self.assertFalse(validation.errors)

    def test_review9_s5pat03_manifest_records_opme_only_scope(self) -> None:
        manifest = json.loads(
            (
                ROOT
                / "governance"
                / "run_manifests"
                / "GOV-REVIEW9-S5PAT03-OPME-SYSTEM-CANONICAL-RENDER-20260624.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(manifest["project_id"], "OpMe_System")
        self.assertEqual(manifest["task_id"], "S5PAT03")
        self.assertEqual(manifest["acceptance_ids"], ["ACC-S5PAT03"])
        self.assertEqual(manifest["binding_status"], "PRECOMMIT_TREE_BOUND")
        self.assertIn("review9_stage5_single_project_migration", manifest["change_classification"])
        self.assertIn("opme_system_only_scope", manifest["change_classification"])
        changed = set(manifest["changed_files_actual"])
        for path in {
            "OpMe_System/docs/governance/project.yaml",
            "OpMe_System/docs/governance/roadmap.yaml",
            "OpMe_System/docs/governance/events.jsonl",
            "OpMe_System/功能清单",
            "OpMe_System/开发记录",
            "OpMe_System/模型参数文件",
            "tests/governance/test_project_governance_validator.py",
            "governance/run_manifests/GOV-REVIEW9-S5PAT03-OPME-SYSTEM-CANONICAL-RENDER-20260624.json",
        }:
            self.assertIn(path, changed)
        self.assertFalse(any(path.startswith(("EVA_OS/", "whkmSalary/", "EEI/")) for path in changed))
        self.assertIn("S5PA-GATE remains in_progress", " ".join(manifest["unresolved_risks"]))
        self.assertIn("OpMe_System delivery readiness remains UNVERIFIED", " ".join(manifest["unresolved_risks"]))

    def test_review9_s5pat04_whkm_project_yaml_contains_salary_model_facts(self) -> None:
        validator = load_validator_module()
        project = validator.load_yaml(ROOT / "whkmSalary" / "docs" / "governance" / "project.yaml")
        self.assertEqual(project["schema_version"], "codexproject.project.v1")
        self.assertEqual(project["project_id"], "whkmSalary")
        self.assertEqual(project["fact_level"], "EXTRACTED")
        self.assertEqual(project["current_status"], "failed_delivery_readiness")
        self.assertIn("不证明工资政策、法域、税务、舍入或真实算薪合规", project["summary"])
        self.assertIn("不得声明生产 payroll readiness", project["summary"])
        self.assertEqual(len(project["features"]), 5)
        self.assertEqual(len(project["models"]), 2)
        self.assertEqual(len(project["formulas"]), 10)
        self.assertEqual(len(project["parameters"]), 80)
        self.assertEqual(len(project["strategies"]), 3)

        model_ids = {item["model_id"] for item in project["models"]}
        formula_ids = {item["formula_id"] for item in project["formulas"]}
        parameter_ids = {item["parameter_id"] for item in project["parameters"]}
        self.assertEqual({"MOD-001", "MOD-002"}, model_ids)
        self.assertEqual({f"FORM-{index:03d}" for index in range(1, 11)}, formula_ids)
        self.assertEqual({f"PARAM-{index:03d}" for index in range(1, 81)}, parameter_ids)

        evidence_ids = {item["evidence_id"] for item in project["evidence_refs"]}
        self.assertIn("EVID-REVIEW9-S5PAT04-MANIFEST", evidence_ids)
        self.assertIn("EVID-WHKM-SEMANTIC-MANIFEST", evidence_ids)
        for section in ("features", "models", "formulas", "parameters", "strategies", "validations"):
            for item in project[section]:
                for evidence_id in item["evidence_refs"]:
                    self.assertIn(evidence_id, evidence_ids)

        parameter_semantic_counts = Counter(item["semantic_status"] for item in project["parameters"])
        formula_semantic_counts = Counter(item["semantic_status"] for item in project["formulas"])
        parameter_fact_counts = Counter(item["fact_level"] for item in project["parameters"])
        self.assertEqual(parameter_semantic_counts["MACHINE_VERIFIED"], 78)
        self.assertEqual(parameter_semantic_counts["HUMAN_REVIEW_REQUIRED"], 2)
        self.assertEqual(formula_semantic_counts["MACHINE_VERIFIED"], 9)
        self.assertEqual(formula_semantic_counts["HUMAN_REVIEW_REQUIRED"], 1)
        self.assertEqual(parameter_fact_counts["UNKNOWN"], 78)
        self.assertEqual(parameter_fact_counts["EXTRACTED"], 2)
        limitations = " ".join(item["statement"] for item in project["limitations"])
        self.assertIn("PARAM-004、PARAM-005 与 FORM-010 仍为 HUMAN_REVIEW_REQUIRED", limitations)
        self.assertIn("78 个参数的政策、法域、生效日期、税务、舍入或工资依据仍为 UNKNOWN", limitations)
        self.assertIn("delivery_readiness 仍为 FAILED", limitations)
        self.assertIn("不引入任何真实 payroll 数据", limitations)
        self.assertEqual(project["validations"][0]["status"], "PARTIAL")
        self.assertEqual(project["delivery_readiness"]["status"], "FAILED")
        self.assertTrue(project["delivery_readiness"]["owner_decision_required"])

    def test_review9_s5pat04_whkm_roadmap_tracks_single_project_task(self) -> None:
        validator = load_validator_module()
        roadmap = validator.load_yaml(ROOT / "whkmSalary" / "docs" / "governance" / "roadmap.yaml")
        self.assertEqual(roadmap["schema_version"], "codexproject.roadmap.v1")
        self.assertEqual(roadmap["project_id"], "whkmSalary")
        self.assertEqual(roadmap["current_stage_id"], "S5")
        self.assertEqual(roadmap["current_phase_id"], "S5PA")
        self.assertEqual(roadmap["current_task_id"], "S5PAT04")
        self.assertEqual(roadmap["next_gate_id"], "S5PA-GATE-PENDING-MAIN-MERGE")
        self.assertEqual(roadmap["total_estimated_hours"], 5)
        self.assertEqual(roadmap["completed_estimated_hours"], 5)

        tasks = [
            task
            for stage in roadmap["stages"]
            for phase in stage["phases"]
            for task in phase["tasks"]
        ]
        self.assertEqual([task["task_id"] for task in tasks], ["S5PAT04"])
        task = tasks[0]
        self.assertEqual(task["status"], "completed")
        self.assertEqual(task["dependencies"], ["S5PAT03"])
        self.assertEqual(task["acceptance_ids"], ["ACC-S5PAT04"])
        self.assertIn("whkmSalary/docs/governance/project.yaml", task["evidence_refs"])
        self.assertIn("一次 PR 同时迁移多个项目", roadmap["stages"][0]["stop_conditions"])
        self.assertIn("批量脚本产生无证据事实", roadmap["stages"][0]["phases"][0]["stop_conditions"])

    def test_review9_s5pat04_whkm_events_preserve_truth_levels(self) -> None:
        events = [
            json.loads(line)
            for line in (ROOT / "whkmSalary" / "docs" / "governance" / "events.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
            if line.strip()
        ]
        self.assertEqual(len(events), 4)
        self.assertEqual({event["schema_version"] for event in events}, {"codexproject.event.v1"})
        self.assertTrue({event["fact_level"] for event in events}.issubset({"VERIFIED", "RECONSTRUCTED", "PROPOSED", "UNKNOWN"}))
        by_id = {event["event_id"]: event for event in events}
        self.assertEqual(by_id["EVT-WHKM-SEMANTIC-20260621-001"]["fact_level"], "RECONSTRUCTED")
        self.assertIn("Coverage remains in_progress", by_id["EVT-WHKM-SEMANTIC-20260621-001"]["notes"])
        self.assertEqual(by_id["EVT-WHKM-REVIEW8-OWNER-DECISION-20260622-001"]["fact_level"], "UNKNOWN")
        self.assertEqual(by_id["EVT-WHKM-REVIEW9-S5PAT04-LOCAL"]["fact_level"], "PROPOSED")
        self.assertIn("Must remain PROPOSED", by_id["EVT-WHKM-REVIEW9-S5PAT04-LOCAL"]["notes"])
        self.assertFalse(any(event["runtime_behavior_changed"] for event in events))

    def test_review9_s5pat04_whkm_human_files_render_without_drift(self) -> None:
        cli = load_lean_governance_module()
        result = cli.check_render_project_files(ROOT / "whkmSalary")
        self.assertEqual(result["drift_count"], 0, result["drift"])
        self.assertEqual(result["reference_issue_count"], 0, result["reference_issues"])

        feature_text = (ROOT / "whkmSalary" / "功能清单").read_text(encoding="utf-8")
        dev_text = (ROOT / "whkmSalary" / "开发记录").read_text(encoding="utf-8")
        model_text = (ROOT / "whkmSalary" / "模型参数文件").read_text(encoding="utf-8")
        self.assertIn("# 功能清单", feature_text)
        self.assertIn("FEAT-WHKM-005", feature_text)
        self.assertIn("Stage -> Phase -> Task", dev_text)
        self.assertIn("S5PAT04", dev_text)
        self.assertIn("MOD-002", model_text)
        self.assertIn("PARAM-080", model_text)
        for text in (feature_text, dev_text, model_text):
            self.assertNotIn("docs/governance/", text.splitlines()[0])

    def test_review9_s5pat04_files_are_project_governance_only(self) -> None:
        sync = load_sync_module()
        project = {
            "project_id": "whkmSalary",
            "path": "whkmSalary",
            "model_behavior_globs": ["*.py"],
        }
        changes, _ = sync.classify_changes(
            {"projects": [project]},
            [
                "whkmSalary/docs/governance/project.yaml",
                "whkmSalary/docs/governance/roadmap.yaml",
                "whkmSalary/docs/governance/events.jsonl",
                "whkmSalary/功能清单",
                "whkmSalary/开发记录",
                "whkmSalary/模型参数文件",
            ],
        )
        self.assertEqual(len(changes), 1)
        self.assertEqual(changes[0].classifications, {"governance_only_change", "trivial_change"})
        self.assertEqual(
            changes[0].updated_governance_files,
            {
                "docs/governance/project.yaml",
                "docs/governance/roadmap.yaml",
                "docs/governance/events.jsonl",
            },
        )
        validation = sync.SyncValidation()
        sync.validate_diff_contract(validation, changes)
        self.assertFalse(validation.errors)

    def test_review9_s5pat04_manifest_records_whkm_only_scope(self) -> None:
        manifest = json.loads(
            (
                ROOT
                / "governance"
                / "run_manifests"
                / "GOV-REVIEW9-S5PAT04-WHKM-SALARY-CANONICAL-RENDER-20260624.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(manifest["project_id"], "whkmSalary")
        self.assertEqual(manifest["task_id"], "S5PAT04")
        self.assertEqual(manifest["acceptance_ids"], ["ACC-S5PAT04"])
        self.assertEqual(manifest["binding_status"], "PRECOMMIT_TREE_BOUND")
        self.assertIn("review9_stage5_single_project_migration", manifest["change_classification"])
        self.assertIn("whkm_salary_only_scope", manifest["change_classification"])
        changed = set(manifest["changed_files_actual"])
        for path in {
            "whkmSalary/docs/governance/project.yaml",
            "whkmSalary/docs/governance/roadmap.yaml",
            "whkmSalary/docs/governance/events.jsonl",
            "whkmSalary/功能清单",
            "whkmSalary/开发记录",
            "whkmSalary/模型参数文件",
            "tests/governance/test_project_governance_validator.py",
            "governance/run_manifests/GOV-REVIEW9-S5PAT04-WHKM-SALARY-CANONICAL-RENDER-20260624.json",
        }:
            self.assertIn(path, changed)
        self.assertFalse(any(path.startswith(("EVA_OS/", "OpMe_System/", "EEI/")) for path in changed))
        self.assertIn("S5PA-GATE may be evaluated after this PR", " ".join(manifest["unresolved_risks"]))
        self.assertIn("whkmSalary delivery readiness remains FAILED", " ".join(manifest["unresolved_risks"]))

    def test_review9_s5pbt01_eei_project_yaml_preserves_delivery_truth(self) -> None:
        validator = load_validator_module()
        project = validator.load_yaml(ROOT / "EEI" / "docs" / "governance" / "project.yaml")
        self.assertEqual(project["schema_version"], "codexproject.project.v1")
        self.assertEqual(project["project_id"], "EEI")
        self.assertEqual(project["fact_level"], "EXTRACTED")
        self.assertEqual(project["current_status"], "failed_delivery_readiness")
        self.assertIn("不把研究评分", project["summary"])
        self.assertIn("production/publication readiness", project["summary"])
        self.assertEqual(len(project["features"]), 5)
        self.assertEqual(len(project["models"]), 11)
        self.assertEqual(len(project["formulas"]), 11)
        self.assertEqual(len(project["parameters"]), 68)
        self.assertEqual(len(project["strategies"]), 3)

        model_ids = {item["model_id"] for item in project["models"]}
        formula_ids = {item["formula_id"] for item in project["formulas"]}
        parameter_ids = {item["parameter_id"] for item in project["parameters"]}
        self.assertEqual({f"MOD-{index:03d}" for index in range(1, 11)} | {"MOD-012"}, model_ids)
        self.assertNotIn("MOD-011", model_ids)
        self.assertEqual({f"FORM-{index:03d}" for index in range(1, 11)} | {"FORM-012"}, formula_ids)
        self.assertNotIn("FORM-011", formula_ids)
        self.assertEqual({f"PARAM-{index:03d}" for index in range(1, 69)}, parameter_ids)

        evidence_ids = {item["evidence_id"] for item in project["evidence_refs"]}
        self.assertIn("EVID-REVIEW9-S5PBT01-MANIFEST", evidence_ids)
        self.assertIn("EVID-EEI-SEMANTIC-MANIFEST", evidence_ids)
        for section in ("features", "models", "formulas", "parameters", "strategies", "validations"):
            for item in project[section]:
                for evidence_id in item["evidence_refs"]:
                    self.assertIn(evidence_id, evidence_ids)

        parameter_semantic_counts = Counter(item["semantic_status"] for item in project["parameters"])
        formula_semantic_counts = Counter(item["semantic_status"] for item in project["formulas"])
        model_semantic_counts = Counter(item["semantic_status"] for item in project["models"])
        parameter_fact_counts = Counter(item["fact_level"] for item in project["parameters"])
        self.assertEqual(parameter_semantic_counts["MACHINE_VERIFIED"], 61)
        self.assertEqual(parameter_semantic_counts["HUMAN_REVIEW_REQUIRED"], 7)
        self.assertEqual(formula_semantic_counts["MACHINE_VERIFIED"], 10)
        self.assertEqual(formula_semantic_counts["HUMAN_REVIEW_REQUIRED"], 1)
        self.assertEqual(model_semantic_counts["MACHINE_VERIFIED"], 10)
        self.assertEqual(model_semantic_counts["HUMAN_REVIEW_REQUIRED"], 1)
        self.assertEqual(parameter_fact_counts["EXTRACTED"], 61)
        self.assertEqual(parameter_fact_counts["UNKNOWN"], 7)
        limitations = " ".join(item["statement"] for item in project["limitations"])
        self.assertIn("FORM-012 与 PARAM-052..PARAM-058", limitations)
        self.assertIn("delivery_readiness 仍为 FAILED", limitations)
        self.assertIn("A209 24h soak", limitations)
        self.assertIn("不改 scoring formula", limitations)
        self.assertEqual(project["delivery_readiness"]["status"], "FAILED")
        self.assertTrue(project["delivery_readiness"]["owner_decision_required"])

    def test_review9_s5pbt01_eei_roadmap_tracks_single_project_task(self) -> None:
        validator = load_validator_module()
        roadmap = validator.load_yaml(ROOT / "EEI" / "docs" / "governance" / "roadmap.yaml")
        self.assertEqual(roadmap["schema_version"], "codexproject.roadmap.v1")
        self.assertEqual(roadmap["project_id"], "EEI")
        self.assertEqual(roadmap["current_stage_id"], "S5")
        self.assertEqual(roadmap["current_phase_id"], "S5PB")
        self.assertEqual(roadmap["current_task_id"], "S5PBT01")
        self.assertEqual(roadmap["next_gate_id"], "S5PB-GATE-IN-PROGRESS")
        self.assertEqual(roadmap["total_estimated_hours"], 4)
        self.assertEqual(roadmap["completed_estimated_hours"], 4)

        tasks = [
            task
            for stage in roadmap["stages"]
            for phase in stage["phases"]
            for task in phase["tasks"]
        ]
        self.assertEqual([task["task_id"] for task in tasks], ["S5PBT01"])
        task = tasks[0]
        self.assertEqual(task["status"], "completed")
        self.assertEqual(task["dependencies"], ["S5PAT04"])
        self.assertEqual(task["acceptance_ids"], ["ACC-S5PBT01"])
        self.assertIn("EEI/docs/governance/project.yaml", task["evidence_refs"])
        self.assertIn("任何项目缺少 owner-readable 三文件", roadmap["stages"][0]["phases"][0]["stop_conditions"])
        self.assertIn("未知事实被写成 VERIFIED", roadmap["stages"][0]["phases"][0]["stop_conditions"])

    def test_review9_s5pbt01_eei_events_preserve_truth_levels(self) -> None:
        events = [
            json.loads(line)
            for line in (ROOT / "EEI" / "docs" / "governance" / "events.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
            if line.strip()
        ]
        self.assertEqual(len(events), 4)
        self.assertEqual({event["schema_version"] for event in events}, {"codexproject.event.v1"})
        self.assertTrue({event["fact_level"] for event in events}.issubset({"VERIFIED", "EXTRACTED", "RECONSTRUCTED", "PROPOSED", "UNKNOWN"}))
        by_id = {event["event_id"]: event for event in events}
        self.assertEqual(by_id["EVT-EEI-SEMANTIC-20260621-001"]["fact_level"], "RECONSTRUCTED")
        self.assertIn("not model validity", by_id["EVT-EEI-SEMANTIC-20260621-001"]["notes"])
        self.assertEqual(by_id["EVT-EEI-A202-20260623-010"]["fact_level"], "EXTRACTED")
        self.assertIn("not real source-license", by_id["EVT-EEI-A202-20260623-010"]["notes"])
        self.assertEqual(by_id["EVT-EEI-REVIEW8-OWNER-DECISION-20260623-001"]["fact_level"], "UNKNOWN")
        self.assertEqual(by_id["EVT-EEI-REVIEW9-S5PBT01-LOCAL"]["fact_level"], "PROPOSED")
        self.assertFalse(any(event["runtime_behavior_changed"] for event in events))

    def test_review9_s5pbt01_eei_human_files_render_without_drift(self) -> None:
        cli = load_lean_governance_module()
        result = cli.check_render_project_files(ROOT / "EEI")
        self.assertEqual(result["drift_count"], 0, result["drift"])
        self.assertEqual(result["reference_issue_count"], 0, result["reference_issues"])

        feature_text = (ROOT / "EEI" / "功能清单").read_text(encoding="utf-8")
        dev_text = (ROOT / "EEI" / "开发记录").read_text(encoding="utf-8")
        model_text = (ROOT / "EEI" / "模型参数文件").read_text(encoding="utf-8")
        self.assertIn("# 功能清单", feature_text)
        self.assertIn("FEAT-EEI-005", feature_text)
        self.assertIn("Stage -> Phase -> Task", dev_text)
        self.assertIn("S5PBT01", dev_text)
        self.assertIn("MOD-012", model_text)
        self.assertIn("PARAM-068", model_text)
        for text in (feature_text, dev_text, model_text):
            self.assertNotIn("docs/governance/", text.splitlines()[0])

    def test_review9_s5pbt01_files_are_project_governance_only(self) -> None:
        sync = load_sync_module()
        project = {
            "project_id": "EEI",
            "path": "EEI",
            "model_behavior_globs": ["apps/**/*", "scripts/**/*", "packages/**/*", "*.py"],
        }
        changes, _ = sync.classify_changes(
            {"projects": [project]},
            [
                "EEI/docs/governance/project.yaml",
                "EEI/docs/governance/roadmap.yaml",
                "EEI/docs/governance/events.jsonl",
                "EEI/功能清单",
                "EEI/开发记录",
                "EEI/模型参数文件",
            ],
        )
        self.assertEqual(len(changes), 1)
        self.assertEqual(changes[0].classifications, {"governance_only_change", "trivial_change"})
        self.assertEqual(
            changes[0].updated_governance_files,
            {
                "docs/governance/project.yaml",
                "docs/governance/roadmap.yaml",
                "docs/governance/events.jsonl",
            },
        )
        validation = sync.SyncValidation()
        sync.validate_diff_contract(validation, changes)
        self.assertFalse(validation.errors)

    def test_review9_s5pbt01_manifest_records_eei_only_scope(self) -> None:
        manifest = json.loads(
            (
                ROOT
                / "governance"
                / "run_manifests"
                / "GOV-REVIEW9-S5PBT01-EEI-CANONICAL-RENDER-20260624.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(manifest["project_id"], "EEI")
        self.assertEqual(manifest["task_id"], "S5PBT01")
        self.assertEqual(manifest["acceptance_ids"], ["ACC-S5PBT01"])
        self.assertEqual(manifest["binding_status"], "PRECOMMIT_TREE_BOUND")
        self.assertIn("review9_stage5_single_project_migration", manifest["change_classification"])
        self.assertIn("eei_only_scope", manifest["change_classification"])
        changed = set(manifest["changed_files_actual"])
        for path in {
            "EEI/CHECKSUMS.sha256",
            "EEI/DIRECTORY_TREE.txt",
            "EEI/artifacts/release_evidence_t1211.json",
            "EEI/artifacts/tests/a200/Enterprise_Ecosystem_Intelligence_clean_room_t1215.zip",
            "EEI/artifacts/tests/a200/t1215_clean_room_release.json",
            "EEI/docs/governance/project.yaml",
            "EEI/docs/governance/roadmap.yaml",
            "EEI/docs/governance/events.jsonl",
            "EEI/manifest.txt",
            "EEI/scripts/manage_clean_room_release.py",
            "EEI/scripts/manage_release_artifacts.py",
            "EEI/tests/unit/test_clean_room_release_paths.py",
            "EEI/功能清单",
            "EEI/开发记录",
            "EEI/模型参数文件",
            "scripts/validate_governance_sync.py",
            "tests/governance/test_project_governance_validator.py",
            "governance/run_manifests/GOV-REVIEW9-S5PBT01-EEI-CANONICAL-RENDER-20260624.json",
        }:
            self.assertIn(path, changed)
        self.assertFalse(any(path.startswith(("EVA_OS/", "OpMe_System/", "whkmSalary/")) for path in changed))
        self.assertIn("S5PB-GATE remains in_progress", " ".join(manifest["unresolved_risks"]))
        self.assertIn("EEI delivery readiness remains FAILED", " ".join(manifest["unresolved_risks"]))

    def test_review9_s5pbt02_fifa_project_yaml_preserves_research_only_truth(self) -> None:
        validator = load_validator_module()
        project = validator.load_yaml(ROOT / "FIFA" / "docs" / "governance" / "project.yaml")
        self.assertEqual(project["schema_version"], "codexproject.project.v1")
        self.assertEqual(project["project_id"], "FIFA")
        self.assertEqual(project["fact_level"], "EXTRACTED")
        self.assertEqual(project["current_status"], "unverified_delivery_readiness")
        self.assertIn("research-only", project["summary"])
        self.assertIn("production readiness", project["summary"])
        self.assertEqual(len(project["features"]), 6)
        self.assertEqual(len(project["models"]), 11)
        self.assertEqual(len(project["formulas"]), 11)
        self.assertEqual(len(project["parameters"]), 108)
        self.assertEqual(len(project["strategies"]), 3)

        model_ids = {item["model_id"] for item in project["models"]}
        formula_ids = {item["formula_id"] for item in project["formulas"]}
        parameter_ids = {item["parameter_id"] for item in project["parameters"]}
        self.assertEqual({f"MOD-{index:03d}" for index in range(1, 12)}, model_ids)
        self.assertEqual({f"FORM-{index:03d}" for index in range(1, 12)}, formula_ids)
        self.assertEqual({f"PARAM-{index:03d}" for index in range(1, 109)}, parameter_ids)
        self.assertNotIn("PARAM-109", parameter_ids)

        evidence_ids = {item["evidence_id"] for item in project["evidence_refs"]}
        self.assertIn("EVID-REVIEW9-S5PBT02-MANIFEST", evidence_ids)
        self.assertIn("EVID-SEMANTIC-FIFA-MANIFEST", evidence_ids)
        for section in ("features", "models", "formulas", "parameters", "strategies", "validations"):
            for item in project[section]:
                for evidence_id in item["evidence_refs"]:
                    self.assertIn(evidence_id, evidence_ids)

        parameter_semantic_counts = Counter(item["semantic_status"] for item in project["parameters"])
        formula_semantic_counts = Counter(item["semantic_status"] for item in project["formulas"])
        model_semantic_counts = Counter(item["semantic_status"] for item in project["models"])
        self.assertEqual(parameter_semantic_counts["MACHINE_VERIFIED"], 91)
        self.assertEqual(parameter_semantic_counts["HUMAN_REVIEW_REQUIRED"], 17)
        self.assertEqual(formula_semantic_counts["MACHINE_VERIFIED_WITH_HUMAN_REVIEW_CAVEATS"], 10)
        self.assertEqual(formula_semantic_counts["HUMAN_REVIEW_REQUIRED"], 1)
        self.assertEqual(model_semantic_counts["MACHINE_VERIFIED_WITH_HUMAN_REVIEW_CAVEATS"], 10)
        self.assertEqual(model_semantic_counts["HUMAN_REVIEW_REQUIRED"], 1)

        limitations = " ".join(item["statement"] for item in project["limitations"])
        self.assertIn("91/108 active parameters", limitations)
        self.assertIn("17 个 active parameters", limitations)
        self.assertIn("delivery_readiness 仍为 UNVERIFIED", limitations)
        self.assertIn("不改 odds parsing", limitations)
        self.assertEqual(project["delivery_readiness"]["status"], "UNVERIFIED")
        self.assertTrue(project["delivery_readiness"]["owner_decision_required"])
        self.assertEqual(project["delivery_readiness"]["blocked_requirements"], 6)

        matrix = validator.load_yaml(ROOT / "FIFA" / "docs" / "governance" / "VERSION_MATRIX.yaml")
        self.assertEqual(matrix["current_iteration"], "ITER-20260624-REVIEW9-S5PBT02")
        self.assertEqual(matrix["current_phase"], "S5PB")
        self.assertEqual(matrix["current_gate"], "S5PB-GATE-IN-PROGRESS")

    def test_review9_s5pbt02_fifa_roadmap_tracks_single_project_task(self) -> None:
        validator = load_validator_module()
        roadmap = validator.load_yaml(ROOT / "FIFA" / "docs" / "governance" / "roadmap.yaml")
        self.assertEqual(roadmap["schema_version"], "codexproject.roadmap.v1")
        self.assertEqual(roadmap["project_id"], "FIFA")
        self.assertEqual(roadmap["current_stage_id"], "S5")
        self.assertEqual(roadmap["current_phase_id"], "S5PB")
        self.assertEqual(roadmap["current_task_id"], "S5PBT02")
        self.assertEqual(roadmap["next_gate_id"], "S5PB-GATE-IN-PROGRESS")
        self.assertEqual(roadmap["total_estimated_hours"], 4)
        self.assertEqual(roadmap["completed_estimated_hours"], 4)

        tasks = [
            task
            for stage in roadmap["stages"]
            for phase in stage["phases"]
            for task in phase["tasks"]
        ]
        self.assertEqual([task["task_id"] for task in tasks], ["S5PBT02"])
        task = tasks[0]
        self.assertEqual(task["status"], "completed")
        self.assertEqual(task["dependencies"], ["S5PBT01"])
        self.assertEqual(task["acceptance_ids"], ["ACC-S5PBT02"])
        self.assertIn("FIFA/docs/governance/project.yaml", task["evidence_refs"])
        self.assertIn("任何项目缺少 owner-readable 三文件", roadmap["stages"][0]["phases"][0]["stop_conditions"])
        self.assertIn("未知事实被写成 VERIFIED", roadmap["stages"][0]["phases"][0]["stop_conditions"])

    def test_review9_s5pbt02_fifa_events_preserve_truth_levels(self) -> None:
        events = [
            json.loads(line)
            for line in (ROOT / "FIFA" / "docs" / "governance" / "events.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
            if line.strip()
        ]
        self.assertEqual(len(events), 4)
        self.assertEqual({event["schema_version"] for event in events}, {"codexproject.event.v1"})
        self.assertTrue({event["fact_level"] for event in events}.issubset({"VERIFIED", "EXTRACTED", "RECONSTRUCTED", "PROPOSED", "UNKNOWN"}))
        by_id = {event["event_id"]: event for event in events}
        self.assertEqual(by_id["EVT-FIFA-SEMANTIC-20260621-001"]["fact_level"], "RECONSTRUCTED")
        self.assertIn("not model validity", by_id["EVT-FIFA-SEMANTIC-20260621-001"]["notes"])
        self.assertEqual(by_id["EVT-FIFA-REVIEW6-FINAL-20260622-001"]["fact_level"], "EXTRACTED")
        self.assertIn("UNVERIFIED", by_id["EVT-FIFA-REVIEW6-FINAL-20260622-001"]["summary"])
        self.assertEqual(by_id["EVT-FIFA-OWNER-DECISION-20260622-001"]["fact_level"], "UNKNOWN")
        self.assertEqual(by_id["EVT-FIFA-REVIEW9-S5PBT02-LOCAL"]["fact_level"], "PROPOSED")
        self.assertFalse(any(event["runtime_behavior_changed"] for event in events))

    def test_review9_s5pbt02_fifa_human_files_render_without_drift(self) -> None:
        cli = load_lean_governance_module()
        result = cli.check_render_project_files(ROOT / "FIFA")
        self.assertEqual(result["drift_count"], 0, result["drift"])
        self.assertEqual(result["reference_issue_count"], 0, result["reference_issues"])

        feature_text = (ROOT / "FIFA" / "功能清单").read_text(encoding="utf-8")
        dev_text = (ROOT / "FIFA" / "开发记录").read_text(encoding="utf-8")
        model_text = (ROOT / "FIFA" / "模型参数文件").read_text(encoding="utf-8")
        self.assertIn("# 功能清单", feature_text)
        self.assertIn("FEAT-FIFA-006", feature_text)
        self.assertIn("ai_controlled_access_rejected", feature_text)
        self.assertIn("Stage -> Phase -> Task", dev_text)
        self.assertIn("S5PBT02", dev_text)
        self.assertIn("MOD-011", model_text)
        self.assertIn("PARAM-108", model_text)
        for text in (feature_text, dev_text, model_text):
            self.assertNotIn("docs/governance/", text.splitlines()[0])

    def test_review9_s5pbt02_files_are_project_governance_only(self) -> None:
        sync = load_sync_module()
        project = {
            "project_id": "FIFA",
            "path": "FIFA",
            "model_behavior_globs": ["tab-research-pipeline/**/*", "legacy/**/*", "ops/**/*", "*.py"],
        }
        changes, _ = sync.classify_changes(
            {"projects": [project]},
            [
                "FIFA/docs/governance/project.yaml",
                "FIFA/docs/governance/roadmap.yaml",
                "FIFA/docs/governance/events.jsonl",
                "FIFA/docs/governance/VERSION_MATRIX.yaml",
                "FIFA/功能清单",
                "FIFA/开发记录",
                "FIFA/模型参数文件",
            ],
        )
        self.assertEqual(len(changes), 1)
        self.assertEqual(changes[0].classifications, {"governance_only_change", "trivial_change"})
        self.assertEqual(
            changes[0].updated_governance_files,
            {
                "docs/governance/project.yaml",
                "docs/governance/roadmap.yaml",
                "docs/governance/events.jsonl",
                "docs/governance/VERSION_MATRIX.yaml",
            },
        )
        validation = sync.SyncValidation()
        sync.validate_diff_contract(validation, changes)
        self.assertFalse(validation.errors)

    def test_review9_s5pbt02_manifest_records_fifa_only_scope(self) -> None:
        manifest = json.loads(
            (
                ROOT
                / "governance"
                / "run_manifests"
                / "GOV-REVIEW9-S5PBT02-FIFA-CANONICAL-RENDER-20260624.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(manifest["project_id"], "FIFA")
        self.assertEqual(manifest["task_id"], "S5PBT02")
        self.assertEqual(manifest["acceptance_ids"], ["ACC-S5PBT02"])
        self.assertEqual(manifest["binding_status"], "PRECOMMIT_TREE_BOUND")
        self.assertIn("review9_stage5_single_project_migration", manifest["change_classification"])
        self.assertIn("fifa_only_scope", manifest["change_classification"])
        changed = set(manifest["changed_files_actual"])
        for path in {
            "FIFA/docs/governance/project.yaml",
            "FIFA/docs/governance/roadmap.yaml",
            "FIFA/docs/governance/events.jsonl",
            "FIFA/docs/governance/VERSION_MATRIX.yaml",
            "FIFA/功能清单",
            "FIFA/开发记录",
            "FIFA/模型参数文件",
            "tests/governance/test_project_governance_validator.py",
            "governance/run_manifests/GOV-REVIEW9-S5PBT02-FIFA-CANONICAL-RENDER-20260624.json",
        }:
            self.assertIn(path, changed)
        self.assertFalse(any(path.startswith(("EEI/", "OpenAIDatabase/", "PFI_BIG_DATA_SIMULATOR/")) for path in changed))
        self.assertIn("S5PB-GATE remains in_progress", " ".join(manifest["unresolved_risks"]))
        self.assertIn("FIFA delivery readiness remains UNVERIFIED", " ".join(manifest["unresolved_risks"]))

    def test_review9_s5pbt03_openaidatabase_project_yaml_preserves_memory_truth(self) -> None:
        validator = load_validator_module()
        project = validator.load_yaml(ROOT / "OpenAIDatabase" / "docs" / "governance" / "project.yaml")
        self.assertEqual(project["schema_version"], "codexproject.project.v1")
        self.assertEqual(project["project_id"], "OpenAIDatabase")
        self.assertEqual(project["fact_level"], "EXTRACTED")
        self.assertEqual(project["current_status"], "failed_delivery_readiness")
        self.assertIn("partial semantic extraction", project["summary"])
        self.assertIn("draft proposal", project["summary"])
        self.assertEqual(len(project["features"]), 5)
        self.assertEqual(len(project["models"]), 11)
        self.assertEqual(len(project["formulas"]), 11)
        self.assertEqual(len(project["parameters"]), 92)
        self.assertEqual(len(project["strategies"]), 2)

        model_ids = {item["model_id"] for item in project["models"]}
        formula_ids = {item["formula_id"] for item in project["formulas"]}
        parameter_ids = {item["parameter_id"] for item in project["parameters"]}
        self.assertEqual({f"MOD-{index:03d}" for index in range(1, 12)}, model_ids)
        self.assertEqual({f"FORM-{index:03d}" for index in range(1, 12)}, formula_ids)
        self.assertEqual({f"PARAM-{index:03d}" for index in range(1, 93)}, parameter_ids)

        evidence_ids = {item["evidence_id"] for item in project["evidence_refs"]}
        self.assertIn("EVID-REVIEW9-S5PBT03-MANIFEST", evidence_ids)
        self.assertIn("EVID-SEMANTIC-OAIDB-MANIFEST", evidence_ids)
        for section in ("features", "models", "formulas", "parameters", "strategies", "validations"):
            for item in project[section]:
                for evidence_id in item["evidence_refs"]:
                    self.assertIn(evidence_id, evidence_ids)

        parameter_semantic_counts = Counter(item["semantic_status"] for item in project["parameters"])
        formula_semantic_counts = Counter(item["semantic_status"] for item in project["formulas"])
        model_semantic_counts = Counter(item["semantic_status"] for item in project["models"])
        self.assertEqual(parameter_semantic_counts["MACHINE_VERIFIED"], 28)
        self.assertEqual(parameter_semantic_counts["HUMAN_REVIEW_REQUIRED"], 64)
        self.assertEqual(formula_semantic_counts["MACHINE_VERIFIED"], 10)
        self.assertEqual(formula_semantic_counts["HUMAN_REVIEW_REQUIRED"], 1)
        self.assertEqual(model_semantic_counts["MACHINE_VERIFIED_WITH_HUMAN_REVIEW_CAVEATS"], 10)
        self.assertEqual(model_semantic_counts["HUMAN_REVIEW_REQUIRED"], 1)

        limitations = " ".join(item["statement"] for item in project["limitations"])
        self.assertIn("28/92 active parameters", limitations)
        self.assertIn("64 个 active parameters 与 FORM-010", limitations)
        self.assertIn("delivery_readiness 仍为 FAILED", limitations)
        self.assertIn("不改 memory extraction", limitations)
        self.assertEqual(project["delivery_readiness"]["status"], "FAILED")
        self.assertTrue(project["delivery_readiness"]["owner_decision_required"])
        self.assertEqual(project["delivery_readiness"]["blocked_requirements"], 2)
        self.assertEqual(project["delivery_readiness"]["active_requirements"], 9)

        matrix = validator.load_yaml(ROOT / "OpenAIDatabase" / "docs" / "governance" / "VERSION_MATRIX.yaml")
        self.assertEqual(matrix["current_iteration"], "ITER-20260624-REVIEW9-S5PBT03")
        self.assertEqual(matrix["current_phase"], "S5PB")
        self.assertEqual(matrix["current_gate"], "S5PB-GATE-IN-PROGRESS")

    def test_review9_s5pbt03_openaidatabase_roadmap_tracks_single_project_task(self) -> None:
        validator = load_validator_module()
        roadmap = validator.load_yaml(ROOT / "OpenAIDatabase" / "docs" / "governance" / "roadmap.yaml")
        self.assertEqual(roadmap["schema_version"], "codexproject.roadmap.v1")
        self.assertEqual(roadmap["project_id"], "OpenAIDatabase")
        self.assertEqual(roadmap["current_stage_id"], "S5")
        self.assertEqual(roadmap["current_phase_id"], "S5PB")
        self.assertEqual(roadmap["current_task_id"], "S5PBT03")
        self.assertEqual(roadmap["next_gate_id"], "S5PB-GATE-IN-PROGRESS")
        self.assertEqual(roadmap["total_estimated_hours"], 4)
        self.assertEqual(roadmap["completed_estimated_hours"], 4)

        tasks = [
            task
            for stage in roadmap["stages"]
            for phase in stage["phases"]
            for task in phase["tasks"]
        ]
        self.assertEqual([task["task_id"] for task in tasks], ["S5PBT03"])
        task = tasks[0]
        self.assertEqual(task["status"], "completed")
        self.assertEqual(task["dependencies"], ["S5PBT02"])
        self.assertEqual(task["acceptance_ids"], ["ACC-S5PBT03"])
        self.assertIn("OpenAIDatabase/docs/governance/project.yaml", task["evidence_refs"])
        self.assertIn("任何项目缺少 owner-readable 三文件", roadmap["stages"][0]["phases"][0]["stop_conditions"])
        self.assertIn("未知事实被写成 VERIFIED", roadmap["stages"][0]["phases"][0]["stop_conditions"])

    def test_review9_s5pbt03_openaidatabase_events_preserve_truth_levels(self) -> None:
        events = [
            json.loads(line)
            for line in (ROOT / "OpenAIDatabase" / "docs" / "governance" / "events.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
            if line.strip()
        ]
        self.assertEqual(len(events), 4)
        self.assertEqual({event["schema_version"] for event in events}, {"codexproject.event.v1"})
        self.assertTrue({event["fact_level"] for event in events}.issubset({"VERIFIED", "EXTRACTED", "RECONSTRUCTED", "PROPOSED", "UNKNOWN"}))
        by_id = {event["event_id"]: event for event in events}
        self.assertEqual(by_id["EVT-OAIDB-SEMANTIC-20260621-001"]["fact_level"], "RECONSTRUCTED")
        self.assertIn("not model validity", by_id["EVT-OAIDB-SEMANTIC-20260621-001"]["notes"])
        self.assertEqual(by_id["EVT-OAIDB-REVIEW6-FINAL-20260622-001"]["fact_level"], "EXTRACTED")
        self.assertIn("FAILED", by_id["EVT-OAIDB-REVIEW6-FINAL-20260622-001"]["summary"])
        self.assertEqual(by_id["EVT-OAIDB-OWNER-DECISION-20260622-001"]["fact_level"], "UNKNOWN")
        self.assertEqual(by_id["EVT-OAIDB-REVIEW9-S5PBT03-LOCAL"]["fact_level"], "PROPOSED")
        self.assertFalse(any(event["runtime_behavior_changed"] for event in events))

    def test_review9_s5pbt03_openaidatabase_human_files_render_without_drift(self) -> None:
        cli = load_lean_governance_module()
        result = cli.check_render_project_files(ROOT / "OpenAIDatabase")
        self.assertEqual(result["drift_count"], 0, result["drift"])
        self.assertEqual(result["reference_issue_count"], 0, result["reference_issues"])

        feature_text = (ROOT / "OpenAIDatabase" / "功能清单").read_text(encoding="utf-8")
        dev_text = (ROOT / "OpenAIDatabase" / "开发记录").read_text(encoding="utf-8")
        model_text = (ROOT / "OpenAIDatabase" / "模型参数文件").read_text(encoding="utf-8")
        self.assertIn("# 功能清单", feature_text)
        self.assertIn("FEAT-OAIDB-005", feature_text)
        self.assertIn("FORM-010", feature_text)
        self.assertIn("Stage -> Phase -> Task", dev_text)
        self.assertIn("S5PBT03", dev_text)
        self.assertIn("MOD-011", model_text)
        self.assertIn("PARAM-092", model_text)
        for text in (feature_text, dev_text, model_text):
            self.assertNotIn("docs/governance/", text.splitlines()[0])

    def test_review9_s5pbt03_files_are_project_governance_only(self) -> None:
        sync = load_sync_module()
        project = {
            "project_id": "OpenAIDatabase",
            "path": "OpenAIDatabase",
            "model_behavior_globs": ["apps/**/*", "scripts/**/*", "skills/**/*", "data/**/*", "config/**/*", "*.py"],
        }
        changes, _ = sync.classify_changes(
            {"projects": [project]},
            [
                "OpenAIDatabase/docs/governance/project.yaml",
                "OpenAIDatabase/docs/governance/roadmap.yaml",
                "OpenAIDatabase/docs/governance/events.jsonl",
                "OpenAIDatabase/docs/governance/VERSION_MATRIX.yaml",
                "OpenAIDatabase/功能清单",
                "OpenAIDatabase/开发记录",
                "OpenAIDatabase/模型参数文件",
            ],
        )
        self.assertEqual(len(changes), 1)
        self.assertEqual(changes[0].classifications, {"governance_only_change", "trivial_change"})
        self.assertEqual(
            changes[0].updated_governance_files,
            {
                "docs/governance/project.yaml",
                "docs/governance/roadmap.yaml",
                "docs/governance/events.jsonl",
                "docs/governance/VERSION_MATRIX.yaml",
            },
        )
        validation = sync.SyncValidation()
        sync.validate_diff_contract(validation, changes)
        self.assertFalse(validation.errors)

    def test_review9_s5pbt03_manifest_records_openaidatabase_only_scope(self) -> None:
        manifest = json.loads(
            (
                ROOT
                / "governance"
                / "run_manifests"
                / "GOV-REVIEW9-S5PBT03-OPENAIDATABASE-CANONICAL-RENDER-20260624.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(manifest["project_id"], "OpenAIDatabase")
        self.assertEqual(manifest["task_id"], "S5PBT03")
        self.assertEqual(manifest["acceptance_ids"], ["ACC-S5PBT03"])
        self.assertEqual(manifest["binding_status"], "PRECOMMIT_TREE_BOUND")
        self.assertIn("review9_stage5_single_project_migration", manifest["change_classification"])
        self.assertIn("openaidatabase_only_scope", manifest["change_classification"])
        changed = set(manifest["changed_files_actual"])
        for path in {
            "OpenAIDatabase/docs/governance/project.yaml",
            "OpenAIDatabase/docs/governance/roadmap.yaml",
            "OpenAIDatabase/docs/governance/events.jsonl",
            "OpenAIDatabase/docs/governance/VERSION_MATRIX.yaml",
            "OpenAIDatabase/功能清单",
            "OpenAIDatabase/开发记录",
            "OpenAIDatabase/模型参数文件",
            "tests/governance/test_project_governance_validator.py",
            "governance/run_manifests/GOV-REVIEW9-S5PBT03-OPENAIDATABASE-CANONICAL-RENDER-20260624.json",
        }:
            self.assertIn(path, changed)
        self.assertFalse(any(path.startswith(("FIFA/", "PFI/", "arxiv-daily-push/")) for path in changed))
        self.assertIn("S5PB-GATE remains in_progress", " ".join(manifest["unresolved_risks"]))
        self.assertIn("OpenAIDatabase delivery readiness remains FAILED", " ".join(manifest["unresolved_risks"]))

    def test_review9_s5pbt04_pfi_project_yaml_preserves_strategy_truth(self) -> None:
        validator = load_validator_module()
        pfi_root = ROOT / "PFI" / "大数据模拟器"
        project = validator.load_yaml(pfi_root / "docs" / "governance" / "project.yaml")
        self.assertEqual(project["schema_version"], "codexproject.project.v1")
        self.assertEqual(project["project_id"], "PFI_BIG_DATA_SIMULATOR")
        self.assertEqual(project["fact_level"], "EXTRACTED")
        self.assertEqual(project["current_status"], "unverified_delivery_readiness")
        self.assertIn("策略族", project["summary"])
        self.assertIn("不把模拟胜出", project["summary"])
        self.assertIn("实盘有效", project["summary"])
        self.assertEqual(len(project["features"]), 6)
        self.assertEqual(len(project["models"]), 15)
        self.assertEqual(len(project["formulas"]), 15)
        self.assertEqual(len(project["parameters"]), 213)
        self.assertEqual(len(project["strategies"]), 2)

        model_ids = {item["model_id"] for item in project["models"]}
        formula_ids = {item["formula_id"] for item in project["formulas"]}
        parameter_ids = {item["parameter_id"] for item in project["parameters"]}
        self.assertEqual({f"MOD-{index:03d}" for index in range(1, 16)}, model_ids)
        self.assertEqual({f"FORM-{index:03d}" for index in range(1, 16)}, formula_ids)
        self.assertEqual({f"PARAM-{index:03d}" for index in range(1, 214)}, parameter_ids)

        evidence_ids = {item["evidence_id"] for item in project["evidence_refs"]}
        self.assertIn("EVID-REVIEW9-S5PBT04-MANIFEST", evidence_ids)
        self.assertIn("EVID-SEMANTIC-PFI-MANIFEST", evidence_ids)
        for section in ("features", "models", "formulas", "parameters", "strategies", "validations"):
            for item in project[section]:
                for evidence_id in item["evidence_refs"]:
                    self.assertIn(evidence_id, evidence_ids)

        parameter_semantic_counts = Counter(item["semantic_status"] for item in project["parameters"])
        formula_semantic_counts = Counter(item["semantic_status"] for item in project["formulas"])
        model_semantic_counts = Counter(item["semantic_status"] for item in project["models"])
        self.assertEqual(parameter_semantic_counts["MACHINE_VERIFIED"], 211)
        self.assertEqual(parameter_semantic_counts["HUMAN_REVIEW_REQUIRED"], 2)
        self.assertEqual(formula_semantic_counts["MACHINE_VERIFIED"], 15)
        self.assertEqual(model_semantic_counts["MACHINE_VERIFIED"], 15)

        limitations = " ".join(item["statement"] for item in project["limitations"])
        self.assertIn("211/213 active parameters", limitations)
        self.assertIn("PARAM-110/PARAM-111", limitations)
        self.assertIn("delivery_readiness 仍为 UNVERIFIED", limitations)
        self.assertIn("TASK-PFI-B-001", limitations)
        self.assertIn("不改策略规则", limitations)
        self.assertEqual(project["delivery_readiness"]["status"], "UNVERIFIED")
        self.assertTrue(project["delivery_readiness"]["owner_decision_required"])
        self.assertEqual(project["delivery_readiness"]["active_requirements"], 15)

        matrix = validator.load_yaml(pfi_root / "docs" / "governance" / "VERSION_MATRIX.yaml")
        self.assertEqual(matrix["current_iteration"], "ITER-20260624-REVIEW9-S5PBT04")
        self.assertEqual(matrix["current_phase"], "S5PB")
        self.assertEqual(matrix["current_gate"], "S5PB-GATE-IN-PROGRESS")

    def test_review9_s5pbt04_pfi_roadmap_tracks_single_project_task(self) -> None:
        validator = load_validator_module()
        pfi_root = ROOT / "PFI" / "大数据模拟器"
        roadmap = validator.load_yaml(pfi_root / "docs" / "governance" / "roadmap.yaml")
        self.assertEqual(roadmap["schema_version"], "codexproject.roadmap.v1")
        self.assertEqual(roadmap["project_id"], "PFI_BIG_DATA_SIMULATOR")
        self.assertEqual(roadmap["current_stage_id"], "S5")
        self.assertEqual(roadmap["current_phase_id"], "S5PB")
        self.assertEqual(roadmap["current_task_id"], "S5PBT04")
        self.assertEqual(roadmap["next_gate_id"], "S5PB-GATE-IN-PROGRESS")
        self.assertEqual(roadmap["total_estimated_hours"], 4)
        self.assertEqual(roadmap["completed_estimated_hours"], 4)

        tasks = [
            task
            for stage in roadmap["stages"]
            for phase in stage["phases"]
            for task in phase["tasks"]
        ]
        self.assertEqual([task["task_id"] for task in tasks], ["S5PBT04"])
        task = tasks[0]
        self.assertEqual(task["status"], "completed")
        self.assertEqual(task["dependencies"], ["S5PBT03"])
        self.assertEqual(task["acceptance_ids"], ["ACC-S5PBT04"])
        self.assertIn("PFI/大数据模拟器/docs/governance/project.yaml", task["evidence_refs"])
        self.assertIn("任何项目缺少 owner-readable 三文件", roadmap["stages"][0]["phases"][0]["stop_conditions"])
        self.assertIn("未知事实被写成 VERIFIED", roadmap["stages"][0]["phases"][0]["stop_conditions"])

    def test_review9_s5pbt04_pfi_events_preserve_truth_levels(self) -> None:
        events = [
            json.loads(line)
            for line in (ROOT / "PFI" / "大数据模拟器" / "docs" / "governance" / "events.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
            if line.strip()
        ]
        self.assertEqual(len(events), 4)
        self.assertEqual({event["schema_version"] for event in events}, {"codexproject.event.v1"})
        self.assertTrue({event["fact_level"] for event in events}.issubset({"VERIFIED", "EXTRACTED", "RECONSTRUCTED", "PROPOSED", "UNKNOWN"}))
        by_id = {event["event_id"]: event for event in events}
        self.assertEqual(by_id["EVT-PFI-SEMANTIC-20260621-001"]["fact_level"], "RECONSTRUCTED")
        self.assertIn("not strategy validity", by_id["EVT-PFI-SEMANTIC-20260621-001"]["notes"])
        self.assertEqual(by_id["EVT-PFI-REVIEW6-FINAL-20260622-001"]["fact_level"], "EXTRACTED")
        self.assertIn("UNVERIFIED", by_id["EVT-PFI-REVIEW6-FINAL-20260622-001"]["summary"])
        self.assertEqual(by_id["EVT-PFI-OWNER-DECISION-20260622-001"]["fact_level"], "UNKNOWN")
        self.assertIn("OOS", by_id["EVT-PFI-OWNER-DECISION-20260622-001"]["summary"])
        self.assertEqual(by_id["EVT-PFI-REVIEW9-S5PBT04-LOCAL"]["fact_level"], "PROPOSED")
        self.assertFalse(any(event["runtime_behavior_changed"] for event in events))

    def test_review9_s5pbt04_pfi_human_files_render_without_drift(self) -> None:
        cli = load_lean_governance_module()
        pfi_root = ROOT / "PFI" / "大数据模拟器"
        result = cli.check_render_project_files(pfi_root)
        self.assertEqual(result["drift_count"], 0, result["drift"])
        self.assertEqual(result["reference_issue_count"], 0, result["reference_issues"])

        feature_text = (pfi_root / "功能清单").read_text(encoding="utf-8")
        dev_text = (pfi_root / "开发记录").read_text(encoding="utf-8")
        model_text = (pfi_root / "模型参数文件").read_text(encoding="utf-8")
        self.assertIn("# 功能清单", feature_text)
        self.assertIn("FEAT-PFI-006", feature_text)
        self.assertIn("provider/OOS", feature_text)
        self.assertIn("Stage -> Phase -> Task", dev_text)
        self.assertIn("S5PBT04", dev_text)
        self.assertIn("MOD-015", model_text)
        self.assertIn("PARAM-213", model_text)
        self.assertIn("PARAM-110", model_text)
        for text in (feature_text, dev_text, model_text):
            self.assertNotIn("docs/governance/", text.splitlines()[0])

    def test_review9_s5pbt04_files_are_project_governance_only(self) -> None:
        sync = load_sync_module()
        project = {
            "project_id": "PFI_BIG_DATA_SIMULATOR",
            "path": "PFI/大数据模拟器",
            "model_behavior_globs": ["qbvs/**/*", "scripts/**/*", "data/**/*", "config/**/*", "*.py"],
        }
        changes, _ = sync.classify_changes(
            {"projects": [project]},
            [
                "PFI/大数据模拟器/docs/governance/project.yaml",
                "PFI/大数据模拟器/docs/governance/roadmap.yaml",
                "PFI/大数据模拟器/docs/governance/events.jsonl",
                "PFI/大数据模拟器/docs/governance/VERSION_MATRIX.yaml",
                "PFI/大数据模拟器/功能清单",
                "PFI/大数据模拟器/开发记录",
                "PFI/大数据模拟器/模型参数文件",
            ],
        )
        self.assertEqual(len(changes), 1)
        self.assertEqual(changes[0].classifications, {"governance_only_change", "trivial_change"})
        self.assertEqual(
            changes[0].updated_governance_files,
            {
                "docs/governance/project.yaml",
                "docs/governance/roadmap.yaml",
                "docs/governance/events.jsonl",
                "docs/governance/VERSION_MATRIX.yaml",
            },
        )
        validation = sync.SyncValidation()
        sync.validate_diff_contract(validation, changes)
        self.assertFalse(validation.errors)

    def test_review9_s5pbt04_manifest_records_pfi_only_scope(self) -> None:
        manifest = json.loads(
            (
                ROOT
                / "governance"
                / "run_manifests"
                / "GOV-REVIEW9-S5PBT04-PFI-BIG-DATA-SIMULATOR-CANONICAL-RENDER-20260624.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(manifest["project_id"], "PFI_BIG_DATA_SIMULATOR")
        self.assertEqual(manifest["task_id"], "S5PBT04")
        self.assertEqual(manifest["acceptance_ids"], ["ACC-S5PBT04"])
        self.assertEqual(manifest["binding_status"], "PRECOMMIT_TREE_BOUND")
        self.assertIn("review9_stage5_single_project_migration", manifest["change_classification"])
        self.assertIn("pfi_big_data_simulator_only_scope", manifest["change_classification"])
        changed = set(manifest["changed_files_actual"])
        for path in {
            "PFI/大数据模拟器/docs/governance/project.yaml",
            "PFI/大数据模拟器/docs/governance/roadmap.yaml",
            "PFI/大数据模拟器/docs/governance/events.jsonl",
            "PFI/大数据模拟器/docs/governance/VERSION_MATRIX.yaml",
            "PFI/大数据模拟器/功能清单",
            "PFI/大数据模拟器/开发记录",
            "PFI/大数据模拟器/模型参数文件",
            "tests/governance/test_project_governance_validator.py",
            "governance/run_manifests/GOV-REVIEW9-S5PBT04-PFI-BIG-DATA-SIMULATOR-CANONICAL-RENDER-20260624.json",
        }:
            self.assertIn(path, changed)
        self.assertFalse(any(path.startswith(("FIFA/", "OpenAIDatabase/", "arxiv-daily-push/")) for path in changed))
        self.assertIn("S5PB-GATE remains in_progress", " ".join(manifest["unresolved_risks"]))
        self.assertIn("PFI delivery readiness remains UNVERIFIED", " ".join(manifest["unresolved_risks"]))

    def test_review9_s5pbt05_arxiv_project_yaml_preserves_stage_truth(self) -> None:
        validator = load_validator_module()
        arxiv_root = ROOT / "arxiv-daily-push"
        project = validator.load_yaml(arxiv_root / "docs" / "governance" / "project.yaml")
        self.assertEqual(project["schema_version"], "codexproject.project.v1")
        self.assertEqual(project["project_id"], "arxiv-daily-push")
        self.assertEqual(project["fact_level"], "EXTRACTED")
        self.assertEqual(project["current_status"], "stage1_accepted_s2pct01_shadow_merged_s2pct02_next_no_formal_production")
        self.assertIn("Stage 1 B1/arXiv accepted", project["summary"])
        self.assertIn("S2PBT01/S2P1T01 bioRxiv/medRxiv", project["summary"])
        self.assertIn("S2PCT01 / legacy S2P2T01 Nature/top-journal", project["summary"])
        self.assertIn("不得宣称 Stage 2 或 integrated production accepted", project["summary"])
        self.assertEqual(len(project["features"]), 9)
        self.assertEqual(len(project["models"]), 52)
        self.assertEqual(len(project["formulas"]), 54)
        self.assertEqual(len(project["parameters"]), 364)
        self.assertEqual(len(project["strategies"]), 3)
        self.assertEqual(len(project["validations"]), 4)

        source_models = validator.load_yaml(arxiv_root / "docs" / "governance" / "model_registry.yaml")["models"]
        source_formulas = validator.load_yaml(arxiv_root / "docs" / "governance" / "formula_registry.yaml")["formulas"]
        with (arxiv_root / "docs" / "governance" / "parameter_registry.csv").open(encoding="utf-8", newline="") as handle:
            source_parameters = list(csv.DictReader(handle))
        self.assertEqual(
            {item["model_id"] for item in source_models if item.get("status") == "active"},
            {item["model_id"] for item in project["models"]},
        )
        self.assertEqual(
            {item["formula_id"] for item in source_formulas if item.get("status") == "active"},
            {item["formula_id"] for item in project["formulas"]},
        )
        self.assertEqual(
            {item["parameter_id"] for item in source_parameters if item.get("status") == "active"},
            {item["parameter_id"] for item in project["parameters"]},
        )

        evidence_ids = {item["evidence_id"] for item in project["evidence_refs"]}
        self.assertIn("EVID-REVIEW9-S5PBT05-MANIFEST", evidence_ids)
        self.assertIn("EVID-ADP-STAGE1-ACCEPTED", evidence_ids)
        self.assertIn("EVID-ADP-LOCAL-PRODUCTION-PREP", evidence_ids)
        self.assertIn("EVID-ADP-S2PBT01-REAL-REPLAY-SHADOW", evidence_ids)
        self.assertIn("EVID-ADP-S2PCT01-NATURE", evidence_ids)
        for section in ("features", "models", "formulas", "parameters", "strategies", "validations"):
            for item in project[section]:
                for evidence_id in item["evidence_refs"]:
                    self.assertIn(evidence_id, evidence_ids)

        parameter_semantic_counts = Counter(item["semantic_status"] for item in project["parameters"])
        formula_semantic_counts = Counter(item["semantic_status"] for item in project["formulas"])
        model_semantic_counts = Counter(item["semantic_status"] for item in project["models"])
        self.assertEqual(parameter_semantic_counts["MACHINE_VERIFIED"], 364)
        self.assertEqual(formula_semantic_counts["MACHINE_VERIFIED"], 54)
        self.assertEqual(model_semantic_counts["EXTRACTED"], 52)

        limitations = " ".join(item["statement"] for item in project["limitations"])
        self.assertIn("364/364 active parameters", limitations)
        self.assertIn("54/54 active formulas", limitations)
        self.assertIn("52 个 active models 只从 model_registry EXTRACTED", limitations)
        self.assertIn("delivery_readiness 对 Stage 1 arXiv 为 VERIFIED", limitations)
        self.assertIn("evidence_freshness 仍为 PARTIAL", limitations)
        self.assertIn("S2PCT01 / legacy S2P2T01 Nature/top-journal", limitations)
        self.assertEqual(project["delivery_readiness"]["status"], "VERIFIED")
        self.assertEqual(project["delivery_readiness"]["release_gate"], "ARXIV_PRODUCTION_ACCEPTED")
        self.assertTrue(project["delivery_readiness"]["owner_decision_required"])
        self.assertEqual(project["delivery_readiness"]["blocked_requirements"], 0)
        self.assertEqual(project["delivery_readiness"]["active_requirements"], 9)
        self.assertEqual(project["delivery_readiness"]["partial_requirements"], 1)
        self.assertEqual(project["delivery_readiness"]["next_executable_task_id"], "S2PCT02")
        self.assertEqual(project["delivery_readiness"]["next_executable_task_status"], "planned")

        matrix = validator.load_yaml(arxiv_root / "docs" / "governance" / "VERSION_MATRIX.yaml")
        self.assertEqual(matrix["current_iteration"], "ITER-20260624-ADP-S2PCT01-POST-MERGE-STATUS")
        self.assertEqual(matrix["current_phase"], "S2PC")
        self.assertEqual(matrix["current_gate"], "ARXIV_PRODUCTION_ACCEPTED_MAINTAINED_AND_V7_1_PRODUCT_CONTRACT_AND_AUDIT_LOCKED")
        self.assertEqual(matrix["current_v7_task_id"], "S2PCT01")
        self.assertEqual(matrix["current_v6_task_id"], "S2P2T01")
        self.assertIn("S2PCT01 -> S2P2T01", matrix["current_v7_legacy_alias"])
        self.assertEqual(matrix["current_v7_shadow_source_task_id"], "S2PBT01")
        self.assertEqual(matrix["current_v7_final_task_id"], "S2PMT07")
        self.assertEqual(matrix["review9_migration_iteration"], "ITER-20260624-REVIEW9-S5PBT05")
        self.assertEqual(matrix["review9_migration_phase"], "S5PB")
        self.assertEqual(matrix["review9_migration_gate"], "S5PB-GATE-IN-PROGRESS")

    def test_review9_s5pbt05_arxiv_roadmap_tracks_single_project_task(self) -> None:
        validator = load_validator_module()
        roadmap = validator.load_yaml(ROOT / "arxiv-daily-push" / "docs" / "governance" / "roadmap.yaml")
        self.assertEqual(roadmap["schema_version"], "codexproject.roadmap.v1")
        self.assertEqual(roadmap["project_id"], "arxiv-daily-push")
        self.assertEqual(roadmap["current_stage_id"], "S2")
        self.assertEqual(roadmap["current_phase_id"], "S2PC")
        self.assertEqual(roadmap["current_task_id"], "S2PCT02")
        self.assertEqual(roadmap["next_gate_id"], "S2PC-GATE-V7-CONTRACT-BLOCKED")
        self.assertEqual(roadmap["total_estimated_hours"], 10.5)
        self.assertEqual(roadmap["completed_estimated_hours"], 8.5)

        tasks = [
            task
            for stage in roadmap["stages"]
            for phase in stage["phases"]
            for task in phase["tasks"]
        ]
        self.assertEqual([task["task_id"] for task in tasks], ["S2PBT01", "S2PCT01", "S2PCT02", "S5PBT05"])
        task = tasks[0]
        self.assertEqual(task["status"], "completed")
        self.assertEqual(task["dependencies"], ["ARXIV_PRODUCTION_ACCEPTED", "ADP-S1P5T05"])
        self.assertEqual(task["acceptance_ids"], ["ADP-ACC-S2P1T01-SOURCE-PROMOTION"])
        self.assertIn("governance/run_manifests/ADP-S2PBT01-REAL-REPLAY-SHADOW-EVIDENCE-20260624.json", task["evidence_refs"])
        nature_task = tasks[1]
        self.assertEqual(nature_task["task_id"], "S2PCT01")
        self.assertEqual(nature_task["legacy_alias"], "S2P2T01")
        self.assertEqual(nature_task["status"], "completed")
        self.assertEqual(nature_task["acceptance_ids"], ["ACC-S2PCT01-NATURE"])
        self.assertIn(
            "governance/run_manifests/ADP-S2P2T01-TOP-JOURNAL-SHADOW-FOUNDATION-20260624.json",
            nature_task["evidence_refs"],
        )
        science_task = tasks[2]
        self.assertEqual(science_task["task_id"], "S2PCT02")
        self.assertEqual(science_task["legacy_alias"], "S2P2T02")
        self.assertEqual(science_task["status"], "planned")
        self.assertEqual(science_task["acceptance_ids"], ["ACC-S2PCT02-SCIENCE"])
        self.assertIn("V7/root contract gate 未通过时宣称 STAGE2_PRODUCTION_ACCEPTED", roadmap["stages"][0]["stop_conditions"])

    def test_review9_s5pbt05_arxiv_events_preserve_truth_levels(self) -> None:
        events = [
            json.loads(line)
            for line in (ROOT / "arxiv-daily-push" / "docs" / "governance" / "events.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
            if line.strip()
        ]
        self.assertEqual(len(events), 7)
        self.assertEqual({event["schema_version"] for event in events}, {"codexproject.event.v1"})
        self.assertTrue({event["fact_level"] for event in events}.issubset({"VERIFIED", "EXTRACTED", "RECONSTRUCTED", "PROPOSED", "UNKNOWN"}))
        by_id = {event["event_id"]: event for event in events}
        self.assertEqual(by_id["EVT-ADP-STAGE1-ACCEPTED-20260623-001"]["fact_level"], "EXTRACTED")
        self.assertIn("does not imply Stage 2 sources are implemented", by_id["EVT-ADP-STAGE1-ACCEPTED-20260623-001"]["notes"])
        self.assertEqual(by_id["EVT-ADP-TEST10-20260624-001"]["fact_level"], "EXTRACTED")
        self.assertIn("does not mean unattended local production mail is installed", by_id["EVT-ADP-TEST10-20260624-001"]["notes"])
        self.assertEqual(by_id["EVT-ADP-S2P1T01-READY-20260624-001"]["fact_level"], "EXTRACTED")
        self.assertIn("Ready is not implemented", by_id["EVT-ADP-S2P1T01-READY-20260624-001"]["notes"])
        self.assertEqual(by_id["EVT-ADP-S2PBT01-REAL-REPLAY-SHADOW-20260624-001"]["fact_level"], "EXTRACTED")
        self.assertIn("formal production inclusion", by_id["EVT-ADP-S2PBT01-REAL-REPLAY-SHADOW-20260624-001"]["notes"])
        self.assertEqual(by_id["EVT-ADP-REVIEW9-S5PBT05-LOCAL"]["fact_level"], "PROPOSED")
        self.assertFalse(any(event["runtime_behavior_changed"] for event in events))

    def test_review9_s5pbt05_arxiv_human_files_render_without_drift(self) -> None:
        cli = load_lean_governance_module()
        arxiv_root = ROOT / "arxiv-daily-push"
        result = cli.check_render_project_files(arxiv_root)
        self.assertEqual(result["drift_count"], 0, result["drift"])
        self.assertEqual(result["reference_issue_count"], 0, result["reference_issues"])

        feature_text = (arxiv_root / "功能清单").read_text(encoding="utf-8")
        dev_text = (arxiv_root / "开发记录").read_text(encoding="utf-8")
        model_text = (arxiv_root / "模型参数文件").read_text(encoding="utf-8")
        self.assertIn("# 功能清单", feature_text)
        self.assertIn("FEAT-ADP-008", feature_text)
        self.assertIn("bioRxiv/medRxiv", feature_text)
        self.assertIn("Stage -> Phase -> Task", dev_text)
        self.assertIn("S5PBT05", dev_text)
        self.assertIn("ARXIV_PRODUCTION_ACCEPTED", dev_text)
        self.assertIn("S2P1T01", dev_text)
        self.assertIn("MOD-ADP-046", model_text)
        self.assertIn("FORM-ADP-048", model_text)
        self.assertIn("PARAM-ADP-359", model_text)
        for text in (feature_text, dev_text, model_text):
            self.assertNotIn("docs/governance/", text.splitlines()[0])

    def test_review9_s5pbt05_files_are_project_governance_only(self) -> None:
        sync = load_sync_module()
        project = {
            "project_id": "arxiv-daily-push",
            "path": "arxiv-daily-push",
            "model_behavior_globs": ["src/**/*", "config/**/*", "schemas/**/*", "tests/**/*", ".github/workflows/arxiv-daily-push-*"],
        }
        changes, _ = sync.classify_changes(
            {"projects": [project]},
            [
                "arxiv-daily-push/docs/governance/project.yaml",
                "arxiv-daily-push/docs/governance/roadmap.yaml",
                "arxiv-daily-push/docs/governance/events.jsonl",
                "arxiv-daily-push/docs/governance/VERSION_MATRIX.yaml",
                "arxiv-daily-push/功能清单",
                "arxiv-daily-push/开发记录",
                "arxiv-daily-push/模型参数文件",
            ],
        )
        self.assertEqual(len(changes), 1)
        self.assertEqual(changes[0].classifications, {"governance_only_change", "trivial_change"})
        self.assertEqual(
            changes[0].updated_governance_files,
            {
                "docs/governance/project.yaml",
                "docs/governance/roadmap.yaml",
                "docs/governance/events.jsonl",
                "docs/governance/VERSION_MATRIX.yaml",
            },
        )
        validation = sync.SyncValidation()
        sync.validate_diff_contract(validation, changes)
        self.assertFalse(validation.errors)

    def test_review9_s5pbt05_manifest_records_arxiv_only_scope(self) -> None:
        manifest = json.loads(
            (
                ROOT
                / "governance"
                / "run_manifests"
                / "GOV-REVIEW9-S5PBT05-ARXIV-DAILY-PUSH-CANONICAL-RENDER-20260624.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(manifest["project_id"], "arxiv-daily-push")
        self.assertEqual(manifest["task_id"], "S5PBT05")
        self.assertEqual(manifest["acceptance_ids"], ["ACC-S5PBT05"])
        self.assertEqual(manifest["binding_status"], "PRECOMMIT_TREE_BOUND")
        self.assertIn("review9_stage5_single_project_migration", manifest["change_classification"])
        self.assertIn("arxiv_daily_push_only_scope", manifest["change_classification"])
        self.assertIn("arxiv_external_ci_scope_guard", manifest["change_classification"])
        changed = set(manifest["changed_files_actual"])
        for path in {
            ".github/workflows/arxiv-daily-push-stage1-bootstrap.yml",
            ".github/workflows/arxiv-daily-push-phase12-cloud-dry-run.yml",
            ".github/workflows/arxiv-daily-push-real-backfill.yml",
            "arxiv-daily-push/docs/governance/project.yaml",
            "arxiv-daily-push/docs/governance/roadmap.yaml",
            "arxiv-daily-push/docs/governance/events.jsonl",
            "arxiv-daily-push/docs/governance/VERSION_MATRIX.yaml",
            "arxiv-daily-push/功能清单",
            "arxiv-daily-push/开发记录",
            "arxiv-daily-push/模型参数文件",
            "tests/governance/test_project_governance_validator.py",
            "governance/run_manifests/GOV-REVIEW9-S5PBT05-ARXIV-DAILY-PUSH-CANONICAL-RENDER-20260624.json",
        }:
            self.assertIn(path, changed)
        self.assertFalse(any(path.startswith(("FIFA/", "OpenAIDatabase/", "PFI/")) for path in changed))
        self.assertIn("S5PB-GATE remains in_progress", " ".join(manifest["unresolved_risks"]))
        self.assertIn("evidence_freshness remains PARTIAL", " ".join(manifest["unresolved_risks"]))
        self.assertIn("S2P1T01 is ready but not implemented", " ".join(manifest["unresolved_risks"]))

    def test_review9_s5_gate_all_projects_have_lean_v2_owner_entries(self) -> None:
        validator = load_validator_module()
        cli = load_lean_governance_module()
        config = validator.load_yaml(ROOT / "governance" / "projects.yaml")
        projects = [project for project in validator.as_list(config.get("projects")) if isinstance(project, dict)]

        self.assertEqual(len(projects), 10)
        for project in projects:
            project_id = project["project_id"]
            project_root = ROOT / project["path"]
            governance_root = project_root / "docs" / "governance"
            for relative in ("project.yaml", "roadmap.yaml", "events.jsonl"):
                self.assertTrue((governance_root / relative).is_file(), f"{project_id}: missing {relative}")

            result = cli.check_render_project_files(project_root)
            self.assertEqual(result["drift_count"], 0, f"{project_id}: {result['drift']}")
            self.assertEqual(result["reference_issue_count"], 0, f"{project_id}: {result['reference_issues']}")

            for filename in ("功能清单", "开发记录", "模型参数文件"):
                text = (project_root / filename).read_text(encoding="utf-8")
                self.assertTrue(text.startswith("# "), f"{project_id}: {filename} is not a readable document")
                self.assertNotIn("docs/governance/", text.splitlines()[0], f"{project_id}: {filename} is an index page")
                self.assertGreater(len(text), 800, f"{project_id}: {filename} is too thin for owner review")

            roadmap = validator.load_yaml(governance_root / "roadmap.yaml")
            self.assertTrue(roadmap["stages"], f"{project_id}: roadmap has no stages")
            self.assertIn("Stage -> Phase -> Task", (project_root / "开发记录").read_text(encoding="utf-8"))

    def test_review9_s5_gate_manifest_closes_stage5_without_promoting_required(self) -> None:
        manifest_path = ROOT / "governance" / "run_manifests" / "GOV-REVIEW9-S5-GATE-CLOSED-20260624.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

        self.assertEqual(manifest["project_id"], "CodexProject")
        self.assertEqual(manifest["task_id"], "S5-GATE")
        self.assertEqual(manifest["acceptance_ids"], ["ACC-S5-GATE", "ACC-S5PB-GATE"])
        self.assertEqual(manifest["binding_status"], "PRECOMMIT_TREE_BOUND")
        self.assertEqual(manifest["stage_gate_status"]["S5PB-GATE"], "PASSED")
        self.assertEqual(manifest["stage_gate_status"]["S5-GATE"], "PASSED")
        self.assertEqual(manifest["next_allowed_stage"], "S6")
        self.assertEqual(manifest["project_acceptance_totals"], {"accepted_projects": 10, "registered_projects": 10})

        expected_projects = {
            "Alpha": ("S5PAT01", 103),
            "EVA_OS": ("S5PAT02", 104),
            "OpMe_System": ("S5PAT03", 106),
            "whkmSalary": ("S5PAT04", 108),
            "EEI": ("S5PBT01", 109),
            "FIFA": ("S5PBT02", 111),
            "OpenAIDatabase": ("S5PBT03", 112),
            "PFI_BIG_DATA_SIMULATOR": ("S5PBT04", 113),
            "Serenity-Alipay": ("S4PC", 101),
            "arxiv-daily-push": ("S5PBT05", 115),
        }
        matrix = {row["project_id"]: row for row in manifest["project_acceptance_matrix"]}
        self.assertEqual(set(matrix), set(expected_projects))
        for project_id, (task_id, pr_number) in expected_projects.items():
            row = matrix[project_id]
            self.assertEqual(row["task_id"], task_id)
            self.assertEqual(row["owner_account"], "LinzeColin")
            self.assertEqual(row["owner_signoff_pr"], pr_number)
            self.assertTrue(row["lean_v2_canonical_files"])
            self.assertTrue(row["owner_readable_entries"])
            self.assertEqual(row["render_drift_count"], 0)

        for path in manifest["s5_task_manifests"]:
            self.assertTrue((ROOT / path).is_file(), path)
        self.assertTrue(manifest["daily_compute_contract"]["changed_only_ci"])
        self.assertTrue(manifest["daily_compute_contract"]["full_semantic_sweeps_manual_only"])
        self.assertFalse(manifest["stage6_actions_performed"]["ci_mode_required_enabled"])
        self.assertFalse(manifest["stage6_actions_performed"]["legacy_files_archived_or_deleted"])
        self.assertIn("Stage 6 may start", manifest["summary"])

    def test_review9_s6pat01_archive_manifest_records_legacy_checksums(self) -> None:
        archive_path = ROOT / "governance" / "archive" / "review9_s6pat01_legacy_archive_manifest.csv"
        manifest = json.loads(
            (
                ROOT
                / "governance"
                / "run_manifests"
                / "GOV-REVIEW9-S6PAT01-LEGACY-ARCHIVE-MANIFEST-20260624.json"
            ).read_text(encoding="utf-8")
        )
        snapshot_ref = manifest["implementation_base_sha"]
        with archive_path.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))

        self.assertEqual(len(rows), 160)
        counts = Counter(row["category"] for row in rows)
        self.assertEqual(counts["project_v1_governance_file"], 150)
        self.assertEqual(counts["root_legacy_governance_script"], 7)
        self.assertEqual(counts["root_generated_or_status_view"], 3)
        self.assertGreater(sum(int(row["active_reference_count"]) for row in rows), 0)

        later_changed = set()
        s6pat02_manifest = ROOT / "governance" / "run_manifests" / "GOV-REVIEW9-S6PAT02-GENERATED-VIEWS-ARTIFACT-20260624.json"
        if s6pat02_manifest.exists():
            later_changed.update(json.loads(s6pat02_manifest.read_text(encoding="utf-8"))["changed_files_actual"])

        for row in rows:
            source = ROOT / row["source_path"]
            if not source.exists():
                self.assertEqual(row["category"], "root_generated_or_status_view", row["source_path"])
                self.assertIn("s6pat02_generated_view_removal", row["archive_action"])
                continue
            if row["source_path"] in later_changed:
                self.assertIn(row["category"], {"root_legacy_governance_script", "root_generated_or_status_view", "project_v1_governance_file"})
                continue
            self.assertTrue(source.is_file(), row["source_path"])
            blob = subprocess.run(
                ["git", "show", f"{snapshot_ref}:{row['source_path']}"],
                cwd=ROOT,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
            ).stdout
            observed = hashlib.sha256(blob).hexdigest()
            self.assertEqual(len(blob), int(row["size_bytes"]), row["source_path"])
            self.assertEqual(observed, row["sha256"], row["source_path"])
            self.assertIn("retain_in_place", row["archive_action"])
            self.assertIn("OWNER_APPROVAL", row["retention_until"])

    def test_review9_s6pat01_manifest_blocks_moves_while_references_are_active(self) -> None:
        manifest = json.loads(
            (
                ROOT
                / "governance"
                / "run_manifests"
                / "GOV-REVIEW9-S6PAT01-LEGACY-ARCHIVE-MANIFEST-20260624.json"
            ).read_text(encoding="utf-8")
        )

        self.assertEqual(manifest["project_id"], "CodexProject")
        self.assertEqual(manifest["task_id"], "S6PAT01")
        self.assertEqual(manifest["acceptance_ids"], ["ACC-S6PAT01"])
        self.assertEqual(manifest["stage_gate_status"]["S6PA-GATE"], "IN_PROGRESS")
        self.assertEqual(manifest["legacy_archive_summary"]["candidate_files"], 160)
        self.assertEqual(manifest["legacy_archive_summary"]["project_v1_governance_files"], 150)
        self.assertEqual(manifest["legacy_archive_summary"]["root_legacy_governance_scripts"], 7)
        self.assertEqual(manifest["legacy_archive_summary"]["root_generated_or_status_views"], 3)
        self.assertEqual(manifest["legacy_archive_summary"]["archive_manifest_sha256"], "96b6b25ab8a584b0bfb09c01a2b5bf943dece9a654f992147cbc4ae8c89210a5")
        self.assertEqual(manifest["reference_scan"]["status"], "ACTIVE_REFERENCES_FOUND")
        self.assertGreater(manifest["reference_scan"]["active_reference_rows"], 0)
        self.assertFalse(manifest["stage6_actions_performed"]["legacy_files_moved"])
        self.assertFalse(manifest["stage6_actions_performed"]["legacy_files_deleted"])
        self.assertFalse(manifest["stage6_actions_performed"]["ci_mode_required_enabled"])
        self.assertIn("S6PAT02", manifest["next_required_tasks"])
        self.assertIn("S6PAT03", manifest["next_required_tasks"])

    def test_review9_s6pat02_root_generated_views_are_artifact_only(self) -> None:
        for rel_path in (
            "GOVERNANCE_DASHBOARD.md",
            "OWNER_PORTFOLIO.md",
            "governance/binding_backlog.yaml",
        ):
            self.assertFalse((ROOT / rel_path).exists(), rel_path)

        projects = load_validator_module().load_yaml(ROOT / "governance" / "projects.yaml")
        required = set(projects["root_governance"]["required_files"])
        self.assertFalse(
            required
            & {
                "GOVERNANCE_DASHBOARD.md",
                "OWNER_PORTFOLIO.md",
                "governance/binding_backlog.yaml",
            }
        )

        workflow = (ROOT / ".github" / "workflows" / "project-governance.yml").read_text(encoding="utf-8")
        self.assertIn("--root-artifact-dir", workflow)
        self.assertIn("governance-generated-views", workflow)
        self.assertNotIn("GOVERNANCE_DASHBOARD.md OWNER_PORTFOLIO.md governance/binding_backlog.yaml", workflow)

    def test_review9_s6pat02_generator_exposes_root_artifact_mode(self) -> None:
        dashboard = load_dashboard_module()
        self.assertIn("GOVERNANCE_DASHBOARD.md", dashboard.ROOT_OUTPUT_REL_PATHS)
        self.assertIn("root_artifact_dir", dashboard.generate.__code__.co_varnames)

    def test_review9_s2_projects_registry_is_identity_only(self) -> None:
        validator = load_validator_module()
        config = validator.load_yaml(ROOT / "governance" / "projects.yaml")
        projects = [project for project in validator.as_list(config.get("projects")) if isinstance(project, dict)]
        self.assertEqual(len(projects), 10)
        for project in projects:
            self.assertEqual(set(project), {"project_id", "path", "ci_mode", "migration"})
            self.assertEqual(project["ci_mode"], "required")
            self.assertEqual(project["migration"], {"version": "lean-v2"})

    def test_review9_s6pbt01_all_migrated_projects_are_required(self) -> None:
        validator = load_validator_module()
        config = validator.load_yaml(ROOT / "governance" / "projects.yaml")
        projects = [project for project in validator.as_list(config.get("projects")) if isinstance(project, dict)]
        self.assertEqual(len(projects), 10)

        manifest_path = ROOT / "governance" / "run_manifests" / "GOV-REVIEW9-S6PBT01-REQUIRED-CI-MODE-20260624.json"
        self.assertTrue(manifest_path.is_file(), manifest_path)
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        matrix = {row["project_id"]: row for row in manifest["required_matrix"]}
        self.assertEqual(set(matrix), {project["project_id"] for project in projects})

        for project in projects:
            project_id = project["project_id"]
            project_root = ROOT / project["path"]
            self.assertEqual(project["ci_mode"], "required", project_id)
            self.assertEqual(project["migration"], {"version": "lean-v2"}, project_id)
            self.assertTrue((project_root / "docs" / "governance" / "project.yaml").is_file(), project_id)
            self.assertTrue((project_root / "docs" / "governance" / "roadmap.yaml").is_file(), project_id)
            self.assertTrue((project_root / "docs" / "governance" / "events.jsonl").is_file(), project_id)
            for human_file in ("功能清单", "开发记录", "模型参数文件"):
                self.assertTrue((project_root / human_file).is_file(), f"{project_id}:{human_file}")
            self.assertEqual(matrix[project_id]["ci_mode_after"], "required")
            self.assertEqual(matrix[project_id]["migration_version_after"], "lean-v2")
            self.assertEqual(matrix[project_id]["rollback"], "set this project ci_mode to advisory")

    def test_review9_s6pbt02_branch_protection_truth_packet_is_unverified(self) -> None:
        manifest_path = (
            ROOT
            / "governance"
            / "run_manifests"
            / "GOV-REVIEW9-S6PBT02-BRANCH-PROTECTION-UNVERIFIED-20260624.json"
        )
        self.assertTrue(manifest_path.is_file(), manifest_path)
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

        self.assertEqual(manifest["task_id"], "S6PBT02")
        self.assertEqual(manifest["stage_gate_status"]["S6PBT02"], "UNVERIFIED_EXTERNAL_OWNER_ACTION_REQUIRED")
        self.assertEqual(manifest["stage_gate_status"]["S6PB-GATE"], "IN_PROGRESS")
        self.assertEqual(manifest["stage_gate_status"]["S6-GATE"], "IN_PROGRESS")
        self.assertNotIn("PASSED", set(manifest["stage_gate_status"].values()))

        contract = manifest["required_check_contract"]
        self.assertEqual(contract["branch"], "main")
        self.assertEqual(contract["required_status_checks"], ["Project Governance / governance"])
        self.assertEqual(contract["required_status_check_count"], 1)
        self.assertTrue(contract["require_pull_request_before_merging"])
        self.assertTrue(contract["require_status_checks_to_pass"])
        self.assertTrue(contract["no_bypass_required"])

        evidence = manifest["branch_protection_evidence"]
        self.assertEqual(evidence["status"], "UNVERIFIED")
        self.assertEqual(evidence["required_status_checks"], "UNVERIFIED")
        self.assertEqual(evidence["no_bypass"], "UNVERIFIED")
        self.assertIn("GITHUB_TOKEN", evidence["protection_error"])

        setup = (ROOT / "docs" / "governance" / "CODEX_SETUP.md").read_text(encoding="utf-8")
        self.assertIn("Review9 S6PBT02 Owner Checklist", setup)
        self.assertIn("Project Governance / governance", setup)
        self.assertIn("--check-github --strict-github --json", setup)
        self.assertNotIn("generate_governance_dashboard.py --write --all --root-artifact-dir", setup)

    def test_review9_s2_projects_registry_rejects_computed_fields(self) -> None:
        validator = load_validator_module()
        project = {
            "project_id": "P",
            "path": "P",
            "ci_mode": "advisory",
            "migration": {"version": "legacy-v1-pending-lean-v2"},
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
        validator.validate_project_registry_entry(validation, project, "P")
        self.assertTrue(any("non-registry fields" in issue.message for issue in validation.errors), validation.errors)

    def test_review9_s2_projects_registry_requires_migration_version(self) -> None:
        validator = load_validator_module()
        project = {
            "project_id": "P",
            "path": "P",
            "ci_mode": "advisory",
            "migration": {},
        }
        validation = validator.Validation()
        validator.validate_project_registry_entry(validation, project, "P")
        self.assertTrue(any("Invalid migration.version" in issue.message for issue in validation.errors), validation.errors)

    def test_unknown_project_returns_nonzero(self) -> None:
        result = run_validator("--project", "__missing_project__")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Unknown project: __missing_project__", result.stdout)

    def test_governance_stop_hook_continues_enabled_repo_without_validator(self) -> None:
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
        self.assertTrue(payload.get("continue"))
        self.assertEqual(payload.get("governance_hint", {}).get("mode"), "advisory")
        self.assertNotIn("decision", payload)

    def test_governance_stop_hook_allows_recursive_stop_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            subprocess.run(["git", "init"], cwd=tmp_path, stdout=subprocess.PIPE, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True)
            subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, check=True)
            (tmp_path / "governance").mkdir()
            (tmp_path / "governance" / "projects.yaml").write_text("governance_spec_version: '1.0.0'\n", encoding="utf-8")
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
        self.assertTrue(payload.get("continue"))
        self.assertEqual(payload.get("governance_hint", {}).get("mode"), "advisory")
        self.assertNotIn("decision", payload)

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

    def test_changed_only_root_governance_change_does_not_select_all_projects(self) -> None:
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

        self.assertEqual([project["project_id"] for project in selected], ["A"])

    def test_changed_only_root_governance_only_change_selects_no_projects(self) -> None:
        validator = load_validator_module()
        config = {
            "projects": [
                {"project_id": "A", "path": "A", "model_behavior_globs": []},
                {"project_id": "B", "path": "B", "model_behavior_globs": []},
            ]
        }
        args = SimpleNamespace(project=None, changed_only=True)

        with patch.object(validator, "git_changed_files", return_value=["scripts/validate_project_governance.py"]):
            selected = validator.select_projects(config, args)

        self.assertEqual(selected, [])

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
        changed = ["governance/projects.yaml", "README.md"]
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

    def test_review8_manifest_only_root_change_does_not_require_test_marker(self) -> None:
        sync = load_sync_module()
        changed = ["governance/run_manifests/GOV-REVIEW8-TEST.json"]
        validation = sync.SyncValidation()

        sync.root_sync_requirements(validation, changed, changed)

        self.assertFalse(validation.errors)

    def test_sync_changed_only_semantic_checks_only_changed_projects(self) -> None:
        sync = load_sync_module()
        project_a = {"project_id": "A", "path": "A"}
        project_b = {"project_id": "B", "path": "B"}
        checked: list[str] = []

        def fake_validate_semantic_project(validation, project):
            checked.append(project["project_id"])
            return {"current_iteration": "ITER-1"}

        with (
            patch.object(sync, "load_projects", return_value={"projects": [project_a, project_b]}),
            patch.object(sync, "explicit_base_ref", return_value=None),
            patch.object(sync, "merge_base", return_value="BASE"),
            patch.object(sync, "changed_files_against_base", return_value=["B/app/main.py"]),
            patch.object(
                sync,
                "classify_changes",
                return_value=(
                    [sync.ProjectChange(project=project_b, files=["B/app/main.py"])],
                    [],
                ),
            ),
            patch.object(sync, "validate_diff_contract"),
            patch.object(sync, "validate_append_only"),
            patch.object(sync, "validate_event_files_changed"),
            patch.object(sync, "root_sync_requirements"),
            patch.object(sync, "validate_semantic_project", side_effect=fake_validate_semantic_project),
            patch.object(sync, "validate_run_manifests"),
        ):
            exit_code, _ = sync.validate(changed_only=True, enforce_sync=True, semantic=True)

        self.assertEqual(exit_code, 0)
        self.assertEqual(checked, ["B"])

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

    def test_review9_sync_allows_stale_pending_binding_classification_only(self) -> None:
        sync = load_sync_module()
        old_event = {
            "event_id": "EVENT-OLD",
            "timestamp": "2026-06-22T00:00:00Z",
            "result": "LOCAL_PENDING_REMOTE_CI",
            "git_commit": "PENDING",
            "binding_status": "pre_commit_pending",
            "summary": "Local validation remains pending remote CI.",
        }
        classified_event = {
            **old_event,
            "binding_status": "stale_unbound",
            "stale_classification_reason": "Later governance event superseded this local pending record.",
        }
        self.assertTrue(
            sync.binding_classification_only(
                json.dumps(old_event) + "\n",
                json.dumps(classified_event) + "\n",
            )
        )

        mutated_event = {**classified_event, "summary": "Changed fact"}
        self.assertFalse(
            sync.binding_classification_only(
                json.dumps(old_event) + "\n",
                json.dumps(mutated_event) + "\n",
            )
        )

    def test_review9_sync_treats_eei_clean_room_tooling_as_governance_only(self) -> None:
        sync = load_sync_module()
        project = {
            "project_id": "EEI",
            "path": "EEI",
            "model_behavior_globs": ["apps/**/*", "scripts/**/*", "packages/**/*", "*.py"],
        }
        changes, _ = sync.classify_changes(
            {"projects": [project]},
            [
                "EEI/scripts/manage_clean_room_release.py",
                "EEI/scripts/manage_release_artifacts.py",
                "EEI/tests/unit/test_clean_room_release_paths.py",
                "EEI/docs/governance/development_events.jsonl",
            ],
        )

        self.assertEqual(len(changes), 1)
        self.assertEqual(changes[0].classifications, {"governance_only_change"})
        validation = sync.SyncValidation()
        sync.validate_diff_contract(validation, changes)
        self.assertFalse(validation.errors)

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
            "pull_request_skips_full_governance_tests",
            "main_push_changed_only_uses_event_before",
            "pull_request_skips_information_quality",
            "full_governance_runs_only_on_schedule_or_manual_all",
            "manual_changed_only_accepts_base_ref",
            "manual_project_scope_requires_project",
            "ci_attestation_validated",
            "ci_attestation_uploaded_as_artifact",
            "setup_doctor_runs_in_ci",
            "required_failures_not_masked",
        }:
            self.assertTrue(checks[check_name], check_name)

    def test_review9_stop_hook_is_advisory_and_non_writing(self) -> None:
        text = STOP_HOOK.read_text(encoding="utf-8")
        self.assertIn('"mode": "advisory"', text)
        self.assertIn('"continue": True', text)
        self.assertIn("suggested_commands", text)
        for forbidden in {
            "generate_governance_dashboard.py",
            "validate_information_quality.py",
            "governance_setup_doctor.py",
            "subprocess",
            "git_root",
            "changed_files",
            "status --porcelain",
            "write_receipt",
            "atomic_write_json",
            "decision\": \"block",
            "--all --semantic --drift-report",
        }:
            self.assertNotIn(forbidden, text)

    def test_review9_s3_stop_hook_is_pure_advisory_without_repository_scan(self) -> None:
        text = STOP_HOOK.read_text(encoding="utf-8")
        for forbidden in {"subprocess", "git_root", "changed_files", "status --porcelain", "Path("}:
            self.assertNotIn(forbidden, text)
        result = subprocess.run(
            [sys.executable, str(STOP_HOOK)],
            input=json.dumps({"cwd": str(ROOT), "stop_hook_active": True}),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertTrue(payload.get("continue"))
        hint = payload.get("governance_hint", {})
        self.assertEqual(hint.get("mode"), "advisory")
        self.assertIn("scripts/lean_governance.py ci --changed-only", " ".join(hint.get("suggested_commands", [])))
        self.assertNotIn("changed_files", hint)
        self.assertNotIn("governance_changed_files", hint)

    def test_review9_pr_governance_keeps_full_computation_out_of_pr_path(self) -> None:
        workflow = (ROOT / ".github" / "workflows" / "project-governance.yml").read_text(encoding="utf-8")
        self.assertIn("github.event_name == 'pull_request'", workflow)
        self.assertIn("github.event.pull_request.base.sha", workflow)
        self.assertIn("scripts/lean_governance.py ci --changed-only", workflow)
        self.assertNotIn("scripts/validate_project_governance.py --changed-only", workflow)
        self.assertIn("Run full governance validator tests", workflow)
        self.assertNotIn("github.event_name == 'pull_request' || github.event_name == 'schedule' || (github.event_name == 'workflow_dispatch' && inputs.scope != 'information-quality')", workflow)
        self.assertIn("scripts/lean_governance.py validate --all --semantic --drift-report", workflow)
        self.assertIn("scripts/lean_governance.py validate --project", workflow)
        self.assertIn("github.event_name == 'schedule' || (github.event_name == 'workflow_dispatch' && inputs.scope == 'all')", workflow)
        self.assertIn("github.event_name == 'workflow_dispatch' && inputs.scope == 'all'", workflow)
        self.assertNotIn("github.event_name == 'push' || (github.event_name == 'workflow_dispatch' && inputs.scope == 'all')", workflow)

    def test_other8_s2pct02_budget_guard_contract_passes(self) -> None:
        hook_text = STOP_HOOK.read_text(encoding="utf-8")
        self.assertIn("budget_policy", hook_text)
        self.assertIn("event_matrix", hook_text)
        self.assertNotIn("unittest discover", hook_text)
        self.assertNotIn("pytest tests/governance", hook_text)

        result = subprocess.run(
            [sys.executable, str(ROOT / "tools" / "budget_guard.py"), "--self-test"],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["status"], "PASS", report)

    def test_review9_s2_root_agents_declares_lean_v2_entry_contract(self) -> None:
        text = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        for required in {
            "功能清单",
            "开发记录",
            "模型参数文件",
            "compatibility indexes",
            "Stage -> Phase ->",
            "^S[1-9][0-9]*P[A-Z]T[0-9]{2}$",
            "Stop Conditions",
            "Stop Gates",
            "docs/governance/project.yaml",
            "docs/governance/roadmap.yaml",
            "docs/governance/events.jsonl",
            "Low-Token Contract",
            "中文优先",
            "默认全局中文",
            "whole repository",
            "registered project",
            "agent-facing responses",
            "PR descriptions",
            "CI-facing summaries",
            "owner-facing docs",
        }:
            self.assertIn(required, text)
        for mode in {"READ_ONLY", "REVIEW", "PLAN", "CI", "Hook", "IMPLEMENT"}:
            self.assertIn(mode, text)
        self.assertIn("must not modify", text)
        self.assertIn("Full semantic sweeps", text)

    def test_review9_s2_standard_is_lean_v2_contract(self) -> None:
        text = (ROOT / "docs" / "governance" / "STANDARD.md").read_text(encoding="utf-8")
        for required in {
            "Lean Project Governance Standard v2.0",
            "功能清单",
            "开发记录",
            "模型参数文件",
            "docs/governance/project.yaml",
            "docs/governance/roadmap.yaml",
            "docs/governance/events.jsonl",
            "Stage -> Phase -> Task",
            "^S[1-9][0-9]*P[A-Z]T[0-9]{2}$",
            "Run Modes And Writes",
            "Risk-Tier Routing",
            "Changed-Scope CI And Hook",
            "Sync And Manifests",
            "Machine Field Contracts",
            "Semantic Accuracy",
            "Token Budget And Scope",
            "中文优先，默认全局中文",
            "whole repository",
            "registered project",
            "PR descriptions",
            "CI-facing summaries",
            "owner-facing documents",
        }:
            self.assertIn(required, text)
        for forbidden in {
            "Review-5 Diff Synchronization Contract",
            "Review-9 Cost and Entry Gate Contract",
            "Human-Readable Generated Status",
        }:
            self.assertNotIn(forbidden, text)

    def test_review9_adp_bootstrap_does_not_trigger_on_shared_governance_paths(self) -> None:
        for workflow_name in {
            "arxiv-daily-push-stage1-bootstrap.yml",
            "arxiv-daily-push-phase12-cloud-dry-run.yml",
            "arxiv-daily-push-real-backfill.yml",
        }:
            workflow = (ROOT / ".github" / "workflows" / workflow_name).read_text(encoding="utf-8")
            self.assertIn('"arxiv-daily-push/**"', workflow)
            self.assertIn("runtime-change-scope:", workflow)
            self.assertIn("classify-arxiv-runtime-change", workflow)
            self.assertIn("needs: runtime-change-scope", workflow)
            self.assertIn("governance-only paths do not run this external/runtime check", workflow)
            self.assertIn("arxiv-daily-push/(src|tests|config|schemas)/", workflow)
            for forbidden in {'"governance/**"', '"scripts/**"', '"tests/governance/**"'}:
                self.assertNotIn(forbidden, workflow)

    def test_review7_setup_doctor_reports_missing_hooks_unverified(self) -> None:
        doctor = load_setup_doctor_module()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            with patch.object(doctor, "ROOT", tmp_path):
                status = doctor.hook_status()
        self.assertEqual(status["hooks_enabled"], "UNVERIFIED")
        self.assertEqual(status["stop_hook_loaded"], "UNVERIFIED")
        self.assertEqual(status["repository_trusted"], "UNVERIFIED")

    def test_review8_setup_doctor_strict_local_fails_unverified_hook(self) -> None:
        doctor = load_setup_doctor_module()
        report = doctor.build_report(check_github=False, strict_local=True, strict_github=False)
        self.assertEqual(report["status"], "FAIL", report)
        self.assertTrue(any("hook.repository_trusted" in item for item in report["failures"]), report)

    def test_review8_setup_doctor_non_strict_reports_warn_not_pass(self) -> None:
        doctor = load_setup_doctor_module()
        report = doctor.build_report(check_github=False)
        self.assertEqual(report["status"], "WARN", report)
        self.assertTrue(report["warnings"], report)

    def test_review8_owner_portfolio_bucket_total_must_cover_unverified(self) -> None:
        quality = load_information_quality_module()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            (tmp_path / "OWNER_PORTFOLIO.md").write_text(
                "\n".join(
                    [
                        "# OWNER_PORTFOLIO",
                        "- project_total: `2`",
                        "- bucket_total: `1`",
                        "- failed: `1`",
                        "- partial: `0`",
                        "- unverified: `0`",
                        "- verified: `0`",
                        "- not_applicable: `0`",
                        "`A`",
                        "`B`",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            projects = [{"project_id": "A"}, {"project_id": "B"}]
            with patch.object(quality, "ROOT", tmp_path):
                gate = quality.Gate()
                quality.check_owner_portfolio_buckets(gate, projects)
        self.assertTrue(any(item.code == "PORTFOLIO_BUCKET_TOTAL" for item in gate.errors), gate.errors)

    def test_review9_s6pat03_information_quality_uses_artifact_portfolio_text(self) -> None:
        quality = load_information_quality_module()
        projects = [{"project_id": "A", "path": "A"}, {"project_id": "B", "path": "B"}]
        portfolio_text = (
            "\n".join(
                [
                    "# OWNER_PORTFOLIO",
                    "- project_total: `2`",
                    "- bucket_total: `2`",
                    "- failed: `1`",
                    "- partial: `1`",
                    "- unverified: `0`",
                    "- verified: `0`",
                    "- not_applicable: `0`",
                    "`A`",
                    "`B`",
                ]
            )
            + "\n"
        )
        with (
            patch.object(quality, "project_config", return_value=projects),
            patch.object(quality, "check_project_set"),
            patch.object(quality, "check_generated_views"),
            patch.object(quality, "check_hook_and_ci"),
            patch.object(quality, "check_assurance"),
            patch.object(quality, "check_events"),
            patch.object(quality, "render_owner_portfolio_text", return_value=portfolio_text) as render_portfolio,
        ):
            result = quality.run()
        render_portfolio.assert_called_once_with(projects)
        self.assertEqual(result["errors"], 0, result)

    def test_review8_owner_decision_rejects_codex_owner_and_review6(self) -> None:
        quality = load_information_quality_module()
        assurance = {
            "owner_decision": {
                "decision_id": "DEC-P-REVIEW6-001",
                "review_id": "REVIEW6",
                "project_id": "P",
                "decision_question": "Decide",
                "human_owner_role": "Codex/governance runner",
                "human_assignment_status": "HUMAN_ASSIGNMENT_REQUIRED",
                "current_recommendation": "A",
                "option_a": "A",
                "option_b": "B",
                "option_c": "C",
                "estimated_effort": "P1",
                "estimated_cost_or_resource": "time",
                "expected_benefit": "benefit",
                "principal_risks": "risk",
                "evidence_required": "evidence",
                "decision_deadline_or_priority": "P1",
                "consequence_of_no_decision": "blocked",
                "unblock_task_id": "TASK-1",
                "acceptance_ids": ["ACC-1"],
            }
        }
        gate = quality.Gate()
        quality.check_owner_decision(gate, assurance, ROOT / "OWNER_PORTFOLIO.md", "P")
        codes = {item.code for item in gate.errors}
        self.assertIn("DECISION_OWNER", codes)
        self.assertIn("DECISION_REVIEW", codes)

    def test_review8_serenity_first_baseline_next_task_is_stale(self) -> None:
        quality = load_information_quality_module()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            docs = tmp_path / "Serenity-Alipay" / "docs" / "governance"
            docs.mkdir(parents=True)
            (docs / "delivery_tasks.yaml").write_text(
                "\n".join(
                    [
                        "tasks:",
                        "  - task_id: TASK-A-001",
                        "    objective: Create the first CodexProject-auditable Serenity-Alipay governance baseline.",
                        "    status: in_progress",
                        "    dependencies: []",
                        "    acceptance_ids: [ACC-A-001]",
                        "    test_commands: [validator]",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            assurance = {
                "next_executable_task": {"task_id": "TASK-A-001"},
                "dimensions": {
                    "implementation_congruence": {
                        "status": "VERIFIED",
                        "total_active_parameters": 49,
                        "total_active_formulas": 12,
                    }
                },
            }
            with patch.object(quality, "ROOT", tmp_path), patch.object(quality.structural, "ROOT", tmp_path):
                gate = quality.Gate()
                quality.check_next_task(gate, assurance, tmp_path / "Serenity-Alipay", "Serenity-Alipay")
        self.assertTrue(any(item.code == "NEXT_TASK_STALE" for item in gate.errors), gate.errors)

    def test_review9_stop_hook_does_not_write_receipts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            subprocess.run(["git", "init"], cwd=tmp_path, stdout=subprocess.PIPE, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True)
            subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, check=True)
            (tmp_path / "governance").mkdir()
            (tmp_path / "governance" / "projects.yaml").write_text("governance_spec_version: '1.0.0'\n", encoding="utf-8")
            subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
            subprocess.run(["git", "commit", "-m", "init"], cwd=tmp_path, stdout=subprocess.PIPE, check=True)
            result = subprocess.run(
                [sys.executable, str(STOP_HOOK)],
                input=json.dumps({"cwd": str(tmp_path), "task_id": "GOV-REVIEW8-TEST"}),
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            payload = json.loads(result.stdout)
            receipts_dir_exists = (tmp_path / "governance" / "run_receipts").exists()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(payload.get("continue"))
        self.assertEqual(payload.get("governance_hint", {}).get("mode"), "advisory")
        self.assertNotIn("governance_receipt", payload)
        self.assertFalse(receipts_dir_exists)

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
            status_path = tmp_path / "P" / "docs" / "governance" / "STATUS.md"
            status_path.parent.mkdir(parents=True)
            status_path.write_text(
                "source_base_commit\nsource_snapshot_hash\ngenerator_version\nPENDING\n",
                encoding="utf-8",
            )
            with patch.object(quality, "ROOT", tmp_path):
                gate = quality.Gate()
                quality.check_generated_views(gate, [{"path": "P"}], include_root=False)
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
        if os.environ.get("GITHUB_EVENT_NAME") == "pull_request":
            base_ref = os.environ.get("GITHUB_BASE_REF") or "main"
            diff = subprocess.run(
                ["git", "-c", "core.quotePath=false", "diff", "--name-only", f"origin/{base_ref}...HEAD"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
            )
            if diff.returncode == 0 and not any(path.startswith("Serenity-Alipay/") for path in diff.stdout.splitlines()):
                self.skipTest("Serenity semantic extractor gate is enforced only for Serenity PR diffs, schedule, or manual all-scope runs")
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

    def test_review6_numeric_selector_multiply_transform(self) -> None:
        semantic = load_semantic_module()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            project = tmp_path / "P"
            project.mkdir(parents=True)
            (project / "impl.py").write_text('WINDOWS = ("1m", "3m", "12m", "10d")\n', encoding="utf-8")
            with patch.object(semantic, "ROOT", tmp_path):
                extracted = semantic.extract_selector("python_ast_tuple_len:P/impl.py::WINDOWS|multiply=2")
        self.assertEqual(extracted, 8)

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

    def test_fallback_yaml_loader_preserves_quoted_symbol_refs(self) -> None:
        structural = load_validator_module()
        parsed = structural.fallback_yaml_load(
            "\n".join(
                [
                    "implementation_refs:",
                    '  - "P/impl.py::rule"',
                    '  - "csv_row:P/formulas.csv::formula_id=F-X"',
                    "",
                ]
            )
        )
        self.assertEqual(
            parsed["implementation_refs"],
            ["P/impl.py::rule", "csv_row:P/formulas.csv::formula_id=F-X"],
        )

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
        owner_outputs = [path for path in first["outputs"] if path.replace("\\", "/").endswith("/docs/governance/OWNER_STATUS.md")]
        status_outputs = [path for path in first["outputs"] if path.replace("\\", "/").endswith("/docs/governance/STATUS.md")]
        self.assertEqual(len(owner_outputs), len(status_outputs))
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
        pfi_project = next(
            project
            for project in dashboard.structural.load_yaml(ROOT / "governance" / "projects.yaml")["projects"]
            if project["project_id"] == "PFI_BIG_DATA_SIMULATOR"
        )
        self.assertIn("PFI_BIG_DATA_SIMULATOR", dashboard.render_owner_status(dashboard.load_project(pfi_project)))

    def test_review6_owner_status_is_readable_and_prioritized(self) -> None:
        dashboard = load_dashboard_module()
        config = dashboard.structural.load_yaml(ROOT / "governance" / "projects.yaml")
        serenity = next(project for project in config["projects"] if project["project_id"] == "Serenity-Alipay")
        info = dashboard.load_project(serenity)
        rendered = dashboard.render_owner_status(info)
        for marker in (
            "## 1. 当前结论",
            "## 2. 本次运行改变了什么",
            "## 4. 需要人类决定什么",
            "## 9. A/B/C Choice Matrix",
            "## 17. Next Unique Task",
        ):
            self.assertIn(marker, rendered)
        self.assertIn("实现一致性", rendered)
        self.assertIn("empirical_validation", rendered)
        self.assertIn("operational_validation", rendered)
        self.assertNotIn("['", rendered)
        self.assertNotIn("{'", rendered)
        self.assertNotEqual(info["assurance"]["next_executable_task"]["task_id"], "TASK-A-001")

    def test_arxiv_s1_v4_baseline_lock_hashes_and_version_alignment(self) -> None:
        baseline_dir = ROOT / "arxiv-daily-push" / "docs" / "pursuing_goal"
        expected_hashes = {
            "START_HERE_MASTER_TASK_PACK_TWO_STAGE_V4.md": "4de90b3ddac0d38880fe185d5f14c997fca797cbd26f80755bb33b5bc6806e1a",
            "FULL_PURSUING_GOAL_PROMPT_TWO_STAGE_V4.txt": "b20add8661983e4797da72c3800d86f343fad3a1c13c62f3b08c8b0320634c3c",
            "baseline/REFERENCE_OWNER_DECISIONS.rtf": "ed983f72e6233b6c2d707e69d131be9416f894aa46d39e7d962dcf65c738f7e0",
            "baseline/MULTISOURCE_LOCAL_PRODUCTION_TASKPACK_V1.md": "2900f5c810ea4e87ea8a33b953551c4d822475e7063547e9cbc1627100f96bab",
        }
        for relative, expected in expected_hashes.items():
            data = (baseline_dir / relative).read_bytes().replace(b"\r\n", b"\n")
            actual = hashlib.sha256(data).hexdigest()
            self.assertEqual(actual, expected, relative)

        version = (ROOT / "arxiv-daily-push" / "VERSION").read_text(encoding="utf-8").strip()
        pyproject = (ROOT / "arxiv-daily-push" / "pyproject.toml").read_text(encoding="utf-8")
        package_init = (ROOT / "arxiv-daily-push" / "src" / "arxiv_daily_push" / "__init__.py").read_text(encoding="utf-8")
        matrix = load_validator_module().load_yaml(ROOT / "arxiv-daily-push" / "docs" / "governance" / "VERSION_MATRIX.yaml")
        self.assertEqual(version, matrix["product_version"])
        self.assertIn(f'version = "{version}"', pyproject)
        self.assertIn(f'__version__ = "{version}"', package_init)

        tasks = load_validator_module().load_yaml(ROOT / "arxiv-daily-push" / "docs" / "governance" / "delivery_tasks.yaml")["tasks"]
        task_by_id = {task["task_id"]: task for task in tasks}
        self.assertEqual(task_by_id["ADP-PHASE12-MANUAL-DELIVERY-INTERNAL-RELEASE-DEDUPE-035"]["status"], "completed")
        self.assertEqual(task_by_id["S1-02-BASELINE-LOCK-TRACEABILITY-001"]["status"], "completed")
        self.assertEqual(task_by_id["ADP-PHASE12-EMAIL-HUMAN-FORMAT-036"]["status"], "completed")
        self.assertEqual(task_by_id["S1-03-OWNER-CONTROLS-001"]["status"], "completed")
        self.assertEqual(task_by_id["S1-04-SQLITE-DATA-MODEL-001"]["status"], "completed")
        self.assertEqual(task_by_id["S1-05-ARXIV-CONNECTOR-CONTRACT-001"]["status"], "completed")
        self.assertEqual(task_by_id["S1-06-SCORING-QUEUE-LEDGER-001"]["status"], "completed")
        self.assertEqual(task_by_id["S1-07-B1_REPORT_EMAIL_TEXT-001"]["status"], "completed")
        self.assertEqual(task_by_id["S1-08-LOCAL_RUNTIME_RECOVERY-001"]["status"], "completed")
        self.assertEqual(task_by_id["S1-09-MIGRATION_PACKAGE-001"]["status"], "completed")
        self.assertEqual(task_by_id["S1-10-POST_MIGRATION_BOOTSTRAP-001"]["status"], "completed")
        self.assertEqual(task_by_id["S1-11-HISTORICAL_B1_PREVIEWS-001"]["status"], "completed")
        self.assertEqual(task_by_id["S1P5T03-R-REAL_ARXIV_30_DAY_BACKFILL_AND_LEDGER_RECONCILE"]["status"], "completed")
        self.assertEqual(task_by_id["S1-12-CONTROLLED_B1_LIVE_EMAIL_DAYS-001"]["status"], "completed")
        self.assertEqual(task_by_id["ADP-S1P5T05-LOCAL-PRODUCTION-AND-MIGRATION-PREP"]["status"], "completed")
        self.assertEqual(task_by_id["S2PAT05"]["status"], "completed")
        self.assertEqual(task_by_id["S2PBT01"]["status"], "completed")
        self.assertEqual(task_by_id["S2P1T01"]["status"], "deprecated")
        self.assertEqual(task_by_id["ADP-PHASE12-EMAIL-FRONTSTAGE-QUALITY-037"]["status"], "planned")
        self.assertEqual(task_by_id["ADP-PHASE12-EMAIL-DECISION-UI-V2-038"]["status"], "planned")

    def test_arxiv_project_root_human_entry_files_include_v6_roadmap(self) -> None:
        project_dir = ROOT / "arxiv-daily-push"
        for name in ("功能清单", "开发记录", "模型参数文件"):
            text = (project_dir / name).read_text(encoding="utf-8")
            self.assertIn("arxiv-daily-push", text)
            self.assertNotIn("TODO", text)
        ledger = (project_dir / "开发记录").read_text(encoding="utf-8")
        for required in {
            "S1P5T04",
            "ARXIV_PRODUCTION_ACCEPTED",
            "S2P7T04",
            "roadmap_sha256",
            "76b2d29a6d5cd62de472f1a8c265a89fcf03dc7031f7d4e209f85c650b498f10",
        }:
            self.assertIn(required, ledger)

    def test_arxiv_owner_status_uses_latest_event_manifest(self) -> None:
        dashboard = load_dashboard_module()
        config = dashboard.structural.load_yaml(ROOT / "governance" / "projects.yaml")
        project = next(project for project in config["projects"] if project["project_id"] == "arxiv-daily-push")
        info = dashboard.load_project(project)
        self.assertEqual(info["latest_event"]["event_id"], "EVENT-20260624-ADP-094")
        self.assertEqual(info["assurance"]["as_of_event_id"], "EVENT-20260624-ADP-094")
        self.assertEqual(info["product_version"], "0.23.0")
        self.assertEqual(
            info["current_gate"],
            "ARXIV_PRODUCTION_ACCEPTED_MAINTAINED_AND_V7_1_PRODUCT_CONTRACT_AND_AUDIT_LOCKED",
        )
        self.assertEqual(
            info["latest_manifest"]["_path"].replace("\\", "/"),
            "governance/run_manifests/ADP-S2P2T01-TOP-JOURNAL-SHADOW-FOUNDATION-20260624.json",
        )
        self.assertEqual(info["assurance"]["delivery_readiness"]["status"], "VERIFIED")
        self.assertEqual(
            info["assurance"]["delivery_readiness"]["release_gate"],
            "ARXIV_PRODUCTION_ACCEPTED_MAINTAINED_AND_V7_1_PRODUCT_CONTRACT_AND_AUDIT_LOCKED",
        )
        self.assertFalse(info["latest_manifest"].get("production_acceptance_claimed", False))
        self.assertFalse(info["latest_event"]["production_schedule_enabled"])
        self.assertFalse(info["latest_event"]["real_smtp_sent"])
        self.assertFalse(info["latest_event"]["real_release_uploaded"])
        rendered = dashboard.render_owner_status(info)
        self.assertIn("0.23.0", rendered)
        self.assertIn("ARXIV_PRODUCTION_ACCEPTED", rendered)
        self.assertIn("ADP-S1P5T05", rendered)
        self.assertIn("V7_1_PRODUCT_CONTRACT_AND_AUDIT_LOCKED", rendered)
        self.assertIn("S2P1T01", rendered)
        self.assertIn("GitHub 只保留代码、PR/CI、证据、状态和备份角色", rendered)
        self.assertNotIn("是否继续执行 S1-07", rendered)
        self.assertNotIn("是否继续执行 S1-08", rendered)
        self.assertNotIn("是否继续执行 S1-09", rendered)
        self.assertNotIn("是否继续执行 S1-10", rendered)
        self.assertNotIn("是否继续执行 S1-11", rendered)
        self.assertNotIn("STRICT_ARXIV_PRODUCTION_ACCEPTANCE_REOPENED_PENDING_S1P5T03R_CLOUD_CI", rendered)
        self.assertNotIn("DETERMINISTIC_GENERATION", rendered)

    def test_arxiv_s1_next_task_priority_does_not_reorder_other_projects(self) -> None:
        dashboard = load_dashboard_module()
        config = dashboard.structural.load_yaml(ROOT / "governance" / "projects.yaml")
        expected = {
            "arxiv-daily-push": "S2PCT02",
            "OpenAIDatabase": "TASK-OAI-B-001",
            "PFI_BIG_DATA_SIMULATOR": "TASK-PFI-B-001",
            "whkmSalary": "TASK-WHKM-B-001",
        }
        for project_id, task_id in expected.items():
            with self.subTest(project_id=project_id):
                project = next(project for project in config["projects"] if project["project_id"] == project_id)
                info = dashboard.load_project(project)
                self.assertEqual(info["assurance"]["next_executable_task"]["task_id"], task_id)

    def test_eei_a209_4h_soak_governance_stays_partial_until_24h_exists(self) -> None:
        validator = load_validator_module()
        matrix = validator.load_yaml(ROOT / "EEI" / "docs" / "governance" / "VERSION_MATRIX.yaml")
        self.assertEqual(matrix["current_iteration"], "ITER-20260624-REVIEW9-S5PBT01")
        self.assertEqual(
            matrix["current_gate"],
            "S5PB-GATE-IN-PROGRESS",
        )
        assurance = validator.load_yaml(ROOT / "EEI" / "docs" / "governance" / "ASSURANCE_STATUS.yaml")
        self.assertEqual(
            assurance["delivery_readiness"]["release_gate"],
            "TASK-T904-A026-A027-PRODUCTION-GOLD-INTAKE-IN-PROGRESS",
        )

        events = [json.loads(line) for line in (ROOT / "EEI" / "docs" / "governance" / "development_events.jsonl").read_text(encoding="utf-8").splitlines()]
        soak_event = next(event for event in events if event.get("event_id") == "EVENT-20260621-019")
        self.assertEqual(soak_event["task_id"], "TASK-T1307")
        self.assertIn("PARTIAL", soak_event["result"])
        release_bundle_event = next(event for event in events if event.get("event_id") == "EVENT-20260622-012")
        self.assertEqual(release_bundle_event["task_id"], "TASK-T1301")
        self.assertIn("TASK-T1307", release_bundle_event["task_ids"])
        self.assertIn("release_ready=false", "; ".join(release_bundle_event["test_results"]))
        review6_event = next(event for event in events if event.get("event_id") == "EVT-REVIEW6-FINAL-EEI-001")
        self.assertEqual(review6_event["binding_status"], "pre_commit_pending")
        ci_binding_event = next(event for event in events if event.get("event_id") == "EVENT-20260623-001")
        self.assertEqual(ci_binding_event["binding_status"], "ci_attested")
        self.assertEqual(
            ci_binding_event["result_commit"],
            "d009516c57c4908a025c401a711dfb4d599f7b73",
        )
        worker_wake_event = next(event for event in events if event.get("event_id") == "EVENT-20260623-002")
        self.assertEqual(worker_wake_event["task_id"], "TASK-T1303")
        self.assertEqual(worker_wake_event["binding_status"], "stale_unbound")
        self.assertIn("stale_classification_reason", worker_wake_event)
        self.assertIn("TASK-T1307", worker_wake_event["task_ids"])
        self.assertIn("make verify PASS", worker_wake_event["test_results"])
        self.assertIn("TASK-T1302", ci_binding_event["task_ids"])
        self.assertIn("TASK-T1303", ci_binding_event["task_ids"])
        operation_log_event = next(event for event in events if event.get("event_id") == "EVENT-20260623-004")
        self.assertEqual(operation_log_event["task_id"], "TASK-T1301")
        self.assertEqual(operation_log_event["binding_status"], "ci_attested")
        self.assertEqual(
            operation_log_event["result_commit"],
            "cb8e096fd54508080d73a6e83c015c15cfd9bd9a",
        )
        self.assertIn("TASK-T1307", operation_log_event["task_ids"])
        source_withdrawal_event = next(
            event for event in events if event.get("event_id") == "EVENT-20260623-005"
        )
        self.assertEqual(source_withdrawal_event["task_id"], "TASK-T1301")
        self.assertEqual(source_withdrawal_event["binding_status"], "stale_unbound")
        self.assertIn("stale_classification_reason", source_withdrawal_event)
        self.assertIn("TASK-T1307", source_withdrawal_event["task_ids"])
        self.assertIn("make verify PASS", "; ".join(source_withdrawal_event["test_results"]))
        release_manager_event = next(event for event in events if event.get("event_id") == "EVENT-20260623-006")
        self.assertEqual(release_manager_event["task_id"], "TASK-T1303")
        self.assertEqual(release_manager_event["binding_status"], "pre_commit_pending")
        self.assertIn("TASK-T904", release_manager_event["task_ids"])
        self.assertIn("release-manager artifact validate PASS", release_manager_event["test_results"])
        gold_intake_event = next(event for event in events if event.get("event_id") == "EVENT-20260623-008")
        self.assertEqual(gold_intake_event["task_id"], "TASK-T904")
        self.assertEqual(gold_intake_event["binding_status"], "pre_commit_pending")
        self.assertIn("TASK-T1303", gold_intake_event["task_ids"])
        self.assertIn("gold-quality unit tests PASS 7/7", gold_intake_event["test_results"])
        t905_event = next(event for event in events if event.get("event_id") == "EVENT-20260623-009")
        self.assertEqual(t905_event["task_id"], "TASK-T905")
        self.assertEqual(t905_event["binding_status"], "pre_commit_pending")
        self.assertIn("TASK-T905", t905_event["task_ids"])
        self.assertIn("T905 validator PASS", t905_event["test_results"])
        source_anchor_event = next(event for event in events if event.get("event_id") == "EVENT-20260623-010")
        self.assertEqual(source_anchor_event["task_id"], "TASK-T1301")
        self.assertEqual(source_anchor_event["binding_status"], "pre_commit_pending")
        self.assertIn("TASK-T1301", source_anchor_event["task_ids"])
        self.assertIn("candidate-source-anchor coverage PASS", "; ".join(source_anchor_event["test_results"]))

        owner_text = (ROOT / "EEI" / "docs" / "governance" / "OWNER_STATUS.md").read_text(encoding="utf-8")
        self.assertIn(
            "TASK-T904-A026-A027-PRODUCTION-GOLD-INTAKE-IN-PROGRESS",
            owner_text,
        )
        self.assertIn("24h operator soak evidence", owner_text)

        self.assertTrue((ROOT / "EEI" / "artifacts" / "tests" / "a209" / "t1307_operator_soak_4h.json").is_file())
        self.assertTrue((ROOT / "EEI" / "artifacts" / "tests" / "a209" / "t1307_operator_soak_4h.checkpoints.jsonl").is_file())
        self.assertFalse((ROOT / "EEI" / "artifacts" / "tests" / "a209" / "t1307_operator_soak_24h.json").exists())

    def test_eei_dashboard_sync_manifest_binds_root_views(self) -> None:
        manifest = json.loads(
            (
                ROOT
                / "governance"
                / "run_manifests"
                / "GOV-EEI-DASHBOARD-SYNC-20260622.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(manifest["schema_version"], 2)
        self.assertEqual(manifest["project_id"], "root-governance")
        self.assertEqual(manifest["binding_status"], "PRECOMMIT_TREE_BOUND")
        self.assertRegex(
            manifest["content_tree_hash"],
            r"^sha256-changed-files-excluding-this-manifest:[0-9a-f]{64}$",
        )
        changed = set(manifest["changed_files_actual"])
        for path in {
            "README.md",
            "GOVERNANCE_DASHBOARD.md",
            "OWNER_PORTFOLIO.md",
            "governance/binding_backlog.yaml",
            "tests/governance/test_project_governance_validator.py",
            "governance/run_manifests/GOV-EEI-DASHBOARD-SYNC-20260622.json",
        }:
            self.assertIn(path, changed)
        self.assertFalse((ROOT / "governance" / "binding_backlog.yaml").exists())

    def test_eei_a202_dashboard_sync_manifest_binds_root_views(self) -> None:
        manifest = json.loads(
            (
                ROOT
                / "governance"
                / "run_manifests"
                / "GOV-EEI-A202-DASHBOARD-SYNC-20260623.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(manifest["schema_version"], 2)
        self.assertEqual(manifest["project_id"], "root-governance")
        self.assertEqual(manifest["binding_status"], "PRECOMMIT_TREE_BOUND")
        self.assertRegex(
            manifest["content_tree_hash"],
            r"^sha256-changed-files-excluding-this-manifest:[0-9a-f]{64}$",
        )
        changed = set(manifest["changed_files_actual"])
        for path in {
            "README.md",
            "GOVERNANCE_DASHBOARD.md",
            "OWNER_PORTFOLIO.md",
            "governance/binding_backlog.yaml",
            "EEI/docs/governance/ASSURANCE_STATUS.yaml",
            "EEI/docs/governance/STATUS.md",
            "EEI/docs/governance/OWNER_STATUS.md",
            "tests/governance/test_project_governance_validator.py",
            "governance/run_manifests/GOV-EEI-A202-DASHBOARD-SYNC-20260623.json",
        }:
            self.assertIn(path, changed)
        self.assertFalse((ROOT / "GOVERNANCE_DASHBOARD.md").exists())

    def test_adp_s104_dashboard_sync_manifest_binds_root_views(self) -> None:
        manifest = json.loads(
            (
                ROOT
                / "governance"
                / "run_manifests"
                / "ADP-S1-04-DASHBOARD-SYNC-20260622.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(manifest["schema_version"], 2)
        self.assertEqual(manifest["project_id"], "root-governance")
        self.assertEqual(manifest["binding_status"], "PRECOMMIT_TREE_BOUND")
        self.assertRegex(
            manifest["content_tree_hash"],
            r"^sha256-changed-files-excluding-this-manifest:[0-9a-f]{64}$",
        )
        changed = set(manifest["changed_files_actual"])
        for path in {
            "README.md",
            "GOVERNANCE_DASHBOARD.md",
            "OWNER_PORTFOLIO.md",
            "governance/binding_backlog.yaml",
            "tests/governance/test_project_governance_validator.py",
            "governance/run_manifests/ADP-S1-04-DASHBOARD-SYNC-20260622.json",
        }:
            self.assertIn(path, changed)
        self.assertFalse((ROOT / "GOVERNANCE_DASHBOARD.md").exists())
        self.assertFalse((ROOT / "governance" / "binding_backlog.yaml").exists())

    def test_review5_run_manifest_supports_post_commit_binding_fields(self) -> None:
        manifest = json.loads(
            (ROOT / "governance" / "run_manifests" / "GOV-REVIEW5-SYNC-001.json").read_text(encoding="utf-8")
        )
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
            (ROOT / "governance" / "run_manifests" / "ADP-PHASE2-DATA-CONTRACTS-20260621.json").read_text(encoding="utf-8")
        )
        self.assertEqual(manifest["project_id"], "arxiv-daily-push")
        self.assertEqual(manifest["task_id"], "ADP-PHASE2-DATA-CONTRACTS-001")
        self.assertIn("MOD-ADP-004", manifest["model_delta"])

    def test_arxiv_daily_push_phase3_manifest_records_arxiv_adapter_gate(self) -> None:
        manifest = json.loads(
            (ROOT / "governance" / "run_manifests" / "ADP-PHASE3-ARXIV-ADAPTER-20260621.json").read_text(encoding="utf-8")
        )
        self.assertEqual(manifest["project_id"], "arxiv-daily-push")
        self.assertEqual(manifest["task_id"], "ADP-PHASE3-ARXIV-ADAPTER-001")
        self.assertIn("MOD-ADP-005", manifest["model_delta"])

    def test_arxiv_daily_push_phase4_manifest_records_ranking_gate(self) -> None:
        manifest = json.loads((ROOT / "governance" / "run_manifests" / "ADP-PHASE4-RANKING-20260621.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["project_id"], "arxiv-daily-push")
        self.assertEqual(manifest["task_id"], "ADP-PHASE4-RANKING-001")
        self.assertIn("MOD-ADP-002", manifest["model_delta"])

    def test_arxiv_daily_push_phase5_manifest_records_evidence_gate(self) -> None:
        manifest = json.loads(
            (ROOT / "governance" / "run_manifests" / "ADP-PHASE5-EVIDENCE-GATE-20260621.json").read_text(encoding="utf-8")
        )
        self.assertEqual(manifest["project_id"], "arxiv-daily-push")
        self.assertEqual(manifest["task_id"], "ADP-PHASE5-EVIDENCE-GATE-001")
        self.assertIn("MOD-ADP-003", manifest["model_delta"])

    def test_arxiv_daily_push_phase6_manifest_records_lesson_gate(self) -> None:
        manifest = json.loads((ROOT / "governance" / "run_manifests" / "ADP-PHASE6-LESSON-20260621.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["project_id"], "arxiv-daily-push")
        self.assertEqual(manifest["task_id"], "ADP-PHASE6-LESSON-001")
        self.assertIn("MOD-ADP-006", manifest["model_delta"])

    def test_arxiv_daily_push_phase7_manifest_records_narration_gate(self) -> None:
        manifest = json.loads((ROOT / "governance" / "run_manifests" / "ADP-PHASE7-TTS-20260621.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["project_id"], "arxiv-daily-push")
        self.assertEqual(manifest["task_id"], "ADP-PHASE7-TTS-001")
        self.assertIn("MOD-ADP-007", manifest["model_delta"])

    def test_arxiv_daily_push_phase8_manifest_records_video_gate(self) -> None:
        manifest = json.loads((ROOT / "governance" / "run_manifests" / "ADP-PHASE8-VIDEO-20260621.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["project_id"], "arxiv-daily-push")
        self.assertEqual(manifest["task_id"], "ADP-PHASE8-VIDEO-001")
        self.assertIn("MOD-ADP-008", manifest["model_delta"])

    def test_arxiv_daily_push_phase9_manifest_records_pipeline_gate(self) -> None:
        manifest = json.loads((ROOT / "governance" / "run_manifests" / "ADP-PHASE9-LOCAL-PIPELINE-20260621.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["project_id"], "arxiv-daily-push")
        self.assertEqual(manifest["task_id"], "ADP-PHASE9-LOCAL-PIPELINE-001")
        self.assertIn("MOD-ADP-009", manifest["model_delta"])

    def test_arxiv_daily_push_phase10_manifest_records_handoff_gate(self) -> None:
        manifest = json.loads(
            (ROOT / "governance" / "run_manifests" / "ADP-PHASE10-RUNNER-RELEASE-EMAIL-20260621.json").read_text(encoding="utf-8")
        )
        self.assertEqual(manifest["project_id"], "arxiv-daily-push")
        self.assertEqual(manifest["task_id"], "ADP-PHASE10-RUNNER-RELEASE-EMAIL-001")
        self.assertIn("MOD-ADP-010", manifest["model_delta"])

    def test_arxiv_daily_push_phase11_manifest_records_acceptance_gate(self) -> None:
        manifest = json.loads(
            (ROOT / "governance" / "run_manifests" / "ADP-PHASE11-ACCEPTANCE-HANDOFF-20260621.json").read_text(encoding="utf-8")
        )
        self.assertEqual(manifest["project_id"], "arxiv-daily-push")
        self.assertEqual(manifest["task_id"], "ADP-PHASE11-ACCEPTANCE-HANDOFF-001")
        self.assertIn("MOD-ADP-011", manifest["model_delta"])

    def test_arxiv_daily_push_phase11_manifest_records_evidence_ref_hardening(self) -> None:
        manifest = json.loads(
            (ROOT / "governance" / "run_manifests" / "ADP-PHASE11-EVIDENCE-REF-HARDENING-20260621.json").read_text(encoding="utf-8")
        )
        self.assertEqual(manifest["project_id"], "arxiv-daily-push")
        self.assertEqual(manifest["task_id"], "ADP-PHASE11-EVIDENCE-REF-HARDENING-002")
        self.assertIn("MOD-ADP-011", manifest["model_delta"])

    def test_arxiv_daily_push_phase11_manifest_records_trial_evidence_validator(self) -> None:
        manifest = json.loads(
            (ROOT / "governance" / "run_manifests" / "ADP-PHASE11-TRIAL-EVIDENCE-VALIDATOR-20260621.json").read_text(encoding="utf-8")
        )
        self.assertEqual(manifest["project_id"], "arxiv-daily-push")
        self.assertEqual(manifest["task_id"], "ADP-PHASE11-TRIAL-EVIDENCE-VALIDATOR-003")
        self.assertIn("MOD-ADP-012", manifest["model_delta"])

    def test_arxiv_daily_push_phase11_manifest_records_production_preflight(self) -> None:
        manifest = json.loads(
            (ROOT / "governance" / "run_manifests" / "ADP-PHASE11-PRODUCTION-PREFLIGHT-20260621.json").read_text(encoding="utf-8")
        )
        self.assertEqual(manifest["project_id"], "arxiv-daily-push")
        self.assertEqual(manifest["task_id"], "ADP-PHASE11-PRODUCTION-PREFLIGHT-004")
        self.assertIn("MOD-ADP-013", manifest["model_delta"])

    def test_arxiv_daily_push_phase11_manifest_records_trial_bootstrap(self) -> None:
        manifest = json.loads(
            (ROOT / "governance" / "run_manifests" / "ADP-PHASE11-TRIAL-BOOTSTRAP-20260621.json").read_text(encoding="utf-8")
        )
        self.assertEqual(manifest["project_id"], "arxiv-daily-push")
        self.assertEqual(manifest["task_id"], "ADP-PHASE11-TRIAL-BOOTSTRAP-005")
        self.assertIn("MOD-ADP-014", manifest["model_delta"])

    def test_arxiv_daily_push_phase11_manifest_records_live_arxiv_ingest(self) -> None:
        manifest = json.loads(
            (ROOT / "governance" / "run_manifests" / "ADP-PHASE11-LIVE-ARXIV-INGEST-20260621.json").read_text(encoding="utf-8")
        )
        self.assertEqual(manifest["project_id"], "arxiv-daily-push")
        self.assertEqual(manifest["task_id"], "ADP-PHASE11-LIVE-ARXIV-INGEST-006")
        self.assertIn("MOD-ADP-015", manifest["model_delta"])

    def test_arxiv_daily_push_phase11_manifest_records_smtp_delivery(self) -> None:
        manifest = json.loads(
            (ROOT / "governance" / "run_manifests" / "ADP-PHASE11-SMTP-DELIVERY-20260621.json").read_text(encoding="utf-8")
        )
        self.assertEqual(manifest["project_id"], "arxiv-daily-push")
        self.assertEqual(manifest["task_id"], "ADP-PHASE11-SMTP-DELIVERY-007")
        self.assertIn("MOD-ADP-016", manifest["model_delta"])

    def test_arxiv_daily_push_phase11_manifest_records_release_delivery(self) -> None:
        manifest = json.loads(
            (ROOT / "governance" / "run_manifests" / "ADP-PHASE11-RELEASE-DELIVERY-20260621.json").read_text(encoding="utf-8")
        )
        self.assertEqual(manifest["project_id"], "arxiv-daily-push")
        self.assertEqual(manifest["task_id"], "ADP-PHASE11-RELEASE-DELIVERY-008")
        self.assertIn("MOD-ADP-017", manifest["model_delta"])

    def test_arxiv_daily_push_phase11_manifest_records_production_scheduler(self) -> None:
        manifest = json.loads(
            (ROOT / "governance" / "run_manifests" / "ADP-PHASE11-PRODUCTION-SCHEDULER-20260621.json").read_text(encoding="utf-8")
        )
        self.assertEqual(manifest["project_id"], "arxiv-daily-push")
        self.assertEqual(manifest["task_id"], "ADP-PHASE11-PRODUCTION-SCHEDULER-009")
        self.assertIn("MOD-ADP-018", manifest["model_delta"])

    def test_arxiv_daily_push_phase11_manifest_records_scheduled_execution(self) -> None:
        manifest = json.loads(
            (ROOT / "governance" / "run_manifests" / "ADP-PHASE11-SCHEDULED-EXECUTION-20260621.json").read_text(encoding="utf-8")
        )
        self.assertEqual(manifest["project_id"], "arxiv-daily-push")
        self.assertEqual(manifest["task_id"], "ADP-PHASE11-SCHEDULED-EXECUTION-010")
        self.assertIn("MOD-ADP-019", manifest["model_delta"])

    def test_arxiv_daily_push_phase11_manifest_records_daily_input_builder(self) -> None:
        manifest = json.loads(
            (ROOT / "governance" / "run_manifests" / "ADP-PHASE11-DAILY-INPUT-BUILDER-20260621.json").read_text(encoding="utf-8")
        )
        self.assertEqual(manifest["project_id"], "arxiv-daily-push")
        self.assertEqual(manifest["task_id"], "ADP-PHASE11-DAILY-INPUT-BUILDER-011")
        self.assertIn("MOD-ADP-020", manifest["model_delta"])

    def test_arxiv_daily_push_phase11_manifest_records_trial_ledger(self) -> None:
        manifest = json.loads(
            (ROOT / "governance" / "run_manifests" / "ADP-PHASE11-TRIAL-LEDGER-20260621.json").read_text(encoding="utf-8")
        )
        self.assertEqual(manifest["project_id"], "arxiv-daily-push")
        self.assertEqual(manifest["task_id"], "ADP-PHASE11-TRIAL-LEDGER-012")
        self.assertIn("MOD-ADP-021", manifest["model_delta"])

    def test_arxiv_daily_push_phase11_manifest_records_trial_ledger_state(self) -> None:
        manifest = json.loads(
            (ROOT / "governance" / "run_manifests" / "ADP-PHASE11-TRIAL-LEDGER-STATE-20260622.json").read_text(encoding="utf-8")
        )
        self.assertEqual(manifest["project_id"], "arxiv-daily-push")
        self.assertEqual(manifest["task_id"], "ADP-PHASE11-TRIAL-LEDGER-STATE-013")
        self.assertIn("MOD-ADP-022", manifest["model_delta"])

    def test_arxiv_daily_push_phase11_manifest_records_trial_ops_evidence(self) -> None:
        manifest = json.loads(
            (ROOT / "governance" / "run_manifests" / "ADP-PHASE11-TRIAL-OPS-EVIDENCE-20260622.json").read_text(encoding="utf-8")
        )
        self.assertEqual(manifest["project_id"], "arxiv-daily-push")
        self.assertEqual(manifest["task_id"], "ADP-PHASE11-TRIAL-OPS-EVIDENCE-014")
        self.assertIn("MOD-ADP-023", manifest["model_delta"])

    def test_arxiv_daily_push_phase11_manifest_records_trial_replay_evidence(self) -> None:
        manifest = json.loads(
            (ROOT / "governance" / "run_manifests" / "ADP-PHASE11-TRIAL-REPLAY-EVIDENCE-20260622.json").read_text(encoding="utf-8")
        )
        self.assertEqual(manifest["project_id"], "arxiv-daily-push")
        self.assertEqual(manifest["task_id"], "ADP-PHASE11-TRIAL-REPLAY-EVIDENCE-015")
        self.assertIn("MOD-ADP-024", manifest["model_delta"])

    def test_arxiv_daily_push_phase11_manifest_records_trial_recovery_evidence(self) -> None:
        manifest = json.loads(
            (ROOT / "governance" / "run_manifests" / "ADP-PHASE11-TRIAL-RECOVERY-EVIDENCE-20260622.json").read_text(encoding="utf-8")
        )
        self.assertEqual(manifest["project_id"], "arxiv-daily-push")
        self.assertEqual(manifest["task_id"], "ADP-PHASE11-TRIAL-RECOVERY-EVIDENCE-016")
        self.assertIn("MOD-ADP-025", manifest["model_delta"])

    def test_arxiv_daily_push_phase11_manifest_records_trial_resource_evidence(self) -> None:
        manifest = json.loads(
            (ROOT / "governance" / "run_manifests" / "ADP-PHASE11-TRIAL-RESOURCE-EVIDENCE-20260622.json").read_text(encoding="utf-8")
        )
        self.assertEqual(manifest["project_id"], "arxiv-daily-push")
        self.assertEqual(manifest["task_id"], "ADP-PHASE11-TRIAL-RESOURCE-EVIDENCE-017")
        self.assertIn("MOD-ADP-026", manifest["model_delta"])

    def test_arxiv_daily_push_phase11_manifest_records_trial_start_gate(self) -> None:
        manifest = json.loads(
            (ROOT / "governance" / "run_manifests" / "ADP-PHASE11-TRIAL-START-GATE-20260622.json").read_text(encoding="utf-8")
        )
        self.assertEqual(manifest["project_id"], "arxiv-daily-push")
        self.assertEqual(manifest["task_id"], "ADP-PHASE11-TRIAL-START-GATE-018")
        self.assertIn("MOD-ADP-027", manifest["model_delta"])

    def test_arxiv_daily_push_phase11_manifest_records_trial_start_workflow(self) -> None:
        manifest = json.loads(
            (ROOT / "governance" / "run_manifests" / "ADP-PHASE11-TRIAL-START-WORKFLOW-20260622.json").read_text(encoding="utf-8")
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
            ).read_text(encoding="utf-8")
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
            ).read_text(encoding="utf-8")
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
        self.assertIn("contents: read", trial_start_workflow)
        self.assertIn("contents: read", scheduled_workflow)
        self.assertNotIn("contents: write", trial_start_workflow)
        self.assertNotIn("contents: write", scheduled_workflow)
        self.assertTrue(any("Production launch remains blocked" in risk for risk in manifest["risks"]))
        self.assertNotIn("draft and unmerged", " ".join(manifest["risks"]))

    def test_arxiv_daily_push_phase11_manifest_records_production_trial_start_precheck(self) -> None:
        manifest = json.loads(
            (
                ROOT
                / "governance"
                / "run_manifests"
                / "ADP-PHASE11-PRODUCTION-TRIAL-START-PRECHECK-20260622.json"
            ).read_text(encoding="utf-8")
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
            ).read_text(encoding="utf-8")
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
            ).read_text(encoding="utf-8")
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
            ).read_text(encoding="utf-8")
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
            ).read_text(encoding="utf-8")
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
            ).read_text(encoding="utf-8")
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
            ).read_text(encoding="utf-8")
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
            ).read_text(encoding="utf-8")
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
            ).read_text(encoding="utf-8")
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
            ).read_text(encoding="utf-8")
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
            ).read_text(encoding="utf-8")
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
            ).read_text(encoding="utf-8")
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
            ).read_text(encoding="utf-8")
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
            ).read_text(encoding="utf-8")
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
            ).read_text(encoding="utf-8")
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
            ).read_text(encoding="utf-8")
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
            ).read_text(encoding="utf-8")
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
            ).read_text(encoding="utf-8")
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
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(manifest["project_id"], "arxiv-daily-push")
        self.assertEqual(manifest["task_id"], "GOV-SEMANTIC-ADP-001")
        self.assertEqual(manifest["coverage_status"], "machine_verified")
        self.assertEqual(manifest["semantic_parameters_checked"], 152)
        self.assertEqual(manifest["human_review_required_parameters"], 0)
        self.assertEqual(manifest["semantic_formulas_checked"], 31)
        self.assertEqual(manifest["human_review_required_formulas"], 0)

    def test_adp_v7_1_root_lock_hashes_stage_gates_and_aliases_are_machine_checkable(self) -> None:
        validator = load_validator_module()
        v7_root = ROOT / "arxiv-daily-push" / "docs" / "pursuing_goal" / "v7_1"
        lock = validator.load_yaml(v7_root / "V7_1_ROOT_LOCK.yaml")
        contract_hash = (v7_root / "CONTRACT_HASH.txt").read_text(encoding="utf-8").strip()

        product_contract = v7_root / "machine_readable" / "product_contract_v7.yaml"
        roadmap = v7_root / "ROADMAP" / "roadmap_v7.yaml"
        audit = v7_root / "machine_readable" / "audit_findings_v7_1.yaml"
        product_digest = validator.sha256_file(product_contract)
        roadmap_digest = validator.sha256_file(roadmap)
        audit_digest = validator.sha256_file(audit)

        self.assertEqual(lock["status"], "repository_locked_pending_pr_ci")
        self.assertEqual(lock["current_contract"]["contract_version"], "ADP-PRODUCT-CONTRACT-V7.1")
        self.assertEqual(lock["current_contract"]["contract_sha256"], product_digest)
        self.assertEqual(contract_hash, product_digest)
        self.assertEqual(lock["current_contract"]["roadmap_version"], "ADP-ROADMAP-V7.1")
        self.assertEqual(lock["current_contract"]["roadmap_sha256"], roadmap_digest)
        self.assertEqual(lock["current_contract"]["audit_version"], "ADP-PARALLEL-AUDIT-V7.1")
        self.assertEqual(lock["current_contract"]["audit_findings_sha256"], audit_digest)
        self.assertEqual(lock["stage1_boundary"]["accepted_gate"], "ARXIV_PRODUCTION_ACCEPTED")
        self.assertTrue(lock["stage1_boundary"]["must_not_regress"])
        self.assertEqual(lock["stage2_boundary"]["stop_gate"], "INTEGRATED_PRODUCTION_ACCEPTED -> DAILY_OPERATION")
        self.assertFalse(lock["stage2_boundary"]["production_accepted"])
        self.assertEqual(lock["stage2_boundary"]["current_task_id"], "S2PCT01")
        self.assertEqual(lock["stage2_boundary"]["current_shadow_source_task"], "S2PBT01")
        self.assertEqual(lock["stage2_boundary"]["final_task"], "S2PMT07")
        self.assertEqual(lock["stage2_boundary"]["legacy_aliases"]["S2PCT01"], "S2P2T01")
        self.assertEqual(lock["stage2_boundary"]["legacy_aliases"]["S2PBT01"], "S2P1T01")
        self.assertIn("P0 findings are zero", lock["production_forbidden_until"])
        self.assertIn("P1 findings are zero", lock["production_forbidden_until"])

    def test_adp_v7_1_hashing_normalizes_windows_line_endings(self) -> None:
        validator = load_validator_module()
        tmp = Path(tempfile.mkdtemp(prefix="codex-adp-v71-hash-"))
        try:
            sample = tmp / "sample.yaml"
            sample.write_bytes(b"contract_version: ADP-PRODUCT-CONTRACT-V7.1\r\nstatus: locked\r\n")
            expected = hashlib.sha256(
                b"contract_version: ADP-PRODUCT-CONTRACT-V7.1\nstatus: locked\n"
            ).hexdigest()
            self.assertEqual(validator.sha256_file(sample), expected)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_adp_v7_1_root_lock_is_enforced_by_project_validator_and_human_entries(self) -> None:
        result = run_validator("--project", "arxiv-daily-push")
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("errors: 0", result.stdout)

        for relative in ("功能清单", "开发记录", "模型参数文件"):
            text = (ROOT / "arxiv-daily-push" / relative).read_text(encoding="utf-8")
            self.assertIn("ADP-PRODUCT-CONTRACT-V7.1", text)
            self.assertIn("V7_1_ROOT_LOCK.yaml", text)
            self.assertIn("ARXIV_PRODUCTION_ACCEPTED", text)
            self.assertIn("S2PCT01", text)
            self.assertIn("S2P2T01", text)
            self.assertIn("S2PBT01", text)
            self.assertIn("S2PMT07", text)

        status = (ROOT / "arxiv-daily-push" / "docs" / "governance" / "STATUS.md").read_text(encoding="utf-8")
        self.assertIn("ARXIV_PRODUCTION_ACCEPTED_MAINTAINED", status)
        self.assertIn("INTEGRATED_PRODUCTION_ACCEPTED -> DAILY_OPERATION", status)
        self.assertIn("Stage 2 integrated accepted: `false`", status)

    def test_review9_information_quality_gate_reports_truth_without_pr_blocking_assumption(self) -> None:
        quality = load_information_quality_module()
        result = quality.run()
        self.assertIn(result["status"], {"PASS", "FAIL"}, result)
        self.assertIn("findings", result)
        codes = {item["code"] for item in result["findings"]}
        self.assertFalse(
            codes
            & {
                "HOOK_QUALITY",
                "CI_QUALITY",
                "CI_CHANGED_QUALITY",
                "CI_ALL_QUALITY",
                "CI_DRIFT",
                "CI_PORTFOLIO",
                "CI_MASKING",
            },
            result,
        )

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

    def test_review9_s6pat03_root_entry_points_only_to_human_files_and_standard(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        entry = readme.split("## Governance Entry", 1)[1].split("##", 1)[0]
        for required in ("docs/governance/STANDARD.md", "功能清单", "开发记录", "模型参数文件"):
            self.assertIn(required, entry)
        for forbidden in ("AGENTS.md", "governance/projects.yaml", "GOVERNANCE_DASHBOARD.md", "OWNER_PORTFOLIO.md"):
            self.assertNotIn(forbidden, entry)
        self.assertNotIn("source_snapshot_hash", readme)

    def test_review9_s6pat03_generated_readme_entry_matches_lean_contract(self) -> None:
        dashboard = load_dashboard_module()
        rendered = dashboard.render_readme(
            [{"project_id": "Example", "path": "Example"}],
            {
                "source_base_commit": "a" * 40,
                "source_tree_hash": "sha256:" + "b" * 64,
                "source_snapshot_hash": "sha256:" + "c" * 64,
            },
        )
        entry = rendered.split("## Governance Entry", 1)[1].split("##", 1)[0]
        for required in ("docs/governance/STANDARD.md", "功能清单", "开发记录", "模型参数文件"):
            self.assertIn(required, entry)
        for forbidden in ("governance/projects.yaml", "GOVERNANCE_DASHBOARD.md", "OWNER_PORTFOLIO.md"):
            self.assertNotIn(forbidden, entry)

    def test_other8_s2pat01_root_readme_uses_read_only_fast_gate(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        required = readme.split("## Required Checks", 1)[1].split("##", 1)[0]
        self.assertIn("lean_governance.py ci --changed-only --base-ref origin/main", required)
        self.assertIn("Write-mode generators are not part of the ordinary PR fast gate", required)
        self.assertIn("--write --changed-only --base-ref origin/main --root-artifact-dir", required)
        fast_gate = required.split("Write-mode generators", 1)[0]
        self.assertNotIn("generate_governance_dashboard.py --write", fast_gate)

        dashboard = load_dashboard_module()
        rendered = dashboard.render_readme(
            [{"project_id": "Example", "path": "Example"}],
            {
                "source_base_commit": "a" * 40,
                "source_tree_hash": "sha256:" + "b" * 64,
                "source_snapshot_hash": "sha256:" + "c" * 64,
            },
        )
        self.assertNotIn("source_snapshot_hash", rendered)
        rendered_required = rendered.split("## Required Checks", 1)[1].split("##", 1)[0]
        self.assertIn("lean_governance.py ci --changed-only --base-ref origin/main", rendered_required)
        self.assertNotIn("generate_governance_dashboard.py --write", rendered_required.split("Write-mode generators", 1)[0])

    def test_other8_s2pat02_target_readmes_use_chinese_human_entry_navigation(self) -> None:
        target_readmes = [
            ROOT / "Alpha" / "README.md",
            ROOT / "EVA_OS" / "README.md",
            ROOT / "FIFA" / "README.md",
            ROOT / "OpMe_System" / "README.md",
            ROOT / "OpenAIDatabase" / "README.md",
            ROOT / "PFI" / "大数据模拟器" / "README.md",
            ROOT / "Serenity-Alipay" / "README.md",
            ROOT / "whkmSalary" / "README.md",
        ]
        for readme_path in target_readmes:
            with self.subTest(readme=str(readme_path.relative_to(ROOT))):
                text = readme_path.read_text(encoding="utf-8")
                self.assertIn("中文人类入口", text)
                self.assertIn("docs/governance/", text)
                for human_entry in ("功能清单", "开发记录", "模型参数文件"):
                    self.assertIn(human_entry, text)
                for forbidden in ("compatibility index", "compatibility indexes", "兼容索引"):
                    self.assertNotIn(forbidden, text.lower())

    def test_other8_s2pat03_human_entry_quality_rejects_index_pages(self) -> None:
        validator = load_validator_module()
        with tempfile.TemporaryDirectory() as tmp:
            project_path = Path(tmp)
            for filename in ("功能清单", "开发记录", "模型参数文件"):
                (project_path / filename).write_text(
                    f"# {filename}\n\n详见 docs/governance/project.yaml\ncompatibility indexes only\n",
                    encoding="utf-8",
                )
            validation = validator.Validation()
            validator.check_human_entry_quality(validation, project_path, True, "ProjectA")
        messages = [issue.message for issue in validation.errors]
        self.assertTrue(any("not a compatibility index or link page" in message for message in messages))
        self.assertTrue(any("missing owner-readable token" in message for message in messages))

    def test_other8_s2pat03_current_human_entries_pass_quality_contract(self) -> None:
        validator = load_validator_module()
        config = validator.load_yaml(ROOT / "governance" / "projects.yaml")
        projects = [project for project in validator.as_list(config.get("projects")) if isinstance(project, dict)]
        self.assertEqual(len(projects), 10)
        for project in projects:
            with self.subTest(project=project.get("project_id")):
                validation = validator.Validation()
                project_path = ROOT / str(project.get("path") or "")
                validator.check_human_entry_quality(validation, project_path, True, validator.project_scope(project))
                self.assertFalse(validation.errors, [issue.message for issue in validation.errors])

    def test_other8_s2pbt01_target_roadmaps_are_explicit_product_kind(self) -> None:
        validator = load_validator_module()
        target_roadmaps = [
            ROOT / "Alpha" / "docs" / "governance" / "roadmap.yaml",
            ROOT / "EVA_OS" / "docs" / "governance" / "roadmap.yaml",
            ROOT / "FIFA" / "docs" / "governance" / "roadmap.yaml",
            ROOT / "OpMe_System" / "docs" / "governance" / "roadmap.yaml",
            ROOT / "OpenAIDatabase" / "docs" / "governance" / "roadmap.yaml",
            ROOT / "PFI" / "大数据模拟器" / "docs" / "governance" / "roadmap.yaml",
            ROOT / "Serenity-Alipay" / "docs" / "governance" / "roadmap.yaml",
            ROOT / "whkmSalary" / "docs" / "governance" / "roadmap.yaml",
        ]
        for path in target_roadmaps:
            with self.subTest(path=str(path.relative_to(ROOT))):
                roadmap = validator.load_yaml(path)
                self.assertEqual(roadmap["roadmap_kind"], "product")

    def test_other8_s2pbt01_validator_requires_product_kind_for_non_excluded_projects(self) -> None:
        validator = load_validator_module()
        missing = validator.Validation()
        validator.check_product_roadmap_kind(
            missing,
            {"project_id": "Alpha"},
            {"roadmap": {"schema_version": "codexproject.roadmap.v1"}},
            True,
            "Alpha",
        )
        self.assertTrue(any("roadmap_kind must be product" in issue.message for issue in missing.errors))

        excluded = validator.Validation()
        validator.check_product_roadmap_kind(
            excluded,
            {"project_id": "EEI"},
            {"roadmap": {"schema_version": "codexproject.roadmap.v1"}},
            True,
            "EEI",
        )
        self.assertFalse(excluded.errors, [issue.message for issue in excluded.errors])

    def test_other8_s2pbt01_renderer_rejects_portfolio_remediation_roadmap(self) -> None:
        cli = load_lean_governance_module()
        with self.assertRaisesRegex(ValueError, "roadmap_kind=product"):
            cli.render_development_record(
                {"project_id": "CodexProject", "version": "0.0.0", "fact_level": "PROPOSED"},
                {"roadmap_kind": "portfolio_remediation", "stages": []},
                [],
            )

    def test_other8_s2pbt01_product_development_records_do_not_embed_portfolio_roadmap(self) -> None:
        for project_path in [
            ROOT / "Alpha",
            ROOT / "EVA_OS",
            ROOT / "FIFA",
            ROOT / "OpMe_System",
            ROOT / "OpenAIDatabase",
            ROOT / "PFI" / "大数据模拟器",
            ROOT / "Serenity-Alipay",
            ROOT / "whkmSalary",
        ]:
            with self.subTest(project=str(project_path.relative_to(ROOT))):
                text = (project_path / "开发记录").read_text(encoding="utf-8")
                self.assertNotIn("portfolio_remediation", text)
                self.assertNotIn("CodexProject_Other8_Remediation_Roadmap", text)

    def test_other8_s2pbt02_renderer_derives_owner_fields_from_canonical_facts(self) -> None:
        cli = load_lean_governance_module()
        project = {
            "project_id": "ProjectA",
            "version": "0.1.0",
            "fact_level": "VERIFIED",
            "features": [],
            "evidence_refs": [{"evidence_id": "EVID-A", "kind": "test", "ref": "tests/a.py", "fact_level": "VERIFIED"}],
            "models": [
                {"model_id": "MOD-A", "name": "Active model", "status": "active", "fact_level": "VERIFIED"},
                {"model_id": "MOD-P", "name": "Planned model", "status": "planned", "fact_level": "PROPOSED"},
            ],
            "formulas": [
                {"formula_id": "FORM-A", "status": "active", "fact_level": "VERIFIED"},
                {"formula_id": "FORM-D", "status": "deprecated", "fact_level": "VERIFIED"},
            ],
            "parameters": [
                {"parameter_id": "PARAM-A", "symbol": "x", "name": "Active parameter", "status": "active", "value": 7, "source": "canonical", "fact_level": "VERIFIED"},
                {"parameter_id": "PARAM-P", "symbol": "y", "name": "Proposed parameter", "status": "proposed", "value": 9, "source": "proposal", "fact_level": "PROPOSED"},
            ],
        }
        roadmap = {
            "roadmap_kind": "product",
            "current_stage_id": "S1",
            "current_phase_id": "S1PA",
            "current_task_id": "S1PAT02",
            "next_gate_id": "S1PA-GATE",
            "stages": [
                {
                    "stage_id": "S1",
                    "name": "Stage One",
                    "person_goal": "Ship",
                    "status": "in_progress",
                    "stop_conditions": ["stop"],
                    "stop_gate": {
                        "gate_id": "S1-GATE",
                        "pass_criteria": ["stage pass"],
                        "evidence": ["EVID-STAGE"],
                        "failure_action": "blocked",
                    },
                    "phases": [
                        {
                            "phase_id": "S1PA",
                            "name": "Phase A",
                            "objective": "Do work",
                            "status": "in_progress",
                            "stop_conditions": ["phase stop"],
                            "stop_gate": {
                                "gate_id": "S1PA-GATE",
                                "pass_criteria": ["phase pass"],
                                "evidence": ["EVID-PHASE"],
                                "failure_action": "remain_in_phase",
                            },
                            "tasks": [
                                {
                                    "task_id": "S1PAT01",
                                    "name": "Done",
                                    "status": "completed",
                                    "estimated_hours": 1,
                                    "dependencies": ["none"],
                                    "acceptance_ids": ["ACC-A"],
                                    "test_commands": ["pytest done"],
                                    "test_results": ["pass"],
                                    "evidence_refs": ["EVID-DONE"],
                                    "risks": ["none"],
                                    "rollback": "revert done",
                                },
                                {
                                    "task_id": "S1PAT02",
                                    "name": "Blocked item",
                                    "status": "blocked",
                                    "estimated_hours": 3,
                                    "dependencies": ["S1PAT01"],
                                    "acceptance_ids": ["ACC-B"],
                                    "test_commands": ["pytest blocked"],
                                    "test_results": ["pending blocker"],
                                    "evidence_refs": ["EVID-BLOCKED"],
                                    "risks": ["blocked risk"],
                                    "rollback": "revert blocked",
                                },
                            ],
                        }
                    ],
                }
            ],
        }

        feature_list = cli.render_feature_list(project, roadmap)
        dev_record = cli.render_development_record(project, roadmap, [])
        model_params = cli.render_model_parameters(project, roadmap)

        for rendered in (feature_list, dev_record, model_params):
            self.assertIn("blockers: `S1PAT02 Blocked item (blocked)`", rendered)
            self.assertIn("next_unique_task: `S1PAT02 Blocked item (blocked)`", rendered)
            self.assertIn("roadmap_test_command_count: `2`", rendered)
            self.assertIn("roadmap_gate_count: `2`", rendered)
            self.assertNotIn("blockers: `NOT_APPLICABLE`", rendered)
            self.assertNotIn("next_unique_task: `NOT_APPLICABLE`", rendered)
        self.assertIn("roadmap_kind: `product`", dev_record)
        self.assertIn("stop_gate_pass_criteria: `stage pass`", dev_record)
        self.assertIn("stop_gate_evidence: `EVID-PHASE`", dev_record)
        self.assertIn("Task detail fields:", dev_record)
        self.assertIn("S1PAT02 test_commands: `pytest blocked`", dev_record)
        self.assertIn("S1PAT02 evidence_refs: `EVID-BLOCKED`", dev_record)
        self.assertIn("active_model_count: `1`", model_params)
        self.assertIn("active_formula_count: `1`", model_params)
        self.assertIn("active_parameter_count: `1`", model_params)

    def test_other8_s2pbt03_render_write_is_noop_and_supports_single_view(self) -> None:
        cli = load_lean_governance_module()
        with tempfile.TemporaryDirectory() as tmp:
            project_root = Path(tmp) / "ProjectA"
            governance_root = project_root / "docs" / "governance"
            governance_root.mkdir(parents=True)
            (governance_root / "project.yaml").write_text(
                "\n".join(
                    [
                        "schema_version: codexproject.project.v1",
                        "project_id: ProjectA",
                        "version: 0.1.0",
                        "fact_level: VERIFIED",
                        "features: []",
                        "models: []",
                        "formulas: []",
                        "parameters: []",
                        "evidence_refs: []",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            (governance_root / "roadmap.yaml").write_text(
                "\n".join(
                    [
                        "schema_version: codexproject.roadmap.v1",
                        "roadmap_kind: product",
                        "project_id: ProjectA",
                        "total_estimated_hours: 1",
                        "current_stage_id: S1",
                        "current_phase_id: S1PA",
                        "current_task_id: S1PAT01",
                        "next_gate_id: S1PA-GATE",
                        "stages:",
                        "  - stage_id: S1",
                        "    name: Stage One",
                        "    person_goal: Ship",
                        "    status: in_progress",
                        "    stop_conditions: [stop]",
                        "    stop_gate:",
                        "      gate_id: S1-GATE",
                        "      pass_criteria: [pass]",
                        "      evidence: [EVID-A]",
                        "      failure_action: blocked",
                        "    phases:",
                        "      - phase_id: S1PA",
                        "        name: Phase A",
                        "        objective: Do work",
                        "        status: in_progress",
                        "        stop_conditions: [stop]",
                        "        stop_gate:",
                        "          gate_id: S1PA-GATE",
                        "          pass_criteria: [pass]",
                        "          evidence: [EVID-A]",
                        "          failure_action: remain_in_phase",
                        "        tasks:",
                        "          - task_id: S1PAT01",
                        "            name: Current",
                        "            objective: Finish",
                        "            status: in_progress",
                        "            estimated_hours: 1",
                        "            dependencies: [none]",
                        "            acceptance_ids: [ACC-A]",
                        "            test_commands: [pytest]",
                        "            test_results: [pending]",
                        "            evidence_refs: [EVID-A]",
                        "            risks: [none]",
                        "            rollback: revert",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            (governance_root / "events.jsonl").write_text("", encoding="utf-8")

            first = cli.render_project_files(project_root, write=True, view="development-record")
            self.assertEqual(first["view"], "开发记录")
            self.assertEqual(first["updated_count"], 1)
            self.assertEqual(first["unchanged_count"], 0)
            self.assertTrue((project_root / "开发记录").exists())
            self.assertFalse((project_root / "功能清单").exists())
            self.assertFalse((project_root / "模型参数文件").exists())
            before = (project_root / "开发记录").read_text(encoding="utf-8")

            second = cli.render_project_files(project_root, write=True, view="development-record")
            after = (project_root / "开发记录").read_text(encoding="utf-8")
            self.assertEqual(before, after)
            self.assertEqual(second["updated_count"], 0)
            self.assertEqual(second["unchanged_count"], 1)

            checked = cli.check_render_project_files(project_root, view="development-record")
            self.assertEqual(checked["view"], "开发记录")
            self.assertEqual(checked["drift_count"], 0)

            with self.assertRaisesRegex(ValueError, "Unknown render view"):
                cli.render_project_files(project_root, write=False, view="unknown-view")


if __name__ == "__main__":
    unittest.main()
