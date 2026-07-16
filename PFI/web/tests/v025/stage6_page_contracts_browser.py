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
import subprocess
import tempfile
import threading
import zipfile


PFI_ROOT = Path(__file__).resolve().parents[3]
REPORT_DIR = PFI_ROOT / "reports/pfi_v025/stage_6/phase_6_2"
STAGE5_BROWSER = PFI_ROOT / "scripts/v025/browser_validate_stage5_whole_review.py"


def _load_node_contracts() -> tuple[dict[str, object], dict[str, object]]:
    script = """
const navigation = require(process.argv[1]);
const routes = require(process.argv[2]);
console.log(JSON.stringify({pageContracts: navigation.v025PageContracts, routes}));
"""
    completed = subprocess.run(
        ["node", "-e", script, str(PFI_ROOT / "web/app/navigation.js"), str(PFI_ROOT / "web/app/routes.js")],
        cwd=PFI_ROOT.parent,
        check=True,
        text=True,
        capture_output=True,
    )
    payload = json.loads(completed.stdout)
    return payload["pageContracts"], payload["routes"]


def _load_browser_helpers() -> object:
    spec = importlib.util.spec_from_file_location("pfi_stage5_browser_helpers", STAGE5_BROWSER)
    if spec is None or spec.loader is None:
        raise RuntimeError("formal-shell browser helpers are unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _validation_script() -> str:
    return r"""
<script data-stage6-phase62-browser-validation="true">
window.setTimeout(async () => {
  const waitFrame = () => new Promise((resolve) => window.requestAnimationFrame(() => window.requestAnimationFrame(resolve)));
  const route = () => decodeURIComponent(String(window.location.hash || "")).replace(/^#/, "");
  const redactEvidence = () => {
    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
    const nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);
    nodes.forEach((node) => {
      const original = String(node.textContent || "");
      const redacted = original
        .replace(/AUD\/CNY\s*=\s*-?[0-9,.]+/g, "AUD/CNY=未加载")
        .replace(/CNY\s*-?[0-9,.]+/g, "CNY 已脱敏")
        .replace(/AUD\s*-?[0-9,.]+/g, "AUD 已脱敏");
      if (redacted !== original) node.textContent = redacted;
    });
    document.body.dataset.stage6Phase62EvidenceRedacted = "true";
  };
  const snapshot = () => {
    const main = document.querySelector("#main-workspace");
    const page = document.querySelector("article[data-stage6-page-contract='phase_6_2']");
    const breadcrumb = page?.querySelector("[data-stage4-breadcrumb]");
    return {
      route: route(),
      mainRoute: main?.dataset.routeAlias || "",
      workspace: main?.dataset.activeWorkspace || "",
      documentTitle: document.title,
      pageTitle: page?.querySelector("[data-stage6-page-heading]")?.textContent || "",
      breadcrumb: breadcrumb?.textContent?.replace(/\s+/g, " ").trim() || "",
      job: page?.dataset.stage6JobToBeDone || "",
      loadingState: page?.dataset.stage6LoadingState || "",
      emptyState: page?.dataset.stage6EmptyState || "",
      errorState: page?.dataset.stage6ErrorState || "",
      structuralSignature: page?.dataset.stage6StructuralSignature || "",
      primaryAction: page?.dataset.stage4PrimaryAction || "",
      dataObject: page?.dataset.stage5DataObject || "",
      headingFocused: document.activeElement === page?.querySelector("[data-stage6-page-heading]"),
    };
  };

  const registry = window.PFI_V025_STAGE6_ROUTES;
  const contract = window.PFI_V025_STAGE6_PAGE_CONTRACTS;
  const initial = snapshot();
  const representatives = [];
  const primaryEntries = [...document.querySelectorAll('[data-primary-entry="true"]')];
  for (const entry of primaryEntries) {
    entry.click();
    const firstSecondary = document.querySelector("[data-secondary-tab]");
    firstSecondary?.click();
    await waitFrame();
    representatives.push(snapshot());
  }

  const accountEntry = primaryEntries.find((entry) => entry.dataset.workspace === "accounts");
  accountEntry?.click();
  document.querySelector('[data-route-alias="/accounts/overview"]')?.click();
  await waitFrame();
  window.scrollTo(0, 360);
  document.querySelector('[data-route-alias="/accounts/list"]')?.click();
  await waitFrame();
  window.scrollTo(0, 140);
  document.querySelector('[data-route-alias="/accounts/overview"]')?.click();
  await waitFrame();
  const scrollRestoration = {
    route: route(),
    restoredY: Math.round(window.scrollY),
    expectedY: 360,
    passed: Math.abs(window.scrollY - 360) <= 2,
  };

  redactEvidence();
  const activeEntries = primaryEntries.filter((entry) => entry.classList.contains("is-active"));
  const result = {
    registrySchema: registry?.phase62RouteRegistry?.schema || "",
    pageContractSchema: contract?.schema || "",
    pageCount: contract?.pages?.length || 0,
    canonicalRouteCount: registry?.canonicalSecondaryRoutes?.length || 0,
    initial,
    representatives,
    distinctRepresentativeSignatures: new Set(representatives.map((item) => item.structuralSignature)).size,
    distinctRepresentativeDataObjects: new Set(representatives.map((item) => item.dataObject)).size,
    distinctRepresentativeActions: new Set(representatives.map((item) => item.primaryAction)).size,
    activePrimaryCount: activeEntries.length,
    scrollRestoration,
    releaseIdentityState: document.body.dataset.pfiReleaseIdentityState || "",
    conflictHidden: document.querySelector("#pfi-release-conflict")?.hidden === true,
    appShellVisible: document.querySelector(".app-shell")?.hidden === false,
    evidenceRedacted: document.body.dataset.stage6Phase62EvidenceRedacted === "true",
  };
  const output = document.createElement("script");
  output.type = "application/json";
  output.id = "stage6-phase62-browser-result";
  output.textContent = JSON.stringify(result);
  document.body.appendChild(output);
  window.scrollTo(0, 0);
}, 2600);
</script>
"""


def _extract_result(dom: str) -> dict[str, object]:
    matched = re.search(
        r'<script type="application/json" id="stage6-phase62-browser-result">(.*?)</script>',
        dom,
        flags=re.DOTALL,
    )
    if not matched:
        raise RuntimeError("Stage 6 Phase 6.2 browser result was not emitted")
    return json.loads(unescape(matched.group(1)))


def _run_chrome(helpers: object, base_url: str, *, name: str, route: str, window_size: str) -> dict[str, object]:
    url = f"{base_url}/index.html#{route}"
    screenshot = REPORT_DIR / f"{name}.png"
    profile = Path(tempfile.mkdtemp(prefix=f"pfi-stage6-{name}-", dir="/tmp"))
    dom_path: Path | None = None
    try:
        shot_stderr = helpers._run_chrome_to_file(
            helpers._chrome_common(profile, url)[:-1] + [f"--window-size={window_size}", f"--screenshot={screenshot}", url],
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
        result = _extract_result(dom_path.read_text(encoding="utf-8", errors="strict"))
    finally:
        if dom_path is not None:
            dom_path.unlink(missing_ok=True)
        shutil.rmtree(profile, ignore_errors=True)

    representatives = result.get("representatives", [])
    errors = [
        line for line in (shot_stderr + "\n" + dump_stderr).splitlines()
        if "Uncaught" in line or "ReferenceError" in line or "TypeError" in line
    ]
    checks = {
        "phase62_contracts": result.get("registrySchema") == "PFIV025Stage6Phase62RouteRegistryV1"
        and result.get("pageContractSchema") == "PFIV025Stage6Phase62PageContractsV1",
        "all_pages_registered": result.get("pageCount") == 45 and result.get("canonicalRouteCount") == 45,
        "deep_link_nonblank": result.get("initial", {}).get("route") == route
        and bool(result.get("initial", {}).get("pageTitle")),
        "ten_workspace_representatives": len(representatives) == 10
        and {item.get("workspace") for item in representatives}
        == {"home", "accounts", "ledger", "investment", "consumption", "sync", "recommendations", "insights", "market_research", "settings"},
        "canonical_url_state_match": all(item.get("route") == item.get("mainRoute") for item in representatives),
        "page_contract_visible": all(
            item.get("pageTitle") and item.get("breadcrumb") and item.get("job")
            and item.get("loadingState") and item.get("emptyState") and item.get("errorState")
            for item in representatives
        ),
        "not_title_only_clones": result.get("distinctRepresentativeSignatures") == 10
        and result.get("distinctRepresentativeDataObjects") == 10
        and result.get("distinctRepresentativeActions") == 10,
        "title_and_focus": all(item.get("pageTitle") in item.get("documentTitle", "") and item.get("headingFocused") for item in representatives),
        "scroll_restoration": result.get("scrollRestoration", {}).get("passed") is True,
        "single_active_primary": result.get("activePrimaryCount") == 1,
        "release_identity_ready": result.get("releaseIdentityState") == "ready"
        and result.get("conflictHidden") is True and result.get("appShellVisible") is True,
        "evidence_redacted": result.get("evidenceRedacted") is True,
        "console_errors": not errors,
    }
    return {
        "status": "pass" if all(checks.values()) else "fail",
        "route": route,
        "window_size": window_size,
        "screenshot": f"PFI/reports/pfi_v025/stage_6/phase_6_2/{name}.png",
        "screenshot_bytes": screenshot.stat().st_size,
        "checks": checks,
        "result": result,
        "console_errors": errors,
    }


def _run_nojs(helpers: object, base_url: str) -> dict[str, object]:
    route = "/overview/status"
    url = f"{base_url}/index.html"
    screenshot = REPORT_DIR / "nojs_navigation.png"
    profile = Path(tempfile.mkdtemp(prefix="pfi-stage6-nojs-", dir="/tmp"))
    dom_path: Path | None = None
    flags = ["--window-size=1280,900"]
    preferences = profile / "Default/Preferences"
    preferences.parent.mkdir(parents=True, exist_ok=True)
    preferences.write_text(json.dumps({"profile": {"default_content_setting_values": {"javascript": 2}}}), encoding="utf-8")
    try:
        shot_stderr = helpers._run_chrome_to_file(
            helpers._chrome_common(profile, url)[:-1] + flags + [f"--screenshot={screenshot}", url],
            screenshot,
            stdout_is_output=False,
        )
        shutil.rmtree(profile, ignore_errors=True)
        profile = Path(tempfile.mkdtemp(prefix="pfi-stage6-nojs-dom-", dir="/tmp"))
        preferences = profile / "Default/Preferences"
        preferences.parent.mkdir(parents=True, exist_ok=True)
        preferences.write_text(json.dumps({"profile": {"default_content_setting_values": {"javascript": 2}}}), encoding="utf-8")
        temporary = tempfile.NamedTemporaryFile(prefix="pfi-stage6-nojs-", suffix=".html", dir="/tmp", delete=False)
        temporary.close()
        dom_path = Path(temporary.name)
        dump_stderr = helpers._run_chrome_to_file(
            helpers._chrome_common(profile, url)[:-1] + flags + ["--dump-dom", url],
            dom_path,
            stdout_is_output=True,
        )
        dom = dom_path.read_text(encoding="utf-8", errors="strict")
    finally:
        if dom_path is not None:
            dom_path.unlink(missing_ok=True)
        shutil.rmtree(profile, ignore_errors=True)
    page_routes = re.findall(r'data-no-js-page-route="([^"]+)"', dom)
    errors = [
        line for line in (shot_stderr + "\n" + dump_stderr).splitlines()
        if "Uncaught" in line or "ReferenceError" in line or "TypeError" in line
    ]
    checks = {
        "javascript_disabled": '<script type="application/json" id="stage6-phase62-browser-result">' not in dom,
        "fallback_directory_visible": "PFI 无脚本页面目录" in dom,
        "all_fallback_pages_present": len(page_routes) == 45 and len(set(page_routes)) == 45,
        "deep_link_page_present": route in page_routes and 'data-no-js-page-title="财务状态"' in dom,
        "ten_primary_links_only": len(re.findall(r'data-no-js-route="', dom)) == 10,
        "console_errors": not errors,
    }
    return {
        "status": "pass" if all(checks.values()) else "fail",
        "route": route,
        "screenshot": "PFI/reports/pfi_v025/stage_6/phase_6_2/nojs_navigation.png",
        "screenshot_bytes": screenshot.stat().st_size,
        "checks": checks,
        "page_count": len(page_routes),
        "console_errors": errors,
    }


def main() -> int:
    helpers = _load_browser_helpers()
    if not helpers.CHROME.is_file():
        raise RuntimeError("local Google Chrome is required")
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    markup = helpers._offline_formal_shell_html({}).replace("</body>", _validation_script() + "</body>")
    temp_dir = Path(tempfile.mkdtemp(prefix="pfi-stage6-phase62-formal-shell-", dir="/tmp"))
    markup_path = temp_dir / "index.html"
    server: ThreadingHTTPServer | None = None
    thread: threading.Thread | None = None
    try:
        markup_path.write_text(markup, encoding="utf-8")
        handler = partial(helpers._QuietLoopbackHandler, directory=str(temp_dir))
        server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        thread = threading.Thread(target=server.serve_forever, name="pfi-stage6-phase62-loopback", daemon=True)
        thread.start()
        base_url = f"http://127.0.0.1:{server.server_address[1]}"
        desktop = _run_chrome(helpers, base_url, name="desktop_page_contracts", route="/accounts/reconcile", window_size="1440,1100")
        mobile = _run_chrome(helpers, base_url, name="mobile_page_contracts", route="/market-research/strategy-lab", window_size="390,844")
        nojs = _run_nojs(helpers, base_url)
    finally:
        if server is not None:
            server.shutdown()
            server.server_close()
        if thread is not None:
            thread.join(timeout=5)
        markup_path.unlink(missing_ok=True)
        shutil.rmtree(temp_dir, ignore_errors=True)

    status = "pass" if desktop["status"] == mobile["status"] == nojs["status"] == "pass" else "fail"
    page_contracts, routes = _load_node_contracts()
    validation = {
        "schema": "PFIV025Stage6Phase62BrowserValidationV1",
        "status": status,
        "contract_id": "PFI-V025-STAGE6-PHASE62-PAGE-CONTRACTS",
        "acceptance_id": "ACC-PFI-V025-S6-P62-PAGE-CONTRACTS",
        "method": "actual_formal_shell_ephemeral_loopback_isolated_chrome",
        "actual_formal_shell": True,
        "financial_data_loaded": False,
        "finder_used": False,
        "network_scope": "ephemeral_local_loopback_only",
        "external_network_performed": False,
        "desktop": desktop,
        "mobile": mobile,
        "nojs": nojs,
    }
    (REPORT_DIR / "browser_validation.json").write_text(
        json.dumps(validation, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (REPORT_DIR / "page_contracts.json").write_text(
        json.dumps(page_contracts, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (REPORT_DIR / "page_data_actions.json").write_text(
        json.dumps({
            "schema": "PFIV025Stage6Phase62PageDataActionsV1",
            "status": "pass" if status == "pass" else "fail",
            "page_count": len(page_contracts["pages"]),
            "pages": [{
                key: page[key] for key in (
                    "workspace", "routeAlias", "layoutKind", "structuralSignature", "dataObject",
                    "primaryAction", "jobToBeDone", "states",
                )
            } for page in page_contracts["pages"]],
        }, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (REPORT_DIR / "navigation_behavior.json").write_text(
        json.dumps({
            "schema": "PFIV025Stage6Phase62NavigationBehaviorV1",
            "status": "pass" if desktop["status"] == mobile["status"] == "pass" else "fail",
            "document_title_bound_to_page": desktop["checks"]["title_and_focus"] and mobile["checks"]["title_and_focus"],
            "breadcrumb_bound_to_page": desktop["checks"]["page_contract_visible"] and mobile["checks"]["page_contract_visible"],
            "heading_focus_after_navigation": desktop["checks"]["title_and_focus"] and mobile["checks"]["title_and_focus"],
            "scroll_restored_per_canonical_route": desktop["checks"]["scroll_restoration"] and mobile["checks"]["scroll_restoration"],
            "full_back_forward_reload_acceptance_deferred_to_phase_6_3": True,
        }, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (REPORT_DIR / "deep_link_fallback.json").write_text(
        json.dumps({
            "schema": "PFIV025Stage6Phase62DeepLinkFallbackV1",
            "status": "pass" if desktop["checks"]["deep_link_nonblank"] and mobile["checks"]["deep_link_nonblank"] and nojs["status"] == "pass" else "fail",
            "canonical_secondary_route_count": len(routes["canonicalSecondaryRoutes"]),
            "historical_secondary_redirect_count": len(page_contracts["historicalRouteTargets"]),
            "nojs_secondary_page_count": nojs["page_count"],
            "desktop_deep_link": desktop["route"],
            "mobile_deep_link": mobile["route"],
            "nojs_fallback_directory_nonblank": nojs["checks"]["fallback_directory_visible"],
            "strategy_lab_canonical_route": routes["canonicalStrategyLabRoute"],
        }, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (REPORT_DIR / "phase_contract.json").write_text(
        json.dumps({
            "schema": "PFIV025Stage6Phase62RunContractV1",
            "status": "candidate_pass" if status == "pass" else "fail",
            "iteration_id": "ITER-20260715-PFI-V025-S6-P62",
            "contract_id": "PFI-V025-STAGE6-PHASE62-PAGE-CONTRACTS",
            "acceptance_id": "ACC-PFI-V025-S6-P62-PAGE-CONTRACTS",
            "task_ids": ["S6-P2-T1", "S6-P2-T2", "S6-P2-T3", "S6-P2-T4"],
            "implementation_base": "6b96bcb655b1c11d91b23dd10cf25b33e37f0242",
            "current_phase_only": True,
            "phase_6_3_started": False,
            "stage_6_whole_stage_review_started": False,
            "push_performed": False,
            "app_install_performed": False,
            "finder_used": False,
        }, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    trace = REPORT_DIR / "browser_trace.zip"
    with zipfile.ZipFile(trace, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("browser_validation.json", json.dumps(validation, ensure_ascii=False, indent=2))
        archive.writestr("trace_metadata.json", json.dumps({
            "sanitized": True,
            "financial_data_loaded": False,
            "finder_used": False,
            "network_scope": "ephemeral_local_loopback_only",
            "external_network_performed": False,
        }, ensure_ascii=False, indent=2))
    print(json.dumps({
        "status": status,
        "desktop": desktop["status"],
        "mobile": mobile["status"],
        "nojs": nojs["status"],
        "trace_sha256": hashlib.sha256(trace.read_bytes()).hexdigest(),
    }, ensure_ascii=False))
    return 0 if status == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
