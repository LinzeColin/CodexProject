from __future__ import annotations

import unittest

from KMFA.tools import build_v015_s15_stage_review as builder


class S15StageReviewEvidenceTests(unittest.TestCase):
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
                "predecessor_public_check_count": 36,
                "predecessor_receipt_count": 60,
            },
        )
        self.assertEqual([row["validation_receipt_count"] for row in evidence["phases"]], [20, 20, 20])

    def test_cross_phase_connections_and_findings_are_closed(self) -> None:
        cross = builder.cross_phase_contracts()
        self.assertEqual(cross["accounting"], {"total": 41, "passed": 41, "failed": 0, "blocking_failed": 0})
        self.assertEqual([row["finding_id"] for row in builder.findings()], ["S15REV-F001", "S15REV-F002", "S15REV-F003", "S15REV-F004"])
        self.assertTrue(all(row["status"] == "FIXED_VALIDATED" for row in builder.findings()))

    def test_residual_risks_are_routed_and_nonblocking(self) -> None:
        risks = builder.risks()
        self.assertEqual(len(risks), 5)
        self.assertTrue(all(row["status"] == "ROUTED_RESIDUAL" for row in risks))
        self.assertTrue(all(row["plan_complete"] == "true" for row in risks))
        self.assertTrue(all(row["blocks_s15_stage_acceptance"] == "false" for row in risks))

    def test_pending_manifest_stops_before_s16(self) -> None:
        manifest = builder.manifest([])
        self.assertEqual(manifest["phase_acceptance_status"], "PENDING_FINAL_VALIDATION")
        self.assertEqual(manifest["decision"], "REMAIN_IN_S15_STAGE_REVIEW")
        self.assertTrue(manifest["s15_stage_review_started"])
        self.assertFalse(manifest["s15_stage_review_performed"])
        self.assertFalse(manifest["s16_entry_allowed"])
        self.assertFalse(manifest["s16_p1_started"])
        self.assertFalse(manifest["github_upload_performed"])
        self.assertFalse(manifest["app_reinstall_performed"])
        self.assertEqual(manifest["overall_accepted_phase_count"], 43)

    def test_browser_contract_covers_desktop_tablet_and_mobile(self) -> None:
        browser = builder.browser_contract()
        self.assertEqual(len(browser["required_viewports"]), 3)
        self.assertEqual(len(browser["required_flows"]), 8)
        self.assertEqual(len(browser["screenshot_paths"]), 4)

    def test_deterministic_outputs_are_exact(self) -> None:
        self.assertEqual(builder.check_outputs(), [])


if __name__ == "__main__":
    unittest.main()
