#!/usr/bin/env node
import { createRequire } from "node:module";
import { mkdir, writeFile } from "node:fs/promises";
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
const primaryRoutes = [
  "/overview", "/accounts", "/ledger", "/investment", "/consumption",
  "/data", "/review", "/reports", "/market-research", "/settings",
];
const primaryNames = [
  "首页总览", "账户与资产", "账本流水", "投资管理", "消费管理",
  "数据源与上传", "建议与复盘", "报告与洞察", "市场与研究", "设置",
];
const aliasTargets = {
  "/home": "/overview",
  "/market": "/market-research/market",
  "/research": "/market-research/research",
  "/holdings": "/investment/holdings",
  "/strategy-lab": "/market-research/strategy-lab",
  "/investment/strategy-lab": "/market-research/strategy-lab",
  "/data-system": "/settings/data-system",
};


function valueOf(node, key) {
  return String(node?.[key]?.value || "").trim();
}


function sanitizeAxTree(nodes) {
  const byId = new Map(nodes.map((node) => [node.nodeId, node]));
  const navigation = nodes.find((node) => valueOf(node, "role") === "navigation" && valueOf(node, "name") === "一级工作区");
  const selected = [];
  const queue = navigation ? [navigation.nodeId] : [];
  const seen = new Set();
  while (queue.length) {
    const id = queue.shift();
    if (!id || seen.has(id)) continue;
    seen.add(id);
    const node = byId.get(id);
    if (!node) continue;
    selected.push({ role: valueOf(node, "role"), name: valueOf(node, "name"), ignored: node.ignored === true });
    queue.push(...(node.childIds || []));
  }
  const buttons = selected.filter((node) => !node.ignored && node.role === "button").map((node) => node.name);
  const names = primaryNames.filter((expected) => buttons.some((name) => name.includes(expected)));
  return {
    source: "Accessibility.getFullAXTree",
    navigation_found: Boolean(navigation),
    primary_navigation_names: names,
    primary_navigation_count: names.length,
    primary_navigation_unique_count: new Set(names).size,
    expected_primary_navigation_names: primaryNames,
    hidden_or_duplicate_primary_count: Math.max(0, names.length - primaryNames.length),
    nodes: selected,
  };
}


async function waitForShell(page, route) {
  await page.waitForFunction((expected) => {
    const main = document.querySelector("#main-workspace");
    return document.querySelector(".app-shell")?.hidden === false
      && document.body.dataset.pfiReleaseIdentityState === "ready"
      && window.location.pathname === expected
      && main?.dataset.routeAlias === expected;
  }, route, { timeout: 20_000 });
  await page.waitForTimeout(80);
}


async function snapshot(page) {
  return page.evaluate(() => {
    const main = document.querySelector("#main-workspace");
    const pageNode = document.querySelector("article[data-stage6-page-contract='phase_6_2']");
    const heading = document.querySelector("[data-stage6-page-heading]");
    return {
      pathname: window.location.pathname,
      route_alias: main?.dataset.routeAlias || "",
      route_state: main?.getAttribute("data-stage6-route-state") || "",
      workspace: main?.dataset.activeWorkspace || "",
      title: document.title,
      heading: heading?.textContent?.trim() || "",
      heading_focused: document.activeElement === heading,
      history_state: window.history.state,
      history_length: window.history.length,
      scroll_y: Math.round(window.scrollY),
      primary_dom_count: document.querySelectorAll('[data-primary-entry="true"]').length,
      active_primary_count: document.querySelectorAll('[data-primary-entry="true"].is-active').length,
      job: pageNode?.dataset.stage6JobToBeDone || "",
      loading: pageNode?.dataset.stage6LoadingState || "",
      empty: pageNode?.dataset.stage6EmptyState || "",
      error: pageNode?.dataset.stage6ErrorState || "",
      signature: pageNode?.dataset.stage6StructuralSignature || "",
      action: pageNode?.dataset.stage4PrimaryAction || "",
      data_object: pageNode?.dataset.stage5DataObject || "",
      invalid_visible: document.querySelector("[data-stage6-invalid-route]")?.hidden === false,
      invalid_requested: document.querySelector("[data-stage6-invalid-route-requested]")?.textContent || "",
    };
  });
}


function browserArgs() {
  return [
    "--disable-background-networking", "--disable-component-update", "--disable-default-apps",
    "--disable-domain-reliability", "--disable-extensions",
    "--disable-features=OptimizationHints,MediaRouter,ServiceWorker", "--disable-sync",
    "--metrics-recording-only", "--no-first-run", "--no-default-browser-check",
  ];
}


async function installNetworkGate(context, blockedExternal, requestedOrigins) {
  const baseOrigin = new URL(baseUrl).origin;
  await context.route("**/*", async (route) => {
    const requestUrl = route.request().url();
    const parsed = new URL(requestUrl);
    if (["data:", "blob:", "about:"].includes(parsed.protocol) || parsed.origin === baseOrigin) {
      if (parsed.origin === baseOrigin) requestedOrigins.add(parsed.origin);
      await route.continue();
      return;
    }
    if (["127.0.0.1", "localhost"].includes(parsed.hostname) && parsed.pathname.startsWith("/api/")) {
      requestedOrigins.add(parsed.origin);
      const body = parsed.pathname === "/api/trends"
        ? '{"trends":null,"readModel":{}}'
        : parsed.pathname === "/api/holdings" ? '{"holdings":[]}' : "{}";
      await route.fulfill({ status: 200, contentType: "application/json", body });
      return;
    }
    blockedExternal.push(requestUrl);
    await route.abort("blockedbyclient");
  });
}


await mkdir(outputDir, { recursive: true });
const browser = await chromium.launch({ executablePath: chromePath, headless: true, args: browserArgs() });
let result;
try {
  const context = await browser.newContext({ locale: "zh-CN", serviceWorkers: "block", viewport: { width: 1440, height: 1000 } });
  await context.addInitScript(() => {
    const redact = () => {
      const root = document.body || document.documentElement;
      if (!root) return;
      const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
      let node = walker.nextNode();
      while (node) {
        const original = String(node.nodeValue || "");
        const redacted = original
          .replace(/AUD\/CNY\s*=\s*-?[0-9,.]+(?:\s*[（(][^）)]*[）)])?/g, "AUD/CNY=未加载")
          .replace(/\bCNY\s+-?[0-9][0-9,.]*/g, "CNY 已脱敏")
          .replace(/\bAUD\s+-?[0-9][0-9,.]*/g, "AUD 已脱敏");
        if (redacted !== original) node.nodeValue = redacted;
        node = walker.nextNode();
      }
      document.body?.setAttribute("data-stage6-evidence-redacted", "true");
    };
    document.addEventListener("DOMContentLoaded", redact);
    const observer = new MutationObserver(redact);
    const start = () => document.documentElement ? observer.observe(document.documentElement, { childList: true, subtree: true, characterData: true }) : setTimeout(start, 0);
    start();
  });
  const blockedExternal = [];
  const requestedOrigins = new Set();
  await installNetworkGate(context, blockedExternal, requestedOrigins);
  await context.tracing.start({ screenshots: false, snapshots: false, sources: false });
  const page = await context.newPage();
  const consoleErrors = [];
  const pageErrors = [];
  const httpErrors = [];
  page.on("console", (message) => { if (message.type() === "error") consoleErrors.push(message.text()); });
  page.on("pageerror", (error) => pageErrors.push(String(error?.message || error)));
  page.on("response", (response) => { if (response.status() >= 400) httpErrors.push({ status: response.status(), url: response.url() }); });

  await page.goto(`${baseUrl}/overview`, { waitUntil: "domcontentloaded" });
  await waitForShell(page, "/overview");
  const primarySnapshots = [];
  for (const route of primaryRoutes) {
    await page.locator(`[data-primary-entry="true"][data-route-alias="${route}"]`).click();
    await waitForShell(page, route);
    primarySnapshots.push(await snapshot(page));
  }
  await page.screenshot({ path: path.join(outputDir, "desktop_navigation.png"), fullPage: true });

  const secondaryRoutes = await page.evaluate(() => {
    const pages = window.PFI_V025_STAGE6_PAGE_CONTRACTS?.pages || [];
    const seen = new Set();
    return pages.filter((item) => !seen.has(item.workspace) && seen.add(item.workspace)).map((item) => item.routeAlias);
  });
  const secondarySnapshots = [];
  for (const route of secondaryRoutes) {
    const primary = primaryRoutes.find((candidate) => route.startsWith(`${candidate}/`));
    await page.locator(`[data-primary-entry="true"][data-route-alias="${primary}"]`).click();
    await waitForShell(page, primary);
    await page.locator(`[data-route-alias="${route}"]`).first().click();
    await waitForShell(page, route);
    secondarySnapshots.push(await snapshot(page));
  }

  const aliasSnapshots = [];
  for (const [alias, target] of Object.entries(aliasTargets)) {
    await page.goto(`${baseUrl}${alias}`, { waitUntil: "domcontentloaded" });
    await waitForShell(page, target);
    aliasSnapshots.push({ alias, target, snapshot: await snapshot(page) });
  }

  await page.goto(`${baseUrl}/accounts/reconcile`, { waitUntil: "domcontentloaded" });
  await waitForShell(page, "/accounts/reconcile");
  await page.locator('[data-route-alias="/accounts/list"]').click();
  await waitForShell(page, "/accounts/list");
  await page.locator('[data-route-alias="/accounts/trend"]').click();
  await waitForShell(page, "/accounts/trend");
  await page.evaluate(() => history.back());
  await waitForShell(page, "/accounts/list");
  const historyBack = await snapshot(page);
  await page.evaluate(() => history.forward());
  await waitForShell(page, "/accounts/trend");
  const historyForward = await snapshot(page);
  await page.evaluate(() => window.scrollTo(0, 360));
  await page.locator('[data-route-alias="/accounts/list"]').click();
  await waitForShell(page, "/accounts/list");
  await page.evaluate(() => history.back());
  await waitForShell(page, "/accounts/trend");
  await page.waitForTimeout(120);
  const scrollRestored = await snapshot(page);
  const beforeRepeated = await page.evaluate(() => history.length);
  await page.locator('[data-route-alias="/accounts/trend"]').first().click();
  await page.locator('[data-route-alias="/accounts/trend"]').first().click();
  const repeatedDelta = (await page.evaluate(() => history.length)) - beforeRepeated;

  await page.goto(`${baseUrl}/market-research/strategy-lab`, { waitUntil: "domcontentloaded" });
  await waitForShell(page, "/market-research/strategy-lab");
  const deepLink = await snapshot(page);
  await page.reload({ waitUntil: "domcontentloaded" });
  await waitForShell(page, "/market-research/strategy-lab");
  const reload = await snapshot(page);

  await page.goto(`${baseUrl}/not-a-real-route`, { waitUntil: "domcontentloaded" });
  await page.waitForFunction(() => document.querySelector("[data-stage6-invalid-route]")?.hidden === false);
  const invalid = await snapshot(page);
  await page.screenshot({ path: path.join(outputDir, "invalid_route.png"), fullPage: true });
  await page.locator("[data-stage6-invalid-route-recover]").click();
  await waitForShell(page, "/overview");
  const recovered = await snapshot(page);

  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto(`${baseUrl}/settings/data-system`, { waitUntil: "domcontentloaded" });
  await waitForShell(page, "/settings/data-system");
  const mobile = await snapshot(page);
  await page.screenshot({ path: path.join(outputDir, "mobile_navigation.png"), fullPage: true });
  await page.setViewportSize({ width: 1440, height: 1000 });
  const devtools = await context.newCDPSession(page);
  const axPayload = await devtools.send("Accessibility.getFullAXTree");
  const a11y = sanitizeAxTree(Array.isArray(axPayload?.nodes) ? axPayload.nodes : []);

  const nojsContext = await browser.newContext({ javaScriptEnabled: false, locale: "zh-CN", viewport: { width: 1280, height: 900 } });
  const nojsBlocked = [];
  const nojsOrigins = new Set();
  await installNetworkGate(nojsContext, nojsBlocked, nojsOrigins);
  const nojsPage = await nojsContext.newPage();
  await nojsPage.goto(`${baseUrl}/overview/status`, { waitUntil: "domcontentloaded" });
  const nojs = {
    primary_route_count: await nojsPage.locator("[data-no-js-route]").count(),
    secondary_route_count: await nojsPage.locator("[data-no-js-page-route]").count(),
    directory_visible: await nojsPage.locator('[data-no-js-route-fallback="10"]').count() === 1,
  };
  await nojsPage.screenshot({ path: path.join(outputDir, "nojs_navigation.png"), fullPage: true });
  await nojsContext.close();

  const primaryExact = primarySnapshots.length === 10 && primarySnapshots.every((item, index) =>
    item.pathname === primaryRoutes[index] && item.route_alias === primaryRoutes[index]
      && item.route_state === "resolved" && item.primary_dom_count === 10 && item.active_primary_count === 1
      && item.heading_focused && item.history_state?.routeAlias === item.pathname);
  const secondaryContract = secondarySnapshots.length === 10 && secondarySnapshots.every((item) =>
    item.pathname === item.route_alias && item.job && item.loading && item.empty && item.error
      && item.heading && item.heading_focused && item.title.includes(item.heading));
  const checks = {
    primary_routes_exact_and_operable: primaryExact,
    shared_responsive_tree_and_single_active: mobile.primary_dom_count === 10 && mobile.active_primary_count === 1,
    aliases_normalize_without_primary_pollution: aliasSnapshots.length === 7 && aliasSnapshots.every((item) =>
      item.snapshot.pathname === item.target && item.snapshot.route_alias === item.target && item.snapshot.primary_dom_count === 10),
    ten_structurally_distinct_secondary_pages: secondaryContract
      && new Set(secondarySnapshots.map((item) => item.signature)).size === 10
      && new Set(secondarySnapshots.map((item) => item.data_object)).size === 10
      && new Set(secondarySnapshots.map((item) => item.action)).size === 10,
    history_back_forward_and_state: historyBack.pathname === "/accounts/list" && historyForward.pathname === "/accounts/trend"
      && historyBack.history_state?.routeAlias === historyBack.pathname && historyForward.history_state?.routeAlias === historyForward.pathname,
    scroll_restoration: Math.abs(scrollRestored.scroll_y - 360) <= 6,
    repeated_click_no_extra_history: repeatedDelta === 0,
    deep_link_reload_same_page: deepLink.pathname === "/market-research/strategy-lab" && reload.pathname === deepLink.pathname && reload.heading === deepLink.heading,
    invalid_route_actionable_and_recoverable: invalid.invalid_visible && invalid.invalid_requested === "/not-a-real-route" && recovered.pathname === "/overview",
    keyboard_focus_contract: primarySnapshots.every((item) => item.heading_focused) && secondarySnapshots.every((item) => item.heading_focused),
    accessibility_tree_exactly_ten_primary: a11y.primary_navigation_count === 10 && a11y.primary_navigation_unique_count === 10
      && primaryNames.every((name, index) => a11y.primary_navigation_names[index] === name),
    nojs_complete_and_readable: nojs.primary_route_count === 10 && nojs.secondary_route_count === 45 && nojs.directory_visible,
    no_console_page_http_errors: consoleErrors.length === 0 && pageErrors.length === 0 && httpErrors.length === 0,
    external_network_unused: blockedExternal.length === 0 && nojsBlocked.length === 0 && [...requestedOrigins, ...nojsOrigins].every((origin) => {
      const hostname = new URL(origin).hostname;
      return hostname === "127.0.0.1" || hostname === "localhost";
    }),
  };
  result = {
    schema: "PFIV025Stage6WholeReviewPlaywrightResultV1",
    status: Object.values(checks).every(Boolean) ? "pass" : "fail",
    acceptance_id: "ACC-PFI-V025-STAGE6-WHOLE-REVIEW",
    checks,
    primary_snapshots: primarySnapshots,
    secondary_snapshots: secondarySnapshots,
    alias_snapshots: aliasSnapshots,
    history: { back: historyBack, forward: historyForward, scroll_restored: scrollRestored, repeated_click_delta: repeatedDelta },
    deep_link: { before_reload: deepLink, after_reload: reload },
    invalid: { invalid, recovered },
    mobile,
    nojs,
    a11y,
    console_errors: consoleErrors,
    page_errors: pageErrors,
    http_errors: httpErrors,
    requested_origins: [...requestedOrigins],
    blocked_external_requests: blockedExternal,
    external_network_performed: false,
    finder_used: false,
    evidence_redaction: "browser_init_script_fx_and_currency_values",
  };
  await writeFile(path.join(outputDir, "playwright_result.json"), `${JSON.stringify(result, null, 2)}\n`, "utf8");
  await context.tracing.stop({ path: path.join(outputDir, "browser_trace.zip") });
  await context.close();
} finally {
  await browser.close();
}

if (!result || result.status !== "pass") {
  throw new Error(`Stage 6 whole-stage Playwright acceptance failed: ${JSON.stringify(result?.checks || {})}`);
}
process.stdout.write(`${JSON.stringify({ status: result.status, checks: result.checks })}\n`);
