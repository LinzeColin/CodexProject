from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from arxiv_daily_push.cli import main as cli_main
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
    build_s2plt01_independent_replay_review_report,
    build_s2plt01_replay_evidence_from_records,
    build_s2plt01_replay_evidence_state,
    build_s2plt01_replay_payload,
    build_s2plt01_replay_payload_execution_report,
    validate_s2plt01_entry_precheck_report,
    validate_s2plt01_independent_replay_review_report,
    validate_s2plt01_replay_payload,
    validate_s2plt01_replay_payload_execution_report,
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

    def test_replay_payload_contract_passes_valid_no_production_records(self) -> None:
        payload = build_s2plt01_replay_payload(
            payload_id="S2PLT01-PAYLOAD-20260626-001",
            generated_at="2026-06-26T18:30:00+10:00",
            generated_by="codex-stage2-local",
            evidence_mode="actual_replay_evidence",
            replay_records=self.replay_records(),
            mail_preview_records=self.mail_preview_records(),
            source_terminal_states=self.source_terminal_states(),
            evidence_refs=["runs/s2plt01/payload.json"],
        )

        self.assertEqual(payload["status"], "pass")
        self.assertEqual(payload["replay_evidence"]["status"], "pass")
        self.assertEqual(payload["validation_errors"], [])
        for flag in S2PLT01_FORBIDDEN_FLAGS:
            self.assertFalse(payload[flag])
        self.assertEqual(validate_s2plt01_replay_payload(payload), [])

        report = build_s2plt01_entry_precheck_report(
            generated_at="2026-06-26T18:30:00+10:00",
            replay_evidence=payload["replay_evidence"],
        )
        self.assertEqual(report["status"], "blocked")
        self.assertIn("inherited_v7_1_p0_findings_open", report["blocking_reasons"])
        self.assertIn("inherited_v7_1_p1_findings_open", report["blocking_reasons"])

    def test_replay_payload_contract_blocks_missing_metadata_and_evidence(self) -> None:
        payload = build_s2plt01_replay_payload(
            payload_id="",
            generated_at="",
            generated_by="",
            evidence_mode="invalid",
            replay_records=[],
            mail_preview_records=[],
            source_terminal_states=[],
            evidence_refs=[],
        )

        self.assertEqual(payload["status"], "blocked")
        self.assertIn("payload_id_required", payload["validation_errors"])
        self.assertIn("generated_at_required", payload["validation_errors"])
        self.assertIn("generated_by_required", payload["validation_errors"])
        self.assertIn("invalid_evidence_mode", payload["validation_errors"])
        self.assertIn("replay_records_required", payload["validation_errors"])
        self.assertIn("mail_preview_records_required", payload["validation_errors"])
        self.assertIn("source_terminal_states_required", payload["validation_errors"])
        self.assertIn("evidence_refs_required", payload["validation_errors"])
        errors = validate_s2plt01_replay_payload(payload)
        self.assertIn("S2PLT01 replay payload_id is required", errors)
        self.assertIn("S2PLT01 replay payload evidence_mode is invalid", errors)
        self.assertIn("S2PLT01 replay payload evidence_refs are required", errors)

    def test_replay_payload_validator_rejects_production_side_effect_and_hash_drift(self) -> None:
        payload = build_s2plt01_replay_payload(
            payload_id="S2PLT01-PAYLOAD-20260626-001",
            generated_at="2026-06-26T18:30:00+10:00",
            generated_by="codex-stage2-local",
            evidence_mode="fixture_replay_contract",
            replay_records=self.replay_records(),
            mail_preview_records=self.mail_preview_records(),
            source_terminal_states=self.source_terminal_states(),
            evidence_refs=["runs/s2plt01/payload-fixture.json"],
        )
        tampered = dict(payload)
        tampered["real_smtp_sent"] = True

        errors = validate_s2plt01_replay_payload(tampered)

        self.assertIn("real_smtp_sent must be false", errors)
        self.assertIn("S2PLT01 replay payload_hash does not match payload content", errors)

    def test_replay_payload_execution_report_packages_payload_but_stays_blocked_by_inherited_findings(self) -> None:
        report = build_s2plt01_replay_payload_execution_report(
            execution_id="S2PLT01-REPLAY-PAYLOAD-EXECUTION-20260626-001",
            generated_at="2026-06-26T19:10:00+10:00",
            generated_by="codex-stage2-local",
            evidence_mode="actual_replay_evidence",
            replay_records=self.replay_records(),
            mail_preview_records=self.mail_preview_records(),
            source_terminal_states=self.source_terminal_states(),
            evidence_refs=["runs/s2plt01/replay_payload_execution.json"],
        )

        self.assertEqual(report["status"], "blocked")
        self.assertTrue(report["payload_execution_package_passed"])
        self.assertFalse(report["entry_precheck_passed"])
        self.assertEqual(report["payload"]["status"], "pass")
        self.assertEqual(report["entry_precheck"]["status"], "blocked")
        self.assertIn("inherited_v7_1_p0_findings_open", report["blocking_reasons"])
        self.assertIn("inherited_v7_1_p1_findings_open", report["blocking_reasons"])
        self.assertNotIn("full_30_day_replay_not_executed", report["blocking_reasons"])
        self.assertNotIn("mail_preview_count_not_proven", report["blocking_reasons"])
        self.assertNotIn("source_terminal_states_not_proven", report["blocking_reasons"])
        for flag in S2PLT01_FORBIDDEN_FLAGS:
            self.assertFalse(report[flag])
            self.assertFalse(report["payload"][flag])
            self.assertFalse(report["entry_precheck"][flag])
        self.assertEqual(validate_s2plt01_replay_payload_execution_report(report), [])

    def test_replay_payload_execution_report_blocks_invalid_payload_inputs(self) -> None:
        report = build_s2plt01_replay_payload_execution_report(
            execution_id="",
            generated_at="",
            generated_by="",
            evidence_mode="invalid",
            replay_records=[],
            mail_preview_records=[],
            source_terminal_states=[],
            evidence_refs=[],
        )

        self.assertEqual(report["status"], "blocked")
        self.assertFalse(report["payload_execution_package_passed"])
        self.assertIn("payload_id_required", report["blocking_reasons"])
        self.assertIn("replay_payload_execution_package_not_passed", report["blocking_reasons"])
        errors = validate_s2plt01_replay_payload_execution_report(report)
        self.assertIn("S2PLT01 replay payload execution_id is required", errors)
        self.assertIn("S2PLT01 replay payload execution evidence_mode is invalid", errors)
        self.assertIn("S2PLT01 replay payload execution evidence_refs are required", errors)

    def test_replay_payload_execution_validator_rejects_production_side_effect_and_hash_drift(self) -> None:
        report = build_s2plt01_replay_payload_execution_report(
            execution_id="S2PLT01-REPLAY-PAYLOAD-EXECUTION-20260626-001",
            generated_at="2026-06-26T19:10:00+10:00",
            generated_by="codex-stage2-local",
            evidence_mode="fixture_replay_contract",
            replay_records=self.replay_records(),
            mail_preview_records=self.mail_preview_records(),
            source_terminal_states=self.source_terminal_states(),
            evidence_refs=["runs/s2plt01/replay_payload_execution_fixture.json"],
        )
        tampered = dict(report)
        tampered["scheduler_enabled"] = True

        errors = validate_s2plt01_replay_payload_execution_report(tampered)

        self.assertIn("scheduler_enabled must be false", errors)
        self.assertIn("S2PLT01 replay payload execution_hash does not match report content", errors)

    def test_replay_payload_execution_cli_returns_success_for_valid_package_with_blocked_precheck(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "s2plt01_evidence.json"
            input_path.write_text(
                json.dumps(
                    {
                        "replay_records": self.replay_records(),
                        "mail_preview_records": self.mail_preview_records(),
                        "source_terminal_states": self.source_terminal_states(),
                        "evidence_refs": ["runs/s2plt01/replay_payload_execution_cli.json"],
                    },
                    ensure_ascii=False,
                    sort_keys=True,
                ),
                encoding="utf-8",
            )
            stdout = io.StringIO()

            with redirect_stdout(stdout):
                exit_code = cli_main(
                    [
                        "stage2-replay-payload-execution",
                        "--input",
                        str(input_path),
                        "--execution-id",
                        "S2PLT01-REPLAY-PAYLOAD-EXECUTION-CLI-20260626-001",
                        "--generated-at",
                        "2026-06-26T19:20:00+10:00",
                        "--json",
                    ]
                )

        output = json.loads(stdout.getvalue())
        self.assertEqual(exit_code, 0)
        self.assertEqual(output["status"], "blocked")
        self.assertTrue(output["payload_execution_package_passed"])
        self.assertFalse(output["entry_precheck_passed"])
        self.assertIn("inherited_v7_1_p0_findings_open", output["blocking_reasons"])
        self.assertIn("inherited_v7_1_p1_findings_open", output["blocking_reasons"])

    def test_independent_replay_review_accepts_valid_package_but_keeps_s2plt01_blocked(self) -> None:
        execution_report = build_s2plt01_replay_payload_execution_report(
            execution_id="S2PLT01-REPLAY-PAYLOAD-EXECUTION-20260626-001",
            generated_at="2026-06-26T19:10:00+10:00",
            generated_by="codex-stage2-local",
            evidence_mode="actual_replay_evidence",
            replay_records=self.replay_records(),
            mail_preview_records=self.mail_preview_records(),
            source_terminal_states=self.source_terminal_states(),
            evidence_refs=["runs/s2plt01/replay_payload_execution.json"],
        )

        review = build_s2plt01_independent_replay_review_report(
            review_id="S2PLT01-INDEPENDENT-REVIEW-20260626-001",
            generated_at="2026-06-26T20:00:00+10:00",
            reviewer_id="codex-independent-reviewer",
            reviewer_role="independent_stage2_replay_reviewer",
            reviewer_involved_in_s2plt01_implementation=False,
            replay_execution_report=execution_report,
            ci_evidence_refs=[
                "https://github.com/LinzeColin/CodexProject/actions/runs/28217724286",
                "https://github.com/LinzeColin/CodexProject/actions/runs/28217724275",
            ],
            evidence_refs=["reviews/s2plt01/independent_replay_review.json"],
        )

        self.assertEqual(review["status"], "blocked")
        self.assertTrue(review["review_package_passed"])
        self.assertFalse(review["s2plt01_acceptance_claimed"])
        self.assertFalse(review["production_acceptance_claimed"])
        self.assertIn("inherited_v7_1_p0_findings_open", review["blocking_reasons"])
        self.assertIn("inherited_v7_1_p1_findings_open", review["blocking_reasons"])
        self.assertNotIn("reviewer_independence_not_proven", review["blocking_reasons"])
        self.assertNotIn("replay_execution_report_invalid", review["blocking_reasons"])
        for flag in S2PLT01_FORBIDDEN_FLAGS:
            self.assertFalse(review[flag])
        self.assertEqual(validate_s2plt01_independent_replay_review_report(review), [])

    def test_independent_replay_review_blocks_self_review_missing_ci_and_hash_drift(self) -> None:
        execution_report = build_s2plt01_replay_payload_execution_report(
            execution_id="S2PLT01-REPLAY-PAYLOAD-EXECUTION-20260626-001",
            generated_at="2026-06-26T19:10:00+10:00",
            generated_by="codex-stage2-local",
            evidence_mode="fixture_replay_contract",
            replay_records=self.replay_records(),
            mail_preview_records=self.mail_preview_records(),
            source_terminal_states=self.source_terminal_states(),
            evidence_refs=["runs/s2plt01/replay_payload_execution_fixture.json"],
        )
        review = build_s2plt01_independent_replay_review_report(
            review_id="S2PLT01-INDEPENDENT-REVIEW-20260626-002",
            generated_at="2026-06-26T20:00:00+10:00",
            reviewer_id="codex-same-agent",
            reviewer_role="implementation_agent",
            reviewer_involved_in_s2plt01_implementation=True,
            replay_execution_report=execution_report,
            ci_evidence_refs=[],
            evidence_refs=[],
        )

        self.assertEqual(review["status"], "blocked")
        self.assertFalse(review["review_package_passed"])
        self.assertIn("reviewer_independence_not_proven", review["blocking_reasons"])
        self.assertIn("ci_evidence_refs_missing", review["blocking_reasons"])
        self.assertIn("review_evidence_refs_missing", review["blocking_reasons"])
        errors = validate_s2plt01_independent_replay_review_report(review)
        self.assertIn("S2PLT01 independent replay review ci_evidence_refs are required", errors)
        self.assertIn("S2PLT01 independent replay review evidence_refs are required", errors)

        tampered = dict(review)
        tampered["real_smtp_sent"] = True
        tampered["review_hash"] = review["review_hash"]
        errors = validate_s2plt01_independent_replay_review_report(tampered)
        self.assertIn("real_smtp_sent must be false", errors)
        self.assertIn("S2PLT01 independent replay review_hash does not match report content", errors)

    def test_independent_replay_review_cli_returns_success_for_valid_review_package(self) -> None:
        execution_report = build_s2plt01_replay_payload_execution_report(
            execution_id="S2PLT01-REPLAY-PAYLOAD-EXECUTION-CLI-20260626-001",
            generated_at="2026-06-26T19:20:00+10:00",
            generated_by="codex-stage2-local",
            evidence_mode="actual_replay_evidence",
            replay_records=self.replay_records(),
            mail_preview_records=self.mail_preview_records(),
            source_terminal_states=self.source_terminal_states(),
            evidence_refs=["runs/s2plt01/replay_payload_execution_cli.json"],
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "execution_report.json"
            input_path.write_text(json.dumps(execution_report, ensure_ascii=False, sort_keys=True), encoding="utf-8")
            stdout = io.StringIO()

            with redirect_stdout(stdout):
                exit_code = cli_main(
                    [
                        "stage2-independent-replay-review",
                        "--execution-report",
                        str(input_path),
                        "--review-id",
                        "S2PLT01-INDEPENDENT-REVIEW-CLI-20260626-001",
                        "--generated-at",
                        "2026-06-26T20:10:00+10:00",
                        "--reviewer-id",
                        "codex-independent-reviewer",
                        "--reviewer-role",
                        "independent_stage2_replay_reviewer",
                        "--ci-evidence-ref",
                        "https://github.com/LinzeColin/CodexProject/actions/runs/28217724286",
                        "--evidence-ref",
                        "reviews/s2plt01/independent_replay_review_cli.json",
                        "--json",
                    ]
                )

        output = json.loads(stdout.getvalue())
        self.assertEqual(exit_code, 0)
        self.assertEqual(output["status"], "blocked")
        self.assertTrue(output["review_package_passed"])
        self.assertIn("inherited_v7_1_p0_findings_open", output["blocking_reasons"])
        self.assertIn("inherited_v7_1_p1_findings_open", output["blocking_reasons"])

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

    def test_current_s2plt01_records_recognize_independent_review_receipt(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        review_manifest_path = (
            repo_root / "governance/run_manifests/ADP-S2PLT01-INDEPENDENT-REPLAY-REVIEW-20260626.json"
        )
        self.assertTrue(review_manifest_path.exists())
        review_manifest = json.loads(review_manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(review_manifest["task_id"], "S2PLT01-INDEPENDENT-REPLAY-REVIEW")
        self.assertNotIn("independent_s2plt01_review_not_completed", review_manifest["blocking_reasons"])

        manifest_paths = [
            repo_root / "governance/run_manifests/ADP-S2PLT01-REPLAY-EVIDENCE-GATE-20260626.json",
            repo_root / "governance/run_manifests/ADP-S2PLT01-REPLAY-PAYLOAD-CONTRACT-20260626.json",
            repo_root / "governance/run_manifests/ADP-S2PLT01-REPLAY-PAYLOAD-EXECUTION-20260626.json",
        ]
        for manifest_path in manifest_paths:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertNotIn("independent_s2plt01_review_not_completed", manifest["blocking_reasons"])
            self.assertIn("inherited_v7_1_p0_findings_open", manifest["blocking_reasons"])
            self.assertIn("inherited_v7_1_p1_findings_open", manifest["blocking_reasons"])
            self.assertFalse(manifest["s2plt01_accepted"])
            self.assertFalse(manifest["stage2_integrated_production_accepted"])

        phase_paths = [
            repo_root / "arxiv-daily-push/docs/phase_records/PHASE_S2PLT01_REPLAY_EVIDENCE_GATE.md",
            repo_root / "arxiv-daily-push/docs/phase_records/PHASE_S2PLT01_REPLAY_PAYLOAD_CONTRACT.md",
            repo_root / "arxiv-daily-push/docs/phase_records/PHASE_S2PLT01_REPLAY_PAYLOAD_EXECUTION.md",
        ]
        for phase_path in phase_paths:
            text = phase_path.read_text(encoding="utf-8")
            self.assertNotIn("independent S2PLT01 replay review: missing", text)


if __name__ == "__main__":
    unittest.main()
