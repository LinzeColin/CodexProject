from __future__ import annotations

import unittest

from KMFA.tools import v015_s23_stage_review_contract as contract


class Stage23ReviewContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.payload = contract.integrated_review()

    def test_all_cross_phase_bindings_pass(self) -> None:
        self.assertEqual(self.payload["integration_binding_count"], 40)
        self.assertEqual(self.payload["integration_binding_failed_count"], 0)
        self.assertTrue(self.payload["stage_acceptance_ready"])

    def test_findings_are_real_closed_and_limitations_are_explicit(self) -> None:
        self.assertEqual(len(contract.REVIEW_FINDINGS), 2)
        self.assertTrue(all(row["status"] == "FIXED_VALIDATED" and not row["blocks_stage_acceptance"] for row in contract.REVIEW_FINDINGS))
        self.assertEqual(len(contract.KNOWN_LIMITATIONS), 2)
        self.assertTrue(all(row["status"] == "CONTROLLED_NONBLOCKING" for row in contract.KNOWN_LIMITATIONS))

    def test_receipt_and_public_accounting_is_exact(self) -> None:
        self.assertEqual(self.payload["predecessor_phase_count"], 3)
        self.assertEqual(self.payload["predecessor_task_accepted_count"], 9)
        self.assertEqual(self.payload["predecessor_receipt_count"], 60)
        self.assertEqual(self.payload["predecessor_public_check_count"], 156)

    def test_review_does_not_advance_taskpack_or_release(self) -> None:
        self.assertEqual(self.payload["taskpack_phase_count_delta"], 0)
        self.assertEqual(self.payload["taskpack_task_count_delta"], 0)
        self.assertEqual((self.payload["raw_root_access_count"], self.payload["external_network_request_count"], self.payload["github_upload_count"], self.payload["app_reinstall_count"]), (0, 0, 0, 0))
        self.assertFalse(self.payload["s24_started"])


if __name__ == "__main__":
    unittest.main()
