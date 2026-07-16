from __future__ import annotations

from typing import Final


PHASE_ID: Final = "V025-S10-P10.1"
TASK_IDS: Final = (
    "S10-P1-T1",
    "S10-P1-T2",
    "S10-P1-T3",
    "S10-P1-T4",
)
ACCEPTANCE_ID: Final = "ACC-PFI-V025-STAGE10-WHOLE-REVIEW"
JOB_LIFECYCLE_SCHEMA: Final = "PFIV025DurableJobLifecycleV1"
JOB_EVENT_SCHEMA: Final = "PFIV025DurableJobEventV1"
JOB_MIGRATION_ID: Final = "v025_stage10_durable_jobs_v1"

JOB_STATUSES: Final = (
    "queued",
    "running",
    "retrying",
    "succeeded",
    "failed",
    "cancelled",
    "dead_letter",
)
CLAIMABLE_STATUSES: Final = frozenset({"queued", "retrying"})
TERMINAL_STATUSES: Final = frozenset(
    {"succeeded", "failed", "cancelled", "dead_letter"}
)


class JobLifecycleError(RuntimeError):
    """Base error for fail-closed durable-job lifecycle operations."""


class JobConflictError(JobLifecycleError):
    """An idempotency key was reused with different immutable inputs."""


class JobTransitionError(JobLifecycleError):
    """The requested lifecycle transition is invalid for the current state."""


class LeaseConflictError(JobLifecycleError):
    """A worker does not hold the active, unexpired lease."""


class StaleRevisionError(JobLifecycleError):
    """A compare-and-swap operation used an outdated job revision."""


def build_phase_10_1_contract() -> dict[str, object]:
    """Return the executable Phase 10.1 boundary without claiming Stage acceptance."""

    return {
        "schema": JOB_LIFECYCLE_SCHEMA,
        "phase_id": PHASE_ID,
        "task_ids": list(TASK_IDS),
        "acceptance_id": ACCEPTANCE_ID,
        "status": "implementation_contract",
        "current_phase_only": True,
        "stage_10_whole_review_status": "not_started",
        "phase_10_2_started": False,
        "phase_10_3_started": False,
        "states": list(JOB_STATUSES),
        "storage": {
            "job_table": "durable_jobs",
            "event_table": "durable_job_events",
            "migration_id": JOB_MIGRATION_ID,
            "process_memory_only": False,
            "events_append_only": True,
        },
        "worker_protocol": {
            "claim_lock": "BEGIN IMMEDIATE",
            "claim_compare_and_swap": "job_id + revision + prior status",
            "lease_token_persisted": False,
            "lease_token_hash_persisted": True,
            "heartbeat_requires_active_lease": True,
            "expired_lease_recovery": True,
            "duplicate_execution_prevention": True,
        },
        "recovery": {
            "bounded_attempts": True,
            "retry": True,
            "cancel": True,
            "dead_letter": True,
            "stale_worker_write_rejected": True,
        },
        "progress": {
            "source": "durable_job_events",
            "completed_units_and_total_units_required": True,
            "monotonic": True,
            "timer_based": False,
            "heartbeat_counts_as_progress": False,
        },
        "sqlite": {
            "foreign_keys": True,
            "busy_timeout_ms": 30_000,
            "explicit_transactions": True,
            "rollback_on_error": True,
            "journal_mode": "DELETE",
            "wal_enabled": False,
            "reason": (
                "Phase 10 leaves WAL disabled; Stage 11 must prove SQLite 3.51.3+ "
                "or an official safe backport such as 3.44.6/3.50.7 before concurrent WAL"
            ),
        },
        "safety_boundary": {
            "external_network_allowed": False,
            "background_publish_unverified_financial_facts": False,
            "result_artifact_is_publication": False,
            "raw_financial_values_in_evidence": False,
            "real_database_used_by_phase_tests": False,
            "finder_used": False,
        },
    }
