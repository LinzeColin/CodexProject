from __future__ import annotations

import unittest

from arxiv_daily_push.trial import evaluate_trial_evidence, validate_trial_evidence_report


def evidence() -> dict:
    return {
        "trial_id": "adp-trial-test",
        "trial_ref": "artifact://trial/state",
        "period": {"expected_days": 2},
        "daily_runs": [
            {"date": "2026-07-01", "run_id": "r1", "source_id": "s1", "publication_id": "p1", "status": "succeeded", "scheduled_local_time": "05:00", "p0_claims_traceable": True, "text_degradation_path_verified": True, "duplicate_publication": False, "unsupported_claims_published": False, "failure_generated_misleading_content": False, "run_record_ref": "run://r1", "text_artifact_ref": "text-artifact://r1", "email_ref": "email://r1", "resource_gate_ref": "resource://r1"},
            {"date": "2026-07-02", "run_id": "r2", "source_id": "s2", "publication_id": "p2", "status": "succeeded", "scheduled_local_time": "05:00", "p0_claims_traceable": True, "text_degradation_path_verified": True, "duplicate_publication": False, "unsupported_claims_published": False, "failure_generated_misleading_content": False, "run_record_ref": "run://r2", "text_artifact_ref": "text-artifact://r2", "email_ref": "email://r2", "resource_gate_ref": "resource://r2"},
        ],
        "scheduler": {"enabled": True, "target_local_time": "05:00", "health_check_time": "04:45", "manual_rerun_verified": True, "ref": "scheduler://ok"},
        "text_artifacts": {"b1_text_artifacts_verified": True, "ref": "text-artifact://trial"},
        "email": {"real_smtp_verified": True, "recipient": "linzezhang35@gmail.com", "ref": "email://trial"},
        "resource_pressure": {"disk_ok": True, "memory_ok": True, "cache_ok": True, "secrets_ok": True, "git_large_artifacts_ok": True, "ref": "resource://trial"},
        "weekly_monthly": {"weekly_replay_verified": True, "monthly_replay_verified": True, "ref": "replay://trial"},
        "recovery": {"failure_recovery_drill_verified": True, "ref": "recovery://trial"},
    }

class TrialEvidenceTests(unittest.TestCase):
    def test_accepts_text_artifact_trial_evidence(self) -> None:
        report = evaluate_trial_evidence(evidence(), generated_at="2026-07-03T05:00:00+10:00")
        self.assertTrue(report["accepted_for_production"])
        self.assertIn("text_artifacts_verified", {gate["gate_id"] for gate in report["gates"]})
        self.assertFalse(validate_trial_evidence_report(report))

    def test_blocks_missing_text_artifact_ref(self) -> None:
        data = evidence()
        del data["daily_runs"][0]["text_artifact_ref"]
        report = evaluate_trial_evidence(data, generated_at="2026-07-03T05:00:00+10:00")
        self.assertFalse(report["accepted_for_production"])
        self.assertIn("text_artifact_ref", " ".join(report["blocking_reasons"]))

if __name__ == "__main__":
    unittest.main()
