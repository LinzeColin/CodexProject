from __future__ import annotations

import csv
import json
import unittest

from KMFA.tools import build_v015_s20_stage_review as builder


class S20StageReviewArtifactTests(unittest.TestCase):
    def test_deterministic_outputs_are_exact(self) -> None:
        self.assertEqual(builder.check_outputs(), [])

    def test_public_evidence_accounting_is_exact(self) -> None:
        verification = json.loads(builder.CROSS_PHASE_VERIFICATION_PATH.read_text(encoding="utf-8"))
        self.assertEqual(verification["accounting"], {"total": 239, "passed": 239, "failed": 0})
        cross = json.loads(builder.CROSS_PHASE_CONTRACTS_PATH.read_text(encoding="utf-8"))
        self.assertEqual(cross["accounting"], {"total": 44, "passed": 44, "failed": 0, "blocking_failed": 0})

    def test_findings_and_residual_risks_are_honest(self) -> None:
        with builder.FINDINGS_PATH.open(encoding="utf-8", newline="") as handle:
            findings = list(csv.DictReader(handle))
        self.assertEqual([row["finding_id"] for row in findings], ["S20REV-F001", "S20REV-F002"])
        self.assertTrue(all(row["status"] == "FIXED_VALIDATED" for row in findings))
        with builder.RISKS_PATH.open(encoding="utf-8", newline="") as handle:
            risks = list(csv.DictReader(handle))
        self.assertEqual(len(risks), 4)
        self.assertTrue(all(row["status"] == "ROUTED_RESIDUAL" and row["plan_complete"] == "true" for row in risks))

    def test_human_reports_are_plain_chinese(self) -> None:
        review = builder.REVIEW_REPORT_PATH.read_text(encoding="utf-8")
        tests = builder.TEST_RESULTS_PATH.read_text(encoding="utf-8")
        for phrase in ("三步页面缺少统一流程指引", "重算日志没有重新核对原人工确认记录"):
            self.assertIn(phrase, review)
        self.assertIn("239/239", tests)


if __name__ == "__main__":
    unittest.main()
