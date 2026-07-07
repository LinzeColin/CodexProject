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
