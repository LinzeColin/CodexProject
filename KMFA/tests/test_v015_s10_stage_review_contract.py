from __future__ import annotations

import copy
import unittest

from KMFA.tools import v015_s10_stage_review_contract as review


class V015S10StageReviewContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.chain = review._synthetic_chain()

    def test_all_thirty_six_cross_part_checks_pass(self) -> None:
        self.assertEqual(review.public_verification()["accounting"], {"total": 36, "passed": 36, "failed": 0})

    def test_confirmation_cannot_be_reused_after_preview_changes(self) -> None:
        preview = copy.deepcopy(self.chain["preview"])
        preview["period"]["value"] = "2026-07"
        with self.assertRaisesRegex(review.StageReviewError, "P1_CONFIRMATION_CHAIN_INVALID"):
            review.bind_confirmed_file_adaptation(
                inspection=self.chain["inspection"],
                preview=preview,
                confirmation=self.chain["confirmation"],
                adaptation=self.chain["adaptation"],
                source_binding=self.chain["source_binding"],
            )

    def test_automatic_envelope_cannot_bypass_file_chain(self) -> None:
        self.assertFalse(self.chain["envelope"]["importable"])
        self.assertEqual(
            self.chain["envelope"]["required_processing_chain"],
            ["S10-P1", "S10-P2", "PRIVATE-ATOMIC-COMMIT"],
        )
        result = review.authorize_connector_file_commit(
            envelope=self.chain["envelope"], file_binding=self.chain["file_binding"]
        )
        self.assertEqual(result["authorization_status"], "READY_FOR_PRIVATE_ATOMIC_COMMIT")
        self.assertFalse(result["import_success_recorded"])

    def test_tax_has_one_exact_adapter_mapping(self) -> None:
        self.assertEqual(review.adapter_source_for_connector("TAX"), "TAX_EINVOICE")
        self.assertNotIn("CONTRACT_LEDGER", review.CONNECTOR_TO_ADAPTER.values())

    def test_scheduled_failure_never_claims_import_success(self) -> None:
        for outcome in ("NO_DATA", "TRANSIENT_FAILURE", "PERMANENT_FAILURE"):
            with self.subTest(outcome=outcome):
                result = review.scheduled_check_outcome(source_id="REDCIRCLE", attempt=1, outcome=outcome)
                self.assertFalse(result["import_success_recorded"])
                self.assertFalse(result["scheduled_import_committed"])
                self.assertFalse(result["checkpoint_advanced"])
                self.assertTrue(result["manual_import_available"])


if __name__ == "__main__":
    unittest.main()
