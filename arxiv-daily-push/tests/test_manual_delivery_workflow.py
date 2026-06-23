from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github/workflows/arxiv-daily-push-manual-delivery-test.yml"

class ManualDeliveryWorkflowTests(unittest.TestCase):
    def test_manual_delivery_workflow_is_cloud_manual_text_only(self) -> None:
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("workflow_dispatch", workflow)
        self.assertNotIn("\n  schedule:", workflow)
        self.assertIn("runs-on: ubuntu-latest", workflow)
        self.assertIn("contents: read", workflow)
        self.assertNotIn("contents: write", workflow)
        self.assertIn("SEND_TEST_EMAIL_TO_LINZEZHANG35_GMAIL_COM", workflow)
        self.assertIn("linzezhang35@gmail.com", workflow)
        self.assertIn('ADP_ALLOW_SMTP_SEND: "true"', workflow)
        self.assertNotIn("ADP_ALLOW_RELEASE", workflow)
        self.assertNotIn("ADP_RELEASE", workflow)
        self.assertNotIn("render-lightweight-mp4", workflow)
        self.assertNotIn("ffmpeg", workflow)

    def test_manual_delivery_workflow_orders_text_email_path(self) -> None:
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertLess(workflow.index("preflight-production"), workflow.index("build-all-arxiv-daily-input"))
        self.assertLess(workflow.index("build-all-arxiv-daily-input"), workflow.index("adp-text-delivery-policy.json"))
        self.assertLess(workflow.index("adp-text-delivery-policy.json"), workflow.index("run-scheduled-production"))
        self.assertIn("adp-manual-delivery-scheduled-execution", workflow)
        self.assertNotIn("gh release", workflow)

if __name__ == "__main__":
    unittest.main()
