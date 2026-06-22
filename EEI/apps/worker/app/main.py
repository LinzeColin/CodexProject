from __future__ import annotations

import argparse
import json
import signal
import time
from typing import Any

from scripts.job_scheduler import (
    connect_job_database,
    dispatch_outbox_once,
    jsonable,
    recover_expired_leases,
    run_once,
)

WORKER_CONTRACT_VERSION = "worker-supervisor-v1"
BASE_ACCEPTANCE_IDS = {"A206", "A209"}
MODEL_REFRESH_ACCEPTANCE_IDS = {"A204", "A205"}
ACCEPTANCE_ID_ORDER = ["A204", "A205", "A206", "A209"]
MODEL_REFRESH_JOB_TYPES = {"score_recompute", "data_snapshot_refresh"}
MODEL_REFRESH_EVENT_TYPES = {
    "data.snapshot.activated",
    "data.snapshot.refresh.requested",
    "model.profile.activated",
    "score.recompute.requested",
    "score.snapshot.activated",
}
_STOP_REQUESTED = False


def _request_stop(_signum: int, _frame: object) -> None:
    global _STOP_REQUESTED
    _STOP_REQUESTED = True


def _status_counts(connection: Any, *, table: str) -> dict[str, int]:
    rows = connection.execute(
        f"""
        SELECT status, count(*)::int AS count
        FROM {table}
        GROUP BY status
        ORDER BY status
        """
    ).fetchall()
    return {str(row["status"]): int(row["count"]) for row in rows}


def _ordered_acceptance_ids(ids: set[str]) -> list[str]:
    return [acceptance_id for acceptance_id in ACCEPTANCE_ID_ORDER if acceptance_id in ids]


def _acceptance_ids_for_filters(
    *,
    job_type: str | None,
    event_type: str | None,
) -> list[str]:
    ids = set(BASE_ACCEPTANCE_IDS)
    if job_type in MODEL_REFRESH_JOB_TYPES or event_type in MODEL_REFRESH_EVENT_TYPES:
        ids.update(MODEL_REFRESH_ACCEPTANCE_IDS)
    return _ordered_acceptance_ids(ids)


def _model_refresh_wake_contract(
    *,
    job_type: str | None,
    event_type: str | None,
) -> dict[str, Any] | None:
    matched_job = job_type in MODEL_REFRESH_JOB_TYPES
    matched_event = event_type in MODEL_REFRESH_EVENT_TYPES
    if not matched_job and not matched_event:
        return None
    return {
        "schema_version": "eei-model-refresh-worker-wake-contract-v1",
        "contract": "t1303-a204-a205-supervised-refresh-wake-v1",
        "scope": "supervisor_cli_and_process_manager_wake",
        "job_type": job_type,
        "event_type": event_type,
        "matched_model_refresh_job": matched_job,
        "matched_model_refresh_event": matched_event,
        "covered_job_types": sorted(MODEL_REFRESH_JOB_TYPES),
        "covered_event_types": sorted(MODEL_REFRESH_EVENT_TYPES),
        "guarantees": [
            "supervisor_wake_can_execute_score_recompute_and_data_snapshot_refresh_handlers",
            "handlers_advance_active_analysis_context_refresh_token_atomically",
            "transactional_outbox_dispatch_is_available_in_the_same_supervised_cycle",
        ],
        "non_closure": [
            "does_not_complete_A209_4h_or_24h_soak",
            "does_not_replace_host_level_release_manager_or_platform_process_supervision",
            "does_not_close_A204_or_A205_without_current_governance_evidence",
        ],
        "acceptance_ids": _acceptance_ids_for_filters(
            job_type=job_type,
            event_type=event_type,
        ),
    }


def worker_health_snapshot() -> dict[str, Any]:
    with connect_job_database() as connection:
        background_counts = _status_counts(connection, table="background_jobs")
        outbox_counts = _status_counts(connection, table="transactional_outbox")
        row = connection.execute(
            """
            SELECT
              (
                SELECT count(*)::int
                FROM background_jobs
                WHERE status = 'running'
                  AND lease_expires_at IS NOT NULL
                  AND lease_expires_at <= now()
              ) AS expired_background_leases,
              (
                SELECT count(*)::int
                FROM transactional_outbox
                WHERE status = 'processing'
                  AND lease_expires_at IS NOT NULL
                  AND lease_expires_at <= now()
              ) AS expired_outbox_leases,
              (
                SELECT max(heartbeat_at)
                FROM background_jobs
              ) AS latest_background_heartbeat_at,
              (
                SELECT max(heartbeat_at)
                FROM transactional_outbox
              ) AS latest_outbox_heartbeat_at,
              (
                SELECT count(*)::int
                FROM dead_letter_jobs
              ) AS dead_letter_job_count
            """
        ).fetchone()
    blocking_background = (
        background_counts.get("running", 0)
        + background_counts.get("dead_letter", 0)
        + int(row["expired_background_leases"])
    )
    blocking_outbox = (
        outbox_counts.get("processing", 0)
        + outbox_counts.get("dead_letter", 0)
        + int(row["expired_outbox_leases"])
    )
    return jsonable(
        {
            "schema_version": "eei-worker-health-v1",
            "handler_contract": WORKER_CONTRACT_VERSION,
            "status": "ready" if blocking_background + blocking_outbox == 0 else "attention",
            "background_jobs": {
                "counts": background_counts,
                "expired_leases": row["expired_background_leases"],
                "latest_heartbeat_at": row["latest_background_heartbeat_at"],
            },
            "transactional_outbox": {
                "counts": outbox_counts,
                "expired_leases": row["expired_outbox_leases"],
                "latest_heartbeat_at": row["latest_outbox_heartbeat_at"],
            },
            "dead_letter_job_count": row["dead_letter_job_count"],
            "supervision": {
                "recover_expired_leases": True,
                "run_background_jobs": True,
                "dispatch_transactional_outbox": True,
                "graceful_shutdown_signal": "SIGTERM/SIGINT",
                "acceptance_ids": ["A206", "A209"],
            },
        }
    )


def run_worker_cycle(
    *,
    worker_id: str,
    job_type: str | None = None,
    event_type: str | None = None,
    max_jobs: int = 1,
    max_outbox: int = 1,
    recover_leases: bool = True,
) -> dict[str, Any]:
    acceptance_ids = _acceptance_ids_for_filters(job_type=job_type, event_type=event_type)
    model_refresh_wake_contract = _model_refresh_wake_contract(
        job_type=job_type,
        event_type=event_type,
    )
    recovered = recover_expired_leases() if recover_leases else {"recovered": 0, "dead_lettered": 0}
    jobs: list[dict[str, Any]] = []
    outbox_events: list[dict[str, Any]] = []

    for _ in range(max_jobs):
        job = run_once(worker_id=worker_id, job_type=job_type)
        if job is None:
            break
        jobs.append(job)

    for _ in range(max_outbox):
        event = dispatch_outbox_once(worker_id=worker_id, event_type=event_type)
        if event is None:
            break
        outbox_events.append(event)

    idle = (
        recovered["recovered"] == 0
        and recovered["dead_lettered"] == 0
        and len(jobs) == 0
        and len(outbox_events) == 0
    )
    return jsonable(
        {
            "schema_version": "eei-worker-cycle-v1",
            "handler_contract": WORKER_CONTRACT_VERSION,
            "worker_id": worker_id,
            "filters": {
                "job_type": job_type,
                "event_type": event_type,
            },
            "limits": {
                "max_jobs": max_jobs,
                "max_outbox": max_outbox,
            },
            "lease_recovery": recovered,
            "jobs_processed": len(jobs),
            "outbox_events_dispatched": len(outbox_events),
            "idle": idle,
            "jobs": jobs,
            "outbox_events": outbox_events,
            "health": worker_health_snapshot(),
            "model_refresh_wake_contract": model_refresh_wake_contract,
            "acceptance_ids": acceptance_ids,
        }
    )


def supervise_worker(
    *,
    worker_id: str,
    job_type: str | None = None,
    event_type: str | None = None,
    max_jobs_per_cycle: int = 1,
    max_outbox_per_cycle: int = 1,
    poll_interval_seconds: float = 5.0,
    max_cycles: int | None = None,
    stop_when_idle: bool = False,
) -> dict[str, Any]:
    acceptance_ids = _acceptance_ids_for_filters(job_type=job_type, event_type=event_type)
    model_refresh_wake_contract = _model_refresh_wake_contract(
        job_type=job_type,
        event_type=event_type,
    )
    signal.signal(signal.SIGTERM, _request_stop)
    signal.signal(signal.SIGINT, _request_stop)
    summary: dict[str, Any] = {
        "schema_version": "eei-worker-supervision-summary-v1",
        "handler_contract": WORKER_CONTRACT_VERSION,
        "worker_id": worker_id,
        "status": "running",
        "cycles": 0,
        "jobs_processed": 0,
        "outbox_events_dispatched": 0,
        "lease_recoveries": 0,
        "lease_dead_letters": 0,
        "filters": {
            "job_type": job_type,
            "event_type": event_type,
        },
        "model_refresh_wake_contract": model_refresh_wake_contract,
        "stop_reason": None,
        "last_cycle": None,
        "acceptance_ids": acceptance_ids,
    }
    while not _STOP_REQUESTED:
        cycle = run_worker_cycle(
            worker_id=worker_id,
            job_type=job_type,
            event_type=event_type,
            max_jobs=max_jobs_per_cycle,
            max_outbox=max_outbox_per_cycle,
        )
        summary["cycles"] += 1
        summary["jobs_processed"] += cycle["jobs_processed"]
        summary["outbox_events_dispatched"] += cycle["outbox_events_dispatched"]
        summary["lease_recoveries"] += cycle["lease_recovery"]["recovered"]
        summary["lease_dead_letters"] += cycle["lease_recovery"]["dead_lettered"]
        summary["last_cycle"] = cycle
        if stop_when_idle and cycle["idle"]:
            summary["stop_reason"] = "idle"
            break
        if max_cycles is not None and summary["cycles"] >= max_cycles:
            summary["stop_reason"] = "max_cycles"
            break
        time.sleep(poll_interval_seconds)
    if _STOP_REQUESTED and summary["stop_reason"] is None:
        summary["stop_reason"] = "signal"
    summary["status"] = "stopped"
    summary["health"] = worker_health_snapshot()
    return jsonable(summary)


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("value must be zero or greater")
    return parsed


def non_negative_float(value: str) -> float:
    parsed = float(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("value must be zero or greater")
    return parsed


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the EEI supervised worker.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("health")

    once_parser = subparsers.add_parser("once")
    once_parser.add_argument("--worker-id", required=True)
    once_parser.add_argument("--job-type")
    once_parser.add_argument("--event-type")
    once_parser.add_argument("--max-jobs", type=positive_int, default=1)
    once_parser.add_argument("--max-outbox", type=positive_int, default=1)
    once_parser.add_argument("--no-recover-leases", action="store_true")

    supervise_parser = subparsers.add_parser("supervise")
    supervise_parser.add_argument("--worker-id", required=True)
    supervise_parser.add_argument("--job-type")
    supervise_parser.add_argument("--event-type")
    supervise_parser.add_argument("--max-jobs-per-cycle", type=positive_int, default=1)
    supervise_parser.add_argument("--max-outbox-per-cycle", type=positive_int, default=1)
    supervise_parser.add_argument("--poll-interval-seconds", type=non_negative_float, default=5.0)
    supervise_parser.add_argument("--max-cycles", type=positive_int)
    supervise_parser.add_argument("--stop-when-idle", action="store_true")

    args = parser.parse_args()
    if args.command == "health":
        payload = worker_health_snapshot()
    elif args.command == "once":
        payload = run_worker_cycle(
            worker_id=args.worker_id,
            job_type=args.job_type,
            event_type=args.event_type,
            max_jobs=args.max_jobs,
            max_outbox=args.max_outbox,
            recover_leases=not args.no_recover_leases,
        )
    else:
        payload = supervise_worker(
            worker_id=args.worker_id,
            job_type=args.job_type,
            event_type=args.event_type,
            max_jobs_per_cycle=args.max_jobs_per_cycle,
            max_outbox_per_cycle=args.max_outbox_per_cycle,
            poll_interval_seconds=args.poll_interval_seconds,
            max_cycles=args.max_cycles,
            stop_when_idle=args.stop_when_idle,
        )
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
