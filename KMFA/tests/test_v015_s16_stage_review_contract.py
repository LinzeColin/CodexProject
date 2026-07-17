from __future__ import annotations

import copy
import unittest

from KMFA.tools import v015_s16_stage_review_contract as contract


class S16StageReviewContractTests(unittest.TestCase):
    def test_integrated_review_closes_all_bindings_and_findings(self) -> None:
        value = contract.build_integrated_review()
        self.assertEqual(
            contract.validate_integrated_review(value),
            {
                "integration_binding_count": 45,
                "integration_binding_failed_count": 0,
                "review_finding_count": 3,
                "fixed_review_finding_count": 3,
                "open_review_finding_count": 0,
                "technical_audit_score": 19,
            },
        )

    def test_public_verification_has_exact_accounting(self) -> None:
        value = contract.validate_public_contract()
        self.assertEqual(
            value["accounting"], {"total": 240, "passed": 240, "failed": 0}
        )
        self.assertEqual(value["failed_checks"], [])

    def test_all_three_fix_markers_are_bound_to_live_html(self) -> None:
        html = contract.render_html()
        for markers in contract.FIX_MARKERS.values():
            for marker in markers:
                self.assertIn(marker, html)

    def test_fingerprint_tampering_is_rejected(self) -> None:
        value = contract.build_integrated_review()
        value["review_finding_count"] = 4
        with self.assertRaisesRegex(contract.StageReviewError, "FINGERPRINT"):
            contract.validate_integrated_review(value)

    def test_side_effect_claim_is_rejected(self) -> None:
        value = copy.deepcopy(contract.build_integrated_review())
        value.pop("review_fingerprint")
        value["github_upload_performed"] = True
        value["review_fingerprint"] = contract._fingerprint(value)
        with self.assertRaisesRegex(contract.StageReviewError, "CROSS_PHASE|SIDE_EFFECT"):
            contract.validate_integrated_review(value)

    def test_technical_audit_has_no_open_issue(self) -> None:
        audit = contract.technical_audit()
        self.assertEqual(audit["total_score"], 19)
        self.assertEqual(audit["maximum_score"], 20)
        self.assertEqual(audit["open_issue_count"], 0)
        self.assertEqual(
            {row["dimension"] for row in audit["dimensions"]},
            {"accessibility", "performance", "theming", "responsive", "anti_patterns"},
        )


if __name__ == "__main__":
    unittest.main()
