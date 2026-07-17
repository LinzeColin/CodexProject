from __future__ import annotations

import copy
import json
import unittest

from KMFA.tools import v015_s09_p2_conversion_reconciliation_engine as engine


class ConversionReconciliationEngineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.cases = engine.synthetic_acceptance_cases()

    def test_conversion_is_exactly_balanced(self) -> None:
        result = self.cases["conversion"]
        self.assertEqual(result["status"], "BALANCED")
        self.assertEqual(result["conservation"]["input_total_cents"], 60000)
        self.assertEqual(result["conservation"]["approved_adjustment_total_cents"], 5000)
        self.assertEqual(result["conservation"]["output_total_cents"], 65000)
        self.assertEqual(result["conservation"]["residual_cents"], 0)

    def test_unbalanced_conversion_blocks(self) -> None:
        self.assertTrue(self.cases["imbalance_blocked"])
        with self.assertRaisesRegex(engine.ConversionReconciliationError, "CONVERSION_NOT_BALANCED"):
            engine.assert_conservation(
                input_total_cents=100,
                adjustment_total_cents=0,
                output_total_cents=99,
                explicit_difference_total_cents=0,
            )

    def test_float_money_is_rejected(self) -> None:
        self.assertTrue(self.cases["float_money_rejected"])
        with self.assertRaisesRegex(engine.ConversionReconciliationError, "INTEGER_CENTS_REQUIRED"):
            engine.assert_conservation(
                input_total_cents=json.loads("0.1"),
                adjustment_total_cents=0,
                output_total_cents=0,
                explicit_difference_total_cents=0,
            )

    def test_policy_binds_one_ledger_and_p1_contracts(self) -> None:
        policy = engine.validate_conversion_policy(engine.default_conversion_policy())
        self.assertEqual(policy["source_ledger_ref"], "LEGAL-LEDGER-PRIMARY")
        self.assertEqual(policy["p1_ledger_policy_ref"], "LEDGER-VIEW-POLICY-S09P1-V1")
        self.assertEqual(policy["p1_adjustment_protocol_ref"], "ADJUSTMENT-EVENT-PROTOCOL-S09P1-V1")
        self.assertFalse(policy["source_mutation_allowed"])

    def test_ambiguous_rule_is_rejected(self) -> None:
        policy = engine.default_conversion_policy()
        policy["rules"][1]["source_kind"] = "ACCOUNTING_REVENUE"
        with self.assertRaisesRegex(engine.ConversionReconciliationError, "AMBIGUOUS_CONVERSION_RULE"):
            engine.validate_conversion_policy(policy)

    def test_unapproved_adjustment_cannot_be_effective(self) -> None:
        batch = {
            "schema_version": engine.SOURCE_BATCH_SCHEMA,
            "batch_ref": "SYN-BATCH",
            "source_version": "SYN-V1",
            "legal_ledger_ref": "LEGAL-LEDGER-PRIMARY",
            "period_ref": "SYN-PERIOD",
            "rows": [
                {
                    "row_ref": "ROW-1",
                    "project_ref": "PROJECT-1",
                    "source_kind": "ACCOUNTING_REVENUE",
                    "amount_cents": 100,
                    "source_evidence_ref": "EVIDENCE-1",
                }
            ],
        }
        with self.assertRaisesRegex(engine.ConversionReconciliationError, "UNAPPROVED_ADJUSTMENT_EFFECTIVE"):
            engine.convert_ledger_to_operating_facts(
                source_batch=batch,
                adjustments=(
                    {
                        "event_ref": "EVENT-1",
                        "source_row_ref": "ROW-1",
                        "target_metric": "OPERATING_REVENUE",
                        "affected_view_id": "OPERATING_ANALYSIS",
                        "amount_delta_cents": 10,
                        "approval_status": "PENDING",
                        "effective": True,
                    },
                ),
            )

    def test_pending_adjustment_is_ignored_and_source_is_unchanged(self) -> None:
        result = self.cases["conversion"]
        self.assertEqual(result["ignored_adjustment_refs"], ["CTRL-EVENT-SYN-PENDING-001"])
        self.assertEqual(result["unapproved_effective_count"], 0)
        self.assertTrue(result["source_snapshot_unchanged"])
        self.assertEqual(result["source_snapshot_hash_before"], result["source_snapshot_hash_after"])

    def test_project_financial_chain_checks_four_source_types(self) -> None:
        result = self.cases["reconciliation"]
        self.assertTrue(result["complete_chain"])
        self.assertEqual(result["required_source_count"], 4)
        self.assertEqual(result["observed_source_count"], 4)
        self.assertEqual(result["exact_match_count"], 2)
        self.assertEqual(result["difference_count"], 2)

    def test_each_difference_has_source_amount_and_impact(self) -> None:
        for row in self.cases["reconciliation"]["differences"]:
            self.assertGreaterEqual(len(row["source_refs"]), 2)
            self.assertIsInstance(row["expected_amount_cents"], int)
            self.assertIsInstance(row["actual_amount_cents"], int)
            self.assertIsInstance(row["delta_cents"], int)
            self.assertTrue(row["affected_view_ids"])
            self.assertTrue(row["impact_zh"])
            self.assertTrue(row["manual_confirmation_required"])

    def test_opposite_differences_are_not_silently_netted(self) -> None:
        result = self.cases["reconciliation"]
        self.assertEqual(self.cases["opposite_delta_values"], [-1000, 1000])
        self.assertEqual(result["difference_delta_sum_cents"], 0)
        self.assertEqual(result["difference_count"], 2)
        self.assertEqual(result["silent_offset_count"], 0)
        self.assertTrue(result["opposite_differences_retained_separately"])

    def test_missing_source_routes_to_confirmation(self) -> None:
        result = self.cases["missing_source_reconciliation"]
        self.assertFalse(result["complete_chain"])
        self.assertEqual(result["status"], "REQUIRES_CONFIRMATION")
        missing = [row for row in result["differences"] if row["difference_type_code"] == "MISSING_SOURCE"]
        self.assertEqual(len(missing), 1)
        self.assertEqual(missing[0]["status"], "MISSING_SOURCE_REQUIRES_CONFIRMATION")

    def test_comparison_basis_mismatch_fails_closed(self) -> None:
        result = self.cases["reconciliation"]
        fact = {
            "fact_ref": result["fact_ref"],
            "project_ref": result["project_ref"],
            "metric": result["metric"],
            "amount_cents": 10,
            "source_ref": "FACT-SOURCE",
            "source_version": "V1",
            "comparison_basis": "BASIS-A",
        }
        observation = {
            "observation_ref": "OBS-1",
            "project_ref": result["project_ref"],
            "metric": result["metric"],
            "source_kind": "VOUCHER",
            "source_ref": "VOUCHER-SOURCE",
            "source_version": "V1",
            "comparison_basis": "BASIS-B",
            "amount_cents": 10,
            "evidence_codes": ["EVIDENCE"],
        }
        with self.assertRaisesRegex(engine.ConversionReconciliationError, "COMPARISON_BASIS_MISMATCH"):
            engine.reconcile_project_financial_chain(project_fact=fact, observations=(observation,))

    def test_same_source_rerun_resolves_full_chain_append_only(self) -> None:
        result = self.cases["rerun_resolved"]
        self.assertEqual(result["status"], "RERUN_RESOLVED")
        self.assertTrue(result["full_chain_rerun"])
        self.assertTrue(result["chain_state_consistent"])
        self.assertEqual(result["chain_layer_count"], 4)
        self.assertTrue(all(row["old_version_preserved"] for row in result["version_events"]))
        self.assertTrue(all(not row["old_version_overwritten"] for row in result["version_events"]))

    def test_persistent_same_source_mismatch_blocks_as_system_error(self) -> None:
        result = self.cases["rerun_persistent"]
        self.assertEqual(result["status"], "SYSTEM_ERROR_BLOCKED")
        self.assertTrue(result["formal_report_blocked"])
        self.assertTrue(result["chain_state_consistent"])
        self.assertEqual({row["new_version_status"] for row in result["version_events"]}, {"BLOCKED_SYSTEM_ERROR"})

    def test_cross_source_conflict_never_selects_a_winner(self) -> None:
        result = self.cases["cross_source_confirmation"]
        self.assertEqual(result["status"], "PENDING_HUMAN_CONFIRMATION")
        self.assertIsNone(result["automatic_winner"])
        self.assertIsNone(result["resolved_value"])
        self.assertFalse(result["auto_selection_performed"])
        self.assertTrue(result["formal_report_blocked"])

    def test_source_and_raw_are_never_mutated(self) -> None:
        self.assertTrue(self.cases["source_snapshot_unchanged"])
        self.assertTrue(self.cases["rerun_resolved"]["source_snapshot_unchanged"])
        self.assertTrue(self.cases["rerun_persistent"]["source_snapshot_unchanged"])
        self.assertFalse(self.cases["rerun_resolved"]["raw_source_mutation_performed"])
        self.assertEqual(self.cases["raw_root_access_count"], 0)

    def test_source_fixture_is_not_modified_by_acceptance_run(self) -> None:
        original = copy.deepcopy(self.cases["conversion"]["operating_facts"])
        replay = engine.synthetic_acceptance_cases()
        self.assertEqual(replay["conversion"]["operating_facts"], original)


if __name__ == "__main__":
    unittest.main()
