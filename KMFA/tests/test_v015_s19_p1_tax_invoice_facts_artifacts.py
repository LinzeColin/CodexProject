from __future__ import annotations

import json
import unittest

from KMFA.tools import build_v015_s19_p1_tax_invoice_facts as builder


class TaxInvoiceArtifactsTests(unittest.TestCase):
    def load(self, path):
        return json.loads(path.read_text(encoding="utf-8"))

    def test_outputs_are_deterministic(self) -> None:
        builder.check_outputs()

    def test_tax_model_keeps_unknown_rate_blocked(self) -> None:
        value = self.load(builder.TAX_MODEL_PATH)
        self.assertEqual(value["fact_count"], 8)
        self.assertEqual(value["linked_dimension_count"], 4)
        self.assertEqual(value["unknown_rate_count"], 1)
        self.assertEqual(value["unknown_rate_display_zh"], "待确认")
        self.assertTrue(value["unknown_rate_blocked"])
        self.assertEqual(value["rate_inference_count"], 0)
        self.assertTrue(value["integer_cent_required"])

    def test_matching_contract_has_evidence_and_no_adjustment(self) -> None:
        value = self.load(builder.MATCHING_PATH)
        self.assertEqual(value["matching_dimensions"], ["entity", "project", "period", "tax_rate"])
        self.assertEqual(value["matched_count"], 4)
        self.assertEqual(value["review_count"], 4)
        self.assertEqual(value["anomaly_count"], 5)
        self.assertEqual(value["anomaly_type_count"], 5)
        self.assertTrue(value["all_anomalies_have_invoice_and_contract_evidence"])
        self.assertEqual(value["automatic_tax_adjustment_count"], 0)

    def test_project_burden_is_reconciled_and_not_filing(self) -> None:
        value = self.load(builder.BURDEN_PATH)
        self.assertEqual(value["project_count"], 3)
        self.assertEqual(value["business_type_count"], 3)
        self.assertEqual(value["equation_difference_cents"], 0)
        self.assertEqual(value["scope_limitation_displayed_count"], 3)
        self.assertEqual(value["formal_filing_conclusion_count"], 0)

    def test_browser_and_human_evidence_exist(self) -> None:
        value = self.load(builder.BROWSER_CONTRACT_PATH)
        self.assertEqual(value["browser_flow_count"], 7)
        self.assertEqual(value["visual_evidence_count"], 5)
        self.assertEqual(value["minimum_touch_target_px"], 44)
        self.assertTrue(all(path.is_file() and path.stat().st_size > 10_000 for path in builder.SCREENSHOT_PATHS))
        for path in (builder.IMPLEMENTATION_REPORT_PATH, builder.USER_GUIDE_PATH, builder.TEST_RESULTS_PATH, builder.RISKS_ROLLBACK_PATH):
            self.assertTrue(path.is_file())
            self.assertGreater(len(path.read_text(encoding="utf-8")), 120)

    def test_manifest_uses_receipt_bound_acceptance(self) -> None:
        value = self.load(builder.MANIFEST_PATH)
        final, run_id, validation_head = builder.final_binding(builder.receipts())
        self.assertEqual(value["phase_acceptance_status"], "PASSED" if final else "PENDING_FINAL_VALIDATION")
        self.assertEqual(value["phase_task_accepted_count"], 3 if final else 0)
        self.assertEqual(value["overall_accepted_phase_count"], 53 if final else 52)
        self.assertTrue(value["s19_p1_started"])
        self.assertEqual(value["s19_p1_completed"], final)
        self.assertEqual(value["s19_p2_entry_allowed"], final)
        self.assertFalse(value["s19_p2_started"])
        self.assertEqual(value["validation_run_id"], run_id)
        self.assertEqual(value["validation_head"], validation_head)
        self.assertFalse(value["github_upload_performed"])
        self.assertFalse(value["app_reinstall_performed"])


if __name__ == "__main__":
    unittest.main()
