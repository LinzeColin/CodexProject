from __future__ import annotations

import fcntl
import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from .artifacts import public_artifact_ref, sanitize_public_payload, sanitize_public_text
from .boards import BOARD_CONFIGS, BoardConfig
from .evidence import build_evidence_bundle
from .io import atomic_write_json, atomic_write_text
from .markdown_visuals import mermaid_bar, mermaid_pie
from .model_compare import MODEL_COMPARISON_JSON
from .recommendations import apply_public_time_adjusted_match_stakes, display_stake_aud
from .sidecar_pdf import chart_from_items, render_sidecar_pdf
from .visuals import build_visual_summary


SCHEMA_VERSION = 10
REPORT_INDEX_REPORT_LATEST = "report_index_latest.md"
REPORT_INDEX_PDF_LATEST = "report_index_latest.pdf"

SCHEMA_COLUMNS = {
    "report_runs": [
        ("run_id", "run_id TEXT DEFAULT ''"),
        ("status", "status TEXT NOT NULL DEFAULT ''"),
        ("report_date", "report_date TEXT"),
        ("started_at", "started_at TEXT"),
        ("finished_at", "finished_at TEXT"),
        ("technical_ready", "technical_ready INTEGER NOT NULL DEFAULT 0"),
        ("automation_entry_ready", "automation_entry_ready INTEGER NOT NULL DEFAULT 0"),
        ("raw_refresh_ready", "raw_refresh_ready INTEGER NOT NULL DEFAULT 0"),
        ("safety_ready", "safety_ready INTEGER NOT NULL DEFAULT 0"),
        ("portfolio_ready", "portfolio_ready INTEGER NOT NULL DEFAULT 0"),
        ("recommended_new_exposure_aud", "recommended_new_exposure_aud REAL NOT NULL DEFAULT 0"),
        ("time_adjusted_new_exposure_aud", "time_adjusted_new_exposure_aud REAL NOT NULL DEFAULT 0"),
        ("pdf_report", "pdf_report TEXT"),
        ("pdf_output_copy", "pdf_output_copy TEXT"),
        ("dashboard_path", "dashboard_path TEXT"),
        ("dashboard_data_path", "dashboard_data_path TEXT"),
        ("manifest_path", "manifest_path TEXT"),
        ("summary_json", "summary_json TEXT NOT NULL DEFAULT '{}'"),
    ],
    "board_runs": [
        ("run_id", "run_id TEXT NOT NULL DEFAULT ''"),
        ("board_id", "board_id TEXT NOT NULL DEFAULT ''"),
        ("name", "name TEXT NOT NULL DEFAULT ''"),
        ("priority", "priority INTEGER NOT NULL DEFAULT 0"),
        ("ready", "ready INTEGER NOT NULL DEFAULT 0"),
        ("raw_fresh", "raw_fresh INTEGER NOT NULL DEFAULT 0"),
        ("raw_valid", "raw_valid INTEGER NOT NULL DEFAULT 0"),
        ("gate_ready", "gate_ready INTEGER NOT NULL DEFAULT 0"),
        ("report_exists", "report_exists INTEGER NOT NULL DEFAULT 0"),
        ("raw_age_hours", "raw_age_hours REAL"),
        ("missing_json", "missing_json TEXT NOT NULL DEFAULT '[]'"),
        ("validation_errors_json", "validation_errors_json TEXT NOT NULL DEFAULT '[]'"),
    ],
    "recommendations": [
        ("run_id", "run_id TEXT NOT NULL DEFAULT ''"),
        ("board_id", "board_id TEXT NOT NULL DEFAULT ''"),
        ("board_name", "board_name TEXT NOT NULL DEFAULT ''"),
        ("rank", "rank INTEGER NOT NULL DEFAULT 0"),
        ("event_name", "event_name TEXT NOT NULL DEFAULT ''"),
        ("market", "market TEXT NOT NULL DEFAULT ''"),
        ("selection", "selection TEXT NOT NULL DEFAULT ''"),
        ("odds", "odds REAL"),
        ("probability", "probability REAL"),
        ("expected_value", "expected_value REAL"),
        ("stake_aud", "stake_aud REAL NOT NULL DEFAULT 0"),
        ("action", "action TEXT NOT NULL DEFAULT ''"),
        ("raw_json", "raw_json TEXT NOT NULL DEFAULT '{}'"),
    ],
    "report_diffs": [
        ("run_id", "run_id TEXT NOT NULL DEFAULT ''"),
        ("added_count", "added_count INTEGER NOT NULL DEFAULT 0"),
        ("removed_count", "removed_count INTEGER NOT NULL DEFAULT 0"),
        ("changed_count", "changed_count INTEGER NOT NULL DEFAULT 0"),
        ("retained_count", "retained_count INTEGER NOT NULL DEFAULT 0"),
        ("exposure_change_aud", "exposure_change_aud REAL NOT NULL DEFAULT 0"),
        ("raw_json", "raw_json TEXT NOT NULL DEFAULT '{}'"),
    ],
    "board_diffs": [
        ("run_id", "run_id TEXT NOT NULL DEFAULT ''"),
        ("board_id", "board_id TEXT NOT NULL DEFAULT ''"),
        ("board_name", "board_name TEXT NOT NULL DEFAULT ''"),
        ("added_count", "added_count INTEGER NOT NULL DEFAULT 0"),
        ("removed_count", "removed_count INTEGER NOT NULL DEFAULT 0"),
        ("changed_count", "changed_count INTEGER NOT NULL DEFAULT 0"),
        ("retained_count", "retained_count INTEGER NOT NULL DEFAULT 0"),
        ("exposure_change_aud", "exposure_change_aud REAL NOT NULL DEFAULT 0"),
        ("raw_json", "raw_json TEXT NOT NULL DEFAULT '{}'"),
    ],
    "artifacts": [
        ("run_id", "run_id TEXT NOT NULL DEFAULT ''"),
        ("kind", "kind TEXT NOT NULL DEFAULT ''"),
        ("path", "path TEXT NOT NULL DEFAULT ''"),
    ],
    "model_comparisons": [
        ("run_id", "run_id TEXT NOT NULL DEFAULT ''"),
        ("match_name", "match_name TEXT NOT NULL DEFAULT ''"),
        ("consensus_selection", "consensus_selection TEXT NOT NULL DEFAULT ''"),
        ("consensus_probability", "consensus_probability REAL"),
        ("confidence", "confidence TEXT NOT NULL DEFAULT ''"),
        ("max_disagreement", "max_disagreement REAL NOT NULL DEFAULT 0"),
        ("high_divergence", "high_divergence INTEGER NOT NULL DEFAULT 0"),
        ("rating_source", "rating_source TEXT"),
        ("raw_json", "raw_json TEXT NOT NULL DEFAULT '{}'"),
    ],
    "visual_snapshots": [
        ("run_id", "run_id TEXT NOT NULL DEFAULT ''"),
        ("chart_id", "chart_id TEXT NOT NULL DEFAULT ''"),
        ("title", "title TEXT NOT NULL DEFAULT ''"),
        ("kind", "kind TEXT NOT NULL DEFAULT ''"),
        ("item_count", "item_count INTEGER NOT NULL DEFAULT 0"),
        ("raw_json", "raw_json TEXT NOT NULL DEFAULT '{}'"),
    ],
    "source_logs": [
        ("run_id", "run_id TEXT NOT NULL DEFAULT ''"),
        ("source_type", "source_type TEXT NOT NULL DEFAULT ''"),
        ("name", "name TEXT NOT NULL DEFAULT ''"),
        ("url_or_ref", "url_or_ref TEXT NOT NULL DEFAULT ''"),
        ("usage", "usage TEXT NOT NULL DEFAULT ''"),
        ("status", "status TEXT NOT NULL DEFAULT ''"),
        ("status_code", "status_code INTEGER"),
        ("freshness", "freshness TEXT NOT NULL DEFAULT ''"),
        ("evidence_layer", "evidence_layer TEXT NOT NULL DEFAULT ''"),
        ("message", "message TEXT NOT NULL DEFAULT ''"),
        ("raw_json", "raw_json TEXT NOT NULL DEFAULT '{}'"),
    ],
    "audit_logs": [
        ("run_id", "run_id TEXT NOT NULL DEFAULT ''"),
        ("check_name", "check_name TEXT NOT NULL DEFAULT ''"),
        ("status", "status TEXT NOT NULL DEFAULT ''"),
        ("severity", "severity TEXT NOT NULL DEFAULT ''"),
        ("message", "message TEXT NOT NULL DEFAULT ''"),
        ("raw_json", "raw_json TEXT NOT NULL DEFAULT '{}'"),
    ],
    "decision_records": [
        ("run_id", "run_id TEXT NOT NULL DEFAULT ''"),
        ("board_id", "board_id TEXT NOT NULL DEFAULT ''"),
        ("board_name", "board_name TEXT NOT NULL DEFAULT ''"),
        ("rank", "rank INTEGER NOT NULL DEFAULT 0"),
        ("event_name", "event_name TEXT NOT NULL DEFAULT ''"),
        ("market", "market TEXT NOT NULL DEFAULT ''"),
        ("selection", "selection TEXT NOT NULL DEFAULT ''"),
        ("action", "action TEXT NOT NULL DEFAULT ''"),
        ("stake_aud", "stake_aud REAL NOT NULL DEFAULT 0"),
        ("probability", "probability REAL"),
        ("expected_value", "expected_value REAL"),
        ("evidence_layer", "evidence_layer TEXT NOT NULL DEFAULT ''"),
        ("reason", "reason TEXT NOT NULL DEFAULT ''"),
        ("raw_json", "raw_json TEXT NOT NULL DEFAULT '{}'"),
    ],
    "missing_data_logs": [
        ("run_id", "run_id TEXT NOT NULL DEFAULT ''"),
        ("category", "category TEXT NOT NULL DEFAULT ''"),
        ("item", "item TEXT NOT NULL DEFAULT ''"),
        ("severity", "severity TEXT NOT NULL DEFAULT ''"),
        ("status", "status TEXT NOT NULL DEFAULT ''"),
        ("message", "message TEXT NOT NULL DEFAULT ''"),
        ("raw_json", "raw_json TEXT NOT NULL DEFAULT '{}'"),
    ],
    "manual_review_queue": [
        ("run_id", "run_id TEXT NOT NULL DEFAULT ''"),
        ("queue_type", "queue_type TEXT NOT NULL DEFAULT ''"),
        ("item", "item TEXT NOT NULL DEFAULT ''"),
        ("severity", "severity TEXT NOT NULL DEFAULT ''"),
        ("status", "status TEXT NOT NULL DEFAULT ''"),
        ("message", "message TEXT NOT NULL DEFAULT ''"),
        ("raw_json", "raw_json TEXT NOT NULL DEFAULT '{}'"),
    ],
    "automation_runs": [
        ("automation_run_id", "automation_run_id TEXT NOT NULL DEFAULT ''"),
        ("mode", "mode TEXT NOT NULL DEFAULT ''"),
        ("verify_mode", "verify_mode TEXT NOT NULL DEFAULT ''"),
        ("status", "status TEXT NOT NULL DEFAULT ''"),
        ("exit_code", "exit_code INTEGER NOT NULL DEFAULT 0"),
        ("started_at", "started_at TEXT NOT NULL DEFAULT ''"),
        ("finished_at", "finished_at TEXT NOT NULL DEFAULT ''"),
        ("report_run_id", "report_run_id TEXT NOT NULL DEFAULT ''"),
        ("latest_commit_run_id", "latest_commit_run_id TEXT NOT NULL DEFAULT ''"),
        ("formal_report_publish_ready", "formal_report_publish_ready INTEGER NOT NULL DEFAULT 0"),
        ("recurring_automation_ready", "recurring_automation_ready INTEGER NOT NULL DEFAULT 0"),
        ("raw_refresh_ready", "raw_refresh_ready INTEGER NOT NULL DEFAULT 0"),
        ("my_bets_capture_enabled", "my_bets_capture_enabled INTEGER NOT NULL DEFAULT 0"),
        ("my_bets_report_date", "my_bets_report_date TEXT NOT NULL DEFAULT ''"),
        ("my_bets_capture_exit_code", "my_bets_capture_exit_code INTEGER NOT NULL DEFAULT 0"),
        ("my_bets_import_exit_code", "my_bets_import_exit_code INTEGER NOT NULL DEFAULT 0"),
        ("my_bets_raw_text_seen", "my_bets_raw_text_seen INTEGER NOT NULL DEFAULT 0"),
        ("capture_log", "capture_log TEXT NOT NULL DEFAULT ''"),
        ("import_log", "import_log TEXT NOT NULL DEFAULT ''"),
        ("summary_json", "summary_json TEXT NOT NULL DEFAULT '{}'"),
    ],
    "active_timeline_audits": [
        ("audit_id", "audit_id TEXT NOT NULL DEFAULT ''"),
        ("generated_at", "generated_at TEXT NOT NULL DEFAULT ''"),
        ("timezone", "timezone TEXT NOT NULL DEFAULT ''"),
        ("day_count", "day_count INTEGER NOT NULL DEFAULT 0"),
        ("complete_day_count", "complete_day_count INTEGER NOT NULL DEFAULT 0"),
        ("missing_analysis_day_count", "missing_analysis_day_count INTEGER NOT NULL DEFAULT 0"),
        ("missing_report_day_count", "missing_report_day_count INTEGER NOT NULL DEFAULT 0"),
        ("backfill_queue_count", "backfill_queue_count INTEGER NOT NULL DEFAULT 0"),
        ("cadence_ready_for_all_days", "cadence_ready_for_all_days INTEGER NOT NULL DEFAULT 0"),
        ("formal_report_ready_for_all_days", "formal_report_ready_for_all_days INTEGER NOT NULL DEFAULT 0"),
        ("backfill_status", "backfill_status TEXT NOT NULL DEFAULT ''"),
        ("raw_refresh_ready", "raw_refresh_ready INTEGER NOT NULL DEFAULT 0"),
        ("raw_refresh_status", "raw_refresh_status TEXT NOT NULL DEFAULT ''"),
        ("raw_blocker_json", "raw_blocker_json TEXT NOT NULL DEFAULT '{}'"),
        ("payload_json", "payload_json TEXT NOT NULL DEFAULT '{}'"),
    ],
    "available_board_strategy_snapshots": [
        ("strategy_id", "strategy_id TEXT NOT NULL DEFAULT ''"),
        ("generated_at", "generated_at TEXT NOT NULL DEFAULT ''"),
        ("status", "status TEXT NOT NULL DEFAULT ''"),
        ("listed_expected_count", "listed_expected_count INTEGER NOT NULL DEFAULT 0"),
        ("missing_expected_count", "missing_expected_count INTEGER NOT NULL DEFAULT 0"),
        ("route_mismatch_active", "route_mismatch_active INTEGER NOT NULL DEFAULT 0"),
        ("executable_report_allowed", "executable_report_allowed INTEGER NOT NULL DEFAULT 0"),
        ("research_diagnostic_allowed", "research_diagnostic_allowed INTEGER NOT NULL DEFAULT 0"),
        ("payload_json", "payload_json TEXT NOT NULL DEFAULT '{}'"),
    ],
    "position_monitor_snapshots": [
        ("monitor_id", "monitor_id TEXT NOT NULL DEFAULT ''"),
        ("generated_at", "generated_at TEXT NOT NULL DEFAULT ''"),
        ("status", "status TEXT NOT NULL DEFAULT ''"),
        ("report_date", "report_date TEXT NOT NULL DEFAULT ''"),
        ("snapshot_ready", "snapshot_ready INTEGER NOT NULL DEFAULT 0"),
        ("raw_text_exists", "raw_text_exists INTEGER NOT NULL DEFAULT 0"),
        ("public_metrics_available", "public_metrics_available INTEGER NOT NULL DEFAULT 0"),
        ("payload_json", "payload_json TEXT NOT NULL DEFAULT '{}'"),
    ],
}


@contextmanager
def connect_report_db(db_path: Path):
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with schema_migration_lock(db_path):
        conn = sqlite3.connect(db_path)
        try:
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA busy_timeout=5000")
            init_report_db(conn)
            secure_report_db_files(db_path)
            yield conn
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()


def init_report_db(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS schema_meta (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS report_runs (
            run_id TEXT PRIMARY KEY,
            status TEXT NOT NULL,
            report_date TEXT,
            started_at TEXT,
            finished_at TEXT,
            technical_ready INTEGER NOT NULL DEFAULT 0,
            automation_entry_ready INTEGER NOT NULL DEFAULT 0,
            raw_refresh_ready INTEGER NOT NULL DEFAULT 0,
            safety_ready INTEGER NOT NULL DEFAULT 0,
            portfolio_ready INTEGER NOT NULL DEFAULT 0,
            recommended_new_exposure_aud REAL NOT NULL DEFAULT 0,
            time_adjusted_new_exposure_aud REAL NOT NULL DEFAULT 0,
            pdf_report TEXT,
            pdf_output_copy TEXT,
            dashboard_path TEXT,
            dashboard_data_path TEXT,
            manifest_path TEXT,
            summary_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS board_runs (
            run_id TEXT NOT NULL,
            board_id TEXT NOT NULL,
            name TEXT NOT NULL,
            priority INTEGER NOT NULL DEFAULT 0,
            ready INTEGER NOT NULL DEFAULT 0,
            raw_fresh INTEGER NOT NULL DEFAULT 0,
            raw_valid INTEGER NOT NULL DEFAULT 0,
            gate_ready INTEGER NOT NULL DEFAULT 0,
            report_exists INTEGER NOT NULL DEFAULT 0,
            raw_age_hours REAL,
            missing_json TEXT NOT NULL,
            validation_errors_json TEXT NOT NULL,
            PRIMARY KEY (run_id, board_id)
        );

        CREATE TABLE IF NOT EXISTS recommendations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id TEXT NOT NULL,
            board_id TEXT NOT NULL,
            board_name TEXT NOT NULL,
            rank INTEGER NOT NULL,
            event_name TEXT NOT NULL,
            market TEXT NOT NULL,
            selection TEXT NOT NULL,
            odds REAL,
            probability REAL,
            expected_value REAL,
            stake_aud REAL NOT NULL DEFAULT 0,
            action TEXT NOT NULL,
            raw_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS report_diffs (
            run_id TEXT PRIMARY KEY,
            added_count INTEGER NOT NULL DEFAULT 0,
            removed_count INTEGER NOT NULL DEFAULT 0,
            changed_count INTEGER NOT NULL DEFAULT 0,
            retained_count INTEGER NOT NULL DEFAULT 0,
            exposure_change_aud REAL NOT NULL DEFAULT 0,
            raw_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS board_diffs (
            run_id TEXT NOT NULL,
            board_id TEXT NOT NULL,
            board_name TEXT NOT NULL,
            added_count INTEGER NOT NULL DEFAULT 0,
            removed_count INTEGER NOT NULL DEFAULT 0,
            changed_count INTEGER NOT NULL DEFAULT 0,
            retained_count INTEGER NOT NULL DEFAULT 0,
            exposure_change_aud REAL NOT NULL DEFAULT 0,
            raw_json TEXT NOT NULL,
            PRIMARY KEY (run_id, board_id)
        );

        CREATE TABLE IF NOT EXISTS artifacts (
            run_id TEXT NOT NULL,
            kind TEXT NOT NULL,
            path TEXT NOT NULL,
            PRIMARY KEY (run_id, kind)
        );

        CREATE TABLE IF NOT EXISTS model_comparisons (
            run_id TEXT NOT NULL,
            match_name TEXT NOT NULL,
            consensus_selection TEXT NOT NULL,
            consensus_probability REAL,
            confidence TEXT NOT NULL,
            max_disagreement REAL NOT NULL DEFAULT 0,
            high_divergence INTEGER NOT NULL DEFAULT 0,
            rating_source TEXT,
            raw_json TEXT NOT NULL,
            PRIMARY KEY (run_id, match_name)
        );

        CREATE TABLE IF NOT EXISTS visual_snapshots (
            run_id TEXT NOT NULL,
            chart_id TEXT NOT NULL,
            title TEXT NOT NULL,
            kind TEXT NOT NULL,
            item_count INTEGER NOT NULL DEFAULT 0,
            raw_json TEXT NOT NULL,
            PRIMARY KEY (run_id, chart_id)
        );

        CREATE TABLE IF NOT EXISTS source_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id TEXT NOT NULL,
            source_type TEXT NOT NULL,
            name TEXT NOT NULL,
            url_or_ref TEXT NOT NULL,
            usage TEXT NOT NULL,
            status TEXT NOT NULL,
            status_code INTEGER,
            freshness TEXT NOT NULL,
            evidence_layer TEXT NOT NULL,
            message TEXT NOT NULL,
            raw_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id TEXT NOT NULL,
            check_name TEXT NOT NULL,
            status TEXT NOT NULL,
            severity TEXT NOT NULL,
            message TEXT NOT NULL,
            raw_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS decision_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id TEXT NOT NULL,
            board_id TEXT NOT NULL,
            board_name TEXT NOT NULL,
            rank INTEGER NOT NULL DEFAULT 0,
            event_name TEXT NOT NULL,
            market TEXT NOT NULL,
            selection TEXT NOT NULL,
            action TEXT NOT NULL,
            stake_aud REAL NOT NULL DEFAULT 0,
            probability REAL,
            expected_value REAL,
            evidence_layer TEXT NOT NULL,
            reason TEXT NOT NULL,
            raw_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS missing_data_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id TEXT NOT NULL,
            category TEXT NOT NULL,
            item TEXT NOT NULL,
            severity TEXT NOT NULL,
            status TEXT NOT NULL,
            message TEXT NOT NULL,
            raw_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS manual_review_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id TEXT NOT NULL,
            queue_type TEXT NOT NULL,
            item TEXT NOT NULL,
            severity TEXT NOT NULL,
            status TEXT NOT NULL,
            message TEXT NOT NULL,
            raw_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS automation_runs (
            automation_run_id TEXT PRIMARY KEY,
            mode TEXT NOT NULL DEFAULT '',
            verify_mode TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT '',
            exit_code INTEGER NOT NULL DEFAULT 0,
            started_at TEXT NOT NULL DEFAULT '',
            finished_at TEXT NOT NULL DEFAULT '',
            report_run_id TEXT NOT NULL DEFAULT '',
            latest_commit_run_id TEXT NOT NULL DEFAULT '',
            formal_report_publish_ready INTEGER NOT NULL DEFAULT 0,
            recurring_automation_ready INTEGER NOT NULL DEFAULT 0,
            raw_refresh_ready INTEGER NOT NULL DEFAULT 0,
            my_bets_capture_enabled INTEGER NOT NULL DEFAULT 0,
            my_bets_report_date TEXT NOT NULL DEFAULT '',
            my_bets_capture_exit_code INTEGER NOT NULL DEFAULT 0,
            my_bets_import_exit_code INTEGER NOT NULL DEFAULT 0,
            my_bets_raw_text_seen INTEGER NOT NULL DEFAULT 0,
            capture_log TEXT NOT NULL DEFAULT '',
            import_log TEXT NOT NULL DEFAULT '',
            summary_json TEXT NOT NULL DEFAULT '{}'
        );

        CREATE TABLE IF NOT EXISTS active_timeline_audits (
            audit_id TEXT PRIMARY KEY,
            generated_at TEXT NOT NULL,
            timezone TEXT NOT NULL,
            day_count INTEGER NOT NULL DEFAULT 0,
            complete_day_count INTEGER NOT NULL DEFAULT 0,
            missing_analysis_day_count INTEGER NOT NULL DEFAULT 0,
            missing_report_day_count INTEGER NOT NULL DEFAULT 0,
            backfill_queue_count INTEGER NOT NULL DEFAULT 0,
            cadence_ready_for_all_days INTEGER NOT NULL DEFAULT 0,
            formal_report_ready_for_all_days INTEGER NOT NULL DEFAULT 0,
            backfill_status TEXT NOT NULL DEFAULT '',
            raw_refresh_ready INTEGER NOT NULL DEFAULT 0,
            raw_refresh_status TEXT NOT NULL DEFAULT '',
            raw_blocker_json TEXT NOT NULL DEFAULT '{}',
            payload_json TEXT NOT NULL DEFAULT '{}'
        );

        CREATE TABLE IF NOT EXISTS available_board_strategy_snapshots (
            strategy_id TEXT PRIMARY KEY,
            generated_at TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT '',
            listed_expected_count INTEGER NOT NULL DEFAULT 0,
            missing_expected_count INTEGER NOT NULL DEFAULT 0,
            route_mismatch_active INTEGER NOT NULL DEFAULT 0,
            executable_report_allowed INTEGER NOT NULL DEFAULT 0,
            research_diagnostic_allowed INTEGER NOT NULL DEFAULT 0,
            payload_json TEXT NOT NULL DEFAULT '{}'
        );

        CREATE TABLE IF NOT EXISTS position_monitor_snapshots (
            monitor_id TEXT PRIMARY KEY,
            generated_at TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT '',
            report_date TEXT NOT NULL DEFAULT '',
            snapshot_ready INTEGER NOT NULL DEFAULT 0,
            raw_text_exists INTEGER NOT NULL DEFAULT 0,
            public_metrics_available INTEGER NOT NULL DEFAULT 0,
            payload_json TEXT NOT NULL DEFAULT '{}'
        );
        """
    )
    migrate_schema(conn)
    ensure_unique_indexes(conn)
    conn.execute(
        "INSERT OR REPLACE INTO schema_meta(key, value) VALUES(?, ?)",
        ("schema_version", str(SCHEMA_VERSION)),
    )
    conn.commit()


def migrate_schema(conn: sqlite3.Connection) -> None:
    for table_name, columns in SCHEMA_COLUMNS.items():
        ensure_columns(conn, table_name, columns)


def ensure_columns(conn: sqlite3.Connection, table_name: str, columns: Iterable[tuple[str, str]]) -> None:
    existing = table_columns(conn, table_name)
    for column_name, column_sql in columns:
        if column_name in existing:
            continue
        conn.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_sql}")
        existing.add(column_name)


def table_columns(conn: sqlite3.Connection, table_name: str) -> set[str]:
    return {row["name"] for row in conn.execute(f"PRAGMA table_info({table_name})").fetchall()}


def ensure_unique_indexes(conn: sqlite3.Connection) -> None:
    unique_indexes = {
        "artifacts": ("idx_artifacts_run_kind", ["run_id", "kind"]),
        "model_comparisons": ("idx_model_comparisons_run_match", ["run_id", "match_name"]),
        "visual_snapshots": ("idx_visual_snapshots_run_chart", ["run_id", "chart_id"]),
        "board_diffs": ("idx_board_diffs_run_board", ["run_id", "board_id"]),
        "automation_runs": ("idx_automation_runs_id", ["automation_run_id"]),
        "active_timeline_audits": ("idx_active_timeline_audits_audit", ["audit_id"]),
        "available_board_strategy_snapshots": ("idx_available_board_strategy_id", ["strategy_id"]),
        "position_monitor_snapshots": ("idx_position_monitor_id", ["monitor_id"]),
    }
    for table_name, (index_name, columns) in unique_indexes.items():
        existing = table_columns(conn, table_name)
        if not set(columns).issubset(existing):
            continue
        dedupe_table(conn, table_name, columns)
        conn.execute(f"CREATE UNIQUE INDEX IF NOT EXISTS {index_name} ON {table_name}({', '.join(columns)})")


def dedupe_table(conn: sqlite3.Connection, table_name: str, columns: List[str]) -> None:
    group_by = ", ".join(columns)
    conn.execute(
        f"""
        DELETE FROM {table_name}
        WHERE rowid NOT IN (
            SELECT MAX(rowid)
            FROM {table_name}
            GROUP BY {group_by}
        )
        """
    )


@contextmanager
def schema_migration_lock(db_path: Path):
    lock_path = Path(f"{db_path}.schema.lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    handle = lock_path.open("a+", encoding="utf-8")
    try:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        yield
    finally:
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        finally:
            handle.close()


def secure_report_db_files(db_path: Path) -> None:
    for suffix in ["", "-wal", "-shm", ".schema.lock"]:
        path = Path(f"{db_path}{suffix}")
        if path.exists():
            try:
                os.chmod(path, 0o600)
            except OSError:
                pass


def sanitize_report_db_public_fields(conn: sqlite3.Connection) -> None:
    tables = [
        row[0]
        for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()
        if not str(row[0]).startswith("sqlite_")
    ]
    for table in tables:
        columns = conn.execute(f"PRAGMA table_info({table})").fetchall()
        text_columns = [row[1] for row in columns if "TEXT" in str(row[2]).upper()]
        if not text_columns:
            continue
        quoted = ", ".join(f'"{column}"' for column in text_columns)
        rows = conn.execute(f'SELECT rowid, {quoted} FROM "{table}"').fetchall()
        for row in rows:
            updates = {}
            for column in text_columns:
                value = row[column]
                if isinstance(value, str):
                    sanitized = sanitize_public_text(value)
                    if sanitized != value:
                        updates[column] = sanitized
            if updates:
                assignments = ", ".join(f'"{column}" = ?' for column in updates)
                conn.execute(
                    f'UPDATE "{table}" SET {assignments} WHERE rowid = ?',
                    (*updates.values(), row["rowid"]),
                )


def store_daily_run(db_path: Path, manifest: Dict, output_dir: Path, boards: Iterable[BoardConfig] = BOARD_CONFIGS) -> Dict:
    output_dir = Path(output_dir)
    outputs = manifest.get("outputs", {})
    public_outputs = sanitize_public_payload(outputs)
    public_manifest = sanitize_public_payload(manifest)
    run_id = manifest["run_id"]
    with connect_report_db(db_path) as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO report_runs(
                run_id, status, report_date, started_at, finished_at,
                technical_ready, automation_entry_ready, raw_refresh_ready,
                safety_ready, portfolio_ready, recommended_new_exposure_aud,
                time_adjusted_new_exposure_aud,
                pdf_report, pdf_output_copy, dashboard_path, dashboard_data_path,
                manifest_path, summary_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                manifest.get("status", ""),
                manifest.get("report_date"),
                manifest.get("started_at"),
                manifest.get("finished_at"),
                int(bool(manifest.get("technical_automation_ready"))),
                int(bool(manifest.get("automation_entry_ready"))),
                int(bool(outputs.get("raw_refresh_ready"))),
                int(bool(outputs.get("automation_safety_ready"))),
                int(bool(outputs.get("portfolio_automation_ready"))),
                float(outputs.get("recommended_new_exposure_aud") or 0),
                float(outputs.get("pdf_time_adjusted_new_exposure_aud") or outputs.get("time_adjusted_new_exposure_aud") or 0),
                public_outputs.get("pdf_report"),
                public_outputs.get("pdf_output_copy"),
                public_outputs.get("dashboard_run_copy") or public_outputs.get("dashboard"),
                public_outputs.get("dashboard_data_run_copy") or public_outputs.get("dashboard_data"),
                public_outputs.get("manifest"),
                json.dumps(public_manifest, ensure_ascii=False, sort_keys=True),
            ),
        )
        conn.execute("DELETE FROM board_runs WHERE run_id = ?", (run_id,))
        conn.execute("DELETE FROM recommendations WHERE run_id = ?", (run_id,))
        conn.execute("DELETE FROM artifacts WHERE run_id = ?", (run_id,))
        conn.execute("DELETE FROM report_diffs WHERE run_id = ?", (run_id,))
        conn.execute("DELETE FROM board_diffs WHERE run_id = ?", (run_id,))
        conn.execute("DELETE FROM model_comparisons WHERE run_id = ?", (run_id,))
        conn.execute("DELETE FROM visual_snapshots WHERE run_id = ?", (run_id,))
        conn.execute("DELETE FROM source_logs WHERE run_id = ?", (run_id,))
        conn.execute("DELETE FROM audit_logs WHERE run_id = ?", (run_id,))
        conn.execute("DELETE FROM decision_records WHERE run_id = ?", (run_id,))
        conn.execute("DELETE FROM missing_data_logs WHERE run_id = ?", (run_id,))
        conn.execute("DELETE FROM manual_review_queue WHERE run_id = ?", (run_id,))

        portfolio = load_optional_json(output_dir / "portfolio_automation_gate_v0_12.json")
        bankroll = load_bankroll_plan(output_dir, outputs)
        board_count = store_board_runs(conn, run_id, portfolio)
        recommendation_count = 0
        for board in boards:
            recommendation_count += store_board_recommendations(conn, run_id, board, output_dir, bankroll)
        diff_summary = store_report_diff(conn, run_id, output_dir, outputs)
        model_comparison_count = store_model_comparisons(conn, run_id, output_dir)
        visual_chart_count = store_visual_snapshots(conn, run_id, output_dir, portfolio, outputs, boards, bankroll)
        evidence_summary = store_evidence_bundle(conn, run_id, output_dir, public_manifest, boards)
        artifact_count = store_artifacts(conn, run_id, outputs)
        sanitize_report_db_public_fields(conn)
        conn.commit()
        secure_report_db_files(Path(db_path))
    return {
        "db_path": public_artifact_ref(db_path),
        "run_id": run_id,
        "board_count": board_count,
        "recommendation_count": recommendation_count,
        "model_comparison_count": model_comparison_count,
        "visual_chart_count": visual_chart_count,
        "evidence_summary": evidence_summary,
        "artifact_count": artifact_count,
        "diff_summary": diff_summary,
    }


def store_automation_run(db_path: Path, summary: Dict) -> Dict:
    public_summary = sanitize_public_payload(summary)
    automation_run_id = automation_run_id_from_summary(public_summary)
    readiness = public_summary.get("automation_readiness") or {}
    my_bets_capture = public_summary.get("my_bets_capture") or {}
    last_success = public_summary.get("last_success") or {}
    with connect_report_db(db_path) as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO automation_runs(
                automation_run_id, mode, verify_mode, status, exit_code, started_at, finished_at,
                report_run_id, latest_commit_run_id, formal_report_publish_ready,
                recurring_automation_ready, raw_refresh_ready, my_bets_capture_enabled,
                my_bets_report_date, my_bets_capture_exit_code, my_bets_import_exit_code,
                my_bets_raw_text_seen, capture_log, import_log, summary_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                automation_run_id,
                str(public_summary.get("mode") or ""),
                str(public_summary.get("verify_mode") or ""),
                str(public_summary.get("status") or ""),
                int(public_summary.get("exit_code") or 0),
                str(public_summary.get("started_at") or ""),
                str(public_summary.get("finished_at") or ""),
                str(public_summary.get("run_id") or ""),
                str(last_success.get("run_id") or ""),
                int(bool(readiness.get("formal_report_publish_ready"))),
                int(bool(readiness.get("recurring_automation_ready"))),
                int(bool(public_summary.get("raw_refresh_ready"))),
                int(bool(my_bets_capture.get("enabled"))),
                str(my_bets_capture.get("report_date") or ""),
                int(my_bets_capture.get("capture_exit_code") or 0),
                int(my_bets_capture.get("import_exit_code") or 0),
                int(bool(my_bets_capture.get("raw_text_seen"))),
                public_artifact_ref(my_bets_capture.get("capture_log") or ""),
                public_artifact_ref(my_bets_capture.get("import_log") or ""),
                json.dumps(public_summary, ensure_ascii=False, sort_keys=True),
            ),
        )
        sanitize_report_db_public_fields(conn)
        conn.commit()
        secure_report_db_files(Path(db_path))
    return {
        "db_path": public_artifact_ref(db_path),
        "automation_run_id": automation_run_id,
        "mode": public_summary.get("mode", ""),
        "verify_mode": public_summary.get("verify_mode", ""),
        "status": public_summary.get("status", ""),
    }


def automation_run_id_from_summary(summary: Dict) -> str:
    stdout_log = str(summary.get("stdout_log") or "")
    if stdout_log:
        return stdout_log.replace(".stdout.log", "")
    started_at = str(summary.get("started_at") or "")
    mode = str(summary.get("mode") or "run")
    report_run_id = str(summary.get("run_id") or "")
    value = "-".join(part for part in [mode, started_at, report_run_id] if part)
    return value.replace(":", "").replace("+", "").replace(" ", "_") or "automation-run"


def latest_automation_runs(db_path: Path, limit: int = 8) -> List[Dict]:
    if not Path(db_path).exists():
        return []
    with connect_report_db(db_path) as conn:
        rows = conn.execute(
            """
            SELECT automation_run_id, mode, verify_mode, status, exit_code, started_at, finished_at,
                   report_run_id, latest_commit_run_id, formal_report_publish_ready,
                   recurring_automation_ready, raw_refresh_ready, my_bets_capture_enabled,
                   my_bets_report_date, my_bets_capture_exit_code, my_bets_import_exit_code,
                   my_bets_raw_text_seen, capture_log, import_log
            FROM automation_runs
            ORDER BY started_at DESC, automation_run_id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [
        {
            "automation_run_id": row["automation_run_id"],
            "mode": row["mode"],
            "verify_mode": row["verify_mode"],
            "status": row["status"],
            "exit_code": int(row["exit_code"] or 0),
            "started_at": row["started_at"],
            "finished_at": row["finished_at"],
            "report_run_id": row["report_run_id"],
            "latest_commit_run_id": row["latest_commit_run_id"],
            "formal_report_publish_ready": bool(row["formal_report_publish_ready"]),
            "recurring_automation_ready": bool(row["recurring_automation_ready"]),
            "raw_refresh_ready": bool(row["raw_refresh_ready"]),
            "my_bets_capture_enabled": bool(row["my_bets_capture_enabled"]),
            "my_bets_report_date": row["my_bets_report_date"],
            "my_bets_capture_exit_code": int(row["my_bets_capture_exit_code"] or 0),
            "my_bets_import_exit_code": int(row["my_bets_import_exit_code"] or 0),
            "my_bets_raw_text_seen": bool(row["my_bets_raw_text_seen"]),
            "capture_log": public_artifact_ref(row["capture_log"]),
            "import_log": public_artifact_ref(row["import_log"]),
        }
        for row in rows
    ]


def store_board_runs(conn: sqlite3.Connection, run_id: str, portfolio: Dict) -> int:
    count = 0
    for board in portfolio.get("board_statuses", []):
        conn.execute(
            """
            INSERT OR REPLACE INTO board_runs(
                run_id, board_id, name, priority, ready, raw_fresh, raw_valid,
                gate_ready, report_exists, raw_age_hours, missing_json,
                validation_errors_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                board.get("board_id", ""),
                board.get("name", ""),
                int(board.get("priority") or 0),
                int(bool(board.get("ready"))),
                int(bool(board.get("raw_fresh"))),
                int(bool(board.get("raw_valid"))),
                int(bool(board.get("gate_ready"))),
                int(bool(board.get("report_exists"))),
                board.get("raw_age_hours"),
                json.dumps(board.get("missing", []), ensure_ascii=False),
                json.dumps(board.get("raw_validation_errors", []), ensure_ascii=False),
            ),
        )
        count += 1
    return count


def store_board_recommendations(conn: sqlite3.Connection, run_id: str, board: BoardConfig, output_dir: Path, bankroll: Dict | None = None) -> int:
    payload = load_optional_json(output_dir / board.recommendations_artifact) if board.recommendations_artifact else {}
    if board.board_id == "world_cup_matches":
        payload = apply_public_time_adjusted_match_stakes(payload, bankroll)
    count = 0
    for rank, item in enumerate(payload.get("recommendations", []), start=1):
        normalized = normalize_recommendation(board, item, bankroll)
        conn.execute(
            """
            INSERT INTO recommendations(
                run_id, board_id, board_name, rank, event_name, market,
                selection, odds, probability, expected_value, stake_aud,
                action, raw_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                board.board_id,
                board.name,
                rank,
                normalized["event_name"],
                normalized["market"],
                normalized["selection"],
                normalized["odds"],
                normalized["probability"],
                normalized["expected_value"],
                normalized["stake_aud"],
                normalized["action"],
                json.dumps(item, ensure_ascii=False, sort_keys=True),
            ),
        )
        count += 1
    return count


def normalize_recommendation(board: BoardConfig, item: Dict, bankroll: Dict | None = None) -> Dict:
    probability = item.get("model_probability", item.get("no_vig_probability", item.get("probability")))
    if board.board_id == "world_cup_matches":
        event_name = item.get("match", "")
        selection = item.get("selection", "")
    elif board.board_id == "world_cup_group_betting":
        event_name = f"Group {item.get('group', '')}".strip()
        selection = item.get("team", "")
    elif board.board_id in {"world_cup_futures", "world_cup_team_futures_multi"}:
        event_name = item.get("team", "")
        selection = item.get("team", "")
    else:
        event_name = item.get("market", board.name)
        selection = item.get("selection", "")
    stake_aud = display_stake_aud(board.board_id, item, bankroll)
    return {
        "event_name": str(event_name),
        "market": str(item.get("market", "")),
        "selection": str(selection),
        "odds": optional_float(item.get("odds")),
        "probability": optional_float(probability),
        "expected_value": optional_float(item.get("expected_value")),
        "stake_aud": stake_aud,
        "action": str("buy" if stake_aud > 0 else item.get("decision") or "watch_or_no_bet"),
    }


def store_report_diff(conn: sqlite3.Connection, run_id: str, output_dir: Path, outputs: Dict) -> Dict:
    diff = load_portfolio_compare(output_dir, outputs)
    if not diff:
        matches_board = next(board for board in BOARD_CONFIGS if board.board_id == "world_cup_matches")
        matches = load_optional_json(output_dir / matches_board.recommendations_artifact)
        diff = matches.get("daily_compare", {})
    summary = diff.get("summary", {}) if isinstance(diff, dict) else {}
    conn.execute(
        """
        INSERT OR REPLACE INTO report_diffs(
            run_id, added_count, removed_count, changed_count, retained_count,
            exposure_change_aud, raw_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            run_id,
            int(summary.get("added_count") or 0),
            int(summary.get("removed_count") or 0),
            int(summary.get("changed_count") or 0),
            int(summary.get("retained_count") or 0),
            float(summary.get("exposure_change_aud") or 0),
            json.dumps(diff or {}, ensure_ascii=False, sort_keys=True),
        ),
    )
    for board_id, board in (diff.get("by_board", {}) if isinstance(diff, dict) else {}).items():
        conn.execute(
            """
            INSERT OR REPLACE INTO board_diffs(
                run_id, board_id, board_name, added_count, removed_count,
                changed_count, retained_count, exposure_change_aud, raw_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                board_id,
                str(board.get("board_name") or board_id),
                int(board.get("added_count") or 0),
                int(board.get("removed_count") or 0),
                int(board.get("changed_count") or 0),
                int(board.get("retained_count") or 0),
                float(board.get("exposure_change_aud") or 0),
                json.dumps(board, ensure_ascii=False, sort_keys=True),
            ),
        )
    return {
        "added_count": int(summary.get("added_count") or 0),
        "removed_count": int(summary.get("removed_count") or 0),
        "changed_count": int(summary.get("changed_count") or 0),
        "retained_count": int(summary.get("retained_count") or 0),
        "exposure_change_aud": float(summary.get("exposure_change_aud") or 0),
    }


def load_portfolio_compare(output_dir: Path, outputs: Dict) -> Dict:
    configured = outputs.get("portfolio_daily_compare")
    if configured:
        path = Path(configured)
        if path.exists():
            return load_optional_json(path)
    return load_optional_json(output_dir / "portfolio_daily_compare_latest.json")


def load_bankroll_plan(output_dir: Path, outputs: Dict) -> Dict:
    configured = outputs.get("bankroll_plan")
    if configured:
        path = Path(configured)
        if path.exists():
            return load_optional_json(path)
    report_date = outputs.get("report_date")
    if report_date:
        return load_optional_json(output_dir / f"tab_fifa_bankroll_plan_{report_date}.json")
    return {}


def store_model_comparisons(conn: sqlite3.Connection, run_id: str, output_dir: Path) -> int:
    payload = load_optional_json(output_dir / MODEL_COMPARISON_JSON)
    count = 0
    for row in payload.get("rows", []):
        consensus = row.get("consensus", {})
        disagreement = row.get("disagreement", {})
        ratings = row.get("ratings", {})
        conn.execute(
            """
            INSERT OR REPLACE INTO model_comparisons(
                run_id, match_name, consensus_selection, consensus_probability,
                confidence, max_disagreement, high_divergence, rating_source,
                raw_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                row.get("match", ""),
                consensus.get("selection", ""),
                optional_float(consensus.get("mean_probability")),
                str(consensus.get("confidence", "")),
                float(disagreement.get("max_abs_current_vs_elo_dc") or 0),
                int(bool(disagreement.get("high_divergence"))),
                ratings.get("source"),
                json.dumps(row, ensure_ascii=False, sort_keys=True),
            ),
        )
        count += 1
    return count


def store_visual_snapshots(
    conn: sqlite3.Connection,
    run_id: str,
    output_dir: Path,
    portfolio: Dict,
    outputs: Dict,
    boards: Iterable[BoardConfig],
    bankroll: Dict | None = None,
) -> int:
    charts = load_dashboard_visual_summary(run_id, outputs)
    if not charts:
        model_comparison = load_optional_json(output_dir / MODEL_COMPARISON_JSON)
        charts = build_visual_summary(
            board_statuses=portfolio.get("board_statuses", []),
            compare_summary=load_compare_summary(output_dir),
            recommendation_counts=visual_recommendation_counts(output_dir, boards, bankroll),
            match_recommendations=load_match_recommendations(output_dir)[:7],
            model_rows=model_comparison.get("rows", [])[:7],
            model_references=model_comparison.get("references", []),
        )
    count = 0
    for chart in charts:
        chart_id = str(chart.get("id") or "")
        if not chart_id:
            continue
        conn.execute(
            """
            INSERT OR REPLACE INTO visual_snapshots(
                run_id, chart_id, title, kind, item_count, raw_json
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                chart_id,
                str(chart.get("title") or chart_id),
                str(chart.get("kind") or "bar"),
                len(chart.get("items", [])),
                json.dumps(chart, ensure_ascii=False, sort_keys=True),
            ),
        )
        count += 1
    return count


def store_evidence_bundle(conn: sqlite3.Connection, run_id: str, output_dir: Path, manifest: Dict, boards: Iterable[BoardConfig]) -> Dict:
    bundle = build_evidence_bundle(output_dir, manifest, boards)
    for item in bundle.get("source_logs", []):
        conn.execute(
            """
            INSERT INTO source_logs(
                run_id, source_type, name, url_or_ref, usage, status,
                status_code, freshness, evidence_layer, message, raw_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                item.get("source_type", ""),
                item.get("name", ""),
                public_artifact_ref(item.get("url_or_ref", "")) if str(item.get("source_type")) == "local_reference_file" else item.get("url_or_ref", ""),
                item.get("usage", ""),
                item.get("status", ""),
                item.get("status_code"),
                item.get("freshness", ""),
                item.get("evidence_layer", ""),
                item.get("message", ""),
                safe_raw_json(item),
            ),
        )
    for item in bundle.get("audit_logs", []):
        conn.execute(
            """
            INSERT INTO audit_logs(run_id, check_name, status, severity, message, raw_json)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                item.get("check_name", ""),
                item.get("status", ""),
                item.get("severity", ""),
                item.get("message", ""),
                safe_raw_json(item),
            ),
        )
    for item in bundle.get("decision_records", []):
        conn.execute(
            """
            INSERT INTO decision_records(
                run_id, board_id, board_name, rank, event_name, market,
                selection, action, stake_aud, probability, expected_value,
                evidence_layer, reason, raw_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                item.get("board_id", ""),
                item.get("board_name", ""),
                int(item.get("rank") or 0),
                item.get("event_name", ""),
                item.get("market", ""),
                item.get("selection", ""),
                item.get("action", ""),
                float(item.get("stake_aud") or 0),
                optional_float(item.get("probability")),
                optional_float(item.get("expected_value")),
                item.get("evidence_layer", ""),
                item.get("reason", ""),
                safe_raw_json(item),
            ),
        )
    for item in bundle.get("missing_data_logs", []):
        conn.execute(
            """
            INSERT INTO missing_data_logs(run_id, category, item, severity, status, message, raw_json)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                item.get("category", ""),
                item.get("item", ""),
                item.get("severity", ""),
                item.get("status", ""),
                item.get("message", ""),
                safe_raw_json(item),
            ),
        )
    for item in bundle.get("manual_review_queue", []):
        conn.execute(
            """
            INSERT INTO manual_review_queue(run_id, queue_type, item, severity, status, message, raw_json)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                item.get("queue_type", ""),
                item.get("item", ""),
                item.get("severity", ""),
                item.get("status", ""),
                item.get("message", ""),
                safe_raw_json(item),
            ),
        )
    return bundle.get("summary", {})


def safe_raw_json(item: Dict) -> str:
    raw = item.get("raw", item)
    return json.dumps(sanitize_public_payload(raw), ensure_ascii=False, sort_keys=True)


def load_dashboard_visual_summary(run_id: str, outputs: Dict) -> List[Dict]:
    configured = outputs.get("dashboard_data")
    if not configured:
        return []
    payload = load_optional_json(Path(configured))
    if payload.get("run_id") != run_id:
        return []
    charts = payload.get("visual_summary", [])
    return charts if isinstance(charts, list) else []


def load_compare_summary(output_dir: Path) -> Dict:
    diff = load_portfolio_compare(output_dir, {})
    if not diff:
        matches_board = next(board for board in BOARD_CONFIGS if board.board_id == "world_cup_matches")
        matches = load_optional_json(output_dir / matches_board.recommendations_artifact)
        diff = matches.get("daily_compare", {})
    summary = diff.get("summary", {}) if isinstance(diff, dict) else {}
    return {
        "added_count": int(summary.get("added_count") or 0),
        "removed_count": int(summary.get("removed_count") or 0),
        "changed_count": int(summary.get("changed_count") or 0),
        "retained_count": int(summary.get("retained_count") or 0),
        "exposure_change_aud": float(summary.get("exposure_change_aud") or 0),
    }


def load_match_recommendations(output_dir: Path) -> List[Dict]:
    matches_board = next(board for board in BOARD_CONFIGS if board.board_id == "world_cup_matches")
    return load_optional_json(output_dir / matches_board.recommendations_artifact).get("recommendations", [])


def visual_recommendation_counts(output_dir: Path, boards: Iterable[BoardConfig], bankroll: Dict | None = None) -> List[Dict]:
    counts = []
    for board in boards:
        payload = load_optional_json(output_dir / board.recommendations_artifact) if board.recommendations_artifact else {}
        if board.board_id == "world_cup_matches":
            payload = apply_public_time_adjusted_match_stakes(payload, bankroll)
        recommendations = payload.get("recommendations", [])
        counts.append(
            {
                "board_id": board.board_id,
                "name": board.name.replace("2026 World Cup ", ""),
                "count": len(recommendations),
                "stake_aud": sum(display_stake_aud(board.board_id, item, bankroll) for item in recommendations),
            }
        )
    return counts


def store_artifacts(conn: sqlite3.Connection, run_id: str, outputs: Dict) -> int:
    artifact_keys = [
        "pdf_report",
        "pdf_output_copy",
        "bankroll_plan",
        "portfolio_daily_compare",
        "portfolio_daily_compare_latest",
        "portfolio_baseline",
        "portfolio_baseline_latest",
        "portfolio_gate",
        "current_baseline",
        "latest_baseline",
        "safety_gate",
        "raw_refresh_manifest",
        "raw_refresh_batch_manifest",
        "raw_refresh_health",
        "raw_refresh_diagnostics",
        "raw_refresh_diagnostics_latest",
        "pdf_qa",
        "pdf_qa_latest",
        "automation_preflight",
        "automation_preflight_latest",
        "report_index",
        "report_index_latest",
        "report_index_report",
        "report_index_report_latest",
        "report_index_pdf",
        "report_index_pdf_latest",
        "report_intelligence",
        "report_intelligence_latest",
        "report_intelligence_report",
        "report_intelligence_report_latest",
        "report_intelligence_pdf",
        "report_intelligence_pdf_latest",
        "automation_readiness",
        "automation_readiness_report",
        "automation_readiness_pdf",
        "automation_candidate",
        "automation_candidate_report",
        "automation_candidate_pdf",
        "manifest",
        "latest_manifest",
        "latest_commit",
        "dashboard",
        "dashboard_data",
        "dashboard_run_copy",
        "dashboard_data_run_copy",
        "report_database",
        "model_comparison_json",
        "model_comparison_report",
        "model_comparison_pdf",
        "pdf_run_copy",
        "bankroll_plan_run_copy",
    ]
    count = 0
    for key in artifact_keys:
        value = outputs.get(key)
        if not value:
            continue
        conn.execute(
            "INSERT OR REPLACE INTO artifacts(run_id, kind, path) VALUES (?, ?, ?)",
            (run_id, key, public_artifact_ref(value)),
        )
        count += 1
    return count


def write_report_index(db_path: Path, output_dir: Path, output_path: Path, limit: int = 20, latest_commit: Dict | None = None) -> Dict:
    payload = build_report_index(db_path, output_dir, limit=limit, latest_commit=latest_commit)
    atomic_write_json(Path(output_path), payload)
    return payload


def write_report_index_report(index_payload: Dict, output_path: Path) -> Dict:
    markdown = render_report_index_markdown(index_payload)
    atomic_write_text(Path(output_path), markdown)
    return {
        "path": public_artifact_ref(output_path),
        "run_count": int(index_payload.get("run_count") or 0),
        "latest_success_run_id": index_payload.get("latest_success_run_id", ""),
        "mermaid_blocks": markdown.count("```mermaid"),
    }


def write_report_index_pdf(index_payload: Dict, output_path: Path) -> Dict:
    runs = index_payload.get("runs") or []
    automation_runs = index_payload.get("automation_runs") or []
    pdf_summary = render_sidecar_pdf(
        output_path,
        title="TAB FIFA Report History Index",
        subtitle="Local SQLite report history, run comparison and artifact coverage. No new wagering recommendation.",
        summary_rows=[
            ("committed_latest_run_id", str(index_payload.get("committed_latest_run_id", ""))),
            ("latest_success_run_id", str(index_payload.get("latest_success_run_id", ""))),
            ("latest_report_date", str(index_payload.get("latest_report_date", ""))),
            ("run_count", str(index_payload.get("run_count", 0))),
            ("automation_run_count", str(index_payload.get("automation_run_count", 0))),
        ],
        charts=[
            chart_from_items("Run status mix", report_status_items(runs), "#1F4E79"),
            chart_from_items("Technical readiness by run", report_ready_items(runs, "technical_ready"), "#2E7D32"),
            chart_from_items("Recommended exposure by run", report_exposure_items(runs), "#6A4C93"),
            chart_from_items("Recommendation volume by run", report_count_items(runs, "recommendations"), "#D17A22"),
            chart_from_items("New-vs-old changed items", report_change_items(runs), "#C62828"),
            chart_from_items("Automation runner status mix", automation_status_items(automation_runs), "#1F4E79"),
            chart_from_items("Automation publish readiness", automation_publish_items(automation_runs), "#2E7D32"),
        ],
        table_headers=["Run", "Date", "Status", "Recs", "Charts", "Exposure", "Changed"],
        table_rows=[
            [
                str(run.get("run_id", "")),
                str(run.get("report_date", "")),
                str(run.get("status", "")),
                str((run.get("counts") or {}).get("recommendations", 0)),
                str((run.get("counts") or {}).get("visual_charts", 0)),
                f"{float(run.get('time_adjusted_new_exposure_aud') or 0):.2f}",
                str(
                    int((run.get("compare_summary") or {}).get("added_count") or 0)
                    + int((run.get("compare_summary") or {}).get("changed_count") or 0)
                    + int((run.get("compare_summary") or {}).get("removed_count") or 0)
                ),
            ]
            for run in runs[:20]
        ],
        extra_tables=[
            {
                "title": "Automation Runner History",
                "headers": ["Runner", "Mode", "Verify", "Status", "Exit", "Raw", "Publish", "Capture"],
                "rows": [
                    [
                        str(run.get("automation_run_id", "")),
                        str(run.get("mode", "")),
                        str(run.get("verify_mode", "")),
                        str(run.get("status", "")),
                        str(int(run.get("exit_code") or 0)),
                        str(int(bool(run.get("raw_refresh_ready")))),
                        str(int(bool(run.get("formal_report_publish_ready")))),
                        str(int(bool(run.get("my_bets_capture_enabled")))),
                    ]
                    for run in automation_runs[:20]
                ],
            }
        ],
    )
    return {
        **pdf_summary,
        "run_count": int(index_payload.get("run_count") or 0),
        "latest_success_run_id": index_payload.get("latest_success_run_id", ""),
    }


def render_report_index_markdown(index_payload: Dict) -> str:
    runs = index_payload.get("runs") or []
    automation_runs = index_payload.get("automation_runs") or []
    latest = index_payload.get("latest_commit") or {}
    lines = [
        "# TAB FIFA Report History Index",
        "",
        "本报告把本地 SQLite 历史记录转换为可审阅的报告索引，用于追踪每次日报的新旧变化、图表覆盖、推荐数量和发布状态。它不生成新的下注建议。",
        "",
        "## Executive Status",
        "",
        f"- committed_latest_run_id: `{index_payload.get('committed_latest_run_id', '')}`",
        f"- latest_success_run_id: `{index_payload.get('latest_success_run_id', '')}`",
        f"- latest_report_date: `{index_payload.get('latest_report_date', '')}`",
        f"- run_count: `{index_payload.get('run_count', 0)}`",
        f"- automation_run_count: `{index_payload.get('automation_run_count', 0)}`",
        f"- latest_status: `{latest.get('status', '')}`",
        "",
        "## Visual Summary",
        "",
        "### Run status mix",
        "",
        mermaid_pie("Run status mix", report_status_items(runs)),
        "",
        "### Technical readiness by recent run",
        "",
        mermaid_bar("Technical readiness by recent run", report_ready_items(runs, "technical_ready"), y_label="ready score"),
        "",
        "### Recommended new exposure by run",
        "",
        mermaid_bar("Recommended new exposure by run", report_exposure_items(runs), y_label="AUD"),
        "",
        "### Recommendation volume by run",
        "",
        mermaid_bar("Recommendation volume by run", report_count_items(runs, "recommendations"), y_label="count"),
        "",
        "### New-vs-old changed items by run",
        "",
        mermaid_bar("New-vs-old changed items by run", report_change_items(runs), y_label="changed count"),
        "",
        "### Automation runner status mix",
        "",
        mermaid_pie("Automation runner status mix", automation_status_items(automation_runs)),
        "",
        "### Automation publish readiness by runner",
        "",
        mermaid_bar("Automation publish readiness by runner", automation_publish_items(automation_runs), y_label="publish ready"),
        "",
        "## Recent Runs",
        "",
        "| Run | Date | Status | Tech | Raw | Safety | Portfolio | Recs | Charts | Exposure AUD | Added | Changed | Removed |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for run in runs[:20]:
        counts = run.get("counts") or {}
        compare = run.get("compare_summary") or {}
        lines.append(
            "| {run_id} | {date} | {status} | {tech} | {raw} | {safety} | {portfolio} | {recs} | {charts} | {exposure:.2f} | {added} | {changed} | {removed} |".format(
                run_id=run.get("run_id", ""),
                date=run.get("report_date", ""),
                status=run.get("status", ""),
                tech=int(bool(run.get("technical_ready"))),
                raw=int(bool(run.get("raw_refresh_ready"))),
                safety=int(bool(run.get("safety_ready"))),
                portfolio=int(bool(run.get("portfolio_ready"))),
                recs=int(counts.get("recommendations") or 0),
                charts=int(counts.get("visual_charts") or 0),
                exposure=float(run.get("time_adjusted_new_exposure_aud") or 0),
                added=int(compare.get("added_count") or 0),
                changed=int(compare.get("changed_count") or 0),
                removed=int(compare.get("removed_count") or 0),
            )
        )
    lines.extend(
        [
            "",
            "## Automation Runner History",
            "",
            "| Runner | Mode | Verify | Status | Exit | Raw | Publish | Private Capture | Started |",
            "|---|---|---|---|---:|---:|---:|---:|---|",
        ]
    )
    for run in automation_runs[:20]:
        lines.append(
            "| {runner} | {mode} | {verify} | {status} | {exit_code} | {raw} | {publish} | {capture} | {started} |".format(
                runner=run.get("automation_run_id", ""),
                mode=run.get("mode", ""),
                verify=run.get("verify_mode", ""),
                status=run.get("status", ""),
                exit_code=int(run.get("exit_code") or 0),
                raw=int(bool(run.get("raw_refresh_ready"))),
                publish=int(bool(run.get("formal_report_publish_ready"))),
                capture=int(bool(run.get("my_bets_capture_enabled"))),
                started=run.get("started_at", ""),
            )
        )
    return "\n".join(lines)


def build_report_index(db_path: Path, output_dir: Path, limit: int = 20, latest_commit: Dict | None = None) -> Dict:
    runs = indexed_report_runs(db_path, limit=limit)
    automation_runs = latest_automation_runs(db_path, limit=limit)
    latest_commit_summary = sanitize_latest_commit_summary(latest_commit or {})
    committed_run_id = latest_commit_summary.get("run_id", "")
    latest_success = (
        next((run for run in runs if committed_run_id and run.get("run_id") == committed_run_id), {})
        or next((run for run in runs if run.get("status") == "ready_for_manual_report"), {})
    )
    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "database": public_artifact_ref(db_path),
        "output_dir": public_artifact_ref(output_dir),
        "run_count": len(runs),
        "committed_latest_run_id": committed_run_id,
        "latest_success_run_id": latest_success.get("run_id", ""),
        "latest_report_date": latest_success.get("report_date", ""),
        "latest_commit": latest_commit_summary,
        "runs": runs,
        "automation_run_count": len(automation_runs),
        "automation_runs": automation_runs,
    }


def indexed_report_runs(db_path: Path, limit: int = 20) -> List[Dict]:
    if not Path(db_path).exists():
        return []
    with connect_report_db(db_path) as conn:
        rows = conn.execute(
            """
            SELECT report_runs.run_id, report_runs.status, report_runs.report_date,
                   report_runs.started_at, report_runs.finished_at,
                   report_runs.technical_ready, report_runs.automation_entry_ready,
                   report_runs.raw_refresh_ready, report_runs.safety_ready,
                   report_runs.portfolio_ready,
                   report_runs.time_adjusted_new_exposure_aud,
                   report_diffs.added_count, report_diffs.removed_count,
                   report_diffs.changed_count, report_diffs.retained_count,
                   report_diffs.exposure_change_aud,
                   COALESCE(pdf_run.path, report_runs.pdf_output_copy, report_runs.pdf_report) AS pdf_report,
                   COALESCE(dashboard_run.path, report_runs.dashboard_path) AS dashboard,
                   dashboard_data_run.path AS dashboard_data,
                   manifest.path AS manifest,
                   (SELECT COUNT(*) FROM recommendations WHERE recommendations.run_id = report_runs.run_id) AS recommendation_count,
                   (SELECT COUNT(*) FROM visual_snapshots WHERE visual_snapshots.run_id = report_runs.run_id) AS visual_chart_count,
                   (SELECT COUNT(*) FROM model_comparisons WHERE model_comparisons.run_id = report_runs.run_id) AS model_comparison_count,
                   (SELECT COUNT(*) FROM source_logs WHERE source_logs.run_id = report_runs.run_id) AS source_count,
                   (SELECT COUNT(*) FROM audit_logs WHERE audit_logs.run_id = report_runs.run_id) AS audit_count,
                   (SELECT COUNT(*) FROM missing_data_logs WHERE missing_data_logs.run_id = report_runs.run_id) AS missing_data_count,
                   (SELECT COUNT(*) FROM manual_review_queue WHERE manual_review_queue.run_id = report_runs.run_id) AS manual_review_count
            FROM report_runs
            LEFT JOIN report_diffs
              ON report_diffs.run_id = report_runs.run_id
            LEFT JOIN artifacts AS pdf_run
              ON pdf_run.run_id = report_runs.run_id
             AND pdf_run.kind = 'pdf_run_copy'
            LEFT JOIN artifacts AS dashboard_run
              ON dashboard_run.run_id = report_runs.run_id
             AND dashboard_run.kind = 'dashboard_run_copy'
            LEFT JOIN artifacts AS dashboard_data_run
              ON dashboard_data_run.run_id = report_runs.run_id
             AND dashboard_data_run.kind = 'dashboard_data_run_copy'
            LEFT JOIN artifacts AS manifest
              ON manifest.run_id = report_runs.run_id
             AND manifest.kind = 'manifest'
            ORDER BY report_runs.started_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [indexed_report_run(row) for row in rows]


def indexed_report_run(row: sqlite3.Row) -> Dict:
    return {
        "run_id": row["run_id"],
        "status": row["status"],
        "report_date": row["report_date"],
        "started_at": row["started_at"],
        "finished_at": row["finished_at"],
        "technical_ready": bool(row["technical_ready"]),
        "automation_entry_ready": bool(row["automation_entry_ready"]),
        "raw_refresh_ready": bool(row["raw_refresh_ready"]),
        "safety_ready": bool(row["safety_ready"]),
        "portfolio_ready": bool(row["portfolio_ready"]),
        "time_adjusted_new_exposure_aud": float(row["time_adjusted_new_exposure_aud"] or 0),
        "compare_summary": {
            "added_count": int(row["added_count"] or 0),
            "removed_count": int(row["removed_count"] or 0),
            "changed_count": int(row["changed_count"] or 0),
            "retained_count": int(row["retained_count"] or 0),
            "exposure_change_aud": float(row["exposure_change_aud"] or 0),
        },
        "artifact_refs": {
            "pdf_report": public_artifact_ref(row["pdf_report"]),
            "dashboard": public_artifact_ref(row["dashboard"]),
            "dashboard_data": public_artifact_ref(row["dashboard_data"]),
            "manifest": public_artifact_ref(row["manifest"]),
        },
        "counts": {
            "recommendations": int(row["recommendation_count"] or 0),
            "visual_charts": int(row["visual_chart_count"] or 0),
            "model_comparisons": int(row["model_comparison_count"] or 0),
            "sources": int(row["source_count"] or 0),
            "audits": int(row["audit_count"] or 0),
            "missing_data": int(row["missing_data_count"] or 0),
            "manual_review": int(row["manual_review_count"] or 0),
        },
    }


def report_status_items(runs: List[Dict]) -> List[tuple[str, float]]:
    counts: Dict[str, int] = {}
    for run in runs:
        status = str(run.get("status") or "unknown")
        counts[status] = counts.get(status, 0) + 1
    return sorted(counts.items(), key=lambda item: (-item[1], item[0])) or [("none", 1.0)]


def report_ready_items(runs: List[Dict], field: str) -> List[tuple[str, float]]:
    return [(report_run_label(run), 1.0 if run.get(field) else 0.0) for run in runs[:8]]


def report_exposure_items(runs: List[Dict]) -> List[tuple[str, float]]:
    return [(report_run_label(run), float(run.get("time_adjusted_new_exposure_aud") or 0)) for run in runs[:8]]


def report_count_items(runs: List[Dict], count_key: str) -> List[tuple[str, float]]:
    return [(report_run_label(run), float((run.get("counts") or {}).get(count_key) or 0)) for run in runs[:8]]


def report_change_items(runs: List[Dict]) -> List[tuple[str, float]]:
    rows = []
    for run in runs[:8]:
        compare = run.get("compare_summary") or {}
        changed = int(compare.get("added_count") or 0) + int(compare.get("changed_count") or 0) + int(compare.get("removed_count") or 0)
        rows.append((report_run_label(run), float(changed)))
    return rows


def automation_status_items(runs: List[Dict]) -> List[tuple[str, float]]:
    counts: Dict[str, int] = {}
    for run in runs:
        status = str(run.get("status") or "unknown")
        counts[status] = counts.get(status, 0) + 1
    return sorted(counts.items(), key=lambda item: (-item[1], item[0])) or [("none", 1.0)]


def automation_publish_items(runs: List[Dict]) -> List[tuple[str, float]]:
    return [(automation_run_label(run), 1.0 if run.get("formal_report_publish_ready") else 0.0) for run in runs[:8]]


def automation_run_label(run: Dict) -> str:
    run_id = str(run.get("automation_run_id") or "")
    suffix = run_id[-8:] if len(run_id) >= 8 else run_id or "unknown"
    verify = str(run.get("verify_mode") or run.get("mode") or "")
    return f"{verify}-{suffix}" if verify else suffix


def report_run_label(run: Dict) -> str:
    run_id = str(run.get("run_id") or "")
    suffix = run_id[-8:] if len(run_id) >= 8 else run_id or "unknown"
    date = str(run.get("report_date") or "")
    return f"{date}-{suffix}" if date else suffix


def sanitize_latest_commit_summary(payload: Dict) -> Dict:
    if not payload:
        return {}
    return {
        "run_id": payload.get("run_id", ""),
        "report_date": payload.get("report_date", ""),
        "status": payload.get("status", ""),
        "technical_automation_ready": bool(payload.get("technical_automation_ready")),
        "public_artifact_safety_ready": bool(payload.get("public_artifact_safety_ready")),
        "ready_required_boards": payload.get("ready_required_boards", ""),
    }


def update_run_dashboard_paths(db_path: Path, run_id: str, dashboard_path: Path, dashboard_data_path: Path) -> None:
    with connect_report_db(db_path) as conn:
        conn.execute(
            "UPDATE report_runs SET dashboard_path = ?, dashboard_data_path = ? WHERE run_id = ?",
            (public_artifact_ref(dashboard_path), public_artifact_ref(dashboard_data_path), run_id),
        )
        for kind, path in [
            ("dashboard", dashboard_path),
            ("dashboard_data", dashboard_data_path),
            ("dashboard_run_copy", dashboard_path),
            ("dashboard_data_run_copy", dashboard_data_path),
        ]:
            conn.execute(
                "INSERT OR REPLACE INTO artifacts(run_id, kind, path) VALUES (?, ?, ?)",
                (run_id, kind, public_artifact_ref(path)),
            )
        sanitize_report_db_public_fields(conn)
        conn.commit()


def latest_runs(db_path: Path, limit: int = 8) -> List[Dict]:
    if not Path(db_path).exists():
        return []
    with connect_report_db(db_path) as conn:
        rows = conn.execute(
            """
            SELECT report_runs.run_id, report_runs.status, report_runs.report_date,
                   report_runs.started_at, report_runs.finished_at,
                   report_runs.technical_ready, report_runs.automation_entry_ready,
                   report_runs.recommended_new_exposure_aud, report_runs.time_adjusted_new_exposure_aud,
                   COALESCE(dashboard_run.path, dashboard_legacy.path, report_runs.dashboard_path) AS dashboard_path
            FROM report_runs
            LEFT JOIN artifacts AS dashboard_run
              ON dashboard_run.run_id = report_runs.run_id
             AND dashboard_run.kind = 'dashboard_run_copy'
            LEFT JOIN artifacts AS dashboard_legacy
              ON dashboard_legacy.run_id = report_runs.run_id
             AND dashboard_legacy.kind = 'dashboard'
            ORDER BY report_runs.started_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]


def load_optional_json(path: Path) -> Dict:
    try:
        if not path.exists():
            return {}
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return {}


def optional_float(value) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
