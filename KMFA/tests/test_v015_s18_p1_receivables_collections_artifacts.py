from __future__ import annotations

import json
import unittest

from KMFA.tools import build_v015_s18_p1_receivables_collections as builder


class ReceivablesArtifactsTests(unittest.TestCase):
    def load(self, path):
        return json.loads(path.read_text(encoding="utf-8"))

    def test_expected_outputs_are_deterministic(self) -> None:
        builder.check_outputs()

    def test_aging_contract_separates_unbilled_and_uses_zero_tolerance(self) -> None:
        value = self.load(builder.AGING_CONTRACT_PATH)
        self.assertEqual(value["source_item_count"], 8)
        self.assertEqual(value["invoice_item_count"], 7)
        self.assertEqual(value["open_receivable_count"], 6)
        self.assertEqual(value["settled_invoice_count"], 1)
        self.assertEqual(value["unbilled_item_count"], 1)
        self.assertEqual(value["unbilled_receivable_cents"], 0)
        self.assertEqual(value["aging_bucket_count"], 5)
        self.assertEqual(value["cutoff_date"], "2026-07-15")
        self.assertEqual(value["money_tolerance_cents"], 0)

    def test_priority_contract_is_explainable_and_fail_closed(self) -> None:
        value = self.load(builder.PRIORITY_CONTRACT_PATH)
        self.assertEqual(value["component_count"], 5)
        self.assertEqual(value["component_max_total"], 107)
        self.assertEqual(value["supported_priority_count"], 5)
        self.assertEqual(value["evidence_missing_count"], 1)
        self.assertTrue(value["all_supported_rows_have_five_reasons"])
        self.assertEqual(value["score_component_difference"], 0)
        self.assertEqual(value["unsupported_recommendation_count"], 0)
        self.assertEqual(value["automatic_customer_contact_count"], 0)

    def test_view_contract_reconciles_all_dimensions_and_entities(self) -> None:
        value = self.load(builder.VIEW_CONTRACT_PATH)
        self.assertEqual(value["group_dimension_count"], 4)
        self.assertEqual(value["company_count"], 3)
        self.assertEqual(value["money_difference_cents"], 0)
        self.assertEqual(value["group_difference_cents"], 0)
        self.assertEqual(value["cross_company_leak_count"], 0)
        self.assertTrue(all(row["group_difference_cents"] == 0 for row in value["dimension_results"].values()))

    def test_browser_and_human_evidence_exist(self) -> None:
        contract = self.load(builder.BROWSER_CONTRACT_PATH)
        self.assertEqual(contract["browser_flow_count"], 8)
        self.assertEqual(contract["visual_evidence_count"], 5)
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
        self.assertEqual(value["overall_accepted_phase_count"], 50 if final else 49)
        self.assertTrue(value["s18_p1_started"])
        self.assertEqual(value["s18_p1_completed"], final)
        self.assertEqual(value["s18_p2_entry_allowed"], final)
        self.assertFalse(value["s18_p2_started"])
        self.assertEqual(value["validation_run_id"], run_id)
        self.assertEqual(value["validation_head"], validation_head)
        self.assertFalse(value["github_upload_performed"])
        self.assertFalse(value["app_reinstall_performed"])


if __name__ == "__main__":
    unittest.main()
