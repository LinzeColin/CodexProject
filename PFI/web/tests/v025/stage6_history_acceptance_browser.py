#!/usr/bin/env python3
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
REPORT_DIR = PFI_ROOT / "reports/pfi_v025/stage_6/phase_6_3"
STAGE5_BROWSER = PFI_ROOT / "scripts/v025/browser_validate_stage5_whole_review.py"
CDP_RUNNER = PFI_ROOT / "web/tests/v025/stage6_history_acceptance_cdp.mjs"
PLAYWRIGHT_MODULE_DIR = Path(
    "/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules"
)
CHROME = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
IMPLEMENTATION_BASE = "80396224f049658e9293f8da313a92a50431f903"


def _load_browser_helpers() -> object:
    spec = importlib.util.spec_from_file_location("pfi_stage5_browser_helpers", STAGE5_BROWSER)
    if spec is None or spec.loader is None:
        raise RuntimeError("formal-shell browser helpers are unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class _SpaLoopbackHandler:  # mixed in dynamically with the existing quiet handler
    def do_GET(self) -> None:  # noqa: N802
        request_path = urlsplit(self.path).path
        if request_path == "/" or Path(request_path).suffix == "":
            self.path = "/index.html"
        super().do_GET()


def _load_route_contract() -> dict[str, object]:
    script = """
const routes = require(process.argv[1]);
console.log(JSON.stringify(routes.phase63HistoryContract));
"""
    completed = subprocess.run(
        ["node", "-e", script, str(PFI_ROOT / "web/app/routes.js")],
        cwd=PFI_ROOT.parent,
        check=True,
        text=True,
        capture_output=True,
    )
    return json.loads(completed.stdout)


def _write_json(name: str, payload: object) -> None:
    (REPORT_DIR / name).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    if not CHROME.is_file():
        raise RuntimeError("local Google Chrome is required")
    if not (PLAYWRIGHT_MODULE_DIR / "playwright").is_dir():
        raise RuntimeError("cached Playwright runtime is required; installation is forbidden")
    helpers = _load_browser_helpers()
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    markup = helpers._offline_formal_shell_html({})
    temp_dir = Path(tempfile.mkdtemp(prefix="pfi-stage6-phase63-formal-shell-", dir="/tmp"))
    markup_path = temp_dir / "index.html"
    runner_path = temp_dir / "stage6_history_acceptance_cdp.mjs"
    server: ThreadingHTTPServer | None = None
    thread: threading.Thread | None = None
    try:
        markup_path.write_text(markup, encoding="utf-8")
        shutil.copyfile(CDP_RUNNER, runner_path)
        handler_type = type(
            "PFIPhase63SpaHandler",
            (_SpaLoopbackHandler, helpers._QuietLoopbackHandler),
            {},
        )
        handler = partial(handler_type, directory=str(temp_dir))
        server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        thread = threading.Thread(target=server.serve_forever, name="pfi-stage6-phase63-loopback", daemon=True)
        thread.start()
        base_url = f"http://127.0.0.1:{server.server_address[1]}"
        environment = {
            **os.environ,
            "PFI_PLAYWRIGHT_MODULE_DIR": str(PLAYWRIGHT_MODULE_DIR),
        }
        completed = subprocess.run(
            [
                "node",
                str(runner_path),
                "--base-url",
                base_url,
                "--output-dir",
                str(REPORT_DIR),
                "--chrome",
                str(CHROME),
            ],
            cwd=PFI_ROOT.parent,
            env=environment,
            check=False,
            text=True,
            capture_output=True,
            timeout=120,
        )
        if completed.returncode != 0:
            raise RuntimeError(f"Playwright acceptance failed: {completed.stderr or completed.stdout}")
    finally:
        if server is not None:
            server.shutdown()
            server.server_close()
        if thread is not None:
            thread.join(timeout=5)
        markup_path.unlink(missing_ok=True)
        shutil.rmtree(temp_dir, ignore_errors=True)

    playwright_result = json.loads((REPORT_DIR / "playwright_result.json").read_text(encoding="utf-8"))
    route_contract = _load_route_contract()
    checks = playwright_result["checks"]
    status = "pass" if playwright_result["status"] == "pass" and all(checks.values()) else "fail"
    browser_history_validation = {
        "schema": "PFIV025Stage6Phase63BrowserHistoryValidationV1",
        "status": status,
        "acceptance_id": "ACC-PFI-V025-S6-P63-HISTORY-ACCEPTANCE",
        "method": "cached_playwright_actual_formal_shell_ephemeral_loopback_local_chrome",
        "checks": checks,
        "snapshots": playwright_result["snapshots"],
        "repeated_click_history_delta": playwright_result["repeated_click_history_delta"],
        "console_errors": playwright_result["console_errors"],
        "page_errors": playwright_result["page_errors"],
        "http_errors": playwright_result["http_errors"],
        "finder_used": False,
        "network_scope": "ephemeral_local_loopback_only",
        "external_network_performed": False,
        "financial_data_loaded": False,
    }
    _write_json("browser_history_validation.json", browser_history_validation)
    _write_json(
        "a11y_tree.json",
        {
            "schema": "PFIV025Stage6Phase63AccessibilityTreeV1",
            "status": "pass" if checks["accessibility_tree_only_ten_primary_entries"] else "fail",
            **playwright_result["a11y"],
        },
    )
    _write_json(
        "route_runtime.json",
        {
            "schema": "PFIV025Stage6Phase63RouteRuntimeV1",
            "status": status,
            "contract": route_contract,
            "canonical_path_history": checks["canonical_path_history"],
            "back_forward_restores_route": checks["back_forward_restores_route"],
            "history_state_matches_url": checks["history_state_matches_url"],
            "scroll_restoration": checks["scroll_restoration"],
            "deep_link_and_reload": checks["deep_link_and_reload"],
        },
    )
    _write_json(
        "invalid_route_validation.json",
        {
            "schema": "PFIV025Stage6Phase63InvalidRouteValidationV1",
            "status": "pass" if checks["invalid_route_actionable"] and checks["invalid_route_recovery"] else "fail",
            "invalid_snapshot": playwright_result["snapshots"]["invalid"],
            "recovered_snapshot": playwright_result["snapshots"]["recovered"],
        },
    )
    _write_json(
        "phase_contract.json",
        {
            "schema": "PFIV025Stage6Phase63RunContractV1",
            "status": "candidate_pass" if status == "pass" else "fail",
            "iteration_id": "ITER-20260715-PFI-V025-S6-P63",
            "contract_id": "PFI-V025-STAGE6-PHASE63-HISTORY-ACCEPTANCE",
            "acceptance_id": "ACC-PFI-V025-S6-P63-HISTORY-ACCEPTANCE",
            "task_ids": ["S6-P3-T1", "S6-P3-T2", "S6-P3-T3", "S6-P3-T4"],
            "implementation_base": IMPLEMENTATION_BASE,
            "current_phase_only": True,
            "stage_6_whole_stage_review_started": False,
            "stage_7_started": False,
            "push_performed": False,
            "app_install_performed": False,
            "finder_used": False,
            "external_network_performed": False,
            "real_financial_data_read": False,
            "database_changed": False,
        },
    )
    _write_json(
        "stage_6_evidence.json",
        {
            "schema": "PFIV025Stage6Phase63CandidateEvidenceV1",
            "status": "candidate_pass_waiting_for_independent_whole_stage_review" if status == "pass" else "fail",
            "phase_6_1_status": "candidate_pass",
            "phase_6_2_status": "candidate_pass",
            "phase_6_3_status": "candidate_pass" if status == "pass" else "fail",
            "stage_6_phase_task_count": 12,
            "stage_6_phase_task_completed_count": 12 if status == "pass" else 8,
            "stage_6_whole_stage_review_status": "not_started",
            "stage_6_user_acceptance_status": "waiting",
            "stage_7_status": "not_started",
            "production_accepted": False,
            "final_human_acceptance": False,
            "evidence_refs": [
                "PFI/reports/pfi_v025/stage_6/phase_6_3/playwright_result.json",
                "PFI/reports/pfi_v025/stage_6/phase_6_3/browser_history_validation.json",
                "PFI/reports/pfi_v025/stage_6/phase_6_3/a11y_tree.json",
                "PFI/reports/pfi_v025/stage_6/phase_6_3/route_runtime.json",
                "PFI/reports/pfi_v025/stage_6/phase_6_3/invalid_route_validation.json",
            ],
        },
    )
    print(
        json.dumps(
            {
                "status": status,
                "checks": checks,
                "playwright_stdout": completed.stdout.strip(),
            },
            ensure_ascii=False,
        )
    )
    return 0 if status == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
