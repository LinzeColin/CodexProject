from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Iterable


SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS run_log (
  run_id TEXT PRIMARY KEY,
  run_time_bj TEXT NOT NULL,
  run_time_au TEXT NOT NULL,
  schedule_slot TEXT NOT NULL,
  model_profile TEXT NOT NULL,
  status TEXT NOT NULL,
  data_quality_status TEXT NOT NULL,
  notification_status TEXT,
  notes TEXT,
  report_path TEXT,
  offline_html_path TEXT,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS asset_master (
  asset_id TEXT PRIMARY KEY,
  asset_code TEXT NOT NULL UNIQUE,
  asset_name TEXT NOT NULL,
  asset_type TEXT NOT NULL,
  market TEXT,
  fund_company TEXT,
  risk_level TEXT,
  is_excluded INTEGER NOT NULL DEFAULT 0,
  exclusion_reason TEXT
);

CREATE TABLE IF NOT EXISTS source_log (
  source_id TEXT PRIMARY KEY,
  run_id TEXT NOT NULL,
  asset_id TEXT,
  source_name TEXT NOT NULL,
  source_type TEXT NOT NULL,
  source_priority INTEGER NOT NULL,
  url_or_path TEXT,
  observed_at TEXT,
  fetched_at TEXT NOT NULL,
  evidence_level TEXT NOT NULL,
  field_list TEXT NOT NULL,
  fallback_aggregated INTEGER NOT NULL DEFAULT 0,
  conflict_group TEXT,
  FOREIGN KEY (run_id) REFERENCES run_log(run_id)
);

CREATE TABLE IF NOT EXISTS fund_nav_snapshot (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  run_id TEXT NOT NULL,
  asset_id TEXT NOT NULL,
  nav_date TEXT NOT NULL,
  nav REAL,
  accumulated_nav REAL,
  daily_return REAL,
  nav_source_id TEXT,
  freshness_status TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS market_kline_snapshot (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  run_id TEXT NOT NULL,
  asset_id TEXT NOT NULL,
  bar_interval TEXT NOT NULL,
  start_time TEXT NOT NULL,
  end_time TEXT NOT NULL,
  open REAL,
  high REAL,
  low REAL,
  close REAL,
  volume REAL,
  turnover REAL,
  source_id TEXT
);

CREATE TABLE IF NOT EXISTS fund_rule_snapshot (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  run_id TEXT NOT NULL,
  asset_id TEXT NOT NULL,
  subscription_status TEXT,
  redemption_status TEXT,
  cutoff_time TEXT,
  confirm_lag TEXT,
  redeem_lag TEXT,
  subscription_fee REAL,
  redemption_fee REAL,
  management_fee REAL,
  custody_fee REAL,
  sales_service_fee REAL,
  min_purchase_amount REAL,
  subscription_fee_schedule TEXT,
  redemption_fee_schedule TEXT,
  fee_schedule_as_of TEXT,
  fee_schedule_note TEXT,
  alipay_trade_status TEXT,
  moomoo_trade_status TEXT,
  platform_trade_note TEXT,
  source_id TEXT
);

CREATE TABLE IF NOT EXISTS position_snapshot (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  run_id TEXT NOT NULL,
  asset_id TEXT NOT NULL,
  platform TEXT NOT NULL,
  current_amount REAL,
  current_weight REAL,
  cost_basis REAL,
  unrealized_pnl REAL,
  imported_by TEXT NOT NULL,
  source_id TEXT
);

CREATE TABLE IF NOT EXISTS baseline_snapshot (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  run_id TEXT NOT NULL,
  asset_id TEXT NOT NULL,
  baseline_weight REAL NOT NULL,
  baseline_kind TEXT NOT NULL,
  reference_run_id TEXT,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS score_snapshot (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  run_id TEXT NOT NULL,
  asset_id TEXT NOT NULL,
  total_score REAL NOT NULL,
  data_score REAL NOT NULL,
  timeliness_score REAL NOT NULL,
  source_score REAL NOT NULL,
  return_score REAL NOT NULL,
  risk_score REAL NOT NULL,
  executable_score REAL NOT NULL,
  evidence_coverage REAL NOT NULL,
  grade TEXT NOT NULL,
  hard_block_reason TEXT
);

CREATE TABLE IF NOT EXISTS recommendation_snapshot (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  run_id TEXT NOT NULL,
  asset_id TEXT NOT NULL,
  rank INTEGER,
  target_weight REAL,
  current_weight REAL,
  deviation REAL,
  action_label TEXT NOT NULL,
  trigger_reason TEXT NOT NULL,
  next_check_by TEXT,
  manual_review_required INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS comparison_snapshot (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  run_id TEXT NOT NULL,
  asset_id TEXT NOT NULL,
  compare_type TEXT NOT NULL,
  base_run_id TEXT,
  delta_rank REAL,
  delta_score REAL,
  delta_weight REAL,
  top5_changed INTEGER,
  key_field_sigma REAL
);

CREATE TABLE IF NOT EXISTS audit_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  run_id TEXT NOT NULL,
  event_type TEXT NOT NULL,
  severity TEXT NOT NULL,
  message TEXT NOT NULL,
  context_json TEXT,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS notification_log (
  notification_id TEXT PRIMARY KEY,
  run_id TEXT NOT NULL,
  channel TEXT NOT NULL,
  severity TEXT NOT NULL,
  title TEXT NOT NULL,
  body_path TEXT NOT NULL,
  send_status TEXT NOT NULL,
  sent_at TEXT,
  error_message TEXT
);

CREATE TABLE IF NOT EXISTS missing_data_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  run_id TEXT NOT NULL,
  asset_id TEXT,
  field_name TEXT NOT NULL,
  severity TEXT NOT NULL,
  reason TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS manual_review_queue (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  run_id TEXT NOT NULL,
  asset_id TEXT,
  reason TEXT NOT NULL,
  action_blocked TEXT NOT NULL,
  status TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS manual_review_decision (
  review_id INTEGER PRIMARY KEY,
  run_id TEXT NOT NULL,
  decision TEXT NOT NULL,
  note TEXT,
  saved_at TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS conflict_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  run_id TEXT NOT NULL,
  asset_id TEXT,
  field_name TEXT NOT NULL,
  conflict_note TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS decision_record (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  run_id TEXT NOT NULL,
  asset_id TEXT,
  decision_type TEXT NOT NULL,
  decision TEXT NOT NULL,
  rationale TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS rebalance_event_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  run_id TEXT NOT NULL,
  trigger_reason TEXT NOT NULL,
  severity TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS automation_tick_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  tick_time_bj TEXT NOT NULL,
  tick_time_au TEXT NOT NULL,
  due_slot TEXT,
  action TEXT NOT NULL,
  run_id TEXT,
  dry_run INTEGER NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS source_evidence_audit_snapshot (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  audit_run_id TEXT NOT NULL,
  generated_at TEXT NOT NULL,
  area TEXT NOT NULL,
  row_id TEXT,
  field TEXT NOT NULL,
  source_file TEXT NOT NULL,
  raw_value TEXT,
  evidence_ref TEXT,
  ref_type TEXT NOT NULL,
  status TEXT NOT NULL,
  message TEXT NOT NULL,
  resolved_path TEXT,
  sha256 TEXT,
  size_bytes TEXT,
  mtime TEXT,
  created_at TEXT NOT NULL
);
"""


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(db_path: Path) -> None:
    with connect(db_path) as conn:
        conn.executescript(SCHEMA)
        _ensure_columns(
            conn,
            "fund_rule_snapshot",
            {
                "subscription_fee_schedule": "TEXT",
                "redemption_fee_schedule": "TEXT",
                "fee_schedule_as_of": "TEXT",
                "fee_schedule_note": "TEXT",
                "alipay_trade_status": "TEXT",
                "moomoo_trade_status": "TEXT",
                "platform_trade_note": "TEXT",
            },
        )


def _ensure_columns(conn: sqlite3.Connection, table: str, columns: dict[str, str]) -> None:
    existing = {row["name"] for row in conn.execute(f"PRAGMA table_info({table})")}
    for name, ddl in columns.items():
        if name not in existing:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {name} {ddl}")


def insert_row(conn: sqlite3.Connection, table: str, row: dict[str, Any]) -> None:
    columns = list(row)
    placeholders = ", ".join(["?"] * len(columns))
    names = ", ".join(columns)
    values = [row[column] for column in columns]
    conn.execute(f"INSERT INTO {table} ({names}) VALUES ({placeholders})", values)


def upsert_asset(conn: sqlite3.Connection, row: dict[str, Any]) -> None:
    conn.execute(
        """
        INSERT INTO asset_master (
            asset_id, asset_code, asset_name, asset_type, market,
            fund_company, risk_level, is_excluded, exclusion_reason
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(asset_code) DO NOTHING
        """,
        (
            row["asset_id"],
            row["asset_code"],
            row["asset_name"],
            row["asset_type"],
            row.get("market"),
            row.get("fund_company"),
            row.get("risk_level"),
            int(row.get("is_excluded", 0)),
            row.get("exclusion_reason"),
        ),
    )


def latest_run_id(conn: sqlite3.Connection) -> str | None:
    row = conn.execute(
        "SELECT run_id FROM run_log ORDER BY created_at DESC, rowid DESC LIMIT 1"
    ).fetchone()
    return row["run_id"] if row else None


def fetch_all(conn: sqlite3.Connection, query: str, params: Iterable[Any] = ()) -> list[sqlite3.Row]:
    return list(conn.execute(query, tuple(params)).fetchall())
