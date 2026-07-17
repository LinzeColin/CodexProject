from __future__ import annotations

import csv
import io
import unittest

from KMFA.tools import v015_s16_p1_homepage as homepage
from KMFA.tools import v015_s17_p1_project_list as project_list


class ProjectListTests(unittest.TestCase):
    def test_source_contract_matches_all_three_roadmap_tasks(self) -> None:
        value = project_list.source_contract()
        self.assertEqual(value["roadmap_phase_id"], "S17-P1")
        self.assertEqual(value["task_ids"], ["S17P1T01", "S17P1T02", "S17P1T03"])
        self.assertEqual(value["acceptance_zh"], ["列可配置，默认不过载。", "排序公式可解释。", "批量操作不修改事实。"])
        self.assertIn("导出缺少来源说明失败。", value["stop_conditions_zh"])

    def test_catalog_has_eighteen_public_projects_and_first_four_match_homepage(self) -> None:
        all_rows = []
        for company_id in project_list.COMPANY_IDS:
            rows = project_list.project_catalog(company_id, "2026-07")
            self.assertEqual(len(rows), 6)
            self.assertTrue(all(row["company_id"] == company_id for row in rows))
            self.assertTrue(all(row["data_classification"] == "PUBLIC_SYNTHETIC" for row in rows))
            homepage_rows = homepage.homepage_snapshot(company_id=company_id, period="2026-07")["project_portfolio"]
            self.assertEqual(len(homepage_rows), 4)
            for row, summary in zip(rows[:4], homepage_rows):
                self.assertEqual(row["project_id"], summary["project_id"])
                self.assertEqual(row["revenue_cents"], summary["revenue_cents"])
                self.assertEqual(row["gross_margin_bps"], summary["gross_margin_bps"])
                self.assertEqual(row["collection_bps"], summary["collection_bps"])
                self.assertEqual(row["status"], summary["status"])
            all_rows.extend((company_id, row["project_id"]) for row in rows)
        self.assertEqual(len(all_rows), 18)

    def test_money_uses_integer_cents_and_equation_is_exact(self) -> None:
        for row in project_list.project_catalog("demo-north", "2026-Q2"):
            self.assertIs(type(row["revenue_cents"]), int)
            self.assertIs(type(row["cost_cents"]), int)
            self.assertIs(type(row["gross_profit_cents"]), int)
            self.assertEqual(row["revenue_cents"], row["cost_cents"] + row["gross_profit_cents"])

    def test_default_columns_are_not_overloaded_and_can_be_configured(self) -> None:
        default = project_list.project_list()
        custom = project_list.project_list(columns=["project", "revenue", "cost", "source"])
        self.assertEqual(default["selected_columns"], list(project_list.DEFAULT_COLUMNS))
        self.assertEqual(default["default_visible_column_count"], 8)
        self.assertEqual(len(default["available_columns"]), 12)
        self.assertEqual(custom["selected_columns"], ["project", "revenue", "cost", "source"])

    def test_filter_then_sort_then_pagination_never_shifts_rows(self) -> None:
        first = project_list.project_list(sort_by="margin", page=1, page_size=4)
        second = project_list.project_list(sort_by="margin", page=2, page_size=4)
        ids = [row["project_id"] for row in first["rows"] + second["rows"]]
        self.assertEqual(ids, first["all_filtered_project_ids"])
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual([row["absolute_row_number"] for row in first["rows"]], [1, 2, 3, 4])
        self.assertEqual([row["absolute_row_number"] for row in second["rows"]], [5, 6])
        attention = project_list.project_list(project_status="attention", page_size=6)
        self.assertTrue(all(row["status"] == "ATTENTION" for row in attention["rows"]))

    def test_all_group_and_sort_rules_are_visible_and_deterministic(self) -> None:
        for group_by in project_list.GROUP_OPTIONS:
            value = project_list.project_list(group_by=group_by, sort_by="risk", page_size=6)
            self.assertTrue(value["group_explanation_zh"])
            self.assertEqual(sum(group["count"] for group in value["groups"]), 6)
        for sort_by in project_list.SORT_OPTIONS:
            left = project_list.project_list(sort_by=sort_by, page_size=6)
            right = project_list.project_list(sort_by=sort_by, page_size=6)
            self.assertEqual(left["all_filtered_project_ids"], right["all_filtered_project_ids"])
            self.assertTrue(left["sort_explanation_zh"])
        self.assertIn("没有隐藏评分", project_list.SORT_EXPLANATIONS["risk"])

    def test_batch_compare_is_read_only_and_totals_are_exact(self) -> None:
        rows = project_list.project_catalog("demo-north", "2026-07")[:3]
        ids = [row["project_id"] for row in rows]
        before = project_list.project_catalog("demo-north", "2026-07")
        value = project_list.batch_compare(ids)
        after = project_list.project_catalog("demo-north", "2026-07")
        self.assertEqual(value["totals"]["revenue_cents"], sum(row["revenue_cents"] for row in rows))
        self.assertEqual(value["totals"]["cost_cents"], sum(row["cost_cents"] for row in rows))
        self.assertEqual(value["fact_layer_write_count"], 0)
        self.assertEqual(before, after)

    def test_csv_matches_selected_facts_and_each_row_has_lineage(self) -> None:
        rows = project_list.project_catalog("demo-north", "2026-07")[:2]
        content = project_list.export_csv([row["project_id"] for row in rows])
        exported = list(csv.DictReader(io.StringIO(content)))
        self.assertEqual([row["项目编号"] for row in exported], [row["project_id"] for row in rows])
        self.assertEqual([int(row["收入(分)"]) for row in exported], [row["revenue_cents"] for row in rows])
        self.assertTrue(all(row["来源说明"] and row["来源编号"] and row["数据截止日"] for row in exported))

    def test_invalid_or_cross_scope_batch_requests_fail_closed(self) -> None:
        with self.assertRaises(project_list.ProjectListError):
            project_list.batch_compare(["PUB-PROJ-001"])
        with self.assertRaises(project_list.ProjectListError):
            project_list.batch_compare(["PUB-PROJ-001", "NOT-IN-SCOPE"])
        with self.assertRaises(project_list.ProjectListError):
            project_list.project_list(columns=[])
        with self.assertRaises(project_list.ProjectListError):
            project_list.project_list(page_size=99)

    def test_public_check_suite_passes(self) -> None:
        checks = project_list.public_checks()
        self.assertEqual(len(checks), 58)
        self.assertTrue(all(row["passed"] for row in checks))


if __name__ == "__main__":
    unittest.main()
