#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import socket
import struct
import subprocess
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


DEFAULT_PAGES = [
    "index.html",
    "operations_center.html",
    "data_access_hub.html",
    "acceptance_workbench.html",
    "reference_model_lab.html",
    "dashboard.html",
    "behavior_analysis.html",
    "transaction_explorer.html",
    "tag_library.html",
    "review/review_workbench.html",
]
DEFAULT_VIEWPORTS = [
    {"name": "desktop", "width": 1440, "height": 1000},
    {"name": "mobile", "width": 390, "height": 844},
]
REQUIRED_TEXT = {
    "index.html": ["经济放血", "报告", "Dashboard"],
    "operations_center.html": ["运行控制台", "浏览器验收", "交付打包"],
    "data_access_hub.html": ["数据接入与回测入口", "PFIOS", "只读 API"],
    "acceptance_workbench.html": ["用户验收工作台", "验收选择矩阵", "ChatGPT"],
    "reference_model_lab.html": ["开源参考模型工作台", "GitHub", "吸收度"],
    "dashboard.html": ["现金流", "风险", "分类"],
    "behavior_analysis.html": ["交易行为分析", "标签", "图表"],
    "transaction_explorer.html": ["交易", "搜索", "筛选"],
    "tag_library.html": ["标签库编辑", "保存", "筛选"],
    "review/review_workbench.html": ["复核", "下拉", "候选"],
}


class CdpWebSocket:
    def __init__(self, url: str) -> None:
        parsed = urllib.parse.urlparse(url)
        self.host = parsed.hostname or "127.0.0.1"
        self.port = parsed.port or 80
        self.path = parsed.path + (("?" + parsed.query) if parsed.query else "")
        self.sock = socket.create_connection((self.host, self.port), timeout=10)
        self.next_id = 1
        self._handshake()

    def _handshake(self) -> None:
        key = base64.b64encode(os.urandom(16)).decode("ascii")
        request = (
            f"GET {self.path} HTTP/1.1\r\n"
            f"Host: {self.host}:{self.port}\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {key}\r\n"
            "Sec-WebSocket-Version: 13\r\n\r\n"
        )
        self.sock.sendall(request.encode("ascii"))
        response = b""
        while b"\r\n\r\n" not in response:
            chunk = self.sock.recv(4096)
            if not chunk:
                break
            response += chunk
        if b" 101 " not in response.split(b"\r\n", 1)[0]:
            raise RuntimeError(f"CDP websocket handshake failed: {response[:200]!r}")

    def close(self) -> None:
        try:
            self.sock.close()
        except OSError:
            pass

    def send(self, method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        message_id = self.next_id
        self.next_id += 1
        self._send_frame(json.dumps({"id": message_id, "method": method, "params": params or {}}).encode("utf-8"))
        deadline = time.time() + 20
        while time.time() < deadline:
            payload = self._recv_frame()
            if not payload:
                continue
            message = json.loads(payload.decode("utf-8"))
            if message.get("id") == message_id:
                if "error" in message:
                    raise RuntimeError(f"CDP error for {method}: {message['error']}")
                return message.get("result", {})
        raise TimeoutError(f"CDP response timeout for {method}")

    def wait_for_event(self, method: str, timeout: float = 10) -> dict[str, Any] | None:
        deadline = time.time() + timeout
        while time.time() < deadline:
            payload = self._recv_frame()
            if not payload:
                continue
            message = json.loads(payload.decode("utf-8"))
            if message.get("method") == method:
                return message
        return None

    def _send_frame(self, payload: bytes) -> None:
        mask = os.urandom(4)
        header = bytearray([0x81])
        length = len(payload)
        if length < 126:
            header.append(0x80 | length)
        elif length < 65536:
            header.append(0x80 | 126)
            header.extend(struct.pack("!H", length))
        else:
            header.append(0x80 | 127)
            header.extend(struct.pack("!Q", length))
        masked = bytes(byte ^ mask[index % 4] for index, byte in enumerate(payload))
        self.sock.sendall(bytes(header) + mask + masked)

    def _recv_frame(self) -> bytes:
        first = self._read_exact(2)
        if not first:
            return b""
        opcode = first[0] & 0x0F
        masked = first[1] & 0x80
        length = first[1] & 0x7F
        if length == 126:
            length = struct.unpack("!H", self._read_exact(2))[0]
        elif length == 127:
            length = struct.unpack("!Q", self._read_exact(8))[0]
        mask = self._read_exact(4) if masked else b""
        payload = self._read_exact(length)
        if masked:
            payload = bytes(byte ^ mask[index % 4] for index, byte in enumerate(payload))
        if opcode == 8:
            return b""
        if opcode == 9:
            self._send_pong(payload)
            return b""
        return payload

    def _send_pong(self, payload: bytes) -> None:
        header = bytearray([0x8A])
        header.append(len(payload))
        self.sock.sendall(bytes(header) + payload)

    def _read_exact(self, length: int) -> bytes:
        chunks = bytearray()
        while len(chunks) < length:
            chunk = self.sock.recv(length - len(chunks))
            if not chunk:
                raise ConnectionError("CDP websocket closed")
            chunks.extend(chunk)
        return bytes(chunks)


def find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def wait_for_json(url: str, timeout: float = 10) -> Any:
    deadline = time.time() + timeout
    last_error: Exception | None = None
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as response:
                return json.loads(response.read().decode("utf-8"))
        except Exception as exc:  # pragma: no cover - depends on local Chrome startup timing
            last_error = exc
            time.sleep(0.2)
    raise TimeoutError(f"Timed out waiting for {url}: {last_error}")


def start_chrome(chrome_path: str, port: int, profile_dir: Path) -> subprocess.Popen[bytes]:
    cmd = [
        chrome_path,
        "--headless=new",
        "--disable-gpu",
        "--no-sandbox",
        "--disable-dev-shm-usage",
        "--disable-background-networking",
        "--disable-component-update",
        "--disable-extensions",
        "--disable-sync",
        "--no-first-run",
        "--no-default-browser-check",
        "--remote-allow-origins=*",
        f"--remote-debugging-port={port}",
        f"--user-data-dir={profile_dir}",
        "about:blank",
    ]
    return subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def create_tab(port: int, url: str) -> str:
    encoded = urllib.parse.quote(url, safe=":/?&=#")
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/json/new?{encoded}", timeout=5) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError:
        request = urllib.request.Request(f"http://127.0.0.1:{port}/json/new?{encoded}", method="PUT")
        with urllib.request.urlopen(request, timeout=5) as response:
            payload = json.loads(response.read().decode("utf-8"))
    return str(payload["webSocketDebuggerUrl"])


def first_page_ws_url(port: int) -> str:
    with urllib.request.urlopen(f"http://127.0.0.1:{port}/json/list", timeout=5) as response:
        payload = json.loads(response.read().decode("utf-8"))
    for item in payload:
        if item.get("type") == "page" and item.get("webSocketDebuggerUrl"):
            return str(item["webSocketDebuggerUrl"])
    raise RuntimeError("No CDP page target is available")


def evaluate_page(ws: CdpWebSocket, page_name: str) -> dict[str, Any]:
    required = REQUIRED_TEXT.get(page_name, [])
    expression = f"""
(() => {{
  const required = {json.dumps(required, ensure_ascii=False)};
  const text = document.body ? document.body.innerText : "";
  const markerOk = required.length === 0 || required.some(item => text.includes(item));
  const chartNodes = Array.from(document.querySelectorAll("svg,canvas,.chart,.svg-chart,.donut-chart,.radar-chart"));
  const badChartBoxes = chartNodes.map(node => {{
    const rect = node.getBoundingClientRect();
    return {{ tag: node.tagName, id: node.id || "", width: Math.round(rect.width), height: Math.round(rect.height) }};
  }}).filter(item => item.width < 20 || item.height < 20);
  const root = document.documentElement;
  const style = getComputedStyle(document.body);
  return {{
    title: document.title,
    text_length: text.trim().length,
    marker_ok: markerOk,
    body_bg: style.backgroundColor,
    body_color: style.color,
    body_scroll_width: document.body ? document.body.scrollWidth : 0,
    root_scroll_width: root.scrollWidth,
    inner_width: window.innerWidth,
    overflow_x: Math.max(0, root.scrollWidth - window.innerWidth),
    chart_count: chartNodes.length,
    bad_chart_boxes: badChartBoxes,
    form_control_count: document.querySelectorAll("button,input,select,textarea,a").length,
    table_count: document.querySelectorAll("table").length
  }};
}})()
"""
    result = ws.send("Runtime.evaluate", {"expression": expression, "returnByValue": True, "awaitPromise": True})
    return dict(result["result"].get("value") or {})


def visual_ok(page_name: str, row: dict[str, Any], viewport_name: str) -> bool:
    if not row.get("marker_ok"):
        return False
    if int(row.get("text_length") or 0) < 300:
        return False
    if viewport_name == "mobile" and int(row.get("overflow_x") or 0) > 8:
        return False
    if row.get("bad_chart_boxes"):
        return False
    if page_name in {"dashboard.html", "behavior_analysis.html", "reference_model_lab.html"} and int(row.get("chart_count") or 0) < 1:
        return False
    if page_name in {"transaction_explorer.html", "tag_library.html", "review/review_workbench.html", "operations_center.html", "acceptance_workbench.html", "reference_model_lab.html"} and int(row.get("form_control_count") or 0) < 5:
        return False
    return True


def run_acceptance(args: argparse.Namespace) -> dict[str, Any]:
    output_dir = Path(args.output_dir)
    audit_path = output_dir / "audit" / "browser_visual_acceptance.json"
    screenshot_dir = Path(args.screenshot_dir)
    screenshot_dir.mkdir(parents=True, exist_ok=True)
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    process: subprocess.Popen[bytes] | None = None
    port = 0
    try:
        startup_failures: list[dict[str, Any]] = []
        for attempt in range(1, args.chrome_startup_retries + 1):
            port = find_free_port()
            profile_dir = (
                Path(args.profile_dir)
                if args.profile_dir
                else Path("/tmp") / f"econ-bleed-browser-audit-{port}-{attempt}"
            )
            profile_dir.mkdir(parents=True, exist_ok=True)
            process = start_chrome(args.chrome, port, profile_dir)
            try:
                wait_for_json(f"http://127.0.0.1:{port}/json/version", timeout=args.startup_timeout)
                break
            except Exception as exc:
                startup_failures.append(
                    {
                        "attempt": attempt,
                        "port": port,
                        "reason": str(exc),
                        "chrome": chrome_process_detail(process),
                    }
                )
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                process = None
        if process is None:
            payload = {
                "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                "base_url": args.base_url,
                "browser": args.chrome,
                "checked_count": 0,
                "failure_count": 1,
                "failures": [{"page": "chrome_startup", "viewport": {}, "reason": "Chrome DevTools did not become ready", "attempts": startup_failures}],
                "results": [],
            }
            audit_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            return payload
        for viewport in DEFAULT_VIEWPORTS:
            for page_name in DEFAULT_PAGES:
                url = urllib.parse.urljoin(args.base_url.rstrip("/") + "/", page_name) + f"?v={int(time.time() * 1000)}"
                ws_url = first_page_ws_url(port)
                ws = CdpWebSocket(ws_url)
                row: dict[str, Any] = {"page": page_name, "viewport": viewport, "url": url}
                try:
                    ws.send("Page.enable")
                    ws.send("Runtime.enable")
                    ws.send(
                        "Emulation.setDeviceMetricsOverride",
                        {
                            "width": viewport["width"],
                            "height": viewport["height"],
                            "deviceScaleFactor": 1,
                            "mobile": viewport["name"] == "mobile",
                        },
                    )
                    ws.send("Page.navigate", {"url": url})
                    ws.wait_for_event("Page.loadEventFired", timeout=args.page_timeout)
                    time.sleep(args.settle_ms / 1000)
                    row.update(evaluate_page(ws, page_name))
                    row["visual_ok"] = visual_ok(page_name, row, str(viewport["name"]))
                    screenshot = ws.send("Page.captureScreenshot", {"format": "png", "captureBeyondViewport": False})
                    screenshot_name = f"{Path(page_name).stem}_{viewport['name']}.png"
                    screenshot_path = screenshot_dir / screenshot_name
                    screenshot_path.write_bytes(base64.b64decode(screenshot["data"]))
                    row["screenshot"] = str(screenshot_path)
                    if not row["visual_ok"]:
                        failures.append({"page": page_name, "viewport": viewport, "reason": "visual_ok is false", "checks": row})
                except Exception as exc:
                    row["marker_ok"] = False
                    row["visual_ok"] = False
                    row["error"] = str(exc)
                    failures.append({"page": page_name, "viewport": viewport, "reason": str(exc)})
                finally:
                    ws.close()
                results.append(row)
    finally:
        if process is not None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:  # pragma: no cover - depends on Chrome process state
                process.kill()
    payload = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "base_url": args.base_url,
        "browser": args.chrome,
        "acceptance_dimensions": [
            "marker_ok",
            "no_document_horizontal_overflow",
            "chart_geometry_nonblank",
            "visible_text_nonblank",
            "visual_ok",
        ],
        "checked_count": len(results),
        "failure_count": len(failures),
        "failures": failures,
        "results": results,
        "source_hash": hashlib.sha256(json.dumps(results, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest(),
    }
    audit_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def chrome_process_detail(process: subprocess.Popen[bytes]) -> dict[str, Any]:
    detail: dict[str, Any] = {"returncode": process.poll()}
    if process.poll() is not None:
        try:
            stdout, stderr = process.communicate(timeout=1)
        except Exception:
            stdout, stderr = b"", b""
        detail["stdout"] = stdout.decode("utf-8", errors="replace")[-3000:]
        detail["stderr"] = stderr.decode("utf-8", errors="replace")[-3000:]
    return detail


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run browser visual acceptance against the local economic bleed report pages.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8772/")
    parser.add_argument("--output-dir", default="outputs/finance_ledger_20220605_20260603")
    parser.add_argument("--screenshot-dir", default="work/browser_visual_acceptance/screenshots")
    parser.add_argument("--chrome", default="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
    parser.add_argument("--profile-dir", default="")
    parser.add_argument("--startup-timeout", type=float, default=10)
    parser.add_argument("--chrome-startup-retries", type=int, default=3)
    parser.add_argument("--page-timeout", type=float, default=12)
    parser.add_argument("--settle-ms", type=int, default=600)
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    payload = run_acceptance(args)
    summary = {
        "audit": str(Path(args.output_dir) / "audit" / "browser_visual_acceptance.json"),
        "checked_count": payload["checked_count"],
        "failure_count": payload["failure_count"],
        "generated_at": payload["generated_at"],
    }
    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print(f"browser_acceptance audit={summary['audit']} checked={summary['checked_count']} failures={summary['failure_count']}")
    return 0 if payload["failure_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
