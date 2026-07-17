from __future__ import annotations

import copy
import unittest

from KMFA.tools import v015_s09_p1_scope_rule_modeling as p1
from KMFA.tools import v015_s09_p2_conversion_reconciliation_engine as p2
from KMFA.tools import v015_s09_stage_review_contract as review


class V015S09StageReviewContractTests(unittest.TestCase):
    def source_batch(self) -> dict:
        return {
            "schema_version": p2.SOURCE_BATCH_SCHEMA,
            "batch_ref": "TEST-BATCH",
            "source_version": "TEST-V1",
            "legal_ledger_ref": "LEGAL-LEDGER-PRIMARY",
            "period_ref": "TEST-PERIOD",
            "rows": [
                {
                    "row_ref": "TEST-ROW",
                    "project_ref": "TEST-PROJECT",
                    "source_kind": "ACCOUNTING_REVENUE",
                    "amount_cents": 10000,
                    "source_evidence_ref": "TEST-EVIDENCE",
                }
            ],
        }

    def adjustment_ledger(self) -> p1.AdjustmentEventLedger:
        ledger = p1.AdjustmentEventLedger()
        proposal = ledger.propose(
            adjustment_ref="TEST-ADJ",
            difference_type_code="UNBILLED",
            amount_delta_cents=500,
            affected_view_ids=("OPERATING_ANALYSIS", "PROJECT_REALITY"),
            reason_zh="公开合成测试调整。",
            evidence_codes=("CONTRACT_OR_DELIVERY", "PERIOD_BASIS"),
            valid_from="2026-01-01",
            valid_to="2026-12-31",
            actor_role="ANALYST",
            recorded_at="2026-07-15T20:00:00+10:00",
        )
        ledger.approve(
            proposal_event_ref=proposal["event_ref"],
            actor_role="FINANCE_REVIEWER",
            recorded_at="2026-07-15T20:01:00+10:00",
        )
        return ledger

    def test_all_thirty_live_checks_pass(self) -> None:
        result = review.public_verification()
        self.assertEqual(result["accounting"], {"total": 30, "passed": 30, "failed": 0})

    def test_p2_cannot_accept_an_unbound_active_adjustment(self) -> None:
        with self.assertRaisesRegex(review.StageReviewError, "ADJUSTMENT_BINDING_SET_MISMATCH"):
            review.convert_with_bound_adjustments(
                source_batch=self.source_batch(),
                adjustment_events=self.adjustment_ledger().events,
                bindings=(),
                on_date="2026-07-15",
            )

    def test_adjustment_amount_and_approval_are_derived_from_p1(self) -> None:
        ledger = self.adjustment_ledger()
        result = review.convert_with_bound_adjustments(
            source_batch=self.source_batch(),
            adjustment_events=ledger.events,
            bindings=({"adjustment_ref": "TEST-ADJ", "source_row_ref": "TEST-ROW"},),
            on_date="2026-07-15",
        )
        binding = result["bindings"][0]
        self.assertEqual(binding["amount_delta_cents"], 500)
        self.assertEqual(binding["approval_event_ref"], ledger.events[-1]["event_ref"])
        self.assertEqual(result["conversion"]["operating_facts"][0]["amount_cents"], 10500)

    def test_tampered_reconciliation_cannot_reach_report(self) -> None:
        reconciliation = p2.synthetic_acceptance_cases()["reconciliation"]
        tampered = copy.deepcopy(reconciliation)
        tampered["differences"][0]["delta_cents"] += 1
        with self.assertRaisesRegex(review.StageReviewError, "DIFFERENCE_ARITHMETIC_INVALID"):
            review.build_bound_management_summary(tampered)

    def test_summary_cannot_omit_a_p2_decision_difference(self) -> None:
        cases = p2.synthetic_acceptance_cases()
        for case_name in ("reconciliation", "missing_source_reconciliation"):
            with self.subTest(case_name=case_name):
                reconciliation = cases[case_name]
                result = review.build_bound_management_summary(reconciliation)
                self.assertEqual(result["input_difference_count"], reconciliation["difference_count"])
                self.assertEqual(result["included_difference_count"], reconciliation["difference_count"])
                self.assertEqual(result["omitted_decision_difference_count"], 0)
                self.assertEqual(len(result["management_summary"]["items"]), reconciliation["difference_count"])

    def test_closure_rejects_cross_case_and_stale_version(self) -> None:
        reconciliation = p2.synthetic_acceptance_cases()["reconciliation"]
        state = review.new_bound_closure(
            reconciliation=reconciliation,
            difference_ref=reconciliation["differences"][0]["difference_ref"],
            initial_report_version="经营差异摘要-v1",
        )
        event = {
            "schema_version": "kmfa.v015.s09p3.difference_closure_event.v1",
            "event_ref": "TEST-CLOSURE-1",
            "difference_ref": reconciliation["differences"][1]["difference_ref"],
            "difference_fingerprint": state["difference_fingerprint"],
            "reconciliation_fingerprint": state["reconciliation_fingerprint"],
            "sequence": 1,
            "event_type": "DIFFERENCE_DISCOVERED",
            "actor_role": "SYSTEM",
            "occurred_at": "2026-07-15T20:10:00+10:00",
            "feedback_zh": "公开合成串单测试。",
            "difference_summary_zh": "公开合成差异。",
        }
        with self.assertRaisesRegex(review.StageReviewError, "CLOSURE_DIFFERENCE_MISMATCH"):
            review.append_bound_closure_event(state, event)
        event["difference_ref"] = state["difference_ref"]
        event["reconciliation_fingerprint"] = "sha256:" + "0" * 64
        with self.assertRaisesRegex(review.StageReviewError, "STALE_RECONCILIATION_REJECTED"):
            review.append_bound_closure_event(state, event)


if __name__ == "__main__":
    unittest.main()
