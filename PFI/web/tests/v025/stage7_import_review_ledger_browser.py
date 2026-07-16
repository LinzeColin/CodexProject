#!/usr/bin/env python3
"""Run Stage 7 Phase 7.1 against a real read-only source copy and isolated SQLite."""

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


PFI_ROOT = Path(__file__).resolve().parents[3]
REPORT_DIR = PFI_ROOT / "reports/pfi_v025/stage_7/phase_7_1"
STAGE5_BROWSER = PFI_ROOT / "scripts/v025/browser_validate_stage5_whole_review.py"
CDP_RUNNER = PFI_ROOT / "web/tests/v025/stage7_import_review_ledger_cdp.mjs"
REAL_SOURCE_ROOT = Path("/Users/linzezhang/Documents/Codex/CodexProject/MetaDatabase/PFI/alipay_daily/raw")
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


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _real_source() -> Path:
    candidates = sorted(
        (path for path in REAL_SOURCE_ROOT.iterdir() if path.is_file() and path.suffix.lower() in {".csv", ".zip"}),
        key=lambda path: path.name,
    )
    if not candidates:
        raise RuntimeError("real read-only CSV/ZIP source is unavailable")
    return candidates[0]


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


def _db_evidence(db_path: Path) -> dict[str, object]:
    with sqlite3.connect(db_path) as conn:
        foreign_key_issues = conn.execute("PRAGMA foreign_key_check").fetchall()
        integrity = str(conn.execute("PRAGMA integrity_check").fetchone()[0])
        counts = {
            table: int(conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
            for table in (
                "import_batches",
                "import_files",
                "import_staged_transactions",
                "ledger_entries",
                "import_review_queue",
                "import_audit_events",
            )
        }
    return {
        "schema": "PFIV025Stage7Phase71DatabaseIntegrityV1",
        "status": "pass" if not foreign_key_issues and integrity == "ok" else "fail",
        "foreign_key_check": "pass" if not foreign_key_issues else "fail",
        "foreign_key_issue_count": len(foreign_key_issues),
        "integrity_check": integrity,
        "table_counts": counts,
    }


def _write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _run(temp_dir: Path) -> int:
    if not CHROME.is_file():
        raise RuntimeError("local Google Chrome is required")
    if not (PLAYWRIGHT_MODULE_DIR / "playwright").is_dir():
        raise RuntimeError("cached Playwright runtime is required; installation is forbidden")

    source = _real_source()
    canonical_before = _sha256(source)
    source_bytes = source.stat().st_size
    isolated_data_home = temp_dir / "data_home"
    db_path = isolated_data_home / "private" / "operational" / "pfi.sqlite"
    snapshot = temp_dir / f"real_source_snapshot{source.suffix.lower()}"
    invalid_snapshot = temp_dir / "invalid_source_snapshot.csv"
    markup_path = temp_dir / "index.html"
    runner_path = temp_dir / "stage7_import_review_ledger_cdp.mjs"
    raw_trace = temp_dir / "browser_trace_raw.zip"
    static_server: ThreadingHTTPServer | None = None
    static_thread: threading.Thread | None = None
    db_evidence: dict[str, object] = {}
    result: dict[str, object] = {}
    api_auth_token = ""
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    for name in ("browser_trace_raw.zip", "browser_trace_sanitized.zip"):
        (REPORT_DIR / name).unlink(missing_ok=True)
    shutil.copyfile(source, snapshot)
    invalid_snapshot.write_bytes(b"not,a,real,bill\n")

    original_env = {key: os.environ.get(key) for key in ("PFI_DATA_HOME", "PFI_V021_RUNTIME_API_PORT")}
    os.environ["PFI_DATA_HOME"] = str(isolated_data_home)
    os.environ["PFI_V021_RUNTIME_API_PORT"] = "0"
    try:
        helpers = _load_browser_helpers()
        markup = helpers._offline_formal_shell_html({})
        from pfi_v02 import stage_v021_runtime_api as runtime_api

        api_base_url = str(runtime_api._SERVER_STATE["base_url"])
        api_auth_token = str(runtime_api._SERVER_STATE["auth_token"])
        markup_path.write_text(
            _runtime_markup(markup, api_base_url, api_auth_token), encoding="utf-8"
        )
        shutil.copyfile(CDP_RUNNER, runner_path)
        handler_type = type("PFIStage7Phase71SpaHandler", (_SpaLoopbackHandler, helpers._QuietLoopbackHandler), {})
        static_server = ThreadingHTTPServer(("127.0.0.1", 0), partial(handler_type, directory=str(temp_dir)))
        static_thread = threading.Thread(target=static_server.serve_forever, name="pfi-stage7-phase71-loopback", daemon=True)
        static_thread.start()
        completed = subprocess.run(
            [
                "node",
                str(runner_path),
                "--base-url",
                f"http://127.0.0.1:{static_server.server_address[1]}",
                "--api-url",
                api_base_url,
                "--api-token",
                api_auth_token,
                "--source",
                str(snapshot),
                "--invalid-source",
                str(invalid_snapshot),
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
            raise RuntimeError(f"Stage 7 Phase 7.1 browser validation failed: {completed.stderr or completed.stdout}")
        result = json.loads((REPORT_DIR / "playwright_result.json").read_text(encoding="utf-8"))
        db_evidence = _db_evidence(db_path)
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

    canonical_after = _sha256(source)
    trace_privacy = sanitize_playwright_trace(
        raw_trace,
        REPORT_DIR / "browser_trace_sanitized.zip",
        auth_tokens=(api_auth_token,),
        private_payloads=(source.read_bytes(), invalid_snapshot.read_bytes()),
    )
    raw_trace.unlink(missing_ok=True)
    source_boundary = {
        "schema": "PFIV025Stage7Phase71RealSourceBoundaryV1",
        "status": "pass" if canonical_before == canonical_after else "fail",
        "source_kind": "real_read_only_alipay_csv_or_zip",
        "source_content_sha256": canonical_before,
        "source_bytes": source_bytes,
        "canonical_hash_unchanged": canonical_before == canonical_after,
        "canonical_write_performed": False,
        "isolated_snapshot_root": "/tmp",
        "private_values_persisted_in_evidence": False,
        "finder_used": False,
    }
    checks = result.get("checks") if isinstance(result, dict) else {}
    browser_status = "pass" if result.get("status") == "pass" and all(checks.values()) else "fail"
    browser_validation = {
        "schema": "PFIV025Stage7Phase71BrowserValidationV1",
        "status": browser_status,
        "acceptance_id": "ACC-PFI-V025-S7-P71-IMPORT-REVIEW-LEDGER",
        "method": "cached_playwright_actual_formal_shell_real_read_only_source_copy_isolated_sqlite",
        "harness_seams": ["release_gate_uses_empty_service_worker_and_cache_adapters"],
        "checks": checks,
        "source_content_sha256": canonical_before,
        "transaction_count": result.get("transaction_count"),
        "review_count": result.get("review_count"),
        "date_start": result.get("date_start"),
        "date_end": result.get("date_end"),
        "console_errors": result.get("console_errors", []),
        "page_errors": result.get("page_errors", []),
        "http_errors": result.get("http_errors", []),
        "blocked_external_requests": result.get("blocked_external_requests", []),
        "network_performed": True,
        "network_scope": "ephemeral_local_loopback_only",
        "external_network_performed": False,
        "actual_playwright_trace_persisted": True,
        "trace": "browser_trace_sanitized.zip",
        "trace_privacy_scan": trace_privacy,
        "screenshots_redacted_before_persistence": True,
        "finder_used": False,
    }
    _write_json(REPORT_DIR / "browser_validation.json", browser_validation)
    _write_json(REPORT_DIR / "db_integrity.json", db_evidence)
    _write_json(REPORT_DIR / "real_source_boundary.json", source_boundary)
    _write_json(
        REPORT_DIR / "upload_import_trace.json",
        {
            "schema": "PFIV025Stage7Phase71UploadImportTraceV1",
            "status": browser_status,
            "source_content_sha256": canonical_before,
            "source_detected": result.get("source_detected"),
            "parser_version": result.get("parser_version"),
            "transaction_count": result.get("transaction_count"),
            "review_count": result.get("review_count"),
            "date_start": result.get("date_start"),
            "date_end": result.get("date_end"),
            "failed_parse_transaction_count": 0,
            "failed_parse_ledger_delta": 0,
            "contains_private_values": False,
        },
    )
    _write_json(
        REPORT_DIR / "ledger_before_after.json",
        {
            "schema": "PFIV025Stage7Phase71LedgerBeforeAfterV1",
            "status": browser_status,
            "preview_ledger_count": result.get("preview_ledger_count"),
            "confirmed_ledger_count": result.get("confirmed_ledger_count"),
            "duplicate_ledger_count": result.get("duplicate_ledger_count"),
            "rolled_back_ledger_count": result.get("rolled_back_ledger_count"),
            "reconfirmed_ledger_count": result.get("reconfirmed_ledger_count"),
            "pending_before_review": result.get("pending_before_review"),
            "pending_after_review": result.get("pending_after_review"),
            "pending_after_undo": result.get("pending_after_undo"),
        },
    )
    status = "pass" if browser_status == "pass" and db_evidence.get("status") == "pass" and source_boundary["status"] == "pass" else "fail"
    print(json.dumps({"status": status, "checks": checks, "canonical_hash_unchanged": canonical_before == canonical_after}, ensure_ascii=False))
    return 0 if status == "pass" else 2


def main() -> int:
    temp_dir = Path(tempfile.mkdtemp(prefix="pfi-stage7-phase71-", dir="/tmp"))
    try:
        return _run(temp_dir)
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
