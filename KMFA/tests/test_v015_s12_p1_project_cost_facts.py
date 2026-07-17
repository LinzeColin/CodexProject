from __future__ import annotations

import unittest

from KMFA.tools import v015_s12_p1_project_cost_facts as facts


class ProjectCostFactsTests(unittest.TestCase):
    def _income(self, record_id: str, *, layer: str = "CONTRACT", basis: str = "TAX_INCLUSIVE", amount: int = 100) -> dict:
        return {
            **facts._common(record_id, amount),
            "income_layer": layer,
            "amount_basis": basis,
        }

    def _cost(self, record_id: str, *, category: str = "LABOR", amount: int = 100) -> dict:
        return {**facts._common(record_id, amount), "cost_category": category}

    def test_contracts_cover_all_income_layers_cost_categories_and_traceability(self) -> None:
        contracts = facts.public_schema_contracts()
        self.assertEqual(tuple(contracts["income_fact"]["income_layers"]), facts.INCOME_LAYERS)
        self.assertEqual(tuple(contracts["cost_fact"]["cost_categories"]), facts.COST_CATEGORIES)
        self.assertEqual(tuple(contracts["cost_fact"]["traceability_fields"]), facts.TRACEABILITY_FIELDS)
        self.assertEqual(contracts["unallocated_cost_pool"]["money_tolerance_cents"], 0)
        self.assertFalse(contracts["income_fact"]["unknown_basis_combination_allowed"])
        self.assertFalse(contracts["income_fact"]["cross_layer_combination_allowed"])
        self.assertFalse(contracts["unallocated_cost_pool"]["dropped_cost_allowed"])
        self.assertFalse(contracts["unallocated_cost_pool"]["average_allocation_allowed"])

    def test_income_facts_remain_layered_and_known_same_scope_can_subtotal(self) -> None:
        ledger = facts.ProjectCostFactLedger()
        first = ledger.add_income_fact(self._income("REV-TEST-001", amount=101))
        second = ledger.add_income_fact(self._income("REV-TEST-002", amount=-1))
        settlement = ledger.add_income_fact(
            self._income("REV-TEST-003", layer="SETTLEMENT", basis="TAX_EXCLUSIVE", amount=90)
        )

        subtotal = ledger.combine_income_facts([first["fact_id"], second["fact_id"]])
        self.assertEqual(subtotal["amount_cents"], 100)
        self.assertEqual(subtotal["income_layer"], "CONTRACT")
        self.assertEqual(subtotal["amount_basis"], "TAX_INCLUSIVE")
        self.assertFalse(subtotal["cross_layer_merge_performed"])
        self.assertFalse(subtotal["tax_basis_conversion_performed"])
        with self.assertRaisesRegex(facts.ProjectCostFactError, "INCOME_SCOPE_MISMATCH"):
            ledger.combine_income_facts([first["fact_id"], settlement["fact_id"]])

    def test_unknown_or_mismatched_income_scope_never_merges(self) -> None:
        ledger = facts.ProjectCostFactLedger()
        unknown = ledger.add_income_fact(self._income("REV-UNKNOWN-TEST", basis="UNKNOWN"))
        inclusive = ledger.add_income_fact(self._income("REV-INCLUSIVE-TEST"))
        exclusive = ledger.add_income_fact(self._income("REV-EXCLUSIVE-TEST", basis="TAX_EXCLUSIVE"))
        other_period = self._income("REV-PERIOD-TEST")
        other_period["period_ref"] = "PERIOD-2026-08"
        period_fact = ledger.add_income_fact(other_period)

        self.assertFalse(unknown["merge_eligible"])
        self.assertIn("AMOUNT_BASIS_UNKNOWN", unknown["unresolved_reason_codes"])
        with self.assertRaisesRegex(facts.ProjectCostFactError, "UNKNOWN_INCOME_SCOPE"):
            ledger.combine_income_facts([unknown["fact_id"]])
        with self.assertRaisesRegex(facts.ProjectCostFactError, "INCOME_SCOPE_MISMATCH"):
            ledger.combine_income_facts([inclusive["fact_id"], exclusive["fact_id"]])
        with self.assertRaisesRegex(facts.ProjectCostFactError, "INCOME_SCOPE_MISMATCH"):
            ledger.combine_income_facts([inclusive["fact_id"], period_fact["fact_id"]])

    def test_costs_route_exactly_once_and_unknowns_enter_explicit_pool(self) -> None:
        ledger = facts.ProjectCostFactLedger()
        allocated = ledger.add_cost_fact(self._cost("COST-KNOWN-001", category="MATERIAL", amount=1_001))
        unknown_project = self._cost("COST-PROJECT-UNKNOWN", amount=202)
        unknown_project["project_ref"] = facts.UNRESOLVED
        pooled_project = ledger.add_cost_fact(unknown_project)
        pooled_category = ledger.add_cost_fact(self._cost("COST-CATEGORY-UNKNOWN", category="UNKNOWN", amount=303))
        unknown_period = self._cost("COST-PERIOD-UNKNOWN", category="WARRANTY", amount=-4)
        unknown_period["period_ref"] = facts.UNRESOLVED
        unknown_period["period_version"] = facts.UNRESOLVED
        pooled_period = ledger.add_cost_fact(unknown_period)

        self.assertEqual(allocated["allocation_status"], "ALLOCATED")
        self.assertEqual(pooled_project["allocation_status"], "UNALLOCATED")
        self.assertIn("PROJECT_UNRESOLVED", pooled_project["unallocated_reason_codes"])
        self.assertIn("CATEGORY_UNRESOLVED", pooled_category["unallocated_reason_codes"])
        self.assertIn("PERIOD_UNRESOLVED", pooled_period["unallocated_reason_codes"])
        self.assertTrue(all(not row["automatic_allocation_performed"] for row in ledger.unallocated_cost_pool))
        self.assertTrue(all(not row["average_allocation_performed"] for row in ledger.unallocated_cost_pool))
        self.assertTrue(all(not row["silent_classification_performed"] for row in ledger.unallocated_cost_pool))
        conservation = ledger.cost_conservation()
        self.assertEqual(conservation["input_cost_fact_count"], 4)
        self.assertEqual(conservation["allocated_cost_fact_count"], 1)
        self.assertEqual(conservation["unallocated_cost_pool_count"], 3)
        self.assertEqual(conservation["conservation_delta_cents"], 0)
        self.assertEqual(conservation["dropped_cost_fact_count"], 0)

    def test_conservation_holds_for_signed_integer_partitions(self) -> None:
        partitions = (
            (0, 0, 0),
            (1, 2, 3),
            (-5, 8, -3),
            (10**12, -(10**12 - 1), -1),
        )
        for case_index, amounts in enumerate(partitions, start=1):
            with self.subTest(amounts=amounts):
                ledger = facts.ProjectCostFactLedger()
                ledger.add_cost_fact(self._cost(f"COST-PROP-{case_index}-A", amount=amounts[0]))
                unknown_project = self._cost(f"COST-PROP-{case_index}-B", amount=amounts[1])
                unknown_project["project_ref"] = facts.UNRESOLVED
                ledger.add_cost_fact(unknown_project)
                ledger.add_cost_fact(
                    self._cost(f"COST-PROP-{case_index}-C", category="UNKNOWN", amount=amounts[2])
                )
                ledger.assert_cost_conservation()
                result = ledger.cost_conservation()
                self.assertEqual(result["input_cost_cents"], sum(amounts))
                self.assertEqual(result["conservation_delta_cents"], 0)
                self.assertEqual(result["dropped_cost_fact_count"], 0)

    def test_money_is_integer_cents_only(self) -> None:
        for value in (1.5, True, False, "100", None):
            with self.subTest(value=value):
                income = self._income("REV-MONEY-TEST")
                income["amount_cents"] = value
                with self.assertRaisesRegex(facts.ProjectCostFactError, "INTEGER_CENTS_REQUIRED"):
                    facts.ProjectCostFactLedger().add_income_fact(income)
                cost = self._cost("COST-MONEY-TEST")
                cost["amount_cents"] = value
                with self.assertRaisesRegex(facts.ProjectCostFactError, "INTEGER_CENTS_REQUIRED"):
                    facts.ProjectCostFactLedger().add_cost_fact(cost)

    def test_exact_replay_is_idempotent_and_changed_history_is_rejected(self) -> None:
        ledger = facts.ProjectCostFactLedger()
        income = self._income("REV-IDEMPOTENT-001")
        first = ledger.add_income_fact(income)
        replay = ledger.add_income_fact(dict(income))
        self.assertEqual(first, replay)
        self.assertEqual(len(ledger.income_facts), 1)
        with self.assertRaisesRegex(facts.ProjectCostFactError, "IMMUTABLE_EVENT_CONFLICT"):
            ledger.add_income_fact({**income, "amount_cents": 101})

        cost = self._cost("COST-IDEMPOTENT-001")
        ledger.add_cost_fact(cost)
        ledger.add_cost_fact(dict(cost))
        self.assertEqual(len(ledger.allocated_cost_facts), 1)
        self.assertEqual(ledger.cost_conservation()["input_cost_fact_count"], 1)
        with self.assertRaisesRegex(facts.ProjectCostFactError, "IMMUTABLE_EVENT_CONFLICT"):
            ledger.add_cost_fact({**cost, "cost_category": "MATERIAL"})

    def test_returned_facts_are_copies_and_cannot_mutate_ledger(self) -> None:
        ledger = facts.ProjectCostFactLedger()
        stored = ledger.add_cost_fact(self._cost("COST-COPY-001", amount=999))
        stored["amount_cents"] = 0
        view = ledger.allocated_cost_facts
        view[0]["amount_cents"] = -1
        self.assertEqual(ledger.cost_conservation()["input_cost_cents"], 999)
        self.assertEqual(ledger.allocated_cost_facts[0]["amount_cents"], 999)

    def test_private_material_and_unknown_category_are_rejected(self) -> None:
        private = self._cost("COST-PRIVATE-TEST")
        private["source_ref"] = "/Users/example/private"
        with self.assertRaisesRegex(facts.ProjectCostFactError, "PRIVATE_VALUE_REJECTED"):
            facts.ProjectCostFactLedger().add_cost_fact(private)
        with self.assertRaisesRegex(facts.ProjectCostFactError, "ENUM_INVALID"):
            facts.ProjectCostFactLedger().add_cost_fact(
                self._cost("COST-GUESSED-TEST", category="OTHER_GUESSED")
            )

    def test_public_verification_passes_without_raw_or_later_phase_work(self) -> None:
        result = facts.public_verification()
        self.assertEqual(result["accounting"], {"total": 63, "passed": 63, "failed": 0})
        self.assertEqual(result["failed_checks"], [])
        self.assertEqual(result["income_layer_count"], 5)
        self.assertEqual(result["cost_category_count"], 10)
        self.assertEqual(result["traceability_field_count"], 7)
        self.assertEqual(result["summary"]["income_fact_count"], 7)
        self.assertEqual(result["summary"]["allocated_cost_fact_count"], 10)
        self.assertEqual(result["summary"]["unallocated_cost_pool_count"], 3)
        self.assertEqual(result["summary"]["conservation_delta_cents"], 0)
        self.assertEqual(result["raw_root_access_count"], 0)
        self.assertEqual(result["live_source_read_count"], 0)
        self.assertFalse(result["formal_calculation_allowed"])


if __name__ == "__main__":
    unittest.main()
