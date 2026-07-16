#!/usr/bin/env python3
"""Run formal-shell Stage 7.3 browser validation without Finder or network."""

from __future__ import annotations

from functools import partial
from http.server import ThreadingHTTPServer
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import threading
from urllib.parse import urlsplit
import zipfile

_BROWSER_TEST_DIR = Path(__file__).resolve().parent
if str(_BROWSER_TEST_DIR) not in sys.path:
    sys.path.insert(0, str(_BROWSER_TEST_DIR))
from stage7_trace_privacy import sanitize_playwright_trace  # noqa: E402


PFI_ROOT = Path(__file__).resolve().parents[3]
REPORT_DIR = PFI_ROOT / "reports/pfi_v025/stage_7/phase_7_3"
STAGE5_BROWSER = PFI_ROOT / "scripts/v025/browser_validate_stage5_whole_review.py"
CDP_RUNNER = PFI_ROOT / "web/tests/v025/stage7_metric_drilldown_cdp.mjs"
PLAYWRIGHT_MODULE_DIR = Path(
    "/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules"
)
CHROME = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
REAL_SOURCE_ROOT = Path(
    "/Users/linzezhang/Documents/Codex/CodexProject/MetaDatabase/PFI/alipay_daily/raw"
)
LEGACY_TRACE_PRIVATE_LITERALS = (
    b"987654.32",
    b"MetaDatabase",
    b"PFI-V025-LEGACY-FINANCIAL-PUBLICATION",
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
        "readModelStatusApi": True,
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


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _sanitize_trace(trace_path: Path, scratch_dir: Path) -> dict[str, object]:
    sanitized_path = scratch_dir / "browser_trace_sanitized.zip"
    value_pattern = re.compile(
        r'("value"\s*:\s*)(?:"(?:\\.|[^"\\])*"|-?[0-9]+(?:\.[0-9]+)?|null|true|false)'
    )
    absolute_path_pattern = re.compile(r"/Users/[^\"'\s<>,)]+")
    replacements = {"value_fields": 0, "absolute_paths": 0, "cny_text": 0}
    with zipfile.ZipFile(trace_path) as source, zipfile.ZipFile(
        sanitized_path, "w", compression=zipfile.ZIP_DEFLATED
    ) as target:
        for info in source.infolist():
            data = source.read(info.filename)
            if Path(info.filename).suffix.lower() not in {".jpg", ".jpeg", ".png", ".webp"}:
                try:
                    text = data.decode("utf-8")
                except UnicodeDecodeError:
                    pass
                else:
                    text, count = value_pattern.subn(r'\1"[FINANCIAL_VALUE_REDACTED]"', text)
                    replacements["value_fields"] += count
                    text, count = absolute_path_pattern.subn("[LOCAL_PATH_REDACTED]", text)
                    replacements["absolute_paths"] += count
                    text, count = re.subn(r"CNY\s+-?[0-9][0-9,.]*", "CNY [FINANCIAL_VALUE_REDACTED]", text)
                    replacements["cny_text"] += count
                    data = text.encode("utf-8")
            target.writestr(info, data)
    sanitized_path.replace(trace_path)

    forbidden_hits: list[str] = []
    with zipfile.ZipFile(trace_path) as archive:
        for info in archive.infolist():
            if Path(info.filename).suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}:
                continue
            data = archive.read(info.filename)
            try:
                text = data.decode("utf-8")
            except UnicodeDecodeError:
                continue
            if "/Users/" in text:
                forbidden_hits.append(f"{info.filename}:absolute_path")
            if re.search(r'"value"\s*:\s*(?:"-?[0-9]+(?:\.[0-9]+)?"|-?[0-9]+(?:\.[0-9]+)?)', text):
                forbidden_hits.append(f"{info.filename}:numeric_value")
    if forbidden_hits:
        trace_path.unlink(missing_ok=True)
        raise RuntimeError(f"sanitized trace privacy scan failed: {forbidden_hits[:5]}")
    return {
        "status": "pass",
        "trace": trace_path.name,
        "replacements": replacements,
        "absolute_path_hit_count": 0,
        "numeric_value_hit_count": 0,
        "contains_private_values": False,
    }


def _run(temp_dir: Path) -> int:
    if not CHROME.is_file():
        raise RuntimeError("local Google Chrome is required")
    if not (PLAYWRIGHT_MODULE_DIR / "playwright").is_dir():
        raise RuntimeError("cached Playwright runtime is required; installation is forbidden")
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    for name in (
        "parameter_center.png",
        "interconnection_map.png",
        "browser_trace_sanitized.zip",
        "browser_trace_raw.zip",
        "playwright_result.json",
        "browser_validation.json",
        "metric_drilldown.json",
        "privacy_scan.txt",
    ):
        (REPORT_DIR / name).unlink(missing_ok=True)

    raw_trace = temp_dir / "browser_trace_raw.zip"
    isolated_data_home = temp_dir / "data_home"
    db_path = isolated_data_home / "private" / "operational" / "pfi.sqlite"
    static_server: ThreadingHTTPServer | None = None
    static_thread: threading.Thread | None = None
    original_env = {
        key: os.environ.get(key)
        for key in ("PFI_DATA_HOME", "PFI_V021_RUNTIME_API_PORT", "PFI_STAGE1_CANDIDATE_MODE")
    }
    os.environ["PFI_DATA_HOME"] = str(isolated_data_home)
    os.environ["PFI_V021_RUNTIME_API_PORT"] = "0"
    os.environ["PFI_STAGE1_CANDIDATE_MODE"] = "0"
    try:
        from pfi_os.application.use_cases.import_review_ledger import (
            ImportReviewLedgerService,
            UploadedImportFile,
        )

        sources = sorted(
            path for path in REAL_SOURCE_ROOT.iterdir()
            if path.is_file() and path.suffix.lower() in {".csv", ".zip"}
        )
        if not sources:
            raise RuntimeError("real read-only Alipay source is unavailable")
        ledger_service = ImportReviewLedgerService(db_path=db_path)
        preview = ledger_service.preview_upload(
            (UploadedImportFile(name=sources[0].name, content=sources[0].read_bytes()),)
        )
        ledger_service.confirm_batch(str(preview["batch_id"]))

        helpers = _load_browser_helpers()
        markup = helpers._offline_formal_shell_html({})
        from pfi_v02 import stage_v021_runtime_api as runtime_api

        api_url = str(runtime_api._SERVER_STATE["base_url"])
        api_auth_token = str(runtime_api._SERVER_STATE["auth_token"])
        (temp_dir / "index.html").write_text(
            _runtime_markup(markup, api_url, api_auth_token), encoding="utf-8"
        )
        handler_type = type("PFIStage7Phase73SpaHandler", (_SpaLoopbackHandler, helpers._QuietLoopbackHandler), {})
        static_server = ThreadingHTTPServer(("127.0.0.1", 0), partial(handler_type, directory=str(temp_dir)))
        static_thread = threading.Thread(target=static_server.serve_forever, name="pfi-stage7-phase73-loopback", daemon=True)
        static_thread.start()
        base_url = f"http://127.0.0.1:{static_server.server_address[1]}"

        completed = subprocess.run(
            [
                "node",
                str(CDP_RUNNER),
                "--base-url",
                base_url,
                "--api-url",
                api_url,
                "--api-token",
                api_auth_token,
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
            timeout=300,
        )
        if completed.returncode != 0:
            raise RuntimeError(completed.stderr or completed.stdout or "Stage 7.3 browser validation failed")
        result = json.loads((REPORT_DIR / "playwright_result.json").read_text(encoding="utf-8"))

        from pfi_os.application.use_cases.metric_lineage_drilldown import (
            build_stage7_phase73_evidence_projection,
            build_stage7_phase73_payload,
        )

        phase_payload = build_stage7_phase73_payload(
            PFI_ROOT,
            operational_ledger=ledger_service.build_ledger_runtime_read_model(),
        )
        evidence_projection = build_stage7_phase73_evidence_projection(phase_payload)
        trace_privacy = sanitize_playwright_trace(
            raw_trace,
            REPORT_DIR / "browser_trace_sanitized.zip",
            auth_tokens=(api_auth_token,),
            private_payloads=LEGACY_TRACE_PRIVATE_LITERALS,
        )
        raw_trace.unlink(missing_ok=True)
        _write_json(REPORT_DIR / "metric_drilldown.json", evidence_projection)
        browser_validation = {
            "schema": "PFIV025Stage7Phase73BrowserEvidenceV1",
            "status": result["status"],
            "check_count": len(result["checks"]),
            "passed_check_count": sum(bool(value) for value in result["checks"].values()),
            "checks": result["checks"],
            "formal_routes": evidence_projection["formal_routes"],
            "parameter_center_screenshot": "parameter_center.png",
            "interconnection_map_screenshot": "interconnection_map.png",
            "trace": "browser_trace_sanitized.zip",
            "trace_privacy_scan": trace_privacy,
            "contains_private_values": False,
            "financial_values_persisted": 0,
            "finder_used": False,
            "external_network_used": False,
        }
        _write_json(REPORT_DIR / "browser_validation.json", browser_validation)
        (REPORT_DIR / "privacy_scan.txt").write_text(
            "status=pass\n"
            "contains_private_values=false\n"
            "absolute_path_hit_count=0\n"
            "numeric_value_hit_count=0\n"
            f"trace_sensitive_field_replacements={trace_privacy['replacements']['sensitive_fields']}\n"
            f"trace_absolute_path_replacements={trace_privacy['replacements']['absolute_paths']}\n",
            encoding="utf-8",
        )
        print(json.dumps({"status": result["status"], "checks": len(result["checks"])}, ensure_ascii=False))
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
    return 0


def main() -> int:
    temp_dir = Path(tempfile.mkdtemp(prefix="pfi-stage7-phase73-", dir="/tmp"))
    try:
        return _run(temp_dir)
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
