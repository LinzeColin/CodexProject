#!/usr/bin/env node
import { createHash } from "node:crypto";
import { createReadStream } from "node:fs";
import { mkdir, readFile, stat, unlink, writeFile } from "node:fs/promises";
import http from "node:http";
import { createRequire } from "node:module";
import path from "node:path";
import { spawnSync } from "node:child_process";


const require = createRequire(import.meta.url);
const args = Object.fromEntries(process.argv.slice(2).reduce((pairs, value, index, values) => {
  if (value.startsWith("--")) pairs.push([value.slice(2), values[index + 1]]);
  return pairs;
}, []));
const webRoot = path.resolve(String(args["web-root"] || ""));
const outputDir = path.resolve(String(args["output-dir"] || ""));
const chromePath = path.resolve(String(args.chrome || "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"));
const moduleDir = process.env.PFI_PLAYWRIGHT_MODULE_DIR;
const selectedWorkspace = String(args.workspace || "").trim();
if (!webRoot || !outputDir || !moduleDir) throw new Error("web root, output directory and cached Playwright module are required");
const { chromium } = require(path.join(moduleDir, "playwright"));

const ROUTES = Object.freeze({
  home: { route: "/overview", archetype: "status_board" },
  accounts: { route: "/accounts/overview", archetype: "balance_sheet" },
  ledger: { route: "/ledger/list", archetype: "review_table" },
  investment: { route: "/investment/overview", archetype: "portfolio_analytics" },
  consumption: { route: "/consumption/overview", archetype: "spending_flow" },
  sync: { route: "/data/upload", archetype: "data_pipeline" },
  recommendations: { route: "/review/list", archetype: "decision_inbox" },
  insights: { route: "/reports/monthly", archetype: "report_library" },
  market_research: { route: "/market-research/research", archetype: "research_workspace" },
  settings: { route: "/settings/account", archetype: "control_center" },
});
const SECONDARY_ROUTES = Object.freeze({
  home_status: { workspace: "home", route: "/overview/status", archetype: "status_board" },
  accounts_reconcile: { workspace: "accounts", route: "/accounts/reconcile", archetype: "balance_sheet" },
  ledger_review: { workspace: "ledger", route: "/ledger/review", archetype: "review_table" },
  investment_holdings: { workspace: "investment", route: "/investment/holdings", archetype: "portfolio_analytics" },
  consumption_budget: { workspace: "consumption", route: "/consumption/budget", archetype: "spending_flow" },
  sync_sources: { workspace: "sync", route: "/data/sources", archetype: "data_pipeline" },
  recommendations_detail: { workspace: "recommendations", route: "/review/detail", archetype: "decision_inbox" },
  insights_custom: { workspace: "insights", route: "/reports/custom", archetype: "report_library" },
  market_strategy_lab: { workspace: "market_research", route: "/market-research/strategy-lab", archetype: "research_workspace" },
  settings_feedback: { workspace: "settings", route: "/settings/feedback", archetype: "control_center" },
});

const CONTENT_TYPES = Object.freeze({
  ".css": "text/css; charset=utf-8",
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".mjs": "text/javascript; charset=utf-8",
  ".png": "image/png",
  ".svg": "image/svg+xml",
});

function browserArgs() {
  return [
    "--disable-background-networking", "--disable-component-update", "--disable-default-apps",
    "--disable-domain-reliability", "--disable-extensions",
    "--disable-features=OptimizationHints,MediaRouter,ServiceWorker", "--disable-sync",
    "--disable-gpu",
    "--metrics-recording-only", "--no-first-run", "--no-default-browser-check",
  ];
}

function jsonResponse(response, statusCode, payload) {
  const body = JSON.stringify(payload);
  response.writeHead(statusCode, {
    "Cache-Control": "no-store",
    "Content-Type": "application/json; charset=utf-8",
    "Content-Length": Buffer.byteLength(body),
  });
  response.end(body);
}

function runtimeConfig(baseUrl) {
  return JSON.stringify({
    apiBaseUrl: baseUrl,
    readModelStatusApi: false,
    runtimeApiEnabled: false,
    releaseManifestApi: false,
    releaseCachePolicyApi: false,
    stage1OfficialCandidate: false,
    candidateDataMode: "canonical",
  });
}

async function transformedIndex(baseUrl) {
  const source = await readFile(path.join(webRoot, "index.html"), "utf8");
  const updated = source.replace(
    /<script type="application\/json" id="pfi-runtime-config">.*?<\/script>/s,
    `<script type="application/json" id="pfi-runtime-config">${runtimeConfig(baseUrl)}</script>`,
  );
  if (updated === source) throw new Error("runtime config seam is unavailable");
  return updated;
}

function staticPath(pathname) {
  const clean = pathname.replace(/^\/+/, "");
  const nestedAsset = clean.match(/(?:^|\/)(app\/.*|styles\/.*|styles\.css)$/)?.[1];
  const relative = nestedAsset || clean;
  const candidate = path.resolve(webRoot, relative);
  return candidate === webRoot || candidate.startsWith(`${webRoot}${path.sep}`) ? candidate : null;
}

async function startServer() {
  let baseUrl = "";
  const server = http.createServer(async (request, response) => {
    try {
      const requestUrl = new URL(request.url || "/", baseUrl || "http://127.0.0.1");
      if (requestUrl.pathname === "/api/trends") return jsonResponse(response, 200, { trends: {}, readModel: {} });
      if (requestUrl.pathname === "/api/read-model") return jsonResponse(response, 200, {});
      if (requestUrl.pathname === "/api/read-model-status") return jsonResponse(response, 200, {});
      if (requestUrl.pathname === "/api/health") return jsonResponse(response, 200, { status: "ready" });

      const candidate = staticPath(decodeURIComponent(requestUrl.pathname));
      let candidateStat = null;
      try { candidateStat = candidate ? await stat(candidate) : null; } catch (_error) { candidateStat = null; }
      const extension = candidateStat?.isFile() ? path.extname(candidate).toLowerCase() : "";
      if (candidateStat?.isFile() && extension !== ".html") {
        response.writeHead(200, {
          "Cache-Control": "no-store",
          "Content-Type": CONTENT_TYPES[extension] || "application/octet-stream",
        });
        createReadStream(candidate).pipe(response);
        return;
      }

      const markup = await transformedIndex(baseUrl);
      response.writeHead(200, {
        "Cache-Control": "no-store",
        "Content-Type": "text/html; charset=utf-8",
        "Content-Length": Buffer.byteLength(markup),
      });
      response.end(markup);
    } catch (error) {
      jsonResponse(response, 500, { error: String(error?.message || error) });
    }
  });
  await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
  const address = server.address();
  if (!address || typeof address === "string") throw new Error("loopback server address is unavailable");
  baseUrl = `http://127.0.0.1:${address.port}`;
  return { server, baseUrl };
}

function watchPage(page, diagnostics) {
  page.on("console", (message) => { if (message.type() === "error") diagnostics.consoleErrors.push(message.text()); });
  page.on("pageerror", (error) => diagnostics.pageErrors.push(String(error?.message || error)));
  page.on("response", (response) => {
    if (response.status() >= 400) diagnostics.httpErrors.push({ status: response.status(), url: response.url() });
  });
}

async function waitForReady(page) {
  try {
    await page.waitForFunction(() => (
      document.querySelector(".app-shell")?.hidden === false
      && document.body.dataset.pfiReleaseIdentityState === "ready"
      && Boolean(document.querySelector("#main-workspace")?.dataset.stage8Archetype)
      && Boolean(document.querySelector("[data-trend-panel]")?.dataset.stage8ChartState)
    ), null, { timeout: 30_000 });
  } catch (error) {
    const debug = await page.evaluate(() => ({
      url: window.location.href,
      releaseIdentityState: document.body?.dataset.pfiReleaseIdentityState || "",
      appShellHidden: document.querySelector(".app-shell")?.hidden,
      workspace: document.querySelector("#main-workspace")?.dataset.activeWorkspace || "",
      archetype: document.querySelector("#main-workspace")?.dataset.stage8Archetype || "",
      chartState: document.querySelector("[data-trend-panel]")?.dataset.stage8ChartState || "",
      conflict: document.querySelector("#pfi-release-conflict")?.textContent?.replace(/\s+/g, " ").trim() || "",
      designSystemLoaded: Boolean(window.PFI_V025_STAGE8_DESIGN_SYSTEM),
    }));
    throw new Error(`formal shell readiness timeout: ${JSON.stringify(debug)}`, { cause: error });
  }
  await page.waitForTimeout(350);
}

async function inspectPage(page, workspace, expected, viewportKind) {
  return page.evaluate(({ workspaceId, expectedArchetype, kind }) => {
    const main = document.querySelector("#main-workspace");
    const shell = document.querySelector(".app-shell");
    const sideNav = document.querySelector(".side-nav");
    const mobileNav = document.querySelector(".mobile-bottom-nav");
    const panel = document.querySelector("[data-trend-panel]");
    const canvas = panel?.querySelector("[data-trend-canvas]");
    const empty = panel?.querySelector("[data-trend-empty]");
    const chartStatus = panel?.querySelector("[data-stage8-chart-status]");
    const stagePage = document.querySelector("[data-stage6-structural-signature]");
    const metricGrid = document.querySelector(".metric-grid");
    const stageGrid = document.querySelector(".stage4-section-grid");
    const contentGrid = document.querySelector(".content-grid");
    const workspaceFocus = document.querySelector("[data-stage8-workspace-focus]");
    const workspaceFocusBody = workspaceFocus?.querySelector("[data-stage8-workspace-focus-body]");
    const homeQuestions = document.querySelector("[data-home-question-grid]");
    const rootStyle = getComputedStyle(document.documentElement);
    const bodyStyle = getComputedStyle(document.body);
    const rgb = bodyStyle.backgroundColor.match(/[0-9.]+/g)?.slice(0, 3).map(Number) || [0, 0, 0];
    const visible = (node) => Boolean(node) && getComputedStyle(node).display !== "none" && getComputedStyle(node).visibility !== "hidden";
    const mobileTargets = [...document.querySelectorAll(".mobile-tab")].map((node) => {
      const box = node.getBoundingClientRect();
      return { width: Math.round(box.width), height: Math.round(box.height) };
    });
    const paintSample = (x, y) => {
      const node = document.elementFromPoint(x, y);
      if (!node) return { x, y, node: "none" };
      const style = getComputedStyle(node);
      return {
        x,
        y,
        node: `${node.tagName.toLowerCase()}.${String(node.className || "").replace(/\s+/g, ".")}`,
        backgroundColor: style.backgroundColor,
        backgroundImage: style.backgroundImage,
        backdropFilter: style.backdropFilter,
        filter: style.filter,
        opacity: style.opacity,
        position: style.position,
        zIndex: style.zIndex,
      };
    };
    const visibleRegionClasses = [...main.querySelectorAll(":scope > section")]
      .filter(visible)
      .map((node) => [...node.classList].sort().join("."))
      .filter(Boolean);
    const focusDomShape = workspaceFocusBody && visible(workspaceFocus)
      ? [...workspaceFocusBody.querySelectorAll(":scope > *, :scope > * > *")]
        .map((node) => `${node.tagName.toLowerCase()}.${[...node.classList].sort().join(".")}`)
      : [];
    const layoutSignature = [
      metricGrid ? getComputedStyle(metricGrid).gridTemplateColumns : "none",
      stageGrid ? getComputedStyle(stageGrid).gridTemplateColumns : "none",
      contentGrid ? getComputedStyle(contentGrid).gridTemplateColumns : "none",
      stagePage?.getAttribute("data-stage6-structural-signature") || main?.dataset.stage6PageContract || "none",
      visible(homeQuestions) ? `home-questions:${homeQuestions.children.length}` : "home-questions:hidden",
      visible(workspaceFocus) ? `focus:${workspaceFocusBody?.children.length || 0}` : "focus:hidden",
      visibleRegionClasses.join(","),
      focusDomShape.join(","),
    ].join("|");
    return {
      workspace: main?.dataset.activeWorkspace || "",
      route: main?.dataset.routeAlias || "",
      archetype: main?.dataset.stage8Archetype || "",
      expectedWorkspace: workspaceId,
      expectedArchetype,
      releaseIdentityState: document.body.dataset.pfiReleaseIdentityState || "",
      shellVisible: visible(shell),
      rootColorScheme: rootStyle.colorScheme,
      bodyBackground: bodyStyle.backgroundColor,
      bodyBackgroundIsLight: (rgb[0] + rgb[1] + rgb[2]) / 3 >= 220,
      chartState: panel?.dataset.stage8ChartState || "",
      chartCanvasHidden: canvas?.hidden === true,
      chartRole: canvas?.getAttribute("role") || "",
      chartDescription: canvas?.getAttribute("aria-describedby") || "",
      chartEmptyVisible: empty?.hidden === false,
      chartEmptyText: empty?.textContent?.trim() || "",
      chartStatusText: chartStatus?.textContent?.trim() || "",
      primaryEntryCount: document.querySelectorAll('[data-primary-entry="true"]').length,
      horizontalDocumentOverflow: document.documentElement.scrollWidth > window.innerWidth + 1,
      horizontalMainOverflow: Boolean(main) && main.scrollWidth > main.clientWidth + 1,
      sideNavVisible: visible(sideNav),
      mobileNavVisible: visible(mobileNav),
      mobileTargetMinimum: mobileTargets.length ? Math.min(...mobileTargets.map((item) => Math.min(item.width, item.height))) : 0,
      deviceMockupCount: document.querySelectorAll(".phone-preview, .mobile-preview-frame, .device-mockup, .iphone-frame").length,
      homeQuestionsVisible: visible(homeQuestions),
      workspaceFocusVisible: visible(workspaceFocus),
      workspaceFocusChildCount: workspaceFocusBody?.children.length || 0,
      entryBundleBadge: document.querySelector("[data-pfi-entry-bundle-hash]")?.textContent?.trim() || "",
      embeddedFrontendHash: JSON.parse(document.querySelector("#pfi-release-manifest")?.textContent || "{}").frontend_bundle_hash || "",
      paintSamples: [
        paintSample(8, 8),
        paintSample(Math.min(110, window.innerWidth - 8), Math.min(100, window.innerHeight - 8)),
        paintSample(Math.min(110, window.innerWidth - 8), Math.min(360, window.innerHeight - 8)),
        paintSample(Math.max(8, window.innerWidth - 8), Math.floor(window.innerHeight / 2)),
        paintSample(Math.floor(window.innerWidth / 2), Math.max(8, window.innerHeight - 16)),
      ],
      layoutSignature,
      actualDomSignature: layoutSignature,
      viewportKind: kind,
    };
  }, { workspaceId: workspace, expectedArchetype: expected.archetype, kind: viewportKind });
}

async function captureViewport(browser, baseUrl, kind, viewport, diagnostics, tracePath = "") {
  const origin = new URL(baseUrl).origin;
  const results = [];
  const screenshotDir = path.join(outputDir, `${kind}_pages`);
  await mkdir(screenshotDir, { recursive: true });
  const routes = [
    ...Object.entries(ROUTES).map(([workspace, expected]) => [workspace, { ...expected, workspace, pageKind: "primary" }]),
    ...Object.entries(SECONDARY_ROUTES).map(([pageId, expected]) => [pageId, { ...expected, pageKind: "secondary" }]),
  ].filter(([, expected]) => !selectedWorkspace || expected.workspace === selectedWorkspace);
  for (const [index, [pageId, expected]] of routes.entries()) {
    const workspace = expected.workspace;
    const context = await browser.newContext({
      locale: "zh-CN",
      serviceWorkers: "block",
      viewport,
      colorScheme: "dark",
      reducedMotion: "no-preference",
    });
    const shouldTrace = Boolean(tracePath) && index === 0;
    try {
      if (shouldTrace) await context.tracing.start({ screenshots: false, snapshots: false, sources: false });
      await context.route("**/*", async (route) => {
        const requestUrl = route.request().url();
        const parsed = new URL(requestUrl);
        if (["data:", "blob:", "about:"].includes(parsed.protocol) || parsed.origin === origin) {
          if (parsed.origin === origin) diagnostics.requestedOrigins.add(parsed.origin);
          await route.continue();
          return;
        }
        diagnostics.blockedExternal.push(requestUrl);
        await route.abort("blockedbyclient");
      });
      const page = await context.newPage();
      watchPage(page, diagnostics);
      console.log(`[stage8-phase81] ${kind}:${workspace}:navigate`);
      await page.goto(`${baseUrl}${expected.route}`, { waitUntil: "domcontentloaded" });
      await waitForReady(page);
      const inspection = await inspectPage(page, workspace, expected, kind);
      const targetDir = expected.pageKind === "primary" ? screenshotDir : path.join(outputDir, `${kind}_secondary`);
      await mkdir(targetDir, { recursive: true });
      const screenshotPath = path.join(targetDir, `${pageId}.png`);
      await page.screenshot({ path: screenshotPath, fullPage: false, animations: "disabled" });
      const screenshotBytes = (await stat(screenshotPath)).size;
      console.log(`[stage8-phase81] ${kind}:${workspace}:captured:${screenshotBytes}`);
      const checks = {
        workspace_and_archetype: inspection.workspace === workspace && inspection.archetype === expected.archetype,
        release_identity_ready: inspection.releaseIdentityState === "ready" && inspection.shellVisible,
        forced_os_dark_still_light: inspection.rootColorScheme === "light" && inspection.bodyBackgroundIsLight,
        ten_primary_entries: inspection.primaryEntryCount === 10,
        no_horizontal_overflow: !inspection.horizontalDocumentOverflow && !inspection.horizontalMainOverflow,
        chart_accessible: inspection.chartRole === "img" && inspection.chartDescription.split(/\s+/).length >= 3,
        chart_truthful_empty: inspection.chartState === "empty" && inspection.chartCanvasHidden
          && inspection.chartEmptyVisible
          && /不显示伪造曲线|不绘制曲线/.test(`${inspection.chartEmptyText} ${inspection.chartStatusText}`),
        no_device_mockup: inspection.deviceMockupCount === 0,
        workspace_surface_is_real: workspace === "home"
          ? inspection.homeQuestionsVisible && !inspection.workspaceFocusVisible
          : !inspection.homeQuestionsVisible && inspection.workspaceFocusVisible && inspection.workspaceFocusChildCount > 0,
        release_badge_bound_to_embedded_manifest: inspection.entryBundleBadge
          === `bundle ${inspection.embeddedFrontendHash.slice(0, 16)}`,
        responsive_navigation: kind === "desktop"
          ? inspection.sideNavVisible && !inspection.mobileNavVisible
          : !inspection.sideNavVisible && inspection.mobileNavVisible && inspection.mobileTargetMinimum >= 44,
        screenshot_written: screenshotBytes > 10_000,
      };
      results.push({
        workspace,
        page_id: pageId,
        page_kind: expected.pageKind,
        route: expected.route,
        archetype: expected.archetype,
        status: Object.values(checks).every(Boolean) ? "pass" : "fail",
        checks,
        inspection,
        screenshot: `${expected.pageKind === "primary" ? `${kind}_pages` : `${kind}_secondary`}/${pageId}.png`,
        screenshot_bytes: screenshotBytes,
      });
      if (shouldTrace) await context.tracing.stop({ path: tracePath });
    } finally {
      await context.close();
    }
  }
  return results;
}

await mkdir(outputDir, { recursive: true });
const tracePath = path.join(outputDir, "browser_trace.zip");
const rawTracePath = path.join(outputDir, ".browser_trace_raw.zip");
const diagnostics = {
  consoleErrors: [],
  pageErrors: [],
  httpErrors: [],
  blockedExternal: [],
  requestedOrigins: new Set(),
};
const { server, baseUrl } = await startServer();
console.log(`[stage8-phase81] loopback:${baseUrl}`);
const browser = await chromium.launch({ executablePath: chromePath, headless: true, args: browserArgs() });
console.log("[stage8-phase81] chrome:ready");
let result;
try {
  const desktop = await captureViewport(browser, baseUrl, "desktop", { width: 1440, height: 1000 }, diagnostics, rawTracePath);
  const mobile = await captureViewport(browser, baseUrl, "mobile", { width: 390, height: 844 }, diagnostics);
  const allPages = [...desktop, ...mobile];
  const desktopPrimary = desktop.filter((item) => item.page_kind === "primary");
  const mobilePrimary = mobile.filter((item) => item.page_kind === "primary");
  const desktopSignatures = new Set(desktopPrimary.map((item) => item.inspection.layoutSignature));
  const mobileSignatures = new Set(mobilePrimary.map((item) => item.inspection.layoutSignature));
  const expectedPageCount = selectedWorkspace ? 4 : 40;
  const expectedArchetypeCount = selectedWorkspace ? 1 : 10;
  const checks = {
    forty_real_route_viewports_pass: allPages.length === expectedPageCount && allPages.every((item) => item.status === "pass"),
    ten_semantic_archetypes: new Set(desktopPrimary.map((item) => item.archetype)).size === expectedArchetypeCount,
    desktop_not_title_only_clones: desktopSignatures.size === expectedArchetypeCount,
    mobile_not_title_only_clones: mobileSignatures.size === expectedArchetypeCount,
    no_console_errors: diagnostics.consoleErrors.length === 0,
    no_page_errors: diagnostics.pageErrors.length === 0,
    no_http_errors: diagnostics.httpErrors.length === 0,
    no_external_requests: diagnostics.blockedExternal.length === 0
      && [...diagnostics.requestedOrigins].every((origin) => origin === new URL(baseUrl).origin),
  };
  result = {
    schema: "PFIV025Stage8Phase81BrowserValidationV1",
    status: Object.values(checks).every(Boolean) ? "pass" : "fail",
    contract_id: "PFI-V025-STAGE8-PHASE81-DESIGN-SYSTEM",
    acceptance_id: "ACC-PFI-V025-STAGE8-WHOLE-REVIEW",
    method: "actual_current_worktree_formal_shell_playwright_ephemeral_loopback",
    actual_formal_shell: true,
    forced_os_color_scheme: "dark",
    expected_product_default: "light",
    financial_data_loaded: false,
    private_values_persisted: false,
    network_scope: "ephemeral_local_loopback_only",
    external_network_performed: false,
    finder_used: false,
    checks,
    desktop,
    mobile,
    diagnostics: {
      console_errors: diagnostics.consoleErrors,
      page_errors: diagnostics.pageErrors,
      http_errors: diagnostics.httpErrors,
      blocked_external_requests: diagnostics.blockedExternal,
      requested_origin_count: diagnostics.requestedOrigins.size,
    },
  };
} finally {
  await browser.close();
  server.closeAllConnections?.();
  await new Promise((resolve) => server.close(resolve));
}

const encoded = `${JSON.stringify(result, null, 2)}\n`;
await writeFile(path.join(outputDir, "browser_validation.json"), encoded, "utf8");
const sanitizer = path.join(webRoot, "tests", "v025", "stage8_phase81_trace_privacy.py");
const sanitized = spawnSync(process.env.PFI_PYTHON || "python3", ["-B", sanitizer, rawTracePath, tracePath], {
  cwd: path.dirname(webRoot),
  encoding: "utf8",
});
await unlink(rawTracePath).catch(() => {});
if (sanitized.status !== 0) {
  throw new Error(`trace sanitization failed: ${sanitized.stderr || sanitized.stdout}`);
}
const traceSha256 = createHash("sha256").update(await readFile(tracePath)).digest("hex");
console.log(JSON.stringify({ status: result.status, checks: result.checks, trace_sha256: traceSha256 }));
if (result.status !== "pass") process.exitCode = 2;
