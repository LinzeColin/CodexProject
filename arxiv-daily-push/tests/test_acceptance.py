from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from arxiv_daily_push.acceptance import AcceptanceError, build_acceptance_package, validate_acceptance_package
from arxiv_daily_push.handoff import build_handoff
from arxiv_daily_push.pipeline import run_daily_dry_run


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

    def test_acceptance_can_pass_with_explicit_operational_evidence(self) -> None:
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

        self.assertTrue(package["accepted_for_production"])
        self.assertEqual(package["production_acceptance_status"], "pass")
        self.assertFalse(package["blocking_reasons"])
        self.assertFalse(validate_acceptance_package(package))

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
