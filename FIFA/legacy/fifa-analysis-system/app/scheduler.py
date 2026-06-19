import sqlite3
import threading
import time
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from .config import settings
from .crawler import crawl_source
from .database import connect, init_db, row, rows
from .services import build_prediction, create_match_report


class RefreshScheduler:
    def __init__(self) -> None:
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()
        self.last_started_at: Optional[str] = None
        self.last_finished_at: Optional[str] = None
        self.last_status = "not_started"
        self.last_summary = ""
        self.last_error = ""

    @property
    def interval_seconds(self) -> float:
        return max(settings.refresh_interval_hours * 60 * 60, 60)

    def start(self) -> None:
        if not settings.enable_scheduler:
            self.last_status = "disabled"
            self.last_summary = "Scheduler disabled by ENABLE_SCHEDULER."
            return
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._loop, name="refresh-scheduler", daemon=True)
        self._thread.start()
        self.last_status = "running"
        self.last_summary = f"Scheduler running every {settings.refresh_interval_hours:g} hours."

    def stop(self) -> None:
        self._stop_event.set()

    def status(self) -> Dict[str, Any]:
        next_run_at = None
        if self.last_finished_at and self.last_status != "disabled":
            finished = datetime.fromisoformat(self.last_finished_at)
            next_run_at = (finished + timedelta(seconds=self.interval_seconds)).isoformat(timespec="seconds")
        return {
            "enabled": settings.enable_scheduler,
            "running": bool(self._thread and self._thread.is_alive()),
            "interval_hours": settings.refresh_interval_hours,
            "last_started_at": self.last_started_at,
            "last_finished_at": self.last_finished_at,
            "next_run_at": next_run_at,
            "last_status": self.last_status,
            "last_summary": self.last_summary,
            "last_error": self.last_error,
        }

    def run_once(self) -> Dict[str, Any]:
        with self._lock:
            self.last_started_at = datetime.utcnow().isoformat(timespec="seconds")
            self.last_status = "running"
            self.last_error = ""
            try:
                with connect() as conn:
                    init_db(conn)
                    result = run_refresh_cycle(conn)
                self.last_status = result["status"]
                self.last_summary = result.get("summary", "")
                return result
            except Exception as exc:
                self.last_status = "failed"
                self.last_error = str(exc)
                raise
            finally:
                self.last_finished_at = datetime.utcnow().isoformat(timespec="seconds")

    def _loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                self.run_once()
            except Exception:
                pass
            self._stop_event.wait(self.interval_seconds)


def _run_source(conn: sqlite3.Connection, source: Dict[str, Any]) -> Dict[str, Any]:
    cur = conn.execute(
        "INSERT INTO crawl_jobs(source_id, status, started_at) VALUES (?, 'running', CURRENT_TIMESTAMP)",
        (source["id"],),
    )
    job_id = int(cur.lastrowid)
    result = crawl_source(conn, source, job_id)
    conn.execute(
        "UPDATE crawl_jobs SET status = ?, finished_at = CURRENT_TIMESTAMP, summary = ? WHERE id = ?",
        (result["status"], result["summary"], job_id),
    )
    return result


def run_refresh_cycle(conn: sqlite3.Connection) -> Dict[str, Any]:
    run_cur = conn.execute("INSERT INTO refresh_runs(status) VALUES ('running')")
    run_id = int(run_cur.lastrowid)
    sources_checked = 0
    articles_inserted = 0
    matches_refreshed = 0
    reports_created = 0
    errors = []

    for source in rows(conn, "SELECT * FROM crawl_sources WHERE enabled = 1 ORDER BY id"):
        sources_checked += 1
        result = _run_source(conn, source)
        articles_inserted += int(result.get("inserted") or 0)
        if result.get("status") == "failed":
            errors.append(result.get("summary", "source failed"))

    matches = rows(
        conn,
        """
        SELECT id FROM matches
        WHERE status IN ('scheduled', 'postponed')
        ORDER BY match_time
        """,
    )
    for match in matches:
        try:
            build_prediction(conn, int(match["id"]))
            create_match_report(conn, int(match["id"]), include_prediction=True)
            matches_refreshed += 1
            reports_created += 1
        except ValueError as exc:
            errors.append(f"match {match['id']}: {exc}")

    status = "completed" if not errors else "completed_with_errors"
    summary = (
        f"Checked {sources_checked} sources, inserted {articles_inserted} articles, "
        f"refreshed {matches_refreshed} matches, created {reports_created} reports."
    )
    if errors:
        summary = f"{summary} Errors: {'; '.join(errors[:5])}"

    conn.execute(
        """
        UPDATE refresh_runs
        SET status = ?, finished_at = CURRENT_TIMESTAMP, sources_checked = ?,
            articles_inserted = ?, matches_refreshed = ?, reports_created = ?, summary = ?
        WHERE id = ?
        """,
        (status, sources_checked, articles_inserted, matches_refreshed, reports_created, summary, run_id),
    )
    persisted = row(conn, "SELECT * FROM refresh_runs WHERE id = ?", (run_id,))
    return persisted or {"status": status, "summary": summary}


scheduler = RefreshScheduler()
