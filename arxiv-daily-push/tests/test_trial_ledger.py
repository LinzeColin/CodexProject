from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from arxiv_daily_push.cli import main
from arxiv_daily_push.scheduled_execution import SCHEDULED_EXECUTION_MODEL_ID
from arxiv_daily_push.trial_ledger import (
    TRIAL_LEDGER_MODEL_ID,
    update_trial_evidence_ledger,
    validate_trial_ledger_update_report,
)


def scheduled_execution_report(*, date: str = "2026-07-01", production_ready: bool = True) -> dict:
    status = "succeeded" if production_ready else "degraded"
    return {
        "execution_id": f"scheduled-execution:arxiv-daily-push:daily-run:{date}",
        "validator_id": SCHEDULED_EXECUTION_MODEL_ID,
        "project_id": "arxiv-daily-push",
        "generated_at": f"{date}T05:00:00+10:00",
        "mode": "daily-run",
        "status": status,
        "exit_code": 0 if production_ready else 2,
        "preflight_status": "pass",
        "scheduled_run_enabled": True,
        "production_evidence_ready": production_ready,
        "side_effect_policy": {
            "smtp_send_requested": True,
            "release_upload_requested": True,
            "secret_values_logged": False,
            "email_body_logged": False,
            "gh_output_logged": False,
            "codex_auth_read": False,
        },
        "evidence_refs": {
            "daily_run_ref": f"run-record://daily-{date}",
            "release_ref": f"github-release://LinzeColin/CodexProject/adp-daily-{date}",
            "email_ref": f"smtp://message/adp-{date}",
            "resource_gate_ref": f"resource-gate://adp/{date}",
        },
        "blocking_reasons": [] if production_ready else ["dry-run side effects are not production evidence"],
        "daily_run_report": {
            "status": "succeeded",
            "run_id": f"daily:{date}:arxiv:2607.00001",
            "date": date,
            "scheduled_local_time": "05:00",
            "source_id": f"arxiv:2607.{date[-2:]}001",
            "publication_id": f"pub:daily:{date}:arxiv:2607.00001",
            "run_record_status": "succeeded",
            "p0_claims_traceable": True,
            "unsupported_claims_published": False,
            "failure_generated_misleading_content": False,
        },
    }


class TrialLedgerTests(unittest.TestCase):
    def test_update_trial_ledger_appends_daily_entry_without_claiming_acceptance(self) -> None:
        report = update_trial_evidence_ledger(
            None,
            scheduled_execution_report(),
            generated_at="2026-07-01T06:00:00+10:00",
            trial_id="adp-trial-202607",
            trial_ref="release://adp/trial-ledger.json",
            text_degradation_path_verified=True,
            video_degradation_path_verified=True,
            scheduler_enabled=True,
            manual_rerun_verified=True,
            scheduler_ref="github-actions://adp-scheduler",
            private_release_verified=True,
            release_ref="github-release://LinzeColin/CodexProject/adp-trial",
            real_smtp_verified=True,
            email_ref="smtp://adp/30-day-delivery-evidence",
            resource_pressure_ok=True,
            resource_ref="resource-gate://adp/30-day",
        )

        self.assertEqual(report["model_id"], TRIAL_LEDGER_MODEL_ID)
        self.assertEqual(report["status"], "pass")
        self.assertTrue(report["ledger_updated"])
        self.assertFalse(report["accepted_for_production"])
        self.assertEqual(report["observed_day_count"], 1)
        self.assertEqual(report["daily_entry"]["source_id"], "arxiv:2607.01001")
        self.assertIn("below required 30", " ".join(report["trial_evidence_report"]["blocking_reasons"]))
        self.assertFalse(validate_trial_ledger_update_report(report))

    def test_update_trial_ledger_blocks_non_production_ready_scheduled_report(self) -> None:
        report = update_trial_evidence_ledger(
            None,
            scheduled_execution_report(production_ready=False),
            generated_at="2026-07-01T06:00:00+10:00",
        )

        self.assertEqual(report["status"], "blocked")
        self.assertFalse(report["ledger_updated"])
        self.assertIn("production_evidence_ready", " ".join(report["blocking_reasons"]))
        self.assertFalse(validate_trial_ledger_update_report(report))

    def test_update_trial_ledger_blocks_duplicate_daily_entry(self) -> None:
        first = update_trial_evidence_ledger(
            None,
            scheduled_execution_report(),
            generated_at="2026-07-01T06:00:00+10:00",
            text_degradation_path_verified=True,
            video_degradation_path_verified=True,
        )
        second = update_trial_evidence_ledger(
            first["trial_evidence"],
            scheduled_execution_report(),
            generated_at="2026-07-01T07:00:00+10:00",
            text_degradation_path_verified=True,
            video_degradation_path_verified=True,
        )

        self.assertEqual(second["status"], "blocked")
        self.assertIn("duplicates", " ".join(second["blocking_reasons"]))
        self.assertFalse(validate_trial_ledger_update_report(second))

    def test_update_trial_ledger_can_upgrade_global_evidence_flags(self) -> None:
        first = update_trial_evidence_ledger(
            None,
            scheduled_execution_report(date="2026-07-01"),
            generated_at="2026-07-01T06:00:00+10:00",
            text_degradation_path_verified=True,
            video_degradation_path_verified=True,
        )
        second = update_trial_evidence_ledger(
            first["trial_evidence"],
            scheduled_execution_report(date="2026-07-02"),
            generated_at="2026-07-02T06:00:00+10:00",
            text_degradation_path_verified=True,
            video_degradation_path_verified=True,
            scheduler_enabled=True,
            scheduler_ref="github-actions://adp-scheduler",
            private_release_verified=True,
            release_ref="github-release://LinzeColin/CodexProject/adp-trial",
            real_smtp_verified=True,
            email_ref="smtp://adp/30-day-delivery-evidence",
            resource_pressure_ok=True,
            resource_ref="resource-gate://adp/30-day",
        )

        evidence = second["trial_evidence"]
        self.assertTrue(evidence["scheduler"]["enabled"])
        self.assertTrue(evidence["release"]["private_release_verified"])
        self.assertTrue(evidence["email"]["real_smtp_verified"])
        self.assertTrue(evidence["resource_pressure"]["disk_ok"])

    def test_cli_update_trial_ledger_outputs_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            scheduled_path = Path(tmp) / "scheduled.json"
            scheduled_path.write_text(json.dumps(scheduled_execution_report()), encoding="utf-8")
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                result = main(
                    [
                        "update-trial-ledger",
                        "--scheduled-execution",
                        str(scheduled_path),
                        "--generated-at",
                        "2026-07-01T06:00:00+10:00",
                        "--trial-ref",
                        "release://adp/trial-ledger.json",
                        "--text-degradation-verified",
                        "--video-degradation-verified",
                        "--json",
                    ]
                )

        payload = json.loads(buffer.getvalue())
        self.assertEqual(result, 0)
        self.assertEqual(payload["model_id"], TRIAL_LEDGER_MODEL_ID)
        self.assertTrue(payload["ledger_updated"])


if __name__ == "__main__":
    unittest.main()
