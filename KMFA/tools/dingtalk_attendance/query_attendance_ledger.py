#!/usr/bin/env python3
"""Read-only queries for the private KMFA S19 attendance ledger."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from contextlib import closing
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from KMFA.tools.dingtalk_attendance.sync_attendance_ledger import DEFAULT_LEDGER_PATH


def get_month_summary(*, db_path: Path = DEFAULT_LEDGER_PATH, month: str) -> dict[str, Any]:
    with closing(_connect(db_path)) as conn:
        row = conn.execute(
            """
            select
                count(*) as run_count,
                coalesce(sum(member_count), 0) as member_count_total,
                coalesce(sum(record_success_count), 0) as record_success_count_total,
                coalesce(sum(summary_success_count), 0) as summary_success_count_total,
                coalesce(sum(record_failure_count), 0) as record_failure_count_total,
                coalesce(sum(summary_failure_count), 0) as summary_failure_count_total,
                coalesce(sum(command_failure_count), 0) as command_failure_count_total,
                coalesce(sum(attendance_anomaly_count), 0) as attendance_anomaly_count_total
            from runs
            where month = ?
            """,
            (month,),
        ).fetchone()
        employee_count = conn.execute(
            "select count(distinct user_id) from daily_attendance where month = ?",
            (month,),
        ).fetchone()[0]
        effective_days = conn.execute(
            "select coalesce(sum(effective_attendance_day), 0) from daily_attendance where month = ?",
            (month,),
        ).fetchone()[0]
    return {
        "month": month,
        "run_count": int(row["run_count"]),
        "employee_count": int(employee_count),
        "member_count_total": int(row["member_count_total"]),
        "record_success_count_total": int(row["record_success_count_total"]),
        "summary_success_count_total": int(row["summary_success_count_total"]),
        "record_failure_count_total": int(row["record_failure_count_total"]),
        "summary_failure_count_total": int(row["summary_failure_count_total"]),
        "command_failure_count_total": int(row["command_failure_count_total"]),
        "attendance_anomaly_count_total": int(row["attendance_anomaly_count_total"]),
        "effective_attendance_day_total": int(effective_days),
    }


def get_employee_month_effective_days(*, db_path: Path = DEFAULT_LEDGER_PATH, month: str, employee: str) -> int:
    with closing(_connect(db_path)) as conn:
        row = conn.execute(
            """
            select count(distinct da.work_date) as effective_days
            from daily_attendance da
            join employees e on e.user_id = da.user_id
            where da.month = ?
              and da.effective_attendance_day = 1
              and (e.name = ? or e.user_id = ?)
            """,
            (month, employee, employee),
        ).fetchone()
    return int(row["effective_days"])


def get_month_anomalies(*, db_path: Path = DEFAULT_LEDGER_PATH, month: str) -> list[dict[str, Any]]:
    with closing(_connect(db_path)) as conn:
        rows = conn.execute(
            """
            select a.run_id, a.work_date, a.user_id, e.name, a.anomaly_type, a.detail
            from anomalies a
            join employees e on e.user_id = a.user_id
            where a.month = ?
            order by a.work_date, e.name, a.anomaly_type, a.detail
            """,
            (month,),
        ).fetchall()
    return [dict(row) for row in rows]


def get_month_rest_required_people(*, db_path: Path = DEFAULT_LEDGER_PATH, month: str) -> list[dict[str, Any]]:
    with closing(_connect(db_path)) as conn:
        rows = conn.execute(
            """
            select e.name, r.user_id, min(r.work_date) as first_work_date, max(r.effective_attendance_days) as effective_attendance_days
            from rest_required_snapshots r
            join employees e on e.user_id = r.user_id
            where r.month = ?
            group by r.user_id, e.name
            order by effective_attendance_days desc, e.name
            """,
            (month,),
        ).fetchall()
    return [
        {
            "name": row["name"],
            "user_id": row["user_id"],
            "first_work_date": row["first_work_date"],
            "effective_attendance_days": int(row["effective_attendance_days"]),
        }
        for row in rows
    ]


def get_run_sync_status(*, db_path: Path = DEFAULT_LEDGER_PATH, run_id: str) -> dict[str, Any]:
    with closing(_connect(db_path)) as conn:
        row = conn.execute(
            """
            select run_id, work_date, month, sync_status, hash_status, raw_path, manifest_path,
                   member_count, record_success_count, summary_success_count, command_failure_count
            from runs
            where run_id = ?
            """,
            (run_id,),
        ).fetchone()
    return dict(row) if row else {"run_id": run_id, "sync_status": "NOT_FOUND"}


def _connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Query the private KMFA S19 attendance ledger.")
    parser.add_argument("--db-path", default=str(DEFAULT_LEDGER_PATH))
    parser.add_argument("--month")
    parser.add_argument("--employee")
    parser.add_argument("--run-id")
    parser.add_argument("--summary", action="store_true")
    parser.add_argument("--effective-days", action="store_true")
    parser.add_argument("--anomalies", action="store_true")
    parser.add_argument("--rest-required", action="store_true")
    parser.add_argument("--run-status", action="store_true")
    args = parser.parse_args(argv)
    db_path = Path(args.db_path)
    if args.summary:
        _require(args.month, "--month is required for --summary")
        result: Any = get_month_summary(db_path=db_path, month=args.month)
    elif args.effective_days:
        _require(args.month, "--month is required for --effective-days")
        _require(args.employee, "--employee is required for --effective-days")
        result = {
            "month": args.month,
            "employee": args.employee,
            "effective_attendance_days": get_employee_month_effective_days(
                db_path=db_path,
                month=args.month,
                employee=args.employee,
            ),
        }
    elif args.anomalies:
        _require(args.month, "--month is required for --anomalies")
        result = {"month": args.month, "anomalies": get_month_anomalies(db_path=db_path, month=args.month)}
    elif args.rest_required:
        _require(args.month, "--month is required for --rest-required")
        result = {"month": args.month, "rest_required_people": get_month_rest_required_people(db_path=db_path, month=args.month)}
    elif args.run_status:
        _require(args.run_id, "--run-id is required for --run-status")
        result = get_run_sync_status(db_path=db_path, run_id=args.run_id)
    else:
        parser.error("choose one query: --summary, --effective-days, --anomalies, --rest-required, or --run-status")
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def _require(value: Any, message: str) -> None:
    if not value:
        raise SystemExit(message)


if __name__ == "__main__":
    sys.exit(main())
