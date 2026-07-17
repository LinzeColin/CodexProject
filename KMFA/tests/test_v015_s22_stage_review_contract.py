from __future__ import annotations

import unittest

from KMFA.tools import v015_s22_stage_review_contract as contract


class Stage22ReviewContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.payload = contract.integrated_review()

    def test_all_cross_phase_bindings_pass(self) -> None:
        self.assertEqual(self.payload["integration_binding_count"], 48)
        self.assertEqual(self.payload["integration_binding_failed_count"], 0)
        self.assertTrue(self.payload["stage_acceptance_ready"])

    def test_findings_are_real_and_closed(self) -> None:
        self.assertEqual(len(contract.REVIEW_FINDINGS), 4)
        self.assertTrue(
            all(
                row["status"] == "FIXED_VALIDATED"
                and not row["blocks_stage_acceptance"]
                for row in contract.REVIEW_FINDINGS
            )
        )

    def test_live_fixture_backs_up_current_notification_and_audit(self) -> None:
        fixture = contract.end_to_end_fixture()
        datasets = fixture["backup_payload"]["datasets"]
        self.assertEqual(set(datasets), {"PRIVATE_DERIVED", "CONFIGURATION", "AUDIT_EVENTS"})
        self.assertEqual(datasets["PRIVATE_DERIVED"]["source"], "LIVE_RUNTIME")
        self.assertEqual(datasets["PRIVATE_DERIVED"]["notification_event_count"], 2)
        self.assertGreaterEqual(datasets["AUDIT_EVENTS"]["security_event_count"], 6)
        self.assertFalse(fixture["backup_contains_secret"])

    def test_review_does_not_advance_taskpack_or_release(self) -> None:
        self.assertEqual(self.payload["taskpack_phase_count_delta"], 0)
        self.assertEqual(self.payload["taskpack_task_count_delta"], 0)
        self.assertEqual(
            (
                self.payload["raw_root_access_count"],
                self.payload["external_network_request_count"],
                self.payload["github_upload_count"],
                self.payload["app_reinstall_count"],
            ),
            (0, 0, 0, 0),
        )
        self.assertFalse(self.payload["s23_started"])


if __name__ == "__main__":
    unittest.main()
