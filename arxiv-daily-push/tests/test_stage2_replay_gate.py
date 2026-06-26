from __future__ import annotations

import unittest

from arxiv_daily_push.stage2_replay_gate import (
    S2PLT01_BLOCKING_REASONS,
    S2PLT01_FORBIDDEN_FLAGS,
    S2PLT01_REQUIRED_MAIL_PRODUCTS,
    S2PLT01_REQUIRED_DEPENDENCIES,
    S2PLT01_REQUIRED_MAIL_PREVIEWS,
    S2PLT01_REQUIRED_REPLAY_DAYS,
    build_s2plt01_audit_blocker_state,
    build_s2plt01_dependency_state,
    build_s2plt01_entry_precheck_report,
    build_s2plt01_replay_evidence_from_records,
    build_s2plt01_replay_evidence_state,
    validate_s2plt01_entry_precheck_report,
)


class Stage2ReplayGateTests(unittest.TestCase):
    def replay_records(self) -> list[dict]:
        records = []
        for day in range(1, 31):
            records.append(
                {
                    "as_of_date": f"2026-05-{day:02d}",
                    "status": "pass",
                    "source_domains": ["D1", "D2", "D3", "D4"],
                    "reading_boards": ["B1", "B2", "B3", "B4", "B5", "B6"],
                    "future_leakage_count": 0,
                    "p0_p1_blocker_count": 0,
                    "evidence_refs": [f"replay/{day:02d}.json"],
                }
            )
        return records

    def mail_preview_records(self) -> list[dict]:
        records = []
        for day in range(1, 31):
            for product_id in S2PLT01_REQUIRED_MAIL_PRODUCTS:
                records.append(
                    {
                        "as_of_date": f"2026-05-{day:02d}",
                        "mail_product_id": product_id,
                        "status": "pass",
                        "email_template_contract": "EMAIL_LEARNING_V1",
                        "real_smtp_sent": False,
                        "evidence_refs": [f"mail/{day:02d}/{product_id}.json"],
                    }
                )
        return records

    def source_terminal_states(self) -> list[dict]:
        return [
            {
                "source_domain": domain,
                "status": "terminal_ready",
                "terminal_state": "qualified_no_send",
                "production_inclusion": False,
                "evidence_refs": [f"terminal/{domain}.json"],
            }
            for domain in ("D1", "D2", "D3", "D4")
        ]

    def test_dependency_state_includes_completed_d1_domain_qualification(self) -> None:
        state = build_s2plt01_dependency_state()

        self.assertEqual(state["status"], "pass")
        self.assertEqual(tuple(state["required_dependencies"]), S2PLT01_REQUIRED_DEPENDENCIES)
        self.assertEqual(state["missing_dependencies"], [])
        for task_id in ("S2PBT05", "S2PCT07", "S2PDT04", "S2PET04", "S2PFT05", "S2PKT05"):
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

    def test_replay_evidence_from_records_passes_with_30_days_120_mail_previews_and_terminal_sources(self) -> None:
        state = build_s2plt01_replay_evidence_from_records(
            replay_records=self.replay_records(),
            mail_preview_records=self.mail_preview_records(),
            source_terminal_states=self.source_terminal_states(),
        )

        self.assertEqual(state["status"], "pass")
        self.assertEqual(state["observed_replay_days"], 30)
        self.assertEqual(state["observed_mail_previews"], 120)
        self.assertTrue(state["source_terminal_states_proven"])
        self.assertEqual(state["future_leakage_count"], 0)
        self.assertEqual(state["blocking_reasons"], [])
        self.assertTrue(all(state["available_outputs"].values()))

    def test_replay_evidence_from_records_blocks_missing_mail_preview(self) -> None:
        state = build_s2plt01_replay_evidence_from_records(
            replay_records=self.replay_records(),
            mail_preview_records=self.mail_preview_records()[:-1],
            source_terminal_states=self.source_terminal_states(),
        )

        self.assertEqual(state["status"], "blocked")
        self.assertEqual(state["observed_mail_previews"], 119)
        self.assertIn("mail_preview_count_not_proven", state["blocking_reasons"])

    def test_replay_evidence_from_records_blocks_missing_terminal_source_domain(self) -> None:
        state = build_s2plt01_replay_evidence_from_records(
            replay_records=self.replay_records(),
            mail_preview_records=self.mail_preview_records(),
            source_terminal_states=self.source_terminal_states()[:-1],
        )

        self.assertEqual(state["status"], "blocked")
        self.assertFalse(state["source_terminal_states_proven"])
        self.assertIn("source_terminal_states_not_proven", state["blocking_reasons"])

    def test_replay_evidence_from_records_blocks_invalid_replay_date(self) -> None:
        replay_records = self.replay_records()
        replay_records[0]["as_of_date"] = "2026-99-99"

        state = build_s2plt01_replay_evidence_from_records(
            replay_records=replay_records,
            mail_preview_records=self.mail_preview_records(),
            source_terminal_states=self.source_terminal_states(),
        )

        self.assertEqual(state["status"], "blocked")
        self.assertEqual(state["observed_replay_days"], 29)
        self.assertIn("full_30_day_replay_not_executed", state["blocking_reasons"])

    def test_entry_precheck_can_consume_replay_evidence_but_stays_blocked_by_inherited_findings(self) -> None:
        replay_evidence = build_s2plt01_replay_evidence_from_records(
            replay_records=self.replay_records(),
            mail_preview_records=self.mail_preview_records(),
            source_terminal_states=self.source_terminal_states(),
        )

        report = build_s2plt01_entry_precheck_report(
            generated_at="2026-06-26T18:00:00+10:00",
            replay_evidence=replay_evidence,
        )

        self.assertEqual(report["status"], "blocked")
        self.assertNotIn("full_30_day_replay_not_executed", report["blocking_reasons"])
        self.assertNotIn("mail_preview_count_not_proven", report["blocking_reasons"])
        self.assertNotIn("source_terminal_states_not_proven", report["blocking_reasons"])
        self.assertIn("inherited_v7_1_p0_findings_open", report["blocking_reasons"])
        self.assertIn("inherited_v7_1_p1_findings_open", report["blocking_reasons"])
        self.assertEqual(validate_s2plt01_entry_precheck_report(report), [])

    def test_entry_precheck_report_fails_closed_without_production_side_effects(self) -> None:
        report = build_s2plt01_entry_precheck_report(generated_at="2026-06-26T18:00:00+10:00")

        self.assertEqual(report["status"], "blocked")
        self.assertFalse(report["production_acceptance_claimed"])
        for flag in S2PLT01_FORBIDDEN_FLAGS:
            self.assertFalse(report[flag])
        for reason in S2PLT01_BLOCKING_REASONS:
            self.assertIn(reason, report["blocking_reasons"])
        self.assertNotIn("s2pbt05_missing", report["blocking_reasons"])
        self.assertEqual(validate_s2plt01_entry_precheck_report(report), [])

        tampered = dict(report)
        tampered["s2plt01_accepted"] = True
        self.assertIn("s2plt01_accepted must be false", validate_s2plt01_entry_precheck_report(tampered))


if __name__ == "__main__":
    unittest.main()
