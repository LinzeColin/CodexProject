from __future__ import annotations

import argparse
import json
import mimetypes
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Callable
from urllib.parse import parse_qs, unquote, urlparse

from .query import (
    PERIOD_TABLES,
    connect_readonly,
    list_question_templates,
    query_categories,
    query_control_plan,
    query_daily_cashflow,
    query_question,
    query_review,
    query_review_candidate_groups,
    query_review_candidates,
    query_review_status,
    query_risks,
    query_source_platforms,
    query_stats,
    query_transactions,
)


DEFAULT_DB = Path("data/finance_ledger/finance_ledger.sqlite")
DEFAULT_REPORT_DIR = Path("outputs/finance_ledger_20220605_20260603/reports")


def _int_param(params: dict[str, list[str]], name: str, default: int, *, minimum: int = 1, maximum: int = 500) -> int:
    raw = params.get(name, [str(default)])[0]
    try:
        value = int(raw)
    except ValueError:
        value = default
    return max(minimum, min(maximum, value))


def _float_param(params: dict[str, list[str]], name: str) -> float | None:
    raw = params.get(name, [""])[0]
    if not raw:
        return None
    try:
        return float(raw)
    except ValueError:
        return None


def _text_param(params: dict[str, list[str]], name: str) -> str:
    return params.get(name, [""])[0].strip()


def _json_bytes(payload: Any) -> bytes:
    return json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")


def _safe_static_path(root: Path, raw_path: str) -> Path | None:
    relative = unquote(raw_path.removeprefix("/reports/")).strip("/")
    if not relative:
        relative = "index.html"
    candidate = (root / relative).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError:
        return None
    return candidate


class LedgerApiServer(ThreadingHTTPServer):
    def __init__(self, server_address: tuple[str, int], handler: type[BaseHTTPRequestHandler], *, db_path: Path, report_dir: Path) -> None:
        super().__init__(server_address, handler)
        self.db_path = db_path
        self.report_dir = report_dir


class LedgerApiHandler(BaseHTTPRequestHandler):
    server: LedgerApiServer

    def log_message(self, format: str, *args: Any) -> None:
        return

    def _send(self, status: HTTPStatus, body: bytes, content_type: str = "application/json; charset=utf-8") -> None:
        self.send_response(status.value)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Access-Control-Allow-Origin", "http://127.0.0.1")
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, status: HTTPStatus, payload: Any) -> None:
        self._send(status, _json_bytes(payload))

    def _send_error(self, status: HTTPStatus, message: str) -> None:
        self._send_json(status, {"ok": False, "error": message})

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        try:
            if parsed.path == "/" or parsed.path == "/api":
                self._send_json(HTTPStatus.OK, self._api_index())
                return
            if parsed.path.startswith("/reports/"):
                self._serve_static(parsed.path)
                return
            if not parsed.path.startswith("/api/"):
                self._send_error(HTTPStatus.NOT_FOUND, "unknown route")
                return
            route = parsed.path.removeprefix("/api/")
            self._serve_api(route, params)
        except FileNotFoundError as exc:
            self._send_error(HTTPStatus.NOT_FOUND, str(exc))
        except ValueError as exc:
            self._send_error(HTTPStatus.BAD_REQUEST, str(exc))

    def _api_index(self) -> dict[str, Any]:
        return {
            "ok": True,
            "service": "finance-ledger-readonly-api",
            "mode": "read_only",
            "db_path": str(self.server.db_path),
            "report_dir": str(self.server.report_dir),
            "endpoints": [
                "/api/health",
                "/api/metadata",
                "/api/stats?period=month&limit=12",
                "/api/categories?limit=30",
                "/api/risks?limit=20",
                "/api/control-plan?limit=20",
                "/api/review?limit=30",
                "/api/review-status",
                "/api/review-candidates?limit=100",
                "/api/review-candidate-groups?limit=100",
                "/api/source-platforms",
                "/api/daily-cashflow?limit=90",
                "/api/ask?q=本月现金流如何&limit=10",
                "/api/question-templates",
                "/api/transactions?month=2026-06&limit=50",
                "/reports/index.html",
            ],
        }

    def _with_conn(self, fn: Callable[[Any], Any]) -> Any:
        with connect_readonly(self.server.db_path) as conn:
            return fn(conn)

    def _serve_api(self, route: str, params: dict[str, list[str]]) -> None:
        if route == "health":
            self._send_json(HTTPStatus.OK, self._health())
            return
        if route == "metadata":
            self._send_json(HTTPStatus.OK, {"ok": True, "data": self._metadata()})
            return
        if route == "stats":
            period = _text_param(params, "period") or "month"
            if period not in PERIOD_TABLES:
                raise ValueError(f"unsupported period: {period}")
            limit = _int_param(params, "limit", 12)
            self._send_json(HTTPStatus.OK, {"ok": True, "data": self._with_conn(lambda conn: query_stats(conn, period, limit))})
            return
        if route == "categories":
            limit = _int_param(params, "limit", 30)
            self._send_json(HTTPStatus.OK, {"ok": True, "data": self._with_conn(lambda conn: query_categories(conn, limit))})
            return
        if route == "risks":
            limit = _int_param(params, "limit", 20)
            self._send_json(HTTPStatus.OK, {"ok": True, "data": self._with_conn(lambda conn: query_risks(conn, limit))})
            return
        if route == "control-plan":
            limit = _int_param(params, "limit", 20)
            self._send_json(HTTPStatus.OK, {"ok": True, "data": self._with_conn(lambda conn: query_control_plan(conn, limit))})
            return
        if route == "review":
            limit = _int_param(params, "limit", 30)
            self._send_json(HTTPStatus.OK, {"ok": True, "data": self._with_conn(lambda conn: query_review(conn, limit))})
            return
        if route == "review-status":
            self._send_json(HTTPStatus.OK, {"ok": True, "data": self._with_conn(query_review_status)})
            return
        if route == "review-candidates":
            limit = _int_param(params, "limit", 100)
            self._send_json(HTTPStatus.OK, {"ok": True, "data": self._with_conn(lambda conn: query_review_candidates(conn, limit))})
            return
        if route == "review-candidate-groups":
            limit = _int_param(params, "limit", 100)
            self._send_json(HTTPStatus.OK, {"ok": True, "data": self._with_conn(lambda conn: query_review_candidate_groups(conn, limit))})
            return
        if route == "source-platforms":
            self._send_json(HTTPStatus.OK, {"ok": True, "data": self._with_conn(query_source_platforms)})
            return
        if route == "daily-cashflow":
            limit = _int_param(params, "limit", 90)
            self._send_json(HTTPStatus.OK, {"ok": True, "data": self._with_conn(lambda conn: query_daily_cashflow(conn, limit))})
            return
        if route == "question-templates":
            self._send_json(HTTPStatus.OK, {"ok": True, "data": list_question_templates()})
            return
        if route == "ask":
            question = _text_param(params, "q") or _text_param(params, "question")
            limit = _int_param(params, "limit", 20)
            if not question:
                raise ValueError("missing q")
            self._send_json(HTTPStatus.OK, self._with_conn(lambda conn: query_question(conn, question, limit)))
            return
        if route == "transactions":
            limit = _int_param(params, "limit", 50)
            self._send_json(
                HTTPStatus.OK,
                {
                    "ok": True,
                    "data": self._with_conn(
                        lambda conn: query_transactions(
                            conn,
                            month=_text_param(params, "month"),
                            main_category=_text_param(params, "main_category"),
                            sub_category=_text_param(params, "sub_category"),
                            risk_tag=_text_param(params, "risk_tag"),
                            counterparty=_text_param(params, "counterparty"),
                            min_amount=_float_param(params, "min_amount"),
                            limit=limit,
                        )
                    ),
                },
            )
            return
        self._send_error(HTTPStatus.NOT_FOUND, "unknown api endpoint")

    def _health(self) -> dict[str, Any]:
        metadata = self._metadata()
        return {
            "ok": True,
            "db_exists": self.server.db_path.exists(),
            "report_dir_exists": self.server.report_dir.exists(),
            "schema_version": metadata.get("schema_version", ""),
            "transaction_count": metadata.get("transaction_count", ""),
            "date_start": metadata.get("date_start", ""),
            "date_end": metadata.get("date_end", ""),
        }

    def _metadata(self) -> dict[str, str]:
        def fetch(conn: Any) -> dict[str, str]:
            return {str(row["key"]): str(row["value"]) for row in conn.execute("select key,value from ledger_metadata")}

        return self._with_conn(fetch)

    def _serve_static(self, raw_path: str) -> None:
        target = _safe_static_path(self.server.report_dir, raw_path)
        if target is None or not target.exists() or not target.is_file():
            self._send_error(HTTPStatus.NOT_FOUND, "report not found")
            return
        content_type = mimetypes.guess_type(str(target))[0] or "application/octet-stream"
        self._send(HTTPStatus.OK, target.read_bytes(), content_type)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Serve the finance ledger through a local read-only HTTP API.")
    parser.add_argument("--db", default=str(DEFAULT_DB), help="SQLite ledger path.")
    parser.add_argument("--reports", default=str(DEFAULT_REPORT_DIR), help="Report directory to serve under /reports/.")
    parser.add_argument("--host", default="127.0.0.1", help="Bind host. Keep 127.0.0.1 unless you add auth and network controls.")
    parser.add_argument("--port", type=int, default=8766, help="Bind port.")
    return parser


def serve(db_path: str | Path = DEFAULT_DB, report_dir: str | Path = DEFAULT_REPORT_DIR, host: str = "127.0.0.1", port: int = 8766) -> None:
    server = LedgerApiServer((host, port), LedgerApiHandler, db_path=Path(db_path), report_dir=Path(report_dir))
    print(f"Finance ledger read-only API: http://{host}:{port}/api")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    finally:
        server.server_close()


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    serve(args.db, args.reports, args.host, args.port)
    return 0
