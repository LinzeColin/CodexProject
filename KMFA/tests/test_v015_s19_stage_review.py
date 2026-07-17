from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from KMFA.tools import run_v015_s19_p3_tax_policy_reporting as runtime
from KMFA.tools import v015_s19_p3_tax_policy_reporting as kernel


class S19StageReviewIntegrationTests(unittest.TestCase):
    def valid_event(self) -> dict[str, object]:
        report = kernel.report_view()
        return kernel._review_event(
            report_id=report["report_id"], company_id=report["company_id"], period=report["period"],
            user_id="demo-owner", role_id="tax", opinion_code="NEEDS_SOURCE_CHECK",
            comment_zh="请核对当前报告依据。", basis_refs=[report["review_basis"][0]["basis_ref"]],
            idempotency_key="stage-review-integrity",
        )

    def test_three_pages_have_continuous_human_navigation(self) -> None:
        html = runtime.render_html()
        for token in (
            'aria-label="税务与政策步骤"', "1 税票事实", "2 政策材料", "3 周期报告",
            'href="/tax-policy"', 'href="/policy-eligibility"', 'href="/tax-policy-report"',
            ".s19-journey", "min-height:44px",
        ):
            self.assertIn(token, html)

    def test_journal_rejects_tampered_event(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "reviews.jsonl"
            value = self.valid_event()
            path.write_text(json.dumps(value, ensure_ascii=False) + "\n", encoding="utf-8")
            journal = kernel.ProfessionalReviewJournal(path)
            self.assertEqual(journal.read()[0]["event_id"], value["event_id"])
            value["comment_zh"] = "篡改后的复核内容"
            path.write_text(json.dumps(value, ensure_ascii=False) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(kernel.TaxPolicyReportingError, "指纹校验失败"):
                journal.read()

    def test_event_field_injection_is_rejected(self) -> None:
        value = self.valid_event()
        value["unexpected"] = "injected"
        with self.assertRaisesRegex(kernel.TaxPolicyReportingError, "字段集合无效"):
            kernel._validate_review_event(value)

    def test_report_projection_requires_exact_report_id(self) -> None:
        valid = self.valid_event()
        wrong = dict(valid)
        wrong["report_id"] = "TPR-demo-north-2026-Q2"
        view = kernel.report_view(events=[valid, wrong])
        self.assertEqual(view["review_event_count"], 1)
        self.assertEqual(view["review_events"][0]["event_id"], valid["event_id"])

    def test_professional_permissions_remain_fail_closed(self) -> None:
        self.assertFalse(kernel.review_permission("demo-owner", "management", "demo-north")["allowed"])
        self.assertTrue(kernel.review_permission("demo-owner", "tax", "demo-north")["allowed"])
        self.assertTrue(kernel.review_permission("demo-owner", "reviewer", "demo-north")["allowed"])


if __name__ == "__main__":
    unittest.main()
