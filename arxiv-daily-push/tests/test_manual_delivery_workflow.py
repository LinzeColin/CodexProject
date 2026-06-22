from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github/workflows/arxiv-daily-push-manual-delivery-test.yml"


class ManualDeliveryWorkflowTests(unittest.TestCase):
    def test_manual_delivery_workflow_is_cloud_manual_only(self) -> None:
        workflow = WORKFLOW.read_text(encoding="utf-8")

        self.assertIn("workflow_dispatch", workflow)
        self.assertNotIn("\n  schedule:", workflow)
        self.assertIn("runs-on: ubuntu-latest", workflow)
        self.assertNotIn("self-hosted", workflow)
        self.assertIn("contents: write", workflow)
        self.assertIn("SEND_TEST_EMAIL_TO_LINZEZHANG35_GMAIL_COM", workflow)
        self.assertIn("github.event.repository.default_branch", workflow)
        self.assertIn("linzezhang35@gmail.com", workflow)
        self.assertIn("secrets.ADP_SMTP_PASSWORD", workflow)
        self.assertIn("smtp.gmail.com", workflow)
        self.assertIn("ADP_PRODUCTION_ENABLED: \"false\"", workflow)
        self.assertIn("ADP_SCHEDULED_RUN_ENABLED: \"true\"", workflow)
        self.assertIn("ADP_ALLOW_SMTP_SEND: \"true\"", workflow)
        self.assertIn("ADP_ALLOW_RELEASE_UPLOAD: \"true\"", workflow)
        self.assertIn("ADP_RELEASE_DRAFT: \"false\"", workflow)
        self.assertNotIn("vars.ADP_PRODUCTION_ENABLED", workflow)
        self.assertNotIn("vars.ADP_SCHEDULED_RUN_ENABLED", workflow)
        self.assertNotIn("vars.ADP_ALLOW_SMTP_SEND", workflow)
        self.assertNotIn("vars.ADP_ALLOW_RELEASE_UPLOAD", workflow)

    def test_manual_delivery_workflow_orders_release_backed_email_path(self) -> None:
        workflow = WORKFLOW.read_text(encoding="utf-8")

        self.assertLess(workflow.index("preflight-production"), workflow.index("build-all-arxiv-daily-input"))
        self.assertLess(workflow.index("build-all-arxiv-daily-input"), workflow.index("render-lightweight-mp4"))
        self.assertLess(workflow.index("render-lightweight-mp4"), workflow.index("run-scheduled-production"))
        self.assertIn("--mode daily-run", workflow)
        self.assertIn("--release-asset", workflow)
        self.assertIn("adp-manual-delivery-scheduled-execution", workflow)
        self.assertIn("GitHub Release link only, no email attachment", workflow)
        self.assertNotIn("send-notification", workflow)
        self.assertNotIn("gh release create", workflow)

    def test_manual_delivery_workflow_deduplicates_release_assets_by_name(self) -> None:
        workflow = WORKFLOW.read_text(encoding="utf-8")

        self.assertIn("declare -A release_asset_names=()", workflow)
        self.assertIn("add_release_asset()", workflow)
        self.assertIn("basename \"$artifact\"", workflow)
        self.assertIn("Skipping duplicate Release asset name", workflow)
        self.assertIn('command+=(--release-asset "$artifact")', workflow)
        self.assertIn('add_release_asset "${{ steps.mp4.outputs.video_path }}"', workflow)
        self.assertIn('add_release_asset "$artifact"', workflow)
        self.assertNotIn('command+=(--release-asset "$artifact")\n            done', workflow)


if __name__ == "__main__":
    unittest.main()
