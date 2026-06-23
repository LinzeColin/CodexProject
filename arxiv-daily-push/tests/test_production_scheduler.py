from __future__ import annotations

import io
import json
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from arxiv_daily_push.cli import main
from arxiv_daily_push.production_scheduler import PRODUCTION_SCHEDULER_VALIDATOR_ID, SCHEDULER_TIMEZONE, build_production_scheduler_plan, validate_production_scheduler_plan

ROOT = Path(__file__).resolve().parents[2]

class ProductionSchedulerTests(unittest.TestCase):
    def test_scheduler_plan_validates_timezone_scheduled_workflow(self) -> None:
        plan = build_production_scheduler_plan(ROOT, generated_at="2026-07-01T04:45:00+10:00")
        self.assertEqual(plan["validator_id"], PRODUCTION_SCHEDULER_VALIDATOR_ID)
        self.assertEqual(plan["status"], "pass")
        self.assertTrue(plan["scheduler_contract_ready"])
        self.assertEqual(plan["timezone"], SCHEDULER_TIMEZONE)
        self.assertEqual(plan["required_github_permissions"], ["actions: read", "contents: read"])
        self.assertEqual(plan["side_effect_enablement_vars"], ["ADP_ALLOW_SMTP_SEND"])
        self.assertFalse(validate_production_scheduler_plan(plan))

    def test_scheduled_workflow_is_text_only_and_side_effect_safe(self) -> None:
        workflow = (ROOT / ".github/workflows/arxiv-daily-push-scheduled.yml").read_text(encoding="utf-8")
        self.assertIn("actions: read", workflow)
        self.assertIn("contents: read", workflow)
        self.assertNotIn("contents: write", workflow)
        self.assertIn("runs-on: ubuntu-latest", workflow)
        self.assertIn('timezone: "Australia/Sydney"', workflow)
        self.assertIn("vars.ADP_PRODUCTION_ENABLED", workflow)
        self.assertIn("ADP_ALLOW_SMTP_SEND", workflow)
        self.assertNotIn("ADP_ALLOW_RELEASE", workflow)
        self.assertNotIn("ADP_RELEASE", workflow)
        self.assertIn("build-all-arxiv-daily-input", workflow)
        self.assertIn("ADP_ARXIV_MAX_RESULTS_PER_CATEGORY:-3", workflow)
        self.assertNotIn("ADP_ARXIV_MAX_RESULTS_PER_CATEGORY:-1", workflow)
        self.assertIn("adp-text-delivery-policy.json", workflow)
        self.assertNotIn("render-lightweight-mp4", workflow)
        self.assertNotIn("ffmpeg", workflow)
        self.assertIn("update-trial-ledger", workflow)
        self.assertIn("--text-artifacts-verified", workflow)
        self.assertNotIn("--private-release-verified", workflow)
        self.assertNotIn("gh release", workflow)

    def test_cli_plan_production_scheduler_outputs_ready_json(self) -> None:
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            result = main(["plan-production-scheduler", "--path", str(ROOT), "--generated-at", "2026-07-01T04:45:00+10:00", "--json"])
        payload = json.loads(buffer.getvalue())
        self.assertEqual(result, 0)
        self.assertEqual(payload["validator_id"], PRODUCTION_SCHEDULER_VALIDATOR_ID)
        self.assertTrue(payload["scheduler_contract_ready"])

if __name__ == "__main__":
    unittest.main()
