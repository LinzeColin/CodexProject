from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DEPLOYMENTS = ROOT / "governance/cloudflare/deployments.json"
RUN_MANIFEST = ROOT / "governance/run_manifests/CF-L2-20260710.json"
REQUIRED_PROJECTS = {
    "linze-home-hub",
    "nab",
    "eei",
    "openaidatabase",
    "pfi",
    "serenity-alipay",
}
PROJECT_TASK_FILES = (
    ROOT / "EEI/docs/governance/delivery_tasks.yaml",
    ROOT / "OpenAIDatabase/docs/governance/delivery_tasks.yaml",
    ROOT / "PFI/docs/governance/delivery_tasks.yaml",
    ROOT / "Serenity-Alipay/docs/governance/delivery_tasks.yaml",
)


class CloudflareCompatibilityGovernanceTests(unittest.TestCase):
    def test_required_deployments_are_recorded_without_false_live_claims(self) -> None:
        document = json.loads(DEPLOYMENTS.read_text(encoding="utf-8"))
        records = {item["project_id"]: item for item in document["projects"]}
        self.assertEqual(set(records), REQUIRED_PROJECTS)
        for project_id, record in records.items():
            with self.subTest(project_id=project_id):
                if str(record["deploy_result"]).startswith("deployed_"):
                    self.assertTrue(record["actual_url"])
                    self.assertEqual(record["http_verification"], "verified_200")
                else:
                    self.assertFalse(record["actual_url"])

    def test_each_changed_project_has_the_cloudflare_delivery_task(self) -> None:
        for path in PROJECT_TASK_FILES:
            with self.subTest(path=path):
                self.assertIn('task_id: "CF-L2-20260710"', path.read_text(encoding="utf-8"))

    def test_root_run_manifest_binds_the_acceptance(self) -> None:
        manifest = json.loads(RUN_MANIFEST.read_text(encoding="utf-8"))
        self.assertGreaterEqual(manifest["schema_version"], 2)
        self.assertEqual(manifest["task_id"], "CF-L2-20260710")
        self.assertIn("ACC-CF-L2-20260710", manifest["acceptance_ids"])
        self.assertIn("governance/cloudflare/deployments.json", manifest["changed_files_actual"])


if __name__ == "__main__":
    unittest.main()
