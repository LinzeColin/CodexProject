from __future__ import annotations

import unittest

from arxiv_daily_push.trial_recovery import build_trial_recovery_evidence, validate_trial_recovery_report


def execution(status: str, ready: bool) -> dict:
    return {
        "validator_id": "adp-scheduled-execution-v1",
        "mode": "daily-run",
        "status": status,
        "exit_code": 0 if status == "succeeded" else 2,
        "production_evidence_ready": ready,
        "blocking_reasons": [] if ready else ["smtp dry run"],
        "side_effect_policy": {
            "smtp_send_requested": True,
            "release_upload_requested": False,
            "secret_values_logged": False,
            "email_body_logged": False,
            "gh_output_logged": False,
            "video_attachment_allowed": False,
        },
        "notification_report": {
            "validator_id": "adp-smtp-delivery-v1",
            "status": "sent",
            "delivery_id": "smtp-delivery:test",
            "mail_key": "mail-key:test",
            "content_revision_id": "content-revision:test",
            "message_id": "<adp-test@arxiv-daily-push.local>",
            "recipient": "linzezhang35@gmail.com",
            "delivery_ref": "email://x",
            "smtp_config": {"secret_values_logged": False, "timeout_seconds": 30},
            "message": {
                "mail_key": "mail-key:test",
                "mail_key_components": {
                    "cycle_id": "2026-07-01",
                    "product_id": "M1",
                    "recipient": "linzezhang35@gmail.com",
                },
                "content_revision_id": "content-revision:test",
                "body_sha256": "abc123",
                "html_body_sha256": "",
                "body_logged": False,
                "message_id": "<adp-test@arxiv-daily-push.local>",
                "resend_policy": "same_mail_key_and_content_revision_retry_keeps_message_id; content_revision_change_requires_explicit_supersede_or_resend",
            },
        },
        "daily_run_report": {
            "date": "2026-07-01",
            "run_id": "r",
            "source_id": "s",
            "publication_id": "p",
            "scheduled_local_time": "05:00",
            "p0_claims_traceable": True,
            "unsupported_claims_published": False,
            "failure_generated_misleading_content": False,
        },
        "delivery_package": {
            "email_contains_chinese_lesson": True,
            "email_contains_candidate_queue_summary": True,
            "email_contains_html": True,
            "video_required": False,
            "video_generation_required": False,
            "release_required": False,
            "email_contains_video_link": False,
        },
        "evidence_refs": {
            "daily_run_ref": "run://r",
            "text_artifact_ref": "text-artifact://r",
            "email_ref": "email://r",
            "resource_gate_ref": "resource://r",
        },
    }

class TrialRecoveryTests(unittest.TestCase):
    def test_recovery_requires_text_artifact_ref(self) -> None:
        report = build_trial_recovery_evidence(execution("degraded", False), execution("succeeded", True), generated_at="2026-07-01T06:00:00+10:00", failure_ref="artifact://failure", recovery_ref="artifact://recovery")
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["evidence_refs"]["text_artifact_ref"], "text-artifact://r")
        self.assertFalse(validate_trial_recovery_report(report))

if __name__ == "__main__":
    unittest.main()
