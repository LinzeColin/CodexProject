from __future__ import annotations

import unittest

from arxiv_daily_push.trial_start import REQUIRED_START_REF_KEYS, build_trial_start_gate, validate_trial_start_report

class TrialStartTests(unittest.TestCase):
    def test_required_refs_do_not_include_release_ref(self) -> None:
        self.assertNotIn("release_ref", REQUIRED_START_REF_KEYS)

    def test_trial_start_gate_does_not_require_release_delivery(self) -> None:
        report = build_trial_start_gate(
            generated_at="2026-07-01T04:00:00+10:00",
            preflight_report={"validator_id": "adp-production-preflight-v1", "status": "blocked", "production_run_allowed": False, "gates": [{"gate_id": "x", "passed": False, "blocking_reasons": ["x"]}], "blocking_reasons": ["x"], "secret_policy": {"secret_values_logged": False}},
            bootstrap_plan={"validator_id": "adp-trial-bootstrap-v1", "trial_bootstrap_ready": False, "checks": [{"check_id": "x", "passed": False, "blocking_reasons": ["x"]}], "blocking_reasons": ["x"]},
            scheduler_plan={"validator_id": "adp-production-scheduler-v1", "scheduler_contract_ready": False, "schedule_slots": [], "checks": [{"check_id": "x", "passed": False, "blocking_reasons": ["x"]}], "blocking_reasons": ["x"], "scheduled_production_enabled": False, "scheduled_run_enabled": False, "release_upload_enabled": False, "real_smtp_send_enabled": False, "secret_values_logged": False, "codex_auth_read": False},
            source_batch={},
            smtp_delivery_report={},
            confirm_start=True,
        )
        self.assertEqual(report["status"], "blocked")
        self.assertNotIn("release_ref", report["evidence_refs"])
        self.assertNotIn("Release delivery", " ".join(report["blocking_reasons"]))
        self.assertFalse(validate_trial_start_report(report))

if __name__ == "__main__":
    unittest.main()
