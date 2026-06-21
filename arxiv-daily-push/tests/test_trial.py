from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import date, timedelta
from pathlib import Path

from arxiv_daily_push.trial import evaluate_trial_evidence, validate_trial_evidence_report


def trial_evidence(days: int = 30) -> dict:
    start = date(2026, 7, 1)
    runs = []
    for offset in range(days):
        current = start + timedelta(days=offset)
        stamp = current.isoformat()
        runs.append(
            {
                "date": stamp,
                "run_id": f"adp-daily-{stamp}",
                "source_id": f"arxiv:2607.{offset:05d}",
                "publication_id": f"adp-publication-{stamp}",
                "status": "succeeded",
                "scheduled_local_time": "05:00",
                "p0_claims_traceable": True,
                "text_degradation_path_verified": True,
                "video_degradation_path_verified": True,
                "duplicate_publication": False,
                "unsupported_claims_published": False,
                "failure_generated_misleading_content": False,
                "run_record_ref": f"release://adp/2026-07/run-record-{stamp}.json",
                "release_ref": f"release://adp/2026-07/publication-{stamp}.json",
                "email_ref": f"smtp://message/adp-{stamp}",
                "resource_gate_ref": f"release://adp/2026-07/resource-{stamp}.json",
            }
        )
    return {
        "trial_id": "adp-trial-202607",
        "timezone": "Australia/Sydney",
        "trial_ref": "release://adp/30-day-trial-evidence.json",
        "period": {"start_date": "2026-07-01", "end_date": "2026-07-30", "expected_days": 30},
        "scheduler": {
            "enabled": True,
            "target_local_time": "05:00",
            "health_check_time": "04:45",
            "manual_rerun_verified": True,
            "ref": "release://adp/scheduler-rerun-evidence.json",
        },
        "release": {
            "private_release_verified": True,
            "ref": "release://adp/private-release-evidence.json",
        },
        "email": {
            "real_smtp_verified": True,
            "recipient": "linzezhang35@gmail.com",
            "ref": "smtp://adp/30-day-delivery-evidence",
        },
        "resource_pressure": {
            "disk_ok": True,
            "memory_ok": True,
            "cache_ok": True,
            "secrets_ok": True,
            "git_large_artifacts_ok": True,
            "ref": "release://adp/resource-pressure-evidence.json",
        },
        "weekly_monthly": {
            "weekly_replay_verified": True,
            "monthly_replay_verified": True,
            "ref": "release://adp/weekly-monthly-replay-evidence.json",
        },
        "recovery": {
            "failure_recovery_drill_verified": True,
            "ref": "release://adp/recovery-drill-evidence.json",
        },
        "daily_runs": runs,
    }


class TrialEvidenceTests(unittest.TestCase):
    def test_trial_evidence_passes_and_exports_operational_evidence(self) -> None:
        report = evaluate_trial_evidence(trial_evidence(), generated_at="2026-07-31T06:00:00+10:00")

        self.assertTrue(report["accepted_for_production"])
        self.assertEqual(report["production_evidence_status"], "pass")
        self.assertFalse(validate_trial_evidence_report(report))
        operational = report["operational_evidence"]
        self.assertEqual(operational["_validated_by"], "adp-trial-evidence-v1")
        self.assertTrue(operational["thirty_day_trial_passed"])
        self.assertTrue(operational["real_smtp_verified"])
        self.assertIn("trial-evidence:adp-trial-202607", operational["_trial_evidence_id"])

    def test_trial_evidence_blocks_missing_trial_days(self) -> None:
        report = evaluate_trial_evidence(trial_evidence(days=29), generated_at="2026-07-31T06:00:00+10:00")

        self.assertFalse(report["accepted_for_production"])
        self.assertEqual(report["production_evidence_status"], "blocked")
        self.assertIn("observed unique trial days 29 is below required 30", " ".join(report["blocking_reasons"]))
        self.assertFalse(report["operational_evidence"]["thirty_day_trial_passed"])

    def test_trial_evidence_blocks_duplicate_publication(self) -> None:
        evidence = trial_evidence()
        evidence["daily_runs"][1]["publication_id"] = evidence["daily_runs"][0]["publication_id"]
        report = evaluate_trial_evidence(evidence, generated_at="2026-07-31T06:00:00+10:00")

        self.assertFalse(report["accepted_for_production"])
        self.assertIn("publication_id duplicates", " ".join(report["blocking_reasons"]))

    def test_trial_evidence_blocks_untraceable_claims(self) -> None:
        evidence = trial_evidence()
        evidence["daily_runs"][0]["p0_claims_traceable"] = False
        report = evaluate_trial_evidence(evidence, generated_at="2026-07-31T06:00:00+10:00")

        self.assertFalse(report["accepted_for_production"])
        self.assertIn("p0_claims_traceable must be true", " ".join(report["blocking_reasons"]))

    def test_cli_evaluate_trial_outputs_json(self) -> None:
        from arxiv_daily_push.cli import main

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "trial.json"
            path.write_text(json.dumps(trial_evidence(), ensure_ascii=False), encoding="utf-8")
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                result = main(["evaluate-trial", "--path", str(path), "--generated-at", "2026-07-31T06:00:00+10:00", "--json"])

        payload = json.loads(buffer.getvalue())
        self.assertEqual(result, 0)
        self.assertEqual(payload["validator_id"], "adp-trial-evidence-v1")
        self.assertEqual(payload["production_evidence_status"], "pass")


if __name__ == "__main__":
    unittest.main()
