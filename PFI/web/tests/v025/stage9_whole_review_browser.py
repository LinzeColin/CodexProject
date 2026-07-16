#!/usr/bin/env python3
"""Generate current-content Stage 9 browser evidence using headless Chrome only."""

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
REPORT_DIR = PFI_ROOT / "reports/pfi_v025/stage_9/whole_stage_review"
CDP_RUNNER = PFI_ROOT / "web/tests/v025/stage9_whole_review_cdp.mjs"
CHROME = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
DEFAULT_PLAYWRIGHT_MODULE_DIR = (
    Path.home()
    / ".cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules"
)
REVIEW_BASE = "45653bd4d57d3a4a8d6f025b5f624fed5f155d1e"
REQUIRED_FILES = (
    "playwright_result.json",
    "stage9_analysis_components.png",
    "stage9_decision_review.png",
    "sensitivity_view.png",
    "phase_9_2_dom_snapshot.json",
    "phase_9_2_accessibility_tree.json",
    "phase_9_3_dom_snapshot.json",
    "phase_9_3_accessibility_tree.json",
    "browser_trace_sanitized.zip",
)


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
    if head != REVIEW_BASE:
        raise RuntimeError("browser evidence must run on the frozen Stage 9 remediation commit")

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    for name in (*REQUIRED_FILES, "browser_validation.json"):
        (REPORT_DIR / name).unlink(missing_ok=True)
    with tempfile.TemporaryDirectory(prefix="pfi-stage9-whole-review-browser-") as temp:
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
            timeout=180,
        )
        if completed.returncode != 0:
            raise RuntimeError(completed.stderr or completed.stdout or "Stage 9 browser failed")
        result = json.loads(
            (REPORT_DIR / "playwright_result.json").read_text(encoding="utf-8")
        )
        if result.get("status") != "pass":
            raise RuntimeError("Stage 9 browser result is not passing")
        trace_privacy = sanitize_playwright_trace(
            raw_trace,
            REPORT_DIR / "browser_trace_sanitized.zip",
        )

    missing = [name for name in REQUIRED_FILES if not (REPORT_DIR / name).is_file()]
    if missing:
        raise RuntimeError(f"browser evidence files are missing: {missing}")
    files = [
        {
            "path": f"PFI/reports/pfi_v025/stage_9/whole_stage_review/{name}",
            "sha256": _sha(REPORT_DIR / name),
            "byte_size": (REPORT_DIR / name).stat().st_size,
        }
        for name in REQUIRED_FILES
    ]
    validation = {
        "schema": "PFIV025Stage9WholeReviewBrowserEvidenceV1",
        "status": "pass",
        "acceptance_id": "ACC-PFI-V025-STAGE9-WHOLE-REVIEW",
        "review_base": REVIEW_BASE,
        "check_count": result["checkCount"],
        "passed_check_count": result["passedCheckCount"],
        "checks": result["checks"],
        "visible": result["visible"],
        "persistence": result["persistence"],
        "exports": result["exports"],
        "diagnostics": result["diagnostics"],
        "files": files,
        "trace_privacy_scan": trace_privacy,
        "loopback_only": True,
        "finder_used": False,
        "launchservices_used": False,
        "external_network_used": False,
        "financial_values_persisted": 0,
        "contains_private_values": False,
        "automatic_trading_allowed": False,
        "trade_execution_available": False,
        "stage_10_started": False,
    }
    _write_json(REPORT_DIR / "browser_validation.json", validation)
    print(
        "stage9 whole-review browser evidence: "
        f"{validation['passed_check_count']}/{validation['check_count']} pass"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
