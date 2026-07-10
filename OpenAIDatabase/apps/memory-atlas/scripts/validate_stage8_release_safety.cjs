#!/usr/bin/env node
"use strict";

const fs = require("node:fs");
const http = require("node:http");
const os = require("node:os");
const path = require("node:path");
const { spawn, spawnSync } = require("node:child_process");

const appRoot = path.resolve(__dirname, "..");
const repoRoot = path.resolve(appRoot, "../..");
const port = Number(process.env.MEMORY_ATLAS_STAGE8_RELEASE_PORT || 4177);
const targetUrl = `http://127.0.0.1:${port}`;
const outputDir = process.env.MEMORY_ATLAS_STAGE8_RELEASE_DIR || fs.mkdtempSync(path.join(os.tmpdir(), "memory-atlas-stage8-release-safety-"));
const browserExecutable = process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH || findChromiumExecutable();

const visualFlagsPath = path.join(appRoot, "src/config/visualFlags.ts");
const appSourcePath = path.join(appRoot, "src/App.tsx");
const acceptanceDocPath = path.join(repoRoot, "docs/acceptance/memory_atlas_v1_1_5_stage8_2_release_safety.md");
const releaseNotesPath = path.join(repoRoot, "docs/release_notes/memory_atlas_v1_1_5_stage8_release_notes.md");
const reviewDocPath = path.join(repoRoot, "docs/reviews/memory_atlas_v1_1_5_stage8_2_review.md");
const modelParametersPath = path.join(repoRoot, "docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md");
const deliveryRecordPath = path.join(repoRoot, "docs/MEMORY_ATLAS_DELIVERY_RECORD.md");
const changelogPath = path.join(repoRoot, "CHANGELOG.md");

const checks = [];

function pass(name, evidence) {
  checks.push({ name, status: "PASS", evidence });
}

function assertCondition(condition, name, evidence, failure, details = {}) {
  if (condition) {
    pass(name, evidence);
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
    const candidate = fs
      .readdirSync(pnpmRoot)
      .filter((entry) => entry.startsWith("playwright@"))
      .sort()
      .at(-1);
    if (candidate) return require(path.join(pnpmRoot, candidate, "node_modules/playwright"));
  } catch {}
  throw new Error("Playwright is not resolvable from project dependencies or Codex bundled runtime");
}

function run(command, args, options = {}) {
  const result = spawnSync(command, args, {
    cwd: options.cwd || repoRoot,
    env: options.env || process.env,
    encoding: "utf8",
    stdio: options.stdio || "pipe",
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
  assertCondition(fs.existsSync(tsc) && fs.existsSync(vite), "stage8_2_dependencies_ready", "TypeScript and Vite CLIs are available in node_modules", "TypeScript or Vite CLI missing from app node_modules", { tsc, vite });
  run(process.execPath, [tsc, "-b"], { cwd: appRoot });
  run(process.execPath, [vite, "build", "--emptyOutDir"], { cwd: appRoot });
  assertCondition(
    fs.existsSync(path.join(appRoot, "dist/index.html")) && fs.existsSync(path.join(appRoot, "dist/memory_atlas.json")),
    "stage8_2_build_ready",
    "Production build created dist/index.html and dist/memory_atlas.json",
    "Production build did not create expected release files",
  );
}

function validateFlagSourceContracts() {
  const visualFlags = fs.readFileSync(visualFlagsPath, "utf8");
  const appSource = fs.readFileSync(appSourcePath, "utf8");
  assertCondition(
    hasAll(visualFlags, [
      'DEFAULT_GALAXY_RENDERER_MODE: GalaxyRendererMode = "memory-starfield"',
      'DEFAULT_TIMELINE_RENDERER_MODE: TimelineRendererMode = "memory-river"',
      'GALAXY_RENDERER_STORAGE_KEY = "memory-atlas.galaxy-renderer"',
      'TIMELINE_RENDERER_STORAGE_KEY = "memory-atlas.timeline-renderer"',
      "VITE_MEMORY_ATLAS_GALAXY_RENDERER",
      "VITE_MEMORY_ATLAS_TIMELINE_RENDERER",
      'params.get("galaxyRenderer") ?? params.get("galaxy")',
      'params.get("timelineRenderer") ?? params.get("timeline")',
      'value === "legacy" || value === "old"',
      'value === "legacy" || value === "old" || value === "timeline"',
    ]),
    "stage8_2_flag_source_contracts",
    "Visual flag config exposes default, URL, localStorage, env, and legacy rollback modes for Galaxy and Timeline",
    "Visual flag source contracts are missing default or rollback paths",
  );
  assertCondition(
    hasAll(appSource, [
      'aria-label="Galaxy renderer feature flag"',
      'aria-label="Timeline renderer feature flag"',
      'updateGalaxyRendererMode("legacy")',
      'updateTimelineRendererMode("legacy")',
      'data-timeline-renderer={timelineRendererMode}',
      '<GalaxyScene nodes={graphNodes} edges={graphEdges} rendererMode={galaxyRendererMode}',
    ]),
    "stage8_2_toggle_ui_contracts",
    "App UI exposes Galaxy and Timeline renderer toggles and passes selected modes to runtime renderers",
    "App UI is missing renderer rollback toggle contracts",
  );
}

function validateReleaseAudits() {
  run("python3", ["scripts/audit_memory_atlas_release.py", "--repo-root", repoRoot, "--publish-dir", path.join(appRoot, "dist")], { cwd: repoRoot });
  pass("stage8_2_release_audit", "Release audit passed on production dist");
  run("python3", ["scripts/audit_memory_atlas_acceptance.py", "--repo-root", repoRoot, "--publish-dir", path.join(appRoot, "dist")], { cwd: repoRoot });
  pass("stage8_2_acceptance_audit", "Overall acceptance audit passed on production dist");
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
  const server = spawn(process.execPath, [viteCli, "preview", "--host", "127.0.0.1", "--port", String(port), "--strictPort"], {
    cwd: appRoot,
    env: { ...process.env },
    stdio: ["ignore", "pipe", "pipe"],
  });
  const logs = [];
  server.stdout.on("data", (chunk) => logs.push(chunk.toString()));
  server.stderr.on("data", (chunk) => logs.push(chunk.toString()));
  return { server, logs };
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

async function validateBrowserRollback() {
  const { chromium } = requirePlaywright();
  assertCondition(Boolean(browserExecutable), "stage8_2_browser_available", `Using Chromium-compatible browser: ${browserExecutable}`, "No Chromium-compatible browser executable found");
  const browser = await chromium.launch({ executablePath: browserExecutable, headless: true });
  try {
    const page = await browser.newPage({ viewport: { width: 1440, height: 920 }, deviceScaleFactor: 1 });
    const consoleErrors = [];
    const failedResponses = [];
    page.on("console", (message) => {
      if (message.type() === "error") consoleErrors.push(message.text());
    });
    page.on("pageerror", (error) => consoleErrors.push(error.message));
    page.on("response", (response) => {
      if (response.status() >= 400) failedResponses.push({ status: response.status(), url: response.url() });
    });

    await page.goto(`${targetUrl}/?galaxyRenderer=legacy&timelineRenderer=legacy`, { waitUntil: "domcontentloaded", timeout: 20000 });
    await page.waitForSelector('.content-grid[data-view="home"]', { timeout: 20000 });

    await page.getByRole("button", { name: /银河星云/ }).click({ timeout: 5000 });
    await page.waitForSelector(".galaxy-webgl-canvas", { timeout: 20000 });
    await page.waitForFunction(() => window.__memoryAtlasGalaxySignal?.()?.rendererMode === "legacy", null, { timeout: 20000 });
    const legacyGalaxy = await page.evaluate(() => window.__memoryAtlasGalaxySignal?.() ?? null);
    assertCondition(
      legacyGalaxy?.rendererMode === "legacy" && legacyGalaxy?.fallbackMode === "legacy",
      "stage8_2_galaxy_url_rollback",
      "Galaxy URL flag rolls back to legacy renderer",
      "Galaxy URL rollback did not switch to legacy renderer",
      legacyGalaxy,
    );

    await page.getByRole("button", { name: /^Flow Field$/ }).click({ timeout: 5000 });
    await page.waitForFunction(() => window.__memoryAtlasGalaxySignal?.()?.rendererMode === "memory-starfield", null, { timeout: 20000 });
    const restoredGalaxy = await page.evaluate(() => ({
      signal: window.__memoryAtlasGalaxySignal?.() ?? null,
      stored: window.localStorage.getItem("memory-atlas.galaxy-renderer"),
    }));
    assertCondition(
      restoredGalaxy.signal?.rendererMode === "memory-starfield" && restoredGalaxy.stored === "memory-starfield",
      "stage8_2_galaxy_toggle_restore",
      "Galaxy in-app toggle restores memory-starfield and persists the selected renderer",
      "Galaxy in-app toggle did not restore or persist memory-starfield",
      restoredGalaxy,
    );

    await page.locator('[data-nav-view="timeline"]').click({ timeout: 5000 });
    await page.waitForSelector(".timeline-map", { timeout: 20000 });
    const legacyTimeline = await page.evaluate(() => ({
      renderer: document.querySelector(".timeline-map")?.getAttribute("data-timeline-renderer") || "",
      hasMemoryRiver: Boolean(document.querySelector(".memory-river-canvas")),
      hasLegacyCanvas: Boolean(document.querySelector(".timeline-canvas")),
    }));
    assertCondition(
      legacyTimeline.renderer === "legacy" && !legacyTimeline.hasMemoryRiver && legacyTimeline.hasLegacyCanvas,
      "stage8_2_timeline_url_rollback",
      "Timeline URL flag rolls back to legacy timeline renderer",
      "Timeline URL rollback did not switch to legacy renderer",
      legacyTimeline,
    );

    await page.getByRole("button", { name: /^Memory River$/ }).click({ timeout: 5000 });
    await page.waitForSelector(".memory-river-canvas", { timeout: 20000 });
    const restoredTimeline = await page.evaluate(() => ({
      renderer: document.querySelector(".timeline-map")?.getAttribute("data-timeline-renderer") || "",
      hasMemoryRiver: Boolean(document.querySelector(".memory-river-canvas")),
      stored: window.localStorage.getItem("memory-atlas.timeline-renderer"),
    }));
    assertCondition(
      restoredTimeline.renderer === "memory-river" && restoredTimeline.hasMemoryRiver && restoredTimeline.stored === "memory-river",
      "stage8_2_timeline_toggle_restore",
      "Timeline in-app toggle restores Memory River and persists the selected renderer",
      "Timeline in-app toggle did not restore or persist Memory River",
      restoredTimeline,
    );

    await page.goto(targetUrl, { waitUntil: "domcontentloaded", timeout: 20000 });
    await page.waitForSelector('.content-grid[data-view="home"]', { timeout: 20000 });
    await page.getByRole("button", { name: /银河星云/ }).click({ timeout: 5000 });
    await page.waitForFunction(() => window.__memoryAtlasGalaxySignal?.()?.rendererMode === "memory-starfield", null, { timeout: 20000 });
    await page.locator('[data-nav-view="timeline"]').click({ timeout: 5000 });
    await page.waitForSelector('.timeline-map[data-timeline-renderer="memory-river"]', { timeout: 20000 });
    pass("stage8_2_storage_restore", "Persisted renderer selections survive a fresh navigation without URL flags");

    const screenshotPath = path.join(outputDir, "stage8-release-safety-restored.png");
    await page.screenshot({ path: screenshotPath, fullPage: false });
    const screenshotBytes = fs.statSync(screenshotPath).size;
    assertCondition(screenshotBytes > 20_000, "stage8_2_restored_screenshot", `Restored Memory River screenshot ${screenshotBytes} bytes`, "Restored release-safety screenshot is unexpectedly small", { screenshotPath, screenshotBytes });

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
    assertCondition(
      actionableConsoleErrors.length === 0 && actionableFailedResponses.length === 0,
      "stage8_2_browser_console_clean",
      "Release-safety browser rollback test completed without actionable console errors or failed responses",
      "Release-safety browser rollback test produced actionable console errors or failed responses",
      { consoleErrors, failedResponses, actionableConsoleErrors, actionableFailedResponses },
    );
    await page.close();
  } finally {
    await browser.close();
  }
}

function validateDocs() {
  const acceptance = fs.readFileSync(acceptanceDocPath, "utf8");
  const releaseNotes = fs.readFileSync(releaseNotesPath, "utf8");
  const review = fs.readFileSync(reviewDocPath, "utf8");
  const model = fs.readFileSync(modelParametersPath, "utf8");
  const delivery = fs.readFileSync(deliveryRecordPath, "utf8");
  const changelog = fs.readFileSync(changelogPath, "utf8");
  assertCondition(
    hasAll(acceptance, [
      "Stage 8.2 Release Safety Acceptance",
      "8.2.1 Feature Flag Rollback",
      "8.2.2 Acceptance Audit",
      "8.2.3 Release Notes",
      "No Cloudflare live deploy",
      "No Access policy change",
      "No raw/private/cookie/session/secret",
      "No direct frontend writeback",
    ]),
    "stage8_2_acceptance_doc_current",
    "Acceptance doc records rollback, audit, notes, boundaries, and residual risks",
    "Acceptance doc is missing Stage 8.2 required sections",
  );
  assertCondition(
    hasAll(releaseNotes, [
      "Memory Atlas v1.1.5 Stage 8 Release Notes",
      "回滚",
      "Galaxy",
      "Timeline",
      "Cloudflare",
      "proposal-only",
    ]),
    "stage8_2_release_notes_current",
    "Release notes are Chinese-readable and include rollback and boundary notes",
    "Release notes are missing rollback or boundary guidance",
  );
  assertCondition(
    hasAll(review, [
      "Stage 8.2 is review-passed",
      "feature flag rollback",
      "acceptance audit",
      "release notes",
      "Stage 8 whole-stage review",
    ]),
    "stage8_2_review_doc_current",
    "Stage 8.2 review records phase PASS and next whole-stage review gate",
    "Stage 8.2 review doc is missing pass status or next gate",
  );
  assertCondition(
    hasAll(model, [
      "stage_8_2_release_safety_passed",
      "validate:stage8-release-safety",
      "VITE_MEMORY_ATLAS_GALAXY_RENDERER",
      "VITE_MEMORY_ATLAS_TIMELINE_RENDERER",
    ]),
    "stage8_2_model_parameters_current",
    "Model parameters record Stage 8.2 release safety thresholds",
    "Model parameters do not record Stage 8.2 release safety status",
  );
  assertCondition(
    hasAll(delivery, [
      "完成 Memory Atlas v1.1.5 Stage 8.2 Release Safety",
      "Stage 8 整体复审",
    ]),
    "stage8_2_delivery_record_current",
    "Delivery record marks Stage 8.2 complete and moves the next gate to Stage 8 whole-stage review",
    "Delivery record does not mark Stage 8.2 complete or next review gate",
  );
  assertCondition(
    hasAll(changelog, [
      "Memory Atlas v1.1.5 Stage 8.2 Release Safety",
      "validate:stage8-release-safety",
      "No Stage 8 whole-stage review",
    ]),
    "stage8_2_changelog_current",
    "Changelog records Stage 8.2 release safety and preserves non-goal boundaries",
    "Changelog does not record Stage 8.2 release safety status",
  );
}

(async () => {
  let preview = null;
  try {
    fs.mkdirSync(outputDir, { recursive: true });
    buildFrontend();
    validateFlagSourceContracts();
    validateReleaseAudits();
    validateDocs();
    preview = startPreviewServer();
    await waitForHttp(`${targetUrl}/memory_atlas.json`);
    await validateBrowserRollback();
  } catch (error) {
    checks.push({
      name: "stage8_2_release_safety",
      status: "FAIL",
      evidence: error.message,
      details: error.details || { stdout: error.stdout, stderr: error.stderr },
    });
    console.error(JSON.stringify({ status: "FAIL", outputDir, checks }, null, 2));
    process.exitCode = 1;
  } finally {
    if (preview) await stopPreviewServer(preview.server);
    try {
      await assertPortClosed();
      if (!process.exitCode) pass("stage8_2_preview_cleanup", `Port ${port} released after release-safety validation`);
    } catch (error) {
      checks.push({ name: "stage8_2_preview_cleanup", status: "FAIL", evidence: error.message });
      process.exitCode = 1;
    }
  }

  if (!process.exitCode) {
    console.log(JSON.stringify({ status: "PASS", outputDir, checks }, null, 2));
  } else {
    console.error(JSON.stringify({ status: "FAIL", outputDir, checks }, null, 2));
  }
})();

function hasAll(source, needles) {
  return needles.every((needle) => source.includes(needle));
}
