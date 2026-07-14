#!/usr/bin/env node
"use strict";

const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");

const outputDir = getArg("--output-dir") || fs.mkdtempSync(path.join(os.tmpdir(), "cross-board-shared-state-browser-"));
const targetUrl = getArg("--url") || "http://127.0.0.1:5173/";
const browserExecutable = process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH || findChromiumExecutable();
const checks = [];

const runtimeVersion = "cross_board_shared_state.v1_1_7_stage9_phase1";
const inspectorLayerVersion = "inspector_explanation_layer.v1_1_7_stage9_phase1";
const expectedSurfaces = ["home", "galaxy", "notion", "roi", "obsidian", "timeline", "contribution", "wordcloud", "search", "summary"];

function pass(name, evidence, details) {
  checks.push({ name, status: "PASS", evidence, ...(details ? { details } : {}) });
}

function assertCondition(condition, name, evidence, failure, details = {}) {
  if (condition) {
    pass(name, evidence, details);
    return;
  }
  const error = new Error(failure);
  error.details = details;
  throw error;
}

function getArg(name) {
  const index = process.argv.indexOf(name);
  if (index === -1) return null;
  return process.argv[index + 1] || null;
}

function findChromiumExecutable() {
  const candidates = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
  ];
  return candidates.find((candidate) => fs.existsSync(candidate));
}

function requirePlaywright() {
  try {
    return require("playwright");
  } catch {}
  const pnpmRoot = path.join(os.homedir(), ".cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/.pnpm");
  try {
    const candidate = fs.readdirSync(pnpmRoot).filter((entry) => entry.startsWith("playwright@")).sort().at(-1);
    if (candidate) return require(path.join(pnpmRoot, candidate, "node_modules/playwright"));
  } catch {}
  throw new Error("Playwright is not resolvable from project dependencies or Codex bundled runtime");
}

async function openApp(page) {
  await page.goto(targetUrl, { waitUntil: "networkidle", timeout: 30_000 });
  await page.waitForSelector(`[data-stage9-phase1-shared-state="${runtimeVersion}"]`, { timeout: 30_000 });
}

async function stage9Snapshot(page) {
  return page.evaluate(() => {
    const root = document.querySelector("[data-stage9-phase1-shared-state]");
    const lens = document.querySelector(".interaction-lens[data-stage9-phase1-shared-state]");
    const inspector = document.querySelector("[data-stage9-inspector-explanation]");
    const debug = window.__memoryAtlasStage9Phase1?.() ?? null;
    return {
      rootRuntime: root?.getAttribute("data-stage9-phase1-shared-state") || null,
      rootInspector: root?.getAttribute("data-stage9-inspector-explanation") || null,
      rootTokens: root?.getAttribute("data-stage9-synchronized-filters") || "",
      rootSurfaceCount: Number(root?.getAttribute("data-stage9-surface-count") || 0),
      lensRuntime: lens?.getAttribute("data-stage9-phase1-shared-state") || null,
      lensTokens: lens?.getAttribute("data-stage9-synchronized-filters") || "",
      inspectorVersion: inspector?.getAttribute("data-stage9-inspector-explanation") || null,
      debug,
    };
  });
}

async function clickView(page, view) {
  await page.locator(`[data-nav-view="${view}"]`).click({ timeout: 10_000 });
  await page.waitForFunction((expectedView) => window.__memoryAtlasStage9Phase1?.().activeView === expectedView, view, {
    timeout: 20_000,
  });
}

async function main() {
  fs.mkdirSync(outputDir, { recursive: true });
  const { chromium } = requirePlaywright();
  const browser = await chromium.launch({
    executablePath: browserExecutable,
    headless: true,
    args: ["--disable-dev-shm-usage"],
  });
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 }, deviceScaleFactor: 1 });
  const page = await context.newPage();
  const consoleMessages = [];
  const failedResponses = [];
  page.on("console", (message) => {
    if (message.type() === "error") consoleMessages.push(message.text());
  });
  page.on("response", (response) => {
    if (response.status() >= 400) failedResponses.push({ status: response.status(), url: response.url() });
  });
  await page.route("**/__memory_atlas_runtime_state", (route) => route.fulfill({ status: 204, body: "" }));
  await page.route("**/__memory_atlas_heartbeat", (route) => route.fulfill({ status: 204, body: "" }));
  await page.route("**/__memory_atlas_release", (route) => route.fulfill({ status: 204, body: "" }));

  try {
    await openApp(page);
    const initial = await stage9Snapshot(page);
    const initialDebug = initial.debug;
    assertCondition(
      initial.rootRuntime === runtimeVersion &&
        initial.rootInspector === inspectorLayerVersion &&
        initial.lensRuntime === runtimeVersion &&
        initial.rootTokens.includes("shared_state_filters") &&
        initial.rootTokens.includes("synchronized_filters") &&
        initial.rootTokens.includes("inspector_explanation_layer") &&
        initial.lensTokens.includes("shared_state_filters") &&
        initial.lensTokens.includes("synchronized_filters"),
      "stage9_phase1_browser_root_markers",
      "Root shell and interaction lens expose Stage 9.1 shared-state and synchronized filter markers",
      "Root shell or interaction lens Stage 9.1 markers are incomplete",
      initial,
    );

    assertCondition(
      initialDebug?.runtimeVersion === runtimeVersion &&
        initialDebug?.inspectorLayerVersion === inspectorLayerVersion &&
        initialDebug?.shared_state_filters === true &&
        initialDebug?.synchronized_filters === true &&
        initialDebug?.surfaceCount === expectedSurfaces.length &&
        expectedSurfaces.every((surface) => initialDebug?.surfaces?.includes(surface)) &&
        initialDebug?.selectedNodeId &&
        initialDebug?.inspector_explanation_layer?.mounted === true &&
        initialDebug?.inspector_explanation_layer?.formulaCount >= 3 &&
        initialDebug?.inspector_explanation_layer?.evidenceCount >= 5 &&
        initialDebug?.safety?.rawPrivateDataIncluded === false &&
        initialDebug?.safety?.directActiveMemoryWriteback === false &&
        initialDebug?.safety?.proposalWrite === false,
      "stage9_phase1_browser_debug_signal",
      "Stage 9.1 debug signal exposes shared-state surfaces, Inspector explanation coverage and no-write safety",
      "Stage 9.1 debug signal is incomplete",
      initialDebug,
    );

    const searchInput = page.locator(".search-box input");
    await searchInput.fill("project");
    await page.waitForFunction(() => window.__memoryAtlasStage9Phase1?.().synchronizedFilters.query === "project", null, {
      timeout: 20_000,
    });
    await clickView(page, "timeline");
    const timelineDebug = await page.evaluate(() => window.__memoryAtlasStage9Phase1?.() ?? null);
    await clickView(page, "summary");
    const summaryDebug = await page.evaluate(() => window.__memoryAtlasStage9Phase1?.() ?? null);
    assertCondition(
      timelineDebug?.activeView === "timeline" &&
        summaryDebug?.activeView === "summary" &&
        timelineDebug?.synchronizedFilters?.query === "project" &&
        summaryDebug?.synchronizedFilters?.query === "project" &&
        timelineDebug?.focus?.inspector?.nodeId === summaryDebug?.focus?.inspector?.nodeId,
      "stage9_phase1_browser_cross_board_filter_sync",
      "Search filter and Inspector focus persist across Timeline and Summary board switches",
      "Cross-board synchronized filters or Inspector focus did not persist across board switches",
      { timelineDebug, summaryDebug },
    );

    const screenshotPath = path.join(outputDir, "cross-board-shared-state-stage9-phase1.png");
    await page.screenshot({ path: screenshotPath, fullPage: false });
    const screenshotBytes = fs.statSync(screenshotPath).size;
    assertCondition(
      screenshotBytes > 20_000,
      `stage9_phase1_browser_screenshot`,
      `Browser cross-board shared-state screenshot captured ${screenshotBytes} bytes`,
      "Browser cross-board shared-state screenshot is unexpectedly small",
      { screenshotPath, screenshotBytes },
    );

    const actionableFailedResponses = failedResponses.filter((response) => {
      try {
        const pathname = new URL(response.url).pathname;
        return !["/__memory_atlas_runtime_state", "/__memory_atlas_heartbeat", "/__memory_atlas_release"].includes(pathname);
      } catch {
        return true;
      }
    });
    const actionableConsoleErrors = consoleMessages.filter((message) => {
      return !(message.startsWith("Failed to load resource:") && actionableFailedResponses.length === 0);
    });
    assertCondition(
      actionableConsoleErrors.length === 0 && actionableFailedResponses.length === 0,
      "stage9_phase1_browser_console",
      "Browser cross-board shared-state test completed without actionable console errors or failed responses",
      "Browser cross-board shared-state test produced actionable console errors or failed responses",
      { consoleMessages, failedResponses, actionableConsoleErrors, actionableFailedResponses },
    );
  } finally {
    await browser.close();
  }

  console.log(JSON.stringify({
    status: "PASS",
    validator: "validate_cross_board_shared_state_browser",
    runtime_version: runtimeVersion,
    inspector_layer_version: inspectorLayerVersion,
    output_dir: outputDir,
    checks,
  }, null, 2));
}

main().catch((error) => {
  console.error(JSON.stringify({
    status: "FAIL",
    validator: "validate_cross_board_shared_state_browser",
    runtime_version: runtimeVersion,
    inspector_layer_version: inspectorLayerVersion,
    error: error.message,
    details: error.details || null,
    checks,
  }, null, 2));
  process.exit(1);
});
