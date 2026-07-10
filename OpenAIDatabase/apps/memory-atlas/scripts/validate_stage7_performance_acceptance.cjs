#!/usr/bin/env node
"use strict";

const fs = require("node:fs");
const http = require("node:http");
const os = require("node:os");
const path = require("node:path");
const { spawn } = require("node:child_process");

const appRoot = path.resolve(__dirname, "..");
const port = Number(process.env.MEMORY_ATLAS_STAGE7_PERFORMANCE_PORT || 4177);
const targetUrl = `http://127.0.0.1:${port}`;
const outputDir = process.env.MEMORY_ATLAS_PERFORMANCE_AUDIT_DIR
  || fs.mkdtempSync(path.join(os.tmpdir(), "memory-atlas-stage7-performance-"));
const browserExecutable = process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH || findChromiumExecutable();

const ACCEPTANCE = {
  highMinFps: 45,
  midMinFps: 30,
  minimumPixelSignal: 100,
};

function assertCondition(condition, message, details = {}) {
  if (!condition) {
    const error = new Error(message);
    error.details = details;
    throw error;
  }
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
    if (candidate) {
      return require(path.join(pnpmRoot, candidate, "node_modules/playwright"));
    }
  } catch {}
  throw new Error("Playwright is not resolvable from project dependencies or Codex bundled runtime");
}

function httpGet(url, timeoutMs = 2000) {
  return new Promise((resolve, reject) => {
    const request = http.get(url, (response) => {
      response.resume();
      response.on("end", () => resolve(response.statusCode || 0));
    });
    request.setTimeout(timeoutMs, () => {
      request.destroy(new Error(`timeout waiting for ${url}`));
    });
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
  assertCondition(fs.existsSync(viteCli), "Vite CLI is missing from app node_modules", { viteCli });
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

function isIgnoredRuntimeProbe(response) {
  try {
    const pathname = new URL(response.url).pathname;
    return response.status === 404 && ["/__memory_atlas_heartbeat", "/__memory_atlas_release"].includes(pathname);
  } catch {
    return false;
  }
}

async function waitForGalaxy(page) {
  await page.getByRole("button", { name: /银河星云/ }).click({ timeout: 5000 });
  await page.waitForSelector(".galaxy-webgl-canvas", { timeout: 25000 });
  await page.waitForFunction(() => {
    const signal = window.__memoryAtlasGalaxySignal?.();
    return Boolean(signal && signal.rendererMode === "memory-starfield" && signal.renderTicks > 5 && signal.lit > 100);
  }, null, { timeout: 25000 });
  await page.getByRole("button", { name: /analysis mode/i }).click({ timeout: 5000 });
  await page.waitForSelector(".galaxy-performance-overlay[data-performance-overlay='true']", { timeout: 10000 });
}

async function selectQuality(page, quality) {
  await page.getByRole("button", { name: new RegExp(`^${quality} quality$`, "i") }).click({ timeout: 5000 });
  await page.waitForFunction((expectedQuality) => {
    const signal = window.__memoryAtlasGalaxySignal?.();
    return Boolean(signal && signal.quality === expectedQuality && signal.renderTicks > 8);
  }, quality, { timeout: 15000 });
}

async function waitForQualityMetric(page, quality, minFps) {
  await page.waitForFunction((expectedQuality) => {
    const signal = window.__memoryAtlasGalaxySignal?.();
    return Boolean(
      signal
        && signal.quality === expectedQuality
        && signal.fps > 0
        && signal.sampleSeconds >= 0.8
        && signal.lit > 100
        && signal.points > 0,
    );
  }, quality, { timeout: 15000 });
  await page.waitForTimeout(1400);
  const signal = await page.evaluate(() => window.__memoryAtlasGalaxySignal?.() ?? null);
  assertCondition(signal, `${quality} quality signal is missing`);
  assertCondition(signal.quality === quality, `${quality} quality signal did not stabilize`, signal);
  assertCondition(signal.fps >= minFps, `${quality} quality FPS is below acceptance threshold`, { signal, minFps });
  assertCondition(signal.lit > ACCEPTANCE.minimumPixelSignal && signal.alpha > ACCEPTANCE.minimumPixelSignal, `${quality} quality rendered blank`, signal);
  assertCondition(signal.points > 0 && signal.triangles > 0, `${quality} quality render stats are missing`, signal);
  return signal;
}

async function validateInitialAdaptiveOverlay(page) {
  await page.waitForFunction(() => {
    const signal = window.__memoryAtlasGalaxySignal?.();
    return Boolean(
      signal
        && signal.adaptiveQualityEnabled === true
        && signal.quality === "mid"
        && signal.fps > 0
        && signal.sampleSeconds >= 0.8,
    );
  }, null, { timeout: 15000 });
  const overlay = await page.evaluate(() => {
    const signal = window.__memoryAtlasGalaxySignal?.();
    const overlay = document.querySelector(".galaxy-performance-overlay");
    return {
      signal,
      overlayVisible: Boolean(overlay),
      overlayText: overlay?.textContent || "",
      dataFps: document.querySelector(".galaxy-scene")?.getAttribute("data-galaxy-fps") || "",
      dataAdaptiveQuality: document.querySelector(".galaxy-scene")?.getAttribute("data-adaptive-quality") || "",
    };
  });
  assertCondition(overlay.signal?.adaptiveQualityEnabled === true, "Adaptive quality should be enabled by default", overlay);
  assertCondition(overlay.signal?.quality === "mid", "Initial adaptive quality should start from mid tier", overlay);
  assertCondition(overlay.signal?.fps > 0 && overlay.signal?.sampleSeconds >= 0.8, "FPS overlay did not expose a sampled metric", overlay);
  assertCondition(overlay.signal?.minFps === ACCEPTANCE.midMinFps, "Initial mid-tier FPS threshold is missing", overlay);
  assertCondition(overlay.overlayVisible && overlay.overlayText.includes("FPS"), "FPS overlay is missing in Analysis mode", overlay);
  assertCondition(overlay.dataAdaptiveQuality === "enabled", "Adaptive quality data contract is missing", overlay);
  return overlay;
}

async function validateLowQualityFallback(page) {
  await selectQuality(page, "low");
  await page.waitForTimeout(1400);
  const signal = await page.evaluate(() => window.__memoryAtlasGalaxySignal?.() ?? null);
  assertCondition(signal, "low quality signal is missing");
  assertCondition(signal.quality === "low", "low quality did not activate", signal);
  assertCondition(signal.fallbackMode === "low-quality", "low quality fallback contract is missing", signal);
  assertCondition(signal.lit > ACCEPTANCE.minimumPixelSignal && signal.alpha > ACCEPTANCE.minimumPixelSignal, "low quality rendered blank", signal);
  assertCondition(signal.points > 0 && signal.triangles > 0, "low quality render stats are missing", signal);
  return signal;
}

async function validateAutoCanResume(page) {
  await page.getByRole("button", { name: /enable adaptive quality/i }).click({ timeout: 5000 });
  await page.waitForFunction(() => {
    const signal = window.__memoryAtlasGalaxySignal?.();
    return Boolean(signal && signal.adaptiveQualityEnabled === true && signal.quality === "mid");
  }, null, { timeout: 10000 });
  const signal = await page.evaluate(() => window.__memoryAtlasGalaxySignal?.() ?? null);
  assertCondition(signal?.adaptiveQualityEnabled === true, "Adaptive quality did not resume after Auto toggle", signal || {});
  assertCondition(signal?.quality === "mid", "Adaptive quality did not upgrade low tier after Auto resumed", signal || {});
  return signal;
}

async function validateCleanupHooks(page) {
  await page.locator('[data-nav-view="timeline"]').click({ timeout: 5000 });
  await page.waitForFunction(() => {
    const lifecycle = window.__memoryAtlasGalaxyLifecycle;
    return Boolean(
      lifecycle
        && lifecycle.disposedAt
        && lifecycle.activeRaf === false
        && lifecycle.rafCancelled === true
        && lifecycle.rendererDisposed === true
        && lifecycle.workersClosed === true
        && lifecycle.audioContextClosed === true
        && !window.__memoryAtlasGalaxySignal,
    );
  }, null, { timeout: 10000 });
  const lifecycle = await page.evaluate(() => window.__memoryAtlasGalaxyLifecycle ?? null);
  assertCondition(lifecycle?.webglContextLost === true, "WebGL context loss hook did not complete", lifecycle || {});
  const disposedTick = lifecycle.renderTicksAtDispose;
  await page.waitForTimeout(700);
  const afterWait = await page.evaluate(() => ({
    lifecycle: window.__memoryAtlasGalaxyLifecycle ?? null,
    signalPresent: Boolean(window.__memoryAtlasGalaxySignal),
  }));
  assertCondition(afterWait.signalPresent === false, "Galaxy signal remained after unmount", afterWait);
  assertCondition(afterWait.lifecycle?.renderTicksAtDispose === disposedTick, "Galaxy RAF tick changed after dispose", afterWait);
  return lifecycle;
}

async function runBrowserValidation() {
  const { chromium } = requirePlaywright();
  assertCondition(Boolean(browserExecutable), "No Chromium-compatible browser executable found");
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
      if (response.status() >= 400) {
        failedResponses.push({ status: response.status(), url: response.url() });
      }
    });

    await page.goto(targetUrl, { waitUntil: "domcontentloaded", timeout: 20000 });
    await page.waitForLoadState("networkidle", { timeout: 10000 }).catch(() => undefined);
    await waitForGalaxy(page);
    const adaptiveOverlay = await validateInitialAdaptiveOverlay(page);
    await selectQuality(page, "high");
    const high = await waitForQualityMetric(page, "high", ACCEPTANCE.highMinFps);
    await selectQuality(page, "mid");
    const mid = await waitForQualityMetric(page, "mid", ACCEPTANCE.midMinFps);
    const low = await validateLowQualityFallback(page);
    const resumedAuto = await validateAutoCanResume(page);
    const cleanup = await validateCleanupHooks(page);

    const actionableFailedResponses = failedResponses.filter((response) => !isIgnoredRuntimeProbe(response));
    const actionableConsoleErrors = consoleErrors.filter((message) => {
      return !(message.startsWith("Failed to load resource:") && actionableFailedResponses.length === 0);
    });
    assertCondition(actionableConsoleErrors.length === 0 && actionableFailedResponses.length === 0, "Browser console/page errors occurred", {
      consoleErrors,
      failedResponses,
      actionableConsoleErrors,
      actionableFailedResponses,
    });
    await page.close();
    return {
      thresholds: ACCEPTANCE,
      adaptiveOverlay,
      high,
      mid,
      low,
      resumedAuto,
      cleanup,
      consoleErrors,
      failedResponses,
      actionableConsoleErrors,
      actionableFailedResponses,
    };
  } finally {
    await browser.close();
  }
}

(async () => {
  let preview = null;
  try {
    fs.mkdirSync(outputDir, { recursive: true });
    preview = startPreviewServer();
    await waitForHttp(targetUrl);
    const results = await runBrowserValidation();
    await stopPreviewServer(preview.server);
    await assertPortClosed();
    const report = {
      status: "PASS",
      stage: "7.2",
      targetUrl,
      outputDir,
      checks: [
        "FPS overlay exposes sampled metrics",
        "high quality FPS >= 45",
        "mid quality FPS >= 30",
        "low quality remains non-blank",
        "adaptive quality resumes and upgrades low tier after manual rollback",
        "Galaxy unmount releases RAF and WebGL lifecycle hooks",
        "preview server released after validation",
      ],
      results,
    };
    fs.writeFileSync(path.join(outputDir, "stage7-performance-report.json"), `${JSON.stringify(report, null, 2)}\n`);
    console.log(JSON.stringify(report, null, 2));
  } catch (error) {
    if (preview) await stopPreviewServer(preview.server).catch(() => undefined);
    console.error(JSON.stringify({
      status: "FAIL",
      stage: "7.2",
      message: error.message,
      details: error.details || null,
      targetUrl,
      outputDir,
      serverLogs: preview?.logs?.join("").slice(-4000) || "",
    }, null, 2));
    process.exitCode = 1;
  }
})();
