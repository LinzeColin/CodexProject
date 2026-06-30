#!/usr/bin/env node
"use strict";

const crypto = require("node:crypto");
const fs = require("node:fs");
const http = require("node:http");
const path = require("node:path");
const { URL } = require("node:url");

let playwright;
try {
  playwright = require("playwright");
} catch (error) {
  if (!process.env.PLAYWRIGHT_PACKAGE_PATH) throw error;
  playwright = require(process.env.PLAYWRIGHT_PACKAGE_PATH);
}

const { chromium } = playwright;

const CONTRACT = "PFI-V024-STAGE3-PHASE33-BROWSER-NAVIGATION";
const ROOT = path.resolve(__dirname, "..");
const WEB_ROOT = path.join(ROOT, "web");
const EVIDENCE_DIR = path.join(ROOT, "reports", "pfi_v024", "stage_3", "phase_3_3");
const SCREENSHOT_DIR = path.join(EVIDENCE_DIR, "screenshots");

const OFFICIAL_PRIMARY_LABELS = Object.freeze([
  "首页总览",
  "账户与资产",
  "账本流水",
  "投资管理",
  "消费管理",
  "数据源与上传",
  "建议与复盘",
  "报告与洞察",
  "市场与研究",
  "设置",
]);

const DEPRECATED_PRIMARY_LABELS = Object.freeze(["首页", "市场", "研究", "持仓", "策略实验室", "数据与系统"]);
const LEGACY_ALIAS_CASES = Object.freeze([
  Object.freeze(["/home/today", "/home", "home"]),
  Object.freeze(["/market/watch", "/market-research?tab=market", "market_research"]),
  Object.freeze(["/market/research", "/market-research?tab=research", "market_research"]),
  Object.freeze(["/investment/holdings", "/investment?tab=holdings", "investment"]),
  Object.freeze(["/market/lab", "/market-research/strategy-lab", "market_research"]),
  Object.freeze(["/settings/data", "/settings?tab=data-system", "settings"]),
]);

function ensureDirs() {
  fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
}

function mimeType(filePath) {
  const ext = path.extname(filePath).toLowerCase();
  return {
    ".html": "text/html; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".png": "image/png",
    ".svg": "image/svg+xml",
  }[ext] || "application/octet-stream";
}

function startStaticServer() {
  const server = http.createServer((request, response) => {
    try {
      const requestUrl = new URL(request.url || "/", "http://127.0.0.1");
      const requestedPath = decodeURIComponent(requestUrl.pathname === "/" ? "/index.html" : requestUrl.pathname);
      const resolved = path.resolve(WEB_ROOT, `.${requestedPath}`);
      if (!resolved.startsWith(WEB_ROOT)) {
        response.writeHead(403);
        response.end("Forbidden");
        return;
      }
      const stat = fs.existsSync(resolved) ? fs.statSync(resolved) : null;
      const filePath = stat?.isDirectory() ? path.join(resolved, "index.html") : resolved;
      if (!fs.existsSync(filePath)) {
        response.writeHead(404);
        response.end("Not found");
        return;
      }
      response.writeHead(200, { "Content-Type": mimeType(filePath) });
      fs.createReadStream(filePath).pipe(response);
    } catch (error) {
      response.writeHead(500);
      response.end(String(error && error.message ? error.message : error));
    }
  });
  return new Promise((resolve, reject) => {
    server.on("error", reject);
    server.listen(0, "127.0.0.1", () => {
      const address = server.address();
      resolve({ server, baseUrl: `http://127.0.0.1:${address.port}` });
    });
  });
}

async function waitForReady(page) {
  await page.waitForLoadState("networkidle");
  await page.waitForFunction(() => {
    return document.querySelector(".app-shell")?.dataset.state === "ready" && Boolean(window.PFI_V024_STAGE3_ROUTES);
  });
}

async function activeWorkspace(page) {
  return page.locator("#main-workspace").evaluate((node) => node.dataset.activeWorkspace || "");
}

async function activeRoute(page) {
  return page.locator("#main-workspace").evaluate((node) => node.dataset.routeAlias || "");
}

async function clickPrimaryRoute(page, routeAlias, expectedWorkspace) {
  await page.locator(`[data-primary-entry="true"][data-route-alias="${routeAlias}"]`).click();
  await page.waitForFunction((workspace) => {
    return document.querySelector("#main-workspace")?.dataset.activeWorkspace === workspace;
  }, expectedWorkspace);
  const actualWorkspace = await activeWorkspace(page);
  const actualRoute = await activeRoute(page);
  if (actualWorkspace !== expectedWorkspace) {
    throw new Error(`route ${routeAlias} active workspace ${actualWorkspace}, expected ${expectedWorkspace}`);
  }
  if (actualRoute !== routeAlias) {
    throw new Error(`route ${routeAlias} active route ${actualRoute}, expected ${routeAlias}`);
  }
}

async function evaluateLegacyRoutes(page) {
  return page.evaluate((cases) => {
    return Object.fromEntries(cases.map(([inputRoute]) => [
      inputRoute,
      window.PFI_V024_STAGE3_ROUTES.resolveRouteAlias(inputRoute),
    ]));
  }, LEGACY_ALIAS_CASES);
}

async function validateDirectAliases(page, baseUrl) {
  const results = {};
  for (const [inputRoute, resolvedRoute, expectedWorkspace] of LEGACY_ALIAS_CASES) {
    await page.goto(`${baseUrl}/index.html#${inputRoute}`, { waitUntil: "networkidle" });
    await waitForReady(page);
    await page.waitForFunction((workspace) => {
      return document.querySelector("#main-workspace")?.dataset.activeWorkspace === workspace;
    }, expectedWorkspace);
    const workspace = await activeWorkspace(page);
    const route = await activeRoute(page);
    const hash = await page.evaluate(() => window.location.hash);
    results[inputRoute] = { inputRoute, resolvedRoute, expectedWorkspace, workspace, route, hash };
    if (workspace !== expectedWorkspace || route !== resolvedRoute || decodeURIComponent(hash) !== `#${resolvedRoute}`) {
      throw new Error(`direct alias ${inputRoute} resolved to workspace=${workspace}, route=${route}, hash=${hash}`);
    }
  }
  return results;
}

async function main() {
  ensureDirs();
  const started = await startStaticServer();
  const { server, baseUrl } = started;
  const consoleErrors = [];
  const pageErrors = [];
  let browser;
  try {
    browser = await chromium.launch({ headless: true });
    const page = await browser.newPage({ viewport: { width: 1440, height: 960 } });
    page.on("console", (message) => {
      if (message.type() === "error") consoleErrors.push(message.text());
    });
    page.on("pageerror", (error) => pageErrors.push(error.message));

    await page.goto(`${baseUrl}/index.html`, { waitUntil: "networkidle" });
    await waitForReady(page);

    const desktopPrimaryLabels = await page.$$eval('[data-primary-entry="true"]', (nodes) => (
      nodes.map((node) => node.textContent.trim())
    ));
    const mobilePrimaryLabels = await page.$$eval('[data-mobile-primary-entry="true"]', (nodes) => (
      nodes.map((node) => node.textContent.trim())
    ));
    const desktopPrimaryCount = desktopPrimaryLabels.length;
    const mobilePrimaryCount = mobilePrimaryLabels.length;
    const marketResearchIndex = await page.locator('[data-primary-entry="true"][data-workspace="market_research"]').evaluate((node) => Number(node.dataset.navIndex || 0));
    const legacyLabelsAbsentAsPrimaryExact = DEPRECATED_PRIMARY_LABELS.every((label) => !desktopPrimaryLabels.includes(label));

    if (desktopPrimaryCount !== 10) throw new Error(`desktop primary count ${desktopPrimaryCount}`);
    if (mobilePrimaryCount !== 10) throw new Error(`mobile primary count ${mobilePrimaryCount}`);
    if (JSON.stringify(desktopPrimaryLabels) !== JSON.stringify(OFFICIAL_PRIMARY_LABELS)) {
      throw new Error(`desktop labels ${JSON.stringify(desktopPrimaryLabels)}`);
    }
    if (marketResearchIndex !== 9) throw new Error(`market_research index ${marketResearchIndex}`);
    if (!legacyLabelsAbsentAsPrimaryExact) throw new Error("deprecated legacy labels are still exact primary entries");

    const desktopNavPath = path.join(SCREENSHOT_DIR, "desktop_nav.png");
    await page.screenshot({ path: desktopNavPath, fullPage: true });

    const legacyCases = await evaluateLegacyRoutes(page);
    for (const [inputRoute, resolvedRoute, workspace] of LEGACY_ALIAS_CASES) {
      const actual = legacyCases[inputRoute];
      if (actual.status !== "resolved" || actual.routeType !== "legacy_redirect" || actual.routeAlias !== resolvedRoute || actual.workspace !== workspace) {
        throw new Error(`legacy route ${inputRoute} resolved as ${JSON.stringify(actual)}`);
      }
    }

    await clickPrimaryRoute(page, "/accounts", "accounts");
    await clickPrimaryRoute(page, "/market-research", "market_research");
    await clickPrimaryRoute(page, "/settings", "settings");

    await page.goBack();
    await page.waitForFunction(() => document.querySelector("#main-workspace")?.dataset.activeWorkspace === "market_research");
    const afterBackWorkspace = await activeWorkspace(page);
    const afterBackRoute = await activeRoute(page);
    if (afterBackWorkspace !== "market_research" || afterBackRoute !== "/market-research") {
      throw new Error(`back navigation workspace=${afterBackWorkspace} route=${afterBackRoute}`);
    }

    await page.goForward();
    await page.waitForFunction(() => document.querySelector("#main-workspace")?.dataset.activeWorkspace === "settings");
    const afterForwardWorkspace = await activeWorkspace(page);
    const afterForwardRoute = await activeRoute(page);
    if (afterForwardWorkspace !== "settings" || afterForwardRoute !== "/settings") {
      throw new Error(`forward navigation workspace=${afterForwardWorkspace} route=${afterForwardRoute}`);
    }

    const browserBackPath = path.join(SCREENSHOT_DIR, "browser_back_after_forward.png");
    await page.screenshot({ path: browserBackPath, fullPage: true });

    const directAliases = await validateDirectAliases(page, baseUrl);

    const browserValidation = {
      contract: CONTRACT,
      status: "pass",
      source: `${baseUrl}/index.html`,
      desktop_primary_count: desktopPrimaryCount,
      mobile_primary_count: mobilePrimaryCount,
      desktop_primary_labels: desktopPrimaryLabels,
      mobile_primary_labels: mobilePrimaryLabels,
      market_research_index: marketResearchIndex,
      legacy_labels_absent_as_primary_exact: legacyLabelsAbsentAsPrimaryExact,
      click_navigation_passed: true,
      back_forward_passed: true,
      direct_url_alias_passed: true,
      direct_aliases: directAliases,
      final_workspace_after_forward: afterForwardWorkspace,
      final_route_after_forward: afterForwardRoute,
      console_errors: consoleErrors,
      page_errors: pageErrors,
      screenshots: {
        desktop_nav: path.relative(EVIDENCE_DIR, desktopNavPath),
        browser_back_after_forward: path.relative(EVIDENCE_DIR, browserBackPath),
      },
      generated_at: new Date().toISOString(),
      validation_hash: crypto.createHash("sha256").update(JSON.stringify({
        desktopPrimaryLabels,
        mobilePrimaryLabels,
        legacyCases,
        directAliases,
      })).digest("hex"),
    };
    const legacyValidation = {
      contract: CONTRACT,
      status: "pass",
      cases: legacyCases,
      generated_at: browserValidation.generated_at,
    };

    fs.writeFileSync(path.join(EVIDENCE_DIR, "browser_validation.json"), `${JSON.stringify(browserValidation, null, 2)}\n`);
    fs.writeFileSync(path.join(EVIDENCE_DIR, "legacy_routes_validation.json"), `${JSON.stringify(legacyValidation, null, 2)}\n`);

    if (consoleErrors.length || pageErrors.length) {
      throw new Error(`browser errors console=${consoleErrors.length} page=${pageErrors.length}`);
    }
    console.log(JSON.stringify({
      status: "pass",
      contract: CONTRACT,
      desktop_primary_count: desktopPrimaryCount,
      mobile_primary_count: mobilePrimaryCount,
      legacy_alias_count: Object.keys(legacyCases).length,
      screenshots: browserValidation.screenshots,
    }, null, 2));
  } finally {
    if (browser) await browser.close();
    await new Promise((resolve) => server.close(resolve));
  }
}

main().catch((error) => {
  console.error(error && error.stack ? error.stack : String(error));
  process.exit(1);
});
