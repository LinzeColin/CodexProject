from __future__ import annotations

import unittest

from KMFA.tools import v015_s09_p1_scope_rule_modeling as scope


class ScopeRuleModelingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.policy = scope.default_ledger_view_policy()
        self.dictionary = scope.default_difference_dictionary()

    def test_single_legal_ledger_and_five_views(self) -> None:
        checked = scope.validate_ledger_view_policy(self.policy)
        self.assertEqual(checked["legal_ledger_count"], 1)
        self.assertEqual({row["view_id"] for row in checked["views"]}, set(scope.VIEW_IDS))
        self.assertTrue(all(row["source_ledger_ref"] == checked["legal_ledger_ref"] for row in checked["views"]))
        self.assertTrue(all(row["independent_ledger"] is False for row in checked["views"]))

    def test_parallel_ledger_and_regulatory_bypass_fail_closed(self) -> None:
        for request, code in (
            ({"operation": "CREATE_PARALLEL_LEDGER"}, "PARALLEL_LEDGER_FORBIDDEN"),
            ({"operation": "BYPASS_STATUTORY_RECONCILIATION"}, "REGULATORY_EVASION_STOP"),
            ({"operation": "MUTATE_SOURCE_FOR_VIEW"}, "SOURCE_MUTATION_FORBIDDEN"),
        ):
            with self.subTest(request=request):
                with self.assertRaises(scope.ScopeRuleError) as caught:
                    scope.evaluate_view_boundary(request, self.policy)
                self.assertEqual(caught.exception.code, code)

    def test_read_only_view_requires_exact_registered_rule_version(self) -> None:
        result = scope.evaluate_view_boundary(
            {"operation": "READ_DERIVED_VIEW", "view_id": "FUNDS", "rule_version": "SCOPE-RULE-V1"},
            self.policy,
        )
        self.assertEqual(result["decision"], "ALLOWED_READ_ONLY_DERIVED_VIEW")
        self.assertFalse(result["independent_ledger_created"])
        with self.assertRaises(scope.ScopeRuleError) as caught:
            scope.evaluate_view_boundary(
                {"operation": "READ_DERIVED_VIEW", "view_id": "FUNDS", "rule_version": "STALE"},
                self.policy,
            )
        self.assertEqual(caught.exception.code, "VIEW_RULE_VERSION_REQUIRED")

    def test_difference_dictionary_has_required_explainable_fields(self) -> None:
        checked = scope.validate_difference_dictionary(self.dictionary)
        self.assertEqual({row["difference_type_code"] for row in checked["types"]}, set(scope.DIFFERENCE_TYPE_CODES))
        for row in checked["types"]:
            self.assertTrue(row["required_evidence_codes"])
            self.assertTrue(row["handling_rule_zh"])
            self.assertTrue(row["report_display_rule_zh"])
            self.assertFalse(row["silent_offset_allowed"])

    def test_unknown_and_incomplete_differences_require_confirmation(self) -> None:
        unknown = scope.classify_difference(
            difference_type_code="NOT_REGISTERED",
            amount_delta_cents=100,
            evidence_codes=("REVIEW_NOTE",),
            dictionary=self.dictionary,
        )
        self.assertEqual(unknown["state"], "UNKNOWN_REQUIRES_CONFIRMATION")
        self.assertFalse(unknown["adjustment_event_allowed"])
        incomplete = scope.classify_difference(
            difference_type_code="BAD_DEBT",
            amount_delta_cents=-100,
            evidence_codes=("RECEIVABLE_EVIDENCE",),
            dictionary=self.dictionary,
        )
        self.assertEqual(incomplete["state"], "EVIDENCE_INCOMPLETE_REQUIRES_CONFIRMATION")
        self.assertFalse(incomplete["adjustment_event_allowed"])

    def test_float_money_is_rejected(self) -> None:
        with self.assertRaises(scope.ScopeRuleError) as caught:
            scope.classify_difference(
                difference_type_code="UNBILLED",
                amount_delta_cents=scope.json.loads("1.25"),  # type: ignore[arg-type]
                evidence_codes=("CONTRACT_OR_DELIVERY", "PERIOD_BASIS"),
                dictionary=self.dictionary,
            )
        self.assertEqual(caught.exception.code, "INTEGER_CENTS_REQUIRED")

    def test_adjustment_requires_approval_and_can_be_reversed(self) -> None:
        ledger = scope.AdjustmentEventLedger(dictionary=self.dictionary)
        proposal = ledger.propose(
            adjustment_ref="ADJ-TEST-001",
            difference_type_code="UNBILLED",
            amount_delta_cents=500,
            affected_view_ids=("OPERATING_ANALYSIS",),
            reason_zh="模拟未开票期间差异。",
            evidence_codes=("CONTRACT_OR_DELIVERY", "PERIOD_BASIS"),
            valid_from="2026-01-01",
            valid_to="2026-12-31",
            actor_role="ANALYST",
            recorded_at="2026-07-15T17:00:00+10:00",
        )
        self.assertEqual(ledger.effective_adjustment(adjustment_ref="ADJ-TEST-001", on_date="2026-07-15")["status"], "PENDING_APPROVAL")
        approval = ledger.approve(
            proposal_event_ref=proposal["event_ref"],
            actor_role="FINANCE_REVIEWER",
            recorded_at="2026-07-15T17:01:00+10:00",
        )
        self.assertEqual(ledger.effective_adjustment(adjustment_ref="ADJ-TEST-001", on_date="2026-07-15")["status"], "ACTIVE")
        ledger.reverse(
            approval_event_ref=approval["event_ref"],
            actor_role="OWNER",
            recorded_at="2026-07-15T17:02:00+10:00",
        )
        self.assertEqual(ledger.effective_adjustment(adjustment_ref="ADJ-TEST-001", on_date="2026-07-15")["status"], "REVERSED")

    def test_high_risk_adjustment_needs_high_risk_approver(self) -> None:
        ledger = scope.AdjustmentEventLedger(dictionary=self.dictionary)
        proposal = ledger.propose(
            adjustment_ref="ADJ-TEST-002",
            difference_type_code="BAD_DEBT",
            amount_delta_cents=-500,
            affected_view_ids=("OPERATING_ANALYSIS", "FUNDS"),
            reason_zh="模拟坏账审批边界。",
            evidence_codes=("RECEIVABLE_EVIDENCE", "RECOVERY_ASSESSMENT", "APPROVAL_BASIS"),
            valid_from="2026-01-01",
            valid_to="2026-12-31",
            actor_role="ANALYST",
            recorded_at="2026-07-15T17:00:00+10:00",
        )
        with self.assertRaises(scope.ScopeRuleError) as caught:
            ledger.approve(
                proposal_event_ref=proposal["event_ref"],
                actor_role="FINANCE_REVIEWER",
                recorded_at="2026-07-15T17:01:00+10:00",
            )
        self.assertEqual(caught.exception.code, "HIGH_RISK_APPROVAL_REQUIRED")
        self.assertEqual(len(ledger.events), 1)

    def test_event_replay_is_exact_and_source_ledger_is_immutable(self) -> None:
        acceptance = scope.synthetic_acceptance_cases()
        self.assertTrue(acceptance["adjustment_event_roundtrip_exact"])
        self.assertTrue(acceptance["direct_ledger_mutation_rejected"])
        self.assertTrue(acceptance["source_snapshot_unchanged"])
        self.assertEqual(acceptance["raw_root_access_count"], 0)


if __name__ == "__main__":
    unittest.main()
