from __future__ import annotations

import unittest

from arxiv_daily_push.stage2_replay_gate import (
    S2PLT01_BLOCKING_REASONS,
    S2PLT01_FORBIDDEN_FLAGS,
    S2PLT01_REQUIRED_DEPENDENCIES,
    S2PLT01_REQUIRED_MAIL_PREVIEWS,
    S2PLT01_REQUIRED_REPLAY_DAYS,
    build_s2plt01_audit_blocker_state,
    build_s2plt01_dependency_state,
    build_s2plt01_entry_precheck_report,
    build_s2plt01_replay_evidence_state,
    validate_s2plt01_entry_precheck_report,
)


class Stage2ReplayGateTests(unittest.TestCase):
    def test_dependency_state_blocks_missing_d1_domain_qualification(self) -> None:
        state = build_s2plt01_dependency_state()

        self.assertEqual(state["status"], "blocked")
        self.assertEqual(tuple(state["required_dependencies"]), S2PLT01_REQUIRED_DEPENDENCIES)
        self.assertIn("S2PBT05", state["missing_dependencies"])
        for task_id in ("S2PCT07", "S2PDT04", "S2PET04", "S2PFT05", "S2PKT05"):
            self.assertIn(task_id, state["completed_dependencies"])

    def test_audit_blocker_state_blocks_current_inherited_p0_p1(self) -> None:
        state = build_s2plt01_audit_blocker_state()

        self.assertEqual(state["status"], "blocked")
        self.assertEqual(state["inherited_v7_1_open_p0_findings"], 8)
        self.assertEqual(state["inherited_v7_1_open_p1_findings"], 37)
        self.assertFalse(state["checks"]["P0_zero"])
        self.assertFalse(state["checks"]["P1_zero"])

        cleared = build_s2plt01_audit_blocker_state(inherited_p0=0, inherited_p1=0)
        self.assertEqual(cleared["status"], "pass")

    def test_replay_evidence_state_requires_full_system_outputs(self) -> None:
        state = build_s2plt01_replay_evidence_state()

        self.assertEqual(state["status"], "blocked")
        self.assertEqual(state["required_replay_days"], S2PLT01_REQUIRED_REPLAY_DAYS)
        self.assertEqual(state["observed_replay_days"], 0)
        self.assertEqual(state["required_mail_previews"], S2PLT01_REQUIRED_MAIL_PREVIEWS)
        self.assertEqual(state["observed_mail_previews"], 0)
        self.assertEqual(set(state["required_source_domains"]), {"D1", "D2", "D3", "D4"})
        self.assertEqual(set(state["required_reading_boards"]), {"B1", "B2", "B3", "B4", "B5", "B6"})
        self.assertFalse(any(state["available_outputs"].values()))

    def test_entry_precheck_report_fails_closed_without_production_side_effects(self) -> None:
        report = build_s2plt01_entry_precheck_report(generated_at="2026-06-26T18:00:00+10:00")

        self.assertEqual(report["status"], "blocked")
        self.assertFalse(report["production_acceptance_claimed"])
        for flag in S2PLT01_FORBIDDEN_FLAGS:
            self.assertFalse(report[flag])
        for reason in S2PLT01_BLOCKING_REASONS:
            self.assertIn(reason, report["blocking_reasons"])
        self.assertEqual(validate_s2plt01_entry_precheck_report(report), [])

        tampered = dict(report)
        tampered["s2plt01_accepted"] = True
        self.assertIn("s2plt01_accepted must be false", validate_s2plt01_entry_precheck_report(tampered))


if __name__ == "__main__":
    unittest.main()
