#!/usr/bin/env node
"use strict";

const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");

const outputDir = getArg("--output-dir") || fs.mkdtempSync(path.join(os.tmpdir(), "memory-starfield-integration-browser-"));
const targetUrl = getArg("--url") || "http://127.0.0.1:5173/";
const browserExecutable = process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH || findChromiumExecutable();
const checks = [];

const integrationVersion = "memory_starfield_integration.v1_1_7_stage4_phase3";
const mappingVersion = "memory_starfield_snapshot_mapping.v1_1_7_stage4_phase3";

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

async function readIntegration(page) {
  return page.evaluate(() => window.__memoryAtlasStage4Phase3?.() ?? null);
}

async function readGalaxySignal(page) {
  return page.evaluate(() => window.__memoryAtlasGalaxySignal?.() ?? null);
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
  await page.route("**/__memory_atlas_runtime_state", (route) => route.fulfill({ status: 204, body: "" }));
  await page.route("**/__memory_atlas_heartbeat", (route) => route.fulfill({ status: 204, body: "" }));
  await page.route("**/__memory_atlas_release", (route) => route.fulfill({ status: 204, body: "" }));

  try {
    await page.goto(targetUrl, { waitUntil: "networkidle", timeout: 30_000 });
    await page.getByRole("button", { name: "银河星云" }).click();
    await page.waitForSelector(".galaxy-scene", { timeout: 30_000 });
    await page.waitForFunction(() => Boolean(window.__memoryAtlasGalaxySignal?.()), null, { timeout: 20_000 });
    await page.waitForFunction(() => (window.__memoryAtlasGalaxySignal?.().fps || 0) >= 30, null, {
      timeout: 20_000,
    });

    const integration = await readIntegration(page);
    const defaultSignal = await readGalaxySignal(page);
    assertCondition(
      integration?.integrationVersion === integrationVersion &&
        integration?.mappingVersion === mappingVersion &&
        integration?.rendererMode === "memory-starfield",
      "stage4_phase3_browser_default_starfield",
      "Production Galaxy defaults to the new memory-starfield renderer with Stage 4.3 integration metadata",
      "Production Galaxy did not default to Stage 4.3 memory-starfield integration",
      { integration, defaultSignal },
    );

    assertCondition(
      defaultSignal?.rendererMode === "memory-starfield" &&
        defaultSignal?.mappingVersion === mappingVersion &&
        defaultSignal?.mappingSource === "universe_state_snapshot" &&
        defaultSignal?.mappedParticleCount >= 3 &&
        defaultSignal?.fps >= 30,
      "stage4_phase3_browser_snapshot_mapping",
      "Browser Galaxy reports redacted universe_state snapshot mapping with >=30 FPS",
      "Browser Galaxy did not expose valid Stage 4.3 snapshot mapping metadata",
      { defaultSignal },
    );

    await page.getByRole("button", { name: "analysis mode" }).click();
    await page.waitForSelector('[data-starfield-formula-panel="stage4-phase3"]', { timeout: 10_000 });
    const formulaText = await page.locator('[data-starfield-formula-panel="stage4-phase3"]').innerText();
    assertCondition(
      formulaText.includes("mass") &&
        formulaText.includes("brightness") &&
        formulaText.includes("color") &&
        formulaText.includes("trail") &&
        formulaText.includes("universe_state"),
      "stage4_phase3_browser_formula_panel",
      "Analysis panel explains mass, brightness, color and trail formulas from the redacted snapshot mapping",
      "Analysis panel did not expose the Stage 4.3 mapping formulas",
      { formulaText },
    );

    await page.getByRole("button", { name: "Legacy" }).click();
    await page.waitForFunction(() => window.__memoryAtlasStage4Phase3?.().rendererMode === "legacy", null, {
      timeout: 10_000,
    });
    const legacyIntegration = await readIntegration(page);
    const legacySignal = await readGalaxySignal(page);
    assertCondition(
      legacyIntegration?.rendererMode === "legacy" &&
        legacySignal?.rendererMode === "legacy" &&
        legacySignal?.fallbackMode === "legacy",
      "stage4_phase3_browser_legacy_switch",
      "Feature flag can switch back to the legacy Galaxy renderer as rollback",
      "Legacy renderer rollback did not work in browser validation",
      { legacyIntegration, legacySignal },
    );

    const screenshotPath = path.join(outputDir, "memory-starfield-stage4-phase3.png");
    await page.screenshot({ path: screenshotPath, fullPage: false });
    const screenshotBytes = fs.statSync(screenshotPath).size;
    assertCondition(
      screenshotBytes > 20_000,
      "stage4_phase3_browser_screenshot",
      `Browser integration screenshot captured ${screenshotBytes} bytes`,
      "Browser integration screenshot is unexpectedly small",
      { screenshotPath, screenshotBytes },
    );

    assertCondition(
      consoleMessages.length === 0,
      "stage4_phase3_browser_console",
      "Browser integration run reported no console errors",
      "Browser integration reported console errors",
      { consoleMessages },
    );

    await browser.close();
    console.log(
      JSON.stringify(
        {
          status: "PASS",
          validator: "validate_memory_starfield_integration_browser",
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
          validator: "validate_memory_starfield_integration_browser",
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
