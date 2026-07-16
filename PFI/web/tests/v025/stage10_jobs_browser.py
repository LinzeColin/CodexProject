#!/usr/bin/env python3
"""Run the Phase 10.3 formal-shell job recovery proof on loopback only."""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
from functools import partial
import hashlib
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import re
import secrets
import sqlite3
import subprocess
import sys
import tempfile
import threading
import time
from urllib.parse import urlsplit


THIS_DIR = Path(__file__).resolve().parent
if str(THIS_DIR) not in sys.path:
    sys.path.insert(0, str(THIS_DIR))
from stage7_trace_privacy import sanitize_playwright_trace  # noqa: E402


PFI_ROOT = Path(__file__).resolve().parents[3]
REPO_ROOT = PFI_ROOT.parent
DEFAULT_OUTPUT_DIR = PFI_ROOT / "reports/pfi_v025/stage_10/phase_10_3"
CDP_RUNNER = PFI_ROOT / "web/tests/v025/stage10_jobs_cdp.mjs"
CODEX_RUNTIME_ROOT = (
    Path.home() / ".cache/codex-runtimes/codex-primary-runtime/dependencies"
)
PLAYWRIGHT_MODULE_DIR = CODEX_RUNTIME_ROOT / "node/node_modules"
NODE = CODEX_RUNTIME_ROOT / "node/bin/node"
CHROME = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")


class _FormalShellHandler(SimpleHTTPRequestHandler):
    index_markup = ""

    def do_GET(self) -> None:  # noqa: N802
        request_path = urlsplit(self.path).path
        if request_path == "/" or Path(request_path).suffix == "":
            body = self.index_markup.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)
            return
        super().do_GET()

    def log_message(self, _format: str, *_args: object) -> None:
        return


def _runtime_markup(api_base_url: str, api_auth_token: str) -> str:
    source = (PFI_ROOT / "web/index.html").read_text(encoding="utf-8")
    runtime = {
        "apiBaseUrl": api_base_url,
        "apiAuthToken": api_auth_token,
        "readModelStatusApi": False,
        "runtimeApiEnabled": True,
        "releaseManifestApi": False,
        "releaseCachePolicyApi": False,
        "stage1OfficialCandidate": False,
        "candidateDataMode": "canonical",
        "projectRoot": "",
    }
    encoded = json.dumps(runtime, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    markup, count = re.subn(
        r'<script type="application/json" id="pfi-runtime-config">.*?</script>',
        f'<script type="application/json" id="pfi-runtime-config">{encoded}</script>',
        source,
        count=1,
        flags=re.DOTALL,
    )
    if count != 1:
        raise RuntimeError("formal shell runtime config is unavailable")
    return markup


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _observability_context(label: str) -> dict[str, object]:
    return {
        "source_hash": hashlib.sha256(f"{label}:source".encode()).hexdigest(),
        "data_hash": hashlib.sha256(f"{label}:data".encode()).hexdigest(),
        "formula_hash": hashlib.sha256(f"{label}:formula".encode()).hexdigest(),
        "parameter_hash": hashlib.sha256(f"{label}:parameter".encode()).hexdigest(),
        "read_model_hash": hashlib.sha256(f"{label}:read-model".encode()).hexdigest(),
        "cache_key": hashlib.sha256(f"{label}:cache".encode()).hexdigest(),
        "impact_scope": ["review.job_state_projection"],
        "cache_fallback_used": False,
        "external_network_calls": 0,
    }


def _seed_projection_states(db_path: Path) -> dict[str, str]:
    """Create actual persisted retrying/dead-letter projections for formal UI checks."""

    from pfi_os.infrastructure.jobs import SQLiteDurableJobStore

    base = datetime.now(timezone.utc) - timedelta(minutes=5)
    store = SQLiteDurableJobStore(db_path)
    states: dict[str, str] = {}
    for offset, (expected_state, job_type, max_attempts) in enumerate(
        (
            ("retrying", "review.retrying", 3),
            ("dead_letter", "review.dead-letter", 1),
        )
    ):
        queued_at = base + timedelta(seconds=offset * 10)
        queued = store.enqueue(
            job_type=job_type,
            idempotency_key=f"formal-ui-{expected_state}",
            payload={"fixture": "persisted_state_projection"},
            max_attempts=max_attempts,
            contains_financial_facts=False,
            observability_context=_observability_context(expected_state),
            now=queued_at,
        )["job"]
        claimed = store.claim(
            job_type=job_type,
            worker_id="formal-ui-fixture-worker",
            lease_seconds=1,
            now=queued_at + timedelta(seconds=1),
        )
        if not claimed["claimed"]:
            raise RuntimeError(f"unable to claim {expected_state} UI fixture")
        recovered = store.recover_expired_leases(
            job_type=job_type,
            now=queued_at + timedelta(seconds=3),
        )
        projected = store.get(str(queued["job_id"]))
        if projected["status"] != expected_state or recovered["recovered_count"] != 1:
            raise RuntimeError(f"unable to persist {expected_state} UI fixture")
        states[expected_state] = str(queued["job_id"])
    return states


def _database_evidence(
    db_path: Path,
    *,
    browser: dict[str, object],
    fixture_job_ids: dict[str, str],
) -> dict[str, object]:
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        integrity_check = str(conn.execute("PRAGMA integrity_check").fetchone()[0])
        foreign_key_issues = conn.execute("PRAGMA foreign_key_check").fetchall()
        journal_mode = str(conn.execute("PRAGMA journal_mode").fetchone()[0]).upper()
        jobs = [
            dict(row)
            for row in conn.execute(
                """
                SELECT j.job_id, j.job_type, j.status, j.revision, j.attempt_count,
                       j.progress_completed, j.progress_total, j.progress_step,
                       j.error_code, t.cache_fallback_used, t.external_network_calls
                FROM durable_jobs AS j
                JOIN durable_job_trace_contexts AS t ON t.job_id = j.job_id
                ORDER BY j.job_id
                """
            )
        ]
        counts = {
            table: int(conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
            for table in (
                "durable_jobs",
                "durable_job_events",
                "durable_job_trace_contexts",
                "durable_job_spans",
                "durable_job_logs",
            )
        }
        trace_rows = [
            dict(row)
            for row in conn.execute(
                """
                SELECT t.job_id, t.trace_id, t.external_network_calls,
                       COUNT(DISTINCT s.span_row_id) AS span_count,
                       COUNT(DISTINCT l.log_id) AS log_count
                FROM durable_job_trace_contexts AS t
                LEFT JOIN durable_job_spans AS s ON s.job_id = t.job_id
                LEFT JOIN durable_job_logs AS l ON l.job_id = t.job_id
                GROUP BY t.job_id, t.trace_id, t.external_network_calls
                ORDER BY t.job_id
                """
            )
        ]
        event_types = [
            {"job_id": str(row[0]), "event_type": str(row[1])}
            for row in conn.execute(
                "SELECT job_id, event_type FROM durable_job_events ORDER BY event_id"
            )
        ]
    by_id = {str(row["job_id"]): row for row in jobs}
    success_id = str(browser.get("job_id") or "")
    failure_id = str(browser.get("failure_job_id") or "")
    success_events = [
        row["event_type"] for row in event_types if row["job_id"] == success_id
    ]
    expected_statuses = {
        success_id: "succeeded",
        failure_id: "failed",
        fixture_job_ids["retrying"]: "retrying",
        fixture_job_ids["dead_letter"]: "dead_letter",
    }
    status_match = all(
        job_id in by_id and by_id[job_id]["status"] == expected
        for job_id, expected in expected_statuses.items()
    )
    return {
        "schema": "PFIV025Stage10WholeReviewDatabaseEvidenceV1",
        "status": "pass"
        if integrity_check == "ok"
        and not foreign_key_issues
        and journal_mode == "DELETE"
        and counts["durable_jobs"] == 4
        and counts["durable_job_events"] == counts["durable_job_spans"] == counts["durable_job_logs"]
        and status_match
        and int(by_id[success_id]["attempt_count"]) == 1
        and success_events.count("heartbeat") >= 2
        and "lease_expired_requeued" not in success_events
        and int(by_id[failure_id]["cache_fallback_used"]) == 1
        and all(int(row["external_network_calls"]) == 0 for row in trace_rows)
        else "fail",
        "integrity_check": integrity_check,
        "foreign_key_check": "pass" if not foreign_key_issues else "fail",
        "foreign_key_issue_count": len(foreign_key_issues),
        "journal_mode": journal_mode,
        "wal_enabled": journal_mode == "WAL",
        "counts": counts,
        "jobs": jobs,
        "expected_statuses": expected_statuses,
        "status_match": status_match,
        "trace_rows": trace_rows,
        "event_types": event_types,
        "contains_financial_values": False,
        "contains_private_paths": False,
        "canonical_private_database_used": False,
    }


def _write_json(path: Path, payload: object) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def run(output_dir: Path) -> dict[str, object]:
    if not CHROME.is_file():
        raise RuntimeError("local Google Chrome executable is required")
    if not NODE.is_file() or not (PLAYWRIGHT_MODULE_DIR / "playwright").is_dir():
        raise RuntimeError("cached Node/Playwright runtime is required; installation is forbidden")
    output_dir.mkdir(parents=True, exist_ok=True)
    for name in (
        "browser_validation.json",
        "database_integrity.json",
        "job_recovery_redacted.png",
        "job_failure_redacted.png",
        "dom_snapshot.json",
        "accessibility_tree.json",
        "browser_trace_raw.zip",
        "browser_trace_sanitized.zip",
        "trace_privacy.json",
    ):
        (output_dir / name).unlink(missing_ok=True)

    original_env = {
        key: os.environ.get(key)
        for key in ("PFI_DATA_HOME", "PFI_STAGE1_CANDIDATE_MODE", "PFI_STREAMLIT_CACHE_KEY")
    }
    api_server: ThreadingHTTPServer | None = None
    api_thread: threading.Thread | None = None
    web_server: ThreadingHTTPServer | None = None
    web_thread: threading.Thread | None = None
    raw_trace = output_dir / "browser_trace_raw.zip"
    runtime_token = secrets.token_urlsafe(32)
    with tempfile.TemporaryDirectory(prefix="pfi-v025-stage10-jobs-") as temporary:
        temp_root = Path(temporary)
        data_home = temp_root / "data_home"
        db_path = data_home / "private/operational/pfi.sqlite"
        os.environ["PFI_DATA_HOME"] = str(data_home)
        os.environ["PFI_STAGE1_CANDIDATE_MODE"] = "0"
        os.environ.pop("PFI_STREAMLIT_CACHE_KEY", None)
        try:
            from pfi_v02 import stage_v021_runtime_api as runtime_api

            fixture_job_ids = _seed_projection_states(db_path)
            original_policy_builder = runtime_api.build_v025_release_cache_policy
            policy_call_count = 0
            policy_lock = threading.Lock()

            def delayed_policy(*args: object, **kwargs: object) -> dict[str, object]:
                nonlocal policy_call_count
                with policy_lock:
                    policy_call_count += 1
                    current_call = policy_call_count
                if current_call == 2:
                    time.sleep(10.8)
                if current_call == 3:
                    raise RuntimeError("formal review preflight unavailable")
                policy = dict(original_policy_builder(*args, **kwargs))
                if current_call == 4:
                    policy["external_network_calls"] = 1
                return policy

            runtime_api.build_v025_release_cache_policy = delayed_policy
            api_handler = runtime_api._handler_factory(db_path, auth_token=runtime_token)
            api_server = ThreadingHTTPServer(("127.0.0.1", 0), api_handler)
            api_thread = threading.Thread(
                target=api_server.serve_forever,
                name="pfi-stage10-jobs-api",
                daemon=True,
            )
            api_thread.start()
            api_url = f"http://127.0.0.1:{api_server.server_port}"

            handler = type(
                "PFIStage10FormalShellHandler",
                (_FormalShellHandler,),
                {"index_markup": _runtime_markup(api_url, runtime_token)},
            )
            web_server = ThreadingHTTPServer(
                ("127.0.0.1", 0),
                partial(handler, directory=str(PFI_ROOT / "web")),
            )
            web_thread = threading.Thread(
                target=web_server.serve_forever,
                name="pfi-stage10-jobs-web",
                daemon=True,
            )
            web_thread.start()
            web_url = f"http://127.0.0.1:{web_server.server_port}"

            completed = subprocess.run(
                [
                    str(NODE),
                    str(CDP_RUNNER),
                    "--base-url",
                    web_url,
                    "--api-url",
                    api_url,
                    "--api-token",
                    runtime_token,
                    "--output-dir",
                    str(output_dir),
                    "--raw-trace",
                    str(raw_trace),
                    "--chrome",
                    str(CHROME),
                    "--retrying-job-id",
                    fixture_job_ids["retrying"],
                    "--dead-letter-job-id",
                    fixture_job_ids["dead_letter"],
                ],
                cwd=REPO_ROOT,
                env={**os.environ, "PFI_PLAYWRIGHT_MODULE_DIR": str(PLAYWRIGHT_MODULE_DIR)},
                check=False,
                text=True,
                capture_output=True,
                timeout=90,
            )
            if completed.returncode != 0:
                raise RuntimeError(
                    "Stage 10 Phase 10.3 headless browser failed: "
                    + (completed.stderr or completed.stdout)[-4000:]
                )
            browser = json.loads((output_dir / "browser_validation.json").read_text(encoding="utf-8"))
            database_evidence = _database_evidence(
                db_path,
                browser=browser,
                fixture_job_ids=fixture_job_ids,
            )
            _write_json(output_dir / "database_integrity.json", database_evidence)
            trace_privacy = sanitize_playwright_trace(
                raw_trace,
                output_dir / "browser_trace_sanitized.zip",
                auth_tokens=(runtime_token,),
            )
            _write_json(output_dir / "trace_privacy.json", trace_privacy)
            raw_trace.unlink(missing_ok=True)

            result = {
                "schema": "PFIV025Stage10WholeReviewBrowserDriverV1",
                "status": "pass"
                if browser.get("status") == "pass"
                and database_evidence["status"] == "pass"
                and trace_privacy["status"] == "pass"
                else "fail",
                "browser_status": browser.get("status"),
                "database_status": database_evidence["status"],
                "trace_privacy_status": trace_privacy["status"],
                "policy_builder_call_count": policy_call_count,
                "fixture_job_ids": fixture_job_ids,
                "loopback_only": True,
                "external_network_calls": 0,
                "canonical_private_database_used": False,
                "screenshot_sha256": _sha256(output_dir / "job_recovery_redacted.png"),
                "failure_screenshot_sha256": _sha256(output_dir / "job_failure_redacted.png"),
                "dom_snapshot_sha256": _sha256(output_dir / "dom_snapshot.json"),
                "accessibility_tree_sha256": _sha256(output_dir / "accessibility_tree.json"),
                "trace_sha256": _sha256(output_dir / "browser_trace_sanitized.zip"),
                "finder_used": False,
                "launchservices_used": False,
                "gui_file_operations_used": False,
            }
            if result["status"] != "pass":
                raise RuntimeError(f"Stage 10 browser driver failed closed: {result}")
            return result
        finally:
            try:
                runtime_api.build_v025_release_cache_policy = original_policy_builder
            except (NameError, AttributeError):
                pass
            for server, thread in ((web_server, web_thread), (api_server, api_thread)):
                if server is not None:
                    server.shutdown()
                    server.server_close()
                if thread is not None:
                    thread.join(timeout=5)
            for key, value in original_env.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()
    result = run(args.output_dir.resolve())
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
