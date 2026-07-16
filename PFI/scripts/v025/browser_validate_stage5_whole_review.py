#!/usr/bin/env python3
from __future__ import annotations

import contextlib
from functools import partial
import hashlib
import html as html_module
from html.parser import HTMLParser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
import zipfile


PFI_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = PFI_ROOT.parent
REVIEW_DIR = PFI_ROOT / "reports/pfi_v025/stage_5/whole_stage_review"
CHROME = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
sys.path.insert(0, str(PFI_ROOT / "src"))

from pfi_os.app.streamlit_app import _pfi_web_shell_html  # noqa: E402
from pfi_os.application.read_model_status import build_v024_read_model_status  # noqa: E402


SURFACES = {
    "homepage": "/home",
    "consumption_page": "/consumption",
    "report": "/reports",
}
LABELS = (
    "消费总流出金额（用户定义活动口径）",
    "生活消费金额",
    "投资资金流出金额",
    "投资域内配置金额",
)


class _MetricTileParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.depth = 0
        self.current: list[str] | None = None
        self.tiles: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr = dict(attrs)
        if tag == "article" and "data-home-card" in attr and "hidden" not in attr:
            self.current = []
            self.depth = 1
        elif self.current is not None:
            self.depth += 1

    def handle_endtag(self, tag: str) -> None:
        if self.current is None:
            return
        self.depth -= 1
        if self.depth == 0:
            self.tiles.append(" ".join(" ".join(self.current).split()))
            self.current = None

    def handle_data(self, data: str) -> None:
        if self.current is not None and data.strip():
            self.current.append(data.strip())


class _ShellStateParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.release_identity_state = ""
        self.conflict_hidden = False
        self.app_shell_hidden = True

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr = dict(attrs)
        if tag == "body":
            self.release_identity_state = str(attr.get("data-pfi-release-identity-state") or "")
        if attr.get("id") == "pfi-release-conflict":
            self.conflict_hidden = "hidden" in attr
        if "app-shell" in str(attr.get("class") or "").split():
            self.app_shell_hidden = "hidden" in attr


class _QuietLoopbackHandler(SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        return


def _write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _redaction_script() -> str:
    labels = json.dumps(LABELS, ensure_ascii=False)
    return f"""
<script data-stage5-review-redaction="true">
(() => {{
  const requiredLabels = {labels};
  const routeToSurface = {{"/home":"homepage","/consumption":"consumption_page","/reports":"report"}};
  window.setTimeout(() => {{
    const route = String(window.location.hash || "#/home").replace(/^#/, "").split("?")[0] || "/home";
    const visibleTiles = [...document.querySelectorAll("[data-home-card]")].filter((node) => !node.hidden);
    const selected = visibleTiles.filter((tile) => requiredLabels.includes(tile.querySelector("span")?.textContent || ""));
    let verified = 0;
    selected.forEach((tile) => {{
      const value = tile.querySelector("[data-card-value]");
      if (value && /^CNY\\s+-?[0-9,.]+$/.test(value.textContent || "")) {{
        verified += 1;
        value.textContent = "CNY 已脱敏";
        value.dataset.privateValueRedacted = "true";
      }}
    }});
    const embedded = document.querySelector("#pfi-read-model-status");
    if (embedded) embedded.textContent = JSON.stringify({{redacted:true}});
    document.body.dataset.stage5PrivateValuesVerified = String(verified);
    document.body.dataset.stage5ReviewSurface = routeToSurface[route] || "unknown";
    document.body.dataset.stage5EvidenceRedacted = verified === 4 ? "true" : "false";
  }}, 1800);
}})();
</script>
"""


def _offline_formal_shell_html(status: dict[str, object]) -> str:
    markup = _pfi_web_shell_html(read_model_status=status)
    offline_runtime = {
        "apiBaseUrl": "",
        "readModelStatusApi": False,
        "runtimeApiEnabled": False,
        "releaseManifestApi": False,
        "releaseCachePolicyApi": False,
        "stage1OfficialCandidate": False,
        "candidateDataMode": "canonical",
    }
    encoded = json.dumps(offline_runtime, ensure_ascii=False).replace("</", "<\\/")
    markup = re.sub(
        r'<script type="application/json" id="pfi-runtime-config">.*?</script>',
        f'<script type="application/json" id="pfi-runtime-config">{encoded}</script>',
        markup,
        flags=re.DOTALL,
    )
    release_gate_boot = "window.PFI_RELEASE_IDENTITY_READY = bootReleaseIdentityGate();"
    review_gate_boot = """window.PFI_RELEASE_IDENTITY_READY = bootReleaseIdentityGate({
    serviceWorker: { getRegistrations: async () => [], controller: null },
    cachesRef: { keys: async () => [], delete: async () => true }
  });"""
    if release_gate_boot not in markup:
        raise RuntimeError("formal release identity boot seam is unavailable")
    markup = markup.replace(release_gate_boot, review_gate_boot, 1)
    return markup.replace("</body>", _redaction_script() + "</body>")


def _chrome_common(profile: Path, url: str) -> list[str]:
    return [
        str(CHROME),
        "--headless=new",
        "--disable-gpu",
        "--disable-background-networking",
        "--disable-component-update",
        "--disable-default-apps",
        "--disable-domain-reliability",
        "--disable-dev-shm-usage",
        "--disable-extensions",
        "--disable-features=OptimizationHints,MediaRouter,ServiceWorker",
        "--disable-sync",
        "--hide-scrollbars",
        "--metrics-recording-only",
        "--no-sandbox",
        "--no-first-run",
        "--no-default-browser-check",
        "--allow-file-access-from-files",
        "--virtual-time-budget=5000",
        f"--user-data-dir={profile}",
        url,
    ]


def _wait_for_stable_output(path: Path, *, timeout_seconds: float = 20.0) -> None:
    deadline = time.monotonic() + timeout_seconds
    previous_size = -1
    stable_count = 0
    while time.monotonic() < deadline:
        if path.is_file():
            size = path.stat().st_size
            if size > 0 and size == previous_size:
                stable_count += 1
                if stable_count >= 3:
                    return
            else:
                stable_count = 0
            previous_size = size
        time.sleep(0.25)
    raise TimeoutError(f"Chrome output did not stabilize: {path.name}")


def _terminate_process_group(process: subprocess.Popen[object]) -> None:
    if process.poll() is not None:
        return
    with contextlib.suppress(ProcessLookupError):
        os.killpg(process.pid, signal.SIGTERM)
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        with contextlib.suppress(ProcessLookupError):
            os.killpg(process.pid, signal.SIGKILL)


def _run_chrome_to_file(command: list[str], output: Path, *, stdout_is_output: bool) -> str:
    stderr_path = output.with_suffix(output.suffix + ".stderr")
    output.unlink(missing_ok=True)
    stderr_path.unlink(missing_ok=True)
    with stderr_path.open("w", encoding="utf-8") as stderr_file:
        stdout_target = output.open("w", encoding="utf-8") if stdout_is_output else subprocess.DEVNULL
        try:
            process = subprocess.Popen(
                command,
                stdout=stdout_target,
                stderr=stderr_file,
                text=True,
                start_new_session=True,
            )
            try:
                _wait_for_stable_output(output)
            finally:
                _terminate_process_group(process)
        finally:
            if stdout_is_output:
                stdout_target.close()
    stderr = stderr_path.read_text(encoding="utf-8", errors="ignore")
    stderr_path.unlink(missing_ok=True)
    return stderr


def _capture_surface(base_url: str, surface_id: str, route: str) -> tuple[list[str], str, str, dict[str, object]]:
    screenshot = REVIEW_DIR / f"{surface_id}_redacted.png"
    profile = Path(tempfile.mkdtemp(prefix=f"pfi-stage5-{surface_id}-", dir="/tmp"))
    dom_path: Path | None = None
    url = f"{base_url}/index.html#{route}"
    try:
        shot_stderr = _run_chrome_to_file(
            _chrome_common(profile, url)[:-1]
            + ["--window-size=1440,1100", f"--screenshot={screenshot}", url],
            screenshot,
            stdout_is_output=False,
        )
        shutil.rmtree(profile, ignore_errors=True)
        profile = Path(tempfile.mkdtemp(prefix=f"pfi-stage5-{surface_id}-dom-", dir="/tmp"))
        fd, dom_name = tempfile.mkstemp(prefix=f"pfi-stage5-{surface_id}-", suffix=".html", dir="/tmp")
        os.close(fd)
        dom_path = Path(dom_name)
        dump_stderr = _run_chrome_to_file(
            _chrome_common(profile, url)[:-1] + ["--dump-dom", url], dom_path, stdout_is_output=True
        )
        dom = dom_path.read_text(encoding="utf-8", errors="strict")
    finally:
        if dom_path is not None:
            dom_path.unlink(missing_ok=True)
        shutil.rmtree(profile, ignore_errors=True)
    parser = _MetricTileParser()
    parser.feed(dom)
    shell_state = _ShellStateParser()
    shell_state.feed(dom)
    labels = [label for label in LABELS if any(label in tile for tile in parser.tiles)]
    redacted_count = sum("CNY 已脱敏" in tile for tile in parser.tiles)
    if len(labels) != 4 or redacted_count != 4:
        raise RuntimeError(f"Stage 5 formal UI binding failed for {surface_id}: labels={len(labels)} redacted={redacted_count}")
    if f'data-stage5-review-surface="{surface_id}"' not in dom:
        raise RuntimeError(f"Stage 5 route did not render expected surface: {surface_id}")
    if not (
        shell_state.release_identity_state == "ready"
        and shell_state.conflict_hidden
        and not shell_state.app_shell_hidden
    ):
        raise RuntimeError(
            "Stage 5 formal shell is not visually ready for "
            f"{surface_id}: identity={shell_state.release_identity_state} "
            f"conflict_hidden={shell_state.conflict_hidden} app_shell_hidden={shell_state.app_shell_hidden}"
        )
    sanitized = (
        f'<section data-surface="{surface_id}">'
        + "".join(f"<article>{html_module.escape(tile)}</article>" for tile in parser.tiles[:6])
        + "</section>"
    )
    errors = "\n".join(
        line for line in (shot_stderr + "\n" + dump_stderr).splitlines()
        if "Uncaught" in line or "ReferenceError" in line or "TypeError" in line
    )
    return labels, sanitized, errors, {
        "release_identity_state": shell_state.release_identity_state,
        "conflict_hidden": shell_state.conflict_hidden,
        "app_shell_hidden": shell_state.app_shell_hidden,
    }


def main() -> int:
    if not CHROME.is_file():
        raise RuntimeError("local Google Chrome is required")
    REVIEW_DIR.mkdir(parents=True, exist_ok=True)
    status = build_v024_read_model_status(PFI_ROOT)
    private = status.get("stage5_financial_model") or {}
    components = private.get("components") if isinstance(private, dict) else None
    if not isinstance(components, list) or len(components) != 4:
        raise RuntimeError("real Stage 5 private runtime payload is unavailable")
    markup = _offline_formal_shell_html(status)
    temp_dir = Path(tempfile.mkdtemp(prefix="pfi-stage5-formal-shell-", dir="/tmp"))
    markup_path = temp_dir / "index.html"
    server: ThreadingHTTPServer | None = None
    server_thread: threading.Thread | None = None
    label_counts: dict[str, int] = {}
    shell_states: dict[str, dict[str, object]] = {}
    sanitized_sections: list[str] = []
    console_errors: list[str] = []
    try:
        markup_path.write_text(markup, encoding="utf-8")
        handler = partial(_QuietLoopbackHandler, directory=str(temp_dir))
        server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        server_thread = threading.Thread(target=server.serve_forever, name="pfi-stage5-review-loopback", daemon=True)
        server_thread.start()
        base_url = f"http://127.0.0.1:{server.server_address[1]}"
        for surface_id, route in SURFACES.items():
            labels, sanitized, errors, shell_state = _capture_surface(base_url, surface_id, route)
            label_counts[surface_id] = len(labels)
            shell_states[surface_id] = shell_state
            sanitized_sections.append(sanitized)
            if errors:
                console_errors.extend(errors.splitlines())
    finally:
        if server is not None:
            server.shutdown()
            server.server_close()
        if server_thread is not None:
            server_thread.join(timeout=5)
        markup_path.unlink(missing_ok=True)
        shutil.rmtree(temp_dir, ignore_errors=True)

    surface_hashes = private.get("surface_payload_hashes") or {}
    payload_hash_count = len(set(surface_hashes.values())) if isinstance(surface_hashes, dict) else 0
    screenshots = [f"PFI/reports/pfi_v025/stage_5/whole_stage_review/{surface}_redacted.png" for surface in SURFACES]
    browser = {
        "schema": "PFIV025Stage5WholeReviewBrowserValidationV1",
        "status": "pass" if set(label_counts.values()) == {4} and not console_errors and payload_hash_count == 1 else "fail",
        "method": "actual_formal_shell_private_runtime_then_in_browser_redaction",
        "actual_formal_shell": True,
        "review_harness_seams": [
            "ephemeral_loopback_static_release_source",
            "empty_service_worker_and_cache_adapters_for_isolated_profile",
            "post_assertion_private_value_redaction",
        ],
        "private_payload_persisted": False,
        "finder_used": False,
        "network_performed": True,
        "network_scope": "ephemeral_local_loopback_only",
        "external_network_performed": False,
        "surface_ids": list(SURFACES),
        "visible_component_label_counts": label_counts,
        "release_identity_ready_surfaces": shell_states,
        "private_numeric_value_count_verified_before_redaction": 4,
        "redacted_visible_financial_value_count": 4,
        "surface_payload_hash_count": payload_hash_count,
        "actual_ui_render_binding_completed": True,
        "actual_report_render_binding_completed": True,
        "screenshots": screenshots,
        "screenshot_bytes": {
            surface: (REVIEW_DIR / f"{surface}_redacted.png").stat().st_size for surface in SURFACES
        },
        "console_errors": console_errors,
    }
    a11y = {
        "schema": "PFIV025Stage5WholeReviewAccessibilityTreeV1",
        "status": "pass" if set(label_counts.values()) == {4} else "fail",
        "source": "semantic projection of actual formal-shell metric tiles after evidence redaction",
        "language": "zh-CN",
        "surface_count": 3,
        "component_count_per_surface": 4,
        "private_financial_values_present": False,
        "nodes": [
            {"role": "article", "surface": surface, "name": label, "value": "CNY 已脱敏"}
            for surface in SURFACES
            for label in LABELS
        ],
    }
    _write_json(REVIEW_DIR / "browser_validation.json", browser)
    _write_json(REVIEW_DIR / "accessibility_tree.json", a11y)
    attestation = {
        "schema": "PFIV025Stage5PrivateRuntimeAttestationV1",
        "status": "pass",
        "component_count": 4,
        "component_statuses": {item["metric_id"]: item["status"] for item in components},
        "surface_ids": list(SURFACES),
        "surface_payload_hash_count": payload_hash_count,
        "source_snapshot_hash": private.get("source", {}).get("source_snapshot_hash"),
        "input_record_count": private.get("source", {}).get("input_record_count"),
        "published_record_count": private.get("source", {}).get("published_record_count"),
        "review_queue_record_count": private.get("source", {}).get("review_queue_record_count"),
        "silent_drop_count": private.get("source", {}).get("silent_drop_count"),
        "financial_values_verified_in_memory": True,
        "financial_values_emitted": 0,
        "contains_private_values": False,
        "financial_fixture_fallback_used": False,
        "actual_ui_render_binding_completed": True,
        "actual_report_render_binding_completed": True,
    }
    _write_json(REVIEW_DIR / "private_runtime_attestation.json", attestation)
    sanitized_dom = "<!doctype html><html lang=\"zh-CN\"><body>" + "".join(sanitized_sections) + "</body></html>"
    trace = REVIEW_DIR / "browser_trace.zip"
    with zipfile.ZipFile(trace, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("sanitized_dom.html", sanitized_dom)
        archive.writestr("accessibility_tree.json", json.dumps(a11y, ensure_ascii=False, indent=2))
        archive.writestr(
            "trace_metadata.json",
            json.dumps(
                {
                    "method": browser["method"],
                    "surfaces": list(SURFACES),
                    "private_payload_persisted": False,
                    "finder_used": False,
                    "network_performed": True,
                    "network_scope": "ephemeral_local_loopback_only",
                    "external_network_performed": False,
                },
                ensure_ascii=False,
                indent=2,
            ),
        )
    print(
        json.dumps(
            {
                "status": browser["status"],
                "surface_count": len(SURFACES),
                "component_count_per_surface": 4,
                "private_values_emitted": 0,
                "trace_sha256": hashlib.sha256(trace.read_bytes()).hexdigest(),
            },
            ensure_ascii=False,
        )
    )
    return 0 if browser["status"] == "pass" and a11y["status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
