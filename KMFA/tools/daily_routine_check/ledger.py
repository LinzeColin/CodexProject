from __future__ import annotations

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Any

SCHEMA = """
CREATE TABLE IF NOT EXISTS run_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  run_id TEXT NOT NULL,
  created_at TEXT NOT NULL,
  event_type TEXT NOT NULL,
  payload_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS routine_check_results (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  event_key TEXT UNIQUE,
  check_date TEXT NOT NULL,
  rule_id TEXT NOT NULL,
  status TEXT NOT NULL,
  group_name TEXT NOT NULL,
  artifact_name TEXT NOT NULL,
  matched_message_id TEXT,
  confidence REAL,
  payload_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS source_runs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  run_id TEXT UNIQUE,
  created_at TEXT NOT NULL,
  payload_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS cash_risk_results (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  event_key TEXT UNIQUE,
  report_date TEXT NOT NULL,
  risk_level TEXT NOT NULL,
  total_available_cash REAL,
  hard_threshold REAL,
  soft_threshold REAL,
  source_message_id TEXT,
  source_file_sha256 TEXT,
  confidence REAL,
  payload_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS source_messages (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  message_key TEXT UNIQUE,
  group_name TEXT NOT NULL,
  message_id TEXT NOT NULL,
  message_time TEXT,
  sender_name TEXT,
  payload_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS source_files (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  file_key TEXT UNIQUE,
  group_name TEXT NOT NULL,
  message_id TEXT,
  sha256 TEXT,
  payload_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS document_candidates (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  candidate_key TEXT UNIQUE,
  check_date TEXT NOT NULL,
  document_type TEXT NOT NULL,
  confidence REAL,
  payload_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS routine_rules_snapshot (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  snapshot_key TEXT UNIQUE,
  run_id TEXT NOT NULL,
  payload_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS ocr_jobs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  job_key TEXT UNIQUE,
  status TEXT NOT NULL,
  payload_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS ocr_extractions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  extraction_key TEXT UNIQUE,
  document_type TEXT NOT NULL,
  confidence REAL,
  payload_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS cash_account_snapshots (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  snapshot_key TEXT UNIQUE,
  report_date TEXT NOT NULL,
  total_available_cash REAL,
  payload_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS cash_flow_entries (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  entry_key TEXT UNIQUE,
  flow_date TEXT,
  payload_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS notification_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  idempotency_key TEXT UNIQUE,
  created_at TEXT NOT NULL,
  event_type TEXT NOT NULL,
  target_label TEXT NOT NULL,
  status TEXT NOT NULL,
  payload_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS data_quality_issues (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  issue_key TEXT UNIQUE,
  created_at TEXT NOT NULL,
  issue_type TEXT NOT NULL,
  severity TEXT NOT NULL,
  payload_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS git_sync_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  event_key TEXT UNIQUE,
  created_at TEXT NOT NULL,
  status TEXT NOT NULL,
  payload_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS cleanup_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  event_key TEXT UNIQUE,
  created_at TEXT NOT NULL,
  status TEXT NOT NULL,
  payload_json TEXT NOT NULL
);
"""


def connect(db_path: str | Path) -> sqlite3.Connection:
    p = Path(db_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(p))
    conn.executescript(SCHEMA)
    conn.commit()
    return conn


def write_run_log(conn: sqlite3.Connection, run_id: str, payload: dict[str, Any]) -> None:
    conn.execute(
        "INSERT INTO run_log (run_id, created_at, event_type, payload_json) VALUES (?, ?, ?, ?)",
        (
            run_id,
            datetime.now().isoformat(timespec="seconds"),
            "routine_check_run",
            json.dumps(payload, ensure_ascii=False, sort_keys=True),
        ),
    )
    conn.commit()


def dump_json(value: dict[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def write_run_payload(conn: sqlite3.Connection, run_id: str, payload: dict[str, Any]) -> None:
    created_at = datetime.now().isoformat(timespec="seconds")
    write_run_log(conn, run_id, payload)
    conn.execute(
        "INSERT OR REPLACE INTO source_runs (run_id, created_at, payload_json) VALUES (?, ?, ?)",
        (run_id, created_at, dump_json(payload)),
    )

    for result in payload.get("results", []):
        event_key = f"{result.get('check_date')}:{result.get('rule_id')}"
        conn.execute(
            """
            INSERT OR REPLACE INTO routine_check_results
              (event_key, check_date, rule_id, status, group_name, artifact_name, matched_message_id, confidence, payload_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event_key,
                result.get("check_date"),
                result.get("rule_id"),
                result.get("status"),
                result.get("group_name"),
                result.get("artifact_name"),
                result.get("matched_message_id"),
                result.get("confidence"),
                dump_json(result),
            ),
        )

    cash = payload.get("cash_risk_result")
    if cash:
        event_key = f"{cash.get('report_date')}:{cash.get('risk_level')}:{cash.get('source_message_id')}"
        conn.execute(
            """
            INSERT OR REPLACE INTO cash_risk_results
              (event_key, report_date, risk_level, total_available_cash, hard_threshold, soft_threshold,
               source_message_id, source_file_sha256, confidence, payload_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event_key,
                cash.get("report_date"),
                cash.get("risk_level"),
                cash.get("total_available_cash"),
                cash.get("hard_threshold"),
                cash.get("soft_threshold"),
                cash.get("source_message_id"),
                cash.get("source_file_sha256"),
                cash.get("confidence"),
                dump_json(cash),
            ),
        )
        if cash.get("total_available_cash") is not None:
            conn.execute(
                """
                INSERT OR REPLACE INTO cash_account_snapshots
                  (snapshot_key, report_date, total_available_cash, payload_json)
                VALUES (?, ?, ?, ?)
                """,
                (
                    f"{cash.get('report_date')}:{cash.get('source_message_id')}",
                    cash.get("report_date"),
                    cash.get("total_available_cash"),
                    dump_json(cash),
                ),
            )

    for event in payload.get("notification_events", []):
        event_key = event.get("idempotency_key") or f"{event.get('event_type')}:{run_id}"
        conn.execute(
            """
            INSERT OR REPLACE INTO notification_events
              (idempotency_key, created_at, event_type, target_label, status, payload_json)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                event_key,
                created_at,
                event.get("event_type", ""),
                event.get("target_label", ""),
                "QUEUED_OR_LOGGED",
                dump_json(event),
            ),
        )

    for issue in payload.get("data_quality_issues", []):
        issue_key = ":".join([
            issue.get("issue_type", ""),
            issue.get("group_name", ""),
            issue.get("check_date", ""),
            issue.get("issue_code", ""),
        ])
        conn.execute(
            """
            INSERT OR REPLACE INTO data_quality_issues
              (issue_key, created_at, issue_type, severity, payload_json)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                issue_key,
                created_at,
                issue.get("issue_type", ""),
                "WARN",
                dump_json(issue),
            ),
        )
    conn.commit()


def write_cleanup_event(conn: sqlite3.Connection, payload: dict[str, Any]) -> None:
    created_at = datetime.now().isoformat(timespec="seconds")
    event_key = payload.get("event_key") or f"cleanup:{created_at}"
    conn.execute(
        """
        INSERT OR REPLACE INTO cleanup_events
          (event_key, created_at, status, payload_json)
        VALUES (?, ?, ?, ?)
        """,
        (event_key, created_at, payload.get("status", "DONE"), dump_json(payload)),
    )
    conn.commit()
