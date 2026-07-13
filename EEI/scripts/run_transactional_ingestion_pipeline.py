#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import UUID

import psycopg
from psycopg.rows import dict_row

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from apps.api.app.ingest.transactional_pipeline import (  # noqa: E402
    execute_transactional_pipeline,
    publication_state,
    record_pipeline_failure,
)


def write_report(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def latest_ingestion_run_id(connection: psycopg.Connection, connector_version: str) -> UUID:
    row = connection.execute(
        """
        SELECT id
        FROM ingestion_runs
        WHERE connector_version = %s AND status = 'succeeded'
        ORDER BY started_at DESC, id DESC
        LIMIT 1
        """,
        (connector_version,),
    ).fetchone()
    if row is None:
        raise RuntimeError(f"No succeeded ingestion run for connector {connector_version!r}")
    return row["id"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Atomically derive facts, scores and changes from a succeeded ingestion run."
    )
    parser.add_argument("--database-url", required=True)
    parser.add_argument("--ingestion-run-id")
    parser.add_argument("--latest-connector-version", default="sec-fixture-ingestion-v1")
    parser.add_argument("--scope", default="golden-vertical:sec-fixture")
    parser.add_argument(
        "--record-mode",
        choices=("fixture", "curated_official_fixture", "dry_run", "live"),
        default="fixture",
    )
    parser.add_argument("--reason", default="T705 transactional ingestion pipeline")
    parser.add_argument("--stale-after-days", type=int, default=365)
    parser.add_argument(
        "--failure-injection-stage",
        choices=("after_facts", "after_scores", "after_changes"),
    )
    parser.add_argument("--allow-failure-injection", action="store_true")
    parser.add_argument("--report")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    started_at = datetime.now(UTC)
    if args.failure_injection_stage and not args.allow_failure_injection:
        raise SystemExit("--failure-injection-stage requires --allow-failure-injection")

    with psycopg.connect(args.database_url, connect_timeout=5, row_factory=dict_row) as connection:
        ingestion_run_id = (
            UUID(args.ingestion_run_id)
            if args.ingestion_run_id
            else latest_ingestion_run_id(connection, args.latest_connector_version)
        )
        before = publication_state(connection)
        try:
            result = execute_transactional_pipeline(
                connection,
                ingestion_run_id=ingestion_run_id,
                scope=args.scope,
                record_mode=args.record_mode,
                reason=args.reason,
                stale_after_days=args.stale_after_days,
                failure_stage=args.failure_injection_stage,
            )
            report = {
                "schema_version": "eei-transactional-ingestion-run-report-v1",
                "task_id": "T705",
                "acceptance_ids": ["A105", "A106", "A107"],
                "status": "succeeded",
                "started_at": started_at.isoformat().replace("+00:00", "Z"),
                "finished_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
                "ingestion_run_id": str(ingestion_run_id),
                "result": result,
                "error_class": None,
                "error_message": None,
                "failure_audit": None,
                "release_scope": {
                    "live_network_performed": False,
                    "a202_closed_by_report": False,
                    "a209_closed_by_report": False,
                    "mvp_release_ready": False,
                },
            }
        except Exception as exc:  # noqa: BLE001 - governed failure audit boundary.
            connection.rollback()
            after = publication_state(connection)
            with connection.transaction():
                failure_audit = record_pipeline_failure(
                    connection,
                    ingestion_run_id=ingestion_run_id,
                    error=exc,
                    failure_stage=args.failure_injection_stage,
                    before_state=before,
                    after_state=after,
                )
            report = {
                "schema_version": "eei-transactional-ingestion-run-report-v1",
                "task_id": "T705",
                "acceptance_ids": ["A105", "A106", "A107"],
                "status": "failed",
                "started_at": started_at.isoformat().replace("+00:00", "Z"),
                "finished_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
                "ingestion_run_id": str(ingestion_run_id),
                "result": None,
                "error_class": type(exc).__name__,
                "error_message": str(exc),
                "failure_audit": failure_audit,
                "release_scope": {
                    "live_network_performed": False,
                    "a202_closed_by_report": False,
                    "a209_closed_by_report": False,
                    "mvp_release_ready": False,
                },
            }

    if args.report:
        write_report(Path(args.report), report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "succeeded" else 1


if __name__ == "__main__":
    raise SystemExit(main())
