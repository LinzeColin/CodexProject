from __future__ import annotations

import io
import json
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from arxiv_daily_push.cli import main
from arxiv_daily_push.production_scheduler import (
    PRODUCTION_SCHEDULER_VALIDATOR_ID,
    SCHEDULER_TIMEZONE,
    build_production_scheduler_plan,
    validate_production_scheduler_plan,
)


ROOT = Path(__file__).resolve().parents[2]


class ProductionSchedulerTests(unittest.TestCase):
    def test_scheduler_plan_validates_timezone_scheduled_workflow(self) -> None:
        plan = build_production_scheduler_plan(ROOT, generated_at="2026-07-01T04:45:00+10:00")

        self.assertEqual(plan["validator_id"], PRODUCTION_SCHEDULER_VALIDATOR_ID)
        self.assertEqual(plan["status"], "pass")
        self.assertTrue(plan["scheduler_contract_ready"])
        self.assertEqual(plan["timezone"], SCHEDULER_TIMEZONE)
        self.assertEqual([slot["local_time"] for slot in plan["schedule_slots"]], ["04:45", "05:00", "05:10"])
        self.assertFalse(plan["scheduled_production_enabled"])
        self.assertFalse(plan["scheduled_run_enabled"])
        self.assertFalse(plan["release_upload_enabled"])
        self.assertFalse(plan["real_smtp_send_enabled"])
        self.assertFalse(plan["secret_values_logged"])
        self.assertFalse(validate_production_scheduler_plan(plan))

    def test_scheduled_workflow_is_preflight_first_and_side_effect_safe(self) -> None:
        workflow = (ROOT / ".github/workflows/arxiv-daily-push-scheduled.yml").read_text(encoding="utf-8")

        self.assertIn('timezone: "Australia/Sydney"', workflow)
        self.assertIn('cron: "45 4 * * *"', workflow)
        self.assertIn('cron: "0 5 * * *"', workflow)
        self.assertIn('cron: "10 5 * * *"', workflow)
        self.assertIn("vars.ADP_PRODUCTION_ENABLED", workflow)
        self.assertIn("ADP_SCHEDULED_RUN_ENABLED", workflow)
        self.assertIn("ADP_DAILY_INPUT_PATH", workflow)
        self.assertIn("ADP_ALLOW_SMTP_SEND", workflow)
        self.assertIn("ADP_ALLOW_RELEASE_UPLOAD", workflow)
        self.assertLess(workflow.index("preflight-production"), workflow.index("Run scheduled mode"))
        self.assertIn("adp-scheduled-preflight", workflow)
        self.assertIn("run-scheduled-production", workflow)
        self.assertIn("adp-scheduled-execution", workflow)
        self.assertIn("secrets.ADP_SMTP_PASSWORD", workflow)
        self.assertNotIn("auth.json", workflow)
        self.assertNotIn("--allow-send", workflow)
        self.assertNotIn("--allow-upload", workflow)
        self.assertNotIn("gh release create", workflow)

    def test_cli_plan_production_scheduler_outputs_ready_json(self) -> None:
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            result = main(
                [
                    "plan-production-scheduler",
                    "--path",
                    str(ROOT),
                    "--generated-at",
                    "2026-07-01T04:45:00+10:00",
                    "--json",
                ]
            )

        payload = json.loads(buffer.getvalue())
        self.assertEqual(result, 0)
        self.assertEqual(payload["validator_id"], PRODUCTION_SCHEDULER_VALIDATOR_ID)
        self.assertTrue(payload["scheduler_contract_ready"])


if __name__ == "__main__":
    unittest.main()
