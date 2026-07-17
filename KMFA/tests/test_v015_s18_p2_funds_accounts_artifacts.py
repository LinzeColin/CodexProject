from __future__ import annotations

import json
import unittest

from KMFA.tools import build_v015_s18_p2_funds_accounts as builder


class FundsAccountsArtifactsTests(unittest.TestCase):
    def load(self, path):
        return json.loads(path.read_text(encoding="utf-8"))

    def test_expected_outputs_are_deterministic(self) -> None:
        builder.check_outputs()

    def test_account_contract_is_masked_sourced_and_reconciled(self) -> None:
        value = self.load(builder.ACCOUNT_CONTRACT_PATH)
        self.assertEqual(value["company_count"], 3)
        self.assertEqual(value["bank_count"], 3)
        self.assertEqual(value["known_account_count"], 4)
        self.assertEqual(value["unknown_account_count"], 1)
        self.assertEqual(value["excluded_unknown_account_count"], 1)
        self.assertTrue(value["all_account_identifiers_masked"])
        self.assertTrue(value["all_sources_explicit"])
        self.assertEqual(value["account_reconciliation_difference_cents"], 0)
        self.assertEqual(value["bank_reconciliation_difference_cents"], 0)
        self.assertEqual(value["unknown_amount_in_total_cents"], 0)
        self.assertEqual(value["cross_company_leak_count"], 0)

    def test_forecast_contract_never_masquerades_as_fact(self) -> None:
        value = self.load(builder.FORECAST_CONTRACT_PATH)
        self.assertEqual(value["scenario_count"], 3)
        self.assertEqual(value["forecast_period_count"], 4)
        self.assertTrue(value["all_scenarios_separate_fact_plan_assumption"])
        self.assertEqual(value["forecast_presented_as_certainty_count"], 0)
        self.assertEqual(value["assumption_fact_write_count"], 0)
        self.assertEqual(value["scenario_difference_cents"], 0)
        self.assertEqual(value["distinct_final_scenario_balance_count"], 3)
        self.assertIn("不是确定值", value["result_label_zh"])

    def test_funding_contract_has_no_execution_surface(self) -> None:
        value = self.load(builder.FUNDING_CONTRACT_PATH)
        self.assertEqual(value["loan_count"], 3)
        self.assertEqual(value["loan_due_within_90_days_count"], 2)
        self.assertEqual(value["funding_period_count"], 4)
        self.assertTrue(value["all_maturities_explicit"])
        self.assertGreater(value["total_estimated_interest_cents"], 0)
        self.assertGreater(value["total_margin_cents"], 0)
        self.assertGreater(value["maximum_funding_gap_cents"], 0)
        self.assertEqual(value["payment_execution_count"], 0)
        self.assertEqual(value["bank_operation_count"], 0)
        self.assertEqual(value["payment_button_count"], 0)

    def test_browser_and_human_evidence_exist(self) -> None:
        contract = self.load(builder.BROWSER_CONTRACT_PATH)
        self.assertEqual(contract["browser_flow_count"], 8)
        self.assertEqual(contract["visual_evidence_count"], 6)
        self.assertEqual(contract["minimum_touch_target_px"], 44)
        self.assertTrue(all(path.is_file() and path.stat().st_size > 10_000 for path in builder.SCREENSHOT_PATHS))
        for path in (builder.IMPLEMENTATION_REPORT_PATH, builder.USER_GUIDE_PATH, builder.TEST_RESULTS_PATH, builder.RISKS_ROLLBACK_PATH):
            self.assertTrue(path.is_file())
            self.assertGreater(len(path.read_text(encoding="utf-8")), 120)

    def test_manifest_follows_receipt_bound_acceptance(self) -> None:
        value = self.load(builder.MANIFEST_PATH)
        final, run_id, validation_head = builder.final_binding(builder.receipts())
        self.assertEqual(value["phase_acceptance_status"], "PASSED" if final else "PENDING_FINAL_VALIDATION")
        self.assertEqual(value["phase_task_accepted_count"], 3 if final else 0)
        self.assertEqual(value["overall_accepted_phase_count"], 51 if final else 50)
        self.assertTrue(value["s18_p2_started"])
        self.assertEqual(value["s18_p2_completed"], final)
        self.assertEqual(value["s18_p3_entry_allowed"], final)
        self.assertFalse(value["s18_p3_started"])
        self.assertEqual(value["validation_run_id"], run_id)
        self.assertEqual(value["validation_head"], validation_head)
        self.assertFalse(value["github_upload_performed"])
        self.assertFalse(value["app_reinstall_performed"])


if __name__ == "__main__":
    unittest.main()
