from __future__ import annotations

import unittest

from KMFA.tools import build_v015_s17_stage_review as builder


class S17StageReviewEvidenceTests(unittest.TestCase):
    def test_taskpack_source_and_predecessors_are_bound(self) -> None:
        self.assertEqual(builder.source_contract()["source_integrity_status"], "PASS")
        evidence = builder.phase_evidence()
        self.assertEqual(
            evidence["accounting"],
            {
                "phase_count": 3,
                "phase_passed_count": 3,
                "task_count": 9,
                "task_accepted_count": 9,
                "predecessor_public_check_count": 199,
                "predecessor_receipt_count": 60,
            },
        )
        self.assertEqual(
            [row["validation_receipt_count"] for row in evidence["phases"]],
            [20, 20, 20],
        )

    def test_cross_phase_connections_and_findings_are_closed(self) -> None:
        cross = builder.cross_phase_contracts()
        self.assertEqual(
            cross["accounting"],
            {"total": 40, "passed": 40, "failed": 0, "blocking_failed": 0},
        )
        self.assertEqual(
            [row["finding_id"] for row in builder.contract.REVIEW_FINDINGS],
            ["S17REV-F001", "S17REV-F002", "S17REV-F003", "S17REV-F004"],
        )
        self.assertTrue(
            all(
                row["status"] == "FIXED_VALIDATED"
                for row in builder.contract.REVIEW_FINDINGS
            )
        )

    def test_pending_manifest_stops_before_s18(self) -> None:
        current = builder.manifest()
        self.assertEqual(current["phase_acceptance_status"], "PENDING_FINAL_VALIDATION")
        self.assertEqual(current["decision"], "REMAIN_IN_S17_STAGE_REVIEW")
        self.assertTrue(current["s17_stage_review_started"])
        self.assertFalse(current["s17_stage_review_performed"])
        self.assertFalse(current["s18_entry_allowed"])
        self.assertFalse(current["s18_p1_entry_allowed"])
        self.assertFalse(current["s18_p1_started"])
        self.assertFalse(current["github_upload_performed"])
        self.assertFalse(current["app_reinstall_performed"])
        self.assertEqual(current["overall_accepted_phase_count"], 49)

    def test_browser_contract_covers_required_flows_and_viewports(self) -> None:
        browser = builder.browser_contract()
        self.assertEqual(len(browser["required_viewports"]), 3)
        self.assertEqual(len(browser["required_flows"]), 10)
        self.assertEqual(len(browser["required_screenshot_paths"]), 5)


if __name__ == "__main__":
    unittest.main()
