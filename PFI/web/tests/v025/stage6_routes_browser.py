#!/usr/bin/env python3
from __future__ import annotations

from functools import partial
import hashlib
from html import unescape
from http.server import ThreadingHTTPServer
import importlib.util
import json
from pathlib import Path
import re
import shutil
import tempfile
import threading
import zipfile


PFI_ROOT = Path(__file__).resolve().parents[3]
REPO_ROOT = PFI_ROOT.parent
REPORT_DIR = PFI_ROOT / "reports/pfi_v025/stage_6/phase_6_1"
STAGE5_BROWSER = PFI_ROOT / "scripts/v025/browser_validate_stage5_whole_review.py"


def _load_browser_helpers() -> object:
    spec = importlib.util.spec_from_file_location("pfi_stage5_browser_helpers", STAGE5_BROWSER)
    if spec is None or spec.loader is None:
        raise RuntimeError("formal-shell browser helpers are unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _validation_script() -> str:
    return r"""
<script data-stage6-phase61-browser-validation="true">
window.setTimeout(() => {
  const redactEvidence = () => {
    const textWalker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
    const textNodes = [];
    while (textWalker.nextNode()) textNodes.push(textWalker.currentNode);
    textNodes.forEach((node) => {
      const original = String(node.textContent || "");
      const redacted = original
        .replace(/AUD\/CNY\s*=\s*-?[0-9,.]+/g, "AUD/CNY=未加载")
        .replace(/CNY\s*-?[0-9,.]+/g, "CNY 已脱敏")
        .replace(/AUD\s*-?[0-9,.]+/g, "AUD 已脱敏");
      if (redacted !== original) node.textContent = redacted;
    });
    document.body.dataset.stage6Phase61EvidenceRedacted = "true";
  };
  const registry = window.PFI_V025_STAGE6_ROUTES;
  const entries = [...document.querySelectorAll('[data-primary-entry="true"]')];
  const initialNormalizedHash = decodeURIComponent(String(window.location.hash || "")).replace(/^#/, "");
  const clickedRoutes = [];
  entries.forEach((entry) => {
    entry.click();
    clickedRoutes.push(decodeURIComponent(String(window.location.hash || "")).replace(/^#/, ""));
  });
  entries[0]?.click();
  redactEvidence();
  window.setInterval(redactEvidence, 120);
  const aliases = ["/home", "/market", "/research", "/holdings", "/strategy-lab", "/investment/strategy-lab", "/data-system"];
  const aliasResults = aliases.map((route) => registry?.resolveRouteAlias(route) || {});
  const activeEntries = entries.filter((entry) => entry.classList.contains("is-active"));
  const result = {
    registrySchema: registry?.schema || "",
    contractVersion: registry?.navigationContractVersion || "",
    uniquePrimaryNodeCount: entries.length,
    primaryRoutes: entries.map((entry) => entry.dataset.routeAlias || ""),
    mobilePrimaryCount: entries.filter((entry) => entry.dataset.mobilePrimaryEntry === "true").length,
    mobileOnlyPrimaryCount: document.querySelectorAll('[data-mobile-primary-entry="true"]:not([data-primary-entry="true"])').length,
    bottomPrimaryTreeCount: document.querySelectorAll(".mobile-bottom-nav").length,
    aliasPrimaryNodeCount: entries.filter((entry) => aliases.includes(entry.dataset.routeAlias || "")).length,
    activePrimaryCount: activeEntries.length,
    initialNormalizedHash,
    clickedRoutes,
    aliasResults,
    releaseIdentityState: document.body.dataset.pfiReleaseIdentityState || "",
    conflictHidden: document.querySelector("#pfi-release-conflict")?.hidden === true,
    appShellVisible: document.querySelector(".app-shell")?.hidden === false,
    evidenceRedacted: document.body.dataset.stage6Phase61EvidenceRedacted === "true",
  };
  const output = document.createElement("script");
  output.type = "application/json";
  output.id = "stage6-phase61-browser-result";
  output.textContent = JSON.stringify(result);
  document.body.appendChild(output);
}, 2600);
</script>
"""


def _extract_result(dom: str) -> dict[str, object]:
    matched = re.search(
        r'<script type="application/json" id="stage6-phase61-browser-result">(.*?)</script>',
        dom,
        flags=re.DOTALL,
    )
    if not matched:
        raise RuntimeError("Stage 6 Phase 6.1 browser result was not emitted")
    return json.loads(unescape(matched.group(1)))


def _capture(
    helpers: object,
    base_url: str,
    *,
    name: str,
    input_route: str,
    expected_initial_route: str,
    window_size: str,
) -> dict[str, object]:
    screenshot = REPORT_DIR / f"{name}.png"
    url = f"{base_url}/index.html#{input_route}"
    profile = Path(tempfile.mkdtemp(prefix=f"pfi-stage6-{name}-", dir="/tmp"))
    dom_path: Path | None = None
    try:
        shot_stderr = helpers._run_chrome_to_file(
            helpers._chrome_common(profile, url)[:-1]
            + [f"--window-size={window_size}", f"--screenshot={screenshot}", url],
            screenshot,
            stdout_is_output=False,
        )
        shutil.rmtree(profile, ignore_errors=True)
        profile = Path(tempfile.mkdtemp(prefix=f"pfi-stage6-{name}-dom-", dir="/tmp"))
        temporary = tempfile.NamedTemporaryFile(prefix=f"pfi-stage6-{name}-", suffix=".html", dir="/tmp", delete=False)
        temporary.close()
        dom_path = Path(temporary.name)
        dump_stderr = helpers._run_chrome_to_file(
            helpers._chrome_common(profile, url)[:-1] + ["--dump-dom", url],
            dom_path,
            stdout_is_output=True,
        )
        dom = dom_path.read_text(encoding="utf-8", errors="strict")
    finally:
        if dom_path is not None:
            dom_path.unlink(missing_ok=True)
        shutil.rmtree(profile, ignore_errors=True)

    result = _extract_result(dom)
    expected_routes = [
        "/overview",
        "/accounts",
        "/ledger",
        "/investment",
        "/consumption",
        "/data",
        "/review",
        "/reports",
        "/market-research",
        "/settings",
    ]
    expected_alias_targets = [
        "/overview",
        "/market-research/market",
        "/market-research/research",
        "/investment/holdings",
        "/market-research/strategy-lab",
        "/market-research/strategy-lab",
        "/settings/data-system",
    ]
    error_lines = [
        line
        for line in (shot_stderr + "\n" + dump_stderr).splitlines()
        if "Uncaught" in line or "ReferenceError" in line or "TypeError" in line
    ]
    checks = {
        "registry_contract": result.get("registrySchema") == "PFIV025Stage6Phase61NavigationContractV1"
        and result.get("contractVersion") == "PFI-V025-STAGE6-PHASE61-NAVIGATION-ALIAS",
        "one_shared_primary_tree": result.get("uniquePrimaryNodeCount") == 10
        and result.get("mobilePrimaryCount") == 10
        and result.get("mobileOnlyPrimaryCount") == 0
        and result.get("bottomPrimaryTreeCount") == 0,
        "primary_order": result.get("primaryRoutes") == expected_routes,
        "primary_clicks": result.get("clickedRoutes") == expected_routes,
        "aliases_non_primary": result.get("aliasPrimaryNodeCount") == 0,
        "aliases_resolve": [item.get("routeAlias") for item in result.get("aliasResults", [])]
        == expected_alias_targets,
        "strategy_lab_single_canonical": [
            item.get("routeAlias")
            for item in result.get("aliasResults", [])
            if item.get("inputRouteAlias") in {"/strategy-lab", "/investment/strategy-lab"}
        ]
        == ["/market-research/strategy-lab", "/market-research/strategy-lab"],
        "input_alias_normalized": result.get("initialNormalizedHash") == expected_initial_route,
        "single_active_entry": result.get("activePrimaryCount") == 1,
        "release_identity_ready": result.get("releaseIdentityState") == "ready"
        and result.get("conflictHidden") is True
        and result.get("appShellVisible") is True,
        "tracked_screenshot_redaction": result.get("evidenceRedacted") is True,
        "console_errors": not error_lines,
    }
    return {
        "status": "pass" if all(checks.values()) else "fail",
        "input_route": input_route,
        "expected_initial_route": expected_initial_route,
        "window_size": window_size,
        "screenshot": f"PFI/reports/pfi_v025/stage_6/phase_6_1/{name}.png",
        "screenshot_bytes": screenshot.stat().st_size,
        "checks": checks,
        "result": result,
        "console_errors": error_lines,
    }


def main() -> int:
    helpers = _load_browser_helpers()
    if not helpers.CHROME.is_file():
        raise RuntimeError("local Google Chrome is required")
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    markup = helpers._offline_formal_shell_html({})
    markup = markup.replace("</body>", _validation_script() + "</body>")
    temp_dir = Path(tempfile.mkdtemp(prefix="pfi-stage6-phase61-formal-shell-", dir="/tmp"))
    markup_path = temp_dir / "index.html"
    server: ThreadingHTTPServer | None = None
    server_thread: threading.Thread | None = None
    try:
        markup_path.write_text(markup, encoding="utf-8")
        handler = partial(helpers._QuietLoopbackHandler, directory=str(temp_dir))
        server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        server_thread = threading.Thread(target=server.serve_forever, name="pfi-stage6-phase61-loopback", daemon=True)
        server_thread.start()
        base_url = f"http://127.0.0.1:{server.server_address[1]}"
        desktop = _capture(
            helpers,
            base_url,
            name="desktop_navigation",
            input_route="/home",
            expected_initial_route="/overview",
            window_size="1440,1100",
        )
        mobile = _capture(
            helpers,
            base_url,
            name="mobile_navigation",
            input_route="/data-system",
            expected_initial_route="/settings/data-system",
            window_size="390,844",
        )
    finally:
        if server is not None:
            server.shutdown()
            server.server_close()
        if server_thread is not None:
            server_thread.join(timeout=5)
        markup_path.unlink(missing_ok=True)
        shutil.rmtree(temp_dir, ignore_errors=True)

    status = "pass" if desktop["status"] == mobile["status"] == "pass" else "fail"
    validation = {
        "schema": "PFIV025Stage6Phase61BrowserValidationV1",
        "status": status,
        "contract_id": "PFI-V025-STAGE6-PHASE61-NAVIGATION-ALIAS",
        "acceptance_id": "ACC-PFI-V025-S6-P61-NAVIGATION-ALIAS",
        "method": "actual_formal_shell_ephemeral_loopback_isolated_chrome",
        "actual_formal_shell": True,
        "financial_data_loaded": False,
        "finder_used": False,
        "network_performed": True,
        "network_scope": "ephemeral_local_loopback_only",
        "external_network_performed": False,
        "desktop": desktop,
        "mobile": mobile,
    }
    (REPORT_DIR / "browser_validation.json").write_text(
        json.dumps(validation, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    trace = REPORT_DIR / "browser_trace.zip"
    with zipfile.ZipFile(trace, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("browser_validation.json", json.dumps(validation, ensure_ascii=False, indent=2))
        archive.writestr(
            "trace_metadata.json",
            json.dumps(
                {
                    "sanitized": True,
                    "financial_data_loaded": False,
                    "finder_used": False,
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
                "status": status,
                "desktop": desktop["status"],
                "mobile": mobile["status"],
                "trace_sha256": hashlib.sha256(trace.read_bytes()).hexdigest(),
            },
            ensure_ascii=False,
        )
    )
    return 0 if status == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
