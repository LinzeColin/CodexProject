#!/usr/bin/env python3
"""Run the Stage 12.1 real-data browser flow on isolated local state only."""

from __future__ import annotations

from functools import partial
from http.server import ThreadingHTTPServer
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import sqlite3
import subprocess
import sys
import tempfile
import threading
from urllib.parse import urlsplit


THIS_DIR = Path(__file__).resolve().parent
if str(THIS_DIR) not in sys.path:
    sys.path.insert(0, str(THIS_DIR))
from stage7_trace_privacy import sanitize_playwright_trace  # noqa: E402


PFI_ROOT = Path(__file__).resolve().parents[3]
REPO_ROOT = PFI_ROOT.parent
SCRIPTS_ROOT = PFI_ROOT / "scripts/v025"
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))
from immutable_real_sources import load_locked_source_objects  # noqa: E402

STAGE5_BROWSER = PFI_ROOT / "scripts/v025/browser_validate_stage5_whole_review.py"
CDP_RUNNER = THIS_DIR / "stage12_real_e2e_cdp.mjs"
PLAYWRIGHT_MODULE_DIR = (
    Path.home()
    / ".cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules"
)
NODE = (
    Path.home()
    / ".cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node"
)
CHROME = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")


def _load_browser_helpers() -> object:
    spec = importlib.util.spec_from_file_location(
        "pfi_stage12_formal_shell_helpers", STAGE5_BROWSER
    )
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


def _git_bytes(*args: str) -> bytes:
    return subprocess.run(
        ["git", "-c", "core.quotePath=false", *args],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
    ).stdout


def _git_text(*args: str) -> str:
    return _git_bytes(*args).decode("utf-8").strip()


def _sha_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _sha_file(path: Path) -> str:
    return _sha_bytes(path.read_bytes())


def _write_json(path: Path, payload: object) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _real_git_sources(temp_root: Path) -> tuple[list[Path], list[bytes], dict[str, object]]:
    temp_root.mkdir(parents=True, exist_ok=True)
    objects, attestation = load_locked_source_objects(repo_root=REPO_ROOT)
    snapshots: list[Path] = []
    payloads: list[bytes] = []
    for row in objects:
        index = int(row["source_index"])
        payload = row["content"]
        if not isinstance(payload, bytes):
            raise RuntimeError("immutable source payload is not bytes")
        snapshot = temp_root / f"real_source_{index}.csv"
        snapshot.write_bytes(payload)
        snapshot.chmod(0o600)
        snapshots.append(snapshot)
        payloads.append(payload)
    browser_attestation = dict(attestation)
    browser_attestation.pop("schema", None)
    browser_attestation.pop("status", None)
    for row in browser_attestation["source_objects"]:
        row["git_object_id"] = row.pop("git_blob_oid")
    return snapshots, payloads, browser_attestation


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
    updated, count = re.subn(
        r'<script type="application/json" id="pfi-runtime-config">.*?</script>',
        f'<script type="application/json" id="pfi-runtime-config">{encoded}</script>',
        markup,
        flags=re.DOTALL,
    )
    if count != 1:
        raise RuntimeError("formal-shell runtime configuration seam is unavailable")
    return updated


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


def _database_evidence(db_path: Path) -> dict[str, object]:
    with sqlite3.connect(db_path) as connection:
        integrity = str(connection.execute("PRAGMA integrity_check").fetchone()[0])
        foreign_key_issue_count = len(
            connection.execute("PRAGMA foreign_key_check").fetchall()
        )
        counts = {
            "import_batch_count": int(
                connection.execute("SELECT COUNT(*) FROM import_batches").fetchone()[0]
            ),
            "import_file_count": int(
                connection.execute("SELECT COUNT(*) FROM import_files").fetchone()[0]
            ),
            "staged_transaction_count": int(
                connection.execute(
                    "SELECT COUNT(*) FROM import_staged_transactions"
                ).fetchone()[0]
            ),
            "ledger_entry_count": int(
                connection.execute("SELECT COUNT(*) FROM ledger_entries").fetchone()[0]
            ),
            "review_item_count": int(
                connection.execute("SELECT COUNT(*) FROM import_review_queue").fetchone()[0]
            ),
            "active_holding_count": int(
                connection.execute(
                    "SELECT COUNT(*) FROM v025_holding_records WHERE status = 'active'"
                ).fetchone()[0]
            ),
        }
    return {
        "schema": "PFIV025Stage12Phase121DatabaseBeforeAfterV1",
        "status": (
            "pass"
            if integrity == "ok" and foreign_key_issue_count == 0
            else "fail"
        ),
        "before": {"database_exists": False, "ledger_entry_count": 0},
        "after": {
            "database_exists": True,
            "integrity_check": integrity,
            "foreign_key_issue_count": foreign_key_issue_count,
            **counts,
        },
        "database_scope": "temporary_isolated_runtime_only",
        "canonical_database_read": False,
        "canonical_database_changed": False,
        "financial_values_emitted": 0,
        "contains_private_values": False,
    }


def run(output_dir: Path) -> dict[str, object]:
    if not CHROME.is_file():
        raise RuntimeError("local headless Chrome is unavailable")
    if not NODE.is_file() or not (PLAYWRIGHT_MODULE_DIR / "playwright").is_dir():
        raise RuntimeError("bundled Playwright runtime is unavailable")
    output_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="pfi-stage12-real-e2e-") as temp_name:
        temp_root = Path(temp_name)
        temp_root.chmod(0o700)
        snapshots, private_payloads, source_contract = _real_git_sources(temp_root)
        source_identity_before = dict(source_contract)
        isolated_data_home = temp_root / "data_home"
        db_path = isolated_data_home / "private/operational/pfi.sqlite"
        markup_path = temp_root / "index.html"
        raw_trace = temp_root / "browser_trace_raw.zip"
        static_server: ThreadingHTTPServer | None = None
        static_thread: threading.Thread | None = None
        api_auth_token = ""
        original_env = {
            key: os.environ.get(key)
            for key in ("PFI_DATA_HOME", "PFI_V021_RUNTIME_API_PORT")
        }
        os.environ["PFI_DATA_HOME"] = str(isolated_data_home)
        os.environ["PFI_V021_RUNTIME_API_PORT"] = "0"
        try:
            helpers = _load_browser_helpers()
            markup = helpers._offline_formal_shell_html({})
            from pfi_v02 import stage_v021_runtime_api as runtime_api

            api_base_url = str(runtime_api._SERVER_STATE["base_url"])
            api_auth_token = str(runtime_api._SERVER_STATE["auth_token"])
            markup_path.write_text(
                _runtime_markup(markup, api_base_url, api_auth_token),
                encoding="utf-8",
            )
            handler_type = type(
                "PFIStage12RealE2ESpaHandler",
                (_SpaLoopbackHandler, helpers._QuietLoopbackHandler),
                {},
            )
            static_server = ThreadingHTTPServer(
                ("127.0.0.1", 0),
                partial(handler_type, directory=str(temp_root)),
            )
            static_thread = threading.Thread(
                target=static_server.serve_forever,
                name="pfi-stage12-real-e2e-loopback",
                daemon=True,
            )
            static_thread.start()
            completed = subprocess.run(
                [
                    str(NODE),
                    str(CDP_RUNNER),
                    "--base-url",
                    f"http://127.0.0.1:{static_server.server_address[1]}",
                    "--api-url",
                    api_base_url,
                    "--api-token",
                    api_auth_token,
                    "--sources-json",
                    json.dumps([str(path) for path in snapshots]),
                    "--output-dir",
                    str(output_dir),
                    "--raw-trace",
                    str(raw_trace),
                    "--chrome",
                    str(CHROME),
                ],
                cwd=REPO_ROOT,
                env={
                    **os.environ,
                    "PFI_PLAYWRIGHT_MODULE_DIR": str(PLAYWRIGHT_MODULE_DIR),
                },
                check=False,
                text=True,
                capture_output=True,
                timeout=300,
            )
            if completed.returncode != 0:
                raise RuntimeError(
                    "Stage 12 real browser E2E failed: "
                    + (completed.stderr or completed.stdout)[-3000:]
                )
            browser_result = json.loads(
                (output_dir / "playwright_result.json").read_text(encoding="utf-8")
            )
            database = _database_evidence(db_path)
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

        trace_privacy = sanitize_playwright_trace(
            raw_trace,
            output_dir / "browser_trace_sanitized.zip",
            auth_tokens=(api_auth_token,),
            private_payloads=private_payloads,
        )
        source_identity_after = _real_git_sources(temp_root / "after")[2]

    source_unchanged = source_identity_before == source_identity_after
    e2e = {
        "schema": "PFIV025Stage12Phase121RealDataE2EV1",
        "status": (
            "pass"
            if browser_result.get("status") == "pass"
            and database.get("status") == "pass"
            and trace_privacy.get("status") == "pass"
            and source_unchanged
            else "fail"
        ),
        "source": {
            **source_identity_before,
            "isolation_mode": "immutable_git_object_to_temporary_0600_snapshot",
            "source_unchanged": source_unchanged,
            "fixture_used": False,
            "fallback_used": False,
        },
        "import": browser_result.get("import"),
        "holding": browser_result.get("holding"),
        "report": browser_result.get("report"),
        "route_regression": browser_result.get("route_regression"),
        "no_false_zero": browser_result.get("no_false_zero"),
        "no_template_clone": browser_result.get("no_template_clone"),
        "database_evidence": "database_before_after.json",
        "trace": "browser_trace_sanitized.zip",
        "trace_sha256": f"sha256:{_sha_file(output_dir / 'browser_trace_sanitized.zip')}",
        "trace_privacy": trace_privacy,
        "actual_playwright_trace": True,
        "network_scope": "ephemeral_loopback_only",
        "external_network_performed": False,
        "canonical_database_read": False,
        "canonical_database_changed": False,
        "financial_values_emitted": 0,
        "contains_private_values": False,
        "contains_absolute_paths": False,
        "finder_used": False,
        "launchservices_used": False,
        "gui_file_operations_used": False,
    }
    browser_validation = {
        "schema": "PFIV025Stage12Phase121BrowserValidationV1",
        "status": browser_result.get("status"),
        "check_count": browser_result.get("check_count"),
        "passed_check_count": browser_result.get("passed_check_count"),
        "checks": browser_result.get("checks"),
        "performance": browser_result.get("performance"),
        "accessibility": browser_result.get("accessibility"),
        "diagnostics": browser_result.get("diagnostics"),
        "screenshots": browser_result.get("screenshots"),
        "loopback_only": True,
        "external_network_performed": False,
        "contains_private_values": False,
        "finder_used": False,
    }
    _write_json(output_dir / "database_before_after.json", database)
    _write_json(output_dir / "real_data_e2e.json", e2e)
    _write_json(output_dir / "browser_validation.json", browser_validation)
    if e2e["status"] != "pass":
        raise RuntimeError("Stage 12 real-data browser evidence failed closed")
    return e2e


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
    print(
        json.dumps(
            {
                "status": result["status"],
                "source_blob_count": result["source"]["source_blob_count"],
                "transaction_count": result["import"]["transaction_count"],
                "holding_execution_status": result["holding"]["execution_status"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
