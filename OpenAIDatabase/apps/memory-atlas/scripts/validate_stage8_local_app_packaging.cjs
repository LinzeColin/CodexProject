#!/usr/bin/env node
"use strict";

const fs = require("node:fs");
const http = require("node:http");
const os = require("node:os");
const path = require("node:path");
const { spawn, spawnSync } = require("node:child_process");

const appRoot = path.resolve(__dirname, "..");
const repoRoot = path.resolve(appRoot, "../..");
const port = Number(process.env.MEMORY_ATLAS_STAGE8_PORT || 4177);
const targetUrl = `http://127.0.0.1:${port}`;
const outputDir = process.env.MEMORY_ATLAS_STAGE8_AUDIT_DIR || fs.mkdtempSync(path.join(os.tmpdir(), "memory-atlas-stage8-local-app-"));
const browserExecutable = process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH || findChromiumExecutable();
const stage81Review = path.join(repoRoot, "docs/reviews/memory_atlas_v1_1_5_stage8_1_review.md");
const modelParameters = path.join(repoRoot, "docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md");
const deliveryRecord = path.join(repoRoot, "docs/MEMORY_ATLAS_DELIVERY_RECORD.md");
const changelog = path.join(repoRoot, "CHANGELOG.md");

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
  assertCondition(fs.existsSync(tsc) && fs.existsSync(vite), "stage8_1_dependencies_ready", "TypeScript and Vite CLIs are available in node_modules", "TypeScript or Vite CLI missing from app node_modules", { tsc, vite });
  run(process.execPath, [tsc, "-b"], { cwd: appRoot });
  run(process.execPath, [vite, "build", "--emptyOutDir"], { cwd: appRoot });
  const indexPath = path.join(appRoot, "dist/index.html");
  const atlasPath = path.join(appRoot, "dist/memory_atlas.json");
  assertCondition(fs.existsSync(indexPath) && fs.existsSync(atlasPath), "stage8_1_local_build", "Production build created dist/index.html and dist/memory_atlas.json", "Production build did not create the required local app runtime files", { indexPath, atlasPath });
}

function validateTemporaryAppBundle() {
  const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), "memory-atlas-stage8-bundle-"));
  const target = path.join(tempDir, "Memory Atlas.app");
  const appSupport = path.join(tempDir, "app-support");
  const env = { ...process.env, MEMORY_ATLAS_APP_SUPPORT_ROOT: appSupport };
  run("python3", ["scripts/install_memory_atlas_app.py", "--repo-root", repoRoot, "--target", target, "--skip-runtime"], { cwd: repoRoot, env });

  const executable = path.join(target, "Contents/MacOS/memory-atlas-launcher");
  const infoPlist = path.join(target, "Contents/Info.plist");
  const icon = path.join(target, "Contents/Resources/MemoryAtlas.icns");
  const sourceWorkspace = path.join(appSupport, "source");
  assertCondition(
    fs.existsSync(executable) && fs.statSync(executable).mode & 0o111 && fs.existsSync(infoPlist) && fs.existsSync(icon) && fs.statSync(icon).size > 1024,
    "stage8_1_temp_app_bundle",
    "Installer creates an executable Memory Atlas.app bundle with plist and icon in a temporary target",
    "Temporary Memory Atlas.app bundle is incomplete",
    { executable, infoPlist, icon },
  );
  assertCondition(
    fs.existsSync(path.join(sourceWorkspace, "apps/memory-atlas/package.json"))
      && fs.existsSync(path.join(sourceWorkspace, "scripts/sync_codex_memory_data.py"))
      && fs.existsSync(path.join(sourceWorkspace, "memory_atlas_source_workspace.json"))
      && !fs.existsSync(path.join(sourceWorkspace, ".git"))
      && !fs.existsSync(path.join(sourceWorkspace, "apps/memory-atlas/node_modules")),
    "stage8_1_source_workspace",
    "Installer copies a clean Application Support source workspace without .git or node_modules",
    "Application Support source workspace is missing required files or contains excluded state",
    { sourceWorkspace },
  );

  const launcherText = fs.readFileSync(executable, "utf8");
  const singleWindowContract = launcherText.includes('open "$STATUS_FILE"')
    && !launcherText.includes('open "$URL"')
    && launcherText.includes("Status page will redirect to the ready app.")
    && launcherText.includes("window.location.href = target")
    && launcherText.includes("__memory_atlas_runtime_state")
    && launcherText.includes("__memory_atlas_release")
    && launcherText.includes("request_shutdown");
  assertCondition(
    singleWindowContract,
    "stage8_1_launcher_single_window_contract",
    "Launcher opens one status page, redirects it to the ready local app, and exposes heartbeat/release shutdown endpoints",
    "Launcher single-window or self-release contract is missing",
  );
  assertCondition(
    launcherText.includes("MEMORY_ATLAS_PID_FILE")
      && launcherText.includes("path.unlink()")
      && launcherText.includes('path.read_text(encoding="utf-8").strip() == str(os.getpid())'),
    "stage8_1_launcher_pid_cleanup_contract",
    "Launcher server removes its managed pid file on normal release, idle, or TTL shutdown",
    "Launcher managed pid cleanup contract is missing",
  );

  const plistBytes = fs.readFileSync(infoPlist);
  assertCondition(
    plistBytes.includes("Memory Atlas") && plistBytes.includes("memory-atlas-launcher") && plistBytes.includes("Application Support") && plistBytes.includes("脱敏快照"),
    "stage8_1_plist_contract",
    "App plist identifies Memory Atlas, the launcher executable, and the Application Support redacted snapshot purpose",
    "App plist does not expose the required Memory Atlas launcher contract",
  );
}

function validateStage81Docs() {
  const reviewSource = fs.readFileSync(stage81Review, "utf8");
  const modelSource = fs.readFileSync(modelParameters, "utf8");
  const deliverySource = fs.readFileSync(deliveryRecord, "utf8");
  const changelogSource = fs.readFileSync(changelog, "utf8");
  assertCondition(
    hasAll(reviewSource, [
      "Stage 8.1 is review-passed",
      "8.1.1 local build",
      "8.1.2 launcher check",
      "8.1.3 default route check",
      "No Cloudflare deployment or Access policy change was performed",
      "No raw/private/cookie/session/secret fields were introduced",
      "No direct frontend writeback was added",
      "Stage 8.2: Release Safety",
    ]),
    "stage8_1_review_doc_current",
    "Stage 8.1 review records phase scope, pass status, boundaries, and next Stage 8.2 gate",
    "Stage 8.1 review doc is missing required scope, status, or boundary markers",
  );
  assertCondition(
    hasAll(modelSource, [
      "stage_8_1_local_app_packaging_passed",
      "validate:stage8-local-app",
      "MEMORY_ATLAS_PID_FILE",
      "data-view=\"home\"",
      "Stage 8.2 Release Safety",
    ]),
    "stage8_1_model_parameters_current",
    "Model parameters record Stage 8.1 local app packaging thresholds and next gate",
    "Model parameters do not record Stage 8.1 local app packaging status",
  );
  assertCondition(
    hasAll(deliverySource, [
      "完成 Memory Atlas v1.1.5 Stage 8.1 Local App Packaging",
      "validate:stage8-local-app",
      "Stage 8.2 Release Safety",
    ]),
    "stage8_1_delivery_record_current",
    "Delivery record marks Stage 8.1 complete and moves the high-priority gate to Stage 8.2",
    "Delivery record does not mark Stage 8.1 complete or Stage 8.2 next",
  );
  assertCondition(
    hasAll(changelogSource, [
      "Memory Atlas v1.1.5 Stage 8.1 Local App Packaging",
      "validate:stage8-local-app",
      "No Stage 8.2 release safety work",
    ]),
    "stage8_1_changelog_current",
    "Changelog records Stage 8.1 local app packaging and preserves non-goal boundaries",
    "Changelog does not record Stage 8.1 local app packaging status",
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

async function validateDefaultRoute() {
  const { chromium } = requirePlaywright();
  assertCondition(Boolean(browserExecutable), "stage8_1_browser_available", `Using Chromium-compatible browser: ${browserExecutable}`, "No Chromium-compatible browser executable found");
  const browser = await chromium.launch({ executablePath: browserExecutable, headless: true });
  try {
    const page = await browser.newPage({ viewport: { width: 1366, height: 900 }, deviceScaleFactor: 1 });
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
    await page.waitForSelector(".home-overview-view", { timeout: 20000 });
    const route = await page.evaluate(() => {
      const activeNav = document.querySelector(".nav-item.active")?.textContent?.trim() || "";
      const title = document.querySelector(".topbar h1")?.textContent?.trim() || "";
      const contentView = document.querySelector(".content-grid")?.getAttribute("data-view") || "";
      const hasHome = Boolean(document.querySelector(".home-overview-view"));
      const hasPrimaryBand = Boolean(document.querySelector('[aria-label="当前认知状态"]'));
      return { activeNav, title, contentView, hasHome, hasPrimaryBand };
    });
    const screenshotPath = path.join(outputDir, "stage8-local-app-default-home.png");
    await page.screenshot({ path: screenshotPath, fullPage: false });
    const screenshotBytes = fs.statSync(screenshotPath).size;
    assertCondition(
      route.activeNav.includes("记忆总览")
        && route.title === "记忆总览"
        && route.contentView === "home"
        && route.hasHome
        && route.hasPrimaryBand
        && screenshotBytes > 20_000,
      "stage8_1_default_route_memory_overview",
      `Default production preview opens 记忆总览 with screenshot ${screenshotBytes} bytes`,
      "Default production preview did not open the Memory Overview route",
      { route, screenshotPath, screenshotBytes },
    );
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
      "stage8_1_default_route_console_clean",
      "Default route opened without actionable browser console errors or failed responses",
      "Default route produced browser console errors or failed responses",
      { consoleErrors, failedResponses, actionableConsoleErrors, actionableFailedResponses },
    );
    await page.close();
  } finally {
    await browser.close();
  }
}

(async () => {
  let preview = null;
  try {
    fs.mkdirSync(outputDir, { recursive: true });
    buildFrontend();
    validateTemporaryAppBundle();
    validateStage81Docs();
    preview = startPreviewServer();
    await waitForHttp(`${targetUrl}/memory_atlas.json`);
    await validateDefaultRoute();
  } catch (error) {
    checks.push({
      name: "stage8_1_local_app_packaging",
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
      if (!process.exitCode) pass("stage8_1_preview_cleanup", `Port ${port} released after production preview shutdown`);
    } catch (error) {
      checks.push({ name: "stage8_1_preview_cleanup", status: "FAIL", evidence: error.message });
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
