from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from arxiv_daily_push.cli import main
from arxiv_daily_push.trial_ops import (
    TRIAL_OPS_MODEL_ID,
    annotate_trial_operational_evidence,
    validate_trial_ops_report,
)


def trial_evidence_without_replay(days: int = 30) -> dict:
    daily_runs = []
    for day in range(1, days + 1):
        date = f"2026-07-{day:02d}"
        daily_runs.append(
            {
                "date": date,
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
        "scheduler": {
            "enabled": True,
            "target_local_time": "05:00",
            "health_check_time": "04:45",
            "manual_rerun_verified": True,
            "ref": "github-actions://adp/scheduler",
        },
        "release": {"private_release_verified": True, "ref": "github-release://adp/trial"},
        "email": {
            "real_smtp_verified": True,
            "recipient": "linzezhang35@gmail.com",
            "ref": "smtp://adp/trial",
        },
        "resource_pressure": {
            "disk_ok": True,
            "memory_ok": True,
            "cache_ok": True,
            "secrets_ok": True,
            "git_large_artifacts_ok": True,
            "ref": "resource-gate://adp/trial",
        },
        "weekly_monthly": {"weekly_replay_verified": False, "monthly_replay_verified": False, "ref": ""},
        "recovery": {"failure_recovery_drill_verified": False, "ref": ""},
    }


class TrialOpsTests(unittest.TestCase):
    def test_annotate_trial_ops_adds_weekly_monthly_and_recovery_evidence(self) -> None:
        report = annotate_trial_operational_evidence(
            trial_evidence_without_replay(),
            generated_at="2026-07-31T06:30:00+10:00",
            weekly_replay_verified=True,
            monthly_replay_verified=True,
            weekly_monthly_ref="github-release://adp/weekly-monthly-replay",
            recovery_drill_verified=True,
            recovery_ref="github-actions://adp/recovery-drill",
        )

        self.assertEqual(report["model_id"], TRIAL_OPS_MODEL_ID)
        self.assertEqual(report["status"], "pass")
        self.assertTrue(report["trial_evidence_updated"])
        self.assertTrue(report["accepted_for_production"])
        self.assertFalse(validate_trial_ops_report(report))
        self.assertTrue(report["trial_evidence"]["weekly_monthly"]["weekly_replay_verified"])
        self.assertTrue(report["trial_evidence"]["recovery"]["failure_recovery_drill_verified"])

    def test_annotate_trial_ops_blocks_verified_replay_without_ref(self) -> None:
        report = annotate_trial_operational_evidence(
            trial_evidence_without_replay(days=1),
            generated_at="2026-07-02T06:30:00+10:00",
            weekly_replay_verified=True,
        )

        self.assertEqual(report["status"], "blocked")
        self.assertFalse(report["trial_evidence_updated"])
        self.assertIn("weekly/monthly replay ref", " ".join(report["blocking_reasons"]))
        self.assertFalse(validate_trial_ops_report(report))

    def test_annotate_trial_ops_does_not_promote_string_false_flags(self) -> None:
        evidence = trial_evidence_without_replay(days=1)
        evidence["weekly_monthly"] = {
            "weekly_replay_verified": "false",
            "monthly_replay_verified": "false",
            "ref": "github-release://adp/weekly-monthly-replay",
        }
        report = annotate_trial_operational_evidence(
            evidence,
            generated_at="2026-07-02T06:30:00+10:00",
            recovery_drill_verified=True,
            recovery_ref="github-actions://adp/recovery-drill",
        )

        self.assertEqual(report["status"], "pass")
        self.assertFalse(report["trial_evidence"]["weekly_monthly"]["weekly_replay_verified"])
        self.assertFalse(report["trial_evidence"]["weekly_monthly"]["monthly_replay_verified"])

    def test_cli_annotate_trial_ops_evidence_outputs_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            evidence_path = Path(tmp) / "trial-evidence.json"
            evidence_path.write_text(json.dumps(trial_evidence_without_replay(), ensure_ascii=False), encoding="utf-8")
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                result = main(
                    [
                        "annotate-trial-ops-evidence",
                        "--path",
                        str(evidence_path),
                        "--generated-at",
                        "2026-07-31T06:30:00+10:00",
                        "--weekly-replay-verified",
                        "--monthly-replay-verified",
                        "--weekly-monthly-ref",
                        "github-release://adp/weekly-monthly-replay",
                        "--recovery-drill-verified",
                        "--recovery-ref",
                        "github-actions://adp/recovery-drill",
                        "--json",
                    ]
                )

        payload = json.loads(buffer.getvalue())
        self.assertEqual(result, 0)
        self.assertEqual(payload["model_id"], TRIAL_OPS_MODEL_ID)
        self.assertTrue(payload["trial_evidence_updated"])

    def test_cli_export_trial_ops_state_outputs_updated_evidence(self) -> None:
        report = annotate_trial_operational_evidence(
            trial_evidence_without_replay(days=1),
            generated_at="2026-07-02T06:30:00+10:00",
            recovery_drill_verified=True,
            recovery_ref="github-actions://adp/recovery-drill",
        )
        with tempfile.TemporaryDirectory() as tmp:
            report_path = Path(tmp) / "trial-ops-update.json"
            report_path.write_text(json.dumps(report), encoding="utf-8")
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                result = main(["export-trial-ops-state", "--ops-update", str(report_path), "--json"])

        payload = json.loads(buffer.getvalue())
        self.assertEqual(result, 0)
        self.assertEqual(payload["trial_id"], "adp-trial-202607")
        self.assertTrue(payload["recovery"]["failure_recovery_drill_verified"])

    def test_cli_export_trial_ops_state_blocks_unupdated_report(self) -> None:
        report = annotate_trial_operational_evidence(
            trial_evidence_without_replay(days=1),
            generated_at="2026-07-02T06:30:00+10:00",
        )
        with tempfile.TemporaryDirectory() as tmp:
            report_path = Path(tmp) / "trial-ops-update.json"
            report_path.write_text(json.dumps(report), encoding="utf-8")
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                result = main(["export-trial-ops-state", "--ops-update", str(report_path), "--json"])

        payload = json.loads(buffer.getvalue())
        self.assertEqual(result, 2)
        self.assertEqual(payload["status"], "blocked")
        self.assertIn("no operational evidence annotation requested", " ".join(payload["errors"]))


if __name__ == "__main__":
    unittest.main()
