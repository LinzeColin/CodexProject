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
EXPECTED_ONLINE_SURFACES = {
    "linze-home-hub": ("deployed_custom_domain_verified", "https://home.linzezhang.com"),
    "nab": ("deployed_custom_domain_verified", "https://nab.linzezhang.com"),
    "eei": ("deployed_workers_dev_domain_pending", "https://codex-eei.linzezhang35.workers.dev"),
    "openaidatabase": ("deployed_custom_domain_verified", "https://memoryatlas.linzezhang.com"),
    "pfi": ("deployed_workers_dev_domain_pending", "https://codex-pfi.linzezhang35.workers.dev"),
    "serenity-alipay": (
        "deployed_workers_dev_domain_pending",
        "https://serenity-alipay.linzezhang35.workers.dev",
    ),
}
EXPECTED_EVIDENCE_COMMITS = {
    "linze-home-hub": "59347956c03ee2810358887f20cb13bdc2ef9289",
    "nab": "d0721022cfb48ae3edf439fffeb92c36ed00cefc",
    "eei": "ed0fe3a3e8f2f0f46d0f4f442c23fed5ed093935",
    "openaidatabase": "00f4187f43960a3b25fc696ae2a15951f4431763",
    "pfi": "ed0fe3a3e8f2f0f46d0f4f442c23fed5ed093935",
    "serenity-alipay": "ed0fe3a3e8f2f0f46d0f4f442c23fed5ed093935",
}
PROJECT_TASK_FILES = (
    ROOT / "OpenAIDatabase/docs/governance/delivery_tasks.yaml",
    ROOT / "PFI/docs/governance/delivery_tasks.yaml",
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

    def test_required_l2_online_surfaces_are_verified(self) -> None:
        document = json.loads(DEPLOYMENTS.read_text(encoding="utf-8"))
        records = {item["project_id"]: item for item in document["projects"]}
        self.assertEqual(set(records), set(EXPECTED_ONLINE_SURFACES))
        for project_id, (expected_result, expected_url) in EXPECTED_ONLINE_SURFACES.items():
            with self.subTest(project_id=project_id):
                record = records[project_id]
                self.assertEqual(record["deploy_result"], expected_result)
                self.assertEqual(record["actual_url"], expected_url)
                self.assertEqual(record["http_verification"], "verified_200")
                self.assertEqual(record["evidence_commit_sha"], EXPECTED_EVIDENCE_COMMITS[project_id])

    def test_root_run_manifest_binds_the_acceptance(self) -> None:
        manifest = json.loads(RUN_MANIFEST.read_text(encoding="utf-8"))
        self.assertGreaterEqual(manifest["schema_version"], 2)
        self.assertEqual(manifest["task_id"], "CF-L2-20260710")
        self.assertIn("ACC-CF-L2-20260710", manifest["acceptance_ids"])
        self.assertIn("governance/cloudflare/deployments.json", manifest["changed_files_actual"])


if __name__ == "__main__":
    unittest.main()
