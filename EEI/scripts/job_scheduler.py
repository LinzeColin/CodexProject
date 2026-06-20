#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

try:
    from db_tools import database_url
except ModuleNotFoundError:  # pragma: no cover - used when imported as scripts.job_scheduler
    from scripts.db_tools import database_url

try:
    from load_curated_ingestion_anchors import load_anchors
except ModuleNotFoundError:  # pragma: no cover - used when imported as scripts.job_scheduler
    from scripts.load_curated_ingestion_anchors import load_anchors

try:
    from apps.api.app.scoring import candidate_score_metrics
except ModuleNotFoundError:  # pragma: no cover - used when imported from packaged contexts.
    from ..apps.api.app.scoring import candidate_score_metrics

DEFAULT_LEASE_TTL_SECONDS = 900
DEFAULT_MAX_ATTEMPTS = 5
DEFAULT_DEAD_LETTER_AFTER_ATTEMPTS = 5
DEFAULT_RETRY_BACKOFF_SECONDS = 30
ACTIVE_REFRESH_MODULES = [
    "business_empire",
    "group_structure",
    "business_segments",
    "supply_chain",
    "capital_network",
    "ma_transactions",
    "control_relationships",
    "policy_environment",
    "strategic_signals",
    "watchlist",
    "evidence_center",
    "model_center",
    "data_center",
]


class SchedulerError(RuntimeError):
    pass


def connect_job_database() -> psycopg.Connection:
    return psycopg.connect(database_url(), connect_timeout=5, row_factory=dict_row)


def utc_now() -> datetime:
    return datetime.now(UTC)


def jsonable(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.astimezone(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, dict):
        return {str(key): jsonable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [jsonable(item) for item in value]
    return value


def job_payload(row: dict[str, Any] | None) -> dict[str, Any] | None:
    if row is None:
        return None
    return jsonable(dict(row))


def enqueue_job(
    *,
    job_type: str,
    idempotency_key: str,
    payload: dict[str, Any] | None = None,
    priority: int = 100,
    scheduled_for: datetime | None = None,
    max_attempts: int = DEFAULT_MAX_ATTEMPTS,
    dead_letter_after_attempts: int = DEFAULT_DEAD_LETTER_AFTER_ATTEMPTS,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    scheduled_at = scheduled_for or utc_now()
    with connect_job_database() as connection:
        row = connection.execute(
            """
            INSERT INTO background_jobs(
              job_type, idempotency_key, payload, priority, status, scheduled_for,
              max_attempts, dead_letter_after_attempts, metadata
            )
            VALUES (%s, %s, %s, %s, 'queued', %s, %s, %s, %s)
            ON CONFLICT (job_type, idempotency_key) DO UPDATE SET
              updated_at = background_jobs.updated_at
            RETURNING *
            """,
            (
                job_type,
                idempotency_key,
                Jsonb(payload or {}),
                priority,
                scheduled_at,
                max_attempts,
                dead_letter_after_attempts,
                Jsonb(metadata or {}),
            ),
        ).fetchone()
        return job_payload(row) or {}


def record_dead_letter(
    connection: psycopg.Connection,
    job: dict[str, Any],
    *,
    error_class: str,
    error_message: str,
) -> None:
    connection.execute(
        """
        INSERT INTO dead_letter_jobs(
          job_id, final_attempt_no, error_class, error_message, payload, metadata
        )
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (job_id) DO UPDATE SET
          dead_lettered_at = now(),
          final_attempt_no = EXCLUDED.final_attempt_no,
          error_class = EXCLUDED.error_class,
          error_message = EXCLUDED.error_message,
          payload = EXCLUDED.payload,
          metadata = EXCLUDED.metadata
        """,
        (
            job["id"],
            job["attempt_count"],
            error_class,
            error_message,
            Jsonb(job["payload"] or {}),
            Jsonb(job["metadata"] or {}),
        ),
    )


def recover_expired_leases(*, now: datetime | None = None) -> dict[str, int]:
    recovered = 0
    dead_lettered = 0
    timestamp = now or utc_now()
    with connect_job_database() as connection:
        expired_jobs = connection.execute(
            """
            SELECT *
            FROM background_jobs
            WHERE status = 'running'
              AND lease_expires_at IS NOT NULL
              AND lease_expires_at <= %s
            FOR UPDATE
            """,
            (timestamp,),
        ).fetchall()
        for job in expired_jobs:
            terminal = int(job["attempt_count"]) >= int(job["dead_letter_after_attempts"])
            if terminal:
                connection.execute(
                    """
                    UPDATE background_jobs
                    SET status = 'dead_letter',
                        lease_owner = NULL,
                        lease_token = NULL,
                        lease_expires_at = NULL,
                        last_error_class = 'lease_expired',
                        last_error_message = 'Worker lease expired after retry cap.',
                        updated_at = %s,
                        finished_at = %s
                    WHERE id = %s
                    """,
                    (timestamp, timestamp, job["id"]),
                )
                connection.execute(
                    """
                    UPDATE background_job_attempts
                    SET status = 'expired',
                        finished_at = %s,
                        error_class = 'lease_expired',
                        error_message = 'Worker lease expired after retry cap.'
                    WHERE job_id = %s
                      AND lease_token = %s
                      AND status = 'running'
                    """,
                    (timestamp, job["id"], job["lease_token"]),
                )
                record_dead_letter(
                    connection,
                    job,
                    error_class="lease_expired",
                    error_message="Worker lease expired after retry cap.",
                )
                dead_lettered += 1
            else:
                connection.execute(
                    """
                    UPDATE background_jobs
                    SET status = 'queued',
                        lease_owner = NULL,
                        lease_token = NULL,
                        lease_expires_at = NULL,
                        scheduled_for = %s,
                        last_error_class = 'lease_expired',
                        last_error_message = 'Worker lease expired and job was requeued.',
                        updated_at = %s
                    WHERE id = %s
                    """,
                    (timestamp, timestamp, job["id"]),
                )
                connection.execute(
                    """
                    UPDATE background_job_attempts
                    SET status = 'expired',
                        finished_at = %s,
                        error_class = 'lease_expired',
                        error_message = 'Worker lease expired and job was requeued.'
                    WHERE job_id = %s
                      AND lease_token = %s
                      AND status = 'running'
                    """,
                    (timestamp, job["id"], job["lease_token"]),
                )
                recovered += 1
    return {"recovered": recovered, "dead_lettered": dead_lettered}


def lease_next_job(
    *,
    worker_id: str,
    job_type: str | None = None,
    lease_ttl_seconds: int = DEFAULT_LEASE_TTL_SECONDS,
    now: datetime | None = None,
) -> dict[str, Any] | None:
    timestamp = now or utc_now()
    recover_expired_leases(now=timestamp)
    lease_token = uuid4()
    lease_expires_at = timestamp + timedelta(seconds=lease_ttl_seconds)
    job_type_filter = "AND job_type = %s" if job_type else ""
    params: list[Any] = [timestamp]
    if job_type:
        params.append(job_type)
    with connect_job_database() as connection:
        row = connection.execute(
            f"""
            WITH candidate AS (
              SELECT id
              FROM background_jobs
              WHERE status = 'queued'
                AND scheduled_for <= %s
                {job_type_filter}
              ORDER BY priority ASC, scheduled_for ASC, created_at ASC
              LIMIT 1
              FOR UPDATE SKIP LOCKED
            )
            UPDATE background_jobs
            SET status = 'running',
                attempt_count = attempt_count + 1,
                lease_owner = %s,
                lease_token = %s,
                lease_expires_at = %s,
                heartbeat_at = %s,
                updated_at = %s
            WHERE id = (SELECT id FROM candidate)
            RETURNING *
            """,
            (*params, worker_id, lease_token, lease_expires_at, timestamp, timestamp),
        ).fetchone()
        if row is None:
            return None
        connection.execute(
            """
            INSERT INTO background_job_attempts(
              job_id, attempt_no, worker_id, lease_token, status, started_at, heartbeat_at
            )
            VALUES (%s, %s, %s, %s, 'running', %s, %s)
            """,
            (
                row["id"],
                row["attempt_count"],
                worker_id,
                lease_token,
                timestamp,
                timestamp,
            ),
        )
        return job_payload(row)


def require_running_job(
    connection: psycopg.Connection,
    *,
    job_id: UUID | str,
    lease_token: UUID | str,
) -> dict[str, Any]:
    row = connection.execute(
        """
        SELECT *
        FROM background_jobs
        WHERE id = %s
          AND lease_token = %s
          AND status = 'running'
        FOR UPDATE
        """,
        (job_id, lease_token),
    ).fetchone()
    if row is None:
        raise SchedulerError("No running job matches the lease token")
    return row


def heartbeat_job(
    *,
    job_id: UUID | str,
    lease_token: UUID | str,
    worker_id: str,
    lease_ttl_seconds: int = DEFAULT_LEASE_TTL_SECONDS,
    now: datetime | None = None,
) -> dict[str, Any]:
    timestamp = now or utc_now()
    lease_expires_at = timestamp + timedelta(seconds=lease_ttl_seconds)
    with connect_job_database() as connection:
        job = require_running_job(connection, job_id=job_id, lease_token=lease_token)
        if job["lease_owner"] != worker_id:
            raise SchedulerError("Worker does not own the running lease")
        row = connection.execute(
            """
            UPDATE background_jobs
            SET heartbeat_at = %s,
                lease_expires_at = %s,
                updated_at = %s
            WHERE id = %s
            RETURNING *
            """,
            (timestamp, lease_expires_at, timestamp, job_id),
        ).fetchone()
        connection.execute(
            """
            UPDATE background_job_attempts
            SET heartbeat_at = %s
            WHERE job_id = %s
              AND lease_token = %s
              AND status = 'running'
            """,
            (timestamp, job_id, lease_token),
        )
        return job_payload(row) or {}


def complete_job(
    *,
    job_id: UUID | str,
    lease_token: UUID | str,
    result: dict[str, Any] | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    timestamp = now or utc_now()
    with connect_job_database() as connection:
        require_running_job(connection, job_id=job_id, lease_token=lease_token)
        row = connection.execute(
            """
            UPDATE background_jobs
            SET status = 'succeeded',
                lease_owner = NULL,
                lease_token = NULL,
                lease_expires_at = NULL,
                updated_at = %s,
                finished_at = %s,
                metadata = metadata || %s
            WHERE id = %s
            RETURNING *
            """,
            (timestamp, timestamp, Jsonb({"result": result or {}}), job_id),
        ).fetchone()
        connection.execute(
            """
            UPDATE background_job_attempts
            SET status = 'succeeded',
                finished_at = %s,
                metadata = metadata || %s
            WHERE job_id = %s
              AND lease_token = %s
              AND status = 'running'
            """,
            (timestamp, Jsonb({"result": result or {}}), job_id, lease_token),
        )
        return job_payload(row) or {}


def release_job(
    *,
    job_id: UUID | str,
    lease_token: UUID | str,
    reason: str,
    now: datetime | None = None,
) -> dict[str, Any]:
    timestamp = now or utc_now()
    with connect_job_database() as connection:
        require_running_job(connection, job_id=job_id, lease_token=lease_token)
        row = connection.execute(
            """
            UPDATE background_jobs
            SET status = 'queued',
                lease_owner = NULL,
                lease_token = NULL,
                lease_expires_at = NULL,
                scheduled_for = %s,
                updated_at = %s,
                metadata = metadata || %s
            WHERE id = %s
            RETURNING *
            """,
            (timestamp, timestamp, Jsonb({"last_release_reason": reason}), job_id),
        ).fetchone()
        connection.execute(
            """
            UPDATE background_job_attempts
            SET status = 'released',
                finished_at = %s,
                metadata = metadata || %s
            WHERE job_id = %s
              AND lease_token = %s
              AND status = 'running'
            """,
            (timestamp, Jsonb({"reason": reason}), job_id, lease_token),
        )
        return job_payload(row) or {}


def fail_job(
    *,
    job_id: UUID | str,
    lease_token: UUID | str,
    error_class: str,
    error_message: str,
    retry_backoff_seconds: int = DEFAULT_RETRY_BACKOFF_SECONDS,
    now: datetime | None = None,
) -> dict[str, Any]:
    timestamp = now or utc_now()
    with connect_job_database() as connection:
        job = require_running_job(connection, job_id=job_id, lease_token=lease_token)
        terminal = int(job["attempt_count"]) >= min(
            int(job["max_attempts"]), int(job["dead_letter_after_attempts"])
        )
        next_status = "dead_letter" if terminal else "queued"
        next_scheduled_for = timestamp + timedelta(
            seconds=0 if terminal else retry_backoff_seconds * int(job["attempt_count"])
        )
        row = connection.execute(
            """
            UPDATE background_jobs
            SET status = %s,
                lease_owner = NULL,
                lease_token = NULL,
                lease_expires_at = NULL,
                scheduled_for = %s,
                last_error_class = %s,
                last_error_message = %s,
                updated_at = %s,
                finished_at = CASE WHEN %s THEN %s ELSE finished_at END
            WHERE id = %s
            RETURNING *
            """,
            (
                next_status,
                next_scheduled_for,
                error_class,
                error_message,
                timestamp,
                terminal,
                timestamp,
                job_id,
            ),
        ).fetchone()
        connection.execute(
            """
            UPDATE background_job_attempts
            SET status = 'failed',
                finished_at = %s,
                error_class = %s,
                error_message = %s
            WHERE job_id = %s
              AND lease_token = %s
              AND status = 'running'
            """,
            (timestamp, error_class, error_message, job_id, lease_token),
        )
        if terminal:
            record_dead_letter(
                connection,
                row,
                error_class=error_class,
                error_message=error_message,
            )
        return job_payload(row) or {}


def write_outbox_event(
    connection: psycopg.Connection,
    *,
    event_type: str,
    aggregate_type: str,
    aggregate_id: UUID | str | None,
    idempotency_key: str,
    payload: dict[str, Any],
    metadata: dict[str, Any] | None = None,
    priority: int = 100,
) -> dict[str, Any]:
    row = connection.execute(
        """
        INSERT INTO transactional_outbox(
          event_type, aggregate_type, aggregate_id, idempotency_key,
          payload, priority, status, metadata
        )
        VALUES (%s, %s, %s, %s, %s, %s, 'pending', %s)
        ON CONFLICT (idempotency_key) DO UPDATE SET
          updated_at = transactional_outbox.updated_at
        RETURNING *
        """,
        (
            event_type,
            aggregate_type,
            aggregate_id,
            idempotency_key,
            Jsonb(jsonable(payload)),
            priority,
            Jsonb(jsonable(metadata or {})),
        ),
    ).fetchone()
    return job_payload(row) or {}


def log_outbox_operation(
    connection: psycopg.Connection,
    *,
    event: dict[str, Any],
    result_status: str,
    reason: str,
    error: str | None = None,
) -> None:
    connection.execute(
        """
        INSERT INTO operation_logs(
          actor, action_type, object_type, object_id, old_value, new_value,
          diff, reason, result_status, error
        )
        VALUES (
          'system', 'dispatch_outbox_event', 'transactional_outbox',
          %s, %s, %s, %s, %s, %s, %s
        )
        """,
        (
            event["id"],
            Jsonb(jsonable(event)),
            Jsonb(jsonable(event)),
            Jsonb(
                {
                    "event_type": event["event_type"],
                    "attempt_count": event["attempt_count"],
                    "status": result_status,
                }
            ),
            reason,
            result_status,
            error,
        ),
    )


def lease_next_outbox_event(
    *,
    worker_id: str,
    event_type: str | None = None,
    lease_ttl_seconds: int = DEFAULT_LEASE_TTL_SECONDS,
    now: datetime | None = None,
) -> dict[str, Any] | None:
    timestamp = now or utc_now()
    lease_token = uuid4()
    lease_expires_at = timestamp + timedelta(seconds=lease_ttl_seconds)
    event_type_filter = "AND event_type = %s" if event_type else ""
    params: list[Any] = [timestamp]
    if event_type:
        params.append(event_type)
    with connect_job_database() as connection:
        row = connection.execute(
            f"""
            WITH candidate AS (
              SELECT id
              FROM transactional_outbox
              WHERE status IN ('pending','failed')
                AND scheduled_for <= %s
                {event_type_filter}
              ORDER BY priority ASC, scheduled_for ASC, created_at ASC
              LIMIT 1
              FOR UPDATE SKIP LOCKED
            )
            UPDATE transactional_outbox
            SET status = 'processing',
                attempt_count = attempt_count + 1,
                lease_owner = %s,
                lease_token = %s,
                lease_expires_at = %s,
                heartbeat_at = %s,
                updated_at = %s
            WHERE id = (SELECT id FROM candidate)
            RETURNING *
            """,
            (*params, worker_id, lease_token, lease_expires_at, timestamp, timestamp),
        ).fetchone()
        return job_payload(row)


def complete_outbox_event(
    *,
    event_id: UUID | str,
    lease_token: UUID | str,
    result: dict[str, Any] | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    timestamp = now or utc_now()
    with connect_job_database() as connection:
        event = connection.execute(
            """
            SELECT *
            FROM transactional_outbox
            WHERE id = %s
              AND lease_token = %s
              AND status = 'processing'
            FOR UPDATE
            """,
            (event_id, lease_token),
        ).fetchone()
        if event is None:
            raise SchedulerError("No processing outbox event matches the lease token")
        row = connection.execute(
            """
            UPDATE transactional_outbox
            SET status = 'dispatched',
                lease_owner = NULL,
                lease_token = NULL,
                lease_expires_at = NULL,
                updated_at = %s,
                dispatched_at = %s,
                metadata = metadata || %s
            WHERE id = %s
            RETURNING *
            """,
            (timestamp, timestamp, Jsonb({"dispatch_result": result or {}}), event_id),
        ).fetchone()
        log_outbox_operation(
            connection,
            event=dict(row),
            result_status="success",
            reason="Transactional outbox event dispatched",
        )
        return job_payload(row) or {}


def fail_outbox_event(
    *,
    event_id: UUID | str,
    lease_token: UUID | str,
    error_class: str,
    error_message: str,
    retry_backoff_seconds: int = DEFAULT_RETRY_BACKOFF_SECONDS,
    now: datetime | None = None,
) -> dict[str, Any]:
    timestamp = now or utc_now()
    with connect_job_database() as connection:
        event = connection.execute(
            """
            SELECT *
            FROM transactional_outbox
            WHERE id = %s
              AND lease_token = %s
              AND status = 'processing'
            FOR UPDATE
            """,
            (event_id, lease_token),
        ).fetchone()
        if event is None:
            raise SchedulerError("No processing outbox event matches the lease token")
        terminal = int(event["attempt_count"]) >= int(event["max_attempts"])
        next_status = "dead_letter" if terminal else "failed"
        next_scheduled_for = timestamp + timedelta(
            seconds=0 if terminal else retry_backoff_seconds * int(event["attempt_count"])
        )
        row = connection.execute(
            """
            UPDATE transactional_outbox
            SET status = %s,
                lease_owner = NULL,
                lease_token = NULL,
                lease_expires_at = NULL,
                scheduled_for = %s,
                last_error_class = %s,
                last_error_message = %s,
                updated_at = %s
            WHERE id = %s
            RETURNING *
            """,
            (
                next_status,
                next_scheduled_for,
                error_class,
                error_message,
                timestamp,
                event_id,
            ),
        ).fetchone()
        log_outbox_operation(
            connection,
            event=dict(row),
            result_status="failed" if not terminal else "dead_letter",
            reason="Transactional outbox event dispatch failed",
            error=f"{error_class}: {error_message}",
        )
        return job_payload(row) or {}


def dispatch_outbox_once(
    *,
    worker_id: str,
    event_type: str | None = None,
) -> dict[str, Any] | None:
    event = lease_next_outbox_event(worker_id=worker_id, event_type=event_type)
    if event is None:
        return None
    result = {
        "handler": "transactional_outbox",
        "handler_contract": "outbox-dispatch-v1",
        "event_type": event["event_type"],
        "aggregate_type": event["aggregate_type"],
        "aggregate_id": event["aggregate_id"],
        "acceptance_ids": event.get("metadata", {}).get("acceptance_ids", []),
    }
    try:
        return complete_outbox_event(
            event_id=event["id"],
            lease_token=event["lease_token"],
            result=result,
        )
    except Exception as exc:
        return fail_outbox_event(
            event_id=event["id"],
            lease_token=event["lease_token"],
            error_class=exc.__class__.__name__,
            error_message=str(exc),
        )


def log_score_recompute_operation(
    connection: psycopg.Connection,
    *,
    object_type: str,
    object_id: UUID | str | None,
    old_value: dict[str, Any] | None,
    new_value: dict[str, Any] | None,
    diff: dict[str, Any],
    reason: str,
    model_version: str | None,
    profile_version: str | None,
    result_status: str,
    error: str | None = None,
) -> None:
    connection.execute(
        """
        INSERT INTO operation_logs(
          actor, action_type, object_type, object_id, old_value, new_value, diff,
          reason, model_version, profile_version, result_status, error
        )
        VALUES (
          'system', 'execute_score_recompute', %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
        """,
        (
            object_type,
            object_id,
            Jsonb(jsonable(old_value or {})),
            Jsonb(jsonable(new_value or {})),
            Jsonb(jsonable(diff)),
            reason,
            model_version,
            profile_version,
            result_status,
            error,
        ),
    )


def log_data_snapshot_refresh_operation(
    connection: psycopg.Connection,
    *,
    object_type: str,
    object_id: UUID | str | None,
    old_value: dict[str, Any] | None,
    new_value: dict[str, Any] | None,
    diff: dict[str, Any],
    reason: str,
    model_version: str | None,
    profile_version: str | None,
    result_status: str,
    error: str | None = None,
) -> None:
    connection.execute(
        """
        INSERT INTO operation_logs(
          actor, action_type, object_type, object_id, old_value, new_value, diff,
          reason, model_version, profile_version, result_status, error
        )
        VALUES (
          'system', 'execute_data_snapshot_refresh', %s, %s, %s, %s, %s,
          %s, %s, %s, %s, %s
        )
        """,
        (
            object_type,
            object_id,
            Jsonb(jsonable(old_value or {})),
            Jsonb(jsonable(new_value or {})),
            Jsonb(jsonable(diff)),
            reason,
            model_version,
            profile_version,
            result_status,
            error,
        ),
    )


def log_curated_ingestion_refresh_operation(
    connection: psycopg.Connection,
    *,
    object_id: UUID | str | None,
    old_value: dict[str, Any] | None,
    new_value: dict[str, Any] | None,
    diff: dict[str, Any],
    reason: str,
    result_status: str,
    error: str | None = None,
) -> None:
    connection.execute(
        """
        INSERT INTO operation_logs(
          actor, action_type, object_type, object_id, old_value, new_value, diff,
          reason, result_status, error
        )
        VALUES (
          'system', 'execute_curated_ingestion_refresh', 'ingestion_run', %s,
          %s, %s, %s, %s, %s, %s
        )
        """,
        (
            object_id,
            Jsonb(jsonable(old_value or {})),
            Jsonb(jsonable(new_value or {})),
            Jsonb(jsonable(diff)),
            reason,
            result_status,
            error,
        ),
    )


def log_calibration_run_operation(
    connection: psycopg.Connection,
    *,
    object_id: UUID | str | None,
    old_value: dict[str, Any] | None,
    new_value: dict[str, Any] | None,
    diff: dict[str, Any],
    reason: str,
    model_version: str | None,
    profile_version: str | None,
    result_status: str,
    error: str | None = None,
) -> None:
    connection.execute(
        """
        INSERT INTO operation_logs(
          actor, action_type, object_type, object_id, old_value, new_value, diff,
          reason, model_version, profile_version, result_status, error
        )
        VALUES (
          'system', 'execute_calibration_run', 'calibration_run', %s,
          %s, %s, %s, %s, %s, %s, %s, %s
        )
        """,
        (
            object_id,
            Jsonb(jsonable(old_value or {})),
            Jsonb(jsonable(new_value or {})),
            Jsonb(jsonable(diff)),
            reason,
            model_version,
            profile_version,
            result_status,
            error,
        ),
    )


def current_data_snapshot_source_stats(connection: psycopg.Connection) -> dict[str, Any]:
    row = connection.execute(
        """
        SELECT
          (SELECT count(*)::int FROM source_documents) AS source_document_count,
          (SELECT count(*)::int FROM raw_source_snapshots) AS raw_snapshot_count,
          (SELECT count(*)::int FROM ingestion_evidence_chain) AS evidence_chain_count,
          (SELECT count(*)::int FROM relationship_fact_candidates) AS fact_candidate_count,
          (
            SELECT count(*)::int
            FROM relationship_fact_candidates
            WHERE publication_status = 'published'
          ) AS published_fact_candidate_count,
          (
            SELECT count(*)::int
            FROM relationship_fact_candidates
            WHERE source_threshold_met = false
          ) AS source_threshold_open_count,
          (
            SELECT count(*)::int
            FROM relationship_fact_candidates
            WHERE review_status <> 'human_verified'
          ) AS review_open_count,
          (
            SELECT count(*)::int
            FROM relationships
            WHERE status NOT IN ('superseded', 'revoked')
          ) AS relationship_count,
          (
            SELECT count(*)::int
            FROM events
            WHERE status NOT IN ('superseded', 'revoked')
          ) AS event_count,
          (SELECT max(retrieved_at) FROM source_documents) AS latest_source_retrieved_at,
          (SELECT max(observed_at) FROM source_documents) AS latest_source_observed_at,
          (
            SELECT max(observed_at)
            FROM relationships
            WHERE status NOT IN ('superseded', 'revoked')
          ) AS latest_relationship_observed_at,
          (
            SELECT id
            FROM ingestion_runs
            WHERE status = 'succeeded'
            ORDER BY finished_at DESC NULLS LAST, started_at DESC
            LIMIT 1
          ) AS latest_ingestion_run_id
        """
    ).fetchone()
    return jsonable(dict(row))


def data_snapshot_source_hash(
    *,
    scope: str,
    record_mode: str,
    source_stats: dict[str, Any],
) -> str:
    payload = json.dumps(
        jsonable(
            {
                "scope": scope,
                "record_mode": record_mode,
                "source_stats": source_stats,
            }
        ),
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def handle_curated_ingestion_refresh_job(job: dict[str, Any]) -> dict[str, Any]:
    payload = job.get("payload") or {}
    if payload.get("schema_version") != "curated-ingestion-refresh-job-v1":
        raise SchedulerError(
            "curated_ingestion_refresh payload schema_version must be "
            "curated-ingestion-refresh-job-v1"
        )
    record_mode = str(payload.get("record_mode") or "curated_official_fixture")
    if record_mode != "curated_official_fixture":
        raise SchedulerError("curated_ingestion_refresh only supports curated_official_fixture")
    reason = str(payload.get("reason") or "curated official ingestion refresh worker execution")
    counts = load_anchors()
    with connect_job_database() as connection:
        source_stats = current_data_snapshot_source_stats(connection)
        latest_ingestion_run_id = source_stats.get("latest_ingestion_run_id")
        result = {
            "handler": "curated_ingestion_refresh",
            "handler_contract": "curated-ingestion-refresh-worker-v1",
            "status": "completed",
            "job_id": job["id"],
            "record_mode": record_mode,
            "counts": counts,
            "source_stats": source_stats,
            "latest_ingestion_run_id": latest_ingestion_run_id,
            "fixture_policy": "curated_official_fixture is not live/full-text ingestion",
            "acceptance_ids": ["A202", "A206"],
        }
        outbox_event = write_outbox_event(
            connection,
            event_type="data.ingestion.completed",
            aggregate_type="ingestion_run",
            aggregate_id=latest_ingestion_run_id,
            idempotency_key=f"curated-ingestion-completed:{job['id']}",
            payload={
                "schema_version": "data-ingestion-event-v1",
                "job_id": job["id"],
                "record_mode": record_mode,
                "counts": counts,
                "source_stats": source_stats,
                "latest_ingestion_run_id": latest_ingestion_run_id,
                "fixture_policy": "curated_official_fixture is not live/full-text ingestion",
            },
            metadata={
                "task_ids": ["T1301", "T1304"],
                "acceptance_ids": ["A202", "A206"],
                "contract": "transactional-outbox-event-v1",
            },
        )
        result["outbox_event"] = outbox_event
        log_curated_ingestion_refresh_operation(
            connection,
            object_id=latest_ingestion_run_id,
            old_value=payload,
            new_value=result,
            diff={
                "record_mode": record_mode,
                "source_hash": counts.get("source_hash"),
                "relationship_fact_candidates": counts.get("relationship_fact_candidates"),
                "raw_snapshot_count": source_stats.get("raw_snapshot_count"),
            },
            reason=reason,
            result_status="success",
        )
        return jsonable(result)


def calibration_metrics(
    connection: psycopg.Connection,
    active_scoring_run_id: UUID | None,
) -> dict[str, Any]:
    fact_counts = connection.execute(
        """
        SELECT
          count(*)::int AS total,
          count(*) FILTER (WHERE source_threshold_met)::int AS source_threshold_met,
          count(*) FILTER (WHERE NOT source_threshold_met)::int AS source_threshold_open,
          count(*) FILTER (WHERE review_status = 'human_verified')::int AS human_verified,
          count(*) FILTER (WHERE publication_status = 'published')::int AS published
        FROM relationship_fact_candidates
        """
    ).fetchone()
    score_counts = connection.execute(
        """
        SELECT
          count(*)::int AS scored_objects,
          COALESCE(avg(coverage), 0)::float AS average_coverage,
          COALESCE(min(coverage), 0)::float AS minimum_coverage,
          COALESCE(avg(adjusted_score), 0)::float AS average_adjusted_score,
          count(*) FILTER (
            WHERE jsonb_array_length(
              CASE
                WHEN jsonb_typeof(missing_inputs) = 'array' THEN missing_inputs
                ELSE '[]'::jsonb
              END
            ) > 0
          )::int AS objects_with_missing_inputs
        FROM score_results
        WHERE (%s::uuid IS NULL OR scoring_run_id = %s)
        """,
        (active_scoring_run_id, active_scoring_run_id),
    ).fetchone()
    data_stats = current_data_snapshot_source_stats(connection)
    total = int(fact_counts["total"] or 0)
    return jsonable(
        {
            "relationship_fact_candidates": {
                "total": total,
                "source_threshold_met": int(fact_counts["source_threshold_met"] or 0),
                "source_threshold_open": int(fact_counts["source_threshold_open"] or 0),
                "human_verified": int(fact_counts["human_verified"] or 0),
                "published": int(fact_counts["published"] or 0),
            },
            "score_results": {
                "active_scoring_run_id": active_scoring_run_id,
                "scored_objects": int(score_counts["scored_objects"] or 0),
                "average_coverage": float(score_counts["average_coverage"] or 0),
                "minimum_coverage": float(score_counts["minimum_coverage"] or 0),
                "average_adjusted_score": float(score_counts["average_adjusted_score"] or 0),
                "objects_with_missing_inputs": int(
                    score_counts["objects_with_missing_inputs"] or 0
                ),
            },
            "data_coverage": {
                "source_document_count": data_stats.get("source_document_count", 0),
                "raw_snapshot_count": data_stats.get("raw_snapshot_count", 0),
                "evidence_chain_count": data_stats.get("evidence_chain_count", 0),
                "latest_ingestion_run_id": data_stats.get("latest_ingestion_run_id"),
            },
            "calibration_policy": {
                "cadence_days": 14,
                "coverage_warning_threshold": 80.0,
                "auto_activation_enabled": False,
            },
        }
    )


def handle_calibration_run_job(job: dict[str, Any]) -> dict[str, Any]:
    payload = job.get("payload") or {}
    if payload.get("schema_version") != "calibration-run-job-v1":
        raise SchedulerError(
            "calibration_run payload schema_version must be calibration-run-job-v1"
        )
    calibration_run_id = UUID(str(payload["calibration_run_id"]))
    expected_profile_id = UUID(str(payload["active_scoring_profile_version_id"]))
    reason = str(payload.get("reason") or "calibration run worker execution")
    with connect_job_database() as connection:
        calibration_run = connection.execute(
            """
            SELECT *
            FROM calibration_runs
            WHERE id = %s
            FOR UPDATE
            """,
            (calibration_run_id,),
        ).fetchone()
        if calibration_run is None:
            raise SchedulerError(f"Calibration run not found: {calibration_run_id}")
        if calibration_run["status"] in {"passed", "warning", "failed", "cancelled"}:
            return jsonable(
                {
                    "handler": "calibration_run",
                    "handler_contract": "calibration-run-worker-v1",
                    "status": "already_finished",
                    "calibration_run_id": calibration_run_id,
                    "calibration_status": calibration_run["status"],
                    "acceptance_ids": ["A206"],
                }
            )
        context = connection.execute(
            """
            SELECT
              aac.active_scoring_profile_version_id,
              aac.active_data_snapshot_id,
              aac.active_scoring_run_id,
              aac.refresh_generation,
              sp.profile_key,
              spv.version AS profile_version_number,
              sm.model_key,
              sm.version AS model_version_number
            FROM active_analysis_contexts aac
            JOIN scoring_profile_versions spv
              ON spv.id = aac.active_scoring_profile_version_id
            JOIN scoring_profiles sp ON sp.id = spv.profile_id
            JOIN scoring_models sm ON sm.id = spv.model_id
            WHERE aac.context_key = 'global'
            """
        ).fetchone()
        if context is None:
            raise SchedulerError("No active analysis context is available")
        if calibration_run["status"] == "scheduled":
            connection.execute(
                """
                UPDATE calibration_runs
                SET status = 'running', started_at = COALESCE(started_at, now())
                WHERE id = %s
                """,
                (calibration_run_id,),
            )
        active_scoring_run_id = context["active_scoring_run_id"]
        metrics = calibration_metrics(connection, active_scoring_run_id)
        profile_changed = context["active_scoring_profile_version_id"] != expected_profile_id
        scored_objects = int(metrics["score_results"]["scored_objects"])
        average_coverage = float(metrics["score_results"]["average_coverage"])
        source_threshold_open = int(
            metrics["relationship_fact_candidates"]["source_threshold_open"]
        )
        warnings = []
        if profile_changed:
            warnings.append("active_profile_changed_since_queue")
        if scored_objects == 0:
            warnings.append("no_active_score_results")
        if average_coverage < 80.0:
            warnings.append("average_coverage_below_threshold")
        if source_threshold_open > 0:
            warnings.append("source_threshold_open")
        calibration_status = "warning" if warnings else "passed"
        model_version = f"{context['model_key']}@{context['model_version_number']}"
        profile_version = f"{context['profile_key']}@{context['profile_version_number']}"
        drift_report = {
            "schema_version": "calibration-drift-report-v1",
            "warnings": warnings,
            "active_profile_changed_since_queue": profile_changed,
            "queued_active_scoring_profile_version_id": expected_profile_id,
            "current_active_scoring_profile_version_id": context[
                "active_scoring_profile_version_id"
            ],
            "active_data_snapshot_id": context["active_data_snapshot_id"],
            "active_scoring_run_id": active_scoring_run_id,
            "refresh_generation": context["refresh_generation"],
            "auto_activation_enabled": False,
        }
        proposal = {
            "schema_version": "calibration-proposal-v1",
            "proposal_status": "none",
            "proposed_changes": [],
            "reason": "MVP calibration reports drift only; parameter activation remains manual.",
        }
        updated_run = connection.execute(
            """
            UPDATE calibration_runs
            SET status = %s,
                metrics = %s,
                drift_report = %s,
                proposal = %s,
                proposal_status = 'none',
                started_at = COALESCE(started_at, now()),
                finished_at = now(),
                error = NULL
            WHERE id = %s
            RETURNING id, scheduled_for, cadence_days, data_snapshot_at,
                      profile_version_id, status, metrics, drift_report,
                      proposal, proposal_status, started_at, finished_at, error
            """,
            (
                calibration_status,
                Jsonb(jsonable(metrics)),
                Jsonb(jsonable(drift_report)),
                Jsonb(jsonable(proposal)),
                calibration_run_id,
            ),
        ).fetchone()
        result = {
            "handler": "calibration_run",
            "handler_contract": "calibration-run-worker-v1",
            "status": "completed",
            "job_id": job["id"],
            "calibration_run_id": calibration_run_id,
            "calibration_status": calibration_status,
            "metrics": metrics,
            "drift_report": drift_report,
            "proposal_status": "none",
            "model_version": model_version,
            "profile_version": profile_version,
            "acceptance_ids": ["A206"],
        }
        outbox_event = write_outbox_event(
            connection,
            event_type="calibration.run.completed",
            aggregate_type="calibration_run",
            aggregate_id=calibration_run_id,
            idempotency_key=f"calibration-run-completed:{calibration_run_id}",
            payload={
                "schema_version": "calibration-event-v1",
                "job_id": job["id"],
                "calibration_run_id": calibration_run_id,
                "calibration_status": calibration_status,
                "warnings": warnings,
                "proposal_status": "none",
                "auto_activation_enabled": False,
            },
            metadata={
                "task_ids": ["T1304", "T605", "T606"],
                "acceptance_ids": ["A090", "A091", "A092", "A206"],
                "contract": "transactional-outbox-event-v1",
            },
        )
        result["outbox_event"] = outbox_event
        log_calibration_run_operation(
            connection,
            object_id=calibration_run_id,
            old_value=dict(calibration_run),
            new_value=dict(updated_run),
            diff={
                "calibration_status": calibration_status,
                "warnings": warnings,
                "proposal_status": "none",
                "auto_activation_enabled": False,
            },
            reason=reason,
            model_version=model_version,
            profile_version=profile_version,
            result_status="success",
        )
        return jsonable(result)


def handle_data_snapshot_refresh_job(job: dict[str, Any]) -> dict[str, Any]:
    payload = job.get("payload") or {}
    if payload.get("schema_version") != "data-snapshot-refresh-job-v1":
        raise SchedulerError(
            "data_snapshot_refresh payload schema_version must be "
            "data-snapshot-refresh-job-v1"
        )
    expected_profile_id = UUID(str(payload["active_scoring_profile_version_id"]))
    expected_refresh_token = str(payload["refresh_token"])
    requested_generation = int(payload["refresh_generation"])
    scope = str(payload.get("scope") or "golden-vertical:nvidia")
    record_mode = str(payload.get("record_mode") or "curated_official_fixture")
    reason = str(payload.get("reason") or "data snapshot refresh worker execution")
    with connect_job_database() as connection:
        context = connection.execute(
            """
            SELECT
              aac.active_scoring_profile_version_id,
              aac.active_data_snapshot_id,
              aac.active_scoring_run_id,
              aac.refresh_token::text AS refresh_token,
              aac.refresh_generation,
              aac.status,
              sp.profile_key,
              spv.version AS profile_version_number,
              sm.model_key,
              sm.version AS model_version_number
            FROM active_analysis_contexts aac
            JOIN scoring_profile_versions spv
              ON spv.id = aac.active_scoring_profile_version_id
            JOIN scoring_profiles sp ON sp.id = spv.profile_id
            JOIN scoring_models sm ON sm.id = spv.model_id
            WHERE aac.context_key = 'global'
            FOR UPDATE OF aac
            """
        ).fetchone()
        if context is None:
            raise SchedulerError("No active analysis context is available")
        model_version = f"{context['model_key']}@{context['model_version_number']}"
        profile_version = f"{context['profile_key']}@{context['profile_version_number']}"
        actual_profile_id = context["active_scoring_profile_version_id"]
        actual_refresh_token = str(context["refresh_token"])
        if (
            actual_profile_id != expected_profile_id
            or actual_refresh_token != expected_refresh_token
        ):
            stale_result = {
                "handler": "data_snapshot_refresh",
                "handler_contract": "data-snapshot-refresh-worker-v1",
                "status": "skipped_stale_context",
                "reason": (
                    "active profile or refresh token changed before the worker executed"
                ),
                "requested_active_scoring_profile_version_id": expected_profile_id,
                "actual_active_scoring_profile_version_id": actual_profile_id,
                "requested_refresh_token": expected_refresh_token,
                "actual_refresh_token": actual_refresh_token,
                "requested_refresh_generation": requested_generation,
                "actual_refresh_generation": context["refresh_generation"],
                "scope": scope,
                "record_mode": record_mode,
                "acceptance_ids": ["A204", "A205", "A206"],
            }
            log_data_snapshot_refresh_operation(
                connection,
                object_type="active_analysis_context",
                object_id=actual_profile_id,
                old_value=payload,
                new_value=dict(context),
                diff=stale_result,
                reason=reason,
                model_version=model_version,
                profile_version=profile_version,
                result_status="skipped",
            )
            return jsonable(stale_result)

        timestamp = utc_now()
        source_stats = current_data_snapshot_source_stats(connection)
        source_hash = data_snapshot_source_hash(
            scope=scope,
            record_mode=record_mode,
            source_stats=source_stats,
        )
        as_of = (
            source_stats.get("latest_source_retrieved_at")
            or source_stats.get("latest_relationship_observed_at")
            or source_stats.get("latest_source_observed_at")
            or timestamp
        )
        previous_scope_snapshot = connection.execute(
            """
            UPDATE data_snapshots
            SET status = 'superseded',
                metadata = metadata || %s
            WHERE scope = %s
              AND record_mode = %s
              AND status = 'active'
            RETURNING id, snapshot_key
            """,
            (
                Jsonb(
                    jsonable(
                        {
                            "superseded_by_job_id": job["id"],
                            "superseded_reason": reason,
                        }
                    )
                ),
                scope,
                record_mode,
            ),
        ).fetchone()
        snapshot_key = f"{scope}:{record_mode}:job:{str(job['id'])[:8]}"
        new_snapshot = connection.execute(
            """
            INSERT INTO data_snapshots(
              snapshot_key, scope, record_mode, status, built_from_ingestion_run_id,
              source_hash, as_of, activated_at, supersedes_snapshot_id, metadata
            )
            VALUES (%s, %s, %s, 'active', %s, %s, %s, %s, %s, %s)
            RETURNING id, snapshot_key, scope, record_mode, status, source_hash,
                      as_of, activated_at, supersedes_snapshot_id, metadata
            """,
            (
                snapshot_key,
                scope,
                record_mode,
                source_stats.get("latest_ingestion_run_id"),
                source_hash,
                as_of,
                timestamp,
                previous_scope_snapshot["id"] if previous_scope_snapshot else None,
                Jsonb(
                    jsonable(
                        {
                            "handler": "data_snapshot_refresh",
                            "handler_contract": "data-snapshot-refresh-worker-v1",
                            "job_id": job["id"],
                            "source_stats": source_stats,
                            "source_hash_contract": "source-stats-sha256-v1",
                            "fixture_policy": (
                                "curated_official_fixture is not live/full-text ingestion"
                            ),
                        }
                    )
                ),
            ),
        ).fetchone()
        updated_context = connection.execute(
            """
            UPDATE active_analysis_contexts
            SET active_data_snapshot_id = %s,
                refresh_token = gen_random_uuid(),
                refresh_generation = refresh_generation + 1,
                status = 'active',
                activated_at = %s,
                activated_by = 'system',
                affected_modules = %s,
                metadata = metadata || %s,
                updated_at = %s
            WHERE context_key = 'global'
            RETURNING refresh_token::text AS refresh_token, refresh_generation
            """,
            (
                new_snapshot["id"],
                timestamp,
                Jsonb(ACTIVE_REFRESH_MODULES),
                Jsonb(
                    jsonable(
                        {
                            "last_data_snapshot_refresh_job_id": job["id"],
                            "last_data_snapshot_id": new_snapshot["id"],
                            "last_data_snapshot_key": new_snapshot["snapshot_key"],
                            "last_data_snapshot_contract": (
                                "data-snapshot-refresh-worker-v1"
                            ),
                        }
                    )
                ),
                timestamp,
            ),
        ).fetchone()
        result = {
            "handler": "data_snapshot_refresh",
            "handler_contract": "data-snapshot-refresh-worker-v1",
            "status": "completed",
            "job_id": job["id"],
            "data_snapshot_id": new_snapshot["id"],
            "data_snapshot_key": new_snapshot["snapshot_key"],
            "previous_active_data_snapshot_id": context["active_data_snapshot_id"],
            "superseded_snapshot_id": (
                previous_scope_snapshot["id"] if previous_scope_snapshot else None
            ),
            "scope": scope,
            "record_mode": record_mode,
            "source_hash": source_hash,
            "source_stats": source_stats,
            "active_scoring_profile_version_id": expected_profile_id,
            "active_scoring_run_id": context["active_scoring_run_id"],
            "previous_refresh_token": expected_refresh_token,
            "refresh_token": updated_context["refresh_token"],
            "previous_refresh_generation": requested_generation,
            "refresh_generation": updated_context["refresh_generation"],
            "affected_modules": ACTIVE_REFRESH_MODULES,
            "acceptance_ids": ["A204", "A205", "A206"],
        }
        outbox_event = write_outbox_event(
            connection,
            event_type="data.snapshot.activated",
            aggregate_type="data_snapshot",
            aggregate_id=new_snapshot["id"],
            idempotency_key=f"data-snapshot-activated:{new_snapshot['id']}",
            payload={
                "schema_version": "analysis-refresh-event-v1",
                "job_id": job["id"],
                "data_snapshot_id": new_snapshot["id"],
                "data_snapshot_key": new_snapshot["snapshot_key"],
                "active_scoring_profile_version_id": expected_profile_id,
                "active_scoring_run_id": context["active_scoring_run_id"],
                "previous_refresh_token": expected_refresh_token,
                "refresh_token": updated_context["refresh_token"],
                "previous_refresh_generation": requested_generation,
                "refresh_generation": updated_context["refresh_generation"],
                "scope": scope,
                "record_mode": record_mode,
                "source_hash": source_hash,
                "source_stats": source_stats,
                "affected_modules": ACTIVE_REFRESH_MODULES,
            },
            metadata={
                "task_ids": ["T1303", "T1304"],
                "acceptance_ids": ["A204", "A205", "A206"],
                "contract": "transactional-outbox-event-v1",
            },
        )
        result["outbox_event"] = outbox_event
        log_data_snapshot_refresh_operation(
            connection,
            object_type="data_snapshot",
            object_id=new_snapshot["id"],
            old_value=dict(context),
            new_value=result,
            diff={
                "previous_refresh_token": expected_refresh_token,
                "refresh_token": updated_context["refresh_token"],
                "previous_refresh_generation": requested_generation,
                "refresh_generation": updated_context["refresh_generation"],
                "previous_active_data_snapshot_id": context["active_data_snapshot_id"],
                "data_snapshot_id": new_snapshot["id"],
                "source_hash": source_hash,
            },
            reason=reason,
            model_version=model_version,
            profile_version=profile_version,
            result_status="success",
        )
        return jsonable(result)


def handle_score_recompute_job(job: dict[str, Any]) -> dict[str, Any]:
    payload = job.get("payload") or {}
    if payload.get("schema_version") != "score-recompute-job-v1":
        raise SchedulerError(
            "score_recompute payload schema_version must be score-recompute-job-v1"
        )
    expected_profile_id = UUID(str(payload["active_scoring_profile_version_id"]))
    expected_refresh_token = str(payload["refresh_token"])
    requested_generation = int(payload["refresh_generation"])
    reason = str(payload.get("reason") or "score recompute worker execution")
    with connect_job_database() as connection:
        context = connection.execute(
            """
            SELECT
              aac.active_scoring_profile_version_id,
              aac.active_data_snapshot_id,
              aac.active_scoring_run_id,
              aac.refresh_token::text AS refresh_token,
              aac.refresh_generation,
              aac.status,
              sp.profile_key,
              spv.version AS profile_version_number,
              spv.id AS profile_version_id,
              spv.model_id,
              spv.weights,
              spv.thresholds,
              spv.half_lives,
              spv.missing_value_policy,
              sm.model_key,
              sm.version AS model_version_number,
              ds.as_of AS data_snapshot_at
            FROM active_analysis_contexts aac
            JOIN scoring_profile_versions spv
              ON spv.id = aac.active_scoring_profile_version_id
            JOIN scoring_profiles sp ON sp.id = spv.profile_id
            JOIN scoring_models sm ON sm.id = spv.model_id
            LEFT JOIN data_snapshots ds ON ds.id = aac.active_data_snapshot_id
            WHERE aac.context_key = 'global'
            FOR UPDATE OF aac
            """
        ).fetchone()
        if context is None:
            raise SchedulerError("No active analysis context is available")
        model_version = f"{context['model_key']}@{context['model_version_number']}"
        profile_version = f"{context['profile_key']}@{context['profile_version_number']}"
        actual_profile_id = context["active_scoring_profile_version_id"]
        actual_refresh_token = str(context["refresh_token"])
        if (
            actual_profile_id != expected_profile_id
            or actual_refresh_token != expected_refresh_token
        ):
            stale_result = {
                "handler": "score_recompute",
                "handler_contract": "score-recompute-worker-v1",
                "status": "skipped_stale_context",
                "reason": (
                    "active profile or refresh token changed before the worker executed"
                ),
                "requested_active_scoring_profile_version_id": expected_profile_id,
                "actual_active_scoring_profile_version_id": actual_profile_id,
                "requested_refresh_token": expected_refresh_token,
                "actual_refresh_token": actual_refresh_token,
                "requested_refresh_generation": requested_generation,
                "actual_refresh_generation": context["refresh_generation"],
                "acceptance_ids": ["A204", "A205", "A206"],
            }
            log_score_recompute_operation(
                connection,
                object_type="active_analysis_context",
                object_id=actual_profile_id,
                old_value=payload,
                new_value=dict(context),
                diff=stale_result,
                reason=reason,
                model_version=model_version,
                profile_version=profile_version,
                result_status="skipped",
            )
            return jsonable(stale_result)

        candidates = connection.execute(
            """
            SELECT
              rfc.id,
              rfc.candidate_key,
              rfc.confidence,
              rfc.independent_source_count,
              rfc.source_threshold_met,
              rfc.review_status,
              rfc.publication_status,
              rfc.parser_version,
              EXISTS (
                SELECT 1
                FROM relationship_fact_candidate_evidence rfce
                WHERE rfce.candidate_id = rfc.id
              ) AS evidence_present
            FROM relationship_fact_candidates rfc
            ORDER BY rfc.candidate_key
            """
        ).fetchall()
        data_snapshot_at = context["data_snapshot_at"] or utc_now()
        scoring_run = connection.execute(
            """
            INSERT INTO scoring_runs(
              model_id, profile_version_id, data_snapshot_at, parameters,
              status, started_at, finished_at, content_hash
            )
            VALUES (%s, %s, %s, %s, 'completed', now(), now(), %s)
            RETURNING id
            """,
            (
                context["model_id"],
                expected_profile_id,
                data_snapshot_at,
                Jsonb(
                    jsonable(
                        {
                            "handler": "score_recompute",
                            "handler_contract": "score-recompute-worker-v1",
                            "job_id": job["id"],
                            "source_refresh_generation": requested_generation,
                            "scope": payload.get("scope", "global"),
                            "weights": context["weights"],
                            "thresholds": context["thresholds"],
                            "half_lives": context["half_lives"],
                            "missing_value_policy": context["missing_value_policy"],
                        }
                    )
                ),
                f"score-recompute:{job['id']}:{expected_profile_id}:{requested_generation}",
            ),
        ).fetchone()
        scored_objects = 0
        for candidate in candidates:
            metrics = candidate_score_metrics(
                confidence=float(candidate["confidence"]),
                independent_source_count=int(candidate["independent_source_count"]),
                source_threshold_met=bool(candidate["source_threshold_met"]),
                review_status=candidate["review_status"],
                publication_status=candidate["publication_status"],
                parser_version_present=candidate["parser_version"] is not None,
                evidence_present=bool(candidate["evidence_present"]),
            )
            connection.execute(
                """
                INSERT INTO score_results(
                  scoring_run_id, object_type, object_id, raw_score, evidence_quality,
                  adjusted_score, coverage, contributions, missing_inputs
                )
                VALUES (
                  %s, 'relationship_fact_candidate', %s, %s, %s, %s, %s, %s, %s
                )
                """,
                (
                    scoring_run["id"],
                    candidate["id"],
                    metrics["raw_score"],
                    metrics["evidence_quality"],
                    metrics["adjusted_score"],
                    metrics["coverage"],
                    Jsonb(jsonable(metrics["contributions"])),
                    Jsonb(jsonable(metrics["missing_inputs"])),
                ),
            )
            scored_objects += 1
        updated_context = connection.execute(
            """
            UPDATE active_analysis_contexts
            SET active_scoring_run_id = %s,
                refresh_token = gen_random_uuid(),
                refresh_generation = refresh_generation + 1,
                status = 'active',
                activated_at = now(),
                activated_by = 'system',
                affected_modules = %s,
                metadata = metadata || %s,
                updated_at = now()
            WHERE context_key = 'global'
            RETURNING refresh_token::text AS refresh_token, refresh_generation
            """,
            (
                scoring_run["id"],
                Jsonb(ACTIVE_REFRESH_MODULES),
                Jsonb(
                    jsonable(
                        {
                            "last_score_recompute_job_id": job["id"],
                            "last_score_recompute_scoring_run_id": scoring_run["id"],
                            "last_score_recompute_scored_objects": scored_objects,
                            "last_score_recompute_contract": "score-recompute-worker-v1",
                        }
                    )
                ),
            ),
        ).fetchone()
        result = {
            "handler": "score_recompute",
            "handler_contract": "score-recompute-worker-v1",
            "status": "completed",
            "job_id": job["id"],
            "scoring_run_id": scoring_run["id"],
            "previous_scoring_run_id": context["active_scoring_run_id"],
            "active_scoring_profile_version_id": expected_profile_id,
            "active_data_snapshot_id": context["active_data_snapshot_id"],
            "previous_refresh_token": expected_refresh_token,
            "refresh_token": updated_context["refresh_token"],
            "previous_refresh_generation": requested_generation,
            "refresh_generation": updated_context["refresh_generation"],
            "scored_objects": scored_objects,
            "score_result_object_type": "relationship_fact_candidate",
            "affected_modules": ACTIVE_REFRESH_MODULES,
            "acceptance_ids": ["A204", "A205", "A206"],
        }
        outbox_event = write_outbox_event(
            connection,
            event_type="score.snapshot.activated",
            aggregate_type="scoring_run",
            aggregate_id=scoring_run["id"],
            idempotency_key=f"score-snapshot-activated:{scoring_run['id']}",
            payload={
                "schema_version": "analysis-refresh-event-v1",
                "job_id": job["id"],
                "scoring_run_id": scoring_run["id"],
                "active_scoring_profile_version_id": expected_profile_id,
                "active_data_snapshot_id": context["active_data_snapshot_id"],
                "previous_refresh_token": expected_refresh_token,
                "refresh_token": updated_context["refresh_token"],
                "previous_refresh_generation": requested_generation,
                "refresh_generation": updated_context["refresh_generation"],
                "scored_objects": scored_objects,
                "affected_modules": ACTIVE_REFRESH_MODULES,
            },
            metadata={
                "task_ids": ["T1303", "T1304"],
                "acceptance_ids": ["A204", "A205", "A206"],
                "contract": "transactional-outbox-event-v1",
            },
        )
        result["outbox_event"] = outbox_event
        log_score_recompute_operation(
            connection,
            object_type="scoring_run",
            object_id=scoring_run["id"],
            old_value=dict(context),
            new_value=result,
            diff={
                "previous_refresh_token": expected_refresh_token,
                "refresh_token": updated_context["refresh_token"],
                "previous_refresh_generation": requested_generation,
                "refresh_generation": updated_context["refresh_generation"],
                "scored_objects": scored_objects,
            },
            reason=reason,
            model_version=model_version,
            profile_version=profile_version,
            result_status="success",
        )
        return jsonable(result)


def run_once(*, worker_id: str, job_type: str | None = None) -> dict[str, Any] | None:
    job = lease_next_job(worker_id=worker_id, job_type=job_type)
    if job is None:
        return None
    if job["job_type"] == "noop":
        return complete_job(
            job_id=job["id"],
            lease_token=job["lease_token"],
            result={"handler": "noop"},
        )
    if job["job_type"] == "score_recompute":
        try:
            result = handle_score_recompute_job(job)
        except Exception as exc:
            return fail_job(
                job_id=job["id"],
                lease_token=job["lease_token"],
                error_class=exc.__class__.__name__,
                error_message=str(exc),
            )
        return complete_job(
            job_id=job["id"],
            lease_token=job["lease_token"],
            result=result,
        )
    if job["job_type"] == "data_snapshot_refresh":
        try:
            result = handle_data_snapshot_refresh_job(job)
        except Exception as exc:
            return fail_job(
                job_id=job["id"],
                lease_token=job["lease_token"],
                error_class=exc.__class__.__name__,
                error_message=str(exc),
            )
        return complete_job(
            job_id=job["id"],
            lease_token=job["lease_token"],
            result=result,
        )
    if job["job_type"] == "curated_ingestion_refresh":
        try:
            result = handle_curated_ingestion_refresh_job(job)
        except Exception as exc:
            return fail_job(
                job_id=job["id"],
                lease_token=job["lease_token"],
                error_class=exc.__class__.__name__,
                error_message=str(exc),
            )
        return complete_job(
            job_id=job["id"],
            lease_token=job["lease_token"],
            result=result,
        )
    if job["job_type"] == "calibration_run":
        try:
            result = handle_calibration_run_job(job)
        except Exception as exc:
            return fail_job(
                job_id=job["id"],
                lease_token=job["lease_token"],
                error_class=exc.__class__.__name__,
                error_message=str(exc),
            )
        return complete_job(
            job_id=job["id"],
            lease_token=job["lease_token"],
            result=result,
        )
    return fail_job(
        job_id=job["id"],
        lease_token=job["lease_token"],
        error_class="handler_not_registered",
        error_message=f"No handler registered for job type {job['job_type']}",
    )


def parse_json_object(value: str) -> dict[str, Any]:
    payload = json.loads(value)
    if not isinstance(payload, dict):
        raise argparse.ArgumentTypeError("JSON payload must be an object")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Manage EEI background jobs.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    enqueue_parser = subparsers.add_parser("enqueue")
    enqueue_parser.add_argument("--job-type", required=True)
    enqueue_parser.add_argument("--idempotency-key", required=True)
    enqueue_parser.add_argument("--payload-json", type=parse_json_object, default={})
    enqueue_parser.add_argument("--priority", type=int, default=100)
    enqueue_parser.add_argument("--max-attempts", type=int, default=DEFAULT_MAX_ATTEMPTS)
    enqueue_parser.add_argument(
        "--dead-letter-after-attempts",
        type=int,
        default=DEFAULT_DEAD_LETTER_AFTER_ATTEMPTS,
    )

    lease_parser = subparsers.add_parser("lease")
    lease_parser.add_argument("--worker-id", required=True)
    lease_parser.add_argument("--job-type")
    lease_parser.add_argument("--lease-ttl-seconds", type=int, default=DEFAULT_LEASE_TTL_SECONDS)

    run_once_parser = subparsers.add_parser("run-once")
    run_once_parser.add_argument("--worker-id", required=True)
    run_once_parser.add_argument("--job-type")

    dispatch_outbox_parser = subparsers.add_parser("dispatch-outbox-once")
    dispatch_outbox_parser.add_argument("--worker-id", required=True)
    dispatch_outbox_parser.add_argument("--event-type")

    recover_parser = subparsers.add_parser("recover-expired")
    recover_parser.set_defaults(_recover=True)

    args = parser.parse_args()
    if args.command == "enqueue":
        payload = enqueue_job(
            job_type=args.job_type,
            idempotency_key=args.idempotency_key,
            payload=args.payload_json,
            priority=args.priority,
            max_attempts=args.max_attempts,
            dead_letter_after_attempts=args.dead_letter_after_attempts,
        )
    elif args.command == "lease":
        payload = lease_next_job(
            worker_id=args.worker_id,
            job_type=args.job_type,
            lease_ttl_seconds=args.lease_ttl_seconds,
        )
    elif args.command == "run-once":
        payload = run_once(worker_id=args.worker_id, job_type=args.job_type)
    elif args.command == "dispatch-outbox-once":
        payload = dispatch_outbox_once(worker_id=args.worker_id, event_type=args.event_type)
    else:
        payload = recover_expired_leases()
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
