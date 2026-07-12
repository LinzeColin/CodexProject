#!/usr/bin/env node
"use strict";

const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");

const outputDir = getArg("--output-dir") || fs.mkdtempSync(path.join(os.tmpdir(), "memory-river-integration-browser-"));
const targetUrl = getArg("--url") || "http://127.0.0.1:5173/";
const browserExecutable = process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH || findChromiumExecutable();
const checks = [];

const integrationVersion = "memory_river_integration.v1_1_7_stage5_phase3";

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

async function openTimeline(page, url = targetUrl) {
  await page.goto(url, { waitUntil: "networkidle", timeout: 30_000 });
  await page.locator('[data-nav-view="timeline"]').click({ timeout: 10_000 });
  await page.waitForSelector(".timeline-map", { timeout: 30_000 });
}

async function readStage5Phase3(page) {
  return page.evaluate(() => window.__memoryAtlasStage5Phase3?.() ?? null);
}

async function main() {
  fs.mkdirSync(outputDir, { recursive: true });
  const { chromium } = requirePlaywright();
  const browser = await chromium.launch({
    executablePath: browserExecutable,
    headless: true,
    args: ["--disable-dev-shm-usage"],
  });
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 }, deviceScaleFactor: 1 });
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
    await openTimeline(page);
    await page.evaluate(() => window.localStorage.removeItem("memory-atlas.timeline-renderer"));
    await openTimeline(page);
    await page.waitForSelector('.timeline-map[data-timeline-renderer="memory-river"]', { timeout: 20_000 });
    await page.waitForSelector('.memory-river-canvas[data-stage5-phase3-memory-river="memory_river_integration.v1_1_7_stage5_phase3"]', { timeout: 20_000 });
    await page.waitForFunction(() => window.__memoryAtlasStage5Phase3?.()?.rendererMode === "memory-river", null, {
      timeout: 20_000,
    });
    const defaultIntegration = await readStage5Phase3(page);
    assertCondition(
      defaultIntegration?.integrationVersion === integrationVersion &&
        defaultIntegration?.rendererMode === "memory-river" &&
        defaultIntegration?.defaultRendererMode === "memory-river" &&
        defaultIntegration?.legacyRollbackEnabled === true,
      "stage5_phase3_browser_default_memory_river",
      "Production Timeline defaults to Memory River with Stage 5.3 integration metadata and rollback enabled",
      "Production Timeline did not default to the Stage 5.3 Memory River integration",
      defaultIntegration,
    );

    assertCondition(
      ["Macro", "Meso", "Micro"].every((level) => Number(defaultIntegration?.levelCounts?.[level] || 0) > 0) &&
        ["black-hole-lifecycle", "proto-star-lifecycle", "stale-deprecated", "roi-gradient"].every((layer) =>
          defaultIntegration?.evidenceLayers?.includes(layer),
        ),
      "stage5_phase3_browser_river_layers",
      "Memory River exposes Macro/Meso/Micro lanes and Black Hole, Proto-Star, stale/deprecated and ROI evidence layers",
      "Memory River layer metadata is incomplete",
      defaultIntegration,
    );

    await page.getByRole("button", { name: /^Legacy$/ }).click({ timeout: 10_000 });
    await page.waitForSelector('.timeline-map[data-timeline-renderer="legacy"]', { timeout: 10_000 });
    const legacySwitch = await page.evaluate(() => ({
      signal: window.__memoryAtlasStage5Phase3?.() ?? null,
      hasMemoryRiver: Boolean(document.querySelector(".memory-river-canvas")),
      hasLegacyCanvas: Boolean(document.querySelector(".timeline-canvas")),
      stored: window.localStorage.getItem("memory-atlas.timeline-renderer"),
    }));
    assertCondition(
      legacySwitch.signal?.rendererMode === "legacy" &&
        legacySwitch.hasMemoryRiver === false &&
        legacySwitch.hasLegacyCanvas === true &&
        legacySwitch.stored === "legacy",
      "stage5_phase3_browser_legacy_toggle",
      "In-app Legacy toggle rolls back to the old Timeline renderer and persists the rollback flag",
      "Legacy renderer toggle did not roll back or persist correctly",
      legacySwitch,
    );

    await page.getByRole("button", { name: /^Memory River$/ }).click({ timeout: 10_000 });
    await page.waitForSelector('.timeline-map[data-timeline-renderer="memory-river"]', { timeout: 10_000 });
    const restoredSwitch = await page.evaluate(() => ({
      signal: window.__memoryAtlasStage5Phase3?.() ?? null,
      hasMemoryRiver: Boolean(document.querySelector(".memory-river-canvas")),
      stored: window.localStorage.getItem("memory-atlas.timeline-renderer"),
    }));
    assertCondition(
      restoredSwitch.signal?.rendererMode === "memory-river" &&
        restoredSwitch.hasMemoryRiver === true &&
        restoredSwitch.stored === "memory-river",
      "stage5_phase3_browser_memory_river_toggle",
      "In-app Memory River toggle restores the new Timeline renderer and persists it",
      "Memory River toggle did not restore or persist correctly",
      restoredSwitch,
    );

    await page.evaluate(() => window.localStorage.removeItem("memory-atlas.timeline-renderer"));
    await openTimeline(page, `${targetUrl}?timelineRenderer=legacy`);
    await page.waitForSelector('.timeline-map[data-timeline-renderer="legacy"]', { timeout: 10_000 });
    const urlRollback = await page.evaluate(() => ({
      signal: window.__memoryAtlasStage5Phase3?.() ?? null,
      hasMemoryRiver: Boolean(document.querySelector(".memory-river-canvas")),
      hasLegacyCanvas: Boolean(document.querySelector(".timeline-canvas")),
    }));
    assertCondition(
      urlRollback.signal?.rendererMode === "legacy" && !urlRollback.hasMemoryRiver && urlRollback.hasLegacyCanvas,
      "stage5_phase3_browser_url_rollback",
      "URL flag timelineRenderer=legacy rolls back to the old Timeline renderer",
      "URL rollback did not activate legacy Timeline",
      urlRollback,
    );

    await page.evaluate(() => window.localStorage.removeItem("memory-atlas.timeline-renderer"));
    await openTimeline(page, `${targetUrl}?timelineRenderer=memory-river`);
    await page.waitForSelector('.memory-river-canvas[data-interaction-mode="pan"]', { timeout: 10_000 });
    await page.getByRole("button", { name: /^Brush$/ }).click({ timeout: 10_000 });
    await page.waitForSelector('.memory-river-canvas[data-interaction-mode="brush"]', { timeout: 10_000 });
    const box = await page.locator(".memory-river-canvas").boundingBox();
    assertCondition(Boolean(box), "stage5_phase3_browser_canvas_box", "Memory River canvas has a measurable browser layout box", "Memory River canvas has no browser layout box");
    await page.mouse.move(box.x + box.width * 0.35, box.y + box.height * 0.55);
    await page.mouse.down();
    await page.mouse.move(box.x + box.width * 0.68, box.y + box.height * 0.55, { steps: 8 });
    await page.mouse.up();
    await page.waitForSelector('.memory-river-selected-range[data-selected-time-range="active"]', { timeout: 10_000 });
    await page.waitForFunction(() => window.__memoryAtlasStage5Phase3?.()?.selectedRangeActive === true, null, {
      timeout: 10_000,
    });
    const brushed = await readStage5Phase3(page);
    assertCondition(
      brushed?.selectedRangeActive === true && Number(brushed?.selectedRange?.eventCount || 0) > 0,
      "stage5_phase3_browser_brush_interaction",
      "Brush interaction creates a selected Memory River time range and exposes selected event metadata",
      "Brush interaction did not create a selected range",
      brushed,
    );

    const screenshotPath = path.join(outputDir, "memory-river-stage5-phase3.png");
    await page.screenshot({ path: screenshotPath, fullPage: false });
    const screenshotBytes = fs.statSync(screenshotPath).size;
    assertCondition(
      screenshotBytes > 20_000,
      "stage5_phase3_browser_screenshot",
      `Browser integration screenshot captured ${screenshotBytes} bytes`,
      "Browser integration screenshot is unexpectedly small",
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
      "stage5_phase3_browser_console",
      "Browser integration test completed without actionable console errors or failed responses",
      "Browser integration test produced actionable console errors or failed responses",
      { consoleMessages, failedResponses, actionableConsoleErrors, actionableFailedResponses },
    );

    await browser.close();
    console.log(
      JSON.stringify(
        {
          status: "PASS",
          validator: "validate_memory_river_integration_browser",
          url: targetUrl,
          output_dir: outputDir,
          checks,
        },
        null,
        2,
      ),
    );
  } catch (error) {
    await browser.close();
    console.error(
      JSON.stringify(
        {
          status: "FAIL",
          validator: "validate_memory_river_integration_browser",
          url: targetUrl,
          output_dir: outputDir,
          error: error.message,
          details: error.details || null,
          checks,
        },
        null,
        2,
      ),
    );
    process.exit(1);
  }
}

main();
