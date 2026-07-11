#!/usr/bin/env python3
"""Validate and evaluate the STAGE-037 metadata-only job-state contract."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
from typing import Any, Mapping, Optional
import unicodedata


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PURSUE_ROOT = PROJECT_ROOT / "docs" / "pursuing_goal" / "ids_v0_1"
INDEX_PATH = PURSUE_ROOT / "job_state_model" / "stage037_job_state_model_index.json"
REVIEW_ARTIFACT_PATH = PURSUE_ROOT / "STAGE037_STAGE_REVIEW.md"
BATCH_LOCK_PATH = PURSUE_ROOT / "BATCH031_040_UPLOAD_LOCK.yaml"
ROADMAP_PATH = PROJECT_ROOT / "docs" / "governance" / "roadmap.yaml"
EVENTS_PATH = PROJECT_ROOT / "docs" / "governance" / "events.jsonl"
GOVERNANCE_VALIDATOR_PATH = PURSUE_ROOT / "validate_stage005_governance_regression.py"

INDEX_SCHEMA_VERSION = "ids.stage037.job_state_model.index.v1"
REPORT_SCHEMA_VERSION = "ids.stage037.job_state_model.phase2.v1"
DECISION_SCHEMA_VERSION = "ids.stage037.job_state_model.transition_decision.v1"
CONTRACT_ID = "ids_stage037_job_state_model_static_slice"
VALID_STATE = "STATIC_JOB_STATE_CONTRACT_VALID_RUNTIME_DISABLED"
INVALID_STATE = "BLOCKED_INVALID_JOB_STATE_CONTRACT"
EXECUTION_MODE = "METADATA_ONLY_DETERMINISTIC_CONTRACT_EVALUATION"
EVALUATION_MODE = "STATIC_CONTRACT_EVALUATION_ONLY"
TASK_ID = "IDS-V0_1-STAGE037-P2"
ACCEPTANCE_ID = "ACC-STAGE-037"
NEXT_GATE = "IDS-STAGE037-P3-GATE"
PHASE3_REPORT_SCHEMA_VERSION = "ids.stage037.job_state_model.phase3.v1"
PHASE3_TASK_ID = "IDS-V0_1-STAGE037-P3"
PHASE3_NEXT_GATE = "IDS-STAGE037-P4-GATE"
PHASE3_VALID_STATE = "STATIC_JOB_STATE_SCENARIOS_VALID_RUNTIME_DISABLED"
PHASE3_EXECUTION_MODE = (
    "STATIC_JOB_STATE_ADVERSARIAL_SCENARIO_VALIDATION_ONLY"
)
SCENARIO_FACT_LEVEL = "STATIC_CONTRACT_SCENARIO_ONLY"
PHASE4_REPORT_SCHEMA_VERSION = "ids.stage037.job_state_model.phase4.v1"
PHASE4_CONTRACT_SCHEMA_VERSION = (
    "ids.stage037.job_state_model.delivery_contract.v1"
)
PHASE4_TASK_ID = "IDS-V0_1-STAGE037-P4"
PHASE4_NEXT_GATE = "IDS-STAGE037-REVIEW-GATE"
PHASE4_VALID_STATE = "STATIC_JOB_STATE_CLOSEOUT_VALID_RUNTIME_DISABLED"
PHASE4_EXECUTION_MODE = "STATIC_TRACKED_CLOSEOUT_EVIDENCE_ONLY"
PHASE4_VALID_RESULT = "PASS_STATIC_CLOSEOUT_RUNTIME_DISABLED"
REVIEW_STATUS = "completed_reviewed_local"
REVIEW_NEXT_GATE = "IDS-STAGE038-P1-GATE"
BLOCKED_REVIEW_STATUS = "blocked_invalid_review_evidence"
REVIEW_OWNER_FEEDBACK_ZH = (
    "STAGE-037 已完成本地 whole-stage review；直接与暂停重试资格、取消原因、"
    "完整 job envelope、中文中间态、结构化治理及 Git-index 交付/复审证据均已修复。"
    "当前仍未运行队列、worker、重试、数据库、清理或真实任务，批次上传继续阻断。"
)

EXPECTED_PHASE3_SCENARIOS = (
    "duplicate_click_idempotent_replay",
    "duplicate_click_payload_conflict",
    "worker_crash_retry_reservation",
    "stale_worker_fencing_block",
    "removable_drive_offline_pause",
    "drive_reconnect_no_auto_resume",
    "low_disk_retry_pause_preserves_budget",
    "same_source_concurrency_blocked",
    "lock_claim_without_proof_blocked",
    "cleanup_authorization_blocked",
)

EXPECTED_PHASE4_EVIDENCE_REFS = {
    "phase1_scope_ref": "../STAGE037_PHASE1_SCOPE_BOUNDARY.md",
    "phase2_slice_ref": "../STAGE037_PHASE2_JOB_STATE_MODEL_SLICE.md",
    "phase3_scenarios_ref": "../STAGE037_PHASE3_ADVERSARIAL_SCENARIOS.md",
    "phase4_closeout_ref": "../STAGE037_PHASE4_CLOSEOUT.md",
}
EXPECTED_PHASE4_EVIDENCE_SHA256 = {
    "phase1_scope_ref": "e692bfb2f4786c076135888731c6eca6ce0f342a8fa19c1334394ca2d3db3730",
    "phase2_slice_ref": "e29690f7d7c45760c53cbc69f5594dc15d8b3ba31d36bd270bf778d2f622d3d9",
    "phase3_scenarios_ref": "059033f50b1aba9ff1cc72ea716efb0895a0e292e72ec50e518041ff588c12f8",
    "phase4_closeout_ref": "00beec1b60d7dbdb6da5678dcbbcf2d9c6d02826979403797759798ea518201a",
}
EXPECTED_SAFE_SHUTDOWN_GUARDS = {
    "stop_new_admission": ("queue_admission_runtime_performed", False),
    "request_safe_checkpoint": ("checkpoint_runtime_performed", False),
    "deactivate_and_fence": ("deactivation_runtime_performed", False),
    "preserve_source_and_evidence": (
        "source_or_evidence_deletion_allowed",
        False,
    ),
}
EXPECTED_RECOVERY_GUARDS = {
    "record_worker_loss_evidence": ("fabricated_crash_log_allowed", False),
    "cas_deactivate_expired_attempt": ("recovery_runtime_performed", False),
    "reserve_retry_without_consuming": (
        "retry_admission_runtime_performed",
        False,
    ),
    "require_owner_resource_revalidation": ("automatic_resume_allowed", False),
    "block_stale_worker_commit": ("stale_worker_commit_allowed", False),
}
EXPECTED_ROLLBACK_GUARDS = {
    "stop_on_invalid_contract": ("runtime_action_allowed", False),
    "revert_phase4_contract_only": ("phase1_phase3_revert_allowed", False),
    "preserve_phase1_phase3_evidence": (
        "prior_evidence_mutation_allowed",
        False,
    ),
    "preserve_data_and_runtime": ("data_or_runtime_mutation_allowed", False),
}
EXPECTED_KNOWN_LIMIT_IDS = {
    "no_queue_or_worker_runtime",
    "numeric_policies_deferred",
    "no_live_crash_or_recovery",
    "no_cleanup_runtime",
    "no_database_or_registry_execution",
    "static_closeout_is_not_readiness",
    "stage_review_and_batch_upload_blocked",
}

JOB_TYPES = [
    "IMPORT",
    "ARCHIVE",
    "PARSE",
    "OCR",
    "CHUNK",
    "EMBED",
    "INDEX",
    "REPORT",
]
JOB_STATES = [
    "CREATED",
    "QUEUED",
    "CLAIMED",
    "RUNNING",
    "PAUSE_REQUESTED",
    "PAUSED",
    "RETRY_WAIT",
    "SUCCEEDED",
    "FAILED",
    "DEAD_LETTERED",
    "CANCELLED",
]
TERMINAL_STATES = ["SUCCEEDED", "FAILED", "DEAD_LETTERED", "CANCELLED"]
ACTIVE_STATES = ["CLAIMED", "RUNNING", "PAUSE_REQUESTED"]
ALLOWED_TRANSITIONS = {
    "CREATED": ["QUEUED", "CANCELLED"],
    "QUEUED": ["CLAIMED", "PAUSED", "CANCELLED"],
    "CLAIMED": ["RUNNING", "PAUSE_REQUESTED", "RETRY_WAIT"],
    "RUNNING": ["SUCCEEDED", "PAUSE_REQUESTED", "RETRY_WAIT", "FAILED"],
    "PAUSE_REQUESTED": ["PAUSED", "CANCELLED", "RETRY_WAIT"],
    "PAUSED": ["QUEUED", "CANCELLED"],
    "RETRY_WAIT": ["QUEUED", "PAUSED", "DEAD_LETTERED", "CANCELLED"],
}

EXPECTED_SOURCE_HASHES = {
    "phase1_scope_ref": "e692bfb2f4786c076135888731c6eca6ce0f342a8fa19c1334394ca2d3db3730",
    "removable_drive_state_ref": "e7bca4b8ad2be3ab1c5c91ace5c6741309faa4c0f53509e1cd1ba1c7779a5fc9",
    "storage_budget_ref": "4e43fb28d0616fcacfe8303146f6558b72e2478cd2c32163ec61041d914e2cdf",
    "safe_mode_ref": "ee1aa8202ff40bc69a50fc5d515afd3cf5cfa48df8bcaf8ca8a1e5ef5baa44e3",
    "import_idempotency_ref": "43b91e02072c56d0459dd7e62ed653f1702848f9eb725fffb1183f7715498765",
    "priority_queue_ref": "7abcc97a3812454b6767d88989c53992d2db45db4a56450ca24c6b47b05b8359",
    "control_plane_schema_ref": "9fa7b8e535fe799c0aed14d738f568b33a19fc2835eeb492c8217bc35b588479",
    "database_quality_index_ref": "016abaa478da1c6cc98513e432429a26402fde5b0b5ac050ec4ceb03aeb33271",
    "state_registry_structure_ref": "52cd624f9e3bec197fa20a14405c7fe2ea149362115c33e9de0145b315dd455a",
    "raw_data_boundary_ref": "ad4695abf250049699a1b96b49b81432e5d5754dfe7de69c7f3056463a0a7d51",
}

EXPECTED_SOURCE_REFS = {
    "phase1_scope_ref": "../STAGE037_PHASE1_SCOPE_BOUNDARY.md",
    "phase2_slice_ref": "../STAGE037_PHASE2_JOB_STATE_MODEL_SLICE.md",
    "removable_drive_state_ref": "../STAGE008_PHASE2_REMOVABLE_DRIVE_STATE.md",
    "storage_budget_ref": "../STAGE009_PHASE2_STORAGE_BUDGET_BASELINE.md",
    "safe_mode_ref": "../STAGE011_PHASE2_SAFE_MODE_BASELINE.md",
    "import_idempotency_ref": "../STAGE016_PHASE2_IMPORT_IDEMPOTENCY_SLICE.md",
    "priority_queue_ref": "../STAGE022_PHASE2_DATA_PRIORITY_QUEUE_SLICE.md",
    "control_plane_schema_ref": (
        "../postgresql_control_plane/001_control_plane_schema.sql"
    ),
    "database_quality_index_ref": (
        "../database_quality_constraints/stage036_database_quality_constraints_index.json"
    ),
    "state_registry_structure_ref": (
        "../database_quality_constraints/002_database_quality_constraints.sql"
    ),
    "raw_data_boundary_ref": "../IDS_METADATA_RAW_DATA_BOUNDARY.md",
    "phase2_checker_ref": "../../../../scripts/check_job_state_model.py",
}

EXPECTED_GUARD_FACTS = [
    "identity_idempotency_valid",
    "admission_gates_passed",
    "no_active_claim_or_lock",
    "claim_lease_and_lock_acquired",
    "live_lease_valid",
    "lease_valid_or_expiry_evidence",
    "fencing_token_matches",
    "pause_intent_recorded",
    "checkpoint_or_quarantine_complete",
    "output_validated",
    "retryable_failure_recorded",
    "permanent_failure_recorded",
    "error_evidence_present",
    "resource_gate_blocked",
    "resource_gates_passed",
    "owner_revalidated",
    "next_eligible_reached",
    "retry_exhaustion_confirmed",
    "cancellation_requested",
]

EXPECTED_EDGE_GUARDS = {
    "CREATED->QUEUED": [
        "identity_idempotency_valid",
        "admission_gates_passed",
        "no_active_claim_or_lock",
    ],
    "CREATED->CANCELLED": ["no_active_claim_or_lock"],
    "QUEUED->CLAIMED": [
        "admission_gates_passed",
        "claim_lease_and_lock_acquired",
    ],
    "QUEUED->PAUSED": ["resource_gate_blocked", "no_active_claim_or_lock"],
    "QUEUED->CANCELLED": ["no_active_claim_or_lock"],
    "CLAIMED->RUNNING": ["live_lease_valid", "fencing_token_matches"],
    "CLAIMED->PAUSE_REQUESTED": [
        "live_lease_valid",
        "fencing_token_matches",
        "pause_intent_recorded",
    ],
    "CLAIMED->RETRY_WAIT": [
        "lease_valid_or_expiry_evidence",
        "fencing_token_matches",
        "retryable_failure_recorded",
        "error_evidence_present",
    ],
    "RUNNING->SUCCEEDED": [
        "live_lease_valid",
        "fencing_token_matches",
        "output_validated",
    ],
    "RUNNING->PAUSE_REQUESTED": [
        "live_lease_valid",
        "fencing_token_matches",
        "pause_intent_recorded",
    ],
    "RUNNING->RETRY_WAIT": [
        "lease_valid_or_expiry_evidence",
        "fencing_token_matches",
        "retryable_failure_recorded",
        "error_evidence_present",
    ],
    "RUNNING->FAILED": [
        "live_lease_valid",
        "fencing_token_matches",
        "permanent_failure_recorded",
        "error_evidence_present",
    ],
    "PAUSE_REQUESTED->PAUSED": [
        "lease_valid_or_expiry_evidence",
        "fencing_token_matches",
        "checkpoint_or_quarantine_complete",
    ],
    "PAUSE_REQUESTED->CANCELLED": [
        "lease_valid_or_expiry_evidence",
        "fencing_token_matches",
        "checkpoint_or_quarantine_complete",
        "cancellation_requested",
    ],
    "PAUSE_REQUESTED->RETRY_WAIT": [
        "lease_valid_or_expiry_evidence",
        "fencing_token_matches",
        "retryable_failure_recorded",
        "error_evidence_present",
    ],
    "PAUSED->QUEUED": [
        "owner_revalidated",
        "resource_gates_passed",
        "no_active_claim_or_lock",
    ],
    "PAUSED->CANCELLED": ["no_active_claim_or_lock"],
    "RETRY_WAIT->QUEUED": [
        "next_eligible_reached",
        "resource_gates_passed",
        "no_active_claim_or_lock",
    ],
    "RETRY_WAIT->PAUSED": [
        "resource_gate_blocked",
        "no_active_claim_or_lock",
    ],
    "RETRY_WAIT->DEAD_LETTERED": [
        "retry_exhaustion_confirmed",
        "no_active_claim_or_lock",
    ],
    "RETRY_WAIT->CANCELLED": ["no_active_claim_or_lock"],
}

EXPECTED_EDGE_REFERENCES = {
    "CREATED->QUEUED": ["input_refs", "audit_ref"],
    "CREATED->CANCELLED": ["stop_reason", "audit_ref"],
    "QUEUED->CLAIMED": ["candidate_claim", "audit_ref"],
    "QUEUED->PAUSED": ["pause_reason_code", "resource_gate_refs", "audit_ref"],
    "QUEUED->CANCELLED": ["stop_reason", "audit_ref"],
    "CLAIMED->RUNNING": ["fencing_token", "audit_ref"],
    "CLAIMED->PAUSE_REQUESTED": [
        "fencing_token",
        "pause_reason_code",
        "audit_ref",
    ],
    "CLAIMED->RETRY_WAIT": ["fencing_token", "error_ref", "audit_ref"],
    "RUNNING->SUCCEEDED": ["fencing_token", "output_refs", "audit_ref"],
    "RUNNING->PAUSE_REQUESTED": [
        "fencing_token",
        "pause_reason_code",
        "audit_ref",
    ],
    "RUNNING->RETRY_WAIT": ["fencing_token", "error_ref", "audit_ref"],
    "RUNNING->FAILED": ["fencing_token", "error_ref", "audit_ref"],
    "PAUSE_REQUESTED->PAUSED": [
        "fencing_token",
        "checkpoint_or_quarantine_ref",
        "pause_reason_code",
        "audit_ref",
    ],
    "PAUSE_REQUESTED->CANCELLED": [
        "fencing_token",
        "checkpoint_or_quarantine_ref",
        "stop_reason",
        "audit_ref",
    ],
    "PAUSE_REQUESTED->RETRY_WAIT": [
        "fencing_token",
        "error_ref",
        "audit_ref",
    ],
    "PAUSED->QUEUED": ["audit_ref"],
    "PAUSED->CANCELLED": ["stop_reason", "audit_ref"],
    "RETRY_WAIT->QUEUED": ["next_eligible_evidence_ref", "audit_ref"],
    "RETRY_WAIT->PAUSED": [
        "pause_reason_code",
        "resource_gate_refs",
        "audit_ref",
    ],
    "RETRY_WAIT->DEAD_LETTERED": ["error_ref", "audit_ref"],
    "RETRY_WAIT->CANCELLED": ["stop_reason", "audit_ref"],
}

EXPECTED_PROJECTIONS = {
    "CREATED": ("等待处理", "查看优先级或暂停", False),
    "QUEUED": ("等待处理", "查看优先级或暂停", False),
    "CLAIMED": ("处理中", "查看进度；必要时安全暂停", False),
    "RUNNING": ("处理中", "查看进度；必要时安全暂停", False),
    "PAUSE_REQUESTED": ("暂停中", "查看原因并等待安全检查点", True),
    "PAUSED": ("已暂停", "查看原因并完成复核", True),
    "RETRY_WAIT": ("等待重试", "查看安全错误与下次资格时间", False),
    "SUCCEEDED": ("已完成", "查看已验证输出引用", False),
    "FAILED": ("处理失败", "查看原因并决定是否新建重跑", True),
    "DEAD_LETTERED": ("需要人工处理", "人工复核，不自动继续", True),
    "CANCELLED": ("已取消", "确认无自动副作用", False),
}

EXPECTED_OWNERSHIP = {
    "queue_and_claim_transport": "STAGE-038",
    "retry_and_dead_letter_policy": "STAGE-039",
    "backpressure_runtime": "STAGE-040",
    "lock_lease_and_fencing_runtime": "STAGE-041",
    "automatic_lifecycle_runtime": "STAGE-042",
    "worker_crash_recovery": "STAGE-043",
    "half_product_cleanup_runtime": "STAGE-044",
}

TOP_LEVEL_KEYS = {
    "schema_version",
    "stage",
    "phase",
    "task_id",
    "acceptance_id",
    "local_code",
    "domain",
    "entrance",
    "job_state_model_contract_id",
    "contract_state",
    "execution_mode",
    "execution_ready",
    "next_gate",
    "source_refs",
    "dependency_contract",
    "state_model",
    "job_control_envelope_contract",
    "transition_contract",
    "deactivation_contract",
    "retry_contract",
    "reference_policy",
    "cleanup_boundary",
    "human_status_projection",
    "downstream_ownership",
    "runtime_policy",
    "delivery_policy",
    "phase4_delivery_contract",
    "truth_contract",
}
JOB_CONTROL_ENVELOPE_KEYS = {
    "schema_version",
    "phase2_scope",
    "all_fields",
    "phase2_snapshot_fields",
    "phase2_request_fields",
    "runtime_persistence_owner",
    "runtime_persistence_performed",
    "timestamp_fabrication_allowed",
}
EXPECTED_JOB_CONTROL_ENVELOPE_FIELDS = [
    "job_id",
    "job_type",
    "job_state",
    "state_version",
    "idempotency_key",
    "transition_request_id",
    "parent_job_id",
    "dependency_refs",
    "attempt_id",
    "retry_count",
    "max_retries",
    "retry_pending",
    "next_eligible_at",
    "input_refs",
    "output_refs",
    "checkpoint_ref",
    "operation_contract_version",
    "lease_owner_ref",
    "lease_expires_at",
    "fencing_token",
    "lock_key",
    "priority_ref",
    "pause_reason_code",
    "stop_reason",
    "owner_action_ref",
    "resource_gate_refs",
    "safe_error_code",
    "error_ref",
    "audit_ref",
    "transition_actor_ref",
    "created_at",
    "updated_at",
    "cleanup_manifest_ref",
]
DEPENDENCY_KEYS = {
    "source_sha256",
    "required_control_plane_table",
    "required_job_columns",
    "state_registry_table",
    "state_registry_write_allowed",
    "postgres_connection_allowed",
}
STATE_MODEL_KEYS = {
    "state_namespace",
    "state_model_version",
    "introduced_version",
    "job_types",
    "job_states",
    "terminal_states",
    "active_execution_states",
    "allowed_transitions",
    "pause_reason_is_state",
    "terminal_state_mutation_allowed",
    "direct_running_cancel_allowed",
}
TRANSITION_KEYS = {
    "compare_and_set_fields",
    "state_version_increment",
    "transition_request_id_unique",
    "idempotent_replay_returns_original_result",
    "request_id_payload_conflict_fails_closed",
    "append_only_audit_required",
    "runtime_transition_performed",
    "snapshot_required_fields",
    "transition_request_required_fields",
    "guard_facts_allowed",
    "edge_guard_requirements",
    "edge_reference_requirements",
}
DEACTIVATION_KEYS = {
    "active_states",
    "non_active_destinations",
    "atomic_state_and_audit",
    "lease_revoked",
    "lock_revoked",
    "fencing_token_advanced",
    "stale_worker_commit_allowed",
}
RETRY_KEYS = {
    "max_retries_definition",
    "initial_retry_count",
    "total_attempt_limit_formula",
    "max_retries_immutable",
    "eligible_entry_sets_retry_pending",
    "eligible_entry_increments_retry_count",
    "retry_admission_increments_retry_count",
    "retry_admission_clears_retry_pending",
    "retry_pause_preserves_retry_pending",
    "paused_retry_resume_consumes_pending_retry",
    "ordinary_pause_consumes_retry",
    "exhausted_entry_retry_pending",
    "exhausted_disposition",
    "exhausted_only_next_state",
    "resource_gate_can_pause_exhausted_retry",
    "running_to_dead_letter_allowed",
    "retry_delay_policy",
    "next_eligible_at_required_for_eligible_retry",
    "next_eligible_evidence_required_for_admission",
    "paused_retry_resume_requires_next_eligible_at",
    "paused_retry_resume_requires_next_eligible_evidence",
    "paused_retry_resume_requires_next_eligible_reached",
    "retry_scheduler_allowed",
}
EXPECTED_FORBIDDEN_KEY_TOKENS = [
    "api_key",
    "password",
    "credential",
    "plaintext_secret",
    "dsn",
    "raw_content",
    "source_body",
    "document_body",
    "ocr_body",
    "vector_payload",
    "report_binary",
    "raw_log",
]
REFERENCE_KEYS = {
    "maximum_text_length",
    "maximum_refs_per_field",
    "absolute_path_allowed",
    "parent_path_segment_allowed",
    "file_uri_allowed",
    "backslash_separator_allowed",
    "percent_encoded_path_tokens_allowed",
    "unicode_path_separator_normalization_required",
    "case_insensitive_path_guard_required",
    "raw_metadata_root",
    "raw_metadata_content_access_allowed",
    "forbidden_key_tokens",
    "bounded_ref_fields",
    "raw_body_fields_allowed",
    "plaintext_secrets_allowed",
}
CLEANUP_KEYS = {
    "cleanup_runtime_allowed",
    "state_transition_authorizes_deletion",
    "cleanup_owner",
    "approved_root_identity_required",
    "root_relative_path_required",
    "lstat_identity_required",
    "symlink_allowed",
    "exclusive_namespace_lock_required",
    "writer_quiescence_required",
    "openat_no_follow_required",
    "unlinkat_required",
    "source_and_durable_evidence_targets_allowed",
}
RUNTIME_KEYS = {
    "queue_runtime_allowed",
    "worker_runtime_allowed",
    "retry_scheduler_allowed",
    "dead_letter_runtime_allowed",
    "backpressure_runtime_allowed",
    "lock_runtime_allowed",
    "automatic_lifecycle_runtime_allowed",
    "cleanup_runtime_allowed",
    "postgres_connection_allowed",
    "state_registry_write_allowed",
    "schema_change_allowed",
    "runtime_output_allowed",
    "source_read_allowed",
}
DELIVERY_KEYS = {
    "github_upload_allowed",
    "pull_request_allowed",
    "merge_allowed",
    "app_reinstall_allowed",
    "stage_review_allowed_in_phase2",
    "batch_review_allowed",
    "next_phase_allowed",
    "next_gate",
}
PHASE4_CONTRACT_KEYS = {
    "schema_version",
    "state_graph",
    "retry_evidence_contract",
    "backpressure_evidence_contract",
    "cleanup_evidence_contract",
    "automatic_manual_boundary",
    "safe_shutdown_steps",
    "recovery_steps",
    "rollback_steps",
    "known_limits",
    "evidence_refs",
    "evidence_sha256",
    "stage_review_status",
    "next_gate",
    "github_upload_allowed",
    "app_reinstall_allowed",
    "chinese_owner_feedback",
}
PHASE4_STATE_GRAPH_KEYS = {
    "mode",
    "state_model_version",
    "job_type_count",
    "job_state_count",
    "allowed_transition_count",
    "terminal_state_count",
    "active_execution_state_count",
    "source_ref",
    "runtime_transition_performed",
}
PHASE4_RETRY_KEYS = {
    "mode",
    "runtime_owner",
    "total_attempt_limit_formula",
    "reservation_increments_retry_count",
    "admission_increments_retry_count",
    "resource_pause_preserves_reservation",
    "exhausted_only_next_state",
    "numeric_policy",
    "retry_scheduler_performed",
    "dead_letter_runtime_performed",
}
PHASE4_BACKPRESSURE_KEYS = {
    "mode",
    "runtime_owner",
    "pause_reason_is_state",
    "resource_gate_required",
    "retry_budget_consumed_while_blocked",
    "numeric_policy",
    "backpressure_runtime_performed",
}
PHASE4_CLEANUP_KEYS = {
    "mode",
    "runtime_owner",
    "state_transition_authorizes_deletion",
    "approved_root_identity_required",
    "lstat_identity_required",
    "symlink_allowed",
    "exclusive_namespace_lock_required",
    "writer_quiescence_required",
    "openat_no_follow_required",
    "unlinkat_required",
    "source_and_durable_evidence_targets_allowed",
    "cleanup_runtime_performed",
}
PHASE4_AUTOMATIC_MANUAL_KEYS = {
    "mode",
    "runtime_owner",
    "automatic_run_allowed",
    "automatic_resume_allowed",
    "automatic_shutdown_allowed",
    "owner_revalidation_required_for_resume",
    "safe_deactivation_required_for_cancel",
    "terminal_history_rewrite_allowed",
    "automatic_lifecycle_runtime_performed",
}
EXPECTED_TRUTH_CONTRACT = {
    "runtime_transition_performed": False,
    "real_job_created": False,
    "fake_ids_business_data_used": False,
    "fake_database_row_used": False,
    "fabricated_job_log_or_evidence_used": False,
    "raw_metadata_content_accessed": False,
    "database_connected": False,
    "state_registry_written": False,
    "schema_changed": False,
    "runtime_output_written": False,
}

SNAPSHOT_KEYS = {
    "evaluation_mode",
    "job_id",
    "job_type",
    "job_state",
    "state_version",
    "retry_count",
    "max_retries",
    "retry_pending",
    "retry_disposition",
    "next_eligible_at",
    "lease_active",
    "lock_active",
    "fencing_token",
    "attempt_id",
    "lease_owner_ref",
    "lease_expires_at",
    "lock_key",
    "pause_reason_code",
    "stop_reason",
    "input_refs",
    "output_refs",
    "checkpoint_ref",
    "quarantine_ref",
    "error_ref",
}
REQUEST_KEYS = {
    "job_id",
    "transition_request_id",
    "expected_state",
    "expected_state_version",
    "target_state",
    "actor_ref",
    "reason_code",
    "audit_ref",
    "guard_facts",
    "input_refs",
    "output_refs",
    "checkpoint_ref",
    "quarantine_ref",
    "error_ref",
    "resource_gate_refs",
    "pause_reason_code",
    "stop_reason",
    "next_eligible_at",
    "next_eligible_evidence_ref",
    "fencing_token",
    "candidate_claim",
}
CLAIM_KEYS = {
    "attempt_id",
    "lease_owner_ref",
    "lease_expires_at",
    "fencing_token",
    "lock_key",
}
DECISION_KEYS = {
    "schema_version",
    "job_state_model_contract_id",
    "fact_level",
    "accepted",
    "result_code",
    "transition_request_id",
    "request_fingerprint_sha256",
    "previous_state",
    "requested_state",
    "idempotent_replay",
    "runtime_transition_performed",
    "database_write_performed",
    "queue_or_worker_action_performed",
    "next_snapshot",
    "transition_candidate",
    "human_status_projection",
}
TRANSITION_CANDIDATE_KEYS = {
    "candidate_only",
    "transition_request_id",
    "job_id",
    "job_type",
    "previous_state",
    "current_state",
    "previous_state_version",
    "current_state_version",
    "reason_code",
    "stop_reason",
    "next_eligible_at",
    "next_eligible_evidence_ref",
    "actor_ref",
    "audit_ref",
    "transition_timestamp",
    "timestamp_persistence_required",
    "append_only_audit_required",
    "persisted",
}
REF_SCALAR_FIELDS = {
    "job_id",
    "attempt_id",
    "lease_owner_ref",
    "lease_expires_at",
    "lock_key",
    "next_eligible_at",
    "next_eligible_evidence_ref",
    "transition_request_id",
    "actor_ref",
    "audit_ref",
    "checkpoint_ref",
    "quarantine_ref",
    "error_ref",
}
REF_LIST_FIELDS = {"input_refs", "output_refs", "resource_gate_refs"}


def _as_object(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def load_contract() -> dict[str, Any]:
    return _load_json(INDEX_PATH)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 128), b""):
            digest.update(block)
    return digest.hexdigest()


def _resolve_source_paths(index: Mapping[str, Any]) -> dict[str, Path]:
    refs = _as_object(index.get("source_refs"))
    resolved: dict[str, Path] = {}
    for name, value in refs.items():
        if not isinstance(name, str) or not isinstance(value, str):
            continue
        path = (INDEX_PATH.parent / value).resolve()
        if path == PROJECT_ROOT or PROJECT_ROOT in path.parents:
            resolved[name] = path
    return resolved


def _source_integrity(
    index: Mapping[str, Any],
) -> tuple[dict[str, bool], dict[str, Optional[str]]]:
    configured = _as_object(_as_object(index.get("dependency_contract")).get("source_sha256"))
    paths = _resolve_source_paths(index)
    checks: dict[str, bool] = {}
    observed: dict[str, Optional[str]] = {}
    for name, expected in EXPECTED_SOURCE_HASHES.items():
        path = paths.get(name)
        observed_hash: Optional[str] = None
        if path is not None and path.is_file():
            try:
                observed_hash = _sha256_file(path)
            except OSError:
                observed_hash = None
        observed[name] = observed_hash
        checks[name] = configured.get(name) == expected and observed_hash == expected
    checks["exact_hash_key_set"] = set(configured) == set(EXPECTED_SOURCE_HASHES)
    return checks, observed


def _all_edges(transitions: Mapping[str, Any]) -> set[str]:
    edges: set[str] = set()
    for source, targets in transitions.items():
        if not isinstance(source, str) or not isinstance(targets, list):
            continue
        for target in targets:
            if isinstance(target, str):
                edges.add(f"{source}->{target}")
    return edges


def _projection_contract_valid(value: Any) -> bool:
    projections = _as_object(value)
    if set(projections) != set(EXPECTED_PROJECTIONS):
        return False
    for state, expected in EXPECTED_PROJECTIONS.items():
        item = _as_object(projections.get(state))
        if set(item) != {
            "label_zh",
            "owner_action_zh",
            "owner_attention_required",
        }:
            return False
        actual = (
            item.get("label_zh"),
            item.get("owner_action_zh"),
            item.get("owner_attention_required"),
        )
        if actual != expected:
            return False
    return True


def _job_control_envelope_valid(
    value: Any, transition: Mapping[str, Any]
) -> bool:
    envelope = _as_object(value)
    snapshot_fields = envelope.get("phase2_snapshot_fields")
    request_fields = envelope.get("phase2_request_fields")
    return (
        set(envelope) == JOB_CONTROL_ENVELOPE_KEYS
        and envelope.get("schema_version") == "ids.job_control_envelope.v1"
        and envelope.get("phase2_scope") == "STATIC_EVALUATOR_SUBSET_ONLY"
        and envelope.get("all_fields") == EXPECTED_JOB_CONTROL_ENVELOPE_FIELDS
        and isinstance(snapshot_fields, list)
        and len(snapshot_fields) == len(SNAPSHOT_KEYS)
        and set(snapshot_fields) == SNAPSHOT_KEYS
        and snapshot_fields == transition.get("snapshot_required_fields")
        and isinstance(request_fields, list)
        and len(request_fields) == len(REQUEST_KEYS)
        and set(request_fields) == REQUEST_KEYS
        and request_fields == transition.get("transition_request_required_fields")
        and envelope.get("runtime_persistence_owner")
        == "STAGE-038..STAGE-041"
        and envelope.get("runtime_persistence_performed") is False
        and envelope.get("timestamp_fabrication_allowed") is False
    )


def _zh_text(value: Any) -> bool:
    return (
        isinstance(value, str)
        and 1 <= len(value) <= 512
        and re.search(r"[\u4e00-\u9fff]", value) is not None
    )


def _step_contract_valid(
    value: Any, expected_guards: Mapping[str, tuple[str, bool]]
) -> bool:
    if not isinstance(value, list) or len(value) != len(expected_guards):
        return False
    observed_ids: set[str] = set()
    for item in value:
        if not isinstance(item, dict):
            return False
        step_id = item.get("step_id")
        if not isinstance(step_id, str) or step_id not in expected_guards:
            return False
        guard_name, guard_value = expected_guards[step_id]
        if (
            set(item) != {"step_id", "required", guard_name, "owner_message_zh"}
            or item.get("required") is not True
            or item.get(guard_name) is not guard_value
            or not _zh_text(item.get("owner_message_zh"))
        ):
            return False
        observed_ids.add(step_id)
    return observed_ids == set(expected_guards)


def _known_limits_valid(value: Any) -> bool:
    if not isinstance(value, list) or len(value) != len(EXPECTED_KNOWN_LIMIT_IDS):
        return False
    observed_ids: set[str] = set()
    for item in value:
        if (
            not isinstance(item, dict)
            or set(item) != {"limit_id", "acknowledged", "owner_message_zh"}
            or item.get("acknowledged") is not True
            or not _zh_text(item.get("owner_message_zh"))
        ):
            return False
        limit_id = item.get("limit_id")
        if not isinstance(limit_id, str):
            return False
        observed_ids.add(limit_id)
    return observed_ids == EXPECTED_KNOWN_LIMIT_IDS


def _phase4_shape_exact(value: Any) -> bool:
    contract = _as_object(value)
    return (
        set(contract) == PHASE4_CONTRACT_KEYS
        and set(_as_object(contract.get("state_graph")))
        == PHASE4_STATE_GRAPH_KEYS
        and set(_as_object(contract.get("retry_evidence_contract")))
        == PHASE4_RETRY_KEYS
        and set(_as_object(contract.get("backpressure_evidence_contract")))
        == PHASE4_BACKPRESSURE_KEYS
        and set(_as_object(contract.get("cleanup_evidence_contract")))
        == PHASE4_CLEANUP_KEYS
        and set(_as_object(contract.get("automatic_manual_boundary")))
        == PHASE4_AUTOMATIC_MANUAL_KEYS
        and _step_contract_valid(
            contract.get("safe_shutdown_steps"), EXPECTED_SAFE_SHUTDOWN_GUARDS
        )
        and _step_contract_valid(
            contract.get("recovery_steps"), EXPECTED_RECOVERY_GUARDS
        )
        and _step_contract_valid(
            contract.get("rollback_steps"), EXPECTED_ROLLBACK_GUARDS
        )
        and _known_limits_valid(contract.get("known_limits"))
        and set(_as_object(contract.get("evidence_refs")))
        == set(EXPECTED_PHASE4_EVIDENCE_REFS)
        and set(_as_object(contract.get("evidence_sha256")))
        == set(EXPECTED_PHASE4_EVIDENCE_SHA256)
    )


def _contract_shape_exact(index: Mapping[str, Any]) -> bool:
    transition = _as_object(index.get("transition_contract"))
    return (
        set(index) == TOP_LEVEL_KEYS
        and index.get("source_refs") == EXPECTED_SOURCE_REFS
        and set(_as_object(index.get("dependency_contract"))) == DEPENDENCY_KEYS
        and set(_as_object(index.get("state_model"))) == STATE_MODEL_KEYS
        and _job_control_envelope_valid(
            index.get("job_control_envelope_contract"), transition
        )
        and set(transition) == TRANSITION_KEYS
        and set(transition.get("snapshot_required_fields", [])) == SNAPSHOT_KEYS
        and len(transition.get("snapshot_required_fields", []))
        == len(SNAPSHOT_KEYS)
        and set(transition.get("transition_request_required_fields", []))
        == REQUEST_KEYS
        and len(transition.get("transition_request_required_fields", []))
        == len(REQUEST_KEYS)
        and set(_as_object(index.get("deactivation_contract")))
        == DEACTIVATION_KEYS
        and set(_as_object(index.get("retry_contract"))) == RETRY_KEYS
        and set(_as_object(index.get("reference_policy"))) == REFERENCE_KEYS
        and set(_as_object(index.get("cleanup_boundary"))) == CLEANUP_KEYS
        and set(_as_object(index.get("runtime_policy"))) == RUNTIME_KEYS
        and set(_as_object(index.get("delivery_policy"))) == DELIVERY_KEYS
        and _phase4_shape_exact(index.get("phase4_delivery_contract"))
        and set(_as_object(index.get("truth_contract")))
        == set(EXPECTED_TRUTH_CONTRACT)
    )


def _phase4_evidence_integrity(
    contract: Mapping[str, Any],
) -> tuple[dict[str, bool], dict[str, Optional[str]]]:
    refs = _as_object(contract.get("evidence_refs"))
    configured_hashes = _as_object(contract.get("evidence_sha256"))
    checks: dict[str, bool] = {}
    observed: dict[str, Optional[str]] = {}
    for name, expected_ref in EXPECTED_PHASE4_EVIDENCE_REFS.items():
        configured_ref = refs.get(name)
        path: Optional[Path] = None
        if configured_ref == expected_ref:
            candidate = (INDEX_PATH.parent / expected_ref).resolve()
            if candidate != PROJECT_ROOT and PROJECT_ROOT in candidate.parents:
                path = candidate
        observed_hash: Optional[str] = None
        if path is not None and path.is_file():
            try:
                observed_hash = _sha256_file(path)
            except OSError:
                observed_hash = None
        observed[name] = observed_hash
        expected_hash = EXPECTED_PHASE4_EVIDENCE_SHA256[name]
        checks[name] = (
            configured_hashes.get(name) == expected_hash
            and observed_hash == expected_hash
        )
    checks["exact_ref_key_set"] = set(refs) == set(EXPECTED_PHASE4_EVIDENCE_REFS)
    checks["exact_hash_key_set"] = set(configured_hashes) == set(
        EXPECTED_PHASE4_EVIDENCE_SHA256
    )
    return checks, observed


def _git_relative(path: Path) -> Optional[str]:
    try:
        return path.resolve().relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return None


def _git_path_check(path: Path, arguments: list[str]) -> bool:
    relative = _git_relative(path)
    if relative is None:
        return False
    try:
        completed = subprocess.run(
            ["git", "-C", str(PROJECT_ROOT), *arguments, "--", relative],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return completed.returncode == 0


def _git_tracked(path: Path) -> bool:
    return _git_path_check(path, ["ls-files", "--error-unmatch"])


def _git_index_matches(path: Path) -> bool:
    return _git_tracked(path) and _git_path_check(path, ["diff", "--quiet"])


def _git_head_matches(path: Path) -> bool:
    return _git_tracked(path) and _git_path_check(
        path, ["diff", "--cached", "--quiet", "HEAD"]
    )


def _source_binding(
    paths: Mapping[str, Optional[Path]],
) -> tuple[
    dict[str, bool],
    dict[str, bool],
    dict[str, bool],
    dict[str, Optional[str]],
]:
    tracked: dict[str, bool] = {}
    index_matches: dict[str, bool] = {}
    head_matches: dict[str, bool] = {}
    observed: dict[str, Optional[str]] = {}
    for name, path in paths.items():
        is_file = path is not None and path.is_file()
        tracked[name] = bool(is_file and path is not None and _git_tracked(path))
        index_matches[name] = bool(
            tracked[name] and path is not None and _git_index_matches(path)
        )
        head_matches[name] = bool(
            tracked[name] and path is not None and _git_head_matches(path)
        )
        observed_hash: Optional[str] = None
        if is_file and path is not None:
            try:
                observed_hash = _sha256_file(path)
            except OSError:
                observed_hash = None
        observed[name] = observed_hash
    return tracked, index_matches, head_matches, observed


def _delivery_source_binding(
    contract: Mapping[str, Any],
) -> tuple[
    dict[str, bool],
    dict[str, bool],
    dict[str, bool],
    dict[str, Optional[str]],
]:
    refs = _as_object(contract.get("evidence_refs"))
    paths: dict[str, Optional[Path]] = {
        "index": INDEX_PATH.resolve(),
        "checker": Path(__file__).resolve(),
    }
    for name, expected_ref in EXPECTED_PHASE4_EVIDENCE_REFS.items():
        path: Optional[Path] = None
        if refs.get(name) == expected_ref:
            candidate = (INDEX_PATH.parent / expected_ref).resolve()
            if candidate != PROJECT_ROOT and PROJECT_ROOT in candidate.parents:
                path = candidate
        paths[name] = path

    return _source_binding(paths)


def _review_source_binding() -> tuple[
    dict[str, bool],
    dict[str, bool],
    dict[str, bool],
    dict[str, Optional[str]],
]:
    return _source_binding(
        {
            "review_artifact": REVIEW_ARTIFACT_PATH,
            "batch_lock": BATCH_LOCK_PATH,
            "roadmap": ROADMAP_PATH,
            "events": EVENTS_PATH,
            "governance_validator": GOVERNANCE_VALIDATOR_PATH,
        }
    )


def _canonical_review_governance_report() -> dict[str, Any]:
    module_name = "_ids_stage037_review_governance_validator"
    try:
        spec = importlib.util.spec_from_file_location(
            module_name, GOVERNANCE_VALIDATOR_PATH
        )
        if spec is None or spec.loader is None:
            raise RuntimeError("unable to load Stage005 governance validator")
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        report = module.build_stage037_review_governance_report(PROJECT_ROOT)
    except Exception as exc:
        return {
            "valid": False,
            "load_error": f"{type(exc).__name__}: {exc}",
        }
    return copy.deepcopy(report) if isinstance(report, dict) else {"valid": False}


def _review_artifact_semantics_exact() -> bool:
    try:
        text = REVIEW_ARTIFACT_PATH.read_text(encoding="utf-8")
    except OSError:
        return False
    required_terms = {
        "# STAGE-037 Whole-Stage Review - 任务状态模型",
        "- Review Task ID: `IDS-V0_1-STAGE037-REVIEW`",
        "- Acceptance ID: `ACC-STAGE-037`",
        "- Current state: `completed_reviewed_local`",
        "- Current upload switch: `push_allowed=false`",
        "- Next allowed gate: `IDS-STAGE038-P1-GATE`",
        "NO_GITHUB_UPLOAD",
        "NO_APP_REINSTALL",
        "NO_STAGE038_THIS_RUN",
        "/Users/linzezhang/Downloads/IDS_MetaData",
        "不得读取、列出、hash、打开、复制、移动、删除、修改、dump 或扫描该目录内容。",
        "## Real Data Only Policy",
        "fake business data",
    }
    contradictory_true = re.search(
        r"\b(?:push_allowed|github_upload_allowed|app_reinstall_allowed|"
        r"raw_metadata_content_accessed|fake_ids_business_data_used)\s*=\s*true\b",
        text,
        re.IGNORECASE,
    )
    return all(term in text for term in required_terms) and contradictory_true is None


def _review_governance_checks(report: Mapping[str, Any]) -> dict[str, bool]:
    phase_checks = _as_object(report.get("phase_state_checks"))
    data_checks = _as_object(report.get("data_boundary_checks"))
    required_phase_checks = {
        "current_state_yaml_documents_parsed",
        "current_state_current_stage_node_resolved",
        "current_state_batch_top_status_matches_stage",
        "current_state_batch_stage_gate_matches_roadmap",
        "current_state_batch_stage_task_matches_roadmap",
        "current_state_decision_task_matches_roadmap",
        "current_state_decision_next_allowed_task_matches_gate",
        "current_state_decision_upload_locked",
        "current_state_push_locked_structurally",
        "current_state_roadmap_current_task_completed",
        "current_state_roadmap_current_task_evidence_recorded",
        "current_state_roadmap_current_task_results_recorded",
        "current_task_allowed",
        "next_gate_allowed",
    }
    required_data_checks = {
        "boundary_ref_recorded",
        "raw_content_not_committed",
        "raw_root_recorded",
        "read_only_policy_recorded",
        "real_data_only_policy_recorded",
    }
    return {
        "validator_identity_exact": (
            report.get("stage") == "STAGE-005"
            and report.get("acceptance_id") == "ACC-STAGE-005"
        ),
        "validator_valid": report.get("valid") is True,
        "review_artifact_semantics_exact": _review_artifact_semantics_exact(),
        "review_event_semantics_exact": (
            report.get("event_json_errors") == []
            and report.get("event_semantic_errors") == []
            and report.get("missing_event_ids") == []
        ),
        "review_state_structured_and_exact": (
            required_phase_checks.issubset(phase_checks)
            and all(phase_checks.get(name) is True for name in required_phase_checks)
        ),
        "raw_and_real_data_boundaries_exact": (
            set(data_checks) == required_data_checks
            and all(data_checks.get(name) is True for name in required_data_checks)
        ),
        "required_governance_files_present": report.get("missing_required_files")
        == [],
        "no_tracked_forbidden_runtime_paths": report.get(
            "tracked_forbidden_runtime_files"
        )
        == [],
    }


def _phase4_contract_results(index: Mapping[str, Any]) -> dict[str, bool]:
    contract = _as_object(index.get("phase4_delivery_contract"))
    state_graph = _as_object(contract.get("state_graph"))
    retry_evidence = _as_object(contract.get("retry_evidence_contract"))
    backpressure = _as_object(contract.get("backpressure_evidence_contract"))
    cleanup_evidence = _as_object(contract.get("cleanup_evidence_contract"))
    automatic_manual = _as_object(contract.get("automatic_manual_boundary"))
    state_model = _as_object(index.get("state_model"))
    retry = _as_object(index.get("retry_contract"))
    cleanup = _as_object(index.get("cleanup_boundary"))
    evidence_checks, _ = _phase4_evidence_integrity(contract)
    transition_count = sum(
        len(targets)
        for targets in ALLOWED_TRANSITIONS.values()
        if isinstance(targets, list)
    )
    return {
        "contract_shape_exact": _phase4_shape_exact(contract),
        "identity_exact": (
            contract.get("schema_version") == PHASE4_CONTRACT_SCHEMA_VERSION
        ),
        "state_graph_exact": (
            state_graph.get("mode") == "static_tracked_job_state_graph"
            and state_graph.get("state_model_version") == "ids.job_state.v1"
            and state_graph.get("job_type_count") == len(JOB_TYPES)
            and state_graph.get("job_state_count") == len(JOB_STATES)
            and state_graph.get("allowed_transition_count") == transition_count
            and state_graph.get("terminal_state_count") == len(TERMINAL_STATES)
            and state_graph.get("active_execution_state_count")
            == len(ACTIVE_STATES)
            and state_graph.get("source_ref")
            == "../STAGE037_PHASE1_SCOPE_BOUNDARY.md"
            and state_graph.get("runtime_transition_performed") is False
            and state_model.get("state_model_version") == "ids.job_state.v1"
            and state_model.get("job_types") == JOB_TYPES
            and state_model.get("job_states") == JOB_STATES
            and state_model.get("allowed_transitions") == ALLOWED_TRANSITIONS
        ),
        "retry_evidence_exact": (
            retry_evidence.get("mode") == "static_retry_contract_evidence_only"
            and retry_evidence.get("runtime_owner") == "STAGE-039"
            and retry_evidence.get("total_attempt_limit_formula")
            == "1 + max_retries"
            and retry_evidence.get("reservation_increments_retry_count") is False
            and retry_evidence.get("admission_increments_retry_count") is True
            and retry_evidence.get("resource_pause_preserves_reservation") is True
            and retry_evidence.get("exhausted_only_next_state")
            == "DEAD_LETTERED"
            and retry_evidence.get("numeric_policy")
            == "POLICY_VALUE_DEFERRED_TO_STAGE039_040_041"
            and retry_evidence.get("retry_scheduler_performed") is False
            and retry_evidence.get("dead_letter_runtime_performed") is False
            and retry.get("total_attempt_limit_formula") == "1 + max_retries"
            and retry.get("eligible_entry_increments_retry_count") is False
            and retry.get("retry_admission_increments_retry_count") is True
            and retry.get("retry_pause_preserves_retry_pending") is True
            and retry.get("exhausted_only_next_state") == "DEAD_LETTERED"
        ),
        "backpressure_evidence_exact": (
            backpressure.get("mode")
            == "static_backpressure_boundary_evidence_only"
            and backpressure.get("runtime_owner") == "STAGE-040"
            and backpressure.get("pause_reason_is_state") is False
            and backpressure.get("resource_gate_required") is True
            and backpressure.get("retry_budget_consumed_while_blocked") is False
            and backpressure.get("numeric_policy")
            == "POLICY_VALUE_DEFERRED_TO_STAGE039_040_041"
            and backpressure.get("backpressure_runtime_performed") is False
            and state_model.get("pause_reason_is_state") is False
        ),
        "cleanup_evidence_exact": (
            cleanup_evidence.get("mode")
            == "static_cleanup_boundary_evidence_only"
            and cleanup_evidence.get("runtime_owner") == "STAGE-044"
            and cleanup_evidence.get("state_transition_authorizes_deletion")
            is False
            and cleanup_evidence.get("approved_root_identity_required") is True
            and cleanup_evidence.get("lstat_identity_required") is True
            and cleanup_evidence.get("symlink_allowed") is False
            and cleanup_evidence.get("exclusive_namespace_lock_required") is True
            and cleanup_evidence.get("writer_quiescence_required") is True
            and cleanup_evidence.get("openat_no_follow_required") is True
            and cleanup_evidence.get("unlinkat_required") is True
            and cleanup_evidence.get(
                "source_and_durable_evidence_targets_allowed"
            )
            is False
            and cleanup_evidence.get("cleanup_runtime_performed") is False
            and cleanup.get("cleanup_owner") == "STAGE-044"
            and cleanup.get("state_transition_authorizes_deletion") is False
            and cleanup.get("cleanup_runtime_allowed") is False
        ),
        "automatic_manual_boundary_exact": (
            automatic_manual.get("mode")
            == "static_automatic_manual_boundary_only"
            and automatic_manual.get("runtime_owner") == "STAGE-042"
            and automatic_manual.get("automatic_run_allowed") is False
            and automatic_manual.get("automatic_resume_allowed") is False
            and automatic_manual.get("automatic_shutdown_allowed") is False
            and automatic_manual.get("owner_revalidation_required_for_resume")
            is True
            and automatic_manual.get("safe_deactivation_required_for_cancel")
            is True
            and automatic_manual.get("terminal_history_rewrite_allowed") is False
            and automatic_manual.get("automatic_lifecycle_runtime_performed")
            is False
        ),
        "safe_shutdown_steps_exact": _step_contract_valid(
            contract.get("safe_shutdown_steps"), EXPECTED_SAFE_SHUTDOWN_GUARDS
        ),
        "recovery_steps_exact": _step_contract_valid(
            contract.get("recovery_steps"), EXPECTED_RECOVERY_GUARDS
        ),
        "rollback_steps_exact": _step_contract_valid(
            contract.get("rollback_steps"), EXPECTED_ROLLBACK_GUARDS
        ),
        "known_limits_exact": _known_limits_valid(contract.get("known_limits")),
        "evidence_integrity_exact": all(evidence_checks.values()),
        "review_and_delivery_locked": (
            contract.get("stage_review_status") == "pending_next_run"
            and contract.get("next_gate") == PHASE4_NEXT_GATE
            and contract.get("github_upload_allowed") is False
            and contract.get("app_reinstall_allowed") is False
        ),
        "chinese_owner_feedback_present": _zh_text(
            contract.get("chinese_owner_feedback")
        ),
    }


def _dependency_semantics_valid(
    index: Mapping[str, Any], paths: Mapping[str, Path]
) -> bool:
    dependency = _as_object(index.get("dependency_contract"))
    if dependency.get("required_control_plane_table") != "ids_jobs":
        return False
    if dependency.get("required_job_columns") != [
        "job_id",
        "job_type",
        "job_state",
        "parent_job_id",
        "retry_count",
        "max_retries",
        "stop_reason",
    ]:
        return False
    if dependency.get("state_registry_table") != "ids_state_value_registry":
        return False
    if dependency.get("state_registry_write_allowed") is not False:
        return False
    if dependency.get("postgres_connection_allowed") is not False:
        return False
    try:
        schema = paths["control_plane_schema_ref"].read_text(encoding="utf-8")
        quality = _load_json(paths["database_quality_index_ref"])
        registry_sql = paths["state_registry_structure_ref"].read_text(encoding="utf-8")
        phase1 = paths["phase1_scope_ref"].read_text(encoding="utf-8")
    except (KeyError, OSError, ValueError, json.JSONDecodeError):
        return False
    required_schema_terms = [
        "CREATE TABLE IF NOT EXISTS ids_jobs",
        "job_id",
        "job_type",
        "job_state",
        "retry_count",
        "max_retries",
    ]
    registry = _as_object(quality.get("versioned_state_registry"))
    return (
        all(term in schema for term in required_schema_terms)
        and "CREATE TABLE IF NOT EXISTS public.ids_state_value_registry"
        in registry_sql
        and registry.get("populated") is False
        and registry.get("state_values_owner") == "STAGE-037"
        and "state_namespace=job_state" in phase1
        and "state_model_version=ids.job_state.v1" in phase1
        and "RUNNING never transitions directly to CANCELLED" in phase1
    )


def build_stage037_job_state_report(
    *, index: Optional[dict[str, Any]] = None
) -> dict[str, Any]:
    load_error: Optional[str] = None
    if index is None:
        try:
            index = load_contract()
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            index = {}
            load_error = f"{type(exc).__name__}: {exc}"
    elif not isinstance(index, dict):
        index = {}
        load_error = "index must be a JSON object"

    state_model = _as_object(index.get("state_model"))
    transition = _as_object(index.get("transition_contract"))
    retry = _as_object(index.get("retry_contract"))
    deactivation = _as_object(index.get("deactivation_contract"))
    reference = _as_object(index.get("reference_policy"))
    runtime = _as_object(index.get("runtime_policy"))
    delivery = _as_object(index.get("delivery_policy"))
    truth = _as_object(index.get("truth_contract"))
    cleanup = _as_object(index.get("cleanup_boundary"))
    envelope = _as_object(index.get("job_control_envelope_contract"))
    paths = _resolve_source_paths(index)
    source_checks, observed_hashes = _source_integrity(index)

    edge_guards = _as_object(transition.get("edge_guard_requirements"))
    edge_refs = _as_object(transition.get("edge_reference_requirements"))
    expected_edges = _all_edges(ALLOWED_TRANSITIONS)
    allowed_reference_requirement_names = {
        "input_refs",
        "audit_ref",
        "candidate_claim",
        "pause_reason_code",
        "resource_gate_refs",
        "fencing_token",
        "output_refs",
        "error_ref",
        "checkpoint_or_quarantine_ref",
        "stop_reason",
        "next_eligible_evidence_ref",
    }

    checks = {
        "index_loaded": load_error is None,
        "contract_shape_exact": _contract_shape_exact(index),
        "identity_exact": (
            index.get("schema_version") == INDEX_SCHEMA_VERSION
            and index.get("stage") == "STAGE-037"
            and index.get("phase") == "Phase 2"
            and index.get("task_id") == TASK_ID
            and index.get("acceptance_id") == ACCEPTANCE_ID
            and index.get("job_state_model_contract_id") == CONTRACT_ID
            and index.get("contract_state") == VALID_STATE
            and index.get("execution_mode") == EXECUTION_MODE
            and index.get("execution_ready") is False
            and index.get("next_gate") == NEXT_GATE
        ),
        "state_membership_exact": (
            state_model.get("state_namespace") == "job_state"
            and state_model.get("state_model_version") == "ids.job_state.v1"
            and state_model.get("introduced_version") == "v0.1"
            and state_model.get("job_types") == JOB_TYPES
            and state_model.get("job_states") == JOB_STATES
            and state_model.get("terminal_states") == TERMINAL_STATES
            and state_model.get("active_execution_states") == ACTIVE_STATES
        ),
        "transition_matrix_exact": (
            state_model.get("allowed_transitions") == ALLOWED_TRANSITIONS
            and state_model.get("pause_reason_is_state") is False
            and state_model.get("terminal_state_mutation_allowed") is False
            and state_model.get("direct_running_cancel_allowed") is False
        ),
        "compare_and_set_and_idempotency_exact": (
            transition.get("compare_and_set_fields")
            == ["job_id", "expected_state", "expected_state_version"]
            and transition.get("state_version_increment") == 1
            and transition.get("transition_request_id_unique") is True
            and transition.get("idempotent_replay_returns_original_result") is True
            and transition.get("request_id_payload_conflict_fails_closed") is True
            and transition.get("append_only_audit_required") is True
            and transition.get("runtime_transition_performed") is False
        ),
        "job_control_envelope_exact": _job_control_envelope_valid(
            envelope, transition
        ),
        "guard_fact_vocabulary_exact": (
            transition.get("guard_facts_allowed") == EXPECTED_GUARD_FACTS
        ),
        "edge_guards_exact": edge_guards == EXPECTED_EDGE_GUARDS,
        "edge_guards_cover_every_transition": set(edge_guards) == expected_edges,
        "edge_reference_contract_exact": (
            edge_refs == EXPECTED_EDGE_REFERENCES
            and set(edge_refs) == expected_edges
            and all(
                isinstance(values, list)
                and values
                and all(
                    isinstance(item, str)
                    and item in allowed_reference_requirement_names
                    for item in values
                )
                for values in edge_refs.values()
            )
        ),
        "deactivation_exact": (
            deactivation.get("active_states") == ACTIVE_STATES
            and deactivation.get("non_active_destinations")
            == ["PAUSED", "RETRY_WAIT", "SUCCEEDED", "FAILED", "CANCELLED"]
            and deactivation.get("atomic_state_and_audit") is True
            and deactivation.get("lease_revoked") is True
            and deactivation.get("lock_revoked") is True
            and deactivation.get("fencing_token_advanced") is True
            and deactivation.get("stale_worker_commit_allowed") is False
        ),
        "retry_budget_exact": (
            retry.get("max_retries_definition")
            == "number_of_retry_attempts_after_initial_attempt"
            and retry.get("initial_retry_count") == 0
            and retry.get("total_attempt_limit_formula") == "1 + max_retries"
            and retry.get("max_retries_immutable") is True
            and retry.get("eligible_entry_sets_retry_pending") is True
            and retry.get("eligible_entry_increments_retry_count") is False
            and retry.get("retry_admission_increments_retry_count") is True
            and retry.get("retry_admission_clears_retry_pending") is True
            and retry.get("retry_pause_preserves_retry_pending") is True
            and retry.get("paused_retry_resume_consumes_pending_retry") is True
            and retry.get("ordinary_pause_consumes_retry") is False
            and retry.get("exhausted_entry_retry_pending") is False
            and retry.get("exhausted_disposition") == "exhausted"
            and retry.get("exhausted_only_next_state") == "DEAD_LETTERED"
            and retry.get("resource_gate_can_pause_exhausted_retry") is False
            and retry.get("running_to_dead_letter_allowed") is False
            and retry.get("retry_delay_policy")
            == "POLICY_VALUE_DEFERRED_TO_STAGE039_040_041"
            and retry.get("next_eligible_at_required_for_eligible_retry") is True
            and retry.get("next_eligible_evidence_required_for_admission") is True
            and retry.get("paused_retry_resume_requires_next_eligible_at") is True
            and retry.get("paused_retry_resume_requires_next_eligible_evidence")
            is True
            and retry.get("paused_retry_resume_requires_next_eligible_reached")
            is True
            and retry.get("retry_scheduler_allowed") is False
        ),
        "reference_policy_fail_closed": (
            reference.get("maximum_text_length") == 512
            and reference.get("maximum_refs_per_field") == 64
            and reference.get("absolute_path_allowed") is False
            and reference.get("parent_path_segment_allowed") is False
            and reference.get("file_uri_allowed") is False
            and reference.get("backslash_separator_allowed") is False
            and reference.get("percent_encoded_path_tokens_allowed") is False
            and reference.get("unicode_path_separator_normalization_required")
            is True
            and reference.get("case_insensitive_path_guard_required") is True
            and reference.get("raw_metadata_root")
            == "/Users/linzezhang/Downloads/IDS_MetaData"
            and reference.get("raw_metadata_content_access_allowed") is False
            and reference.get("forbidden_key_tokens")
            == EXPECTED_FORBIDDEN_KEY_TOKENS
            and reference.get("raw_body_fields_allowed") is False
            and reference.get("plaintext_secrets_allowed") is False
            and set(reference.get("bounded_ref_fields", []))
            == (REF_SCALAR_FIELDS | REF_LIST_FIELDS)
            and len(reference.get("bounded_ref_fields", []))
            == len(REF_SCALAR_FIELDS | REF_LIST_FIELDS)
        ),
        "cleanup_runtime_deferred_and_protected": (
            cleanup.get("cleanup_runtime_allowed") is False
            and cleanup.get("state_transition_authorizes_deletion") is False
            and cleanup.get("cleanup_owner") == "STAGE-044"
            and cleanup.get("approved_root_identity_required") is True
            and cleanup.get("root_relative_path_required") is True
            and cleanup.get("lstat_identity_required") is True
            and cleanup.get("symlink_allowed") is False
            and cleanup.get("exclusive_namespace_lock_required") is True
            and cleanup.get("writer_quiescence_required") is True
            and cleanup.get("openat_no_follow_required") is True
            and cleanup.get("unlinkat_required") is True
            and cleanup.get("source_and_durable_evidence_targets_allowed") is False
        ),
        "human_status_projection_exact": _projection_contract_valid(
            index.get("human_status_projection")
        ),
        "downstream_ownership_exact": index.get("downstream_ownership")
        == EXPECTED_OWNERSHIP,
        "runtime_actions_all_disabled": (
            bool(runtime)
            and set(runtime) == RUNTIME_KEYS
            and all(value is False for value in runtime.values())
        ),
        "delivery_locked": (
            delivery.get("github_upload_allowed") is False
            and delivery.get("pull_request_allowed") is False
            and delivery.get("merge_allowed") is False
            and delivery.get("app_reinstall_allowed") is False
            and delivery.get("stage_review_allowed_in_phase2") is False
            and delivery.get("batch_review_allowed") is False
            and delivery.get("next_phase_allowed") == "Phase 3"
            and delivery.get("next_gate") == NEXT_GATE
        ),
        "truthful_no_execution_result": truth == EXPECTED_TRUTH_CONTRACT,
        "source_hashes_exact": all(source_checks.values()),
        "dependency_semantics_valid": _dependency_semantics_valid(index, paths),
    }
    contract_valid = all(checks.values())
    return {
        "schema_version": REPORT_SCHEMA_VERSION,
        "stage": "STAGE-037",
        "phase": "Phase 2",
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "job_state_model_contract_id": CONTRACT_ID,
        "contract_valid": contract_valid,
        "execution_ready": False,
        "execution_state": VALID_STATE if contract_valid else INVALID_STATE,
        "execution_mode": EXECUTION_MODE,
        "runtime_actions": dict(runtime),
        "runtime_transition_performed": False,
        "real_job_created": False,
        "raw_metadata_content_accessed": False,
        "fake_ids_business_data_used": False,
        "github_upload_allowed": False,
        "app_reinstall_allowed": False,
        "next_gate": NEXT_GATE,
        "checks": checks,
        "source_integrity": source_checks,
        "observed_source_sha256": observed_hashes,
        "load_error": load_error,
    }


def _canonical_fingerprint(value: Mapping[str, Any]) -> Optional[str]:
    try:
        encoded = json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError):
        return None
    return hashlib.sha256(encoded).hexdigest()


def _decision_base(
    snapshot: Mapping[str, Any],
    request: Mapping[str, Any],
    *,
    accepted: bool,
    result_code: str,
    fingerprint: Optional[str],
) -> dict[str, Any]:
    return {
        "schema_version": DECISION_SCHEMA_VERSION,
        "job_state_model_contract_id": CONTRACT_ID,
        "fact_level": EVALUATION_MODE,
        "accepted": accepted,
        "result_code": result_code,
        "transition_request_id": request.get("transition_request_id"),
        "request_fingerprint_sha256": fingerprint,
        "previous_state": snapshot.get("job_state"),
        "requested_state": request.get("target_state"),
        "idempotent_replay": False,
        "runtime_transition_performed": False,
        "database_write_performed": False,
        "queue_or_worker_action_performed": False,
        "next_snapshot": None,
        "transition_candidate": None,
        "human_status_projection": None,
    }


def _reject(
    snapshot: Mapping[str, Any],
    request: Mapping[str, Any],
    code: str,
    fingerprint: Optional[str] = None,
) -> dict[str, Any]:
    return _decision_base(
        snapshot,
        request,
        accepted=False,
        result_code=code,
        fingerprint=fingerprint,
    )


def _valid_nonnegative_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _forbidden_key_present(
    value: Any, forbidden_tokens: set[str]
) -> bool:
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = str(key).lower()
            if any(token in normalized for token in forbidden_tokens):
                return True
            if _forbidden_key_present(child, forbidden_tokens):
                return True
    elif isinstance(value, list):
        return any(_forbidden_key_present(item, forbidden_tokens) for item in value)
    return False


def _bounded_text(value: Any, maximum: int) -> bool:
    return (
        isinstance(value, str)
        and 0 < len(value) <= maximum
        and "\x00" not in value
        and "\n" not in value
        and "\r" not in value
    )


def _ref_valid(value: Any, reference: Mapping[str, Any]) -> bool:
    maximum = reference.get("maximum_text_length")
    if not isinstance(maximum, int) or not _bounded_text(value, maximum):
        return False
    assert isinstance(value, str)
    normalized = unicodedata.normalize("NFKC", value)
    if "%" in normalized or "\\" in normalized:
        return False
    for separator in ("\u2215", "\u2044", "\uff0f", "\uff3c", "\u29f8", "\u2216"):
        normalized = normalized.replace(separator, "/")
    folded = normalized.casefold()
    raw_root = unicodedata.normalize(
        "NFKC", str(reference.get("raw_metadata_root", ""))
    ).replace("\\", "/").casefold()
    if raw_root and raw_root in folded:
        return False
    path_part = normalized.split("#", 1)[0]
    path_folded = path_part.casefold()
    if (
        path_part.startswith(("/", "~"))
        or path_folded.startswith("file:")
        or re.match(r"^[a-z]:/", path_folded)
    ):
        return False
    parts = path_part.split("/")
    if any(part in {".", ".."} for part in parts):
        return False
    return True


def _refs_valid(value: Any, reference: Mapping[str, Any]) -> bool:
    maximum = reference.get("maximum_refs_per_field")
    return (
        isinstance(value, list)
        and isinstance(maximum, int)
        and len(value) <= maximum
        and all(_ref_valid(item, reference) for item in value)
    )


def _metadata_boundaries_valid(
    snapshot: Mapping[str, Any],
    request: Mapping[str, Any],
    reference: Mapping[str, Any],
) -> tuple[bool, Optional[str]]:
    maximum = reference.get("maximum_text_length")
    if not isinstance(maximum, int):
        return False, "INVALID_CONTRACT"
    forbidden_tokens = {
        item.lower()
        for item in reference.get("forbidden_key_tokens", [])
        if isinstance(item, str)
    }
    if _forbidden_key_present(snapshot, forbidden_tokens) or _forbidden_key_present(
        request, forbidden_tokens
    ):
        return False, "FORBIDDEN_METADATA_FIELD"

    for owner in (snapshot, request):
        for field in ("reason_code", "pause_reason_code", "stop_reason"):
            value = owner.get(field)
            if value is not None and not _bounded_text(value, maximum):
                return False, "UNBOUNDED_METADATA"
        for field in REF_SCALAR_FIELDS:
            if field not in owner:
                continue
            value = owner.get(field)
            if value is not None and not _ref_valid(value, reference):
                return False, "FORBIDDEN_REFERENCE"
        for field in REF_LIST_FIELDS:
            if field in owner and not _refs_valid(owner.get(field), reference):
                return False, "FORBIDDEN_REFERENCE"

    claim = request.get("candidate_claim")
    if claim is not None:
        if not isinstance(claim, dict) or set(claim) != CLAIM_KEYS:
            return False, "INVALID_CLAIM_SHAPE"
        for field in CLAIM_KEYS - {"fencing_token"}:
            if not _ref_valid(claim.get(field), reference):
                return False, "FORBIDDEN_REFERENCE"
        if not _valid_nonnegative_int(claim.get("fencing_token")):
            return False, "INVALID_CLAIM_SHAPE"
    return True, None


def _snapshot_shape_valid(snapshot: Mapping[str, Any]) -> bool:
    if set(snapshot) != SNAPSHOT_KEYS:
        return False
    if snapshot.get("evaluation_mode") != EVALUATION_MODE:
        return False
    if snapshot.get("job_type") not in JOB_TYPES:
        return False
    if snapshot.get("job_state") not in JOB_STATES:
        return False
    for field in ("state_version", "retry_count", "max_retries", "fencing_token"):
        if not _valid_nonnegative_int(snapshot.get(field)):
            return False
    if snapshot.get("retry_count") > snapshot.get("max_retries"):
        return False
    for field in ("retry_pending", "lease_active", "lock_active"):
        if not isinstance(snapshot.get(field), bool):
            return False
    if snapshot.get("retry_disposition") not in {"none", "eligible", "exhausted"}:
        return False
    state = snapshot.get("job_state")
    active = state in ACTIVE_STATES
    if active:
        if snapshot.get("lease_active") is not True or snapshot.get("lock_active") is not True:
            return False
        if snapshot.get("fencing_token", 0) <= 0:
            return False
        if any(
            snapshot.get(field) is None
            for field in (
                "attempt_id",
                "lease_owner_ref",
                "lease_expires_at",
                "lock_key",
            )
        ):
            return False
    else:
        if snapshot.get("lease_active") is not False or snapshot.get("lock_active") is not False:
            return False
        if any(
            snapshot.get(field) is not None
            for field in ("lease_owner_ref", "lease_expires_at", "lock_key")
        ):
            return False
    disposition = snapshot.get("retry_disposition")
    pending = snapshot.get("retry_pending")
    if active and (pending is not False or disposition != "none"):
        return False
    if pending and (disposition != "eligible" or state not in {"RETRY_WAIT", "PAUSED"}):
        return False
    if pending and not snapshot.get("next_eligible_at"):
        return False
    if not pending and snapshot.get("next_eligible_at") is not None:
        return False
    if disposition == "exhausted" and not (
        state == "RETRY_WAIT"
        and pending is False
        and snapshot.get("retry_count") == snapshot.get("max_retries")
    ):
        return False
    if state in {"CREATED", "QUEUED", "CLAIMED", "RUNNING", "PAUSE_REQUESTED"}:
        if not snapshot.get("input_refs"):
            return False
    if state == "SUCCEEDED" and not snapshot.get("output_refs"):
        return False
    if state in {"RETRY_WAIT", "FAILED", "DEAD_LETTERED"}:
        if not snapshot.get("error_ref"):
            return False
    if state == "PAUSED" and not snapshot.get("pause_reason_code"):
        return False
    if state == "CANCELLED":
        if not isinstance(snapshot.get("stop_reason"), str):
            return False
    elif snapshot.get("stop_reason") is not None:
        return False
    return True


def _request_shape_valid(
    request: Mapping[str, Any], allowed_guard_facts: set[str]
) -> bool:
    if set(request) != REQUEST_KEYS:
        return False
    if request.get("expected_state") not in JOB_STATES:
        return False
    if request.get("target_state") not in JOB_STATES:
        return False
    if not _valid_nonnegative_int(request.get("expected_state_version")):
        return False
    fencing = request.get("fencing_token")
    if fencing is not None and not _valid_nonnegative_int(fencing):
        return False
    facts = request.get("guard_facts")
    if not isinstance(facts, dict) or not set(facts).issubset(allowed_guard_facts):
        return False
    return all(isinstance(value, bool) for value in facts.values())


def _prior_result_valid(
    prior: Mapping[str, Any],
    request: Mapping[str, Any],
    fingerprint: str,
    contract: Mapping[str, Any],
    reference: Mapping[str, Any],
) -> bool:
    if set(prior) != DECISION_KEYS:
        return False
    if (
        prior.get("schema_version") != DECISION_SCHEMA_VERSION
        or prior.get("job_state_model_contract_id") != CONTRACT_ID
        or prior.get("fact_level") != EVALUATION_MODE
        or prior.get("transition_request_id")
        != request.get("transition_request_id")
        or prior.get("request_fingerprint_sha256") != fingerprint
        or prior.get("previous_state") != request.get("expected_state")
        or prior.get("requested_state") != request.get("target_state")
        or prior.get("idempotent_replay") is not False
        or prior.get("runtime_transition_performed") is not False
        or prior.get("database_write_performed") is not False
        or prior.get("queue_or_worker_action_performed") is not False
    ):
        return False
    accepted = prior.get("accepted")
    if not isinstance(accepted, bool):
        return False
    if not accepted:
        return (
            isinstance(prior.get("result_code"), str)
            and prior.get("result_code") != "TRANSITION_ACCEPTED"
            and prior.get("next_snapshot") is None
            and prior.get("transition_candidate") is None
        )
    if prior.get("result_code") != "TRANSITION_ACCEPTED":
        return False
    next_snapshot = prior.get("next_snapshot")
    candidate = prior.get("transition_candidate")
    if not isinstance(next_snapshot, dict) or not isinstance(candidate, dict):
        return False
    if not _snapshot_shape_valid(next_snapshot):
        return False
    boundaries_valid, _ = _metadata_boundaries_valid(
        next_snapshot, request, reference
    )
    if not boundaries_valid or set(candidate) != TRANSITION_CANDIDATE_KEYS:
        return False
    expected_version = request.get("expected_state_version")
    if not isinstance(expected_version, int):
        return False
    if (
        next_snapshot.get("job_id") != request.get("job_id")
        or next_snapshot.get("job_state") != request.get("target_state")
        or next_snapshot.get("state_version") != expected_version + 1
        or candidate.get("candidate_only") is not True
        or candidate.get("persisted") is not False
        or candidate.get("append_only_audit_required") is not True
        or candidate.get("transition_request_id")
        != request.get("transition_request_id")
        or candidate.get("job_id") != request.get("job_id")
        or candidate.get("job_type") != next_snapshot.get("job_type")
        or candidate.get("previous_state") != request.get("expected_state")
        or candidate.get("current_state") != request.get("target_state")
        or candidate.get("previous_state_version") != expected_version
        or candidate.get("current_state_version") != expected_version + 1
        or candidate.get("reason_code") != request.get("reason_code")
        or candidate.get("stop_reason") != request.get("stop_reason")
        or candidate.get("next_eligible_at")
        != next_snapshot.get("next_eligible_at")
        or candidate.get("next_eligible_evidence_ref")
        != request.get("next_eligible_evidence_ref")
        or candidate.get("actor_ref") != request.get("actor_ref")
        or candidate.get("audit_ref") != request.get("audit_ref")
        or candidate.get("transition_timestamp") is not None
        or candidate.get("timestamp_persistence_required") is not True
        or prior.get("human_status_projection")
        != _projection(contract, str(request.get("target_state")))
    ):
        return False
    return True


def _reference_requirement_present(
    requirement: str,
    snapshot: Mapping[str, Any],
    request: Mapping[str, Any],
) -> bool:
    if requirement == "input_refs":
        return bool(request.get("input_refs") or snapshot.get("input_refs"))
    if requirement == "output_refs":
        return bool(request.get("output_refs") or snapshot.get("output_refs"))
    if requirement == "resource_gate_refs":
        return bool(request.get("resource_gate_refs"))
    if requirement == "checkpoint_or_quarantine_ref":
        return bool(request.get("checkpoint_ref") or request.get("quarantine_ref"))
    if requirement == "candidate_claim":
        return isinstance(request.get("candidate_claim"), dict)
    if requirement == "fencing_token":
        return _valid_nonnegative_int(request.get("fencing_token"))
    if requirement == "error_ref":
        return bool(request.get("error_ref") or snapshot.get("error_ref"))
    return bool(request.get(requirement))


def _projection(
    contract: Mapping[str, Any], state: str
) -> Optional[dict[str, Any]]:
    value = _as_object(_as_object(contract.get("human_status_projection")).get(state))
    return copy.deepcopy(value) if value else None


def evaluate_transition(
    snapshot: Mapping[str, Any],
    request: Mapping[str, Any],
    *,
    contract: Optional[dict[str, Any]] = None,
    prior_results: Optional[Mapping[str, Mapping[str, Any]]] = None,
) -> dict[str, Any]:
    if not isinstance(snapshot, dict) or not isinstance(request, dict):
        return _reject({}, {}, "INVALID_INPUT_SHAPE")
    if contract is None:
        try:
            contract = load_contract()
        except (OSError, ValueError, json.JSONDecodeError):
            return _reject(snapshot, request, "INVALID_CONTRACT")
    report = build_stage037_job_state_report(index=contract)
    if not report["contract_valid"]:
        return _reject(snapshot, request, "INVALID_CONTRACT")

    transition = _as_object(contract.get("transition_contract"))
    reference = _as_object(contract.get("reference_policy"))
    allowed_guard_facts = {
        item
        for item in transition.get("guard_facts_allowed", [])
        if isinstance(item, str)
    }
    if (
        set(snapshot) == SNAPSHOT_KEYS
        and snapshot.get("retry_pending") is True
        and not snapshot.get("next_eligible_at")
    ):
        return _reject(
            snapshot, request, "MISSING_RETRY_SCHEDULE_EVIDENCE"
        )
    if not _snapshot_shape_valid(snapshot):
        return _reject(snapshot, request, "INVALID_SNAPSHOT_SHAPE")
    if not _request_shape_valid(request, allowed_guard_facts):
        return _reject(snapshot, request, "INVALID_REQUEST_SHAPE")

    boundaries_valid, boundary_error = _metadata_boundaries_valid(
        snapshot, request, reference
    )
    if not boundaries_valid:
        return _reject(snapshot, request, boundary_error or "FORBIDDEN_REFERENCE")
    fingerprint = _canonical_fingerprint(request)
    if fingerprint is None:
        return _reject(snapshot, request, "INVALID_REQUEST_SHAPE")
    if request.get("job_id") != snapshot.get("job_id"):
        return _reject(snapshot, request, "COMPARE_AND_SET_MISMATCH", fingerprint)

    request_id = request["transition_request_id"]
    if prior_results is not None and request_id in prior_results:
        prior = prior_results[request_id]
        if not isinstance(prior, Mapping):
            return _reject(snapshot, request, "TRANSITION_REQUEST_CONFLICT", fingerprint)
        if prior.get("request_fingerprint_sha256") != fingerprint:
            return _reject(snapshot, request, "TRANSITION_REQUEST_CONFLICT", fingerprint)
        if not _prior_result_valid(
            prior, request, fingerprint, contract, reference
        ):
            return _reject(snapshot, request, "INVALID_PRIOR_RESULT", fingerprint)
        replay = copy.deepcopy(dict(prior))
        replay["idempotent_replay"] = True
        replay["runtime_transition_performed"] = False
        replay["database_write_performed"] = False
        replay["queue_or_worker_action_performed"] = False
        return replay

    if (
        request.get("job_id") != snapshot.get("job_id")
        or request.get("expected_state") != snapshot.get("job_state")
        or request.get("expected_state_version") != snapshot.get("state_version")
    ):
        return _reject(snapshot, request, "COMPARE_AND_SET_MISMATCH", fingerprint)

    source = str(snapshot["job_state"])
    target = str(request["target_state"])
    if source in TERMINAL_STATES:
        return _reject(snapshot, request, "TERMINAL_STATE_IMMUTABLE", fingerprint)
    if target not in ALLOWED_TRANSITIONS.get(source, []):
        return _reject(snapshot, request, "TRANSITION_NOT_ALLOWED", fingerprint)

    if target == "CANCELLED" and not request.get("stop_reason"):
        return _reject(snapshot, request, "MISSING_STOP_REASON", fingerprint)

    if source == "RETRY_WAIT" and target == "QUEUED" and (
        not snapshot.get("next_eligible_at")
        or not request.get("next_eligible_evidence_ref")
    ):
        return _reject(
            snapshot, request, "MISSING_RETRY_SCHEDULE_EVIDENCE", fingerprint
        )

    paused_retry_resume = (
        source == "PAUSED"
        and target == "QUEUED"
        and snapshot.get("retry_pending") is True
    )
    if paused_retry_resume and (
        not snapshot.get("next_eligible_at")
        or not request.get("next_eligible_evidence_ref")
        or request.get("guard_facts", {}).get("next_eligible_reached") is not True
    ):
        return _reject(
            snapshot, request, "MISSING_RETRY_SCHEDULE_EVIDENCE", fingerprint
        )

    if target == "RETRY_WAIT":
        retry_is_eligible = snapshot["retry_count"] < snapshot["max_retries"]
        if retry_is_eligible and not request.get("next_eligible_at"):
            return _reject(
                snapshot, request, "MISSING_RETRY_SCHEDULE_EVIDENCE", fingerprint
            )
        if not retry_is_eligible and request.get("next_eligible_at") is not None:
            return _reject(
                snapshot, request, "INVALID_RETRY_SCHEDULE_EVIDENCE", fingerprint
            )

    if (
        source == "RETRY_WAIT"
        and snapshot.get("retry_disposition") == "exhausted"
        and target != "DEAD_LETTERED"
    ):
        return _reject(
            snapshot, request, "EXHAUSTED_RETRY_MUST_DEAD_LETTER", fingerprint
        )

    edge = f"{source}->{target}"
    guards = _as_object(transition.get("edge_guard_requirements"))
    required_guards = guards.get(edge)
    if not isinstance(required_guards, list):
        return _reject(snapshot, request, "MISSING_EDGE_CONTRACT", fingerprint)
    facts = request["guard_facts"]
    if any(facts.get(name) is not True for name in required_guards):
        return _reject(snapshot, request, "MISSING_TRANSITION_GUARD", fingerprint)

    reference_requirements = _as_object(
        transition.get("edge_reference_requirements")
    ).get(edge, ["audit_ref"])
    if not isinstance(reference_requirements, list) or any(
        not _reference_requirement_present(item, snapshot, request)
        for item in reference_requirements
    ):
        return _reject(snapshot, request, "MISSING_REQUIRED_REFERENCE", fingerprint)

    if source in ACTIVE_STATES:
        if request.get("fencing_token") != snapshot.get("fencing_token"):
            return _reject(snapshot, request, "FENCING_TOKEN_MISMATCH", fingerprint)

    next_snapshot = copy.deepcopy(dict(snapshot))
    next_snapshot["job_state"] = target
    next_snapshot["state_version"] = snapshot["state_version"] + 1
    if request.get("input_refs"):
        next_snapshot["input_refs"] = copy.deepcopy(request["input_refs"])
    if request.get("output_refs"):
        next_snapshot["output_refs"] = copy.deepcopy(request["output_refs"])
    for field in (
        "checkpoint_ref",
        "quarantine_ref",
        "error_ref",
        "pause_reason_code",
        "stop_reason",
    ):
        if request.get(field) is not None:
            next_snapshot[field] = request[field]

    if source == "QUEUED" and target == "CLAIMED":
        claim = request.get("candidate_claim")
        assert isinstance(claim, dict)
        if claim["fencing_token"] <= snapshot["fencing_token"]:
            return _reject(snapshot, request, "FENCING_TOKEN_NOT_ADVANCED", fingerprint)
        next_snapshot.update(copy.deepcopy(claim))
        next_snapshot["lease_active"] = True
        next_snapshot["lock_active"] = True

    if source in ACTIVE_STATES and target not in ACTIVE_STATES:
        next_snapshot["lease_active"] = False
        next_snapshot["lock_active"] = False
        next_snapshot["lease_owner_ref"] = None
        next_snapshot["lease_expires_at"] = None
        next_snapshot["lock_key"] = None
        next_snapshot["fencing_token"] = snapshot["fencing_token"] + 1

    if target == "RETRY_WAIT":
        if snapshot["retry_count"] < snapshot["max_retries"]:
            next_snapshot["retry_pending"] = True
            next_snapshot["retry_disposition"] = "eligible"
            next_snapshot["next_eligible_at"] = request["next_eligible_at"]
        else:
            next_snapshot["retry_pending"] = False
            next_snapshot["retry_disposition"] = "exhausted"
            next_snapshot["next_eligible_at"] = None

    if source == "RETRY_WAIT" and target == "QUEUED":
        if (
            snapshot.get("retry_pending") is not True
            or snapshot.get("retry_disposition") != "eligible"
            or snapshot["retry_count"] >= snapshot["max_retries"]
        ):
            return _reject(
                snapshot, request, "RETRY_ADMISSION_NOT_RESERVED", fingerprint
            )
        next_snapshot["retry_count"] = snapshot["retry_count"] + 1
        next_snapshot["retry_pending"] = False
        next_snapshot["retry_disposition"] = "none"
        next_snapshot["next_eligible_at"] = None

    if source == "RETRY_WAIT" and target == "PAUSED":
        if (
            snapshot.get("retry_pending") is not True
            or snapshot.get("retry_disposition") != "eligible"
        ):
            return _reject(
                snapshot, request, "RETRY_PAUSE_NOT_ELIGIBLE", fingerprint
            )
        next_snapshot["retry_pending"] = True
        next_snapshot["retry_disposition"] = "eligible"

    if source == "PAUSED" and target == "QUEUED":
        if snapshot.get("retry_pending") is True:
            if (
                snapshot.get("retry_disposition") != "eligible"
                or snapshot["retry_count"] >= snapshot["max_retries"]
            ):
                return _reject(
                    snapshot, request, "RETRY_ADMISSION_NOT_RESERVED", fingerprint
                )
            next_snapshot["retry_count"] = snapshot["retry_count"] + 1
            next_snapshot["retry_pending"] = False
            next_snapshot["retry_disposition"] = "none"
            next_snapshot["next_eligible_at"] = None
        next_snapshot["pause_reason_code"] = None

    if source == "RETRY_WAIT" and target == "DEAD_LETTERED":
        if not (
            snapshot.get("retry_disposition") == "exhausted"
            and snapshot.get("retry_pending") is False
            and snapshot["retry_count"] == snapshot["max_retries"]
        ):
            return _reject(
                snapshot, request, "RETRY_EXHAUSTION_NOT_PROVEN", fingerprint
            )

    result = _decision_base(
        snapshot,
        request,
        accepted=True,
        result_code="TRANSITION_ACCEPTED",
        fingerprint=fingerprint,
    )
    result["next_snapshot"] = next_snapshot
    result["transition_candidate"] = {
        "candidate_only": True,
        "transition_request_id": request_id,
        "job_id": snapshot["job_id"],
        "job_type": snapshot["job_type"],
        "previous_state": source,
        "current_state": target,
        "previous_state_version": snapshot["state_version"],
        "current_state_version": next_snapshot["state_version"],
        "reason_code": request["reason_code"],
        "stop_reason": request["stop_reason"],
        "next_eligible_at": next_snapshot["next_eligible_at"],
        "next_eligible_evidence_ref": request["next_eligible_evidence_ref"],
        "actor_ref": request["actor_ref"],
        "audit_ref": request["audit_ref"],
        "transition_timestamp": None,
        "timestamp_persistence_required": True,
        "append_only_audit_required": True,
        "persisted": False,
    }
    result["human_status_projection"] = _projection(contract, target)
    return result


def _scenario_snapshot(
    scenario_id: str, state: str = "CREATED", **overrides: Any
) -> dict[str, Any]:
    active = state in ACTIVE_STATES
    snapshot: dict[str, Any] = {
        "evaluation_mode": EVALUATION_MODE,
        "job_id": f"contract:{PHASE3_TASK_ID}:{scenario_id}",
        "job_type": "IMPORT",
        "job_state": state,
        "state_version": 0,
        "retry_count": 0,
        "max_retries": 2,
        "retry_pending": False,
        "retry_disposition": "none",
        "next_eligible_at": None,
        "lease_active": active,
        "lock_active": active,
        "fencing_token": 7 if active else 0,
        "attempt_id": (
            f"acceptance:{ACCEPTANCE_ID}:{scenario_id}" if active else None
        ),
        "lease_owner_ref": f"task:{PHASE3_TASK_ID}" if active else None,
        "lease_expires_at": (
            "policy:POLICY_VALUE_DEFERRED_TO_STAGE039_040_041"
            if active
            else None
        ),
        "lock_key": f"contract:ids.job_state.v1:{scenario_id}" if active else None,
        "pause_reason_code": None,
        "stop_reason": (
            "CONTRACT_TERMINAL_CANCELLED" if state == "CANCELLED" else None
        ),
        "input_refs": [
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/"
            "STAGE037_PHASE1_SCOPE_BOUNDARY.md#Job-Control-Envelope"
        ],
        "output_refs": [],
        "checkpoint_ref": None,
        "quarantine_ref": None,
        "error_ref": None,
    }
    snapshot.update(overrides)
    return snapshot


def _scenario_request(
    snapshot: Mapping[str, Any],
    target_state: str,
    request_suffix: str,
    **overrides: Any,
) -> dict[str, Any]:
    request: dict[str, Any] = {
        "job_id": snapshot.get("job_id"),
        "transition_request_id": (
            f"acceptance:{ACCEPTANCE_ID}:{request_suffix}"
        ),
        "expected_state": snapshot.get("job_state"),
        "expected_state_version": snapshot.get("state_version"),
        "target_state": target_state,
        "actor_ref": f"task:{PHASE3_TASK_ID}",
        "reason_code": "PHASE3_STATIC_ADVERSARIAL_SCENARIO",
        "audit_ref": (
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/"
            "STAGE037_PHASE3_ADVERSARIAL_SCENARIOS.md#Truthful-Scenario-Result"
        ),
        "guard_facts": {},
        "input_refs": [],
        "output_refs": [],
        "checkpoint_ref": None,
        "quarantine_ref": None,
        "error_ref": None,
        "resource_gate_refs": [],
        "pause_reason_code": None,
        "stop_reason": None,
        "next_eligible_at": None,
        "next_eligible_evidence_ref": None,
        "fencing_token": None,
        "candidate_claim": None,
    }
    request.update(overrides)
    return request


def _scenario_result(
    decision: Mapping[str, Any],
    *,
    phase2_contract_valid: bool,
    expected_accepted: bool,
    expected_result_code: str,
    expected_state: Optional[str],
    evidence: str,
    owner_explanation_zh: str,
    invariant_checks: Mapping[str, bool],
) -> dict[str, Any]:
    next_snapshot = decision.get("next_snapshot")
    transition_candidate = decision.get("transition_candidate")
    candidate_created = (
        next_snapshot is not None or transition_candidate is not None
    )
    observed_state = (
        next_snapshot.get("job_state") if isinstance(next_snapshot, dict) else None
    )
    observed_accepted = decision.get("accepted")
    observed_code = decision.get("result_code")
    checks = {
        "phase2_contract_valid": phase2_contract_valid,
        "accepted_matches": observed_accepted is expected_accepted,
        "result_code_matches": observed_code == expected_result_code,
        "state_matches": observed_state == expected_state,
        "candidate_presence_matches": (
            isinstance(next_snapshot, dict)
            and isinstance(transition_candidate, dict)
            if expected_accepted
            else next_snapshot is None and transition_candidate is None
        ),
        "runtime_transition_not_performed": (
            decision.get("runtime_transition_performed") is False
        ),
        "database_write_not_performed": (
            decision.get("database_write_performed") is False
        ),
        "queue_or_worker_action_not_performed": (
            decision.get("queue_or_worker_action_performed") is False
        ),
        **{name: value is True for name, value in invariant_checks.items()},
    }
    return {
        "status": "PASS" if all(checks.values()) else "FAIL",
        "fact_level": SCENARIO_FACT_LEVEL,
        "expected_outcome": "ACCEPT" if expected_accepted else "BLOCK",
        "observed_accepted": observed_accepted,
        "observed_result_code": observed_code,
        "observed_state": observed_state,
        "candidate_created": candidate_created,
        "invariant_checks": checks,
        "evidence": evidence,
        "owner_explanation_zh": owner_explanation_zh,
        "live_execution_performed": False,
    }


def build_stage037_scenario_validation_report(
    *, contract: Optional[dict[str, Any]] = None
) -> dict[str, Any]:
    if contract is None:
        try:
            loaded_contract = load_contract()
        except (OSError, ValueError, json.JSONDecodeError):
            loaded_contract = {}
        contract_object = loaded_contract if isinstance(loaded_contract, dict) else {}
    else:
        contract_object = contract if isinstance(contract, dict) else {}

    phase2_report = build_stage037_job_state_report(index=contract_object)
    phase2_valid = phase2_report["contract_valid"] is True

    duplicate_snapshot = _scenario_snapshot("duplicate-click")
    duplicate_request = _scenario_request(
        duplicate_snapshot,
        "QUEUED",
        "duplicate-click",
        guard_facts={
            "identity_idempotency_valid": True,
            "admission_gates_passed": True,
            "no_active_claim_or_lock": True,
        },
    )
    duplicate_first = evaluate_transition(
        duplicate_snapshot, duplicate_request, contract=contract_object
    )
    duplicate_replay = evaluate_transition(
        duplicate_snapshot,
        duplicate_request,
        contract=contract_object,
        prior_results={
            str(duplicate_request["transition_request_id"]): duplicate_first
        },
    )
    conflict_request = copy.deepcopy(duplicate_request)
    conflict_request["target_state"] = "CANCELLED"
    duplicate_conflict = evaluate_transition(
        duplicate_snapshot,
        conflict_request,
        contract=contract_object,
        prior_results={
            str(duplicate_request["transition_request_id"]): duplicate_first
        },
    )

    crash_snapshot = _scenario_snapshot(
        "worker-crash", "RUNNING", state_version=4
    )
    crash_request = _scenario_request(
        crash_snapshot,
        "RETRY_WAIT",
        "worker-crash-retry",
        fencing_token=7,
        error_ref=(
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/"
            "STAGE037_PHASE3_ADVERSARIAL_SCENARIOS.md#Scenario-Matrix"
        ),
        next_eligible_at="policy:STAGE039:next-eligible-at",
        guard_facts={
            "lease_valid_or_expiry_evidence": True,
            "fencing_token_matches": True,
            "retryable_failure_recorded": True,
            "error_evidence_present": True,
        },
    )
    worker_crash = evaluate_transition(
        crash_snapshot, crash_request, contract=contract_object
    )
    crash_next = worker_crash.get("next_snapshot")
    worker_crash_prerequisite_exact = (
        worker_crash.get("accepted") is True
        and isinstance(crash_next, dict)
        and crash_next.get("job_state") == "RETRY_WAIT"
        and crash_next.get("state_version") == crash_snapshot["state_version"] + 1
        and crash_next.get("retry_pending") is True
        and crash_next.get("lease_active") is False
        and crash_next.get("lock_active") is False
        and crash_next.get("fencing_token")
        == crash_snapshot["fencing_token"] + 1
    )
    stale_worker_request = _scenario_request(
        crash_snapshot,
        "SUCCEEDED",
        "stale-worker-success",
        fencing_token=7,
        output_refs=[
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/"
            "STAGE037_PHASE3_ADVERSARIAL_SCENARIOS.md#Scenario-Matrix"
        ],
        guard_facts={
            "live_lease_valid": True,
            "fencing_token_matches": True,
            "output_validated": True,
        },
    )
    stale_worker_snapshot = (
        crash_next if worker_crash_prerequisite_exact else crash_snapshot
    )
    stale_worker = (
        _reject(
            stale_worker_snapshot,
            stale_worker_request,
            "SCENARIO_PREREQUISITE_FAILED",
        )
        if phase2_valid and not worker_crash_prerequisite_exact
        else evaluate_transition(
            stale_worker_snapshot,
            stale_worker_request,
            contract=contract_object,
        )
    )

    drive_snapshot = _scenario_snapshot("drive-offline", "QUEUED")
    drive_pause_request = _scenario_request(
        drive_snapshot,
        "PAUSED",
        "drive-offline-pause",
        pause_reason_code="SAFE_MODE_DRIVE_OFFLINE",
        resource_gate_refs=[
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/"
            "STAGE008_PHASE2_REMOVABLE_DRIVE_STATE.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/"
            "STAGE011_PHASE2_SAFE_MODE_BASELINE.md",
        ],
        guard_facts={
            "resource_gate_blocked": True,
            "no_active_claim_or_lock": True,
        },
    )
    drive_paused = evaluate_transition(
        drive_snapshot, drive_pause_request, contract=contract_object
    )
    drive_paused_snapshot = drive_paused.get("next_snapshot")
    drive_pause_prerequisite_exact = (
        drive_paused.get("accepted") is True
        and isinstance(drive_paused_snapshot, dict)
        and drive_paused_snapshot.get("job_state") == "PAUSED"
        and drive_paused_snapshot.get("state_version")
        == drive_snapshot["state_version"] + 1
        and drive_paused_snapshot.get("pause_reason_code")
        == "SAFE_MODE_DRIVE_OFFLINE"
        and drive_paused_snapshot.get("lease_active") is False
        and drive_paused_snapshot.get("lock_active") is False
    )
    drive_resume_snapshot = (
        drive_paused_snapshot
        if drive_pause_prerequisite_exact
        else _scenario_snapshot(
            "drive-offline",
            "PAUSED",
            state_version=1,
            pause_reason_code="SAFE_MODE_DRIVE_OFFLINE",
        )
    )
    drive_resume_request = _scenario_request(
        drive_resume_snapshot,
        "QUEUED",
        "drive-reconnect-without-owner",
        guard_facts={
            "resource_gates_passed": True,
            "no_active_claim_or_lock": True,
        },
    )
    drive_auto_resume = (
        _reject(
            drive_resume_snapshot,
            drive_resume_request,
            "SCENARIO_PREREQUISITE_FAILED",
        )
        if phase2_valid and not drive_pause_prerequisite_exact
        else evaluate_transition(
            drive_resume_snapshot,
            drive_resume_request,
            contract=contract_object,
        )
    )

    low_disk_snapshot = _scenario_snapshot(
        "low-disk",
        "RETRY_WAIT",
        state_version=3,
        retry_pending=True,
        retry_disposition="eligible",
        next_eligible_at="policy:STAGE039:next-eligible-at",
        error_ref=(
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/"
            "STAGE037_PHASE3_ADVERSARIAL_SCENARIOS.md#Scenario-Matrix"
        ),
    )
    low_disk_request = _scenario_request(
        low_disk_snapshot,
        "PAUSED",
        "low-disk-retry-pause",
        pause_reason_code="BUDGET_BLOCKED_LOW_FREE",
        resource_gate_refs=[
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/"
            "STAGE009_PHASE2_STORAGE_BUDGET_BASELINE.md"
        ],
        guard_facts={
            "resource_gate_blocked": True,
            "no_active_claim_or_lock": True,
        },
    )
    low_disk_paused = evaluate_transition(
        low_disk_snapshot, low_disk_request, contract=contract_object
    )

    same_source_refs = [
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/"
        "STAGE016_PHASE2_IMPORT_IDEMPOTENCY_SLICE.md"
        "#Import-Idempotency-Key"
    ]
    same_source_lock_key = (
        "contract:IDS-V0_1-STAGE016-P2:ids-import-file-sha256"
    )
    concurrency_holder_snapshot = _scenario_snapshot(
        "same-source-holder",
        "QUEUED",
        input_refs=same_source_refs,
    )
    concurrency_holder_claim = {
        "attempt_id": f"acceptance:{ACCEPTANCE_ID}:same-source-holder",
        "lease_owner_ref": f"task:{PHASE3_TASK_ID}:same-source-holder",
        "lease_expires_at": "policy:POLICY_VALUE_DEFERRED_TO_STAGE039_040_041",
        "fencing_token": 1,
        "lock_key": same_source_lock_key,
    }
    concurrency_holder_request = _scenario_request(
        concurrency_holder_snapshot,
        "CLAIMED",
        "same-source-holder-claim",
        guard_facts={
            "admission_gates_passed": True,
            "claim_lease_and_lock_acquired": True,
        },
        candidate_claim=concurrency_holder_claim,
    )
    concurrency_holder = evaluate_transition(
        concurrency_holder_snapshot,
        concurrency_holder_request,
        contract=contract_object,
    )

    concurrency_snapshot = _scenario_snapshot(
        "same-source-contender",
        "QUEUED",
        input_refs=same_source_refs,
    )
    concurrency_claim = {
        "attempt_id": f"acceptance:{ACCEPTANCE_ID}:same-source-contender",
        "lease_owner_ref": f"task:{PHASE3_TASK_ID}:same-source-contender",
        "lease_expires_at": "policy:POLICY_VALUE_DEFERRED_TO_STAGE039_040_041",
        "fencing_token": 1,
        "lock_key": same_source_lock_key,
    }
    concurrency_request = _scenario_request(
        concurrency_snapshot,
        "CLAIMED",
        "same-source-second-claim",
        reason_code="SAME_SOURCE_LOCK_HELD_STATIC_EVIDENCE",
        guard_facts={
            "admission_gates_passed": True,
            "claim_lease_and_lock_acquired": False,
        },
        candidate_claim=concurrency_claim,
    )
    concurrency_blocked = evaluate_transition(
        concurrency_snapshot, concurrency_request, contract=contract_object
    )

    lock_snapshot = _scenario_snapshot("lock-proof", "QUEUED")
    lock_claim = {
        "attempt_id": f"acceptance:{ACCEPTANCE_ID}:lock-proof",
        "lease_owner_ref": f"task:{PHASE3_TASK_ID}:lock-proof",
        "lease_expires_at": "policy:POLICY_VALUE_DEFERRED_TO_STAGE039_040_041",
        "fencing_token": 1,
        "lock_key": "contract:ids.job_state.v1:lock-proof",
    }
    lock_positive_request = _scenario_request(
        lock_snapshot,
        "CLAIMED",
        "lock-proof-control",
        guard_facts={
            "admission_gates_passed": True,
            "claim_lease_and_lock_acquired": True,
        },
        candidate_claim=lock_claim,
    )
    lock_positive = evaluate_transition(
        lock_snapshot, lock_positive_request, contract=contract_object
    )
    lock_request = copy.deepcopy(lock_positive_request)
    lock_request["guard_facts"]["claim_lease_and_lock_acquired"] = False
    lock_blocked = evaluate_transition(
        lock_snapshot, lock_request, contract=contract_object
    )

    cleanup_snapshot = _scenario_snapshot(
        "cleanup-protection",
        "PAUSED",
        pause_reason_code="OWNER_HOLD",
    )
    cleanup_baseline_request = _scenario_request(
        cleanup_snapshot,
        "CANCELLED",
        "cleanup-through-transition",
        stop_reason="OWNER_REQUESTED_CANCEL",
        guard_facts={"no_active_claim_or_lock": True},
    )
    cleanup_baseline = evaluate_transition(
        cleanup_snapshot,
        cleanup_baseline_request,
        contract=contract_object,
    )
    cleanup_request = copy.deepcopy(cleanup_baseline_request)
    cleanup_request["cleanup_manifest_ref"] = (
        "contract:STAGE-044:cleanup-runtime-not-authorized"
    )
    cleanup_blocked = evaluate_transition(
        cleanup_snapshot, cleanup_request, contract=contract_object
    )

    retry_next = worker_crash.get("next_snapshot")
    drive_next = drive_paused.get("next_snapshot")
    low_disk_next = low_disk_paused.get("next_snapshot")
    concurrency_holder_next = concurrency_holder.get("next_snapshot")
    lock_positive_next = lock_positive.get("next_snapshot")
    cleanup_baseline_next = cleanup_baseline.get("next_snapshot")
    lock_proof_only_changed = copy.deepcopy(lock_positive_request)
    lock_proof_only_changed["guard_facts"][
        "claim_lease_and_lock_acquired"
    ] = False
    cleanup_only_field_added = (
        set(cleanup_request) - set(cleanup_baseline_request)
        == {"cleanup_manifest_ref"}
        and all(
            cleanup_request.get(key) == value
            for key, value in cleanup_baseline_request.items()
        )
    )
    cleanup_contract = _as_object(contract_object.get("cleanup_boundary"))
    scenario_results = {
        "duplicate_click_idempotent_replay": _scenario_result(
            duplicate_replay,
            phase2_contract_valid=phase2_valid,
            expected_accepted=True,
            expected_result_code="TRANSITION_ACCEPTED",
            expected_state="QUEUED",
            evidence=(
                "the same transition_request_id and payload returns the exact "
                "original in-memory candidate with idempotent_replay=true"
            ),
            owner_explanation_zh=(
                "重复点击使用同一请求标识时只返回原确定性候选，不产生第二次状态变更或审计写入。"
            ),
            invariant_checks={
                "first_candidate_accepted": duplicate_first.get("accepted") is True,
                "idempotent_replay_marked": (
                    duplicate_replay.get("idempotent_replay") is True
                ),
                "candidate_unchanged": duplicate_replay.get("next_snapshot")
                == duplicate_first.get("next_snapshot"),
            },
        ),
        "duplicate_click_payload_conflict": _scenario_result(
            duplicate_conflict,
            phase2_contract_valid=phase2_valid,
            expected_accepted=False,
            expected_result_code="TRANSITION_REQUEST_CONFLICT",
            expected_state=None,
            evidence=(
                "reusing a transition_request_id with a different target state "
                "fails closed before a candidate is produced"
            ),
            owner_explanation_zh=(
                "同一请求标识若携带不同目标状态会失败关闭，防止重复点击被篡改成另一项操作。"
            ),
            invariant_checks={
                "no_conflicting_candidate": duplicate_conflict.get("next_snapshot")
                is None,
            },
        ),
        "worker_crash_retry_reservation": _scenario_result(
            worker_crash,
            phase2_contract_valid=phase2_valid,
            expected_accepted=True,
            expected_result_code="TRANSITION_ACCEPTED",
            expected_state="RETRY_WAIT",
            evidence=(
                "lease-expiry evidence routes RUNNING to RETRY_WAIT, reserves one "
                "retry, revokes lease/lock, and advances fencing without runtime"
            ),
            owner_explanation_zh=(
                "worker 崩溃只形成等待重试候选；重试次数尚未消费，旧租约和锁已在候选中撤销。"
            ),
            invariant_checks={
                "retry_reserved_without_consumption": isinstance(retry_next, dict)
                and retry_next.get("retry_pending") is True
                and retry_next.get("retry_count") == crash_snapshot["retry_count"],
                "lease_and_lock_revoked": isinstance(retry_next, dict)
                and retry_next.get("lease_active") is False
                and retry_next.get("lock_active") is False,
                "fencing_advanced": isinstance(retry_next, dict)
                and retry_next.get("fencing_token")
                == crash_snapshot["fencing_token"] + 1,
            },
        ),
        "stale_worker_fencing_block": _scenario_result(
            stale_worker,
            phase2_contract_valid=phase2_valid,
            expected_accepted=False,
            expected_result_code="COMPARE_AND_SET_MISMATCH",
            expected_state=None,
            evidence=(
                "a stale success request evaluated against the post-crash retry "
                "snapshot cannot satisfy compare-and-set"
            ),
            owner_explanation_zh=(
                "崩溃后的旧 worker 不能再标记成功；状态版本已推进，旧请求按 CAS 失败关闭。"
            ),
            invariant_checks={
                "worker_crash_prerequisite_exact": (
                    worker_crash_prerequisite_exact
                ),
                "no_stale_success_candidate": stale_worker.get("next_snapshot")
                is None,
            },
        ),
        "removable_drive_offline_pause": _scenario_result(
            drive_paused,
            phase2_contract_valid=phase2_valid,
            expected_accepted=True,
            expected_result_code="TRANSITION_ACCEPTED",
            expected_state="PAUSED",
            evidence=(
                "SAFE_MODE_DRIVE_OFFLINE plus tracked STAGE008/STAGE011 refs "
                "pauses a queued candidate without acquiring a worker lease"
            ),
            owner_explanation_zh=(
                "移动硬盘离线时任务保持暂停候选，不领取 worker，也不会因设备重新出现而自动恢复。"
            ),
            invariant_checks={
                "drive_reason_preserved": isinstance(drive_next, dict)
                and drive_next.get("pause_reason_code")
                == "SAFE_MODE_DRIVE_OFFLINE",
                "no_claim_activated": isinstance(drive_next, dict)
                and drive_next.get("lease_active") is False
                and drive_next.get("lock_active") is False,
            },
        ),
        "drive_reconnect_no_auto_resume": _scenario_result(
            drive_auto_resume,
            phase2_contract_valid=phase2_valid,
            expected_accepted=False,
            expected_result_code="MISSING_TRANSITION_GUARD",
            expected_state=None,
            evidence=(
                "PAUSED to QUEUED without owner_revalidated remains blocked even "
                "when a resource-gates-passed fact is supplied"
            ),
            owner_explanation_zh=(
                "设备重连不等于自动恢复；缺少 owner 复核时，暂停任务不能重新排队。"
            ),
            invariant_checks={
                "drive_pause_prerequisite_exact": drive_pause_prerequisite_exact,
                "paused_candidate_not_resumed": drive_auto_resume.get(
                    "next_snapshot"
                )
                is None,
            },
        ),
        "low_disk_retry_pause_preserves_budget": _scenario_result(
            low_disk_paused,
            phase2_contract_valid=phase2_valid,
            expected_accepted=True,
            expected_result_code="TRANSITION_ACCEPTED",
            expected_state="PAUSED",
            evidence=(
                "BUDGET_BLOCKED_LOW_FREE pauses an eligible retry while keeping "
                "retry_pending=true and retry_count unchanged"
            ),
            owner_explanation_zh=(
                "低磁盘条件只暂停已保留的重试资格，不提前消耗重试次数，也不启动反压运行时。"
            ),
            invariant_checks={
                "retry_reservation_preserved": isinstance(low_disk_next, dict)
                and low_disk_next.get("retry_pending") is True
                and low_disk_next.get("retry_disposition") == "eligible",
                "retry_count_unchanged": isinstance(low_disk_next, dict)
                and low_disk_next.get("retry_count")
                == low_disk_snapshot["retry_count"],
                "low_disk_reason_preserved": isinstance(low_disk_next, dict)
                and low_disk_next.get("pause_reason_code")
                == "BUDGET_BLOCKED_LOW_FREE",
            },
        ),
        "same_source_concurrency_blocked": _scenario_result(
            concurrency_blocked,
            phase2_contract_valid=phase2_valid,
            expected_accepted=False,
            expected_result_code="MISSING_TRANSITION_GUARD",
            expected_state=None,
            evidence=(
                "a same-source second claim with claim_lease_and_lock_acquired=false "
                "cannot produce a CLAIMED candidate"
            ),
            owner_explanation_zh=(
                "同源并发只有在后续锁运行时证明已取得唯一租约和锁后才能领取；当前证明失败即阻断。"
            ),
            invariant_checks={
                "first_same_source_claim_accepted": (
                    concurrency_holder.get("accepted") is True
                    and isinstance(concurrency_holder_next, dict)
                    and concurrency_holder_next.get("job_state") == "CLAIMED"
                ),
                "distinct_job_ids": concurrency_holder_snapshot.get("job_id")
                != concurrency_snapshot.get("job_id"),
                "shared_source_identity": (
                    concurrency_holder_snapshot.get("input_refs")
                    == concurrency_snapshot.get("input_refs")
                    == same_source_refs
                ),
                "shared_lock_key": (
                    concurrency_holder_claim.get("lock_key")
                    == concurrency_claim.get("lock_key")
                    == same_source_lock_key
                ),
                "second_claim_envelope_complete": (
                    set(concurrency_claim) == CLAIM_KEYS
                    and concurrency_claim.get("fencing_token")
                    > concurrency_snapshot.get("fencing_token")
                ),
                "no_second_claim_candidate": concurrency_blocked.get(
                    "next_snapshot"
                )
                is None,
            },
        ),
        "lock_claim_without_proof_blocked": _scenario_result(
            lock_blocked,
            phase2_contract_valid=phase2_valid,
            expected_accepted=False,
            expected_result_code="MISSING_TRANSITION_GUARD",
            expected_state=None,
            evidence=(
                "QUEUED to CLAIMED without positive lock-acquisition proof fails "
                "before any worker or lock action"
            ),
            owner_explanation_zh=(
                "没有锁取得证明就不能形成领取候选；Phase 3 不创建锁记录或 worker。"
            ),
            invariant_checks={
                "positive_claim_accepted": (
                    lock_positive.get("accepted") is True
                    and isinstance(lock_positive_next, dict)
                    and lock_positive_next.get("job_state") == "CLAIMED"
                ),
                "negative_claim_envelope_complete": (
                    isinstance(lock_request.get("candidate_claim"), dict)
                    and set(lock_request["candidate_claim"]) == CLAIM_KEYS
                ),
                "only_lock_proof_changed": (
                    lock_request == lock_proof_only_changed
                ),
                "no_unproven_claim_candidate": lock_blocked.get("next_snapshot")
                is None,
            },
        ),
        "cleanup_authorization_blocked": _scenario_result(
            cleanup_blocked,
            phase2_contract_valid=phase2_valid,
            expected_accepted=False,
            expected_result_code="INVALID_REQUEST_SHAPE",
            expected_state=None,
            evidence=(
                "adding cleanup_manifest_ref to a state-transition request is an "
                "unknown request shape and cleanup remains STAGE044-owned"
            ),
            owner_explanation_zh=(
                "状态转换不能夹带清理授权；清理仍由 Stage 44 独立门禁，当前不会删除任何内容。"
            ),
            invariant_checks={
                "baseline_cancel_accepted": (
                    cleanup_baseline.get("accepted") is True
                    and isinstance(cleanup_baseline_next, dict)
                    and cleanup_baseline_next.get("job_state") == "CANCELLED"
                ),
                "only_cleanup_field_added": cleanup_only_field_added,
                "state_transition_does_not_authorize_deletion": (
                    cleanup_contract.get("state_transition_authorizes_deletion")
                    is False
                ),
                "cleanup_runtime_disabled": (
                    cleanup_contract.get("cleanup_runtime_allowed") is False
                ),
                "no_cleanup_candidate": cleanup_blocked.get("next_snapshot")
                is None,
            },
        ),
    }
    scenario_validation_valid = (
        phase2_valid
        and tuple(scenario_results) == EXPECTED_PHASE3_SCENARIOS
        and all(
            result.get("status") == "PASS"
            for result in scenario_results.values()
        )
    )
    return {
        "schema_version": PHASE3_REPORT_SCHEMA_VERSION,
        "phase2_schema_version": REPORT_SCHEMA_VERSION,
        "index_schema_version": INDEX_SCHEMA_VERSION,
        "stage": "STAGE-037",
        "phase": "Phase 3",
        "task_id": PHASE3_TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "job_state_model_contract_id": CONTRACT_ID,
        "phase2_contract_valid": phase2_valid,
        "scenario_validation_valid": scenario_validation_valid,
        "scenario_results": scenario_results,
        "execution_mode": PHASE3_EXECUTION_MODE,
        "execution_ready": False,
        "execution_state": (
            PHASE3_VALID_STATE if scenario_validation_valid else INVALID_STATE
        ),
        "live_execution_performed": False,
        "queue_runtime_performed": False,
        "worker_runtime_performed": False,
        "retry_scheduler_performed": False,
        "backpressure_runtime_performed": False,
        "lock_runtime_performed": False,
        "automatic_lifecycle_runtime_performed": False,
        "crash_recovery_runtime_performed": False,
        "cleanup_runtime_performed": False,
        "database_connection_performed": False,
        "schema_change_performed": False,
        "state_registry_write_performed": False,
        "runtime_output_written": False,
        "real_job_created": False,
        "fake_ids_business_data_used": False,
        "raw_metadata_content_accessed": False,
        "phase2_report": phase2_report,
        "next_gate": PHASE3_NEXT_GATE,
        "github_upload_allowed": False,
        "app_reinstall_allowed": False,
        "owner_feedback_zh": (
            "任务状态模型 Phase 3 静态异常场景验证通过；所有结果仅为内存合同候选，"
            "未运行 worker、磁盘动作、锁、清理或数据库。"
            if scenario_validation_valid
            else "任务状态模型 Phase 3 静态异常场景验证失败；已失败关闭，禁止进入 Phase 4。"
        ),
    }


def build_stage037_delivery_report(
    *,
    contract: Optional[dict[str, Any]] = None,
    review_governance_report: Optional[Mapping[str, Any]] = None,
) -> dict[str, Any]:
    load_error: Optional[str] = None
    canonical_snapshot_bound = contract is None
    if contract is None:
        try:
            loaded_contract = load_contract()
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            loaded_contract = {}
            load_error = f"{type(exc).__name__}: {exc}"
        contract_object = (
            loaded_contract if isinstance(loaded_contract, dict) else {}
        )
        if not isinstance(loaded_contract, dict):
            canonical_snapshot_bound = False
            load_error = "index must be a JSON object"
    else:
        contract_object = contract if isinstance(contract, dict) else {}
        canonical_snapshot_bound = False
        if not isinstance(contract, dict):
            load_error = "index must be a JSON object"

    phase3_report = build_stage037_scenario_validation_report(
        contract=contract_object
    )
    phase2_report = phase3_report["phase2_report"]
    phase4_contract = _as_object(
        contract_object.get("phase4_delivery_contract")
    )
    state_model = _as_object(contract_object.get("state_model"))
    transitions = _as_object(state_model.get("allowed_transitions"))
    runtime_policy = _as_object(contract_object.get("runtime_policy"))
    truth_contract = _as_object(contract_object.get("truth_contract"))
    phase4_contract_results = _phase4_contract_results(contract_object)
    evidence_integrity, observed_evidence_sha256 = _phase4_evidence_integrity(
        phase4_contract
    )
    (
        git_tracked_sources,
        git_index_sources,
        git_head_sources,
        observed_source_sha256,
    ) = _delivery_source_binding(phase4_contract)
    governance_report = (
        _canonical_review_governance_report()
        if review_governance_report is None
        else copy.deepcopy(dict(review_governance_report))
    )
    review_governance_check_results = _review_governance_checks(governance_report)
    (
        review_git_tracked_sources,
        review_git_index_sources,
        review_git_head_sources,
        review_observed_source_sha256,
    ) = _review_source_binding()
    scenario_results = phase3_report.get("scenario_results")
    scenario_results = (
        scenario_results if isinstance(scenario_results, dict) else {}
    )
    allowed_transition_count = sum(
        len(targets)
        for targets in transitions.values()
        if isinstance(targets, list)
    )

    delivery_check_results = {
        "canonical_snapshot_bound": canonical_snapshot_bound
        and load_error is None,
        "phase2_contract_valid": phase2_report.get("contract_valid") is True,
        "phase3_scenarios_valid": phase3_report.get(
            "scenario_validation_valid"
        )
        is True,
        "ten_scenarios_pass": (
            tuple(scenario_results) == EXPECTED_PHASE3_SCENARIOS
            and all(
                isinstance(item, dict) and item.get("status") == "PASS"
                for item in scenario_results.values()
            )
        ),
        "phase4_machine_contract_valid": all(
            phase4_contract_results.values()
        ),
        "phase4_evidence_hashes_valid": all(evidence_integrity.values()),
        "canonical_sources_git_tracked": (
            bool(git_tracked_sources)
            and all(git_tracked_sources.values())
            and all(observed_source_sha256.values())
        ),
        "canonical_sources_match_git_index": (
            bool(git_index_sources) and all(git_index_sources.values())
        ),
        "review_governance_valid": (
            bool(review_governance_check_results)
            and all(review_governance_check_results.values())
        ),
        "review_sources_git_tracked": (
            bool(review_git_tracked_sources)
            and all(review_git_tracked_sources.values())
            and all(review_observed_source_sha256.values())
        ),
        "review_sources_match_git_index": (
            bool(review_git_index_sources)
            and all(review_git_index_sources.values())
        ),
        "state_graph_matches_phase2": (
            state_model.get("job_types") == JOB_TYPES
            and state_model.get("job_states") == JOB_STATES
            and state_model.get("allowed_transitions") == ALLOWED_TRANSITIONS
            and allowed_transition_count == 21
        ),
        "all_runtime_actions_disabled": (
            set(runtime_policy) == RUNTIME_KEYS
            and bool(runtime_policy)
            and all(value is False for value in runtime_policy.values())
        ),
        "truth_contract_preserved": truth_contract == EXPECTED_TRUTH_CONTRACT,
        "raw_metadata_boundary_preserved": (
            phase2_report.get("raw_metadata_content_accessed") is False
            and phase3_report.get("raw_metadata_content_accessed") is False
        ),
        "fake_data_boundary_preserved": (
            phase2_report.get("fake_ids_business_data_used") is False
            and phase3_report.get("fake_ids_business_data_used") is False
        ),
        "github_and_app_delivery_blocked": (
            phase4_contract.get("github_upload_allowed") is False
            and phase4_contract.get("app_reinstall_allowed") is False
        ),
    }
    delivery_contract_valid = all(delivery_check_results.values())
    execution_state = (
        PHASE4_VALID_STATE if delivery_contract_valid else INVALID_STATE
    )
    result = PHASE4_VALID_RESULT if delivery_contract_valid else "FAIL_CLOSED"
    review_evidence_valid = (
        delivery_check_results["review_governance_valid"]
        and delivery_check_results["review_sources_git_tracked"]
        and delivery_check_results["review_sources_match_git_index"]
    )
    stage_review_status = (
        REVIEW_STATUS
        if delivery_contract_valid
        else (
            BLOCKED_REVIEW_STATUS
            if not review_evidence_valid
            else "blocked_invalid_delivery_evidence"
        )
    )
    next_gate = REVIEW_NEXT_GATE if delivery_contract_valid else PHASE4_NEXT_GATE

    retry_evidence = copy.deepcopy(
        _as_object(phase4_contract.get("retry_evidence_contract"))
    )
    backpressure_evidence = copy.deepcopy(
        _as_object(phase4_contract.get("backpressure_evidence_contract"))
    )
    cleanup_evidence = copy.deepcopy(
        _as_object(phase4_contract.get("cleanup_evidence_contract"))
    )
    automatic_manual = copy.deepcopy(
        _as_object(phase4_contract.get("automatic_manual_boundary"))
    )
    known_limits = copy.deepcopy(phase4_contract.get("known_limits", []))
    if isinstance(known_limits, list):
        for item in known_limits:
            if (
                isinstance(item, dict)
                and item.get("limit_id") == "stage_review_and_batch_upload_blocked"
            ):
                if delivery_contract_valid:
                    item["owner_message_zh"] = (
                        "STAGE-037 whole-stage review 已完成；BATCH031_040 upload、"
                        "app reinstall 和 STAGE-038 本轮仍阻断。"
                    )

    return {
        "schema_version": PHASE4_REPORT_SCHEMA_VERSION,
        "phase3_schema_version": PHASE3_REPORT_SCHEMA_VERSION,
        "phase2_schema_version": REPORT_SCHEMA_VERSION,
        "index_schema_version": INDEX_SCHEMA_VERSION,
        "stage": "STAGE-037",
        "phase": "Phase 4",
        "task_id": PHASE4_TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "job_state_model_contract_id": CONTRACT_ID,
        "delivery_contract_valid": delivery_contract_valid,
        "delivery_check_results": delivery_check_results,
        "phase4_contract_results": phase4_contract_results,
        "result": result,
        "execution_mode": PHASE4_EXECUTION_MODE,
        "execution_ready": False,
        "execution_state": execution_state,
        "stage_review_status": stage_review_status,
        "next_gate": next_gate,
        "github_upload_allowed": False,
        "app_reinstall_allowed": False,
        "snapshot_binding": {
            "source": (
                "canonical_repository_index"
                if canonical_snapshot_bound and load_error is None
                else "in_memory_validation_snapshot"
            ),
            "canonical_snapshot_bound": canonical_snapshot_bound
            and load_error is None,
            "single_snapshot_reused": True,
            "index_ref": INDEX_PATH.relative_to(PROJECT_ROOT).as_posix(),
            "load_error": load_error,
            "evidence_integrity": evidence_integrity,
            "observed_evidence_sha256": observed_evidence_sha256,
            "all_delivery_sources_git_tracked": (
                bool(git_tracked_sources) and all(git_tracked_sources.values())
            ),
            "all_delivery_sources_match_git_index": (
                bool(git_index_sources) and all(git_index_sources.values())
            ),
            "all_delivery_sources_match_head": (
                bool(git_head_sources) and all(git_head_sources.values())
            ),
            "git_tracked_sources": git_tracked_sources,
            "git_index_sources": git_index_sources,
            "git_head_sources": git_head_sources,
            "observed_source_sha256": observed_source_sha256,
        },
        "review_governance_check_results": review_governance_check_results,
        "review_governance_binding": {
            "validator_ref": GOVERNANCE_VALIDATOR_PATH.relative_to(
                PROJECT_ROOT
            ).as_posix(),
            "validator_load_error": governance_report.get("load_error"),
            "all_review_sources_git_tracked": (
                bool(review_git_tracked_sources)
                and all(review_git_tracked_sources.values())
            ),
            "all_review_sources_match_git_index": (
                bool(review_git_index_sources)
                and all(review_git_index_sources.values())
            ),
            "all_review_sources_match_head": (
                bool(review_git_head_sources)
                and all(review_git_head_sources.values())
            ),
            "git_tracked_sources": review_git_tracked_sources,
            "git_index_sources": review_git_index_sources,
            "git_head_sources": review_git_head_sources,
            "observed_source_sha256": review_observed_source_sha256,
        },
        "state_graph": {
            "mode": _as_object(phase4_contract.get("state_graph")).get(
                "mode"
            ),
            "state_model_version": state_model.get("state_model_version"),
            "job_types": copy.deepcopy(state_model.get("job_types", [])),
            "job_states": copy.deepcopy(state_model.get("job_states", [])),
            "terminal_states": copy.deepcopy(
                state_model.get("terminal_states", [])
            ),
            "active_execution_states": copy.deepcopy(
                state_model.get("active_execution_states", [])
            ),
            "allowed_transitions": copy.deepcopy(transitions),
            "allowed_transition_count": allowed_transition_count,
            "runtime_transition_performed": False,
        },
        "retry_evidence_contract": retry_evidence,
        "backpressure_evidence_contract": backpressure_evidence,
        "cleanup_evidence_contract": cleanup_evidence,
        "automatic_manual_boundary": automatic_manual,
        "safe_shutdown_steps": copy.deepcopy(
            phase4_contract.get("safe_shutdown_steps", [])
        ),
        "recovery_steps": copy.deepcopy(
            phase4_contract.get("recovery_steps", [])
        ),
        "rollback_steps": copy.deepcopy(
            phase4_contract.get("rollback_steps", [])
        ),
        "known_limits": known_limits,
        "chinese_owner_feedback": (
            REVIEW_OWNER_FEEDBACK_ZH
            if delivery_contract_valid
            else "任务状态模型 Phase 4 交付合同无效；已失败关闭，禁止运行队列、worker、重试、反压、锁、自动生命周期、恢复或清理。"
        ),
        "live_execution_performed": False,
        "queue_runtime_performed": False,
        "worker_runtime_performed": False,
        "retry_scheduler_performed": False,
        "dead_letter_runtime_performed": False,
        "backpressure_runtime_performed": False,
        "lock_runtime_performed": False,
        "automatic_lifecycle_runtime_performed": False,
        "crash_recovery_runtime_performed": False,
        "cleanup_runtime_performed": False,
        "database_connection_performed": False,
        "schema_change_performed": False,
        "state_registry_write_performed": False,
        "runtime_output_written": False,
        "real_job_created": False,
        "fake_ids_business_data_used": False,
        "raw_metadata_content_accessed": False,
        "phase3_report": phase3_report,
        "phase2_report": phase2_report,
    }


def main() -> int:
    report = build_stage037_delivery_report()
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    checks = [
        report["delivery_contract_valid"],
        all(report["delivery_check_results"].values()),
        all(report["phase4_contract_results"].values()),
        report["result"] == PHASE4_VALID_RESULT,
        report["execution_ready"] is False,
        report["execution_state"] == PHASE4_VALID_STATE,
        report["stage_review_status"] == REVIEW_STATUS,
        report["next_gate"] == REVIEW_NEXT_GATE,
        report["github_upload_allowed"] is False,
        report["app_reinstall_allowed"] is False,
        report["live_execution_performed"] is False,
        report["queue_runtime_performed"] is False,
        report["worker_runtime_performed"] is False,
        report["retry_scheduler_performed"] is False,
        report["dead_letter_runtime_performed"] is False,
        report["backpressure_runtime_performed"] is False,
        report["lock_runtime_performed"] is False,
        report["automatic_lifecycle_runtime_performed"] is False,
        report["crash_recovery_runtime_performed"] is False,
        report["cleanup_runtime_performed"] is False,
        report["database_connection_performed"] is False,
        report["schema_change_performed"] is False,
        report["state_registry_write_performed"] is False,
        report["runtime_output_written"] is False,
        report["real_job_created"] is False,
        report["fake_ids_business_data_used"] is False,
        report["raw_metadata_content_accessed"] is False,
        report["phase3_report"]["scenario_validation_valid"],
        report["phase2_report"]["contract_valid"],
    ]
    return 0 if all(checks) else 1


if __name__ == "__main__":
    sys.exit(main())
