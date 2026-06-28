from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from arxiv_daily_push.stage2_final_gate import (
    S2PLT02_BLOCKING_REASONS,
    S2PLT02_FORBIDDEN_FLAGS,
    S2PLT02_REQUIRED_DEPENDENCIES,
    S2PLT02_REQUIRED_EMAIL_COUNT,
    S2PLT02_REQUIRED_EVIDENCE,
    S2PLT02_REQUIRED_MAIL_PRODUCTS,
    S2PLT02_REQUIRED_NATURAL_DAYS,
    S2PLT02_PARTIAL_REAL_DELIVERY_EVIDENCE_REFS,
    S2PLT02_PARTIAL_REAL_DELIVERY_NEWLY_SENT_PRODUCTS,
    S2PLT02_PARTIAL_REAL_DELIVERY_PRODUCTS,
    S2PLT02_M4_WATERMARK_PROOF_MODEL_ID,
    S2PLT02_M4_WATERMARK_PROOF_RECORD_REF,
    S2PLT02_M4_WATERMARK_PROOF_SCOPE,
    S2PLT02_M4_WATERMARK_REQUIRED_TERMINAL_PRODUCTS,
    S2PLT03_BLOCKING_REASONS,
    S2PLT03_FORBIDDEN_FLAGS,
    S2PLT03_LOCAL_DRILL_FORBIDDEN_FLAGS,
    S2PLT03_LOCAL_DRILL_REQUIRED_CASES,
    S2PLT03_REQUIRED_DEPENDENCIES,
    S2PLT03_REQUIRED_EVIDENCE,
    S2PLT04_BLOCKING_REASONS,
    S2PLT04_FORBIDDEN_FLAGS,
    S2PLT04_REQUIRED_DEPENDENCIES,
    S2PLT04_REQUIRED_EVIDENCE,
    S2PMT07_BLOCKING_REASONS,
    S2PMT07_FINAL_ACCEPTANCE_BUNDLE_BLOCKING_REASONS,
    S2PMT07_FINAL_ACCEPTANCE_BUNDLE_FORBIDDEN_FLAGS,
    S2PMT07_FINAL_ACCEPTANCE_BUNDLE_MANIFEST_DECISION,
    S2PMT07_FINAL_ACCEPTANCE_BUNDLE_MANIFEST_REQUIRED_ARTIFACT_VALIDATIONS,
    S2PMT07_FINAL_ACCEPTANCE_BUNDLE_MANIFEST_SCHEMA_VERSION,
    S2PMT07_FINAL_ACCEPTANCE_BUNDLE_NO_PRODUCTION_FLAGS,
    S2PMT07_FINAL_ACCEPTANCE_BUNDLE_REQUIRED_ITEMS,
    S2PMT07_FINAL_BUNDLE_PREREQUISITE_PLAN_BLOCKING_REASONS,
    S2PMT07_FINAL_BUNDLE_PREREQUISITE_PLAN_FORBIDDEN_FLAGS,
    S2PMT07_FINAL_BUNDLE_PREREQUISITE_PLAN_REQUIRED_STEPS,
    S2PMT07_FINAL_COMMAND_EXECUTION_DECISION,
    S2PMT07_FINAL_COMMAND_EXECUTION_NO_PRODUCTION_FLAGS,
    S2PMT07_FINAL_COMMAND_EXECUTION_REQUIRED_FIELDS,
    S2PMT07_FINAL_COMMAND_EXECUTION_SCHEMA_VERSION,
    S2PMT07_NO_PRODUCTION_SIDE_EFFECT_ATTESTATION_DECISION,
    S2PMT07_NO_PRODUCTION_SIDE_EFFECT_ATTESTATION_NO_PRODUCTION_FLAGS,
    S2PMT07_NO_PRODUCTION_SIDE_EFFECT_ATTESTATION_REQUIRED_EVIDENCE_REFS,
    S2PMT07_NO_PRODUCTION_SIDE_EFFECT_ATTESTATION_REQUIRED_FIELDS,
    S2PMT07_NO_PRODUCTION_SIDE_EFFECT_ATTESTATION_SCHEMA_VERSION,
    S2PMT07_LOCAL_RUNTIME_NO_PRODUCTION_REQUIRED_LABELS,
    S2PMT07_LOCAL_RUNTIME_NO_PRODUCTION_REQUIRED_ENV_FLAGS_FALSE,
    S2PMT07_NEXT_AGENT_HANDOFF_DECISION,
    S2PMT07_NEXT_AGENT_HANDOFF_NO_PRODUCTION_FLAGS,
    S2PMT07_NEXT_AGENT_HANDOFF_REQUIRED_ARTIFACT_VALIDATIONS,
    S2PMT07_NEXT_AGENT_HANDOFF_REQUIRED_FIELDS,
    S2PMT07_NEXT_AGENT_HANDOFF_REQUIRED_READER_FILES,
    S2PMT07_NEXT_AGENT_HANDOFF_SCHEMA_VERSION,
    S2PMT07_REMAINING_BLOCKER_MATRIX_REQUIRED_BLOCKERS,
    S2PMT07_INDEPENDENT_REVIEW_SIGNOFF_DECISION,
    S2PMT07_INDEPENDENT_REVIEW_SIGNOFF_NO_PRODUCTION_FLAGS,
    S2PMT07_INDEPENDENT_REVIEW_SIGNOFF_REQUIRED_ARTIFACT_VALIDATIONS,
    S2PMT07_INDEPENDENT_REVIEW_SIGNOFF_REQUIRED_FIELDS,
    S2PMT07_INDEPENDENT_REVIEW_SIGNOFF_SCHEMA_VERSION,
    S2PMT07_FORBIDDEN_PASS_FLAGS,
    S2PMT07_P0_P1_ZERO_PROOF_ASSEMBLY_BLOCKING_REASONS,
    S2PMT07_P0_P1_ZERO_PROOF_ASSEMBLY_FORBIDDEN_FLAGS,
    S2PMT07_P0_P1_ZERO_PROOF_ASSEMBLY_REQUIRED_INPUTS,
    S2PMT07_INDEPENDENT_FINAL_CLOSURE_DECISION_REQUEST_BLOCKING_REASONS,
    S2PMT07_INDEPENDENT_FINAL_CLOSURE_DECISION_REQUEST_FORBIDDEN_FLAGS,
    S2PMT07_INDEPENDENT_FINAL_CLOSURE_DECISION_REQUEST_REQUIRED_INPUTS,
    S2PMT07_INDEPENDENT_FINAL_CLOSURE_DECISION_OWNER_PACKET_BLOCKING_REASONS,
    S2PMT07_INDEPENDENT_FINAL_CLOSURE_DECISION_OWNER_PACKET_FORBIDDEN_FLAGS,
    S2PMT07_INDEPENDENT_FINAL_CLOSURE_DECISION_OWNER_PACKET_REQUIRED_ACTIONS,
    S2PMT07_INDEPENDENT_FINAL_REVIEWER_ASSIGNMENT_REQUEST_BLOCKING_REASONS,
    S2PMT07_INDEPENDENT_FINAL_REVIEWER_ASSIGNMENT_REQUEST_FORBIDDEN_FLAGS,
    S2PMT07_INDEPENDENT_FINAL_REVIEWER_ASSIGNMENT_REQUEST_REQUIRED_INPUTS,
    S2PMT07_INDEPENDENT_FINAL_REVIEWER_ASSIGNMENT_OWNER_PACKET_BLOCKING_REASONS,
    S2PMT07_INDEPENDENT_FINAL_REVIEWER_ASSIGNMENT_OWNER_PACKET_FORBIDDEN_FLAGS,
    S2PMT07_INDEPENDENT_FINAL_REVIEWER_ASSIGNMENT_OWNER_PACKET_REQUIRED_ACTIONS,
    S2PMT07_INDEPENDENT_FINAL_REVIEWER_ASSIGNMENT_DECISION,
    S2PMT07_INDEPENDENT_FINAL_REVIEWER_ASSIGNMENT_NO_PRODUCTION_FLAGS,
    S2PMT07_INDEPENDENT_FINAL_REVIEWER_ASSIGNMENT_REQUIRED_FIELDS,
    S2PMT07_INDEPENDENT_FINAL_REVIEWER_ASSIGNMENT_SCHEMA_VERSION,
    S2PMT07_MAINLINE_ATTESTATION_NO_PRODUCTION_FLAGS,
    S2PMT07_MAINLINE_ATTESTATION_REQUIRED_VALIDATIONS,
    S2PMT07_P0_P1_ZERO_PROOF_CLOSURE_DECISION,
    S2PMT07_P0_P1_ZERO_PROOF_NO_PRODUCTION_FLAGS,
    S2PMT07_P0_P1_ZERO_PROOF_REQUIRED_FIELDS,
    S2PMT07_P0_P1_ZERO_PROOF_SCHEMA_VERSION,
    S2PMT07_REQUIRED_DEPENDENCIES,
    S2PMT07_REQUIRED_EVIDENCE,
    S2PMT07_REQUIRED_TEST_COMMANDS,
    S2PMT07_S2PLT04_COMPLETION_REPORT_DECISION,
    S2PMT07_S2PLT04_COMPLETION_REPORT_NO_PRODUCTION_FLAGS,
    S2PMT07_S2PLT04_COMPLETION_REPORT_REQUIRED_TERMINAL_DEPENDENCIES,
    S2PMT07_S2PLT04_COMPLETION_REPORT_SCHEMA_VERSION,
    build_final_acceptance_bundle_readiness_state,
    build_final_acceptance_bundle_artifact_validation_state,
    build_final_bundle_prerequisite_plan_state,
    build_final_command_execution_hash,
    build_final_command_execution_validation_state,
    build_local_runtime_no_production_state,
    build_no_production_side_effect_attestation_hash,
    build_no_production_side_effect_attestation_validation_state,
    build_next_agent_handoff_hash,
    build_next_agent_handoff_validation_state,
    build_independent_review_signoff_hash,
    build_independent_review_signoff_validation_state,
    build_independent_final_closure_decision_owner_packet_state,
    build_independent_final_closure_decision_request_state,
    build_independent_final_reviewer_assignment_owner_packet_state,
    build_independent_final_reviewer_assignment_hash,
    build_independent_final_reviewer_assignment_validation_state,
    build_independent_final_reviewer_assignment_request_state,
    build_s2pmt07_mainline_attestation_state,
    build_final_acceptance_bundle_manifest_hash,
    build_final_acceptance_bundle_manifest_validation_state,
    build_p0_p1_zero_proof_assembly_state,
    build_p0_p1_zero_proof_artifact_validation_state,
    build_p0_p1_zero_proof_decision_hash,
    build_p0_p1_zero_proof_readiness_state,
    build_s2plt04_completion_report_hash,
    build_s2plt04_completion_report_validation_state,
    build_p0_p1_technical_closure_candidate_state,
    build_s2pmt07_remaining_blocker_matrix_state,
    build_s2plt02_dependency_state,
    build_s2plt02_delivery_evidence_ledger_state,
    build_s2plt02_live_2d_precheck_report,
    build_s2plt02_live_evidence_state,
    build_s2plt02_m4_watermark_proof_state,
    build_s2plt02_partial_real_delivery_state,
    build_s2plt03_dependency_state,
    build_s2plt03_local_resilience_drill_bundle,
    build_s2plt03_resilience_evidence_state,
    build_s2plt03_resilience_precheck_report,
    build_s2plt04_dependency_state,
    build_s2plt04_evidence_state,
    build_s2plt04_integration_candidate_report,
    build_audit_blocker_state,
    build_dependency_state,
    build_evidence_bundle_state,
    build_reviewer_independence_state,
    build_s2pmt07_precheck_report,
    build_test_gate_state,
    validate_s2plt02_live_2d_precheck_report,
    validate_s2plt02_delivery_evidence_ledger_state,
    validate_s2plt02_m4_watermark_proof_state,
    validate_s2plt03_local_resilience_drill_bundle,
    validate_s2plt03_resilience_precheck_report,
    validate_s2plt04_integration_candidate_report,
    validate_final_acceptance_bundle_artifact_validation_state,
    validate_final_acceptance_bundle_readiness_state,
    validate_final_bundle_prerequisite_plan_state,
    validate_final_command_execution_artifact,
    validate_local_runtime_no_production_state,
    validate_no_production_side_effect_attestation,
    validate_next_agent_handoff,
    validate_independent_review_signoff_artifact,
    validate_final_acceptance_bundle_manifest,
    validate_independent_final_closure_decision_owner_packet_state,
    validate_independent_final_closure_decision_request_state,
    validate_independent_final_reviewer_assignment_owner_packet_state,
    validate_independent_final_reviewer_assignment_artifact,
    validate_independent_final_reviewer_assignment_request_state,
    validate_s2pmt07_mainline_attestation_state,
    validate_p0_p1_zero_proof_assembly_state,
    validate_p0_p1_zero_proof_artifact,
    validate_p0_p1_zero_proof_readiness_state,
    validate_s2plt04_completion_report,
    validate_p0_p1_technical_closure_candidate_state,
    validate_s2pmt07_remaining_blocker_matrix_state,
    validate_s2pmt07_precheck_report,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


class Stage2FinalGateTests(unittest.TestCase):
    def test_s2plt02_dependency_state_blocks_without_s2plt01_acceptance(self) -> None:
        state = build_s2plt02_dependency_state()

        self.assertEqual(state["status"], "blocked")
        self.assertEqual(tuple(state["required_dependencies"]), S2PLT02_REQUIRED_DEPENDENCIES)
        self.assertEqual(state["completed_dependencies"], {})
        self.assertEqual(tuple(state["unmet_dependencies"]), S2PLT02_REQUIRED_DEPENDENCIES)
        self.assertEqual(state["s2plt01_acceptance_status"], "blocked_by_inherited_p0_p1_and_final_gates")

    def test_s2plt02_partial_real_delivery_state_records_one_day_four_mail_evidence(self) -> None:
        state = build_s2plt02_partial_real_delivery_state()

        self.assertEqual(state["status"], "partial")
        self.assertEqual(state["observed_natural_days"], 1)
        self.assertEqual(state["observed_email_count"], 4)
        self.assertEqual(tuple(state["sent_mail_products"]), S2PLT02_PARTIAL_REAL_DELIVERY_PRODUCTS)
        self.assertEqual(tuple(state["newly_sent_mail_products"]), S2PLT02_PARTIAL_REAL_DELIVERY_NEWLY_SENT_PRODUCTS)
        self.assertEqual(tuple(state["evidence_refs"]), S2PLT02_PARTIAL_REAL_DELIVERY_EVIDENCE_REFS)
        self.assertTrue(state["real_smtp_evidence_present"])
        self.assertFalse(state["scheduler_evidence_present"])
        self.assertFalse(state["m4_watermark_correct"])
        self.assertFalse(state["s2plt02_accepted"])
        self.assertFalse(state["production_acceptance_claimed"])

    def test_s2plt02_delivery_evidence_ledger_tracks_current_real_manifest_without_acceptance(self) -> None:
        ledger = build_s2plt02_delivery_evidence_ledger_state()

        self.assertEqual(ledger["status"], "partial")
        self.assertEqual(ledger["scope"], "delivery_manifest_ledger_no_s2plt02_acceptance")
        self.assertEqual(ledger["required_natural_days"], S2PLT02_REQUIRED_NATURAL_DAYS)
        self.assertEqual(ledger["observed_natural_days"], 1)
        self.assertEqual(ledger["required_email_count"], S2PLT02_REQUIRED_EMAIL_COUNT)
        self.assertEqual(ledger["observed_email_count"], 4)
        self.assertEqual(ledger["service_dates"], ["2026-06-28"])
        self.assertEqual(ledger["products_by_service_date"]["2026-06-28"], list(S2PLT02_REQUIRED_MAIL_PRODUCTS))
        self.assertEqual(ledger["duplicate_email_count"], 0)
        self.assertEqual(ledger["duplicate_service_date_count"], 0)
        self.assertTrue(ledger["real_smtp_evidence_present"])
        self.assertFalse(ledger["two_day_delivery_evidence_present"])
        self.assertFalse(ledger["s2plt02_accepted"])
        self.assertEqual(validate_s2plt02_delivery_evidence_ledger_state(ledger), [])

    def test_s2plt02_delivery_evidence_ledger_rejects_duplicate_service_date_product(self) -> None:
        base_manifest = build_s2plt02_delivery_evidence_ledger_state()["source_manifests"][0]
        duplicate = dict(base_manifest)
        duplicate["manifest_ref"] = "governance/run_manifests/DUPLICATE-LOCAL-DAILY-M1-M4-20260628.json"

        ledger = build_s2plt02_delivery_evidence_ledger_state(delivery_manifests=[base_manifest, duplicate])

        self.assertEqual(ledger["observed_natural_days"], 1)
        self.assertEqual(ledger["duplicate_service_date_count"], 1)
        self.assertEqual(ledger["duplicate_email_count"], 4)
        self.assertFalse(ledger["two_day_delivery_evidence_present"])
        self.assertIn("duplicate service date manifest: 2026-06-28", ledger["validation_errors"])
        self.assertIn("duplicate email evidence for 2026-06-28/M1", validate_s2plt02_delivery_evidence_ledger_state(ledger))

    def test_s2plt02_delivery_evidence_ledger_rejects_missing_product_and_acceptance_flags(self) -> None:
        base_manifest = build_s2plt02_delivery_evidence_ledger_state()["source_manifests"][0]
        broken = json.loads(json.dumps(base_manifest))
        broken["manifest_ref"] = "governance/run_manifests/BROKEN-LOCAL-DAILY-M1-M4-20260628.json"
        broken["integrated_production_accepted"] = True
        broken["mail_delivery_summary"]["sent_mail_products"] = ["M1", "M2", "M3"]
        broken["mail_delivery_summary"]["sent_mail_count"] = 3
        broken["mail_delivery_summary"]["delivery_ref_by_product"].pop("M4")

        ledger = build_s2plt02_delivery_evidence_ledger_state(delivery_manifests=[broken])

        errors = validate_s2plt02_delivery_evidence_ledger_state(ledger)
        self.assertIn("manifest governance/run_manifests/BROKEN-LOCAL-DAILY-M1-M4-20260628.json sent products must be M1-M4", errors)
        self.assertIn("manifest governance/run_manifests/BROKEN-LOCAL-DAILY-M1-M4-20260628.json integrated_production_accepted must be false", errors)
        self.assertFalse(ledger["two_day_delivery_evidence_present"])

    def test_s2plt02_m4_watermark_proof_blocks_when_current_m4_has_no_explicit_watermark(self) -> None:
        proof = build_s2plt02_m4_watermark_proof_state(watermark_proofs=[])

        self.assertEqual(proof["model_id"], S2PLT02_M4_WATERMARK_PROOF_MODEL_ID)
        self.assertEqual(proof["status"], "blocked")
        self.assertEqual(proof["scope"], S2PLT02_M4_WATERMARK_PROOF_SCOPE)
        self.assertEqual(tuple(proof["required_terminal_mail_products"]), S2PLT02_M4_WATERMARK_REQUIRED_TERMINAL_PRODUCTS)
        self.assertEqual(proof["required_service_dates"], ["2026-06-28"])
        self.assertEqual(proof["covered_service_dates"], [])
        self.assertFalse(proof["m4_watermark_correct"])
        self.assertIn("M4 watermark proof record is missing for 2026-06-28", proof["blocking_reasons"])
        self.assertFalse(proof["s2plt02_accepted"])
        self.assertFalse(proof["production_acceptance_claimed"])
        self.assertEqual(validate_s2plt02_m4_watermark_proof_state(proof), [])

    def test_s2plt02_m4_watermark_proof_consumes_committed_same_day_record_without_acceptance(self) -> None:
        proof = build_s2plt02_m4_watermark_proof_state()

        self.assertEqual(proof["model_id"], S2PLT02_M4_WATERMARK_PROOF_MODEL_ID)
        self.assertEqual(proof["status"], "ready")
        self.assertEqual(proof["proof_refs"], [S2PLT02_M4_WATERMARK_PROOF_RECORD_REF])
        self.assertEqual(proof["covered_service_dates"], ["2026-06-28"])
        self.assertEqual(proof["missing_service_dates"], [])
        self.assertTrue(proof["m4_watermark_correct"])
        self.assertFalse(proof["s2plt02_accepted"])
        self.assertFalse(proof["production_acceptance_claimed"])
        self.assertFalse(proof["stage2_integrated_production_accepted"])
        self.assertEqual(validate_s2plt02_m4_watermark_proof_state(proof), [])

        ready = proof["ready_proofs_by_service_date"]["2026-06-28"]
        self.assertEqual(ready["proof_ref"], S2PLT02_M4_WATERMARK_PROOF_RECORD_REF)
        self.assertEqual(ready["m4_delivery_ref"], "smtp://message/smtp-delivery:7f815186af789297")
        self.assertEqual(ready["terminal_mail_products"], ["M1", "M2", "M3"])

    def test_s2plt02_m4_watermark_proof_accepts_explicit_same_day_proof_without_acceptance(self) -> None:
        ledger = build_s2plt02_delivery_evidence_ledger_state()
        cycle_id = "adp:2026-06-28:EMAIL_LEARNING_V1:M1-M4"
        refs = ledger["delivery_ref_by_service_date"]["2026-06-28"]
        proof_record = {
            "proof_ref": "governance/run_manifests/FUTURE-M4-WATERMARK-PROOF-20260628.json",
            "status": "pass",
            "service_date": "2026-06-28",
            "cycle_id": cycle_id,
            "mail_product_id": "M4",
            "m4_delivery_ref": refs["M4"],
            "terminal_mail_records": [
                {"product_id": "M1", "cycle_id": cycle_id, "status": "SENT", "observed_at": "2026-06-28T07:30:00+10:00", "delivery_ref": refs["M1"]},
                {"product_id": "M2", "cycle_id": cycle_id, "status": "SENT", "observed_at": "2026-06-28T11:30:00+10:00", "delivery_ref": refs["M2"]},
                {"product_id": "M3", "cycle_id": cycle_id, "status": "SENT", "observed_at": "2026-06-28T17:30:00+10:00", "delivery_ref": refs["M3"]},
            ],
            "watermark": {
                "cycle_id": cycle_id,
                "status": "ready",
                "m4_ready": True,
                "m4_cycle_watermark": True,
                "watermark_finalized_at": "2026-06-28T21:30:00+10:00",
            },
            "integrated_production_accepted": False,
            "stage2_integrated_production_accepted": False,
            "daily_operation_enabled": False,
            "scheduler_enabled": False,
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
        }

        proof = build_s2plt02_m4_watermark_proof_state(watermark_proofs=[proof_record])

        self.assertEqual(proof["status"], "ready")
        self.assertEqual(proof["covered_service_dates"], ["2026-06-28"])
        self.assertTrue(proof["m4_watermark_correct"])
        self.assertFalse(proof["s2plt02_accepted"])
        self.assertFalse(proof["production_acceptance_claimed"])
        self.assertEqual(validate_s2plt02_m4_watermark_proof_state(proof), [])

    def test_s2plt02_m4_watermark_proof_rejects_wrong_cycle_and_forbidden_flags(self) -> None:
        ledger = build_s2plt02_delivery_evidence_ledger_state()
        refs = ledger["delivery_ref_by_service_date"]["2026-06-28"]
        broken = {
            "proof_ref": "governance/run_manifests/BROKEN-M4-WATERMARK-PROOF-20260628.json",
            "status": "pass",
            "service_date": "2026-06-28",
            "cycle_id": "adp:wrong-cycle",
            "mail_product_id": "M4",
            "m4_delivery_ref": refs["M4"],
            "terminal_mail_records": [
                {"product_id": "M1", "cycle_id": "adp:wrong-cycle", "status": "SENT", "observed_at": "2026-06-28T07:30:00+10:00", "delivery_ref": refs["M1"]},
                {"product_id": "M2", "cycle_id": "adp:other-cycle", "status": "SENT", "observed_at": "2026-06-28T11:30:00+10:00", "delivery_ref": refs["M2"]},
                {"product_id": "M3", "cycle_id": "adp:wrong-cycle", "status": "SENT", "observed_at": "2026-06-28T17:30:00+10:00", "delivery_ref": refs["M3"]},
            ],
            "watermark": {"cycle_id": "adp:wrong-cycle", "status": "ready", "m4_ready": True, "m4_cycle_watermark": True},
            "integrated_production_accepted": True,
        }

        proof = build_s2plt02_m4_watermark_proof_state(watermark_proofs=[broken])
        errors = validate_s2plt02_m4_watermark_proof_state(proof)

        self.assertEqual(proof["status"], "blocked")
        self.assertFalse(proof["m4_watermark_correct"])
        self.assertIn("proof governance/run_manifests/BROKEN-M4-WATERMARK-PROOF-20260628.json integrated_production_accepted must be false", errors)
        self.assertIn("proof governance/run_manifests/BROKEN-M4-WATERMARK-PROOF-20260628.json derived watermark must be ready", errors)

    def test_s2plt02_live_evidence_state_records_partial_real_run_without_acceptance(self) -> None:
        state = build_s2plt02_live_evidence_state()

        self.assertEqual(state["status"], "blocked")
        self.assertEqual(tuple(state["required_evidence"]), S2PLT02_REQUIRED_EVIDENCE)
        self.assertEqual(state["required_natural_days"], S2PLT02_REQUIRED_NATURAL_DAYS)
        self.assertEqual(state["observed_natural_days"], 1)
        self.assertEqual(state["required_email_count"], S2PLT02_REQUIRED_EMAIL_COUNT)
        self.assertEqual(state["observed_email_count"], 4)
        self.assertEqual(tuple(state["required_mail_products"]), S2PLT02_REQUIRED_MAIL_PRODUCTS)
        self.assertEqual(tuple(state["observed_mail_products"]), S2PLT02_PARTIAL_REAL_DELIVERY_PRODUCTS)
        self.assertFalse(state["available_evidence"]["S2PLT01_ACCEPTED"])
        self.assertFalse(state["available_evidence"]["TWO_CONSECUTIVE_REAL_NATURAL_DAYS"])
        self.assertFalse(state["available_evidence"]["EIGHT_REAL_EMAILS_SENT"])
        self.assertTrue(state["available_evidence"]["NO_DUPLICATE_EMAILS"])
        self.assertFalse(state["available_evidence"]["REAL_SCHEDULER_PROVEN"])
        self.assertTrue(state["available_evidence"]["REAL_SMTP_PROVEN"])
        self.assertTrue(state["m4_watermark_correct"])
        self.assertTrue(state["available_evidence"]["M4_WATERMARK_CORRECT"])
        self.assertEqual(state["m4_watermark_proof"]["status"], "ready")
        self.assertEqual(state["partial_real_delivery_evidence"]["status"], "partial")
        self.assertEqual(state["delivery_evidence_ledger"]["status"], "partial")
        self.assertFalse(state["delivery_evidence_ledger"]["two_day_delivery_evidence_present"])

    def test_s2plt02_live_2d_precheck_fails_closed_without_production_side_effects(self) -> None:
        report = build_s2plt02_live_2d_precheck_report(generated_at="2026-06-26T19:00:00+10:00")

        self.assertEqual(report["status"], "blocked")
        self.assertFalse(report["production_acceptance_claimed"])
        self.assertFalse(report["inherited_p0_p1_closed"])
        for flag in S2PLT02_FORBIDDEN_FLAGS:
            self.assertFalse(report[flag])
        for reason in (
            "s2plt01_not_accepted",
            "two_consecutive_real_days_not_proven",
            "eight_real_emails_not_proven",
            "real_scheduler_not_proven",
            "inherited_v7_1_p0_findings_open",
            "inherited_v7_1_p1_findings_open",
        ):
            self.assertIn(reason, report["blocking_reasons"])
        self.assertNotIn("m4_watermark_not_proven", report["blocking_reasons"])
        self.assertNotIn("real_smtp_not_proven", report["blocking_reasons"])
        self.assertFalse(report["gates"]["s2plt01_accepted"])
        self.assertFalse(report["gates"]["real_scheduler_proven"])
        self.assertTrue(report["gates"]["real_smtp_proven"])
        self.assertEqual(report["evidence"]["observed_natural_days"], 1)
        self.assertEqual(report["evidence"]["observed_email_count"], 4)
        self.assertEqual(validate_s2plt02_live_2d_precheck_report(report), [])

        tampered = dict(report)
        tampered["real_smtp_sent"] = True
        self.assertIn("real_smtp_sent must be false", validate_s2plt02_live_2d_precheck_report(tampered))

    def test_s2plt03_dependency_state_blocks_without_s2plt02_acceptance(self) -> None:
        state = build_s2plt03_dependency_state()

        self.assertEqual(state["status"], "blocked")
        self.assertEqual(tuple(state["required_dependencies"]), S2PLT03_REQUIRED_DEPENDENCIES)
        self.assertEqual(state["completed_dependencies"], {})
        self.assertEqual(tuple(state["unmet_dependencies"]), S2PLT03_REQUIRED_DEPENDENCIES)
        self.assertEqual(state["s2plt02_acceptance_status"], "blocked_by_missing_real_2d_run_and_final_gates")

    def test_s2plt03_local_resilience_drill_bundle_passes_without_acceptance_or_side_effects(self) -> None:
        bundle = build_s2plt03_local_resilience_drill_bundle(generated_at="2026-06-28T03:00:00+10:00")

        self.assertEqual(bundle["status"], "pass")
        self.assertEqual(tuple(bundle["required_drill_cases"]), S2PLT03_LOCAL_DRILL_REQUIRED_CASES)
        self.assertTrue(bundle["all_local_drills_passed"])
        self.assertEqual(set(bundle["available_evidence"]), set(S2PLT03_REQUIRED_EVIDENCE))
        self.assertTrue(all(bundle["available_evidence"].values()))
        self.assertFalse(bundle["s2plt03_accepted"])
        self.assertFalse(bundle["s2plt03_resilience_drill_completed"])
        self.assertFalse(bundle["production_acceptance_claimed"])
        for flag in S2PLT03_LOCAL_DRILL_FORBIDDEN_FLAGS:
            self.assertFalse(bundle[flag])
        self.assertEqual(validate_s2plt03_local_resilience_drill_bundle(bundle), [])

        cases = {case["case_id"]: case for case in bundle["drill_cases"]}
        self.assertTrue(cases["rate_limit_blocks_excess_request"]["passed"])
        self.assertEqual(cases["rate_limit_blocks_excess_request"]["blocked_count"], 1)
        self.assertTrue(cases["parser_drift_quarantines_unknown_schema"]["passed"])
        self.assertIn("missing_required_field:evidence_claims", cases["parser_drift_quarantines_unknown_schema"]["quarantine_reasons"])
        self.assertTrue(cases["restart_recovery_reconciles_pending_rows"]["passed"])
        self.assertEqual(cases["restart_recovery_reconciles_pending_rows"]["rows_before"], cases["restart_recovery_reconciles_pending_rows"]["rows_after"])
        self.assertTrue(cases["disk_pressure_degrades_to_no_write"]["passed"])
        self.assertEqual(cases["disk_pressure_degrades_to_no_write"]["writes_allowed"], 0)
        self.assertTrue(cases["backup_restore_point_hash_matches"]["passed"])
        self.assertTrue(cases["rollback_plan_is_dry_run_executable"]["passed"])
        self.assertTrue(cases["ledger_count_conservation_balances_states"]["passed"])

        tampered = dict(bundle)
        tampered["real_smtp_sent"] = True
        self.assertIn("real_smtp_sent must be false", validate_s2plt03_local_resilience_drill_bundle(tampered))

    def test_s2plt03_resilience_evidence_state_records_local_no_production_drill(self) -> None:
        bundle = build_s2plt03_local_resilience_drill_bundle(generated_at="2026-06-28T03:00:00+10:00")
        state = build_s2plt03_resilience_evidence_state(local_drill_bundle=bundle)

        self.assertEqual(state["status"], "pass")
        self.assertEqual(tuple(state["required_evidence"]), S2PLT03_REQUIRED_EVIDENCE)
        self.assertTrue(state["available_evidence"]["RATE_LIMIT_DRILL"])
        self.assertTrue(state["available_evidence"]["PARSER_DRIFT_DRILL"])
        self.assertTrue(state["available_evidence"]["RESTART_RECOVERY_DRILL"])
        self.assertTrue(state["available_evidence"]["DISK_PRESSURE_DRILL"])
        self.assertTrue(state["available_evidence"]["BACKUP_RESTORE_POINT_PROVEN"])
        self.assertTrue(state["available_evidence"]["ROLLBACK_EXECUTABLE"])
        self.assertTrue(state["available_evidence"]["LEDGER_COUNT_CONSERVATION"])
        self.assertEqual(state["missing_evidence"], [])
        self.assertEqual(state["evidence_scope"], "local_no_production_drill_not_terminal_acceptance")
        self.assertEqual(state["ledger_count_conservation_status"], "local_drill_passed")

    def test_s2plt03_resilience_precheck_fails_closed_without_production_side_effects(self) -> None:
        report = build_s2plt03_resilience_precheck_report(generated_at="2026-06-28T01:30:57+10:00")

        self.assertEqual(report["status"], "blocked")
        self.assertFalse(report["production_acceptance_claimed"])
        self.assertFalse(report["inherited_p0_p1_closed"])
        for flag in S2PLT03_FORBIDDEN_FLAGS:
            self.assertFalse(report[flag])
        self.assertIn("s2plt02_not_accepted", report["blocking_reasons"])
        self.assertIn("inherited_v7_1_p0_findings_open", report["blocking_reasons"])
        self.assertIn("inherited_v7_1_p1_findings_open", report["blocking_reasons"])
        self.assertNotIn("rate_limit_drill_not_proven", report["blocking_reasons"])
        self.assertNotIn("parser_drift_drill_not_proven", report["blocking_reasons"])
        self.assertNotIn("restart_recovery_drill_not_proven", report["blocking_reasons"])
        self.assertNotIn("disk_pressure_drill_not_proven", report["blocking_reasons"])
        self.assertNotIn("backup_restore_point_not_proven", report["blocking_reasons"])
        self.assertNotIn("rollback_executable_not_proven", report["blocking_reasons"])
        self.assertNotIn("ledger_count_conservation_not_proven", report["blocking_reasons"])
        self.assertFalse(report["gates"]["s2plt02_accepted"])
        self.assertTrue(report["gates"]["ledger_count_conserved"])
        self.assertTrue(report["evidence"]["available_evidence"]["RATE_LIMIT_DRILL"])
        self.assertEqual(report["evidence"]["evidence_scope"], "local_no_production_drill_not_terminal_acceptance")
        self.assertEqual(validate_s2plt03_resilience_precheck_report(report), [])

        tampered = dict(report)
        tampered["production_restore_executed"] = True
        self.assertIn("production_restore_executed must be false", validate_s2plt03_resilience_precheck_report(tampered))

    def test_s2plt04_dependency_state_keeps_unaccepted_upstream_tasks_blocked(self) -> None:
        state = build_s2plt04_dependency_state()

        self.assertEqual(state["status"], "blocked")
        self.assertEqual(tuple(state["required_dependencies"]), S2PLT04_REQUIRED_DEPENDENCIES)
        self.assertEqual(state["completed_dependencies"], {})
        self.assertEqual(set(state["unmet_dependencies"]), set(S2PLT04_REQUIRED_DEPENDENCIES))
        self.assertIn("S2PLT01-INDEPENDENT-REPLAY-REVIEW", state["available_local_evidence"])
        self.assertEqual(state["s2plt01_acceptance_status"], "blocked_by_inherited_p0_p1_and_final_gates")
        self.assertEqual(state["s2plt02_status"], "missing_authoritative_completion_evidence")
        self.assertEqual(state["s2plt03_status"], "missing_authoritative_completion_evidence")

    def test_s2plt04_evidence_state_records_available_local_evidence_without_final_bundle(self) -> None:
        state = build_s2plt04_evidence_state()

        self.assertEqual(state["status"], "blocked")
        self.assertEqual(tuple(state["required_evidence"]), S2PLT04_REQUIRED_EVIDENCE)
        self.assertTrue(state["available_evidence"]["STATE_CONSISTENCY_EVIDENCE"])
        self.assertTrue(state["available_evidence"]["CONTENT_EVIDENCE"])
        self.assertFalse(state["available_evidence"]["S2PLT01_ACCEPTED"])
        self.assertFalse(state["available_evidence"]["S2PLT02_2D_REAL_RUN"])
        self.assertFalse(state["available_evidence"]["S2PLT03_RESILIENCE_DRILL"])
        self.assertFalse(state["available_evidence"]["FINAL_ACCEPTANCE_BUNDLE/"])

    def test_s2plt04_binds_state_and_content_evidence_bundles_without_terminal_acceptance(self) -> None:
        report = build_s2plt04_integration_candidate_report(generated_at="2026-06-28T03:26:05+10:00")

        state_bundle = report["evidence"]["state_consistency_evidence_bundle"]
        content_bundle = report["evidence"]["content_evidence_bundle"]
        self.assertEqual(state_bundle["status"], "pass")
        self.assertEqual(content_bundle["status"], "pass")
        self.assertEqual(
            state_bundle["source_tasks"],
            ["S2PMT02", "S2PMT03", "S2PMT04", "S2PMT05", "S2PMT06"],
        )
        self.assertEqual(content_bundle["source_tasks"], ["S2PHT05", "S2PIT04", "S2PKT05"])
        self.assertTrue(state_bundle["no_production_side_effects"])
        self.assertTrue(content_bundle["no_production_side_effects"])
        self.assertEqual(len(state_bundle["evidence_refs"]), 5)
        self.assertEqual(len(content_bundle["evidence_refs"]), 3)
        self.assertRegex(state_bundle["bundle_hash"], r"^[0-9a-f]{64}$")
        self.assertRegex(content_bundle["bundle_hash"], r"^[0-9a-f]{64}$")
        self.assertTrue(report["gates"]["state_consistency_evidence_present"])
        self.assertTrue(report["gates"]["content_evidence_present"])
        self.assertFalse(report["gates"]["final_acceptance_bundle_present"])
        self.assertIn("final_acceptance_bundle_missing", report["blocking_reasons"])
        self.assertEqual(validate_s2plt04_integration_candidate_report(report), [])

    def test_s2plt04_consumes_s2plt03_local_drill_as_nonterminal_evidence(self) -> None:
        report = build_s2plt04_integration_candidate_report(generated_at="2026-06-28T02:24:54+10:00")

        self.assertEqual(report["status"], "blocked")
        self.assertIn("S2PLT03-LOCAL-RESILIENCE-DRILL", report["dependencies"]["available_local_evidence"])
        self.assertTrue(report["evidence"]["available_nonterminal_evidence"]["S2PLT03_LOCAL_RESILIENCE_DRILL"])
        self.assertEqual(
            report["evidence"]["s2plt03_local_drill_scope"],
            "local_no_production_drill_not_terminal_acceptance",
        )
        self.assertTrue(report["gates"]["s2plt03_local_drill_evidence_present"])
        self.assertFalse(report["gates"]["s2plt03_completed"])
        self.assertFalse(report["evidence"]["available_evidence"]["S2PLT03_RESILIENCE_DRILL"])
        self.assertIn("s2plt03_not_completed", report["blocking_reasons"])
        self.assertEqual(validate_s2plt04_integration_candidate_report(report), [])

    def test_s2plt04_consumes_s2plt02_readiness_precheck_as_nonterminal_evidence(self) -> None:
        report = build_s2plt04_integration_candidate_report(generated_at="2026-06-28T02:46:45+10:00")

        self.assertEqual(report["status"], "blocked")
        self.assertIn("S2PLT02-LIVE-2D-PRECHECK", report["dependencies"]["available_local_evidence"])
        self.assertTrue(report["evidence"]["available_nonterminal_evidence"]["S2PLT02_LIVE_2D_PRECHECK"])
        self.assertEqual(
            report["evidence"]["s2plt02_readiness_precheck_scope"],
            "no_production_live_2d_readiness_precheck_only",
        )
        self.assertEqual(
            report["evidence"]["s2plt02_readiness_precheck_status"],
            "blocked_precheck_present_not_terminal_acceptance",
        )
        self.assertTrue(report["gates"]["s2plt02_readiness_precheck_present"])
        self.assertFalse(report["gates"]["s2plt02_completed"])
        self.assertFalse(report["evidence"]["available_evidence"]["S2PLT02_2D_REAL_RUN"])
        self.assertIn("s2plt02_not_completed", report["blocking_reasons"])
        self.assertEqual(validate_s2plt04_integration_candidate_report(report), [])

    def test_s2plt04_consumes_s2plt01_independent_review_as_nonterminal_evidence(self) -> None:
        report = build_s2plt04_integration_candidate_report(generated_at="2026-06-28T03:07:28+10:00")

        self.assertEqual(report["status"], "blocked")
        self.assertIn("S2PLT01-INDEPENDENT-REPLAY-REVIEW", report["dependencies"]["available_local_evidence"])
        self.assertTrue(report["evidence"]["available_nonterminal_evidence"]["S2PLT01_INDEPENDENT_REPLAY_REVIEW"])
        self.assertEqual(
            report["evidence"]["s2plt01_independent_replay_review_scope"],
            "no_production_independent_replay_review_receipt",
        )
        self.assertEqual(
            report["evidence"]["s2plt01_independent_replay_review_status"],
            "blocked_review_package_passed_not_terminal_acceptance",
        )
        self.assertTrue(report["gates"]["s2plt01_independent_replay_review_present"])
        self.assertFalse(report["gates"]["s2plt01_accepted"])
        self.assertFalse(report["evidence"]["available_evidence"]["S2PLT01_ACCEPTED"])
        self.assertIn("s2plt01_not_accepted", report["blocking_reasons"])
        self.assertEqual(validate_s2plt04_integration_candidate_report(report), [])

    def test_s2plt04_integration_candidate_report_fails_closed_without_production_side_effects(self) -> None:
        report = build_s2plt04_integration_candidate_report(generated_at="2026-06-26T18:00:00+10:00")

        self.assertEqual(report["status"], "blocked")
        self.assertFalse(report["production_acceptance_claimed"])
        self.assertFalse(report["inherited_p0_p1_closed"])
        for flag in S2PLT04_FORBIDDEN_FLAGS:
            self.assertFalse(report[flag])
        for reason in S2PLT04_BLOCKING_REASONS:
            self.assertIn(reason, report["blocking_reasons"])
        self.assertIn("s2pmt07_final_gate_precheck_blocked", report["blocking_reasons"])
        self.assertEqual(report["s2pmt07_precheck"]["status"], "blocked")
        self.assertEqual(validate_s2plt04_integration_candidate_report(report), [])

        tampered = dict(report)
        tampered["s2_integration_candidate_ready"] = True
        self.assertIn("s2_integration_candidate_ready must be false", validate_s2plt04_integration_candidate_report(tampered))

    def test_s2plt04_embeds_final_bundle_readiness_detail_without_claiming_bundle(self) -> None:
        report = build_s2plt04_integration_candidate_report(generated_at="2026-06-28T03:51:22+10:00")

        readiness = report["evidence"]["final_acceptance_bundle_readiness"]
        expected_missing = set(S2PMT07_FINAL_ACCEPTANCE_BUNDLE_REQUIRED_ITEMS) - {
            "FINAL_ACCEPTANCE_BUNDLE/no_production_side_effects.json"
        }
        expected_blockers = set(S2PMT07_FINAL_ACCEPTANCE_BUNDLE_BLOCKING_REASONS) - {
            "final_acceptance_bundle_directory_missing",
            "no_production_side_effect_attestation_missing",
        }
        self.assertEqual(readiness["status"], "blocked")
        self.assertEqual(tuple(readiness["required_items"]), S2PMT07_FINAL_ACCEPTANCE_BUNDLE_REQUIRED_ITEMS)
        self.assertEqual(set(readiness["missing_items"]), expected_missing)
        self.assertTrue(expected_blockers.issubset(set(readiness["blocking_reasons"])))
        self.assertNotIn("no_production_side_effect_attestation_missing", readiness["blocking_reasons"])
        self.assertFalse(readiness["bundle_present"])
        self.assertFalse(readiness["bundle_claimed_ready"])
        self.assertFalse(readiness["production_acceptance_claimed"])
        self.assertFalse(report["gates"]["final_acceptance_bundle_present"])
        self.assertFalse(report["evidence"]["available_evidence"]["FINAL_ACCEPTANCE_BUNDLE/"])
        self.assertIn("final_acceptance_bundle_missing", report["blocking_reasons"])
        self.assertEqual(validate_final_acceptance_bundle_readiness_state(readiness), [])
        self.assertEqual(validate_s2plt04_integration_candidate_report(report), [])

    def test_audit_blocker_state_blocks_current_inherited_p0_p1(self) -> None:
        state = build_audit_blocker_state()

        self.assertEqual(state["status"], "blocked")
        self.assertEqual(state["inherited_v7_1_open_p0_findings"], 8)
        self.assertEqual(state["inherited_v7_1_open_p1_findings"], 37)
        self.assertFalse(state["checks"]["P0_zero"])
        self.assertFalse(state["checks"]["P1_zero"])

        cleared = build_audit_blocker_state(inherited_p0=0, inherited_p1=0)
        self.assertEqual(cleared["status"], "pass")

    def test_p0_review_receipt_uses_refreshed_current_evidence(self) -> None:
        receipt_path = REPO_ROOT / "arxiv-daily-push/docs/phase_records/PHASE_S2PMT07_P0_INDEPENDENT_REVIEW_RECEIPT.md"
        manifest_path = REPO_ROOT / "governance/run_manifests/ADP-S2PMT07-P0-INDEPENDENT-REVIEW-RECEIPT-20260626.json"
        package_manifest_path = (
            REPO_ROOT
            / "governance/run_manifests/ADP-S2PMT07-P0-TECHNICAL-CLOSURE-CANDIDATE-PACKAGE-20260627.json"
        )
        package_phase_record_path = (
            REPO_ROOT
            / "arxiv-daily-push/docs/phase_records/PHASE_S2PMT07_P0_TECHNICAL_CLOSURE_CANDIDATE_PACKAGE.md"
        )
        refresh_manifest_path = (
            REPO_ROOT
            / "governance/run_manifests/ADP-S2PMT07-B008-FAKE-SMTP-CRASH-WINDOW-EVIDENCE-20260627.json"
        )
        isolated_proof_manifest_path = (
            REPO_ROOT
            / "governance/run_manifests/ADP-S2PMT07-B001-ISOLATED-PROOF-RECONCILIATION-20260627.json"
        )
        independent_review_manifest_path = (
            REPO_ROOT
            / "governance/run_manifests/ADP-S2PMT07-B001-INDEPENDENT-TECHNICAL-REVIEW-20260627.json"
        )
        a001_independent_review_manifest_path = (
            REPO_ROOT
            / "governance/run_manifests/ADP-S2PMT07-A001-INDEPENDENT-TECHNICAL-REVIEW-20260627.json"
        )
        a002_independent_review_manifest_path = (
            REPO_ROOT
            / "governance/run_manifests/ADP-S2PMT07-A002-INDEPENDENT-TECHNICAL-REVIEW-20260627.json"
        )
        a003_independent_review_manifest_path = (
            REPO_ROOT
            / "governance/run_manifests/ADP-S2PMT07-A003-INDEPENDENT-TECHNICAL-REVIEW-20260627.json"
        )
        a004_independent_review_manifest_path = (
            REPO_ROOT
            / "governance/run_manifests/ADP-S2PMT07-A004-INDEPENDENT-TECHNICAL-REVIEW-20260627.json"
        )
        a005_independent_review_manifest_path = (
            REPO_ROOT
            / "governance/run_manifests/ADP-S2PMT07-A005-INDEPENDENT-TECHNICAL-REVIEW-20260627.json"
        )
        b007_independent_review_manifest_path = (
            REPO_ROOT
            / "governance/run_manifests/ADP-S2PMT07-B007-INDEPENDENT-TECHNICAL-REVIEW-20260627.json"
        )
        b008_independent_review_manifest_path = (
            REPO_ROOT
            / "governance/run_manifests/ADP-S2PMT07-B008-INDEPENDENT-TECHNICAL-REVIEW-20260627.json"
        )
        receipt = receipt_path.read_text(encoding="utf-8")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        receipt_rows = {
            line.split("|", 3)[1].strip(" `"): line
            for line in receipt.splitlines()
            if line.startswith("| `")
        }

        self.assertIn("PHASE_S2PMT02_RESTORE_PATH_SAFETY_A001.md", receipt_rows["A-001"])
        self.assertIn("ADP-S2PMT02-RESTORE-PATH-SAFETY-A001-20260627.json", receipt_rows["A-001"])
        self.assertIn("ADP-S2PMT07-A001-INDEPENDENT-TECHNICAL-REVIEW-20260627.json", receipt_rows["A-001"])
        self.assertIn("用户中心/恢复路径安全扫描.md", receipt_rows["A-001"])
        self.assertNotIn("PHASE_S2PMT02_ATOMIC_RECOVERY.md", receipt_rows["A-001"])
        self.assertIn("PHASE_S2PMT02_RESTORE_ATOMIC_REPLACEMENT_A002.md", receipt_rows["A-002"])
        self.assertIn("ADP-S2PMT02-RESTORE-ATOMIC-REPLACEMENT-A002-20260627.json", receipt_rows["A-002"])
        self.assertIn("ADP-S2PMT07-A002-INDEPENDENT-TECHNICAL-REVIEW-20260627.json", receipt_rows["A-002"])
        self.assertIn("用户中心/恢复原子替换扫描.md", receipt_rows["A-002"])
        self.assertNotIn("PHASE_S2PMT02_ATOMIC_RECOVERY.md", receipt_rows["A-002"])
        self.assertNotIn("PHASE_S2PMT02_RESTORE_SAFETY_REMEDIATION.md", receipt_rows["A-002"])
        self.assertIn("PHASE_S2PMT03_OUTBOX_DELIVERY_A003.md", receipt_rows["A-003"])
        self.assertIn("ADP-S2PMT03-OUTBOX-DELIVERY-A003-20260627.json", receipt_rows["A-003"])
        self.assertIn("ADP-S2PMT07-A003-INDEPENDENT-TECHNICAL-REVIEW-20260627.json", receipt_rows["A-003"])
        self.assertIn("用户中心/事务发件箱与消息ID扫描.md", receipt_rows["A-003"])
        self.assertIn("test_stage2_lease_fencing.py", receipt_rows["A-003"])
        self.assertNotIn("PHASE_S2PMT03_LEASE_FENCING.md", receipt_rows["A-003"])
        self.assertNotIn("ADP-S2PMT03-LEASE-FENCING-20260626.json", receipt_rows["A-003"])
        self.assertIn("PHASE_S2PMT01_FRONTSTAGE_EVIDENCE_A004.md", receipt_rows["A-004"])
        self.assertIn("ADP-S2PMT01-FRONTSTAGE-EVIDENCE-A004-20260627.json", receipt_rows["A-004"])
        self.assertIn("ADP-S2PMT07-A004-INDEPENDENT-TECHNICAL-REVIEW-20260627.json", receipt_rows["A-004"])
        self.assertIn("用户中心/前台陈述证据绑定扫描.md", receipt_rows["A-004"])
        self.assertIn("security_boundary.py", receipt_rows["A-004"])
        self.assertIn("test_security_boundary.py", receipt_rows["A-004"])
        self.assertNotIn("PHASE_S2PMT01_SECURITY_BOUNDARY.md", receipt_rows["A-004"])
        self.assertNotIn("ADP-S2PMT01-SECURITY-BOUNDARY-20260626.json", receipt_rows["A-004"])
        self.assertIn("PHASE_S2PMT01_TRUST_BOUNDARY_A005.md", receipt_rows["A-005"])
        self.assertIn("ADP-S2PMT01-TRUST-BOUNDARY-A005-20260627.json", receipt_rows["A-005"])
        self.assertIn("ADP-S2PMT07-A005-INDEPENDENT-TECHNICAL-REVIEW-20260627.json", receipt_rows["A-005"])
        self.assertIn("用户中心/来源信任边界扫描.md", receipt_rows["A-005"])
        self.assertIn("security_boundary.py", receipt_rows["A-005"])
        self.assertIn("test_security_boundary.py", receipt_rows["A-005"])
        self.assertNotIn("PHASE_S2PMT01_SECURITY_BOUNDARY.md", receipt_rows["A-005"])
        self.assertNotIn("ADP-S2PMT01-SECURITY-BOUNDARY-20260626.json", receipt_rows["A-005"])
        self.assertIn("PHASE_S2PMT04_INSTALL_LIFECYCLE_B001.md", receipt_rows["B-001"])
        self.assertIn("ADP-S2PMT04-INSTALL-LIFECYCLE-B001-20260627.json", receipt_rows["B-001"])
        self.assertIn("ADP-S2PMT07-B001-ISOLATED-PROOF-RECONCILIATION-20260627.json", receipt_rows["B-001"])
        self.assertIn("ADP-S2PMT07-B001-INDEPENDENT-TECHNICAL-REVIEW-20260627.json", receipt_rows["B-001"])
        self.assertIn("用户中心/自动唤醒安装生命周期扫描.md", receipt_rows["B-001"])
        self.assertIn("test_stage2_lifecycle_cache.py", receipt_rows["B-001"])
        self.assertNotIn("PHASE_S2PMT04_LIFECYCLE_CACHE.md", receipt_rows["B-001"])
        self.assertNotIn("ADP-S2PMT04-LIFECYCLE-CACHE-20260626.json", receipt_rows["B-001"])
        self.assertIn("PHASE_S2PMT05_DUPLICATE_TRIGGER_B007.md", receipt_rows["B-007"])
        self.assertIn("ADP-S2PMT05-DUPLICATE-TRIGGER-B007-20260627.json", receipt_rows["B-007"])
        self.assertIn("PHASE_S2PMT07_B007_MULTIPROCESS_RACE_EVIDENCE.md", receipt_rows["B-007"])
        self.assertIn("ADP-S2PMT07-B007-MULTIPROCESS-RACE-EVIDENCE-20260627.json", receipt_rows["B-007"])
        self.assertIn("ADP-S2PMT07-B007-INDEPENDENT-TECHNICAL-REVIEW-20260627.json", receipt_rows["B-007"])
        self.assertIn("stage2_stress_e2e.py", receipt_rows["B-007"])
        self.assertIn("stage2_lease_fencing.py", receipt_rows["B-007"])
        self.assertNotIn("ADP-S2PMT05-STRESS-E2E-20260626.json", receipt_rows["B-007"])
        self.assertIn("PHASE_S2PMT05_SMTP_CRASH_WINDOW_B008.md", receipt_rows["B-008"])
        self.assertIn("ADP-S2PMT05-SMTP-CRASH-WINDOW-B008-20260627.json", receipt_rows["B-008"])
        self.assertIn("PHASE_S2PMT07_B008_FAKE_SMTP_CRASH_WINDOW_EVIDENCE.md", receipt_rows["B-008"])
        self.assertIn("ADP-S2PMT07-B008-FAKE-SMTP-CRASH-WINDOW-EVIDENCE-20260627.json", receipt_rows["B-008"])
        self.assertIn("ADP-S2PMT07-B008-INDEPENDENT-TECHNICAL-REVIEW-20260627.json", receipt_rows["B-008"])
        self.assertIn("stage2_lease_fencing.py", receipt_rows["B-008"])
        self.assertIn("test_smtp_delivery.py", receipt_rows["B-008"])
        self.assertNotIn("ADP-S2PMT05-STRESS-E2E-20260626.json", receipt_rows["B-008"])

        findings = {finding["finding_id"]: finding for finding in manifest["p0_findings"]}
        self.assertEqual(
            manifest["refreshed_findings"],
            ["A-001", "A-002", "A-003", "A-004", "A-005", "B-001", "B-007", "B-008"],
        )
        self.assertEqual(
            manifest["refresh_manifest"],
            "governance/run_manifests/ADP-S2PMT07-P0-TECHNICAL-CLOSURE-CANDIDATE-PACKAGE-20260627.json",
        )
        self.assertEqual(
            manifest["previous_refresh_manifest"],
            "governance/run_manifests/ADP-S2PMT07-B008-INDEPENDENT-TECHNICAL-REVIEW-20260627.json",
        )
        self.assertIn(manifest["refresh_manifest"], manifest["refresh_manifests"])
        self.assertEqual(
            manifest["technical_closure_candidate_package"],
            "governance/run_manifests/ADP-S2PMT07-P0-TECHNICAL-CLOSURE-CANDIDATE-PACKAGE-20260627.json",
        )
        self.assertTrue(manifest["all_p0_finding_level_reviews_passed_no_production_acceptance"])
        self.assertTrue(manifest["p0_closure_package_ready_for_final_gate_review"])
        self.assertIn(
            "governance/run_manifests/ADP-S2PMT07-P0-REVIEW-RECEIPT-REFRESH-B001-ISOLATED-PROOF-20260627.json",
            manifest["refresh_manifest_history"],
        )
        self.assertIn(
            "governance/run_manifests/ADP-S2PMT07-B007-MULTIPROCESS-RACE-EVIDENCE-20260627.json",
            manifest["refresh_manifest_history"],
        )
        self.assertIn(
            "governance/run_manifests/ADP-S2PMT07-A004-INDEPENDENT-TECHNICAL-REVIEW-20260627.json",
            manifest["refresh_manifest_history"],
        )
        self.assertIn(
            "governance/run_manifests/ADP-S2PMT07-A005-INDEPENDENT-TECHNICAL-REVIEW-20260627.json",
            manifest["refresh_manifest_history"],
        )
        self.assertIn(
            "governance/run_manifests/ADP-S2PMT07-B007-INDEPENDENT-TECHNICAL-REVIEW-20260627.json",
            manifest["refresh_manifest_history"],
        )
        self.assertIn(
            "governance/run_manifests/ADP-S2PMT07-B008-INDEPENDENT-TECHNICAL-REVIEW-20260627.json",
            manifest["refresh_manifest_history"],
        )
        self.assertTrue(refresh_manifest_path.exists())
        self.assertTrue(isolated_proof_manifest_path.exists())
        self.assertTrue(independent_review_manifest_path.exists())
        self.assertTrue(a001_independent_review_manifest_path.exists())
        self.assertTrue(a002_independent_review_manifest_path.exists())
        self.assertTrue(a003_independent_review_manifest_path.exists())
        self.assertTrue(a004_independent_review_manifest_path.exists())
        self.assertTrue(a005_independent_review_manifest_path.exists())
        self.assertTrue(b007_independent_review_manifest_path.exists())
        self.assertTrue(b008_independent_review_manifest_path.exists())
        self.assertTrue(package_manifest_path.exists())
        self.assertTrue(package_phase_record_path.exists())
        self.assertFalse(manifest["p0_closure_claimed"])
        self.assertFalse(manifest["stage2_integrated_production_accepted"])
        self.assertIn(
            "arxiv-daily-push/docs/phase_records/PHASE_S2PMT02_RESTORE_PATH_SAFETY_A001.md",
            findings["A-001"]["evidence_refs"],
        )
        self.assertIn(
            "governance/run_manifests/ADP-S2PMT02-RESTORE-PATH-SAFETY-A001-20260627.json",
            findings["A-001"]["evidence_refs"],
        )
        self.assertIn(
            "governance/run_manifests/ADP-S2PMT07-A001-INDEPENDENT-TECHNICAL-REVIEW-20260627.json",
            findings["A-001"]["evidence_refs"],
        )
        self.assertIn(
            "arxiv-daily-push/用户中心/恢复路径安全扫描.md",
            findings["A-001"]["evidence_refs"],
        )
        self.assertEqual(findings["A-001"]["reviewer_verdict"], "PASS_WITH_NO_PRODUCTION_ACCEPTANCE")
        self.assertEqual(
            findings["A-001"]["finding_level_independent_review_receipt"],
            "governance/run_manifests/ADP-S2PMT07-A001-INDEPENDENT-TECHNICAL-REVIEW-20260627.json",
        )
        self.assertIn("finding_level_independent_review_passed", findings["A-001"]["preliminary_review_state"])
        self.assertNotIn("arxiv-daily-push/docs/phase_records/PHASE_S2PMT02_ATOMIC_RECOVERY.md", findings["A-001"]["evidence_refs"])
        self.assertIn(
            "arxiv-daily-push/docs/phase_records/PHASE_S2PMT02_RESTORE_ATOMIC_REPLACEMENT_A002.md",
            findings["A-002"]["evidence_refs"],
        )
        self.assertIn(
            "governance/run_manifests/ADP-S2PMT02-RESTORE-ATOMIC-REPLACEMENT-A002-20260627.json",
            findings["A-002"]["evidence_refs"],
        )
        self.assertIn(
            "governance/run_manifests/ADP-S2PMT07-A002-INDEPENDENT-TECHNICAL-REVIEW-20260627.json",
            findings["A-002"]["evidence_refs"],
        )
        self.assertIn(
            "arxiv-daily-push/用户中心/恢复原子替换扫描.md",
            findings["A-002"]["evidence_refs"],
        )
        self.assertEqual(findings["A-002"]["reviewer_verdict"], "PASS_WITH_NO_PRODUCTION_ACCEPTANCE")
        self.assertEqual(
            findings["A-002"]["finding_level_independent_review_receipt"],
            "governance/run_manifests/ADP-S2PMT07-A002-INDEPENDENT-TECHNICAL-REVIEW-20260627.json",
        )
        self.assertIn("finding_level_independent_review_passed", findings["A-002"]["preliminary_review_state"])
        self.assertNotIn("arxiv-daily-push/docs/phase_records/PHASE_S2PMT02_ATOMIC_RECOVERY.md", findings["A-002"]["evidence_refs"])
        self.assertNotIn(
            "arxiv-daily-push/docs/phase_records/PHASE_S2PMT02_RESTORE_SAFETY_REMEDIATION.md",
            findings["A-002"]["evidence_refs"],
        )
        self.assertIn(
            "arxiv-daily-push/docs/phase_records/PHASE_S2PMT03_OUTBOX_DELIVERY_A003.md",
            findings["A-003"]["evidence_refs"],
        )
        self.assertIn(
            "governance/run_manifests/ADP-S2PMT03-OUTBOX-DELIVERY-A003-20260627.json",
            findings["A-003"]["evidence_refs"],
        )
        self.assertIn(
            "governance/run_manifests/ADP-S2PMT07-A003-INDEPENDENT-TECHNICAL-REVIEW-20260627.json",
            findings["A-003"]["evidence_refs"],
        )
        self.assertIn(
            "arxiv-daily-push/用户中心/事务发件箱与消息ID扫描.md",
            findings["A-003"]["evidence_refs"],
        )
        self.assertIn("arxiv-daily-push/tests/test_stage2_lease_fencing.py", findings["A-003"]["evidence_refs"])
        self.assertEqual(findings["A-003"]["reviewer_verdict"], "PASS_WITH_NO_PRODUCTION_ACCEPTANCE")
        self.assertEqual(
            findings["A-003"]["finding_level_independent_review_receipt"],
            "governance/run_manifests/ADP-S2PMT07-A003-INDEPENDENT-TECHNICAL-REVIEW-20260627.json",
        )
        self.assertIn("finding_level_independent_review_passed", findings["A-003"]["preliminary_review_state"])
        self.assertNotIn("arxiv-daily-push/docs/phase_records/PHASE_S2PMT03_LEASE_FENCING.md", findings["A-003"]["evidence_refs"])
        self.assertNotIn("governance/run_manifests/ADP-S2PMT03-LEASE-FENCING-20260626.json", findings["A-003"]["evidence_refs"])
        self.assertIn(
            "arxiv-daily-push/docs/phase_records/PHASE_S2PMT01_FRONTSTAGE_EVIDENCE_A004.md",
            findings["A-004"]["evidence_refs"],
        )
        self.assertIn(
            "governance/run_manifests/ADP-S2PMT01-FRONTSTAGE-EVIDENCE-A004-20260627.json",
            findings["A-004"]["evidence_refs"],
        )
        self.assertIn(
            "governance/run_manifests/ADP-S2PMT07-A004-INDEPENDENT-TECHNICAL-REVIEW-20260627.json",
            findings["A-004"]["evidence_refs"],
        )
        self.assertIn(
            "arxiv-daily-push/src/arxiv_daily_push/security_boundary.py",
            findings["A-004"]["evidence_refs"],
        )
        self.assertIn(
            "arxiv-daily-push/用户中心/前台陈述证据绑定扫描.md",
            findings["A-004"]["evidence_refs"],
        )
        self.assertIn("arxiv-daily-push/tests/test_security_boundary.py", findings["A-004"]["evidence_refs"])
        self.assertEqual(findings["A-004"]["reviewer_verdict"], "PASS_WITH_NO_PRODUCTION_ACCEPTANCE")
        self.assertEqual(
            findings["A-004"]["finding_level_independent_review_receipt"],
            "governance/run_manifests/ADP-S2PMT07-A004-INDEPENDENT-TECHNICAL-REVIEW-20260627.json",
        )
        self.assertIn("finding_level_independent_review_passed", findings["A-004"]["preliminary_review_state"])
        self.assertNotIn("arxiv-daily-push/docs/phase_records/PHASE_S2PMT01_SECURITY_BOUNDARY.md", findings["A-004"]["evidence_refs"])
        self.assertNotIn("governance/run_manifests/ADP-S2PMT01-SECURITY-BOUNDARY-20260626.json", findings["A-004"]["evidence_refs"])
        self.assertIn(
            "arxiv-daily-push/docs/phase_records/PHASE_S2PMT01_TRUST_BOUNDARY_A005.md",
            findings["A-005"]["evidence_refs"],
        )
        self.assertIn(
            "governance/run_manifests/ADP-S2PMT01-TRUST-BOUNDARY-A005-20260627.json",
            findings["A-005"]["evidence_refs"],
        )
        self.assertIn(
            "governance/run_manifests/ADP-S2PMT07-A005-INDEPENDENT-TECHNICAL-REVIEW-20260627.json",
            findings["A-005"]["evidence_refs"],
        )
        self.assertIn(
            "arxiv-daily-push/src/arxiv_daily_push/security_boundary.py",
            findings["A-005"]["evidence_refs"],
        )
        self.assertIn(
            "arxiv-daily-push/用户中心/来源信任边界扫描.md",
            findings["A-005"]["evidence_refs"],
        )
        self.assertIn("arxiv-daily-push/tests/test_security_boundary.py", findings["A-005"]["evidence_refs"])
        self.assertEqual(findings["A-005"]["reviewer_verdict"], "PASS_WITH_NO_PRODUCTION_ACCEPTANCE")
        self.assertEqual(
            findings["A-005"]["finding_level_independent_review_receipt"],
            "governance/run_manifests/ADP-S2PMT07-A005-INDEPENDENT-TECHNICAL-REVIEW-20260627.json",
        )
        self.assertIn("finding_level_independent_review_passed", findings["A-005"]["preliminary_review_state"])
        self.assertNotIn("arxiv-daily-push/docs/phase_records/PHASE_S2PMT01_SECURITY_BOUNDARY.md", findings["A-005"]["evidence_refs"])
        self.assertNotIn("governance/run_manifests/ADP-S2PMT01-SECURITY-BOUNDARY-20260626.json", findings["A-005"]["evidence_refs"])
        self.assertEqual(findings["B-001"]["fix_task"], "S2PMT04-INSTALL-LIFECYCLE-B001")
        self.assertIn(
            "arxiv-daily-push/docs/phase_records/PHASE_S2PMT04_INSTALL_LIFECYCLE_B001.md",
            findings["B-001"]["evidence_refs"],
        )
        self.assertIn(
            "governance/run_manifests/ADP-S2PMT04-INSTALL-LIFECYCLE-B001-20260627.json",
            findings["B-001"]["evidence_refs"],
        )
        self.assertIn(
            "governance/run_manifests/ADP-S2PMT07-B001-ISOLATED-PROOF-RECONCILIATION-20260627.json",
            findings["B-001"]["evidence_refs"],
        )
        self.assertIn(
            "governance/run_manifests/ADP-S2PMT07-B001-INDEPENDENT-TECHNICAL-REVIEW-20260627.json",
            findings["B-001"]["evidence_refs"],
        )
        self.assertIn(
            "arxiv-daily-push/用户中心/自动唤醒安装生命周期扫描.md",
            findings["B-001"]["evidence_refs"],
        )
        self.assertIn("arxiv-daily-push/tests/test_stage2_lifecycle_cache.py", findings["B-001"]["evidence_refs"])
        self.assertEqual(findings["B-001"]["reviewer_verdict"], "PASS_WITH_NO_PRODUCTION_ACCEPTANCE")
        self.assertEqual(
            findings["B-001"]["finding_level_independent_review_receipt"],
            "governance/run_manifests/ADP-S2PMT07-B001-INDEPENDENT-TECHNICAL-REVIEW-20260627.json",
        )
        self.assertIn("finding_level_independent_review_passed", findings["B-001"]["preliminary_review_state"])
        self.assertNotIn("arxiv-daily-push/docs/phase_records/PHASE_S2PMT04_LIFECYCLE_CACHE.md", findings["B-001"]["evidence_refs"])
        self.assertNotIn("governance/run_manifests/ADP-S2PMT04-LIFECYCLE-CACHE-20260626.json", findings["B-001"]["evidence_refs"])
        self.assertIn(
            "arxiv-daily-push/docs/phase_records/PHASE_S2PMT05_DUPLICATE_TRIGGER_B007.md",
            findings["B-007"]["evidence_refs"],
        )
        self.assertIn(
            "governance/run_manifests/ADP-S2PMT05-DUPLICATE-TRIGGER-B007-20260627.json",
            findings["B-007"]["evidence_refs"],
        )
        self.assertIn("arxiv-daily-push/docs/phase_records/PHASE_S2PMT07_B007_MULTIPROCESS_RACE_EVIDENCE.md", findings["B-007"]["evidence_refs"])
        self.assertIn("governance/run_manifests/ADP-S2PMT07-B007-MULTIPROCESS-RACE-EVIDENCE-20260627.json", findings["B-007"]["evidence_refs"])
        self.assertIn(
            "governance/run_manifests/ADP-S2PMT07-B007-INDEPENDENT-TECHNICAL-REVIEW-20260627.json",
            findings["B-007"]["evidence_refs"],
        )
        self.assertIn("arxiv-daily-push/src/arxiv_daily_push/stage2_stress_e2e.py", findings["B-007"]["evidence_refs"])
        self.assertIn("arxiv-daily-push/src/arxiv_daily_push/stage2_lease_fencing.py", findings["B-007"]["evidence_refs"])
        self.assertIn("arxiv-daily-push/tests/test_stage2_lease_fencing.py", findings["B-007"]["evidence_refs"])
        self.assertEqual(findings["B-007"]["reviewer_verdict"], "PASS_WITH_NO_PRODUCTION_ACCEPTANCE")
        self.assertEqual(
            findings["B-007"]["finding_level_independent_review_receipt"],
            "governance/run_manifests/ADP-S2PMT07-B007-INDEPENDENT-TECHNICAL-REVIEW-20260627.json",
        )
        self.assertIn("finding_level_independent_review_passed", findings["B-007"]["preliminary_review_state"])
        self.assertIn(
            "arxiv-daily-push/docs/phase_records/PHASE_S2PMT05_SMTP_CRASH_WINDOW_B008.md",
            findings["B-008"]["evidence_refs"],
        )
        self.assertIn(
            "governance/run_manifests/ADP-S2PMT05-SMTP-CRASH-WINDOW-B008-20260627.json",
            findings["B-008"]["evidence_refs"],
        )
        self.assertNotIn("governance/run_manifests/ADP-S2PMT05-STRESS-E2E-20260626.json", findings["B-007"]["evidence_refs"])
        self.assertIn("arxiv-daily-push/docs/phase_records/PHASE_S2PMT07_B008_FAKE_SMTP_CRASH_WINDOW_EVIDENCE.md", findings["B-008"]["evidence_refs"])
        self.assertIn("governance/run_manifests/ADP-S2PMT07-B008-FAKE-SMTP-CRASH-WINDOW-EVIDENCE-20260627.json", findings["B-008"]["evidence_refs"])
        self.assertIn(
            "governance/run_manifests/ADP-S2PMT07-B008-INDEPENDENT-TECHNICAL-REVIEW-20260627.json",
            findings["B-008"]["evidence_refs"],
        )
        self.assertIn("arxiv-daily-push/src/arxiv_daily_push/stage2_lease_fencing.py", findings["B-008"]["evidence_refs"])
        self.assertIn("arxiv-daily-push/tests/test_stage2_lease_fencing.py", findings["B-008"]["evidence_refs"])
        self.assertIn("arxiv-daily-push/tests/test_smtp_delivery.py", findings["B-008"]["evidence_refs"])
        self.assertEqual(findings["B-008"]["reviewer_verdict"], "PASS_WITH_NO_PRODUCTION_ACCEPTANCE")
        self.assertEqual(
            findings["B-008"]["finding_level_independent_review_receipt"],
            "governance/run_manifests/ADP-S2PMT07-B008-INDEPENDENT-TECHNICAL-REVIEW-20260627.json",
        )
        self.assertIn("finding_level_independent_review_passed", findings["B-008"]["preliminary_review_state"])
        self.assertNotIn("governance/run_manifests/ADP-S2PMT05-STRESS-E2E-20260626.json", findings["B-008"]["evidence_refs"])

        package_manifest = json.loads(package_manifest_path.read_text(encoding="utf-8"))
        package_phase_record = package_phase_record_path.read_text(encoding="utf-8")
        self.assertEqual(
            package_manifest["status"],
            "technical_closure_candidate_package_ready_no_p0_closure_no_production",
        )
        self.assertEqual(package_manifest["finding_count"], 8)
        self.assertEqual(package_manifest["expected_p0_finding_ids"], list(findings))
        self.assertTrue(package_manifest["package_checks"]["all_8_p0_findings_present"])
        self.assertTrue(package_manifest["package_checks"]["all_finding_level_review_receipts_present"])
        self.assertTrue(
            package_manifest["package_checks"]["all_finding_level_verdicts_pass_with_no_production_acceptance"]
        )
        self.assertTrue(package_manifest["package_checks"]["p0_counter_preserved_open"])
        self.assertTrue(package_manifest["package_checks"]["p1_counter_preserved_open"])
        self.assertFalse(package_manifest["package_checks"]["independent_final_signoff_present"])
        self.assertFalse(package_manifest["package_checks"]["independent_final_command_execution_present"])
        self.assertEqual(package_manifest["inherited_v7_1_open_p0_findings_after"], 8)
        self.assertEqual(package_manifest["inherited_v7_1_open_p1_findings_after"], 37)
        self.assertFalse(package_manifest["p0_closure_claimed"])
        self.assertFalse(package_manifest["p1_closure_claimed"])
        self.assertFalse(package_manifest["closure_claimed"])
        self.assertFalse(package_manifest["s2pmt07_final_pass_claimed"])
        self.assertFalse(package_manifest["stage2_integrated_production_accepted"])
        self.assertFalse(package_manifest["real_smtp_sent"])
        self.assertFalse(package_manifest["scheduler_install_enabled"])
        self.assertFalse(package_manifest["release_packaging_enabled"])
        self.assertFalse(package_manifest["production_restore_enabled"])
        self.assertFalse(package_manifest["current_pointer_changed"])
        self.assertFalse(package_manifest["v7_1_baseline_changed"])
        self.assertFalse(package_manifest["v7_2_contract_files_changed"])
        packaged = {finding["finding_id"]: finding for finding in package_manifest["packaged_findings"]}
        self.assertEqual(set(packaged), set(findings))
        for finding_id, finding in findings.items():
            self.assertEqual(
                packaged[finding_id]["finding_level_independent_review_receipt"],
                finding["finding_level_independent_review_receipt"],
            )
            self.assertEqual(packaged[finding_id]["reviewer_verdict"], "PASS_WITH_NO_PRODUCTION_ACCEPTANCE")
            self.assertTrue(packaged[finding_id]["technical_closure_candidate"])
        self.assertIn("P0 Technical Closure Candidate Package", receipt)
        self.assertIn("P0 findings packaged | `8 / 8`", package_phase_record)
        self.assertIn("Integrated production accepted | `false`", package_phase_record)

        isolated_manifest = json.loads(isolated_proof_manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(isolated_manifest["inherited_finding"], "B-001")
        self.assertEqual(
            isolated_manifest["status"],
            "review_ready_external_isolated_proof_recorded_no_closure",
        )
        self.assertFalse(isolated_manifest["closure_claimed"])
        self.assertFalse(isolated_manifest["p0_closure_claimed"])
        self.assertFalse(isolated_manifest["independent_review_signoff_present"])
        self.assertFalse(isolated_manifest["stage2_integrated_production_accepted"])
        self.assertEqual(isolated_manifest["inherited_v7_1_open_p0_findings_after"], 8)
        self.assertEqual(isolated_manifest["inherited_v7_1_open_p1_findings_after"], 37)
        self.assertTrue(isolated_manifest["external_proof"]["isolated_label"].startswith("com.linze.adp.b001.isolated."))
        self.assertEqual(isolated_manifest["external_proof"]["production_boundary"]["production_labels_touched"], [])
        self.assertFalse(isolated_manifest["external_proof"]["production_boundary"]["real_smtp_send_enabled_or_run"])
        self.assertFalse(isolated_manifest["external_proof"]["production_boundary"]["local_runner_daily_invoked"])
        self.assertTrue(isolated_manifest["reconciliation_checks"]["operation_sequence_complete"])
        self.assertTrue(isolated_manifest["reconciliation_checks"]["artifact_hashes_match"])
        self.assertTrue(isolated_manifest["reconciliation_checks"]["launchd_run_exit_0_observed"])
        self.assertTrue(isolated_manifest["reconciliation_checks"]["launchd_uninstall_not_found_observed"])
        self.assertTrue(isolated_manifest["reconciliation_checks"]["production_labels_not_touched"])
        self.assertEqual(isolated_manifest["reconciliation_summary"]["artifact_hash_mismatches"], [])

        independent_review = json.loads(independent_review_manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(independent_review["reviewer_verdict"], "PASS_WITH_NO_PRODUCTION_ACCEPTANCE")
        self.assertEqual(independent_review["finding_id"], "B-001")
        self.assertTrue(independent_review["technical_closure_candidate"])
        self.assertTrue(independent_review["external_isolated_launchd_proof_verified"])
        self.assertEqual(independent_review["artifact_hashes_checked"], 15)
        self.assertTrue(independent_review["artifact_hashes_match"])
        self.assertTrue(independent_review["operation_sequence_complete"])
        self.assertTrue(independent_review["launchd_run_exit_0_observed"])
        self.assertTrue(independent_review["launchd_uninstall_not_found_observed"])
        self.assertTrue(independent_review["isolated_label_not_loaded_now"])
        self.assertTrue(independent_review["isolated_plist_absent_now"])
        self.assertFalse(independent_review["p0_closure_claimed"])
        self.assertFalse(independent_review["p1_closure_claimed"])
        self.assertFalse(independent_review["s2pmt07_final_pass_claimed"])
        self.assertFalse(independent_review["s2plt04_completed"])
        self.assertFalse(independent_review["stage2_integrated_production_accepted"])
        self.assertFalse(independent_review["scheduler_install_enabled"])
        self.assertFalse(independent_review["real_smtp_sent"])

        a001_independent_review = json.loads(a001_independent_review_manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(a001_independent_review["reviewer_verdict"], "PASS_WITH_NO_PRODUCTION_ACCEPTANCE")
        self.assertEqual(a001_independent_review["finding_id"], "A-001")
        self.assertTrue(a001_independent_review["technical_closure_candidate"])
        self.assertTrue(a001_independent_review["restore_path_safety_verified"])
        self.assertTrue(a001_independent_review["real_stage1_restore_probes_verified"])
        self.assertEqual(a001_independent_review["probe_count"], 4)
        self.assertTrue(a001_independent_review["path_traversal_blocked"])
        self.assertTrue(a001_independent_review["absolute_path_escape_blocked"])
        self.assertTrue(a001_independent_review["symlink_escape_blocked"])
        self.assertTrue(a001_independent_review["target_preserved_on_block"])
        self.assertTrue(a001_independent_review["false_pass_guard_verified"])
        self.assertFalse(a001_independent_review["p0_closure_claimed"])
        self.assertFalse(a001_independent_review["p1_closure_claimed"])
        self.assertFalse(a001_independent_review["closure_claimed"])
        self.assertFalse(a001_independent_review["s2pmt07_final_pass_claimed"])
        self.assertFalse(a001_independent_review["s2plt04_completed"])
        self.assertFalse(a001_independent_review["stage2_integrated_production_accepted"])
        self.assertFalse(a001_independent_review["production_restore_executed"])
        self.assertFalse(a001_independent_review["production_restore_enabled"])
        self.assertFalse(a001_independent_review["scheduler_install_enabled"])
        self.assertFalse(a001_independent_review["real_smtp_sent"])

        a002_independent_review = json.loads(a002_independent_review_manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(a002_independent_review["reviewer_verdict"], "PASS_WITH_NO_PRODUCTION_ACCEPTANCE")
        self.assertEqual(a002_independent_review["finding_id"], "A-002")
        self.assertTrue(a002_independent_review["technical_closure_candidate"])
        self.assertTrue(a002_independent_review["restore_atomic_replacement_verified"])
        self.assertTrue(a002_independent_review["real_stage1_backup_restore_probes_verified"])
        self.assertEqual(a002_independent_review["probe_count"], 3)
        self.assertTrue(a002_independent_review["valid_restore_new_target_verified"])
        self.assertTrue(a002_independent_review["valid_overwrite_previous_backup_preserved"])
        self.assertTrue(a002_independent_review["invalid_overwrite_target_preserved"])
        self.assertTrue(a002_independent_review["temp_files_cleaned"])
        self.assertTrue(a002_independent_review["false_pass_guard_verified"])
        self.assertFalse(a002_independent_review["p0_closure_claimed"])
        self.assertFalse(a002_independent_review["p1_closure_claimed"])
        self.assertFalse(a002_independent_review["closure_claimed"])
        self.assertFalse(a002_independent_review["s2pmt07_final_pass_claimed"])
        self.assertFalse(a002_independent_review["s2plt04_completed"])
        self.assertFalse(a002_independent_review["stage2_integrated_production_accepted"])
        self.assertFalse(a002_independent_review["production_restore_executed"])
        self.assertFalse(a002_independent_review["production_restore_enabled"])
        self.assertFalse(a002_independent_review["production_side_effects_enabled"])
        self.assertFalse(a002_independent_review["scheduler_install_enabled"])
        self.assertFalse(a002_independent_review["real_scheduler_installed"])
        self.assertFalse(a002_independent_review["real_smtp_sent"])
        self.assertFalse(a002_independent_review["real_release_uploaded"])
        self.assertFalse(a002_independent_review["daily_operation_enabled"])
        self.assertFalse(a002_independent_review["public_schema_changed"])
        self.assertFalse(a002_independent_review["db_migration_executed"])
        self.assertFalse(a002_independent_review["queue_mutation_allowed"])
        self.assertFalse(a002_independent_review["current_pointer_changed"])
        self.assertFalse(a002_independent_review["v7_1_baseline_changed"])
        self.assertFalse(a002_independent_review["v7_2_contract_files_changed"])

        a003_independent_review = json.loads(a003_independent_review_manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(a003_independent_review["reviewer_verdict"], "PASS_WITH_NO_PRODUCTION_ACCEPTANCE")
        self.assertEqual(a003_independent_review["finding_id"], "A-003")
        self.assertTrue(a003_independent_review["technical_closure_candidate"])
        self.assertTrue(a003_independent_review["transactional_outbox_verified"])
        self.assertTrue(a003_independent_review["message_id_stability_verified"])
        self.assertTrue(a003_independent_review["changed_revision_rekeys_message_id"])
        self.assertTrue(a003_independent_review["outbox_claim_contention_verified"])
        self.assertEqual(a003_independent_review["claim_attempts"], 100)
        self.assertEqual(a003_independent_review["passed_claims"], 1)
        self.assertEqual(a003_independent_review["blocked_claims"], 99)
        self.assertTrue(a003_independent_review["smtp_accept_pending_commit_fail_closed_verified"])
        self.assertTrue(a003_independent_review["fail_closed_not_retry_safe_not_reclaimed_verified"])
        self.assertTrue(a003_independent_review["provider_accept_finalizes_without_resend_verified"])
        self.assertTrue(a003_independent_review["provider_finalized_not_reclaimed_verified"])
        self.assertTrue(a003_independent_review["at_least_once_with_idempotent_message_id_verified"])
        self.assertFalse(a003_independent_review["exactly_once_claimed"])
        self.assertTrue(a003_independent_review["false_pass_guard_verified"])
        self.assertFalse(a003_independent_review["p0_closure_claimed"])
        self.assertFalse(a003_independent_review["p1_closure_claimed"])
        self.assertFalse(a003_independent_review["closure_claimed"])
        self.assertFalse(a003_independent_review["s2pmt07_final_pass_claimed"])
        self.assertFalse(a003_independent_review["s2plt04_completed"])
        self.assertFalse(a003_independent_review["stage2_integrated_production_accepted"])
        self.assertFalse(a003_independent_review["production_side_effects_enabled"])
        self.assertFalse(a003_independent_review["scheduler_install_enabled"])
        self.assertFalse(a003_independent_review["real_scheduler_installed"])
        self.assertFalse(a003_independent_review["real_smtp_sent"])
        self.assertFalse(a003_independent_review["real_release_uploaded"])
        self.assertFalse(a003_independent_review["daily_operation_enabled"])
        self.assertFalse(a003_independent_review["public_schema_changed"])
        self.assertFalse(a003_independent_review["db_migration_executed"])
        self.assertFalse(a003_independent_review["queue_mutation_allowed"])
        self.assertFalse(a003_independent_review["source_adapter_changed"])
        self.assertFalse(a003_independent_review["ranking_algorithm_changed"])
        self.assertFalse(a003_independent_review["current_pointer_changed"])
        self.assertFalse(a003_independent_review["v7_1_baseline_changed"])
        self.assertFalse(a003_independent_review["v7_2_contract_files_changed"])

        a004_independent_review = json.loads(a004_independent_review_manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(a004_independent_review["reviewer_verdict"], "PASS_WITH_NO_PRODUCTION_ACCEPTANCE")
        self.assertEqual(a004_independent_review["finding_id"], "A-004")
        self.assertTrue(a004_independent_review["technical_closure_candidate"])
        self.assertTrue(a004_independent_review["typed_statement_schema_enforced"])
        self.assertTrue(a004_independent_review["evidence_binding_enforced"])
        self.assertTrue(a004_independent_review["unknown_claims_blocked"])
        self.assertTrue(a004_independent_review["unsupported_foreground_claims_blocked"])
        self.assertTrue(a004_independent_review["frontstage_no_production_side_effects_verified"])
        self.assertTrue(a004_independent_review["false_pass_guard_verified"])
        self.assertTrue(a004_independent_review["tampered_gate_blocks"])
        self.assertEqual(a004_independent_review["required_probe_count"], 5)
        self.assertFalse(a004_independent_review["p0_closure_claimed"])
        self.assertFalse(a004_independent_review["p1_closure_claimed"])
        self.assertFalse(a004_independent_review["closure_claimed"])
        self.assertFalse(a004_independent_review["s2pmt07_final_pass_claimed"])
        self.assertFalse(a004_independent_review["s2plt04_completed"])
        self.assertFalse(a004_independent_review["stage2_integrated_production_accepted"])
        self.assertFalse(a004_independent_review["production_side_effects_enabled"])
        self.assertFalse(a004_independent_review["scheduler_install_enabled"])
        self.assertFalse(a004_independent_review["real_scheduler_installed"])
        self.assertFalse(a004_independent_review["real_smtp_sent"])
        self.assertFalse(a004_independent_review["real_release_uploaded"])
        self.assertFalse(a004_independent_review["daily_operation_enabled"])
        self.assertFalse(a004_independent_review["public_schema_changed"])
        self.assertFalse(a004_independent_review["db_migration_executed"])
        self.assertFalse(a004_independent_review["queue_mutation_allowed"])
        self.assertFalse(a004_independent_review["current_pointer_changed"])
        self.assertFalse(a004_independent_review["v7_1_baseline_changed"])
        self.assertFalse(a004_independent_review["v7_2_contract_files_changed"])

        a005_independent_review = json.loads(a005_independent_review_manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(a005_independent_review["reviewer_verdict"], "PASS_WITH_NO_PRODUCTION_ACCEPTANCE")
        self.assertEqual(a005_independent_review["finding_id"], "A-005")
        self.assertTrue(a005_independent_review["technical_closure_candidate"])
        self.assertTrue(a005_independent_review["untrusted_source_content_verified"])
        self.assertTrue(a005_independent_review["safe_url_rendering_verified"])
        self.assertTrue(a005_independent_review["unsafe_url_schemes_blocked"])
        self.assertTrue(a005_independent_review["unsafe_hosts_blocked"])
        self.assertTrue(a005_independent_review["source_content_tool_requests_blocked"])
        self.assertTrue(a005_independent_review["secret_access_blocked"])
        self.assertTrue(a005_independent_review["repository_write_blocked"])
        self.assertTrue(a005_independent_review["email_send_blocked"])
        self.assertTrue(a005_independent_review["tool_and_secret_boundary_enforced"])
        self.assertTrue(a005_independent_review["trust_receipt_schema_enforced"])
        self.assertTrue(a005_independent_review["false_pass_guard_verified"])
        self.assertTrue(a005_independent_review["tampered_boundary_blocks"])
        self.assertEqual(a005_independent_review["required_probe_count"], 7)
        self.assertFalse(a005_independent_review["p0_closure_claimed"])
        self.assertFalse(a005_independent_review["p1_closure_claimed"])
        self.assertFalse(a005_independent_review["closure_claimed"])
        self.assertFalse(a005_independent_review["s2pmt07_final_pass_claimed"])
        self.assertFalse(a005_independent_review["s2plt04_completed"])
        self.assertFalse(a005_independent_review["stage2_integrated_production_accepted"])
        self.assertFalse(a005_independent_review["production_side_effects_enabled"])
        self.assertFalse(a005_independent_review["scheduler_install_enabled"])
        self.assertFalse(a005_independent_review["real_scheduler_installed"])
        self.assertFalse(a005_independent_review["real_smtp_sent"])
        self.assertFalse(a005_independent_review["real_release_uploaded"])
        self.assertFalse(a005_independent_review["daily_operation_enabled"])
        self.assertFalse(a005_independent_review["public_schema_changed"])
        self.assertFalse(a005_independent_review["db_migration_executed"])
        self.assertFalse(a005_independent_review["queue_mutation_allowed"])
        self.assertFalse(a005_independent_review["current_pointer_changed"])
        self.assertFalse(a005_independent_review["v7_1_baseline_changed"])
        self.assertFalse(a005_independent_review["v7_2_contract_files_changed"])

        b007_independent_review = json.loads(b007_independent_review_manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(b007_independent_review["reviewer_verdict"], "PASS_WITH_NO_PRODUCTION_ACCEPTANCE")
        self.assertEqual(b007_independent_review["finding_id"], "B-007")
        self.assertTrue(b007_independent_review["technical_closure_candidate"])
        self.assertTrue(b007_independent_review["multiprocess_race_harness_verified"])
        self.assertTrue(b007_independent_review["dual_scheduler_race_verified"])
        self.assertTrue(b007_independent_review["four_actor_sources_verified"])
        self.assertEqual(b007_independent_review["process_count"], 4)
        self.assertEqual(b007_independent_review["trigger_count"], 100)
        self.assertEqual(b007_independent_review["attempted_revisions"], 400)
        self.assertEqual(b007_independent_review["observed_active_revisions"], 4)
        self.assertEqual(b007_independent_review["observed_blocked_duplicate_attempts"], 396)
        self.assertTrue(b007_independent_review["one_active_revision_per_mail_product_verified"])
        self.assertTrue(b007_independent_review["reason_coded_duplicate_blocks_verified"])
        self.assertTrue(b007_independent_review["lease_fencing_receipts_verified"])
        self.assertTrue(b007_independent_review["scheduler_side_effects_absent"])
        self.assertTrue(b007_independent_review["false_pass_guard_verified"])
        self.assertFalse(b007_independent_review["p0_closure_claimed"])
        self.assertFalse(b007_independent_review["p1_closure_claimed"])
        self.assertFalse(b007_independent_review["closure_claimed"])
        self.assertFalse(b007_independent_review["s2pmt07_final_pass_claimed"])
        self.assertFalse(b007_independent_review["s2plt04_completed"])
        self.assertFalse(b007_independent_review["stage2_integrated_production_accepted"])
        self.assertFalse(b007_independent_review["production_side_effects_enabled"])
        self.assertFalse(b007_independent_review["scheduler_install_enabled"])
        self.assertFalse(b007_independent_review["real_scheduler_installed"])
        self.assertFalse(b007_independent_review["real_smtp_sent"])
        self.assertFalse(b007_independent_review["real_release_uploaded"])
        self.assertFalse(b007_independent_review["daily_operation_enabled"])
        self.assertFalse(b007_independent_review["public_schema_changed"])
        self.assertFalse(b007_independent_review["db_migration_executed"])
        self.assertFalse(b007_independent_review["queue_mutation_allowed"])
        self.assertFalse(b007_independent_review["current_pointer_changed"])
        self.assertFalse(b007_independent_review["v7_1_baseline_changed"])
        self.assertFalse(b007_independent_review["v7_2_contract_files_changed"])

        b008_independent_review = json.loads(b008_independent_review_manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(b008_independent_review["reviewer_verdict"], "PASS_WITH_NO_PRODUCTION_ACCEPTANCE")
        self.assertEqual(b008_independent_review["finding_id"], "B-008")
        self.assertTrue(b008_independent_review["technical_closure_candidate"])
        self.assertTrue(b008_independent_review["fake_smtp_crash_window_verified"])
        self.assertTrue(b008_independent_review["outbox_claimed_before_smtp_verified"])
        self.assertTrue(b008_independent_review["accepted_pending_commit_reproduced"])
        self.assertTrue(b008_independent_review["idempotent_message_identity_stable"])
        self.assertTrue(b008_independent_review["mail_key_stable"])
        self.assertTrue(b008_independent_review["message_id_stable"])
        self.assertTrue(b008_independent_review["changed_revision_rekeys_message_id"])
        self.assertTrue(b008_independent_review["resend_without_provider_ref_blocked"])
        self.assertTrue(b008_independent_review["provider_accept_ref_required_before_resolution"])
        self.assertTrue(b008_independent_review["provider_accept_ref_finalizes_without_resend"])
        self.assertTrue(b008_independent_review["durable_fake_provider_ref_finalizes_sent"])
        self.assertTrue(b008_independent_review["retry_safe_false_after_accept"])
        self.assertTrue(b008_independent_review["no_real_smtp_side_effect_verified"])
        self.assertTrue(b008_independent_review["false_pass_guard_verified"])
        self.assertFalse(b008_independent_review["p0_closure_claimed"])
        self.assertFalse(b008_independent_review["p1_closure_claimed"])
        self.assertFalse(b008_independent_review["closure_claimed"])
        self.assertFalse(b008_independent_review["s2pmt07_final_pass_claimed"])
        self.assertFalse(b008_independent_review["s2plt04_completed"])
        self.assertFalse(b008_independent_review["stage2_integrated_production_accepted"])
        self.assertFalse(b008_independent_review["production_side_effects_enabled"])
        self.assertFalse(b008_independent_review["scheduler_install_enabled"])
        self.assertFalse(b008_independent_review["real_scheduler_installed"])
        self.assertFalse(b008_independent_review["real_smtp_sent"])
        self.assertFalse(b008_independent_review["real_release_uploaded"])
        self.assertFalse(b008_independent_review["daily_operation_enabled"])
        self.assertFalse(b008_independent_review["public_schema_changed"])
        self.assertFalse(b008_independent_review["db_migration_executed"])
        self.assertFalse(b008_independent_review["queue_mutation_allowed"])
        self.assertFalse(b008_independent_review["current_pointer_changed"])
        self.assertFalse(b008_independent_review["v7_1_baseline_changed"])
        self.assertFalse(b008_independent_review["v7_2_contract_files_changed"])

    def test_p1_review_receipt_uses_refreshed_current_evidence(self) -> None:
        receipt_path = REPO_ROOT / "arxiv-daily-push/docs/phase_records/PHASE_S2PMT07_P1_INDEPENDENT_REVIEW_RECEIPT.md"
        manifest_path = REPO_ROOT / "governance/run_manifests/ADP-S2PMT07-P1-INDEPENDENT-REVIEW-RECEIPT-20260626.json"
        refresh_manifest_path = (
            REPO_ROOT
            / "governance/run_manifests/ADP-S2PMT07-P1-REVIEW-RECEIPT-REFRESH-C011-20260627.json"
        )
        a006_a009_review_manifest_path = (
            REPO_ROOT
            / "governance/run_manifests/ADP-S2PMT07-P1-A006-A009-TECHNICAL-REVIEW-20260627.json"
        )
        a006_a009_review_phase_path = (
            REPO_ROOT
            / "arxiv-daily-push/docs/phase_records/PHASE_S2PMT07_P1_A006_A009_TECHNICAL_REVIEW.md"
        )
        a010_a016_review_manifest_path = (
            REPO_ROOT
            / "governance/run_manifests/ADP-S2PMT07-P1-A010-A016-TECHNICAL-REVIEW-20260627.json"
        )
        a010_a016_review_phase_path = (
            REPO_ROOT
            / "arxiv-daily-push/docs/phase_records/PHASE_S2PMT07_P1_A010_A016_TECHNICAL_REVIEW.md"
        )
        a017_a019_review_manifest_path = (
            REPO_ROOT
            / "governance/run_manifests/ADP-S2PMT07-P1-A017-A019-TECHNICAL-REVIEW-20260627.json"
        )
        a017_a019_review_phase_path = (
            REPO_ROOT
            / "arxiv-daily-push/docs/phase_records/PHASE_S2PMT07_P1_A017_A019_TECHNICAL_REVIEW.md"
        )
        a018_a021_review_manifest_path = (
            REPO_ROOT
            / "governance/run_manifests/ADP-S2PMT07-P1-A018-A021-TECHNICAL-REVIEW-20260627.json"
        )
        a018_a021_review_phase_path = (
            REPO_ROOT
            / "arxiv-daily-push/docs/phase_records/PHASE_S2PMT07_P1_A018_A021_TECHNICAL_REVIEW.md"
        )
        b002_b004_b005_b015_review_manifest_path = (
            REPO_ROOT
            / "governance/run_manifests/ADP-S2PMT07-P1-B002-B004-B005-B015-TECHNICAL-REVIEW-20260627.json"
        )
        b002_b004_b005_b015_review_phase_path = (
            REPO_ROOT
            / "arxiv-daily-push/docs/phase_records/PHASE_S2PMT07_P1_B002_B004_B005_B015_TECHNICAL_REVIEW.md"
        )
        b003_b011_review_manifest_path = (
            REPO_ROOT
            / "governance/run_manifests/ADP-S2PMT07-P1-B003-B011-TECHNICAL-REVIEW-20260627.json"
        )
        b003_b011_review_phase_path = (
            REPO_ROOT
            / "arxiv-daily-push/docs/phase_records/PHASE_S2PMT07_P1_B003_B011_TECHNICAL_REVIEW.md"
        )
        b006_b009_b010_b012_b013_b014_review_manifest_path = (
            REPO_ROOT
            / "governance/run_manifests/ADP-S2PMT07-P1-B006-B009-B010-B012-B013-B014-TECHNICAL-REVIEW-20260627.json"
        )
        b006_b009_b010_b012_b013_b014_review_phase_path = (
            REPO_ROOT
            / "arxiv-daily-push/docs/phase_records/PHASE_S2PMT07_P1_B006_B009_B010_B012_B013_B014_TECHNICAL_REVIEW.md"
        )
        a020_sbom_ci_manifest_path = (
            REPO_ROOT
            / "governance/run_manifests/ADP-S2PMT01-SUPPLY-CHAIN-A020-SBOM-CI-20260627.json"
        )
        a020_review_manifest_path = (
            REPO_ROOT
            / "governance/run_manifests/ADP-S2PMT07-P1-A020-TECHNICAL-REVIEW-20260627.json"
        )
        a020_review_phase_path = (
            REPO_ROOT
            / "arxiv-daily-push/docs/phase_records/PHASE_S2PMT07_P1_A020_TECHNICAL_REVIEW.md"
        )
        c_group_review_manifest_path = (
            REPO_ROOT
            / "governance/run_manifests/ADP-S2PMT07-P1-C001-C003-C005-C006-C007-C010-C011-C012-TECHNICAL-REVIEW-20260627.json"
        )
        c_group_review_phase_path = (
            REPO_ROOT
            / "arxiv-daily-push/docs/phase_records/PHASE_S2PMT07_P1_C001_C003_C005_C006_C007_C010_C011_C012_TECHNICAL_REVIEW.md"
        )
        c002_status_states_manifest_path = (
            REPO_ROOT / "governance/run_manifests/ADP-S2PIT02-OWNER-STATUS-C002-RUNTIME-STATES-20260628.json"
        )
        c002_review_manifest_path = (
            REPO_ROOT / "governance/run_manifests/ADP-S2PMT07-P1-C002-TECHNICAL-REVIEW-20260628.json"
        )
        c002_review_phase_path = (
            REPO_ROOT / "arxiv-daily-push/docs/phase_records/PHASE_S2PMT07_P1_C002_TECHNICAL_REVIEW.md"
        )
        receipt = receipt_path.read_text(encoding="utf-8")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        receipt_rows = {
            line.split("|", 3)[1].strip(" `"): line
            for line in receipt.splitlines()
            if line.startswith("| `")
        }

        expected_current_refs = {
            "A-006": ("PHASE_S2PMT03_RUNTIME_LOCK_A006.md", "ADP-S2PMT03-RUNTIME-LOCK-A006-20260626.json"),
            "A-007": ("PHASE_S2PMT03_STATE_HISTORY_A007.md", "ADP-S2PMT03-STATE-HISTORY-A007-20260626.json"),
            "A-008": (
                "PHASE_S2PMT03_STATE_CONSISTENCY_A008.md",
                "ADP-S2PMT03-STATE-CONSISTENCY-A008-20260626.json",
            ),
            "A-009": (
                "PHASE_S2PMT03_OPTIMISTIC_FENCING_A009.md",
                "ADP-S2PMT03-OPTIMISTIC-FENCING-A009-20260626.json",
            ),
            "A-010": ("PHASE_S2PMT02_ARTIFACT_ATOMIC_PUBLISH.md", "ADP-S2PMT02-ARTIFACT-ATOMIC-PUBLISH-20260626.json"),
            "A-011": ("PHASE_S2PMT02_ARTIFACT_SHA256.md", "ADP-S2PMT02-ARTIFACT-SHA256-20260626.json"),
            "A-012": ("PHASE_S2PMT01_INPUT_URL_SAFETY_A012.md", "ADP-S2PMT01-INPUT-URL-SAFETY-A012-20260626.json"),
            "A-013": ("PHASE_S2PMT04_SCHEDULER_TEMPLATE_A013.md", "ADP-S2PMT04-SCHEDULER-TEMPLATE-A013-20260626.json"),
            "A-014": ("PHASE_S2PMT02_SUPPORTING_FILE_COLLISION.md", "ADP-S2PMT02-SUPPORTING-FILE-COLLISION-20260626.json"),
            "A-015": ("PHASE_S2PMT05_FUTURE_HEARTBEAT_A015.md", "ADP-S2PMT05-FUTURE-HEARTBEAT-A015-20260627.json"),
            "A-016": ("PHASE_S2PMT03_LESSON_REVISION_A016.md", "ADP-S2PMT03-LESSON-REVISION-A016-20260626.json"),
            "A-017": ("PHASE_S2PMT03_SMTP_IDENTITY_A017.md", "ADP-S2PMT03-SMTP-IDENTITY-A017-20260626.json"),
            "A-018": ("PHASE_S2PAT05_ROI_DISCLOSURE_A018.md", "ADP-S2PAT05-ROI-DISCLOSURE-A018-20260626.json"),
            "A-019": ("PHASE_S2PMT01_ZERO_CRITICAL_CLAIM_A019.md", "ADP-S2PMT01-ZERO-CRITICAL-CLAIM-A019-20260627.json"),
            "A-020": (
                "PHASE_S2PMT01_SUPPLY_CHAIN_A020.md",
                "ADP-S2PMT01-SUPPLY-CHAIN-A020-20260626.json",
                "ADP-S2PMT01-SUPPLY-CHAIN-A020-SBOM-CI-20260627.json",
                "ADP-S2PMT07-P1-A020-TECHNICAL-REVIEW-20260627.json",
            ),
            "A-021": ("PHASE_S2PAT05_ROADMAP_STOP_CODE_A021.md", "ADP-S2PAT05-ROADMAP-STOP-CODE-A021-20260626.json"),
            "B-002": ("PHASE_S2PMT04_PROCESS_LIFECYCLE_B002.md", "ADP-S2PMT04-PROCESS-LIFECYCLE-B002-20260627.json"),
            "B-003": ("PHASE_S2PMT03_WATCHDOG_RECOVERY_B003.md", "ADP-S2PMT03-WATCHDOG-RECOVERY-B003-20260626.json"),
            "B-004": ("PHASE_S2PMT04_STARTUP_CONVERGENCE_B004.md", "ADP-S2PMT04-STARTUP-CONVERGENCE-B004-20260626.json"),
            "B-005": ("PHASE_S2PMT04_CACHE_LOW_DISK_B005.md", "ADP-S2PMT04-CACHE-LOW-DISK-B005-20260626.json"),
            "B-006": ("PHASE_S2PMT05_CAPACITY_BASELINE_B006.md", "ADP-S2PMT05-CAPACITY-BASELINE-B006-20260627.json"),
            "B-009": ("PHASE_S2PMT05_FAULT_INJECTION_B009.md", "ADP-S2PMT05-FAULT-INJECTION-B009-20260627.json"),
            "B-010": ("PHASE_S2PMT05_TIME_POLICY_B010.md", "ADP-S2PMT05-TIME-POLICY-B010-20260627.json"),
            "B-011": ("PHASE_S2PMT03_M4_WATERMARK_B011.md", "ADP-S2PMT03-M4-WATERMARK-B011-20260626.json"),
            "B-012": ("PHASE_S2PMT05_E2E_B012.md", "ADP-S2PMT05-E2E-B012-20260627.json"),
            "B-013": ("PHASE_S2PMT05_RESULT_VALIDITY_B013.md", "ADP-S2PMT05-RESULT-VALIDITY-B013-20260626.json"),
            "B-014": ("PHASE_S2PMT05_BACKPRESSURE_B014.md", "ADP-S2PMT05-BACKPRESSURE-B014-20260627.json"),
            "B-015": ("PHASE_S2PMT04_TRANSACTION_COMPLETION_B015.md", "ADP-S2PMT04-TRANSACTION-COMPLETION-B015-20260626.json"),
            "C-001": (
                "PHASE_S2PIT01_SHALLOW_USER_CENTER_C001.md",
                "ADP-S2PIT01-SHALLOW-USER-CENTER-C001-20260627.json",
                "ADP-S2PMT07-P1-C001-C003-C005-C006-C007-C010-C011-C012-TECHNICAL-REVIEW-20260627.json",
            ),
            "C-002": (
                "PHASE_S2PIT02_OWNER_STATUS_C002.md",
                "ADP-S2PIT02-OWNER-STATUS-C002-20260627.json",
                "ADP-S2PIT02-OWNER-STATUS-C002-RUNTIME-STATES-20260628.json",
                "ADP-S2PMT07-P1-C002-TECHNICAL-REVIEW-20260628.json",
            ),
            "C-003": (
                "PHASE_S2PIT05_FOUR_CHECK_FRESHNESS_C003.md",
                "ADP-S2PIT05-FOUR-CHECK-FRESHNESS-C003-20260627.json",
                "ADP-S2PMT07-P1-C001-C003-C005-C006-C007-C010-C011-C012-TECHNICAL-REVIEW-20260627.json",
            ),
            "C-005": (
                "PHASE_S2PMT06_RECOVERABLE_ERROR_C005.md",
                "ADP-S2PMT06-RECOVERABLE-ERROR-C005-20260627.json",
                "ADP-S2PMT07-P1-C001-C003-C005-C006-C007-C010-C011-C012-TECHNICAL-REVIEW-20260627.json",
            ),
            "C-006": (
                "PHASE_S2PMT06_SAFE_CONFIG_C006.md",
                "ADP-S2PMT06-SAFE-CONFIG-C006-20260627.json",
                "ADP-S2PMT07-P1-C001-C003-C005-C006-C007-C010-C011-C012-TECHNICAL-REVIEW-20260627.json",
            ),
            "C-007": (
                "PHASE_S2PMT06_APPEND_ONLY_AUDIT_C007.md",
                "ADP-S2PMT06-APPEND-ONLY-AUDIT-C007-20260627.json",
                "ADP-S2PMT07-P1-C001-C003-C005-C006-C007-C010-C011-C012-TECHNICAL-REVIEW-20260627.json",
            ),
            "C-010": (
                "PHASE_S2PAT05_TRACEABILITY_CHAIN_C010.md",
                "ADP-S2PAT05-TRACEABILITY-CHAIN-C010-20260627.json",
                "用户中心/功能任务测试证据追踪链.md",
                "ADP-S2PMT07-P1-C001-C003-C005-C006-C007-C010-C011-C012-TECHNICAL-REVIEW-20260627.json",
            ),
            "C-011": (
                "PHASE_S2PAT05_LEGACY_MAIL_SCAN_C011.md",
                "ADP-S2PAT05-LEGACY-MAIL-SCAN-C011-20260627.json",
                "用户中心/旧邮件标识兼容扫描.md",
                "ADP-S2PMT07-P1-C001-C003-C005-C006-C007-C010-C011-C012-TECHNICAL-REVIEW-20260627.json",
            ),
            "C-012": (
                "PHASE_S2PMT06_SAFE_MANUAL_ACTION_C012.md",
                "ADP-S2PMT06-SAFE-MANUAL-ACTION-C012-20260627.json",
                "ADP-S2PMT07-P1-C001-C003-C005-C006-C007-C010-C011-C012-TECHNICAL-REVIEW-20260627.json",
            ),
        }
        stale_refs = {
            "A-006": ("PHASE_S2PMT03_LEASE_FENCING.md", "ADP-S2PMT03-LEASE-FENCING-20260626.json"),
            "A-007": ("PHASE_S2PMT03_LEASE_FENCING.md", "ADP-S2PMT03-LEASE-FENCING-20260626.json"),
            "A-008": ("PHASE_S2PMT03_LEASE_FENCING.md", "ADP-S2PMT03-LEASE-FENCING-20260626.json"),
            "A-009": ("PHASE_S2PMT03_LEASE_FENCING.md", "ADP-S2PMT03-LEASE-FENCING-20260626.json"),
            "A-010": (
                "PHASE_S2PMT02_ATOMIC_RECOVERY.md",
                "PHASE_S2PMT02_RESTORE_SAFETY_REMEDIATION.md",
                "ADP-S2PMT02-ATOMIC-RECOVERY-20260626.json",
            ),
            "A-011": (
                "PHASE_S2PMT02_ATOMIC_RECOVERY.md",
                "PHASE_S2PMT02_RESTORE_SAFETY_REMEDIATION.md",
                "ADP-S2PMT02-ATOMIC-RECOVERY-20260626.json",
            ),
            "A-012": ("ADP-S2PMT01-SECURITY-BOUNDARY-20260626.json",),
            "A-013": ("PHASE_S2PMT04_LIFECYCLE_CACHE.md", "ADP-S2PMT04-LIFECYCLE-CACHE-20260626.json"),
            "A-014": (
                "PHASE_S2PMT02_ATOMIC_RECOVERY.md",
                "PHASE_S2PMT02_RESTORE_SAFETY_REMEDIATION.md",
                "ADP-S2PMT02-ATOMIC-RECOVERY-20260626.json",
            ),
            "A-015": ("PHASE_S2PMT05_STRESS_E2E.md", "ADP-S2PMT05-STRESS-E2E-20260626.json"),
            "A-016": ("PHASE_S2PMT03_LEASE_FENCING.md", "ADP-S2PMT03-LEASE-FENCING-20260626.json"),
            "A-017": ("ADP-S2PMT03-LEASE-FENCING-20260626.json",),
            "A-018": ("PHASE_S2PKT01_MAIL_CONTRACT.md",),
            "A-019": ("PHASE_S2PMT01_SECURITY_BOUNDARY.md", "ADP-S2PMT01-SECURITY-BOUNDARY-20260626.json"),
            "A-020": ("ADP-S2PMT01-SECURITY-BOUNDARY-20260626.json",),
            "A-021": ("PHASE_S2PAT02_PRODUCT_CONTRACT.md",),
            "B-002": ("PHASE_S2PMT04_LIFECYCLE_CACHE.md", "ADP-S2PMT04-LIFECYCLE-CACHE-20260626.json"),
            "B-003": ("ADP-S2PMT03-LEASE-FENCING-20260626.json",),
            "B-004": ("ADP-S2PMT04-LIFECYCLE-CACHE-20260626.json",),
            "B-005": ("ADP-S2PMT04-LIFECYCLE-CACHE-20260626.json",),
            "B-006": ("ADP-S2PMT05-STRESS-E2E-20260626.json",),
            "B-009": ("ADP-S2PMT05-STRESS-E2E-20260626.json",),
            "B-010": ("ADP-S2PMT05-STRESS-E2E-20260626.json",),
            "B-011": ("ADP-S2PMT03-LEASE-FENCING-20260626.json",),
            "B-012": ("ADP-S2PMT05-STRESS-E2E-20260626.json",),
            "B-013": ("ADP-S2PHT05-CONTENT-QUALITY-GATE-20260626.json", "S2PHT05"),
            "B-014": ("ADP-S2PMT05-STRESS-E2E-20260626.json",),
            "B-015": ("ADP-S2PMT04-LIFECYCLE-CACHE-20260626.json",),
            "C-001": (
                "PHASE_S2PIT01_USER_CENTER.md",
                "ADP-S2PIT01-USER-CENTER-20260625.json",
                "docs/owner/00_用户中心/00_开始这里.md",
            ),
            "C-002": (
                "PHASE_S2PIT02_RUNTIME_DASHBOARD.md",
                "ADP-S2PIT02-RUNTIME-DASHBOARD-20260625.json",
                "docs/owner/00_用户中心/01_当前状态.md",
            ),
            "C-003": ("PHASE_S2PMT06_OWNER_UX.md", "ADP-S2PMT06-OWNER-UX-20260626.json"),
            "C-005": ("PHASE_S2PMT06_OWNER_UX.md", "ADP-S2PMT06-OWNER-UX-20260626.json"),
            "C-006": ("PHASE_S2PMT06_OWNER_UX.md", "ADP-S2PMT06-OWNER-UX-20260626.json"),
            "C-007": ("PHASE_S2PMT06_OWNER_UX.md", "ADP-S2PMT06-OWNER-UX-20260626.json"),
            "C-010": ("并行审查汇总与合并结论.md", "问题清单.csv"),
            "C-011": (
                "PHASE_S2PHT01V1_1_T01_EMAIL_PATH_AUDIT.md",
                "PHASE_S2PHT01V1_1_T02_T04_EMAIL_V1_RENDERER.md",
                "PHASE_S2PMT06_OWNER_UX.md",
                "并行审查汇总与合并结论.md",
                "问题清单.csv",
            ),
            "C-012": ("PHASE_S2PMT06_OWNER_UX.md", "ADP-S2PMT06-OWNER-UX-20260626.json"),
        }

        findings = {finding["finding_id"]: finding for finding in manifest["p1_findings"]}
        self.assertEqual(manifest["refreshed_findings"], list(expected_current_refs))
        self.assertEqual(
            manifest["refresh_manifest"],
            "governance/run_manifests/ADP-S2PMT07-P1-C002-TECHNICAL-REVIEW-20260628.json",
        )
        self.assertEqual(
            manifest["previous_refresh_manifest"],
            "governance/run_manifests/ADP-S2PMT07-P1-C001-C003-C005-C006-C007-C010-C011-C012-TECHNICAL-REVIEW-20260627.json",
        )
        self.assertIn(
            "governance/run_manifests/ADP-S2PMT07-P1-REVIEW-RECEIPT-REFRESH-20260627.json",
            manifest["refresh_manifests"],
        )
        self.assertIn(manifest["refresh_manifest"], manifest["refresh_manifests"])
        self.assertTrue(refresh_manifest_path.exists())
        self.assertTrue(a006_a009_review_manifest_path.exists())
        self.assertTrue(a006_a009_review_phase_path.exists())
        self.assertTrue(a010_a016_review_manifest_path.exists())
        self.assertTrue(a010_a016_review_phase_path.exists())
        self.assertTrue(a017_a019_review_manifest_path.exists())
        self.assertTrue(a017_a019_review_phase_path.exists())
        self.assertTrue(a018_a021_review_manifest_path.exists())
        self.assertTrue(a018_a021_review_phase_path.exists())
        self.assertTrue(b002_b004_b005_b015_review_manifest_path.exists())
        self.assertTrue(b002_b004_b005_b015_review_phase_path.exists())
        self.assertTrue(b003_b011_review_manifest_path.exists())
        self.assertTrue(b003_b011_review_phase_path.exists())
        self.assertTrue(b006_b009_b010_b012_b013_b014_review_manifest_path.exists())
        self.assertTrue(b006_b009_b010_b012_b013_b014_review_phase_path.exists())
        self.assertTrue(a020_sbom_ci_manifest_path.exists())
        self.assertTrue(a020_review_manifest_path.exists())
        self.assertTrue(a020_review_phase_path.exists())
        self.assertTrue(c_group_review_manifest_path.exists())
        self.assertTrue(c_group_review_phase_path.exists())
        self.assertTrue(c002_status_states_manifest_path.exists())
        self.assertTrue(c002_review_manifest_path.exists())
        self.assertTrue(c002_review_phase_path.exists())
        self.assertEqual(
            set(manifest["p1_technical_review_candidate_findings"]),
            {
                "A-006",
                "A-007",
                "A-008",
                "A-009",
                "A-010",
                "A-011",
                "A-012",
                "A-013",
                "A-014",
                "A-015",
                "A-016",
                "A-017",
                "A-018",
                "A-019",
                "A-020",
                "A-021",
                "B-002",
                "B-003",
                "B-004",
                "B-005",
                "B-006",
                "B-009",
                "B-010",
                "B-011",
                "B-012",
                "B-013",
                "B-014",
                "B-015",
                "C-001",
                "C-002",
                "C-003",
                "C-005",
                "C-006",
                "C-007",
                "C-010",
                "C-011",
                "C-012",
            },
        )
        self.assertEqual(
            manifest["p1_latest_technical_review_candidate_findings"],
            ["C-002"],
        )
        self.assertEqual(
            manifest["p1_technical_review_candidate_manifest"],
            "governance/run_manifests/ADP-S2PMT07-P1-C002-TECHNICAL-REVIEW-20260628.json",
        )
        self.assertIn(
            "governance/run_manifests/ADP-S2PMT07-P1-A006-A009-TECHNICAL-REVIEW-20260627.json",
            manifest["p1_technical_review_candidate_manifests"],
        )
        self.assertIn(
            "governance/run_manifests/ADP-S2PMT07-P1-A010-A016-TECHNICAL-REVIEW-20260627.json",
            manifest["p1_technical_review_candidate_manifests"],
        )
        self.assertIn(
            "governance/run_manifests/ADP-S2PMT07-P1-A017-A019-TECHNICAL-REVIEW-20260627.json",
            manifest["p1_technical_review_candidate_manifests"],
        )
        self.assertIn(
            "governance/run_manifests/ADP-S2PMT07-P1-A018-A021-TECHNICAL-REVIEW-20260627.json",
            manifest["p1_technical_review_candidate_manifests"],
        )
        self.assertIn(
            "governance/run_manifests/ADP-S2PMT07-P1-B002-B004-B005-B015-TECHNICAL-REVIEW-20260627.json",
            manifest["p1_technical_review_candidate_manifests"],
        )
        self.assertIn(
            "governance/run_manifests/ADP-S2PMT07-P1-B003-B011-TECHNICAL-REVIEW-20260627.json",
            manifest["p1_technical_review_candidate_manifests"],
        )
        self.assertIn(
            "governance/run_manifests/ADP-S2PMT07-P1-B006-B009-B010-B012-B013-B014-TECHNICAL-REVIEW-20260627.json",
            manifest["p1_technical_review_candidate_manifests"],
        )
        self.assertIn(
            "governance/run_manifests/ADP-S2PMT07-P1-A020-TECHNICAL-REVIEW-20260627.json",
            manifest["p1_technical_review_candidate_manifests"],
        )
        self.assertIn(
            "governance/run_manifests/ADP-S2PMT07-P1-C001-C003-C005-C006-C007-C010-C011-C012-TECHNICAL-REVIEW-20260627.json",
            manifest["p1_technical_review_candidate_manifests"],
        )
        self.assertIn(
            "governance/run_manifests/ADP-S2PMT07-P1-C002-TECHNICAL-REVIEW-20260628.json",
            manifest["p1_technical_review_candidate_manifests"],
        )
        self.assertFalse(manifest["p1_closure_claimed"])
        self.assertFalse(manifest["independent_review_signoff_present"])
        self.assertFalse(manifest["stage2_integrated_production_accepted"])
        self.assertEqual(manifest["inherited_v7_1_open_p0_findings_after"], 8)
        self.assertEqual(manifest["inherited_v7_1_open_p1_findings_after"], 37)

        for finding_id, refs in expected_current_refs.items():
            row = receipt_rows[finding_id]
            finding_refs = "\n".join(findings[finding_id]["evidence_refs"])
            for ref in refs:
                self.assertIn(ref, row)
                self.assertIn(ref, finding_refs)
            for stale_ref in stale_refs[finding_id]:
                self.assertNotIn(stale_ref, row)
                self.assertNotIn(stale_ref, finding_refs)
            if finding_id in {
                "A-006",
                "A-007",
                "A-008",
                "A-009",
                "A-010",
                "A-011",
                "A-012",
                "A-013",
                "A-014",
                "A-015",
                "A-016",
                "A-017",
                "A-018",
                "A-019",
                "A-020",
                "A-021",
                "B-002",
                "B-003",
                "B-004",
                "B-005",
                "B-006",
                "B-009",
                "B-010",
                "B-011",
                "B-012",
                "B-013",
                "B-014",
                "B-015",
                "C-001",
                "C-002",
                "C-003",
                "C-005",
                "C-006",
                "C-007",
                "C-010",
                "C-011",
                "C-012",
            }:
                self.assertEqual(
                    findings[finding_id]["technical_review_verdict"],
                    "PASS_WITH_NO_PRODUCTION_ACCEPTANCE",
                )
                expected_receipt = (
                    "governance/run_manifests/ADP-S2PMT07-P1-A020-TECHNICAL-REVIEW-20260627.json"
                    if finding_id == "A-020"
                    else (
                        "governance/run_manifests/ADP-S2PMT07-P1-A006-A009-TECHNICAL-REVIEW-20260627.json"
                        if finding_id in {"A-006", "A-007", "A-008", "A-009"}
                        else (
                            "governance/run_manifests/ADP-S2PMT07-P1-A010-A016-TECHNICAL-REVIEW-20260627.json"
                            if finding_id in {"A-010", "A-011", "A-012", "A-013", "A-014", "A-015", "A-016"}
                            else (
                                "governance/run_manifests/ADP-S2PMT07-P1-A017-A019-TECHNICAL-REVIEW-20260627.json"
                                if finding_id in {"A-017", "A-019"}
                                else (
                                    "governance/run_manifests/ADP-S2PMT07-P1-A018-A021-TECHNICAL-REVIEW-20260627.json"
                                    if finding_id in {"A-018", "A-021"}
                                    else (
                                        "governance/run_manifests/ADP-S2PMT07-P1-B003-B011-TECHNICAL-REVIEW-20260627.json"
                                        if finding_id in {"B-003", "B-011"}
                                        else (
                                            "governance/run_manifests/ADP-S2PMT07-P1-B006-B009-B010-B012-B013-B014-TECHNICAL-REVIEW-20260627.json"
                                        if finding_id in {"B-006", "B-009", "B-010", "B-012", "B-013", "B-014"}
                                            else (
                                                "governance/run_manifests/ADP-S2PMT07-P1-C002-TECHNICAL-REVIEW-20260628.json"
                                                if finding_id == "C-002"
                                                else (
                                                    "governance/run_manifests/ADP-S2PMT07-P1-C001-C003-C005-C006-C007-C010-C011-C012-TECHNICAL-REVIEW-20260627.json"
                                                    if finding_id
                                                    in {
                                                        "C-001",
                                                        "C-003",
                                                        "C-005",
                                                        "C-006",
                                                        "C-007",
                                                        "C-010",
                                                        "C-011",
                                                        "C-012",
                                                    }
                                                    else "governance/run_manifests/ADP-S2PMT07-P1-B002-B004-B005-B015-TECHNICAL-REVIEW-20260627.json"
                                                )
                                            )
                                        )
                                    )
                                )
                            )
                        )
                    )
                )
                self.assertEqual(
                    findings[finding_id]["finding_level_technical_review_receipt"],
                    expected_receipt,
                )
                self.assertTrue(findings[finding_id]["technical_closure_candidate"])
                self.assertIn("finding_level_technical_review_passed", findings[finding_id]["preliminary_review_state"])
            elif finding_id == "A-020":
                self.assertNotIn("technical_review_verdict", findings[finding_id])
                self.assertNotIn("finding_level_technical_review_receipt", findings[finding_id])
                self.assertIn("sufficiency_gap", findings[finding_id]["preliminary_review_state"])
                self.assertIn("SBOM", findings[finding_id]["reviewer_decision_required"])
                self.assertIn("CI enforcement", findings[finding_id]["reviewer_decision_required"])
            else:
                self.assertIn("refreshed_current_evidence_located", findings[finding_id]["preliminary_review_state"])

        a006_a009_review = json.loads(a006_a009_review_manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(
            a006_a009_review["status"],
            "finding_level_technical_review_passed_no_p1_closure_no_production",
        )
        self.assertEqual(a006_a009_review["finding_ids"], ["A-006", "A-007", "A-008", "A-009"])
        self.assertFalse(a006_a009_review["reviewer_independence_for_final_gate_claimed"])
        self.assertTrue(a006_a009_review["technical_review_checks"]["all_four_findings_present"])
        self.assertTrue(a006_a009_review["technical_review_checks"]["all_evidence_files_exist"])
        self.assertTrue(a006_a009_review["technical_review_checks"]["all_technical_review_verdicts_pass_no_production"])
        self.assertFalse(a006_a009_review["technical_review_checks"]["independent_final_signoff_present"])
        self.assertEqual(a006_a009_review["inherited_v7_1_open_p0_findings_after"], 8)
        self.assertEqual(a006_a009_review["inherited_v7_1_open_p1_findings_after"], 37)
        self.assertFalse(a006_a009_review["p1_closure_claimed"])
        self.assertFalse(a006_a009_review["s2pmt07_final_pass_claimed"])
        self.assertFalse(a006_a009_review["stage2_integrated_production_accepted"])
        self.assertFalse(a006_a009_review["real_smtp_sent"])
        self.assertFalse(a006_a009_review["scheduler_install_enabled"])
        self.assertFalse(a006_a009_review["release_packaging_enabled"])
        self.assertFalse(a006_a009_review["production_restore_enabled"])
        self.assertFalse(a006_a009_review["current_pointer_changed"])
        self.assertFalse(a006_a009_review["v7_1_baseline_changed"])
        self.assertFalse(a006_a009_review["v7_2_contract_files_changed"])
        reviewed = {finding["finding_id"]: finding for finding in a006_a009_review["reviewed_findings"]}
        self.assertEqual(set(reviewed), {"A-006", "A-007", "A-008", "A-009"})
        for finding in reviewed.values():
            self.assertEqual(finding["technical_review_verdict"], "PASS_WITH_NO_PRODUCTION_ACCEPTANCE")
            self.assertTrue(finding["technical_closure_candidate"])
            self.assertTrue(finding["independent_final_closure_decision_required"])
        self.assertIn("A-006", a006_a009_review_phase_path.read_text(encoding="utf-8"))

        a010_a016_review = json.loads(a010_a016_review_manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(
            a010_a016_review["status"],
            "finding_level_technical_review_passed_no_p1_closure_no_production",
        )
        self.assertEqual(
            a010_a016_review["finding_ids"],
            ["A-010", "A-011", "A-012", "A-013", "A-014", "A-015", "A-016"],
        )
        self.assertFalse(a010_a016_review["reviewer_independence_for_final_gate_claimed"])
        self.assertTrue(a010_a016_review["technical_review_checks"]["all_seven_findings_present"])
        self.assertTrue(a010_a016_review["technical_review_checks"]["all_evidence_files_exist"])
        self.assertTrue(a010_a016_review["technical_review_checks"]["all_technical_review_verdicts_pass_no_production"])
        self.assertFalse(a010_a016_review["technical_review_checks"]["independent_final_signoff_present"])
        self.assertEqual(a010_a016_review["inherited_v7_1_open_p0_findings_after"], 8)
        self.assertEqual(a010_a016_review["inherited_v7_1_open_p1_findings_after"], 37)
        self.assertFalse(a010_a016_review["p1_closure_claimed"])
        self.assertFalse(a010_a016_review["s2pmt07_final_pass_claimed"])
        self.assertFalse(a010_a016_review["stage2_integrated_production_accepted"])
        self.assertFalse(a010_a016_review["real_smtp_sent"])
        self.assertFalse(a010_a016_review["scheduler_install_enabled"])
        self.assertFalse(a010_a016_review["release_packaging_enabled"])
        self.assertFalse(a010_a016_review["production_restore_enabled"])
        self.assertFalse(a010_a016_review["current_pointer_changed"])
        self.assertFalse(a010_a016_review["v7_1_baseline_changed"])
        self.assertFalse(a010_a016_review["v7_2_contract_files_changed"])
        reviewed = {finding["finding_id"]: finding for finding in a010_a016_review["reviewed_findings"]}
        self.assertEqual(set(reviewed), {"A-010", "A-011", "A-012", "A-013", "A-014", "A-015", "A-016"})
        for finding in reviewed.values():
            self.assertEqual(finding["technical_review_verdict"], "PASS_WITH_NO_PRODUCTION_ACCEPTANCE")
            self.assertTrue(finding["technical_closure_candidate"])
            self.assertTrue(finding["independent_final_closure_decision_required"])
        self.assertIn("A-010", a010_a016_review_phase_path.read_text(encoding="utf-8"))

        a017_a019_review = json.loads(a017_a019_review_manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(
            a017_a019_review["status"],
            "finding_level_technical_review_passed_no_p1_closure_no_production",
        )
        self.assertEqual(a017_a019_review["finding_ids"], ["A-017", "A-019"])
        self.assertFalse(a017_a019_review["reviewer_independence_for_final_gate_claimed"])
        self.assertTrue(a017_a019_review["technical_review_checks"]["all_two_reviewed_findings_present"])
        self.assertTrue(a017_a019_review["technical_review_checks"]["a018_explicitly_excluded_as_sufficiency_gap"])
        self.assertTrue(a017_a019_review["technical_review_checks"]["all_evidence_files_exist"])
        self.assertTrue(a017_a019_review["technical_review_checks"]["all_technical_review_verdicts_pass_no_production"])
        self.assertFalse(a017_a019_review["technical_review_checks"]["independent_final_signoff_present"])
        self.assertEqual(a017_a019_review["excluded_findings"][0]["finding_id"], "A-018")
        self.assertIn("sufficiency_gap", a017_a019_review["excluded_findings"][0]["reason"])
        self.assertEqual(a017_a019_review["inherited_v7_1_open_p0_findings_after"], 8)
        self.assertEqual(a017_a019_review["inherited_v7_1_open_p1_findings_after"], 37)
        self.assertFalse(a017_a019_review["p1_closure_claimed"])
        self.assertFalse(a017_a019_review["s2pmt07_final_pass_claimed"])
        self.assertFalse(a017_a019_review["stage2_integrated_production_accepted"])
        self.assertFalse(a017_a019_review["real_smtp_sent"])
        self.assertFalse(a017_a019_review["scheduler_install_enabled"])
        self.assertFalse(a017_a019_review["release_packaging_enabled"])
        self.assertFalse(a017_a019_review["production_restore_enabled"])
        self.assertFalse(a017_a019_review["current_pointer_changed"])
        self.assertFalse(a017_a019_review["v7_1_baseline_changed"])
        self.assertFalse(a017_a019_review["v7_2_contract_files_changed"])
        reviewed = {finding["finding_id"]: finding for finding in a017_a019_review["reviewed_findings"]}
        self.assertEqual(set(reviewed), {"A-017", "A-019"})
        for finding in reviewed.values():
            self.assertEqual(finding["technical_review_verdict"], "PASS_WITH_NO_PRODUCTION_ACCEPTANCE")
            self.assertTrue(finding["technical_closure_candidate"])
            self.assertTrue(finding["independent_final_closure_decision_required"])
        self.assertIn("A-017", a017_a019_review_phase_path.read_text(encoding="utf-8"))

        a018_a021_review = json.loads(a018_a021_review_manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(
            a018_a021_review["status"],
            "finding_level_technical_review_passed_no_p1_closure_no_production",
        )
        self.assertEqual(a018_a021_review["finding_ids"], ["A-018", "A-021"])
        self.assertFalse(a018_a021_review["reviewer_independence_for_final_gate_claimed"])
        self.assertTrue(a018_a021_review["technical_review_checks"]["all_two_reviewed_findings_present"])
        self.assertTrue(a018_a021_review["technical_review_checks"]["a020_explicitly_excluded_as_supply_chain_sufficiency_gap"])
        self.assertTrue(a018_a021_review["technical_review_checks"]["all_evidence_files_exist"])
        self.assertTrue(a018_a021_review["technical_review_checks"]["all_technical_review_verdicts_pass_no_production"])
        self.assertFalse(a018_a021_review["technical_review_checks"]["independent_final_signoff_present"])
        self.assertEqual(a018_a021_review["excluded_findings"][0]["finding_id"], "A-020")
        self.assertIn("SBOM", a018_a021_review["excluded_findings"][0]["reason"])
        self.assertIn("CI enforcement", a018_a021_review["excluded_findings"][0]["reason"])
        self.assertEqual(a018_a021_review["inherited_v7_1_open_p0_findings_after"], 8)
        self.assertEqual(a018_a021_review["inherited_v7_1_open_p1_findings_after"], 37)
        self.assertFalse(a018_a021_review["p1_closure_claimed"])
        self.assertFalse(a018_a021_review["s2pmt07_final_pass_claimed"])
        self.assertFalse(a018_a021_review["stage2_integrated_production_accepted"])
        self.assertFalse(a018_a021_review["real_smtp_sent"])
        self.assertFalse(a018_a021_review["scheduler_install_enabled"])
        self.assertFalse(a018_a021_review["release_packaging_enabled"])
        self.assertFalse(a018_a021_review["production_restore_enabled"])
        self.assertFalse(a018_a021_review["current_pointer_changed"])
        self.assertFalse(a018_a021_review["v7_1_baseline_changed"])
        self.assertFalse(a018_a021_review["v7_2_contract_files_changed"])
        reviewed = {finding["finding_id"]: finding for finding in a018_a021_review["reviewed_findings"]}
        self.assertEqual(set(reviewed), {"A-018", "A-021"})
        for finding in reviewed.values():
            self.assertEqual(finding["technical_review_verdict"], "PASS_WITH_NO_PRODUCTION_ACCEPTANCE")
            self.assertTrue(finding["technical_closure_candidate"])
            self.assertTrue(finding["independent_final_closure_decision_required"])
        a018_a021_phase = a018_a021_review_phase_path.read_text(encoding="utf-8")
        self.assertIn("A-018", a018_a021_phase)
        self.assertIn("A-020", a018_a021_phase)

        b002_b004_b005_b015_review = json.loads(
            b002_b004_b005_b015_review_manifest_path.read_text(encoding="utf-8")
        )
        self.assertEqual(
            b002_b004_b005_b015_review["status"],
            "finding_level_technical_review_passed_no_p1_closure_no_production",
        )
        self.assertEqual(b002_b004_b005_b015_review["finding_ids"], ["B-002", "B-004", "B-005", "B-015"])
        self.assertFalse(b002_b004_b005_b015_review["reviewer_independence_for_final_gate_claimed"])
        self.assertTrue(b002_b004_b005_b015_review["technical_review_checks"]["all_four_reviewed_findings_present"])
        self.assertTrue(b002_b004_b005_b015_review["technical_review_checks"]["all_evidence_files_exist"])
        self.assertTrue(
            b002_b004_b005_b015_review["technical_review_checks"][
                "all_technical_review_verdicts_pass_no_production"
            ]
        )
        self.assertTrue(
            b002_b004_b005_b015_review["technical_review_checks"][
                "lifecycle_cache_tests_cover_positive_and_negative_paths"
            ]
        )
        self.assertFalse(b002_b004_b005_b015_review["technical_review_checks"]["independent_final_signoff_present"])
        self.assertEqual(b002_b004_b005_b015_review["inherited_v7_1_open_p0_findings_after"], 8)
        self.assertEqual(b002_b004_b005_b015_review["inherited_v7_1_open_p1_findings_after"], 37)
        self.assertFalse(b002_b004_b005_b015_review["p1_closure_claimed"])
        self.assertFalse(b002_b004_b005_b015_review["s2pmt07_final_pass_claimed"])
        self.assertFalse(b002_b004_b005_b015_review["stage2_integrated_production_accepted"])
        self.assertFalse(b002_b004_b005_b015_review["real_smtp_sent"])
        self.assertFalse(b002_b004_b005_b015_review["scheduler_install_enabled"])
        self.assertFalse(b002_b004_b005_b015_review["release_packaging_enabled"])
        self.assertFalse(b002_b004_b005_b015_review["production_restore_enabled"])
        self.assertFalse(b002_b004_b005_b015_review["current_pointer_changed"])
        self.assertFalse(b002_b004_b005_b015_review["v7_1_baseline_changed"])
        self.assertFalse(b002_b004_b005_b015_review["v7_2_contract_files_changed"])
        reviewed = {finding["finding_id"]: finding for finding in b002_b004_b005_b015_review["reviewed_findings"]}
        self.assertEqual(set(reviewed), {"B-002", "B-004", "B-005", "B-015"})
        for finding in reviewed.values():
            self.assertEqual(finding["technical_review_verdict"], "PASS_WITH_NO_PRODUCTION_ACCEPTANCE")
            self.assertTrue(finding["technical_closure_candidate"])
            self.assertTrue(finding["independent_final_closure_decision_required"])
        b002_b004_b005_b015_phase = b002_b004_b005_b015_review_phase_path.read_text(encoding="utf-8")
        self.assertIn("B-002", b002_b004_b005_b015_phase)
        self.assertIn("B-015", b002_b004_b005_b015_phase)

        b003_b011_review = json.loads(b003_b011_review_manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(
            b003_b011_review["status"],
            "finding_level_technical_review_passed_no_p1_closure_no_production",
        )
        self.assertEqual(b003_b011_review["finding_ids"], ["B-003", "B-011"])
        self.assertFalse(b003_b011_review["reviewer_independence_for_final_gate_claimed"])
        self.assertTrue(b003_b011_review["technical_review_checks"]["all_two_reviewed_findings_present"])
        self.assertTrue(b003_b011_review["technical_review_checks"]["all_evidence_files_exist"])
        self.assertTrue(
            b003_b011_review["technical_review_checks"][
                "all_technical_review_verdicts_pass_no_production"
            ]
        )
        self.assertTrue(
            b003_b011_review["technical_review_checks"][
                "lease_fencing_tests_cover_watchdog_and_m4_watermark_positive_negative_paths"
            ]
        )
        self.assertFalse(b003_b011_review["technical_review_checks"]["independent_final_signoff_present"])
        self.assertEqual(b003_b011_review["inherited_v7_1_open_p0_findings_after"], 8)
        self.assertEqual(b003_b011_review["inherited_v7_1_open_p1_findings_after"], 37)
        self.assertFalse(b003_b011_review["p1_closure_claimed"])
        self.assertFalse(b003_b011_review["s2pmt07_final_pass_claimed"])
        self.assertFalse(b003_b011_review["stage2_integrated_production_accepted"])
        self.assertFalse(b003_b011_review["real_smtp_sent"])
        self.assertFalse(b003_b011_review["scheduler_install_enabled"])
        self.assertFalse(b003_b011_review["release_packaging_enabled"])
        self.assertFalse(b003_b011_review["production_restore_enabled"])
        self.assertFalse(b003_b011_review["current_pointer_changed"])
        self.assertFalse(b003_b011_review["v7_1_baseline_changed"])
        self.assertFalse(b003_b011_review["v7_2_contract_files_changed"])
        reviewed = {finding["finding_id"]: finding for finding in b003_b011_review["reviewed_findings"]}
        self.assertEqual(set(reviewed), {"B-003", "B-011"})
        for finding in reviewed.values():
            self.assertEqual(finding["technical_review_verdict"], "PASS_WITH_NO_PRODUCTION_ACCEPTANCE")
            self.assertTrue(finding["technical_closure_candidate"])
            self.assertTrue(finding["independent_final_closure_decision_required"])
        b003_b011_phase = b003_b011_review_phase_path.read_text(encoding="utf-8")
        self.assertIn("B-003", b003_b011_phase)
        self.assertIn("B-011", b003_b011_phase)

        b006_b009_b010_b012_b013_b014_review = json.loads(
            b006_b009_b010_b012_b013_b014_review_manifest_path.read_text(encoding="utf-8")
        )
        self.assertEqual(
            b006_b009_b010_b012_b013_b014_review["status"],
            "finding_level_technical_review_passed_no_p1_closure_no_production",
        )
        self.assertEqual(
            b006_b009_b010_b012_b013_b014_review["finding_ids"],
            ["B-006", "B-009", "B-010", "B-012", "B-013", "B-014"],
        )
        self.assertFalse(b006_b009_b010_b012_b013_b014_review["reviewer_independence_for_final_gate_claimed"])
        self.assertTrue(
            b006_b009_b010_b012_b013_b014_review["technical_review_checks"][
                "all_six_reviewed_findings_present"
            ]
        )
        self.assertTrue(b006_b009_b010_b012_b013_b014_review["technical_review_checks"]["all_evidence_files_exist"])
        self.assertTrue(
            b006_b009_b010_b012_b013_b014_review["technical_review_checks"][
                "all_technical_review_verdicts_pass_no_production"
            ]
        )
        self.assertTrue(
            b006_b009_b010_b012_b013_b014_review["technical_review_checks"][
                "stress_e2e_tests_cover_capacity_fault_time_e2e_result_validity_backpressure"
            ]
        )
        self.assertFalse(
            b006_b009_b010_b012_b013_b014_review["technical_review_checks"][
                "independent_final_signoff_present"
            ]
        )
        self.assertEqual(b006_b009_b010_b012_b013_b014_review["inherited_v7_1_open_p0_findings_after"], 8)
        self.assertEqual(b006_b009_b010_b012_b013_b014_review["inherited_v7_1_open_p1_findings_after"], 37)
        self.assertFalse(b006_b009_b010_b012_b013_b014_review["p1_closure_claimed"])
        self.assertFalse(b006_b009_b010_b012_b013_b014_review["s2pmt07_final_pass_claimed"])
        self.assertFalse(b006_b009_b010_b012_b013_b014_review["stage2_integrated_production_accepted"])
        self.assertFalse(b006_b009_b010_b012_b013_b014_review["real_smtp_sent"])
        self.assertFalse(b006_b009_b010_b012_b013_b014_review["scheduler_install_enabled"])
        self.assertFalse(b006_b009_b010_b012_b013_b014_review["release_packaging_enabled"])
        self.assertFalse(b006_b009_b010_b012_b013_b014_review["production_restore_enabled"])
        self.assertFalse(b006_b009_b010_b012_b013_b014_review["current_pointer_changed"])
        self.assertFalse(b006_b009_b010_b012_b013_b014_review["v7_1_baseline_changed"])
        self.assertFalse(b006_b009_b010_b012_b013_b014_review["v7_2_contract_files_changed"])
        reviewed = {finding["finding_id"]: finding for finding in b006_b009_b010_b012_b013_b014_review["reviewed_findings"]}
        self.assertEqual(set(reviewed), {"B-006", "B-009", "B-010", "B-012", "B-013", "B-014"})
        for finding in reviewed.values():
            self.assertEqual(finding["technical_review_verdict"], "PASS_WITH_NO_PRODUCTION_ACCEPTANCE")
            self.assertTrue(finding["technical_closure_candidate"])
            self.assertTrue(finding["independent_final_closure_decision_required"])
        b006_b009_b010_b012_b013_b014_phase = b006_b009_b010_b012_b013_b014_review_phase_path.read_text(
            encoding="utf-8"
        )
        self.assertIn("B-006", b006_b009_b010_b012_b013_b014_phase)
        self.assertIn("B-014", b006_b009_b010_b012_b013_b014_phase)

        a020_sbom_ci = json.loads(a020_sbom_ci_manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(a020_sbom_ci["status"], "completed_local_validation_no_production")
        self.assertEqual(a020_sbom_ci["finding_id"], "A-020")
        self.assertFalse(a020_sbom_ci["production_side_effects"])
        self.assertTrue(a020_sbom_ci["supply_chain_gate"]["dependency_sbom"]["status"] == "pass")
        self.assertEqual(a020_sbom_ci["supply_chain_gate"]["dependency_sbom"]["runtime_dependency_count"], 0)
        self.assertGreaterEqual(a020_sbom_ci["supply_chain_gate"]["dependency_sbom"]["build_dependency_count"], 1)
        self.assertEqual(a020_sbom_ci["supply_chain_gate"]["ci_enforcement_gate"]["status"], "pass")
        self.assertEqual(
            a020_sbom_ci["supply_chain_gate"]["ci_enforcement_gate"]["required_test"],
            "arxiv-daily-push/tests/test_security_boundary.py",
        )
        self.assertFalse(a020_sbom_ci["real_smtp_enabled"])
        self.assertFalse(a020_sbom_ci["scheduler_enabled"])
        self.assertFalse(a020_sbom_ci["stage2_integrated_production_accepted"])

        a020_review = json.loads(a020_review_manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(
            a020_review["status"],
            "finding_level_technical_review_passed_no_p1_closure_no_production",
        )
        self.assertEqual(a020_review["finding_ids"], ["A-020"])
        self.assertFalse(a020_review["reviewer_independence_for_final_gate_claimed"])
        self.assertTrue(a020_review["technical_review_checks"]["sbom_generated"])
        self.assertTrue(a020_review["technical_review_checks"]["ci_enforcement_present"])
        self.assertTrue(a020_review["technical_review_checks"]["vulnerability_gate_fail_closed"])
        self.assertTrue(a020_review["technical_review_checks"]["action_reference_policy_present"])
        self.assertTrue(a020_review["technical_review_checks"]["all_evidence_files_exist"])
        self.assertFalse(a020_review["technical_review_checks"]["independent_final_signoff_present"])
        self.assertEqual(a020_review["inherited_v7_1_open_p0_findings_after"], 8)
        self.assertEqual(a020_review["inherited_v7_1_open_p1_findings_after"], 37)
        self.assertFalse(a020_review["p1_closure_claimed"])
        self.assertFalse(a020_review["s2pmt07_final_pass_claimed"])
        self.assertFalse(a020_review["stage2_integrated_production_accepted"])
        self.assertFalse(a020_review["real_smtp_sent"])
        self.assertFalse(a020_review["scheduler_install_enabled"])
        self.assertFalse(a020_review["release_packaging_enabled"])
        self.assertFalse(a020_review["production_restore_enabled"])
        self.assertFalse(a020_review["current_pointer_changed"])
        self.assertFalse(a020_review["v7_1_baseline_changed"])
        self.assertFalse(a020_review["v7_2_contract_files_changed"])
        reviewed = {finding["finding_id"]: finding for finding in a020_review["reviewed_findings"]}
        self.assertEqual(set(reviewed), {"A-020"})
        self.assertEqual(reviewed["A-020"]["technical_review_verdict"], "PASS_WITH_NO_PRODUCTION_ACCEPTANCE")
        self.assertTrue(reviewed["A-020"]["technical_closure_candidate"])
        self.assertTrue(reviewed["A-020"]["independent_final_closure_decision_required"])
        a020_phase = a020_review_phase_path.read_text(encoding="utf-8")
        self.assertIn("A-020", a020_phase)
        self.assertIn("SBOM", a020_phase)
        self.assertIn("CI", a020_phase)

        c_group_review = json.loads(c_group_review_manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(
            c_group_review["status"],
            "finding_level_technical_review_passed_no_p1_closure_no_production",
        )
        self.assertEqual(
            c_group_review["finding_ids"],
            ["C-001", "C-003", "C-005", "C-006", "C-007", "C-010", "C-011", "C-012"],
        )
        self.assertIn("C-002", c_group_review["excluded_findings"])
        self.assertFalse(c_group_review["reviewer_independence_for_final_gate_claimed"])
        self.assertTrue(c_group_review["technical_review_checks"]["all_eight_reviewed_findings_present"])
        self.assertTrue(c_group_review["technical_review_checks"]["all_evidence_files_exist"])
        self.assertTrue(c_group_review["technical_review_checks"]["all_technical_review_verdicts_pass_no_production"])
        self.assertTrue(c_group_review["technical_review_checks"]["c002_explicitly_excluded_as_status_state_gap"])
        self.assertFalse(c_group_review["technical_review_checks"]["independent_final_signoff_present"])
        self.assertEqual(c_group_review["inherited_v7_1_open_p0_findings_after"], 8)
        self.assertEqual(c_group_review["inherited_v7_1_open_p1_findings_after"], 37)
        self.assertFalse(c_group_review["p1_closure_claimed"])
        self.assertFalse(c_group_review["s2pmt07_final_pass_claimed"])
        self.assertFalse(c_group_review["stage2_integrated_production_accepted"])
        self.assertFalse(c_group_review["real_smtp_sent"])
        self.assertFalse(c_group_review["scheduler_install_enabled"])
        self.assertFalse(c_group_review["release_packaging_enabled"])
        self.assertFalse(c_group_review["production_restore_enabled"])
        self.assertFalse(c_group_review["current_pointer_changed"])
        self.assertFalse(c_group_review["v7_1_baseline_changed"])
        self.assertFalse(c_group_review["v7_2_contract_files_changed"])
        reviewed = {finding["finding_id"]: finding for finding in c_group_review["reviewed_findings"]}
        self.assertEqual(set(reviewed), {"C-001", "C-003", "C-005", "C-006", "C-007", "C-010", "C-011", "C-012"})
        for finding in reviewed.values():
            self.assertEqual(finding["technical_review_verdict"], "PASS_WITH_NO_PRODUCTION_ACCEPTANCE")
            self.assertTrue(finding["technical_closure_candidate"])
            self.assertTrue(finding["independent_final_closure_decision_required"])
        c_group_phase = c_group_review_phase_path.read_text(encoding="utf-8")
        self.assertIn("C-001", c_group_phase)
        self.assertIn("C-012", c_group_phase)
        self.assertIn("C-002 excluded", c_group_phase)

        c002_states = json.loads(c002_status_states_manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(c002_states["status"], "completed_local_validation_no_closure_no_production")
        self.assertEqual(
            c002_states["owner_status_summary"]["status_states_observed"],
            ["sent", "blocked_not_sent", "queued_or_pending", "empty", "delayed", "failed"],
        )
        self.assertEqual(c002_states["owner_status_summary"]["status_states_not_proven"], [])
        self.assertFalse(c002_states["p1_closure_claimed"])
        self.assertFalse(c002_states["stage2_integrated_production_accepted"])

        c002_review = json.loads(c002_review_manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(
            c002_review["status"],
            "finding_level_technical_review_passed_no_p1_closure_no_production",
        )
        self.assertEqual(c002_review["finding_ids"], ["C-002"])
        self.assertTrue(c002_review["technical_review_checks"]["empty_delayed_failed_states_required"])
        self.assertTrue(c002_review["technical_review_checks"]["missing_required_state_blocks"])
        self.assertTrue(c002_review["technical_review_checks"]["unproven_required_state_blocks"])
        self.assertFalse(c002_review["technical_review_checks"]["independent_final_signoff_present"])
        self.assertEqual(c002_review["inherited_v7_1_open_p0_findings_after"], 8)
        self.assertEqual(c002_review["inherited_v7_1_open_p1_findings_after"], 37)
        self.assertFalse(c002_review["p1_closure_claimed"])
        self.assertFalse(c002_review["s2pmt07_final_pass_claimed"])
        self.assertFalse(c002_review["stage2_integrated_production_accepted"])
        self.assertFalse(c002_review["real_smtp_sent"])
        self.assertFalse(c002_review["scheduler_install_enabled"])
        self.assertFalse(c002_review["release_packaging_enabled"])
        self.assertFalse(c002_review["production_restore_enabled"])
        self.assertFalse(c002_review["current_pointer_changed"])
        self.assertFalse(c002_review["v7_1_baseline_changed"])
        self.assertFalse(c002_review["v7_2_contract_files_changed"])
        c002_phase = c002_review_phase_path.read_text(encoding="utf-8")
        self.assertIn("C-002", c002_phase)
        self.assertIn("empty", c002_phase)
        self.assertIn("delayed", c002_phase)
        self.assertIn("failed", c002_phase)

    def test_dependency_state_requires_s2plt04_and_records_missing_completion(self) -> None:
        state = build_dependency_state()

        self.assertEqual(state["status"], "blocked")
        self.assertEqual(tuple(state["required_dependencies"]), S2PMT07_REQUIRED_DEPENDENCIES)
        self.assertEqual(state["s2plt04_status"], "missing_authoritative_completion_evidence")
        self.assertIn("S2PLT04", state["missing_dependencies"])
        for task_id in S2PMT07_REQUIRED_DEPENDENCIES[:6]:
            self.assertIn(task_id, state["completed_dependencies"])

    def test_reviewer_independence_does_not_self_certify_final_review(self) -> None:
        state = build_reviewer_independence_state()

        self.assertEqual(state["status"], "blocked")
        self.assertTrue(state["reviewer_involved_in_s2pmt01_t06"])
        self.assertFalse(state["independent_reviewer_proven"])

        independent = build_reviewer_independence_state(reviewer_involved_in_s2pmt01_t06=False)
        self.assertEqual(independent["status"], "pass")

    def test_remaining_blocker_matrix_maps_current_final_gate_blockers_to_required_evidence(self) -> None:
        state = build_s2pmt07_remaining_blocker_matrix_state(generated_at="2026-06-28T14:30:00+10:00")

        self.assertEqual(state["status"], "blocked_matrix_ready_no_closure")
        self.assertEqual(tuple(state["required_blockers"]), S2PMT07_REMAINING_BLOCKER_MATRIX_REQUIRED_BLOCKERS)
        self.assertEqual(set(state["current_blockers"]), set(S2PMT07_BLOCKING_REASONS))
        self.assertFalse(state["p0_closure_claimed"])
        self.assertFalse(state["p1_closure_claimed"])
        self.assertFalse(state["s2pmt07_pass_claimed"])
        self.assertFalse(state["integrated_production_accepted"])
        self.assertFalse(state["daily_operation_enabled"])

        by_reason = {item["blocking_reason"]: item for item in state["blocker_rows"]}
        self.assertEqual(set(by_reason), set(S2PMT07_BLOCKING_REASONS))
        self.assertEqual(
            by_reason["reviewer_independence_not_proven"]["required_evidence"],
            "FINAL_ACCEPTANCE_BUNDLE/independent_final_reviewer_assignment.json",
        )
        self.assertEqual(by_reason["reviewer_independence_not_proven"]["owner_action"], "assign_independent_final_reviewer")
        self.assertTrue(by_reason["reviewer_independence_not_proven"]["external_or_future_evidence_required"])
        self.assertTrue(by_reason["reviewer_independence_not_proven"]["cannot_be_self_certified_by_current_agent"])
        self.assertEqual(
            by_reason["inherited_v7_1_p0_findings_open"]["required_evidence"],
            "FINAL_ACCEPTANCE_BUNDLE/p0_p1_zero_proof.json#independent_closure_decision",
        )
        self.assertEqual(
            by_reason["inherited_v7_1_p1_findings_open"]["required_evidence"],
            "FINAL_ACCEPTANCE_BUNDLE/p0_p1_zero_proof.json#independent_closure_decision",
        )
        self.assertEqual(
            by_reason["s2plt04_not_completed"]["required_evidence"],
            "FINAL_ACCEPTANCE_BUNDLE/s2plt04_completion_report.json",
        )
        self.assertEqual(validate_s2pmt07_remaining_blocker_matrix_state(state), [])

        tampered = dict(state)
        tampered["blocker_rows"] = state["blocker_rows"][:-1]
        self.assertIn(
            "remaining blocker matrix must cover every current S2PMT07 blocking reason",
            validate_s2pmt07_remaining_blocker_matrix_state(tampered),
        )

    def test_evidence_bundle_and_test_gate_are_blocked_until_final_artifacts_exist(self) -> None:
        evidence = build_evidence_bundle_state()
        tests = build_test_gate_state()

        self.assertEqual(evidence["status"], "blocked")
        self.assertEqual(tuple(evidence["required_evidence"]), S2PMT07_REQUIRED_EVIDENCE)
        self.assertEqual(set(evidence["missing_evidence"]), set(S2PMT07_REQUIRED_EVIDENCE))
        self.assertEqual(tests["status"], "blocked")
        self.assertEqual(tuple(tests["required_test_commands"]), S2PMT07_REQUIRED_TEST_COMMANDS)
        self.assertFalse(tests["executed_as_final_reviewer"])

    def test_final_acceptance_bundle_readiness_state_lists_missing_required_items(self) -> None:
        state = build_final_acceptance_bundle_readiness_state()
        expected_missing = set(S2PMT07_FINAL_ACCEPTANCE_BUNDLE_REQUIRED_ITEMS) - {
            "FINAL_ACCEPTANCE_BUNDLE/no_production_side_effects.json"
        }

        self.assertEqual(state["status"], "blocked")
        self.assertEqual(tuple(state["required_items"]), S2PMT07_FINAL_ACCEPTANCE_BUNDLE_REQUIRED_ITEMS)
        self.assertEqual(set(state["missing_items"]), expected_missing)
        self.assertFalse(state["bundle_present"])
        self.assertFalse(state["bundle_claimed_ready"])
        self.assertFalse(state["production_acceptance_claimed"])
        self.assertFalse(state["release_packaging_enabled"])
        for flag in S2PMT07_FINAL_ACCEPTANCE_BUNDLE_FORBIDDEN_FLAGS:
            self.assertFalse(state[flag])
        expected_blockers = set(S2PMT07_FINAL_ACCEPTANCE_BUNDLE_BLOCKING_REASONS) - {
            "final_acceptance_bundle_directory_missing",
            "no_production_side_effect_attestation_missing",
        }
        for reason in expected_blockers:
            self.assertIn(reason, state["blocking_reasons"])
        self.assertNotIn("final_acceptance_bundle_directory_missing", state["blocking_reasons"])
        self.assertNotIn("no_production_side_effect_attestation_missing", state["blocking_reasons"])
        self.assertEqual(validate_final_acceptance_bundle_readiness_state(state), [])

        tampered = dict(state)
        tampered["bundle_claimed_ready"] = True
        self.assertIn(
            "final acceptance bundle readiness must not claim ready while blocked",
            validate_final_acceptance_bundle_readiness_state(tampered),
        )

    def test_final_acceptance_bundle_readiness_embeds_p0_p1_candidates_without_zero_proof(self) -> None:
        state = build_final_acceptance_bundle_readiness_state()
        candidate = state["p0_p1_technical_closure_candidate_state"]

        self.assertEqual(candidate["status"], "blocked_candidate_ready_no_closure")
        self.assertEqual(candidate["p0_candidate_count"], 8)
        self.assertEqual(candidate["p1_candidate_count"], 37)
        self.assertEqual(len(candidate["p0_candidate_findings"]), 8)
        self.assertEqual(len(candidate["p1_candidate_findings"]), 37)
        self.assertTrue(candidate["p0_candidate_package_present"])
        self.assertTrue(candidate["p1_candidate_receipt_present"])
        self.assertTrue(candidate["all_p0_candidate_reviews_passed_no_production_acceptance"])
        self.assertTrue(candidate["all_p1_candidate_reviews_passed_no_production_acceptance"])
        self.assertFalse(candidate["p0_p1_zero_proof_present"])
        self.assertFalse(candidate["independent_final_closure_decision_present"])
        self.assertFalse(candidate["p0_closure_claimed"])
        self.assertFalse(candidate["p1_closure_claimed"])
        self.assertFalse(candidate["closure_claimed"])
        self.assertEqual(candidate["inherited_v7_1_open_p0_findings"], 8)
        self.assertEqual(candidate["inherited_v7_1_open_p1_findings"], 37)
        self.assertIn("p0_p1_zero_proof_missing", candidate["blocking_reasons"])
        self.assertFalse(state["available_items"]["FINAL_ACCEPTANCE_BUNDLE/p0_p1_zero_proof.json"])
        self.assertTrue(state["available_prebundle_evidence"]["P0_P1_TECHNICAL_CLOSURE_CANDIDATES"])
        for ref in candidate["candidate_manifest_refs"]:
            self.assertTrue((REPO_ROOT / ref).exists(), ref)
        self.assertEqual(validate_p0_p1_technical_closure_candidate_state(candidate), [])
        self.assertEqual(validate_final_acceptance_bundle_readiness_state(state), [])

        tampered = json.loads(json.dumps(candidate))
        tampered["p1_closure_claimed"] = True
        self.assertIn("p1_closure_claimed must be false", validate_p0_p1_technical_closure_candidate_state(tampered))

    def test_p0_p1_zero_proof_readiness_fails_closed_until_independent_zero_artifact_exists(self) -> None:
        state = build_p0_p1_zero_proof_readiness_state()

        self.assertEqual(state["status"], "blocked")
        self.assertEqual(state["scope"], "p0_p1_zero_proof_readiness_schema_only_no_closure")
        self.assertFalse(state["zero_proof_artifact_present"])
        self.assertEqual(state["zero_proof_artifact_path"], "FINAL_ACCEPTANCE_BUNDLE/p0_p1_zero_proof.json")
        self.assertEqual(tuple(state["required_zero_severities"]), ("P0", "P1"))
        self.assertEqual(tuple(state["required_fields"]), S2PMT07_P0_P1_ZERO_PROOF_REQUIRED_FIELDS)
        self.assertEqual(state["required_open_p0_findings"], 0)
        self.assertEqual(state["required_open_p1_findings"], 0)
        self.assertEqual(state["observed_open_p0_findings"], 8)
        self.assertEqual(state["observed_open_p1_findings"], 37)
        self.assertFalse(state["independent_final_closure_decision_present"])
        self.assertFalse(state["p0_zero_proven"])
        self.assertFalse(state["p1_zero_proven"])
        self.assertFalse(state["closure_claimed"])
        self.assertIn("p0_p1_zero_proof_artifact_missing", state["blocking_reasons"])
        self.assertIn("independent_final_closure_decision_missing", state["blocking_reasons"])
        self.assertIn("inherited_v7_1_p0_findings_open", state["blocking_reasons"])
        self.assertIn("inherited_v7_1_p1_findings_open", state["blocking_reasons"])
        self.assertEqual(validate_p0_p1_zero_proof_readiness_state(state), [])

        tampered = json.loads(json.dumps(state))
        tampered["observed_open_p0_findings"] = 0
        tampered["p0_zero_proven"] = True
        self.assertIn(
            "P0/P1 zero proof readiness must preserve inherited open P0 count until artifact exists",
            validate_p0_p1_zero_proof_readiness_state(tampered),
        )

    def test_final_acceptance_bundle_readiness_embeds_zero_proof_readiness_not_closure(self) -> None:
        state = build_final_acceptance_bundle_readiness_state()
        assembly = state["p0_p1_zero_proof_assembly"]
        zero_proof = state["p0_p1_zero_proof_readiness"]

        self.assertEqual(assembly["status"], "blocked_candidate_inputs_ready_no_closure")
        self.assertTrue(state["available_prebundle_evidence"]["P0_P1_ZERO_PROOF_ASSEMBLY"])
        self.assertEqual(zero_proof["status"], "blocked")
        self.assertFalse(zero_proof["zero_proof_artifact_present"])
        self.assertFalse(zero_proof["p0_zero_proven"])
        self.assertFalse(zero_proof["p1_zero_proven"])
        self.assertFalse(state["available_prebundle_evidence"]["P0_P1_ZERO_PROOF_READINESS"])
        self.assertIn("p0_p1_zero_proof_artifact_missing", zero_proof["blocking_reasons"])
        self.assertEqual(validate_p0_p1_zero_proof_readiness_state(zero_proof), [])
        self.assertEqual(validate_final_acceptance_bundle_readiness_state(state), [])

    def test_p0_p1_zero_proof_assembly_binds_candidate_inputs_without_closure(self) -> None:
        state = build_p0_p1_zero_proof_assembly_state()

        self.assertEqual(state["status"], "blocked_candidate_inputs_ready_no_closure")
        self.assertEqual(state["scope"], "p0_p1_zero_proof_assembly_only_no_closure")
        self.assertEqual(tuple(state["required_inputs"]), S2PMT07_P0_P1_ZERO_PROOF_ASSEMBLY_REQUIRED_INPUTS)
        self.assertEqual(state["p0_candidate_count"], 8)
        self.assertEqual(state["p1_candidate_count"], 37)
        self.assertEqual(state["candidate_total"], 45)
        self.assertTrue(state["all_candidate_reviews_available"])
        self.assertTrue(state["all_candidate_refs_exist"])
        self.assertEqual(state["next_required_action"], "independent_final_closure_decision")
        self.assertFalse(state["independent_final_closure_decision_present"])
        self.assertFalse(state["zero_proof_artifact_present"])
        self.assertFalse(state["p0_zero_proven"])
        self.assertFalse(state["p1_zero_proven"])
        self.assertFalse(state["closure_claimed"])
        self.assertEqual(state["observed_open_p0_findings"], 8)
        self.assertEqual(state["observed_open_p1_findings"], 37)
        for reason in S2PMT07_P0_P1_ZERO_PROOF_ASSEMBLY_BLOCKING_REASONS:
            self.assertIn(reason, state["blocking_reasons"])
        for flag in S2PMT07_P0_P1_ZERO_PROOF_ASSEMBLY_FORBIDDEN_FLAGS:
            self.assertFalse(state[flag])
        for ref in state["candidate_manifest_refs"]:
            self.assertTrue((REPO_ROOT / ref).exists(), ref)
        self.assertEqual(validate_p0_p1_zero_proof_assembly_state(state), [])

        tampered = json.loads(json.dumps(state))
        tampered["all_candidate_refs_exist"] = False
        self.assertIn(
            "P0/P1 zero proof assembly candidate refs must exist",
            validate_p0_p1_zero_proof_assembly_state(tampered),
        )

        tampered_flag = json.loads(json.dumps(state))
        tampered_flag["real_smtp_sent"] = True
        self.assertIn("real_smtp_sent must be false", validate_p0_p1_zero_proof_assembly_state(tampered_flag))

    def test_independent_final_closure_decision_request_binds_reviewer_inputs_without_closure(self) -> None:
        state = build_independent_final_closure_decision_request_state()

        self.assertEqual(state["status"], "blocked_decision_request_ready_no_closure")
        self.assertEqual(state["scope"], "independent_final_closure_decision_request_only_no_closure")
        self.assertEqual(
            tuple(state["required_inputs"]),
            S2PMT07_INDEPENDENT_FINAL_CLOSURE_DECISION_REQUEST_REQUIRED_INPUTS,
        )
        self.assertEqual(
            state["decision_artifact_ref"],
            "FINAL_ACCEPTANCE_BUNDLE/p0_p1_zero_proof.json#independent_closure_decision",
        )
        self.assertEqual(state["required_reviewer_role"], "independent_final_reviewer")
        self.assertEqual(state["p0_candidate_count"], 8)
        self.assertEqual(state["p1_candidate_count"], 37)
        self.assertEqual(state["candidate_total"], 45)
        self.assertTrue(state["all_candidate_inputs_ready"])
        self.assertTrue(state["all_candidate_refs_exist"])
        self.assertFalse(state["independent_final_closure_decision_present"])
        self.assertFalse(state["zero_proof_artifact_present"])
        self.assertFalse(state["p0_zero_proven"])
        self.assertFalse(state["p1_zero_proven"])
        self.assertFalse(state["closure_claimed"])
        self.assertEqual(state["observed_open_p0_findings"], 8)
        self.assertEqual(state["observed_open_p1_findings"], 37)
        self.assertEqual(
            state["next_required_action"],
            "independent_final_reviewer_must_issue_or_reject_closure_decision",
        )
        for reason in S2PMT07_INDEPENDENT_FINAL_CLOSURE_DECISION_REQUEST_BLOCKING_REASONS:
            self.assertIn(reason, state["blocking_reasons"])
        for flag in S2PMT07_INDEPENDENT_FINAL_CLOSURE_DECISION_REQUEST_FORBIDDEN_FLAGS:
            self.assertFalse(state[flag])
        for ref in state["candidate_manifest_refs"]:
            self.assertTrue((REPO_ROOT / ref).exists(), ref)
        self.assertEqual(validate_independent_final_closure_decision_request_state(state), [])

        readiness = build_final_acceptance_bundle_readiness_state()
        self.assertTrue(readiness["available_prebundle_evidence"]["INDEPENDENT_FINAL_CLOSURE_DECISION_REQUEST"])
        self.assertEqual(
            readiness["independent_final_closure_decision_request"]["status"],
            "blocked_decision_request_ready_no_closure",
        )

        tampered = json.loads(json.dumps(state))
        tampered["independent_final_closure_decision_present"] = True
        self.assertIn(
            "independent_final_closure_decision_present must be false until artifact exists",
            validate_independent_final_closure_decision_request_state(tampered),
        )

        tampered_flag = json.loads(json.dumps(state))
        tampered_flag["real_smtp_sent"] = True
        self.assertIn(
            "real_smtp_sent must be false",
            validate_independent_final_closure_decision_request_state(tampered_flag),
        )

    def test_independent_final_closure_decision_owner_packet_is_ready_but_not_closure(self) -> None:
        packet = build_independent_final_closure_decision_owner_packet_state()

        self.assertEqual(packet["status"], "blocked_owner_action_packet_ready_no_closure")
        self.assertEqual(packet["scope"], "owner_closure_decision_packet_only_no_closure")
        self.assertEqual(packet["task_id"], "S2PMT07")
        self.assertEqual(packet["acceptance_id"], "ACC-S2PMT07-FINAL-REVIEW")
        self.assertEqual(
            tuple(packet["required_owner_actions"]),
            S2PMT07_INDEPENDENT_FINAL_CLOSURE_DECISION_OWNER_PACKET_REQUIRED_ACTIONS,
        )
        self.assertEqual(
            packet["decision_artifact_ref"],
            "FINAL_ACCEPTANCE_BUNDLE/p0_p1_zero_proof.json#independent_closure_decision",
        )
        self.assertEqual(packet["required_reviewer_role"], "independent_final_reviewer")
        self.assertTrue(packet["closure_decision_request_ready"])
        self.assertFalse(packet["assignment_artifact_present"])
        self.assertFalse(packet["independent_final_reviewer_assigned"])
        self.assertFalse(packet["independent_final_closure_decision_present"])
        self.assertFalse(packet["zero_proof_artifact_present"])
        self.assertFalse(packet["p0_zero_proven"])
        self.assertFalse(packet["p1_zero_proven"])
        self.assertFalse(packet["closure_claimed"])
        self.assertEqual(packet["observed_open_p0_findings"], 8)
        self.assertEqual(packet["observed_open_p1_findings"], 37)
        self.assertEqual(
            packet["next_required_action"],
            "owner_or_independent_reviewer_must_record_final_closure_decision_after_assignment",
        )
        for ref in build_independent_final_closure_decision_request_state()["review_input_refs"]:
            self.assertIn(ref, packet["review_input_refs"])
        for reason in S2PMT07_INDEPENDENT_FINAL_CLOSURE_DECISION_OWNER_PACKET_BLOCKING_REASONS:
            self.assertIn(reason, packet["blocking_reasons"])
        for flag in S2PMT07_INDEPENDENT_FINAL_CLOSURE_DECISION_OWNER_PACKET_FORBIDDEN_FLAGS:
            self.assertFalse(packet[flag])
        self.assertEqual(validate_independent_final_closure_decision_owner_packet_state(packet), [])

        readiness = build_final_acceptance_bundle_readiness_state()
        self.assertTrue(
            readiness["available_prebundle_evidence"]["INDEPENDENT_FINAL_CLOSURE_DECISION_OWNER_PACKET"]
        )
        self.assertEqual(
            readiness["independent_final_closure_decision_owner_packet"]["status"],
            "blocked_owner_action_packet_ready_no_closure",
        )
        self.assertFalse(readiness["available_prebundle_evidence"]["P0_P1_ZERO_PROOF_ARTIFACT_VALIDATION"])

        tampered = json.loads(json.dumps(packet))
        tampered["independent_final_closure_decision_present"] = True
        self.assertIn(
            "independent_final_closure_decision_present must remain false until final reviewer supplies decision",
            validate_independent_final_closure_decision_owner_packet_state(tampered),
        )

        tampered_flag = json.loads(json.dumps(packet))
        tampered_flag["real_smtp_sent"] = True
        self.assertIn(
            "real_smtp_sent must be false",
            validate_independent_final_closure_decision_owner_packet_state(tampered_flag),
        )

    def test_independent_final_reviewer_assignment_request_remains_blocked_without_assignment(self) -> None:
        state = build_independent_final_reviewer_assignment_request_state()

        self.assertEqual(state["status"], "blocked_reviewer_assignment_request_ready_no_assignment")
        self.assertEqual(state["scope"], "independent_final_reviewer_assignment_request_only_no_assignment")
        self.assertEqual(
            tuple(state["required_inputs"]),
            S2PMT07_INDEPENDENT_FINAL_REVIEWER_ASSIGNMENT_REQUEST_REQUIRED_INPUTS,
        )
        self.assertEqual(
            state["assignment_artifact_ref"],
            "FINAL_ACCEPTANCE_BUNDLE/independent_final_reviewer_assignment.json",
        )
        self.assertEqual(state["required_reviewer_role"], "independent_final_reviewer")
        self.assertEqual(
            state["required_reviewer_independence"],
            "not_involved_in_S2PMT01_T06_implementation",
        )
        self.assertEqual(state["p0_candidate_count"], 8)
        self.assertEqual(state["p1_candidate_count"], 37)
        self.assertEqual(state["candidate_total"], 45)
        self.assertTrue(state["all_candidate_inputs_ready"])
        self.assertTrue(state["all_candidate_refs_exist"])
        self.assertTrue(state["assignment_request_ready"])
        self.assertFalse(state["independent_final_reviewer_assigned"])
        self.assertFalse(state["independent_final_closure_decision_present"])
        self.assertFalse(state["zero_proof_artifact_present"])
        self.assertFalse(state["p0_zero_proven"])
        self.assertFalse(state["p1_zero_proven"])
        self.assertFalse(state["closure_claimed"])
        self.assertEqual(state["observed_open_p0_findings"], 8)
        self.assertEqual(state["observed_open_p1_findings"], 37)
        self.assertEqual(
            state["next_required_action"],
            "independent_final_reviewer_must_be_assigned_before_closure_decision",
        )
        for reason in S2PMT07_INDEPENDENT_FINAL_REVIEWER_ASSIGNMENT_REQUEST_BLOCKING_REASONS:
            self.assertIn(reason, state["blocking_reasons"])
        for flag in S2PMT07_INDEPENDENT_FINAL_REVIEWER_ASSIGNMENT_REQUEST_FORBIDDEN_FLAGS:
            self.assertFalse(state[flag])
        for ref in state["review_input_refs"]:
            self.assertTrue((REPO_ROOT / ref).exists(), ref)
        self.assertEqual(validate_independent_final_reviewer_assignment_request_state(state), [])

        readiness = build_final_acceptance_bundle_readiness_state()
        self.assertTrue(
            readiness["available_prebundle_evidence"]["INDEPENDENT_FINAL_REVIEWER_ASSIGNMENT_REQUEST"]
        )
        self.assertEqual(
            readiness["independent_final_reviewer_assignment_request"]["status"],
            "blocked_reviewer_assignment_request_ready_no_assignment",
        )

        tampered = json.loads(json.dumps(state))
        tampered["independent_final_reviewer_assigned"] = True
        self.assertIn(
            "independent_final_reviewer_assigned must be false until assignment artifact exists",
            validate_independent_final_reviewer_assignment_request_state(tampered),
        )

        tampered_flag = json.loads(json.dumps(state))
        tampered_flag["real_smtp_sent"] = True
        self.assertIn(
            "real_smtp_sent must be false",
            validate_independent_final_reviewer_assignment_request_state(tampered_flag),
        )

    def test_independent_final_reviewer_assignment_owner_packet_is_ready_but_not_assignment(self) -> None:
        packet = build_independent_final_reviewer_assignment_owner_packet_state()

        self.assertEqual(packet["status"], "blocked_owner_action_packet_ready_no_assignment")
        self.assertEqual(packet["scope"], "owner_assignment_packet_only_no_assignment")
        self.assertEqual(packet["task_id"], "S2PMT07")
        self.assertEqual(packet["acceptance_id"], "ACC-S2PMT07-FINAL-REVIEW")
        self.assertEqual(
            tuple(packet["required_owner_actions"]),
            S2PMT07_INDEPENDENT_FINAL_REVIEWER_ASSIGNMENT_OWNER_PACKET_REQUIRED_ACTIONS,
        )
        self.assertEqual(
            packet["assignment_artifact_path"],
            "FINAL_ACCEPTANCE_BUNDLE/independent_final_reviewer_assignment.json",
        )
        self.assertEqual(
            tuple(packet["assignment_required_fields"]),
            S2PMT07_INDEPENDENT_FINAL_REVIEWER_ASSIGNMENT_REQUIRED_FIELDS,
        )
        self.assertEqual(packet["required_reviewer_role"], "independent_final_reviewer")
        self.assertEqual(packet["forbidden_reviewer_ids"], ["codex-current-agent"])
        self.assertFalse(packet["assignment_artifact_present"])
        self.assertFalse(packet["independent_final_reviewer_assigned"])
        self.assertFalse(packet["assignment_satisfies_gate"])
        self.assertFalse(packet["p0_zero_proven"])
        self.assertFalse(packet["p1_zero_proven"])
        self.assertEqual(packet["observed_open_p0_findings"], 8)
        self.assertEqual(packet["observed_open_p1_findings"], 37)
        self.assertEqual(
            packet["next_required_action"],
            "owner_or_coordinator_must_create_assignment_artifact_with_independent_reviewer",
        )
        for ref in build_independent_final_reviewer_assignment_request_state()["review_input_refs"]:
            self.assertIn(ref, packet["review_input_refs"])
        for reason in S2PMT07_INDEPENDENT_FINAL_REVIEWER_ASSIGNMENT_OWNER_PACKET_BLOCKING_REASONS:
            self.assertIn(reason, packet["blocking_reasons"])
        for flag in S2PMT07_INDEPENDENT_FINAL_REVIEWER_ASSIGNMENT_OWNER_PACKET_FORBIDDEN_FLAGS:
            self.assertFalse(packet[flag])
        self.assertEqual(validate_independent_final_reviewer_assignment_owner_packet_state(packet), [])

        readiness = build_final_acceptance_bundle_readiness_state()
        self.assertTrue(
            readiness["available_prebundle_evidence"]["INDEPENDENT_FINAL_REVIEWER_ASSIGNMENT_OWNER_PACKET"]
        )
        self.assertFalse(
            readiness["available_prebundle_evidence"]["INDEPENDENT_FINAL_REVIEWER_ASSIGNMENT_VALIDATION"]
        )
        self.assertEqual(
            readiness["independent_final_reviewer_assignment_owner_packet"]["status"],
            "blocked_owner_action_packet_ready_no_assignment",
        )

        tampered = json.loads(json.dumps(packet))
        tampered["assignment_artifact_present"] = True
        self.assertIn(
            "assignment_artifact_present must remain false until owner supplies artifact",
            validate_independent_final_reviewer_assignment_owner_packet_state(tampered),
        )

        tampered_flag = json.loads(json.dumps(packet))
        tampered_flag["real_smtp_sent"] = True
        self.assertIn(
            "real_smtp_sent must be false",
            validate_independent_final_reviewer_assignment_owner_packet_state(tampered_flag),
        )

    def _valid_independent_final_reviewer_assignment_payload(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "schema_version": S2PMT07_INDEPENDENT_FINAL_REVIEWER_ASSIGNMENT_SCHEMA_VERSION,
            "contract_id": "ADP-PRODUCT-CONTRACT-V7.2",
            "generated_at": "2026-06-28T09:16:00+10:00",
            "assignment_decision": S2PMT07_INDEPENDENT_FINAL_REVIEWER_ASSIGNMENT_DECISION,
            "reviewer_assignment": {
                "reviewer_id": "independent-final-reviewer-001",
                "reviewer_role": "independent_final_reviewer",
                "assigned_by": "owner_or_coordinator",
                "assignment_scope": "S2PMT07_P0_P1_FINAL_CLOSURE_REVIEW",
            },
            "reviewer_independence": {
                "status": "verified",
                "required_independence": "not_involved_in_S2PMT01_T06_implementation",
                "reviewer_involved_in_s2pmt01_t06": False,
            },
            "review_input_refs": build_independent_final_reviewer_assignment_request_state()[
                "review_input_refs"
            ],
            "no_production_side_effects": {
                flag: False for flag in S2PMT07_INDEPENDENT_FINAL_REVIEWER_ASSIGNMENT_NO_PRODUCTION_FLAGS
            },
            "assignment_hash": "",
        }
        payload["assignment_hash"] = build_independent_final_reviewer_assignment_hash(payload)
        return payload

    def test_independent_final_reviewer_assignment_artifact_validator_accepts_only_exact_hash_bound_payload(self) -> None:
        payload = self._valid_independent_final_reviewer_assignment_payload()

        self.assertEqual(tuple(payload), S2PMT07_INDEPENDENT_FINAL_REVIEWER_ASSIGNMENT_REQUIRED_FIELDS)
        self.assertEqual(validate_independent_final_reviewer_assignment_artifact(payload), [])

        state = build_independent_final_reviewer_assignment_validation_state(payload)
        self.assertEqual(state["status"], "pass")
        self.assertTrue(state["assignment_present"])
        self.assertTrue(state["independent_final_reviewer_assigned_by_payload"])
        self.assertFalse(state["production_acceptance_claimed"])
        self.assertFalse(state["integrated_production_accepted"])

    def test_final_acceptance_bundle_readiness_consumes_committed_independent_final_reviewer_assignment(self) -> None:
        payload = self._valid_independent_final_reviewer_assignment_payload()

        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            bundle_dir = root / "FINAL_ACCEPTANCE_BUNDLE"
            bundle_dir.mkdir()
            (bundle_dir / "independent_final_reviewer_assignment.json").write_text(
                json.dumps(payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

            state = build_final_acceptance_bundle_readiness_state(repo_root=root)

        assignment_validation = state["independent_final_reviewer_assignment_validation"]
        self.assertTrue(state["available_prebundle_evidence"]["INDEPENDENT_FINAL_REVIEWER_ASSIGNMENT_VALIDATION"])
        self.assertEqual(assignment_validation["status"], "pass")
        self.assertTrue(assignment_validation["assignment_present"])
        self.assertTrue(assignment_validation["independent_final_reviewer_assigned_by_payload"])
        self.assertEqual(assignment_validation["validation_errors"], [])
        self.assertEqual(state["status"], "blocked")
        self.assertFalse(state["production_acceptance_claimed"])
        self.assertFalse(state["integrated_production_accepted"])
        self.assertFalse(state["daily_operation_enabled"])
        self.assertEqual(validate_final_acceptance_bundle_readiness_state(state), [])

    def test_final_acceptance_bundle_readiness_requires_independent_reviewer_assignment_even_when_artifacts_pass(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            bundle_dir = root / "FINAL_ACCEPTANCE_BUNDLE"
            handoff_dir = root / "HANDOFF"
            bundle_dir.mkdir()
            handoff_dir.mkdir()
            bundle_payloads = {
                "manifest.json": self._valid_final_acceptance_bundle_manifest_payload(),
                "p0_p1_zero_proof.json": self._valid_zero_proof_payload(),
                "s2plt04_completion_report.json": self._valid_s2plt04_completion_report_payload(),
                "independent_review_signoff.yaml": self._valid_independent_review_signoff_payload(),
                "final_command_execution.json": self._valid_final_command_execution_payload(),
                "no_production_side_effects.json": self._valid_no_production_side_effect_attestation_payload(),
            }
            for filename, payload in bundle_payloads.items():
                (bundle_dir / filename).write_text(
                    json.dumps(payload, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
            (handoff_dir / "00_下一Agent先读.md").write_text(
                json.dumps(self._valid_next_agent_handoff_payload(), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

            state = build_final_acceptance_bundle_readiness_state(
                repo_root=root,
                manifest=bundle_payloads["manifest.json"],
                p0_p1_zero_proof=bundle_payloads["p0_p1_zero_proof.json"],
                s2plt04_completion_report=bundle_payloads["s2plt04_completion_report.json"],
                independent_review_signoff=bundle_payloads["independent_review_signoff.yaml"],
                final_command_execution=bundle_payloads["final_command_execution.json"],
                no_production_side_effect_attestation=bundle_payloads["no_production_side_effects.json"],
                next_agent_handoff=self._valid_next_agent_handoff_payload(),
            )

        self.assertEqual(state["final_acceptance_bundle_artifact_validation"]["status"], "pass")
        self.assertEqual(state["independent_final_reviewer_assignment_validation"]["status"], "blocked")
        self.assertFalse(
            state["available_prebundle_evidence"]["INDEPENDENT_FINAL_REVIEWER_ASSIGNMENT_VALIDATION"]
        )
        self.assertEqual(state["status"], "blocked")
        self.assertFalse(state["bundle_present"])
        self.assertIn("independent_final_reviewer_assignment_missing", state["blocking_reasons"])
        self.assertFalse(state["production_acceptance_claimed"])
        self.assertFalse(state["integrated_production_accepted"])
        self.assertEqual(validate_final_acceptance_bundle_readiness_state(state), [])

    def test_independent_final_reviewer_assignment_artifact_validator_fails_closed_on_missing_self_review_or_production_flags(self) -> None:
        state = build_independent_final_reviewer_assignment_validation_state(None)

        self.assertEqual(state["status"], "blocked")
        self.assertFalse(state["assignment_present"])
        self.assertIn("independent_final_reviewer_assignment_missing", state["validation_errors"])
        self.assertFalse(state["independent_final_reviewer_assigned_by_payload"])
        self.assertFalse(state["production_acceptance_claimed"])

        payload = {
            "schema_version": S2PMT07_INDEPENDENT_FINAL_REVIEWER_ASSIGNMENT_SCHEMA_VERSION,
            "contract_id": "ADP-PRODUCT-CONTRACT-V7.2",
            "generated_at": "2026-06-28T09:16:00+10:00",
            "assignment_decision": S2PMT07_INDEPENDENT_FINAL_REVIEWER_ASSIGNMENT_DECISION,
            "reviewer_assignment": {
                "reviewer_id": "codex-current-agent",
                "reviewer_role": "independent_final_reviewer",
                "assigned_by": "owner_or_coordinator",
                "assignment_scope": "S2PMT07_P0_P1_FINAL_CLOSURE_REVIEW",
            },
            "reviewer_independence": {
                "status": "verified",
                "required_independence": "not_involved_in_S2PMT01_T06_implementation",
                "reviewer_involved_in_s2pmt01_t06": True,
            },
            "review_input_refs": build_independent_final_reviewer_assignment_request_state()["review_input_refs"],
            "no_production_side_effects": {
                flag: False for flag in S2PMT07_INDEPENDENT_FINAL_REVIEWER_ASSIGNMENT_NO_PRODUCTION_FLAGS
            },
            "assignment_hash": "",
        }
        payload["no_production_side_effects"]["real_smtp_sent"] = True
        payload["assignment_hash"] = build_independent_final_reviewer_assignment_hash(payload)

        errors = validate_independent_final_reviewer_assignment_artifact(payload)
        self.assertIn("reviewer_independence.reviewer_involved_in_s2pmt01_t06 must be false", errors)
        self.assertIn("reviewer_assignment.reviewer_id must not be codex-current-agent", errors)
        self.assertIn("no_production_side_effects.real_smtp_sent must be false", errors)

    def test_s2pmt07_mainline_attestation_binds_main_branch_without_production_acceptance(self) -> None:
        target_commit = "729cda3c6b5d6618ab29afa3161fc3ecd721b87c"
        origin_main_commit = "e7cdeb7a342a4ecee2bde43db479ee30ca72c042"
        state = build_s2pmt07_mainline_attestation_state(
            target_commit=target_commit,
            origin_main_commit=origin_main_commit,
            target_commit_on_origin_main=True,
            open_pr_count=0,
            remote_adp_arxiv_s2p_branch_count=0,
            validations={name: True for name in S2PMT07_MAINLINE_ATTESTATION_REQUIRED_VALIDATIONS},
        )

        self.assertEqual(state["status"], "pass")
        self.assertEqual(state["scope"], "s2pmt07_mainline_attestation_only_no_final_acceptance")
        self.assertEqual(state["attested_commit"], target_commit)
        self.assertEqual(state["origin_main_commit"], origin_main_commit)
        self.assertTrue(state["target_commit_on_origin_main"])
        self.assertEqual(state["open_pr_count"], 0)
        self.assertEqual(state["remote_adp_arxiv_s2p_branch_count"], 0)
        self.assertEqual(tuple(state["required_validations"]), S2PMT07_MAINLINE_ATTESTATION_REQUIRED_VALIDATIONS)
        self.assertEqual(state["missing_validations"], [])
        self.assertTrue(state["mainline_attested"])
        self.assertFalse(state["p0_zero_proven"])
        self.assertFalse(state["p1_zero_proven"])
        self.assertFalse(state["integrated_production_accepted"])
        self.assertFalse(state["daily_operation_enabled"])
        for flag in S2PMT07_MAINLINE_ATTESTATION_NO_PRODUCTION_FLAGS:
            self.assertFalse(state[flag])
        self.assertEqual(validate_s2pmt07_mainline_attestation_state(state), [])

        tampered = json.loads(json.dumps(state))
        tampered["target_commit_on_origin_main"] = False
        self.assertIn(
            "mainline attestation target commit must be contained in origin/main",
            validate_s2pmt07_mainline_attestation_state(tampered),
        )

        tampered_flag = json.loads(json.dumps(state))
        tampered_flag["real_smtp_sent"] = True
        self.assertIn("real_smtp_sent must be false", validate_s2pmt07_mainline_attestation_state(tampered_flag))

        blocked = build_s2pmt07_mainline_attestation_state(
            target_commit=target_commit,
            origin_main_commit=origin_main_commit,
            target_commit_on_origin_main=False,
            open_pr_count=1,
            remote_adp_arxiv_s2p_branch_count=1,
            validations={name: True for name in S2PMT07_MAINLINE_ATTESTATION_REQUIRED_VALIDATIONS[:-1]},
        )
        self.assertEqual(blocked["status"], "blocked")
        self.assertIn("target_commit_not_on_origin_main", blocked["blocking_reasons"])
        self.assertIn("open_pr_count_not_zero", blocked["blocking_reasons"])
        self.assertIn("remote_adp_arxiv_s2p_branch_count_not_zero", blocked["blocking_reasons"])
        self.assertIn("required_validation_missing", blocked["blocking_reasons"])

    def _valid_zero_proof_payload(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "schema_version": S2PMT07_P0_P1_ZERO_PROOF_SCHEMA_VERSION,
            "contract_id": "ADP-PRODUCT-CONTRACT-V7.2",
            "generated_at": "2026-06-28T04:58:30+10:00",
            "reviewer_independence": {
                "status": "verified",
                "required_independence": "not_involved_in_S2PMT01_T06_implementation",
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
        }
        payload["decision_hash"] = build_p0_p1_zero_proof_decision_hash(payload)
        return payload

    def test_p0_p1_zero_proof_artifact_validator_accepts_only_exact_hash_bound_payload(self) -> None:
        payload = self._valid_zero_proof_payload()
        state = build_p0_p1_zero_proof_artifact_validation_state(payload)

        self.assertEqual(validate_p0_p1_zero_proof_artifact(payload), [])
        self.assertEqual(state["status"], "pass")
        self.assertTrue(state["artifact_present"])
        self.assertTrue(state["p0_zero_proven_by_payload"])
        self.assertTrue(state["p1_zero_proven_by_payload"])
        self.assertFalse(state["production_acceptance_claimed"])
        self.assertFalse(state["integrated_production_accepted"])
        self.assertEqual(state["validation_errors"], [])

        tampered = json.loads(json.dumps(payload))
        tampered["finding_counts"]["P0"] = 1
        self.assertIn("finding_counts.P0 must be 0", validate_p0_p1_zero_proof_artifact(tampered))

        tampered_hash = json.loads(json.dumps(payload))
        tampered_hash["decision_hash"] = "sha256:not-the-payload-hash"
        self.assertIn("decision_hash does not match payload content", validate_p0_p1_zero_proof_artifact(tampered_hash))

    def test_p0_p1_zero_proof_artifact_validator_fails_closed_on_missing_refs_or_production_flags(self) -> None:
        missing_state = build_p0_p1_zero_proof_artifact_validation_state(None)

        self.assertEqual(missing_state["status"], "blocked")
        self.assertFalse(missing_state["artifact_present"])
        self.assertIn("p0_p1_zero_proof_artifact_missing", missing_state["validation_errors"])
        self.assertFalse(missing_state["p0_zero_proven_by_payload"])
        self.assertFalse(missing_state["p1_zero_proven_by_payload"])

        payload = self._valid_zero_proof_payload()
        payload["source_candidate_refs"] = []
        self.assertIn(
            "source_candidate_refs must include all P0/P1 technical candidate refs",
            validate_p0_p1_zero_proof_artifact(payload),
        )

        payload = self._valid_zero_proof_payload()
        payload["no_production_side_effects"]["real_smtp_sent"] = True
        self.assertIn("no_production_side_effects.real_smtp_sent must be false", validate_p0_p1_zero_proof_artifact(payload))

    def _valid_final_acceptance_bundle_manifest_payload(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "schema_version": S2PMT07_FINAL_ACCEPTANCE_BUNDLE_MANIFEST_SCHEMA_VERSION,
            "contract_id": "ADP-PRODUCT-CONTRACT-V7.2",
            "generated_at": "2026-06-28T05:18:27+10:00",
            "final_bundle_decision": S2PMT07_FINAL_ACCEPTANCE_BUNDLE_MANIFEST_DECISION,
            "bundle_items": list(S2PMT07_FINAL_ACCEPTANCE_BUNDLE_REQUIRED_ITEMS),
            "bundle_item_hashes": {
                item: f"sha256:{index:064x}" for index, item in enumerate(S2PMT07_FINAL_ACCEPTANCE_BUNDLE_REQUIRED_ITEMS, 1)
            },
            "artifact_validations": {
                validation: {"status": "pass", "artifact_ref": validation.lower()}
                for validation in S2PMT07_FINAL_ACCEPTANCE_BUNDLE_MANIFEST_REQUIRED_ARTIFACT_VALIDATIONS
            },
            "closure_state": {
                "p0_zero_proven": True,
                "p1_zero_proven": True,
                "s2plt04_completed": True,
                "independent_final_review_passed": True,
                "final_commands_executed": True,
                "production_acceptance_claimed": False,
                "integrated_production_accepted": False,
            },
            "no_production_side_effects": {
                flag: False for flag in S2PMT07_FINAL_ACCEPTANCE_BUNDLE_NO_PRODUCTION_FLAGS
            },
        }
        payload["manifest_hash"] = build_final_acceptance_bundle_manifest_hash(payload)
        return payload

    def test_final_acceptance_bundle_manifest_validator_accepts_only_exact_hash_bound_payload(self) -> None:
        payload = self._valid_final_acceptance_bundle_manifest_payload()
        state = build_final_acceptance_bundle_manifest_validation_state(payload)

        self.assertEqual(validate_final_acceptance_bundle_manifest(payload), [])
        self.assertEqual(state["status"], "pass")
        self.assertTrue(state["manifest_present"])
        self.assertTrue(state["bundle_items_complete"])
        self.assertTrue(state["all_artifact_validations_passed"])
        self.assertFalse(state["production_acceptance_claimed"])
        self.assertFalse(state["integrated_production_accepted"])

        tampered = json.loads(json.dumps(payload))
        tampered["bundle_items"] = []
        self.assertIn(
            "bundle_items must exactly match final acceptance bundle required items",
            validate_final_acceptance_bundle_manifest(tampered),
        )

        tampered_hash = json.loads(json.dumps(payload))
        tampered_hash["manifest_hash"] = "sha256:not-the-manifest-hash"
        self.assertIn("manifest_hash does not match payload content", validate_final_acceptance_bundle_manifest(tampered_hash))

    def test_final_acceptance_bundle_manifest_validator_fails_closed_on_missing_or_production_flags(self) -> None:
        missing_state = build_final_acceptance_bundle_manifest_validation_state(None)

        self.assertEqual(missing_state["status"], "blocked")
        self.assertFalse(missing_state["manifest_present"])
        self.assertIn("final_acceptance_bundle_manifest_missing", missing_state["validation_errors"])
        self.assertFalse(missing_state["bundle_items_complete"])
        self.assertFalse(missing_state["all_artifact_validations_passed"])

        payload = self._valid_final_acceptance_bundle_manifest_payload()
        payload["no_production_side_effects"]["scheduler_enabled"] = True
        self.assertIn(
            "no_production_side_effects.scheduler_enabled must be false",
            validate_final_acceptance_bundle_manifest(payload),
        )

        payload = self._valid_final_acceptance_bundle_manifest_payload()
        payload["artifact_validations"]["P0_P1_ZERO_PROOF_ARTIFACT"]["status"] = "blocked"
        self.assertIn(
            "artifact_validations.P0_P1_ZERO_PROOF_ARTIFACT.status must be pass",
            validate_final_acceptance_bundle_manifest(payload),
        )

    def test_final_acceptance_bundle_readiness_embeds_manifest_validation_as_blocked(self) -> None:
        state = build_final_acceptance_bundle_readiness_state()
        manifest_validation = state["final_acceptance_bundle_manifest_validation"]

        self.assertEqual(manifest_validation["status"], "blocked")
        self.assertFalse(manifest_validation["manifest_present"])
        self.assertFalse(state["available_prebundle_evidence"]["FINAL_ACCEPTANCE_BUNDLE_MANIFEST_VALIDATION"])
        self.assertIn("final_acceptance_bundle_manifest_missing", manifest_validation["validation_errors"])
        self.assertEqual(validate_final_acceptance_bundle_readiness_state(state), [])

    def _valid_s2plt04_completion_report_payload(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "schema_version": S2PMT07_S2PLT04_COMPLETION_REPORT_SCHEMA_VERSION,
            "contract_id": "ADP-PRODUCT-CONTRACT-V7.2",
            "generated_at": "2026-06-28T05:42:10+10:00",
            "s2plt04_decision": S2PMT07_S2PLT04_COMPLETION_REPORT_DECISION,
            "source_evidence_refs": {
                "S2PLT01_REPLAY_REVIEW": {
                    "status": "pass",
                    "artifact_ref": "governance/run_manifests/ADP-S2PLT01-INDEPENDENT-REPLAY-REVIEW-20260626.json",
                },
                "S2PLT02_LIVE_2D_PROOF": {
                    "status": "pass",
                    "artifact_ref": "governance/run_manifests/ADP-S2PLT02-LIVE-2D-PROOF-20260628.json",
                },
                "S2PLT03_RESILIENCE_PROOF": {
                    "status": "pass",
                    "artifact_ref": "governance/run_manifests/ADP-S2PLT03-RESILIENCE-PROOF-20260628.json",
                },
                "P0_P1_ZERO_PROOF": {
                    "status": "pass",
                    "artifact_ref": "FINAL_ACCEPTANCE_BUNDLE/p0_p1_zero_proof.json",
                },
                "FINAL_BUNDLE_MANIFEST": {
                    "status": "pass",
                    "artifact_ref": "FINAL_ACCEPTANCE_BUNDLE/manifest.json",
                },
            },
            "terminal_dependency_state": {
                dependency: True
                for dependency in S2PMT07_S2PLT04_COMPLETION_REPORT_REQUIRED_TERMINAL_DEPENDENCIES
            },
            "final_bundle_refs": list(S2PMT07_FINAL_ACCEPTANCE_BUNDLE_REQUIRED_ITEMS),
            "no_production_side_effects": {
                flag: False for flag in S2PMT07_S2PLT04_COMPLETION_REPORT_NO_PRODUCTION_FLAGS
            },
        }
        payload["report_hash"] = build_s2plt04_completion_report_hash(payload)
        return payload

    def test_s2plt04_completion_report_validator_accepts_only_exact_hash_bound_payload(self) -> None:
        payload = self._valid_s2plt04_completion_report_payload()
        state = build_s2plt04_completion_report_validation_state(payload)

        self.assertEqual(validate_s2plt04_completion_report(payload), [])
        self.assertEqual(state["status"], "pass")
        self.assertTrue(state["report_present"])
        self.assertTrue(state["s2plt04_completed_by_report"])
        self.assertTrue(state["terminal_dependencies_passed"])
        self.assertFalse(state["production_acceptance_claimed"])
        self.assertFalse(state["integrated_production_accepted"])

        tampered = json.loads(json.dumps(payload))
        tampered["terminal_dependency_state"]["S2PLT02_ACCEPTED"] = False
        self.assertIn(
            "terminal_dependency_state.S2PLT02_ACCEPTED must be true",
            validate_s2plt04_completion_report(tampered),
        )

        tampered_hash = json.loads(json.dumps(payload))
        tampered_hash["report_hash"] = "sha256:not-the-report-hash"
        self.assertIn("report_hash does not match payload content", validate_s2plt04_completion_report(tampered_hash))

    def test_s2plt04_completion_report_validator_fails_closed_on_missing_or_production_flags(self) -> None:
        missing_state = build_s2plt04_completion_report_validation_state(None)

        self.assertEqual(missing_state["status"], "blocked")
        self.assertFalse(missing_state["report_present"])
        self.assertIn("s2plt04_completion_report_missing", missing_state["validation_errors"])
        self.assertFalse(missing_state["s2plt04_completed_by_report"])
        self.assertFalse(missing_state["terminal_dependencies_passed"])

        payload = self._valid_s2plt04_completion_report_payload()
        payload["no_production_side_effects"]["release_uploaded"] = True
        self.assertIn(
            "no_production_side_effects.release_uploaded must be false",
            validate_s2plt04_completion_report(payload),
        )

        payload = self._valid_s2plt04_completion_report_payload()
        del payload["source_evidence_refs"]["S2PLT03_RESILIENCE_PROOF"]
        self.assertIn(
            "source_evidence_refs must include S2PLT03_RESILIENCE_PROOF",
            validate_s2plt04_completion_report(payload),
        )

    def test_final_acceptance_bundle_readiness_embeds_s2plt04_completion_report_validation_as_blocked(self) -> None:
        state = build_final_acceptance_bundle_readiness_state()
        completion_report = state["s2plt04_completion_report_validation"]

        self.assertEqual(completion_report["status"], "blocked")
        self.assertFalse(completion_report["report_present"])
        self.assertFalse(state["available_prebundle_evidence"]["S2PLT04_COMPLETION_REPORT_VALIDATION"])
        self.assertIn("s2plt04_completion_report_missing", completion_report["validation_errors"])
        self.assertEqual(validate_final_acceptance_bundle_readiness_state(state), [])

    def _valid_final_command_execution_payload(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "schema_version": S2PMT07_FINAL_COMMAND_EXECUTION_SCHEMA_VERSION,
            "contract_id": "ADP-PRODUCT-CONTRACT-V7.2",
            "generated_at": "2026-06-28T06:26:30+10:00",
            "execution_decision": S2PMT07_FINAL_COMMAND_EXECUTION_DECISION,
            "executor_independence": {
                "status": "verified",
                "required_independence": "not_involved_in_S2PMT01_T06_implementation",
                "executor_role": "independent_final_reviewer",
            },
            "required_commands_executed": list(S2PMT07_REQUIRED_TEST_COMMANDS),
            "command_results": {
                command: {
                    "status": "pass",
                    "exit_code": 0,
                    "executed_by": "independent_final_reviewer",
                    "evidence_ref": f"governance/final_command_logs/{index:02d}.log",
                }
                for index, command in enumerate(S2PMT07_REQUIRED_TEST_COMMANDS, 1)
            },
            "final_bundle_refs": list(S2PMT07_FINAL_ACCEPTANCE_BUNDLE_REQUIRED_ITEMS),
            "no_production_side_effects": {
                flag: False for flag in S2PMT07_FINAL_COMMAND_EXECUTION_NO_PRODUCTION_FLAGS
            },
        }
        payload["execution_hash"] = build_final_command_execution_hash(payload)
        return payload

    def test_final_command_execution_validator_accepts_only_exact_hash_bound_payload(self) -> None:
        payload = self._valid_final_command_execution_payload()
        state = build_final_command_execution_validation_state(payload)

        self.assertEqual(validate_final_command_execution_artifact(payload), [])
        self.assertEqual(tuple(payload), S2PMT07_FINAL_COMMAND_EXECUTION_REQUIRED_FIELDS)
        self.assertEqual(state["status"], "pass")
        self.assertTrue(state["command_execution_present"])
        self.assertTrue(state["all_required_commands_passed"])
        self.assertTrue(state["final_commands_executed_by_payload"])
        self.assertFalse(state["production_acceptance_claimed"])
        self.assertFalse(state["integrated_production_accepted"])

        tampered = json.loads(json.dumps(payload))
        tampered["command_results"][S2PMT07_REQUIRED_TEST_COMMANDS[0]] = {
            "status": "pass",
            "exit_code": 1,
            "executed_by": "independent_final_reviewer",
            "evidence_ref": "governance/final_command_logs/01.log",
        }
        self.assertIn(
            f"command_results.{S2PMT07_REQUIRED_TEST_COMMANDS[0]}.exit_code must be 0",
            validate_final_command_execution_artifact(tampered),
        )

        tampered_hash = json.loads(json.dumps(payload))
        tampered_hash["execution_hash"] = "sha256:not-the-execution-hash"
        self.assertIn("execution_hash does not match payload content", validate_final_command_execution_artifact(tampered_hash))

    def test_final_command_execution_validator_fails_closed_on_missing_or_production_flags(self) -> None:
        missing_state = build_final_command_execution_validation_state(None)

        self.assertEqual(missing_state["status"], "blocked")
        self.assertFalse(missing_state["command_execution_present"])
        self.assertIn("final_command_execution_missing", missing_state["validation_errors"])
        self.assertFalse(missing_state["all_required_commands_passed"])
        self.assertFalse(missing_state["final_commands_executed_by_payload"])

        payload = self._valid_final_command_execution_payload()
        payload["no_production_side_effects"]["real_smtp_sent"] = True
        self.assertIn(
            "no_production_side_effects.real_smtp_sent must be false",
            validate_final_command_execution_artifact(payload),
        )

        payload = self._valid_final_command_execution_payload()
        del payload["command_results"][S2PMT07_REQUIRED_TEST_COMMANDS[-1]]
        self.assertIn(
            f"command_results must include {S2PMT07_REQUIRED_TEST_COMMANDS[-1]}",
            validate_final_command_execution_artifact(payload),
        )

    def test_final_acceptance_bundle_readiness_embeds_final_command_execution_validation_as_blocked(self) -> None:
        state = build_final_acceptance_bundle_readiness_state()
        final_command = state["final_command_execution_validation"]

        self.assertEqual(final_command["status"], "blocked")
        self.assertFalse(final_command["command_execution_present"])
        self.assertFalse(state["available_prebundle_evidence"]["FINAL_COMMAND_EXECUTION_VALIDATION"])
        self.assertIn("final_command_execution_missing", final_command["validation_errors"])
        self.assertEqual(validate_final_acceptance_bundle_readiness_state(state), [])

    def test_final_acceptance_bundle_readiness_consumes_committed_final_command_execution(self) -> None:
        payload = self._valid_final_command_execution_payload()

        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            bundle_dir = root / "FINAL_ACCEPTANCE_BUNDLE"
            bundle_dir.mkdir()
            (bundle_dir / "final_command_execution.json").write_text(
                json.dumps(payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

            state = build_final_acceptance_bundle_readiness_state(repo_root=root)

        self.assertTrue(state["available_items"]["FINAL_ACCEPTANCE_BUNDLE/final_command_execution.json"])
        self.assertTrue(state["available_prebundle_evidence"]["FINAL_COMMAND_EXECUTION_VALIDATION"])
        self.assertEqual(state["final_command_execution_validation"]["status"], "pass")
        self.assertEqual(
            state["final_acceptance_bundle_artifact_validation"]["artifact_validations"][
                "FINAL_COMMAND_EXECUTION"
            ]["status"],
            "pass",
        )
        self.assertNotIn("independent_final_command_execution_missing", state["blocking_reasons"])
        self.assertIn("p0_p1_zero_proof_missing", state["blocking_reasons"])
        self.assertIn("no_production_side_effect_attestation_missing", state["blocking_reasons"])
        self.assertEqual(state["status"], "blocked")
        self.assertFalse(state["production_acceptance_claimed"])
        self.assertFalse(state["integrated_production_accepted"])
        self.assertEqual(validate_final_acceptance_bundle_readiness_state(state), [])

    def test_local_runtime_no_production_state_accepts_disabled_launchd_and_smtp_false(self) -> None:
        print_disabled_output = "\n".join(
            f'\t\t"{label}" => disabled'
            for label in S2PMT07_LOCAL_RUNTIME_NO_PRODUCTION_REQUIRED_LABELS
        )
        service_outputs = {
            label: f"gui/501/{label} = {{\n\tstate = not running\n}}"
            for label in S2PMT07_LOCAL_RUNTIME_NO_PRODUCTION_REQUIRED_LABELS
        }
        env_flags = {
            flag: "false"
            for flag in S2PMT07_LOCAL_RUNTIME_NO_PRODUCTION_REQUIRED_ENV_FLAGS_FALSE
        }

        state = build_local_runtime_no_production_state(
            generated_at="2026-06-28T17:12:00+10:00",
            launchctl_print_disabled_output=print_disabled_output,
            launchctl_print_outputs=service_outputs,
            env_flags=env_flags,
        )

        self.assertEqual(state["status"], "pass")
        self.assertTrue(state["launchd_labels_disabled"])
        self.assertTrue(state["launchd_labels_not_running"])
        self.assertTrue(state["smtp_send_flag_false"])
        self.assertEqual(state["blocking_reasons"], [])
        self.assertFalse(state["real_smtp_send_enabled"])
        self.assertFalse(state["scheduler_install_enabled"])
        self.assertEqual(validate_local_runtime_no_production_state(state), [])

    def test_local_runtime_no_production_state_blocks_enabled_launchd_or_smtp_true(self) -> None:
        print_disabled_output = "\n".join(
            f'\t\t"{label}" => enabled'
            for label in S2PMT07_LOCAL_RUNTIME_NO_PRODUCTION_REQUIRED_LABELS
        )
        service_outputs = {
            label: f"gui/501/{label} = {{\n\tstate = not running\n}}"
            for label in S2PMT07_LOCAL_RUNTIME_NO_PRODUCTION_REQUIRED_LABELS
        }

        state = build_local_runtime_no_production_state(
            generated_at="2026-06-28T17:12:00+10:00",
            launchctl_print_disabled_output=print_disabled_output,
            launchctl_print_outputs=service_outputs,
            env_flags={"ADP_ALLOW_SMTP_SEND": "true"},
        )

        self.assertEqual(state["status"], "blocked")
        self.assertFalse(state["launchd_labels_disabled"])
        self.assertTrue(state["launchd_labels_not_running"])
        self.assertFalse(state["smtp_send_flag_false"])
        self.assertIn("launchd_label_not_disabled", state["blocking_reasons"])
        self.assertIn("smtp_send_flag_enabled", state["blocking_reasons"])
        self.assertEqual(validate_local_runtime_no_production_state(state), [])

        tampered = json.loads(json.dumps(state))
        tampered["blocking_reasons"] = []
        self.assertIn(
            "blocked local runtime no-production blocking_reasons must match failed gates",
            validate_local_runtime_no_production_state(tampered),
        )

    def _valid_no_production_side_effect_attestation_payload(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "schema_version": S2PMT07_NO_PRODUCTION_SIDE_EFFECT_ATTESTATION_SCHEMA_VERSION,
            "contract_id": "ADP-PRODUCT-CONTRACT-V7.2",
            "generated_at": "2026-06-28T08:40:00+10:00",
            "attestation_decision": S2PMT07_NO_PRODUCTION_SIDE_EFFECT_ATTESTATION_DECISION,
            "attestation_scope": {
                "task_id": "S2PMT07",
                "scope": "no_production_side_effect_attestation_validation_only_no_production_acceptance",
                "required_bundle_items": list(S2PMT07_FINAL_ACCEPTANCE_BUNDLE_REQUIRED_ITEMS),
            },
            "verified_evidence_refs": {
                ref: {
                    "status": "pass",
                    "evidence_ref": f"governance/final_review/{ref.lower()}.json",
                }
                for ref in S2PMT07_NO_PRODUCTION_SIDE_EFFECT_ATTESTATION_REQUIRED_EVIDENCE_REFS
            },
            "no_production_side_effects": {
                flag: False
                for flag in S2PMT07_NO_PRODUCTION_SIDE_EFFECT_ATTESTATION_NO_PRODUCTION_FLAGS
            },
            "closure_state": {
                "no_production_side_effects_proven": True,
                "production_acceptance_claimed": False,
                "integrated_production_accepted": False,
                "daily_operation_enabled": False,
            },
        }
        payload["attestation_hash"] = build_no_production_side_effect_attestation_hash(payload)
        return payload

    def test_no_production_side_effect_attestation_accepts_only_exact_hash_bound_payload(self) -> None:
        payload = self._valid_no_production_side_effect_attestation_payload()
        state = build_no_production_side_effect_attestation_validation_state(payload)

        self.assertEqual(validate_no_production_side_effect_attestation(payload), [])
        self.assertEqual(tuple(payload), S2PMT07_NO_PRODUCTION_SIDE_EFFECT_ATTESTATION_REQUIRED_FIELDS)
        self.assertEqual(state["status"], "pass")
        self.assertTrue(state["attestation_present"])
        self.assertTrue(state["all_required_evidence_refs_passed"])
        self.assertTrue(state["no_production_side_effects_proven_by_payload"])
        self.assertFalse(state["production_acceptance_claimed"])
        self.assertFalse(state["integrated_production_accepted"])

        tampered = json.loads(json.dumps(payload))
        tampered["verified_evidence_refs"]["FULL_ADP_UNITTEST"]["status"] = "blocked"
        self.assertIn(
            "verified_evidence_refs.FULL_ADP_UNITTEST.status must be pass",
            validate_no_production_side_effect_attestation(tampered),
        )

        tampered_hash = json.loads(json.dumps(payload))
        tampered_hash["attestation_hash"] = "sha256:not-the-attestation-hash"
        self.assertIn(
            "attestation_hash does not match payload content",
            validate_no_production_side_effect_attestation(tampered_hash),
        )

    def test_committed_no_production_side_effect_attestation_artifact_validates(self) -> None:
        artifact_path = REPO_ROOT / "FINAL_ACCEPTANCE_BUNDLE" / "no_production_side_effects.json"
        payload = json.loads(artifact_path.read_text(encoding="utf-8"))
        state = build_final_acceptance_bundle_artifact_validation_state(
            bundle_directory_present=True,
            no_production_side_effect_attestation=payload,
        )

        self.assertEqual(validate_no_production_side_effect_attestation(payload), [])
        self.assertEqual(
            payload["attestation_hash"],
            build_no_production_side_effect_attestation_hash(payload),
        )
        self.assertEqual(
            state["artifact_validations"]["NO_PRODUCTION_SIDE_EFFECT_ATTESTATION"]["status"],
            "pass",
        )
        self.assertEqual(state["status"], "blocked")
        self.assertIn("final_acceptance_bundle_manifest_missing", state["blocking_reasons"])
        self.assertIn("p0_p1_zero_proof_missing", state["blocking_reasons"])
        self.assertFalse(state["production_acceptance_claimed"])
        self.assertFalse(state["integrated_production_accepted"])
        self.assertFalse(state["daily_operation_enabled"])

    def test_final_acceptance_bundle_readiness_consumes_committed_no_production_attestation(self) -> None:
        state = build_final_acceptance_bundle_readiness_state()
        artifact_validation = state["final_acceptance_bundle_artifact_validation"]

        self.assertTrue(state["available_items"]["FINAL_ACCEPTANCE_BUNDLE/no_production_side_effects.json"])
        self.assertFalse(state["available_items"]["FINAL_ACCEPTANCE_BUNDLE/p0_p1_zero_proof.json"])
        self.assertTrue(state["available_prebundle_evidence"]["NO_PRODUCTION_SIDE_EFFECT_ATTESTATION_VALIDATION"])
        self.assertEqual(state["no_production_side_effect_attestation_validation"]["status"], "pass")
        self.assertTrue(artifact_validation["bundle_directory_present"])
        self.assertEqual(
            artifact_validation["artifact_validations"]["NO_PRODUCTION_SIDE_EFFECT_ATTESTATION"]["status"],
            "pass",
        )
        self.assertNotIn("no_production_side_effect_attestation_missing", state["blocking_reasons"])
        self.assertIn("p0_p1_zero_proof_missing", state["blocking_reasons"])
        self.assertIn("final_acceptance_bundle_manifest_missing", state["blocking_reasons"])
        self.assertEqual(state["status"], "blocked")
        self.assertFalse(state["production_acceptance_claimed"])
        self.assertFalse(state["integrated_production_accepted"])
        self.assertEqual(validate_final_acceptance_bundle_readiness_state(state), [])

    def test_final_bundle_templates_exist_but_do_not_satisfy_readiness(self) -> None:
        template_dir = REPO_ROOT / "FINAL_ACCEPTANCE_BUNDLE" / "templates"
        self.assertTrue((template_dir / "TEMPLATE_INDEX.md").exists())
        self.assertFalse((template_dir / "README.md").exists())

        expected_templates = (
            "independent_final_reviewer_assignment.template.json",
            "p0_p1_zero_proof.template.json",
            "s2plt04_completion_report.template.json",
            "independent_review_signoff.template.yaml",
            "final_command_execution.template.json",
            "next_agent_handoff.template.json",
        )

        for filename in expected_templates:
            template_path = template_dir / filename
            self.assertTrue(template_path.exists(), str(template_path))
            self.assertGreater(template_path.stat().st_size, 200, str(template_path))

        state = build_final_acceptance_bundle_readiness_state()

        for required_item in (
            "FINAL_ACCEPTANCE_BUNDLE/p0_p1_zero_proof.json",
            "FINAL_ACCEPTANCE_BUNDLE/s2plt04_completion_report.json",
            "FINAL_ACCEPTANCE_BUNDLE/independent_review_signoff.yaml",
            "FINAL_ACCEPTANCE_BUNDLE/final_command_execution.json",
            "HANDOFF/00_下一Agent先读.md",
        ):
            self.assertFalse(state["available_items"][required_item], required_item)
            self.assertIn(required_item, state["missing_items"], required_item)
        self.assertEqual(state["status"], "blocked")
        self.assertFalse(state["production_acceptance_claimed"])
        self.assertFalse(state["integrated_production_accepted"])
        self.assertFalse(state["daily_operation_enabled"])

    def test_no_production_side_effect_attestation_fails_closed_on_missing_or_production_flags(self) -> None:
        missing_state = build_no_production_side_effect_attestation_validation_state(None)

        self.assertEqual(missing_state["status"], "blocked")
        self.assertFalse(missing_state["attestation_present"])
        self.assertIn("no_production_side_effect_attestation_missing", missing_state["validation_errors"])
        self.assertFalse(missing_state["all_required_evidence_refs_passed"])
        self.assertFalse(missing_state["no_production_side_effects_proven_by_payload"])

        payload = self._valid_no_production_side_effect_attestation_payload()
        payload["no_production_side_effects"]["release_uploaded"] = True
        self.assertIn(
            "no_production_side_effects.release_uploaded must be false",
            validate_no_production_side_effect_attestation(payload),
        )

        payload = self._valid_no_production_side_effect_attestation_payload()
        del payload["verified_evidence_refs"]["OPEN_PR_COUNT_ZERO"]
        self.assertIn(
            "verified_evidence_refs must include OPEN_PR_COUNT_ZERO",
            validate_no_production_side_effect_attestation(payload),
        )

    def test_final_acceptance_bundle_readiness_embeds_committed_no_production_attestation(self) -> None:
        state = build_final_acceptance_bundle_readiness_state()
        attestation = state["no_production_side_effect_attestation_validation"]

        self.assertEqual(attestation["status"], "pass")
        self.assertTrue(attestation["attestation_present"])
        self.assertTrue(state["available_prebundle_evidence"]["NO_PRODUCTION_SIDE_EFFECT_ATTESTATION_VALIDATION"])
        self.assertEqual(attestation["validation_errors"], [])
        self.assertEqual(validate_final_acceptance_bundle_readiness_state(state), [])

    def _valid_next_agent_handoff_payload(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "schema_version": S2PMT07_NEXT_AGENT_HANDOFF_SCHEMA_VERSION,
            "contract_id": "ADP-PRODUCT-CONTRACT-V7.2",
            "generated_at": "2026-06-28T09:16:00+10:00",
            "handoff_decision": S2PMT07_NEXT_AGENT_HANDOFF_DECISION,
            "handoff_scope": {
                "task_id": "S2PMT07",
                "scope": "next_agent_handoff_validation_only_no_production_acceptance",
                "required_reader_files": list(S2PMT07_NEXT_AGENT_HANDOFF_REQUIRED_READER_FILES),
            },
            "required_reader_files": list(S2PMT07_NEXT_AGENT_HANDOFF_REQUIRED_READER_FILES),
            "required_artifact_validations": {
                validation: {
                    "status": "pass",
                    "evidence_ref": f"governance/final_review/{validation.lower()}.json",
                }
                for validation in S2PMT07_NEXT_AGENT_HANDOFF_REQUIRED_ARTIFACT_VALIDATIONS
            },
            "required_bundle_refs": list(S2PMT07_FINAL_ACCEPTANCE_BUNDLE_REQUIRED_ITEMS),
            "blocking_state": {
                "p0_zero_proven": True,
                "p1_zero_proven": True,
                "s2plt04_completed": True,
                "final_commands_executed": True,
                "no_production_side_effects_proven": True,
                "production_acceptance_claimed": False,
                "integrated_production_accepted": False,
                "daily_operation_enabled": False,
            },
            "no_production_side_effects": {
                flag: False for flag in S2PMT07_NEXT_AGENT_HANDOFF_NO_PRODUCTION_FLAGS
            },
        }
        payload["handoff_hash"] = build_next_agent_handoff_hash(payload)
        return payload

    def test_next_agent_handoff_validator_accepts_only_exact_hash_bound_payload(self) -> None:
        payload = self._valid_next_agent_handoff_payload()
        state = build_next_agent_handoff_validation_state(payload)

        self.assertEqual(validate_next_agent_handoff(payload), [])
        self.assertEqual(tuple(payload), S2PMT07_NEXT_AGENT_HANDOFF_REQUIRED_FIELDS)
        self.assertEqual(state["status"], "pass")
        self.assertTrue(state["handoff_present"])
        self.assertTrue(state["all_required_artifact_validations_passed"])
        self.assertTrue(state["all_required_reader_files_declared"])
        self.assertTrue(state["next_agent_handoff_ready_by_payload"])
        self.assertFalse(state["production_acceptance_claimed"])
        self.assertFalse(state["integrated_production_accepted"])

        tampered = json.loads(json.dumps(payload))
        tampered["required_reader_files"] = []
        self.assertIn(
            "required_reader_files must exactly match next-agent handoff required reader files",
            validate_next_agent_handoff(tampered),
        )

        tampered_hash = json.loads(json.dumps(payload))
        tampered_hash["handoff_hash"] = "sha256:not-the-handoff-hash"
        self.assertIn("handoff_hash does not match payload content", validate_next_agent_handoff(tampered_hash))

    def test_next_agent_handoff_validator_fails_closed_on_missing_or_production_flags(self) -> None:
        missing_state = build_next_agent_handoff_validation_state(None)

        self.assertEqual(missing_state["status"], "blocked")
        self.assertFalse(missing_state["handoff_present"])
        self.assertIn("next_agent_handoff_missing", missing_state["validation_errors"])
        self.assertFalse(missing_state["all_required_artifact_validations_passed"])
        self.assertFalse(missing_state["next_agent_handoff_ready_by_payload"])

        payload = self._valid_next_agent_handoff_payload()
        payload["no_production_side_effects"]["daily_operation_enabled"] = True
        self.assertIn(
            "no_production_side_effects.daily_operation_enabled must be false",
            validate_next_agent_handoff(payload),
        )

        payload = self._valid_next_agent_handoff_payload()
        del payload["required_artifact_validations"]["NO_PRODUCTION_SIDE_EFFECT_ATTESTATION"]
        self.assertIn(
            "required_artifact_validations must include NO_PRODUCTION_SIDE_EFFECT_ATTESTATION",
            validate_next_agent_handoff(payload),
        )

    def test_final_acceptance_bundle_readiness_embeds_next_agent_handoff_validation_as_blocked(self) -> None:
        state = build_final_acceptance_bundle_readiness_state()
        handoff = state["next_agent_handoff_validation"]

        self.assertEqual(handoff["status"], "blocked")
        self.assertFalse(handoff["handoff_present"])
        self.assertFalse(state["available_prebundle_evidence"]["NEXT_AGENT_HANDOFF_VALIDATION"])
        self.assertIn("next_agent_handoff_missing", handoff["validation_errors"])
        self.assertEqual(validate_final_acceptance_bundle_readiness_state(state), [])

    def _valid_independent_review_signoff_payload(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "schema_version": S2PMT07_INDEPENDENT_REVIEW_SIGNOFF_SCHEMA_VERSION,
            "contract_id": "ADP-PRODUCT-CONTRACT-V7.2",
            "generated_at": "2026-06-28T07:18:00+10:00",
            "signoff_decision": S2PMT07_INDEPENDENT_REVIEW_SIGNOFF_DECISION,
            "reviewer_independence": {
                "status": "verified",
                "required_independence": "not_involved_in_S2PMT01_T06_implementation",
                "reviewer_role": "independent_final_reviewer",
                "not_implementation_agent": True,
            },
            "review_scope": {
                "task_id": "S2PMT07",
                "scope": "independent_review_signoff_validation_only_no_production_acceptance",
                "reviewed_artifact_validations": list(
                    S2PMT07_INDEPENDENT_REVIEW_SIGNOFF_REQUIRED_ARTIFACT_VALIDATIONS
                ),
            },
            "artifact_validations": {
                validation: {
                    "status": "pass",
                    "evidence_ref": f"governance/final_review/{validation.lower()}.json",
                }
                for validation in S2PMT07_INDEPENDENT_REVIEW_SIGNOFF_REQUIRED_ARTIFACT_VALIDATIONS
            },
            "closure_state": {
                "p0_zero_proven": True,
                "p1_zero_proven": True,
                "s2plt04_completed": True,
                "final_commands_executed": True,
                "no_production_side_effects_proven": True,
                "production_acceptance_claimed": False,
                "integrated_production_accepted": False,
            },
            "final_bundle_refs": list(S2PMT07_FINAL_ACCEPTANCE_BUNDLE_REQUIRED_ITEMS),
            "no_production_side_effects": {
                flag: False for flag in S2PMT07_INDEPENDENT_REVIEW_SIGNOFF_NO_PRODUCTION_FLAGS
            },
        }
        payload["signoff_hash"] = build_independent_review_signoff_hash(payload)
        return payload

    def test_independent_review_signoff_validator_accepts_only_exact_hash_bound_payload(self) -> None:
        payload = self._valid_independent_review_signoff_payload()
        state = build_independent_review_signoff_validation_state(payload)

        self.assertEqual(validate_independent_review_signoff_artifact(payload), [])
        self.assertEqual(tuple(payload), S2PMT07_INDEPENDENT_REVIEW_SIGNOFF_REQUIRED_FIELDS)
        self.assertEqual(state["status"], "pass")
        self.assertTrue(state["signoff_present"])
        self.assertTrue(state["all_required_artifact_validations_passed"])
        self.assertTrue(state["independent_review_signed_off_by_payload"])
        self.assertFalse(state["production_acceptance_claimed"])
        self.assertFalse(state["integrated_production_accepted"])

        tampered = json.loads(json.dumps(payload))
        tampered["artifact_validations"]["FINAL_COMMAND_EXECUTION"]["status"] = "blocked"
        self.assertIn(
            "artifact_validations.FINAL_COMMAND_EXECUTION.status must be pass",
            validate_independent_review_signoff_artifact(tampered),
        )

        tampered_hash = json.loads(json.dumps(payload))
        tampered_hash["signoff_hash"] = "sha256:not-the-signoff-hash"
        self.assertIn(
            "signoff_hash does not match payload content",
            validate_independent_review_signoff_artifact(tampered_hash),
        )

    def test_independent_review_signoff_validator_fails_closed_on_missing_or_production_flags(self) -> None:
        missing_state = build_independent_review_signoff_validation_state(None)

        self.assertEqual(missing_state["status"], "blocked")
        self.assertFalse(missing_state["signoff_present"])
        self.assertIn("independent_review_signoff_missing", missing_state["validation_errors"])
        self.assertFalse(missing_state["all_required_artifact_validations_passed"])
        self.assertFalse(missing_state["independent_review_signed_off_by_payload"])

        payload = self._valid_independent_review_signoff_payload()
        payload["no_production_side_effects"]["scheduler_install_enabled"] = True
        self.assertIn(
            "no_production_side_effects.scheduler_install_enabled must be false",
            validate_independent_review_signoff_artifact(payload),
        )

        payload = self._valid_independent_review_signoff_payload()
        del payload["artifact_validations"]["NO_PRODUCTION_SIDE_EFFECT_ATTESTATION"]
        self.assertIn(
            "artifact_validations must include NO_PRODUCTION_SIDE_EFFECT_ATTESTATION",
            validate_independent_review_signoff_artifact(payload),
        )

    def test_final_acceptance_bundle_readiness_embeds_independent_review_signoff_validation_as_blocked(self) -> None:
        state = build_final_acceptance_bundle_readiness_state()
        signoff = state["independent_review_signoff_validation"]

        self.assertEqual(signoff["status"], "blocked")
        self.assertFalse(signoff["signoff_present"])
        self.assertFalse(state["available_prebundle_evidence"]["INDEPENDENT_REVIEW_SIGNOFF_VALIDATION"])
        self.assertIn("independent_review_signoff_missing", signoff["validation_errors"])
        self.assertEqual(validate_final_acceptance_bundle_readiness_state(state), [])

    def test_final_bundle_prerequisite_plan_orders_missing_artifacts_fail_closed(self) -> None:
        plan = build_final_bundle_prerequisite_plan_state()

        self.assertEqual(plan["status"], "blocked")
        self.assertEqual(plan["scope"], "final_bundle_prerequisite_plan_only_no_production_acceptance")
        self.assertEqual(tuple(plan["required_steps"]), S2PMT07_FINAL_BUNDLE_PREREQUISITE_PLAN_REQUIRED_STEPS)
        self.assertFalse(plan["all_required_steps_passed"])
        self.assertFalse(plan["ready_for_final_bundle_manifest"])
        self.assertEqual(plan["next_required_step"], "P0_P1_ZERO_PROOF_ARTIFACT")
        self.assertEqual([step["step_id"] for step in plan["ordered_steps"]], list(plan["required_steps"]))
        for reason in S2PMT07_FINAL_BUNDLE_PREREQUISITE_PLAN_BLOCKING_REASONS:
            self.assertIn(reason, plan["blocking_reasons"])
        for flag in S2PMT07_FINAL_BUNDLE_PREREQUISITE_PLAN_FORBIDDEN_FLAGS:
            self.assertFalse(plan[flag])
        self.assertEqual(validate_final_bundle_prerequisite_plan_state(plan), [])

        tampered = json.loads(json.dumps(plan))
        tampered["ordered_steps"][0]["status"] = "pass"
        self.assertIn(
            "final bundle prerequisite plan cannot mark steps pass before artifacts exist",
            validate_final_bundle_prerequisite_plan_state(tampered),
        )

        tampered_flag = json.loads(json.dumps(plan))
        tampered_flag["real_smtp_send_enabled"] = True
        self.assertIn(
            "real_smtp_send_enabled must be false",
            validate_final_bundle_prerequisite_plan_state(tampered_flag),
        )

    def test_final_acceptance_bundle_readiness_embeds_prerequisite_plan_as_valid_blocked_evidence(self) -> None:
        state = build_final_acceptance_bundle_readiness_state()
        plan = state["final_bundle_prerequisite_plan"]

        self.assertEqual(plan["status"], "blocked")
        self.assertFalse(plan["ready_for_final_bundle_manifest"])
        self.assertTrue(state["available_prebundle_evidence"]["FINAL_BUNDLE_PREREQUISITE_PLAN"])
        self.assertEqual(validate_final_bundle_prerequisite_plan_state(plan), [])
        self.assertEqual(validate_final_acceptance_bundle_readiness_state(state), [])

    def test_final_acceptance_bundle_artifact_validation_blocks_incomplete_bundle_directory(self) -> None:
        state = build_final_acceptance_bundle_artifact_validation_state(bundle_directory_present=True)

        self.assertEqual(state["status"], "blocked")
        self.assertEqual(state["scope"], "final_acceptance_bundle_artifact_validation_only_no_production_acceptance")
        self.assertTrue(state["bundle_directory_present"])
        self.assertFalse(state["all_required_items_present"])
        self.assertFalse(state["all_artifact_validations_passed"])
        self.assertEqual(set(state["missing_items"]), set(S2PMT07_FINAL_ACCEPTANCE_BUNDLE_REQUIRED_ITEMS))
        self.assertNotIn("final_acceptance_bundle_directory_missing", state["blocking_reasons"])
        self.assertIn("final_acceptance_bundle_manifest_missing", state["blocking_reasons"])
        self.assertIn("p0_p1_zero_proof_missing", state["blocking_reasons"])
        self.assertIn("s2plt04_completion_evidence_missing", state["blocking_reasons"])
        self.assertIn("independent_review_signoff_missing", state["blocking_reasons"])
        self.assertIn("independent_final_command_execution_missing", state["blocking_reasons"])
        self.assertIn("no_production_side_effect_attestation_missing", state["blocking_reasons"])
        self.assertEqual(state["artifact_validations"]["FINAL_ACCEPTANCE_BUNDLE_MANIFEST"]["status"], "blocked")
        self.assertEqual(state["artifact_validations"]["P0_P1_ZERO_PROOF_ARTIFACT"]["status"], "blocked")
        self.assertEqual(state["artifact_validations"]["S2PLT04_COMPLETION_REPORT"]["status"], "blocked")
        self.assertEqual(state["artifact_validations"]["INDEPENDENT_REVIEW_SIGNOFF"]["status"], "blocked")
        self.assertEqual(state["artifact_validations"]["FINAL_COMMAND_EXECUTION"]["status"], "blocked")
        self.assertEqual(
            state["artifact_validations"]["NO_PRODUCTION_SIDE_EFFECT_ATTESTATION"]["status"],
            "blocked",
        )
        self.assertEqual(state["artifact_validations"]["NEXT_AGENT_HANDOFF"]["status"], "blocked")
        self.assertFalse(state["production_acceptance_claimed"])
        self.assertFalse(state["integrated_production_accepted"])
        self.assertEqual(validate_final_acceptance_bundle_artifact_validation_state(state), [])

        tampered = json.loads(json.dumps(state))
        tampered["all_artifact_validations_passed"] = True
        self.assertIn(
            "final acceptance bundle artifact validation cannot pass while artifact validations are blocked",
            validate_final_acceptance_bundle_artifact_validation_state(tampered),
        )

    def test_final_acceptance_bundle_readiness_embeds_directory_level_artifact_validation(self) -> None:
        state = build_final_acceptance_bundle_readiness_state()
        directory_validation = state["final_acceptance_bundle_artifact_validation"]

        self.assertEqual(directory_validation["status"], "blocked")
        self.assertTrue(directory_validation["bundle_directory_present"])
        self.assertFalse(state["available_prebundle_evidence"]["FINAL_ACCEPTANCE_BUNDLE_ARTIFACT_VALIDATION"])
        self.assertNotIn("final_acceptance_bundle_directory_missing", directory_validation["blocking_reasons"])
        self.assertNotIn("no_production_side_effect_attestation_missing", directory_validation["blocking_reasons"])
        self.assertEqual(
            directory_validation["artifact_validations"]["NO_PRODUCTION_SIDE_EFFECT_ATTESTATION"]["status"],
            "pass",
        )
        self.assertEqual(validate_final_acceptance_bundle_artifact_validation_state(directory_validation), [])
        self.assertEqual(validate_final_acceptance_bundle_readiness_state(state), [])

    def test_p0_p1_technical_candidate_builder_fails_closed_without_closure(self) -> None:
        state = build_p0_p1_technical_closure_candidate_state()

        self.assertEqual(state["scope"], "technical_closure_candidate_reviews_only_not_p0_p1_zero_proof")
        self.assertIn(
            "governance/run_manifests/ADP-S2PMT07-P0-TECHNICAL-CLOSURE-CANDIDATE-PACKAGE-20260627.json",
            state["candidate_manifest_refs"],
        )
        self.assertIn(
            "governance/run_manifests/ADP-S2PMT07-P1-INDEPENDENT-REVIEW-RECEIPT-20260626.json",
            state["candidate_manifest_refs"],
        )
        self.assertEqual(validate_p0_p1_technical_closure_candidate_state(state), [])

    def test_full_precheck_report_fails_closed_without_production_side_effects(self) -> None:
        report = build_s2pmt07_precheck_report(generated_at="2026-06-26T17:00:00+10:00")

        self.assertEqual(report["status"], "blocked")
        self.assertFalse(report["production_acceptance_claimed"])
        self.assertFalse(report["inherited_p0_p1_closed"])
        for flag in S2PMT07_FORBIDDEN_PASS_FLAGS:
            self.assertFalse(report[flag])
        for reason in S2PMT07_BLOCKING_REASONS[:4]:
            self.assertIn(reason, report["blocking_reasons"])
        self.assertIn("final_acceptance_bundle_missing", report["blocking_reasons"])
        self.assertIn("independent_review_signoff_missing", report["blocking_reasons"])
        self.assertIn("independent_final_command_execution_missing", report["blocking_reasons"])
        self.assertFalse(report["test_gates"]["executed_as_final_reviewer"])
        self.assertEqual(validate_s2pmt07_precheck_report(report), [])

        tampered = dict(report)
        tampered["integrated_production_accepted"] = True
        self.assertIn("integrated_production_accepted must be false", validate_s2pmt07_precheck_report(tampered))

        tampered_bundle = json.loads(json.dumps(report))
        tampered_bundle["final_acceptance_bundle_readiness"]["bundle_claimed_ready"] = True
        self.assertIn(
            "S2PMT07 final acceptance bundle readiness is invalid",
            validate_s2pmt07_precheck_report(tampered_bundle),
        )

    def test_s2pmt07_final_command_blocker_is_recorded_in_report_phase_and_manifest(self) -> None:
        blocker = "independent_final_command_execution_missing"
        report = build_s2pmt07_precheck_report(generated_at="2026-06-27T02:59:04+10:00")
        phase_record = (
            REPO_ROOT / "arxiv-daily-push/docs/phase_records/PHASE_S2PMT07_FINAL_GATE_PRECHECK.md"
        ).read_text(encoding="utf-8")
        manifest = json.loads(
            (REPO_ROOT / "governance/run_manifests/ADP-S2PMT07-FINAL-GATE-PRECHECK-20260626.json").read_text(
                encoding="utf-8"
            )
        )

        self.assertIn(blocker, S2PMT07_BLOCKING_REASONS)
        self.assertIn(blocker, report["blocking_reasons"])
        self.assertFalse(report["gates"]["required_final_commands_executed"])
        self.assertFalse(report["test_gates"]["executed_as_final_reviewer"])
        self.assertIn(blocker, phase_record)
        self.assertIn(blocker, manifest["blocking_reasons"])
        self.assertFalse(manifest["independent_final_command_execution_present"])


if __name__ == "__main__":
    unittest.main()
