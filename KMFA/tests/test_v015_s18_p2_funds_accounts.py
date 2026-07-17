from __future__ import annotations

import unittest

from KMFA.tools import v015_s18_p2_funds_accounts as subject


class FundsAccountsTests(unittest.TestCase):
    def test_source_contract_matches_all_three_tasks(self) -> None:
        value = subject.source_contract()
        self.assertEqual(value["roadmap_phase_id"], "S18-P2")
        self.assertEqual(value["task_ids"], ["S18P2T01", "S18P2T02", "S18P2T03"])
        self.assertIn("账户不明不得汇总。", value["stop_conditions_zh"])
        self.assertIn("预测不得伪装成确定值。", value["stop_conditions_zh"])
        self.assertIn("付款按钮不得出现。", value["stop_conditions_zh"])

    def test_account_balances_reconcile_and_unknown_is_excluded(self) -> None:
        value = subject.account_facts()
        self.assertEqual(value["known_account_count"], 4)
        self.assertEqual(value["unknown_account_count"], 1)
        self.assertEqual(value["excluded_unknown_account_count"], 1)
        self.assertEqual(value["unknown_amount_in_total_cents"], 0)
        self.assertEqual(value["account_reconciliation_difference_cents"], 0)
        self.assertEqual(value["bank_reconciliation_difference_cents"], 0)
        self.assertEqual(value["total_available_cents"], sum(row["closing_cents"] for row in value["accounts"]))
        for row in value["accounts"]:
            self.assertEqual(row["opening_cents"] + row["inflow_cents"] - row["outflow_cents"], row["closing_cents"])
            self.assertTrue(row["masked_account"].startswith("****"))
            self.assertEqual(row["balance_date"], "2026-07-15")
            self.assertTrue(row["source_ref"].startswith("PUBLIC-SYNTHETIC:"))

    def test_all_companies_are_isolated_and_distinct(self) -> None:
        totals = set()
        for company_id in subject.COMPANY_IDS:
            value = subject.account_facts(company_id=company_id)
            self.assertEqual(value["cross_company_leak_count"], 0)
            self.assertTrue(all(row["company_id"] == company_id for row in value["accounts"]))
            totals.add(value["total_available_cents"])
        self.assertEqual(len(totals), 3)

    def test_forecast_separates_fact_plan_and_assumption(self) -> None:
        endings = set()
        for scenario_id in subject.SCENARIO_IDS:
            value = subject.cash_forecast(scenario_id=scenario_id)
            self.assertEqual(value["forecast_period_count"], 4)
            self.assertGreater(value["fact_event_count"], 0)
            self.assertGreater(value["plan_event_count"], 0)
            self.assertEqual(value["assumption_event_count"], 4)
            self.assertTrue(value["fact_plan_assumption_separated"])
            self.assertEqual(value["forecast_presented_as_certainty_count"], 0)
            self.assertEqual(value["assumption_fact_write_count"], 0)
            self.assertEqual(value["scenario_difference_cents"], 0)
            self.assertTrue(all(row["result_kind"] == "SCENARIO_NOT_CERTAINTY" for row in value["rows"]))
            endings.add(value["rows"][-1]["scenario_closing_cents"])
        self.assertEqual(len(endings), 3)

    def test_loan_plan_shows_maturity_interest_margin_and_gap_without_payment(self) -> None:
        value = subject.loan_funding_plan(scenario_id="collection_delay")
        self.assertEqual(value["loan_count"], 3)
        self.assertEqual(value["loan_due_within_90_days_count"], 2)
        self.assertGreater(value["total_principal_cents"], 0)
        self.assertGreater(value["total_estimated_interest_cents"], 0)
        self.assertGreater(value["total_margin_cents"], 0)
        self.assertGreater(value["maximum_funding_gap_cents"], 0)
        self.assertEqual(value["payment_execution_count"], 0)
        self.assertEqual(value["bank_operation_count"], 0)
        self.assertEqual(value["payment_button_count"], 0)
        self.assertTrue(all(not row["payment_execution_allowed"] for row in value["loans"]))

    def test_public_checks_all_pass(self) -> None:
        checks = subject.public_checks()
        self.assertEqual(len(checks), 61)
        self.assertTrue(all(row["status"] == "PASS" for row in checks))

    def test_invalid_company_period_or_scenario_fails_closed(self) -> None:
        with self.assertRaises(subject.FundsAccountsError):
            subject.funds_view(company_id="unknown")
        with self.assertRaises(subject.FundsAccountsError):
            subject.funds_view(period="1900")
        with self.assertRaises(subject.FundsAccountsError):
            subject.funds_view(scenario_id="certain")


if __name__ == "__main__":
    unittest.main()
