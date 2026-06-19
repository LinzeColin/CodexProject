from __future__ import annotations

import json
import os
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from pfi_os.config import DATA_DIR
from pfi_os.integrations.research_bus import initialize_research_bus


DEFAULT_CONSUMER_DB_PATHS = (
    Path("~/Documents/Codex/2026-06-04/files-mentioned-by-the-user-01/data/local/consumption.sqlite"),
    Path("~/Documents/Codex/2026-06-04/files-mentioned-by-the-user-01/outputs/data/consumption.sqlite"),
    DATA_DIR / "external" / "consumerBehavior" / "consumption.sqlite",
)


@dataclass(frozen=True)
class ConsumerBehaviorSyncResult:
    synced_at: str
    db_path: str
    source_db_count: int
    records: int
    events: int
    warnings: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "synced_at": self.synced_at,
            "db_path": self.db_path,
            "source_db_count": self.source_db_count,
            "records": self.records,
            "events": self.events,
            "warnings": list(self.warnings),
        }


def sync_consumer_behavior_state(
    source_dbs: list[str | Path] | tuple[str | Path, ...] | None = None,
    *,
    bus_db_path: Path | str | None = None,
) -> ConsumerBehaviorSyncResult:
    target_db = initialize_research_bus(bus_db_path)
    candidates = _configured_source_dbs(source_dbs)
    states = []
    warnings: list[str] = []
    for db_path in candidates:
        if not db_path.exists():
            continue
        try:
            states.append(read_consumer_behavior_state(db_path))
        except Exception as exc:
            warnings.append(f"读取消费行为数据库失败：{db_path}：{exc}")
    with sqlite3.connect(target_db, timeout=30) as conn:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=30000")
        for state in states:
            _upsert_consumer_state(conn, state)
        _upsert_system_state(
            conn,
            "ConsumptionAnalysisSystem",
            "Ready" if states else "ConfiguredNoData",
            "\n".join(str(path) for path in candidates),
            {"source_db_count": len(states), "purpose": "消费行为系统内部状态只读同步"},
        )
        _record_event(conn, "consumer_behavior_sync", "ConsumptionAnalysisSystem", "ResearchBus", "success", f"states={len(states)}")
    return ConsumerBehaviorSyncResult(synced_at=_now(), db_path=str(target_db), source_db_count=len(states), records=len(states), events=1, warnings=tuple(warnings))


def read_consumer_behavior_state(path: Path | str) -> dict[str, Any]:
    db_path = Path(path).expanduser()
    uri = f"file:{db_path}?mode=ro"
    conn = sqlite3.connect(uri, uri=True, timeout=30)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA busy_timeout=30000")
        tables = _table_names(conn)
        run_count = _count_table(conn, "runs", tables)
        transaction_count = _count_table(conn, "transactions", tables)
        ledger_count = _count_table(conn, "transactions_ledger", tables)
        latest_run = _latest_run(conn, tables)
        summary = _summary_metrics(conn, tables)
        risk_counts = _group_counts(conn, "transactions_ledger", "risk_label", tables)
        category_counts = _group_counts(conn, "transactions_ledger", "main_category", tables)
        total_amount = _total_amount(conn, tables)
        manual_review_count = _manual_review_count(conn, tables)
    finally:
        conn.close()
    return {
        "state_id": _state_id(db_path),
        "source_system": "ConsumptionAnalysisSystem",
        "db_path": str(db_path),
        "run_count": run_count,
        "transaction_count": transaction_count,
        "ledger_count": ledger_count,
        "latest_run_id": str(latest_run.get("run_id", "")),
        "latest_generated_at": str(latest_run.get("generated_at", "")),
        "total_amount": total_amount,
        "manual_review_count": manual_review_count,
        "summary": {
            "summary_metrics": summary,
            "risk_counts": risk_counts,
            "category_counts": category_counts,
            "tables": sorted(tables),
        },
        "updated_at": _now(),
    }


def consumer_behavior_state_frame(bus_db_path: Path | str | None = None) -> pd.DataFrame:
    target_db = initialize_research_bus(bus_db_path)
    conn = sqlite3.connect(target_db, timeout=30)
    try:
        rows = conn.execute(
            """
            SELECT source_system, db_path, run_count, transaction_count, ledger_count,
                   latest_run_id, latest_generated_at, total_amount, manual_review_count,
                   summary_json, updated_at
            FROM consumer_behavior_state
            ORDER BY updated_at DESC
            """
        ).fetchall()
    finally:
        conn.close()
    columns = [
        "source_system",
        "db_path",
        "run_count",
        "transaction_count",
        "ledger_count",
        "latest_run_id",
        "latest_generated_at",
        "total_amount",
        "manual_review_count",
        "summary_json",
        "updated_at",
    ]
    return pd.DataFrame(rows, columns=columns)


def _configured_source_dbs(source_dbs: list[str | Path] | tuple[str | Path, ...] | None) -> list[Path]:
    if source_dbs is not None:
        return [Path(item).expanduser() for item in source_dbs]
    configured = os.getenv("PFI_CONSUMER_BEHAVIOR_DB", "").strip()
    if configured:
        return [Path(item).expanduser() for item in configured.split(":") if item.strip()]
    return [path.expanduser() for path in DEFAULT_CONSUMER_DB_PATHS]


def _upsert_consumer_state(conn: sqlite3.Connection, state: dict[str, Any]) -> None:
    conn.execute(
        """
        INSERT INTO consumer_behavior_state(
            state_id, source_system, db_path, run_count, transaction_count, ledger_count,
            latest_run_id, latest_generated_at, total_amount, manual_review_count, summary_json, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(state_id) DO UPDATE SET
            run_count=excluded.run_count,
            transaction_count=excluded.transaction_count,
            ledger_count=excluded.ledger_count,
            latest_run_id=excluded.latest_run_id,
            latest_generated_at=excluded.latest_generated_at,
            total_amount=excluded.total_amount,
            manual_review_count=excluded.manual_review_count,
            summary_json=excluded.summary_json,
            updated_at=excluded.updated_at
        """,
        (
            state["state_id"],
            state["source_system"],
            state["db_path"],
            int(state["run_count"]),
            int(state["transaction_count"]),
            int(state["ledger_count"]),
            state["latest_run_id"],
            state["latest_generated_at"],
            float(state["total_amount"]),
            int(state["manual_review_count"]),
            json.dumps(state["summary"], ensure_ascii=False, sort_keys=True, default=str),
            state["updated_at"],
        ),
    )


def _upsert_system_state(conn: sqlite3.Connection, system_name: str, status: str, root_path: str, summary: dict[str, Any]) -> None:
    conn.execute(
        """
        INSERT INTO system_state(system_name, status, root_path, last_sync_at, summary_json)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(system_name) DO UPDATE SET
            status=excluded.status,
            root_path=excluded.root_path,
            last_sync_at=excluded.last_sync_at,
            summary_json=excluded.summary_json
        """,
        (system_name, status, root_path, _now(), json.dumps(summary, ensure_ascii=False, sort_keys=True)),
    )


def _record_event(conn: sqlite3.Connection, event_type: str, source_system: str, target_system: str, status: str, message: str) -> None:
    conn.execute(
        """
        INSERT INTO sync_events(event_id, event_type, source_system, target_system, status, message, payload_json, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (_state_id(Path(f"{event_type}_{source_system}_{target_system}_{_now()}")), event_type, source_system, target_system, status, message, "{}", _now()),
    )


def _table_names(conn: sqlite3.Connection) -> set[str]:
    return {str(row[0]) for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}


def _count_table(conn: sqlite3.Connection, table: str, tables: set[str]) -> int:
    if table not in tables:
        return 0
    return int(conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])


def _latest_run(conn: sqlite3.Connection, tables: set[str]) -> dict[str, Any]:
    if "runs" not in tables:
        return {}
    row = conn.execute("SELECT run_id, generated_at FROM runs ORDER BY COALESCE(generated_at, created_at, run_id) DESC LIMIT 1").fetchone()
    return dict(row) if row else {}


def _summary_metrics(conn: sqlite3.Connection, tables: set[str]) -> dict[str, str]:
    table = "latest_summary_metrics" if "latest_summary_metrics" in tables else "summary_metrics"
    if table not in tables:
        return {}
    rows = conn.execute(f"SELECT metric, value FROM {table}").fetchall()
    return {str(row["metric"]): str(row["value"]) for row in rows}


def _group_counts(conn: sqlite3.Connection, table: str, column: str, tables: set[str]) -> dict[str, int]:
    if table not in tables:
        return {}
    rows = conn.execute(f"SELECT COALESCE({column}, '') AS label, COUNT(*) AS count FROM {table} GROUP BY COALESCE({column}, '') ORDER BY count DESC LIMIT 20").fetchall()
    return {str(row["label"] or "未标记"): int(row["count"]) for row in rows}


def _total_amount(conn: sqlite3.Connection, tables: set[str]) -> float:
    table = "transactions_ledger" if "transactions_ledger" in tables else "transactions"
    if table not in tables:
        return 0.0
    rows = conn.execute(f"SELECT amount FROM {table}").fetchall()
    total = 0.0
    for row in rows:
        total += _float_amount(row["amount"])
    return total


def _manual_review_count(conn: sqlite3.Connection, tables: set[str]) -> int:
    table = "transactions_ledger" if "transactions_ledger" in tables else "transactions"
    if table not in tables:
        return 0
    return int(conn.execute(f"SELECT COUNT(*) FROM {table} WHERE CAST(COALESCE(needs_manual_review, 0) AS INTEGER) <> 0").fetchone()[0])


def _float_amount(value: object) -> float:
    try:
        return float(str(value or "0").replace(",", "").replace("¥", "").replace("$", "").strip())
    except ValueError:
        return 0.0


def _state_id(path: Path) -> str:
    import hashlib

    return "consumerState_" + hashlib.sha1(str(path).encode("utf-8")).hexdigest()[:20]


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")
