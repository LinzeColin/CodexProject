from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from KMFA.tools import v015_s19_p3_tax_policy_reporting as subject


class TaxPolicyReportingTests(unittest.TestCase):
    def test_tax_summary_is_plain_and_evidence_backed(self) -> None:
        value = subject.tax_risk_summary()
        self.assertEqual((value["invoice_fact_count"], value["review_invoice_count"], value["anomaly_count"]), (8, 4, 5))
        self.assertEqual(value["alarm_copy_count"], 0)
        self.assertTrue(all(row["issue_zh"] and row["next_step_zh"] and len(row["basis_refs"]) == 2 for row in value["items"]))

    def test_unknown_amount_stays_unknown_and_no_adjustment_is_inferred(self) -> None:
        value = subject.tax_risk_summary()
        unknown = next(row for row in value["items"] if "UNKNOWN_TAX_RATE" in row["anomaly_types"])
        self.assertIsNone(unknown["reference_tax_cents"])
        self.assertIn("不能估算", unknown["impact_zh"])
        self.assertEqual(value["automatic_tax_adjustment_count"], 0)
        self.assertIsNone(value["formal_filing_conclusion"])

    def test_policy_report_has_cycle_gaps_and_no_recognition_promise(self) -> None:
        value = subject.policy_preparation_report()
        self.assertEqual(value["cycle_id"], "MONTHLY")
        self.assertEqual((value["category_count"], value["evidence_item_count"]), (6, 12))
        self.assertEqual((value["available_evidence_count"], value["missing_evidence_count"], value["review_evidence_count"]), (7, 3, 2))
        self.assertIsNone(value["formal_eligibility_conclusion"])
        self.assertFalse(value["recognition_result_promised"])

    def test_periodic_reports_cover_month_quarter_and_half_year(self) -> None:
        rows = subject.periodic_policy_reports("demo-west")
        self.assertEqual([row["cycle_id"] for row in rows], ["MONTHLY", "QUARTERLY", "HALF_YEAR"])
        self.assertEqual(len({row["report_id"] for row in rows}), 3)
        self.assertTrue(all(row["company_id"] == "demo-west" for row in rows))

    def test_review_permission_is_role_and_company_scoped(self) -> None:
        self.assertFalse(subject.review_permission("demo-owner", "management", "demo-north")["allowed"])
        self.assertTrue(subject.review_permission("demo-owner", "tax", "demo-north")["allowed"])
        denied = subject.review_permission("demo-finance", "reviewer", "demo-south")
        self.assertFalse(denied["allowed"])

    def test_unauthorised_role_cannot_record_review(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            journal = subject.ProfessionalReviewJournal(Path(directory) / "reviews.jsonl")
            view = subject.report_view()
            with self.assertRaisesRegex(subject.TaxPolicyReportingError, "只有税务或审核角色"):
                subject.record_professional_review(
                    journal, report_id=view["report_id"], company_id="demo-north", period="2026-07",
                    user_id="demo-owner", role_id="management", opinion_code="NEEDS_SOURCE_CHECK",
                    comment_zh="请核对当前来源", basis_refs=[view["review_basis"][0]["basis_ref"]], idempotency_key="denied-1",
                )
            self.assertEqual(journal.read(), [])

    def test_authorised_review_is_append_only_and_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            journal = subject.ProfessionalReviewJournal(Path(directory) / "reviews.jsonl")
            view = subject.report_view(role_id="tax")
            kwargs = dict(
                report_id=view["report_id"], company_id="demo-north", period="2026-07",
                user_id="demo-owner", role_id="tax", opinion_code="NEEDS_SOURCE_CHECK",
                comment_zh="请核对票据与合同依据", basis_refs=[view["review_basis"][0]["basis_ref"]], idempotency_key="review-1",
            )
            first = subject.record_professional_review(journal, **kwargs)
            second = subject.record_professional_review(journal, **kwargs)
            self.assertFalse(first["idempotent_replay"])
            self.assertTrue(second["idempotent_replay"])
            self.assertEqual(len(journal.read()), 1)
            event = journal.read()[0]
            self.assertTrue(event["append_only"])
            self.assertFalse(event["in_place_update_allowed"])
            self.assertEqual((event["source_data_write_count"], event["fact_layer_write_count"]), (0, 0))

    def test_idempotency_collision_and_unknown_basis_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            journal = subject.ProfessionalReviewJournal(Path(directory) / "reviews.jsonl")
            view = subject.report_view(role_id="reviewer")
            common = dict(report_id=view["report_id"], company_id="demo-north", period="2026-07", user_id="demo-owner", role_id="reviewer", opinion_code="NEEDS_SOURCE_CHECK", basis_refs=[view["review_basis"][0]["basis_ref"]], idempotency_key="collision-1")
            subject.record_professional_review(journal, comment_zh="第一次复核说明", **common)
            with self.assertRaisesRegex(subject.TaxPolicyReportingError, "不能提交不同"):
                subject.record_professional_review(journal, comment_zh="第二次不同说明", **common)
            with self.assertRaisesRegex(subject.TaxPolicyReportingError, "不属于当前报告"):
                subject.record_professional_review(journal, **{**common, "idempotency_key": "unknown-1", "comment_zh": "检查未知依据", "basis_refs": ["UNKNOWN"]})
            self.assertEqual(len(journal.read()), 1)

    def test_review_events_do_not_leak_across_company_or_period(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            journal = subject.ProfessionalReviewJournal(Path(directory) / "reviews.jsonl")
            north = subject.report_view(role_id="tax")
            subject.record_professional_review(
                journal, report_id=north["report_id"], company_id="demo-north", period="2026-07",
                user_id="demo-owner", role_id="tax", opinion_code="CONFIRMED_FOR_INTERNAL_USE",
                comment_zh="仅用于北方本月内部复核", basis_refs=[north["review_basis"][0]["basis_ref"]], idempotency_key="scope-1",
            )
            self.assertEqual(subject.report_view(role_id="tax", events=journal.read())["review_event_count"], 1)
            self.assertEqual(subject.report_view("demo-west", "2026-07", role_id="tax", events=journal.read())["review_event_count"], 0)
            self.assertEqual(subject.report_view("demo-north", "2026-Q2", role_id="tax", events=journal.read())["review_event_count"], 0)

    def test_public_contract_has_exactly_seventy_two_passes(self) -> None:
        rows = subject.public_checks()
        self.assertEqual(len(rows), 72)
        self.assertTrue(all(row["status"] == "PASS" for row in rows))


if __name__ == "__main__":
    unittest.main()
