#!/usr/bin/env node
import { createHash } from "node:crypto";
import { createReadStream } from "node:fs";
import { mkdir, readFile, stat, unlink, writeFile } from "node:fs/promises";
import http from "node:http";
import { createRequire } from "node:module";
import path from "node:path";
import { pathToFileURL } from "node:url";
import { spawnSync } from "node:child_process";


const require = createRequire(import.meta.url);
const args = Object.fromEntries(process.argv.slice(2).reduce((pairs, value, index, values) => {
  if (value.startsWith("--")) pairs.push([value.slice(2), values[index + 1]]);
  return pairs;
}, []));
const webRoot = path.resolve(String(args["web-root"] || ""));
const outputDir = path.resolve(String(args["output-dir"] || ""));
const baselineDir = path.resolve(String(args["baseline-dir"] || path.join(outputDir, "..", "phase_8_1")));
const chromePath = path.resolve(String(args.chrome || "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"));
const moduleDir = process.env.PFI_PLAYWRIGHT_MODULE_DIR;
if (!args["web-root"] || !args["output-dir"] || !moduleDir) {
  throw new Error("--web-root, --output-dir and PFI_PLAYWRIGHT_MODULE_DIR are required");
}
const { chromium } = require(path.join(moduleDir, "playwright"));
const { PNG } = require(require.resolve("pngjs", { paths: [moduleDir] }));
const pixelmatchPath = require.resolve("pixelmatch", { paths: [moduleDir] });
const pixelmatchModule = await import(pathToFileURL(pixelmatchPath).href);
const pixelmatch = pixelmatchModule.default || pixelmatchModule;

const PRIMARY_ROUTES = Object.freeze([
  Object.freeze({ workspace: "home", route: "/overview" }),
  Object.freeze({ workspace: "accounts", route: "/accounts/overview" }),
  Object.freeze({ workspace: "ledger", route: "/ledger/list" }),
  Object.freeze({ workspace: "investment", route: "/investment/overview" }),
  Object.freeze({ workspace: "consumption", route: "/consumption/overview" }),
  Object.freeze({ workspace: "sync", route: "/data/upload" }),
  Object.freeze({ workspace: "recommendations", route: "/review/list" }),
  Object.freeze({ workspace: "insights", route: "/reports/monthly" }),
  Object.freeze({ workspace: "market_research", route: "/market-research/research" }),
  Object.freeze({ workspace: "settings", route: "/settings/account" }),
]);
const SECONDARY_ROUTES = Object.freeze([
  "/overview/status", "/accounts/reconcile", "/ledger/review", "/investment/holdings",
  "/consumption/budget", "/data/sources", "/review/detail", "/reports/custom",
  "/market-research/strategy-lab", "/settings/feedback",
]);
const SECONDARY_SCREENSHOT_ROUTES = Object.freeze([
  Object.freeze({ pageId: "home_status", workspace: "home", route: "/overview/status" }),
  Object.freeze({ pageId: "accounts_reconcile", workspace: "accounts", route: "/accounts/reconcile" }),
  Object.freeze({ pageId: "ledger_review", workspace: "ledger", route: "/ledger/review" }),
  Object.freeze({ pageId: "investment_holdings", workspace: "investment", route: "/investment/holdings" }),
  Object.freeze({ pageId: "consumption_budget", workspace: "consumption", route: "/consumption/budget" }),
  Object.freeze({ pageId: "sync_sources", workspace: "sync", route: "/data/sources" }),
  Object.freeze({ pageId: "recommendations_detail", workspace: "recommendations", route: "/review/detail" }),
  Object.freeze({ pageId: "insights_custom", workspace: "insights", route: "/reports/custom" }),
  Object.freeze({ pageId: "market_strategy_lab", workspace: "market_research", route: "/market-research/strategy-lab" }),
  Object.freeze({ pageId: "settings_feedback", workspace: "settings", route: "/settings/feedback" }),
]);
if (PRIMARY_ROUTES.length !== 10) throw new Error("PRIMARY_ROUTES.length !== 10");
if (SECONDARY_ROUTES.length < 8) throw new Error("SECONDARY_ROUTES.length < 8");

const CONTENT_TYPES = Object.freeze({
  ".css": "text/css; charset=utf-8", ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8", ".json": "application/json; charset=utf-8",
  ".mjs": "text/javascript; charset=utf-8", ".png": "image/png", ".svg": "image/svg+xml",
});

function browserArgs() {
  return [
    "--disable-background-networking", "--disable-component-update", "--disable-default-apps",
    "--disable-domain-reliability", "--disable-extensions",
    "--disable-features=OptimizationHints,MediaRouter,ServiceWorker", "--disable-sync",
    "--disable-gpu", "--metrics-recording-only", "--no-first-run", "--no-default-browser-check",
  ];
}

function jsonResponse(response, statusCode, payload) {
  const body = JSON.stringify(payload);
  response.writeHead(statusCode, {
    "Cache-Control": "no-store", "Content-Type": "application/json; charset=utf-8",
    "Content-Length": Buffer.byteLength(body),
  });
  response.end(body);
}

function runtimeConfig(baseUrl) {
  return JSON.stringify({
    apiBaseUrl: baseUrl, readModelStatusApi: false, runtimeApiEnabled: false,
    releaseManifestApi: false, releaseCachePolicyApi: false,
    stage1OfficialCandidate: false, candidateDataMode: "canonical",
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
        response.writeHead(200, { "Cache-Control": "no-store", "Content-Type": CONTENT_TYPES[extension] || "application/octet-stream" });
        createReadStream(candidate).pipe(response);
        return;
      }
      const markup = await transformedIndex(baseUrl);
      response.writeHead(200, {
        "Cache-Control": "no-store", "Content-Type": "text/html; charset=utf-8",
        "Content-Length": Buffer.byteLength(markup),
      });
      response.end(markup);
    } catch (error) {
      jsonResponse(response, 500, { error: String(error?.message || error) });
    }
  });
  await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
  const address = server.address();
  if (!address || typeof address === "string") throw new Error("loopback server address unavailable");
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

async function routeLoopbackOnly(context, baseUrl, diagnostics) {
  const origin = new URL(baseUrl).origin;
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
}

async function waitForReady(page) {
  await page.waitForFunction(() => (
    document.querySelector(".app-shell")?.hidden === false
    && document.body.dataset.pfiReleaseIdentityState === "ready"
    && Boolean(window.PFI_V025_STAGE8_ACCESSIBILITY)
    && document.body.dataset.v025Stage8PrimaryEntryCount === "10"
    && Boolean(document.querySelector("#main-workspace")?.dataset.routeAlias)
  ), null, { timeout: 30_000 });
  await page.waitForTimeout(250);
}

async function auditDocument(page) {
  return page.evaluate(() => {
    const visible = (node) => {
      if (!(node instanceof Element)) return false;
      const style = getComputedStyle(node);
      const rect = node.getBoundingClientRect();
      return !node.hidden && style.display !== "none" && style.visibility !== "hidden"
        && Number(style.opacity) > 0.01 && rect.width > 0 && rect.height > 0;
    };
    const parseColor = (value) => {
      const serialized = String(value || "").trim().toLowerCase();
      const parts = serialized.match(/[\d.]+/g)?.map(Number) || [];
      if (parts.length < 3) return null;
      if (serialized.startsWith("color(srgb ")) {
        return { r: parts[0] * 255, g: parts[1] * 255, b: parts[2] * 255, a: parts.length > 3 ? parts[3] : 1 };
      }
      return { r: parts[0], g: parts[1], b: parts[2], a: parts.length > 3 ? parts[3] : 1 };
    };
    const composite = (front, back) => ({
      r: front.r * front.a + back.r * (1 - front.a),
      g: front.g * front.a + back.g * (1 - front.a),
      b: front.b * front.a + back.b * (1 - front.a), a: 1,
    });
    const backgroundFor = (node) => {
      const layers = [];
      for (let current = node; current instanceof Element; current = current.parentElement) {
        const color = parseColor(getComputedStyle(current).backgroundColor);
        if (color && color.a > 0) layers.push(color);
      }
      let result = { r: 255, g: 255, b: 255, a: 1 };
      for (const layer of layers.reverse()) result = composite(layer, result);
      return result;
    };
    const luminance = (color) => {
      const channels = [color.r, color.g, color.b].map((value) => {
        const normalized = value / 255;
        return normalized <= 0.04045 ? normalized / 12.92 : ((normalized + 0.055) / 1.055) ** 2.4;
      });
      return channels[0] * 0.2126 + channels[1] * 0.7152 + channels[2] * 0.0722;
    };
    const contrastRatio = (foreground, background) => {
      const front = foreground.a < 1 ? composite(foreground, background) : foreground;
      const a = luminance(front);
      const b = luminance(background);
      return (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05);
    };
    const selectorFor = (node) => {
      if (node.id) return `#${node.id}`;
      const marker = [...node.attributes].find((item) => item.name.startsWith("data-"));
      return marker ? `${node.tagName.toLowerCase()}[${marker.name}]` : `${node.tagName.toLowerCase()}.${[...node.classList].slice(0, 2).join(".")}`;
    };
    const contrastFailures = [];
    const textSamples = [];
    document.querySelectorAll("body *").forEach((node) => {
      if (!visible(node) || node.closest("[aria-hidden='true']")) return;
      const directText = [...node.childNodes].filter((child) => child.nodeType === Node.TEXT_NODE)
        .map((child) => child.textContent).join(" ").replace(/\s+/g, " ").trim();
      if (!directText) return;
      const style = getComputedStyle(node);
      const foreground = parseColor(style.color);
      if (!foreground) return;
      const background = backgroundFor(node);
      const ratio = contrastRatio(foreground, background);
      const fontSize = Number.parseFloat(style.fontSize || "0");
      const fontWeight = Number.parseInt(style.fontWeight || "400", 10) || 400;
      const threshold = fontSize >= 24 || (fontSize >= 18.66 && fontWeight >= 700) ? 3 : 4.5;
      const sample = { selector: selectorFor(node), text: directText.slice(0, 80), ratio: Number(ratio.toFixed(3)), threshold };
      textSamples.push(sample);
      if (ratio + 0.01 < threshold) contrastFailures.push(sample);
    });
    document.querySelectorAll("input[placeholder], textarea[placeholder]").forEach((node) => {
      if (!visible(node)) return;
      const style = getComputedStyle(node, "::placeholder");
      const foreground = parseColor(style.color);
      if (!foreground) return;
      const ratio = contrastRatio(foreground, backgroundFor(node));
      const sample = { selector: selectorFor(node), text: node.getAttribute("placeholder") || "", ratio: Number(ratio.toFixed(3)), threshold: 4.5, pseudo: "placeholder" };
      textSamples.push(sample);
      if (ratio + 0.01 < 4.5) contrastFailures.push(sample);
    });
    const interactiveSelector = "a[href],button,input,select,textarea,summary,[role='button'],[role='option'],[tabindex='0']";
    const unnamedInteractive = [];
    const targetSizeFailures = [];
    document.querySelectorAll(interactiveSelector).forEach((node) => {
      if (!visible(node) || node.disabled || node.closest("[inert]")) return;
      const labelledBy = String(node.getAttribute("aria-labelledby") || "").split(/\s+/).filter(Boolean)
        .map((id) => document.getElementById(id)?.textContent?.trim() || "").join(" ").trim();
      const implicitLabels = [...(node.labels || [])].map((label) => label.textContent?.trim() || "").join(" ").trim();
      const name = node.getAttribute("aria-label") || labelledBy || implicitLabels || node.getAttribute("alt")
        || node.getAttribute("title") || node.textContent?.trim() || node.getAttribute("placeholder") || "";
      if (!name.trim()) unnamedInteractive.push({ selector: selectorFor(node), tag: node.tagName });
      if (node.matches(".skip-link")) return;
      const rect = node.getBoundingClientRect();
      const required = 44;
      if (rect.width + 0.5 < required || rect.height + 0.5 < required) {
        targetSizeFailures.push({ selector: selectorFor(node), width: Number(rect.width.toFixed(2)), height: Number(rect.height.toFixed(2)), required });
      }
    });
    const ids = [...document.querySelectorAll("[id]")].map((node) => node.id);
    const duplicateIds = [...new Set(ids.filter((id, index) => ids.indexOf(id) !== index))];
    const headingLevels = [...document.querySelectorAll("h1,h2,h3,h4,h5,h6")].filter(visible)
      .map((node) => Number(node.tagName.slice(1)));
    const headingOrderJumps = headingLevels.filter((level, index) => index > 0 && level - headingLevels[index - 1] > 1);
    return {
      route: document.querySelector("#main-workspace")?.dataset.routeAlias || location.pathname,
      text_sample_count: textSamples.length,
      contrast_failures: contrastFailures,
      unnamed_interactive_nodes: unnamedInteractive,
      target_size_failures: targetSizeFailures,
      duplicate_ids: duplicateIds,
      main_landmark_count: document.querySelectorAll("main").length,
      heading_order_jump_count: headingOrderJumps.length,
      status_region_count: document.querySelectorAll("[role='status'][aria-live]").length,
      alert_region_count: document.querySelectorAll("[role='alert'][aria-live]").length,
      error_prevention_binding_count: document.querySelectorAll("[data-stage8-error-prevention]").length,
      primary_navigation_entry_count: document.querySelectorAll('[data-primary-entry="true"]').length,
    };
  });
}

async function runRouteAudits(browser, baseUrl, diagnostics) {
  const context = await browser.newContext({
    locale: "zh-CN", serviceWorkers: "block", viewport: { width: 1440, height: 1000 },
    colorScheme: "light", reducedMotion: "reduce",
  });
  await routeLoopbackOnly(context, baseUrl, diagnostics);
  const page = await context.newPage();
  watchPage(page, diagnostics);
  const primary = [];
  const secondary = [];
  try {
    for (const item of PRIMARY_ROUTES) {
      await page.goto(`${baseUrl}${item.route}`, { waitUntil: "domcontentloaded" });
      await waitForReady(page);
      primary.push({ workspace: item.workspace, ...(await auditDocument(page)) });
    }
    for (const route of SECONDARY_ROUTES) {
      await page.goto(`${baseUrl}${route}`, { waitUntil: "domcontentloaded" });
      await waitForReady(page);
      secondary.push(await auditDocument(page));
    }
  } finally {
    await context.close();
  }
  return { primary, secondary };
}

async function keyboardFlow(browser, baseUrl, diagnostics, rawTracePath) {
  const context = await browser.newContext({
    locale: "zh-CN", serviceWorkers: "block", viewport: { width: 1440, height: 1000 }, reducedMotion: "reduce",
  });
  await routeLoopbackOnly(context, baseUrl, diagnostics);
  await context.tracing.start({ screenshots: false, snapshots: false, sources: false });
  const page = await context.newPage();
  watchPage(page, diagnostics);
  try {
    await page.goto(`${baseUrl}/overview`, { waitUntil: "domcontentloaded" });
    await waitForReady(page);
    await page.keyboard.press("Tab");
    const firstTab = await page.evaluate(() => ({
      isSkipLink: document.activeElement?.matches(".skip-link") === true,
      outlineWidth: getComputedStyle(document.activeElement).outlineWidth,
    }));
    await page.keyboard.press("Enter");
    await page.waitForTimeout(100);
    const skipDestination = await page.evaluate(() => document.activeElement?.id === "main-workspace");

    await page.focus('[data-primary-entry="true"][data-workspace="accounts"]');
    const primaryFocus = await page.evaluate(() => {
      const node = document.activeElement;
      const style = getComputedStyle(node);
      const rect = node.getBoundingClientRect();
      return {
        workspace: node?.getAttribute("data-workspace") || "", outlineWidth: style.outlineWidth,
        unobscured: rect.top >= 0 && rect.bottom <= innerHeight && rect.left >= 0 && rect.right <= innerWidth,
      };
    });
    await page.keyboard.press("Enter");
    await page.waitForFunction(() => document.querySelector("#main-workspace")?.dataset.activeWorkspace === "accounts");
    await page.waitForTimeout(100);
    const primaryHeadingFocused = await page.evaluate(() => (
      document.activeElement === document.querySelector("[data-stage6-page-heading]")
      || document.activeElement === document.querySelector("#workspace-title")
    ));

    const secondarySelector = '[data-secondary-tab][data-route-alias="/accounts/reconcile"]';
    await page.focus(secondarySelector);
    const secondaryRoute = await page.getAttribute(secondarySelector, "data-route-alias");
    await page.keyboard.press("Enter");
    await page.waitForFunction((route) => document.querySelector("#main-workspace")?.dataset.routeAlias === route, secondaryRoute);
    await page.waitForTimeout(100);
    const secondaryHeadingFocused = await page.evaluate(() => document.activeElement?.matches("[data-stage6-page-heading]") === true);

    await page.keyboard.press("Control+k");
    const searchFocused = await page.evaluate(() => document.activeElement?.matches("[data-global-search-input]") === true);
    await page.keyboard.type("设置");
    await page.keyboard.press("ArrowDown");
    await page.keyboard.press("Enter");
    await page.waitForTimeout(120);
    const searchOpenedRoute = await page.evaluate(() => document.querySelector("#main-workspace")?.dataset.routeAlias || "");

    await page.focus("#main-workspace");
    const focusSequence = [];
    for (let index = 0; index < 30; index += 1) {
      await page.keyboard.press("Tab");
      focusSequence.push(await page.evaluate(() => {
        const node = document.activeElement;
        return node?.id || node?.getAttribute("data-workspace") || node?.getAttribute("data-secondary-tab")
          || node?.getAttribute("data-route-alias") || node?.getAttribute("data-command-open") || node?.tagName || "";
      }));
    }
    const uniqueFocusTargets = [...new Set(focusSequence.filter(Boolean))];
    const routeAnnouncer = await page.evaluate(() => document.querySelector("[data-stage8-route-announcer]")?.textContent?.trim() || "");
    const result = {
      schema: "PFIV025Stage8Phase83KeyboardFlowV1",
      status: "pending",
      skip_link_to_main_passed: firstTab.isSkipLink && skipDestination,
      primary_navigation_passed: primaryFocus.workspace === "accounts" && primaryHeadingFocused,
      secondary_navigation_passed: Boolean(secondaryRoute) && secondaryHeadingFocused,
      focus_not_obscured_passed: primaryFocus.unobscured && Number.parseFloat(primaryFocus.outlineWidth) >= 3,
      global_search_keyboard_passed: searchFocused && Boolean(searchOpenedRoute),
      no_keyboard_trap: uniqueFocusTargets.length >= 8,
      first_tab: firstTab,
      secondary_route: secondaryRoute,
      search_opened_route: searchOpenedRoute,
      unique_focus_target_count: uniqueFocusTargets.length,
      focus_sequence: focusSequence,
      route_announcer_text: routeAnnouncer,
    };
    result.status = [
      result.skip_link_to_main_passed, result.primary_navigation_passed, result.secondary_navigation_passed,
      result.focus_not_obscured_passed, result.global_search_keyboard_passed, result.no_keyboard_trap,
      Boolean(result.route_announcer_text),
    ].every(Boolean) ? "pass" : "fail";
    return result;
  } finally {
    await context.tracing.stop({ path: rawTracePath });
    await context.close();
  }
}

async function accessibilityTree(browser, baseUrl, diagnostics) {
  const context = await browser.newContext({ locale: "zh-CN", serviceWorkers: "block", viewport: { width: 1440, height: 1000 } });
  await routeLoopbackOnly(context, baseUrl, diagnostics);
  const page = await context.newPage();
  watchPage(page, diagnostics);
  try {
    const devtools = await context.newCDPSession(page);
    await devtools.send("Accessibility.enable");
    const interactiveRoles = new Set(["button", "link", "textbox", "combobox", "checkbox", "radio", "menuitem", "option", "switch", "tab"]);
    const routes = [...PRIMARY_ROUTES.map((item) => item.route), ...SECONDARY_ROUTES];
    const routeSummaries = [];
    for (const route of routes) {
      await page.goto(`${baseUrl}${route}`, { waitUntil: "domcontentloaded" });
      await waitForReady(page);
      const payload = await devtools.send("Accessibility.getFullAXTree");
      const roleCounts = {};
      const unnamed = [];
      for (const node of payload.nodes || []) {
        const role = String(node.role?.value || "");
        if (!role || node.ignored) continue;
        roleCounts[role] = (roleCounts[role] || 0) + 1;
        if (interactiveRoles.has(role) && !String(node.name?.value || "").trim()) {
          unnamed.push({ role, backend_dom_node_id: node.backendDOMNodeId || null });
        }
      }
      const dom = await page.evaluate(() => {
        const ids = [...document.querySelectorAll("[id]")].map((node) => node.id);
        return {
          route: document.querySelector("#main-workspace")?.dataset.routeAlias || location.pathname,
          duplicateIds: [...new Set(ids.filter((id, index) => ids.indexOf(id) !== index))],
          primaryNavigationEntryCount: document.querySelectorAll('[data-primary-entry="true"]').length,
        };
      });
      routeSummaries.push({
        route: dom.route,
        summarized_node_count: Object.values(roleCounts).reduce((sum, value) => sum + value, 0),
        role_counts: roleCounts,
        landmark_count: (roleCounts.main || 0) + (roleCounts.navigation || 0) + (roleCounts.banner || 0) + (roleCounts.contentinfo || 0),
        heading_count: roleCounts.heading || 0,
        unnamed_interactive_node_count: unnamed.length,
        unnamed_interactive_nodes: unnamed,
        duplicate_id_count: dom.duplicateIds.length,
        duplicate_ids: dom.duplicateIds,
        primary_navigation_entry_count: dom.primaryNavigationEntryCount,
      });
    }
    const status = routeSummaries.length === 20 && routeSummaries.every((item) => (
      item.unnamed_interactive_node_count === 0
      && item.duplicate_id_count === 0
      && item.primary_navigation_entry_count === 10
      && item.landmark_count >= 2
      && item.heading_count > 0
    ));
    return {
      schema: "PFIV025Stage8Phase83AccessibilityTreeV1",
      source: "Accessibility.getFullAXTree",
      status: status ? "pass" : "fail",
      audited_route_count: routeSummaries.length,
      unique_route_count: new Set(routeSummaries.map((item) => item.route)).size,
      summarized_node_count: routeSummaries.reduce((sum, item) => sum + item.summarized_node_count, 0),
      unnamed_interactive_node_count: routeSummaries.reduce((sum, item) => sum + item.unnamed_interactive_node_count, 0),
      duplicate_id_count: routeSummaries.reduce((sum, item) => sum + item.duplicate_id_count, 0),
      route_summaries: routeSummaries,
      raw_tree_persisted: false,
    };
  } finally {
    await context.close();
  }
}

async function errorPreventionAudit(browser, baseUrl, diagnostics) {
  const context = await browser.newContext({ locale: "zh-CN", serviceWorkers: "block", viewport: { width: 1440, height: 1000 } });
  await routeLoopbackOnly(context, baseUrl, diagnostics);
  const page = await context.newPage();
  watchPage(page, diagnostics);
  try {
    const routes = ["/data/upload", "/investment/holdings", "/settings/account"];
    const snapshots = [];
    for (const route of routes) {
      await page.goto(`${baseUrl}${route}`, { waitUntil: "domcontentloaded" });
      await waitForReady(page);
      snapshots.push(await page.evaluate(() => ({
        route: document.querySelector("#main-workspace")?.dataset.routeAlias || location.pathname,
        bindings: [...document.querySelectorAll("[data-stage8-error-prevention]")].map((node) => ({
          marker: node.getAttribute("data-stage8-error-prevention") || "",
          describedBy: node.getAttribute("aria-describedby") || "",
          descriptorExists: String(node.getAttribute("aria-describedby") || "").split(/\s+/).filter(Boolean)
            .every((id) => Boolean(document.getElementById(id))),
          disabled: Boolean(node.disabled),
        })),
        importConfirmDisabledBeforePreview: document.querySelector("[data-import-confirm]")?.disabled === true,
      })));
    }
    const bindings = snapshots.flatMap((item) => item.bindings);
    const markers = new Set(bindings.map((item) => item.marker));
    const requiredMarkers = [
      "import-preview-before-commit", "holding-review-before-save", "holding-reset-state",
      "holding-soft-delete-confirmation", "settings-review-before-save", "settings-reset-state",
    ];
    const result = {
      schema: "PFIV025Stage8Phase83ErrorPreventionAuditV1", status: "pending",
      financial_data_loaded: false, database_changed: false,
      import_confirm_disabled_before_preview: snapshots.some((item) => item.importConfirmDisabledBeforePreview),
      described_control_count: markers.size,
      missing_markers: requiredMarkers.filter((marker) => !markers.has(marker)),
      all_descriptors_resolve: bindings.length > 0 && bindings.every((item) => item.describedBy && item.descriptorExists),
      snapshots,
    };
    result.status = result.import_confirm_disabled_before_preview && result.missing_markers.length === 0
      && result.all_descriptors_resolve ? "pass" : "fail";
    return result;
  } finally {
    await context.close();
  }
}

async function captureAndCompare(browser, baseUrl, diagnostics) {
  const results = [];
  const viewports = [
    { kind: "desktop", width: 1440, height: 1000 },
    { kind: "mobile", width: 390, height: 844 },
  ];
  const allowedDiffRatio = 0.12;
  const routes = [
    ...PRIMARY_ROUTES.map((item) => ({ ...item, pageId: item.workspace, pageKind: "primary" })),
    ...SECONDARY_SCREENSHOT_ROUTES.map((item) => ({ ...item, pageKind: "secondary" })),
  ];
  for (const viewport of viewports) {
    for (const item of routes) {
      const directoryName = item.pageKind === "primary" ? `${viewport.kind}_pages` : `${viewport.kind}_secondary`;
      const screenshotDir = path.join(outputDir, directoryName);
      await mkdir(screenshotDir, { recursive: true });
      const context = await browser.newContext({
        locale: "zh-CN", serviceWorkers: "block", viewport: { width: viewport.width, height: viewport.height },
        colorScheme: "light", reducedMotion: "reduce", deviceScaleFactor: 1,
      });
      await routeLoopbackOnly(context, baseUrl, diagnostics);
      const page = await context.newPage();
      watchPage(page, diagnostics);
      try {
        await page.goto(`${baseUrl}${item.route}`, { waitUntil: "domcontentloaded" });
        await waitForReady(page);
        const identity = await page.evaluate(() => {
          const manifest = JSON.parse(document.querySelector("#pfi-release-manifest")?.textContent || "{}");
          return {
            badge: document.querySelector("[data-pfi-entry-bundle-hash]")?.textContent?.trim() || "",
            frontendHash: String(manifest.frontend_bundle_hash || ""),
          };
        });
        const screenshotPath = path.join(screenshotDir, `${item.pageId}.png`);
        await page.screenshot({ path: screenshotPath, fullPage: false, animations: "disabled" });
        const baselineDirectory = item.pageKind === "primary" ? `${viewport.kind}_pages` : `${viewport.kind}_secondary`;
        const baselinePath = path.join(baselineDir, baselineDirectory, `${item.pageId}.png`);
        let decodeFailure = false;
        let dimensionMismatch = false;
        let diffRatio = 1;
        let nearBlackRatio = 1;
        try {
          const current = PNG.sync.read(await readFile(screenshotPath));
          const baseline = PNG.sync.read(await readFile(baselinePath));
          let nearBlackPixels = 0;
          for (let offset = 0; offset < current.data.length; offset += 4) {
            if (current.data[offset] < 8 && current.data[offset + 1] < 8 && current.data[offset + 2] < 8 && current.data[offset + 3] > 245) {
              nearBlackPixels += 1;
            }
          }
          nearBlackRatio = nearBlackPixels / (current.width * current.height);
          dimensionMismatch = current.width !== baseline.width || current.height !== baseline.height;
          if (!dimensionMismatch) {
            const diff = new PNG({ width: current.width, height: current.height });
            const mismatchedPixels = pixelmatch(baseline.data, current.data, diff.data, current.width, current.height, { threshold: 0.15, includeAA: false });
            diffRatio = mismatchedPixels / (current.width * current.height);
          }
        } catch (_error) {
          decodeFailure = true;
        }
        results.push({
          page_id: item.pageId, page_kind: item.pageKind, workspace: item.workspace, route: item.route, viewport: viewport.kind,
          width: viewport.width, height: viewport.height,
          screenshot_bytes: (await stat(screenshotPath)).size,
          screenshot: `${directoryName}/${item.pageId}.png`,
          baseline: `${baselineDirectory}/${item.pageId}.png`,
          decode_failure: decodeFailure, dimension_mismatch: dimensionMismatch,
          release_badge: identity.badge,
          embedded_frontend_hash: identity.frontendHash,
          release_badge_match: identity.badge === `bundle ${identity.frontendHash.slice(0, 16)}`,
          near_black_ratio: Number(nearBlackRatio.toFixed(8)),
          diff_ratio: Number(diffRatio.toFixed(6)), allowed_diff_ratio: allowedDiffRatio,
          passed: !decodeFailure && !dimensionMismatch && diffRatio <= allowedDiffRatio
            && nearBlackRatio < 0.001 && identity.badge === `bundle ${identity.frontendHash.slice(0, 16)}`,
        });
      } finally {
        await context.close();
      }
    }
  }
  const maximum = Math.max(...results.map((item) => item.diff_ratio));
  return {
    schema: "PFIV025Stage8Phase83VisualRegressionV1",
    status: results.every((item) => item.passed) ? "pass" : "fail",
    baseline_semantics: "stage8_whole_review_repaired_content_commit",
    primary_page_count: PRIMARY_ROUTES.length,
    secondary_page_count: SECONDARY_SCREENSHOT_ROUTES.length,
    unique_route_count: new Set(results.map((item) => item.route)).size,
    viewport_count: viewports.length, screenshot_count: results.length,
    decode_failure_count: results.filter((item) => item.decode_failure).length,
    dimension_mismatch_count: results.filter((item) => item.dimension_mismatch).length,
    regression_failure_count: results.filter((item) => !item.passed).length,
    maximum_diff_ratio: Number(maximum.toFixed(6)), allowed_diff_ratio: allowedDiffRatio,
    comparator: { engine: "pixelmatch", threshold: 0.15, antialiasing_ignored: true }, results,
  };
}

function aggregateWcag(routeAudits, errorPrevention) {
  const audits = [...routeAudits.primary, ...routeAudits.secondary];
  const contrastFailures = audits.flatMap((item) => item.contrast_failures.map((failure) => ({ route: item.route, ...failure })));
  const targetFailures = audits.flatMap((item) => item.target_size_failures.map((failure) => ({ route: item.route, ...failure })));
  const unnamed = audits.flatMap((item) => item.unnamed_interactive_nodes.map((failure) => ({ route: item.route, ...failure })));
  const duplicateIds = audits.flatMap((item) => item.duplicate_ids.map((id) => ({ route: item.route, id })));
  const structural = audits.filter((item) => item.main_landmark_count !== 1 || item.heading_order_jump_count > 0);
  const blockingViolationCount = contrastFailures.length + targetFailures.length + unnamed.length + duplicateIds.length + structural.length
    + (errorPrevention.status === "pass" ? 0 : 1);
  return {
    schema: "PFIV025Stage8Phase83WCAGAuditV1", standard: "WCAG 2.2 AA",
    engine: "local_deterministic_wcag22aa_contrast_ax_keyboard", axe_core_available: false,
    axe_disposition: "not_claimed; normalized axe_results.json must retain engine_unavailable and bind the deterministic substitute",
    status: blockingViolationCount === 0 ? "pass" : "fail",
    audited_primary_page_count: routeAudits.primary.length,
    audited_secondary_page_count: routeAudits.secondary.length,
    audited_route_count: audits.length,
    unique_route_count: new Set(audits.map((item) => item.route)).size,
    text_sample_count: audits.reduce((sum, item) => sum + item.text_sample_count, 0),
    blocking_violation_count: blockingViolationCount,
    contrast_failure_count: contrastFailures.length,
    target_size_failure_count: targetFailures.length,
    unnamed_interactive_count: unnamed.length,
    duplicate_id_count: duplicateIds.length,
    structural_failure_count: structural.length,
    financial_data_error_prevention_passed: errorPrevention.status === "pass",
    contrast_failures: contrastFailures, target_size_failures: targetFailures,
    unnamed_interactive_nodes: unnamed, duplicate_ids: duplicateIds,
    structural_failures: structural.map((item) => ({ route: item.route, main_landmark_count: item.main_landmark_count, heading_order_jump_count: item.heading_order_jump_count })),
    route_summaries: audits.map((item) => ({
      route: item.route, text_sample_count: item.text_sample_count,
      status_region_count: item.status_region_count, alert_region_count: item.alert_region_count,
      error_prevention_binding_count: item.error_prevention_binding_count,
    })),
  };
}

async function writeJson(name, payload) {
  await writeFile(path.join(outputDir, name), `${JSON.stringify(payload, null, 2)}\n`, "utf8");
}

await mkdir(outputDir, { recursive: true });
const rawTracePath = path.join(outputDir, ".browser_trace_raw.zip");
const tracePath = path.join(outputDir, "browser_trace.zip");
const diagnostics = { consoleErrors: [], pageErrors: [], httpErrors: [], blockedExternal: [], requestedOrigins: new Set() };
const { server, baseUrl } = await startServer();
console.log(`[stage8-phase83] loopback:${baseUrl}`);
const browser = await chromium.launch({ executablePath: chromePath, headless: true, args: browserArgs() });
let browserValidation;
try {
  const routeAudits = await runRouteAudits(browser, baseUrl, diagnostics);
  console.log(`[stage8-phase83] route-audits:${routeAudits.primary.length + routeAudits.secondary.length}`);
  const keyboard = await keyboardFlow(browser, baseUrl, diagnostics, rawTracePath);
  console.log(`[stage8-phase83] keyboard:${keyboard.status}`);
  const axTree = await accessibilityTree(browser, baseUrl, diagnostics);
  console.log(`[stage8-phase83] ax-tree:${axTree.status}`);
  const errorPrevention = await errorPreventionAudit(browser, baseUrl, diagnostics);
  console.log(`[stage8-phase83] error-prevention:${errorPrevention.status}`);
  const visual = await captureAndCompare(browser, baseUrl, diagnostics);
  console.log(`[stage8-phase83] visual:${visual.status}:${visual.maximum_diff_ratio}`);
  const wcag = aggregateWcag(routeAudits, errorPrevention);
  const checks = {
    wcag_22_aa_zero_blocking: wcag.status === "pass" && wcag.blocking_violation_count === 0
      && wcag.unique_route_count === 20,
    keyboard_flow_pass: keyboard.status === "pass",
    accessibility_tree_pass: axTree.status === "pass",
    financial_error_prevention_pass: errorPrevention.status === "pass",
    visual_regression_pass: visual.status === "pass" && visual.screenshot_count === 40
      && visual.unique_route_count === 20,
    no_console_errors: diagnostics.consoleErrors.length === 0,
    no_page_errors: diagnostics.pageErrors.length === 0,
    no_http_errors: diagnostics.httpErrors.length === 0,
    no_external_requests: diagnostics.blockedExternal.length === 0
      && [...diagnostics.requestedOrigins].every((origin) => origin === new URL(baseUrl).origin),
  };
  browserValidation = {
    schema: "PFIV025Stage8Phase83BrowserValidationV1",
    status: Object.values(checks).every(Boolean) ? "pass" : "fail",
    contract_id: "PFI-V025-STAGE8-PHASE83-ACCESSIBILITY-HUMAN-QUALITY",
    acceptance_id: "ACC-PFI-V025-STAGE8-WHOLE-REVIEW",
    method: "actual_current_worktree_formal_shell_playwright_cdp_ephemeral_loopback",
    actual_formal_shell: true, checks,
    audited_primary_page_count: routeAudits.primary.length,
    audited_secondary_page_count: routeAudits.secondary.length,
    screenshot_count: visual.screenshot_count,
    network_scope: "ephemeral_local_loopback_only", external_network_performed: false,
    financial_data_loaded: false, database_changed: false, finder_used: false,
    diagnostics: {
      console_errors: diagnostics.consoleErrors, page_errors: diagnostics.pageErrors,
      http_errors: diagnostics.httpErrors, blocked_external: diagnostics.blockedExternal,
      requested_origins: [...diagnostics.requestedOrigins],
    },
  };
  await Promise.all([
    writeJson("wcag_audit.json", wcag), writeJson("keyboard_flow.json", keyboard),
    writeJson("accessibility_tree.json", axTree), writeJson("error_prevention_audit.json", errorPrevention),
    writeJson("visual_regression.json", visual), writeJson("browser_validation.json", browserValidation),
  ]);
} finally {
  await browser.close();
  await new Promise((resolve) => server.close(resolve));
}

const sanitizer = path.join(webRoot, "tests", "v025", "stage8_phase81_trace_privacy.py");
const pythonExecutable = process.env.PFI_PYTHON ? path.resolve(process.env.PFI_PYTHON) : "python3";
const sanitized = spawnSync(pythonExecutable, ["-B", sanitizer, rawTracePath, tracePath], {
  cwd: path.dirname(webRoot), encoding: "utf8",
});
if (sanitized.status !== 0) throw new Error(`trace sanitization failed: ${sanitized.error?.message || sanitized.stderr || sanitized.stdout || "unknown subprocess failure"}`);
await unlink(rawTracePath).catch(() => {});
const traceSha256 = createHash("sha256").update(await readFile(tracePath)).digest("hex");
browserValidation.trace_sha256 = traceSha256;
await writeJson("browser_validation.json", browserValidation);
console.log(JSON.stringify({ status: browserValidation.status, checks: browserValidation.checks, trace_sha256: traceSha256 }, null, 2));
if (browserValidation.status !== "pass") process.exitCode = 1;
