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

const ROOT = path.resolve(__dirname, "..");
const WEB_ROOT = path.join(ROOT, "web");
const REVIEW_DIR = path.join(ROOT, "reports", "pfi_v024", "stage_5", "whole_stage_review");
const SCREENSHOT_DIR = path.join(REVIEW_DIR, "screenshots");
const PLAYWRIGHT_PACKAGE_PATH = process.env.PLAYWRIGHT_PACKAGE_PATH || "";
const MECHANICAL_TERMS = Object.freeze(["功能面板", "PFI 功能入口", "功能已准备", "进入操作面板"]);
const serverNotFoundPaths = [];

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
      if (requestUrl.pathname === "/favicon.ico") {
        response.writeHead(204);
        response.end();
        return;
      }
      const requestPath = decodeURIComponent(requestUrl.pathname === "/" ? "/index.html" : requestUrl.pathname);
      const resolved = path.resolve(WEB_ROOT, `.${requestPath}`);
      if (!resolved.startsWith(WEB_ROOT)) {
        response.writeHead(403);
        response.end("Forbidden");
        return;
      }
      const stat = fs.existsSync(resolved) ? fs.statSync(resolved) : null;
      const filePath = stat?.isDirectory() ? path.join(resolved, "index.html") : resolved;
      if (!fs.existsSync(filePath)) {
        serverNotFoundPaths.push(requestPath);
        response.writeHead(404);
        response.end("Not found");
        return;
      }
      response.writeHead(200, { "Content-Type": mimeType(filePath) });
      fs.createReadStream(filePath).pipe(response);
    } catch (error) {
      response.writeHead(500);
      response.end(String(error?.message || error));
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
    const shellReady = document.querySelector(".app-shell")?.dataset.state === "ready";
    return shellReady && Boolean(window.PFI_V024_STAGE5_PAGES) && Boolean(window.PFI_V024_STAGE5_UX_STATE);
  });
}

async function navigateRoute(page, baseUrl, routeAlias, workspace) {
  await page.goto(`${baseUrl}/index.html#${encodeURIComponent(routeAlias)}`, { waitUntil: "networkidle" });
  await waitForReady(page);
  await page.waitForFunction((expectedWorkspace) => {
    return document.querySelector("#main-workspace")?.dataset.activeWorkspace === expectedWorkspace
      && document.querySelector("[data-stage4-subpage-surface]")?.hidden === false;
  }, workspace);
  await page.waitForFunction(() => document.querySelectorAll("[data-stage5-state]").length >= 4);
}

async function activeRoute(page) {
  return page.locator("#main-workspace").evaluate((node) => node.dataset.routeAlias || "");
}

async function capture(page, file, kind, workspace, routeAlias, screenshots) {
  const filePath = path.join(SCREENSHOT_DIR, file);
  await page.screenshot({ path: filePath, fullPage: true });
  screenshots.push({
    kind,
    workspace,
    routeAlias,
    file,
    bytes: fs.statSync(filePath).size,
  });
}

async function main() {
  ensureDirs();
  const { server, baseUrl } = await startStaticServer();
  const consoleErrors = [];
  const pageErrors = [];
  const httpErrors = [];
  const screenshots = [];
  let browser;
  try {
    browser = await chromium.launch({ headless: true });
    const page = await browser.newPage({ viewport: { width: 1440, height: 960 } });
    page.on("console", (message) => {
      if (message.type() === "error") consoleErrors.push(message.text());
    });
    page.on("pageerror", (error) => pageErrors.push(error.message));
    page.on("response", (response) => {
      if (response.status() >= 400) {
        httpErrors.push({ url: response.url(), status: response.status() });
      }
    });

    await page.goto(`${baseUrl}/index.html`, { waitUntil: "networkidle" });
    await waitForReady(page);

    const catalog = await page.evaluate(() => window.PFI_V024_STAGE5_PAGES.buildV024Stage5Phase52Catalog());
    const primaryWorkspaces = Object.keys(catalog);
    const primaryLabels = await page.$$eval('[data-primary-entry="true"]', (nodes) => nodes.map((node) => node.textContent.trim()));
    if (primaryWorkspaces.length !== 10) throw new Error(`primary workspace count ${primaryWorkspaces.length}`);
    if (primaryLabels.length !== 10) throw new Error(`primary entry count ${primaryLabels.length}`);

    for (const [index, workspace] of primaryWorkspaces.entries()) {
      const pages = catalog[workspace] || [];
      if (pages.length < 3) throw new Error(`${workspace} has ${pages.length} pages`);
      const primaryPage = pages[0];
      await navigateRoute(page, baseUrl, primaryPage.routeAlias, workspace);
      const route = await activeRoute(page);
      if (route !== primaryPage.routeAlias) throw new Error(`${workspace} active route ${route}, expected ${primaryPage.routeAlias}`);
      await capture(page, `primary_${String(index + 1).padStart(2, "0")}_${workspace}.png`, "primary", workspace, primaryPage.routeAlias, screenshots);

      const corePage = pages[1];
      await navigateRoute(page, baseUrl, corePage.routeAlias, workspace);
      const coreRoute = await activeRoute(page);
      if (coreRoute !== corePage.routeAlias) throw new Error(`${workspace} active route ${coreRoute}, expected ${corePage.routeAlias}`);
      await capture(page, `core_secondary_${String(index + 1).padStart(2, "0")}_${workspace}.png`, "core_secondary", workspace, corePage.routeAlias, screenshots);
    }

    const visibleStateKinds = await page.$$eval("[data-stage5-state]", (nodes) => [...new Set(nodes.map((node) => node.getAttribute("data-stage5-state")))].sort());
    const stage5UxStateVisible = ["empty", "error", "loading", "success"].every((kind) => visibleStateKinds.includes(kind));
    const stateActionTargets = await page.$$eval("[data-stage5-state-action]", (nodes) => nodes.map((node) => ({
      state: node.getAttribute("data-stage5-state-action"),
      routeAlias: node.getAttribute("data-route-alias") || node.dataset.routeAlias || "",
      workspace: node.getAttribute("data-feature-workspace") || node.dataset.featureWorkspace || "",
    })));
    const clickActionsRouteNotToastOnly = stateActionTargets.length >= 4
      && stateActionTargets.every((item) => item.routeAlias.startsWith("/") && Boolean(item.workspace));

    await navigateRoute(page, baseUrl, catalog.accounts[0].routeAlias, "accounts");
    await navigateRoute(page, baseUrl, catalog.investment[0].routeAlias, "investment");
    await page.goBack();
    await page.waitForFunction(() => document.querySelector("#main-workspace")?.dataset.activeWorkspace === "accounts");
    const backRoute = await activeRoute(page);
    await page.goForward();
    await page.waitForFunction(() => document.querySelector("#main-workspace")?.dataset.activeWorkspace === "investment");
    const forwardRoute = await activeRoute(page);
    const historyBackForwardPassed = backRoute === catalog.accounts[0].routeAlias && forwardRoute === catalog.investment[0].routeAlias;

    const visibleText = await page.locator("body").innerText();
    const mechanicalTermsVisible = MECHANICAL_TERMS.filter((term) => visibleText.includes(term));

    const browserValidation = {
      schema: "PFIV024Stage5WholeReviewBrowserValidationV1",
      target_version: "v0.2.4",
      source_package_version: "v0.2.3-repair",
      stage: "Stage 5",
      review_id: "stage_5_whole_review",
      status: consoleErrors.length || pageErrors.length || mechanicalTermsVisible.length || !stage5UxStateVisible || !clickActionsRouteNotToastOnly || !historyBackForwardPassed ? "fail" : "pass",
      source: `${baseUrl}/index.html`,
      playwright_package_path: PLAYWRIGHT_PACKAGE_PATH,
      primary_entry_count: primaryLabels.length,
      primary_workspaces: primaryWorkspaces,
      primary_labels: primaryLabels,
      primary_screenshot_count: screenshots.filter((item) => item.kind === "primary").length,
      core_secondary_screenshot_count: screenshots.filter((item) => item.kind === "core_secondary").length,
      stage5_ux_state_visible: stage5UxStateVisible,
      visible_state_kinds: visibleStateKinds,
      click_actions_route_not_toast_only: clickActionsRouteNotToastOnly,
      state_action_targets: stateActionTargets,
      history_back_forward_passed: historyBackForwardPassed,
      mechanical_terms_visible: mechanicalTermsVisible,
      server_not_found_paths: serverNotFoundPaths,
      http_errors: httpErrors,
      console_errors: consoleErrors,
      page_errors: pageErrors,
      screenshots,
      generated_at: new Date().toISOString(),
      validation_hash: crypto.createHash("sha256").update(JSON.stringify({
        primaryLabels,
        primaryWorkspaces,
        screenshots: screenshots.map((item) => [item.kind, item.workspace, item.routeAlias, item.bytes]),
        visibleStateKinds,
        stateActionTargets,
      })).digest("hex"),
    };
    fs.writeFileSync(path.join(REVIEW_DIR, "browser_validation.json"), `${JSON.stringify(browserValidation, null, 2)}\n`);
    console.log(JSON.stringify({ status: browserValidation.status, screenshots: screenshots.length, review_dir: REVIEW_DIR }, null, 2));
    if (browserValidation.status !== "pass") process.exitCode = 1;
  } finally {
    if (browser) await browser.close();
    server.close();
  }
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
