from __future__ import annotations

import json
import os
import threading
import traceback
from dataclasses import dataclass
from datetime import datetime, timedelta, time, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

from app.config import Settings
from app.core.run_visibility import is_future_controlled_backfill
from app.core.time_display import format_now_display
from app.db import connect, init_db
from app.scheduler import SCHEDULE_SLOTS


_APPLICATION_WRITE_LOCK = threading.RLock()
_MANUAL_REVIEW_WRITE_LOCK = threading.RLock()
_MANUAL_REVIEW_REFRESH_LOCK = threading.RLock()
_MANUAL_REVIEW_REFRESH_IN_FLIGHT: set[int] = set()
MANUAL_REVIEW_STALE_REFRESH_SECONDS = 15 * 60
DEFAULT_AUTO_SHUTDOWN_SECONDS = 0
DEFAULT_AUTOSCHEDULER_INTERVAL_SECONDS = 60
DEFAULT_AUTOSCHEDULER_INITIAL_DELAY_SECONDS = 3


def automation_tick(*args: object, **kwargs: object) -> dict[str, object]:
    from app.core.automation_tick import automation_tick as real_automation_tick

    return real_automation_tick(*args, **kwargs)


def run_slot(*args: object, **kwargs: object) -> dict[str, object]:
    from app.core.pipeline import run_slot as real_run_slot

    return real_run_slot(*args, **kwargs)


def build_application_portal(*args: object, **kwargs: object) -> dict[str, object]:
    from app.core.application_portal import build_application_portal as real_build_application_portal

    return real_build_application_portal(*args, **kwargs)


MANUAL_REVIEW_OUTCOMES: dict[str, dict[str, str]] = {
    "observe_pool": {
        "label": "放入观察池继续观察",
        "system_disposition": "继续留在观察池；保存后立即新增一次真实 Serenity run，并在后续满足 Serenity 标准和条件后更新进持仓建议，不满足则继续观察，直到不再满足观察池标准后移出。",
    },
    "exclude_current_observation": {
        "label": "剔除这一轮观察池",
        "system_disposition": "本轮观察池移除；保存后立即新增一次真实 Serenity run；当前问题解决后，或 14 天后再次满足 Serenity 标准和条件时，才允许重新进入观察池。",
    },
    "promote_top5_candidate_pool": {
        "label": "进入 Top 5 候选操作池",
        "system_disposition": "进入候选持仓建议操作池；保存后立即运行一次 Serenity 全流程，并同步更新首页、报告、数据库和全局展示数据。",
    },
}


@dataclass(frozen=True)
class RefreshHolding:
    code: str
    name: str
    weight: float


def _bool_env(name: str, default: bool) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _int_env(name: str, default: int) -> int:
    value = os.environ.get(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _autoscheduler_status_path(settings: Settings) -> Path:
    return settings.root_dir / "outputs" / "implementation" / "AUTOSCHEDULER_STATUS.json"


def _atomic_write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(f".{path.name}.tmp")
    tmp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp_path.replace(path)


def _next_real_slot_snapshot(settings: Settings, current: datetime | None = None) -> dict[str, object]:
    primary_zone = ZoneInfo(settings.timezone_primary)
    secondary_zone = ZoneInfo(settings.timezone_secondary)
    now_bj = (current or datetime.now(primary_zone)).astimezone(primary_zone)
    for offset in range(0, 8):
        day = now_bj.date() + timedelta(days=offset)
        if day.weekday() >= 5:
            continue
        for slot, hhmm in SCHEDULE_SLOTS.items():
            hour, minute = [int(part) for part in hhmm.split(":")]
            candidate = datetime.combine(day, time(hour, minute), tzinfo=primary_zone)
            if candidate > now_bj:
                return {
                    "slot": slot,
                    "run_time_bj": candidate.isoformat(timespec="seconds"),
                    "run_time_au": candidate.astimezone(secondary_zone).isoformat(timespec="seconds"),
                }
    return {"slot": None, "run_time_bj": None, "run_time_au": None}


def read_autoscheduler_status(settings: Settings) -> dict[str, object]:
    path = _autoscheduler_status_path(settings)
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                data["status_path"] = str(path)
                return data
        except json.JSONDecodeError:
            pass
    return {
        "status": "not_started",
        "scheduler_kind": "application_server_interval",
        "status_path": str(path),
        "next_real_slot": _next_real_slot_snapshot(settings),
    }


class ApplicationAutoScheduler:
    def __init__(
        self,
        settings: Settings,
        *,
        interval_seconds: int = DEFAULT_AUTOSCHEDULER_INTERVAL_SECONDS,
        initial_delay_seconds: int = DEFAULT_AUTOSCHEDULER_INITIAL_DELAY_SECONDS,
        send_mail: bool = True,
        local: bool = True,
    ) -> None:
        self.settings = settings
        self.interval_seconds = max(5, int(interval_seconds))
        self.initial_delay_seconds = max(0, int(initial_delay_seconds))
        self.send_mail = send_mail
        self.local = local
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    @property
    def status_path(self) -> Path:
        return _autoscheduler_status_path(self.settings)

    def _status_payload(self, **extra: object) -> dict[str, object]:
        now_utc = datetime.now(timezone.utc)
        payload: dict[str, object] = {
            "status": "running",
            "scheduler_kind": "application_server_interval",
            "pid": os.getpid(),
            "thread_alive": bool(self._thread and self._thread.is_alive()),
            "interval_seconds": self.interval_seconds,
            "initial_delay_seconds": self.initial_delay_seconds,
            "send_mail_requested": self.send_mail,
            "local_notification_requested": self.local,
            "updated_at": now_utc.isoformat(timespec="seconds"),
            "status_path": str(self.status_path),
            "next_check_after_utc": (now_utc + timedelta(seconds=self.interval_seconds)).isoformat(timespec="seconds"),
            "next_real_slot": _next_real_slot_snapshot(self.settings),
        }
        payload.update(extra)
        return payload

    def _write_status(self, **extra: object) -> dict[str, object]:
        payload = self._status_payload(**extra)
        _atomic_write_json(self.status_path, payload)
        return payload

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._write_status(status="starting", last_tick_action=None, last_exit_code=None)
        self._thread = threading.Thread(target=self._run_loop, name="SerenityAutoScheduler", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)
        self._write_status(
            status="stopped",
            thread_alive=bool(self._thread and self._thread.is_alive()),
            last_exit_code=0,
        )

    def run_once(self) -> dict[str, object]:
        started = datetime.now(timezone.utc)
        try:
            with _APPLICATION_WRITE_LOCK:
                tick_result = automation_tick(
                    self.settings,
                    dry_run=False,
                    send_mail=self.send_mail,
                    local=self.local,
                )
            action = str(tick_result.get("action") or "")
            scheduler = tick_result.get("scheduler") if isinstance(tick_result.get("scheduler"), dict) else {}
            run_id = tick_result.get("run_id") or (scheduler or {}).get("run_id")
            due_slot = tick_result.get("due_slot") or (scheduler or {}).get("due_slot")
            return self._write_status(
                status="success",
                last_tick_started_at=started.isoformat(timespec="seconds"),
                last_tick_finished_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
                last_tick_action=action,
                last_due_slot=due_slot,
                last_run_id=run_id,
                last_exit_code=0,
                last_error=None,
                last_result=tick_result,
            )
        except Exception as exc:  # pragma: no cover - production boundary
            return self._write_status(
                status="error",
                last_tick_started_at=started.isoformat(timespec="seconds"),
                last_tick_finished_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
                last_tick_action="error",
                last_exit_code=1,
                last_error=f"{type(exc).__name__}: {exc}",
                traceback=traceback.format_exc(limit=12),
            )

    def _run_loop(self) -> None:
        if self.initial_delay_seconds and self._stop_event.wait(self.initial_delay_seconds):
            return
        while not self._stop_event.is_set():
            self.run_once()
            self._stop_event.wait(self.interval_seconds)


def _pct_compact(value: float) -> str:
    formatted = f"{value * 100:.2f}".rstrip("0").rstrip(".")
    return f"{formatted}%"


def _refresh_time(settings: Settings) -> str:
    return format_now_display(settings.timezone_secondary)


def _select_manual_refresh_slot(settings: Settings, current: datetime | None = None) -> tuple[str, datetime]:
    primary_zone = ZoneInfo(settings.timezone_primary)
    beijing_now = (current or datetime.now(primary_zone)).astimezone(primary_zone)

    selected_slot = next(iter(SCHEDULE_SLOTS))
    for slot, hhmm in SCHEDULE_SLOTS.items():
        hour, minute = [int(part) for part in hhmm.split(":")]
        scheduled = datetime.combine(beijing_now.date(), time(hour, minute), tzinfo=primary_zone)
        if scheduled <= beijing_now:
            selected_slot = slot
        else:
            break
    return selected_slot, beijing_now


def _run_manual_serenity_refresh(settings: Settings) -> dict[str, object]:
    init_db(settings.db_path)
    slot, run_datetime_bj = _select_manual_refresh_slot(settings)
    result = run_slot(
        settings,
        slot,
        dry_run=False,
        send_mail=False,
        run_date=run_datetime_bj.date(),
        run_datetime_bj=run_datetime_bj,
    )
    created_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with connect(settings.db_path) as conn:
        conn.execute(
            """
            INSERT INTO automation_tick_log (
              tick_time_bj, tick_time_au, due_slot, action, run_id, dry_run, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_datetime_bj.isoformat(timespec="seconds"),
                run_datetime_bj.astimezone(ZoneInfo(settings.timezone_secondary)).isoformat(timespec="seconds"),
                slot,
                "manual_refresh_ran",
                result["run_id"],
                0,
                created_at,
            ),
        )
    return {
        "action": "manual_serenity_run",
        "due_slot": slot,
        "run_date": run_datetime_bj.date().isoformat(),
        "run_time_bj": run_datetime_bj.isoformat(timespec="seconds"),
        "run_id": result["run_id"],
        "result": result,
    }


def _latest_holdings(settings: Settings) -> dict[str, RefreshHolding]:
    init_db(settings.db_path)
    with connect(settings.db_path) as conn:
        latest_rows = conn.execute(
            """
            SELECT run_id, run_time_bj, created_at FROM run_log
            WHERE report_path IS NOT NULL
              AND schedule_slot LIKE 'R%'
            ORDER BY run_time_bj DESC, created_at DESC, rowid DESC LIMIT 12
            """
        ).fetchall()
        visible_rows = [
            row for row in latest_rows if not is_future_controlled_backfill(row["run_time_bj"], row["created_at"])
        ]
        latest = (visible_rows or latest_rows or [None])[0]
        if not latest:
            return {}
        rows = conn.execute(
            """
            SELECT a.asset_code, a.asset_name, r.target_weight
            FROM recommendation_snapshot r
            JOIN asset_master a ON a.asset_id=r.asset_id
            WHERE r.run_id=?
              AND r.rank BETWEEN 1 AND 5
            ORDER BY r.rank ASC
            """,
            (latest["run_id"],),
        ).fetchall()
    return {
        row["asset_code"]: RefreshHolding(
            code=row["asset_code"],
            name=row["asset_name"],
            weight=float(row["target_weight"] or 0.0),
        )
        for row in rows
    }


def summarize_refresh_changes(
    before: dict[str, RefreshHolding],
    after: dict[str, RefreshHolding],
    *,
    relative_threshold: float = 0.01,
) -> str:
    if not after:
        return "暂无持仓建议"

    changes: list[str] = []
    for code, current in after.items():
        previous = before.get(code)
        if previous is None:
            changes.append(f"买入{code} 到{_pct_compact(current.weight)}")
            continue
        delta = current.weight - previous.weight
        if abs(delta) < 0.0001:
            continue
        ratio = delta / previous.weight if previous.weight else delta
        if abs(ratio) <= relative_threshold:
            continue
        action = "增仓" if delta > 0 else "减仓"
        changes.append(f"{action}{code} {_pct_compact(abs(delta))}到{_pct_compact(current.weight)}")

    for code in before:
        if code not in after:
            changes.append(f"卖出{code} 到0%")

    return "；".join(changes) if changes else "保持当前持仓"


def build_refresh_message(
    settings: Settings,
    before: dict[str, RefreshHolding],
    after: dict[str, RefreshHolding],
) -> str:
    return f"目前更新到最新时间 {_refresh_time(settings)} {summarize_refresh_changes(before, after)}"


def _parse_iso_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    normalized = value.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _manual_review_outcome(payload: dict[str, object]) -> tuple[str, dict[str, str]]:
    raw = str(payload.get("outcome") or payload.get("decision") or "").strip()
    if raw in MANUAL_REVIEW_OUTCOMES:
        return raw, MANUAL_REVIEW_OUTCOMES[raw]
    for key, item in MANUAL_REVIEW_OUTCOMES.items():
        if raw == item["label"]:
            return key, item
    legacy_map = {
        "保持禁止新增": "observe_pool",
        "需要补证据": "observe_pool",
        "确认观察": "observe_pool",
        "已人工处理": "exclude_current_observation",
    }
    key = legacy_map.get(raw, "observe_pool")
    return key, MANUAL_REVIEW_OUTCOMES[key]


def refresh_application(settings: Settings) -> dict[str, object]:
    with _APPLICATION_WRITE_LOCK:
        before = _latest_holdings(settings)
        tick_result = _run_manual_serenity_refresh(settings)
        portal_result = build_application_portal(settings, install_apps=False)
        after = _latest_holdings(settings)
        return {
            "status": "pass",
            "message": build_refresh_message(settings, before, after),
            "action_summary": summarize_refresh_changes(before, after),
            "tick_action": tick_result["action"],
            "due_slot": tick_result.get("due_slot"),
            "run_date": tick_result.get("run_date"),
            "run_id": tick_result.get("run_id"),
            "portal_path": portal_result.get("portal_path"),
        }


def fetch_manual_review_decisions(settings: Settings) -> dict[str, dict[str, object]]:
    init_db(settings.db_path)
    with connect(settings.db_path) as conn:
        now = datetime.now(timezone.utc)
        stale_rows = conn.execute(
            """
            SELECT review_id, updated_at, created_at
            FROM manual_review_decision
            WHERE refresh_status='running'
            """
        ).fetchall()
        for stale in stale_rows:
            last_update = _parse_iso_datetime(stale["updated_at"]) or _parse_iso_datetime(stale["created_at"])
            if last_update and (now - last_update).total_seconds() <= MANUAL_REVIEW_STALE_REFRESH_SECONDS:
                continue
            conn.execute(
                """
                UPDATE manual_review_decision
                SET refresh_status='error',
                    refresh_message='后台刷新超过15分钟未完成；复核已写入数据库，请点击刷新重新同步首页',
                    updated_at=?
                WHERE review_id=? AND refresh_status='running'
                """,
                (now.isoformat(), stale["review_id"]),
            )
        rows = conn.execute(
            """
            SELECT review_id, run_id, decision, outcome, outcome_label, system_disposition,
                   refresh_triggered, refresh_status, refresh_message, refresh_run_id,
                   note, saved_at, updated_at
            FROM manual_review_decision
            ORDER BY updated_at DESC, review_id ASC
            """
        ).fetchall()
    return {
        str(row["review_id"]): {
            "review_id": int(row["review_id"]),
            "run_id": row["run_id"],
            "decision": row["decision"],
            "outcome": row["outcome"] or "",
            "outcomeLabel": row["outcome_label"] or row["decision"],
            "systemDisposition": row["system_disposition"] or "",
            "refreshTriggered": bool(row["refresh_triggered"]),
            "refreshStatus": row["refresh_status"] or "",
            "refreshMessage": row["refresh_message"] or "",
            "refreshRunId": row["refresh_run_id"] or "",
            "note": row["note"] or "",
            "savedAt": row["saved_at"],
            "updatedAt": row["updated_at"],
            "source": "sqlite",
        }
        for row in rows
    }


def _update_manual_review_refresh_result(
    settings: Settings,
    review_id: int,
    *,
    refresh_status: str,
    refresh_message: str,
    refresh_run_id: str,
) -> None:
    now = datetime.now(timezone.utc).isoformat()
    with connect(settings.db_path) as conn:
        conn.execute(
            """
            UPDATE manual_review_decision
            SET refresh_triggered=?, refresh_status=?, refresh_message=?,
                refresh_run_id=?, updated_at=?
            WHERE review_id=?
            """,
            (1, refresh_status, refresh_message, refresh_run_id, now, review_id),
        )


def _refresh_manual_review_async(settings: Settings, review_id: int) -> None:
    try:
        try:
            refresh_result = refresh_application(settings)
            refresh_status = str(refresh_result.get("status") or "pass")
            refresh_message = str(refresh_result.get("message") or "")
            refresh_run_id = str(refresh_result.get("run_id") or "")
        except Exception as exc:  # pragma: no cover - production boundary
            refresh_status = "error"
            refresh_message = f"同步刷新失败：{exc}"
            refresh_run_id = ""
        _update_manual_review_refresh_result(
            settings,
            review_id,
            refresh_status=refresh_status,
            refresh_message=refresh_message,
            refresh_run_id=refresh_run_id,
        )
    finally:
        with _MANUAL_REVIEW_REFRESH_LOCK:
            _MANUAL_REVIEW_REFRESH_IN_FLIGHT.discard(review_id)


def _start_manual_review_refresh(settings: Settings, review_id: int) -> bool:
    with _MANUAL_REVIEW_REFRESH_LOCK:
        if review_id in _MANUAL_REVIEW_REFRESH_IN_FLIGHT:
            return False
        _MANUAL_REVIEW_REFRESH_IN_FLIGHT.add(review_id)
    thread = threading.Thread(
        target=_refresh_manual_review_async,
        args=(settings, review_id),
        name=f"SerenityManualReviewRefresh-{review_id}",
        daemon=True,
    )
    thread.start()
    return True


def save_manual_review_decision(
    settings: Settings,
    payload: dict[str, object],
    *,
    refresh_async: bool = False,
) -> dict[str, object]:
    try:
        review_id = int(str(payload.get("review_id") or payload.get("reviewId") or "").strip())
    except ValueError as exc:
        raise ValueError("review_id must be an integer") from exc
    outcome, outcome_config = _manual_review_outcome(payload)
    decision = outcome_config["label"]
    system_disposition = outcome_config["system_disposition"]
    note = str(payload.get("note") or "").strip()
    saved_at = str(payload.get("saved_at") or payload.get("savedAt") or "").strip()
    if not saved_at:
        saved_at = datetime.now(timezone.utc).isoformat()

    init_db(settings.db_path)
    now = datetime.now(timezone.utc).isoformat()
    refresh_triggered = True
    refresh_status = "running" if refresh_async else ""
    refresh_message = "已保存到数据库，正在重新运行 Serenity 全流程" if refresh_async else ""
    refresh_run_id = ""
    with connect(settings.db_path) as conn:
        queue_row = conn.execute(
            """
            SELECT m.run_id, m.reason, m.action_blocked, m.asset_id,
                   a.asset_code, a.asset_name
            FROM manual_review_queue m
            LEFT JOIN asset_master a ON a.asset_id=m.asset_id
            WHERE m.id=?
            """,
            (review_id,),
        ).fetchone()
        run_id = str(payload.get("run_id") or payload.get("runId") or (queue_row["run_id"] if queue_row else "")).strip()
        if not run_id:
            raise ValueError("run_id is required when review_id is not present in manual_review_queue")
        conn.execute(
            """
            INSERT INTO manual_review_decision (
                review_id, run_id, decision, outcome, outcome_label, system_disposition,
                refresh_triggered, refresh_status, refresh_message, refresh_run_id,
                note, saved_at, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(review_id) DO UPDATE SET
                run_id=excluded.run_id,
                decision=excluded.decision,
                outcome=excluded.outcome,
                outcome_label=excluded.outcome_label,
                system_disposition=excluded.system_disposition,
                refresh_triggered=excluded.refresh_triggered,
                refresh_status=excluded.refresh_status,
                refresh_message=excluded.refresh_message,
                refresh_run_id=excluded.refresh_run_id,
                note=excluded.note,
                saved_at=excluded.saved_at,
                updated_at=excluded.updated_at
            """,
            (
                review_id,
                run_id,
                decision,
                outcome,
                outcome_config["label"],
                system_disposition,
                int(refresh_triggered),
                refresh_status,
                refresh_message,
                refresh_run_id,
                note,
                saved_at,
                now,
                now,
            ),
        )

    if refresh_async:
        if not _start_manual_review_refresh(settings, review_id):
            refresh_message = "已保存到数据库，上一轮 Serenity 后台刷新仍在运行"
            _update_manual_review_refresh_result(
                settings,
                review_id,
                refresh_status="running",
                refresh_message=refresh_message,
                refresh_run_id="",
            )
    elif refresh_triggered:
        try:
            refresh_result = refresh_application(settings)
            refresh_status = str(refresh_result.get("status") or "pass")
            refresh_message = str(refresh_result.get("message") or "")
            refresh_run_id = str(refresh_result.get("run_id") or "")
        except Exception as exc:  # pragma: no cover - production boundary
            refresh_status = "error"
            refresh_message = f"同步刷新失败：{exc}"
            refresh_run_id = ""

        _update_manual_review_refresh_result(
            settings,
            review_id,
            refresh_status=refresh_status,
            refresh_message=refresh_message,
            refresh_run_id=refresh_run_id,
        )

    reason = queue_row["reason"] if queue_row else ""
    action_blocked = queue_row["action_blocked"] if queue_row else ""
    asset_code = queue_row["asset_code"] if queue_row and queue_row["asset_code"] else ""
    asset_name = queue_row["asset_name"] if queue_row and queue_row["asset_name"] else ""
    return {
        "status": "pass",
        "record": {
            "review_id": review_id,
            "run_id": run_id,
            "decision": decision,
            "outcome": outcome,
            "outcomeLabel": outcome_config["label"],
            "systemDisposition": system_disposition,
            "reviewReason": reason,
            "actionBlocked": action_blocked,
            "assetCode": asset_code,
            "assetName": asset_name,
            "refreshTriggered": refresh_triggered,
            "refreshStatus": refresh_status,
            "refreshMessage": refresh_message,
            "refreshRunId": refresh_run_id,
            "note": note,
            "savedAt": saved_at,
            "updatedAt": now,
            "source": "sqlite",
        },
    }


def clear_manual_review_decisions(settings: Settings) -> dict[str, object]:
    init_db(settings.db_path)
    with connect(settings.db_path) as conn:
        deleted = conn.execute("DELETE FROM manual_review_decision").rowcount
    return {"status": "pass", "deleted": int(deleted or 0)}


def _json_bytes(payload: dict[str, object]) -> bytes:
    return json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")


def make_handler(settings: Settings) -> type[BaseHTTPRequestHandler]:
    root_dir = settings.root_dir
    portal_path = root_dir / "outputs" / "application" / "index.html"

    class SerenityApplicationHandler(BaseHTTPRequestHandler):
        server_version = "SerenityApplicationServer/1.0"

        def log_message(self, format: str, *args: object) -> None:  # noqa: A002
            return

        def _send_bytes(self, body: bytes, content_type: str, status: HTTPStatus = HTTPStatus.OK) -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.end_headers()
            self.wfile.write(body)

        def _read_json_body(self) -> dict[str, object]:
            length = int(self.headers.get("Content-Length") or "0")
            if length <= 0:
                return {}
            raw = self.rfile.read(length)
            payload = json.loads(raw.decode("utf-8"))
            if not isinstance(payload, dict):
                raise ValueError("JSON body must be an object")
            return payload

        def do_GET(self) -> None:  # noqa: N802
            path = urlparse(self.path).path
            if path == "/api/health":
                self._send_bytes(_json_bytes({"status": "ok"}), "application/json; charset=utf-8")
                return
            if path == "/api/scheduler/status":
                self._send_bytes(_json_bytes(read_autoscheduler_status(settings)), "application/json; charset=utf-8")
                return
            if path == "/api/manual-review":
                self._send_bytes(
                    _json_bytes({"status": "pass", "records": fetch_manual_review_decisions(settings)}),
                    "application/json; charset=utf-8",
                )
                return
            if path not in {"/", "/index.html"}:
                self.send_error(HTTPStatus.NOT_FOUND, "Not found")
                return
            if not portal_path.exists():
                build_application_portal(settings, install_apps=False)
            self._send_bytes(portal_path.read_bytes(), "text/html; charset=utf-8")

        def do_POST(self) -> None:  # noqa: N802
            path = urlparse(self.path).path
            if path == "/api/manual-review":
                try:
                    with _MANUAL_REVIEW_WRITE_LOCK:
                        result = save_manual_review_decision(settings, self._read_json_body(), refresh_async=True)
                    self._send_bytes(_json_bytes(result), "application/json; charset=utf-8")
                except Exception as exc:  # pragma: no cover - defensive HTTP boundary
                    body = _json_bytes({"status": "error", "message": f"保存复核失败：{exc}"})
                    self._send_bytes(body, "application/json; charset=utf-8", HTTPStatus.BAD_REQUEST)
                return
            if path != "/api/refresh":
                self.send_error(HTTPStatus.NOT_FOUND, "Not found")
                return
            try:
                result = refresh_application(settings)
                self._send_bytes(_json_bytes(result), "application/json; charset=utf-8")
            except Exception as exc:  # pragma: no cover - defensive HTTP boundary
                body = _json_bytes({"status": "error", "message": f"刷新失败：{exc}"})
                self._send_bytes(body, "application/json; charset=utf-8", HTTPStatus.INTERNAL_SERVER_ERROR)

        def do_DELETE(self) -> None:  # noqa: N802
            path = urlparse(self.path).path
            if path != "/api/manual-review":
                self.send_error(HTTPStatus.NOT_FOUND, "Not found")
                return
            try:
                with _MANUAL_REVIEW_WRITE_LOCK:
                    result = clear_manual_review_decisions(settings)
                self._send_bytes(_json_bytes(result), "application/json; charset=utf-8")
            except Exception as exc:  # pragma: no cover - defensive HTTP boundary
                body = _json_bytes({"status": "error", "message": f"清空复核失败：{exc}"})
                self._send_bytes(body, "application/json; charset=utf-8", HTTPStatus.INTERNAL_SERVER_ERROR)

        def do_OPTIONS(self) -> None:  # noqa: N802
            self._send_bytes(b"", "text/plain; charset=utf-8", HTTPStatus.NO_CONTENT)

    return SerenityApplicationHandler


def _auto_shutdown_seconds(configured: int | None = None) -> int:
    if configured is not None:
        return max(0, int(configured))
    raw = os.environ.get("SERENITY_APPLICATION_SERVER_TTL_SECONDS", str(DEFAULT_AUTO_SHUTDOWN_SECONDS)).strip()
    try:
        return max(0, int(raw))
    except ValueError:
        return DEFAULT_AUTO_SHUTDOWN_SECONDS


def serve_application(
    settings: Settings,
    host: str = "127.0.0.1",
    port: int = 8765,
    ttl_seconds: int | None = None,
    enable_autoscheduler: bool | None = None,
    autoscheduler_interval_seconds: int | None = None,
    autoscheduler_initial_delay_seconds: int | None = None,
) -> None:
    init_db(settings.db_path)
    portal_path = settings.root_dir / "outputs" / "application" / "index.html"
    if not portal_path.exists():
        build_application_portal(settings, install_apps=False)
    handler = make_handler(settings)
    server = ThreadingHTTPServer((host, port), handler)
    shutdown_timer: threading.Timer | None = None
    autoscheduler: ApplicationAutoScheduler | None = None
    auto_shutdown_seconds = _auto_shutdown_seconds(ttl_seconds)
    if auto_shutdown_seconds > 0:
        shutdown_timer = threading.Timer(auto_shutdown_seconds, server.shutdown)
        shutdown_timer.daemon = True
        shutdown_timer.start()
    if enable_autoscheduler is None:
        enable_autoscheduler = _bool_env("SERENITY_APP_AUTOSCHEDULER_ENABLED", True)
    if enable_autoscheduler:
        autoscheduler = ApplicationAutoScheduler(
            settings,
            interval_seconds=autoscheduler_interval_seconds
            if autoscheduler_interval_seconds is not None
            else _int_env("SERENITY_APP_AUTOSCHEDULER_INTERVAL_SECONDS", DEFAULT_AUTOSCHEDULER_INTERVAL_SECONDS),
            initial_delay_seconds=autoscheduler_initial_delay_seconds
            if autoscheduler_initial_delay_seconds is not None
            else _int_env(
                "SERENITY_APP_AUTOSCHEDULER_INITIAL_DELAY_SECONDS",
                DEFAULT_AUTOSCHEDULER_INITIAL_DELAY_SECONDS,
            ),
        )
        autoscheduler.start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        if autoscheduler:
            autoscheduler.stop()
        if shutdown_timer:
            shutdown_timer.cancel()
        server.server_close()


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Run the local Serenity application server.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--ttl-seconds", type=int, default=None)
    parser.add_argument("--disable-autoscheduler", action="store_true")
    parser.add_argument("--autoscheduler-interval-seconds", type=int, default=None)
    parser.add_argument("--autoscheduler-initial-delay-seconds", type=int, default=None)
    args = parser.parse_args(argv)
    settings = Settings.load()
    settings.ensure_dirs()
    serve_application(
        settings,
        host=args.host,
        port=args.port,
        ttl_seconds=args.ttl_seconds,
        enable_autoscheduler=not args.disable_autoscheduler,
        autoscheduler_interval_seconds=args.autoscheduler_interval_seconds,
        autoscheduler_initial_delay_seconds=args.autoscheduler_initial_delay_seconds,
    )
    return 0


if __name__ == "__main__":  # pragma: no cover - launcher entry
    raise SystemExit(main())
