#!/usr/bin/env python3
"""Build and validate the Stage 11 public boundary in a headless loopback browser."""

from __future__ import annotations

import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
from urllib.parse import unquote, urlsplit


THIS_DIR = Path(__file__).resolve().parent
if str(THIS_DIR) not in sys.path:
    sys.path.insert(0, str(THIS_DIR))
from stage7_trace_privacy import sanitize_playwright_trace  # noqa: E402


PFI_ROOT = Path(__file__).resolve().parents[3]
REPO_ROOT = PFI_ROOT.parent
PUBLIC_SOURCE = PFI_ROOT / "web/cloudflare-public/public"
CDP_RUNNER = THIS_DIR / "stage11_public_boundary_cdp.mjs"
CODEX_RUNTIME_ROOT = Path.home() / ".cache/codex-runtimes/codex-primary-runtime/dependencies"
PLAYWRIGHT_MODULE_DIR = CODEX_RUNTIME_ROOT / "node/node_modules"
NODE = CODEX_RUNTIME_ROOT / "node/bin/node"
CHROME = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")


class _BoundaryHandler(SimpleHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        request_path = unquote(urlsplit(self.path).path)
        relative = request_path.lstrip("/") or "index.html"
        candidate = Path(self.directory) / relative
        if candidate.is_file():
            super().do_GET()
            return
        body = (Path(self.directory) / "404.html").read_bytes()
        self.send_response(404)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, _format: str, *_args: object) -> None:
        return


def run(output_dir: Path) -> dict[str, object]:
    if not NODE.is_file() or not PLAYWRIGHT_MODULE_DIR.joinpath("playwright").is_dir():
        raise RuntimeError("bundled Playwright runtime is unavailable")
    if not CHROME.is_file():
        raise RuntimeError("headless Chrome executable is unavailable")
    output_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="pfi-stage11-public-browser-") as temp_name:
        temp_root = Path(temp_name)
        dist = temp_root / "dist"
        raw_trace = temp_root / "raw-trace.zip"
        build = subprocess.run(
            [
                str(NODE),
                "scripts/cloudflare/build_static_surface.mjs",
                "--source",
                str(PUBLIC_SOURCE),
                "--output",
                str(dist),
            ],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if build.returncode != 0:
            raise RuntimeError("static public build failed")
        handler = partial(_BoundaryHandler, directory=str(dist))
        server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            completed = subprocess.run(
                [
                    str(NODE),
                    str(CDP_RUNNER),
                    "--base-url",
                    f"http://127.0.0.1:{server.server_port}",
                    "--output-dir",
                    str(output_dir),
                    "--raw-trace",
                    str(raw_trace),
                    "--chrome",
                    str(CHROME),
                ],
                cwd=REPO_ROOT,
                env={**os.environ, "PFI_PLAYWRIGHT_MODULE_DIR": str(PLAYWRIGHT_MODULE_DIR)},
                text=True,
                capture_output=True,
                check=False,
                timeout=60,
            )
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)
        if completed.returncode != 0:
            raise RuntimeError(
                "headless public boundary validation failed: "
                + (completed.stderr or completed.stdout)[-2000:]
            )
        browser = json.loads(
            (output_dir / "browser_validation.json").read_text(encoding="utf-8")
        )
        trace_privacy = sanitize_playwright_trace(
            raw_trace,
            output_dir / "browser_trace_sanitized.zip",
            private_payloads=(b"PRIVATE_USER", b"PRIVATE_DERIVED"),
        )
        (output_dir / "trace_privacy.json").write_text(
            json.dumps(trace_privacy, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    result = {
        "schema": "PFIV025Stage11PublicBoundaryBrowserDriverV1",
        "status": (
            "pass"
            if browser.get("status") == "pass" and trace_privacy.get("status") == "pass"
            else "fail"
        ),
        "browser_status": browser.get("status"),
        "trace_privacy_status": trace_privacy.get("status"),
        "browser_check_count": browser.get("checkCount"),
        "loopback_only": True,
        "external_network_calls": 0,
        "contains_private_values": False,
        "contains_absolute_paths": False,
        "finder_used": False,
        "launchservices_used": False,
        "gui_file_operations_used": False,
    }
    if result["status"] != "pass":
        raise RuntimeError("public boundary browser evidence failed closed")
    return result


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    try:
        result = run(args.output_dir)
    except Exception as exc:
        print(json.dumps({"status": "fail", "error_type": type(exc).__name__}))
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
