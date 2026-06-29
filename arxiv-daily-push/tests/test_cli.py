import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from arxiv_daily_push.cli import main
from arxiv_daily_push.stage2_final_gate import (
    S2PMT07_FINAL_ACCEPTANCE_BUNDLE_REQUIRED_ITEMS,
    S2PMT07_FINAL_COMMAND_EXECUTION_DECISION,
    S2PMT07_FINAL_COMMAND_EXECUTION_NO_PRODUCTION_FLAGS,
    S2PMT07_FINAL_COMMAND_EXECUTION_SCHEMA_VERSION,
    S2PMT07_INDEPENDENT_FINAL_REVIEWER_ASSIGNMENT_DECISION,
    S2PMT07_INDEPENDENT_FINAL_REVIEWER_ASSIGNMENT_NO_PRODUCTION_FLAGS,
    S2PMT07_INDEPENDENT_FINAL_REVIEWER_ASSIGNMENT_REQUIRED_FIELDS,
    S2PMT07_INDEPENDENT_FINAL_REVIEWER_ASSIGNMENT_SCHEMA_VERSION,
    S2PMT07_P0_P1_ZERO_PROOF_CLOSURE_DECISION,
    S2PMT07_P0_P1_ZERO_PROOF_NO_PRODUCTION_FLAGS,
    S2PMT07_P0_P1_ZERO_PROOF_SCHEMA_VERSION,
    S2PMT07_REQUIRED_REVIEWER_INDEPENDENCE,
    S2PMT07_REQUIRED_TEST_COMMANDS,
    build_final_command_execution_hash,
    build_independent_final_reviewer_assignment_hash,
    build_independent_final_reviewer_assignment_request_state,
    build_p0_p1_zero_proof_decision_hash,
    build_p0_p1_zero_proof_readiness_state,
)
from arxiv_daily_push.state_machine import initial_run_record


class CliTests(unittest.TestCase):
    def test_version_command(self):
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            result = main(["version"])
        self.assertEqual(result, 0)
        self.assertEqual(buffer.getvalue().strip(), "0.23.0")

    def test_doctor_json_command_warns_without_blocking_phase1(self):
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            result = main(["doctor", "--json", "--path", "."])
        self.assertIn(result, (0, 2))
        output = buffer.getvalue()
        self.assertIn('"phase": "1"', output)
        self.assertIn('"future_runtime_commands"', output)

    def test_validate_record_json_command(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "run_record.json"
            path.write_text(json.dumps(initial_run_record("run-001", "2026-06-21", "Australia/Sydney")), encoding="utf-8")
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                result = main(["validate-record", "--path", str(path), "--json"])
        self.assertEqual(result, 0)
        self.assertIn('"status": "pass"', buffer.getvalue())

    def test_send_notification_json_command_defaults_to_dry_run(self):
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            result = main(
                [
                    "send-notification",
                    "--run-id",
                    "run-001",
                    "--summary",
                    "Daily status",
                    "--date",
                    "2026-06-21",
                    "--generated-at",
                    "2026-06-21T05:00:00+10:00",
                    "--json",
                ]
            )
        self.assertEqual(result, 0)
        payload = json.loads(buffer.getvalue())
        self.assertEqual(payload["status"], "dry_run")
        self.assertFalse(payload["real_smtp_send_enabled"])

    def test_publish_release_json_command_defaults_to_dry_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            asset = Path(tmp) / "trial-evidence.json"
            asset.write_text('{"status":"pass"}\n', encoding="utf-8")
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                result = main(
                    [
                        "publish-release",
                        "--tag",
                        "adp-test-20260621",
                        "--title",
                        "ADP test release",
                        "--notes",
                        "Release notes",
                        "--asset",
                        str(asset),
                        "--generated-at",
                        "2026-06-21T05:00:00+10:00",
                        "--json",
                    ]
                )
        self.assertEqual(result, 0)
        payload = json.loads(buffer.getvalue())
        self.assertEqual(payload["status"], "dry_run")
        self.assertFalse(payload["release_upload_enabled"])
        self.assertFalse(payload["notes"]["notes_logged"])

    def test_storage_json_commands_migrate_inspect_and_rollback(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "adp.sqlite3"
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                migrate_result = main(["storage", "migrate", "--db", str(db_path), "--json"])
            migrate_payload = json.loads(buffer.getvalue())
            self.assertEqual(migrate_result, 0)
            self.assertEqual(migrate_payload["status"], "pass")
            self.assertEqual(migrate_payload["journal_mode"], "wal")
            self.assertTrue(migrate_payload["fts5_ready"])

            buffer = io.StringIO()
            with redirect_stdout(buffer):
                inspect_result = main(["storage", "inspect", "--db", str(db_path), "--json"])
            self.assertEqual(inspect_result, 0)
            self.assertEqual(json.loads(buffer.getvalue())["schema_version"], 1)

            buffer = io.StringIO()
            with redirect_stdout(buffer):
                rollback_result = main(["storage", "rollback", "--db", str(db_path), "--target-version", "0", "--json"])
            rollback_payload = json.loads(buffer.getvalue())
            self.assertEqual(rollback_result, 0)
            self.assertEqual(rollback_payload["status"], "pass")
            self.assertEqual(rollback_payload["schema_version"], 0)

    def test_validate_final_reviewer_assignment_blocks_when_artifact_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "independent_final_reviewer_assignment.json"
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                result = main(["validate-final-reviewer-assignment", "--path", str(path), "--json"])
        self.assertEqual(result, 2)
        payload = json.loads(buffer.getvalue())
        self.assertEqual(payload["status"], "blocked")
        self.assertFalse(payload["assignment_present"])
        self.assertIn("independent_final_reviewer_assignment_missing", payload["validation_errors"])
        self.assertFalse(payload["integrated_production_accepted"])
        self.assertFalse(payload["daily_operation_enabled"])

    def test_validate_p0_p1_zero_proof_blocks_when_artifact_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "p0_p1_zero_proof.json"
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                result = main(["validate-p0-p1-zero-proof", "--path", str(path), "--json"])
        self.assertEqual(result, 2)
        payload = json.loads(buffer.getvalue())
        self.assertEqual(payload["status"], "blocked")
        self.assertFalse(payload["artifact_present"])
        self.assertIn("p0_p1_zero_proof_artifact_missing", payload["validation_errors"])
        self.assertFalse(payload["p0_zero_proven_by_payload"])
        self.assertFalse(payload["p1_zero_proven_by_payload"])
        self.assertFalse(payload["production_acceptance_claimed"])
        self.assertFalse(payload["integrated_production_accepted"])
        self.assertFalse(payload["daily_operation_enabled"])

    def test_validate_final_command_execution_blocks_when_artifact_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "final_command_execution.json"
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                result = main(["validate-final-command-execution", "--path", str(path), "--json"])
        self.assertEqual(result, 2)
        payload = json.loads(buffer.getvalue())
        self.assertEqual(payload["status"], "blocked")
        self.assertFalse(payload["command_execution_present"])
        self.assertIn("final_command_execution_missing", payload["validation_errors"])
        self.assertFalse(payload["final_commands_executed_by_payload"])
        self.assertFalse(payload["production_acceptance_claimed"])
        self.assertFalse(payload["integrated_production_accepted"])
        self.assertFalse(payload["daily_operation_enabled"])

    def test_validate_remaining_final_bundle_artifacts_block_when_missing(self):
        cases = (
            (
                "validate-final-bundle-manifest",
                "manifest.json",
                "manifest_present",
                "final_acceptance_bundle_manifest_missing",
            ),
            (
                "validate-s2plt04-completion-report",
                "s2plt04_completion_report.json",
                "report_present",
                "s2plt04_completion_report_missing",
            ),
            (
                "validate-no-production-attestation",
                "no_production_side_effects.json",
                "attestation_present",
                "no_production_side_effect_attestation_missing",
            ),
            (
                "validate-next-agent-handoff",
                "next_agent_handoff.json",
                "handoff_present",
                "next_agent_handoff_missing",
            ),
        )

        with tempfile.TemporaryDirectory() as tmp:
            for command, filename, present_key, expected_error in cases:
                path = Path(tmp) / filename
                buffer = io.StringIO()
                with redirect_stdout(buffer):
                    result = main([command, "--path", str(path), "--json"])
                payload = json.loads(buffer.getvalue())

                self.assertEqual(result, 2, command)
                self.assertEqual(payload["status"], "blocked", command)
                self.assertFalse(payload[present_key], command)
                self.assertIn(expected_error, payload["validation_errors"], command)
                self.assertFalse(payload["production_acceptance_claimed"], command)
                self.assertFalse(payload["integrated_production_accepted"], command)
                self.assertFalse(payload["real_smtp_send_enabled"], command)
                self.assertFalse(payload["scheduler_install_enabled"], command)

    def test_audit_s2plt02_terminal_readiness_json_exposes_current_partial_state(self):
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            result = main(["audit-s2plt02-terminal-readiness", "--json"])
        payload = json.loads(buffer.getvalue())

        self.assertEqual(result, 2)
        self.assertEqual(payload["status"], "blocked")
        self.assertEqual(payload["scope"], "s2plt02_terminal_readiness_audit_only_no_acceptance_claim")
        self.assertFalse(payload["s2plt02_accepted"])
        self.assertFalse(payload["production_acceptance_claimed"])
        self.assertFalse(payload["integrated_production_accepted"])
        self.assertFalse(payload["daily_operation_enabled"])
        self.assertEqual(payload["observed_natural_days"], 1)
        self.assertEqual(payload["observed_email_count"], 4)
        self.assertTrue(payload["m4_watermark_correct"])
        self.assertEqual(
            payload["m4_watermark_proof_ref"],
            "governance/run_manifests/ADP-S2PLT02-M4-WATERMARK-PROOF-RECORD-20260628.json",
        )
        self.assertIn("two_consecutive_real_days_not_proven", payload["blocking_reasons"])
        self.assertIn("eight_real_emails_not_proven", payload["blocking_reasons"])
        self.assertIn("real_scheduler_not_proven", payload["blocking_reasons"])
        self.assertNotIn("inherited_v7_1_p0_findings_open", payload["blocking_reasons"])
        self.assertNotIn("inherited_v7_1_p1_findings_open", payload["blocking_reasons"])
        self.assertNotIn("m4_watermark_not_proven", payload["blocking_reasons"])
        self.assertTrue(payload["terminal_dependency_state"]["P0_ZERO"])
        self.assertTrue(payload["terminal_dependency_state"]["P1_ZERO"])

    def test_audit_s2plt02_dry_run_second_day_json_blocks_terminal_credit(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            state_dir = Path(tmp_dir)
            run_dir = state_dir / "runs" / "20260629"
            run_dir.mkdir(parents=True)
            products = ["M1", "M2", "M3", "M4"]
            for product in products:
                (run_dir / f"adp-smtp-delivery-report-{product}.json").write_text(
                    json.dumps(
                        {
                            "status": "dry_run",
                            "product_id": product,
                            "cycle_id": "2026-06-29",
                            "generated_at": "2026-06-28T19:00:02Z",
                            "dry_run": True,
                            "allow_send": False,
                            "real_send_attempted": False,
                            "real_smtp_send_enabled": False,
                        }
                    ),
                    encoding="utf-8",
                )
            (run_dir / "adp-local-runner-report.json").write_text(
                json.dumps(
                    {
                        "status": "pass",
                        "date": "2026-06-29",
                        "generated_at": "2026-06-28T19:00:02Z",
                        "production_evidence_ready": False,
                        "real_smtp_sent": False,
                        "mail_delivery_summary": {
                            "planned_send_total": 4,
                            "planned_mail_products": products,
                            "sent_mail_count": 0,
                            "sent_mail_products": [],
                            "dry_run_mail_products": products,
                            "status_by_product": {product: "dry_run" for product in products},
                        },
                    }
                ),
                encoding="utf-8",
            )
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                result = main(
                    [
                        "audit-s2plt02-dry-run-second-day",
                        "--state-dir",
                        str(state_dir),
                        "--service-date",
                        "2026-06-29",
                        "--json",
                    ]
                )
        payload = json.loads(buffer.getvalue())

        self.assertEqual(result, 2)
        self.assertEqual(payload["status"], "blocked")
        self.assertEqual(payload["service_date"], "2026-06-29")
        self.assertEqual(payload["dry_run_mail_count"], 4)
        self.assertEqual(payload["real_sent_mail_count"], 0)
        self.assertFalse(payload["counts_toward_s2plt02_terminal_proof"])
        self.assertFalse(payload["terminal_delivery_credit"])
        self.assertFalse(payload["real_smtp_proven"])
        self.assertFalse(payload["real_scheduler_proven"])
        self.assertFalse(payload["s2plt02_accepted"])
        self.assertIn("dry_run_evidence_only_not_real_smtp", payload["blocking_reasons"])
        self.assertIn("two_consecutive_real_days_not_proven", payload["blocking_reasons"])
        self.assertIn("eight_real_emails_not_proven", payload["blocking_reasons"])

    def test_audit_s2plt02_real_proof_capture_readiness_json_blocks_without_authorization_or_scheduler(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_root = Path(tmp_dir)
            state_dir = tmp_root / "state"
            run_dir = state_dir / "runs" / "20260629"
            run_dir.mkdir(parents=True)
            products = ["M1", "M2", "M3", "M4"]
            for product in products:
                (run_dir / f"adp-smtp-delivery-report-{product}.json").write_text(
                    json.dumps(
                        {
                            "status": "dry_run",
                            "product_id": product,
                            "dry_run": True,
                            "allow_send": False,
                            "real_send_attempted": False,
                            "real_smtp_send_enabled": False,
                        }
                    ),
                    encoding="utf-8",
                )
            (run_dir / "adp-local-runner-report.json").write_text(
                json.dumps(
                    {
                        "status": "pass",
                        "production_evidence_ready": False,
                        "real_smtp_sent": False,
                        "mail_delivery_summary": {
                            "planned_send_total": 4,
                            "planned_mail_products": products,
                            "dry_run_mail_products": products,
                            "sent_mail_products": [],
                            "sent_mail_count": 0,
                            "status_by_product": {product: "dry_run" for product in products},
                        },
                    }
                ),
                encoding="utf-8",
            )
            launchctl_file = tmp_root / "launchctl-disabled.txt"
            launchctl_file.write_text(
                "\n".join(
                    [
                        '"com.linze.adp.local.daily" => disabled',
                        '"com.linze.adp.local.health" => disabled',
                        '"com.linze.adp.local.watchdog" => disabled',
                    ]
                ),
                encoding="utf-8",
            )
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                result = main(
                    [
                        "audit-s2plt02-real-proof-capture-readiness",
                        "--repo-root",
                        str(tmp_root),
                        "--state-dir",
                        str(state_dir),
                        "--service-date",
                        "2026-06-29",
                        "--launchctl-disabled-file",
                        str(launchctl_file),
                        "--json",
                    ]
                )
        payload = json.loads(buffer.getvalue())

        self.assertEqual(result, 2)
        self.assertEqual(payload["status"], "blocked")
        self.assertFalse(payload["safe_to_collect_terminal_proof"])
        self.assertFalse(payload["real_proof_capture_authorized"])
        self.assertTrue(payload["all_required_launchagents_disabled"])
        self.assertIn("real_proof_capture_authorization_missing", payload["blocking_reasons"])
        self.assertIn("required_launchagents_disabled", payload["blocking_reasons"])
        self.assertIn("dry_run_second_day_not_terminal", payload["blocking_reasons"])

    def test_validate_s2plt02_real_proof_capture_authorization_blocks_missing_artifact(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "s2plt02_real_proof_capture_authorization.json"
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                result = main(
                    [
                        "validate-s2plt02-real-proof-capture-authorization",
                        "--path",
                        str(path),
                        "--json",
                    ]
                )
        payload = json.loads(buffer.getvalue())

        self.assertEqual(result, 2)
        self.assertEqual(payload["status"], "blocked")
        self.assertFalse(payload["authorization_present"])
        self.assertFalse(payload["real_proof_capture_authorized_by_payload"])
        self.assertIn("s2plt02_real_proof_capture_authorization_missing", payload["validation_errors"])
        self.assertFalse(payload["real_smtp_send_enabled"])
        self.assertFalse(payload["scheduler_install_enabled"])
        self.assertFalse(payload["production_acceptance_claimed"])
        self.assertFalse(payload["integrated_production_accepted"])

    def test_build_s2plt02_real_proof_capture_authorization_owner_packet_json_command(self):
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            result = main(
                [
                    "build-s2plt02-real-proof-capture-authorization-owner-packet",
                    "--readiness-state-hash",
                    "readiness-hash-001",
                    "--json",
                ]
            )
        payload = json.loads(buffer.getvalue())

        self.assertEqual(result, 0)
        self.assertEqual(payload["status"], "blocked_owner_action_packet_ready_no_authorization")
        self.assertEqual(payload["task_id"], "S2PLT02-REAL-PROOF-CAPTURE-AUTHORIZATION")
        self.assertEqual(
            payload["artifact_path"],
            "FINAL_ACCEPTANCE_BUNDLE/s2plt02_real_proof_capture_authorization.json",
        )
        self.assertEqual(payload["readiness_state_hash"], "readiness-hash-001")
        self.assertFalse(payload["authorization_artifact_present"])
        self.assertFalse(payload["real_proof_capture_authorized"])
        self.assertFalse(payload["real_smtp_send_enabled_by_this_packet"])
        self.assertFalse(payload["scheduler_install_enabled_by_this_packet"])
        self.assertFalse(payload["production_acceptance_claimed"])
        self.assertFalse(payload["integrated_production_accepted"])
        self.assertIn("s2plt02_real_proof_capture_authorization_missing", payload["blocking_reasons"])
        self.assertIn(
            "write_authorization_artifact_only_if_owner_explicitly_approves_real_smtp_scheduler_capture",
            payload["required_owner_actions"],
        )
        self.assertEqual(payload["owner_packet_validation_errors"], [])

    def test_validate_s2plt02_terminal_delivery_proof_json_blocks_missing_artifact(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                result = main(["validate-s2plt02-terminal-delivery-proof", "--repo-root", tmp_dir, "--json"])
        payload = json.loads(buffer.getvalue())

        self.assertEqual(result, 2)
        self.assertEqual(payload["status"], "blocked")
        self.assertFalse(payload["artifact_present"])
        self.assertFalse(payload["s2plt02_accepted_by_artifact"])
        self.assertFalse(payload["terminal_delivery_proof_ready"])
        self.assertIn("s2plt02_terminal_delivery_proof_artifact_missing", payload["validation_errors"])
        self.assertIn("two_consecutive_real_days_not_proven", payload["blocking_reasons"])
        self.assertIn("eight_real_emails_not_proven", payload["blocking_reasons"])
        self.assertIn("real_scheduler_not_proven", payload["blocking_reasons"])
        self.assertFalse(payload["production_acceptance_claimed"])
        self.assertFalse(payload["integrated_production_accepted"])
        self.assertFalse(payload["daily_operation_enabled"])

    def test_audit_s2plt03_resilience_readiness_json_command_consumes_zero_proof_but_blocks(self):
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            result = main(["audit-s2plt03-resilience-readiness", "--json"])
        payload = json.loads(buffer.getvalue())

        self.assertEqual(result, 2)
        self.assertEqual(payload["status"], "blocked")
        self.assertEqual(payload["p0_p1_zero_proof_artifact_validation"]["status"], "pass")
        self.assertTrue(payload["gates"]["p0_zero"])
        self.assertTrue(payload["gates"]["p1_zero"])
        self.assertIn("s2plt02_not_accepted", payload["blocking_reasons"])
        self.assertNotIn("inherited_v7_1_p0_findings_open", payload["blocking_reasons"])
        self.assertNotIn("inherited_v7_1_p1_findings_open", payload["blocking_reasons"])
        self.assertFalse(payload["s2plt03_accepted"])
        self.assertFalse(payload["s2plt03_resilience_drill_completed"])
        self.assertFalse(payload["integrated_production_accepted"])
        self.assertFalse(payload["scheduler_install_enabled"])

    def test_plan_final_bundle_prerequisites_json_command_blocks_without_artifacts(self):
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            result = main(["plan-final-bundle-prerequisites", "--json"])
        payload = json.loads(buffer.getvalue())

        self.assertEqual(result, 2)
        self.assertEqual(payload["status"], "blocked")
        self.assertEqual(payload["scope"], "final_bundle_prerequisite_plan_only_no_production_acceptance")
        self.assertEqual(payload["next_required_step"], "S2PLT04_COMPLETION_REPORT")
        self.assertFalse(payload["all_required_steps_passed"])
        self.assertFalse(payload["ready_for_final_bundle_manifest"])
        step_status = {step["step_id"]: step["status"] for step in payload["ordered_steps"]}
        self.assertEqual(step_status["INDEPENDENT_FINAL_REVIEWER_ASSIGNMENT_VALIDATION"], "pass")
        self.assertEqual(step_status["P0_P1_ZERO_PROOF_ARTIFACT"], "pass")
        self.assertEqual(step_status["NO_PRODUCTION_SIDE_EFFECT_ATTESTATION"], "pass")
        self.assertNotIn("independent_final_reviewer_assignment_missing", payload["blocking_reasons"])
        self.assertNotIn("p0_p1_zero_proof_artifact_missing", payload["blocking_reasons"])
        self.assertIn("s2plt04_completion_report_missing", payload["blocking_reasons"])
        self.assertNotIn("no_production_side_effect_attestation_missing", payload["blocking_reasons"])
        self.assertFalse(payload["production_acceptance_claimed"])
        self.assertFalse(payload["integrated_production_accepted"])
        self.assertFalse(payload["daily_operation_enabled"])
        self.assertFalse(payload["real_smtp_send_enabled"])

    def test_audit_s2plt04_completion_evidence_json_command_exposes_terminal_gaps(self):
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            result = main(["audit-s2plt04-completion-evidence", "--json"])
        payload = json.loads(buffer.getvalue())

        self.assertEqual(result, 2)
        self.assertEqual(payload["status"], "blocked")
        self.assertEqual(payload["scope"], "s2plt04_completion_evidence_audit_only_no_report_creation")
        self.assertFalse(payload["completion_report_ready"])
        self.assertFalse(payload["s2plt04_completion_report_written"])
        self.assertEqual(payload["next_required_artifact"], "FINAL_ACCEPTANCE_BUNDLE/s2plt04_completion_report.json")
        self.assertEqual(
            payload["source_evidence"]["S2PLT01_REPLAY_REVIEW"]["artifact_ref"],
            "FINAL_ACCEPTANCE_BUNDLE/s2plt01_terminal_acceptance.json",
        )
        self.assertEqual(
            payload["source_evidence"]["S2PLT01_REPLAY_REVIEW"]["nonterminal_ref"],
            "governance/run_manifests/ADP-S2PLT01-INDEPENDENT-REPLAY-REVIEW-20260626.json",
        )
        self.assertEqual(payload["source_evidence"]["S2PLT01_REPLAY_REVIEW"]["artifact_status"], "pass")
        self.assertTrue(payload["source_evidence"]["S2PLT01_REPLAY_REVIEW"]["terminal_dependency_value"])
        self.assertEqual(payload["source_evidence"]["S2PLT02_LIVE_2D_PROOF"]["artifact_status"], "missing_terminal")
        s2plt02_evidence = payload["source_evidence"]["S2PLT02_LIVE_2D_PROOF"]
        self.assertIn(
            "governance/run_manifests/ADP-S2PLT02-ZERO-PROOF-READINESS-SYNC-20260629.json",
            s2plt02_evidence["nonterminal_refs"],
        )
        self.assertEqual(s2plt02_evidence["observed_natural_days"], 1)
        self.assertEqual(s2plt02_evidence["required_natural_days"], 2)
        self.assertEqual(s2plt02_evidence["observed_email_count"], 4)
        self.assertEqual(s2plt02_evidence["required_email_count"], 8)
        self.assertTrue(s2plt02_evidence["m4_watermark_correct"])
        self.assertEqual(
            s2plt02_evidence["m4_watermark_proof_ref"],
            "governance/run_manifests/ADP-S2PLT02-M4-WATERMARK-PROOF-RECORD-20260628.json",
        )
        self.assertIn("two_consecutive_real_days_not_proven", s2plt02_evidence["remaining_terminal_blockers"])
        self.assertIn("eight_real_emails_not_proven", s2plt02_evidence["remaining_terminal_blockers"])
        self.assertIn("real_scheduler_not_proven", s2plt02_evidence["remaining_terminal_blockers"])
        self.assertNotIn("inherited_v7_1_p0_findings_open", s2plt02_evidence["remaining_terminal_blockers"])
        self.assertNotIn("inherited_v7_1_p1_findings_open", s2plt02_evidence["remaining_terminal_blockers"])
        self.assertNotIn("m4_watermark_not_proven", s2plt02_evidence["remaining_terminal_blockers"])
        self.assertEqual(payload["source_evidence"]["S2PLT03_RESILIENCE_PROOF"]["artifact_status"], "missing_terminal")
        self.assertIn(
            "governance/run_manifests/ADP-S2PLT03-ZERO-PROOF-RESILIENCE-SYNC-20260629.json",
            payload["source_evidence"]["S2PLT03_RESILIENCE_PROOF"]["nonterminal_refs"],
        )
        self.assertEqual(payload["source_evidence"]["P0_P1_ZERO_PROOF"]["artifact_status"], "pass")
        self.assertTrue(payload["terminal_dependency_state"]["S2PLT01_ACCEPTED"])
        self.assertFalse(payload["terminal_dependency_state"]["S2PLT02_ACCEPTED"])
        self.assertFalse(payload["terminal_dependency_state"]["S2PLT03_ACCEPTED"])
        self.assertTrue(payload["terminal_dependency_state"]["P0_ZERO_PROVEN"])
        self.assertTrue(payload["terminal_dependency_state"]["P1_ZERO_PROVEN"])
        self.assertNotIn("s2plt01_not_accepted", payload["blocking_reasons"])
        self.assertIn("s2plt02_live_2d_terminal_proof_missing", payload["blocking_reasons"])
        self.assertIn("s2plt03_resilience_terminal_proof_missing", payload["blocking_reasons"])
        self.assertFalse(payload["production_acceptance_claimed"])
        self.assertFalse(payload["integrated_production_accepted"])
        self.assertFalse(payload["real_smtp_send_enabled"])
        self.assertFalse(payload["scheduler_install_enabled"])

    def test_module_entrypoint_executes_final_bundle_plan_command(self):
        repo_root = Path(__file__).resolve().parents[2]
        env = os.environ.copy()
        src_path = str(repo_root / "arxiv-daily-push" / "src")
        env["PYTHONPATH"] = (
            src_path
            if not env.get("PYTHONPATH")
            else f"{src_path}{os.pathsep}{env['PYTHONPATH']}"
        )
        completed = subprocess.run(
            [
                sys.executable,
                "-B",
                "-m",
                "arxiv_daily_push.cli",
                "plan-final-bundle-prerequisites",
                "--json",
            ],
            cwd=repo_root,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(completed.returncode, 2, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["status"], "blocked")
        self.assertEqual(payload["next_required_step"], "S2PLT04_COMPLETION_REPORT")
        self.assertFalse(payload["integrated_production_accepted"])
        self.assertFalse(payload["real_smtp_send_enabled"])
        self.assertFalse(payload["scheduler_install_enabled"])
        self.assertEqual(payload["plan_validation_errors"], [])

    def test_validate_p0_p1_zero_proof_passes_valid_artifact_without_production_claim(self):
        zero_proof = {
            "schema_version": S2PMT07_P0_P1_ZERO_PROOF_SCHEMA_VERSION,
            "contract_id": "ADP-PRODUCT-CONTRACT-V7.2",
            "generated_at": "2026-06-28T22:35:00+10:00",
            "reviewer_independence": {
                "status": "verified",
                "required_independence": S2PMT07_REQUIRED_REVIEWER_INDEPENDENCE,
            },
            "source_candidate_refs": build_p0_p1_zero_proof_readiness_state()["candidate_evidence_refs"],
            "finding_counts": {"P0": 0, "P1": 0},
            "zero_severity_counts": {"P0": 0, "P1": 0},
            "independent_closure_decision": {
                "decision": S2PMT07_P0_P1_ZERO_PROOF_CLOSURE_DECISION,
                "p0_zero_proven": True,
                "p1_zero_proven": True,
                "production_acceptance_claimed": False,
            },
            "final_bundle_refs": list(S2PMT07_FINAL_ACCEPTANCE_BUNDLE_REQUIRED_ITEMS),
            "no_production_side_effects": {
                flag: False for flag in S2PMT07_P0_P1_ZERO_PROOF_NO_PRODUCTION_FLAGS
            },
            "decision_hash": "",
        }
        zero_proof["decision_hash"] = build_p0_p1_zero_proof_decision_hash(zero_proof)

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "p0_p1_zero_proof.json"
            path.write_text(json.dumps(zero_proof), encoding="utf-8")
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                result = main(["validate-p0-p1-zero-proof", "--path", str(path), "--json"])
        self.assertEqual(result, 0)
        payload = json.loads(buffer.getvalue())
        self.assertEqual(payload["status"], "pass")
        self.assertTrue(payload["artifact_present"])
        self.assertTrue(payload["p0_zero_proven_by_payload"])
        self.assertTrue(payload["p1_zero_proven_by_payload"])
        self.assertFalse(payload["production_acceptance_claimed"])
        self.assertFalse(payload["integrated_production_accepted"])
        self.assertFalse(payload["daily_operation_enabled"])

    def test_validate_final_command_execution_passes_valid_artifact_without_production_claim(self):
        command_execution = {
            "schema_version": S2PMT07_FINAL_COMMAND_EXECUTION_SCHEMA_VERSION,
            "contract_id": "ADP-PRODUCT-CONTRACT-V7.2",
            "generated_at": "2026-06-28T23:50:00+10:00",
            "execution_decision": S2PMT07_FINAL_COMMAND_EXECUTION_DECISION,
            "executor_independence": {
                "status": "verified",
                "required_independence": S2PMT07_REQUIRED_REVIEWER_INDEPENDENCE,
                "executor_role": "independent_final_reviewer",
            },
            "required_commands_executed": list(S2PMT07_REQUIRED_TEST_COMMANDS),
            "command_results": {
                command: {
                    "status": "pass",
                    "exit_code": 0,
                    "executed_by": "independent_final_reviewer",
                    "evidence_ref": f"FINAL_ACCEPTANCE_BUNDLE/command_evidence/{index}.txt",
                }
                for index, command in enumerate(S2PMT07_REQUIRED_TEST_COMMANDS, start=1)
            },
            "final_bundle_refs": list(S2PMT07_FINAL_ACCEPTANCE_BUNDLE_REQUIRED_ITEMS),
            "no_production_side_effects": {
                flag: False for flag in S2PMT07_FINAL_COMMAND_EXECUTION_NO_PRODUCTION_FLAGS
            },
            "execution_hash": "",
        }
        command_execution["execution_hash"] = build_final_command_execution_hash(command_execution)

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "final_command_execution.json"
            path.write_text(json.dumps(command_execution), encoding="utf-8")
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                result = main(["validate-final-command-execution", "--path", str(path), "--json"])
        self.assertEqual(result, 0)
        payload = json.loads(buffer.getvalue())
        self.assertEqual(payload["status"], "pass")
        self.assertTrue(payload["command_execution_present"])
        self.assertTrue(payload["all_required_commands_passed"])
        self.assertTrue(payload["final_commands_executed_by_payload"])
        self.assertFalse(payload["production_acceptance_claimed"])
        self.assertFalse(payload["integrated_production_accepted"])
        self.assertFalse(payload["daily_operation_enabled"])

    def test_build_final_reviewer_assignment_owner_packet_json_command(self):
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            result = main(["build-final-reviewer-assignment-owner-packet", "--json"])
        self.assertEqual(result, 0)
        payload = json.loads(buffer.getvalue())
        self.assertEqual(payload["status"], "blocked_owner_action_packet_ready_no_assignment")
        self.assertEqual(payload["task_id"], "S2PMT07")
        self.assertEqual(payload["assignment_artifact_path"], "FINAL_ACCEPTANCE_BUNDLE/independent_final_reviewer_assignment.json")
        self.assertFalse(payload["assignment_artifact_present"])
        self.assertFalse(payload["independent_final_reviewer_assigned"])
        self.assertFalse(payload["assignment_satisfies_gate"])
        self.assertFalse(payload["p0_zero_proven"])
        self.assertFalse(payload["p1_zero_proven"])
        self.assertEqual(payload["observed_open_p0_findings"], 8)
        self.assertEqual(payload["observed_open_p1_findings"], 37)
        self.assertFalse(payload["production_acceptance_claimed"])
        self.assertFalse(payload["integrated_production_accepted"])
        self.assertFalse(payload["daily_operation_enabled"])
        self.assertEqual(payload["owner_packet_validation_errors"], [])

    def test_build_final_reviewer_assignment_artifact_draft_json_command(self):
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            result = main(
                [
                    "build-final-reviewer-assignment-artifact-draft",
                    "--reviewer-id",
                    "independent-final-reviewer-001",
                    "--assigned-by",
                    "owner_or_coordinator",
                    "--generated-at",
                    "2026-06-29T00:40:23+10:00",
                    "--json",
                ]
            )

        self.assertEqual(result, 0)
        payload = json.loads(buffer.getvalue())
        self.assertEqual(payload["status"], "draft")
        self.assertEqual(
            payload["scope"],
            "independent_final_reviewer_assignment_artifact_draft_only_no_assignment_no_production",
        )
        self.assertEqual(
            payload["artifact_path"],
            "FINAL_ACCEPTANCE_BUNDLE/independent_final_reviewer_assignment.json",
        )
        self.assertFalse(payload["assignment_artifact_written"])
        self.assertFalse(payload["assignment_gate_satisfied_by_this_command"])
        self.assertFalse(payload["production_acceptance_claimed"])
        self.assertFalse(payload["integrated_production_accepted"])
        self.assertFalse(payload["daily_operation_enabled"])
        self.assertFalse(payload["real_smtp_send_enabled"])
        self.assertFalse(payload["scheduler_install_enabled"])
        self.assertEqual(payload["validation_errors"], [])

        artifact = payload["artifact"]
        self.assertEqual(list(artifact.keys()), list(S2PMT07_INDEPENDENT_FINAL_REVIEWER_ASSIGNMENT_REQUIRED_FIELDS))
        self.assertEqual(
            artifact["schema_version"],
            S2PMT07_INDEPENDENT_FINAL_REVIEWER_ASSIGNMENT_SCHEMA_VERSION,
        )
        self.assertEqual(
            artifact["assignment_decision"],
            S2PMT07_INDEPENDENT_FINAL_REVIEWER_ASSIGNMENT_DECISION,
        )
        self.assertEqual(artifact["generated_at"], "2026-06-29T00:40:23+10:00")
        self.assertEqual(artifact["reviewer_assignment"]["reviewer_id"], "independent-final-reviewer-001")
        self.assertEqual(artifact["reviewer_assignment"]["reviewer_role"], "independent_final_reviewer")
        self.assertEqual(artifact["reviewer_assignment"]["assigned_by"], "owner_or_coordinator")
        self.assertEqual(
            artifact["reviewer_assignment"]["assignment_scope"],
            "S2PMT07_P0_P1_FINAL_CLOSURE_REVIEW",
        )
        self.assertEqual(artifact["reviewer_independence"]["status"], "verified")
        self.assertEqual(
            artifact["reviewer_independence"]["required_independence"],
            S2PMT07_REQUIRED_REVIEWER_INDEPENDENCE,
        )
        self.assertFalse(artifact["reviewer_independence"]["reviewer_involved_in_s2pmt01_t06"])
        self.assertEqual(
            artifact["review_input_refs"],
            build_independent_final_reviewer_assignment_request_state()["review_input_refs"],
        )
        self.assertEqual(
            artifact["no_production_side_effects"],
            {flag: False for flag in S2PMT07_INDEPENDENT_FINAL_REVIEWER_ASSIGNMENT_NO_PRODUCTION_FLAGS},
        )
        self.assertEqual(
            artifact["assignment_hash"],
            build_independent_final_reviewer_assignment_hash(artifact),
        )

    def test_build_final_closure_decision_owner_packet_json_command(self):
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            try:
                result = main(["build-final-closure-decision-owner-packet", "--json"])
            except SystemExit as exc:
                self.fail(f"command should be registered without exiting argparse: {exc}")
        self.assertEqual(result, 0)
        payload = json.loads(buffer.getvalue())
        self.assertEqual(payload["status"], "blocked_owner_action_packet_ready_no_closure")
        self.assertEqual(payload["task_id"], "S2PMT07")
        self.assertEqual(
            payload["decision_artifact_ref"],
            "FINAL_ACCEPTANCE_BUNDLE/p0_p1_zero_proof.json#independent_closure_decision",
        )
        self.assertEqual(
            payload["assignment_artifact_path"],
            "FINAL_ACCEPTANCE_BUNDLE/independent_final_reviewer_assignment.json",
        )
        self.assertTrue(payload["assignment_owner_packet_ready"])
        self.assertTrue(payload["closure_decision_request_ready"])
        self.assertFalse(payload["assignment_artifact_present"])
        self.assertFalse(payload["independent_final_reviewer_assigned"])
        self.assertFalse(payload["independent_final_closure_decision_present"])
        self.assertFalse(payload["zero_proof_artifact_present"])
        self.assertFalse(payload["p0_zero_proven"])
        self.assertFalse(payload["p1_zero_proven"])
        self.assertFalse(payload["closure_claimed"])
        self.assertEqual(payload["observed_open_p0_findings"], 8)
        self.assertEqual(payload["observed_open_p1_findings"], 37)
        self.assertFalse(payload["production_acceptance_claimed"])
        self.assertFalse(payload["integrated_production_accepted"])
        self.assertFalse(payload["daily_operation_enabled"])
        self.assertEqual(payload["owner_packet_validation_errors"], [])

    def test_validate_final_acceptance_bundle_json_command_blocks_without_live_artifacts(self):
        repo_root = Path(__file__).resolve().parents[2]
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            result = main(
                [
                    "validate-final-acceptance-bundle",
                    "--repo-root",
                    str(repo_root),
                    "--json",
                ]
            )
        self.assertEqual(result, 2)
        payload = json.loads(buffer.getvalue())
        self.assertEqual(payload["status"], "blocked")
        self.assertEqual(payload["scope"], "final_acceptance_bundle_readiness_precheck_only")
        self.assertIn("FINAL_ACCEPTANCE_BUNDLE/manifest.json", payload["missing_items"])
        self.assertNotIn("FINAL_ACCEPTANCE_BUNDLE/no_production_side_effects.json", payload["missing_items"])
        self.assertNotIn("FINAL_ACCEPTANCE_BUNDLE/p0_p1_zero_proof.json", payload["missing_items"])
        self.assertTrue(payload["available_items"]["FINAL_ACCEPTANCE_BUNDLE/no_production_side_effects.json"])
        self.assertTrue(payload["available_items"]["FINAL_ACCEPTANCE_BUNDLE/p0_p1_zero_proof.json"])
        self.assertNotIn("independent_final_reviewer_assignment_missing", payload["blocking_reasons"])
        self.assertNotIn("p0_p1_zero_proof_missing", payload["blocking_reasons"])
        self.assertIn("s2plt04_completion_evidence_missing", payload["blocking_reasons"])
        self.assertFalse(payload["production_acceptance_claimed"])
        self.assertFalse(payload["integrated_production_accepted"])
        self.assertFalse(payload["daily_operation_enabled"])
        self.assertEqual(payload["readiness_validation_errors"], [])

    def test_validate_final_reviewer_assignment_passes_valid_artifact_without_production_claim(self):
        assignment = {
            "schema_version": S2PMT07_INDEPENDENT_FINAL_REVIEWER_ASSIGNMENT_SCHEMA_VERSION,
            "contract_id": "ADP-PRODUCT-CONTRACT-V7.2",
            "generated_at": "2026-06-28T21:20:00+10:00",
            "assignment_decision": S2PMT07_INDEPENDENT_FINAL_REVIEWER_ASSIGNMENT_DECISION,
            "reviewer_assignment": {
                "reviewer_id": "independent-final-reviewer-001",
                "reviewer_role": "independent_final_reviewer",
                "assigned_by": "owner_or_coordinator",
                "assignment_scope": "S2PMT07_P0_P1_FINAL_CLOSURE_REVIEW",
            },
            "reviewer_independence": {
                "status": "verified",
                "required_independence": S2PMT07_REQUIRED_REVIEWER_INDEPENDENCE,
                "reviewer_involved_in_s2pmt01_t06": False,
            },
            "review_input_refs": build_independent_final_reviewer_assignment_request_state()[
                "review_input_refs"
            ],
            "no_production_side_effects": {
                flag: False
                for flag in S2PMT07_INDEPENDENT_FINAL_REVIEWER_ASSIGNMENT_NO_PRODUCTION_FLAGS
            },
            "assignment_hash": "",
        }
        assignment["assignment_hash"] = build_independent_final_reviewer_assignment_hash(assignment)

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "independent_final_reviewer_assignment.json"
            path.write_text(json.dumps(assignment), encoding="utf-8")
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                result = main(["validate-final-reviewer-assignment", "--path", str(path), "--json"])
        self.assertEqual(result, 0)
        payload = json.loads(buffer.getvalue())
        self.assertEqual(payload["status"], "pass")
        self.assertTrue(payload["assignment_present"])
        self.assertTrue(payload["independent_final_reviewer_assigned_by_payload"])
        self.assertFalse(payload["production_acceptance_claimed"])
        self.assertFalse(payload["integrated_production_accepted"])
        self.assertFalse(payload["daily_operation_enabled"])


if __name__ == "__main__":
    unittest.main()
