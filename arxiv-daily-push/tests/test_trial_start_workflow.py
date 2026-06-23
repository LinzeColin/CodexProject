from __future__ import annotations

import io
import json
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from arxiv_daily_push.cli import main
from arxiv_daily_push.trial_start_workflow import TRIAL_START_WORKFLOW_VALIDATOR_ID, build_trial_start_workflow_plan, validate_trial_start_workflow_plan

ROOT = Path(__file__).resolve().parents[2]

class TrialStartWorkflowTests(unittest.TestCase):
    def test_trial_start_workflow_plan_is_text_only(self) -> None:
        plan = build_trial_start_workflow_plan(ROOT, generated_at="2026-07-01T04:00:00+10:00")
        self.assertEqual(plan["validator_id"], TRIAL_START_WORKFLOW_VALIDATOR_ID)
        self.assertEqual(plan["status"], "pass")
        self.assertTrue(plan["trial_start_workflow_ready"])
        self.assertFalse(plan["requires_explicit_release_var"])
        self.assertEqual(plan["required_github_permissions"], ["actions: read", "contents: read"])
        self.assertFalse(validate_trial_start_workflow_plan(plan))

    def test_workflow_collects_text_artifact_before_smtp(self) -> None:
        workflow = (ROOT / ".github/workflows/arxiv-daily-push-trial-start.yml").read_text(encoding="utf-8")
        self.assertIn("workflow_dispatch", workflow)
        self.assertIn("runs-on: ubuntu-latest", workflow)
        self.assertIn("contents: read", workflow)
        self.assertLess(workflow.index("preflight-production"), workflow.index("Build all-arXiv trial input"))
        self.assertLess(workflow.index("adp-text-delivery-policy.json"), workflow.index("Run SMTP delivery probe"))
        self.assertIn("plan-trial-start", workflow)
        self.assertNotIn("ADP_ALLOW_RELEASE", workflow)
        self.assertNotIn("ADP_RELEASE", workflow)
        self.assertNotIn("render-lightweight-mp4", workflow)
        self.assertNotIn("ffmpeg", workflow)
        self.assertNotIn("--release-ref", workflow)

    def test_cli_plan_trial_start_workflow_outputs_ready_json(self) -> None:
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            result = main(["plan-trial-start-workflow", "--path", str(ROOT), "--generated-at", "2026-07-01T04:00:00+10:00", "--json"])
        payload = json.loads(buffer.getvalue())
        self.assertEqual(result, 0)
        self.assertEqual(payload["validator_id"], TRIAL_START_WORKFLOW_VALIDATOR_ID)
        self.assertTrue(payload["trial_start_workflow_ready"])

if __name__ == "__main__":
    unittest.main()
