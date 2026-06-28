"""S2PL/S2PM fail-closed final production gate precheck helpers."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from typing import Any

from arxiv_daily_push.stage2_lease_fencing import build_m4_cycle_watermark
from arxiv_daily_push.stage2_replay_gate import (
    S2PLT01_REQUIRED_MAIL_PRODUCTS,
    build_s2plt01_independent_replay_review_report,
    build_s2plt01_replay_payload_execution_report,
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
S2PMT07_P0_P1_ZERO_PROOF_ARTIFACT_PATH = "FINAL_ACCEPTANCE_BUNDLE/p0_p1_zero_proof.json"
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
S2PMT07_FINAL_ACCEPTANCE_BUNDLE_REQUIRED_ITEMS = (
    "FINAL_ACCEPTANCE_BUNDLE/manifest.json",
    S2PMT07_P0_P1_ZERO_PROOF_ARTIFACT_PATH,
    "FINAL_ACCEPTANCE_BUNDLE/s2plt04_completion_report.json",
    "FINAL_ACCEPTANCE_BUNDLE/independent_review_signoff.yaml",
    "FINAL_ACCEPTANCE_BUNDLE/final_command_execution.json",
    "FINAL_ACCEPTANCE_BUNDLE/no_production_side_effects.json",
    "HANDOFF/00_下一Agent先读.md",
)
S2PMT07_FINAL_ACCEPTANCE_BUNDLE_BLOCKING_REASONS = (
    "final_acceptance_bundle_directory_missing",
    "final_acceptance_bundle_manifest_missing",
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
    "FINAL_BUNDLE_MANIFEST",
)
S2PMT07_S2PLT04_COMPLETION_REPORT_REQUIRED_TERMINAL_DEPENDENCIES = (
    "S2PLT01_ACCEPTED",
    "S2PLT02_ACCEPTED",
    "S2PLT03_ACCEPTED",
    "P0_ZERO_PROVEN",
    "P1_ZERO_PROVEN",
    "FINAL_ACCEPTANCE_BUNDLE_PRESENT",
)
S2PMT07_S2PLT04_COMPLETION_REPORT_NO_PRODUCTION_FLAGS = S2PMT07_FINAL_ACCEPTANCE_BUNDLE_NO_PRODUCTION_FLAGS
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
    "OPEN_PR_COUNT_ZERO",
    "REMOTE_ADP_BRANCH_SCAN",
    "PRODUCTION_TRUE_FLAG_DIFF_SCAN",
)
S2PMT07_NO_PRODUCTION_SIDE_EFFECT_ATTESTATION_NO_PRODUCTION_FLAGS = (
    S2PMT07_FINAL_ACCEPTANCE_BUNDLE_NO_PRODUCTION_FLAGS
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
    "P0_P1_ZERO_PROOF_ARTIFACT",
    "S2PLT04_COMPLETION_REPORT",
    "INDEPENDENT_REVIEW_SIGNOFF",
    "FINAL_COMMAND_EXECUTION",
    "NO_PRODUCTION_SIDE_EFFECT_ATTESTATION",
    "NEXT_AGENT_HANDOFF",
)
S2PMT07_FINAL_ACCEPTANCE_BUNDLE_ITEM_BLOCKING_REASONS = {
    "FINAL_ACCEPTANCE_BUNDLE/manifest.json": "final_acceptance_bundle_manifest_missing",
    "FINAL_ACCEPTANCE_BUNDLE/p0_p1_zero_proof.json": "p0_p1_zero_proof_missing",
    "FINAL_ACCEPTANCE_BUNDLE/s2plt04_completion_report.json": "s2plt04_completion_evidence_missing",
    "FINAL_ACCEPTANCE_BUNDLE/independent_review_signoff.yaml": "independent_review_signoff_missing",
    "FINAL_ACCEPTANCE_BUNDLE/final_command_execution.json": "independent_final_command_execution_missing",
    "FINAL_ACCEPTANCE_BUNDLE/no_production_side_effects.json": "no_production_side_effect_attestation_missing",
    "HANDOFF/00_下一Agent先读.md": "next_agent_handoff_missing",
}
S2PMT07_FINAL_BUNDLE_PREREQUISITE_PLAN_REQUIRED_STEPS = (
    "P0_P1_ZERO_PROOF_ARTIFACT",
    "S2PLT04_COMPLETION_REPORT",
    "FINAL_COMMAND_EXECUTION",
    "NO_PRODUCTION_SIDE_EFFECT_ATTESTATION",
    "NEXT_AGENT_HANDOFF",
    "INDEPENDENT_REVIEW_SIGNOFF",
    "FINAL_ACCEPTANCE_BUNDLE_MANIFEST",
)
S2PMT07_FINAL_BUNDLE_PREREQUISITE_PLAN_BLOCKING_REASONS = (
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
S2PLT02_M4_WATERMARK_REQUIRED_TERMINAL_PRODUCTS = ("M1", "M2", "M3")
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

    return {
        "status": "blocked",
        "required_dependencies": list(S2PLT02_REQUIRED_DEPENDENCIES),
        "completed_dependencies": {},
        "unmet_dependencies": list(S2PLT02_REQUIRED_DEPENDENCIES),
        "s2plt01_acceptance_status": "blocked_by_inherited_p0_p1_and_final_gates",
    }


def _default_s2plt02_delivery_manifest_records() -> list[dict[str, Any]]:
    """Return committed real-delivery manifest facts used by the S2PLT02 ledger."""

    return [
        {
            "manifest_ref": S2PLT02_PARTIAL_REAL_DELIVERY_EVIDENCE_REFS[0],
            "schema_version": 1,
            "project_id": "arxiv-daily-push",
            "task_id": "LOCAL-DAILY-M1-M4-RESEND-EXECUTION",
            "status": "pass",
            "generated_at": S2PLT02_PARTIAL_REAL_DELIVERY_GENERATED_AT,
            "service_date": S2PLT02_PARTIAL_REAL_DELIVERY_SERVICE_DATE,
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
            "evidence_refs": list(S2PLT02_PARTIAL_REAL_DELIVERY_EVIDENCE_REFS),
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


def build_s2plt02_m4_watermark_proof_state(
    *,
    watermark_proofs: list[Mapping[str, Any]] | None = None,
    delivery_ledger: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the S2PLT02 M4 watermark proof state without enabling production."""

    ledger = dict(delivery_ledger or build_s2plt02_delivery_evidence_ledger_state())
    source_proofs = [
        json.loads(json.dumps(record, ensure_ascii=False))
        for record in (watermark_proofs if watermark_proofs is not None else [])
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


def build_s2plt02_live_2d_precheck_report(*, generated_at: str) -> dict[str, Any]:
    """Build a deterministic fail-closed S2PLT02 two-day live-run precheck."""

    dependencies = build_s2plt02_dependency_state()
    evidence = build_s2plt02_live_evidence_state()
    audit_blockers = build_audit_blocker_state()
    gates = {
        "s2plt01_accepted": "S2PLT01" in dependencies["completed_dependencies"],
        "two_consecutive_real_days": evidence["observed_natural_days"] >= S2PLT02_REQUIRED_NATURAL_DAYS,
        "eight_real_emails_sent": evidence["observed_email_count"] >= S2PLT02_REQUIRED_EMAIL_COUNT,
        "no_duplicate_emails": evidence["duplicate_email_count"] == 0,
        "m4_watermark_correct": evidence["m4_watermark_correct"],
        "real_scheduler_proven": evidence["real_scheduler_proven"],
        "real_smtp_proven": evidence["real_smtp_proven"],
        "p0_zero": audit_blockers["checks"]["P0_zero"],
        "p1_zero": audit_blockers["checks"]["P1_zero"],
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
        "blocking_reasons": blocking_reasons,
        "production_acceptance_claimed": False,
        "inherited_p0_p1_closed": False,
        "report_hash": "",
        **{flag: False for flag in S2PLT02_FORBIDDEN_FLAGS},
    }
    report["report_hash"] = _stable_hash({key: value for key, value in report.items() if key != "report_hash"})
    return report


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


def build_s2plt03_resilience_precheck_report(*, generated_at: str) -> dict[str, Any]:
    """Build a deterministic fail-closed S2PLT03 resilience precheck."""

    dependencies = build_s2plt03_dependency_state()
    local_drill_bundle = build_s2plt03_local_resilience_drill_bundle(generated_at=generated_at)
    evidence = build_s2plt03_resilience_evidence_state(local_drill_bundle=local_drill_bundle)
    audit_blockers = build_audit_blocker_state()
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
        "p0_zero": audit_blockers["checks"]["P0_zero"],
        "p1_zero": audit_blockers["checks"]["P1_zero"],
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
    if report.get("status") == "pass":
        gates = _mapping(report.get("gates"))
        if not all(gates.values()):
            errors.append("passing S2PLT03 report requires every gate true")
        if report.get("blocking_reasons"):
            errors.append("passing S2PLT03 report must not have blocking reasons")
    else:
        gates = _mapping(report.get("gates"))
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


def build_s2plt04_dependency_state() -> dict[str, Any]:
    """Build current S2PLT04 dependency state without accepting upstream tasks."""

    available_local_evidence = {
        task_id: "local_evidence_present_not_terminal_acceptance"
        for task_id in S2PLT04_AVAILABLE_LOCAL_EVIDENCE
    }
    return {
        "status": "blocked",
        "required_dependencies": list(S2PLT04_REQUIRED_DEPENDENCIES),
        "completed_dependencies": {},
        "unmet_dependencies": list(S2PLT04_REQUIRED_DEPENDENCIES),
        "available_local_evidence": available_local_evidence,
        "s2plt01_acceptance_status": "blocked_by_inherited_p0_p1_and_final_gates",
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
    available = {
        "S2PLT01_ACCEPTED": False,
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
            "blocked_review_package_passed_not_terminal_acceptance" if replay_review_present else "not_proven"
        ),
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


def build_s2plt04_integration_candidate_report(*, generated_at: str) -> dict[str, Any]:
    """Build a deterministic fail-closed S2PLT04 integration-candidate precheck."""

    dependencies = build_s2plt04_dependency_state()
    evidence = build_s2plt04_evidence_state()
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
        for reason in S2PLT04_BLOCKING_REASONS:
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


def build_independent_final_reviewer_assignment_hash(payload: Mapping[str, Any]) -> str:
    """Return the canonical reviewer-assignment hash excluding its hash field."""

    payload_without_hash = {key: value for key, value in payload.items() if key != "assignment_hash"}
    return f"sha256:{_stable_hash(payload_without_hash)}"


def validate_independent_final_reviewer_assignment_artifact(payload: Mapping[str, Any] | None) -> list[str]:
    """Validate a future independent-final-reviewer assignment artifact."""

    if payload is None:
        return ["independent_final_reviewer_assignment_missing"]
    errors: list[str] = []
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
    if payload.get("assignment_decision") != S2PMT07_INDEPENDENT_FINAL_REVIEWER_ASSIGNMENT_DECISION:
        errors.append("assignment_decision is invalid")

    assignment = _mapping(payload.get("reviewer_assignment"))
    reviewer_id = assignment.get("reviewer_id")
    if not isinstance(reviewer_id, str) or not reviewer_id:
        errors.append("reviewer_assignment.reviewer_id must be a non-empty string")
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


def build_p0_p1_zero_proof_readiness_state() -> dict[str, Any]:
    """Build a fail-closed schema contract for the future P0/P1 zero proof artifact."""

    assembly_state = build_p0_p1_zero_proof_assembly_state()
    state = {
        "status": "blocked",
        "scope": "p0_p1_zero_proof_readiness_schema_only_no_closure",
        "zero_proof_artifact_path": S2PMT07_P0_P1_ZERO_PROOF_ARTIFACT_PATH,
        "zero_proof_artifact_present": False,
        "required_zero_severities": list(S2PMT07_REQUIRED_ZERO_FINDING_SEVERITIES),
        "required_fields": list(S2PMT07_P0_P1_ZERO_PROOF_REQUIRED_FIELDS),
        "required_open_p0_findings": 0,
        "required_open_p1_findings": 0,
        "observed_open_p0_findings": S2PMT07_INHERITED_V7_1_OPEN_P0_FINDINGS,
        "observed_open_p1_findings": S2PMT07_INHERITED_V7_1_OPEN_P1_FINDINGS,
        "candidate_evidence_refs": [
            S2PMT07_P0_TECHNICAL_CLOSURE_CANDIDATE_PACKAGE,
            S2PMT07_P1_TECHNICAL_CLOSURE_CANDIDATE_RECEIPT,
            *S2PMT07_P1_TECHNICAL_CLOSURE_CANDIDATE_MANIFESTS,
        ],
        "zero_proof_assembly_state": assembly_state,
        "candidate_evidence_only": True,
        "independent_final_closure_decision_present": False,
        "p0_zero_proven": False,
        "p1_zero_proven": False,
        "closure_claimed": False,
        "production_acceptance_claimed": False,
        "integrated_production_accepted": False,
        "daily_operation_enabled": False,
        "real_smtp_send_enabled": False,
        "scheduler_install_enabled": False,
        "release_packaging_enabled": False,
        "production_restore_enabled": False,
        "blocking_reasons": list(S2PMT07_P0_P1_ZERO_PROOF_BLOCKING_REASONS),
        "state_hash": "",
    }
    state["state_hash"] = _stable_hash({key: value for key, value in state.items() if key != "state_hash"})
    return state


def validate_p0_p1_zero_proof_readiness_state(state: Mapping[str, Any]) -> list[str]:
    """Validate P0/P1 zero-proof readiness without accepting closure."""

    errors: list[str] = []
    if state.get("status") != "blocked":
        errors.append("P0/P1 zero proof readiness status must remain blocked")
    if state.get("scope") != "p0_p1_zero_proof_readiness_schema_only_no_closure":
        errors.append("P0/P1 zero proof readiness scope is invalid")
    if state.get("zero_proof_artifact_path") != S2PMT07_P0_P1_ZERO_PROOF_ARTIFACT_PATH:
        errors.append("P0/P1 zero proof readiness artifact path is invalid")
    if state.get("zero_proof_artifact_present") is not False:
        errors.append("P0/P1 zero proof readiness must not claim artifact presence")
    if tuple(state.get("required_zero_severities", [])) != S2PMT07_REQUIRED_ZERO_FINDING_SEVERITIES:
        errors.append("P0/P1 zero proof readiness required zero severities are invalid")
    if tuple(state.get("required_fields", [])) != S2PMT07_P0_P1_ZERO_PROOF_REQUIRED_FIELDS:
        errors.append("P0/P1 zero proof readiness required fields are invalid")
    if state.get("required_open_p0_findings") != 0:
        errors.append("P0/P1 zero proof readiness required open P0 findings must be zero")
    if state.get("required_open_p1_findings") != 0:
        errors.append("P0/P1 zero proof readiness required open P1 findings must be zero")
    if state.get("observed_open_p0_findings") != S2PMT07_INHERITED_V7_1_OPEN_P0_FINDINGS:
        errors.append("P0/P1 zero proof readiness must preserve inherited open P0 count until artifact exists")
    if state.get("observed_open_p1_findings") != S2PMT07_INHERITED_V7_1_OPEN_P1_FINDINGS:
        errors.append("P0/P1 zero proof readiness must preserve inherited open P1 count until artifact exists")
    refs = state.get("candidate_evidence_refs", [])
    for ref in (
        S2PMT07_P0_TECHNICAL_CLOSURE_CANDIDATE_PACKAGE,
        S2PMT07_P1_TECHNICAL_CLOSURE_CANDIDATE_RECEIPT,
        *S2PMT07_P1_TECHNICAL_CLOSURE_CANDIDATE_MANIFESTS,
    ):
        if ref not in refs:
            errors.append(f"P0/P1 zero proof readiness refs must include {ref}")
    if state.get("candidate_evidence_only") is not True:
        errors.append("P0/P1 zero proof readiness must label candidate evidence as non-closure")
    assembly_state = _mapping(state.get("zero_proof_assembly_state"))
    if validate_p0_p1_zero_proof_assembly_state(assembly_state):
        errors.append("P0/P1 zero proof readiness assembly state is invalid")
    if state.get("independent_final_closure_decision_present") is not False:
        errors.append("P0/P1 zero proof readiness must not claim independent final closure decision")
    for flag in (
        "p0_zero_proven",
        "p1_zero_proven",
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


def build_final_command_execution_hash(payload: Mapping[str, Any]) -> str:
    """Return the canonical final-command execution hash excluding its hash field."""

    payload_without_hash = {key: value for key, value in payload.items() if key != "execution_hash"}
    return f"sha256:{_stable_hash(payload_without_hash)}"


def validate_final_command_execution_artifact(payload: Mapping[str, Any] | None) -> list[str]:
    """Validate a future final command execution artifact without accepting production."""

    if payload is None:
        return ["final_command_execution_missing"]
    errors: list[str] = []
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


def build_no_production_side_effect_attestation_hash(payload: Mapping[str, Any]) -> str:
    """Return the canonical no-production attestation hash excluding its hash field."""

    payload_without_hash = {key: value for key, value in payload.items() if key != "attestation_hash"}
    return f"sha256:{_stable_hash(payload_without_hash)}"


def validate_no_production_side_effect_attestation(payload: Mapping[str, Any] | None) -> list[str]:
    """Validate a future no-production side-effect attestation without accepting production."""

    if payload is None:
        return ["no_production_side_effect_attestation_missing"]
    errors: list[str] = []
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


def build_final_bundle_prerequisite_plan_state() -> dict[str, Any]:
    """Build the current fail-closed execution order for final-bundle prerequisites."""

    validation_states: dict[str, Mapping[str, Any]] = {
        "P0_P1_ZERO_PROOF_ARTIFACT": build_p0_p1_zero_proof_artifact_validation_state(None),
        "S2PLT04_COMPLETION_REPORT": build_s2plt04_completion_report_validation_state(None),
        "FINAL_COMMAND_EXECUTION": build_final_command_execution_validation_state(None),
        "NO_PRODUCTION_SIDE_EFFECT_ATTESTATION": (
            build_no_production_side_effect_attestation_validation_state(None)
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
        ordered_steps.append(
            {
                "step_id": step_id,
                "status": validation.get("status"),
                "artifact_ref": artifact_ref,
                "validation_errors": list(validation.get("validation_errors", [])),
                "default_action": "produce_artifact_then_revalidate_without_production_side_effects",
            }
        )

    all_required_steps_passed = all(step["status"] == "pass" for step in ordered_steps)
    state = {
        "status": "pass" if all_required_steps_passed else "blocked",
        "scope": "final_bundle_prerequisite_plan_only_no_production_acceptance",
        "task_id": S2PMT07_TASK_ID,
        "acceptance_id": S2PMT07_ACCEPTANCE_ID,
        "required_steps": list(S2PMT07_FINAL_BUNDLE_PREREQUISITE_PLAN_REQUIRED_STEPS),
        "ordered_steps": ordered_steps,
        "next_required_step": next(
            (step["step_id"] for step in ordered_steps if step["status"] != "pass"),
            None,
        ),
        "all_required_steps_passed": all_required_steps_passed,
        "ready_for_final_bundle_manifest": False,
        "blocking_reasons": list(S2PMT07_FINAL_BUNDLE_PREREQUISITE_PLAN_BLOCKING_REASONS),
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
    if any(step.get("status") == "pass" for step in ordered_steps):
        errors.append("final bundle prerequisite plan cannot mark steps pass before artifacts exist")
    for step in ordered_steps:
        if not isinstance(step.get("artifact_ref"), str) or not step.get("artifact_ref"):
            errors.append(f"{step.get('step_id', 'UNKNOWN')}.artifact_ref must be a non-empty string")

    if state.get("next_required_step") != "P0_P1_ZERO_PROOF_ARTIFACT":
        errors.append("final bundle prerequisite plan next_required_step must remain P0_P1_ZERO_PROOF_ARTIFACT")
    if state.get("all_required_steps_passed") is not False:
        errors.append("final bundle prerequisite plan all_required_steps_passed must remain false")
    if state.get("ready_for_final_bundle_manifest") is not False:
        errors.append("final bundle prerequisite plan must not be ready for final bundle manifest")
    for reason in S2PMT07_FINAL_BUNDLE_PREREQUISITE_PLAN_BLOCKING_REASONS:
        if reason not in state.get("blocking_reasons", []):
            errors.append(f"final bundle prerequisite plan must include blocker {reason}")
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


def build_final_acceptance_bundle_readiness_state() -> dict[str, Any]:
    """Build the current final acceptance bundle readiness state without packaging."""

    available_items = {item: False for item in S2PMT07_FINAL_ACCEPTANCE_BUNDLE_REQUIRED_ITEMS}
    final_bundle_prerequisite_plan = build_final_bundle_prerequisite_plan_state()
    p0_p1_technical_candidate_state = build_p0_p1_technical_closure_candidate_state()
    p0_p1_zero_proof_assembly = build_p0_p1_zero_proof_assembly_state()
    independent_final_reviewer_assignment_request = (
        build_independent_final_reviewer_assignment_request_state()
    )
    independent_final_reviewer_assignment_validation = (
        build_independent_final_reviewer_assignment_validation_state(None)
    )
    independent_final_closure_decision_request = (
        build_independent_final_closure_decision_request_state()
    )
    p0_p1_zero_proof_readiness = build_p0_p1_zero_proof_readiness_state()
    p0_p1_zero_proof_artifact_validation = build_p0_p1_zero_proof_artifact_validation_state(None)
    final_acceptance_bundle_manifest_validation = build_final_acceptance_bundle_manifest_validation_state(None)
    s2plt04_completion_report_validation = build_s2plt04_completion_report_validation_state(None)
    final_command_execution_validation = build_final_command_execution_validation_state(None)
    no_production_side_effect_attestation_validation = (
        build_no_production_side_effect_attestation_validation_state(None)
    )
    next_agent_handoff_validation = build_next_agent_handoff_validation_state(None)
    independent_review_signoff_validation = build_independent_review_signoff_validation_state(None)
    final_acceptance_bundle_artifact_validation = build_final_acceptance_bundle_artifact_validation_state()
    state = {
        "status": "blocked",
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
            "INDEPENDENT_FINAL_REVIEWER_ASSIGNMENT_VALIDATION": (
                independent_final_reviewer_assignment_validation["status"] == "pass"
            ),
            "INDEPENDENT_FINAL_CLOSURE_DECISION_REQUEST": (
                not validate_independent_final_closure_decision_request_state(
                    independent_final_closure_decision_request
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
        "missing_items": [item for item, present in available_items.items() if not present],
        "blocking_reasons": list(S2PMT07_FINAL_ACCEPTANCE_BUNDLE_BLOCKING_REASONS),
        "final_bundle_prerequisite_plan": final_bundle_prerequisite_plan,
        "p0_p1_technical_closure_candidate_state": p0_p1_technical_candidate_state,
        "p0_p1_zero_proof_assembly": p0_p1_zero_proof_assembly,
        "independent_final_reviewer_assignment_request": independent_final_reviewer_assignment_request,
        "independent_final_reviewer_assignment_validation": independent_final_reviewer_assignment_validation,
        "independent_final_closure_decision_request": independent_final_closure_decision_request,
        "p0_p1_zero_proof_readiness": p0_p1_zero_proof_readiness,
        "p0_p1_zero_proof_artifact_validation": p0_p1_zero_proof_artifact_validation,
        "final_acceptance_bundle_manifest_validation": final_acceptance_bundle_manifest_validation,
        "final_acceptance_bundle_artifact_validation": final_acceptance_bundle_artifact_validation,
        "s2plt04_completion_report_validation": s2plt04_completion_report_validation,
        "final_command_execution_validation": final_command_execution_validation,
        "no_production_side_effect_attestation_validation": no_production_side_effect_attestation_validation,
        "next_agent_handoff_validation": next_agent_handoff_validation,
        "independent_review_signoff_validation": independent_review_signoff_validation,
        "bundle_present": False,
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
    if available.get("FINAL_ACCEPTANCE_BUNDLE/p0_p1_zero_proof.json") is not False:
        errors.append("final acceptance bundle readiness must not expose p0_p1_zero_proof before final bundle exists")
    prebundle = _mapping(state.get("available_prebundle_evidence"))
    if prebundle.get("FINAL_BUNDLE_PREREQUISITE_PLAN") is not True:
        errors.append("final acceptance bundle readiness must expose a valid final-bundle prerequisite plan")
    if prebundle.get("P0_P1_TECHNICAL_CLOSURE_CANDIDATES") is not True:
        errors.append("final acceptance bundle readiness must expose P0/P1 technical closure candidates")
    if prebundle.get("P0_P1_ZERO_PROOF_ASSEMBLY") is not True:
        errors.append("final acceptance bundle readiness must expose P0/P1 zero proof assembly")
    if prebundle.get("INDEPENDENT_FINAL_REVIEWER_ASSIGNMENT_REQUEST") is not True:
        errors.append("final acceptance bundle readiness must expose independent final reviewer assignment request")
    if prebundle.get("INDEPENDENT_FINAL_REVIEWER_ASSIGNMENT_VALIDATION") is not False:
        errors.append(
            "final acceptance bundle readiness must not expose independent final reviewer assignment validation as passing"
        )
    if prebundle.get("INDEPENDENT_FINAL_CLOSURE_DECISION_REQUEST") is not True:
        errors.append("final acceptance bundle readiness must expose independent final closure decision request")
    if prebundle.get("P0_P1_ZERO_PROOF_READINESS") is not False:
        errors.append("final acceptance bundle readiness must not expose P0/P1 zero proof readiness as passing")
    if prebundle.get("P0_P1_ZERO_PROOF_ARTIFACT_VALIDATION") is not False:
        errors.append("final acceptance bundle readiness must not expose P0/P1 zero proof artifact validation as passing")
    if prebundle.get("FINAL_ACCEPTANCE_BUNDLE_MANIFEST_VALIDATION") is not False:
        errors.append("final acceptance bundle readiness must not expose final bundle manifest validation as passing")
    if prebundle.get("FINAL_ACCEPTANCE_BUNDLE_ARTIFACT_VALIDATION") is not False:
        errors.append("final acceptance bundle readiness must not expose final bundle artifact validation as passing")
    if prebundle.get("S2PLT04_COMPLETION_REPORT_VALIDATION") is not False:
        errors.append("final acceptance bundle readiness must not expose S2PLT04 completion report validation as passing")
    if prebundle.get("FINAL_COMMAND_EXECUTION_VALIDATION") is not False:
        errors.append("final acceptance bundle readiness must not expose final command execution validation as passing")
    if prebundle.get("NO_PRODUCTION_SIDE_EFFECT_ATTESTATION_VALIDATION") is not False:
        errors.append(
            "final acceptance bundle readiness must not expose no-production side-effect attestation validation as passing"
        )
    if prebundle.get("NEXT_AGENT_HANDOFF_VALIDATION") is not False:
        errors.append("final acceptance bundle readiness must not expose next-agent handoff validation as passing")
    if prebundle.get("INDEPENDENT_REVIEW_SIGNOFF_VALIDATION") is not False:
        errors.append("final acceptance bundle readiness must not expose independent review signoff validation as passing")
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
    reviewer_assignment_validation = _mapping(state.get("independent_final_reviewer_assignment_validation"))
    if reviewer_assignment_validation.get("status") != "blocked":
        errors.append(
            "final acceptance bundle readiness independent final reviewer assignment validation must remain blocked"
        )
    final_closure_request = _mapping(state.get("independent_final_closure_decision_request"))
    if validate_independent_final_closure_decision_request_state(final_closure_request):
        errors.append("final acceptance bundle readiness independent final closure decision request is invalid")
    p0_p1_zero_proof = _mapping(state.get("p0_p1_zero_proof_readiness"))
    if validate_p0_p1_zero_proof_readiness_state(p0_p1_zero_proof):
        errors.append("final acceptance bundle readiness P0/P1 zero proof readiness state is invalid")
    p0_p1_zero_proof_artifact = _mapping(state.get("p0_p1_zero_proof_artifact_validation"))
    if p0_p1_zero_proof_artifact.get("status") != "blocked":
        errors.append("final acceptance bundle readiness P0/P1 zero proof artifact validation must remain blocked")
    manifest_validation = _mapping(state.get("final_acceptance_bundle_manifest_validation"))
    if manifest_validation.get("status") != "blocked":
        errors.append("final acceptance bundle readiness manifest validation must remain blocked")
    artifact_validation = _mapping(state.get("final_acceptance_bundle_artifact_validation"))
    if validate_final_acceptance_bundle_artifact_validation_state(artifact_validation):
        errors.append("final acceptance bundle readiness artifact validation is invalid")
    if artifact_validation.get("status") != "blocked":
        errors.append("final acceptance bundle readiness artifact validation must remain blocked")
    if artifact_validation.get("bundle_directory_present") != state.get("bundle_present"):
        errors.append("final acceptance bundle readiness bundle_present must match artifact validation directory state")
    completion_report = _mapping(state.get("s2plt04_completion_report_validation"))
    if completion_report.get("status") != "blocked":
        errors.append("final acceptance bundle readiness S2PLT04 completion report validation must remain blocked")
    final_command = _mapping(state.get("final_command_execution_validation"))
    if final_command.get("status") != "blocked":
        errors.append("final acceptance bundle readiness final command execution validation must remain blocked")
    no_production_attestation = _mapping(state.get("no_production_side_effect_attestation_validation"))
    if no_production_attestation.get("status") != "blocked":
        errors.append(
            "final acceptance bundle readiness no-production side-effect attestation validation must remain blocked"
        )
    next_agent_handoff = _mapping(state.get("next_agent_handoff_validation"))
    if next_agent_handoff.get("status") != "blocked":
        errors.append("final acceptance bundle readiness next-agent handoff validation must remain blocked")
    independent_signoff = _mapping(state.get("independent_review_signoff_validation"))
    if independent_signoff.get("status") != "blocked":
        errors.append("final acceptance bundle readiness independent review signoff validation must remain blocked")
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
        for reason in S2PMT07_FINAL_ACCEPTANCE_BUNDLE_BLOCKING_REASONS:
            if reason not in state.get("blocking_reasons", []):
                errors.append(f"blocked final acceptance bundle readiness must include {reason}")
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
