from __future__ import annotations

import copy
import json
import unittest

from KMFA.tools.v015_s08_p3_matching_quality_confirmation import (
    AffectedChainRecalculator,
    ImmutableFactStore,
    MatchDecisionLedger,
    MatchingControlError,
    build_confirmation_card,
    classify_match,
    default_matching_policy,
    synthetic_acceptance_cases,
    validate_matching_policy,
    validate_policy_change,
)


class MatchingQualityConfirmationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.cases = synthetic_acceptance_cases()

    def test_external_policy_defines_exact_three_states_and_ordered_thresholds(self) -> None:
        policy = validate_matching_policy(self.cases["matching_policy"])
        self.assertEqual((policy["auto_match_min_bps"], policy["candidate_review_min_bps"]), (8500, 7000))
        self.assertEqual(
            set(policy["state_labels_zh"]),
            {"AUTO_MATCH", "CANDIDATE_REVIEW", "MANUAL_CONFIRMATION"},
        )
        self.assertTrue(policy["threshold_change_requires_regression"])
        self.assertFalse(policy["silent_threshold_change_allowed"])

    def test_thresholds_route_automatic_candidate_and_manual_states(self) -> None:
        results = self.cases["classification_cases"]
        self.assertEqual(results["automatic"]["state"], "AUTO_MATCH")
        self.assertEqual(results["candidate"]["state"], "CANDIDATE_REVIEW")
        self.assertEqual(results["manual_low"]["state"], "MANUAL_CONFIRMATION")
        self.assertTrue(results["automatic"]["auto_merge_allowed"])
        self.assertFalse(results["candidate"]["auto_merge_allowed"])
        self.assertFalse(results["manual_low"]["auto_merge_allowed"])
        self.assertTrue(all(row["reason_details"] for row in results.values()))

    def test_hard_conflict_overrides_a_high_score(self) -> None:
        value = self.cases["classification_cases"]["manual_hard_conflict"]
        self.assertEqual(value["score_bps"], 9300)
        self.assertEqual(value["state"], "MANUAL_CONFIRMATION")
        self.assertEqual(value["reason_details"][0]["code"], "HARD_CONFLICT")
        self.assertFalse(value["auto_merge_allowed"])

    def test_invalid_threshold_order_fails_closed(self) -> None:
        policy = default_matching_policy()
        policy["candidate_review_min_bps"] = policy["auto_match_min_bps"]
        with self.assertRaisesRegex(MatchingControlError, "POLICY_THRESHOLD_ORDER_INVALID"):
            validate_matching_policy(policy)

    def test_threshold_change_requires_and_passes_explicit_regression(self) -> None:
        regression = self.cases["policy_regression"]
        self.assertEqual(regression["regression_case_count"], 5)
        self.assertEqual(regression["regression_pass_count"], 5)
        self.assertEqual(regression["regression_fail_count"], 0)
        self.assertTrue(regression["threshold_change_accepted"])
        self.assertTrue(self.cases["regression_required_enforced"])
        proposed = default_matching_policy()
        proposed.update(
            {
                "policy_ref": "POLICY-CHANGED",
                "policy_version": "2.0.0",
                "auto_match_min_bps": 8700,
                "candidate_review_min_bps": 7200,
            }
        )
        with self.assertRaisesRegex(MatchingControlError, "POLICY_REGRESSION_REQUIRED"):
            validate_policy_change(default_matching_policy(), proposed, [])

    def test_confirmation_cards_are_side_by_side_plain_chinese_and_source_safe(self) -> None:
        cards = self.cases["confirmation_cards"]
        self.assertEqual(len(cards), 2)
        for card in cards:
            self.assertEqual([row["名称"] for row in card["并排对比"]], ["当前记录", "候选记录"])
            self.assertTrue(card["相同点"])
            self.assertTrue(card["冲突点"])
            self.assertTrue(card["可能影响"])
            self.assertEqual(len(card["可选操作"]), 3)
            self.assertIn("不会修改原始资料或事实记录", card["资料保护说明"])
            text = json.dumps(card, ensure_ascii=False).lower()
            for term in ("hash", "sha-", "digest", "payload", "record_ref", "基点"):
                self.assertNotIn(term, text)

    def test_confirmation_card_does_not_modify_input_records(self) -> None:
        classification = self.cases["classification_cases"]["candidate"]
        current = {
            "项目名称": "示例甲",
            "合同编号": "示例合同甲",
            "公司主体": "示例主体",
            "往来方": "示例往来方",
            "时间说明": "同一期间",
            "金额说明": "金额接近",
        }
        candidate = {**current, "项目名称": "示例乙"}
        before = (copy.deepcopy(current), copy.deepcopy(candidate))
        build_confirmation_card(classification=classification, current_record=current, candidate_record=candidate)
        self.assertEqual((current, candidate), before)

    def test_decisions_are_append_only_persistent_reversible_and_rollbackable(self) -> None:
        events = self.cases["decision_events"]
        self.assertEqual(len(events), 4)
        self.assertEqual([row["sequence"] for row in events], [1, 2, 3, 4])
        self.assertEqual(events[1]["event_type"], "MATCH_DECISION_REVERSED")
        self.assertEqual(events[3]["event_type"], "MATCH_DECISION_ROLLBACK")
        self.assertEqual(events[3]["resulting_decision"], "CONFIRMED_MATCH")
        self.assertTrue(all(row["append_only"] and row["auditable"] and row["reversible"] for row in events))
        self.assertTrue(self.cases["decision_event_roundtrip_exact"])
        self.assertEqual(self.cases["decision_event_roundtrip_count"], 4)
        self.assertEqual(self.cases["current_decision_after_rollback"], "CONFIRMED_MATCH")
        ledger = MatchDecisionLedger(events)
        ledger.record_decision(
            case_ref="SYN-MATCH-OTHER",
            candidate_ref="SYN-CANDIDATE-OTHER",
            decision="DEFERRED",
            actor_role="REVIEWER",
            reason_zh="等待补充信息。",
            recorded_at="2026-07-15T10:05:00+10:00",
        )
        self.assertEqual(
            ledger.current_decision(case_ref="SYN-MATCH-CANDIDATE", candidate_ref="SYN-CANDIDATE-001"),
            "CONFIRMED_MATCH",
        )
        self.assertEqual(
            ledger.current_decision(case_ref="SYN-MATCH-OTHER", candidate_ref="SYN-CANDIDATE-OTHER"),
            "DEFERRED",
        )
        with self.assertRaisesRegex(MatchingControlError, "MATCH_PAIR_REQUIRED"):
            ledger.current_decision()

    def test_tampered_persisted_event_chain_is_rejected(self) -> None:
        rows = copy.deepcopy(self.cases["decision_events"])
        rows[1]["previous_event_ref"] = "WRONG"
        text = "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows)
        with self.assertRaisesRegex(MatchingControlError, "EVENT_CHAIN_INVALID"):
            MatchDecisionLedger.from_jsonl(text)
        rows = copy.deepcopy(self.cases["decision_events"])
        rows[0]["resulting_decision"] = "UNREGISTERED_DECISION"
        text = "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows)
        with self.assertRaisesRegex(MatchingControlError, "EVENT_CHAIN_INVALID"):
            MatchDecisionLedger.from_jsonl(text)
        rows = copy.deepcopy(self.cases["decision_events"])
        rows[3]["target_event_ref"] = rows[1]["event_ref"]
        text = "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows)
        with self.assertRaisesRegex(MatchingControlError, "EVENT_CHAIN_INVALID"):
            MatchDecisionLedger.from_jsonl(text)

    def test_every_control_event_triggers_affected_chain_recalculation(self) -> None:
        receipts = self.cases["recalculation_receipts"]
        events = self.cases["decision_events"]
        self.assertEqual(len(receipts), len(events))
        self.assertEqual(
            [row["trigger_event_ref"] for row in receipts],
            [row["event_ref"] for row in events],
        )
        self.assertTrue(all(row["status"] == "RECALCULATED" for row in receipts))
        self.assertTrue(all(row["affected_node_count"] == 3 for row in receipts))
        self.assertTrue(all(not row["fact_table_mutation_performed"] for row in receipts))

    def test_recalculation_without_recorded_control_event_fails(self) -> None:
        engine = AffectedChainRecalculator({"CASE-A": ["SUMMARY-A"]})
        with self.assertRaisesRegex(MatchingControlError, "CONTROL_EVENT_REQUIRED"):
            engine.recalculate({"case_ref": "CASE-A", "control_event_recorded": False})
        with self.assertRaisesRegex(MatchingControlError, "CONTROL_EVENT_REQUIRED"):
            engine.recalculate(
                {
                    "schema_version": "kmfa.v015.s08p3.match_decision_event.v1",
                    "event_type": "MATCH_DECISION_RECORDED",
                    "event_ref": "FORGED",
                    "sequence": 1,
                    "case_ref": "CASE-A",
                    "control_event_recorded": True,
                    "affected_chain_recalculation_required": True,
                    "raw_source_mutation_performed": False,
                    "fact_table_mutation_performed": True,
                }
            )

    def test_direct_fact_mutation_is_rejected_and_sources_remain_unchanged(self) -> None:
        store = ImmutableFactStore({"FACT-A": {"version": "V1"}})
        before = store.snapshot()
        with self.assertRaisesRegex(MatchingControlError, "DIRECT_FACT_TABLE_MUTATION_FORBIDDEN"):
            store.direct_update("FACT-A", {"version": "V2"})
        self.assertEqual(store.snapshot(), before)
        self.assertTrue(self.cases["direct_fact_mutation_rejected"])
        self.assertTrue(self.cases["fact_snapshot_unchanged"])
        self.assertTrue(self.cases["source_snapshot_unchanged"])
        self.assertEqual(self.cases["raw_root_access_count"], 0)

    def test_boolean_score_is_rejected(self) -> None:
        with self.assertRaisesRegex(MatchingControlError, "SCORE_OUT_OF_RANGE"):
            classify_match(
                case_ref="CASE-BOOL",
                score_bps=True,
                matched_points_zh=["项目名称一致"],
                conflict_points_zh=[],
                impact_zh="影响项目归属。",
                policy=default_matching_policy(),
            )


if __name__ == "__main__":
    unittest.main()
