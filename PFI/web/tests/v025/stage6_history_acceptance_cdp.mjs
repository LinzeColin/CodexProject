#!/usr/bin/env node
import { createRequire } from "node:module";
import { mkdir, mkdtemp, rm, writeFile } from "node:fs/promises";
import os from "node:os";
import path from "node:path";


const require = createRequire(import.meta.url);
const args = Object.fromEntries(process.argv.slice(2).reduce((pairs, value, index, values) => {
  if (value.startsWith("--")) pairs.push([value.slice(2), values[index + 1]]);
  return pairs;
}, []));
const baseUrl = String(args["base-url"] || "").replace(/\/$/, "");
const outputDir = path.resolve(String(args["output-dir"] || ""));
const chromePath = path.resolve(String(args.chrome || "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"));
const moduleDir = process.env.PFI_PLAYWRIGHT_MODULE_DIR;
if (!baseUrl || !outputDir || !moduleDir || !path.isAbsolute(moduleDir)) {
  throw new Error("base URL, output directory and cached Playwright module are required");
}
const { chromium } = require(path.join(moduleDir, "playwright"));
const expectedPrimaryNames = [
  "首页总览", "账户与资产", "账本流水", "投资管理", "消费管理",
  "数据源与上传", "建议与复盘", "报告与洞察", "市场与研究", "设置",
];


function valueOf(node, key) {
  return String(node?.[key]?.value || "").trim();
}


function sanitizeAxSubtree(nodes) {
  const nodeById = new Map(nodes.map((node) => [node.nodeId, node]));
  const navigation = nodes.find((node) => valueOf(node, "role") === "navigation" && valueOf(node, "name") === "一级工作区");
  if (!navigation) return { navigation_found: false, nodes: [], primary_names: [] };
  const selected = [];
  const queue = [navigation.nodeId];
  const seen = new Set();
  while (queue.length) {
    const id = queue.shift();
    if (!id || seen.has(id)) continue;
    seen.add(id);
    const node = nodeById.get(id);
    if (!node) continue;
    selected.push({
      role: valueOf(node, "role"),
      name: valueOf(node, "name"),
      ignored: node.ignored === true,
      focusable: Array.isArray(node.properties) && node.properties.some(
        (property) => property?.name === "focusable" && property?.value?.value === true,
      ),
      child_count: Array.isArray(node.childIds) ? node.childIds.length : 0,
    });
    queue.push(...(node.childIds || []));
  }
  const buttonNames = selected
    .filter((node) => node.ignored !== true && node.role === "button")
    .map((node) => node.name);
  const primaryNames = expectedPrimaryNames.filter(
    (expectedName) => buttonNames.some((buttonName) => buttonName.includes(expectedName)),
  );
  return { navigation_found: true, nodes: selected, primary_names: primaryNames };
}


async function waitForShell(page, routeAlias) {
  await page.waitForFunction((route) => {
    const shell = document.querySelector(".app-shell");
    const main = document.querySelector("#main-workspace");
    return shell && !shell.hidden
      && document.body.dataset.pfiReleaseIdentityState === "ready"
      && (!route || (window.location.pathname === route && main?.dataset.routeAlias === route));
  }, routeAlias, { timeout: 20_000 });
}


async function snapshot(page) {
  return page.evaluate(() => {
    const main = document.querySelector("#main-workspace");
    const invalidSurface = document.querySelector("[data-stage6-invalid-route]");
    const heading = invalidSurface?.hidden === false
      ? document.querySelector("[data-stage6-invalid-route-title]")
      : document.querySelector("[data-stage6-page-heading]");
    return {
      pathname: window.location.pathname,
      hash: window.location.hash,
      history_length: window.history.length,
      history_state: window.history.state,
      route_alias: main?.dataset.routeAlias || "",
      route_state: main?.getAttribute("data-stage6-route-state") || "",
      workspace: main?.dataset.activeWorkspace || "",
      title: document.title,
      heading: heading?.textContent?.trim() || "",
      heading_focused: document.activeElement === heading,
      scroll_y: Math.round(window.scrollY),
      invalid_visible: document.querySelector("[data-stage6-invalid-route]")?.hidden === false,
      invalid_requested: invalidSurface?.querySelector("[data-stage6-invalid-route-requested]")?.textContent || "",
      invalid_recovery_label: document.querySelector("[data-stage6-invalid-route-recover]")?.textContent?.trim() || "",
      primary_dom_count: document.querySelectorAll('[data-primary-entry="true"]').length,
      active_primary_count: document.querySelectorAll('[data-primary-entry="true"].is-active').length,
    };
  });
}


async function clickRoute(page, routeAlias) {
  await page.locator(`[data-route-alias="${routeAlias}"]`).first().click();
  await page.waitForFunction((route) => window.location.pathname === route && document.querySelector("#main-workspace")?.dataset.routeAlias === route, routeAlias);
  await page.waitForTimeout(80);
  return snapshot(page);
}


await mkdir(outputDir, { recursive: true });
const profile = await mkdtemp(path.join(os.tmpdir(), "pfi-v025-s63-playwright-"));
const tracePath = path.join(outputDir, "browser_trace.zip");
const resultPath = path.join(outputDir, "playwright_result.json");
let context;
let result;
try {
  context = await chromium.launchPersistentContext(profile, {
    executablePath: chromePath,
    headless: true,
    locale: "zh-CN",
    serviceWorkers: "block",
    viewport: { width: 1440, height: 1000 },
    args: [
      "--disable-background-networking", "--disable-component-update", "--disable-default-apps",
      "--disable-domain-reliability", "--disable-extensions", "--disable-features=OptimizationHints,MediaRouter,ServiceWorker",
      "--disable-sync", "--metrics-recording-only", "--no-first-run", "--no-default-browser-check",
    ],
  });
  await context.addInitScript(() => {
    const redactEvidenceValues = () => {
      document.querySelectorAll('[data-fx-badge], [data-context-field="fx_badge"]').forEach((node) => {
        const display = "AUD/CNY=未加载";
        if ("value" in node) node.value = display;
        else if (node.textContent !== display) node.textContent = display;
        node.dataset.fxSourceLabel = display;
        node.dataset.fxEffectiveDate = "";
        node.dataset.fxCacheState = "not_loaded";
        node.dataset.evidenceRedacted = "true";
      });
      const root = document.body || document.documentElement;
      if (!root) return;
      const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
      let textNode = walker.nextNode();
      while (textNode) {
        const original = String(textNode.nodeValue || "");
        const redacted = original
          .replace(/AUD\/CNY\s*=\s*-?[0-9,.]+(?:\s*[（(][^）)]*[）)])?/g, "AUD/CNY=未加载")
          .replace(/\bCNY\s+-?[0-9][0-9,.]*/g, "CNY 已脱敏")
          .replace(/\bAUD\s+-?[0-9][0-9,.]*/g, "AUD 已脱敏");
        if (redacted !== original) textNode.nodeValue = redacted;
        textNode = walker.nextNode();
      }
      document.body?.setAttribute("data-stage6-evidence-redacted", "true");
    };
    window.__pfiStage6RedactEvidence = redactEvidenceValues;
    document.addEventListener("DOMContentLoaded", redactEvidenceValues);
    const observer = new MutationObserver(redactEvidenceValues);
    const observeDocument = () => {
      if (!document.documentElement) {
        window.setTimeout(observeDocument, 0);
        return;
      }
      observer.observe(document.documentElement, {
        childList: true,
        subtree: true,
        characterData: true,
      });
    };
    observeDocument();
  });
  await context.tracing.start({ screenshots: true, snapshots: false, sources: false });
  const baseOrigin = new URL(baseUrl).origin;
  const blockedExternal = [];
  const requestedOrigins = new Set();
  await context.route("**/*", async (route) => {
    const requestUrl = route.request().url();
    const parsed = new URL(requestUrl);
    if (["data:", "blob:", "about:"].includes(parsed.protocol) || parsed.origin === baseOrigin) {
      if (parsed.origin === baseOrigin) requestedOrigins.add(parsed.origin);
      await route.continue();
      return;
    }
    if (["127.0.0.1", "localhost"].includes(parsed.hostname) && ["/api/trends", "/api/read-model"].includes(parsed.pathname)) {
      requestedOrigins.add(parsed.origin);
      const body = parsed.pathname === "/api/trends"
        ? JSON.stringify({ trends: null, readModel: {} })
        : JSON.stringify({});
      await route.fulfill({ status: 200, contentType: "application/json", body });
      return;
    }
    blockedExternal.push(requestUrl);
    await route.abort("blockedbyclient");
  });

  const page = context.pages()[0] || await context.newPage();
  const consoleErrors = [];
  const pageErrors = [];
  const httpErrors = [];
  page.on("console", (message) => {
    if (message.type() === "error") consoleErrors.push(message.text());
  });
  page.on("pageerror", (error) => pageErrors.push(String(error?.message || error)));
  page.on("response", (response) => {
    if (response.status() >= 400) httpErrors.push({ status: response.status(), url: response.url() });
  });

  await page.goto(`${baseUrl}/accounts/reconcile`, { waitUntil: "domcontentloaded" });
  await waitForShell(page, "/accounts/reconcile");
  await page.waitForFunction(() => document.body.dataset.stage6EvidenceRedacted === "true");
  const initial = await snapshot(page);
  const list = await clickRoute(page, "/accounts/list");
  const trend = await clickRoute(page, "/accounts/trend");

  await page.evaluate(() => history.back());
  await page.waitForFunction(() => window.location.pathname === "/accounts/list");
  await page.waitForTimeout(100);
  const back = await snapshot(page);

  await page.evaluate(() => history.forward());
  await page.waitForFunction(() => window.location.pathname === "/accounts/trend");
  await page.waitForTimeout(100);
  const forward = await snapshot(page);

  await page.evaluate(() => window.scrollTo(0, 360));
  await page.waitForTimeout(80);
  await clickRoute(page, "/accounts/list");
  await page.evaluate(() => history.back());
  await page.waitForFunction(() => window.location.pathname === "/accounts/trend");
  await page.waitForTimeout(160);
  const restored = await snapshot(page);

  const historyBeforeRepeatedClick = await page.evaluate(() => window.history.length);
  await clickRoute(page, "/accounts/trend");
  await clickRoute(page, "/accounts/trend");
  const historyAfterRepeatedClick = await page.evaluate(() => window.history.length);
  const repeatedClickHistoryDelta = historyAfterRepeatedClick - historyBeforeRepeatedClick; // repeated_click_history_delta

  await page.goto(`${baseUrl}/market-research/strategy-lab`, { waitUntil: "domcontentloaded" });
  await waitForShell(page, "/market-research/strategy-lab");
  const deepLink = await snapshot(page);
  const devtools = await context.newCDPSession(page);
  await devtools.send("Page.reload", { ignoreCache: false });
  await waitForShell(page, "/market-research/strategy-lab");
  const reload = await snapshot(page);

  await page.goto(`${baseUrl}/not-a-real-route`, { waitUntil: "domcontentloaded" });
  await page.waitForFunction(() => document.querySelector("[data-stage6-invalid-route]")?.hidden === false);
  const invalid = await snapshot(page); // invalid_route_actionable
  await page.setViewportSize({ width: 390, height: 844 });
  await page.screenshot({ path: path.join(outputDir, "invalid_route_mobile.png"), fullPage: true });
  await page.locator("[data-stage6-invalid-route-recover]").click();
  await page.waitForFunction(() => window.location.pathname === "/overview");
  const recovered = await snapshot(page);

  await page.setViewportSize({ width: 1440, height: 1000 });
  const ledgerButton = page.locator('[data-primary-entry="true"][data-route-alias="/ledger"]');
  await ledgerButton.focus();
  await page.keyboard.press("Enter"); // keyboard_primary_navigation
  await page.waitForFunction(() => window.location.pathname === "/ledger");
  await page.waitForTimeout(100);
  const keyboard = await snapshot(page);
  await page.screenshot({ path: path.join(outputDir, "history_desktop.png"), fullPage: true });

  const axPayload = await devtools.send("Accessibility.getFullAXTree");
  const ax = sanitizeAxSubtree(Array.isArray(axPayload?.nodes) ? axPayload.nodes : []);
  const a11yContract = {
    source: "Accessibility.getFullAXTree",
    navigation_found: ax.navigation_found,
    primary_navigation_names: ax.primary_names,
    primary_navigation_count: ax.primary_names.length,
    primary_navigation_unique_count: new Set(ax.primary_names).size,
    expected_primary_navigation_names: expectedPrimaryNames,
    hidden_or_duplicate_primary_count: Math.max(0, ax.primary_names.length - expectedPrimaryNames.length),
    nodes: ax.nodes,
  };

  const checks = {
    canonical_path_history: [initial, list, trend, back, forward].every((item) => item.hash === "" && item.pathname === item.route_alias),
    back_forward_restores_route: back.pathname === "/accounts/list" && forward.pathname === "/accounts/trend",
    history_state_matches_url: [initial, list, trend, back, forward, reload, recovered, keyboard].every(
      (item) => item.history_state?.routeAlias === item.pathname,
    ),
    scroll_restoration: Math.abs(restored.scroll_y - 360) <= 6,
    repeated_click_no_new_entry: repeatedClickHistoryDelta === 0,
    deep_link_and_reload: deepLink.pathname === "/market-research/strategy-lab"
      && reload.pathname === deepLink.pathname
      && reload.heading === deepLink.heading,
    invalid_route_actionable: invalid.route_state === "invalid"
      && invalid.invalid_visible
      && invalid.invalid_requested === "/not-a-real-route"
      && invalid.invalid_recovery_label === "返回首页总览",
    invalid_route_recovery: recovered.pathname === "/overview" && recovered.route_state === "resolved",
    keyboard_primary_navigation: keyboard.pathname === "/ledger" && keyboard.heading_focused,
    accessibility_tree_only_ten_primary_entries: a11yContract.primary_navigation_count === 10
      && a11yContract.primary_navigation_unique_count === 10
      && expectedPrimaryNames.every((name, index) => a11yContract.primary_navigation_names[index] === name)
      && a11yContract.hidden_or_duplicate_primary_count === 0,
    dom_only_ten_primary_entries: keyboard.primary_dom_count === 10 && keyboard.active_primary_count === 1,
    console_page_http_errors: consoleErrors.length === 0 && pageErrors.length === 0 && httpErrors.length === 0,
    external_network_blocked_and_unused: blockedExternal.length === 0 && [...requestedOrigins].every((origin) => {
      const hostname = new URL(origin).hostname;
      return hostname === "127.0.0.1" || hostname === "localhost";
    }),
  };
  result = {
    schema: "PFIV025Stage6Phase63PlaywrightResultV1",
    status: Object.values(checks).every(Boolean) ? "pass" : "fail",
    driver: "cached_playwright_with_local_google_chrome_and_cdp_ax_tree",
    acceptance_id: "ACC-PFI-V025-S6-P63-HISTORY-ACCEPTANCE",
    checks,
    snapshots: { initial, list, trend, back, forward, restored, deep_link: deepLink, reload, invalid, recovered, keyboard },
    repeated_click_history_delta: repeatedClickHistoryDelta,
    a11y: a11yContract,
    console_errors: consoleErrors,
    page_errors: pageErrors,
    http_errors: httpErrors,
    requested_origins: [...requestedOrigins],
    blocked_external_requests: blockedExternal,
    external_network_performed: false,
    finder_used: false,
    evidence_redaction: "browser_init_script_fx_and_currency_values",
  };
  await writeFile(resultPath, `${JSON.stringify(result, null, 2)}\n`, "utf8");
  await context.tracing.stop({ path: tracePath });
} finally {
  if (context) await context.close().catch(() => {});
  await rm(profile, { recursive: true, force: true });
}

if (!result || result.status !== "pass") {
  throw new Error(`Phase 6.3 Playwright acceptance failed: ${JSON.stringify(result?.checks || {})}`);
}
process.stdout.write(`${JSON.stringify({ status: result.status, checks: result.checks })}\n`);
