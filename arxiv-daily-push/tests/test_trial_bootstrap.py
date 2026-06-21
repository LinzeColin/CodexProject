from __future__ import annotations

import io
import json
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from arxiv_daily_push.cli import main
from arxiv_daily_push.trial_bootstrap import (
    TRIAL_BOOTSTRAP_PLAN_ID,
    build_trial_bootstrap_plan,
    validate_trial_bootstrap_plan,
)


ROOT = Path(__file__).resolve().parents[2]


class TrialBootstrapTests(unittest.TestCase):
    def test_trial_bootstrap_plan_validates_manual_workflow(self) -> None:
        plan = build_trial_bootstrap_plan(ROOT, generated_at="2026-07-01T04:45:00+10:00")

        self.assertEqual(plan["validator_id"], TRIAL_BOOTSTRAP_PLAN_ID)
        self.assertEqual(plan["status"], "pass")
        self.assertTrue(plan["trial_bootstrap_ready"])
        self.assertFalse(plan["scheduled_production_enabled"])
        self.assertFalse(plan["release_upload_enabled"])
        self.assertFalse(plan["real_smtp_send_enabled"])
        self.assertFalse(plan["secret_values_logged"])
        self.assertFalse(validate_trial_bootstrap_plan(plan))

    def test_trial_bootstrap_workflow_is_preflight_first_and_secret_safe(self) -> None:
        workflow = (ROOT / ".github/workflows/arxiv-daily-push-production-trial.yml").read_text(encoding="utf-8")

        self.assertIn("workflow_dispatch", workflow)
        self.assertNotIn("schedule:", workflow)
        self.assertLess(workflow.index("preflight-production"), workflow.index("Run project tests after preflight"))
        self.assertIn("secrets.ADP_SMTP_PASSWORD", workflow)
        self.assertNotIn("auth.json", workflow)
        self.assertNotIn("gh release upload", workflow)
        self.assertNotIn("sendmail", workflow)

    def test_cli_plan_trial_bootstrap_outputs_ready_json(self) -> None:
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            result = main(["plan-trial-bootstrap", "--path", str(ROOT), "--generated-at", "2026-07-01T04:45:00+10:00", "--json"])

        payload = json.loads(buffer.getvalue())
        self.assertEqual(result, 0)
        self.assertEqual(payload["validator_id"], TRIAL_BOOTSTRAP_PLAN_ID)
        self.assertTrue(payload["trial_bootstrap_ready"])


if __name__ == "__main__":
    unittest.main()
