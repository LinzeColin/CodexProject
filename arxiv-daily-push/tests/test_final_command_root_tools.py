from __future__ import annotations

import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[2]
DAILY_OPERATION_AUTHORIZATION_ARTIFACT = (
    "FINAL_ACCEPTANCE_BUNDLE/daily_operation_persistent_enablement_authorization.json"
)
DAILY_OPERATION_RUNTIME_FORBIDDEN_FLAGS = (
    "daily_operation_enabled",
    "real_smtp_sent",
    "real_smtp_send_enabled",
    "scheduler_enabled",
    "scheduler_install_enabled",
    "release_uploaded",
    "release_packaging_enabled",
    "production_restore_enabled",
    "production_restore_executed",
    "public_schema_changed",
    "db_migration_executed",
    "production_queue_mutated",
    "source_adapter_changed",
    "ranking_algorithm_changed",
    "current_pointer_changed",
    "v7_1_baseline_changed",
    "v7_2_contract_files_changed",
)


def load_enablement_preflight_tool():
    spec = importlib.util.spec_from_file_location(
        "verify_daily_operation_enablement_preflight",
        REPO_ROOT / "tools" / "verify_daily_operation_enablement_preflight.py",
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load verify_daily_operation_enablement_preflight.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FinalCommandRootToolTests(unittest.TestCase):
    def _env(self) -> dict[str, str]:
        return {
            **os.environ,
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONPATH": str(REPO_ROOT / "arxiv-daily-push" / "src"),
        }

    def _temp_root_with_invalid_persistent_authorization(self) -> tuple[tempfile.TemporaryDirectory[str], Path]:
        temp = tempfile.TemporaryDirectory()
        temp_root = Path(temp.name)
        for dirname in ("arxiv-daily-push", "governance", "tools"):
            (temp_root / dirname).symlink_to(REPO_ROOT / dirname, target_is_directory=True)
        shutil.copytree(REPO_ROOT / "FINAL_ACCEPTANCE_BUNDLE", temp_root / "FINAL_ACCEPTANCE_BUNDLE")
        artifact = {
            "schema_version": "adp.daily_operation_persistent_enablement_authorization.v1",
            "contract_id": "ADP-PRODUCT-CONTRACT-V7.2",
            "task_id": "S2PMT07-DAILY-OPERATION-PERSISTENT-ENABLEMENT-AUTHORIZATION",
            "decision": "authorize_persistent_daily_operation_enablement",
            "template_only": False,
            "explicit_persistent_daily_operation_authorization": True,
            "generated_at": "REPLACE_WITH_OWNER_AUTHORIZATION_TIMESTAMP",
            "authorization_scope": "persistent_daily_operation_enablement",
            "authorized_by": "owner",
            "authorization_text": "REPLACE_WITH_EXPLICIT_OWNER_AUTHORIZATION_TEXT",
            "owner_decision_ref": "FINAL_ACCEPTANCE_BUNDLE/obsolete_owner_decision.json",
            "readiness_gate_ref": "FINAL_ACCEPTANCE_BUNDLE/obsolete_gate.json",
            "request_artifact_ref": "FINAL_ACCEPTANCE_BUNDLE/obsolete_request.json",
            **{flag: False for flag in DAILY_OPERATION_RUNTIME_FORBIDDEN_FLAGS},
        }
        artifact_path = temp_root / DAILY_OPERATION_AUTHORIZATION_ARTIFACT
        artifact_path.write_text(json.dumps(artifact, ensure_ascii=False, indent=2), encoding="utf-8")
        self.assertFalse((REPO_ROOT / DAILY_OPERATION_AUTHORIZATION_ARTIFACT).exists())
        return temp, temp_root

    def _temp_root_with_failed_authorization_prerequisites(
        self,
    ) -> tuple[tempfile.TemporaryDirectory[str], Path]:
        temp = tempfile.TemporaryDirectory()
        temp_root = Path(temp.name)
        for dirname in ("arxiv-daily-push", "tools"):
            (temp_root / dirname).symlink_to(REPO_ROOT / dirname, target_is_directory=True)
        shutil.copytree(REPO_ROOT / "FINAL_ACCEPTANCE_BUNDLE", temp_root / "FINAL_ACCEPTANCE_BUNDLE")
        template = json.loads(
            (
                REPO_ROOT
                / "FINAL_ACCEPTANCE_BUNDLE/templates/daily_operation_persistent_enablement_authorization.template.json"
            ).read_text(encoding="utf-8")
        )
        template.update(
            {
                "generated_at": "2026-07-10T10:25:00+10:00",
                "template_only": False,
                "explicit_persistent_daily_operation_authorization": True,
                "authorization_text": "Owner explicitly authorizes persistent DAILY_OPERATION for this fixture.",
            }
        )
        artifact_path = temp_root / DAILY_OPERATION_AUTHORIZATION_ARTIFACT
        artifact_path.write_text(json.dumps(template, ensure_ascii=False, indent=2), encoding="utf-8")
        controlled_path = (
            temp_root
            / "governance/run_manifests/ADP-S2PMT07-AUTHORIZED-CONTROLLED-REAL-RUN-ACCEPTANCE-20260701.json"
        )
        controlled_path.parent.mkdir(parents=True)
        controlled_path.write_text("{}\n", encoding="utf-8")
        self.assertFalse((REPO_ROOT / DAILY_OPERATION_AUTHORIZATION_ARTIFACT).exists())
        return temp, temp_root

    def test_validate_task_pack_root_tool_passes_without_production_side_effects(self) -> None:
        completed = subprocess.run(
            [sys.executable, "tools/validate_task_pack.py", "--root", "."],
            cwd=REPO_ROOT,
            env=self._env(),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout[-2000:])
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["status"], "PASS")
        self.assertEqual(payload["contract_id"], "ADP-PRODUCT-CONTRACT-V7.2")
        self.assertEqual(payload["task_id"], "S2PMT07")
        self.assertTrue(payload["integrated_production_accepted"])
        self.assertFalse(payload["daily_operation_enabled"])
        self.assertFalse(payload["real_smtp_send_enabled"])
        self.assertEqual(payload["portable_validation_status"], "pass")
        self.assertIn(
            payload["full_monorepo_governance_status"],
            {"pass", "blocked_sparse_external_projects"},
        )
        command_statuses = [result["status"] for result in payload["command_results"]]
        self.assertEqual(command_statuses[0], "pass")
        self.assertIn(command_statuses[1], {"pass", "blocked_sparse_external_projects"})
        if command_statuses[1] == "blocked_sparse_external_projects":
            self.assertTrue(payload["sparse_external_project_paths"])
            self.assertNotIn("arxiv-daily-push", payload["sparse_external_project_paths"])

    def test_verify_acceptance_bundle_root_tool_accepts_final_command_prerequisites(self) -> None:
        completed = subprocess.run(
            [sys.executable, "tools/verify_acceptance_bundle.py", "--require-zero", "P0", "P1"],
            cwd=REPO_ROOT,
            env=self._env(),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout[-2000:])
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["status"], "PASS")
        self.assertEqual(payload["required_zero"], ["P0", "P1"])
        self.assertEqual(payload["missing_required_zero"], [])
        self.assertTrue(payload["zero_checks"]["P0"])
        self.assertTrue(payload["zero_checks"]["P1"])
        self.assertEqual(payload["bundle_status"], "pass")
        self.assertTrue(payload["bundle_complete"])
        self.assertFalse(payload["final_command_prerequisite_ready"])
        self.assertIsNone(payload["next_required_step"])
        self.assertIsNone(payload["next_executable_task"])
        self.assertEqual(payload["s2plt04_completion_report_status"], "pass")
        self.assertEqual(payload["blocking_reasons"], [])
        self.assertFalse(payload["daily_operation_authorization_ready"])
        self.assertEqual(
            payload["daily_operation_blocking_reasons"],
            ["persistent_daily_operation_authorization_missing"],
        )
        self.assertEqual(
            payload["daily_operation_next_required_step"],
            "OBTAIN_EXPLICIT_OWNER_PERSISTENT_DAILY_OPERATION_AUTHORIZATION",
        )
        self.assertEqual(
            payload["daily_operation_next_executable_task"],
            "S2PMT07-DAILY-OPERATION-PERSISTENT-ENABLEMENT-AUTHORIZATION",
        )
        self.assertEqual(
            payload["daily_operation_persistent_authorization_artifact"],
            "FINAL_ACCEPTANCE_BUNDLE/daily_operation_persistent_enablement_authorization.json",
        )
        self.assertEqual(
            payload["daily_operation_gate_artifact"],
            "FINAL_ACCEPTANCE_BUNDLE/daily_operation_persistent_enablement_authorization_gate.json",
        )
        self.assertTrue(payload["integrated_production_accepted"])
        self.assertFalse(payload["daily_operation_enabled"])
        self.assertFalse(payload["real_smtp_send_enabled"])

    def test_verify_daily_operation_readiness_root_tool_fails_closed_without_authorization(self) -> None:
        completed = subprocess.run(
            [sys.executable, "tools/verify_daily_operation_readiness.py"],
            cwd=REPO_ROOT,
            env=self._env(),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

        self.assertEqual(completed.returncode, 2, completed.stderr + completed.stdout[-2000:])
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["status"], "FAIL")
        self.assertIn("repo_root", payload)
        self.assertIn("required_cwd", payload)
        self.assertIn("authorization_artifact_exists", payload)
        self.assertEqual(payload["repo_root"], str(REPO_ROOT))
        self.assertEqual(payload["required_cwd"], "CodexProject repository root")
        self.assertTrue(payload["repo_root_valid"])
        self.assertEqual(payload["root_validation_errors"], [])
        self.assertEqual(payload["required_paths_missing"], [])
        self.assertFalse(payload["authorization_artifact_exists"])
        self.assertFalse(payload["daily_operation_ready"])
        self.assertFalse(payload["persistent_daily_operation_authorized"])
        self.assertFalse(payload["daily_operation_enabled"])
        self.assertFalse(payload["real_smtp_send_enabled"])
        self.assertFalse(payload["scheduler_install_enabled"])
        self.assertEqual(
            payload["blocking_reasons"],
            ["persistent_daily_operation_authorization_missing"],
        )
        self.assertEqual(
            payload["next_required_step"],
            "OBTAIN_EXPLICIT_OWNER_PERSISTENT_DAILY_OPERATION_AUTHORIZATION",
        )
        self.assertEqual(
            payload["authorization_artifact"],
            "FINAL_ACCEPTANCE_BUNDLE/daily_operation_persistent_enablement_authorization.json",
        )
        self.assertEqual(payload["validation_errors"], [])

    def test_verify_daily_operation_readiness_root_tool_surfaces_invalid_authorization_artifact_errors(self) -> None:
        temp, temp_root = self._temp_root_with_invalid_persistent_authorization()
        self.addCleanup(temp.cleanup)

        completed = subprocess.run(
            [
                sys.executable,
                "tools/verify_daily_operation_readiness.py",
                "--root",
                str(temp_root),
                "--generated-at",
                "2026-07-03T15:50:00+10:00",
            ],
            cwd=REPO_ROOT,
            env=self._env(),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

        self.assertEqual(completed.returncode, 2, completed.stderr + completed.stdout[-2000:])
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["status"], "FAIL")
        self.assertTrue(payload["repo_root_valid"])
        self.assertTrue(payload["authorization_artifact_exists"])
        self.assertEqual(payload["gate_status"], "blocked_persistent_daily_operation_authorization_invalid")
        self.assertEqual(payload["blocking_reasons"], ["persistent_authorization_artifact_valid_failed"])
        self.assertEqual(
            payload["next_required_step"],
            "REPAIR_PERSISTENT_DAILY_OPERATION_AUTHORIZATION_ARTIFACT",
        )
        self.assertFalse(payload["daily_operation_ready"])
        self.assertFalse(payload["persistent_daily_operation_authorized"])
        self.assertFalse(payload["daily_operation_enablement_allowed_by_this_artifact"])
        self.assertFalse(payload["runtime_enablement_detected"])
        self.assertEqual(payload["validation_errors"], [])
        artifact_errors = payload["authorization_artifact_validation_errors"]
        self.assertIn(
            "persistent daily operation authorization artifact generated_at must be a real timestamp",
            artifact_errors,
        )
        self.assertIn(
            "persistent daily operation authorization artifact authorization_text must be explicit owner evidence",
            artifact_errors,
        )
        self.assertIn("persistent daily operation authorization artifact owner_decision_ref is invalid", artifact_errors)
        self.assertIn("persistent daily operation authorization artifact readiness_gate_ref is invalid", artifact_errors)
        self.assertIn("persistent daily operation authorization artifact request_artifact_ref is invalid", artifact_errors)

    def test_verify_daily_operation_readiness_root_tool_blocks_failed_authorization_prerequisites(self) -> None:
        temp, temp_root = self._temp_root_with_failed_authorization_prerequisites()
        self.addCleanup(temp.cleanup)

        completed = subprocess.run(
            [
                sys.executable,
                "tools/verify_daily_operation_readiness.py",
                "--root",
                str(temp_root),
                "--generated-at",
                "2026-07-10T10:30:00+10:00",
            ],
            cwd=REPO_ROOT,
            env=self._env(),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

        self.assertEqual(completed.returncode, 2, completed.stderr + completed.stdout[-2000:])
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["status"], "FAIL")
        self.assertEqual(
            payload["gate_status"],
            "blocked_persistent_daily_operation_authorization_prerequisites_failed",
        )
        self.assertIn("controlled_real_run_acceptance_present_failed", payload["blocking_reasons"])
        self.assertFalse(payload["daily_operation_ready"])
        self.assertFalse(payload["persistent_daily_operation_authorized"])
        self.assertFalse(payload["daily_operation_enablement_allowed_by_this_artifact"])
        self.assertEqual(payload["authorization_artifact_validation_errors"], [])
        self.assertEqual(payload["validation_errors"], [])
        self.assertEqual(
            payload["next_required_step"],
            "REPAIR_PERSISTENT_DAILY_OPERATION_AUTHORIZATION_PREREQUISITES",
        )

    def test_verify_daily_operation_readiness_root_tool_fails_closed_for_project_subdir_root(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                "tools/verify_daily_operation_readiness.py",
                "--root",
                "arxiv-daily-push",
                "--generated-at",
                "2026-07-02T23:00:00+10:00",
            ],
            cwd=REPO_ROOT,
            env=self._env(),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

        self.assertEqual(completed.returncode, 2, completed.stderr + completed.stdout[-2000:])
        self.assertEqual(completed.stderr, "")
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["status"], "FAIL")
        self.assertEqual(payload["repo_root"], str(REPO_ROOT / "arxiv-daily-push"))
        self.assertEqual(payload["required_cwd"], "CodexProject repository root")
        self.assertFalse(payload["repo_root_valid"])
        self.assertIn("codexproject_repo_root_invalid", payload["root_validation_errors"])
        self.assertIn("codexproject_repo_root_invalid", payload["blocking_reasons"])
        self.assertIn("arxiv-daily-push/src", payload["required_paths_missing"])
        self.assertFalse(payload["authorization_artifact_exists"])
        self.assertFalse(payload["daily_operation_ready"])

    def test_verify_daily_operation_enablement_preflight_root_tool_fails_closed_without_authorization(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                "tools/verify_daily_operation_enablement_preflight.py",
                "--generated-at",
                "2026-07-02T19:40:00+10:00",
                "--open-pr-count",
                "0",
                "--adp-allow-smtp-send",
                "UNSET",
                "--launchagent-daily-disabled",
                "true",
                "--launchagent-health-disabled",
                "true",
                "--launchagent-watchdog-disabled",
                "true",
                "--background-adp-process-count",
                "0",
            ],
            cwd=REPO_ROOT,
            env=self._env(),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

        self.assertEqual(completed.returncode, 2, completed.stderr + completed.stdout[-2000:])
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["status"], "FAIL")
        self.assertIn("repo_root", payload)
        self.assertIn("required_cwd", payload)
        self.assertIn("authorization_artifact_exists", payload)
        self.assertEqual(payload["repo_root"], str(REPO_ROOT))
        self.assertEqual(payload["required_cwd"], "CodexProject repository root")
        self.assertTrue(payload["repo_root_valid"])
        self.assertEqual(payload["root_validation_errors"], [])
        self.assertEqual(payload["required_paths_missing"], [])
        self.assertFalse(payload["authorization_artifact_exists"])
        self.assertEqual(
            payload["scope"],
            "adp_s3_daily_operation_enablement_preflight_fail_closed_no_runtime_enablement",
        )
        self.assertFalse(payload["enablement_preflight_ready"])
        self.assertFalse(payload["daily_operation_ready"])
        self.assertFalse(payload["persistent_daily_operation_authorized"])
        self.assertFalse(payload["daily_operation_enabled"])
        self.assertFalse(payload["real_smtp_send_enabled"])
        self.assertFalse(payload["scheduler_install_enabled"])
        self.assertFalse(payload["release_packaging_enabled"])
        self.assertFalse(payload["production_restore_enabled"])
        self.assertFalse(payload["runtime_enablement_detected"])
        self.assertEqual(
            payload["blocking_reasons"],
            ["persistent_daily_operation_authorization_missing"],
        )
        self.assertEqual(payload["readiness_status"], "FAIL")
        self.assertFalse(payload["checks"]["daily_operation_readiness_passed"])
        self.assertTrue(payload["checks"]["open_pr_count_zero"])
        self.assertTrue(payload["checks"]["adp_allow_smtp_send_false_like"])
        self.assertTrue(payload["checks"]["launchagents_disabled"])
        self.assertTrue(payload["checks"]["background_adp_process_count_zero"])
        self.assertEqual(
            payload["launchagent_disabled_states"],
            {
                "com.linzezhang.adp.daily": True,
                "com.linzezhang.adp.health": True,
                "com.linzezhang.adp.watchdog": True,
            },
        )
        self.assertEqual(payload["background_adp_process_count"], 0)
        self.assertEqual(
            payload["authorization_artifact"],
            "FINAL_ACCEPTANCE_BUNDLE/daily_operation_persistent_enablement_authorization.json",
        )

    def test_verify_daily_operation_enablement_preflight_root_tool_surfaces_invalid_authorization_artifact_errors(
        self,
    ) -> None:
        temp, temp_root = self._temp_root_with_invalid_persistent_authorization()
        self.addCleanup(temp.cleanup)

        completed = subprocess.run(
            [
                sys.executable,
                "tools/verify_daily_operation_enablement_preflight.py",
                "--root",
                str(temp_root),
                "--generated-at",
                "2026-07-03T15:55:00+10:00",
                "--open-pr-count",
                "0",
                "--adp-allow-smtp-send",
                "UNSET",
                "--launchagent-daily-disabled",
                "true",
                "--launchagent-health-disabled",
                "true",
                "--launchagent-watchdog-disabled",
                "true",
                "--background-adp-process-count",
                "0",
            ],
            cwd=REPO_ROOT,
            env=self._env(),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

        self.assertEqual(completed.returncode, 2, completed.stderr + completed.stdout[-2000:])
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["status"], "FAIL")
        self.assertTrue(payload["repo_root_valid"])
        self.assertTrue(payload["authorization_artifact_exists"])
        self.assertFalse(payload["enablement_preflight_ready"])
        self.assertEqual(payload["readiness_status"], "FAIL")
        self.assertFalse(payload["daily_operation_ready"])
        self.assertFalse(payload["persistent_daily_operation_authorized"])
        self.assertFalse(payload["runtime_enablement_detected"])
        self.assertEqual(payload["blocking_reasons"], ["persistent_authorization_artifact_valid_failed"])
        self.assertEqual(
            payload["next_required_step"],
            "REPAIR_PERSISTENT_DAILY_OPERATION_AUTHORIZATION_ARTIFACT",
        )
        artifact_errors = payload["authorization_artifact_validation_errors"]
        self.assertIn(
            "persistent daily operation authorization artifact generated_at must be a real timestamp",
            artifact_errors,
        )
        self.assertIn(
            "persistent daily operation authorization artifact authorization_text must be explicit owner evidence",
            artifact_errors,
        )
        self.assertIn("persistent daily operation authorization artifact owner_decision_ref is invalid", artifact_errors)
        self.assertIn("persistent daily operation authorization artifact readiness_gate_ref is invalid", artifact_errors)
        self.assertIn("persistent daily operation authorization artifact request_artifact_ref is invalid", artifact_errors)

    def test_verify_daily_operation_enablement_preflight_root_tool_blocks_failed_authorization_prerequisites(
        self,
    ) -> None:
        temp, temp_root = self._temp_root_with_failed_authorization_prerequisites()
        self.addCleanup(temp.cleanup)

        completed = subprocess.run(
            [
                sys.executable,
                "tools/verify_daily_operation_enablement_preflight.py",
                "--root",
                str(temp_root),
                "--generated-at",
                "2026-07-10T10:35:00+10:00",
                "--open-pr-count",
                "0",
                "--adp-allow-smtp-send",
                "UNSET",
                "--launchagent-daily-disabled",
                "true",
                "--launchagent-health-disabled",
                "true",
                "--launchagent-watchdog-disabled",
                "true",
                "--background-adp-process-count",
                "0",
            ],
            cwd=REPO_ROOT,
            env=self._env(),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

        self.assertEqual(completed.returncode, 2, completed.stderr + completed.stdout[-2000:])
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["status"], "FAIL")
        self.assertFalse(payload["enablement_preflight_ready"])
        self.assertEqual(payload["readiness_status"], "FAIL")
        self.assertIn("controlled_real_run_acceptance_present_failed", payload["blocking_reasons"])
        self.assertFalse(payload["daily_operation_ready"])
        self.assertFalse(payload["persistent_daily_operation_authorized"])
        self.assertFalse(payload["runtime_enablement_detected"])
        self.assertEqual(payload["authorization_artifact_validation_errors"], [])
        self.assertEqual(
            payload["next_required_step"],
            "REPAIR_PERSISTENT_DAILY_OPERATION_AUTHORIZATION_PREREQUISITES",
        )

    def test_verify_daily_operation_enablement_preflight_root_tool_fails_closed_for_project_subdir_root(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                "tools/verify_daily_operation_enablement_preflight.py",
                "--root",
                "arxiv-daily-push",
                "--generated-at",
                "2026-07-02T23:05:00+10:00",
                "--open-pr-count",
                "0",
                "--adp-allow-smtp-send",
                "UNSET",
                "--launchagent-daily-disabled",
                "true",
                "--launchagent-health-disabled",
                "true",
                "--launchagent-watchdog-disabled",
                "true",
                "--background-adp-process-count",
                "0",
            ],
            cwd=REPO_ROOT,
            env=self._env(),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

        self.assertEqual(completed.returncode, 2, completed.stderr + completed.stdout[-2000:])
        self.assertEqual(completed.stderr, "")
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["status"], "FAIL")
        self.assertEqual(payload["repo_root"], str(REPO_ROOT / "arxiv-daily-push"))
        self.assertEqual(payload["required_cwd"], "CodexProject repository root")
        self.assertFalse(payload["repo_root_valid"])
        self.assertIn("codexproject_repo_root_invalid", payload["root_validation_errors"])
        self.assertIn("codexproject_repo_root_invalid", payload["blocking_reasons"])
        self.assertIn("arxiv-daily-push/src", payload["required_paths_missing"])
        self.assertFalse(payload["authorization_artifact_exists"])
        self.assertFalse(payload["enablement_preflight_ready"])
        self.assertFalse(payload["daily_operation_ready"])
        self.assertFalse(payload["checks"]["daily_operation_readiness_passed"])
        self.assertTrue(payload["checks"]["open_pr_count_zero"])
        self.assertTrue(payload["checks"]["adp_allow_smtp_send_false_like"])
        self.assertTrue(payload["checks"]["launchagents_disabled"])
        self.assertTrue(payload["checks"]["background_adp_process_count_zero"])

    def test_verify_daily_operation_enablement_preflight_observes_runtime_by_default(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                "tools/verify_daily_operation_enablement_preflight.py",
                "--generated-at",
                "2026-07-02T20:10:00+10:00",
                "--open-pr-count",
                "0",
                "--adp-allow-smtp-send",
                "UNSET",
            ],
            cwd=REPO_ROOT,
            env=self._env(),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

        self.assertEqual(completed.returncode, 2, completed.stderr + completed.stdout[-2000:])
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["status"], "FAIL")
        self.assertEqual(payload["runtime_observation_mode"], "auto_observed")
        self.assertEqual(payload["runtime_observation_errors"], [])
        self.assertEqual(
            payload["launchagent_disabled_states"],
            {
                "com.linzezhang.adp.daily": True,
                "com.linzezhang.adp.health": True,
                "com.linzezhang.adp.watchdog": True,
            },
        )
        self.assertEqual(payload["background_adp_process_count"], 0)
        self.assertFalse(payload["enablement_preflight_ready"])
        self.assertEqual(
            payload["blocking_reasons"],
            ["persistent_daily_operation_authorization_missing"],
        )

    def test_verify_daily_operation_enablement_preflight_observes_open_pr_count_by_default(self) -> None:
        tool = load_enablement_preflight_tool()
        labels = {
            "com.linzezhang.adp.daily": True,
            "com.linzezhang.adp.health": True,
            "com.linzezhang.adp.watchdog": True,
        }
        stdout = io.StringIO()

        with (
            mock.patch.object(tool, "_observe_open_pr_count", return_value=(0, [])),
            mock.patch.object(tool, "observe_runtime_boundary", return_value=(labels, 0, [])),
            mock.patch("sys.stdout", stdout),
        ):
            exit_code = tool.main(
                [
                    "--root",
                    str(REPO_ROOT),
                    "--generated-at",
                    "2026-07-02T20:35:00+10:00",
                    "--adp-allow-smtp-send",
                    "UNSET",
                ]
            )

        self.assertEqual(exit_code, 2)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["open_pr_count"], 0)
        self.assertEqual(payload["open_pr_observation_mode"], "auto_observed")
        self.assertEqual(payload["open_pr_observation_errors"], [])
        self.assertTrue(payload["checks"]["open_pr_count_zero"])
        self.assertEqual(
            payload["blocking_reasons"],
            ["persistent_daily_operation_authorization_missing"],
        )

    def test_verify_daily_operation_enablement_preflight_open_pr_observation_timeout_is_fail_closed(self) -> None:
        tool = load_enablement_preflight_tool()

        with mock.patch.object(
            tool.subprocess,
            "run",
            side_effect=subprocess.TimeoutExpired(cmd=["/usr/bin/curl"], timeout=20),
        ):
            count, errors = tool._observe_open_pr_count()

        self.assertIsNone(count)
        self.assertEqual(errors, ["open_pr_count_observation_failed"])

    def test_verify_daily_operation_enablement_preflight_surfaces_observation_errors_as_blockers(self) -> None:
        tool = load_enablement_preflight_tool()
        labels = {
            "com.linzezhang.adp.daily": True,
            "com.linzezhang.adp.health": True,
            "com.linzezhang.adp.watchdog": True,
        }
        stdout = io.StringIO()

        with (
            mock.patch.object(
                tool,
                "_observe_open_pr_count",
                return_value=(None, ["open_pr_count_observation_failed"]),
            ),
            mock.patch.object(
                tool,
                "observe_runtime_boundary",
                return_value=(labels, None, ["background_process_observation_failed"]),
            ),
            mock.patch("sys.stdout", stdout),
        ):
            exit_code = tool.main(
                [
                    "--root",
                    str(REPO_ROOT),
                    "--generated-at",
                    "2026-07-02T21:05:00+10:00",
                    "--adp-allow-smtp-send",
                    "UNSET",
                ]
            )

        self.assertEqual(exit_code, 2)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["open_pr_observation_errors"], ["open_pr_count_observation_failed"])
        self.assertEqual(payload["runtime_observation_errors"], ["background_process_observation_failed"])
        self.assertIn("open_pr_count_not_zero_or_unknown", payload["blocking_reasons"])
        self.assertIn("open_pr_count_observation_failed", payload["blocking_reasons"])
        self.assertIn("background_adp_process_count_not_zero_or_unknown", payload["blocking_reasons"])
        self.assertIn("background_process_observation_failed", payload["blocking_reasons"])

    def test_verify_daily_operation_enablement_preflight_truthy_smtp_env_overrides_false_like_argument(self) -> None:
        tool = load_enablement_preflight_tool()
        labels = {
            "com.linzezhang.adp.daily": True,
            "com.linzezhang.adp.health": True,
            "com.linzezhang.adp.watchdog": True,
        }
        stdout = io.StringIO()

        with (
            mock.patch.object(tool, "_observe_open_pr_count", return_value=(0, [])),
            mock.patch.object(tool, "observe_runtime_boundary", return_value=(labels, 0, [])),
            mock.patch.dict(os.environ, {"ADP_ALLOW_SMTP_SEND": "true"}),
            mock.patch("sys.stdout", stdout),
        ):
            exit_code = tool.main(
                [
                    "--root",
                    str(REPO_ROOT),
                    "--generated-at",
                    "2026-07-02T20:50:00+10:00",
                    "--adp-allow-smtp-send",
                    "UNSET",
                ]
            )

        self.assertEqual(exit_code, 2)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["adp_allow_smtp_send_raw"], "UNSET")
        self.assertEqual(payload["adp_allow_smtp_send_environment_raw"], "true")
        self.assertFalse(payload["checks"]["adp_allow_smtp_send_false_like"])
        self.assertIn("adp_allow_smtp_send_truthy_or_unknown", payload["blocking_reasons"])


if __name__ == "__main__":
    unittest.main()
