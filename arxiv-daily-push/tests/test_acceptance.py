from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import date, timedelta
from pathlib import Path

from arxiv_daily_push.acceptance import AcceptanceError, build_acceptance_package, validate_acceptance_package
from arxiv_daily_push.handoff import build_handoff
from arxiv_daily_push.pipeline import run_daily_dry_run
from arxiv_daily_push.trial import evaluate_trial_evidence


FIXTURE = Path(__file__).parent / "fixtures" / "pipeline_input.json"


def handoff_payload() -> dict:
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    pipeline = run_daily_dry_run(
        data["source_item"],
        data["claims"],
        run_id=data["run_id"],
        publication_id=data["publication_id"],
        date=data["date"],
        generated_at=data["generated_at"],
    )
    return build_handoff(pipeline, generated_at="2026-06-21T05:45:00+10:00")


def trial_report_payload() -> dict:
    start = date(2026, 7, 1)
    daily_runs = []
    for offset in range(30):
        current = (start + timedelta(days=offset)).isoformat()
        daily_runs.append(
            {
                "date": current,
                "run_id": f"adp-daily-{current}",
                "source_id": f"arxiv:2607.{offset:05d}",
                "publication_id": f"adp-publication-{current}",
                "status": "succeeded",
                "scheduled_local_time": "05:00",
                "p0_claims_traceable": True,
                "text_degradation_path_verified": True,
                "duplicate_publication": False,
                "unsupported_claims_published": False,
                "failure_generated_misleading_content": False,
                "run_record_ref": f"release://adp/run-record-{current}.json",
                "text_artifact_ref": f"artifact://adp/text-artifacts-{current}.json",
                "email_ref": f"smtp://message/adp-{current}",
                "resource_gate_ref": f"release://adp/resource-{current}.json",
            }
        )
    evidence = {
        "trial_id": "adp-trial-202607",
        "trial_ref": "release://adp/30-day-trial-evidence.json",
        "scheduler": {
            "enabled": True,
            "target_local_time": "05:00",
            "health_check_time": "04:45",
            "manual_rerun_verified": True,
            "ref": "release://adp/scheduler-rerun-evidence.json",
        },
        "text_artifacts": {"b1_text_artifacts_verified": True, "ref": "artifact://adp/text-artifacts-evidence.json"},
        "email": {"real_smtp_verified": True, "recipient": "linzezhang35@gmail.com", "ref": "smtp://adp/30-day-delivery-evidence"},
        "resource_pressure": {
            "disk_ok": True,
            "memory_ok": True,
            "cache_ok": True,
            "secrets_ok": True,
            "git_large_artifacts_ok": True,
            "ref": "release://adp/resource-pressure-evidence.json",
        },
        "weekly_monthly": {"weekly_replay_verified": True, "monthly_replay_verified": True, "ref": "release://adp/weekly-monthly.json"},
        "recovery": {"failure_recovery_drill_verified": True, "ref": "release://adp/recovery-drill.json"},
        "daily_runs": daily_runs,
    }
    return evaluate_trial_evidence(evidence, generated_at="2026-07-31T06:00:00+10:00")


class AcceptanceTests(unittest.TestCase):
    def test_acceptance_package_blocks_production_without_live_evidence(self) -> None:
        package = build_acceptance_package(handoff_payload(), generated_at="2026-06-21T06:00:00+10:00")

        self.assertEqual(package["dry_run_handoff_status"], "pass")
        self.assertEqual(package["production_acceptance_status"], "blocked")
        self.assertFalse(package["accepted_for_production"])
        self.assertTrue(package["no_claims"]["does_not_claim_30_day_trial"])
        self.assertIn("missing 30-day live trial evidence", " ".join(package["blocking_reasons"]))
        self.assertFalse(validate_acceptance_package(package))

    def test_acceptance_rejects_invalid_handoff(self) -> None:
        handoff = handoff_payload()
        handoff["email_transport_gate"]["real_smtp_send_enabled"] = True

        with self.assertRaises(AcceptanceError):
            build_acceptance_package(handoff, generated_at="2026-06-21T06:00:00+10:00")

    def test_acceptance_can_pass_with_validated_trial_report(self) -> None:
        package = build_acceptance_package(
            handoff_payload(),
            generated_at="2026-06-21T06:00:00+10:00",
            operational_evidence=trial_report_payload(),
        )

        self.assertTrue(package["accepted_for_production"])
        self.assertEqual(package["production_acceptance_status"], "pass")
        self.assertEqual(package["evidence_validator"], "adp-trial-evidence-v1")
        self.assertEqual(package["trial_evidence_id"], "trial-evidence:adp-trial-202607")
        self.assertFalse(package["blocking_reasons"])
        self.assertFalse(validate_acceptance_package(package))

    def test_acceptance_blocks_raw_refs_without_trial_report(self) -> None:
        evidence = {
            "thirty_day_trial_passed": True,
            "thirty_day_trial_passed_ref": "release://adp/30-day-trial.json",
            "scheduler_operational": True,
            "scheduler_operational_ref": "release://adp/scheduler-rerun-evidence.json",
            "release_upload_verified": True,
            "release_upload_verified_ref": "release://adp/private-release-evidence.json",
            "real_smtp_verified": True,
            "real_smtp_verified_ref": "release://adp/smtp-delivery-evidence.json",
            "resource_pressure_ok": True,
            "resource_pressure_ok_ref": "release://adp/resource-pressure-evidence.json",
        }
        package = build_acceptance_package(
            handoff_payload(),
            generated_at="2026-06-21T06:00:00+10:00",
            operational_evidence=evidence,
        )

        self.assertFalse(package["accepted_for_production"])
        self.assertEqual(package["production_acceptance_status"], "blocked")

    def test_acceptance_blocks_true_flags_without_evidence_refs(self) -> None:
        evidence = {
            "thirty_day_trial_passed": True,
            "scheduler_operational": True,
            "release_upload_verified": True,
            "real_smtp_verified": True,
            "resource_pressure_ok": True,
        }
        package = build_acceptance_package(
            handoff_payload(),
            generated_at="2026-06-21T06:00:00+10:00",
            operational_evidence=evidence,
        )

        self.assertFalse(package["accepted_for_production"])
        self.assertEqual(package["production_acceptance_status"], "blocked")
        self.assertIn("missing 30-day live trial evidence", " ".join(package["blocking_reasons"]))

    def test_validation_rejects_false_production_pass(self) -> None:
        package = build_acceptance_package(handoff_payload(), generated_at="2026-06-21T06:00:00+10:00")
        package["accepted_for_production"] = True
        package["production_acceptance_status"] = "pass"

        self.assertTrue(validate_acceptance_package(package))

    def test_cli_builds_acceptance_from_handoff_payload(self) -> None:
        from arxiv_daily_push.cli import main

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "handoff.json"
            path.write_text(json.dumps(handoff_payload(), ensure_ascii=False), encoding="utf-8")
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                result = main(["build-acceptance", "--path", str(path), "--generated-at", "2026-06-21T06:00:00+10:00", "--json"])

        payload = json.loads(buffer.getvalue())
        self.assertEqual(result, 0)
        self.assertEqual(payload["production_acceptance_status"], "blocked")


if __name__ == "__main__":
    unittest.main()
