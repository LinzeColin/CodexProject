from __future__ import annotations

import copy
import unittest

from KMFA.tools import v015_s14_p1_information_architecture as p1
from KMFA.tools import v015_s14_p2_design_system as p2
from KMFA.tools import v015_s14_p3_language_content as p3
from KMFA.tools import v015_s14_stage_review_contract as review


class V015S14StageReviewContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.result = review.build_integrated_review()

    def test_all_eighty_four_checks_pass(self) -> None:
        verification = review.public_verification()
        self.assertEqual(verification["accounting"], {"total": 84, "passed": 84, "failed": 0})
        self.assertEqual(verification["failed_checks"], [])

    def test_navigation_screen_and_theme_bindings_are_exact(self) -> None:
        summary = review.validate_integrated_review(self.result)
        self.assertEqual(summary["navigation_binding_count"], 7)
        self.assertEqual(summary["screen_binding_count"], 6)
        self.assertEqual(summary["theme_binding_count"], 2)
        self.assertEqual(summary["integration_binding_count"], 15)
        self.assertEqual(list(p1.NAV_ITEMS), list(p2.NAV_ITEMS))
        self.assertEqual(list(p2.NAV_ITEMS), list(p3.NAV_ITEMS))
        self.assertEqual(p2.THEMES, p3.THEMES)

    def test_six_page_types_have_routes_previous_task_and_next_step(self) -> None:
        routes = self.result["route_evidence"]
        self.assertEqual(routes["canonical_screen_count"], 6)
        self.assertEqual(routes["missing_route_count"], 0)
        self.assertEqual(routes["page_type_mismatch_count"], 0)
        self.assertEqual(routes["navigation_dead_end_count"], 0)
        self.assertEqual(set(review.CANONICAL_SCREEN_ROUTES), set(p1.PAGE_TYPES))

    def test_page_numbers_bind_exact_integer_or_null_values(self) -> None:
        numbers = self.result["number_binding_evidence"]
        self.assertEqual(numbers["key_number_binding_count"], 3)
        self.assertEqual(numbers["focus_amount_binding_count"], 3)
        self.assertEqual(numbers["key_number_mismatch_count"], 0)
        self.assertEqual(numbers["focus_amount_mismatch_count"], 0)
        self.assertEqual(numbers["float_storage_count"], 0)

    def test_plain_chinese_default_and_collapsed_professional_detail(self) -> None:
        scan = self.result["language_scan_evidence"]
        self.assertEqual(scan["forbidden_term_hit_count"], 0)
        self.assertEqual(scan["forbidden_ai_copy_hit_count"], 0)
        self.assertEqual(scan["machine_pattern_hit_count"], 0)
        self.assertTrue(scan["professional_details_collapsed_by_default"])

    def test_tampered_binding_and_fingerprint_are_rejected(self) -> None:
        fingerprint = copy.deepcopy(self.result)
        fingerprint["integration_binding_count"] = 14
        with self.assertRaisesRegex(review.StageReviewError, "REVIEW_FINGERPRINT_MISMATCH"):
            review.validate_integrated_review(fingerprint)

        binding = copy.deepcopy(self.result)
        binding["integration_bindings"][0]["status"] = "FAIL"
        payload = {key: copy.deepcopy(value) for key, value in binding.items() if key != "review_fingerprint"}
        binding["review_fingerprint"] = review._fingerprint(payload)
        with self.assertRaisesRegex(review.StageReviewError, "REVIEW_CROSS_PHASE_MISMATCH"):
            review.validate_integrated_review(binding)

    def test_review_is_deterministic_and_has_no_external_side_effect(self) -> None:
        self.assertEqual(self.result, review.build_integrated_review())
        for key in ("raw_root_access_count", "live_source_read_count", "network_request_count", "real_business_action_count"):
            self.assertEqual(self.result[key], 0)
        self.assertFalse(self.result["github_upload_performed"])
        self.assertFalse(self.result["app_reinstall_performed"])
        self.assertFalse(self.result["s15_started"])


if __name__ == "__main__":
    unittest.main()
