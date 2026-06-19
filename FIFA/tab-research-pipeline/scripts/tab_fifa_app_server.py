#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import io
import json
import mimetypes
import os
import re
import secrets
import shutil
import shlex
import subprocess
import sys
import threading
import time
from html import escape as html_escape
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse
from datetime import datetime
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tab_research.my_bets_bootstrap import build_private_position_bootstrap_status, private_dir_for_output
from tab_research.paths import resolve_output_dir, resolve_private_dir, resolve_workspace_root
from tab_research.partial_daily_research import (
    partial_daily_research_status,
    partial_daily_research_status_from_payload,
    write_partial_daily_research_bundle,
)
from tab_research.provider_fallback_verification import TEAM_TOTAL_LABEL
from tab_research.provider_manual_verification import (
    CSV_FIELDS,
    DEFAULT_IMPORT_RELATIVE_PATH,
    PROVIDER_MANUAL_NEXT_BATCH_PAIR_TEMPLATE_CSV_LATEST,
    write_provider_manual_verification_bundle,
)
from tab_research.raw_refresh import normalize_partial_research_refresh


PIPELINE_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = resolve_workspace_root(Path(__file__))
OUTPUT_DIR = resolve_output_dir(Path(__file__))
REPORT_DIR = Path.home() / "Downloads" / "FIFA Report"
ENTRY_HTML = REPORT_DIR / "TAB FIFA盘口研究系统.html"
ASSETS_DIR = REPORT_DIR / "app_assets"
ENTRY_FALLBACK_HTML = OUTPUT_DIR / "tab_fifa_app_entry_runtime.html"
PRIVATE_LOG_DIR = resolve_private_dir(Path(__file__), "app_server_logs")
BACKFILL_PID_PATH = PRIVATE_LOG_DIR / "active_backfill_worker.pid"
PRIVATE_BOOTSTRAP_PID_PATH = PRIVATE_LOG_DIR / "private_position_bootstrap_runner.pid"
DAILY_RERUN_PID_PATH = PRIVATE_LOG_DIR / "daily_report_runner.pid"
PUBLIC_RAW_REFRESH_PID_PATH = PRIVATE_LOG_DIR / "public_raw_refresh_runner.pid"
LIVE_DISCOVERY_PID_PATH = PRIVATE_LOG_DIR / "live_board_discovery_runner.pid"
SOURCE_METADATA_PID_PATH = PRIVATE_LOG_DIR / "source_model_metadata_runner.pid"
ACTIVE_BACKFILL_LATEST_JSON = OUTPUT_DIR / "active_backfill_latest.json"
ACTIVE_TIMELINE_LATEST_JSON = OUTPUT_DIR / "active_timeline_latest.json"
REPORT_TZ = ZoneInfo("Australia/Sydney")
LOCAL_WEB_APP_URL = f"http://127.0.0.1:{os.getenv('TAB_FIFA_APP_PORT', '8767')}/"
PROVIDER_CREDIT_RESERVE_FLOOR = 200
MAX_MANUAL_TEAM_TOTAL_EVENTS = 80
MAX_MANUAL_TEAM_TOTAL_BODY_BYTES = 128_000
DEFAULT_NODE_BIN = Path.home() / ".cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node"
NODE_BIN = Path(os.getenv("TAB_FIFA_NODE_BIN") or str(DEFAULT_NODE_BIN if DEFAULT_NODE_BIN.exists() else (shutil.which("node") or DEFAULT_NODE_BIN))).expanduser()
LIVE_BOARD_DISCOVERY_SCRIPT = PIPELINE_ROOT / "scripts" / "discover_tab_live_boards.mjs"
ACTION_TOKEN = os.getenv("TAB_FIFA_ACTION_TOKEN") or secrets.token_urlsafe(32)
LOCAL_HOSTS = {"127.0.0.1", "localhost", "::1"}
RUNNER_START_LOCK = threading.Lock()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Local-only TAB FIFA app entry server.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8767)
    return parser.parse_args()


def json_response(handler: BaseHTTPRequestHandler, status: int, payload: dict) -> None:
    body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Cache-Control", "no-store")
    handler.end_headers()
    handler.wfile.write(body)


def text_response(handler: BaseHTTPRequestHandler, status: int, text: str) -> None:
    body = text.encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "text/plain; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def serve_file(handler: BaseHTTPRequestHandler, path: Path, *, inject_action_token: bool = False) -> bool:
    if not path.exists() or not path.is_file():
        return False
    mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    try:
        if inject_action_token and mime == "text/html":
            body = html_with_action_token(path.read_text(encoding="utf-8")).encode("utf-8")
        else:
            body = path.read_bytes()
    except PermissionError:
        return False
    handler.send_response(HTTPStatus.OK)
    handler.send_header("Content-Type", mime)
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Cache-Control", "no-store")
    handler.end_headers()
    handler.wfile.write(body)
    return True


def html_with_action_token(text: str) -> str:
    meta = f'<meta name="tab-fifa-action-token" content="{html_escape(ACTION_TOKEN, quote=True)}">'
    if re.search(r"<meta\\s+[^>]*name=[\"']tab-fifa-action-token[\"']", text, flags=re.IGNORECASE):
        return text
    if "<head>" in text:
        return text.replace("<head>", f"<head>\n    {meta}", 1)
    return meta + "\n" + text


def serve_first_readable(handler: BaseHTTPRequestHandler, paths: list[Path], *, inject_action_token: bool = False) -> None:
    for path in paths:
        if serve_file(handler, path, inject_action_token=inject_action_token):
            return
    text_response(handler, HTTPStatus.NOT_FOUND, "not found")


def safe_asset_paths(raw_path: str) -> list[Path] | None:
    name = unquote(raw_path.removeprefix("/app_assets/"))
    download_candidate = (ASSETS_DIR / name).resolve()
    output_candidate = (OUTPUT_DIR / name).resolve()
    try:
        download_candidate.relative_to(ASSETS_DIR.resolve())
        output_candidate.relative_to(OUTPUT_DIR.resolve())
    except ValueError:
        return None
    return [download_candidate, output_candidate]


class Handler(BaseHTTPRequestHandler):
    server_version = "TABFIFAApp/1.0"

    def log_message(self, fmt: str, *args) -> None:  # noqa: N802 - stdlib signature
        PRIVATE_LOG_DIR.mkdir(parents=True, exist_ok=True)
        with (PRIVATE_LOG_DIR / "access.log").open("a", encoding="utf-8") as handle:
            handle.write("%s - %s\n" % (self.log_date_time_string(), fmt % args))

    def do_GET(self) -> None:  # noqa: N802 - stdlib signature
        if self.path in {"/", "/index.html"}:
            serve_first_readable(self, [ENTRY_HTML, ENTRY_FALLBACK_HTML], inject_action_token=True)
            return
        if self.path.startswith("/app_assets/"):
            assets = safe_asset_paths(self.path)
            if assets is None:
                text_response(self, HTTPStatus.FORBIDDEN, "forbidden")
                return
            serve_first_readable(self, assets)
            return
        if self.path == "/api/health":
            json_response(self, HTTPStatus.OK, {"ok": True, "entry": ENTRY_HTML.exists()})
            return
        if self.path == "/api/status":
            json_response(self, HTTPStatus.OK, app_status())
            return
        if self.path == "/api/manual-team-total-entry":
            json_response(self, HTTPStatus.OK, manual_team_total_entry_payload())
            return
        if self.path.startswith("/api/status."):
            payload, status_code = app_status_section_payload(self.path)
            json_response(self, status_code, payload)
            return
        text_response(self, HTTPStatus.NOT_FOUND, "not found")

    def do_POST(self) -> None:  # noqa: N802 - stdlib signature
        allowed, reason = validate_post_request(self)
        if not allowed:
            json_response(self, HTTPStatus.FORBIDDEN, {"ok": False, "error": "forbidden", "reason": reason})
            return
        if self.path == "/api/active-test":
            json_response(self, HTTPStatus.OK, run_active_test())
            return
        if self.path == "/api/backfill-missing":
            json_response(self, HTTPStatus.ACCEPTED, start_backfill())
            return
        if self.path == "/api/private-bootstrap":
            json_response(self, HTTPStatus.ACCEPTED, start_private_position_bootstrap())
            return
        if self.path == "/api/rerun-daily-report":
            json_response(self, HTTPStatus.ACCEPTED, start_daily_report_rerun())
            return
        if self.path == "/api/public-raw-refresh":
            json_response(self, HTTPStatus.ACCEPTED, start_public_raw_refresh())
            return
        if self.path == "/api/live-board-discovery":
            json_response(self, HTTPStatus.ACCEPTED, start_live_board_discovery())
            return
        if self.path == "/api/source-model-metadata-refresh":
            json_response(self, HTTPStatus.ACCEPTED, start_source_model_metadata_refresh())
            return
        if self.path == "/api/manual-team-total-entry":
            body, body_error = read_json_request(self, max_bytes=MAX_MANUAL_TEAM_TOTAL_BODY_BYTES)
            if body_error:
                json_response(self, body_error["status"], body_error["payload"])
                return
            payload, status_code = save_manual_team_total_entry(body)
            json_response(self, status_code, payload)
            return
        text_response(self, HTTPStatus.NOT_FOUND, "not found")


def validate_post_request(handler: BaseHTTPRequestHandler) -> tuple[bool, str]:
    host = normalize_host_header(handler.headers.get("Host", ""))
    if host not in LOCAL_HOSTS:
        return False, "invalid_host"
    token = handler.headers.get("X-TAB-FIFA-Action-Token", "")
    if not secrets.compare_digest(token, ACTION_TOKEN):
        return False, "invalid_action_token"
    for header_name in ("Origin", "Referer"):
        header_value = handler.headers.get(header_name, "")
        if header_value and not is_allowed_local_url(header_value, handler):
            if header_name == "Origin":
                return False, "invalid_origin"
            return False, "invalid_referer"
    return True, ""


def normalize_host_header(value: str) -> str:
    value = (value or "").strip()
    if not value:
        return ""
    if value.startswith("[") and "]" in value:
        return value[1 : value.index("]")].lower()
    if ":" in value and value.count(":") == 1:
        return value.split(":", 1)[0].lower()
    return value.lower()


def is_allowed_local_url(value: str, handler: BaseHTTPRequestHandler) -> bool:
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"}:
        return False
    host = (parsed.hostname or "").lower()
    if host not in LOCAL_HOSTS:
        return False
    expected_port = int(getattr(handler.server, "server_port", 8767))
    actual_port = parsed.port or (443 if parsed.scheme == "https" else 80)
    return actual_port == expected_port


def app_status_section_payload(path: str) -> tuple[dict, int]:
    key = unquote(path.removeprefix("/api/status.")).strip()
    if not re.fullmatch(r"[A-Za-z0-9_]+", key or ""):
        return {"ok": False, "error": "invalid_status_key", "key": key}, HTTPStatus.BAD_REQUEST
    status = app_status()
    section = status.get(key)
    if not isinstance(section, dict):
        return {"ok": False, "error": "unknown_status_key", "key": key}, HTTPStatus.NOT_FOUND
    return {"ok": True, "key": key, **section}, HTTPStatus.OK


def run_active_test() -> dict:
    started = time.perf_counter()
    cached = fresh_active_timeline_cache(max_age_seconds=90)
    if cached:
        cached["ok"] = True
        cached["fallback_used"] = False
        cached["active_test_runtime"] = {
            "elapsed_ms": int((time.perf_counter() - started) * 1000),
            "mode": "fresh_cached_timeline_fast_path",
            "cache_age_seconds": int(cached.get("cache_age_seconds") or 0),
            "downloads_rebuild": "skipped_for_fast_result",
        }
        return attach_active_backfill_decision(cached)
    try:
        proc = subprocess.run(
            [sys.executable, "scripts/active_timeline_check.py", "--json", "--write-latest"],
            cwd=PIPELINE_ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=45,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        return active_test_fallback_payload(
            started=started,
            error=f"active test timed out after {exc.timeout}s",
            exit_code=None,
        )
    if proc.returncode != 0:
        return active_test_fallback_payload(
            started=started,
            error=proc.stderr[-1200:] or proc.stdout[-1200:] or "active test failed",
            exit_code=proc.returncode,
        )
    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return active_test_fallback_payload(
            started=started,
            error="active test returned invalid JSON",
            exit_code=proc.returncode,
        )
    payload["ok"] = True
    payload["fallback_used"] = False
    payload["active_test_runtime"] = {
        "elapsed_ms": int((time.perf_counter() - started) * 1000),
        "mode": "fresh_timeline_direct_api",
        "downloads_rebuild": "skipped_for_fast_result",
    }
    return attach_active_backfill_decision(payload)


def attach_active_backfill_decision(payload: dict) -> dict:
    summary = payload.get("summary") or {}
    if int(summary.get("backfill_queue_count") or 0) > 0:
        payload["auto_backfill"] = start_backfill(refresh_assets=False)
    else:
        payload["auto_backfill"] = {
            "ok": True,
            "started": False,
            "message": "主动测试完成，未发现需要补跑的缺口。",
        }
    return payload


def fresh_active_timeline_cache(max_age_seconds: int) -> dict:
    payload = load_json(ACTIVE_TIMELINE_LATEST_JSON)
    if not payload:
        return {}
    generated_at = str(payload.get("generated_at") or "")
    try:
        parsed = datetime.fromisoformat(generated_at.replace("Z", "+00:00"))
    except ValueError:
        return {}
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=REPORT_TZ)
    age_seconds = (datetime.now(REPORT_TZ) - parsed.astimezone(REPORT_TZ)).total_seconds()
    if age_seconds < 0 or age_seconds > max_age_seconds:
        return {}
    cached = dict(payload)
    cached["cache_age_seconds"] = int(age_seconds)
    return cached


def active_test_fallback_payload(*, started: float, error: str, exit_code: int | None) -> dict:
    payload = load_json(ACTIVE_TIMELINE_LATEST_JSON)
    if not payload:
        return {
            "ok": False,
            "exit_code": exit_code,
            "error": error,
            "active_test_runtime": {
                "elapsed_ms": int((time.perf_counter() - started) * 1000),
                "mode": "failed_no_cached_timeline",
            },
        }
    payload["ok"] = True
    payload["fallback_used"] = True
    payload["exit_code"] = exit_code
    payload["warning"] = str(error).splitlines()[0][:220]
    payload["active_test_runtime"] = {
        "elapsed_ms": int((time.perf_counter() - started) * 1000),
        "mode": "cached_timeline_after_failure",
        "downloads_rebuild": "skipped_for_fast_result",
    }
    payload["auto_backfill"] = {
        "ok": True,
        "started": False,
        "fallback_guard": True,
        "message": "实时主动测试失败，已展示最近一次时间线快照；为避免误补跑，本次不启动自动补缺。",
    }
    return payload


def start_backfill(refresh_assets: bool = False) -> dict:
    PRIVATE_LOG_DIR.mkdir(parents=True, exist_ok=True)
    raw_blocker = raw_refresh_backfill_blocker()
    if raw_blocker:
        blocked_payload = write_blocked_backfill_latest(raw_blocker)
        partial_status = blocked_payload.get("partial_daily_research") or {}
        if refresh_assets:
            refresh_download_assets()
        return {
            "ok": True,
            "started": False,
            "blocked": True,
            "mode": "safe_no_latest_publish",
            "blocker": raw_blocker,
            "blocked_queue_count": blocked_payload.get("blocked_queue_count", 0),
            "latest_status": blocked_payload.get("status", ""),
            "partial_daily_research": partial_status,
            "message": (
                "公开盘口 raw 未就绪，已停止正式补跑；"
                f"{partial_daily_research_backfill_message(partial_status)}"
                "TAB 拒绝 AI controlled access 时需接入授权数据源或导入用户导出快照，才能恢复正式日报门禁。"
            ),
        }
    with RUNNER_START_LOCK:
        if process_running(BACKFILL_PID_PATH):
            return {
                "ok": True,
                "started": False,
                "already_running": True,
                "mode": "safe_no_latest_publish",
                "message": "缺口补跑已在运行，完成后会自动刷新入口。",
            }
        log_path = PRIVATE_LOG_DIR / "active_backfill_command.log"
        process = start_background_shell(
            command=f"{shlex.quote(sys.executable)} scripts/app_backfill_worker.py --max-backfill-runs 3",
            pid_path=BACKFILL_PID_PATH,
            log_path=log_path,
        )
    return {
        "ok": True,
        "started": True,
        "pid": process.pid,
        "mode": "safe_no_latest_publish",
        "message": "已启动缺口补跑。补跑不会发布 latest_commit；完成后会自动刷新入口和研究智能层。",
        "log": log_path.name,
    }


def start_private_position_bootstrap() -> dict:
    PRIVATE_LOG_DIR.mkdir(parents=True, exist_ok=True)
    with RUNNER_START_LOCK:
        if process_running(PRIVATE_BOOTSTRAP_PID_PATH):
            return {
                "ok": True,
                "started": False,
                "already_running": True,
                "mode": "read_only_private_position_bootstrap",
                "message": "只读持仓读取已在运行；请在打开的 TAB 窗口完成授权后等待日报刷新。",
            }
        if process_running(DAILY_RERUN_PID_PATH):
            return {
                "ok": True,
                "started": False,
                "already_running": True,
                "mode": "daily_report_rerun",
                "message": "日报重跑已在运行；当前不重复启动持仓读取。",
            }
        report_date = current_report_date()
        log_path = PRIVATE_LOG_DIR / "private_position_bootstrap_command.log"
        command = (
            "TAB_FIFA_HEADLESS=0 TAB_FIFA_REFRESH_RAW=reuse_fresh "
            f"scripts/run_tab_fifa_daily_automation.sh --capture-my-bets --report-date {shlex.quote(report_date)} "
            "--wait-for-login-ms 600000; "
            "cmd_rc=$?; "
            f"TAB_FIFA_FAST_ENTRY_REBUILD=1 {shlex.quote(sys.executable)} scripts/build_downloads_app_entry.py; "
            "exit $cmd_rc"
        )
        process = start_background_shell(command=command, pid_path=PRIVATE_BOOTSTRAP_PID_PATH, log_path=log_path)
    return {
        "ok": True,
        "started": True,
        "pid": process.pid,
        "mode": "read_only_private_position_bootstrap",
        "report_date": report_date,
        "message": "已启动只读持仓读取。若出现 TAB 窗口，请完成授权；系统随后会导入私有快照并重跑日报门禁。",
        "log": log_path.name,
    }


def start_daily_report_rerun() -> dict:
    PRIVATE_LOG_DIR.mkdir(parents=True, exist_ok=True)
    with RUNNER_START_LOCK:
        if process_running(DAILY_RERUN_PID_PATH):
            return {
                "ok": True,
                "started": False,
                "already_running": True,
                "mode": "daily_report_rerun",
                "message": "日报重跑已在运行；完成后会刷新入口。",
            }
        if process_running(PRIVATE_BOOTSTRAP_PID_PATH):
            return {
                "ok": True,
                "started": False,
                "already_running": True,
                "mode": "read_only_private_position_bootstrap",
                "message": "只读持仓读取仍在运行；完成后会自动进入日报门禁。",
            }
        log_path = PRIVATE_LOG_DIR / "daily_report_rerun_command.log"
        command = (
            "TAB_FIFA_REFRESH_RAW=reuse_fresh scripts/run_tab_fifa_daily_automation.sh; "
            "cmd_rc=$?; "
            f"TAB_FIFA_FAST_ENTRY_REBUILD=1 {shlex.quote(sys.executable)} scripts/build_downloads_app_entry.py; "
            "exit $cmd_rc"
        )
        process = start_background_shell(command=command, pid_path=DAILY_RERUN_PID_PATH, log_path=log_path)
    return {
        "ok": True,
        "started": True,
        "pid": process.pid,
        "mode": "daily_report_rerun",
        "message": "已启动日报门禁重跑。若私有持仓仍缺失，报告会继续 fail-closed。",
        "log": log_path.name,
    }


def start_public_raw_refresh() -> dict:
    raw_health = load_json(OUTPUT_DIR / "raw_refresh_health_latest.json")
    return {
        "ok": True,
        "started": False,
        "blocked": True,
        "mode": "public_raw_access_policy_blocked",
        "message": (
            "TAB 会拒绝 AI controlled access；系统已停止自动公开 raw 刷新。"
            "请接入官方/授权数据源，或使用用户导出导入快照；当前只保留 research-only 诊断，不解锁新增下注金额。"
        ),
        "blocker_code": "ai_controlled_access_rejected",
        "forbidden_recovery": ["headed_fallback", "captcha_bypass", "fingerprint_spoofing", "stealth_browser"],
        "allowed_recovery": ["official_data_feed", "user_authorized_manual_export_import", "research_only_from_existing_fresh_partial_raw"],
        "raw_status": raw_health.get("status", "missing"),
        "partial_research_refresh": raw_health.get("partial_research_refresh") or {},
    }


def start_live_board_discovery() -> dict:
    return {
        "ok": True,
        "started": False,
        "blocked": True,
        "mode": "live_board_discovery_access_policy_blocked",
        "message": (
            "TAB 会拒绝 AI controlled access；系统已停止自动 Live 板块发现。"
            "请等待授权数据源/用户导出导入，或只使用已有 fresh partial raw 做 research-only 诊断。"
        ),
        "blocker_code": "ai_controlled_access_rejected",
        "forbidden_recovery": ["headed_fallback", "captcha_bypass", "fingerprint_spoofing", "stealth_browser"],
    }


def start_source_model_metadata_refresh() -> dict:
    PRIVATE_LOG_DIR.mkdir(parents=True, exist_ok=True)
    with RUNNER_START_LOCK:
        if process_running(SOURCE_METADATA_PID_PATH):
            return {
                "ok": True,
                "started": False,
                "already_running": True,
                "mode": "source_model_metadata_refresh",
                "message": "开源模型证据刷新已在运行；完成后会自动刷新入口。",
            }
        if process_running(DAILY_RERUN_PID_PATH) or process_running(PRIVATE_BOOTSTRAP_PID_PATH):
            return {
                "ok": True,
                "started": False,
                "already_running": True,
                "mode": "daily_gate_active",
                "message": "日报门禁或持仓读取仍在运行；当前不重复启动开源模型证据刷新。",
            }
        log_path = PRIVATE_LOG_DIR / "source_model_metadata_command.log"
        command = (
            f"{shlex.quote(sys.executable)} scripts/refresh_source_model_metadata.py --output-dir {shlex.quote(str(OUTPUT_DIR))}; "
            "cmd_rc=$?; "
            f"TAB_FIFA_FAST_ENTRY_REBUILD=1 {shlex.quote(sys.executable)} scripts/build_downloads_app_entry.py; "
            "exit $cmd_rc"
        )
        process = start_background_shell(command=command, pid_path=SOURCE_METADATA_PID_PATH, log_path=log_path)
    return {
        "ok": True,
        "started": True,
        "pid": process.pid,
        "mode": "source_model_metadata_refresh",
        "message": "已启动开源模型证据刷新。系统只访问 GitHub 公共 API，不触发 TAB 或下注操作。",
        "log": log_path.name,
    }


def start_background_shell(command: str, pid_path: Path, log_path: Path) -> subprocess.Popen:
    shell_command = (
        f"{command}; "
        "rc=$?; "
        f"rm -f {shlex.quote(str(pid_path))}; "
        "exit $rc"
    )
    with log_path.open("a", encoding="utf-8") as log:
        process = subprocess.Popen(
            ["/bin/zsh", "-lc", shell_command],
            cwd=PIPELINE_ROOT,
            stdout=log,
            stderr=log,
            start_new_session=True,
        )
    write_pid_file(pid_path, process.pid)
    return process


def write_pid_file(pid_path: Path, pid: int) -> None:
    pid_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = pid_path.with_name(f".{pid_path.name}.{os.getpid()}.tmp")
    tmp.write_text(str(pid), encoding="utf-8")
    os.replace(tmp, pid_path)


def process_running(pid_path: Path) -> bool:
    if not pid_path.exists():
        return False
    try:
        pid = int(pid_path.read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        pid_path.unlink(missing_ok=True)
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        pid_path.unlink(missing_ok=True)
        return False
    except PermissionError:
        return True
    if process_is_zombie(pid):
        pid_path.unlink(missing_ok=True)
        return False
    return True


def process_is_zombie(pid: int) -> bool:
    try:
        result = subprocess.run(
            ["ps", "-p", str(pid), "-o", "stat="],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            timeout=2,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return result.returncode == 0 and result.stdout.strip().startswith("Z")


def current_report_date() -> str:
    return datetime.now(REPORT_TZ).strftime("%d%m%Y")


def load_json(path: Path) -> dict:
    try:
        if not path.exists():
            return {}
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def read_json_request(handler: BaseHTTPRequestHandler, *, max_bytes: int) -> tuple[dict, dict | None]:
    raw_length = handler.headers.get("Content-Length", "0")
    try:
        length = int(raw_length)
    except ValueError:
        return {}, {
            "status": HTTPStatus.BAD_REQUEST,
            "payload": {"ok": False, "error": "invalid_content_length", "current_executable_new_stake_aud": 0},
        }
    if length < 0 or length > max_bytes:
        return {}, {
            "status": HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
            "payload": {"ok": False, "error": "request_body_too_large", "max_bytes": max_bytes, "current_executable_new_stake_aud": 0},
        }
    try:
        body = handler.rfile.read(length).decode("utf-8")
        payload = json.loads(body or "{}")
    except (UnicodeDecodeError, json.JSONDecodeError):
        return {}, {
            "status": HTTPStatus.BAD_REQUEST,
            "payload": {"ok": False, "error": "invalid_json_body", "current_executable_new_stake_aud": 0},
        }
    if not isinstance(payload, dict):
        return {}, {
            "status": HTTPStatus.BAD_REQUEST,
            "payload": {"ok": False, "error": "json_body_must_be_object", "current_executable_new_stake_aud": 0},
        }
    return payload, None


def read_csv_dict_rows(path: Path, *, max_rows: int = 500) -> tuple[list[dict[str, str]], list[dict]]:
    if not path.exists():
        return [], []
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            rows = []
            for index, row in enumerate(reader):
                if index >= max_rows:
                    break
                rows.append({str(key or ""): str(value or "").strip() for key, value in (row or {}).items()})
    except Exception as exc:
        return [], [{"issue": f"cannot_read_csv: {str(exc).splitlines()[0][:160]}", "path": str(path)}]
    return rows, []


def clean_manual_value(value: object, *, max_len: int = 220) -> str:
    text = " ".join(str(value or "").replace("\x00", " ").split())
    return text[:max_len]


def manual_direction(row: dict[str, str]) -> str:
    text = " ".join(
        [
            str(row.get("direction_hint") or ""),
            str(row.get("entry_slot") or ""),
            str(row.get("selection_name") or ""),
        ]
    ).lower()
    if "over" in text:
        return "Over"
    if "under" in text:
        return "Under"
    return ""


def first_nonblank(*values: object) -> str:
    for value in values:
        text = clean_manual_value(value)
        if text:
            return text
    return ""


def manual_entry_status_for_fields(entry: dict[str, str]) -> str:
    status = clean_manual_value(entry.get("verification_status")).lower()
    complete_values = [
        entry.get("team_scope"),
        entry.get("line"),
        entry.get("over_decimal_odds"),
        entry.get("under_decimal_odds"),
        entry.get("observed_at_aest"),
        entry.get("operator_initials"),
        entry.get("evidence_note_or_screenshot_ref"),
    ]
    if not any(clean_manual_value(value) for value in complete_values):
        return "pending"
    if status in {"verified", "manual_verified", "pending_review"}:
        return status
    return "pending_review"


def manual_entry_is_complete(entry: dict[str, str]) -> bool:
    required = [
        "tab_match_name",
        "team_scope",
        "tab_market_name",
        "line",
        "over_decimal_odds",
        "under_decimal_odds",
        "observed_at_aest",
        "operator_initials",
        "evidence_note_or_screenshot_ref",
    ]
    return all(clean_manual_value(entry.get(field)) for field in required)


def blank_manual_csv_row(template_row: dict[str, str]) -> dict[str, str]:
    return {
        "event_id": clean_manual_value(template_row.get("event_id")),
        "rank": clean_manual_value(template_row.get("rank")),
        "match": clean_manual_value(template_row.get("match")),
        "commence_time": clean_manual_value(template_row.get("commence_time")),
        "priority_tier": clean_manual_value(template_row.get("priority_tier")),
        "missing_market": clean_manual_value(template_row.get("missing_market")) or TEAM_TOTAL_LABEL,
        "tab_match_name": "",
        "team_scope": "",
        "tab_market_name": "",
        "selection_name": "",
        "line": "",
        "decimal_odds": "",
        "observed_at_aest": "",
        "operator_initials": "",
        "evidence_note_or_screenshot_ref": "",
        "verification_status": "pending",
    }


def manual_team_total_entry_payload() -> dict:
    template_path = OUTPUT_DIR / PROVIDER_MANUAL_NEXT_BATCH_PAIR_TEMPLATE_CSV_LATEST
    import_path = OUTPUT_DIR / DEFAULT_IMPORT_RELATIVE_PATH
    template_rows, template_errors = read_csv_dict_rows(template_path, max_rows=MAX_MANUAL_TEAM_TOTAL_EVENTS * 2)
    import_rows, import_errors = read_csv_dict_rows(import_path, max_rows=MAX_MANUAL_TEAM_TOTAL_EVENTS * 2)
    existing_by_event: dict[str, dict[str, dict[str, str]]] = {}
    for row in import_rows:
        event_id = clean_manual_value(row.get("event_id"))
        direction = manual_direction(row)
        if event_id and direction:
            existing_by_event.setdefault(event_id, {})[direction] = row

    grouped: dict[str, dict] = {}
    for row in template_rows:
        event_id = clean_manual_value(row.get("event_id"))
        if not event_id:
            continue
        direction = manual_direction(row)
        group = grouped.setdefault(
            event_id,
            {
                "event_id": event_id,
                "rank": clean_manual_value(row.get("rank")),
                "match": clean_manual_value(row.get("match")),
                "commence_time": clean_manual_value(row.get("commence_time")),
                "priority_tier": clean_manual_value(row.get("priority_tier")),
                "missing_market": clean_manual_value(row.get("missing_market")) or TEAM_TOTAL_LABEL,
                "template_rows": {},
            },
        )
        if direction:
            group["template_rows"][direction] = row
    entries = []
    for event_id, group in list(grouped.items())[:MAX_MANUAL_TEAM_TOTAL_EVENTS]:
        over_existing = existing_by_event.get(event_id, {}).get("Over", {})
        under_existing = existing_by_event.get(event_id, {}).get("Under", {})
        entry = {
            "event_id": event_id,
            "rank": group.get("rank", ""),
            "match": group.get("match", ""),
            "commence_time": group.get("commence_time", ""),
            "priority_tier": group.get("priority_tier", ""),
            "missing_market": group.get("missing_market", TEAM_TOTAL_LABEL),
            "tab_match_name": first_nonblank(over_existing.get("tab_match_name"), under_existing.get("tab_match_name"), group.get("match")),
            "team_scope": first_nonblank(over_existing.get("team_scope"), under_existing.get("team_scope")),
            "tab_market_name": first_nonblank(over_existing.get("tab_market_name"), under_existing.get("tab_market_name"), "Team Total Goals"),
            "line": first_nonblank(over_existing.get("line"), under_existing.get("line")),
            "over_decimal_odds": first_nonblank(over_existing.get("decimal_odds")),
            "under_decimal_odds": first_nonblank(under_existing.get("decimal_odds")),
            "observed_at_aest": first_nonblank(over_existing.get("observed_at_aest"), under_existing.get("observed_at_aest")),
            "operator_initials": first_nonblank(over_existing.get("operator_initials"), under_existing.get("operator_initials")),
            "evidence_note_or_screenshot_ref": first_nonblank(
                over_existing.get("evidence_note_or_screenshot_ref"),
                under_existing.get("evidence_note_or_screenshot_ref"),
            ),
            "verification_status": first_nonblank(over_existing.get("verification_status"), under_existing.get("verification_status"), "pending"),
        }
        entries.append(entry)
    return {
        "ok": True,
        "ready": bool(entries),
        "status": "ready" if entries else "template_missing_or_empty",
        "entry_mode": "one_event_generates_over_under_pair_rows",
        "template_exists": template_path.exists(),
        "import_exists": import_path.exists(),
        "template_csv": PROVIDER_MANUAL_NEXT_BATCH_PAIR_TEMPLATE_CSV_LATEST,
        "import_target": DEFAULT_IMPORT_RELATIVE_PATH,
        "import_target_display": f"outputs/{DEFAULT_IMPORT_RELATIVE_PATH}",
        "event_count": len(entries),
        "row_count": len(template_rows),
        "entries": entries,
        "template_errors": template_errors,
        "import_errors": import_errors,
        "current_executable_new_stake_aud": 0,
        "safety_boundary": "只写固定 Team Total manual import CSV；不触发 provider refresh、TAB 点击、Bet Slip 修改或自动下注。",
    }


def manual_csv_rows_from_entry(template_rows: dict[str, dict[str, str]], entry: dict[str, str]) -> tuple[list[dict[str, str]], bool]:
    over_template = template_rows.get("Over") or next(iter(template_rows.values()), {})
    under_template = template_rows.get("Under") or over_template
    normalized = {
        "tab_match_name": first_nonblank(entry.get("tab_match_name"), over_template.get("match")),
        "team_scope": clean_manual_value(entry.get("team_scope"), max_len=40).lower(),
        "tab_market_name": first_nonblank(entry.get("tab_market_name"), "Team Total Goals"),
        "line": clean_manual_value(entry.get("line"), max_len=40),
        "over_decimal_odds": clean_manual_value(entry.get("over_decimal_odds"), max_len=40),
        "under_decimal_odds": clean_manual_value(entry.get("under_decimal_odds"), max_len=40),
        "observed_at_aest": clean_manual_value(entry.get("observed_at_aest"), max_len=80),
        "operator_initials": clean_manual_value(entry.get("operator_initials"), max_len=24),
        "evidence_note_or_screenshot_ref": clean_manual_value(entry.get("evidence_note_or_screenshot_ref"), max_len=220),
        "verification_status": manual_entry_status_for_fields(entry),
    }
    if normalized["team_scope"] not in {"home", "away", "team"}:
        normalized["team_scope"] = ""
    if not manual_entry_is_complete(normalized):
        return [blank_manual_csv_row(over_template), blank_manual_csv_row(under_template)], False
    rows = []
    for direction, template, odds in (
        ("Over", over_template, normalized["over_decimal_odds"]),
        ("Under", under_template, normalized["under_decimal_odds"]),
    ):
        row = blank_manual_csv_row(template)
        row.update(
            {
                "tab_match_name": normalized["tab_match_name"],
                "team_scope": normalized["team_scope"],
                "tab_market_name": normalized["tab_market_name"],
                "selection_name": direction,
                "line": normalized["line"],
                "decimal_odds": odds,
                "observed_at_aest": normalized["observed_at_aest"],
                "operator_initials": normalized["operator_initials"],
                "evidence_note_or_screenshot_ref": normalized["evidence_note_or_screenshot_ref"],
                "verification_status": normalized["verification_status"],
            }
        )
        rows.append(row)
    return rows, True


def render_manual_team_total_import_csv(rows: list[dict[str, str]]) -> str:
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=CSV_FIELDS, extrasaction="ignore", lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({field: row.get(field, "") for field in CSV_FIELDS})
    return buffer.getvalue()


def save_manual_team_total_entry(body: dict) -> tuple[dict, int]:
    payload = manual_team_total_entry_payload()
    template_path = OUTPUT_DIR / PROVIDER_MANUAL_NEXT_BATCH_PAIR_TEMPLATE_CSV_LATEST
    template_rows, template_errors = read_csv_dict_rows(template_path, max_rows=MAX_MANUAL_TEAM_TOTAL_EVENTS * 2)
    if template_errors or not template_rows:
        return {
            "ok": False,
            "error": "manual_template_not_ready",
            "template_csv": PROVIDER_MANUAL_NEXT_BATCH_PAIR_TEMPLATE_CSV_LATEST,
            "template_errors": template_errors,
            "current_executable_new_stake_aud": 0,
        }, HTTPStatus.CONFLICT
    entries = body.get("entries")
    if not isinstance(entries, list):
        return {"ok": False, "error": "entries_must_be_list", "current_executable_new_stake_aud": 0}, HTTPStatus.BAD_REQUEST

    incoming_by_event = {}
    for item in entries[:MAX_MANUAL_TEAM_TOTAL_EVENTS]:
        if not isinstance(item, dict):
            continue
        event_id = clean_manual_value(item.get("event_id"))
        if event_id:
            incoming_by_event[event_id] = item

    grouped_templates: dict[str, dict[str, dict[str, str]]] = {}
    ordered_event_ids = []
    for row in template_rows:
        event_id = clean_manual_value(row.get("event_id"))
        direction = manual_direction(row)
        if not event_id:
            continue
        if event_id not in grouped_templates:
            ordered_event_ids.append(event_id)
        grouped_templates.setdefault(event_id, {})
        if direction:
            grouped_templates[event_id][direction] = row

    output_rows = []
    completed_event_ids = []
    skipped_event_ids = []
    for event_id in ordered_event_ids[:MAX_MANUAL_TEAM_TOTAL_EVENTS]:
        entry = dict(incoming_by_event.get(event_id) or {})
        entry["event_id"] = event_id
        rows, complete = manual_csv_rows_from_entry(grouped_templates.get(event_id, {}), entry)
        output_rows.extend(rows)
        if complete:
            completed_event_ids.append(event_id)
        else:
            skipped_event_ids.append(event_id)

    import_path = OUTPUT_DIR / DEFAULT_IMPORT_RELATIVE_PATH
    import_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = import_path.with_name(f".{import_path.name}.{os.getpid()}.tmp")
    tmp.write_text(render_manual_team_total_import_csv(output_rows), encoding="utf-8")
    os.replace(tmp, import_path)
    bundle = write_provider_manual_verification_bundle(OUTPUT_DIR)
    refresh_download_assets()
    completion = bundle.get("completion") or {}
    import_quality = bundle.get("import_quality") or {}
    return {
        "ok": True,
        "status": bundle.get("status", "saved"),
        "import_target": DEFAULT_IMPORT_RELATIVE_PATH,
        "import_target_display": f"outputs/{DEFAULT_IMPORT_RELATIVE_PATH}",
        "written_row_count": len(output_rows),
        "complete_event_count": len(completed_event_ids),
        "skipped_incomplete_event_count": len(skipped_event_ids),
        "completed_event_ids": completed_event_ids,
        "skipped_incomplete_event_ids": skipped_event_ids,
        "manual_import_status": bundle.get("status", ""),
        "valid_row_count": completion.get("valid_row_count", 0),
        "invalid_row_count": completion.get("invalid_row_count", 0),
        "quality_status": import_quality.get("status", ""),
        "current_executable_new_stake_aud": 0,
        "safety_boundary": payload.get("safety_boundary"),
    }, HTTPStatus.OK


def public_raw_access_policy_runtime() -> dict:
    return {
        "status": "blocked_by_access_policy",
        "blocker_code": "ai_controlled_access_rejected",
        "automated_public_raw_refresh_allowed": False,
        "next_safe_action": (
            "TAB 拒绝 AI controlled access；停止自动公开 raw 抓取。"
            "请接入官方/授权数据源，或导入用户导出的公开盘口快照。"
        ),
        "forbidden_recovery": ["headed_fallback", "captcha_bypass", "fingerprint_spoofing", "stealth_browser"],
        "allowed_recovery": ["official_data_feed", "user_authorized_manual_export_import", "research_only_from_existing_fresh_partial_raw"],
    }


def raw_refresh_backfill_blocker() -> dict | None:
    health = load_json(OUTPUT_DIR / "raw_refresh_health_latest.json")
    if health.get("ready") is True:
        return None
    access_policy = health.get("access_policy") or public_raw_access_policy_runtime()
    blocker_codes = list(health.get("blocker_codes") or ["missing_raw_refresh_health"])
    if access_policy.get("blocker_code") and access_policy.get("blocker_code") not in blocker_codes:
        blocker_codes.append(access_policy["blocker_code"])
    return {
        "code": "raw_refresh_not_ready",
        "raw_status": health.get("status", "missing"),
        "ready_required_target_count": health.get("ready_required_target_count", 0),
        "blocker_codes": blocker_codes,
        "recommended_next_action": access_policy.get("next_safe_action", "先接入授权 raw 或导入用户导出快照，再执行缺口补跑。"),
        "access_policy": access_policy,
    }


def write_blocked_backfill_latest(blocker: dict) -> dict:
    timeline = load_json(OUTPUT_DIR / "active_timeline_latest.json")
    summary = timeline.get("summary") or {}
    total_queue_count = int(summary.get("backfill_queue_count") or 0)
    now = datetime.now(REPORT_TZ).isoformat()
    payload = {
        "schema_version": 1,
        "started_at": now,
        "finished_at": now,
        "mode": "safe_no_latest_publish",
        "status": "blocked_by_raw_refresh",
        "requested_count": 0,
        "completed_count": 0,
        "blocked_queue_count": min(total_queue_count, 3),
        "total_backfill_queue_count": total_queue_count,
        "max_backfill_runs": 3,
        "blocker": blocker,
        "partial_daily_research": write_partial_daily_research_after_blocked_backfill(),
        "results": [],
        "truthfulness_note": "公开盘口 raw 未就绪时不执行历史补跑，避免用 stale/blocked 数据生成误导性报告。",
    }
    ACTIVE_BACKFILL_LATEST_JSON.parent.mkdir(parents=True, exist_ok=True)
    tmp = ACTIVE_BACKFILL_LATEST_JSON.with_name(f".{ACTIVE_BACKFILL_LATEST_JSON.name}.{os.getpid()}.tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, ACTIVE_BACKFILL_LATEST_JSON)
    return payload


def write_partial_daily_research_after_blocked_backfill() -> dict:
    try:
        payload = write_partial_daily_research_bundle(OUTPUT_DIR, report_date=current_report_date())
    except Exception as exc:
        return {
            "ready": False,
            "status": "failed",
            "error": str(exc).splitlines()[0][:180],
            "message": "raw blocked 时尝试生成研究诊断日报失败。",
        }
    status = partial_daily_research_status_from_payload(payload)
    status["message"] = partial_daily_research_backfill_message(status)
    return status


def partial_daily_research_backfill_message(status: dict) -> str:
    if status.get("ready"):
        return "已补写 research-only 研究诊断日报；正式补跑仍因 raw blocked 暂停。"
    if status.get("status") == "failed":
        return "尝试生成 research-only 研究诊断日报失败；正式补跑仍因 raw blocked 暂停。"
    return "已尝试生成 research-only 研究诊断日报，但当前未达到 ready；正式补跑仍因 raw blocked 暂停。"


def int_or_none(value: object) -> int | None:
    try:
        return int(float(str(value)))
    except (TypeError, ValueError):
        return None


def float_or_zero(value: object) -> float:
    try:
        return float(str(value))
    except (TypeError, ValueError):
        return 0.0


def int_or_zero(value: object) -> int:
    try:
        return int(float(str(value)))
    except (TypeError, ValueError):
        return 0


def provider_credit_runway_payload(
    *,
    reported_remaining: object,
    estimated_credit_floor: object,
    estimated_credit_ceiling: object,
    recommended_batch_size: int,
) -> dict:
    remaining = int_or_none(reported_remaining)
    floor = max(0, int_or_none(estimated_credit_floor) or 0)
    ceiling = max(floor, int_or_none(estimated_credit_ceiling) or floor)
    remaining_after_floor = remaining - floor if remaining is not None else None
    remaining_after_ceiling = remaining - ceiling if remaining is not None else None
    if remaining is None:
        status = "credit_unknown"
        safe_batches = 0
        recommended_action = "credit 剩余值未同步；暂停新增 API probe，先刷新 provider KPI。"
    elif remaining <= PROVIDER_CREDIT_RESERVE_FLOOR:
        status = "reserve_floor_reached"
        safe_batches = 0
        recommended_action = "已触及 200 credits 保底线；停止 The Odds API 新增 probe，转 TT-001 人工校验或 OpticOdds 官方访问。"
    elif ceiling and remaining_after_ceiling is not None and remaining_after_ceiling < PROVIDER_CREDIT_RESERVE_FLOOR:
        status = "next_batch_would_cross_reserve"
        safe_batches = max(0, (remaining - PROVIDER_CREDIT_RESERVE_FLOOR) // ceiling)
        recommended_action = "下一批预计跌破 200 credits 保底线；本轮暂停 API，优先 Team Total 人工/OpticOdds。"
    elif recommended_batch_size <= 0 or ceiling <= 0:
        status = "no_api_batch_recommended"
        safe_batches = 0
        recommended_action = "当前无推荐 API batch；按工作台处理人工校验或等待新 provider 数据。"
    else:
        status = "credit_safe"
        safe_batches = max(0, (remaining - PROVIDER_CREDIT_RESERVE_FLOOR) // ceiling)
        recommended_action = "credit 仍在保底线以上；只允许按推荐 batch 小批量执行并复核 KPI。"
    return {
        "status": status,
        "reserve_floor": PROVIDER_CREDIT_RESERVE_FLOOR,
        "reported_remaining": remaining,
        "estimated_credit_floor": floor,
        "estimated_credit_ceiling": ceiling,
        "remaining_after_next_batch_floor": remaining_after_floor,
        "remaining_after_next_batch_ceiling": remaining_after_ceiling,
        "safe_next_batch_count_before_reserve": safe_batches,
        "recommended_action": recommended_action,
    }


def provider_command_center_payload(
    *,
    provider_config_doctor: dict,
    provider_kpi: dict,
    provider_alternate_plan: dict,
    provider_manual_workbench: dict,
) -> dict:
    summary = provider_kpi.get("summary") or {}
    executive = provider_kpi.get("executive_status") or {}
    credit = summary.get("credit") or {}
    config_odds = provider_config_doctor.get("the_odds_api") or {}
    config_summary = provider_config_doctor.get("summary") or {}
    credit_policy = provider_alternate_plan.get("credit_policy") or {}
    operational_decision = provider_alternate_plan.get("operational_decision") or {}
    event_probe_evidence = provider_alternate_plan.get("event_probe_evidence") or {}
    next_batch = provider_manual_workbench.get("next_batch") or {}
    pair_templates = provider_manual_workbench.get("pair_templates") or {}
    quality_gate = provider_manual_workbench.get("quality_gate_summary") or {}
    manual_intake_contract = provider_manual_workbench.get("manual_intake_contract") or {}
    recommended_batch_size = int(credit_policy.get("recommended_batch_size") or 0)
    recommended_command = str(provider_alternate_plan.get("recommended_command") or "")
    provider_key_present = bool(config_odds.get("api_key_present"))
    credit_runway = provider_credit_runway_payload(
        reported_remaining=credit.get("reported_remaining"),
        estimated_credit_floor=credit_policy.get("estimated_next_batch_credit_floor"),
        estimated_credit_ceiling=credit_policy.get("estimated_next_batch_credit_ceiling"),
        recommended_batch_size=recommended_batch_size,
    )
    can_run_provider_batch = bool(
        provider_key_present
        and recommended_batch_size > 0
        and recommended_command
        and credit_runway["status"] == "credit_safe"
    )
    return {
        "ready": bool(provider_kpi) or bool(provider_alternate_plan),
        "status": provider_alternate_plan.get("status", "missing"),
        "refresh_id": provider_alternate_plan.get("refresh_id") or provider_kpi.get("refresh_id", ""),
        "title": operational_decision.get("title") or executive.get("primary_gap", ""),
        "primary_action": operational_decision.get("primary_action")
        or provider_alternate_plan.get("recommended_next_action")
        or executive.get("recommended_next_action", ""),
        "why": operational_decision.get("why") or config_summary.get("next_safe_action", ""),
        "can_run_provider_batch": can_run_provider_batch,
        "provider_batch": {
            "recommended_batch_size": recommended_batch_size,
            "probe_queue_count": int(provider_alternate_plan.get("probe_queue_count") or 0),
            "recommended_command": recommended_command,
            "estimated_credit_floor": credit_policy.get("estimated_next_batch_credit_floor"),
            "estimated_credit_ceiling": credit_policy.get("estimated_next_batch_credit_ceiling"),
            "provider_key_present": provider_key_present,
        },
        "credit": {
            "reported_remaining": credit.get("reported_remaining"),
            "reported_used": credit.get("reported_used"),
            "remaining_ratio": credit.get("remaining_ratio"),
            "latest_request_cost": credit.get("reported_last_request_cost"),
            "inferred_monthly_limit": credit.get("inferred_monthly_limit"),
        },
        "credit_runway": credit_runway,
        "team_total_manual": {
            "status": provider_manual_workbench.get("status", "missing"),
            "next_batch_id": next_batch.get("batch_id", ""),
            "next_batch_event_count": int(next_batch.get("event_count") or 0),
            "next_batch_pair_rows": int(pair_templates.get("next_batch_pair_rows") or 0),
            "next_batch_template_csv": pair_templates.get("next_batch_csv", ""),
            "import_target": pair_templates.get("import_target", ""),
            "quality_status": quality_gate.get("import_quality_status", ""),
            "missing_event_count": int(quality_gate.get("missing_event_count") or 0),
            "manual_intake_contract": manual_intake_contract,
        },
        "evidence": {
            "market_probe_count": int(event_probe_evidence.get("market_probe_count") or 0),
            "event_odds_count": int(event_probe_evidence.get("event_odds_count") or 0),
            "team_total_available_probe_count": int(event_probe_evidence.get("team_total_available_probe_count") or 0),
            "total_available_probe_count": int(event_probe_evidence.get("total_available_probe_count") or 0),
        },
        "gates": {
            "formal_publish_allowed": bool(provider_kpi.get("formal_publish_allowed")),
            "full_automation_allowed": bool(provider_kpi.get("full_automation_allowed")),
            "current_executable_new_stake_aud": provider_kpi.get("current_executable_new_stake_aud", 0),
        },
        "market_family_gaps": provider_alternate_plan.get("market_family_gaps", []),
        "stop_conditions": provider_alternate_plan.get("stop_conditions", []),
        "recommended_next_action": provider_alternate_plan.get("recommended_next_action")
        or executive.get("recommended_next_action", ""),
    }


def provider_alternate_market_decision(row: dict, credit_runway: dict) -> dict:
    status = str(row.get("status") or "")
    family_id = str(row.get("id") or "")
    coverage_ratio = float_or_zero(row.get("coverage_ratio"))
    required_ratio = float_or_zero(row.get("required_ratio"))
    missing_count = int_or_zero(row.get("missing_count"))
    if family_id == "team_total_ou":
        action_status = "manual_or_official_required"
        action_label = "转 TT-001 / OpticOdds"
        action = "The Odds API 当前 TAB 样本未提供 Team Total；不扩大盲扫，走 TT-001 人工只读或 OpticOdds 官方访问。"
    elif status == "ready" or (required_ratio and coverage_ratio >= required_ratio):
        action_status = "coverage_threshold_met"
        action_label = "可用于研究上下文"
        action = "覆盖已达到当前阈值；只有进入候选下注研究时才做 TAB/官方源最终校验。"
    elif credit_runway.get("status") != "credit_safe":
        action_status = "credit_paused"
        action_label = "暂停 API"
        action = "当前 credit runway 不允许继续 batch；保留现有覆盖，等待额度或转人工/官方源。"
    elif missing_count > 0:
        action_status = "api_batch_candidate"
        action_label = "可小批量补齐"
        action = "仅在 credit_safe 时按 recommended command 小批量补齐，完成后重建 KPI。"
    else:
        action_status = "watch"
        action_label = "观察"
        action = "暂无可执行补齐动作；等待下一批 provider evidence。"
    return {
        "market_id": family_id,
        "market": row.get("label", ""),
        "role": row.get("role", ""),
        "covered_count": int_or_zero(row.get("covered_count")),
        "event_count": int_or_zero(row.get("event_count")),
        "coverage_ratio": row.get("coverage_ratio"),
        "required_ratio": row.get("required_ratio"),
        "missing_count": missing_count,
        "status": status,
        "provider_status": row.get("provider_status", ""),
        "available_probe_count": int_or_zero(row.get("available_probe_count")),
        "sample_evidence": row.get("sample_evidence", ""),
        "action_status": action_status,
        "action_label": action_label,
        "recommended_action": row.get("recommended_provider_action") or action,
    }


def provider_alternate_workbench_payload(
    *,
    provider_kpi: dict,
    provider_alternate_plan: dict,
    provider_command_center: dict,
) -> dict:
    summary = provider_kpi.get("summary") or {}
    executive = provider_kpi.get("executive_status") or {}
    credit_runway = provider_command_center.get("credit_runway") or {}
    family_rows = [
        provider_alternate_market_decision(dict(row), credit_runway)
        for row in (provider_alternate_plan.get("market_family_gaps") or [])
        if isinstance(row, dict)
    ]
    ready_count = sum(1 for row in family_rows if row.get("action_status") == "coverage_threshold_met")
    api_candidate_count = sum(1 for row in family_rows if row.get("action_status") == "api_batch_candidate")
    manual_count = sum(1 for row in family_rows if row.get("action_status") == "manual_or_official_required")
    credit_paused_count = sum(1 for row in family_rows if row.get("action_status") == "credit_paused")
    value_support_rows = [row for row in family_rows if row.get("role") == "value_support"]
    value_support_ready_count = sum(1 for row in value_support_rows if row.get("status") == "ready")
    next_queue = [
        {
            "event_id": row.get("event_id", ""),
            "match": row.get("match", ""),
            "commence_time": row.get("commence_time", ""),
            "missing_families": row.get("missing_families") or [],
            "recommended_markets": row.get("recommended_markets") or [],
            "recommended_action": row.get("recommended_action", ""),
        }
        for row in (provider_alternate_plan.get("next_probe_queue") or provider_alternate_plan.get("next_probe_queue_preview") or [])[:12]
        if isinstance(row, dict)
    ]
    recommended_command = str(provider_alternate_plan.get("recommended_command") or "")
    can_run_provider_batch = bool(provider_command_center.get("can_run_provider_batch"))
    if can_run_provider_batch:
        next_safe_action = "credit_safe 时才允许人工终端执行 recommended command；完成后重建 KPI 并复核 stake=0。"
    else:
        next_safe_action = "当前不执行 The Odds API 新 batch；优先 TT-001 人工校验、OpticOdds 官方访问和 My Bets 只读持仓。"
    return {
        "ready": bool(family_rows) or bool(provider_alternate_plan),
        "status": provider_alternate_plan.get("status", "missing"),
        "refresh_id": provider_alternate_plan.get("refresh_id") or provider_kpi.get("refresh_id", ""),
        "overall_progress_pct": executive.get("overall_progress_pct") or executive.get("overall_score"),
        "event_count": int_or_zero(summary.get("event_count")),
        "can_run_provider_batch": can_run_provider_batch,
        "credit_runway_status": credit_runway.get("status", ""),
        "recommended_command": recommended_command,
        "summary": {
            "market_family_count": len(family_rows),
            "coverage_threshold_met_count": ready_count,
            "api_candidate_count": api_candidate_count,
            "manual_or_official_required_count": manual_count,
            "credit_paused_count": credit_paused_count,
            "value_support_ready_count": value_support_ready_count,
            "value_support_count": len(value_support_rows),
            "next_probe_queue_count": int_or_zero(provider_alternate_plan.get("probe_queue_count") or len(next_queue)),
            "fallback_queue_count": int_or_zero(provider_alternate_plan.get("fallback_queue_count")),
        },
        "market_rows": family_rows,
        "next_probe_queue_preview": next_queue,
        "stop_conditions": provider_alternate_plan.get("stop_conditions") or [],
        "operational_decision": provider_alternate_plan.get("operational_decision") or {},
        "current_executable_new_stake_aud": provider_kpi.get("current_executable_new_stake_aud", 0),
        "next_safe_action": next_safe_action,
        "safety_boundary": "该工作台只读聚合已有 provider artifacts，不触发 API refresh、TAB 点击、Bet Slip 修改或自动下注。",
    }


def automation_work_queue_payload(
    *,
    provider_command_center: dict,
    provider_config_doctor: dict,
    provider_fallback_verification: dict,
    provider_manual_overlay_publish_preflight: dict,
    provider_manual_overlay_publish: dict,
    readiness: dict,
    raw_health: dict,
    private_position: dict,
) -> dict:
    tasks: list[dict] = []
    gates = provider_command_center.get("gates") or {}
    team_total = provider_command_center.get("team_total_manual") or {}
    intake = team_total.get("manual_intake_contract") or {}
    intake_state = intake.get("current_state") or {}
    credit_runway = provider_command_center.get("credit_runway") or {}
    provider_batch = provider_command_center.get("provider_batch") or {}
    config_optic = provider_config_doctor.get("opticodds") or {}
    fallback_queue_count = int(provider_fallback_verification.get("queue_count") or 0)
    stake = gates.get("current_executable_new_stake_aud", 0) or 0

    def add_task(
        *,
        task_id: str,
        priority: str,
        title: str,
        status: str,
        owner: str,
        gate: str,
        action: str,
        acceptance: str,
        blocker: str = "",
        command: str = "",
        artifact: str = "",
        evidence: str = "",
        stake_boundary: str = "current_executable_new_stake_aud=0",
    ) -> None:
        tasks.append(
            {
                "id": task_id,
                "priority": priority,
                "title": title,
                "status": status,
                "owner": owner,
                "gate": gate,
                "action": action,
                "blocker": blocker,
                "command": command,
                "artifact": artifact,
                "evidence": evidence,
                "acceptance": acceptance,
                "stake_boundary": stake_boundary,
            }
        )

    manual_missing = int(team_total.get("missing_event_count") or intake_state.get("missing_event_count") or 0)
    next_batch_id = str(team_total.get("next_batch_id") or intake.get("current_batch_id") or "TT-001")
    next_batch_rows = int(team_total.get("next_batch_pair_rows") or intake_state.get("next_batch_pair_rows") or 0)
    if manual_missing > 0 or next_batch_rows > 0:
        add_task(
            task_id="TT-001",
            priority="P0",
            title=f"{next_batch_id} Team Total 人工导入",
            status="manual_required",
            owner="operator",
            gate="provider_manual_workbench",
            action=f"填写 {next_batch_rows} 行 Team Total O/U，只读核验 TAB，不点击赔率或 Bet Slip。",
            blocker=f"Team Total 缺失 {manual_missing} 场；API 当前不能给出完整覆盖。",
            command=str(intake.get("rebuild_command") or "TAB_FIFA_FAST_ENTRY_REBUILD=1 python3 scripts/build_downloads_app_entry.py"),
            artifact=str(intake.get("import_target_display") or intake.get("import_target") or team_total.get("import_target") or ""),
            evidence=f"quality={team_total.get('quality_status', '')}; batch={next_batch_id}; rows={next_batch_rows}",
            acceptance="CSV 导入质量为 complete 或 partial 可解释，hash gate 生成，stake 仍为 0。",
        )

    credit_status = str(credit_runway.get("status") or "credit_unknown")
    if credit_status != "credit_safe" or not provider_command_center.get("can_run_provider_batch"):
        add_task(
            task_id="CREDIT-RESERVE",
            priority="P0",
            title="The Odds API batch 暂停",
            status="credit_or_yield_blocked",
            owner="system",
            gate="provider_credit_runway",
            action="不要继续批量消耗 The Odds API credits；保留 200 credits 安全线，优先人工/官方 provider。",
            blocker=str(credit_runway.get("recommended_action") or provider_command_center.get("why") or ""),
            command=str(provider_batch.get("recommended_command") or ""),
            artifact="outputs/provider_kpi_latest.json",
            evidence=(
                f"remaining={credit_runway.get('reported_remaining')}; reserve={credit_runway.get('reserve_floor')}; "
                f"after_next={credit_runway.get('remaining_after_next_batch_ceiling')}; status={credit_status}"
            ),
            acceptance="只有 credit_runway=credit_safe 且 recommended_batch_size>0 时，才允许人工终端执行下一批。",
        )

    if fallback_queue_count > 0 or not config_optic.get("api_key_present"):
        add_task(
            task_id="OPTICODDS-ACCESS",
            priority="P1",
            title="OpticOdds 官方访问/白名单",
            status="provider_access_required",
            owner="operator",
            gate="authorized_provider_access",
            action="申请或配置 OpticOdds 官方访问，用于补 Team Total 和盘口深度，不绕过 TAB AI access 限制。",
            blocker=f"fallback queue {fallback_queue_count}; opticodds_key_present={bool(config_optic.get('api_key_present'))}",
            artifact="config/odds_providers.local.env.example",
            evidence=str(provider_fallback_verification.get("provider_blocker_code") or ""),
            acceptance="Provider doctor 显示 OpticOdds key 可用，且 Team Total coverage 能通过官方 API 或人工最终校验增加。",
        )

    if not private_position.get("ready"):
        add_task(
            task_id="MY-BETS-READONLY",
            priority="P1",
            title="My Bets 私有持仓只读同步",
            status="login_required",
            owner="operator",
            gate="private_position_profile",
            action="在本机 Chrome/TAB 登录状态下运行只读持仓读取；不自动下注、不改 Bet Slip。",
            blocker=str(private_position.get("blocking_reason") or private_position.get("next_safe_action") or ""),
            artifact="private_outputs/my_bets/",
            evidence=f"profile_exists={private_position.get('profile_exists')}; snapshot_exists={private_position.get('snapshot_exists')}",
            acceptance="position_monitor 能同步已下注、结算和累计收益率；失败时继续 stake=0。",
        )

    if not gates.get("formal_publish_allowed") or not gates.get("full_automation_allowed"):
        preflight_status = str(provider_manual_overlay_publish_preflight.get("status") or "missing")
        publish_status = str(provider_manual_overlay_publish.get("status") or "not_run")
        add_task(
            task_id="FORMAL-PUBLISH-GATE",
            priority="P1",
            title="正式 raw 发布与 automation gate",
            status="blocked_until_manual_signature",
            owner="system",
            gate="manual_hash_overlay_preflight",
            action="等人工导入、hash gate、overlay preflight 和用户签名全部通过后，才允许正式 raw/报告发布。",
            blocker=f"formal={bool(gates.get('formal_publish_allowed'))}; automation={bool(gates.get('full_automation_allowed'))}",
            artifact="outputs/provider_manual_overlay_publish_preflight_latest.json",
            evidence=f"preflight={preflight_status}; publish={publish_status}",
            acceptance="formal_publish_allowed=true、full_automation_allowed=true 且当前新增下注金额由报告策略重新计算。",
        )

    raw_ready = bool(raw_health.get("ready"))
    readiness_status = str(readiness.get("status") or readiness.get("automation_status") or "unknown")
    add_task(
        task_id="AUTOMATION-READINESS",
        priority="P2",
        title="每日 automation readiness 验证",
        status="not_ready" if tasks or not raw_ready else "ready_for_review",
        owner="system",
        gate="end_to_end_verification",
        action="在所有 P0/P1 gate 关闭后，运行完整测试、报告构建、浏览器 smoke 和 API status smoke。",
        blocker="" if raw_ready else str(raw_health.get("recommended_next_action") or "raw_refresh not ready"),
        artifact="outputs/automation_readiness_latest.json",
        evidence=f"readiness={readiness_status}; raw_ready={raw_ready}",
        acceptance="测试通过、报告可打开、status 无冲突、stake 不再被 gate 强制归零后，再讨论每日自动生成。",
    )

    priority_order = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
    status_order = {
        "manual_required": 0,
        "credit_or_yield_blocked": 1,
        "provider_access_required": 2,
        "login_required": 3,
        "blocked_until_manual_signature": 4,
        "not_ready": 5,
    }
    tasks.sort(
        key=lambda item: (
            priority_order.get(str(item.get("priority")), 9),
            status_order.get(str(item.get("status")), 9),
            str(item.get("id")),
        )
    )
    blocked_statuses = {"manual_required", "credit_or_yield_blocked", "provider_access_required", "login_required", "blocked_until_manual_signature", "not_ready"}
    blocked_count = sum(1 for item in tasks if item.get("status") in blocked_statuses)
    manual_required_count = sum(1 for item in tasks if item.get("status") == "manual_required")
    p0_count = sum(1 for item in tasks if item.get("priority") == "P0")
    automation_ready = blocked_count == 0 and bool(gates.get("full_automation_allowed")) and bool(raw_health.get("ready"))
    return {
        "ready": True,
        "automation_ready": automation_ready,
        "formal_publish_allowed": bool(gates.get("formal_publish_allowed")),
        "full_automation_allowed": bool(gates.get("full_automation_allowed")),
        "current_executable_new_stake_aud": stake,
        "summary": {
            "task_count": len(tasks),
            "blocked_count": blocked_count,
            "manual_required_count": manual_required_count,
            "p0_count": p0_count,
            "next_task_id": (tasks[0] or {}).get("id") if tasks else "",
            "next_task_title": (tasks[0] or {}).get("title") if tasks else "",
            "credit_runway_status": credit_status,
            "team_total_missing_event_count": manual_missing,
            "team_total_next_batch_pair_rows": next_batch_rows,
            "provider_fallback_queue_count": fallback_queue_count,
        },
        "tasks": tasks,
        "next_safe_action": (tasks[0] or {}).get("action") if tasks else "所有 gate 已清空；进入最终 automation readiness 验证。",
        "safety_boundary": "此队列只读聚合，不触发 provider refresh、TAB 点击、Bet Slip 修改或自动下注。",
    }


def automation_scorecard_payload(
    *,
    provider_config_doctor: dict,
    provider_command_center: dict,
    provider_alternate_workbench: dict,
    automation_work_queue: dict,
    position_monitor_status: dict,
    raw_health: dict,
) -> dict:
    config_odds = provider_config_doctor.get("the_odds_api") or {}
    alternate_summary = provider_alternate_workbench.get("summary") or {}
    gates = provider_command_center.get("gates") or {}
    credit_runway = provider_command_center.get("credit_runway") or {}
    tasks = automation_work_queue.get("tasks") or []
    task_by_id = {str(item.get("id") or ""): item for item in tasks if isinstance(item, dict)}
    credit_status = str(provider_alternate_workbench.get("credit_runway_status") or credit_runway.get("status") or "")
    value_support_count = int_or_zero(alternate_summary.get("value_support_count"))
    value_support_ready_count = int_or_zero(alternate_summary.get("value_support_ready_count"))
    credit_done = credit_status == "credit_safe" or (
        credit_status == "no_api_batch_recommended"
        and int_or_zero(alternate_summary.get("api_candidate_count")) == 0
        and int_or_zero(alternate_summary.get("credit_paused_count")) == 0
    )
    gate_rows: list[dict] = []

    def add_gate(
        gate_id: str,
        title: str,
        weight: int,
        done: bool,
        status: str,
        owner: str,
        evidence: str,
        next_action: str,
    ) -> None:
        gate_rows.append(
            {
                "id": gate_id,
                "title": title,
                "weight": weight,
                "done": bool(done),
                "status": "passed" if done else status,
                "owner": owner,
                "evidence": evidence,
                "next_action": "保持监控。" if done else next_action,
            }
        )

    add_gate(
        "provider_key_and_sport_config",
        "Provider key 与 sport 配置",
        10,
        bool(config_odds.get("api_key_present")) and "soccer_world_cup" not in (config_odds.get("known_invalid_or_legacy_sports") or []),
        "blocked",
        "system",
        f"the_odds_key={bool(config_odds.get('api_key_present'))}; recommended_sports={','.join(config_odds.get('recommended_sports') or [])}",
        "配置 THE_ODDS_API_KEY，并保持 sport 为 soccer_fifa_world_cup；不把真实 key 提交到 Git。",
    )
    add_gate(
        "core_matches_coverage",
        "Matches 核心盘口覆盖",
        18,
        int_or_zero(alternate_summary.get("coverage_threshold_met_count")) >= 2,
        "in_progress",
        "system",
        f"ready_families={alternate_summary.get('coverage_threshold_met_count')}/{alternate_summary.get('market_family_count')}; events={provider_alternate_workbench.get('event_count')}",
        "继续用授权 provider 或人工最终校验补齐 Result/Handicap/Total 等核心上下文。",
    )
    add_gate(
        "value_support_coverage",
        "Value-support 盘口覆盖",
        12,
        value_support_count > 0 and value_support_ready_count >= value_support_count,
        "paused",
        "system",
        f"value_support_ready={value_support_ready_count}/{value_support_count}; credit_paused={alternate_summary.get('credit_paused_count')}",
        "只在 credit_safe 时小批量补 BTTS、Double Chance、Draw No Bet；否则等待额度或官方源。",
    )
    add_gate(
        "team_total_coverage",
        "Team Total O/U 覆盖",
        18,
        int_or_zero(alternate_summary.get("manual_or_official_required_count")) == 0 and "TT-001" not in task_by_id,
        "manual_required",
        "operator",
        f"manual_or_official_required={alternate_summary.get('manual_or_official_required_count')}; fallback_queue={alternate_summary.get('fallback_queue_count')}",
        "完成 TT-001 人工只读录入，或接入 OpticOdds 官方访问/白名单。",
    )
    add_gate(
        "credit_runway",
        "Credit runway",
        10,
        credit_done,
        "paused",
        "system",
        f"status={credit_status}; remaining={credit_runway.get('reported_remaining')}; after_next={credit_runway.get('remaining_after_next_batch_ceiling')}",
        "保持 200 credits reserve；只有 credit_safe 或无剩余 API 候选时才解锁。",
    )
    add_gate(
        "my_bets_readonly_snapshot",
        "My Bets 只读持仓快照",
        14,
        bool(position_monitor_status.get("ready")) and bool(position_monitor_status.get("snapshot_ready")),
        "login_required",
        "operator",
        f"profile_exists={position_monitor_status.get('profile_exists')}; snapshot_ready={position_monitor_status.get('snapshot_ready')}",
        "在本机 TAB 登录后运行只读持仓读取；不同步持仓时 stake 继续为 0。",
    )
    add_gate(
        "formal_publish_gate",
        "Formal publish / automation gate",
        12,
        bool(gates.get("formal_publish_allowed")) and bool(gates.get("full_automation_allowed")),
        "blocked",
        "system",
        f"formal={bool(gates.get('formal_publish_allowed'))}; automation={bool(gates.get('full_automation_allowed'))}",
        "等待人工导入、hash gate、overlay preflight 和用户签名全部通过。",
    )
    add_gate(
        "daily_automation_verification",
        "每日 automation E2E 验证",
        6,
        bool(automation_work_queue.get("automation_ready")) and bool(raw_health.get("ready")),
        "not_ready",
        "system",
        f"automation_ready={bool(automation_work_queue.get('automation_ready'))}; raw_ready={bool(raw_health.get('ready'))}",
        "所有 P0/P1 gate 清空后运行完整测试、报告构建、浏览器 smoke 和 API smoke。",
    )
    total_weight = sum(int(row["weight"]) for row in gate_rows) or 1
    passed_weight = sum(int(row["weight"]) for row in gate_rows if row["done"])
    blocked_rows = [row for row in gate_rows if not row["done"]]
    p0_count = int_or_zero((automation_work_queue.get("summary") or {}).get("p0_count"))
    stage = "automation_ready" if not blocked_rows else "research_platform_with_manual_gates"
    return {
        "ready": True,
        "stage": stage,
        "automation_progress_pct": round(passed_weight / total_weight, 4),
        "passed_weight": passed_weight,
        "total_weight": total_weight,
        "gate_count": len(gate_rows),
        "passed_gate_count": len(gate_rows) - len(blocked_rows),
        "blocked_gate_count": len(blocked_rows),
        "p0_count": p0_count,
        "next_gate_id": (blocked_rows[0] or {}).get("id") if blocked_rows else "",
        "next_gate_title": (blocked_rows[0] or {}).get("title") if blocked_rows else "Ready for final automation verification",
        "next_safe_action": (blocked_rows[0] or {}).get("next_action") if blocked_rows else "运行最终 readiness 验证并准备每日自动报告。",
        "current_executable_new_stake_aud": automation_work_queue.get("current_executable_new_stake_aud", 0),
        "can_enter_daily_automation": not blocked_rows and bool(automation_work_queue.get("automation_ready")),
        "gate_rows": gate_rows,
        "safety_boundary": "Scorecard 只读聚合现有 artifacts/API 状态，不触发 provider refresh、TAB 点击、Bet Slip 修改或自动下注。",
    }


def operation_panel_payload(
    *,
    automation_scorecard: dict,
    automation_work_queue: dict,
    provider_command_center: dict,
    provider_alternate_workbench: dict,
    position_monitor_status: dict,
    raw_health: dict,
    provider_kpi: dict,
    report_date: str,
) -> dict:
    work_summary = automation_work_queue.get("summary") or {}
    tasks = automation_work_queue.get("tasks") or []
    next_task = tasks[0] if tasks else {}
    current_stake = automation_scorecard.get("current_executable_new_stake_aud", 0) or 0
    execution_allowed = bool(automation_scorecard.get("can_enter_daily_automation")) and current_stake > 0
    next_task_id = str(next_task.get("id") or "")
    if next_task_id.startswith("TT-"):
        primary_href = "#team-total-manual-entry"
        primary_label = "填写 TT-001"
    elif next_task_id.startswith("MY-BETS"):
        primary_href = "#position-monitor"
        primary_label = "同步只读持仓"
    elif next_task_id.startswith("CREDIT") or next_task_id.startswith("OPTICODDS"):
        primary_href = "#provider-command-console"
        primary_label = "看采集控制台"
    elif next_task_id:
        primary_href = "#automation-work-queue"
        primary_label = "处理工作队列"
    else:
        primary_href = "#active-test"
        primary_label = "运行最终验证"
    raw_partial = normalize_partial_research_refresh(raw_health.get("partial_research_refresh") or {})
    provider_summary = provider_kpi.get("summary") or {}
    provider_credit = provider_summary.get("credit") or {}
    status_cards = [
        {
            "label": "下注状态",
            "value": "可进入人工复核执行" if execution_allowed else "暂停新增下注",
            "detail": f"新增可执行金额 AUD {float(current_stake):.0f}",
            "status": "ok" if execution_allowed else "blocked",
        },
        {
            "label": "Automation",
            "value": f"{float(automation_scorecard.get('automation_progress_pct') or 0) * 100:.2f}%",
            "detail": f"通过 {automation_scorecard.get('passed_gate_count', 0)}/{automation_scorecard.get('gate_count', 0)} gates",
            "status": "ok" if automation_scorecard.get("can_enter_daily_automation") else "watch",
        },
        {
            "label": "数据新鲜度",
            "value": raw_partial.get("freshness_status") or raw_health.get("status") or "missing",
            "detail": f"raw {raw_health.get('status', 'missing')}；report {report_date}",
            "status": "ok" if raw_health.get("ready") else "blocked",
        },
        {
            "label": "盘口覆盖",
            "value": provider_alternate_workbench.get("status") or provider_command_center.get("status") or "missing",
            "detail": f"events {provider_alternate_workbench.get('event_count', provider_summary.get('event_count', 0))}；credit {provider_credit.get('reported_remaining', '待同步')}",
            "status": "ok" if provider_command_center.get("can_run_provider_batch") else "watch",
        },
        {
            "label": "持仓同步",
            "value": "已同步" if position_monitor_status.get("snapshot_ready") else "待只读同步",
            "detail": position_monitor_status.get("blocking_reason") or position_monitor_status.get("next_safe_action") or "",
            "status": "ok" if position_monitor_status.get("snapshot_ready") else "blocked",
        },
    ]
    quick_steps = [
        {
            "label": "1. 先看结论",
            "href": "#recommendations",
            "detail": "只读查看候选，不代表可执行。",
            "status": "ok" if provider_kpi.get("provider_analysis_ready") else "watch",
        },
        {
            "label": "2. 处理下一任务",
            "href": primary_href,
            "detail": next_task.get("title") or automation_scorecard.get("next_gate_title") or "",
            "status": "blocked" if not execution_allowed else "ok",
        },
        {
            "label": "3. 主动测试补缺",
            "href": "#active-test",
            "detail": f"待补 {work_summary.get('blocked_count', 0)} 个 gate / P0 {work_summary.get('p0_count', 0)}",
            "status": "watch",
        },
        {
            "label": "4. 最终再执行",
            "href": "#execution-list",
            "detail": "所有 gate 通过前金额保持 0。",
            "status": "ok" if execution_allowed else "blocked",
        },
    ]
    blockers = [
        {
            "id": row.get("id"),
            "title": row.get("title"),
            "status": row.get("status"),
            "next_action": row.get("next_action"),
        }
        for row in (automation_scorecard.get("gate_rows") or [])
        if not row.get("done")
    ][:4]
    headline = "可进入人工复核执行" if execution_allowed else "当前不要新增下注"
    subheadline = (
        "所有 gate 已通过，仍需人工复核 TAB 实时赔率后再执行。"
        if execution_allowed
        else "系统当前只能输出研究候选；正式 raw、持仓或人工校验 gate 未通过前，新增下注金额保持 AUD 0。"
    )
    return {
        "ready": True,
        "headline": headline,
        "subheadline": subheadline,
        "primary_label": primary_label,
        "primary_href": primary_href,
        "secondary_label": "主动测试与自动补缺",
        "secondary_href": "#active-test",
        "next_safe_action": next_task.get("action") or automation_scorecard.get("next_safe_action") or "",
        "generated_at_aest": datetime.now(REPORT_TZ).isoformat(timespec="seconds"),
        "report_date": report_date,
        "current_executable_new_stake_aud": current_stake,
        "automation_progress_pct": automation_scorecard.get("automation_progress_pct", 0),
        "status_cards": status_cards,
        "quick_steps": quick_steps,
        "blockers": blockers,
        "safety_boundary": "操作总览只读展示状态和跳转，不触发 provider refresh、TAB 点击、Bet Slip 修改或自动下注。",
    }


def position_monitor_status_payload(
    *,
    position_monitor: dict,
    private_position: dict,
    report_date: str,
) -> dict:
    summary = position_monitor.get("summary") or {}
    executive = position_monitor.get("executive_status") or {}
    preflight = position_monitor.get("private_preflight") or private_position.get("preflight") or {}
    policy = position_monitor.get("private_metric_policy") or {}
    rows = []
    for row in (position_monitor.get("monitor_rows") or [])[:12]:
        rows.append(
            {
                "item_id": row.get("item_id", ""),
                "label": row.get("label", ""),
                "status": row.get("status", ""),
                "ready": bool(row.get("ready")),
                "next_action": row.get("next_action", ""),
            }
        )
    snapshot_ready = bool(summary.get("snapshot_ready") or private_position.get("snapshot_exists"))
    private_metrics_available = bool(executive.get("private_metrics_available") or snapshot_ready)
    status = str(executive.get("status") or private_position.get("status") or "missing")
    recommended_next_action = (
        executive.get("recommended_next_action")
        or summary.get("preflight_next_safe_action")
        or private_position.get("next_safe_action")
        or ""
    )
    blocking_reason = (
        summary.get("preflight_blocking_reason")
        or preflight.get("blocking_reason")
        or private_position.get("blocking_reason")
        or ""
    )
    return {
        "ready": private_metrics_available,
        "artifact_ready": bool(position_monitor),
        "status": status,
        "report_date": summary.get("report_date") or private_position.get("report_date") or report_date,
        "snapshot_ready": snapshot_ready,
        "snapshot_status": summary.get("snapshot_status", ""),
        "snapshot_issue_count": int(summary.get("snapshot_issue_count") or 0),
        "private_metrics_available": private_metrics_available,
        "profile_exists": bool(summary.get("profile_exists") or private_position.get("profile_exists")),
        "raw_text_exists": bool(summary.get("raw_text_exists") or private_position.get("raw_text_exists")),
        "snapshot_exists": bool(summary.get("snapshot_exists") or private_position.get("snapshot_exists")),
        "diagnostics_exists": bool(summary.get("diagnostics_exists") or private_position.get("diagnostics_exists")),
        "preflight_status": summary.get("preflight_status") or preflight.get("status", ""),
        "blocking_reason": blocking_reason,
        "next_safe_action": recommended_next_action,
        "recommended_next_action": recommended_next_action,
        "login_window_required": bool(summary.get("login_window_required") or private_position.get("login_window_required")),
        "manual_step_required": bool(summary.get("manual_step_required") or private_position.get("manual_step_required")),
        "wait_for_login_seconds": summary.get("wait_for_login_seconds") or private_position.get("wait_for_login_seconds", 600),
        "capture_mode": summary.get("capture_mode") or private_position.get("capture_mode", ""),
        "credential_policy": summary.get("credential_policy") or preflight.get("credential_policy") or policy.get("credential_policy", ""),
        "automation_boundary": summary.get("automation_boundary")
        or preflight.get("automation_boundary")
        or policy.get("automation_boundary", ""),
        "public_visible_balance": summary.get("public_visible_balance", "account-update-pending"),
        "public_visible_open_exposure": summary.get("public_visible_open_exposure", "account-update-pending"),
        "public_visible_realized_roi": summary.get("public_visible_realized_roi", "account-update-pending"),
        "raw_refresh_ready": bool(summary.get("raw_refresh_ready")),
        "active_backfill_queue_count": int(summary.get("active_backfill_queue_count") or 0),
        "monitor_rows": rows,
        "private_metric_policy": {
            "public_outputs": policy.get("public_outputs", ""),
            "amount_display_until_ready": policy.get("amount_display_until_ready", "account-update-pending"),
            "credential_policy": policy.get("credential_policy", ""),
            "automation_boundary": policy.get("automation_boundary", ""),
        },
        "current_executable_new_stake_aud": 0,
    }


def app_status() -> dict:
    readiness = load_json(OUTPUT_DIR / "automation_readiness_latest.json")
    raw_health = load_json(OUTPUT_DIR / "raw_refresh_health_latest.json")
    partial_refresh = normalize_partial_research_refresh(raw_health.get("partial_research_refresh") or {})
    raw_access_policy = raw_health.get("access_policy") or public_raw_access_policy_runtime()
    raw_blocker_codes = list(raw_health.get("blocker_codes") or [])
    if not raw_health.get("ready") and raw_access_policy.get("blocker_code") not in raw_blocker_codes:
        raw_blocker_codes.append(raw_access_policy["blocker_code"])
    raw_next_action = raw_health.get("recommended_next_action", "")
    if not raw_health.get("ready"):
        raw_next_action = raw_access_policy.get("next_safe_action", raw_next_action)
    source_metadata = load_json(OUTPUT_DIR / "source_model_github_metadata_latest.json")
    provider_config_doctor = load_json(OUTPUT_DIR / "provider_config_doctor_latest.json")
    provider_config_summary = provider_config_doctor.get("summary") or {}
    provider_config_odds = provider_config_doctor.get("the_odds_api") or {}
    provider_config_optic = provider_config_doctor.get("opticodds") or {}
    provider_kpi = load_json(OUTPUT_DIR / "provider_kpi_latest.json")
    provider_kpi_summary = provider_kpi.get("summary") or {}
    provider_kpi_executive = provider_kpi.get("executive_status") or {}
    provider_blocked = load_json(OUTPUT_DIR / "odds_provider_blocked_latest.json")
    provider_alternate_plan = load_json(OUTPUT_DIR / "provider_alternate_plan_latest.json")
    provider_alternate_credit = provider_alternate_plan.get("credit_policy") or {}
    provider_alternate_evidence = provider_alternate_plan.get("event_probe_evidence") or {}
    public_snapshot_import = load_json(OUTPUT_DIR / "public_snapshot_import_status_latest.json")
    public_snapshot_publish_preflight = load_json(OUTPUT_DIR / "public_snapshot_import_publish_preflight_latest.json")
    public_snapshot_raw_publish = load_json(OUTPUT_DIR / "public_snapshot_raw_publish_latest.json")
    provider_fallback_verification = load_json(OUTPUT_DIR / "provider_fallback_verification_latest.json")
    provider_manual_verification = load_json(OUTPUT_DIR / "provider_manual_verification_status_latest.json")
    provider_manual_completion = provider_manual_verification.get("completion") or {}
    provider_manual_hash_gate = load_json(OUTPUT_DIR / "provider_manual_hash_gate_latest.json")
    provider_manual_hash_completion = provider_manual_hash_gate.get("completion") or {}
    provider_manual_overlay_preview = load_json(OUTPUT_DIR / "provider_manual_overlay_preview_latest.json")
    provider_manual_overlay_completion = provider_manual_overlay_preview.get("completion") or {}
    provider_manual_overlay_publish_preflight = load_json(OUTPUT_DIR / "provider_manual_overlay_publish_preflight_latest.json")
    provider_manual_overlay_publish = load_json(OUTPUT_DIR / "provider_manual_overlay_publish_latest.json")
    provider_manual_workbench = load_json(OUTPUT_DIR / "provider_manual_workbench_latest.json")
    provider_manual_pair_templates = provider_manual_workbench.get("pair_templates") or {}
    provider_manual_operator_cockpit = provider_manual_workbench.get("operator_cockpit") or {}
    position_monitor = load_json(OUTPUT_DIR / "position_monitor_latest.json")
    report_date = current_report_date()
    bootstrap = current_private_position_bootstrap(readiness, report_date)
    private_preflight = bootstrap.get("preflight") or {}
    private_position_status = {
        "ready": bool(bootstrap.get("ready")),
        "status": bootstrap.get("status", ""),
        "report_date": bootstrap.get("report_date", ""),
        "profile_exists": bool((bootstrap.get("profile") or {}).get("exists")),
        "raw_text_exists": bool((bootstrap.get("files") or {}).get("raw_text_exists")),
        "snapshot_exists": bool((bootstrap.get("files") or {}).get("snapshot_exists")),
        "diagnostics_exists": bool((bootstrap.get("files") or {}).get("diagnostics_exists")),
        "preflight": private_preflight,
        "blocking_reason": private_preflight.get("blocking_reason", ""),
        "next_safe_action": private_preflight.get("next_safe_action", ""),
        "login_window_required": bool(private_preflight.get("login_window_required")),
        "manual_step_required": bool(private_preflight.get("manual_step_required")),
        "wait_for_login_seconds": private_preflight.get("wait_for_login_seconds", 600),
        "capture_mode": private_preflight.get("capture_mode", ""),
        "credential_policy": private_preflight.get("credential_policy", ""),
            "automation_boundary": private_preflight.get("automation_boundary", ""),
    }
    position_monitor_status = position_monitor_status_payload(
        position_monitor=position_monitor,
        private_position=private_position_status,
        report_date=report_date,
    )
    provider_command_center = provider_command_center_payload(
        provider_config_doctor=provider_config_doctor,
        provider_kpi=provider_kpi,
        provider_alternate_plan=provider_alternate_plan,
        provider_manual_workbench=provider_manual_workbench,
    )
    provider_alternate_workbench = provider_alternate_workbench_payload(
        provider_kpi=provider_kpi,
        provider_alternate_plan=provider_alternate_plan,
        provider_command_center=provider_command_center,
    )
    automation_work_queue = automation_work_queue_payload(
        provider_command_center=provider_command_center,
        provider_config_doctor=provider_config_doctor,
        provider_fallback_verification=provider_fallback_verification,
        provider_manual_overlay_publish_preflight=provider_manual_overlay_publish_preflight,
        provider_manual_overlay_publish=provider_manual_overlay_publish,
        readiness=readiness,
        raw_health=raw_health,
        private_position=position_monitor_status,
    )
    automation_scorecard = automation_scorecard_payload(
        provider_config_doctor=provider_config_doctor,
        provider_command_center=provider_command_center,
        provider_alternate_workbench=provider_alternate_workbench,
        automation_work_queue=automation_work_queue,
        position_monitor_status=position_monitor_status,
        raw_health=raw_health,
    )
    operation_panel = operation_panel_payload(
        automation_scorecard=automation_scorecard,
        automation_work_queue=automation_work_queue,
        provider_command_center=provider_command_center,
        provider_alternate_workbench=provider_alternate_workbench,
        position_monitor_status=position_monitor_status,
        raw_health=raw_health,
        provider_kpi=provider_kpi,
        report_date=report_date,
    )
    return {
        "ok": True,
        "entry": ENTRY_HTML.exists(),
        "current_report_date": report_date,
        "interaction_mode": {
            "primary": "web",
            "web_primary": True,
            "current_surface": "local_web_app",
            "primary_entry": LOCAL_WEB_APP_URL,
            "static_html_role": "read_only_preview",
            "runtime_controls_enabled": True,
            "forbidden_actions": ["auto_betting", "odds_click", "ticket_mutation"],
        },
        "private_position": private_position_status,
        "position_monitor": position_monitor_status,
        "raw_refresh": {
            "ready": bool(raw_health.get("ready")),
            "status": raw_health.get("status", ""),
            "ready_required_target_count": raw_health.get("ready_required_target_count", ""),
            "blocker_codes": raw_blocker_codes,
            "recommended_next_action": raw_next_action,
            "access_policy": raw_access_policy,
            "partial_research_refresh": {
                "status": partial_refresh.get("status", "not_attempted"),
                "freshness_status": partial_refresh.get("freshness_status", "missing"),
                "fresh_within_sla": bool(partial_refresh.get("fresh_within_sla")),
                "current_research_only_allowed": bool(partial_refresh.get("current_research_only_allowed")),
                "historical_research_evidence_available": bool(partial_refresh.get("historical_research_evidence_available")),
                "age_hours": partial_refresh.get("age_hours"),
                "freshness_sla_hours": partial_refresh.get("freshness_sla_hours"),
                "successful_board_count": int(partial_refresh.get("successful_board_count") or 0),
                "attempted_board_count": int(partial_refresh.get("attempted_board_count") or 0),
            },
        },
        "partial_daily_research": partial_daily_research_status(OUTPUT_DIR),
        "provider_config_doctor": {
            "ready": bool(provider_config_doctor),
            "status": provider_config_doctor.get("status", "missing"),
            "local_env_exists": bool((provider_config_doctor.get("local_env") or {}).get("exists")),
            "the_odds_api_key_present": bool(provider_config_odds.get("api_key_present")),
            "opticodds_key_present": bool(provider_config_optic.get("api_key_present")),
            "sports_discovery_enabled": bool(provider_config_odds.get("sports_discovery_enabled")),
            "requested_sports": provider_config_odds.get("requested_sports", []),
            "recommended_sports": provider_config_odds.get("recommended_sports", []),
            "known_invalid_or_legacy_sports": provider_config_odds.get("known_invalid_or_legacy_sports", []),
            "issue_count": int(provider_config_summary.get("issue_count") or 0),
            "legacy_sport_count": int(provider_config_summary.get("legacy_sport_count") or 0),
            "event_market_probe_limit": provider_config_odds.get("event_market_probe_limit", 0),
            "recommended_env_patch": provider_config_doctor.get("recommended_env_patch") or {},
            "next_safe_action": provider_config_summary.get("next_safe_action", ""),
            "current_executable_new_stake_aud": provider_config_doctor.get("current_executable_new_stake_aud", 0),
        },
        "provider_kpi": {
            "ready": bool(provider_kpi.get("provider_analysis_ready")),
            "status": provider_kpi_executive.get("status", "missing"),
            "overall_progress_pct": provider_kpi_executive.get("overall_progress_pct"),
            "refresh_id": provider_kpi.get("refresh_id", ""),
            "event_count": provider_kpi_summary.get("event_count", 0),
            "covered_market_family_count": provider_kpi_summary.get("covered_market_family_count", 0),
            "formal_publish_allowed": bool(provider_kpi.get("formal_publish_allowed")),
            "full_automation_allowed": bool(provider_kpi.get("full_automation_allowed")),
            "current_executable_new_stake_aud": provider_kpi.get("current_executable_new_stake_aud", 0),
            "primary_gap": provider_kpi_executive.get("primary_gap", ""),
            "recommended_next_action": provider_kpi_executive.get("recommended_next_action", ""),
            "last_blocked_attempt": provider_kpi.get("last_blocked_attempt") or {},
        },
        "provider_blocked": {
            "ready": bool(provider_blocked),
            "provider": provider_blocked.get("provider", ""),
            "refresh_id": provider_blocked.get("refresh_id", ""),
            "blocker_code": provider_blocked.get("blocker_code", ""),
            "last_good_coverage_preserved": bool(provider_blocked.get("last_good_coverage_preserved")),
            "next_safe_action": provider_blocked.get("next_safe_action", ""),
        },
        "provider_command_center": provider_command_center,
        "provider_alternate_workbench": provider_alternate_workbench,
        "automation_work_queue": automation_work_queue,
        "automation_scorecard": automation_scorecard,
        "operation_panel": operation_panel,
        "provider_alternate_plan": {
            "ready": provider_alternate_plan.get("status") in {"ready", "in_progress", "fallback_required"},
            "status": provider_alternate_plan.get("status", "missing"),
            "refresh_id": provider_alternate_plan.get("refresh_id", ""),
            "probe_queue_count": provider_alternate_plan.get("probe_queue_count", 0),
            "fallback_queue_count": provider_alternate_plan.get("fallback_queue_count", 0),
            "recommended_batch_size": provider_alternate_credit.get("recommended_batch_size", 0),
            "estimated_next_batch_credit_floor": provider_alternate_credit.get("estimated_next_batch_credit_floor"),
            "estimated_next_batch_credit_ceiling": provider_alternate_credit.get("estimated_next_batch_credit_ceiling"),
            "recommended_command": provider_alternate_plan.get("recommended_command", ""),
            "recommended_next_action": provider_alternate_plan.get("recommended_next_action", ""),
            "operational_decision": provider_alternate_plan.get("operational_decision") or {},
            "event_probe_evidence": {
                "market_probe_count": provider_alternate_evidence.get("market_probe_count", 0),
                "event_odds_count": provider_alternate_evidence.get("event_odds_count", 0),
                "team_total_available_probe_count": provider_alternate_evidence.get("team_total_available_probe_count", 0),
                "total_available_probe_count": provider_alternate_evidence.get("total_available_probe_count", 0),
                "canonical_available_market_counts": provider_alternate_evidence.get("canonical_available_market_counts", {}),
            },
            "market_family_gaps": provider_alternate_plan.get("market_family_gaps", []),
            "current_executable_new_stake_aud": provider_alternate_plan.get("current_executable_new_stake_aud", 0),
        },
        "public_snapshot_import": {
            "ready": bool(public_snapshot_import),
            "status": public_snapshot_import.get("status", "missing"),
            "board_id": public_snapshot_import.get("board_id", ""),
            "import_dir_relative_path": public_snapshot_import.get("import_dir_relative_path", ""),
            "selected_snapshot_file": public_snapshot_import.get("selected_snapshot_file", ""),
            "selected_snapshot_sha256": public_snapshot_import.get("selected_snapshot_sha256", ""),
            "preview_raw_snapshot": public_snapshot_import.get("preview_raw_snapshot", ""),
            "preview_raw_sha256": public_snapshot_import.get("preview_raw_sha256", ""),
            "match_count": public_snapshot_import.get("match_count", 0),
            "covered_market_family_count": public_snapshot_import.get("covered_market_family_count", 0),
            "market_coverage": public_snapshot_import.get("market_coverage", {}),
            "issue_count": len(public_snapshot_import.get("issues") or []),
            "snapshot_import_preview_ready": bool(public_snapshot_import.get("snapshot_import_preview_ready")),
            "formal_publish_allowed": bool(public_snapshot_import.get("formal_publish_allowed")),
            "full_automation_allowed": bool(public_snapshot_import.get("full_automation_allowed")),
            "current_executable_new_stake_aud": public_snapshot_import.get("current_executable_new_stake_aud", 0),
            "recommended_next_action": public_snapshot_import.get("recommended_next_action", ""),
        },
        "public_snapshot_publish_preflight": {
            "ready": bool(public_snapshot_publish_preflight),
            "status": public_snapshot_publish_preflight.get("status", "missing"),
            "board_id": public_snapshot_publish_preflight.get("board_id", ""),
            "approval_relative_path": public_snapshot_publish_preflight.get("approval_relative_path", ""),
            "approval_file_sha256": public_snapshot_publish_preflight.get("approval_file_sha256", ""),
            "selected_snapshot_file": public_snapshot_publish_preflight.get("selected_snapshot_file", ""),
            "selected_snapshot_sha256": public_snapshot_publish_preflight.get("selected_snapshot_sha256", ""),
            "preview_raw_snapshot": public_snapshot_publish_preflight.get("preview_raw_snapshot", ""),
            "preview_raw_sha256": public_snapshot_publish_preflight.get("preview_raw_sha256", ""),
            "match_count": public_snapshot_publish_preflight.get("match_count", 0),
            "approved_by_user": bool(public_snapshot_publish_preflight.get("approved_by_user")),
            "snapshot_publish_preflight_passed": bool(
                public_snapshot_publish_preflight.get("snapshot_publish_preflight_passed")
            ),
            "publish_compatible_with_snapshot_preview": bool(
                public_snapshot_publish_preflight.get("publish_compatible_with_snapshot_preview")
            ),
            "issue_count": len(public_snapshot_publish_preflight.get("issues") or []),
            "formal_publish_allowed": bool(public_snapshot_publish_preflight.get("formal_publish_allowed")),
            "full_automation_allowed": bool(public_snapshot_publish_preflight.get("full_automation_allowed")),
            "current_executable_new_stake_aud": public_snapshot_publish_preflight.get(
                "current_executable_new_stake_aud", 0
            ),
            "next_safe_action": public_snapshot_publish_preflight.get("next_safe_action", ""),
        },
        "public_snapshot_raw_publish": {
            "ready": bool(public_snapshot_raw_publish),
            "ok": bool(public_snapshot_raw_publish.get("ok")),
            "status": public_snapshot_raw_publish.get("status", "missing"),
            "board_id": public_snapshot_raw_publish.get("board_id", ""),
            "refresh_id": public_snapshot_raw_publish.get("refresh_id", ""),
            "selected_snapshot_file": public_snapshot_raw_publish.get("selected_snapshot_file", ""),
            "selected_snapshot_sha256": public_snapshot_raw_publish.get("selected_snapshot_sha256", ""),
            "preview_raw_snapshot": public_snapshot_raw_publish.get("preview_raw_snapshot", ""),
            "preview_raw_sha256": public_snapshot_raw_publish.get("preview_raw_sha256", ""),
            "approval_relative_path": public_snapshot_raw_publish.get("approval_relative_path", ""),
            "approval_file_sha256": public_snapshot_raw_publish.get("approval_file_sha256", ""),
            "published_raw_snapshot": public_snapshot_raw_publish.get("published_raw_snapshot", ""),
            "published_raw_sha256": public_snapshot_raw_publish.get("published_raw_sha256", ""),
            "formal_raw_publish_performed": bool(public_snapshot_raw_publish.get("formal_raw_publish_performed")),
            "full_automation_allowed": bool(public_snapshot_raw_publish.get("full_automation_allowed")),
            "raw_batch_manifest_written": bool(public_snapshot_raw_publish.get("raw_batch_manifest_written")),
            "raw_gate_ready": bool(public_snapshot_raw_publish.get("raw_gate_ready")),
            "issue_count": len(public_snapshot_raw_publish.get("issues") or []),
            "current_executable_new_stake_aud": public_snapshot_raw_publish.get("current_executable_new_stake_aud", 0),
            "next_safe_action": public_snapshot_raw_publish.get("next_safe_action", ""),
        },
        "provider_fallback_verification": {
            "ready": bool(provider_fallback_verification),
            "status": provider_fallback_verification.get("status", "missing"),
            "refresh_id": provider_fallback_verification.get("refresh_id", ""),
            "queue_count": provider_fallback_verification.get("queue_count", 0),
            "top_priority_count": provider_fallback_verification.get("top_priority_count", 0),
            "provider_blocker_code": provider_fallback_verification.get("provider_blocker_code", ""),
            "recommended_next_action": provider_fallback_verification.get("recommended_next_action", ""),
            "current_executable_new_stake_aud": provider_fallback_verification.get("current_executable_new_stake_aud", 0),
        },
        "provider_manual_verification": {
            "ready": bool(provider_manual_verification),
            "status": provider_manual_verification.get("status", "missing"),
            "refresh_id": provider_manual_verification.get("refresh_id", ""),
            "import_file": provider_manual_verification.get("import_file", ""),
            "import_relative_path": provider_manual_verification.get("import_relative_path", ""),
            "complete_event_count": provider_manual_completion.get("complete_event_count", 0),
            "queue_count": provider_manual_completion.get("queue_count", provider_manual_verification.get("queue_count", 0)),
            "high_priority_complete_count": provider_manual_completion.get("high_priority_complete_count", 0),
            "high_priority_count": provider_manual_completion.get("high_priority_count", provider_manual_verification.get("high_priority_count", 0)),
            "invalid_row_count": provider_manual_completion.get("invalid_row_count", 0),
            "recommended_next_action": provider_manual_verification.get("recommended_next_action", ""),
            "current_executable_new_stake_aud": provider_manual_verification.get("current_executable_new_stake_aud", 0),
        },
        "provider_manual_hash_gate": {
            "ready": bool(provider_manual_hash_gate),
            "status": provider_manual_hash_gate.get("status", "missing"),
            "refresh_id": provider_manual_hash_gate.get("refresh_id", ""),
            "manual_import_sha256": provider_manual_hash_gate.get("manual_import_sha256", ""),
            "import_file_sha256": provider_manual_hash_gate.get("import_file_sha256", ""),
            "complete_event_count": provider_manual_hash_completion.get("complete_event_count", 0),
            "queue_count": provider_manual_hash_completion.get("queue_count", 0),
            "ready_for_manual_signature": bool(provider_manual_hash_gate.get("ready_for_manual_signature")),
            "approved_by_user": bool((provider_manual_hash_gate.get("provider_tab_final_verification_draft") or {}).get("approved_by_user")),
            "publish_compatible_with_provider_raw": bool((provider_manual_hash_gate.get("provider_tab_final_verification_draft") or {}).get("publish_compatible_with_provider_raw")),
            "recommended_next_action": provider_manual_hash_gate.get("recommended_next_action", ""),
            "current_executable_new_stake_aud": provider_manual_hash_gate.get("current_executable_new_stake_aud", 0),
        },
        "provider_manual_overlay_preview": {
            "ready": bool(provider_manual_overlay_preview),
            "status": provider_manual_overlay_preview.get("status", "missing"),
            "refresh_id": provider_manual_overlay_preview.get("refresh_id", ""),
            "overlay_event_count": provider_manual_overlay_preview.get("overlay_event_count", 0),
            "overlay_row_count": provider_manual_overlay_preview.get("overlay_row_count", 0),
            "queue_count": provider_manual_overlay_completion.get("queue_count", 0),
            "high_priority_complete_count": provider_manual_overlay_completion.get("high_priority_complete_count", 0),
            "high_priority_count": provider_manual_overlay_completion.get("high_priority_count", 0),
            "overlay_raw_snapshot": provider_manual_overlay_preview.get("overlay_raw_snapshot", ""),
            "overlay_raw_sha256": provider_manual_overlay_preview.get("overlay_raw_sha256", ""),
            "ready_for_publish_preflight": bool(provider_manual_overlay_preview.get("ready_for_publish_preflight")),
            "approved_by_user": bool(
                (provider_manual_overlay_preview.get("provider_tab_final_verification_overlay_draft") or {}).get("approved_by_user")
            ),
            "publish_compatible_with_provider_raw": bool(
                (provider_manual_overlay_preview.get("provider_tab_final_verification_overlay_draft") or {}).get(
                    "publish_compatible_with_provider_raw"
                )
            ),
            "formal_publish_allowed": bool(provider_manual_overlay_preview.get("formal_publish_allowed")),
            "recommended_next_action": provider_manual_overlay_preview.get("recommended_next_action", ""),
            "current_executable_new_stake_aud": provider_manual_overlay_preview.get("current_executable_new_stake_aud", 0),
        },
        "provider_manual_overlay_publish_preflight": {
            "ready": bool(provider_manual_overlay_publish_preflight),
            "status": provider_manual_overlay_publish_preflight.get("status", "missing"),
            "refresh_id": provider_manual_overlay_publish_preflight.get("refresh_id", ""),
            "approval_relative_path": provider_manual_overlay_publish_preflight.get("approval_relative_path", ""),
            "approval_file_sha256": provider_manual_overlay_publish_preflight.get("approval_file_sha256", ""),
            "overlay_raw_sha256": provider_manual_overlay_publish_preflight.get("overlay_raw_sha256", ""),
            "overlay_event_count": provider_manual_overlay_publish_preflight.get("overlay_event_count", 0),
            "approved_by_user": bool(provider_manual_overlay_publish_preflight.get("approved_by_user")),
            "overlay_publish_preflight_passed": bool(
                provider_manual_overlay_publish_preflight.get("overlay_publish_preflight_passed")
            ),
            "publish_compatible_with_provider_raw": bool(
                provider_manual_overlay_publish_preflight.get("publish_compatible_with_provider_raw")
            ),
            "issue_count": len(provider_manual_overlay_publish_preflight.get("issues") or []),
            "formal_publish_allowed": bool(provider_manual_overlay_publish_preflight.get("formal_publish_allowed")),
            "next_safe_action": provider_manual_overlay_publish_preflight.get("next_safe_action", ""),
            "current_executable_new_stake_aud": provider_manual_overlay_publish_preflight.get("current_executable_new_stake_aud", 0),
        },
        "provider_manual_overlay_publish": {
            "ready": bool(provider_manual_overlay_publish),
            "ok": bool(provider_manual_overlay_publish.get("ok")),
            "status": provider_manual_overlay_publish.get("status", "missing"),
            "board_id": provider_manual_overlay_publish.get("board_id", ""),
            "market_family": provider_manual_overlay_publish.get("market_family", ""),
            "refresh_id": provider_manual_overlay_publish.get("refresh_id", ""),
            "provider_refresh_id": provider_manual_overlay_publish.get("provider_refresh_id", ""),
            "manual_import_sha256": provider_manual_overlay_publish.get("manual_import_sha256", ""),
            "overlay_raw_snapshot": provider_manual_overlay_publish.get("overlay_raw_snapshot", ""),
            "overlay_raw_sha256": provider_manual_overlay_publish.get("overlay_raw_sha256", ""),
            "overlay_event_count": provider_manual_overlay_publish.get("overlay_event_count", 0),
            "overlay_row_count": provider_manual_overlay_publish.get("overlay_row_count", 0),
            "approval_relative_path": provider_manual_overlay_publish.get("approval_relative_path", ""),
            "approval_file_sha256": provider_manual_overlay_publish.get("approval_file_sha256", ""),
            "published_raw_snapshot": provider_manual_overlay_publish.get("published_raw_snapshot", ""),
            "published_raw_sha256": provider_manual_overlay_publish.get("published_raw_sha256", ""),
            "formal_raw_publish_performed": bool(provider_manual_overlay_publish.get("formal_raw_publish_performed")),
            "full_automation_allowed": bool(provider_manual_overlay_publish.get("full_automation_allowed")),
            "raw_batch_manifest_written": bool(provider_manual_overlay_publish.get("raw_batch_manifest_written")),
            "raw_gate_ready": bool(provider_manual_overlay_publish.get("raw_gate_ready")),
            "issue_count": len(provider_manual_overlay_publish.get("issues") or []),
            "current_executable_new_stake_aud": provider_manual_overlay_publish.get("current_executable_new_stake_aud", 0),
            "next_safe_action": provider_manual_overlay_publish.get("next_safe_action", ""),
        },
        "provider_manual_workbench": {
            "ready": bool(provider_manual_workbench),
            "status": provider_manual_workbench.get("status", "missing"),
            "refresh_id": provider_manual_workbench.get("refresh_id", ""),
            "batch_size": provider_manual_workbench.get("batch_size", 0),
            "batch_count": provider_manual_workbench.get("batch_count", 0),
            "queue_count": provider_manual_workbench.get("queue_count", 0),
            "remaining_event_count": provider_manual_workbench.get("remaining_event_count", 0),
            "remaining_high_priority_count": provider_manual_workbench.get("remaining_high_priority_count", 0),
            "verified_event_count": provider_manual_workbench.get("verified_event_count", 0),
            "partial_event_count": provider_manual_workbench.get("partial_event_count", 0),
            "invalid_row_count": provider_manual_workbench.get("invalid_row_count", 0),
            "next_batch_id": (provider_manual_workbench.get("next_batch") or {}).get("batch_id", ""),
            "next_batch_event_count": (provider_manual_workbench.get("next_batch") or {}).get("event_count", 0),
            "all_pair_template_csv": provider_manual_pair_templates.get("all_candidates_csv", ""),
            "next_batch_pair_template_csv": provider_manual_pair_templates.get("next_batch_csv", ""),
            "all_candidate_pair_rows": provider_manual_pair_templates.get("all_candidate_pair_rows", 0),
            "next_batch_pair_rows": provider_manual_pair_templates.get("next_batch_pair_rows", 0),
            "gate_snapshot": provider_manual_workbench.get("gate_snapshot") or {},
            "operator_cockpit": provider_manual_operator_cockpit,
            "import_quality": provider_manual_workbench.get("import_quality") or {},
            "next_batch_summary": provider_manual_workbench.get("next_batch_summary") or {},
            "next_batch_quality": provider_manual_workbench.get("next_batch_quality") or {},
            "quality_gate_summary": provider_manual_workbench.get("quality_gate_summary") or {},
            "field_checklist": provider_manual_workbench.get("field_checklist") or [],
            "workflow_steps": provider_manual_workbench.get("workflow_steps") or [],
            "action_contract": provider_manual_workbench.get("action_contract") or {},
            "manual_intake_contract": provider_manual_workbench.get("manual_intake_contract") or {},
            "publish_status": provider_manual_operator_cockpit.get("publish_status", ""),
            "can_publish_now": bool(provider_manual_operator_cockpit.get("can_publish_now")),
            "formal_publish_allowed": bool(provider_manual_workbench.get("formal_publish_allowed")),
            "full_automation_allowed": bool(provider_manual_workbench.get("full_automation_allowed")),
            "current_executable_new_stake_aud": provider_manual_workbench.get("current_executable_new_stake_aud", 0),
            "recommended_next_action": provider_manual_workbench.get("recommended_next_action", ""),
        },
        "source_model_metadata": {
            "ready": source_metadata.get("status") == "ready",
            "status": source_metadata.get("status", "missing"),
            "generated_at": source_metadata.get("generated_at", ""),
            "freshness_status": source_metadata.get("freshness_status", "missing"),
            "freshness_sla_hours": source_metadata.get("freshness_sla_hours", 4),
            "source_count": source_metadata.get("source_count", 0),
            "fetched_count": source_metadata.get("fetched_count", 0),
            "failed_count": source_metadata.get("failed_count", 0),
            "stars_total": source_metadata.get("stars_total", 0),
            "open_issues_total": source_metadata.get("open_issues_total", 0),
        },
        "runners": {
            "active_backfill": process_running(BACKFILL_PID_PATH),
            "private_bootstrap": process_running(PRIVATE_BOOTSTRAP_PID_PATH),
            "daily_rerun": process_running(DAILY_RERUN_PID_PATH),
            "public_raw_refresh": process_running(PUBLIC_RAW_REFRESH_PID_PATH),
            "live_board_discovery": process_running(LIVE_DISCOVERY_PID_PATH),
            "source_model_metadata_refresh": process_running(SOURCE_METADATA_PID_PATH),
        },
    }


def current_private_position_bootstrap(readiness: dict, report_date: str) -> dict:
    bootstrap = readiness.get("private_position_bootstrap") or {}
    if str(bootstrap.get("report_date") or "") == str(report_date) and isinstance(bootstrap.get("preflight"), dict):
        return bootstrap
    return build_private_position_bootstrap_status(private_dir_for_output(OUTPUT_DIR), report_date)


def refresh_download_assets() -> None:
    try:
        env = os.environ.copy()
        env["TAB_FIFA_FAST_ENTRY_REBUILD"] = "1"
        subprocess.run(
            [sys.executable, "scripts/build_downloads_app_entry.py"],
            cwd=PIPELINE_ROOT,
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=15,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return


def main() -> None:
    args = parse_args()
    os.chdir(PIPELINE_ROOT)
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    server.serve_forever()


if __name__ == "__main__":
    main()
