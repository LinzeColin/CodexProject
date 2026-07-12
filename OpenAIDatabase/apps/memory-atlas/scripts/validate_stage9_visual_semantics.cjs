#!/usr/bin/env node
"use strict";

const fs = require("node:fs");
const http = require("node:http");
const os = require("node:os");
const path = require("node:path");
const { spawn, spawnSync } = require("node:child_process");

const appRoot = path.resolve(__dirname, "..");
const repoRoot = path.resolve(appRoot, "../..");
const port = Number(process.env.MEMORY_ATLAS_STAGE9_VISUAL_SEMANTICS_PORT || 4177);
const targetUrl = `http://127.0.0.1:${port}`;
const outputDir = process.env.MEMORY_ATLAS_STAGE9_VISUAL_SEMANTICS_DIR || fs.mkdtempSync(path.join(os.tmpdir(), "memory-atlas-stage9-visual-semantics-"));
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

function hasAll(source, fragments) {
  return fragments.every((fragment) => source.includes(fragment));
}

function run(command, args, options = {}) {
  const result = spawnSync(command, args, {
    cwd: options.cwd || repoRoot,
    env: options.env || process.env,
    encoding: "utf8",
    stdio: "pipe",
  });
  if (result.status !== 0) {
    const error = new Error(`${command} ${args.join(" ")} failed with ${result.status}`);
    error.stdout = result.stdout;
    error.stderr = result.stderr;
    throw error;
  }
  return result;
}

function buildFrontend() {
  const tsc = path.join(appRoot, "node_modules/typescript/bin/tsc");
  const vite = path.join(appRoot, "node_modules/vite/bin/vite.js");
  assertCondition(fs.existsSync(tsc) && fs.existsSync(vite), "stage9_2_dependencies_ready", "TypeScript and Vite CLIs are available in node_modules", "TypeScript or Vite CLI missing from app node_modules");
  run(process.execPath, [tsc, "-b"], { cwd: appRoot });
  run(process.execPath, [vite, "build", "--emptyOutDir"], { cwd: appRoot });
  assertCondition(
    fs.existsSync(path.join(appRoot, "dist/index.html")) && fs.existsSync(path.join(appRoot, "dist/memory_atlas.json")),
    "stage9_2_build_ready",
    "Production build created dist/index.html and dist/memory_atlas.json",
    "Production build did not create expected release files",
  );
}

function validateSourceContracts() {
  const app = fs.readFileSync(path.join(appRoot, "src/App.tsx"), "utf8");
  const galaxy = fs.readFileSync(path.join(appRoot, "src/components/GalaxyScene.tsx"), "utf8");
  const css = fs.readFileSync(path.join(appRoot, "src/styles.css"), "utf8");
  const packageSource = fs.readFileSync(path.join(appRoot, "package.json"), "utf8");
  assertCondition(
    hasAll(app, [
      "Memory Weather v2",
      "data-memory-weather-v2",
      "buildMemoryWeatherV2",
      "memory-river-roi-gradient",
      "buildMemoryRiverRoiGradient",
      "data-roi-gradient=\"capability-growth\"",
    ]) && hasAll(galaxy, [
      "Memory Terrain v2",
      "data-memory-terrain-v2",
      "buildGalaxyRoiGradientSummary",
      "galaxy-roi-gradient-panel",
      "data-roi-gradient=\"galaxy-analysis\"",
    ]) && hasAll(css, [
      ".home-weather-v2-scores",
      ".galaxy-roi-gradient-panel",
      ".memory-river-roi-gradient",
    ]) && packageSource.includes('"validate:stage9-visual-semantics": "node scripts/validate_stage9_visual_semantics.cjs"'),
    "stage9_2_source_contracts",
    "Source exposes Memory Weather v2, Terrain v2, Galaxy ROI gradient, Memory River ROI gradient, styles, and package validator",
    "Stage 9.2 source contract is incomplete",
  );
}

function httpGet(url, timeoutMs = 2000) {
  return new Promise((resolve, reject) => {
    const request = http.get(url, (response) => {
      response.resume();
      response.on("end", () => resolve(response.statusCode || 0));
    });
    request.setTimeout(timeoutMs, () => request.destroy(new Error(`timeout waiting for ${url}`)));
    request.on("error", reject);
  });
}

async function waitForHttp(url, timeoutMs = 20000) {
  const started = Date.now();
  let lastError = null;
  while (Date.now() - started < timeoutMs) {
    try {
      const status = await httpGet(url, 1200);
      if (status >= 200 && status < 500) return status;
    } catch (error) {
      lastError = error;
    }
    await new Promise((resolve) => setTimeout(resolve, 250));
  }
  throw new Error(`Vite preview did not become ready at ${url}: ${lastError?.message || "unknown"}`);
}

function startPreviewServer() {
  const viteCli = path.join(appRoot, "node_modules/vite/bin/vite.js");
  return spawn(process.execPath, [viteCli, "preview", "--host", "127.0.0.1", "--port", String(port), "--strictPort"], {
    cwd: appRoot,
    env: { ...process.env },
    stdio: ["ignore", "pipe", "pipe"],
  });
}

async function stopPreviewServer(server) {
  if (!server || server.exitCode !== null) return;
  server.kill("SIGTERM");
  await Promise.race([
    new Promise((resolve) => server.once("exit", resolve)),
    new Promise((resolve) => setTimeout(resolve, 2500)),
  ]);
  if (server.exitCode === null) {
    server.kill("SIGKILL");
    await new Promise((resolve) => server.once("exit", resolve));
  }
}

async function assertPortClosed() {
  try {
    await httpGet(targetUrl, 600);
    throw new Error(`preview server still responds on ${targetUrl}`);
  } catch (error) {
    if (String(error.message || "").includes("still responds")) throw error;
  }
}

async function validateBrowserVisualSemantics() {
  const { chromium } = requirePlaywright();
  assertCondition(Boolean(browserExecutable), "stage9_2_browser_available", `Using Chromium-compatible browser: ${browserExecutable}`, "No Chromium-compatible browser executable found");
  const browser = await chromium.launch({ executablePath: browserExecutable, headless: true });
  try {
    const page = await browser.newPage({ viewport: { width: 1440, height: 920 }, deviceScaleFactor: 1 });
    const consoleErrors = [];
    const failedResponses = [];
    page.on("console", (message) => {
      if (message.type() !== "error") return;
      const text = message.text();
      if (/Failed to load resource: the server responded with a status of 404/.test(text)) return;
      consoleErrors.push(text);
    });
    page.on("pageerror", (error) => consoleErrors.push(error.message));
    page.on("response", (response) => {
      if (response.status() >= 400 && !response.url().endsWith("/favicon.ico")) {
        failedResponses.push({ status: response.status(), url: response.url() });
      }
    });

    await page.goto(`${targetUrl}?galaxyRenderer=memory-starfield&timelineRenderer=memory-river`, { waitUntil: "domcontentloaded", timeout: 20000 });
    await page.waitForSelector('.content-grid[data-view="home"]', { timeout: 20000 });
    const weatherState = await page.locator('[data-memory-weather-v2="true"]').evaluate((element) => ({
      label: element.querySelector("strong")?.textContent || "",
      scoreCount: element.querySelectorAll(".home-weather-v2-scores dd").length,
      signalCount: element.querySelectorAll(".home-weather-v2-signals li").length,
      confidence: element.getAttribute("data-weather-confidence"),
      risk: element.getAttribute("data-weather-risk"),
    }));
    assertCondition(
      weatherState.label.length > 0 && weatherState.scoreCount === 4 && weatherState.signalCount >= 3,
      "stage9_2_memory_weather_v2",
      "Home exposes stable Memory Weather v2 state judgment with four scores and signal list",
      "Memory Weather v2 browser contract is missing",
      weatherState,
    );

    await page.getByRole("button", { name: /银河星云/ }).click({ timeout: 5000 });
    await page.waitForSelector(".galaxy-scene", { timeout: 20000 });
    await page.getByRole("button", { name: /analysis mode/i }).click({ timeout: 10000 });
    await page.waitForSelector('[data-memory-terrain-v2="analysis-only"]', { timeout: 12000 });
    await page.waitForSelector('[data-roi-gradient="galaxy-analysis"]', { timeout: 12000 });
    const galaxyState = await page.evaluate(() => ({
      terrainRows: document.querySelectorAll("[data-terrain-v2-role]").length,
      coverage: document.querySelector("[data-memory-terrain-v2]")?.getAttribute("data-terrain-semantic-coverage"),
      roiRows: document.querySelectorAll("[data-roi-gradient-row]").length,
      terrainText: document.querySelector("[data-memory-terrain-v2]")?.textContent || "",
      roiText: document.querySelector('[data-roi-gradient="galaxy-analysis"]')?.textContent || "",
    }));
    assertCondition(
      galaxyState.terrainRows >= 5 && galaxyState.roiRows >= 4 && galaxyState.terrainText.includes("analysis-only") && galaxyState.roiText.includes("ROI"),
      "stage9_2_galaxy_terrain_roi",
      "Galaxy analysis mode exposes explainable Terrain v2 and ROI capability gradient overlays",
      "Galaxy Terrain v2 or ROI gradient browser contract is missing",
      galaxyState,
    );

    await page.locator('[data-nav-view="timeline"]').click({ timeout: 5000 });
    await page.waitForSelector('.content-grid[data-view="timeline"]', { timeout: 20000 });
    await page.waitForSelector('.memory-river-canvas[data-roi-gradient="capability-growth"]', { timeout: 20000 });
    const riverState = await page.evaluate(() => ({
      bandCount: document.querySelectorAll("[data-roi-gradient-band]").length,
      text: document.querySelector(".memory-river-roi-gradient")?.textContent || "",
      evidenceLayers: document.querySelector(".memory-river-canvas")?.getAttribute("data-evidence-layers"),
    }));
    assertCondition(
      riverState.bandCount >= 8 && riverState.text.includes("ROI gradient") && riverState.evidenceLayers?.includes("roi-gradient"),
      "stage9_2_memory_river_roi_gradient",
      "Memory River renders ROI/capability gradient as a visible analysis overlay",
      "Memory River ROI gradient browser contract is missing",
      riverState,
    );

    await page.screenshot({ path: path.join(outputDir, "stage9_2_visual_semantics.png"), fullPage: true });
    const actionableFailedResponses = failedResponses.filter((response) => {
      try {
        const pathname = new URL(response.url).pathname;
        return !["/__memory_atlas_heartbeat", "/__memory_atlas_release"].includes(pathname);
      } catch {
        return true;
      }
    });
    const actionableConsoleErrors = consoleErrors.filter((message) => {
      return !(message.startsWith("Failed to load resource:") && actionableFailedResponses.length === 0);
    });
    assertCondition(actionableConsoleErrors.length === 0, "stage9_2_browser_console_clean", "No actionable browser console/page errors during Stage 9.2 visual semantics probe", "Browser console/page errors were emitted", { consoleErrors, actionableConsoleErrors });
    assertCondition(actionableFailedResponses.length === 0, "stage9_2_browser_network_clean", "No actionable HTTP >=400 responses during Stage 9.2 visual semantics probe", "Browser network failures were emitted", { failedResponses, actionableFailedResponses });
  } finally {
    await browser.close();
  }
}

async function main() {
  let server = null;
  try {
    validateSourceContracts();
    buildFrontend();
    server = startPreviewServer();
    await waitForHttp(targetUrl);
    await validateBrowserVisualSemantics();
  } finally {
    await stopPreviewServer(server);
    await assertPortClosed();
  }
  pass("stage9_2_port_cleanup", `Preview server stopped and ${targetUrl} no longer responds`);
  const report = {
    status: "PASS",
    stage: "9.2",
    outputDir,
    checks,
  };
  console.log(JSON.stringify(report, null, 2));
}

main().catch((error) => {
  const report = {
    status: "FAIL",
    stage: "9.2",
    outputDir,
    checks,
    error: {
      message: error.message,
      details: error.details || null,
      stdout: error.stdout || "",
      stderr: error.stderr || "",
    },
  };
  console.error(JSON.stringify(report, null, 2));
  process.exit(1);
});
