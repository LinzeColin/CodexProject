#!/usr/bin/env node
"use strict";

const fs = require("node:fs");
const http = require("node:http");
const os = require("node:os");
const path = require("node:path");
const { spawn, spawnSync } = require("node:child_process");

const appRoot = path.resolve(__dirname, "..");
const repoRoot = path.resolve(appRoot, "../..");
const port = Number(process.env.MEMORY_ATLAS_STAGE9_OBSIDIAN_PORT || 4177);
const targetUrl = `http://127.0.0.1:${port}`;
const outputDir = process.env.MEMORY_ATLAS_STAGE9_OBSIDIAN_DIR || fs.mkdtempSync(path.join(os.tmpdir(), "memory-atlas-stage9-obsidian-"));
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
  assertCondition(fs.existsSync(tsc) && fs.existsSync(vite), "stage9_1_dependencies_ready", "TypeScript and Vite CLIs are available in node_modules", "TypeScript or Vite CLI missing from app node_modules");
  run(process.execPath, [tsc, "-b"], { cwd: appRoot });
  run(process.execPath, [vite, "build", "--emptyOutDir"], { cwd: appRoot });
  assertCondition(
    fs.existsSync(path.join(appRoot, "dist/index.html")) && fs.existsSync(path.join(appRoot, "dist/memory_atlas.json")),
    "stage9_1_build_ready",
    "Production build created dist/index.html and dist/memory_atlas.json",
    "Production build did not create expected release files",
  );
}

function validateSourceContracts() {
  const obsidian = fs.readFileSync(path.join(appRoot, "src/components/ObsidianGraphScene.tsx"), "utf8");
  const app = fs.readFileSync(path.join(appRoot, "src/App.tsx"), "utf8");
  const css = fs.readFileSync(path.join(appRoot, "src/styles.css"), "utf8");
  const packageSource = fs.readFileSync(path.join(appRoot, "package.json"), "utf8");
  assertCondition(
    hasAll(obsidian, [
      "LOCAL_GRAPH_PRIMARY_NODE_LIMIT",
      "LOCAL_GRAPH_SECONDARY_NODE_LIMIT",
      "LOCAL_GRAPH_CLUSTER_MEMBER_LIMIT",
      "buildLocalGraphPlan",
      "sharedFocus.sourceView === \"galaxy\"",
      "data-local-graph-mode",
      "data-galaxy-cluster-focus",
      "data-hidden-local-neighbors",
      "data-label-budget",
      "labelVisibilityRule",
      "data-label-rule",
      "Local Graph Budget",
    ]) && hasAll(app, [
      "sharedFocus={sharedState.focus}",
      "sharedState: SharedAtlasState",
    ]) && hasAll(css, [
      ".obsidian-local-budget",
      ".obsidian-node-label[data-label-rule=\"local-neighbor\"]",
    ]) && packageSource.includes('"validate:stage9-obsidian": "node scripts/validate_stage9_obsidian_iteration.cjs"'),
    "stage9_1_source_contracts",
    "Source exposes local graph budget, Galaxy cluster focus sync, label rules, styles, and package validator",
    "Stage 9.1 source contract is incomplete",
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
  const server = spawn(process.execPath, [viteCli, "preview", "--host", "127.0.0.1", "--port", String(port), "--strictPort"], {
    cwd: appRoot,
    env: { ...process.env },
    stdio: ["ignore", "pipe", "pipe"],
  });
  return server;
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

async function validateBrowserObsidian() {
  const { chromium } = requirePlaywright();
  assertCondition(Boolean(browserExecutable), "stage9_1_browser_available", `Using Chromium-compatible browser: ${browserExecutable}`, "No Chromium-compatible browser executable found");
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

    await page.goto(targetUrl, { waitUntil: "domcontentloaded", timeout: 20000 });
    await page.waitForSelector('.content-grid[data-view="home"]', { timeout: 20000 });
    await page.getByRole("button", { name: /Obsidian 图谱/ }).click({ timeout: 5000 });
    await page.waitForSelector(".obsidian-graph-canvas", { timeout: 20000 });
    await page.waitForFunction(() => document.querySelectorAll(".obsidian-node").length > 12 && document.querySelectorAll(".obsidian-link").length > 8, null, { timeout: 10000 });
    await page.waitForTimeout(500);

    const globalState = await inspectObsidian(page);
    assertCondition(
      globalState.localMode === "global" && globalState.nodeCount > 12 && globalState.labelCount <= Math.max(20, Math.ceil(globalState.nodeCount * 0.45)),
      "stage9_1_default_label_budget",
      "Default Obsidian Graph opens globally with bounded label density",
      "Default Obsidian Graph is overloaded or not global",
      globalState,
    );

    await page.locator(".obsidian-node").first().click({ force: true, timeout: 5000 });
    await page.getByRole("button", { name: /^局部图$/ }).click({ timeout: 5000 });
    await page.waitForFunction(() => document.querySelector(".obsidian-graph-view")?.getAttribute("data-local-graph-mode") === "node", null, { timeout: 10000 });
    await page.waitForFunction(() => {
      const count = document.querySelectorAll(".obsidian-node").length;
      return count > 3 && count <= 96;
    }, null, { timeout: 10000 });
    const localState = await inspectObsidian(page);
    assertCondition(
      localState.localMode === "node"
        && localState.nodeCount <= 96
        && localState.edgeCount > 0
        && localState.localBudgetVisible
        && (localState.labelRules.includes("local-neighbor") || localState.labelRules.includes("hub")),
      "stage9_1_local_graph_budget",
      "Local graph caps high-degree neighborhood and uses selected/local label rules",
      "Local graph budget or label rule behavior is missing",
      localState,
    );

    await page.getByRole("button", { name: /^全局图$/ }).click({ timeout: 5000 });
    await page.getByRole("button", { name: /银河星云/ }).click({ timeout: 5000 });
    await page.waitForSelector(".galaxy-webgl-canvas", { timeout: 20000 });
    const canvasBox = await page.locator(".galaxy-webgl-canvas").boundingBox();
    assertCondition(Boolean(canvasBox), "stage9_1_galaxy_canvas_ready", "Galaxy canvas is visible for shared focus probe", "Galaxy canvas has no bounding box");
    await page.mouse.click(canvasBox.x + canvasBox.width / 2, canvasBox.y + canvasBox.height / 2);
    await page.waitForTimeout(500);
    await page.getByRole("button", { name: /Obsidian 图谱/ }).click({ timeout: 5000 });
    await page.waitForSelector(".obsidian-graph-canvas", { timeout: 20000 });
    await page.waitForFunction(() => {
      const view = document.querySelector(".obsidian-graph-view");
      return view?.getAttribute("data-local-graph-mode") === "cluster" || view?.getAttribute("data-galaxy-cluster-focus");
    }, null, { timeout: 12000 });
    await page.waitForFunction(() => {
      const count = document.querySelectorAll(".obsidian-node").length;
      return count > 3 && count <= 96;
    }, null, { timeout: 10000 });
    const syncedState = await inspectObsidian(page);
    assertCondition(
      syncedState.localMode === "cluster" && syncedState.galaxyClusterFocus && syncedState.nodeCount <= 96,
      "stage9_1_galaxy_cluster_sync",
      "Galaxy cluster focus opens Obsidian local cluster graph with bounded node count",
      "Galaxy cluster focus did not synchronize into Obsidian local graph",
      syncedState,
    );

    const screenshotPath = path.join(outputDir, "stage9-obsidian-local-sync.png");
    await page.screenshot({ path: screenshotPath, fullPage: false });
    const screenshotBytes = fs.statSync(screenshotPath).size;
    assertCondition(screenshotBytes > 20_000, "stage9_1_obsidian_screenshot", `Obsidian Stage 9.1 screenshot ${screenshotBytes} bytes`, "Obsidian Stage 9.1 screenshot is unexpectedly small", { screenshotPath, screenshotBytes });

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
      "stage9_1_browser_console_clean",
      "Stage 9.1 browser validation completed without actionable console errors or failed responses",
      "Stage 9.1 browser validation produced actionable console errors or failed responses",
      { consoleErrors, failedResponses, actionableConsoleErrors, actionableFailedResponses },
    );
    await page.close();
  } finally {
    await browser.close();
  }
}

async function inspectObsidian(page) {
  return page.evaluate(() => {
    const root = document.querySelector(".obsidian-graph-view");
    return {
      localMode: root?.getAttribute("data-local-graph-mode") || "",
      galaxyClusterFocus: root?.getAttribute("data-galaxy-cluster-focus") || "",
      hiddenLocalNeighbors: Number(root?.getAttribute("data-hidden-local-neighbors") || "0"),
      labelBudget: Number(root?.getAttribute("data-label-budget") || "0"),
      nodeCount: document.querySelectorAll(".obsidian-node").length,
      edgeCount: document.querySelectorAll(".obsidian-link").length,
      labelCount: document.querySelectorAll(".obsidian-node-label").length,
      labelRules: Array.from(document.querySelectorAll(".obsidian-node-label")).map((label) => label.getAttribute("data-label-rule") || ""),
      localBudgetVisible: Boolean(document.querySelector(".obsidian-local-budget")),
      focusText: document.querySelector(".obsidian-focus-connectivity")?.textContent || "",
    };
  });
}

(async () => {
  let preview = null;
  try {
    fs.mkdirSync(outputDir, { recursive: true });
    buildFrontend();
    validateSourceContracts();
    preview = startPreviewServer();
    await waitForHttp(`${targetUrl}/memory_atlas.json`);
    await validateBrowserObsidian();
  } catch (error) {
    checks.push({
      name: "stage9_1_obsidian_iteration",
      status: "FAIL",
      evidence: error.message,
      details: error.details || { stdout: error.stdout, stderr: error.stderr },
    });
    console.error(JSON.stringify({ status: "FAIL", outputDir, checks }, null, 2));
    process.exitCode = 1;
  } finally {
    if (preview) await stopPreviewServer(preview);
    try {
      await assertPortClosed();
      if (!process.exitCode) pass("stage9_1_preview_cleanup", `Port ${port} released after Stage 9.1 validation`);
    } catch (error) {
      checks.push({ name: "stage9_1_preview_cleanup", status: "FAIL", evidence: error.message });
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
