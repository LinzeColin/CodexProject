from __future__ import annotations

import csv
import json
import unittest

from KMFA.tools import build_v015_s22_stage_review as builder


class Stage22ReviewArtifactTests(unittest.TestCase):
    def test_pending_builder_is_exact(self) -> None:
        state, run_id, head = builder._current_state()
        builder.check_outputs(builder.expected_outputs(state, run_id, head))

    def test_manifest_stops_before_s23_until_formal_acceptance(self) -> None:
        manifest = json.loads(builder.MANIFEST_PATH.read_text(encoding="utf-8"))
        self.assertFalse(manifest["s23_p1_started"])
        self.assertEqual(manifest["overall_phase_accepted_count"], 64)
        self.assertFalse(manifest["github_upload_performed"] or manifest["app_reinstall_performed"])

    def test_findings_closed_and_open_risk_register_empty(self) -> None:
        with builder.FINDINGS_PATH.open(encoding="utf-8", newline="") as handle:
            findings = list(csv.DictReader(handle))
        with builder.RISKS_PATH.open(encoding="utf-8", newline="") as handle:
            risks = list(csv.DictReader(handle))
        self.assertEqual(len(findings), 4)
        self.assertTrue(all(row["status"] == "FIXED_VALIDATED" for row in findings))
        self.assertEqual(risks, [])

    def test_required_visual_evidence_exists(self) -> None:
        self.assertEqual(len(builder.SCREENSHOT_PATHS), 5)
        self.assertTrue(all(path.is_file() and path.stat().st_size > 10_000 for path in builder.SCREENSHOT_PATHS))


if __name__ == "__main__":
    unittest.main()
