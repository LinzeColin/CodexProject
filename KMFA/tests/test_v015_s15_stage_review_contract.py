from __future__ import annotations

import copy
import unittest

from KMFA.tools import v015_s15_stage_review_contract as contract


class S15StageReviewContractTests(unittest.TestCase):
    def test_integrated_review_closes_all_bindings_and_findings(self) -> None:
        value = contract.build_integrated_review()
        summary = contract.validate_integrated_review(value)
        self.assertEqual(summary["integration_binding_count"], 41)
        self.assertEqual(summary["integration_binding_failed_count"], 0)
        self.assertEqual(summary["review_finding_count"], 4)
        self.assertEqual(summary["fixed_review_finding_count"], 4)
        self.assertEqual(summary["open_review_finding_count"], 0)
        self.assertEqual(summary["design_audit_average_score"], 92)

    def test_public_verification_has_exact_accounting(self) -> None:
        value = contract.validate_public_contract()
        self.assertEqual(value["accounting"], {"total": 72, "passed": 72, "failed": 0})
        self.assertEqual(value["failed_checks"], [])

    def test_review_fix_markers_are_bound_to_the_integrated_page(self) -> None:
        html = contract.render_html()
        for tokens in contract.FIX_MARKERS.values():
            for token in tokens:
                self.assertIn(token, html)
        self.assertIn("@media (pointer:coarse)", html)
        self.assertIn("min-height:44px", html)

    def test_fingerprint_tampering_is_rejected(self) -> None:
        value = contract.build_integrated_review()
        value["route_count"] = 17
        with self.assertRaisesRegex(contract.StageReviewError, "FINGERPRINT"):
            contract.validate_integrated_review(value)

    def test_side_effect_claim_is_rejected_even_with_rebound_fingerprint(self) -> None:
        value = contract.build_integrated_review()
        value = copy.deepcopy(value)
        value.pop("review_fingerprint")
        value["github_upload_performed"] = True
        value["review_fingerprint"] = contract._fingerprint(value)
        with self.assertRaisesRegex(contract.StageReviewError, "CROSS_PHASE|SIDE_EFFECT"):
            contract.validate_integrated_review(value)

    def test_design_audit_covers_all_required_dimensions(self) -> None:
        audit = contract.design_audit()
        self.assertEqual(
            {row["dimension"] for row in audit["dimensions"]},
            {"accessibility", "performance", "theming", "responsive", "anti_patterns"},
        )
        self.assertGreaterEqual(audit["average_score"], 90)
        self.assertEqual(audit["open_blocking_issue_count"], 0)


if __name__ == "__main__":
    unittest.main()
