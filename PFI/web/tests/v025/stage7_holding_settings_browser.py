#!/usr/bin/env python3
"""Validate Stage 7 Phase 7.2 in the formal shell with isolated SQLite."""

from __future__ import annotations

from functools import partial
from http.server import ThreadingHTTPServer
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import threading
from urllib.parse import urlsplit
_BROWSER_TEST_DIR = Path(__file__).resolve().parent
if str(_BROWSER_TEST_DIR) not in sys.path:
    sys.path.insert(0, str(_BROWSER_TEST_DIR))
from stage7_trace_privacy import sanitize_playwright_trace  # noqa: E402


HOLDING_TRACE_PRIVATE_LITERALS = (b"CONTRACT-SENTINEL", b"contract-sentinel")


PFI_ROOT = Path(__file__).resolve().parents[3]
REPORT_DIR = PFI_ROOT / "reports/pfi_v025/stage_7/phase_7_2"
STAGE5_BROWSER = PFI_ROOT / "scripts/v025/browser_validate_stage5_whole_review.py"
CDP_RUNNER = PFI_ROOT / "web/tests/v025/stage7_holding_settings_cdp.mjs"
PLAYWRIGHT_MODULE_DIR = Path(
    "/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules"
)
CHROME = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
BROWSER_ARTIFACT_NAMES = (
    "browser_trace_sanitized.zip",
    "browser_trace_restart_sanitized.zip",
    "browser_validation.json",
    "db_integrity.json",
    "holding_db_before_after.json",
    "holding_saved_redacted.png",
    "playwright_exercise.json",
    "playwright_result.json",
    "restart_persistence.json",
    "restart_persistence_redacted.png",
    "settings_persistence.json",
    "settings_saved_redacted.png",
)


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


def _runtime_markup(markup: str, api_base_url: str, api_auth_token: str) -> str:
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
    encoded = json.dumps(runtime, ensure_ascii=False).replace("</", "<\\/")
    return re.sub(
        r'<script type="application/json" id="pfi-runtime-config">.*?</script>',
        f'<script type="application/json" id="pfi-runtime-config">{encoded}</script>',
        markup,
        flags=re.DOTALL,
    )


def _shutdown_runtime_server() -> None:
    from pfi_v02 import stage_v021_runtime_api as runtime_api

    server = runtime_api._SERVER_STATE.get("server")
    thread = runtime_api._SERVER_STATE.get("thread")
    if server is not None:
        server.shutdown()
        server.server_close()
    if thread is not None:
        thread.join(timeout=5)
    runtime_api._SERVER_STATE.clear()


def _run_browser(
    *, mode: str, base_url: str, api_url: str, api_token: str, raw_trace: Path
) -> None:
    completed = subprocess.run(
        [
            "node",
            str(CDP_RUNNER),
            "--mode",
            mode,
            "--base-url",
            base_url,
            "--api-url",
            api_url,
            "--api-token",
            api_token,
            "--output-dir",
            str(REPORT_DIR),
            "--raw-trace",
            str(raw_trace),
            "--chrome",
            str(CHROME),
        ],
        cwd=PFI_ROOT.parent,
        env={**os.environ, "PFI_PLAYWRIGHT_MODULE_DIR": str(PLAYWRIGHT_MODULE_DIR)},
        check=False,
        text=True,
        capture_output=True,
        timeout=240,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"Stage 7 Phase 7.2 browser {mode} failed: {completed.stderr or completed.stdout}"
        )


def _db_snapshot(db_path: Path) -> dict[str, object]:
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        foreign_key_issues = conn.execute("PRAGMA foreign_key_check").fetchall()
        integrity = str(conn.execute("PRAGMA integrity_check").fetchone()[0])
        record_counts = {
            "active": int(
                conn.execute("SELECT COUNT(*) FROM v025_holding_records WHERE status='active'").fetchone()[0]
            ),
            "deleted": int(
                conn.execute("SELECT COUNT(*) FROM v025_holding_records WHERE status='deleted'").fetchone()[0]
            ),
        }
        table_counts = {
            table: int(conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
            for table in (
                "v025_holding_records",
                "v025_holding_change_sets",
                "v025_holding_events",
                "v025_settings_preferences",
                "v025_settings_events",
            )
        }
        operation_counts = {
            str(row["operation"]): int(row["count"])
            for row in conn.execute(
                "SELECT operation, COUNT(*) AS count FROM v025_holding_events GROUP BY operation"
            ).fetchall()
        }
        holding_revisions = [
            int(row[0])
            for row in conn.execute("SELECT revision FROM v025_holding_records ORDER BY holding_id").fetchall()
        ]
        settings_revisions = [
            int(row[0])
            for row in conn.execute("SELECT revision FROM v025_settings_preferences ORDER BY scope").fetchall()
        ]
        migration_count = int(
            conn.execute(
                "SELECT COUNT(*) FROM pfi_schema_migrations WHERE migration_id=?",
                ("v025_stage7_holding_settings_v1",),
            ).fetchone()[0]
        )
    return {
        "foreign_key_check": "pass" if not foreign_key_issues else "fail",
        "foreign_key_issue_count": len(foreign_key_issues),
        "integrity_check": integrity,
        "record_counts": record_counts,
        "table_counts": table_counts,
        "operation_counts": operation_counts,
        "holding_revisions": holding_revisions,
        "settings_revisions": settings_revisions,
        "migration_count": migration_count,
    }


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _run(temp_dir: Path) -> int:
    if not CHROME.is_file():
        raise RuntimeError("local Google Chrome is required")
    if not (PLAYWRIGHT_MODULE_DIR / "playwright").is_dir():
        raise RuntimeError("cached Playwright runtime is required; installation is forbidden")

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    for name in (
        "playwright_exercise.json",
        "playwright_result.json",
        "holding_saved_redacted.png",
        "settings_saved_redacted.png",
        "restart_persistence_redacted.png",
        "browser_trace_exercise_raw.zip",
        "browser_trace_restart_raw.zip",
        "browser_trace_sanitized.zip",
        "browser_trace_restart_sanitized.zip",
    ):
        (REPORT_DIR / name).unlink(missing_ok=True)

    isolated_data_home = temp_dir / "data_home"
    db_path = isolated_data_home / "private" / "operational" / "pfi.sqlite"
    markup_path = temp_dir / "index.html"
    static_server: ThreadingHTTPServer | None = None
    static_thread: threading.Thread | None = None
    before_restart: dict[str, object] = {}
    after_restart: dict[str, object] = {}
    result: dict[str, object] = {}
    exercise: dict[str, object] = {}
    api_url_before = ""
    api_url_after = ""
    api_auth_token_before = ""
    api_auth_token_after = ""

    original_env = {
        key: os.environ.get(key)
        for key in ("PFI_DATA_HOME", "PFI_V021_RUNTIME_API_PORT", "PFI_STAGE1_CANDIDATE_MODE")
    }
    os.environ["PFI_DATA_HOME"] = str(isolated_data_home)
    os.environ["PFI_V021_RUNTIME_API_PORT"] = "0"
    os.environ["PFI_STAGE1_CANDIDATE_MODE"] = "0"
    try:
        helpers = _load_browser_helpers()
        markup = helpers._offline_formal_shell_html({})
        from pfi_v02 import stage_v021_runtime_api as runtime_api

        api_url_before = str(runtime_api._SERVER_STATE["base_url"])
        api_auth_token_before = str(runtime_api._SERVER_STATE["auth_token"])
        markup_path.write_text(
            _runtime_markup(markup, api_url_before, api_auth_token_before), encoding="utf-8"
        )
        handler_type = type("PFIStage7Phase72SpaHandler", (_SpaLoopbackHandler, helpers._QuietLoopbackHandler), {})
        static_server = ThreadingHTTPServer(("127.0.0.1", 0), partial(handler_type, directory=str(temp_dir)))
        static_thread = threading.Thread(
            target=static_server.serve_forever,
            name="pfi-stage7-phase72-loopback",
            daemon=True,
        )
        static_thread.start()
        base_url = f"http://127.0.0.1:{static_server.server_address[1]}"

        _run_browser(
            mode="exercise", base_url=base_url, api_url=api_url_before,
            api_token=api_auth_token_before,
            raw_trace=temp_dir / "browser_trace_exercise_raw.zip",
        )
        exercise = json.loads((REPORT_DIR / "playwright_exercise.json").read_text(encoding="utf-8"))
        before_restart = _db_snapshot(db_path)

        _shutdown_runtime_server()
        api_url_after = runtime_api.ensure_v021_runtime_api_server(db_path=db_path, port=0)
        api_auth_token_after = str(runtime_api._SERVER_STATE["auth_token"])
        markup_path.write_text(
            _runtime_markup(markup, api_url_after, api_auth_token_after), encoding="utf-8"
        )
        _run_browser(
            mode="restart", base_url=base_url, api_url=api_url_after,
            api_token=api_auth_token_after,
            raw_trace=temp_dir / "browser_trace_restart_raw.zip",
        )
        result = json.loads((REPORT_DIR / "playwright_result.json").read_text(encoding="utf-8"))
        after_restart = _db_snapshot(db_path)
    finally:
        if static_server is not None:
            static_server.shutdown()
            static_server.server_close()
        if static_thread is not None:
            static_thread.join(timeout=5)
        try:
            _shutdown_runtime_server()
        except (ImportError, AttributeError):
            pass
        for key, value in original_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    expected_before = (
        before_restart.get("record_counts") == {"active": 1, "deleted": 0}
        and before_restart.get("table_counts", {}).get("v025_holding_events") == 2
        and before_restart.get("table_counts", {}).get("v025_holding_change_sets") == 2
        and before_restart.get("table_counts", {}).get("v025_settings_events") == 1
        and before_restart.get("holding_revisions") == [2]
        and before_restart.get("settings_revisions") == [1]
    )
    expected_after = (
        after_restart.get("record_counts") == {"active": 0, "deleted": 1}
        and after_restart.get("table_counts", {}).get("v025_holding_events") == 3
        and after_restart.get("table_counts", {}).get("v025_holding_change_sets") == 3
        and after_restart.get("table_counts", {}).get("v025_settings_events") == 2
        and after_restart.get("operation_counts") == {"create": 1, "delete": 1, "update": 1}
        and after_restart.get("holding_revisions") == [3]
        and after_restart.get("settings_revisions") == [2]
        and after_restart.get("migration_count") == 1
    )
    db_ok = all(
        snapshot.get("foreign_key_check") == "pass" and snapshot.get("integrity_check") == "ok"
        for snapshot in (before_restart, after_restart)
    )
    browser_checks = result.get("checks") if isinstance(result.get("checks"), dict) else {}
    browser_ok = result.get("status") == "pass" and all(browser_checks.values())
    overall_status = "pass" if exercise.get("status") == "pass" and browser_ok and expected_before and expected_after and db_ok else "fail"
    exercise_trace_privacy = sanitize_playwright_trace(
        temp_dir / "browser_trace_exercise_raw.zip",
        REPORT_DIR / "browser_trace_sanitized.zip",
        auth_tokens=(api_auth_token_before,),
        private_payloads=HOLDING_TRACE_PRIVATE_LITERALS,
    )
    restart_trace_privacy = sanitize_playwright_trace(
        temp_dir / "browser_trace_restart_raw.zip",
        REPORT_DIR / "browser_trace_restart_sanitized.zip",
        auth_tokens=(api_auth_token_after,),
        private_payloads=HOLDING_TRACE_PRIVATE_LITERALS,
    )
    (temp_dir / "browser_trace_exercise_raw.zip").unlink(missing_ok=True)
    (temp_dir / "browser_trace_restart_raw.zip").unlink(missing_ok=True)

    browser_validation = {
        "schema": "PFIV025Stage7Phase72BrowserValidationV1",
        "status": overall_status,
        "acceptance_id": "ACC-PFI-V025-S7-P72-HOLDINGS-SETTINGS",
        "method": "cached_playwright_formal_shell_isolated_sqlite_browser_and_service_restart",
        "checks": browser_checks,
        "exercise_checks": exercise.get("checks", {}),
        "console_errors": result.get("console_errors", []),
        "page_errors": result.get("page_errors", []),
        "http_errors": result.get("http_errors", []),
        "blocked_external_requests": result.get("blocked_external_requests", []),
        "runtime_api_port_changed_on_restart": api_url_before != api_url_after,
        "network_scope": "ephemeral_local_loopback_only",
        "external_network_performed": False,
        "browser_context_reopened_after_service_restart": True,
        "screenshots_redacted_before_persistence": True,
        "actual_playwright_traces": [
            "browser_trace_sanitized.zip",
            "browser_trace_restart_sanitized.zip",
        ],
        "trace_privacy_scans": [exercise_trace_privacy, restart_trace_privacy],
        "financial_sentinel_counts_as_real_acceptance": False,
        "private_values_persisted_in_evidence": False,
        "finder_used": False,
    }
    _write_json(REPORT_DIR / "browser_validation.json", browser_validation)
    _write_json(
        REPORT_DIR / "holding_db_before_after.json",
        {
            "schema": "PFIV025Stage7Phase72HoldingDatabaseBeforeAfterV1",
            "status": "pass" if expected_before and expected_after else "fail",
            "before_service_restart": before_restart,
            "after_delete_and_settings_reset": after_restart,
            "sentinel_identity_persisted_in_evidence": False,
            "financial_values_persisted_in_evidence": False,
        },
    )
    _write_json(
        REPORT_DIR / "restart_persistence.json",
        {
            "schema": "PFIV025Stage7Phase72RestartPersistenceV1",
            "status": "pass" if browser_ok and expected_before else "fail",
            "browser_reopened": True,
            "runtime_service_restarted": True,
            "runtime_api_port_changed": api_url_before != api_url_after,
            "holding_revision_after_restart": result.get("revision_after_restart"),
            "projection_hash_stable_across_restart": browser_checks.get("service_restart_projection_hash_same"),
            "settings_revision_after_restart": result.get("settings_revision_after_restart"),
        },
    )
    _write_json(
        REPORT_DIR / "settings_persistence.json",
        {
            "schema": "PFIV025Stage7Phase72SettingsPersistenceV1",
            "status": "pass" if browser_checks.get("browser_reopen_settings_persisted") and expected_after else "fail",
            "settings_surface_scope": "settings_only",
            "revision_before_restart": exercise.get("settings_revision"),
            "revision_after_restart": result.get("settings_revision_after_restart"),
            "revision_after_reset": result.get("settings_revision_after_reset"),
            "browser_storage_used_for_formal_settings": False,
        },
    )
    _write_json(
        REPORT_DIR / "db_integrity.json",
        {
            "schema": "PFIV025Stage7Phase72DatabaseIntegrityV1",
            "status": "pass" if db_ok else "fail",
            "before_service_restart": before_restart,
            "after_service_restart": after_restart,
        },
    )


    artifact_hashes = {
        name: _sha256(REPORT_DIR / name)
        for name in BROWSER_ARTIFACT_NAMES
        if (REPORT_DIR / name).is_file()
    }
    _write_json(
        REPORT_DIR / "artifact_hashes.json",
        {
            "schema": "PFIV025Stage7Phase72ArtifactHashesV1",
            "status": overall_status,
            "sha256": artifact_hashes,
        },
    )
    print(
        json.dumps(
            {
                "status": overall_status,
                "browser_check_count": len(browser_checks),
                "exercise_check_count": len(exercise.get("checks", {})),
                "db_before_expected": expected_before,
                "db_after_expected": expected_after,
                "db_integrity": db_ok,
                "finder_used": False,
            },
            ensure_ascii=False,
        )
    )
    return 0 if overall_status == "pass" else 2


def main() -> int:
    temp_dir = Path(tempfile.mkdtemp(prefix="pfi-stage7-phase72-", dir="/tmp"))
    try:
        return _run(temp_dir)
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
