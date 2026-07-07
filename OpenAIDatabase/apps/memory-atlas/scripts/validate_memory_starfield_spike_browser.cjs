#!/usr/bin/env node
"use strict";

const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");

const outputDir = getArg("--output-dir") || fs.mkdtempSync(path.join(os.tmpdir(), "memory-starfield-spike-browser-"));
const targetUrl = getArg("--url") || "http://127.0.0.1:5173/src/experiments/memory-starfield-spike/index.html";
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
    await page.waitForFunction(() => Boolean(window.__memoryStarfieldSpike?.metrics), null, { timeout: 20_000 });
    await page.waitForFunction(() => (window.__memoryStarfieldSpike?.metrics?.fps || 0) >= 30, null, {
      timeout: 20_000,
    });

    const beforeHover = await page.evaluate(() => window.__memoryStarfieldSpike.metrics);
    assertCondition(
      beforeHover.particleCount >= 10000,
      "stage4_phase2_browser_particle_count",
      "Browser spike reports particleCount >= 10000",
      "Browser spike particleCount is below 10000",
      beforeHover,
    );
    assertCondition(
      beforeHover.fps >= 30,
      "stage4_phase2_browser_fps",
      "Browser spike reports fps >= 30",
      "Browser spike fps is below 30",
      beforeHover,
    );
    assertCondition(
      beforeHover.flowFieldMode === "curl_noise_shader",
      "stage4_phase2_browser_flow_field",
      "Browser spike reports curl_noise_shader flow field mode",
      "Browser spike flow field mode is not curl_noise_shader",
      beforeHover,
    );
    assertCondition(
      beforeHover.trajectoryTrailCount >= 256,
      "stage4_phase2_browser_particle_trails",
      "Browser spike reports trajectoryTrailCount >= 256",
      "Browser spike does not report enough particle trails",
      beforeHover,
    );
    assertCondition(
      beforeHover.gravitySourceCount >= 6,
      "stage4_phase2_browser_gravity_sources",
      "Browser spike reports at least six gravity sources",
      "Browser spike does not report enough gravity sources",
      beforeHover,
    );
    assertCondition(
      beforeHover.hoverCardMode === "B2",
      "stage4_phase2_browser_hover_mode",
      "Browser spike reports Hover Cards B2 mode",
      "Browser spike hover card mode is not B2",
      beforeHover,
    );

    const target = await page.evaluate(() => window.__memoryStarfieldSpike.getClusterScreenPosition("cluster-visual-ux"));
    assertCondition(
      target && Number.isFinite(target.x) && Number.isFinite(target.y),
      "stage4_phase2_browser_hover_target",
      "Browser spike exposes projected cluster screen position for hover validation",
      "Browser spike did not expose a valid hover target",
      { target },
    );

    await page.mouse.move(target.x, target.y);
    await page.waitForFunction(
      () => window.__memoryStarfieldSpike?.metrics?.hoveredClusterId === "cluster-visual-ux",
      null,
      { timeout: 10_000 },
    );
    const hoverText = await page.locator("#hoverCard").innerText();
    assertCondition(
      hoverText.includes("可视化体验升级") &&
        hoverText.includes("Importance") &&
        hoverText.includes("Priority"),
      "stage4_phase2_browser_hover_card_b2",
      "Hover card B2 shows topic, summary, importance and priority without blocking the canvas",
      "Hover card B2 did not expose required fields",
      { hoverText },
    );

    const screenshotPath = path.join(outputDir, "memory-starfield-stage4-phase2.png");
    await page.screenshot({ path: screenshotPath, fullPage: false });
    const screenshotBytes = fs.statSync(screenshotPath).size;
    assertCondition(
      screenshotBytes > 20_000,
      "stage4_phase2_browser_screenshot",
      `Browser screenshot captured ${screenshotBytes} bytes`,
      "Browser screenshot is unexpectedly small",
      { screenshotPath, screenshotBytes },
    );

    assertCondition(
      beforeHover.consoleErrors === 0 && consoleMessages.length === 0,
      "stage4_phase2_browser_console",
      "Browser spike reports no console errors",
      "Browser spike reported console errors",
      { metricsConsoleErrors: beforeHover.consoleErrors, consoleMessages },
    );

    await browser.close();
    console.log(
      JSON.stringify(
        {
          status: "PASS",
          validator: "validate_memory_starfield_spike_browser",
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
          validator: "validate_memory_starfield_spike_browser",
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
