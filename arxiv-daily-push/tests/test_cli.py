import io
import json
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
        self.assertTrue(payload["available_items"]["FINAL_ACCEPTANCE_BUNDLE/no_production_side_effects.json"])
        self.assertIn("independent_final_reviewer_assignment_missing", payload["blocking_reasons"])
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
