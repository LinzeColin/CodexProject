#!/usr/bin/env node
"use strict";

const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");

const outputDir = getArg("--output-dir") || fs.mkdtempSync(path.join(os.tmpdir(), "memory-river-spike-browser-"));
const targetUrl =
  getArg("--url") || "http://127.0.0.1:5173/src/experiments/memory-river-spike/index.html?smoke=1";
const browserExecutable = process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH || findChromiumExecutable();
const checks = [];

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
  page.on("console", (message) => {
    if (message.type() === "error") consoleMessages.push(message.text());
  });

  try {
    await page.goto(targetUrl, { waitUntil: "networkidle", timeout: 30_000 });
    await page.waitForFunction(() => Boolean(window.__memoryRiverSpike?.metrics), null, { timeout: 20_000 });
    await page.waitForFunction(() => JSON.parse(document.querySelector("#smokeStatus")?.textContent || "{}").ready, null, {
      timeout: 20_000,
    });

    const initial = await page.evaluate(() => window.__memoryRiverSpike.metrics);
    assertCondition(
      initial.spikeVersion === "memory_river_c3_spike.v1_1_7_stage5_phase2" &&
        initial.d3ScaleUtc &&
        initial.d3Zoom &&
        initial.d3Brush,
      "stage5_phase2_browser_runtime_contract",
      "Browser spike exposes Stage 5.2 version plus D3 UTC scale, zoom and brush metrics",
      "Browser spike did not expose required Stage 5.2 runtime metrics",
      initial,
    );

    assertCondition(
      ["year", "month", "week", "day"].every((level) => initial.availableTimeLevels.includes(level)),
      "stage5_phase2_browser_time_levels",
      "Browser spike exposes year, month, week and day time scale levels",
      "Browser spike is missing required time scale levels",
      initial,
    );

    for (const level of ["year", "month", "week", "day"]) {
      await page.evaluate((nextLevel) => window.__memoryRiverSpike.api.setTimeLevel(nextLevel), level);
      await page.waitForFunction((nextLevel) => window.__memoryRiverSpike.metrics.activeTimeLevel === nextLevel, level, {
        timeout: 5_000,
      });
    }
    pass("stage5_phase2_browser_time_level_switching", "Browser controls can switch through year, month, week and day");

    await page.evaluate(() => window.__memoryRiverSpike.api.reset());
    const beforeZoom = await page.evaluate(() => window.__memoryRiverSpike.metrics.zoomK);
    await page.mouse.move(720, 450);
    await page.mouse.wheel(0, -1200);
    await page.waitForFunction((zoomK) => window.__memoryRiverSpike.metrics.zoomK > zoomK, beforeZoom, { timeout: 10_000 });
    const afterZoom = await page.evaluate(() => window.__memoryRiverSpike.metrics);
    assertCondition(
      afterZoom.zoomK > beforeZoom,
      "stage5_phase2_browser_zoom",
      "Browser wheel zoom increases the Memory River zoom scale",
      "Browser zoom did not increase",
      { beforeZoom, afterZoom: afterZoom.zoomK, activeTimeLevel: afterZoom.activeTimeLevel },
    );

    await page.evaluate(() => {
      window.__memoryRiverSpike.api.reset();
      window.__memoryRiverSpike.api.setBrushRange("2026-03-01T00:00:00Z", "2026-06-15T00:00:00Z");
    });
    await page.waitForFunction(() => (window.__memoryRiverSpike.metrics.selectedRangeSummary?.eventCount || 0) >= 4, null, {
      timeout: 10_000,
    });
    const brushed = await page.evaluate(() => window.__memoryRiverSpike.metrics);
    assertCondition(
      Array.isArray(brushed.brushRange) &&
        brushed.selectedRangeSummary.themeCount >= 3 &&
        brushed.selectedRangeSummary.eventCount >= 4,
      "stage5_phase2_browser_brush_selection",
      "Browser brush selection creates a readable selected range with multiple themes and events",
      "Browser brush selection did not produce the required selected summary",
      brushed,
    );
    assertCondition(
      brushed.selectedRangeSummary.themes.some((theme) => theme.includes("trend: rising")) &&
        brushed.selectedRangeSummary.themes.some((theme) => theme.includes("trend: conflict")) &&
        brushed.selectedRangeSummary.signals.some((signal) => signal.includes("Black Hole")) &&
        brushed.selectedRangeSummary.signals.some((signal) => signal.includes("Proto-Star")),
      "stage5_phase2_browser_selected_theme_events",
      "Selected range summary includes trend lanes plus Black Hole and Proto-Star signals",
      "Selected range summary is missing trend lanes or status signals",
      brushed.selectedRangeSummary,
    );

    const signalPositions = await page.evaluate(() => ({
      bandStartX: window.__memoryRiverSpike.api.getDateScreenX("2026-03-18T00:00:00Z"),
      protoX: window.__memoryRiverSpike.api.getDateScreenX("2026-05-21T00:00:00Z"),
      metrics: window.__memoryRiverSpike.metrics.signalPositions,
    }));
    assertCondition(
      Number.isFinite(signalPositions.bandStartX) &&
        Number.isFinite(signalPositions.protoX) &&
        signalPositions.metrics.blackHoleBandCount >= 1 &&
        signalPositions.metrics.protoStarCount >= 2,
      "stage5_phase2_browser_signal_positioning",
      "Browser spike positions Black Hole and Proto-Star signals on the time scale",
      "Browser spike did not expose valid signal positions",
      signalPositions,
    );

    await page.evaluate(() => window.__memoryRiverSpike.api.setReducedMotion(true));
    await page.waitForFunction(() => window.__memoryRiverSpike.metrics.reducedMotion === true, null, { timeout: 5_000 });
    const reducedMotion = await page.evaluate(() => ({
      metric: window.__memoryRiverSpike.metrics.reducedMotion,
      body: document.body.dataset.reducedMotion,
    }));
    assertCondition(
      reducedMotion.metric === true && reducedMotion.body === "true",
      "stage5_phase2_browser_reduced_motion",
      "Reduced motion disables continuous river animation while keeping runtime interactive",
      "Reduced motion state was not applied",
      reducedMotion,
    );

    const screenshotPath = path.join(outputDir, "memory-river-stage5-phase2.png");
    await page.screenshot({ path: screenshotPath, fullPage: false });
    const screenshotBytes = fs.statSync(screenshotPath).size;
    assertCondition(
      screenshotBytes > 20_000,
      "stage5_phase2_browser_screenshot",
      `Browser screenshot captured ${screenshotBytes} bytes`,
      "Browser screenshot is unexpectedly small",
      { screenshotPath, screenshotBytes },
    );

    const finalMetrics = await page.evaluate(() => window.__memoryRiverSpike.metrics);
    assertCondition(
      finalMetrics.consoleErrors === 0 && consoleMessages.length === 0,
      "stage5_phase2_browser_console",
      "Browser spike reports no console errors",
      "Browser spike reported console errors",
      { metricsConsoleErrors: finalMetrics.consoleErrors, consoleMessages },
    );

    await browser.close();
    console.log(
      JSON.stringify(
        {
          status: "PASS",
          validator: "validate_memory_river_spike_browser",
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
          validator: "validate_memory_river_spike_browser",
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
