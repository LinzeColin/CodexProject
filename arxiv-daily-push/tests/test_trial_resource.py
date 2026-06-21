from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from arxiv_daily_push.cli import main
from arxiv_daily_push.production_preflight import PRODUCTION_PREFLIGHT_VALIDATOR_ID
from arxiv_daily_push.trial_resource import (
    TRIAL_RESOURCE_MODEL_ID,
    build_trial_resource_evidence,
    validate_trial_resource_report,
)


def trial_evidence(days: int = 30) -> dict:
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
                "resource_gate_ref": f"production-preflight://arxiv-daily-push/2026-07-{day:02d}",
            }
        )
    return {
        "trial_id": "adp-trial-202607",
        "timezone": "Australia/Sydney",
        "trial_ref": "github-release://adp/30-day-trial-evidence",
        "period": {"expected_days": days, "start_date": "2026-07-01", "end_date": f"2026-07-{days:02d}"},
        "daily_runs": daily_runs,
    }


def preflight_report(day: int, *, passed: bool = True) -> dict:
    date = f"2026-07-{day:02d}"
    gates = []
    for gate_id in ("required_commands", "secret_environment", "disk_pressure", "memory_pressure", "git_artifact_hygiene", "local_artifact_cache"):
        gates.append({"gate_id": gate_id, "passed": passed, "blocking_reasons": [] if passed else [f"{gate_id} blocked"]})
    return {
        "preflight_id": f"production-preflight:arxiv-daily-push:{date}",
        "validator_id": PRODUCTION_PREFLIGHT_VALIDATOR_ID,
        "project_id": "arxiv-daily-push",
        "generated_at": f"{date}T04:45:00+10:00",
        "timezone": "Australia/Sydney",
        "recipient": "linzezhang35@gmail.com",
        "status": "pass" if passed else "blocked",
        "production_run_allowed": passed,
        "gates": gates,
        "blocking_reasons": [] if passed else ["preflight blocked"],
        "secret_policy": {
            "secret_values_logged": False,
            "secret_names_only": True,
            "codex_auth_read": False,
        },
        "resource_evidence": {
            "resource_pressure_ok": passed,
            "resource_pressure_ok_ref": f"production-preflight://arxiv-daily-push/{date}" if passed else "",
        },
    }


class TrialResourceTests(unittest.TestCase):
    def test_build_trial_resource_evidence_passes_with_daily_preflight_refs(self) -> None:
        report = build_trial_resource_evidence(
            trial_evidence(),
            [preflight_report(day) for day in range(1, 31)],
            generated_at="2026-07-31T06:50:00+10:00",
            resource_ref="github-actions://adp/resource-telemetry/20260731",
        )

        self.assertEqual(report["model_id"], TRIAL_RESOURCE_MODEL_ID)
        self.assertEqual(report["status"], "pass")
        self.assertTrue(report["resource_pressure_verified"])
        self.assertEqual(report["coverage"]["matched_daily_resource_refs"], 30)
        self.assertEqual(report["annotation_hint"]["resource_ref"], "github-actions://adp/resource-telemetry/20260731")
        self.assertFalse(validate_trial_resource_report(report))

    def test_build_trial_resource_evidence_blocks_missing_matching_preflight(self) -> None:
        report = build_trial_resource_evidence(
            trial_evidence(),
            [preflight_report(day) for day in range(1, 30)],
            generated_at="2026-07-31T06:50:00+10:00",
            resource_ref="github-actions://adp/resource-telemetry/20260731",
        )

        self.assertEqual(report["status"], "blocked")
        self.assertIn("matched by preflight", " ".join(report["blocking_reasons"]))
        self.assertFalse(validate_trial_resource_report(report))

    def test_build_trial_resource_evidence_blocks_blocked_preflight(self) -> None:
        reports = [preflight_report(day) for day in range(1, 31)]
        reports[4] = preflight_report(5, passed=False)
        report = build_trial_resource_evidence(
            trial_evidence(),
            reports,
            generated_at="2026-07-31T06:50:00+10:00",
            resource_ref="github-actions://adp/resource-telemetry/20260731",
        )

        self.assertEqual(report["status"], "blocked")
        self.assertIn("must be a passing production preflight report", " ".join(report["blocking_reasons"]))
        self.assertFalse(validate_trial_resource_report(report))

    def test_build_trial_resource_evidence_blocks_missing_durable_ref(self) -> None:
        report = build_trial_resource_evidence(
            trial_evidence(),
            [preflight_report(day) for day in range(1, 31)],
            generated_at="2026-07-31T06:50:00+10:00",
        )

        self.assertEqual(report["status"], "blocked")
        self.assertIn("resource_ref is required", " ".join(report["blocking_reasons"]))
        self.assertFalse(validate_trial_resource_report(report))

    def test_build_trial_resource_evidence_blocks_lowered_expected_days(self) -> None:
        report = build_trial_resource_evidence(
            trial_evidence(days=7),
            [preflight_report(day) for day in range(1, 8)],
            generated_at="2026-07-08T06:50:00+10:00",
            resource_ref="github-actions://adp/resource-telemetry/20260708",
        )

        self.assertEqual(report["status"], "blocked")
        self.assertEqual(report["coverage"]["required_days"], 30)
        self.assertIn("at least 30 unique daily resource refs", " ".join(report["blocking_reasons"]))
        self.assertFalse(validate_trial_resource_report(report))

    def test_cli_build_trial_resource_evidence_outputs_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            evidence_path = Path(tmp) / "trial-evidence.json"
            evidence_path.write_text(json.dumps(trial_evidence(), ensure_ascii=False), encoding="utf-8")
            args = [
                "build-trial-resource-evidence",
                "--path",
                str(evidence_path),
                "--generated-at",
                "2026-07-31T06:50:00+10:00",
                "--resource-ref",
                "github-actions://adp/resource-telemetry/20260731",
                "--json",
            ]
            for day in range(1, 31):
                preflight_path = Path(tmp) / f"preflight-{day:02d}.json"
                preflight_path.write_text(json.dumps(preflight_report(day), ensure_ascii=False), encoding="utf-8")
                args.extend(["--preflight-report", str(preflight_path)])
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                result = main(args)

        payload = json.loads(buffer.getvalue())
        self.assertEqual(result, 0)
        self.assertEqual(payload["model_id"], TRIAL_RESOURCE_MODEL_ID)
        self.assertTrue(payload["resource_pressure_verified"])


if __name__ == "__main__":
    unittest.main()
