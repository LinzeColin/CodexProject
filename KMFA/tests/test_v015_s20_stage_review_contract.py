from __future__ import annotations

import copy
import unittest

from KMFA.tools import v015_s20_stage_review_contract as contract


class S20StageReviewContractTests(unittest.TestCase):
    def test_integrated_review_closes_all_findings(self) -> None:
        value = contract.build_integrated_review()
        self.assertEqual(
            contract.validate_integrated_review(value),
            {
                "integration_binding_count": 44,
                "integration_binding_failed_count": 0,
                "review_finding_count": 2,
                "fixed_review_finding_count": 2,
                "open_review_finding_count": 0,
                "technical_audit_score": 20,
            },
        )

    def test_public_verification_accounting_is_exact(self) -> None:
        value = contract.validate_public_contract()
        self.assertEqual(value["accounting"], {"total": 239, "passed": 239, "failed": 0})
        self.assertEqual(value["failed_checks"], [])

    def test_review_fingerprint_tampering_is_rejected(self) -> None:
        value = contract.build_integrated_review()
        value["review_finding_count"] = 9
        with self.assertRaisesRegex(contract.StageReviewError, "FINGERPRINT"):
            contract.validate_integrated_review(value)

    def test_side_effect_claim_is_rejected(self) -> None:
        value = copy.deepcopy(contract.build_integrated_review())
        value.pop("review_fingerprint")
        value["github_upload_performed"] = True
        value["review_fingerprint"] = contract._fingerprint(value)
        with self.assertRaisesRegex(contract.StageReviewError, "CROSS_PHASE|SIDE_EFFECT"):
            contract.validate_integrated_review(value)

    def test_audit_is_complete(self) -> None:
        audit = contract.technical_audit()
        self.assertEqual(audit["total_score"], 20)
        self.assertEqual(audit["open_issue_count"], 0)
        self.assertEqual(len(audit["dimensions"]), 5)


if __name__ == "__main__":
    unittest.main()
