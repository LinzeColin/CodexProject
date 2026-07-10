from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = REPO_ROOT / "scripts/cloudflare/validate_compatibility_envelope.py"
SCANNER = REPO_ROOT / "scripts/cloudflare/scan_public_dist.py"
STATIC_BUILDER = REPO_ROOT / "scripts/cloudflare/build_static_surface.mjs"
REQUIRED_PROJECTS = (
    "linze-home-hub",
    "nab",
    "eei",
    "openaidatabase",
    "pfi",
    "serenity-alipay",
)
REQUIRED_FIELDS = (
    "project_id",
    "source_repo",
    "source_path",
    "compatibility_level",
    "public_surface",
    "deploy_target",
    "worker_name",
    "preferred_domain",
    "actual_url",
    "status",
    "data_boundary",
    "private_data_allowed_in_dist",
    "build_command",
    "output_dir",
    "wrangler_config",
    "homehub_visibility",
    "required_for_this_task",
    "deployment_required",
    "deployment_result",
    "blockers",
    "acceptance",
    "rollback",
    "future_l3_extensions",
)


def project(project_id: str) -> dict[str, object]:
    item: dict[str, object] = {
        "project_id": project_id,
        "source_repo": "LinzeColin/CodexProject",
        "source_path": project_id,
        "compatibility_level": "L2",
        "public_surface": f"{project_id}/public",
        "deploy_target": "cloudflare_workers_static_assets",
        "worker_name": project_id,
        "preferred_domain": f"{project_id}.example.test",
        "actual_url": "",
        "status": "deploy_ready_auth_blocked",
        "data_boundary": "public_safe_static_only",
        "private_data_allowed_in_dist": False,
        "build_command": "npm run build",
        "output_dir": f"{project_id}/dist",
        "wrangler_config": f"{project_id}/wrangler.jsonc",
        "homehub_visibility": "visible_if_public_safe",
        "required_for_this_task": True,
        "deployment_required": True,
        "deployment_result": "deploy_ready_auth_blocked",
        "blockers": ["cloudflare_workers_auth"],
        "acceptance": ["build", "private_scan", "wrangler_dry_run"],
        "rollback": "revert bounded commit",
        "future_l3_extensions": [],
    }
    assert set(REQUIRED_FIELDS).issubset(item)
    return item


def registry() -> dict[str, object]:
    return {
        "schema_version": "cloudflare_compatibility_envelope.v1",
        "acceptance_id": "ACC-CF-L2-20260710",
        "projects": [project(project_id) for project_id in REQUIRED_PROJECTS],
    }


def deployments() -> dict[str, object]:
    return {
        "schema_version": "cloudflare_deployments.v1",
        "projects": [
            {
                "project_id": project_id,
                "deploy_result": "deploy_ready_auth_blocked",
                "actual_url": "",
                "http_verification": "not_run_auth_blocked",
            }
            for project_id in REQUIRED_PROJECTS
        ],
    }


class CompatibilityEnvelopeTests(unittest.TestCase):
    def run_python(self, script: Path, *args: str) -> subprocess.CompletedProcess[str]:
        self.assertTrue(script.is_file(), f"production script missing: {script}")
        return subprocess.run(
            [sys.executable, str(script), *args],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

    def write_json(self, path: Path, value: object) -> None:
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")

    def run_validator(
        self,
        temp: Path,
        projects_value: object,
        deployments_value: object | None = None,
    ) -> subprocess.CompletedProcess[str]:
        projects_path = temp / "projects.yaml"
        deployments_path = temp / "deployments.json"
        self.write_json(projects_path, projects_value)
        self.write_json(deployments_path, deployments_value or deployments())
        return self.run_python(
            VALIDATOR,
            "--projects",
            str(projects_path),
            "--deployments",
            str(deployments_path),
        )

    def test_valid_required_registry_passes(self) -> None:
        with tempfile.TemporaryDirectory() as raw_temp:
            result = self.run_validator(Path(raw_temp), registry())
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("PASS", result.stdout)

    def test_missing_required_project_fails(self) -> None:
        value = registry()
        value["projects"] = value["projects"][:-1]  # type: ignore[index]
        with tempfile.TemporaryDirectory() as raw_temp:
            result = self.run_validator(Path(raw_temp), value)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("missing required project", result.stdout + result.stderr)

    def test_required_project_cannot_remain_l1(self) -> None:
        value = registry()
        value["projects"][0]["compatibility_level"] = "L1"  # type: ignore[index]
        with tempfile.TemporaryDirectory() as raw_temp:
            result = self.run_validator(Path(raw_temp), value)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("required project cannot be L1", result.stdout + result.stderr)

    def test_deployed_result_requires_verified_url(self) -> None:
        value = registry()
        value["projects"][0]["deployment_result"] = "deployed_workers_dev_domain_pending"  # type: ignore[index]
        deployment_value = deployments()
        deployment_value["projects"][0]["deploy_result"] = "deployed_workers_dev_domain_pending"  # type: ignore[index]
        with tempfile.TemporaryDirectory() as raw_temp:
            result = self.run_validator(Path(raw_temp), value, deployment_value)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("deployed result requires verified actual_url", result.stdout + result.stderr)

    def test_safe_public_distribution_passes(self) -> None:
        with tempfile.TemporaryDirectory() as raw_temp:
            dist = Path(raw_temp) / "dist"
            dist.mkdir()
            (dist / "index.html").write_text(
                "<!doctype html><title>Public-safe L2 surface</title>",
                encoding="utf-8",
            )
            result = self.run_python(SCANNER, "--path", str(dist))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("PASS", result.stdout)

    def test_private_key_marker_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as raw_temp:
            dist = Path(raw_temp) / "dist"
            dist.mkdir()
            (dist / "index.html").write_text(
                "-----BEGIN PRIVATE KEY-----\nnot-a-real-key",
                encoding="utf-8",
            )
            result = self.run_python(SCANNER, "--path", str(dist))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("private_key", result.stdout + result.stderr)

    def test_local_absolute_path_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as raw_temp:
            dist = Path(raw_temp) / "dist"
            dist.mkdir()
            (dist / "app.js").write_text(
                'const runtime = "/Users/example/private.sqlite";',
                encoding="utf-8",
            )
            result = self.run_python(SCANNER, "--path", str(dist))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("local_absolute_path", result.stdout + result.stderr)

    def test_static_builder_replaces_stale_output_and_copies_source(self) -> None:
        self.assertTrue(STATIC_BUILDER.is_file(), f"production script missing: {STATIC_BUILDER}")
        with tempfile.TemporaryDirectory() as raw_temp:
            root = Path(raw_temp)
            source = root / "public"
            output = root / "dist"
            source.mkdir()
            output.mkdir()
            (source / "index.html").write_text("<title>safe</title>", encoding="utf-8")
            (source / "styles.css").write_text("body { color: black; }", encoding="utf-8")
            (output / "stale.txt").write_text("stale", encoding="utf-8")
            result = subprocess.run(
                [
                    "node",
                    str(STATIC_BUILDER),
                    "--source",
                    str(source),
                    "--output",
                    str(output),
                ],
                cwd=REPO_ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertFalse((output / "stale.txt").exists())
            self.assertEqual((output / "index.html").read_text(), "<title>safe</title>")
            self.assertEqual((output / "styles.css").read_text(), "body { color: black; }")


if __name__ == "__main__":
    unittest.main()
