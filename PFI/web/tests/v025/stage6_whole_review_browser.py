#!/usr/bin/env python3
"""Run the Stage 6 current-HEAD whole-stage browser acceptance locally."""

from __future__ import annotations

from functools import partial
from http.server import ThreadingHTTPServer
import importlib.util
import json
import os
from pathlib import Path
from urllib.parse import urlsplit
import shutil
import subprocess
import tempfile
import threading


PFI_ROOT = Path(__file__).resolve().parents[3]
REPORT_DIR = PFI_ROOT / "reports/pfi_v025/stage_6/whole_stage_review"
STAGE5_BROWSER = PFI_ROOT / "scripts/v025/browser_validate_stage5_whole_review.py"
CDP_RUNNER = PFI_ROOT / "web/tests/v025/stage6_whole_review_cdp.mjs"
PLAYWRIGHT_MODULE_DIR = Path(
    "/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules"
)
CHROME = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")


def _load_browser_helpers() -> object:
    spec = importlib.util.spec_from_file_location("pfi_stage5_browser_helpers", STAGE5_BROWSER)
    if spec is None or spec.loader is None:
        raise RuntimeError("formal-shell browser helpers are unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class _SpaLoopbackHandler:
    def do_GET(self) -> None:  # noqa: N802
        request_path = urlsplit(self.path).path
        if request_path == "/" or Path(request_path).suffix == "":
            self.path = "/index.html"
        super().do_GET()


def main() -> int:
    if not CHROME.is_file():
        raise RuntimeError("local Google Chrome is required")
    if not (PLAYWRIGHT_MODULE_DIR / "playwright").is_dir():
        raise RuntimeError("cached Playwright runtime is required; installation is forbidden")
    helpers = _load_browser_helpers()
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    temp_dir = Path(tempfile.mkdtemp(prefix="pfi-stage6-whole-review-", dir="/tmp"))
    markup_path = temp_dir / "index.html"
    runner_path = temp_dir / "stage6_whole_review_cdp.mjs"
    server: ThreadingHTTPServer | None = None
    thread: threading.Thread | None = None
    try:
        markup_path.write_text(helpers._offline_formal_shell_html({}), encoding="utf-8")
        shutil.copyfile(CDP_RUNNER, runner_path)
        handler_type = type("PFIStage6WholeReviewSpaHandler", (_SpaLoopbackHandler, helpers._QuietLoopbackHandler), {})
        server = ThreadingHTTPServer(("127.0.0.1", 0), partial(handler_type, directory=str(temp_dir)))
        thread = threading.Thread(target=server.serve_forever, name="pfi-stage6-whole-review-loopback", daemon=True)
        thread.start()
        completed = subprocess.run(
            [
                "node", str(runner_path),
                "--base-url", f"http://127.0.0.1:{server.server_address[1]}",
                "--output-dir", str(REPORT_DIR),
                "--chrome", str(CHROME),
            ],
            cwd=PFI_ROOT.parent,
            env={**os.environ, "PFI_PLAYWRIGHT_MODULE_DIR": str(PLAYWRIGHT_MODULE_DIR)},
            check=False,
            text=True,
            capture_output=True,
            timeout=180,
        )
        if completed.returncode != 0:
            raise RuntimeError(f"Stage 6 whole-stage browser review failed: {completed.stderr or completed.stdout}")
    finally:
        if server is not None:
            server.shutdown()
            server.server_close()
        if thread is not None:
            thread.join(timeout=5)
        shutil.rmtree(temp_dir, ignore_errors=True)

    result = json.loads((REPORT_DIR / "playwright_result.json").read_text(encoding="utf-8"))
    checks = result["checks"]
    status = "pass" if result["status"] == "pass" and all(checks.values()) else "fail"
    validation = {
        "schema": "PFIV025Stage6WholeReviewBrowserValidationV1",
        "status": status,
        "acceptance_id": "ACC-PFI-V025-STAGE6-WHOLE-REVIEW",
        "method": "cached_playwright_actual_formal_shell_ephemeral_loopback_local_chrome",
        "current_head_combined_review": True,
        "primary_routes_checked": len(result["primary_snapshots"]),
        "representative_secondary_routes_checked": len(result["secondary_snapshots"]),
        "alias_routes_checked": len(result["alias_snapshots"]),
        "nojs_primary_route_count": result["nojs"]["primary_route_count"],
        "nojs_secondary_route_count": result["nojs"]["secondary_route_count"],
        "checks": checks,
        "console_errors": result["console_errors"],
        "page_errors": result["page_errors"],
        "http_errors": result["http_errors"],
        "blocked_external_requests": result["blocked_external_requests"],
        "network_performed": True,
        "network_scope": "ephemeral_local_loopback_only",
        "external_network_performed": False,
        "finder_used": False,
        "real_financial_data_read": False,
        "database_changed": False,
    }
    (REPORT_DIR / "browser_validation.json").write_text(
        json.dumps(validation, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (REPORT_DIR / "accessibility_tree.json").write_text(
        json.dumps(
            {
                "schema": "PFIV025Stage6WholeReviewAccessibilityTreeV1",
                "status": "pass" if checks["accessibility_tree_exactly_ten_primary"] else "fail",
                **result["a11y"],
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"status": status, "checks": checks}, ensure_ascii=False))
    return 0 if status == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
