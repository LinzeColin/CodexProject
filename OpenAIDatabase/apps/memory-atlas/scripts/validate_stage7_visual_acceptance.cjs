#!/usr/bin/env node
"use strict";

const fs = require("node:fs");
const http = require("node:http");
const os = require("node:os");
const path = require("node:path");
const { spawn } = require("node:child_process");

const appRoot = path.resolve(__dirname, "..");
const port = Number(process.env.MEMORY_ATLAS_STAGE7_PORT || 4177);
const targetUrl = `http://127.0.0.1:${port}`;
const outputDir = process.env.MEMORY_ATLAS_VISUAL_AUDIT_DIR || fs.mkdtempSync(path.join(os.tmpdir(), "memory-atlas-stage7-visual-"));
const browserExecutable = process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH || findChromiumExecutable();

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

function assertScreenshotFile(filePath, label) {
  const stat = fs.statSync(filePath);
  assertCondition(stat.size > 20_000, `${label} screenshot is unexpectedly small`, { filePath, size: stat.size });
  return { path: filePath, bytes: stat.size };
}

function isIgnoredRuntimeProbe(response) {
  try {
    const pathname = new URL(response.url).pathname;
    return response.status === 404 && ["/__memory_atlas_heartbeat", "/__memory_atlas_release"].includes(pathname);
  } catch {
    return false;
  }
}

async function validateGalaxyVisualAcceptance(page) {
  await page.getByRole("button", { name: /银河星云/ }).click({ timeout: 5000 });
  await page.waitForSelector(".galaxy-webgl-canvas", { timeout: 25000 });
  await page.waitForFunction(() => {
    const signal = window.__memoryAtlasGalaxySignal?.();
    return Boolean(signal && signal.lit > 100 && signal.max > 42 && signal.width > 100 && signal.height > 100);
  }, null, { timeout: 25000 });
  await page.waitForTimeout(350);
  const signal = await page.evaluate(() => window.__memoryAtlasGalaxySignal?.() ?? null);
  assertCondition(signal, "Galaxy pixel signal is missing");
  assertCondition(signal.rendererMode === "memory-starfield", "Galaxy is not using memory-starfield renderer", signal);
  assertCondition(signal.fallbackMode !== "legacy", "Galaxy fell back to legacy mode during visual acceptance", signal);
  assertCondition(signal.lit > 100 && signal.alpha > 100 && signal.max > 42, "Galaxy canvas pixel signal is blank or too dark", signal);
  assertCondition(signal.points > 0 && signal.triangles > 0, "Galaxy WebGL render statistics are missing points or triangles", signal);
  assertCondition(signal.terrainFeatureCount > 0, "Galaxy terrain feature count is missing", signal);
  assertCondition(signal.flowFieldStrength > 0, "Galaxy flow field signal is missing", signal);

  const screenshotPath = path.join(outputDir, "stage7-galaxy-desktop.png");
  await page.screenshot({ path: screenshotPath, fullPage: false });
  return {
    screenshot: assertScreenshotFile(screenshotPath, "Galaxy"),
    signal,
  };
}

async function validateMemoryRiverVisualAcceptance(page) {
  await page.getByRole("button", { name: /时间轴/ }).click({ timeout: 5000 });
  await page.waitForSelector(".timeline-map", { timeout: 15000 });
  const renderer = await page.locator(".timeline-map").getAttribute("data-timeline-renderer");
  if (renderer !== "memory-river") {
    await page.getByRole("button", { name: /^Memory River$/ }).click({ timeout: 5000 });
  }
  await page.waitForSelector(".memory-river-canvas", { timeout: 15000 });
  await page.waitForFunction(() => {
    const canvas = document.querySelector(".memory-river-canvas");
    return Boolean(
      canvas
        && document.querySelectorAll(".memory-river-lane-flow").length >= 3
        && document.querySelectorAll(".memory-river-evidence-layer").length >= 3
        && document.querySelectorAll(".memory-river-marker").length >= 3,
    );
  }, null, { timeout: 10000 });

  const river = await page.evaluate(() => {
    const canvas = document.querySelector(".memory-river-canvas");
    const box = canvas?.getBoundingClientRect();
    const evidenceLayers = Array.from(document.querySelectorAll(".memory-river-evidence-layer"))
      .map((layer) => layer.getAttribute("data-evidence-layer"))
      .filter(Boolean);
    const levelLabels = Array.from(document.querySelectorAll(".memory-river-level-label")).map((node) => node.textContent?.trim());
    return {
      renderer: document.querySelector(".timeline-map")?.getAttribute("data-timeline-renderer") || "",
      canvasBox: box ? { width: Math.round(box.width), height: Math.round(box.height) } : null,
      utcScale: canvas?.getAttribute("data-utc-time-scale") || "",
      evidenceContract: canvas?.getAttribute("data-evidence-layers") || "",
      laneFlows: document.querySelectorAll(".memory-river-lane-flow").length,
      laneLabels: document.querySelectorAll(".memory-river-lane-label").length,
      levelLabels,
      evidenceLayers,
      evidenceSegments: document.querySelectorAll("[data-evidence-segment]").length,
      blackHoleMarkers: document.querySelectorAll(".memory-river-marker.black-hole").length,
      protoStarMarkers: document.querySelectorAll(".memory-river-marker.proto-star").length,
      eventMarkers: document.querySelectorAll(".memory-river-marker.memory-event").length,
      totalMarkers: document.querySelectorAll(".memory-river-marker").length,
      densityBands: document.querySelectorAll(".timeline-density-band").length,
    };
  });
  assertCondition(river.renderer === "memory-river", "Timeline did not use Memory River renderer", river);
  assertCondition(river.canvasBox && river.canvasBox.width > 700 && river.canvasBox.height > 300, "Memory River canvas is too small or missing", river);
  assertCondition(river.utcScale === "true", "Memory River did not expose UTC scale contract", river);
  assertCondition(["Macro", "Meso", "Micro"].every((label) => river.levelLabels.includes(label)), "Memory River Macro/Meso/Micro labels are missing", river);
  assertCondition(river.laneFlows >= 3 && river.laneLabels >= 3, "Memory River lane visual structure is too sparse", river);
  assertCondition(["black-hole-lifecycle", "proto-star-lifecycle", "stale-deprecated"].every((kind) => river.evidenceLayers.includes(kind)), "Memory River evidence layers are missing", river);
  assertCondition(river.evidenceSegments > 0, "Memory River evidence layer segments are missing", river);
  assertCondition(river.totalMarkers >= 3 && river.protoStarMarkers > 0, "Memory River marker quality gate is missing opportunity markers", river);
  assertCondition(river.evidenceContract.includes("black-hole-lifecycle"), "Memory River black-hole lifecycle band contract is missing", river);
  assertCondition(river.densityBands >= 24, "Memory River density band context is too sparse", river);

  const screenshotPath = path.join(outputDir, "stage7-memory-river-desktop.png");
  await page.screenshot({ path: screenshotPath, fullPage: false });
  return {
    screenshot: assertScreenshotFile(screenshotPath, "Memory River"),
    river,
  };
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

    const galaxy = await validateGalaxyVisualAcceptance(page);
    const memoryRiver = await validateMemoryRiverVisualAcceptance(page);
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
    return { galaxy, memoryRiver, consoleErrors, failedResponses, actionableConsoleErrors, actionableFailedResponses };
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
    console.log(JSON.stringify({
      status: "PASS",
      stage: "7.1",
      targetUrl,
      outputDir,
      checks: [
        "galaxy canvas non-empty pixel signal",
        "galaxy starfield quality screenshot gate",
        "memory river quality screenshot gate",
        "preview server released after validation",
      ],
      results,
    }, null, 2));
  } catch (error) {
    if (preview) await stopPreviewServer(preview.server).catch(() => undefined);
    console.error(JSON.stringify({
      status: "FAIL",
      stage: "7.1",
      message: error.message,
      details: error.details || null,
      targetUrl,
      outputDir,
      serverLogs: preview?.logs?.join("").slice(-4000) || "",
    }, null, 2));
    process.exitCode = 1;
  }
})();
