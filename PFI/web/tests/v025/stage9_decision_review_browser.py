#!/usr/bin/env python3
"""Run Phase 9.3 formal-shell validation without Finder or external network."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile

from stage7_trace_privacy import sanitize_playwright_trace


PFI_ROOT = Path(__file__).resolve().parents[3]
REPO_ROOT = PFI_ROOT.parent
REPORT_DIR = PFI_ROOT / "reports/pfi_v025/stage_9/phase_9_3"
CDP_RUNNER = PFI_ROOT / "web/tests/v025/stage9_decision_review_cdp.mjs"
CHROME = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
DEFAULT_PLAYWRIGHT_MODULE_DIR = (
    Path.home()
    / ".cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules"
)
PRODUCT_COMMIT = "168666305c874d91ab8fd45e9f925e49928e7e63"


def _write_json(path: Path, payload: object) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _sha(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    playwright_dir = Path(
        os.environ.get("PFI_PLAYWRIGHT_MODULE_DIR", DEFAULT_PLAYWRIGHT_MODULE_DIR)
    ).expanduser()
    if not CHROME.is_file():
        raise RuntimeError("local Chrome is unavailable; installation is forbidden")
    if not (playwright_dir / "playwright").is_dir():
        raise RuntimeError("cached Playwright is unavailable; installation is forbidden")
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=REPO_ROOT,
        check=True,
        text=True,
        capture_output=True,
    ).stdout.strip()
    if head != PRODUCT_COMMIT:
        raise RuntimeError("browser evidence must be generated directly on product commit")

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    for name in (
        "decision_review_view.png",
        "playwright_result.json",
        "browser_trace_sanitized.zip",
        "browser_validation.json",
    ):
        (REPORT_DIR / name).unlink(missing_ok=True)
    with tempfile.TemporaryDirectory(prefix="pfi-stage9-phase93-browser-") as temp:
        raw_trace = Path(temp) / "browser_trace_raw.zip"
        completed = subprocess.run(
            [
                "node",
                str(CDP_RUNNER),
                "--web-root",
                str(PFI_ROOT / "web"),
                "--output-dir",
                str(REPORT_DIR),
                "--raw-trace",
                str(raw_trace),
                "--chrome",
                str(CHROME),
            ],
            cwd=REPO_ROOT,
            env={**os.environ, "PFI_PLAYWRIGHT_MODULE_DIR": str(playwright_dir)},
            check=False,
            text=True,
            capture_output=True,
            timeout=120,
        )
        if completed.returncode != 0:
            raise RuntimeError(completed.stderr or completed.stdout or "Phase 9.3 browser failed")
        result = json.loads((REPORT_DIR / "playwright_result.json").read_text(encoding="utf-8"))
        if result.get("status") != "pass":
            raise RuntimeError("Phase 9.3 browser result is not passing")
        trace_privacy = sanitize_playwright_trace(
            raw_trace,
            REPORT_DIR / "browser_trace_sanitized.zip",
        )

    screenshot = REPORT_DIR / "decision_review_view.png"
    trace = REPORT_DIR / "browser_trace_sanitized.zip"
    if not screenshot.is_file() or screenshot.stat().st_size == 0:
        raise RuntimeError("decision review screenshot is unavailable")
    if not trace.is_file() or trace.stat().st_size == 0:
        raise RuntimeError("sanitized browser trace is unavailable")
    validation = {
        "schema": "PFIV025Stage9Phase93BrowserEvidenceV1",
        "status": "pass",
        "product_commit": PRODUCT_COMMIT,
        "check_count": result["checkCount"],
        "passed_check_count": result["passedCheckCount"],
        "checks": result["checks"],
        "visible": result["visible"],
        "downloads": result["downloads"],
        "diagnostics": result["diagnostics"],
        "decision_review_screenshot": screenshot.name,
        "decision_review_screenshot_sha256": _sha(screenshot),
        "trace": trace.name,
        "trace_sha256": _sha(trace),
        "trace_privacy_scan": trace_privacy,
        "loopback_only": True,
        "finder_used": False,
        "launchservices_used": False,
        "external_network_used": False,
        "financial_values_persisted": 0,
        "contains_private_values": False,
        "automatic_trading_allowed": False,
        "trade_execution_available": False,
    }
    _write_json(REPORT_DIR / "browser_validation.json", validation)
    print(
        "stage9 phase 9.3 browser evidence: "
        f"{validation['passed_check_count']}/{validation['check_count']} pass"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
