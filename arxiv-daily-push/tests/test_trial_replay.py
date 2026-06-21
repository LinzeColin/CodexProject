from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from arxiv_daily_push.cli import main
from arxiv_daily_push.trial_replay import (
    TRIAL_REPLAY_MODEL_ID,
    build_trial_replay_evidence,
    validate_trial_replay_report,
)


def trial_evidence(days: int = 30) -> dict:
    daily_runs = []
    for day in range(1, days + 1):
        run_date = f"2026-07-{day:02d}"
        daily_runs.append(
            {
                "date": run_date,
                "run_id": f"daily-{day:02d}",
                "source_id": f"arxiv:2607.{day:05d}",
                "publication_id": f"pub-{day:02d}",
                "status": "succeeded",
                "scheduled_local_time": "05:00",
                "p0_claims_traceable": True,
                "text_degradation_path_verified": True,
                "video_degradation_path_verified": True,
                "duplicate_publication": False,
                "unsupported_claims_published": False,
                "failure_generated_misleading_content": False,
                "run_record_ref": f"run-record://daily-{day:02d}",
                "release_ref": f"github-release://adp/daily-{day:02d}",
                "email_ref": f"smtp://adp/daily-{day:02d}",
                "resource_gate_ref": f"resource-gate://adp/daily-{day:02d}",
            }
        )
    return {
        "trial_id": "adp-trial-202607",
        "timezone": "Australia/Sydney",
        "trial_ref": "github-release://adp/30-day-trial-evidence",
        "period": {"expected_days": days, "start_date": "2026-07-01", "end_date": f"2026-07-{days:02d}"},
        "daily_runs": daily_runs,
    }


class TrialReplayTests(unittest.TestCase):
    def test_build_trial_replay_evidence_passes_weekly_and_monthly(self) -> None:
        report = build_trial_replay_evidence(
            trial_evidence(),
            generated_at="2026-07-31T06:45:00+10:00",
            weekly_replay=True,
            monthly_replay=True,
            replay_ref="github-actions://adp/weekly-monthly-replay/20260731",
        )

        self.assertEqual(report["model_id"], TRIAL_REPLAY_MODEL_ID)
        self.assertEqual(report["status"], "pass")
        self.assertTrue(report["replay_evidence_verified"])
        self.assertTrue(report["weekly_replay_verified"])
        self.assertTrue(report["monthly_replay_verified"])
        self.assertEqual(report["coverage"]["longest_consecutive_days"], 30)
        self.assertEqual(
            report["annotation_hint"]["weekly_monthly_ref"],
            "github-actions://adp/weekly-monthly-replay/20260731",
        )
        self.assertFalse(validate_trial_replay_report(report))

    def test_build_trial_replay_evidence_blocks_monthly_without_full_coverage(self) -> None:
        report = build_trial_replay_evidence(
            trial_evidence(days=7),
            generated_at="2026-07-08T06:45:00+10:00",
            monthly_replay=True,
            replay_ref="github-actions://adp/monthly-replay/20260708",
        )

        self.assertEqual(report["status"], "blocked")
        self.assertFalse(report["replay_evidence_verified"])
        self.assertIn("monthly replay requires at least", " ".join(report["blocking_reasons"]))
        self.assertFalse(validate_trial_replay_report(report))

    def test_build_trial_replay_evidence_blocks_missing_durable_ref(self) -> None:
        report = build_trial_replay_evidence(
            trial_evidence(days=7),
            generated_at="2026-07-08T06:45:00+10:00",
            weekly_replay=True,
        )

        self.assertEqual(report["status"], "blocked")
        self.assertIn("replay_ref is required", " ".join(report["blocking_reasons"]))
        self.assertFalse(validate_trial_replay_report(report))

    def test_build_trial_replay_evidence_blocks_duplicate_daily_date(self) -> None:
        evidence = trial_evidence(days=8)
        evidence["daily_runs"][7]["date"] = "2026-07-07"
        report = build_trial_replay_evidence(
            evidence,
            generated_at="2026-07-09T06:45:00+10:00",
            weekly_replay=True,
            replay_ref="github-actions://adp/weekly-replay/20260709",
        )

        self.assertEqual(report["status"], "blocked")
        self.assertIn("duplicates", " ".join(report["blocking_reasons"]))
        self.assertFalse(validate_trial_replay_report(report))

    def test_cli_build_trial_replay_evidence_outputs_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            evidence_path = Path(tmp) / "trial-evidence.json"
            evidence_path.write_text(json.dumps(trial_evidence(), ensure_ascii=False), encoding="utf-8")
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                result = main(
                    [
                        "build-trial-replay-evidence",
                        "--path",
                        str(evidence_path),
                        "--generated-at",
                        "2026-07-31T06:45:00+10:00",
                        "--weekly-replay",
                        "--monthly-replay",
                        "--replay-ref",
                        "github-actions://adp/weekly-monthly-replay/20260731",
                        "--json",
                    ]
                )

        payload = json.loads(buffer.getvalue())
        self.assertEqual(result, 0)
        self.assertEqual(payload["model_id"], TRIAL_REPLAY_MODEL_ID)
        self.assertTrue(payload["replay_evidence_verified"])


if __name__ == "__main__":
    unittest.main()
