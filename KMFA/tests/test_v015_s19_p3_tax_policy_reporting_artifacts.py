from __future__ import annotations

import json
import unittest

from KMFA.tools import build_v015_s19_p3_tax_policy_reporting as builder


class TaxPolicyReportingArtifactsTests(unittest.TestCase):
    def load(self, path):
        return json.loads(path.read_text(encoding="utf-8"))

    def test_outputs_are_deterministic(self) -> None:
        builder.check_outputs()

    def test_tax_summary_is_plain_evidence_backed_and_non_filing(self) -> None:
        value = self.load(builder.TAX_SUMMARY_PATH)
        self.assertEqual((value["review_invoice_count"], value["anomaly_count"], value["unknown_amount_item_count"]), (4, 5, 1))
        self.assertEqual(value["alarm_copy_count"], 0)
        self.assertEqual(value["automatic_tax_adjustment_count"], 0)
        self.assertEqual(value["formal_filing_conclusion_count"], 0)
        self.assertTrue(all(len(row["basis_refs"]) == 2 for row in value["items"]))

    def test_policy_reports_cover_three_cycles_without_promise(self) -> None:
        value = self.load(builder.POLICY_REPORT_PATH)
        self.assertEqual(value["report_count"], 3)
        self.assertEqual(value["cycle_ids"], ["MONTHLY", "QUARTERLY", "HALF_YEAR"])
        self.assertEqual((value["available_evidence_count_per_report"], value["missing_evidence_count_per_report"], value["review_evidence_count_per_report"]), (7, 3, 2))
        self.assertEqual(value["formal_eligibility_conclusion_count"], 0)
        self.assertEqual(value["recognition_result_promise_count"], 0)

    def test_review_contract_is_authorised_append_only_and_non_mutating(self) -> None:
        value = self.load(builder.REVIEW_CONTRACT_PATH)
        self.assertEqual(value["professional_review_roles"], ["reviewer", "tax"])
        self.assertFalse(value["management_review_allowed"])
        self.assertTrue(value["tax_review_allowed"])
        self.assertTrue(value["append_only"])
        self.assertFalse(value["in_place_update_allowed"])
        self.assertEqual((value["update_endpoint_count"], value["delete_endpoint_count"], value["source_data_write_count"], value["fact_layer_write_count"]), (0, 0, 0, 0))

    def test_browser_human_and_manifest_evidence_exist(self) -> None:
        browser = self.load(builder.BROWSER_CONTRACT_PATH)
        self.assertEqual((browser["browser_flow_count"], browser["visual_evidence_count"]), (8, 6))
        self.assertEqual(browser["minimum_touch_target_px"], 44)
        self.assertTrue(all(path.is_file() and path.stat().st_size > 10_000 for path in builder.SCREENSHOT_PATHS))
        for path in (builder.IMPLEMENTATION_REPORT_PATH, builder.USER_GUIDE_PATH, builder.TEST_RESULTS_PATH, builder.RISKS_ROLLBACK_PATH):
            self.assertTrue(path.is_file())
            self.assertGreater(len(path.read_text(encoding="utf-8")), 150)
        manifest = self.load(builder.MANIFEST_PATH)
        final, run_id, head = builder.final_binding(builder.receipts())
        self.assertEqual(manifest["phase_acceptance_status"], "PASSED" if final else "PENDING_FINAL_VALIDATION")
        self.assertEqual(manifest["phase_task_accepted_count"], 3 if final else 0)
        self.assertEqual(manifest["overall_accepted_phase_count"], 55 if final else 54)
        self.assertEqual(manifest["s19_stage_review_entry_allowed"], final)
        self.assertFalse(manifest["s19_stage_review_started"])
        self.assertEqual((manifest["validation_run_id"], manifest["validation_head"]), (run_id, head))
        self.assertFalse(manifest["github_upload_performed"])
        self.assertFalse(manifest["app_reinstall_performed"])


if __name__ == "__main__":
    unittest.main()
