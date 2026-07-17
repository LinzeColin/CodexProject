from __future__ import annotations

import csv
import io
import json
import tempfile
import unittest
from pathlib import Path

from KMFA.tools import v015_s18_p3_relation_reporting as subject


class RelationReportingTests(unittest.TestCase):
    def test_source_contract_matches_all_three_tasks(self) -> None:
        value = subject.source_contract()
        self.assertEqual(value["roadmap_phase_id"], "S18-P3")
        self.assertEqual(value["task_ids"], ["S18P3T01", "S18P3T02", "S18P3T03"])
        self.assertIn("口径不明则显示限制。", value["stop_conditions_zh"])
        self.assertIn("提醒不得包含完整敏感明细。", value["stop_conditions_zh"])
        self.assertIn("未核验数据报告降级。", value["stop_conditions_zh"])

    def test_project_profit_and_cash_are_separate_and_reconciled(self) -> None:
        value = subject.project_cash_dual_view()
        self.assertEqual(value["project_count"], 6)
        self.assertEqual(value["profit_cash_substitution_count"], 0)
        self.assertEqual(value["scope_limitation_displayed_count"], 6)
        self.assertEqual(value["profit_equation_difference_cents"], 0)
        self.assertEqual(value["cash_occupancy_reconciliation_difference_cents"], 0)
        for row in value["rows"]:
            self.assertEqual(row["revenue_cents"], row["cost_cents"] + row["gross_profit_cents"])
            self.assertEqual(row["cash_occupied_cents"], row["open_receivable_cents"] + row["unbilled_cents"])
            self.assertNotEqual(row["profit_basis_zh"], row["cash_basis_zh"])
            self.assertFalse(row["profit_used_as_cash"])
            self.assertIn("不代表项目完整现金流", row["scope_limitation_zh"])

    def test_all_companies_are_isolated(self) -> None:
        totals = set()
        for company_id in ("demo-north", "demo-south", "demo-west"):
            value = subject.project_cash_dual_view(company_id=company_id)
            self.assertEqual(value["cross_company_leak_count"], 0)
            self.assertTrue(all(row["company_id"] == company_id for row in value["rows"]))
            totals.add(value["totals"]["cash_occupied_cents"])
        self.assertEqual(len(totals), 3)

    def test_external_thresholds_trigger_three_sanitised_alert_types(self) -> None:
        value = subject.alert_view()
        self.assertTrue(value["thresholds_externalized"])
        self.assertEqual(value["threshold_config_ref"], "KMFA/config/v015_s18_p3_alert_thresholds.json")
        self.assertEqual(value["alert_count"], 5)
        self.assertEqual(value["alert_type_count"], 3)
        self.assertEqual(value["alert_count_by_type"], {"MAJOR_OVERDUE": 2, "FUNDING_GAP": 1, "LOAN_MATURITY": 2})
        self.assertEqual(value["full_sensitive_detail_count"], 0)
        self.assertEqual(value["exposed_sensitive_field_count"], 0)
        self.assertEqual(value["notification_send_count"], 0)
        self.assertEqual(value["external_message_count"], 0)
        self.assertTrue(all(not row["notification_send_allowed"] for row in value["alerts"]))

    def test_invalid_or_incomplete_thresholds_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "thresholds.json"
            path.write_text(json.dumps({"schema_version": "wrong"}), encoding="utf-8")
            with self.assertRaises(subject.RelationReportingError):
                subject.load_alert_thresholds(path)
        with self.assertRaises(subject.RelationReportingError):
            subject.alert_view(scenario_id="certain")

    def test_report_html_and_csv_match_page_numbers(self) -> None:
        report = subject.periodic_report()
        html = subject.render_report_html(report)
        rows = list(csv.DictReader(io.StringIO(subject.export_appendix_csv(report))))
        self.assertEqual(report["report_page_export_difference_cents"], 0)
        self.assertEqual(len(report["page_rows"]), len(rows), 6)
        self.assertEqual(
            [int(row["资金占用(分)"]) for row in rows],
            [row["cash_occupied_cents"] for row in report["page_rows"]],
        )
        self.assertIn("利润和现金是两套数字", html)
        self.assertIn("页面与附表允许差异 0 分", html)
        self.assertFalse(report["formal_business_report"])

    def test_unverified_report_degrades_and_hides_all_money(self) -> None:
        report = subject.periodic_report(verification_state="UNVERIFIED")
        rows = list(csv.DictReader(io.StringIO(subject.export_appendix_csv(report))))
        self.assertEqual(report["report_status"], "DEGRADED_UNVERIFIED")
        self.assertEqual(report["report_grade"], "D")
        self.assertTrue(report["report_degraded"])
        self.assertFalse(report["numeric_detail_allowed"])
        self.assertEqual(report["alert_count"], 0)
        self.assertTrue(all(row[field] is None for row in report["page_rows"] for field in subject.REPORT_MONEY_FIELDS))
        self.assertTrue(all(not row["收入(分)"] and not row["资金占用(分)"] for row in rows))

    def test_view_keeps_all_real_actions_closed(self) -> None:
        value = subject.relation_report_view()
        self.assertEqual(value["money_difference_cents"], 0)
        self.assertEqual(value["profit_used_as_cash_count"], 0)
        self.assertEqual(value["full_sensitive_detail_count"], 0)
        for key in (
            "raw_root_access_count",
            "live_source_read_count",
            "external_network_request_count",
            "source_data_write_count",
            "fact_layer_write_count",
            "notification_send_count",
            "external_message_count",
            "payment_execution_count",
            "bank_operation_count",
            "real_business_action_count",
        ):
            self.assertEqual(value[key], 0, key)
        self.assertFalse(value["formal_business_report"])

    def test_public_checks_all_pass(self) -> None:
        checks = subject.public_checks()
        self.assertEqual(len(checks), 76)
        self.assertTrue(all(row["status"] == "PASS" for row in checks))


if __name__ == "__main__":
    unittest.main()
