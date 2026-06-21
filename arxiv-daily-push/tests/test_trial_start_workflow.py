from __future__ import annotations

import io
import json
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from arxiv_daily_push.cli import main
from arxiv_daily_push.trial_start_workflow import (
    REQUIRED_START_WORKFLOW_ARTIFACTS,
    TRIAL_START_WORKFLOW_VALIDATOR_ID,
    build_trial_start_workflow_plan,
    validate_trial_start_workflow_plan,
)


ROOT = Path(__file__).resolve().parents[2]


class TrialStartWorkflowTests(unittest.TestCase):
    def test_trial_start_workflow_plan_validates_manual_artifact_workflow(self) -> None:
        plan = build_trial_start_workflow_plan(ROOT, generated_at="2026-07-01T05:10:00+10:00")

        self.assertEqual(plan["validator_id"], TRIAL_START_WORKFLOW_VALIDATOR_ID)
        self.assertEqual(plan["status"], "pass")
        self.assertTrue(plan["trial_start_workflow_ready"])
        self.assertTrue(plan["manual_only"])
        self.assertFalse(plan["default_side_effects_enabled"])
        self.assertTrue(plan["requires_explicit_smtp_var"])
        self.assertTrue(plan["requires_explicit_release_var"])
        self.assertEqual(set(plan["required_artifacts"]), set(REQUIRED_START_WORKFLOW_ARTIFACTS))
        self.assertFalse(validate_trial_start_workflow_plan(plan))

    def test_trial_start_workflow_is_preflight_first_and_ref_complete(self) -> None:
        workflow = (ROOT / ".github/workflows/arxiv-daily-push-trial-start.yml").read_text(encoding="utf-8")

        self.assertIn("workflow_dispatch", workflow)
        self.assertNotIn("schedule:", workflow)
        self.assertIn("confirm_trial_start", workflow)
        self.assertIn("self-hosted", workflow)
        self.assertLess(workflow.index("preflight-production"), workflow.index("Fetch live source batch"))
        self.assertLess(workflow.index("Stop if preflight blocked"), workflow.index("Run SMTP delivery probe"))
        self.assertLess(workflow.index("fetch-arxiv-latest"), workflow.index("Run Release delivery probe"))
        self.assertIn("vars.ADP_ALLOW_SMTP_SEND", workflow)
        self.assertIn("vars.ADP_ALLOW_RELEASE_UPLOAD", workflow)
        self.assertIn("--allow-send", workflow)
        self.assertIn("--allow-upload", workflow)
        self.assertIn("secrets.ADP_SMTP_PASSWORD", workflow)
        self.assertIn("vars.ADP_RELEASE_TARGET", workflow)
        self.assertNotIn("auth.json", workflow)
        for artifact in REQUIRED_START_WORKFLOW_ARTIFACTS:
            self.assertIn(artifact, workflow)
        for ref_arg in (
            "--default-branch-ref",
            "--runner-ref",
            "--preflight-ref",
            "--source-ingest-ref",
            "--smtp-ref",
            "--release-ref",
            "--scheduler-ref",
            "--trial-state-ref",
            "--trial-start-ref",
        ):
            self.assertIn(ref_arg, workflow)

    def test_cli_plan_trial_start_workflow_outputs_ready_json(self) -> None:
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            result = main(
                [
                    "plan-trial-start-workflow",
                    "--path",
                    str(ROOT),
                    "--generated-at",
                    "2026-07-01T05:10:00+10:00",
                    "--json",
                ]
            )

        payload = json.loads(buffer.getvalue())
        self.assertEqual(result, 0)
        self.assertEqual(payload["validator_id"], TRIAL_START_WORKFLOW_VALIDATOR_ID)
        self.assertTrue(payload["trial_start_workflow_ready"])


if __name__ == "__main__":
    unittest.main()
