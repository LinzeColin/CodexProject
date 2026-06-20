#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

try:
    from db_tools import database_url
except ModuleNotFoundError:  # pragma: no cover - used when imported as scripts.job_scheduler
    from scripts.db_tools import database_url

DEFAULT_LEASE_TTL_SECONDS = 900
DEFAULT_MAX_ATTEMPTS = 5
DEFAULT_DEAD_LETTER_AFTER_ATTEMPTS = 5
DEFAULT_RETRY_BACKOFF_SECONDS = 30


class SchedulerError(RuntimeError):
    pass


def connect_job_database() -> psycopg.Connection:
    return psycopg.connect(database_url(), connect_timeout=5, row_factory=dict_row)


def utc_now() -> datetime:
    return datetime.now(UTC).replace(microsecond=0)


def jsonable(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.astimezone(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    if isinstance(value, UUID):
        return str(value)
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
    else:
        payload = recover_expired_leases()
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
