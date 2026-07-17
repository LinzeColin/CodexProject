from __future__ import annotations

import copy
import unittest

from KMFA.tools import v015_s13_p2_business_health_model as p2
from KMFA.tools import v015_s13_stage_review_contract as review


class V015S13StageReviewContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.result = review.build_integrated_review()

    def test_all_seventy_two_checks_pass(self) -> None:
        verification = review.public_verification()
        self.assertEqual(verification["accounting"], {"total": 72, "passed": 72, "failed": 0})
        self.assertEqual(verification["failed_checks"], [])

    def test_health_sources_bind_exact_registered_indicators(self) -> None:
        self.assertEqual(self.result["source_binding_count"], 7)
        self.assertEqual(len(self.result["health_result"]["dimension_results"]), 6)
        for candidate in self.result["health_action_candidates"]:
            self.assertTrue(candidate["source_refs"][0].startswith("S13-P2:HEALTH-"))
            self.assertTrue(any(ref.startswith("S13-P1:IND-") for ref in candidate["source_refs"]))
            self.assertTrue(candidate["source_fingerprint"].startswith("sha256:"))

    def test_six_candidates_produce_five_human_focus_items(self) -> None:
        self.assertEqual(len(self.result["health_action_candidates"]), 6)
        self.assertEqual(len(self.result["ranked_actions"]), 6)
        self.assertEqual(self.result["focus_selection"]["focus_item_count"], 5)
        self.assertEqual(self.result["focus_selection"]["selection_status"], "READY")
        self.assertTrue(all(not row["automatic_execution_allowed"] for row in self.result["focus_selection"]["focus_items"]))

    def test_unknown_outcomes_do_not_write_facts_or_parameters(self) -> None:
        self.assertEqual(len(self.result["recommendation_reviews"]), 5)
        self.assertTrue(all(row["outcome_state"] == "UNKNOWN" for row in self.result["recommendation_reviews"]))
        self.assertTrue(all(not row["recommendation_written_as_fact"] for row in self.result["recommendation_reviews"]))
        self.assertEqual(self.result["calibration_proposal"]["status"], "INSUFFICIENT_DATA")
        self.assertFalse(self.result["calibration_proposal"]["automatic_parameter_change_allowed"])

    def test_hard_gate_and_stale_states_propagate_to_actions(self) -> None:
        hard = p2.synthetic_observations()
        hard[5]["hard_gate_passed"] = False
        hard[5]["hard_gate_reason_zh"] = "公开测试触发硬门禁。"
        hard_result = review.build_integrated_review(hard)
        blocked = next(row for row in hard_result["ranked_actions"] if row["candidate_id"] == "ACT-S13-REVIEW-06")
        self.assertEqual(blocked["state"], "BLOCKED_BY_HARD_GATE")
        self.assertIsNone(blocked["priority_score_bps"])
        self.assertNotIn(blocked["candidate_id"], {row["candidate_id"] for row in hard_result["focus_selection"]["focus_items"]})

        stale = p2.synthetic_observations()
        stale[0]["freshness_age_days"] = 30
        stale_result = review.build_integrated_review(stale)
        insufficient = next(row for row in stale_result["ranked_actions"] if row["candidate_id"] == "ACT-S13-REVIEW-01")
        self.assertEqual(insufficient["state"], "INSUFFICIENT_DATA")
        self.assertIsNone(insufficient["priority_score_bps"])

    def test_tampered_health_and_action_bindings_are_rejected(self) -> None:
        health = copy.deepcopy(self.result["health_result"])
        health["overall_score_bps"] += 1
        with self.assertRaisesRegex(review.StageReviewError, "HEALTH_FINGERPRINT_MISMATCH"):
            review.build_health_action_candidates(health)

        tampered = copy.deepcopy(self.result)
        tampered["health_action_candidates"][0]["source_refs"][0] = "S13-P2:HEALTH-TAMPERED"
        tampered["review_fingerprint"] = review._fingerprint({key: copy.deepcopy(value) for key, value in tampered.items() if key != "review_fingerprint"})
        with self.assertRaisesRegex(review.StageReviewError, "REVIEW_CROSS_PHASE_MISMATCH"):
            review.validate_integrated_review(tampered)

    def test_review_is_deterministic_and_public_only(self) -> None:
        self.assertEqual(self.result, review.build_integrated_review())
        self.assertEqual(self.result["raw_root_access_count"], 0)
        self.assertEqual(self.result["live_source_read_count"], 0)
        self.assertEqual(self.result["real_business_action_count"], 0)
        self.assertFalse(self.result["github_upload_performed"])
        self.assertFalse(self.result["app_reinstall_performed"])


if __name__ == "__main__":
    unittest.main()
