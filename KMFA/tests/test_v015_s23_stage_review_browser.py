from __future__ import annotations

import json
import struct
import unittest

from KMFA.tools import build_v015_s23_stage_review as builder


class Stage23ReviewBrowserEvidenceTests(unittest.TestCase):
    def test_role_tasks_bind_exact_business_targets(self) -> None:
        evidence = json.loads((builder.PROJECT_ROOT / "stage_artifacts/V015_S23_P3_STABILITY_USABILITY/machine/browser_acceptance.json").read_text(encoding="utf-8"))
        usability = evidence["usability"]
        self.assertEqual(usability["business_target_assertion_count"], 11)
        self.assertEqual(usability["business_target_assertion_fail_count"], 0)
        self.assertEqual(usability["role_persistence_check_count"], 1)
        self.assertEqual([row["target_path"] for row in usability["tasks"]], ["/collections", "/reports", "/tax-policy"])
        self.assertTrue(all(all(row["target_assertions"].values()) for row in usability["tasks"]))

    def test_real_browser_evidence_is_reused_without_duplicates(self) -> None:
        contract = json.loads(builder.BROWSER_CONTRACT_PATH.read_text(encoding="utf-8"))
        self.assertEqual(contract["evidence_strategy"], "REUSE_AND_RERUN_PREDECESSOR_REAL_BROWSER_EVIDENCE")
        self.assertEqual((contract["required_flow_count"], contract["visual_evidence_count"], contract["duplicate_review_screenshot_count"]), (14, 15, 0))
        for path in builder.VISUAL_EVIDENCE_PATHS:
            body = path.read_bytes()
            self.assertGreater(len(body), 10_000)
            self.assertEqual(body[:8], b"\x89PNG\r\n\x1a\n")
            width, height = struct.unpack(">II", body[16:24])
            self.assertGreaterEqual(width, 320)
            self.assertGreaterEqual(height, 500)


if __name__ == "__main__":
    unittest.main()
