from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from app.config import Settings
from app.core.application_portal import build_application_portal
from app.core.automation_tick import automation_tick
from app.core.time_display import format_now_display
from app.db import connect, init_db


@dataclass(frozen=True)
class RefreshHolding:
    code: str
    name: str
    weight: float


def _pct_compact(value: float) -> str:
    formatted = f"{value * 100:.2f}".rstrip("0").rstrip(".")
    return f"{formatted}%"


def _refresh_time(settings: Settings) -> str:
    return format_now_display(settings.timezone_secondary)


def _latest_holdings(settings: Settings) -> dict[str, RefreshHolding]:
    init_db(settings.db_path)
    with connect(settings.db_path) as conn:
        latest = conn.execute(
            """
            SELECT run_id FROM run_log
            WHERE report_path IS NOT NULL
              AND schedule_slot LIKE 'R%'
            ORDER BY created_at DESC, rowid DESC LIMIT 1
            """
        ).fetchone()
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


def refresh_application(settings: Settings) -> dict[str, object]:
    before = _latest_holdings(settings)
    tick_result = automation_tick(
        settings,
        dry_run=False,
        allow_duplicate=False,
        scan_paths=[],
        send_mail=False,
        local=False,
    )
    portal_result = build_application_portal(settings)
    after = _latest_holdings(settings)
    return {
        "status": "pass",
        "message": build_refresh_message(settings, before, after),
        "action_summary": summarize_refresh_changes(before, after),
        "tick_action": tick_result.get("action"),
        "due_slot": tick_result.get("due_slot"),
        "run_id": tick_result.get("scheduler", {}).get("run_id")
        if isinstance(tick_result.get("scheduler"), dict)
        else None,
        "portal_path": portal_result.get("portal_path"),
    }


def fetch_manual_review_decisions(settings: Settings) -> dict[str, dict[str, object]]:
    init_db(settings.db_path)
    with connect(settings.db_path) as conn:
        rows = conn.execute(
            """
            SELECT review_id, run_id, decision, note, saved_at, updated_at
            FROM manual_review_decision
            ORDER BY updated_at DESC, review_id ASC
            """
        ).fetchall()
    return {
        str(row["review_id"]): {
            "review_id": int(row["review_id"]),
            "run_id": row["run_id"],
            "decision": row["decision"],
            "note": row["note"] or "",
            "savedAt": row["saved_at"],
            "updatedAt": row["updated_at"],
            "source": "sqlite",
        }
        for row in rows
    }


def save_manual_review_decision(settings: Settings, payload: dict[str, object]) -> dict[str, object]:
    try:
        review_id = int(str(payload.get("review_id") or payload.get("reviewId") or "").strip())
    except ValueError as exc:
        raise ValueError("review_id must be an integer") from exc
    decision = str(payload.get("decision") or "").strip() or "保持禁止新增"
    note = str(payload.get("note") or "").strip()
    saved_at = str(payload.get("saved_at") or payload.get("savedAt") or "").strip()
    if not saved_at:
        saved_at = datetime.now(timezone.utc).isoformat()

    init_db(settings.db_path)
    now = datetime.now(timezone.utc).isoformat()
    with connect(settings.db_path) as conn:
        queue_row = conn.execute(
            "SELECT run_id FROM manual_review_queue WHERE id=?",
            (review_id,),
        ).fetchone()
        run_id = str(payload.get("run_id") or payload.get("runId") or (queue_row["run_id"] if queue_row else "")).strip()
        if not run_id:
            raise ValueError("run_id is required when review_id is not present in manual_review_queue")
        conn.execute(
            """
            INSERT INTO manual_review_decision (
                review_id, run_id, decision, note, saved_at, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(review_id) DO UPDATE SET
                run_id=excluded.run_id,
                decision=excluded.decision,
                note=excluded.note,
                saved_at=excluded.saved_at,
                updated_at=excluded.updated_at
            """,
            (review_id, run_id, decision, note, saved_at, now, now),
        )
    return {
        "status": "pass",
        "record": {
            "review_id": review_id,
            "run_id": run_id,
            "decision": decision,
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
                build_application_portal(settings)
            self._send_bytes(portal_path.read_bytes(), "text/html; charset=utf-8")

        def do_POST(self) -> None:  # noqa: N802
            path = urlparse(self.path).path
            if path == "/api/manual-review":
                try:
                    result = save_manual_review_decision(settings, self._read_json_body())
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
                self._send_bytes(_json_bytes(clear_manual_review_decisions(settings)), "application/json; charset=utf-8")
            except Exception as exc:  # pragma: no cover - defensive HTTP boundary
                body = _json_bytes({"status": "error", "message": f"清空复核失败：{exc}"})
                self._send_bytes(body, "application/json; charset=utf-8", HTTPStatus.INTERNAL_SERVER_ERROR)

    return SerenityApplicationHandler


def serve_application(settings: Settings, host: str = "127.0.0.1", port: int = 8765) -> None:
    build_application_portal(settings)
    handler = make_handler(settings)
    server = ThreadingHTTPServer((host, port), handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
