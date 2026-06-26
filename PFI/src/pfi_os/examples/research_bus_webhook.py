from __future__ import annotations

import argparse
import json
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from pfi_os.integrations.research_bus_api import process_pending_bus_requests, research_bus_health_summary, submit_webhook_payload


class ResearchBusWebhookHandler(BaseHTTPRequestHandler):
    server_version = "PFIOSResearchBusWebhook/1.0"

    def do_GET(self) -> None:  # noqa: N802 - stdlib handler API
        parsed = urlparse(self.path)
        if parsed.path in {"/", "/health", "/status"}:
            self._send_json({"status": "Ready", "health": research_bus_health_summary(db_path=self.server.db_path)})
            return
        self._send_json({"error": "Not found"}, status=404)

    def do_POST(self) -> None:  # noqa: N802 - stdlib handler API
        parsed = urlparse(self.path)
        if parsed.path not in {"/chat", "/request", "/webhook"}:
            self._send_json({"error": "Not found"}, status=404)
            return
        try:
            payload = self._read_payload()
            result = submit_webhook_payload(payload, source_system=self.server.source_system, db_path=self.server.db_path)
            if self.server.process_after_submit:
                result["process_result"] = process_pending_bus_requests(system_name="ResearchBus", db_path=self.server.db_path)
            self._send_json(result)
        except Exception as exc:
            self._send_json({"error": str(exc)}, status=400)

    def log_message(self, format: str, *args: Any) -> None:
        if self.server.quiet:
            return
        super().log_message(format, *args)

    def _read_payload(self) -> dict[str, Any] | str:
        length = int(self.headers.get("content-length") or 0)
        raw = self.rfile.read(length).decode("utf-8") if length > 0 else ""
        content_type = self.headers.get("content-type", "").lower()
        if "application/json" in content_type:
            payload = json.loads(raw or "{}")
            if not isinstance(payload, dict):
                raise ValueError("JSON webhook body must be an object.")
            return payload
        return raw

    def _send_json(self, payload: dict[str, Any], *, status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False, indent=2, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def run_server(
    *,
    host: str = "127.0.0.1",
    port: int = 8765,
    db_path: Path | str | None = None,
    source_system: str = "LocalWebhook",
    process_after_submit: bool = False,
    max_requests: int = 0,
    run_seconds: float = 0,
    quiet: bool = False,
) -> None:
    if host not in {"127.0.0.1", "localhost"}:
        raise ValueError("ResearchBus webhook only binds to 127.0.0.1/localhost.")
    server = ThreadingHTTPServer((host, int(port)), ResearchBusWebhookHandler)
    server.db_path = Path(db_path).expanduser() if db_path is not None else None
    server.source_system = source_system
    server.process_after_submit = bool(process_after_submit)
    server.quiet = quiet
    started = time.time()
    handled = 0
    try:
        if max_requests > 0 or run_seconds > 0:
            while True:
                if max_requests > 0 and handled >= max_requests:
                    break
                if run_seconds > 0 and time.time() - started >= run_seconds:
                    break
                server.handle_request()
                handled += 1
        else:
            server.serve_forever()
    finally:
        server.server_close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Local-only HTTP webhook for ResearchBus chat and API requests.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--db", default="")
    parser.add_argument("--source-system", default="LocalWebhook")
    parser.add_argument("--process-after-submit", action="store_true")
    parser.add_argument("--max-requests", type=int, default=0)
    parser.add_argument("--run-seconds", type=float, default=0)
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()
    run_server(
        host=args.host,
        port=args.port,
        db_path=Path(args.db).expanduser() if args.db else None,
        source_system=args.source_system,
        process_after_submit=args.process_after_submit,
        max_requests=args.max_requests,
        run_seconds=args.run_seconds,
        quiet=args.quiet,
    )


if __name__ == "__main__":
    main()
