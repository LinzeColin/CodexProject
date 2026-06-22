from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github/workflows/arxiv-daily-push-phase12-cloud-dry-run.yml"


class CloudDryRunWorkflowTests(unittest.TestCase):
    def test_phase12_cloud_dry_run_is_github_hosted_and_side_effect_safe(self) -> None:
        workflow = WORKFLOW.read_text(encoding="utf-8")

        self.assertIn("runs-on: ubuntu-latest", workflow)
        self.assertIn("push:", workflow)
        self.assertIn("adp-phase12-cloud-enable", workflow)
        self.assertNotIn("self-hosted", workflow)
        self.assertIn("contents: read", workflow)
        self.assertNotIn("contents: write", workflow)
        self.assertIn("run-live-all-arxiv-dry-run", workflow)
        self.assertIn("render-lightweight-mp4", workflow)
        self.assertIn("adp-phase12-cloud-dry-run", workflow)
        self.assertIn("ADP_ALLOW_SMTP_SEND: \"false\"", workflow)
        self.assertIn("ADP_ALLOW_RELEASE_UPLOAD: \"false\"", workflow)
        self.assertNotIn("--allow-send", workflow)
        self.assertNotIn("--allow-upload", workflow)
        self.assertNotIn("gh release create", workflow)
        self.assertNotIn("gh release upload", workflow)


if __name__ == "__main__":
    unittest.main()
