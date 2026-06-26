import csv
import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ADP = ROOT / "arxiv-daily-push"
FINDINGS = ADP / "docs" / "pursuing_goal" / "v7_1" / "09_并行审查" / "问题清单.csv"
P0_RECEIPT = ADP / "docs" / "phase_records" / "PHASE_S2PMT07_P0_INDEPENDENT_REVIEW_RECEIPT.md"
P1_RECEIPT = ADP / "docs" / "phase_records" / "PHASE_S2PMT07_P1_INDEPENDENT_REVIEW_RECEIPT.md"
P1_MANIFEST = ROOT / "governance" / "run_manifests" / "ADP-S2PMT07-P1-INDEPENDENT-REVIEW-RECEIPT-20260626.json"


class S2PMT07ReviewReceiptTests(unittest.TestCase):
    def test_p1_receipt_covers_all_inherited_p1_findings_without_closure(self):
        findings = list(csv.DictReader(FINDINGS.read_text(encoding="utf-8-sig").splitlines()))
        p1_findings = [row for row in findings if row["severity"] == "P1"]
        receipt = P1_RECEIPT.read_text(encoding="utf-8")
        table_rows = re.findall(r"^\| `[^`]+` \| `[^`]+` \|", receipt, flags=re.MULTILINE)

        self.assertEqual(len(p1_findings), 37)
        self.assertEqual(len(table_rows), 37)
        self.assertIn("status: `review_receipt_ready_no_closure_claim`", receipt)
        self.assertIn("This receipt organizes the inherited V7.1 P1 evidence set", receipt)
        self.assertIn("does not close any P0/P1 finding", receipt)
        self.assertIn("P1 findings retained open | 37", receipt)
        self.assertIn("p1_closure_not_claimed", receipt)
        self.assertIn("integrated_production_accepted`: `false`", receipt)
        self.assertNotIn("P1 closed", receipt)
        self.assertNotIn("INTEGRATED_PRODUCTION_ACCEPTED` claim: `true`", receipt)

    def test_p1_manifest_preserves_blocker_counts_and_no_production_flags(self):
        payload = json.loads(P1_MANIFEST.read_text(encoding="utf-8"))

        self.assertEqual(payload["status"], "review_receipt_ready_no_closure_claim")
        self.assertFalse(payload["reviewer_independence_claimed"])
        self.assertFalse(payload["independent_review_signoff_present"])
        self.assertFalse(payload["closure_claimed"])
        self.assertFalse(payload["p0_closure_claimed"])
        self.assertFalse(payload["p1_closure_claimed"])
        self.assertEqual(payload["inherited_v7_1_open_p0_findings_before"], 8)
        self.assertEqual(payload["inherited_v7_1_open_p0_findings_after"], 8)
        self.assertEqual(payload["inherited_v7_1_open_p1_findings_before"], 37)
        self.assertEqual(payload["inherited_v7_1_open_p1_findings_after"], 37)
        self.assertEqual(len(payload["p1_findings"]), 37)
        self.assertEqual(payload["p1_findings_by_task"]["S2PMT03"], 8)
        self.assertEqual(payload["p1_findings_by_track"]["A_安全代码并发"], 16)
        for key, value in payload["forbidden_side_effects"].items():
            with self.subTest(key=key):
                self.assertIs(value, False)

    def test_p0_receipt_still_retains_p0_and_p1_blockers(self):
        receipt = P0_RECEIPT.read_text(encoding="utf-8")

        self.assertIn("status: `review_receipt_ready_no_closure_claim`", receipt)
        self.assertIn("p0_closure_not_claimed", receipt)
        self.assertIn("p1_closure_not_claimed", receipt)
        self.assertIn("integrated_production_accepted`: `false`", receipt)


if __name__ == "__main__":
    unittest.main()
