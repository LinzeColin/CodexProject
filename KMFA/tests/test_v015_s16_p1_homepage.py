from __future__ import annotations

import unittest

from KMFA.tools import v015_s16_p1_homepage as kernel


class HomepageKernelTests(unittest.TestCase):
    def test_source_contract_matches_current_taskpack_phase(self) -> None:
        contract = kernel.source_contract()
        self.assertEqual((contract["stage_id"], contract["roadmap_phase_id"]), ("S16", "S16-P1"))
        self.assertEqual(contract["task_ids"], ["S16P1T01", "S16P1T02", "S16P1T03"])
        self.assertEqual(len(contract["acceptance_zh"]), 3)
        self.assertEqual(len(contract["stop_conditions_zh"]), 3)

    def test_complete_snapshot_has_five_source_bound_metrics(self) -> None:
        value = kernel.homepage_snapshot()
        self.assertTrue(value["allowed"])
        self.assertEqual(value["overall_completeness"], "COMPLETE")
        self.assertEqual(len(value["summary_metrics"]), 5)
        for metric in value["summary_metrics"]:
            self.assertTrue(metric["source_zh"])
            self.assertTrue(metric["source_ref"].startswith("PUBLIC-SYNTHETIC:"))
            self.assertEqual(metric["cutoff_date"], "2026-07-15")
            self.assertEqual(metric["completeness"], "COMPLETE")

    def test_partial_snapshot_does_not_invent_complete_conclusion_or_zero(self) -> None:
        value = kernel.homepage_snapshot(data_state="partial")
        overdue = next(row for row in value["summary_metrics"] if row["metric_id"] == "OVERDUE_RECEIVABLE")
        self.assertEqual(value["overall_completeness"], "INCOMPLETE")
        self.assertFalse(value["complete_management_conclusion_available"])
        self.assertIsNone(overdue["primary_value"])
        self.assertEqual(overdue["display_zh"], "资料不足")
        self.assertEqual(value["missing_as_zero_count"], 0)

    def test_focus_has_exactly_five_items_and_one_action_each(self) -> None:
        items = kernel.homepage_snapshot()["focus_items"]
        self.assertEqual(len(items), 5)
        self.assertEqual(sum(row["primary_action_count"] for row in items), 5)
        self.assertTrue(all(row["primary_action_count"] == 1 for row in items))
        self.assertTrue(all(row["advisory_only"] for row in items))
        self.assertTrue(all(not row["automatic_execution_allowed"] for row in items))

    def test_focus_actions_use_known_routes(self) -> None:
        routes = {row["primary_action"]["route"] for row in kernel.homepage_snapshot()["focus_items"]}
        self.assertEqual(routes, {"/collections", "/funds", "/tax-policy", "/projects", "/data-update"})

    def test_trends_have_table_alternative_and_integer_values(self) -> None:
        trends = kernel.homepage_snapshot()["trend_series"]
        self.assertEqual(len(trends), 3)
        self.assertTrue(all(len(row["periods"]) == 4 for row in trends))
        self.assertTrue(all(row["table_alternative_available"] for row in trends))
        self.assertTrue(all(all(isinstance(value, int) for value in row["values_cents"]) for row in trends))

    def test_project_portfolio_is_small_readable_matrix(self) -> None:
        rows = kernel.homepage_snapshot()["project_portfolio"]
        self.assertEqual(len(rows), 4)
        self.assertEqual({row["status_zh"] for row in rows}, {"需要关注", "进展正常"})
        self.assertTrue(all(isinstance(row["revenue_cents"], int) for row in rows))
        self.assertTrue(all(isinstance(row["gross_margin_bps"], int) for row in rows))

    def test_company_and_period_change_values_deterministically(self) -> None:
        north = kernel.homepage_snapshot(company_id="demo-north", period="2026-07")
        south = kernel.homepage_snapshot(company_id="demo-south", period="2026-07")
        quarter = kernel.homepage_snapshot(company_id="demo-north", period="2026-Q2")
        self.assertNotEqual(north["summary_metrics"][0]["primary_value"], south["summary_metrics"][0]["primary_value"])
        self.assertNotEqual(north["summary_metrics"][0]["primary_value"], quarter["summary_metrics"][0]["primary_value"])
        self.assertEqual(north, kernel.homepage_snapshot(company_id="demo-north", period="2026-07"))

    def test_cross_company_access_fails_closed(self) -> None:
        value = kernel.homepage_snapshot(user_id="demo-finance", role_id="finance", company_id="demo-south")
        self.assertFalse(value["allowed"])
        self.assertEqual(value["reason_code"], "COMPANY_NOT_GRANTED")
        self.assertEqual(value["summary_metrics"], [])
        self.assertEqual(value["focus_items"], [])

    def test_invalid_data_state_is_rejected(self) -> None:
        with self.assertRaises(kernel.HomepageError):
            kernel.homepage_snapshot(data_state="unknown")

    def test_integer_formatters_preserve_missing_and_precision(self) -> None:
        self.assertEqual(kernel.format_wan_cents(None), "资料不足")
        self.assertEqual(kernel.format_wan_cents(684_250_000), "¥684.25 万")
        self.assertEqual(kernel.format_percent_bps(None), "资料不足")
        self.assertEqual(kernel.format_percent_bps(2_386), "23.86%")

    def test_no_real_action_or_fact_write(self) -> None:
        value = kernel.homepage_snapshot()
        self.assertEqual(value["automatic_execution_count"], 0)
        self.assertEqual(value["fact_layer_write_count"], 0)
        self.assertEqual(value["raw_write_count"], 0)
        self.assertEqual(value["real_business_action_count"], 0)
        self.assertFalse(value["real_business_conclusion_allowed"])

    def test_public_acceptance_checks_all_pass(self) -> None:
        contract = kernel.build_contract()
        self.assertEqual(contract["public_check_total"], 50)
        self.assertEqual(contract["public_check_pass_count"], 50)
        self.assertEqual(contract["public_check_failed_count"], 0)


if __name__ == "__main__":
    unittest.main()
