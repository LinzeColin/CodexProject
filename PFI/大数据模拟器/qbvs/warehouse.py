from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

import pandas as pd

from qbvs.repository import summarize_by_strategy_market


SCHEMA_VERSION = 1


def init_warehouse(db_path: Path | str) -> Path:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as conn:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS meta (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS runs (
                run_dir TEXT PRIMARY KEY,
                validation_results_path TEXT,
                strategy_summary_path TEXT,
                task_status_path TEXT,
                pdf_count INTEGER DEFAULT 0,
                imported_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS validation_results (
                row_id TEXT PRIMARY KEY,
                run_dir TEXT NOT NULL,
                strategy_id TEXT,
                symbol TEXT,
                market TEXT,
                window_label TEXT,
                start TEXT,
                end TEXT,
                passes_user_floor INTEGER,
                total_return_gap REAL,
                annualized_return_gap REAL,
                drawdown_improvement REAL,
                strategy_total_return REAL,
                buy_hold_total_return REAL,
                strategy_max_drawdown REAL,
                buy_hold_max_drawdown REAL,
                strategy_var_5 REAL,
                strategy_cvar_5 REAL,
                quality_score REAL,
                quality_grade TEXT,
                task_id TEXT,
                error TEXT,
                raw_json TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS strategy_summaries (
                row_id TEXT PRIMARY KEY,
                run_dir TEXT NOT NULL,
                strategy_id TEXT,
                samples INTEGER,
                pass_rate REAL,
                avg_total_gap REAL,
                avg_annualized_gap REAL,
                avg_drawdown_improvement REAL,
                avg_var_5 REAL,
                avg_cvar_5 REAL,
                raw_json TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS strategy_market_summary (
                strategy_id TEXT NOT NULL,
                market TEXT NOT NULL,
                samples INTEGER,
                pass_rate REAL,
                avg_total_gap REAL,
                avg_annualized_gap REAL,
                avg_drawdown_improvement REAL,
                avg_var_5 REAL,
                avg_cvar_5 REAL,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (strategy_id, market)
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_results_strategy_market ON validation_results(strategy_id, market)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_results_symbol ON validation_results(symbol)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_results_quality ON validation_results(quality_score)")
        conn.execute("INSERT OR REPLACE INTO meta(key, value) VALUES('schema_version', ?)", (str(SCHEMA_VERSION),))
    return path


def import_runs_to_warehouse(runs_dir: Path | str, db_path: Path | str) -> dict[str, int]:
    db = init_warehouse(db_path)
    root = Path(runs_dir)
    run_count = 0
    result_rows = 0
    summary_rows = 0
    with sqlite3.connect(db) as conn:
        for result_path in sorted(root.glob("**/validation_results.csv")):
            run_dir = result_path.parent
            summary_path = run_dir / "strategy_summary.csv"
            status_path = run_dir / "task_status.csv"
            pdf_count = len(list(run_dir.glob("*.pdf")))
            conn.execute(
                """
                INSERT OR REPLACE INTO runs(run_dir, validation_results_path, strategy_summary_path, task_status_path, pdf_count)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    str(run_dir),
                    str(result_path),
                    str(summary_path) if summary_path.exists() else "",
                    str(status_path) if status_path.exists() else "",
                    pdf_count,
                ),
            )
            run_count += 1
            results = _read_csv_safely(result_path)
            for index, row in results.iterrows():
                conn.execute(
                    """
                    INSERT OR REPLACE INTO validation_results(
                        row_id, run_dir, strategy_id, symbol, market, window_label, start, end,
                        passes_user_floor, total_return_gap, annualized_return_gap, drawdown_improvement,
                        strategy_total_return, buy_hold_total_return, strategy_max_drawdown, buy_hold_max_drawdown,
                        strategy_var_5, strategy_cvar_5, quality_score, quality_grade, task_id, error, raw_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    _result_tuple(str(run_dir), index, row),
                )
                result_rows += 1
            if summary_path.exists():
                summaries = _read_csv_safely(summary_path)
                for index, row in summaries.iterrows():
                    conn.execute(
                        """
                        INSERT OR REPLACE INTO strategy_summaries(
                            row_id, run_dir, strategy_id, samples, pass_rate, avg_total_gap,
                            avg_annualized_gap, avg_drawdown_improvement, avg_var_5, avg_cvar_5, raw_json
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        _summary_tuple(str(run_dir), index, row),
                    )
                    summary_rows += 1
        refresh_warehouse_market_summary(conn)
    return {"runs": run_count, "validation_results": result_rows, "strategy_summaries": summary_rows}


def refresh_warehouse_market_summary(conn: sqlite3.Connection) -> int:
    frame = pd.read_sql_query("SELECT * FROM validation_results", conn)
    summary = summarize_by_strategy_market(frame)
    conn.execute("DELETE FROM strategy_market_summary")
    for _, row in summary.iterrows():
        conn.execute(
            """
            INSERT OR REPLACE INTO strategy_market_summary(
                strategy_id, market, samples, pass_rate, avg_total_gap, avg_annualized_gap,
                avg_drawdown_improvement, avg_var_5, avg_cvar_5
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                _text(row.get("strategy_id")),
                _text(row.get("market")),
                _int(row.get("samples")),
                _float(row.get("pass_rate")),
                _float(row.get("avg_total_gap")),
                _float(row.get("avg_annualized_gap")),
                _float(row.get("avg_drawdown_improvement")),
                _float(row.get("avg_var_5")),
                _float(row.get("avg_cvar_5")),
            ),
        )
    return len(summary)


def export_warehouse_tables(db_path: Path | str, output_dir: Path | str) -> dict[str, Path]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    paths = {}
    with sqlite3.connect(db_path) as conn:
        for table in ["runs", "validation_results", "strategy_summaries", "strategy_market_summary"]:
            frame = pd.read_sql_query(f"SELECT * FROM {table}", conn)
            path = output / f"{table}.csv"
            frame.to_csv(path, index=False)
            paths[table] = path
    return paths


def warehouse_stats(db_path: Path | str) -> dict[str, Any]:
    with sqlite3.connect(db_path) as conn:
        tables = ["runs", "validation_results", "strategy_summaries", "strategy_market_summary"]
        stats = {}
        for table in tables:
            stats[table] = int(conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
        stats["db_path"] = str(db_path)
        return stats


def _read_csv_safely(path: Path) -> pd.DataFrame:
    try:
        return pd.read_csv(path)
    except pd.errors.EmptyDataError:
        return pd.DataFrame()


def _result_tuple(run_dir: str, index: int, row: pd.Series) -> tuple[Any, ...]:
    row_id = _row_id(run_dir, index, row)
    return (
        row_id,
        run_dir,
        _text(row.get("strategy_id")),
        _text(row.get("symbol")),
        _text(row.get("market")),
        _text(row.get("window_label")),
        _text(row.get("start")),
        _text(row.get("end")),
        _bool_int(row.get("passes_user_floor")),
        _float(row.get("total_return_gap")),
        _float(row.get("annualized_return_gap")),
        _float(row.get("drawdown_improvement")),
        _float(row.get("strategy_total_return")),
        _float(row.get("buy_hold_total_return")),
        _float(row.get("strategy_max_drawdown")),
        _float(row.get("buy_hold_max_drawdown")),
        _float(row.get("strategy_var_5")),
        _float(row.get("strategy_cvar_5")),
        _float(row.get("quality_score")),
        _text(row.get("quality_grade")),
        _text(row.get("task_id")),
        _text(row.get("error")),
        json.dumps(row.dropna().to_dict(), ensure_ascii=False, default=str),
    )


def _summary_tuple(run_dir: str, index: int, row: pd.Series) -> tuple[Any, ...]:
    row_id = f"{run_dir}:summary:{index}:{_text(row.get('strategy_id'))}"
    return (
        row_id,
        run_dir,
        _text(row.get("strategy_id")),
        _int(row.get("samples")),
        _float(row.get("pass_rate")),
        _float(row.get("avg_total_gap")),
        _float(row.get("avg_annualized_gap")),
        _float(row.get("avg_drawdown_improvement")),
        _float(row.get("avg_var_5")),
        _float(row.get("avg_cvar_5")),
        json.dumps(row.dropna().to_dict(), ensure_ascii=False, default=str),
    )


def _row_id(run_dir: str, index: int, row: pd.Series) -> str:
    task_id = _text(row.get("task_id"))
    if task_id:
        return f"{run_dir}:task:{task_id}"
    return f"{run_dir}:row:{index}:{_text(row.get('strategy_id'))}:{_text(row.get('symbol'))}:{_text(row.get('window_label'))}"


def _text(value: Any) -> str:
    if value is None or pd.isna(value):
        return ""
    return str(value)


def _float(value: Any) -> float | None:
    if value is None or pd.isna(value) or value == "":
        return None
    return float(value)


def _int(value: Any) -> int | None:
    if value is None or pd.isna(value) or value == "":
        return None
    return int(float(value))


def _bool_int(value: Any) -> int | None:
    if value is None or pd.isna(value) or value == "":
        return None
    if isinstance(value, str):
        return 1 if value.lower() in {"true", "1", "yes"} else 0
    return 1 if bool(value) else 0
