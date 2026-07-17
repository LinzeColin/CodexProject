from __future__ import annotations

import copy
import unittest

from KMFA.tools import v015_s08_p1_project_composite_identity as p1
from KMFA.tools import v015_s08_p2_business_entity_hierarchy as p2
from KMFA.tools import v015_s08_p3_matching_quality_confirmation as p3
from KMFA.tools import v015_s08_stage_review_contract as review


class S08StageReviewContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.p1_cases = p1.synthetic_acceptance_cases()["match_cases"]
        p2_cases = p2.synthetic_acceptance_cases()
        self.entity_assigned, self.entity_missing, _ = p2_cases["entity_assignment_cases"]
        self.accounts = p2_cases["account_resolution_cases"]
        self.counterparties = p2_cases["counterparty_resolution_cases"]
        self.policy = p3.default_matching_policy()

    def route(self, project, *, entity=None, account=None, counterparty=None):
        return review.route_match_for_confirmation(
            project_match=project,
            entity_assignment=entity or self.entity_assigned,
            account_resolution=account or self.accounts["same_entity_resolved"],
            counterparty_resolution=counterparty or self.counterparties["historical_name_resolved"],
            policy=self.policy,
        )

    def test_public_verification_passes_all_twenty_live_checks(self) -> None:
        result = review.public_verification()
        self.assertEqual(result["accounting"], {"total": 20, "passed": 20, "failed": 0})

    def test_low_coverage_high_score_cannot_bypass_p1_gate(self) -> None:
        project = self.p1_cases["low_coverage_fail_closed"]
        self.assertEqual(project["renormalized_similarity_bps"], 10000)
        routed = self.route(project)
        self.assertEqual(routed["p3_state"], "MANUAL_CONFIRMATION")
        self.assertFalse(routed["auto_merge_allowed"])

    def test_p2_fail_closed_results_cannot_become_automatic(self) -> None:
        project = self.p1_cases["missing_contract_renormalized"]
        missing_entity = self.route(project, entity=self.entity_missing)
        cross_entity = self.route(project, account=self.accounts["cross_entity_high_risk"])
        same_name = self.route(
            project, counterparty=self.counterparties["same_name_not_force_merged"]
        )
        for routed in (missing_entity, cross_entity, same_name):
            self.assertEqual(routed["p3_state"], "MANUAL_CONFIRMATION")
            self.assertFalse(routed["auto_merge_allowed"])
            self.assertFalse(routed["funds_aggregation_allowed"])

    def test_policy_threshold_drift_fails_closed(self) -> None:
        changed = copy.deepcopy(self.policy)
        changed["auto_match_min_bps"] = 8600
        with self.assertRaisesRegex(review.StageReviewError, "AUTO_THRESHOLD_MISMATCH"):
            review.route_match_for_confirmation(
                project_match=self.p1_cases["missing_contract_renormalized"],
                entity_assignment=self.entity_assigned,
                account_resolution=self.accounts["same_entity_resolved"],
                counterparty_resolution=self.counterparties["historical_name_resolved"],
                policy=changed,
            )

    def test_decision_and_recalculation_are_bound_to_exact_pair(self) -> None:
        route = self.route(self.p1_cases["same_name_time_amount_conflict"])
        ledger = p3.MatchDecisionLedger()
        recalculator = p3.AffectedChainRecalculator(
            {route["authority_record_ref"]: ["PROJECT-ASSIGNMENT", "REPORT-STATE"]}
        )
        binding = review.record_bound_decision_and_recalculate(
            route=route,
            ledger=ledger,
            recalculator=recalculator,
            decision="CONFIRMED_MATCH",
            actor_role="ROLE-DATA-STEWARD",
            reason_zh="公开合成案例确认属于同一项目。",
            recorded_at="2026-07-15T15:00:00+10:00",
        )
        self.assertTrue(binding["binding_exact"])
        self.assertTrue(binding["recalculation_completed"])
        foreign = p3.MatchDecisionLedger().record_decision(
            case_ref=route["authority_record_ref"],
            candidate_ref="OTHER-CANDIDATE",
            decision="DEFERRED",
            actor_role="ROLE-DATA-STEWARD",
            reason_zh="公开合成串单测试。",
            recorded_at="2026-07-15T15:01:00+10:00",
        )
        with self.assertRaisesRegex(review.StageReviewError, "MATCH_PAIR_MISMATCH"):
            review.bind_existing_decision_and_recalculate(
                route=route, event=foreign, recalculator=recalculator
            )


if __name__ == "__main__":
    unittest.main()
