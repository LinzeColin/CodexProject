from __future__ import annotations

import fcntl
import hashlib
import hmac
import json
import os
import re
import secrets
import sqlite3
import threading
import warnings
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable, Iterator, Mapping

from pfi_os.application.jobs.lifecycle import (
    CLAIMABLE_STATUSES,
    JOB_EVENT_SCHEMA,
    JOB_LIFECYCLE_SCHEMA,
    JOB_MIGRATION_ID,
    JOB_STATUSES,
    TERMINAL_STATUSES,
    JobConflictError,
    JobLifecycleError,
    JobTransitionError,
    LeaseConflictError,
    StaleRevisionError,
)
from pfi_os.infrastructure.operational_store_runtime import operational_store_guard
from pfi_os.observability.job_trace import (
    JOB_LOG_SCHEMA,
    JOB_OBSERVABILITY_MIGRATION_ID,
    JOB_SPAN_SCHEMA,
    JOB_TRACE_SCHEMA,
    deterministic_span_id,
    deterministic_trace_id,
    new_span_id,
    new_trace_id,
    normalize_observability_context,
    redact_log_fields,
    redact_log_text,
    validate_span_id,
    validate_trace_id,
)


_INITIALIZE_LOCK = threading.Lock()
_TOKEN_FACTORY = lambda: secrets.token_urlsafe(32)
_CODE_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]{0,63}$")
_NAME_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$")
_ALLOWED_ARTIFACT_PREFIXES = ("artifact://", "private://", "report://")


_MIGRATION_STATEMENTS = (
    """
    CREATE TABLE IF NOT EXISTS pfi_schema_migrations (
        migration_id TEXT PRIMARY KEY,
        applied_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS durable_jobs (
        job_id TEXT PRIMARY KEY,
        schema_version TEXT NOT NULL,
        job_type TEXT NOT NULL,
        idempotency_key TEXT NOT NULL,
        payload_json TEXT NOT NULL,
        payload_hash TEXT NOT NULL,
        contains_financial_facts INTEGER NOT NULL DEFAULT 0,
        status TEXT NOT NULL,
        revision INTEGER NOT NULL DEFAULT 0,
        attempt_count INTEGER NOT NULL DEFAULT 0,
        max_attempts INTEGER NOT NULL,
        available_at TEXT NOT NULL,
        lease_owner TEXT,
        lease_token_hash TEXT,
        lease_expires_at TEXT,
        heartbeat_at TEXT,
        progress_completed INTEGER NOT NULL DEFAULT 0,
        progress_total INTEGER NOT NULL DEFAULT 0,
        progress_step TEXT NOT NULL DEFAULT '',
        result_uri TEXT NOT NULL DEFAULT '',
        result_review_state TEXT NOT NULL DEFAULT 'not_applicable',
        error_code TEXT NOT NULL DEFAULT '',
        error_message TEXT NOT NULL DEFAULT '',
        cancel_reason TEXT NOT NULL DEFAULT '',
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        finished_at TEXT,
        UNIQUE(job_type, idempotency_key),
        CHECK(schema_version = 'PFIV025DurableJobLifecycleV1'),
        CHECK(contains_financial_facts IN (0, 1)),
        CHECK(status IN ('queued', 'running', 'retrying', 'succeeded', 'failed', 'cancelled', 'dead_letter')),
        CHECK(revision >= 0),
        CHECK(max_attempts BETWEEN 1 AND 100),
        CHECK(attempt_count BETWEEN 0 AND max_attempts),
        CHECK(progress_completed >= 0),
        CHECK(progress_total >= 0),
        CHECK(progress_completed <= progress_total),
        CHECK((progress_total = 0 AND progress_completed = 0) OR progress_total > 0),
        CHECK(result_review_state IN ('not_applicable', 'pending_human_review')),
        CHECK(
            (status = 'running' AND lease_owner IS NOT NULL AND lease_token_hash IS NOT NULL AND lease_expires_at IS NOT NULL)
            OR
            (status <> 'running' AND lease_owner IS NULL AND lease_token_hash IS NULL AND lease_expires_at IS NULL)
        ),
        CHECK(
            (status IN ('succeeded', 'failed', 'cancelled', 'dead_letter') AND finished_at IS NOT NULL)
            OR
            (status IN ('queued', 'running', 'retrying') AND finished_at IS NULL)
        )
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_durable_jobs_claim
    ON durable_jobs(job_type, status, available_at, created_at, job_id)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_durable_jobs_lease_expiry
    ON durable_jobs(status, lease_expires_at)
    """,
    """
    CREATE TABLE IF NOT EXISTS durable_job_events (
        event_id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_schema TEXT NOT NULL,
        job_id TEXT NOT NULL REFERENCES durable_jobs(job_id) ON DELETE RESTRICT,
        job_revision INTEGER NOT NULL,
        event_type TEXT NOT NULL,
        from_status TEXT NOT NULL,
        to_status TEXT NOT NULL,
        worker_id TEXT NOT NULL DEFAULT '',
        progress_completed INTEGER NOT NULL,
        progress_total INTEGER NOT NULL,
        progress_step TEXT NOT NULL DEFAULT '',
        detail_code TEXT NOT NULL DEFAULT '',
        detail_message TEXT NOT NULL DEFAULT '',
        occurred_at TEXT NOT NULL,
        previous_event_hash TEXT NOT NULL,
        event_hash TEXT NOT NULL UNIQUE,
        UNIQUE(job_id, job_revision),
        CHECK(event_schema = 'PFIV025DurableJobEventV1'),
        CHECK(from_status = '' OR from_status IN ('queued', 'running', 'retrying', 'succeeded', 'failed', 'cancelled', 'dead_letter')),
        CHECK(to_status IN ('queued', 'running', 'retrying', 'succeeded', 'failed', 'cancelled', 'dead_letter')),
        CHECK(job_revision >= 0),
        CHECK(progress_completed >= 0),
        CHECK(progress_total >= 0),
        CHECK(progress_completed <= progress_total)
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_durable_job_events_stream
    ON durable_job_events(job_id, event_id)
    """,
    """
    CREATE TRIGGER IF NOT EXISTS durable_job_events_no_update
    BEFORE UPDATE ON durable_job_events
    BEGIN
        SELECT RAISE(ABORT, 'durable_job_events is append-only');
    END
    """,
    """
    CREATE TRIGGER IF NOT EXISTS durable_job_events_no_delete
    BEFORE DELETE ON durable_job_events
    BEGIN
        SELECT RAISE(ABORT, 'durable_job_events is append-only');
    END
    """,
)

_OBSERVABILITY_MIGRATION_STATEMENTS = (
    """
    CREATE TABLE IF NOT EXISTS durable_job_trace_contexts (
        job_id TEXT PRIMARY KEY REFERENCES durable_jobs(job_id) ON DELETE RESTRICT,
        trace_schema TEXT NOT NULL,
        trace_id TEXT NOT NULL,
        initial_span_id TEXT NOT NULL,
        parent_span_id TEXT NOT NULL DEFAULT '',
        source_hash TEXT NOT NULL,
        data_hash TEXT NOT NULL,
        formula_hash TEXT NOT NULL,
        parameter_hash TEXT NOT NULL,
        read_model_hash TEXT NOT NULL,
        cache_key TEXT NOT NULL,
        impact_scope_json TEXT NOT NULL,
        cache_fallback_used INTEGER NOT NULL DEFAULT 0,
        external_network_calls INTEGER NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL,
        CHECK(trace_schema = 'PFIV025DurableJobTraceV1'),
        CHECK(length(trace_id) = 32 AND trace_id NOT GLOB '*[^0-9a-f]*'),
        CHECK(length(initial_span_id) = 16 AND initial_span_id NOT GLOB '*[^0-9a-f]*'),
        CHECK(parent_span_id = '' OR (length(parent_span_id) = 16 AND parent_span_id NOT GLOB '*[^0-9a-f]*')),
        CHECK(cache_fallback_used IN (0, 1)),
        CHECK(external_network_calls = 0)
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_durable_job_trace_id
    ON durable_job_trace_contexts(trace_id, job_id)
    """,
    """
    CREATE TABLE IF NOT EXISTS durable_job_spans (
        span_row_id INTEGER PRIMARY KEY AUTOINCREMENT,
        span_schema TEXT NOT NULL,
        trace_id TEXT NOT NULL,
        span_id TEXT NOT NULL UNIQUE,
        parent_span_id TEXT NOT NULL DEFAULT '',
        job_id TEXT NOT NULL REFERENCES durable_jobs(job_id) ON DELETE RESTRICT,
        job_revision INTEGER NOT NULL,
        event_type TEXT NOT NULL,
        stage TEXT NOT NULL,
        status TEXT NOT NULL,
        started_at TEXT NOT NULL,
        ended_at TEXT NOT NULL,
        duration_ms INTEGER NOT NULL,
        error_code TEXT NOT NULL DEFAULT '',
        impact_scope_json TEXT NOT NULL,
        retry_count INTEGER NOT NULL DEFAULT 0,
        cache_fallback_used INTEGER NOT NULL DEFAULT 0,
        UNIQUE(job_id, job_revision),
        CHECK(span_schema = 'PFIV025DurableJobSpanV1'),
        CHECK(length(trace_id) = 32 AND trace_id NOT GLOB '*[^0-9a-f]*'),
        CHECK(length(span_id) = 16 AND span_id NOT GLOB '*[^0-9a-f]*'),
        CHECK(parent_span_id = '' OR (length(parent_span_id) = 16 AND parent_span_id NOT GLOB '*[^0-9a-f]*')),
        CHECK(duration_ms >= 0),
        CHECK(retry_count >= 0),
        CHECK(cache_fallback_used IN (0, 1))
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_durable_job_spans_trace
    ON durable_job_spans(trace_id, span_row_id)
    """,
    """
    CREATE TABLE IF NOT EXISTS durable_job_logs (
        log_id INTEGER PRIMARY KEY AUTOINCREMENT,
        log_schema TEXT NOT NULL,
        trace_id TEXT NOT NULL,
        span_id TEXT NOT NULL,
        job_id TEXT NOT NULL REFERENCES durable_jobs(job_id) ON DELETE RESTRICT,
        job_revision INTEGER NOT NULL,
        level TEXT NOT NULL,
        event TEXT NOT NULL,
        stage TEXT NOT NULL,
        message TEXT NOT NULL,
        fields_json TEXT NOT NULL,
        occurred_at TEXT NOT NULL,
        previous_log_hash TEXT NOT NULL,
        log_hash TEXT NOT NULL UNIQUE,
        UNIQUE(job_id, job_revision),
        CHECK(log_schema = 'PFIV025DurableJobStructuredLogV1'),
        CHECK(length(trace_id) = 32 AND trace_id NOT GLOB '*[^0-9a-f]*'),
        CHECK(length(span_id) = 16 AND span_id NOT GLOB '*[^0-9a-f]*'),
        CHECK(level IN ('info', 'warning', 'error'))
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_durable_job_logs_trace
    ON durable_job_logs(trace_id, log_id)
    """,
    """
    CREATE TRIGGER IF NOT EXISTS durable_job_trace_contexts_no_update
    BEFORE UPDATE ON durable_job_trace_contexts
    BEGIN
        SELECT RAISE(ABORT, 'durable_job_trace_contexts is immutable');
    END
    """,
    """
    CREATE TRIGGER IF NOT EXISTS durable_job_trace_contexts_no_delete
    BEFORE DELETE ON durable_job_trace_contexts
    BEGIN
        SELECT RAISE(ABORT, 'durable_job_trace_contexts is immutable');
    END
    """,
    """
    CREATE TRIGGER IF NOT EXISTS durable_job_spans_no_update
    BEFORE UPDATE ON durable_job_spans
    BEGIN
        SELECT RAISE(ABORT, 'durable_job_spans is append-only');
    END
    """,
    """
    CREATE TRIGGER IF NOT EXISTS durable_job_spans_no_delete
    BEFORE DELETE ON durable_job_spans
    BEGIN
        SELECT RAISE(ABORT, 'durable_job_spans is append-only');
    END
    """,
    """
    CREATE TRIGGER IF NOT EXISTS durable_job_logs_no_update
    BEFORE UPDATE ON durable_job_logs
    BEGIN
        SELECT RAISE(ABORT, 'durable_job_logs is append-only');
    END
    """,
    """
    CREATE TRIGGER IF NOT EXISTS durable_job_logs_no_delete
    BEFORE DELETE ON durable_job_logs
    BEGIN
        SELECT RAISE(ABORT, 'durable_job_logs is append-only');
    END
    """,
)

_MIGRATION_PLAN = (
    (JOB_MIGRATION_ID, _MIGRATION_STATEMENTS),
    (JOB_OBSERVABILITY_MIGRATION_ID, _OBSERVABILITY_MIGRATION_STATEMENTS),
)


class SQLiteDurableJobStore:
    """SQLite durable-job store with revision CAS and opaque leases.

    A database path is mandatory so tests and callers cannot silently touch the
    canonical private PFI database. Workers receive the raw lease token once;
    SQLite stores only its job-bound SHA-256 digest.
    """

    def __init__(
        self,
        db_path: Path | str,
        *,
        backup_dir: Path | str | None = None,
        token_factory: Callable[[], str] | None = None,
    ) -> None:
        if not str(db_path).strip():
            raise ValueError("db_path is required")
        self.db_path = Path(db_path).expanduser()
        self.backup_dir = (
            Path(backup_dir).expanduser()
            if backup_dir is not None
            else self.db_path.parent / "migration_backups"
        )
        self._token_factory = token_factory or _TOKEN_FACTORY
        self.initialize()

    def initialize(self) -> Path:
        parent_existed = self.db_path.parent.exists()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        if not parent_existed:
            os.chmod(self.db_path.parent, 0o700)

        with _INITIALIZE_LOCK:
            lock_path = self.db_path.with_name(f".{self.db_path.name}.v025-jobs-migration.lock")
            with _exclusive_file_lock(lock_path):
                existed_before = self.db_path.is_file() and self.db_path.stat().st_size > 0
                applied = self._applied_migration_ids() if existed_before else set()
                pending = [migration_id for migration_id, _statements in _MIGRATION_PLAN if migration_id not in applied]
                if existed_before and pending:
                    self._backup_before_migration(pending[-1])
                if pending:
                    self._apply_migrations(pending)
        os.chmod(self.db_path, 0o600)
        return self.db_path

    def enqueue(
        self,
        *,
        job_type: str,
        idempotency_key: str,
        payload: Mapping[str, object] | None = None,
        max_attempts: int = 3,
        contains_financial_facts: bool = False,
        trace_id: str = "",
        parent_span_id: str = "",
        observability_context: Mapping[str, object] | None = None,
        available_at: datetime | None = None,
        now: datetime | None = None,
    ) -> dict[str, object]:
        job_type = _name(job_type, "job_type")
        idempotency_key = _text(idempotency_key, "idempotency_key", limit=256)
        max_attempts = _bounded_int(max_attempts, "max_attempts", minimum=1, maximum=100)
        if not isinstance(contains_financial_facts, bool):
            raise TypeError("contains_financial_facts must be a boolean")
        payload_json = _canonical_payload(payload or {})
        payload_hash = hashlib.sha256(payload_json.encode("utf-8")).hexdigest()
        resolved_trace_id = (
            validate_trace_id(trace_id) if str(trace_id or "").strip() else new_trace_id()
        )
        resolved_parent_span_id = validate_span_id(parent_span_id, allow_empty=True)
        initial_span_id = new_span_id()
        normalized_observability = normalize_observability_context(observability_context)
        resolved_now = _utc(now)
        resolved_available_at = _utc(available_at or resolved_now)
        job_id = _job_id(job_type, idempotency_key)

        with self._transaction(immediate=True) as conn:
            existing = conn.execute(
                "SELECT * FROM durable_jobs WHERE job_type = ? AND idempotency_key = ?",
                (job_type, idempotency_key),
            ).fetchone()
            if existing is not None:
                immutable_match = (
                    str(existing["payload_hash"]) == payload_hash
                    and int(existing["max_attempts"]) == max_attempts
                    and bool(existing["contains_financial_facts"]) is bool(contains_financial_facts)
                )
                if not immutable_match:
                    raise JobConflictError(
                        "idempotency key already exists with different immutable inputs"
                    )
                return {"created": False, "job": self._project(conn, existing)}

            conn.execute(
                """
                INSERT INTO durable_jobs(
                    job_id, schema_version, job_type, idempotency_key,
                    payload_json, payload_hash, contains_financial_facts,
                    status, revision, attempt_count, max_attempts, available_at,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 'queued', 0, 0, ?, ?, ?, ?)
                """,
                (
                    job_id,
                    JOB_LIFECYCLE_SCHEMA,
                    job_type,
                    idempotency_key,
                    payload_json,
                    payload_hash,
                    int(bool(contains_financial_facts)),
                    max_attempts,
                    _iso(resolved_available_at),
                    _iso(resolved_now),
                    _iso(resolved_now),
                ),
            )
            row = self._job_row(conn, job_id)
            self._insert_trace_context(
                conn,
                row,
                trace_id=resolved_trace_id,
                initial_span_id=initial_span_id,
                parent_span_id=resolved_parent_span_id,
                context=normalized_observability,
                created_at=resolved_now,
            )
            self._append_event(
                conn,
                row,
                event_type="queued",
                from_status="",
                worker_id="",
                detail_code="",
                detail_message="",
                occurred_at=resolved_now,
            )
            return {"created": True, "job": self._project(conn, row)}

    def claim(
        self,
        *,
        job_type: str,
        worker_id: str,
        lease_seconds: int = 60,
        now: datetime | None = None,
    ) -> dict[str, object]:
        job_type = _name(job_type, "job_type")
        worker_id = _name(worker_id, "worker_id")
        lease_seconds = _bounded_int(lease_seconds, "lease_seconds", minimum=1, maximum=3600)
        resolved_now = _utc(now)

        with self._transaction(immediate=True) as conn:
            recovered = self._recover_expired_in_transaction(conn, now=resolved_now, job_type=job_type)
            placeholders = ",".join("?" for _ in CLAIMABLE_STATUSES)
            row = conn.execute(
                f"""
                SELECT * FROM durable_jobs
                WHERE job_type = ?
                  AND status IN ({placeholders})
                  AND available_at <= ?
                  AND attempt_count < max_attempts
                ORDER BY available_at, created_at, job_id
                LIMIT 1
                """,
                (job_type, *sorted(CLAIMABLE_STATUSES), _iso(resolved_now)),
            ).fetchone()
            if row is None:
                return {
                    "claimed": False,
                    "job_type": job_type,
                    "worker_id": worker_id,
                    "recovered_job_ids": [item["job_id"] for item in recovered],
                }

            token = _text(self._token_factory(), "lease_token", limit=512)
            expires_at = resolved_now + timedelta(seconds=lease_seconds)
            updated = self._cas_mutation(
                conn,
                row,
                updates={
                    "status": "running",
                    "attempt_count": int(row["attempt_count"]) + 1,
                    "lease_owner": worker_id,
                    "lease_token_hash": _lease_token_hash(str(row["job_id"]), token),
                    "lease_expires_at": _iso(expires_at),
                    "heartbeat_at": _iso(resolved_now),
                    "finished_at": None,
                },
                event_type="claimed",
                worker_id=worker_id,
                detail_code="",
                detail_message="",
                occurred_at=resolved_now,
            )
            return {
                "claimed": True,
                "job": self._project(conn, updated),
                "payload": json.loads(str(updated["payload_json"])),
                "lease": {
                    "owner": worker_id,
                    "token": token,
                    "expires_at": str(updated["lease_expires_at"]),
                    "revision": int(updated["revision"]),
                },
                "recovered_job_ids": [item["job_id"] for item in recovered],
            }

    def heartbeat(
        self,
        job_id: str,
        *,
        worker_id: str,
        lease_token: str,
        expected_revision: int,
        lease_seconds: int = 60,
        now: datetime | None = None,
    ) -> dict[str, object]:
        worker_id = _name(worker_id, "worker_id")
        lease_seconds = _bounded_int(lease_seconds, "lease_seconds", minimum=1, maximum=3600)
        resolved_now = _utc(now)
        with self._transaction(immediate=True) as conn:
            row = self._job_row(conn, job_id)
            self._require_revision(row, expected_revision)
            self._require_active_lease(row, worker_id, lease_token, resolved_now)
            updated = self._cas_mutation(
                conn,
                row,
                updates={
                    "heartbeat_at": _iso(resolved_now),
                    "lease_expires_at": _iso(resolved_now + timedelta(seconds=lease_seconds)),
                },
                event_type="heartbeat",
                worker_id=worker_id,
                detail_code="",
                detail_message="",
                occurred_at=resolved_now,
            )
            return self._project(conn, updated)

    def record_progress(
        self,
        job_id: str,
        *,
        worker_id: str,
        lease_token: str,
        expected_revision: int,
        completed_units: int,
        total_units: int,
        step: str,
        now: datetime | None = None,
    ) -> dict[str, object]:
        worker_id = _name(worker_id, "worker_id")
        completed_units = _bounded_int(completed_units, "completed_units", minimum=0, maximum=10**12)
        total_units = _bounded_int(total_units, "total_units", minimum=1, maximum=10**12)
        if completed_units > total_units:
            raise ValueError("completed_units must not exceed total_units")
        step = redact_log_text(_text(step, "step", limit=160), limit=160)
        resolved_now = _utc(now)

        with self._transaction(immediate=True) as conn:
            row = self._job_row(conn, job_id)
            self._require_revision(row, expected_revision)
            self._require_active_lease(row, worker_id, lease_token, resolved_now)
            current_total = int(row["progress_total"])
            current_completed = int(row["progress_completed"])
            current_step = str(row["progress_step"])
            if current_total not in {0, total_units}:
                raise JobLifecycleError("total_units is immutable after the first progress event")
            if completed_units < current_completed:
                raise JobLifecycleError("completed_units must be monotonic")
            if completed_units == current_completed and step == current_step:
                raise JobLifecycleError("progress event must advance units or record a new real step")

            updated = self._cas_mutation(
                conn,
                row,
                updates={
                    "progress_completed": completed_units,
                    "progress_total": total_units,
                    "progress_step": step,
                },
                event_type="progressed",
                worker_id=worker_id,
                detail_code="",
                detail_message="",
                occurred_at=resolved_now,
            )
            return self._project(conn, updated)

    def succeed(
        self,
        job_id: str,
        *,
        worker_id: str,
        lease_token: str,
        expected_revision: int,
        result_uri: str = "",
        now: datetime | None = None,
    ) -> dict[str, object]:
        worker_id = _name(worker_id, "worker_id")
        result_uri = _artifact_uri(result_uri)
        resolved_now = _utc(now)
        with self._transaction(immediate=True) as conn:
            row = self._job_row(conn, job_id)
            self._require_revision(row, expected_revision)
            self._require_active_lease(row, worker_id, lease_token, resolved_now)
            if int(row["progress_total"]) <= 0 or int(row["progress_completed"]) != int(row["progress_total"]):
                raise JobTransitionError(
                    "job cannot succeed until real completed_units equals total_units"
                )
            review_state = (
                "pending_human_review" if bool(row["contains_financial_facts"]) else "not_applicable"
            )
            updated = self._cas_mutation(
                conn,
                row,
                updates={
                    "status": "succeeded",
                    "lease_owner": None,
                    "lease_token_hash": None,
                    "lease_expires_at": None,
                    "result_uri": result_uri,
                    "result_review_state": review_state,
                    "error_code": "",
                    "error_message": "",
                    "finished_at": _iso(resolved_now),
                },
                event_type="succeeded",
                worker_id=worker_id,
                detail_code="",
                detail_message="",
                occurred_at=resolved_now,
            )
            return self._project(conn, updated)

    def fail(
        self,
        job_id: str,
        *,
        worker_id: str,
        lease_token: str,
        expected_revision: int,
        error_code: str,
        error_message: str,
        retryable: bool,
        retry_delay_seconds: int = 0,
        now: datetime | None = None,
    ) -> dict[str, object]:
        worker_id = _name(worker_id, "worker_id")
        error_code = _code(error_code, "error_code")
        error_message = _detail(error_message, "error_message")
        retry_delay_seconds = _bounded_int(
            retry_delay_seconds,
            "retry_delay_seconds",
            minimum=0,
            maximum=86_400,
        )
        resolved_now = _utc(now)
        with self._transaction(immediate=True) as conn:
            row = self._job_row(conn, job_id)
            self._require_revision(row, expected_revision)
            self._require_active_lease(row, worker_id, lease_token, resolved_now)
            exhausted = int(row["attempt_count"]) >= int(row["max_attempts"])
            if retryable and not exhausted:
                status = "retrying"
                event_type = "retry_scheduled"
                available_at = _iso(resolved_now + timedelta(seconds=retry_delay_seconds))
                finished_at = None
            elif retryable:
                status = "dead_letter"
                event_type = "dead_lettered"
                available_at = str(row["available_at"])
                finished_at = _iso(resolved_now)
            else:
                status = "failed"
                event_type = "failed"
                available_at = str(row["available_at"])
                finished_at = _iso(resolved_now)
            updated = self._cas_mutation(
                conn,
                row,
                updates={
                    "status": status,
                    "available_at": available_at,
                    "lease_owner": None,
                    "lease_token_hash": None,
                    "lease_expires_at": None,
                    "error_code": error_code,
                    "error_message": error_message,
                    "finished_at": finished_at,
                },
                event_type=event_type,
                worker_id=worker_id,
                detail_code=error_code,
                detail_message=error_message,
                occurred_at=resolved_now,
            )
            return self._project(conn, updated)

    def cancel(
        self,
        job_id: str,
        *,
        expected_revision: int,
        reason: str,
        now: datetime | None = None,
    ) -> dict[str, object]:
        reason = _detail(reason, "reason")
        resolved_now = _utc(now)
        with self._transaction(immediate=True) as conn:
            row = self._job_row(conn, job_id)
            self._require_revision(row, expected_revision)
            if str(row["status"]) in TERMINAL_STATUSES:
                raise JobTransitionError(f"cannot cancel terminal job in {row['status']} state")
            updated = self._cas_mutation(
                conn,
                row,
                updates={
                    "status": "cancelled",
                    "lease_owner": None,
                    "lease_token_hash": None,
                    "lease_expires_at": None,
                    "cancel_reason": reason,
                    "finished_at": _iso(resolved_now),
                },
                event_type="cancelled",
                worker_id="",
                detail_code="CANCELLED",
                detail_message=reason,
                occurred_at=resolved_now,
            )
            return self._project(conn, updated)

    def dead_letter(
        self,
        job_id: str,
        *,
        expected_revision: int,
        reason_code: str,
        reason: str,
        now: datetime | None = None,
    ) -> dict[str, object]:
        reason_code = _code(reason_code, "reason_code")
        reason = _detail(reason, "reason")
        resolved_now = _utc(now)
        with self._transaction(immediate=True) as conn:
            row = self._job_row(conn, job_id)
            self._require_revision(row, expected_revision)
            if str(row["status"]) == "running":
                raise JobTransitionError("running jobs must be failed or cancelled before dead-lettering")
            if str(row["status"]) in {"succeeded", "cancelled", "dead_letter"}:
                raise JobTransitionError(f"cannot dead-letter job in {row['status']} state")
            updated = self._cas_mutation(
                conn,
                row,
                updates={
                    "status": "dead_letter",
                    "error_code": reason_code,
                    "error_message": reason,
                    "finished_at": _iso(resolved_now),
                },
                event_type="dead_lettered",
                worker_id="",
                detail_code=reason_code,
                detail_message=reason,
                occurred_at=resolved_now,
            )
            return self._project(conn, updated)

    def recover_expired_leases(
        self,
        *,
        job_type: str = "",
        now: datetime | None = None,
    ) -> dict[str, object]:
        normalized_job_type = _name(job_type, "job_type") if job_type else ""
        resolved_now = _utc(now)
        with self._transaction(immediate=True) as conn:
            recovered = self._recover_expired_in_transaction(
                conn,
                now=resolved_now,
                job_type=normalized_job_type,
            )
            return {
                "recovered_count": len(recovered),
                "jobs": recovered,
                "observed_at": _iso(resolved_now),
            }

    def get(self, job_id: str) -> dict[str, object]:
        with self._transaction() as conn:
            return self._project(conn, self._job_row(conn, job_id))

    def list_jobs(
        self,
        *,
        status: str = "",
        limit: int = 50,
    ) -> list[dict[str, object]]:
        limit = _bounded_int(limit, "limit", minimum=1, maximum=500)
        normalized_status = str(status or "").strip()
        if normalized_status and normalized_status not in JOB_STATUSES:
            raise ValueError("status is not a durable job lifecycle state")
        with self._transaction() as conn:
            if normalized_status:
                rows = conn.execute(
                    """
                    SELECT * FROM durable_jobs
                    WHERE status = ?
                    ORDER BY updated_at DESC, job_id
                    LIMIT ?
                    """,
                    (normalized_status, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT * FROM durable_jobs
                    ORDER BY updated_at DESC, job_id
                    LIMIT ?
                    """,
                    (limit,),
                ).fetchall()
            return [self._project(conn, row) for row in rows]

    def list_events(self, job_id: str, *, after_event_id: int = 0) -> list[dict[str, object]]:
        after_event_id = _bounded_int(after_event_id, "after_event_id", minimum=0, maximum=2**63 - 1)
        with self._transaction() as conn:
            self._job_row(conn, job_id)
            rows = conn.execute(
                """
                SELECT e.*, s.trace_id AS obs_trace_id, s.span_id AS obs_span_id,
                       s.parent_span_id AS obs_parent_span_id, s.stage AS obs_stage,
                       s.started_at AS obs_started_at, s.ended_at AS obs_ended_at,
                       s.duration_ms AS obs_duration_ms
                FROM durable_job_events AS e
                LEFT JOIN durable_job_spans AS s
                  ON s.job_id = e.job_id AND s.job_revision = e.job_revision
                WHERE e.job_id = ? AND e.event_id > ?
                ORDER BY e.event_id
                """,
                (job_id, after_event_id),
            ).fetchall()
            return [_event_projection(row) for row in rows]

    def list_logs(self, job_id: str, *, after_log_id: int = 0) -> list[dict[str, object]]:
        after_log_id = _bounded_int(after_log_id, "after_log_id", minimum=0, maximum=2**63 - 1)
        with self._transaction() as conn:
            self._job_row(conn, job_id)
            rows = conn.execute(
                """
                SELECT * FROM durable_job_logs
                WHERE job_id = ? AND log_id > ?
                ORDER BY log_id
                """,
                (job_id, after_log_id),
            ).fetchall()
            return [_log_projection(row) for row in rows]

    def get_observability(self, job_id: str) -> dict[str, object]:
        with self._transaction() as conn:
            job = self._project(conn, self._job_row(conn, job_id))
            events = conn.execute(
                """
                SELECT e.*, s.trace_id AS obs_trace_id, s.span_id AS obs_span_id,
                       s.parent_span_id AS obs_parent_span_id, s.stage AS obs_stage,
                       s.started_at AS obs_started_at, s.ended_at AS obs_ended_at,
                       s.duration_ms AS obs_duration_ms
                FROM durable_job_events AS e
                LEFT JOIN durable_job_spans AS s
                  ON s.job_id = e.job_id AND s.job_revision = e.job_revision
                WHERE e.job_id = ?
                ORDER BY e.event_id
                """,
                (job_id,),
            ).fetchall()
            logs = conn.execute(
                "SELECT * FROM durable_job_logs WHERE job_id = ? ORDER BY log_id",
                (job_id,),
            ).fetchall()
            return {
                "schema": "PFIV025DurableJobObservabilityProjectionV1",
                "job": job,
                "events": [_event_projection(row) for row in events],
                "logs": [_log_projection(row) for row in logs],
            }

    def integrity(self) -> dict[str, object]:
        with self._transaction() as conn:
            foreign_key_rows = conn.execute("PRAGMA foreign_key_check").fetchall()
            integrity_result = str(conn.execute("PRAGMA integrity_check").fetchone()[0])
            journal_mode = str(conn.execute("PRAGMA journal_mode").fetchone()[0]).upper()
            foreign_keys = int(conn.execute("PRAGMA foreign_keys").fetchone()[0])
            busy_timeout = int(conn.execute("PRAGMA busy_timeout").fetchone()[0])
            synchronous = int(conn.execute("PRAGMA synchronous").fetchone()[0])
            sqlite_runtime = str(conn.execute("SELECT sqlite_version()").fetchone()[0])
            migration_ids = [
                str(row["migration_id"])
                for row in conn.execute(
                    "SELECT migration_id FROM pfi_schema_migrations ORDER BY migration_id"
                )
            ]
            expected_migrations = {migration_id for migration_id, _statements in _MIGRATION_PLAN}
            migration_count = len(expected_migrations.intersection(migration_ids))
            job_count = int(conn.execute("SELECT COUNT(*) FROM durable_jobs").fetchone()[0])
            event_count = int(conn.execute("SELECT COUNT(*) FROM durable_job_events").fetchone()[0])
            trace_count = int(
                conn.execute("SELECT COUNT(*) FROM durable_job_trace_contexts").fetchone()[0]
            )
            span_count = int(conn.execute("SELECT COUNT(*) FROM durable_job_spans").fetchone()[0])
            log_count = int(conn.execute("SELECT COUNT(*) FROM durable_job_logs").fetchone()[0])
            observability_consistent = (
                trace_count == job_count and span_count == event_count and log_count == event_count
            )
        return {
            "status": "pass"
            if (
                integrity_result == "ok"
                and not foreign_key_rows
                and migration_count == len(_MIGRATION_PLAN)
                and observability_consistent
            )
            else "fail",
            "python_sqlite3_module_version": _python_sqlite3_module_version(),
            "sqlite_runtime_version": sqlite_runtime,
            "journal_mode": journal_mode,
            "wal_enabled": journal_mode == "WAL",
            "foreign_keys": foreign_keys == 1,
            "busy_timeout_ms": busy_timeout,
            "synchronous": synchronous,
            "explicit_transactions": True,
            "rollback_on_error": True,
            "migration_id": JOB_MIGRATION_ID,
            "observability_migration_id": JOB_OBSERVABILITY_MIGRATION_ID,
            "migration_ids": migration_ids,
            "migration_count": migration_count,
            "integrity_check": integrity_result,
            "foreign_key_check": "pass" if not foreign_key_rows else "fail",
            "foreign_key_issue_count": len(foreign_key_rows),
            "job_count": job_count,
            "event_count": event_count,
            "trace_count": trace_count,
            "span_count": span_count,
            "log_count": log_count,
            "observability_consistent": observability_consistent,
        }

    def schema_snapshot(self) -> dict[str, object]:
        with self._transaction() as conn:
            tables: dict[str, list[str]] = {}
            for table in (
                "durable_jobs",
                "durable_job_events",
                "durable_job_trace_contexts",
                "durable_job_spans",
                "durable_job_logs",
                "pfi_schema_migrations",
            ):
                tables[table] = [str(row["name"]) for row in conn.execute(f"PRAGMA table_info({table})")]
            triggers = [
                str(row["name"])
                for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'trigger' AND name LIKE 'durable_job_%' ORDER BY name"
                )
            ]
            migration_ids = [
                str(row["migration_id"])
                for row in conn.execute(
                    "SELECT migration_id FROM pfi_schema_migrations ORDER BY migration_id"
                )
            ]
        return {
            "migration_id": JOB_MIGRATION_ID,
            "observability_migration_id": JOB_OBSERVABILITY_MIGRATION_ID,
            "migration_ids": migration_ids,
            "tables": tables,
            "triggers": triggers,
        }

    def _recover_expired_in_transaction(
        self,
        conn: sqlite3.Connection,
        *,
        now: datetime,
        job_type: str = "",
    ) -> list[dict[str, object]]:
        query = "SELECT * FROM durable_jobs WHERE status = 'running' AND lease_expires_at <= ?"
        params: list[object] = [_iso(now)]
        if job_type:
            query += " AND job_type = ?"
            params.append(job_type)
        query += " ORDER BY lease_expires_at, job_id"
        rows = conn.execute(query, tuple(params)).fetchall()
        recovered: list[dict[str, object]] = []
        for row in rows:
            exhausted = int(row["attempt_count"]) >= int(row["max_attempts"])
            status = "dead_letter" if exhausted else "retrying"
            event_type = "dead_lettered" if exhausted else "lease_expired_requeued"
            code = "LEASE_EXPIRED"
            message = "worker lease expired before a terminal result"
            updated = self._cas_mutation(
                conn,
                row,
                updates={
                    "status": status,
                    "available_at": _iso(now),
                    "lease_owner": None,
                    "lease_token_hash": None,
                    "lease_expires_at": None,
                    "error_code": code,
                    "error_message": message,
                    "finished_at": _iso(now) if exhausted else None,
                },
                event_type=event_type,
                worker_id="",
                detail_code=code,
                detail_message=message,
                occurred_at=now,
            )
            recovered.append(self._project(conn, updated))
        return recovered

    def _cas_mutation(
        self,
        conn: sqlite3.Connection,
        row: sqlite3.Row,
        *,
        updates: Mapping[str, object],
        event_type: str,
        worker_id: str,
        detail_code: str,
        detail_message: str,
        occurred_at: datetime,
    ) -> sqlite3.Row:
        allowed = {
            "status",
            "attempt_count",
            "available_at",
            "lease_owner",
            "lease_token_hash",
            "lease_expires_at",
            "heartbeat_at",
            "progress_completed",
            "progress_total",
            "progress_step",
            "result_uri",
            "result_review_state",
            "error_code",
            "error_message",
            "cancel_reason",
            "finished_at",
        }
        unknown = set(updates) - allowed
        if unknown:
            raise AssertionError(f"unsupported durable job columns: {sorted(unknown)}")
        old_revision = int(row["revision"])
        new_revision = old_revision + 1
        values = dict(updates)
        values["revision"] = new_revision
        values["updated_at"] = _iso(occurred_at)
        assignments = ", ".join(f"{column} = ?" for column in values)
        cursor = conn.execute(
            f"""
            UPDATE durable_jobs
            SET {assignments}
            WHERE job_id = ? AND revision = ? AND status = ?
            """,
            (*values.values(), str(row["job_id"]), old_revision, str(row["status"])),
        )
        if cursor.rowcount != 1:
            raise StaleRevisionError(
                f"CAS rejected job {row['job_id']} at revision {old_revision}"
            )
        updated = self._job_row(conn, str(row["job_id"]))
        self._append_event(
            conn,
            updated,
            event_type=event_type,
            from_status=str(row["status"]),
            worker_id=worker_id,
            detail_code=detail_code,
            detail_message=detail_message,
            occurred_at=occurred_at,
        )
        return updated

    def _append_event(
        self,
        conn: sqlite3.Connection,
        row: sqlite3.Row,
        *,
        event_type: str,
        from_status: str,
        worker_id: str,
        detail_code: str,
        detail_message: str,
        occurred_at: datetime,
    ) -> None:
        previous = conn.execute(
            "SELECT event_hash FROM durable_job_events WHERE job_id = ? ORDER BY event_id DESC LIMIT 1",
            (str(row["job_id"]),),
        ).fetchone()
        previous_hash = str(previous["event_hash"]) if previous is not None else ""
        redacted_detail = redact_log_text(detail_message)
        event_fields = {
            "event_schema": JOB_EVENT_SCHEMA,
            "job_id": str(row["job_id"]),
            "job_revision": int(row["revision"]),
            "event_type": _text(event_type, "event_type", limit=80),
            "from_status": from_status,
            "to_status": str(row["status"]),
            "worker_id": worker_id,
            "progress_completed": int(row["progress_completed"]),
            "progress_total": int(row["progress_total"]),
            "progress_step": str(row["progress_step"]),
            "detail_code": detail_code,
            "detail_message": redacted_detail,
            "occurred_at": _iso(occurred_at),
            "previous_event_hash": previous_hash,
        }
        event_hash = hashlib.sha256(
            json.dumps(
                event_fields,
                ensure_ascii=False,
                allow_nan=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        conn.execute(
            """
            INSERT INTO durable_job_events(
                event_schema, job_id, job_revision, event_type, from_status,
                to_status, worker_id, progress_completed, progress_total,
                progress_step, detail_code, detail_message, occurred_at,
                previous_event_hash, event_hash
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (*event_fields.values(), event_hash),
        )
        event_row = conn.execute(
            "SELECT * FROM durable_job_events WHERE job_id = ? AND job_revision = ?",
            (str(row["job_id"]), int(row["revision"])),
        ).fetchone()
        if event_row is None:
            raise JobLifecycleError("durable job event was not persisted")
        self._append_observability_event(conn, event_row)

    @staticmethod
    def _insert_trace_context(
        conn: sqlite3.Connection,
        row: sqlite3.Row,
        *,
        trace_id: str,
        initial_span_id: str,
        parent_span_id: str,
        context: Mapping[str, object],
        created_at: datetime,
    ) -> None:
        conn.execute(
            """
            INSERT INTO durable_job_trace_contexts(
                job_id, trace_schema, trace_id, initial_span_id, parent_span_id,
                source_hash, data_hash, formula_hash, parameter_hash,
                read_model_hash, cache_key, impact_scope_json,
                cache_fallback_used, external_network_calls, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(row["job_id"]),
                JOB_TRACE_SCHEMA,
                validate_trace_id(trace_id),
                validate_span_id(initial_span_id),
                validate_span_id(parent_span_id, allow_empty=True),
                str(context["source_hash"]),
                str(context["data_hash"]),
                str(context["formula_hash"]),
                str(context["parameter_hash"]),
                str(context["read_model_hash"]),
                str(context["cache_key"]),
                json.dumps(
                    list(context["impact_scope"]),
                    ensure_ascii=False,
                    allow_nan=False,
                    sort_keys=True,
                    separators=(",", ":"),
                ),
                int(bool(context["cache_fallback_used"])),
                int(context["external_network_calls"]),
                _iso(created_at),
            ),
        )

    @staticmethod
    def _append_observability_event(
        conn: sqlite3.Connection,
        event_row: sqlite3.Row,
    ) -> None:
        job_id = str(event_row["job_id"])
        revision = int(event_row["job_revision"])
        trace = conn.execute(
            "SELECT * FROM durable_job_trace_contexts WHERE job_id = ?",
            (job_id,),
        ).fetchone()
        if trace is None:
            raise JobLifecycleError("durable job trace context is unavailable")
        previous_span = conn.execute(
            """
            SELECT span_id, ended_at
            FROM durable_job_spans
            WHERE job_id = ?
            ORDER BY span_row_id DESC
            LIMIT 1
            """,
            (job_id,),
        ).fetchone()
        trace_id = validate_trace_id(trace["trace_id"])
        span_id = (
            validate_span_id(trace["initial_span_id"])
            if revision == 0
            else deterministic_span_id(
                trace_id,
                job_id,
                revision,
                str(event_row["event_type"]),
            )
        )
        parent_span_id = (
            str(previous_span["span_id"])
            if previous_span is not None
            else validate_span_id(trace["parent_span_id"], allow_empty=True)
        )
        ended_at = str(event_row["occurred_at"])
        started_at = str(previous_span["ended_at"]) if previous_span is not None else ended_at
        duration_ms = max(
            0,
            int((_parse_utc(ended_at) - _parse_utc(started_at)).total_seconds() * 1000),
        )
        stage = redact_log_text(
            str(event_row["progress_step"] or event_row["event_type"]),
            limit=120,
        )
        impact_scope = json.loads(str(trace["impact_scope_json"]))
        retry_count = int(
            conn.execute(
                """
                SELECT COUNT(*)
                FROM durable_job_events
                WHERE job_id = ?
                  AND job_revision <= ?
                  AND event_type IN ('retry_scheduled', 'lease_expired_requeued')
                """,
                (job_id, revision),
            ).fetchone()[0]
        )
        cache_fallback_used = bool(trace["cache_fallback_used"])
        conn.execute(
            """
            INSERT INTO durable_job_spans(
                span_schema, trace_id, span_id, parent_span_id, job_id,
                job_revision, event_type, stage, status, started_at, ended_at,
                duration_ms, error_code, impact_scope_json, retry_count,
                cache_fallback_used
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                JOB_SPAN_SCHEMA,
                trace_id,
                span_id,
                parent_span_id,
                job_id,
                revision,
                str(event_row["event_type"]),
                stage,
                str(event_row["to_status"]),
                started_at,
                ended_at,
                duration_ms,
                str(event_row["detail_code"]),
                str(trace["impact_scope_json"]),
                retry_count,
                int(cache_fallback_used),
            ),
        )

        fields = redact_log_fields(
            {
                "source_hash": str(trace["source_hash"]),
                "data_hash": str(trace["data_hash"]),
                "formula_hash": str(trace["formula_hash"]),
                "parameter_hash": str(trace["parameter_hash"]),
                "read_model_hash": str(trace["read_model_hash"]),
                "cache_key": str(trace["cache_key"]),
                "impact_scope": impact_scope,
                "from_status": str(event_row["from_status"]),
                "to_status": str(event_row["to_status"]),
                "progress_completed": int(event_row["progress_completed"]),
                "progress_total": int(event_row["progress_total"]),
                "retry_count": retry_count,
                "cache_fallback_used": cache_fallback_used,
                "external_network_calls": int(trace["external_network_calls"]),
                "stage_duration_ms": duration_ms,
            }
        )
        fields_json = json.dumps(
            fields,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        previous_log = conn.execute(
            "SELECT log_hash FROM durable_job_logs WHERE job_id = ? ORDER BY log_id DESC LIMIT 1",
            (job_id,),
        ).fetchone()
        previous_log_hash = str(previous_log["log_hash"]) if previous_log is not None else ""
        event_type = str(event_row["event_type"])
        level = (
            "error"
            if str(event_row["to_status"]) in {"failed", "dead_letter"}
            else "warning"
            if event_type in {"retry_scheduled", "lease_expired_requeued", "cancelled"}
            else "info"
        )
        message = redact_log_text(str(event_row["detail_message"] or event_type))
        log_fields = {
            "log_schema": JOB_LOG_SCHEMA,
            "trace_id": trace_id,
            "span_id": span_id,
            "job_id": job_id,
            "job_revision": revision,
            "level": level,
            "event": event_type,
            "stage": stage,
            "message": message,
            "fields_json": fields_json,
            "occurred_at": ended_at,
            "previous_log_hash": previous_log_hash,
        }
        log_hash = hashlib.sha256(
            json.dumps(
                log_fields,
                ensure_ascii=False,
                allow_nan=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        conn.execute(
            """
            INSERT INTO durable_job_logs(
                log_schema, trace_id, span_id, job_id, job_revision, level,
                event, stage, message, fields_json, occurred_at,
                previous_log_hash, log_hash
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (*log_fields.values(), log_hash),
        )

    @staticmethod
    def _require_revision(row: sqlite3.Row, expected_revision: int) -> None:
        expected_revision = _bounded_int(
            expected_revision,
            "expected_revision",
            minimum=0,
            maximum=2**63 - 1,
        )
        if int(row["revision"]) != expected_revision:
            raise StaleRevisionError(
                f"expected revision {expected_revision}, current revision is {row['revision']}"
            )

    @staticmethod
    def _require_active_lease(
        row: sqlite3.Row,
        worker_id: str,
        lease_token: str,
        now: datetime,
    ) -> None:
        lease_token = _text(lease_token, "lease_token", limit=512)
        if str(row["status"]) != "running":
            raise JobTransitionError(f"job is {row['status']}, not running")
        if str(row["lease_owner"] or "") != worker_id:
            raise LeaseConflictError("worker does not own this lease")
        expected_hash = _lease_token_hash(str(row["job_id"]), lease_token)
        if not hmac.compare_digest(str(row["lease_token_hash"] or ""), expected_hash):
            raise LeaseConflictError("lease token does not match")
        expires_at = _parse_utc(str(row["lease_expires_at"] or ""))
        if expires_at <= now:
            raise LeaseConflictError("lease has expired and must be recovered before reuse")

    @staticmethod
    def _job_row(conn: sqlite3.Connection, job_id: str) -> sqlite3.Row:
        job_id = _text(job_id, "job_id", limit=128)
        row = conn.execute("SELECT * FROM durable_jobs WHERE job_id = ?", (job_id,)).fetchone()
        if row is None:
            raise KeyError(job_id)
        return row

    @staticmethod
    def _project(conn: sqlite3.Connection, row: sqlite3.Row) -> dict[str, object]:
        latest_event = conn.execute(
            "SELECT event_id, event_type FROM durable_job_events WHERE job_id = ? ORDER BY event_id DESC LIMIT 1",
            (str(row["job_id"]),),
        ).fetchone()
        trace = conn.execute(
            "SELECT * FROM durable_job_trace_contexts WHERE job_id = ?",
            (str(row["job_id"]),),
        ).fetchone()
        latest_span = conn.execute(
            """
            SELECT * FROM durable_job_spans
            WHERE job_id = ?
            ORDER BY span_row_id DESC
            LIMIT 1
            """,
            (str(row["job_id"]),),
        ).fetchone()
        log_count = int(
            conn.execute(
                "SELECT COUNT(*) FROM durable_job_logs WHERE job_id = ?",
                (str(row["job_id"]),),
            ).fetchone()[0]
        )
        total = int(row["progress_total"])
        completed = int(row["progress_completed"])
        progress_percent = round(completed * 100 / total, 2) if total else None
        impact_scope = json.loads(str(trace["impact_scope_json"])) if trace is not None else []
        return {
            "schema": JOB_LIFECYCLE_SCHEMA,
            "job_id": str(row["job_id"]),
            "job_type": str(row["job_type"]),
            "idempotency_key": str(row["idempotency_key"]),
            "payload_hash": str(row["payload_hash"]),
            "contains_financial_facts": bool(row["contains_financial_facts"]),
            "status": str(row["status"]),
            "revision": int(row["revision"]),
            "attempt_count": int(row["attempt_count"]),
            "max_attempts": int(row["max_attempts"]),
            "available_at": str(row["available_at"]),
            "lease": {
                "owner": str(row["lease_owner"] or ""),
                "expires_at": str(row["lease_expires_at"] or ""),
                "heartbeat_at": str(row["heartbeat_at"] or ""),
                "token_exposed": False,
            },
            "progress": {
                "completed_units": completed,
                "total_units": total,
                "percent": progress_percent,
                "step": str(row["progress_step"]),
                "source": "durable_job_events",
                "timer_based": False,
            },
            "trace": {
                "schema": str(trace["trace_schema"]) if trace is not None else "",
                "trace_id": str(trace["trace_id"]) if trace is not None else "",
                "span_id": str(latest_span["span_id"]) if latest_span is not None else "",
                "parent_span_id": (
                    str(latest_span["parent_span_id"]) if latest_span is not None else ""
                ),
                "stage": str(latest_span["stage"]) if latest_span is not None else "",
                "started_at": (
                    str(latest_span["started_at"]) if latest_span is not None else ""
                ),
                "ended_at": str(latest_span["ended_at"]) if latest_span is not None else "",
                "duration_ms": (
                    int(latest_span["duration_ms"]) if latest_span is not None else 0
                ),
            },
            "observability": {
                "source_hash": str(trace["source_hash"]) if trace is not None else "not_loaded",
                "data_hash": str(trace["data_hash"]) if trace is not None else "not_loaded",
                "formula_hash": (
                    str(trace["formula_hash"]) if trace is not None else "not_loaded"
                ),
                "parameter_hash": (
                    str(trace["parameter_hash"]) if trace is not None else "not_loaded"
                ),
                "read_model_hash": (
                    str(trace["read_model_hash"]) if trace is not None else "not_loaded"
                ),
                "cache_key": str(trace["cache_key"]) if trace is not None else "not_loaded",
                "impact_scope": impact_scope,
                "retry_count": (
                    int(latest_span["retry_count"]) if latest_span is not None else 0
                ),
                "cache_fallback_used": (
                    bool(trace["cache_fallback_used"]) if trace is not None else False
                ),
                "external_network_calls": (
                    int(trace["external_network_calls"]) if trace is not None else 0
                ),
                "structured_log_count": log_count,
            },
            "result": {
                "artifact_uri": str(row["result_uri"]),
                "review_state": str(row["result_review_state"]),
                "publishable": False,
            },
            "error": {
                "code": str(row["error_code"]),
                "message": str(row["error_message"]),
            },
            "cancel_reason": str(row["cancel_reason"]),
            "created_at": str(row["created_at"]),
            "updated_at": str(row["updated_at"]),
            "finished_at": str(row["finished_at"] or ""),
            "latest_event_id": int(latest_event["event_id"]) if latest_event is not None else None,
            "latest_event_type": str(latest_event["event_type"]) if latest_event is not None else "",
        }

    @contextmanager
    def _transaction(self, *, immediate: bool = False) -> Iterator[sqlite3.Connection]:
        with operational_store_guard(self.db_path):
            conn = sqlite3.connect(self.db_path, timeout=30, isolation_level=None)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute("PRAGMA busy_timeout = 30000")
            conn.execute("PRAGMA journal_mode = DELETE")
            conn.execute("PRAGMA synchronous = FULL")
            conn.execute("BEGIN IMMEDIATE" if immediate else "BEGIN")
            try:
                yield conn
            except Exception:
                conn.rollback()
                raise
            else:
                conn.commit()
            finally:
                conn.close()

    def _applied_migration_ids(self) -> set[str]:
        uri = f"{self.db_path.resolve().as_uri()}?mode=ro"
        with operational_store_guard(self.db_path):
            conn: sqlite3.Connection | None = None
            try:
                conn = sqlite3.connect(uri, uri=True, timeout=5)
                conn.row_factory = sqlite3.Row
                table = conn.execute(
                    "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'pfi_schema_migrations'"
                ).fetchone()
                if table is None:
                    return set()
                return {
                    str(row["migration_id"])
                    for row in conn.execute("SELECT migration_id FROM pfi_schema_migrations")
                }
            except sqlite3.DatabaseError:
                return set()
            finally:
                if conn is not None:
                    conn.close()

    def _backup_before_migration(self, migration_id: str) -> Path:
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        os.chmod(self.backup_dir, 0o700)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        target = self.backup_dir / f"pre-{migration_id}-{stamp}.sqlite"
        suffix = 1
        while target.exists():
            target = self.backup_dir / f"pre-{migration_id}-{stamp}-{suffix}.sqlite"
            suffix += 1
        with operational_store_guard(self.db_path):
            source = sqlite3.connect(
                f"{self.db_path.resolve().as_uri()}?mode=ro", uri=True, timeout=30
            )
            destination = sqlite3.connect(target)
            try:
                source.backup(destination)
                destination.commit()
            finally:
                destination.close()
                source.close()
        os.chmod(target, 0o600)
        return target

    def _apply_migrations(self, pending: list[str]) -> None:
        planned = {migration_id: statements for migration_id, statements in _MIGRATION_PLAN}
        unknown = set(pending) - set(planned)
        if unknown:
            raise JobLifecycleError(f"unknown durable-job migrations: {sorted(unknown)}")
        with operational_store_guard(self.db_path):
            conn = sqlite3.connect(self.db_path, timeout=30, isolation_level=None)
            conn.row_factory = sqlite3.Row
            try:
                conn.execute("PRAGMA foreign_keys = ON")
                conn.execute("PRAGMA busy_timeout = 30000")
                conn.execute("PRAGMA journal_mode = DELETE")
                conn.execute("PRAGMA synchronous = FULL")
                conn.execute("BEGIN IMMEDIATE")
                for migration_id, _statements in _MIGRATION_PLAN:
                    if migration_id not in pending:
                        continue
                    for statement in planned[migration_id]:
                        conn.execute(statement)
                    if migration_id == JOB_OBSERVABILITY_MIGRATION_ID:
                        self._backfill_observability(conn)
                    conn.execute(
                        "INSERT INTO pfi_schema_migrations(migration_id, applied_at) VALUES (?, ?)",
                        (migration_id, _iso(_utc(None))),
                    )
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                conn.close()

    def _backfill_observability(self, conn: sqlite3.Connection) -> None:
        jobs = conn.execute("SELECT * FROM durable_jobs ORDER BY created_at, job_id").fetchall()
        for row in jobs:
            job_id = str(row["job_id"])
            trace_id = deterministic_trace_id(job_id)
            trace_exists = conn.execute(
                "SELECT 1 FROM durable_job_trace_contexts WHERE job_id = ?",
                (job_id,),
            ).fetchone()
            if trace_exists is None:
                initial_span_id = deterministic_span_id(trace_id, job_id, 0, "queued")
                self._insert_trace_context(
                    conn,
                    row,
                    trace_id=trace_id,
                    initial_span_id=initial_span_id,
                    parent_span_id="",
                    context=normalize_observability_context(None),
                    created_at=_parse_utc(str(row["created_at"])),
                )
            events = conn.execute(
                "SELECT * FROM durable_job_events WHERE job_id = ? ORDER BY event_id",
                (job_id,),
            ).fetchall()
            for event in events:
                span_exists = conn.execute(
                    """
                    SELECT 1 FROM durable_job_spans
                    WHERE job_id = ? AND job_revision = ?
                    """,
                    (job_id, int(event["job_revision"])),
                ).fetchone()
                if span_exists is None:
                    self._append_observability_event(conn, event)


def _event_projection(row: sqlite3.Row) -> dict[str, object]:
    projection = {
        "schema": str(row["event_schema"]),
        "event_id": int(row["event_id"]),
        "job_id": str(row["job_id"]),
        "job_revision": int(row["job_revision"]),
        "event_type": str(row["event_type"]),
        "from_status": str(row["from_status"]),
        "to_status": str(row["to_status"]),
        "worker_id": str(row["worker_id"]),
        "progress": {
            "completed_units": int(row["progress_completed"]),
            "total_units": int(row["progress_total"]),
            "step": str(row["progress_step"]),
            "timer_based": False,
        },
        "detail": {
            "code": str(row["detail_code"]),
            "message": str(row["detail_message"]),
        },
        "occurred_at": str(row["occurred_at"]),
        "previous_event_hash": str(row["previous_event_hash"]),
        "event_hash": str(row["event_hash"]),
    }
    if "obs_trace_id" in row.keys() and row["obs_trace_id"] is not None:
        projection["trace"] = {
            "trace_id": str(row["obs_trace_id"]),
            "span_id": str(row["obs_span_id"]),
            "parent_span_id": str(row["obs_parent_span_id"]),
            "stage": str(row["obs_stage"]),
            "started_at": str(row["obs_started_at"]),
            "ended_at": str(row["obs_ended_at"]),
            "duration_ms": int(row["obs_duration_ms"]),
        }
    return projection


def _log_projection(row: sqlite3.Row) -> dict[str, object]:
    try:
        fields = json.loads(str(row["fields_json"]))
    except (TypeError, ValueError) as exc:
        raise JobLifecycleError("persisted structured log fields are invalid") from exc
    if not isinstance(fields, dict):
        raise JobLifecycleError("persisted structured log fields must be an object")
    return {
        "schema": str(row["log_schema"]),
        "log_id": int(row["log_id"]),
        "trace_id": str(row["trace_id"]),
        "span_id": str(row["span_id"]),
        "job_id": str(row["job_id"]),
        "job_revision": int(row["job_revision"]),
        "level": str(row["level"]),
        "event": str(row["event"]),
        "stage": str(row["stage"]),
        "message": str(row["message"]),
        "fields": fields,
        "occurred_at": str(row["occurred_at"]),
        "previous_log_hash": str(row["previous_log_hash"]),
        "log_hash": str(row["log_hash"]),
    }


def _job_id(job_type: str, idempotency_key: str) -> str:
    digest = hashlib.sha256(f"{job_type}\x1f{idempotency_key}".encode("utf-8")).hexdigest()
    return f"job-{digest}"


def _lease_token_hash(job_id: str, token: str) -> str:
    return hashlib.sha256(f"{job_id}\x1f{token}".encode("utf-8")).hexdigest()


def _canonical_payload(payload: Mapping[str, object]) -> str:
    if not isinstance(payload, Mapping):
        raise TypeError("payload must be a JSON object")
    try:
        return json.dumps(
            dict(payload),
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    except (TypeError, ValueError) as exc:
        raise ValueError("payload must be finite canonical JSON") from exc


def _python_sqlite3_module_version() -> str:
    # CPython deprecates sqlite3.version in 3.12, but the Task Pack explicitly
    # requires recording both the wrapper and SQLite runtime versions. Keep the
    # compatibility read isolated and warning-free until that field disappears.
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        return str(getattr(sqlite3, "version", "stdlib"))


def _utc(value: datetime | None) -> datetime:
    resolved = value or datetime.now(timezone.utc)
    if resolved.tzinfo is None or resolved.utcoffset() is None:
        raise ValueError("timestamps must be timezone-aware")
    return resolved.astimezone(timezone.utc)


def _iso(value: datetime) -> str:
    return _utc(value).isoformat(timespec="microseconds")


def _parse_utc(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise JobLifecycleError("persisted lease timestamp is invalid") from exc
    return _utc(parsed)


def _text(value: object, field: str, *, limit: int) -> str:
    normalized = str(value or "").strip()
    if not normalized:
        raise ValueError(f"{field} is required")
    if "\x00" in normalized or len(normalized) > limit:
        raise ValueError(f"{field} is invalid or exceeds {limit} characters")
    return normalized


def _name(value: object, field: str) -> str:
    normalized = _text(value, field, limit=128)
    if not _NAME_PATTERN.fullmatch(normalized):
        raise ValueError(f"{field} must use letters, digits, dot, colon, underscore, or hyphen")
    return normalized


def _code(value: object, field: str) -> str:
    normalized = _text(value, field, limit=64).upper()
    if not _CODE_PATTERN.fullmatch(normalized):
        raise ValueError(f"{field} must be an uppercase machine-readable code")
    return normalized


def _detail(value: object, field: str) -> str:
    normalized = _text(value, field, limit=1000)
    return redact_log_text(normalized)


def _artifact_uri(value: object) -> str:
    normalized = str(value or "").strip()
    if not normalized:
        return ""
    if len(normalized) > 500 or "\x00" in normalized:
        raise ValueError("result_uri is invalid")
    if not normalized.startswith(_ALLOWED_ARTIFACT_PREFIXES):
        raise ValueError("result_uri must use artifact://, private://, or report://")
    return normalized


def _bounded_int(value: object, field: str, *, minimum: int, maximum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field} must be an integer")
    if value < minimum or value > maximum:
        raise ValueError(f"{field} must be between {minimum} and {maximum}")
    return value


@contextmanager
def _exclusive_file_lock(path: Path) -> Iterator[None]:
    descriptor = os.open(path, os.O_RDWR | os.O_CREAT, 0o600)
    try:
        os.chmod(path, 0o600)
        fcntl.flock(descriptor, fcntl.LOCK_EX)
        yield
    finally:
        fcntl.flock(descriptor, fcntl.LOCK_UN)
        os.close(descriptor)
