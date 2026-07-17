from __future__ import annotations

import csv
import json
import unittest

from KMFA.tools import build_v015_s18_p3_relation_reporting as builder


class RelationReportingArtifactsTests(unittest.TestCase):
    def load(self, path):
        return json.loads(path.read_text(encoding="utf-8"))

    def test_expected_outputs_are_deterministic(self) -> None:
        builder.check_outputs()

    def test_dual_view_keeps_profit_and_cash_separate(self) -> None:
        value = self.load(builder.DUAL_VIEW_CONTRACT_PATH)
        self.assertEqual(value["project_count"], 6)
        self.assertEqual(value["profit_cash_substitution_count"], 0)
        self.assertEqual(value["scope_limitation_displayed_count"], 6)
        self.assertEqual(value["profit_equation_difference_cents"], 0)
        self.assertEqual(value["cash_occupancy_reconciliation_difference_cents"], 0)
        self.assertNotEqual(value["profit_basis_zh"], value["cash_basis_zh"])
        self.assertEqual(value["money_tolerance_cents"], 0)

    def test_alert_contract_is_externalised_sanitised_and_non_sending(self) -> None:
        value = self.load(builder.ALERT_CONTRACT_PATH)
        self.assertEqual(value["alert_count"], 5)
        self.assertEqual(value["alert_type_count"], 3)
        self.assertEqual(value["alert_count_by_type"], {"MAJOR_OVERDUE": 2, "FUNDING_GAP": 1, "LOAN_MATURITY": 2})
        self.assertTrue(value["thresholds_externalized"])
        self.assertEqual(value["full_sensitive_detail_count"], 0)
        self.assertEqual(value["exposed_sensitive_field_count"], 0)
        self.assertEqual(value["notification_send_count"], 0)
        self.assertEqual(value["external_message_count"], 0)
        self.assertEqual(value["unverified_alert_count"], 0)

    def test_report_and_appendix_match_and_unverified_degrades(self) -> None:
        value = self.load(builder.REPORT_CONTRACT_PATH)
        self.assertEqual(value["page_row_count"], 6)
        self.assertEqual(value["appendix_row_count"], 6)
        self.assertEqual(value["report_page_export_difference_cents"], 0)
        self.assertEqual(value["degraded_report_status"], "DEGRADED_UNVERIFIED")
        self.assertEqual(value["degraded_report_grade"], "D")
        self.assertFalse(value["degraded_numeric_detail_allowed"])
        self.assertEqual(value["degraded_alert_count"], 0)
        self.assertEqual(value["unverified_numeric_visible_count"], 0)
        self.assertFalse(value["formal_business_report"])
        with builder.CSV_APPENDIX_PATH.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(len(rows), 6)

    def test_browser_and_human_evidence_exist(self) -> None:
        contract = self.load(builder.BROWSER_CONTRACT_PATH)
        self.assertEqual(contract["browser_flow_count"], 9)
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
        self.assertEqual(value["overall_accepted_phase_count"], 52 if final else 51)
        self.assertTrue(value["s18_p3_started"])
        self.assertEqual(value["s18_p3_completed"], final)
        self.assertEqual(value["s18_stage_review_entry_allowed"], final)
        self.assertFalse(value["s18_stage_review_started"])
        self.assertEqual(value["validation_run_id"], run_id)
        self.assertEqual(value["validation_head"], validation_head)
        self.assertFalse(value["github_upload_performed"])
        self.assertFalse(value["app_reinstall_performed"])


if __name__ == "__main__":
    unittest.main()
