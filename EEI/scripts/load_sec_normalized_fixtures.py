#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import psycopg

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from apps.api.app.ingest.sec_fixture_ingestion import (  # noqa: E402
    failure_report,
    run_sec_fixture_ingestion,
)

DEFAULT_SUBMISSIONS_FIXTURE = ROOT / "tests/fixtures/sec/submissions_golden.json"
DEFAULT_COMPANYFACTS_FIXTURE = ROOT / "tests/fixtures/sec/companyfacts_golden.json"


def read_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"fixture must contain a JSON object: {path}")
    return payload


def write_report(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Normalize and dry-run or idempotently upsert synthetic SEC fixtures."
    )
    parser.add_argument("--mode", choices=("fixture", "dry-run"), required=True)
    parser.add_argument("--submissions", default=str(DEFAULT_SUBMISSIONS_FIXTURE))
    parser.add_argument("--companyfacts", default=str(DEFAULT_COMPANYFACTS_FIXTURE))
    parser.add_argument("--database-url")
    parser.add_argument(
        "--allow-database-write",
        action="store_true",
        help="Required with --mode fixture; dry-run never opens a database connection.",
    )
    parser.add_argument("--report")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    started_at = datetime.now(UTC)
    mode = "dry_run" if args.mode == "dry-run" else "fixture"
    try:
        submissions_path = Path(args.submissions).resolve()
        companyfacts_path = Path(args.companyfacts).resolve()
        submissions = read_object(submissions_path)
        companyfacts = read_object(companyfacts_path)
        fixture_paths = {
            "submissions_fixture_path": submissions_path.relative_to(ROOT).as_posix(),
            "companyfacts_fixture_path": companyfacts_path.relative_to(ROOT).as_posix(),
        }
        if mode == "dry_run":
            report = run_sec_fixture_ingestion(
                submissions,
                companyfacts,
                execution_mode=mode,
                **fixture_paths,
            )
        else:
            if not args.allow_database_write:
                raise ValueError("--mode fixture requires --allow-database-write")
            if not args.database_url:
                raise ValueError("--mode fixture requires --database-url")
            with psycopg.connect(args.database_url, connect_timeout=5) as connection:
                report = run_sec_fixture_ingestion(
                    submissions,
                    companyfacts,
                    execution_mode=mode,
                    connection=connection,
                    **fixture_paths,
                )
    except Exception as exc:  # noqa: BLE001 - CLI must emit a structured failure report.
        report = failure_report(
            execution_mode=mode,
            error=exc,
            started_at=started_at,
        )

    if args.report:
        write_report(Path(args.report), report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report.get("status") == "succeeded" else 1


if __name__ == "__main__":
    raise SystemExit(main())
