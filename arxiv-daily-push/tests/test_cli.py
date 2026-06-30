import io
import json
import os
import shlex
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
        self.assertEqual(payload["observed_natural_days"], 2)
        self.assertEqual(payload["observed_email_count"], 8)
        self.assertTrue(payload["m4_watermark_correct"])
        self.assertEqual(
            payload["m4_watermark_proof_ref"],
            "governance/run_manifests/ADP-S2PLT02-M4-WATERMARK-PROOF-RECORD-20260628.json",
        )
        self.assertNotIn("two_consecutive_real_days_not_proven", payload["blocking_reasons"])
        self.assertNotIn("eight_real_emails_not_proven", payload["blocking_reasons"])
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
            (run_dir / "adp-daily-run.json").write_text(
                json.dumps(
                    {
                        "status": "succeeded",
                        "run_record": {
                            "date": "2026-06-29",
                            "current_state": "completed",
                            "status": "SUCCESS",
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
        self.assertTrue(payload["daily_run_report_present"])
        self.assertEqual(payload["daily_run_status"], "succeeded")
        self.assertTrue(payload["daily_run_succeeded"])
        self.assertTrue(payload["daily_run_succeeded_but_smtp_dry_run_not_terminal"])
        self.assertFalse(payload["daily_run_counts_toward_terminal_proof"])
        self.assertFalse(payload["counts_toward_s2plt02_terminal_proof"])
        self.assertFalse(payload["terminal_delivery_credit"])
        self.assertFalse(payload["real_smtp_proven"])
        self.assertFalse(payload["real_scheduler_proven"])
        self.assertFalse(payload["s2plt02_accepted"])
        self.assertIn("dry_run_evidence_only_not_real_smtp", payload["blocking_reasons"])
        self.assertIn("daily_run_succeeded_but_smtp_dry_run_not_terminal", payload["blocking_reasons"])
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

    def test_audit_s2plt02_terminal_capture_window_json_blocks_dry_runs_and_disabled_scheduler(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_root = Path(tmp_dir)
            state_dir = tmp_root / "state"
            products = ["M1", "M2", "M3", "M4"]
            for service_date in ("2026-06-29", "2026-06-30"):
                run_dir = state_dir / "runs" / service_date.replace("-", "")
                run_dir.mkdir(parents=True)
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
                            "date": service_date,
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
                (run_dir / "adp-daily-run.json").write_text(
                    json.dumps(
                        {
                            "status": "succeeded",
                            "run_record": {
                                "date": service_date,
                                "current_state": "completed",
                                "status": "SUCCESS",
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
            launchctl_print_files = []
            for label in (
                "com.linze.adp.local.daily",
                "com.linze.adp.local.health",
                "com.linze.adp.local.watchdog",
            ):
                launchctl_print_file = tmp_root / f"{label}.print.txt"
                launchctl_print_file.write_text(
                    """
                    type = LaunchAgent
                    state = not running
                    event triggers = {
                        com.linze.adp.local.daily.268435486 => {
                            stream = com.apple.launchd.calendarinterval
                        }
                    }
                    """,
                    encoding="utf-8",
                )
                launchctl_print_files.extend(["--launchctl-print-file", f"{label}={launchctl_print_file}"])
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                result = main(
                    [
                        "audit-s2plt02-terminal-capture-window",
                        "--repo-root",
                        str(tmp_root),
                        "--state-dir",
                        str(state_dir),
                        "--candidate-service-dates",
                        "2026-06-29,2026-06-30",
                        "--launchctl-disabled-file",
                        str(launchctl_file),
                        *launchctl_print_files,
                        "--json",
                    ]
                )
        payload = json.loads(buffer.getvalue())

        self.assertEqual(result, 2)
        self.assertEqual(payload["task_id"], "S2PLT02-TERMINAL-CAPTURE-WINDOW-AUDIT")
        self.assertEqual(payload["status"], "blocked")
        self.assertFalse(payload["terminal_delivery_credit"])
        self.assertFalse(payload["counts_toward_s2plt02_terminal_proof"])
        self.assertTrue(payload["real_smtp_proven_for_terminal_pair"])
        self.assertFalse(payload["real_scheduler_proven"])
        self.assertTrue(payload["all_required_launchagents_disabled"])
        self.assertTrue(payload["all_required_launchagents_loaded"])
        self.assertTrue(payload["all_required_launchagents_not_running"])
        self.assertTrue(payload["all_required_launchagents_have_calendar_triggers"])
        self.assertTrue(payload["launchagents_loaded_but_disabled"])
        self.assertEqual(payload["daily_run_succeeded_service_dates"], ["2026-06-29", "2026-06-30"])
        self.assertEqual(payload["nonterminal_succeeded_dry_run_service_dates"], ["2026-06-29", "2026-06-30"])
        self.assertEqual(payload["nonterminal_succeeded_dry_run_count"], 2)
        self.assertEqual(
            payload["scheduler_runtime_evidence_status"],
            "launchagents_loaded_but_disabled_not_terminal_scheduler_proof",
        )
        self.assertEqual(payload["observed_terminal_email_count_credit"], 8)
        self.assertEqual(payload["required_email_count"], 8)
        self.assertIn("adp_launchagents_disabled_by_user_domain_override", payload["blocking_reasons"])
        self.assertNotIn("second_consecutive_real_m1_m4_smtp_day_missing", payload["blocking_reasons"])
        self.assertIn("daily_run_succeeded_but_smtp_dry_run_not_terminal", payload["blocking_reasons"])

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

    def test_audit_s2plt02_real_proof_capture_readiness_cli_blocks_stale_authorization_hash(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_root = Path(tmp_dir)
            state_dir = tmp_root / "state"
            products = ["M1", "M2", "M3", "M4"]
            run_dir = state_dir / "runs" / "20260629"
            run_dir.mkdir(parents=True)
            for product in products:
                (run_dir / f"adp-smtp-delivery-report-{product}.json").write_text(
                    json.dumps(
                        {
                            "status": "dry_run",
                            "mail_product_id": product,
                            "service_date": "2026-06-29",
                            "real_smtp_sent": False,
                        }
                    ),
                    encoding="utf-8",
                )
            (run_dir / "adp-daily-run.json").write_text(
                json.dumps(
                    {
                        "status": "succeeded",
                        "service_date": "2026-06-29",
                        "mail_delivery_summary": {
                            "planned_send_total": 4,
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
            artifact_path = tmp_root / "FINAL_ACCEPTANCE_BUNDLE" / "s2plt02_real_proof_capture_authorization.json"
            artifact_path.parent.mkdir(parents=True)
            artifact = {
                "schema_version": "adp.s2plt02_real_proof_capture_authorization.v1",
                "contract_id": "ADP-PRODUCT-CONTRACT-V7.2",
                "generated_at": "2026-06-30T07:41:53+10:00",
                "authorization_decision": "S2PLT02_REAL_PROOF_CAPTURE_AUTHORIZED_NO_PRODUCTION_ACCEPTANCE",
                "authorized_by": {
                    "owner_id": "owner_or_coordinator",
                    "owner_role": "owner",
                    "authorization_source": "explicit_owner_instruction",
                },
                "authorization_scope": "S2PLT02_REAL_SMTP_SCHEDULER_PROOF_CAPTURE_ONLY",
                "authorized_actions": [
                    "capture_second_consecutive_real_m1_m4_smtp_day",
                    "capture_real_launchd_scheduler_proof",
                    "validate_s2plt02_terminal_delivery_proof_artifact",
                ],
                "authorization_constraints": {
                    "stage2_production_acceptance_not_granted": True,
                    "daily_operation_not_enabled": True,
                    "release_not_enabled": True,
                    "current_v7_unchanged": True,
                    "only_capture_second_day_and_scheduler_proof": True,
                },
                "readiness_state_hash": "old-readiness-hash",
                "evidence_refs": [
                    "arxiv-daily-push/docs/governance/ASSURANCE_STATUS.yaml",
                    "arxiv-daily-push/docs/phase_records/PHASE_S2PLT02_REAL_PROOF_CAPTURE_READINESS.md",
                    "governance/run_manifests/ADP-S2PLT02-REAL-PROOF-CAPTURE-READINESS-20260629.json",
                ],
                "no_production_side_effects": {
                    "production_acceptance_claimed": False,
                    "integrated_production_accepted": False,
                    "stage2_integrated_production_accepted": False,
                    "daily_operation_enabled": False,
                    "real_smtp_sent": False,
                    "real_smtp_send_enabled": False,
                    "scheduler_enabled": False,
                    "scheduler_install_enabled": False,
                    "release_uploaded": False,
                    "release_packaging_enabled": False,
                    "production_restore_enabled": False,
                    "production_restore_executed": False,
                    "public_schema_changed": False,
                    "db_migration_executed": False,
                    "production_queue_mutated": False,
                    "source_adapter_changed": False,
                    "ranking_algorithm_changed": False,
                    "current_pointer_changed": False,
                    "v7_1_baseline_changed": False,
                    "v7_2_contract_files_changed": False,
                },
                "authorization_hash": "",
            }
            artifact["authorization_hash"] = (
                "sha256:"
                "a85e6e2e0d0fb45ec9bfbb6a0c8f103675bf20a98a93f950989cd150b3438f27"
            )
            artifact_path.write_text(json.dumps(artifact, ensure_ascii=False), encoding="utf-8")
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
                        "--expected-authorization-readiness-state-hash",
                        "current-readiness-hash",
                        "--json",
                    ]
                )
        payload = json.loads(buffer.getvalue())

        self.assertEqual(result, 2)
        self.assertFalse(payload["real_proof_capture_authorized"])
        self.assertEqual(payload["authorization_artifact_status"], "blocked")
        self.assertIn(
            "readiness_state_hash does not match current readiness state",
            payload["authorization_validation_errors"],
        )
        self.assertIn("real_proof_capture_authorization_invalid", payload["blocking_reasons"])

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

    def test_build_s2plt02_real_proof_capture_authorization_artifact_draft_json_command(self):
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            result = main(
                [
                    "build-s2plt02-real-proof-capture-authorization-artifact-draft",
                    "--owner-id",
                    "owner",
                    "--owner-role",
                    "owner",
                    "--generated-at",
                    "2026-06-29T20:57:12+10:00",
                    "--readiness-state-hash",
                    "readiness-hash-001",
                    "--json",
                ]
            )
        payload = json.loads(buffer.getvalue())

        self.assertEqual(result, 0)
        self.assertEqual(payload["status"], "draft")
        self.assertEqual(
            payload["scope"],
            "s2plt02_real_proof_capture_authorization_artifact_draft_only_no_write_no_production",
        )
        self.assertEqual(
            payload["artifact_path"],
            "FINAL_ACCEPTANCE_BUNDLE/s2plt02_real_proof_capture_authorization.json",
        )
        self.assertFalse(payload["authorization_artifact_written"])
        self.assertFalse(payload["authorization_artifact_present_in_repo"])
        self.assertFalse(payload["real_proof_capture_authorized_by_this_command"])
        self.assertFalse(payload["real_smtp_send_enabled"])
        self.assertFalse(payload["scheduler_install_enabled"])
        self.assertFalse(payload["production_acceptance_claimed"])
        self.assertEqual(payload["validation_errors"], [])
        self.assertEqual(payload["artifact"]["readiness_state_hash"], "readiness-hash-001")
        self.assertEqual(payload["artifact"]["authorized_by"]["owner_id"], "owner")

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
        self.assertNotIn("two_consecutive_real_days_not_proven", payload["blocking_reasons"])
        self.assertNotIn("eight_real_emails_not_proven", payload["blocking_reasons"])
        self.assertIn("real_scheduler_not_proven", payload["blocking_reasons"])
        self.assertFalse(payload["production_acceptance_claimed"])
        self.assertFalse(payload["integrated_production_accepted"])
        self.assertFalse(payload["daily_operation_enabled"])

    def test_audit_s2plt02_terminal_delivery_inputs_json_lists_missing_inputs(self):
        repo_root = Path(__file__).resolve().parents[2]
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            result = main(
                [
                    "audit-s2plt02-terminal-delivery-inputs",
                    "--repo-root",
                    str(repo_root),
                    "--generated-at",
                    "2026-06-30T10:12:54+10:00",
                    "--json",
                ]
            )
        payload = json.loads(buffer.getvalue())

        self.assertEqual(result, 2)
        self.assertEqual(payload["status"], "blocked")
        self.assertEqual(payload["task_id"], "S2PLT02-TERMINAL-DELIVERY-INPUT-INVENTORY")
        self.assertFalse(payload["terminal_delivery_proof_ready"])
        self.assertFalse(payload["artifact_written"])
        self.assertIn("SECOND_REAL_DELIVERY_DAY", payload["ready_inputs"])
        self.assertIn("EIGHT_REAL_EMAILS", payload["ready_inputs"])
        self.assertNotIn("SECOND_REAL_DELIVERY_DAY", payload["missing_inputs"])
        self.assertNotIn("EIGHT_REAL_EMAILS", payload["missing_inputs"])
        self.assertIn("REAL_SCHEDULER_PROOF", payload["missing_inputs"])
        self.assertIn("S2PLT02_TERMINAL_DELIVERY_PROOF_ARTIFACT", payload["missing_inputs"])
        self.assertFalse(payload["real_smtp_send_enabled"])
        self.assertFalse(payload["scheduler_install_enabled"])
        self.assertFalse(payload["daily_operation_enabled"])

    def test_audit_s2plt02_terminal_proof_evidence_inventory_json_classifies_dry_run_candidate(self):
        repo_root = Path(__file__).resolve().parents[2]
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
                            "dry_run": True,
                            "allow_send": False,
                            "real_send_attempted": False,
                            "real_smtp_send_enabled": False,
                        },
                        ensure_ascii=False,
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
                            "sent_mail_count": 0,
                            "sent_mail_products": [],
                            "dry_run_mail_products": products,
                            "status_by_product": {product: "dry_run" for product in products},
                        },
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            (run_dir / "adp-daily-run.json").write_text(
                json.dumps(
                    {
                        "status": "succeeded",
                        "run_record": {
                            "date": "2026-06-29",
                            "current_state": "completed",
                            "status": "SUCCESS",
                        },
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                result = main(
                    [
                        "audit-s2plt02-terminal-proof-evidence-inventory",
                        "--repo-root",
                        str(repo_root),
                        "--state-dir",
                        str(state_dir),
                        "--candidate-service-dates",
                        "2026-06-29",
                        "--generated-at",
                        "2026-06-30T13:24:00+10:00",
                        "--json",
                    ]
                )
        payload = json.loads(buffer.getvalue())

        self.assertEqual(result, 2)
        self.assertEqual(payload["status"], "blocked")
        self.assertEqual(payload["task_id"], "S2PLT02-TERMINAL-PROOF-EVIDENCE-INVENTORY")
        self.assertFalse(payload["safe_to_build_terminal_artifact"])
        self.assertFalse(payload["artifact_written"])
        self.assertIn("FIRST_REAL_DELIVERY_DAY", payload["ready_inputs"])
        self.assertIn("SECOND_REAL_DELIVERY_DAY", payload["ready_inputs"])
        self.assertIn("EIGHT_REAL_EMAILS", payload["ready_inputs"])
        self.assertNotIn("SECOND_REAL_DELIVERY_DAY", payload["missing_terminal_inputs"])
        self.assertNotIn("EIGHT_REAL_EMAILS", payload["missing_terminal_inputs"])
        self.assertEqual(payload["blocked_candidate_service_dates"], ["2026-06-29"])
        self.assertEqual(payload["daily_run_succeeded_service_dates"], ["2026-06-29"])
        self.assertEqual(payload["nonterminal_succeeded_dry_run_service_dates"], ["2026-06-29"])
        self.assertEqual(payload["nonterminal_succeeded_dry_run_count"], 1)
        self.assertEqual(payload["blocked_candidate_inputs"][0]["classification"], "blocked_dry_run_not_real_terminal_input")
        self.assertTrue(payload["blocked_candidate_inputs"][0]["daily_run_succeeded"])
        self.assertTrue(payload["blocked_candidate_inputs"][0]["daily_run_succeeded_but_smtp_dry_run_not_terminal"])
        self.assertFalse(payload["blocked_candidate_inputs"][0]["counts_toward_s2plt02_terminal_proof"])
        self.assertFalse(payload["real_smtp_send_enabled"])
        self.assertFalse(payload["scheduler_install_enabled"])
        self.assertFalse(payload["daily_operation_enabled"])

    def test_audit_s2plt02_terminal_proof_evidence_inventory_json_blocks_missing_launchctl_file(self):
        repo_root = Path(__file__).resolve().parents[2]
        with tempfile.TemporaryDirectory() as tmp_dir:
            state_dir = Path(tmp_dir)
            missing_launchctl_file = state_dir / "missing-launchctl-disabled.txt"
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                result = main(
                    [
                        "audit-s2plt02-terminal-proof-evidence-inventory",
                        "--repo-root",
                        str(repo_root),
                        "--state-dir",
                        str(state_dir),
                        "--candidate-service-dates",
                        "2026-06-30",
                        "--launchctl-disabled-file",
                        str(missing_launchctl_file),
                        "--generated-at",
                        "2026-06-30T16:36:09+10:00",
                        "--json",
                    ]
                )
        payload = json.loads(buffer.getvalue())

        self.assertEqual(result, 2)
        self.assertEqual(payload["status"], "blocked")
        self.assertFalse(payload["safe_to_build_terminal_artifact"])
        self.assertFalse(payload["counts_toward_s2plt02_terminal_proof"])
        self.assertIn("launchctl_disabled_file_missing", payload["blocking_reasons"])
        self.assertEqual(payload["launchctl_disabled_file_status"], "missing")
        self.assertEqual(payload["launchctl_disabled_file_ref"], str(missing_launchctl_file))

    def test_plan_s2plt02_terminal_delivery_proof_capture_json_lists_safe_next_steps(self):
        repo_root = Path(__file__).resolve().parents[2]
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            result = main(
                [
                    "plan-s2plt02-terminal-delivery-proof-capture",
                    "--repo-root",
                    str(repo_root),
                    "--generated-at",
                    "2026-06-30T10:41:36+10:00",
                    "--json",
                ]
            )
        payload = json.loads(buffer.getvalue())

        self.assertEqual(result, 2)
        self.assertEqual(payload["status"], "blocked")
        self.assertEqual(payload["task_id"], "S2PLT02-TERMINAL-DELIVERY-PROOF-CAPTURE-PLAN")
        self.assertFalse(payload["terminal_delivery_proof_ready"])
        self.assertFalse(payload["artifact_written"])
        self.assertNotIn("SECOND_REAL_DELIVERY_DAY", payload["blocked_by_missing_inputs"])
        self.assertNotIn("EIGHT_REAL_EMAILS", payload["blocked_by_missing_inputs"])
        self.assertIn("REAL_SCHEDULER_PROOF", payload["blocked_by_missing_inputs"])
        self.assertEqual(payload["authorization_artifact_status"], "pass")
        self.assertTrue(payload["real_proof_capture_authorized"])
        self.assertEqual(payload["authorization_validation_errors"], [])
        self.assertTrue(payload["authorization_validation_state_hash"])
        self.assertTrue(payload["terminal_evidence_inventory_state_hash"])
        input_inventory_summary = payload["terminal_delivery_input_inventory_summary"]
        self.assertEqual(input_inventory_summary["status"], "blocked")
        self.assertEqual(input_inventory_summary["state_hash"], payload["input_inventory_state_hash"])
        self.assertEqual(input_inventory_summary["missing_inputs"], payload["blocked_by_missing_inputs"])
        self.assertEqual(input_inventory_summary["observed_real_delivery_days"], 2)
        self.assertEqual(input_inventory_summary["observed_real_email_count"], 8)
        self.assertFalse(input_inventory_summary["terminal_delivery_proof_ready"])
        artifact_validation_summary = payload["terminal_delivery_artifact_validation_summary"]
        self.assertEqual(artifact_validation_summary["status"], "blocked")
        self.assertEqual(
            artifact_validation_summary["state_hash"],
            payload["terminal_artifact_validation_state_hash"],
        )
        self.assertEqual(
            artifact_validation_summary["artifact_ref"],
            "FINAL_ACCEPTANCE_BUNDLE/s2plt02_terminal_delivery_proof.json",
        )
        self.assertFalse(artifact_validation_summary["artifact_present"])
        self.assertFalse(artifact_validation_summary["terminal_delivery_proof_ready"])
        self.assertFalse(payload["runtime_capture_ready"])
        self.assertIn("adp_allow_smtp_send_false", payload["runtime_capture_blockers"])
        self.assertIn("real_smtp_secret_env_missing", payload["runtime_capture_blockers"])
        self.assertNotIn("daily_run_succeeded_but_smtp_dry_run_not_terminal", payload["runtime_capture_blockers"])
        self.assertEqual(
            payload["required_smtp_secret_env_names"],
            ["ADP_SMTP_HOST", "ADP_SMTP_PORT", "ADP_SMTP_USERNAME", "ADP_SMTP_PASSWORD"],
        )
        self.assertEqual(
            payload["missing_smtp_secret_env_names"],
            ["ADP_SMTP_HOST", "ADP_SMTP_PORT", "ADP_SMTP_USERNAME", "ADP_SMTP_PASSWORD"],
        )
        self.assertFalse(payload["smtp_secret_env_ready"])
        self.assertFalse(payload["smtp_secret_values_logged"])
        self.assertEqual(payload["next_executable_step"], "WAIT_FOR_REAL_SMTP_SCHEDULER_CAPTURE_WINDOW")
        self.assertEqual(payload["current_wait_state"], "WAIT_FOR_REAL_SMTP_SCHEDULER_CAPTURE_WINDOW")
        self.assertEqual(
            payload["current_wait_state"],
            payload["capture_wait_state_guard"]["current_wait_state"],
        )
        self.assertFalse(payload["write_terminal_artifact_allowed"])
        self.assertFalse(payload["scheduler_enable_allowed_by_this_plan"])
        self.assertFalse(payload["production_acceptance_allowed"])
        self.assertIs(
            payload["write_terminal_artifact_allowed"],
            payload["capture_wait_state_guard"]["write_terminal_artifact_allowed"],
        )
        self.assertIs(
            payload["scheduler_enable_allowed_by_this_plan"],
            payload["capture_wait_state_guard"]["scheduler_enable_allowed_by_this_plan"],
        )
        self.assertIs(
            payload["production_acceptance_allowed"],
            payload["capture_wait_state_guard"]["production_acceptance_allowed"],
        )
        guard_command = payload["capture_wait_state_guard"]["allowed_readonly_commands"][0]
        self.assertEqual(
            guard_command,
            "adp plan-s2plt02-terminal-delivery-proof-capture --repo-root . "
            "--generated-at 2026-06-30T10:41:36+10:00 --json",
        )
        repo_root = Path(__file__).resolve().parents[2]
        previous_cwd = Path.cwd()
        try:
            os.chdir(repo_root)
            guard_buffer = io.StringIO()
            with redirect_stdout(guard_buffer):
                guard_result = main(shlex.split(guard_command)[1:])
        finally:
            os.chdir(previous_cwd)
        guard_payload = json.loads(guard_buffer.getvalue())
        self.assertEqual(guard_result, 2)
        self.assertEqual(guard_payload["status"], "blocked")
        self.assertEqual(
            guard_payload["capture_wait_state_guard"]["allowed_readonly_commands"][0],
            guard_command,
        )
        for readonly_command in payload["capture_wait_state_guard"]["allowed_readonly_commands"]:
            command_args = shlex.split(readonly_command)
            self.assertEqual(command_args[0], "adp")
            readonly_buffer = io.StringIO()
            with redirect_stdout(readonly_buffer):
                readonly_result = main(command_args[1:])
            readonly_payload = json.loads(readonly_buffer.getvalue())
            self.assertEqual(readonly_result, 2)
            self.assertEqual(readonly_payload["status"], "blocked")
            self.assertNotIn("state_validation_errors", readonly_payload)
        self.assertEqual(payload["capture_steps"][0]["step_id"], "CAPTURE_SECOND_REAL_M1_M4_SMTP_DAY")
        self.assertEqual(
            payload["capture_steps"][-1]["command"],
            "adp validate-s2plt02-terminal-delivery-proof --repo-root . --json",
        )
        self.assertTrue(payload["no_production_side_effects"])
        self.assertFalse(payload["real_smtp_send_enabled"])
        self.assertFalse(payload["scheduler_install_enabled"])
        self.assertFalse(payload["daily_operation_enabled"])

    def test_build_s2plt02_terminal_delivery_proof_artifact_draft_json_command(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            day1 = tmp / "day1.json"
            day2 = tmp / "day2.json"
            scheduler = tmp / "scheduler.json"
            base_manifest = {
                "manifest_ref": "governance/run_manifests/FUTURE-S2PLT02-DAY1.json",
                "schema_version": 1,
                "project_id": "arxiv-daily-push",
                "task_id": "LOCAL-DAILY-M1-M4-RESEND-EXECUTION",
                "status": "pass",
                "generated_at": "2026-06-28T11:28:25+10:00",
                "service_date": "2026-06-28",
                "mail_delivery_summary": {
                    "planned_send_total": 4,
                    "sent_mail_count": 4,
                    "sent_mail_products": ["M1", "M2", "M3", "M4"],
                    "delivery_ref_by_product": {
                        "M1": "smtp://message/day1-m1",
                        "M2": "smtp://message/day1-m2",
                        "M3": "smtp://message/day1-m3",
                        "M4": "smtp://message/day1-m4",
                    },
                },
                "real_smtp_sent": True,
                "real_smtp_send_enabled": True,
                "stage2_integrated_production_accepted": False,
                "integrated_production_accepted": False,
                "daily_operation_enabled": False,
                "release_uploaded": False,
                "production_restore_executed": False,
                "production_queue_mutated": False,
                "public_schema_changed": False,
                "db_migration_executed": False,
                "source_adapter_changed": False,
                "ranking_algorithm_changed": False,
                "current_pointer_changed": False,
                "v7_1_baseline_changed": False,
                "v7_2_contract_files_changed": False,
                "evidence_refs": ["governance/run_manifests/FUTURE-S2PLT02-DAY1.json"],
            }
            day1.write_text(json.dumps(base_manifest), encoding="utf-8")
            day2_payload = json.loads(json.dumps(base_manifest))
            day2_payload["manifest_ref"] = "governance/run_manifests/FUTURE-S2PLT02-DAY2.json"
            day2_payload["service_date"] = "2026-06-29"
            day2_payload["mail_delivery_summary"]["delivery_ref_by_product"] = {
                "M1": "smtp://message/day2-m1",
                "M2": "smtp://message/day2-m2",
                "M3": "smtp://message/day2-m3",
                "M4": "smtp://message/day2-m4",
            }
            day2_payload["evidence_refs"] = ["governance/run_manifests/FUTURE-S2PLT02-DAY2.json"]
            day2.write_text(json.dumps(day2_payload), encoding="utf-8")
            scheduler.write_text(
                json.dumps(
                    {
                        "proof_ref": "governance/run_manifests/FUTURE-S2PLT02-SCHEDULER-PROOF.json",
                        "status": "pass",
                        "real_scheduler_proven": True,
                        "scheduler_evidence_present": True,
                        "production_acceptance_claimed": False,
                        "integrated_production_accepted": False,
                        "stage2_integrated_production_accepted": False,
                        "daily_operation_enabled": False,
                        "release_uploaded": False,
                        "production_restore_enabled": False,
                        "production_restore_executed": False,
                        "public_schema_changed": False,
                        "db_migration_executed": False,
                        "production_queue_mutated": False,
                        "source_adapter_changed": False,
                        "ranking_algorithm_changed": False,
                        "current_pointer_changed": False,
                        "v7_1_baseline_changed": False,
                        "v7_2_contract_files_changed": False,
                    }
                ),
                encoding="utf-8",
            )
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                result = main(
                    [
                        "build-s2plt02-terminal-delivery-proof-artifact-draft",
                        "--generated-at",
                        "2026-06-30T10:35:11+10:00",
                        "--delivery-manifest",
                        str(day1),
                        "--delivery-manifest",
                        str(day2),
                        "--scheduler-proof",
                        str(scheduler),
                        "--json",
                    ]
                )

        payload = json.loads(buffer.getvalue())
        self.assertEqual(result, 0)
        self.assertEqual(payload["status"], "pass")
        self.assertFalse(payload["artifact_written"])
        self.assertEqual(payload["artifact_draft"]["observed_email_count"], 8)
        self.assertEqual(payload["artifact_validation_errors"], [])
        self.assertFalse(payload["artifact_draft"]["integrated_production_accepted"])

    def test_validate_s2plt02_real_delivery_manifest_json_command(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            manifest = Path(tmp_dir) / "delivery.json"
            manifest.write_text(
                json.dumps(
                    {
                        "manifest_ref": "governance/run_manifests/FUTURE-S2PLT02-DAY2.json",
                        "schema_version": 1,
                        "project_id": "arxiv-daily-push",
                        "task_id": "LOCAL-DAILY-M1-M4-RESEND-EXECUTION",
                        "status": "pass",
                        "generated_at": "2026-06-29T11:28:25+10:00",
                        "service_date": "2026-06-29",
                        "mail_delivery_summary": {
                            "planned_send_total": 4,
                            "sent_mail_count": 4,
                            "sent_mail_products": ["M1", "M2", "M3", "M4"],
                            "delivery_ref_by_product": {
                                "M1": "smtp://message/day2-m1",
                                "M2": "smtp://message/day2-m2",
                                "M3": "smtp://message/day2-m3",
                                "M4": "smtp://message/day2-m4",
                            },
                        },
                        "real_smtp_sent": True,
                        "real_smtp_send_enabled": True,
                        "stage2_integrated_production_accepted": False,
                        "integrated_production_accepted": False,
                        "daily_operation_enabled": False,
                        "release_uploaded": False,
                        "production_restore_executed": False,
                        "production_queue_mutated": False,
                        "public_schema_changed": False,
                        "db_migration_executed": False,
                        "source_adapter_changed": False,
                        "ranking_algorithm_changed": False,
                        "current_pointer_changed": False,
                        "v7_1_baseline_changed": False,
                        "v7_2_contract_files_changed": False,
                        "evidence_refs": ["governance/run_manifests/FUTURE-S2PLT02-DAY2.json"],
                    }
                ),
                encoding="utf-8",
            )
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                result = main(
                    [
                        "validate-s2plt02-real-delivery-manifest",
                        "--delivery-manifest",
                        str(manifest),
                        "--json",
                    ]
                )

        payload = json.loads(buffer.getvalue())
        self.assertEqual(result, 0)
        self.assertEqual(payload["status"], "pass")
        self.assertTrue(payload["delivery_manifest_ready"])
        self.assertEqual(payload["service_date"], "2026-06-29")
        self.assertEqual(payload["observed_email_count"], 4)
        self.assertEqual(payload["sent_mail_products"], ["M1", "M2", "M3", "M4"])
        self.assertEqual(payload["validation_errors"], [])
        self.assertFalse(payload["artifact_written"])
        self.assertFalse(payload["real_smtp_send_enabled"])
        self.assertFalse(payload["scheduler_install_enabled"])
        self.assertFalse(payload["daily_operation_enabled"])

    def test_build_s2plt02_normalized_delivery_manifest_json_command(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            raw = Path(tmp_dir) / "raw-day1.json"
            raw.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "project_id": "arxiv-daily-push",
                        "task_id": "LOCAL-DAILY-M1-M4-RESEND-EXECUTION",
                        "status": "pass",
                        "generated_at": "2026-06-28T11:28:25+10:00",
                        "service_date": "2026-06-28",
                        "mail_delivery_summary": {
                            "planned_send_total": 4,
                            "sent_mail_count": 4,
                            "sent_mail_products": ["M1", "M2", "M3", "M4"],
                            "delivery_ref_by_product": {
                                "M1": "smtp://message/smtp-delivery:87f268d29a31288d",
                                "M2": "smtp://message/smtp-delivery:c72ffcd03a277e1d",
                                "M3": "smtp://message/smtp-delivery:590b7230463ff9f7",
                                "M4": "smtp://message/smtp-delivery:7f815186af789297",
                            },
                        },
                        "evidence_refs": [
                            "arxiv-daily-push/docs/phase_records/PHASE_LOCAL_DAILY_M1_M4_RESEND_EXECUTION_20260628.md"
                        ],
                        "real_smtp_sent": True,
                        "real_smtp_send_enabled": True,
                        "stage2_integrated_production_accepted": False,
                        "integrated_production_accepted": False,
                        "scheduler_enabled": False,
                        "release_uploaded": False,
                        "public_schema_changed": False,
                        "ranking_algorithm_changed": False,
                        "source_adapter_changed": False,
                        "current_pointer_changed": False,
                    }
                ),
                encoding="utf-8",
            )
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                result = main(
                    [
                        "build-s2plt02-normalized-delivery-manifest",
                        "--raw-manifest",
                        str(raw),
                        "--raw-manifest-ref",
                        "governance/run_manifests/ADP-LOCAL-DAILY-M1-M4-RESEND-EXECUTION-20260628.json",
                        "--normalized-manifest-ref",
                        "governance/run_manifests/ADP-S2PLT02-NORMALIZED-REAL-DELIVERY-MANIFEST-20260628.json",
                        "--normalized-at",
                        "2026-06-30T11:45:16+10:00",
                        "--json",
                    ]
                )

        payload = json.loads(buffer.getvalue())
        normalized = payload["normalized_manifest"]
        self.assertEqual(result, 0)
        self.assertEqual(payload["status"], "pass")
        self.assertTrue(payload["normalized_manifest_ready"])
        self.assertEqual(normalized["manifest_ref"], "governance/run_manifests/ADP-S2PLT02-NORMALIZED-REAL-DELIVERY-MANIFEST-20260628.json")
        self.assertEqual(normalized["service_date"], "2026-06-28")
        self.assertFalse(normalized["daily_operation_enabled"])
        self.assertFalse(normalized["production_restore_executed"])
        self.assertFalse(normalized["production_queue_mutated"])
        self.assertFalse(normalized["db_migration_executed"])
        self.assertFalse(normalized["v7_1_baseline_changed"])
        self.assertFalse(normalized["v7_2_contract_files_changed"])
        self.assertEqual(payload["manifest_validation"]["status"], "pass")
        self.assertFalse(payload["artifact_written"])
        self.assertFalse(payload["terminal_delivery_proof_written"])

    def test_validate_s2plt02_real_scheduler_proof_json_command(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            scheduler = Path(tmp_dir) / "scheduler.json"
            scheduler.write_text(
                json.dumps(
                    {
                        "proof_ref": "governance/run_manifests/FUTURE-S2PLT02-SCHEDULER-PROOF.json",
                        "status": "pass",
                        "real_scheduler_proven": True,
                        "scheduler_evidence_present": True,
                        "production_acceptance_claimed": False,
                        "integrated_production_accepted": False,
                        "stage2_integrated_production_accepted": False,
                        "daily_operation_enabled": False,
                        "release_uploaded": False,
                        "production_restore_enabled": False,
                        "production_restore_executed": False,
                        "public_schema_changed": False,
                        "db_migration_executed": False,
                        "production_queue_mutated": False,
                        "source_adapter_changed": False,
                        "ranking_algorithm_changed": False,
                        "current_pointer_changed": False,
                        "v7_1_baseline_changed": False,
                        "v7_2_contract_files_changed": False,
                    }
                ),
                encoding="utf-8",
            )
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                result = main(["validate-s2plt02-real-scheduler-proof", "--scheduler-proof", str(scheduler), "--json"])

        payload = json.loads(buffer.getvalue())
        self.assertEqual(result, 0)
        self.assertEqual(payload["status"], "pass")
        self.assertTrue(payload["scheduler_proof_ready"])
        self.assertFalse(payload["artifact_written"])
        self.assertFalse(payload["scheduler_install_enabled"])
        self.assertFalse(payload["daily_operation_enabled"])
        self.assertEqual(payload["validation_errors"], [])

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

    def test_validate_s2plt03_terminal_resilience_proof_json_blocks_missing_artifact(self):
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            result = main(["validate-s2plt03-terminal-resilience-proof", "--repo-root", ".", "--json"])
        payload = json.loads(buffer.getvalue())

        self.assertEqual(result, 2)
        self.assertEqual(payload["status"], "blocked")
        self.assertFalse(payload["artifact_present"])
        self.assertFalse(payload["terminal_resilience_proof_ready"])
        self.assertFalse(payload["s2plt03_accepted_by_artifact"])
        self.assertIn("s2plt03_terminal_resilience_proof_artifact_missing", payload["validation_errors"])
        self.assertIn("s2plt03_terminal_resilience_proof_artifact_missing", payload["blocking_reasons"])
        self.assertIn("s2plt02_not_accepted", payload["blocking_reasons"])
        self.assertFalse(payload["terminal_gates"]["s2plt02_accepted"])
        self.assertTrue(payload["terminal_gates"]["rate_limit_drill_proven"])
        self.assertTrue(payload["terminal_gates"]["p0_zero"])
        self.assertTrue(payload["terminal_gates"]["p1_zero"])
        self.assertFalse(payload["integrated_production_accepted"])
        self.assertFalse(payload["scheduler_install_enabled"])

    def test_plan_s2plt03_terminal_resilience_proof_capture_json_blocks_until_s2plt02_acceptance(self):
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            result = main(
                [
                    "plan-s2plt03-terminal-resilience-proof-capture",
                    "--repo-root",
                    ".",
                    "--generated-at",
                    "2026-06-30T17:00:08+10:00",
                    "--json",
                ]
            )
        payload = json.loads(buffer.getvalue())

        self.assertEqual(result, 2)
        self.assertEqual(payload["status"], "blocked")
        self.assertEqual(payload["next_executable_step"], "WAIT_FOR_S2PLT02_TERMINAL_ACCEPTANCE")
        self.assertIn("s2plt02_not_accepted", payload["blocking_reasons"])
        self.assertIn("S2PLT02_TERMINAL_DELIVERY_PROOF_ARTIFACT", payload["missing_terminal_inputs"])
        self.assertIn("S2PLT03_TERMINAL_RESILIENCE_PROOF_ARTIFACT", payload["missing_terminal_inputs"])
        self.assertFalse(payload["artifact_written"])
        self.assertFalse(payload["s2plt03_accepted"])
        self.assertFalse(payload["production_acceptance_claimed"])
        self.assertFalse(payload["real_smtp_send_enabled"])
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
        self.assertFalse(payload["next_required_step_is_actionable"])
        self.assertEqual(payload["next_executable_task"], "S2PLT02_TERMINAL_DELIVERY_PROOF")
        self.assertEqual(payload["next_executable_runtime_step"], "WAIT_FOR_REAL_SMTP_SCHEDULER_CAPTURE_WINDOW")
        self.assertEqual(payload["current_wait_state"], "WAIT_FOR_REAL_SMTP_SCHEDULER_CAPTURE_WINDOW")
        self.assertFalse(payload["ready_to_write_live_artifacts"])
        capture_summary = payload["s2plt02_terminal_delivery_capture_plan_summary"]
        self.assertEqual(payload["current_wait_state"], capture_summary["current_wait_state"])
        self.assertIs(
            payload["write_terminal_artifact_allowed"],
            capture_summary["write_terminal_artifact_allowed"],
        )
        self.assertIs(
            payload["scheduler_enable_allowed_by_this_plan"],
            capture_summary["scheduler_enable_allowed_by_this_plan"],
        )
        self.assertIs(
            payload["production_acceptance_allowed"],
            capture_summary["production_acceptance_allowed"],
        )
        self.assertFalse(payload["write_terminal_artifact_allowed"])
        self.assertFalse(payload["scheduler_enable_allowed_by_this_plan"])
        self.assertFalse(payload["production_acceptance_allowed"])
        self.assertEqual(capture_summary["status"], "blocked")
        self.assertEqual(capture_summary["next_executable_step"], "WAIT_FOR_REAL_SMTP_SCHEDULER_CAPTURE_WINDOW")
        self.assertEqual(capture_summary["current_wait_state"], "WAIT_FOR_REAL_SMTP_SCHEDULER_CAPTURE_WINDOW")
        self.assertEqual(
            capture_summary["current_wait_state"],
            capture_summary["capture_wait_state_guard"]["current_wait_state"],
        )
        self.assertEqual(capture_summary["authorization_artifact_status"], "pass")
        self.assertFalse(capture_summary["runtime_capture_ready"])
        self.assertEqual(capture_summary["observed_real_delivery_days"], 2)
        self.assertEqual(capture_summary["observed_real_email_count"], 8)
        self.assertEqual(capture_summary["required_real_delivery_days"], 2)
        self.assertEqual(capture_summary["required_real_email_count"], 8)
        self.assertEqual(capture_summary["terminal_artifact_validation_status"], "blocked")
        self.assertIsInstance(capture_summary["terminal_artifact_validation_state_hash"], str)
        self.assertTrue(capture_summary["terminal_artifact_validation_state_hash"])
        self.assertEqual(
            capture_summary["terminal_artifact_ref"],
            "FINAL_ACCEPTANCE_BUNDLE/s2plt02_terminal_delivery_proof.json",
        )
        self.assertFalse(capture_summary["terminal_artifact_present"])
        self.assertFalse(capture_summary["terminal_artifact_ready"])
        self.assertIn(
            "s2plt02_terminal_delivery_proof_artifact_missing",
            capture_summary["terminal_artifact_validation_errors"],
        )
        self.assertIn(
            "s2plt02_terminal_delivery_proof_artifact_missing",
            capture_summary["terminal_artifact_blocking_reasons"],
        )
        self.assertEqual(capture_summary["remaining_runtime_actions"], [
            "capture_real_launchd_scheduler_proof",
            "write_and_validate_s2plt02_terminal_delivery_proof_artifact",
        ])
        self.assertIn("real_launchd_scheduler_proof_missing", capture_summary["runtime_capture_blockers"])
        self.assertIn("real_smtp_secret_env_missing", capture_summary["runtime_capture_blockers"])
        self.assertEqual(
            capture_summary["missing_smtp_secret_env_names"],
            ["ADP_SMTP_HOST", "ADP_SMTP_PORT", "ADP_SMTP_USERNAME", "ADP_SMTP_PASSWORD"],
        )
        self.assertFalse(capture_summary["smtp_secret_env_ready"])
        self.assertFalse(capture_summary["smtp_secret_values_logged"])
        s2plt03_summary = payload["s2plt03_terminal_resilience_capture_plan_summary"]
        self.assertEqual(s2plt03_summary["status"], "blocked")
        self.assertEqual(s2plt03_summary["state_hash"], "bd5f74277b41f7e43ec1a907f6d13eee215808e86d04594e03bd4ed71091ddd5")
        self.assertEqual(s2plt03_summary["next_executable_step"], "WAIT_FOR_S2PLT02_TERMINAL_ACCEPTANCE")
        self.assertEqual(
            s2plt03_summary["terminal_artifact_ref"],
            "FINAL_ACCEPTANCE_BUNDLE/s2plt03_terminal_resilience_proof.json",
        )
        self.assertEqual(
            s2plt03_summary["s2plt02_terminal_delivery_proof_ref"],
            "FINAL_ACCEPTANCE_BUNDLE/s2plt02_terminal_delivery_proof.json",
        )
        self.assertIn("S2PLT02_TERMINAL_DELIVERY_PROOF_ARTIFACT", s2plt03_summary["missing_terminal_inputs"])
        self.assertIn("S2PLT03_TERMINAL_RESILIENCE_PROOF_ARTIFACT", s2plt03_summary["missing_terminal_inputs"])
        self.assertIn("s2plt02_not_accepted", s2plt03_summary["blocking_reasons"])
        self.assertFalse(s2plt03_summary["artifact_written"])
        self.assertFalse(s2plt03_summary["s2plt03_accepted"])
        self.assertFalse(s2plt03_summary["s2plt03_resilience_drill_completed"])
        self.assertEqual(payload["next_executable_command"], "plan-s2plt02-terminal-delivery-proof-capture")
        self.assertEqual(payload["next_executable_command_args"], {
            "repo_root": ".",
            "generated_at": "2026-06-30T18:03:24+10:00",
            "json": True,
        })
        self.assertFalse(payload["next_executable_command_writes_artifact"])
        self.assertFalse(payload["next_executable_command_satisfies_gate"])
        self.assertEqual(payload["next_executable_command_dry_run_status"], "blocked")
        self.assertEqual(
            payload["next_executable_command_dry_run_evidence_ref"],
            "governance/run_manifests/ADP-S2PLT02-TERMINAL-DELIVERY-PROOF-CAPTURE-PLAN-20260630.json",
        )
        self.assertFalse(payload["next_executable_command_dry_run_wrote_artifact"])
        self.assertFalse(payload["draft_authorization_is_live_authorization"])
        self.assertEqual(payload["live_authorization_artifact_status"], "pass")
        self.assertEqual(
            payload["live_authorization_artifact_path"],
            "FINAL_ACCEPTANCE_BUNDLE/s2plt02_real_proof_capture_authorization.json",
        )
        self.assertEqual(payload["live_authorization_validation_errors"], [])
        self.assertEqual(
            payload["next_executable_command_validation_command"],
            "plan-s2plt02-terminal-delivery-proof-capture --repo-root . "
            "--generated-at 2026-06-30T18:03:24+10:00 --json",
        )
        self.assertEqual(payload["next_executable_evidence_refs"], [
            "governance/run_manifests/ADP-S2PLT02-TERMINAL-DELIVERY-PROOF-CAPTURE-PLAN-20260630.json",
            "arxiv-daily-push/docs/phase_records/PHASE_S2PLT02_TERMINAL_DELIVERY_PROOF_CAPTURE_PLAN.md",
        ])
        self.assertTrue(payload["next_required_step_blocked_by_upstream_evidence"])
        self.assertEqual(
            payload["upstream_blockers"],
            [
                "s2plt04_completion_report_blocked_by_s2plt02_terminal_delivery_proof_missing",
                "s2plt04_completion_report_blocked_by_s2plt03_terminal_resilience_proof_missing",
            ],
        )
        missing_inventory = payload["final_bundle_missing_artifact_inventory"]
        self.assertEqual(missing_inventory["status"], "blocked")
        self.assertEqual(missing_inventory["missing_item_count"], 5)
        self.assertEqual(
            missing_inventory["missing_live_artifact_refs"],
            [
                "FINAL_ACCEPTANCE_BUNDLE/manifest.json",
                "FINAL_ACCEPTANCE_BUNDLE/s2plt04_completion_report.json",
                "FINAL_ACCEPTANCE_BUNDLE/independent_review_signoff.yaml",
                "FINAL_ACCEPTANCE_BUNDLE/final_command_execution.json",
                "HANDOFF/00_下一Agent先读.md",
            ],
        )
        self.assertEqual(missing_inventory["next_executable_task"], payload["next_executable_task"])
        self.assertEqual(
            missing_inventory["next_executable_runtime_step"],
            payload["next_executable_runtime_step"],
        )
        self.assertFalse(missing_inventory["ready_to_write_live_artifacts"])
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
            "governance/run_manifests/ADP-S2PLT02-TERMINAL-CAPTURE-WINDOW-AUDIT-CLI-20260630.json",
            s2plt02_evidence["nonterminal_refs"],
        )
        self.assertIn(
            "governance/run_manifests/ADP-S2PLT02-TERMINAL-PROOF-EVIDENCE-INVENTORY-20260630.json",
            s2plt02_evidence["nonterminal_refs"],
        )
        self.assertIn(
            "governance/run_manifests/ADP-S2PLT02-REAL-PROOF-CAPTURE-READINESS-LIVE-AUTH-SYNC-20260630.json",
            s2plt02_evidence["nonterminal_refs"],
        )
        self.assertEqual(s2plt02_evidence["real_proof_capture_authorization_status"], "pass")
        self.assertTrue(s2plt02_evidence["real_proof_capture_authorized"])
        self.assertNotIn(
            "s2plt02_real_proof_capture_authorization_missing",
            s2plt02_evidence["remaining_terminal_blockers"],
        )
        self.assertEqual(s2plt02_evidence["observed_natural_days"], 2)
        self.assertEqual(s2plt02_evidence["required_natural_days"], 2)
        self.assertEqual(s2plt02_evidence["observed_email_count"], 8)
        self.assertEqual(s2plt02_evidence["required_email_count"], 8)
        self.assertTrue(s2plt02_evidence["m4_watermark_correct"])
        self.assertEqual(
            s2plt02_evidence["m4_watermark_proof_ref"],
            "governance/run_manifests/ADP-S2PLT02-M4-WATERMARK-PROOF-RECORD-20260628.json",
        )
        self.assertNotIn("two_consecutive_real_days_not_proven", s2plt02_evidence["remaining_terminal_blockers"])
        self.assertNotIn("eight_real_emails_not_proven", s2plt02_evidence["remaining_terminal_blockers"])
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
        self.assertFalse(payload["next_required_step_is_actionable"])
        self.assertEqual(payload["next_executable_task"], "S2PLT02_TERMINAL_DELIVERY_PROOF")
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
        self.assertEqual(payload["next_required_step"], "S2PLT04_COMPLETION_REPORT")
        self.assertEqual(payload["next_executable_task"], "S2PLT02_TERMINAL_DELIVERY_PROOF")
        self.assertEqual(payload["next_executable_runtime_step"], "WAIT_FOR_REAL_SMTP_SCHEDULER_CAPTURE_WINDOW")
        self.assertEqual(payload["current_wait_state"], "WAIT_FOR_REAL_SMTP_SCHEDULER_CAPTURE_WINDOW")
        self.assertFalse(payload["ready_to_write_live_artifacts"])
        self.assertIs(
            payload["ready_to_write_live_artifacts"],
            payload["final_bundle_prerequisite_plan"]["ready_to_write_live_artifacts"],
        )
        self.assertEqual(
            payload["final_bundle_prerequisite_plan_state_hash"],
            payload["final_bundle_prerequisite_plan"]["state_hash"],
        )
        self.assertEqual(
            payload["s2plt02_terminal_delivery_capture_plan_summary"],
            payload["final_bundle_prerequisite_plan"]["s2plt02_terminal_delivery_capture_plan_summary"],
        )
        self.assertEqual(
            payload["current_wait_state"],
            payload["s2plt02_terminal_delivery_capture_plan_summary"]["current_wait_state"],
        )
        self.assertEqual(
            payload["s2plt02_terminal_delivery_capture_plan_summary"]["current_wait_state"],
            "WAIT_FOR_REAL_SMTP_SCHEDULER_CAPTURE_WINDOW",
        )
        self.assertEqual(
            payload["s2plt02_terminal_delivery_capture_plan_summary"]["current_wait_state"],
            payload["s2plt02_terminal_delivery_capture_plan_summary"]["capture_wait_state_guard"][
                "current_wait_state"
            ],
        )
        capture_summary = payload["s2plt02_terminal_delivery_capture_plan_summary"]
        wait_guard = capture_summary["capture_wait_state_guard"]
        self.assertIs(capture_summary["write_terminal_artifact_allowed"], wait_guard["write_terminal_artifact_allowed"])
        self.assertIs(
            capture_summary["scheduler_enable_allowed_by_this_plan"],
            wait_guard["scheduler_enable_allowed_by_this_plan"],
        )
        self.assertIs(capture_summary["production_acceptance_allowed"], wait_guard["production_acceptance_allowed"])
        self.assertEqual(
            payload["s2plt03_terminal_resilience_capture_plan_summary"],
            payload["final_bundle_prerequisite_plan"]["s2plt03_terminal_resilience_capture_plan_summary"],
        )
        self.assertEqual(
            payload["s2plt04_completion_evidence_audit_summary"],
            payload["final_bundle_prerequisite_plan"]["s2plt04_completion_evidence_audit_summary"],
        )
        self.assertEqual(payload["s2plt04_completion_evidence_audit_summary"]["status"], "blocked")
        self.assertFalse(payload["s2plt04_completion_evidence_audit_summary"]["completion_report_ready"])
        self.assertFalse(
            payload["s2plt04_completion_evidence_audit_summary"]["s2plt04_completion_report_written"]
        )
        self.assertIn(
            "s2plt02_live_2d_terminal_proof_missing",
            payload["s2plt04_completion_evidence_audit_summary"]["blocking_reasons"],
        )
        self.assertIn(
            "s2plt03_resilience_terminal_proof_missing",
            payload["s2plt04_completion_evidence_audit_summary"]["blocking_reasons"],
        )
        self.assertEqual(
            payload["s2plt03_terminal_resilience_capture_plan_summary"]["next_executable_step"],
            "WAIT_FOR_S2PLT02_TERMINAL_ACCEPTANCE",
        )
        self.assertIn(
            "s2plt02_not_accepted",
            payload["s2plt03_terminal_resilience_capture_plan_summary"]["blocking_reasons"],
        )
        self.assertFalse(payload["s2plt03_terminal_resilience_capture_plan_summary"]["artifact_written"])
        self.assertFalse(payload["s2plt02_terminal_delivery_capture_plan_summary"]["runtime_capture_ready"])
        self.assertIn(
            "real_smtp_secret_env_missing",
            payload["s2plt02_terminal_delivery_capture_plan_summary"]["runtime_capture_blockers"],
        )
        self.assertEqual(
            payload["s2plt02_terminal_delivery_capture_plan_summary"]["missing_smtp_secret_env_names"],
            ["ADP_SMTP_HOST", "ADP_SMTP_PORT", "ADP_SMTP_USERNAME", "ADP_SMTP_PASSWORD"],
        )
        self.assertFalse(payload["s2plt02_terminal_delivery_capture_plan_summary"]["smtp_secret_env_ready"])
        self.assertFalse(payload["s2plt02_terminal_delivery_capture_plan_summary"]["smtp_secret_values_logged"])
        self.assertEqual(payload["s2plt02_runtime_readiness_summary"]["status"], "blocked")
        self.assertTrue(payload["s2plt02_runtime_readiness_summary"]["real_proof_capture_authorized"])
        self.assertIn(
            "real_smtp_secret_env_missing",
            payload["s2plt02_runtime_readiness_summary"]["runtime_capture_blockers"],
        )
        self.assertEqual(
            payload["s2plt02_runtime_readiness_summary"]["missing_smtp_secret_env_names"],
            ["ADP_SMTP_HOST", "ADP_SMTP_PORT", "ADP_SMTP_USERNAME", "ADP_SMTP_PASSWORD"],
        )
        self.assertFalse(payload["s2plt02_runtime_readiness_summary"]["smtp_secret_env_ready"])
        self.assertFalse(payload["s2plt02_runtime_readiness_summary"]["smtp_secret_values_logged"])
        self.assertEqual(
            payload["s2plt02_runtime_readiness_summary"]["remaining_next_actions"],
            [
                "capture_real_launchd_scheduler_proof",
                "write_and_validate_s2plt02_terminal_delivery_proof_artifact",
            ],
        )
        self.assertEqual(
            payload["s2plt02_runtime_readiness_summary"],
            payload["final_bundle_prerequisite_plan"]["s2plt02_runtime_readiness_summary"],
        )
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
