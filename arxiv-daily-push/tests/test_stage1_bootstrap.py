from __future__ import annotations

import io
import json
import subprocess
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from arxiv_daily_push.cli import main
from arxiv_daily_push.stage1_bootstrap import (
    STAGE1_BOOTSTRAP_REQUIRED_SECRET_NAMES,
    build_stage1_bootstrap_report,
    validate_stage1_bootstrap_report,
)
from arxiv_daily_push.stage1_migration import build_migration_package
from arxiv_daily_push.storage import migrate_database


def github_env(tmp: Path) -> dict[str, str]:
    return {
        "GITHUB_ACTIONS": "true",
        "GITHUB_WORKFLOW": "arXiv Daily Push Stage 1 bootstrap",
        "GITHUB_RUN_ID": "123456",
        "GITHUB_SHA": "abc123",
        "RUNNER_OS": "Linux",
        "RUNNER_ARCH": "X64",
        "RUNNER_TEMP": str(tmp / "runner-temp"),
        "RUNNER_ENVIRONMENT": "github-hosted",
    }


def init_git_project(root: Path) -> None:
    subprocess.run(["git", "init"], cwd=root, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)


def prepare_project(root: Path) -> Path:
    (root / "config").mkdir(parents=True)
    (root / "VERSION").write_text("0.20.0\n", encoding="utf-8")
    (root / "config" / "owner_controls.yaml").write_text("project: arxiv-daily-push\n", encoding="utf-8")
    db_path = root / "adp.sqlite3"
    migrate_database(db_path)
    return db_path


def build_package(tmp_path: Path, root: Path, db_path: Path) -> dict:
    return build_migration_package(
        project_root=root,
        output_dir=tmp_path / "package",
        db_path=db_path,
        generated_at="2026-07-01T05:50:00+10:00",
        required_paths=["VERSION", "config/owner_controls.yaml"],
    )


def write_workflow(root: Path, *, runs_on: str = "ubuntu-latest") -> Path:
    workflow = root / ".github" / "workflows" / "arxiv-daily-push-stage1-bootstrap.yml"
    workflow.parent.mkdir(parents=True)
    workflow.write_text(
        "\n".join(
            [
                "name: arXiv Daily Push Stage 1 bootstrap",
                "on: workflow_dispatch",
                "jobs:",
                "  bootstrap:",
                f"    runs-on: {runs_on}",
                "    steps:",
                "      - run: python -m arxiv_daily_push post-migration-bootstrap",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return workflow


class FakeResponse:
    status = 200

    def __enter__(self) -> FakeResponse:
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        return None

    def read(self, size: int) -> bytes:
        return b"<"[:size]


class Stage1BootstrapTests(unittest.TestCase):
    def test_bootstrap_passes_on_github_hosted_runner_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            root = tmp_path / "project"
            root.mkdir()
            init_git_project(root)
            db_path = prepare_project(root)
            package = build_package(tmp_path, root, db_path)
            workflow = write_workflow(root)
            with patch("arxiv_daily_push.stage1_bootstrap._ssl_check", return_value={"passed": True, "openssl_version": "test", "ca_cert_count": 1}):
                report = build_stage1_bootstrap_report(
                    project_root=root,
                    migration_manifest=package["package_manifest_path"],
                    state_dir=tmp_path / "state",
                    db_path=db_path,
                    generated_at="2026-07-01T06:00:00+10:00",
                    workflow_path=workflow,
                    require_github_actions=True,
                    environment=github_env(tmp_path),
                )

            self.assertEqual(report["status"], "pass")
            self.assertTrue(report["bootstrap_ready"])
            self.assertTrue(report["cloud_runner_verified"])
            self.assertFalse(report["production_side_effects_enabled"])
            self.assertFalse(report["real_smtp_sent"])
            self.assertFalse(report["real_release_uploaded"])
            self.assertFalse(report["video_generated"])
            self.assertFalse(report["large_replay_executed"])
            self.assertEqual(tuple(report["required_secret_names"]), STAGE1_BOOTSTRAP_REQUIRED_SECRET_NAMES)
            self.assertFalse(any(item["value_recorded"] for item in report["secret_name_report"]))
            self.assertFalse(validate_stage1_bootstrap_report(report))

    def test_network_probe_retries_transient_timeout(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            root = tmp_path / "project"
            root.mkdir()
            init_git_project(root)
            db_path = prepare_project(root)
            package = build_package(tmp_path, root, db_path)
            workflow = write_workflow(root)
            with (
                patch("arxiv_daily_push.stage1_bootstrap._ssl_check", return_value={"passed": True, "openssl_version": "test", "ca_cert_count": 1}),
                patch("arxiv_daily_push.stage1_bootstrap.urllib.request.urlopen", side_effect=[TimeoutError(), FakeResponse()]),
            ):
                report = build_stage1_bootstrap_report(
                    project_root=root,
                    migration_manifest=package["package_manifest_path"],
                    state_dir=tmp_path / "state",
                    db_path=db_path,
                    generated_at="2026-07-01T06:00:00+10:00",
                    workflow_path=workflow,
                    require_github_actions=True,
                    require_network_probe=True,
                    network_timeout_seconds=1,
                    network_max_attempts=2,
                    environment=github_env(tmp_path),
                )

            self.assertEqual(report["status"], "pass")
            self.assertEqual(report["network_probe"]["attempt_count"], 2)
            self.assertEqual(report["network_probe"]["attempts"][0]["error"], "TimeoutError")
            self.assertTrue(report["network_probe"]["attempts"][1]["passed"])
            self.assertFalse(validate_stage1_bootstrap_report(report))

    def test_network_probe_fails_closed_after_retry_exhaustion(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            root = tmp_path / "project"
            root.mkdir()
            init_git_project(root)
            db_path = prepare_project(root)
            package = build_package(tmp_path, root, db_path)
            workflow = write_workflow(root)
            with (
                patch("arxiv_daily_push.stage1_bootstrap._ssl_check", return_value={"passed": True, "openssl_version": "test", "ca_cert_count": 1}),
                patch("arxiv_daily_push.stage1_bootstrap.urllib.request.urlopen", side_effect=TimeoutError()),
            ):
                report = build_stage1_bootstrap_report(
                    project_root=root,
                    migration_manifest=package["package_manifest_path"],
                    state_dir=tmp_path / "state",
                    db_path=db_path,
                    generated_at="2026-07-01T06:00:00+10:00",
                    workflow_path=workflow,
                    require_github_actions=True,
                    require_network_probe=True,
                    network_timeout_seconds=1,
                    network_max_attempts=2,
                    environment=github_env(tmp_path),
                )

            self.assertEqual(report["status"], "blocked")
            self.assertIn("network probe did not pass", report["blocking_reasons"])
            self.assertEqual(report["network_probe"]["attempt_count"], 2)
            self.assertEqual(report["network_probe"]["error"], "TimeoutError")
            self.assertFalse(report["real_smtp_sent"])

    def test_bootstrap_blocks_enabled_production_flag(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            root = tmp_path / "project"
            root.mkdir()
            init_git_project(root)
            db_path = prepare_project(root)
            package = build_package(tmp_path, root, db_path)
            workflow = write_workflow(root)
            env = {**github_env(tmp_path), "ADP_PRODUCTION_ENABLED": "true"}
            report = build_stage1_bootstrap_report(
                project_root=root,
                migration_manifest=package["package_manifest_path"],
                state_dir=tmp_path / "state",
                db_path=db_path,
                generated_at="2026-07-01T06:00:00+10:00",
                workflow_path=workflow,
                require_github_actions=True,
                environment=env,
            )

            self.assertEqual(report["status"], "blocked")
            self.assertIn("ADP_PRODUCTION_ENABLED must not be true during S1-10", report["blocking_reasons"])

    def test_bootstrap_blocks_self_hosted_workflow(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            root = tmp_path / "project"
            root.mkdir()
            init_git_project(root)
            db_path = prepare_project(root)
            package = build_package(tmp_path, root, db_path)
            workflow = write_workflow(root, runs_on="[self-hosted, arxiv-daily-push]")
            with patch("arxiv_daily_push.stage1_bootstrap._ssl_check", return_value={"passed": True, "openssl_version": "test", "ca_cert_count": 1}):
                report = build_stage1_bootstrap_report(
                    project_root=root,
                    migration_manifest=package["package_manifest_path"],
                    state_dir=tmp_path / "state",
                    db_path=db_path,
                    generated_at="2026-07-01T06:00:00+10:00",
                    workflow_path=workflow,
                    require_github_actions=True,
                    environment=github_env(tmp_path),
                )

            self.assertEqual(report["status"], "blocked")
            self.assertIn("workflow runner contract check did not pass", report["blocking_reasons"])

    def test_bootstrap_blocks_tampered_migration_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            root = tmp_path / "project"
            root.mkdir()
            init_git_project(root)
            db_path = prepare_project(root)
            package = build_package(tmp_path, root, db_path)
            restore_drill = Path(package["output_dir"]) / "RESTORE_DRILL.md"
            restore_drill.write_text(restore_drill.read_text(encoding="utf-8") + "\ntampered\n", encoding="utf-8")
            workflow = write_workflow(root)
            report = build_stage1_bootstrap_report(
                project_root=root,
                migration_manifest=package["package_manifest_path"],
                state_dir=tmp_path / "state",
                db_path=db_path,
                generated_at="2026-07-01T06:00:00+10:00",
                workflow_path=workflow,
                require_github_actions=True,
                environment=github_env(tmp_path),
            )

            self.assertEqual(report["status"], "blocked")
            self.assertIn("migration package verification did not pass", report["blocking_reasons"])
            self.assertEqual(report["migration_verify_report"]["status"], "blocked")

    def test_validation_blocks_forged_side_effect_claim(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            root = tmp_path / "project"
            root.mkdir()
            init_git_project(root)
            db_path = prepare_project(root)
            package = build_package(tmp_path, root, db_path)
            workflow = write_workflow(root)
            report = build_stage1_bootstrap_report(
                project_root=root,
                migration_manifest=package["package_manifest_path"],
                state_dir=tmp_path / "state",
                db_path=db_path,
                generated_at="2026-07-01T06:00:00+10:00",
                workflow_path=workflow,
                require_github_actions=True,
                environment=github_env(tmp_path),
            )
            forged = {**report, "real_smtp_sent": True}

            self.assertIn("real_smtp_sent must be false", validate_stage1_bootstrap_report(forged))

    def test_cli_post_migration_bootstrap(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            root = tmp_path / "project"
            root.mkdir()
            init_git_project(root)
            db_path = prepare_project(root)
            package = build_package(tmp_path, root, db_path)
            workflow = write_workflow(root)
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                result = main(
                    [
                        "post-migration-bootstrap",
                        "--project-root",
                        str(root),
                        "--migration-manifest",
                        package["package_manifest_path"],
                        "--state-dir",
                        str(tmp_path / "state"),
                        "--db",
                        str(db_path),
                        "--generated-at",
                        "2026-07-01T06:00:00+10:00",
                        "--workflow-path",
                        str(workflow),
                        "--require-github-actions",
                        "--json",
                    ]
                )

            self.assertEqual(result, 2)
            report = json.loads(buffer.getvalue())
            self.assertIn("GitHub-hosted cloud runner evidence is required", report["blocking_reasons"])


if __name__ == "__main__":
    unittest.main()
