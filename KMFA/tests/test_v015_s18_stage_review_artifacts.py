from __future__ import annotations

import csv
import json
import unittest

from KMFA.tools import build_v015_s18_stage_review as builder


class S18StageReviewArtifactTests(unittest.TestCase):
    def test_deterministic_outputs_are_exact(self) -> None:
        self.assertEqual(builder.check_outputs(), [])

    def test_public_evidence_accounting_is_exact(self) -> None:
        verification = json.loads(
            builder.CROSS_PHASE_VERIFICATION_PATH.read_text(encoding="utf-8")
        )
        self.assertEqual(
            verification["accounting"], {"total": 246, "passed": 246, "failed": 0}
        )
        cross = json.loads(
            builder.CROSS_PHASE_CONTRACTS_PATH.read_text(encoding="utf-8")
        )
        self.assertEqual(
            cross["accounting"],
            {"total": 41, "passed": 41, "failed": 0, "blocking_failed": 0},
        )

    def test_findings_and_risks_are_honestly_closed_or_routed(self) -> None:
        with builder.FINDINGS_PATH.open(encoding="utf-8", newline="") as handle:
            findings = list(csv.DictReader(handle))
        self.assertEqual(len(findings), 2)
        self.assertTrue(
            all(
                row["status"] == "FIXED_VALIDATED"
                and row["blocks_stage_acceptance"] == "false"
                for row in findings
            )
        )
        with builder.RISKS_PATH.open(encoding="utf-8", newline="") as handle:
            risks = list(csv.DictReader(handle))
        self.assertEqual(len(risks), 4)
        self.assertTrue(
            all(
                row["status"] == "ROUTED_RESIDUAL"
                and row["plan_complete"] == "true"
                and row["blocks_s18_stage_acceptance"] == "false"
                for row in risks
            )
        )

    def test_human_reports_use_plain_chinese(self) -> None:
        review = builder.REVIEW_REPORT_PATH.read_text(encoding="utf-8")
        tests = builder.TEST_RESULTS_PATH.read_text(encoding="utf-8")
        for phrase in (
            "报告与导出仍显示旧金额",
            "预警卡没有直接处理入口",
        ):
            self.assertIn(phrase, review)
        self.assertIn("246/246", tests)


if __name__ == "__main__":
    unittest.main()
