from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from arxiv_daily_push.cli import main
from arxiv_daily_push.scheduled_execution import SCHEDULED_EXECUTION_MODEL_ID
from arxiv_daily_push.smtp_delivery import SMTP_DELIVERY_MODEL_ID
from arxiv_daily_push.trial_recovery import (
    TRIAL_RECOVERY_MODEL_ID,
    build_trial_recovery_evidence,
    validate_trial_recovery_report,
)


def sent_notification(delivery_id: str = "failure") -> dict:
    return {
        "delivery_id": f"smtp-delivery:{delivery_id}",
        "validator_id": SMTP_DELIVERY_MODEL_ID,
        "project_id": "arxiv-daily-push",
        "project_name": "arXiv Daily Push",
        "generated_at": "2026-07-01T05:00:00+10:00",
        "recipient": "linzezhang35@gmail.com",
        "expected_recipient": "linzezhang35@gmail.com",
        "subject": f"arXiv Daily Push {delivery_id}",
        "status": "sent",
        "dry_run": False,
        "real_smtp_send_enabled": True,
        "required_env_keys": ["ADP_SMTP_HOST", "ADP_SMTP_PORT", "ADP_SMTP_USERNAME", "ADP_SMTP_PASSWORD"],
        "smtp_config": {
            "host_configured": True,
            "port_configured": True,
            "username_configured": True,
            "password_configured": True,
            "port_valid": True,
            "require_tls": True,
            "timeout_seconds": 30,
            "secret_values_logged": False,
        },
        "message": {
            "body_sha256": "0" * 64,
            "body_logged": False,
            "message_id": f"smtp-delivery:{delivery_id}",
        },
        "blocking_reasons": [],
        "delivery_ref": f"smtp://message/smtp-delivery:{delivery_id}",
    }


def dry_run_notification() -> dict:
    report = sent_notification("dry-run")
    report["status"] = "dry_run"
    report["dry_run"] = True
    report["real_smtp_send_enabled"] = False
    report.pop("delivery_ref")
    return report


def failure_execution_report(status: str = "failed", notification: dict | None = None) -> dict:
    report = {
        "execution_id": "scheduled-execution:arxiv-daily-push:daily-run:failed",
        "validator_id": SCHEDULED_EXECUTION_MODEL_ID,
        "project_id": "arxiv-daily-push",
        "generated_at": "2026-07-01T05:00:00+10:00",
        "mode": "daily-run",
        "status": status,
        "exit_code": 2,
        "preflight_status": "pass",
        "scheduled_run_enabled": True,
        "production_evidence_ready": False,
        "side_effect_policy": {
            "smtp_send_requested": True,
            "release_upload_requested": True,
            "secret_values_logged": False,
            "email_body_logged": False,
            "gh_output_logged": False,
            "codex_auth_read": False,
        },
        "evidence_refs": {
            "daily_run_ref": "",
            "release_ref": "",
            "email_ref": "",
            "resource_gate_ref": "resource-gate://adp/20260701",
        },
        "blocking_reasons": ["daily pipeline failed: simulated failure"],
        "notification_report": notification or sent_notification("failure"),
        "daily_run_report": {
            "status": "failed",
            "run_id": "daily:2026-07-01:failed",
            "date": "2026-07-01",
            "scheduled_local_time": "05:00",
            "source_id": "arxiv:2607.00001",
            "publication_id": "pub-20260701",
            "run_record_status": "failed",
            "p0_claims_traceable": False,
            "unsupported_claims_published": False,
            "failure_generated_misleading_content": False,
        },
    }
    if status == "blocked":
        report.pop("daily_run_report")
    return report


def recovery_execution_report(*, production_ready: bool = True) -> dict:
    status = "succeeded" if production_ready else "degraded"
    return {
        "execution_id": "scheduled-execution:arxiv-daily-push:daily-run:recovered",
        "validator_id": SCHEDULED_EXECUTION_MODEL_ID,
        "project_id": "arxiv-daily-push",
        "generated_at": "2026-07-01T05:30:00+10:00",
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
            "daily_run_ref": "run-record://daily:2026-07-01:recovered",
            "release_ref": "github-release://adp/daily-20260701-recovery",
            "email_ref": "smtp://message/smtp-delivery:recovery",
            "resource_gate_ref": "resource-gate://adp/20260701",
        },
        "blocking_reasons": [] if production_ready else ["daily pipeline completed but real SMTP and Release evidence are not both present"],
        "notification_report": sent_notification("recovery"),
        "daily_run_report": {
            "status": "succeeded",
            "run_id": "daily:2026-07-01:recovered",
            "date": "2026-07-01",
            "scheduled_local_time": "05:00",
            "source_id": "arxiv:2607.00001",
            "publication_id": "pub-20260701",
            "run_record_status": "succeeded",
            "p0_claims_traceable": True,
            "unsupported_claims_published": False,
            "failure_generated_misleading_content": False,
        },
    }


class TrialRecoveryTests(unittest.TestCase):
    def test_build_trial_recovery_evidence_passes_failed_then_recovered_daily_run(self) -> None:
        report = build_trial_recovery_evidence(
            failure_execution_report(),
            recovery_execution_report(),
            generated_at="2026-07-01T05:45:00+10:00",
            failure_ref="github-actions://adp/run/failed-20260701",
            recovery_ref="github-actions://adp/run/recovered-20260701",
        )

        self.assertEqual(report["model_id"], TRIAL_RECOVERY_MODEL_ID)
        self.assertEqual(report["status"], "pass")
        self.assertTrue(report["recovery_drill_verified"])
        self.assertEqual(report["failure_summary"]["notification_status"], "sent")
        self.assertEqual(report["recovery_summary"]["status"], "succeeded")
        self.assertEqual(report["annotation_hint"]["recovery_ref"], "github-actions://adp/run/recovered-20260701")
        self.assertFalse(validate_trial_recovery_report(report))

    def test_build_trial_recovery_evidence_blocks_dry_run_failure_notification(self) -> None:
        report = build_trial_recovery_evidence(
            failure_execution_report(notification=dry_run_notification()),
            recovery_execution_report(),
            generated_at="2026-07-01T05:45:00+10:00",
            failure_ref="github-actions://adp/run/failed-20260701",
            recovery_ref="github-actions://adp/run/recovered-20260701",
        )

        self.assertEqual(report["status"], "blocked")
        self.assertIn("failure notification_report status must be sent", " ".join(report["blocking_reasons"]))
        self.assertFalse(validate_trial_recovery_report(report))

    def test_build_trial_recovery_evidence_blocks_missing_recovery_ref(self) -> None:
        report = build_trial_recovery_evidence(
            failure_execution_report(),
            recovery_execution_report(),
            generated_at="2026-07-01T05:45:00+10:00",
            failure_ref="github-actions://adp/run/failed-20260701",
        )

        self.assertEqual(report["status"], "blocked")
        self.assertIn("recovery_ref is required", " ".join(report["blocking_reasons"]))
        self.assertFalse(validate_trial_recovery_report(report))

    def test_build_trial_recovery_evidence_blocks_non_production_ready_recovery(self) -> None:
        report = build_trial_recovery_evidence(
            failure_execution_report(status="blocked"),
            recovery_execution_report(production_ready=False),
            generated_at="2026-07-01T05:45:00+10:00",
            failure_ref="github-actions://adp/run/failed-20260701",
            recovery_ref="github-actions://adp/run/recovered-20260701",
        )

        self.assertEqual(report["status"], "blocked")
        self.assertIn("recovery report must be production_evidence_ready", " ".join(report["blocking_reasons"]))
        self.assertFalse(validate_trial_recovery_report(report))

    def test_cli_build_trial_recovery_evidence_outputs_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            failure_path = Path(tmp) / "failure.json"
            recovery_path = Path(tmp) / "recovery.json"
            failure_path.write_text(json.dumps(failure_execution_report(), ensure_ascii=False), encoding="utf-8")
            recovery_path.write_text(json.dumps(recovery_execution_report(), ensure_ascii=False), encoding="utf-8")
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                result = main(
                    [
                        "build-trial-recovery-evidence",
                        "--failure-execution",
                        str(failure_path),
                        "--recovery-execution",
                        str(recovery_path),
                        "--generated-at",
                        "2026-07-01T05:45:00+10:00",
                        "--failure-ref",
                        "github-actions://adp/run/failed-20260701",
                        "--recovery-ref",
                        "github-actions://adp/run/recovered-20260701",
                        "--json",
                    ]
                )

        payload = json.loads(buffer.getvalue())
        self.assertEqual(result, 0)
        self.assertEqual(payload["model_id"], TRIAL_RECOVERY_MODEL_ID)
        self.assertTrue(payload["recovery_drill_verified"])


if __name__ == "__main__":
    unittest.main()
