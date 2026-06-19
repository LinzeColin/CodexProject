import importlib.util
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/deploy_memory_atlas_cloudflare.py"


def load_module():
    spec = importlib.util.spec_from_file_location("deploy_memory_atlas_cloudflare", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class MemoryAtlasCloudflareDeployTests(unittest.TestCase):
    def test_deploy_defaults_to_dry_run_without_external_writes(self) -> None:
        module = load_module()
        args = module.parse_args([])

        result = module.deploy(args)

        self.assertEqual(result["status"], "DRY_RUN")
        commands = [entry["command"] for entry in result["commands"]]
        self.assertIn(["npx", "wrangler", "pages", "deploy", "apps/memory-atlas/dist", "--project-name", "openai-memory-atlas"], commands)
        self.assertTrue(all(entry["status"] == "DRY_RUN" for entry in result["commands"]))

    def test_execute_requires_explicit_authorization_env(self) -> None:
        module = load_module()
        args = module.parse_args(["--execute"])

        with self.assertRaises(module.DeploymentError) as raised:
            module.deploy(args)

        self.assertIn("missing explicit local authorization", str(raised.exception))

    def test_write_evidence_requires_all_manual_verification_flags(self) -> None:
        module = load_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            args = module.parse_args(
                [
                    "--write-evidence",
                    "--evidence-out",
                    str(Path(temp_dir) / "live_evidence.json"),
                    "--deployment-url",
                    "https://openai-memory-atlas.pages.dev",
                ]
            )

            with self.assertRaises(module.DeploymentError) as raised:
                module.sanitized_evidence(args, ROOT, "https://openai-memory-atlas.pages.dev")

            self.assertIn("verification flags missing", str(raised.exception))

    def test_write_evidence_requires_output_path(self) -> None:
        module = load_module()
        args = module.parse_args(
            [
                "--write-evidence",
                "--deployment-url",
                "https://openai-memory-atlas.pages.dev",
                "--access-challenge-verified",
                "--allowed-user-app-load-verified",
                "--memory-atlas-json-fetch-verified",
                "--published-artifact-audited",
                "--no-raw-sensitive-artifacts-verified",
            ]
        )

        with self.assertRaises(module.DeploymentError) as raised:
            module.sanitized_evidence(args, ROOT, "https://openai-memory-atlas.pages.dev")

        self.assertIn("without --evidence-out", str(raised.exception))

    def test_write_sanitized_evidence_after_verified_execute(self) -> None:
        module = load_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            evidence_path = Path(temp_dir) / "live_evidence.json"
            args = module.parse_args(
                [
                    "--execute",
                    "--deployment-url",
                    "https://openai-memory-atlas.pages.dev",
                    "--write-evidence",
                    "--evidence-out",
                    str(evidence_path),
                    "--operator",
                    "test operator",
                    "--access-challenge-verified",
                    "--allowed-user-app-load-verified",
                    "--memory-atlas-json-fetch-verified",
                    "--published-artifact-audited",
                    "--no-raw-sensitive-artifacts-verified",
                ]
            )
            env = {
                "MEMORY_ATLAS_CLOUDFLARE_AUTHORIZED": "I_AUTHORIZE_THIS_DEPLOY",
                "CLOUDFLARE_ACCOUNT_ID": "account-id-not-written",
                "CLOUDFLARE_API_TOKEN": "token-not-written",
                "MEMORY_ATLAS_ACCESS_HOSTNAME": "openai-memory-atlas.pages.dev",
                "MEMORY_ATLAS_ALLOWED_EMAIL": "user@example.com",
            }
            with patch.dict(os.environ, env, clear=False):
                with patch.object(module, "run_command", return_value={"command": [], "status": "PASS", "stdout": "", "stderr": ""}):
                    result = module.deploy(args)

            evidence_text = evidence_path.read_text(encoding="utf-8")

        self.assertEqual(result["status"], "DEPLOY_COMMANDS_COMPLETED")
        self.assertNotIn("token-not-written", evidence_text)
        self.assertNotIn("account-id-not-written", evidence_text)
        self.assertIn("openai-memory-atlas.pages.dev", evidence_text)


if __name__ == "__main__":
    unittest.main()
