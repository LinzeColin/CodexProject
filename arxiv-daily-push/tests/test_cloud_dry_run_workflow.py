from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github/workflows/arxiv-daily-push-phase12-cloud-dry-run.yml"

class CloudDryRunWorkflowTests(unittest.TestCase):
    def test_phase12_cloud_dry_run_is_github_hosted_and_side_effect_safe(self) -> None:
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("runs-on: ubuntu-latest", workflow)
        self.assertNotIn("self-hosted", workflow)
        self.assertIn("contents: read", workflow)
        self.assertNotIn("contents: write", workflow)
        self.assertIn("run-live-all-arxiv-dry-run", workflow)
        self.assertIn("--fetcher curl", workflow)
        self.assertIn("adp-phase12-cloud-dry-run", workflow)
        self.assertIn('ADP_ALLOW_SMTP_SEND: "false"', workflow)
        self.assertNotIn("ADP_ALLOW_RELEASE", workflow)
        self.assertNotIn("render-lightweight-mp4", workflow)
        self.assertNotIn("ffmpeg", workflow)
        self.assertNotIn("gh release", workflow)
        self.assertIn('ZoneInfo("Australia/Sydney")', workflow)
        self.assertIn("astimezone", workflow)
        self.assertIn("service_date", workflow)
        self.assertNotIn("${generated_at:0:10}", workflow)

if __name__ == "__main__":
    unittest.main()
