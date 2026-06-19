import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class MemoryAtlasDeploymentTests(unittest.TestCase):
    def test_cloudflare_pages_config_and_access_docs_exist(self) -> None:
        wrangler = json.loads((ROOT / "wrangler.jsonc").read_text(encoding="utf-8"))
        self.assertEqual(wrangler["name"], "openai-memory-atlas")
        self.assertEqual(wrangler["pages_build_output_dir"], "apps/memory-atlas/dist")

        docs = (ROOT / "docs/MEMORY_ATLAS_DEPLOYMENT.md").read_text(encoding="utf-8")
        self.assertIn("Cloudflare Pages + Access", docs)
        self.assertIn("MEMORY_ATLAS_CLOUDFLARE_RUNBOOK.md", docs)
        self.assertIn("preflight_cloudflare_pages_access.py", docs)
        self.assertIn("Build output directory: apps/memory-atlas/dist", docs)
        self.assertIn("Zero Trust Access", docs)
        self.assertIn("versioned proposal", docs)
        self.assertIn("cannot mutate active", docs)

        runbook = (ROOT / "docs/MEMORY_ATLAS_CLOUDFLARE_RUNBOOK.md").read_text(encoding="utf-8")
        self.assertIn("https://developers.cloudflare.com/pages/get-started/direct-upload/", runbook)
        self.assertIn("https://developers.cloudflare.com/cloudflare-one/access-controls/applications/http-apps/self-hosted-public-app/", runbook)
        self.assertIn("wrangler pages deploy apps/memory-atlas/dist", runbook)
        self.assertIn("明确授权", runbook)

        pages_template = json.loads((ROOT / "config/cloudflare/pages_direct_upload.template.json").read_text(encoding="utf-8"))
        access_template = json.loads((ROOT / "config/cloudflare/access_self_hosted_application.template.json").read_text(encoding="utf-8"))
        self.assertEqual(pages_template["project_name"], "openai-memory-atlas")
        self.assertTrue(pages_template["deploy"]["requires_explicit_user_authorization"])
        self.assertEqual(access_template["application"]["type"], "self_hosted_public_hostname")
        self.assertTrue(access_template["policy"]["deny_by_default"])


if __name__ == "__main__":
    unittest.main()
