import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/audit_memory_atlas_goal_completion.py"


def load_module():
    spec = importlib.util.spec_from_file_location("audit_memory_atlas_goal_completion", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def current_commit() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


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
                    }
                ),
                encoding="utf-8",
            )

            result = module.audit_goal_completion(ROOT, live_evidence=evidence_path, require_complete=True)

        self.assertEqual(result["status"], "COMPLETE_WITH_OPERATOR_EVIDENCE")

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
