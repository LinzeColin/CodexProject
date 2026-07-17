import copy
import unittest

from KMFA.tools import v015_s13_p3_action_priority as action


class TestV015S13P3ActionPriority(unittest.TestCase):
    def test_ranking_contract_is_complete_and_balanced(self) -> None:
        summary = action.validate_ranking_contract(action.ranking_contract())
        self.assertEqual(summary["factor_count"], 6)
        self.assertEqual(summary["weight_total_bps"], 10000)
        self.assertEqual(summary["score_range_bps"], [0, 10000])

    def test_candidate_ranking_is_explainable_and_advisory_only(self) -> None:
        result = action.rank_action_candidate(action.sample_candidates()[0])
        self.assertEqual(result["state"], "ELIGIBLE")
        self.assertEqual(len(result["factor_explanations"]), 6)
        self.assertIsInstance(result["priority_score_bps"], int)
        self.assertTrue(result["advisory_only"])
        self.assertFalse(result["automatic_execution_allowed"])

    def test_hard_gate_and_stale_data_cannot_be_hidden_by_score(self) -> None:
        blocked = action.rank_action_candidate(action.sample_candidates()[-1])
        self.assertEqual(blocked["state"], "BLOCKED_BY_HARD_GATE")
        self.assertIsNone(blocked["priority_score_bps"])
        stale = copy.deepcopy(action.sample_candidates()[0])
        stale["freshness"] = "STALE"
        result = action.rank_action_candidate(stale)
        self.assertEqual(result["state"], "INSUFFICIENT_DATA")
        self.assertIsNone(result["priority_score_bps"])

    def test_low_confidence_is_kept_for_review_not_focus(self) -> None:
        low = action.rank_action_candidate(action.sample_candidates()[-2])
        self.assertEqual(low["state"], "REQUIRES_REVIEW")
        self.assertFalse(low["focus_eligible"])

    def test_ranking_is_deterministic_and_tie_safe(self) -> None:
        first = action.rank_actions(action.sample_candidates())
        second = action.rank_actions(action.sample_candidates())
        self.assertEqual(first, second)
        tied = action.sample_candidates()[:2]
        tied[1]["factors"] = copy.deepcopy(tied[0]["factors"])
        ranked = action.rank_actions(tied)
        self.assertEqual([row["candidate_id"] for row in ranked], sorted(row["candidate_id"] for row in tied))

    def test_focus_items_are_limited_to_three_to_five(self) -> None:
        result = action.select_focus_items(action.sample_candidates())
        self.assertEqual(result["selection_status"], "READY")
        self.assertEqual(result["focus_item_count"], 5)
        self.assertTrue(all(not item["automatic_execution_allowed"] for item in result["focus_items"]))
        self.assertLessEqual(result["focus_item_count"], 5)

    def test_focus_selection_does_not_invent_missing_items(self) -> None:
        result = action.select_focus_items(action.sample_candidates()[:2])
        self.assertEqual(result["selection_status"], "INSUFFICIENT_ELIGIBLE_ITEMS")
        self.assertEqual(result["focus_item_count"], 2)

    def test_focus_selection_rejects_card_flooding(self) -> None:
        with self.assertRaises(action.ActionPriorityError):
            action.select_focus_items(action.sample_candidates(), max_items=6)
        with self.assertRaises(action.ActionPriorityError):
            action.select_focus_items(action.sample_candidates(), max_items=True)

    def test_unknown_outcome_is_explicit_and_not_fact(self) -> None:
        record = action.build_recommendation_review(
            recommendation_id="REC-TEST-001",
            candidate_id="ACT-TEST-001",
            recommendation_text_zh="请负责人核对后决定。",
        )
        self.assertEqual(record["outcome_state"], "UNKNOWN")
        self.assertFalse(record["recommendation_written_as_fact"])
        self.assertFalse(record["automatic_parameter_change_allowed"])

    def test_known_outcome_requires_evidence(self) -> None:
        with self.assertRaises(action.ActionPriorityError):
            action.build_recommendation_review(
                recommendation_id="REC-TEST-002",
                candidate_id="ACT-TEST-002",
                recommendation_text_zh="公开模拟建议。",
                decision="ACCEPTED",
                outcome_state="POSITIVE",
            )

    def test_review_history_is_append_only(self) -> None:
        record = action.build_recommendation_review(
            recommendation_id="REC-TEST-003",
            candidate_id="ACT-TEST-003",
            recommendation_text_zh="公开模拟建议。",
        )
        history = []
        snapshot = copy.deepcopy(history)
        appended = action.append_review_record(history, record)
        self.assertEqual(history, snapshot)
        self.assertEqual(len(appended), 1)
        with self.assertRaises(action.ActionPriorityError):
            action.append_review_record(appended, record)

    def test_calibration_is_proposal_only(self) -> None:
        records = [
            action.build_recommendation_review(
                recommendation_id=f"REC-CAL-{index}",
                candidate_id=f"ACT-CAL-{index}",
                recommendation_text_zh="公开模拟建议。",
                decision="ACCEPTED",
                outcome_state="POSITIVE" if index < 3 else "NEGATIVE",
                outcome_evidence_refs=[f"PUBLIC-EVIDENCE-{index}"],
            )
            for index in range(4)
        ]
        proposal = action.build_calibration_proposal(records)
        self.assertEqual(proposal["status"], "PROPOSAL_ONLY")
        self.assertEqual(proposal["success_rate_bps"], 7500)
        self.assertFalse(proposal["automatic_parameter_change_allowed"])

    def test_missing_results_block_calibration(self) -> None:
        record = action.build_recommendation_review(
            recommendation_id="REC-UNKNOWN",
            candidate_id="ACT-UNKNOWN",
            recommendation_text_zh="公开模拟建议。",
        )
        proposal = action.build_calibration_proposal([record])
        self.assertEqual(proposal["status"], "INSUFFICIENT_DATA")
        self.assertIsNone(proposal["success_rate_bps"])

    def test_float_bool_private_and_bad_shape_are_rejected(self) -> None:
        for field_value in (1.5, True):
            row = copy.deepcopy(action.sample_candidates()[0])
            row["factors"]["IMPACT"] = field_value
            with self.assertRaises(action.ActionPriorityError):
                action.rank_action_candidate(row)
        private = copy.deepcopy(action.sample_candidates()[0])
        private["title_zh"] = "/Users/example/private"
        with self.assertRaises(action.ActionPriorityError):
            action.rank_action_candidate(private)
        missing = copy.deepcopy(action.sample_candidates()[0])
        missing["factors"].pop("IMPACT")
        with self.assertRaises(action.ActionPriorityError):
            action.rank_action_candidate(missing)

    def test_public_verification_has_no_failure_or_side_effect(self) -> None:
        verification = action.public_verification()
        self.assertEqual(verification["accounting"]["failed"], 0)
        self.assertEqual(verification["failed_checks"], [])
        self.assertEqual(verification["automatic_execution_count"], 0)
        self.assertEqual(verification["recommendation_fact_write_count"], 0)
        self.assertEqual(verification["automatic_parameter_change_count"], 0)
        self.assertEqual(verification["raw_root_access_count"], 0)
        self.assertEqual(verification["live_source_read_count"], 0)
        self.assertEqual(verification["real_business_action_count"], 0)


if __name__ == "__main__":
    unittest.main()
