from __future__ import annotations

import unittest

from arxiv_daily_push.stage2_d1_gate import (
    S2PBT05_FORBIDDEN_FLAGS,
    S2PBT05_REQUIRED_ALIAS_TASKS,
    S2PBT05_REQUIRED_READY_FLAGS,
    S2PBT05_REQUIRED_SOURCE_SERVERS,
    S2PBT05_REQUIRED_ZERO_COUNTERS,
    build_s2pbt05_d1_qualification_report,
    validate_s2pbt05_d1_qualification_report,
)


class Stage2D1GateTests(unittest.TestCase):
    def test_d1_qualification_receipt_passes_from_existing_s2pbt01_evidence(self) -> None:
        report = build_s2pbt05_d1_qualification_report(generated_at="2026-06-26T18:40:00+10:00")

        self.assertEqual(report["status"], "pass")
        self.assertEqual(tuple(report["alias_tasks"]), S2PBT05_REQUIRED_ALIAS_TASKS)
        self.assertEqual(tuple(report["source_servers"]), S2PBT05_REQUIRED_SOURCE_SERVERS)
        self.assertEqual(report["source_domain"], "D1")
        self.assertEqual(report["replay_summary"]["success_count"], 30)
        self.assertEqual(report["replay_summary"]["real_preprint_source_id_count"], 30)
        self.assertGreaterEqual(report["shadow_summary"]["shadow_hours"], 48)
        self.assertEqual(validate_s2pbt05_d1_qualification_report(report), [])

    def test_d1_qualification_preserves_no_production_side_effects(self) -> None:
        report = build_s2pbt05_d1_qualification_report(generated_at="2026-06-26T18:40:00+10:00")

        for flag in S2PBT05_FORBIDDEN_FLAGS:
            self.assertFalse(report[flag])
        self.assertFalse(report["source_gate_summary"]["formal_production_inclusion"])

        tampered = dict(report)
        tampered["integrated_production_accepted"] = True
        self.assertIn("integrated_production_accepted must be false", validate_s2pbt05_d1_qualification_report(tampered))

    def test_d1_qualification_requires_zero_counters_and_ready_flags(self) -> None:
        report = build_s2pbt05_d1_qualification_report(generated_at="2026-06-26T18:40:00+10:00")

        for name in S2PBT05_REQUIRED_ZERO_COUNTERS:
            self.assertEqual(report["replay_summary"][name], 0)
        for name in S2PBT05_REQUIRED_READY_FLAGS:
            self.assertTrue(report["source_gate_summary"][name])

        broken = dict(report)
        broken["replay_summary"] = dict(report["replay_summary"], future_leakage_count=1)
        self.assertIn("S2PBT05 future_leakage_count must be zero", validate_s2pbt05_d1_qualification_report(broken))


if __name__ == "__main__":
    unittest.main()
