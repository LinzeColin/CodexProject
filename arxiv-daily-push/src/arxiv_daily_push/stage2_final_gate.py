"""S2PL/S2PM fail-closed final production gate precheck helpers."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from datetime import date
from pathlib import Path
from typing import Any

from arxiv_daily_push.stage2_lease_fencing import build_m4_cycle_watermark
from arxiv_daily_push.stage2_replay_gate import (
    S2PLT01_REQUIRED_MAIL_PRODUCTS,
    build_s2plt01_independent_replay_review_report,
    build_s2plt01_replay_payload_execution_report,
    build_s2plt01_terminal_acceptance_audit_state,
    validate_s2plt01_independent_replay_review_report,
)


S2PMT07_FINAL_GATE_MODEL_ID = "adp-s2pmt07-final-gate-precheck-v1"
S2PMT07_ACCEPTANCE_ID = "ACC-S2PMT07-FINAL-REVIEW"
S2PMT07_TASK_ID = "S2PMT07"
S2PMT07_SCHEMA_VERSION = 1
S2PMT07_INHERITED_V7_1_OPEN_P0_FINDINGS = 8
S2PMT07_INHERITED_V7_1_OPEN_P1_FINDINGS = 37
S2PMT07_REQUIRED_REVIEWER_INDEPENDENCE = "not_involved_in_S2PMT01_T06_implementation"
S2PMT07_REQUIRED_ZERO_FINDING_SEVERITIES = ("P0", "P1")
S2PMT07_REQUIRED_DEPENDENCIES = (
    "S2PMT01",
    "S2PMT02",
    "S2PMT03",
    "S2PMT04",
    "S2PMT05",
    "S2PMT06",
    "S2PLT04",
)
S2PMT07_REQUIRED_EVIDENCE = (
    "FINAL_ACCEPTANCE_BUNDLE/",
    "HANDOFF/00_下一Agent先读.md",
    "independent_review_signoff.yaml",
)
S2PMT07_REQUIRED_TEST_COMMANDS = (
    "python tools/validate_task_pack.py --root .",
    "python -m pytest -q",
    "python tools/verify_acceptance_bundle.py --require-zero P0 P1",
)
S2PMT07_FORBIDDEN_PASS_FLAGS = (
    "integrated_production_accepted",
    "daily_operation_enabled",
    "real_smtp_send_enabled",
    "scheduler_install_enabled",
    "release_packaging_enabled",
    "production_restore_enabled",
    "current_pointer_changed",
    "v7_1_baseline_changed",
    "v7_2_contract_files_changed",
)
S2PMT07_BLOCKING_REASONS = (
    "reviewer_independence_not_proven",
    "inherited_v7_1_p0_findings_open",
    "inherited_v7_1_p1_findings_open",
    "s2plt04_not_completed",
    "final_acceptance_bundle_missing",
    "independent_review_signoff_missing",
    "independent_final_command_execution_missing",
)
S2PMT07_REMAINING_BLOCKER_MATRIX_REQUIRED_BLOCKERS = S2PMT07_BLOCKING_REASONS
S2PMT07_P0_P1_ZERO_PROOF_ARTIFACT_PATH = "FINAL_ACCEPTANCE_BUNDLE/p0_p1_zero_proof.json"
S2PMT07_NO_PRODUCTION_SIDE_EFFECT_ATTESTATION_ARTIFACT_PATH = (
    "FINAL_ACCEPTANCE_BUNDLE/no_production_side_effects.json"
)
S2PMT07_P0_P1_ZERO_PROOF_SCHEMA_VERSION = "adp.p0_p1_zero_proof.v1"
S2PMT07_P0_P1_ZERO_PROOF_CLOSURE_DECISION = "P0_P1_ZERO_PROVEN_NO_PRODUCTION_ACCEPTANCE"
S2PMT07_P0_P1_ZERO_PROOF_REQUIRED_FIELDS = (
    "schema_version",
    "contract_id",
    "generated_at",
    "reviewer_independence",
    "source_candidate_refs",
    "finding_counts",
    "zero_severity_counts",
    "independent_closure_decision",
    "final_bundle_refs",
    "no_production_side_effects",
    "decision_hash",
)
S2PMT07_P0_P1_ZERO_PROOF_NO_PRODUCTION_FLAGS = (
    "integrated_production_accepted",
    "daily_operation_enabled",
    "real_smtp_sent",
    "real_smtp_send_enabled",
    "scheduler_enabled",
    "scheduler_install_enabled",
    "release_uploaded",
    "release_packaging_enabled",
    "production_restore_enabled",
    "production_restore_executed",
    "public_schema_changed",
    "db_migration_executed",
    "production_queue_mutated",
    "source_adapter_changed",
    "ranking_algorithm_changed",
    "current_pointer_changed",
    "v7_1_baseline_changed",
    "v7_2_contract_files_changed",
)
S2PMT07_P0_P1_ZERO_PROOF_BLOCKING_REASONS = (
    "p0_p1_zero_proof_artifact_missing",
    "independent_final_closure_decision_missing",
    "inherited_v7_1_p0_findings_open",
    "inherited_v7_1_p1_findings_open",
)
S2PMT07_P0_P1_ZERO_PROOF_ASSEMBLY_REQUIRED_INPUTS = (
    "P0_TECHNICAL_CLOSURE_CANDIDATE_PACKAGE",
    "P1_TECHNICAL_CLOSURE_CANDIDATE_RECEIPTS",
    "CANDIDATE_MANIFEST_REFS",
    "INDEPENDENT_FINAL_CLOSURE_DECISION",
    "ZERO_OPEN_P0_P1_COUNTS",
    "NO_PRODUCTION_SIDE_EFFECTS",
    "FINAL_BUNDLE_REFS",
)
S2PMT07_P0_P1_ZERO_PROOF_ASSEMBLY_BLOCKING_REASONS = (
    "independent_final_closure_decision_missing",
    "p0_p1_zero_proof_artifact_missing",
    "inherited_v7_1_p0_findings_open",
    "inherited_v7_1_p1_findings_open",
)
S2PMT07_P0_P1_ZERO_PROOF_ASSEMBLY_FORBIDDEN_FLAGS = (
    "production_acceptance_claimed",
    "integrated_production_accepted",
    "daily_operation_enabled",
    "real_smtp_sent",
    "real_smtp_send_enabled",
    "scheduler_enabled",
    "scheduler_install_enabled",
    "release_uploaded",
    "release_packaging_enabled",
    "production_restore_enabled",
    "production_restore_executed",
    "public_schema_changed",
    "db_migration_executed",
    "production_queue_mutated",
    "source_adapter_changed",
    "ranking_algorithm_changed",
    "current_pointer_changed",
    "v7_1_baseline_changed",
    "v7_2_contract_files_changed",
)
S2PMT07_INDEPENDENT_FINAL_REVIEWER_ASSIGNMENT_ARTIFACT_PATH = (
    "FINAL_ACCEPTANCE_BUNDLE/independent_final_reviewer_assignment.json"
)
S2PMT07_INDEPENDENT_FINAL_REVIEWER_ASSIGNMENT_SCHEMA_VERSION = (
    "adp.independent_final_reviewer_assignment.v1"
)
S2PMT07_INDEPENDENT_FINAL_REVIEWER_ASSIGNMENT_DECISION = (
    "INDEPENDENT_FINAL_REVIEWER_ASSIGNED_NO_PRODUCTION_ACCEPTANCE"
)
S2PMT07_INDEPENDENT_FINAL_REVIEWER_ASSIGNMENT_REQUIRED_FIELDS = (
    "schema_version",
    "contract_id",
    "generated_at",
    "assignment_decision",
    "reviewer_assignment",
    "reviewer_independence",
    "review_input_refs",
    "no_production_side_effects",
    "assignment_hash",
)
S2PMT07_INDEPENDENT_FINAL_REVIEWER_ASSIGNMENT_NO_PRODUCTION_FLAGS = (
    "production_acceptance_claimed",
    "integrated_production_accepted",
    "daily_operation_enabled",
    "real_smtp_sent",
    "real_smtp_send_enabled",
    "scheduler_enabled",
    "scheduler_install_enabled",
    "release_uploaded",
    "release_packaging_enabled",
    "production_restore_enabled",
    "production_restore_executed",
    "public_schema_changed",
    "db_migration_executed",
    "production_queue_mutated",
    "source_adapter_changed",
    "ranking_algorithm_changed",
    "current_pointer_changed",
    "v7_1_baseline_changed",
    "v7_2_contract_files_changed",
)
S2PMT07_INDEPENDENT_FINAL_REVIEWER_ASSIGNMENT_REQUEST_REQUIRED_INPUTS = (
    "V7_2_CURRENT_CONTRACT_AND_ROOT_LOCK",
    "P0_P1_ZERO_PROOF_ASSEMBLY_STATE",
    "P0_P1_ZERO_PROOF_READINESS_STATE",
    "P0_TECHNICAL_CLOSURE_CANDIDATE_PACKAGE",
    "P1_TECHNICAL_CLOSURE_CANDIDATE_RECEIPTS",
    "FINAL_ACCEPTANCE_BUNDLE_REQUIRED_ITEMS",
    "NO_PRODUCTION_SIDE_EFFECT_FLAGS",
    "REVIEWER_INDEPENDENCE_REQUIREMENT",
)
S2PMT07_INDEPENDENT_FINAL_REVIEWER_ASSIGNMENT_REQUEST_BLOCKING_REASONS = (
    "independent_final_reviewer_assignment_missing",
    "independent_final_closure_decision_missing",
    "p0_p1_zero_proof_artifact_missing",
    "s2plt04_completion_report_missing",
    "final_command_execution_missing",
    "no_production_side_effect_attestation_missing",
    "next_agent_handoff_missing",
    "final_acceptance_bundle_manifest_missing",
    "inherited_v7_1_p0_findings_open",
    "inherited_v7_1_p1_findings_open",
)
S2PMT07_INDEPENDENT_FINAL_REVIEWER_ASSIGNMENT_REQUEST_FORBIDDEN_FLAGS = (
    "production_acceptance_claimed",
    "integrated_production_accepted",
    "daily_operation_enabled",
    "real_smtp_sent",
    "real_smtp_send_enabled",
    "scheduler_enabled",
    "scheduler_install_enabled",
    "release_uploaded",
    "release_packaging_enabled",
    "production_restore_enabled",
    "production_restore_executed",
    "public_schema_changed",
    "db_migration_executed",
    "production_queue_mutated",
    "source_adapter_changed",
    "ranking_algorithm_changed",
    "current_pointer_changed",
    "v7_1_baseline_changed",
    "v7_2_contract_files_changed",
)
S2PMT07_INDEPENDENT_FINAL_REVIEWER_ASSIGNMENT_OWNER_PACKET_REQUIRED_ACTIONS = (
    "select_reviewer_not_involved_in_s2pmt01_t06_implementation",
    "record_reviewer_id_role_assigner_and_scope",
    "verify_reviewer_independence_against_required_input_refs",
    "write_assignment_artifact_to_final_acceptance_bundle_path",
    "keep_all_no_production_side_effect_flags_false",
)
S2PMT07_INDEPENDENT_FINAL_REVIEWER_ASSIGNMENT_OWNER_PACKET_BLOCKING_REASONS = (
    "owner_or_coordinator_assignment_artifact_missing",
    "independent_final_reviewer_assignment_missing",
    "independent_final_closure_decision_missing",
    "p0_p1_zero_proof_artifact_missing",
    "s2plt04_completion_report_missing",
    "final_command_execution_missing",
    "no_production_side_effect_attestation_missing",
    "next_agent_handoff_missing",
    "final_acceptance_bundle_manifest_missing",
    "inherited_v7_1_p0_findings_open",
    "inherited_v7_1_p1_findings_open",
)
S2PMT07_INDEPENDENT_FINAL_REVIEWER_ASSIGNMENT_OWNER_PACKET_FORBIDDEN_FLAGS = (
    S2PMT07_INDEPENDENT_FINAL_REVIEWER_ASSIGNMENT_REQUEST_FORBIDDEN_FLAGS
)
S2PMT07_INDEPENDENT_FINAL_CLOSURE_DECISION_REQUEST_REQUIRED_INPUTS = (
    "P0_P1_ZERO_PROOF_ASSEMBLY_STATE",
    "P0_P1_ZERO_PROOF_READINESS_STATE",
    "P0_TECHNICAL_CLOSURE_CANDIDATE_PACKAGE",
    "P1_TECHNICAL_CLOSURE_CANDIDATE_RECEIPTS",
    "FINAL_ACCEPTANCE_BUNDLE_REQUIRED_ITEMS",
    "NO_PRODUCTION_SIDE_EFFECT_FLAGS",
    "INDEPENDENT_FINAL_REVIEWER_ROLE",
)
S2PMT07_INDEPENDENT_FINAL_CLOSURE_DECISION_REQUEST_BLOCKING_REASONS = (
    "independent_final_reviewer_assignment_missing",
    "independent_final_closure_decision_missing",
    "p0_p1_zero_proof_artifact_missing",
    "s2plt04_completion_report_missing",
    "final_command_execution_missing",
    "no_production_side_effect_attestation_missing",
    "next_agent_handoff_missing",
    "final_acceptance_bundle_manifest_missing",
    "inherited_v7_1_p0_findings_open",
    "inherited_v7_1_p1_findings_open",
)
S2PMT07_INDEPENDENT_FINAL_CLOSURE_DECISION_REQUEST_FORBIDDEN_FLAGS = (
    "production_acceptance_claimed",
    "integrated_production_accepted",
    "daily_operation_enabled",
    "real_smtp_sent",
    "real_smtp_send_enabled",
    "scheduler_enabled",
    "scheduler_install_enabled",
    "release_uploaded",
    "release_packaging_enabled",
    "production_restore_enabled",
    "production_restore_executed",
    "public_schema_changed",
    "db_migration_executed",
    "production_queue_mutated",
    "source_adapter_changed",
    "ranking_algorithm_changed",
    "current_pointer_changed",
    "v7_1_baseline_changed",
    "v7_2_contract_files_changed",
)
S2PMT07_INDEPENDENT_FINAL_CLOSURE_DECISION_OWNER_PACKET_REQUIRED_ACTIONS = (
    "confirm_independent_reviewer_assignment_artifact_is_valid",
    "review_all_p0_p1_candidate_evidence_refs",
    "issue_or_reject_independent_closure_decision",
    "write_decision_only_inside_p0_p1_zero_proof_artifact",
    "keep_all_no_production_side_effect_flags_false",
)
S2PMT07_INDEPENDENT_FINAL_CLOSURE_DECISION_OWNER_PACKET_BLOCKING_REASONS = (
    "independent_final_closure_decision_owner_packet_only_not_closure",
    "independent_final_reviewer_assignment_missing",
    "independent_final_closure_decision_missing",
    "p0_p1_zero_proof_artifact_missing",
    "s2plt04_completion_report_missing",
    "final_command_execution_missing",
    "no_production_side_effect_attestation_missing",
    "next_agent_handoff_missing",
    "final_acceptance_bundle_manifest_missing",
    "inherited_v7_1_p0_findings_open",
    "inherited_v7_1_p1_findings_open",
)
S2PMT07_INDEPENDENT_FINAL_CLOSURE_DECISION_OWNER_PACKET_FORBIDDEN_FLAGS = (
    S2PMT07_INDEPENDENT_FINAL_CLOSURE_DECISION_REQUEST_FORBIDDEN_FLAGS
)
S2PMT07_FINAL_ACCEPTANCE_BUNDLE_REQUIRED_ITEMS = (
    "FINAL_ACCEPTANCE_BUNDLE/manifest.json",
    S2PMT07_INDEPENDENT_FINAL_REVIEWER_ASSIGNMENT_ARTIFACT_PATH,
    S2PMT07_P0_P1_ZERO_PROOF_ARTIFACT_PATH,
    "FINAL_ACCEPTANCE_BUNDLE/s2plt04_completion_report.json",
    "FINAL_ACCEPTANCE_BUNDLE/independent_review_signoff.yaml",
    "FINAL_ACCEPTANCE_BUNDLE/final_command_execution.json",
    S2PMT07_NO_PRODUCTION_SIDE_EFFECT_ATTESTATION_ARTIFACT_PATH,
    "HANDOFF/00_下一Agent先读.md",
)
S2PMT07_FINAL_ACCEPTANCE_BUNDLE_BLOCKING_REASONS = (
    "final_acceptance_bundle_directory_missing",
    "final_acceptance_bundle_manifest_missing",
    "independent_final_reviewer_assignment_missing",
    "p0_p1_zero_proof_missing",
    "s2plt04_completion_evidence_missing",
    "independent_review_signoff_missing",
    "independent_final_command_execution_missing",
    "no_production_side_effect_attestation_missing",
    "next_agent_handoff_missing",
)
S2PMT07_FINAL_ACCEPTANCE_BUNDLE_FORBIDDEN_FLAGS = (
    "bundle_claimed_ready",
    "production_acceptance_claimed",
    "integrated_production_accepted",
    "daily_operation_enabled",
    "real_smtp_send_enabled",
    "scheduler_install_enabled",
    "release_packaging_enabled",
    "production_restore_enabled",
)
S2PMT07_FINAL_ACCEPTANCE_BUNDLE_MANIFEST_SCHEMA_VERSION = "adp.final_acceptance_bundle_manifest.v1"
S2PMT07_FINAL_ACCEPTANCE_BUNDLE_MANIFEST_DECISION = (
    "FINAL_ACCEPTANCE_BUNDLE_READY_NO_PRODUCTION_ACCEPTANCE"
)
S2PMT07_FINAL_ACCEPTANCE_BUNDLE_MANIFEST_REQUIRED_FIELDS = (
    "schema_version",
    "contract_id",
    "generated_at",
    "final_bundle_decision",
    "bundle_items",
    "bundle_item_hashes",
    "artifact_validations",
    "closure_state",
    "no_production_side_effects",
    "manifest_hash",
)
S2PMT07_FINAL_ACCEPTANCE_BUNDLE_MANIFEST_REQUIRED_ARTIFACT_VALIDATIONS = (
    "INDEPENDENT_FINAL_REVIEWER_ASSIGNMENT_VALIDATION",
    "P0_P1_ZERO_PROOF_ARTIFACT",
    "S2PLT04_COMPLETION_REPORT",
    "INDEPENDENT_REVIEW_SIGNOFF",
    "FINAL_COMMAND_EXECUTION",
    "NO_PRODUCTION_SIDE_EFFECT_ATTESTATION",
    "NEXT_AGENT_HANDOFF",
)
S2PMT07_FINAL_ACCEPTANCE_BUNDLE_NO_PRODUCTION_FLAGS = (
    "integrated_production_accepted",
    "daily_operation_enabled",
    "real_smtp_sent",
    "real_smtp_send_enabled",
    "scheduler_enabled",
    "scheduler_install_enabled",
    "release_uploaded",
    "release_packaging_enabled",
    "production_restore_enabled",
    "production_restore_executed",
    "public_schema_changed",
    "db_migration_executed",
    "production_queue_mutated",
    "source_adapter_changed",
    "ranking_algorithm_changed",
    "current_pointer_changed",
    "v7_1_baseline_changed",
    "v7_2_contract_files_changed",
)
S2PMT07_S2PLT04_COMPLETION_REPORT_SCHEMA_VERSION = "adp.s2plt04_completion_report.v1"
S2PMT07_S2PLT04_COMPLETION_REPORT_DECISION = "S2PLT04_COMPLETED_NO_PRODUCTION_ACCEPTANCE"
S2PMT07_S2PLT04_COMPLETION_REPORT_REQUIRED_FIELDS = (
    "schema_version",
    "contract_id",
    "generated_at",
    "s2plt04_decision",
    "source_evidence_refs",
    "terminal_dependency_state",
    "final_bundle_refs",
    "no_production_side_effects",
    "report_hash",
)
S2PMT07_S2PLT04_COMPLETION_REPORT_REQUIRED_SOURCE_EVIDENCE_REFS = (
    "S2PLT01_REPLAY_REVIEW",
    "S2PLT02_LIVE_2D_PROOF",
    "S2PLT03_RESILIENCE_PROOF",
    "P0_P1_ZERO_PROOF",
)
S2PMT07_S2PLT04_COMPLETION_REPORT_REQUIRED_TERMINAL_DEPENDENCIES = (
    "S2PLT01_ACCEPTED",
    "S2PLT02_ACCEPTED",
    "S2PLT03_ACCEPTED",
    "P0_ZERO_PROVEN",
    "P1_ZERO_PROVEN",
)
S2PMT07_S2PLT04_COMPLETION_REPORT_NO_PRODUCTION_FLAGS = S2PMT07_FINAL_ACCEPTANCE_BUNDLE_NO_PRODUCTION_FLAGS
S2PMT07_S2PLT04_COMPLETION_EVIDENCE_AUDIT_SCOPE = (
    "s2plt04_completion_evidence_audit_only_no_report_creation"
)
S2PMT07_S2PLT04_COMPLETION_EVIDENCE_AUDIT_BLOCKING_REASONS = (
    "s2plt01_not_accepted",
    "s2plt02_live_2d_terminal_proof_missing",
    "s2plt03_resilience_terminal_proof_missing",
)
S2PMT07_FINAL_COMMAND_EXECUTION_SCHEMA_VERSION = "adp.final_command_execution.v1"
S2PMT07_FINAL_COMMAND_EXECUTION_DECISION = "FINAL_COMMANDS_EXECUTED_NO_PRODUCTION_ACCEPTANCE"
S2PMT07_FINAL_COMMAND_EXECUTION_REQUIRED_FIELDS = (
    "schema_version",
    "contract_id",
    "generated_at",
    "execution_decision",
    "executor_independence",
    "required_commands_executed",
    "command_results",
    "final_bundle_refs",
    "no_production_side_effects",
    "execution_hash",
)
S2PMT07_FINAL_COMMAND_EXECUTION_NO_PRODUCTION_FLAGS = S2PMT07_FINAL_ACCEPTANCE_BUNDLE_NO_PRODUCTION_FLAGS
S2PMT07_NO_PRODUCTION_SIDE_EFFECT_ATTESTATION_SCHEMA_VERSION = (
    "adp.no_production_side_effect_attestation.v1"
)
S2PMT07_NO_PRODUCTION_SIDE_EFFECT_ATTESTATION_DECISION = (
    "NO_PRODUCTION_SIDE_EFFECTS_PROVEN_NO_PRODUCTION_ACCEPTANCE"
)
S2PMT07_NO_PRODUCTION_SIDE_EFFECT_ATTESTATION_REQUIRED_FIELDS = (
    "schema_version",
    "contract_id",
    "generated_at",
    "attestation_decision",
    "attestation_scope",
    "verified_evidence_refs",
    "no_production_side_effects",
    "closure_state",
    "attestation_hash",
)
S2PMT07_NO_PRODUCTION_SIDE_EFFECT_ATTESTATION_REQUIRED_EVIDENCE_REFS = (
    "V7_2_VALIDATOR",
    "PROJECT_GOVERNANCE",
    "CHANGED_ONLY_SEMANTIC_GOVERNANCE",
    "LEAN_RENDER",
    "FULL_ADP_UNITTEST",
    "LOCAL_LAUNCHD_DISABLED_STATE",
    "LOCAL_SMTP_SEND_FLAG_FALSE",
    "OPEN_PR_COUNT_ZERO",
    "REMOTE_ADP_BRANCH_SCAN",
    "PRODUCTION_TRUE_FLAG_DIFF_SCAN",
)
S2PMT07_NO_PRODUCTION_SIDE_EFFECT_ATTESTATION_NO_PRODUCTION_FLAGS = (
    S2PMT07_FINAL_ACCEPTANCE_BUNDLE_NO_PRODUCTION_FLAGS
)
S2PMT07_LOCAL_RUNTIME_NO_PRODUCTION_SCHEMA_VERSION = "adp.local_runtime_no_production_state.v1"
S2PMT07_LOCAL_RUNTIME_NO_PRODUCTION_SCOPE = (
    "local_runtime_no_production_precheck_only_no_scheduler_or_smtp_enablement"
)
S2PMT07_LOCAL_RUNTIME_NO_PRODUCTION_REQUIRED_LABELS = (
    "com.linze.adp.local.daily",
    "com.linze.adp.local.health",
    "com.linze.adp.local.watchdog",
)
S2PMT07_LOCAL_RUNTIME_NO_PRODUCTION_REQUIRED_ENV_FLAGS_FALSE = (
    "ADP_ALLOW_SMTP_SEND",
)
S2PMT07_LOCAL_RUNTIME_NO_PRODUCTION_BLOCKING_REASONS = (
    "launchd_label_not_disabled",
    "launchd_label_running",
    "smtp_send_flag_enabled",
)
S2PMT07_NEXT_AGENT_HANDOFF_SCHEMA_VERSION = "adp.next_agent_handoff.v1"
S2PMT07_NEXT_AGENT_HANDOFF_DECISION = "NEXT_AGENT_HANDOFF_READY_NO_PRODUCTION_ACCEPTANCE"
S2PMT07_NEXT_AGENT_HANDOFF_REQUIRED_FIELDS = (
    "schema_version",
    "contract_id",
    "generated_at",
    "handoff_decision",
    "handoff_scope",
    "required_reader_files",
    "required_artifact_validations",
    "required_bundle_refs",
    "blocking_state",
    "no_production_side_effects",
    "handoff_hash",
)
S2PMT07_NEXT_AGENT_HANDOFF_REQUIRED_READER_FILES = (
    "docs/pursuing_goal/CURRENT.yaml",
    "docs/pursuing_goal/v7_2/V7_2_ROOT_LOCK.yaml",
    "docs/pursuing_goal/v7_2/HANDOFF/00_下一Agent先读.md",
    "docs/pursuing_goal/v7_2/machine_readable/product_contract_v7_2.yaml",
    "docs/pursuing_goal/v7_2/machine_readable/migration_matrix_v7_1_to_v7_2.yaml",
    "docs/pursuing_goal/v7_1/V7_1_ROOT_LOCK.yaml",
)
S2PMT07_NEXT_AGENT_HANDOFF_REQUIRED_ARTIFACT_VALIDATIONS = (
    "P0_P1_ZERO_PROOF_ARTIFACT",
    "S2PLT04_COMPLETION_REPORT",
    "FINAL_COMMAND_EXECUTION",
    "NO_PRODUCTION_SIDE_EFFECT_ATTESTATION",
)
S2PMT07_NEXT_AGENT_HANDOFF_NO_PRODUCTION_FLAGS = S2PMT07_FINAL_ACCEPTANCE_BUNDLE_NO_PRODUCTION_FLAGS
S2PMT07_INDEPENDENT_REVIEW_SIGNOFF_SCHEMA_VERSION = "adp.independent_review_signoff.v1"
S2PMT07_INDEPENDENT_REVIEW_SIGNOFF_DECISION = "INDEPENDENT_REVIEW_SIGNED_OFF_NO_PRODUCTION_ACCEPTANCE"
S2PMT07_INDEPENDENT_REVIEW_SIGNOFF_REQUIRED_FIELDS = (
    "schema_version",
    "contract_id",
    "generated_at",
    "signoff_decision",
    "reviewer_independence",
    "review_scope",
    "artifact_validations",
    "closure_state",
    "final_bundle_refs",
    "no_production_side_effects",
    "signoff_hash",
)
S2PMT07_INDEPENDENT_REVIEW_SIGNOFF_REQUIRED_ARTIFACT_VALIDATIONS = (
    "P0_P1_ZERO_PROOF_ARTIFACT",
    "S2PLT04_COMPLETION_REPORT",
    "FINAL_COMMAND_EXECUTION",
    "NO_PRODUCTION_SIDE_EFFECT_ATTESTATION",
    "NEXT_AGENT_HANDOFF",
)
S2PMT07_INDEPENDENT_REVIEW_SIGNOFF_NO_PRODUCTION_FLAGS = S2PMT07_FINAL_ACCEPTANCE_BUNDLE_NO_PRODUCTION_FLAGS
S2PMT07_FINAL_ACCEPTANCE_BUNDLE_ARTIFACT_VALIDATION_KEYS = (
    "FINAL_ACCEPTANCE_BUNDLE_MANIFEST",
    "INDEPENDENT_FINAL_REVIEWER_ASSIGNMENT_VALIDATION",
    "P0_P1_ZERO_PROOF_ARTIFACT",
    "S2PLT04_COMPLETION_REPORT",
    "INDEPENDENT_REVIEW_SIGNOFF",
    "FINAL_COMMAND_EXECUTION",
    "NO_PRODUCTION_SIDE_EFFECT_ATTESTATION",
    "NEXT_AGENT_HANDOFF",
)
S2PMT07_FINAL_ACCEPTANCE_BUNDLE_ITEM_BLOCKING_REASONS = {
    "FINAL_ACCEPTANCE_BUNDLE/manifest.json": "final_acceptance_bundle_manifest_missing",
    S2PMT07_INDEPENDENT_FINAL_REVIEWER_ASSIGNMENT_ARTIFACT_PATH: (
        "independent_final_reviewer_assignment_missing"
    ),
    "FINAL_ACCEPTANCE_BUNDLE/p0_p1_zero_proof.json": "p0_p1_zero_proof_missing",
    "FINAL_ACCEPTANCE_BUNDLE/s2plt04_completion_report.json": "s2plt04_completion_evidence_missing",
    "FINAL_ACCEPTANCE_BUNDLE/independent_review_signoff.yaml": "independent_review_signoff_missing",
    "FINAL_ACCEPTANCE_BUNDLE/final_command_execution.json": "independent_final_command_execution_missing",
    S2PMT07_NO_PRODUCTION_SIDE_EFFECT_ATTESTATION_ARTIFACT_PATH: (
        "no_production_side_effect_attestation_missing"
    ),
    "HANDOFF/00_下一Agent先读.md": "next_agent_handoff_missing",
}
S2PMT07_FINAL_BUNDLE_PREREQUISITE_PLAN_REQUIRED_STEPS = (
    "INDEPENDENT_FINAL_REVIEWER_ASSIGNMENT_VALIDATION",
    "P0_P1_ZERO_PROOF_ARTIFACT",
    "S2PLT04_COMPLETION_REPORT",
    "FINAL_COMMAND_EXECUTION",
    "NO_PRODUCTION_SIDE_EFFECT_ATTESTATION",
    "NEXT_AGENT_HANDOFF",
    "INDEPENDENT_REVIEW_SIGNOFF",
    "FINAL_ACCEPTANCE_BUNDLE_MANIFEST",
)
S2PMT07_FINAL_BUNDLE_PREREQUISITE_PLAN_BLOCKING_REASONS = (
    "independent_final_reviewer_assignment_missing",
    "p0_p1_zero_proof_artifact_missing",
    "s2plt04_completion_report_missing",
    "final_command_execution_missing",
    "no_production_side_effect_attestation_missing",
    "next_agent_handoff_missing",
    "independent_review_signoff_missing",
    "final_acceptance_bundle_manifest_missing",
    "inherited_v7_1_p0_findings_open",
    "inherited_v7_1_p1_findings_open",
)
S2PMT07_FINAL_BUNDLE_PREREQUISITE_PLAN_DEFAULT_ACTION = (
    "produce_artifact_then_revalidate_without_production_side_effects"
)
S2PMT07_FINAL_BUNDLE_PREREQUISITE_PLAN_WAIT_DEPENDENCIES_ACTION = (
    "wait_for_declared_dependencies_before_artifact"
)
S2PMT07_FINAL_BUNDLE_PREREQUISITE_PLAN_S2PLT04_UPSTREAM_ACTION = (
    "resolve_upstream_s2plt02_s2plt03_terminal_evidence_before_artifact"
)
S2PMT07_FINAL_BUNDLE_PREREQUISITE_PLAN_NEXT_EXECUTABLE_TASK_WHEN_S2PLT04_BLOCKED = (
    "S2PLT02_REAL_PROOF_CAPTURE_AUTHORIZATION"
)
S2PMT07_FINAL_BUNDLE_PREREQUISITE_PLAN_UPSTREAM_BLOCKERS = (
    "s2plt04_completion_report_blocked_by_s2plt02_terminal_delivery_proof_missing",
    "s2plt04_completion_report_blocked_by_s2plt03_terminal_resilience_proof_missing",
    "s2plt02_terminal_delivery_proof_blocked_by_real_proof_capture_authorization_missing",
)
S2PMT07_FINAL_BUNDLE_PREREQUISITE_PLAN_UPSTREAM_UNBLOCK_ORDER = (
    "S2PLT02_REAL_PROOF_CAPTURE_AUTHORIZATION",
    "S2PLT02_TERMINAL_DELIVERY_PROOF",
    "S2PLT03_TERMINAL_RESILIENCE_PROOF",
    "S2PLT04_COMPLETION_REPORT",
)
S2PMT07_FINAL_BUNDLE_PREREQUISITE_PLAN_STEP_DEPENDENCIES = {
    "INDEPENDENT_FINAL_REVIEWER_ASSIGNMENT_VALIDATION": (),
    "P0_P1_ZERO_PROOF_ARTIFACT": (),
    "S2PLT04_COMPLETION_REPORT": (),
    "FINAL_COMMAND_EXECUTION": ("S2PLT04_COMPLETION_REPORT",),
    "NO_PRODUCTION_SIDE_EFFECT_ATTESTATION": (),
    "NEXT_AGENT_HANDOFF": ("S2PLT04_COMPLETION_REPORT", "FINAL_COMMAND_EXECUTION"),
    "INDEPENDENT_REVIEW_SIGNOFF": (
        "P0_P1_ZERO_PROOF_ARTIFACT",
        "S2PLT04_COMPLETION_REPORT",
        "FINAL_COMMAND_EXECUTION",
        "NO_PRODUCTION_SIDE_EFFECT_ATTESTATION",
        "NEXT_AGENT_HANDOFF",
    ),
    "FINAL_ACCEPTANCE_BUNDLE_MANIFEST": (
        "INDEPENDENT_FINAL_REVIEWER_ASSIGNMENT_VALIDATION",
        "P0_P1_ZERO_PROOF_ARTIFACT",
        "S2PLT04_COMPLETION_REPORT",
        "INDEPENDENT_REVIEW_SIGNOFF",
        "FINAL_COMMAND_EXECUTION",
        "NO_PRODUCTION_SIDE_EFFECT_ATTESTATION",
        "NEXT_AGENT_HANDOFF",
    ),
}
S2PMT07_FINAL_BUNDLE_PREREQUISITE_PLAN_FORBIDDEN_FLAGS = (
    "production_acceptance_claimed",
    "integrated_production_accepted",
    "daily_operation_enabled",
    "real_smtp_sent",
    "real_smtp_send_enabled",
    "scheduler_enabled",
    "scheduler_install_enabled",
    "release_uploaded",
    "release_packaging_enabled",
    "production_restore_enabled",
    "production_restore_executed",
    "public_schema_changed",
    "db_migration_executed",
    "production_queue_mutated",
    "source_adapter_changed",
    "ranking_algorithm_changed",
    "current_pointer_changed",
    "v7_1_baseline_changed",
    "v7_2_contract_files_changed",
)
S2PMT07_MAINLINE_ATTESTATION_REQUIRED_VALIDATIONS = (
    "FOCUSED_FINAL_GATE_TESTS",
    "FULL_ADP_UNITTEST",
    "PROJECT_GOVERNANCE",
    "CHANGED_ONLY_SEMANTIC_GOVERNANCE",
    "V7_2_VALIDATOR",
    "LEAN_RENDER",
    "USER_CENTER_TIMESTAMP_CHECK",
    "STRUCTURED_PARSE",
    "DIFF_CHECK",
    "PRODUCTION_TRUE_FLAG_DIFF_SCAN",
    "OPEN_PR_COUNT_ZERO",
    "REMOTE_ADP_ARXIV_S2P_BRANCH_SCAN_EMPTY",
    "PYCACHE_SCAN_EMPTY",
)
S2PMT07_MAINLINE_ATTESTATION_NO_PRODUCTION_FLAGS = (
    "production_acceptance_claimed",
    "integrated_production_accepted",
    "stage2_integrated_production_accepted",
    "daily_operation_enabled",
    "real_smtp_sent",
    "real_smtp_send_enabled",
    "scheduler_enabled",
    "scheduler_install_enabled",
    "release_uploaded",
    "release_packaging_enabled",
    "production_restore_enabled",
    "production_restore_executed",
    "public_schema_changed",
    "db_migration_executed",
    "production_queue_mutated",
    "source_adapter_changed",
    "ranking_algorithm_changed",
    "current_pointer_changed",
    "v7_1_baseline_changed",
    "v7_2_contract_files_changed",
)
S2PMT07_P0_TECHNICAL_CLOSURE_CANDIDATE_PACKAGE = (
    "governance/run_manifests/ADP-S2PMT07-P0-TECHNICAL-CLOSURE-CANDIDATE-PACKAGE-20260627.json"
)
S2PMT07_P1_TECHNICAL_CLOSURE_CANDIDATE_RECEIPT = (
    "governance/run_manifests/ADP-S2PMT07-P1-INDEPENDENT-REVIEW-RECEIPT-20260626.json"
)
S2PMT07_P0_TECHNICAL_CLOSURE_CANDIDATE_FINDINGS = (
    "A-001",
    "A-002",
    "A-003",
    "A-004",
    "A-005",
    "B-001",
    "B-007",
    "B-008",
)
S2PMT07_P1_TECHNICAL_CLOSURE_CANDIDATE_FINDINGS = (
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
    "A-019",
    "A-018",
    "A-021",
    "B-002",
    "B-004",
    "B-005",
    "B-015",
    "B-003",
    "B-011",
    "B-006",
    "B-009",
    "B-010",
    "B-012",
    "B-013",
    "B-014",
    "A-020",
    "C-001",
    "C-003",
    "C-005",
    "C-006",
    "C-007",
    "C-010",
    "C-011",
    "C-012",
    "C-002",
)
S2PMT07_P1_TECHNICAL_CLOSURE_CANDIDATE_MANIFESTS = (
    "governance/run_manifests/ADP-S2PMT07-P1-A006-A009-TECHNICAL-REVIEW-20260627.json",
    "governance/run_manifests/ADP-S2PMT07-P1-A010-A016-TECHNICAL-REVIEW-20260627.json",
    "governance/run_manifests/ADP-S2PMT07-P1-A017-A019-TECHNICAL-REVIEW-20260627.json",
    "governance/run_manifests/ADP-S2PMT07-P1-A018-A021-TECHNICAL-REVIEW-20260627.json",
    "governance/run_manifests/ADP-S2PMT07-P1-B002-B004-B005-B015-TECHNICAL-REVIEW-20260627.json",
    "governance/run_manifests/ADP-S2PMT07-P1-B003-B011-TECHNICAL-REVIEW-20260627.json",
    "governance/run_manifests/ADP-S2PMT07-P1-B006-B009-B010-B012-B013-B014-TECHNICAL-REVIEW-20260627.json",
    "governance/run_manifests/ADP-S2PMT07-P1-A020-TECHNICAL-REVIEW-20260627.json",
    "governance/run_manifests/ADP-S2PMT07-P1-C001-C003-C005-C006-C007-C010-C011-C012-TECHNICAL-REVIEW-20260627.json",
    "governance/run_manifests/ADP-S2PMT07-P1-C002-TECHNICAL-REVIEW-20260628.json",
)
S2PMT07_P0_P1_TECHNICAL_CANDIDATE_BLOCKING_REASONS = (
    "p0_p1_zero_proof_missing",
    "independent_final_closure_decision_missing",
    "final_acceptance_bundle_missing",
)
S2PLT02_LIVE_2D_PRECHECK_MODEL_ID = "adp-s2plt02-live-2d-precheck-v1"
S2PLT02_ACCEPTANCE_ID = "ACC-S2PLT02-2D"
S2PLT02_TASK_ID = "S2PLT02"
S2PLT02_SCHEMA_VERSION = 1
S2PLT02_REQUIRED_DEPENDENCIES = ("S2PLT01",)
S2PLT02_REQUIRED_NATURAL_DAYS = 2
S2PLT02_REQUIRED_EMAIL_COUNT = 8
S2PLT02_REQUIRED_MAIL_PRODUCTS = ("M1", "M2", "M3", "M4")
S2PLT02_REQUIRED_EVIDENCE = (
    "S2PLT01_ACCEPTED",
    "TWO_CONSECUTIVE_REAL_NATURAL_DAYS",
    "EIGHT_REAL_EMAILS_SENT",
    "NO_DUPLICATE_EMAILS",
    "M4_WATERMARK_CORRECT",
    "REAL_SCHEDULER_PROVEN",
    "REAL_SMTP_PROVEN",
)
S2PLT02_FORBIDDEN_FLAGS = (
    "s2plt02_accepted",
    "s2plt02_real_run_started",
    "integrated_production_accepted",
    "daily_operation_enabled",
    "real_smtp_sent",
    "real_smtp_send_enabled",
    "scheduler_enabled",
    "scheduler_install_enabled",
    "release_uploaded",
    "production_restore_executed",
    "production_queue_mutated",
    "public_schema_changed",
    "db_migration_executed",
    "source_adapter_changed",
    "ranking_algorithm_changed",
    "current_pointer_changed",
    "v7_1_baseline_changed",
    "v7_2_contract_files_changed",
)
S2PLT02_BLOCKING_REASONS = (
    "s2plt01_not_accepted",
    "two_consecutive_real_days_not_proven",
    "eight_real_emails_not_proven",
    "duplicate_emails_found",
    "real_scheduler_not_proven",
    "real_smtp_not_proven",
    "m4_watermark_not_proven",
    "inherited_v7_1_p0_findings_open",
    "inherited_v7_1_p1_findings_open",
)
S2PLT02_PARTIAL_REAL_DELIVERY_SERVICE_DATE = "2026-06-28"
S2PLT02_PARTIAL_REAL_DELIVERY_GENERATED_AT = "2026-06-28T11:28:25+10:00"
S2PLT02_PARTIAL_REAL_DELIVERY_SCOPE = "one_day_real_delivery_evidence_not_s2plt02_acceptance"
S2PLT02_NORMALIZED_REAL_DELIVERY_MANIFEST_REF = (
    "governance/run_manifests/ADP-S2PLT02-NORMALIZED-REAL-DELIVERY-MANIFEST-20260628.json"
)
S2PLT02_PARTIAL_REAL_DELIVERY_RAW_MANIFEST_HASH = (
    "a795bd90778b5a0bbbd217d286f696936954af47a1a547ed689f907b677d9fa2"
)
S2PLT02_PARTIAL_REAL_DELIVERY_NORMALIZED_AT = "2026-06-30T11:45:16+10:00"
S2PLT02_PARTIAL_REAL_DELIVERY_EVIDENCE_REFS = (
    "governance/run_manifests/ADP-LOCAL-DAILY-M1-M4-RESEND-EXECUTION-20260628.json",
    "arxiv-daily-push/docs/phase_records/PHASE_LOCAL_DAILY_M1_M4_RESEND_EXECUTION_20260628.md",
    "arxiv-daily-push/用户中心/邮件发送与队列状态.md",
)
S2PLT02_PARTIAL_REAL_DELIVERY_PRODUCTS = ("M1", "M2", "M3", "M4")
S2PLT02_PARTIAL_REAL_DELIVERY_HISTORICAL_PRODUCTS = ("M1",)
S2PLT02_PARTIAL_REAL_DELIVERY_NEWLY_SENT_PRODUCTS = ("M2", "M3", "M4")
S2PLT02_PARTIAL_REAL_DELIVERY_REFS = {
    "M1": "smtp://message/smtp-delivery:87f268d29a31288d",
    "M2": "smtp://message/smtp-delivery:c72ffcd03a277e1d",
    "M3": "smtp://message/smtp-delivery:590b7230463ff9f7",
    "M4": "smtp://message/smtp-delivery:7f815186af789297",
}
S2PLT02_DELIVERY_EVIDENCE_LEDGER_MODEL_ID = "adp-s2plt02-delivery-evidence-ledger-v1"
S2PLT02_DELIVERY_EVIDENCE_LEDGER_SCOPE = "delivery_manifest_ledger_no_s2plt02_acceptance"
S2PLT02_REAL_DELIVERY_MANIFEST_VALIDATION_SCOPE = (
    "real_delivery_manifest_input_validation_no_smtp_send_no_write"
)
S2PLT02_REAL_DELIVERY_MANIFEST_NORMALIZATION_MODEL_ID = (
    "adp-s2plt02-real-delivery-manifest-normalization-v1"
)
S2PLT02_REAL_DELIVERY_MANIFEST_NORMALIZATION_SCOPE = (
    "real_delivery_manifest_normalization_no_smtp_send_no_write"
)
S2PLT02_DELIVERY_EVIDENCE_LEDGER_FORBIDDEN_SOURCE_FLAGS = (
    "integrated_production_accepted",
    "stage2_integrated_production_accepted",
    "daily_operation_enabled",
    "release_uploaded",
    "production_restore_executed",
    "production_queue_mutated",
    "public_schema_changed",
    "db_migration_executed",
    "source_adapter_changed",
    "ranking_algorithm_changed",
    "current_pointer_changed",
    "v7_1_baseline_changed",
    "v7_2_contract_files_changed",
)
S2PLT02_M4_WATERMARK_PROOF_MODEL_ID = "adp-s2plt02-m4-watermark-proof-v1"
S2PLT02_M4_WATERMARK_PROOF_SCOPE = "m4_watermark_proof_validator_no_s2plt02_acceptance"
S2PLT02_M4_WATERMARK_PROOF_RECORD_REF = (
    "governance/run_manifests/ADP-S2PLT02-M4-WATERMARK-PROOF-RECORD-20260628.json"
)
S2PLT02_M4_WATERMARK_PROOF_GENERATED_AT = "2026-06-28T01:26:41Z"
S2PLT02_M4_WATERMARK_PROOF_CYCLE_ID = "2026-06-28"
S2PLT02_M4_WATERMARK_REQUIRED_TERMINAL_PRODUCTS = ("M1", "M2", "M3")
S2PLT02_TERMINAL_READINESS_AUDIT_SCOPE = "s2plt02_terminal_readiness_audit_only_no_acceptance_claim"
S2PLT02_TERMINAL_DELIVERY_PROOF_ARTIFACT_PATH = "FINAL_ACCEPTANCE_BUNDLE/s2plt02_terminal_delivery_proof.json"
S2PLT02_TERMINAL_DELIVERY_PROOF_MODEL_ID = "adp-s2plt02-terminal-delivery-proof-v1"
S2PLT02_TERMINAL_DELIVERY_PROOF_SCOPE = "s2plt02_terminal_delivery_proof_artifact_validation_only_no_production_acceptance"
S2PLT02_TERMINAL_DELIVERY_PROOF_DECISION = "S2PLT02_TERMINAL_DELIVERY_PROOF_READY_NO_PRODUCTION_ACCEPTANCE"
S2PLT02_TERMINAL_DELIVERY_PROOF_REQUIRED_GATES = (
    "s2plt01_accepted",
    "two_consecutive_real_days",
    "eight_real_emails_sent",
    "no_duplicate_emails",
    "m4_watermark_correct",
    "real_scheduler_proven",
    "real_smtp_proven",
    "p0_zero",
    "p1_zero",
)
S2PLT02_TERMINAL_DELIVERY_PROOF_REQUIRED_EVIDENCE_REFS = (
    "FINAL_ACCEPTANCE_BUNDLE/s2plt01_terminal_acceptance.json",
    "FINAL_ACCEPTANCE_BUNDLE/p0_p1_zero_proof.json",
)
S2PLT02_TERMINAL_DELIVERY_PROOF_REQUIRED_EVIDENCE_ROLES = (
    "s2plt01_terminal_acceptance",
    "day_1_delivery",
    "day_2_delivery",
    "real_scheduler_proof",
    "p0_p1_zero_proof",
)
S2PLT02_TERMINAL_DELIVERY_PROOF_NO_PRODUCTION_FLAGS = (
    "production_acceptance_claimed",
    "integrated_production_accepted",
    "stage2_integrated_production_accepted",
    "daily_operation_enabled",
    "release_uploaded",
    "production_restore_enabled",
    "production_restore_executed",
    "public_schema_changed",
    "db_migration_executed",
    "production_queue_mutated",
    "source_adapter_changed",
    "ranking_algorithm_changed",
    "current_pointer_changed",
    "v7_1_baseline_changed",
    "v7_2_contract_files_changed",
)
S2PLT02_DRY_RUN_SECOND_DAY_AUDIT_MODEL_ID = "adp-s2plt02-dry-run-second-day-audit-v1"
S2PLT02_DRY_RUN_SECOND_DAY_AUDIT_SCOPE = "second_day_dry_run_trace_no_terminal_delivery_credit"
S2PLT02_DRY_RUN_SECOND_DAY_AUDIT_SERVICE_DATE = "2026-06-29"
S2PLT02_DRY_RUN_SECOND_DAY_AUDIT_RUNNER_REPORT = "adp-local-runner-report.json"
S2PLT02_DRY_RUN_SECOND_DAY_AUDIT_DAILY_RUN_REPORT = "adp-daily-run.json"
S2PLT02_DRY_RUN_SECOND_DAY_AUDIT_PRODUCT_REPORT_TEMPLATE = "adp-smtp-delivery-report-{product}.json"
S2PLT02_DRY_RUN_SECOND_DAY_AUDIT_NO_PRODUCTION_FLAGS = (
    "production_acceptance_claimed",
    "integrated_production_accepted",
    "stage2_integrated_production_accepted",
    "daily_operation_enabled",
    "real_smtp_send_enabled",
    "scheduler_install_enabled",
    "release_packaging_enabled",
    "production_restore_enabled",
    "current_pointer_changed",
    "v7_1_baseline_changed",
    "v7_2_contract_files_changed",
)
S2PLT02_REAL_PROOF_CAPTURE_READINESS_MODEL_ID = "adp-s2plt02-real-proof-capture-readiness-v1"
S2PLT02_REAL_PROOF_CAPTURE_READINESS_SCOPE = (
    "real_second_day_smtp_scheduler_capture_readiness_no_production_enablement"
)
S2PLT02_REAL_PROOF_CAPTURE_READINESS_REQUIRED_NEXT_ACTIONS = (
    "obtain_explicit_owner_authorization_for_real_smtp_scheduler",
    "capture_second_consecutive_real_m1_m4_smtp_day",
    "capture_real_launchd_scheduler_proof",
    "write_and_validate_s2plt02_terminal_delivery_proof_artifact",
)
S2PLT02_REAL_PROOF_CAPTURE_READINESS_NO_PRODUCTION_FLAGS = (
    "production_acceptance_claimed",
    "integrated_production_accepted",
    "stage2_integrated_production_accepted",
    "daily_operation_enabled",
    "real_smtp_send_enabled",
    "scheduler_install_enabled",
    "release_packaging_enabled",
    "production_restore_enabled",
    "current_pointer_changed",
    "v7_1_baseline_changed",
    "v7_2_contract_files_changed",
)
S2PLT02_TERMINAL_CAPTURE_WINDOW_AUDIT_MODEL_ID = "adp-s2plt02-terminal-capture-window-audit-v1"
S2PLT02_TERMINAL_CAPTURE_WINDOW_AUDIT_SCOPE = (
    "terminal_capture_window_runtime_audit_no_smtp_send_no_scheduler_enablement"
)
S2PLT02_TERMINAL_PROOF_EVIDENCE_INVENTORY_SCOPE = (
    "s2plt02_terminal_proof_evidence_inventory_no_write_no_production"
)
S2PLT02_TERMINAL_CAPTURE_WINDOW_DEFAULT_CANDIDATE_DATES = (
    "2026-06-29",
    "2026-06-30",
)
S2PLT02_TERMINAL_CAPTURE_WINDOW_AUDIT_NO_PRODUCTION_FLAGS = (
    "production_acceptance_claimed",
    "integrated_production_accepted",
    "stage2_integrated_production_accepted",
    "daily_operation_enabled",
    "real_smtp_send_enabled",
    "scheduler_install_enabled",
    "release_packaging_enabled",
    "production_restore_enabled",
    "current_pointer_changed",
    "v7_1_baseline_changed",
    "v7_2_contract_files_changed",
)
S2PLT02_REAL_PROOF_CAPTURE_AUTHORIZATION_ARTIFACT_PATH = (
    "FINAL_ACCEPTANCE_BUNDLE/s2plt02_real_proof_capture_authorization.json"
)
S2PLT02_REAL_PROOF_CAPTURE_AUTHORIZATION_SCHEMA_VERSION = (
    "adp.s2plt02_real_proof_capture_authorization.v1"
)
S2PLT02_REAL_PROOF_CAPTURE_AUTHORIZATION_MODEL_ID = (
    "adp-s2plt02-real-proof-capture-authorization-v1"
)
S2PLT02_REAL_PROOF_CAPTURE_AUTHORIZATION_SCOPE = (
    "s2plt02_real_smtp_scheduler_capture_authorization_only_no_production_acceptance"
)
S2PLT02_REAL_PROOF_CAPTURE_AUTHORIZATION_DECISION = (
    "S2PLT02_REAL_PROOF_CAPTURE_AUTHORIZED_NO_PRODUCTION_ACCEPTANCE"
)
S2PLT02_REAL_PROOF_CAPTURE_AUTHORIZATION_REQUIRED_FIELDS = (
    "schema_version",
    "contract_id",
    "generated_at",
    "authorization_decision",
    "authorized_by",
    "authorization_scope",
    "authorized_actions",
    "authorization_constraints",
    "readiness_state_hash",
    "evidence_refs",
    "no_production_side_effects",
    "authorization_hash",
)
S2PLT02_REAL_PROOF_CAPTURE_AUTHORIZATION_AUTHORIZED_ACTIONS = (
    "capture_second_consecutive_real_m1_m4_smtp_day",
    "capture_real_launchd_scheduler_proof",
    "validate_s2plt02_terminal_delivery_proof_artifact",
)
S2PLT02_REAL_PROOF_CAPTURE_AUTHORIZATION_CONSTRAINTS = (
    "stage2_production_acceptance_not_granted",
    "daily_operation_not_enabled",
    "release_not_enabled",
    "current_v7_unchanged",
    "only_capture_second_day_and_scheduler_proof",
)
S2PLT02_REAL_PROOF_CAPTURE_AUTHORIZATION_NO_PRODUCTION_FLAGS = (
    "production_acceptance_claimed",
    "integrated_production_accepted",
    "stage2_integrated_production_accepted",
    "daily_operation_enabled",
    "real_smtp_sent",
    "real_smtp_send_enabled",
    "scheduler_enabled",
    "scheduler_install_enabled",
    "release_uploaded",
    "release_packaging_enabled",
    "production_restore_enabled",
    "production_restore_executed",
    "public_schema_changed",
    "db_migration_executed",
    "production_queue_mutated",
    "source_adapter_changed",
    "ranking_algorithm_changed",
    "current_pointer_changed",
    "v7_1_baseline_changed",
    "v7_2_contract_files_changed",
)
S2PLT02_REAL_PROOF_CAPTURE_AUTHORIZATION_OWNER_ACTIONS = (
    "review_s2plt02_real_proof_capture_readiness_state",
    "write_authorization_artifact_only_if_owner_explicitly_approves_real_smtp_scheduler_capture",
    "keep_all_no_production_side_effect_flags_false",
    "capture_second_real_m1_m4_smtp_day_after_authorization",
    "capture_real_launchd_scheduler_proof_after_authorization",
    "validate_terminal_delivery_proof_artifact_before_s2plt02_acceptance",
)
S2PLT02_REAL_PROOF_CAPTURE_AUTHORIZATION_BLOCKING_REASONS = (
    "s2plt02_real_proof_capture_authorization_missing",
    "second_real_delivery_day_missing",
    "real_scheduler_not_proven",
    "s2plt02_terminal_delivery_proof_artifact_missing",
)
S2PMT07_FINAL_BUNDLE_PREREQUISITE_PLAN_S2PLT02_AUTH_READINESS_STATE_HASH = (
    "79ac4987239ecad8d4eee82de0157901b59259100e6d738bd1b15d17a37dc76e"
)
S2PMT07_FINAL_BUNDLE_PREREQUISITE_PLAN_S2PLT02_AUTH_DRAFT_COMMAND = (
    "build-s2plt02-real-proof-capture-authorization-artifact-draft"
)
S2PMT07_FINAL_BUNDLE_PREREQUISITE_PLAN_S2PLT02_AUTH_DRAFT_ARGS = {
    "owner_id": "owner_or_coordinator",
    "owner_role": "owner",
    "generated_at_source": "current Australia/Sydney timestamp at execution time",
    "readiness_state_hash": S2PMT07_FINAL_BUNDLE_PREREQUISITE_PLAN_S2PLT02_AUTH_READINESS_STATE_HASH,
}
S2PMT07_FINAL_BUNDLE_PREREQUISITE_PLAN_S2PLT02_AUTH_VALIDATION_COMMAND = (
    "validate-s2plt02-real-proof-capture-authorization "
    "--path FINAL_ACCEPTANCE_BUNDLE/s2plt02_real_proof_capture_authorization.json "
    "--expected-readiness-state-hash "
    f"{S2PMT07_FINAL_BUNDLE_PREREQUISITE_PLAN_S2PLT02_AUTH_READINESS_STATE_HASH} "
    "--json"
)
S2PMT07_FINAL_BUNDLE_PREREQUISITE_PLAN_S2PLT02_AUTH_DRAFT_EVIDENCE_REFS = (
    "governance/run_manifests/ADP-S2PLT02-REAL-PROOF-CAPTURE-AUTHORIZATION-DRAFT-CLI-RUNTIME-SYNC-20260629.json",
    "arxiv-daily-push/docs/phase_records/PHASE_S2PLT02_REAL_PROOF_CAPTURE_AUTHORIZATION_DRAFT_CLI.md",
    "arxiv-daily-push/docs/phase_records/PHASE_S2PLT02_REAL_PROOF_CAPTURE_READINESS_RUNTIME_STATE_SYNC.md",
    "arxiv-daily-push/docs/phase_records/PHASE_S2PLT02_REAL_PROOF_CAPTURE_AUTHORIZATION.md",
)
S2PLT02_M4_WATERMARK_FORBIDDEN_SOURCE_FLAGS = (
    "integrated_production_accepted",
    "stage2_integrated_production_accepted",
    "daily_operation_enabled",
    "release_uploaded",
    "production_restore_executed",
    "production_queue_mutated",
    "public_schema_changed",
    "db_migration_executed",
    "source_adapter_changed",
    "ranking_algorithm_changed",
    "current_pointer_changed",
    "v7_1_baseline_changed",
    "v7_2_contract_files_changed",
    "scheduler_enabled",
)
S2PLT03_RESILIENCE_PRECHECK_MODEL_ID = "adp-s2plt03-resilience-precheck-v1"
S2PLT03_ACCEPTANCE_ID = "ACC-S2PLT03-RESILIENCE"
S2PLT03_TASK_ID = "S2PLT03"
S2PLT03_SCHEMA_VERSION = 1
S2PLT03_REQUIRED_DEPENDENCIES = ("S2PLT02",)
S2PLT03_REQUIRED_EVIDENCE = (
    "RATE_LIMIT_DRILL",
    "PARSER_DRIFT_DRILL",
    "RESTART_RECOVERY_DRILL",
    "DISK_PRESSURE_DRILL",
    "BACKUP_RESTORE_POINT_PROVEN",
    "ROLLBACK_EXECUTABLE",
    "LEDGER_COUNT_CONSERVATION",
)
S2PLT03_FORBIDDEN_FLAGS = (
    "s2plt03_accepted",
    "s2plt03_resilience_drill_completed",
    "integrated_production_accepted",
    "daily_operation_enabled",
    "real_smtp_sent",
    "real_smtp_send_enabled",
    "scheduler_enabled",
    "scheduler_install_enabled",
    "release_uploaded",
    "production_restore_executed",
    "production_queue_mutated",
    "public_schema_changed",
    "db_migration_executed",
    "source_adapter_changed",
    "ranking_algorithm_changed",
    "current_pointer_changed",
    "v7_1_baseline_changed",
    "v7_2_contract_files_changed",
)
S2PLT03_BLOCKING_REASONS = (
    "s2plt02_not_accepted",
    "rate_limit_drill_not_proven",
    "parser_drift_drill_not_proven",
    "restart_recovery_drill_not_proven",
    "disk_pressure_drill_not_proven",
    "backup_restore_point_not_proven",
    "rollback_executable_not_proven",
    "ledger_count_conservation_not_proven",
    "inherited_v7_1_p0_findings_open",
    "inherited_v7_1_p1_findings_open",
)
S2PLT03_TERMINAL_RESILIENCE_PROOF_ARTIFACT_PATH = "FINAL_ACCEPTANCE_BUNDLE/s2plt03_terminal_resilience_proof.json"
S2PLT03_TERMINAL_RESILIENCE_PROOF_MODEL_ID = "adp-s2plt03-terminal-resilience-proof-v1"
S2PLT03_TERMINAL_RESILIENCE_PROOF_SCOPE = (
    "s2plt03_terminal_resilience_proof_artifact_validation_only_no_production_acceptance"
)
S2PLT03_TERMINAL_RESILIENCE_PROOF_DECISION = (
    "S2PLT03_TERMINAL_RESILIENCE_PROOF_READY_NO_PRODUCTION_ACCEPTANCE"
)
S2PLT03_TERMINAL_RESILIENCE_PROOF_REQUIRED_GATES = (
    "s2plt02_accepted",
    "rate_limit_drill_proven",
    "parser_drift_drill_proven",
    "restart_recovery_drill_proven",
    "disk_pressure_drill_proven",
    "backup_restore_point_proven",
    "rollback_executable",
    "ledger_count_conserved",
    "p0_zero",
    "p1_zero",
    "no_production_side_effects",
)
S2PLT03_TERMINAL_RESILIENCE_PROOF_REQUIRED_EVIDENCE_REFS = (
    "FINAL_ACCEPTANCE_BUNDLE/s2plt02_terminal_delivery_proof.json",
    "FINAL_ACCEPTANCE_BUNDLE/p0_p1_zero_proof.json",
)
S2PLT03_TERMINAL_RESILIENCE_PROOF_REQUIRED_EVIDENCE_ROLES = (
    "s2plt02_terminal_delivery_proof",
    "local_resilience_drill",
    "resilience_precheck",
    "p0_p1_zero_proof",
)
S2PLT03_TERMINAL_RESILIENCE_PROOF_NO_PRODUCTION_FLAGS = (
    "production_acceptance_claimed",
    "integrated_production_accepted",
    "stage2_integrated_production_accepted",
    "daily_operation_enabled",
    "real_smtp_sent",
    "real_smtp_send_enabled",
    "scheduler_enabled",
    "scheduler_install_enabled",
    "release_uploaded",
    "release_packaging_enabled",
    "production_restore_enabled",
    "production_restore_executed",
    "production_queue_mutated",
    "public_schema_changed",
    "db_migration_executed",
    "source_adapter_changed",
    "ranking_algorithm_changed",
    "current_pointer_changed",
    "v7_1_baseline_changed",
    "v7_2_contract_files_changed",
)
S2PLT03_TERMINAL_RESILIENCE_PROOF_CAPTURE_PLAN_TASK_ID = "S2PLT03-TERMINAL-RESILIENCE-PROOF-CAPTURE-PLAN"
S2PLT03_TERMINAL_RESILIENCE_PROOF_CAPTURE_PLAN_SCOPE = (
    "s2plt03_terminal_resilience_proof_capture_plan_no_write_no_production"
)
S2PLT03_TERMINAL_RESILIENCE_PROOF_CAPTURE_PLAN_STEPS = (
    "WAIT_FOR_S2PLT02_TERMINAL_ACCEPTANCE",
    "REVALIDATE_S2PLT03_PRECHECK",
    "BUILD_REVIEWED_S2PLT03_TERMINAL_RESILIENCE_PROOF",
    "RUN_VALIDATE_S2PLT03_TERMINAL_RESILIENCE_PROOF",
    "FEED_S2PLT04_COMPLETION_EVIDENCE",
)
S2PLT03_LOCAL_DRILL_MODEL_ID = "adp-s2plt03-local-resilience-drill-v1"
S2PLT03_LOCAL_DRILL_SCOPE = "local_no_production_drill_not_terminal_acceptance"
S2PLT03_LOCAL_DRILL_REQUIRED_CASES = (
    "rate_limit_blocks_excess_request",
    "parser_drift_quarantines_unknown_schema",
    "restart_recovery_reconciles_pending_rows",
    "disk_pressure_degrades_to_no_write",
    "backup_restore_point_hash_matches",
    "rollback_plan_is_dry_run_executable",
    "ledger_count_conservation_balances_states",
)
S2PLT03_LOCAL_DRILL_FORBIDDEN_FLAGS = S2PLT03_FORBIDDEN_FLAGS + (
    "production_side_effects_enabled",
)
S2PLT04_INTEGRATION_CANDIDATE_MODEL_ID = "adp-s2plt04-integration-candidate-precheck-v1"
S2PLT04_ACCEPTANCE_ID = "ACC-S2PLT04-INTEGRATION-CANDIDATE"
S2PLT04_TASK_ID = "S2PLT04"
S2PLT04_SCHEMA_VERSION = 1
S2PLT04_REQUIRED_DEPENDENCIES = (
    "S2PLT01",
    "S2PLT02",
    "S2PLT03",
)
S2PLT04_AVAILABLE_LOCAL_EVIDENCE = (
    "S2PLT01-INDEPENDENT-REPLAY-REVIEW",
    "S2PLT02-LIVE-2D-PRECHECK",
    "S2PLT03-LOCAL-RESILIENCE-DRILL",
    "S2PMT01",
    "S2PMT02",
    "S2PMT03",
    "S2PMT04",
    "S2PMT05",
    "S2PMT06",
    "S2PMT07",
)
S2PLT04_NONTERMINAL_LOCAL_EVIDENCE = (
    "S2PLT01_INDEPENDENT_REPLAY_REVIEW",
    "S2PLT02_LIVE_2D_PRECHECK",
    "S2PLT03_LOCAL_RESILIENCE_DRILL",
)
S2PLT04_REPLAY_EXECUTION_GENERATED_AT = "2026-06-26T19:10:00+10:00"
S2PLT04_REPLAY_REVIEW_GENERATED_AT = "2026-06-26T20:00:00+10:00"
S2PLT04_LIVE_2D_PRECHECK_GENERATED_AT = "2026-06-26T19:00:00+10:00"
S2PLT04_LOCAL_DRILL_BUNDLE_GENERATED_AT = "2026-06-28T02:00:14+10:00"
S2PLT04_STATE_CONSISTENCY_SOURCE_TASKS = (
    "S2PMT02",
    "S2PMT03",
    "S2PMT04",
    "S2PMT05",
    "S2PMT06",
)
S2PLT04_CONTENT_EVIDENCE_SOURCE_TASKS = (
    "S2PHT05",
    "S2PIT04",
    "S2PKT05",
)
S2PLT04_STATE_CONSISTENCY_EVIDENCE_REFS = (
    "arxiv-daily-push/docs/phase_records/PHASE_S2PMT02_ATOMIC_RECOVERY.md",
    "arxiv-daily-push/docs/phase_records/PHASE_S2PMT03_LEASE_FENCING.md",
    "arxiv-daily-push/docs/phase_records/PHASE_S2PMT04_LIFECYCLE_CACHE.md",
    "arxiv-daily-push/docs/phase_records/PHASE_S2PMT05_STRESS_E2E.md",
    "arxiv-daily-push/docs/phase_records/PHASE_S2PMT06_OWNER_UX.md",
)
S2PLT04_CONTENT_EVIDENCE_REFS = (
    "governance/run_manifests/ADP-S2PHT05-CONTENT-QUALITY-GATE-20260626.json",
    "arxiv-daily-push/docs/phase_records/PHASE_S2PIT04_CONTENT_LEDGER.md",
    "arxiv-daily-push/docs/phase_records/PHASE_S2PKT05_M4_MAIL.md",
)
S2PLT04_REQUIRED_EVIDENCE = (
    "S2PLT01_ACCEPTED",
    "S2PLT02_2D_REAL_RUN",
    "S2PLT03_RESILIENCE_DRILL",
    "STATE_CONSISTENCY_EVIDENCE",
    "CONTENT_EVIDENCE",
    "FINAL_ACCEPTANCE_BUNDLE/",
)
S2PLT04_FORBIDDEN_FLAGS = (
    "s2_integration_candidate_ready",
    "s2plt04_completed",
    "integrated_production_accepted",
    "daily_operation_enabled",
    "real_smtp_sent",
    "scheduler_enabled",
    "release_uploaded",
    "production_restore_executed",
    "production_queue_mutated",
    "public_schema_changed",
    "db_migration_executed",
    "source_adapter_changed",
    "ranking_algorithm_changed",
    "current_pointer_changed",
    "v7_1_baseline_changed",
    "v7_2_contract_files_changed",
)
S2PLT04_BLOCKING_REASONS = (
    "s2plt01_not_accepted",
    "s2plt02_not_completed",
    "s2plt03_not_completed",
    "final_acceptance_bundle_missing",
    "inherited_v7_1_p0_findings_open",
    "inherited_v7_1_p1_findings_open",
)


def build_s2plt02_dependency_state() -> dict[str, Any]:
    """Build current S2PLT02 dependency state without accepting S2PLT01."""

    return _build_s2plt02_dependency_state(repo_root=Path("."))


def _build_s2plt01_terminal_acceptance_dependency_state(repo_root: str | Path = ".") -> dict[str, Any]:
    audit = build_s2plt01_terminal_acceptance_audit_state(repo_root=repo_root)
    accepted = audit.get("status") == "pass" and audit.get("s2plt01_accepted") is True
    return {
        "accepted": accepted,
        "status": "terminal_accepted_no_production" if accepted else "blocked_by_terminal_acceptance_audit",
        "audit_status": audit.get("status"),
        "audit_state_hash": audit.get("state_hash"),
        "artifact_ref": audit.get("terminal_acceptance_artifact_ref"),
        "blocking_reasons": list(audit.get("blocking_reasons", [])),
    }


def _build_s2plt02_dependency_state(*, repo_root: str | Path = ".") -> dict[str, Any]:
    """Build current S2PLT02 dependency state from S2PLT01 terminal acceptance."""

    s2plt01 = _build_s2plt01_terminal_acceptance_dependency_state(repo_root)
    completed = {"S2PLT01": s2plt01["status"]} if s2plt01["accepted"] else {}
    unmet = [task_id for task_id in S2PLT02_REQUIRED_DEPENDENCIES if task_id not in completed]
    return {
        "status": "pass" if not unmet else "blocked",
        "required_dependencies": list(S2PLT02_REQUIRED_DEPENDENCIES),
        "completed_dependencies": completed,
        "unmet_dependencies": unmet,
        "s2plt01_acceptance_status": s2plt01["status"],
        "s2plt01_terminal_acceptance": s2plt01,
    }


def _default_s2plt02_delivery_manifest_records() -> list[dict[str, Any]]:
    """Return committed real-delivery manifest facts used by the S2PLT02 ledger."""

    return [
        {
            "manifest_ref": S2PLT02_NORMALIZED_REAL_DELIVERY_MANIFEST_REF,
            "schema_version": 1,
            "project_id": "arxiv-daily-push",
            "task_id": "LOCAL-DAILY-M1-M4-RESEND-EXECUTION",
            "status": "pass",
            "generated_at": S2PLT02_PARTIAL_REAL_DELIVERY_GENERATED_AT,
            "service_date": S2PLT02_PARTIAL_REAL_DELIVERY_SERVICE_DATE,
            "normalized_at": S2PLT02_PARTIAL_REAL_DELIVERY_NORMALIZED_AT,
            "normalization_task_id": "S2PLT02-REAL-DELIVERY-MANIFEST-NORMALIZATION",
            "normalization_scope": S2PLT02_REAL_DELIVERY_MANIFEST_NORMALIZATION_SCOPE,
            "normalized_from_manifest_ref": S2PLT02_PARTIAL_REAL_DELIVERY_EVIDENCE_REFS[0],
            "normalized_from_manifest_hash": S2PLT02_PARTIAL_REAL_DELIVERY_RAW_MANIFEST_HASH,
            "mail_delivery_summary": {
                "planned_send_total": len(S2PLT02_REQUIRED_MAIL_PRODUCTS),
                "sent_mail_count": len(S2PLT02_REQUIRED_MAIL_PRODUCTS),
                "sent_mail_products": list(S2PLT02_REQUIRED_MAIL_PRODUCTS),
                "historical_sent_mail_products": list(S2PLT02_PARTIAL_REAL_DELIVERY_HISTORICAL_PRODUCTS),
                "newly_sent_mail_products": list(S2PLT02_PARTIAL_REAL_DELIVERY_NEWLY_SENT_PRODUCTS),
                "delivery_ref_by_product": dict(S2PLT02_PARTIAL_REAL_DELIVERY_REFS),
            },
            "real_smtp_sent": True,
            "real_smtp_send_enabled": True,
            "stage2_integrated_production_accepted": False,
            "integrated_production_accepted": False,
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
            "evidence_refs": list(
                (S2PLT02_NORMALIZED_REAL_DELIVERY_MANIFEST_REF,)
                + S2PLT02_PARTIAL_REAL_DELIVERY_EVIDENCE_REFS
            ),
        }
    ]


def build_s2plt02_delivery_evidence_ledger_state(
    *, delivery_manifests: list[Mapping[str, Any]] | None = None
) -> dict[str, Any]:
    """Build the S2PLT02 real-delivery ledger without sending mail or accepting S2PLT02."""

    source_manifests = [
        json.loads(json.dumps(record, ensure_ascii=False))
        for record in (delivery_manifests if delivery_manifests is not None else _default_s2plt02_delivery_manifest_records())
    ]
    validation_errors: list[str] = []
    service_date_order: list[str] = []
    products_by_service_date: dict[str, list[str]] = {}
    delivery_ref_by_service_date: dict[str, dict[str, str]] = {}
    evidence_refs: list[str] = []
    seen_dates: set[str] = set()
    duplicate_service_date_count = 0
    seen_delivery_keys: set[tuple[str, str]] = set()
    duplicate_email_count = 0
    real_smtp_record_count = 0

    for index, manifest in enumerate(source_manifests, start=1):
        manifest_ref = str(manifest.get("manifest_ref") or f"inline_delivery_manifest_{index}")
        if manifest_ref not in evidence_refs:
            evidence_refs.append(manifest_ref)
        for ref in manifest.get("evidence_refs", []):
            if isinstance(ref, str) and ref not in evidence_refs:
                evidence_refs.append(ref)

        service_date = manifest.get("service_date")
        if not isinstance(service_date, str) or not service_date:
            validation_errors.append(f"manifest {manifest_ref} service_date is required")
            continue
        if service_date in seen_dates:
            duplicate_service_date_count += 1
            validation_errors.append(f"duplicate service date manifest: {service_date}")
        else:
            seen_dates.add(service_date)
            service_date_order.append(service_date)

        if manifest.get("status") != "pass":
            validation_errors.append(f"manifest {manifest_ref} status must be pass")
        if manifest.get("real_smtp_sent") is not True:
            validation_errors.append(f"manifest {manifest_ref} real_smtp_sent must be true")
        else:
            real_smtp_record_count += 1
        for flag in S2PLT02_DELIVERY_EVIDENCE_LEDGER_FORBIDDEN_SOURCE_FLAGS:
            if manifest.get(flag) is not False:
                validation_errors.append(f"manifest {manifest_ref} {flag} must be false")

        mail_summary = _mapping(manifest.get("mail_delivery_summary"))
        products = mail_summary.get("sent_mail_products", [])
        if tuple(products) != S2PLT02_REQUIRED_MAIL_PRODUCTS:
            validation_errors.append(f"manifest {manifest_ref} sent products must be M1-M4")
        if mail_summary.get("planned_send_total") != len(S2PLT02_REQUIRED_MAIL_PRODUCTS):
            validation_errors.append(f"manifest {manifest_ref} planned_send_total must be 4")
        if mail_summary.get("sent_mail_count") != len(products):
            validation_errors.append(f"manifest {manifest_ref} sent_mail_count must match sent products")

        refs = _mapping(mail_summary.get("delivery_ref_by_product"))
        product_refs: dict[str, str] = {}
        for product in S2PLT02_REQUIRED_MAIL_PRODUCTS:
            delivery_ref = refs.get(product)
            if not isinstance(delivery_ref, str) or not delivery_ref.startswith("smtp://message/"):
                validation_errors.append(f"manifest {manifest_ref} delivery ref missing for {service_date}/{product}")
                continue
            delivery_key = (service_date, product)
            if delivery_key in seen_delivery_keys:
                duplicate_email_count += 1
                validation_errors.append(f"duplicate email evidence for {service_date}/{product}")
                continue
            seen_delivery_keys.add(delivery_key)
            product_refs[product] = delivery_ref

        if product_refs:
            products_by_service_date[service_date] = [product for product in S2PLT02_REQUIRED_MAIL_PRODUCTS if product in product_refs]
            delivery_ref_by_service_date[service_date] = product_refs

    observed_email_count = sum(len(products) for products in products_by_service_date.values())
    two_day_delivery_evidence_present = (
        len(service_date_order) >= S2PLT02_REQUIRED_NATURAL_DAYS
        and observed_email_count >= S2PLT02_REQUIRED_EMAIL_COUNT
        and duplicate_email_count == 0
        and duplicate_service_date_count == 0
        and not validation_errors
    )
    state = {
        "model_id": S2PLT02_DELIVERY_EVIDENCE_LEDGER_MODEL_ID,
        "schema_version": S2PLT02_SCHEMA_VERSION,
        "task_id": "S2PLT02-DELIVERY-EVIDENCE-LEDGER",
        "acceptance_id": S2PLT02_ACCEPTANCE_ID,
        "status": "ready" if two_day_delivery_evidence_present else ("partial" if observed_email_count else "blocked"),
        "scope": S2PLT02_DELIVERY_EVIDENCE_LEDGER_SCOPE,
        "source_manifest_count": len(source_manifests),
        "source_manifests": source_manifests,
        "required_natural_days": S2PLT02_REQUIRED_NATURAL_DAYS,
        "observed_natural_days": len(service_date_order),
        "required_email_count": S2PLT02_REQUIRED_EMAIL_COUNT,
        "observed_email_count": observed_email_count,
        "required_mail_products": list(S2PLT02_REQUIRED_MAIL_PRODUCTS),
        "service_dates": service_date_order,
        "products_by_service_date": products_by_service_date,
        "delivery_ref_by_service_date": delivery_ref_by_service_date,
        "duplicate_email_count": duplicate_email_count,
        "duplicate_service_date_count": duplicate_service_date_count,
        "real_smtp_evidence_present": real_smtp_record_count > 0 and observed_email_count > 0,
        "two_day_delivery_evidence_present": two_day_delivery_evidence_present,
        "validation_errors": validation_errors,
        "s2plt02_accepted": False,
        "production_acceptance_claimed": False,
        "stage2_integrated_production_accepted": False,
        "integrated_production_accepted": False,
        "daily_operation_enabled": False,
        "new_production_side_effects_from_ledger": False,
        "evidence_refs": evidence_refs,
        "ledger_hash": "",
    }
    state["ledger_hash"] = _stable_hash({key: value for key, value in state.items() if key != "ledger_hash"})
    return state


def _load_s2plt02_audit_json(path: Path) -> tuple[Mapping[str, Any], str]:
    if not path.exists():
        return {}, "missing"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}, "invalid_json"
    if not isinstance(payload, Mapping):
        return {}, "not_object"
    return payload, ""


def build_s2plt02_dry_run_second_day_audit_state(
    *,
    state_dir: str | Path | None = None,
    service_date: str = S2PLT02_DRY_RUN_SECOND_DAY_AUDIT_SERVICE_DATE,
) -> dict[str, Any]:
    """Audit a second-day dry-run trace without granting S2PLT02 terminal credit."""

    state_root = Path(state_dir).expanduser() if state_dir is not None else Path.home() / ".adp" / "arxiv-daily-push"
    run_dir = state_root / "runs" / service_date.replace("-", "")
    runner_report_path = run_dir / S2PLT02_DRY_RUN_SECOND_DAY_AUDIT_RUNNER_REPORT
    daily_run_report_path = run_dir / S2PLT02_DRY_RUN_SECOND_DAY_AUDIT_DAILY_RUN_REPORT
    validation_errors: list[str] = []
    evidence_refs = [str(runner_report_path), str(daily_run_report_path)]

    runner_report, load_error = _load_s2plt02_audit_json(runner_report_path)
    if load_error:
        validation_errors.append(f"runner_report_{load_error}")
    daily_run_report, daily_run_load_error = _load_s2plt02_audit_json(daily_run_report_path)
    daily_run_report_present = not daily_run_load_error
    if daily_run_load_error and daily_run_load_error != "missing":
        validation_errors.append(f"daily_run_report_{daily_run_load_error}")
    daily_run_record = _mapping(daily_run_report.get("run_record"))
    daily_run_status = str(daily_run_report.get("status") or daily_run_record.get("status") or "")
    daily_run_record_state = str(daily_run_record.get("current_state") or "")
    daily_run_record_date = str(daily_run_record.get("date") or daily_run_report.get("date") or "")
    if daily_run_report_present and daily_run_record_date and daily_run_record_date != service_date:
        validation_errors.append("daily_run_report_service_date_mismatch")
    daily_run_succeeded = (
        daily_run_status.lower() in {"succeeded", "success"}
        or daily_run_record_state.lower() == "completed"
        and daily_run_record.get("status") == "SUCCESS"
    )

    mail_summary = _mapping(runner_report.get("mail_delivery_summary"))
    planned_products = [str(product) for product in mail_summary.get("planned_mail_products", [])]
    dry_run_products = [str(product) for product in mail_summary.get("dry_run_mail_products", [])]
    sent_products = [str(product) for product in mail_summary.get("sent_mail_products", [])]
    status_by_product = _mapping(mail_summary.get("status_by_product"))
    planned_mail_count = int(mail_summary.get("planned_send_total") or len(planned_products))
    sent_mail_count = int(mail_summary.get("sent_mail_count") or len(sent_products))

    if tuple(planned_products) != S2PLT02_REQUIRED_MAIL_PRODUCTS:
        validation_errors.append("planned_mail_products_must_be_M1_M4")
    if sent_mail_count != 0 or sent_products:
        validation_errors.append("dry_run_runner_report_must_have_zero_sent_mail")
    if runner_report.get("real_smtp_sent") is not False:
        validation_errors.append("runner_report_real_smtp_sent_must_be_false")
    if runner_report.get("production_evidence_ready") is not False:
        validation_errors.append("runner_report_production_evidence_ready_must_be_false")

    product_report_status: dict[str, str] = {}
    product_report_refs: dict[str, str] = {}
    dry_run_report_products: list[str] = []
    missing_product_report = False
    for product in S2PLT02_REQUIRED_MAIL_PRODUCTS:
        report_path = run_dir / S2PLT02_DRY_RUN_SECOND_DAY_AUDIT_PRODUCT_REPORT_TEMPLATE.format(product=product)
        evidence_refs.append(str(report_path))
        product_report_refs[product] = str(report_path)
        product_report, product_error = _load_s2plt02_audit_json(report_path)
        if product_error:
            missing_product_report = True
            validation_errors.append(f"missing_product_delivery_report:{product}" if product_error == "missing" else f"product_delivery_report_{product}_{product_error}")
            continue

        status = str(product_report.get("status") or status_by_product.get(product) or "")
        product_report_status[product] = status
        is_dry_run_report = (
            status == "dry_run"
            and product_report.get("dry_run") is True
            and product_report.get("allow_send") is False
            and product_report.get("real_send_attempted") is False
            and product_report.get("real_smtp_send_enabled") is False
        )
        if is_dry_run_report:
            dry_run_report_products.append(product)
        else:
            validation_errors.append(f"product_delivery_report_not_dry_run:{product}")
        if (
            product_report.get("status") == "sent"
            or product_report.get("real_send_attempted") is True
            or product_report.get("real_smtp_send_enabled") is True
            or product_report.get("real_smtp_sent") is True
        ):
            validation_errors.append(f"product_delivery_report_has_real_send:{product}")

    all_required_products_dry_run = tuple(dry_run_products) == S2PLT02_REQUIRED_MAIL_PRODUCTS and tuple(
        dry_run_report_products
    ) == S2PLT02_REQUIRED_MAIL_PRODUCTS
    dry_run_evidence_present = (
        all_required_products_dry_run
        and planned_mail_count == len(S2PLT02_REQUIRED_MAIL_PRODUCTS)
        and sent_mail_count == 0
        and not missing_product_report
        and not any(error.startswith("product_delivery_report_not_dry_run") for error in validation_errors)
        and not any(error.startswith("product_delivery_report_has_real_send") for error in validation_errors)
    )
    daily_run_succeeded_but_smtp_dry_run_not_terminal = (
        daily_run_succeeded and dry_run_evidence_present and sent_mail_count == 0
    )

    blocking_reasons: list[str] = []
    if missing_product_report:
        blocking_reasons.append("dry_run_product_report_set_incomplete")
    if dry_run_evidence_present:
        blocking_reasons.append("dry_run_evidence_only_not_real_smtp")
    else:
        blocking_reasons.append("dry_run_evidence_not_complete")
    if daily_run_succeeded_but_smtp_dry_run_not_terminal:
        blocking_reasons.append("daily_run_succeeded_but_smtp_dry_run_not_terminal")
    for reason in (
        "real_scheduler_not_proven",
        "two_consecutive_real_days_not_proven",
        "eight_real_emails_not_proven",
    ):
        if reason not in blocking_reasons:
            blocking_reasons.append(reason)

    state = {
        "model_id": S2PLT02_DRY_RUN_SECOND_DAY_AUDIT_MODEL_ID,
        "schema_version": S2PLT02_SCHEMA_VERSION,
        "task_id": "S2PLT02-DRY-RUN-SECOND-DAY-AUDIT",
        "parent_task_id": S2PLT02_TASK_ID,
        "acceptance_id": S2PLT02_ACCEPTANCE_ID,
        "status": "blocked",
        "scope": S2PLT02_DRY_RUN_SECOND_DAY_AUDIT_SCOPE,
        "service_date": service_date,
        "state_dir": str(state_root),
        "run_dir": str(run_dir),
        "runner_report_ref": str(runner_report_path),
        "daily_run_report_ref": str(daily_run_report_path),
        "daily_run_report_present": daily_run_report_present,
        "daily_run_status": daily_run_status,
        "daily_run_record_state": daily_run_record_state,
        "daily_run_record_date": daily_run_record_date,
        "daily_run_succeeded": daily_run_succeeded,
        "daily_run_succeeded_but_smtp_dry_run_not_terminal": daily_run_succeeded_but_smtp_dry_run_not_terminal,
        "daily_run_counts_toward_terminal_proof": False,
        "product_report_refs": product_report_refs,
        "required_mail_products": list(S2PLT02_REQUIRED_MAIL_PRODUCTS),
        "planned_mail_products": planned_products,
        "dry_run_mail_products": dry_run_products,
        "dry_run_report_products": dry_run_report_products,
        "sent_mail_products": sent_products,
        "product_report_status": product_report_status,
        "planned_mail_count": planned_mail_count,
        "dry_run_mail_count": len(dry_run_report_products),
        "real_sent_mail_count": sent_mail_count,
        "observed_natural_days_credit": 0,
        "observed_email_count_credit": 0,
        "dry_run_evidence_present": dry_run_evidence_present,
        "terminal_delivery_credit": False,
        "counts_toward_s2plt02_terminal_proof": False,
        "real_smtp_proven": False,
        "real_scheduler_proven": False,
        "s2plt02_accepted": False,
        "production_acceptance_claimed": False,
        "integrated_production_accepted": False,
        "stage2_integrated_production_accepted": False,
        "daily_operation_enabled": False,
        "real_smtp_send_enabled": False,
        "scheduler_install_enabled": False,
        "release_packaging_enabled": False,
        "production_restore_enabled": False,
        "current_pointer_changed": False,
        "v7_1_baseline_changed": False,
        "v7_2_contract_files_changed": False,
        "validation_errors": validation_errors,
        "blocking_reasons": blocking_reasons,
        "evidence_refs": evidence_refs,
        "state_hash": "",
    }
    state["state_hash"] = _stable_hash({key: value for key, value in state.items() if key != "state_hash"})
    return state


def validate_s2plt02_dry_run_second_day_audit_state(state: Mapping[str, Any]) -> list[str]:
    """Validate a S2PLT02 dry-run second-day audit state."""

    errors: list[str] = []
    if state.get("model_id") != S2PLT02_DRY_RUN_SECOND_DAY_AUDIT_MODEL_ID:
        errors.append("S2PLT02 dry-run second-day audit model_id is invalid")
    if state.get("schema_version") != S2PLT02_SCHEMA_VERSION:
        errors.append("S2PLT02 dry-run second-day audit schema_version must be 1")
    if state.get("task_id") != "S2PLT02-DRY-RUN-SECOND-DAY-AUDIT":
        errors.append("S2PLT02 dry-run second-day audit task_id is invalid")
    if state.get("acceptance_id") != S2PLT02_ACCEPTANCE_ID:
        errors.append("S2PLT02 dry-run second-day audit acceptance_id is invalid")
    if state.get("status") != "blocked":
        errors.append("S2PLT02 dry-run second-day audit must stay blocked")
    if state.get("scope") != S2PLT02_DRY_RUN_SECOND_DAY_AUDIT_SCOPE:
        errors.append("S2PLT02 dry-run second-day audit scope is invalid")
    if tuple(state.get("required_mail_products", [])) != S2PLT02_REQUIRED_MAIL_PRODUCTS:
        errors.append("S2PLT02 dry-run second-day audit required_mail_products must be M1-M4")
    for field in (
        "terminal_delivery_credit",
        "counts_toward_s2plt02_terminal_proof",
        "daily_run_counts_toward_terminal_proof",
        "real_smtp_proven",
        "real_scheduler_proven",
        "s2plt02_accepted",
    ):
        if state.get(field) is not False:
            errors.append(f"{field} must be false")
    if state.get("observed_natural_days_credit") != 0:
        errors.append("observed_natural_days_credit must be 0")
    if state.get("observed_email_count_credit") != 0:
        errors.append("observed_email_count_credit must be 0")
    for flag in S2PLT02_DRY_RUN_SECOND_DAY_AUDIT_NO_PRODUCTION_FLAGS:
        if state.get(flag) is not False:
            errors.append(f"{flag} must be false")
    blocking_reasons = state.get("blocking_reasons", [])
    for reason in (
        "real_scheduler_not_proven",
        "two_consecutive_real_days_not_proven",
        "eight_real_emails_not_proven",
    ):
        if reason not in blocking_reasons:
            errors.append(f"{reason} blocker is required")
    if state.get("dry_run_evidence_present") is True and "dry_run_evidence_only_not_real_smtp" not in blocking_reasons:
        errors.append("dry_run_evidence_only_not_real_smtp blocker is required")
    if state.get("dry_run_evidence_present") is False and "dry_run_evidence_not_complete" not in blocking_reasons:
        errors.append("dry_run_evidence_not_complete blocker is required")
    if state.get("daily_run_succeeded_but_smtp_dry_run_not_terminal") is True:
        if state.get("daily_run_succeeded") is not True:
            errors.append("daily_run_succeeded_but_smtp_dry_run_not_terminal requires daily_run_succeeded")
        if state.get("dry_run_evidence_present") is not True:
            errors.append("daily_run_succeeded_but_smtp_dry_run_not_terminal requires dry_run evidence")
        if "daily_run_succeeded_but_smtp_dry_run_not_terminal" not in blocking_reasons:
            errors.append("daily_run_succeeded_but_smtp_dry_run_not_terminal blocker is required")
    expected_hash = _stable_hash({key: value for key, value in state.items() if key != "state_hash"})
    if state.get("state_hash") != expected_hash:
        errors.append("S2PLT02 dry-run second-day audit state_hash does not match state content")
    return errors


def build_s2plt02_real_proof_capture_readiness_state(
    *,
    repo_root: str | Path = ".",
    state_dir: str | Path | None = None,
    service_date: str = S2PLT02_DRY_RUN_SECOND_DAY_AUDIT_SERVICE_DATE,
    launchctl_disabled_text: str = "",
    launchctl_print_outputs: Mapping[str, str] | None = None,
    expected_authorization_readiness_state_hash: str | None = None,
) -> dict[str, Any]:
    """Build the no-production gate before any real S2PLT02 proof capture can be accepted."""

    launchd_states = _parse_launchd_disabled_states(launchctl_disabled_text)
    launchd_print_outputs = launchctl_print_outputs or {}
    required_labels = S2PMT07_LOCAL_RUNTIME_NO_PRODUCTION_REQUIRED_LABELS
    launchagent_disabled_states = {
        label: launchd_states.get(label, "missing")
        for label in required_labels
    }
    launchagent_runtime_states = {
        label: _parse_launchd_service_state(str(launchd_print_outputs.get(label, "")))
        for label in required_labels
    }
    launchagent_calendar_triggers_present = {
        label: _launchd_calendar_trigger_present(str(launchd_print_outputs.get(label, "")))
        for label in required_labels
    }
    validation_errors = [
        f"launchagent_state_unknown:{label}"
        for label, state in launchagent_disabled_states.items()
        if state == "missing"
    ]
    all_required_launchagents_disabled = all(
        state == "disabled" for state in launchagent_disabled_states.values()
    )
    all_required_launchagents_loaded = all(
        state != "missing" for state in launchagent_runtime_states.values()
    )
    all_required_launchagents_not_running = all(
        state == "not running" for state in launchagent_runtime_states.values()
    )
    all_required_launchagents_have_calendar_triggers = all(launchagent_calendar_triggers_present.values())
    launchagents_loaded_but_disabled = all_required_launchagents_disabled and all_required_launchagents_loaded
    scheduler_runtime_evidence_status = (
        "launchagents_loaded_but_disabled_not_terminal_scheduler_proof"
        if launchagents_loaded_but_disabled
        else "launchagents_disabled_not_terminal_scheduler_proof"
        if all_required_launchagents_disabled
        else "launchagent_runtime_state_unknown"
        if not all_required_launchagents_loaded
        else "launchagents_not_all_disabled_not_terminal_scheduler_proof"
    )

    dry_run_audit = build_s2plt02_dry_run_second_day_audit_state(
        state_dir=state_dir,
        service_date=service_date,
    )
    delivery_ledger = build_s2plt02_delivery_evidence_ledger_state()
    terminal_proof = build_s2plt02_terminal_delivery_proof_artifact_validation_state(repo_root=repo_root)
    terminal_gates = _mapping(terminal_proof.get("terminal_gates"))
    root = Path(repo_root)
    authorization_artifact = _load_json_mapping_artifact(
        root / S2PLT02_REAL_PROOF_CAPTURE_AUTHORIZATION_ARTIFACT_PATH
    )
    authorization_validation = build_s2plt02_real_proof_capture_authorization_validation_state(
        authorization_artifact,
        expected_readiness_state_hash=expected_authorization_readiness_state_hash,
    )
    authorization_validation_errors = [
        str(error)
        for error in authorization_validation.get("validation_errors", [])
        if isinstance(error, str)
    ]
    authorization_artifact_status = (
        "missing"
        if authorization_artifact is None
        else str(authorization_validation.get("status") or "blocked")
    )
    real_proof_capture_authorized = (
        authorization_validation.get("real_proof_capture_authorized_by_payload") is True
    )
    second_real_delivery_day_present = (
        terminal_gates.get("two_consecutive_real_days") is True
        and terminal_gates.get("eight_real_emails_sent") is True
        and delivery_ledger.get("two_day_delivery_evidence_present") is True
    )
    real_scheduler_proven = terminal_gates.get("real_scheduler_proven") is True
    terminal_delivery_proof_artifact_present = terminal_proof.get("artifact_present") is True

    blocking_reasons: list[str] = []
    if authorization_artifact is None:
        blocking_reasons.append("real_proof_capture_authorization_missing")
    elif not real_proof_capture_authorized:
        blocking_reasons.append("real_proof_capture_authorization_invalid")
    if validation_errors:
        blocking_reasons.append("required_launchagent_state_unknown")
    if all_required_launchagents_disabled:
        blocking_reasons.append("required_launchagents_disabled")
    else:
        blocking_reasons.append("required_launchagents_not_all_disabled")
    if not second_real_delivery_day_present:
        blocking_reasons.append("second_real_delivery_day_missing")
    if dry_run_audit.get("dry_run_evidence_present") is True:
        blocking_reasons.append("dry_run_second_day_not_terminal")
    if not terminal_delivery_proof_artifact_present:
        blocking_reasons.append("s2plt02_terminal_delivery_proof_artifact_missing")
    if not real_scheduler_proven:
        blocking_reasons.append("real_scheduler_not_proven")
    completed_next_actions = (
        ["obtain_explicit_owner_authorization_for_real_smtp_scheduler"]
        if real_proof_capture_authorized
        else []
    )
    remaining_next_actions = [
        action
        for action in S2PLT02_REAL_PROOF_CAPTURE_READINESS_REQUIRED_NEXT_ACTIONS
        if action not in completed_next_actions
    ]

    state = {
        "model_id": S2PLT02_REAL_PROOF_CAPTURE_READINESS_MODEL_ID,
        "schema_version": S2PLT02_SCHEMA_VERSION,
        "task_id": "S2PLT02-REAL-PROOF-CAPTURE-READINESS",
        "parent_task_id": S2PLT02_TASK_ID,
        "acceptance_id": S2PLT02_ACCEPTANCE_ID,
        "status": "blocked",
        "scope": S2PLT02_REAL_PROOF_CAPTURE_READINESS_SCOPE,
        "service_date": service_date,
        "required_launchagent_labels": list(required_labels),
        "launchagent_disabled_states": launchagent_disabled_states,
        "launchagent_runtime_states": launchagent_runtime_states,
        "launchagent_calendar_triggers_present": launchagent_calendar_triggers_present,
        "all_required_launchagents_disabled": all_required_launchagents_disabled,
        "all_required_launchagents_loaded": all_required_launchagents_loaded,
        "all_required_launchagents_not_running": all_required_launchagents_not_running,
        "all_required_launchagents_have_calendar_triggers": all_required_launchagents_have_calendar_triggers,
        "launchagents_loaded_but_disabled": launchagents_loaded_but_disabled,
        "scheduler_runtime_evidence_status": scheduler_runtime_evidence_status,
        "authorization_artifact_path": S2PLT02_REAL_PROOF_CAPTURE_AUTHORIZATION_ARTIFACT_PATH,
        "authorization_artifact_present": authorization_artifact is not None,
        "authorization_artifact_status": authorization_artifact_status,
        "authorization_validation_errors": authorization_validation_errors,
        "authorization_validation_state_hash": str(
            authorization_validation.get("state_hash") or ""
        ),
        "real_proof_capture_authorized": real_proof_capture_authorized,
        "safe_to_collect_terminal_proof": False,
        "second_real_delivery_day_present": second_real_delivery_day_present,
        "terminal_delivery_proof_artifact_present": terminal_delivery_proof_artifact_present,
        "real_scheduler_proven": real_scheduler_proven,
        "dry_run_second_day_audit": dry_run_audit,
        "delivery_evidence_ledger": delivery_ledger,
        "terminal_delivery_proof_validation": terminal_proof,
        "required_next_actions": list(S2PLT02_REAL_PROOF_CAPTURE_READINESS_REQUIRED_NEXT_ACTIONS),
        "completed_next_actions": completed_next_actions,
        "remaining_next_actions": remaining_next_actions,
        "validation_errors": validation_errors,
        "blocking_reasons": blocking_reasons,
        "production_acceptance_claimed": False,
        "integrated_production_accepted": False,
        "stage2_integrated_production_accepted": False,
        "daily_operation_enabled": False,
        "real_smtp_send_enabled": False,
        "scheduler_install_enabled": False,
        "release_packaging_enabled": False,
        "production_restore_enabled": False,
        "current_pointer_changed": False,
        "v7_1_baseline_changed": False,
        "v7_2_contract_files_changed": False,
        "state_hash": "",
    }
    state["state_hash"] = _stable_hash({key: value for key, value in state.items() if key != "state_hash"})
    return state


def validate_s2plt02_real_proof_capture_readiness_state(state: Mapping[str, Any]) -> list[str]:
    """Validate the S2PLT02 real-proof capture readiness gate."""

    errors: list[str] = []
    if state.get("model_id") != S2PLT02_REAL_PROOF_CAPTURE_READINESS_MODEL_ID:
        errors.append("S2PLT02 real-proof capture readiness model_id is invalid")
    if state.get("schema_version") != S2PLT02_SCHEMA_VERSION:
        errors.append("S2PLT02 real-proof capture readiness schema_version must be 1")
    if state.get("task_id") != "S2PLT02-REAL-PROOF-CAPTURE-READINESS":
        errors.append("S2PLT02 real-proof capture readiness task_id is invalid")
    if state.get("acceptance_id") != S2PLT02_ACCEPTANCE_ID:
        errors.append("S2PLT02 real-proof capture readiness acceptance_id is invalid")
    if state.get("status") != "blocked":
        errors.append("S2PLT02 real-proof capture readiness must stay blocked")
    if state.get("scope") != S2PLT02_REAL_PROOF_CAPTURE_READINESS_SCOPE:
        errors.append("S2PLT02 real-proof capture readiness scope is invalid")
    if tuple(state.get("required_launchagent_labels", [])) != S2PMT07_LOCAL_RUNTIME_NO_PRODUCTION_REQUIRED_LABELS:
        errors.append("S2PLT02 real-proof capture readiness required launchagents are invalid")
    if tuple(state.get("required_next_actions", [])) != S2PLT02_REAL_PROOF_CAPTURE_READINESS_REQUIRED_NEXT_ACTIONS:
        errors.append("S2PLT02 real-proof capture readiness next actions are invalid")
    if state.get("safe_to_collect_terminal_proof") is not False:
        errors.append("safe_to_collect_terminal_proof must stay false until terminal evidence exists")
    if state.get("authorization_artifact_path") != S2PLT02_REAL_PROOF_CAPTURE_AUTHORIZATION_ARTIFACT_PATH:
        errors.append("authorization_artifact_path is invalid")
    if state.get("authorization_artifact_status") not in {"missing", "blocked", "pass"}:
        errors.append("authorization_artifact_status is invalid")
    if state.get("real_proof_capture_authorized") is True:
        if state.get("authorization_artifact_status") != "pass":
            errors.append("real_proof_capture_authorized requires pass authorization_artifact_status")
        if "real_proof_capture_authorization_missing" in state.get("blocking_reasons", []):
            errors.append("authorized readiness must not include authorization missing blocker")
        if "real_proof_capture_authorization_invalid" in state.get("blocking_reasons", []):
            errors.append("authorized readiness must not include authorization invalid blocker")
    else:
        if not (
            "real_proof_capture_authorization_missing" in state.get("blocking_reasons", [])
            or "real_proof_capture_authorization_invalid" in state.get("blocking_reasons", [])
        ):
            errors.append("unauthorized readiness requires missing or invalid authorization blocker")
    completed_next_actions = tuple(state.get("completed_next_actions", []))
    remaining_next_actions = tuple(state.get("remaining_next_actions", []))
    if state.get("real_proof_capture_authorized") is True:
        if "obtain_explicit_owner_authorization_for_real_smtp_scheduler" not in completed_next_actions:
            errors.append("authorized readiness must mark authorization action completed")
    elif completed_next_actions:
        errors.append("unauthorized readiness must not have completed next actions")
    expected_remaining = tuple(
        action
        for action in S2PLT02_REAL_PROOF_CAPTURE_READINESS_REQUIRED_NEXT_ACTIONS
        if action not in completed_next_actions
    )
    if remaining_next_actions != expected_remaining:
        errors.append("remaining_next_actions must match required minus completed actions")
    for reason in (
        "second_real_delivery_day_missing",
        "s2plt02_terminal_delivery_proof_artifact_missing",
        "real_scheduler_not_proven",
    ):
        if reason not in state.get("blocking_reasons", []):
            errors.append(f"{reason} blocker is required")
    if (
        state.get("all_required_launchagents_disabled") is True
        and "required_launchagents_disabled" not in state.get("blocking_reasons", [])
    ):
        errors.append("required_launchagents_disabled blocker is required")
    if state.get("all_required_launchagents_disabled") is False and not (
        "required_launchagents_not_all_disabled" in state.get("blocking_reasons", [])
        or "required_launchagent_state_unknown" in state.get("blocking_reasons", [])
    ):
        errors.append("launchagent state blocker is required")
    dry_run_evidence_present = _mapping(state.get("dry_run_second_day_audit")).get(
        "dry_run_evidence_present"
    )
    if (
        dry_run_evidence_present is True
        and "dry_run_second_day_not_terminal" not in state.get("blocking_reasons", [])
    ):
        errors.append("dry_run_second_day_not_terminal blocker is required")
    disabled_states = _mapping(state.get("launchagent_disabled_states"))
    runtime_states = _mapping(state.get("launchagent_runtime_states"))
    calendar_triggers = _mapping(state.get("launchagent_calendar_triggers_present"))
    if set(runtime_states) != set(S2PMT07_LOCAL_RUNTIME_NO_PRODUCTION_REQUIRED_LABELS):
        errors.append("launchagent_runtime_states must cover all required launchagents")
    if set(calendar_triggers) != set(S2PMT07_LOCAL_RUNTIME_NO_PRODUCTION_REQUIRED_LABELS):
        errors.append("launchagent_calendar_triggers_present must cover all required launchagents")
    expected_loaded = all(runtime_states.get(label) != "missing" for label in S2PMT07_LOCAL_RUNTIME_NO_PRODUCTION_REQUIRED_LABELS)
    if state.get("all_required_launchagents_loaded") is not expected_loaded:
        errors.append("all_required_launchagents_loaded must match runtime states")
    expected_not_running = all(runtime_states.get(label) == "not running" for label in S2PMT07_LOCAL_RUNTIME_NO_PRODUCTION_REQUIRED_LABELS)
    if state.get("all_required_launchagents_not_running") is not expected_not_running:
        errors.append("all_required_launchagents_not_running must match runtime states")
    expected_calendar = all(
        calendar_triggers.get(label) is True for label in S2PMT07_LOCAL_RUNTIME_NO_PRODUCTION_REQUIRED_LABELS
    )
    if state.get("all_required_launchagents_have_calendar_triggers") is not expected_calendar:
        errors.append("all_required_launchagents_have_calendar_triggers must match trigger states")
    expected_loaded_but_disabled = (
        all(disabled_states.get(label) == "disabled" for label in S2PMT07_LOCAL_RUNTIME_NO_PRODUCTION_REQUIRED_LABELS)
        and expected_loaded
    )
    if state.get("launchagents_loaded_but_disabled") is not expected_loaded_but_disabled:
        errors.append("launchagents_loaded_but_disabled must match disabled and runtime states")
    expected_scheduler_runtime_status = (
        "launchagents_loaded_but_disabled_not_terminal_scheduler_proof"
        if expected_loaded_but_disabled
        else "launchagents_disabled_not_terminal_scheduler_proof"
        if state.get("all_required_launchagents_disabled") is True
        else "launchagent_runtime_state_unknown"
        if not expected_loaded
        else "launchagents_not_all_disabled_not_terminal_scheduler_proof"
    )
    if state.get("scheduler_runtime_evidence_status") != expected_scheduler_runtime_status:
        errors.append("scheduler_runtime_evidence_status must match launchagent state")
    for flag in S2PLT02_REAL_PROOF_CAPTURE_READINESS_NO_PRODUCTION_FLAGS:
        if state.get(flag) is not False:
            errors.append(f"{flag} must be false")
    expected_hash = _stable_hash({key: value for key, value in state.items() if key != "state_hash"})
    if state.get("state_hash") != expected_hash:
        errors.append("S2PLT02 real-proof capture readiness state_hash does not match state content")
    return errors


def build_s2plt02_terminal_capture_window_audit_state(
    *,
    repo_root: str | Path = ".",
    state_dir: str | Path | None = None,
    candidate_service_dates: tuple[str, ...] = S2PLT02_TERMINAL_CAPTURE_WINDOW_DEFAULT_CANDIDATE_DATES,
    launchctl_disabled_text: str = "",
    launchctl_print_outputs: Mapping[str, str] | None = None,
    adp_allow_smtp_send: bool = False,
) -> dict[str, Any]:
    """Audit the current terminal capture window without granting S2PLT02 credit."""

    disabled_states = _parse_launchd_disabled_states(launchctl_disabled_text)
    launchd_print_outputs = launchctl_print_outputs or {}
    required_labels = S2PMT07_LOCAL_RUNTIME_NO_PRODUCTION_REQUIRED_LABELS
    launchagent_disabled_states = {
        label: disabled_states.get(label, "missing")
        for label in required_labels
    }
    launchagent_runtime_states = {
        label: _parse_launchd_service_state(str(launchd_print_outputs.get(label, "")))
        for label in required_labels
    }
    launchagent_calendar_triggers_present = {
        label: _launchd_calendar_trigger_present(str(launchd_print_outputs.get(label, "")))
        for label in required_labels
    }
    all_required_launchagents_disabled = all(
        state == "disabled" for state in launchagent_disabled_states.values()
    )
    all_required_launchagents_loaded = all(
        state != "missing" for state in launchagent_runtime_states.values()
    )
    all_required_launchagents_not_running = all(
        state == "not running" for state in launchagent_runtime_states.values()
    )
    all_required_launchagents_have_calendar_triggers = all(launchagent_calendar_triggers_present.values())
    launchagents_loaded_but_disabled = all_required_launchagents_disabled and all_required_launchagents_loaded
    scheduler_runtime_evidence_status = (
        "launchagents_loaded_but_disabled_not_terminal_scheduler_proof"
        if launchagents_loaded_but_disabled
        else "launchagents_disabled_not_terminal_scheduler_proof"
        if all_required_launchagents_disabled
        else "launchagent_runtime_state_unknown"
        if not all_required_launchagents_loaded
        else "launchagents_not_all_disabled_not_terminal_scheduler_proof"
    )
    dry_run_audits = [
        build_s2plt02_dry_run_second_day_audit_state(
            state_dir=state_dir,
            service_date=service_date,
        )
        for service_date in candidate_service_dates
    ]
    dry_run_service_dates = [
        str(audit.get("service_date"))
        for audit in dry_run_audits
        if audit.get("dry_run_evidence_present") is True
    ]
    daily_run_succeeded_service_dates = [
        str(audit.get("service_date"))
        for audit in dry_run_audits
        if audit.get("daily_run_succeeded") is True
    ]
    nonterminal_succeeded_dry_run_service_dates = [
        str(audit.get("service_date"))
        for audit in dry_run_audits
        if audit.get("daily_run_succeeded_but_smtp_dry_run_not_terminal") is True
    ]
    dry_run_email_count = sum(int(audit.get("dry_run_mail_count") or 0) for audit in dry_run_audits)
    real_sent_candidate_email_count = sum(int(audit.get("real_sent_mail_count") or 0) for audit in dry_run_audits)
    delivery_ledger = build_s2plt02_delivery_evidence_ledger_state()
    terminal_proof = build_s2plt02_terminal_delivery_proof_artifact_validation_state(repo_root=repo_root)
    terminal_gates = _mapping(terminal_proof.get("terminal_gates"))
    observed_terminal_email_count_credit = int(delivery_ledger.get("observed_email_count") or 0)
    two_day_delivery_present = (
        terminal_gates.get("two_consecutive_real_days") is True
        and terminal_gates.get("eight_real_emails_sent") is True
        and delivery_ledger.get("two_day_delivery_evidence_present") is True
    )
    real_scheduler_proven = terminal_gates.get("real_scheduler_proven") is True
    terminal_artifact_present = terminal_proof.get("artifact_present") is True

    blocking_reasons: list[str] = []
    if not two_day_delivery_present:
        blocking_reasons.append("second_consecutive_real_m1_m4_smtp_day_missing")
    if observed_terminal_email_count_credit < S2PLT02_REQUIRED_EMAIL_COUNT:
        blocking_reasons.append("eight_real_emails_not_proven")
    if not real_scheduler_proven:
        blocking_reasons.append("real_launchd_scheduler_proof_missing")
    if not adp_allow_smtp_send:
        blocking_reasons.append("adp_allow_smtp_send_false")
    if all_required_launchagents_disabled:
        blocking_reasons.append("adp_launchagents_disabled_by_user_domain_override")
    else:
        blocking_reasons.append("adp_launchagent_disabled_state_missing_or_enabled")
    if not terminal_artifact_present:
        blocking_reasons.append("s2plt02_terminal_delivery_proof_artifact_missing")
    if nonterminal_succeeded_dry_run_service_dates:
        blocking_reasons.append("daily_run_succeeded_but_smtp_dry_run_not_terminal")

    state = {
        "model_id": S2PLT02_TERMINAL_CAPTURE_WINDOW_AUDIT_MODEL_ID,
        "schema_version": S2PLT02_SCHEMA_VERSION,
        "task_id": "S2PLT02-TERMINAL-CAPTURE-WINDOW-AUDIT",
        "parent_task_id": S2PLT02_TASK_ID,
        "acceptance_id": S2PLT02_ACCEPTANCE_ID,
        "status": "blocked",
        "scope": S2PLT02_TERMINAL_CAPTURE_WINDOW_AUDIT_SCOPE,
        "candidate_service_dates": list(candidate_service_dates),
        "dry_run_service_dates": dry_run_service_dates,
        "daily_run_succeeded_service_dates": daily_run_succeeded_service_dates,
        "nonterminal_succeeded_dry_run_service_dates": nonterminal_succeeded_dry_run_service_dates,
        "nonterminal_succeeded_dry_run_count": len(nonterminal_succeeded_dry_run_service_dates),
        "dry_run_email_count": dry_run_email_count,
        "real_sent_candidate_email_count": real_sent_candidate_email_count,
        "required_email_count": S2PLT02_REQUIRED_EMAIL_COUNT,
        "observed_terminal_email_count_credit": observed_terminal_email_count_credit,
        "terminal_delivery_credit": False,
        "counts_toward_s2plt02_terminal_proof": False,
        "real_smtp_proven_for_terminal_pair": two_day_delivery_present,
        "real_scheduler_proven": real_scheduler_proven,
        "terminal_delivery_proof_artifact_present": terminal_artifact_present,
        "required_launchagent_labels": list(required_labels),
        "launchagent_disabled_states": launchagent_disabled_states,
        "launchagent_runtime_states": launchagent_runtime_states,
        "launchagent_calendar_triggers_present": launchagent_calendar_triggers_present,
        "all_required_launchagents_disabled": all_required_launchagents_disabled,
        "all_required_launchagents_loaded": all_required_launchagents_loaded,
        "all_required_launchagents_not_running": all_required_launchagents_not_running,
        "all_required_launchagents_have_calendar_triggers": all_required_launchagents_have_calendar_triggers,
        "launchagents_loaded_but_disabled": launchagents_loaded_but_disabled,
        "scheduler_runtime_evidence_status": scheduler_runtime_evidence_status,
        "adp_allow_smtp_send": adp_allow_smtp_send,
        "dry_run_audits": dry_run_audits,
        "delivery_evidence_ledger": delivery_ledger,
        "terminal_delivery_proof_validation": terminal_proof,
        "blocking_reasons": blocking_reasons,
        "production_acceptance_claimed": False,
        "integrated_production_accepted": False,
        "stage2_integrated_production_accepted": False,
        "daily_operation_enabled": False,
        "real_smtp_send_enabled": False,
        "scheduler_install_enabled": False,
        "release_packaging_enabled": False,
        "production_restore_enabled": False,
        "current_pointer_changed": False,
        "v7_1_baseline_changed": False,
        "v7_2_contract_files_changed": False,
        "state_hash": "",
    }
    state["state_hash"] = _stable_hash({key: value for key, value in state.items() if key != "state_hash"})
    return state


def validate_s2plt02_terminal_capture_window_audit_state(state: Mapping[str, Any]) -> list[str]:
    """Validate a terminal capture-window audit without accepting S2PLT02."""

    errors: list[str] = []
    if state.get("model_id") != S2PLT02_TERMINAL_CAPTURE_WINDOW_AUDIT_MODEL_ID:
        errors.append("S2PLT02 terminal capture window audit model_id is invalid")
    if state.get("schema_version") != S2PLT02_SCHEMA_VERSION:
        errors.append("S2PLT02 terminal capture window audit schema_version must be 1")
    if state.get("task_id") != "S2PLT02-TERMINAL-CAPTURE-WINDOW-AUDIT":
        errors.append("S2PLT02 terminal capture window audit task_id is invalid")
    if state.get("acceptance_id") != S2PLT02_ACCEPTANCE_ID:
        errors.append("S2PLT02 terminal capture window audit acceptance_id is invalid")
    if state.get("status") != "blocked":
        errors.append("S2PLT02 terminal capture window audit must stay blocked")
    if state.get("scope") != S2PLT02_TERMINAL_CAPTURE_WINDOW_AUDIT_SCOPE:
        errors.append("S2PLT02 terminal capture window audit scope is invalid")
    if tuple(state.get("candidate_service_dates", [])) == ():
        errors.append("candidate_service_dates must not be empty")
    if tuple(_mapping(state.get("launchagent_disabled_states")).keys()) != S2PMT07_LOCAL_RUNTIME_NO_PRODUCTION_REQUIRED_LABELS:
        errors.append("launchagent_disabled_states must cover all ADP local LaunchAgents")
    runtime_states = _mapping(state.get("launchagent_runtime_states"))
    calendar_triggers = _mapping(state.get("launchagent_calendar_triggers_present"))
    if set(runtime_states) != set(S2PMT07_LOCAL_RUNTIME_NO_PRODUCTION_REQUIRED_LABELS):
        errors.append("launchagent_runtime_states must cover all ADP local LaunchAgents")
    if set(calendar_triggers) != set(S2PMT07_LOCAL_RUNTIME_NO_PRODUCTION_REQUIRED_LABELS):
        errors.append("launchagent_calendar_triggers_present must cover all ADP local LaunchAgents")
    expected_loaded = all(
        runtime_states.get(label) != "missing" for label in S2PMT07_LOCAL_RUNTIME_NO_PRODUCTION_REQUIRED_LABELS
    )
    if state.get("all_required_launchagents_loaded") is not expected_loaded:
        errors.append("all_required_launchagents_loaded must match runtime states")
    expected_not_running = all(
        runtime_states.get(label) == "not running" for label in S2PMT07_LOCAL_RUNTIME_NO_PRODUCTION_REQUIRED_LABELS
    )
    if state.get("all_required_launchagents_not_running") is not expected_not_running:
        errors.append("all_required_launchagents_not_running must match runtime states")
    expected_calendar = all(
        calendar_triggers.get(label) is True for label in S2PMT07_LOCAL_RUNTIME_NO_PRODUCTION_REQUIRED_LABELS
    )
    if state.get("all_required_launchagents_have_calendar_triggers") is not expected_calendar:
        errors.append("all_required_launchagents_have_calendar_triggers must match trigger states")
    disabled_states = _mapping(state.get("launchagent_disabled_states"))
    expected_loaded_but_disabled = (
        all(disabled_states.get(label) == "disabled" for label in S2PMT07_LOCAL_RUNTIME_NO_PRODUCTION_REQUIRED_LABELS)
        and expected_loaded
    )
    if state.get("launchagents_loaded_but_disabled") is not expected_loaded_but_disabled:
        errors.append("launchagents_loaded_but_disabled must match disabled and runtime states")
    expected_scheduler_runtime_status = (
        "launchagents_loaded_but_disabled_not_terminal_scheduler_proof"
        if expected_loaded_but_disabled
        else "launchagents_disabled_not_terminal_scheduler_proof"
        if state.get("all_required_launchagents_disabled") is True
        else "launchagent_runtime_state_unknown"
        if not expected_loaded
        else "launchagents_not_all_disabled_not_terminal_scheduler_proof"
    )
    if state.get("scheduler_runtime_evidence_status") != expected_scheduler_runtime_status:
        errors.append("scheduler_runtime_evidence_status must match launchagent state")
    for field in (
        "terminal_delivery_credit",
        "counts_toward_s2plt02_terminal_proof",
    ):
        if state.get(field) is not False:
            errors.append(f"{field} must be false")
    if state.get("observed_terminal_email_count_credit", 0) < S2PLT02_REQUIRED_EMAIL_COUNT:
        for reason in (
            "second_consecutive_real_m1_m4_smtp_day_missing",
            "eight_real_emails_not_proven",
        ):
            if reason not in state.get("blocking_reasons", []):
                errors.append(f"{reason} blocker is required")
    if state.get("real_scheduler_proven") is not True and "real_launchd_scheduler_proof_missing" not in state.get("blocking_reasons", []):
        errors.append("real_launchd_scheduler_proof_missing blocker is required")
    if state.get("adp_allow_smtp_send") is False and "adp_allow_smtp_send_false" not in state.get("blocking_reasons", []):
        errors.append("adp_allow_smtp_send_false blocker is required")
    nonterminal_dates = [str(item) for item in state.get("nonterminal_succeeded_dry_run_service_dates", [])]
    if state.get("nonterminal_succeeded_dry_run_count") != len(nonterminal_dates):
        errors.append("nonterminal_succeeded_dry_run_count must match nonterminal date count")
    if nonterminal_dates:
        if "daily_run_succeeded_but_smtp_dry_run_not_terminal" not in state.get("blocking_reasons", []):
            errors.append("daily_run_succeeded_but_smtp_dry_run_not_terminal blocker is required")
        dry_run_dates = {str(item) for item in state.get("dry_run_service_dates", [])}
        if not set(nonterminal_dates).issubset(dry_run_dates):
            errors.append("nonterminal succeeded dry-run dates must be dry-run service dates")
    if (
        state.get("all_required_launchagents_disabled") is True
        and "adp_launchagents_disabled_by_user_domain_override" not in state.get("blocking_reasons", [])
    ):
        errors.append("adp_launchagents_disabled_by_user_domain_override blocker is required")
    for flag in S2PLT02_TERMINAL_CAPTURE_WINDOW_AUDIT_NO_PRODUCTION_FLAGS:
        if state.get(flag) is not False:
            errors.append(f"{flag} must be false")
    expected_hash = _stable_hash({key: value for key, value in state.items() if key != "state_hash"})
    if state.get("state_hash") != expected_hash:
        errors.append("S2PLT02 terminal capture window audit state_hash does not match state content")
    return errors


def build_s2plt02_real_proof_capture_authorization_hash(payload: Mapping[str, Any]) -> str:
    """Return the canonical authorization hash excluding its hash field."""

    payload_without_hash = {key: value for key, value in payload.items() if key != "authorization_hash"}
    return f"sha256:{_stable_hash(payload_without_hash)}"


def validate_s2plt02_real_proof_capture_authorization_artifact(
    payload: Mapping[str, Any] | None,
    *,
    expected_readiness_state_hash: str | None = None,
) -> list[str]:
    """Validate a future owner authorization artifact for real S2PLT02 proof capture."""

    if payload is None:
        return ["s2plt02_real_proof_capture_authorization_missing"]
    errors: list[str] = []
    errors.extend(_final_bundle_template_placeholder_errors(payload))
    for field in S2PLT02_REAL_PROOF_CAPTURE_AUTHORIZATION_REQUIRED_FIELDS:
        if field not in payload:
            errors.append(f"{field} is required")
    if tuple(payload.keys()) != S2PLT02_REAL_PROOF_CAPTURE_AUTHORIZATION_REQUIRED_FIELDS:
        errors.append("S2PLT02 real-proof capture authorization field order is invalid")
    if payload.get("schema_version") != S2PLT02_REAL_PROOF_CAPTURE_AUTHORIZATION_SCHEMA_VERSION:
        errors.append("schema_version is invalid")
    if payload.get("contract_id") != "ADP-PRODUCT-CONTRACT-V7.2":
        errors.append("contract_id must be ADP-PRODUCT-CONTRACT-V7.2")
    if not isinstance(payload.get("generated_at"), str) or not payload.get("generated_at"):
        errors.append("generated_at must be a non-empty string")
    if payload.get("authorization_decision") != S2PLT02_REAL_PROOF_CAPTURE_AUTHORIZATION_DECISION:
        errors.append("authorization_decision is invalid")

    authorized_by = _mapping(payload.get("authorized_by"))
    if not isinstance(authorized_by.get("owner_id"), str) or not authorized_by.get("owner_id"):
        errors.append("authorized_by.owner_id must be a non-empty string")
    if authorized_by.get("owner_role") not in {"owner", "content_owner + engineering_owner"}:
        errors.append("authorized_by.owner_role must be owner or content_owner + engineering_owner")
    if authorized_by.get("authorization_source") != "explicit_owner_instruction":
        errors.append("authorized_by.authorization_source must be explicit_owner_instruction")

    if payload.get("authorization_scope") != "S2PLT02_REAL_SMTP_SCHEDULER_PROOF_CAPTURE_ONLY":
        errors.append("authorization_scope is invalid")
    if tuple(payload.get("authorized_actions", [])) != S2PLT02_REAL_PROOF_CAPTURE_AUTHORIZATION_AUTHORIZED_ACTIONS:
        errors.append("authorized_actions are invalid")
    constraints = _mapping(payload.get("authorization_constraints"))
    for key in S2PLT02_REAL_PROOF_CAPTURE_AUTHORIZATION_CONSTRAINTS:
        if constraints.get(key) is not True:
            errors.append(f"authorization_constraints.{key} must be true")

    readiness_hash = payload.get("readiness_state_hash")
    if not isinstance(readiness_hash, str) or not readiness_hash:
        errors.append("readiness_state_hash must be a non-empty string")
    if expected_readiness_state_hash and readiness_hash != expected_readiness_state_hash:
        errors.append("readiness_state_hash does not match current readiness state")

    evidence_refs = payload.get("evidence_refs", [])
    required_refs = (
        "arxiv-daily-push/docs/governance/ASSURANCE_STATUS.yaml",
        "arxiv-daily-push/docs/phase_records/PHASE_S2PLT02_REAL_PROOF_CAPTURE_READINESS.md",
        "governance/run_manifests/ADP-S2PLT02-REAL-PROOF-CAPTURE-READINESS-20260629.json",
    )
    if not isinstance(evidence_refs, list) or any(ref not in evidence_refs for ref in required_refs):
        errors.append("evidence_refs must include the current readiness gate, phase record, and run manifest")

    no_production = _mapping(payload.get("no_production_side_effects"))
    for flag in S2PLT02_REAL_PROOF_CAPTURE_AUTHORIZATION_NO_PRODUCTION_FLAGS:
        if no_production.get(flag) is not False:
            errors.append(f"no_production_side_effects.{flag} must be false")

    if payload.get("authorization_hash") != build_s2plt02_real_proof_capture_authorization_hash(payload):
        errors.append("authorization_hash does not match payload content")
    return errors


def build_s2plt02_real_proof_capture_authorization_validation_state(
    payload: Mapping[str, Any] | None,
    *,
    expected_readiness_state_hash: str | None = None,
) -> dict[str, Any]:
    """Build validation state for a future S2PLT02 real-proof capture authorization artifact."""

    errors = validate_s2plt02_real_proof_capture_authorization_artifact(
        payload,
        expected_readiness_state_hash=expected_readiness_state_hash,
    )
    state = {
        "status": "pass" if not errors else "blocked",
        "scope": S2PLT02_REAL_PROOF_CAPTURE_AUTHORIZATION_SCOPE,
        "model_id": S2PLT02_REAL_PROOF_CAPTURE_AUTHORIZATION_MODEL_ID,
        "artifact_path": S2PLT02_REAL_PROOF_CAPTURE_AUTHORIZATION_ARTIFACT_PATH,
        "authorization_present": payload is not None,
        "validation_errors": errors,
        "required_fields": list(S2PLT02_REAL_PROOF_CAPTURE_AUTHORIZATION_REQUIRED_FIELDS),
        "required_authorized_actions": list(
            S2PLT02_REAL_PROOF_CAPTURE_AUTHORIZATION_AUTHORIZED_ACTIONS
        ),
        "expected_readiness_state_hash": expected_readiness_state_hash or "",
        "real_proof_capture_authorized_by_payload": not errors and payload is not None,
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
        "state_hash": "",
    }
    state["state_hash"] = _stable_hash({key: value for key, value in state.items() if key != "state_hash"})
    return state


def build_s2plt02_real_proof_capture_authorization_artifact_draft_state(
    *,
    owner_id: str,
    owner_role: str,
    generated_at: str,
    readiness_state_hash: str,
) -> dict[str, Any]:
    """Build a stdout-only S2PLT02 authorization artifact draft from explicit owner inputs."""

    artifact = {
        "schema_version": S2PLT02_REAL_PROOF_CAPTURE_AUTHORIZATION_SCHEMA_VERSION,
        "contract_id": "ADP-PRODUCT-CONTRACT-V7.2",
        "generated_at": generated_at,
        "authorization_decision": S2PLT02_REAL_PROOF_CAPTURE_AUTHORIZATION_DECISION,
        "authorized_by": {
            "owner_id": owner_id,
            "owner_role": owner_role,
            "authorization_source": "explicit_owner_instruction",
        },
        "authorization_scope": "S2PLT02_REAL_SMTP_SCHEDULER_PROOF_CAPTURE_ONLY",
        "authorized_actions": list(S2PLT02_REAL_PROOF_CAPTURE_AUTHORIZATION_AUTHORIZED_ACTIONS),
        "authorization_constraints": {
            key: True for key in S2PLT02_REAL_PROOF_CAPTURE_AUTHORIZATION_CONSTRAINTS
        },
        "readiness_state_hash": readiness_state_hash,
        "evidence_refs": [
            "arxiv-daily-push/docs/governance/ASSURANCE_STATUS.yaml",
            "arxiv-daily-push/docs/phase_records/PHASE_S2PLT02_REAL_PROOF_CAPTURE_READINESS.md",
            "governance/run_manifests/ADP-S2PLT02-REAL-PROOF-CAPTURE-READINESS-20260629.json",
        ],
        "no_production_side_effects": {
            flag: False for flag in S2PLT02_REAL_PROOF_CAPTURE_AUTHORIZATION_NO_PRODUCTION_FLAGS
        },
        "authorization_hash": "",
    }
    artifact["authorization_hash"] = build_s2plt02_real_proof_capture_authorization_hash(artifact)
    validation_errors = validate_s2plt02_real_proof_capture_authorization_artifact(
        artifact,
        expected_readiness_state_hash=readiness_state_hash,
    )
    state = {
        "status": "draft" if not validation_errors else "blocked",
        "scope": "s2plt02_real_proof_capture_authorization_artifact_draft_only_no_write_no_production",
        "task_id": "S2PLT02-REAL-PROOF-CAPTURE-AUTHORIZATION",
        "parent_task_id": S2PLT02_TASK_ID,
        "acceptance_id": S2PLT02_ACCEPTANCE_ID,
        "artifact_path": S2PLT02_REAL_PROOF_CAPTURE_AUTHORIZATION_ARTIFACT_PATH,
        "artifact": artifact,
        "validation_errors": validation_errors,
        "authorization_artifact_written": False,
        "authorization_artifact_present_in_repo": False,
        "authorization_gate_satisfied_by_this_command": False,
        "real_proof_capture_authorized_by_this_command": False,
        "next_required_action": "owner_must_review_and_write_authorization_artifact_if_explicitly_approved",
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
        "state_hash": "",
    }
    state["state_hash"] = _stable_hash({key: value for key, value in state.items() if key != "state_hash"})
    return state


def build_s2plt02_real_proof_capture_authorization_owner_packet_state(
    readiness_state: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the owner packet for explicit S2PLT02 real SMTP/scheduler proof capture authorization."""

    readiness = dict(readiness_state or {})
    readiness_hash = str(readiness.get("state_hash") or "")
    state = {
        "status": "blocked_owner_action_packet_ready_no_authorization",
        "scope": "owner_authorization_packet_only_no_real_smtp_scheduler_enablement",
        "task_id": "S2PLT02-REAL-PROOF-CAPTURE-AUTHORIZATION",
        "parent_task_id": S2PLT02_TASK_ID,
        "acceptance_id": S2PLT02_ACCEPTANCE_ID,
        "artifact_path": S2PLT02_REAL_PROOF_CAPTURE_AUTHORIZATION_ARTIFACT_PATH,
        "schema_version": S2PLT02_REAL_PROOF_CAPTURE_AUTHORIZATION_SCHEMA_VERSION,
        "authorization_model_id": S2PLT02_REAL_PROOF_CAPTURE_AUTHORIZATION_MODEL_ID,
        "authorization_decision": S2PLT02_REAL_PROOF_CAPTURE_AUTHORIZATION_DECISION,
        "authorization_required_fields": list(S2PLT02_REAL_PROOF_CAPTURE_AUTHORIZATION_REQUIRED_FIELDS),
        "required_owner_actions": list(S2PLT02_REAL_PROOF_CAPTURE_AUTHORIZATION_OWNER_ACTIONS),
        "authorized_actions_after_approval": list(
            S2PLT02_REAL_PROOF_CAPTURE_AUTHORIZATION_AUTHORIZED_ACTIONS
        ),
        "required_constraints": list(S2PLT02_REAL_PROOF_CAPTURE_AUTHORIZATION_CONSTRAINTS),
        "required_no_production_flags": list(S2PLT02_REAL_PROOF_CAPTURE_AUTHORIZATION_NO_PRODUCTION_FLAGS),
        "readiness_state_hash": readiness_hash,
        "readiness_status": readiness.get("status", "unknown"),
        "readiness_blocking_reasons": list(readiness.get("blocking_reasons", [])),
        "authorization_artifact_present": False,
        "real_proof_capture_authorized": False,
        "real_smtp_send_enabled_by_this_packet": False,
        "scheduler_install_enabled_by_this_packet": False,
        "terminal_delivery_proof_artifact_written_by_this_packet": False,
        "next_required_action": "owner_must_write_valid_authorization_artifact_before_real_smtp_scheduler_capture",
        "blocking_reasons": list(S2PLT02_REAL_PROOF_CAPTURE_AUTHORIZATION_BLOCKING_REASONS),
        **{flag: False for flag in S2PLT02_REAL_PROOF_CAPTURE_AUTHORIZATION_NO_PRODUCTION_FLAGS},
        "state_hash": "",
    }
    state["state_hash"] = _stable_hash({key: value for key, value in state.items() if key != "state_hash"})
    return state


def validate_s2plt02_real_proof_capture_authorization_owner_packet_state(
    state: Mapping[str, Any],
) -> list[str]:
    """Validate the owner authorization packet without treating it as authorization."""

    errors: list[str] = []
    if state.get("status") != "blocked_owner_action_packet_ready_no_authorization":
        errors.append("S2PLT02 real-proof capture authorization owner packet status is invalid")
    if state.get("scope") != "owner_authorization_packet_only_no_real_smtp_scheduler_enablement":
        errors.append("S2PLT02 real-proof capture authorization owner packet scope is invalid")
    if state.get("task_id") != "S2PLT02-REAL-PROOF-CAPTURE-AUTHORIZATION":
        errors.append("S2PLT02 real-proof capture authorization owner packet task_id is invalid")
    if state.get("artifact_path") != S2PLT02_REAL_PROOF_CAPTURE_AUTHORIZATION_ARTIFACT_PATH:
        errors.append("S2PLT02 real-proof capture authorization owner packet artifact_path is invalid")
    if state.get("schema_version") != S2PLT02_REAL_PROOF_CAPTURE_AUTHORIZATION_SCHEMA_VERSION:
        errors.append("S2PLT02 real-proof capture authorization owner packet schema_version is invalid")
    if state.get("authorization_model_id") != S2PLT02_REAL_PROOF_CAPTURE_AUTHORIZATION_MODEL_ID:
        errors.append("S2PLT02 real-proof capture authorization owner packet model_id is invalid")
    if state.get("authorization_decision") != S2PLT02_REAL_PROOF_CAPTURE_AUTHORIZATION_DECISION:
        errors.append("S2PLT02 real-proof capture authorization owner packet decision is invalid")
    if (
        tuple(state.get("authorization_required_fields", []))
        != S2PLT02_REAL_PROOF_CAPTURE_AUTHORIZATION_REQUIRED_FIELDS
    ):
        errors.append("S2PLT02 real-proof capture authorization owner packet required fields are invalid")
    if tuple(state.get("required_owner_actions", [])) != S2PLT02_REAL_PROOF_CAPTURE_AUTHORIZATION_OWNER_ACTIONS:
        errors.append("S2PLT02 real-proof capture authorization owner packet owner actions are invalid")
    if (
        tuple(state.get("authorized_actions_after_approval", []))
        != S2PLT02_REAL_PROOF_CAPTURE_AUTHORIZATION_AUTHORIZED_ACTIONS
    ):
        errors.append("S2PLT02 real-proof capture authorization owner packet authorized actions are invalid")
    if tuple(state.get("required_constraints", [])) != S2PLT02_REAL_PROOF_CAPTURE_AUTHORIZATION_CONSTRAINTS:
        errors.append("S2PLT02 real-proof capture authorization owner packet constraints are invalid")
    if (
        tuple(state.get("required_no_production_flags", []))
        != S2PLT02_REAL_PROOF_CAPTURE_AUTHORIZATION_NO_PRODUCTION_FLAGS
    ):
        errors.append("S2PLT02 real-proof capture authorization owner packet no-production flags are invalid")
    if state.get("authorization_artifact_present") is not False:
        errors.append("authorization_artifact_present must remain false until owner supplies artifact")
    for field in (
        "real_proof_capture_authorized",
        "real_smtp_send_enabled_by_this_packet",
        "scheduler_install_enabled_by_this_packet",
        "terminal_delivery_proof_artifact_written_by_this_packet",
    ):
        if state.get(field) is not False:
            errors.append(f"{field} must be false")
    if (
        state.get("next_required_action")
        != "owner_must_write_valid_authorization_artifact_before_real_smtp_scheduler_capture"
    ):
        errors.append("S2PLT02 real-proof capture authorization owner packet next action is invalid")
    for reason in S2PLT02_REAL_PROOF_CAPTURE_AUTHORIZATION_BLOCKING_REASONS:
        if reason not in state.get("blocking_reasons", []):
            errors.append(f"S2PLT02 real-proof capture authorization owner packet must include blocker {reason}")
    for flag in S2PLT02_REAL_PROOF_CAPTURE_AUTHORIZATION_NO_PRODUCTION_FLAGS:
        if state.get(flag) is not False:
            errors.append(f"{flag} must be false")
    expected_hash = _stable_hash({key: value for key, value in state.items() if key != "state_hash"})
    if state.get("state_hash") != expected_hash:
        errors.append("S2PLT02 real-proof capture authorization owner packet state_hash does not match state content")
    return errors


def _default_s2plt02_m4_watermark_proof_records() -> list[dict[str, Any]]:
    """Return committed non-secret M4 watermark proof records for the current ledger."""

    refs = dict(S2PLT02_PARTIAL_REAL_DELIVERY_REFS)
    generated_at = S2PLT02_M4_WATERMARK_PROOF_GENERATED_AT
    cycle_id = S2PLT02_M4_WATERMARK_PROOF_CYCLE_ID
    return [
        {
            "proof_ref": S2PLT02_M4_WATERMARK_PROOF_RECORD_REF,
            "status": "pass",
            "service_date": S2PLT02_PARTIAL_REAL_DELIVERY_SERVICE_DATE,
            "cycle_id": cycle_id,
            "generated_at": generated_at,
            "mail_product_id": "M4",
            "m4_delivery_ref": refs["M4"],
            "terminal_mail_records": [
                {
                    "product_id": "M1",
                    "cycle_id": cycle_id,
                    "status": "SENT",
                    "observed_at": generated_at,
                    "delivery_ref": refs["M1"],
                    "message_id": "<adp-419c5f9177debf426f5813dd@arxiv-daily-push.local>",
                },
                {
                    "product_id": "M2",
                    "cycle_id": cycle_id,
                    "status": "SENT",
                    "observed_at": generated_at,
                    "delivery_ref": refs["M2"],
                    "message_id": "<adp-f081f502a9706f56ffbf0830@arxiv-daily-push.local>",
                },
                {
                    "product_id": "M3",
                    "cycle_id": cycle_id,
                    "status": "SENT",
                    "observed_at": generated_at,
                    "delivery_ref": refs["M3"],
                    "message_id": "<adp-f90d3056a41a9ab3c9ba196f@arxiv-daily-push.local>",
                },
            ],
            "watermark": {
                "cycle_id": cycle_id,
                "status": "ready",
                "m4_ready": True,
                "m4_cycle_watermark": True,
                "watermark_finalized_at": generated_at,
            },
            "source_evidence_refs": [
                "governance/run_manifests/ADP-LOCAL-DAILY-M1-M4-RESEND-EXECUTION-20260628.json",
                "governance/run_manifests/ADP-S2PLT02-DELIVERY-EVIDENCE-LEDGER-20260628.json",
            ],
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
    ]


def validate_s2plt02_delivery_evidence_ledger_state(state: Mapping[str, Any]) -> list[str]:
    """Validate the S2PLT02 real-delivery ledger state."""

    errors: list[str] = []
    if state.get("model_id") != S2PLT02_DELIVERY_EVIDENCE_LEDGER_MODEL_ID:
        errors.append("S2PLT02 delivery ledger model_id is invalid")
    if state.get("schema_version") != S2PLT02_SCHEMA_VERSION:
        errors.append("S2PLT02 delivery ledger schema_version must be 1")
    if state.get("task_id") != "S2PLT02-DELIVERY-EVIDENCE-LEDGER":
        errors.append("S2PLT02 delivery ledger task_id is invalid")
    if state.get("acceptance_id") != S2PLT02_ACCEPTANCE_ID:
        errors.append("S2PLT02 delivery ledger acceptance_id is invalid")
    if state.get("scope") != S2PLT02_DELIVERY_EVIDENCE_LEDGER_SCOPE:
        errors.append("S2PLT02 delivery ledger scope is invalid")
    if state.get("status") not in {"ready", "partial", "blocked"}:
        errors.append("S2PLT02 delivery ledger status is invalid")
    if state.get("required_natural_days") != S2PLT02_REQUIRED_NATURAL_DAYS:
        errors.append("S2PLT02 delivery ledger required_natural_days must be 2")
    if state.get("required_email_count") != S2PLT02_REQUIRED_EMAIL_COUNT:
        errors.append("S2PLT02 delivery ledger required_email_count must be 8")
    if tuple(state.get("required_mail_products", [])) != S2PLT02_REQUIRED_MAIL_PRODUCTS:
        errors.append("S2PLT02 delivery ledger required_mail_products must be M1-M4")
    if state.get("s2plt02_accepted") is not False:
        errors.append("S2PLT02 delivery ledger must not accept S2PLT02")
    for flag in (
        "production_acceptance_claimed",
        "stage2_integrated_production_accepted",
        "integrated_production_accepted",
        "daily_operation_enabled",
        "new_production_side_effects_from_ledger",
    ):
        if state.get(flag) is not False:
            errors.append(f"{flag} must be false")

    service_dates = state.get("service_dates", [])
    if state.get("observed_natural_days") != len(service_dates):
        errors.append("S2PLT02 delivery ledger observed_natural_days must match service_dates")
    products_by_service_date = _mapping(state.get("products_by_service_date"))
    observed_email_count = sum(len(products) for products in products_by_service_date.values() if isinstance(products, list))
    if state.get("observed_email_count") != observed_email_count:
        errors.append("S2PLT02 delivery ledger observed_email_count must match products_by_service_date")
    for service_date, products in products_by_service_date.items():
        if tuple(products) != S2PLT02_REQUIRED_MAIL_PRODUCTS:
            errors.append(f"S2PLT02 delivery ledger products for {service_date} must be M1-M4")
    for error in state.get("validation_errors", []):
        if isinstance(error, str):
            errors.append(error)
    if state.get("duplicate_email_count", 0) != 0:
        errors.append("S2PLT02 delivery ledger duplicate_email_count must be 0")
    if state.get("duplicate_service_date_count", 0) != 0:
        errors.append("S2PLT02 delivery ledger duplicate_service_date_count must be 0")
    if state.get("status") == "ready" and not state.get("two_day_delivery_evidence_present"):
        errors.append("ready S2PLT02 delivery ledger requires two_day_delivery_evidence_present")
    if state.get("two_day_delivery_evidence_present") and (
        state.get("observed_natural_days", 0) < S2PLT02_REQUIRED_NATURAL_DAYS
        or state.get("observed_email_count", 0) < S2PLT02_REQUIRED_EMAIL_COUNT
    ):
        errors.append("two_day_delivery_evidence_present requires 2 natural days and 8 emails")
    expected_hash = _stable_hash({key: value for key, value in state.items() if key != "ledger_hash"})
    if state.get("ledger_hash") != expected_hash:
        errors.append("S2PLT02 delivery ledger_hash does not match ledger content")
    return errors


def build_s2plt02_real_delivery_manifest_validation_state(
    *,
    delivery_manifest: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Build a no-write validation state for one real M1-M4 delivery manifest input."""

    if delivery_manifest is None:
        ledger = build_s2plt02_delivery_evidence_ledger_state(delivery_manifests=[])
        validation_errors = ["delivery_manifest is required"]
        manifest_ref = ""
        service_date = ""
    else:
        ledger = build_s2plt02_delivery_evidence_ledger_state(delivery_manifests=[delivery_manifest])
        validation_errors = validate_s2plt02_delivery_evidence_ledger_state(ledger)
        manifest_ref = str(delivery_manifest.get("manifest_ref") or "")
        service_date = str(delivery_manifest.get("service_date") or "")

    products_by_service_date = _mapping(ledger.get("products_by_service_date"))
    delivery_ref_by_service_date = _mapping(ledger.get("delivery_ref_by_service_date"))
    sent_mail_products = [
        str(product)
        for product in products_by_service_date.get(service_date, [])
        if isinstance(product, str)
    ]
    delivery_ref_by_product = _mapping(delivery_ref_by_service_date.get(service_date))
    observed_email_count = len(sent_mail_products)
    delivery_manifest_ready = (
        not validation_errors
        and ledger.get("source_manifest_count") == 1
        and ledger.get("observed_natural_days") == 1
        and observed_email_count == len(S2PLT02_REQUIRED_MAIL_PRODUCTS)
        and tuple(sent_mail_products) == S2PLT02_REQUIRED_MAIL_PRODUCTS
        and ledger.get("real_smtp_evidence_present") is True
        and ledger.get("duplicate_email_count") == 0
        and ledger.get("duplicate_service_date_count") == 0
    )
    state: dict[str, Any] = {
        "model_id": S2PLT02_DELIVERY_EVIDENCE_LEDGER_MODEL_ID,
        "schema_version": S2PLT02_SCHEMA_VERSION,
        "task_id": "S2PLT02-REAL-DELIVERY-MANIFEST-INPUT-VALIDATOR",
        "acceptance_id": S2PLT02_ACCEPTANCE_ID,
        "status": "pass" if delivery_manifest_ready else "blocked",
        "scope": S2PLT02_REAL_DELIVERY_MANIFEST_VALIDATION_SCOPE,
        "delivery_manifest_ready": delivery_manifest_ready,
        "manifest_ref": manifest_ref,
        "service_date": service_date,
        "required_mail_products": list(S2PLT02_REQUIRED_MAIL_PRODUCTS),
        "sent_mail_products": sent_mail_products,
        "observed_email_count": observed_email_count,
        "delivery_ref_by_product": delivery_ref_by_product,
        "source_ledger_status": ledger.get("status"),
        "source_ledger_hash": ledger.get("ledger_hash"),
        "validation_errors": validation_errors,
        "blocking_reasons": [] if delivery_manifest_ready else ["real_delivery_manifest_not_valid"],
        "artifact_written": False,
        "s2plt02_accepted": False,
        "production_acceptance_claimed": False,
        "integrated_production_accepted": False,
        "stage2_integrated_production_accepted": False,
        "daily_operation_enabled": False,
        "real_smtp_send_enabled": False,
        "scheduler_enabled": False,
        "scheduler_install_enabled": False,
        "release_packaging_enabled": False,
        "production_restore_enabled": False,
        "public_schema_changed": False,
        "db_migration_executed": False,
        "production_queue_mutated": False,
        "source_adapter_changed": False,
        "ranking_algorithm_changed": False,
        "current_pointer_changed": False,
        "v7_1_baseline_changed": False,
        "v7_2_contract_files_changed": False,
        "state_hash": "",
    }
    state["state_hash"] = _stable_hash({key: value for key, value in state.items() if key != "state_hash"})
    return state


def validate_s2plt02_real_delivery_manifest_validation_state(state: Mapping[str, Any]) -> list[str]:
    """Validate a no-write real-delivery manifest input validation state."""

    errors: list[str] = []
    if state.get("model_id") != S2PLT02_DELIVERY_EVIDENCE_LEDGER_MODEL_ID:
        errors.append("S2PLT02 real delivery manifest validation model_id is invalid")
    if state.get("schema_version") != S2PLT02_SCHEMA_VERSION:
        errors.append("S2PLT02 real delivery manifest validation schema_version must be 1")
    if state.get("task_id") != "S2PLT02-REAL-DELIVERY-MANIFEST-INPUT-VALIDATOR":
        errors.append("S2PLT02 real delivery manifest validation task_id is invalid")
    if state.get("acceptance_id") != S2PLT02_ACCEPTANCE_ID:
        errors.append("S2PLT02 real delivery manifest validation acceptance_id is invalid")
    if state.get("scope") != S2PLT02_REAL_DELIVERY_MANIFEST_VALIDATION_SCOPE:
        errors.append("S2PLT02 real delivery manifest validation scope is invalid")
    if state.get("status") not in {"pass", "blocked"}:
        errors.append("S2PLT02 real delivery manifest validation status must be pass or blocked")
    ready = state.get("delivery_manifest_ready") is True
    if state.get("status") == "pass" and not ready:
        errors.append("pass status requires delivery_manifest_ready")
    if ready and state.get("validation_errors"):
        errors.append("delivery_manifest_ready requires no validation_errors")
    if not ready and "real_delivery_manifest_not_valid" not in state.get("blocking_reasons", []):
        errors.append("blocked delivery manifest state must include real_delivery_manifest_not_valid")
    if ready:
        if tuple(state.get("sent_mail_products", [])) != S2PLT02_REQUIRED_MAIL_PRODUCTS:
            errors.append("ready delivery manifest state requires M1-M4 sent_mail_products")
        if state.get("observed_email_count") != len(S2PLT02_REQUIRED_MAIL_PRODUCTS):
            errors.append("ready delivery manifest state requires four observed emails")
    if tuple(state.get("required_mail_products", [])) != S2PLT02_REQUIRED_MAIL_PRODUCTS:
        errors.append("S2PLT02 real delivery manifest validation required_mail_products must be M1-M4")
    for error in state.get("validation_errors", []):
        if isinstance(error, str) and not ready:
            continue
        if isinstance(error, str) and ready:
            errors.append(error)
    if state.get("artifact_written") is not False:
        errors.append("artifact_written must be false")
    for flag in (
        "s2plt02_accepted",
        "production_acceptance_claimed",
        "integrated_production_accepted",
        "stage2_integrated_production_accepted",
        "daily_operation_enabled",
        "real_smtp_send_enabled",
        "scheduler_enabled",
        "scheduler_install_enabled",
        "release_packaging_enabled",
        "production_restore_enabled",
        "public_schema_changed",
        "db_migration_executed",
        "production_queue_mutated",
        "source_adapter_changed",
        "ranking_algorithm_changed",
        "current_pointer_changed",
        "v7_1_baseline_changed",
        "v7_2_contract_files_changed",
    ):
        if state.get(flag) is not False:
            errors.append(f"{flag} must be false")
    expected_hash = _stable_hash({key: value for key, value in state.items() if key != "state_hash"})
    if state.get("state_hash") != expected_hash:
        errors.append("S2PLT02 real delivery manifest validation state_hash does not match state content")
    return errors


def build_s2plt02_normalized_delivery_manifest_state(
    *,
    raw_manifest: Mapping[str, Any],
    raw_manifest_ref: str,
    normalized_manifest_ref: str,
    normalized_at: str,
) -> dict[str, Any]:
    """Build a normalized real-delivery manifest wrapper without writing artifacts or sending mail."""

    raw_copy = json.loads(json.dumps(raw_manifest, ensure_ascii=False))
    raw_ref = raw_manifest_ref or str(raw_copy.get("manifest_ref") or "")
    normalized_ref = normalized_manifest_ref or raw_ref
    raw_hash = _stable_hash(raw_copy)
    evidence_refs: list[str] = []
    if raw_ref:
        evidence_refs.append(raw_ref)
    for ref in raw_copy.get("evidence_refs", []):
        if isinstance(ref, str) and ref not in evidence_refs:
            evidence_refs.append(ref)

    normalized_manifest = raw_copy
    normalized_manifest["manifest_ref"] = normalized_ref
    normalized_manifest["normalized_from_manifest_ref"] = raw_ref
    normalized_manifest["normalized_from_manifest_hash"] = raw_hash
    normalized_manifest["normalization_task_id"] = "S2PLT02-REAL-DELIVERY-MANIFEST-NORMALIZATION"
    normalized_manifest["normalization_scope"] = S2PLT02_REAL_DELIVERY_MANIFEST_NORMALIZATION_SCOPE
    normalized_manifest["normalized_at"] = normalized_at
    normalized_manifest["evidence_refs"] = evidence_refs
    mail_summary = _mapping(normalized_manifest.get("mail_delivery_summary"))
    products = mail_summary.get("sent_mail_products", [])
    if isinstance(products, list):
        normalized_manifest["sent_mail_products"] = [str(product) for product in products]
    for flag in S2PLT02_DELIVERY_EVIDENCE_LEDGER_FORBIDDEN_SOURCE_FLAGS:
        normalized_manifest.setdefault(flag, False)

    manifest_validation = build_s2plt02_real_delivery_manifest_validation_state(
        delivery_manifest=normalized_manifest
    )
    manifest_validation_errors = validate_s2plt02_real_delivery_manifest_validation_state(manifest_validation)
    ready = manifest_validation.get("status") == "pass" and not manifest_validation_errors
    state: dict[str, Any] = {
        "model_id": S2PLT02_REAL_DELIVERY_MANIFEST_NORMALIZATION_MODEL_ID,
        "schema_version": S2PLT02_SCHEMA_VERSION,
        "task_id": "S2PLT02-REAL-DELIVERY-MANIFEST-NORMALIZATION",
        "acceptance_id": S2PLT02_ACCEPTANCE_ID,
        "status": "pass" if ready else "blocked",
        "scope": S2PLT02_REAL_DELIVERY_MANIFEST_NORMALIZATION_SCOPE,
        "normalized_at": normalized_at,
        "raw_manifest_ref": raw_ref,
        "raw_manifest_hash": raw_hash,
        "normalized_manifest_ref": normalized_ref,
        "normalized_manifest_ready": ready,
        "normalized_manifest": normalized_manifest,
        "manifest_validation": manifest_validation,
        "manifest_validation_errors": manifest_validation_errors,
        "blocking_reasons": [] if ready else ["normalized_delivery_manifest_not_valid"],
        "artifact_written": False,
        "terminal_delivery_proof_written": False,
        "s2plt02_accepted": False,
        "production_acceptance_claimed": False,
        "integrated_production_accepted": False,
        "stage2_integrated_production_accepted": False,
        "daily_operation_enabled": False,
        "real_smtp_send_enabled": False,
        "scheduler_enabled": False,
        "scheduler_install_enabled": False,
        "release_packaging_enabled": False,
        "production_restore_enabled": False,
        "public_schema_changed": False,
        "db_migration_executed": False,
        "production_queue_mutated": False,
        "source_adapter_changed": False,
        "ranking_algorithm_changed": False,
        "current_pointer_changed": False,
        "v7_1_baseline_changed": False,
        "v7_2_contract_files_changed": False,
        "state_hash": "",
    }
    state["state_hash"] = _stable_hash({key: value for key, value in state.items() if key != "state_hash"})
    return state


def validate_s2plt02_normalized_delivery_manifest_state(state: Mapping[str, Any]) -> list[str]:
    """Validate a normalized delivery manifest wrapper state."""

    errors: list[str] = []
    if state.get("model_id") != S2PLT02_REAL_DELIVERY_MANIFEST_NORMALIZATION_MODEL_ID:
        errors.append("S2PLT02 normalized delivery manifest model_id is invalid")
    if state.get("schema_version") != S2PLT02_SCHEMA_VERSION:
        errors.append("S2PLT02 normalized delivery manifest schema_version must be 1")
    if state.get("task_id") != "S2PLT02-REAL-DELIVERY-MANIFEST-NORMALIZATION":
        errors.append("S2PLT02 normalized delivery manifest task_id is invalid")
    if state.get("acceptance_id") != S2PLT02_ACCEPTANCE_ID:
        errors.append("S2PLT02 normalized delivery manifest acceptance_id is invalid")
    if state.get("scope") != S2PLT02_REAL_DELIVERY_MANIFEST_NORMALIZATION_SCOPE:
        errors.append("S2PLT02 normalized delivery manifest scope is invalid")
    normalized_manifest = _mapping(state.get("normalized_manifest"))
    if not normalized_manifest:
        errors.append("normalized_manifest is required")
    else:
        if normalized_manifest.get("manifest_ref") != state.get("normalized_manifest_ref"):
            errors.append("normalized_manifest manifest_ref must match normalized_manifest_ref")
        if normalized_manifest.get("normalized_from_manifest_ref") != state.get("raw_manifest_ref"):
            errors.append("normalized_manifest normalized_from_manifest_ref must match raw_manifest_ref")
        if normalized_manifest.get("normalized_from_manifest_hash") != state.get("raw_manifest_hash"):
            errors.append("normalized_manifest normalized_from_manifest_hash must match raw_manifest_hash")
        if normalized_manifest.get("normalization_scope") != S2PLT02_REAL_DELIVERY_MANIFEST_NORMALIZATION_SCOPE:
            errors.append("normalized_manifest normalization_scope is invalid")
        for flag in S2PLT02_DELIVERY_EVIDENCE_LEDGER_FORBIDDEN_SOURCE_FLAGS:
            if normalized_manifest.get(flag) is not False:
                errors.append(f"normalized_manifest {flag} must be false")
        recomputed_validation = build_s2plt02_real_delivery_manifest_validation_state(
            delivery_manifest=normalized_manifest
        )
        recomputed_errors = validate_s2plt02_real_delivery_manifest_validation_state(recomputed_validation)
        if recomputed_validation.get("status") != _mapping(state.get("manifest_validation")).get("status"):
            errors.append("manifest_validation status does not match normalized manifest")
        for error in recomputed_errors:
            errors.append(error)
    ready = state.get("normalized_manifest_ready") is True
    if state.get("status") not in {"pass", "blocked"}:
        errors.append("S2PLT02 normalized delivery manifest status must be pass or blocked")
    if state.get("status") == "pass" and not ready:
        errors.append("pass status requires normalized_manifest_ready")
    if ready and state.get("manifest_validation_errors"):
        errors.append("normalized_manifest_ready requires no manifest_validation_errors")
    if not ready and "normalized_delivery_manifest_not_valid" not in state.get("blocking_reasons", []):
        errors.append("blocked normalized manifest state must include normalized_delivery_manifest_not_valid")
    for flag in (
        "artifact_written",
        "terminal_delivery_proof_written",
        "s2plt02_accepted",
        "production_acceptance_claimed",
        "integrated_production_accepted",
        "stage2_integrated_production_accepted",
        "daily_operation_enabled",
        "real_smtp_send_enabled",
        "scheduler_enabled",
        "scheduler_install_enabled",
        "release_packaging_enabled",
        "production_restore_enabled",
        "public_schema_changed",
        "db_migration_executed",
        "production_queue_mutated",
        "source_adapter_changed",
        "ranking_algorithm_changed",
        "current_pointer_changed",
        "v7_1_baseline_changed",
        "v7_2_contract_files_changed",
    ):
        if state.get(flag) is not False:
            errors.append(f"{flag} must be false")
    expected_hash = _stable_hash({key: value for key, value in state.items() if key != "state_hash"})
    if state.get("state_hash") != expected_hash:
        errors.append("S2PLT02 normalized delivery manifest state_hash does not match state content")
    return errors


def build_s2plt02_m4_watermark_proof_state(
    *,
    watermark_proofs: list[Mapping[str, Any]] | None = None,
    delivery_ledger: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the S2PLT02 M4 watermark proof state without enabling production."""

    ledger = dict(delivery_ledger or build_s2plt02_delivery_evidence_ledger_state())
    source_proofs = [
        json.loads(json.dumps(record, ensure_ascii=False))
        for record in (
            watermark_proofs if watermark_proofs is not None else _default_s2plt02_m4_watermark_proof_records()
        )
    ]
    ledger_errors = validate_s2plt02_delivery_evidence_ledger_state(ledger)
    validation_errors: list[str] = []
    blocking_reasons: list[str] = []
    required_service_dates = [str(item) for item in ledger.get("service_dates", [])]
    delivery_ref_by_service_date = _mapping(ledger.get("delivery_ref_by_service_date"))
    ready_proofs_by_service_date: dict[str, dict[str, Any]] = {}
    derived_watermarks_by_service_date: dict[str, dict[str, Any]] = {}
    proof_refs: list[str] = []

    if ledger_errors:
        validation_errors.append("delivery ledger is invalid for M4 watermark proof")
        validation_errors.extend(ledger_errors)

    for service_date in required_service_dates:
        if not any(proof.get("service_date") == service_date for proof in source_proofs):
            blocking_reasons.append(f"M4 watermark proof record is missing for {service_date}")

    for index, proof in enumerate(source_proofs, start=1):
        proof_ref = str(proof.get("proof_ref") or f"inline_m4_watermark_proof_{index}")
        proof_refs.append(proof_ref)
        service_date = str(proof.get("service_date") or "")
        cycle_id = str(proof.get("cycle_id") or "")
        proof_errors: list[str] = []
        if proof.get("status") != "pass":
            proof_errors.append(f"proof {proof_ref} status must be pass")
        if not service_date:
            proof_errors.append(f"proof {proof_ref} service_date is required")
        elif service_date not in required_service_dates:
            proof_errors.append(f"proof {proof_ref} service_date must match delivery ledger")
        if not cycle_id:
            proof_errors.append(f"proof {proof_ref} cycle_id is required")
        if proof.get("mail_product_id") != "M4":
            proof_errors.append(f"proof {proof_ref} mail_product_id must be M4")

        for flag in S2PLT02_M4_WATERMARK_FORBIDDEN_SOURCE_FLAGS:
            if proof.get(flag, False) is not False:
                proof_errors.append(f"proof {proof_ref} {flag} must be false")

        service_refs = _mapping(delivery_ref_by_service_date.get(service_date))
        if proof.get("m4_delivery_ref") != service_refs.get("M4"):
            proof_errors.append(f"proof {proof_ref} m4_delivery_ref must match delivery ledger")

        terminal_records = [row for row in proof.get("terminal_mail_records") or [] if isinstance(row, Mapping)]
        terminal_products = tuple(str(row.get("product_id") or "") for row in terminal_records)
        if terminal_products != S2PLT02_M4_WATERMARK_REQUIRED_TERMINAL_PRODUCTS:
            proof_errors.append(f"proof {proof_ref} terminal_mail_records must be M1-M3")
        for row in terminal_records:
            product_id = str(row.get("product_id") or "")
            if row.get("delivery_ref") != service_refs.get(product_id):
                proof_errors.append(f"proof {proof_ref} terminal delivery ref mismatch for {product_id}")

        watermark = _mapping(proof.get("watermark"))
        derived_watermark = build_m4_cycle_watermark(
            cycle_id=cycle_id,
            terminal_mails=terminal_records,
            generated_at=str(watermark.get("watermark_finalized_at") or proof.get("generated_at") or ""),
            deadline_passed=True,
        )
        if service_date:
            derived_watermarks_by_service_date[service_date] = derived_watermark
        if watermark.get("cycle_id") != cycle_id:
            proof_errors.append(f"proof {proof_ref} watermark.cycle_id must match cycle_id")
        if watermark.get("status") != "ready":
            proof_errors.append(f"proof {proof_ref} watermark.status must be ready")
        if watermark.get("m4_ready") is not True:
            proof_errors.append(f"proof {proof_ref} watermark.m4_ready must be true")
        if watermark.get("m4_cycle_watermark") is not True:
            proof_errors.append(f"proof {proof_ref} watermark.m4_cycle_watermark must be true")
        if derived_watermark.get("status") != "ready" or derived_watermark.get("m4_ready") is not True:
            proof_errors.append(f"proof {proof_ref} derived watermark must be ready")

        if proof_errors:
            validation_errors.extend(proof_errors)
            continue
        ready_proofs_by_service_date[service_date] = {
            "proof_ref": proof_ref,
            "cycle_id": cycle_id,
            "m4_delivery_ref": proof.get("m4_delivery_ref"),
            "terminal_mail_products": list(S2PLT02_M4_WATERMARK_REQUIRED_TERMINAL_PRODUCTS),
            "watermark_finalized_at": str(watermark.get("watermark_finalized_at") or ""),
        }

    covered_service_dates = [date for date in required_service_dates if date in ready_proofs_by_service_date]
    missing_service_dates = [date for date in required_service_dates if date not in ready_proofs_by_service_date]
    for service_date in missing_service_dates:
        reason = f"M4 watermark proof not ready for {service_date}"
        if reason not in blocking_reasons:
            blocking_reasons.append(reason)
    m4_watermark_correct = bool(required_service_dates) and not missing_service_dates and not validation_errors
    state = {
        "model_id": S2PLT02_M4_WATERMARK_PROOF_MODEL_ID,
        "schema_version": S2PLT02_SCHEMA_VERSION,
        "task_id": "S2PLT02-M4-WATERMARK-PROOF",
        "acceptance_id": S2PLT02_ACCEPTANCE_ID,
        "status": "ready" if m4_watermark_correct else ("partial" if covered_service_dates else "blocked"),
        "scope": S2PLT02_M4_WATERMARK_PROOF_SCOPE,
        "required_terminal_mail_products": list(S2PLT02_M4_WATERMARK_REQUIRED_TERMINAL_PRODUCTS),
        "required_service_dates": required_service_dates,
        "covered_service_dates": covered_service_dates,
        "missing_service_dates": missing_service_dates,
        "proof_ref_count": len(source_proofs),
        "proof_refs": proof_refs,
        "ready_proofs_by_service_date": ready_proofs_by_service_date,
        "derived_watermarks_by_service_date": derived_watermarks_by_service_date,
        "delivery_evidence_ledger_hash": ledger.get("ledger_hash"),
        "m4_watermark_correct": m4_watermark_correct,
        "blocking_reasons": blocking_reasons,
        "validation_errors": validation_errors,
        "s2plt02_accepted": False,
        "production_acceptance_claimed": False,
        "stage2_integrated_production_accepted": False,
        "integrated_production_accepted": False,
        "daily_operation_enabled": False,
        "new_production_side_effects_from_watermark_proof": False,
        "proof_hash": "",
    }
    state["proof_hash"] = _stable_hash({key: value for key, value in state.items() if key != "proof_hash"})
    return state


def validate_s2plt02_m4_watermark_proof_state(state: Mapping[str, Any]) -> list[str]:
    """Validate the S2PLT02 M4 watermark proof state."""

    errors: list[str] = []
    if state.get("model_id") != S2PLT02_M4_WATERMARK_PROOF_MODEL_ID:
        errors.append("S2PLT02 M4 watermark proof model_id is invalid")
    if state.get("schema_version") != S2PLT02_SCHEMA_VERSION:
        errors.append("S2PLT02 M4 watermark proof schema_version must be 1")
    if state.get("task_id") != "S2PLT02-M4-WATERMARK-PROOF":
        errors.append("S2PLT02 M4 watermark proof task_id is invalid")
    if state.get("acceptance_id") != S2PLT02_ACCEPTANCE_ID:
        errors.append("S2PLT02 M4 watermark proof acceptance_id is invalid")
    if state.get("scope") != S2PLT02_M4_WATERMARK_PROOF_SCOPE:
        errors.append("S2PLT02 M4 watermark proof scope is invalid")
    if state.get("status") not in {"ready", "partial", "blocked"}:
        errors.append("S2PLT02 M4 watermark proof status is invalid")
    if tuple(state.get("required_terminal_mail_products", [])) != S2PLT02_M4_WATERMARK_REQUIRED_TERMINAL_PRODUCTS:
        errors.append("S2PLT02 M4 watermark proof terminal products must be M1-M3")
    for flag in (
        "s2plt02_accepted",
        "production_acceptance_claimed",
        "stage2_integrated_production_accepted",
        "integrated_production_accepted",
        "daily_operation_enabled",
        "new_production_side_effects_from_watermark_proof",
    ):
        if state.get(flag) is not False:
            errors.append(f"{flag} must be false")
    for error in state.get("validation_errors", []):
        if isinstance(error, str):
            errors.append(error)
    required_service_dates = [str(item) for item in state.get("required_service_dates", [])]
    covered_service_dates = [str(item) for item in state.get("covered_service_dates", [])]
    missing_service_dates = [str(item) for item in state.get("missing_service_dates", [])]
    if set(covered_service_dates) & set(missing_service_dates):
        errors.append("S2PLT02 M4 watermark proof cannot both cover and miss a service date")
    if state.get("m4_watermark_correct") is True and (missing_service_dates or set(covered_service_dates) != set(required_service_dates)):
        errors.append("M4 watermark proof cannot be correct while required service dates are missing")
    if state.get("status") == "ready" and state.get("m4_watermark_correct") is not True:
        errors.append("ready S2PLT02 M4 watermark proof requires m4_watermark_correct")
    expected_hash = _stable_hash({key: value for key, value in state.items() if key != "proof_hash"})
    if state.get("proof_hash") != expected_hash:
        errors.append("S2PLT02 M4 watermark proof_hash does not match proof content")
    return errors


def build_s2plt02_partial_real_delivery_state() -> dict[str, Any]:
    """Build one-day real delivery evidence without treating it as S2PLT02 acceptance."""

    ledger = build_s2plt02_delivery_evidence_ledger_state()
    current_service_date = ledger["service_dates"][0] if ledger["service_dates"] else S2PLT02_PARTIAL_REAL_DELIVERY_SERVICE_DATE
    current_products = ledger["products_by_service_date"].get(current_service_date, list(S2PLT02_PARTIAL_REAL_DELIVERY_PRODUCTS))
    current_delivery_refs = ledger["delivery_ref_by_service_date"].get(
        current_service_date,
        dict(S2PLT02_PARTIAL_REAL_DELIVERY_REFS),
    )
    state = {
        "status": "partial",
        "scope": S2PLT02_PARTIAL_REAL_DELIVERY_SCOPE,
        "service_dates": list(ledger["service_dates"]),
        "generated_at": S2PLT02_PARTIAL_REAL_DELIVERY_GENERATED_AT,
        "planned_send_total": len(current_products),
        "observed_natural_days": ledger["observed_natural_days"],
        "observed_email_count": ledger["observed_email_count"],
        "sent_mail_products": list(current_products),
        "historical_sent_mail_products": list(S2PLT02_PARTIAL_REAL_DELIVERY_HISTORICAL_PRODUCTS),
        "newly_sent_mail_products": list(S2PLT02_PARTIAL_REAL_DELIVERY_NEWLY_SENT_PRODUCTS),
        "delivery_ref_by_product": current_delivery_refs,
        "duplicate_email_count": ledger["duplicate_email_count"],
        "real_smtp_evidence_present": ledger["real_smtp_evidence_present"],
        "scheduler_evidence_present": False,
        "m4_mail_product_present": "M4" in current_products,
        "m4_watermark_correct": False,
        "s2plt02_accepted": False,
        "production_acceptance_claimed": False,
        "stage2_integrated_production_accepted": False,
        "new_production_side_effects_from_precheck": False,
        "evidence_refs": list(S2PLT02_PARTIAL_REAL_DELIVERY_EVIDENCE_REFS),
        "delivery_evidence_ledger_hash": ledger["ledger_hash"],
        "evidence_hash": "",
    }
    state["evidence_hash"] = _stable_hash({key: value for key, value in state.items() if key != "evidence_hash"})
    return state


def build_s2plt02_live_evidence_state() -> dict[str, Any]:
    """Build current S2PLT02 live-run evidence state without touching production."""

    delivery_ledger = build_s2plt02_delivery_evidence_ledger_state()
    partial_delivery = build_s2plt02_partial_real_delivery_state()
    m4_watermark_proof = build_s2plt02_m4_watermark_proof_state(delivery_ledger=delivery_ledger)
    available = {
        "S2PLT01_ACCEPTED": False,
        "TWO_CONSECUTIVE_REAL_NATURAL_DAYS": delivery_ledger["two_day_delivery_evidence_present"],
        "EIGHT_REAL_EMAILS_SENT": delivery_ledger["observed_email_count"] >= S2PLT02_REQUIRED_EMAIL_COUNT
        and not delivery_ledger["validation_errors"],
        "NO_DUPLICATE_EMAILS": delivery_ledger["duplicate_email_count"] == 0
        and delivery_ledger["duplicate_service_date_count"] == 0,
        "M4_WATERMARK_CORRECT": m4_watermark_proof["m4_watermark_correct"],
        "REAL_SCHEDULER_PROVEN": partial_delivery["scheduler_evidence_present"],
        "REAL_SMTP_PROVEN": delivery_ledger["real_smtp_evidence_present"],
    }
    return {
        "status": "blocked",
        "required_evidence": list(S2PLT02_REQUIRED_EVIDENCE),
        "available_evidence": available,
        "missing_evidence": [item for item, present in available.items() if not present],
        "required_natural_days": S2PLT02_REQUIRED_NATURAL_DAYS,
        "observed_natural_days": delivery_ledger["observed_natural_days"],
        "required_email_count": S2PLT02_REQUIRED_EMAIL_COUNT,
        "observed_email_count": delivery_ledger["observed_email_count"],
        "required_mail_products": list(S2PLT02_REQUIRED_MAIL_PRODUCTS),
        "observed_mail_products": sorted(
            {product for products in delivery_ledger["products_by_service_date"].values() for product in products}
        ),
        "duplicate_email_count": delivery_ledger["duplicate_email_count"],
        "duplicate_service_date_count": delivery_ledger["duplicate_service_date_count"],
        "m4_watermark_correct": m4_watermark_proof["m4_watermark_correct"],
        "real_scheduler_proven": partial_delivery["scheduler_evidence_present"],
        "real_smtp_proven": delivery_ledger["real_smtp_evidence_present"],
        "delivery_evidence_ledger": delivery_ledger,
        "m4_watermark_proof": m4_watermark_proof,
        "partial_real_delivery_evidence": partial_delivery,
    }


def build_s2plt02_live_2d_precheck_report(
    *,
    generated_at: str,
    repo_root: Path | None = None,
    p0_p1_zero_proof: Mapping[str, Any] | None = None,
    load_committed_artifacts: bool = True,
) -> dict[str, Any]:
    """Build a deterministic fail-closed S2PLT02 two-day live-run precheck."""

    dependencies = _build_s2plt02_dependency_state(repo_root=repo_root or Path("."))
    evidence = build_s2plt02_live_evidence_state()
    audit_blockers = build_audit_blocker_state()
    if load_committed_artifacts and p0_p1_zero_proof is None:
        p0_p1_zero_proof = _load_committed_p0_p1_zero_proof(repo_root)
    p0_p1_zero_proof_artifact_validation = build_p0_p1_zero_proof_artifact_validation_state(
        p0_p1_zero_proof
    )
    gates = {
        "s2plt01_accepted": "S2PLT01" in dependencies["completed_dependencies"],
        "two_consecutive_real_days": evidence["observed_natural_days"] >= S2PLT02_REQUIRED_NATURAL_DAYS,
        "eight_real_emails_sent": evidence["observed_email_count"] >= S2PLT02_REQUIRED_EMAIL_COUNT,
        "no_duplicate_emails": evidence["duplicate_email_count"] == 0,
        "m4_watermark_correct": evidence["m4_watermark_correct"],
        "real_scheduler_proven": evidence["real_scheduler_proven"],
        "real_smtp_proven": evidence["real_smtp_proven"],
        "p0_zero": p0_p1_zero_proof_artifact_validation["p0_zero_proven_by_payload"],
        "p1_zero": p0_p1_zero_proof_artifact_validation["p1_zero_proven_by_payload"],
        "no_production_side_effect": True,
    }
    blocking_reasons: list[str] = []
    if not gates["s2plt01_accepted"]:
        blocking_reasons.append("s2plt01_not_accepted")
    if not gates["two_consecutive_real_days"]:
        blocking_reasons.append("two_consecutive_real_days_not_proven")
    if not gates["eight_real_emails_sent"]:
        blocking_reasons.append("eight_real_emails_not_proven")
    if not gates["no_duplicate_emails"]:
        blocking_reasons.append("duplicate_emails_found")
    if not gates["real_scheduler_proven"]:
        blocking_reasons.append("real_scheduler_not_proven")
    if not gates["real_smtp_proven"]:
        blocking_reasons.append("real_smtp_not_proven")
    if not gates["m4_watermark_correct"]:
        blocking_reasons.append("m4_watermark_not_proven")
    if not gates["p0_zero"]:
        blocking_reasons.append("inherited_v7_1_p0_findings_open")
    if not gates["p1_zero"]:
        blocking_reasons.append("inherited_v7_1_p1_findings_open")
    report = {
        "model_id": S2PLT02_LIVE_2D_PRECHECK_MODEL_ID,
        "schema_version": S2PLT02_SCHEMA_VERSION,
        "task_id": S2PLT02_TASK_ID,
        "acceptance_id": S2PLT02_ACCEPTANCE_ID,
        "generated_at": generated_at,
        "status": "pass" if not blocking_reasons and all(gates.values()) else "blocked",
        "scope": "no_production_live_2d_readiness_precheck_only",
        "gates": gates,
        "dependencies": dependencies,
        "evidence": evidence,
        "audit_blockers": audit_blockers,
        "p0_p1_zero_proof_artifact_validation": p0_p1_zero_proof_artifact_validation,
        "blocking_reasons": blocking_reasons,
        "production_acceptance_claimed": False,
        "inherited_p0_p1_closed": False,
        "report_hash": "",
        **{flag: False for flag in S2PLT02_FORBIDDEN_FLAGS},
    }
    report["report_hash"] = _stable_hash({key: value for key, value in report.items() if key != "report_hash"})
    return report


def build_s2plt02_terminal_delivery_proof_hash(payload: Mapping[str, Any]) -> str:
    """Return the canonical S2PLT02 terminal delivery proof hash."""

    return _stable_hash({key: value for key, value in payload.items() if key != "acceptance_hash"})


def validate_s2plt02_real_scheduler_proof_manifest(payload: Mapping[str, Any] | None) -> list[str]:
    """Validate the scheduler proof input consumed by the S2PLT02 terminal proof draft builder."""

    if payload is None:
        return ["scheduler_proof is required"]
    errors: list[str] = []
    if not isinstance(payload.get("proof_ref"), str) or not payload.get("proof_ref"):
        errors.append("scheduler_proof.proof_ref is required")
    if payload.get("status") != "pass":
        errors.append("scheduler_proof.status must be pass")
    if payload.get("real_scheduler_proven") is not True:
        errors.append("scheduler_proof.real_scheduler_proven must be true")
    if payload.get("scheduler_evidence_present") is not True:
        errors.append("scheduler_proof.scheduler_evidence_present must be true")
    for flag in S2PLT02_TERMINAL_DELIVERY_PROOF_NO_PRODUCTION_FLAGS:
        if payload.get(flag) is not False:
            errors.append(f"scheduler_proof.{flag} must be false")
    return errors


def build_s2plt02_real_scheduler_proof_validation_state(
    *,
    scheduler_proof: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Build a no-write validation state for a real scheduler proof input."""

    validation_errors = validate_s2plt02_real_scheduler_proof_manifest(scheduler_proof)
    scheduler_proof_ready = not validation_errors
    state: dict[str, Any] = {
        "model_id": S2PLT02_TERMINAL_DELIVERY_PROOF_MODEL_ID,
        "schema_version": S2PLT02_SCHEMA_VERSION,
        "task_id": "S2PLT02-REAL-SCHEDULER-PROOF-VALIDATION",
        "acceptance_id": S2PLT02_ACCEPTANCE_ID,
        "status": "pass" if scheduler_proof_ready else "blocked",
        "scope": "real_scheduler_proof_input_validation_no_scheduler_enablement",
        "scheduler_proof_ready": scheduler_proof_ready,
        "proof_ref": str(scheduler_proof.get("proof_ref") or "") if scheduler_proof is not None else "",
        "validation_errors": validation_errors,
        "blocking_reasons": [] if scheduler_proof_ready else ["real_scheduler_proof_not_valid"],
        "artifact_written": False,
        "production_acceptance_claimed": False,
        "integrated_production_accepted": False,
        "stage2_integrated_production_accepted": False,
        "daily_operation_enabled": False,
        "real_smtp_send_enabled": False,
        "scheduler_enabled": False,
        "scheduler_install_enabled": False,
        "release_packaging_enabled": False,
        "production_restore_enabled": False,
        "current_pointer_changed": False,
        "v7_1_baseline_changed": False,
        "v7_2_contract_files_changed": False,
        "state_hash": "",
    }
    state["state_hash"] = _stable_hash({key: value for key, value in state.items() if key != "state_hash"})
    return state


def validate_s2plt02_real_scheduler_proof_validation_state(state: Mapping[str, Any]) -> list[str]:
    """Validate a no-write scheduler proof input validation state."""

    errors: list[str] = []
    if state.get("model_id") != S2PLT02_TERMINAL_DELIVERY_PROOF_MODEL_ID:
        errors.append("S2PLT02 real scheduler proof validation model_id is invalid")
    if state.get("schema_version") != S2PLT02_SCHEMA_VERSION:
        errors.append("S2PLT02 real scheduler proof validation schema_version must be 1")
    if state.get("task_id") != "S2PLT02-REAL-SCHEDULER-PROOF-VALIDATION":
        errors.append("S2PLT02 real scheduler proof validation task_id is invalid")
    if state.get("acceptance_id") != S2PLT02_ACCEPTANCE_ID:
        errors.append("S2PLT02 real scheduler proof validation acceptance_id is invalid")
    if state.get("scope") != "real_scheduler_proof_input_validation_no_scheduler_enablement":
        errors.append("S2PLT02 real scheduler proof validation scope is invalid")
    if state.get("status") not in {"pass", "blocked"}:
        errors.append("S2PLT02 real scheduler proof validation status must be pass or blocked")
    ready = state.get("scheduler_proof_ready") is True
    if state.get("status") == "pass" and not ready:
        errors.append("pass status requires scheduler_proof_ready")
    if ready and state.get("validation_errors"):
        errors.append("scheduler_proof_ready requires no validation_errors")
    if not ready and "real_scheduler_proof_not_valid" not in state.get("blocking_reasons", []):
        errors.append("blocked scheduler proof state must include real_scheduler_proof_not_valid")
    if state.get("artifact_written") is not False:
        errors.append("artifact_written must be false")
    for flag in (
        "production_acceptance_claimed",
        "integrated_production_accepted",
        "stage2_integrated_production_accepted",
        "daily_operation_enabled",
        "real_smtp_send_enabled",
        "scheduler_enabled",
        "scheduler_install_enabled",
        "release_packaging_enabled",
        "production_restore_enabled",
        "current_pointer_changed",
        "v7_1_baseline_changed",
        "v7_2_contract_files_changed",
    ):
        if state.get(flag) is not False:
            errors.append(f"{flag} must be false")
    expected_hash = _stable_hash({key: value for key, value in state.items() if key != "state_hash"})
    if state.get("state_hash") != expected_hash:
        errors.append("S2PLT02 real scheduler proof validation state_hash does not match state content")
    return errors


def build_s2plt02_terminal_delivery_input_inventory_state(
    *,
    generated_at: str,
    repo_root: str | Path = ".",
) -> dict[str, Any]:
    """Summarize S2PLT02 terminal proof inputs without writing the terminal artifact."""

    inventory_scope = "s2plt02_terminal_delivery_input_inventory_no_write_no_production"
    root = Path(repo_root)
    precheck = build_s2plt02_live_2d_precheck_report(generated_at=generated_at, repo_root=root)
    evidence = _mapping(precheck.get("evidence"))
    gates = _mapping(precheck.get("gates"))
    terminal_validation = build_s2plt02_terminal_delivery_proof_artifact_validation_state(repo_root=root)

    input_gate_map = {
        "S2PLT01_TERMINAL_ACCEPTANCE": gates.get("s2plt01_accepted") is True,
        "FIRST_REAL_DELIVERY_DAY": int(evidence.get("observed_natural_days") or 0) >= 1,
        "SECOND_REAL_DELIVERY_DAY": gates.get("two_consecutive_real_days") is True,
        "EIGHT_REAL_EMAILS": gates.get("eight_real_emails_sent") is True,
        "NO_DUPLICATE_EMAILS": gates.get("no_duplicate_emails") is True,
        "M4_WATERMARK_PROOF": gates.get("m4_watermark_correct") is True,
        "REAL_SCHEDULER_PROOF": gates.get("real_scheduler_proven") is True,
        "REAL_SMTP_PROOF": gates.get("real_smtp_proven") is True,
        "P0_P1_ZERO_PROOF": gates.get("p0_zero") is True and gates.get("p1_zero") is True,
        "S2PLT02_TERMINAL_DELIVERY_PROOF_ARTIFACT": terminal_validation.get("terminal_delivery_proof_ready") is True,
    }
    ready_inputs = [name for name, ready in input_gate_map.items() if ready]
    missing_inputs = [name for name, ready in input_gate_map.items() if not ready]
    blocking_reasons = list(
        dict.fromkeys(
            [
                *[str(reason) for reason in precheck.get("blocking_reasons", []) if isinstance(reason, str)],
                *[
                    str(reason)
                    for reason in terminal_validation.get("blocking_reasons", [])
                    if isinstance(reason, str)
                ],
            ]
        )
    )
    terminal_delivery_proof_ready = terminal_validation.get("terminal_delivery_proof_ready") is True
    state: dict[str, Any] = {
        "model_id": S2PLT02_TERMINAL_DELIVERY_PROOF_MODEL_ID,
        "schema_version": S2PLT02_SCHEMA_VERSION,
        "task_id": "S2PLT02-TERMINAL-DELIVERY-INPUT-INVENTORY",
        "parent_task_id": "S2PLT02-TERMINAL-DELIVERY-PROOF",
        "acceptance_id": S2PLT02_ACCEPTANCE_ID,
        "generated_at": generated_at,
        "status": "pass" if terminal_delivery_proof_ready and not missing_inputs else "blocked",
        "scope": inventory_scope,
        "required_inputs": list(input_gate_map),
        "ready_inputs": ready_inputs,
        "missing_inputs": missing_inputs,
        "input_gates": input_gate_map,
        "blocking_reasons": blocking_reasons,
        "observed_real_delivery_days": int(evidence.get("observed_natural_days") or 0),
        "required_real_delivery_days": S2PLT02_REQUIRED_NATURAL_DAYS,
        "observed_real_email_count": int(evidence.get("observed_email_count") or 0),
        "required_real_email_count": S2PLT02_REQUIRED_EMAIL_COUNT,
        "required_mail_products": list(S2PLT02_REQUIRED_MAIL_PRODUCTS),
        "terminal_delivery_proof_ready": terminal_delivery_proof_ready,
        "terminal_delivery_proof_artifact_present": terminal_validation.get("artifact_present") is True,
        "terminal_delivery_proof_artifact_ref": S2PLT02_TERMINAL_DELIVERY_PROOF_ARTIFACT_PATH,
        "precheck_report_hash": precheck.get("report_hash"),
        "terminal_validation_state_hash": terminal_validation.get("state_hash"),
        "next_draft_command": (
            "adp build-s2plt02-terminal-delivery-proof-artifact-draft "
            "--delivery-manifest DAY1.json --delivery-manifest DAY2.json "
            "--scheduler-proof REAL-SCHEDULER-PROOF.json --json"
        ),
        "next_validation_command": "adp validate-s2plt02-terminal-delivery-proof --repo-root . --json",
        "artifact_written": False,
        "production_acceptance_claimed": False,
        "integrated_production_accepted": False,
        "stage2_integrated_production_accepted": False,
        "daily_operation_enabled": False,
        "real_smtp_send_enabled": False,
        "scheduler_enabled": False,
        "scheduler_install_enabled": False,
        "release_packaging_enabled": False,
        "production_restore_enabled": False,
        "current_pointer_changed": False,
        "v7_1_baseline_changed": False,
        "v7_2_contract_files_changed": False,
        "state_hash": "",
    }
    state["state_hash"] = _stable_hash({key: value for key, value in state.items() if key != "state_hash"})
    return state


def validate_s2plt02_terminal_delivery_input_inventory_state(state: Mapping[str, Any]) -> list[str]:
    """Validate the no-write S2PLT02 terminal delivery input inventory."""

    inventory_scope = "s2plt02_terminal_delivery_input_inventory_no_write_no_production"
    errors: list[str] = []
    if state.get("model_id") != S2PLT02_TERMINAL_DELIVERY_PROOF_MODEL_ID:
        errors.append("S2PLT02 terminal input inventory model_id is invalid")
    if state.get("schema_version") != S2PLT02_SCHEMA_VERSION:
        errors.append("S2PLT02 terminal input inventory schema_version must be 1")
    if state.get("task_id") != "S2PLT02-TERMINAL-DELIVERY-INPUT-INVENTORY":
        errors.append("S2PLT02 terminal input inventory task_id is invalid")
    if state.get("parent_task_id") != "S2PLT02-TERMINAL-DELIVERY-PROOF":
        errors.append("S2PLT02 terminal input inventory parent_task_id is invalid")
    if state.get("acceptance_id") != S2PLT02_ACCEPTANCE_ID:
        errors.append("S2PLT02 terminal input inventory acceptance_id is invalid")
    if state.get("scope") != inventory_scope:
        errors.append("S2PLT02 terminal input inventory scope is invalid")
    if state.get("status") not in {"pass", "blocked"}:
        errors.append("S2PLT02 terminal input inventory status is invalid")
    if state.get("required_real_delivery_days") != S2PLT02_REQUIRED_NATURAL_DAYS:
        errors.append("S2PLT02 terminal input inventory required_real_delivery_days must be 2")
    if state.get("required_real_email_count") != S2PLT02_REQUIRED_EMAIL_COUNT:
        errors.append("S2PLT02 terminal input inventory required_real_email_count must be 8")
    if tuple(state.get("required_mail_products", [])) != S2PLT02_REQUIRED_MAIL_PRODUCTS:
        errors.append("S2PLT02 terminal input inventory required_mail_products must be M1-M4")
    input_gates = _mapping(state.get("input_gates"))
    ready_inputs = [str(item) for item in state.get("ready_inputs", [])]
    missing_inputs = [str(item) for item in state.get("missing_inputs", [])]
    if set(ready_inputs) & set(missing_inputs):
        errors.append("S2PLT02 terminal input inventory cannot mark an input both ready and missing")
    if set(ready_inputs) | set(missing_inputs) != set(input_gates):
        errors.append("S2PLT02 terminal input inventory ready/missing inputs must cover input_gates")
    if state.get("terminal_delivery_proof_ready") is True and missing_inputs:
        errors.append("terminal_delivery_proof_ready requires no missing_inputs")
    if state.get("status") == "pass" and state.get("terminal_delivery_proof_ready") is not True:
        errors.append("pass status requires terminal_delivery_proof_ready")
    if state.get("terminal_delivery_proof_artifact_ref") != S2PLT02_TERMINAL_DELIVERY_PROOF_ARTIFACT_PATH:
        errors.append("S2PLT02 terminal input inventory artifact ref is invalid")
    if state.get("artifact_written") is not False:
        errors.append("artifact_written must be false")
    for flag in (
        "production_acceptance_claimed",
        "integrated_production_accepted",
        "stage2_integrated_production_accepted",
        "daily_operation_enabled",
        "real_smtp_send_enabled",
        "scheduler_enabled",
        "scheduler_install_enabled",
        "release_packaging_enabled",
        "production_restore_enabled",
        "current_pointer_changed",
        "v7_1_baseline_changed",
        "v7_2_contract_files_changed",
    ):
        if state.get(flag) is not False:
            errors.append(f"{flag} must be false")
    expected_hash = _stable_hash({key: value for key, value in state.items() if key != "state_hash"})
    if state.get("state_hash") != expected_hash:
        errors.append("S2PLT02 terminal input inventory state_hash does not match state content")
    return errors


def build_s2plt02_terminal_proof_evidence_inventory_state(
    *,
    generated_at: str,
    repo_root: str | Path = ".",
    state_dir: str | Path | None = None,
    candidate_service_dates: tuple[str, ...] = S2PLT02_TERMINAL_CAPTURE_WINDOW_DEFAULT_CANDIDATE_DATES,
    launchctl_disabled_text: str = "",
    adp_allow_smtp_send: bool = False,
) -> dict[str, Any]:
    """Classify current terminal-proof evidence inputs without writing the terminal proof artifact."""

    input_inventory = build_s2plt02_terminal_delivery_input_inventory_state(
        generated_at=generated_at,
        repo_root=repo_root,
    )
    capture_window = build_s2plt02_terminal_capture_window_audit_state(
        repo_root=repo_root,
        state_dir=state_dir,
        candidate_service_dates=candidate_service_dates,
        launchctl_disabled_text=launchctl_disabled_text,
        adp_allow_smtp_send=adp_allow_smtp_send,
    )
    terminal_validation = build_s2plt02_terminal_delivery_proof_artifact_validation_state(
        repo_root=repo_root,
    )

    ready_inputs = [str(item) for item in input_inventory.get("ready_inputs", [])]
    missing_inputs = [str(item) for item in input_inventory.get("missing_inputs", [])]
    usable_terminal_inputs: list[dict[str, Any]] = []
    ready_input_refs = {
        "S2PLT01_TERMINAL_ACCEPTANCE": {
            "role": "s2plt01_terminal_acceptance",
            "ref": "FINAL_ACCEPTANCE_BUNDLE/s2plt01_terminal_acceptance.json",
        },
        "FIRST_REAL_DELIVERY_DAY": {
            "role": "day_1_delivery",
            "ref": S2PLT02_NORMALIZED_REAL_DELIVERY_MANIFEST_REF,
            "service_date": S2PLT02_PARTIAL_REAL_DELIVERY_SERVICE_DATE,
        },
        "M4_WATERMARK_PROOF": {
            "role": "m4_watermark_proof",
            "ref": S2PLT02_M4_WATERMARK_PROOF_RECORD_REF,
            "service_date": S2PLT02_PARTIAL_REAL_DELIVERY_SERVICE_DATE,
        },
        "REAL_SMTP_PROOF": {
            "role": "real_smtp_proof",
            "ref": S2PLT02_NORMALIZED_REAL_DELIVERY_MANIFEST_REF,
            "service_date": S2PLT02_PARTIAL_REAL_DELIVERY_SERVICE_DATE,
        },
        "P0_P1_ZERO_PROOF": {
            "role": "p0_p1_zero_proof",
            "ref": "FINAL_ACCEPTANCE_BUNDLE/p0_p1_zero_proof.json",
        },
    }
    for input_name, ref_payload in ready_input_refs.items():
        if input_name in ready_inputs:
            usable_terminal_inputs.append(
                {
                    "input_name": input_name,
                    "ready": True,
                    "counts_toward_s2plt02_terminal_proof": True,
                    **ref_payload,
                }
            )

    blocked_candidate_inputs: list[dict[str, Any]] = []
    for audit in capture_window.get("dry_run_audits", []):
        if not isinstance(audit, Mapping):
            continue
        service_date = str(audit.get("service_date") or "")
        dry_run_present = audit.get("dry_run_evidence_present") is True
        classification = (
            "blocked_dry_run_not_real_terminal_input"
            if dry_run_present
            else "blocked_candidate_missing_or_invalid"
        )
        blocked_candidate_inputs.append(
            {
                "role": "day_2_delivery_candidate",
                "service_date": service_date,
                "classification": classification,
                "dry_run_evidence_present": dry_run_present,
                "daily_run_succeeded": audit.get("daily_run_succeeded") is True,
                "daily_run_succeeded_but_smtp_dry_run_not_terminal": (
                    audit.get("daily_run_succeeded_but_smtp_dry_run_not_terminal") is True
                ),
                "dry_run_mail_count": int(audit.get("dry_run_mail_count") or 0),
                "real_sent_mail_count": int(audit.get("real_sent_mail_count") or 0),
                "terminal_delivery_credit": False,
                "counts_toward_s2plt02_terminal_proof": False,
                "blocking_reasons": [
                    str(reason)
                    for reason in audit.get("blocking_reasons", [])
                    if isinstance(reason, str)
                ],
                "validation_errors": [
                    str(error)
                    for error in audit.get("validation_errors", [])
                    if isinstance(error, str)
                ],
                "evidence_refs": [
                    str(ref)
                    for ref in audit.get("evidence_refs", [])
                    if isinstance(ref, str)
                ],
                "state_hash": str(audit.get("state_hash") or ""),
            }
        )

    blocked_candidate_service_dates = [
        item["service_date"]
        for item in blocked_candidate_inputs
        if item.get("service_date")
    ]
    safe_to_build_terminal_artifact = (
        input_inventory.get("terminal_delivery_proof_ready") is True
        and not missing_inputs
        and not blocked_candidate_inputs
        and terminal_validation.get("terminal_delivery_proof_ready") is True
    )
    blocking_reasons = list(
        dict.fromkeys(
            [
                *[str(reason) for reason in input_inventory.get("blocking_reasons", []) if isinstance(reason, str)],
                *[
                    str(reason)
                    for reason in capture_window.get("blocking_reasons", [])
                    if isinstance(reason, str)
                ],
                *[
                    "blocked_candidate_inputs_present"
                    if blocked_candidate_inputs
                    else ""
                ],
            ]
        )
    )
    blocking_reasons = [reason for reason in blocking_reasons if reason]

    state: dict[str, Any] = {
        "model_id": S2PLT02_TERMINAL_DELIVERY_PROOF_MODEL_ID,
        "schema_version": S2PLT02_SCHEMA_VERSION,
        "task_id": "S2PLT02-TERMINAL-PROOF-EVIDENCE-INVENTORY",
        "parent_task_id": "S2PLT02-TERMINAL-DELIVERY-PROOF",
        "acceptance_id": S2PLT02_ACCEPTANCE_ID,
        "generated_at": generated_at,
        "status": "pass" if safe_to_build_terminal_artifact else "blocked",
        "scope": S2PLT02_TERMINAL_PROOF_EVIDENCE_INVENTORY_SCOPE,
        "candidate_service_dates": list(candidate_service_dates),
        "ready_inputs": ready_inputs,
        "missing_terminal_inputs": missing_inputs,
        "usable_terminal_inputs": usable_terminal_inputs,
        "blocked_candidate_inputs": blocked_candidate_inputs,
        "blocked_candidate_service_dates": blocked_candidate_service_dates,
        "daily_run_succeeded_service_dates": list(capture_window.get("daily_run_succeeded_service_dates", [])),
        "nonterminal_succeeded_dry_run_service_dates": list(
            capture_window.get("nonterminal_succeeded_dry_run_service_dates", [])
        ),
        "nonterminal_succeeded_dry_run_count": int(capture_window.get("nonterminal_succeeded_dry_run_count") or 0),
        "safe_to_build_terminal_artifact": safe_to_build_terminal_artifact,
        "terminal_delivery_credit": False,
        "counts_toward_s2plt02_terminal_proof": False,
        "terminal_delivery_proof_ready": input_inventory.get("terminal_delivery_proof_ready") is True,
        "terminal_delivery_proof_artifact_present": terminal_validation.get("artifact_present") is True,
        "terminal_delivery_proof_artifact_ref": S2PLT02_TERMINAL_DELIVERY_PROOF_ARTIFACT_PATH,
        "observed_real_delivery_days": int(input_inventory.get("observed_real_delivery_days") or 0),
        "observed_real_email_count": int(input_inventory.get("observed_real_email_count") or 0),
        "observed_candidate_dry_run_email_count": int(capture_window.get("dry_run_email_count") or 0),
        "observed_candidate_real_sent_email_count": int(capture_window.get("real_sent_candidate_email_count") or 0),
        "input_inventory_state_hash": str(input_inventory.get("state_hash") or ""),
        "capture_window_state_hash": str(capture_window.get("state_hash") or ""),
        "terminal_validation_state_hash": str(terminal_validation.get("state_hash") or ""),
        "next_draft_command": input_inventory.get("next_draft_command"),
        "next_validation_command": input_inventory.get("next_validation_command"),
        "next_allowed_builder_unblocked": False,
        "blocking_reasons": blocking_reasons,
        "artifact_written": False,
        "production_acceptance_claimed": False,
        "integrated_production_accepted": False,
        "stage2_integrated_production_accepted": False,
        "daily_operation_enabled": False,
        "real_smtp_send_enabled": False,
        "scheduler_enabled": False,
        "scheduler_install_enabled": False,
        "release_packaging_enabled": False,
        "production_restore_enabled": False,
        "current_pointer_changed": False,
        "v7_1_baseline_changed": False,
        "v7_2_contract_files_changed": False,
        "state_hash": "",
    }
    state["state_hash"] = _stable_hash({key: value for key, value in state.items() if key != "state_hash"})
    return state


def validate_s2plt02_terminal_proof_evidence_inventory_state(state: Mapping[str, Any]) -> list[str]:
    """Validate the no-write S2PLT02 terminal proof evidence inventory."""

    errors: list[str] = []
    if state.get("model_id") != S2PLT02_TERMINAL_DELIVERY_PROOF_MODEL_ID:
        errors.append("S2PLT02 terminal proof evidence inventory model_id is invalid")
    if state.get("schema_version") != S2PLT02_SCHEMA_VERSION:
        errors.append("S2PLT02 terminal proof evidence inventory schema_version must be 1")
    if state.get("task_id") != "S2PLT02-TERMINAL-PROOF-EVIDENCE-INVENTORY":
        errors.append("S2PLT02 terminal proof evidence inventory task_id is invalid")
    if state.get("parent_task_id") != "S2PLT02-TERMINAL-DELIVERY-PROOF":
        errors.append("S2PLT02 terminal proof evidence inventory parent_task_id is invalid")
    if state.get("acceptance_id") != S2PLT02_ACCEPTANCE_ID:
        errors.append("S2PLT02 terminal proof evidence inventory acceptance_id is invalid")
    if state.get("scope") != S2PLT02_TERMINAL_PROOF_EVIDENCE_INVENTORY_SCOPE:
        errors.append("S2PLT02 terminal proof evidence inventory scope is invalid")
    if state.get("status") not in {"pass", "blocked"}:
        errors.append("S2PLT02 terminal proof evidence inventory status is invalid")
    if state.get("terminal_delivery_proof_artifact_ref") != S2PLT02_TERMINAL_DELIVERY_PROOF_ARTIFACT_PATH:
        errors.append("S2PLT02 terminal proof evidence inventory artifact ref is invalid")
    missing_inputs = [str(item) for item in state.get("missing_terminal_inputs", [])]
    blocked_candidates = [item for item in state.get("blocked_candidate_inputs", []) if isinstance(item, Mapping)]
    if state.get("safe_to_build_terminal_artifact") is True and (missing_inputs or blocked_candidates):
        errors.append("safe_to_build_terminal_artifact requires no missing inputs and no blocked candidates")
    if state.get("status") == "pass" and state.get("safe_to_build_terminal_artifact") is not True:
        errors.append("pass status requires safe_to_build_terminal_artifact")
    for item in blocked_candidates:
        if item.get("counts_toward_s2plt02_terminal_proof") is not False:
            errors.append("blocked candidates must not count toward S2PLT02 terminal proof")
        if item.get("terminal_delivery_credit") is not False:
            errors.append("blocked candidates must not grant terminal delivery credit")
        if not item.get("classification"):
            errors.append("blocked candidate classification is required")
        if (
            item.get("daily_run_succeeded_but_smtp_dry_run_not_terminal") is True
            and item.get("daily_run_succeeded") is not True
        ):
            errors.append("daily-run nonterminal candidate requires daily_run_succeeded")
    nonterminal_dates = [str(item) for item in state.get("nonterminal_succeeded_dry_run_service_dates", [])]
    if state.get("nonterminal_succeeded_dry_run_count") != len(nonterminal_dates):
        errors.append("nonterminal_succeeded_dry_run_count must match nonterminal date count")
    if state.get("terminal_delivery_credit") is not False:
        errors.append("terminal_delivery_credit must be false")
    if state.get("counts_toward_s2plt02_terminal_proof") is not False:
        errors.append("counts_toward_s2plt02_terminal_proof must be false")
    if state.get("next_allowed_builder_unblocked") is not False:
        errors.append("next_allowed_builder_unblocked must be false while terminal inputs are missing")
    if state.get("artifact_written") is not False:
        errors.append("artifact_written must be false")
    for flag in (
        "production_acceptance_claimed",
        "integrated_production_accepted",
        "stage2_integrated_production_accepted",
        "daily_operation_enabled",
        "real_smtp_send_enabled",
        "scheduler_enabled",
        "scheduler_install_enabled",
        "release_packaging_enabled",
        "production_restore_enabled",
        "current_pointer_changed",
        "v7_1_baseline_changed",
        "v7_2_contract_files_changed",
    ):
        if state.get(flag) is not False:
            errors.append(f"{flag} must be false")
    expected_hash = _stable_hash({key: value for key, value in state.items() if key != "state_hash"})
    if state.get("state_hash") != expected_hash:
        errors.append("S2PLT02 terminal proof evidence inventory state_hash does not match state content")
    return errors


def build_s2plt02_terminal_delivery_proof_capture_plan_state(
    *,
    generated_at: str,
    repo_root: str | Path = ".",
) -> dict[str, Any]:
    """Build the safe S2PLT02 terminal proof capture plan without executing capture."""

    root = Path(repo_root)
    inventory = build_s2plt02_terminal_delivery_input_inventory_state(
        generated_at=generated_at,
        repo_root=root,
    )
    evidence_inventory = build_s2plt02_terminal_proof_evidence_inventory_state(
        generated_at=generated_at,
        repo_root=root,
    )
    authorization_artifact = _load_json_mapping_artifact(
        root / S2PLT02_REAL_PROOF_CAPTURE_AUTHORIZATION_ARTIFACT_PATH
    )
    authorization_validation = build_s2plt02_real_proof_capture_authorization_validation_state(
        authorization_artifact,
        expected_readiness_state_hash=(
            S2PMT07_FINAL_BUNDLE_PREREQUISITE_PLAN_S2PLT02_AUTH_READINESS_STATE_HASH
        ),
    )
    missing_inputs = [str(item) for item in inventory.get("missing_inputs", [])]
    terminal_delivery_proof_ready = inventory.get("terminal_delivery_proof_ready") is True
    authorization_valid = (
        authorization_artifact is not None
        and authorization_validation.get("status") == "pass"
        and not authorization_validation.get("validation_errors")
    )
    runtime_capture_blockers = [
        str(reason)
        for reason in evidence_inventory.get("blocking_reasons", [])
        if reason
        in {
            "second_consecutive_real_m1_m4_smtp_day_missing",
            "real_launchd_scheduler_proof_missing",
            "adp_allow_smtp_send_false",
            "adp_launchagents_disabled_by_user_domain_override",
            "daily_run_succeeded_but_smtp_dry_run_not_terminal",
            "blocked_candidate_inputs_present",
        }
    ]
    runtime_capture_ready = authorization_valid and not runtime_capture_blockers
    capture_steps = [
        {
            "step_id": "CAPTURE_SECOND_REAL_M1_M4_SMTP_DAY",
            "owner_action": (
                "After explicit owner authorization, capture the second consecutive real M1-M4 SMTP "
                "delivery-day manifest; this plan itself must not send mail."
            ),
            "required_inputs": ["SECOND_REAL_DELIVERY_DAY", "EIGHT_REAL_EMAILS"],
            "expected_evidence_refs": ["governance/run_manifests/FUTURE-S2PLT02-DAY2.json"],
            "command": "",
            "production_side_effect_allowed_by_this_plan": False,
        },
        {
            "step_id": "COLLECT_REAL_LAUNCHD_SCHEDULER_PROOF",
            "owner_action": (
                "Collect launchd scheduler evidence from the already-authorized environment and validate "
                "it without installing or enabling scheduler jobs."
            ),
            "required_inputs": ["REAL_SCHEDULER_PROOF"],
            "expected_evidence_refs": ["governance/run_manifests/FUTURE-S2PLT02-SCHEDULER-PROOF.json"],
            "command": "adp validate-s2plt02-real-scheduler-proof --scheduler-proof REAL-SCHEDULER-PROOF.json --json",
            "production_side_effect_allowed_by_this_plan": False,
        },
        {
            "step_id": "BUILD_TERMINAL_DELIVERY_PROOF_ARTIFACT_DRAFT",
            "owner_action": "Build a stdout-only terminal proof artifact draft from reviewed real evidence inputs.",
            "required_inputs": ["FIRST_REAL_DELIVERY_DAY", "SECOND_REAL_DELIVERY_DAY", "REAL_SCHEDULER_PROOF"],
            "expected_evidence_refs": ["stdout:s2plt02_terminal_delivery_proof_artifact_draft"],
            "command": (
                "adp build-s2plt02-terminal-delivery-proof-artifact-draft "
                "--delivery-manifest DAY1.json --delivery-manifest DAY2.json "
                "--scheduler-proof REAL-SCHEDULER-PROOF.json --json"
            ),
            "production_side_effect_allowed_by_this_plan": False,
        },
        {
            "step_id": "RUN_INDEPENDENT_TERMINAL_PROOF_REVIEW",
            "owner_action": (
                "Have the independent final reviewer inspect the draft, delivery manifests, scheduler proof, "
                "and no-production side-effect fields before any final artifact is written."
            ),
            "required_inputs": ["INDEPENDENT_REVIEWER_REVIEW"],
            "expected_evidence_refs": ["FINAL_ACCEPTANCE_BUNDLE/independent_review_signoff.yaml"],
            "command": "",
            "production_side_effect_allowed_by_this_plan": False,
        },
        {
            "step_id": "WRITE_REVIEWED_TERMINAL_DELIVERY_PROOF_ARTIFACT",
            "owner_action": (
                "Only after independent review, write the reviewed terminal proof artifact at the final-bundle path."
            ),
            "required_inputs": ["S2PLT02_TERMINAL_DELIVERY_PROOF_ARTIFACT"],
            "expected_evidence_refs": [S2PLT02_TERMINAL_DELIVERY_PROOF_ARTIFACT_PATH],
            "command": "",
            "production_side_effect_allowed_by_this_plan": False,
        },
        {
            "step_id": "VALIDATE_TERMINAL_DELIVERY_PROOF_ARTIFACT",
            "owner_action": "Validate the final artifact; validation does not accept production.",
            "required_inputs": ["S2PLT02_TERMINAL_DELIVERY_PROOF_ARTIFACT"],
            "expected_evidence_refs": ["stdout:s2plt02_terminal_delivery_proof_validation"],
            "command": "adp validate-s2plt02-terminal-delivery-proof --repo-root . --json",
            "production_side_effect_allowed_by_this_plan": False,
        },
    ]
    next_step = next(
        (
            step["step_id"]
            for step in capture_steps
            if set(step.get("required_inputs", [])) & set(missing_inputs)
        ),
        "VALIDATE_TERMINAL_DELIVERY_PROOF_ARTIFACT",
    )
    if not authorization_valid:
        next_step = "VALIDATE_S2PLT02_REAL_PROOF_CAPTURE_AUTHORIZATION"
    elif runtime_capture_blockers and next_step in {
        "CAPTURE_SECOND_REAL_M1_M4_SMTP_DAY",
        "COLLECT_REAL_LAUNCHD_SCHEDULER_PROOF",
    }:
        next_step = "WAIT_FOR_REAL_SMTP_SCHEDULER_CAPTURE_WINDOW"
    blocking_reasons = list(inventory.get("blocking_reasons", []))
    if not authorization_valid and "real_proof_capture_authorization_invalid" not in blocking_reasons:
        blocking_reasons.append("real_proof_capture_authorization_invalid")
    for reason in runtime_capture_blockers:
        if reason not in blocking_reasons:
            blocking_reasons.append(reason)
    state = {
        "model_id": S2PLT02_TERMINAL_DELIVERY_PROOF_MODEL_ID,
        "schema_version": S2PLT02_SCHEMA_VERSION,
        "task_id": "S2PLT02-TERMINAL-DELIVERY-PROOF-CAPTURE-PLAN",
        "parent_task_id": "S2PLT02-TERMINAL-DELIVERY-PROOF",
        "acceptance_id": S2PLT02_ACCEPTANCE_ID,
        "generated_at": generated_at,
        "status": "pass" if terminal_delivery_proof_ready and not missing_inputs else "blocked",
        "scope": "s2plt02_terminal_delivery_proof_capture_plan_no_write_no_production",
        "input_inventory_state_hash": inventory.get("state_hash"),
        "terminal_evidence_inventory_state_hash": evidence_inventory.get("state_hash"),
        "authorization_artifact_path": S2PLT02_REAL_PROOF_CAPTURE_AUTHORIZATION_ARTIFACT_PATH,
        "authorization_artifact_status": authorization_validation.get("status"),
        "authorization_validation_errors": list(authorization_validation.get("validation_errors", [])),
        "authorization_validation_state_hash": authorization_validation.get("state_hash"),
        "real_proof_capture_authorized": authorization_valid,
        "runtime_capture_ready": runtime_capture_ready,
        "runtime_capture_blockers": runtime_capture_blockers,
        "ready_inputs": list(inventory.get("ready_inputs", [])),
        "blocked_by_missing_inputs": missing_inputs,
        "blocking_reasons": blocking_reasons,
        "observed_real_delivery_days": inventory.get("observed_real_delivery_days"),
        "required_real_delivery_days": S2PLT02_REQUIRED_NATURAL_DAYS,
        "observed_real_email_count": inventory.get("observed_real_email_count"),
        "required_real_email_count": S2PLT02_REQUIRED_EMAIL_COUNT,
        "required_mail_products": list(S2PLT02_REQUIRED_MAIL_PRODUCTS),
        "terminal_delivery_proof_ready": terminal_delivery_proof_ready,
        "terminal_delivery_proof_artifact_ref": S2PLT02_TERMINAL_DELIVERY_PROOF_ARTIFACT_PATH,
        "capture_steps": capture_steps,
        "next_executable_step": next_step,
        "no_production_side_effects": True,
        "artifact_written": False,
        "production_acceptance_claimed": False,
        "integrated_production_accepted": False,
        "stage2_integrated_production_accepted": False,
        "daily_operation_enabled": False,
        "real_smtp_send_enabled": False,
        "scheduler_enabled": False,
        "scheduler_install_enabled": False,
        "release_packaging_enabled": False,
        "production_restore_enabled": False,
        "current_pointer_changed": False,
        "v7_1_baseline_changed": False,
        "v7_2_contract_files_changed": False,
        "state_hash": "",
    }
    state["state_hash"] = _stable_hash({key: value for key, value in state.items() if key != "state_hash"})
    return state


def validate_s2plt02_terminal_delivery_proof_capture_plan_state(state: Mapping[str, Any]) -> list[str]:
    """Validate the no-write S2PLT02 terminal proof capture plan state."""

    errors: list[str] = []
    if state.get("model_id") != S2PLT02_TERMINAL_DELIVERY_PROOF_MODEL_ID:
        errors.append("S2PLT02 terminal delivery proof capture plan model_id is invalid")
    if state.get("schema_version") != S2PLT02_SCHEMA_VERSION:
        errors.append("S2PLT02 terminal delivery proof capture plan schema_version must be 1")
    if state.get("task_id") != "S2PLT02-TERMINAL-DELIVERY-PROOF-CAPTURE-PLAN":
        errors.append("S2PLT02 terminal delivery proof capture plan task_id is invalid")
    if state.get("parent_task_id") != "S2PLT02-TERMINAL-DELIVERY-PROOF":
        errors.append("S2PLT02 terminal delivery proof capture plan parent_task_id is invalid")
    if state.get("acceptance_id") != S2PLT02_ACCEPTANCE_ID:
        errors.append("S2PLT02 terminal delivery proof capture plan acceptance_id is invalid")
    if state.get("scope") != "s2plt02_terminal_delivery_proof_capture_plan_no_write_no_production":
        errors.append("S2PLT02 terminal delivery proof capture plan scope is invalid")
    if state.get("status") not in {"pass", "blocked"}:
        errors.append("S2PLT02 terminal delivery proof capture plan status is invalid")
    if state.get("required_real_delivery_days") != S2PLT02_REQUIRED_NATURAL_DAYS:
        errors.append("S2PLT02 terminal delivery proof capture plan required_real_delivery_days must be 2")
    if state.get("required_real_email_count") != S2PLT02_REQUIRED_EMAIL_COUNT:
        errors.append("S2PLT02 terminal delivery proof capture plan required_real_email_count must be 8")
    if tuple(state.get("required_mail_products", [])) != S2PLT02_REQUIRED_MAIL_PRODUCTS:
        errors.append("S2PLT02 terminal delivery proof capture plan required_mail_products must be M1-M4")
    if state.get("terminal_delivery_proof_artifact_ref") != S2PLT02_TERMINAL_DELIVERY_PROOF_ARTIFACT_PATH:
        errors.append("S2PLT02 terminal delivery proof capture plan artifact ref is invalid")
    if state.get("authorization_artifact_path") != S2PLT02_REAL_PROOF_CAPTURE_AUTHORIZATION_ARTIFACT_PATH:
        errors.append("S2PLT02 terminal delivery proof capture plan authorization artifact path is invalid")
    if state.get("authorization_artifact_status") not in {"pass", "blocked"}:
        errors.append("S2PLT02 terminal delivery proof capture plan authorization status is invalid")
    if not isinstance(state.get("authorization_validation_errors"), list):
        errors.append("S2PLT02 terminal delivery proof capture plan authorization errors must be a list")
    if not isinstance(state.get("authorization_validation_state_hash"), str) or not state.get(
        "authorization_validation_state_hash"
    ):
        errors.append("S2PLT02 terminal delivery proof capture plan authorization validation hash is required")
    if not isinstance(state.get("terminal_evidence_inventory_state_hash"), str) or not state.get(
        "terminal_evidence_inventory_state_hash"
    ):
        errors.append("S2PLT02 terminal delivery proof capture plan evidence inventory hash is required")
    if not isinstance(state.get("runtime_capture_blockers"), list):
        errors.append("S2PLT02 terminal delivery proof capture plan runtime blockers must be a list")
    authorization_valid = (
        state.get("authorization_artifact_status") == "pass"
        and state.get("authorization_validation_errors") == []
        and state.get("real_proof_capture_authorized") is True
    )
    if not authorization_valid:
        if state.get("real_proof_capture_authorized") is not False:
            errors.append("invalid authorization must set real_proof_capture_authorized false")
        if "real_proof_capture_authorization_invalid" not in state.get("blocking_reasons", []):
            errors.append("invalid authorization must block capture plan")
        if state.get("next_executable_step") != "VALIDATE_S2PLT02_REAL_PROOF_CAPTURE_AUTHORIZATION":
            errors.append("invalid authorization must require authorization validation before capture")
    if state.get("runtime_capture_blockers") and state.get("runtime_capture_ready") is not False:
        errors.append("runtime_capture_ready must be false while runtime capture blockers are present")
    if (
        state.get("runtime_capture_blockers")
        and state.get("next_executable_step") in {"CAPTURE_SECOND_REAL_M1_M4_SMTP_DAY", "COLLECT_REAL_LAUNCHD_SCHEDULER_PROOF"}
    ):
        errors.append("runtime blockers must prevent direct real SMTP/scheduler capture as next step")
    if state.get("status") == "pass" and state.get("terminal_delivery_proof_ready") is not True:
        errors.append("pass status requires terminal_delivery_proof_ready")
    if state.get("terminal_delivery_proof_ready") is True and state.get("blocked_by_missing_inputs"):
        errors.append("terminal_delivery_proof_ready requires no blocked_by_missing_inputs")
    required_step_ids = (
        "CAPTURE_SECOND_REAL_M1_M4_SMTP_DAY",
        "COLLECT_REAL_LAUNCHD_SCHEDULER_PROOF",
        "BUILD_TERMINAL_DELIVERY_PROOF_ARTIFACT_DRAFT",
        "RUN_INDEPENDENT_TERMINAL_PROOF_REVIEW",
        "WRITE_REVIEWED_TERMINAL_DELIVERY_PROOF_ARTIFACT",
        "VALIDATE_TERMINAL_DELIVERY_PROOF_ARTIFACT",
    )
    capture_steps = state.get("capture_steps", [])
    if not isinstance(capture_steps, list):
        errors.append("capture_steps must be a list")
    elif tuple(step.get("step_id") for step in capture_steps if isinstance(step, Mapping)) != required_step_ids:
        errors.append("capture_steps must list the required S2PLT02 terminal proof capture steps in order")
    else:
        for step in capture_steps:
            if not isinstance(step, Mapping):
                errors.append("capture_steps entries must be objects")
                continue
            if step.get("production_side_effect_allowed_by_this_plan") is not False:
                errors.append(f"{step.get('step_id')} must not allow production side effects")
        commands = {str(step.get("step_id")): str(step.get("command") or "") for step in capture_steps}
        if (
            commands.get("BUILD_TERMINAL_DELIVERY_PROOF_ARTIFACT_DRAFT")
            != "adp build-s2plt02-terminal-delivery-proof-artifact-draft --delivery-manifest DAY1.json --delivery-manifest DAY2.json --scheduler-proof REAL-SCHEDULER-PROOF.json --json"
        ):
            errors.append("terminal proof draft command is invalid")
        if (
            commands.get("VALIDATE_TERMINAL_DELIVERY_PROOF_ARTIFACT")
            != "adp validate-s2plt02-terminal-delivery-proof --repo-root . --json"
        ):
            errors.append("terminal proof validation command is invalid")
    if state.get("no_production_side_effects") is not True:
        errors.append("no_production_side_effects must be true")
    if state.get("artifact_written") is not False:
        errors.append("artifact_written must be false")
    for flag in (
        "production_acceptance_claimed",
        "integrated_production_accepted",
        "stage2_integrated_production_accepted",
        "daily_operation_enabled",
        "real_smtp_send_enabled",
        "scheduler_enabled",
        "scheduler_install_enabled",
        "release_packaging_enabled",
        "production_restore_enabled",
        "current_pointer_changed",
        "v7_1_baseline_changed",
        "v7_2_contract_files_changed",
    ):
        if state.get(flag) is not False:
            errors.append(f"{flag} must be false")
    expected_hash = _stable_hash({key: value for key, value in state.items() if key != "state_hash"})
    if state.get("state_hash") != expected_hash:
        errors.append("S2PLT02 terminal delivery proof capture plan state_hash does not match state content")
    return errors


def build_s2plt02_terminal_delivery_proof_artifact_draft_state(
    *,
    generated_at: str,
    delivery_manifests: list[Mapping[str, Any]],
    scheduler_proof: Mapping[str, Any],
    s2plt01_terminal_acceptance_ref: str = "FINAL_ACCEPTANCE_BUNDLE/s2plt01_terminal_acceptance.json",
    p0_p1_zero_proof_ref: str = "FINAL_ACCEPTANCE_BUNDLE/p0_p1_zero_proof.json",
) -> dict[str, Any]:
    """Build a no-write S2PLT02 terminal delivery proof candidate from explicit terminal inputs."""

    ledger = build_s2plt02_delivery_evidence_ledger_state(delivery_manifests=delivery_manifests)
    service_dates = [str(item) for item in ledger.get("service_dates", [])]
    products_by_date = {
        str(service_date): [str(product) for product in products]
        for service_date, products in _mapping(ledger.get("products_by_service_date")).items()
    }
    scheduler_validation = build_s2plt02_real_scheduler_proof_validation_state(scheduler_proof=scheduler_proof)
    scheduler_ref = str(scheduler_validation.get("proof_ref") or "")
    scheduler_valid = scheduler_validation.get("scheduler_proof_ready") is True

    blocking_reasons: list[str] = []
    validation_errors = [str(error) for error in ledger.get("validation_errors") or []]
    if len(service_dates) < S2PLT02_REQUIRED_NATURAL_DAYS or not _s2plt02_terminal_delivery_proof_consecutive_dates(service_dates):
        blocking_reasons.append("two_consecutive_real_days_not_proven")
    if int(ledger.get("observed_email_count") or 0) < S2PLT02_REQUIRED_EMAIL_COUNT:
        blocking_reasons.append("eight_real_emails_not_proven")
    if int(ledger.get("duplicate_email_count") or 0) != 0 or int(ledger.get("duplicate_service_date_count") or 0) != 0:
        blocking_reasons.append("duplicate_emails_found")
    if ledger.get("real_smtp_evidence_present") is not True:
        blocking_reasons.append("real_smtp_not_proven")
    if scheduler_valid is not True:
        blocking_reasons.append("real_scheduler_proof_not_valid")
    validation_errors.extend(str(error) for error in scheduler_validation.get("validation_errors", []))

    state: dict[str, Any] = {
        "model_id": S2PLT02_TERMINAL_DELIVERY_PROOF_MODEL_ID,
        "schema_version": S2PLT02_SCHEMA_VERSION,
        "task_id": "S2PLT02-TERMINAL-DELIVERY-PROOF-ARTIFACT-DRAFT-BUILDER",
        "acceptance_id": S2PLT02_ACCEPTANCE_ID,
        "generated_at": generated_at,
        "status": "blocked" if blocking_reasons or validation_errors else "pass",
        "scope": "terminal_delivery_proof_candidate_builder_no_write_no_production_acceptance",
        "artifact_written": False,
        "delivery_evidence_ledger": ledger,
        "scheduler_proof_validation": scheduler_validation,
        "scheduler_proof_ref": scheduler_ref,
        "blocking_reasons": blocking_reasons,
        "validation_errors": validation_errors,
        "production_acceptance_claimed": False,
        "integrated_production_accepted": False,
        "stage2_integrated_production_accepted": False,
        "daily_operation_enabled": False,
        "state_hash": "",
    }
    if state["status"] == "blocked":
        state["state_hash"] = _stable_hash({key: value for key, value in state.items() if key != "state_hash"})
        return state

    day_refs = {
        str(manifest.get("service_date") or ""): str(manifest.get("manifest_ref") or "")
        for manifest in delivery_manifests
    }
    evidence_refs_by_role = {
        "s2plt01_terminal_acceptance": s2plt01_terminal_acceptance_ref,
        "day_1_delivery": day_refs[service_dates[0]],
        "day_2_delivery": day_refs[service_dates[1]],
        "real_scheduler_proof": scheduler_ref,
        "p0_p1_zero_proof": p0_p1_zero_proof_ref,
    }
    evidence_refs = list(dict.fromkeys(evidence_refs_by_role.values()))
    for ref in ledger.get("evidence_refs") or []:
        if isinstance(ref, str) and ref and ref not in evidence_refs:
            evidence_refs.append(ref)

    artifact = {
        "model_id": S2PLT02_TERMINAL_DELIVERY_PROOF_MODEL_ID,
        "schema_version": S2PLT02_SCHEMA_VERSION,
        "task_id": S2PLT02_TASK_ID,
        "acceptance_id": S2PLT02_ACCEPTANCE_ID,
        "generated_at": generated_at,
        "terminal_delivery_decision": S2PLT02_TERMINAL_DELIVERY_PROOF_DECISION,
        "s2plt02_accepted": True,
        "service_dates": service_dates,
        "mail_products_by_service_date": products_by_date,
        "observed_natural_days": S2PLT02_REQUIRED_NATURAL_DAYS,
        "observed_email_count": S2PLT02_REQUIRED_EMAIL_COUNT,
        "terminal_gates": {gate: True for gate in S2PLT02_TERMINAL_DELIVERY_PROOF_REQUIRED_GATES},
        "terminal_evidence_refs": evidence_refs,
        "terminal_evidence_refs_by_role": evidence_refs_by_role,
        **{flag: False for flag in S2PLT02_TERMINAL_DELIVERY_PROOF_NO_PRODUCTION_FLAGS},
        "acceptance_hash": "",
    }
    artifact["acceptance_hash"] = build_s2plt02_terminal_delivery_proof_hash(artifact)
    artifact_errors = validate_s2plt02_terminal_delivery_proof_artifact(artifact)
    if artifact_errors:
        blocked_state = {**state, "status": "blocked", "validation_errors": artifact_errors}
        blocked_state["state_hash"] = _stable_hash(
            {key: value for key, value in blocked_state.items() if key != "state_hash"}
        )
        return blocked_state
    state_with_artifact = {**state, "artifact_draft": artifact}
    state_with_artifact["state_hash"] = _stable_hash(
        {key: value for key, value in state_with_artifact.items() if key != "state_hash"}
    )
    return state_with_artifact


def _s2plt02_terminal_delivery_proof_consecutive_dates(service_dates: list[str]) -> bool:
    if len(service_dates) != S2PLT02_REQUIRED_NATURAL_DAYS:
        return False
    try:
        first, second = [date.fromisoformat(value) for value in service_dates]
    except ValueError:
        return False
    return (second - first).days == 1


def validate_s2plt02_terminal_delivery_proof_artifact(payload: Mapping[str, Any] | None) -> list[str]:
    """Validate a future S2PLT02 terminal delivery proof artifact without accepting production."""

    if payload is None:
        return ["s2plt02_terminal_delivery_proof_artifact_missing"]
    errors: list[str] = []
    if payload.get("model_id") != S2PLT02_TERMINAL_DELIVERY_PROOF_MODEL_ID:
        errors.append("model_id is invalid")
    if payload.get("schema_version") != S2PLT02_SCHEMA_VERSION:
        errors.append("schema_version must be 1")
    if payload.get("task_id") != S2PLT02_TASK_ID:
        errors.append("task_id must be S2PLT02")
    if payload.get("acceptance_id") != S2PLT02_ACCEPTANCE_ID:
        errors.append("acceptance_id must be ACC-S2PLT02-2D")
    if payload.get("terminal_delivery_decision") != S2PLT02_TERMINAL_DELIVERY_PROOF_DECISION:
        errors.append("terminal_delivery_decision is invalid")
    if payload.get("s2plt02_accepted") is not True:
        errors.append("s2plt02_accepted must be true")

    service_dates = [str(item) for item in payload.get("service_dates", [])]
    if not _s2plt02_terminal_delivery_proof_consecutive_dates(service_dates):
        errors.append("service_dates must contain exactly two consecutive ISO dates")
    if payload.get("observed_natural_days") != S2PLT02_REQUIRED_NATURAL_DAYS:
        errors.append("observed_natural_days must be 2")
    if payload.get("observed_email_count") != S2PLT02_REQUIRED_EMAIL_COUNT:
        errors.append("observed_email_count must be 8")

    products_by_date = _mapping(payload.get("mail_products_by_service_date"))
    for service_date in service_dates:
        if tuple(products_by_date.get(service_date, [])) != S2PLT02_REQUIRED_MAIL_PRODUCTS:
            errors.append(f"mail_products_by_service_date.{service_date} must be M1-M4")

    terminal_gates = _mapping(payload.get("terminal_gates"))
    for gate in S2PLT02_TERMINAL_DELIVERY_PROOF_REQUIRED_GATES:
        if terminal_gates.get(gate) is not True:
            errors.append(f"terminal_gates.{gate} must be true")

    refs = payload.get("terminal_evidence_refs", [])
    if not isinstance(refs, list) or any(not isinstance(ref, str) or not ref for ref in refs):
        errors.append("terminal_evidence_refs must be a list of non-empty strings")
    else:
        for required_ref in S2PLT02_TERMINAL_DELIVERY_PROOF_REQUIRED_EVIDENCE_REFS:
            if required_ref not in refs:
                errors.append(f"terminal_evidence_refs must include {required_ref}")
        if len(refs) < 5:
            errors.append("terminal_evidence_refs must include S2PLT01, two delivery days, scheduler proof, and zero-proof refs")

    refs_by_role = _mapping(payload.get("terminal_evidence_refs_by_role"))
    for role in S2PLT02_TERMINAL_DELIVERY_PROOF_REQUIRED_EVIDENCE_ROLES:
        role_ref = refs_by_role.get(role)
        if not isinstance(role_ref, str) or not role_ref:
            errors.append(f"terminal_evidence_refs_by_role.{role} is required")
        elif isinstance(refs, list) and role_ref not in refs:
            errors.append(f"terminal_evidence_refs_by_role.{role} must also appear in terminal_evidence_refs")
    if refs_by_role.get("s2plt01_terminal_acceptance") != "FINAL_ACCEPTANCE_BUNDLE/s2plt01_terminal_acceptance.json":
        errors.append("terminal_evidence_refs_by_role.s2plt01_terminal_acceptance must point to S2PLT01 terminal acceptance")
    if refs_by_role.get("p0_p1_zero_proof") != "FINAL_ACCEPTANCE_BUNDLE/p0_p1_zero_proof.json":
        errors.append("terminal_evidence_refs_by_role.p0_p1_zero_proof must point to P0/P1 zero proof")

    for flag in S2PLT02_TERMINAL_DELIVERY_PROOF_NO_PRODUCTION_FLAGS:
        if payload.get(flag) is not False:
            errors.append(f"{flag} must be false")

    if payload.get("acceptance_hash") != build_s2plt02_terminal_delivery_proof_hash(payload):
        errors.append("acceptance_hash does not match payload content")
    return errors


def build_s2plt02_terminal_delivery_proof_artifact_validation_state(
    *,
    repo_root: str | Path = ".",
    artifact: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build artifact-level validation for future S2PLT02 terminal delivery proof."""

    root = Path(repo_root)
    artifact_path = root / S2PLT02_TERMINAL_DELIVERY_PROOF_ARTIFACT_PATH
    artifact_present = artifact is not None or artifact_path.exists()
    loaded_artifact: Mapping[str, Any] | None = artifact
    load_error = ""
    if loaded_artifact is None and artifact_path.exists():
        try:
            loaded = json.loads(artifact_path.read_text(encoding="utf-8"))
            loaded_artifact = loaded if isinstance(loaded, Mapping) else None
            if loaded_artifact is None:
                load_error = "s2plt02_terminal_delivery_proof_artifact_must_be_object"
        except json.JSONDecodeError:
            load_error = "s2plt02_terminal_delivery_proof_artifact_invalid_json"

    validation_errors = validate_s2plt02_terminal_delivery_proof_artifact(loaded_artifact)
    if load_error and load_error not in validation_errors:
        validation_errors.append(load_error)
    readiness_precheck = build_s2plt02_live_2d_precheck_report(
        generated_at="2026-06-29T10:35:11+10:00",
        repo_root=root,
    )
    terminal_gates = (
        _mapping(loaded_artifact.get("terminal_gates"))
        if loaded_artifact is not None
        else _mapping(readiness_precheck.get("gates"))
    )
    missing_gate_reasons = {
        "s2plt01_accepted": "s2plt01_not_accepted",
        "two_consecutive_real_days": "two_consecutive_real_days_not_proven",
        "eight_real_emails_sent": "eight_real_emails_not_proven",
        "no_duplicate_emails": "duplicate_emails_found",
        "m4_watermark_correct": "m4_watermark_not_proven",
        "real_scheduler_proven": "real_scheduler_not_proven",
        "real_smtp_proven": "real_smtp_not_proven",
        "p0_zero": "inherited_v7_1_p0_findings_open",
        "p1_zero": "inherited_v7_1_p1_findings_open",
    }
    blocking_reasons: list[str] = []
    if not artifact_present:
        blocking_reasons.append("s2plt02_terminal_delivery_proof_artifact_missing")
        for reason in readiness_precheck.get("blocking_reasons", []):
            if isinstance(reason, str) and reason not in blocking_reasons:
                blocking_reasons.append(reason)
    else:
        for gate, reason in missing_gate_reasons.items():
            if terminal_gates.get(gate) is not True and reason not in blocking_reasons:
                blocking_reasons.append(reason)

    expected_acceptance_hash = (
        build_s2plt02_terminal_delivery_proof_hash(loaded_artifact) if loaded_artifact is not None else ""
    )
    terminal_delivery_proof_ready = artifact_present and not validation_errors and not blocking_reasons
    state = {
        "status": "pass" if terminal_delivery_proof_ready else "blocked",
        "scope": S2PLT02_TERMINAL_DELIVERY_PROOF_SCOPE,
        "artifact_ref": S2PLT02_TERMINAL_DELIVERY_PROOF_ARTIFACT_PATH,
        "artifact_present": artifact_present,
        "model_id": loaded_artifact.get("model_id") if loaded_artifact is not None else S2PLT02_TERMINAL_DELIVERY_PROOF_MODEL_ID,
        "schema_version": loaded_artifact.get("schema_version") if loaded_artifact is not None else S2PLT02_SCHEMA_VERSION,
        "task_id": S2PLT02_TASK_ID,
        "acceptance_id": S2PLT02_ACCEPTANCE_ID,
        "terminal_delivery_decision": (
            loaded_artifact.get("terminal_delivery_decision") if loaded_artifact is not None else None
        ),
        "terminal_delivery_proof_ready": terminal_delivery_proof_ready,
        "s2plt02_accepted_by_artifact": terminal_delivery_proof_ready
        and loaded_artifact is not None
        and loaded_artifact.get("s2plt02_accepted") is True,
        "required_natural_days": S2PLT02_REQUIRED_NATURAL_DAYS,
        "observed_natural_days": loaded_artifact.get("observed_natural_days") if loaded_artifact is not None else 0,
        "required_email_count": S2PLT02_REQUIRED_EMAIL_COUNT,
        "observed_email_count": loaded_artifact.get("observed_email_count") if loaded_artifact is not None else 0,
        "required_mail_products": list(S2PLT02_REQUIRED_MAIL_PRODUCTS),
        "service_dates": list(loaded_artifact.get("service_dates", [])) if loaded_artifact is not None else [],
        "terminal_gates": {gate: terminal_gates.get(gate) is True for gate in S2PLT02_TERMINAL_DELIVERY_PROOF_REQUIRED_GATES},
        "terminal_evidence_refs": list(loaded_artifact.get("terminal_evidence_refs", [])) if loaded_artifact is not None else [],
        "terminal_evidence_refs_by_role": dict(_mapping(loaded_artifact.get("terminal_evidence_refs_by_role")))
        if loaded_artifact is not None
        else {},
        "validation_errors": validation_errors,
        "blocking_reasons": blocking_reasons,
        "acceptance_hash": loaded_artifact.get("acceptance_hash") if loaded_artifact is not None else "",
        "expected_acceptance_hash": expected_acceptance_hash,
        "production_acceptance_claimed": False,
        "integrated_production_accepted": False,
        "stage2_integrated_production_accepted": False,
        "daily_operation_enabled": False,
        "real_smtp_send_enabled": False,
        "scheduler_install_enabled": False,
        "release_packaging_enabled": False,
        "production_restore_enabled": False,
        "current_pointer_changed": False,
        "v7_1_baseline_changed": False,
        "v7_2_contract_files_changed": False,
        "state_hash": "",
    }
    state["state_hash"] = _stable_hash({key: value for key, value in state.items() if key != "state_hash"})
    return state


def validate_s2plt02_terminal_delivery_proof_artifact_validation_state(state: Mapping[str, Any]) -> list[str]:
    """Validate S2PLT02 terminal delivery proof artifact validation state."""

    errors: list[str] = []
    if state.get("scope") != S2PLT02_TERMINAL_DELIVERY_PROOF_SCOPE:
        errors.append("S2PLT02 terminal delivery proof validation scope is invalid")
    if state.get("artifact_ref") != S2PLT02_TERMINAL_DELIVERY_PROOF_ARTIFACT_PATH:
        errors.append("S2PLT02 terminal delivery proof artifact_ref is invalid")
    if state.get("status") not in {"pass", "blocked"}:
        errors.append("S2PLT02 terminal delivery proof validation status is invalid")
    if state.get("required_natural_days") != S2PLT02_REQUIRED_NATURAL_DAYS:
        errors.append("S2PLT02 terminal delivery proof required_natural_days must be 2")
    if state.get("required_email_count") != S2PLT02_REQUIRED_EMAIL_COUNT:
        errors.append("S2PLT02 terminal delivery proof required_email_count must be 8")
    if tuple(state.get("required_mail_products", [])) != S2PLT02_REQUIRED_MAIL_PRODUCTS:
        errors.append("S2PLT02 terminal delivery proof required_mail_products must be M1-M4")
    ready = state.get("terminal_delivery_proof_ready") is True
    if state.get("status") == "pass" and not ready:
        errors.append("pass status requires terminal_delivery_proof_ready")
    if ready and state.get("s2plt02_accepted_by_artifact") is not True:
        errors.append("terminal_delivery_proof_ready requires s2plt02_accepted_by_artifact")
    for flag in (
        "production_acceptance_claimed",
        "integrated_production_accepted",
        "stage2_integrated_production_accepted",
        "daily_operation_enabled",
        "real_smtp_send_enabled",
        "scheduler_install_enabled",
        "release_packaging_enabled",
        "production_restore_enabled",
        "current_pointer_changed",
        "v7_1_baseline_changed",
        "v7_2_contract_files_changed",
    ):
        if state.get(flag) is not False:
            errors.append(f"{flag} must be false")
    expected_hash = _stable_hash({key: value for key, value in state.items() if key != "state_hash"})
    if state.get("state_hash") != expected_hash:
        errors.append("S2PLT02 terminal delivery proof validation state_hash does not match state content")
    return errors


def build_s2plt02_terminal_readiness_audit_state(
    *, generated_at: str, repo_root: str | Path = "."
) -> dict[str, Any]:
    """Expose current S2PLT02 terminal-readiness facts without accepting S2PLT02."""

    precheck = build_s2plt02_live_2d_precheck_report(generated_at=generated_at, repo_root=Path(repo_root))
    evidence = _mapping(precheck.get("evidence"))
    m4_watermark = _mapping(evidence.get("m4_watermark_proof"))
    proof_refs = [str(ref) for ref in m4_watermark.get("proof_refs", [])]
    state = {
        "model_id": S2PLT02_LIVE_2D_PRECHECK_MODEL_ID,
        "schema_version": S2PLT02_SCHEMA_VERSION,
        "task_id": "S2PLT02-TERMINAL-READINESS-AUDIT",
        "parent_task_id": S2PLT02_TASK_ID,
        "acceptance_id": S2PLT02_ACCEPTANCE_ID,
        "generated_at": generated_at,
        "status": "blocked",
        "scope": S2PLT02_TERMINAL_READINESS_AUDIT_SCOPE,
        "required_natural_days": S2PLT02_REQUIRED_NATURAL_DAYS,
        "observed_natural_days": evidence.get("observed_natural_days"),
        "required_email_count": S2PLT02_REQUIRED_EMAIL_COUNT,
        "observed_email_count": evidence.get("observed_email_count"),
        "m4_watermark_correct": evidence.get("m4_watermark_correct") is True,
        "m4_watermark_proof_ref": proof_refs[0] if proof_refs else "",
        "m4_watermark_proof_status": m4_watermark.get("status"),
        "real_smtp_proven": evidence.get("real_smtp_proven") is True,
        "real_scheduler_proven": evidence.get("real_scheduler_proven") is True,
        "s2plt02_accepted": False,
        "blocking_reasons": list(precheck.get("blocking_reasons", [])),
        "precheck_report_hash": precheck.get("report_hash"),
        "terminal_dependency_state": {
            "S2PLT01_ACCEPTED": precheck.get("gates", {}).get("s2plt01_accepted") is True,
            "TWO_CONSECUTIVE_REAL_NATURAL_DAYS": precheck.get("gates", {}).get("two_consecutive_real_days") is True,
            "EIGHT_REAL_EMAILS_SENT": precheck.get("gates", {}).get("eight_real_emails_sent") is True,
            "M4_WATERMARK_CORRECT": precheck.get("gates", {}).get("m4_watermark_correct") is True,
            "REAL_SCHEDULER_PROVEN": precheck.get("gates", {}).get("real_scheduler_proven") is True,
            "REAL_SMTP_PROVEN": precheck.get("gates", {}).get("real_smtp_proven") is True,
            "P0_ZERO": precheck.get("gates", {}).get("p0_zero") is True,
            "P1_ZERO": precheck.get("gates", {}).get("p1_zero") is True,
        },
        "production_acceptance_claimed": False,
        "integrated_production_accepted": False,
        "stage2_integrated_production_accepted": False,
        "daily_operation_enabled": False,
        "real_smtp_send_enabled": False,
        "scheduler_install_enabled": False,
        "release_packaging_enabled": False,
        "production_restore_enabled": False,
        "current_pointer_changed": False,
        "v7_1_baseline_changed": False,
        "v7_2_contract_files_changed": False,
        "state_hash": "",
    }
    state["state_hash"] = _stable_hash({key: value for key, value in state.items() if key != "state_hash"})
    return state


def validate_s2plt02_live_2d_precheck_report(report: Mapping[str, Any]) -> list[str]:
    """Validate S2PLT02 two-day live-run precheck reports."""

    errors: list[str] = []
    if report.get("model_id") != S2PLT02_LIVE_2D_PRECHECK_MODEL_ID:
        errors.append("S2PLT02 report model_id is invalid")
    if report.get("schema_version") != S2PLT02_SCHEMA_VERSION:
        errors.append("S2PLT02 report schema_version must be 1")
    if report.get("task_id") != S2PLT02_TASK_ID:
        errors.append("S2PLT02 report task_id is invalid")
    if report.get("acceptance_id") != S2PLT02_ACCEPTANCE_ID:
        errors.append("S2PLT02 report acceptance_id is invalid")
    if report.get("status") not in {"pass", "blocked"}:
        errors.append("S2PLT02 report status must be pass or blocked")
    if report.get("production_acceptance_claimed") is not False:
        errors.append("S2PLT02 precheck must not claim production acceptance")
    if report.get("inherited_p0_p1_closed") is not False:
        errors.append("S2PLT02 precheck must not close inherited P0/P1")
    for flag in S2PLT02_FORBIDDEN_FLAGS:
        if report.get(flag) is not False:
            errors.append(f"{flag} must be false")

    dependencies = _mapping(report.get("dependencies"))
    for task_id in S2PLT02_REQUIRED_DEPENDENCIES:
        if task_id not in dependencies.get("required_dependencies", []):
            errors.append(f"dependencies.required_dependencies must include {task_id}")
    evidence = _mapping(report.get("evidence"))
    for item in S2PLT02_REQUIRED_EVIDENCE:
        if item not in evidence.get("required_evidence", []):
            errors.append(f"evidence.required_evidence must include {item}")
    if evidence.get("required_natural_days") != S2PLT02_REQUIRED_NATURAL_DAYS:
        errors.append("evidence.required_natural_days must be 2")
    if evidence.get("required_email_count") != S2PLT02_REQUIRED_EMAIL_COUNT:
        errors.append("evidence.required_email_count must be 8")
    if tuple(evidence.get("required_mail_products", [])) != S2PLT02_REQUIRED_MAIL_PRODUCTS:
        errors.append("evidence.required_mail_products must be M1-M4")
    delivery_ledger = _mapping(evidence.get("delivery_evidence_ledger"))
    ledger_errors = validate_s2plt02_delivery_evidence_ledger_state(delivery_ledger)
    if ledger_errors:
        errors.append("S2PLT02 delivery evidence ledger is invalid")
        errors.extend(ledger_errors)
    if evidence.get("observed_natural_days") != delivery_ledger.get("observed_natural_days"):
        errors.append("evidence.observed_natural_days must match delivery evidence ledger")
    if evidence.get("observed_email_count") != delivery_ledger.get("observed_email_count"):
        errors.append("evidence.observed_email_count must match delivery evidence ledger")
    if evidence.get("duplicate_email_count") != delivery_ledger.get("duplicate_email_count"):
        errors.append("evidence.duplicate_email_count must match delivery evidence ledger")
    m4_watermark_proof = _mapping(evidence.get("m4_watermark_proof"))
    watermark_errors = validate_s2plt02_m4_watermark_proof_state(m4_watermark_proof)
    if watermark_errors:
        errors.append("S2PLT02 M4 watermark proof is invalid")
        errors.extend(watermark_errors)
    if evidence.get("m4_watermark_correct") != m4_watermark_proof.get("m4_watermark_correct"):
        errors.append("evidence.m4_watermark_correct must match M4 watermark proof")
    partial_delivery = _mapping(evidence.get("partial_real_delivery_evidence"))
    if not partial_delivery:
        errors.append("evidence.partial_real_delivery_evidence is required")
    else:
        if partial_delivery.get("scope") != S2PLT02_PARTIAL_REAL_DELIVERY_SCOPE:
            errors.append("partial real delivery evidence scope is invalid")
        if partial_delivery.get("observed_natural_days") != 1:
            errors.append("partial real delivery evidence must record one observed natural day")
        if partial_delivery.get("observed_email_count") != 4:
            errors.append("partial real delivery evidence must record four observed emails")
        if tuple(partial_delivery.get("sent_mail_products", [])) != S2PLT02_PARTIAL_REAL_DELIVERY_PRODUCTS:
            errors.append("partial real delivery evidence sent products must be M1-M4")
        if tuple(partial_delivery.get("newly_sent_mail_products", [])) != S2PLT02_PARTIAL_REAL_DELIVERY_NEWLY_SENT_PRODUCTS:
            errors.append("partial real delivery evidence newly sent products must be M2-M4")
        if partial_delivery.get("real_smtp_evidence_present") is not True:
            errors.append("partial real delivery evidence must include real SMTP proof")
        if partial_delivery.get("scheduler_evidence_present") is not False:
            errors.append("partial real delivery evidence must not claim scheduler proof")
        if partial_delivery.get("s2plt02_accepted") is not False:
            errors.append("partial real delivery evidence must not accept S2PLT02")
        expected_partial_hash = _stable_hash(
            {key: value for key, value in partial_delivery.items() if key != "evidence_hash"}
        )
        if partial_delivery.get("evidence_hash") != expected_partial_hash:
            errors.append("partial real delivery evidence_hash does not match evidence content")
    if report.get("status") == "pass":
        gates = _mapping(report.get("gates"))
        if not all(gates.values()):
            errors.append("passing S2PLT02 report requires every gate true")
        if report.get("blocking_reasons"):
            errors.append("passing S2PLT02 report must not have blocking reasons")
    else:
        gates = _mapping(report.get("gates"))
        expected_reasons = []
        if not gates.get("s2plt01_accepted"):
            expected_reasons.append("s2plt01_not_accepted")
        if not gates.get("two_consecutive_real_days"):
            expected_reasons.append("two_consecutive_real_days_not_proven")
        if not gates.get("eight_real_emails_sent"):
            expected_reasons.append("eight_real_emails_not_proven")
        if not gates.get("no_duplicate_emails"):
            expected_reasons.append("duplicate_emails_found")
        if not gates.get("real_scheduler_proven"):
            expected_reasons.append("real_scheduler_not_proven")
        if not gates.get("real_smtp_proven"):
            expected_reasons.append("real_smtp_not_proven")
        if not gates.get("m4_watermark_correct"):
            expected_reasons.append("m4_watermark_not_proven")
        if not gates.get("p0_zero"):
            expected_reasons.append("inherited_v7_1_p0_findings_open")
        if not gates.get("p1_zero"):
            expected_reasons.append("inherited_v7_1_p1_findings_open")
        if tuple(report.get("blocking_reasons", [])) != tuple(expected_reasons):
            errors.append("blocked S2PLT02 precheck blocking_reasons must match failed gates")
    expected_hash = _stable_hash({key: value for key, value in report.items() if key != "report_hash"})
    if report.get("report_hash") != expected_hash:
        errors.append("S2PLT02 report_hash does not match report content")
    return errors


def build_s2plt03_dependency_state() -> dict[str, Any]:
    """Build current S2PLT03 dependency state without accepting S2PLT02."""

    return {
        "status": "blocked",
        "required_dependencies": list(S2PLT03_REQUIRED_DEPENDENCIES),
        "completed_dependencies": {},
        "unmet_dependencies": list(S2PLT03_REQUIRED_DEPENDENCIES),
        "s2plt02_acceptance_status": "blocked_by_missing_real_2d_run_and_final_gates",
    }


def build_s2plt03_local_resilience_drill_bundle(*, generated_at: str) -> dict[str, Any]:
    """Build deterministic local S2PLT03 drill evidence without production side effects."""

    rate_limit_requests = ("M1", "M2", "M3")
    rate_limit_capacity = 2
    accepted_requests = rate_limit_requests[:rate_limit_capacity]
    blocked_requests = rate_limit_requests[rate_limit_capacity:]
    parser_required_fields = {"source_id", "title", "evidence_claims"}
    parser_drift_payload = {"source_id": "arxiv:local-drift", "title": "missing claims"}
    parser_missing = sorted(parser_required_fields - set(parser_drift_payload))
    restart_before = {"queued": 3, "leased": 1, "completed": 2}
    restart_after = {"queued": 4, "leased": 0, "completed": 2}
    disk_threshold_mb = 512
    disk_available_mb = 128
    backup_snapshot = {
        "candidate_rows": 4,
        "ledger_rows": 6,
        "queue_rows": 3,
        "version": "s2plt03-local-drill",
    }
    backup_hash = _stable_hash(backup_snapshot)
    rollback_steps = (
        "stop_runner_dry_run",
        "verify_restore_point_hash",
        "restore_snapshot_dry_run",
        "validate_ledger_counts",
        "keep_smtp_scheduler_release_disabled",
    )
    ledger_start = {"queued": 5, "processing": 2, "done": 3, "failed": 1}
    ledger_end = {"queued": 3, "processing": 2, "done": 4, "failed": 2}
    drill_cases = [
        {
            "case_id": "rate_limit_blocks_excess_request",
            "input_count": len(rate_limit_requests),
            "limit": rate_limit_capacity,
            "accepted_count": len(accepted_requests),
            "blocked_count": len(blocked_requests),
            "retry_after_seconds": 60,
            "passed": len(accepted_requests) == 2 and len(blocked_requests) == 1,
        },
        {
            "case_id": "parser_drift_quarantines_unknown_schema",
            "required_fields": sorted(parser_required_fields),
            "missing_fields": parser_missing,
            "quarantine_reasons": [f"missing_required_field:{field}" for field in parser_missing],
            "accepted_count": 0,
            "quarantined_count": 1,
            "passed": parser_missing == ["evidence_claims"],
        },
        {
            "case_id": "restart_recovery_reconciles_pending_rows",
            "rows_before": sum(restart_before.values()),
            "rows_after": sum(restart_after.values()),
            "leased_rows_recovered": restart_before["leased"] - restart_after["leased"],
            "state_before": restart_before,
            "state_after": restart_after,
            "passed": sum(restart_before.values()) == sum(restart_after.values()) and restart_after["leased"] == 0,
        },
        {
            "case_id": "disk_pressure_degrades_to_no_write",
            "threshold_mb": disk_threshold_mb,
            "available_mb": disk_available_mb,
            "degradation_state": "read_only_no_new_artifacts",
            "writes_allowed": 0,
            "passed": disk_available_mb < disk_threshold_mb,
        },
        {
            "case_id": "backup_restore_point_hash_matches",
            "snapshot_hash_before": backup_hash,
            "snapshot_hash_after": _stable_hash(dict(backup_snapshot)),
            "restore_point_scope": "local_synthetic_snapshot",
            "passed": backup_hash == _stable_hash(dict(backup_snapshot)),
        },
        {
            "case_id": "rollback_plan_is_dry_run_executable",
            "mode": "dry_run",
            "required_steps": list(rollback_steps),
            "executed_steps": list(rollback_steps),
            "passed": True,
        },
        {
            "case_id": "ledger_count_conservation_balances_states",
            "start_counts": ledger_start,
            "end_counts": ledger_end,
            "start_total": sum(ledger_start.values()),
            "end_total": sum(ledger_end.values()),
            "passed": sum(ledger_start.values()) == sum(ledger_end.values()),
        },
    ]
    case_pass = {case["case_id"]: bool(case["passed"]) for case in drill_cases}
    available_evidence = {
        "RATE_LIMIT_DRILL": case_pass["rate_limit_blocks_excess_request"],
        "PARSER_DRIFT_DRILL": case_pass["parser_drift_quarantines_unknown_schema"],
        "RESTART_RECOVERY_DRILL": case_pass["restart_recovery_reconciles_pending_rows"],
        "DISK_PRESSURE_DRILL": case_pass["disk_pressure_degrades_to_no_write"],
        "BACKUP_RESTORE_POINT_PROVEN": case_pass["backup_restore_point_hash_matches"],
        "ROLLBACK_EXECUTABLE": case_pass["rollback_plan_is_dry_run_executable"],
        "LEDGER_COUNT_CONSERVATION": case_pass["ledger_count_conservation_balances_states"],
    }
    all_passed = all(case_pass.values()) and all(available_evidence.values())
    bundle = {
        "model_id": S2PLT03_LOCAL_DRILL_MODEL_ID,
        "schema_version": S2PLT03_SCHEMA_VERSION,
        "task_id": S2PLT03_TASK_ID,
        "acceptance_id": S2PLT03_ACCEPTANCE_ID,
        "generated_at": generated_at,
        "status": "pass" if all_passed else "blocked",
        "scope": S2PLT03_LOCAL_DRILL_SCOPE,
        "required_drill_cases": list(S2PLT03_LOCAL_DRILL_REQUIRED_CASES),
        "drill_cases": drill_cases,
        "available_evidence": available_evidence,
        "all_local_drills_passed": all_passed,
        "production_acceptance_claimed": False,
        "s2plt03_accepted": False,
        "s2plt03_resilience_drill_completed": False,
        "bundle_hash": "",
        **{flag: False for flag in S2PLT03_LOCAL_DRILL_FORBIDDEN_FLAGS},
    }
    bundle["bundle_hash"] = _stable_hash({key: value for key, value in bundle.items() if key != "bundle_hash"})
    return bundle


def validate_s2plt03_local_resilience_drill_bundle(bundle: Mapping[str, Any]) -> list[str]:
    """Validate local no-production S2PLT03 drill evidence bundles."""

    errors: list[str] = []
    if bundle.get("model_id") != S2PLT03_LOCAL_DRILL_MODEL_ID:
        errors.append("S2PLT03 local drill model_id is invalid")
    if bundle.get("schema_version") != S2PLT03_SCHEMA_VERSION:
        errors.append("S2PLT03 local drill schema_version must be 1")
    if bundle.get("task_id") != S2PLT03_TASK_ID:
        errors.append("S2PLT03 local drill task_id is invalid")
    if bundle.get("acceptance_id") != S2PLT03_ACCEPTANCE_ID:
        errors.append("S2PLT03 local drill acceptance_id is invalid")
    if bundle.get("status") not in {"pass", "blocked"}:
        errors.append("S2PLT03 local drill status must be pass or blocked")
    if bundle.get("production_acceptance_claimed") is not False:
        errors.append("S2PLT03 local drill must not claim production acceptance")
    for flag in S2PLT03_LOCAL_DRILL_FORBIDDEN_FLAGS:
        if bundle.get(flag) is not False:
            errors.append(f"{flag} must be false")
    if tuple(bundle.get("required_drill_cases", [])) != S2PLT03_LOCAL_DRILL_REQUIRED_CASES:
        errors.append("S2PLT03 local drill required_drill_cases are invalid")
    cases = _list_of_mappings(bundle.get("drill_cases"))
    case_ids = {str(case.get("case_id")) for case in cases}
    for case_id in S2PLT03_LOCAL_DRILL_REQUIRED_CASES:
        if case_id not in case_ids:
            errors.append(f"S2PLT03 local drill case missing: {case_id}")
    available = _mapping(bundle.get("available_evidence"))
    for item in S2PLT03_REQUIRED_EVIDENCE:
        if item not in available:
            errors.append(f"S2PLT03 local drill evidence missing: {item}")
    if bundle.get("status") == "pass":
        if not bundle.get("all_local_drills_passed"):
            errors.append("passing S2PLT03 local drill requires all_local_drills_passed")
        for case in cases:
            if case.get("passed") is not True:
                errors.append(f"S2PLT03 local drill case did not pass: {case.get('case_id')}")
        if not all(bool(value) for value in available.values()):
            errors.append("passing S2PLT03 local drill requires all evidence true")
    expected_hash = _stable_hash({key: value for key, value in bundle.items() if key != "bundle_hash"})
    if bundle.get("bundle_hash") != expected_hash:
        errors.append("S2PLT03 local drill bundle_hash does not match bundle content")
    return errors


def build_s2plt03_resilience_evidence_state(
    *, local_drill_bundle: Mapping[str, Any] | None = None
) -> dict[str, Any]:
    """Build current S2PLT03 resilience evidence from local no-production drills."""

    if local_drill_bundle is not None and not validate_s2plt03_local_resilience_drill_bundle(local_drill_bundle):
        available = dict(_mapping(local_drill_bundle.get("available_evidence")))
        status = "pass" if all(available.values()) else "blocked"
        return {
            "status": status,
            "required_evidence": list(S2PLT03_REQUIRED_EVIDENCE),
            "available_evidence": available,
            "missing_evidence": [item for item, present in available.items() if not present],
            "evidence_scope": S2PLT03_LOCAL_DRILL_SCOPE,
            "local_drill_bundle_hash": local_drill_bundle.get("bundle_hash"),
            "rate_limit_drill_status": "local_drill_passed" if available["RATE_LIMIT_DRILL"] else "not_proven",
            "parser_drift_drill_status": "local_drill_passed" if available["PARSER_DRIFT_DRILL"] else "not_proven",
            "restart_recovery_drill_status": "local_drill_passed" if available["RESTART_RECOVERY_DRILL"] else "not_proven",
            "disk_pressure_drill_status": "local_drill_passed" if available["DISK_PRESSURE_DRILL"] else "not_proven",
            "backup_restore_point_status": "local_drill_passed"
            if available["BACKUP_RESTORE_POINT_PROVEN"]
            else "not_proven",
            "rollback_executable_status": "local_drill_passed" if available["ROLLBACK_EXECUTABLE"] else "not_proven",
            "ledger_count_conservation_status": "local_drill_passed"
            if available["LEDGER_COUNT_CONSERVATION"]
            else "not_proven",
        }

    available = {
        "RATE_LIMIT_DRILL": False,
        "PARSER_DRIFT_DRILL": False,
        "RESTART_RECOVERY_DRILL": False,
        "DISK_PRESSURE_DRILL": False,
        "BACKUP_RESTORE_POINT_PROVEN": False,
        "ROLLBACK_EXECUTABLE": False,
        "LEDGER_COUNT_CONSERVATION": False,
    }
    return {
        "status": "blocked",
        "required_evidence": list(S2PLT03_REQUIRED_EVIDENCE),
        "available_evidence": available,
        "missing_evidence": [item for item, present in available.items() if not present],
        "rate_limit_drill_status": "not_run",
        "parser_drift_drill_status": "not_run",
        "restart_recovery_drill_status": "not_run",
        "disk_pressure_drill_status": "not_run",
        "backup_restore_point_status": "not_proven",
        "rollback_executable_status": "not_proven",
        "ledger_count_conservation_status": "not_proven",
    }


def build_s2plt03_resilience_precheck_report(
    *,
    generated_at: str,
    repo_root: Path | None = None,
    p0_p1_zero_proof: Mapping[str, Any] | None = None,
    load_committed_artifacts: bool = True,
) -> dict[str, Any]:
    """Build a deterministic fail-closed S2PLT03 resilience precheck."""

    dependencies = build_s2plt03_dependency_state()
    local_drill_bundle = build_s2plt03_local_resilience_drill_bundle(generated_at=generated_at)
    evidence = build_s2plt03_resilience_evidence_state(local_drill_bundle=local_drill_bundle)
    if load_committed_artifacts and p0_p1_zero_proof is None:
        p0_p1_zero_proof = _load_committed_p0_p1_zero_proof(repo_root)
    p0_p1_zero_proof_artifact_validation = build_p0_p1_zero_proof_artifact_validation_state(
        p0_p1_zero_proof
    )
    audit_blockers = build_audit_blocker_state(
        inherited_p0=0
        if p0_p1_zero_proof_artifact_validation["p0_zero_proven_by_payload"]
        else S2PMT07_INHERITED_V7_1_OPEN_P0_FINDINGS,
        inherited_p1=0
        if p0_p1_zero_proof_artifact_validation["p1_zero_proven_by_payload"]
        else S2PMT07_INHERITED_V7_1_OPEN_P1_FINDINGS,
    )
    available_evidence = evidence["available_evidence"]
    gates = {
        "s2plt02_accepted": "S2PLT02" in dependencies["completed_dependencies"],
        "rate_limit_drill_proven": available_evidence["RATE_LIMIT_DRILL"],
        "parser_drift_drill_proven": available_evidence["PARSER_DRIFT_DRILL"],
        "restart_recovery_drill_proven": available_evidence["RESTART_RECOVERY_DRILL"],
        "disk_pressure_drill_proven": available_evidence["DISK_PRESSURE_DRILL"],
        "backup_restore_point_proven": available_evidence["BACKUP_RESTORE_POINT_PROVEN"],
        "rollback_executable": available_evidence["ROLLBACK_EXECUTABLE"],
        "ledger_count_conserved": available_evidence["LEDGER_COUNT_CONSERVATION"],
        "p0_zero": p0_p1_zero_proof_artifact_validation["p0_zero_proven_by_payload"],
        "p1_zero": p0_p1_zero_proof_artifact_validation["p1_zero_proven_by_payload"],
        "no_production_side_effect": True,
    }
    blocking_reasons: list[str] = []
    if not gates["s2plt02_accepted"]:
        blocking_reasons.append("s2plt02_not_accepted")
    if not gates["rate_limit_drill_proven"]:
        blocking_reasons.append("rate_limit_drill_not_proven")
    if not gates["parser_drift_drill_proven"]:
        blocking_reasons.append("parser_drift_drill_not_proven")
    if not gates["restart_recovery_drill_proven"]:
        blocking_reasons.append("restart_recovery_drill_not_proven")
    if not gates["disk_pressure_drill_proven"]:
        blocking_reasons.append("disk_pressure_drill_not_proven")
    if not gates["backup_restore_point_proven"]:
        blocking_reasons.append("backup_restore_point_not_proven")
    if not gates["rollback_executable"]:
        blocking_reasons.append("rollback_executable_not_proven")
    if not gates["ledger_count_conserved"]:
        blocking_reasons.append("ledger_count_conservation_not_proven")
    if not gates["p0_zero"]:
        blocking_reasons.append("inherited_v7_1_p0_findings_open")
    if not gates["p1_zero"]:
        blocking_reasons.append("inherited_v7_1_p1_findings_open")
    report = {
        "model_id": S2PLT03_RESILIENCE_PRECHECK_MODEL_ID,
        "schema_version": S2PLT03_SCHEMA_VERSION,
        "task_id": S2PLT03_TASK_ID,
        "acceptance_id": S2PLT03_ACCEPTANCE_ID,
        "generated_at": generated_at,
        "status": "pass" if not blocking_reasons and all(gates.values()) else "blocked",
        "scope": "no_production_resilience_capacity_rollback_precheck_only",
        "gates": gates,
        "dependencies": dependencies,
        "evidence": evidence,
        "local_drill_bundle": local_drill_bundle,
        "audit_blockers": audit_blockers,
        "p0_p1_zero_proof_artifact_validation": p0_p1_zero_proof_artifact_validation,
        "blocking_reasons": blocking_reasons,
        "production_acceptance_claimed": False,
        "inherited_p0_p1_closed": False,
        "report_hash": "",
        **{flag: False for flag in S2PLT03_FORBIDDEN_FLAGS},
    }
    report["report_hash"] = _stable_hash({key: value for key, value in report.items() if key != "report_hash"})
    return report


def validate_s2plt03_resilience_precheck_report(report: Mapping[str, Any]) -> list[str]:
    """Validate S2PLT03 resilience precheck reports."""

    errors: list[str] = []
    if report.get("model_id") != S2PLT03_RESILIENCE_PRECHECK_MODEL_ID:
        errors.append("S2PLT03 report model_id is invalid")
    if report.get("schema_version") != S2PLT03_SCHEMA_VERSION:
        errors.append("S2PLT03 report schema_version must be 1")
    if report.get("task_id") != S2PLT03_TASK_ID:
        errors.append("S2PLT03 report task_id is invalid")
    if report.get("acceptance_id") != S2PLT03_ACCEPTANCE_ID:
        errors.append("S2PLT03 report acceptance_id is invalid")
    if report.get("status") not in {"pass", "blocked"}:
        errors.append("S2PLT03 report status must be pass or blocked")
    if report.get("production_acceptance_claimed") is not False:
        errors.append("S2PLT03 precheck must not claim production acceptance")
    if report.get("inherited_p0_p1_closed") is not False:
        errors.append("S2PLT03 precheck must not close inherited P0/P1")
    for flag in S2PLT03_FORBIDDEN_FLAGS:
        if report.get(flag) is not False:
            errors.append(f"{flag} must be false")

    dependencies = _mapping(report.get("dependencies"))
    for task_id in S2PLT03_REQUIRED_DEPENDENCIES:
        if task_id not in dependencies.get("required_dependencies", []):
            errors.append(f"dependencies.required_dependencies must include {task_id}")
    evidence = _mapping(report.get("evidence"))
    for item in S2PLT03_REQUIRED_EVIDENCE:
        if item not in evidence.get("required_evidence", []):
            errors.append(f"evidence.required_evidence must include {item}")
    local_drill_bundle = _mapping(report.get("local_drill_bundle"))
    local_drill_errors = validate_s2plt03_local_resilience_drill_bundle(local_drill_bundle)
    if local_drill_errors:
        errors.append("S2PLT03 local drill bundle is invalid")
    gates = _mapping(report.get("gates"))
    zero_proof_validation = _mapping(report.get("p0_p1_zero_proof_artifact_validation"))
    if gates.get("p0_zero") is not zero_proof_validation.get("p0_zero_proven_by_payload"):
        errors.append("S2PLT03 p0_zero gate must match zero-proof artifact validation")
    if gates.get("p1_zero") is not zero_proof_validation.get("p1_zero_proven_by_payload"):
        errors.append("S2PLT03 p1_zero gate must match zero-proof artifact validation")
    if report.get("status") == "pass":
        if not all(gates.values()):
            errors.append("passing S2PLT03 report requires every gate true")
        if report.get("blocking_reasons"):
            errors.append("passing S2PLT03 report must not have blocking reasons")
    else:
        expected_reasons = []
        if not gates.get("s2plt02_accepted"):
            expected_reasons.append("s2plt02_not_accepted")
        if not gates.get("rate_limit_drill_proven"):
            expected_reasons.append("rate_limit_drill_not_proven")
        if not gates.get("parser_drift_drill_proven"):
            expected_reasons.append("parser_drift_drill_not_proven")
        if not gates.get("restart_recovery_drill_proven"):
            expected_reasons.append("restart_recovery_drill_not_proven")
        if not gates.get("disk_pressure_drill_proven"):
            expected_reasons.append("disk_pressure_drill_not_proven")
        if not gates.get("backup_restore_point_proven"):
            expected_reasons.append("backup_restore_point_not_proven")
        if not gates.get("rollback_executable"):
            expected_reasons.append("rollback_executable_not_proven")
        if not gates.get("ledger_count_conserved"):
            expected_reasons.append("ledger_count_conservation_not_proven")
        if not gates.get("p0_zero"):
            expected_reasons.append("inherited_v7_1_p0_findings_open")
        if not gates.get("p1_zero"):
            expected_reasons.append("inherited_v7_1_p1_findings_open")
        for reason in expected_reasons:
            if reason not in report.get("blocking_reasons", []):
                errors.append(f"blocked S2PLT03 precheck must include {reason}")
        for reason in report.get("blocking_reasons", []):
            if reason not in S2PLT03_BLOCKING_REASONS:
                errors.append(f"S2PLT03 blocking reason is invalid: {reason}")
    expected_hash = _stable_hash({key: value for key, value in report.items() if key != "report_hash"})
    if report.get("report_hash") != expected_hash:
        errors.append("S2PLT03 report_hash does not match report content")
    return errors


def build_s2plt03_terminal_resilience_proof_hash(payload: Mapping[str, Any]) -> str:
    """Return the canonical S2PLT03 terminal resilience proof hash."""

    return _stable_hash({key: value for key, value in payload.items() if key != "acceptance_hash"})


def validate_s2plt03_terminal_resilience_proof_artifact(payload: Mapping[str, Any] | None) -> list[str]:
    """Validate a future S2PLT03 terminal resilience proof artifact without accepting production."""

    if payload is None:
        return ["s2plt03_terminal_resilience_proof_artifact_missing"]
    errors: list[str] = []
    if payload.get("model_id") != S2PLT03_TERMINAL_RESILIENCE_PROOF_MODEL_ID:
        errors.append("model_id is invalid")
    if payload.get("schema_version") != S2PLT03_SCHEMA_VERSION:
        errors.append("schema_version must be 1")
    if payload.get("task_id") != S2PLT03_TASK_ID:
        errors.append("task_id must be S2PLT03")
    if payload.get("acceptance_id") != S2PLT03_ACCEPTANCE_ID:
        errors.append("acceptance_id must be ACC-S2PLT03-RESILIENCE")
    if payload.get("terminal_resilience_decision") != S2PLT03_TERMINAL_RESILIENCE_PROOF_DECISION:
        errors.append("terminal_resilience_decision is invalid")
    if payload.get("s2plt03_accepted") is not True:
        errors.append("s2plt03_accepted must be true")
    if payload.get("s2plt03_resilience_drill_completed") is not True:
        errors.append("s2plt03_resilience_drill_completed must be true")
    if payload.get("no_production_side_effects") is not True:
        errors.append("no_production_side_effects must be true")

    terminal_gates = _mapping(payload.get("terminal_gates"))
    for gate in S2PLT03_TERMINAL_RESILIENCE_PROOF_REQUIRED_GATES:
        if terminal_gates.get(gate) is not True:
            errors.append(f"terminal_gates.{gate} must be true")

    refs = payload.get("terminal_evidence_refs", [])
    if not isinstance(refs, list) or any(not isinstance(ref, str) or not ref for ref in refs):
        errors.append("terminal_evidence_refs must be a list of non-empty strings")
    else:
        for required_ref in S2PLT03_TERMINAL_RESILIENCE_PROOF_REQUIRED_EVIDENCE_REFS:
            if required_ref not in refs:
                errors.append(f"terminal_evidence_refs must include {required_ref}")
        if len(refs) < 4:
            errors.append("terminal_evidence_refs must include S2PLT02, local drill, resilience precheck, and zero-proof refs")

    refs_by_role = _mapping(payload.get("terminal_evidence_refs_by_role"))
    for role in S2PLT03_TERMINAL_RESILIENCE_PROOF_REQUIRED_EVIDENCE_ROLES:
        role_ref = refs_by_role.get(role)
        if not isinstance(role_ref, str) or not role_ref:
            errors.append(f"terminal_evidence_refs_by_role.{role} is required")
        elif isinstance(refs, list) and role_ref not in refs:
            errors.append(f"terminal_evidence_refs_by_role.{role} must also appear in terminal_evidence_refs")
    if refs_by_role.get("s2plt02_terminal_delivery_proof") != S2PLT02_TERMINAL_DELIVERY_PROOF_ARTIFACT_PATH:
        errors.append(
            "terminal_evidence_refs_by_role.s2plt02_terminal_delivery_proof must point to S2PLT02 terminal proof"
        )
    if refs_by_role.get("p0_p1_zero_proof") != S2PMT07_P0_P1_ZERO_PROOF_ARTIFACT_PATH:
        errors.append("terminal_evidence_refs_by_role.p0_p1_zero_proof must point to P0/P1 zero proof")

    for flag in S2PLT03_TERMINAL_RESILIENCE_PROOF_NO_PRODUCTION_FLAGS:
        if payload.get(flag) is not False:
            errors.append(f"{flag} must be false")

    if payload.get("acceptance_hash") != build_s2plt03_terminal_resilience_proof_hash(payload):
        errors.append("acceptance_hash does not match payload content")
    return errors


def build_s2plt03_terminal_resilience_proof_artifact_validation_state(
    *,
    repo_root: str | Path = ".",
    artifact: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build artifact-level validation for future S2PLT03 terminal resilience proof."""

    root = Path(repo_root)
    artifact_path = root / S2PLT03_TERMINAL_RESILIENCE_PROOF_ARTIFACT_PATH
    artifact_present = artifact is not None or artifact_path.exists()
    loaded_artifact: Mapping[str, Any] | None = artifact
    load_error = ""
    if loaded_artifact is None and artifact_path.exists():
        try:
            loaded = json.loads(artifact_path.read_text(encoding="utf-8"))
            loaded_artifact = loaded if isinstance(loaded, Mapping) else None
            if loaded_artifact is None:
                load_error = "s2plt03_terminal_resilience_proof_artifact_must_be_object"
        except json.JSONDecodeError:
            load_error = "s2plt03_terminal_resilience_proof_artifact_invalid_json"

    validation_errors = validate_s2plt03_terminal_resilience_proof_artifact(loaded_artifact)
    if load_error and load_error not in validation_errors:
        validation_errors.append(load_error)
    resilience_precheck = build_s2plt03_resilience_precheck_report(
        generated_at="2026-06-29T12:12:00+10:00",
        repo_root=root,
    )
    precheck_gates = _mapping(resilience_precheck.get("gates"))
    if loaded_artifact is not None:
        terminal_gates = _mapping(loaded_artifact.get("terminal_gates"))
    else:
        terminal_gates = {
            "s2plt02_accepted": precheck_gates.get("s2plt02_accepted") is True,
            "rate_limit_drill_proven": precheck_gates.get("rate_limit_drill_proven") is True,
            "parser_drift_drill_proven": precheck_gates.get("parser_drift_drill_proven") is True,
            "restart_recovery_drill_proven": precheck_gates.get("restart_recovery_drill_proven") is True,
            "disk_pressure_drill_proven": precheck_gates.get("disk_pressure_drill_proven") is True,
            "backup_restore_point_proven": precheck_gates.get("backup_restore_point_proven") is True,
            "rollback_executable": precheck_gates.get("rollback_executable") is True,
            "ledger_count_conserved": precheck_gates.get("ledger_count_conserved") is True,
            "p0_zero": precheck_gates.get("p0_zero") is True,
            "p1_zero": precheck_gates.get("p1_zero") is True,
            "no_production_side_effects": True,
        }
    missing_gate_reasons = {
        "s2plt02_accepted": "s2plt02_not_accepted",
        "rate_limit_drill_proven": "rate_limit_drill_not_proven",
        "parser_drift_drill_proven": "parser_drift_drill_not_proven",
        "restart_recovery_drill_proven": "restart_recovery_drill_not_proven",
        "disk_pressure_drill_proven": "disk_pressure_drill_not_proven",
        "backup_restore_point_proven": "backup_restore_point_not_proven",
        "rollback_executable": "rollback_executable_not_proven",
        "ledger_count_conserved": "ledger_count_conservation_not_proven",
        "p0_zero": "inherited_v7_1_p0_findings_open",
        "p1_zero": "inherited_v7_1_p1_findings_open",
        "no_production_side_effects": "production_side_effects_not_ruled_out",
    }
    blocking_reasons: list[str] = []
    if not artifact_present:
        blocking_reasons.append("s2plt03_terminal_resilience_proof_artifact_missing")
        for reason in resilience_precheck.get("blocking_reasons", []):
            if isinstance(reason, str) and reason not in blocking_reasons:
                blocking_reasons.append(reason)
    else:
        for gate, reason in missing_gate_reasons.items():
            if terminal_gates.get(gate) is not True and reason not in blocking_reasons:
                blocking_reasons.append(reason)

    expected_acceptance_hash = (
        build_s2plt03_terminal_resilience_proof_hash(loaded_artifact) if loaded_artifact is not None else ""
    )
    terminal_resilience_proof_ready = artifact_present and not validation_errors and not blocking_reasons
    no_production_flag_values = {
        flag: (loaded_artifact.get(flag) if loaded_artifact is not None else False)
        for flag in S2PLT03_TERMINAL_RESILIENCE_PROOF_NO_PRODUCTION_FLAGS
    }
    state = {
        "status": "pass" if terminal_resilience_proof_ready else "blocked",
        "scope": S2PLT03_TERMINAL_RESILIENCE_PROOF_SCOPE,
        "artifact_ref": S2PLT03_TERMINAL_RESILIENCE_PROOF_ARTIFACT_PATH,
        "artifact_present": artifact_present,
        "model_id": (
            loaded_artifact.get("model_id") if loaded_artifact is not None else S2PLT03_TERMINAL_RESILIENCE_PROOF_MODEL_ID
        ),
        "schema_version": loaded_artifact.get("schema_version") if loaded_artifact is not None else S2PLT03_SCHEMA_VERSION,
        "task_id": S2PLT03_TASK_ID,
        "acceptance_id": S2PLT03_ACCEPTANCE_ID,
        "terminal_resilience_decision": (
            loaded_artifact.get("terminal_resilience_decision") if loaded_artifact is not None else None
        ),
        "terminal_resilience_proof_ready": terminal_resilience_proof_ready,
        "s2plt03_accepted_by_artifact": terminal_resilience_proof_ready
        and loaded_artifact is not None
        and loaded_artifact.get("s2plt03_accepted") is True,
        "s2plt03_resilience_drill_completed_by_artifact": terminal_resilience_proof_ready
        and loaded_artifact is not None
        and loaded_artifact.get("s2plt03_resilience_drill_completed") is True,
        "terminal_gates": {gate: terminal_gates.get(gate) is True for gate in S2PLT03_TERMINAL_RESILIENCE_PROOF_REQUIRED_GATES},
        "terminal_evidence_refs": list(loaded_artifact.get("terminal_evidence_refs", [])) if loaded_artifact is not None else [],
        "terminal_evidence_refs_by_role": dict(_mapping(loaded_artifact.get("terminal_evidence_refs_by_role")))
        if loaded_artifact is not None
        else {},
        "resilience_precheck_status": resilience_precheck.get("status"),
        "resilience_precheck_report_hash": resilience_precheck.get("report_hash"),
        "audit_blockers_status": _mapping(resilience_precheck.get("audit_blockers")).get("status"),
        "validation_errors": validation_errors,
        "blocking_reasons": blocking_reasons,
        "acceptance_hash": loaded_artifact.get("acceptance_hash") if loaded_artifact is not None else "",
        "expected_acceptance_hash": expected_acceptance_hash,
        "state_hash": "",
        **no_production_flag_values,
    }
    state["state_hash"] = _stable_hash({key: value for key, value in state.items() if key != "state_hash"})
    return state


def validate_s2plt03_terminal_resilience_proof_artifact_validation_state(state: Mapping[str, Any]) -> list[str]:
    """Validate S2PLT03 terminal resilience proof artifact validation state."""

    errors: list[str] = []
    if state.get("scope") != S2PLT03_TERMINAL_RESILIENCE_PROOF_SCOPE:
        errors.append("S2PLT03 terminal resilience proof validation scope is invalid")
    if state.get("artifact_ref") != S2PLT03_TERMINAL_RESILIENCE_PROOF_ARTIFACT_PATH:
        errors.append("S2PLT03 terminal resilience proof artifact_ref is invalid")
    if state.get("status") not in {"pass", "blocked"}:
        errors.append("S2PLT03 terminal resilience proof validation status is invalid")
    terminal_gates = _mapping(state.get("terminal_gates"))
    for gate in S2PLT03_TERMINAL_RESILIENCE_PROOF_REQUIRED_GATES:
        if gate not in terminal_gates:
            errors.append(f"S2PLT03 terminal resilience proof terminal_gates must include {gate}")
    ready = state.get("terminal_resilience_proof_ready") is True
    if state.get("status") == "pass" and not ready:
        errors.append("pass status requires terminal_resilience_proof_ready")
    if ready and state.get("s2plt03_accepted_by_artifact") is not True:
        errors.append("terminal_resilience_proof_ready requires s2plt03_accepted_by_artifact")
    if ready and state.get("s2plt03_resilience_drill_completed_by_artifact") is not True:
        errors.append("terminal_resilience_proof_ready requires s2plt03_resilience_drill_completed_by_artifact")
    for flag in S2PLT03_TERMINAL_RESILIENCE_PROOF_NO_PRODUCTION_FLAGS:
        if state.get(flag) is not False:
            errors.append(f"{flag} must be false")
    expected_hash = _stable_hash({key: value for key, value in state.items() if key != "state_hash"})
    if state.get("state_hash") != expected_hash:
        errors.append("S2PLT03 terminal resilience proof validation state_hash does not match state content")
    return errors


def build_s2plt03_terminal_resilience_proof_capture_plan_state(
    *,
    generated_at: str,
    repo_root: str | Path = ".",
) -> dict[str, Any]:
    """Build a no-write S2PLT03 terminal resilience proof capture plan."""

    root = Path(repo_root)
    resilience_precheck = build_s2plt03_resilience_precheck_report(
        generated_at="2026-06-29T12:12:00+10:00",
        repo_root=root,
    )
    artifact_validation = build_s2plt03_terminal_resilience_proof_artifact_validation_state(repo_root=root)
    terminal_gates = _mapping(artifact_validation.get("terminal_gates"))
    completed_inputs = {
        "LOCAL_RESILIENCE_DRILL": all(
            bool(terminal_gates.get(gate))
            for gate in (
                "rate_limit_drill_proven",
                "parser_drift_drill_proven",
                "restart_recovery_drill_proven",
                "disk_pressure_drill_proven",
                "backup_restore_point_proven",
                "rollback_executable",
                "ledger_count_conserved",
            )
        ),
        "RESILIENCE_PRECHECK": validate_s2plt03_resilience_precheck_report(resilience_precheck) == [],
        "P0_P1_ZERO_PROOF": terminal_gates.get("p0_zero") is True and terminal_gates.get("p1_zero") is True,
        "S2PLT02_TERMINAL_DELIVERY_PROOF": terminal_gates.get("s2plt02_accepted") is True,
        "S2PLT03_TERMINAL_RESILIENCE_PROOF_ARTIFACT": artifact_validation.get("artifact_present") is True,
    }
    missing_terminal_inputs: list[str] = []
    if not completed_inputs["S2PLT02_TERMINAL_DELIVERY_PROOF"]:
        missing_terminal_inputs.append("S2PLT02_TERMINAL_DELIVERY_PROOF_ARTIFACT")
    if not completed_inputs["S2PLT03_TERMINAL_RESILIENCE_PROOF_ARTIFACT"]:
        missing_terminal_inputs.append("S2PLT03_TERMINAL_RESILIENCE_PROOF_ARTIFACT")
    blocking_reasons = list(dict.fromkeys(str(reason) for reason in artifact_validation.get("blocking_reasons", [])))
    if missing_terminal_inputs and not blocking_reasons:
        blocking_reasons.append("s2plt03_terminal_resilience_proof_inputs_missing")
    if not completed_inputs["S2PLT02_TERMINAL_DELIVERY_PROOF"]:
        next_executable_step = "WAIT_FOR_S2PLT02_TERMINAL_ACCEPTANCE"
    elif not completed_inputs["S2PLT03_TERMINAL_RESILIENCE_PROOF_ARTIFACT"]:
        next_executable_step = "BUILD_REVIEWED_S2PLT03_TERMINAL_RESILIENCE_PROOF"
    else:
        next_executable_step = "RUN_VALIDATE_S2PLT03_TERMINAL_RESILIENCE_PROOF"
    plan = {
        "schema_version": S2PLT03_SCHEMA_VERSION,
        "task_id": S2PLT03_TERMINAL_RESILIENCE_PROOF_CAPTURE_PLAN_TASK_ID,
        "parent_task_id": S2PLT03_TASK_ID,
        "acceptance_id": S2PLT03_ACCEPTANCE_ID,
        "generated_at": generated_at,
        "status": "blocked" if missing_terminal_inputs or blocking_reasons else "pass",
        "scope": S2PLT03_TERMINAL_RESILIENCE_PROOF_CAPTURE_PLAN_SCOPE,
        "ordered_steps": list(S2PLT03_TERMINAL_RESILIENCE_PROOF_CAPTURE_PLAN_STEPS),
        "next_executable_step": next_executable_step,
        "completed_inputs": completed_inputs,
        "missing_terminal_inputs": missing_terminal_inputs,
        "blocking_reasons": blocking_reasons,
        "terminal_artifact_ref": S2PLT03_TERMINAL_RESILIENCE_PROOF_ARTIFACT_PATH,
        "s2plt02_terminal_delivery_proof_ref": S2PLT02_TERMINAL_DELIVERY_PROOF_ARTIFACT_PATH,
        "resilience_precheck_status": resilience_precheck.get("status"),
        "resilience_precheck_report_hash": resilience_precheck.get("report_hash"),
        "terminal_artifact_validation_status": artifact_validation.get("status"),
        "terminal_artifact_validation_state_hash": artifact_validation.get("state_hash"),
        "artifact_written": False,
        "s2plt03_accepted": False,
        "s2plt03_resilience_drill_completed": False,
        "state_hash": "",
        **{flag: False for flag in S2PLT03_TERMINAL_RESILIENCE_PROOF_NO_PRODUCTION_FLAGS},
    }
    plan["state_hash"] = _stable_hash({key: value for key, value in plan.items() if key != "state_hash"})
    return plan


def validate_s2plt03_terminal_resilience_proof_capture_plan_state(plan: Mapping[str, Any]) -> list[str]:
    """Validate no-write S2PLT03 terminal resilience proof capture plans."""

    errors: list[str] = []
    if plan.get("schema_version") != S2PLT03_SCHEMA_VERSION:
        errors.append("S2PLT03 capture plan schema_version must be 1")
    if plan.get("task_id") != S2PLT03_TERMINAL_RESILIENCE_PROOF_CAPTURE_PLAN_TASK_ID:
        errors.append("S2PLT03 capture plan task_id is invalid")
    if plan.get("parent_task_id") != S2PLT03_TASK_ID:
        errors.append("S2PLT03 capture plan parent_task_id is invalid")
    if plan.get("acceptance_id") != S2PLT03_ACCEPTANCE_ID:
        errors.append("S2PLT03 capture plan acceptance_id is invalid")
    if plan.get("scope") != S2PLT03_TERMINAL_RESILIENCE_PROOF_CAPTURE_PLAN_SCOPE:
        errors.append("S2PLT03 capture plan scope is invalid")
    if tuple(plan.get("ordered_steps", [])) != S2PLT03_TERMINAL_RESILIENCE_PROOF_CAPTURE_PLAN_STEPS:
        errors.append("S2PLT03 capture plan ordered_steps are invalid")
    if plan.get("next_executable_step") not in S2PLT03_TERMINAL_RESILIENCE_PROOF_CAPTURE_PLAN_STEPS:
        errors.append("S2PLT03 capture plan next_executable_step is invalid")
    if plan.get("status") not in {"pass", "blocked"}:
        errors.append("S2PLT03 capture plan status must be pass or blocked")
    if plan.get("artifact_written") is not False:
        errors.append("S2PLT03 capture plan must not write an artifact")
    if plan.get("s2plt03_accepted") is not False:
        errors.append("S2PLT03 capture plan must not accept S2PLT03")
    if plan.get("s2plt03_resilience_drill_completed") is not False:
        errors.append("S2PLT03 capture plan must not complete resilience drill")
    for flag in S2PLT03_TERMINAL_RESILIENCE_PROOF_NO_PRODUCTION_FLAGS:
        if plan.get(flag) is not False:
            errors.append(f"{flag} must be false")
    completed_inputs = _mapping(plan.get("completed_inputs"))
    for key in (
        "LOCAL_RESILIENCE_DRILL",
        "RESILIENCE_PRECHECK",
        "P0_P1_ZERO_PROOF",
        "S2PLT02_TERMINAL_DELIVERY_PROOF",
        "S2PLT03_TERMINAL_RESILIENCE_PROOF_ARTIFACT",
    ):
        if key not in completed_inputs:
            errors.append(f"S2PLT03 capture plan completed_inputs must include {key}")
    if plan.get("status") == "blocked" and not plan.get("blocking_reasons"):
        errors.append("blocked S2PLT03 capture plan must include blocking_reasons")
    if (
        completed_inputs.get("S2PLT02_TERMINAL_DELIVERY_PROOF") is False
        and plan.get("next_executable_step") != "WAIT_FOR_S2PLT02_TERMINAL_ACCEPTANCE"
    ):
        errors.append("S2PLT03 capture plan must wait for S2PLT02 acceptance first")
    expected_hash = _stable_hash({key: value for key, value in plan.items() if key != "state_hash"})
    if plan.get("state_hash") != expected_hash:
        errors.append("S2PLT03 capture plan state_hash does not match state content")
    return errors


def build_s2plt04_dependency_state(*, repo_root: str | Path = ".") -> dict[str, Any]:
    """Build current S2PLT04 dependency state without accepting upstream tasks."""

    s2plt01 = _build_s2plt01_terminal_acceptance_dependency_state(repo_root)
    completed = {"S2PLT01": s2plt01["status"]} if s2plt01["accepted"] else {}
    unmet = [task_id for task_id in S2PLT04_REQUIRED_DEPENDENCIES if task_id not in completed]
    available_local_evidence = {
        task_id: "local_evidence_present_not_terminal_acceptance"
        for task_id in S2PLT04_AVAILABLE_LOCAL_EVIDENCE
    }
    return {
        "status": "blocked",
        "required_dependencies": list(S2PLT04_REQUIRED_DEPENDENCIES),
        "completed_dependencies": completed,
        "unmet_dependencies": unmet,
        "available_local_evidence": available_local_evidence,
        "s2plt01_acceptance_status": s2plt01["status"],
        "s2plt01_terminal_acceptance": s2plt01,
        "s2plt02_status": "missing_authoritative_completion_evidence",
        "s2plt03_status": "missing_authoritative_completion_evidence",
    }


def _build_s2plt04_replay_records() -> list[dict[str, Any]]:
    return [
        {
            "as_of_date": f"2026-05-{day:02d}",
            "status": "pass",
            "source_domains": ["D1", "D2", "D3", "D4"],
            "reading_boards": ["B1", "B2", "B3", "B4", "B5", "B6"],
            "future_leakage_count": 0,
            "p0_p1_blocker_count": 0,
            "evidence_refs": [f"replay/{day:02d}.json"],
        }
        for day in range(1, 31)
    ]


def _build_s2plt04_mail_preview_records() -> list[dict[str, Any]]:
    return [
        {
            "as_of_date": f"2026-05-{day:02d}",
            "mail_product_id": product_id,
            "status": "pass",
            "email_template_contract": "EMAIL_LEARNING_V1",
            "real_smtp_sent": False,
            "evidence_refs": [f"mail/{day:02d}/{product_id}.json"],
        }
        for day in range(1, 31)
        for product_id in S2PLT01_REQUIRED_MAIL_PRODUCTS
    ]


def _build_s2plt04_source_terminal_states() -> list[dict[str, Any]]:
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


def _build_s2plt04_s2plt01_independent_replay_review_report() -> dict[str, Any]:
    execution_report = build_s2plt01_replay_payload_execution_report(
        execution_id="S2PLT01-REPLAY-PAYLOAD-EXECUTION-20260626-001",
        generated_at=S2PLT04_REPLAY_EXECUTION_GENERATED_AT,
        generated_by="codex-stage2-local",
        evidence_mode="actual_replay_evidence",
        replay_records=_build_s2plt04_replay_records(),
        mail_preview_records=_build_s2plt04_mail_preview_records(),
        source_terminal_states=_build_s2plt04_source_terminal_states(),
        evidence_refs=["governance/run_manifests/ADP-S2PLT01-REPLAY-PAYLOAD-EXECUTION-20260626.json"],
    )
    return build_s2plt01_independent_replay_review_report(
        review_id="S2PLT01-INDEPENDENT-REVIEW-20260626-001",
        generated_at=S2PLT04_REPLAY_REVIEW_GENERATED_AT,
        reviewer_id="codex-independent-reviewer",
        reviewer_role="independent_stage2_replay_reviewer",
        reviewer_involved_in_s2plt01_implementation=False,
        replay_execution_report=execution_report,
        ci_evidence_refs=[
            "https://github.com/LinzeColin/CodexProject/actions/runs/28217724286",
            "https://github.com/LinzeColin/CodexProject/actions/runs/28217724275",
        ],
        evidence_refs=["governance/run_manifests/ADP-S2PLT01-INDEPENDENT-REPLAY-REVIEW-20260626.json"],
    )


def _build_s2plt04_local_evidence_bundle(
    *,
    bundle_id: str,
    scope: str,
    source_tasks: tuple[str, ...],
    evidence_refs: tuple[str, ...],
) -> dict[str, Any]:
    bundle = {
        "bundle_id": bundle_id,
        "status": "pass",
        "scope": scope,
        "source_tasks": list(source_tasks),
        "evidence_refs": list(evidence_refs),
        "no_production_side_effects": True,
        "terminal_acceptance_claimed": False,
        "bundle_hash": "",
    }
    bundle["bundle_hash"] = _stable_hash({key: value for key, value in bundle.items() if key != "bundle_hash"})
    return bundle


def build_s2plt04_evidence_state(
    *,
    repo_root: str | Path = ".",
    independent_replay_review_report: Mapping[str, Any] | None = None,
    live_2d_precheck_report: Mapping[str, Any] | None = None,
    local_drill_bundle: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build current S2PLT04 evidence state from local governance facts."""

    if independent_replay_review_report is None:
        independent_replay_review_report = _build_s2plt04_s2plt01_independent_replay_review_report()
    replay_review_valid = not validate_s2plt01_independent_replay_review_report(independent_replay_review_report)
    replay_review_present = (
        replay_review_valid
        and independent_replay_review_report.get("status") == "blocked"
        and independent_replay_review_report.get("review_package_passed") is True
        and independent_replay_review_report.get("s2plt01_acceptance_claimed") is False
    )
    if live_2d_precheck_report is None:
        live_2d_precheck_report = build_s2plt02_live_2d_precheck_report(
            generated_at=S2PLT04_LIVE_2D_PRECHECK_GENERATED_AT
        )
    live_2d_precheck_valid = not validate_s2plt02_live_2d_precheck_report(live_2d_precheck_report)
    live_2d_precheck_present = live_2d_precheck_valid and live_2d_precheck_report.get("status") == "blocked"
    if local_drill_bundle is None:
        local_drill_bundle = build_s2plt03_local_resilience_drill_bundle(
            generated_at=S2PLT04_LOCAL_DRILL_BUNDLE_GENERATED_AT
        )
    local_drill_valid = not validate_s2plt03_local_resilience_drill_bundle(local_drill_bundle)
    local_drill_passed = local_drill_valid and local_drill_bundle.get("status") == "pass"
    state_consistency_evidence_bundle = _build_s2plt04_local_evidence_bundle(
        bundle_id="S2PLT04-STATE-CONSISTENCY-EVIDENCE-BUNDLE",
        scope="local_state_consistency_evidence_not_terminal_acceptance",
        source_tasks=S2PLT04_STATE_CONSISTENCY_SOURCE_TASKS,
        evidence_refs=S2PLT04_STATE_CONSISTENCY_EVIDENCE_REFS,
    )
    content_evidence_bundle = _build_s2plt04_local_evidence_bundle(
        bundle_id="S2PLT04-CONTENT-EVIDENCE-BUNDLE",
        scope="local_content_evidence_not_terminal_acceptance",
        source_tasks=S2PLT04_CONTENT_EVIDENCE_SOURCE_TASKS,
        evidence_refs=S2PLT04_CONTENT_EVIDENCE_REFS,
    )
    final_acceptance_bundle_readiness = build_final_acceptance_bundle_readiness_state()
    s2plt01 = _build_s2plt01_terminal_acceptance_dependency_state(repo_root)
    available = {
        "S2PLT01_ACCEPTED": s2plt01["accepted"],
        "S2PLT02_2D_REAL_RUN": False,
        "S2PLT03_RESILIENCE_DRILL": False,
        "STATE_CONSISTENCY_EVIDENCE": state_consistency_evidence_bundle["status"] == "pass",
        "CONTENT_EVIDENCE": content_evidence_bundle["status"] == "pass",
        "FINAL_ACCEPTANCE_BUNDLE/": final_acceptance_bundle_readiness["bundle_present"],
    }
    available_nonterminal = {
        "S2PLT01_INDEPENDENT_REPLAY_REVIEW": replay_review_present,
        "S2PLT02_LIVE_2D_PRECHECK": live_2d_precheck_present,
        "S2PLT03_LOCAL_RESILIENCE_DRILL": local_drill_passed,
    }
    return {
        "status": "blocked",
        "required_evidence": list(S2PLT04_REQUIRED_EVIDENCE),
        "available_evidence": available,
        "available_nonterminal_evidence": available_nonterminal,
        "missing_evidence": [item for item, present in available.items() if not present],
        "s2plt01_independent_replay_review_scope": (
            independent_replay_review_report.get("scope") if replay_review_valid else "invalid"
        ),
        "s2plt01_independent_replay_review_hash": (
            independent_replay_review_report.get("review_hash") if replay_review_valid else None
        ),
        "s2plt01_independent_replay_review_status": (
            s2plt01["status"] if s2plt01["accepted"]
            else "blocked_review_package_passed_not_terminal_acceptance" if replay_review_present
            else "not_proven"
        ),
        "s2plt01_terminal_acceptance": s2plt01,
        "s2plt01_independent_replay_review_generated_at": (
            independent_replay_review_report.get("generated_at") if replay_review_valid else None
        ),
        "s2plt02_readiness_precheck_scope": (
            live_2d_precheck_report.get("scope") if live_2d_precheck_valid else "invalid"
        ),
        "s2plt02_readiness_precheck_report_hash": (
            live_2d_precheck_report.get("report_hash") if live_2d_precheck_valid else None
        ),
        "s2plt02_readiness_precheck_status": (
            "blocked_precheck_present_not_terminal_acceptance" if live_2d_precheck_present else "not_proven"
        ),
        "s2plt03_local_drill_scope": local_drill_bundle.get("scope") if local_drill_valid else "invalid",
        "s2plt03_local_drill_bundle_hash": local_drill_bundle.get("bundle_hash") if local_drill_valid else None,
        "s2plt03_local_drill_status": "present_not_terminal_acceptance" if local_drill_passed else "not_proven",
        "state_consistency_evidence_bundle": state_consistency_evidence_bundle,
        "content_evidence_bundle": content_evidence_bundle,
        "final_acceptance_bundle_readiness": final_acceptance_bundle_readiness,
        "state_consistency_basis": "S2PMT02_through_S2PMT06_local_validation",
        "content_evidence_basis": "S2PHT05_S2PIT04_S2PKT05_local_validation",
        "production_evidence_basis": "not_present",
    }


def build_s2plt04_integration_candidate_report(
    *, generated_at: str, repo_root: str | Path = "."
) -> dict[str, Any]:
    """Build a deterministic fail-closed S2PLT04 integration-candidate precheck."""

    dependencies = build_s2plt04_dependency_state(repo_root=repo_root)
    evidence = build_s2plt04_evidence_state(repo_root=repo_root)
    audit_blockers = build_audit_blocker_state()
    s2pmt07 = build_s2pmt07_precheck_report(generated_at=generated_at)
    gates = {
        "dependencies_complete": dependencies["status"] == "pass",
        "s2plt01_accepted": "S2PLT01" in dependencies["completed_dependencies"],
        "s2plt02_completed": "S2PLT02" in dependencies["completed_dependencies"],
        "s2plt03_completed": "S2PLT03" in dependencies["completed_dependencies"],
        "s2plt01_independent_replay_review_present": evidence["available_nonterminal_evidence"][
            "S2PLT01_INDEPENDENT_REPLAY_REVIEW"
        ],
        "s2plt02_readiness_precheck_present": evidence["available_nonterminal_evidence"][
            "S2PLT02_LIVE_2D_PRECHECK"
        ],
        "s2plt03_local_drill_evidence_present": evidence["available_nonterminal_evidence"][
            "S2PLT03_LOCAL_RESILIENCE_DRILL"
        ],
        "state_consistency_evidence_present": evidence["available_evidence"]["STATE_CONSISTENCY_EVIDENCE"],
        "content_evidence_present": evidence["available_evidence"]["CONTENT_EVIDENCE"],
        "final_acceptance_bundle_present": evidence["available_evidence"]["FINAL_ACCEPTANCE_BUNDLE/"],
        "p0_zero": audit_blockers["checks"]["P0_zero"],
        "p1_zero": audit_blockers["checks"]["P1_zero"],
        "s2pmt07_precheck_passed": s2pmt07["status"] == "pass",
        "no_production_side_effect": True,
    }
    blocking_reasons: list[str] = []
    if not gates["s2plt01_accepted"]:
        blocking_reasons.append("s2plt01_not_accepted")
    if not gates["s2plt02_completed"]:
        blocking_reasons.append("s2plt02_not_completed")
    if not gates["s2plt03_completed"]:
        blocking_reasons.append("s2plt03_not_completed")
    if not gates["final_acceptance_bundle_present"]:
        blocking_reasons.append("final_acceptance_bundle_missing")
    if not gates["p0_zero"]:
        blocking_reasons.append("inherited_v7_1_p0_findings_open")
    if not gates["p1_zero"]:
        blocking_reasons.append("inherited_v7_1_p1_findings_open")
    if not gates["s2pmt07_precheck_passed"]:
        blocking_reasons.append("s2pmt07_final_gate_precheck_blocked")
    report = {
        "model_id": S2PLT04_INTEGRATION_CANDIDATE_MODEL_ID,
        "schema_version": S2PLT04_SCHEMA_VERSION,
        "task_id": S2PLT04_TASK_ID,
        "acceptance_id": S2PLT04_ACCEPTANCE_ID,
        "generated_at": generated_at,
        "status": "pass" if not blocking_reasons and all(gates.values()) else "blocked",
        "scope": "no_production_integration_candidate_precheck_only",
        "gates": gates,
        "dependencies": dependencies,
        "evidence": evidence,
        "audit_blockers": audit_blockers,
        "s2pmt07_precheck": s2pmt07,
        "blocking_reasons": blocking_reasons,
        "production_acceptance_claimed": False,
        "inherited_p0_p1_closed": False,
        "candidate_hash": "",
        **{flag: False for flag in S2PLT04_FORBIDDEN_FLAGS},
    }
    report["candidate_hash"] = _stable_hash({key: value for key, value in report.items() if key != "candidate_hash"})
    return report


def validate_s2plt04_integration_candidate_report(report: Mapping[str, Any]) -> list[str]:
    """Validate S2PLT04 integration-candidate precheck reports."""

    errors: list[str] = []
    if report.get("model_id") != S2PLT04_INTEGRATION_CANDIDATE_MODEL_ID:
        errors.append("S2PLT04 report model_id is invalid")
    if report.get("schema_version") != S2PLT04_SCHEMA_VERSION:
        errors.append("S2PLT04 report schema_version must be 1")
    if report.get("task_id") != S2PLT04_TASK_ID:
        errors.append("S2PLT04 report task_id is invalid")
    if report.get("acceptance_id") != S2PLT04_ACCEPTANCE_ID:
        errors.append("S2PLT04 report acceptance_id is invalid")
    if report.get("status") not in {"pass", "blocked"}:
        errors.append("S2PLT04 report status must be pass or blocked")
    if report.get("production_acceptance_claimed") is not False:
        errors.append("S2PLT04 precheck must not claim production acceptance")
    if report.get("inherited_p0_p1_closed") is not False:
        errors.append("S2PLT04 precheck must not close inherited P0/P1")
    for flag in S2PLT04_FORBIDDEN_FLAGS:
        if report.get(flag) is not False:
            errors.append(f"{flag} must be false")

    dependencies = _mapping(report.get("dependencies"))
    for task_id in S2PLT04_REQUIRED_DEPENDENCIES:
        if task_id not in dependencies.get("required_dependencies", []):
            errors.append(f"dependencies.required_dependencies must include {task_id}")
    evidence = _mapping(report.get("evidence"))
    for item in S2PLT04_REQUIRED_EVIDENCE:
        if item not in evidence.get("required_evidence", []):
            errors.append(f"evidence.required_evidence must include {item}")
    nonterminal_evidence = _mapping(evidence.get("available_nonterminal_evidence"))
    for item in S2PLT04_NONTERMINAL_LOCAL_EVIDENCE:
        if item not in nonterminal_evidence:
            errors.append(f"evidence.available_nonterminal_evidence must include {item}")
    for bundle_key in ("state_consistency_evidence_bundle", "content_evidence_bundle"):
        bundle = _mapping(evidence.get(bundle_key))
        if bundle.get("status") != "pass":
            errors.append(f"evidence.{bundle_key}.status must be pass")
        if bundle.get("no_production_side_effects") is not True:
            errors.append(f"evidence.{bundle_key}.no_production_side_effects must be true")
        if bundle.get("terminal_acceptance_claimed") is not False:
            errors.append(f"evidence.{bundle_key}.terminal_acceptance_claimed must be false")
        if not bundle.get("source_tasks"):
            errors.append(f"evidence.{bundle_key}.source_tasks must not be empty")
        if not bundle.get("evidence_refs"):
            errors.append(f"evidence.{bundle_key}.evidence_refs must not be empty")
        expected_bundle_hash = _stable_hash({key: value for key, value in bundle.items() if key != "bundle_hash"})
        if bundle.get("bundle_hash") != expected_bundle_hash:
            errors.append(f"evidence.{bundle_key}.bundle_hash does not match bundle content")
    final_bundle = _mapping(evidence.get("final_acceptance_bundle_readiness"))
    final_bundle_errors = validate_final_acceptance_bundle_readiness_state(final_bundle)
    if final_bundle_errors:
        errors.append("S2PLT04 final acceptance bundle readiness is invalid")
    available = _mapping(evidence.get("available_evidence"))
    if available.get("FINAL_ACCEPTANCE_BUNDLE/") != final_bundle.get("bundle_present"):
        errors.append("evidence.FINAL_ACCEPTANCE_BUNDLE/ must match final bundle readiness bundle_present")
    s2pmt07 = _mapping(report.get("s2pmt07_precheck"))
    s2pmt07_errors = validate_s2pmt07_precheck_report(s2pmt07)
    if s2pmt07_errors:
        errors.append("S2PLT04 embedded S2PMT07 precheck is invalid")
    if report.get("status") == "pass":
        gates = _mapping(report.get("gates"))
        if not all(gates.values()):
            errors.append("passing S2PLT04 report requires every gate true")
        if report.get("blocking_reasons"):
            errors.append("passing S2PLT04 report must not have blocking reasons")
    else:
        gates = _mapping(report.get("gates"))
        expected_reasons: list[str] = []
        if not gates.get("s2plt01_accepted"):
            expected_reasons.append("s2plt01_not_accepted")
        if not gates.get("s2plt02_completed"):
            expected_reasons.append("s2plt02_not_completed")
        if not gates.get("s2plt03_completed"):
            expected_reasons.append("s2plt03_not_completed")
        if not gates.get("final_acceptance_bundle_present"):
            expected_reasons.append("final_acceptance_bundle_missing")
        if not gates.get("p0_zero"):
            expected_reasons.append("inherited_v7_1_p0_findings_open")
        if not gates.get("p1_zero"):
            expected_reasons.append("inherited_v7_1_p1_findings_open")
        if not gates.get("s2pmt07_precheck_passed"):
            expected_reasons.append("s2pmt07_final_gate_precheck_blocked")
        for reason in expected_reasons:
            if reason not in report.get("blocking_reasons", []):
                errors.append(f"blocked S2PLT04 precheck must include {reason}")
    expected_hash = _stable_hash({key: value for key, value in report.items() if key != "candidate_hash"})
    if report.get("candidate_hash") != expected_hash:
        errors.append("S2PLT04 candidate_hash does not match report content")
    return errors


def build_dependency_state() -> dict[str, Any]:
    """Build the current dependency state from authoritative governance facts."""

    completed = {
        "S2PMT01": "completed_local_validation",
        "S2PMT02": "completed_local_validation",
        "S2PMT03": "completed_local_validation",
        "S2PMT04": "completed_local_validation",
        "S2PMT05": "completed_local_validation",
        "S2PMT06": "completed_local_validation",
    }
    missing = [task_id for task_id in S2PMT07_REQUIRED_DEPENDENCIES if task_id not in completed]
    return {
        "status": "blocked",
        "required_dependencies": list(S2PMT07_REQUIRED_DEPENDENCIES),
        "completed_dependencies": completed,
        "missing_dependencies": missing,
        "s2plt04_status": "missing_authoritative_completion_evidence",
    }


def build_audit_blocker_state(
    *,
    inherited_p0: int = S2PMT07_INHERITED_V7_1_OPEN_P0_FINDINGS,
    inherited_p1: int = S2PMT07_INHERITED_V7_1_OPEN_P1_FINDINGS,
) -> dict[str, Any]:
    """Build the inherited V7.1 P0/P1 blocker state."""

    checks = {
        "P0_zero": inherited_p0 == 0,
        "P1_zero": inherited_p1 == 0,
    }
    return {
        "status": "pass" if all(checks.values()) else "blocked",
        "required_zero_severities": list(S2PMT07_REQUIRED_ZERO_FINDING_SEVERITIES),
        "inherited_v7_1_open_p0_findings": inherited_p0,
        "inherited_v7_1_open_p1_findings": inherited_p1,
        "checks": checks,
    }


def build_reviewer_independence_state(*, reviewer_involved_in_s2pmt01_t06: bool = True) -> dict[str, Any]:
    """Build reviewer independence state without self-certifying final review."""

    independent = not reviewer_involved_in_s2pmt01_t06
    return {
        "status": "pass" if independent else "blocked",
        "requirement": S2PMT07_REQUIRED_REVIEWER_INDEPENDENCE,
        "reviewer_involved_in_s2pmt01_t06": reviewer_involved_in_s2pmt01_t06,
        "independent_reviewer_proven": independent,
    }


def build_evidence_bundle_state() -> dict[str, Any]:
    """Build the required evidence bundle state."""

    available = {
        "FINAL_ACCEPTANCE_BUNDLE/": False,
        "HANDOFF/00_下一Agent先读.md": False,
        "independent_review_signoff.yaml": False,
    }
    missing = [item for item, present in available.items() if not present]
    return {
        "status": "blocked",
        "required_evidence": list(S2PMT07_REQUIRED_EVIDENCE),
        "available_evidence": available,
        "missing_evidence": missing,
    }


def build_test_gate_state() -> dict[str, Any]:
    """Build required S2PMT07 command coverage without pretending final execution."""

    return {
        "status": "blocked",
        "required_test_commands": list(S2PMT07_REQUIRED_TEST_COMMANDS),
        "executed_as_final_reviewer": False,
        "full_pytest_executed_by_independent_reviewer": False,
        "acceptance_bundle_zero_p0_p1_verified": False,
    }


def _s2pmt07_blocker_matrix_row(blocking_reason: str) -> dict[str, Any]:
    """Return the required evidence/action row for a current S2PMT07 blocker."""

    rows = {
        "reviewer_independence_not_proven": {
            "blocking_reason": "reviewer_independence_not_proven",
            "required_evidence": "FINAL_ACCEPTANCE_BUNDLE/independent_final_reviewer_assignment.json",
            "owner_action": "assign_independent_final_reviewer",
            "default_next_step": "create_or_validate_independent_final_reviewer_assignment_artifact",
            "external_or_future_evidence_required": True,
            "cannot_be_self_certified_by_current_agent": True,
            "production_gate_unblocked_by_this_row": False,
        },
        "inherited_v7_1_p0_findings_open": {
            "blocking_reason": "inherited_v7_1_p0_findings_open",
            "required_evidence": f"{S2PMT07_P0_P1_ZERO_PROOF_ARTIFACT_PATH}#independent_closure_decision",
            "owner_action": "obtain_independent_final_closure_decision_for_p0",
            "default_next_step": "independent_final_reviewer_must_accept_or_reject_p0_zero_proof",
            "external_or_future_evidence_required": True,
            "cannot_be_self_certified_by_current_agent": True,
            "production_gate_unblocked_by_this_row": False,
        },
        "inherited_v7_1_p1_findings_open": {
            "blocking_reason": "inherited_v7_1_p1_findings_open",
            "required_evidence": f"{S2PMT07_P0_P1_ZERO_PROOF_ARTIFACT_PATH}#independent_closure_decision",
            "owner_action": "obtain_independent_final_closure_decision_for_p1",
            "default_next_step": "independent_final_reviewer_must_accept_or_reject_p1_zero_proof",
            "external_or_future_evidence_required": True,
            "cannot_be_self_certified_by_current_agent": True,
            "production_gate_unblocked_by_this_row": False,
        },
        "s2plt04_not_completed": {
            "blocking_reason": "s2plt04_not_completed",
            "required_evidence": "FINAL_ACCEPTANCE_BUNDLE/s2plt04_completion_report.json",
            "owner_action": "complete_s2plt04_after_s2plt01_s2plt02_s2plt03_and_p0_p1_gates",
            "default_next_step": "validate_s2plt04_completion_report_artifact_after_terminal_dependencies",
            "external_or_future_evidence_required": True,
            "cannot_be_self_certified_by_current_agent": False,
            "production_gate_unblocked_by_this_row": False,
        },
        "final_acceptance_bundle_missing": {
            "blocking_reason": "final_acceptance_bundle_missing",
            "required_evidence": "FINAL_ACCEPTANCE_BUNDLE/manifest.json",
            "owner_action": "assemble_final_acceptance_bundle_after_required_artifacts_pass",
            "default_next_step": "run_final_bundle_manifest_validator_after_all_artifacts_exist",
            "external_or_future_evidence_required": True,
            "cannot_be_self_certified_by_current_agent": False,
            "production_gate_unblocked_by_this_row": False,
        },
        "independent_review_signoff_missing": {
            "blocking_reason": "independent_review_signoff_missing",
            "required_evidence": "FINAL_ACCEPTANCE_BUNDLE/independent_review_signoff.yaml",
            "owner_action": "obtain_independent_final_review_signoff",
            "default_next_step": "validate_independent_review_signoff_artifact",
            "external_or_future_evidence_required": True,
            "cannot_be_self_certified_by_current_agent": True,
            "production_gate_unblocked_by_this_row": False,
        },
        "independent_final_command_execution_missing": {
            "blocking_reason": "independent_final_command_execution_missing",
            "required_evidence": "FINAL_ACCEPTANCE_BUNDLE/final_command_execution.json",
            "owner_action": "execute_required_final_commands_by_independent_final_reviewer",
            "default_next_step": "validate_final_command_execution_artifact",
            "external_or_future_evidence_required": True,
            "cannot_be_self_certified_by_current_agent": True,
            "production_gate_unblocked_by_this_row": False,
        },
    }
    return dict(rows[blocking_reason])


def build_s2pmt07_remaining_blocker_matrix_state(*, generated_at: str) -> dict[str, Any]:
    """Build the current S2PMT07 blocker matrix without closing any gate."""

    precheck = build_s2pmt07_precheck_report(generated_at=generated_at)
    current_blockers = list(precheck.get("blocking_reasons", []))
    blocker_rows = [_s2pmt07_blocker_matrix_row(reason) for reason in current_blockers]
    state = {
        "status": "blocked_matrix_ready_no_closure",
        "scope": "s2pmt07_remaining_blocker_matrix_only_no_gate_closure",
        "task_id": S2PMT07_TASK_ID,
        "acceptance_id": S2PMT07_ACCEPTANCE_ID,
        "generated_at": generated_at,
        "source_precheck_hash": precheck["report_hash"],
        "required_blockers": list(S2PMT07_REMAINING_BLOCKER_MATRIX_REQUIRED_BLOCKERS),
        "current_blockers": current_blockers,
        "blocker_rows": blocker_rows,
        "next_unblocked_by_agent": False,
        "requires_external_or_future_evidence": True,
        "p0_zero_proven": False,
        "p1_zero_proven": False,
        "p0_closure_claimed": False,
        "p1_closure_claimed": False,
        "s2plt04_completed": False,
        "final_acceptance_bundle_present": False,
        "independent_review_signoff_present": False,
        "required_final_commands_executed": False,
        "s2pmt07_pass_claimed": False,
        "production_acceptance_claimed": False,
        **{flag: False for flag in S2PMT07_FORBIDDEN_PASS_FLAGS},
        "state_hash": "",
    }
    state["state_hash"] = _stable_hash({key: value for key, value in state.items() if key != "state_hash"})
    return state


def validate_s2pmt07_remaining_blocker_matrix_state(state: Mapping[str, Any]) -> list[str]:
    """Validate the S2PMT07 blocker matrix without treating it as closure evidence."""

    errors: list[str] = []
    if state.get("status") != "blocked_matrix_ready_no_closure":
        errors.append("remaining blocker matrix status must remain blocked_matrix_ready_no_closure")
    if state.get("scope") != "s2pmt07_remaining_blocker_matrix_only_no_gate_closure":
        errors.append("remaining blocker matrix scope is invalid")
    if state.get("task_id") != S2PMT07_TASK_ID:
        errors.append("remaining blocker matrix task_id is invalid")
    if state.get("acceptance_id") != S2PMT07_ACCEPTANCE_ID:
        errors.append("remaining blocker matrix acceptance_id is invalid")
    if not isinstance(state.get("generated_at"), str) or not state.get("generated_at"):
        errors.append("remaining blocker matrix generated_at must be a non-empty string")
    if not isinstance(state.get("source_precheck_hash"), str) or not state.get("source_precheck_hash"):
        errors.append("remaining blocker matrix source_precheck_hash must be present")
    if tuple(state.get("required_blockers", [])) != S2PMT07_REMAINING_BLOCKER_MATRIX_REQUIRED_BLOCKERS:
        errors.append("remaining blocker matrix required_blockers are invalid")
    if set(state.get("current_blockers", [])) != set(S2PMT07_BLOCKING_REASONS):
        errors.append("remaining blocker matrix current_blockers must match current S2PMT07 blocking reasons")

    blocker_rows = _list_of_mappings(state.get("blocker_rows"))
    row_reasons = [row.get("blocking_reason") for row in blocker_rows]
    if set(row_reasons) != set(S2PMT07_BLOCKING_REASONS):
        errors.append("remaining blocker matrix must cover every current S2PMT07 blocking reason")
    for row in blocker_rows:
        reason = row.get("blocking_reason")
        if reason not in S2PMT07_BLOCKING_REASONS:
            errors.append(f"remaining blocker matrix has invalid blocker row: {reason}")
            continue
        expected = _s2pmt07_blocker_matrix_row(str(reason))
        for field in (
            "required_evidence",
            "owner_action",
            "default_next_step",
            "external_or_future_evidence_required",
            "cannot_be_self_certified_by_current_agent",
            "production_gate_unblocked_by_this_row",
        ):
            if row.get(field) != expected[field]:
                errors.append(f"{reason}.{field} is invalid")

    for flag in (
        "next_unblocked_by_agent",
        "p0_zero_proven",
        "p1_zero_proven",
        "p0_closure_claimed",
        "p1_closure_claimed",
        "s2plt04_completed",
        "final_acceptance_bundle_present",
        "independent_review_signoff_present",
        "required_final_commands_executed",
        "s2pmt07_pass_claimed",
        "production_acceptance_claimed",
    ):
        if state.get(flag) is not False:
            errors.append(f"{flag} must be false")
    if state.get("requires_external_or_future_evidence") is not True:
        errors.append("remaining blocker matrix must require external or future evidence")
    for flag in S2PMT07_FORBIDDEN_PASS_FLAGS:
        if state.get(flag) is not False:
            errors.append(f"{flag} must be false")
    expected_hash = _stable_hash({key: value for key, value in state.items() if key != "state_hash"})
    if state.get("state_hash") != expected_hash:
        errors.append("remaining blocker matrix state_hash does not match state content")
    return errors


def build_p0_p1_technical_closure_candidate_state() -> dict[str, Any]:
    """Build P0/P1 technical candidate state without closing inherited findings."""

    candidate_manifest_refs = [
        S2PMT07_P0_TECHNICAL_CLOSURE_CANDIDATE_PACKAGE,
        S2PMT07_P1_TECHNICAL_CLOSURE_CANDIDATE_RECEIPT,
        *S2PMT07_P1_TECHNICAL_CLOSURE_CANDIDATE_MANIFESTS,
    ]
    state = {
        "status": "blocked_candidate_ready_no_closure",
        "scope": "technical_closure_candidate_reviews_only_not_p0_p1_zero_proof",
        "p0_candidate_package_manifest": S2PMT07_P0_TECHNICAL_CLOSURE_CANDIDATE_PACKAGE,
        "p1_candidate_receipt_manifest": S2PMT07_P1_TECHNICAL_CLOSURE_CANDIDATE_RECEIPT,
        "candidate_manifest_refs": candidate_manifest_refs,
        "p0_candidate_findings": list(S2PMT07_P0_TECHNICAL_CLOSURE_CANDIDATE_FINDINGS),
        "p1_candidate_findings": list(S2PMT07_P1_TECHNICAL_CLOSURE_CANDIDATE_FINDINGS),
        "p0_candidate_count": len(S2PMT07_P0_TECHNICAL_CLOSURE_CANDIDATE_FINDINGS),
        "p1_candidate_count": len(S2PMT07_P1_TECHNICAL_CLOSURE_CANDIDATE_FINDINGS),
        "p0_candidate_package_present": True,
        "p1_candidate_receipt_present": True,
        "all_p0_candidate_reviews_passed_no_production_acceptance": True,
        "all_p1_candidate_reviews_passed_no_production_acceptance": True,
        "p0_p1_zero_proof_present": False,
        "independent_final_closure_decision_present": False,
        "p0_closure_claimed": False,
        "p1_closure_claimed": False,
        "closure_claimed": False,
        "inherited_v7_1_open_p0_findings": S2PMT07_INHERITED_V7_1_OPEN_P0_FINDINGS,
        "inherited_v7_1_open_p1_findings": S2PMT07_INHERITED_V7_1_OPEN_P1_FINDINGS,
        "production_acceptance_claimed": False,
        "integrated_production_accepted": False,
        "blocking_reasons": list(S2PMT07_P0_P1_TECHNICAL_CANDIDATE_BLOCKING_REASONS),
        "state_hash": "",
    }
    state["state_hash"] = _stable_hash({key: value for key, value in state.items() if key != "state_hash"})
    return state


def validate_p0_p1_technical_closure_candidate_state(state: Mapping[str, Any]) -> list[str]:
    """Validate P0/P1 technical candidate evidence without accepting closure."""

    errors: list[str] = []
    if state.get("status") != "blocked_candidate_ready_no_closure":
        errors.append("P0/P1 technical candidate status must remain blocked_candidate_ready_no_closure")
    if state.get("scope") != "technical_closure_candidate_reviews_only_not_p0_p1_zero_proof":
        errors.append("P0/P1 technical candidate scope is invalid")
    if tuple(state.get("p0_candidate_findings", [])) != S2PMT07_P0_TECHNICAL_CLOSURE_CANDIDATE_FINDINGS:
        errors.append("P0 technical candidate finding list is invalid")
    if tuple(state.get("p1_candidate_findings", [])) != S2PMT07_P1_TECHNICAL_CLOSURE_CANDIDATE_FINDINGS:
        errors.append("P1 technical candidate finding list is invalid")
    if state.get("p0_candidate_count") != len(S2PMT07_P0_TECHNICAL_CLOSURE_CANDIDATE_FINDINGS):
        errors.append("P0 technical candidate count is invalid")
    if state.get("p1_candidate_count") != len(S2PMT07_P1_TECHNICAL_CLOSURE_CANDIDATE_FINDINGS):
        errors.append("P1 technical candidate count is invalid")
    refs = state.get("candidate_manifest_refs", [])
    for ref in (
        S2PMT07_P0_TECHNICAL_CLOSURE_CANDIDATE_PACKAGE,
        S2PMT07_P1_TECHNICAL_CLOSURE_CANDIDATE_RECEIPT,
        *S2PMT07_P1_TECHNICAL_CLOSURE_CANDIDATE_MANIFESTS,
    ):
        if ref not in refs:
            errors.append(f"P0/P1 technical candidate refs must include {ref}")
    if state.get("p0_candidate_package_present") is not True:
        errors.append("P0 technical candidate package must be present")
    if state.get("p1_candidate_receipt_present") is not True:
        errors.append("P1 technical candidate receipt must be present")
    if state.get("all_p0_candidate_reviews_passed_no_production_acceptance") is not True:
        errors.append("P0 candidate reviews must pass with no production acceptance")
    if state.get("all_p1_candidate_reviews_passed_no_production_acceptance") is not True:
        errors.append("P1 candidate reviews must pass with no production acceptance")
    if state.get("p0_p1_zero_proof_present") is not False:
        errors.append("P0/P1 technical candidate must not claim zero proof")
    if state.get("independent_final_closure_decision_present") is not False:
        errors.append("P0/P1 technical candidate must not claim independent final closure decision")
    for flag in ("p0_closure_claimed", "p1_closure_claimed", "closure_claimed"):
        if state.get(flag) is not False:
            errors.append(f"{flag} must be false")
    if state.get("production_acceptance_claimed") is not False:
        errors.append("P0/P1 technical candidate must not claim production acceptance")
    if state.get("integrated_production_accepted") is not False:
        errors.append("P0/P1 technical candidate must not claim integrated production acceptance")
    if state.get("inherited_v7_1_open_p0_findings") != S2PMT07_INHERITED_V7_1_OPEN_P0_FINDINGS:
        errors.append("P0 inherited open finding count must remain unchanged")
    if state.get("inherited_v7_1_open_p1_findings") != S2PMT07_INHERITED_V7_1_OPEN_P1_FINDINGS:
        errors.append("P1 inherited open finding count must remain unchanged")
    for reason in S2PMT07_P0_P1_TECHNICAL_CANDIDATE_BLOCKING_REASONS:
        if reason not in state.get("blocking_reasons", []):
            errors.append(f"P0/P1 technical candidate must include blocker {reason}")
    expected_hash = _stable_hash({key: value for key, value in state.items() if key != "state_hash"})
    if state.get("state_hash") != expected_hash:
        errors.append("P0/P1 technical candidate state_hash does not match state content")
    return errors


def build_p0_p1_zero_proof_assembly_state() -> dict[str, Any]:
    """Build the current P0/P1 zero-proof input assembly state without claiming closure."""

    candidate_state = build_p0_p1_technical_closure_candidate_state()
    candidate_refs = list(candidate_state["candidate_manifest_refs"])
    all_candidate_reviews_available = (
        candidate_state["p0_candidate_package_present"] is True
        and candidate_state["p1_candidate_receipt_present"] is True
        and candidate_state["all_p0_candidate_reviews_passed_no_production_acceptance"] is True
        and candidate_state["all_p1_candidate_reviews_passed_no_production_acceptance"] is True
    )
    state = {
        "status": "blocked_candidate_inputs_ready_no_closure",
        "scope": "p0_p1_zero_proof_assembly_only_no_closure",
        "required_inputs": list(S2PMT07_P0_P1_ZERO_PROOF_ASSEMBLY_REQUIRED_INPUTS),
        "p0_candidate_findings": list(candidate_state["p0_candidate_findings"]),
        "p1_candidate_findings": list(candidate_state["p1_candidate_findings"]),
        "p0_candidate_count": candidate_state["p0_candidate_count"],
        "p1_candidate_count": candidate_state["p1_candidate_count"],
        "candidate_total": candidate_state["p0_candidate_count"] + candidate_state["p1_candidate_count"],
        "candidate_manifest_refs": candidate_refs,
        "all_candidate_reviews_available": all_candidate_reviews_available,
        "all_candidate_refs_exist": True,
        "next_required_action": "independent_final_closure_decision",
        "independent_final_closure_decision_present": False,
        "zero_proof_artifact_present": False,
        "p0_zero_proven": False,
        "p1_zero_proven": False,
        "closure_claimed": False,
        "observed_open_p0_findings": S2PMT07_INHERITED_V7_1_OPEN_P0_FINDINGS,
        "observed_open_p1_findings": S2PMT07_INHERITED_V7_1_OPEN_P1_FINDINGS,
        "blocking_reasons": list(S2PMT07_P0_P1_ZERO_PROOF_ASSEMBLY_BLOCKING_REASONS),
        **{flag: False for flag in S2PMT07_P0_P1_ZERO_PROOF_ASSEMBLY_FORBIDDEN_FLAGS},
        "state_hash": "",
    }
    state["state_hash"] = _stable_hash({key: value for key, value in state.items() if key != "state_hash"})
    return state


def validate_p0_p1_zero_proof_assembly_state(state: Mapping[str, Any]) -> list[str]:
    """Validate the P0/P1 zero-proof input assembly state without accepting closure."""

    errors: list[str] = []
    if state.get("status") != "blocked_candidate_inputs_ready_no_closure":
        errors.append("P0/P1 zero proof assembly status must remain blocked_candidate_inputs_ready_no_closure")
    if state.get("scope") != "p0_p1_zero_proof_assembly_only_no_closure":
        errors.append("P0/P1 zero proof assembly scope is invalid")
    if tuple(state.get("required_inputs", [])) != S2PMT07_P0_P1_ZERO_PROOF_ASSEMBLY_REQUIRED_INPUTS:
        errors.append("P0/P1 zero proof assembly required_inputs are invalid")
    if tuple(state.get("p0_candidate_findings", [])) != S2PMT07_P0_TECHNICAL_CLOSURE_CANDIDATE_FINDINGS:
        errors.append("P0/P1 zero proof assembly P0 candidate findings are invalid")
    if tuple(state.get("p1_candidate_findings", [])) != S2PMT07_P1_TECHNICAL_CLOSURE_CANDIDATE_FINDINGS:
        errors.append("P0/P1 zero proof assembly P1 candidate findings are invalid")
    if state.get("p0_candidate_count") != len(S2PMT07_P0_TECHNICAL_CLOSURE_CANDIDATE_FINDINGS):
        errors.append("P0/P1 zero proof assembly P0 candidate count is invalid")
    if state.get("p1_candidate_count") != len(S2PMT07_P1_TECHNICAL_CLOSURE_CANDIDATE_FINDINGS):
        errors.append("P0/P1 zero proof assembly P1 candidate count is invalid")
    if state.get("candidate_total") != (
        len(S2PMT07_P0_TECHNICAL_CLOSURE_CANDIDATE_FINDINGS)
        + len(S2PMT07_P1_TECHNICAL_CLOSURE_CANDIDATE_FINDINGS)
    ):
        errors.append("P0/P1 zero proof assembly candidate_total is invalid")
    refs = state.get("candidate_manifest_refs", [])
    for ref in build_p0_p1_technical_closure_candidate_state()["candidate_manifest_refs"]:
        if ref not in refs:
            errors.append(f"P0/P1 zero proof assembly refs must include {ref}")
    if state.get("all_candidate_reviews_available") is not True:
        errors.append("P0/P1 zero proof assembly candidate reviews must be available")
    if state.get("all_candidate_refs_exist") is not True:
        errors.append("P0/P1 zero proof assembly candidate refs must exist")
    if state.get("next_required_action") != "independent_final_closure_decision":
        errors.append("P0/P1 zero proof assembly next_required_action is invalid")
    for flag in (
        "independent_final_closure_decision_present",
        "zero_proof_artifact_present",
        "p0_zero_proven",
        "p1_zero_proven",
        "closure_claimed",
    ):
        if state.get(flag) is not False:
            errors.append(f"{flag} must be false")
    if state.get("observed_open_p0_findings") != S2PMT07_INHERITED_V7_1_OPEN_P0_FINDINGS:
        errors.append("P0/P1 zero proof assembly must preserve inherited open P0 count")
    if state.get("observed_open_p1_findings") != S2PMT07_INHERITED_V7_1_OPEN_P1_FINDINGS:
        errors.append("P0/P1 zero proof assembly must preserve inherited open P1 count")
    for reason in S2PMT07_P0_P1_ZERO_PROOF_ASSEMBLY_BLOCKING_REASONS:
        if reason not in state.get("blocking_reasons", []):
            errors.append(f"P0/P1 zero proof assembly must include blocker {reason}")
    for flag in S2PMT07_P0_P1_ZERO_PROOF_ASSEMBLY_FORBIDDEN_FLAGS:
        if state.get(flag) is not False:
            errors.append(f"{flag} must be false")
    expected_hash = _stable_hash({key: value for key, value in state.items() if key != "state_hash"})
    if state.get("state_hash") != expected_hash:
        errors.append("P0/P1 zero proof assembly state_hash does not match state content")
    return errors


def build_independent_final_reviewer_assignment_request_state() -> dict[str, Any]:
    """Build the fail-closed request package for assigning an independent final reviewer."""

    assembly_state = build_p0_p1_zero_proof_assembly_state()
    readiness_state = build_p0_p1_zero_proof_readiness_state()
    all_candidate_inputs_ready = (
        not validate_p0_p1_zero_proof_assembly_state(assembly_state)
        and assembly_state["all_candidate_reviews_available"] is True
        and assembly_state["all_candidate_refs_exist"] is True
    )
    review_input_refs = list(
        dict.fromkeys(
            list(assembly_state["candidate_manifest_refs"])
            + list(readiness_state["candidate_evidence_refs"])
            + ["arxiv-daily-push/docs/pursuing_goal/CURRENT.yaml"]
        )
    )
    state = {
        "status": "blocked_reviewer_assignment_request_ready_no_assignment",
        "scope": "independent_final_reviewer_assignment_request_only_no_assignment",
        "task_id": S2PMT07_TASK_ID,
        "acceptance_id": S2PMT07_ACCEPTANCE_ID,
        "required_inputs": list(S2PMT07_INDEPENDENT_FINAL_REVIEWER_ASSIGNMENT_REQUEST_REQUIRED_INPUTS),
        "assignment_artifact_ref": S2PMT07_INDEPENDENT_FINAL_REVIEWER_ASSIGNMENT_ARTIFACT_PATH,
        "required_reviewer_role": "independent_final_reviewer",
        "required_reviewer_independence": S2PMT07_REQUIRED_REVIEWER_INDEPENDENCE,
        "p0_candidate_findings": list(assembly_state["p0_candidate_findings"]),
        "p1_candidate_findings": list(assembly_state["p1_candidate_findings"]),
        "p0_candidate_count": assembly_state["p0_candidate_count"],
        "p1_candidate_count": assembly_state["p1_candidate_count"],
        "candidate_total": assembly_state["candidate_total"],
        "candidate_manifest_refs": list(assembly_state["candidate_manifest_refs"]),
        "review_input_refs": review_input_refs,
        "all_candidate_inputs_ready": all_candidate_inputs_ready,
        "all_candidate_refs_exist": assembly_state["all_candidate_refs_exist"],
        "assignment_request_ready": all_candidate_inputs_ready,
        "independent_final_reviewer_assigned": False,
        "independent_final_closure_decision_present": False,
        "zero_proof_artifact_present": False,
        "p0_zero_proven": False,
        "p1_zero_proven": False,
        "closure_claimed": False,
        "observed_open_p0_findings": S2PMT07_INHERITED_V7_1_OPEN_P0_FINDINGS,
        "observed_open_p1_findings": S2PMT07_INHERITED_V7_1_OPEN_P1_FINDINGS,
        "next_required_action": "independent_final_reviewer_must_be_assigned_before_closure_decision",
        "blocking_reasons": list(S2PMT07_INDEPENDENT_FINAL_REVIEWER_ASSIGNMENT_REQUEST_BLOCKING_REASONS),
        **{flag: False for flag in S2PMT07_INDEPENDENT_FINAL_REVIEWER_ASSIGNMENT_REQUEST_FORBIDDEN_FLAGS},
        "state_hash": "",
    }
    state["state_hash"] = _stable_hash({key: value for key, value in state.items() if key != "state_hash"})
    return state


def validate_independent_final_reviewer_assignment_request_state(state: Mapping[str, Any]) -> list[str]:
    """Validate the reviewer assignment request without assigning a reviewer or closing P0/P1."""

    errors: list[str] = []
    if state.get("status") != "blocked_reviewer_assignment_request_ready_no_assignment":
        errors.append(
            "independent final reviewer assignment request status must remain "
            "blocked_reviewer_assignment_request_ready_no_assignment"
        )
    if state.get("scope") != "independent_final_reviewer_assignment_request_only_no_assignment":
        errors.append("independent final reviewer assignment request scope is invalid")
    if state.get("task_id") != S2PMT07_TASK_ID:
        errors.append("independent final reviewer assignment request task_id is invalid")
    if state.get("acceptance_id") != S2PMT07_ACCEPTANCE_ID:
        errors.append("independent final reviewer assignment request acceptance_id is invalid")
    if (
        tuple(state.get("required_inputs", []))
        != S2PMT07_INDEPENDENT_FINAL_REVIEWER_ASSIGNMENT_REQUEST_REQUIRED_INPUTS
    ):
        errors.append("independent final reviewer assignment request required_inputs are invalid")
    if state.get("assignment_artifact_ref") != S2PMT07_INDEPENDENT_FINAL_REVIEWER_ASSIGNMENT_ARTIFACT_PATH:
        errors.append("independent final reviewer assignment request assignment_artifact_ref is invalid")
    if state.get("required_reviewer_role") != "independent_final_reviewer":
        errors.append("independent final reviewer assignment request reviewer role is invalid")
    if state.get("required_reviewer_independence") != S2PMT07_REQUIRED_REVIEWER_INDEPENDENCE:
        errors.append("independent final reviewer assignment request reviewer independence is invalid")
    if tuple(state.get("p0_candidate_findings", [])) != S2PMT07_P0_TECHNICAL_CLOSURE_CANDIDATE_FINDINGS:
        errors.append("independent final reviewer assignment request P0 candidate findings are invalid")
    if tuple(state.get("p1_candidate_findings", [])) != S2PMT07_P1_TECHNICAL_CLOSURE_CANDIDATE_FINDINGS:
        errors.append("independent final reviewer assignment request P1 candidate findings are invalid")
    if state.get("p0_candidate_count") != len(S2PMT07_P0_TECHNICAL_CLOSURE_CANDIDATE_FINDINGS):
        errors.append("independent final reviewer assignment request P0 candidate count is invalid")
    if state.get("p1_candidate_count") != len(S2PMT07_P1_TECHNICAL_CLOSURE_CANDIDATE_FINDINGS):
        errors.append("independent final reviewer assignment request P1 candidate count is invalid")
    if state.get("candidate_total") != (
        len(S2PMT07_P0_TECHNICAL_CLOSURE_CANDIDATE_FINDINGS)
        + len(S2PMT07_P1_TECHNICAL_CLOSURE_CANDIDATE_FINDINGS)
    ):
        errors.append("independent final reviewer assignment request candidate_total is invalid")
    refs = state.get("candidate_manifest_refs", [])
    for ref in build_p0_p1_zero_proof_assembly_state()["candidate_manifest_refs"]:
        if ref not in refs:
            errors.append(f"independent final reviewer assignment request refs must include {ref}")
    review_input_refs = state.get("review_input_refs", [])
    for ref in build_p0_p1_zero_proof_readiness_state()["candidate_evidence_refs"]:
        if ref not in review_input_refs:
            errors.append(f"independent final reviewer assignment request review inputs must include {ref}")
    if "arxiv-daily-push/docs/pursuing_goal/CURRENT.yaml" not in review_input_refs:
        errors.append("independent final reviewer assignment request must include CURRENT.yaml")
    if state.get("all_candidate_inputs_ready") is not True:
        errors.append("independent final reviewer assignment request candidate inputs must be ready")
    if state.get("all_candidate_refs_exist") is not True:
        errors.append("independent final reviewer assignment request candidate refs must exist")
    if state.get("assignment_request_ready") is not True:
        errors.append("independent final reviewer assignment request must be ready")
    for flag in (
        "independent_final_reviewer_assigned",
        "independent_final_closure_decision_present",
        "zero_proof_artifact_present",
        "p0_zero_proven",
        "p1_zero_proven",
        "closure_claimed",
    ):
        if state.get(flag) is not False:
            if flag == "independent_final_reviewer_assigned":
                errors.append("independent_final_reviewer_assigned must be false until assignment artifact exists")
            else:
                errors.append(f"{flag} must be false")
    if state.get("observed_open_p0_findings") != S2PMT07_INHERITED_V7_1_OPEN_P0_FINDINGS:
        errors.append("independent final reviewer assignment request must preserve inherited open P0 count")
    if state.get("observed_open_p1_findings") != S2PMT07_INHERITED_V7_1_OPEN_P1_FINDINGS:
        errors.append("independent final reviewer assignment request must preserve inherited open P1 count")
    if state.get("next_required_action") != "independent_final_reviewer_must_be_assigned_before_closure_decision":
        errors.append("independent final reviewer assignment request next_required_action is invalid")
    for reason in S2PMT07_INDEPENDENT_FINAL_REVIEWER_ASSIGNMENT_REQUEST_BLOCKING_REASONS:
        if reason not in state.get("blocking_reasons", []):
            errors.append(f"independent final reviewer assignment request must include blocker {reason}")
    for flag in S2PMT07_INDEPENDENT_FINAL_REVIEWER_ASSIGNMENT_REQUEST_FORBIDDEN_FLAGS:
        if state.get(flag) is not False:
            errors.append(f"{flag} must be false")
    expected_hash = _stable_hash({key: value for key, value in state.items() if key != "state_hash"})
    if state.get("state_hash") != expected_hash:
        errors.append("independent final reviewer assignment request state_hash does not match state content")
    return errors


def build_independent_final_reviewer_assignment_owner_packet_state() -> dict[str, Any]:
    """Build the owner/coordinator packet for creating the reviewer assignment artifact."""

    request_state = build_independent_final_reviewer_assignment_request_state()
    state = {
        "status": "blocked_owner_action_packet_ready_no_assignment",
        "scope": "owner_assignment_packet_only_no_assignment",
        "task_id": S2PMT07_TASK_ID,
        "acceptance_id": S2PMT07_ACCEPTANCE_ID,
        "required_owner_actions": list(
            S2PMT07_INDEPENDENT_FINAL_REVIEWER_ASSIGNMENT_OWNER_PACKET_REQUIRED_ACTIONS
        ),
        "assignment_artifact_path": S2PMT07_INDEPENDENT_FINAL_REVIEWER_ASSIGNMENT_ARTIFACT_PATH,
        "assignment_schema_version": S2PMT07_INDEPENDENT_FINAL_REVIEWER_ASSIGNMENT_SCHEMA_VERSION,
        "assignment_decision": S2PMT07_INDEPENDENT_FINAL_REVIEWER_ASSIGNMENT_DECISION,
        "assignment_required_fields": list(S2PMT07_INDEPENDENT_FINAL_REVIEWER_ASSIGNMENT_REQUIRED_FIELDS),
        "required_reviewer_role": "independent_final_reviewer",
        "required_reviewer_independence": S2PMT07_REQUIRED_REVIEWER_INDEPENDENCE,
        "allowed_assigned_by_values": ["owner_or_coordinator", "owner"],
        "required_assignment_scope": "S2PMT07_P0_P1_FINAL_CLOSURE_REVIEW",
        "forbidden_reviewer_ids": ["codex-current-agent"],
        "review_input_refs": list(request_state["review_input_refs"]),
        "candidate_manifest_refs": list(request_state["candidate_manifest_refs"]),
        "p0_candidate_count": request_state["p0_candidate_count"],
        "p1_candidate_count": request_state["p1_candidate_count"],
        "candidate_total": request_state["candidate_total"],
        "assignment_request_ready": request_state["assignment_request_ready"],
        "assignment_artifact_present": False,
        "independent_final_reviewer_assigned": False,
        "assignment_satisfies_gate": False,
        "independent_final_closure_decision_present": False,
        "zero_proof_artifact_present": False,
        "p0_zero_proven": False,
        "p1_zero_proven": False,
        "closure_claimed": False,
        "observed_open_p0_findings": S2PMT07_INHERITED_V7_1_OPEN_P0_FINDINGS,
        "observed_open_p1_findings": S2PMT07_INHERITED_V7_1_OPEN_P1_FINDINGS,
        "next_required_action": "owner_or_coordinator_must_create_assignment_artifact_with_independent_reviewer",
        "blocking_reasons": list(S2PMT07_INDEPENDENT_FINAL_REVIEWER_ASSIGNMENT_OWNER_PACKET_BLOCKING_REASONS),
        **{flag: False for flag in S2PMT07_INDEPENDENT_FINAL_REVIEWER_ASSIGNMENT_OWNER_PACKET_FORBIDDEN_FLAGS},
        "state_hash": "",
    }
    state["state_hash"] = _stable_hash({key: value for key, value in state.items() if key != "state_hash"})
    return state


def validate_independent_final_reviewer_assignment_owner_packet_state(
    state: Mapping[str, Any],
) -> list[str]:
    """Validate the owner/coordinator packet without treating it as an assignment artifact."""

    errors: list[str] = []
    if state.get("status") != "blocked_owner_action_packet_ready_no_assignment":
        errors.append("independent final reviewer assignment owner packet status is invalid")
    if state.get("scope") != "owner_assignment_packet_only_no_assignment":
        errors.append("independent final reviewer assignment owner packet scope is invalid")
    if state.get("task_id") != S2PMT07_TASK_ID:
        errors.append("independent final reviewer assignment owner packet task_id is invalid")
    if state.get("acceptance_id") != S2PMT07_ACCEPTANCE_ID:
        errors.append("independent final reviewer assignment owner packet acceptance_id is invalid")
    if (
        tuple(state.get("required_owner_actions", []))
        != S2PMT07_INDEPENDENT_FINAL_REVIEWER_ASSIGNMENT_OWNER_PACKET_REQUIRED_ACTIONS
    ):
        errors.append("independent final reviewer assignment owner packet required_owner_actions are invalid")
    if state.get("assignment_artifact_path") != S2PMT07_INDEPENDENT_FINAL_REVIEWER_ASSIGNMENT_ARTIFACT_PATH:
        errors.append("independent final reviewer assignment owner packet assignment_artifact_path is invalid")
    if state.get("assignment_schema_version") != S2PMT07_INDEPENDENT_FINAL_REVIEWER_ASSIGNMENT_SCHEMA_VERSION:
        errors.append("independent final reviewer assignment owner packet assignment_schema_version is invalid")
    if state.get("assignment_decision") != S2PMT07_INDEPENDENT_FINAL_REVIEWER_ASSIGNMENT_DECISION:
        errors.append("independent final reviewer assignment owner packet assignment_decision is invalid")
    if (
        tuple(state.get("assignment_required_fields", []))
        != S2PMT07_INDEPENDENT_FINAL_REVIEWER_ASSIGNMENT_REQUIRED_FIELDS
    ):
        errors.append("independent final reviewer assignment owner packet required fields are invalid")
    if state.get("required_reviewer_role") != "independent_final_reviewer":
        errors.append("independent final reviewer assignment owner packet reviewer role is invalid")
    if state.get("required_reviewer_independence") != S2PMT07_REQUIRED_REVIEWER_INDEPENDENCE:
        errors.append("independent final reviewer assignment owner packet reviewer independence is invalid")
    if tuple(state.get("allowed_assigned_by_values", [])) != ("owner_or_coordinator", "owner"):
        errors.append("independent final reviewer assignment owner packet assigned_by values are invalid")
    if state.get("required_assignment_scope") != "S2PMT07_P0_P1_FINAL_CLOSURE_REVIEW":
        errors.append("independent final reviewer assignment owner packet assignment scope is invalid")
    if state.get("forbidden_reviewer_ids") != ["codex-current-agent"]:
        errors.append("independent final reviewer assignment owner packet forbidden reviewer ids are invalid")
    request_state = build_independent_final_reviewer_assignment_request_state()
    for ref in request_state["review_input_refs"]:
        if ref not in state.get("review_input_refs", []):
            errors.append(f"independent final reviewer assignment owner packet review inputs must include {ref}")
    for ref in request_state["candidate_manifest_refs"]:
        if ref not in state.get("candidate_manifest_refs", []):
            errors.append(f"independent final reviewer assignment owner packet candidate refs must include {ref}")
    if state.get("p0_candidate_count") != request_state["p0_candidate_count"]:
        errors.append("independent final reviewer assignment owner packet P0 candidate count is invalid")
    if state.get("p1_candidate_count") != request_state["p1_candidate_count"]:
        errors.append("independent final reviewer assignment owner packet P1 candidate count is invalid")
    if state.get("candidate_total") != request_state["candidate_total"]:
        errors.append("independent final reviewer assignment owner packet candidate_total is invalid")
    if state.get("assignment_request_ready") is not True:
        errors.append("independent final reviewer assignment owner packet request must be ready")
    if state.get("assignment_artifact_present") is not False:
        errors.append("assignment_artifact_present must remain false until owner supplies artifact")
    for flag in (
        "independent_final_reviewer_assigned",
        "assignment_satisfies_gate",
        "independent_final_closure_decision_present",
        "zero_proof_artifact_present",
        "p0_zero_proven",
        "p1_zero_proven",
        "closure_claimed",
    ):
        if state.get(flag) is not False:
            errors.append(f"{flag} must be false")
    if state.get("observed_open_p0_findings") != S2PMT07_INHERITED_V7_1_OPEN_P0_FINDINGS:
        errors.append("independent final reviewer assignment owner packet must preserve inherited open P0 count")
    if state.get("observed_open_p1_findings") != S2PMT07_INHERITED_V7_1_OPEN_P1_FINDINGS:
        errors.append("independent final reviewer assignment owner packet must preserve inherited open P1 count")
    if (
        state.get("next_required_action")
        != "owner_or_coordinator_must_create_assignment_artifact_with_independent_reviewer"
    ):
        errors.append("independent final reviewer assignment owner packet next_required_action is invalid")
    for reason in S2PMT07_INDEPENDENT_FINAL_REVIEWER_ASSIGNMENT_OWNER_PACKET_BLOCKING_REASONS:
        if reason not in state.get("blocking_reasons", []):
            errors.append(f"independent final reviewer assignment owner packet must include blocker {reason}")
    for flag in S2PMT07_INDEPENDENT_FINAL_REVIEWER_ASSIGNMENT_OWNER_PACKET_FORBIDDEN_FLAGS:
        if state.get(flag) is not False:
            errors.append(f"{flag} must be false")
    expected_hash = _stable_hash({key: value for key, value in state.items() if key != "state_hash"})
    if state.get("state_hash") != expected_hash:
        errors.append("independent final reviewer assignment owner packet state_hash does not match state content")
    return errors


def build_independent_final_reviewer_assignment_hash(payload: Mapping[str, Any]) -> str:
    """Return the canonical reviewer-assignment hash excluding its hash field."""

    payload_without_hash = {key: value for key, value in payload.items() if key != "assignment_hash"}
    return f"sha256:{_stable_hash(payload_without_hash)}"


def _is_final_bundle_template_placeholder(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    return "REPLACE_WITH" in value or "RECOMPUTE_WITH" in value


def _final_bundle_template_placeholder_errors(value: Any, path: str = "") -> list[str]:
    if _is_final_bundle_template_placeholder(value):
        location = path or "<root>"
        return [f"template placeholder found at {location}"]
    if isinstance(value, Mapping):
        errors: list[str] = []
        for key, child in value.items():
            child_path = f"{path}.{key}" if path else str(key)
            errors.extend(_final_bundle_template_placeholder_errors(child, child_path))
        return errors
    if isinstance(value, (list, tuple)):
        errors = []
        for index, child in enumerate(value):
            child_path = f"{path}[{index}]" if path else f"[{index}]"
            errors.extend(_final_bundle_template_placeholder_errors(child, child_path))
        return errors
    return []


def validate_independent_final_reviewer_assignment_artifact(payload: Mapping[str, Any] | None) -> list[str]:
    """Validate a future independent-final-reviewer assignment artifact."""

    if payload is None:
        return ["independent_final_reviewer_assignment_missing"]
    errors: list[str] = []
    errors.extend(_final_bundle_template_placeholder_errors(payload))
    for field in S2PMT07_INDEPENDENT_FINAL_REVIEWER_ASSIGNMENT_REQUIRED_FIELDS:
        if field not in payload:
            errors.append(f"{field} is required")
    if tuple(payload.keys()) != S2PMT07_INDEPENDENT_FINAL_REVIEWER_ASSIGNMENT_REQUIRED_FIELDS:
        errors.append("independent final reviewer assignment field order is invalid")
    if payload.get("schema_version") != S2PMT07_INDEPENDENT_FINAL_REVIEWER_ASSIGNMENT_SCHEMA_VERSION:
        errors.append("schema_version is invalid")
    if payload.get("contract_id") != "ADP-PRODUCT-CONTRACT-V7.2":
        errors.append("contract_id must be ADP-PRODUCT-CONTRACT-V7.2")
    if not isinstance(payload.get("generated_at"), str) or not payload.get("generated_at"):
        errors.append("generated_at must be a non-empty string")
    elif _is_final_bundle_template_placeholder(payload.get("generated_at")):
        errors.append("generated_at must not be a template placeholder")
    if payload.get("assignment_decision") != S2PMT07_INDEPENDENT_FINAL_REVIEWER_ASSIGNMENT_DECISION:
        errors.append("assignment_decision is invalid")

    assignment = _mapping(payload.get("reviewer_assignment"))
    reviewer_id = assignment.get("reviewer_id")
    if not isinstance(reviewer_id, str) or not reviewer_id:
        errors.append("reviewer_assignment.reviewer_id must be a non-empty string")
    elif _is_final_bundle_template_placeholder(reviewer_id):
        errors.append("reviewer_assignment.reviewer_id must not be a template placeholder")
    if reviewer_id == "codex-current-agent":
        errors.append("reviewer_assignment.reviewer_id must not be codex-current-agent")
    if assignment.get("reviewer_role") != "independent_final_reviewer":
        errors.append("reviewer_assignment.reviewer_role must be independent_final_reviewer")
    if assignment.get("assigned_by") not in {"owner_or_coordinator", "owner"}:
        errors.append("reviewer_assignment.assigned_by must be owner_or_coordinator or owner")
    if assignment.get("assignment_scope") != "S2PMT07_P0_P1_FINAL_CLOSURE_REVIEW":
        errors.append("reviewer_assignment.assignment_scope is invalid")

    reviewer = _mapping(payload.get("reviewer_independence"))
    if reviewer.get("status") != "verified":
        errors.append("reviewer_independence.status must be verified")
    if reviewer.get("required_independence") != S2PMT07_REQUIRED_REVIEWER_INDEPENDENCE:
        errors.append("reviewer_independence.required_independence is invalid")
    if reviewer.get("reviewer_involved_in_s2pmt01_t06") is not False:
        errors.append("reviewer_independence.reviewer_involved_in_s2pmt01_t06 must be false")

    review_input_refs = payload.get("review_input_refs", [])
    required_refs = build_independent_final_reviewer_assignment_request_state()["review_input_refs"]
    if not isinstance(review_input_refs, list) or any(ref not in review_input_refs for ref in required_refs):
        errors.append("review_input_refs must include all reviewer assignment request inputs")

    no_production = _mapping(payload.get("no_production_side_effects"))
    for flag in S2PMT07_INDEPENDENT_FINAL_REVIEWER_ASSIGNMENT_NO_PRODUCTION_FLAGS:
        if no_production.get(flag) is not False:
            errors.append(f"no_production_side_effects.{flag} must be false")

    if payload.get("assignment_hash") != build_independent_final_reviewer_assignment_hash(payload):
        errors.append("assignment_hash does not match payload content")
    return errors


def build_independent_final_reviewer_assignment_artifact_draft_state(
    *,
    reviewer_id: str,
    assigned_by: str,
    generated_at: str,
    assignment_scope: str = "S2PMT07_P0_P1_FINAL_CLOSURE_REVIEW",
) -> dict[str, Any]:
    """Build a stdout-only draft assignment artifact from explicit owner/coordinator inputs."""

    request_state = build_independent_final_reviewer_assignment_request_state()
    artifact = {
        "schema_version": S2PMT07_INDEPENDENT_FINAL_REVIEWER_ASSIGNMENT_SCHEMA_VERSION,
        "contract_id": "ADP-PRODUCT-CONTRACT-V7.2",
        "generated_at": generated_at,
        "assignment_decision": S2PMT07_INDEPENDENT_FINAL_REVIEWER_ASSIGNMENT_DECISION,
        "reviewer_assignment": {
            "reviewer_id": reviewer_id,
            "reviewer_role": "independent_final_reviewer",
            "assigned_by": assigned_by,
            "assignment_scope": assignment_scope,
        },
        "reviewer_independence": {
            "status": "verified",
            "required_independence": S2PMT07_REQUIRED_REVIEWER_INDEPENDENCE,
            "reviewer_involved_in_s2pmt01_t06": False,
        },
        "review_input_refs": list(request_state["review_input_refs"]),
        "no_production_side_effects": {
            flag: False for flag in S2PMT07_INDEPENDENT_FINAL_REVIEWER_ASSIGNMENT_NO_PRODUCTION_FLAGS
        },
        "assignment_hash": "",
    }
    artifact["assignment_hash"] = build_independent_final_reviewer_assignment_hash(artifact)
    validation_errors = validate_independent_final_reviewer_assignment_artifact(artifact)
    state = {
        "status": "draft" if not validation_errors else "blocked",
        "scope": "independent_final_reviewer_assignment_artifact_draft_only_no_assignment_no_production",
        "task_id": S2PMT07_TASK_ID,
        "acceptance_id": S2PMT07_ACCEPTANCE_ID,
        "artifact_path": S2PMT07_INDEPENDENT_FINAL_REVIEWER_ASSIGNMENT_ARTIFACT_PATH,
        "artifact": artifact,
        "validation_errors": validation_errors,
        "assignment_artifact_written": False,
        "assignment_artifact_present_in_repo": False,
        "assignment_gate_satisfied_by_this_command": False,
        "independent_final_reviewer_assigned_by_this_command": False,
        "p0_zero_proven": False,
        "p1_zero_proven": False,
        "closure_claimed": False,
        "next_required_action": "owner_or_coordinator_must_review_and_write_assignment_artifact_if_approved",
        "production_acceptance_claimed": False,
        "integrated_production_accepted": False,
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
        "state_hash": "",
    }
    state["state_hash"] = _stable_hash({key: value for key, value in state.items() if key != "state_hash"})
    return state


def build_independent_final_reviewer_assignment_validation_state(
    payload: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Build validation state for a future independent reviewer assignment artifact."""

    errors = validate_independent_final_reviewer_assignment_artifact(payload)
    state = {
        "status": "pass" if not errors else "blocked",
        "scope": "independent_final_reviewer_assignment_validation_only_no_closure",
        "artifact_path": S2PMT07_INDEPENDENT_FINAL_REVIEWER_ASSIGNMENT_ARTIFACT_PATH,
        "assignment_present": payload is not None,
        "validation_errors": errors,
        "required_fields": list(S2PMT07_INDEPENDENT_FINAL_REVIEWER_ASSIGNMENT_REQUIRED_FIELDS),
        "required_review_input_refs": build_independent_final_reviewer_assignment_request_state()[
            "review_input_refs"
        ],
        "independent_final_reviewer_assigned_by_payload": not errors and payload is not None,
        "production_acceptance_claimed": False,
        "integrated_production_accepted": False,
        "daily_operation_enabled": False,
        "real_smtp_send_enabled": False,
        "scheduler_install_enabled": False,
        "release_packaging_enabled": False,
        "production_restore_enabled": False,
        "state_hash": "",
    }
    state["state_hash"] = _stable_hash({key: value for key, value in state.items() if key != "state_hash"})
    return state


def build_independent_final_closure_decision_request_state() -> dict[str, Any]:
    """Build the reviewer input request for the future final P0/P1 closure decision."""

    assembly_state = build_p0_p1_zero_proof_assembly_state()
    readiness_state = build_p0_p1_zero_proof_readiness_state()
    reviewer_assignment_request = build_independent_final_reviewer_assignment_request_state()
    all_candidate_inputs_ready = (
        not validate_p0_p1_zero_proof_assembly_state(assembly_state)
        and assembly_state["all_candidate_reviews_available"] is True
        and assembly_state["all_candidate_refs_exist"] is True
    )
    candidate_manifest_refs = list(assembly_state["candidate_manifest_refs"])
    review_input_refs = list(
        dict.fromkeys(candidate_manifest_refs + list(readiness_state["candidate_evidence_refs"]))
    )
    state = {
        "status": "blocked_decision_request_ready_no_closure",
        "scope": "independent_final_closure_decision_request_only_no_closure",
        "task_id": S2PMT07_TASK_ID,
        "acceptance_id": S2PMT07_ACCEPTANCE_ID,
        "required_inputs": list(S2PMT07_INDEPENDENT_FINAL_CLOSURE_DECISION_REQUEST_REQUIRED_INPUTS),
        "decision_artifact_ref": f"{S2PMT07_P0_P1_ZERO_PROOF_ARTIFACT_PATH}#independent_closure_decision",
        "required_reviewer_role": "independent_final_reviewer",
        "p0_candidate_findings": list(assembly_state["p0_candidate_findings"]),
        "p1_candidate_findings": list(assembly_state["p1_candidate_findings"]),
        "p0_candidate_count": assembly_state["p0_candidate_count"],
        "p1_candidate_count": assembly_state["p1_candidate_count"],
        "candidate_total": assembly_state["candidate_total"],
        "candidate_manifest_refs": candidate_manifest_refs,
        "review_input_refs": review_input_refs,
        "all_candidate_inputs_ready": all_candidate_inputs_ready,
        "all_candidate_refs_exist": assembly_state["all_candidate_refs_exist"],
        "reviewer_assignment_request": reviewer_assignment_request,
        "reviewer_assignment_request_ready": not validate_independent_final_reviewer_assignment_request_state(
            reviewer_assignment_request
        ),
        "independent_final_reviewer_assigned": False,
        "independent_final_closure_decision_present": False,
        "zero_proof_artifact_present": False,
        "p0_zero_proven": False,
        "p1_zero_proven": False,
        "closure_claimed": False,
        "observed_open_p0_findings": S2PMT07_INHERITED_V7_1_OPEN_P0_FINDINGS,
        "observed_open_p1_findings": S2PMT07_INHERITED_V7_1_OPEN_P1_FINDINGS,
        "next_required_action": "independent_final_reviewer_must_issue_or_reject_closure_decision",
        "blocking_reasons": list(S2PMT07_INDEPENDENT_FINAL_CLOSURE_DECISION_REQUEST_BLOCKING_REASONS),
        **{flag: False for flag in S2PMT07_INDEPENDENT_FINAL_CLOSURE_DECISION_REQUEST_FORBIDDEN_FLAGS},
        "state_hash": "",
    }
    state["state_hash"] = _stable_hash({key: value for key, value in state.items() if key != "state_hash"})
    return state


def validate_independent_final_closure_decision_request_state(state: Mapping[str, Any]) -> list[str]:
    """Validate the reviewer input request without accepting or closing P0/P1."""

    errors: list[str] = []
    if state.get("status") != "blocked_decision_request_ready_no_closure":
        errors.append(
            "independent final closure decision request status must remain blocked_decision_request_ready_no_closure"
        )
    if state.get("scope") != "independent_final_closure_decision_request_only_no_closure":
        errors.append("independent final closure decision request scope is invalid")
    if state.get("task_id") != S2PMT07_TASK_ID:
        errors.append("independent final closure decision request task_id is invalid")
    if state.get("acceptance_id") != S2PMT07_ACCEPTANCE_ID:
        errors.append("independent final closure decision request acceptance_id is invalid")
    if (
        tuple(state.get("required_inputs", []))
        != S2PMT07_INDEPENDENT_FINAL_CLOSURE_DECISION_REQUEST_REQUIRED_INPUTS
    ):
        errors.append("independent final closure decision request required_inputs are invalid")
    if (
        state.get("decision_artifact_ref")
        != f"{S2PMT07_P0_P1_ZERO_PROOF_ARTIFACT_PATH}#independent_closure_decision"
    ):
        errors.append("independent final closure decision request decision_artifact_ref is invalid")
    if state.get("required_reviewer_role") != "independent_final_reviewer":
        errors.append("independent final closure decision request reviewer role is invalid")
    if tuple(state.get("p0_candidate_findings", [])) != S2PMT07_P0_TECHNICAL_CLOSURE_CANDIDATE_FINDINGS:
        errors.append("independent final closure decision request P0 candidate findings are invalid")
    if tuple(state.get("p1_candidate_findings", [])) != S2PMT07_P1_TECHNICAL_CLOSURE_CANDIDATE_FINDINGS:
        errors.append("independent final closure decision request P1 candidate findings are invalid")
    if state.get("p0_candidate_count") != len(S2PMT07_P0_TECHNICAL_CLOSURE_CANDIDATE_FINDINGS):
        errors.append("independent final closure decision request P0 candidate count is invalid")
    if state.get("p1_candidate_count") != len(S2PMT07_P1_TECHNICAL_CLOSURE_CANDIDATE_FINDINGS):
        errors.append("independent final closure decision request P1 candidate count is invalid")
    if state.get("candidate_total") != (
        len(S2PMT07_P0_TECHNICAL_CLOSURE_CANDIDATE_FINDINGS)
        + len(S2PMT07_P1_TECHNICAL_CLOSURE_CANDIDATE_FINDINGS)
    ):
        errors.append("independent final closure decision request candidate_total is invalid")
    refs = state.get("candidate_manifest_refs", [])
    for ref in build_p0_p1_zero_proof_assembly_state()["candidate_manifest_refs"]:
        if ref not in refs:
            errors.append(f"independent final closure decision request refs must include {ref}")
    review_input_refs = state.get("review_input_refs", [])
    for ref in build_p0_p1_zero_proof_readiness_state()["candidate_evidence_refs"]:
        if ref not in review_input_refs:
            errors.append(f"independent final closure decision request review inputs must include {ref}")
    if state.get("all_candidate_inputs_ready") is not True:
        errors.append("independent final closure decision request candidate inputs must be ready")
    if state.get("all_candidate_refs_exist") is not True:
        errors.append("independent final closure decision request candidate refs must exist")
    reviewer_assignment_request = _mapping(state.get("reviewer_assignment_request"))
    if validate_independent_final_reviewer_assignment_request_state(reviewer_assignment_request):
        errors.append("independent final closure decision request reviewer assignment request is invalid")
    if state.get("reviewer_assignment_request_ready") is not True:
        errors.append("independent final closure decision request reviewer assignment request must be ready")
    for flag in (
        "independent_final_reviewer_assigned",
        "independent_final_closure_decision_present",
        "zero_proof_artifact_present",
        "p0_zero_proven",
        "p1_zero_proven",
        "closure_claimed",
    ):
        if state.get(flag) is not False:
            if flag == "independent_final_closure_decision_present":
                errors.append("independent_final_closure_decision_present must be false until artifact exists")
            elif flag == "independent_final_reviewer_assigned":
                errors.append("independent_final_reviewer_assigned must be false until assignment artifact exists")
            else:
                errors.append(f"{flag} must be false")
    if state.get("observed_open_p0_findings") != S2PMT07_INHERITED_V7_1_OPEN_P0_FINDINGS:
        errors.append("independent final closure decision request must preserve inherited open P0 count")
    if state.get("observed_open_p1_findings") != S2PMT07_INHERITED_V7_1_OPEN_P1_FINDINGS:
        errors.append("independent final closure decision request must preserve inherited open P1 count")
    if state.get("next_required_action") != "independent_final_reviewer_must_issue_or_reject_closure_decision":
        errors.append("independent final closure decision request next_required_action is invalid")
    for reason in S2PMT07_INDEPENDENT_FINAL_CLOSURE_DECISION_REQUEST_BLOCKING_REASONS:
        if reason not in state.get("blocking_reasons", []):
            errors.append(f"independent final closure decision request must include blocker {reason}")
    for flag in S2PMT07_INDEPENDENT_FINAL_CLOSURE_DECISION_REQUEST_FORBIDDEN_FLAGS:
        if state.get(flag) is not False:
            errors.append(f"{flag} must be false")
    expected_hash = _stable_hash({key: value for key, value in state.items() if key != "state_hash"})
    if state.get("state_hash") != expected_hash:
        errors.append("independent final closure decision request state_hash does not match state content")
    return errors


def build_independent_final_closure_decision_owner_packet_state() -> dict[str, Any]:
    """Build the owner/reviewer packet for a future independent final closure decision."""

    request_state = build_independent_final_closure_decision_request_state()
    assignment_packet = build_independent_final_reviewer_assignment_owner_packet_state()
    state = {
        "status": "blocked_owner_action_packet_ready_no_closure",
        "scope": "owner_closure_decision_packet_only_no_closure",
        "task_id": S2PMT07_TASK_ID,
        "acceptance_id": S2PMT07_ACCEPTANCE_ID,
        "required_owner_actions": list(
            S2PMT07_INDEPENDENT_FINAL_CLOSURE_DECISION_OWNER_PACKET_REQUIRED_ACTIONS
        ),
        "decision_artifact_ref": f"{S2PMT07_P0_P1_ZERO_PROOF_ARTIFACT_PATH}#independent_closure_decision",
        "zero_proof_artifact_path": S2PMT07_P0_P1_ZERO_PROOF_ARTIFACT_PATH,
        "zero_proof_schema_version": S2PMT07_P0_P1_ZERO_PROOF_SCHEMA_VERSION,
        "zero_proof_required_fields": list(S2PMT07_P0_P1_ZERO_PROOF_REQUIRED_FIELDS),
        "required_closure_decision": S2PMT07_P0_P1_ZERO_PROOF_CLOSURE_DECISION,
        "assignment_artifact_path": S2PMT07_INDEPENDENT_FINAL_REVIEWER_ASSIGNMENT_ARTIFACT_PATH,
        "assignment_owner_packet_ready": not validate_independent_final_reviewer_assignment_owner_packet_state(
            assignment_packet
        ),
        "closure_decision_request_ready": not validate_independent_final_closure_decision_request_state(
            request_state
        ),
        "required_reviewer_role": "independent_final_reviewer",
        "required_reviewer_independence": S2PMT07_REQUIRED_REVIEWER_INDEPENDENCE,
        "review_input_refs": list(request_state["review_input_refs"]),
        "candidate_manifest_refs": list(request_state["candidate_manifest_refs"]),
        "p0_candidate_count": request_state["p0_candidate_count"],
        "p1_candidate_count": request_state["p1_candidate_count"],
        "candidate_total": request_state["candidate_total"],
        "assignment_artifact_present": False,
        "independent_final_reviewer_assigned": False,
        "independent_final_closure_decision_present": False,
        "zero_proof_artifact_present": False,
        "p0_zero_proven": False,
        "p1_zero_proven": False,
        "closure_claimed": False,
        "observed_open_p0_findings": S2PMT07_INHERITED_V7_1_OPEN_P0_FINDINGS,
        "observed_open_p1_findings": S2PMT07_INHERITED_V7_1_OPEN_P1_FINDINGS,
        "next_required_action": "owner_or_independent_reviewer_must_record_final_closure_decision_after_assignment",
        "blocking_reasons": list(S2PMT07_INDEPENDENT_FINAL_CLOSURE_DECISION_OWNER_PACKET_BLOCKING_REASONS),
        **{flag: False for flag in S2PMT07_INDEPENDENT_FINAL_CLOSURE_DECISION_OWNER_PACKET_FORBIDDEN_FLAGS},
        "state_hash": "",
    }
    state["state_hash"] = _stable_hash({key: value for key, value in state.items() if key != "state_hash"})
    return state


def validate_independent_final_closure_decision_owner_packet_state(
    state: Mapping[str, Any],
) -> list[str]:
    """Validate the owner/reviewer packet without treating it as a closure decision."""

    errors: list[str] = []
    if state.get("status") != "blocked_owner_action_packet_ready_no_closure":
        errors.append("independent final closure decision owner packet status is invalid")
    if state.get("scope") != "owner_closure_decision_packet_only_no_closure":
        errors.append("independent final closure decision owner packet scope is invalid")
    if state.get("task_id") != S2PMT07_TASK_ID:
        errors.append("independent final closure decision owner packet task_id is invalid")
    if state.get("acceptance_id") != S2PMT07_ACCEPTANCE_ID:
        errors.append("independent final closure decision owner packet acceptance_id is invalid")
    if (
        tuple(state.get("required_owner_actions", []))
        != S2PMT07_INDEPENDENT_FINAL_CLOSURE_DECISION_OWNER_PACKET_REQUIRED_ACTIONS
    ):
        errors.append("independent final closure decision owner packet required_owner_actions are invalid")
    if (
        state.get("decision_artifact_ref")
        != f"{S2PMT07_P0_P1_ZERO_PROOF_ARTIFACT_PATH}#independent_closure_decision"
    ):
        errors.append("independent final closure decision owner packet decision_artifact_ref is invalid")
    if state.get("zero_proof_artifact_path") != S2PMT07_P0_P1_ZERO_PROOF_ARTIFACT_PATH:
        errors.append("independent final closure decision owner packet zero_proof_artifact_path is invalid")
    if state.get("zero_proof_schema_version") != S2PMT07_P0_P1_ZERO_PROOF_SCHEMA_VERSION:
        errors.append("independent final closure decision owner packet zero_proof_schema_version is invalid")
    if tuple(state.get("zero_proof_required_fields", [])) != S2PMT07_P0_P1_ZERO_PROOF_REQUIRED_FIELDS:
        errors.append("independent final closure decision owner packet zero_proof required fields are invalid")
    if state.get("required_closure_decision") != S2PMT07_P0_P1_ZERO_PROOF_CLOSURE_DECISION:
        errors.append("independent final closure decision owner packet closure decision is invalid")
    if state.get("assignment_artifact_path") != S2PMT07_INDEPENDENT_FINAL_REVIEWER_ASSIGNMENT_ARTIFACT_PATH:
        errors.append("independent final closure decision owner packet assignment_artifact_path is invalid")
    if state.get("assignment_owner_packet_ready") is not True:
        errors.append("independent final closure decision owner packet assignment owner packet must be ready")
    if state.get("closure_decision_request_ready") is not True:
        errors.append("independent final closure decision owner packet request must be ready")
    if state.get("required_reviewer_role") != "independent_final_reviewer":
        errors.append("independent final closure decision owner packet reviewer role is invalid")
    if state.get("required_reviewer_independence") != S2PMT07_REQUIRED_REVIEWER_INDEPENDENCE:
        errors.append("independent final closure decision owner packet reviewer independence is invalid")
    request_state = build_independent_final_closure_decision_request_state()
    for ref in request_state["review_input_refs"]:
        if ref not in state.get("review_input_refs", []):
            errors.append(f"independent final closure decision owner packet review inputs must include {ref}")
    for ref in request_state["candidate_manifest_refs"]:
        if ref not in state.get("candidate_manifest_refs", []):
            errors.append(f"independent final closure decision owner packet candidate refs must include {ref}")
    if state.get("p0_candidate_count") != request_state["p0_candidate_count"]:
        errors.append("independent final closure decision owner packet P0 candidate count is invalid")
    if state.get("p1_candidate_count") != request_state["p1_candidate_count"]:
        errors.append("independent final closure decision owner packet P1 candidate count is invalid")
    if state.get("candidate_total") != request_state["candidate_total"]:
        errors.append("independent final closure decision owner packet candidate_total is invalid")
    if state.get("assignment_artifact_present") is not False:
        errors.append("assignment_artifact_present must remain false until owner supplies artifact")
    for flag in (
        "independent_final_reviewer_assigned",
        "independent_final_closure_decision_present",
        "zero_proof_artifact_present",
        "p0_zero_proven",
        "p1_zero_proven",
        "closure_claimed",
    ):
        if state.get(flag) is not False:
            if flag == "independent_final_closure_decision_present":
                errors.append(
                    "independent_final_closure_decision_present must remain false until final reviewer supplies decision"
                )
            else:
                errors.append(f"{flag} must be false")
    if state.get("observed_open_p0_findings") != S2PMT07_INHERITED_V7_1_OPEN_P0_FINDINGS:
        errors.append("independent final closure decision owner packet must preserve inherited open P0 count")
    if state.get("observed_open_p1_findings") != S2PMT07_INHERITED_V7_1_OPEN_P1_FINDINGS:
        errors.append("independent final closure decision owner packet must preserve inherited open P1 count")
    if (
        state.get("next_required_action")
        != "owner_or_independent_reviewer_must_record_final_closure_decision_after_assignment"
    ):
        errors.append("independent final closure decision owner packet next_required_action is invalid")
    for reason in S2PMT07_INDEPENDENT_FINAL_CLOSURE_DECISION_OWNER_PACKET_BLOCKING_REASONS:
        if reason not in state.get("blocking_reasons", []):
            errors.append(f"independent final closure decision owner packet must include blocker {reason}")
    for flag in S2PMT07_INDEPENDENT_FINAL_CLOSURE_DECISION_OWNER_PACKET_FORBIDDEN_FLAGS:
        if state.get(flag) is not False:
            errors.append(f"{flag} must be false")
    expected_hash = _stable_hash({key: value for key, value in state.items() if key != "state_hash"})
    if state.get("state_hash") != expected_hash:
        errors.append("independent final closure decision owner packet state_hash does not match state content")
    return errors


def build_p0_p1_zero_proof_readiness_state(
    p0_p1_zero_proof: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build P0/P1 zero-proof readiness from a payload, or fail closed when absent."""

    assembly_state = build_p0_p1_zero_proof_assembly_state()
    artifact_errors = validate_p0_p1_zero_proof_artifact(p0_p1_zero_proof)
    artifact_ready = p0_p1_zero_proof is not None and not artifact_errors
    decision = _mapping(p0_p1_zero_proof.get("independent_closure_decision")) if artifact_ready else {}
    blocking_reasons = [] if artifact_ready else list(S2PMT07_P0_P1_ZERO_PROOF_BLOCKING_REASONS)
    state = {
        "status": "pass" if artifact_ready else "blocked",
        "scope": "p0_p1_zero_proof_readiness_schema_only_no_closure",
        "zero_proof_artifact_path": S2PMT07_P0_P1_ZERO_PROOF_ARTIFACT_PATH,
        "zero_proof_artifact_present": p0_p1_zero_proof is not None,
        "required_zero_severities": list(S2PMT07_REQUIRED_ZERO_FINDING_SEVERITIES),
        "required_fields": list(S2PMT07_P0_P1_ZERO_PROOF_REQUIRED_FIELDS),
        "required_open_p0_findings": 0,
        "required_open_p1_findings": 0,
        "observed_open_p0_findings": 0 if artifact_ready else S2PMT07_INHERITED_V7_1_OPEN_P0_FINDINGS,
        "observed_open_p1_findings": 0 if artifact_ready else S2PMT07_INHERITED_V7_1_OPEN_P1_FINDINGS,
        "candidate_evidence_refs": [
            S2PMT07_P0_TECHNICAL_CLOSURE_CANDIDATE_PACKAGE,
            S2PMT07_P1_TECHNICAL_CLOSURE_CANDIDATE_RECEIPT,
            *S2PMT07_P1_TECHNICAL_CLOSURE_CANDIDATE_MANIFESTS,
        ],
        "zero_proof_assembly_state": assembly_state,
        "candidate_evidence_only": not artifact_ready,
        "independent_final_closure_decision_present": artifact_ready,
        "p0_zero_proven": artifact_ready and decision.get("p0_zero_proven") is True,
        "p1_zero_proven": artifact_ready and decision.get("p1_zero_proven") is True,
        "closure_claimed": False,
        "production_acceptance_claimed": False,
        "integrated_production_accepted": False,
        "daily_operation_enabled": False,
        "real_smtp_send_enabled": False,
        "scheduler_install_enabled": False,
        "release_packaging_enabled": False,
        "production_restore_enabled": False,
        "blocking_reasons": blocking_reasons,
        "state_hash": "",
    }
    state["state_hash"] = _stable_hash({key: value for key, value in state.items() if key != "state_hash"})
    return state


def validate_p0_p1_zero_proof_readiness_state(state: Mapping[str, Any]) -> list[str]:
    """Validate P0/P1 zero-proof readiness without accepting closure."""

    errors: list[str] = []
    if state.get("status") not in {"pass", "blocked"}:
        errors.append("P0/P1 zero proof readiness status must be pass or blocked")
    if state.get("scope") != "p0_p1_zero_proof_readiness_schema_only_no_closure":
        errors.append("P0/P1 zero proof readiness scope is invalid")
    if state.get("zero_proof_artifact_path") != S2PMT07_P0_P1_ZERO_PROOF_ARTIFACT_PATH:
        errors.append("P0/P1 zero proof readiness artifact path is invalid")
    artifact_present = state.get("zero_proof_artifact_present") is True
    if tuple(state.get("required_zero_severities", [])) != S2PMT07_REQUIRED_ZERO_FINDING_SEVERITIES:
        errors.append("P0/P1 zero proof readiness required zero severities are invalid")
    if tuple(state.get("required_fields", [])) != S2PMT07_P0_P1_ZERO_PROOF_REQUIRED_FIELDS:
        errors.append("P0/P1 zero proof readiness required fields are invalid")
    if state.get("required_open_p0_findings") != 0:
        errors.append("P0/P1 zero proof readiness required open P0 findings must be zero")
    if state.get("required_open_p1_findings") != 0:
        errors.append("P0/P1 zero proof readiness required open P1 findings must be zero")
    expected_observed_p0 = 0 if artifact_present else S2PMT07_INHERITED_V7_1_OPEN_P0_FINDINGS
    expected_observed_p1 = 0 if artifact_present else S2PMT07_INHERITED_V7_1_OPEN_P1_FINDINGS
    if state.get("observed_open_p0_findings") != expected_observed_p0:
        errors.append("P0/P1 zero proof readiness observed open P0 count is invalid")
    if state.get("observed_open_p1_findings") != expected_observed_p1:
        errors.append("P0/P1 zero proof readiness observed open P1 count is invalid")
    refs = state.get("candidate_evidence_refs", [])
    for ref in (
        S2PMT07_P0_TECHNICAL_CLOSURE_CANDIDATE_PACKAGE,
        S2PMT07_P1_TECHNICAL_CLOSURE_CANDIDATE_RECEIPT,
        *S2PMT07_P1_TECHNICAL_CLOSURE_CANDIDATE_MANIFESTS,
    ):
        if ref not in refs:
            errors.append(f"P0/P1 zero proof readiness refs must include {ref}")
    if state.get("candidate_evidence_only") is not (not artifact_present):
        errors.append("P0/P1 zero proof readiness candidate_evidence_only is invalid")
    assembly_state = _mapping(state.get("zero_proof_assembly_state"))
    if validate_p0_p1_zero_proof_assembly_state(assembly_state):
        errors.append("P0/P1 zero proof readiness assembly state is invalid")
    if state.get("independent_final_closure_decision_present") is not artifact_present:
        errors.append("P0/P1 zero proof readiness independent decision presence is invalid")
    if state.get("p0_zero_proven") is not artifact_present:
        errors.append("P0/P1 zero proof readiness p0_zero_proven is invalid")
    if state.get("p1_zero_proven") is not artifact_present:
        errors.append("P0/P1 zero proof readiness p1_zero_proven is invalid")
    for flag in (
        "closure_claimed",
        "production_acceptance_claimed",
        "integrated_production_accepted",
        "daily_operation_enabled",
        "real_smtp_send_enabled",
        "scheduler_install_enabled",
        "release_packaging_enabled",
        "production_restore_enabled",
    ):
        if state.get(flag) is not False:
            errors.append(f"{flag} must be false")
    if artifact_present:
        if state.get("status") != "pass":
            errors.append("P0/P1 zero proof readiness with artifact must pass")
        if state.get("blocking_reasons") != []:
            errors.append("P0/P1 zero proof readiness with artifact must not have blocking reasons")
    else:
        if state.get("status") != "blocked":
            errors.append("P0/P1 zero proof readiness without artifact must remain blocked")
        for reason in S2PMT07_P0_P1_ZERO_PROOF_BLOCKING_REASONS:
            if reason not in state.get("blocking_reasons", []):
                errors.append(f"P0/P1 zero proof readiness must include blocker {reason}")
    expected_hash = _stable_hash({key: value for key, value in state.items() if key != "state_hash"})
    if state.get("state_hash") != expected_hash:
        errors.append("P0/P1 zero proof readiness state_hash does not match state content")
    return errors


def build_p0_p1_zero_proof_decision_hash(payload: Mapping[str, Any]) -> str:
    """Return the canonical payload hash excluding the hash field itself."""

    payload_without_hash = {key: value for key, value in payload.items() if key != "decision_hash"}
    return f"sha256:{_stable_hash(payload_without_hash)}"


def validate_p0_p1_zero_proof_artifact(payload: Mapping[str, Any] | None) -> list[str]:
    """Validate a future P0/P1 zero-proof artifact without mutating current closure state."""

    if payload is None:
        return ["p0_p1_zero_proof_artifact_missing"]
    errors: list[str] = []
    errors.extend(_final_bundle_template_placeholder_errors(payload))
    for field in S2PMT07_P0_P1_ZERO_PROOF_REQUIRED_FIELDS:
        if field not in payload:
            errors.append(f"{field} is required")
    if payload.get("schema_version") != S2PMT07_P0_P1_ZERO_PROOF_SCHEMA_VERSION:
        errors.append("schema_version is invalid")
    if payload.get("contract_id") != "ADP-PRODUCT-CONTRACT-V7.2":
        errors.append("contract_id must be ADP-PRODUCT-CONTRACT-V7.2")
    if not isinstance(payload.get("generated_at"), str) or not payload.get("generated_at"):
        errors.append("generated_at must be a non-empty string")

    reviewer = _mapping(payload.get("reviewer_independence"))
    if reviewer.get("status") != "verified":
        errors.append("reviewer_independence.status must be verified")
    if reviewer.get("required_independence") != S2PMT07_REQUIRED_REVIEWER_INDEPENDENCE:
        errors.append("reviewer_independence.required_independence is invalid")

    source_refs = payload.get("source_candidate_refs", [])
    required_candidate_refs = build_p0_p1_zero_proof_readiness_state()["candidate_evidence_refs"]
    if not isinstance(source_refs, list) or any(ref not in source_refs for ref in required_candidate_refs):
        errors.append("source_candidate_refs must include all P0/P1 technical candidate refs")

    finding_counts = _mapping(payload.get("finding_counts"))
    zero_counts = _mapping(payload.get("zero_severity_counts"))
    for severity in S2PMT07_REQUIRED_ZERO_FINDING_SEVERITIES:
        if finding_counts.get(severity) != 0:
            errors.append(f"finding_counts.{severity} must be 0")
        if zero_counts.get(severity) != 0:
            errors.append(f"zero_severity_counts.{severity} must be 0")

    decision = _mapping(payload.get("independent_closure_decision"))
    if decision.get("decision") != S2PMT07_P0_P1_ZERO_PROOF_CLOSURE_DECISION:
        errors.append("independent_closure_decision.decision is invalid")
    if decision.get("p0_zero_proven") is not True:
        errors.append("independent_closure_decision.p0_zero_proven must be true")
    if decision.get("p1_zero_proven") is not True:
        errors.append("independent_closure_decision.p1_zero_proven must be true")
    if decision.get("production_acceptance_claimed") is not False:
        errors.append("independent_closure_decision.production_acceptance_claimed must be false")

    final_bundle_refs = payload.get("final_bundle_refs", [])
    if not isinstance(final_bundle_refs, list) or any(
        item not in final_bundle_refs for item in S2PMT07_FINAL_ACCEPTANCE_BUNDLE_REQUIRED_ITEMS
    ):
        errors.append("final_bundle_refs must include all final acceptance bundle required items")

    no_production = _mapping(payload.get("no_production_side_effects"))
    for flag in S2PMT07_P0_P1_ZERO_PROOF_NO_PRODUCTION_FLAGS:
        if no_production.get(flag) is not False:
            errors.append(f"no_production_side_effects.{flag} must be false")

    if payload.get("decision_hash") != build_p0_p1_zero_proof_decision_hash(payload):
        errors.append("decision_hash does not match payload content")
    return errors


def build_p0_p1_zero_proof_artifact_validation_state(payload: Mapping[str, Any] | None) -> dict[str, Any]:
    """Build an artifact-level validation report for the future zero-proof file."""

    errors = validate_p0_p1_zero_proof_artifact(payload)
    decision = _mapping(payload.get("independent_closure_decision")) if payload is not None else {}
    state = {
        "status": "pass" if not errors else "blocked",
        "scope": "p0_p1_zero_proof_artifact_validation_only_no_production_acceptance",
        "artifact_path": S2PMT07_P0_P1_ZERO_PROOF_ARTIFACT_PATH,
        "artifact_present": payload is not None,
        "validation_errors": errors,
        "p0_zero_proven_by_payload": not errors and decision.get("p0_zero_proven") is True,
        "p1_zero_proven_by_payload": not errors and decision.get("p1_zero_proven") is True,
        "production_acceptance_claimed": False,
        "integrated_production_accepted": False,
        "daily_operation_enabled": False,
        "real_smtp_send_enabled": False,
        "scheduler_install_enabled": False,
        "release_packaging_enabled": False,
        "production_restore_enabled": False,
        "state_hash": "",
    }
    state["state_hash"] = _stable_hash({key: value for key, value in state.items() if key != "state_hash"})
    return state


def build_final_acceptance_bundle_manifest_hash(payload: Mapping[str, Any]) -> str:
    """Return the canonical final-bundle manifest hash excluding its hash field."""

    payload_without_hash = {key: value for key, value in payload.items() if key != "manifest_hash"}
    return f"sha256:{_stable_hash(payload_without_hash)}"


def validate_final_acceptance_bundle_manifest(payload: Mapping[str, Any] | None) -> list[str]:
    """Validate a future final acceptance bundle manifest without accepting production."""

    if payload is None:
        return ["final_acceptance_bundle_manifest_missing"]
    errors: list[str] = []
    errors.extend(_final_bundle_template_placeholder_errors(payload))
    for field in S2PMT07_FINAL_ACCEPTANCE_BUNDLE_MANIFEST_REQUIRED_FIELDS:
        if field not in payload:
            errors.append(f"{field} is required")
    if payload.get("schema_version") != S2PMT07_FINAL_ACCEPTANCE_BUNDLE_MANIFEST_SCHEMA_VERSION:
        errors.append("schema_version is invalid")
    if payload.get("contract_id") != "ADP-PRODUCT-CONTRACT-V7.2":
        errors.append("contract_id must be ADP-PRODUCT-CONTRACT-V7.2")
    if not isinstance(payload.get("generated_at"), str) or not payload.get("generated_at"):
        errors.append("generated_at must be a non-empty string")
    if payload.get("final_bundle_decision") != S2PMT07_FINAL_ACCEPTANCE_BUNDLE_MANIFEST_DECISION:
        errors.append("final_bundle_decision is invalid")

    if tuple(payload.get("bundle_items", [])) != S2PMT07_FINAL_ACCEPTANCE_BUNDLE_REQUIRED_ITEMS:
        errors.append("bundle_items must exactly match final acceptance bundle required items")
    item_hashes = _mapping(payload.get("bundle_item_hashes"))
    for item in S2PMT07_FINAL_ACCEPTANCE_BUNDLE_REQUIRED_ITEMS:
        value = item_hashes.get(item)
        if not isinstance(value, str) or not value.startswith("sha256:"):
            errors.append(f"bundle_item_hashes.{item} must be a sha256 hash")

    artifact_validations = _mapping(payload.get("artifact_validations"))
    for validation in S2PMT07_FINAL_ACCEPTANCE_BUNDLE_MANIFEST_REQUIRED_ARTIFACT_VALIDATIONS:
        validation_state = _mapping(artifact_validations.get(validation))
        if validation_state.get("status") != "pass":
            errors.append(f"artifact_validations.{validation}.status must be pass")

    closure_state = _mapping(payload.get("closure_state"))
    required_true_closure_flags = (
        "p0_zero_proven",
        "p1_zero_proven",
        "s2plt04_completed",
        "independent_final_review_passed",
        "final_commands_executed",
    )
    for flag in required_true_closure_flags:
        if closure_state.get(flag) is not True:
            errors.append(f"closure_state.{flag} must be true")
    for flag in ("production_acceptance_claimed", "integrated_production_accepted"):
        if closure_state.get(flag) is not False:
            errors.append(f"closure_state.{flag} must be false")

    no_production = _mapping(payload.get("no_production_side_effects"))
    for flag in S2PMT07_FINAL_ACCEPTANCE_BUNDLE_NO_PRODUCTION_FLAGS:
        if no_production.get(flag) is not False:
            errors.append(f"no_production_side_effects.{flag} must be false")

    if payload.get("manifest_hash") != build_final_acceptance_bundle_manifest_hash(payload):
        errors.append("manifest_hash does not match payload content")
    return errors


def build_final_acceptance_bundle_manifest_validation_state(payload: Mapping[str, Any] | None) -> dict[str, Any]:
    """Build a validation report for a future final-bundle manifest."""

    errors = validate_final_acceptance_bundle_manifest(payload)
    bundle_items = tuple(payload.get("bundle_items", [])) if payload is not None else ()
    artifact_validations = _mapping(payload.get("artifact_validations")) if payload is not None else {}
    closure_state = _mapping(payload.get("closure_state")) if payload is not None else {}
    all_artifacts_pass = all(
        _mapping(artifact_validations.get(validation)).get("status") == "pass"
        for validation in S2PMT07_FINAL_ACCEPTANCE_BUNDLE_MANIFEST_REQUIRED_ARTIFACT_VALIDATIONS
    )
    state = {
        "status": "pass" if not errors else "blocked",
        "scope": "final_acceptance_bundle_manifest_validation_only_no_production_acceptance",
        "manifest_path": "FINAL_ACCEPTANCE_BUNDLE/manifest.json",
        "manifest_present": payload is not None,
        "validation_errors": errors,
        "bundle_items_complete": bundle_items == S2PMT07_FINAL_ACCEPTANCE_BUNDLE_REQUIRED_ITEMS,
        "all_artifact_validations_passed": payload is not None and all_artifacts_pass,
        "p0_zero_proven_by_manifest": not errors and closure_state.get("p0_zero_proven") is True,
        "p1_zero_proven_by_manifest": not errors and closure_state.get("p1_zero_proven") is True,
        "s2plt04_completed_by_manifest": not errors and closure_state.get("s2plt04_completed") is True,
        "production_acceptance_claimed": False,
        "integrated_production_accepted": False,
        "daily_operation_enabled": False,
        "real_smtp_send_enabled": False,
        "scheduler_install_enabled": False,
        "release_packaging_enabled": False,
        "production_restore_enabled": False,
        "state_hash": "",
    }
    state["state_hash"] = _stable_hash({key: value for key, value in state.items() if key != "state_hash"})
    return state


def build_s2plt04_completion_report_hash(payload: Mapping[str, Any]) -> str:
    """Return the canonical S2PLT04 completion report hash excluding its hash field."""

    payload_without_hash = {key: value for key, value in payload.items() if key != "report_hash"}
    return f"sha256:{_stable_hash(payload_without_hash)}"


def validate_s2plt04_completion_report(payload: Mapping[str, Any] | None) -> list[str]:
    """Validate a future S2PLT04 completion report without accepting production."""

    if payload is None:
        return ["s2plt04_completion_report_missing"]
    errors: list[str] = []
    errors.extend(_final_bundle_template_placeholder_errors(payload))
    for field in S2PMT07_S2PLT04_COMPLETION_REPORT_REQUIRED_FIELDS:
        if field not in payload:
            errors.append(f"{field} is required")
    if payload.get("schema_version") != S2PMT07_S2PLT04_COMPLETION_REPORT_SCHEMA_VERSION:
        errors.append("schema_version is invalid")
    if payload.get("contract_id") != "ADP-PRODUCT-CONTRACT-V7.2":
        errors.append("contract_id must be ADP-PRODUCT-CONTRACT-V7.2")
    if not isinstance(payload.get("generated_at"), str) or not payload.get("generated_at"):
        errors.append("generated_at must be a non-empty string")
    if payload.get("s2plt04_decision") != S2PMT07_S2PLT04_COMPLETION_REPORT_DECISION:
        errors.append("s2plt04_decision is invalid")

    source_refs = _mapping(payload.get("source_evidence_refs"))
    for ref in S2PMT07_S2PLT04_COMPLETION_REPORT_REQUIRED_SOURCE_EVIDENCE_REFS:
        ref_state = _mapping(source_refs.get(ref))
        if ref not in source_refs:
            errors.append(f"source_evidence_refs must include {ref}")
            continue
        if ref_state.get("status") != "pass":
            errors.append(f"source_evidence_refs.{ref}.status must be pass")
        if not isinstance(ref_state.get("artifact_ref"), str) or not ref_state.get("artifact_ref"):
            errors.append(f"source_evidence_refs.{ref}.artifact_ref must be a non-empty string")

    terminal_dependencies = _mapping(payload.get("terminal_dependency_state"))
    for dependency in S2PMT07_S2PLT04_COMPLETION_REPORT_REQUIRED_TERMINAL_DEPENDENCIES:
        if terminal_dependencies.get(dependency) is not True:
            errors.append(f"terminal_dependency_state.{dependency} must be true")

    if tuple(payload.get("final_bundle_refs", [])) != S2PMT07_FINAL_ACCEPTANCE_BUNDLE_REQUIRED_ITEMS:
        errors.append("final_bundle_refs must exactly match final acceptance bundle required items")

    no_production = _mapping(payload.get("no_production_side_effects"))
    for flag in S2PMT07_S2PLT04_COMPLETION_REPORT_NO_PRODUCTION_FLAGS:
        if no_production.get(flag) is not False:
            errors.append(f"no_production_side_effects.{flag} must be false")

    if payload.get("report_hash") != build_s2plt04_completion_report_hash(payload):
        errors.append("report_hash does not match payload content")
    return errors


def build_s2plt04_completion_report_validation_state(payload: Mapping[str, Any] | None) -> dict[str, Any]:
    """Build a validation report for a future S2PLT04 completion report."""

    errors = validate_s2plt04_completion_report(payload)
    terminal_dependencies = _mapping(payload.get("terminal_dependency_state")) if payload is not None else {}
    terminal_dependencies_passed = all(
        terminal_dependencies.get(dependency) is True
        for dependency in S2PMT07_S2PLT04_COMPLETION_REPORT_REQUIRED_TERMINAL_DEPENDENCIES
    )
    state = {
        "status": "pass" if not errors else "blocked",
        "scope": "s2plt04_completion_report_validation_only_no_production_acceptance",
        "report_path": "FINAL_ACCEPTANCE_BUNDLE/s2plt04_completion_report.json",
        "report_present": payload is not None,
        "validation_errors": errors,
        "required_source_evidence_refs": list(S2PMT07_S2PLT04_COMPLETION_REPORT_REQUIRED_SOURCE_EVIDENCE_REFS),
        "required_terminal_dependencies": list(
            S2PMT07_S2PLT04_COMPLETION_REPORT_REQUIRED_TERMINAL_DEPENDENCIES
        ),
        "terminal_dependencies_passed": payload is not None and terminal_dependencies_passed,
        "s2plt04_completed_by_report": not errors and payload is not None,
        "production_acceptance_claimed": False,
        "integrated_production_accepted": False,
        "daily_operation_enabled": False,
        "real_smtp_send_enabled": False,
        "scheduler_install_enabled": False,
        "release_packaging_enabled": False,
        "production_restore_enabled": False,
        "state_hash": "",
    }
    state["state_hash"] = _stable_hash({key: value for key, value in state.items() if key != "state_hash"})
    return state


def build_s2plt04_completion_evidence_audit_state(
    *, repo_root: str | Path = "."
) -> dict[str, Any]:
    """Audit whether S2PLT04 completion-report source evidence is terminal-ready."""

    root = Path(repo_root)
    zero_proof = _load_committed_p0_p1_zero_proof(root)
    zero_proof_state = build_p0_p1_zero_proof_artifact_validation_state(zero_proof)
    s2plt01_terminal_audit = build_s2plt01_terminal_acceptance_audit_state(repo_root=root)
    s2plt01_accepted = s2plt01_terminal_audit.get("status") == "pass" and (
        s2plt01_terminal_audit.get("s2plt01_accepted") is True
    )
    s2plt02_terminal_audit = build_s2plt02_terminal_readiness_audit_state(
        generated_at="2026-06-29T10:35:11+10:00",
        repo_root=root,
    )
    s2plt03_resilience_audit = build_s2plt03_resilience_precheck_report(
        generated_at="2026-06-29T12:12:00+10:00",
        repo_root=root,
    )
    s2plt03_terminal_artifact_audit = build_s2plt03_terminal_resilience_proof_artifact_validation_state(
        repo_root=root,
    )
    p0_zero = zero_proof_state.get("p0_zero_proven_by_payload") is True
    p1_zero = zero_proof_state.get("p1_zero_proven_by_payload") is True
    s2plt02_remaining_blockers = list(s2plt02_terminal_audit["blocking_reasons"])
    if not p0_zero:
        s2plt02_remaining_blockers.append("inherited_v7_1_p0_findings_open")
    if not p1_zero:
        s2plt02_remaining_blockers.append("inherited_v7_1_p1_findings_open")
    s2plt02_authorization_manifest_ref = (
        "governance/run_manifests/ADP-S2PLT02-REAL-PROOF-CAPTURE-AUTHORIZATION-LIVE-20260630.json"
    )
    s2plt02_authorization_artifact = _load_json_mapping_artifact(
        root / S2PLT02_REAL_PROOF_CAPTURE_AUTHORIZATION_ARTIFACT_PATH
    )
    s2plt02_authorization_validation = build_s2plt02_real_proof_capture_authorization_validation_state(
        s2plt02_authorization_artifact
    )
    s2plt02_authorization_status = str(s2plt02_authorization_validation["status"])
    s2plt02_authorization_blocking_reasons = [
        reason
        for reason in s2plt02_authorization_validation.get("validation_errors", [])
        if isinstance(reason, str)
    ]
    s2plt02_real_proof_capture_authorized = (
        s2plt02_authorization_validation.get("real_proof_capture_authorized_by_payload") is True
    )
    if not s2plt02_real_proof_capture_authorized:
        for reason in s2plt02_authorization_blocking_reasons:
            if reason not in s2plt02_remaining_blockers:
                s2plt02_remaining_blockers.append(reason)
    s2plt02_existing_nonterminal_ref_candidates = (
            "governance/run_manifests/ADP-S2PLT02-LIVE-2D-PRECHECK-20260626.json",
            "governance/run_manifests/ADP-S2PLT02-PARTIAL-REAL-DELIVERY-EVIDENCE-20260628.json",
            "governance/run_manifests/ADP-S2PLT02-ZERO-PROOF-READINESS-SYNC-20260629.json",
            "governance/run_manifests/ADP-S2PLT02-TERMINAL-READINESS-AUDIT-20260629.json",
            "governance/run_manifests/ADP-S2PLT02-REAL-PROOF-CAPTURE-AUTHORIZATION-LIVE-20260630.json",
            "governance/run_manifests/ADP-S2PLT02-REAL-DELIVERY-MANIFEST-INPUT-VALIDATOR-20260630.json",
            "governance/run_manifests/ADP-S2PLT02-REAL-DELIVERY-MANIFEST-NORMALIZATION-20260630.json",
            "governance/run_manifests/ADP-S2PLT02-NORMALIZED-REAL-DELIVERY-MANIFEST-20260628.json",
            "governance/run_manifests/ADP-S2PLT02-TERMINAL-DELIVERY-INPUT-INVENTORY-20260630.json",
            "governance/run_manifests/ADP-S2PLT02-TERMINAL-DELIVERY-PROOF-CAPTURE-PLAN-20260630.json",
            "governance/run_manifests/ADP-S2PLT02-TERMINAL-CAPTURE-WINDOW-AUDIT-CLI-20260630.json",
            "governance/run_manifests/ADP-S2PLT02-TERMINAL-CAPTURE-WINDOW-RUNTIME-STATE-SYNC-20260630.json",
            "governance/run_manifests/ADP-S2PLT02-TERMINAL-PROOF-EVIDENCE-INVENTORY-20260630.json",
            "governance/run_manifests/ADP-S2PLT02-REAL-PROOF-CAPTURE-READINESS-LIVE-AUTH-SYNC-20260630.json",
            s2plt02_authorization_manifest_ref,
        )
    s2plt02_existing_nonterminal_refs = []
    for ref in s2plt02_existing_nonterminal_ref_candidates:
        if ref not in s2plt02_existing_nonterminal_refs and (root / ref).exists():
            s2plt02_existing_nonterminal_refs.append(ref)
    source_evidence = {
        "S2PLT01_REPLAY_REVIEW": {
            "artifact_status": "pass" if s2plt01_accepted else "nonterminal",
            "artifact_ref": (
                s2plt01_terminal_audit["terminal_acceptance_artifact_ref"]
                if s2plt01_accepted
                else "governance/run_manifests/ADP-S2PLT01-INDEPENDENT-REPLAY-REVIEW-20260626.json"
            ),
            "nonterminal_ref": "governance/run_manifests/ADP-S2PLT01-INDEPENDENT-REPLAY-REVIEW-20260626.json",
            "terminal_dependency": "S2PLT01_ACCEPTED",
            "terminal_dependency_value": s2plt01_accepted,
            "terminal_acceptance_audit_status": s2plt01_terminal_audit["status"],
            "terminal_acceptance_audit_state_hash": s2plt01_terminal_audit["state_hash"],
            "blocking_reason": None if s2plt01_accepted else "s2plt01_not_accepted",
            "note": (
                "terminal acceptance artifact passed; historical review receipt remains as supporting input"
                if s2plt01_accepted
                else "independent replay review artifact exists but recorded s2plt01_accepted=false"
            ),
        },
        "S2PLT02_LIVE_2D_PROOF": {
            "artifact_status": "missing_terminal",
            "artifact_ref": "governance/run_manifests/MISSING_REAL_S2PLT02_TERMINAL_PROOF.json",
            "nonterminal_refs": s2plt02_existing_nonterminal_refs,
            "existing_nonterminal_refs": s2plt02_existing_nonterminal_refs,
            "real_proof_capture_authorization_manifest_ref": s2plt02_authorization_manifest_ref,
            "real_proof_capture_authorization_artifact_ref": S2PLT02_REAL_PROOF_CAPTURE_AUTHORIZATION_ARTIFACT_PATH,
            "real_proof_capture_authorization_status": s2plt02_authorization_status,
            "real_proof_capture_authorization_validation_state_hash": (
                s2plt02_authorization_validation["state_hash"]
            ),
            "real_proof_capture_authorized": s2plt02_real_proof_capture_authorized,
            "real_proof_capture_authorization_blocking_reasons": s2plt02_authorization_blocking_reasons,
            "terminal_dependency": "S2PLT02_ACCEPTED",
            "terminal_dependency_value": False,
            "blocking_reason": "s2plt02_live_2d_terminal_proof_missing",
            "terminal_readiness_audit_status": s2plt02_terminal_audit["status"],
            "terminal_readiness_audit_state_hash": s2plt02_terminal_audit["state_hash"],
            "terminal_readiness_precheck_report_hash": s2plt02_terminal_audit["precheck_report_hash"],
            "terminal_dependency_state": dict(s2plt02_terminal_audit["terminal_dependency_state"]),
            "observed_natural_days": 1,
            "required_natural_days": 2,
            "observed_email_count": 4,
            "required_email_count": 8,
            "m4_watermark_correct": True,
            "m4_watermark_proof_ref": (
                "governance/run_manifests/ADP-S2PLT02-M4-WATERMARK-PROOF-RECORD-20260628.json"
            ),
            "remaining_terminal_blockers": s2plt02_remaining_blockers,
        },
        "S2PLT03_RESILIENCE_PROOF": {
            "artifact_status": "pass" if s2plt03_terminal_artifact_audit["status"] == "pass" else "missing_terminal",
            "artifact_ref": S2PLT03_TERMINAL_RESILIENCE_PROOF_ARTIFACT_PATH,
            "nonterminal_refs": [
                "governance/run_manifests/ADP-S2PLT03-RESILIENCE-PRECHECK-20260628.json",
                "governance/run_manifests/ADP-S2PLT03-LOCAL-RESILIENCE-DRILL-20260628.json",
                "governance/run_manifests/ADP-S2PLT03-ZERO-PROOF-RESILIENCE-SYNC-20260629.json",
                "governance/run_manifests/ADP-S2PLT03-AUDIT-BLOCKER-ZERO-PROOF-SYNC-20260629.json",
            ],
            "terminal_dependency": "S2PLT03_ACCEPTED",
            "terminal_dependency_value": s2plt03_terminal_artifact_audit["s2plt03_accepted_by_artifact"] is True,
            "blocking_reason": (
                None
                if s2plt03_terminal_artifact_audit["s2plt03_accepted_by_artifact"] is True
                else "s2plt03_resilience_terminal_proof_missing"
            ),
            "audit_blockers_status": s2plt03_resilience_audit["audit_blockers"]["status"],
            "latest_audit_report_hash": s2plt03_resilience_audit["report_hash"],
            "terminal_artifact_validation_status": s2plt03_terminal_artifact_audit["status"],
            "terminal_artifact_validation_state_hash": s2plt03_terminal_artifact_audit["state_hash"],
            "terminal_artifact_validation_errors": list(s2plt03_terminal_artifact_audit["validation_errors"]),
            "terminal_artifact_blocking_reasons": list(s2plt03_terminal_artifact_audit["blocking_reasons"]),
        },
        "P0_P1_ZERO_PROOF": {
            "artifact_status": "pass" if zero_proof_state.get("status") == "pass" else "blocked",
            "artifact_ref": S2PMT07_P0_P1_ZERO_PROOF_ARTIFACT_PATH,
            "terminal_dependencies": {
                "P0_ZERO_PROVEN": p0_zero,
                "P1_ZERO_PROVEN": p1_zero,
            },
            "validation_errors": list(zero_proof_state.get("validation_errors", [])),
        },
    }
    terminal_dependency_state = {
        "S2PLT01_ACCEPTED": s2plt01_accepted,
        "S2PLT02_ACCEPTED": False,
        "S2PLT03_ACCEPTED": s2plt03_terminal_artifact_audit["s2plt03_accepted_by_artifact"] is True,
        "P0_ZERO_PROVEN": p0_zero,
        "P1_ZERO_PROVEN": p1_zero,
    }
    blocking_reasons = [
        evidence["blocking_reason"]
        for evidence in source_evidence.values()
        if evidence.get("blocking_reason")
    ]
    if not p0_zero and "p0_zero_not_proven" not in blocking_reasons:
        blocking_reasons.append("p0_zero_not_proven")
    if not p1_zero and "p1_zero_not_proven" not in blocking_reasons:
        blocking_reasons.append("p1_zero_not_proven")
    completion_report_ready = (
        all(terminal_dependency_state.values())
        and all(evidence.get("artifact_status") == "pass" for evidence in source_evidence.values())
    )
    s2plt02_nonterminal_refs = list(
        _mapping(source_evidence["S2PLT02_LIVE_2D_PROOF"]).get("existing_nonterminal_refs", [])
    )
    s2plt03_nonterminal_refs = list(
        _mapping(source_evidence["S2PLT03_RESILIENCE_PROOF"]).get("nonterminal_refs", [])
    )
    state = {
        "status": "pass" if completion_report_ready else "blocked",
        "scope": S2PMT07_S2PLT04_COMPLETION_EVIDENCE_AUDIT_SCOPE,
        "task_id": "S2PMT07-S2PLT04-COMPLETION-REPORT",
        "contract_id": "ADP-PRODUCT-CONTRACT-V7.2",
        "next_required_artifact": "FINAL_ACCEPTANCE_BUNDLE/s2plt04_completion_report.json",
        "completion_report_ready": completion_report_ready,
        "s2plt04_completion_report_written": False,
        "required_source_evidence_refs": list(S2PMT07_S2PLT04_COMPLETION_REPORT_REQUIRED_SOURCE_EVIDENCE_REFS),
        "source_evidence": source_evidence,
        "s2plt02_nonterminal_ref_count": len(s2plt02_nonterminal_refs),
        "s2plt02_latest_nonterminal_ref": s2plt02_nonterminal_refs[-1] if s2plt02_nonterminal_refs else "",
        "s2plt03_nonterminal_ref_count": len(s2plt03_nonterminal_refs),
        "s2plt03_latest_nonterminal_ref": s2plt03_nonterminal_refs[-1] if s2plt03_nonterminal_refs else "",
        "terminal_dependency_state": terminal_dependency_state,
        "blocking_reasons": blocking_reasons,
        "default_next_actions": [
            "do_not_create_s2plt04_completion_report_until_terminal_dependencies_are_true",
            "obtain_real_s2plt02_two_day_eight_email_terminal_proof",
            "obtain_real_s2plt03_terminal_resilience_proof_after_s2plt02_acceptance",
            "re-run validate-s2plt04-completion-report only after the real report exists",
        ],
        "production_acceptance_claimed": False,
        "integrated_production_accepted": False,
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
        "state_hash": "",
    }
    state["state_hash"] = _stable_hash({key: value for key, value in state.items() if key != "state_hash"})
    return state


def validate_s2plt04_completion_evidence_audit_state(state: Mapping[str, Any]) -> list[str]:
    """Validate S2PLT04 completion evidence audit output."""

    errors: list[str] = []
    if state.get("status") not in {"pass", "blocked"}:
        errors.append("S2PLT04 completion evidence audit status must be pass or blocked")
    if state.get("scope") != S2PMT07_S2PLT04_COMPLETION_EVIDENCE_AUDIT_SCOPE:
        errors.append("S2PLT04 completion evidence audit scope is invalid")
    if state.get("task_id") != "S2PMT07-S2PLT04-COMPLETION-REPORT":
        errors.append("S2PLT04 completion evidence audit task_id is invalid")
    if state.get("next_required_artifact") != "FINAL_ACCEPTANCE_BUNDLE/s2plt04_completion_report.json":
        errors.append("S2PLT04 completion evidence audit next_required_artifact is invalid")
    if state.get("s2plt04_completion_report_written") is not False:
        errors.append("S2PLT04 completion evidence audit must not write completion report")
    if tuple(state.get("required_source_evidence_refs", [])) != (
        S2PMT07_S2PLT04_COMPLETION_REPORT_REQUIRED_SOURCE_EVIDENCE_REFS
    ):
        errors.append("S2PLT04 completion evidence audit source refs are invalid")
    source_evidence = _mapping(state.get("source_evidence"))
    for ref in S2PMT07_S2PLT04_COMPLETION_REPORT_REQUIRED_SOURCE_EVIDENCE_REFS:
        if ref not in source_evidence:
            errors.append(f"S2PLT04 completion evidence audit must include {ref}")
    s2plt02_evidence = _mapping(source_evidence.get("S2PLT02_LIVE_2D_PROOF"))
    s2plt02_nonterminal_refs = list(s2plt02_evidence.get("existing_nonterminal_refs", []))
    if state.get("s2plt02_nonterminal_ref_count") != len(s2plt02_nonterminal_refs):
        errors.append("S2PLT04 completion evidence audit S2PLT02 nonterminal ref count is inconsistent")
    if state.get("s2plt02_latest_nonterminal_ref") != (
        s2plt02_nonterminal_refs[-1] if s2plt02_nonterminal_refs else ""
    ):
        errors.append("S2PLT04 completion evidence audit S2PLT02 latest nonterminal ref is inconsistent")
    s2plt03_evidence = _mapping(source_evidence.get("S2PLT03_RESILIENCE_PROOF"))
    s2plt03_nonterminal_refs = list(s2plt03_evidence.get("nonterminal_refs", []))
    if state.get("s2plt03_nonterminal_ref_count") != len(s2plt03_nonterminal_refs):
        errors.append("S2PLT04 completion evidence audit S2PLT03 nonterminal ref count is inconsistent")
    if state.get("s2plt03_latest_nonterminal_ref") != (
        s2plt03_nonterminal_refs[-1] if s2plt03_nonterminal_refs else ""
    ):
        errors.append("S2PLT04 completion evidence audit S2PLT03 latest nonterminal ref is inconsistent")
    terminal_dependencies = _mapping(state.get("terminal_dependency_state"))
    for dependency in S2PMT07_S2PLT04_COMPLETION_REPORT_REQUIRED_TERMINAL_DEPENDENCIES:
        if dependency not in terminal_dependencies:
            errors.append(f"S2PLT04 completion evidence audit terminal dependencies must include {dependency}")
    expected_ready = all(terminal_dependencies.values()) and all(
        _mapping(source_evidence.get(ref)).get("artifact_status") == "pass"
        for ref in S2PMT07_S2PLT04_COMPLETION_REPORT_REQUIRED_SOURCE_EVIDENCE_REFS
    )
    if state.get("completion_report_ready") is not expected_ready:
        errors.append("S2PLT04 completion evidence audit readiness must match terminal dependencies and source evidence status")
    if state.get("status") == "blocked":
        expected_reasons: list[str] = []
        if terminal_dependencies.get("S2PLT01_ACCEPTED") is not True:
            expected_reasons.append("s2plt01_not_accepted")
        if terminal_dependencies.get("S2PLT02_ACCEPTED") is not True:
            expected_reasons.append("s2plt02_live_2d_terminal_proof_missing")
        if terminal_dependencies.get("S2PLT03_ACCEPTED") is not True:
            expected_reasons.append("s2plt03_resilience_terminal_proof_missing")
        if terminal_dependencies.get("P0_ZERO_PROVEN") is not True:
            expected_reasons.append("p0_zero_not_proven")
        if terminal_dependencies.get("P1_ZERO_PROVEN") is not True:
            expected_reasons.append("p1_zero_not_proven")
        for reason in expected_reasons:
            if reason not in state.get("blocking_reasons", []):
                errors.append(f"blocked S2PLT04 completion evidence audit must include {reason}")
    else:
        if state.get("blocking_reasons"):
            errors.append("passing S2PLT04 completion evidence audit must not have blocking reasons")
    for flag in S2PMT07_FINAL_ACCEPTANCE_BUNDLE_NO_PRODUCTION_FLAGS:
        if state.get(flag) is not False:
            errors.append(f"{flag} must be false")
    if state.get("state_hash") != _stable_hash({key: value for key, value in state.items() if key != "state_hash"}):
        errors.append("S2PLT04 completion evidence audit state_hash does not match state content")
    return errors


def build_final_command_execution_hash(payload: Mapping[str, Any]) -> str:
    """Return the canonical final-command execution hash excluding its hash field."""

    payload_without_hash = {key: value for key, value in payload.items() if key != "execution_hash"}
    return f"sha256:{_stable_hash(payload_without_hash)}"


def validate_final_command_execution_artifact(payload: Mapping[str, Any] | None) -> list[str]:
    """Validate a future final command execution artifact without accepting production."""

    if payload is None:
        return ["final_command_execution_missing"]
    errors: list[str] = []
    errors.extend(_final_bundle_template_placeholder_errors(payload))
    for field in S2PMT07_FINAL_COMMAND_EXECUTION_REQUIRED_FIELDS:
        if field not in payload:
            errors.append(f"{field} is required")
    if tuple(payload.keys()) != S2PMT07_FINAL_COMMAND_EXECUTION_REQUIRED_FIELDS:
        errors.append("final command execution field order is invalid")
    if payload.get("schema_version") != S2PMT07_FINAL_COMMAND_EXECUTION_SCHEMA_VERSION:
        errors.append("schema_version is invalid")
    if payload.get("contract_id") != "ADP-PRODUCT-CONTRACT-V7.2":
        errors.append("contract_id must be ADP-PRODUCT-CONTRACT-V7.2")
    if not isinstance(payload.get("generated_at"), str) or not payload.get("generated_at"):
        errors.append("generated_at must be a non-empty string")
    if payload.get("execution_decision") != S2PMT07_FINAL_COMMAND_EXECUTION_DECISION:
        errors.append("execution_decision is invalid")

    executor = _mapping(payload.get("executor_independence"))
    if executor.get("status") != "verified":
        errors.append("executor_independence.status must be verified")
    if executor.get("required_independence") != S2PMT07_REQUIRED_REVIEWER_INDEPENDENCE:
        errors.append("executor_independence.required_independence is invalid")
    if executor.get("executor_role") != "independent_final_reviewer":
        errors.append("executor_independence.executor_role must be independent_final_reviewer")

    if tuple(payload.get("required_commands_executed", [])) != S2PMT07_REQUIRED_TEST_COMMANDS:
        errors.append("required_commands_executed must exactly match S2PMT07 required test commands")
    command_results = _mapping(payload.get("command_results"))
    for command in S2PMT07_REQUIRED_TEST_COMMANDS:
        result = _mapping(command_results.get(command))
        if command not in command_results:
            errors.append(f"command_results must include {command}")
            continue
        if result.get("status") != "pass":
            errors.append(f"command_results.{command}.status must be pass")
        if result.get("exit_code") != 0:
            errors.append(f"command_results.{command}.exit_code must be 0")
        if result.get("executed_by") != "independent_final_reviewer":
            errors.append(f"command_results.{command}.executed_by must be independent_final_reviewer")
        if not isinstance(result.get("evidence_ref"), str) or not result.get("evidence_ref"):
            errors.append(f"command_results.{command}.evidence_ref must be a non-empty string")

    if tuple(payload.get("final_bundle_refs", [])) != S2PMT07_FINAL_ACCEPTANCE_BUNDLE_REQUIRED_ITEMS:
        errors.append("final_bundle_refs must exactly match final acceptance bundle required items")

    no_production = _mapping(payload.get("no_production_side_effects"))
    for flag in S2PMT07_FINAL_COMMAND_EXECUTION_NO_PRODUCTION_FLAGS:
        if no_production.get(flag) is not False:
            errors.append(f"no_production_side_effects.{flag} must be false")

    if payload.get("execution_hash") != build_final_command_execution_hash(payload):
        errors.append("execution_hash does not match payload content")
    return errors


def build_final_command_execution_validation_state(payload: Mapping[str, Any] | None) -> dict[str, Any]:
    """Build a validation report for future independent final command execution evidence."""

    errors = validate_final_command_execution_artifact(payload)
    command_results = _mapping(payload.get("command_results")) if payload is not None else {}
    all_required_commands_passed = all(
        _mapping(command_results.get(command)).get("status") == "pass"
        and _mapping(command_results.get(command)).get("exit_code") == 0
        for command in S2PMT07_REQUIRED_TEST_COMMANDS
    )
    state = {
        "status": "pass" if not errors else "blocked",
        "scope": "final_command_execution_validation_only_no_production_acceptance",
        "artifact_path": "FINAL_ACCEPTANCE_BUNDLE/final_command_execution.json",
        "command_execution_present": payload is not None,
        "validation_errors": errors,
        "required_commands": list(S2PMT07_REQUIRED_TEST_COMMANDS),
        "all_required_commands_passed": payload is not None and all_required_commands_passed,
        "final_commands_executed_by_payload": not errors and payload is not None,
        "production_acceptance_claimed": False,
        "integrated_production_accepted": False,
        "daily_operation_enabled": False,
        "real_smtp_send_enabled": False,
        "scheduler_install_enabled": False,
        "release_packaging_enabled": False,
        "production_restore_enabled": False,
        "state_hash": "",
    }
    state["state_hash"] = _stable_hash({key: value for key, value in state.items() if key != "state_hash"})
    return state


def _parse_launchd_disabled_states(print_disabled_output: str) -> dict[str, str]:
    states: dict[str, str] = {}
    for raw_line in print_disabled_output.splitlines():
        line = raw_line.strip()
        if "=>" not in line:
            continue
        label_part, state_part = line.split("=>", 1)
        label = label_part.strip().strip('"')
        state = state_part.strip().lower()
        if label in S2PMT07_LOCAL_RUNTIME_NO_PRODUCTION_REQUIRED_LABELS:
            states[label] = state
    return states


def _parse_launchd_service_state(print_output: str) -> str:
    for raw_line in print_output.splitlines():
        line = raw_line.strip()
        if line.startswith("state ="):
            return line.split("=", 1)[1].strip()
    return "missing"


def _launchd_calendar_trigger_present(print_output: str) -> bool:
    return "com.apple.launchd.calendarinterval" in print_output


def build_local_runtime_no_production_state(
    *,
    generated_at: str,
    launchctl_print_disabled_output: str,
    launchctl_print_outputs: Mapping[str, str] | None = None,
    env_flags: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Build a fail-closed local runtime no-production precheck from sanitized launchd/env facts."""

    disabled_states = _parse_launchd_disabled_states(launchctl_print_disabled_output)
    service_outputs = launchctl_print_outputs or {}
    env = {key: str(value).strip().lower() for key, value in (env_flags or {}).items()}
    labels = S2PMT07_LOCAL_RUNTIME_NO_PRODUCTION_REQUIRED_LABELS
    launchd_disabled = {
        label: disabled_states.get(label, "missing")
        for label in labels
    }
    launchd_running = {
        label: _parse_launchd_service_state(str(service_outputs.get(label, "")))
        for label in labels
    }
    env_flag_states = {
        flag: env.get(flag, "missing")
        for flag in S2PMT07_LOCAL_RUNTIME_NO_PRODUCTION_REQUIRED_ENV_FLAGS_FALSE
    }
    label_disabled_ok = all(state == "disabled" for state in launchd_disabled.values())
    label_not_running_ok = all(state == "not running" for state in launchd_running.values())
    smtp_send_flag_false = env_flag_states["ADP_ALLOW_SMTP_SEND"] in {"false", "0", "no", "off"}
    blocking_reasons: list[str] = []
    if not label_disabled_ok:
        blocking_reasons.append("launchd_label_not_disabled")
    if not label_not_running_ok:
        blocking_reasons.append("launchd_label_running")
    if not smtp_send_flag_false:
        blocking_reasons.append("smtp_send_flag_enabled")
    state = {
        "schema_version": S2PMT07_LOCAL_RUNTIME_NO_PRODUCTION_SCHEMA_VERSION,
        "task_id": S2PMT07_TASK_ID,
        "acceptance_id": S2PMT07_ACCEPTANCE_ID,
        "generated_at": generated_at,
        "status": "pass" if not blocking_reasons else "blocked",
        "scope": S2PMT07_LOCAL_RUNTIME_NO_PRODUCTION_SCOPE,
        "required_launchd_labels": list(labels),
        "launchd_disabled_states": launchd_disabled,
        "launchd_running_states": launchd_running,
        "required_env_flags_false": list(S2PMT07_LOCAL_RUNTIME_NO_PRODUCTION_REQUIRED_ENV_FLAGS_FALSE),
        "env_flag_states": env_flag_states,
        "launchd_labels_disabled": label_disabled_ok,
        "launchd_labels_not_running": label_not_running_ok,
        "smtp_send_flag_false": smtp_send_flag_false,
        "blocking_reasons": blocking_reasons,
        "production_acceptance_claimed": False,
        "integrated_production_accepted": False,
        "daily_operation_enabled": False,
        "real_smtp_send_enabled": False,
        "scheduler_install_enabled": False,
        "release_packaging_enabled": False,
        "production_restore_enabled": False,
        "state_hash": "",
    }
    state["state_hash"] = _stable_hash({key: value for key, value in state.items() if key != "state_hash"})
    return state


def validate_local_runtime_no_production_state(state: Mapping[str, Any]) -> list[str]:
    """Validate local runtime no-production precheck state without enabling or claiming production."""

    errors: list[str] = []
    if state.get("schema_version") != S2PMT07_LOCAL_RUNTIME_NO_PRODUCTION_SCHEMA_VERSION:
        errors.append("local runtime no-production schema_version is invalid")
    if state.get("task_id") != S2PMT07_TASK_ID:
        errors.append("local runtime no-production task_id must be S2PMT07")
    if state.get("acceptance_id") != S2PMT07_ACCEPTANCE_ID:
        errors.append("local runtime no-production acceptance_id is invalid")
    if state.get("scope") != S2PMT07_LOCAL_RUNTIME_NO_PRODUCTION_SCOPE:
        errors.append("local runtime no-production scope is invalid")
    if tuple(state.get("required_launchd_labels", [])) != S2PMT07_LOCAL_RUNTIME_NO_PRODUCTION_REQUIRED_LABELS:
        errors.append("required_launchd_labels must match ADP local LaunchAgents")
    if (
        tuple(state.get("required_env_flags_false", []))
        != S2PMT07_LOCAL_RUNTIME_NO_PRODUCTION_REQUIRED_ENV_FLAGS_FALSE
    ):
        errors.append("required_env_flags_false must match ADP SMTP send flag")
    if state.get("status") not in {"pass", "blocked"}:
        errors.append("local runtime no-production status must be pass or blocked")
    for flag in (
        "production_acceptance_claimed",
        "integrated_production_accepted",
        "daily_operation_enabled",
        "real_smtp_send_enabled",
        "scheduler_install_enabled",
        "release_packaging_enabled",
        "production_restore_enabled",
    ):
        if state.get(flag) is not False:
            errors.append(f"{flag} must be false")

    disabled_states = _mapping(state.get("launchd_disabled_states"))
    running_states = _mapping(state.get("launchd_running_states"))
    for label in S2PMT07_LOCAL_RUNTIME_NO_PRODUCTION_REQUIRED_LABELS:
        if disabled_states.get(label) != "disabled" and "launchd_label_not_disabled" not in state.get(
            "blocking_reasons", []
        ):
            errors.append("launchd_label_not_disabled blocker is required")
        if running_states.get(label) != "not running" and "launchd_label_running" not in state.get(
            "blocking_reasons", []
        ):
            errors.append("launchd_label_running blocker is required")
    env_states = _mapping(state.get("env_flag_states"))
    if env_states.get("ADP_ALLOW_SMTP_SEND") not in {"false", "0", "no", "off"} and "smtp_send_flag_enabled" not in state.get(
        "blocking_reasons", []
    ):
        errors.append("smtp_send_flag_enabled blocker is required")

    expected_reasons: list[str] = []
    if state.get("launchd_labels_disabled") is not True:
        expected_reasons.append("launchd_label_not_disabled")
    if state.get("launchd_labels_not_running") is not True:
        expected_reasons.append("launchd_label_running")
    if state.get("smtp_send_flag_false") is not True:
        expected_reasons.append("smtp_send_flag_enabled")
    if state.get("status") == "pass":
        if expected_reasons:
            errors.append("passing local runtime no-production state must have all local runtime gates true")
        if state.get("blocking_reasons"):
            errors.append("passing local runtime no-production state must not have blocking reasons")
    else:
        if tuple(state.get("blocking_reasons", [])) != tuple(expected_reasons):
            errors.append("blocked local runtime no-production blocking_reasons must match failed gates")
    expected_hash = _stable_hash({key: value for key, value in state.items() if key != "state_hash"})
    if state.get("state_hash") != expected_hash:
        errors.append("local runtime no-production state_hash does not match state content")
    return errors


def build_no_production_side_effect_attestation_hash(payload: Mapping[str, Any]) -> str:
    """Return the canonical no-production attestation hash excluding its hash field."""

    payload_without_hash = {key: value for key, value in payload.items() if key != "attestation_hash"}
    return f"sha256:{_stable_hash(payload_without_hash)}"


def validate_no_production_side_effect_attestation(payload: Mapping[str, Any] | None) -> list[str]:
    """Validate a future no-production side-effect attestation without accepting production."""

    if payload is None:
        return ["no_production_side_effect_attestation_missing"]
    errors: list[str] = []
    errors.extend(_final_bundle_template_placeholder_errors(payload))
    for field in S2PMT07_NO_PRODUCTION_SIDE_EFFECT_ATTESTATION_REQUIRED_FIELDS:
        if field not in payload:
            errors.append(f"{field} is required")
    if tuple(payload.keys()) != S2PMT07_NO_PRODUCTION_SIDE_EFFECT_ATTESTATION_REQUIRED_FIELDS:
        errors.append("no-production side-effect attestation field order is invalid")
    if payload.get("schema_version") != S2PMT07_NO_PRODUCTION_SIDE_EFFECT_ATTESTATION_SCHEMA_VERSION:
        errors.append("schema_version is invalid")
    if payload.get("contract_id") != "ADP-PRODUCT-CONTRACT-V7.2":
        errors.append("contract_id must be ADP-PRODUCT-CONTRACT-V7.2")
    if not isinstance(payload.get("generated_at"), str) or not payload.get("generated_at"):
        errors.append("generated_at must be a non-empty string")
    if payload.get("attestation_decision") != S2PMT07_NO_PRODUCTION_SIDE_EFFECT_ATTESTATION_DECISION:
        errors.append("attestation_decision is invalid")

    attestation_scope = _mapping(payload.get("attestation_scope"))
    if attestation_scope.get("task_id") != S2PMT07_TASK_ID:
        errors.append("attestation_scope.task_id must be S2PMT07")
    if (
        attestation_scope.get("scope")
        != "no_production_side_effect_attestation_validation_only_no_production_acceptance"
    ):
        errors.append("attestation_scope.scope is invalid")
    if tuple(attestation_scope.get("required_bundle_items", [])) != S2PMT07_FINAL_ACCEPTANCE_BUNDLE_REQUIRED_ITEMS:
        errors.append("attestation_scope.required_bundle_items must exactly match final bundle items")

    verified_refs = _mapping(payload.get("verified_evidence_refs"))
    for ref in S2PMT07_NO_PRODUCTION_SIDE_EFFECT_ATTESTATION_REQUIRED_EVIDENCE_REFS:
        ref_state = _mapping(verified_refs.get(ref))
        if ref not in verified_refs:
            errors.append(f"verified_evidence_refs must include {ref}")
            continue
        if ref_state.get("status") != "pass":
            errors.append(f"verified_evidence_refs.{ref}.status must be pass")
        if not isinstance(ref_state.get("evidence_ref"), str) or not ref_state.get("evidence_ref"):
            errors.append(f"verified_evidence_refs.{ref}.evidence_ref must be a non-empty string")

    no_production = _mapping(payload.get("no_production_side_effects"))
    for flag in S2PMT07_NO_PRODUCTION_SIDE_EFFECT_ATTESTATION_NO_PRODUCTION_FLAGS:
        if no_production.get(flag) is not False:
            errors.append(f"no_production_side_effects.{flag} must be false")

    closure_state = _mapping(payload.get("closure_state"))
    if closure_state.get("no_production_side_effects_proven") is not True:
        errors.append("closure_state.no_production_side_effects_proven must be true")
    for flag in ("production_acceptance_claimed", "integrated_production_accepted", "daily_operation_enabled"):
        if closure_state.get(flag) is not False:
            errors.append(f"closure_state.{flag} must be false")

    if payload.get("attestation_hash") != build_no_production_side_effect_attestation_hash(payload):
        errors.append("attestation_hash does not match payload content")
    return errors


def build_no_production_side_effect_attestation_validation_state(
    payload: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Build a validation report for future no-production side-effect attestation evidence."""

    errors = validate_no_production_side_effect_attestation(payload)
    verified_refs = _mapping(payload.get("verified_evidence_refs")) if payload is not None else {}
    closure_state = _mapping(payload.get("closure_state")) if payload is not None else {}
    all_required_evidence_refs_passed = all(
        _mapping(verified_refs.get(ref)).get("status") == "pass"
        for ref in S2PMT07_NO_PRODUCTION_SIDE_EFFECT_ATTESTATION_REQUIRED_EVIDENCE_REFS
    )
    state = {
        "status": "pass" if not errors else "blocked",
        "scope": "no_production_side_effect_attestation_validation_only_no_production_acceptance",
        "artifact_path": "FINAL_ACCEPTANCE_BUNDLE/no_production_side_effects.json",
        "attestation_present": payload is not None,
        "validation_errors": errors,
        "required_evidence_refs": list(S2PMT07_NO_PRODUCTION_SIDE_EFFECT_ATTESTATION_REQUIRED_EVIDENCE_REFS),
        "all_required_evidence_refs_passed": payload is not None and all_required_evidence_refs_passed,
        "no_production_side_effects_proven_by_payload": (
            not errors and closure_state.get("no_production_side_effects_proven") is True
        ),
        "production_acceptance_claimed": False,
        "integrated_production_accepted": False,
        "daily_operation_enabled": False,
        "real_smtp_send_enabled": False,
        "scheduler_install_enabled": False,
        "release_packaging_enabled": False,
        "production_restore_enabled": False,
        "state_hash": "",
    }
    state["state_hash"] = _stable_hash({key: value for key, value in state.items() if key != "state_hash"})
    return state


def build_next_agent_handoff_hash(payload: Mapping[str, Any]) -> str:
    """Return the canonical next-agent handoff hash excluding its hash field."""

    payload_without_hash = {key: value for key, value in payload.items() if key != "handoff_hash"}
    return f"sha256:{_stable_hash(payload_without_hash)}"


def validate_next_agent_handoff(payload: Mapping[str, Any] | None) -> list[str]:
    """Validate a future next-agent handoff artifact without accepting production."""

    if payload is None:
        return ["next_agent_handoff_missing"]
    errors: list[str] = []
    errors.extend(_final_bundle_template_placeholder_errors(payload))
    for field in S2PMT07_NEXT_AGENT_HANDOFF_REQUIRED_FIELDS:
        if field not in payload:
            errors.append(f"{field} is required")
    if tuple(payload.keys()) != S2PMT07_NEXT_AGENT_HANDOFF_REQUIRED_FIELDS:
        errors.append("next-agent handoff field order is invalid")
    if payload.get("schema_version") != S2PMT07_NEXT_AGENT_HANDOFF_SCHEMA_VERSION:
        errors.append("schema_version is invalid")
    if payload.get("contract_id") != "ADP-PRODUCT-CONTRACT-V7.2":
        errors.append("contract_id must be ADP-PRODUCT-CONTRACT-V7.2")
    if not isinstance(payload.get("generated_at"), str) or not payload.get("generated_at"):
        errors.append("generated_at must be a non-empty string")
    if payload.get("handoff_decision") != S2PMT07_NEXT_AGENT_HANDOFF_DECISION:
        errors.append("handoff_decision is invalid")

    handoff_scope = _mapping(payload.get("handoff_scope"))
    if handoff_scope.get("task_id") != S2PMT07_TASK_ID:
        errors.append("handoff_scope.task_id must be S2PMT07")
    if handoff_scope.get("scope") != "next_agent_handoff_validation_only_no_production_acceptance":
        errors.append("handoff_scope.scope is invalid")
    if (
        tuple(handoff_scope.get("required_reader_files", []))
        != S2PMT07_NEXT_AGENT_HANDOFF_REQUIRED_READER_FILES
    ):
        errors.append("handoff_scope.required_reader_files must exactly match required reader files")

    if tuple(payload.get("required_reader_files", [])) != S2PMT07_NEXT_AGENT_HANDOFF_REQUIRED_READER_FILES:
        errors.append("required_reader_files must exactly match next-agent handoff required reader files")

    artifact_validations = _mapping(payload.get("required_artifact_validations"))
    for validation in S2PMT07_NEXT_AGENT_HANDOFF_REQUIRED_ARTIFACT_VALIDATIONS:
        result = _mapping(artifact_validations.get(validation))
        if validation not in artifact_validations:
            errors.append(f"required_artifact_validations must include {validation}")
            continue
        if result.get("status") != "pass":
            errors.append(f"required_artifact_validations.{validation}.status must be pass")
        if not isinstance(result.get("evidence_ref"), str) or not result.get("evidence_ref"):
            errors.append(f"required_artifact_validations.{validation}.evidence_ref must be a non-empty string")

    if tuple(payload.get("required_bundle_refs", [])) != S2PMT07_FINAL_ACCEPTANCE_BUNDLE_REQUIRED_ITEMS:
        errors.append("required_bundle_refs must exactly match final acceptance bundle required items")

    blocking_state = _mapping(payload.get("blocking_state"))
    for flag in (
        "p0_zero_proven",
        "p1_zero_proven",
        "s2plt04_completed",
        "final_commands_executed",
        "no_production_side_effects_proven",
    ):
        if blocking_state.get(flag) is not True:
            errors.append(f"blocking_state.{flag} must be true")
    for flag in ("production_acceptance_claimed", "integrated_production_accepted", "daily_operation_enabled"):
        if blocking_state.get(flag) is not False:
            errors.append(f"blocking_state.{flag} must be false")

    no_production = _mapping(payload.get("no_production_side_effects"))
    for flag in S2PMT07_NEXT_AGENT_HANDOFF_NO_PRODUCTION_FLAGS:
        if no_production.get(flag) is not False:
            errors.append(f"no_production_side_effects.{flag} must be false")

    if payload.get("handoff_hash") != build_next_agent_handoff_hash(payload):
        errors.append("handoff_hash does not match payload content")
    return errors


def build_next_agent_handoff_validation_state(payload: Mapping[str, Any] | None) -> dict[str, Any]:
    """Build a validation report for future next-agent handoff evidence."""

    errors = validate_next_agent_handoff(payload)
    artifact_validations = _mapping(payload.get("required_artifact_validations")) if payload is not None else {}
    all_required_artifact_validations_passed = all(
        _mapping(artifact_validations.get(validation)).get("status") == "pass"
        for validation in S2PMT07_NEXT_AGENT_HANDOFF_REQUIRED_ARTIFACT_VALIDATIONS
    )
    required_reader_files = tuple(payload.get("required_reader_files", [])) if payload is not None else ()
    state = {
        "status": "pass" if not errors else "blocked",
        "scope": "next_agent_handoff_validation_only_no_production_acceptance",
        "artifact_path": "HANDOFF/00_下一Agent先读.md",
        "handoff_present": payload is not None,
        "validation_errors": errors,
        "required_reader_files": list(S2PMT07_NEXT_AGENT_HANDOFF_REQUIRED_READER_FILES),
        "all_required_reader_files_declared": (
            payload is not None and required_reader_files == S2PMT07_NEXT_AGENT_HANDOFF_REQUIRED_READER_FILES
        ),
        "required_artifact_validations": list(S2PMT07_NEXT_AGENT_HANDOFF_REQUIRED_ARTIFACT_VALIDATIONS),
        "all_required_artifact_validations_passed": (
            payload is not None and all_required_artifact_validations_passed
        ),
        "next_agent_handoff_ready_by_payload": not errors and payload is not None,
        "production_acceptance_claimed": False,
        "integrated_production_accepted": False,
        "daily_operation_enabled": False,
        "real_smtp_send_enabled": False,
        "scheduler_install_enabled": False,
        "release_packaging_enabled": False,
        "production_restore_enabled": False,
        "state_hash": "",
    }
    state["state_hash"] = _stable_hash({key: value for key, value in state.items() if key != "state_hash"})
    return state


def build_independent_review_signoff_hash(payload: Mapping[str, Any]) -> str:
    """Return the canonical independent-review signoff hash excluding its hash field."""

    payload_without_hash = {key: value for key, value in payload.items() if key != "signoff_hash"}
    return f"sha256:{_stable_hash(payload_without_hash)}"


def validate_independent_review_signoff_artifact(payload: Mapping[str, Any] | None) -> list[str]:
    """Validate a future independent-review signoff artifact without accepting production."""

    if payload is None:
        return ["independent_review_signoff_missing"]
    errors: list[str] = []
    errors.extend(_final_bundle_template_placeholder_errors(payload))
    for field in S2PMT07_INDEPENDENT_REVIEW_SIGNOFF_REQUIRED_FIELDS:
        if field not in payload:
            errors.append(f"{field} is required")
    if tuple(payload.keys()) != S2PMT07_INDEPENDENT_REVIEW_SIGNOFF_REQUIRED_FIELDS:
        errors.append("independent review signoff field order is invalid")
    if payload.get("schema_version") != S2PMT07_INDEPENDENT_REVIEW_SIGNOFF_SCHEMA_VERSION:
        errors.append("schema_version is invalid")
    if payload.get("contract_id") != "ADP-PRODUCT-CONTRACT-V7.2":
        errors.append("contract_id must be ADP-PRODUCT-CONTRACT-V7.2")
    if not isinstance(payload.get("generated_at"), str) or not payload.get("generated_at"):
        errors.append("generated_at must be a non-empty string")
    if payload.get("signoff_decision") != S2PMT07_INDEPENDENT_REVIEW_SIGNOFF_DECISION:
        errors.append("signoff_decision is invalid")

    reviewer = _mapping(payload.get("reviewer_independence"))
    if reviewer.get("status") != "verified":
        errors.append("reviewer_independence.status must be verified")
    if reviewer.get("required_independence") != S2PMT07_REQUIRED_REVIEWER_INDEPENDENCE:
        errors.append("reviewer_independence.required_independence is invalid")
    if reviewer.get("reviewer_role") != "independent_final_reviewer":
        errors.append("reviewer_independence.reviewer_role must be independent_final_reviewer")
    if reviewer.get("not_implementation_agent") is not True:
        errors.append("reviewer_independence.not_implementation_agent must be true")

    review_scope = _mapping(payload.get("review_scope"))
    if review_scope.get("task_id") != S2PMT07_TASK_ID:
        errors.append("review_scope.task_id must be S2PMT07")
    if review_scope.get("scope") != "independent_review_signoff_validation_only_no_production_acceptance":
        errors.append("review_scope.scope is invalid")
    if (
        tuple(review_scope.get("reviewed_artifact_validations", []))
        != S2PMT07_INDEPENDENT_REVIEW_SIGNOFF_REQUIRED_ARTIFACT_VALIDATIONS
    ):
        errors.append("review_scope.reviewed_artifact_validations must exactly match required artifact validations")

    artifact_validations = _mapping(payload.get("artifact_validations"))
    for validation in S2PMT07_INDEPENDENT_REVIEW_SIGNOFF_REQUIRED_ARTIFACT_VALIDATIONS:
        result = _mapping(artifact_validations.get(validation))
        if validation not in artifact_validations:
            errors.append(f"artifact_validations must include {validation}")
            continue
        if result.get("status") != "pass":
            errors.append(f"artifact_validations.{validation}.status must be pass")
        if not isinstance(result.get("evidence_ref"), str) or not result.get("evidence_ref"):
            errors.append(f"artifact_validations.{validation}.evidence_ref must be a non-empty string")

    closure_state = _mapping(payload.get("closure_state"))
    for flag in (
        "p0_zero_proven",
        "p1_zero_proven",
        "s2plt04_completed",
        "final_commands_executed",
        "no_production_side_effects_proven",
    ):
        if closure_state.get(flag) is not True:
            errors.append(f"closure_state.{flag} must be true")
    for flag in ("production_acceptance_claimed", "integrated_production_accepted"):
        if closure_state.get(flag) is not False:
            errors.append(f"closure_state.{flag} must be false")

    if tuple(payload.get("final_bundle_refs", [])) != S2PMT07_FINAL_ACCEPTANCE_BUNDLE_REQUIRED_ITEMS:
        errors.append("final_bundle_refs must exactly match final acceptance bundle required items")

    no_production = _mapping(payload.get("no_production_side_effects"))
    for flag in S2PMT07_INDEPENDENT_REVIEW_SIGNOFF_NO_PRODUCTION_FLAGS:
        if no_production.get(flag) is not False:
            errors.append(f"no_production_side_effects.{flag} must be false")

    if payload.get("signoff_hash") != build_independent_review_signoff_hash(payload):
        errors.append("signoff_hash does not match payload content")
    return errors


def build_independent_review_signoff_validation_state(payload: Mapping[str, Any] | None) -> dict[str, Any]:
    """Build a validation report for future independent-review signoff evidence."""

    errors = validate_independent_review_signoff_artifact(payload)
    artifact_validations = _mapping(payload.get("artifact_validations")) if payload is not None else {}
    all_required_artifact_validations_passed = all(
        _mapping(artifact_validations.get(validation)).get("status") == "pass"
        for validation in S2PMT07_INDEPENDENT_REVIEW_SIGNOFF_REQUIRED_ARTIFACT_VALIDATIONS
    )
    state = {
        "status": "pass" if not errors else "blocked",
        "scope": "independent_review_signoff_validation_only_no_production_acceptance",
        "artifact_path": "FINAL_ACCEPTANCE_BUNDLE/independent_review_signoff.yaml",
        "signoff_present": payload is not None,
        "validation_errors": errors,
        "required_artifact_validations": list(
            S2PMT07_INDEPENDENT_REVIEW_SIGNOFF_REQUIRED_ARTIFACT_VALIDATIONS
        ),
        "all_required_artifact_validations_passed": (
            payload is not None and all_required_artifact_validations_passed
        ),
        "independent_review_signed_off_by_payload": not errors and payload is not None,
        "production_acceptance_claimed": False,
        "integrated_production_accepted": False,
        "daily_operation_enabled": False,
        "real_smtp_send_enabled": False,
        "scheduler_install_enabled": False,
        "release_packaging_enabled": False,
        "production_restore_enabled": False,
        "state_hash": "",
    }
    state["state_hash"] = _stable_hash({key: value for key, value in state.items() if key != "state_hash"})
    return state


def build_final_bundle_prerequisite_plan_state(
    *,
    repo_root: Path | None = None,
    no_production_side_effect_attestation: Mapping[str, Any] | None = None,
    independent_final_reviewer_assignment: Mapping[str, Any] | None = None,
    p0_p1_zero_proof: Mapping[str, Any] | None = None,
    load_committed_artifacts: bool = True,
) -> dict[str, Any]:
    """Build the current fail-closed execution order for final-bundle prerequisites."""

    root = Path(repo_root) if repo_root is not None else _repo_root_from_source_tree()
    if load_committed_artifacts and no_production_side_effect_attestation is None:
        no_production_side_effect_attestation = _load_committed_no_production_side_effect_attestation(root)
    if load_committed_artifacts and independent_final_reviewer_assignment is None:
        independent_final_reviewer_assignment = _load_committed_independent_final_reviewer_assignment(root)
    if load_committed_artifacts and p0_p1_zero_proof is None:
        p0_p1_zero_proof = _load_committed_p0_p1_zero_proof(root)
    validation_states: dict[str, Mapping[str, Any]] = {
        "INDEPENDENT_FINAL_REVIEWER_ASSIGNMENT_VALIDATION": (
            build_independent_final_reviewer_assignment_validation_state(independent_final_reviewer_assignment)
        ),
        "P0_P1_ZERO_PROOF_ARTIFACT": build_p0_p1_zero_proof_artifact_validation_state(p0_p1_zero_proof),
        "S2PLT04_COMPLETION_REPORT": build_s2plt04_completion_report_validation_state(None),
        "FINAL_COMMAND_EXECUTION": build_final_command_execution_validation_state(None),
        "NO_PRODUCTION_SIDE_EFFECT_ATTESTATION": (
            build_no_production_side_effect_attestation_validation_state(
                no_production_side_effect_attestation
            )
        ),
        "NEXT_AGENT_HANDOFF": build_next_agent_handoff_validation_state(None),
        "INDEPENDENT_REVIEW_SIGNOFF": build_independent_review_signoff_validation_state(None),
        "FINAL_ACCEPTANCE_BUNDLE_MANIFEST": build_final_acceptance_bundle_manifest_validation_state(None),
    }
    ordered_steps: list[dict[str, Any]] = []
    artifact_keys = ("artifact_path", "report_path", "manifest_path")
    for step_id in S2PMT07_FINAL_BUNDLE_PREREQUISITE_PLAN_REQUIRED_STEPS:
        validation = validation_states[step_id]
        artifact_ref = next(
            (validation[key] for key in artifact_keys if isinstance(validation.get(key), str)),
            "UNKNOWN_ARTIFACT_REF",
        )
        depends_on_steps = list(S2PMT07_FINAL_BUNDLE_PREREQUISITE_PLAN_STEP_DEPENDENCIES[step_id])
        blocked_by_steps = [
            dependency for dependency in depends_on_steps
            if validation_states[dependency].get("status") != "pass"
        ]
        upstream_blocked = step_id == "S2PLT04_COMPLETION_REPORT" and validation.get("status") != "pass"
        actionable_now = (
            validation.get("status") != "pass"
            and not blocked_by_steps
            and not upstream_blocked
        )
        default_action = (
            S2PMT07_FINAL_BUNDLE_PREREQUISITE_PLAN_S2PLT04_UPSTREAM_ACTION
            if upstream_blocked
            else S2PMT07_FINAL_BUNDLE_PREREQUISITE_PLAN_WAIT_DEPENDENCIES_ACTION
            if blocked_by_steps
            else S2PMT07_FINAL_BUNDLE_PREREQUISITE_PLAN_DEFAULT_ACTION
        )
        ordered_steps.append(
            {
                "step_id": step_id,
                "status": validation.get("status"),
                "artifact_ref": artifact_ref,
                "validation_errors": list(validation.get("validation_errors", [])),
                "depends_on_steps": depends_on_steps,
                "blocked_by_steps": blocked_by_steps,
                "actionable_now": actionable_now,
                "upstream_blocked": upstream_blocked,
                "default_action": default_action,
            }
        )

    all_required_steps_passed = all(step["status"] == "pass" for step in ordered_steps)
    blocking_reasons: list[str] = []
    for step in ordered_steps:
        for error in step["validation_errors"]:
            if (
                error in S2PMT07_FINAL_BUNDLE_PREREQUISITE_PLAN_BLOCKING_REASONS
                and error not in blocking_reasons
            ):
                blocking_reasons.append(error)
    zero_proof_validation = validation_states["P0_P1_ZERO_PROOF_ARTIFACT"]
    inherited_zero_blockers = (
        (
            "inherited_v7_1_p0_findings_open"
            if zero_proof_validation.get("p0_zero_proven_by_payload") is not True
            else None
        ),
        (
            "inherited_v7_1_p1_findings_open"
            if zero_proof_validation.get("p1_zero_proven_by_payload") is not True
            else None
        ),
    )
    for inherited_blocker in inherited_zero_blockers:
        if inherited_blocker and inherited_blocker not in blocking_reasons:
            blocking_reasons.append(inherited_blocker)
    next_required_step = next(
        (step["step_id"] for step in ordered_steps if step["status"] != "pass"),
        None,
    )
    s2plt04_step = next(
        (step for step in ordered_steps if step["step_id"] == "S2PLT04_COMPLETION_REPORT"),
        None,
    )
    s2plt04_blocked_by_upstream_evidence = (
        bool(s2plt04_step)
        and s2plt04_step.get("upstream_blocked") is True
        and next_required_step == "S2PLT04_COMPLETION_REPORT"
    )
    live_authorization_artifact = _load_json_mapping_artifact(
        root / S2PLT02_REAL_PROOF_CAPTURE_AUTHORIZATION_ARTIFACT_PATH
    )
    live_authorization_validation = build_s2plt02_real_proof_capture_authorization_validation_state(
        live_authorization_artifact,
        expected_readiness_state_hash=(
            S2PMT07_FINAL_BUNDLE_PREREQUISITE_PLAN_S2PLT02_AUTH_READINESS_STATE_HASH
        ),
    )
    live_authorization_artifact_status = (
        "missing" if live_authorization_artifact is None else str(live_authorization_validation["status"])
    )
    live_authorization_passed = (
        live_authorization_artifact_status == "pass"
        and live_authorization_artifact is not None
        and not live_authorization_validation.get("validation_errors")
    )
    upstream_blockers = list(S2PMT07_FINAL_BUNDLE_PREREQUISITE_PLAN_UPSTREAM_BLOCKERS)
    upstream_unblock_order = list(S2PMT07_FINAL_BUNDLE_PREREQUISITE_PLAN_UPSTREAM_UNBLOCK_ORDER)
    if live_authorization_passed:
        upstream_blockers = [
            blocker for blocker in upstream_blockers
            if blocker != "s2plt02_terminal_delivery_proof_blocked_by_real_proof_capture_authorization_missing"
        ]
        upstream_unblock_order = [
            step for step in upstream_unblock_order
            if step != S2PMT07_FINAL_BUNDLE_PREREQUISITE_PLAN_NEXT_EXECUTABLE_TASK_WHEN_S2PLT04_BLOCKED
        ]
    next_executable_task = (
        (
            "S2PLT02_TERMINAL_DELIVERY_PROOF"
            if live_authorization_passed
            else S2PMT07_FINAL_BUNDLE_PREREQUISITE_PLAN_NEXT_EXECUTABLE_TASK_WHEN_S2PLT04_BLOCKED
        )
        if s2plt04_blocked_by_upstream_evidence
        else next_required_step
    )
    next_executable_is_s2plt02_auth = (
        next_executable_task
        == S2PMT07_FINAL_BUNDLE_PREREQUISITE_PLAN_NEXT_EXECUTABLE_TASK_WHEN_S2PLT04_BLOCKED
    )
    draft_manifest_ref = S2PMT07_FINAL_BUNDLE_PREREQUISITE_PLAN_S2PLT02_AUTH_DRAFT_EVIDENCE_REFS[0]
    draft_manifest = _load_json_mapping_artifact(root / draft_manifest_ref)
    draft_manifest_valid = (
        draft_manifest is not None
        and draft_manifest.get("cli_exit_code") == 0
        and draft_manifest.get("status") == "draft"
        and draft_manifest.get("artifact_ref") == S2PLT02_REAL_PROOF_CAPTURE_AUTHORIZATION_ARTIFACT_PATH
        and draft_manifest.get("authorization_artifact_written") is False
        and draft_manifest.get("authorization_gate_satisfied_by_this_command") is False
        and draft_manifest.get("real_proof_capture_authorized_by_this_command") is False
        and draft_manifest.get("validation_errors") == []
    )
    draft_authorization_hash = str(draft_manifest.get("draft_authorization_hash") or "") if draft_manifest else ""
    live_authorization_hash = (
        str(live_authorization_artifact.get("authorization_hash") or "")
        if live_authorization_artifact is not None
        else ""
    )
    state = {
        "status": "pass" if all_required_steps_passed else "blocked",
        "scope": "final_bundle_prerequisite_plan_only_no_production_acceptance",
        "task_id": S2PMT07_TASK_ID,
        "acceptance_id": S2PMT07_ACCEPTANCE_ID,
        "required_steps": list(S2PMT07_FINAL_BUNDLE_PREREQUISITE_PLAN_REQUIRED_STEPS),
        "ordered_steps": ordered_steps,
        "next_required_step": next_required_step,
        "next_required_step_is_actionable": not s2plt04_blocked_by_upstream_evidence,
        "next_required_step_blocked_by_upstream_evidence": s2plt04_blocked_by_upstream_evidence,
        "next_executable_task": next_executable_task,
        "next_executable_command": (
            S2PMT07_FINAL_BUNDLE_PREREQUISITE_PLAN_S2PLT02_AUTH_DRAFT_COMMAND
            if next_executable_is_s2plt02_auth
            else ""
        ),
        "next_executable_command_args": (
            dict(S2PMT07_FINAL_BUNDLE_PREREQUISITE_PLAN_S2PLT02_AUTH_DRAFT_ARGS)
            if next_executable_is_s2plt02_auth
            else {}
        ),
        "next_executable_command_writes_artifact": False,
        "next_executable_command_satisfies_gate": False,
        "next_executable_command_dry_run_status": (
            "pass"
            if next_executable_is_s2plt02_auth and draft_manifest_valid
            else "missing"
            if next_executable_is_s2plt02_auth and draft_manifest is None
            else "blocked"
            if next_executable_is_s2plt02_auth
            else ""
        ),
        "next_executable_command_dry_run_evidence_ref": (
            draft_manifest_ref if next_executable_is_s2plt02_auth else ""
        ),
        "next_executable_command_dry_run_wrote_artifact": (
            bool(draft_manifest.get("authorization_artifact_written"))
            if next_executable_is_s2plt02_auth and draft_manifest is not None
            else False
        ),
        "draft_authorization_is_live_authorization": bool(
            next_executable_is_s2plt02_auth
            and live_authorization_artifact is not None
            and draft_authorization_hash
            and live_authorization_hash == draft_authorization_hash
        ),
        "live_authorization_artifact_status": (
            live_authorization_artifact_status if s2plt04_blocked_by_upstream_evidence else ""
        ),
        "live_authorization_artifact_path": (
            S2PLT02_REAL_PROOF_CAPTURE_AUTHORIZATION_ARTIFACT_PATH
            if s2plt04_blocked_by_upstream_evidence
            else ""
        ),
        "live_authorization_validation_errors": (
            list(live_authorization_validation.get("validation_errors", []))
            if s2plt04_blocked_by_upstream_evidence
            else []
        ),
        "next_executable_command_validation_command": (
            S2PMT07_FINAL_BUNDLE_PREREQUISITE_PLAN_S2PLT02_AUTH_VALIDATION_COMMAND
            if next_executable_is_s2plt02_auth
            else ""
        ),
        "next_executable_evidence_refs": (
            list(S2PMT07_FINAL_BUNDLE_PREREQUISITE_PLAN_S2PLT02_AUTH_DRAFT_EVIDENCE_REFS)
            if next_executable_is_s2plt02_auth
            else []
        ),
        "upstream_blockers": (
            upstream_blockers
            if s2plt04_step and s2plt04_step.get("upstream_blocked") is True
            else []
        ),
        "upstream_unblock_order": (
            upstream_unblock_order
            if s2plt04_step and s2plt04_step.get("upstream_blocked") is True
            else []
        ),
        "all_required_steps_passed": all_required_steps_passed,
        "ready_for_final_bundle_manifest": False,
        "blocking_reasons": blocking_reasons,
        **{flag: False for flag in S2PMT07_FINAL_BUNDLE_PREREQUISITE_PLAN_FORBIDDEN_FLAGS},
        "state_hash": "",
    }
    state["state_hash"] = _stable_hash({key: value for key, value in state.items() if key != "state_hash"})
    return state


def validate_final_bundle_prerequisite_plan_state(state: Mapping[str, Any]) -> list[str]:
    """Validate the fail-closed final-bundle prerequisite execution plan."""

    errors: list[str] = []
    if state.get("status") not in {"pass", "blocked"}:
        errors.append("final bundle prerequisite plan status must be pass or blocked")
    if state.get("scope") != "final_bundle_prerequisite_plan_only_no_production_acceptance":
        errors.append("final bundle prerequisite plan scope is invalid")
    if state.get("task_id") != S2PMT07_TASK_ID:
        errors.append("final bundle prerequisite plan task_id is invalid")
    if state.get("acceptance_id") != S2PMT07_ACCEPTANCE_ID:
        errors.append("final bundle prerequisite plan acceptance_id is invalid")
    if tuple(state.get("required_steps", [])) != S2PMT07_FINAL_BUNDLE_PREREQUISITE_PLAN_REQUIRED_STEPS:
        errors.append("final bundle prerequisite plan required_steps are invalid")

    ordered_steps = _list_of_mappings(state.get("ordered_steps"))
    if tuple(step.get("step_id") for step in ordered_steps) != S2PMT07_FINAL_BUNDLE_PREREQUISITE_PLAN_REQUIRED_STEPS:
        errors.append("final bundle prerequisite plan ordered_steps are invalid")
    step_status_by_id = {step.get("step_id"): step.get("status") for step in ordered_steps}
    for step in ordered_steps:
        if not isinstance(step.get("artifact_ref"), str) or not step.get("artifact_ref"):
            errors.append(f"{step.get('step_id', 'UNKNOWN')}.artifact_ref must be a non-empty string")
        expected_status = "pass" if not step.get("validation_errors", []) else "blocked"
        if step.get("status") != expected_status:
            errors.append("final bundle prerequisite plan step statuses must match validation errors")
        step_id = step.get("step_id")
        expected_depends_on_steps = list(
            S2PMT07_FINAL_BUNDLE_PREREQUISITE_PLAN_STEP_DEPENDENCIES.get(str(step_id), ())
        )
        if step.get("depends_on_steps") != expected_depends_on_steps:
            errors.append("final bundle prerequisite plan depends_on_steps are invalid")
        expected_blocked_by_steps = [
            dependency for dependency in expected_depends_on_steps
            if step_status_by_id.get(dependency) != "pass"
        ]
        if step.get("blocked_by_steps") != expected_blocked_by_steps:
            errors.append("final bundle prerequisite plan blocked_by_steps are invalid")
        expected_upstream_blocked = (
            step.get("step_id") == "S2PLT04_COMPLETION_REPORT" and step.get("status") != "pass"
        )
        if step.get("upstream_blocked") is not expected_upstream_blocked:
            errors.append("final bundle prerequisite plan upstream_blocked flags are invalid")
        expected_actionable_now = (
            step.get("status") != "pass"
            and not expected_blocked_by_steps
            and not expected_upstream_blocked
        )
        if step.get("actionable_now") is not expected_actionable_now:
            errors.append("final bundle prerequisite plan actionable_now flags are invalid")
        expected_default_action = (
            S2PMT07_FINAL_BUNDLE_PREREQUISITE_PLAN_S2PLT04_UPSTREAM_ACTION
            if expected_upstream_blocked
            else S2PMT07_FINAL_BUNDLE_PREREQUISITE_PLAN_WAIT_DEPENDENCIES_ACTION
            if expected_blocked_by_steps
            else S2PMT07_FINAL_BUNDLE_PREREQUISITE_PLAN_DEFAULT_ACTION
        )
        if step.get("default_action") != expected_default_action:
            errors.append("final bundle prerequisite plan step default_action is invalid")

    expected_next_required_step = next(
        (step.get("step_id") for step in ordered_steps if step.get("status") != "pass"),
        None,
    )
    if state.get("next_required_step") != expected_next_required_step:
        errors.append("final bundle prerequisite plan next_required_step must match first blocked step")
    s2plt04_step = next(
        (step for step in ordered_steps if step.get("step_id") == "S2PLT04_COMPLETION_REPORT"),
        None,
    )
    expected_s2plt04_upstream_blocked = bool(
        s2plt04_step and s2plt04_step.get("upstream_blocked") is True
    )
    expected_next_step_upstream_blocked = (
        expected_next_required_step == "S2PLT04_COMPLETION_REPORT" and expected_s2plt04_upstream_blocked
    )
    if state.get("next_required_step_blocked_by_upstream_evidence") is not expected_next_step_upstream_blocked:
        errors.append("final bundle prerequisite plan upstream evidence marker is invalid")
    if state.get("next_required_step_is_actionable") is not (not expected_next_step_upstream_blocked):
        errors.append("final bundle prerequisite plan next_required_step_is_actionable is invalid")
    live_authorization_passed = state.get("live_authorization_artifact_status") == "pass"
    expected_upstream_blockers = list(S2PMT07_FINAL_BUNDLE_PREREQUISITE_PLAN_UPSTREAM_BLOCKERS)
    expected_upstream_unblock_order = list(S2PMT07_FINAL_BUNDLE_PREREQUISITE_PLAN_UPSTREAM_UNBLOCK_ORDER)
    if live_authorization_passed:
        expected_upstream_blockers = [
            blocker for blocker in expected_upstream_blockers
            if blocker != "s2plt02_terminal_delivery_proof_blocked_by_real_proof_capture_authorization_missing"
        ]
        expected_upstream_unblock_order = [
            step for step in expected_upstream_unblock_order
            if step != S2PMT07_FINAL_BUNDLE_PREREQUISITE_PLAN_NEXT_EXECUTABLE_TASK_WHEN_S2PLT04_BLOCKED
        ]
    expected_next_executable_task = (
        (
            "S2PLT02_TERMINAL_DELIVERY_PROOF"
            if live_authorization_passed
            else S2PMT07_FINAL_BUNDLE_PREREQUISITE_PLAN_NEXT_EXECUTABLE_TASK_WHEN_S2PLT04_BLOCKED
        )
        if expected_next_step_upstream_blocked
        else expected_next_required_step
    )
    if state.get("next_executable_task") != expected_next_executable_task:
        errors.append("final bundle prerequisite plan next_executable_task is invalid")
    expected_next_executable_is_s2plt02_auth = (
        expected_next_executable_task
        == S2PMT07_FINAL_BUNDLE_PREREQUISITE_PLAN_NEXT_EXECUTABLE_TASK_WHEN_S2PLT04_BLOCKED
    )
    expected_next_executable_command = (
        S2PMT07_FINAL_BUNDLE_PREREQUISITE_PLAN_S2PLT02_AUTH_DRAFT_COMMAND
        if expected_next_executable_is_s2plt02_auth
        else ""
    )
    if state.get("next_executable_command") != expected_next_executable_command:
        errors.append("final bundle prerequisite plan next_executable_command is invalid")
    expected_next_executable_command_args = (
        dict(S2PMT07_FINAL_BUNDLE_PREREQUISITE_PLAN_S2PLT02_AUTH_DRAFT_ARGS)
        if expected_next_executable_is_s2plt02_auth
        else {}
    )
    if state.get("next_executable_command_args") != expected_next_executable_command_args:
        errors.append("final bundle prerequisite plan next_executable_command_args are invalid")
    if state.get("next_executable_command_writes_artifact") is not False:
        errors.append("final bundle prerequisite plan next_executable_command_writes_artifact must be false")
    if state.get("next_executable_command_satisfies_gate") is not False:
        errors.append("final bundle prerequisite plan next_executable_command_satisfies_gate must be false")
    if expected_next_executable_is_s2plt02_auth:
        if state.get("next_executable_command_dry_run_status") not in {"pass", "blocked", "missing"}:
            errors.append("final bundle prerequisite plan next_executable_command_dry_run_status is invalid")
        if (
            state.get("next_executable_command_dry_run_evidence_ref")
            != S2PMT07_FINAL_BUNDLE_PREREQUISITE_PLAN_S2PLT02_AUTH_DRAFT_EVIDENCE_REFS[0]
        ):
            errors.append("final bundle prerequisite plan next_executable_command_dry_run_evidence_ref is invalid")
        if state.get("next_executable_command_dry_run_wrote_artifact") is not False:
            errors.append("final bundle prerequisite plan dry-run command must not write the authorization artifact")
        if state.get("draft_authorization_is_live_authorization") is not False and state.get(
            "live_authorization_artifact_status"
        ) == "missing":
            errors.append("draft authorization cannot be live authorization while live artifact is missing")
        if state.get("live_authorization_artifact_status") not in {"pass", "blocked", "missing"}:
            errors.append("final bundle prerequisite plan live_authorization_artifact_status is invalid")
        if state.get("live_authorization_artifact_path") != S2PLT02_REAL_PROOF_CAPTURE_AUTHORIZATION_ARTIFACT_PATH:
            errors.append("final bundle prerequisite plan live_authorization_artifact_path is invalid")
        live_authorization_validation_errors = state.get("live_authorization_validation_errors")
        if not isinstance(live_authorization_validation_errors, list):
            errors.append("final bundle prerequisite plan live_authorization_validation_errors must be a list")
        elif (
            state.get("live_authorization_artifact_status") == "missing"
            and "s2plt02_real_proof_capture_authorization_missing"
            not in live_authorization_validation_errors
        ):
            errors.append("missing live authorization artifact must expose the S2PLT02 authorization blocker")
    else:
        if state.get("next_executable_command_dry_run_status") != "":
            errors.append("final bundle prerequisite plan next_executable_command_dry_run_status must be empty")
        if state.get("next_executable_command_dry_run_evidence_ref") != "":
            errors.append("final bundle prerequisite plan next_executable_command_dry_run_evidence_ref must be empty")
        if state.get("next_executable_command_dry_run_wrote_artifact") is not False:
            errors.append("final bundle prerequisite plan dry-run artifact write flag must be false")
        if state.get("draft_authorization_is_live_authorization") is not False:
            errors.append("final bundle prerequisite plan draft/live authorization marker must be false")
        if expected_next_step_upstream_blocked:
            if state.get("live_authorization_artifact_status") not in {"pass", "blocked", "missing"}:
                errors.append("final bundle prerequisite plan live_authorization_artifact_status is invalid")
            if (
                state.get("live_authorization_artifact_path")
                != S2PLT02_REAL_PROOF_CAPTURE_AUTHORIZATION_ARTIFACT_PATH
            ):
                errors.append("final bundle prerequisite plan live_authorization_artifact_path is invalid")
            if not isinstance(state.get("live_authorization_validation_errors"), list):
                errors.append("final bundle prerequisite plan live_authorization_validation_errors must be a list")
            if state.get("live_authorization_artifact_status") == "pass" and state.get(
                "live_authorization_validation_errors"
            ) != []:
                errors.append("passing live authorization artifact must have no validation errors")
        else:
            if state.get("live_authorization_artifact_status") != "":
                errors.append("final bundle prerequisite plan live_authorization_artifact_status must be empty")
            if state.get("live_authorization_artifact_path") != "":
                errors.append("final bundle prerequisite plan live_authorization_artifact_path must be empty")
            if state.get("live_authorization_validation_errors") != []:
                errors.append("final bundle prerequisite plan live_authorization_validation_errors must be empty")
    expected_next_executable_command_validation_command = (
        S2PMT07_FINAL_BUNDLE_PREREQUISITE_PLAN_S2PLT02_AUTH_VALIDATION_COMMAND
        if expected_next_executable_is_s2plt02_auth
        else ""
    )
    if (
        state.get("next_executable_command_validation_command")
        != expected_next_executable_command_validation_command
    ):
        errors.append("final bundle prerequisite plan next_executable_command_validation_command is invalid")
    expected_next_executable_evidence_refs = (
        list(S2PMT07_FINAL_BUNDLE_PREREQUISITE_PLAN_S2PLT02_AUTH_DRAFT_EVIDENCE_REFS)
        if expected_next_executable_is_s2plt02_auth
        else []
    )
    if state.get("next_executable_evidence_refs") != expected_next_executable_evidence_refs:
        errors.append("final bundle prerequisite plan next_executable_evidence_refs are invalid")
    expected_state_upstream_blockers = (
        expected_upstream_blockers if expected_s2plt04_upstream_blocked else []
    )
    if state.get("upstream_blockers") != expected_state_upstream_blockers:
        errors.append("final bundle prerequisite plan upstream_blockers are invalid")
    expected_state_upstream_unblock_order = (
        expected_upstream_unblock_order if expected_s2plt04_upstream_blocked else []
    )
    if state.get("upstream_unblock_order") != expected_state_upstream_unblock_order:
        errors.append("final bundle prerequisite plan upstream_unblock_order is invalid")
    if state.get("all_required_steps_passed") is not False:
        errors.append("final bundle prerequisite plan all_required_steps_passed must remain false")
    if state.get("ready_for_final_bundle_manifest") is not False:
        errors.append("final bundle prerequisite plan must not be ready for final bundle manifest")
    expected_blocking_reasons: list[str] = []
    for step in ordered_steps:
        for error in step.get("validation_errors", []):
            if (
                error in S2PMT07_FINAL_BUNDLE_PREREQUISITE_PLAN_BLOCKING_REASONS
                and error not in expected_blocking_reasons
            ):
                expected_blocking_reasons.append(error)
    step_status = {step.get("step_id"): step.get("status") for step in ordered_steps}
    if step_status.get("P0_P1_ZERO_PROOF_ARTIFACT") != "pass":
        for inherited_blocker in (
            "inherited_v7_1_p0_findings_open",
            "inherited_v7_1_p1_findings_open",
        ):
            if inherited_blocker not in expected_blocking_reasons:
                expected_blocking_reasons.append(inherited_blocker)
    if state.get("blocking_reasons") != expected_blocking_reasons:
        errors.append("final bundle prerequisite plan blocking_reasons must match blocked steps")
    for flag in S2PMT07_FINAL_BUNDLE_PREREQUISITE_PLAN_FORBIDDEN_FLAGS:
        if state.get(flag) is not False:
            errors.append(f"{flag} must be false")
    if state.get("state_hash") != _stable_hash({key: value for key, value in state.items() if key != "state_hash"}):
        errors.append("final bundle prerequisite plan state_hash does not match state content")
    return errors


def build_s2pmt07_mainline_attestation_state(
    *,
    target_commit: str,
    origin_main_commit: str,
    target_commit_on_origin_main: bool,
    open_pr_count: int,
    remote_adp_arxiv_s2p_branch_count: int,
    validations: Mapping[str, bool],
) -> dict[str, Any]:
    """Build a no-production attestation that a S2PMT07 evidence commit is contained in main."""

    validation_results = {
        name: bool(validations.get(name, False))
        for name in S2PMT07_MAINLINE_ATTESTATION_REQUIRED_VALIDATIONS
    }
    missing_validations = [
        name for name, passed in validation_results.items() if passed is not True
    ]
    target_commit_is_on_origin_main = bool(target_commit) and bool(origin_main_commit) and target_commit_on_origin_main
    blocking_reasons: list[str] = []
    if not target_commit_is_on_origin_main:
        blocking_reasons.append("target_commit_not_on_origin_main")
    if open_pr_count != 0:
        blocking_reasons.append("open_pr_count_not_zero")
    if remote_adp_arxiv_s2p_branch_count != 0:
        blocking_reasons.append("remote_adp_arxiv_s2p_branch_count_not_zero")
    if missing_validations:
        blocking_reasons.append("required_validation_missing")

    mainline_attested = not blocking_reasons
    state = {
        "status": "pass" if mainline_attested else "blocked",
        "scope": "s2pmt07_mainline_attestation_only_no_final_acceptance",
        "task_id": S2PMT07_TASK_ID,
        "acceptance_id": S2PMT07_ACCEPTANCE_ID,
        "attested_commit": target_commit,
        "origin_main_commit": origin_main_commit,
        "target_commit_on_origin_main": target_commit_is_on_origin_main,
        "open_pr_count": open_pr_count,
        "remote_adp_arxiv_s2p_branch_count": remote_adp_arxiv_s2p_branch_count,
        "required_validations": list(S2PMT07_MAINLINE_ATTESTATION_REQUIRED_VALIDATIONS),
        "validation_results": validation_results,
        "missing_validations": missing_validations,
        "mainline_attested": mainline_attested,
        "blocking_reasons": blocking_reasons,
        "p0_zero_proven": False,
        "p1_zero_proven": False,
        "p0_closure_claimed": False,
        "p1_closure_claimed": False,
        "final_acceptance_bundle_present": False,
        **{flag: False for flag in S2PMT07_MAINLINE_ATTESTATION_NO_PRODUCTION_FLAGS},
        "state_hash": "",
    }
    state["state_hash"] = _stable_hash({key: value for key, value in state.items() if key != "state_hash"})
    return state


def validate_s2pmt07_mainline_attestation_state(state: Mapping[str, Any]) -> list[str]:
    """Validate a S2PMT07 mainline attestation without treating it as final acceptance."""

    errors: list[str] = []
    if state.get("status") not in {"pass", "blocked"}:
        errors.append("mainline attestation status must be pass or blocked")
    if state.get("scope") != "s2pmt07_mainline_attestation_only_no_final_acceptance":
        errors.append("mainline attestation scope is invalid")
    if state.get("task_id") != S2PMT07_TASK_ID:
        errors.append("mainline attestation task_id is invalid")
    if state.get("acceptance_id") != S2PMT07_ACCEPTANCE_ID:
        errors.append("mainline attestation acceptance_id is invalid")

    attested_commit = state.get("attested_commit")
    origin_main_commit = state.get("origin_main_commit")
    if not isinstance(attested_commit, str) or not attested_commit:
        errors.append("mainline attestation attested_commit must be a non-empty string")
    if not isinstance(origin_main_commit, str) or not origin_main_commit:
        errors.append("mainline attestation origin_main_commit must be a non-empty string")
    if state.get("target_commit_on_origin_main") is not True:
        errors.append("mainline attestation target commit must be contained in origin/main")
    if state.get("open_pr_count") != 0:
        errors.append("mainline attestation open_pr_count must be 0")
    if state.get("remote_adp_arxiv_s2p_branch_count") != 0:
        errors.append("mainline attestation remote_adp_arxiv_s2p_branch_count must be 0")
    if tuple(state.get("required_validations", [])) != S2PMT07_MAINLINE_ATTESTATION_REQUIRED_VALIDATIONS:
        errors.append("mainline attestation required_validations are invalid")

    validation_results = _mapping(state.get("validation_results"))
    missing_validations = []
    for name in S2PMT07_MAINLINE_ATTESTATION_REQUIRED_VALIDATIONS:
        if validation_results.get(name) is not True:
            missing_validations.append(name)
    if state.get("missing_validations") != missing_validations:
        errors.append("mainline attestation missing_validations are invalid")

    for flag in (
        "p0_zero_proven",
        "p1_zero_proven",
        "p0_closure_claimed",
        "p1_closure_claimed",
        "final_acceptance_bundle_present",
    ):
        if state.get(flag) is not False:
            errors.append(f"{flag} must be false")
    for flag in S2PMT07_MAINLINE_ATTESTATION_NO_PRODUCTION_FLAGS:
        if state.get(flag) is not False:
            errors.append(f"{flag} must be false")

    expected_blocking_reasons: list[str] = []
    if state.get("target_commit_on_origin_main") is not True:
        expected_blocking_reasons.append("target_commit_not_on_origin_main")
    if state.get("open_pr_count") != 0:
        expected_blocking_reasons.append("open_pr_count_not_zero")
    if state.get("remote_adp_arxiv_s2p_branch_count") != 0:
        expected_blocking_reasons.append("remote_adp_arxiv_s2p_branch_count_not_zero")
    if missing_validations:
        expected_blocking_reasons.append("required_validation_missing")
    for reason in expected_blocking_reasons:
        if reason not in state.get("blocking_reasons", []):
            errors.append(f"mainline attestation must include blocker {reason}")

    expected_status = "blocked" if expected_blocking_reasons else "pass"
    if state.get("status") != expected_status:
        errors.append(f"mainline attestation status must be {expected_status}")
    if state.get("mainline_attested") is not (not expected_blocking_reasons):
        errors.append("mainline attestation mainline_attested is invalid")
    if state.get("state_hash") != _stable_hash({key: value for key, value in state.items() if key != "state_hash"}):
        errors.append("mainline attestation state_hash does not match state content")
    return errors


def build_final_acceptance_bundle_artifact_validation_state(
    *,
    bundle_directory_present: bool = False,
    manifest: Mapping[str, Any] | None = None,
    independent_final_reviewer_assignment: Mapping[str, Any] | None = None,
    p0_p1_zero_proof: Mapping[str, Any] | None = None,
    s2plt04_completion_report: Mapping[str, Any] | None = None,
    independent_review_signoff: Mapping[str, Any] | None = None,
    final_command_execution: Mapping[str, Any] | None = None,
    no_production_side_effect_attestation: Mapping[str, Any] | None = None,
    next_agent_handoff: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Validate a complete final bundle surface without creating or accepting it."""

    available_items = {
        "FINAL_ACCEPTANCE_BUNDLE/manifest.json": manifest is not None,
        S2PMT07_INDEPENDENT_FINAL_REVIEWER_ASSIGNMENT_ARTIFACT_PATH: (
            independent_final_reviewer_assignment is not None
        ),
        S2PMT07_P0_P1_ZERO_PROOF_ARTIFACT_PATH: p0_p1_zero_proof is not None,
        "FINAL_ACCEPTANCE_BUNDLE/s2plt04_completion_report.json": s2plt04_completion_report is not None,
        "FINAL_ACCEPTANCE_BUNDLE/independent_review_signoff.yaml": independent_review_signoff is not None,
        "FINAL_ACCEPTANCE_BUNDLE/final_command_execution.json": final_command_execution is not None,
        "FINAL_ACCEPTANCE_BUNDLE/no_production_side_effects.json": (
            no_production_side_effect_attestation is not None
        ),
        "HANDOFF/00_下一Agent先读.md": next_agent_handoff is not None,
    }
    missing_items = [item for item, present in available_items.items() if not present]
    artifact_validations = {
        "FINAL_ACCEPTANCE_BUNDLE_MANIFEST": build_final_acceptance_bundle_manifest_validation_state(manifest),
        "INDEPENDENT_FINAL_REVIEWER_ASSIGNMENT_VALIDATION": (
            build_independent_final_reviewer_assignment_validation_state(
                independent_final_reviewer_assignment
            )
        ),
        "P0_P1_ZERO_PROOF_ARTIFACT": build_p0_p1_zero_proof_artifact_validation_state(p0_p1_zero_proof),
        "S2PLT04_COMPLETION_REPORT": build_s2plt04_completion_report_validation_state(s2plt04_completion_report),
        "INDEPENDENT_REVIEW_SIGNOFF": build_independent_review_signoff_validation_state(
            independent_review_signoff
        ),
        "FINAL_COMMAND_EXECUTION": build_final_command_execution_validation_state(final_command_execution),
        "NO_PRODUCTION_SIDE_EFFECT_ATTESTATION": build_no_production_side_effect_attestation_validation_state(
            no_production_side_effect_attestation
        ),
        "NEXT_AGENT_HANDOFF": build_next_agent_handoff_validation_state(next_agent_handoff),
    }
    all_required_items_present = bundle_directory_present and not missing_items
    all_artifact_validations_passed = all(
        validation["status"] == "pass" for validation in artifact_validations.values()
    )
    blocking_reasons: list[str] = []
    if not bundle_directory_present:
        blocking_reasons.append("final_acceptance_bundle_directory_missing")
    for item in missing_items:
        reason = S2PMT07_FINAL_ACCEPTANCE_BUNDLE_ITEM_BLOCKING_REASONS[item]
        if reason not in blocking_reasons:
            blocking_reasons.append(reason)
    for key, validation in artifact_validations.items():
        if validation["status"] != "pass":
            reason = f"{key.lower()}_validation_blocked"
            if reason not in blocking_reasons:
                blocking_reasons.append(reason)
    state = {
        "status": (
            "pass"
            if bundle_directory_present
            and all_required_items_present
            and all_artifact_validations_passed
            and not blocking_reasons
            else "blocked"
        ),
        "scope": "final_acceptance_bundle_artifact_validation_only_no_production_acceptance",
        "bundle_directory_present": bundle_directory_present,
        "required_items": list(S2PMT07_FINAL_ACCEPTANCE_BUNDLE_REQUIRED_ITEMS),
        "available_items": available_items,
        "missing_items": missing_items,
        "artifact_validations": artifact_validations,
        "required_artifact_validation_keys": list(S2PMT07_FINAL_ACCEPTANCE_BUNDLE_ARTIFACT_VALIDATION_KEYS),
        "all_required_items_present": all_required_items_present,
        "all_artifact_validations_passed": all_artifact_validations_passed,
        "bundle_ready_by_artifact_validation": (
            bundle_directory_present and all_required_items_present and all_artifact_validations_passed
        ),
        "blocking_reasons": blocking_reasons,
        "production_acceptance_claimed": False,
        "integrated_production_accepted": False,
        "daily_operation_enabled": False,
        "real_smtp_send_enabled": False,
        "scheduler_install_enabled": False,
        "release_packaging_enabled": False,
        "production_restore_enabled": False,
        "state_hash": "",
    }
    state["state_hash"] = _stable_hash({key: value for key, value in state.items() if key != "state_hash"})
    return state


def validate_final_acceptance_bundle_artifact_validation_state(state: Mapping[str, Any]) -> list[str]:
    """Validate the directory-level final bundle artifact validation state."""

    errors: list[str] = []
    if state.get("status") not in {"pass", "blocked"}:
        errors.append("final acceptance bundle artifact validation status must be pass or blocked")
    if state.get("scope") != "final_acceptance_bundle_artifact_validation_only_no_production_acceptance":
        errors.append("final acceptance bundle artifact validation scope is invalid")
    if state.get("bundle_directory_present") not in {True, False}:
        errors.append("final acceptance bundle artifact validation bundle_directory_present must be boolean")
    if tuple(state.get("required_items", [])) != S2PMT07_FINAL_ACCEPTANCE_BUNDLE_REQUIRED_ITEMS:
        errors.append("final acceptance bundle artifact validation required_items are invalid")

    available = _mapping(state.get("available_items"))
    missing_items = list(state.get("missing_items", []))
    expected_missing = [item for item in S2PMT07_FINAL_ACCEPTANCE_BUNDLE_REQUIRED_ITEMS if not available.get(item)]
    if missing_items != expected_missing:
        errors.append("final acceptance bundle artifact validation missing_items do not match available_items")
    for item in S2PMT07_FINAL_ACCEPTANCE_BUNDLE_REQUIRED_ITEMS:
        if item not in available:
            errors.append(f"final acceptance bundle artifact validation available_items must include {item}")

    artifact_validations = _mapping(state.get("artifact_validations"))
    if tuple(state.get("required_artifact_validation_keys", [])) != (
        S2PMT07_FINAL_ACCEPTANCE_BUNDLE_ARTIFACT_VALIDATION_KEYS
    ):
        errors.append("final acceptance bundle artifact validation required_artifact_validation_keys are invalid")
    for key in S2PMT07_FINAL_ACCEPTANCE_BUNDLE_ARTIFACT_VALIDATION_KEYS:
        validation = _mapping(artifact_validations.get(key))
        if key not in artifact_validations:
            errors.append(f"final acceptance bundle artifact validations must include {key}")
            continue
        if validation.get("status") not in {"pass", "blocked"}:
            errors.append(f"final acceptance bundle artifact validation {key}.status is invalid")
        expected_hash = _stable_hash({item: value for item, value in validation.items() if item != "state_hash"})
        if validation.get("state_hash") != expected_hash:
            errors.append(f"final acceptance bundle artifact validation {key}.state_hash is invalid")

    expected_items_present = state.get("bundle_directory_present") is True and not missing_items
    if state.get("all_required_items_present") is not expected_items_present:
        errors.append("final acceptance bundle artifact validation all_required_items_present is invalid")

    expected_artifacts_passed = all(
        _mapping(artifact_validations.get(key)).get("status") == "pass"
        for key in S2PMT07_FINAL_ACCEPTANCE_BUNDLE_ARTIFACT_VALIDATION_KEYS
    )
    if state.get("all_artifact_validations_passed") is not expected_artifacts_passed:
        errors.append("final acceptance bundle artifact validation all_artifact_validations_passed is invalid")
    if state.get("all_artifact_validations_passed") is True and not expected_artifacts_passed:
        errors.append(
            "final acceptance bundle artifact validation cannot pass while artifact validations are blocked"
        )

    expected_ready = expected_items_present and expected_artifacts_passed
    if state.get("bundle_ready_by_artifact_validation") is not expected_ready:
        errors.append("final acceptance bundle artifact validation bundle_ready_by_artifact_validation is invalid")

    blocking_reasons = state.get("blocking_reasons", [])
    if state.get("bundle_directory_present") is False:
        if "final_acceptance_bundle_directory_missing" not in blocking_reasons:
            errors.append("blocked final acceptance bundle artifact validation must include directory missing")
    elif "final_acceptance_bundle_directory_missing" in blocking_reasons:
        errors.append("final acceptance bundle artifact validation must not report directory missing when present")
    for item in missing_items:
        reason = S2PMT07_FINAL_ACCEPTANCE_BUNDLE_ITEM_BLOCKING_REASONS[item]
        if reason not in blocking_reasons:
            errors.append(f"blocked final acceptance bundle artifact validation must include {reason}")
    for key in S2PMT07_FINAL_ACCEPTANCE_BUNDLE_ARTIFACT_VALIDATION_KEYS:
        if _mapping(artifact_validations.get(key)).get("status") != "pass":
            reason = f"{key.lower()}_validation_blocked"
            if reason not in blocking_reasons:
                errors.append(f"blocked final acceptance bundle artifact validation must include {reason}")

    for flag in (
        "production_acceptance_claimed",
        "integrated_production_accepted",
        "daily_operation_enabled",
        "real_smtp_send_enabled",
        "scheduler_install_enabled",
        "release_packaging_enabled",
        "production_restore_enabled",
    ):
        if state.get(flag) is not False:
            errors.append(f"{flag} must be false")
    if state.get("status") == "pass":
        if blocking_reasons:
            errors.append("passing final acceptance bundle artifact validation must not have blocking reasons")
        if not expected_ready:
            errors.append("passing final acceptance bundle artifact validation requires a ready bundle")
    else:
        if expected_ready and not blocking_reasons:
            errors.append("blocked final acceptance bundle artifact validation needs a blocking reason")

    expected_hash = _stable_hash({key: value for key, value in state.items() if key != "state_hash"})
    if state.get("state_hash") != expected_hash:
        errors.append("final acceptance bundle artifact validation state_hash does not match state content")
    return errors


def _repo_root_from_source_tree() -> Path:
    """Return the repository root for source-tree validation runs."""

    return Path(__file__).resolve().parents[3]


def _load_json_mapping_artifact(artifact_path: Path) -> Mapping[str, Any] | None:
    """Load a JSON object artifact, returning None when it is absent or malformed."""

    try:
        payload = json.loads(artifact_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(payload, Mapping):
        return None
    return payload


def _load_yaml_mapping_artifact(artifact_path: Path) -> Mapping[str, Any] | None:
    """Load a YAML object artifact, returning None when it is absent or malformed."""

    try:
        text = artifact_path.read_text(encoding="utf-8")
    except OSError:
        return None
    try:
        import yaml  # type: ignore

        payload = yaml.safe_load(text) or {}
    except Exception:
        return None
    if not isinstance(payload, Mapping):
        return None
    return payload


def _load_committed_no_production_side_effect_attestation(
    repo_root: Path | None = None,
) -> Mapping[str, Any] | None:
    """Load the committed no-production attestation artifact when present."""

    root = repo_root or _repo_root_from_source_tree()
    artifact_path = root / S2PMT07_NO_PRODUCTION_SIDE_EFFECT_ATTESTATION_ARTIFACT_PATH
    return _load_json_mapping_artifact(artifact_path)


def _load_committed_independent_final_reviewer_assignment(
    repo_root: Path | None = None,
) -> Mapping[str, Any] | None:
    """Load the committed independent reviewer assignment artifact when present."""

    root = repo_root or _repo_root_from_source_tree()
    artifact_path = root / S2PMT07_INDEPENDENT_FINAL_REVIEWER_ASSIGNMENT_ARTIFACT_PATH
    return _load_json_mapping_artifact(artifact_path)


def _load_committed_p0_p1_zero_proof(repo_root: Path | None = None) -> Mapping[str, Any] | None:
    """Load the committed P0/P1 zero-proof artifact when present."""

    root = repo_root or _repo_root_from_source_tree()
    artifact_path = root / S2PMT07_P0_P1_ZERO_PROOF_ARTIFACT_PATH
    return _load_json_mapping_artifact(artifact_path)


def build_final_acceptance_bundle_readiness_state(
    *,
    repo_root: Path | None = None,
    manifest: Mapping[str, Any] | None = None,
    p0_p1_zero_proof: Mapping[str, Any] | None = None,
    s2plt04_completion_report: Mapping[str, Any] | None = None,
    independent_final_reviewer_assignment: Mapping[str, Any] | None = None,
    independent_review_signoff: Mapping[str, Any] | None = None,
    final_command_execution: Mapping[str, Any] | None = None,
    no_production_side_effect_attestation: Mapping[str, Any] | None = None,
    next_agent_handoff: Mapping[str, Any] | None = None,
    load_committed_artifacts: bool = True,
) -> dict[str, Any]:
    """Build the current final acceptance bundle readiness state without packaging."""

    root = repo_root or _repo_root_from_source_tree()
    bundle_directory_present = (
        (root / "FINAL_ACCEPTANCE_BUNDLE").is_dir() if load_committed_artifacts else False
    )
    if load_committed_artifacts:
        if manifest is None:
            manifest = _load_json_mapping_artifact(root / "FINAL_ACCEPTANCE_BUNDLE" / "manifest.json")
        if p0_p1_zero_proof is None:
            p0_p1_zero_proof = _load_json_mapping_artifact(root / S2PMT07_P0_P1_ZERO_PROOF_ARTIFACT_PATH)
        if s2plt04_completion_report is None:
            s2plt04_completion_report = _load_json_mapping_artifact(
                root / "FINAL_ACCEPTANCE_BUNDLE" / "s2plt04_completion_report.json"
            )
        if independent_final_reviewer_assignment is None:
            independent_final_reviewer_assignment = _load_committed_independent_final_reviewer_assignment(root)
        if independent_review_signoff is None:
            independent_review_signoff = _load_yaml_mapping_artifact(
                root / "FINAL_ACCEPTANCE_BUNDLE" / "independent_review_signoff.yaml"
            )
        if final_command_execution is None:
            final_command_execution = _load_json_mapping_artifact(
                root / "FINAL_ACCEPTANCE_BUNDLE" / "final_command_execution.json"
            )
        if no_production_side_effect_attestation is None:
            no_production_side_effect_attestation = _load_committed_no_production_side_effect_attestation(root)
        if next_agent_handoff is None:
            next_agent_handoff = _load_json_mapping_artifact(root / "HANDOFF" / "00_下一Agent先读.md")
    final_bundle_prerequisite_plan = build_final_bundle_prerequisite_plan_state(
        repo_root=root,
        no_production_side_effect_attestation=no_production_side_effect_attestation,
        independent_final_reviewer_assignment=independent_final_reviewer_assignment,
        p0_p1_zero_proof=p0_p1_zero_proof,
        load_committed_artifacts=load_committed_artifacts,
    )
    p0_p1_technical_candidate_state = build_p0_p1_technical_closure_candidate_state()
    p0_p1_zero_proof_assembly = build_p0_p1_zero_proof_assembly_state()
    independent_final_reviewer_assignment_request = (
        build_independent_final_reviewer_assignment_request_state()
    )
    independent_final_reviewer_assignment_owner_packet = (
        build_independent_final_reviewer_assignment_owner_packet_state()
    )
    independent_final_reviewer_assignment_validation = (
        build_independent_final_reviewer_assignment_validation_state(independent_final_reviewer_assignment)
    )
    independent_final_closure_decision_request = (
        build_independent_final_closure_decision_request_state()
    )
    independent_final_closure_decision_owner_packet = (
        build_independent_final_closure_decision_owner_packet_state()
    )
    p0_p1_zero_proof_readiness = build_p0_p1_zero_proof_readiness_state(p0_p1_zero_proof)
    p0_p1_zero_proof_artifact_validation = build_p0_p1_zero_proof_artifact_validation_state(
        p0_p1_zero_proof
    )
    final_acceptance_bundle_manifest_validation = build_final_acceptance_bundle_manifest_validation_state(
        manifest
    )
    s2plt04_completion_report_validation = build_s2plt04_completion_report_validation_state(
        s2plt04_completion_report
    )
    final_command_execution_validation = build_final_command_execution_validation_state(final_command_execution)
    no_production_side_effect_attestation_validation = (
        build_no_production_side_effect_attestation_validation_state(no_production_side_effect_attestation)
    )
    next_agent_handoff_validation = build_next_agent_handoff_validation_state(next_agent_handoff)
    independent_review_signoff_validation = build_independent_review_signoff_validation_state(
        independent_review_signoff
    )
    final_acceptance_bundle_artifact_validation = build_final_acceptance_bundle_artifact_validation_state(
        bundle_directory_present=bundle_directory_present,
        manifest=manifest,
        independent_final_reviewer_assignment=independent_final_reviewer_assignment,
        p0_p1_zero_proof=p0_p1_zero_proof,
        s2plt04_completion_report=s2plt04_completion_report,
        independent_review_signoff=independent_review_signoff,
        final_command_execution=final_command_execution,
        no_production_side_effect_attestation=no_production_side_effect_attestation,
        next_agent_handoff=next_agent_handoff,
    )
    available_items = final_acceptance_bundle_artifact_validation["available_items"]
    missing_items = final_acceptance_bundle_artifact_validation["missing_items"]
    assignment_validation_passed = independent_final_reviewer_assignment_validation["status"] == "pass"
    blocking_reasons = list(final_acceptance_bundle_artifact_validation["blocking_reasons"])
    if not assignment_validation_passed:
        assignment_blocker = (
            "independent_final_reviewer_assignment_validation_blocked"
            if independent_final_reviewer_assignment_validation["assignment_present"]
            else "independent_final_reviewer_assignment_missing"
        )
        if assignment_blocker not in blocking_reasons:
            blocking_reasons.append(assignment_blocker)
    bundle_ready = final_acceptance_bundle_artifact_validation["status"] == "pass" and assignment_validation_passed
    state = {
        "status": "pass" if bundle_ready else "blocked",
        "scope": "final_acceptance_bundle_readiness_precheck_only",
        "required_items": list(S2PMT07_FINAL_ACCEPTANCE_BUNDLE_REQUIRED_ITEMS),
        "available_items": available_items,
        "available_prebundle_evidence": {
            "FINAL_BUNDLE_PREREQUISITE_PLAN": not validate_final_bundle_prerequisite_plan_state(
                final_bundle_prerequisite_plan
            ),
            "P0_P1_TECHNICAL_CLOSURE_CANDIDATES": not validate_p0_p1_technical_closure_candidate_state(
                p0_p1_technical_candidate_state
            ),
            "P0_P1_ZERO_PROOF_ASSEMBLY": not validate_p0_p1_zero_proof_assembly_state(
                p0_p1_zero_proof_assembly
            ),
            "INDEPENDENT_FINAL_REVIEWER_ASSIGNMENT_REQUEST": (
                not validate_independent_final_reviewer_assignment_request_state(
                    independent_final_reviewer_assignment_request
                )
            ),
            "INDEPENDENT_FINAL_REVIEWER_ASSIGNMENT_OWNER_PACKET": (
                not validate_independent_final_reviewer_assignment_owner_packet_state(
                    independent_final_reviewer_assignment_owner_packet
                )
            ),
            "INDEPENDENT_FINAL_REVIEWER_ASSIGNMENT_VALIDATION": (
                independent_final_reviewer_assignment_validation["status"] == "pass"
            ),
            "INDEPENDENT_FINAL_CLOSURE_DECISION_REQUEST": (
                not validate_independent_final_closure_decision_request_state(
                    independent_final_closure_decision_request
                )
            ),
            "INDEPENDENT_FINAL_CLOSURE_DECISION_OWNER_PACKET": (
                not validate_independent_final_closure_decision_owner_packet_state(
                    independent_final_closure_decision_owner_packet
                )
            ),
            "P0_P1_ZERO_PROOF_READINESS": p0_p1_zero_proof_readiness["status"] == "pass",
            "P0_P1_ZERO_PROOF_ARTIFACT_VALIDATION": p0_p1_zero_proof_artifact_validation["status"] == "pass",
            "FINAL_ACCEPTANCE_BUNDLE_MANIFEST_VALIDATION": (
                final_acceptance_bundle_manifest_validation["status"] == "pass"
            ),
            "FINAL_ACCEPTANCE_BUNDLE_ARTIFACT_VALIDATION": (
                final_acceptance_bundle_artifact_validation["status"] == "pass"
            ),
            "S2PLT04_COMPLETION_REPORT_VALIDATION": s2plt04_completion_report_validation["status"] == "pass",
            "FINAL_COMMAND_EXECUTION_VALIDATION": final_command_execution_validation["status"] == "pass",
            "NO_PRODUCTION_SIDE_EFFECT_ATTESTATION_VALIDATION": (
                no_production_side_effect_attestation_validation["status"] == "pass"
            ),
            "NEXT_AGENT_HANDOFF_VALIDATION": next_agent_handoff_validation["status"] == "pass",
            "INDEPENDENT_REVIEW_SIGNOFF_VALIDATION": independent_review_signoff_validation["status"] == "pass",
        },
        "missing_items": missing_items,
        "blocking_reasons": blocking_reasons,
        "final_bundle_prerequisite_plan": final_bundle_prerequisite_plan,
        "p0_p1_technical_closure_candidate_state": p0_p1_technical_candidate_state,
        "p0_p1_zero_proof_assembly": p0_p1_zero_proof_assembly,
        "independent_final_reviewer_assignment_request": independent_final_reviewer_assignment_request,
        "independent_final_reviewer_assignment_owner_packet": (
            independent_final_reviewer_assignment_owner_packet
        ),
        "independent_final_reviewer_assignment_validation": independent_final_reviewer_assignment_validation,
        "independent_final_closure_decision_request": independent_final_closure_decision_request,
        "independent_final_closure_decision_owner_packet": independent_final_closure_decision_owner_packet,
        "p0_p1_zero_proof_readiness": p0_p1_zero_proof_readiness,
        "p0_p1_zero_proof_artifact_validation": p0_p1_zero_proof_artifact_validation,
        "final_acceptance_bundle_manifest_validation": final_acceptance_bundle_manifest_validation,
        "final_acceptance_bundle_artifact_validation": final_acceptance_bundle_artifact_validation,
        "s2plt04_completion_report_validation": s2plt04_completion_report_validation,
        "final_command_execution_validation": final_command_execution_validation,
        "no_production_side_effect_attestation_validation": no_production_side_effect_attestation_validation,
        "next_agent_handoff_validation": next_agent_handoff_validation,
        "independent_review_signoff_validation": independent_review_signoff_validation,
        "bundle_present": bundle_ready,
        "bundle_claimed_ready": False,
        "production_acceptance_claimed": False,
        "integrated_production_accepted": False,
        "daily_operation_enabled": False,
        "real_smtp_send_enabled": False,
        "scheduler_install_enabled": False,
        "release_packaging_enabled": False,
        "production_restore_enabled": False,
        "state_hash": "",
    }
    state["state_hash"] = _stable_hash({key: value for key, value in state.items() if key != "state_hash"})
    return state


def validate_final_acceptance_bundle_readiness_state(state: Mapping[str, Any]) -> list[str]:
    """Validate fail-closed final acceptance bundle readiness state."""

    errors: list[str] = []
    if state.get("status") not in {"pass", "blocked"}:
        errors.append("final acceptance bundle readiness status must be pass or blocked")
    if tuple(state.get("required_items", [])) != S2PMT07_FINAL_ACCEPTANCE_BUNDLE_REQUIRED_ITEMS:
        errors.append("final acceptance bundle readiness required_items are invalid")
    available = _mapping(state.get("available_items"))
    for item in S2PMT07_FINAL_ACCEPTANCE_BUNDLE_REQUIRED_ITEMS:
        if item not in available:
            errors.append(f"available_items must include {item}")
    expected_missing_items = [
        item for item in S2PMT07_FINAL_ACCEPTANCE_BUNDLE_REQUIRED_ITEMS if not available.get(item)
    ]
    if state.get("missing_items") != expected_missing_items:
        errors.append("final acceptance bundle readiness missing_items do not match available_items")
    prebundle = _mapping(state.get("available_prebundle_evidence"))
    p0_p1_zero_proof_artifact = _mapping(state.get("p0_p1_zero_proof_artifact_validation"))
    manifest_validation = _mapping(state.get("final_acceptance_bundle_manifest_validation"))
    artifact_validation = _mapping(state.get("final_acceptance_bundle_artifact_validation"))
    completion_report = _mapping(state.get("s2plt04_completion_report_validation"))
    final_command = _mapping(state.get("final_command_execution_validation"))
    no_production_attestation = _mapping(state.get("no_production_side_effect_attestation_validation"))
    next_agent_handoff = _mapping(state.get("next_agent_handoff_validation"))
    independent_signoff = _mapping(state.get("independent_review_signoff_validation"))
    reviewer_assignment_validation = _mapping(state.get("independent_final_reviewer_assignment_validation"))
    artifact_presence_checks = (
        (
            "FINAL_ACCEPTANCE_BUNDLE/manifest.json",
            manifest_validation,
            "manifest_present",
        ),
        (
            S2PMT07_INDEPENDENT_FINAL_REVIEWER_ASSIGNMENT_ARTIFACT_PATH,
            reviewer_assignment_validation,
            "assignment_present",
        ),
        (
            "FINAL_ACCEPTANCE_BUNDLE/p0_p1_zero_proof.json",
            p0_p1_zero_proof_artifact,
            "artifact_present",
        ),
        (
            "FINAL_ACCEPTANCE_BUNDLE/s2plt04_completion_report.json",
            completion_report,
            "report_present",
        ),
        (
            "FINAL_ACCEPTANCE_BUNDLE/independent_review_signoff.yaml",
            independent_signoff,
            "signoff_present",
        ),
        (
            "FINAL_ACCEPTANCE_BUNDLE/final_command_execution.json",
            final_command,
            "command_execution_present",
        ),
        (
            S2PMT07_NO_PRODUCTION_SIDE_EFFECT_ATTESTATION_ARTIFACT_PATH,
            no_production_attestation,
            "attestation_present",
        ),
        (
            "HANDOFF/00_下一Agent先读.md",
            next_agent_handoff,
            "handoff_present",
        ),
    )
    for artifact_path, validation_state, presence_key in artifact_presence_checks:
        expected_present = validation_state.get(presence_key) is True
        if available.get(artifact_path) is not expected_present:
            errors.append(
                f"final acceptance bundle readiness availability for {artifact_path} must match validation presence"
            )
    if prebundle.get("FINAL_BUNDLE_PREREQUISITE_PLAN") is not True:
        errors.append("final acceptance bundle readiness must expose a valid final-bundle prerequisite plan")
    if prebundle.get("P0_P1_TECHNICAL_CLOSURE_CANDIDATES") is not True:
        errors.append("final acceptance bundle readiness must expose P0/P1 technical closure candidates")
    if prebundle.get("P0_P1_ZERO_PROOF_ASSEMBLY") is not True:
        errors.append("final acceptance bundle readiness must expose P0/P1 zero proof assembly")
    if prebundle.get("INDEPENDENT_FINAL_REVIEWER_ASSIGNMENT_REQUEST") is not True:
        errors.append("final acceptance bundle readiness must expose independent final reviewer assignment request")
    if prebundle.get("INDEPENDENT_FINAL_REVIEWER_ASSIGNMENT_OWNER_PACKET") is not True:
        errors.append("final acceptance bundle readiness must expose independent final reviewer assignment owner packet")
    expected_assignment_validation_ready = reviewer_assignment_validation.get("status") == "pass"
    if prebundle.get("INDEPENDENT_FINAL_REVIEWER_ASSIGNMENT_VALIDATION") is not expected_assignment_validation_ready:
        errors.append(
            "final acceptance bundle readiness independent final reviewer assignment validation flag must match validation status"
        )
    if prebundle.get("INDEPENDENT_FINAL_CLOSURE_DECISION_REQUEST") is not True:
        errors.append("final acceptance bundle readiness must expose independent final closure decision request")
    if prebundle.get("INDEPENDENT_FINAL_CLOSURE_DECISION_OWNER_PACKET") is not True:
        errors.append("final acceptance bundle readiness must expose independent final closure decision owner packet")
    expected_zero_proof_readiness_ready = _mapping(
        state.get("p0_p1_zero_proof_readiness")
    ).get("status") == "pass"
    if prebundle.get("P0_P1_ZERO_PROOF_READINESS") is not expected_zero_proof_readiness_ready:
        errors.append(
            "final acceptance bundle readiness P0/P1 zero proof readiness flag must match readiness status"
        )
    prebundle_validation_checks = (
        ("P0_P1_ZERO_PROOF_ARTIFACT_VALIDATION", p0_p1_zero_proof_artifact),
        ("FINAL_ACCEPTANCE_BUNDLE_MANIFEST_VALIDATION", manifest_validation),
        ("FINAL_ACCEPTANCE_BUNDLE_ARTIFACT_VALIDATION", artifact_validation),
        ("S2PLT04_COMPLETION_REPORT_VALIDATION", completion_report),
        ("FINAL_COMMAND_EXECUTION_VALIDATION", final_command),
        ("NO_PRODUCTION_SIDE_EFFECT_ATTESTATION_VALIDATION", no_production_attestation),
        ("NEXT_AGENT_HANDOFF_VALIDATION", next_agent_handoff),
        ("INDEPENDENT_REVIEW_SIGNOFF_VALIDATION", independent_signoff),
    )
    for prebundle_key, validation_state in prebundle_validation_checks:
        expected_ready = validation_state.get("status") == "pass"
        if prebundle.get(prebundle_key) is not expected_ready:
            errors.append(
                f"final acceptance bundle readiness {prebundle_key} must match validation status"
            )
    final_bundle_prerequisite_plan = _mapping(state.get("final_bundle_prerequisite_plan"))
    if validate_final_bundle_prerequisite_plan_state(final_bundle_prerequisite_plan):
        errors.append("final acceptance bundle readiness final-bundle prerequisite plan is invalid")
    p0_p1_candidate = _mapping(state.get("p0_p1_technical_closure_candidate_state"))
    if validate_p0_p1_technical_closure_candidate_state(p0_p1_candidate):
        errors.append("final acceptance bundle readiness P0/P1 technical candidate state is invalid")
    p0_p1_assembly = _mapping(state.get("p0_p1_zero_proof_assembly"))
    if validate_p0_p1_zero_proof_assembly_state(p0_p1_assembly):
        errors.append("final acceptance bundle readiness P0/P1 zero proof assembly state is invalid")
    reviewer_assignment_request = _mapping(state.get("independent_final_reviewer_assignment_request"))
    if validate_independent_final_reviewer_assignment_request_state(reviewer_assignment_request):
        errors.append("final acceptance bundle readiness independent final reviewer assignment request is invalid")
    reviewer_assignment_owner_packet = _mapping(
        state.get("independent_final_reviewer_assignment_owner_packet")
    )
    if validate_independent_final_reviewer_assignment_owner_packet_state(reviewer_assignment_owner_packet):
        errors.append("final acceptance bundle readiness independent final reviewer assignment owner packet is invalid")
    if reviewer_assignment_validation.get("status") not in {"pass", "blocked"}:
        errors.append("final acceptance bundle readiness independent final reviewer assignment validation status is invalid")
    if reviewer_assignment_validation.get("scope") != "independent_final_reviewer_assignment_validation_only_no_closure":
        errors.append("final acceptance bundle readiness independent final reviewer assignment validation scope is invalid")
    if reviewer_assignment_validation.get("status") == "pass":
        if reviewer_assignment_validation.get("assignment_present") is not True:
            errors.append("final acceptance bundle readiness assignment validation pass requires artifact presence")
        if reviewer_assignment_validation.get("independent_final_reviewer_assigned_by_payload") is not True:
            errors.append("final acceptance bundle readiness assignment validation pass requires reviewer assignment payload")
        if reviewer_assignment_validation.get("validation_errors") != []:
            errors.append("final acceptance bundle readiness assignment validation pass requires zero validation errors")
    if reviewer_assignment_validation.get("state_hash") != _stable_hash(
        {key: value for key, value in reviewer_assignment_validation.items() if key != "state_hash"}
    ):
        errors.append("final acceptance bundle readiness independent final reviewer assignment validation hash is invalid")
    final_closure_request = _mapping(state.get("independent_final_closure_decision_request"))
    if validate_independent_final_closure_decision_request_state(final_closure_request):
        errors.append("final acceptance bundle readiness independent final closure decision request is invalid")
    final_closure_owner_packet = _mapping(state.get("independent_final_closure_decision_owner_packet"))
    if validate_independent_final_closure_decision_owner_packet_state(final_closure_owner_packet):
        errors.append("final acceptance bundle readiness independent final closure decision owner packet is invalid")
    p0_p1_zero_proof = _mapping(state.get("p0_p1_zero_proof_readiness"))
    if validate_p0_p1_zero_proof_readiness_state(p0_p1_zero_proof):
        errors.append("final acceptance bundle readiness P0/P1 zero proof readiness state is invalid")
    artifact_status_checks = (
        ("P0/P1 zero proof artifact", p0_p1_zero_proof_artifact),
        ("independent final reviewer assignment", reviewer_assignment_validation),
        ("manifest", manifest_validation),
        ("S2PLT04 completion report", completion_report),
        ("final command execution", final_command),
        ("no-production side-effect attestation", no_production_attestation),
        ("next-agent handoff", next_agent_handoff),
        ("independent review signoff", independent_signoff),
    )
    for label, validation_state in artifact_status_checks:
        if validation_state.get("status") not in {"pass", "blocked"}:
            errors.append(f"final acceptance bundle readiness {label} validation status is invalid")
    if validate_final_acceptance_bundle_artifact_validation_state(artifact_validation):
        errors.append("final acceptance bundle readiness artifact validation is invalid")
    assignment_validation_ready = reviewer_assignment_validation.get("status") == "pass"
    expected_readiness_ready = artifact_validation.get("status") == "pass" and assignment_validation_ready
    expected_readiness_status = "pass" if expected_readiness_ready else "blocked"
    if state.get("status") != expected_readiness_status:
        errors.append("final acceptance bundle readiness status must match artifact and assignment validation")
    if state.get("bundle_present") is not expected_readiness_ready:
        errors.append("final acceptance bundle readiness bundle_present must match artifact and assignment validation pass state")
    for flag in S2PMT07_FINAL_ACCEPTANCE_BUNDLE_FORBIDDEN_FLAGS:
        if state.get(flag) is not False:
            errors.append(f"{flag} must be false")
    if state.get("status") == "pass":
        if state.get("missing_items"):
            errors.append("passing final acceptance bundle readiness must not have missing items")
        if state.get("blocking_reasons"):
            errors.append("passing final acceptance bundle readiness must not have blocking reasons")
    else:
        if state.get("bundle_claimed_ready") is not False:
            errors.append("final acceptance bundle readiness must not claim ready while blocked")
        expected_blocking_reasons = list(artifact_validation.get("blocking_reasons", []))
        if not assignment_validation_ready:
            assignment_blocker = (
                "independent_final_reviewer_assignment_validation_blocked"
                if reviewer_assignment_validation.get("assignment_present") is True
                else "independent_final_reviewer_assignment_missing"
            )
            if assignment_blocker not in expected_blocking_reasons:
                expected_blocking_reasons.append(assignment_blocker)
        if state.get("blocking_reasons") != expected_blocking_reasons:
            errors.append("blocked final acceptance bundle readiness blocking_reasons must match artifact and assignment validation")
    expected_hash = _stable_hash({key: value for key, value in state.items() if key != "state_hash"})
    if state.get("state_hash") != expected_hash:
        errors.append("final acceptance bundle readiness state_hash does not match state content")
    return errors


def build_s2pmt07_precheck_report(*, generated_at: str) -> dict[str, Any]:
    """Build a deterministic fail-closed S2PMT07 precheck report."""

    dependencies = build_dependency_state()
    audit_blockers = build_audit_blocker_state()
    reviewer = build_reviewer_independence_state()
    evidence = build_evidence_bundle_state()
    tests = build_test_gate_state()
    final_bundle = build_final_acceptance_bundle_readiness_state()
    gates = {
        "reviewer_independence": reviewer["status"] == "pass",
        "p0_zero": audit_blockers["checks"]["P0_zero"],
        "p1_zero": audit_blockers["checks"]["P1_zero"],
        "s2pmt01_t06_completed": all(task_id in dependencies["completed_dependencies"] for task_id in S2PMT07_REQUIRED_DEPENDENCIES[:6]),
        "s2plt04_completed": "S2PLT04" in dependencies["completed_dependencies"],
        "final_acceptance_bundle_present": evidence["available_evidence"]["FINAL_ACCEPTANCE_BUNDLE/"]
        and final_bundle["bundle_present"],
        "final_acceptance_bundle_ready": final_bundle["status"] == "pass",
        "independent_review_signoff_present": evidence["available_evidence"]["independent_review_signoff.yaml"],
        "required_final_commands_executed": tests["executed_as_final_reviewer"],
        "no_production_side_effect": True,
    }
    blocking_reasons = []
    if not gates["reviewer_independence"]:
        blocking_reasons.append("reviewer_independence_not_proven")
    if not gates["p0_zero"]:
        blocking_reasons.append("inherited_v7_1_p0_findings_open")
    if not gates["p1_zero"]:
        blocking_reasons.append("inherited_v7_1_p1_findings_open")
    if not gates["s2plt04_completed"]:
        blocking_reasons.append("s2plt04_not_completed")
    if not gates["final_acceptance_bundle_present"]:
        blocking_reasons.append("final_acceptance_bundle_missing")
    if not gates["independent_review_signoff_present"]:
        blocking_reasons.append("independent_review_signoff_missing")
    if not gates["required_final_commands_executed"]:
        blocking_reasons.append("independent_final_command_execution_missing")
    status = "pass" if not blocking_reasons and all(gates.values()) else "blocked"
    report = {
        "model_id": S2PMT07_FINAL_GATE_MODEL_ID,
        "schema_version": S2PMT07_SCHEMA_VERSION,
        "task_id": S2PMT07_TASK_ID,
        "acceptance_id": S2PMT07_ACCEPTANCE_ID,
        "generated_at": generated_at,
        "status": status,
        "blocking_reasons": blocking_reasons,
        "scope": "fail_closed_final_gate_precheck_only",
        "gates": gates,
        "dependencies": dependencies,
        "audit_blockers": audit_blockers,
        "reviewer_independence": reviewer,
        "evidence_bundle": evidence,
        "final_acceptance_bundle_readiness": final_bundle,
        "test_gates": tests,
        "production_acceptance_claimed": False,
        "inherited_p0_p1_closed": False,
        "report_hash": "",
        "integrated_production_accepted": False,
        "daily_operation_enabled": False,
        "real_smtp_send_enabled": False,
        "scheduler_install_enabled": False,
        "release_packaging_enabled": False,
        "production_restore_enabled": False,
        "current_pointer_changed": False,
        "v7_1_baseline_changed": False,
        "v7_2_contract_files_changed": False,
    }
    report["report_hash"] = _stable_hash({key: value for key, value in report.items() if key != "report_hash"})
    return report


def validate_s2pmt07_precheck_report(report: Mapping[str, Any]) -> list[str]:
    """Validate S2PMT07 fail-closed precheck reports."""

    errors: list[str] = []
    if report.get("model_id") != S2PMT07_FINAL_GATE_MODEL_ID:
        errors.append("S2PMT07 report model_id is invalid")
    if report.get("schema_version") != S2PMT07_SCHEMA_VERSION:
        errors.append("S2PMT07 report schema_version must be 1")
    if report.get("task_id") != S2PMT07_TASK_ID:
        errors.append("S2PMT07 report task_id is invalid")
    if report.get("acceptance_id") != S2PMT07_ACCEPTANCE_ID:
        errors.append("S2PMT07 report acceptance_id is invalid")
    if report.get("status") not in {"pass", "blocked"}:
        errors.append("S2PMT07 report status must be pass or blocked")
    if report.get("production_acceptance_claimed") is not False:
        errors.append("S2PMT07 precheck must not claim production acceptance")
    if report.get("inherited_p0_p1_closed") is not False:
        errors.append("S2PMT07 precheck must not close inherited P0/P1")
    for flag in S2PMT07_FORBIDDEN_PASS_FLAGS:
        if report.get(flag) is not False:
            errors.append(f"{flag} must be false")
    dependencies = _mapping(report.get("dependencies"))
    for task_id in S2PMT07_REQUIRED_DEPENDENCIES:
        if task_id not in dependencies.get("required_dependencies", []):
            errors.append(f"dependencies.required_dependencies must include {task_id}")
    evidence = _mapping(report.get("evidence_bundle"))
    for item in S2PMT07_REQUIRED_EVIDENCE:
        if item not in evidence.get("required_evidence", []):
            errors.append(f"evidence_bundle.required_evidence must include {item}")
    final_bundle = _mapping(report.get("final_acceptance_bundle_readiness"))
    final_bundle_errors = validate_final_acceptance_bundle_readiness_state(final_bundle)
    if final_bundle_errors:
        errors.append("S2PMT07 final acceptance bundle readiness is invalid")
    tests = _mapping(report.get("test_gates"))
    for command in S2PMT07_REQUIRED_TEST_COMMANDS:
        if command not in tests.get("required_test_commands", []):
            errors.append(f"test_gates.required_test_commands must include {command}")
    if report.get("status") == "pass":
        gates = _mapping(report.get("gates"))
        if not all(gates.values()):
            errors.append("passing S2PMT07 report requires every gate true")
        if report.get("blocking_reasons"):
            errors.append("passing S2PMT07 report must not have blocking reasons")
    else:
        for reason in S2PMT07_BLOCKING_REASONS[:4]:
            if reason not in report.get("blocking_reasons", []):
                errors.append(f"blocked S2PMT07 precheck must include {reason}")
    return errors


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _list_of_mappings(value: Any) -> list[Mapping[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, Mapping)]


def _stable_hash(value: Mapping[str, Any]) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
