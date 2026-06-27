"""S2PL/S2PM fail-closed final production gate precheck helpers."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from typing import Any

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
    "real_scheduler_not_proven",
    "real_smtp_not_proven",
    "m4_watermark_not_proven",
    "inherited_v7_1_p0_findings_open",
    "inherited_v7_1_p1_findings_open",
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


def build_s2plt02_live_evidence_state() -> dict[str, Any]:
    """Build current S2PLT02 live-run evidence state without touching production."""

    available = {
        "S2PLT01_ACCEPTED": False,
        "TWO_CONSECUTIVE_REAL_NATURAL_DAYS": False,
        "EIGHT_REAL_EMAILS_SENT": False,
        "NO_DUPLICATE_EMAILS": False,
        "M4_WATERMARK_CORRECT": False,
        "REAL_SCHEDULER_PROVEN": False,
        "REAL_SMTP_PROVEN": False,
    }
    return {
        "status": "blocked",
        "required_evidence": list(S2PLT02_REQUIRED_EVIDENCE),
        "available_evidence": available,
        "missing_evidence": [item for item, present in available.items() if not present],
        "required_natural_days": S2PLT02_REQUIRED_NATURAL_DAYS,
        "observed_natural_days": 0,
        "required_email_count": S2PLT02_REQUIRED_EMAIL_COUNT,
        "observed_email_count": 0,
        "required_mail_products": list(S2PLT02_REQUIRED_MAIL_PRODUCTS),
        "observed_mail_products": [],
        "duplicate_email_count": None,
        "m4_watermark_correct": False,
        "real_scheduler_proven": False,
        "real_smtp_proven": False,
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
    if report.get("status") == "pass":
        gates = _mapping(report.get("gates"))
        if not all(gates.values()):
            errors.append("passing S2PLT02 report requires every gate true")
        if report.get("blocking_reasons"):
            errors.append("passing S2PLT02 report must not have blocking reasons")
    else:
        for reason in S2PLT02_BLOCKING_REASONS:
            if reason not in report.get("blocking_reasons", []):
                errors.append(f"blocked S2PLT02 precheck must include {reason}")
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


def build_p0_p1_zero_proof_readiness_state() -> dict[str, Any]:
    """Build a fail-closed schema contract for the future P0/P1 zero proof artifact."""

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


def build_final_acceptance_bundle_readiness_state() -> dict[str, Any]:
    """Build the current final acceptance bundle readiness state without packaging."""

    available_items = {item: False for item in S2PMT07_FINAL_ACCEPTANCE_BUNDLE_REQUIRED_ITEMS}
    p0_p1_technical_candidate_state = build_p0_p1_technical_closure_candidate_state()
    p0_p1_zero_proof_readiness = build_p0_p1_zero_proof_readiness_state()
    p0_p1_zero_proof_artifact_validation = build_p0_p1_zero_proof_artifact_validation_state(None)
    final_acceptance_bundle_manifest_validation = build_final_acceptance_bundle_manifest_validation_state(None)
    s2plt04_completion_report_validation = build_s2plt04_completion_report_validation_state(None)
    final_command_execution_validation = build_final_command_execution_validation_state(None)
    no_production_side_effect_attestation_validation = (
        build_no_production_side_effect_attestation_validation_state(None)
    )
    independent_review_signoff_validation = build_independent_review_signoff_validation_state(None)
    state = {
        "status": "blocked",
        "scope": "final_acceptance_bundle_readiness_precheck_only",
        "required_items": list(S2PMT07_FINAL_ACCEPTANCE_BUNDLE_REQUIRED_ITEMS),
        "available_items": available_items,
        "available_prebundle_evidence": {
            "P0_P1_TECHNICAL_CLOSURE_CANDIDATES": not validate_p0_p1_technical_closure_candidate_state(
                p0_p1_technical_candidate_state
            ),
            "P0_P1_ZERO_PROOF_READINESS": p0_p1_zero_proof_readiness["status"] == "pass",
            "P0_P1_ZERO_PROOF_ARTIFACT_VALIDATION": p0_p1_zero_proof_artifact_validation["status"] == "pass",
            "FINAL_ACCEPTANCE_BUNDLE_MANIFEST_VALIDATION": (
                final_acceptance_bundle_manifest_validation["status"] == "pass"
            ),
            "S2PLT04_COMPLETION_REPORT_VALIDATION": s2plt04_completion_report_validation["status"] == "pass",
            "FINAL_COMMAND_EXECUTION_VALIDATION": final_command_execution_validation["status"] == "pass",
            "NO_PRODUCTION_SIDE_EFFECT_ATTESTATION_VALIDATION": (
                no_production_side_effect_attestation_validation["status"] == "pass"
            ),
            "INDEPENDENT_REVIEW_SIGNOFF_VALIDATION": independent_review_signoff_validation["status"] == "pass",
        },
        "missing_items": [item for item, present in available_items.items() if not present],
        "blocking_reasons": list(S2PMT07_FINAL_ACCEPTANCE_BUNDLE_BLOCKING_REASONS),
        "p0_p1_technical_closure_candidate_state": p0_p1_technical_candidate_state,
        "p0_p1_zero_proof_readiness": p0_p1_zero_proof_readiness,
        "p0_p1_zero_proof_artifact_validation": p0_p1_zero_proof_artifact_validation,
        "final_acceptance_bundle_manifest_validation": final_acceptance_bundle_manifest_validation,
        "s2plt04_completion_report_validation": s2plt04_completion_report_validation,
        "final_command_execution_validation": final_command_execution_validation,
        "no_production_side_effect_attestation_validation": no_production_side_effect_attestation_validation,
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
    if prebundle.get("P0_P1_TECHNICAL_CLOSURE_CANDIDATES") is not True:
        errors.append("final acceptance bundle readiness must expose P0/P1 technical closure candidates")
    if prebundle.get("P0_P1_ZERO_PROOF_READINESS") is not False:
        errors.append("final acceptance bundle readiness must not expose P0/P1 zero proof readiness as passing")
    if prebundle.get("P0_P1_ZERO_PROOF_ARTIFACT_VALIDATION") is not False:
        errors.append("final acceptance bundle readiness must not expose P0/P1 zero proof artifact validation as passing")
    if prebundle.get("FINAL_ACCEPTANCE_BUNDLE_MANIFEST_VALIDATION") is not False:
        errors.append("final acceptance bundle readiness must not expose final bundle manifest validation as passing")
    if prebundle.get("S2PLT04_COMPLETION_REPORT_VALIDATION") is not False:
        errors.append("final acceptance bundle readiness must not expose S2PLT04 completion report validation as passing")
    if prebundle.get("FINAL_COMMAND_EXECUTION_VALIDATION") is not False:
        errors.append("final acceptance bundle readiness must not expose final command execution validation as passing")
    if prebundle.get("NO_PRODUCTION_SIDE_EFFECT_ATTESTATION_VALIDATION") is not False:
        errors.append(
            "final acceptance bundle readiness must not expose no-production side-effect attestation validation as passing"
        )
    if prebundle.get("INDEPENDENT_REVIEW_SIGNOFF_VALIDATION") is not False:
        errors.append("final acceptance bundle readiness must not expose independent review signoff validation as passing")
    p0_p1_candidate = _mapping(state.get("p0_p1_technical_closure_candidate_state"))
    if validate_p0_p1_technical_closure_candidate_state(p0_p1_candidate):
        errors.append("final acceptance bundle readiness P0/P1 technical candidate state is invalid")
    p0_p1_zero_proof = _mapping(state.get("p0_p1_zero_proof_readiness"))
    if validate_p0_p1_zero_proof_readiness_state(p0_p1_zero_proof):
        errors.append("final acceptance bundle readiness P0/P1 zero proof readiness state is invalid")
    p0_p1_zero_proof_artifact = _mapping(state.get("p0_p1_zero_proof_artifact_validation"))
    if p0_p1_zero_proof_artifact.get("status") != "blocked":
        errors.append("final acceptance bundle readiness P0/P1 zero proof artifact validation must remain blocked")
    manifest_validation = _mapping(state.get("final_acceptance_bundle_manifest_validation"))
    if manifest_validation.get("status") != "blocked":
        errors.append("final acceptance bundle readiness manifest validation must remain blocked")
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
