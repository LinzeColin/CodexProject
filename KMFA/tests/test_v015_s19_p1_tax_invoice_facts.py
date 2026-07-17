from __future__ import annotations

import unittest

from KMFA.tools import v015_s19_p1_tax_invoice_facts as subject


class TaxInvoiceFactsTests(unittest.TestCase):
    def test_source_contract_matches_taskpack(self) -> None:
        contract = subject.source_contract()
        self.assertEqual(contract["roadmap_phase_id"], "S19-P1")
        self.assertEqual(contract["task_ids"], ["S19P1T01", "S19P1T02", "S19P1T03"])
        self.assertEqual(contract["stop_conditions_zh"], ["未知税率不自动推断。", "不自动做税务调整。", "不得输出正式申报结论。"])

    def test_eight_facts_have_explicit_links_and_states(self) -> None:
        rows = subject.tax_invoice_facts()
        self.assertEqual(len(rows), 8)
        self.assertEqual({row["direction"] for row in rows}, {"OUTPUT", "INPUT"})
        for row in rows:
            self.assertEqual(set(row["links"]), {"contract_ref", "project_ref", "voucher_ref", "cash_ref"})
            self.assertIn(row["tax_inclusive_state"], {"INCLUSIVE", "EXCLUSIVE", "UNKNOWN"})
            self.assertIn(row["invoice_status"], {"ISSUED", "RECEIVED", "PENDING_CONFIRMATION"})

    def test_known_tax_amounts_use_integer_cents_and_exact_equation(self) -> None:
        for company_id in subject.COMPANY_FACTORS:
            for row in subject.tax_invoice_facts(company_id):
                if row["tax_rate_bps"] is None:
                    continue
                self.assertIs(type(row["net_cents"]), int)
                self.assertIs(type(row["tax_cents"]), int)
                self.assertIs(type(row["gross_cents"]), int)
                self.assertEqual(row["tax_cents"], row["net_cents"] * row["tax_rate_bps"] // 10_000)
                self.assertEqual(row["gross_cents"], row["net_cents"] + row["tax_cents"])

    def test_unknown_rate_stays_unknown_and_blocked(self) -> None:
        row = next(item for item in subject.tax_invoice_facts() if item["invoice_id"] == "TAX-OUT-003")
        self.assertIsNone(row["tax_rate_bps"])
        self.assertEqual(row["tax_rate_display_zh"], "待确认")
        self.assertIsNone(row["net_cents"])
        self.assertIsNone(row["tax_cents"])
        self.assertTrue(row["unknown_rate_blocked"])
        self.assertFalse(row["rate_inferred"])

    def test_matching_covers_four_dimensions_with_evidence(self) -> None:
        matches = {row["invoice_id"]: row for row in subject.match_results(subject.tax_invoice_facts())}
        self.assertEqual(sum(row["match_state"] == "MATCHED" for row in matches.values()), 4)
        self.assertEqual(matches["TAX-OUT-003"]["anomaly_types"], ["UNKNOWN_TAX_RATE"])
        self.assertEqual(matches["TAX-IN-003"]["anomaly_types"], ["ENTITY_MISMATCH"])
        self.assertEqual(matches["TAX-OUT-004"]["anomaly_types"], ["PERIOD_MISMATCH"])
        self.assertEqual(matches["TAX-IN-004"]["anomaly_types"], ["PROJECT_MISMATCH", "TAX_RATE_MISMATCH"])
        for row in matches.values():
            self.assertEqual(row["evidence_count"], len(row["anomaly_types"]))
            self.assertFalse(row["automatic_tax_adjustment_allowed"])
            self.assertTrue(all(item["invoice_ref"] and item["contract_ref"] and item["fact_zh"] for item in row["evidence"]))

    def test_project_tax_burden_excludes_unmatched_facts(self) -> None:
        view = subject.tax_invoice_view()
        self.assertEqual(len(view["project_burden"]), 3)
        for row in view["project_burden"]:
            self.assertEqual(row["management_net_tax_pressure_cents"], row["output_tax_cents"] - row["eligible_input_tax_cents"])
            self.assertFalse(row["formal_filing_conclusion"])
            self.assertIn("不是正式申报结论", row["scope_limitation_zh"])
        project_three = next(row for row in view["project_burden"] if row["project_id"] == "PUB-PROJ-003")
        self.assertEqual(project_three["included_fact_count"], 0)
        self.assertEqual(project_three["management_net_tax_pressure_cents"], 0)
        self.assertEqual(project_three["unknown_rate_count"], 1)

    def test_filters_reconcile_summary_and_anomalies(self) -> None:
        view = subject.tax_invoice_view(direction="INPUT", match_state="REVIEW_REQUIRED")
        self.assertEqual(view["summary"]["fact_count"], 2)
        self.assertTrue(all(row["direction"] == "INPUT" and row["match_state"] == "REVIEW_REQUIRED" for row in view["rows"]))
        self.assertEqual(view["anomaly_count"], sum(len(row["anomaly_types"]) for row in view["rows"]))

    def test_cross_company_and_period_isolation(self) -> None:
        totals = set()
        for company_id in subject.COMPANY_FACTORS:
            view = subject.tax_invoice_view(company_id=company_id, period="2026-Q2")
            self.assertEqual(view["cross_company_leak_count"], 0)
            self.assertTrue(all(row["company_id"] == company_id and row["contract_period"] == "2026-Q2" for row in view["rows"]))
            totals.add(view["summary"]["explicit_tax_cents"])
        self.assertEqual(len(totals), 3)

    def test_execution_and_filing_boundaries_are_zero(self) -> None:
        view = subject.tax_invoice_view()
        self.assertTrue(view["management_analysis_only"])
        self.assertFalse(view["formal_filing_conclusion"])
        self.assertEqual(view["raw_root_access_count"], 0)
        self.assertEqual(view["rate_inference_count"], 0)
        self.assertEqual(view["automatic_tax_adjustment_count"], 0)
        self.assertEqual(view["business_action_count"], 0)

    def test_public_checks_are_exact_and_all_pass(self) -> None:
        checks = subject.public_checks()
        self.assertEqual(len(checks), 64)
        self.assertEqual({row["status"] for row in checks}, {"PASS"})


if __name__ == "__main__":
    unittest.main()
