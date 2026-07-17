from __future__ import annotations

import unittest

from KMFA.tools import v015_s17_p1_project_list as project_list
from KMFA.tools import v015_s17_p2_project_detail as detail


class ProjectDetailTests(unittest.TestCase):
    def test_source_contract_matches_all_three_roadmap_tasks(self) -> None:
        value = detail.source_contract()
        self.assertEqual(value["roadmap_phase_id"], "S17-P2")
        self.assertEqual(value["task_ids"], ["S17P2T01", "S17P2T02", "S17P2T03"])
        self.assertEqual(
            value["acceptance_zh"],
            ["一页可回答项目是否赚钱及为什么。", "合计与引擎一致。", "返回保留上下文。"],
        )
        self.assertIn("图表与表格金额不一致失败。", value["stop_conditions_zh"])

    def test_overview_answers_profitability_before_professional_codes(self) -> None:
        value = detail.project_detail(project_id="PUB-PROJ-001")
        overview = value["overview"]
        self.assertEqual(overview["profit_verdict_zh"], "项目目前赚钱")
        self.assertGreaterEqual(len(overview["profit_reason_zh"]), 3)
        self.assertTrue(overview["business_summary_first"])
        self.assertEqual(
            overview["revenue_cents"], overview["cost_cents"] + overview["gross_profit_cents"]
        )
        self.assertIn("professional_basis", overview)

    def test_management_view_reuses_project_list_facts_and_engine_is_zero_difference(self) -> None:
        row = project_list.project_catalog("demo-north", "2026-07")[2]
        value = detail.project_detail(project_id=row["project_id"])
        management = value["overview"]["professional_basis"]["margin_views"]["views"]["management"]
        golden = value["overview"]["professional_basis"]["golden_comparison"]
        self.assertEqual(management["revenue_cents"], row["revenue_cents"])
        self.assertEqual(management["cost_cents"], row["cost_cents"])
        self.assertTrue(golden["zero_difference_pass"])
        self.assertEqual(set(golden["differences_cents"].values()), {0})

    def test_cost_categories_table_chart_trend_and_engine_conserve_every_cent(self) -> None:
        for row in project_list.project_catalog("demo-north", "2026-07"):
            cost = detail.project_detail(project_id=row["project_id"])["cost"]
            self.assertEqual(len(cost["categories"]), 10)
            self.assertEqual(
                sum(item["actual_cents"] for item in cost["categories"])
                + cost["unallocated"]["amount_cents"],
                row["cost_cents"],
            )
            self.assertEqual(cost["table_total_cents"], cost["chart_total_cents"])
            self.assertEqual(cost["chart_total_cents"], cost["actual_total_cents"])
            self.assertEqual(cost["trend_total_cents"], cost["actual_total_cents"])
            self.assertEqual(cost["engine_difference_cents"], 0)
            self.assertEqual(cost["chart_table_difference_cents"], 0)
            self.assertTrue(cost["zero_difference_pass"])

    def test_budget_variance_and_unallocated_cost_are_visible_and_sourced(self) -> None:
        cost = detail.project_detail(project_id="PUB-PROJ-004")["cost"]
        self.assertEqual(
            cost["variance_total_cents"], cost["actual_total_cents"] - cost["budget_total_cents"]
        )
        self.assertGreater(cost["unallocated"]["amount_cents"], 0)
        self.assertIn("未归集池", cost["unallocated"]["reason_zh"])
        self.assertTrue(cost["unallocated"]["source_ref"])
        self.assertTrue(all(row["source_ref"] for row in cost["categories"]))

    def test_revenue_collection_variance_and_documents_have_distinct_jobs(self) -> None:
        value = detail.project_detail(project_id="PUB-PROJ-003")
        revenue = value["revenue_collection"]
        variance = value["variance"]
        documents = value["documents"]
        self.assertEqual(revenue["receivable_cents"], max(revenue["invoiced_cents"] - revenue["collected_cents"], 0))
        self.assertEqual(len(revenue["timeline"]), 4)
        self.assertEqual([row["variance_id"] for row in variance["rows"]], ["REVENUE", "COST", "GROSS_PROFIT"])
        self.assertEqual(documents["document_count"], 6)
        self.assertTrue(all("amount_cents" not in row for row in documents["documents"]))
        self.assertEqual(value["section_overlap_count"], 0)

    def test_navigation_keeps_list_scope_and_each_tab_is_addressable(self) -> None:
        context = {
            "risk": "HIGH",
            "group_by": "risk",
            "sort_by": "margin",
            "page": "2",
            "page_size": "4",
            "columns": "project,margin,risk",
        }
        for tab in detail.TAB_IDS:
            value = detail.project_detail(
                project_id="PUB-PROJ-001", active_tab=tab, list_context=context
            )
            self.assertEqual(value["active_tab"], tab)
            self.assertEqual(sum(item["active"] for item in value["tabs"]), 1)
            self.assertIn("risk=HIGH", value["navigation"]["return_url"])
            self.assertIn("page=2", value["navigation"]["return_url"])
            self.assertTrue(value["navigation"]["preserves_list_context"])

    def test_invalid_tab_project_and_cross_company_request_fail_closed(self) -> None:
        with self.assertRaises(detail.ProjectDetailError):
            detail.project_detail(project_id="NOT-IN-SCOPE")
        with self.assertRaises(detail.ProjectDetailError):
            detail.project_detail(project_id="../private")
        with self.assertRaises(detail.ProjectDetailError):
            detail.project_detail(project_id="PUB-PROJ-001", active_tab="all-at-once")

    def test_public_check_suite_passes(self) -> None:
        checks = detail.public_checks()
        self.assertEqual(len(checks), detail.PUBLIC_CHECK_COUNT)
        self.assertTrue(all(row["passed"] for row in checks))


if __name__ == "__main__":
    unittest.main()
