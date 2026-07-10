#!/usr/bin/env python3
"""Loopback-only static and command server for the Memory Atlas local app."""

from __future__ import annotations

import argparse
import ipaddress
import json
import os
import sys
import threading
import time
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


COMMAND_API_VERSION = "memory_atlas_command_api.v1_2_r3"
PROPOSAL_API_VERSION = "memory_atlas_proposal_api.v1_2_r4"
MAX_COMMAND_BODY_BYTES = 1024
LOOPBACK_HOSTS = ("127.0.0.1", "localhost")


class RuntimeState:
    def __init__(self, runtime_dir: Path, ttl_seconds: int, idle_seconds: int) -> None:
        self.runtime_dir = runtime_dir
        self.ttl_seconds = ttl_seconds
        self.idle_seconds = idle_seconds
        self.started_at = time.time()
        self.last_seen_at = self.started_at
        self.had_client = False
        self.release_requested = False
        self.released_at: float | None = None
        self.shutdown_timer: threading.Timer | None = None
        self.lock = threading.Lock()

    def touch(self, client: bool = True) -> None:
        with self.lock:
            self.last_seen_at = time.time()
            if client:
                self.had_client = True

    def snapshot_mtime(self) -> int | None:
        snapshot = self.runtime_dir / "memory_atlas.json"
        if not snapshot.exists():
            return None
        return int(snapshot.stat().st_mtime)

    def request_shutdown(self, server: ThreadingHTTPServer, reason: str) -> None:
        start_timer = False
        with self.lock:
            self.had_client = True
            self.last_seen_at = time.time()
            self.release_requested = True
            self.released_at = self.last_seen_at
            if self.shutdown_timer is None:
                start_timer = True
        if not start_timer:
            return
        sys.stderr.write(f"Memory Atlas server release requested ({reason}); shutting down.\n")

        def shutdown_later() -> None:
            server.shutdown()

        timer = threading.Timer(0.2, shutdown_later)
        timer.daemon = True
        with self.lock:
            self.shutdown_timer = timer
        timer.start()

    def runtime_payload(self, command_ids: tuple[str, ...]) -> dict[str, Any]:
        with self.lock:
            last_seen = int(self.last_seen_at)
            active = self.had_client
            released = self.release_requested
            release_epoch = int(self.released_at) if self.released_at else None
        return {
            "status": "running",
            "pid": os.getpid(),
            "started_at_epoch": int(self.started_at),
            "last_seen_epoch": last_seen,
            "had_client": active,
            "release_requested": released,
            "released_at_epoch": release_epoch,
            "active_thread_count": threading.active_count(),
            "idle_seconds": self.idle_seconds,
            "ttl_seconds": self.ttl_seconds,
            "snapshot_mtime_epoch": self.snapshot_mtime(),
            "command_api_version": COMMAND_API_VERSION,
            "command_ids": list(command_ids),
            "command_execution_scope": "local_application_support_source_copy",
            "proposal_api_version": PROPOSAL_API_VERSION,
            "proposal_action_scope": "local_application_support_source_copy",
        }


class MemoryAtlasHTTPServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(
        self,
        server_address: tuple[str, int],
        request_handler_class: type[SimpleHTTPRequestHandler],
        *,
        state: RuntimeState,
        command_bridge: Any,
    ) -> None:
        self.state = state
        self.command_bridge = command_bridge
        super().__init__(server_address, request_handler_class)

    def handle_error(self, request: object, client_address: object) -> None:
        exc_type, exc, _traceback = sys.exc_info()
        if exc_type in {BrokenPipeError, ConnectionResetError} or isinstance(exc, (BrokenPipeError, ConnectionResetError)):
            return
        super().handle_error(request, client_address)


class Handler(SimpleHTTPRequestHandler):
    server: MemoryAtlasHTTPServer

    def end_headers(self) -> None:
        if self.path.startswith("/memory_atlas.json") or self.path.startswith("/__memory_atlas"):
            self.send_header("Cache-Control", "no-store")
        else:
            self.send_header("Cache-Control", "no-cache")
        super().end_headers()

    def log_message(self, fmt: str, *args: object) -> None:
        sys.stderr.write("%s - - [%s] %s\n" % (self.client_address[0], self.log_date_time_string(), fmt % args))

    def send_json(self, payload: dict[str, Any], status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_empty(self, status: int = 204) -> None:
        self.send_response(status)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def send_command_error(self, status: int, message_zh: str) -> None:
        self.send_json(
            {
                "schema_version": "memory_atlas_command_error.v1_2_r3",
                "status": "error",
                "message_zh": message_zh,
            },
            status=status,
        )

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/__memory_atlas_runtime_state":
            self.send_json(self.server.state.runtime_payload(tuple(self.server.command_bridge.command_ids)))
            return
        if path == "/memory_atlas.json":
            self.server.state.touch(True)
        super().do_GET()

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        if path == "/__memory_atlas_heartbeat":
            if not self.validate_local_origin():
                return
            self.server.state.touch(True)
            self.send_empty()
            return
        if path == "/__memory_atlas_release":
            if not self.validate_local_origin():
                return
            self.server.state.request_shutdown(self.server, "page_release")
            self.send_empty()
            return
        if path == "/__memory_atlas_command":
            self.handle_command()
            return
        if path == "/__memory_atlas_proposal_action":
            self.handle_proposal_action()
            return
        self.send_command_error(404, "未找到该本地 Memory Atlas 接口。")

    def do_OPTIONS(self) -> None:
        self.send_command_error(405, "Memory Atlas 本地命令接口不提供跨来源访问。")

    def validate_local_origin(self) -> bool:
        try:
            client_ip = ipaddress.ip_address(self.client_address[0])
        except ValueError:
            self.send_command_error(403, "请求不是来自本机 loopback，已拒绝执行。")
            return False
        if not client_ip.is_loopback:
            self.send_command_error(403, "请求不是来自本机 loopback，已拒绝执行。")
            return False

        active_port = int(self.server.server_address[1])
        allowed_hosts = {f"{host}:{active_port}" for host in LOOPBACK_HOSTS}
        host = (self.headers.get("Host") or "").strip().lower()
        if host not in allowed_hosts:
            self.send_command_error(403, "请求 Host 不是当前本地 Memory Atlas，已拒绝执行。")
            return False

        allowed_origins = {f"http://{host_value}:{active_port}" for host_value in LOOPBACK_HOSTS}
        origin = (self.headers.get("Origin") or "").strip().lower()
        if origin not in allowed_origins:
            self.send_command_error(403, "请求来源不是当前本地 Memory Atlas 页面，已拒绝执行。")
            return False
        fetch_site = (self.headers.get("Sec-Fetch-Site") or "").strip().lower()
        if fetch_site and fetch_site not in {"same-origin", "none"}:
            self.send_command_error(403, "跨站请求不能调用 Memory Atlas 本地命令。")
            return False
        return True

    def handle_command(self) -> None:
        if not self.validate_local_origin():
            return
        payload = self.read_json_payload()
        if payload is None:
            return
        if set(payload) != {"command_id"}:
            self.send_command_error(400, "本地命令请求只能包含 command_id。")
            return
        command_id = payload.get("command_id")
        if not isinstance(command_id, str) or command_id not in self.server.command_bridge.command_ids:
            self.send_command_error(400, "命令不在 Memory Atlas 固定允许列表中。")
            return
        try:
            result = self.server.command_bridge.execute(command_id)
        except Exception as exc:
            if exc.__class__.__name__ == "CommandBusyError":
                self.send_command_error(409, "另一个 Memory Atlas 本地操作正在运行，请完成后重试。")
                return
            if exc.__class__.__name__ == "CommandRequestError":
                self.send_command_error(400, "命令不在 Memory Atlas 固定允许列表中。")
                return
            self.send_command_error(500, "本地命令服务出现未预期错误；请查看 Memory Atlas 本机日志。")
            return
        self.server.state.touch(True)
        self.send_json(result)

    def read_json_payload(self) -> dict[str, Any] | None:
        content_type = (self.headers.get("Content-Type") or "").split(";", 1)[0].strip().lower()
        if content_type != "application/json":
            self.send_command_error(415, "本地命令请求必须使用 JSON。")
            return None
        length_text = self.headers.get("Content-Length")
        if length_text is None:
            self.send_command_error(411, "本地命令请求缺少 Content-Length。")
            return None
        try:
            length = int(length_text)
        except ValueError:
            self.send_command_error(400, "本地命令请求长度无效。")
            return None
        if length < 2 or length > MAX_COMMAND_BODY_BYTES:
            self.send_command_error(413, "本地命令请求体过大或为空，已拒绝执行。")
            return None

        try:
            body = self.rfile.read(length)
            payload = json.loads(body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            self.send_command_error(400, "本地命令请求不是有效 JSON。")
            return None
        if not isinstance(payload, dict):
            self.send_command_error(400, "本地命令请求必须是 JSON object。")
            return None
        return payload

    def handle_proposal_action(self) -> None:
        if not self.validate_local_origin():
            return
        payload = self.read_json_payload()
        if payload is None:
            return
        action = payload.get("action")
        if action == "approve_apply":
            expected = {"action", "proposal_id", "review_token", "confirmation"}
        elif action == "rollback":
            expected = {"action", "transaction_id", "rollback_token", "confirmation"}
        else:
            self.send_command_error(400, "proposal action 不在固定允许列表中。")
            return
        if set(payload) != expected or any(not isinstance(payload.get(key), str) or not payload.get(key) for key in expected):
            self.send_command_error(400, "proposal action 字段不符合固定合同。")
            return
        try:
            result = self.server.command_bridge.execute_proposal_action(payload)
        except Exception as exc:
            if exc.__class__.__name__ == "CommandBusyError":
                self.send_command_error(409, "另一个 Memory Atlas 本地操作正在运行，请完成后重试。")
                return
            if exc.__class__.__name__ in {
                "CommandRequestError",
                "ProposalAuthorizationError",
                "ProposalBundleError",
                "ProposalRollbackError",
                "ProposalValidationError",
                "ProposalWorkflowError",
            }:
                self.send_command_error(400, str(exc))
                return
            self.send_command_error(500, "本地 proposal 服务出现未预期错误；请查看 Memory Atlas 本机日志。")
            return
        self.server.state.touch(True)
        self.send_json(result)


def load_default_bridge(source_root: Path, runtime_dir: Path) -> Any:
    scripts_dir = source_root / "scripts"
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    from memory_atlas_command_bridge import CommandBridge, CommandContext

    codex_home_value = os.environ.get("MEMORY_ATLAS_CODEX_HOME", "").strip()
    timeout_value = os.environ.get("MEMORY_ATLAS_COMMAND_TIMEOUT_SECONDS", "").strip()
    timeout_seconds = int(timeout_value) if timeout_value else 180
    return CommandBridge(
        CommandContext(
            source_root=source_root,
            runtime_dir=runtime_dir,
            app_support=runtime_dir.parent,
            codex_home=Path(codex_home_value) if codex_home_value else None,
            timeout_seconds=timeout_seconds,
        )
    )


def create_server(
    *,
    runtime_dir: Path,
    source_root: Path,
    port: int,
    ttl_seconds: int,
    idle_seconds: int,
    command_bridge: Any | None = None,
) -> MemoryAtlasHTTPServer:
    resolved_runtime = runtime_dir.expanduser().resolve()
    resolved_source = source_root.expanduser().resolve()
    if not resolved_runtime.is_dir():
        raise FileNotFoundError(f"runtime directory missing: {resolved_runtime}")
    bridge = command_bridge or load_default_bridge(resolved_source, resolved_runtime)
    state = RuntimeState(resolved_runtime, max(0, ttl_seconds), max(0, idle_seconds))
    handler = partial(Handler, directory=str(resolved_runtime))
    return MemoryAtlasHTTPServer(("127.0.0.1", port), handler, state=state, command_bridge=bridge)


def monitor_idle(server: MemoryAtlasHTTPServer) -> None:
    state = server.state
    while True:
        time.sleep(2)
        now = time.time()
        with state.lock:
            idle_for = now - state.last_seen_at
            client_seen = state.had_client
            release_seen = state.release_requested
        if release_seen:
            sys.stderr.write("Memory Atlas server release flag observed; shutting down.\n")
            server.shutdown()
            return
        if state.ttl_seconds > 0 and now - state.started_at >= state.ttl_seconds:
            sys.stderr.write("Memory Atlas server reached TTL; shutting down.\n")
            server.shutdown()
            return
        if client_seen and state.idle_seconds > 0 and idle_for >= state.idle_seconds:
            sys.stderr.write("Memory Atlas server idle after page close; shutting down.\n")
            server.shutdown()
            return


def remove_owned_pid_file(pid_file: str) -> None:
    if not pid_file:
        return
    try:
        path = Path(pid_file)
        if path.exists() and path.read_text(encoding="utf-8").strip() == str(os.getpid()):
            path.unlink()
    except OSError:
        pass


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Serve the Memory Atlas local runtime on loopback.")
    parser.add_argument("runtime_dir", type=Path)
    parser.add_argument("port", type=int)
    parser.add_argument("ttl_seconds", type=int)
    parser.add_argument("idle_seconds", type=int)
    parser.add_argument("source_root", type=Path)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        server = create_server(
            runtime_dir=args.runtime_dir,
            source_root=args.source_root,
            port=args.port,
            ttl_seconds=args.ttl_seconds,
            idle_seconds=args.idle_seconds,
        )
    except Exception as exc:
        sys.stderr.write(f"Memory Atlas runtime server failed to initialize: {exc}\n")
        return 1
    threading.Thread(target=monitor_idle, args=(server,), daemon=True).start()
    try:
        server.serve_forever()
    finally:
        server.server_close()
        remove_owned_pid_file(os.environ.get("MEMORY_ATLAS_PID_FILE", ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
