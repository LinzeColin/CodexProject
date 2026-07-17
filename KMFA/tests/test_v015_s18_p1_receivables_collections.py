from __future__ import annotations

import unittest

from KMFA.tools import v015_s18_p1_receivables_collections as subject


class ReceivablesCollectionsTests(unittest.TestCase):
    def test_source_contract_matches_taskpack(self) -> None:
        contract = subject.source_contract()
        self.assertEqual(contract["roadmap_phase_id"], "S18-P1")
        self.assertEqual(contract["task_ids"], ["S18P1T01", "S18P1T02", "S18P1T03"])
        self.assertIn("未开票和应收不得混淆。", contract["stop_conditions_zh"])

    def test_unbilled_is_never_receivable(self) -> None:
        facts = subject.receivable_facts()
        self.assertEqual(len(facts["unbilled_items"]), 1)
        self.assertEqual(facts["unbilled_items"][0]["invoice_status"], "NOT_INVOICED")
        self.assertEqual(facts["unbilled_items"][0]["receivable_cents"], 0)
        self.assertNotIn("UNBILLED-001", {row["item_id"] for row in facts["rows"]})

    def test_receivable_equation_and_integer_cents(self) -> None:
        for company in subject.COMPANY_AMOUNT_FACTORS:
            facts = subject.receivable_facts(company)
            for row in facts["rows"]:
                self.assertIs(type(row["invoice_cents"]), int)
                self.assertIs(type(row["collected_cents"]), int)
                self.assertIs(type(row["receivable_cents"]), int)
                self.assertEqual(row["invoice_cents"] - row["collected_cents"], row["receivable_cents"])

    def test_aging_cutoff_and_boundaries(self) -> None:
        expected = {
            "2026-08-15": (0, "CURRENT"),
            "2026-07-14": (1, "D01_30"),
            "2026-06-15": (30, "D01_30"),
            "2026-06-14": (31, "D31_60"),
            "2026-05-16": (60, "D31_60"),
            "2026-05-15": (61, "D61_90"),
            "2026-04-16": (90, "D61_90"),
            "2026-04-15": (91, "D90_PLUS"),
        }
        for due_date, (days, bucket) in expected.items():
            with self.subTest(due_date=due_date):
                actual_days, actual_bucket, _ = subject._aging(due_date)
                self.assertEqual((actual_days, actual_bucket), (days, bucket))

    def test_priority_is_explainable_and_deterministic(self) -> None:
        first = subject.receivables_view()
        second = subject.receivables_view()
        self.assertEqual(first["rows"], second["rows"])
        scores = [row["priority_score"] for row in first["rows"] if row["priority_score"] is not None]
        self.assertEqual(scores, sorted(scores, reverse=True))
        for row in first["rows"]:
            if row["priority_supported"]:
                self.assertEqual(row["priority_score"], sum(row["components"].values()))
                self.assertEqual(len(row["priority_reasons_zh"]), 5)
                self.assertIsNotNone(row["recommended_internal_step_zh"])
            self.assertFalse(row["automatic_customer_contact_allowed"])

    def test_missing_evidence_hides_recommendation(self) -> None:
        row = next(item for item in subject.receivables_view()["rows"] if item["item_id"] == "AR-006")
        self.assertFalse(row["priority_supported"])
        self.assertIsNone(row["priority_score"])
        self.assertIsNone(row["recommended_internal_step_zh"])
        self.assertEqual(row["priority_label_zh"], "资料不足")

    def test_filters_and_all_group_dimensions_reconcile(self) -> None:
        base = subject.receivables_view()
        for dimension in subject.GROUP_DIMENSIONS:
            with self.subTest(dimension=dimension):
                view = subject.receivables_view(group_by=dimension)
                self.assertEqual(view["group_difference_cents"], 0)
                self.assertEqual(
                    view["summary"]["receivable_cents"],
                    sum(group["receivable_cents"] for group in view["groups"]),
                )
        owner = base["rows"][0]["owner_zh"]
        filtered = subject.receivables_view(owner=owner)
        self.assertTrue(filtered["rows"])
        self.assertTrue(all(row["owner_zh"] == owner for row in filtered["rows"]))

    def test_cross_company_isolation(self) -> None:
        views = {company: subject.receivables_view(company_id=company) for company in subject.COMPANY_AMOUNT_FACTORS}
        for company, view in views.items():
            self.assertEqual(view["cross_company_leak_count"], 0)
            self.assertTrue(all(row["company_id"] == company for row in view["rows"]))
        self.assertEqual(len({views[company]["summary"]["receivable_cents"] for company in views}), 3)

    def test_summary_detail_consistency_under_filters(self) -> None:
        cases = (
            {"aging_bucket": "D90_PLUS"},
            {"priority": "HIGH"},
            {"project": "PUB-PROJ-001"},
            {"customer": "示例制造集团"},
            {"invoice_period": "2026-07"},
            {"owner": "陈工"},
        )
        for filters in cases:
            with self.subTest(filters=filters):
                view = subject.receivables_view(**filters)
                self.assertEqual(view["money_difference_cents"], 0)
                self.assertEqual(view["group_difference_cents"], 0)
                self.assertEqual(view["summary"]["receivable_cents"], sum(row["receivable_cents"] for row in view["rows"]))

    def test_public_checks_all_pass(self) -> None:
        checks = subject.public_checks()
        self.assertEqual(len(checks), 50)
        self.assertEqual({row["status"] for row in checks}, {"PASS"})


if __name__ == "__main__":
    unittest.main()
