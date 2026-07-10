#!/usr/bin/env node
"use strict";

const fs = require("node:fs");
const http = require("node:http");
const os = require("node:os");
const path = require("node:path");
const { spawn, spawnSync } = require("node:child_process");

const appRoot = path.resolve(__dirname, "..");
const databaseRoot = path.resolve(appRoot, "../..");
const port = Number(process.env.MEMORY_ATLAS_R6_VISUAL_PORT || 4187);
const targetUrl = `http://127.0.0.1:${port}`;
const outputDir = process.env.MEMORY_ATLAS_R6_VISUAL_AUDIT_DIR
  ? path.resolve(databaseRoot, process.env.MEMORY_ATLAS_R6_VISUAL_AUDIT_DIR)
  : fs.mkdtempSync(path.join(os.tmpdir(), "memory-atlas-r6-visual-audit-"));
const browserExecutable = process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH || findChromiumExecutable();
const visualIds = [
  "cluster_tree",
  "bubble_map",
  "topic_cluster_explorer",
  "task_treemap",
  "automation_vs_augmentation",
  "roi_scatter",
  "opportunity_radar",
  "agent_decision_sankey",
  "friction_heatmap",
  "latent_radar",
  "evidence_timeline",
  "formula_explorer",
];
const viewports = [
  { name: "desktop-low-height", width: 1470, height: 661 },
  { name: "desktop-standard", width: 1440, height: 900 },
  { name: "mobile", width: 390, height: 844 },
];

function assertCondition(condition, message, details = {}) {
  if (!condition) {
    const error = new Error(message);
    error.details = details;
    throw error;
  }
}

function findChromiumExecutable() {
  return [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
  ].find((candidate) => fs.existsSync(candidate));
}

function requirePlaywright() {
  try {
    return require("playwright");
  } catch {}
  const pnpmRoot = path.join(
    os.homedir(),
    ".cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/.pnpm",
  );
  try {
    const candidate = fs.readdirSync(pnpmRoot)
      .filter((entry) => entry.startsWith("playwright@"))
      .sort()
      .at(-1);
    if (candidate) return require(path.join(pnpmRoot, candidate, "node_modules/playwright"));
  } catch {}
  throw new Error("Playwright is not resolvable from project dependencies or Codex bundled runtime");
}

function buildFrontend() {
  const result = spawnSync("npm", ["run", "build"], {
    cwd: appRoot,
    env: { ...process.env },
    encoding: "utf8",
  });
  assertCondition(result.status === 0, "Current frontend build failed before R6 browser validation", {
    stdoutTail: String(result.stdout || "").slice(-3000),
    stderrTail: String(result.stderr || "").slice(-3000),
  });
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

async function waitForHttp(url, server, timeoutMs = 20000) {
  const started = Date.now();
  let lastError = null;
  while (Date.now() - started < timeoutMs) {
    if (server.child.exitCode !== null) {
      throw new Error(`Vite preview exited before readiness with code ${server.child.exitCode}: ${server.logs.join("").slice(-3000)}`);
    }
    try {
      const status = await httpGet(url, 1200);
      if (status >= 200 && status < 500) return;
    } catch (error) {
      lastError = error;
    }
    await new Promise((resolve) => setTimeout(resolve, 200));
  }
  throw new Error(`Vite preview did not become ready at ${url}: ${lastError?.message || "unknown"}`);
}

function startPreview() {
  const viteCli = path.join(appRoot, "node_modules/vite/bin/vite.js");
  assertCondition(fs.existsSync(viteCli), "Vite CLI is missing from app node_modules", { viteCli });
  const child = spawn(process.execPath, [
    viteCli,
    "preview",
    "--host",
    "127.0.0.1",
    "--port",
    String(port),
    "--strictPort",
  ], { cwd: appRoot, env: { ...process.env }, stdio: ["ignore", "pipe", "pipe"] });
  const logs = [];
  child.stdout.on("data", (chunk) => logs.push(chunk.toString()));
  child.stderr.on("data", (chunk) => logs.push(chunk.toString()));
  return { child, logs };
}

async function stopPreview(handle) {
  if (!handle || handle.child.exitCode !== null) return;
  handle.child.kill("SIGTERM");
  await Promise.race([
    new Promise((resolve) => handle.child.once("exit", resolve)),
    new Promise((resolve) => setTimeout(resolve, 2500)),
  ]);
  if (handle.child.exitCode === null) {
    handle.child.kill("SIGKILL");
    await new Promise((resolve) => handle.child.once("exit", resolve));
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
    return response.status === 404
      && ["/__memory_atlas_heartbeat", "/__memory_atlas_release"].includes(new URL(response.url).pathname);
  } catch {
    return false;
  }
}

async function assertLayout(page) {
  const layout = await page.locator("[data-r6-visual-workbench]").evaluate((workbench) => {
    const cards = Array.from(workbench.querySelectorAll("[data-r6-visual-id]"));
    const rect = (element) => {
      const box = element.getBoundingClientRect();
      return { top: box.top, right: box.right, bottom: box.bottom, left: box.left, width: box.width, height: box.height };
    };
    const cardRects = cards.map((card) => ({ id: card.getAttribute("data-r6-visual-id"), ...rect(card) }));
    const overlaps = [];
    for (let left = 0; left < cardRects.length; left += 1) {
      for (let right = left + 1; right < cardRects.length; right += 1) {
        const first = cardRects[left];
        const second = cardRects[right];
        const overlapWidth = Math.min(first.right, second.right) - Math.max(first.left, second.left);
        const overlapHeight = Math.min(first.bottom, second.bottom) - Math.max(first.top, second.top);
        if (overlapWidth > 1 && overlapHeight > 1) overlaps.push({ first: first.id, second: second.id, overlapWidth, overlapHeight });
      }
    }
    const clipped = cards
      .filter((card) => card.scrollWidth > card.clientWidth + 1)
      .map((card) => ({ id: card.getAttribute("data-r6-visual-id"), clientWidth: card.clientWidth, scrollWidth: card.scrollWidth }));
    return {
      cardRects,
      clipped,
      documentClientWidth: document.documentElement.clientWidth,
      documentScrollWidth: document.documentElement.scrollWidth,
      overlaps,
      workbenchClientWidth: workbench.clientWidth,
      workbenchScrollWidth: workbench.scrollWidth,
    };
  });
  assertCondition(layout.documentScrollWidth <= layout.documentClientWidth + 1, "R6 page has horizontal overflow", layout);
  assertCondition(layout.workbenchScrollWidth <= layout.workbenchClientWidth + 1, "R6 workbench has horizontal overflow", layout);
  assertCondition(layout.clipped.length === 0, "R6 visual card content is horizontally clipped", layout);
  assertCondition(layout.overlaps.length === 0, "R6 visual cards overlap", layout);
  assertCondition(layout.cardRects.every((item) => item.width > 120 && item.height > 80), "R6 visual cards collapsed", layout);
  return layout;
}

async function assertInventory(page) {
  const inventory = await page.locator("[data-r6-visual-id]").evaluateAll((cards) => cards.map((card) => ({
    id: card.getAttribute("data-r6-visual-id"),
    title: card.querySelector("h3")?.textContent?.trim() || "",
    question: card.querySelector("[data-r6-card-question]")?.textContent?.trim() || "",
    action: card.querySelector("[data-r6-card-action]")?.textContent?.trim() || "",
    datumCount: card.querySelectorAll("[data-r6-visual-datum]").length,
  })));
  assertCondition(JSON.stringify(inventory.map((item) => item.id)) === JSON.stringify(visualIds), "R6 P0 visual inventory is not the exact approved twelve", { inventory });
  assertCondition(inventory.every((item) => item.title && item.question && item.action && item.datumCount >= 1), "R6 visual copy or keyboard datum is incomplete", { inventory });
  return inventory;
}

async function assertEvidenceInteractions(page) {
  const selected = [];
  for (const id of visualIds) {
    const datum = page.locator(`[data-r6-visual-id="${id}"] [data-r6-visual-datum]`).first();
    await datum.scrollIntoViewIfNeeded();
    await datum.click();
    await page.waitForFunction((visualId) => {
      return document.querySelector("[data-r6-visual-evidence]")?.getAttribute("data-r6-selected-visual") === visualId;
    }, id);
    const evidence = await page.locator("[data-r6-visual-evidence]").evaluate((element) => ({
      action: element.querySelector("[data-r6-action-value]")?.textContent?.trim() || "",
      evidenceCount: element.querySelectorAll("[data-r6-evidence-ref]").length,
      next: element.querySelector("[data-r6-next-action]")?.textContent?.trim() || "",
      question: element.querySelector("[data-r6-human-question]")?.textContent?.trim() || "",
      selected: element.getAttribute("data-r6-selected-visual"),
    }));
    assertCondition(evidence.selected === id && evidence.question && evidence.action && evidence.next, "R6 visual did not update the evidence workspace", { id, evidence });
    assertCondition(evidence.evidenceCount >= 1, "R6 visual evidence workspace is missing source evidence", { id, evidence });
    selected.push(id);
  }
  return selected;
}

async function assertFourAxisFilters(page) {
  const reset = page.locator("[data-r6-visual-filter-reset]");
  const signature = page.locator("[data-r6-visual-filter-signature]");
  const baseline = await signature.getAttribute("data-r6-signature");
  assertCondition(Boolean(baseline), "R6 baseline filter signature is missing");
  const results = {};
  for (const axis of ["source", "time", "project", "task"]) {
    await reset.click();
    await page.waitForFunction((expected) => document.querySelector("[data-r6-visual-filter-signature]")?.getAttribute("data-r6-signature") === expected, baseline);
    const select = page.locator(`[data-r6-visual-filter="${axis}"]`);
    const options = await select.locator("option").evaluateAll((items) => items.map((item) => item.value));
    const choice = options.find((value) => value && value !== "all");
    assertCondition(Boolean(choice), `R6 ${axis} filter has no concrete option`, { options });
    await select.selectOption(choice);
    await page.waitForFunction((expected) => document.querySelector("[data-r6-visual-filter-signature]")?.getAttribute("data-r6-signature") !== expected, baseline);
    results[axis] = {
      choice,
      count: await page.locator("[data-r6-visual-event-count]").getAttribute("data-r6-count"),
      signature: await signature.getAttribute("data-r6-signature"),
    };
  }
  await reset.click();
  await page.waitForFunction((expected) => document.querySelector("[data-r6-visual-filter-signature]")?.getAttribute("data-r6-signature") === expected, baseline);
  return { baseline, results };
}

async function assertOpportunityDetail(page) {
  const opportunity = page.locator("[data-r6-opportunity-id]").first();
  assertCondition(await opportunity.count() === 1, "R6 opportunity list is empty");
  await opportunity.click();
  const detail = page.locator("[data-r6-opportunity-detail]");
  await detail.waitFor({ state: "visible" });
  const result = await detail.evaluate((element) => ({
    evidence: element.querySelectorAll("[data-r6-opportunity-evidence]").length,
    halfLife: element.querySelector("[data-r6-opportunity-half-life]")?.textContent?.trim() || "",
    next: element.querySelector("[data-r6-opportunity-next-step]")?.textContent?.trim() || "",
    reason: element.querySelector("[data-r6-opportunity-defer-reason]")?.textContent?.trim() || "",
    boundary: element.querySelector("[data-r6-opportunity-not-pressure]")?.textContent?.trim() || "",
  }));
  assertCondition(result.evidence >= 1 && result.halfLife && result.next && result.reason && result.boundary, "R6 opportunity drill-down is incomplete", result);
  return result;
}

async function assertFormulaInteraction(page, writeRequests) {
  const score = page.locator("[data-r6-formula-score]");
  const baseline = await score.getAttribute("data-r6-score");
  const slider = page.locator('[data-r6-formula-weight="time_saved_weight"]');
  const maximum = await slider.getAttribute("max");
  assertCondition(Boolean(baseline) && Boolean(maximum), "R6 Formula baseline or bounds are missing", { baseline, maximum });
  await slider.evaluate((element, value) => {
    element.value = value;
    element.dispatchEvent(new Event("input", { bubbles: true }));
    element.dispatchEvent(new Event("change", { bubbles: true }));
  }, maximum);
  await page.waitForFunction((expected) => document.querySelector("[data-r6-formula-score]")?.getAttribute("data-r6-score") !== expected, baseline);
  const changed = await score.getAttribute("data-r6-score");
  await page.locator("[data-r6-formula-reset]").click();
  await page.waitForFunction((expected) => document.querySelector("[data-r6-formula-score]")?.getAttribute("data-r6-score") === expected, baseline);
  const safety = await page.locator("[data-r6-formula-safety]").innerText();
  assertCondition(/proxy/i.test(safety) && /不是.*(收入|财务建议)/.test(safety), "R6 Formula safety copy is incomplete", { safety });
  assertCondition(writeRequests.length === 0, "R6 Formula interaction issued a write request", { writeRequests });
  return { baseline, changed, reset: await score.getAttribute("data-r6-score"), safety };
}

async function validateViewport(browser, viewport) {
  const page = await browser.newPage({ viewport: { width: viewport.width, height: viewport.height }, deviceScaleFactor: 1 });
  const consoleErrors = [];
  const failedResponses = [];
  const writeRequests = [];
  page.on("console", (message) => { if (message.type() === "error") consoleErrors.push(message.text()); });
  page.on("pageerror", (error) => consoleErrors.push(error.message));
  page.on("response", (response) => { if (response.status() >= 400) failedResponses.push({ status: response.status(), url: response.url() }); });
  page.on("request", (request) => { if (!["GET", "HEAD", "OPTIONS"].includes(request.method())) writeRequests.push({ method: request.method(), url: request.url() }); });
  try {
    await page.goto(targetUrl, { waitUntil: "domcontentloaded", timeout: 30000 });
    const workbench = page.locator('[data-r6-visual-workbench="memory_atlas_visual_workflows.v1_2_r6"]');
    await workbench.waitFor({ state: "visible", timeout: 20000 });
    await workbench.scrollIntoViewIfNeeded();
    await page.waitForTimeout(200);
    const inventory = await assertInventory(page);
    const layout = await assertLayout(page);
    const filterCount = await page.locator("[data-r6-visual-filter]").count();
    assertCondition(filterCount === 4, "R6 does not expose exactly four visual filters", { filterCount });
    const machineDetails = page.locator("details[data-r6-machine-details]");
    assertCondition(await machineDetails.count() >= 1 && !(await machineDetails.first().evaluate((item) => item.open)), "R6 machine details are not folded by default");

    let interactions = null;
    if (viewport.name === "desktop-low-height") {
      interactions = {
        evidence: await assertEvidenceInteractions(page),
        filters: await assertFourAxisFilters(page),
        opportunity: await assertOpportunityDetail(page),
        formula: await assertFormulaInteraction(page, writeRequests),
      };
    }

    await workbench.scrollIntoViewIfNeeded();
    const screenshotPath = path.join(outputDir, `visual-workflows-${viewport.name}-${viewport.width}x${viewport.height}.png`);
    await page.screenshot({ path: screenshotPath, fullPage: false });
    const screenshotBytes = fs.statSync(screenshotPath).size;
    assertCondition(screenshotBytes > 15000, "R6 visual screenshot is unexpectedly small", { screenshotBytes, screenshotPath });
    const actionableResponses = failedResponses.filter((response) => !isIgnoredRuntimeProbe(response));
    const actionableConsoleErrors = consoleErrors.filter((message) => !(message.startsWith("Failed to load resource:") && actionableResponses.length === 0));
    assertCondition(actionableResponses.length === 0 && actionableConsoleErrors.length === 0, "R6 browser emitted errors", {
      actionableConsoleErrors,
      actionableResponses,
      consoleErrors,
      failedResponses,
    });
    return { status: "PASS", viewport, inventory, layout, interactions, screenshot: { path: screenshotPath, bytes: screenshotBytes } };
  } catch (error) {
    const screenshotPath = path.join(outputDir, `visual-workflows-${viewport.name}-failure.png`);
    await page.screenshot({ path: screenshotPath, fullPage: false }).catch(() => undefined);
    return {
      status: "FAIL",
      viewport,
      message: error.message,
      details: error.details || null,
      consoleErrors,
      failedResponses,
      screenshot: fs.existsSync(screenshotPath) ? { path: screenshotPath, bytes: fs.statSync(screenshotPath).size } : null,
    };
  } finally {
    await page.close();
  }
}

function writeStatus(payload) {
  fs.mkdirSync(outputDir, { recursive: true });
  fs.writeFileSync(path.join(outputDir, "status.json"), `${JSON.stringify(payload, null, 2)}\n`, "utf8");
}

(async () => {
  let preview = null;
  try {
    fs.mkdirSync(outputDir, { recursive: true });
    buildFrontend();
    preview = startPreview();
    await waitForHttp(targetUrl, preview);
    const { chromium } = requirePlaywright();
    assertCondition(Boolean(browserExecutable), "No Chromium-compatible browser executable found");
    const browser = await chromium.launch({ executablePath: browserExecutable, headless: true });
    let results;
    try {
      results = [];
      for (const viewport of viewports) results.push(await validateViewport(browser, viewport));
    } finally {
      await browser.close();
    }
    const failures = results.filter((result) => result.status !== "PASS");
    assertCondition(failures.length === 0, "One or more R6 visual workflow viewport contracts failed", { failures });
    await stopPreview(preview);
    await assertPortClosed();
    const payload = {
      status: "PASS",
      gate: "memory_atlas_v1_2_r6_visual_workflows",
      targetUrl,
      outputDir,
      visualIds,
      viewports,
      checks: [
        "exact twelve approved P0 visual workflows",
        "literal source/time/project/task filters alter the event-backed signature",
        "each visual has a keyboard-operable datum and updates inline evidence",
        "opportunity drill-down exposes evidence, next step, half-life, defer reason and boundary",
        "Formula score changes and resets without a write request",
        "three target viewports have no overlap, clipping or horizontal overflow",
        "nonblank screenshots and clean browser console",
      ],
      results,
    };
    writeStatus(payload);
    console.log(JSON.stringify(payload, null, 2));
  } catch (error) {
    if (preview) await stopPreview(preview).catch(() => undefined);
    await assertPortClosed().catch(() => undefined);
    const payload = {
      status: "FAIL",
      gate: "memory_atlas_v1_2_r6_visual_workflows",
      message: error.message,
      details: error.details || null,
      targetUrl,
      outputDir,
      serverLogs: preview?.logs?.join("").slice(-4000) || "",
    };
    writeStatus(payload);
    console.error(JSON.stringify(payload, null, 2));
    process.exitCode = 1;
  }
})();
