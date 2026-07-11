import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/audit_memory_atlas_goal_completion.py"
CANONICAL_LIVE_EVIDENCE = Path(
    "机器治理/证据与日志/final_delivery/memory_atlas_cloudflare_live_evidence.json"
)


def load_module():
    spec = importlib.util.spec_from_file_location("audit_memory_atlas_goal_completion", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def current_commit() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def run_git(repo_root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def initialize_git_repo(repo_root: Path) -> None:
    run_git(repo_root, "init", "-q")
    run_git(repo_root, "config", "user.name", "Memory Atlas Test")
    run_git(repo_root, "config", "user.email", "memory-atlas-test@example.invalid")


def commit_all(repo_root: Path, message: str) -> str:
    run_git(repo_root, "add", "--all")
    run_git(repo_root, "commit", "-q", "-m", message)
    return run_git(repo_root, "rev-parse", "HEAD")


def live_evidence_payload(git_commit: str) -> dict[str, object]:
    return {
        "schema_version": "memory_atlas.cloudflare_live_evidence.v1",
        "deployment_url": "https://memoryatlas.example.invalid",
        "git_commit": git_commit,
        "cloudflare_pages_project": "openai-memory-atlas",
        "access_hostname": "memoryatlas.example.invalid",
        "allowed_email": "REDACTED_OWNER_EMAIL_ALLOWLIST_VERIFIED",
        "verified_at": "2026-07-10T00:00:00Z",
        "operator": "authorized operator",
        "access_challenge_verified": True,
        "allowed_user_app_load_verified": True,
        "memory_atlas_json_fetch_verified": True,
        "published_artifact_audited": True,
        "no_raw_sensitive_artifacts_verified": True,
    }


def write_live_evidence(path: Path, git_commit: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(live_evidence_payload(git_commit)), encoding="utf-8")


class MemoryAtlasGoalCompletionTests(unittest.TestCase):
    def test_goal_completion_reports_external_blocker_without_live_evidence(self) -> None:
        module = load_module()

        result = module.audit_goal_completion(ROOT)

        self.assertEqual(result["status"], "LOCAL_PASS_EXTERNAL_AUTHORIZATION_REQUIRED")
        checks = {check["name"]: check["status"] for check in result["checks"]}
        self.assertEqual(checks["local_acceptance"], "PASS")
        self.assertEqual(checks["cloudflare_live_access_evidence"], "EXTERNAL_BLOCKED")

    def test_goal_completion_rejects_missing_publish_dir_with_cleanup_hint(self) -> None:
        module = load_module()

        with self.assertRaises(module.GoalCompletionError) as raised:
            module.audit_goal_completion(ROOT, publish_dir=Path("apps/memory-atlas/dist-missing"))

        message = str(raised.exception)
        self.assertIn("publish_dir_available", message)
        self.assertIn("omit --publish-dir after cleanup", message)

    def test_goal_completion_strict_mode_rejects_missing_live_evidence(self) -> None:
        module = load_module()

        with self.assertRaises(module.GoalCompletionError) as raised:
            module.audit_goal_completion(ROOT, require_complete=True)

        self.assertIn("LOCAL_PASS_EXTERNAL_AUTHORIZATION_REQUIRED", str(raised.exception))

    def test_goal_completion_accepts_sanitized_live_evidence(self) -> None:
        module = load_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            evidence_path = Path(temp_dir) / "live_evidence.json"
            write_live_evidence(evidence_path, current_commit())

            with (
                mock.patch.object(module, "audit_acceptance", return_value={"checks": []}),
                mock.patch.object(module, "cloudflare_preflight", return_value={"checks": []}),
                mock.patch.object(
                    module,
                    "audit_final_records",
                    return_value={"status": "PASS", "verified_requirement_count": 58, "stage_count": 14},
                ),
            ):
                result = module.audit_goal_completion(ROOT, live_evidence=evidence_path, require_complete=True)

        self.assertEqual(result["status"], "COMPLETE_WITH_OPERATOR_EVIDENCE")

    def test_goal_completion_cannot_complete_without_r8_58_of_58_records(self) -> None:
        module = load_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            evidence_path = Path(temp_dir) / "live_evidence.json"
            write_live_evidence(evidence_path, current_commit())

            with (
                mock.patch.object(module, "audit_acceptance", return_value={"checks": []}),
                mock.patch.object(module, "cloudflare_preflight", return_value={"checks": []}),
            ):
                result = module.audit_goal_completion(ROOT, live_evidence=evidence_path)

        self.assertEqual(result["status"], "LOCAL_PASS_EXTERNAL_AUTHORIZATION_REQUIRED")
        r8_check = next(check for check in result["checks"] if check["name"] == "r8_final_acceptance")
        self.assertEqual(r8_check["status"], "INCOMPLETE")

    def test_live_evidence_accepts_deployed_commit_as_immediate_parent_of_record_commit(self) -> None:
        module = load_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            initialize_git_repo(repo_root)
            app_path = repo_root / "apps/memory-atlas/src/App.tsx"
            app_path.parent.mkdir(parents=True)
            app_path.write_text("export const deployed = true;\n", encoding="utf-8")
            deployed_commit = commit_all(repo_root, "deploy Memory Atlas")

            evidence_path = repo_root / CANONICAL_LIVE_EVIDENCE
            write_live_evidence(evidence_path, deployed_commit)
            r8_record = repo_root / "机器治理/证据与日志/remediation/v1_2_r8/final_acceptance.json"
            r8_record.parent.mkdir(parents=True)
            r8_record.write_text('{"status":"PASS"}\n', encoding="utf-8")
            commit_all(repo_root, "record live evidence")
            checks: list[dict[str, str]] = []

            accepted = module.audit_live_evidence(repo_root, evidence_path, checks)

        self.assertTrue(accepted)
        git_check = next(check for check in checks if check["name"] == "cloudflare_live_git_commit_matches")
        self.assertEqual(git_check["status"], "PASS")
        self.assertIn("immediate parent", git_check["evidence"])

    def test_live_evidence_rejects_post_deploy_application_change(self) -> None:
        module = load_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            initialize_git_repo(repo_root)
            app_path = repo_root / "apps/memory-atlas/src/App.tsx"
            app_path.parent.mkdir(parents=True)
            app_path.write_text("export const deployed = true;\n", encoding="utf-8")
            deployed_commit = commit_all(repo_root, "deploy Memory Atlas")

            evidence_path = repo_root / CANONICAL_LIVE_EVIDENCE
            write_live_evidence(evidence_path, deployed_commit)
            app_path.write_text("export const deployed = false;\n", encoding="utf-8")
            commit_all(repo_root, "mix evidence with application change")
            checks: list[dict[str, str]] = []

            accepted = module.audit_live_evidence(repo_root, evidence_path, checks)

        self.assertFalse(accepted)
        git_check = next(check for check in checks if check["name"] == "cloudflare_live_git_commit_matches")
        self.assertEqual(git_check["status"], "FAIL")
        self.assertIn("non-record paths", git_check["evidence"])

    def test_live_evidence_rejects_deployed_commit_older_than_immediate_parent(self) -> None:
        module = load_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            initialize_git_repo(repo_root)
            app_path = repo_root / "apps/memory-atlas/src/App.tsx"
            app_path.parent.mkdir(parents=True)
            app_path.write_text("export const deployed = true;\n", encoding="utf-8")
            deployed_commit = commit_all(repo_root, "deploy Memory Atlas")

            evidence_path = repo_root / CANONICAL_LIVE_EVIDENCE
            write_live_evidence(evidence_path, deployed_commit)
            commit_all(repo_root, "record live evidence")
            delivery_record = repo_root / "docs/MEMORY_ATLAS_DELIVERY_RECORD.md"
            delivery_record.parent.mkdir(parents=True)
            delivery_record.write_text("# Later record\n", encoding="utf-8")
            commit_all(repo_root, "add later delivery record")
            checks: list[dict[str, str]] = []

            accepted = module.audit_live_evidence(repo_root, evidence_path, checks)

        self.assertFalse(accepted)
        git_check = next(check for check in checks if check["name"] == "cloudflare_live_git_commit_matches")
        self.assertEqual(git_check["status"], "FAIL")
        self.assertIn("immediate parent", git_check["evidence"])

    def test_goal_completion_rejects_secret_like_evidence_keys(self) -> None:
        module = load_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            evidence_path = Path(temp_dir) / "live_evidence.json"
            evidence_path.write_text(
                json.dumps(
                    {
                        "schema_version": "memory_atlas.cloudflare_live_evidence.v1",
                        "deployment_url": "https://openai-memory-atlas.pages.dev",
                        "git_commit": current_commit(),
                        "cloudflare_pages_project": "openai-memory-atlas",
                        "access_hostname": "openai-memory-atlas.pages.dev",
                        "allowed_email": "user@example.com",
                        "verified_at": "2026-06-16T00:00:00Z",
                        "operator": "authorized operator",
                        "access_challenge_verified": True,
                        "allowed_user_app_load_verified": True,
                        "memory_atlas_json_fetch_verified": True,
                        "published_artifact_audited": True,
                        "no_raw_sensitive_artifacts_verified": True,
                        "api_token": "do-not-store",
                    }
                ),
                encoding="utf-8",
            )

            with self.assertRaises(module.GoalCompletionError) as raised:
                module.audit_goal_completion(ROOT, live_evidence=evidence_path, require_complete=True)

        self.assertIn("forbidden sensitive evidence keys", str(raised.exception))


if __name__ == "__main__":
    unittest.main()
