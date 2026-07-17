from __future__ import annotations

import csv
import json
import unittest

from KMFA.tools import build_v015_s23_stage_review as builder


class Stage23ReviewArtifactTests(unittest.TestCase):
    def test_builder_is_exact_for_current_state(self) -> None:
        state, run_id, head = builder._current_state()
        builder.check_outputs(builder.expected_outputs(state, run_id, head))

    def test_manifest_stops_before_s24_until_formal_acceptance(self) -> None:
        manifest = json.loads(builder.MANIFEST_PATH.read_text(encoding="utf-8"))
        self.assertFalse(manifest["s24_started"] or manifest["s24_p1_started"])
        self.assertEqual((manifest["overall_phase_accepted_count"], manifest["overall_phase_total_count"]), (67, 72))
        self.assertFalse(manifest["github_upload_performed"] or manifest["app_reinstall_performed"])

    def test_findings_closed_limitations_visible_and_open_risk_empty(self) -> None:
        with builder.FINDINGS_PATH.open(encoding="utf-8", newline="") as handle:
            findings = list(csv.DictReader(handle))
        with builder.RISKS_PATH.open(encoding="utf-8", newline="") as handle:
            risks = list(csv.DictReader(handle))
        limitations = json.loads(builder.LIMITATIONS_PATH.read_text(encoding="utf-8"))
        self.assertEqual(len(findings), 2)
        self.assertTrue(all(row["status"] == "FIXED_VALIDATED" for row in findings))
        self.assertEqual(len(limitations["limitations"]), 2)
        self.assertEqual(risks, [])

    def test_phase_evidence_is_bound_to_three_formal_acceptances(self) -> None:
        phase = json.loads(builder.PHASE_EVIDENCE_PATH.read_text(encoding="utf-8"))
        self.assertEqual(phase["accounting"], {
            "phase_count": 3,
            "phase_passed_count": 3,
            "task_count": 9,
            "task_accepted_count": 9,
            "predecessor_public_check_count": 156,
            "predecessor_receipt_count": 60,
        })
        self.assertTrue(all(row["acceptance_status"] == "PASSED" for row in phase["phases"]))


if __name__ == "__main__":
    unittest.main()
