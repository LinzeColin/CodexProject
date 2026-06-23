from __future__ import annotations

import unittest

from arxiv_daily_push.trial_ledger import update_trial_evidence_ledger, validate_trial_ledger_update_report


def scheduled_report() -> dict:
    return {
        "validator_id": "adp-scheduled-execution-v1", "mode": "daily-run", "status": "succeeded", "exit_code": 0, "side_effect_policy": {"smtp_send_requested": True, "release_upload_requested": False, "secret_values_logged": False, "email_body_logged": False, "gh_output_logged": False, "video_attachment_allowed": False}, "production_evidence_ready": True,
        "daily_run_report": {"date": "2026-07-01", "run_id": "r1", "source_id": "s1", "publication_id": "p1", "status": "succeeded", "scheduled_local_time": "05:00", "p0_claims_traceable": True, "unsupported_claims_published": False, "failure_generated_misleading_content": False},
        "delivery_package": {"email_contains_chinese_lesson": True, "email_contains_candidate_queue_summary": True, "email_contains_html": True, "video_required": False, "video_generation_required": False, "release_required": False, "email_contains_video_link": False},
        "evidence_refs": {"daily_run_ref": "run://r1", "text_artifact_ref": "text-artifact://r1", "email_ref": "email://r1", "resource_gate_ref": "resource://r1"},
        "blocking_reasons": [],
    }

class TrialLedgerTests(unittest.TestCase):
    def test_updates_ledger_with_text_artifact_ref(self) -> None:
        report = update_trial_evidence_ledger(None, scheduled_report(), generated_at="2026-07-01T05:05:00+10:00", expected_days=1, text_degradation_path_verified=True)
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["daily_entry"]["text_artifact_ref"], "text-artifact://r1")
        self.assertTrue(report["trial_evidence"]["text_artifacts"]["b1_text_artifacts_verified"])
        self.assertFalse(validate_trial_ledger_update_report(report))

if __name__ == "__main__":
    unittest.main()
