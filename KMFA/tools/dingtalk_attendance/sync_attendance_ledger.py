#!/usr/bin/env python3
"""Sync KMFA S19 OneDrive attendance archives into a private SQLite ledger."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import sys
from collections.abc import Iterable, Mapping
from contextlib import closing
from datetime import datetime
from pathlib import Path
import sqlite3
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from KMFA.tools.dingtalk_attendance import ONEDRIVE_ROOT
from KMFA.tools.dingtalk_attendance.dws_attendance import (
    SUMMARY_TODAY_ANOMALY_TOKENS,
    _record_list_has_morning_and_evening,
)
from KMFA.tools.dingtalk_attendance.notification_template import REST_REQUIRED_THRESHOLD_DAYS
from KMFA.tools.dingtalk_attendance.secrets_loader import ROOT


PRIVATE_RUNTIME_DIR = ROOT / "metadata" / "dingtalk_attendance" / "private_runtime"
DEFAULT_LEDGER_PATH = PRIVATE_RUNTIME_DIR / "attendance_ledger.sqlite"
SCHEMA_VERSION = 1


def initialize_ledger(db_path: Path = DEFAULT_LEDGER_PATH) -> dict[str, Any]:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(db_path)) as conn:
        conn.execute("pragma foreign_keys=on")
        _create_schema(conn)
        conn.commit()
    return {"status": "READY", "db_path": str(db_path), "schema_version": SCHEMA_VERSION}


def sync_archives_to_ledger(
    *,
    onedrive_root: Path | str = Path(ONEDRIVE_ROOT),
    db_path: Path = DEFAULT_LEDGER_PATH,
    month: str | None = None,
    all_months: bool = False,
    dry_run: bool = False,
) -> dict[str, Any]:
    root = Path(onedrive_root)
    months = _selected_month_dirs(root=root, month=month, all_months=all_months)
    manifests = [manifest for month_dir in months for manifest in sorted(month_dir.glob("s19_*.manifest.json"))]
    raw_files = [raw for month_dir in months for raw in sorted(month_dir.glob("s19_*.raw.jsonl.gz"))]
    manifest_run_ids = {_run_id_from_archive_path(path, ".manifest.json") for path in manifests}
    raw_without_manifest = [
        raw
        for raw in raw_files
        if _run_id_from_archive_path(raw, ".raw.jsonl.gz") not in manifest_run_ids
    ]
    dry_summary = {
        "status": "DRY_RUN" if dry_run else "READY_TO_SYNC",
        "onedrive_root": str(root),
        "months": [path.name for path in months],
        "manifest_count": len(manifests),
        "raw_count": len(raw_files),
        "raw_without_manifest_count": len(raw_without_manifest),
        "database_path": str(db_path),
    }
    if dry_run:
        return dry_summary

    initialize_ledger(db_path)
    synced_runs = 0
    warning_count = 0
    error_count = 0
    affected_months: set[str] = set()
    with closing(sqlite3.connect(db_path)) as conn:
        conn.row_factory = sqlite3.Row
        conn.execute("pragma foreign_keys=on")
        for raw in raw_without_manifest:
            warning_count += 1
            _audit(
                conn,
                run_id=_run_id_from_archive_path(raw, ".raw.jsonl.gz"),
                event_type="RAW_WITHOUT_MANIFEST",
                status="WARNING",
                message="raw archive has no matching manifest; source preserved but not indexed",
                source_path=raw,
            )
        for manifest_path in manifests:
            result = _sync_one_manifest(conn, manifest_path)
            synced_runs += 1 if result["indexed"] else 0
            warning_count += result["warning_count"]
            error_count += result["error_count"]
            if result.get("month"):
                affected_months.add(str(result["month"]))
        for month_value in sorted(affected_months):
            _rebuild_rest_required_snapshots(conn, month_value)
        conn.commit()
    return {
        **dry_summary,
        "status": "SYNCED" if error_count == 0 else "SYNCED_WITH_ERRORS",
        "synced_runs": synced_runs,
        "warning_count": warning_count,
        "error_count": error_count,
        "affected_months": sorted(affected_months),
    }


def validate_ledger(db_path: Path = DEFAULT_LEDGER_PATH) -> dict[str, Any]:
    if not db_path.exists():
        return {"status": "MISSING", "db_path": str(db_path), "errors": ["ledger database missing"]}
    with closing(sqlite3.connect(db_path)) as conn:
        conn.row_factory = sqlite3.Row
        expected = {
            "runs",
            "employees",
            "daily_attendance",
            "punch_records",
            "summary_items",
            "anomalies",
            "rest_required_snapshots",
            "dispatch_receipts",
            "sync_audit",
        }
        tables = {
            row["name"]
            for row in conn.execute("select name from sqlite_master where type='table' and name not like 'sqlite_%'")
        }
        missing = sorted(expected - tables)
        hash_mismatches = conn.execute("select count(*) from runs where hash_status='MISMATCH'").fetchone()[0]
        error_audits = conn.execute("select count(*) from sync_audit where status='ERROR'").fetchone()[0]
        warning_audits = conn.execute("select count(*) from sync_audit where status='WARNING'").fetchone()[0]
        run_count = conn.execute("select count(*) from runs").fetchone()[0]
    errors = []
    if missing:
        errors.append(f"missing tables: {', '.join(missing)}")
    if hash_mismatches:
        errors.append(f"hash mismatches: {hash_mismatches}")
    status = "PASS" if not errors else "FAIL"
    return {
        "status": status,
        "db_path": str(db_path),
        "schema_version": SCHEMA_VERSION,
        "run_count": run_count,
        "warning_audit_count": warning_audits,
        "error_audit_count": error_audits,
        "errors": errors,
    }


def _create_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        create table if not exists runs (
            run_id text primary key,
            run_type text,
            work_date text,
            month text,
            backend text,
            sync_status text not null,
            hash_status text not null,
            raw_path text,
            raw_sha256_manifest text,
            raw_sha256_actual text,
            manifest_path text,
            dispatch_path text,
            cleanup_path text,
            member_count integer not null default 0,
            record_success_count integer not null default 0,
            summary_success_count integer not null default 0,
            record_failure_count integer not null default 0,
            summary_failure_count integer not null default 0,
            command_failure_count integer not null default 0,
            attendance_anomaly_count integer not null default 0,
            synced_at text not null
        );
        create table if not exists employees (
            user_id text primary key,
            name text not null,
            first_seen_run_id text,
            last_seen_run_id text,
            updated_at text not null
        );
        create table if not exists daily_attendance (
            run_id text not null,
            user_id text not null,
            work_date text not null,
            month text not null,
            record_status text not null,
            summary_status text not null,
            record_count integer not null default 0,
            record_has_full_day integer not null default 0,
            effective_attendance_day integer not null default 0,
            known_no_record integer not null default 0,
            record_failure_reason text,
            summary_failure_reason text,
            primary key (run_id, user_id),
            foreign key (run_id) references runs(run_id) on delete cascade,
            foreign key (user_id) references employees(user_id) on delete cascade
        );
        create table if not exists punch_records (
            run_id text not null,
            user_id text not null,
            work_date text not null,
            punch_index integer not null,
            check_type text,
            check_type_desc text,
            time_result text,
            source_type text,
            user_check_time text,
            primary key (run_id, user_id, punch_index),
            foreign key (run_id, user_id) references daily_attendance(run_id, user_id) on delete cascade
        );
        create table if not exists summary_items (
            run_id text not null,
            user_id text not null,
            item_id text,
            item_name text,
            child_index integer not null default 0,
            child_name text,
            child_date text,
            is_today integer not null default 0,
            is_anomaly integer not null default 0,
            primary key (run_id, user_id, item_id, child_index),
            foreign key (run_id, user_id) references daily_attendance(run_id, user_id) on delete cascade
        );
        create table if not exists anomalies (
            run_id text not null,
            user_id text not null,
            work_date text not null,
            month text not null,
            anomaly_type text not null,
            detail text,
            primary key (run_id, user_id, anomaly_type, detail),
            foreign key (run_id, user_id) references daily_attendance(run_id, user_id) on delete cascade
        );
        create table if not exists rest_required_snapshots (
            run_id text not null,
            user_id text not null,
            work_date text not null,
            month text not null,
            effective_attendance_days integer not null,
            threshold_days integer not null,
            primary key (run_id, user_id),
            foreign key (run_id) references runs(run_id) on delete cascade,
            foreign key (user_id) references employees(user_id) on delete cascade
        );
        create table if not exists dispatch_receipts (
            run_id text not null,
            target_label text not null,
            target_type text,
            channel text,
            management_status text,
            hr_status text,
            failure_reason text,
            trace_id_present integer not null default 0,
            notification_status text,
            primary key (run_id, target_label, target_type),
            foreign key (run_id) references runs(run_id) on delete cascade
        );
        create table if not exists sync_audit (
            audit_id integer primary key autoincrement,
            run_id text,
            event_type text not null,
            status text not null,
            message text,
            source_path text,
            created_at text not null
        );
        """
    )


def _sync_one_manifest(conn: sqlite3.Connection, manifest_path: Path) -> dict[str, Any]:
    warning_count = 0
    error_count = 0
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        _audit(conn, run_id=None, event_type="MANIFEST_READ_FAILED", status="ERROR", message=str(exc), source_path=manifest_path)
        return {"indexed": False, "warning_count": 0, "error_count": 1}
    run_id = str(manifest.get("run_id") or _run_id_from_archive_path(manifest_path, ".manifest.json"))
    raw_path = _resolve_archive_path(manifest_path.parent, manifest.get("raw_jsonl_gz"))
    dispatch_path = _resolve_archive_path(manifest_path.parent, manifest.get("dispatch_receipt"))
    cleanup_path = _resolve_archive_path(manifest_path.parent, manifest.get("cleanup_audit"))
    if raw_path is None or not raw_path.exists():
        _audit(conn, run_id=run_id, event_type="RAW_MISSING", status="ERROR", message="manifest raw_jsonl_gz missing", source_path=manifest_path)
        error_count += 1
        _upsert_run_from_manifest(
            conn,
            manifest=manifest,
            manifest_path=manifest_path,
            raw_path=raw_path,
            dispatch_path=dispatch_path,
            cleanup_path=cleanup_path,
            raw_sha_actual="",
            hash_status="RAW_MISSING",
            sync_status="RAW_MISSING",
        )
        return {"indexed": False, "warning_count": warning_count, "error_count": error_count, "month": _month_from_run_id(run_id)}
    actual_hash = hashlib.sha256(raw_path.read_bytes()).hexdigest()
    manifest_hash = str(manifest.get("raw_jsonl_gz_sha256") or "")
    hash_status = "OK" if manifest_hash == actual_hash else "MISMATCH"
    if hash_status != "OK":
        _audit(conn, run_id=run_id, event_type="RAW_HASH_MISMATCH", status="ERROR", message="raw sha256 differs from manifest", source_path=raw_path)
        error_count += 1
    try:
        rows, metadata = _read_raw_rows(raw_path)
    except (OSError, gzip.BadGzipFile, json.JSONDecodeError) as exc:
        _audit(conn, run_id=run_id, event_type="RAW_READ_FAILED", status="ERROR", message=str(exc), source_path=raw_path)
        error_count += 1
        _upsert_run_from_manifest(
            conn,
            manifest=manifest,
            manifest_path=manifest_path,
            raw_path=raw_path,
            dispatch_path=dispatch_path,
            cleanup_path=cleanup_path,
            raw_sha_actual=actual_hash,
            hash_status=hash_status,
            sync_status="RAW_READ_FAILED",
        )
        _delete_run_children(conn, run_id)
        return {"indexed": False, "warning_count": warning_count, "error_count": error_count, "month": _month_from_run_id(run_id)}
    run_stats = _manifest_stats(manifest, metadata)
    work_date = _work_date_from_run_id(run_id) or str(metadata.get("work_date") or "")
    month = work_date[:7].replace("-", "") if work_date else _month_from_run_id(run_id)
    _upsert_run_from_manifest(
        conn,
        manifest={**manifest, "stats": run_stats},
        manifest_path=manifest_path,
        raw_path=raw_path,
        dispatch_path=dispatch_path,
        cleanup_path=cleanup_path,
        raw_sha_actual=actual_hash,
        hash_status=hash_status,
        sync_status="SYNCED" if hash_status == "OK" else "HASH_MISMATCH",
    )
    _delete_run_children(conn, run_id)
    for row in rows:
        _insert_employee_row(conn, run_id=run_id, work_date=work_date, month=month, row=row)
    if dispatch_path and dispatch_path.exists():
        _insert_dispatch_receipts(conn, run_id=run_id, dispatch_path=dispatch_path)
    elif dispatch_path:
        warning_count += 1
        _audit(conn, run_id=run_id, event_type="DISPATCH_MISSING", status="WARNING", message="dispatch receipt missing", source_path=dispatch_path)
    _audit(conn, run_id=run_id, event_type="SYNC_RUN", status="OK", message="run indexed from OneDrive manifest", source_path=manifest_path)
    return {"indexed": True, "warning_count": warning_count, "error_count": error_count, "month": month}


def _upsert_run_from_manifest(
    conn: sqlite3.Connection,
    *,
    manifest: Mapping[str, Any],
    manifest_path: Path,
    raw_path: Path | None,
    dispatch_path: Path | None,
    cleanup_path: Path | None,
    raw_sha_actual: str,
    hash_status: str,
    sync_status: str,
) -> None:
    run_id = str(manifest.get("run_id") or _run_id_from_archive_path(manifest_path, ".manifest.json"))
    stats = manifest.get("stats", {}) if isinstance(manifest.get("stats"), Mapping) else {}
    work_date = _work_date_from_run_id(run_id) or ""
    month = work_date[:7].replace("-", "") if work_date else _month_from_run_id(run_id)
    conn.execute(
        """
        insert into runs (
            run_id, run_type, work_date, month, backend, sync_status, hash_status,
            raw_path, raw_sha256_manifest, raw_sha256_actual, manifest_path, dispatch_path, cleanup_path,
            member_count, record_success_count, summary_success_count, record_failure_count,
            summary_failure_count, command_failure_count, attendance_anomaly_count, synced_at
        )
        values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        on conflict(run_id) do update set
            run_type=excluded.run_type,
            work_date=excluded.work_date,
            month=excluded.month,
            backend=excluded.backend,
            sync_status=excluded.sync_status,
            hash_status=excluded.hash_status,
            raw_path=excluded.raw_path,
            raw_sha256_manifest=excluded.raw_sha256_manifest,
            raw_sha256_actual=excluded.raw_sha256_actual,
            manifest_path=excluded.manifest_path,
            dispatch_path=excluded.dispatch_path,
            cleanup_path=excluded.cleanup_path,
            member_count=excluded.member_count,
            record_success_count=excluded.record_success_count,
            summary_success_count=excluded.summary_success_count,
            record_failure_count=excluded.record_failure_count,
            summary_failure_count=excluded.summary_failure_count,
            command_failure_count=excluded.command_failure_count,
            attendance_anomaly_count=excluded.attendance_anomaly_count,
            synced_at=excluded.synced_at
        """,
        (
            run_id,
            _run_type_from_run_id(run_id),
            work_date,
            month,
            str(manifest.get("backend") or "dws"),
            sync_status,
            hash_status,
            str(raw_path or ""),
            str(manifest.get("raw_jsonl_gz_sha256") or ""),
            raw_sha_actual,
            str(manifest_path),
            str(dispatch_path or ""),
            str(cleanup_path or ""),
            _int(stats.get("member_count")),
            _int(stats.get("record_success_count")),
            _int(stats.get("summary_success_count")),
            _int(stats.get("record_failure_count")),
            _int(stats.get("summary_failure_count")),
            _int(stats.get("command_failure_count")),
            _int(stats.get("attendance_anomaly_count")),
            _now_iso(),
        ),
    )


def _delete_run_children(conn: sqlite3.Connection, run_id: str) -> None:
    for table in (
        "dispatch_receipts",
        "rest_required_snapshots",
        "anomalies",
        "summary_items",
        "punch_records",
        "daily_attendance",
    ):
        conn.execute(f"delete from {table} where run_id = ?", (run_id,))


def _insert_employee_row(conn: sqlite3.Connection, *, run_id: str, work_date: str, month: str, row: Mapping[str, Any]) -> None:
    member = row.get("member", {}) if isinstance(row.get("member"), Mapping) else {}
    user_id = str(member.get("userId") or member.get("user_id") or member.get("name") or "").strip()
    name = str(member.get("name") or user_id).strip()
    if not user_id:
        return
    conn.execute(
        """
        insert into employees (user_id, name, first_seen_run_id, last_seen_run_id, updated_at)
        values (?, ?, ?, ?, ?)
        on conflict(user_id) do update set
            name=excluded.name,
            last_seen_run_id=excluded.last_seen_run_id,
            updated_at=excluded.updated_at
        """,
        (user_id, name, run_id, run_id, _now_iso()),
    )
    record_list = _record_list_from_row(row)
    record_success = _record_success(row)
    summary_success = _summary_success(row)
    record_status = "SUCCESS" if record_success else "FAILED"
    summary_status = "SUCCESS" if summary_success else "FAILED"
    record_has_full_day = _record_list_has_morning_and_evening(record_list)
    effective_day = bool(record_success and record_has_full_day)
    derived = row.get("derived", {}) if isinstance(row.get("derived"), Mapping) else {}
    known_no_record = bool(derived.get("known_no_record"))
    conn.execute(
        """
        insert into daily_attendance (
            run_id, user_id, work_date, month, record_status, summary_status, record_count,
            record_has_full_day, effective_attendance_day, known_no_record,
            record_failure_reason, summary_failure_reason
        )
        values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            run_id,
            user_id,
            work_date,
            month,
            record_status,
            summary_status,
            len(record_list),
            int(record_has_full_day),
            int(effective_day),
            int(known_no_record),
            None if record_success else _failure_reason(row.get("record")),
            None if summary_success else _failure_reason(row.get("summary")),
        ),
    )
    for index, punch in enumerate(record_list, start=1):
        _insert_punch(conn, run_id=run_id, user_id=user_id, work_date=work_date, index=index, punch=punch)
    _insert_summary_items(conn, run_id=run_id, user_id=user_id, work_date=work_date, summary_payload=_summary_payload(row))
    _insert_anomalies(conn, run_id=run_id, user_id=user_id, work_date=work_date, month=month, row=row)


def _insert_punch(
    conn: sqlite3.Connection,
    *,
    run_id: str,
    user_id: str,
    work_date: str,
    index: int,
    punch: Any,
) -> None:
    payload = punch if isinstance(punch, Mapping) else {}
    conn.execute(
        """
        insert into punch_records (
            run_id, user_id, work_date, punch_index, check_type, check_type_desc,
            time_result, source_type, user_check_time
        )
        values (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            run_id,
            user_id,
            work_date,
            index,
            _str_or_none(payload.get("checkType")),
            _str_or_none(payload.get("checkTypeDesc")),
            _str_or_none(payload.get("timeResult")),
            _str_or_none(payload.get("sourceType")),
            _str_or_none(payload.get("userCheckTime") or payload.get("checkTime")),
        ),
    )


def _insert_summary_items(
    conn: sqlite3.Connection,
    *,
    run_id: str,
    user_id: str,
    work_date: str,
    summary_payload: Mapping[str, Any],
) -> None:
    result = summary_payload.get("result", {}) if isinstance(summary_payload, Mapping) else {}
    items = result.get("items", []) if isinstance(result, Mapping) else []
    if not isinstance(items, list):
        return
    for item in items:
        if not isinstance(item, Mapping):
            continue
        item_id = str(item.get("id") or item.get("name") or "item")
        item_name = str(item.get("name") or "")
        item_is_anomaly = _is_summary_anomaly_item(item)
        children = item.get("children", [])
        if not isinstance(children, list) or not children:
            conn.execute(
                """
                insert or replace into summary_items (
                    run_id, user_id, item_id, item_name, child_index, child_name,
                    child_date, is_today, is_anomaly
                )
                values (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (run_id, user_id, item_id, item_name, 0, None, None, 0, int(item_is_anomaly)),
            )
            continue
        for index, child in enumerate(children, start=1):
            child_payload = child if isinstance(child, Mapping) else {}
            child_date = _summary_child_date(child_payload)
            conn.execute(
                """
                insert or replace into summary_items (
                    run_id, user_id, item_id, item_name, child_index, child_name,
                    child_date, is_today, is_anomaly
                )
                values (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    user_id,
                    item_id,
                    item_name,
                    index,
                    _str_or_none(child_payload.get("name")),
                    child_date,
                    int(child_date == work_date or work_date in str(child_payload.get("name") or "")),
                    int(item_is_anomaly),
                ),
            )


def _insert_anomalies(
    conn: sqlite3.Connection,
    *,
    run_id: str,
    user_id: str,
    work_date: str,
    month: str,
    row: Mapping[str, Any],
) -> None:
    derived = row.get("derived", {}) if isinstance(row.get("derived"), Mapping) else {}
    anomalies: list[tuple[str, str]] = []
    if not _record_success(row):
        anomalies.append(("SYSTEM_RECORD_FAILURE", _failure_reason(row.get("record")) or "record failed"))
    if not _summary_success(row):
        anomalies.append(("SYSTEM_SUMMARY_FAILURE", _failure_reason(row.get("summary")) or "summary failed"))
    if bool(derived.get("record_anomaly")):
        anomalies.append(("RECORD_ANOMALY", "record empty or missing required punches"))
    if bool(derived.get("summary_today_anomaly")):
        issues = derived.get("summary_today_issues", [])
        if isinstance(issues, list) and issues:
            anomalies.extend(("SUMMARY_TODAY_ANOMALY", str(issue)) for issue in issues)
        else:
            anomalies.append(("SUMMARY_TODAY_ANOMALY", "summary marks today as abnormal"))
    for anomaly_type, detail in anomalies:
        conn.execute(
            """
            insert or replace into anomalies (run_id, user_id, work_date, month, anomaly_type, detail)
            values (?, ?, ?, ?, ?, ?)
            """,
            (run_id, user_id, work_date, month, anomaly_type, detail),
        )


def _insert_dispatch_receipts(conn: sqlite3.Connection, *, run_id: str, dispatch_path: Path) -> None:
    try:
        payload = json.loads(dispatch_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        _audit(conn, run_id=run_id, event_type="DISPATCH_READ_FAILED", status="WARNING", message=str(exc), source_path=dispatch_path)
        return
    target_results = payload.get("target_results", [])
    if not isinstance(target_results, list):
        target_results = []
    for target in target_results:
        if not isinstance(target, Mapping):
            continue
        conn.execute(
            """
            insert or replace into dispatch_receipts (
                run_id, target_label, target_type, channel, management_status, hr_status,
                failure_reason, trace_id_present, notification_status
            )
            values (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                str(target.get("label") or "UNKNOWN"),
                _str_or_none(target.get("type")),
                _str_or_none(target.get("channel")),
                _str_or_none(target.get("management_status")),
                _str_or_none(target.get("hr_status")),
                _str_or_none(target.get("failure_reason")),
                int(bool(target.get("trace_id_present"))),
                _str_or_none(payload.get("notification_status")),
            ),
        )


def _rebuild_rest_required_snapshots(conn: sqlite3.Connection, month: str) -> None:
    conn.execute("delete from rest_required_snapshots where month = ?", (month,))
    runs = conn.execute(
        "select run_id, work_date from runs where month = ? and sync_status in ('SYNCED', 'HASH_MISMATCH') order by work_date, run_id",
        (month,),
    ).fetchall()
    users = conn.execute("select user_id from daily_attendance where month = ? group by user_id", (month,)).fetchall()
    for run in runs:
        for user in users:
            count = conn.execute(
                """
                select count(distinct work_date)
                from daily_attendance
                where month = ?
                  and user_id = ?
                  and work_date <= ?
                  and effective_attendance_day = 1
                """,
                (month, user["user_id"], run["work_date"]),
            ).fetchone()[0]
            if count >= REST_REQUIRED_THRESHOLD_DAYS:
                conn.execute(
                    """
                    insert or replace into rest_required_snapshots (
                        run_id, user_id, work_date, month, effective_attendance_days, threshold_days
                    )
                    values (?, ?, ?, ?, ?, ?)
                    """,
                    (run["run_id"], user["user_id"], run["work_date"], month, count, REST_REQUIRED_THRESHOLD_DAYS),
                )


def _read_raw_rows(raw_path: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    metadata: dict[str, Any] = {}
    with gzip.open(raw_path, "rt", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            payload = json.loads(line)
            if not isinstance(payload, dict):
                continue
            if payload.get("type") == "metadata":
                metadata = payload
            elif payload.get("type") == "employee_attendance":
                rows.append(payload)
    return rows, metadata


def _manifest_stats(manifest: Mapping[str, Any], metadata: Mapping[str, Any]) -> Mapping[str, Any]:
    stats = manifest.get("stats")
    if isinstance(stats, Mapping):
        return stats
    stats = metadata.get("stats")
    return stats if isinstance(stats, Mapping) else {}


def _record_success(row: Mapping[str, Any]) -> bool:
    derived = row.get("derived", {}) if isinstance(row.get("derived"), Mapping) else {}
    if "record_success" in derived:
        return bool(derived["record_success"])
    final = _final_payload(row.get("record"))
    return int(final.get("returncode", 1)) == 0 and bool(final.get("payload", {}).get("success"))


def _summary_success(row: Mapping[str, Any]) -> bool:
    derived = row.get("derived", {}) if isinstance(row.get("derived"), Mapping) else {}
    if "summary_success" in derived:
        return bool(derived["summary_success"])
    final = _final_payload(row.get("summary"))
    return int(final.get("returncode", 1)) == 0 and bool(final.get("payload", {}).get("success"))


def _record_list_from_row(row: Mapping[str, Any]) -> list[Any]:
    direct = row.get("record_list")
    if isinstance(direct, list):
        return direct
    payload = _final_payload(row.get("record")).get("payload", {})
    result = payload.get("result", {}) if isinstance(payload, Mapping) else {}
    record_list = result.get("recordList", []) if isinstance(result, Mapping) else []
    return record_list if isinstance(record_list, list) else []


def _summary_payload(row: Mapping[str, Any]) -> Mapping[str, Any]:
    payload = _final_payload(row.get("summary")).get("payload", {})
    return payload if isinstance(payload, Mapping) else {}


def _final_payload(value: Any) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        return {}
    final = value.get("final", value)
    return final if isinstance(final, Mapping) else {}


def _failure_reason(value: Any) -> str:
    final = _final_payload(value)
    payload = final.get("payload", {}) if isinstance(final, Mapping) else {}
    error = payload.get("error", {}) if isinstance(payload, Mapping) else {}
    if isinstance(error, Mapping):
        return str(error.get("server_error_code") or error.get("message") or error.get("reason") or "")
    return ""


def _selected_month_dirs(*, root: Path, month: str | None, all_months: bool) -> list[Path]:
    if month:
        path = root / month
        return [path] if path.exists() else []
    if all_months:
        return sorted(path for path in root.glob("20[0-9][0-9][0-9][0-9]") if path.is_dir())
    return []


def _resolve_archive_path(month_dir: Path, value: Any) -> Path | None:
    if not value:
        return None
    path = Path(str(value))
    return path if path.is_absolute() else month_dir / path


def _run_id_from_archive_path(path: Path, suffix: str) -> str:
    name = path.name
    return name[: -len(suffix)] if name.endswith(suffix) else path.stem


def _work_date_from_run_id(run_id: str) -> str | None:
    parts = run_id.split("_")
    for part in parts:
        if len(part) == 8 and part.isdigit():
            return f"{part[:4]}-{part[4:6]}-{part[6:8]}"
    return None


def _month_from_run_id(run_id: str) -> str:
    work_date = _work_date_from_run_id(run_id)
    return work_date[:7].replace("-", "") if work_date else ""


def _run_type_from_run_id(run_id: str) -> str:
    parts = run_id.split("_")
    return parts[1] if len(parts) >= 2 and parts[1] in {"morning", "evening"} else ""


def _summary_child_date(child: Mapping[str, Any]) -> str | None:
    extension = child.get("extension", {})
    if isinstance(extension, Mapping) and extension.get("date"):
        return str(extension["date"])
    name = str(child.get("name") or "")
    for token in name.split():
        if len(token) == 10 and token[4] == "-" and token[7] == "-":
            return token
    return None


def _is_summary_anomaly_item(item: Mapping[str, Any]) -> bool:
    text = f"{item.get('id') or ''} {item.get('name') or ''}".lower()
    return any(token.lower() in text for token in SUMMARY_TODAY_ANOMALY_TOKENS)


def _audit(
    conn: sqlite3.Connection,
    *,
    run_id: str | None,
    event_type: str,
    status: str,
    message: str,
    source_path: Path | None,
) -> None:
    source_path_text = str(source_path or "")
    conn.execute(
        """
        delete from sync_audit
        where coalesce(run_id, '') = ?
          and event_type = ?
          and source_path = ?
        """,
        (run_id or "", event_type, source_path_text),
    )
    conn.execute(
        """
        insert into sync_audit (run_id, event_type, status, message, source_path, created_at)
        values (?, ?, ?, ?, ?, ?)
        """,
        (run_id, event_type, status, message, source_path_text, _now_iso()),
    )


def _int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _str_or_none(value: Any) -> str | None:
    return None if value in (None, "") else str(value)


def _now_iso() -> str:
    return datetime.now().astimezone().isoformat()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Sync KMFA S19 OneDrive attendance archives into a private SQLite ledger.")
    scope = parser.add_mutually_exclusive_group()
    scope.add_argument("--all", action="store_true", help="Sync every YYYYMM archive directory.")
    scope.add_argument("--month", help="Sync one YYYYMM archive directory.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--validate", action="store_true")
    parser.add_argument("--db-path", default=str(DEFAULT_LEDGER_PATH))
    parser.add_argument("--onedrive-root", default=ONEDRIVE_ROOT)
    args = parser.parse_args(argv)
    db_path = Path(args.db_path)
    if args.validate:
        result = validate_ledger(db_path=db_path)
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
        return 0 if result["status"] == "PASS" else 2
    result = sync_archives_to_ledger(
        onedrive_root=Path(args.onedrive_root),
        db_path=db_path,
        month=args.month,
        all_months=bool(args.all),
        dry_run=bool(args.dry_run),
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] in {"DRY_RUN", "SYNCED", "SYNCED_WITH_ERRORS"} else 2


if __name__ == "__main__":
    sys.exit(main())
